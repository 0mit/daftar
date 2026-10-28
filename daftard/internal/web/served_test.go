package web

import (
	"bytes"
	"crypto/ecdsa"
	"crypto/elliptic"
	"crypto/rand"
	"crypto/sha256"
	"encoding/json"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"testing"
	"time"

	assets "github.com/0mit/daftar/daftard/web"

	"github.com/0mit/daftar/daftard/internal/config"
	"github.com/0mit/daftar/daftard/internal/guided"
	"github.com/0mit/daftar/daftard/internal/passkey"
	"github.com/0mit/daftar/daftard/internal/private"
	"github.com/0mit/daftar/daftard/internal/served"
	"github.com/0mit/daftar/daftard/internal/testpython"
	"github.com/0mit/daftar/daftard/internal/worker"
)

// the garden, as a stand-in worker answers for it: ana is named by a grant and opens `notes` to herself; eve is kept
// in the garden, named by no grant; nobody else is there
const standIn = `import json, sys
people = {'ana': {'id': 'ana', 'title': 'Ana', 'mail': 'ana@example.org'}, 'eve': {'id': 'eve', 'title': 'Eve', 'mail': 'eve@example.org'}}
def answer(rid, ok, v):
    sys.stdout.write(json.dumps({'id': rid, 'ok': ok, ('result' if ok else 'error'): v}) + '\n'); sys.stdout.flush()
for line in sys.stdin:
    req = json.loads(line); p = req.get('params') or {}; m = req['method']; rid = req['id']
    if m == 'person':
        answer(rid, p['id'] in people, people.get(p['id']) or {'status': 400, 'message': 'no such person', 'kind': 'refused'})
    elif m == 'served_person':
        answer(rid, True, {'mail': people.get(p['id'], {}).get('mail', ''), 'granted': p['id'] == 'ana'})
    elif m == 'may_send':
        answer(rid, True, {'granted': p['party'] == 'mailhost'})
    elif m == 'served_leads':
        answer(rid, True, [{'kind': 'decision', 'about': 'roof', 'title': 'the roof, to ratify', 'since': '2026-10-01'}] if p['person'] == 'ana' else [])
    elif m == 'served_forms':
        answer(rid, True, [{'id': 'intake', 'title': 'Intake', 'questions': ['What do you do?']}] if p['person'] == 'ana' else [])
    elif m == 'served_submit':
        answer(rid, True, {'laid': 'intake.' + p['person'] + '.20261009T120000', 'at': '2026-10-09 12:00:00+0300', 'answers': p['answers']})
    elif m == 'served_passkeys':
        import os
        answer(rid, True, [os.environ.get('ANA_PASSKEY', '')] if p['person'] == 'ana' else [])
    elif m == 'passkey_lay':
        answer(rid, True, {'laid': p['person'] + '.20261009T120000', 'said': 'laid', 'anchor': p['anchor']})
    elif m == 'served_read':
        if p['person'] == 'ana' and p['id'] == 'notes':
            answer(rid, True, {'id': 'notes', 'title': 'The notes', 'kind': 'document', 'statements': [{'say': {'by': 'ana'}}]})
        else:
            answer(rid, False, {'status': 403, 'message': 'not opened to you', 'kind': 'refused'})
    else:
        answer(rid, False, {'status': 404, 'message': 'unknown method', 'kind': 'failed'})
`

// THE SERVED HANDPLACE: answering only to its names; a link sent to a person a grant names, through a mail channel the
// flow law grants, and the same answer — and nothing sent — for anyone else; a link good once, its session reading
// only what `may` opens to its person; a change asked only with the session's own token, from its own origin.
func TestTheServedHandplace(t *testing.T) {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	if err := os.WriteFile(script, []byte(standIn), 0o644); err != nil {
		t.Fatal(err)
	}
	gc := config.Garden{Name: "g", Title: "The garden", Path: dir, Python: py, Served: true,
		Channels: []config.Channel{{Kind: "mail", Party: "nobody-granted", Command: []string{"x"}},
			{Kind: "mail", Party: "mailhost", From: "daftard <d@example.org>", Command: []string{"sendmail", "-t"}}}}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	var mu sync.Mutex
	var sent []string
	t.Setenv("DAFTARD_STATE", t.TempDir())
	s := &Server{Gardens: []*Garden{g}, Assets: assets.FS, Errors: guided.Open()}
	s.Mail = func(ch config.Channel, msg []byte) error {
		mu.Lock()
		defer mu.Unlock()
		sent = append(sent, ch.Party+"\n"+string(msg))
		return nil
	}
	h := s.ServedHandler([]string{"daftar.example.org"}, served.New())
	var cookie *http.Cookie
	csrf := ""
	do := func(method, path string, body any, origin string) *httptest.ResponseRecorder {
		var rd io.Reader
		if body != nil {
			b, _ := json.Marshal(body)
			rd = bytes.NewReader(b)
		}
		r := httptest.NewRequest(method, "https://daftar.example.org"+path, rd)
		r.Host = "daftar.example.org"
		if body != nil {
			r.Header.Set("Content-Type", "application/json")
		}
		if origin != "" {
			r.Header.Set("Origin", origin)
		}
		if csrf != "" {
			r.Header.Set("X-CSRF-Token", csrf)
		}
		if cookie != nil {
			r.AddCookie(cookie)
		}
		w := httptest.NewRecorder()
		h.ServeHTTP(w, r)
		return w
	}
	waitSent := func(n int) []string {
		for i := 0; i < 200; i++ {
			mu.Lock()
			got := append([]string(nil), sent...)
			mu.Unlock()
			if len(got) >= n {
				return got
			}
			time.Sleep(20 * time.Millisecond)
		}
		mu.Lock()
		defer mu.Unlock()
		return append([]string(nil), sent...)
	}

	r := httptest.NewRequest("GET", "https://elsewhere.example/", nil)
	w := httptest.NewRecorder()
	h.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatalf("a page asked for under another name is refused: %d", w.Code)
	}
	if w := do("GET", "/", nil, ""); w.Code != 200 || !strings.Contains(w.Body.String(), "/served.js") ||
		w.Header().Get("Strict-Transport-Security") == "" {
		t.Fatalf("the served page, over TLS only: %d %v", w.Code, w.Header())
	}
	if w := do("GET", "/served/leads", nil, ""); w.Code != 401 {
		t.Fatalf("nothing of a garden before signing in: %d", w.Code)
	}
	if w := do("GET", "/app/index.html", nil, ""); w.Code != 404 {
		t.Fatalf("nothing of the gardener's own handplace is served here: %d", w.Code)
	}
	if w := do("POST", "/served/link", map[string]any{"g": "g", "person": "ana"}, "https://evil.example"); w.Code != 403 {
		t.Fatalf("a link asked from another origin is refused: %d", w.Code)
	}
	answers := map[string]string{}
	for _, who := range []string{"eve", "zed", "ana"} {
		w := do("POST", "/served/link", map[string]any{"g": "g", "person": who}, "https://daftar.example.org")
		answers[who] = w.Body.String()
		if w.Code != 202 {
			t.Fatalf("asking for a link is answered alike for everyone: %s %d", who, w.Code)
		}
	}
	if answers["eve"] != answers["ana"] || answers["zed"] != answers["ana"] {
		t.Fatalf("the answer tells nobody who is kept here: %v", answers)
	}
	got := waitSent(1)
	if len(got) != 1 || !strings.HasPrefix(got[0], "mailhost\n") || !strings.Contains(got[0], "To: ana@example.org") {
		t.Fatalf("one link, to ana alone, through the channel the flow law grants: %q", got)
	}
	// THE LINK'S TOKEN TRAVELS AFTER '#' (security audit 2026-10-10, 1.7): no request carries a fragment, so no
	// server's log — nginx's in front of this one — ever holds it; the page it opens sends it, once, in a POST
	if strings.Contains(got[0], "?t=") || strings.Contains(got[0], "/served/in") {
		t.Fatalf("the link carries its token in no query, which a server's log would keep: %s", got[0])
	}
	link := regexp.MustCompile(`https://daftar\.example\.org/#in=([A-Za-z0-9_-]+)`).FindStringSubmatch(got[0])
	if link == nil {
		t.Fatalf("the message carries the link: %s", got[0])
	}
	do("POST", "/served/link", map[string]any{"g": "g", "person": "ana"}, "https://daftar.example.org")
	if again := waitSent(2); len(again) != 1 {
		t.Fatalf("no second link to her within the minute: %d", len(again))
	}
	if w := do("GET", "/served/in?t="+link[1], nil, ""); w.Code != 403 || len(w.Result().Cookies()) != 0 {
		t.Fatalf("a token in a query (a log read back) signs nobody in: %d", w.Code)
	}
	if w := do("POST", "/served/in", map[string]any{"t": link[1]}, "https://evil.example"); w.Code != 403 {
		t.Fatalf("a token sent from another origin signs nobody in: %d", w.Code)
	}
	w = do("POST", "/served/in", map[string]any{"t": link[1]}, "https://daftar.example.org")
	for _, c := range w.Result().Cookies() {
		if c.Name == servedCookie {
			cookie = c
		}
	}
	if w.Code != 200 || cookie == nil || !cookie.Secure || !cookie.HttpOnly || cookie.SameSite != http.SameSiteStrictMode {
		t.Fatalf("the link's token, sent by its page, begins her session, its cookie secure (and neither the query nor "+
			"another origin spent it): %d %v", w.Code, cookie)
	}
	keep := cookie
	cookie = nil
	if w := do("POST", "/served/in", map[string]any{"t": link[1]}, "https://daftar.example.org"); w.Code != 403 {
		t.Fatalf("a link is good once: %d", w.Code)
	}
	cookie = keep
	w = do("GET", "/served/me", nil, "")
	var me map[string]string
	_ = json.Unmarshal(w.Body.Bytes(), &me)
	if w.Code != 200 || me["person"] != "ana" || me["me"] != "Ana" || me["csrf"] == "" {
		t.Fatalf("who is signed in: %d %v", w.Code, me)
	}
	if w := do("GET", "/served/leads", nil, ""); w.Code != 200 || !strings.Contains(w.Body.String(), "the roof") {
		t.Fatalf("her own leads: %d %s", w.Code, w.Body.String())
	}
	if w := do("GET", "/served/bean?id=notes", nil, ""); w.Code != 200 || !strings.Contains(w.Body.String(), "The notes") {
		t.Fatalf("a bean a grant opens to her: %d %s", w.Code, w.Body.String())
	}
	if w := do("GET", "/served/bean?id=books", nil, ""); w.Code != 403 {
		t.Fatalf("a bean no grant opens to her is refused: %d", w.Code)
	}
	if w := do("POST", "/served/out", map[string]any{}, "https://daftar.example.org"); w.Code != 403 {
		t.Fatalf("a change without the session's own token is refused: %d", w.Code)
	}
	if w := do("POST", "/served/form", map[string]any{"id": "intake", "answers": []string{"I teach"}}, "https://daftar.example.org"); w.Code != 403 {
		t.Fatalf("answers without the session's own token are refused: %d", w.Code)
	}
	csrf = me["csrf"]
	if w := do("GET", "/served/forms", nil, ""); w.Code != 200 || !strings.Contains(w.Body.String(), "What do you do?") {
		t.Fatalf("the forms open to her: %d %s", w.Code, w.Body.String())
	}
	w = do("POST", "/served/form", map[string]any{"id": "intake", "person": "eve", "answers": []string{"I teach"}}, "https://daftar.example.org")
	if w.Code != 200 || !strings.Contains(w.Body.String(), "intake.ana.") {
		t.Fatalf("her answers are laid as hers — the session's person, whatever the request says: %d %s", w.Code, w.Body.String())
	}
	if w := do("POST", "/served/out", map[string]any{}, "https://daftar.example.org"); w.Code != 200 {
		t.Fatalf("signing out: %d", w.Code)
	}
	if w := do("GET", "/served/leads", nil, ""); w.Code != 401 {
		t.Fatalf("after signing out, nothing: %d", w.Code)
	}
}

// passkeyRig is a served handplace whose stand-in garden names ana's passkey in her bean. `post` asks the handler
// `mk` made last; `answer` signs a fresh challenge as her authenticator would, its signature counter at `count`; `mk`
// makes the handler again on the same state folder, as daftard started again would.
type passkeyRig struct {
	h      http.Handler
	mk     func() http.Handler
	key    *ecdsa.PrivateKey
	credID []byte
	state  string
}

func newPasskeyRig(t *testing.T) *passkeyRig {
	py, err := testpython.Path() // a Python that runs: on Windows, never the Store's stand-in
	if err != nil {
		t.Skip(err)
	}
	dir := t.TempDir()
	script := filepath.Join(dir, "worker.py")
	if err := os.WriteFile(script, []byte(standIn), 0o644); err != nil {
		t.Fatal(err)
	}
	key, _ := ecdsa.GenerateKey(elliptic.P256(), rand.Reader)
	x, y := make([]byte, 32), make([]byte, 32)
	key.X.FillBytes(x)
	key.Y.FillBytes(y)
	cose := append(append(append([]byte{0xa5, 0x01, 0x02, 0x03, 0x26, 0x20, 0x01, 0x21, 0x58, 0x20}, x...), 0x22, 0x58, 0x20), y...)
	credID := []byte("ana's credential, sixteen bytes+")
	t.Setenv("ANA_PASSKEY", passkey.Anchor(credID, cose))
	gc := config.Garden{Name: "g", Title: "The garden", Path: dir, Python: py, Served: true}
	g := &Garden{Conf: gc, Worker: worker.New(gc, script)}
	t.Cleanup(g.Worker.Close)
	st := t.TempDir()
	t.Setenv("DAFTARD_STATE", st)
	rig := &passkeyRig{key: key, credID: credID, state: st}
	rig.mk = func() http.Handler {
		s := &Server{Gardens: []*Garden{g}, Assets: assets.FS, Errors: guided.Open()}
		rig.h = s.ServedHandler([]string{"daftar.example.org"}, served.New())
		return rig.h
	}
	rig.mk()
	return rig
}

func (rig *passkeyRig) post(path string, body any) *httptest.ResponseRecorder {
	b, _ := json.Marshal(body)
	r := httptest.NewRequest("POST", "https://daftar.example.org"+path, bytes.NewReader(b))
	r.Host = "daftar.example.org"
	r.Header.Set("Content-Type", "application/json")
	r.Header.Set("Origin", "https://daftar.example.org")
	w := httptest.NewRecorder()
	rig.h.ServeHTTP(w, r)
	return w
}

func (rig *passkeyRig) answer(handle string, count uint32) map[string]any {
	w := rig.post("/served/passkey/challenge", map[string]any{})
	var c map[string]string
	_ = json.Unmarshal(w.Body.Bytes(), &c)
	ch, _ := b64.DecodeString(c["challenge"])
	cd, _ := json.Marshal(map[string]any{"type": "webauthn.get", "challenge": b64.EncodeToString(ch), "origin": "https://daftar.example.org"})
	rp := sha256.Sum256([]byte("daftar.example.org"))
	ad := append(rp[:], 0x05, byte(count>>24), byte(count>>16), byte(count>>8), byte(count))
	hc := sha256.Sum256(cd)
	d := sha256.Sum256(append(append([]byte(nil), ad...), hc[:]...))
	sig, _ := ecdsa.SignASN1(rand.Reader, rig.key, d[:])
	return map[string]any{"id": b64.EncodeToString(rig.credID), "clientDataJSON": b64.EncodeToString(cd),
		"authenticatorData": b64.EncodeToString(ad), "signature": b64.EncodeToString(sig), "userHandle": b64.EncodeToString([]byte(handle))}
}

// A PASSKEY SIGN-IN: the challenge spent once; the person and garden its user handle names; verified against the key
// that person's bean names (the stand-in's answer); a session begun — and a forged or replayed answer refused.
func TestServedPasskeySignIn(t *testing.T) {
	rig := newPasskeyRig(t)
	post := rig.post
	answer := func(handle string) map[string]any { return rig.answer(handle, 9) }
	good := answer("g/ana")
	w := post("/served/passkey/in", good)
	var cookie *http.Cookie
	for _, c := range w.Result().Cookies() {
		if c.Name == servedCookie {
			cookie = c
		}
	}
	if w.Code != 200 || cookie == nil || !cookie.Secure || !cookie.HttpOnly {
		t.Fatalf("her passkey signs her in: %d %s", w.Code, w.Body.String())
	}
	if w := post("/served/passkey/in", good); w.Code != 403 {
		t.Fatalf("an answer given again (its challenge spent) is refused: %d", w.Code)
	}
	forged := answer("g/ana")
	forged["signature"] = answer("g/ana")["signature"] // a signature over another challenge
	if w := post("/served/passkey/in", forged); w.Code != 403 {
		t.Fatalf("a signature that is not over this answer is refused: %d", w.Code)
	}
	if w := post("/served/passkey/in", answer("g/eve")); w.Code != 403 {
		t.Fatalf("a key no bean of that person names signs nobody in: %d", w.Code)
	}
	if w := post("/served/passkey/in", answer("elsewhere/ana")); w.Code != 403 {
		t.Fatalf("a garden not served here signs nobody in: %d", w.Code)
	}
	r := httptest.NewRequest("POST", "https://daftar.example.org/served/passkey/challenge", nil)
	r.Host = "daftar.example.org"
	r.Header.Set("Origin", "https://evil.example")
	w = httptest.NewRecorder()
	rig.h.ServeHTTP(w, r)
	if w.Code != 403 {
		t.Fatalf("a challenge asked from another origin is refused: %d", w.Code)
	}
}

// A PASSKEY'S SIGNATURE COUNTER (W3C WebAuthn §6.1.1, security audit 2026-10-10, 1.4): a sign-in whose counter does not
// grow past the last one seen — where either is not zero — is a cloned authenticator, and signs nobody in; the last
// count is kept in the machine's state folder, never in the garden, and outlives daftard started again. An
// authenticator that keeps no counter (always zero) signs in each time, and nothing is written for it.
func TestServedPasskeyCounter(t *testing.T) {
	rig := newPasskeyRig(t)
	in := func(count uint32) int {
		w := rig.post("/served/passkey/in", rig.answer("g/ana", count))
		return w.Code
	}
	for _, c := range []uint32{0, 0} {
		if code := in(c); code != 200 {
			t.Fatalf("an authenticator that keeps no counter signs in each time: %d at %d", code, c)
		}
	}
	if _, err := os.Stat(filepath.Join(rig.state, "passkey-counts.json")); !os.IsNotExist(err) {
		t.Fatalf("nothing is kept for a counter that stays at zero: %v", err)
	}
	if code := in(9); code != 200 {
		t.Fatalf("a counter that grows signs in: %d", code)
	}
	for _, c := range []uint32{9, 5, 0} {
		if code := in(c); code != 403 {
			t.Fatalf("a counter that does not grow past 9 (%d) is a cloned authenticator, refused: %d", c, code)
		}
	}
	if code := in(10); code != 200 {
		t.Fatalf("the genuine authenticator, its counter grown, still signs in: %d", code)
	}
	if err := private.Check(filepath.Join(rig.state, "passkey-counts.json")); err != nil {
		t.Fatalf("the last count is kept in the state folder, the account's alone: %v", err)
	}
	rig.mk() // daftard started again
	if code := in(10); code != 403 {
		t.Fatalf("the last count outlives a restart: a replayed 10 is refused: %d", code)
	}
	if code := in(11); code != 200 {
		t.Fatalf("after a restart, a counter that grows signs in: %d", code)
	}
	entries, _ := os.ReadDir(filepath.Dir(filepath.Join(rig.state, "x")))
	for _, e := range entries {
		if e.Name() != "passkey-counts.json" && e.Name() != "daftard.log" {
			t.Fatalf("the counter keeps one file in the state folder, nothing else: %s", e.Name())
		}
	}
}
