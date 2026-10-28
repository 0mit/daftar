// Package custom is what a person changed of the handplace for themselves: today, the words on its pages (labels).
//
// A CUSTOMISATION IS THE PERSON'S, NOT THE GARDEN'S. A garden's names and data are its beans', kept sensible there and
// edited as data, with their journal entry; a label only changes how one person's handplace words its own interface
// (a menu, a heading, a button), never what a bean says. So it is never a bean, never in the journal, never judged by
// the gate and never carried by the exchange. And one person's labels are never another's: each person has their own.
//
// IT IS KEPT WHERE THE GARDEN IS, so every machine agrees: in the garden's own repository, on a ref of its own,
// refs/daftar/custom/<person>, beside the garden's branch and outside its tree. The garden's sync never moves it; daftard
// carries it to and from the hub the garden syncs with, after each step, so every hub that serves the garden, and every machine the
// person reads on, comes to the same labels.
//
// CONSISTENCY. Each label is {text, was, at, on}: `was` is the page's own word it replaced, so a page whose own word
// changed since shows the label as one to look at again; `at` is when it was set (UTC) and `on` the machine. Two
// machines that changed labels apart merge word by word: different words both stand; for the same word the later `at`
// (then `on`) stands, and the other stays in the ref's history. A word set back to the page's own is kept as an empty
// text, so a merge never brings back what was taken out.
package custom

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/proc"
)

// Label is one word a person changed.
type Label struct {
	Text string `json:"text"`          // what they read instead; empty: the page's own word again
	Was  string `json:"was,omitempty"` // the page's own word when they changed it
	At   string `json:"at,omitempty"`  // when, UTC, fixed width so that text order is time order
	On   string `json:"on,omitempty"`  // on which machine
}

// Favourite is one search a person saved in Odoo's client, theirs alone (design §10.2: favourites kept as the person's
// own). Like a label it is how they read, never what the garden says, so it is kept here and merged as a label is:
// key by key, the later change standing; one taken out stays, Gone, so a merge never brings it back.
type Favourite struct {
	Model   string `json:"model"`
	Name    string `json:"name"`
	Domain  string `json:"domain,omitempty"`
	Context string `json:"context,omitempty"`
	Sort    string `json:"sort,omitempty"`
	Default bool   `json:"is_default,omitempty"`
	Action  int    `json:"action_id,omitempty"`
	Gone    bool   `json:"gone,omitempty"`
	At      string `json:"at,omitempty"`
	On      string `json:"on,omitempty"`
}

// Doc is one person's customisations of one garden's handplace: the words of its pages, and their saved searches.
type Doc struct {
	Person     string               `json:"person"`
	Labels     map[string]Label     `json:"labels"`
	Favourites map[string]Favourite `json:"favourites,omitempty"`
}

const stamp = "2006-01-02T15:04:05.000000000Z"
const file = "labels.json"

var personRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}$`)

// Ref is where a person's customisations are kept; hubRef where the hub's copy is read into.
func Ref(person string) string    { return "refs/daftar/custom/" + person }
func hubRef(person string) string { return "refs/daftar/hub-custom/" + person }

// Store is one garden's customisations.
type Store struct {
	Path    string // the garden's working copy
	Remote  string // its hub's remote ("hub"); none: kept on this machine alone
	Machine string
	// SignedOnly is set where its hub takes only a person's own signed labels (bin/hub.py, Y8): every commit on
	// a person's ref is then theirs, signed in their sitting, and two machines' labels that moved apart wait for their
	// next sitting to be merged (ErrWaits), since a merge is a new commit its person signs.
	SignedOnly bool
	mu         sync.Mutex
	sign       []string // the signing environment of the call under way (held under mu)
	// held is each person's labels as last read, by the commit of their ref: read again only when it moved
	held map[string]heldLabels
}

type heldLabels struct {
	commit string
	labels map[string]Label
}

// ErrWaits is a person's labels that moved apart on two machines, where only their own signed commit may join them: the
// merge waits for their next sitting.
var ErrWaits = errors.New("the labels moved apart on two machines, and wait for their person's sitting to be merged")

// New is the store of the garden at path, carried through its hub remote.
func New(path, remote string) *Store {
	host, _ := os.Hostname()
	host, _, _ = strings.Cut(host, ".") // the machine's own name; its network's domain says nothing a merge needs
	return &Store{Path: path, Remote: remote, Machine: strings.ToLower(host)}
}

func (s *Store) git(stdin []byte, args ...string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 90*time.Second)
	defer cancel()
	c := proc.CommandContext(ctx, proc.Git(), args...)
	c.Dir = s.Path
	c.Env = append(append(os.Environ(), "GIT_TERMINAL_PROMPT=0", "GIT_AUTHOR_NAME=daftard", "GIT_AUTHOR_EMAIL=daftard@localhost",
		"GIT_COMMITTER_NAME=daftard", "GIT_COMMITTER_EMAIL=daftard@localhost"), s.sign...) // a sitting's own, where one is given
	if stdin != nil {
		c.Stdin = bytes.NewReader(stdin)
	}
	var out, errb bytes.Buffer
	c.Stdout, c.Stderr = &out, &errb
	if err := c.Run(); err != nil {
		return "", fmt.Errorf("git %s: %v %s", args[0], err, strings.TrimSpace(errb.String()))
	}
	return strings.TrimSpace(out.String()), nil
}

// read is the doc a ref holds and its commit; an absent ref is an empty doc.
func (s *Store) read(person, ref string) (Doc, string) {
	d := Doc{Person: person, Labels: map[string]Label{}}
	commit, err := s.git(nil, "rev-parse", "--verify", "--quiet", ref+"^{commit}")
	if err != nil || commit == "" {
		return d, ""
	}
	if b, err := s.git(nil, "cat-file", "blob", commit+":"+file); err == nil {
		_ = json.Unmarshal([]byte(b), &d)
	}
	if d.Labels == nil {
		d.Labels = map[string]Label{}
	}
	d.Person = person
	return d, commit
}

// write commits d on the person's ref, whose commit must still be old (another writer since: refused, not lost).
func (s *Store) write(person string, d Doc, old, message string, parents ...string) (string, error) {
	b, err := json.MarshalIndent(d, "", " ")
	if err != nil {
		return "", err
	}
	blob, err := s.git(append(b, '\n'), "hash-object", "-w", "--stdin")
	if err != nil {
		return "", err
	}
	tree, err := s.git([]byte("100644 blob "+blob+"\t"+file+"\n"), "mktree")
	if err != nil {
		return "", err
	}
	args := []string{"commit-tree", tree, "-m", message}
	if len(s.sign) > 0 {
		args = append(args, "-S") // commit-tree signs only when asked: commit.gpgsign is git commit's
	}
	for _, p := range parents {
		if p != "" {
			args = append(args, "-p", p)
		}
	}
	commit, err := s.git(nil, args...)
	if err != nil {
		return "", err
	}
	if _, err := s.git(nil, "update-ref", "-m", "daftard: "+message, Ref(person), commit, old); err != nil {
		return "", err
	}
	return commit, nil
}

// Labels are the person's labels as they read them: key → {text, was}; words set back to the page's own are left out.
func (s *Store) Labels(person string) map[string]Label {
	out := map[string]Label{}
	if !personRe.MatchString(person) {
		return out
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	// HELD (2026-10-14): the ref's commit is read from git's own files, no process started; the labels are read
	// again (two git processes) only when it moved. A ref git cannot be read so (none, or an odd layout) is asked as
	// before.
	tip, known := refCommit(s.Path, Ref(person))
	if h, ok := s.held[person]; ok && known && h.commit == tip {
		for k, l := range h.labels {
			out[k] = l
		}
		return out
	}
	d, commit := s.read(person, Ref(person))
	for k, l := range d.Labels {
		if l.Text != "" {
			out[k] = Label{Text: l.Text, Was: l.Was}
		}
	}
	if known && commit == tip {
		if s.held == nil {
			s.held = map[string]heldLabels{}
		}
		kept := make(map[string]Label, len(out))
		for k, l := range out {
			kept[k] = l
		}
		s.held[person] = heldLabels{commit: tip, labels: kept}
	}
	return out
}

// refCommit is a ref's commit read from the garden's git files — its own file, else packed-refs — and whether that
// reading can be trusted: "" and true where the ref is in neither (no labels yet).
func refCommit(path, ref string) (string, bool) {
	gitDir := filepath.Join(path, ".git")
	if fi, err := os.Stat(gitDir); err == nil && !fi.IsDir() {
		b, err := os.ReadFile(gitDir)
		if err != nil {
			return "", false
		}
		gitDir = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(string(b)), "gitdir:"))
		if !filepath.IsAbs(gitDir) {
			gitDir = filepath.Join(path, gitDir)
		}
		// a worktree keeps its own HEAD but shares its refs: they are in the common folder
		if c, err := os.ReadFile(filepath.Join(gitDir, "commondir")); err == nil {
			common := strings.TrimSpace(string(c))
			if !filepath.IsAbs(common) {
				common = filepath.Join(gitDir, common)
			}
			gitDir = common
		}
	} else if err != nil {
		return "", false
	}
	if b, err := os.ReadFile(filepath.Join(gitDir, filepath.FromSlash(ref))); err == nil {
		return strings.TrimSpace(string(b)), true
	}
	b, err := os.ReadFile(filepath.Join(gitDir, "packed-refs"))
	if err != nil {
		return "", os.IsNotExist(err)
	}
	for _, line := range strings.Split(string(b), "\n") {
		if f := strings.Fields(line); len(f) == 2 && f[1] == ref {
			return f[0], true
		}
	}
	return "", true
}

// Set changes one of the person's labels; an empty text sets it back to the page's own word. `sign` is the signing
// environment of the person's sitting (internal/sitting SignEnv): the commit is then theirs, signed.
func (s *Store) Set(person, key, text, was string, sign ...string) error {
	if !personRe.MatchString(person) {
		return errors.New("no reader to keep the label for")
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sign = sign
	defer func() { s.sign = nil }()
	if s.SignedOnly && len(sign) == 0 {
		return errors.New("a label is kept here only as its person's own signed commit: it is set in their sitting")
	}
	d, old := s.read(person, Ref(person))
	if cur, ok := d.Labels[key]; (ok && cur.Text == text && (text == "" || cur.Was == was)) || (!ok && text == "") {
		return nil
	}
	d.Labels[key] = Label{Text: text, Was: was, At: time.Now().UTC().Format(stamp), On: s.Machine}
	what := "set " + key
	if text == "" {
		what = "reset " + key
	}
	_, err := s.write(person, d, old, "labels of "+person+": "+what, old)
	return err
}

// Merge is two docs word by word, and favourite by favourite: for each, the later change (then the machine's name,
// then the text, so that every machine picks the same).
func Merge(a, b Doc) Doc {
	out := Doc{Person: a.Person, Labels: map[string]Label{}}
	for k, l := range a.Labels {
		out.Labels[k] = l
	}
	for k, l := range b.Labels {
		if cur, ok := out.Labels[k]; !ok || later(l, cur) {
			out.Labels[k] = l
		}
	}
	for _, d := range []Doc{a, b} {
		for k, f := range d.Favourites {
			if out.Favourites == nil {
				out.Favourites = map[string]Favourite{}
			}
			if cur, ok := out.Favourites[k]; !ok || laterFavourite(f, cur) {
				out.Favourites[k] = f
			}
		}
	}
	return out
}

func laterFavourite(x, y Favourite) bool {
	if x.At != y.At {
		return x.At > y.At
	}
	if x.On != y.On {
		return x.On > y.On
	}
	return x.Name+x.Domain > y.Name+y.Domain
}

func later(x, y Label) bool {
	if x.At != y.At {
		return x.At > y.At
	}
	if x.On != y.On {
		return x.On > y.On
	}
	return x.Text > y.Text
}

func same(a, b Doc) bool {
	if len(a.Labels) != len(b.Labels) || len(a.Favourites) != len(b.Favourites) {
		return false
	}
	for k, l := range a.Labels {
		if b.Labels[k] != l {
			return false
		}
	}
	for k, f := range a.Favourites {
		if g, ok := b.Favourites[k]; !ok || g != f {
			return false
		}
	}
	return true
}

// Sync carries the person's customisations to and from the hub: fetched, merged word by word with this machine's,
// and pushed. It reports whether what this machine reads changed. With no hub remote it does nothing.
func (s *Store) Sync(person string, sign ...string) (bool, error) {
	if s.Remote == "" || !personRe.MatchString(person) {
		return false, nil
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sign = sign
	defer func() { s.sign = nil }()
	if _, err := s.git(nil, "remote", "get-url", s.Remote); err != nil {
		return false, nil
	}
	if _, err := s.git(nil, "fetch", "--quiet", "--no-tags", s.Remote, "+"+Ref(person)+":"+hubRef(person)); err != nil &&
		!strings.Contains(err.Error(), "find remote ref") {
		return false, err
	}
	local, lc := s.read(person, Ref(person))
	remote, rc := s.read(person, hubRef(person))
	changed := false
	switch {
	case rc == "" && lc == "", rc == lc:
		return false, nil
	case rc == "" || s.ancestor(rc, lc): // only this machine moved
	case lc == "" || s.ancestor(lc, rc): // only the hub moved
		if _, err := s.git(nil, "update-ref", "-m", "daftard: labels from the hub", Ref(person), rc, lc); err != nil {
			return false, err
		}
		return !same(local, remote), nil
	default: // both moved: word by word
		if s.SignedOnly && len(s.sign) == 0 {
			return false, ErrWaits
		}
		merged := Merge(local, remote)
		if _, err := s.write(person, merged, lc, "labels of "+person+": merged with the hub's", lc, rc); err != nil {
			return false, err
		}
		changed = !same(local, merged)
	}
	if _, err := s.git(nil, "push", "--quiet", s.Remote, Ref(person)+":"+Ref(person)); err != nil {
		return changed, err // the hub moved meanwhile: the next step merges again
	}
	return changed, nil
}

func (s *Store) ancestor(a, b string) bool {
	_, err := s.git(nil, "merge-base", "--is-ancestor", a, b)
	return err == nil
}
