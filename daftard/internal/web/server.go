// Package web is the handplace's server: the pages, and the data calls they make, for the gardens this machine serves.
// It listens on the loopback address only; a request must carry the page's cookie (set when a one-time code from the
// door opened it: a value of this run's, never the machine's key) or the machine's key in the command line's header,
// name this server as its Host and, for a change, as its Origin with the session's CSRF token. Every
// refusal or failure is a guided error (design §3): a message, a reference, and whom to follow it up with.
package web

import (
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"mime"
	"net"
	"net/http"
	"net/url"
	"path"
	"regexp"
	"strings"
	"sync"
	"time"
	"unicode/utf8"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/custom"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/hubkey"
	"github.com/0mit/daftar/daftard/internal/notify"
	"github.com/0mit/daftar/daftard/internal/passkey"
	"github.com/0mit/daftar/daftard/internal/register"
	"github.com/0mit/daftar/daftard/internal/routines"
	"github.com/0mit/daftar/daftard/internal/sitting"
	"github.com/0mit/daftar/daftard/internal/state"
	"github.com/0mit/daftar/daftard/internal/syncer"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// Garden is what the server holds for one garden.
type Garden struct {
	Conf   config.Garden
	Worker Caller // its own worker; in the machine's daftard, the garden's own daemon (Remote)
	Syncer *syncer.Syncer
	// Routines keeps this machine's routines of the garden and its tools' readings (internal/routines); nil where the
	// garden's settings leave them off
	Routines *routines.Runner
	Custom   *custom.Store // what each person changed of the handplace for themselves (their labels)
	Version  string        // the garden's code when its worker started: a page reloads when it changes
	// Register keeps the routes to the garden's register and their health (internal/register): each Odoo call is
	// handed the healthy ones; nil where the garden names no register
	Register *register.Routes
	// PlaceRoutes keeps the routes to the garden's place service and their health, as Register does its register's: a
	// place lookup goes by the healthy ones; nil where the garden names no place service
	PlaceRoutes *register.Routes
	// HubKey is the key of this machine's hub of the garden (internal/hubkey), found when daftard started; nil where
	// the garden names no hub (Conf.Hub) or its hub has no key yet
	HubKey *hubkey.Key
}

// Server is the handplace's server.
type Server struct {
	Listen string
	Token  string // the machine's key: sent only in keyHeader, by `daftard open` and the command line
	CSRF   string
	// page is what the page's cookie carries: made when this daftard starts and kept in memory alone, so a cookie
	// sent to another port of 127.0.0.1 (cookies are not kept apart by port) is never the key, and is good on this
	// run alone (security audit 2026-10-10, 2.7)
	page    string
	onceMu  sync.Mutex
	onces   map[string]time.Time // `daftard open`'s one-time codes, by digest: the key itself never goes in a URL
	Build   string
	Gardens []*Garden
	Assets  fs.FS
	Errors  *guided.Store
	Stop    func()
	Notify  func(notify.Notice) error // how this machine raises a notice (notify.Show)
	// Who sits at the keyboard (design §6): this machine's people's keys, the sittings begun, and the askpass by which
	// ssh-keygen asks for a sitting's passphrase while it signs.
	Keys     *sitting.Keys
	Sittings *sitting.Sittings
	Askpass  *sitting.Askpass
	// Shared is a machine whose one account several people use (daftard.json `shared`): there reading is closed as
	// well — a garden's pages open to its gardener's sitting alone, and to no page with nobody sitting.
	Shared bool
	// Mail hands a message to a garden's mail channel (SendMail unless a test stands in); Log is the machine's log
	Mail func(ch config.Channel, msg []byte) error
	// Counts are the passkeys' last signature counters (security audit 1.4): the state folder's, unless a test says
	Counts *passkey.Counts
	// OdooDir holds each Odoo series' own web client, as importers/odoo/client.py took it (<OdooDir>/<series>/)
	OdooDir string
	// Odoo is the door to Odoo's own origin (odoo.go): nil, the handplace offers no Odoo page.
	Odoo    *OdooDoor
	Log     func(format string, a ...any)
	hosts   map[string]bool
	watches map[string]*watch
	// Own is the garden this daftard is the daemon of (one daemon per garden); "" in the machine's own daftard. Front is
	// the machine's front door, where another garden's address is sent on to that garden's daemon
	Own, Front string
	front      http.Handler // the front door, as a test asks it (front_test.go)
	// the garden's answers held in memory, by garden (held.go)
	heldMu sync.Mutex
	heldOf map[string]*heldAnswers
	// Places is this machine's own place search (places.go): nil, a garden's own places alone
	Places *PlaceIndex
	ownMu  sync.Mutex
	owned  map[string]ownPlaces // each garden's own places, as of its commit
}

const cookieName = "daftard" // a garden's own daemon: daftard-<garden> (cookie)

// keyHeader carries the machine's key, from `daftard open` (for a one-time code) and the command line: a header no
// browser sends on its own, and no other site's page can add without a preflight this server never answers.
const keyHeader = "X-Daftard-Key"

var dayRe = regexp.MustCompile(`^\d{4}-\d{2}-\d{2}$`)
var refRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]*#[A-Za-z0-9][A-Za-z0-9-]*$`)
var unitRe = regexp.MustCompile(`^[A-Z]{3}$`)
var errRefRe = regexp.MustCompile(`^E-[0-9A-Z]{4}-[0-9A-Z]{4}$`)
var slugRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,120}$`)
var proposalRe = regexp.MustCompile(`^PROPOSAL-[A-Za-z0-9][A-Za-z0-9-]{0,120}$`)
var labelRe = regexp.MustCompile(`^[a-z][a-z0-9-]*(\.[a-z0-9-]+){0,4}$`)
var uuidRe = regexp.MustCompile(`^[0-9a-f]{32}$`)
var passkeyRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}\.\d{8}T\d{6}$`)
var formRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,120}\.[a-z0-9][a-z0-9-]{0,63}\.\d{8}T\d{6}$`)
var actionRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,120}\.[a-z0-9][a-z0-9-]{0,120}$`)

// needRe is a need's landing (`<bean>.<need>`, core 3.7: what waits is a need on the bean it concerns), beside a
// decision of log/pending.md, named by its slug.
var needRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,120}\.[A-Za-z0-9][A-Za-z0-9-]{0,120}$`)

// GoRe is what a landing address may be (/go/<garden>[/<kind>[/<id>]]): the place a notification, a link or a
// platform's own lead brings a person to, naming the case and nothing more (the page reads the case from the garden).
var GoRe = regexp.MustCompile(`^/go/[A-Za-z0-9][A-Za-z0-9._-]{0,40}(/(pending|proposal|error|case|sync|session|action|form|health|obligation|passkey)(/[A-Za-z0-9][A-Za-z0-9._-]{0,120})?)?/?$`)

// OdooRe is the page of Odoo's own client for one garden (odoo.go), the other address the machine's key may open —
// as of a commit or a moment (design §10.3), each in the form the garden's worker reads.
var OdooRe = regexp.MustCompile(`^/odoo\?g=[A-Za-z0-9][A-Za-z0-9._-]{0,40}(&series=\d{2}\.\d)?` +
	`(&asof=([0-9a-f]{4,40}|\d{4}-\d{2}-\d{2}([ T+%:0-9Z-]{0,20})?))?$`)

// csp is the pages' policy: their own scripts, styles and font, their own data calls, nothing else.
const csp = "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; connect-src 'self'; " +
	"img-src 'self' data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"

// cookie is the name of this daftard's cookie: a garden's own daemon names its garden in it, since a browser keeps
// the cookies of 127.0.0.1 apart by name and never by port, and two gardens' daemons must not take each other's
func (s *Server) cookie() string {
	if s.Own != "" {
		return cookieName + "-" + s.Own
	}
	return cookieName
}

func same(a, b string) bool { // compared as bytes: a key in any script is just a wrong key, never a crash
	return subtle.ConstantTimeCompare([]byte(a), []byte(b)) == 1
}

func (s *Server) init() {
	_, port, _ := net.SplitHostPort(s.Listen)
	// 127.0.0.1 alone: `localhost` is Odoo's origin (odoo.go), another host, so no cookie of this page reaches it
	s.hosts = map[string]bool{"127.0.0.1:" + port: true}
	s.onces = map[string]time.Time{}
	if s.page == "" {
		s.page = state.Random(32)
	}
}

func (s *Server) issueOnce(now time.Time) string {
	s.onceMu.Lock()
	defer s.onceMu.Unlock()
	for k, until := range s.onces {
		if now.After(until) {
			delete(s.onces, k)
		}
	}
	t := odooRandom()
	if len(s.onces) < odooMax {
		s.onces[odooDigest(t)] = now.Add(time.Minute)
	}
	return t
}

func (s *Server) spendOnce(t string, now time.Time) bool {
	s.onceMu.Lock()
	defer s.onceMu.Unlock()
	k := odooDigest(t)
	until, ok := s.onces[k]
	delete(s.onces, k)
	return ok && !now.After(until)
}

func (s *Server) hostOK(r *http.Request) bool {
	if !s.hosts[r.Host] { // a page served under another name (DNS rebinding) is refused
		return false
	}
	if site := r.Header.Get("Sec-Fetch-Site"); site != "" && site != "same-origin" && site != "none" {
		return false
	}
	return true
}

func (s *Server) originOK(r *http.Request) bool {
	o := r.Header.Get("Origin")
	return o != "" && s.hosts[strings.TrimPrefix(o, "http://")] && strings.HasPrefix(o, "http://")
}

// authenticated: the machine's key in the command line's header, or the page's cookie carrying this run's value.
func (s *Server) authenticated(r *http.Request) bool {
	if k := r.Header.Get(keyHeader); k != "" {
		return same(k, s.Token)
	}
	c, err := r.Cookie(s.cookie())
	return err == nil && s.page != "" && same(c.Value, s.page)
}

func (s *Server) garden(r *http.Request) *Garden {
	name := r.URL.Query().Get("g")
	for _, g := range s.Gardens {
		if name == "" || g.Conf.Name == name {
			return g
		}
	}
	return nil
}

func reply(w http.ResponseWriter, status int, v any) {
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(v)
}

func text(w http.ResponseWriter, status int, body string) {
	w.Header().Set("Content-Type", "text/plain; charset=utf-8")
	w.WriteHeader(status)
	_, _ = io.WriteString(w, body)
}

// followUp is whom a person in this garden follows an error up with: the gardener and the holders of grants that
// would open the act (the garden's own bin/pass.py, through the worker), then the stewards daftard.json names.
func (s *Server) followUp(g *Garden, act, bean string) []guided.Contact {
	var out []guided.Contact
	seen := map[string]bool{}
	params := map[string]any{"actor": g.Conf.Gardener, "act": act, "bean": bean}
	if raw, err := g.Worker.Call("follow_up", params, 30*time.Second); err == nil {
		var list []struct{ Who, Why, Title string }
		if json.Unmarshal(raw, &list) == nil {
			for _, c := range list {
				if !seen[c.Who] {
					seen[c.Who] = true
					title := c.Title
					if title == "" {
						title = c.Who
					}
					if c.Why == "gardener" {
						title += T(g, " (دفتردار)", " (gardener)")
					}
					out = append(out, guided.Contact{Who: c.Who, Title: title, Why: c.Why, Sees: "all"})
				}
			}
		}
	}
	for _, f := range g.Conf.FollowUp {
		if !seen[f.Who] {
			seen[f.Who] = true
			out = append(out, guided.Contact{Who: f.Who, Title: f.Title, Why: "steward", Reach: f.Reach, Sees: f.Sees})
		}
	}
	return out
}

// fail turns a worker's refusal or failure into a guided error: kept with its reference, and answered with the
// person's message, the reference and whom to follow it up with.
func (s *Server) fail(w http.ResponseWriter, g *Garden, action, bean string, err error) {
	e, ok := worker.IsError(err)
	if !ok {
		e = &worker.Error{Status: 500, Kind: "failed", Message: err.Error(), Diagnostic: err.Error()}
	}
	message := e.Message
	if e.Kind != "refused" { // a failure's own words are for whoever looks into it; the person is told it did not go ahead
		message = T(g, "این کار انجام نشد و چیزی هم تغییر نکرد؛ اطلاعات فرم حفظ شده است.", "It did not go ahead, and nothing changed; the form keeps what you wrote.")
		if action != "save" {
			message = T(g, "خواندن دفتر ممکن نشد؛ اطلاعات قبلی ممکن است قدیمی باشد.", "The garden could not be read; what was shown before may be old.")
		}
	}
	rec := guided.Record{Garden: g.Conf.Name, Action: action, Status: e.Status, Kind: e.Kind, Message: message,
		Diagnostic: strings.TrimSpace(e.Message + "\n" + e.Diagnostic), FollowUp: s.followUp(g, "write", bean)}
	rec.Ref = s.Errors.Add(rec)
	state.Logger().Printf("[%s] %s %s %d %s: %s", g.Conf.Name, rec.Ref, action, e.Status, e.Kind, e.Message)
	status := e.Status
	if status < 400 || status > 599 {
		status = 500
	}
	reply(w, status, map[string]any{"error": rec.Sentence(), "message": message, "ref": rec.Ref, "followUp": rec.FollowUp})
}

// ServeHTTP is the whole of the handplace's routing.
func (s *Server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Security-Policy", csp)
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Referrer-Policy", "no-referrer")
	if !s.hostOK(r) {
		text(w, 403, both("دسترسی مجاز نیست.", "Access is not allowed."))
		return
	}
	p := r.URL.Path
	if s.Own != "" && r.Method == http.MethodGet && s.Front != "" { // another garden's address: its own daemon's, by the front door
		if g := r.URL.Query().Get("g"); g != "" && g != s.Own {
			http.Redirect(w, r, "http://"+s.Front+r.URL.RequestURI(), http.StatusFound)
			return
		}
		if parts := strings.SplitN(p, "/", 4); len(parts) >= 3 && (parts[1] == "go" || parts[1] == "release") && parts[2] != "" && parts[2] != s.Own {
			http.Redirect(w, r, "http://"+s.Front+r.URL.RequestURI(), http.StatusFound)
			return
		}
	}
	if p == "/internal/stop" && r.Method == http.MethodPost && s.Own != "" { // the machine's daftard ending this daemon
		if !same(r.Header.Get(keyHeader), s.Token) {
			reply(w, 403, map[string]any{"error": both("کلید معتبر نیست.", "The key is not valid.")})
			return
		}
		reply(w, 200, map[string]any{"stopping": true})
		if s.Stop != nil {
			go s.Stop()
		}
		return
	}
	if strings.HasPrefix(p, sitting.AskpassPath) && s.Askpass != nil { // ssh-keygen's askpass: by its one-time token
		s.Askpass.ServeHTTP(w, r)
		return
	}
	if p == "/health" { // daftard's own health, and each register's and place service's routes': never where one goes
		h := map[string]any{"app": "daftard", "ready": true, "build": s.Build}
		regs, svcs := map[string]any{}, map[string]any{}
		for _, g := range s.Gardens {
			if g.Register != nil {
				regs[g.Conf.Name] = g.Register.State(false)
			}
			if g.PlaceRoutes != nil {
				svcs[g.Conf.Name] = g.PlaceRoutes.State(false)
			}
		}
		if len(regs) > 0 {
			h["registers"] = regs
		}
		if len(svcs) > 0 {
			h["place_services"] = svcs
		}
		reply(w, 200, h)
		return
	}
	if p == "/internal/call" && r.Method == http.MethodPost { // the machine's daftard asking this garden (remote.go)
		s.internalCall(w, r)
		return
	}
	if p == "/door" && r.Method == http.MethodPost { // `daftard open`: the key in a header, a one-time code back
		if !same(r.Header.Get(keyHeader), s.Token) {
			reply(w, 403, map[string]any{"error": both("کلید معتبر نیست.", "The key is not valid.")})
			return
		}
		reply(w, 200, map[string]any{"once": s.issueOnce(time.Now())})
		return
	}
	if p == "/" && r.Method == http.MethodGet && r.URL.Query().Get("once") != "" {
		// the key never travels in a URL, so no command line or browser history holds it (security audit 2.2): a
		// one-time code does, spent here within a minute
		if !s.spendOnce(r.URL.Query().Get("once"), time.Now()) {
			text(w, 403, both("این پیوند دیگر معتبر نیست؛ دفتر را از میان‌بر روی میز کار باز کنید.", "This link is no longer good: open the garden from the desktop shortcut."))
			return
		}
		// the cookie carries this run's own value, not the key: whatever listens on another port the browser visits is
		// sent it too (security audit 2.7)
		http.SetCookie(w, &http.Cookie{Name: s.cookie(), Value: s.page, Path: "/", HttpOnly: true, SameSite: http.SameSiteStrictMode})
		target := "/"
		if to := r.URL.Query().Get("to"); GoRe.MatchString(to) || OdooRe.MatchString(to) { // this server's own, nothing else
			target = to
		} else if g := r.URL.Query().Get("g"); g != "" {
			target = "/?g=" + url.QueryEscape(g)
		}
		// the page's own switches go along, and nothing else: debug (console logs), admin (labels), static (no events)
		for _, f := range []string{"debug", "admin", "static"} {
			if v := r.URL.Query().Get(f); v == "0" || v == "1" {
				sep := "?"
				if strings.Contains(target, "?") {
					sep = "&"
				}
				target += sep + f + "=" + v
			}
		}
		http.Redirect(w, r, target, http.StatusSeeOther) // the key leaves the address bar and the history
		return
	}
	if !s.authenticated(r) {
		text(w, 403, both("دفتر را از میان‌بر «دفتر» روی میز کار یا از اعلان دفتر باز کنید.", "Open the garden from its desktop shortcut, or from one of its notices."))
		return
	}
	if isOdoo(p) { // Odoo's own client lives on an origin of its own (odoo.go); here is only its door
		if p == "/odoo" && r.Method == http.MethodGet && s.Odoo != nil {
			s.odooOpen(w, r)
			return
		}
		text(w, 404, both("پیدا نشد.", "Not found."))
		return
	}
	if r.Method == http.MethodPost {
		if !s.originOK(r) || !same(r.Header.Get("X-CSRF-Token"), s.CSRF) {
			reply(w, 403, map[string]any{"error": both("نشست معتبر نیست؛ صفحه را دوباره باز کنید.", "The session is not valid: open the page again.")})
			return
		}
		s.post(w, r)
		return
	}
	if strings.HasPrefix(p, "/api/") || p == "/view" {
		s.get(w, r)
		return
	}
	if strings.HasPrefix(p, "/release/") { // a garden's own view asset: its runtime, renderers and widgets (viewpages.go)
		s.release(w, r)
		return
	}
	s.asset(w, r)
}

func (s *Server) get(w http.ResponseWriter, r *http.Request) {
	g := s.garden(r)
	if g == nil {
		reply(w, 404, map[string]any{"error": T(g, "این دفتر روی این رایانه نیست.", "This garden is not on this machine.")})
		return
	}
	q := r.URL.Query()
	if r.URL.Path != "/api/session" && r.URL.Path != "/api/sitting" && !s.mayRead(w, r, g) {
		return
	}
	switch r.URL.Path {
	case "/api/events":
		s.events(w, r, g)
	case "/api/session":
		var info map[string]any
		gardener := false // the garden's own part, as session_info: on a shared machine, to its gardener's sitting alone
		if st := s.sittingOf(r); !s.Shared || (st != nil && st.Person == g.Conf.Gardener) {
			raw, _ := g.Worker.Call("session_info", nil, time.Minute) // the exchange's last round: the garden's own
			_ = json.Unmarshal(raw, &info)
			gardener = true
		}
		if info == nil {
			info = map[string]any{}
		}
		if g.Register != nil && gardener { // its register's routes, and where each goes (`daftard status`)
			info["register"] = g.Register.State(true)
		}
		if g.PlaceRoutes != nil && gardener { // its place service's, likewise
			info["place_service"] = g.PlaceRoutes.State(true)
		}
		info["csrf"], info["version"], info["build"] = s.CSRF, g.Version, s.Build
		if g.Syncer != nil {
			info["sync"] = g.Syncer.Last()
		}
		reply(w, 200, info)
	case "/api/dashboard":
		if g.Conf.ViewHandplace() { // the garden's pages are its page beans: the chrome's data and its navigation
			s.viewPages(w, r, g)
			return
		}
		raw, err := s.call(g, "payload", map[string]any{"private": true}, 2*time.Minute)
		if err != nil {
			s.fail(w, g, "read", "", err)
			return
		}
		var data map[string]any
		if err := json.Unmarshal(raw, &data); err != nil {
			s.fail(w, g, "read", "", err)
			return
		}
		data["csrf"], data["version"], data["build"] = s.CSRF, g.Version, s.Build
		data["sync"] = map[string]any{"state": "off"}
		if g.Syncer != nil {
			data["sync"] = g.Syncer.Last()
		}
		data["garden"] = map[string]any{"name": g.Conf.Name, "title": g.Conf.Title, "lang": g.Conf.Lang,
			"gardener": g.Conf.Gardener, "me": g.Conf.Me, "kind": g.Conf.Kind}
		if g.Conf.Kind == "core" { // what a garden of the core offers, and whether this machine opens it (odoo.go)
			s.odooScreens(data)
		}
		data["labels"] = s.labelsOf(r, g)
		data["reader"] = s.readerOf(r, g)
		data["sitting"] = s.sittingState(r, g)
		reply(w, 200, data)
	case "/api/sitting":
		reply(w, 200, s.sittingState(r, g))
	case "/api/view/page": // one page bean, for the person reading (viewpages.go)
		s.viewPage(w, r, g)
	case "/api/prefs": // the person's own way of reading (prefs.go)
		s.prefsGet(w, r, g)
	case "/api/keys/hub": // the key of this machine's hub of the garden, for the gardener to add to the hub's bean (class F)
		if g.Conf.Hub == "" {
			reply(w, 404, map[string]any{"error": "این دفتر در این رایانه هابی به نام خودش ندارد که چیزی را امضا کند."})
			return
		}
		if g.HubKey == nil {
			reply(w, 404, map[string]any{"error": "هاب این دفتر در این رایانه هنوز کلیدی ندارد: bin/hub.py install آن را می‌سازد.",
				"hub": g.Conf.Hub})
			return
		}
		named, err := g.HubKey.Named(g.Conf.Path, g.Conf.Hub) // what the hub's bean says of it at the last commit
		reply(w, 200, map[string]any{"hub": g.Conf.Hub, "fingerprint": g.HubKey.Fingerprint, "statement": g.HubKey.Statement(),
			"named": named && err == nil})
	case "/api/keys/machine": // the machine's own key, for the gardener to add to the bean of the host it is (class F)
		if g.Conf.Machine == "" || s.Keys == nil {
			reply(w, 404, map[string]any{"error": T(g, "این رایانه در این دفتر به نام خودش چیزی ادغام نمی‌کند.", "This machine merges nothing in its own name in this garden.")})
			return
		}
		fpr, err := s.Keys.Machine()
		if err != nil {
			s.fail(w, g, "keys", g.Conf.Machine, err)
			return
		}
		reply(w, 200, map[string]any{"host": g.Conf.Machine, "fingerprint": fpr,
			"statement": fmt.Sprintf(`name: { by: ssh, of: self, as: "%s" }`, fpr)})
	case "/api/places": // a place as a person types it, from this machine alone (places.go)
		s.placesHere(w, r, g)
	case "/api/places/far": // the same beyond the machine, where the garden's flow law lets it go, never a whereabouts
		s.placesFar(w, r, g)
	case "/api/clock": // what this machine's time sources show of its clock (bin/clock.py): a save stamps only within 30 s
		s.pass(w, g, "clock", nil)
	case "/api/action": // an action's run: where it stands, and the plan its person is asked to ratify (bin/act.py)
		s.pass(w, g, "action", map[string]any{"id": q.Get("id")})
	case "/api/courses": // a being's courses as its garden's release reads them (bin/seq.py courses): a lead's own page
		s.pass(w, g, "courses", map[string]any{"id": q.Get("id")})
	case "/api/probe": // the latest readings of each tool this machine holds, and the routines' last tick (CONTRACT §3)
		if g.Routines == nil {
			reply(w, 200, map[string]any{"garden": g.Conf.Name, "tools": map[string]any{}, "off": true})
			return
		}
		reply(w, 200, g.Routines.Probes())
	case "/api/leads":
		list, err := Leads(g)
		if err != nil {
			s.fail(w, g, "read", "", err)
			return
		}
		reply(w, 200, map[string]any{"garden": g.Conf.Name, "leads": list})
	case "/api/pending":
		if !slugRe.MatchString(q.Get("id")) && !needRe.MatchString(q.Get("id")) {
			reply(w, 400, map[string]any{"error": T(g, "نشانی این مورد معتبر نیست.", "This item's address is not valid.")})
			return
		}
		s.pass(w, g, "pending", map[string]any{"id": q.Get("id")})
	case "/api/passkey": // a passkey a person made on the served page, for the gardener to name as theirs (class F)
		if !passkeyRe.MatchString(q.Get("id")) {
			reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
			return
		}
		s.pass(w, g, "passkey_laid", map[string]any{"id": q.Get("id")})
	case "/api/form": // one person's answers to a served form, laid outside the garden, for the gardener to take
		if !formRe.MatchString(q.Get("id")) {
			reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
			return
		}
		s.pass(w, g, "form_answers", map[string]any{"id": q.Get("id")})
	case "/api/proposal":
		if !proposalRe.MatchString(q.Get("id")) {
			reply(w, 400, map[string]any{"error": T(g, "نشانی این پیشنهاد معتبر نیست.", "This proposal's address is not valid.")})
			return
		}
		s.pass(w, g, "proposal", map[string]any{"id": q.Get("id"), "check": q.Get("check") == "1"})
	case "/api/books":
		from, to, unit := q.Get("from"), q.Get("to"), q.Get("unit")
		if unit == "" {
			unit = "TRY"
		}
		if (from != "" && !dayRe.MatchString(from)) || (to != "" && !dayRe.MatchString(to)) || !unitRe.MatchString(unit) {
			reply(w, 400, map[string]any{"error": T(g, "بازهٔ گزارش معتبر نیست.", "The report's span is not valid.")})
			return
		}
		s.pass(w, g, "books", map[string]any{"from": from, "to": to, "unit": unit})
	case "/api/history":
		if !refRe.MatchString(q.Get("ref")) {
			reply(w, 400, map[string]any{"error": T(g, "سند معتبر نیست.", "Not a valid document.")})
			return
		}
		s.pass(w, g, "history", map[string]any{"ref": q.Get("ref")})
	case "/api/calendar":
		from, to := q.Get("from"), q.Get("to")
		if !dayRe.MatchString(from) || !dayRe.MatchString(to) || from > to {
			reply(w, 400, map[string]any{"error": T(g, "بازهٔ تقویم معتبر نیست.", "The calendar's span is not valid.")})
			return
		}
		s.pass(w, g, "calendar", map[string]any{"from": from, "to": to})
	case "/api/error":
		ref := q.Get("ref")
		rec, ok := s.Errors.Get(ref)
		if !errRefRe.MatchString(ref) || !ok {
			reply(w, 404, map[string]any{"error": T(g, "این مرجع پیدا نشد.", "No such reference.")})
			return
		}
		// The reader here holds the machine's key: the gardener of the gardens this machine serves, who sees it all.
		// A served handplace (P4) reads the reader's own privileges instead.
		reply(w, 200, rec.For("all"))
	case "/view": // the view's own page: a dashboard's, or one page bean's (`page`), drawn by the release the garden runs
		var params map[string]any // a legacy garden's: the dashboard's own, asked as it always was
		if g.Conf.ViewHandplace() {
			params = map[string]any{"lang": g.Conf.Lang, "handplace": "view"}
			if page := q.Get("page"); page != "" {
				if !slugRe.MatchString(page) {
					text(w, 404, T(g, "این صفحه در این دفتر نیست.", "This page is not in this garden."))
					return
				}
				params["page"] = page
			}
		}
		// the page and its policy, made once per answer held: the JSON read, the scripts' hashes taken (derived)
		type viewPage struct{ page, csp string }
		d, err := s.derived(g, "view_html", params, 2*time.Minute, "page", func(raw json.RawMessage) (any, error) {
			var view struct {
				Page    string   `json:"page"`
				Scripts []string `json:"scripts"`
			}
			if err := json.Unmarshal(raw, &view); err != nil {
				return nil, err
			}
			if view.Page == "" {
				return nil, fmt.Errorf("no page")
			}
			// only the scripts the view's asset wrote may run: their hashes are taken from what the worker says the
			// asset declares, never from the page, where a bean's text carried unescaped would be a script too
			// (security audit 2026-10-10, 2.4)
			hashes := []string{}
			for _, sc := range view.Scripts {
				sum := sha256.Sum256([]byte(sc))
				hashes = append(hashes, "'sha256-"+base64.StdEncoding.EncodeToString(sum[:])+"'")
			}
			if len(hashes) == 0 {
				hashes = []string{"'none'"}
			}
			return viewPage{view.Page, "default-src 'none'; script-src " + strings.Join(hashes, " ") +
				"; style-src 'unsafe-inline'; img-src data:; base-uri 'none'; frame-ancestors 'none'; form-action 'none'"}, nil
		})
		if err != nil {
			text(w, 503, T(g, "نقشهٔ دفتر آماده نیست. به دفتر برگردید و دوباره تلاش کنید.", "The garden's page is not ready. Go back to the garden and try again."))
			return
		}
		view := d.(viewPage)
		w.Header().Set("Content-Security-Policy", view.csp)
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		_, _ = io.WriteString(w, view.page)
	default:
		reply(w, 404, map[string]any{"error": T(g, "یافت نشد.", "Not found.")})
	}
}

func (s *Server) pass(w http.ResponseWriter, g *Garden, method string, params map[string]any) {
	raw, err := s.call(g, method, params, 2*time.Minute) // a question that reads is answered from memory (held.go)
	if err != nil {
		s.fail(w, g, "read", "", err)
		return
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(raw)
}

func (s *Server) post(w http.ResponseWriter, r *http.Request) {
	g := s.garden(r)
	if g == nil {
		reply(w, 404, map[string]any{"error": T(g, "این دفتر روی این رایانه نیست.", "This garden is not on this machine.")})
		return
	}
	switch r.URL.Path {
	case "/api/stop":
		reply(w, 200, map[string]any{"stopping": true})
		if s.Stop != nil {
			go s.Stop()
		}
	case "/api/sync":
		if g.Syncer != nil {
			g.Syncer.Wake(true)
			reply(w, 200, map[string]any{"sync": g.Syncer.Last()})
			return
		}
		reply(w, 200, map[string]any{"sync": map[string]any{"state": "off"}})
	case "/api/sync/merge": // where the peers and this machine both moved: the merge is the sitting person's, signed
		if g.Syncer == nil {
			reply(w, 404, map[string]any{"error": T(g, "این دفتر با همتایی همگام نمی‌شود.", "This garden syncs with no peer.")})
			return
		}
		s.decide(w, r, g, "sync_merge", "", map[string]any{"who": s.readerOf(r, g)})
	case "/api/notify/test": // a sample notice, raised by this daftard in its user's own session
		if s.Notify == nil {
			reply(w, 503, map[string]any{"error": T(g, "اعلان‌ها در این رایانه در دسترس نیست.", "Notices are not available on this machine.")})
			return
		}
		err := s.Notify(notify.Notice{Title: T(g, "دفتر ", "Garden ") + g.Conf.Me + T(g, " — آزمایش اعلان", " — a test notice"),
			Body: T(g, "اعلان‌های دفتر کار می‌کنند. دکمه، فهرست «منتظر شما» را باز می‌کند.", "The garden's notices work. The button opens “Waiting for you”."), Button: T(g, "باز کردن", "Open"),
			URL: "daftar://go/" + g.Conf.Name})
		if err != nil {
			s.fail(w, g, "notify", "", err)
			return
		}
		reply(w, 200, map[string]any{"shown": true})
	case "/api/labels":
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		key, _ := req["key"].(string)
		words, _ := req["text"].(string)
		was, _ := req["was"].(string)
		if !labelRe.MatchString(key) || len(key) > 80 || !plainLine(words) || utf8.RuneCountInString(words) > 200 ||
			!plainLine(was) || utf8.RuneCountInString(was) > 200 {
			reply(w, 400, map[string]any{"error": T(g, "برچسب معتبر نیست: یک سطر، بی نویسهٔ کنترلی، تا دویست نویسه.", "Not a label: one line, no control character, up to two hundred characters.")})
			return
		}
		if g.Custom == nil {
			reply(w, 503, map[string]any{"error": T(g, "برچسب‌ها در این دفتر نگه داشته نمی‌شوند.", "Labels are not kept in this garden.")})
			return
		}
		_, env, done, ok := s.signing(w, r, g)
		if !ok {
			return
		}
		err := g.Custom.Set(s.readerOf(r, g), key, strings.TrimSpace(words), was, env...)
		done()
		if err != nil {
			s.fail(w, g, "settings", "", err)
			return
		}
		s.changed(g) // the person's other open pages read their labels again
		if g.Syncer != nil {
			g.Syncer.Wake(false) // and their other machines, after the next step
		}
		reply(w, 200, map[string]any{"labels": s.labelsOf(r, g)})
	case "/api/pending/decide":
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		id, _ := req["id"].(string)
		request, _ := req["request"].(string)
		if !(slugRe.MatchString(id) || needRe.MatchString(id)) || !uuidRe.MatchString(request) {
			reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
			return
		}
		bean, _, _ := strings.Cut(id, ".") // a need's landing names its bean first: whom a refusal is followed up with
		s.decide(w, r, g, "decide_pending", bean, map[string]any{"id": id, "decision": req["decision"], "words": req["words"],
			"digest": req["digest"], "request": request})
	case "/api/passkey/take": // the gardener names a person's passkey in their bean (class F), in their sitting
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		id, _ := req["id"].(string)
		request, _ := req["request"].(string)
		if !passkeyRe.MatchString(id) || !uuidRe.MatchString(request) {
			reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
			return
		}
		s.decide(w, r, g, "take_passkey", id, map[string]any{"id": id, "request": request})
	case "/api/form/take": // the gardener's save takes a person's own words into the garden (class D), in their sitting
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		id, _ := req["id"].(string)
		request, _ := req["request"].(string)
		if !formRe.MatchString(id) || !uuidRe.MatchString(request) {
			reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
			return
		}
		s.decide(w, r, g, "take_form", id, map[string]any{"id": id, "request": request})
	case "/api/proposal/take":
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		id, _ := req["id"].(string)
		request, _ := req["request"].(string)
		if !proposalRe.MatchString(id) || !uuidRe.MatchString(request) {
			reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
			return
		}
		s.decide(w, r, g, "take_proposal", id, map[string]any{"id": id, "fingerprint": req["fingerprint"], "request": request})
	case "/api/sitting/begin": // who is at the keyboard: one of this garden's writers, by their key's passphrase
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		person, _ := req["person"].(string)
		pass, _ := req["passphrase"].(string)
		switch {
		case s.Sittings == nil || !writes(g, person):
			reply(w, 403, map[string]any{"error": say(g, "nobody")})
		case !s.Keys.Has(person):
			reply(w, 409, map[string]any{"error": say(g, "nokey"), "key": false})
		case !s.Keys.Unlocks(person, pass, s.Askpass):
			reply(w, 403, map[string]any{"error": say(g, "wrong")})
		default:
			if c, err := r.Cookie(sittingCookie); err == nil {
				s.Sittings.End(c.Value) // one sitting a page: the one before ends
			}
			cookie := s.Sittings.Begin(person, pass)
			http.SetCookie(w, &http.Cookie{Name: sittingCookie, Value: cookie, Path: "/", HttpOnly: true,
				SameSite: http.SameSiteStrictMode})
			reply(w, 200, map[string]any{"person": person})
		}
	case "/api/sitting/end":
		if c, err := r.Cookie(sittingCookie); err == nil && s.Sittings != nil {
			s.Sittings.End(c.Value)
		}
		http.SetCookie(w, &http.Cookie{Name: sittingCookie, Value: "", Path: "/", MaxAge: -1, HttpOnly: true,
			SameSite: http.SameSiteStrictMode})
		reply(w, 200, map[string]any{"person": nil})
	case "/api/keys/make": // a writer's key, made on this machine under their passphrase; its fingerprint for the gardener
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		person, _ := req["person"].(string)
		pass, _ := req["passphrase"].(string)
		if s.Keys == nil || !writes(g, person) {
			reply(w, 403, map[string]any{"error": say(g, "nobody")})
			return
		}
		if s.Keys.Has(person) {
			reply(w, 409, map[string]any{"error": say(g, "haskey")})
			return
		}
		fpr, err := s.Keys.Make(person, pass, s.Askpass)
		if err != nil {
			s.fail(w, g, "settings", person, fmt.Errorf("%s %w", say(g, "keyfault"), err))
			return
		}
		// what the gardener adds to the person's bean: a name the namespace ssh gives once, an identity (class F)
		reply(w, 200, map[string]any{"person": person, "fingerprint": fpr,
			"statement": fmt.Sprintf(`name: { by: ssh, of: self, as: "%s" }`, fpr)})
	case "/api/action": // run an action's engine, or ratify or decline its plan: the sitting person's act (bin/act.py)
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		id, _ := req["id"].(string)
		do, _ := req["do"].(string)
		if !actionRe.MatchString(id) || (do != "run" && do != "ratify" && do != "decline") {
			reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
			return
		}
		s.decide(w, r, g, "act", id, map[string]any{"id": id, "do": do, "who": s.readerOf(r, g)})
	case "/api/view/write": // a page's Save, by the view's one write path (viewpages.go)
		s.viewWrite(w, r, g)
	case "/api/view/act": // a page's action started, or its plan decided (viewpages.go)
		s.viewAct(w, r, g)
	case "/api/prefs": // the person's own way of reading, kept on this machine (prefs.go)
		s.prefsSet(w, r, g)
	case "/api/save":
		req, ok := readJSON(w, r)
		if !ok {
			return
		}
		sign, _, done, ok := s.signing(w, r, g)
		if !ok {
			return
		}
		params := map[string]any{"body": req}
		if sign != nil {
			params["sign"] = sign
		}
		raw, err := g.Worker.Call("save", params, 5*time.Minute)
		done()
		if err != nil {
			bean, _ := req["bean"].(string)
			s.fail(w, g, "save", bean, err)
			return
		}
		s.changed(g) // open pages hear of it at once
		if g.Syncer != nil {
			g.Syncer.Wake(false) // what was saved reaches the hub soon after
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		_, _ = w.Write(raw)
	default:
		reply(w, 404, map[string]any{"error": T(g, "یافت نشد.", "Not found.")})
	}
}

// Leads is what waits for a person's decision in a garden: the worker's (parked decisions, proposals no consent
// covers or set aside) and, from the syncer, a hub whose history parted from this garden's (class J). The handplace
// lists them; the notifier announces each new one.
func Leads(g *Garden) ([]map[string]any, error) {
	raw, err := g.Worker.Call("leads", nil, 2*time.Minute)
	if err != nil {
		return nil, err
	}
	var list []map[string]any
	if err := json.Unmarshal(raw, &list); err != nil {
		return nil, err
	}
	if g.Syncer != nil {
		if last := g.Syncer.Last(); last["state"] == "diverged" || last["state"] == "refused" {
			list = append(list, map[string]any{"kind": "sync", "id": "", "state": last["state"], "why": last["why"],
				"at": last["at"], "peers": last["peers"]})
		}
	}
	if list == nil {
		list = []map[string]any{}
	}
	return list, nil
}

// decide runs one of the gardener's decisions through the worker: like a save, it is heard by open pages at once and
// reaches the hub soon after.
func (s *Server) decide(w http.ResponseWriter, r *http.Request, g *Garden, method, bean string, params map[string]any) {
	sign, _, done, ok := s.signing(w, r, g)
	if !ok {
		return
	}
	if sign != nil {
		params["sign"] = sign
	}
	raw, err := g.Worker.Call(method, params, 15*time.Minute)
	done()
	if err != nil {
		s.fail(w, g, "save", bean, err)
		return
	}
	s.changed(g)
	if g.Syncer != nil {
		g.Syncer.Wake(false)
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	_, _ = w.Write(raw)
}

// readJSON is a change's body: JSON, at most 64 KiB, an object. A refusal is answered here.
func readJSON(w http.ResponseWriter, r *http.Request) (map[string]any, bool) {
	return readJSONMax(w, r, 65536)
}

// readJSONMax is readJSON within a bound of its own: a page's action, which may carry a file (actBodyMax).
func readJSONMax(w http.ResponseWriter, r *http.Request, max int64) (map[string]any, bool) {
	if ct, _, _ := mime.ParseMediaType(r.Header.Get("Content-Type")); ct != "application/json" {
		reply(w, 415, map[string]any{"error": both("قالب درخواست معتبر نیست.", "The request's form is not valid.")})
		return nil, false
	}
	body, err := io.ReadAll(io.LimitReader(r.Body, max+1))
	if err != nil || len(body) == 0 || int64(len(body)) > max {
		reply(w, 413, map[string]any{"error": both("درخواست بیش از اندازه بزرگ است.", "The request is too large.")})
		return nil, false
	}
	var req map[string]any
	if json.Unmarshal(body, &req) != nil || req == nil {
		reply(w, 400, map[string]any{"error": both("درخواست معتبر نیست.", "The request is not valid.")})
		return nil, false
	}
	return req, true
}

// plainLine: one line of text with no control character and no bidi control, which would reorder what is around it
// wherever it is shown (design/TEXT.md).
func plainLine(s string) bool {
	if !utf8.ValidString(s) {
		return false
	}
	for _, c := range s {
		if c < 0x20 || (c >= 0x7f && c <= 0x9f) || c == 0x061c || c == 0x200e || c == 0x200f ||
			(c >= 0x202a && c <= 0x202e) || (c >= 0x2066 && c <= 0x2069) {
			return false
		}
	}
	return true
}

// reader is the person reading the handplace with no sitting begun: the gardener of the gardens this machine serves; a
// sitting names its own person (readerOf), and a served handplace (design P4) its signed-in reader.
func reader(g *Garden) string { return g.Conf.Gardener }

const sittingCookie = "daftard-sitting"

// sittingOf is the sitting the page's cookie names, if one is going on.
func (s *Server) sittingOf(r *http.Request) *sitting.Sitting {
	if s.Sittings == nil {
		return nil
	}
	c, err := r.Cookie(sittingCookie)
	if err != nil {
		return nil
	}
	st, ok := s.Sittings.Get(c.Value)
	if !ok {
		return nil
	}
	return st
}

// readerOf is who reads: the person sitting at the keyboard, where one sits and may sit here; else the gardener.
func (s *Server) readerOf(r *http.Request, g *Garden) string {
	if st := s.sittingOf(r); st != nil && writes(g, st.Person) {
		return st.Person
	}
	return reader(g)
}

// writers are who may sit at this garden's handplace on this machine: daftard.json's, else its gardener.
func writers(g *Garden) []string {
	if len(g.Conf.Writers) > 0 {
		return g.Conf.Writers
	}
	if g.Conf.Gardener != "" {
		return []string{g.Conf.Gardener}
	}
	return nil
}

func writes(g *Garden, person string) bool {
	for _, w := range writers(g) {
		if w == person {
			return true
		}
	}
	return false
}

var said = map[string][2]string{ // what these calls say, in English and in Persian, as the page's language asks
	"sit":      {"Who is at the keyboard? Begin your sitting: your saves here are signed with your own key.", "چه کسی پشت صفحه‌کلید است؟ نشست خود را آغاز کنید: ذخیره‌های شما در اینجا با کلید خودتان امضا می‌شوند."},
	"nobody":   {"No such person sits at this garden's handplace.", "چنین کسی پشت این دفتر نمی‌نشیند."},
	"nokey":    {"This machine keeps no key for this person yet: make one first.", "این رایانه هنوز کلیدی برای این شخص ندارد: نخست یکی بسازید."},
	"wrong":    {"That passphrase does not open this person's key.", "این گذرواژه کلید این شخص را باز نمی‌کند."},
	"haskey":   {"This machine keeps a key for this person already: a new key is a new identity, which the gardener settles.", "این رایانه برای این شخص کلید دارد: کلید تازه هویتی تازه است که باغبان تعیین می‌کند."},
	"keyfault": {"The key could not be made.", "کلید ساخته نشد."},
	"notyours": {"This garden is another person's, and opens to their sitting.", "این دفتر از آنِ کس دیگری است و به نشست او باز می‌شود."},
}

// mayRead says whether the page may read this garden, answering the refusal where not. On a shared machine a garden's
// pages open to its gardener's sitting alone (design §6: one person's sitting does not show another's); reading as far
// as a grant opens a garden's beans to another person is the garden's own model's to filter, and is not done here.
func (s *Server) mayRead(w http.ResponseWriter, r *http.Request, g *Garden) bool {
	if !s.Shared {
		return true
	}
	st := s.sittingOf(r)
	switch {
	case st == nil:
		reply(w, 409, map[string]any{"error": say(g, "sit"), "sitting": true})
		return false
	case st.Person != g.Conf.Gardener:
		reply(w, 403, map[string]any{"error": say(g, "notyours")})
		return false
	}
	return true
}

// sittingState is what the page shows of who sits here: the person sitting, if any, each writer and whether this
// machine keeps their key, and whether the garden takes only signed writes.
func (s *Server) sittingState(r *http.Request, g *Garden) map[string]any {
	var who any
	if st := s.sittingOf(r); st != nil && writes(g, st.Person) {
		who = st.Person
	}
	list := []map[string]any{}
	for _, p := range writers(g) {
		list = append(list, map[string]any{"person": p, "key": s.Keys != nil && s.Keys.Has(p)})
	}
	return map[string]any{"person": who, "writers": list, "signed": g.Conf.Signed}
}

// T is a message in the reader's language (the operator, 2026-10-14: the UI in English too): Persian where the garden
// reads Persian, English where it reads another; with no garden to ask, both.
func T(g *Garden, fa, en string) string {
	if g == nil {
		return both(fa, en)
	}
	if g.Conf.Lang == "" || strings.HasPrefix(g.Conf.Lang, "fa") {
		return fa
	}
	return en
}

// both is a message for a reader whose language nothing tells: Persian, then English.
func both(fa, en string) string { return fa + " — " + en }

func say(g *Garden, key string) string {
	if g != nil && g.Conf.Lang == "fa" {
		return said[key][1]
	}
	return said[key][0]
}

// signing is what a write made in r runs with: the sitting person's authorship and signature, and what to do once it
// is done. With nobody sitting it is the handplace's own write, unsigned — unless the garden takes only signed writes,
// when it is refused here, asking who is at the keyboard (ok false: the answer is written).
func (s *Server) signing(w http.ResponseWriter, r *http.Request, g *Garden) (map[string]string, []string, func(), bool) {
	st := s.sittingOf(r)
	if st == nil || !writes(g, st.Person) || s.Keys == nil || !s.Keys.Has(st.Person) {
		if g.Conf.Signed || s.Shared { // a shared machine's every write is someone's: whose is asked
			reply(w, 409, map[string]any{"error": say(g, "sit"), "sitting": true})
			return nil, nil, nil, false
		}
		return nil, nil, func() {}, true
	}
	name, mail := st.Person, ""
	if g.Worker == nil {
		// no worker to read the person's bean from: their id is how they are called
	} else if raw, err := g.Worker.Call("person", map[string]any{"id": st.Person}, 30*time.Second); err == nil {
		var who map[string]string
		if json.Unmarshal(raw, &who) == nil {
			name, mail = who["title"], who["mail"]
		}
	}
	if mail == "" {
		mail = st.Person + "@" + g.Conf.Name + ".daftar.invalid" // the bean names no mail: an address that is no one's
	}
	tok := s.Askpass.Issue(st.Pass(), 16, 10*time.Minute)
	env := s.Keys.SignEnv(st.Person, name, mail, tok, s.Askpass)
	m := map[string]string{}
	for _, kv := range env {
		if k, v, ok := strings.Cut(kv, "="); ok {
			m[k] = v
		}
	}
	return m, env, func() { s.Askpass.Revoke(tok) }, true
}

// labelsOf are the reader's own labels of this garden: key → {text, was}.
func (s *Server) labelsOf(r *http.Request, g *Garden) map[string]custom.Label {
	if g.Custom == nil {
		return map[string]custom.Label{}
	}
	return g.Custom.Labels(s.readerOf(r, g))
}

var types = map[string]string{".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
	".css": "text/css; charset=utf-8", ".woff2": "font/woff2", ".txt": "text/plain; charset=utf-8", ".svg": "image/svg+xml"}

func (s *Server) asset(w http.ResponseWriter, r *http.Request) {
	name := strings.TrimPrefix(path.Clean(r.URL.Path), "/")
	switch name {
	case "", ".":
		name = "app/index.html" // the handplace on the toolbox
	case "old":
		name = "index.html" // the earlier pages, kept while the new ones settle
	}
	if name == "go" || strings.HasPrefix(name, "go/") { // a landing address: the handplace, which reads its case
		if !GoRe.MatchString(r.URL.Path) {
			text(w, 404, both("این نشانی در دفتر معنایی ندارد.", "This address means nothing in the garden."))
			return
		}
		name = "app/index.html"
	}
	kind, ok := types[path.Ext(name)]
	if !ok || strings.Contains(name, "..") {
		text(w, 404, both("یافت نشد.", "Not found."))
		return
	}
	b, err := fs.ReadFile(s.Assets, name)
	if err != nil {
		text(w, 404, both("یافت نشد.", "Not found."))
		return
	}
	w.Header().Set("Content-Type", kind)
	if path.Ext(name) == ".woff2" {
		w.Header().Set("Cache-Control", "max-age=31536000, immutable")
	} else {
		w.Header().Set("Cache-Control", "no-cache")
	}
	_, _ = w.Write(b)
}

// Handler returns the server ready to serve.
func (s *Server) Handler() http.Handler {
	s.init()
	return s
}
