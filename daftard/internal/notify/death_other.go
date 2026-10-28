//go:build !linux && !windows

package notify

import "os/exec"

// dieWithParent: where the kernel has no parent-death signal, a notice ends with Stop alone.
func dieWithParent(c *exec.Cmd) {}
