//go:build !windows

package proc

import (
	"os/exec"
	"syscall"
)

func hide(c *exec.Cmd) {
	c.SysProcAttr = &syscall.SysProcAttr{Setpgid: true} // its own group: a signal to daftard is not a signal to it
}
