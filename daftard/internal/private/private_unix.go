//go:build !windows

package private

import (
	"fmt"
	"os"
	"syscall"
)

// Check says why path is not this account's alone — another account owns it, or its mode lets the group or others
// read, change or enter it — and nil where it is.
func Check(path string) error {
	st, err := os.Stat(path)
	if err != nil {
		return err
	}
	if s, ok := st.Sys().(*syscall.Stat_t); ok && int(s.Uid) != os.Getuid() {
		return fmt.Errorf("%s is owned by uid %d, not this account (%d)", path, s.Uid, os.Getuid())
	}
	if m := st.Mode().Perm(); m&0o077 != 0 {
		return fmt.Errorf("%s has mode %04o: its group or others may reach it", path, m)
	}
	return nil
}

// create makes a new file at path, readable and writable by this account alone (0600, whatever the umask leaves; a
// umask only takes away).
func create(path string) (*os.File, error) {
	return os.OpenFile(path, os.O_WRONLY|os.O_CREATE|os.O_EXCL, 0o600)
}
