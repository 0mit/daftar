//go:build linux

package register

import (
	"os/exec"
	"syscall"
)

// endWithDaftard has the kernel end the forward's ssh when daftard ends, however it ends — a kill included.
func endWithDaftard(c *exec.Cmd) {
	if c.SysProcAttr == nil {
		c.SysProcAttr = &syscall.SysProcAttr{}
	}
	c.SysProcAttr.Pdeathsig = syscall.SIGKILL
}
