package web

// THE SERVED HANDPLACE (design §10.1): for a person a garden's grants name, beyond this machine, over TLS. They sign
// in by a link sent to the mail their own bean names, through one of the garden's mail channels that its flow law
// grants (daftard keeps no password); what they then read is asked of the garden's `may` before each one (flow row
// `served`) — a bean a grant opens to them, their own leads — and nothing else of the gardener's handplace is served
// here. Asked for a person nobody knows, the page answers as for one it does, and sends nothing.

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"io/fs"
	"net"
	"net/http"
	"net/mail"
	"path"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/notify"
	"github.com/0mit/daftar/daftard/internal/passkey"
	"github.com/0mit/daftar/daftard/internal/proc"
	"github.com/0mit/daftar/daftard/internal/served"
	"github.com/0mit/daftar/daftard/internal/state"
)

const servedCookie = "__Host-daftard-served"

var personRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}$`)

const linkGone = "این پیوند دیگر معتبر نیست؛ پیوند تازه‌ای بخواهید. — This link is no longer good; ask for a new one."

const servedSaid = "اگر این دفتر شما را می‌شناسد، پیوندی برای ورود به نشانی رایانامهٔ شما فرستاده شد؛ پانزده دقیقه معتبر است. — " +
	"If this garden knows you, a link to sign in has been sent to your mail; it is good for fifteen minutes."

// SendMail hands a message to a mail channel's command (sendmail -t on its standard input).
func SendMail(ch config.Channel, msg []byte) error {
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	c := proc.CommandContext(ctx, ch.Command[0], ch.Command[1:]...)
	c.Stdin = bytes.NewReader(msg)
	if out, err := c.CombinedOutput(); err != nil {
		return fmt.Errorf("%v %s", err, strings.TrimSpace(string(out)))
	}
	return nil
}

// ServedHandler is the served handplace: answering only to `names`, its sessions in `sessions`.
func (s *Server) ServedHandler(names []string, sessions *served.Sessions) http.Handler {
	known := map[string]bool{}
	for _, n := range names {
		known[n] = true
	}
	if s.Mail == nil {
		s.Mail = SendMail
	}
	if s.Counts == nil { // each passkey's last signature counter: the machine's, in its state folder (security audit 1.4)
		path := ""
		if dir, err := state.Ensure(); err == nil {
			path = filepath.Join(dir, "passkey-counts.json")
		}
		s.Counts = passkey.OpenCounts(path)
		if err := s.Counts.Err(); err != nil && s.Log != nil {
			s.Log("passkey counters: %s could not be read (%v); they are kept again from the next sign-in", path, err)
		}
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", csp)
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		w.Header().Set("Strict-Transport-Security", "max-age=31536000")
		if !known[r.Host] {
			text(w, 403, "دسترسی مجاز نیست.")
			return
		}
		origin := "https://" + r.Host
		p := r.URL.Path
		switch {
		case p == "/served/link" && r.Method == http.MethodPost:
			if r.Header.Get("Origin") != origin {
				reply(w, 403, map[string]any{"error": "درخواست معتبر نیست."})
				return
			}
			req, ok := readJSON(w, r)
			if !ok {
				return
			}
			gname, _ := req["g"].(string)
			person, _ := req["person"].(string)
			if g := s.servedGarden(gname); g != nil && personRe.MatchString(person) {
				if tok, fresh := sessions.Issue(g.Conf.Name, person, time.Now()); fresh {
					// the token travels after '#': no request carries a fragment, so no server's log — the proxy's
					// in front of this one — ever holds it; the page it opens sends it here (security audit 1.7)
					go s.sendLink(g, person, origin+"/#in="+tok)
				}
			}
			reply(w, 202, map[string]any{"said": servedSaid})
		case p == "/served/passkey/challenge" && r.Method == http.MethodPost: // a sign-in by a passkey begins here
			if r.Header.Get("Origin") != origin {
				reply(w, 403, map[string]any{"error": "درخواست معتبر نیست."})
				return
			}
			reply(w, 200, map[string]any{"challenge": b64.EncodeToString(sessions.Challenge("signin", "", time.Now())), "rpId": rpID(r.Host)})
		case p == "/served/passkey/in" && r.Method == http.MethodPost:
			if r.Header.Get("Origin") != origin {
				reply(w, 403, map[string]any{"error": "درخواست معتبر نیست."})
				return
			}
			req, ok := readJSON(w, r)
			if !ok {
				return
			}
			s.passkeyIn(w, req, origin, r.Host, sessions)
		case p == "/served/in" && r.Method == http.MethodPost:
			// a link's token, sent once by the page the link opened, from its own origin: spent here, and the session
			// it begins is the answer's cookie (a token in a query — a log read back, an old link — signs nobody in)
			if r.Header.Get("Origin") != origin {
				reply(w, 403, map[string]any{"error": "درخواست معتبر نیست."})
				return
			}
			req, ok := readJSON(w, r)
			if !ok {
				return
			}
			t, _ := req["t"].(string)
			sid, _, ok := sessions.Redeem(t, time.Now())
			if !ok {
				reply(w, 403, map[string]any{"error": linkGone})
				return
			}
			http.SetCookie(w, &http.Cookie{Name: servedCookie, Value: sid, Path: "/", Secure: true, HttpOnly: true,
				SameSite: http.SameSiteStrictMode})
			reply(w, 200, map[string]any{"in": true})
		case p == "/served/in" && r.Method == http.MethodGet:
			text(w, 403, linkGone)
		case p == "/" || p == "/served.js" || p == "/served.css":
			s.servedAsset(w, r, p)
		case strings.HasPrefix(p, "/served/"):
			c, err := r.Cookie(servedCookie)
			var se *served.Session
			if err == nil {
				se, _ = sessions.Get(c.Value, time.Now())
			}
			g := (*Garden)(nil)
			if se != nil {
				g = s.servedGarden(se.Garden)
			}
			if se == nil || g == nil {
				reply(w, 401, map[string]any{"error": "نخست وارد شوید. — Sign in first.", "signin": true})
				return
			}
			if r.Method == http.MethodPost {
				if r.Header.Get("Origin") != origin || !same(r.Header.Get("X-CSRF-Token"), se.CSRF) {
					reply(w, 403, map[string]any{"error": "نشست معتبر نیست؛ صفحه را دوباره باز کنید."})
					return
				}
				if p == "/served/out" {
					sessions.End(c.Value)
					reply(w, 200, map[string]any{"out": true})
					return
				}
				if p == "/served/passkey/new" { // a passkey to register: the challenge, the site, who it is for
					me := se.Person
					reply(w, 200, map[string]any{"challenge": b64.EncodeToString(sessions.Challenge("register", c.Value, time.Now())),
						"rp":         map[string]any{"id": rpID(r.Host), "name": g.Conf.Title},
						"user":       map[string]any{"id": b64.EncodeToString([]byte(g.Conf.Name + "/" + me)), "name": me, "displayName": me},
						"algorithms": passkey.Algorithms})
					return
				}
				if p == "/served/passkey/made" { // a passkey made: verified, and laid for the gardener to name as theirs
					req, ok := readJSON(w, r)
					if !ok {
						return
					}
					cd, _ := b64.DecodeString(str(req["clientDataJSON"]))
					att, _ := b64.DecodeString(str(req["attestationObject"]))
					var client struct{ Challenge string }
					_ = json.Unmarshal(cd, &client)
					ch, _ := b64.DecodeString(strings.TrimRight(client.Challenge, "="))
					if !sessions.Spend(ch, "register", c.Value, time.Now()) {
						reply(w, 403, map[string]any{"error": "این درخواست دیگر معتبر نیست؛ دوباره تلاش کنید."})
						return
					}
					anchor, err := passkey.Register(cd, att, ch, origin, rpID(r.Host))
					if err != nil {
						reply(w, 400, map[string]any{"error": "کلید پذیرفته نشد: " + err.Error()})
						return
					}
					s.pass(w, g, "passkey_lay", map[string]any{"person": se.Person, "anchor": anchor})
					return
				}
				if p == "/served/form" { // their answers to a form open to them: laid for the gardener, never written in
					req, ok := readJSON(w, r)
					if !ok {
						return
					}
					s.pass(w, g, "served_submit", map[string]any{"person": se.Person, "id": req["id"], "answers": req["answers"]})
					return
				}
				reply(w, 404, map[string]any{"error": "پیدا نشد."})
				return
			}
			switch p {
			case "/served/me":
				title := se.Person
				if raw, err := g.Worker.Call("person", map[string]any{"id": se.Person}, 30*time.Second); err == nil {
					var who map[string]string
					if json.Unmarshal(raw, &who) == nil && who["title"] != "" {
						title = who["title"]
					}
				}
				reply(w, 200, map[string]any{"garden": g.Conf.Name, "title": g.Conf.Title, "person": se.Person,
					"me": title, "csrf": se.CSRF})
			case "/served/forms":
				s.pass(w, g, "served_forms", map[string]any{"person": se.Person})
			case "/served/leads":
				s.pass(w, g, "served_leads", map[string]any{"person": se.Person})
			case "/served/bean":
				s.pass(w, g, "served_read", map[string]any{"person": se.Person, "id": r.URL.Query().Get("id")})
			default:
				reply(w, 404, map[string]any{"error": "پیدا نشد."})
			}
		default:
			text(w, 404, "پیدا نشد.")
		}
	})
}

var b64 = base64.RawURLEncoding

func str(v any) string {
	s, _ := v.(string)
	return strings.TrimRight(s, "=")
}

// rpID is the site a passkey is made for: the host the page is served at, without its port.
func rpID(host string) string {
	if h, _, err := net.SplitHostPort(host); err == nil {
		return h
	}
	return host
}

// passkeyIn begins a session for the person whose passkey answered: the garden and person its user handle names (set
// when it was registered), verified against the passkeys that person's own bean names — nothing kept here.
func (s *Server) passkeyIn(w http.ResponseWriter, req map[string]any, origin, host string, sessions *served.Sessions) {
	nope := func() {
		reply(w, 403, map[string]any{"error": "ورود با این کلید ممکن نشد. — This passkey did not sign you in."})
	}
	handle, _ := b64.DecodeString(str(req["userHandle"]))
	gname, person, ok := strings.Cut(string(handle), "/")
	g := s.servedGarden(gname)
	if !ok || g == nil || !personRe.MatchString(person) {
		nope()
		return
	}
	id, _ := b64.DecodeString(str(req["id"]))
	cd, _ := b64.DecodeString(str(req["clientDataJSON"]))
	ad, _ := b64.DecodeString(str(req["authenticatorData"]))
	sig, _ := b64.DecodeString(str(req["signature"]))
	var c struct{ Challenge string }
	_ = json.Unmarshal(cd, &c)
	ch, _ := b64.DecodeString(strings.TrimRight(c.Challenge, "="))
	if !sessions.Spend(ch, "signin", "", time.Now()) {
		nope()
		return
	}
	raw, err := g.Worker.Call("served_passkeys", map[string]any{"person": person}, time.Minute)
	var anchors []string
	if err != nil || json.Unmarshal(raw, &anchors) != nil {
		nope()
		return
	}
	_, count, err := passkey.SignIn(id, cd, ad, sig, ch, origin, rpID(host), anchors)
	if err != nil {
		if s.Log != nil {
			s.Log("[%s] a passkey sign-in for %s refused: %v", g.Conf.Name, person, err)
		}
		nope()
		return
	}
	// the counter, asked only once the signature is the person's own: one that does not grow is a copy of their
	// authenticator answering (W3C Web Authentication §6.1.1, security audit 2026-10-10, 1.4)
	if err := s.Counts.Check(id, count); errors.Is(err, passkey.ErrCloned) {
		if s.Log != nil {
			s.Log("[%s] a passkey sign-in for %s refused at counter %d: %v", g.Conf.Name, person, count, err)
		}
		nope()
		return
	} else if err != nil && s.Log != nil {
		s.Log("[%s] a passkey's counter for %s was kept in memory, not written: %v", g.Conf.Name, person, err)
	}
	sid, _ := sessions.Begin(g.Conf.Name, person, time.Now())
	http.SetCookie(w, &http.Cookie{Name: servedCookie, Value: sid, Path: "/", Secure: true, HttpOnly: true,
		SameSite: http.SameSiteStrictMode})
	reply(w, 200, map[string]any{"in": true})
}

// servedGarden is a garden this machine offers on the served listener, by name.
func (s *Server) servedGarden(name string) *Garden {
	for _, g := range s.Gardens {
		if g.Conf.Served && g.Conf.Name == name && g.Worker != nil {
			return g
		}
	}
	return nil
}

// sendLink sends a sign-in link to the person, where a grant of the garden names them, their bean names their mail,
// and one of the garden's mail channels is granted by its flow law; otherwise nothing, and only the log says why.
func (s *Server) sendLink(g *Garden, person, link string) {
	logf := func(f string, a ...any) {
		if s.Log != nil {
			s.Log(fmt.Sprintf("[%s] served sign-in for %s: ", g.Conf.Name, person)+f, a...)
		}
	}
	raw, err := g.Worker.Call("served_person", map[string]any{"id": person}, time.Minute)
	var who struct {
		Mail    string `json:"mail"`
		Granted bool   `json:"granted"`
	}
	if err != nil || json.Unmarshal(raw, &who) != nil || !who.Granted || who.Mail == "" {
		logf("no link sent (no grant names them, or their bean names no mail)")
		return
	}
	addr, err := mail.ParseAddress(who.Mail)
	if err != nil {
		logf("no link sent: their bean's mail is not an address")
		return
	}
	for _, ch := range g.Conf.Channels {
		if ch.Kind != "mail" || len(ch.Command) == 0 || ch.Party == "" {
			continue
		}
		raw, err := g.Worker.Call("may_send", map[string]any{"party": ch.Party}, time.Minute)
		var may struct {
			Granted bool `json:"granted"`
		}
		if err != nil || json.Unmarshal(raw, &may) != nil || !may.Granted {
			continue
		}
		from := ch.From
		if from == "" {
			from = "daftard <daftard@localhost>"
		}
		n := notify.Notice{Title: "ورود به " + g.Conf.Title + " — Sign in to " + g.Conf.Title,
			Body: "برای ورود این پیوند را باز کنید؛ پانزده دقیقه و یک بار معتبر است:\n" + link +
				"\n\nTo sign in, open this link; it is good once, for fifteen minutes.\nIf you did not ask for it, do nothing."}
		if err := s.Mail(ch, notify.Mail(n, from, addr.Address)); err != nil {
			logf("the channel to %s did not take it: %v", ch.Party, err)
			continue
		}
		logf("a link was sent through %s", ch.Party)
		return
	}
	logf("no link sent: no mail channel of the garden is granted by its flow law")
}

// servedAsset is the served page: its own small page, nothing of the gardener's handplace.
func (s *Server) servedAsset(w http.ResponseWriter, r *http.Request, p string) {
	name := map[string]string{"/": "served/index.html", "/served.js": "served/served.js", "/served.css": "served/served.css"}[p]
	b, err := fs.ReadFile(s.Assets, name)
	if err != nil {
		text(w, 404, "پیدا نشد.")
		return
	}
	ct := types[path.Ext(name)]
	w.Header().Set("Content-Type", ct)
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(b)
}
