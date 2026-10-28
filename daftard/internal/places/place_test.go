// Part of daftard, in daftar: its terms are daftar's code terms (REUSE.toml).
//
// The place modules' own questions, asked of daftard's index: place_graph's tests
// (tests/test_place.py, "what a person types, and the place they meant") over the same small
// tree written as a bundle, and place_ir's (tests/test_ir_places.py, "the data, asked the
// questions a person would ask it") over the Iran bundle itself. Each is the upstream test's
// question and answer at commit c7cb0fd; a question only a database can answer (an order a
// person set with `sequence`, the quick answer Odoo shows first) is left to the upstream, and
// named at the end of this file.
package places

import (
	"crypto/sha256"
	"encoding/csv"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

type row = []string

// fixture writes a sealed place-bundle/1: its CSV files, and a manifest of their checksums.
func fixture(t *testing.T, places, aliases, links, postcodes []row) string {
	t.Helper()
	dir := t.TempDir()
	files := map[string]any{}
	write := func(name string, header row, rows []row) {
		f, err := os.Create(filepath.Join(dir, name))
		if err != nil {
			t.Fatal(err)
		}
		w := csv.NewWriter(f)
		_ = w.Write(header)
		_ = w.WriteAll(rows)
		w.Flush()
		f.Close()
		raw, _ := os.ReadFile(filepath.Join(dir, name))
		sum := sha256.Sum256(raw)
		files[name] = map[string]any{"sha256": hex.EncodeToString(sum[:]), "rows": len(rows)}
	}
	write("places.csv", row{"code", "name", "name_en", "kind", "parent", "in_path", "latitude", "longitude", "source"}, places)
	write("aliases.csv", row{"place", "name", "kind", "source"}, aliases)
	write("links.csv", row{"place", "other", "relation", "source"}, links)
	write("postcodes.csv", row{"prefix", "place", "source", "hits"}, postcodes)
	manifest, _ := json.Marshal(map[string]any{"format": "place-bundle/1", "country": "zz", "files": files})
	if err := os.WriteFile(filepath.Join(dir, "manifest.json"), manifest, 0o644); err != nil {
		t.Fatal(err)
	}
	return dir
}

// place_graph's fixture (test_place.py setUpClass), the same names, kinds and tree.
var testPlaces = []row{
	{"test-ir", "ایران", "", "country", "", "False", "", "", "test"},
	{"test-ir-te", "تهران", "", "province", "test-ir", "True", "", "", "test"},
	// A county is real and nobody picks one: it holds its cities and stays out of the path.
	{"test-ir-te-c-tehran", "شهرستان تهران", "", "county", "test-ir-te", "False", "", "", "test"},
	{"test-ir-te-tehran", "تهران", "", "city", "test-ir-te-c-tehran", "True", "35.6892", "51.3890", "osm:r8775"},
	{"test-ir-te-tehran-6", "منطقهٔ ۶", "", "district", "test-ir-te-tehran", "True", "", "", "test"},
	{"test-ir-te-tehran-6-palestine", "فلسطین", "", "neighbourhood", "test-ir-te-tehran-6", "True", "", "", "osm:w42"},
	{"test-ir-te-tehran-6-valiasr", "ولیعصر", "", "neighbourhood", "test-ir-te-tehran-6", "True", "", "", "osm:n7"},
	// The same name in another city, to make sure context decides between them.
	{"test-ir-rk-mashhad", "مشهد", "", "city", "test-ir", "True", "", "", "test"},
	{"test-ir-rk-mashhad-palestine", "فلسطین", "", "neighbourhood", "test-ir-rk-mashhad", "True", "", "", "test"},
}
var testAliases = []row{{"test-ir-te-tehran-6-palestine", "کاخ", "old", "test"}}

func testIndex(t *testing.T, extra []row, links []row, postcodes []row) *Index {
	t.Helper()
	d, err := LoadBundle([]string{fixture(t, append(append([]row{}, testPlaces...), extra...), testAliases, links, postcodes)})
	if err != nil {
		t.Fatal(err)
	}
	return BuildIndex(d, "", 1)
}

func codes(found []Result) []string {
	out := []string{}
	for _, r := range found {
		out = append(out, r.Place.Code)
	}
	return out
}

func has(list []string, code string) bool {
	for _, c := range list {
		if c == code {
			return true
		}
	}
	return false
}

func (ix *Index) place(code string) *Place { return ix.byCode[code] }

var cityForm = map[string]bool{"city": true, "village": true, "province": true}

// --------------------------------------------------------------------------------- tree

func TestALayerNobodyPicksIsKeptAndLeftOutOfThePath(t *testing.T) {
	ix := testIndex(t, nil, nil, nil)
	if got := ix.place("test-ir-te-tehran").Path; got != "تهران" { // said once, not «تهران · تهران»
		t.Errorf("Tehran's path is %q", got)
	}
	if got := ix.place("test-ir-te-tehran-6-palestine").Path; got != "فلسطین · منطقهٔ ۶ · تهران" {
		t.Errorf("Palestine's path is %q", got)
	}
	// It is still searchable: a county name leads to the city under it.
	if !has(codes(ix.Search("شهرستان تهران", Options{})), "test-ir-te-tehran") {
		t.Errorf("the county's name does not lead to the city under it: %v", codes(ix.Search("شهرستان تهران", Options{})))
	}
}

func TestAPlaceCannotBeInsideItself(t *testing.T) {
	// A bundle writes a parent above its child, so no place can be above itself: one written below is refused.
	_, err := LoadBundle([]string{fixture(t, []row{
		{"zz-a", "الف", "", "city", "zz-b", "True", "", "", "test"},
		{"zz-b", "ب", "", "district", "zz-a", "True", "", "", "test"},
	}, nil, nil, nil)})
	if err == nil || !strings.Contains(err.Error(), "is not above it") {
		t.Errorf("a parent written below its child was loaded: %v", err)
	}
}

// -------------------------------------------------------------------------------- names

func TestAnOldNameFindsThePlaceAndNeverReplacesItsName(t *testing.T) {
	ix := testIndex(t, nil, nil, nil)
	found := ix.Search("کاخ", Options{})
	if len(found) == 0 || found[0].Place.Code != "test-ir-te-tehran-6-palestine" {
		t.Fatalf("«کاخ» found %v", codes(found))
	}
	a := ix.Answers(found[:1])[0]
	if a.Label != "فلسطین" || a.Detail != "فلسطین · منطقهٔ ۶ · تهران" || strings.Contains(a.Label+a.Detail, "کاخ") {
		t.Errorf("the answer reads %q / %q", a.Label, a.Detail)
	}
	if a.Field != "alias" || a.Match != "exact" {
		t.Errorf("it says it was found by %s/%s", a.Field, a.Match)
	}
}

func TestNamingANeighbourFindsThePlace(t *testing.T) {
	ix := testIndex(t, nil, []row{{"test-ir-te-tehran-6-palestine", "test-ir-te-tehran-6-valiasr", "adjacent", "test"}}, nil)
	found := codes(ix.Search("ولیعصر", Options{}))
	if !has(found, "test-ir-te-tehran-6-palestine") {
		t.Errorf("naming the neighbour does not find the place: %v", found)
	}
	if found[0] != "test-ir-te-tehran-6-valiasr" { // and the place itself still wins for its own name
		t.Errorf("Valiasr is not first for its own name: %v", found)
	}
}

func TestAPlaceYouAreInWinsOverTheSameNameElsewhere(t *testing.T) {
	ix := testIndex(t, nil, nil, nil)
	everywhere := codes(ix.Search("فلسطین", Options{}))
	if !has(everywhere, "test-ir-te-tehran-6-palestine") || !has(everywhere, "test-ir-rk-mashhad-palestine") {
		t.Fatalf("both Palestines are not found: %v", everywhere)
	}
	inTehran := ix.Search("فلسطین", Options{Within: ix.Resolve("test-ir-te-tehran")})
	if inTehran[0].Place.Code != "test-ir-te-tehran-6-palestine" || inTehran[0].Boost <= 1 {
		t.Errorf("within Tehran: %v, boost %v", codes(inTehran), inTehran[0].Boost)
	}
	inMashhad := ix.Search("فلسطین", Options{Within: ix.Resolve("test-ir-rk-mashhad")})
	if inMashhad[0].Place.Code != "test-ir-rk-mashhad-palestine" {
		t.Errorf("within Mashhad: %v", codes(inMashhad))
	}
}

func TestAKindNarrowsTheAnswer(t *testing.T) {
	ix := testIndex(t, nil, nil, nil)
	if got := codes(ix.Search("تهران", Options{Kinds: map[string]bool{"city": true}})); len(got) != 1 || got[0] != "test-ir-te-tehran" {
		t.Errorf("«تهران» on a form that asks for a city: %v", got)
	}
}

// -------------------------------------------------------------------------------- graph

func TestANeighbourIsANeighbourFromBothSides(t *testing.T) {
	// One row in links.csv is both directions: each place is found by the other's name.
	ix := testIndex(t, nil, []row{{"test-ir-te-tehran-6-palestine", "test-ir-te-tehran-6-valiasr", "adjacent", "test"}}, nil)
	if !has(codes(ix.Search("ولیعصر", Options{})), "test-ir-te-tehran-6-palestine") ||
		!has(codes(ix.Search("فلسطین", Options{})), "test-ir-te-tehran-6-valiasr") {
		t.Errorf("a neighbour is a neighbour from one side only")
	}
}

// ---------------------------------------------------------------------------- post codes

func TestOnlyThePrefixOfAPostCodeIsEverRead(t *testing.T) {
	for in, want := range map[string]string{"1416753955": "14167", "۱۴۱۶۷-۵۳۹۵۵": "14167", "1416": ""} {
		if got := postcodeQuery(in); got != want {
			t.Errorf("postcodeQuery(%q) = %q, want %q", in, got, want)
		}
	}
}

func TestWhatPeopleConfirmBeatsAnImportedTableOnceEnoughOfThemAgree(t *testing.T) {
	first := func(pcs []row) string {
		ix := testIndex(t, nil, nil, pcs)
		found := ix.Search("1416753955", Options{})
		if len(found) == 0 {
			return ""
		}
		return found[0].Place.Code
	}
	imported := row{"14167", "test-ir-te-tehran-6-valiasr", "import", "0"}
	if got := first([]row{imported}); got != "test-ir-te-tehran-6-valiasr" {
		t.Errorf("the imported table alone: %s", got)
	}
	if got := first([]row{imported, {"14167", "test-ir-te-tehran-6-palestine", "learned", "2"}}); got != "test-ir-te-tehran-6-valiasr" {
		t.Errorf("two people are not enough to outrank the table: %s", got)
	}
	learned := row{"14167", "test-ir-te-tehran-6-palestine", "learned", "3"}
	if got := first([]row{imported, learned}); got != "test-ir-te-tehran-6-palestine" {
		t.Errorf("three people who agree outrank the table: %s", got)
	}
	// Staff outrank both.
	if got := first([]row{imported, learned, {"14167", "test-ir-te-tehran-6", "staff", "0"}}); got != "test-ir-te-tehran-6" {
		t.Errorf("staff outrank both: %s", got)
	}
}

func TestAPostCodeThatIsNotKnownAnswersNothing(t *testing.T) {
	ix := testIndex(t, nil, nil, []row{{"14167", "test-ir-te-tehran-6-valiasr", "import", "0"}})
	if found := ix.Search("9999999999", Options{}); len(found) != 0 {
		t.Errorf("an unknown post code answered %v", codes(found))
	}
}

// ------------------------------------------------------------------- a form that asks for a city

func TestAFinerMatchAnswersAsTheCityOnAFormThatAsksForOne(t *testing.T) {
	ix := testIndex(t, nil, nil, nil)
	found := ix.Search("کاخ", Options{Kinds: cityForm})
	if len(found) == 0 || found[0].Place.Code != "test-ir-te-tehran" {
		t.Fatalf("«کاخ» on a city form: %v", codes(found))
	}
	if found[0].Via == nil || found[0].Via.Code != "test-ir-te-tehran-6-palestine" {
		t.Errorf("and it says which place it came through: %v", found[0].Via)
	}
}

func TestACountyIsNotLiftedToItsProvince(t *testing.T) {
	ix := testIndex(t, nil, nil, nil)
	for _, r := range ix.Search("شهرستان تهران", Options{Kinds: cityForm}) {
		if r.Place.Code == "test-ir-te-c-tehran" || (r.Via != nil && r.Via.Code == "test-ir-te-c-tehran") {
			t.Errorf("the county answers on a city form: %s via %v", r.Place.Code, r.Via)
		}
	}
}

func TestACityCalledThisComesBeforeCitiesThatContainIt(t *testing.T) {
	ix := testIndex(t, []row{
		{"test-ir-mahallat", "محلات", "", "city", "test-ir", "True", "", "", "test"},
		{"test-ir-te-tehran-mahallat-street", "محلات", "", "street", "test-ir-te-tehran-6", "True", "", "", "test"},
	}, nil, nil)
	found := ix.Search("محلات", Options{Kinds: cityForm})
	if got := codes(found); len(got) < 2 || got[0] != "test-ir-mahallat" || got[1] != "test-ir-te-tehran" {
		t.Errorf("«محلات» on a city form: %v", got)
	}
}

// ------------------------------------------------------------------- daftard's own, beside them

func TestAnAnswerSaysWhichMappedObjectItWasReadFrom(t *testing.T) {
	ix := testIndex(t, nil, nil, nil)
	for code, want := range map[string]string{"test-ir-te-tehran": "relation/8775",
		"test-ir-te-tehran-6-palestine": "way/42", "test-ir-te-tehran-6-valiasr": "node/7", "test-ir-rk-mashhad": ""} {
		if got := ix.Answers([]Result{{Place: ix.place(code), Boost: 1}})[0].OSM; got != want {
			t.Errorf("%s: osm %q, want %q", code, got, want)
		}
	}
	for _, bad := range []string{"osm:x1", "osm:r", "osm:r0123", "osm:r12a", "osm:country-ir", "test", ""} {
		if got := OSMElement(bad); got != "" {
			t.Errorf("OSMElement(%q) = %q, want nothing", bad, got)
		}
	}
}

func TestABundleChangedSinceItWasSealedIsRefused(t *testing.T) {
	dir := fixture(t, testPlaces, testAliases, nil, nil)
	f, _ := os.OpenFile(filepath.Join(dir, "places.csv"), os.O_APPEND|os.O_WRONLY, 0)
	_, _ = f.WriteString("test-ir-new,جای تازه,,city,test-ir,True,,,test\n")
	f.Close()
	if _, err := LoadBundle([]string{dir}); err == nil || !strings.Contains(err.Error(), "does not match its checksum") {
		t.Errorf("a bundle edited after its seal was loaded: %v", err)
	}
}

// ------------------------------------------------------------------- place_ir: the data itself

func TestIranTheCountryIsThereWithItsProvinces(t *testing.T) {
	ix := shipped(t)
	count := map[string]int{}
	var tehran, county *Place
	for _, d := range ix.docs {
		count[d.place.Kind]++
		if tehran == nil && d.place.Kind == "city" && name(d.place.Names, "") == "تهران" {
			tehran = d.place
		}
		if county == nil && d.place.Kind == "county" {
			county = d.place
		}
	}
	if count["province"] != 31 {
		t.Errorf("%d provinces", count["province"])
	}
	if tehran == nil || tehran.Path != "تهران · استان تهران" {
		t.Errorf("Tehran: %+v", tehran)
	}
	// A county is loaded and stays out of what a person reads.
	if count["county"] <= 1000 || county.InPath {
		t.Errorf("%d counties; the first in the path: %v", count["county"], county.InPath)
	}
}

func cityNamed(ix *Index, n string) int64 {
	for _, d := range ix.docs {
		if d.place.Kind == "city" && name(d.place.Names, "") == n {
			return d.place.ID
		}
	}
	return 0
}

func TestIranAFormerNameFindsTheStreetItBelongsTo(t *testing.T) {
	ix := shipped(t)
	// «کاخ» is what people still call خیابان فلسطین, in Tehran.
	found := ix.Search("کاخ", Options{Within: cityNamed(ix, "تهران"), Limit: 8})
	ok := false
	for _, r := range found {
		ok = ok || strings.HasPrefix(r.Place.Path, "فلسطین")
	}
	if !ok {
		t.Errorf("«کاخ» does not reach فلسطین: %v", codes(found))
	}
}

func TestIranANeighbourhoodReadsAsItsDistrictAndCity(t *testing.T) {
	ix := shipped(t)
	for _, d := range ix.docs {
		if d.place.Kind == "neighbourhood" && name(d.place.Names, "") == "دانشگاه تهران" {
			if d.place.Path != "دانشگاه تهران · منطقه ۶ · تهران" {
				t.Errorf("its path is %q", d.place.Path)
			}
			return
		}
	}
	t.Error("no neighbourhood «دانشگاه تهران»")
}

func TestIranTheCityYouAreInDecidesBetweenPlacesOfTheSameName(t *testing.T) {
	ix := shipped(t)
	inTehran := ix.Search("فلسطین", Options{Within: cityNamed(ix, "تهران"), Limit: 8})
	inMashhad := ix.Search("فلسطین", Options{Within: cityNamed(ix, "مشهد"), Limit: 8})
	if len(inTehran) == 0 || !strings.Contains(inTehran[0].Place.Path, "تهران") {
		t.Errorf("within Tehran: %v", codes(inTehran))
	}
	if len(inMashhad) == 0 || !strings.Contains(inMashhad[0].Place.Path, "مشهد") {
		t.Errorf("within Mashhad: %v", codes(inMashhad))
	}
}

func TestIranPlacesHaveNeighbours(t *testing.T) {
	ix := shipped(t)
	links := 0
	for _, list := range ix.postings {
		for _, p := range list {
			if p.field == fNeighbour {
				links++
			}
		}
	}
	if links/2 <= 10000 { // each pair is a neighbour text on both of its places
		t.Errorf("%d neighbour texts", links)
	}
}

// Left to the upstream, which only a database answers: test_place.py's "equal scores fall to the order of the city"
// and "a neighbourhood comes before a street of the same name whatever the city" (a bundle carries no `sequence`:
// every place is 100, so its order is the file's), "the quick answer is part of the full one" (Odoo's narrowing
// before its ranking; here nothing is narrowed), "a place is not its own neighbour" (bundle.py's `check` refuses
// it when a bundle is sealed), and test_bundle.py's loading into Odoo.
