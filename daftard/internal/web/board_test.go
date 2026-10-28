package web

import (
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
	assets "github.com/0mit/daftar/daftard/web"
)

// a worker that answers the board's methods, and writes down what each was asked
const boardStandIn = `import json, sys
log = open('asked.jsonl', 'a')
for line in sys.stdin:
    req = json.loads(line)
    m, p = req['method'], req.get('params') or {}
    log.write(json.dumps({'method': m, 'params': p}) + '\n'); log.flush()
    v = {'aspects': [{'lens': 'holds'}], 'orientations': [], 'starts': []} if m == 'board_aspects' else \
        {'lens': p.get('aspect'), 'cursor': [], 'groups': []} if m == 'board_lens' else \
        {'id': p.get('id'), 'facts': []} if m == 'board_being' else {'groups': []}
    sys.stdout.write(json.dumps({'id': req['id'], 'ok': True, 'result': v}) + '\n'); sys.stdout.flush()
`

func newBoardRig(t *testing.T) *viewRig {
	t.Helper()
	py, err := testpython.Path()
	if err != nil {
		t.Skip(err)
	}
	t.Setenv("DAFTARD_STATE", t.TempDir())
	dir := t.TempDir()
	script, log := filepath.Join(dir, "worker.py"), filepath.Join(dir, "garden", "asked.jsonl")
	if err := os.WriteFile(script, []byte(boardStandIn), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(dir, "garden"), 0o755); err != nil {
		t.Fatal(err)
	}
	gc := config.Garden{Name: "g", Path: filepath.Join(dir, "garden"), Python: py, Gardener: "sam", Kind: "core", Lang: "en"}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	s := &Server{Listen: "127.0.0.1:8790", Token: "k", CSRF: "c", Gardens: []*Garden{g}, Errors: guided.Open(), Assets: assets.FS}
	s.Handler()
	return &viewRig{s: s, log: log, dir: dir}
}

// THE BOARD IS DAFTARD'S PAGE, AND THREE.JS IS BENEATH IT: the page, its script and three.js are served from the
// binary, under daftard's own policy (script-src 'self'), so the page holds no script but files it loads, and its
// script imports three.js by its path, with no import map to allow.
func TestTheBoardIsServedWithThreeBeneathIt(t *testing.T) {
	v := newBoardRig(t)
	page := v.do("GET", "/board?g=g", "", true)
	if page.Code != 200 || !strings.Contains(page.Body.String(), `src="/board/board.js"`) {
		t.Fatalf("the board's page: %d %s", page.Code, page.Body.String())
	}
	if csp := page.Header().Get("Content-Security-Policy"); !strings.Contains(csp, "script-src 'self'") {
		t.Fatalf("the board's page is served under daftard's own policy, not %q", csp)
	}
	for _, tag := range regexp.MustCompile(`<script[^>]*>`).FindAllString(page.Body.String(), -1) {
		if !strings.Contains(tag, " src=") {
			t.Fatalf("the board's page holds a script of its own, which the policy refuses: %s", tag)
		}
	}
	js := v.do("GET", "/board/board.js", "", true)
	if js.Code != 200 || !strings.Contains(js.Body.String(), "from '/vendor/three-0.186.1/three.module.js'") {
		t.Fatalf("the board's script imports three.js by its path: %d", js.Code)
	}
	for _, f := range []string{"three.module.js", "three.core.js"} {
		w := v.do("GET", "/vendor/three-0.186.1/"+f, "", true)
		if w.Code != 200 || !strings.Contains(w.Body.String(), "SPDX-License-Identifier: MIT") {
			t.Fatalf("three.js's %s, with its licence, is served from the binary: %d", f, w.Code)
		}
	}
	if b, err := assets.FS.ReadFile("vendor/three-0.186.1/LICENSE"); err != nil || !strings.Contains(string(b), "MIT License") {
		t.Fatalf("three.js's licence is built in beside it: %v", err)
	}
	if w := v.do("GET", "/board", "", false); w.Code != 403 {
		t.Fatalf("the board, like every page, opens only for whom daftard let in: %d", w.Code)
	}
}

// THE BOARD ASKS THE GARDEN'S OWN RELEASE: each question goes to the worker as the page asked it — the cursor's ids
// one by one, the reader daftard says sits here — and none is held, since a store changes without a commit.
func TestTheBoardAsksTheWorkerEachTime(t *testing.T) {
	v := newBoardRig(t)
	for _, target := range []string{"/api/board/aspects?g=g", "/api/board/aspects?g=g",
		"/api/board/lens?g=g&aspect=holds&cursor=vol-a,d-0123456789abcdef", "/api/board/being?g=g&id=c-0123",
		"/api/board/find?g=g&q=IMG&cursor=vol-a"} {
		if w := v.do("GET", target, "", true); w.Code != 200 {
			t.Fatalf("%s: %d %s", target, w.Code, w.Body.String())
		}
	}
	n := 0
	for _, a := range v.asked() {
		if a["method"] == "board_aspects" {
			n++
		}
	}
	if n != 2 {
		t.Fatalf("a board's question is asked of the worker each time, never held: asked %d times of 2", n)
	}
	lens := v.last("board_lens")
	if c, _ := lens["cursor"].([]any); len(c) != 2 || c[0] != "vol-a" || c[1] != "d-0123456789abcdef" || lens["aspect"] != "holds" {
		t.Fatalf("the cursor goes as its ids: %v", lens)
	}
	if b := v.last("board_being"); b["id"] != "c-0123" || b["reader"] != "sam" {
		t.Fatalf("a sheet is asked for the reader who sits here, the gardener where nobody does: %v", b)
	}
	if f := v.last("board_find"); f["q"] != "IMG" {
		t.Fatalf("find: %v", f)
	}
}

// AN ID OF NO SHAPE NEVER REACHES THE WORKER: a path, too many beings, a find with no cursor.
func TestTheBoardRefusesAnIdOfNoShape(t *testing.T) {
	v := newBoardRig(t)
	for _, target := range []string{"/api/board/lens?g=g&aspect=holds&cursor=../beans",
		"/api/board/lens?g=g&aspect=holds&cursor=a,b,c,d,e,f,g,h,i", "/api/board/being?g=g&id=%2Fetc",
		"/api/board/find?g=g&q=IMG&cursor="} {
		if w := v.do("GET", target, "", true); w.Code != 400 {
			t.Fatalf("%s: %d, not refused", target, w.Code)
		}
	}
	for _, a := range v.asked() {
		if strings.HasPrefix(a["method"].(string), "board_") {
			t.Fatalf("the worker was asked %v", a)
		}
	}
}
