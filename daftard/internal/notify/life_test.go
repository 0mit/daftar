//go:build linux

package notify

import (
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"testing"
	"time"
)

// fakeNotifySend puts a notify-send on PATH that writes its pid and then waits as the real one does with --wait: what
// a test daftard raised, standing in for the desktop's own.
func fakeNotifySend(t *testing.T) (pidFile string) {
	t.Helper()
	dir := t.TempDir()
	pidFile = filepath.Join(dir, "pid")
	script := "#!/bin/sh\necho $$ > " + pidFile + "\nexec sleep 300\n"
	if err := os.WriteFile(filepath.Join(dir, "notify-send"), []byte(script), 0o755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", dir+string(os.PathListSeparator)+os.Getenv("PATH"))
	return pidFile
}

func waitPid(t *testing.T, pidFile string) int {
	t.Helper()
	for i := 0; i < 100; i++ {
		if b, err := os.ReadFile(pidFile); err == nil && strings.TrimSpace(string(b)) != "" {
			pid, _ := strconv.Atoi(strings.TrimSpace(string(b)))
			return pid
		}
		time.Sleep(50 * time.Millisecond)
	}
	return 0
}

func gone(pid int) bool {
	for i := 0; i < 100; i++ {
		if syscall.Kill(pid, 0) != nil {
			return true
		}
		// a child of this test process that has ended is a zombie until reaped: read its state
		if b, err := os.ReadFile("/proc/" + strconv.Itoa(pid) + "/stat"); err == nil && strings.Contains(string(b), ") Z ") {
			return true
		}
		time.Sleep(50 * time.Millisecond)
	}
	return false
}

// A DAFTARD A TEST STARTS RAISES NO DESKTOP NOTICE: with DAFTARD_NOTIFY=off a notice is a line of daftard's log, and
// nothing is run on the machine's desktop.
func TestAQuietDaftardRaisesNoNotice(t *testing.T) {
	pidFile := fakeNotifySend(t)
	t.Setenv(QuietEnv, "off")
	var logged []string
	err := Raise(func(f string, a ...any) { logged = append(logged, f) })(Notice{Title: "دفتر Sam", Body: "a case waits", Button: "open", URL: "daftar://go/g/case/c"})
	time.Sleep(300 * time.Millisecond)
	if _, statErr := os.Stat(pidFile); err != nil || statErr == nil || len(logged) != 1 {
		t.Fatalf("quiet: no notify-send run, the notice in the log: err %v, ran %v, logged %v", err, statErr == nil, logged)
	}
}

// A NOTICE ENDS WITH ITS DAFTARD: Stop, as daftard stops, ends every notice still waiting on the desktop.
func TestANoticeEndsWhenItsDaftardStops(t *testing.T) {
	pidFile := fakeNotifySend(t)
	t.Setenv(QuietEnv, "")
	restart()
	if err := Raise(nil)(Notice{Title: "دفتر Sam", Body: "a case waits", Button: "open", URL: "daftard://go/g/case/c"}); err != nil {
		t.Fatal(err)
	}
	pid := waitPid(t, pidFile)
	if pid == 0 {
		t.Fatal("the notice was raised: notify-send ran")
	}
	Stop()
	if !gone(pid) {
		_ = syscall.Kill(pid, syscall.SIGKILL)
		t.Fatalf("the notice ends when daftard stops: notify-send %d still runs", pid)
	}
	restart()
}

// ...AND WHEN IT DIES WITHOUT STOPPING: a daftard killed (a test's, ended by its runner) takes its notices with it.
func TestANoticeEndsWhenItsDaftardDies(t *testing.T) {
	if os.Getenv("NOTIFY_HELPER") == "1" { // the daftard: raise a notice, then die without stopping
		_ = Show(Notice{Title: "دفتر Sam", Body: "a case waits", Button: "open", URL: "daftard://go/g/case/c"})
		for i := 0; i < 100; i++ {
			if b, _ := os.ReadFile(os.Getenv("NOTIFY_PIDFILE")); len(b) > 0 {
				break
			}
			time.Sleep(50 * time.Millisecond)
		}
		os.Exit(0)
	}
	pidFile := fakeNotifySend(t)
	cmd := exec.Command(os.Args[0], "-test.run=^TestANoticeEndsWhenItsDaftardDies$")
	cmd.Env = append(os.Environ(), "NOTIFY_HELPER=1", "NOTIFY_PIDFILE="+pidFile)
	if out, err := cmd.CombinedOutput(); err != nil {
		t.Fatalf("the helper daftard: %v %s", err, out)
	}
	pid := waitPid(t, pidFile)
	if pid == 0 {
		t.Fatal("the helper raised its notice: notify-send ran")
	}
	if !gone(pid) {
		_ = syscall.Kill(pid, syscall.SIGKILL)
		t.Fatalf("a notice outlives the daftard that raised it: notify-send %d still runs", pid)
	}
}
