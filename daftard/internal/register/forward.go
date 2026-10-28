package register

import (
	"bufio"
	"fmt"
	"io"
	"net"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/proc"
)

// forward runs an ssh route: the system's ssh client, forwarding a loopback port daftard picks to the route's `to`
// on the far side, started again whenever it ends — at once after a connection that lasted, backing off while it
// keeps failing — until Close, which ends it.
func (rs *Routes) forward(r *route) {
	back := FirstBack
	for {
		start := time.Now()
		cmd, port, read, why := rs.startSSH(r)
		if cmd != nil {
			rs.mu.Lock()
			r.cmd, r.pid, r.started, r.url = cmd, cmd.Process.Pid, start, "http://127.0.0.1:"+strconv.Itoa(port)
			rs.mu.Unlock()
			rs.logf("%s: forward on 127.0.0.1:%d (ssh pid %d)", r.label(), port, cmd.Process.Pid)
			ended := make(chan error, 1)
			go func() { <-read; ended <- cmd.Wait() }() // what ssh wrote is read whole before it is waited for
			probe := time.NewTicker(time.Second)        // a forward just started is asked each second until it answers
			until := time.After(Starting)
		waiting:
			for {
				select {
				case <-rs.stop:
					probe.Stop()
					_ = cmd.Process.Kill()
					<-ended
					rs.down(r, "daftard stopped")
					return
				case err := <-ended:
					why = rs.ended(r, err)
					break waiting
				case <-probe.C:
					rs.mu.Lock()
					up := r.healthy
					rs.mu.Unlock()
					if !up {
						select {
						case r.asked <- struct{}{}:
						default:
						}
					}
				case <-until:
					probe.Stop()
				}
			}
			probe.Stop()
			lasted := time.Since(start)
			rs.down(r, why)
			if lasted >= Lasted {
				back = FirstBack
			}
			rs.logf("%s: forward ended after %s (%s); started again in %s", r.label(), lasted.Truncate(time.Second), why,
				back)
		} else {
			rs.down(r, why)
			rs.logf("%s: not started (%s); tried again in %s", r.label(), why, back)
		}
		select {
		case <-rs.stop:
			return
		case <-time.After(back):
		}
		if back *= 2; back > MostBack {
			back = MostBack
		}
	}
}

// down marks an ssh route as having no forward: not healthy, nothing handed to the worker, since now.
func (rs *Routes) down(r *route, why string) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	if r.healthy {
		r.since = time.Now()
		rs.logf("%s: not healthy (%s)", r.label(), why)
	}
	r.healthy, r.url, r.cmd, r.pid, r.err = false, "", nil, 0, why
}

// startSSH starts the route's ssh: the process, the port it forwards, and a channel closed once what it writes has
// been read whole — or why it was not started.
func (rs *Routes) startSSH(r *route) (*exec.Cmd, int, <-chan struct{}, string) {
	key, known := rs.key, rs.known
	if why := privateKey(key); why != "" {
		return nil, 0, nil, why
	}
	if err := config.PinnedIn(known, r.conf.Host, r.conf.SSHPort()); err != nil {
		return nil, 0, nil, "host key not pinned"
	}
	port, err := freePort()
	if err != nil {
		return nil, 0, nil, "no loopback port"
	}
	args, err := forwardArgs(r.conf, port, key, known)
	if err != nil {
		return nil, 0, nil, err.Error()
	}
	cmd := proc.Command(rs.SSH, args...)
	endWithDaftard(cmd)
	errs, err := cmd.StderrPipe()
	if err != nil {
		return nil, 0, nil, "ssh not started"
	}
	rs.mu.Lock()
	r.said, r.ending = "", ""
	rs.mu.Unlock()
	if err := cmd.Start(); err != nil {
		return nil, 0, nil, "no ssh client"
	}
	read := make(chan struct{})
	go func() { defer close(read); rs.said(r, errs) }()
	return cmd, port, read, ""
}

// said reads what ssh writes: each line to daftard.log (ssh names hosts and its own failures, never a key — and at
// LogLevel=ERROR little else), at most 20 lines a run, and the kind of the last failure it names kept to tell why it
// ended.
func (rs *Routes) said(r *route, from io.Reader) {
	sc := bufio.NewScanner(from)
	n := 0
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		if n++; n <= 20 {
			rs.logf("%s: ssh: %s", r.label(), line)
		}
		if kind := sshKind(line); kind != "ssh: failed" { // a warning (a weak key exchange, say) is no reason it ended
			rs.mu.Lock()
			r.said = kind
			rs.mu.Unlock()
		}
	}
}

// ended says why a forward ended: daftard ended it, or the kind of what ssh said last, else its exit.
func (rs *Routes) ended(r *route, err error) string {
	rs.mu.Lock()
	said, ending := r.said, r.ending
	rs.mu.Unlock()
	if ending != "" {
		return ending
	}
	if said != "" {
		return said
	}
	code := 0
	if ee, ok := err.(*exec.ExitError); ok {
		code = ee.ExitCode()
	}
	return fmt.Sprintf("ssh ended (exit %d)", code)
}

// sshKind is the kind of what ssh said: a few fixed words, so nothing of a line but its kind is kept on the route.
func sshKind(line string) string {
	l := strings.ToLower(line)
	switch {
	case strings.Contains(l, "host key verification failed"), strings.Contains(l, "remote host identification has changed"),
		strings.Contains(l, "host key for") && strings.Contains(l, "has changed"), strings.Contains(l, "no matching host key"):
		return "ssh: host key"
	case strings.Contains(l, "bad permissions"), strings.Contains(l, "unprotected private key"),
		strings.Contains(l, "no such identity"), strings.Contains(l, "load key"):
		return "ssh: key file"
	case strings.Contains(l, "permission denied"):
		return "ssh: key refused"
	case strings.Contains(l, "could not resolve"), strings.Contains(l, "name or service not known"):
		return "ssh: dns"
	case strings.Contains(l, "connection refused"):
		return "ssh: refused"
	case strings.Contains(l, "timed out"), strings.Contains(l, "timeout"), strings.Contains(l, "not responding"):
		return "ssh: timeout"
	case strings.Contains(l, "forwarding failed"), strings.Contains(l, "prohibited"), strings.Contains(l, "bind"):
		return "ssh: forward refused"
	case strings.Contains(l, "reset"), strings.Contains(l, "broken pipe"), strings.Contains(l, "closed by remote"),
		strings.Contains(l, "connection closed"):
		return "ssh: reset"
	}
	return "ssh: failed"
}

// privateKey says why a route's key file cannot be used, "" where it can: there, and readable by this user alone.
func privateKey(file string) string {
	st, err := os.Stat(file)
	if err != nil || !st.Mode().IsRegular() {
		return "no ssh key"
	}
	if st.Mode().Perm()&0o077 != 0 && !windows {
		return "ssh key readable by others: make it 0600"
	}
	return ""
}

// freePort is a loopback port nothing listens on now: the forward's own, picked by daftard.
func freePort() (int, error) {
	l, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		return 0, err
	}
	defer l.Close()
	return l.Addr().(*net.TCPAddr).Port, nil
}

// forwardArgs are the ssh client's arguments for a route: a forward of this machine's 127.0.0.1:<port> to `to` on the
// far side and nothing else — no command, no terminal, no agent, no other forward, no configuration file of the
// user's or the machine's — trusting only the host's pinned key, offering only the route's own key, ended by its
// keepalives when the link falls silent. Each is its own argument: no shell reads them.
func forwardArgs(c config.Route, port int, key, knownHosts string) ([]string, error) {
	host, toPort, err := config.SplitTo(c.To)
	if err != nil {
		return nil, err
	}
	if ip := net.ParseIP(host); ip != nil && ip.To4() == nil {
		host = "[" + host + "]"
	}
	if strings.ContainsAny(key+knownHosts, "\"\r\n") {
		return nil, fmt.Errorf("the state folder's path cannot be handed to ssh")
	}
	pct := strings.NewReplacer("%", "%%") // ssh expands %-tokens in these two paths
	return []string{"-N", "-F", "none",
		"-o", "BatchMode=yes", "-o", "PreferredAuthentications=publickey",
		"-o", "IdentitiesOnly=yes", "-o", "IdentityAgent=none", "-i", pct.Replace(key),
		"-o", "StrictHostKeyChecking=yes", "-o", `UserKnownHostsFile="` + pct.Replace(knownHosts) + `"`,
		"-o", "GlobalKnownHostsFile=none", "-o", "UpdateHostKeys=no", "-o", "CheckHostIP=no",
		"-o", "ExitOnForwardFailure=yes", "-o", "ForwardAgent=no", "-o", "ForwardX11=no",
		"-o", "PermitLocalCommand=no", "-o", "ControlMaster=no", "-o", "ControlPath=none",
		"-o", "ConnectTimeout=20", "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=3",
		"-o", "TCPKeepAlive=no", "-o", "Compression=yes", "-o", "LogLevel=ERROR",
		"-p", strconv.Itoa(c.SSHPort()), "-l", c.User,
		"-L", fmt.Sprintf("127.0.0.1:%d:%s:%d", port, host, toPort),
		"--", c.Host}, nil
}
