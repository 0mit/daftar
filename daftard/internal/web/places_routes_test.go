package web

import (
	"encoding/json"
	"net"
	"net/http"
	"net/http/httptest"
	"strings"
	"sync/atomic"
	"testing"

	"github.com/0mit/daftar/daftard/internal/config"
)

// byRoutes is a place service named by its routes, each an address tried in this order, as daftard.json names them.
func byRoutes(t *testing.T, urls ...string) *config.PlaceService {
	t.Helper()
	ws := []map[string]string{}
	for _, u := range urls {
		ws = append(ws, map[string]string{"via": "https", "url": u})
	}
	b, _ := json.Marshal(map[string]any{"party": "place-host", "routes": ws})
	var svc config.PlaceService
	if err := json.Unmarshal(b, &svc); err != nil {
		t.Fatal(err)
	}
	return &svc
}

// closedPort is an address of the loopback nothing listens on: a route that refuses at once.
func closedPort(t *testing.T) string {
	t.Helper()
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	addr := l.Addr().String()
	_ = l.Close()
	return "http://" + addr
}

// A PLACE SERVICE BY ITS ROUTES: a lookup goes by the first route; one that fails at the connection is asked once
// more by the next — a lookup is a read, and asking it again repeats nothing — but never after an answer (an HTTP
// error is the service's own answer), and never a third time; a lookup the law seals reaches no route at all.
func TestAPlaceServiceIsReachedByItsRoutes(t *testing.T) {
	ph, other := newPhoton(t), newPhoton(t)
	s := placesServer(t, "place-host", ph)
	far := "/api/places/far?g=g&q=" + q("فلسطین")

	s.Gardens[0].Conf.PlaceService = byRoutes(t, closedPort(t), ph.srv.URL)
	a := ask(t, s, far)
	if !a.Sent || len(a.Places) != 1 || a.Places[0]["osm"] != "way/42" || len(ph.requests()) != 1 {
		t.Fatalf("the first route refused, the lookup asked once more by the second: %+v (%d sent)", a, len(ph.requests()))
	}

	var failed atomic.Int64
	failing := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		failed.Add(1)
		http.Error(w, "busy", http.StatusServiceUnavailable)
	}))
	defer failing.Close()
	s.Gardens[0].Conf.PlaceService = byRoutes(t, failing.URL, other.srv.URL)
	if a := ask(t, s, far); a.Sent || !strings.Contains(a.Why, "503") || failed.Load() != 1 || len(other.requests()) != 0 {
		t.Fatalf("an HTTP error is the service's answer, never asked of another route: %+v (%d, %d)", a, failed.Load(),
			len(other.requests()))
	}

	s.Gardens[0].Conf.PlaceService = byRoutes(t, closedPort(t), closedPort(t), other.srv.URL)
	if a := ask(t, s, far); a.Sent || !strings.Contains(a.Why, "did not answer") || len(other.requests()) != 0 {
		t.Fatalf("two routes refused: asked once more and no third time: %+v (%d)", a, len(other.requests()))
	}

	s.Gardens[0].Conf.PlaceService = byRoutes(t, ph.srv.URL)
	n := len(ph.requests())
	for _, sealed := range []string{far + "&sealed=1", far + "&for=meeting"} {
		if a := ask(t, s, sealed); a.Sent || !strings.HasPrefix(a.Why, "sealed") {
			t.Errorf("%s: %+v", sealed, a)
		}
	}
	if len(ph.requests()) != n {
		t.Fatalf("a sealed lookup reached a route: %d requests", len(ph.requests())-n)
	}
}
