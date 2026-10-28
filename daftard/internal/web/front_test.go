package web

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// a garden's daemon as the front door meets it: a /door that gives a code for the machine's key, a /health
func standInDaemon(t *testing.T, key string) *httptest.Server {
	t.Helper()
	d := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.URL.Path == "/door" && r.Header.Get(keyHeader) == key:
			_ = json.NewEncoder(w).Encode(map[string]string{"once": "daemon-code"})
		case r.URL.Path == "/health":
			_ = json.NewEncoder(w).Encode(map[string]string{"build": "x"})
		default:
			w.WriteHeader(403)
		}
	}))
	t.Cleanup(d.Close)
	return d
}

func frontRig(t *testing.T, daemons []Daemon) *Server {
	t.Helper()
	s := &Server{Listen: "127.0.0.1:8770", Token: "k", CSRF: "c", Errors: guided.Open()}
	s.front = s.FrontHandler(daemons)
	return s
}

func (s *Server) frontDo(method, target string, h map[string]string) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, target, nil)
	r.Host = "127.0.0.1:8770"
	for k, v := range h {
		r.Header.Set(k, v)
	}
	w := httptest.NewRecorder()
	s.front.ServeHTTP(w, r)
	return w
}

// THE FRONT DOOR OPENS EACH GARDEN'S OWN DAEMON: its code, good once, is spent there, and the browser is sent to the
// garden's daemon with that daemon's own code; a lead's garden (/go/<garden>/…) is the one opened.
func TestTheFrontDoorOpensTheGardensOwnDaemon(t *testing.T) {
	d := standInDaemon(t, "k")
	addr := strings.TrimPrefix(d.URL, "http://")
	s := frontRig(t, []Daemon{{Name: "ana", Addr: "127.0.0.1:1"}, {Name: "bo", Addr: addr}})
	if w := s.frontDo("POST", "/door", nil); w.Code != 403 {
		t.Fatalf("no key, no code: %d", w.Code)
	}
	w := s.frontDo("POST", "/door", map[string]string{keyHeader: "k"})
	var got struct{ Once string }
	_ = json.Unmarshal(w.Body.Bytes(), &got)
	w = s.frontDo("GET", "/?once="+url.QueryEscape(got.Once)+"&to="+url.QueryEscape("/go/bo/case/x"), nil)
	loc := w.Header().Get("Location")
	if w.Code != 303 || !strings.HasPrefix(loc, d.URL+"/?") || !strings.Contains(loc, "once=daemon-code") ||
		!strings.Contains(loc, "g=bo") || !strings.Contains(loc, "to=%2Fgo%2Fbo%2Fcase%2Fx") {
		t.Fatalf("sent to bo's daemon with its own code and the lead: %d %s", w.Code, loc)
	}
	if w := s.frontDo("GET", "/?once="+url.QueryEscape(got.Once)+"&g=bo", nil); w.Code != 403 {
		t.Fatalf("the front door's code is good once: %d", w.Code)
	}
	// a garden's board (`daftar board`) is opened on that garden's daemon, though another garden is the first
	w = s.frontDo("POST", "/door", map[string]string{keyHeader: "k"})
	_ = json.Unmarshal(w.Body.Bytes(), &got)
	w = s.frontDo("GET", "/?once="+url.QueryEscape(got.Once)+"&to="+url.QueryEscape("/board?g=bo"), nil)
	if loc := w.Header().Get("Location"); w.Code != 303 || !strings.HasPrefix(loc, d.URL+"/?") ||
		!strings.Contains(loc, "g=bo") || !strings.Contains(loc, "to=%2Fboard%3Fg%3Dbo") {
		t.Fatalf("the board sent to bo's daemon: %d %s", w.Code, loc)
	}
}

// ANY OTHER ADDRESS OF A GARDEN IS SENT ON AS IT IS, to its daemon: by `g`, by /go/<garden> and /release/<garden>; with
// no garden named, the first garden's.
func TestTheFrontDoorSendsAGardensAddressOn(t *testing.T) {
	s := frontRig(t, []Daemon{{Name: "ana", Addr: "127.0.0.1:8781"}, {Name: "bo", Addr: "127.0.0.1:8782"}})
	for target, want := range map[string]string{
		"/?g=bo":                       "http://127.0.0.1:8782/?g=bo",
		"/go/bo/case/x":                "http://127.0.0.1:8782/go/bo/case/x",
		"/release/bo/view_queue.js":    "http://127.0.0.1:8782/release/bo/view_queue.js",
		"/api/view/page?g=ana&page=p1": "http://127.0.0.1:8781/api/view/page?g=ana&page=p1",
		"/":                            "http://127.0.0.1:8781/",
	} {
		if w := s.frontDo("GET", target, nil); w.Code != 302 || w.Header().Get("Location") != want {
			t.Fatalf("%s: %d %s, want %s", target, w.Code, w.Header().Get("Location"), want)
		}
	}
	if w := s.frontDo("POST", "/api/view/write?g=ana", nil); w.Code != 404 {
		t.Fatalf("a write is never sent on by the front door: %d", w.Code)
	}
}

// THE MACHINE'S OWN: stopping wants the machine's key and the front door's CSRF; Odoo's seat wants the key.
func TestTheFrontDoorsOwnWantTheMachinesKey(t *testing.T) {
	s := frontRig(t, nil)
	stopped := make(chan struct{}, 1)
	s.Stop = func() { stopped <- struct{}{} }
	if w := s.frontDo("POST", "/api/stop", map[string]string{keyHeader: "k"}); w.Code != 403 {
		t.Fatalf("no CSRF, no stop: %d", w.Code)
	}
	if w := s.frontDo("POST", "/api/stop", map[string]string{keyHeader: "k", "X-CSRF-Token": "c"}); w.Code != 200 {
		t.Fatalf("stop: %d", w.Code)
	}
	select {
	case <-stopped:
	case <-time.After(5 * time.Second):
		t.Fatal("stopped")
	}
	if w := s.frontDo("POST", "/internal/odoo-issue", nil); w.Code != 403 {
		t.Fatalf("no key, no seat: %d", w.Code)
	}
	if w := s.frontDo("GET", "/health?quick=1", nil); w.Code != 200 || !strings.Contains(w.Body.String(), `"front":true`) {
		t.Fatalf("a quick health: %d %s", w.Code, w.Body.String())
	}
}

// A GARDEN'S DAEMON ANSWERS THE MACHINE'S QUESTIONS, with the machine's key alone, as the garden's worker answers them
// — a refusal comes back as the worker's own error — and is ended by the machine's daftard alone.
func TestAGardensDaemonAnswersTheMachine(t *testing.T) {
	v := newViewRig(t, "view")
	v.s.Own, v.s.Front = "g", "127.0.0.1:8770"
	srv := httptest.NewServer(v.s)
	defer srv.Close()
	addr := strings.TrimPrefix(srv.URL, "http://")
	v.s.Listen = addr
	v.s.Handler() // its hosts are its address's (DNS rebinding refused): the daemon as it listens here
	bad := &Remote{Garden: "g", Addr: addr, Token: "wrong"}
	if _, err := bad.Call("hello", nil, time.Minute); err == nil {
		t.Fatal("no key, no answer")
	}
	rm := &Remote{Garden: "g", Addr: addr, Token: "k"}
	raw, err := rm.Call("view_page", map[string]any{"page": "page-now", "reader": "sam"}, time.Minute)
	if err != nil || !strings.Contains(string(raw), "page-now") || v.last("view_page")["page"] != "page-now" {
		t.Fatalf("the garden's worker answers the machine: %v %s", err, raw)
	}
	_, err = rm.Call("prefs_check", map[string]any{"prefs": map[string]any{"locale": "nonsense"}}, time.Minute)
	if we, ok := worker.IsError(err); !ok || we.Status != 400 || we.Kind != "refused" {
		t.Fatalf("a refusal comes back as the worker's own error: %#v", err)
	}
	if _, err := (&Remote{Garden: "other", Addr: addr, Token: "k"}).Call("hello", nil, time.Minute); err == nil {
		t.Fatal("a garden the daemon does not serve is refused")
	}
	stopped := make(chan struct{}, 1)
	v.s.Stop = func() { stopped <- struct{}{} }
	ask := func(key string) int {
		r := httptest.NewRequest("POST", "/internal/stop", nil)
		r.Host = addr
		if key != "" {
			r.Header.Set(keyHeader, key)
		}
		w := httptest.NewRecorder()
		v.s.ServeHTTP(w, r)
		return w.Code
	}
	if code := ask(""); code != 403 {
		t.Fatalf("no key, no stop: %d", code)
	}
	code := ask("k")
	select {
	case <-stopped:
	case <-time.After(5 * time.Second):
		t.Fatalf("stopped by the machine's key: %d", code)
	}
}

// A GARDEN'S DAEMON KEEPS ITS OWN COOKIE, named for its garden, and sends another garden's address to the front door.
func TestAGardensDaemonKeepsItsOwnCookieAndSendsOthersOn(t *testing.T) {
	v := newViewRig(t, "view")
	v.s.Own, v.s.Front = "g", "127.0.0.1:8770"
	if c := v.s.cookie(); c != "daftard-g" {
		t.Fatalf("its cookie is named for its garden: %s", c)
	}
	if c := (&Server{}).cookie(); c != "daftard" {
		t.Fatalf("the machine's own: %s", c)
	}
	for target, want := range map[string]string{"/?g=other": "http://127.0.0.1:8770/?g=other",
		"/go/other/case/x": "http://127.0.0.1:8770/go/other/case/x"} {
		if w := v.do("GET", target, "", true); w.Code != 302 || w.Header().Get("Location") != want {
			t.Fatalf("%s: %d %s", target, w.Code, w.Header().Get("Location"))
		}
	}
	if w := v.do("GET", "/api/view/page?g=g&page=page-now", "", false); w.Code == 200 {
		t.Fatal("no cookie of its own, no page")
	}
}
