package garden

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/testpython"
)

// The core's reader, run in Python: for each path on stdin, its front matter read by the garden's own core/read.py
// (`document`: its line ends made one, split by bin/parse.py's one splitter, read by `loads`, every scalar a string, a
// key written twice refused, a front matter that is no mapping refused) — one JSON line each: {"ok": tree} or
// {"unread": why}.
const coreReader = `
import json, sys
root = sys.argv[1]
sys.path.insert(0, root)
from core import read
for path in sys.stdin.read().split('\n'):
    if not path:
        continue
    try:
        print(json.dumps({'ok': read.document(path)[0]}, ensure_ascii=False))
    except Exception as e:
        print(json.dumps({'unread': str(e)[:200]}))
`

// both reads every file under the core's reader of the garden at root and under this one, and says where they differ.
func both(t *testing.T, root string, files []string) {
	t.Helper()
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	c := exec.Command(py, "-c", coreReader, root)
	c.Stdin = strings.NewReader(strings.Join(files, "\n"))
	out, err := c.Output()
	if err != nil {
		t.Fatalf("the core's reader in %s: %v", root, err)
	}
	lines := strings.Split(strings.TrimRight(string(out), "\n"), "\n")
	if len(lines) != len(files) {
		t.Fatalf("the core's reader answered %d of %d files", len(lines), len(files))
	}
	differ := 0
	for i, f := range files {
		var core map[string]any
		if err := json.Unmarshal([]byte(lines[i]), &core); err != nil {
			t.Fatalf("%s: %v", f, err)
		}
		b, err := ReadBean(f)
		_, coreUnread := core["unread"]
		switch {
		case coreUnread && err != nil:
			continue // both refuse it
		case coreUnread:
			t.Errorf("%s: the core refuses it (%v), and this reads it", f, core["unread"])
		case err != nil:
			t.Errorf("%s: the core reads it, and this refuses it: %v", f, err)
		default:
			raw, _ := json.Marshal(Plain(b.Header))
			var ours any
			_ = json.Unmarshal(raw, &ours)
			if !reflect.DeepEqual(ours, core["ok"]) {
				t.Errorf("%s: read differently\n core: %.600s\n this: %.600s", f, lines[i], raw)
			} else {
				continue
			}
		}
		if differ++; differ > 20 {
			t.Fatal("…and more")
		}
	}
	t.Logf("%s: %d files read alike", root, len(files)-differ)
}

// TestConformance: every bean and mapping of each garden DAFTARD_CONFORMANCE names (paths, by the OS's list
// separator), read by its own core and by this reader.
func TestConformance(t *testing.T) {
	roots := filepath.SplitList(os.Getenv("DAFTARD_CONFORMANCE"))
	if len(roots) == 0 {
		t.Skip("DAFTARD_CONFORMANCE names no garden to read")
	}
	for _, root := range roots {
		if _, err := os.Stat(filepath.Join(root, "core", "read.py")); err != nil {
			t.Errorf("%s carries no core/read.py", root)
			continue
		}
		var files []string
		for _, dir := range []string{"beans", "mappings"} {
			got, _ := filepath.Glob(filepath.Join(root, dir, "*.md"))
			files = append(files, got...)
		}
		both(t, root, files)
	}
}

// TestHardCases: what YAML lets a bean write that a simple reader gets wrong, each read by the core of the garden
// DAFTARD_CORE names (any garden of the core) and by this reader.
func TestHardCases(t *testing.T) {
	root := os.Getenv("DAFTARD_CORE")
	if root == "" {
		t.Skip("DAFTARD_CORE names no garden whose core reads the cases")
	}
	cases := map[string]string{
		"flow":        "bean: x\nstatements:\n  - say: { by: sam, at: \"2026-10-09 18:30+03:00\", note: 'it''s here: yes' }\n  - be: { by: self, at: [now, \"walk#step\"], placed: { openness: here } }\n",
		"plain-colon": "bean: x\nstatements:\n  - read: {by: unknown, at: 2026-08-02T01:35:21+03:00, note: agent:opus/x (operator)}\n",
		"wrapped":     "bean: x\nsummary: 'a long line that\n  goes on here, and ''quoted'' too'\ntitle: plain words that\n  run on\n",
		"double":      "bean: x\ntitle: \"tab\\there \\u0645 \\\\ end\"\nsummary: \"two\n\n  paragraphs\"\n",
		"blocks":      "bean: x\ndetails:\n  lit: |\n    one\n      two\n\n    three\n  fold: >-\n    a\n    b\n\n    c\n  keep: |+\n    k\n\nnext: v\n",
		"nested":      "bean: x\ndetails:\n  identity:\n    anchors:\n      fqdn:\n        class: logical\n        observed: '2026-08-02'\n  list:\n  - a\n  - b: c\n    d: e\n  empty:\n  on: yes\n",
		"comments":    "# a comment\nbean: x # trailing\ntags: [a, b] # list\nurl: http://x.y/#frag\n",
		"twice":       "bean: x\nbean: y\n",
		"flow-multi":  "bean: x\nstatements:\n  - say: { by: sam,\n      of: [a, b],\n      at: now }\n",
		"numbers":     "bean: x\ncount: 010\nflag: true\nnothing: ~\nday: 2026-10-01\n",
	}
	dir := t.TempDir()
	var files []string
	for name, body := range cases {
		f := filepath.Join(dir, name+".md")
		if err := os.WriteFile(f, []byte("---\n"+body+"---\nbody\n"), 0o644); err != nil {
			t.Fatal(err)
		}
		files = append(files, f)
	}
	both(t, root, files)
}
