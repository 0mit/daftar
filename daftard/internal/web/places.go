package web

// THE PLACE LOOKUP (design §12): what a person types into a place, answered while they type — the garden's own places
// first, then what this machine holds (its place bundles, searched here, offline: internal/places), and beyond the
// machine only where the garden's flow law grants it. Two calls, so a page shows what is here at once and what comes
// from afar after it, if it comes at all:
//
//	GET /api/places?g=&q=&kinds=&within=&limit=&near=      this machine: {own, places, ready, sources, far}
//	GET /api/places/far?g=&q=&lang=&limit=&near=&for=&sealed=1   beyond it: {sent, why?, places, sources?}
//
// NOTHING ABOUT WHERE A PERSON WILL BE IS SENT (§12). A lookup for a place a page marks sealed, or for a being that
// says where people will be — a happening, a being with `attend`, a being whose place is held off git — is answered
// here and sent nowhere. The reader's own position (`near`) is given only when they ask; here it lifts the city
// nearest them, and it goes beyond the machine only with a lookup the law lets go. Neither a query nor a position is
// logged or kept.

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"sync"
	"time"
	"unicode/utf8"

	"github.com/0mit/daftar/daftard/internal/garden"
	"github.com/0mit/daftar/daftard/internal/places"
	"github.com/0mit/daftar/daftard/internal/register"
)

const (
	placeQueryRunes = 80 // as the responder cuts a query
	placeLimit      = 8
	placeMaxLimit   = 25
	nearKm          = 40 // a city further than this from the reader is not where they are
)

var nearRe = regexp.MustCompile(`^(-?\d{1,2}(?:\.\d{1,8})?),(-?\d{1,3}(?:\.\d{1,8})?)$`)
var placeLangRe = regexp.MustCompile(`^[a-z]{2,3}$`)
var geoRe = regexp.MustCompile(`^EPSG:4326;(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:@\d{4}(?:\.\d+)?)?$`)
var osmRe = regexp.MustCompile(`^osm:(node|way|relation)/([1-9][0-9]*)$`)

// PlaceIndex is this machine's own place search: the bundles daftard.json names, read and indexed once, and again when
// one of their manifests changes. Searches use the index in place until a new one is whole.
type PlaceIndex struct {
	Bundles []string
	mu      sync.Mutex
	ix      *places.Index
	sources []places.Source
	err     error
	stamp   string
	checked time.Time
	loading bool
	gen     uint64
	log     func(format string, a ...any)
}

// NewPlaceIndex is the search over these bundles, loaded in the background from now; each load is a line in log,
// saying what was loaded or why not (a path and a checksum, never a query).
func NewPlaceIndex(bundles []string, log func(format string, a ...any)) *PlaceIndex {
	p := &PlaceIndex{Bundles: bundles, log: log}
	p.mu.Lock()
	p.loading = true
	p.mu.Unlock()
	go p.load()
	return p
}

func (p *PlaceIndex) load() {
	started := time.Now()
	d, err := places.LoadBundle(p.Bundles)
	var ix *places.Index
	if err == nil {
		ix = places.BuildIndex(d, "", p.gen+1)
	}
	p.mu.Lock()
	defer p.mu.Unlock()
	p.loading, p.checked = false, time.Now()
	if err != nil {
		p.err = err // the index in use, if any, stays: a damaged copy never replaces a whole one
		if p.log != nil {
			p.log("places: not loaded: %v", err)
		}
		return
	}
	p.gen++
	p.ix, p.sources, p.stamp, p.err = ix, d.Sources, d.Stamp, nil
	if p.log != nil {
		p.log("places: generation %d from %s: %d places, in %s", p.gen, d.Origin, len(d.Places),
			time.Since(started).Round(time.Millisecond))
	}
}

// current is the index in use, its sources and the last error; at most once a minute it looks whether a bundle's
// manifest changed, and loads it again beside the one in use.
func (p *PlaceIndex) current() (*places.Index, []places.Source, error) {
	p.mu.Lock()
	defer p.mu.Unlock()
	if !p.loading && time.Since(p.checked) > time.Minute {
		p.checked = time.Now()
		if stamp, err := places.BundleStamp(p.Bundles); err == nil && stamp != p.stamp {
			p.loading = true
			go p.load()
		}
	}
	return p.ix, p.sources, p.err
}

type ownPlaces struct {
	head string
	ix   *places.Index
}

// own is the index of the garden's own places, as its beans stand at its current commit: each being whose `be …
// as: location` or `as: place` holds a coordinate in EPSG:4326 or an OpenStreetMap element. A statement held off git
// holds nothing here; reading is the reader's own garden, on this machine.
func (s *Server) own(g *Garden) *places.Index {
	head := headOf(g.Conf.Path)
	s.ownMu.Lock()
	defer s.ownMu.Unlock()
	if o, ok := s.owned[g.Conf.Name]; ok && head != "" && o.head == head {
		return o.ix
	}
	beans, _ := garden.Beans(g.Conf.Path)
	var list []places.OwnPlace
	for _, b := range beans {
		o := places.OwnPlace{Code: b.ID, Name: b.Title, Kind: b.Kind}
		found := false
		for _, st := range b.Statements {
			if st.Verb != "be" || st.Roles.Get("held") != nil {
				continue
			}
			if as, _ := st.Roles.Get("as").(string); as != "location" && as != "place" {
				continue
			}
			for _, at := range strings1(st.Roles.Get("at")) {
				if m := geoRe.FindStringSubmatch(at); m != nil && !o.HasPoint {
					o.Lat, _ = strconv.ParseFloat(m[1], 64)
					o.Lon, _ = strconv.ParseFloat(m[2], 64)
					o.HasPoint, found = true, true
				} else if m := osmRe.FindStringSubmatch(at); m != nil && o.Source == "" {
					o.Source, found = "osm:"+m[1][:1]+m[2], true
				}
			}
		}
		if found {
			if o.Name == "" {
				o.Name = b.ID
			}
			list = append(list, o)
		}
	}
	ix := places.BuildIndex(places.Own(list), "", 1)
	if s.owned == nil {
		s.owned = map[string]ownPlaces{}
	}
	s.owned[g.Conf.Name] = ownPlaces{head: head, ix: ix}
	return ix
}

// strings1 is a role's filler as strings: one, or each of a list.
func strings1(v any) []string {
	switch x := v.(type) {
	case string:
		return []string{x}
	case []any:
		var out []string
		for _, e := range x {
			if s, ok := e.(string); ok {
				out = append(out, s)
			}
		}
		return out
	}
	return nil
}

// whereabouts: the being says where people will be — a happening, a being that holds an `attend`, or one whose place
// is held off git — so nothing looked up for it leaves the machine.
func whereabouts(g *Garden, bean string) bool {
	if !slugRe.MatchString(bean) {
		return true // a name that is no bean's cannot be read: it is taken as the careful case
	}
	beans, _ := garden.Beans(g.Conf.Path)
	b, ok := beans[bean]
	if !ok {
		return false // a being not yet made says nothing yet; the page's own `sealed` speaks for it
	}
	if b.Kind == "event" {
		return true
	}
	for _, st := range b.Statements {
		if st.Verb == "attend" || (st.Verb == "be" && st.Roles.Get("held") != nil) {
			return true
		}
	}
	return false
}

func placeQuery(r *http.Request) (string, int) {
	q := []rune(strings.TrimSpace(r.URL.Query().Get("q")))
	if len(q) > placeQueryRunes {
		q = q[:placeQueryRunes]
	}
	limit := placeLimit
	if n, err := strconv.Atoi(r.URL.Query().Get("limit")); err == nil && n > 0 {
		limit = min(n, placeMaxLimit)
	}
	return string(q), limit
}

// near is the reader's own position, given only when they asked: lat,lon in EPSG:4326, or nothing.
func near(r *http.Request) (float64, float64, bool) {
	m := nearRe.FindStringSubmatch(r.URL.Query().Get("near"))
	if m == nil {
		return 0, 0, false
	}
	lat, _ := strconv.ParseFloat(m[1], 64)
	lon, _ := strconv.ParseFloat(m[2], 64)
	return lat, lon, lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180
}

// placesHere answers from this machine alone.
func (s *Server) placesHere(w http.ResponseWriter, r *http.Request, g *Garden) {
	q, limit := placeQuery(r)
	out := map[string]any{"own": []places.Answer{}, "places": []places.Answer{}, "ready": true,
		"sources": []places.Source{}, "far": g.Conf.PlaceService != nil}
	if q == "" || !utf8.ValidString(q) {
		reply(w, 200, out)
		return
	}
	ownIx := s.own(g)
	out["own"] = ownIx.Answers(ownIx.Search(q, places.Options{Limit: limit}))
	if s.Places != nil {
		ix, sources, err := s.Places.current()
		switch {
		case ix == nil && err != nil:
			out["ready"], out["why"] = false, "the place bundles could not be read" // the log says why, once
		case ix == nil:
			out["ready"] = false // still loading
		default:
			opt := places.Options{Kinds: ix.KindSet(r.URL.Query().Get("kinds")), Within: ix.Resolve(r.URL.Query().Get("within")),
				Limit: limit}
			if lat, lon, ok := near(r); ok && opt.Within == 0 {
				opt.Within = ix.Nearest(lat, lon, map[string]bool{"city": true, "village": true}, nearKm)
			}
			out["places"], out["sources"], out["generation"] = ix.Answers(ix.Search(q, opt)), sources, ix.Generation
		}
	}
	reply(w, 200, out)
}

// placeClient asks a place service beyond the machine: briefly, following no redirect (an answer from elsewhere is
// no answer of the service the law granted), through no proxy the environment names (what a person typed goes to the
// route and nowhere else), and reading at most a mebibyte.
var placeClient = &http.Client{Timeout: 5 * time.Second, Transport: &http.Transport{Proxy: nil},
	CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}

// placeWays are the routes a lookup goes by, in the order to try them: those daftard keeps the health of
// (internal/register, as its register's), else each address daftard.json names, in its order.
func placeWays(g *Garden) []register.Way {
	if g.PlaceRoutes != nil {
		return g.PlaceRoutes.Order()
	}
	out := []register.Way{}
	for i, w := range g.Conf.PlaceService.Ways() {
		if w.Via == "https" && w.URL != "" {
			out = append(out, register.Way{Route: i + 1, URL: strings.TrimRight(w.URL, "/")})
		}
	}
	return out
}

// noted tells the place service's routes what a lookup found of one, where daftard keeps them.
func noted(g *Garden, n register.Note) {
	if g.PlaceRoutes != nil {
		g.PlaceRoutes.Note([]register.Note{n})
	}
}

// placesFar sends a lookup to the garden's place service, where the law lets it go, and answers what came back.
func (s *Server) placesFar(w http.ResponseWriter, r *http.Request, g *Garden) {
	q, limit := placeQuery(r)
	none := func(why string) {
		reply(w, 200, map[string]any{"sent": false, "why": why, "places": []places.Answer{}})
	}
	svc := g.Conf.PlaceService
	switch {
	case svc == nil || (svc.URL == "" && len(svc.Routes) == 0) || svc.Party == "":
		none("no place service is named for this garden")
		return
	case r.URL.Query().Get("sealed") == "1" || (r.URL.Query().Get("for") != "" && whereabouts(g, r.URL.Query().Get("for"))):
		none("sealed: where a person will be is looked up on this machine alone")
		return
	case q == "" || !utf8.ValidString(q):
		none("nothing to look up")
		return
	}
	raw, err := g.Worker.Call("may_send", map[string]any{"party": svc.Party}, time.Minute)
	var may struct {
		Granted bool `json:"granted"`
	}
	if err != nil || json.Unmarshal(raw, &may) != nil || !may.Granted {
		none("the garden's flow law does not grant this party: nothing is sent")
		return
	}
	v := url.Values{"q": {q}, "limit": {strconv.Itoa(limit)}}
	if lang := r.URL.Query().Get("lang"); placeLangRe.MatchString(lang) {
		v.Set("lang", lang)
	}
	if lat, lon, ok := near(r); ok {
		v.Set("lat", strconv.FormatFloat(lat, 'f', -1, 64))
		v.Set("lon", strconv.FormatFloat(lon, 'f', -1, 64))
	}
	ways := placeWays(g)
	if len(ways) == 0 {
		noted(g, register.Note{None: true}) // every route asked again at once
		none("the place service is not reachable now: none of its routes answers")
		return
	}
	// BY ITS ROUTES, AS A REGISTER IS READ: the first, and a lookup that fails at the connection once more by the next.
	// A lookup is a read — Photon's /api changes nothing — so asking it again repeats nothing; it is never asked again
	// after an answer (an HTTP error is the service's own), nor a third time: a page waits two attempts at most.
	var resp *http.Response
	err = errors.New("no route")
	for i := 0; i < len(ways) && i < 2; i++ {
		base, perr := url.Parse(ways[i].URL + "/api")
		if perr != nil || (base.Scheme != "http" && base.Scheme != "https") {
			continue
		}
		base.RawQuery = v.Encode()
		if resp, err = placeClient.Get(base.String()); err == nil {
			noted(g, register.Note{Route: ways[i].Route, Answered: true})
			break
		}
		noted(g, register.Note{Route: ways[i].Route, Missed: register.Kind(err)})
	}
	if err != nil {
		none("the place service did not answer")
		return
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if resp.StatusCode != 200 {
		none(fmt.Sprintf("the place service answered %d", resp.StatusCode))
		return
	}
	found, err := photonAnswers(body)
	if err != nil {
		none("the place service's answer is no GeoJSON read here")
		return
	}
	reply(w, 200, map[string]any{"sent": true, "places": found,
		"sources": []places.Source{{Name: "OpenStreetMap", Licence: "ODbL-1.0", Attribution: "© OpenStreetMap contributors",
			URL: "https://www.openstreetmap.org/copyright"}}})
}

// photonAnswers reads Photon's GeoJSON (its API v1: each feature a point and its properties) into the answers a page
// reads, a place's own words in `label` and where it is in `detail`, from the nearest part of its address outward.
func photonAnswers(body []byte) ([]places.Answer, error) {
	var fc struct {
		Features []struct {
			Geometry struct {
				Type        string    `json:"type"`
				Coordinates []float64 `json:"coordinates"`
			} `json:"geometry"`
			Properties map[string]any `json:"properties"`
		} `json:"features"`
	}
	if err := json.Unmarshal(body, &fc); err != nil {
		return nil, err
	}
	out := []places.Answer{}
	kinds := map[string]string{"N": "node", "W": "way", "R": "relation"}
	for _, f := range fc.Features {
		p := func(k string) string { v, _ := f.Properties[k].(string); return v }
		label := p("name")
		if label == "" {
			label = strings.TrimSpace(p("street") + " " + p("housenumber"))
		}
		if label == "" {
			continue
		}
		var parts []string
		// nearest first: Photon's `locality` is a neighbourhood, inside its `district`. A post code Photon gives is not
		// passed on: a whole code names one building, and a page has no use for it here
		for _, k := range []string{"street", "locality", "district", "city", "county", "state", "country"} {
			if v := p(k); v != "" && v != label && !containsString(parts, v) {
				parts = append(parts, v)
			}
		}
		// what Photon ranked by is its own: `field` names the service, `match` the map's tag the place carries
		a := places.Answer{Label: label, Detail: strings.Join(parts, " · "), Kind: p("type"), Field: "photon",
			Match: p("osm_key") + "=" + p("osm_value")}
		if id, ok := f.Properties["osm_id"].(float64); ok && id > 0 && kinds[p("osm_type")] != "" {
			a.OSM = kinds[p("osm_type")] + "/" + strconv.FormatInt(int64(id), 10)
			a.Code = "osm:" + a.OSM
		}
		if f.Geometry.Type == "Point" && len(f.Geometry.Coordinates) == 2 {
			a.Point = &[2]float64{f.Geometry.Coordinates[1], f.Geometry.Coordinates[0]} // GeoJSON is lon, lat
		}
		out = append(out, a)
	}
	return out, nil
}

func containsString(list []string, s string) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}
