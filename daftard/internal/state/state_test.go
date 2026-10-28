package state

import (
	"os"
	"path/filepath"
	"runtime"
	"testing"

	"github.com/0mit/daftar/daftard/internal/private"
)

// THE STATE FOLDER IS THE ACCOUNT'S OWN: what daftard keeps there (its key, a register's keys, its readers' ways of
// reading, its passkeys' counters) is this account's alone because the folder is. On Windows that is where it lies —
// %LOCALAPPDATA%\Daftar, inside a folder of the account's profile whose access list is the account's alone, which every
// file made in it inherits (a mode there says nothing: Go shows 0666 and 0777). On Linux and macOS, it is made, and
// closed again on every start, 0700. The machine's own folder is only named here, never made or changed.
func TestTheStateFolderIsTheAccountsOwn(t *testing.T) {
	t.Setenv("DAFTARD_STATE", "")
	if runtime.GOOS == "windows" {
		local := os.Getenv("LOCALAPPDATA")
		if local == "" || Dir() != filepath.Join(local, "Daftar") {
			t.Fatalf("on Windows the state folder is %%LOCALAPPDATA%%\\Daftar: %q (LOCALAPPDATA %q)", Dir(), local)
		}
		if err := private.Check(local); err != nil {
			t.Fatalf("...whose folder, %%LOCALAPPDATA%%, is this account's alone: %v", err)
		}
	} else if filepath.Base(Dir()) != "daftar" {
		t.Fatalf("the state folder: %q", Dir())
	}
	// made, and closed again after something opened it, as each start of daftard does
	dir := filepath.Join(t.TempDir(), "state")
	t.Setenv("DAFTARD_STATE", dir)
	if got, err := Ensure(); err != nil || got != dir {
		t.Fatalf("Ensure: %q %v", got, err)
	}
	if err := private.Check(dir); err != nil {
		t.Fatalf("made this account's alone: %v", err)
	}
	if runtime.GOOS != "windows" {
		_ = os.Chmod(dir, 0o755)
		if _, err := Ensure(); err != nil || private.Check(dir) != nil {
			t.Fatalf("closed again on the next start: %v", private.Check(dir))
		}
	}
}
