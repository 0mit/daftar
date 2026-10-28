// Package places is place search: a country's places held in memory and ranked while a person is still typing
// (design §12, P8.0 and P8.3). It is place_responder's index, ported whole — a published place search under the
// AGPL-3.0, at its commit c7cb0fd — so daftard ranks exactly as that responder and the Python modules it translates
// (search_suggest's text rules, place_graph's tree) publish: the same folding of Persian text, the same six match
// kinds, the same weights, over every place rather than a shortlist. The ranking is readable: each answer says by
// which text (`field`) and which kind of match (`match`) it was found, and by how much a place it is within lifted it.
//
// THE PORT. text.go, index.go and spec.go are the responder's files as they stand there, the package renamed,
// BuildIndex exported, and text.go's four invisible characters (a joiner, a non-joiner and the two direction marks its
// fold drops) written as escapes rather than as themselves, so no reader of the source is shown one thing for another; bundle.go is its data.go without the live Odoo source (daftard reads only bundles a machine
// holds), LoadBundle and BundleStamp exported; answer.go is what its server.go wrote — kindSet and resolve, exported,
// and the answer of /places/suggest. The tests are its own, given the bundle by path. What daftard adds is marked
// where it stands: a bundle's files are checked against their manifest's checksums before anything is loaded (as
// place_graph's own bundle.py reads one), and each place keeps the `source` its bundle names, so an answer says which
// OpenStreetMap element it was read from (OSMElement) — a corroboration of which mapped object was meant, never an
// identity.
//
// HOW IT STAYS EXACT. The responder's own tests come with it, and pass here unchanged: text_test.go against
// testdata/text_vectors.json, which the Python module wrote (and, given PLACES_FULL_VECTORS, every name of a bundle:
// 152,515 for Iran, all agreeing), and index_test.go's ranking of every place against testdata/rank_reference.json,
// the Python ranking's answer key — given the Iran bundle the reference was written from (DAFTARD_PLACE_BUNDLE:
// place_ir's data/ at that commit). place_test.go asks the place modules' own questions of this index.
//
// UNICODE. The folding is NFKC, then NFKD with the marks outside the Arabic block dropped: Go's standard library has
// neither, so golang.org/x/text/unicode/norm is vendored (vendor/, BSD-3-Clause, v0.42.0) — the one package daftard
// takes from outside the standard library (README, Build).
//
// The data it is usually run with is © OpenStreetMap contributors, under the Open Database Licence 1.0: a page that
// shows these places says so.
package places
