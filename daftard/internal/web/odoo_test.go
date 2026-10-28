package web

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	assets "github.com/0mit/daftar/daftard/web"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
)

const odooStandIn = `import json, sys
def answer(rid, ok, v):
    sys.stdout.write(json.dumps({'id': rid, 'ok': ok, ('result' if ok else 'error'): v}) + '\n'); sys.stdout.flush()
for line in sys.stdin:
    req = json.loads(line); p = req.get('params') or {}; m = req['method']; rid = req['id']
    if m == 'odoo_session':
        answer(rid, True, {'uid': 1, 'name': p['reader'], 'server_version': p['series']})
    elif m == 'odoo_rpc' and p['path'].startswith('/web/dataset/call_kw') and p['payload']['method'] == 'web_search_read':
        answer(rid, True, {'length': 0, 'records': [], 'asked_by': p['reader']})
    elif m == 'odoo_rpc':
        answer(rid, False, {'status': 501, 'message': 'daftar does not answer this yet: ' + p['path'], 'kind': 'refused'})
    else:
        answer(rid, False, {'status': 404, 'message': 'unknown', 'kind': 'failed'})
`

// ODOO'S OWN CLIENT, SERVED: the page opened for one garden only where its series' client was taken, its session
// from the garden, the client's files as they came and nothing outside the client's folder, its JSON calls answered
// in Odoo's own envelope — a refusal as Odoo's error — and taken only as JSON from this server's own pages.
func TestOdooClientServed(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	_ = os.WriteFile(script, []byte(odooStandIn), 0o644)
	odoo := filepath.Join(dir, "odoo")
	_ = os.MkdirAll(filepath.Join(odoo, "17.0", "web", "static", "img"), 0o755)
	_ = os.WriteFile(filepath.Join(odoo, "17.0", "CLIENT.json"), []byte(`{}`), 0o644)
	_ = os.WriteFile(filepath.Join(odoo, "17.0", "web", "static", "img", "a.svg"), []byte(`<svg/>`), 0o644)
	_ = os.WriteFile(filepath.Join(dir, "secret.txt"), []byte(`not the client's`), 0o644)
	gc := config.Garden{Name: "g", Title: "The garden", Path: dir, Python: py, Gardener: "ana"}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	t.Setenv("DAFTARD_STATE", t.TempDir())
	s := &Server{Listen: "127.0.0.1:8770", Token: "k", CSRF: "c", Gardens: []*Garden{g}, Assets: assets.FS,
		Errors: guided.Open(), OdooDir: odoo, Odoo: NewOdooDoor("localhost:8792")}
	h, oh := s.Handler(), s.OdooHandler()
	// the handplace: the machine's key, its own origin; Odoo's origin: another host, its own session
	home := func(method, path string) *httptest.ResponseRecorder {
		r := httptest.NewRequest(method, "http://127.0.0.1:8770"+path, nil)
		r.Host = "127.0.0.1:8770"
		r.AddCookie(&http.Cookie{Name: cookieName, Value: s.page})
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		return w
	}
	var odooC *http.Cookie
	do := func(method, path string, body []byte, ct, origin string) *httptest.ResponseRecorder {
		r := httptest.NewRequest(method, "http://localhost:8792"+path, bytes.NewReader(body))
		r.Host = "localhost:8792"
		if odooC != nil {
			r.AddCookie(odooC)
		}
		if ct != "" {
			r.Header.Set("Content-Type", ct)
		}
		if origin != "" {
			r.Header.Set("Origin", origin)
		}
		w := httptest.NewRecorder()
		oh.ServeHTTP(w, r)
		return w
	}
	if w := home("GET", "/odoo?g=g&series=18.0"); w.Code != 404 {
		t.Fatalf("a series whose client was not taken here is no page: %d", w.Code)
	}
	for _, p := range []string{"/web/static/img/a.svg", "/odoo/session.js", "/web/webclient/load_menus/x"} {
		if w := home("GET", p); w.Code != 404 {
			t.Fatalf("the handplace's origin serves nothing of Odoo's but its door: %s %d", p, w.Code)
		}
	}
	w := home("GET", "/odoo?g=g")
	loc := w.Header().Get("Location")
	if w.Code != http.StatusSeeOther || !strings.HasPrefix(loc, "http://localhost:8792/odoo/enter?t=") {
		t.Fatalf("the door sends the page to Odoo's own origin: %d %q", w.Code, loc)
	}
	enter := strings.TrimPrefix(loc, "http://localhost:8792")
	if w := do("GET", "/odoo", nil, "", ""); w.Code != 403 {
		t.Fatalf("Odoo's origin without its session serves nothing: %d", w.Code)
	}
	for _, v := range []string{"k", s.page} { // neither the machine's key nor the handplace's page cookie
		r0 := httptest.NewRequest("GET", "http://localhost:8792/odoo", nil)
		r0.Host = "localhost:8792"
		r0.AddCookie(&http.Cookie{Name: cookieName, Value: v})
		w0 := httptest.NewRecorder()
		oh.ServeHTTP(w0, r0)
		if w0.Code != 403 {
			t.Fatalf("the handplace's cookie opens nothing on Odoo's origin: %d", w0.Code)
		}
	}
	w = do("GET", enter, nil, "", "")
	for _, c := range w.Result().Cookies() {
		if c.Name == odooCookie {
			odooC = c
		}
	}
	if w.Code != http.StatusOK || odooC == nil || !odooC.HttpOnly || odooC.SameSite != http.SameSiteStrictMode {
		t.Fatalf("the token becomes a session on Odoo's origin: %d %v", w.Code, odooC)
	}
	// the way here was cross-site from its start; a browser that holds SameSite to a whole redirect chain (Firefox)
	// sends no Strict cookie on a later hop of it, so the chain ends here, and this origin's own page moves on to /odoo
	if b := w.Body.String(); !strings.Contains(b, `<meta http-equiv="refresh" content="0; url=/odoo"/>`) ||
		!strings.Contains(b, `<a href="/odoo">`) || strings.Contains(b, strings.TrimPrefix(enter, "/odoo/enter?t=")) ||
		w.Header().Get("Location") != "" || w.Header().Get("Cache-Control") != "no-store" ||
		w.Header().Get("Content-Security-Policy") != odooCSP || w.Header().Get("Referrer-Policy") != "no-referrer" {
		t.Fatalf("its page moves on to /odoo itself, holding no token, kept nowhere: %v %s", w.Header(), b)
	}
	keep := odooC
	odooC = nil
	if w := do("GET", enter, nil, "", ""); w.Code != 403 {
		t.Fatalf("a door's token is good once: %d", w.Code)
	}
	odooC = keep
	rh := httptest.NewRequest("GET", "http://127.0.0.1:8792/odoo", nil)
	rh.Host = "127.0.0.1:8792"
	rh.AddCookie(odooC)
	wh := httptest.NewRecorder()
	oh.ServeHTTP(wh, rh)
	if wh.Code != 403 {
		t.Fatalf("Odoo's origin answers only to its own name: %d", wh.Code)
	}
	w = do("GET", "/odoo", nil, "", "")
	if w.Code != 200 || !strings.Contains(w.Body.String(), "/web/assets/debug/web.assets_web.js") ||
		!strings.Contains(w.Header().Get("Content-Security-Policy"), "'unsafe-eval'") ||
		strings.Contains(w.Header().Get("Content-Security-Policy"), "http") {
		t.Fatalf("the page, for one garden, loading only from its own origin: %d %v", w.Code, w.Header())
	}
	if w := do("GET", "/odoo/session.js", nil, "", ""); w.Code != 200 || !strings.Contains(w.Body.String(), `"name": "ana"`) &&
		!strings.Contains(w.Body.String(), `"name":"ana"`) {
		t.Fatalf("the session is the garden's, for its reader: %d %s", w.Code, w.Body.String())
	}
	if w := do("GET", "/web/static/img/a.svg", nil, "", ""); w.Code != 200 || w.Header().Get("Content-Type") != "image/svg+xml" {
		t.Fatalf("a file of the client, as it came: %d", w.Code)
	}
	if w := do("GET", "/web/../../secret.txt", nil, "", ""); w.Code == 200 && strings.Contains(w.Body.String(), "not the client's") {
		t.Fatalf("nothing outside the client's folder is served")
	}
	if w := do("GET", "/web/webclient/translations/x?lang=../../secret", nil, "", ""); strings.Contains(w.Body.String(), "not the client's") {
		t.Fatalf("a translation's name is checked before a file is opened by it")
	}
	call := func(method string) []byte {
		b, _ := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": 7, "method": "call",
			"params": map[string]any{"model": "hr.employee", "method": method, "args": []any{}, "kwargs": map[string]any{}}})
		return b
	}
	if w := do("POST", "/web/dataset/call_kw/hr.employee/web_search_read", call("web_search_read"), "text/plain", "http://localhost:8792"); w.Code != 403 {
		t.Fatalf("a call that is not JSON is refused: %d", w.Code)
	}
	for _, o := range []string{"http://evil.example", "http://127.0.0.1:8770", ""} {
		if w := do("POST", "/web/dataset/call_kw/hr.employee/web_search_read", call("web_search_read"), "application/json", o); w.Code != 403 {
			t.Fatalf("a call from another origin (%q), the handplace's included, is refused: %d", o, w.Code)
		}
	}
	w = do("POST", "/web/dataset/call_kw/hr.employee/web_search_read", call("web_search_read"), "application/json", "http://localhost:8792")
	var env map[string]any
	_ = json.Unmarshal(w.Body.Bytes(), &env)
	if w.Code != 200 || env["id"] != float64(7) || env["result"].(map[string]any)["asked_by"] != "ana" {
		t.Fatalf("a call answered in Odoo's envelope, for the garden's reader: %d %s", w.Code, w.Body.String())
	}
	w = do("POST", "/web/dataset/call_kw/hr.employee/unlink", call("unlink"), "application/json", "http://localhost:8792")
	env = nil
	_ = json.Unmarshal(w.Body.Bytes(), &env)
	e, _ := env["error"].(map[string]any)
	if w.Code != 200 || e == nil || !strings.Contains(e["data"].(map[string]any)["message"].(string), "does not answer this yet") {
		t.Fatalf("what daftard does not answer is Odoo's own error, said: %d %s", w.Code, w.Body.String())
	}
}

const odooAsofStandIn = `import json, sys
C = 'c' * 40
def answer(rid, ok, v):
    sys.stdout.write(json.dumps({'id': rid, 'ok': ok, ('result' if ok else 'error'): v}) + '\n'); sys.stdout.flush()
for line in sys.stdin:
    req = json.loads(line); p = req.get('params') or {}; m = req['method']; rid = req['id']
    if m == 'odoo_asof':
        if p.get('at') in ('', None):
            answer(rid, True, {})
        elif p['at'] in ('2026-10-11', 'cccc'):
            answer(rid, True, {'commit': C, 'at': '2026-10-11T12:00:00+03:00', 'subject': 'a save'})
        else:
            answer(rid, False, {'status': 404, 'message': 'the garden had no commit then', 'kind': 'refused'})
    elif m == 'odoo_session':
        answer(rid, True, {'uid': 1, 'daftar': {'asof': p.get('asof') or ''}})
    elif m == 'odoo_rpc':
        answer(rid, True, {'asof': p.get('asof') or ''})
    else:
        answer(rid, False, {'status': 404, 'message': 'unknown', 'kind': 'failed'})
`

// THE GARDEN AS OF A MOMENT (design §10.3, P5.4b): the door opens Odoo's page as of a day, a moment or a commit, which
// the garden's worker resolves; every call the page makes then carries that commit to the worker, the session says it,
// and the page itself can move its seat to another moment, or back to now — from its own origin only. A moment the
// garden had no commit at opens nothing.
func TestOdooAsOf(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	_ = os.WriteFile(script, []byte(odooAsofStandIn), 0o644)
	odoo := filepath.Join(dir, "odoo")
	_ = os.MkdirAll(filepath.Join(odoo, "17.0"), 0o755)
	_ = os.WriteFile(filepath.Join(odoo, "17.0", "CLIENT.json"), []byte(`{}`), 0o644)
	gc := config.Garden{Name: "g", Title: "The garden", Path: dir, Python: py, Gardener: "ana"}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	t.Setenv("DAFTARD_STATE", t.TempDir())
	s := &Server{Listen: "127.0.0.1:8770", Token: "k", CSRF: "c", Gardens: []*Garden{g}, Assets: assets.FS,
		Errors: guided.Open(), OdooDir: odoo, Odoo: NewOdooDoor("localhost:8792")}
	h, oh := s.Handler(), s.OdooHandler()
	home := func(path string) *httptest.ResponseRecorder {
		r := httptest.NewRequest("GET", "http://127.0.0.1:8770"+path, nil)
		r.Host = "127.0.0.1:8770"
		r.AddCookie(&http.Cookie{Name: cookieName, Value: s.page}) // the page's cookie, this run's own value
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		return w
	}
	var seat *http.Cookie
	do := func(method, path, body, origin string) *httptest.ResponseRecorder {
		r := httptest.NewRequest(method, "http://localhost:8792"+path, strings.NewReader(body))
		r.Host = "localhost:8792"
		if seat != nil {
			r.AddCookie(seat)
		}
		if method == "POST" {
			r.Header.Set("Content-Type", "application/json")
			r.Header.Set("Origin", origin)
		}
		w := httptest.NewRecorder()
		oh.ServeHTTP(w, r)
		return w
	}
	enter := func(query string) bool {
		w := home("/odoo?g=g" + query)
		loc := w.Header().Get("Location")
		if w.Code != http.StatusSeeOther || !strings.HasPrefix(loc, "http://localhost:8792/odoo/enter?t=") {
			return false
		}
		w = do("GET", strings.TrimPrefix(loc, "http://localhost:8792"), "", "")
		for _, c := range w.Result().Cookies() {
			if c.Name == odooCookie {
				seat = c
			}
		}
		return true
	}
	asked := func() string { // the commit the worker is asked as of, by a call of the page
		w := do("POST", "/web/dataset/call_kw/hr.employee/web_search_read", `{"id": 1, "params": {}}`, "http://localhost:8792")
		var env struct {
			Result struct {
				Asof string `json:"asof"`
			} `json:"result"`
		}
		_ = json.Unmarshal(w.Body.Bytes(), &env)
		return env.Result.Asof
	}
	if enter("&asof=1999-01-01") {
		t.Fatal("a moment the garden had no commit at opens no page")
	}
	if !enter("&asof=2026-10-11") || asked() != strings.Repeat("c", 40) {
		t.Fatalf("the page opened as of a day asks every call as of the commit it resolves to: %q", asked())
	}
	if w := do("GET", "/odoo/session.js", "", ""); !strings.Contains(w.Body.String(), strings.Repeat("c", 40)) {
		t.Fatalf("the session says the commit the page reads as of: %s", w.Body.String())
	}
	if w := do("GET", "/odoo", "", ""); !strings.Contains(w.Body.String(), `src="/odoo/daftar.js"`) {
		t.Fatalf("the page carries daftard's own part, which shows the moment: %s", w.Body.String())
	}
	if w := do("GET", "/odoo/daftar.js", "", ""); w.Code != 200 || !strings.Contains(w.Body.String(), "/odoo/asof") ||
		!strings.HasPrefix(w.Header().Get("Content-Type"), "text/javascript") {
		t.Fatalf("daftard's own part of the page, served from its origin: %d %s", w.Code, w.Header())
	}
	if w := do("POST", "/odoo/asof", `{"at": ""}`, "http://evil.example"); w.Code != 403 || asked() == "" {
		t.Fatalf("another origin cannot move the seat: %d %q", w.Code, asked())
	}
	if w := do("POST", "/odoo/asof", `{"at": "nope"}`, "http://localhost:8792"); w.Code != 404 || asked() == "" {
		t.Fatalf("a moment the garden had no commit at is refused, and the seat stays: %d %q", w.Code, asked())
	}
	if w := do("POST", "/odoo/asof", `{"at": ""}`, "http://localhost:8792"); w.Code != 200 || asked() != "" {
		t.Fatalf("back to now, every call is asked of the garden as it is: %d %q", w.Code, asked())
	}
	if w := do("POST", "/odoo/asof", `{"at": "cccc"}`, "http://localhost:8792"); w.Code != 200 || asked() != strings.Repeat("c", 40) {
		t.Fatalf("the page moves its seat to a commit: %d %q", w.Code, asked())
	}
	if !enter("") || asked() != "" {
		t.Fatalf("a page opened with no moment reads the garden as it is: %q", asked())
	}
}

// The machine's key opens Odoo's page for a garden, as of a commit or a moment too, and nothing else.
func TestOdooDoorAddresses(t *testing.T) {
	for _, ok := range []string{"/odoo?g=g", "/odoo?g=g&series=17.0", "/odoo?g=g&asof=" + strings.Repeat("c", 40),
		"/odoo?g=g&asof=2026-10-11", "/odoo?g=g&series=17.0&asof=2026-10-11 14:30+03:00"} {
		if !OdooRe.MatchString(ok) {
			t.Fatalf("not opened: %q", ok)
		}
	}
	for _, no := range []string{"/odoo?g=g&asof=../x", "/odoo?g=g&asof=2026-10-11&x=1", "/odoo?g=g&next=http://evil",
		"/odoo?g=g&asof=" + strings.Repeat("c", 41), "//evil/odoo?g=g"} {
		if OdooRe.MatchString(no) {
			t.Fatalf("opened: %q", no)
		}
	}
}

const odoo19StandIn = `import json, sys
def answer(rid, ok, v):
    sys.stdout.write(json.dumps({'id': rid, 'ok': ok, ('result' if ok else 'error'): v}) + '\n'); sys.stdout.flush()
for line in sys.stdin:
    req = json.loads(line); p = req.get('params') or {}; m = req['method']; rid = req['id']
    if m == 'odoo_session':
        answer(rid, True, {'uid': 1, 'name': p['reader'], 'view_info': p.get('view_info'), 'lang': p.get('lang')})
    elif m == 'odoo_rpc':
        answer(rid, True, {'path': p['path'], 'week_start': p.get('week_start'), 'series': p['series']})
    else:
        answer(rid, False, {'status': 404, 'message': 'unknown', 'kind': 'failed'})
`

// ODOO 19'S CLIENT, SERVED (P7.1): its page at /odoo and at any of the client's own routes under it (a reload asks for
// /odoo/<path>), but never at daftard's own; its menus and translations asked with no path segment; the bundles it loads
// when a page needs one, as their definitions were taken, and nothing a bundle's name does not name; what each view is
// called handed to the session in the page's language; and the language's first day of a week to every call. A 17
// seat is served as before.
func TestOdooClient19(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	_ = os.WriteFile(script, []byte(odoo19StandIn), 0o644)
	odoo := filepath.Join(dir, "odoo")
	for _, series := range []string{"17.0", "19.0"} {
		_ = os.MkdirAll(filepath.Join(odoo, series, "translations"), 0o755)
		_ = os.MkdirAll(filepath.Join(odoo, series, "bundles"), 0o755)
		_ = os.WriteFile(filepath.Join(odoo, series, "CLIENT.json"), []byte(`{"languages": {"fa_IR": "rtl"},
			"view_info": {"fa_IR": {"list": {"display_name": "فهرست"}}, "en_US": {"list": {"display_name": "List"}}}}`), 0o644)
		_ = os.WriteFile(filepath.Join(odoo, series, "translations", "fa_IR.json"),
			[]byte(`{"lang": "fa_IR", "lang_parameters": {"code": "fa_IR", "week_start": "6"}}`), 0o644)
		_ = os.WriteFile(filepath.Join(odoo, series, "bundles", "web.assets_emoji.json"),
			[]byte(`[{"type": "script", "src": "/web/assets/debug/web.assets_emoji.js"}]`), 0o644)
	}
	_ = os.WriteFile(filepath.Join(dir, "secret.json"), []byte(`"not the client's"`), 0o644)
	gc := config.Garden{Name: "g", Title: "The garden", Path: dir, Python: py, Gardener: "ana", Lang: "fa"}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	t.Setenv("DAFTARD_STATE", t.TempDir())
	s := &Server{Listen: "127.0.0.1:8770", Token: "k", CSRF: "c", Gardens: []*Garden{g}, Assets: assets.FS,
		Errors: guided.Open(), OdooDir: odoo, Odoo: NewOdooDoor("localhost:8792")}
	h, oh := s.Handler(), s.OdooHandler()
	seat := func(series string) func(method, path, body string) *httptest.ResponseRecorder {
		r := httptest.NewRequest("GET", "http://127.0.0.1:8770/odoo?g=g&series="+series, nil)
		r.Host = "127.0.0.1:8770"
		r.AddCookie(&http.Cookie{Name: cookieName, Value: s.page})
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		loc := w.Header().Get("Location")
		r = httptest.NewRequest("GET", loc, nil)
		r.Host = "localhost:8792"
		w = httptest.NewRecorder()
		oh.ServeHTTP(w, r)
		var c *http.Cookie
		for _, x := range w.Result().Cookies() {
			if x.Name == odooCookie {
				c = x
			}
		}
		if c == nil {
			t.Fatalf("no seat for series %s: %d %q", series, w.Code, loc)
		}
		return func(method, path, body string) *httptest.ResponseRecorder {
			r := httptest.NewRequest(method, "http://localhost:8792"+path, strings.NewReader(body))
			r.Host = "localhost:8792"
			r.AddCookie(c)
			if method == "POST" {
				r.Header.Set("Content-Type", "application/json")
				r.Header.Set("Origin", "http://localhost:8792")
			}
			w := httptest.NewRecorder()
			oh.ServeHTTP(w, r)
			return w
		}
	}
	do := seat("19.0")
	for _, p := range []string{"/odoo", "/odoo/action-5", "/odoo/shop.need/7"} {
		if w := do("GET", p, ""); w.Code != 200 || !strings.Contains(w.Body.String(), `<script src="/odoo/session.js">`) {
			t.Fatalf("19's page, at /odoo and at the client's own routes under it (%s): %d", p, w.Code)
		}
	}
	w := do("GET", "/odoo/session.js", "")
	if !strings.Contains(w.Body.String(), `fetch("/web/webclient/load_menus", {cache: "no-store"})`) ||
		!strings.Contains(w.Body.String(), `"فهرست"`) && !strings.Contains(w.Body.String(), `"\u0641\u0647\u0631\u0633\u062a"`) {
		t.Fatalf("19's session: its menus with no path segment, what each view is called in the page's language: %s", w.Body.String())
	}
	if w := do("GET", "/odoo/daftar.js", ""); w.Code != 200 || !strings.HasPrefix(w.Header().Get("Content-Type"), "text/javascript") {
		t.Fatalf("daftard's own part of the page is still its own, not 19's page: %d %s", w.Code, w.Header())
	}
	if w := do("GET", "/web/webclient/translations?hash=&lang=fa_IR", ""); !strings.Contains(w.Body.String(), `"week_start": "6"`) {
		t.Fatalf("19's translations, asked with no path segment, as the instance gave them: %s", w.Body.String())
	}
	var got map[string]any
	_ = json.Unmarshal(do("GET", "/web/webclient/load_menus", "").Body.Bytes(), &got)
	if got["path"] != "/web/webclient/load_menus" {
		t.Fatalf("19's menus, asked of the garden's worker: %v", got)
	}
	if w := do("GET", "/web/bundle/web.assets_emoji?lang=fa_IR", ""); w.Code != 200 || !strings.Contains(w.Body.String(), "web.assets_emoji.js") {
		t.Fatalf("a bundle 19's client loads when a page needs it, as its definition was taken: %d %s", w.Code, w.Body.String())
	}
	for _, p := range []string{"/web/bundle/web.chartjs_lib", "/web/bundle/..%2F..%2Fsecret", "/web/bundle/x", "/web/bundle/A.b"} {
		if w := do("GET", p, ""); w.Code != 404 || strings.Contains(w.Body.String(), "not the client's") {
			t.Fatalf("a bundle not taken, or a name that is no bundle's, opens nothing: %s %d", p, w.Code)
		}
	}
	w = do("POST", "/web/dataset/call_kw/shop.need/web_read_group", `{"id": 1, "params": {}}`)
	var env struct {
		Result map[string]any `json:"result"`
	}
	_ = json.Unmarshal(w.Body.Bytes(), &env)
	if env.Result["week_start"] != float64(6) || env.Result["series"] != "19.0" {
		t.Fatalf("every call carries the language's first day of a week, as its translations say it: %s", w.Body.String())
	}
	old := seat("17.0")
	if w := old("GET", "/odoo/action-5", ""); w.Code == 200 && strings.Contains(w.Body.String(), "session.js") {
		t.Fatalf("a 17 seat has no client routes under /odoo: %d", w.Code)
	}
	if w := old("GET", "/odoo/session.js", ""); !strings.Contains(w.Body.String(), `fetch("/web/webclient/load_menus/daftar").then`) {
		t.Fatalf("a 17 seat's session as before: %s", w.Body.String())
	}
	if w := old("GET", "/web/bundle/web.assets_emoji", ""); w.Code != 404 {
		t.Fatalf("a 17 seat loads no bundle by name: %d", w.Code)
	}
	_ = json.Unmarshal(old("POST", "/web/dataset/call_kw/hr.employee/web_search_read", `{"id": 1, "params": {}}`).Body.Bytes(), &env)
	if _, ok := env.Result["week_start"]; ok && env.Result["week_start"] != nil {
		t.Fatalf("a 17 seat's calls as before: %v", env.Result)
	}
}

// a worker that answers the front page's payload as the garden's kind would: a garden of the core what it offers (the
// series it captured, its register's), a dashboard its own pages' payload
const coreFrontStandIn = `import json, os, sys
for line in sys.stdin:
    req = json.loads(line)
    v = None
    if req['method'] == 'payload' and os.environ.get('DAFTAR_KIND') == 'core':
        v = {'kind': 'core', 'odoo': ['17.0', '19.0', '../x'], 'register': {'series': '19.0', 'bean': 'the-register',
             'title': 'The register', 'captured': True}, 'asOf': '2026-10-12'}
    elif req['method'] == 'payload':
        v = {'cases': [], 'odoo': ['19.0'], 'asOf': '2026-10-12'}
    sys.stdout.write(json.dumps({'id': req['id'], 'ok': True, 'result': v}) + '\n'); sys.stdout.flush()
`

// A GARDEN OF THE CORE HAS NO FRONT PAGE OF ITS OWN (pages/core.js): its front page's data is what it offers, as its
// worker reads it, each Odoo series marked with whether this machine opens it — its client taken here and Odoo's
// origin listening — and a name that is no series dropped. A dashboard's payload is passed on as it always was.
func TestCoreFrontOffers(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	t.Setenv("DAFTAR_KIND", "") // the stand-in reads the kind daftard hands its worker, and no other
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	_ = os.WriteFile(script, []byte(coreFrontStandIn), 0o644)
	odoo := filepath.Join(dir, "odoo")
	_ = os.MkdirAll(filepath.Join(odoo, "19.0"), 0o755)
	_ = os.WriteFile(filepath.Join(odoo, "19.0", "CLIENT.json"), []byte(`{}`), 0o644) // 19's client taken; 17's not
	t.Setenv("DAFTARD_STATE", t.TempDir())
	front := func(kind string, door *OdooDoor) map[string]any {
		t.Helper()
		gc := config.Garden{Name: "g", Path: dir, Python: py, Gardener: "ana", Kind: kind}
		g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
		t.Cleanup(g.Worker.Close)
		s := &Server{Listen: "127.0.0.1:8770", Token: "k", CSRF: "c", Gardens: []*Garden{g}, Assets: assets.FS,
			Errors: guided.Open(), OdooDir: odoo, Odoo: door}
		r := httptest.NewRequest("GET", "http://127.0.0.1:8770/api/dashboard?g=g", nil)
		r.Host = "127.0.0.1:8770"
		r.Header.Set(keyHeader, "k")
		w := httptest.NewRecorder()
		s.Handler().ServeHTTP(w, r)
		var data map[string]any
		if w.Code != 200 || json.Unmarshal(w.Body.Bytes(), &data) != nil {
			t.Fatalf("%s: /api/dashboard → %d %s", kind, w.Code, w.Body.String())
		}
		return data
	}
	got := front("core", NewOdooDoor("localhost:8792"))
	b, _ := json.Marshal([]any{got["odoo"], got["register"], got["garden"].(map[string]any)["kind"]})
	want := `[[{"opens":false,"series":"17.0"},{"opens":true,"series":"19.0"}],` +
		`{"bean":"the-register","captured":true,"opens":true,"series":"19.0","title":"The register"},"core"]`
	if string(b) != want {
		t.Fatalf("a garden of the core: what it offers, and whether this machine opens it:\n got %s\nwant %s", b, want)
	}
	got = front("core", nil) // Odoo's origin not listening: nothing opens
	if b, _ := json.Marshal([]any{got["odoo"], got["register"].(map[string]any)["opens"]}); string(b) !=
		`[[{"opens":false,"series":"17.0"},{"opens":false,"series":"19.0"}],false]` {
		t.Fatalf("no Odoo origin, no screen opens: %s", b)
	}
	got = front("dashboard", NewOdooDoor("localhost:8792"))
	if b, _ := json.Marshal(got["odoo"]); string(b) != `["19.0"]` || got["register"] != nil {
		t.Fatalf("a dashboard's payload is passed on as it was: %s", b)
	}
}
