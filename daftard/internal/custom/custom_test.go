package custom

import (
	"errors"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/sitting"
)

// The test binary is ssh-keygen's askpass, as daftard is.
func TestMain(m *testing.M) {
	if os.Getenv(sitting.AskpassVar) != "" {
		os.Exit(sitting.AskpassMain(os.Args[1:]))
	}
	os.Exit(m.Run())
}

// signer is an askpass on the loopback and a key for ana, made under her passphrase.
func signer(t *testing.T) (*sitting.Askpass, sitting.Keys) {
	t.Helper()
	a := sitting.NewAskpass()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.Handle(sitting.AskpassPath, a)
	srv := &http.Server{Handler: mux}
	go func() { _ = srv.Serve(ln) }()
	t.Cleanup(func() { _ = srv.Close() })
	a.Exe, _ = os.Executable()
	a.Base = "http://" + ln.Addr().String()
	k := sitting.Keys{Dir: t.TempDir()}
	if _, err := k.Make("ana", "ana's own words", a); err != nil {
		t.Fatal(err)
	}
	return a, k
}

func git(t *testing.T, dir string, args ...string) string {
	t.Helper()
	c := exec.Command("git", args...)
	c.Dir = dir
	out, err := c.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v %s", args, err, out)
	}
	return string(out)
}

func run(t *testing.T, dir string, args ...string) {
	t.Helper()
	c := exec.Command("git", args...)
	c.Dir = dir
	if out, err := c.CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v %s", args, err, out)
	}
}

// two machines' copies of one garden, and its hub
func machines(t *testing.T) (*Store, *Store) {
	root := t.TempDir()
	hub := filepath.Join(root, "hub.git")
	run(t, root, "init", "-q", "--bare", hub)
	var out []*Store
	for _, name := range []string{"laptop", "server"} {
		dir := filepath.Join(root, name)
		run(t, root, "init", "-q", dir)
		run(t, dir, "remote", "add", "hub", hub)
		s := New(dir, "hub")
		s.Machine = name
		out = append(out, s)
	}
	return out[0], out[1]
}

func must(t *testing.T, err error) {
	t.Helper()
	if err != nil {
		t.Fatal(err)
	}
}

func text(s *Store, key string) string { return s.Labels("ana")[key].Text }

func TestTwoMachinesAgree(t *testing.T) {
	a, b := machines(t)
	must(t, a.Set("ana", "nav.cases", "مراجعان", "پرونده‌ها"))
	if _, err := a.Sync("ana"); err != nil {
		t.Fatal(err)
	}
	changed, err := b.Sync("ana")
	must(t, err)
	if !changed || text(b, "nav.cases") != "مراجعان" || b.Labels("ana")["nav.cases"].Was != "پرونده‌ها" {
		t.Fatalf("the server did not take the laptop's label: %v %v", changed, b.Labels("ana"))
	}

	// apart: each changes a different word, and both the same word (the server's later)
	must(t, a.Set("ana", "nav.people", "آدم‌ها", "اشخاص"))
	must(t, a.Set("ana", "title.home", "خانه", "امروز"))
	must(t, b.Set("ana", "nav.report", "گزارش ماه", "گزارش"))
	must(t, b.Set("ana", "title.home", "میز کار", "امروز"))
	for _, s := range []*Store{a, b, a} {
		if _, err := s.Sync("ana"); err != nil {
			t.Fatal(err)
		}
	}
	for _, s := range []*Store{a, b} {
		got := s.Labels("ana")
		if got["nav.people"].Text != "آدم‌ها" || got["nav.report"].Text != "گزارش ماه" || got["title.home"].Text != "میز کار" ||
			got["nav.cases"].Text != "مراجعان" {
			t.Fatalf("%s reads %v", s.Machine, got)
		}
	}

	// a word set back to the page's own stays set back, though the other machine still had it
	must(t, a.Set("ana", "nav.cases", "", "پرونده‌ها"))
	for _, s := range []*Store{a, b, a} {
		if _, err := s.Sync("ana"); err != nil {
			t.Fatal(err)
		}
	}
	for _, s := range []*Store{a, b} {
		if _, ok := s.Labels("ana")["nav.cases"]; ok {
			t.Fatalf("%s brought back a label that was set back", s.Machine)
		}
	}

	// one person's labels are not another's
	if len(a.Labels("bo")) != 0 {
		t.Fatal("another person reads ana's labels")
	}
}

func TestNoHubKeepsItHere(t *testing.T) {
	dir := t.TempDir()
	run(t, dir, "init", "-q")
	s := New(dir, "hub")
	must(t, s.Set("ana", "nav.cases", "مراجعان", "پرونده‌ها"))
	if changed, err := s.Sync("ana"); changed || err != nil {
		t.Fatalf("no hub: %v %v", changed, err)
	}
	if text(s, "nav.cases") != "مراجعان" {
		t.Fatal("the label was lost")
	}
}

func TestRefusesAStrangePerson(t *testing.T) {
	dir := t.TempDir()
	run(t, dir, "init", "-q")
	s := New(dir, "")
	if err := s.Set("../heads/main", "nav.cases", "x", "y"); err == nil {
		t.Fatal("a person who is no ref name was taken")
	}
}

// WHERE THE HUB TAKES ONLY SIGNED LABELS (bin/hub.py, Y8), every commit on a person's ref is theirs: a label set in
// their sitting is signed with their key, and two machines' labels that moved apart wait for the next sitting to be
// merged, since a merge is a new commit its person signs.
func TestSignedOnly(t *testing.T) {
	if _, err := exec.LookPath("ssh-keygen"); err != nil {
		t.Skip("no ssh-keygen on this machine")
	}
	a, b := machines(t)
	a.SignedOnly, b.SignedOnly = true, true
	ask, keys := signer(t)
	tok := ask.Issue("ana's own words", 8, time.Minute)
	env := keys.SignEnv("ana", "Ana", "ana@example.org", tok, ask)
	must(t, a.Set("ana", "nav.cases", "x", "y", env...))
	if sig := git(t, a.Path, "cat-file", "commit", Ref("ana")); !strings.Contains(sig, "BEGIN SSH SIGNATURE") ||
		!strings.Contains(sig, "author Ana <ana@example.org>") {
		t.Fatalf("a label set in a sitting is its person's commit, signed: %s", sig)
	}
	_, err := a.Sync("ana")
	must(t, err)
	_, err = b.Sync("ana")
	must(t, err)
	must(t, a.Set("ana", "nav.people", "p", "q", env...))
	must(t, b.Set("ana", "nav.report", "r", "s", env...))
	_, err = a.Sync("ana")
	must(t, err)
	if _, err := b.Sync("ana"); !errors.Is(err, ErrWaits) {
		t.Fatalf("labels that moved apart wait for their person, unmerged: %v", err)
	}
	if _, err := b.Sync("ana", env...); err != nil {
		t.Fatalf("...and in their sitting they are merged, and signed: %v", err)
	}
	if sig := git(t, b.Path, "cat-file", "commit", Ref("ana")); !strings.Contains(sig, "BEGIN SSH SIGNATURE") {
		t.Fatalf("the merge is signed: %s", sig)
	}
	if got := b.Labels("ana"); got["nav.people"].Text != "p" || got["nav.report"].Text != "r" {
		t.Fatalf("both machines' words stand: %v", got)
	}
}

// A PERSON'S FAVOURITES ARE KEPT BESIDE THEIR LABELS (design §10.2, P5.4): Odoo's client reads them from this ref, so
// a label set afterwards keeps them, and two machines that saved different searches apart both keep both.
func TestFavouritesKeptBesideLabels(t *testing.T) {
	a, b := machines(t)
	put := func(s *Store, doc string) { // the ref holding a doc as a person's earlier save left it
		dir := s.Path
		blob := strings.TrimSpace(gitIn(t, dir, doc, "hash-object", "-w", "--stdin"))
		tree := strings.TrimSpace(gitIn(t, dir, "100644 blob "+blob+"\tlabels.json\n", "mktree"))
		commit := strings.TrimSpace(gitIn(t, dir, "", "commit-tree", tree, "-m", "ana: a favourite"))
		run(t, dir, "update-ref", Ref("ana"), commit)
	}
	favs := func(s *Store) string { return git(t, s.Path, "cat-file", "blob", Ref("ana")+":labels.json") }
	put(a, `{"person": "ana", "labels": {}, "favourites": {"f1": {"model": "hr.leave", "name": "Mine this month", "domain": "[]", "at": "2026-10-11T00:00:00.000000000Z"}}}`)
	must(t, a.Set("ana", "nav.cases", "مراجعان", "پرونده‌ها"))
	if !strings.Contains(favs(a), "Mine this month") || text(a, "nav.cases") != "مراجعان" {
		t.Fatalf("a label set took the favourite away: %s", favs(a))
	}
	if _, err := a.Sync("ana"); err != nil {
		t.Fatal(err)
	}
	if _, err := b.Sync("ana"); err != nil {
		t.Fatal(err)
	}
	// apart: the server saves another search, the laptop sets a label
	put(b, strings.Replace(favs(b), `"favourites": {`, `"favourites": {"f2": {"model": "hr.employee", "name": "My team", "at": "2026-10-11T01:00:00.000000000Z"}, `, 1))
	must(t, a.Set("ana", "nav.people", "آدم‌ها", "اشخاص"))
	for _, s := range []*Store{a, b, a} {
		if _, err := s.Sync("ana"); err != nil {
			t.Fatal(err)
		}
	}
	for _, s := range []*Store{a, b} {
		got := favs(s)
		if !strings.Contains(got, "Mine this month") || !strings.Contains(got, "My team") || text(s, "nav.people") != "آدم‌ها" {
			t.Fatalf("%s lost a favourite or a label in the merge: %s", s.Machine, got)
		}
	}
}

func gitIn(t *testing.T, dir, stdin string, args ...string) string {
	t.Helper()
	c := exec.Command("git", args...)
	c.Dir = dir
	c.Stdin = strings.NewReader(stdin)
	out, err := c.Output()
	if err != nil {
		t.Fatalf("git %v: %v", args, err)
	}
	return string(out)
}
