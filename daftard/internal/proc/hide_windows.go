//go:build windows

package proc

import (
	"os/exec"
	"syscall"
)

const (
	createNoWindow        = 0x08000000 // a console program gets a console with no window, which its own children share
	createNewProcessGroup = 0x00000200 // Ctrl+C in one never reaches the other
)

func hide(c *exec.Cmd) {
	c.SysProcAttr = &syscall.SysProcAttr{HideWindow: true, CreationFlags: createNoWindow | createNewProcessGroup}
}
