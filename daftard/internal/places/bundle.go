// Part of place_responder. Licensed under AGPL-3.0.
//
// Where the places come from: a place bundle on disk (place_graph/tools/bundle.py), a country's
// places as CSV files beside a manifest of their checksums, sources and licences.
//
// Ported from place_responder's data.go (see doc.go). Its other source, an Odoo database read
// live, is not here: daftard reads bundles a machine holds, and nothing else.
//
// It READS. It never writes a place, a suggestion or anything else: what a person picks goes
// back to whoever owns the data, as an id or a code.
package places

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
)

type Place struct {
	ID           int64
	Code         string
	Names        names // per language; "" holds the source value
	NameEn       string
	Kind         string
	Parent       int64
	InPath       bool
	Active       bool
	Sequence     int
	CitySequence int    // of the city it is in; the first tie-break (see sortResults)
	Path         string // as the source stored it; computed for a bundle
	Lat, Lon     float64
	HasPoint     bool
	Source       string // where the bundle says the place was read from: osm:n…, osm:w…, osm:r… (OSMElement)
}

type Alias struct {
	Place int64
	Names names
	Kind  string
}

// names is a translated value: (language, text) pairs. A slice, not a map: a hundred
// thousand places with one or two languages each cost a map apiece otherwise, which was
// the largest thing the responder held.
type names []langName

type langName struct{ lang, value string }

func source(value string) names { return names{{"", value}} }

type Link struct {
	Place, Other int64
	Relation     string
}

type Postcode struct {
	Prefix string
	Place  int64
	Source string
	Hits   int
}

type Dataset struct {
	Places    []Place
	Aliases   []Alias
	Links     []Link // one row per direction, as the table holds them
	Postcodes []Postcode
	Langs     []string // installed languages; empty for a bundle
	Spec      Spec
	SpecErr   error
	Origin    string   // "bundle:<dir>[+<dir>…]"
	Stamp     string   // what changed means: a fingerprint of the source
	Sources   []Source // daftard's: whom the data is from, as each manifest says, to be credited where it is shown
}

// Source is one source a bundle's manifest names: what a page that shows its places credits.
type Source struct {
	Name        string `json:"name"`
	Licence     string `json:"licence"`
	Attribution string `json:"attribution"`
	URL         string `json:"url"`
}

// name reads a translated value the way Odoo does: the language asked for, else the source.
func name(values names, lang string) string {
	fallback, source := "", ""
	for _, v := range values {
		switch v.lang {
		case lang:
			return v.value
		case "en_US":
			fallback = v.value
		case "":
			source = v.value
		}
	}
	if fallback != "" {
		return fallback
	}
	return source
}

// ---------------------------------------------------------------------------- bundle

// LoadBundle reads a place bundle, each file checked against its manifest's checksum first. A bundle has no database
// ids, so places are numbered in file order; a caller that needs a key that survives the next bundle uses `code`, which
// every answer carries. Later directories are overlays: a row with a code already seen
// replaces it, so a site can keep its own decisions in a small bundle beside the big one.
func LoadBundle(dirs []string) (*Dataset, error) {
	d := &Dataset{Origin: "bundle:" + strings.Join(dirs, "+")}
	idOf := map[string]int64{}
	var stamps []string
	specSet := false
	for _, dir := range dirs {
		manifestRaw, err := os.ReadFile(filepath.Join(dir, "manifest.json"))
		if err != nil {
			return nil, fmt.Errorf("%s: not a bundle: %w", dir, err)
		}
		var manifest struct {
			Format string          `json:"format"`
			Spec   json.RawMessage `json:"spec"`
			Files  map[string]struct {
				Sha256 string `json:"sha256"`
			} `json:"files"`
			Sources []Source `json:"sources"`
		}
		if err := json.Unmarshal(manifestRaw, &manifest); err != nil {
			return nil, fmt.Errorf("%s/manifest.json: %w", dir, err)
		}
		for _, src := range manifest.Sources {
			if !hasSource(d.Sources, src) {
				d.Sources = append(d.Sources, src)
			}
		}
		if manifest.Format != "place-bundle/1" {
			return nil, fmt.Errorf("%s: format %q, this responder reads place-bundle/1", dir, manifest.Format)
		}
		// A file that changed since the bundle was sealed is somebody's unsealed edit, or a copy damaged on its way
		// (bundle.py's read checks it the same): it is refused, never loaded as a guess.
		for file, f := range manifest.Files {
			if err := sameSum(filepath.Join(dir, file), f.Sha256); err != nil {
				return nil, fmt.Errorf("%s: %w", dir, err)
			}
		}
		if !specSet {
			d.Spec, d.SpecErr = parseSpec(manifest.Spec)
			specSet = true
		}
		names := make([]string, 0, len(manifest.Files))
		for name := range manifest.Files {
			names = append(names, name)
		}
		sort.Strings(names)
		for _, name := range names {
			stamps = append(stamps, name+":"+manifest.Files[name].Sha256)
		}

		index := map[string]int{}
		for i, p := range d.Places {
			index[p.Code] = i
		}
		err = readCSV(filepath.Join(dir, "places.csv"), true, func(r map[string]string) error {
			// Cloned and interned: a field of a CSV record is a slice of the whole line, and
			// keeping one small field would keep every line of the file alive.
			code := strings.Clone(r["code"])
			p := Place{Code: code, Names: source(strings.Clone(r["name"])), NameEn: strings.Clone(r["name_en"]),
				Kind:   intern(r["kind"]),
				InPath: r["in_path"] != "False", Active: true, Sequence: 100, Source: strings.Clone(r["source"])}
			if r["parent"] != "" {
				parent, ok := idOf[r["parent"]]
				if !ok {
					return fmt.Errorf("places.csv: %s: parent %s is not above it", code, r["parent"])
				}
				p.Parent = parent
			}
			if lat, err := strconv.ParseFloat(r["latitude"], 64); err == nil {
				if lon, err := strconv.ParseFloat(r["longitude"], 64); err == nil {
					p.Lat, p.Lon, p.HasPoint = lat, lon, true
				}
			}
			if i, seen := index[code]; seen {
				p.ID = d.Places[i].ID
				d.Places[i] = p
				return nil
			}
			p.ID = int64(len(d.Places) + 1)
			idOf[code] = p.ID
			index[code] = len(d.Places)
			d.Places = append(d.Places, p)
			return nil
		})
		if err != nil {
			return nil, err
		}
		err = readCSV(filepath.Join(dir, "aliases.csv"), false, func(r map[string]string) error {
			id, ok := idOf[r["place"]]
			if !ok {
				return fmt.Errorf("aliases.csv: place %s is not in places.csv", r["place"])
			}
			d.Aliases = append(d.Aliases, Alias{Place: id, Names: source(strings.Clone(r["name"])), Kind: intern(r["kind"])})
			return nil
		})
		if err != nil {
			return nil, err
		}
		err = readCSV(filepath.Join(dir, "links.csv"), false, func(r map[string]string) error {
			a, okA := idOf[r["place"]]
			b, okB := idOf[r["other"]]
			if !okA || !okB {
				return fmt.Errorf("links.csv: %s-%s names a place that is not in places.csv", r["place"], r["other"])
			}
			relation := intern(r["relation"])
			d.Links = append(d.Links, Link{a, b, relation}, Link{b, a, relation})
			return nil
		})
		if err != nil {
			return nil, err
		}
		err = readCSV(filepath.Join(dir, "postcodes.csv"), false, func(r map[string]string) error {
			id, ok := idOf[r["place"]]
			if !ok {
				return fmt.Errorf("postcodes.csv: place %s is not in places.csv", r["place"])
			}
			hits, _ := strconv.Atoi(r["hits"])
			d.Postcodes = append(d.Postcodes, Postcode{strings.Clone(r["prefix"]), id, intern(r["source"]), hits})
			return nil
		})
		if err != nil {
			return nil, err
		}
	}
	if !specSet {
		d.Spec, _ = parseSpec(nil)
	}
	// A bundle stores no path; it is worked out exactly as place_graph's tree.read_path does.
	byID := make(map[int64]*Place, len(d.Places))
	for i := range d.Places {
		byID[d.Places[i].ID] = &d.Places[i]
	}
	for i := range d.Places {
		d.Places[i].Path = readPath(&d.Places[i], byID, "", d.Spec.PathSeparator)
	}
	d.Stamp = strings.Join(stamps, ",")
	return d, nil
}

// BundleStamp is what a poll compares: the checksums in every manifest, nothing more.
func BundleStamp(dirs []string) (string, error) {
	var stamps []string
	for _, dir := range dirs {
		raw, err := os.ReadFile(filepath.Join(dir, "manifest.json"))
		if err != nil {
			return "", err
		}
		var manifest struct {
			Files map[string]struct {
				Sha256 string `json:"sha256"`
			} `json:"files"`
		}
		if err := json.Unmarshal(raw, &manifest); err != nil {
			return "", err
		}
		names := make([]string, 0, len(manifest.Files))
		for name := range manifest.Files {
			names = append(names, name)
		}
		sort.Strings(names)
		for _, name := range names {
			stamps = append(stamps, name+":"+manifest.Files[name].Sha256)
		}
	}
	return strings.Join(stamps, ","), nil
}

var interned sync.Map

// intern keeps one copy of a string that repeats: a kind, a relation, a source.
func intern(s string) string {
	if v, ok := interned.Load(s); ok {
		return v.(string)
	}
	s = strings.Clone(s)
	interned.Store(s, s)
	return s
}

func readCSV(path string, required bool, row func(map[string]string) error) error {
	handle, err := os.Open(path)
	if err != nil {
		if os.IsNotExist(err) && !required {
			return nil
		}
		return err
	}
	defer handle.Close()
	reader := csv.NewReader(handle)
	reader.FieldsPerRecord = -1
	header, err := reader.Read()
	if err != nil {
		return fmt.Errorf("%s: %w", filepath.Base(path), err)
	}
	for {
		record, err := reader.Read()
		if err == io.EOF {
			return nil
		}
		if err != nil {
			return fmt.Errorf("%s: %w", filepath.Base(path), err)
		}
		values := make(map[string]string, len(header))
		for i, column := range header {
			if i < len(record) {
				values[column] = record[i]
			}
		}
		if err := row(values); err != nil {
			return err
		}
	}
}

// --------------------------------------------------------------------------- the tree

var fineness = map[string]int{"country": 0, "province": 1, "county": 2, "city": 3, "village": 3,
	"district": 4, "neighbourhood": 5, "street": 6, "other": 4}

func finenessOf(kind string) int {
	if f, ok := fineness[kind]; ok {
		return f
	}
	return 4
}

// ancestors is tree.chain: the places above, nearest first, safe against a cycle.
func ancestors(p *Place, byID map[int64]*Place) []*Place {
	var out []*Place
	seen := map[int64]bool{p.ID: true}
	for parent := p.Parent; parent != 0 && !seen[parent] && len(out) < 48; {
		above, ok := byID[parent]
		if !ok {
			break
		}
		out = append(out, above)
		seen[parent] = true
		parent = above.Parent
	}
	return out
}

// readPath is tree.read_path, for a bundle, which stores no path.
func readPath(p *Place, byID map[int64]*Place, lang, separator string) string {
	var parts []string
	if p.InPath {
		parts = append(parts, name(p.Names, lang))
	}
	fine := finenessOf(p.Kind)
	var shown []*Place
	for _, a := range ancestors(p, byID) {
		if a.InPath {
			shown = append(shown, a)
		}
	}
	groups := [][]string{{"neighbourhood", "district"}, {"city", "village"}, {"province"}}
	for g, kinds := range groups {
		if len(parts) >= 3 {
			break
		}
		for _, a := range shown {
			if contains(kinds, a.Kind) && finenessOf(a.Kind) < fine {
				n := name(a.Names, lang)
				if !contains(parts, n) {
					parts = append(parts, n)
					if g == 1 {
						goto done
					}
				}
				break
			}
		}
	}
done:
	if len(parts) > 3 {
		parts = parts[:3]
	}
	return strings.Join(parts, separator)
}

func contains(list []string, value string) bool {
	for _, item := range list {
		if item == value {
			return true
		}
	}
	return false
}

// ------------------------------------------------------------------- daftard's own, beside the port

// sameSum: the file holds what the manifest sealed, by its SHA-256.
func sameSum(path, want string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return err
	}
	if got := hex.EncodeToString(h.Sum(nil)); got != want {
		return fmt.Errorf("%s does not match its checksum in manifest.json (sha-256 %s, sealed %s): not loaded",
			filepath.Base(path), got, want)
	}
	return nil
}

// OSMElement is the OpenStreetMap element a place was read from, as the law's `osm` system writes one
// (`relation/1234567`), or "" when its source names none. It says which mapped object was meant and never which
// being: an element is split, merged and re-made, and its id establishes no identity.
func OSMElement(source string) string {
	kinds := map[byte]string{'n': "node", 'w': "way", 'r': "relation"}
	if !strings.HasPrefix(source, "osm:") || len(source) < 6 {
		return ""
	}
	kind, ok := kinds[source[4]]
	digits := source[5:]
	if !ok || digits[0] == '0' {
		return ""
	}
	for i := 0; i < len(digits); i++ {
		if digits[i] < '0' || digits[i] > '9' {
			return ""
		}
	}
	return kind + "/" + digits
}

func hasSource(list []Source, s Source) bool {
	for _, x := range list {
		if x == s {
			return true
		}
	}
	return false
}
