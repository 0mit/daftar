// Part of place_responder. Licensed under AGPL-3.0.
//
// The ranking spec: every number the ranking uses, as the data source publishes it.
//
// A responder that carried its own weights would be a second ranking that can drift from
// the first. So it carries none it trusts: Odoo writes place_graph's tree.spec() into
// ir_config_parameter `place_graph.responder_spec`, and a bundle carries the same object in
// its manifest. The defaults below are that object as of this writing, used only when a
// source publishes nothing -- and the responder says so in /healthz.
package places

import "encoding/json"

type Spec struct {
	Format             string              `json:"format"`
	OwnFields          [][2]any            `json:"own_fields"`
	AliasWeight        map[string]float64  `json:"alias_weight"`
	AliasWeightDefault float64             `json:"alias_weight_default"`
	ParentWeight       float64             `json:"parent_weight"`
	NeighbourWeight    float64             `json:"neighbour_weight"`
	WithinBoost        float64             `json:"within_boost"`
	MatchKinds         map[string]float64  `json:"match_kinds"`
	TypoThreshold      float64             `json:"typo_threshold"`
	PickerKinds        map[string][]string `json:"picker_kinds"`
	PickerDefault      string              `json:"picker_default"`
	PathSeparator      string              `json:"path_separator"`

	nameWeight, nameEnWeight, codeWeight float64
	fromSource                           bool
}

func defaultSpec() Spec {
	return Spec{
		Format:             "place-responder-spec/1",
		OwnFields:          [][2]any{{"name", 1.0}, {"name_en", 0.8}, {"code", 0.4}},
		AliasWeight:        map[string]float64{"old": 0.9, "colloquial": 0.9, "spelling": 0.9, "square": 0.6, "transit": 0.6, "landmark": 0.6},
		AliasWeightDefault: 0.6,
		ParentWeight:       0.35,
		NeighbourWeight:    0.25,
		WithinBoost:        1.35,
		MatchKinds:         copyKinds(defaultMatchKinds),
		TypoThreshold:      defaultTypoThreshold,
		PickerKinds: map[string][]string{
			"city": {"city", "village", "province"},
			"area": {"neighbourhood", "district", "city", "village"},
			"all":  {"street", "neighbourhood", "district", "city", "village", "province"},
		},
		PickerDefault: "all",
		PathSeparator: " · ",
	}
}

// parseSpec reads a published spec over the defaults, so a field a newer publisher adds is
// ignored and a field an older one lacks keeps its default.
func parseSpec(raw []byte) (Spec, error) {
	spec := defaultSpec()
	if len(raw) == 0 {
		spec.settle()
		return spec, nil
	}
	if err := json.Unmarshal(raw, &spec); err != nil {
		d := defaultSpec()
		d.settle()
		return d, err
	}
	spec.fromSource = true
	spec.settle()
	return spec, nil
}

func (s *Spec) settle() {
	s.nameWeight, s.nameEnWeight, s.codeWeight = 1.0, 0.8, 0.4
	for _, pair := range s.OwnFields {
		name, _ := pair[0].(string)
		weight, ok := pair[1].(float64)
		if !ok {
			continue
		}
		switch name {
		case "name":
			s.nameWeight = weight
		case "name_en":
			s.nameEnWeight = weight
		case "code":
			s.codeWeight = weight
		}
	}
	if s.WithinBoost == 0 {
		s.WithinBoost = 1 + s.ParentWeight
	}
	for kind, value := range defaultMatchKinds {
		if _, ok := s.MatchKinds[kind]; !ok {
			s.MatchKinds[kind] = value
		}
	}
}

func (s *Spec) aliasWeight(kind string) float64 {
	if w, ok := s.AliasWeight[kind]; ok {
		return w
	}
	return s.AliasWeightDefault
}

// copyKinds gives every Spec its own map: json.Unmarshal writes INTO an existing map, and
// must never write into the defaults.
func copyKinds(in map[string]float64) map[string]float64 {
	out := make(map[string]float64, len(in))
	for k, v := range in {
		out[k] = v
	}
	return out
}
