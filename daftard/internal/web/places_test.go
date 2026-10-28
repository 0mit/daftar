package web

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// the flow law, as a stand-in worker answers it: the party `place-host` is granted, every other refused
const placeStandIn = `import json, sys
for line in sys.stdin:
    req = json.loads(line); p = req.get('params') or {}
    ok = req['method'] == 'may_send'
    v = {'granted': p.get('party') == 'place-host'} if ok else {'status': 404, 'message': 'unknown method', 'kind': 'failed'}
    sys.stdout.write(json.dumps({'id': req['id'], 'ok': ok, ('result' if ok else 'error'): v}) + '\n'); sys.stdout.flush()
`

// a garden's beans: a bookshop that says where it is; a meeting ahead, which people attend; a person whose home is
// held off git; and a note that is nowhere
var placeBeans = map[string]string{
	"bookshop": `---
bean: bookshop
kind: org
title: "کاخ کتاب"
statements:
  - be: { id: where, by: self, at: ["EPSG:4326;35.7001,51.4012", "osm:way/9001"], as: location }
---
A bookshop.
`,
	"meeting": `---
bean: meeting
kind: event
title: "a meeting ahead"
statements:
  - be: { id: when, by: self, at: "2027-03-01 10:00+03:30" }
  - attend: { by: [p-1a2b3c4d], of: self }
---
A meeting.
`,
	"p-1a2b3c4d": `---
bean: p-1a2b3c4d
kind: person
title: "p-1a2b3c4d"
statements:
  - be: { id: home, held: "root:store/0123456789abcdef0123456789abcdef" }
---
A person.
`,
	"note": `---
bean: note
kind: document
title: "کاخ notes"
statements:
  - say: { by: someone, at: "2026-10-01 10:00+03:30" }
---
Nowhere.
`,
}

// a sealed place-bundle/1, as internal/places reads one: two Palestines, one in each city, and the old name «کاخ»
func placeBundle(t *testing.T) string {
	t.Helper()
	dir := t.TempDir()
	files := map[string]any{}
	write := func(name string, rows [][]string) {
		f, err := os.Create(filepath.Join(dir, name))
		if err != nil {
			t.Fatal(err)
		}
		w := csv.NewWriter(f)
		_ = w.WriteAll(rows)
		f.Close()
		raw, _ := os.ReadFile(filepath.Join(dir, name))
		sum := sha256.Sum256(raw)
		files[name] = map[string]any{"sha256": hex.EncodeToString(sum[:]), "rows": len(rows) - 1}
	}
	write("places.csv", [][]string{{"code", "name", "name_en", "kind", "parent", "in_path", "latitude", "longitude", "source"},
		{"zz", "ایران", "", "country", "", "False", "", "", "osm:country-zz"},
		{"zz-tehran", "تهران", "", "city", "zz", "True", "35.6892", "51.3890", "osm:r8775"},
		{"zz-tehran-palestine", "فلسطین", "", "street", "zz-tehran", "True", "35.6976", "51.4023", "osm:w42"},
		{"zz-mashhad", "مشهد", "", "city", "zz", "True", "36.2970", "59.6062", "osm:r9000"},
		{"zz-mashhad-palestine", "فلسطین", "", "street", "zz-mashhad", "True", "36.30", "59.61", "osm:w43"}})
	write("aliases.csv", [][]string{{"place", "name", "kind", "source"}, {"zz-tehran-palestine", "کاخ", "old", "osm"}})
	manifest, _ := json.Marshal(map[string]any{"format": "place-bundle/1", "files": files, "sources": []any{
		map[string]string{"name": "OpenStreetMap", "licence": "ODbL-1.0", "attribution": "© OpenStreetMap contributors",
			"url": "https://www.openstreetmap.org/copyright"}}})
	if err := os.WriteFile(filepath.Join(dir, "manifest.json"), manifest, 0o644); err != nil {
		t.Fatal(err)
	}
	return dir
}

// photon stands in for a place service beyond the machine: it keeps every request it is sent, and answers one place —
// and its health at /status, which it does not count among them: a lookup is what it was sent.
type photon struct {
	mu   sync.Mutex
	seen []url.Values
	srv  *httptest.Server
}

func newPhoton(t *testing.T) *photon {
	p := &photon{}
	p.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Path == "/status" && r.URL.RawQuery == "" {
			_, _ = w.Write([]byte(`{"status":"Ok"}`))
			return
		}
		p.mu.Lock()
		p.seen = append(p.seen, r.URL.Query())
		p.mu.Unlock()
		if r.URL.Path != "/api" {
			http.Error(w, "no", 404)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"type":"FeatureCollection","features":[{"type":"Feature",
			"geometry":{"type":"Point","coordinates":[51.4023,35.6976]},
			"properties":{"osm_type":"W","osm_id":42,"osm_key":"highway","osm_value":"primary","type":"street",
			"name":"خیابان فلسطین","city":"تهران","country":"ایران","countrycode":"IR"}}]}`))
	}))
	t.Cleanup(p.srv.Close)
	return p
}

func (p *photon) requests() []url.Values {
	p.mu.Lock()
	defer p.mu.Unlock()
	return append([]url.Values{}, p.seen...)
}

type placesAnswer struct {
	Own    []map[string]any `json:"own"`
	Places []map[string]any `json:"places"`
	Ready  bool             `json:"ready"`
	Far    bool             `json:"far"`
	Sent   bool             `json:"sent"`
	Why    string           `json:"why"`
	Srcs   []map[string]any `json:"sources"`
}

func placesServer(t *testing.T, party string, ph *photon) *Server {
	t.Helper()
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	root := t.TempDir()
	if err := os.MkdirAll(filepath.Join(root, "beans"), 0o755); err != nil {
		t.Fatal(err)
	}
	for id, text := range placeBeans {
		if err := os.WriteFile(filepath.Join(root, "beans", id+".md"), []byte(text), 0o644); err != nil {
			t.Fatal(err)
		}
	}
	script := filepath.Join(t.TempDir(), "worker.py")
	if err := os.WriteFile(script, []byte(placeStandIn), 0o644); err != nil {
		t.Fatal(err)
	}
	gc := config.Garden{Name: "g", Path: root, Python: py, Gardener: "keeper",
		PlaceService: &config.PlaceService{URL: ph.srv.URL, Party: party}}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	s := server()
	s.Gardens = []*Garden{g}
	s.Places = NewPlaceIndex([]string{placeBundle(t)}, t.Logf)
	for i := 0; i < 200; i++ { // loaded in the background: a few milliseconds
		if ix, _, err := s.Places.current(); ix != nil || err != nil {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	return s
}

func ask(t *testing.T, s *Server, target string) placesAnswer {
	t.Helper()
	w := get(s, target, true)
	if w.Code != 200 {
		t.Fatalf("%s: %d %s", target, w.Code, w.Body.String())
	}
	var a placesAnswer
	if err := json.Unmarshal(w.Body.Bytes(), &a); err != nil {
		t.Fatalf("%s: %v %s", target, err, w.Body.String())
	}
	return a
}

func q(s string) string { return url.QueryEscape(s) }

// THE GARDEN'S OWN PLACES FIRST, THEN WHAT THIS MACHINE HOLDS: «کاخ» is a bookshop of the garden, with its coordinate
// and the map's element it was read from, and the street the country's bundle knows by that old name — each as the
// same rules rank them; nothing leaves the machine to answer it, and the bundle's sources are said, to be credited.
func TestPlacesHereTheGardensOwnFirst(t *testing.T) {
	ph := newPhoton(t)
	s := placesServer(t, "place-host", ph)
	a := ask(t, s, "/api/places?g=g&q="+q("کاخ"))
	if !a.Ready || len(a.Own) != 1 || a.Own[0]["code"] != "bookshop" || a.Own[0]["label"] != "کاخ کتاب" ||
		a.Own[0]["osm"] != "way/9001" {
		t.Fatalf("the garden's own: %+v", a.Own)
	}
	if pt, _ := a.Own[0]["point"].([]any); len(pt) != 2 || pt[0] != 35.7001 || pt[1] != 51.4012 {
		t.Errorf("its point: %v", a.Own[0]["point"])
	}
	if len(a.Places) == 0 || a.Places[0]["code"] != "zz-tehran-palestine" || a.Places[0]["field"] != "alias" ||
		a.Places[0]["osm"] != "way/42" {
		t.Errorf("the machine's: %+v", a.Places)
	}
	if len(a.Srcs) != 1 || a.Srcs[0]["attribution"] != "© OpenStreetMap contributors" {
		t.Errorf("the sources to credit: %+v", a.Srcs)
	}
	if !a.Far {
		t.Error("the page is not told a place service is named for the garden")
	}
	// a note that says nowhere is no place, and what is held off git holds none
	for _, o := range ask(t, s, "/api/places?g=g&q="+q("notes")).Own {
		t.Errorf("a being with no place answered: %v", o)
	}
	if n := len(ph.requests()); n != 0 {
		t.Errorf("a lookup on this machine sent %d requests beyond it", n)
	}
}

// THE READER'S POSITION, ONLY WHEN THEY ASK: two streets called «فلسطین»; asked with no position, the first in the
// bundle's order; asked near Mashhad, Mashhad's — lifted as the place one is within is.
func TestPlacesNearLiftsTheCityTheReaderIsIn(t *testing.T) {
	s := placesServer(t, "place-host", newPhoton(t))
	if a := ask(t, s, "/api/places?g=g&q="+q("فلسطین")); a.Places[0]["code"] != "zz-tehran-palestine" || a.Places[0]["boost"] != nil {
		t.Errorf("with no position: %+v", a.Places)
	}
	a := ask(t, s, "/api/places?g=g&q="+q("فلسطین")+"&near=36.31,59.58")
	if a.Places[0]["code"] != "zz-mashhad-palestine" || a.Places[0]["boost"] == nil {
		t.Errorf("near Mashhad: %+v", a.Places)
	}
	// far from every city: nothing is lifted
	if a := ask(t, s, "/api/places?g=g&q="+q("فلسطین")+"&near=10,10"); a.Places[0]["code"] != "zz-tehran-palestine" {
		t.Errorf("far from both: %+v", a.Places)
	}
}

// NOTHING ABOUT WHERE A PERSON WILL BE IS SENT TO A PLACE SERVICE (design §12). A lookup a page marks sealed; one for
// a happening ahead, which a person attends; one for a person whose home is held off git — each is answered as not
// sent, and the place service beyond the machine receives nothing at all. A lookup the law lets go carries what was
// typed and how many answers, and nothing of the garden; the reader's position goes only when they gave it.
func TestASealedFuturePositionNeverLeavesTheMachine(t *testing.T) {
	ph := newPhoton(t)
	s := placesServer(t, "place-host", ph)
	for _, target := range []string{
		"/api/places/far?g=g&q=" + q("فلسطین") + "&sealed=1",
		"/api/places/far?g=g&q=" + q("فلسطین") + "&for=meeting",
		"/api/places/far?g=g&q=" + q("فلسطین") + "&for=p-1a2b3c4d",
		"/api/places/far?g=g&q=" + q("فلسطین") + "&for=" + q("../beans/meeting"),
		"/api/places/far?g=g&q=" + q("فلسطین") + "&for=meeting&near=35.7,51.4",
	} {
		a := ask(t, s, target)
		if a.Sent || !strings.HasPrefix(a.Why, "sealed") || len(a.Places) != 0 {
			t.Errorf("%s: %+v", target, a)
		}
	}
	if n := len(ph.requests()); n != 0 {
		t.Fatalf("the place service was sent %d requests about where a person will be: %v", n, ph.requests())
	}

	a := ask(t, s, "/api/places/far?g=g&q="+q("فلسطین")+"&lang=fa&limit=5&for=bookshop")
	if !a.Sent || len(a.Places) != 1 || a.Places[0]["label"] != "خیابان فلسطین" || a.Places[0]["osm"] != "way/42" ||
		a.Places[0]["detail"] != "تهران · ایران" {
		t.Fatalf("a lookup the law lets go: %+v", a)
	}
	if pt, _ := a.Places[0]["point"].([]any); len(pt) != 2 || pt[0] != 35.6976 || pt[1] != 51.4023 {
		t.Errorf("its point, latitude first: %v", a.Places[0]["point"])
	}
	got := ph.requests()
	if len(got) != 1 {
		t.Fatalf("%d requests sent", len(got))
	}
	keys := []string{}
	for k := range got[0] {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	if strings.Join(keys, ",") != "lang,limit,q" || got[0].Get("q") != "فلسطین" || got[0].Get("limit") != "5" {
		t.Errorf("sent: %v", got[0])
	}
	ask(t, s, "/api/places/far?g=g&q="+q("فلسطین")+"&near=35.7,51.4")
	if got := ph.requests(); len(got) != 2 || got[1].Get("lat") != "35.7" || got[1].Get("lon") != "51.4" {
		t.Errorf("the reader's position, asked for: %v", got)
	}
}

// A PARTY THE GARDEN'S FLOW LAW DOES NOT GRANT IS SENT NOTHING (`sent-out`), and a service that answers by sending
// the lookup elsewhere is not followed.
func TestAPlaceServiceTheLawDoesNotGrantIsSentNothing(t *testing.T) {
	ph := newPhoton(t)
	s := placesServer(t, "a-host-not-granted", ph)
	if a := ask(t, s, "/api/places/far?g=g&q="+q("فلسطین")); a.Sent || !strings.Contains(a.Why, "flow law") {
		t.Errorf("not granted: %+v", a)
	}
	if n := len(ph.requests()); n != 0 {
		t.Errorf("%d requests sent to a party the law does not grant", n)
	}
	moved := httptest.NewServer(http.RedirectHandler(ph.srv.URL+"/api?q=x", http.StatusFound))
	defer moved.Close()
	s2 := placesServer(t, "place-host", ph)
	s2.Gardens[0].Conf.PlaceService.URL = moved.URL
	if a := ask(t, s2, "/api/places/far?g=g&q="+q("فلسطین")); a.Sent || !strings.Contains(a.Why, "302") {
		t.Errorf("a redirect: %+v", a)
	}
	if n := len(ph.requests()); n != 0 {
		t.Errorf("the redirect was followed: %d requests", n)
	}
}

// A BUNDLE THAT DOES NOT MATCH ITS SEAL IS NOT LOADED, and the page is told the machine's places are not ready rather
// than shown a guess; the garden's own places still answer.
func TestADamagedBundleIsNotLoaded(t *testing.T) {
	ph := newPhoton(t)
	s := placesServer(t, "place-host", ph)
	dir := placeBundle(t)
	f, _ := os.OpenFile(filepath.Join(dir, "places.csv"), os.O_APPEND|os.O_WRONLY, 0)
	_, _ = f.WriteString("zz-x,جای تازه,,city,zz,True,,,test\n")
	f.Close()
	s.Places = NewPlaceIndex([]string{dir}, t.Logf)
	for i := 0; i < 200; i++ {
		if _, _, err := s.Places.current(); err != nil {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	a := ask(t, s, "/api/places?g=g&q="+q("کاخ"))
	if a.Ready || len(a.Places) != 0 || len(a.Own) != 1 {
		t.Errorf("a damaged bundle: %+v", a)
	}
}

// PHOTON'S OWN ANSWERS, AS IT GAVE THEM: Photon 1.3.0 serving the Iran and Turkey dumps (testdata, captured in the
// rehearsal of 2026-10-11; OpenStreetMap's data, © OpenStreetMap contributors, ODbL 1.0) read as a page reads them —
// each place's own words, where it is from the nearest part of its address outward, its element, its point latitude
// first, and never the whole post code Photon gives.
func TestPhotonsOwnAnswersAreReadAsAPageReadsThem(t *testing.T) {
	read := func(name string) []map[string]any {
		raw, err := os.ReadFile(filepath.Join("testdata", name))
		if err != nil {
			t.Fatal(err)
		}
		found, err := photonAnswers(raw)
		if err != nil {
			t.Fatal(err)
		}
		b, _ := json.Marshal(found)
		var out []map[string]any
		_ = json.Unmarshal(b, &out)
		return out
	}
	tehran := read("photon-1.3.0-tehran-fa.json")
	if len(tehran) != 3 || tehran[0]["label"] != "تهران" || tehran[0]["osm"] != "relation/6663864" ||
		tehran[0]["code"] != "osm:relation/6663864" || tehran[0]["kind"] != "city" || tehran[0]["match"] != "place=city" ||
		tehran[0]["detail"] != "شهرستان تهران · استان تهران · ایران" {
		t.Fatalf("Tehran: %v", tehran)
	}
	if pt, _ := tehran[0]["point"].([]any); len(pt) != 2 || pt[0] != 35.6892523 || pt[1] != 51.3896004 {
		t.Errorf("Tehran's point: %v", tehran[0]["point"])
	}
	if tehran[2]["detail"] != "یافت آباد شمالی · منطقه ۱۷ · شهرستان تهران · استان تهران · ایران" || tehran[2]["osm"] != "way/253206781" {
		t.Errorf("a street called Tehran, in Tehran: %v", tehran[2])
	}
	near := read("photon-1.3.0-street-near.json")
	for _, a := range near {
		if strings.Contains(fmt.Sprint(a), "13144") || strings.Contains(fmt.Sprint(a), "17118") {
			t.Errorf("a whole post code passed on: %v", a)
		}
	}
	if near[1]["label"] != "خیابان وحید نظری" || near[1]["detail"] != "فلسطین - انقلاب · منطقه ۱۱ · تهران · شهرستان تهران · استان تهران · ایران" {
		t.Errorf("a street near: %v", near[1])
	}
}
