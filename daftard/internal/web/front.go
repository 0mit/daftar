package web

import (
	"bytes"
	"encoding/json"
	"io"
	"net/http"
	"net/url"
	"strings"
	"time"
)

// THE MACHINE'S FRONT DOOR. With one daftard per garden, the machine's own address (daftard.json `listen`) is kept by
// the machine's daftard, which serves no garden's pages: it opens the door to each garden's own daemon, where that
// garden's pages are answered from its memory. `daftard open` and the desktop's shortcut knock here as before; the
// one-time code is spent here, and the browser is sent on to the garden's daemon with a code of that daemon's own. Any
// other address of a garden is sent on as it is. Its own: /health (and each daemon's), the machine's key's /door and
// /api/session, /api/stop, and Odoo's seats (/internal/odoo-issue), which the machine's Odoo origin redeems.

// Daemon is a garden's own daftard as the machine's knows it.
type Daemon struct {
	Name string
	Addr string // its address on the loopback
}

// FrontHandler is the machine's front door.
func (s *Server) FrontHandler(daemons []Daemon) http.Handler {
	s.init() // its one-time codes, as a garden's handplace keeps its own
	byName := map[string]Daemon{}
	for _, d := range daemons {
		byName[d.Name] = d
	}
	pick := func(q url.Values) (Daemon, bool) {
		if d, ok := byName[q.Get("g")]; ok {
			return d, true
		}
		if to := q.Get("to"); strings.HasPrefix(to, "/go/") {
			if d, ok := byName[strings.SplitN(strings.TrimPrefix(to, "/go/"), "/", 2)[0]]; ok {
				return d, true
			}
		}
		if len(daemons) > 0 {
			return daemons[0], true
		}
		return Daemon{}, false
	}
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !s.local(r) {
			text(w, 403, both("دسترسی مجاز نیست.", "Access is not allowed."))
			return
		}
		p, q := r.URL.Path, r.URL.Query()
		switch {
		case p == "/health" && q.Get("quick") != "": // a garden's daemon looking whether the machine's daftard is there
			reply(w, 200, map[string]any{"build": s.Build, "front": true})
		case p == "/health":
			gardens := map[string]any{}
			for _, d := range daemons {
				gardens[d.Name] = daemonHealth(d.Addr)
			}
			reply(w, 200, map[string]any{"build": s.Build, "front": true, "gardens": gardens, "odoo": s.Odoo != nil})
		case p == "/door" && r.Method == http.MethodPost:
			if !same(r.Header.Get(keyHeader), s.Token) {
				reply(w, 403, map[string]any{"error": both("کلید معتبر نیست.", "The key is not valid.")})
				return
			}
			reply(w, 200, map[string]any{"once": s.issueOnce(time.Now())})
		case p == "/api/session" && same(r.Header.Get(keyHeader), s.Token):
			reply(w, 200, map[string]any{"csrf": s.CSRF, "front": true})
		case p == "/api/stop" && r.Method == http.MethodPost:
			if !same(r.Header.Get(keyHeader), s.Token) || r.Header.Get("X-CSRF-Token") != s.CSRF {
				reply(w, 403, map[string]any{"error": both("دسترسی مجاز نیست.", "Access is not allowed.")})
				return
			}
			reply(w, 200, map[string]any{"stopping": true})
			if s.Stop != nil {
				go s.Stop()
			}
		case p == "/internal/odoo-issue" && r.Method == http.MethodPost:
			s.odooIssue(w, r)
		case p == "/" && q.Get("once") != "":
			if !s.spendOnce(q.Get("once"), time.Now()) {
				text(w, 403, both("این پیوند دیگر معتبر نیست؛ دفتر را از میان‌بر روی میز کار باز کنید.", "This link is no longer good: open the garden from the desktop shortcut."))
				return
			}
			d, ok := pick(q)
			if !ok {
				text(w, 404, both("این دفتر روی این رایانه نیست.", "This garden is not on this machine."))
				return
			}
			once, err := daemonOnce(d.Addr, s.Token)
			if err != nil {
				text(w, 503, both("دفتر هنوز آماده نیست؛ چند لحظهٔ دیگر دوباره باز کنید.", "The garden is not ready yet: open it again in a moment."))
				return
			}
			v := url.Values{"once": {once}, "g": {d.Name}}
			for _, f := range []string{"to", "debug", "admin", "static"} {
				if x := q.Get(f); x != "" {
					v.Set(f, x)
				}
			}
			http.Redirect(w, r, "http://"+d.Addr+"/?"+v.Encode(), http.StatusSeeOther) // the code leaves the history
		case r.Method == http.MethodGet:
			d, ok := pick(q)
			if strings.HasPrefix(p, "/go/") || strings.HasPrefix(p, "/release/") {
				if x, found := byName[strings.SplitN(strings.SplitN(p, "/", 3)[2], "/", 2)[0]]; found {
					d, ok = x, true
				}
			}
			if !ok {
				text(w, 404, both("این دفتر روی این رایانه نیست.", "This garden is not on this machine."))
				return
			}
			http.Redirect(w, r, "http://"+d.Addr+r.URL.RequestURI(), http.StatusFound)
		default:
			reply(w, 404, map[string]any{"error": both("یافت نشد.", "Not found.")})
		}
	})
}

// local: the front door answers this machine's own browser and command line alone (it listens on the loopback).
func (s *Server) local(r *http.Request) bool {
	return r.Host == s.Listen || strings.HasPrefix(r.Host, "localhost:") || strings.HasPrefix(r.Host, "127.0.0.1:")
}

func daemonHealth(addr string) any {
	resp, err := (&http.Client{Timeout: time.Second}).Get("http://" + addr + "/health")
	if err != nil {
		return map[string]any{"running": false, "listen": addr}
	}
	defer resp.Body.Close()
	var h map[string]any
	_ = json.NewDecoder(io.LimitReader(resp.Body, 1<<20)).Decode(&h)
	if h == nil {
		h = map[string]any{}
	}
	h["running"], h["listen"] = true, addr
	return h
}

// daemonOnce is a one-time code of a garden's daemon, asked with the machine's key.
func daemonOnce(addr, token string) (string, error) {
	req, err := http.NewRequest(http.MethodPost, "http://"+addr+"/door", nil)
	if err != nil {
		return "", err
	}
	req.Header.Set(keyHeader, token)
	resp, err := (&http.Client{Timeout: 10 * time.Second}).Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var got struct {
		Once string `json:"once"`
	}
	if resp.StatusCode != http.StatusOK || json.NewDecoder(io.LimitReader(resp.Body, 4096)).Decode(&got) != nil || got.Once == "" {
		return "", &url.Error{Op: "door", URL: addr, Err: io.ErrUnexpectedEOF}
	}
	return got.Once, nil
}

// odooIssue is a seat at Odoo's origin, issued here — where the origin redeems it — for a garden's daemon that opens
// the door to it (OdooDoor.Issuer).
func (s *Server) odooIssue(w http.ResponseWriter, r *http.Request) {
	if !same(r.Header.Get(keyHeader), s.Token) || s.Odoo == nil {
		reply(w, 403, map[string]any{"error": both("دسترسی مجاز نیست.", "Access is not allowed.")})
		return
	}
	var req struct{ Garden, Series, Reader, Asof string }
	if json.NewDecoder(io.LimitReader(r.Body, 1<<16)).Decode(&req) != nil {
		reply(w, 400, map[string]any{"error": both("درخواست معتبر نیست.", "The request is not valid.")})
		return
	}
	tok, ok := s.Odoo.issue(req.Garden, req.Series, req.Reader, req.Asof, time.Now())
	if !ok {
		reply(w, 503, map[string]any{"error": both("اکنون نمی‌شود.", "Not now.")})
		return
	}
	reply(w, 200, map[string]any{"token": tok})
}

// FrontIssuer issues Odoo's seats at the machine's front door, for a garden's daemon.
func FrontIssuer(front, token string) func(garden, series, reader, asof string) (string, bool) {
	return func(garden, series, reader, asof string) (string, bool) {
		b, _ := json.Marshal(map[string]string{"Garden": garden, "Series": series, "Reader": reader, "Asof": asof})
		req, err := http.NewRequest(http.MethodPost, "http://"+front+"/internal/odoo-issue", bytes.NewReader(b))
		if err != nil {
			return "", false
		}
		req.Header.Set(keyHeader, token)
		resp, err := (&http.Client{Timeout: 10 * time.Second}).Do(req)
		if err != nil {
			return "", false
		}
		defer resp.Body.Close()
		var got struct {
			Token string `json:"token"`
		}
		if resp.StatusCode != http.StatusOK || json.NewDecoder(io.LimitReader(resp.Body, 4096)).Decode(&got) != nil {
			return "", false
		}
		return got.Token, got.Token != ""
	}
}
