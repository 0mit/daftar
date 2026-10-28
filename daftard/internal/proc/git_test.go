package proc

import (
	"errors"
	"path/filepath"
	"testing"
)

// WHERE GIT IS LOOKED FOR, AND WHETHER IT CAME FROM ANOTHER TOOL'S CACHE (security audit 2026-10-10, 2.12): the PATH,
// then Git for Windows' install folders, then — last, and said so — a tool's cache.
func TestFindGit(t *testing.T) {
	home := filepath.Join("C:", "Users", "ana")
	cached := filepath.Join(home, ".cache", "codex-runtimes", "r1", "dependencies", "native", "git", "cmd", "git.exe")
	installed := filepath.Join("C:", "Program Files", "Git", "cmd", "git.exe")
	env := func(k string) string {
		return map[string]string{"ProgramFiles": filepath.Join("C:", "Program Files"), "LOCALAPPDATA": filepath.Join(home, "AppData", "Local")}[k]
	}
	glob := func(string) ([]string, error) { return []string{cached}, nil }
	onPath := func(string) (string, error) { return "/usr/bin/git", nil }
	notOnPath := func(string) (string, error) { return "", errors.New("not found") }
	has := func(files ...string) func(string) bool {
		return func(p string) bool {
			for _, f := range files {
				if f == p {
					return true
				}
			}
			return false
		}
	}
	for _, c := range []struct {
		name      string
		goos      string
		look      func(string) (string, error)
		exists    func(string) bool
		want      string
		fromCache bool
	}{
		{"on the PATH", "linux", onPath, has(), "/usr/bin/git", false},
		{"nowhere, not Windows", "linux", notOnPath, has(), "git", false},
		{"Git for Windows installed", "windows", notOnPath, has(installed, cached), installed, false},
		{"only a tool's cache", "windows", notOnPath, has(cached), cached, true},
		{"nowhere on Windows", "windows", notOnPath, has(), "git", false},
	} {
		got, fromCache := findGit(c.goos, c.look, env, home, c.exists, glob)
		if got != c.want || fromCache != c.fromCache {
			t.Errorf("%s: %q cache=%v, want %q cache=%v", c.name, got, fromCache, c.want, c.fromCache)
		}
	}
}
