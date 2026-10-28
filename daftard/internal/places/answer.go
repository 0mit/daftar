// Part of place_responder. Licensed under AGPL-3.0.
//
// What an answer says, and how a request names kinds and a place it is within: ported from
// place_responder's server.go (its kindSet, resolve and the answer /places/suggest writes), so a
// page reads daftard's answer as it reads the responder's. The extra keys say WHY each place was
// found: the ranking is published, and a caller is entitled to check it. daftard's own keys are
// marked.
package places

import (
	"strconv"
	"strings"
)

// Answer is one place found, as the page reads it.
type Answer struct {
	ID     int64       `json:"id"`
	Code   string      `json:"code"`
	Label  string      `json:"label"`
	Detail string      `json:"detail"`
	Kind   string      `json:"kind"`
	Score  float64     `json:"score"`
	Field  string      `json:"field"`
	Match  string      `json:"match"`
	Boost  float64     `json:"boost,omitempty"`
	Via    string      `json:"via,omitempty"` // the name of the finer place that matched
	Point  *[2]float64 `json:"point,omitempty"`
	OSM    string      `json:"osm,omitempty"` // daftard's: the OpenStreetMap element it was read from (OSMElement)
}

// Answers turns what Search found into what a page reads, labelled in the index's language.
func (ix *Index) Answers(found []Result) []Answer {
	out := []Answer{}
	for _, f := range found {
		p := f.Place
		a := Answer{ID: p.ID, Code: p.Code, Label: name(p.Names, ix.Lang), Detail: p.Path, Kind: p.Kind,
			Score: f.Score, Field: f.Field, Match: f.Match, OSM: OSMElement(p.Source)}
		if f.Boost != 1 {
			a.Boost = f.Boost
		}
		if f.Via != nil {
			a.Via = name(f.Via.Names, ix.Lang)
		}
		if p.HasPoint {
			a.Point = &[2]float64{p.Lat, p.Lon}
		}
		out = append(out, a)
	}
	return out
}

// KindSet: a named set from the spec, a comma list of kinds, or nil for the spec's default.
func (ix *Index) KindSet(value string) map[string]bool {
	if value == "" {
		value = ix.Spec.PickerDefault
	}
	list, named := ix.Spec.PickerKinds[value]
	if !named {
		list = strings.Split(value, ",")
	}
	set := map[string]bool{}
	for _, kind := range list {
		if kind = strings.TrimSpace(kind); kind != "" {
			set[kind] = true
		}
	}
	if len(set) == 0 {
		return nil
	}
	return set
}

// Resolve a place given by id or by code; 0 when it is neither.
func (ix *Index) Resolve(value string) int64 {
	if value == "" {
		return 0
	}
	if id, err := strconv.ParseInt(value, 10, 64); err == nil {
		if _, ok := ix.byID[id]; ok {
			return id
		}
		return 0
	}
	if p, ok := ix.byCode[value]; ok {
		return p.ID
	}
	return 0
}
