package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/hubkey"
	"github.com/0mit/daftar/daftard/internal/web"
)

// WHAT DAFTARD WRITES ON ITS OWN IS THE GARDEN HUB'S: a garden that names its hub's bean, whose key the garden's
// bin/hub.py install made, has its steps asked as that bean, signed with that key; a garden that names none has
// nothing signed as a hub, and one whose hub has no key yet neither, and the log says what makes it.
func TestTheHubSignsWhatDaftardWritesOnItsOwn(t *testing.T) {
	if _, err := exec.LookPath("ssh-keygen"); err != nil {
		t.Skip("no ssh-keygen on this machine")
	}
	dir := t.TempDir()
	for _, a := range [][]string{{"init", "-q"}, {"-c", "user.name=sam", "-c", "user.email=sam@x", "commit", "-q", "--allow-empty", "-m", "germinated"}} {
		if out, err := exec.Command("git", append([]string{"-C", dir}, a...)...).CombinedOutput(); err != nil {
			t.Fatalf("git %v: %v %s", a, err, out)
		}
	}
	state := t.TempDir()
	var logs []string
	logf := func(f string, a ...any) { logs = append(logs, fmt.Sprintf(f, a...)) }
	g := &web.Garden{Conf: config.Garden{Name: "shop", Path: dir, Python: "python3"}}
	if p := hubOf(g, state, nil, logf); p != nil || g.HubKey != nil || len(logs) != 0 {
		t.Fatalf("no hub named: nothing signed as one: %v", logs)
	}
	logs = nil
	g = &web.Garden{Conf: config.Garden{Name: "shop", Path: dir, Python: "python3", Hub: "box-hub"}}
	if p := hubOf(g, state, nil, logf); p != nil || g.HubKey != nil || len(logs) != 1 || !strings.Contains(logs[0], "hub.py install") {
		t.Fatalf("a hub with no key yet signs nothing, and the log says what makes its key: %v", logs)
	}
	key := hubkey.Path(state, hubkey.ID(dir))
	if err := os.MkdirAll(filepath.Dir(key), 0o700); err != nil {
		t.Fatal(err)
	}
	if out, err := exec.Command("ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", key).CombinedOutput(); err != nil {
		t.Fatalf("ssh-keygen: %v %s", err, out)
	}
	logs = nil
	p := hubOf(g, state, nil, logf)
	if p == nil || g.HubKey == nil || g.HubKey.Path != key {
		t.Fatalf("the hub's key is found, and kept for /api/keys/hub: %v %v", g.HubKey, logs)
	}
	// UNTIL THE GARDEN NAMES IT, NOTHING IS SIGNED WITH IT: a hub judges a merge's writer at its first parent, so a merge
	// signed by a key the last commit does not name would be refused there and kept here
	if got := p(); got != nil || len(logs) != 2 || !strings.Contains(logs[1], "not named") {
		t.Fatalf("a key the hub's bean does not name signs nothing, and the log says so: %v %v", got, logs)
	}
	if got := p(); got != nil || len(logs) != 2 {
		t.Fatalf("...said once, not at every step: %v", logs)
	}
	commit := func(text string) {
		t.Helper()
		if err := os.MkdirAll(filepath.Join(dir, "beans"), 0o755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, "beans", "box-hub.md"), []byte(text), 0o644); err != nil {
			t.Fatal(err)
		}
		for _, a := range [][]string{{"add", "-A"}, {"-c", "user.name=sam", "-c", "user.email=sam@x", "commit", "-q", "-m", "the hub"}} {
			if out, err := exec.Command("git", append([]string{"-C", dir}, a...)...).CombinedOutput(); err != nil {
				t.Fatalf("git %v: %v %s", a, err, out)
			}
		}
	}
	bean := "---\nbean: box-hub\nkind: instance\ntitle: \"the shop's hub\"\nstatements:\n  - say: { by: sam, at: now }\n" +
		"  - name: { id: key, by: ssh, of: self, as: \"%s\" }\n---\nThe hub.\n"
	commit(fmt.Sprintf(bean, "SHA256:"+strings.Repeat("A", 43)))
	if got := p(); got != nil {
		t.Fatalf("a bean naming another key names not this one: %v", got)
	}
	commit(fmt.Sprintf(bean, g.HubKey.Fingerprint))
	params := p()
	if params == nil || len(logs) != 3 || !strings.Contains(logs[2], "is named") {
		t.Fatalf("once the gardener's commit names it on the hub's bean, the hub signs, and the log says so once: %v", logs)
	}
	sign, _ := params["sign"].(map[string]string)
	if params["by"] != "box-hub" || sign["GIT_AUTHOR_NAME"] != "box-hub" || sign["GIT_CONFIG_VALUE_1"] != key ||
		sign["GIT_AUTHOR_EMAIL"] != "box-hub@shop.daftar.invalid" {
		t.Fatalf("a step is asked as the hub's bean, signed with its key: %v", params)
	}
	if !strings.Contains(logs[0], g.HubKey.Fingerprint) || strings.Contains(strings.Join(logs, "\n"), key) {
		t.Fatalf("the log names the hub's key by its fingerprint, never by where it lies: %v", logs)
	}
}
