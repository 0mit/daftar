// Package guided keeps the guided errors (design/DESIGN.md §3): every refusal or failure gets a reference, a message the
// person may be shown, the people to follow it up with (the source of the privilege the attempt needed, up to the
// gardener), and its whole detail, kept here, off git, for whoever's privileges cover it.
package guided

import (
	"bufio"
	"crypto/rand"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/state"
)

// Contact is someone a person follows an error up with.
type Contact struct {
	Who   string `json:"who"`
	Title string `json:"title"`
	Why   string `json:"why"`             // gardener, a grant, the tools' steward
	Reach string `json:"reach,omitempty"` // how to reach them, in words
	Sees  string `json:"-"`               // what of the detail they may read: all or summary
}

// Record is one guided error.
type Record struct {
	Ref        string    `json:"ref"`
	At         string    `json:"at"`
	Garden     string    `json:"garden"`
	Action     string    `json:"action"` // what was tried (save, read, sync…)
	Status     int       `json:"status"`
	Kind       string    `json:"kind"`    // refused or failed
	Message    string    `json:"message"` // what the person is told
	Diagnostic string    `json:"diagnostic,omitempty"`
	FollowUp   []Contact `json:"followUp"`
}

// Store is the machine's guided-error file, errors.jsonl in the state folder, readable by the user alone.
type Store struct {
	mu   sync.Mutex
	path string
}

// Open opens the store.
func Open() *Store {
	d, _ := state.Ensure()
	return &Store{path: filepath.Join(d, "errors.jsonl")}
}

// crockford is the alphabet of a reference: no I, L, O or U, so it reads aloud and copies by hand without mistakes.
const crockford = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"

// NewRef is a reference like E-7K3Q-9XWD: eight random characters of the alphabet above.
func NewRef() string {
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	out := []byte("E-")
	for i, v := range b {
		if i == 4 {
			out = append(out, '-')
		}
		out = append(out, crockford[int(v)%32]) // 256 is 8 × 32, so every character is as likely
	}
	return string(out)
}

// Add keeps a record and returns its reference.
func (s *Store) Add(r Record) string {
	if r.Ref == "" {
		r.Ref = NewRef()
	}
	if r.At == "" {
		r.At = time.Now().Format(time.RFC3339)
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if f, err := os.OpenFile(s.path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600); err == nil {
		b, _ := json.Marshal(r)
		_, _ = f.Write(append(b, '\n'))
		_ = f.Close()
	}
	return r.Ref
}

// Get finds a record by its reference.
func (s *Store) Get(ref string) (*Record, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	f, err := os.Open(s.path)
	if err != nil {
		return nil, false
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	sc.Buffer(make([]byte, 1<<20), 16<<20)
	var found *Record
	for sc.Scan() {
		var r Record
		if json.Unmarshal(sc.Bytes(), &r) == nil && r.Ref == ref {
			found = &r
		}
	}
	return found, found != nil
}

// For is the record as a reader with the given sight may see it: "all" sees the whole; anyone else the summary, with
// the detail withheld and said to be withheld.
func (r Record) For(sees string) Record {
	if sees == "all" {
		return r
	}
	out := r
	if out.Diagnostic != "" {
		out.Diagnostic = ""
	}
	return out
}

// Sentence is the person's message with its reference and whom to follow it up with, in one line: what a page that
// shows only an error's text (the MVP's carried-over pages) still shows whole.
func (r Record) Sentence() string {
	var names []string
	for _, c := range r.FollowUp {
		n := c.Title
		if n == "" {
			n = c.Who
		}
		if c.Reach != "" {
			n += " (" + c.Reach + ")"
		}
		names = append(names, n)
	}
	s := strings.TrimSpace(r.Message) + " — مرجع: " + r.Ref
	if len(names) > 0 {
		s += " · پیگیری با: " + strings.Join(names, "، ")
	}
	return s
}
