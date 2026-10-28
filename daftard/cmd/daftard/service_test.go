package main

import (
	"encoding/json"
	"encoding/xml"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
)

// The systemd unit runs `daftard serve` from the binary installed, with the state folder and PATH it was installed
// with, every word quoted as systemd reads it.
func TestUnitText(t *testing.T) {
	u := unitText("/home/sam/my state/bin/daftard", [][2]string{{"DAFTARD_STATE", "/home/sam/my state"}, {"PATH", `/usr/bin:/a"b%c`}})
	for _, want := range []string{
		"ExecStart=\"/home/sam/my state/bin/daftard\" serve\n",
		"Environment=\"DAFTARD_STATE=/home/sam/my state\"\n",
		"Environment=\"PATH=/usr/bin:/a\\\"b%%c\"\n",
		"Restart=on-failure\n", "WantedBy=default.target\n",
	} {
		if !strings.Contains(u, want) {
			t.Errorf("the unit lacks %q:\n%s", want, u)
		}
	}
}

// The launchd agent is a property list that parses, runs `daftard serve`, is started at load and again whenever it
// ends other than by `daftard stop`, and escapes what it carries.
func TestPlistText(t *testing.T) {
	p := plistText("/Users/sam/a&b/bin/daftard", [][2]string{{"PATH", "/opt/homebrew/bin:/usr/bin<x>"}})
	d := xml.NewDecoder(strings.NewReader(p))
	d.Strict = true
	d.Entity = xml.HTMLEntity
	for {
		if _, err := d.Token(); err == io.EOF {
			break
		} else if err != nil {
			t.Fatalf("the agent is no XML: %v\n%s", err, p)
		}
	}
	for _, want := range []string{
		"<string>" + launchdLabel + "</string>", "<string>/Users/sam/a&amp;b/bin/daftard</string>\n\t\t<string>serve</string>",
		"<key>PATH</key>\n\t\t<string>/opt/homebrew/bin:/usr/bin&lt;x&gt;</string>", "<key>RunAtLoad</key>\n\t<true/>",
		"<key>SuccessfulExit</key>\n\t\t<false/>",
	} {
		if !strings.Contains(p, want) {
			t.Errorf("the agent lacks %q:\n%s", want, p)
		}
	}
}

// An install again keeps what daftard.json holds that no flag names — the machine's settings, the other gardens, and
// this garden's own — and changes what the flags name; --no-service writes the file and nothing else.
func TestInstallKeeps(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("DAFTARD_STATE", dir)
	t.Setenv("HOME", filepath.Join(dir, "home")) // nothing of this account's own is touched, whatever the flags
	g1, g2 := filepath.Join(dir, "g1"), filepath.Join(dir, "g2")
	if err := install([]string{"--garden", g1, "--python", "python3", "--name", "one", "--listen", "127.0.0.1:18870",
		"--no-service"}); err != nil {
		t.Fatal(err)
	}
	c, err := config.Load()
	if err != nil || c.Listen != "127.0.0.1:18870" || len(c.Gardens) != 1 || c.Gardens[0].Routines {
		t.Fatalf("first install: %+v %v", c, err)
	}
	c.Shared, c.OdooListen = true, "127.0.0.1:18892"
	c.Gardens[0].Quiet, c.Gardens[0].Writers = true, []string{"sam"}
	if err := c.Save(); err != nil {
		t.Fatal(err)
	}
	if err := install([]string{"--garden", g2, "--python", "python3", "--name", "two", "--no-service"}); err != nil {
		t.Fatal(err)
	}
	if err := install([]string{"--garden", g1, "--python", "/usr/bin/python3", "--routines", "--no-service"}); err != nil {
		t.Fatal(err)
	}
	b, _ := os.ReadFile(config.Path())
	var raw map[string]any
	_ = json.Unmarshal(b, &raw)
	c, err = config.Load()
	if err != nil {
		t.Fatal(err)
	}
	if c.Listen != "127.0.0.1:18870" || !c.Shared || c.OdooListen != "127.0.0.1:18892" || len(c.Gardens) != 2 {
		t.Fatalf("the machine's settings were not kept: %s", b)
	}
	one, two := c.Garden("one"), c.Garden("two")
	if one == nil || two == nil || one.Path != g1 || !one.Quiet || len(one.Writers) != 1 || !one.Routines ||
		one.Python != "/usr/bin/python3" || two.Routines {
		t.Fatalf("a garden's own settings were not kept, or the flags not applied: %s", b)
	}
	if _, err := os.Stat(filepath.Join(dir, "home")); !os.IsNotExist(err) {
		t.Fatalf("--no-service wrote beyond daftard.json: %v", err)
	}
}

// The machine's settings written before any garden are built on, not written over.
func TestInstallOnBareSettings(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("DAFTARD_STATE", dir)
	if err := os.WriteFile(config.Path(), []byte(`{"listen": "127.0.0.1:18970", "odoo_listen": "127.0.0.1:18992"}`), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := install([]string{"--garden", dir, "--python", "python3", "--name", "g", "--no-service"}); err != nil {
		t.Fatal(err)
	}
	c, err := config.Load()
	if err != nil || c.Listen != "127.0.0.1:18970" || c.OdooListen != "127.0.0.1:18992" || c.Garden("g") == nil {
		t.Fatalf("the settings were not built on: %+v %v", c, err)
	}
}

// A daftard.json that does not read is never written over.
func TestInstallRefusesUnread(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("DAFTARD_STATE", dir)
	if err := os.WriteFile(config.Path(), []byte("{not json"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := install([]string{"--garden", dir, "--python", "python3", "--no-service"}); err == nil ||
		!strings.Contains(err.Error(), "does not read") {
		t.Fatalf("an unread daftard.json was not refused: %v", err)
	}
	if b, _ := os.ReadFile(config.Path()); string(b) != "{not json" {
		t.Fatalf("it was written over: %s", b)
	}
}
