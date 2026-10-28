// Package state is where daftard keeps what is the machine's and not a garden's: its settings, its access key, its
// log and the details of guided errors. None of it is in git, and none of it travels with a garden.
package state

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"time"
)

// Dir is the machine's state folder: %LOCALAPPDATA%\Daftar on Windows, $XDG_STATE_HOME/daftar (or
// ~/.local/state/daftar) elsewhere. It is made, private to the user, on first use.
func Dir() string {
	if override := os.Getenv("DAFTARD_STATE"); override != "" { // a test, or a second daftard beside the first
		return filepath.Clean(override)
	}
	if runtime.GOOS == "windows" {
		return filepath.Join(os.Getenv("LOCALAPPDATA"), "Daftar")
	}
	base := os.Getenv("XDG_STATE_HOME")
	if base == "" {
		h, _ := os.UserHomeDir()
		base = filepath.Join(h, ".local", "state")
	}
	return filepath.Join(base, "daftar")
}

// Ensure makes the state folder, readable by the user alone.
func Ensure() (string, error) {
	d := Dir()
	if err := os.MkdirAll(d, 0o700); err != nil {
		return "", err
	}
	// tightened on every start, not only when first made: a folder or a key made looser since is closed again
	// (security audit 2026-10-10, 2.11)
	_ = os.Chmod(d, 0o700)
	_ = os.Chmod(filepath.Join(d, "key"), 0o600)
	return d, nil
}

// Token is the machine's access key: made once, 32 random bytes, kept in a file only the user can read. `daftard open`
// (the desktop icon) sends it in a header for a one-time code that opens the page, and the command line sends it in
// that header; it never goes in a URL or a cookie.
func Token() (string, error) {
	d, err := Ensure()
	if err != nil {
		return "", err
	}
	p := filepath.Join(d, "key")
	if b, err := os.ReadFile(p); err == nil && len(strings.TrimSpace(string(b))) >= 32 {
		return strings.TrimSpace(string(b)), nil
	}
	return newSecret(p)
}

func newSecret(p string) (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	s := hex.EncodeToString(b)
	if err := os.WriteFile(p, []byte(s+"\n"), 0o600); err != nil {
		return "", err
	}
	return s, nil
}

// Random is a fresh random hex string of n bytes (a CSRF token, an error's reference).
func Random(n int) string {
	b := make([]byte, n)
	if _, err := rand.Read(b); err != nil {
		panic(err)
	}
	return hex.EncodeToString(b)
}

// Log is daftard's own log, daftard.log in the state folder, cut over at 5 MB to daftard.log.1.
type Log struct {
	mu   sync.Mutex
	path string
}

var log *Log

// Logger returns the machine's log, made on first use.
// LogTo names the file this process logs to, in the state folder: a garden's own daemon keeps its own
// (garden-<name>.log), beside the machine's daftard.log. Called before anything is logged.
func LogTo(file string) {
	d, _ := Ensure()
	log = &Log{path: filepath.Join(d, file)}
}

func Logger() *Log {
	if log == nil {
		d, _ := Ensure()
		log = &Log{path: filepath.Join(d, "daftard.log")}
	}
	return log
}

// Printf writes one line, with the moment, to the log.
func (l *Log) Printf(format string, args ...any) {
	l.mu.Lock()
	defer l.mu.Unlock()
	if fi, err := os.Stat(l.path); err == nil && fi.Size() > 5<<20 {
		_ = os.Rename(l.path, l.path+".1")
	}
	f, err := os.OpenFile(l.path, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
	if err != nil {
		return
	}
	defer f.Close()
	fmt.Fprintf(f, "%s %s\n", time.Now().Format("2006-01-02 15:04:05"), fmt.Sprintf(format, args...))
}

// Writer is the log as an io.Writer, for what a child process prints.
func (l *Log) Writer(prefix string) io.Writer { return &prefixed{l, prefix} }

type prefixed struct {
	l      *Log
	prefix string
}

func (p *prefixed) Write(b []byte) (int, error) {
	for _, line := range strings.Split(strings.TrimRight(string(b), "\n"), "\n") {
		if strings.TrimSpace(line) != "" {
			p.l.Printf("%s %s", p.prefix, line)
		}
	}
	return len(b), nil
}
