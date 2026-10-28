package proc

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sync"
)

var gitOnce struct {
	sync.Once
	path  string
	cache bool
}

// Git is the git program: the one on the PATH, or, on Windows, where Git for Windows installs itself. A program
// started at logon keeps the PATH of that moment, and Git installed since is missing from it (exchange/exchange.py
// finds it the same way).
func Git() string {
	gitOnce.Do(func() {
		home, _ := os.UserHomeDir()
		gitOnce.path, gitOnce.cache = findGit(runtime.GOOS, exec.LookPath, os.Getenv, home, func(p string) bool {
			_, err := os.Stat(p)
			return err == nil
		}, filepath.Glob)
	})
	return gitOnce.path
}

// GitFromCache says whether Git found its program in another tool's cache rather than in an install of Git — a file
// any program of this account can put there (security audit 2026-10-10, 2.12). daftard says so in its log at every
// start, so a machine that still relies on it is seen before the cache is dropped from the places looked in.
func GitFromCache() bool {
	Git()
	return gitOnce.cache
}

// findGit is where Git looks, in order: the PATH; then, on Windows, Git for Windows' two install folders; then, last,
// a tool's cache that carries a git of its own (cache true).
func findGit(goos string, lookPath func(string) (string, error), getenv func(string) string, home string,
	exists func(string) bool, glob func(string) ([]string, error)) (string, bool) {
	if p, err := lookPath("git"); err == nil {
		return p, false
	}
	if goos != "windows" {
		return "git", false
	}
	for _, p := range []string{
		filepath.Join(getenv("ProgramFiles"), "Git", "cmd", "git.exe"),
		filepath.Join(getenv("LOCALAPPDATA"), "Programs", "Git", "cmd", "git.exe"),
	} {
		if exists(p) {
			return p, false
		}
	}
	found, _ := glob(filepath.Join(home, ".cache", "codex-runtimes", "*", "dependencies", "native", "git", "cmd", "git.exe"))
	for _, p := range found {
		if exists(p) {
			return p, true
		}
	}
	return "git", false
}
