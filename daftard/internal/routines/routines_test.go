package routines

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// fake is a worker that answers each method with what the test set, and remembers what it was asked.
type fake struct {
	answers map[string]any
	calls   []string
	params  []map[string]any
}

func (f *fake) Call(method string, params any, _ time.Duration) (json.RawMessage, error) {
	f.calls = append(f.calls, method)
	p, _ := params.(map[string]any)
	f.params = append(f.params, p)
	a, ok := f.answers[method]
	if !ok {
		return nil, fmt.Errorf("no answer for %s", method)
	}
	return json.Marshal(a)
}

func runner(t *testing.T, f *fake, logs *[]string) *Runner {
	return &Runner{W: f, Garden: "g", State: t.TempDir(), ProbeEvery: time.Second, SeriesDays: 14,
		Log:    func(format string, a ...any) { *logs = append(*logs, fmt.Sprintf(format, a...)) },
		Params: func() map[string]any { return map[string]any{"by": "box-hub"} }}
}

func TestTickLogsEachRoutineItActedOnAndSignsAsTheHub(t *testing.T) {
	var logs []string
	after := 0
	f := &fake{answers: map[string]any{"routines_tick": map[string]any{"state": "ran", "done": []any{
		map[string]any{"routine": "server-a#restart-window", "did": "started", "course": "restart-window-20261018-0545", "stopped": "waits"},
		map[string]any{"routine": "server-b#restart-window", "did": "skipped", "course": "restart-window-20261018-0545", "why": "window-passed"},
	}}}}
	r := runner(t, f, &logs)
	r.After = func() { after++ }
	lines := r.Tick()
	if len(lines) != 2 || !strings.Contains(lines[0], "server-a#restart-window: started restart-window-20261018-0545 → waits") ||
		!strings.Contains(lines[1], "skipped") || !strings.Contains(lines[1], "(window-passed)") {
		t.Fatalf("one log line per routine acted on, saying what was done and where it stopped: %q", lines)
	}
	if f.params[0]["by"] != "box-hub" {
		t.Fatalf("the tick is asked with the hub's signing, as the syncer's merge is: %v", f.params[0])
	}
	if after != 1 {
		t.Fatalf("after a tick that acted, the lead watcher looks again: %d", after)
	}
	if got := r.Probes()["tick"].(map[string]any)["state"]; got != "ran" {
		t.Fatalf("the last tick is kept for the page: %v", got)
	}
}

func TestTickOfAGardenWithoutRoutinesSaysNothing(t *testing.T) {
	var logs []string
	f := &fake{answers: map[string]any{"routines_tick": map[string]any{"state": "off", "why": "this garden's release has no bin/routines.py"}}}
	r := runner(t, f, &logs)
	if lines := r.Tick(); len(lines) != 0 || len(logs) != 0 {
		t.Fatalf("an older release is no failure: nothing is logged, %q %q", lines, logs)
	}
}

func TestProbeRoundKeepsTheLatestAndABoundedSeries(t *testing.T) {
	var logs []string
	now := time.Date(2026, 10, 11, 6, 0, 0, 0, time.UTC)
	reading := func(at string, n string) map[string]any {
		return map[string]any{"key": "usb.present", "being": "usb-cold", "property": "number", "at": at,
			"value": map[string]any{"count": n, "unit": "{item}"}, "quality": "ok"}
	}
	f := &fake{answers: map[string]any{"probe_round": map[string]any{
		"tools": map[string]any{"copyctl": map[string]any{"tool": "copyctl", "readings": []any{reading(now.Format(time.RFC3339), "1")}}},
		"read":  []any{"copyctl"}, "why": map[string]any{"lensctl": "not on this machine"}}}}
	r := runner(t, f, &logs)
	r.Now = func() time.Time { return now }
	series := filepath.Join(r.dir(), "series", "copyctl--usb.present.jsonl")
	if err := os.MkdirAll(filepath.Dir(series), 0o700); err != nil {
		t.Fatal(err)
	}
	old, _ := json.Marshal(map[string]any{"at": now.AddDate(0, 0, -20).Format(time.RFC3339), "value": map[string]any{"count": "0"}})
	recent, _ := json.Marshal(map[string]any{"at": now.AddDate(0, 0, -2).Format(time.RFC3339), "value": map[string]any{"count": "0"}})
	if err := os.WriteFile(series, []byte(string(old)+"\n"+string(recent)+"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if n := r.ProbeRound(); n != 1 {
		t.Fatalf("one reading read: %d", n)
	}
	if f.params[0]["dir"] != r.dir() || f.params[0]["every"] != 1 {
		t.Fatalf("the round is asked where to keep its readings and how often it may probe: %v", f.params[0])
	}
	b, err := os.ReadFile(filepath.Join(r.dir(), "copyctl.json"))
	if err != nil || !strings.Contains(string(b), `"usb.present"`) {
		t.Fatalf("the tool's latest document is kept: %s %v", b, err)
	}
	s, _ := os.ReadFile(series)
	ln := strings.Split(strings.TrimSpace(string(s)), "\n")
	if len(ln) != 2 || strings.Contains(string(s), now.AddDate(0, 0, -20).Format("2006-01-02")) {
		t.Fatalf("the series keeps 14 days and gains the new reading: %q", ln)
	}
	if !strings.Contains(strings.Join(logs, "\n"), "probe lensctl: not on this machine") {
		t.Fatalf("a tool the round could not read is said in the log: %q", logs)
	}
	p := r.Probes()["tools"].(map[string]any)
	if _, ok := p["copyctl"]; !ok {
		t.Fatalf("/api/probe serves the latest of each tool: %v", p)
	}
}

func TestCrossReadsTheKeptReadingsAndLogsWhatCrossed(t *testing.T) {
	var logs []string
	f := &fake{answers: map[string]any{
		"probe_round": map[string]any{"tools": map[string]any{"copyctl": map[string]any{"readings": []any{
			map[string]any{"key": "nas.fill", "at": time.Now().Format(time.RFC3339), "value": map[string]any{"count": "86", "unit": "%"}}}}},
			"read": []any{"copyctl"}},
		"routines_cross": map[string]any{"done": []any{
			map[string]any{"bean": "nas-a", "need": "below-gate", "holds": false},
			map[string]any{"bean": "nas-a", "walk": "copy-prune", "stopped": "waits"}}}}}
	r := runner(t, f, &logs)
	if n := r.ProbeRound(); n != 1 {
		t.Fatalf("a reading: %d", n)
	}
	lines := r.Cross()
	files, _ := f.params[1]["readings"].([]string)
	if len(files) != 1 || !strings.HasSuffix(files[0], "copyctl.json") {
		t.Fatalf("the crossing reads the readings kept, never the device: %v", f.params[1])
	}
	if len(lines) != 2 || !strings.Contains(lines[0], "nas-a below-gate: does not hold") || !strings.Contains(lines[1], "proposes copy-prune (waits)") {
		t.Fatalf("each crossing is a log line, and the walk it proposed: %q", lines)
	}
}

func TestProbesAfterARestartAreThoseKept(t *testing.T) {
	var logs []string
	r := runner(t, &fake{answers: map[string]any{}}, &logs)
	if err := os.MkdirAll(r.dir(), 0o700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(r.dir(), "powerctl.json"), []byte(`{"tool":"powerctl","readings":[]}`), 0o600); err != nil {
		t.Fatal(err)
	}
	if _, ok := r.Probes()["tools"].(map[string]any)["powerctl"]; !ok {
		t.Fatalf("a restarted daftard serves what the last run kept until its first round")
	}
}
