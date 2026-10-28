package web

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	assets "github.com/0mit/daftar/daftard/web"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/register"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// a worker that answers an Odoo call with the routes it was handed, and says the second answered
const routesStandIn = `import json, sys
for line in sys.stdin:
    req = json.loads(line); p = req.get('params') or {}
    out = {'id': req['id'], 'ok': True, 'result': {'routes': p.get('routes')}}
    if req['method'] == 'odoo_rpc':
        out['register'] = [{'route': 1, 'missed': 'refused'}, {'route': 2, 'answered': True}]
    sys.stdout.write(json.dumps(out) + '\n'); sys.stdout.flush()
`

// A REGISTER'S ROUTES, SEEN AND HANDED: each Odoo call is handed the healthy routes in order, and what the worker
// found of them comes back to daftard; /health shows each route — healthy or not, since when, its last error's kind,
// which answered last — and never where it goes; `daftard status` (the session) does, to whoever may read the garden's
// own.
func TestRegisterRoutesSeen(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	t.Setenv("DAFTARD_STATE", t.TempDir())
	ok := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {}))
	defer ok.Close()
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	_ = os.WriteFile(script, []byte(routesStandIn), 0o644)
	odoo := filepath.Join(dir, "odoo")
	_ = os.MkdirAll(filepath.Join(odoo, "19.0"), 0o755)
	_ = os.WriteFile(filepath.Join(odoo, "19.0", "CLIENT.json"), []byte(`{}`), 0o644)
	conf := &config.Register{Series: "19.0", DB: "db", Bean: "the-register",
		Routes: []config.Route{{Via: "https", URL: ok.URL}, {Via: "https", URL: "https://register.example.org"}}}
	gc := config.Garden{Name: "g", Path: dir, Python: py, Gardener: "ana", Kind: "core", Register: conf}
	wk := worker.New(gc, script)
	g := &Garden{Conf: gc, Worker: wk, Register: register.New("g", conf, nil)}
	wk.Noted = g.Register.Noted
	t.Cleanup(g.Worker.Close)
	t.Cleanup(g.Register.Close) // never Run: both routes healthy as they start, nothing asked of the second's address
	s := &Server{Listen: "127.0.0.1:8770", Token: "k", CSRF: "c", Gardens: []*Garden{g}, Assets: assets.FS,
		Errors: guided.Open(), OdooDir: odoo, Odoo: NewOdooDoor("localhost:8792")}
	tok, _ := s.Odoo.issue("g", "19.0", "ana", "", time.Now())
	sid, _ := s.Odoo.redeem(tok, time.Now())
	r := httptest.NewRequest("POST", "http://localhost:8792/web/dataset/call_kw/res.partner/search_count",
		strings.NewReader(`{"id": 1, "params": {"model": "res.partner", "method": "search_count", "args": [[]], "kwargs": {}}}`))
	r.Host = "localhost:8792"
	r.Header.Set("Origin", "http://localhost:8792")
	r.Header.Set("Content-Type", "application/json")
	r.AddCookie(&http.Cookie{Name: odooCookie, Value: sid})
	w := httptest.NewRecorder()
	s.OdooHandler().ServeHTTP(w, r)
	var got struct {
		Result struct {
			Routes []map[string]any `json:"routes"`
		} `json:"result"`
	}
	if json.Unmarshal(w.Body.Bytes(), &got) != nil || len(got.Result.Routes) != 2 || got.Result.Routes[0]["url"] != ok.URL ||
		got.Result.Routes[1]["route"] != float64(2) {
		t.Fatalf("the call is handed the healthy routes in order: %s", w.Body.String())
	}
	// the worker said route 1 missed a read and route 2 answered: route 1 now tried after route 2
	if h := g.Register.Hand(); len(h) != 2 || h[0]["route"] != 2 {
		t.Fatalf("what the worker found came back: %v", h)
	}
	get := func(path string, key bool) map[string]any {
		r := httptest.NewRequest("GET", "http://127.0.0.1:8770"+path, nil)
		r.Host = "127.0.0.1:8770"
		if key {
			r.Header.Set(keyHeader, "k")
		}
		w := httptest.NewRecorder()
		s.Handler().ServeHTTP(w, r)
		var out map[string]any
		if w.Code != 200 || json.Unmarshal(w.Body.Bytes(), &out) != nil {
			t.Fatalf("%s: %d %s", path, w.Code, w.Body.String())
		}
		return out
	}
	h := get("/health", false)
	b, _ := json.Marshal(h["registers"])
	if !strings.Contains(string(b), `"answered":{"at":`) || !strings.Contains(string(b), `"route":2}`) ||
		!strings.Contains(string(b), `"error":"read: refused"`) || !strings.Contains(string(b), `"via":"https"`) ||
		strings.Contains(string(b), "example.org") || strings.Contains(string(b), ok.URL) || strings.Contains(string(b), "label") {
		t.Fatalf("/health: each route's state and which answered last, never where it goes: %s", b)
	}
	b, _ = json.Marshal(get("/api/session?g=g", true)["register"])
	if !strings.Contains(string(b), `"label":"2 (https://register.example.org)"`) {
		t.Fatalf("the session (daftard status): where each route goes: %s", b)
	}
}
