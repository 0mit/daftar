package web

import (
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/private"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// a worker that answers as the view's methods would, and writes down what each was asked
const viewPagesStandIn = `import json, sys
log = open('asked.jsonl', 'a')     # in the garden, where the worker runs
for line in sys.stdin:
    req = json.loads(line)
    m, p = req['method'], req.get('params') or {}
    log.write(json.dumps({'method': m, 'params': p}) + '\n'); log.flush()
    v = None
    if m == 'payload':
        v = {'cases': [], 'legacy': True}
    elif m == 'view_pages':
        v = {'pages': [{'bean': 'page-now', 'title': 'Now', 'place': 1}], 'assets': {'widgets': ['safe'], 'scripts': ['view_queue.js'], 'styles': []}}
    elif m == 'view_page':
        v = {'page': {'bean': p.get('page')}, 'views': {}}
    elif m == 'view_style':
        v = {'css': '.vw{color:red}'}
    elif m == 'view_html':
        v = {'page': '<html><body>' + str(p.get('page')) + '<script>page()</script></body></html>', 'scripts': ['page()']}
    elif m == 'view_write':
        ok = (p.get('body') or {}).get('bean') != 'refused'
        v = {'ok': ok, 'refusals': [] if ok else [{'op': 0, 'fact': 'header:title', 'message': 'a title is never empty'}]}
    elif m == 'view_act':
        b = p.get('body') or {}
        v = {'status': 403, 'answer': {'error': 'refused'}} if b.get('tool') == 'refused' else \
            {'status': 200, 'answer': {'mode': b.get('do') or 'started', 'course': 'run-1', 'plan': '+ stamped'}}
    elif m == 'hello':
        v = {'head': 'abc'}
    elif m == 'prefs_zones':
        v = [['irthr', 'Asia/Tehran']]
    elif m == 'prefs_check':
        tag = ((p.get('prefs') or {}).get('locale') or '')
        if 'nonsense' in tag:
            sys.stdout.write(json.dumps({'id': req['id'], 'ok': False, 'error': {'status': 400, 'kind': 'refused', 'message': "'nonsense' is no ca of CLDR's"}}) + '\n'); sys.stdout.flush()
            continue
        v = {'prefs': {'locale': tag}, 'reader': {'locale': tag}}
    sys.stdout.write(json.dumps({'id': req['id'], 'ok': True, 'result': v}) + '\n'); sys.stdout.flush()
`

type viewRig struct {
	s   *Server
	log string
	dir string
}

func newViewRig(t *testing.T, handplace string) *viewRig {
	t.Helper()
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	t.Setenv("DAFTARD_STATE", t.TempDir())
	dir := t.TempDir()
	script, log := filepath.Join(dir, "worker.py"), filepath.Join(dir, "garden", "asked.jsonl")
	if err := os.WriteFile(script, []byte(viewPagesStandIn), 0o644); err != nil {
		t.Fatal(err)
	}
	lib := filepath.Join(dir, "garden", "assets", "view", "lib")
	for name, body := range map[string]string{"view_queue.js": "queue()", "widgets/safe.js": "export const h = 1;",
		"widgets/widgets.css": ".w{}", "view_model.py": "SECRET = 1", "../../../GARDEN.md": "gardener: sam"} {
		p := filepath.Join(lib, filepath.FromSlash(name))
		_ = os.MkdirAll(filepath.Dir(p), 0o755)
		if err := os.WriteFile(p, []byte(body), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	gc := config.Garden{Name: "g", Path: filepath.Join(dir, "garden"), Python: py, Gardener: "sam", Kind: "core", Lang: "fa", Handplace: handplace,
		Walks: map[string]string{"stamp": "action-stamp"}}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	s := &Server{Listen: "127.0.0.1:8790", Token: "k", CSRF: "c", Gardens: []*Garden{g}, Errors: guided.Open()}
	s.Handler()
	return &viewRig{s: s, log: log, dir: dir}
}

func (v *viewRig) do(method, target, body string, cookie bool) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, target, strings.NewReader(body))
	r.Host = "127.0.0.1:8790"
	if cookie {
		r.AddCookie(&http.Cookie{Name: cookieName, Value: v.s.page})
	}
	if method == "POST" {
		r.Header.Set("Origin", "http://127.0.0.1:8790")
		r.Header.Set("X-CSRF-Token", "c")
		r.Header.Set("Content-Type", "application/json")
	}
	w := httptest.NewRecorder()
	v.s.ServeHTTP(w, r)
	return w
}

// asked is what the worker was asked, method by method, in order
func (v *viewRig) asked() []map[string]any {
	b, _ := os.ReadFile(v.log)
	out := []map[string]any{}
	for _, ln := range strings.Split(strings.TrimSpace(string(b)), "\n") {
		var m map[string]any
		if json.Unmarshal([]byte(ln), &m) == nil {
			out = append(out, m)
		}
	}
	return out
}

func (v *viewRig) last(method string) map[string]any {
	var found map[string]any
	for _, a := range v.asked() {
		if a["method"] == method {
			found, _ = a["params"].(map[string]any)
		}
	}
	return found
}

// A GARDEN'S PAGES ARE ITS PAGE BEANS ONLY WHERE ITS GARDENER SAYS SO: daftard.json's `handplace` is "legacy" when it
// says nothing — daftard's own pages, as before — and "view" moves the garden to its page beans; any other word is
// refused when daftard reads its configuration, never guessed.
func TestHandplaceIsLegacyUntilTheGardenerSaysView(t *testing.T) {
	for _, c := range []struct{ conf, want, err string }{{"", "legacy", ""}, {`"handplace": "view",`, "view", ""},
		{`"handplace": "legacy",`, "legacy", ""}, {`"handplace": "pages",`, "", "neither"}} {
		st := t.TempDir()
		t.Setenv("DAFTARD_STATE", st)
		raw := `{"gardens": [{"name": "g", "path": "/tmp/g", ` + c.conf + ` "kind": "core"}]}`
		if err := os.WriteFile(filepath.Join(st, "daftard.json"), []byte(raw), 0o600); err != nil {
			t.Fatal(err)
		}
		conf, err := config.Load()
		if c.err != "" {
			if err == nil || !strings.Contains(err.Error(), c.err) {
				t.Fatalf("%s: refused, naming the two it may be: %v", c.conf, err)
			}
			continue
		}
		if err != nil || conf.Gardens[0].Handplace != c.want || conf.Gardens[0].ViewHandplace() != (c.want == "view") {
			t.Fatalf("%q: handplace %q, want %q (%v)", c.conf, conf.Gardens[0].Handplace, c.want, err)
		}
	}
}

// THE CHROME'S DATA: a legacy garden's /api/dashboard is its pages' payload, as before; a garden whose handplace is its
// page beans gets the chrome's data and its navigation — the page beans in order, and what the browser loads of its
// release — and the worker is never asked for the legacy payload.
func TestTheDashboardOfAViewGardenIsItsPageBeans(t *testing.T) {
	legacy := newViewRig(t, "legacy")
	w := legacy.do("GET", "/api/dashboard?g=g", "", true)
	if w.Code != 200 || !strings.Contains(w.Body.String(), `"legacy":true`) || strings.Contains(w.Body.String(), `"pages"`) {
		t.Fatalf("a legacy garden is drawn by daftard's own pages: %d %s", w.Code, w.Body.String())
	}
	view := newViewRig(t, "view")
	w = view.do("GET", "/api/dashboard?g=g", "", true)
	var d map[string]any
	_ = json.Unmarshal(w.Body.Bytes(), &d)
	pages, _ := d["pages"].([]any)
	garden, _ := d["garden"].(map[string]any)
	if w.Code != 200 || len(pages) != 1 || d["assets"] == nil || garden["handplace"] != "view" || d["csrf"] != "c" || d["head"] != "abc" {
		t.Fatalf("a view garden's chrome lists its page beans: %d %s", w.Code, w.Body.String())
	}
	if view.last("payload") != nil {
		t.Fatalf("the legacy payload is not read for a view garden: %v", view.asked())
	}
}

// A LEGACY GARDEN KEEPS TODAY'S SURFACE until its gardener moves it: none of a view garden's addresses answers for it —
// a page bean, a page's Save, the release's files, a reader's way of reading — each the 404 an address daftard never
// had answers, and the worker is asked nothing of them; /view is the dashboard's own page, asked as before, whatever
// `page` the address carries. A view garden answers each, as its own tests say.
func TestALegacyGardenKeepsTodaysSurface(t *testing.T) {
	legacy, view := newViewRig(t, "legacy"), newViewRig(t, "view")
	for _, c := range []struct{ method, target, body string }{{"GET", "/api/view/page?g=g&page=page-now", ""},
		{"POST", "/api/view/write?g=g", `{"bean": "repair-1", "ops": []}`}, {"GET", "/release/g/view_queue.js", ""},
		{"GET", "/release/g/widgets/safe.js", ""}, {"GET", "/release/g/kit.css?page=page-now", ""},
		{"GET", "/api/prefs?g=g", ""}, {"POST", "/api/prefs?g=g", `{"locale": "fa"}`},
		{"POST", "/api/view/act?g=g", `{"page": "page-now", "m": "ledger", "el": "line", "tool": "stamp", "bean": "repair-1"}`}} {
		if w := legacy.do(c.method, c.target, c.body, true); w.Code != 404 || !strings.Contains(w.Body.String(), "یافت نشد") {
			t.Fatalf("a legacy garden: %s %s answers as an address daftard never had: %d %s", c.method, c.target, w.Code, w.Body.String())
		}
		if w := view.do(c.method, c.target, c.body, true); w.Code != 200 {
			t.Fatalf("a view garden: %s %s answers as now: %d %s", c.method, c.target, w.Code, w.Body.String())
		}
	}
	for _, m := range []string{"view_page", "view_write", "view_style", "prefs_zones", "prefs_check", "view_act"} {
		if legacy.last(m) != nil {
			t.Fatalf("a legacy garden's worker is asked nothing of a view garden's: %s (%v)", m, legacy.asked())
		}
	}
	if w := legacy.do("GET", "/view?g=g&page=page-now", "", true); w.Code != 200 || legacy.last("view_html") == nil || len(legacy.last("view_html")) != 0 {
		t.Fatalf("a legacy garden's /view is the dashboard's, asked as before: %d %v", w.Code, legacy.last("view_html"))
	}
	if w := legacy.do("GET", "/api/dashboard?g=g", "", true); w.Code != 200 || !strings.Contains(w.Body.String(), `"legacy":true`) {
		t.Fatalf("and its pages' payload, as before: %d %s", w.Code, w.Body.String())
	}
}

// THE RELEASE'S FILES: the browser loads the garden's own runtime, renderers and widgets — its scripts, styles and
// font, and nothing else of the garden: never its Python, never a path that climbs out of the view's library, never
// another garden's, never without the page's cookie.
func TestTheReleaseServesTheViewsFilesAndNothingElse(t *testing.T) {
	v := newViewRig(t, "view")
	for target, want := range map[string]int{"/release/g/view_queue.js": 200, "/release/g/widgets/safe.js": 200,
		"/release/g/widgets/widgets.css": 200, "/release/g/view_model.py": 404, "/release/g/../GARDEN.md": 404,
		"/release/g/widgets/../view_model.py": 404, "/release/g/widgets/%2e%2e/view_model.py": 404,
		"/release/other/view_queue.js": 404, "/release/g/view_absent.js": 404} {
		w := v.do("GET", target, "", true)
		if w.Code != want {
			t.Fatalf("%s: %d, want %d (%s)", target, w.Code, want, w.Body.String())
		}
		if want == 200 && (strings.Contains(w.Body.String(), "SECRET") || w.Header().Get("Content-Type") == "") {
			t.Fatalf("%s: served as what it is: %q %q", target, w.Header().Get("Content-Type"), w.Body.String())
		}
	}
	if w := v.do("GET", "/release/g/view_queue.js", "", false); w.Code != 403 {
		t.Fatalf("without the page's cookie nothing of a garden is served: %d", w.Code)
	}
	w := v.do("GET", "/release/g/kit.css?page=page-now", "", true)
	if w.Code != 200 || !strings.Contains(w.Body.String(), ".vw{color:red}") || v.last("view_style")["page"] != "page-now" {
		t.Fatalf("the kit's style, with the page's palette, from the worker: %d %s", w.Code, w.Body.String())
	}
}

// ONE PAGE, FOR THE PERSON READING: /api/view/page asks the worker for one page bean by a slug, as the person reading,
// in the garden's language; anything else is no page of this garden.
func TestAPageIsAskedForItsReader(t *testing.T) {
	v := newViewRig(t, "view")
	if w := v.do("GET", "/api/view/page?g=g&page=..%2Fbeans", "", true); w.Code != 400 {
		t.Fatalf("a page is a slug: %d", w.Code)
	}
	w := v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	p := v.last("view_page")
	if w.Code != 200 || p["page"] != "page-now" || p["reader"] != "sam" || p["lang"] != "fa" {
		t.Fatalf("the worker is asked for the page, as its reader: %d %v", w.Code, p)
	}
}

// A SAVE GOES TO THE VIEW'S ONE WRITE PATH: posted with the page's CSRF token and origin, it reaches the worker's
// view_write as the person reading; a refusal comes back whole, as 422, for the page to show at the facts it names.
func TestASaveGoesToTheViewsWritePath(t *testing.T) {
	v := newViewRig(t, "view")
	w := v.do("POST", "/api/view/write?g=g", `{"bean": "repair-1", "ops": [{"op": "change", "header": "title", "value": "x"}]}`, true)
	p := v.last("view_write")
	body, _ := p["body"].(map[string]any)
	if w.Code != 200 || p["reader"] != "sam" || body["bean"] != "repair-1" {
		t.Fatalf("the write reaches the view's write path as its reader: %d %v", w.Code, p)
	}
	w = v.do("POST", "/api/view/write?g=g", `{"bean": "refused", "ops": []}`, true)
	if w.Code != 422 || !strings.Contains(w.Body.String(), "a title is never empty") {
		t.Fatalf("a refusal comes back whole: %d %s", w.Code, w.Body.String())
	}
	r := httptest.NewRequest("POST", "/api/view/write?g=g", strings.NewReader(`{"bean": "repair-1", "ops": []}`))
	r.Host = "127.0.0.1:8790"
	r.AddCookie(&http.Cookie{Name: cookieName, Value: v.s.page})
	r.Header.Set("Origin", "http://127.0.0.1:8790")
	w = httptest.NewRecorder()
	v.s.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatalf("without the page's CSRF token nothing is written: %d", w.Code)
	}
}

// THE VIEW'S OWN PAGE OF ONE PAGE BEAN: /view?page= asks the worker for that page, and only the scripts its asset
// declares run, by their hashes, as for every page /view serves.
func TestTheViewsOwnPageOfAPageBean(t *testing.T) {
	v := newViewRig(t, "view")
	w := v.do("GET", "/view?g=g&page=page-now", "", true)
	if w.Code != 200 || v.last("view_html")["page"] != "page-now" || !strings.Contains(w.Header().Get("Content-Security-Policy"), "script-src "+sha("page()")+";") {
		t.Fatalf("the view's page of the bean, its scripts by their hashes: %d %v %s", w.Code, v.last("view_html"), w.Header().Get("Content-Security-Policy"))
	}
	if w := v.do("GET", "/view?g=g&page=Page%20Now", "", true); w.Code != 404 {
		t.Fatalf("a page is a slug: %d", w.Code)
	}
}

// A PERSON'S OWN WAY OF READING is checked by the garden's own view and kept on this machine for that garden and that
// person, never in the garden: GET /api/prefs gives it and the zones the panel offers; POST keeps what the view checked,
// and a refusal says why and keeps nothing; each page is built with it.
func TestAReadersWayOfReadingIsKeptOnTheMachine(t *testing.T) {
	v := newViewRig(t, "view")
	w := v.do("GET", "/api/prefs?g=g", "", true)
	if w.Code != 200 || !strings.Contains(w.Body.String(), `"prefs":{}`) || !strings.Contains(w.Body.String(), "Asia/Tehran") {
		t.Fatalf("unset, and the zones offered: %d %s", w.Code, w.Body.String())
	}
	w = v.do("POST", "/api/prefs?g=g", `{"locale": "fa-u-ca-nonsense"}`, true)
	if w.Code != 400 || !strings.Contains(w.Body.String(), "nonsense") {
		t.Fatalf("a bad tag is refused with the view's sentence: %d %s", w.Code, w.Body.String())
	}
	w = v.do("POST", "/api/prefs?g=g", `{"locale": "fa-u-ca-gregory-nu-latn"}`, true)
	if w.Code != 200 || v.last("prefs_check") == nil {
		t.Fatalf("a good one is checked by the garden's view and kept: %d %s", w.Code, w.Body.String())
	}
	b, err := os.ReadFile(filepath.Join(os.Getenv("DAFTARD_STATE"), "readers.json"))
	if err != nil || !strings.Contains(string(b), `"g/sam"`) || !strings.Contains(string(b), "fa-u-ca-gregory-nu-latn") {
		t.Fatalf("kept in the state folder, by garden and person: %v %s", err, b)
	}
	if err := private.Check(filepath.Join(os.Getenv("DAFTARD_STATE"), "readers.json")); err != nil {
		t.Fatalf("readable by this account alone: %v", err)
	}
	if out, _ := exec.Command("git", "-C", filepath.Join(v.dir, "garden"), "status", "--porcelain").CombinedOutput(); strings.Contains(string(out), "readers") {
		t.Fatalf("nothing of it in the garden: %s", out)
	}
	if w := v.do("GET", "/api/prefs?g=g", "", true); !strings.Contains(w.Body.String(), "fa-u-ca-gregory-nu-latn") {
		t.Fatalf("read back: %s", w.Body.String())
	}
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if p, _ := v.last("view_page")["prefs"].(map[string]any); p == nil || p["locale"] != "fa-u-ca-gregory-nu-latn" {
		t.Fatalf("each page is built with it: %v", v.last("view_page"))
	}
	if w := v.do("POST", "/api/prefs?g=g", `{"locale": "fa"}`, false); w.Code != 403 {
		t.Fatalf("without the page's cookie nothing is kept: %d", w.Code)
	}
}

// A PAGE'S ACTION GOES TO THE WORKER, WITH THE WALKS THIS MACHINE NAMES: /api/view/act carries the page's action (or a
// decision on its run's plan) to the worker's view_act as the person reading, with the garden's `walks` from
// daftard.json — what a page may start is this machine's to say — and an audit record in the state folder, never the
// garden's; the worker's status comes back as it is (a refusal as itself), and a run started is heard by open pages.
func TestAPagesActionGoesToTheWorker(t *testing.T) {
	v := newViewRig(t, "view")
	w := v.do("POST", "/api/view/act?g=g", `{"page": "page-now", "m": "ledger", "el": "line", "tool": "stamp", "bean": "repair-1", "inputs": {"words": "x"}}`, true)
	p := v.last("view_act")
	walks, _ := p["walks"].(map[string]any)
	body, _ := p["body"].(map[string]any)
	if w.Code != 200 || !strings.Contains(w.Body.String(), "run-1") || p["reader"] != "sam" || walks["stamp"] != "action-stamp" ||
		body["tool"] != "stamp" || !strings.HasPrefix(fmt.Sprint(p["audit"]), os.Getenv("DAFTARD_STATE")) {
		t.Fatalf("the action reaches the worker as its reader, with this machine's walks: %d %s %v", w.Code, w.Body.String(), p)
	}
	if strings.HasPrefix(fmt.Sprint(p["audit"]), filepath.Join(v.dir, "garden")) {
		t.Fatalf("the audit is the machine's, never the garden's: %v", p["audit"])
	}
	if w := v.do("POST", "/api/view/act?g=g", `{"page": "page-now", "do": "ratify", "bean": "repair-1", "course": "run-1"}`, true); w.Code != 200 ||
		v.last("view_act")["body"].(map[string]any)["do"] != "ratify" {
		t.Fatalf("a decision on the plan reaches it too: %d %s", w.Code, w.Body.String())
	}
	if w := v.do("POST", "/api/view/act?g=g", `{"page": "page-now", "tool": "refused", "bean": "repair-1"}`, true); w.Code != 403 {
		t.Fatalf("the worker's refusal comes back as itself: %d %s", w.Code, w.Body.String())
	}
	r := httptest.NewRequest("POST", "/api/view/act?g=g", strings.NewReader(`{"page": "page-now", "tool": "stamp", "bean": "repair-1"}`))
	r.Host = "127.0.0.1:8790"
	r.AddCookie(&http.Cookie{Name: cookieName, Value: v.s.page})
	r.Header.Set("Origin", "http://127.0.0.1:8790")
	w = httptest.NewRecorder()
	v.s.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatalf("without the page's CSRF token nothing is started: %d", w.Code)
	}
}

// A PAGE'S ACTION MAY CARRY A FILE: an input of the type `file` (a bank's statement to import, a scan) travels in the
// action's body, its bytes as base64, so /api/view/act takes a body as large as the view's own host takes a file (16 MiB,
// as base64); every other request a page makes keeps its small bound.
func TestAPagesActionTakesAFile(t *testing.T) {
	v := newViewRig(t, "view")
	scan := strings.Repeat("QUJD", 200000) // 800 kB of base64
	body := `{"page": "page-now", "m": "ledger", "el": "pay", "tool": "stamp", "bean": "repair-1#paid", "inputs": {"scan": {"name": "s.pdf", "data": "` + scan + `"}}}`
	w := v.do("POST", "/api/view/act?g=g", body, true)
	b, _ := v.last("view_act")["body"].(map[string]any)
	in, _ := b["inputs"].(map[string]any)
	got, _ := in["scan"].(map[string]any)
	if w.Code != 200 || got["data"] != scan || b["bean"] != "repair-1#paid" {
		t.Fatalf("the action's file reaches the worker whole, the row with it: %d %.200s", w.Code, w.Body.String())
	}
	if w := v.do("POST", "/api/view/write?g=g", `{"bean": "repair-1", "ops": [], "pad": "`+scan+`"}`, true); w.Code != 413 {
		t.Fatalf("a Save keeps its small bound: %d", w.Code)
	}
}
