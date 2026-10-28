package config

import (
	"os"
	"strings"
	"testing"
)

func loadText(t *testing.T, text string) (*Config, error) {
	t.Helper()
	t.Setenv("DAFTARD_STATE", t.TempDir())
	if err := os.WriteFile(Path(), []byte(text), 0o600); err != nil {
		t.Fatal(err)
	}
	return Load()
}

// EACH GARDEN ITS OWN DAEMON'S ADDRESS (one daemon per garden): given, or the machine's port and 11 plus its place;
// two gardens of one name, two daemons at one address, the machine's own or Odoo's, and an address beyond the
// loopback are refused when daftard.json is read.
func TestEachGardenHasItsOwnDaemonsAddress(t *testing.T) {
	c, err := loadText(t, `{"listen": "127.0.0.1:8770", "gardens": [{"name": "ana", "path": "/a"}, {"name": "bo", "path": "/b"},
		{"name": "cy", "path": "/c", "listen": "127.0.0.1:9000"}]}`)
	if err != nil {
		t.Fatal(err)
	}
	if got := []string{c.Gardens[0].Listen, c.Gardens[1].Listen, c.Gardens[2].Listen}; got[0] != "127.0.0.1:8781" ||
		got[1] != "127.0.0.1:8782" || got[2] != "127.0.0.1:9000" {
		t.Fatalf("each its own address: %v", got)
	}
	if c.Garden("bo") == nil || c.Garden("bo").Path != "/b" || c.Garden("nobody") != nil {
		t.Fatal("a garden by its name")
	}
	for why, text := range map[string]string{
		"two gardens are named ana": `{"gardens": [{"name": "ana", "path": "/a"}, {"name": "ana", "path": "/b"}]}`,
		"is garden ana's already": `{"gardens": [{"name": "ana", "path": "/a", "listen": "127.0.0.1:9000"},
			{"name": "bo", "path": "/b", "listen": "127.0.0.1:9000"}]}`,
		"the machine's own page":      `{"listen": "127.0.0.1:8770", "gardens": [{"name": "ana", "path": "/a", "listen": "127.0.0.1:8770"}]}`,
		"Odoo's origin":               `{"odoo_listen": "127.0.0.1:8792", "gardens": [{"name": "ana", "path": "/a", "listen": "127.0.0.1:8792"}]}`,
		"not this machine's loopback": `{"gardens": [{"name": "ana", "path": "/a", "listen": "192.0.2.5:9000"}]}`,
	} {
		if _, err := loadText(t, text); err == nil || !strings.Contains(err.Error(), why) {
			t.Fatalf("refused, %s: %v", why, err)
		}
	}
}
