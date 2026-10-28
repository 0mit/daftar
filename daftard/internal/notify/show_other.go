//go:build !windows

package notify

import (
	"context"
	"os/exec"
	"strings"
	"time"

	"github.com/0mit/daftar/daftard/internal/proc"
)

// Show raises a notice with notify-send where there is a desktop: its "open" action opens the address. With no
// notify-send, nothing (a server with no desktop).
func Show(n Notice) error {
	if _, err := exec.LookPath("notify-send"); err != nil {
		return nil
	}
	go func() {
		ctx, cancel := context.WithTimeout(life, 12*time.Hour) // ended by Stop, with its daftard
		defer cancel()
		cmd := proc.CommandContext(ctx, "notify-send", "--app-name=دفتر", "--action=open="+n.Button, "--wait",
			n.Title, n.Body)
		dieWithParent(cmd)
		out, err := cmd.Output()
		if err == nil && strings.TrimSpace(string(out)) == "open" && Opener != nil {
			Opener(n.URL)
		}
	}()
	return nil
}
