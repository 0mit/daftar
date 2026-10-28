// Package proc starts what daftard runs (the garden's Python, git, a browser) so that NOTHING SHOWS A WINDOW: on
// Windows a console program started by a program with no console opens one of its own: a window that flashes up on
// the desk every time it runs, which is what its users complained of on 2026-10-08. Every child is started through
// Command.
package proc

import (
	"context"
	"os/exec"
)

// Command is exec.Command with the platform's no-window, own-group attributes set (hide_windows.go, hide_other.go).
func Command(name string, args ...string) *exec.Cmd {
	c := exec.Command(name, args...)
	hide(c)
	return c
}

// CommandContext is Command, ended when ctx is.
func CommandContext(ctx context.Context, name string, args ...string) *exec.Cmd {
	c := exec.CommandContext(ctx, name, args...)
	hide(c)
	return c
}
