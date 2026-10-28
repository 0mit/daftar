package web

import (
	"bufio"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/custom"
)

// PUSH, DON'T POLL (design §6: an energy-efficient UI): a page is told when its garden changed and
// only then reads it again. Each garden's commit is watched by reading its git reference files every few seconds (a
// file read: no process started, nothing on the network); any writer's commit (a save, a sync, the exchange, an
// agent) is seen. Pages listen on /api/events (server-sent events) and refresh once per change.

type watch struct {
	mu   sync.Mutex
	head string
	subs map[chan string]struct{}
}

func (w *watch) subscribe() (chan string, string) {
	w.mu.Lock()
	defer w.mu.Unlock()
	ch := make(chan string, 1)
	w.subs[ch] = struct{}{}
	return ch, w.head
}

func (w *watch) unsubscribe(ch chan string) {
	w.mu.Lock()
	defer w.mu.Unlock()
	delete(w.subs, ch)
}

func (w *watch) set(head string) {
	w.mu.Lock()
	defer w.mu.Unlock()
	if head == "" || head == w.head {
		return
	}
	w.head = head
	for ch := range w.subs {
		select {
		case ch <- head:
		default: // a page that has not read the last one is told once: it reads the garden whole anyway
		}
	}
}

// gitDirOf is the garden's git folder (a worktree's .git is a file naming the real one).
func gitDirOf(gardenPath string) string {
	gitDir := filepath.Join(gardenPath, ".git")
	if fi, err := os.Stat(gitDir); err == nil && !fi.IsDir() {
		if b, err := os.ReadFile(gitDir); err == nil {
			gitDir = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(string(b)), "gitdir:"))
		}
	}
	return gitDir
}

// HeadOf is a garden's current commit, read from its git files (headOf).
func HeadOf(gardenPath string) string { return headOf(gardenPath) }

// headOf reads the garden's current commit from its git files: HEAD, the branch it names, or packed-refs.
func headOf(gardenPath string) string {
	gitDir := gitDirOf(gardenPath)
	b, err := os.ReadFile(filepath.Join(gitDir, "HEAD"))
	if err != nil {
		return ""
	}
	h := strings.TrimSpace(string(b))
	if !strings.HasPrefix(h, "ref: ") {
		return h
	}
	return refOf(gitDir, strings.TrimPrefix(h, "ref: "))
}

// refOf is a ref's commit, from its own file or packed-refs; "" when there is none.
func refOf(gitDir, ref string) string {
	if b, err := os.ReadFile(filepath.Join(gitDir, filepath.FromSlash(ref))); err == nil {
		return strings.TrimSpace(string(b))
	}
	f, err := os.Open(filepath.Join(gitDir, "packed-refs"))
	if err != nil {
		return ""
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		if fields := strings.Fields(sc.Text()); len(fields) == 2 && fields[1] == ref {
			return fields[0]
		}
	}
	return ""
}

// stamp is what a page's view of the garden depends on: its commit, and the reader's own labels.
func stamp(g *Garden) string {
	head := headOf(g.Conf.Path)
	if head == "" {
		return ""
	}
	if c := refOf(gitDirOf(g.Conf.Path), custom.Ref(reader(g))); c != "" {
		return head + " " + c
	}
	return head
}

// Watch starts watching every garden's commit; it runs until stop is closed.
func (s *Server) Watch(stop <-chan struct{}) {
	s.watches = map[string]*watch{}
	for _, g := range s.Gardens {
		s.watches[g.Conf.Name] = &watch{head: stamp(g), subs: map[chan string]struct{}{}}
	}
	go func() {
		t := time.NewTicker(3 * time.Second)
		defer t.Stop()
		for {
			select {
			case <-stop:
				return
			case <-t.C:
				for _, g := range s.Gardens {
					s.watches[g.Conf.Name].set(stamp(g))
					s.heldWalk(g, s.held(g), quickVersion(g)) // a change made outside daftard: its answers asked again
				}
			}
		}
	}()
}

// changed is called after daftard itself commits (a save): pages hear at once, not at the next look.
func (s *Server) changed(g *Garden) {
	s.heldWalk(g, s.held(g), quickVersion(g)) // the answers held are of the garden before: asked again at once
	if w := s.watches[g.Conf.Name]; w != nil {
		w.set(stamp(g))
	}
}

// events is /api/events: one `changed` event each time the garden's commit changes, and a comment every minute so a
// connection that died is noticed. The browser reconnects by itself.
func (s *Server) events(w http.ResponseWriter, r *http.Request, g *Garden) {
	wt := s.watches[g.Conf.Name]
	fl, ok := w.(http.Flusher)
	if wt == nil || !ok {
		reply(w, 503, map[string]any{"error": T(g, "رویدادها در دسترس نیست.", "Events are not available.")})
		return
	}
	ch, head := wt.subscribe()
	defer wt.unsubscribe(ch)
	w.Header().Set("Content-Type", "text/event-stream")
	w.Header().Set("Cache-Control", "no-store")
	fmt.Fprintf(w, "event: head\ndata: %s\n\n", head)
	fl.Flush()
	keep := time.NewTicker(time.Minute)
	defer keep.Stop()
	for {
		select {
		case <-r.Context().Done():
			return
		case h := <-ch:
			fmt.Fprintf(w, "event: changed\ndata: %s\n\n", h)
			fl.Flush()
		case <-keep.C:
			fmt.Fprint(w, ": still here\n\n")
			fl.Flush()
		}
	}
}
