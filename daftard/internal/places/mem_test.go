// Part of place_responder. Licensed under AGPL-3.0.
package places

import (
	"os"
	"runtime"
	"runtime/pprof"
	"testing"
)

// What an index of the shipped bundle keeps in memory once it is built. The production host
// has one core and 7.8 GiB shared with Odoo and Postgres, and during a reload two indexes
// are alive at once -- so this number is a budget, not a curiosity.
func TestIndexMemory(t *testing.T) {
	if testing.Short() {
		t.Skip("reads the whole bundle")
	}
	if shippedBundle == "" {
		t.Skip(errNoBundle)
	}
	var before, after runtime.MemStats
	runtime.GC()
	runtime.ReadMemStats(&before)
	d, err := LoadBundle([]string{shippedBundle})
	if err != nil {
		t.Skip(err)
	}
	ix := BuildIndex(d, "", 1)
	d = nil
	runtime.GC()
	runtime.ReadMemStats(&after)
	live := float64(after.HeapAlloc-before.HeapAlloc) / (1 << 20)
	t.Logf("live heap after build: %.1f MiB (%d places, %d texts, %d words), build %s",
		live, len(ix.docs), len(ix.texts), len(ix.vocab), ix.BuildTime)
	if path := os.Getenv("PLACES_HEAP_PROFILE"); path != "" {
		f, _ := os.Create(path)
		pprof.WriteHeapProfile(f)
		f.Close()
	}
	if live > 160 {
		t.Errorf("an index of %.0f MiB is over the 160 MiB budget", live)
	}
	runtime.KeepAlive(ix)
}
