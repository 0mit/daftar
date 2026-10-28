package web

// A garden whose handplace is its PAGE BEANS (daftard.json `handplace: "view"`). daftard keeps its
// chrome — the garden, the sync, the person sitting, the notices and «منتظر شما» — and the pages are the view's:
//
//   - the navigation is the garden's page beans, in the order of its handplace (the worker's `view_pages`);
//   - a page's payload is built and scoped to its reader by the view's own code (`view_page`);
//   - the browser draws it with the release's own runtime, renderers and widgets, served here from the release the
//     garden runs (`/release/<garden>/…`, its assets/view/lib), loaded by the chrome as the files they are;
//   - a Save goes to the view's one write path (`view_write`), signed where a person sits with their own key.
//
// Nothing of a page is daftard's: it draws, reads and writes no fact of its own.

import (
	"encoding/json"
	"net/http"
	"os"
	"path"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/0mit/daftar/daftard/internal/state"
)

// releaseFile is what of a garden's view asset the browser may load: the widgets and their style and font, and the
// view's classic scripts and styles — never its Python, never a file elsewhere in the garden.
var releaseFile = regexp.MustCompile(`^(widgets/[a-z]+\.(js|css|woff2)|view_[a-z]+\.(js|css))$`)

// release serves /release/<garden>/<file> from that garden's own release (assets/view/lib), and
// /release/<garden>/kit.css, the kit's style beside it (the worker's `view_style`, with a page's palette).
func (s *Server) release(w http.ResponseWriter, r *http.Request) {
	rest := strings.TrimPrefix(r.URL.Path, "/release/")
	name, rel, _ := strings.Cut(rest, "/")
	var g *Garden
	for _, x := range s.Gardens {
		if x.Conf.Name == name {
			g = x
		}
	}
	if g == nil || !g.Conf.ViewHandplace() { // a legacy garden has no release here: the 404 of a file daftard never had
		text(w, 404, T(g, "یافت نشد.", "Not found."))
		return
	}
	if !s.mayRead(w, r, g) { // on a shared machine, the garden's own files to whom may read the garden, as every page
		return
	}
	if rel == "kit.css" {
		page := r.URL.Query().Get("page")
		raw, err := s.call(g, "view_style", map[string]any{"page": page}, time.Minute)
		var st struct {
			CSS string `json:"css"`
		}
		if err == nil {
			err = json.Unmarshal(raw, &st)
		}
		if err != nil {
			text(w, 503, T(g, "یافت نشد.", "Not found."))
			return
		}
		w.Header().Set("Content-Type", "text/css; charset=utf-8")
		w.Header().Set("Cache-Control", "no-cache")
		_, _ = w.Write([]byte(st.CSS))
		return
	}
	if !releaseFile.MatchString(rel) || path.Clean(rel) != rel {
		text(w, 404, T(g, "یافت نشد.", "Not found."))
		return
	}
	b, err := os.ReadFile(filepath.Join(g.Conf.Path, "assets", "view", "lib", filepath.FromSlash(rel)))
	if err != nil {
		text(w, 404, T(g, "یافت نشد.", "Not found."))
		return
	}
	w.Header().Set("Content-Type", types[path.Ext(rel)])
	w.Header().Set("Cache-Control", "no-cache")
	_, _ = w.Write(b)
}

// viewOnly says whether g's pages are its page beans. A legacy garden keeps exactly today's surface until its gardener
// moves it (daftard.json `handplace`): each address of a view garden answers it as one daftard never had, get's and
// post's own 404, and its worker is asked nothing.
func viewOnly(w http.ResponseWriter, g *Garden) bool {
	if g.Conf.ViewHandplace() {
		return true
	}
	reply(w, 404, map[string]any{"error": T(g, "یافت نشد.", "Not found.")})
	return false
}

// viewPages is the handplace's data for a garden whose pages are its page beans: the chrome's (the garden, its sync,
// who sits) and the navigation (its page beans, in order) — /api/dashboard's place for such a garden.
func (s *Server) viewPages(w http.ResponseWriter, r *http.Request, g *Garden) {
	type pageList struct {
		Pages  []map[string]any `json:"pages"`
		Assets map[string]any   `json:"assets"`
	}
	d, err := s.derived(g, "view_pages", nil, 2*time.Minute, "list", func(raw json.RawMessage) (any, error) {
		var list pageList
		err := json.Unmarshal(raw, &list)
		return list, err
	})
	if err != nil {
		s.fail(w, g, "read", "", err)
		return
	}
	list := d.(pageList)
	data := map[string]any{"pages": list.Pages, "assets": list.Assets, "csrf": s.CSRF, "version": g.Version, "build": s.Build,
		"head": "", "asOf": time.Now().Format("2006-01-02"), "generatedAt": time.Now().Format(time.RFC3339)}
	if head, err := s.derived(g, "hello", nil, time.Minute, "head", func(raw json.RawMessage) (any, error) {
		var h struct {
			Head string `json:"head"`
		}
		err := json.Unmarshal(raw, &h)
		return h.Head, err
	}); err == nil {
		data["head"] = head
	}
	data["sync"] = map[string]any{"state": "off"}
	if g.Syncer != nil {
		data["sync"] = g.Syncer.Last()
	}
	data["garden"] = map[string]any{"name": g.Conf.Name, "title": g.Conf.Title, "lang": g.Conf.Lang,
		"gardener": g.Conf.Gardener, "me": g.Conf.Me, "kind": g.Conf.Kind, "handplace": "view"}
	data["labels"] = s.labelsOf(r, g)
	data["reader"] = s.readerOf(r, g)
	data["sitting"] = s.sittingState(r, g)
	reply(w, 200, data)
}

// viewPage is one page bean's payload for the person reading: the view's own reading, scoped to them.
func (s *Server) viewPage(w http.ResponseWriter, r *http.Request, g *Garden) {
	if !viewOnly(w, g) {
		return
	}
	page := r.URL.Query().Get("page")
	if !slugRe.MatchString(page) {
		reply(w, 400, map[string]any{"error": T(g, "این صفحه در این دفتر نیست.", "This page is not in this garden.")})
		return
	}
	reader := s.readerOf(r, g)
	s.pass(w, g, "view_page", map[string]any{"page": page, "reader": reader, "lang": g.Conf.Lang,
		"prefs": s.prefs().Get(g.Conf.Name, reader)})
}

// viewWrite is a page's Save: the statements a sheet adds, changes and takes out, or a drawing's form of a verb,
// written by the view's one write path as the person reading — signed with their own key where they sit, refused
// where the garden takes only signed writes and nobody sits. One commit, judged by the gate; a refusal keeps nothing.
func (s *Server) viewWrite(w http.ResponseWriter, r *http.Request, g *Garden) {
	if !viewOnly(w, g) {
		return
	}
	req, ok := readJSON(w, r)
	if !ok {
		return
	}
	sign, _, done, ok := s.signing(w, r, g)
	if !ok {
		return
	}
	params := map[string]any{"body": req, "reader": s.readerOf(r, g)}
	if sign != nil {
		params["sign"] = sign
	}
	raw, err := g.Worker.Call("view_write", params, 10*time.Minute)
	done()
	if err != nil {
		bean, _ := req["bean"].(string)
		s.fail(w, g, "save", bean, err)
		return
	}
	var ans struct {
		OK bool `json:"ok"`
	}
	_ = json.Unmarshal(raw, &ans)
	if ans.OK {
		s.changed(g) // open pages hear of it at once
		if g.Syncer != nil {
			g.Syncer.Wake(false) // and the hub soon after
		}
	}
	w.Header().Set("Content-Type", "application/json; charset=utf-8")
	w.Header().Set("Cache-Control", "no-store")
	if !ans.OK {
		w.WriteHeader(422)
	}
	_, _ = w.Write(raw)
}

// actBodyMax is how large a page's action may be: it may carry a file a person gives (an input of the type `file`, its
// bytes as base64), and the view's own host keeps one of at most 16 MiB; base64 makes it a third larger.
const actBodyMax = 24 << 20

// viewAct is a page's action — a walk of the garden this machine names for the action's tool (daftard.json `walks`),
// started by the garden's own bin/act.py with what the person gave it, its plan returned for them to ratify — or a
// person's ratification or refusal of that plan. As the person reading, signed where they sit; each attempt audited
// in this machine's record of the garden (its state folder), never in git.
func (s *Server) viewAct(w http.ResponseWriter, r *http.Request, g *Garden) {
	if !viewOnly(w, g) {
		return
	}
	req, ok := readJSONMax(w, r, actBodyMax)
	if !ok {
		return
	}
	sign, _, done, ok := s.signing(w, r, g)
	if !ok {
		return
	}
	params := map[string]any{"body": req, "reader": s.readerOf(r, g), "lang": g.Conf.Lang, "walks": g.Conf.Walks,
		"audit": filepath.Join(state.Dir(), "audit-"+g.Conf.Name+".jsonl")}
	if sign != nil {
		params["sign"] = sign
	}
	raw, err := g.Worker.Call("view_act", params, 60*time.Minute)
	done()
	if err != nil {
		bean, _ := req["bean"].(string)
		s.fail(w, g, "save", bean, err)
		return
	}
	var ans struct {
		Status int            `json:"status"`
		Answer map[string]any `json:"answer"`
	}
	if json.Unmarshal(raw, &ans) != nil || ans.Status == 0 {
		reply(w, 502, map[string]any{"error": T(g, "پاسخ دفتر خوانده نشد.", "The garden's answer could not be read.")})
		return
	}
	if ans.Status == 200 {
		s.changed(g) // open pages hear of it at once
		if g.Syncer != nil {
			g.Syncer.Wake(false) // and the hub soon after
		}
	}
	reply(w, ans.Status, ans.Answer)
}
