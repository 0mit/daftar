package web

import (
	"encoding/json"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/hubkey"
)

// THE HUB'S KEY, FOR THE GARDENER TO NAME: /api/keys/hub shows the fingerprint of this machine's hub of the garden,
// the statement its bean takes (class F, the gardener's to add) and whether the garden names it there yet (here, a
// garden with no commit: not named); a garden that names no hub, or whose hub has no key yet, is said so.
func TestTheHubsKeyIsShownForItsBean(t *testing.T) {
	s := server()
	g := &Garden{Conf: config.Garden{Name: "shop"}}
	s.Gardens = []*Garden{g}
	read := func(path string) (int, map[string]any) {
		w := get(s, path, true)
		var got map[string]any
		_ = json.Unmarshal(w.Body.Bytes(), &got)
		return w.Code, got
	}
	if code, _ := read("/api/keys/hub?g=shop"); code != 404 {
		t.Fatalf("a garden that names no hub here signs nothing as one: %d", code)
	}
	g.Conf.Hub = "box-hub"
	if code, got := read("/api/keys/hub?g=shop"); code != 404 || got["hub"] != "box-hub" ||
		!strings.Contains(got["error"].(string), "bin/hub.py install") {
		t.Fatalf("a hub with no key yet: said so, and what makes it: %d %v", code, got)
	}
	fpr := "SHA256:" + strings.Repeat("A", 43)
	g.HubKey = &hubkey.Key{Path: "/nowhere/key", Fingerprint: fpr}
	code, got := read("/api/keys/hub?g=shop")
	if code != 200 || got["hub"] != "box-hub" || got["fingerprint"] != fpr || got["named"] != false ||
		got["statement"] != `name: { by: ssh, of: self, as: "`+fpr+`" }` {
		t.Fatalf("the hub's key: its bean, its fingerprint and the statement for the bean: %d %v", code, got)
	}
	if _, ok := got["path"]; ok || strings.Contains(get(s, "/api/keys/hub?g=shop", true).Body.String(), "/nowhere") {
		t.Fatalf("where the key lies is never shown: %v", got)
	}
}
