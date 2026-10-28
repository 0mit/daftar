package passkey

import (
	"errors"
	"os"
	"path/filepath"
	"sync"
	"testing"

	"github.com/0mit/daftar/daftard/internal/private"
)

// THE SIGNATURE COUNTER (W3C Web Authentication §6.1.1): where the counter or the last one seen is not zero, it must
// grow, or the credential is answered by a copy; both zero is an authenticator that keeps none. What is kept outlives
// a restart, readable by this account alone; a file that cannot be read is begun again, and says so.
func TestCounts(t *testing.T) {
	path := filepath.Join(t.TempDir(), "passkey-counts.json")
	c := OpenCounts(path)
	a, b := []byte("credential a"), []byte("credential b")
	steps := []struct {
		id    []byte
		count uint32
		ok    bool
	}{
		{a, 0, true}, {a, 0, true}, // no counter kept by the authenticator: each sign-in goes
		{a, 3, true}, {a, 3, false}, {a, 2, false}, {a, 0, false}, {a, 4, true}, // once it counts, it must grow
		{b, 1, true}, {b, 0, false}, // each credential its own
		{a, 1 << 31, true}, {a, 1<<32 - 1, true}, {a, 1<<32 - 1, false},
	}
	for i, s := range steps {
		err := c.Check(s.id, s.count)
		if s.ok != (err == nil) || (!s.ok && !errors.Is(err, ErrCloned)) {
			t.Fatalf("step %d (%q at %d): want ok=%v, got %v", i, s.id, s.count, s.ok, err)
		}
	}
	if err := private.Check(path); err != nil { // its mode on Linux and macOS, its access list on Windows
		t.Fatalf("kept in a file of this account's alone: %v", err)
	}
	again := OpenCounts(path)
	if again.Err() != nil || again.Check(a, 1<<32-1) == nil || again.Check(b, 1) == nil || again.Check(b, 2) != nil {
		t.Fatalf("the counts outlive a restart: %v", again.Err())
	}
	if err := os.WriteFile(path, []byte("{not json"), 0o600); err != nil {
		t.Fatal(err)
	}
	broken := OpenCounts(path)
	if broken.Err() == nil || broken.Check(a, 1) != nil {
		t.Fatalf("an unreadable file is begun again, and says why: %v", broken.Err())
	}
	_ = os.WriteFile(path, []byte("null"), 0o600)
	if c := OpenCounts(path); c.Check(a, 1) != nil || !errors.Is(c.Check(a, 1), ErrCloned) {
		t.Fatal("a file that says null is kept in like an empty one")
	}
	if OpenCounts(filepath.Join(t.TempDir(), "none.json")).Err() != nil {
		t.Fatal("no file yet is no error")
	}
	mem := OpenCounts("")
	if mem.Check(a, 5) != nil || !errors.Is(mem.Check(a, 5), ErrCloned) {
		t.Fatal("kept in memory alone, it refuses alike")
	}
}

// Two sign-ins at once with the same counter: one goes, the other is the copy.
func TestCountsAtOnce(t *testing.T) {
	c := OpenCounts(filepath.Join(t.TempDir(), "passkey-counts.json"))
	var wg sync.WaitGroup
	var mu sync.Mutex
	went := 0
	for i := 0; i < 16; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			if c.Check([]byte("one credential"), 7) == nil {
				mu.Lock()
				went++
				mu.Unlock()
			}
		}()
	}
	wg.Wait()
	if went != 1 {
		t.Fatalf("one of sixteen answers at counter 7 goes, not %d", went)
	}
}
