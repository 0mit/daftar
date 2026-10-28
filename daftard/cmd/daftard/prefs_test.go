package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/private"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/web"
)

// a worker that answers as a garden's own release would: the bean a JSON line of what it holds, and `here` the garden's
// folder's name, standing in for its id
const prefsStandIn = `import json, os, sys
here = os.path.basename(os.getcwd())
for line in sys.stdin:
    req = json.loads(line)
    m, p = req['method'], req.get('params') or {}
    if m == 'prefs_bean':
        v = {'bean': 'BEAN ' + json.dumps({'reader': p.get('reader'), 'garden': here, 'prefs': p.get('prefs') or {}}, sort_keys=True)}
    elif m == 'prefs_from_bean':
        text = p.get('text') or ''
        if not text.startswith('BEAN '):
            sys.stdout.write(json.dumps({'id': req['id'], 'ok': False, 'error': {'status': 400, 'kind': 'refused', 'message': 'it holds no preferences'}}) + '\n'); sys.stdout.flush()
            continue
        v = dict(json.loads(text[5:]), here=here, bean='preferences-' + 'x')
    else:
        v = None
    sys.stdout.write(json.dumps({'id': req['id'], 'ok': True, 'result': v}) + '\n'); sys.stdout.flush()
`

func prefsRig(t *testing.T) (dir string) {
	t.Helper()
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir = t.TempDir()
	st := filepath.Join(dir, "state")
	t.Setenv("DAFTARD_STATE", st)
	for _, g := range []string{"g1", "g2"} {
		if err := os.MkdirAll(filepath.Join(dir, g), 0o700); err != nil {
			t.Fatal(err)
		}
	}
	conf, _ := json.Marshal(map[string]any{"listen": "127.0.0.1:8799", "gardens": []map[string]any{
		{"name": "g1", "path": filepath.Join(dir, "g1"), "python": py},
		{"name": "g2", "path": filepath.Join(dir, "g2"), "python": py}}})
	if err := os.MkdirAll(st, 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(st, "daftard.json"), conf, 0o600); err != nil {
		t.Fatal(err)
	}
	script := filepath.Join(dir, "standin.py")
	if err := os.WriteFile(script, []byte(prefsStandIn), 0o600); err != nil {
		t.Fatal(err)
	}
	was := prefsScript
	prefsScript = func() (string, func(), error) { return script, func() {}, nil }
	t.Cleanup(func() { prefsScript = was })
	return dir
}

// A READER'S WAY OF READING, KEPT OR CARRIED AS A BEAN: `daftard prefs export` asks the garden's own release for the
// bean of what this machine keeps, written the person's alone to read — the platform's way (internal/private: its mode
// on Linux and macOS, its access list on Windows), over an older copy others could read too; `import` reads one back
// into it, whole — what it does not hold unset — and in the garden it was set in, found by its id among this machine's
// gardens; a bean of another garden is refused, nothing kept.
func TestAReadersWayOfReadingGoesToABeanAndBack(t *testing.T) {
	dir := prefsRig(t)
	full := map[string]string{"locale": "en-u-ca-persian-nu-latn", "date": "full", "currency": "name"}
	if err := web.SetReaderPrefs("g1", "sam", full); err != nil {
		t.Fatal(err)
	}
	out := filepath.Join(dir, "carried", "sam.md")
	if err := os.MkdirAll(filepath.Dir(out), 0o700); err != nil {
		t.Fatal(err)
	}
	openToAll(t, out)
	if err := prefsCmd([]string{"export", "g1", "sam", "--out", out}); err != nil {
		t.Fatalf("export: %v", err)
	}
	b, _ := os.ReadFile(out)
	if !strings.Contains(string(b), `"garden": "g1"`) || !strings.Contains(string(b), "en-u-ca-persian-nu-latn") {
		t.Fatalf("the bean of what this machine keeps, by the garden's own release: %s", b)
	}
	if err := private.Check(out); err != nil {
		t.Fatalf("the bean is the person's alone to read, where an older copy others could read was: %v", err)
	}
	if left, _ := filepath.Glob(filepath.Join(filepath.Dir(out), ".*")); len(left) != 0 {
		t.Fatalf("nothing is left beside it: %v", left)
	}
	if err := web.SetReaderPrefs("g1", "sam", map[string]string{"date": "short"}); err != nil {
		t.Fatal(err)
	}
	if err := prefsCmd([]string{"import", out}); err != nil {
		t.Fatalf("import, the garden found by its id: %v", err)
	}
	if got := web.ReaderPrefs("g1", "sam"); !reflect.DeepEqual(got, full) {
		t.Fatalf("read back whole, nothing lost: %v", got)
	}
	if got := web.ReaderPrefs("g2", "sam"); len(got) != 0 {
		t.Fatalf("into the garden it was set in only: %v", got)
	}
	err := prefsCmd([]string{"import", out, "g2"})
	if err == nil || !strings.Contains(err.Error(), "g1") || len(web.ReaderPrefs("g2", "sam")) != 0 {
		t.Fatalf("a bean of another garden is refused for this one, nothing kept: %v", err)
	}
	if err := os.WriteFile(filepath.Join(dir, "no.md"), []byte("---\nbean: x\n---\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := prefsCmd([]string{"import", filepath.Join(dir, "no.md"), "g1"}); err == nil || !strings.Contains(err.Error(), "no preferences") {
		t.Fatalf("a bean that holds none is refused with the release's sentence: %v", err)
	}
	if got := web.ReaderPrefs("g1", "sam"); !reflect.DeepEqual(got, full) {
		t.Fatalf("...and nothing kept changes: %v", got)
	}
}

// openToAll writes an older copy at path that others may read: mode 0644 on Linux and macOS; on Windows an entry
// granting Everyone (S-1-1-0) its reading, made by icacls.
func openToAll(t *testing.T, path string) {
	t.Helper()
	if err := os.WriteFile(path, []byte("an older copy\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS == "windows" {
		if out, err := exec.Command("icacls", path, "/grant", "*S-1-1-0:(R)").CombinedOutput(); err != nil {
			t.Fatalf("icacls could not open the file to Everyone: %v %s", err, out)
		}
	} else if err := os.Chmod(path, 0o644); err != nil {
		t.Fatal(err)
	}
	if private.Check(path) == nil {
		t.Fatalf("the older copy is open to others")
	}
}
