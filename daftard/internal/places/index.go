// Part of place_responder. Licensed under AGPL-3.0.
//
// The index, and the search over it.
//
// WHAT IS RANKED. Every place gets the texts place_graph's tree.suggest_texts lists -- its
// names, its English name, its code, its aliases, the names above it, its neighbours -- each
// with the weight the spec gives it. A place's score is the best weight x match value over
// those texts, exactly as search_suggest's rank() computes it, and ties keep (sequence, id).
//
// WHY IT IS FAST. Odoo's own search has to ask the database for candidates and rank a capped
// shortlist, because reading every row is dear there. Here every row is already in memory,
// so nothing is capped and nothing is shortlisted: the answer is the one rank() would give
// over EVERY place.
//   - Texts are stored once. «تهران» is a text of thirty thousand places (as the city above
//     them); it is matched once per query and the result is fanned out to all of them.
//   - A text is only matched when it can match at all: a word of it starts with a word of the
//     query (exact, phrase, words, partial), it contains the query without spaces (compact),
//     or one of its words is close in spelling (typo). Each of those has a table: a sorted
//     vocabulary for word starts, trigram postings for the other two.
package places

import (
	"math"
	"sort"
	"strings"
	"sync"
	"time"
)

type field uint8

const (
	fName field = iota
	fNameEn
	fCode
	fAlias
	fParent
	fNeighbour
)

var fieldNames = [...]string{"name", "name_en", "code", "alias", "parent", "neighbour"}

type posting struct {
	doc    int32
	pos    uint16 // the text's position in the place's list: the first of equal scores wins
	field  field
	weight uint8 // into Index.weights: a handful of distinct values, 700,000 postings
}

type Doc struct {
	place *Place
	kind  string
}

// Index is immutable once built; a reload builds a new one and swaps it in.
type Index struct {
	Lang       string
	Generation uint64
	Built      time.Time
	BuildTime  time.Duration
	Spec       Spec

	docs     []Doc
	byID     map[int64]*Place
	byCode   map[string]*Place
	texts    []*Text
	postings [][]posting // text -> places that carry it
	weights  []float64

	vocab      []string  // every word of every text, spaced and stemmed forms, sorted
	vocabTexts [][]int32 // vocab word -> texts containing it
	stemmed    []int32   // vocab ids of stemmed words (the typo candidates)
	wordGrams  map[trigram][]int32
	wordGramN  []int32             // distinct padded trigrams per vocab word
	subGrams   map[trigram][]int32 // unpadded trigrams of compact texts -> texts
	padGrams   map[trigram][]int32 // padded trigrams of compact texts -> texts
	padGramN   []int32

	postcodes map[string][]Postcode
	scratch   sync.Pool
}

type scratch struct {
	score []float64
	pos   []uint16
	field []field
	kind  []string
	seen  []uint32
	epoch uint32
	hit   []int32
}

// BuildIndex builds the index for one display language.
func BuildIndex(d *Dataset, lang string, generation uint64) *Index {
	started := time.Now()
	ix := &Index{Lang: lang, Generation: generation, Spec: d.Spec,
		byID:      make(map[int64]*Place, len(d.Places)),
		byCode:    make(map[string]*Place, len(d.Places)),
		wordGrams: map[trigram][]int32{}, subGrams: map[trigram][]int32{}, padGrams: map[trigram][]int32{},
		postcodes: map[string][]Postcode{}}
	for i := range d.Places {
		p := &d.Places[i]
		ix.byID[p.ID] = p
		ix.byCode[p.Code] = p
	}
	for i := range d.Places {
		d.Places[i].CitySequence = citySequence(&d.Places[i], ix.byID)
	}
	aliases := map[int64][]Alias{}
	for _, a := range d.Aliases {
		aliases[a.Place] = append(aliases[a.Place], a)
	}
	neighbours := map[int64][]int64{}
	for _, l := range d.Links {
		neighbours[l.Place] = append(neighbours[l.Place], l.Other)
	}
	// search_suggest reads a translated field in every installed language when there is more
	// than one, and in the current language when there is one.
	nameLangs := []string{lang}
	if len(d.Langs) > 1 {
		nameLangs = d.Langs
	}

	textID := map[string]int32{}
	addText := func(raw string) int32 {
		key := normalize(raw)
		if id, ok := textID[key]; ok {
			return id
		}
		id := int32(len(ix.texts))
		textID[key] = id
		ix.texts = append(ix.texts, newText(raw))
		ix.postings = append(ix.postings, nil)
		return id
	}
	spec := &d.Spec
	weightID := map[float64]uint8{}
	weightOf := func(w float64) uint8 {
		if id, ok := weightID[w]; ok {
			return id
		}
		id := uint8(len(ix.weights))
		weightID[w] = id
		ix.weights = append(ix.weights, w)
		return id
	}
	for i := range d.Places {
		p := &d.Places[i]
		if !p.Active {
			continue
		}
		doc := int32(len(ix.docs))
		ix.docs = append(ix.docs, Doc{place: p, kind: p.Kind})
		var pos uint16
		add := func(raw string, f field, weight float64) {
			if raw == "" {
				return
			}
			t := addText(raw)
			ix.postings[t] = append(ix.postings[t], posting{doc, pos, f, weightOf(weight)})
			pos++
		}
		seen := map[string]bool{}
		for _, l := range nameLangs {
			if n := name(p.Names, l); n != "" && !seen[n] {
				seen[n] = true
				add(n, fName, spec.nameWeight)
			}
		}
		add(p.NameEn, fNameEn, spec.nameEnWeight)
		add(p.Code, fCode, spec.codeWeight)
		own := aliases[p.ID]
		sort.SliceStable(own, func(a, b int) bool {
			if own[a].Kind != own[b].Kind {
				return own[a].Kind < own[b].Kind
			}
			return name(own[a].Names, lang) < name(own[b].Names, lang)
		})
		for _, a := range own {
			add(name(a.Names, lang), fAlias, spec.aliasWeight(a.Kind))
		}
		for _, above := range ancestors(p, ix.byID) {
			add(name(above.Names, lang), fParent, spec.ParentWeight)
		}
		for _, other := range neighbours[p.ID] {
			if n, ok := ix.byID[other]; ok {
				add(name(n.Names, lang), fNeighbour, spec.NeighbourWeight)
			}
		}
	}

	// The vocabulary: every spaced word and every stemmed word, each pointing at its texts.
	vocabID := map[string]int32{}
	isStem := map[int32]bool{}
	word := func(w string, t int32, stemmedForm bool) {
		id, ok := vocabID[w]
		if !ok {
			id = int32(len(ix.vocab))
			vocabID[w] = id
			ix.vocab = append(ix.vocab, w)
			ix.vocabTexts = append(ix.vocabTexts, nil)
		}
		list := ix.vocabTexts[id]
		if len(list) == 0 || list[len(list)-1] != t {
			ix.vocabTexts[id] = append(list, t)
		}
		if stemmedForm {
			isStem[id] = true
		}
	}
	for t, text := range ix.texts {
		for _, w := range strings.Fields(text.Spaced) {
			word(w, int32(t), false)
		}
		for _, w := range text.Words {
			word(w, int32(t), true)
		}
		if text.Compact != "" {
			runes := []rune(text.Compact)
			seen := map[trigram]bool{}
			for i := 0; i+3 <= len(runes); i++ {
				g := trigram{runes[i], runes[i+1], runes[i+2]}
				if !seen[g] {
					seen[g] = true
					ix.subGrams[g] = append(ix.subGrams[g], int32(t))
				}
			}
			grams := trigrams(text.Compact)
			for _, g := range grams {
				ix.padGrams[g] = append(ix.padGrams[g], int32(t))
			}
			ix.padGramN = append(ix.padGramN, int32(len(grams)))
		} else {
			ix.padGramN = append(ix.padGramN, 0)
		}
	}
	// Sort the vocabulary so a prefix is a range, and keep the texts beside their words.
	order := make([]int32, len(ix.vocab))
	for i := range order {
		order[i] = int32(i)
	}
	sort.Slice(order, func(a, b int) bool { return ix.vocab[order[a]] < ix.vocab[order[b]] })
	vocab := make([]string, len(order))
	vocabTexts := make([][]int32, len(order))
	for newID, oldID := range order {
		vocab[newID] = ix.vocab[oldID]
		vocabTexts[newID] = ix.vocabTexts[oldID]
		if isStem[oldID] {
			ix.stemmed = append(ix.stemmed, int32(newID))
		}
	}
	ix.vocab, ix.vocabTexts = vocab, vocabTexts
	ix.wordGramN = make([]int32, len(ix.vocab))
	for _, id := range ix.stemmed {
		grams := trigrams(ix.vocab[id])
		ix.wordGramN[id] = int32(len(grams))
		for _, g := range grams {
			ix.wordGrams[g] = append(ix.wordGrams[g], id)
		}
	}
	for _, pc := range d.Postcodes {
		ix.postcodes[pc.Prefix] = append(ix.postcodes[pc.Prefix], pc)
	}
	// Lists grown by append carry up to twice what they hold. The index lives until the next
	// reload, beside Odoo on a small machine: give the slack back.
	for i, list := range ix.postings {
		ix.postings[i] = clip(list)
	}
	for i, list := range ix.vocabTexts {
		ix.vocabTexts[i] = clip(list)
	}
	for _, m := range []map[trigram][]int32{ix.wordGrams, ix.subGrams, ix.padGrams} {
		for g, list := range m {
			m[g] = clip(list)
		}
	}
	ix.scratch.New = func() any {
		n := len(ix.docs)
		return &scratch{score: make([]float64, n), pos: make([]uint16, n), field: make([]field, n),
			kind: make([]string, n), seen: make([]uint32, n)}
	}
	ix.Built = time.Now()
	ix.BuildTime = time.Since(started)
	return ix
}

// Result is one answer.
type Result struct {
	Place *Place
	Score float64
	Field string
	Match string
	Boost float64
	Via   *Place // the finer place that matched, when the form does not offer its kind
}

// Options narrows and lifts a search.
type Options struct {
	Kinds  map[string]bool // nil: every kind
	Within int64           // a place id; its own places are lifted by the spec's within_boost
	Limit  int
}

// Search ranks every active place for `raw`, best first.
func (ix *Index) Search(raw string, opt Options) []Result {
	q := newQuery(raw)
	if q.Spaced == "" || len(ix.docs) == 0 {
		return nil
	}
	if opt.Limit <= 0 {
		opt.Limit = 8
	}
	if code := postcodeQuery(raw); code != "" {
		return ix.byPostcode(code, opt)
	}
	candidates := ix.candidates(q)
	s := ix.scratch.Get().(*scratch)
	defer ix.scratch.Put(s)
	s.epoch++
	if s.epoch == 0 { // wrapped: forget everything
		for i := range s.seen {
			s.seen[i] = 0
		}
		s.epoch = 1
	}
	s.hit = s.hit[:0]
	kinds, threshold := ix.Spec.MatchKinds, ix.Spec.TypoThreshold
	for _, t := range candidates {
		m := match(q, ix.texts[t], kinds, threshold)
		if m.Kind == "" {
			continue
		}
		for _, p := range ix.postings[t] {
			score := ix.weights[p.weight] * m.Value
			if s.seen[p.doc] != s.epoch {
				s.seen[p.doc] = s.epoch
				s.score[p.doc], s.pos[p.doc], s.field[p.doc], s.kind[p.doc] = score, p.pos, p.field, m.Kind
				s.hit = append(s.hit, p.doc)
			} else if score > s.score[p.doc] || (score == s.score[p.doc] && p.pos < s.pos[p.doc]) {
				s.score[p.doc], s.pos[p.doc], s.field[p.doc], s.kind[p.doc] = score, p.pos, p.field, m.Kind
			}
		}
	}
	// A place the form does not offer answers as the nearest place above it that the form
	// does: «کاخ» is a street in Tehran, and on a form that asks for a city it means تهران. The
	// score is the street's; the answer says which place it came through (tree.climb in
	// place_graph does the same for Odoo).
	type best struct {
		raw          float64
		field, match string
		via          *Place
	}
	found := map[*Place]*best{}
	order := make([]*Place, 0, len(s.hit))
	for _, doc := range s.hit {
		matched := ix.docs[doc].place
		target, via := matched, (*Place)(nil)
		if opt.Kinds != nil && !opt.Kinds[matched.Kind] {
			target, via = ix.climb(matched, opt.Kinds), matched
			if target == nil {
				continue
			}
		}
		b := best{s.score[doc], fieldNames[s.field[doc]], s.kind[doc], via}
		have, ok := found[target]
		switch {
		case !ok:
			found[target] = &b
			order = append(order, target)
		case b.raw > have.raw,
			b.raw == have.raw && have.via != nil && (b.via == nil || b.via.ID < have.via.ID):
			*have = b
		}
	}
	results := make([]Result, 0, len(order))
	for _, place := range order {
		b := found[place]
		factor := 1.0
		if opt.Within != 0 && ix.isWithin(place, opt.Within) {
			factor = ix.Spec.WithinBoost
		}
		results = append(results, Result{Place: place, Score: round4(b.raw * factor),
			Field: b.field, Match: b.match, Boost: factor, Via: b.via})
	}
	sortResults(results)
	if len(results) > opt.Limit {
		results = results[:opt.Limit]
	}
	return results
}

// climb is tree.climb: the nearest active place above `p` of a kind in `kinds` -- only for a
// place FINER than anything offered; a county on a city form is not an answer at all.
func (ix *Index) climb(p *Place, kinds map[string]bool) *Place {
	finest := 0
	for k := range kinds {
		finest = max(finest, finenessOf(k))
	}
	if finenessOf(p.Kind) <= finest {
		return nil
	}
	for _, a := range ancestors(p, ix.byID) {
		// never further up than a city: a province says nothing about where a street is
		if a.Active && kinds[a.Kind] && finenessOf(a.Kind) >= finenessOf("city") {
			return a
		}
	}
	return nil
}

// sortResults: best score first. Equal scores: a place that matched itself before one that
// answers through a finer place (Via), then the published order: the place's own
// sequence (its kind: a neighbourhood called «بعثت» before a street called «بعثت»), then the
// order of the city it is in (of two neighbourhoods of that name, the one in the city more
// people mean), then id.
func sortResults(results []Result) {
	sort.Slice(results, func(a, b int) bool {
		ra, rb := results[a], results[b]
		if ra.Score != rb.Score {
			return ra.Score > rb.Score
		}
		// A place CALLED this before one that only contains something called this: on the
		// city form «محلات» is the city first, then the cities with a street of that name.
		if (ra.Via == nil) != (rb.Via == nil) {
			return ra.Via == nil
		}
		if ra.Place.Sequence != rb.Place.Sequence {
			return ra.Place.Sequence < rb.Place.Sequence
		}
		if ra.Place.CitySequence != rb.Place.CitySequence {
			return ra.Place.CitySequence < rb.Place.CitySequence
		}
		return ra.Place.ID < rb.Place.ID
	})
}

func (ix *Index) isWithin(p *Place, within int64) bool {
	if p.ID == within {
		return true
	}
	for _, a := range ancestors(p, ix.byID) {
		if a.ID == within {
			return true
		}
	}
	return false
}

// candidates are the texts that can answer the query at all -- a superset of those match()
// accepts, never a subset. See the comment at the top for the three ways in.
func (ix *Index) candidates(q *Query) []int32 {
	marked := map[int32]struct{}{}
	mark := func(texts []int32) {
		for _, t := range texts {
			marked[t] = struct{}{}
		}
	}
	// 1. A word of the text starts with a word of the query (exact, phrase, words, partial).
	prefixes := append([]string{q.First}, q.Words...)
	done := map[string]bool{}
	for _, p := range prefixes {
		if p == "" || done[p] {
			continue
		}
		done[p] = true
		lo := sort.SearchStrings(ix.vocab, p)
		for i := lo; i < len(ix.vocab) && strings.HasPrefix(ix.vocab[i], p); i++ {
			mark(ix.vocabTexts[i])
		}
	}
	// 2. The query without spaces is inside the text without spaces (compact).
	if runes := []rune(q.Compact); len(runes) >= 3 {
		var lists [][]int32
		seen := map[trigram]bool{}
		for i := 0; i+3 <= len(runes); i++ {
			g := trigram{runes[i], runes[i+1], runes[i+2]}
			if !seen[g] {
				seen[g] = true
				lists = append(lists, ix.subGrams[g])
			}
		}
		mark(intersect(lists))
	}
	// 3. Close in spelling: trigram similarity of a word, or of the whole compact text.
	for i, grams := range q.grams {
		if grams == nil {
			continue
		}
		_ = i
		counts := map[int32]int32{}
		for _, g := range grams {
			for _, w := range ix.wordGrams[g] {
				counts[w]++
			}
		}
		a := float64(len(grams))
		for w, c := range counts {
			if float64(c)/(a+float64(ix.wordGramN[w])-float64(c)) >= ix.Spec.TypoThreshold {
				mark(ix.vocabTexts[w])
			}
		}
	}
	if cq := []rune(q.Compact); len(cq) >= 4 {
		counts := map[int32]int32{}
		for _, g := range q.cgrams {
			for _, t := range ix.padGrams[g] {
				counts[t]++
			}
		}
		a := float64(len(q.cgrams))
		for t, c := range counts {
			if ix.texts[t].compactRunes > 2*len(cq) {
				continue
			}
			if float64(c)/(a+float64(ix.padGramN[t])-float64(c)) >= ix.Spec.TypoThreshold {
				marked[t] = struct{}{}
			}
		}
	}
	out := make([]int32, 0, len(marked))
	for t := range marked {
		out = append(out, t)
	}
	return out
}

// intersect sorted posting lists, smallest first.
func intersect(lists [][]int32) []int32 {
	if len(lists) == 0 {
		return nil
	}
	sort.Slice(lists, func(a, b int) bool { return len(lists[a]) < len(lists[b]) })
	out := append([]int32(nil), lists[0]...)
	for _, list := range lists[1:] {
		kept := out[:0]
		i, j := 0, 0
		for i < len(out) && j < len(list) {
			switch {
			case out[i] == list[j]:
				kept = append(kept, out[i])
				i++
				j++
			case out[i] < list[j]:
				i++
			default:
				j++
			}
		}
		out = kept
		if len(out) == 0 {
			break
		}
	}
	return out
}

// ---------------------------------------------------------------------- post codes

const postcodePrefix = 5

// postcodeQuery: a query that is a post code (digits, and at least a prefix of them) gives
// its first five digits. Nothing after them is kept, looked at, or logged -- a whole code
// names one building, and it is nobody's business but theirs.
func postcodeQuery(raw string) string {
	n := normalize(raw)
	digits := make([]rune, 0, 10)
	for _, r := range n {
		switch {
		case r >= '0' && r <= '9':
			digits = append(digits, r)
		case r == ' ' || r == '-':
		default:
			return ""
		}
	}
	if len(digits) < postcodePrefix {
		return ""
	}
	return string(digits[:postcodePrefix])
}

// byPostcode answers a post code the way place_graph's place_for_code decides: what staff
// said, else what people say once enough of them agree, else the imported table.
func (ix *Index) byPostcode(prefix string, opt Options) []Result {
	rows := ix.postcodes[prefix]
	trust := func(pc Postcode) float64 {
		switch pc.Source {
		case "staff":
			return 2
		case "import":
			return 0
		case "learned":
			if pc.Hits >= 3 {
				return 1
			}
			return -1
		}
		return -2
	}
	sort.SliceStable(rows, func(a, b int) bool {
		ta, tb := trust(rows[a]), trust(rows[b])
		if ta != tb {
			return ta > tb
		}
		return rows[a].Hits > rows[b].Hits
	})
	var out []Result
	seen := map[int64]bool{}
	for _, pc := range rows {
		p, ok := ix.byID[pc.Place]
		if !ok || !p.Active || seen[p.ID] || (opt.Kinds != nil && !opt.Kinds[p.Kind]) {
			continue
		}
		seen[p.ID] = true
		out = append(out, Result{Place: p, Score: math.Max(0, 1-0.1*float64(len(out))), Field: "postcode",
			Match: "postcode:" + pc.Source, Boost: 1})
		if len(out) >= opt.Limit {
			break
		}
	}
	return out
}

// clip copies a list to exactly its length, so the spare capacity of append is released.
func clip[T any](list []T) []T {
	if cap(list) == len(list) {
		return list
	}
	out := make([]T, len(list))
	copy(out, list)
	return out
}

// citySequence is tree.city_sequence: the sequence of the city or village a place is (or is
// in), and the place's own sequence when there is none above it.
func citySequence(p *Place, byID map[int64]*Place) int {
	if p.Kind == "city" || p.Kind == "village" {
		return p.Sequence
	}
	for _, a := range ancestors(p, byID) {
		if a.Kind == "city" || a.Kind == "village" {
			return a.Sequence
		}
	}
	return p.Sequence
}
