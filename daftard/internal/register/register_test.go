package register

import (
	"crypto/tls"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"sync"
	"sync/atomic"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
)

// THE TEST BINARY IS ALSO A STAND-IN FOR SSH: run with DAFTARD_FAKE_SSH set, it writes down the arguments it was given
// and does what an ssh forward does on this side — listens on the -L port and answers there as the register's
// /web/health would through it — until it is ended; while the file DAFTARD_FAKE_SSH_HANG names exists, it takes each
// request and answers nothing (a half-open link, where the ssh lives on and nothing passes).
func TestMain(m *testing.M) {
	if os.Getenv("DAFTARD_FAKE_SSH") != "" {
		fakeSSH()
		return
	}
	os.Exit(m.Run())
}

func fakeSSH() {
	args := os.Args[1:]
	if f := os.Getenv("DAFTARD_FAKE_SSH_ARGS"); f != "" {
		_ = os.WriteFile(f, []byte(strings.Join(args, "\n")), 0o600)
	}
	local := ""
	for i, a := range args {
		if a == "-L" && i+1 < len(args) {
			local = args[i+1]
		}
	}
	parts := strings.SplitN(local, ":", 3)
	if len(parts) < 3 {
		fmt.Fprintln(os.Stderr, "Bad local forwarding specification")
		os.Exit(255)
	}
	l, err := net.Listen("tcp", parts[0]+":"+parts[1])
	if err != nil {
		fmt.Fprintln(os.Stderr, "bind [127.0.0.1]:"+parts[1]+": Address already in use")
		fmt.Fprintln(os.Stderr, "Could not request local forwarding.")
		os.Exit(255)
	}
	_ = http.Serve(l, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if _, err := os.Stat(os.Getenv("DAFTARD_FAKE_SSH_HANG")); err == nil {
			select {}
		}
		_, _ = w.Write([]byte(`{"status": "pass"}`))
	}))
}

// quick makes every interval short, for the test's length, and the log a list to read.
func quick(t *testing.T) *logLines {
	t.Helper()
	was := []time.Duration{Every, Soon, Wait, OnDemandGap, FirstBack, MostBack, Lasted, Starting}
	Every, Soon, Wait, OnDemandGap = 400*time.Millisecond, 100*time.Millisecond, 300*time.Millisecond, 50*time.Millisecond
	FirstBack, MostBack, Lasted, Starting = 200*time.Millisecond, 800*time.Millisecond, time.Hour, 5*time.Second
	t.Cleanup(func() {
		Every, Soon, Wait, OnDemandGap, FirstBack, MostBack, Lasted, Starting = was[0], was[1], was[2], was[3], was[4], was[5],
			was[6], was[7]
	})
	t.Setenv("DAFTARD_STATE", t.TempDir())
	return &logLines{}
}

type logLines struct {
	mu    sync.Mutex
	lines []string
}

func (l *logLines) printf(format string, a ...any) {
	l.mu.Lock()
	defer l.mu.Unlock()
	l.lines = append(l.lines, fmt.Sprintf(format, a...))
}

func (l *logLines) all() string {
	l.mu.Lock()
	defer l.mu.Unlock()
	return strings.Join(l.lines, "\n")
}

// a stand-in register's /web/health: answering, failing (503), or taking the request and answering nothing
type standIn struct {
	mode atomic.Value // "ok", "fail", "hang"
	hits atomic.Int64
	srv  *httptest.Server
}

func newStandIn(t *testing.T) *standIn {
	s := &standIn{}
	s.mode.Store("ok")
	s.srv = httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		s.hits.Add(1)
		switch s.mode.Load() {
		case "fail":
			w.WriteHeader(503)
		case "hang":
			select {
			case <-r.Context().Done():
			case <-time.After(5 * time.Second):
			}
		default:
			_, _ = w.Write([]byte(`{"status": "pass"}`))
		}
	}))
	t.Cleanup(s.srv.Close)
	return s
}

func eventually(t *testing.T, what string, within time.Duration, ok func() bool) {
	t.Helper()
	end := time.Now().Add(within)
	for !ok() {
		if time.Now().After(end) {
			t.Fatalf("not within %s: %s", within, what)
		}
		time.Sleep(20 * time.Millisecond)
	}
}

// handed is the order the worker would be handed: "2,1-" — route 2, then route 1, not healthy, as the last resort
func handed(rs *Routes) string {
	var out []string
	for _, h := range rs.Hand() {
		out = append(out, fmt.Sprint(h["route"])+map[bool]string{true: "-"}[h["down"] == true])
	}
	return strings.Join(out, ",")
}

// HEALTH: a route is healthy until it misses twice in a row, healthy again at its next answer; the worker is handed
// the healthy routes in daftard.json's order — an https route not healthy after them, as the one a failed read may
// still be asked of, but none where no route is healthy — and each transition is in daftard.log.
func TestHealthAndOrder(t *testing.T) {
	log := quick(t)
	a, b := newStandIn(t), newStandIn(t)
	rs := New("g", &config.Register{Routes: []config.Route{{Via: "https", URL: a.srv.URL}, {Via: "https", URL: b.srv.URL + "/"}}},
		log.printf)
	rs.Run()
	defer rs.Close()
	if got := handed(rs); got != "1,2" {
		t.Fatalf("both healthy from the start, in order: %q", got)
	}
	if h := rs.Hand()[1]["url"]; h != b.srv.URL {
		t.Fatalf("a route's address, without its trailing slash: %v", h)
	}
	eventually(t, "each route asked", time.Second, func() bool { return a.hits.Load() > 0 && b.hits.Load() > 0 })
	a.mode.Store("fail")
	eventually(t, "route 1 not healthy after two misses", 2*time.Second, func() bool { return handed(rs) == "2,1-" })
	st := rs.State(false)["routes"].([]RouteState)
	if st[0].Healthy || st[0].Error != "status 503" || !st[1].Healthy || st[0].Label != "" {
		t.Fatalf("seen: %+v", st)
	}
	if full := rs.State(true)["routes"].([]RouteState); full[0].Label != "1 ("+a.srv.URL+")" {
		t.Fatalf("where it goes, for whoever may read daftard.json: %q", full[0].Label)
	}
	a.mode.Store("ok")
	eventually(t, "route 1 healthy again at its next answer", 2*time.Second, func() bool { return handed(rs) == "1,2" })
	if st := rs.State(false)["routes"].([]RouteState); st[0].Error != "status 503" || time.Since(st[0].Since) > 2*time.Second {
		t.Fatalf("its last error kept, since when it answered again: %+v", st[0])
	}
	logged := log.all()
	for _, want := range []string{"[g] register route 1 (" + a.srv.URL + "): missed once (status 503)",
		"[g] register route 1 (" + a.srv.URL + "): not healthy (missed twice: status 503)",
		"[g] register route 1 (" + a.srv.URL + "): healthy (it answers)"} {
		if !strings.Contains(logged, want) {
			t.Fatalf("daftard.log has no %q:\n%s", want, logged)
		}
	}
	a.srv.Close() // gone: refused
	eventually(t, "a route that refuses, not healthy", 2*time.Second, func() bool { return handed(rs) == "2,1-" })
	b.mode.Store("fail")
	eventually(t, "neither healthy: nothing handed", 2*time.Second, func() bool { return handed(rs) == "" })
	// a closed port of the loopback refuses at once — on Windows only after the stack's own retries (~2 s), longer
	// than this test's Wait: there the check times out first
	if st := rs.State(false)["routes"].([]RouteState); st[0].Error != "refused" &&
		!(runtime.GOOS == "windows" && st[0].Error == "timeout") {
		t.Fatalf("its error's kind: %q", st[0].Error)
	}
}

// A HUNG ROUTE: a check that waits longer than Wait is a miss, as a refusal is.
func TestHungRouteMisses(t *testing.T) {
	log := quick(t)
	a := newStandIn(t)
	rs := New("g", &config.Register{URL: a.srv.URL}, log.printf)
	rs.Run()
	defer rs.Close()
	a.mode.Store("hang")
	eventually(t, "a hung route not healthy", 3*time.Second, func() bool { return handed(rs) == "" })
	if st := rs.State(false)["routes"].([]RouteState); st[0].Error != "timeout" {
		t.Fatalf("its error's kind: %q", st[0].Error)
	}
}

// WHAT THE WORKER FOUND: a read that did not reach the register by a route is a miss, and asks a check at once — the
// route, until it answers, tried after those that did not miss; the route that answered last is seen; a reading that
// was handed no healthy route asks every route at once.
func TestWorkerNotes(t *testing.T) {
	log := quick(t)
	Every = time.Hour // only what the notes ask, after the first round
	a, b := newStandIn(t), newStandIn(t)
	rs := New("g", &config.Register{Routes: []config.Route{{Via: "https", URL: a.srv.URL}, {Via: "https", URL: b.srv.URL}}},
		log.printf)
	rs.Run()
	defer rs.Close()
	eventually(t, "the first round", time.Second, func() bool { return a.hits.Load() == 1 && b.hits.Load() == 1 })
	a.mode.Store("fail")
	rs.Note([]Note{{Route: 1, Missed: "timeout"}, {Route: 2, Answered: true}})
	if got := handed(rs); got != "2,1" {
		t.Fatalf("a route a read missed is tried after the others: %q", got)
	}
	eventually(t, "a check asked of route 1 at once", time.Second, func() bool { return a.hits.Load() == 2 })
	eventually(t, "...its second miss: not healthy", time.Second, func() bool { return handed(rs) == "2,1-" })
	st := rs.State(false)
	if st["answered"].(map[string]any)["route"] != 2 || !st["routes"].([]RouteState)[1].Answered {
		t.Fatalf("which route answered last: %v", st)
	}
	if !strings.Contains(log.all(), "route 1 ("+a.srv.URL+"): missed once (read: timeout)") {
		t.Fatalf("the read's miss logged:\n%s", log.all())
	}
	a.mode.Store("ok")
	time.Sleep(3 * OnDemandGap)
	nb := b.hits.Load()
	rs.Note([]Note{{None: true}})
	eventually(t, "every route asked at once", time.Second, func() bool { return b.hits.Load() > nb && handed(rs) == "1,2" })
	rs.Note([]Note{{Route: 9, Missed: "refused"}, {Route: 1, Missed: "<script>"}})
	if st := rs.State(false)["routes"].([]RouteState); st[0].Error != "read: unreachable" {
		t.Fatalf("a kind the worker names is kept to this package's words: %q", st[0].Error)
	}
}

// pinned makes the state folder's ssh key and known_hosts for garden g, the host pinned.
func pinned(t *testing.T, conf *config.Register, host string) {
	t.Helper()
	_ = os.MkdirAll(filepath.Dir(conf.SSHKeyFile("g")), 0o700)
	if err := os.WriteFile(conf.SSHKeyFile("g"), []byte("not a real key: the stand-in reads none\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(conf.KnownHostsFile("g"), []byte(host+" ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl\n"), 0o600); err != nil {
		t.Fatal(err)
	}
}

func sshRoutes(t *testing.T, log *logLines) (*Routes, string) {
	t.Helper()
	conf := &config.Register{Routes: []config.Route{{Via: "ssh", Host: "register.example.org", User: "tunnel", To: "127.0.0.1:8069"}}}
	pinned(t, conf, "register.example.org")
	args := filepath.Join(t.TempDir(), "args")
	t.Setenv("DAFTARD_FAKE_SSH", "1")
	t.Setenv("DAFTARD_FAKE_SSH_ARGS", args)
	t.Setenv("DAFTARD_FAKE_SSH_HANG", filepath.Join(t.TempDir(), "hang"))
	rs := New("g", conf, log.printf)
	self, err := os.Executable() // its own path, whole: Windows runs no bare name from the folder it is in
	if err != nil {
		t.Fatal(err)
	}
	rs.SSH = self
	return rs, args
}

// kill ends a process outright, as a connection cut off ends an ssh (alive: alive_unix_test.go, alive_windows_test.go)
func kill(pid int) {
	if p, err := os.FindProcess(pid); err == nil {
		_ = p.Kill()
	}
}

// THE SSH ROUTE IS DAFTARD'S: its ssh started with only the forward and the state folder's key and pinned host, the
// route healthy once an answer comes through the forward, ended and started again when it ends, and ended with
// daftard.
func TestSSHForward(t *testing.T) {
	log := quick(t)
	rs, argsFile := sshRoutes(t, log)
	if got := handed(rs); got != "" {
		t.Fatalf("an ssh route is handed nothing before its forward answers: %q", got)
	}
	rs.Run()
	eventually(t, "the forward healthy", 5*time.Second, func() bool { return handed(rs) == "1" })
	url := rs.Hand()[0]["url"].(string)
	if !strings.HasPrefix(url, "http://127.0.0.1:") {
		t.Fatalf("the forward's own loopback address: %q", url)
	}
	b, _ := os.ReadFile(argsFile)
	args := strings.Split(string(b), "\n")
	key, known := config.SSHKeyFile("g"), config.KnownHostsFile("g")
	want := []string{"-N", "-F", "none", "-o", "BatchMode=yes", "-o", "PreferredAuthentications=publickey", "-o",
		"IdentitiesOnly=yes", "-o", "IdentityAgent=none", "-i", key, "-o", "StrictHostKeyChecking=yes", "-o",
		`UserKnownHostsFile="` + known + `"`, "-o", "GlobalKnownHostsFile=none", "-o", "UpdateHostKeys=no", "-o",
		"CheckHostIP=no", "-o", "ExitOnForwardFailure=yes", "-o", "ForwardAgent=no", "-o", "ForwardX11=no", "-o",
		"PermitLocalCommand=no", "-o", "ControlMaster=no", "-o", "ControlPath=none", "-o", "ConnectTimeout=20", "-o",
		"ServerAliveInterval=10", "-o", "ServerAliveCountMax=3", "-o", "TCPKeepAlive=no", "-o", "Compression=yes", "-o",
		"LogLevel=ERROR", "-p", "22", "-l", "tunnel", "-L", strings.TrimPrefix(url, "http://") + ":127.0.0.1:8069", "--",
		"register.example.org"}
	if strings.Join(args, " ") != strings.Join(want, " ") {
		t.Fatalf("ssh's arguments:\n got %q\nwant %q", args, want)
	}
	rs.mu.Lock()
	pid := rs.routes[0].pid
	rs.mu.Unlock()
	kill(pid) // the ssh ends, as one cut off does
	eventually(t, "the route down at once when its ssh ends", time.Second, func() bool { return handed(rs) == "" })
	eventually(t, "started again, healthy", 5*time.Second, func() bool { return handed(rs) == "1" })
	rs.mu.Lock()
	again := rs.routes[0].pid
	rs.mu.Unlock()
	if again == pid || !alive(again) {
		t.Fatalf("a new ssh: %d, was %d", again, pid)
	}
	logged := log.all()
	for _, want := range []string{"register route 1 (ssh tunnel@register.example.org:22 → 127.0.0.1:8069): forward on 127.0.0.1:",
		"): healthy (it answers)", "): not healthy (ssh ended (exit ", "): forward ended after "} {
		if !strings.Contains(logged, want) {
			t.Fatalf("daftard.log has no %q:\n%s", want, logged)
		}
	}
	rs.Close()
	if alive(again) {
		t.Fatalf("its ssh ended with daftard: %d lives on", again)
	}
	if st := rs.State(false)["routes"].([]RouteState); st[0].Healthy || st[0].Error != "daftard stopped" {
		t.Fatalf("seen after daftard stopped: %+v", st[0])
	}
}

// A HALF-OPEN LINK: the ssh lives on and nothing passes. The route misses twice, its ssh is ended by daftard and
// started again, as the shell loop's watchdog did outside daftard.
func TestSSHWatchdog(t *testing.T) {
	log := quick(t)
	rs, _ := sshRoutes(t, log)
	rs.Run()
	defer rs.Close()
	eventually(t, "the forward healthy", 5*time.Second, func() bool { return handed(rs) == "1" })
	rs.mu.Lock()
	pid := rs.routes[0].pid
	rs.mu.Unlock()
	hang := os.Getenv("DAFTARD_FAKE_SSH_HANG")
	_ = os.WriteFile(hang, nil, 0o600)
	eventually(t, "two misses: its ssh ended", 5*time.Second, func() bool { return !alive(pid) })
	_ = os.Remove(hang)
	eventually(t, "a new ssh, healthy", 5*time.Second, func() bool { return handed(rs) == "1" })
	if !strings.Contains(log.all(), "forward ended after ") || !strings.Contains(log.all(), "(ended by daftard: missed twice (timeout))") {
		t.Fatalf("daftard.log:\n%s", log.all())
	}
}

// NO KEY, NO FORWARD: an ssh route whose key is not in the state folder, or may be read by others, or whose host's key
// is not pinned, is never started, and says why.
func TestSSHNeedsItsFiles(t *testing.T) {
	log := quick(t)
	rs, argsFile := sshRoutes(t, log)
	_ = os.Remove(config.SSHKeyFile("g"))
	rs.Run()
	defer rs.Close()
	eventually(t, "said why", 2*time.Second, func() bool {
		return rs.State(false)["routes"].([]RouteState)[0].Error == "no ssh key"
	})
	if runtime.GOOS == "windows" {
		// no mode to refuse a key by: on Windows a key's privacy is its folder's access list (%LOCALAPPDATA%; the
		// state package's test holds it), so the key is laid as the state folder keeps it, and the next step follows
		t.Log("Windows: a key file's mode says nothing there; its privacy is the state folder's (internal/state's test)")
		_ = os.WriteFile(config.SSHKeyFile("g"), []byte("k\n"), 0o600)
	} else {
		_ = os.WriteFile(config.SSHKeyFile("g"), []byte("k\n"), 0o644)
		_ = os.Chmod(config.SSHKeyFile("g"), 0o644)
		eventually(t, "said why", 3*time.Second, func() bool {
			return rs.State(false)["routes"].([]RouteState)[0].Error == "ssh key readable by others: make it 0600"
		})
		_ = os.Chmod(config.SSHKeyFile("g"), 0o600)
	}
	_ = os.WriteFile(config.KnownHostsFile("g"), []byte("other.example.org ssh-ed25519 AAAA\n"), 0o600)
	eventually(t, "said why", 3*time.Second, func() bool {
		return rs.State(false)["routes"].([]RouteState)[0].Error == "host key not pinned"
	})
	if _, err := os.Stat(argsFile); err == nil || handed(rs) != "" {
		t.Fatalf("an ssh was started")
	}
	if !strings.Contains(log.all(), "not started (no ssh key); tried again in ") {
		t.Fatalf("daftard.log:\n%s", log.all())
	}
}

// what ssh says it ended of, kept to a few words
func TestSSHKind(t *testing.T) {
	for line, want := range map[string]string{
		"Host key verification failed.":                                                   "ssh: host key",
		"tunnel@register.example.org: Permission denied (publickey).":                     "ssh: key refused",
		"ssh: connect to host 203.0.113.10 port 22: Connection refused":                   "ssh: refused",
		"ssh: connect to host 203.0.113.10 port 22: Connection timed out":                 "ssh: timeout",
		"Timeout, server register.example.org not responding.":                            "ssh: timeout",
		"Connection reset by 203.0.113.10 port 22":                                        "ssh: reset",
		"ssh: Could not resolve hostname register.example.org: Name or service not known": "ssh: dns",
		"Error: remote port forwarding failed for listen port 1":                          "ssh: forward refused",
		"channel 2: open failed: administratively prohibited: open failed":                "ssh: forward refused",
		"Load key \"/x/g.ssh\": bad permissions":                                          "ssh: key file",
		"something else":                                                                  "ssh: failed",
	} {
		if got := sshKind(line); got != want {
			t.Errorf("%q → %q; want %q", line, got, want)
		}
	}
}

func TestKind(t *testing.T) {
	l, _ := net.Listen("tcp", "127.0.0.1:0")
	addr := l.Addr().String()
	l.Close()
	_, err := (&http.Client{Timeout: 10 * time.Second}).Get("http://" + addr) // Windows refuses only after its retries
	if Kind(err) != "refused" {
		t.Errorf("refused: %v → %s", err, Kind(err))
	}
	ts := httptest.NewTLSServer(http.HandlerFunc(func(http.ResponseWriter, *http.Request) {}))
	defer ts.Close()
	_, err = (&http.Client{Timeout: time.Second, Transport: &http.Transport{TLSClientConfig: &tls.Config{}}}).Get(ts.URL)
	if Kind(err) != "tls" {
		t.Errorf("an unknown authority: %v → %s", err, Kind(err))
	}
	if Kind(errors.New("anything")) != "unreachable" {
		t.Errorf("else")
	}
}

// ssh's own arguments: an IPv6 address on the far side in brackets; a path ssh would expand, escaped
func TestForwardArgs(t *testing.T) {
	args, err := forwardArgs(config.Route{Via: "ssh", Host: "203.0.113.10", Port: 2222, User: "tunnel", To: "[::1]:8069"},
		4100, "/s/100%/g.ssh", "/s/100%/g.known_hosts")
	j := strings.Join(args, " ")
	if err != nil || !strings.Contains(j, "-L 127.0.0.1:4100:[::1]:8069 -- 203.0.113.10") || !strings.Contains(j, "-p 2222") ||
		!strings.Contains(j, "-i /s/100%%/g.ssh") || !strings.Contains(j, `UserKnownHostsFile="/s/100%%/g.known_hosts"`) {
		t.Fatalf("%v %s", err, j)
	}
	if _, err := forwardArgs(config.Route{Via: "ssh", Host: "h", User: "u", To: "127.0.0.1:8069"}, 1, `/a"b`, "/k"); err == nil {
		t.Fatalf("a path ssh would read otherwise is not handed to it")
	}
}
