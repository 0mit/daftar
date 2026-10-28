package web

import (
	"crypto/sha256"
	"encoding/base64"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// a garden whose view page carries a bean's title unescaped: a script the asset never wrote
const viewStandIn = `import json, sys
page = '<html><body><h1>A title <script>fetch("/api/stop")</script></h1><script>runtime()</script><script>page()</script></body></html>'
for line in sys.stdin:
    req = json.loads(line)
    v = {'page': page, 'scripts': ['runtime()', 'page()']} if req['method'] == 'view_html' else None
    sys.stdout.write(json.dumps({'id': req['id'], 'ok': True, 'result': v}) + '\n'); sys.stdout.flush()
`

func sha(s string) string {
	d := sha256.Sum256([]byte(s))
	return "'sha256-" + base64.StdEncoding.EncodeToString(d[:]) + "'"
}

// THE VIEW'S PAGE RUNS ONLY ITS ASSET'S SCRIPTS (security audit 2026-10-10, 2.4): the policy's hashes are of the
// scripts the worker says the view's asset wrote, never of a script found in the page — where a bean's text the page
// carried unescaped would be one, run with the handplace's cookie.
func TestTheViewRunsOnlyItsAssetsScripts(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	if err := os.WriteFile(script, []byte(viewStandIn), 0o644); err != nil {
		t.Fatal(err)
	}
	gc := config.Garden{Name: "g", Path: dir, Python: py}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	s := &Server{Listen: "127.0.0.1:8790", Token: "k", CSRF: "c", Gardens: []*Garden{g}}
	s.Handler()
	r := httptest.NewRequest("GET", "/view?g=g", nil)
	r.Host = "127.0.0.1:8790"
	r.AddCookie(&http.Cookie{Name: cookieName, Value: s.page})
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	csp := w.Header().Get("Content-Security-Policy")
	if w.Code != 200 || !strings.Contains(w.Body.String(), "<h1>A title") {
		t.Fatalf("the view's page is served: %d %q", w.Code, w.Body.String())
	}
	if !strings.Contains(csp, "script-src "+sha("runtime()")+" "+sha("page()")+";") {
		t.Fatalf("the asset's own scripts run, by their hashes: %s", csp)
	}
	if strings.Contains(csp, sha(`fetch("/api/stop")`)) {
		t.Fatalf("a script the asset did not write gets no hash: %s", csp)
	}
	for _, d := range []string{"default-src 'none'", "base-uri 'none'", "frame-ancestors 'none'", "form-action 'none'"} {
		if !strings.Contains(csp, d) {
			t.Fatalf("the rest of the policy holds (%s): %s", d, csp)
		}
	}
}
