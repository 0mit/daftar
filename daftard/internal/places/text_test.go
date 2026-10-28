// Part of place_responder. Licensed under AGPL-3.0.
package places

import (
	"encoding/json"
	"os"
	"reflect"
	"testing"
)

type vectors struct {
	Text []struct {
		In        string   `json:"in"`
		Normalize string   `json:"normalize"`
		Spaced    string   `json:"spaced"`
		Compact   string   `json:"compact"`
		Words     []string `json:"words"`
	} `json:"text"`
	Match []struct {
		Q     string  `json:"q"`
		T     string  `json:"t"`
		Kind  *string `json:"kind"`
		Value float64 `json:"value"`
	} `json:"match"`
	Round4 []struct {
		In  float64 `json:"in"`
		Out float64 `json:"out"`
	} `json:"round4"`
	TypoThreshold float64            `json:"typo_threshold"`
	MatchKinds    map[string]float64 `json:"match_kinds"`
}

func readVectors(t *testing.T, path string) vectors {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Skipf("%s: %v", path, err)
	}
	var v vectors
	if err := json.Unmarshal(raw, &v); err != nil {
		t.Fatal(err)
	}
	return v
}

// The Go port answers what search_suggest/tools/text.py answers, string for string.
func TestTextMatchesPython(t *testing.T) {
	path := "testdata/text_vectors.json"
	if full := os.Getenv("PLACES_FULL_VECTORS"); full != "" {
		path = full // tools/make_vectors.py --all OUT.json: every name in the bundle
	}
	v := readVectors(t, path)
	bad := 0
	for _, c := range v.Text {
		got := []string{normalize(c.In), spaced(c.In), compact(c.In)}
		want := []string{c.Normalize, c.Spaced, c.Compact}
		if !reflect.DeepEqual(got, want) || !reflect.DeepEqual(wordsOf(c.In), append([]string{}, c.Words...)) {
			if bad < 10 {
				t.Errorf("%q:\n got  %q %q\n want %q %q", c.In, got, wordsOf(c.In), want, c.Words)
			}
			bad++
		}
	}
	if bad > 0 {
		t.Fatalf("%d of %d strings differ from text.py", bad, len(v.Text))
	}
	t.Logf("%d strings agree with text.py", len(v.Text))
}

func TestMatchMatchesPython(t *testing.T) {
	v := readVectors(t, "testdata/text_vectors.json")
	if !reflect.DeepEqual(v.MatchKinds, defaultMatchKinds) || v.TypoThreshold != defaultTypoThreshold {
		t.Fatalf("text.py's MATCH_KINDS/TYPO_THRESHOLD changed: %v %v", v.MatchKinds, v.TypoThreshold)
	}
	bad := 0
	for _, c := range v.Match {
		got := match(newQuery(c.Q), newText(c.T), defaultMatchKinds, defaultTypoThreshold)
		want := ""
		if c.Kind != nil {
			want = *c.Kind
		}
		if got.Kind != want || got.Value != c.Value {
			if bad < 10 {
				t.Errorf("match(%q, %q) = %s %v, text.py says %s %v", c.Q, c.T, got.Kind, got.Value, want, c.Value)
			}
			bad++
		}
	}
	if bad > 0 {
		t.Fatalf("%d of %d pairs differ", bad, len(v.Match))
	}
	for _, c := range v.Round4 {
		if got := round4(c.In); got != c.Out {
			t.Errorf("round4(%v) = %v, Python round() gives %v", c.In, got, c.Out)
		}
	}
	t.Logf("%d pairs agree with text.py", len(v.Match))
}
