//go:build !windows

package lock

import (
	"errors"
	"os"
	"syscall"
)

func take(p string) (*os.File, error) {
	f, err := os.OpenFile(p, os.O_RDWR|os.O_CREATE, 0o600)
	if err != nil {
		return nil, err
	}
	if err := syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		_ = f.Close()
		if errors.Is(err, syscall.EWOULDBLOCK) {
			return nil, ErrHeld
		}
		return nil, err
	}
	return f, nil
}

func release(f *os.File) { _ = syscall.Flock(int(f.Fd()), syscall.LOCK_UN) }
