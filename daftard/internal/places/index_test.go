// Part of place_responder. Licensed under AGPL-3.0.
package places

import (
	"encoding/json"
	"errors"
	"os"
	"sync"
	"testing"
	"time"
)

// shippedBundle is the bundle the ranking reference was written from: place_ir's data/ at the
// commit the reference names (in daftard, a path given in DAFTARD_PLACE_BUNDLE; none given, the
// tests that need it say so and skip — a bundle is a country's data, fetched, never kept here).
var shippedBundle = os.Getenv("DAFTARD_PLACE_BUNDLE")

var errNoBundle = errors.New("no bundle: DAFTARD_PLACE_BUNDLE names none (the Iran bundle, place_ir's data/, at commit c7cb0fd)")

var (
	bundleOnce  sync.Once
	bundleIndex *Index
	bundleErr   error
)

func shipped(t testing.TB) *Index {
	t.Helper()
	bundleOnce.Do(func() {
		if shippedBundle == "" {
			bundleErr = errNoBundle
			return
		}
		d, err := LoadBundle([]string{shippedBundle})
		if err != nil {
			bundleErr = err
			return
		}
		bundleIndex = BuildIndex(d, "", 1)
	})
	if bundleErr != nil {
		t.Skipf("no bundle: %v", bundleErr)
	}
	return bundleIndex
}

// The responder ranks exactly as search_suggest's rank() does over EVERY place: same places,
// same order, same scores, fields and match kinds (testdata/rank_reference.json, written by
// tools/make_rank_reference.py from the Python modules).
func TestRankingMatchesPython(t *testing.T) {
	ix := shipped(t)
	raw, err := os.ReadFile("testdata/rank_reference.json")
	if err != nil {
		t.Skip(err)
	}
	var cases []struct {
		Q       string `json:"q"`
		Within  string `json:"within"`
		Kinds   string `json:"kinds"`
		Results []struct {
			Code  string  `json:"code"`
			Score float64 `json:"score"`
			Field string  `json:"field"`
			Match string  `json:"match"`
			Via   *string `json:"via"`
		} `json:"results"`
	}
	if err := json.Unmarshal(raw, &cases); err != nil {
		t.Fatal(err)
	}
	for _, c := range cases {
		started := time.Now()
		got := ix.Search(c.Q, Options{Kinds: ix.KindSet(c.Kinds), Within: ix.Resolve(c.Within), Limit: 10})
		took := time.Since(started)
		if len(got) != len(c.Results) {
			t.Errorf("%q: %d results, Python has %d", c.Q, len(got), len(c.Results))
		}
		for i := 0; i < len(got) && i < len(c.Results); i++ {
			g, w := got[i], c.Results[i]
			via := ""
			if g.Via != nil {
				via = g.Via.Code
			}
			wantVia := ""
			if w.Via != nil {
				wantVia = *w.Via
			}
			if g.Place.Code != w.Code || g.Score != w.Score || g.Field != w.Field || g.Match != w.Match || via != wantVia {
				t.Errorf("%q #%d: got %s %v %s/%s, Python %s %v %s/%s", c.Q, i+1,
					g.Place.Code, g.Score, g.Field, g.Match, w.Code, w.Score, w.Field, w.Match)
			}
		}
		t.Logf("%-16s %8s  %d results", c.Q, took.Round(time.Microsecond), len(got))
	}
}

func TestPostcodeIsCutToItsPrefix(t *testing.T) {
	for in, want := range map[string]string{
		"1416753955": "14167", "۱۴۱۶۷-۵۳۹۵۵": "14167", "14167": "14167", "1416": "", "تهران 14167": "",
	} {
		if got := postcodeQuery(in); got != want {
			t.Errorf("postcodeQuery(%q) = %q, want %q", in, got, want)
		}
	}
}

func BenchmarkSearch(b *testing.B) {
	ix := shipped(b)
	queries := []string{"ته", "تهران", "کاخ", "فلسطین", "اندیشه شهریار", "منطقه ۶", "تهرن", "ولیعصر", "ای", "باغ"}
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		ix.Search(queries[i%len(queries)], Options{Limit: 8})
	}
}
