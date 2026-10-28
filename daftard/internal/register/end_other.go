//go:build !linux

package register

import "os/exec"

// endWithDaftard: elsewhere the forward's ssh is ended by daftard's own stopping (Close); a daftard killed outright
// leaves it to end with its connection.
func endWithDaftard(c *exec.Cmd) {}
