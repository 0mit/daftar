// Part of daftard, in daftar: its terms are daftar's code terms (REUSE.toml).
//
// daftard's own, beside the port: a garden's own places searched by the same rules, and the place nearest a position.
package places

import "math"

// OwnPlace is one being of a garden that says where it is: its bean (Code), its title (Name), its kind, and what its
// `be` holds — a coordinate in EPSG:4326, an OpenStreetMap element (Source, `osm:r…`).
type OwnPlace struct {
	Code, Name, Kind, Source string
	Lat, Lon                 float64
	HasPoint                 bool
}

// Own is a dataset of a garden's own places, searched as a bundle's are — by its title as a name and its bean as a
// code, under the published spec's weights — so the garden's own places answer by the same rules as the country's.
func Own(list []OwnPlace) *Dataset {
	d := &Dataset{Origin: "garden"}
	d.Spec, _ = parseSpec(nil)
	for i, o := range list {
		d.Places = append(d.Places, Place{ID: int64(i + 1), Code: o.Code, Names: source(o.Name), Kind: o.Kind,
			InPath: true, Active: true, Sequence: 100, Lat: o.Lat, Lon: o.Lon, HasPoint: o.HasPoint, Source: o.Source})
	}
	return d
}

// Nearest is the place of one of `kinds` whose point is nearest (lat, lon), within `km`; 0 when none is. A reader's
// own position, given only when they ask, lifts what is inside that place (Options.Within) and is kept nowhere.
func (ix *Index) Nearest(lat, lon float64, kinds map[string]bool, km float64) int64 {
	best, id := km, int64(0)
	for _, d := range ix.docs {
		p := d.place
		if !p.HasPoint || !kinds[p.Kind] {
			continue
		}
		if dist := haversine(lat, lon, p.Lat, p.Lon); dist <= best {
			best, id = dist, p.ID
		}
	}
	return id
}

// haversine is the distance in kilometres on a sphere of the Earth's mean radius (IUGG, 6371.0088 km): a place's
// nearness, where a few hundred metres either way changes nothing.
func haversine(lat1, lon1, lat2, lon2 float64) float64 {
	const r = 6371.0088
	rad := math.Pi / 180
	dlat, dlon := (lat2-lat1)*rad, (lon2-lon1)*rad
	a := math.Sin(dlat/2)*math.Sin(dlat/2) + math.Cos(lat1*rad)*math.Cos(lat2*rad)*math.Sin(dlon/2)*math.Sin(dlon/2)
	return 2 * r * math.Asin(math.Min(1, math.Sqrt(a)))
}
