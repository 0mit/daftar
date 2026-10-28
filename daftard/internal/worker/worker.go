// Package worker runs a garden's Python worker (python/garden_worker.py) and calls it: daftard's read and write path
// into a garden until its own index reads gardens natively. One call at a time, as the garden's model takes one lock;
// a worker that dies or hangs is restarted, and one is restarted when a sync brings new code into the garden.
package worker

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"os/exec"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/proc"
	"github.com/0mit/daftar/daftard/internal/state"
)

// Error is what the worker says when a call did not go ahead: Message may be shown to the person, Diagnostic is the
// whole of it and is kept with a guided error's reference.
type Error struct {
	Status     int    `json:"status"`
	Message    string `json:"message"`
	Diagnostic string `json:"diagnostic"`
	Kind       string `json:"kind"` // refused (the garden's model or gate said no) or failed (something broke)
}

func (e *Error) Error() string { return fmt.Sprintf("%d %s: %s", e.Status, e.Kind, e.Message) }

type answer struct {
	ID       int             `json:"id"`
	OK       bool            `json:"ok"`
	Result   json.RawMessage `json:"result"`
	Error    *Error          `json:"error"`
	Register json.RawMessage `json:"register"` // what the register's routes did in the call (python/register.py)
}

// Worker is one garden's worker process.
type Worker struct {
	Garden config.Garden
	// Noted is handed what the register's routes did in a call, where the worker's answer says (internal/register
	// keeps their health by it); nil: it is not asked
	Noted  func(json.RawMessage)
	script string
	mu     sync.Mutex
	cmd    *exec.Cmd
	in     io.WriteCloser
	lines  chan []byte
	next   int
	log    *state.Log
}

// New prepares a worker for the garden; it starts on its first call.
func New(g config.Garden, script string) *Worker {
	return &Worker{Garden: g, script: script, log: state.Logger()}
}

func (w *Worker) start() error {
	c := proc.Command(w.Garden.Python, "-X", "utf8", w.script)
	c.Dir = w.Garden.Path
	c.Env = append(os.Environ(), "PYTHONUTF8=1", "PYTHONIOENCODING=utf-8", "DAFTAR_KIND="+w.Garden.Kind,
		"DAFTAR_TOOLS="+w.Garden.Tools, "DAFTAR_EXCHANGE_DIR="+w.Garden.ExchangeDir)
	if r := w.Garden.Register; r != nil { // which register, and the file its key is in: never the key itself; the routes
		// to it are handed with each call, as they stand then (internal/register)
		b, _ := json.Marshal(map[string]string{"series": r.Series, "url": r.URL, "db": r.DB, "bean": r.Bean,
			"key_file": r.KeyFile(w.Garden.Name)})
		c.Env = append(c.Env, "DAFTAR_REGISTER="+string(b))
	}
	c.Stderr = w.log.Writer("[" + w.Garden.Name + " worker]")
	in, err := c.StdinPipe()
	if err != nil {
		return err
	}
	out, err := c.StdoutPipe()
	if err != nil {
		return err
	}
	if err := c.Start(); err != nil {
		return err
	}
	lines := make(chan []byte, 4)
	go func() {
		r := bufio.NewReaderSize(out, 1<<20)
		for {
			b, err := r.ReadBytes('\n')
			if len(b) > 0 {
				lines <- b
			}
			if err != nil {
				close(lines)
				return
			}
		}
	}()
	w.cmd, w.in, w.lines = c, in, lines
	w.log.Printf("[%s] worker started (pid %d) in %s", w.Garden.Name, c.Process.Pid, w.Garden.Path)
	return nil
}

func (w *Worker) stop() {
	if w.cmd != nil && w.cmd.Process != nil {
		_ = w.in.Close()
		done := make(chan struct{})
		go func() { _ = w.cmd.Wait(); close(done) }()
		select {
		case <-done:
		case <-time.After(5 * time.Second):
			_ = w.cmd.Process.Kill()
		}
	}
	w.cmd, w.in, w.lines = nil, nil, nil
}

// Restart ends the worker; the next call starts a new one, on whatever code the garden now holds.
func (w *Worker) Restart() {
	w.mu.Lock()
	defer w.mu.Unlock()
	w.stop()
	w.log.Printf("[%s] worker restarted", w.Garden.Name)
}

// Close ends the worker for good.
func (w *Worker) Close() { w.Restart() }

// Call sends one request and waits for its answer, up to timeout. The answer's result is returned as raw JSON; a
// refusal or failure the worker reports is an *Error.
func (w *Worker) Call(method string, params any, timeout time.Duration) (json.RawMessage, error) {
	w.mu.Lock()
	defer w.mu.Unlock()
	if w.cmd == nil {
		if err := w.start(); err != nil {
			return nil, &Error{Status: 503, Kind: "failed", Message: "the garden's worker did not start", Diagnostic: err.Error()}
		}
	}
	w.next++
	req, err := json.Marshal(map[string]any{"id": w.next, "method": method, "params": params})
	if err != nil {
		return nil, err
	}
	if _, err := w.in.Write(append(req, '\n')); err != nil {
		w.stop()
		return nil, &Error{Status: 503, Kind: "failed", Message: "the garden's worker stopped", Diagnostic: err.Error()}
	}
	deadline := time.After(timeout)
	for {
		select {
		case b, ok := <-w.lines:
			if !ok {
				w.stop()
				return nil, &Error{Status: 503, Kind: "failed", Message: "the garden's worker ended", Diagnostic: "its output closed during " + method}
			}
			var a answer
			if err := json.Unmarshal(b, &a); err != nil || a.ID != w.next {
				continue // a stray line: the worker's protocol stream carries nothing else, so it is skipped
			}
			if len(a.Register) > 0 && w.Noted != nil {
				w.Noted(a.Register)
			}
			if !a.OK {
				if a.Error == nil {
					a.Error = &Error{Status: 500, Kind: "failed", Message: "no answer"}
				}
				return nil, a.Error
			}
			return a.Result, nil
		case <-deadline:
			w.stop() // a hung worker is ended; the next call starts a fresh one
			return nil, &Error{Status: 504, Kind: "failed", Message: "the garden did not answer in time",
				Diagnostic: fmt.Sprintf("%s took longer than %s; the worker was restarted", method, timeout)}
		}
	}
}

// IsError says whether err is a worker Error and returns it.
func IsError(err error) (*Error, bool) {
	var e *Error
	if errors.As(err, &e) {
		return e, true
	}
	return nil, false
}
