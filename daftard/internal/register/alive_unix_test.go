//go:build !windows

package register

import "syscall"

// alive says whether a process runs: a signal 0 reaches it.
func alive(pid int) bool { return pid > 0 && syscall.Kill(pid, 0) == nil }
