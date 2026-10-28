package main

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"syscall"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
)

const standInVar = "DAFTARD_TEST_STAND_IN" // this test binary, started as a garden's daemon: it notes its pid, then waits

func TestMain(m *testing.M) {
	if f := os.Getenv(standInVar); f != "" && len(os.Args) == 4 && os.Args[1] == "serve" && os.Args[2] == "--garden" {
		fh, _ := os.OpenFile(f, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600)
		fmt.Fprintf(fh, "%d %s %s\n", os.Getpid(), os.Args[3], os.Getenv(frontVar))
		fh.Close()
		time.Sleep(time.Hour) // alive until ended (a bare select{} is a deadlock, and the runtime ends it at once)
		os.Exit(0)
	}
	os.Exit(m.Run())
}

func pidsIn(f string) []string {
	b, _ := os.ReadFile(f)
	return strings.Fields(strings.ReplaceAll(string(b), "\n", " "))
}

// A GARDEN'S DAEMON IS KEPT RUNNING: started as `serve --garden <name>` and told the machine's front door; started
// again when it ends; ended, at last, with the machine's daftard.
func TestAGardensDaemonIsKeptRunning(t *testing.T) {
	f := filepath.Join(t.TempDir(), "started")
	t.Setenv(standInVar, f)
	daemonGrace = 200 * time.Millisecond
	stop, done := make(chan struct{}), make(chan struct{})
	go func() {
		keepDaemon(os.Args[0], config.Garden{Name: "ana", Listen: "127.0.0.1:8781"}, "127.0.0.1:8770", t.Logf, stop)
		close(done)
	}()
	wait := func(n int) []string {
		for i := 0; i < 200 && len(pidsIn(f)) < 3*n; i++ {
			time.Sleep(50 * time.Millisecond)
		}
		return pidsIn(f)
	}
	first := wait(1)
	if len(first) < 3 || first[1] != "ana" || first[2] != "127.0.0.1:8770" {
		t.Fatalf("started as ana's daemon, told the front door: %v", first)
	}
	var pid int
	fmt.Sscan(first[0], &pid)
	p, err := os.FindProcess(pid)
	if err != nil {
		t.Fatalf("the daemon runs until ended: %v", err)
	}
	_ = p.Kill()
	second := wait(2)
	if len(second) < 6 || second[3] == first[0] {
		t.Fatalf("started again when it ended: %v", second)
	}
	close(stop)
	select {
	case <-done:
	case <-time.After(10 * time.Second):
		t.Fatal("ended with the machine's daftard")
	}
	fmt.Sscan(second[3], &pid)
	if runtime.GOOS != "windows" { // a process asked by signal 0 whether it is there
		if p, err := os.FindProcess(pid); err == nil && p.Signal(syscall.Signal(0)) == nil {
			t.Fatalf("the daemon is gone with it: %d", pid)
		}
	}
}
