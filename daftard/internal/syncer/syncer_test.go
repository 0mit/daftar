package syncer

import (
	"encoding/json"
	"os"
	"testing"
	"time"
)

// The loop writes daftard's log (state.Logger): in a state folder of the test's own, never this account's.
func TestMain(m *testing.M) {
	dir, err := os.MkdirTemp("", "syncer-state-")
	if err != nil {
		panic(err)
	}
	os.Setenv("DAFTARD_STATE", dir)
	code := m.Run()
	os.RemoveAll(dir)
	os.Exit(code)
}

type call struct {
	method string
	params any
}

type fake struct {
	calls    []call
	answers  map[string]any
	restarts int
}

func (f *fake) Call(method string, params any, _ time.Duration) (json.RawMessage, error) {
	f.calls = append(f.calls, call{method, params})
	return json.Marshal(f.answers[method])
}

func (f *fake) Restart() { f.restarts++ }

func hub() map[string]any {
	return map[string]any{"by": "box-hub", "sign": map[string]string{"GIT_AUTHOR_NAME": "box-hub"}}
}

// WHAT THE LOOP WRITES ON ITS OWN IS THE HUB'S: a step's merge with no conflict and the exchange round after it — a
// proposal a standing consent takes — are both asked with the hub's bean and its signing, never the one with it and the
// other written by whatever identity the clone has.
func TestAStepAndItsExchangeRoundAreBothTheHubs(t *testing.T) {
	f := &fake{answers: map[string]any{"sync_step": map[string]any{"state": "merged", "pulled": 2},
		"exchange_round": map[string]any{"state": "ran", "taken": []any{"p1"}}}}
	s := newSyncer(f, "shop", time.Minute, true, true)
	s.Params = hub
	if next := s.step(); next != time.Minute {
		t.Fatalf("the next step is due after the garden's interval: %v", next)
	}
	if len(f.calls) != 2 || f.calls[0].method != "sync_step" || f.calls[1].method != "exchange_round" {
		t.Fatalf("a step, then a round: %v", f.calls)
	}
	for _, c := range f.calls {
		p, _ := c.params.(map[string]any)
		if p["by"] != "box-hub" || p["sign"] == nil {
			t.Fatalf("%s is asked as the hub, with its signing: %v", c.method, c.params)
		}
	}
	if s.Round()["state"] != "ran" || s.Last()["state"] != "merged" {
		t.Fatalf("the step's and the round's results are kept for the handplace: %v %v", s.Last(), s.Round())
	}
}

// NO HUB, NOTHING SIGNED AS ONE: with no Params, a step merges nothing of its own (the worker takes fast-forwards
// only) and the round is asked as before; a step that leaves the garden apart from its peers runs no round.
func TestWithNoHubNothingIsSignedAsOne(t *testing.T) {
	f := &fake{answers: map[string]any{"sync_step": map[string]any{"state": "current"},
		"exchange_round": map[string]any{"state": "off"}}}
	s := newSyncer(f, "shop", time.Minute, true, true)
	s.step()
	unsigned := func(c call) bool { p, _ := c.params.(map[string]any); return len(p) == 0 }
	if len(f.calls) != 2 || !unsigned(f.calls[0]) || !unsigned(f.calls[1]) {
		t.Fatalf("with no hub, neither is asked with a signing: %v", f.calls)
	}
	f = &fake{answers: map[string]any{"sync_step": map[string]any{"state": "diverged"}}}
	s = newSyncer(f, "shop", time.Minute, true, true)
	s.Params = hub
	s.step()
	if len(f.calls) != 1 {
		t.Fatalf("a garden apart from its peers takes no proposal until a person merges: %v", f.calls)
	}
}

// A STEP THAT BRINGS NEW CODE restarts the worker, so it reads with that code; a busy clone is tried again soon.
func TestNewCodeRestartsTheWorkerAndABusyCloneIsTriedSoon(t *testing.T) {
	f := &fake{answers: map[string]any{"sync_step": map[string]any{"state": "pulled", "restart": true}}}
	s := newSyncer(f, "shop", time.Minute, false, true)
	s.step()
	if f.restarts != 1 {
		t.Fatalf("new code from the hub restarts the worker: %d", f.restarts)
	}
	f = &fake{answers: map[string]any{"sync_step": map[string]any{"state": "busy"}}}
	s = newSyncer(f, "shop", time.Minute, false, true)
	if next := s.step(); next != 30*time.Second {
		t.Fatalf("a save holding the clone: the next step in thirty seconds, %v", next)
	}
}
