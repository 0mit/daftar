package web

// A READER'S OWN WAY OF READING (the view's view_prefs.py): their language as one BCP 47 tag whose Unicode keys say their
// calendar, digits, hour cycle, first day of the week and the zone moments are shown in, and beside it how a day is
// written and a currency named. Kept HERE, in this machine's state folder (readers.json), by the garden and the person
// reading: never in the garden, never in a commit, never on the garden's custom ref (which carries a person's labels
// through the hub) — a way of reading is the reader's, on the host they read on, as the view's own host keeps it with
// their account. daftard reads nothing of the tag itself: the garden's own view checks it (the worker's prefs_check: RFC
// 5646's grammar and CLDR's own types), and builds each page with it (view_page's `prefs`).

import (
	"encoding/json"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/state"
)

type readerPrefs struct{ path string }

var prefsMu sync.Mutex // one change of the file at a time, whichever garden's

// prefs is the state folder's record of each person's way of reading, read where the state folder is now
func (s *Server) prefs() *readerPrefs {
	return &readerPrefs{path: filepath.Join(state.Dir(), "readers.json")}
}

func (p *readerPrefs) read() map[string]map[string]string {
	all := map[string]map[string]string{}
	if b, err := os.ReadFile(p.path); err == nil {
		_ = json.Unmarshal(b, &all)
	}
	return all
}

// Get is one person's preferences in one garden: {locale, date, currency}, each absent where unset.
func (p *readerPrefs) Get(garden, person string) map[string]string {
	prefsMu.Lock()
	defer prefsMu.Unlock()
	if v := p.read()[garden+"/"+person]; v != nil {
		return v
	}
	return map[string]string{}
}

// Set keeps them, the file rewritten whole, readable by this account alone, as the machine's other state.
func (p *readerPrefs) Set(garden, person string, v map[string]string) error {
	prefsMu.Lock()
	defer prefsMu.Unlock()
	all := p.read()
	if len(v) == 0 {
		delete(all, garden+"/"+person)
	} else {
		all[garden+"/"+person] = v
	}
	b, err := json.MarshalIndent(all, "", " ")
	if err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(p.path), 0o700); err != nil {
		return err
	}
	tmp := p.path + ".tmp"
	if err := os.WriteFile(tmp, b, 0o600); err != nil {
		return err
	}
	return os.Rename(tmp, p.path)
}

// ReaderPrefs is one person's preferences in one garden as this machine keeps them (readers.json): `daftard prefs`'s.
func ReaderPrefs(garden, person string) map[string]string {
	return (&readerPrefs{path: filepath.Join(state.Dir(), "readers.json")}).Get(garden, person)
}

// SetReaderPrefs keeps one person's preferences in one garden, whole: a key they do not hold is unset.
func SetReaderPrefs(garden, person string, v map[string]string) error {
	return (&readerPrefs{path: filepath.Join(state.Dir(), "readers.json")}).Set(garden, person, v)
}

// prefsGet is GET /api/prefs: the person's own preferences in this garden, and the zones the panel offers (CLDR's, as
// the garden's own view names them).
func (s *Server) prefsGet(w http.ResponseWriter, r *http.Request, g *Garden) {
	if !viewOnly(w, g) { // a legacy garden's pages are daftard's own, which have no panel
		return
	}
	out := map[string]any{"prefs": s.prefs().Get(g.Conf.Name, s.readerOf(r, g)), "zones": []any{}}
	if raw, err := g.Worker.Call("prefs_zones", nil, time.Minute); err == nil {
		var z []any
		if json.Unmarshal(raw, &z) == nil {
			out["zones"] = z
		}
	}
	reply(w, 200, out)
}

// prefsSet is POST /api/prefs: checked by the garden's own view, then kept for the person reading; a refusal says why.
// It changes nothing of the garden: no commit, no write, nothing the sync carries.
func (s *Server) prefsSet(w http.ResponseWriter, r *http.Request, g *Garden) {
	if !viewOnly(w, g) { // a legacy garden's pages are daftard's own, which have no panel
		return
	}
	req, ok := readJSON(w, r)
	if !ok {
		return
	}
	raw, err := g.Worker.Call("prefs_check", map[string]any{"prefs": req}, time.Minute)
	if err != nil {
		s.fail(w, g, "read", "", err)
		return
	}
	var ans struct {
		Prefs  map[string]string `json:"prefs"`
		Reader map[string]any    `json:"reader"`
	}
	if err := json.Unmarshal(raw, &ans); err != nil {
		s.fail(w, g, "read", "", err)
		return
	}
	if err := s.prefs().Set(g.Conf.Name, s.readerOf(r, g), ans.Prefs); err != nil {
		reply(w, 500, map[string]any{"error": T(g, "ترجیح شما نگه داشته نشد.", "Your way of reading was not kept.")})
		return
	}
	reply(w, 200, map[string]any{"ok": true, "prefs": ans.Prefs, "reader": ans.Reader})
}
