// Package testpython finds the Python a test starts a garden's worker or a stand-in with: the first `python3`, else
// `python`, in the folders of PATH, that runs. On Windows the first `python3` on PATH is often the Microsoft Store's
// stand-in (…\AppData\Local\Microsoft\WindowsApps\python3.exe), which runs nothing and exits at once, so a worker a
// test starts with it ends before it answers; a candidate that does not run `-c pass` is passed over, and a test skips
// only where none runs. For tests only: daftard runs the Python its configuration names (`install --python`).
package testpython

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

var (
	once  sync.Once
	found string
	why   error
)

// Path is the Python this machine's tests run with, found once; an error says why there is none, for a test to skip.
func Path() (string, error) {
	once.Do(func() { found, why = find(os.Getenv("PATH")) })
	return found, why
}

// find is the first `python3`, else `python`, in the folders of pathList (only those named in full) that runs.
func find(pathList string) (string, error) {
	var tried []string
	for _, name := range []string{"python3", "python"} {
		for _, dir := range filepath.SplitList(pathList) {
			if !filepath.IsAbs(dir) {
				continue
			}
			p, err := exec.LookPath(filepath.Join(dir, name))
			if err != nil {
				continue
			}
			if runs(p) {
				return p, nil
			}
			tried = append(tried, p)
		}
	}
	if len(tried) == 0 {
		return "", errors.New("no python3 or python on PATH")
	}
	return "", fmt.Errorf("no python3 or python on PATH runs: %s", strings.Join(tried, ", "))
}

// runs says whether p runs a program at all: `-c pass`, within half a minute.
func runs(p string) bool {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	return exec.CommandContext(ctx, p, "-c", "pass").Run() == nil
}
