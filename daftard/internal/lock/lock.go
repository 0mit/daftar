// Package lock is a garden's own daemon, alone: one daftard serves one garden on one machine (the operator,
// 2026-10-14), so what it holds of the garden in memory is the garden's only copy being answered from, and a second
// daftard asked to serve the same garden is refused, naming the first. The lock is a file in the garden's git folder,
// held open for as long as the daemon runs: the system lets it go when the process ends, however it ends, so a daemon
// that crashed never leaves its garden locked.
package lock

import (
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

// File is the lock's name in the garden's git folder.
const File = "daftard.lock"

// ErrHeld is a garden another daemon serves already.
var ErrHeld = errors.New("another daftard serves this garden")

// Lock is a garden held by this process.
type Lock struct {
	f    *os.File
	Path string
}

// Garden takes the lock of the garden at gardenPath, writing this process's id into it for whoever finds it held.
func Garden(gardenPath string) (*Lock, error) {
	dir, err := gitDir(gardenPath)
	if err != nil {
		return nil, err
	}
	p := filepath.Join(dir, File)
	f, err := take(p)
	if err != nil {
		if errors.Is(err, ErrHeld) {
			who, _ := os.ReadFile(p)
			return nil, fmt.Errorf("%w (%s): %s", ErrHeld, strings.TrimSpace(string(who)), gardenPath)
		}
		return nil, err
	}
	_ = f.Truncate(0)
	_, _ = f.WriteAt([]byte(fmt.Sprintf("pid %d\n", os.Getpid())), 0)
	return &Lock{f: f, Path: p}, nil
}

// Release lets the garden go (the process's end does too).
func (l *Lock) Release() {
	if l != nil && l.f != nil {
		release(l.f)
		_ = l.f.Close()
		l.f = nil
	}
}

// gitDir is the garden's git folder: .git, or where a worktree's .git file points.
func gitDir(gardenPath string) (string, error) {
	g := filepath.Join(gardenPath, ".git")
	fi, err := os.Stat(g)
	if err != nil {
		return "", fmt.Errorf("%s is no git work tree: a garden is served from its own", gardenPath)
	}
	if fi.IsDir() {
		return g, nil
	}
	b, err := os.ReadFile(g)
	if err != nil {
		return "", err
	}
	d := strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(string(b)), "gitdir:"))
	if !filepath.IsAbs(d) {
		d = filepath.Join(gardenPath, d)
	}
	return d, nil
}
