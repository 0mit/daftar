// Part of place_responder. Licensed under AGPL-3.0.
//
// The text rules of search_suggest (addons/search_suggest/tools/text.py), line for line.
//
// This file is a TRANSLATION, not a second design: the Python module is the published
// ranking, and every function here has to answer exactly what its namesake answers. That
// is checked, not hoped: testdata/text_vectors.json is written by tools/make_vectors.py
// from the Python module itself, over every name in the country's data, and
// text_test.go fails on the first disagreement. Change text.py, regenerate, and this
// file follows -- never the other way round.
package places

import (
	"strconv"
	"strings"
	"unicode"

	"golang.org/x/text/unicode/norm"
)

const zwnj = '\u200c'

// FOLD in text.py: Arabic letters into their Persian forms, other digits into Latin ones,
// tatweel and direction marks dropped (mapped to -1).
var fold = map[rune]rune{
	'ي': 'ی', 'ى': 'ی', 'ئ': 'ی', 'ك': 'ک', 'ة': 'ه', 'ۀ': 'ه', 'ە': 'ه',
	'أ': 'ا', 'إ': 'ا', 'ٱ': 'ا', 'آ': 'ا', 'ؤ': 'و',
	'۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4', '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
	'٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4', '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
	'ـ': -1, '\u200d': -1, '\u200e': -1, '\u200f': -1,
}

// MATCH_KINDS and TYPO_THRESHOLD in text.py. The responder reads the values Odoo
// publishes (see spec.go) and falls back to these only when nothing was published.
var defaultMatchKinds = map[string]float64{
	"exact": 1.0, "phrase": 0.85, "words": 0.75, "compact": 0.6, "partial": 0.45, "typo": 0.35,
}

const defaultTypoThreshold = 0.45

// isMark is text.py's MARKS: [ً-ٰٟۖ-ۭ].
func isMark(r rune) bool {
	return (r >= 0x064b && r <= 0x065f) || r == 0x0670 || (r >= 0x06d6 && r <= 0x06ed)
}

// isWord is Python's \w for str patterns: a letter, a number or the underscore. ZWNJ is
// added by NOT_WORD itself.
func isWord(r rune) bool {
	return r == '_' || r == zwnj || unicode.IsLetter(r) || unicode.IsNumber(r)
}

// normalize is text.normalize: lower-cased, folded text with single spaces, ZWNJ kept as a
// word joiner.
func normalize(text string) string {
	if text == "" {
		return ""
	}
	var b strings.Builder
	for _, r := range norm.NFKC.String(text) {
		if to, ok := fold[r]; ok {
			if to < 0 {
				continue
			}
			r = to
		}
		if isMark(r) {
			continue
		}
		b.WriteRune(r)
	}
	// NFKD, then drop the non-spacing marks outside the Arabic block (Latin accents).
	decomposed := norm.NFKD.String(b.String())
	b.Reset()
	for _, r := range decomposed {
		if unicode.Is(unicode.Mn, r) && !(r >= 0x0600 && r <= 0x06ff) {
			continue
		}
		b.WriteRune(r)
	}
	lowered := pyLower(b.String())
	// NOT_WORD.sub(' ', ...), then '_' -> ' ', then split and strip ZWNJ from each part.
	b.Reset()
	for _, r := range lowered {
		if !isWord(r) || r == '_' {
			b.WriteByte(' ')
		} else {
			b.WriteRune(r)
		}
	}
	parts := strings.Fields(b.String())
	out := parts[:0]
	for _, part := range parts {
		if trimmed := strings.Trim(part, string(zwnj)); trimmed != "" {
			out = append(out, trimmed)
		}
	}
	return strings.Join(out, " ")
}

// pyLower is str.lower(). Go's ToLower agrees with Python on everything the country's
// names contain except the one special case Python expands: İ becomes i + a combining dot.
func pyLower(s string) string {
	if !strings.ContainsRune(s, 'İ') {
		return strings.ToLower(s)
	}
	return strings.ToLower(strings.ReplaceAll(s, "İ", "i̇"))
}

// spaced is text.spaced: ZWNJ read as a space.
func spaced(text string) string {
	return strings.Join(strings.Fields(strings.ReplaceAll(normalize(text), string(zwnj), " ")), " ")
}

// compact is text.compact: spaces and ZWNJ removed.
func compact(text string) string {
	n := normalize(text)
	n = strings.ReplaceAll(n, string(zwnj), "")
	return strings.ReplaceAll(n, " ", "")
}

// stem is text.stem: a light plural fold, Persian «ها/های» and English -s.
func stem(word string) string {
	for _, suffix := range []string{"های", "ها"} {
		if strings.HasSuffix(word, suffix) && runeLen(word)-runeLen(suffix) >= 3 {
			return strings.TrimSuffix(word, suffix)
		}
	}
	if isASCII(word) && strings.HasSuffix(word, "s") && len(word) > 4 {
		return word[:len(word)-1]
	}
	return word
}

// wordsOf is text.words.
func wordsOf(text string) []string {
	parts := strings.Fields(spaced(text))
	for i, part := range parts {
		parts[i] = stem(part)
	}
	return parts
}

func runeLen(s string) int { return len([]rune(s)) }

func isASCII(s string) bool {
	for i := 0; i < len(s); i++ {
		if s[i] >= 0x80 {
			return false
		}
	}
	return true
}

// trigram is three code points.
type trigram [3]rune

// trigrams is text.trigrams: '  word ' cut into every run of three.
func trigrams(word string) []trigram {
	padded := append([]rune("  "+word), ' ')
	seen := make(map[trigram]struct{}, len(padded))
	out := make([]trigram, 0, len(padded))
	for i := 0; i+3 <= len(padded); i++ {
		t := trigram{padded[i], padded[i+1], padded[i+2]}
		if _, ok := seen[t]; !ok {
			seen[t] = struct{}{}
			out = append(out, t)
		}
	}
	return out
}

// similarity is text.similarity: the Jaccard similarity of two trigram sets.
func similarity(a, b string) float64 {
	if a == "" || b == "" {
		return 0
	}
	return jaccard(trigrams(a), trigrams(b))
}

func jaccard(ta, tb []trigram) float64 {
	if len(ta) == 0 || len(tb) == 0 {
		return 0
	}
	set := make(map[trigram]struct{}, len(ta))
	for _, t := range ta {
		set[t] = struct{}{}
	}
	common := 0
	for _, t := range tb {
		if _, ok := set[t]; ok {
			common++
		}
	}
	return float64(common) / float64(len(ta)+len(tb)-common)
}

// Query is what text.match works out about the query on every call, worked out once.
type Query struct {
	Raw     string
	Spaced  string
	Words   []string // stemmed
	Compact string
	First   string // the first spaced word, unstemmed: what a phrase match starts with
	grams   [][]trigram
	cgrams  []trigram
}

func newQuery(raw string) *Query {
	q := &Query{Raw: raw, Spaced: spaced(raw), Words: wordsOf(raw), Compact: compact(raw)}
	if fields := strings.Fields(q.Spaced); len(fields) > 0 {
		q.First = fields[0]
	}
	q.grams = make([][]trigram, len(q.Words))
	for i, w := range q.Words {
		if runeLen(w) >= 3 {
			q.grams[i] = trigrams(w)
		}
	}
	if q.Compact != "" {
		q.cgrams = trigrams(q.Compact)
	}
	return q
}

// Text is what text.match works out about a text, worked out once when the index is built.
type Text struct {
	Spaced       string
	Words        []string // stemmed
	Compact      string
	compactRunes int
}

func newText(raw string) *Text {
	n := normalize(raw)
	t := &Text{Spaced: strings.Join(strings.Fields(strings.ReplaceAll(n, string(zwnj), " ")), " ")}
	// The words are slices of Spaced (stem only ever cuts a suffix off), and Compact IS
	// Spaced when there was nothing to remove: two hundred thousand texts, stored once.
	t.Words = strings.Fields(t.Spaced)
	for i, w := range t.Words {
		t.Words[i] = stem(w)
	}
	if c := strings.ReplaceAll(strings.ReplaceAll(n, string(zwnj), ""), " ", ""); c == t.Spaced {
		t.Compact = t.Spaced
	} else {
		t.Compact = c
	}
	t.compactRunes = runeLen(t.Compact)
	return t
}

// Match is one answer of text.match.
type Match struct {
	Kind  string
	Value float64
}

// match is text.match: the best way `t` answers `q`, or an empty Kind.
func match(q *Query, t *Text, kinds map[string]float64, typoThreshold float64) Match {
	if q.Spaced == "" || t.Spaced == "" {
		return Match{}
	}
	if q.Spaced == t.Spaced {
		return Match{"exact", kinds["exact"]}
	}
	if strings.Contains(" "+t.Spaced, " "+q.Spaced) {
		return Match{"phrase", kinds["phrase"]}
	}
	starts, all, anyStart := 0, true, false
	for _, qw := range q.Words {
		found := false
		for _, tw := range t.Words {
			if strings.HasPrefix(tw, qw) {
				found = true
				break
			}
		}
		if found {
			starts++
			anyStart = true
		} else {
			all = false
		}
	}
	if len(q.Words) > 0 && all {
		return Match{"words", kinds["words"]}
	}
	if runeLen(q.Compact) >= 3 && strings.Contains(t.Compact, q.Compact) {
		return Match{"compact", kinds["compact"]}
	}
	if anyStart && len(q.Words) > 1 {
		return Match{"partial", kinds["partial"] * float64(starts) / float64(len(q.Words))}
	}
	// The typo pass is the only one that needs trigrams of the text. It is reached by few
	// texts per query, so they are worked out here rather than kept for every text forever.
	best := 0.0
	for i := range q.Words {
		if q.grams[i] == nil {
			continue
		}
		for _, tw := range t.Words {
			if s := jaccard(q.grams[i], trigrams(tw)); s > best {
				best = s
			}
		}
	}
	cq := runeLen(q.Compact)
	if cq >= 4 && t.compactRunes <= 2*cq && t.Compact != "" {
		if s := jaccard(q.cgrams, trigrams(t.Compact)); s > best {
			best = s
		}
	}
	if best >= typoThreshold {
		return Match{"typo", kinds["typo"] * best}
	}
	return Match{}
}

// round4 is Python's round(x, 4): correctly rounded from the exact binary value, which is
// what FormatFloat does too.
func round4(x float64) float64 {
	v, _ := strconv.ParseFloat(strconv.FormatFloat(x, 'f', 4, 64), 64)
	return v
}
