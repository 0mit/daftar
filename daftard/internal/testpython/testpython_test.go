package testpython

import (
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// A stand-in first on PATH that runs nothing and exits at once — as the Microsoft Store's `python3` does on Windows
// (…\WindowsApps\python3.exe) — is passed over for a Python on PATH that runs; and where none runs, the answer says
// which were tried.
func TestAPythonThatRuns(t *testing.T) {
	if _, err := find(os.Getenv("PATH")); err != nil {
		t.Skipf("no Python runs on this machine: %v", err)
	}
	stand := t.TempDir()
	name, body := "python3", "#!/bin/sh\nexit 9\n"
	if runtime.GOOS == "windows" {
		name, body = "python3.cmd", "@exit /b 9009\r\n"
	}
	if err := os.WriteFile(filepath.Join(stand, name), []byte(body), 0o700); err != nil {
		t.Fatal(err)
	}
	got, err := find(stand + string(os.PathListSeparator) + os.Getenv("PATH"))
	if err != nil {
		t.Fatalf("a Python that runs, past the stand-in: %v", err)
	}
	if strings.HasPrefix(got, stand) {
		t.Fatalf("the stand-in that exits at once is passed over: %s", got)
	}
	if err := exec.Command(got, "-c", "pass").Run(); err != nil {
		t.Fatalf("what is found runs: %s %v", got, err)
	}
	if _, err := find(stand); err == nil || !strings.Contains(err.Error(), stand) {
		t.Fatalf("where none runs, the answer names what was tried: %v", err)
	}
}
