// Package syncer keeps a garden in step with its hub and runs its exchange rounds: the loop a garden's own
// dashboard used to run (dashboard/server.py Syncer), now daftard's (design §5). Each step is the
// garden's own dashboard/sync.py and exchange/exchange.py, through its worker: every few minutes, soon after a save,
// and at once when asked. A step that brings new code restarts the worker, so it reads with that code. What a step and
// a round write on their own — a merge with no conflict, a proposal a standing consent takes — is the garden hub's:
// both are asked with the hub's signing (Params), and with none where there is no hub to sign.
package syncer

import (
	"encoding/json"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/state"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// Worker is the garden's worker as the loop asks it (internal/worker.Worker).
type Worker interface {
	Call(method string, params any, timeout time.Duration) (json.RawMessage, error)
	Restart()
}

// Syncer is one garden's loop.
type Syncer struct {
	w        Worker
	name     string // the garden's, for the log
	every    time.Duration
	exchange bool
	hub      bool // a garden with no hub has only its exchange rounds
	wake     chan time.Duration
	mu       sync.Mutex
	last     map[string]any
	round    map[string]any
	// After runs after each step, with its state and whether the step brought new code: what travels by the hub beside
	// the garden (a person's labels), what waits, and the gardens served by this garden's code
	After func(state string, newCode bool)
	// Params are what each step and each exchange round are asked with: the bean of this machine's hub of the garden
	// and the hub's signing (internal/hubkey); nil, a step that merges nothing of its own and a round written as before
	Params func() map[string]any
}

// New prepares the loop; Run starts it.
func New(w *worker.Worker, every time.Duration, exchange, hub bool) *Syncer {
	return newSyncer(w, w.Garden.Name, every, exchange, hub)
}

func newSyncer(w Worker, name string, every time.Duration, exchange, hub bool) *Syncer {
	return &Syncer{w: w, name: name, every: every, exchange: exchange, hub: hub, wake: make(chan time.Duration, 1),
		last: map[string]any{"state": "waiting"}}
}

// Wake asks for a step: at once, or in twenty seconds (after a save, so several saves go up together).
func (s *Syncer) Wake(now bool) {
	d := 20 * time.Second
	if now {
		d = 0
	}
	select {
	case s.wake <- d:
	default:
	}
}

// Last is the last step's result, for the handplace.
func (s *Syncer) Last() map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	out := map[string]any{}
	for k, v := range s.last {
		out[k] = v
	}
	return out
}

// Round is the last exchange round's result.
func (s *Syncer) Round() map[string]any {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.round
}

// Run steps until stop is closed.
func (s *Syncer) Run(stop <-chan struct{}) {
	timer := time.NewTimer(5 * time.Second)
	for {
		select {
		case <-stop:
			return
		case d := <-s.wake:
			if !timer.Stop() {
				select {
				case <-timer.C:
				default:
				}
			}
			timer.Reset(d)
			continue
		case <-timer.C:
		}
		timer.Reset(s.step())
	}
}

// step is one step with the hub and, where it leaves the garden clean, one exchange round; it returns when the next
// is due. Both are asked with the same Params: what either writes on its own is the hub's.
func (s *Syncer) step() time.Duration {
	log := state.Logger()
	next := s.every
	var params map[string]any
	if s.Params != nil {
		params = s.Params()
	}
	result := map[string]any{"state": "off"}
	if s.hub {
		raw, err := s.w.Call("sync_step", params, 10*time.Minute)
		if err != nil {
			result = map[string]any{"state": "error", "why": err.Error()}
		} else if json.Unmarshal(raw, &result) != nil {
			result = map[string]any{"state": "error", "why": "unreadable answer"}
		}
	}
	if result["state"] == "busy" {
		next = 30 * time.Second
	}
	result["at"] = time.Now().Format("15:04")
	s.mu.Lock()
	s.last = result
	s.mu.Unlock()
	if s.hub {
		log.Printf("[%s] sync: %v", s.name, result)
	}
	if result["restart"] == true { // the hub brought new code: the worker reads with it from now on
		s.w.Restart()
	}
	if st, _ := result["state"].(string); s.exchange && st != "dirty" && st != "busy" && st != "diverged" && st != "error" {
		raw, err := s.w.Call("exchange_round", params, 15*time.Minute)
		round := map[string]any{}
		if err != nil {
			round = map[string]any{"state": "error", "why": err.Error()}
		} else {
			_ = json.Unmarshal(raw, &round)
		}
		s.mu.Lock()
		s.round = round
		s.mu.Unlock()
		if round["state"] != "off" {
			log.Printf("[%s] exchange: %v", s.name, round)
		}
	}
	if s.After != nil {
		st, _ := result["state"].(string)
		s.After(st, result["restart"] == true)
	}
	return next
}
