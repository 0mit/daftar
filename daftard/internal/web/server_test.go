package web

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"testing"
	"testing/fstest"
)

func TestPlainLine(t *testing.T) {
	for _, s := range []string{"دفتر من", "Cases", "پرونده‌ها (۳)", ""} {
		if !plainLine(s) {
			t.Errorf("plainLine(%q) = false", s)
		}
	}
	for _, s := range []string{"a\nb", "a\tb", "x\u202Ey", "x\u2066y\u2069", "\u200Fx", "a\x00", "\xff"} {
		if plainLine(s) {
			t.Errorf("plainLine(%q) = true", s)
		}
	}
}

func server() *Server {
	s := &Server{Listen: "127.0.0.1:8790", Token: "k", CSRF: "c",
		Assets: fstest.MapFS{"app/index.html": {Data: []byte("app")}, "index.html": {Data: []byte("old")}}}
	s.Handler()
	return s
}

func get(s *Server, target string, cookie bool) *httptest.ResponseRecorder {
	r := httptest.NewRequest("GET", target, nil)
	r.Host = "127.0.0.1:8790"
	if cookie {
		r.AddCookie(&http.Cookie{Name: cookieName, Value: s.page})
	}
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	return w
}

// door asks the server for a one-time code, the machine's key in a header, as `daftard open` does.
func door(s *Server, key string) (int, string) {
	r := httptest.NewRequest("POST", "/door", nil)
	r.Host = "127.0.0.1:8790"
	r.Header.Set("X-Daftard-Key", key)
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	var got struct {
		Once string `json:"once"`
	}
	_ = json.Unmarshal(w.Body.Bytes(), &got)
	return w.Code, got.Once
}

// THE KEY NEVER TRAVELS IN A URL (security audit 2026-10-10, 2.2): `daftard open` sends it in a header and gets a
// one-time code; the page is opened by the code, good once, and it lands only on this server's own pages.
func TestKeyRedirectsOnlyToALanding(t *testing.T) {
	s := server()
	cases := map[string]string{
		"to=/go/home/pending/x":                     "/go/home/pending/x",
		"to=//evil.example/":                        "/",
		"to=https://evil.example/go/home":           "/",
		"to=/api/stop":                              "/",
		"to=/go/home/pending/x%0d%0aSet-Cookie:a=b": "/",
		"g=home":                       "/?g=home",
		"to=/go/home&static=1&admin=1": "/go/home?admin=1&static=1",
		"g=home&debug=1&admin=x":       "/?g=home&debug=1",
		// a garden's Odoo screens, as `daftard open` passes them on (its door, odoo.go), and in no other form
		"to=%2Fodoo%3Fg%3Dhome%26series%3D19.0": "/odoo?g=home&series=19.0",
		"to=%2Fodoo%3Fseries%3D19.0%26g%3Dhome": "/",
	}
	for in, want := range cases {
		code, once := door(s, "k")
		if code != 200 || once == "" {
			t.Fatalf("the door gave no code for the machine's key: %d", code)
		}
		w := get(s, "/?once="+url.QueryEscape(once)+"&"+in, false)
		if w.Code != http.StatusSeeOther || w.Header().Get("Location") != want {
			t.Errorf("%s → %d %q; want 303 %q", in, w.Code, w.Header().Get("Location"), want)
		}
		if w := get(s, "/?once="+url.QueryEscape(once)+"&"+in, false); w.Code != 403 {
			t.Errorf("a code spent once opens nothing again: %d", w.Code)
		}
	}
	if code, once := door(s, "wrong"); code != 403 || once != "" {
		t.Errorf("a wrong key gets no code: %d %q", code, once)
	}
	if w := get(s, "/?key=k&to=/go/home", false); w.Code == http.StatusSeeOther {
		t.Errorf("the key itself in a URL opens nothing any more: %d", w.Code)
	}
	if w := get(s, "/?once=made-up", false); w.Code != 403 {
		t.Errorf("a code nobody was given → %d", w.Code)
	}
}

func TestLandingServesTheHandplace(t *testing.T) {
	s := server()
	if w := get(s, "/go/home/pending/example", true); w.Code != 200 || w.Body.String() != "app" {
		t.Errorf("landing → %d %q", w.Code, w.Body.String())
	}
	if w := get(s, "/go/home/pending/example", false); w.Code != 403 {
		t.Errorf("landing without the key → %d", w.Code)
	}
	if w := get(s, "/go/home/unknown/x", true); w.Code != 404 {
		t.Errorf("an unknown kind → %d", w.Code)
	}
	if w := get(s, "/old", true); w.Body.String() != "old" {
		t.Errorf("/old → %q", w.Body.String())
	}
}

// swap opens the page as a browser does: a code from the door, spent at /?once=, and the cookie its answer sets.
func swap(t *testing.T, s *Server) *http.Cookie {
	t.Helper()
	code, once := door(s, "k")
	if code != 200 {
		t.Fatalf("the door gave no code: %d", code)
	}
	w := get(s, "/?once="+url.QueryEscape(once), false)
	for _, c := range w.Result().Cookies() {
		if c.Name == cookieName {
			return c
		}
	}
	t.Fatalf("the code's answer sets no cookie: %d", w.Code)
	return nil
}

// THE COOKIE IS NOT THE KEY (security audit 2026-10-10, 2.7): a cookie reaches every port of 127.0.0.1, so whatever
// listens on another one the person visits is sent it. It carries a value made when this daftard started, good on
// this run alone; the machine's key opens a page only in the header the command line sends, which no browser sends
// on its own — never as a cookie.
func TestTheCookieIsNotTheKey(t *testing.T) {
	s := server()
	c := swap(t, s)
	if c.Value == "k" {
		t.Fatalf("the cookie carries the machine's key: %q", c.Value)
	}
	if !c.HttpOnly || c.SameSite != http.SameSiteStrictMode || c.Path != "/" {
		t.Fatalf("the cookie is HttpOnly, SameSite=Strict, the whole page's: %+v", c)
	}
	with := func(s *Server, name, value, header string) int {
		r := httptest.NewRequest("GET", "/api/session", nil)
		r.Host = "127.0.0.1:8790"
		if name != "" {
			r.AddCookie(&http.Cookie{Name: name, Value: value})
		}
		if header != "" {
			r.Header.Set("X-Daftard-Key", header)
		}
		w := httptest.NewRecorder()
		s.ServeHTTP(w, r)
		return w.Code
	}
	if code := with(s, cookieName, c.Value, ""); code == 403 {
		t.Fatalf("the page's own cookie opens it: %d", code)
	}
	if code := with(s, cookieName, "k", ""); code != 403 {
		t.Fatalf("the machine's key as a cookie opens nothing: %d", code)
	}
	if code := with(s, "", "", "k"); code == 403 {
		t.Fatalf("the command line's header, the key in it, opens it: %d", code)
	}
	if code := with(s, "", "", "wrong"); code != 403 {
		t.Fatalf("a wrong key in the header opens nothing: %d", code)
	}
	if again := swap(t, s); again.Value != c.Value {
		t.Fatalf("one value a run: every page opened by the door shares it")
	}
	if code := with(server(), cookieName, c.Value, ""); code != 403 {
		t.Fatalf("daftard started again does not take the last run's cookie: %d", code)
	}
}
