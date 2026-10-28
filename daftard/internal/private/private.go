// Package private says whether a file or a folder is this account's alone: whether anyone else on the machine may read
// or change it. daftard keeps its keys, its readers' ways of reading and its passkeys' counters in its state folder,
// readable by its own account alone. On Linux and macOS that is the file's mode and owner; on Windows, where a mode
// says nothing of who may read (Go shows 0666 and 0777), it is the access list the file inherits from its folder —
// %LOCALAPPDATA%, which is the account's own — and this package reads that list itself (private_windows.go).
package private

import (
	"crypto/rand"
	"encoding/hex"
	"errors"
	"os"
	"path/filepath"
)

// WriteFile writes data to path, this account's alone: into a new file beside it, made so from its first byte (the
// platform's way: create), then put in its place. A copy there before, however open to others, is replaced and never
// written through, so its mode or access list does not carry over; and nobody reads half of it. The folder is not made.
func WriteFile(path string, data []byte) error {
	dir, base := filepath.Split(path)
	var f *os.File
	var tmp string
	for i := 0; ; i++ {
		b := make([]byte, 6)
		if _, err := rand.Read(b); err != nil {
			return err
		}
		tmp = filepath.Join(dir, "."+base+"."+hex.EncodeToString(b)+".part")
		var err error
		if f, err = create(tmp); err == nil {
			break
		} else if !errors.Is(err, os.ErrExist) || i == 9 {
			return err
		}
	}
	_, err := f.Write(data)
	if err == nil {
		err = f.Sync()
	}
	if cerr := f.Close(); err == nil {
		err = cerr
	}
	if err == nil {
		err = os.Rename(tmp, path)
	}
	if err != nil {
		_ = os.Remove(tmp)
	}
	return err
}
