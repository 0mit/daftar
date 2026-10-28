// Package config is daftard's settings on this machine: which gardens it serves, with which Python, and each garden's
// own settings (design/DESIGN.md §1: the same tools, each garden its settings). It is JSON, daftard.json in the
// state folder, written by `daftard install` and edited by hand; it holds no garden's facts.
package config

import (
	"crypto/hmac"
	"crypto/sha1"
	"encoding/base64"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"strconv"
	"strings"

	"github.com/0mit/daftar/daftard/internal/state"
)

// FollowUp is someone a person may be sent to when something they tried did not go ahead, beyond whom the garden's
// own grants name (design §3): typically the person who looks after the garden's tools. Shown by title.
type FollowUp struct {
	Who   string `json:"who"`             // their id in the garden (a bean), as grants name them
	Title string `json:"title"`           // how they are called on screen
	Sees  string `json:"sees,omitempty"`  // what of an error's detail they may read: "all" or "summary"
	Reach string `json:"reach,omitempty"` // how to reach them, said in words ("Telegram", "call")
}

// Garden is one garden this machine serves.
type Garden struct {
	Name        string     `json:"name"`         // a short name for the handplace's address (?g=…)
	Path        string     `json:"path"`         // the garden's working copy
	Python      string     `json:"python"`       // the Python its own tools run with
	Title       string     `json:"title"`        // the handplace's title («دفتر من»)
	Gardener    string     `json:"gardener"`     // whose garden it is; read from the garden when empty
	Me          string     `json:"me"`           // how the gardener is called on screen; their bean's title when empty
	Lang        string     `json:"lang"`         // the reader's language (fa)
	Sync        bool       `json:"sync"`         // keep it in step with its hub
	SyncMinutes int        `json:"sync_minutes"` // how often, when nothing wakes it sooner (10)
	Exchange    bool       `json:"exchange"`     // run its exchange rounds with other gardens, where consented
	FollowUp    []FollowUp `json:"follow_up"`    // beyond the gardener and the grants' holders
	Remote      string     `json:"remote"`       // the remote it syncs with, which a person's labels travel by too (hub)
	Quiet       bool       `json:"quiet"`        // no notifications of what waits (the handplace still lists it)
	// Listen is the address on the loopback where this garden's own daftard answers: one daemon serves one garden
	// (the operator, 2026-10-14), each on a port of its own. None given: the machine's port and 11 plus the garden's
	// place in the list (127.0.0.1:8781 for the first where the machine listens on 8770).
	Listen string `json:"listen,omitempty"`
	// Writers are the people who may sit at this garden's handplace on this machine, each by their bean (design §6);
	// none named: its gardener. Signed: every write is the sitting person's own signed commit, and none is made with
	// nobody sitting — set where its hub takes only signed commits (bin/hub.py).
	Writers []string `json:"writers,omitempty"`
	Signed  bool     `json:"signed,omitempty"`
	// Hub is the bean of this machine's hub of the garden: what daftard writes for the garden on its own — a merge with
	// no conflict, an exchange round under a standing consent, a routine's records — is authored as that bean and signed
	// with the hub's own key (internal/hubkey), which the garden's `bin/hub.py install` makes when the hub is initialized
	// and whose fingerprint the gardener adds to that bean (class F). None named, or no key made yet: nothing is signed
	// as the hub, the hub merges nothing, and a merge waits for a person's sitting.
	Hub string `json:"hub,omitempty"`
	// Machine is the bean of the host this machine is, in this garden, for a garden that names no Hub: what the machine
	// does on its own — a merge with no conflict — is authored as that bean and signed with the machine's own key (design
	// §6.5), whose fingerprint the gardener adds to that bean. Neither named: the machine merges nothing, and a merge
	// waits for a person's sitting.
	Machine string `json:"machine,omitempty"`
	// Served offers this garden on the served listener (Config.Served): to the people its grants name, signed in by a
	// link sent through one of its mail channels, each page asked of the garden's `may` (design §10.1).
	Served bool `json:"served,omitempty"`
	// Channels carry its leads off the machine (design §8.2): each a `send` to a party, sent only while the garden's
	// flow law grants that party (a garden's own `sent-out` row, a RULE-CHANGE), and carrying a lead's sentence and its
	// address, never its material.
	Channels []Channel `json:"channels,omitempty"`
	// Routines runs this machine's routines of the garden (internal/routines): each minute the garden's own
	// bin/routines.py ticks — a routine runs here only where the garden grants this machine `enact` of its walk — and
	// each tool the garden places on this machine is probed on its cadence (never faster than ProbeSeconds, 30), its
	// readings kept 14 days and served at /api/probe. Off by default: a machine keeps its routines only where its keeper
	// says so here.
	Routines     bool `json:"routines,omitempty"`
	ProbeSeconds int  `json:"probe_seconds,omitempty"`
	// PlaceService is where this garden's place lookups may go beyond what the machine holds (design §12: a Photon,
	// self-hosted): each lookup a `send` to Party, made only while the garden's flow law grants that party (a
	// garden's own `sent-out` row, a RULE-CHANGE), carrying what the person typed and nothing of the garden — and never
	// for a place that says where a person will be. None: lookups are answered on this machine alone.
	PlaceService *PlaceService `json:"place_service,omitempty"`
	// A garden that carries no handplace code of its own is served by the BOARD of another tree (the board/ and
	// exchange/ of a garden that has them): Kind "board", Tools that tree, ExchangeDir the exchange folder. A garden that
	// carries its own (dashboard/model.py) is Kind "dashboard", the default.
	Kind        string `json:"kind"`
	Tools       string `json:"tools,omitempty"`
	ExchangeDir string `json:"exchange_dir,omitempty"`
	// Handplace is what the garden's pages are : "legacy", the default — daftard's own pages
	// (web/app/pages), as before — or "view": the garden's own page beans, each drawn and written by the view's code
	// from the release the garden runs. Until the gardener says otherwise (V6), every garden stays "legacy".
	Handplace string `json:"handplace,omitempty"`
	// Walks are the walks of the garden a page of it may start (a view garden's pages: an action's `tool`, by the name
	// it gives, to the walk run by the garden's bin/act.py): what a page may start is this machine's to say. None: a
	// page starts nothing.
	Walks map[string]string `json:"walks,omitempty"`

	// Register is an Odoo instance whose records this garden's Odoo pages read live, never copied into the garden (design
	// §10.2, §15.6): for its series, the client's data calls are asked of it, as the reader may ask them.
	Register *Register `json:"register,omitempty"`
}

// ViewHandplace says whether the garden's pages are its page beans, drawn by the view.
func (g Garden) ViewHandplace() bool { return g.Handplace == "view" }

// Channel is one way leads leave the machine: today mail, handed to `Command` (e.g. ssh <host> /usr/sbin/sendmail -t
// -oi) for the party the garden's flow law names.
type Channel struct {
	Kind    string   `json:"kind"`    // mail
	Party   string   `json:"party"`   // the bean of the party that carries it, as the garden's `sent-out` row names it
	To      string   `json:"to"`      // the address it is sent to
	From    string   `json:"from"`    // the address it is sent from
	Command []string `json:"command"` // what takes the message on its standard input
}

// PlaceService is one place search beyond the machine (a Photon: it answers /api, and /status for its health), and the
// party a lookup sent there is a `send` to, as the garden's flow law names it. It is reached as a register is, by ROUTES
// tried in order (internal/register keeps them): `url` alone is one route, as it always was; `routes` names them all —
// its own address by TLS, or http:// on this machine's own loopback, either behind a path; or a forward daftard runs
// with the system's ssh through the service's host — {"via": "ssh", "host": …, "user": …, "to": "127.0.0.1:2322"} —
// with the garden's one ssh key and its hosts' pinned keys (SSHKeyFile, KnownHostsFile), never here.
type PlaceService struct {
	URL    string  `json:"url,omitempty"`
	Routes []Route `json:"routes,omitempty"`
	Party  string  `json:"party"`
}

// Ways are the routes to the place service in the order they are tried: `routes`, or `url` alone as one.
func (p *PlaceService) Ways() []Route {
	if len(p.Routes) > 0 {
		return p.Routes
	}
	return []Route{{Via: "https", URL: p.URL}}
}

// Check refuses a place service a lookup could not be sent to safely, as a register's routes are refused: what a person
// types crossing a network in the clear (plain HTTP beyond this machine), an address with a query or a name and
// password in it, an ssh route whose host's key is not pinned in the state folder — and no party named, which the
// garden's flow law is asked of before anything is sent.
func (p *PlaceService) Check(garden string) error {
	if !registerBean.MatchString(p.Party) {
		return fmt.Errorf("place_service: %q is no bean of the garden to name as its party", p.Party)
	}
	if p.URL != "" && len(p.Routes) > 0 {
		return errors.New("place_service: name it by `url` or by `routes`, not both")
	}
	if p.URL == "" && len(p.Routes) == 0 {
		return errors.New("place_service: no address")
	}
	if len(p.Routes) > MaxRoutes {
		return fmt.Errorf("place_service: %d routes; at most %d", len(p.Routes), MaxRoutes)
	}
	for i, w := range p.Ways() {
		var err error
		switch w.Via {
		case "https":
			err = checkURL(w, true)
		case "ssh":
			err = checkSSH(garden, w)
		default:
			err = fmt.Errorf("no route %q (https or ssh)", w.Via)
		}
		if err != nil {
			return fmt.Errorf("place_service route %d: %w", i+1, err)
		}
	}
	return nil
}

// Places is this machine's own place search (design §12): the place bundles it holds (place-bundle/1 directories,
// each checked against its manifest), searched here, offline. Later bundles overlay earlier ones by code.
type Places struct {
	Bundles []string `json:"bundles"`
}

// Config is the whole of daftard.json.
type Config struct {
	Listen  string   `json:"listen"` // 127.0.0.1:8770
	Gardens []Garden `json:"gardens"`
	// Shared: one account several people use (design §6). Every write is then a person's own sitting's, and a garden's
	// pages open to its gardener's sitting alone.
	Shared bool `json:"shared,omitempty"`
	// Served is the handplace served beyond this machine, over TLS; none, daftard listens on the loopback alone.
	Served *Served `json:"served,omitempty"`
	// OdooListen is where Odoo's own client is served (design §10.2), an origin of its own on the loopback — another
	// site than the handplace, so the machine key never reaches it (security audit 2026-10-10, 2.1). 127.0.0.1:8792
	// when empty; the browser reaches it as localhost:<port>.
	OdooListen string `json:"odoo_listen,omitempty"`
	// Places is the place search this machine holds for every garden it serves; none: a garden's own places alone.
	Places *Places `json:"places,omitempty"`
}

// Served is where and as whom the served handplace answers: the address it listens on, the names it answers to and
// no other (a page asked for under another name is refused), and the certificate it answers with.
type Served struct {
	Listen string   `json:"listen"` // :8443
	Names  []string `json:"names"`  // host[:port] as a browser sends it, e.g. daftar.example.org:8443
	Cert   string   `json:"cert"`   // the certificate chain, PEM
	Key    string   `json:"key"`    // its private key, PEM
}

// Register says where a register answers and which bean of the garden records it. Its account's API key is never here:
// it is in the state folder, registers/<garden>.key, readable by the user alone (KeyFile).
//
// A register may be reached by more than one ROUTE, tried in the order given (internal/register keeps them): `url`
// alone is one route, as it always was; `routes` names them all. A route is either the register's own address, by
// TLS — {"via": "https", "url": "https://…"}, or http:// on this machine's own loopback — or a forward daftard runs
// with the system's ssh to the register's host — {"via": "ssh", "host": …, "port": 22, "user": …, "to": "127.0.0.1:8069"}
// — whose key and whose host's pinned key are in the state folder beside the API key (SSHKeyFile, KnownHostsFile),
// never here.
type Register struct {
	Series string  `json:"series"`           // the Odoo series whose client reads it: "19.0" (read through JSON-2, from 19)
	URL    string  `json:"url,omitempty"`    // where it answers: https://…, or http:// on this machine's own loopback
	Routes []Route `json:"routes,omitempty"` // or the ways to it, each tried in this order
	DB     string  `json:"db"`               // its database
	Bean   string  `json:"bean"`             // the garden's bean of it: who may read the register is who may read this bean
}

// Route is one way to a register: by its own address ("https"), or by a forward through its host ("ssh") to `to`, an
// address as that host sees it — the register's own port on that host's loopback.
type Route struct {
	Via  string `json:"via"`            // https or ssh
	URL  string `json:"url,omitempty"`  // https: https://host[:port], or http:// on this machine's own loopback
	Host string `json:"host,omitempty"` // ssh: the register's host, by name or address
	Port int    `json:"port,omitempty"` // ssh: its ssh port (22)
	User string `json:"user,omitempty"` // ssh: the account whose key may forward to `to` and do nothing else
	To   string `json:"to,omitempty"`   // ssh: host:port on the far side
}

var registerBean = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,120}$`)
var hubBean = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}$`)
var registerSeries = regexp.MustCompile(`^(\d+)\.\d+$`)
var sshHost = regexp.MustCompile(`^[A-Za-z0-9]([A-Za-z0-9-]{0,62})(\.[A-Za-z0-9]([A-Za-z0-9-]{0,62}))*$`)
var sshUser = regexp.MustCompile(`^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$`)

// MaxRoutes is how many routes a register may be reached by.
const MaxRoutes = 8

// Ways are the routes to the register in the order they are tried: `routes`, or `url` alone as one.
func (r *Register) Ways() []Route {
	if len(r.Routes) > 0 {
		return r.Routes
	}
	return []Route{{Via: "https", URL: r.URL}}
}

// Check refuses a register daftard could not read safely: plain HTTP beyond this machine (the key would cross the
// network in the clear), a series before 19 (no JSON-2), an address with a path, a query or a name and password in
// it, an ssh route whose host's key is not pinned in the state folder (KnownHostsFile: daftard's ssh trusts no host
// it has not been told), or no bean to judge readers by — each route as the one address once was.
func (r *Register) Check(garden string) error {
	if r.URL != "" && len(r.Routes) > 0 {
		return errors.New("register: name it by `url` or by `routes`, not both")
	}
	if len(r.Routes) > MaxRoutes {
		return fmt.Errorf("register: %d routes; at most %d", len(r.Routes), MaxRoutes)
	}
	for i, w := range r.Ways() {
		var err error
		switch w.Via {
		case "https":
			err = checkURL(w, false)
		case "ssh":
			err = checkSSH(garden, w)
		default:
			err = fmt.Errorf("no route %q (https or ssh)", w.Via)
		}
		if err != nil {
			return fmt.Errorf("register route %d: %w", i+1, err)
		}
	}
	m := registerSeries.FindStringSubmatch(r.Series)
	if m == nil {
		return fmt.Errorf("register: series %q is no series", r.Series)
	}
	if major, _ := strconv.Atoi(m[1]); major < 19 {
		return fmt.Errorf("register: series %s has no JSON-2 to read it by (from 19)", r.Series)
	}
	if r.DB == "" || strings.ContainsAny(r.DB, "\r\n") {
		return errors.New("register: no database named")
	}
	if !registerBean.MatchString(r.Bean) {
		return fmt.Errorf("register: %q is no bean of the garden", r.Bean)
	}
	return nil
}

// checkURL refuses an https route daftard cannot take; path: whether the address may name a path below which the
// service answers (a place service behind a proxy's path; a register answers at its root).
func checkURL(w Route, path bool) error {
	if w.Host != "" || w.Port != 0 || w.User != "" || w.To != "" {
		return errors.New("an https route is its url alone")
	}
	u, err := url.Parse(w.URL)
	if err != nil || (u.Scheme != "http" && u.Scheme != "https") || u.Hostname() == "" ||
		(!path && u.Path != "" && u.Path != "/") || u.RawQuery != "" || u.ForceQuery || u.Fragment != "" || u.User != nil {
		return fmt.Errorf("%q: an address daftard cannot read (https://host[:port], or http:// on this machine)", w.URL)
	}
	if u.Scheme == "http" && !Loopback(u.Hostname()) {
		return fmt.Errorf("%q: plain HTTP only on this machine's loopback; name it by https", w.URL)
	}
	return nil
}

func checkSSH(garden string, w Route) error {
	if w.URL != "" {
		return errors.New("an ssh route has a host, a user and where it forwards to, no url")
	}
	if !sshHost.MatchString(w.Host) && net.ParseIP(w.Host) == nil {
		return fmt.Errorf("%q is no host to reach by ssh", w.Host)
	}
	if w.Port < 0 || w.Port > 65535 {
		return fmt.Errorf("ssh port %d", w.Port)
	}
	if !sshUser.MatchString(w.User) {
		return fmt.Errorf("%q is no account to reach %s as", w.User, w.Host)
	}
	if _, _, err := SplitTo(w.To); err != nil {
		return err
	}
	return PinnedIn(KnownHostsFile(garden), w.Host, w.SSHPort())
}

// SSHPort is the route's ssh port: 22 where none is named.
func (w Route) SSHPort() int {
	if w.Port == 0 {
		return 22
	}
	return w.Port
}

// SplitTo reads an ssh route's `to`: the address on the far side it forwards to, host:port.
func SplitTo(to string) (string, int, error) {
	h, p, err := net.SplitHostPort(to)
	n, perr := strconv.Atoi(p)
	if err != nil || perr != nil || n < 1 || n > 65535 || (!sshHost.MatchString(h) && net.ParseIP(h) == nil) {
		return "", 0, fmt.Errorf("%q: forward to host:port on the far side", to)
	}
	return h, n, nil
}

// Loopback says whether a host is this machine's own: localhost or a loopback address.
func Loopback(host string) bool {
	ip := net.ParseIP(host)
	return host == "localhost" || ip != nil && ip.IsLoopback()
}

// KeyFile is where the register's account's API key is kept for a garden: the state folder, never git.
func (r *Register) KeyFile(garden string) string {
	return filepath.Join(state.Dir(), "registers", filepath.Base(garden)+".key")
}

// SSHKeyFile is the private key of a garden's ssh routes — to its register and to its place service: one key, whose
// account on the far side may forward to each and do nothing else — readable by the user alone: the state folder,
// never git, a page, a log or a command line's own text (ssh is handed its path).
func SSHKeyFile(garden string) string {
	return filepath.Join(state.Dir(), "registers", filepath.Base(garden)+".ssh")
}

// KnownHostsFile pins the keys of the hosts a garden's ssh routes reach (OpenSSH's known_hosts): ssh trusts those
// and no other, and never adds one.
func KnownHostsFile(garden string) string {
	return filepath.Join(state.Dir(), "registers", filepath.Base(garden)+".known_hosts")
}

// SSHKeyFile is the garden's ssh key, as its register's routes take it.
func (r *Register) SSHKeyFile(garden string) string { return SSHKeyFile(garden) }

// KnownHostsFile is the garden's pinned host keys, as its register's routes take them.
func (r *Register) KnownHostsFile(garden string) string { return KnownHostsFile(garden) }

// PinnedIn says why a known_hosts file pins no key for host at port, nil where it pins one: the file is there, others
// cannot change it, and a line of it names the host as ssh would look it up — `host` at 22, `[host]:port` elsewhere,
// plainly, by a pattern, or hashed — with a key, as a host key or as a certificate authority's (never @revoked).
func PinnedIn(file, host string, port int) error {
	st, err := os.Stat(file)
	if err != nil {
		return fmt.Errorf("no host key pinned for %s: %s is not there", host, filepath.Base(file))
	}
	if runtime.GOOS != "windows" && st.Mode().Perm()&0o022 != 0 {
		return fmt.Errorf("%s may be changed by others than this user: make it 0600", filepath.Base(file))
	}
	b, err := os.ReadFile(file)
	if err != nil {
		return err
	}
	name := host
	if port != 22 {
		name = "[" + host + "]:" + strconv.Itoa(port)
	}
	for _, line := range strings.Split(string(b), "\n") {
		f := strings.Fields(line)
		if len(f) > 0 && strings.HasPrefix(f[0], "@") {
			if f[0] != "@cert-authority" {
				continue // @revoked pins nothing
			}
			f = f[1:]
		}
		if len(f) < 3 || strings.HasPrefix(f[0], "#") {
			continue
		}
		if hostsMatch(f[0], name) {
			return nil
		}
	}
	return fmt.Errorf("no host key pinned for %s in %s", name, filepath.Base(file))
}

// hostsMatch is a known_hosts line's first field matched as ssh matches it: a hashed name (|1|salt|hash, HMAC-SHA1),
// or a list of patterns (* and ?), any of them negated with !, which then excludes the line.
func hostsMatch(field, name string) bool {
	if strings.HasPrefix(field, "|1|") {
		parts := strings.Split(field, "|")
		if len(parts) != 4 {
			return false
		}
		salt, err1 := base64.StdEncoding.DecodeString(parts[2])
		want, err2 := base64.StdEncoding.DecodeString(parts[3])
		if err1 != nil || err2 != nil {
			return false
		}
		m := hmac.New(sha1.New, salt)
		m.Write([]byte(name))
		return hmac.Equal(m.Sum(nil), want)
	}
	hit := false
	for _, pat := range strings.Split(field, ",") {
		neg := strings.HasPrefix(pat, "!")
		if glob(strings.ToLower(strings.TrimPrefix(pat, "!")), strings.ToLower(name)) {
			if neg {
				return false
			}
			hit = true
		}
	}
	return hit
}

// glob matches a name against an ssh pattern, where * is any run of characters and ? any one, and nothing else is
// special ([host]:port is literal).
func glob(pat, name string) bool {
	if pat == "" {
		return name == ""
	}
	switch pat[0] {
	case '*':
		for i := 0; i <= len(name); i++ {
			if glob(pat[1:], name[i:]) {
				return true
			}
		}
		return false
	case '?':
		return name != "" && glob(pat[1:], name[1:])
	}
	return name != "" && pat[0] == name[0] && glob(pat[1:], name[1:])
}

// Path is where daftard.json is.
func Path() string { return filepath.Join(state.Dir(), "daftard.json") }

// Load reads daftard.json, filling what it leaves out.
func Load() (*Config, error) {
	b, err := os.ReadFile(Path())
	if err != nil {
		return nil, err
	}
	var c Config
	if err := json.Unmarshal(b, &c); err != nil {
		return nil, err
	}
	if c.Listen == "" {
		c.Listen = "127.0.0.1:8770"
	}
	if len(c.Gardens) == 0 {
		return nil, errors.New("daftard.json names no garden")
	}
	for i := range c.Gardens {
		g := &c.Gardens[i]
		if g.SyncMinutes <= 0 {
			g.SyncMinutes = 10
		}
		if g.Lang == "" {
			g.Lang = "fa"
		}
		if g.Name == "" {
			g.Name = filepath.Base(g.Path)
		}
		if g.Remote == "" {
			g.Remote = "hub"
		}
		if g.Kind == "" {
			g.Kind = "dashboard"
		}
		switch g.Handplace {
		case "":
			g.Handplace = "legacy"
		case "legacy", "view":
		default:
			return nil, fmt.Errorf("daftard.json: garden %s: handplace %q is neither \"legacy\" nor \"view\"", g.Name, g.Handplace)
		}
		if g.Hub != "" && !hubBean.MatchString(g.Hub) { // whom its commits are by: bin/sync.py --by takes a bean's id
			return nil, fmt.Errorf("daftard.json: garden %s: hub %q is no bean's id", g.Name, g.Hub)
		}
		if g.Register != nil {
			if err := g.Register.Check(g.Name); err != nil {
				return nil, fmt.Errorf("garden %s: %w", g.Name, err)
			}
		}
		if g.PlaceService != nil {
			if err := g.PlaceService.Check(g.Name); err != nil {
				return nil, fmt.Errorf("garden %s: %w", g.Name, err)
			}
		}
	}
	if err := c.gardenListens(); err != nil {
		return nil, err
	}
	return &c, nil
}

// gardenListens gives each garden its own daemon's address where daftard.json gives none, and refuses two gardens of
// one name, two daemons at one address, and an address beyond the loopback or the machine's own.
func (c *Config) gardenListens() error {
	host, port, err := net.SplitHostPort(c.Listen)
	if err != nil {
		return fmt.Errorf("daftard.json: listen %q: %v", c.Listen, err)
	}
	base, err := strconv.Atoi(port)
	if err != nil {
		return fmt.Errorf("daftard.json: listen %q: no port", c.Listen)
	}
	names, addrs := map[string]bool{}, map[string]string{c.Listen: "the machine's own page"}
	if c.OdooListen != "" {
		addrs[c.OdooListen] = "Odoo's origin"
	}
	for i := range c.Gardens {
		g := &c.Gardens[i]
		if names[g.Name] {
			return fmt.Errorf("daftard.json: two gardens are named %s: a garden's name is its address", g.Name)
		}
		names[g.Name] = true
		if g.Listen == "" {
			g.Listen = net.JoinHostPort(host, strconv.Itoa(base+11+i))
		}
		h, _, err := net.SplitHostPort(g.Listen)
		ip := net.ParseIP(h)
		if err != nil || !(h == "localhost" || ip != nil && ip.IsLoopback()) {
			return fmt.Errorf("daftard.json: garden %s: listen %q is not this machine's loopback", g.Name, g.Listen)
		}
		if other, ok := addrs[g.Listen]; ok {
			return fmt.Errorf("daftard.json: garden %s: %s is %s already", g.Name, g.Listen, other)
		}
		addrs[g.Listen] = "garden " + g.Name + "'s"
	}
	return nil
}

// Garden is the garden of that name, or nil.
func (c *Config) Garden(name string) *Garden {
	for i := range c.Gardens {
		if c.Gardens[i].Name == name {
			return &c.Gardens[i]
		}
	}
	return nil
}

// Save writes daftard.json, private to the user.
func (c *Config) Save() error {
	if _, err := state.Ensure(); err != nil {
		return err
	}
	b, err := json.MarshalIndent(c, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(Path(), append(b, '\n'), 0o600)
}
