package register

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
)

// A PLACE SERVICE'S ROUTES ARE KEPT AS A REGISTER'S ARE: each asked for its health — at Photon's own /status, with
// nothing typed — and handed in order; an ssh route forwards to the service's port on the far side with the garden's
// one ssh key and pinned host keys, the same files its register's routes take; daftard.log names them as the place
// service's.
func TestPlaceServiceRoutes(t *testing.T) {
	log := quick(t)
	var mu sync.Mutex
	var paths []string
	photon := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		mu.Lock()
		paths = append(paths, r.URL.RequestURI())
		mu.Unlock()
		_, _ = w.Write([]byte(`{"status":"Ok"}`))
	}))
	defer photon.Close()
	rs := NewPlaces("g", &config.PlaceService{URL: photon.URL + "/", Party: "place-host"}, log.printf)
	rs.Run()
	eventually(t, "the route asked for its health", time.Second, func() bool { mu.Lock(); defer mu.Unlock(); return len(paths) > 0 })
	mu.Lock()
	asked := append([]string{}, paths...)
	mu.Unlock()
	for _, p := range asked {
		if p != "/status" {
			t.Fatalf("a place service's health is its /status, asked with nothing in it: %q", p)
		}
	}
	if o := rs.Order(); len(o) != 1 || o[0].Route != 1 || o[0].URL != photon.URL || o[0].Down {
		t.Fatalf("its one route, in order: %+v", o)
	}
	rs.Close()
	if !strings.Contains(log.all(), "[g] place service route 1 ("+photon.URL+"): taken as healthy until it misses twice") {
		t.Fatalf("daftard.log names the place service's route:\n%s", log.all())
	}

	conf := &config.PlaceService{Party: "place-host", Routes: []config.Route{{Via: "ssh", Host: "places.example.org",
		User: "tunnel", To: "127.0.0.1:2322"}}}
	_ = os.MkdirAll(filepath.Dir(config.SSHKeyFile("g")), 0o700)
	if err := os.WriteFile(config.SSHKeyFile("g"), []byte("not a real key: the stand-in reads none\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(config.KnownHostsFile("g"), []byte("places.example.org ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := conf.Check("g"); err != nil {
		t.Fatalf("an ssh route to a pinned host: %v", err)
	}
	args := filepath.Join(t.TempDir(), "args")
	t.Setenv("DAFTARD_FAKE_SSH", "1")
	t.Setenv("DAFTARD_FAKE_SSH_ARGS", args)
	t.Setenv("DAFTARD_FAKE_SSH_HANG", filepath.Join(t.TempDir(), "hang"))
	ps := NewPlaces("g", conf, log.printf)
	self, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	ps.SSH = self
	ps.Run()
	defer ps.Close()
	eventually(t, "the forward healthy", 5*time.Second, func() bool { return len(ps.Order()) == 1 })
	url := ps.Order()[0].URL
	b, _ := os.ReadFile(args)
	got := " " + strings.ReplaceAll(string(b), "\n", " ") + " "
	for _, want := range []string{" -i " + config.SSHKeyFile("g") + " ", ` UserKnownHostsFile="` + config.KnownHostsFile("g") + `" `,
		" -l tunnel ", " -L " + strings.TrimPrefix(url, "http://") + ":127.0.0.1:2322 ", " -- places.example.org "} {
		if !strings.Contains(got, want) {
			t.Fatalf("ssh's arguments have no %q:\n%s", want, got)
		}
	}
	if !strings.Contains(log.all(), "place service route 1 (ssh tunnel@places.example.org:22 → 127.0.0.1:2322): forward on 127.0.0.1:") {
		t.Fatalf("daftard.log:\n%s", log.all())
	}
}
