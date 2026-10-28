package web

// THE BOARD (`/board?g=<garden>`): one being or several, the cursor, kept still while the aspect around it turns — the
// view profile's archetype `cursor`. The page is daftard's (web/board/, three.js 0.186.1 beneath its HTML, vendored in
// web/vendor/ with its licence); what it shows is read by the garden's own release (assets/view/lib/view_board.py),
// asked through the worker's methods board_aspects, board_lens, board_being and board_find. The aspects are the law's
// rows of the profiles the garden takes, and the beings are the garden's beans and the stores its host keeps: nothing
// of a machine is named here. The page only reads; there is no write behind it.
//
// Its answers are not held (held.go): a store changes without the garden's version moving, so each question is asked
// of the worker, which keeps the law and the beans read once a version and reads the stores in a snapshot each time.

import (
	"net/http"
	"regexp"
	"strings"
)

// boardID is the shape of a being's id the board asks about: a bean's, a store's (`d-…`, `c-…`, a volume's), or a
// store's pointer `store:<kind>:<id>`. The worker holds every id to the same before it reads.
var boardID = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9:._#-]{0,200}$`)

// boardCursor reads a cursor as the page sends it: ids joined by commas, at most eight.
func boardCursor(v string) ([]string, bool) {
	out := []string{}
	for _, id := range strings.Split(v, ",") {
		if id = strings.TrimSpace(id); id == "" {
			continue
		}
		if !boardID.MatchString(id) || len(out) == 8 {
			return nil, false
		}
		out = append(out, id)
	}
	return out, true
}

func (s *Server) board(w http.ResponseWriter, r *http.Request, g *Garden) {
	q := r.URL.Query()
	bad := func() {
		reply(w, 400, map[string]any{"error": T(g, "این نشانی در این دفتر نیست.", "This address is not in this garden.")})
	}
	switch r.URL.Path {
	case "/api/board/aspects":
		s.pass(w, g, "board_aspects", nil)
	case "/api/board/lens":
		ids, ok := boardCursor(q.Get("cursor"))
		if !ok {
			bad()
			return
		}
		s.pass(w, g, "board_lens", map[string]any{"aspect": q.Get("aspect"), "cursor": ids})
	case "/api/board/being":
		if !boardID.MatchString(q.Get("id")) {
			bad()
			return
		}
		s.pass(w, g, "board_being", map[string]any{"id": q.Get("id"), "reader": s.readerOf(r, g)})
	case "/api/board/find":
		ids, ok := boardCursor(q.Get("cursor"))
		if !ok || len(ids) == 0 {
			bad()
			return
		}
		s.pass(w, g, "board_find", map[string]any{"q": q.Get("q"), "cursor": ids})
	}
}
