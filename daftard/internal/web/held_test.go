package web

import (
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"
)

// heldRig is the view rig with its garden a git work tree, as every garden is: its answers are held.
func heldRig(t *testing.T) *viewRig {
	t.Helper()
	if _, err := exec.LookPath("git"); err != nil {
		t.Skip("no git")
	}
	v := newViewRig(t, "view")
	g := filepath.Join(v.dir, "garden")
	if err := os.MkdirAll(filepath.Join(g, "beans"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(g, "beans", "ana.md"), []byte("---\nbean: ana\n---\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitIn(t, g, "init", "-q")
	gitIn(t, g, "add", "-A")
	gitIn(t, g, "-c", "user.name=t", "-c", "user.email=t@localhost", "commit", "-q", "-m", "a garden")
	return v
}

func gitIn(t *testing.T, dir string, args ...string) {
	t.Helper()
	c := exec.Command("git", args...)
	c.Dir = dir
	if out, err := c.CombinedOutput(); err != nil {
		t.Fatalf("git %v: %v %s", args, err, out)
	}
}

func (v *viewRig) count(method string) int {
	n := 0
	for _, a := range v.asked() {
		if a["method"] == method {
			n++
		}
	}
	return n
}

// A PAGE ASKED AGAIN IS ANSWERED FROM MEMORY: the worker is asked once at a version of the garden, and the same page,
// for the same reader, is then answered from daftard's memory, word for word.
func TestAPageAskedAgainIsAnsweredFromMemory(t *testing.T) {
	v := heldRig(t)
	a := v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	b := v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if a.Code != 200 || b.Code != 200 || a.Body.String() != b.Body.String() {
		t.Fatalf("the same answer twice: %d %d %q %q", a.Code, b.Code, a.Body.String(), b.Body.String())
	}
	if n := v.count("view_page"); n != 1 {
		t.Fatalf("the worker is asked once, the second answer is from memory: asked %d times", n)
	}
	if hits, _ := v.s.heldStats(v.s.Gardens[0]); hits != 1 {
		t.Fatalf("one answer from memory: %d", hits)
	}
	v.do("GET", "/api/view/page?g=g&page=page-people", "", true)
	if n := v.count("view_page"); n != 2 {
		t.Fatalf("another page is another question: asked %d times", n)
	}
}

// A CHANGE MOVES THE VERSION: a commit, and a document edited and not committed, each make the next asking reach the
// worker; nothing older than the garden's files is answered.
func TestAChangeIsNeverAnsweredFromBefore(t *testing.T) {
	v := heldRig(t)
	g := filepath.Join(v.dir, "garden")
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if err := os.WriteFile(filepath.Join(g, "beans", "bo.md"), []byte("---\nbean: bo\n---\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitIn(t, g, "add", "-A")
	gitIn(t, g, "-c", "user.name=t", "-c", "user.email=t@localhost", "commit", "-q", "-m", "bo")
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if n := v.count("view_page"); n != 2 {
		t.Fatalf("after a commit the page is read again: asked %d times", n)
	}
	time.Sleep(1100 * time.Millisecond) // an edit with nothing committed or staged is seen by the walk, once a second
	if err := os.WriteFile(filepath.Join(g, "beans", "bo.md"), []byte("---\nbean: bo\ntitle: \"Bo\"\n---\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	time.Sleep(1100 * time.Millisecond)
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if n := v.count("view_page"); n < 3 {
		t.Fatalf("after an edit not committed the page is read again: asked %d times", n)
	}
}

// A WRITE IS NEVER HELD, and another reader's way of reading is another question.
func TestAWriteIsNeverHeldAndPrefsAreAnotherQuestion(t *testing.T) {
	v := heldRig(t)
	for i := 0; i < 2; i++ {
		v.do("POST", "/api/view/write?g=g", `{"bean":"ana","ops":[]}`, true)
	}
	if n := v.count("view_write"); n != 2 {
		t.Fatalf("each save reaches the worker: %d", n)
	}
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if w := v.do("POST", "/api/prefs?g=g", `{"locale":"fa-u-ca-gregory"}`, true); w.Code != 200 {
		t.Fatalf("prefs kept: %d %s", w.Code, w.Body.String())
	}
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if n := v.count("view_page"); n != 2 {
		t.Fatalf("the reader's own way of reading is another question: asked %d times", n)
	}
}

// AFTER A CHANGE, WHAT WAS ASKED LATELY IS ASKED AGAIN BEFORE ANYONE ASKS: the page a person comes back to is ready.
func TestAfterAChangeTheLatestQuestionsAreAskedAgain(t *testing.T) {
	v := heldRig(t)
	g := filepath.Join(v.dir, "garden")
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	v.do("GET", "/api/view/page?g=g&page=page-people", "", true)
	if err := os.WriteFile(filepath.Join(g, "beans", "bo.md"), []byte("---\nbean: bo\n---\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	gitIn(t, g, "add", "-A")
	gitIn(t, g, "-c", "user.name=t", "-c", "user.email=t@localhost", "commit", "-q", "-m", "bo")
	v.s.changed(v.s.Gardens[0]) // as daftard's own save says it
	deadline := time.Now().Add(10 * time.Second)
	for v.count("view_page") < 4 && time.Now().Before(deadline) {
		time.Sleep(50 * time.Millisecond)
	}
	if n := v.count("view_page"); n != 4 {
		t.Fatalf("both pages asked again in the background: asked %d times", n)
	}
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if n := v.count("view_page"); n != 4 {
		t.Fatalf("and then answered from memory: asked %d times", n)
	}
}

// THE VIEW'S OWN PAGE, AND ITS POLICY, ARE MADE ONCE PER ANSWER: the same page and the same Content-Security-Policy,
// and the worker asked once.
func TestTheViewsPageIsMadeOnce(t *testing.T) {
	v := heldRig(t)
	a := v.do("GET", "/view?g=g&page=page-now", "", true)
	b := v.do("GET", "/view?g=g&page=page-now", "", true)
	if a.Code != 200 || a.Body.String() != b.Body.String() || a.Header().Get("Content-Security-Policy") == "" ||
		a.Header().Get("Content-Security-Policy") != b.Header().Get("Content-Security-Policy") {
		t.Fatalf("the same page and policy: %d %q %q", a.Code, a.Header().Get("Content-Security-Policy"), b.Header().Get("Content-Security-Policy"))
	}
	if n := v.count("view_html"); n != 1 {
		t.Fatalf("asked once: %d", n)
	}
}

// NOTHING IS HELD WHERE IT SHOULD NOT BE: a garden that is no git work tree, or DAFTARD_HELD=off, asks the worker each
// time, as before.
func TestNothingIsHeldOutsideAWorkTreeOrWhenOff(t *testing.T) {
	v := newViewRig(t, "view")
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	v.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if n := v.count("view_page"); n != 2 {
		t.Fatalf("no work tree, nothing held: %d", n)
	}
	w := heldRig(t)
	t.Setenv("DAFTARD_HELD", "off")
	w.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	w.do("GET", "/api/view/page?g=g&page=page-now", "", true)
	if n := w.count("view_page"); n != 2 {
		t.Fatalf("held answers off: %d", n)
	}
}
