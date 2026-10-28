package web

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"testing"
	"time"

	assets "github.com/0mit/daftar/daftard/web"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/served"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// WHAT A STRANGER TYPES INTO THE SIGN-IN PAGE (security audit 2026-10-10, part 1): the garden's name and the person's
// name reach daftard as JSON. Whatever they hold — a path, capitals, a bidi control, a NUL, markup, a thousand letters,
// a number where a name goes — the page answers as it answers everyone, sends nothing, begins no session and does not
// fall over; only a well-formed name the garden knows and a grant names gets a link. A body that is not JSON, too big,
// or from another origin is refused before it is read; a passkey whose user handle is forged signs nobody in; and a
// signed-in reader cannot name a bean by a path.
func TestServedSignInInputs(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	if err := os.WriteFile(script, []byte(standIn), 0o644); err != nil {
		t.Fatal(err)
	}
	gc := config.Garden{Name: "g", Title: "The garden", Path: dir, Python: py, Served: true,
		Channels: []config.Channel{{Kind: "mail", Party: "mailhost", From: "daftard <d@example.org>", Command: []string{"sendmail", "-t"}}}}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	var mu sync.Mutex
	var sent []string
	t.Setenv("DAFTARD_STATE", t.TempDir())
	s := &Server{Gardens: []*Garden{g}, Assets: assets.FS, Errors: guided.Open()}
	s.Mail = func(ch config.Channel, msg []byte) error {
		mu.Lock()
		defer mu.Unlock()
		sent = append(sent, string(msg))
		return nil
	}
	h := s.ServedHandler([]string{"daftar.example.org"}, served.New())
	const origin = "https://daftar.example.org"
	raw := func(method, path, ctype string, body []byte, org string, cookie *http.Cookie) *httptest.ResponseRecorder {
		r := httptest.NewRequest(method, origin+path, bytes.NewReader(body))
		r.Host = "daftar.example.org"
		if ctype != "" {
			r.Header.Set("Content-Type", ctype)
		}
		if org != "" {
			r.Header.Set("Origin", org)
		}
		if cookie != nil {
			r.AddCookie(cookie)
		}
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		return w
	}
	post := func(path string, body any) *httptest.ResponseRecorder {
		b, _ := json.Marshal(body)
		return raw(http.MethodPost, path, "application/json", b, origin, nil)
	}
	mails := func() int {
		time.Sleep(300 * time.Millisecond) // a link is sent beside the answer
		mu.Lock()
		defer mu.Unlock()
		return len(sent)
	}
	said := ""
	hostile := []any{"../ana", "ana/../eve", "ANA", "ana\u202e", "ana\u2066x", "ana\x00", "<script>alert(1)</script>",
		"ana; rm -rf /", "a" + strings.Repeat("a", 1000), "", " ana", "ana ", "آنا", "ana\nTo: eve@example.org",
		5, 5.5, true, nil, []any{"ana"}, map[string]any{"id": "ana"}}
	for _, gname := range []any{"g", "../g", "G", "g\u202e", 7, nil} {
		for _, person := range hostile {
			w := post("/served/link", map[string]any{"g": gname, "person": person})
			if w.Code != http.StatusAccepted {
				t.Fatalf("link for g=%#v person=%#v: %d %s, want 202", gname, person, w.Code, w.Body.String())
			}
			if said == "" {
				said = w.Body.String()
			} else if w.Body.String() != said {
				t.Fatalf("link for g=%#v person=%#v answers differently: %s", gname, person, w.Body.String())
			}
			if c := w.Result().Cookies(); len(c) != 0 {
				t.Fatalf("link for %#v set a cookie", person)
			}
		}
	}
	if n := mails(); n != 0 {
		t.Fatalf("%d mail(s) sent for names no grant names: %v", n, sent)
	}
	for _, gname := range []any{"g/../g", "../g", "G"} { // a well-formed person in a garden named otherwise
		post("/served/link", map[string]any{"g": gname, "person": "ana"})
	}
	if n := mails(); n != 0 {
		t.Fatalf("a link was sent for a garden no name of this machine names: %d", n)
	}
	if w := post("/served/link", map[string]any{"g": "g", "person": "ana"}); w.Code != http.StatusAccepted || w.Body.String() != said {
		t.Fatalf("the one well-formed, granted person: %d %s", w.Code, w.Body.String())
	}
	if n := mails(); n != 1 || !strings.Contains(sent[0], "To: ana@example.org") {
		t.Fatalf("the granted person got %d mail(s): %v", n, sent)
	}

	// what is refused before it is read
	big := append([]byte(`{"g":"g","person":"`), bytes.Repeat([]byte("a"), 70000)...)
	big = append(big, []byte(`"}`)...)
	cases := []struct {
		name, ctype string
		body        []byte
		origin      string
		want        int
	}{
		{"a body over 64 KB", "application/json", big, origin, http.StatusRequestEntityTooLarge},
		{"a form instead of JSON", "application/x-www-form-urlencoded", []byte("g=g&person=ana"), origin, http.StatusUnsupportedMediaType},
		{"text that is not JSON", "application/json", []byte(`{"g": "g", "person": `), origin, http.StatusBadRequest},
		{"a JSON list", "application/json", []byte(`["g", "ana"]`), origin, http.StatusBadRequest},
		{"no Origin", "application/json", []byte(`{"g":"g","person":"ana"}`), "", http.StatusForbidden},
		{"another origin", "application/json", []byte(`{"g":"g","person":"ana"}`), "https://evil.example", http.StatusForbidden},
	}
	for _, c := range cases {
		if w := raw(http.MethodPost, "/served/link", c.ctype, c.body, c.origin, nil); w.Code != c.want {
			t.Fatalf("%s: %d %s, want %d", c.name, w.Code, w.Body.String(), c.want)
		}
	}
	if n := mails(); n != 1 {
		t.Fatalf("a refused request sent mail: %d", n)
	}

	// a forged passkey user handle signs nobody in
	b64 := base64.RawURLEncoding.EncodeToString
	for _, handle := range []string{b64([]byte("g/../ana")), b64([]byte("g/ANA")), b64([]byte("x/ana")), b64([]byte("g/ana\u202e")),
		b64([]byte("g")), "!!not base64!!", b64(bytes.Repeat([]byte("g/ana"), 5000))} {
		w := post("/served/passkey/in", map[string]any{"userHandle": handle, "id": b64([]byte("x")), "clientDataJSON": b64([]byte("{}")),
			"authenticatorData": b64([]byte("x")), "signature": b64([]byte("x"))})
		if w.Code != http.StatusForbidden || len(w.Result().Cookies()) != 0 {
			t.Fatalf("passkey with handle %q: %d, cookies %v", handle, w.Code, w.Result().Cookies())
		}
	}

	// signed in by the one link, a reader still cannot name a bean by a path
	m := regexp.MustCompile(`/#in=([A-Za-z0-9_-]+)`).FindStringSubmatch(sent[0])
	if m == nil {
		t.Fatalf("no link in the mail: %s", sent[0])
	}
	w := raw(http.MethodPost, "/served/in", "application/json", []byte(`{"t":"`+m[1]+`"}`), origin, nil)
	var cookie *http.Cookie
	for _, c := range w.Result().Cookies() {
		if c.Name == servedCookie {
			cookie = c
		}
	}
	if cookie == nil {
		t.Fatalf("the link did not sign ana in: %d", w.Code)
	}
	for _, id := range []string{"../notes", "notes/../notes", "/etc/passwd", "..%2Fnotes", "NOTES", "notes\x00", "notes.md"} {
		w := raw(http.MethodGet, "/served/bean?id="+url.QueryEscape(id), "", nil, "", cookie)
		if w.Code == http.StatusOK {
			t.Fatalf("bean %q was read: %s", id, w.Body.String())
		}
	}
	if w := raw(http.MethodGet, "/served/bean?id=notes", "", nil, "", cookie); w.Code != http.StatusOK {
		t.Fatalf("the bean her grant opens: %d %s", w.Code, w.Body.String())
	}
}
