package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// A PLACE SERVICE IS REACHED AS A REGISTER IS: by its `url` alone, as before, or by `routes` tried in order — its own
// address by TLS, or plain HTTP on this machine's loopback; or a forward through its host by ssh, with the garden's
// ssh key and that host's key pinned in the state folder — and daftard.json is refused where a route could not be
// taken safely: what a person types would cross a network in the clear, an ssh host is trusted unpinned, or nothing
// says which party the lookups go to.
func TestPlaceServiceIsCheckedAsARegistersRoutesAre(t *testing.T) {
	t.Setenv("DAFTARD_STATE", t.TempDir())
	if err := os.MkdirAll(filepath.Join(os.Getenv("DAFTARD_STATE"), "registers"), 0o700); err != nil {
		t.Fatal(err)
	}
	known := filepath.Join(os.Getenv("DAFTARD_STATE"), "registers", "g.known_hosts")
	if err := os.WriteFile(known, []byte("places.example.org "+testKey+"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	load := func(svc string) error {
		var ps map[string]any
		if err := json.Unmarshal([]byte(svc), &ps); err != nil {
			t.Fatal(err)
		}
		c := map[string]any{"gardens": []any{map[string]any{"name": "g", "path": t.TempDir(), "place_service": ps}}}
		b, _ := json.Marshal(c)
		if err := os.WriteFile(filepath.Join(os.Getenv("DAFTARD_STATE"), "daftard.json"), b, 0o600); err != nil {
			t.Fatal(err)
		}
		_, err := Load()
		return err
	}
	ssh := `{"via": "ssh", "host": "places.example.org", "user": "tunnel", "to": "127.0.0.1:2322"}`
	for name, svc := range map[string]string{
		"its url alone, as before":          `{"url": "https://places.example.org", "party": "place-host"}`,
		"behind a path":                     `{"url": "https://places.example.org/photon", "party": "place-host"}`,
		"on this machine's loopback, plain": `{"url": "http://127.0.0.1:2322", "party": "place-host"}`,
		"by https, then by ssh":             `{"routes": [{"via": "https", "url": "https://places.example.org"}, ` + ssh + `], "party": "place-host"}`,
		"by ssh alone, through its host":    `{"routes": [` + ssh + `], "party": "place-host"}`,
	} {
		if err := load(svc); err != nil {
			t.Errorf("%s: refused: %v", name, err)
		}
	}
	for name, svc := range map[string]string{
		"plain HTTP beyond the loopback": `{"url": "http://203.0.113.10:2322", "party": "place-host"}`,
		"a name and password":            `{"url": "https://a:b@places.example.org", "party": "place-host"}`,
		"a query":                        `{"url": "https://places.example.org/?lang=fa", "party": "place-host"}`,
		"both url and routes":            `{"url": "https://places.example.org", "routes": [` + ssh + `], "party": "place-host"}`,
		"no address":                     `{"party": "place-host"}`,
		"a route of no kind":             `{"routes": [{"via": "vpn", "url": "https://places.example.org"}], "party": "place-host"}`,
		"ssh to a host not pinned":       `{"routes": [{"via": "ssh", "host": "other.example.org", "user": "tunnel", "to": "127.0.0.1:2322"}], "party": "place-host"}`,
		"ssh forwarding nowhere":         `{"routes": [{"via": "ssh", "host": "places.example.org", "user": "tunnel", "to": "127.0.0.1"}], "party": "place-host"}`,
		"no party":                       `{"url": "https://places.example.org"}`,
		"a party that is no bean":        `{"url": "https://places.example.org", "party": "Place Host!"}`,
	} {
		if err := load(svc); err == nil {
			t.Errorf("%s: taken", name)
		}
	}
}
