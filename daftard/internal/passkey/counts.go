package passkey

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"sync"
)

// ErrCloned is a sign-in whose signature counter did not grow past the last one seen: two authenticators answer as one
// credential, so one of them is a copy (W3C Web Authentication §6.1.1).
var ErrCloned = errors.New("its signature counter did not grow past the last one seen: a cloned authenticator")

// Counts keeps each credential's last signature counter (W3C Web Authentication §6.1.1, security audit 2026-10-10,
// 1.4). It is the machine's, not the garden's: kept in one file in daftard's state folder, so a sign-in never writes to
// the garden, and written only when a counter grows — an authenticator that keeps no counter (it always says zero)
// writes nothing. Only a credential whose signature verified against an anchor a person's bean names is kept, so the
// file grows with the passkeys the gardener named, never with what a stranger sends.
type Counts struct {
	mu   sync.Mutex
	path string            // "" keeps them in memory alone
	seen map[string]uint32 // a credential id's digest → the counter its last sign-in carried
	err  error             // why the file could not be read, if it could not (it is begun again when next written)
}

// OpenCounts reads the counts kept at path ("" keeps them in memory alone). A file that cannot be read is begun again:
// Err says why.
func OpenCounts(path string) *Counts {
	c := &Counts{path: path, seen: map[string]uint32{}}
	if path == "" {
		return c
	}
	b, err := os.ReadFile(path)
	if err == nil {
		err = json.Unmarshal(b, &c.seen)
	}
	if err != nil && !errors.Is(err, os.ErrNotExist) {
		c.seen, c.err = map[string]uint32{}, err
	}
	if c.seen == nil { // a file that says `null` holds nothing, and is no map to keep in
		c.seen = map[string]uint32{}
	}
	return c
}

// Err is why the kept counts could not be read when they were opened, or nil.
func (c *Counts) Err() error { return c.err }

// Check takes a sign-in's counter for the credential. Where the counter or the last one seen is not zero, it must
// grow: then it is kept, and Check is nil; otherwise ErrCloned, and nothing changes. Both zero is an authenticator
// that keeps no counter: nil, nothing kept. Any other error is the file not written: the counter is still kept in
// memory, so this run refuses a replay of it, and the sign-in may go ahead — a full disk locks nobody out.
func (c *Counts) Check(credID []byte, count uint32) error {
	d := sha256.Sum256(credID)
	k := hex.EncodeToString(d[:])
	c.mu.Lock()
	defer c.mu.Unlock()
	last := c.seen[k]
	if count == 0 && last == 0 {
		return nil
	}
	if count <= last {
		return ErrCloned
	}
	c.seen[k] = count
	return c.write()
}

// write puts the counts in their file whole, readable by this account alone: a new file renamed over the old, so a
// crash leaves the one or the other.
func (c *Counts) write() error {
	if c.path == "" {
		return nil
	}
	b, err := json.Marshal(c.seen)
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(c.path), ".passkey-counts-*")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if err := tmp.Chmod(0o600); err != nil {
		tmp.Close()
		return err
	}
	if _, err := tmp.Write(b); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), c.path)
}
