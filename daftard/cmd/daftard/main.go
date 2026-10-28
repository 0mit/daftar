// daftard: one per machine, and one daemon per garden it holds (design/DESIGN.md §5; the operator, 2026-10-14). The MVP serves the handplace, keeps
// each garden in step with its hub, runs its exchange rounds, and turns every refusal into a guided error.
//
//	daftard serve                 run (the logon task starts this; nothing shows a window): the machine's daftard,
//	                              which starts one daemon for each garden and keeps the machine's front door
//	daftard serve --garden <name> one garden's own daemon (the machine's daftard starts each; by hand: that one alone)
//	daftard open [garden | daftar://go/<garden>/<kind>/<id> | daftar://odoo?g=<garden>&series=<series>]
//	                              start it if it is not running, and open the handplace in the browser: at a landing
//	                              address when given one (a notification's button, a link; registered as daftar:),
//	                              or at a garden's Odoo screens (the path /odoo?g=… itself is taken too)
//	daftard leads [garden]        what waits for a person's decision, each with its landing address
//	daftard links                 register daftar: links and the notifications' app id for this user (install does it too)
//	daftard notify-test [garden]  ask the running daftard to raise a sample notice, in its user's session
//	daftard status                is it running, on which build, and each garden's last sync and exchange
//	daftard stop                  stop it; a save under way finishes first
//	daftard error <E-XXXX-XXXX>   a guided error's whole detail, for whoever looks into it
//	daftard install --garden <path> --python <python> --title <title> [--name n] [--listen 127.0.0.1:8770]
//	                              [--sync] [--exchange] [--hub <bean>] [--steward who:title:reach]
//	                              writes daftard.json (and on Windows the logon task, the desktop icon and daftar:);
//	                              with --hub, this machine's hub of the garden is initialized: its own key made by
//	                              the garden's bin/hub.py install, and the statement for the hub's bean printed
//	daftard version
package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	neturl "net/url"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"runtime/debug"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/custom"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/hubkey"
	"github.com/0mit/daftar/daftard/internal/lock"
	"github.com/0mit/daftar/daftard/internal/notify"
	"github.com/0mit/daftar/daftard/internal/proc"
	"github.com/0mit/daftar/daftard/internal/register"
	"github.com/0mit/daftar/daftard/internal/routines"
	"github.com/0mit/daftar/daftard/internal/sitting"
	"github.com/0mit/daftar/daftard/internal/state"
	"github.com/0mit/daftar/daftard/internal/syncer"
	"github.com/0mit/daftar/daftard/internal/web"
	"github.com/0mit/daftar/daftard/internal/worker"
	assets "github.com/0mit/daftar/daftard/web"
)

// Build is set at build time (-ldflags "-X main.Build=…"): the daftar commit this binary is.
var Build = "dev"

func main() {
	if os.Getenv(sitting.AskpassVar) != "" { // ssh-keygen asking for a sitting's passphrase while it signs a save
		os.Exit(sitting.AskpassMain(os.Args[1:]))
	}
	cmd := "serve"
	args := os.Args[1:]
	if len(args) > 0 {
		cmd, args = args[0], args[1:]
	}
	var err error
	switch cmd {
	case "serve":
		if len(args) == 2 && args[0] == "--garden" { // one garden's own daemon, as the machine's daftard starts it
			err = serveGarden(args[1])
		} else {
			err = serve()
		}
	case "open":
		err = open(args)
	case "status":
		err = status()
	case "leads":
		err = leads(args)
	case "links":
		err = registerLinks()
	case "notify-test":
		err = notifyTest(args)
	case "stop":
		err = stop()
	case "error":
		err = showError(args)
	case "install":
		err = install(args)
	case "prefs":
		err = prefsCmd(args)
	case "version":
		fmt.Println("daftard", Build)
	default:
		err = fmt.Errorf("unknown command %q (serve, open, leads, links, notify-test, status, stop, error, install, prefs, version)", cmd)
	}
	if err != nil {
		state.Logger().Printf("%s: %v", cmd, err)
		fmt.Fprintln(os.Stderr, "daftard:", err)
		os.Exit(1)
	}
}

func baseURL(c *config.Config) string { return "http://" + c.Listen }

// listenerUIDs are the accounts listening at an address (proc.ListenerUIDs; a test stands in for them).
var listenerUIDs = proc.ListenerUIDs

// foreign says why daftard's own address is not this account's daftard: another account listens there. Such a listener
// is sent nothing — not the machine's key, not the browser — and is never taken for daftard already running (found
// while fixing security audit 2026-10-10, 2.7: the command line sent the key, and `open` the browser, to whatever
// answered at `listen`, and `serve` returned quietly). Where nothing can be told (not Linux), nil: the machine is
// taken to be one account's.
func foreign(c *config.Config) error { return foreignAt(c.Listen) }

// foreignAt is foreign for any of daftard's addresses: the front door's, or a garden's own daemon's.
func foreignAt(addr string) error {
	me := os.Getuid()
	for _, uid := range listenerUIDs(addr) {
		if uid != me {
			return fmt.Errorf("another account (uid %d) listens at %s, daftard's own address: nothing is sent to it — "+
				"stop whatever it is, or give daftard another listen", uid, addr)
		}
	}
	return nil
}

func health(c *config.Config) map[string]any {
	cl := &http.Client{Timeout: 3 * time.Second}
	resp, err := cl.Get(baseURL(c) + "/health")
	if err != nil {
		return nil
	}
	defer resp.Body.Close()
	var h map[string]any
	if json.NewDecoder(resp.Body).Decode(&h) != nil {
		return nil
	}
	return h
}

// serveGarden is one garden's own daftard (one daemon per garden, the operator 2026-10-14): it holds the garden — its
// worker, its answers in memory, its sync, routines and register — and answers its pages on its own loopback address.
// It takes the garden's lock first: a second daemon for the same garden is refused, naming the first. Started by the
// machine's daftard (serve), it ends when that one is gone; started by hand, it runs alone.
func serveGarden(name string) error {
	c, err := config.Load()
	if err != nil {
		return fmt.Errorf("%v (run `daftard install` first: %s)", err, config.Path())
	}
	gc0 := c.Garden(name)
	if gc0 == nil {
		return fmt.Errorf("daftard.json names no garden %s", name)
	}
	state.LogTo("garden-" + name + ".log")
	held, err := lock.Garden(gc0.Path)
	if err != nil {
		return err
	}
	defer held.Release()
	ln, err := net.Listen("tcp", gc0.Listen)
	if err != nil {
		return err
	}
	dir, err := state.Ensure()
	if err != nil {
		return err
	}
	// A windowless binary has nowhere to print a crash: a fatal one is written to its crash log in the state folder,
	// so daftard never dies without a trace.
	if f, err := os.OpenFile(filepath.Join(dir, "crash-"+name+".log"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600); err == nil {
		_ = debug.SetCrashOutput(f, debug.CrashOptions{})
	}
	script, err := writePython(dir)
	if err != nil {
		return err
	}
	token, err := state.Token()
	if err != nil {
		return err
	}
	log := state.Logger()
	if proc.GitFromCache() { // measured before the cache is dropped from where git is looked for (security audit 2.12)
		log.Printf("git: %s — another program's cache, not an install of Git; install Git for Windows", proc.Git())
	} else {
		log.Printf("git: %s", proc.Git())
	}
	stopAll := make(chan struct{})
	s := &web.Server{Listen: gc0.Listen, Own: name, Front: c.Listen, Token: token, CSRF: state.Random(24), Build: Build,
		Assets: assets.FS, Errors: guided.Open(), Notify: notify.Raise(log.Printf)} // DAFTARD_NOTIFY=off: the log's alone
	// who sits at the keyboard (design §6): each person's key kept here under their passphrase, the sittings begun,
	// and this binary as ssh-keygen's askpass, answered on this listener by one-time tokens
	exe, _ := os.Executable()
	s.Keys = &sitting.Keys{Dir: filepath.Join(dir, "keys")}
	s.OdooDir = filepath.Join(dir, "odoo") // each series' client, taken by importers/odoo/client.py --out <it>/<series>
	// Odoo's own origin is the machine's daftard's (one per machine): a seat is issued at its door, where it is redeemed
	if _, port, err := net.SplitHostPort(odooAddress(c)); err == nil {
		s.Odoo = web.NewOdooDoor("localhost:" + port)
		s.Odoo.Issuer = web.FrontIssuer(c.Listen, token)
	}
	s.Sittings = sitting.NewSittings(30 * time.Minute)
	s.Askpass = sitting.NewAskpass()
	s.Askpass.Exe, s.Askpass.Base = exe, "http://"+gc0.Listen
	s.Shared = c.Shared
	if c.Places != nil && len(c.Places.Bundles) > 0 { // this machine's place search, loaded beside what starts now
		s.Places = web.NewPlaceIndex(c.Places.Bundles, log.Printf)
	}
	notify.Opener = func(url string) { _ = open([]string{url}) }
	for _, gc := range []config.Garden{*gc0} {
		w := worker.New(gc, script)
		g := &web.Garden{Conf: gc, Worker: w, Version: Build}
		if gc.Register != nil { // the routes to its register, their health and its ssh forwards: daftard's own
			g.Register = register.New(gc.Name, gc.Register, log.Printf)
			w.Noted = g.Register.Noted // what the worker found of each route, as it reads by them
			g.Register.Run()
		}
		if gc.PlaceService != nil { // the routes to its place service, kept as its register's are
			g.PlaceRoutes = register.NewPlaces(gc.Name, gc.PlaceService, log.Printf)
			g.PlaceRoutes.Run()
		}
		if raw, err := w.Call("hello", nil, 2*time.Minute); err == nil {
			var hi map[string]any
			_ = json.Unmarshal(raw, &hi)
			if head, ok := hi["head"].(string); ok && len(head) >= 12 {
				g.Version = Build + "+" + head[:12]
			}
			if g.Conf.Gardener == "" {
				g.Conf.Gardener, _ = hi["gardener"].(string)
			}
			if g.Conf.Me == "" {
				g.Conf.Me, _ = hi["me"].(string)
			}
		} else {
			log.Printf("[%s] hello: %v", gc.Name, err)
		}
		g.Custom = custom.New(gc.Path, gc.Remote)
		g.Custom.SignedOnly = gc.Signed // its hub takes only a person's own signed labels
		watcher := leadWatchers(g, dir, log.Printf)
		// this machine's hub of the garden, and its key: what daftard writes for the garden on its own is the hub's
		hubParams := hubOf(g, dir, s.Keys, log.Printf)
		if gc.Sync || gc.Exchange { // a garden with no hub still has its exchange rounds
			g.Syncer = syncer.New(w, time.Duration(gc.SyncMinutes)*time.Minute, gc.Exchange, gc.Sync)
			g.Syncer.Params = hubParams // a merge with no conflict, a proposal a standing consent takes: the hub's
			store, person, name := g.Custom, g.Conf.Gardener, gc.Name
			// a board that runs this garden's code is another garden's daemon: it sees the new code itself (toolsWatch)
			g.Syncer.After = func(step string, newCode bool) {
				if watcher != nil {
					watcher.Check() // what the step brought, or a hub that parted: announced once each
				}
				if step == "error" {
					return // the hub is out of reach: the next step carries the labels
				}
				// the reader's own labels travel by the same hub, after the garden
				if changed, err := store.Sync(person); errors.Is(err, custom.ErrWaits) {
					// apart on two machines: merged in the person's next sitting, signed by them
				} else if err != nil {
					log.Printf("[%s] labels: %v", name, err)
				} else if changed {
					log.Printf("[%s] labels: taken from the hub", name)
				}
			}
			go g.Syncer.Run(stopAll)
		} else if watcher != nil {
			go func() { // no sync loop to follow: look every ten minutes
				t := time.NewTicker(10 * time.Minute)
				defer t.Stop()
				watcher.Check()
				for {
					select {
					case <-stopAll:
						return
					case <-t.C:
						watcher.Check()
					}
				}
			}()
		}
		if gc.Routines { // this machine's routines of the garden, and its tools' readings (internal/routines)
			every := time.Duration(gc.ProbeSeconds) * time.Second
			if every <= 0 {
				every = 30 * time.Second
			}
			// a worker of its own: a routine's step may run for minutes (a copy in slices), and the handplace's pages must
			// not wait on it; two workers' saves queue on the garden's own save lock, as any two writers' do
			rw := worker.New(gc, script)
			g.Routines = &routines.Runner{W: rw, Garden: gc.Name, State: dir, ProbeEvery: every, SeriesDays: 14,
				Log: log.Printf, Params: hubParams, Close: rw.Close}
			if watcher != nil {
				g.Routines.After = watcher.Check
			}
			go g.Routines.Run(stopAll)
			log.Printf("[%s] routines: this machine's run here, its tools probed every %s at the fastest", gc.Name, every)
		}
		if gc.Tools != "" { // a board runs another garden's code: its worker reads with that code's newest commit
			go toolsWatch(gc, w, log.Printf, stopAll)
		}
		s.Gardens = append(s.Gardens, g)
	}
	h := s.Handler()
	s.Watch(stopAll)
	s.Log = log.Printf
	srv := &http.Server{Handler: h, ReadHeaderTimeout: 10 * time.Second}
	done := make(chan struct{})
	var stopNow func()
	var stopping sync.Once // `daftard stop` and a signal may both ask: daftard stops once
	s.Stop = func() { stopping.Do(stopNow) }
	stopNow = func() {
		close(stopAll)
		ctxDone := make(chan struct{})
		go func() {
			_ = srv.Close()
			close(ctxDone)
		}()
		<-ctxDone
		for _, g := range s.Gardens {
			g.Worker.Close() // waits for a call under way: a save finishes, none begins
			if g.Routines != nil && g.Routines.Close != nil {
				g.Routines.Close() // the routines' own worker, likewise
			}
			if g.Register != nil {
				g.Register.Close() // its ssh forwards end with daftard
			}
			if g.PlaceRoutes != nil {
				g.PlaceRoutes.Close() // and its place service's
			}
		}
		close(done)
	}
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM) // a stop asked by the system, as `daftard stop` asks it
	go func() { <-sig; s.Stop() }()
	if os.Getenv(frontVar) != "" { // started by the machine's daftard: ended when it is gone, however it went
		go frontWatch(os.Getenv(frontVar), s.Stop, log.Printf, stopAll)
	}
	log.Printf("daftard %s serving garden %s on %s", Build, name, gc0.Listen)
	if err := srv.Serve(ln); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	<-done
	notify.Stop() // the notices still waiting on the desktop end with it
	log.Printf("daftard stopped")
	return nil
}

// hubOf finds this machine's hub of the garden — its bean (daftard.json `hub`) and the key the garden's bin/hub.py
// install made for it in the state folder `stateDir` — and returns what a step daftard takes on its own for the garden
// is asked with: the hub's bean, whom the commit is by, and the hub's signing (internal/hubkey). nil, with a line in
// the log, where the garden names a hub that has no usable key: then nothing daftard writes is signed as the hub, a
// merge waits for a person, and a round is written as before. And each step asks whether the garden, at its last
// commit, names the key on the hub's bean: a hub judges a merge's writer at its first parent, so a merge signed by a
// key that commit does not name would be refused there, and kept here — the clone and its hub parted for good. Until
// the gardener's commit names it, the step is asked with nothing to sign, and a merge waits; the log says when that
// changes, once each way. A garden that names no hub keeps the machine's own key, where it names its `machine`.
func hubOf(g *web.Garden, stateDir string, keys *sitting.Keys, logf func(string, ...any)) func() map[string]any {
	gc := g.Conf
	if gc.Hub == "" {
		return machineParams(gc, keys, logf)
	}
	k, err := hubkey.Find(stateDir, gc.Path)
	if errors.Is(err, hubkey.ErrNone) {
		logf("[%s] its hub %s has no key on this machine yet — `%s %s install %s` makes it; until then it signs "+
			"nothing, and a merge waits for a person", gc.Name, gc.Hub, gc.Python, filepath.Join(gc.Path, "bin", "hub.py"), gc.Path)
		return nil
	} else if err != nil {
		logf("[%s] its hub %s: %v — it signs nothing", gc.Name, gc.Hub, err)
		return nil
	}
	g.HubKey = &k
	logf("[%s] the hub is %s, its key %s (on its bean: %s)", gc.Name, gc.Hub, k.Fingerprint, k.Statement())
	bean, name, path := gc.Hub, gc.Name, gc.Path
	var mu sync.Mutex
	said := ""
	return func() map[string]any {
		named, err := k.Named(path, bean)
		now := "named"
		switch {
		case err != nil:
			now = "unread: " + err.Error()
		case !named:
			now = "not named"
		}
		mu.Lock()
		if now != said {
			said = now
			if now == "named" {
				logf("[%s] its hub %s's key is named on its bean: what daftard writes on its own is signed as the hub", name, bean)
			} else {
				logf("[%s] its hub %s's key is %s on its bean at the last commit (%s): it signs nothing, and a merge waits "+
					"for a person, until the gardener's commit names it", name, bean, now, k.Statement())
			}
		}
		mu.Unlock()
		if now != "named" {
			return nil
		}
		return k.Params(bean, name)
	}
}

// machineParams is what a step the machine takes on its own is asked with: the host bean it acts as and the signing of
// its own key (design §6.5) — a merge with no conflict, a routine's moves. nil where the garden names no machine, or
// the machine has no key: then nothing it does is signed as the machine.
func machineParams(gc config.Garden, keys *sitting.Keys, logf func(string, ...any)) func() map[string]any {
	if gc.Machine == "" {
		return nil
	}
	fp, err := keys.Machine()
	if err != nil {
		logf("[%s] the machine's key: %v — it signs nothing on its own", gc.Name, err)
		return nil
	}
	logf("[%s] the machine acts as %s, its key %s (on %s's bean: name: { by: ssh, of: self, as: \"%s\" })",
		gc.Name, gc.Machine, fp, gc.Machine, fp)
	host, gname := gc.Machine, gc.Name
	return func() map[string]any {
		sign := map[string]string{}
		for _, kv := range keys.MachineSignEnv(host, host+"@"+gname+".daftar.invalid") {
			if k, v, ok := strings.Cut(kv, "="); ok {
				sign[k] = v
			}
		}
		return map[string]any{"by": host, "sign": sign}
	}
}

// leadWatcher announces a garden's new leads through the platform's notifications, naming whose garden it is; nil
// for a garden that asked for quiet.
// leadWatchers are a garden's watchers: its notices on this machine, and on each channel off it that its flow law
// grants (asked of the garden through its worker; a channel it does not grant sends nothing, and says so once).
func leadWatchers(g *web.Garden, dir string, logf func(string, ...any)) notify.Group {
	var out notify.Group
	base := leadWatcher(g, dir, logf)
	if base == nil {
		return nil
	}
	out = append(out, base)
	for _, ch := range g.Conf.Channels {
		if ch.Kind != "mail" || len(ch.Command) == 0 || ch.To == "" || ch.Party == "" {
			logf("[%s] channel %q: not a mail channel with a party, an address and a command; nothing is sent", g.Conf.Name, ch.Party)
			continue
		}
		raw, err := g.Worker.Call("may_send", map[string]any{"party": ch.Party}, time.Minute)
		var said struct {
			Granted bool     `json:"granted"`
			Grant   string   `json:"grant"`
			Rows    []string `json:"rows"`
		}
		if err != nil || json.Unmarshal(raw, &said) != nil || !said.Granted {
			logf("[%s] channel to %s: the garden's flow law does not grant it (%s %v): nothing is sent", g.Conf.Name, ch.Party, said.Grant, said.Rows)
			continue
		}
		ch := ch
		w := &notify.Watcher{Garden: base.Garden, Whose: base.Whose, Leads: base.Leads, Log: base.Log,
			Path: filepath.Join(dir, "notified-"+g.Conf.Name+"-"+ch.Party+".json"), Compose: notify.MailNotices}
		w.Show = func(n notify.Notice) error {
			from := ch.From
			if from == "" {
				from = "daftard <daftard@localhost>"
			}
			ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
			defer cancel()
			c := proc.CommandContext(ctx, ch.Command[0], ch.Command[1:]...)
			c.Stdin = bytes.NewReader(notify.Mail(n, from, ch.To))
			if out, err := c.CombinedOutput(); err != nil {
				return fmt.Errorf("%v %s", err, strings.TrimSpace(string(out)))
			}
			return nil
		}
		out = append(out, w)
	}
	return out
}

func leadWatcher(g *web.Garden, dir string, logf func(string, ...any)) *notify.Watcher {
	if g.Conf.Quiet {
		return nil
	}
	whose := "دفتر " + g.Conf.Me
	if g.Conf.Me == "" {
		whose = g.Conf.Title
	}
	return &notify.Watcher{Garden: g.Conf.Name, Whose: whose, Path: filepath.Join(dir, "notified-"+g.Conf.Name+".json"),
		Show: notify.Raise(logf), Log: logf,
		Leads: func() ([]notify.Lead, error) {
			list, err := web.Leads(g)
			if err != nil {
				return nil, err
			}
			out := make([]notify.Lead, 0, len(list))
			for _, l := range list {
				about, _ := l["title"].(string)
				if about == "" {
					if from, _ := l["from"].(string); from != "" {
						about = "از " + from
					}
				}
				id, _ := l["id"].(string)
				kind, _ := l["kind"].(string)
				whose, _ := l["for"].(string)
				out = append(out, notify.Lead{Kind: kind, ID: id, About: about, For: whose})
			}
			return out, nil
		}}
}

func open(args []string) error {
	c, err := config.Load()
	if err != nil {
		return err
	}
	if health(c) == nil {
		self, _ := os.Executable()
		cmd := proc.Command(self, "serve")
		if err := cmd.Start(); err != nil {
			return err
		}
		for i := 0; i < 120 && health(c) == nil; i++ {
			time.Sleep(time.Second)
		}
		if health(c) == nil {
			return errors.New("daftard did not answer; see daftard.log in " + state.Dir())
		}
	}
	token, err := state.Token()
	if err != nil {
		return err
	}
	once, err := openCode(c, token)
	if err != nil {
		return err
	}
	url, read := address(baseURL(c), once, args)
	if !read {
		state.Logger().Printf("open: %q is no landing address; the handplace's front page is opened", args[0])
	}
	return browse(url)
}

// address is the page `daftard open` opens by its one-time code: at the landing it was given, or a garden's front
// page by its name. A lead it cannot read — an address in any other form — opens the front page and is never passed
// on: then read is false.
func address(base, once string, args []string) (url string, read bool) {
	url = base + "/?once=" + neturl.QueryEscape(once)
	if len(args) == 0 {
		return url, true
	}
	if to, ok := landing(args[0]); ok {
		return url + "&to=" + neturl.QueryEscape(to), true
	}
	if !strings.ContainsAny(args[0], ":/?&") { // a garden's name
		return url + "&g=" + neturl.QueryEscape(args[0]), true
	}
	return url, false
}

// loopback says whether an address listens on this machine alone.
func loopback(addr string) bool {
	host, _, err := net.SplitHostPort(addr)
	if err != nil {
		return false
	}
	ip := net.ParseIP(host)
	return host == "localhost" || ip != nil && ip.IsLoopback()
}

// openCode asks the running daftard for a one-time code, the machine's key sent in a header: the page is opened by the
// code, so no command line and no browser history ever holds the key (security audit 2026-10-10, 2.2).
func openCode(c *config.Config, token string) (string, error) {
	if err := foreign(c); err != nil {
		return "", err
	}
	req, err := http.NewRequest(http.MethodPost, baseURL(c)+"/door", nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("X-Daftard-Key", token)
	resp, err := (&http.Client{Timeout: 10 * time.Second}).Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var got struct {
		Once string `json:"once"`
	}
	if resp.StatusCode != http.StatusOK || json.NewDecoder(io.LimitReader(resp.Body, 4096)).Decode(&got) != nil || got.Once == "" {
		return "", fmt.Errorf("daftard gave no code to open the page (%s)", resp.Status)
	}
	return got.Once, nil
}

// landing reads a lead — daftar://go/<garden>/<kind>/<id> (what the system hands a registered daftar: link) or the
// path /go/… itself — as the handplace's landing path; and the page of a garden's Odoo screens —
// daftar://odoo?g=<garden>[&series=…][&asof=…] or the path /odoo?g=… itself — as that page's door, in the one form
// the handplace takes it (web.OdooRe). Anything else is not one: it is never passed on as given.
func landing(lead string) (string, bool) {
	p := lead
	if strings.HasPrefix(strings.ToLower(lead), "daftar:") {
		u, err := neturl.Parse(lead)
		if err != nil || u.Fragment != "" || u.User != nil {
			return "", false
		}
		switch {
		case u.Host == "go" && u.RawQuery == "": // the path names the case, all of it
			p = "/go" + u.Path
		case u.Host == "odoo" && u.Path == "", u.Host == "" && (u.Opaque == "odoo" || u.Opaque == "" && u.Path == "/odoo"):
			p = "/odoo?" + u.RawQuery // daftar://odoo?…, daftar:odoo?…, daftar:/odoo?…: the query names the page, all of it
		case u.Host != "" || u.RawQuery != "": // another host is no lead of this machine's
			return "", false
		case u.Opaque != "": // daftar:go/…
			p = "/" + u.Opaque
		default:
			p = u.Path // daftar:/go/…
		}
	}
	if !web.GoRe.MatchString(p) && !web.OdooRe.MatchString(p) {
		return "", false
	}
	return p, true
}

// notifyTest asks the running daftard to raise a sample notice: it is daftard, in the user's own session, that can
// show one (a command run over a remote shell has no desktop to show it on).
func notifyTest(args []string) error {
	c, err := config.Load()
	if err != nil {
		return err
	}
	if health(c) == nil {
		return errors.New("daftard is not running (daftard open)")
	}
	g := c.Gardens[0].Name
	if len(args) > 0 {
		g = args[0]
	}
	gc := c.Garden(g)
	if gc == nil {
		return fmt.Errorf("daftard.json names no garden %s", g)
	}
	cl, auth, csrf, err := sessionAt(c, gc.Listen) // the garden's own daemon raises its notices
	if err != nil {
		return err
	}
	req, _ := http.NewRequest("POST", "http://"+gc.Listen+"/api/notify/test?g="+neturl.QueryEscape(g), strings.NewReader("{}"))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Origin", "http://"+gc.Listen)
	req.Header.Set("X-CSRF-Token", csrf)
	auth(req)
	resp, err := cl.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	b, _ := io.ReadAll(resp.Body)
	fmt.Println(resp.Status, strings.TrimSpace(string(b)))
	return nil
}

// leads prints what waits for a decision in each garden (or the one named), each with its landing address: what a
// notification would carry.
func leads(args []string) error {
	c, err := config.Load()
	if err != nil {
		return err
	}
	if health(c) == nil {
		return errors.New("daftard is not running (daftard open)")
	}
	for _, g := range c.Gardens {
		if len(args) > 0 && args[0] != g.Name {
			continue
		}
		cl, auth, _, err := sessionAt(c, g.Listen) // each garden's own daemon
		if err != nil {
			fmt.Printf("%s: %v\n", g.Name, err)
			continue
		}
		req, _ := http.NewRequest("GET", "http://"+g.Listen+"/api/leads?g="+neturl.QueryEscape(g.Name), nil)
		auth(req)
		resp, err := cl.Do(req)
		if err != nil {
			return err
		}
		var out struct {
			Leads []map[string]any `json:"leads"`
			Error string           `json:"error"`
		}
		_ = json.NewDecoder(resp.Body).Decode(&out)
		resp.Body.Close()
		if out.Error != "" {
			fmt.Printf("%s: %s\n", g.Name, out.Error)
			continue
		}
		fmt.Printf("%s: %d waiting\n", g.Name, len(out.Leads))
		for _, l := range out.Leads {
			addr := "daftar://go/" + g.Name + "/" + fmt.Sprint(l["kind"])
			if id := fmt.Sprint(l["id"]); id != "" && id != "<nil>" {
				addr += "/" + id
			}
			about := l["title"]
			if about == nil {
				about = l["from"]
			}
			fmt.Printf("  %-9v %v\n            %s\n", l["kind"], about, addr)
		}
	}
	return nil
}

// browse opens the default browser, through a program that shows no window of its own.
func browse(url string) error {
	switch runtime.GOOS {
	case "windows":
		return proc.Command(filepath.Join(os.Getenv("WINDIR"), "System32", "rundll32.exe"), "url.dll,FileProtocolHandler", url).Start()
	case "darwin":
		return proc.Command("open", url).Start()
	default:
		return proc.Command("xdg-open", url).Start()
	}
}

// session is what a command line needs to act as the handplace does: a client, how a request carries the machine's
// key, and the CSRF token. The key goes in the X-Daftard-Key header (a page's cookie carries a value of the running
// daftard's own, never the key: security audit 2026-10-10, 2.7). A daftard started before that change takes the key
// only as its cookie and refuses the header: there the cookie is sent instead — to this machine's own listener, as
// it always was — so `daftard stop`, run by a new binary put in place of a running old one, still stops it.
func session(c *config.Config) (*http.Client, func(*http.Request), string, error) {
	return sessionAt(c, c.Listen)
}

// sessionAt is a session with the daftard at addr — the machine's front door, or a garden's own daemon — by the
// machine's key; never with another account's listener there.
func sessionAt(c *config.Config, addr string) (*http.Client, func(*http.Request), string, error) {
	if err := foreignAt(addr); err != nil {
		return nil, nil, "", err
	}
	token, err := state.Token()
	if err != nil {
		return nil, nil, "", err
	}
	cl := &http.Client{Timeout: 30 * time.Second}
	ways := []func(*http.Request){
		func(r *http.Request) { r.Header.Set("X-Daftard-Key", token) },
		func(r *http.Request) { r.AddCookie(&http.Cookie{Name: "daftard", Value: token}) },
	}
	for _, auth := range ways {
		req, _ := http.NewRequest("GET", "http://"+addr+"/api/session", nil)
		auth(req)
		resp, err := cl.Do(req)
		if err != nil {
			return nil, nil, "", err
		}
		if resp.StatusCode == http.StatusForbidden {
			resp.Body.Close()
			continue
		}
		var info map[string]any
		err = json.NewDecoder(resp.Body).Decode(&info)
		resp.Body.Close()
		if err != nil {
			return nil, nil, "", err
		}
		csrf, _ := info["csrf"].(string)
		return cl, auth, csrf, nil
	}
	return nil, nil, "", fmt.Errorf("what answers at %s takes this machine's key neither way: is it this machine's daftard?", addr)
}

func status() error {
	c, err := config.Load()
	if err != nil {
		return err
	}
	out := map[string]any{"running": false, "listen": c.Listen, "state": state.Dir(), "build": Build}
	if err := foreign(c); err != nil {
		out["held"] = err.Error()
	} else if h := health(c); h != nil {
		out["running"], out["serving"] = true, h["build"]
		daemons, _ := h["gardens"].(map[string]any)
		for _, g := range c.Gardens { // each garden's own daemon: its address, whether it runs, and its session
			info := map[string]any{"listen": g.Listen, "daemon": daemons[g.Name]}
			if cl, auth, _, err := sessionAt(c, g.Listen); err == nil {
				req, _ := http.NewRequest("GET", "http://"+g.Listen+"/api/session?g="+g.Name, nil)
				auth(req)
				if resp, err := cl.Do(req); err == nil {
					var sess map[string]any
					_ = json.NewDecoder(resp.Body).Decode(&sess)
					resp.Body.Close()
					delete(sess, "csrf")
					info["session"] = sess
				}
			}
			out[g.Name] = info
		}
	}
	b, _ := json.MarshalIndent(out, "", " ")
	fmt.Println(string(b))
	return nil
}

func stop() error {
	c, err := config.Load()
	if err != nil {
		return err
	}
	if health(c) == nil {
		fmt.Println("not running")
		return nil
	}
	cl, auth, csrf, err := session(c)
	if err != nil {
		return err
	}
	req, _ := http.NewRequest("POST", baseURL(c)+"/api/stop", strings.NewReader("{}"))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Origin", baseURL(c))
	req.Header.Set("X-CSRF-Token", csrf)
	auth(req)
	resp, err := cl.Do(req)
	if err != nil {
		return err
	}
	resp.Body.Close()
	for i := 0; i < 300 && health(c) != nil; i++ {
		time.Sleep(time.Second)
	}
	fmt.Println("stopped")
	return nil
}

func showError(args []string) error {
	if len(args) != 1 {
		return errors.New("usage: daftard error E-XXXX-XXXX")
	}
	rec, ok := guided.Open().Get(strings.ToUpper(args[0]))
	if !ok {
		return errors.New("no such reference")
	}
	b, _ := json.MarshalIndent(rec, "", " ")
	fmt.Println(string(b))
	return nil
}

type stewards []config.FollowUp

func (s *stewards) String() string { return fmt.Sprint(*s) }
func (s *stewards) Set(v string) error {
	parts := strings.SplitN(v, ":", 3)
	f := config.FollowUp{Who: parts[0], Sees: "all"}
	if len(parts) > 1 {
		f.Title = parts[1]
	}
	if len(parts) > 2 {
		f.Reach = parts[2]
	}
	*s = append(*s, f)
	return nil
}

func install(args []string) error {
	fl := flag.NewFlagSet("install", flag.ContinueOnError)
	gardenPath := fl.String("garden", "", "the garden's working copy")
	python := fl.String("python", "", "the Python its tools run with")
	title := fl.String("title", "دفتر", "the handplace's title")
	name := fl.String("name", "", "a short name for the garden")
	me := fl.String("me", "", "how the gardener is called on screen (their bean's title when empty)")
	listen := fl.String("listen", "127.0.0.1:8770", "where the handplace listens (loopback only)")
	doSync := fl.Bool("sync", false, "keep the garden in step with its hub (takes over from another syncing tool)")
	doExchange := fl.Bool("exchange", false, "run its exchange rounds, where consented")
	hub := fl.String("hub", "", "the bean of this machine's hub of the garden, which signs what daftard writes on its own")
	var st stewards
	fl.Var(&st, "steward", "who:title:reach — someone errors are also followed up with (repeatable)")
	if err := fl.Parse(args); err != nil {
		return err
	}
	if *gardenPath == "" || *python == "" {
		return errors.New("--garden and --python are required")
	}
	if !strings.HasPrefix(*listen, "127.0.0.1:") {
		return errors.New("--listen must be on 127.0.0.1: the handplace is never served beyond this machine in the MVP")
	}
	if *hub != "" && !hubkey.ValidBean(*hub) {
		return fmt.Errorf("--hub %q is no bean's id", *hub)
	}
	abs, _ := filepath.Abs(*gardenPath)
	c := &config.Config{Listen: *listen, Gardens: []config.Garden{{Name: *name, Path: abs, Python: *python, Title: *title, Me: *me,
		Sync: *doSync, Exchange: *doExchange, Hub: *hub, FollowUp: st}}}
	if old, err := config.Load(); err == nil { // the other gardens it already serves are kept
		for _, g := range old.Gardens {
			if g.Path != abs {
				c.Gardens = append(c.Gardens, g)
			}
		}
	}
	if err := c.Save(); err != nil {
		return err
	}
	fmt.Println("wrote", config.Path())
	if *hub != "" { // the hub's init on this machine: its key, made by the garden's own tool, never here
		out, err := hubkey.Install(*python, abs, state.Dir())
		fmt.Print(out)
		if err != nil {
			fmt.Println("daftar: the hub's key was not made:", err)
		} else {
			fmt.Printf("daftar: add that statement to the bean %s (the gardener's, class F); until it is there, a hub takes "+
				"nothing this hub signs\n", *hub)
		}
	}
	if runtime.GOOS == "windows" {
		if err := installWindows(); err != nil {
			return err
		}
	}
	if err := registerLinks(); err != nil {
		if runtime.GOOS == "windows" {
			return err
		}
		fmt.Println("daftar: links not registered:", err) // a server with no desktop goes without
	}
	return nil
}

// registerLinks makes daftar: links (a notification's button, a link in another program) open the handplace through
// `daftard open`, which reads the address and passes on only a landing path. For this user alone: on Windows under
// HKCU (no administrator), on Linux a desktop entry that is the default for x-scheme-handler/daftar.
func registerLinks() error {
	self, err := os.Executable()
	if err != nil {
		return err
	}
	switch runtime.GOOS {
	case "windows":
		key := `HKCU\Software\Classes\daftar`
		app := `HKCU\Software\Classes\AppUserModelId\` + notify.AppID // whose name a notification shows
		for _, a := range [][]string{
			{"add", app, "/v", "DisplayName", "/d", "دفتر", "/f"},
			{"add", key, "/ve", "/d", "URL:Daftar", "/f"},
			{"add", key, "/v", "URL Protocol", "/d", "", "/f"},
			{"add", key + `\DefaultIcon`, "/ve", "/d", `"` + self + `",0`, "/f"},
			{"add", key + `\shell\open\command`, "/ve", "/d", `"` + self + `" open "%1"`, "/f"},
		} {
			if out, err := proc.Command("reg", a...).CombinedOutput(); err != nil {
				return fmt.Errorf("daftar: links were not registered: %v %s", err, out)
			}
		}
	case "linux":
		dir := filepath.Join(os.Getenv("HOME"), ".local", "share", "applications")
		if err := os.MkdirAll(dir, 0o755); err != nil {
			return err
		}
		entry := "[Desktop Entry]\nType=Application\nName=Daftar\nExec=\"" + self + "\" open %u\nNoDisplay=true\n" +
			"Terminal=false\nMimeType=x-scheme-handler/daftar;\n"
		if err := os.WriteFile(filepath.Join(dir, "daftard.desktop"), []byte(entry), 0o644); err != nil {
			return err
		}
		if out, err := proc.Command("xdg-mime", "default", "daftard.desktop", "x-scheme-handler/daftar").CombinedOutput(); err != nil {
			return fmt.Errorf("xdg-mime: %v %s", err, out)
		}
	default:
		return errors.New("not on " + runtime.GOOS + " yet")
	}
	fmt.Println("registered daftar: links")
	return nil
}

// installWindows makes the logon task that starts daftard in the user's session (it has no console, so nothing
// shows) and the desktop icon «دفتر» that opens the handplace.
func installWindows() error {
	self, err := os.Executable()
	if err != nil {
		return err
	}
	tr := `"` + self + `" serve`
	out, err := proc.Command("schtasks", "/Create", "/F", "/TN", "Daftar", "/SC", "ONLOGON", "/IT", "/RL", "LIMITED", "/TR", tr).CombinedOutput()
	if err != nil {
		return fmt.Errorf("the logon task was not made: %v %s", err, out)
	}
	desktop := filepath.Join(os.Getenv("USERPROFILE"), "Desktop", "دفتر.lnk")
	// A task schtasks makes is stopped when the computer goes on battery and not started on it: on a laptop, unplugging
	// it ended daftard without a trace (2026-10-08, twice, each at a "power source change"). So the task runs on
	// battery, has no time limit, and is started again if it ends.
	ps := fmt.Sprintf(`$t = Get-ScheduledTask -TaskName 'Daftar'; $x = $t.Settings; $x.DisallowStartIfOnBatteries = $false; `+
		`$x.StopIfGoingOnBatteries = $false; $x.ExecutionTimeLimit = 'PT0S'; $x.RestartCount = 3; $x.RestartInterval = 'PT1M'; `+
		`Set-ScheduledTask -TaskName 'Daftar' -Settings $x | Out-Null; `+
		`$s = New-Object -ComObject WScript.Shell; $l = $s.CreateShortcut(%q); $l.TargetPath = %q; `+
		`$l.Arguments = 'open'; $l.WorkingDirectory = %q; $l.IconLocation = "$env:WINDIR\System32\shell32.dll,1"; $l.Save()`,
		desktop, self, filepath.Dir(self))
	script := filepath.Join(state.Dir(), "shortcut.ps1")
	if err := os.WriteFile(script, []byte("\xef\xbb\xbf"+ps), 0o600); err != nil {
		return err
	}
	if out, err := proc.Command("powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-File", script).CombinedOutput(); err != nil {
		return fmt.Errorf("the task's settings or the desktop icon were not made: %v %s", err, out)
	}
	_, _ = io.WriteString(os.Stdout, "installed: the logon task «Daftar» and the desktop icon «دفتر»\n")
	return nil
}
