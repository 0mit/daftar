package main

import (
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"sync/atomic"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
)

// THE COMMAND LINE SPEAKS TO A DAFTARD OF EITHER SIDE OF 2.7 (security audit 2026-10-10): it sends the machine's key in
// the X-Daftard-Key header, which a daftard of now takes; one started before takes the key only as its cookie and
// refuses the header — so where the header is refused, the cookie is sent, to this machine's own listener, and
// `daftard stop`, run by a new binary put in the place of a running old one, still stops it.
func TestStopEitherDaftard(t *testing.T) {
	key := strings.Repeat("ab", 32)
	for name, takes := range map[string]func(*http.Request) bool{
		"a daftard of now (the header)": func(r *http.Request) bool { return r.Header.Get("X-Daftard-Key") == key },
		"a daftard from before (the cookie)": func(r *http.Request) bool {
			c, err := r.Cookie("daftard")
			return err == nil && c.Value == key && r.Header.Get("X-Daftard-Key") == ""
		},
	} {
		var stopped atomic.Bool
		srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			switch {
			case r.URL.Path == "/health" && !stopped.Load():
				_, _ = w.Write([]byte(`{"app": "daftard", "ready": true}`))
			case r.URL.Path == "/health":
				w.WriteHeader(503) // gone
			case !takes(r):
				w.WriteHeader(403)
				_, _ = w.Write([]byte("دسترسی مجاز نیست."))
			case r.URL.Path == "/api/stop" && r.Method == "POST" && r.Header.Get("X-CSRF-Token") == "c":
				stopped.Store(true)
				_, _ = w.Write([]byte(`{"stopping": true}`))
			default:
				_, _ = w.Write([]byte(`{"csrf": "c"}`))
			}
		}))
		st := t.TempDir()
		t.Setenv("DAFTARD_STATE", st)
		_ = os.WriteFile(filepath.Join(st, "key"), []byte(key+"\n"), 0o600)
		_ = os.WriteFile(filepath.Join(st, "daftard.json"), []byte(`{"listen": "`+strings.TrimPrefix(srv.URL, "http://")+
			`", "gardens": [{"name": "g", "path": "/nowhere"}]}`), 0o600)
		if err := stop(); err != nil || !stopped.Load() {
			t.Fatalf("%s: `daftard stop` stops it: %v", name, err)
		}
		srv.Close()
	}
}

// ANOTHER ACCOUNT'S LISTENER AT DAFTARD'S ADDRESS IS SENT NOTHING (found while fixing security audit 2026-10-10, 2.7):
// while daftard is down, any account may listen at its loopback address, and the command line sent it the machine's
// key — `stop` in the header, `open` to the door (and then the browser to it). Where the address is another account's,
// nothing goes; where it is this account's own, as before.
func TestNoKeyToAnotherAccountsListener(t *testing.T) {
	key := strings.Repeat("cd", 32)
	var heard, stopped atomic.Bool
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Header.Get("X-Daftard-Key") != "" || strings.Contains(r.Header.Get("Cookie"), key) {
			heard.Store(true)
		}
		switch r.URL.Path {
		case "/health":
			if stopped.Load() {
				w.WriteHeader(503)
				return
			}
			_, _ = w.Write([]byte(`{"app": "daftard", "ready": true}`))
		case "/api/stop":
			stopped.Store(true)
			_, _ = w.Write([]byte(`{"stopping": true}`))
		case "/door":
			_, _ = w.Write([]byte(`{"once": "a-code"}`))
		default:
			_, _ = w.Write([]byte(`{"csrf": "c", "stopping": true}`))
		}
	}))
	defer srv.Close()
	st := t.TempDir()
	t.Setenv("DAFTARD_STATE", st)
	_ = os.WriteFile(filepath.Join(st, "key"), []byte(key+"\n"), 0o600)
	addr := strings.TrimPrefix(srv.URL, "http://")
	_ = os.WriteFile(filepath.Join(st, "daftard.json"), []byte(`{"listen": "`+addr+`", "gardens": [{"name": "g", "path": "/nowhere"}]}`), 0o600)
	was := listenerUIDs
	t.Cleanup(func() { listenerUIDs = was })

	listenerUIDs = func(string) []int { return []int{os.Getuid() + 1} } // another account holds the address
	if err := stop(); err == nil || !strings.Contains(err.Error(), "another account") {
		t.Fatalf("`daftard stop` refuses another account's listener: %v", err)
	}
	if _, err := openCode(&config.Config{Listen: addr}, key); err == nil {
		t.Fatal("`daftard open` asks another account's listener for no code")
	}
	if heard.Load() {
		t.Fatal("another account's listener was sent the machine's key")
	}

	listenerUIDs = func(string) []int { return []int{os.Getuid()} } // this account's own daftard
	if once, err := openCode(&config.Config{Listen: addr}, key); err != nil || once != "a-code" || !heard.Load() {
		t.Fatalf("this account's own daftard is asked as before: %q %v", once, err)
	}
}
