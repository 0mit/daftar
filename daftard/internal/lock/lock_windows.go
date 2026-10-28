//go:build windows

package lock

import (
	"errors"
	"os"
	"syscall"
)

// ERROR_SHARING_VIOLATION: the file is open, unshared, in another process
const errSharing syscall.Errno = 32

// take opens the lock file to write shared for reading alone: while this process holds it open, no other process can
// open it to write — a second daemon is refused — and the pid it holds can still be read, to name who holds it.
func take(p string) (*os.File, error) {
	name, err := syscall.UTF16PtrFromString(p)
	if err != nil {
		return nil, err
	}
	h, err := syscall.CreateFile(name, syscall.GENERIC_READ|syscall.GENERIC_WRITE, syscall.FILE_SHARE_READ, nil, syscall.OPEN_ALWAYS,
		syscall.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		if errors.Is(err, errSharing) {
			return nil, ErrHeld
		}
		return nil, err
	}
	return os.NewFile(uintptr(h), p), nil
}

func release(*os.File) {}
