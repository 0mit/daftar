package web

import (
	"encoding/json"
	"strings"
	"testing"

	"github.com/0mit/daftar/daftard/internal/register"
)

// THE ROUTES DAFTARD KEEPS HEAR WHAT A LOOKUP FOUND, as a register's hear the worker: a route that refused is tried
// after the one that answered, which is seen as the one that answered last; /health shows the place service's routes
// beside the registers', healthy or not and never where they go.
func TestAPlaceServicesRoutesHearWhatALookupFound(t *testing.T) {
	ph := newPhoton(t)
	s := placesServer(t, "place-host", ph)
	g := s.Gardens[0]
	g.Conf.PlaceService = byRoutes(t, closedPort(t), ph.srv.URL)
	g.PlaceRoutes = register.NewPlaces("g", g.Conf.PlaceService, t.Logf)
	g.PlaceRoutes.Run()
	defer g.PlaceRoutes.Close()

	if a := ask(t, s, "/api/places/far?g=g&q="+q("فلسطین")); !a.Sent || len(ph.requests()) != 1 {
		t.Fatalf("the lookup, by the second route: %+v (%d sent)", a, len(ph.requests()))
	}
	if o := g.PlaceRoutes.Order(); len(o) == 0 || o[0].Route != 2 {
		t.Fatalf("the route that answered first now, the one that refused after it: %+v", o)
	}
	if st := g.PlaceRoutes.State(false); st["answered"].(map[string]any)["route"] != 2 {
		t.Fatalf("which route answered last: %v", st)
	}
	w := get(s, "/health", false)
	var h struct {
		Places map[string]struct {
			Routes []map[string]any `json:"routes"`
		} `json:"place_services"`
	}
	if err := json.Unmarshal(w.Body.Bytes(), &h); err != nil || len(h.Places["g"].Routes) != 2 {
		t.Fatalf("/health shows the place service's routes: %s", w.Body.String())
	}
	if strings.Contains(w.Body.String(), ph.srv.URL) || strings.Contains(w.Body.String(), "label") {
		t.Fatalf("/health never says where a route goes: %s", w.Body.String())
	}
}
