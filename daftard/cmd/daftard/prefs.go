package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/private"
	"github.com/0mit/daftar/daftard/internal/web"
	"github.com/0mit/daftar/daftard/internal/worker"
	"github.com/0mit/daftar/daftard/python"
)

// A READER'S WAY OF READING, KEPT OR CARRIED AS A BEAN (the view profile's form `reader_preferences`):
//
//	daftard prefs export <garden> <person> [--out FILE]   what this machine keeps of them, as a bean
//	daftard prefs import FILE [<garden>]                  a bean read back into what this machine keeps
//
// This machine's file (readers.json) stays the source. The bean is written and read by the garden's own release
// (view_prefs.to_bean, from_bean, through its worker), which also checks the tag; daftard reads nothing of it itself.
// Both ways lose nothing. A bean set in another garden is refused for this one; a running daftard reads the file on
// each request, so what is imported holds at once.
func prefsCmd(args []string) error {
	const use = "daftard prefs export <garden> <person> [--out FILE] | daftard prefs import FILE [<garden>]"
	if len(args) < 2 {
		return errors.New(use)
	}
	c, err := config.Load()
	if err != nil {
		return err
	}
	switch args[0] {
	case "export":
		if len(args) < 3 {
			return errors.New(use)
		}
		g, err := gardenNamed(c, args[1])
		if err != nil {
			return err
		}
		out := ""
		if len(args) >= 5 && args[3] == "--out" {
			out = args[4]
		}
		var got struct {
			Bean string `json:"bean"`
		}
		if err := prefsAsk(g, "prefs_bean", map[string]any{"prefs": web.ReaderPrefs(g.Name, args[2]), "reader": args[2]}, &got); err != nil {
			return err
		}
		if out == "" {
			fmt.Print(got.Bean)
			return nil
		}
		if err := os.MkdirAll(filepath.Dir(out), 0o700); err != nil {
			return err
		}
		// the person's alone to read, the platform's way (its mode; on Windows its access list), over any copy before
		if err := private.WriteFile(out, []byte(got.Bean)); err != nil {
			return err
		}
		fmt.Printf("daftard: %s's way of reading in %s written to %s\n", args[2], g.Name, out)
		if err := private.Check(out); err != nil { // a drive that keeps no one's file apart (FAT): said, not refused
			fmt.Fprintf(os.Stderr, "daftard: note: others may read it there: %v\n", err)
		}
		return nil
	case "import":
		text, err := os.ReadFile(args[1])
		if err != nil {
			return err
		}
		gardens := c.Gardens
		if len(args) >= 3 {
			g, err := gardenNamed(c, args[2])
			if err != nil {
				return err
			}
			gardens = []config.Garden{g}
		}
		type read struct {
			Bean   string            `json:"bean"`
			Reader string            `json:"reader"`
			Garden string            `json:"garden"`
			Prefs  map[string]string `json:"prefs"`
			Here   string            `json:"here"`
		}
		var hit *read
		var into config.Garden
		for _, g := range gardens {
			var got read
			if err := prefsAsk(g, "prefs_from_bean", map[string]any{"text": string(text)}, &got); err != nil {
				return err
			}
			if got.Garden != "" && got.Garden != got.Here {
				if len(gardens) == 1 {
					return fmt.Errorf("%s: these preferences were set in the garden %s, not in %s (%s)", args[1], got.Garden, g.Name, got.Here)
				}
				continue
			}
			if got.Garden == "" && len(gardens) > 1 {
				return fmt.Errorf("%s names no garden: say which (daftard prefs import %s <garden>)", args[1], args[1])
			}
			hit, into = &got, g
			break
		}
		if hit == nil {
			return fmt.Errorf("%s: no garden here is the one these preferences were set in", args[1])
		}
		if err := web.SetReaderPrefs(into.Name, hit.Reader, hit.Prefs); err != nil {
			return err
		}
		keys := make([]string, 0, len(hit.Prefs))
		for k, v := range hit.Prefs {
			keys = append(keys, k+" "+v)
		}
		sort.Strings(keys)
		said := strings.Join(keys, ", ")
		if said == "" {
			said = "their language's own"
		}
		fmt.Printf("daftard: %s's way of reading in %s read back from %s: %s\n", hit.Reader, into.Name, args[1], said)
		return nil
	}
	return errors.New(use)
}

func gardenNamed(c *config.Config, name string) (config.Garden, error) {
	for _, g := range c.Gardens {
		if g.Name == name {
			return g, nil
		}
	}
	return config.Garden{}, fmt.Errorf("no garden named %q here", name)
}

// prefsAsk asks the garden's own release, through a worker of this command's own, and reads its answer into out.
func prefsAsk(g config.Garden, method string, params map[string]any, out any) error {
	script, done, err := prefsScript()
	if err != nil {
		return err
	}
	defer done()
	w := worker.New(g, script)
	defer w.Close()
	raw, err := w.Call(method, params, 2*time.Minute)
	if err != nil {
		var we *worker.Error
		if errors.As(err, &we) {
			return fmt.Errorf("%s: %s", g.Name, we.Message)
		}
		return err
	}
	return json.Unmarshal(raw, out)
}

// prefsScript is the worker this command asks, written to a folder of its own (never the running daftard's), and how
// to take it away; a test stands in its own.
var prefsScript = func() (string, func(), error) {
	dir, err := os.MkdirTemp("", "daftard-prefs-")
	if err != nil {
		return "", nil, err
	}
	done := func() { _ = os.RemoveAll(dir) }
	script := filepath.Join(dir, "garden_worker.py")
	if err := os.WriteFile(script, python.Worker, 0o600); err != nil {
		done()
		return "", nil, err
	}
	for name, text := range python.Modules {
		if err := os.WriteFile(filepath.Join(dir, name), text, 0o600); err != nil {
			done()
			return "", nil, err
		}
	}
	return script, done, nil
}
