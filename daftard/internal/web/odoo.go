package web

// ODOO'S OWN WEB CLIENT, SERVED BY DAFTARD (design §10.2, P5.2). Its search components and the views that hold them
// run unchanged: the series' client, compiled by that series' own Community instance and taken by
// importers/odoo/client.py into this machine's state folder (odoo/<series>/), is served as it came; every call it makes
// is answered here, by the garden's worker (odoo_rpc), from the views the garden captured and the records its reader
// may read. Nothing is forwarded to an Odoo.
//
// AN ORIGIN OF ITS OWN (security audit 2026-10-10, 2.1). A captured view is the garden's data, and Odoo's client
// compiles its Owl expressions as script: whoever can commit a capture could run script wherever the client runs. So
// the client never runs in the handplace's origin. The handplace (127.0.0.1:<port>, the machine's key, a sitting) keeps
// only a door, `/odoo`: it decides the garden, the series and the reader, and sends the browser to Odoo's own origin
// (localhost:<odoo port>, another site, so the machine key's SameSite=Strict cookie is never sent there and no page
// there can read the handplace) with a one-time token, which becomes a short session bound to those three and nothing
// else. What runs there can read what that reader may read in that garden, and do nothing.

import (
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"net/http"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/worker"
)

// odooCSP lets the client compile its templates (Owl builds them with `new Function`) and set its own styles; it
// still loads nothing from anywhere but this server.
const odooCSP = "default-src 'self'; script-src 'self' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; " +
	"img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self'; worker-src 'self' blob:; " +
	"base-uri 'none'; frame-ancestors 'none'; form-action 'self'"

const odooCookie = "daftard-odoo"

// odooEnterPage is the page /odoo/enter answers once its token became a seat: it moves on to /odoo at once (a refresh,
// which odooCSP leaves alone), and offers the same as a link where a browser holds refreshes back.
const odooEnterPage = `<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8"/>` +
	`<meta http-equiv="refresh" content="0; url=/odoo"/><title>اودو</title></head>` +
	`<body><p><a href="/odoo">ورود به اودو</a></p></body></html>`

var seriesRe = regexp.MustCompile(`^\d{2}\.\d$`)
var langRe = regexp.MustCompile(`^[a-z]{2,3}(_[A-Z]{2})?(@[a-z]+)?$`)

// seriesMajor is a series' major number: 17 of "17.0".
func seriesMajor(series string) int {
	n := 0
	for _, c := range series {
		if c < '0' || c > '9' {
			break
		}
		n = n*10 + int(c-'0')
	}
	return n
}

// FROM SERIES 19 the client routes itself under /odoo/<path> (a reload asks for that path), asks its menus and its
// translations with no path segment of their own, loads some bundles only when a page needs one (/web/bundle/<name>),
// and reads what each kind of view is called from its session (`view_info`). importers/odoo/client.py takes those for
// 19; a 17 seat is served as before.
func modernOdoo(series string) bool { return seriesMajor(series) >= 19 }

// odooOwn says whether a path under /odoo is daftard's own part of Odoo's origin, never one of 19's client routes.
func odooOwn(p string) bool {
	return p == "/odoo/session.js" || p == "/odoo/daftar.js" || p == "/odoo/asof" || p == "/odoo/enter"
}

var bundleRe = regexp.MustCompile(`^/web/bundle/([a-z][a-z0-9_]*(\.[a-z0-9_]+)+)$`)

// odooClientInfo is what CLIENT.json says of a series' client: the languages taken (and their direction), and, from
// 19, what each kind of view is called in each of them.
type odooClientInfo struct {
	Languages map[string]string          `json:"languages"`
	ViewInfo  map[string]json.RawMessage `json:"view_info"`
}

func (s *Server) odooInfo(series string) odooClientInfo {
	var c odooClientInfo
	if b, err := os.ReadFile(s.odooClient(series, "CLIENT.json")); err == nil {
		_ = json.Unmarshal(b, &c)
	}
	return c
}

// odooLang is the Odoo language the garden's page speaks, and its direction: the garden's own language where the
// series' client was taken with Odoo's translations of it, else English.
func (s *Server) odooLang(g *Garden, series string) (string, string) {
	c := s.odooInfo(series)
	want := g.Conf.Lang
	if full, ok := map[string]string{"fa": "fa_IR", "tr": "tr_TR", "en": "en_US", "": "en_US"}[want]; ok {
		want = full
	}
	if dir, ok := c.Languages[want]; ok && langRe.MatchString(want) {
		if dir != "rtl" {
			dir = "ltr"
		}
		return want, dir
	}
	return "en_US", "ltr"
}

var odooStatic = regexp.MustCompile(`^/[a-z0-9_]+/static/[A-Za-z0-9_./@+-]+$`)

// isOdoo says whether a path is one the Odoo client asks of its server: daftard's own under /odoo, and from 19 the
// client's own routes under it.
func isOdoo(p string) bool {
	return p == "/odoo" || p == "/odoo/session.js" || p == "/odoo/daftar.js" || p == "/odoo/asof" ||
		strings.HasPrefix(p, "/odoo/") || strings.HasPrefix(p, "/web/") || strings.HasPrefix(p, "/mail/") ||
		odooStatic.MatchString(p)
}

// OdooDoor carries a page from the handplace to Odoo's own origin: one-time tokens, and the sessions they become there,
// each bound to a garden, a series and a reader decided at the handplace. Kept in memory, by their digests only.
type OdooDoor struct {
	Host string // Odoo's origin as a browser names it, localhost:<port>
	// Issuer issues a seat where Odoo's origin redeems it: in a garden's own daemon, the machine's front door, which
	// keeps the origin (one daemon per garden); nil: here
	Issuer   func(garden, series, reader, asof string) (string, bool)
	mu       sync.Mutex
	tokens   map[string]odooSeat
	sessions map[string]*odooSeat
}

type odooSeat struct {
	garden, series, reader string
	asof                   string // the commit the reader sees the garden as of (design §10.3); empty: now
	until, since, last     time.Time
}

const (
	odooTokenLife = time.Minute      // a door's token: used at once, or not at all
	odooIdle      = 30 * time.Minute // a seat unused this long is given up
	odooLife      = 8 * time.Hour
	odooMax       = 256 // tokens, and seats, held at once at most
)

// NewOdooDoor is the door to Odoo's origin at `host` (localhost:<port>).
func NewOdooDoor(host string) *OdooDoor {
	return &OdooDoor{Host: host, tokens: map[string]odooSeat{}, sessions: map[string]*odooSeat{}}
}

func odooRandom() string {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		panic(err) // no randomness: nothing may be served
	}
	return base64.RawURLEncoding.EncodeToString(b)
}

func odooDigest(t string) string {
	d := sha256.Sum256([]byte(t))
	return hex.EncodeToString(d[:])
}

func (d *OdooDoor) sweep(now time.Time) {
	for k, t := range d.tokens {
		if now.After(t.until) {
			delete(d.tokens, k)
		}
	}
	for k, se := range d.sessions {
		if now.Sub(se.last) > odooIdle || now.Sub(se.since) > odooLife {
			delete(d.sessions, k)
		}
	}
}

func (d *OdooDoor) issue(garden, series, reader, asof string, now time.Time) (string, bool) {
	if d.Issuer != nil {
		return d.Issuer(garden, series, reader, asof)
	}
	d.mu.Lock()
	defer d.mu.Unlock()
	d.sweep(now)
	if len(d.tokens) >= odooMax {
		return "", false
	}
	t := odooRandom()
	d.tokens[odooDigest(t)] = odooSeat{garden: garden, series: series, reader: reader, asof: asof, until: now.Add(odooTokenLife)}
	return t, true
}

func (d *OdooDoor) redeem(t string, now time.Time) (string, bool) {
	d.mu.Lock()
	defer d.mu.Unlock()
	d.sweep(now)
	k := odooDigest(t)
	seat, ok := d.tokens[k]
	delete(d.tokens, k)
	if !ok || now.After(seat.until) || len(d.sessions) >= odooMax {
		return "", false
	}
	sid := odooRandom()
	seat.since, seat.last = now, now
	d.sessions[odooDigest(sid)] = &seat
	return sid, true
}

// lookAt sets the commit the seat's reader sees the garden as of ("" for now): narrowing what the seat reads to a past
// state of the same garden, for the same reader and series, never anything more.
func (d *OdooDoor) lookAt(sid, asof string, now time.Time) bool {
	d.mu.Lock()
	defer d.mu.Unlock()
	se, ok := d.sessions[odooDigest(sid)]
	if !ok || now.Sub(se.last) > odooIdle || now.Sub(se.since) > odooLife {
		return false
	}
	se.asof, se.last = asof, now
	return true
}

func (d *OdooDoor) seat(sid string, now time.Time) (odooSeat, bool) {
	d.mu.Lock()
	defer d.mu.Unlock()
	se, ok := d.sessions[odooDigest(sid)]
	if !ok || now.Sub(se.last) > odooIdle || now.Sub(se.since) > odooLife {
		delete(d.sessions, odooDigest(sid))
		return odooSeat{}, false
	}
	se.last = now
	return *se, true
}

// odooOpen is the handplace's door: the page for one garden and one series, opened by whoever may read the garden
// here, carried to Odoo's own origin by a one-time token.
func (s *Server) odooOpen(w http.ResponseWriter, r *http.Request) {
	g := s.garden(r)
	series := r.URL.Query().Get("series")
	if series == "" {
		series = "17.0"
	}
	if g == nil || g.Worker == nil || !seriesRe.MatchString(series) {
		text(w, 404, T(g, "این دفتر روی این رایانه نیست.", "This garden is not on this machine."))
		return
	}
	if !s.mayRead(w, r, g) {
		return
	}
	if _, err := os.Stat(s.odooClient(series, "CLIENT.json")); err != nil {
		text(w, 404, T(g, "کارخواه اودوی این سری روی این رایانه گرفته نشده است (importers/odoo/client.py).", "This series' Odoo client is not taken on this machine (importers/odoo/client.py)."))
		return
	}
	asof := ""
	if at := r.URL.Query().Get("asof"); at != "" { // the page opened as of a commit or a moment (design §10.3)
		commit, _, err := s.odooAsof(g, at)
		if err != nil {
			s.fail(w, g, "read", "", err)
			return
		}
		asof = commit
	}
	tok, ok := s.Odoo.issue(g.Conf.Name, series, s.readerOf(r, g), asof, time.Now())
	if !ok {
		text(w, 503, T(g, "اکنون نمی‌شود؛ کمی بعد دوباره باز کنید.", "Not now: open it again in a little while."))
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	http.Redirect(w, r, "http://"+s.Odoo.Host+"/odoo/enter?t="+url.QueryEscape(tok), http.StatusSeeOther)
}

// odooScreens is what a garden of the core offers on its front page (the worker's `payload` for such a garden): each
// Odoo series it captured the views of, and the series of its register, marked with whether this machine opens it —
// the series' client taken here (importers/odoo/client.py) and Odoo's own origin listening.
func (s *Server) odooScreens(data map[string]any) {
	opens := func(series string) bool {
		if s.Odoo == nil || s.OdooDir == "" || !seriesRe.MatchString(series) {
			return false
		}
		_, err := os.Stat(s.odooClient(series, "CLIENT.json"))
		return err == nil
	}
	list, _ := data["odoo"].([]any)
	out := []map[string]any{}
	for _, x := range list {
		if series, _ := x.(string); seriesRe.MatchString(series) {
			out = append(out, map[string]any{"series": series, "opens": opens(series)})
		}
	}
	data["odoo"] = out
	if reg, ok := data["register"].(map[string]any); ok {
		series, _ := reg["series"].(string)
		reg["opens"] = opens(series)
	}
}

// OdooHandler is Odoo's own origin: the client and the calls it makes, for the seat its session was given at the
// handplace's door, and nothing else of the handplace.
func (s *Server) OdooHandler() http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Security-Policy", odooCSP)
		w.Header().Set("X-Content-Type-Options", "nosniff")
		w.Header().Set("Referrer-Policy", "no-referrer")
		if s.Odoo == nil || r.Host != s.Odoo.Host {
			text(w, 403, both("دسترسی مجاز نیست.", "Access is not allowed."))
			return
		}
		now := time.Now()
		if r.URL.Path == "/odoo/enter" && r.Method == http.MethodGet {
			sid, ok := s.Odoo.redeem(r.URL.Query().Get("t"), now)
			if !ok {
				text(w, 403, both("این پیوند دیگر معتبر نیست؛ اودو را دوباره از دفتر باز کنید.", "This link is no longer good: open Odoo from the garden again."))
				return
			}
			http.SetCookie(w, &http.Cookie{Name: odooCookie, Value: sid, Path: "/", HttpOnly: true, SameSite: http.SameSiteStrictMode})
			// THE LAST STEP IS THIS ORIGIN'S OWN. The way here is cross-site from its start (the handplace's 127.0.0.1, its
			// door, a redirect to localhost), and a browser that holds SameSite to the whole of a redirect chain — Firefox
			// does — sends no Strict cookie on any later hop of it: a 303 to /odoo arrived without the seat it had just
			// set, and the page said to open Odoo from the handplace (2026-10-12). So the chain ends here, on a page of
			// Odoo's own origin, and that page moves on to /odoo itself: a navigation this origin begins, which carries
			// its own Strict cookie in every browser. The token leaves the address bar with it.
			w.Header().Set("Content-Type", "text/html; charset=utf-8")
			w.Header().Set("Cache-Control", "no-store")
			fmt.Fprint(w, odooEnterPage)
			return
		}
		c, err := r.Cookie(odooCookie)
		var seat odooSeat
		ok := err == nil
		if ok {
			seat, ok = s.Odoo.seat(c.Value, now)
		}
		if !ok {
			text(w, 403, both("اودو را از دفتر باز کنید.", "Open Odoo from the garden."))
			return
		}
		var g *Garden
		for _, x := range s.Gardens {
			if x.Conf.Name == seat.garden && x.Worker != nil {
				g = x
			}
		}
		if g == nil || !isOdoo(r.URL.Path) {
			text(w, 404, T(g, "پیدا نشد.", "Not found."))
			return
		}
		// its calls are taken only from its own pages (Origin) and only as JSON
		if r.Method == http.MethodPost && (r.Header.Get("Origin") != "http://"+s.Odoo.Host ||
			!strings.HasPrefix(r.Header.Get("Content-Type"), "application/json")) {
			reply(w, 403, map[string]any{"error": T(g, "نشست معتبر نیست؛ صفحه را دوباره باز کنید.", "The session is not valid: open the page again.")})
			return
		}
		if r.URL.Path == "/odoo/asof" && r.Method == http.MethodPost { // the reader looks at another moment of the garden
			s.odooLookAt(w, r, g, c.Value, now)
			return
		}
		s.odoo(w, r, g, seat)
	})
}

func (s *Server) odoo(w http.ResponseWriter, r *http.Request, g *Garden, seat odooSeat) {
	series, reader, p := seat.series, seat.reader, r.URL.Path
	modern := modernOdoo(series)
	page := p == "/odoo" || modern && strings.HasPrefix(p, "/odoo/") && !odooOwn(p)
	if page && r.Method == http.MethodGet { // the page, for the seat's garden and series (from 19, at any of its routes)
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		lang, dir := s.odooLang(g, series)
		sheet := "/web/assets/debug/web.assets_web.css"
		if dir == "rtl" {
			sheet = "/web/assets/debug/web.assets_web.rtl.css"
		}
		fmt.Fprint(w, `<!DOCTYPE html><html lang="`+htmlEscape(strings.ReplaceAll(lang, "_", "-"))+`" dir="`+dir+`"><head>`+
			`<meta charset="utf-8"/><title>`+htmlEscape(g.Conf.Title)+`</title>`+
			`<script src="/odoo/session.js"></script>`+
			`<link rel="stylesheet" href="`+sheet+`"/>`+
			`<script src="/web/assets/debug/web.assets_web.js"></script>`+
			`<script src="/odoo/daftar.js"></script></head><body class="o_web_client"></body></html>`)
		return
	}
	switch {
	case p == "/odoo/daftar.js": // daftard's own part of the page: the moment the garden is read as of (design §10.3)
		b, err := fs.ReadFile(s.Assets, "odoo/daftar.js")
		if err != nil {
			text(w, 404, "")
			return
		}
		w.Header().Set("Content-Type", "text/javascript; charset=utf-8")
		w.Header().Set("Cache-Control", "no-cache")
		_, _ = w.Write(b)
	case p == "/odoo/session.js":
		lang, _ := s.odooLang(g, series)
		params := map[string]any{"reader": reader, "series": series, "lang": lang, "asof": seat.asof}
		menus := "/web/webclient/load_menus/daftar"
		if modern { // 19's menus have no path segment; what each view is called, in the page's language
			menus = "/web/webclient/load_menus"
			if vi, ok := s.odooInfo(series).ViewInfo[lang]; ok {
				params["view_info"] = vi
			}
		}
		raw, err := g.Worker.Call("odoo_session", params, time.Minute)
		if err != nil {
			s.fail(w, g, "read", "", err)
			return
		}
		w.Header().Set("Content-Type", "text/javascript; charset=utf-8")
		w.Header().Set("Cache-Control", "no-store")
		load := fmt.Sprintf("fetch(%q)", menus)
		if modern { // as 19's own page asks them: never from a cache
			load = fmt.Sprintf("fetch(%q, {cache: \"no-store\"})", menus)
		}
		fmt.Fprintf(w, "var odoo = {csrf_token: \"\", debug: \"\"};\nodoo.__session_info__ = %s;\n"+
			"odoo.reloadMenus = () => %s.then(r => r.json());\n"+
			"odoo.loadMenusPromise = odoo.reloadMenus();\n", raw, load)
	case r.Method == http.MethodGet && (strings.HasPrefix(p, "/web/webclient/translations/") ||
		modern && p == "/web/webclient/translations"):
		// Odoo's own translations of its client, as the instance gave them; English is the client's own words
		lang := r.URL.Query().Get("lang")
		if langRe.MatchString(lang) { // the name checked before any file is opened by it (security audit 2.6)
			if b, err := os.ReadFile(s.odooClient(series, "translations/"+lang+".json")); err == nil {
				w.Header().Set("Content-Type", "application/json; charset=utf-8")
				_, _ = w.Write(b)
				return
			}
		}
		s.pass(w, g, "odoo_rpc", map[string]any{"path": p, "reader": reader, "series": series})
	case r.Method == http.MethodGet && (strings.HasPrefix(p, "/web/webclient/load_menus/") ||
		modern && p == "/web/webclient/load_menus"):
		lang, _ := s.odooLang(g, series)
		s.pass(w, g, "odoo_rpc", map[string]any{"path": p, "reader": reader, "series": series, "lang": lang})
	case r.Method == http.MethodGet && modern && strings.HasPrefix(p, "/web/bundle/"):
		// a bundle 19's client loads when a page needs it: its definition as the instance gave it, the files it names
		// served as the client's own (importers/odoo/client.py took both); a name that is not a bundle's opens nothing
		m := bundleRe.FindStringSubmatch(p)
		if m == nil {
			text(w, 404, "")
			return
		}
		b, err := os.ReadFile(s.odooClient(series, "bundles/"+m[1]+".json"))
		if err != nil {
			text(w, 404, "")
			return
		}
		w.Header().Set("Content-Type", "application/json; charset=utf-8")
		w.Header().Set("Cache-Control", "no-cache")
		_, _ = w.Write(b)
	case r.Method == http.MethodGet && strings.HasPrefix(p, "/web/image"):
		w.Header().Set("Content-Type", "image/svg+xml")
		fmt.Fprint(w, `<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>`)
	case r.Method == http.MethodGet:
		s.odooFile(w, series, p)
	case r.Method == http.MethodPost:
		s.odooCall(w, r, g, seat)
	default:
		text(w, 405, "")
	}
}

// odooClient is a file of a series' client as importers/odoo/client.py took it.
func (s *Server) odooClient(series string, rel string) string {
	return filepath.Join(s.OdooDir, series, filepath.FromSlash(rel))
}

// odooFile serves a file of the series' client, as it came.
func (s *Server) odooFile(w http.ResponseWriter, series, p string) {
	clean := path.Clean(p)
	if clean != p || strings.Contains(p, "..") || s.OdooDir == "" {
		text(w, 404, "")
		return
	}
	f := s.odooClient(series, strings.TrimPrefix(clean, "/"))
	b, err := os.ReadFile(f)
	if err != nil {
		text(w, 404, "")
		return
	}
	ext := path.Ext(clean)
	ct := map[string]string{".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8", ".svg": "image/svg+xml",
		".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif", ".woff": "font/woff", ".woff2": "font/woff2",
		".ttf": "font/ttf", ".eot": "application/vnd.ms-fontobject"}[ext]
	if ct == "" {
		ct = "application/octet-stream"
	}
	w.Header().Set("Content-Type", ct)
	w.Header().Set("Cache-Control", "no-cache")
	_, _ = w.Write(b)
}

// odooCall answers one JSON-RPC call of the client: its result, or the error the client shows as Odoo's own.
func (s *Server) odooCall(w http.ResponseWriter, r *http.Request, g *Garden, seat odooSeat) {
	series, reader := seat.series, seat.reader
	body, err := io.ReadAll(io.LimitReader(r.Body, 1<<20+1))
	if err != nil || len(body) > 1<<20 {
		reply(w, 413, map[string]any{"error": T(g, "درخواست بیش از اندازه بزرگ است.", "The request is too large.")})
		return
	}
	var req struct {
		ID     any            `json:"id"`
		Params map[string]any `json:"params"`
	}
	if json.Unmarshal(body, &req) != nil {
		reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
		return
	}
	lang, _ := s.odooLang(g, series)
	params := map[string]any{"path": r.URL.Path, "payload": req.Params, "reader": reader, "series": series, "lang": lang,
		"asof": seat.asof}
	if modernOdoo(series) { // 19 starts a week on its language's first day, as the language's translations say it
		params["week_start"] = s.odooWeekStart(series, lang)
	}
	if g.Register != nil { // the routes its register is read by now: the healthy ones, in the order to try them
		params["routes"] = g.Register.Hand()
	}
	raw, err := g.Worker.Call("odoo_rpc", params, 2*time.Minute)
	out := map[string]any{"jsonrpc": "2.0", "id": req.ID}
	if err != nil {
		msg := err.Error()
		if we, ok := worker.IsError(err); ok {
			msg = we.Message
		}
		out["error"] = map[string]any{"code": 200, "message": "daftar", "data": map[string]any{
			"name": "odoo.exceptions.UserError", "message": msg, "arguments": []any{msg}, "debug": ""}}
	} else {
		out["result"] = json.RawMessage(raw)
	}
	reply(w, 200, out)
}

// odooWeekStart is the first day of a week in a language (1 Monday … 7 Sunday), as Odoo's translations of the series'
// client say it (lang_parameters.week_start); English's own, Sunday, where none was taken.
func (s *Server) odooWeekStart(series, lang string) int {
	var t struct {
		LangParameters struct {
			WeekStart any `json:"week_start"`
		} `json:"lang_parameters"`
	}
	if langRe.MatchString(lang) {
		if b, err := os.ReadFile(s.odooClient(series, "translations/"+lang+".json")); err == nil && json.Unmarshal(b, &t) == nil {
			switch v := t.LangParameters.WeekStart.(type) {
			case float64:
				if v >= 1 && v <= 7 {
					return int(v)
				}
			case string:
				if len(v) == 1 && v[0] >= '1' && v[0] <= '7' {
					return int(v[0] - '0')
				}
			}
		}
	}
	return 7
}

// odooAsof is the commit the garden's worker reads `at` as — a commit HEAD reaches, or a moment; "" for now — with the
// worker's answer ({commit, at, subject}), or the worker's refusal.
func (s *Server) odooAsof(g *Garden, at string) (string, json.RawMessage, error) {
	raw, err := g.Worker.Call("odoo_asof", map[string]any{"at": at}, time.Minute)
	if err != nil {
		return "", nil, err
	}
	var got struct {
		Commit string `json:"commit"`
	}
	if json.Unmarshal(raw, &got) != nil || (at != "" && !commitRe.MatchString(got.Commit)) {
		return "", nil, fmt.Errorf("the garden's worker named no commit for %q", at)
	}
	return got.Commit, raw, nil
}

var commitRe = regexp.MustCompile(`^[0-9a-f]{40}$`)

// odooLookAt moves the seat to another moment of its garden — {"at": a commit or a moment}, or {"at": ""} for now — and
// says which commit that is. The seat keeps its garden, series and reader: what it may read is still what the reader's
// grants open now.
func (s *Server) odooLookAt(w http.ResponseWriter, r *http.Request, g *Garden, sid string, now time.Time) {
	var req struct {
		At string `json:"at"`
	}
	if json.NewDecoder(io.LimitReader(r.Body, 4096)).Decode(&req) != nil || len(req.At) > 64 {
		reply(w, 400, map[string]any{"error": T(g, "درخواست معتبر نیست.", "The request is not valid.")})
		return
	}
	commit, raw, err := s.odooAsof(g, req.At)
	if err != nil {
		msg := err.Error()
		if we, ok := worker.IsError(err); ok {
			msg = we.Message
		}
		reply(w, 404, map[string]any{"error": msg})
		return
	}
	if !s.Odoo.lookAt(sid, commit, now) {
		reply(w, 403, map[string]any{"error": T(g, "اودو را از دفتر باز کنید.", "Open Odoo from the garden.")})
		return
	}
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Cache-Control", "no-store")
	_, _ = w.Write(raw)
}

func htmlEscape(s string) string {
	return strings.NewReplacer("&", "&amp;", "<", "&lt;", ">", "&gt;", `"`, "&quot;", "'", "&#39;").Replace(s)
}
