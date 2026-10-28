package hubkey

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func git(t *testing.T, dir string, env []string, args ...string) string {
	t.Helper()
	c := exec.Command("git", args...)
	c.Dir = dir
	c.Env = append(append(os.Environ(), "GIT_AUTHOR_NAME=sam", "GIT_AUTHOR_EMAIL=sam@x", "GIT_COMMITTER_NAME=sam",
		"GIT_COMMITTER_EMAIL=sam@x", "GIT_CONFIG_NOSYSTEM=1", "HOME="+dir), env...)
	out, err := c.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v %s", args, err, out)
	}
	return strings.TrimSpace(string(out))
}

// a garden: a repository with a first commit, whose id is the first twelve digits of that commit
func garden(t *testing.T) (string, string) {
	t.Helper()
	dir := t.TempDir()
	git(t, dir, nil, "init", "-q")
	git(t, dir, nil, "commit", "-q", "--allow-empty", "-m", "germinated")
	root := git(t, dir, nil, "rev-parse", "HEAD")
	return dir, root[:12]
}

// the key as bin/hub.py install makes it: ed25519, no passphrase, in the state folder under hubs/<garden id>/
func made(t *testing.T, state, id string, mode os.FileMode) string {
	t.Helper()
	if _, err := exec.LookPath("ssh-keygen"); err != nil {
		t.Skip("no ssh-keygen on this machine")
	}
	p := Path(state, id)
	if err := os.MkdirAll(filepath.Dir(p), 0o755); err != nil {
		t.Fatal(err)
	}
	if out, err := exec.Command("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-C", "hub@"+id, "-f", p).CombinedOutput(); err != nil {
		t.Fatalf("ssh-keygen: %v %s", err, out)
	}
	if err := os.Chmod(p, mode); err != nil {
		t.Fatal(err)
	}
	return p
}

// THE HUB'S KEY, FOUND WHERE ITS INIT MADE IT: in the state folder under the garden's id, narrowed to this account
// again, its fingerprint read; a commit the hub writes with it is authored as the hub's bean and verifies against it.
func TestTheHubsKeyIsFoundAndSignsAsTheHubsBean(t *testing.T) {
	g, id := garden(t)
	state := t.TempDir()
	if got := ID(g); got != id {
		t.Fatalf("a garden's id is the first twelve digits of its first commit: %q, want %q", got, id)
	}
	p := made(t, state, id, 0o644)
	k, err := Find(state, g)
	if err != nil || !strings.HasPrefix(k.Fingerprint, "SHA256:") || k.Path != p {
		t.Fatalf("the hub's key is found under hubs/<garden id>/: %+v %v", k, err)
	}
	if runtime.GOOS != "windows" {
		for _, x := range []string{filepath.Dir(p), p} {
			if fi, _ := os.Stat(x); fi.Mode().Perm()&0o077 != 0 {
				t.Fatalf("%s is narrowed to this account again: %v", x, fi.Mode().Perm())
			}
		}
	}
	if k.Statement() != `name: { by: ssh, of: self, as: "`+k.Fingerprint+`" }` {
		t.Fatalf("the statement for the hub's bean: %s", k.Statement())
	}
	params := k.Params("box-hub", "shop")
	sign, _ := params["sign"].(map[string]string)
	if params["by"] != "box-hub" || sign["GIT_AUTHOR_NAME"] != "box-hub" || sign["GIT_CONFIG_VALUE_1"] != p {
		t.Fatalf("the worker is asked as the hub's bean, with its signing: %v", params)
	}
	env := []string{}
	for n, v := range sign {
		env = append(env, n+"="+v)
	}
	git(t, g, env, "commit", "-q", "--allow-empty", "-m", "merged")
	allowed := filepath.Join(t.TempDir(), "allowed")
	if err := os.WriteFile(allowed, []byte("box-hub@shop.daftar.invalid "+k.Public+"\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	log := git(t, g, nil, "-c", "gpg.ssh.allowedSignersFile="+allowed, "log", "--show-signature", "--format=%an <%ae>", "-1")
	if !strings.Contains(log, `Good "git" signature for box-hub@shop.daftar.invalid`) ||
		!strings.Contains(log, "box-hub <box-hub@shop.daftar.invalid>") {
		t.Fatalf("a commit the hub writes is the hub's bean's, signed by its key: %s", log)
	}
}

// NO KEY, NOTHING SIGNED: a garden whose hub has no key yet is said so (bin/hub.py install makes it), and daftard does
// not make one of its own; a garden it cannot name — no repository, a shallow clone — has no hub key to find.
func TestNoKeyIsSaidAndNoneIsMadeHere(t *testing.T) {
	g, id := garden(t)
	state := t.TempDir()
	if _, err := Find(state, g); !errors.Is(err, ErrNone) {
		t.Fatalf("no key: ErrNone, %v", err)
	}
	if _, err := os.Stat(filepath.Dir(Path(state, id))); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("finding makes nothing: %v", err)
	}
	if _, err := Find(state, t.TempDir()); err == nil || errors.Is(err, ErrNone) {
		t.Fatalf("a folder that is no repository has no garden id: %v", err)
	}
	git(t, g, nil, "commit", "-q", "--allow-empty", "-m", "second")
	shallow := filepath.Join(t.TempDir(), "shallow")
	git(t, filepath.Dir(shallow), nil, "clone", "-q", "--depth", "1", "file://"+g, shallow)
	if got := ID(shallow); got != "" {
		t.Fatalf("a shallow clone cannot see its root: %q", got)
	}
}

// THE HUB'S INIT IS THE GARDEN'S OWN TOOL: `bin/hub.py install` on the working copy, with the garden's Python and this
// account's state folder; a release whose bin/hub.py makes no key (no `key` command: its usage, exit 2) is left alone,
// since its `install` would write a hook into the working copy's tree.
func TestInstallRunsTheGardensOwnHubInit(t *testing.T) {
	python, err := exec.LookPath("python3")
	if err != nil {
		t.Skip("no python3 on this machine")
	}
	g, _ := garden(t)
	state := t.TempDir()
	if err := os.MkdirAll(filepath.Join(g, "bin"), 0o755); err != nil {
		t.Fatal(err)
	}
	stand := func(src string) {
		if err := os.WriteFile(filepath.Join(g, "bin", "hub.py"), []byte(src), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	ran := filepath.Join(t.TempDir(), "ran")
	stand("import sys\nprint(__doc__)\nsys.exit(2)\n") // an older release: `key` is no command of its
	if _, err := Install(python, g, state); err == nil || !strings.Contains(err.Error(), "makes no hub key yet") {
		t.Fatalf("an older release's hub.py is left alone, and said so: %v", err)
	}
	stand(`import os, sys
if sys.argv[1] == 'key':
    print('hub: no key yet'); sys.exit(1)
open(` + "'" + strings.ReplaceAll(ran, `\`, `\\`) + "'" + `, 'w', newline='\n').write(' '.join(sys.argv[1:]) + '\n' + os.environ['DAFTARD_STATE'])
print('hub: the key of this hub: SHA256:x')
`)
	out, err := Install(python, g, state)
	b, _ := os.ReadFile(ran)
	if err != nil || !strings.Contains(out, "the key of this hub") || string(b) != "install "+g+"\n"+state {
		t.Fatalf("install is run on the working copy, with this account's state folder: %q %v %q", out, err, b)
	}
}

// NAMED AS THE HUB FINDS A WRITER (bin/hub.py writer_of), at the garden's last commit: a `name` the namespace ssh gives,
// of the bean itself and not sealed, or, in a garden in today's words, an identity anchor `ssh_key_fingerprint`; a name
// of another bean, a sealed one, another key, a bean the last commit does not hold: not named.
func TestNamedIsWhatTheHubFindsAtTheLastCommit(t *testing.T) {
	g, _ := garden(t)
	k := Key{Fingerprint: "SHA256:" + strings.Repeat("B", 43)}
	at := func(text string) bool {
		t.Helper()
		if err := os.MkdirAll(filepath.Join(g, "beans"), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(g, "beans", "box-hub.md"), []byte(text), 0o644); err != nil {
			t.Fatal(err)
		}
		git(t, g, nil, "add", "-A")
		git(t, g, nil, "commit", "-q", "-m", "the hub's bean")
		named, err := k.Named(g, "box-hub")
		if err != nil {
			t.Fatalf("read: %v", err)
		}
		return named
	}
	head := "---\nbean: box-hub\nkind: instance\ntitle: \"the hub\"\nstatements:\n  - say: { by: sam, at: now }\n"
	if named, err := k.Named(g, "box-hub"); named || err != nil {
		t.Fatalf("no bean at the last commit: not named, %v", err)
	}
	cases := []struct {
		line string
		want bool
	}{
		{`  - name: { id: key, by: ssh, of: self, as: "` + k.Fingerprint + `" }`, true},
		{`  - name: { id: key, by: ssh, as: "` + k.Fingerprint + `" }`, true},
		{`  - name: { id: key, by: ssh, of: box-hub, as: "` + k.Fingerprint + `" }`, true},
		{`  - name: { id: key, by: ssh, of: box, as: "` + k.Fingerprint + `" }`, false},
		{`  - name: { id: key, by: ssh, of: self, as: "SHA256:` + strings.Repeat("C", 43) + `" }`, false},
		{`  - name: { id: key, by: openpgp, of: self, as: "` + k.Fingerprint + `" }`, false},
		{`  - name: { id: key, by: ssh, held: "root:x/0123456789abcdef0123456789abcdef" }`, false},
	}
	for _, c := range cases {
		if got := at(head + c.line + "\n---\nThe hub.\n"); got != c.want {
			t.Fatalf("%s: named %v, want %v", c.line, got, c.want)
		}
	}
	today := "---\nbean: box-hub\ngenos: instance\nidentity:\n  anchors:\n    - { key: ssh_key_fingerprint, value: \"" +
		k.Fingerprint + "\" }\n---\nThe hub.\n"
	if !at(today) {
		t.Fatalf("a garden in today's words names a writer by its identity anchor")
	}
	if err := os.WriteFile(filepath.Join(g, "beans", "box-hub.md"), []byte(head+`  - name: { id: key, by: ssh, of: self, as: "`+
		k.Fingerprint+`" }`+"\n---\nThe hub.\n"), 0o644); err != nil { // written, and not committed
		t.Fatal(err)
	}
	git(t, g, nil, "rm", "-q", "--cached", "beans/box-hub.md")
	git(t, g, nil, "commit", "-q", "-m", "the hub's bean taken out")
	if named, _ := k.Named(g, "box-hub"); named {
		t.Fatalf("what the working tree holds and the last commit does not, the hub has not judged: not named")
	}
}
