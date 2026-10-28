# The answer keys

Written by place_responder's own tools, at its commit c7cb0fd, from the Python modules the index translates, and
copied here unchanged but for four strings taken out of `text_vectors.json`, each a place name that holds a word the
leak guard refuses (bin/public.py, CONTRIBUTING.md):

- `text_vectors.json` — `tools/make_vectors.py`: what search_suggest's `text.py` answers for 2,028 strings (its
  hand-picked edge cases and a sample of the Iran bundle's names) and 5,346 query–text pairs. `text_test.go` reads it.
- `rank_reference.json` — `tools/make_rank_reference.py`: search_suggest's `rank()` over every place of the Iran
  bundle (place_ir's `data/` at that commit), 25 queries, the first ten answers of each. `index_test.go` reads it,
  given that bundle's path in `DAFTARD_PLACE_BUNDLE`.

The place names in both are OpenStreetMap's: © OpenStreetMap contributors, under the Open Database Licence 1.0
(https://www.openstreetmap.org/copyright).
