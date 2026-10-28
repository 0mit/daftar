package web

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

// THE GARDEN'S ANSWERS, HELD (2026-10-14): what a page reads of its garden is asked of the garden's worker once per
// version of the garden and kept here, in daftard's memory; the same question at the same version is answered from
// memory, in well under a millisecond, and never reaches the worker. A write is still made on disk and committed at
// once, as before: the version moves, and the answers asked lately are asked again in the background, so the page a
// person comes back to is ready. Only questions that read are held (heldMethods); a write is never held, and a
// question whose answer was being read while the version moved is not kept.
//
// The version is what an answer depends on and can be seen without asking the worker: the commit and the reader's
// own labels (stamp), each document's stat (beans/, mappings/, GARDEN.md) and git's index — so an edit not yet
// committed counts — and the day, since what is due is read against it.

var heldMethods = map[string]bool{
	"view_page": true, "view_pages": true, "hello": true, "view_html": true, "view_style": true,
	"payload": true, "calendar": true, "books": true, "history": true,
}

const (
	heldMax    = 512              // answers kept per garden: the oldest asked go first
	heldRecent = 30 * time.Minute // a question asked within this long is asked again after a change
	heldWarm   = 32               // and at most this many of them, the latest first
)

type heldAnswer struct {
	raw     json.RawMessage
	asked   time.Time
	derived map[string]any // what a handler made of it (derived)
}

type heldQuestion struct {
	method string
	params map[string]any
	asked  time.Time
}

type flight struct {
	done chan struct{}
	raw  json.RawMessage
	err  error
}

type heldAnswers struct {
	mu       sync.Mutex
	version  string
	quick    string // the commit and the index's stat: looked at on every question, a fraction of the walk
	answers  map[string]*heldAnswer
	asked    map[string]*heldQuestion
	flying   map[string]*flight
	warming  chan struct{}
	hits     int
	misses   int
	lastWalk time.Time
}

func newHeldAnswers() *heldAnswers {
	return &heldAnswers{answers: map[string]*heldAnswer{}, asked: map[string]*heldQuestion{},
		flying: map[string]*flight{}, warming: make(chan struct{}, 1)}
}

func heldKey(method string, params map[string]any) string {
	b, _ := json.Marshal(params) // a map's keys in order: the same question, the same key
	return method + "\x00" + string(b)
}

// quickVersion is what changes when anything is committed or staged: HEAD's commit and the index's stat.
func quickVersion(g *Garden) string {
	gitDir := gitDirOf(g.Conf.Path)
	q := stamp(g)
	if fi, err := os.Stat(filepath.Join(gitDir, "index")); err == nil {
		q += " " + strconv.FormatInt(fi.ModTime().UnixNano(), 10) + ":" + strconv.FormatInt(fi.Size(), 10)
	}
	return q
}

// fullVersion is the quick version, each document's stat and GARDEN.md's, and the day.
func fullVersion(g *Garden, quick string) string {
	h := sha256.New()
	h.Write([]byte(quick))
	h.Write([]byte("\x00" + time.Now().Format("2006-01-02")))
	var lines []string
	add := func(p string) {
		if fi, err := os.Stat(p); err == nil {
			lines = append(lines, p+"\x00"+strconv.FormatInt(fi.ModTime().UnixNano(), 10)+":"+strconv.FormatInt(fi.Size(), 10))
		}
	}
	add(filepath.Join(g.Conf.Path, "GARDEN.md"))
	for _, d := range []string{"beans", "mappings"} {
		_ = filepath.WalkDir(filepath.Join(g.Conf.Path, d), func(p string, e fs.DirEntry, err error) error {
			if err == nil && !e.IsDir() && strings.HasSuffix(p, ".md") {
				if fi, err := e.Info(); err == nil {
					lines = append(lines, p+"\x00"+strconv.FormatInt(fi.ModTime().UnixNano(), 10)+":"+strconv.FormatInt(fi.Size(), 10))
				}
			}
			return nil
		})
	}
	sort.Strings(lines)
	for _, l := range lines {
		h.Write([]byte(l + "\n"))
	}
	return hex.EncodeToString(h.Sum(nil))
}

// heldVersion is the garden's version now: walked again when the commit or the index moved, or every second.
func (s *Server) heldVersion(g *Garden, a *heldAnswers) string {
	quick := quickVersion(g)
	a.mu.Lock()
	same := quick == a.quick && a.version != "" && time.Since(a.lastWalk) < time.Second
	v := a.version
	a.mu.Unlock()
	if same {
		return v
	}
	return s.heldWalk(g, a, quick)
}

// heldWalk reads the version afresh; when it moved, the answers held go, and those asked lately are asked again.
func (s *Server) heldWalk(g *Garden, a *heldAnswers, quick string) string {
	v := fullVersion(g, quick)
	a.mu.Lock()
	moved := v != a.version
	if moved {
		a.version, a.answers = v, map[string]*heldAnswer{}
	}
	a.quick, a.lastWalk = quick, time.Now()
	a.mu.Unlock()
	if moved {
		s.heldWarm(g, a)
	}
	return v
}

func (s *Server) held(g *Garden) *heldAnswers {
	s.heldMu.Lock()
	defer s.heldMu.Unlock()
	if s.heldOf == nil {
		s.heldOf = map[string]*heldAnswers{}
	}
	a := s.heldOf[g.Conf.Name]
	if a == nil {
		a = newHeldAnswers()
		s.heldOf[g.Conf.Name] = a
	}
	return a
}

// call is the worker's answer to a question that reads: from memory at the garden's version, or asked once — several
// asking the same question at once wait for the one asking — and kept while the version stood still.
func (s *Server) call(g *Garden, method string, params map[string]any, timeout time.Duration) (json.RawMessage, error) {
	if !heldMethods[method] || os.Getenv("DAFTARD_HELD") == "off" || headOf(g.Conf.Path) == "" {
		return g.Worker.Call(method, params, timeout) // a write, or held answers off, or a garden that is no git work tree
	}
	a := s.held(g)
	key := heldKey(method, params)
	v := s.heldVersion(g, a)
	a.mu.Lock()
	a.asked[key] = &heldQuestion{method: method, params: params, asked: time.Now()}
	if h := a.answers[key]; h != nil {
		h.asked = time.Now()
		a.hits++
		raw := h.raw
		a.mu.Unlock()
		return raw, nil
	}
	a.misses++
	if f := a.flying[key]; f != nil {
		a.mu.Unlock()
		<-f.done
		return f.raw, f.err
	}
	f := &flight{done: make(chan struct{})}
	a.flying[key] = f
	a.mu.Unlock()
	f.raw, f.err = g.Worker.Call(method, params, timeout)
	after := s.heldVersion(g, a)
	a.mu.Lock()
	delete(a.flying, key)
	if f.err == nil && after == v && a.version == v { // read while the garden stood still: kept
		a.answers[key] = &heldAnswer{raw: f.raw, asked: time.Now()}
		if len(a.answers) > heldMax {
			a.evictLocked()
		}
	}
	a.mu.Unlock()
	close(f.done)
	return f.raw, f.err
}

func (a *heldAnswers) evictLocked() {
	type kv struct {
		k string
		t time.Time
	}
	all := make([]kv, 0, len(a.answers))
	for k, h := range a.answers {
		all = append(all, kv{k, h.asked})
	}
	sort.Slice(all, func(i, j int) bool { return all[i].t.Before(all[j].t) })
	for _, x := range all[:len(all)-heldMax] {
		delete(a.answers, x.k)
	}
}

// heldWarm asks again, in the background and one at a time, the questions asked lately, the latest first: after a
// change, the page a person returns to is read before they ask. A warm already under way takes the newer version.
func (s *Server) heldWarm(g *Garden, a *heldAnswers) {
	select {
	case a.warming <- struct{}{}:
	default:
		return // one warm at a time per garden; it reads the newest version as it goes
	}
	go func() {
		defer func() { <-a.warming }()
		a.mu.Lock()
		var qs []*heldQuestion
		for k, q := range a.asked {
			if time.Since(q.asked) > heldRecent {
				delete(a.asked, k)
				continue
			}
			qs = append(qs, q)
		}
		a.mu.Unlock()
		sort.Slice(qs, func(i, j int) bool { return qs[i].asked.After(qs[j].asked) })
		if len(qs) > heldWarm {
			qs = qs[:heldWarm]
		}
		for _, q := range qs {
			_, _ = s.call(g, q.method, q.params, 2*time.Minute)
		}
	}()
}

// derived is what a handler makes of an answer — its JSON read into a struct, its scripts' hashes — held beside the
// answer it was made from, so a page asked again does none of that work again either.
func (s *Server) derived(g *Garden, method string, params map[string]any, timeout time.Duration, name string,
	make func(json.RawMessage) (any, error)) (any, error) {
	raw, err := s.call(g, method, params, timeout)
	if err != nil {
		return nil, err
	}
	if !heldMethods[method] || len(raw) == 0 {
		return make(raw)
	}
	a, key := s.held(g), heldKey(method, params)
	same := func(h *heldAnswer) bool { return h != nil && len(h.raw) > 0 && &h.raw[0] == &raw[0] }
	a.mu.Lock()
	if h := a.answers[key]; same(h) {
		if d, ok := h.derived[name]; ok {
			a.mu.Unlock()
			return d, nil
		}
	}
	a.mu.Unlock()
	d, err := make(raw)
	if err != nil {
		return nil, err
	}
	a.mu.Lock()
	if h := a.answers[key]; same(h) {
		if h.derived == nil {
			h.derived = map[string]any{}
		}
		h.derived[name] = d
	}
	a.mu.Unlock()
	return d, nil
}

// heldStats is how often an answer came from memory: for the log and the tests.
func (s *Server) heldStats(g *Garden) (hits, misses int) {
	a := s.held(g)
	a.mu.Lock()
	defer a.mu.Unlock()
	return a.hits, a.misses
}
