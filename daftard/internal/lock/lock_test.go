package lock

import (
	"errors"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func garden(t *testing.T) string {
	t.Helper()
	d := t.TempDir()
	if err := os.Mkdir(filepath.Join(d, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	return d
}

// ONE GARDEN, ONE DAEMON: a garden held is refused to a second holder, naming the first; let go, it is taken again.
func TestAGardenHeldIsRefusedASecondDaemon(t *testing.T) {
	g := garden(t)
	a, err := Garden(g)
	if err != nil {
		t.Fatal(err)
	}
	if _, err := Garden(g); !errors.Is(err, ErrHeld) || !strings.Contains(err.Error(), "pid") {
		t.Fatalf("a second holder is refused, naming the first: %v", err)
	}
	a.Release()
	b, err := Garden(g)
	if err != nil {
		t.Fatalf("let go, the garden is taken again: %v", err)
	}
	b.Release()
}

// A WORKTREE IS LOCKED IN ITS OWN GIT FOLDER, where its .git file points.
func TestAWorktreeIsLockedWhereItsGitFilePoints(t *testing.T) {
	if _, err := exec.LookPath("git"); err != nil {
		t.Skip("no git")
	}
	main := t.TempDir()
	for _, a := range [][]string{{"init", "-q"}, {"-c", "user.name=t", "-c", "user.email=t@l", "commit", "-q", "--allow-empty", "-m", "a"},
		{"worktree", "add", "-q", "-b", "side", filepath.Join(main, "w")}} {
		c := exec.Command("git", a...)
		c.Dir = main
		if out, err := c.CombinedOutput(); err != nil {
			t.Fatalf("git %v: %v %s", a, err, out)
		}
	}
	l, err := Garden(filepath.Join(main, "w"))
	if err != nil {
		t.Fatal(err)
	}
	defer l.Release()
	if !strings.Contains(filepath.ToSlash(l.Path), "/.git/worktrees/") {
		t.Fatalf("held in the worktree's own git folder: %s", l.Path)
	}
	m, err := Garden(main)
	if err != nil {
		t.Fatalf("the main copy is another garden's copy, held apart: %v", err)
	}
	m.Release()
}

// NO GIT FOLDER, NO GARDEN: a folder that is no work tree is refused, never locked somewhere else.
func TestAFolderThatIsNoWorkTreeIsRefused(t *testing.T) {
	if _, err := Garden(t.TempDir()); err == nil || !strings.Contains(err.Error(), "no git work tree") {
		t.Fatalf("refused: %v", err)
	}
}
