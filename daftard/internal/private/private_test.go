package private

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// A folder made as daftard makes its state folder (0700; on Windows inside the test's temporary folder,
// %LOCALAPPDATA%\Temp by default, whose access list the profile gives) and a file kept in it are this account's
// alone; a folder others may enter is not; a file opened to everyone is not — on Linux and macOS by its mode, on
// Windows by an entry granting Everyone (S-1-1-0) its reading, made by icacls.
func TestCheck(t *testing.T) {
	dir := filepath.Join(t.TempDir(), "state")
	if err := os.Mkdir(dir, 0o700); err != nil {
		t.Fatal(err)
	}
	if runtime.GOOS != "windows" {
		open := filepath.Join(t.TempDir(), "open")
		if err := os.Mkdir(open, 0o755); err != nil {
			t.Fatal(err)
		}
		_ = os.Chmod(open, 0o755)
		if err := Check(open); err == nil {
			t.Fatalf("a folder others may enter is not this account's alone")
		}
	}
	f := filepath.Join(dir, "kept.json")
	if err := os.WriteFile(f, []byte("{}"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := Check(dir); err != nil {
		t.Fatalf("the test's own folder is this account's alone: %v", err)
	}
	if err := Check(f); err != nil {
		t.Fatalf("a file kept in it is this account's alone: %v", err)
	}
	if runtime.GOOS == "windows" {
		if out, err := exec.Command("icacls", f, "/grant", "*S-1-1-0:(R)").CombinedOutput(); err != nil {
			t.Fatalf("icacls could not open the file to Everyone: %v %s", err, out)
		}
	} else if err := os.Chmod(f, 0o644); err != nil {
		t.Fatal(err)
	}
	err := Check(f)
	if err == nil {
		t.Fatalf("a file opened to everyone is not this account's alone")
	}
	if runtime.GOOS == "windows" && !strings.Contains(err.Error(), "S-1-1-0") {
		t.Fatalf("its refusal names who may reach it: %v", err)
	}
	if err := Check(filepath.Join(dir, "none")); err == nil {
		t.Fatalf("a file that is not there is no file of this account's")
	}
}

// A file written this account's alone: whole, from its first byte (on Linux and macOS its mode, on Windows an access
// list of its own that nothing its folder passes on opens), in place of an older copy others could read — which it
// replaces, never writes through — and nothing left beside it.
func TestWriteFile(t *testing.T) {
	dir := t.TempDir()
	f := filepath.Join(dir, "carried.md")
	if err := WriteFile(f, []byte("first\n")); err != nil {
		t.Fatal(err)
	}
	if b, _ := os.ReadFile(f); string(b) != "first\n" {
		t.Fatalf("written whole: %q", b)
	}
	if err := Check(f); err != nil {
		t.Fatalf("written this account's alone: %v", err)
	}
	if runtime.GOOS == "windows" {
		if out, err := exec.Command("icacls", f, "/grant", "*S-1-1-0:(R)").CombinedOutput(); err != nil {
			t.Fatalf("icacls could not open the file to Everyone: %v %s", err, out)
		}
	} else if err := os.Chmod(f, 0o644); err != nil {
		t.Fatal(err)
	}
	if Check(f) == nil {
		t.Fatalf("the older copy is open to others")
	}
	if err := WriteFile(f, []byte("second\n")); err != nil {
		t.Fatal(err)
	}
	if b, _ := os.ReadFile(f); string(b) != "second\n" {
		t.Fatalf("written whole again: %q", b)
	}
	if err := Check(f); err != nil {
		t.Fatalf("in place of an older copy others could read, this account's alone: %v", err)
	}
	if left, _ := filepath.Glob(filepath.Join(dir, "*")); len(left) != 1 {
		t.Fatalf("nothing left beside it: %v", left)
	}
	if err := WriteFile(filepath.Join(dir, "no", "such", "folder.md"), nil); err == nil {
		t.Fatalf("a folder that is not there is not made")
	}
}
