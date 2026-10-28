package web

import (
	"bytes"
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"strings"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/custom"
	"github.com/0mit/daftar/daftard/internal/sitting"
)

// The test binary is ssh-keygen's askpass, as daftard is.
func TestMain(m *testing.M) {
	if os.Getenv(sitting.AskpassVar) != "" {
		os.Exit(sitting.AskpassMain(os.Args[1:]))
	}
	os.Exit(m.Run())
}

// A GARDEN THAT TAKES ONLY SIGNED WRITES, served on a real listener (ssh-keygen's askpass reaches it there): a writer's
// key made through the page, a write refused with nobody sitting, a sitting refused on a wrong passphrase and begun on
// the right one, and the write then the person's own commit, signed by their key.
func TestASittingSignsItsPersonsWrites(t *testing.T) {
	if _, err := exec.LookPath("ssh-keygen"); err != nil {
		t.Skip("no ssh-keygen on this machine")
	}
	dir := t.TempDir()
	if out, err := exec.Command("git", "init", "-q", dir).CombinedOutput(); err != nil {
		t.Fatalf("git init: %v %s", err, out)
	}
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	base := "http://" + ln.Addr().String()
	exe, _ := os.Executable()
	s := &Server{Listen: ln.Addr().String(), Token: "k", CSRF: "c", Keys: &sitting.Keys{Dir: t.TempDir()},
		Sittings: sitting.NewSittings(time.Hour), Askpass: sitting.NewAskpass()}
	s.Askpass.Exe, s.Askpass.Base = exe, base
	g := &Garden{Conf: config.Garden{Name: "g", Gardener: "ana", Writers: []string{"ana", "ben"}, Signed: true},
		Custom: custom.New(dir, "")}
	g.Custom.SignedOnly = true
	s.Gardens = []*Garden{g}
	srv := &http.Server{Handler: s.Handler()}
	go func() { _ = srv.Serve(ln) }()
	t.Cleanup(func() { _ = srv.Close() })

	var sitCookie *http.Cookie
	post := func(path string, body map[string]any) (int, map[string]any) {
		b, _ := json.Marshal(body)
		r, _ := http.NewRequest("POST", base+path+"?g=g", bytes.NewReader(b))
		r.Header.Set("Content-Type", "application/json")
		r.Header.Set("Origin", base)
		r.Header.Set("X-CSRF-Token", "c")
		r.AddCookie(&http.Cookie{Name: cookieName, Value: s.page})
		if sitCookie != nil {
			r.AddCookie(sitCookie)
		}
		resp, err := http.DefaultClient.Do(r)
		if err != nil {
			t.Fatal(err)
		}
		defer resp.Body.Close()
		for _, c := range resp.Cookies() {
			if c.Name == sittingCookie {
				sitCookie = c
			}
		}
		var out map[string]any
		_ = json.NewDecoder(resp.Body).Decode(&out)
		return resp.StatusCode, out
	}

	if code, out := post("/api/keys/make", map[string]any{"person": "ana", "passphrase": "ana's own words"}); code != 200 ||
		!strings.HasPrefix(out["fingerprint"].(string), "SHA256:") || !strings.Contains(out["statement"].(string), "by: ssh") {
		t.Fatalf("a writer's key is made through the page, its fingerprint for the gardener: %d %v", code, out)
	}
	if code, _ := post("/api/keys/make", map[string]any{"person": "ana", "passphrase": "another one"}); code != 409 {
		t.Fatalf("a key this machine keeps is never made over: %d", code)
	}
	if code, _ := post("/api/keys/make", map[string]any{"person": "eve", "passphrase": "eve's own words"}); code != 403 {
		t.Fatalf("no key for someone who does not sit here: %d", code)
	}
	if code, out := post("/api/labels", map[string]any{"key": "nav.cases", "text": "x", "was": "y"}); code != 409 ||
		out["sitting"] != true {
		t.Fatalf("with nobody sitting, a garden that takes only signed writes asks who is at the keyboard: %d %v", code, out)
	}
	if code, _ := post("/api/sitting/begin", map[string]any{"person": "ana", "passphrase": "not hers"}); code != 403 ||
		sitCookie != nil {
		t.Fatalf("a wrong passphrase begins no sitting: %d", code)
	}
	if code, _ := post("/api/sitting/begin", map[string]any{"person": "ben", "passphrase": "his"}); code != 409 {
		t.Fatalf("a writer with no key here is asked to make one: %d", code)
	}
	if code, out := post("/api/sitting/begin", map[string]any{"person": "ana", "passphrase": "ana's own words"}); code != 200 ||
		out["person"] != "ana" || sitCookie == nil {
		t.Fatalf("her passphrase begins her sitting: %d %v", code, out)
	}
	if code, out := post("/api/labels", map[string]any{"key": "nav.cases", "text": "x", "was": "y"}); code != 200 {
		t.Fatalf("in her sitting her write is taken: %d %v", code, out)
	}
	raw, err := exec.Command("git", "-C", dir, "cat-file", "commit", custom.Ref("ana")).CombinedOutput()
	if err != nil || !strings.Contains(string(raw), "BEGIN SSH SIGNATURE") || !strings.Contains(string(raw), "author ana <ana@g.daftar.invalid>") {
		t.Fatalf("her write is her own commit, signed by her key: %v %s", err, raw)
	}
	if len(s.Askpass.Pending()) != 0 {
		t.Fatalf("no answer is left once the write is done")
	}
	if code, _ := post("/api/sitting/end", map[string]any{}); code != 200 {
		t.Fatalf("a sitting ends when its person leaves: %d", code)
	}
	if code, _ := post("/api/labels", map[string]any{"key": "nav.cases", "text": "z", "was": "y"}); code != 409 {
		t.Fatalf("after it, nobody sits: %d", code)
	}
}

// ON A SHARED ACCOUNT reading is closed too: a garden's pages open to its gardener's sitting, and to nobody else's,
// nor to a page with nobody sitting; the session's token (to begin a sitting) and who may sit are all it says.
func TestASharedMachineClosesReading(t *testing.T) {
	s := &Server{Listen: "127.0.0.1:8790", Token: "k", CSRF: "c", Shared: true, Sittings: sitting.NewSittings(time.Hour)}
	g := &Garden{Conf: config.Garden{Name: "g", Gardener: "ana", Writers: []string{"ana", "ben"}}}
	s.Gardens = []*Garden{g}
	s.Handler()
	read := func(path, cookie string) int {
		r := httptest.NewRequest("GET", path+"?g=g", nil)
		r.Host = "127.0.0.1:8790"
		r.AddCookie(&http.Cookie{Name: cookieName, Value: s.page})
		if cookie != "" {
			r.AddCookie(&http.Cookie{Name: sittingCookie, Value: cookie})
		}
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		return w.Code
	}
	for _, p := range []string{"/api/dashboard", "/api/books", "/api/history", "/api/calendar", "/api/leads",
		"/api/pending", "/api/proposal", "/view", "/api/events"} {
		if code := read(p, ""); code != 409 {
			t.Errorf("%s with nobody sitting: %d, not 409", p, code)
		}
		if code := read(p, s.Sittings.Begin("ben", "x")); code != 403 {
			t.Errorf("%s in another writer's sitting: %d, not 403", p, code)
		}
	}
	if code := read("/api/sitting", ""); code != 200 {
		t.Errorf("who may sit is said to anyone at the keyboard: %d", code)
	}
	if code := read("/api/session", ""); code != 200 { // no worker here: the garden's own part is not asked for
		t.Errorf("the session's token, to begin a sitting with, is given with nobody sitting: %d", code)
	}
}
