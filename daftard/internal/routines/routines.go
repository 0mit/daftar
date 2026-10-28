// Package routines runs a garden's routines on this machine, and keeps its tools' readings (design §14; CONTRACT §3,
// §5, §8). It decides nothing about the garden: what runs, when, as whom, what it waits on and what proves it are the
// garden's statements, read by the garden's own bin/routines.py and run by its own bin/act.py, through the worker.
// daftard is the clock and the log:
//
//   - each minute, on the minute, the worker is asked to `routines_tick` (bin/routines.py tick): a routine whose window
//     is open starts, one waiting on its interlocks is read again, one whose window closed while it waited is skipped;
//     each routine acted on is one line in daftard's log. Its commits are written by this machine's hub of the garden,
//     signed with the hub's key (Params, as the syncer's merges are; the machine's own key where the garden names no
//     hub), its moves `by` the host whose engine ran them;
//   - on each tool's cadence (its `probe --list` catalogue, never faster than ProbeEvery), the worker is asked to
//     `probe_round`: each tool this machine holds is probed, its latest readings kept under <state>/probes/ and each
//     reading appended to a series kept no longer than SeriesDays — the bounded history the handplace and the
//     thresholds read; long history stays where it is kept today (Zabbix, Prometheus);
//   - after a round that read something, the worker is asked to `routines_cross` against those readings: a need of a
//     being that stops holding writes its crossing once (a health lead), and its repair when it holds again.
//
// A garden takes part only where its settings say `routines: true`; a routine runs here only where the garden grants
// this machine `enact` of its walk. Nothing here runs a tool by itself.
package routines

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

// Caller is the worker's one door: a method, its parameters, an answer (internal/worker.Worker).
type Caller interface {
	Call(method string, params any, timeout time.Duration) (json.RawMessage, error)
}

// Runner is one garden's routines on this machine.
type Runner struct {
	W          Caller
	Garden     string                // the garden's short name, for the log
	State      string                // where its readings are kept: <state>/probes/<garden>/
	ProbeEvery time.Duration         // the fastest a tool is probed (30 s)
	SeriesDays int                   // how long a reading's series is kept (14)
	Log        func(string, ...any)  // daftard's log
	Params     func() map[string]any // the hub's signing, as the syncer's (nil: the worker's own identity)
	After      func()                // after a tick or a crossing wrote something: the lead watcher looks again
	Close      func()                // ends its worker when daftard stops (a call under way finishes first)
	Now        func() time.Time

	mu       sync.Mutex
	latest   map[string]any // the last probe round's documents, by tool
	lastTick map[string]any
}

func (r *Runner) now() time.Time {
	if r.Now != nil {
		return r.Now()
	}
	return time.Now()
}

func (r *Runner) dir() string { return filepath.Join(r.State, "probes", r.Garden) }

func (r *Runner) params(extra map[string]any) map[string]any {
	p := map[string]any{}
	if r.Params != nil {
		for k, v := range r.Params() {
			p[k] = v
		}
	}
	for k, v := range extra {
		p[k] = v
	}
	return p
}

// Tick asks the garden to run what is due now, and logs one line per routine it acted on. It returns those lines.
func (r *Runner) Tick() []string {
	raw, err := r.W.Call("routines_tick", r.params(nil), 50*time.Minute)
	if err != nil {
		r.Log("[%s] routines: %v", r.Garden, err)
		return nil
	}
	var got struct {
		State string           `json:"state"`
		Why   string           `json:"why"`
		Done  []map[string]any `json:"done"`
	}
	if json.Unmarshal(raw, &got) != nil {
		r.Log("[%s] routines: an answer the worker gave is no document", r.Garden)
		return nil
	}
	r.mu.Lock()
	r.lastTick = map[string]any{"at": r.now().Format(time.RFC3339), "state": got.State, "done": got.Done}
	r.mu.Unlock()
	if got.State == "off" {
		return nil
	}
	var lines []string
	for _, d := range got.Done {
		line := fmt.Sprintf("[%s] routine %v: %v", r.Garden, d["routine"], d["did"])
		if c, ok := d["course"].(string); ok && c != "" {
			line += " " + c
		}
		if s, ok := d["stopped"].(string); ok && s != "" {
			line += " → " + s
		}
		if w, ok := d["why"].(string); ok && w != "" {
			line += " (" + w + ")"
		}
		r.Log("%s", line)
		lines = append(lines, line)
	}
	if len(lines) > 0 && r.After != nil {
		r.After()
	}
	return lines
}

// ProbeRound asks the garden to probe each tool this machine holds that is due by its cadence, keeps the readings, and
// returns how many readings it got.
func (r *Runner) ProbeRound() int {
	if err := os.MkdirAll(r.dir(), 0o700); err != nil {
		r.Log("[%s] probes: %v", r.Garden, err)
		return 0
	}
	raw, err := r.W.Call("probe_round", r.params(map[string]any{"dir": r.dir(), "every": int(r.ProbeEvery.Seconds())}), 10*time.Minute)
	if err != nil {
		r.Log("[%s] probes: %v", r.Garden, err)
		return 0
	}
	var got struct {
		Tools map[string]map[string]any `json:"tools"`
		Read  []string                  `json:"read"`
		Why   map[string]string         `json:"why"`
	}
	if json.Unmarshal(raw, &got) != nil {
		return 0
	}
	n := 0
	for _, tool := range got.Read {
		doc := got.Tools[tool]
		if doc == nil {
			continue
		}
		rs, _ := doc["readings"].([]any)
		n += len(rs)
		r.keep(tool, doc, rs)
	}
	for tool, why := range got.Why {
		r.Log("[%s] probe %s: %s", r.Garden, tool, why)
	}
	r.mu.Lock()
	r.latest = map[string]any{}
	for tool, doc := range got.Tools {
		r.latest[tool] = doc
	}
	r.mu.Unlock()
	return n
}

// keep writes a tool's latest document and appends each reading to its key's series, dropping what is older than
// SeriesDays: the bounded history (CONTRACT §8.5).
func (r *Runner) keep(tool string, doc map[string]any, rs []any) {
	b, _ := json.Marshal(doc)
	tmp := filepath.Join(r.dir(), "."+tool+".json.tmp")
	if os.WriteFile(tmp, b, 0o600) == nil {
		_ = os.Rename(tmp, filepath.Join(r.dir(), tool+".json"))
	}
	sdir := filepath.Join(r.dir(), "series")
	if os.MkdirAll(sdir, 0o700) != nil {
		return
	}
	cut := r.now().AddDate(0, 0, -r.days())
	for _, x := range rs {
		rd, _ := x.(map[string]any)
		key, _ := rd["key"].(string)
		if key == "" || strings.ContainsAny(key, "/\\") || strings.HasPrefix(key, ".") {
			continue
		}
		p := filepath.Join(sdir, tool+"--"+key+".jsonl")
		line, _ := json.Marshal(map[string]any{"at": rd["at"], "value": rd["value"], "quality": rd["quality"], "being": rd["being"]})
		trim(p, cut)
		f, err := os.OpenFile(p, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
		if err != nil {
			continue
		}
		_, _ = f.Write(append(line, '\n'))
		_ = f.Close()
	}
}

func (r *Runner) days() int {
	if r.SeriesDays > 0 {
		return r.SeriesDays
	}
	return 14
}

// trim drops a series' lines older than cut, once its first line is: the file is read and written again only then.
func trim(path string, cut time.Time) {
	b, err := os.ReadFile(path)
	if err != nil || len(b) == 0 {
		return
	}
	first := strings.SplitN(string(b), "\n", 2)[0]
	if !older(first, cut) {
		return
	}
	var keep []string
	for _, ln := range strings.Split(strings.TrimRight(string(b), "\n"), "\n") {
		if ln != "" && !older(ln, cut) {
			keep = append(keep, ln)
		}
	}
	out := strings.Join(keep, "\n")
	if out != "" {
		out += "\n"
	}
	tmp := path + ".tmp"
	if os.WriteFile(tmp, []byte(out), 0o600) == nil {
		_ = os.Rename(tmp, path)
	}
}

func older(line string, cut time.Time) bool {
	var x struct {
		At string `json:"at"`
	}
	if json.Unmarshal([]byte(line), &x) != nil {
		return true // a line that says no moment is not kept
	}
	t, err := time.Parse(time.RFC3339, x.At)
	return err != nil || t.Before(cut)
}

// Cross asks the garden to read its beings' needs against the readings kept, and write what crossed.
func (r *Runner) Cross() []string {
	files, _ := filepath.Glob(filepath.Join(r.dir(), "*.json"))
	if len(files) == 0 {
		return nil
	}
	sort.Strings(files)
	raw, err := r.W.Call("routines_cross", r.params(map[string]any{"readings": files}), 30*time.Minute)
	if err != nil {
		r.Log("[%s] crossings: %v", r.Garden, err)
		return nil
	}
	var got struct {
		Done []map[string]any `json:"done"`
	}
	_ = json.Unmarshal(raw, &got)
	var lines []string
	for _, d := range got.Done {
		state := "does not hold"
		if h, _ := d["holds"].(bool); h {
			state = "holds again"
		}
		if w, ok := d["walk"].(string); ok && w != "" {
			state = fmt.Sprintf("proposes %s (%v)", w, d["stopped"])
		}
		line := fmt.Sprintf("[%s] crossing %v %v: %s", r.Garden, d["bean"], d["need"], state)
		r.Log("%s", line)
		lines = append(lines, line)
	}
	if len(lines) > 0 && r.After != nil {
		r.After()
	}
	return lines
}

// Probes is what /api/probe serves: the latest document of each tool, and the last tick.
func (r *Runner) Probes() map[string]any {
	r.mu.Lock()
	defer r.mu.Unlock()
	tools := map[string]any{}
	for k, v := range r.latest {
		tools[k] = v
	}
	if len(tools) == 0 { // a restart: what the last run kept
		files, _ := filepath.Glob(filepath.Join(r.dir(), "*.json"))
		for _, f := range files {
			b, err := os.ReadFile(f)
			var doc map[string]any
			if err == nil && json.Unmarshal(b, &doc) == nil {
				tools[strings.TrimSuffix(filepath.Base(f), ".json")] = doc
			}
		}
	}
	return map[string]any{"garden": r.Garden, "tools": tools, "tick": r.lastTick}
}

// Run ticks on each minute and probes on ProbeEvery, until stop is closed.
func (r *Runner) Run(stop <-chan struct{}) {
	every := r.ProbeEvery
	if every <= 0 {
		every = 30 * time.Second
	}
	probe := time.NewTicker(every)
	defer probe.Stop()
	next := r.now().Truncate(time.Minute).Add(time.Minute + 5*time.Second) // a little past the minute: the clock's
	tick := time.NewTimer(time.Until(next))
	defer tick.Stop()
	if r.ProbeRound() > 0 {
		r.Cross()
	}
	for {
		select {
		case <-stop:
			return
		case <-probe.C:
			if r.ProbeRound() > 0 {
				r.Cross()
			}
		case <-tick.C:
			r.Tick()
			next = r.now().Truncate(time.Minute).Add(time.Minute + 5*time.Second)
			tick.Reset(time.Until(next))
		}
	}
}
