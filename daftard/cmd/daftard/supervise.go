package main

import (
	"bytes"
	"crypto/tls"
	"errors"
	"fmt"
	"net"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"runtime/debug"
	"strconv"
	"sync"
	"syscall"
	"time"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/notify"
	"github.com/0mit/daftar/daftard/internal/proc"
	"github.com/0mit/daftar/daftard/internal/served"
	"github.com/0mit/daftar/daftard/internal/sitting"
	"github.com/0mit/daftar/daftard/internal/state"
	"github.com/0mit/daftar/daftard/internal/web"
	"github.com/0mit/daftar/daftard/internal/worker"
	"github.com/0mit/daftar/daftard/python"
	assets "github.com/0mit/daftar/daftard/web"
)

// ONE DAFTARD PER GARDEN (the operator, 2026-10-14): `daftard serve` is the machine's daftard. It starts one daemon for
// each garden daftard.json names (`daftard serve --garden <name>`, serveGarden), keeps it running — started again when
// it ends, sooner the longer it ran — and ends them with itself. It serves no garden's pages: its own address is the
// machine's front door (web.FrontHandler), which opens each garden's own daemon. What the machine has once is kept
// here — the served handplace's listener over TLS and Odoo's own origin — and each question they have for a garden is
// asked of that garden's daemon (web.Remote), where it is answered from the garden's memory.

// frontVar names, for a garden's daemon, the machine's front door it was started by: it ends when that is gone.
const frontVar = "DAFTARD_FRONT"

// daemonGrace is how long a garden's daemon told to end is given (a save under way finishes) before it is ended.
var daemonGrace = time.Minute

func serve() error {
	c, err := config.Load()
	if err != nil {
		return fmt.Errorf("%v (run `daftard install` first: %s)", err, config.Path())
	}
	if err := foreign(c); err != nil {
		return err
	}
	if health(c) != nil {
		return nil // one per machine: it is already running
	}
	// the machine's own page and Odoo's origin listen on the loopback alone: beyond it is the served listener's, over
	// TLS, for those the grants name (security audit 2026-10-10, 2.10); each garden's own address is held to the
	// loopback when daftard.json is read
	for _, a := range []string{c.Listen, c.OdooListen} {
		if a != "" && !loopback(a) {
			return fmt.Errorf("%s is not this machine's loopback: daftard's own page is this machine's alone; serve beyond it with `served`", a)
		}
	}
	ln, err := net.Listen("tcp", c.Listen)
	if err != nil {
		return err
	}
	// the served listener is bound before anything is served: if its address is taken, daftard stops, and no other
	// process can answer as the served page while daftard runs without it (security audit 2026-10-10, 1.2)
	var servedLn net.Listener
	var servedCert tls.Certificate
	if sv := c.Served; sv != nil {
		if sv.Listen == "" || len(sv.Names) == 0 || sv.Cert == "" || sv.Key == "" {
			return errors.New("daftard.json `served` needs listen, names, cert and key")
		}
		if servedCert, err = tls.LoadX509KeyPair(sv.Cert, sv.Key); err != nil {
			return fmt.Errorf("served: its certificate: %v", err)
		}
		if servedLn, err = net.Listen("tcp", sv.Listen); err != nil {
			return fmt.Errorf("served: %v — another process holds %s; daftard does not start without it", err, sv.Listen)
		}
	}
	// Odoo's own client on an origin of its own (security audit 2.1): localhost:<port>, another site than the
	// handplace; if its address is taken, no Odoo page is offered rather than send anyone to it
	odooAddr := odooAddress(c)
	odooLn, odooErr := net.Listen("tcp", odooAddr)
	dir, err := state.Ensure()
	if err != nil {
		return err
	}
	if f, err := os.OpenFile(filepath.Join(dir, "crash.log"), os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0o600); err == nil {
		_ = debug.SetCrashOutput(f, debug.CrashOptions{})
	}
	if _, err := writePython(dir); err != nil { // once, before the gardens' daemons read it
		return err
	}
	token, err := state.Token()
	if err != nil {
		return err
	}
	log := state.Logger()
	stopAll := make(chan struct{})
	s := &web.Server{Listen: c.Listen, Token: token, CSRF: state.Random(24), Build: Build, Assets: assets.FS,
		Errors: guided.Open(), Notify: notify.Raise(log.Printf)}
	s.Keys = &sitting.Keys{Dir: filepath.Join(dir, "keys")}
	s.OdooDir = filepath.Join(dir, "odoo")
	if odooErr == nil {
		_, port, _ := net.SplitHostPort(odooLn.Addr().String())
		s.Odoo = web.NewOdooDoor("localhost:" + port)
	} else {
		log.Printf("odoo: %v — no Odoo page is offered", odooErr)
	}
	s.Sittings = sitting.NewSittings(30 * time.Minute)
	s.Shared = c.Shared
	if c.Places != nil && len(c.Places.Bundles) > 0 {
		s.Places = web.NewPlaceIndex(c.Places.Bundles, log.Printf)
	}
	s.Log = log.Printf
	var daemons []web.Daemon
	for _, gc := range c.Gardens { // each garden as the served handplace and Odoo's origin ask it: of its own daemon
		s.Gardens = append(s.Gardens, &web.Garden{Conf: gc, Worker: &web.Remote{Garden: gc.Name, Addr: gc.Listen, Token: token},
			Version: Build})
		daemons = append(daemons, web.Daemon{Name: gc.Name, Addr: gc.Listen})
	}
	exe, err := os.Executable()
	if err != nil {
		return err
	}
	var kept sync.WaitGroup
	for _, gc := range c.Gardens {
		kept.Add(1)
		go func(gc config.Garden) {
			defer kept.Done()
			keepDaemon(exe, gc, c.Listen, log.Printf, stopAll)
		}(gc)
	}
	front := &http.Server{Handler: s.FrontHandler(daemons), ReadHeaderTimeout: 10 * time.Second}
	var servedSrv *http.Server
	if sv := c.Served; sv != nil {
		servedSrv = &http.Server{Handler: s.ServedHandler(sv.Names, served.New()), ReadHeaderTimeout: 10 * time.Second,
			ReadTimeout: 30 * time.Second, WriteTimeout: 60 * time.Second, IdleTimeout: 120 * time.Second,
			MaxHeaderBytes: 64 << 10, TLSConfig: &tls.Config{MinVersion: tls.VersionTLS12, Certificates: []tls.Certificate{servedCert}}}
		go func() {
			log.Printf("daftard serving beyond this machine on %s as %v", sv.Listen, sv.Names)
			if err := servedSrv.ServeTLS(servedLn, "", ""); err != nil && !errors.Is(err, http.ErrServerClosed) {
				log.Printf("served: %v", err)
			}
		}()
	}
	var odooSrv *http.Server
	if s.Odoo != nil {
		odooSrv = &http.Server{Handler: s.OdooHandler(), ReadHeaderTimeout: 10 * time.Second, IdleTimeout: 120 * time.Second,
			MaxHeaderBytes: 64 << 10}
		go func() {
			log.Printf("daftard serving Odoo's own client on %s as %s", odooAddr, s.Odoo.Host)
			if err := odooSrv.Serve(odooLn); err != nil && !errors.Is(err, http.ErrServerClosed) {
				log.Printf("odoo: %v", err)
			}
		}()
	}
	done := make(chan struct{})
	var stopping sync.Once
	s.Stop = func() {
		stopping.Do(func() {
			for _, d := range daemons { // each garden's daemon told to end: a save under way finishes first
				stopDaemon(d.Addr, token)
			}
			close(stopAll)
			kept.Wait()
			_ = front.Close()
			if servedSrv != nil {
				_ = servedSrv.Close()
			}
			if odooSrv != nil {
				_ = odooSrv.Close()
			}
			close(done)
		})
	}
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
	go func() { <-sig; s.Stop() }()
	log.Printf("daftard %s: the machine's front door on %s, %d garden(s), each served by its own daemon", Build, c.Listen, len(daemons))
	if err := front.Serve(ln); err != nil && !errors.Is(err, http.ErrServerClosed) {
		return err
	}
	<-done
	notify.Stop()
	log.Printf("daftard stopped")
	return nil
}

// keepDaemon keeps one garden's daemon running until stop: started again when it ends, after a pause that grows to
// half a minute and starts small again once a daemon has run a minute.
func keepDaemon(exe string, gc config.Garden, front string, logf func(string, ...any), stop <-chan struct{}) {
	pause := time.Second
	for {
		select {
		case <-stop:
			return
		default:
		}
		cmd := proc.Command(exe, "serve", "--garden", gc.Name)
		cmd.Env = append(os.Environ(), frontVar+"="+front)
		began := time.Now()
		if err := cmd.Start(); err != nil {
			logf("[%s] its daemon did not start: %v", gc.Name, err)
		} else {
			logf("[%s] its daemon started (pid %d) on %s", gc.Name, cmd.Process.Pid, gc.Listen)
			ended := make(chan error, 1)
			go func() { ended <- cmd.Wait() }()
			select {
			case err := <-ended:
				logf("[%s] its daemon ended: %v (garden-%s.log says why)", gc.Name, err, gc.Name)
			case <-stop: // told to end (stopDaemon): given a minute for a save under way, then ended
				select {
				case <-ended:
				case <-time.After(daemonGrace):
					_ = cmd.Process.Kill()
					<-ended
				}
				return
			}
		}
		if time.Since(began) > time.Minute {
			pause = time.Second
		}
		select {
		case <-stop:
			return
		case <-time.After(pause):
		}
		if pause < 30*time.Second {
			pause *= 2
		}
	}
}

// stopDaemon asks a garden's daemon to end, with the machine's key.
func stopDaemon(addr, token string) {
	req, err := http.NewRequest(http.MethodPost, "http://"+addr+"/internal/stop", nil)
	if err != nil {
		return
	}
	req.Header.Set("X-Daftard-Key", token)
	if resp, err := (&http.Client{Timeout: 5 * time.Second}).Do(req); err == nil {
		resp.Body.Close()
	}
}

// frontWatch ends a garden's daemon when the machine's daftard that started it is gone (five looks, 3 s apart).
func frontWatch(front string, stop func(), logf func(string, ...any), stopAll <-chan struct{}) {
	misses := 0
	t := time.NewTicker(3 * time.Second)
	defer t.Stop()
	cl := &http.Client{Timeout: 2 * time.Second}
	for {
		select {
		case <-stopAll:
			return
		case <-t.C:
		}
		resp, err := cl.Get("http://" + front + "/health?quick=1")
		if err == nil {
			resp.Body.Close()
			misses = 0
			continue
		}
		if misses++; misses >= 5 {
			logf("the machine's daftard at %s is gone: this garden's daemon ends with it", front)
			stop()
			return
		}
	}
}

// toolsWatch restarts a board's worker when the garden whose code it runs moved to a new commit.
func toolsWatch(gc config.Garden, w *worker.Worker, logf func(string, ...any), stop <-chan struct{}) {
	last := web.HeadOf(gc.Tools)
	t := time.NewTicker(10 * time.Second)
	defer t.Stop()
	for {
		select {
		case <-stop:
			return
		case <-t.C:
		}
		if h := web.HeadOf(gc.Tools); h != "" && h != last {
			last = h
			logf("[%s] new code in %s: worker restarted", gc.Name, gc.Tools)
			w.Restart()
		}
	}
}

// writePython writes the worker and its modules into the state folder where they differ, each by a rename, so a
// daemon starting never reads half a file; it returns the worker's path.
func writePython(dir string) (string, error) {
	put := func(name string, text []byte) error {
		p := filepath.Join(dir, name)
		if b, err := os.ReadFile(p); err == nil && bytes.Equal(b, text) {
			return nil
		}
		tmp := p + ".new-" + strconv.Itoa(os.Getpid())
		if err := os.WriteFile(tmp, text, 0o600); err != nil {
			return err
		}
		return os.Rename(tmp, p)
	}
	if err := put("garden_worker.py", python.Worker); err != nil {
		return "", err
	}
	for name, text := range python.Modules { // the worker's own modules, beside it
		if err := put(name, text); err != nil {
			return "", err
		}
	}
	return filepath.Join(dir, "garden_worker.py"), nil
}

// odooAddress is where Odoo's own origin listens: daftard.json's odoo_listen, or 127.0.0.1:8792.
func odooAddress(c *config.Config) string {
	if c.OdooListen != "" {
		return c.OdooListen
	}
	return "127.0.0.1:8792"
}
