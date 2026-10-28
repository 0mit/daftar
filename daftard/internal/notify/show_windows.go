//go:build windows

package notify

import (
	"os"
	"path/filepath"
	"strings"

	"github.com/0mit/daftar/daftard/internal/proc"
	"github.com/0mit/daftar/daftard/internal/state"
)

// the toast is read from a file, never pasted into a command line: what a garden says reaches it only as XML text
const script = "\xef\xbb\xbf" + `param([string]$Xml, [string]$App)
$ErrorActionPreference = 'Stop'
[void][Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
[void][Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]
$doc = New-Object Windows.Data.Xml.Dom.XmlDocument
$doc.LoadXml([IO.File]::ReadAllText($Xml, [Text.Encoding]::UTF8))
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($App).Show([Windows.UI.Notifications.ToastNotification]::new($doc))
`

// Show raises a notice as a toast.
func Show(n Notice) error {
	dir, err := state.Ensure()
	if err != nil {
		return err
	}
	ps := filepath.Join(dir, "toast.ps1")
	if b, _ := os.ReadFile(ps); string(b) != script {
		if err := os.WriteFile(ps, []byte(script), 0o600); err != nil {
			return err
		}
	}
	f := filepath.Join(dir, "toast-"+state.Random(6)+".xml")
	if err := os.WriteFile(f, []byte(Toast(n)), 0o600); err != nil {
		return err
	}
	defer os.Remove(f)
	out, err := proc.Command("powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", ps,
		"-Xml", f, "-App", AppID).CombinedOutput()
	if err != nil {
		return &showError{err, strings.TrimSpace(string(out))}
	}
	return nil
}

type showError struct {
	err error
	out string
}

func (e *showError) Error() string { return e.err.Error() + ": " + e.out }
