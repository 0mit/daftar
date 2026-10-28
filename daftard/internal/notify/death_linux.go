//go:build linux

package notify

import (
	"os/exec"
	"syscall"
)

// dieWithParent ends a notice's notify-send when the daftard that started it dies, stopped or not: the kernel signals
// it (PR_SET_PDEATHSIG). Its own process group stays (proc.hide), so a signal to daftard is still not a signal to it.
func dieWithParent(c *exec.Cmd) {
	if c.SysProcAttr == nil {
		c.SysProcAttr = &syscall.SysProcAttr{}
	}
	c.SysProcAttr.Pdeathsig = syscall.SIGTERM
}
