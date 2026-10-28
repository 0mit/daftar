// Package register keeps the ROUTES by which daftard reaches a garden's register (daftard.json's `register`; design
// §10.2, §15.6; python/register.py reads it) — and, the same way, its place service (`place_service`, design §12: a
// Photon, asked by internal/web's place lookups). A register's host may sit behind an unstable link — one where a
// short connection now and then fails, and a long-lived one is cut — so a register may be named by more than one
// route, in the order they are to be tried: its own address by TLS, then a forward through its host by ssh. This
// package keeps them, so that no loop outside daftard has to (what follows says "the register"; a place service's
// routes are kept alike, its health asked at its own /status, its ssh by the garden's same key and pins):
//
//   - THE HEALTH OF EACH ROUTE: the register's own /web/health, asked with no key through the route every 20 s, and
//     soon again after any miss; a read that did not reach the register by a route (the worker says so) is a miss as
//     well, and asks a check at once. A route is healthy until it misses twice in a row, and healthy again at its next
//     answer.
//   - THE ORDER READS GO BY (Hand): the healthy routes in the order daftard.json gives them, a route that has just
//     missed after those that have not. The worker reads by the first, and asks a read that failed at the connection
//     once more by the next (python/register.py); a route that is not healthy is not handed to it at all.
//   - THE SSH ROUTE, RUN BY DAFTARD: the system's ssh client (OpenSSH, on Linux, macOS and Windows 10+), forwarding a
//     loopback port daftard picks to the register's port on the far side, and nothing else; its keepalives end a
//     silent link, a route that misses twice has its ssh ended, and an ssh that ended is started again — at once after a
//     connection that lasted, backing off to a minute while it keeps failing. It ends with daftard. Its key and its
//     host's pinned key are files in the state folder (config.Register.SSHKeyFile, KnownHostsFile), handed to ssh by
//     their paths: never in daftard.json, a log, a page or an error.
//   - WHAT IS SEEN (State): each route, healthy or not, since when, the kind of its last error, and which route
//     answered last — on daftard's /health and in `daftard status` — and in daftard.log each transition, never a key
//     and never a record.
package register

import (
	"crypto/tls"
	"crypto/x509"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/proc"
)

// How often and how long routes are asked. Variables, so a test can make them short.
var (
	Every       = 20 * time.Second // a route that answered is asked again this long after
	Soon        = 5 * time.Second  // a route that missed, this soon
	Wait        = 8 * time.Second  // a check waits this long for its answer
	OnDemandGap = 2 * time.Second  // a route is checked on demand at most this often
	FirstBack   = 5 * time.Second  // an ssh that ended is started again after this, doubling while it keeps failing,
	MostBack    = time.Minute      // up to this,
	Lasted      = 2 * time.Minute  // and back to the first after a connection that lasted this long
	Starting    = 25 * time.Second // a forward just started is checked each second for this long, until it answers
)

// Misses is how many misses in a row make a route not healthy.
const Misses = 2

// Routes are one garden's routes to its register, or to its place service.
type Routes struct {
	Garden string
	SSH    string // the ssh client ("ssh", found on the PATH); a test stands in
	what   string // "register" or "place service": how daftard.log names the routes
	health string // the path a route's health is asked at, with no key: the register's /web/health, Photon's /status
	ways   []config.Route
	key    string // the garden's ssh key and its pinned host keys, for its ssh routes (config.SSHKeyFile, KnownHostsFile)
	known  string
	log    func(string, ...any)
	client *http.Client
	mu     sync.Mutex
	routes []*route
	last   struct {
		route int
		at    time.Time
	}
	stop chan struct{}
	wg   sync.WaitGroup
	once sync.Once
}

type route struct {
	n       int // its place in the order, from 1
	conf    config.Route
	url     string // where it answers on this machine: its https address, or its forward's http://127.0.0.1:<port>
	healthy bool
	since   time.Time
	misses  int
	err     string // the kind of its last error
	asked   chan struct{}
	lastAsk time.Time
	// an ssh route's forward
	cmd     *exec.Cmd
	pid     int
	started time.Time
	said    string // the kind of what its ssh said last
	ending  string // why daftard ended its ssh, where it did
}

// New keeps the routes of a garden's register; Run starts them.
func New(garden string, conf *config.Register, logf func(string, ...any)) *Routes {
	return keep(garden, "register", "/web/health", conf.Ways(), logf)
}

// NewPlaces keeps the routes of a garden's place service; Run starts them. Its health is Photon's /status, asked
// with nothing typed; its ssh routes go with the garden's one ssh key and pinned host keys, as its register's do.
func NewPlaces(garden string, conf *config.PlaceService, logf func(string, ...any)) *Routes {
	return keep(garden, "place service", "/status", conf.Ways(), logf)
}

func keep(garden, what, health string, ways []config.Route, logf func(string, ...any)) *Routes {
	t := &http.Transport{Proxy: nil, DisableKeepAlives: true, TLSHandshakeTimeout: Wait, ResponseHeaderTimeout: Wait,
		DialContext: (&net.Dialer{Timeout: Wait}).DialContext}
	rs := &Routes{Garden: garden, SSH: "ssh", what: what, health: health, ways: ways, key: config.SSHKeyFile(garden),
		known: config.KnownHostsFile(garden), log: logf, stop: make(chan struct{}),
		client: &http.Client{Transport: t, Timeout: Wait, CheckRedirect: func(*http.Request, []*http.Request) error {
			return http.ErrUseLastResponse // a route's health is its own answer, never another address's
		}}}
	now := time.Now()
	for i, w := range ways {
		r := &route{n: i + 1, conf: w, since: now, asked: make(chan struct{}, 1)}
		if w.Via == "https" { // healthy until it misses twice; an ssh route, once its forward answers
			r.url, r.healthy = strings.TrimRight(w.URL, "/"), true
		}
		rs.routes = append(rs.routes, r)
	}
	return rs
}

// label is a route as daftard.log and `daftard status` name it.
func (r *route) label() string {
	if r.conf.Via == "ssh" {
		return fmt.Sprintf("%d (ssh %s@%s:%d → %s)", r.n, r.conf.User, r.conf.Host, r.conf.SSHPort(), r.conf.To)
	}
	return fmt.Sprintf("%d (%s)", r.n, strings.TrimRight(r.conf.URL, "/"))
}

func (rs *Routes) logf(format string, a ...any) {
	if rs.log != nil {
		rs.log("["+rs.Garden+"] "+rs.what+" route "+format, a...)
	}
}

// Run checks each route and runs each ssh route's forward until Close.
func (rs *Routes) Run() {
	for _, r := range rs.routes {
		r := r
		rs.logf("%s: %s", r.label(), map[bool]string{true: "taken as healthy until it misses twice",
			false: "started by daftard"}[r.conf.Via == "https"])
		rs.wg.Add(1)
		go func() { defer rs.wg.Done(); rs.watch(r) }()
		if r.conf.Via == "ssh" {
			rs.wg.Add(1)
			go func() { defer rs.wg.Done(); rs.forward(r) }()
		}
	}
}

// Close ends every forward and check, waiting for them a few seconds at most.
func (rs *Routes) Close() {
	rs.once.Do(func() { close(rs.stop) })
	done := make(chan struct{})
	go func() { rs.wg.Wait(); close(done) }()
	select {
	case <-done:
	case <-time.After(5 * time.Second):
	}
}

// Hand is the routes the worker reads by, in the order it is to try them — [{"route": n, "url": …}]: each healthy
// route, those that have not just missed first, each group in the order daftard.json gives; and after them, as the
// last a failed read may be asked once more of, each https route that is not healthy — its health is as old as its
// last check (Soon, while it misses), and it may be back. Never an ssh route that is not healthy: its port is
// daftard's own only while its forward runs and answers. None: no route is healthy now, and the worker says so at
// once rather than wait on routes known to be down.
func (rs *Routes) Hand() []map[string]any {
	out := []map[string]any{}
	for _, w := range rs.Order() {
		h := map[string]any{"route": w.Route, "url": w.URL}
		if w.Down {
			h["down"] = true
		}
		out = append(out, h)
	}
	return out
}

// Way is one route in the order a read tries them: its place in daftard.json's order, where it answers on this
// machine, and whether it is the last resort, an https route that is not healthy.
type Way struct {
	Route int
	URL   string
	Down  bool
}

// Order is Hand's order, for a caller in daftard itself (a place lookup): the healthy routes, fresh before suspect,
// then each https route that is not healthy; none where no route is healthy.
func (rs *Routes) Order() []Way {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	out := []Way{}
	for _, fresh := range []bool{true, false} {
		for _, r := range rs.routes {
			if r.healthy && r.url != "" && (r.misses == 0) == fresh {
				out = append(out, Way{Route: r.n, URL: r.url})
			}
		}
	}
	if len(out) == 0 {
		return out
	}
	for _, r := range rs.routes {
		if !r.healthy && r.conf.Via == "https" {
			out = append(out, Way{Route: r.n, URL: r.url, Down: true})
		}
	}
	return out
}

// Note takes what the worker found reading by the routes it was handed (python/register.py's notes): a route that
// answered, one a read did not reach (a miss, and a check asked at once), or that none was healthy (every route
// checked at once).
func (rs *Routes) Note(notes []Note) {
	for _, n := range notes {
		if n.None {
			for _, r := range rs.routes {
				rs.ask(r)
			}
			continue
		}
		r := rs.route(n.Route)
		if r == nil {
			continue
		}
		if n.Answered {
			rs.mu.Lock()
			rs.last.route, rs.last.at = r.n, time.Now()
			rs.mu.Unlock()
			continue
		}
		if n.Missed != "" {
			rs.missed(r, "read: "+kindWord(n.Missed))
			rs.ask(r)
		}
	}
}

// Noted takes the worker's notes as its answer carries them (worker.Worker.Noted); what it cannot read, it ignores.
func (rs *Routes) Noted(raw json.RawMessage) {
	var notes []Note
	if json.Unmarshal(raw, &notes) == nil {
		rs.Note(notes)
	}
}

// Note is one thing the worker found of a route.
type Note struct {
	Route    int    `json:"route"`
	Answered bool   `json:"answered"`
	Missed   string `json:"missed"` // the kind of the failure: refused, reset, timeout, tls, dns, unreachable
	None     bool   `json:"none"`   // it was handed no healthy route
}

func (rs *Routes) route(n int) *route {
	for _, r := range rs.routes {
		if r.n == n {
			return r
		}
	}
	return nil
}

// kindWord keeps a kind the worker names to the few words this package uses, so nothing else is shown or logged.
func kindWord(k string) string {
	switch k {
	case "refused", "reset", "timeout", "tls", "dns", "unreachable":
		return k
	}
	return "unreachable"
}

// ask asks a check of the route soon, unless one was asked a moment ago.
func (rs *Routes) ask(r *route) {
	rs.mu.Lock()
	if time.Since(r.lastAsk) < OnDemandGap {
		rs.mu.Unlock()
		return
	}
	r.lastAsk = time.Now()
	rs.mu.Unlock()
	select {
	case r.asked <- struct{}{}:
	default:
	}
}

// watch checks one route on its cadence and on demand.
func (rs *Routes) watch(r *route) {
	next := time.Duration(0)
	for {
		t := time.NewTimer(next)
		select {
		case <-rs.stop:
			t.Stop()
			return
		case <-r.asked:
			t.Stop()
		case <-t.C:
		}
		rs.mu.Lock()
		url := r.url
		rs.mu.Unlock()
		if url == "" { // an ssh route with no forward running: nothing to ask; its forward says when it is up
			next = Every
			continue
		}
		if kind := rs.check(r, url); kind == "" {
			rs.answered(r)
			next = Every
		} else {
			rs.missed(r, kind)
			next = Soon
		}
	}
}

// check asks the route for the register's health (or the place service's), with no key: "" where it answered, else
// the kind of the miss.
func (rs *Routes) check(r *route, url string) string {
	if r.conf.Via == "ssh" { // its port is daftard's own forward's: never another account's that took it meanwhile
		_, port, _ := net.SplitHostPort(strings.TrimPrefix(url, "http://"))
		for _, uid := range proc.ListenerUIDs("127.0.0.1:" + port) {
			if uid != os.Getuid() {
				return "port taken by another account"
			}
		}
	}
	resp, err := rs.client.Get(url + rs.health)
	if err != nil {
		return Kind(err)
	}
	defer resp.Body.Close()
	_, _ = io.Copy(io.Discard, io.LimitReader(resp.Body, 64<<10))
	if resp.StatusCode != http.StatusOK {
		return "status " + strconv.Itoa(resp.StatusCode)
	}
	return ""
}

func (rs *Routes) answered(r *route) {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	if r.url == "" {
		return // the forward ended while the check was under way
	}
	r.misses = 0
	if !r.healthy {
		r.healthy, r.since = true, time.Now()
		rs.logf("%s: healthy (it answers)", r.label())
	}
}

func (rs *Routes) missed(r *route, kind string) {
	rs.mu.Lock()
	r.misses++
	r.err = kind
	end := false
	if r.healthy && r.misses >= Misses {
		r.healthy, r.since = false, time.Now()
		rs.logf("%s: not healthy (missed twice: %s)", r.label(), kind)
		end = r.cmd != nil // the ssh lives on and nothing passes (a half-open link): it is ended, and started again
		if end {
			r.ending = "ended by daftard: missed twice (" + kind + ")"
		}
	} else if r.healthy {
		rs.logf("%s: missed once (%s)", r.label(), kind)
	}
	cmd := r.cmd
	rs.mu.Unlock()
	if end && cmd != nil && cmd.Process != nil {
		_ = cmd.Process.Kill()
	}
}

// Kind is the kind of a failure to reach a route: refused, reset, timeout, tls, dns or unreachable.
func Kind(err error) string {
	var ne net.Error
	var dns *net.DNSError
	var cv *tls.CertificateVerificationError
	var ua x509.UnknownAuthorityError
	var he x509.HostnameError
	var ci x509.CertificateInvalidError
	var rh tls.RecordHeaderError
	s := strings.ToLower(err.Error())
	switch {
	case errors.As(err, &dns):
		return "dns"
	case errors.As(err, &cv), errors.As(err, &ua), errors.As(err, &he), errors.As(err, &ci), errors.As(err, &rh),
		strings.Contains(s, "tls:"), strings.Contains(s, "x509:"):
		return "tls"
	case errors.As(err, &ne) && ne.Timeout():
		return "timeout"
	case errors.Is(err, syscall.ECONNREFUSED), strings.Contains(s, "refused"):
		return "refused"
	case errors.Is(err, syscall.ECONNRESET), errors.Is(err, io.EOF), errors.Is(err, io.ErrUnexpectedEOF),
		strings.Contains(s, "reset"), strings.Contains(s, "broken pipe"):
		return "reset"
	}
	return "unreachable"
}

// RouteState is one route as State shows it.
type RouteState struct {
	Route    int       `json:"route"`
	Via      string    `json:"via"`
	Label    string    `json:"label,omitempty"` // where it goes: only where whoever asks may read daftard.json's own words
	Healthy  bool      `json:"healthy"`
	Since    time.Time `json:"since"`
	Error    string    `json:"error,omitempty"` // the kind of its last error
	Answered bool      `json:"answered"`        // it is the route that answered last
}

// State is what is seen of the routes: each route, and which answered last and when. With full, where each goes.
func (rs *Routes) State(full bool) map[string]any {
	rs.mu.Lock()
	defer rs.mu.Unlock()
	list := []RouteState{}
	for _, r := range rs.routes {
		s := RouteState{Route: r.n, Via: r.conf.Via, Healthy: r.healthy, Since: r.since.UTC().Truncate(time.Second),
			Error: r.err, Answered: rs.last.route == r.n}
		if full {
			s.Label = r.label()
		}
		list = append(list, s)
	}
	out := map[string]any{"routes": list}
	if rs.last.route != 0 {
		out["answered"] = map[string]any{"route": rs.last.route, "at": rs.last.at.UTC().Truncate(time.Second)}
	}
	return out
}

// windows: no file modes to read a key's privacy by
const windows = runtime.GOOS == "windows"
