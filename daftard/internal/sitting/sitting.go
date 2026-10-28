// Package sitting is who sits at a handplace's keyboard, and the key their saves are signed with (design §6).
//
// EACH PERSON WHO WRITES HAS A KEY, an identity anchor on their own bean (`name: { by: ssh, of: self, as: <its
// fingerprint> }`, which the gardener adds: class F). The key is made and kept by OpenSSH in its own format, under that
// person's own passphrase, in daftard's state folder: daftard writes no cryptography of its own. A SITTING is one
// person at the keyboard: begun by choosing who you are and giving your passphrase, which the key must open to, and
// ended by leaving or after a pause. Its passphrase is held in memory only, for the sitting, and the key is never
// written unlocked.
//
// A SAVE IN A SITTING IS THAT PERSON'S COMMIT: authored by them and signed by git's own SSH signing (`gpg.format ssh`),
// which runs `ssh-keygen -Y sign` on their key. ssh-keygen asks for the passphrase through SSH_ASKPASS, and daftard is
// that askpass: run with DAFTARD_ASKPASS set, the binary fetches one answer from the running daftard by a token issued
// for that one save (AskpassMain), and prints it. A token is good for the few asks one save makes, for a minute, and is
// taken back when the save is done; it is answered on the loopback alone.
package sitting

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"strings"
	"sync"
	"time"

	"github.com/0mit/daftar/daftard/internal/proc"
)

// AskpassVar is the environment variable that makes the binary an askpass: the address of one answer.
const AskpassVar = "DAFTARD_ASKPASS"

// AskpassPath is where daftard answers an askpass, on its own listener: AskpassPath + token.
const AskpassPath = "/askpass/"

var personRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}$`)

func token() string {
	b := make([]byte, 24)
	if _, err := rand.Read(b); err != nil {
		panic(err) // the system's randomness is gone: nothing here can be trusted after it
	}
	return hex.EncodeToString(b)
}

// ---------------------------------------------------------------------------------------------- the askpass

type answer struct {
	pass    string
	uses    int
	expires time.Time
}

// Askpass holds the answers daftard gives ssh-keygen, each by a one-time token.
type Askpass struct {
	Exe  string // the binary ssh-keygen runs as its askpass (daftard itself)
	Base string // where the running daftard answers: http://127.0.0.1:<port>

	mu      sync.Mutex
	answers map[string]answer
}

// NewAskpass is an Askpass that holds no answer yet.
func NewAskpass() *Askpass { return &Askpass{answers: map[string]answer{}} }

// Issue holds `pass` as the answer to `uses` asks within `ttl`, and returns the token they are asked by.
func (a *Askpass) Issue(pass string, uses int, ttl time.Duration) string {
	a.mu.Lock()
	defer a.mu.Unlock()
	t := token()
	a.answers[t] = answer{pass, uses, time.Now().Add(ttl)}
	return t
}

// Pending is how many answers are held: what was issued and neither taken back nor used up.
func (a *Askpass) Pending() []string {
	a.mu.Lock()
	defer a.mu.Unlock()
	out := []string{}
	for t := range a.answers {
		out = append(out, t[:6])
	}
	return out
}

// Revoke takes an answer back: what it was issued for is done.
func (a *Askpass) Revoke(t string) {
	a.mu.Lock()
	defer a.mu.Unlock()
	delete(a.answers, t)
}

func (a *Askpass) take(t string) (string, bool) {
	a.mu.Lock()
	defer a.mu.Unlock()
	now := time.Now()
	for k, v := range a.answers { // what has passed its time is gone, asked or not
		if now.After(v.expires) {
			delete(a.answers, k)
		}
	}
	v, ok := a.answers[t]
	if !ok {
		return "", false
	}
	if v.uses--; v.uses <= 0 {
		delete(a.answers, t)
	} else {
		a.answers[t] = v
	}
	return v.pass, true
}

// ServeHTTP answers GET AskpassPath+token from the loopback with the answer, once per use; anything else, nothing.
func (a *Askpass) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	host, _, _ := net.SplitHostPort(r.RemoteAddr)
	ip := net.ParseIP(host)
	pass, ok := "", false
	if r.Method == http.MethodGet && ip != nil && ip.IsLoopback() {
		pass, ok = a.take(strings.TrimPrefix(r.URL.Path, AskpassPath))
	}
	if !ok {
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	_, _ = io.WriteString(w, pass+"\n")
}

// Env is what makes ssh-keygen ask daftard, by `tok`: its askpass, always, and where the answer is.
func (a *Askpass) Env(tok string) []string {
	env := []string{"SSH_ASKPASS=" + a.Exe, "SSH_ASKPASS_REQUIRE=force", AskpassVar + "=" + a.Base + AskpassPath + tok}
	if os.Getenv("DISPLAY") == "" {
		env = append(env, "DISPLAY=:0") // older OpenSSH asks an askpass only where a display is named
	}
	return env
}

// AskpassMain is the binary run as ssh-keygen's askpass: it prints the one answer DAFTARD_ASKPASS names, or nothing
// and a failure, so that ssh-keygen gives up rather than waits.
func AskpassMain(args []string) int {
	url := os.Getenv(AskpassVar)
	if !strings.HasPrefix(url, "http://127.0.0.1:") && !strings.HasPrefix(url, "http://[::1]:") {
		return 1
	}
	cl := &http.Client{Timeout: 10 * time.Second}
	resp, err := cl.Get(url)
	if err != nil {
		return 1
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return 1
	}
	b, err := io.ReadAll(io.LimitReader(resp.Body, 4096))
	if err != nil {
		return 1
	}
	_, _ = os.Stdout.Write(b)
	return 0
}

// ---------------------------------------------------------------------------------------------- the keys

// Keys is where this machine keeps its people's keys: one file a person, OpenSSH's own format, under their passphrase.
type Keys struct{ Dir string }

// Path is a person's private key; its public key is Path + ".pub".
func (k Keys) Path(person string) string { return filepath.Join(k.Dir, person) }

// Has says whether this machine keeps a key for the person (a bean's id: never the machine's own key).
func (k Keys) Has(person string) bool {
	if !personRe.MatchString(person) {
		return false
	}
	_, err := os.Stat(k.Path(person))
	return err == nil
}

func keygen(ctx context.Context, env []string, args ...string) (string, error) {
	c := proc.CommandContext(ctx, "ssh-keygen", args...)
	c.Env = append(os.Environ(), env...)
	c.Stdin = nil // no terminal: the passphrase comes from the askpass alone
	out, err := c.CombinedOutput()
	return string(out), err
}

// Make makes a person's key under their passphrase, and returns its fingerprint (SHA256:…) for the gardener to add to
// their bean. A key the machine keeps already is never made over: a new key is a new identity, a class-F change.
func (k Keys) Make(person, pass string, a *Askpass) (string, error) {
	if !personRe.MatchString(person) {
		return "", fmt.Errorf("%q is no bean's id", person)
	}
	if k.Has(person) {
		return "", fmt.Errorf("this machine keeps a key for %s already", person)
	}
	if len(pass) < 8 {
		return "", errors.New("a passphrase is at least eight characters")
	}
	if err := os.MkdirAll(k.Dir, 0o700); err != nil {
		return "", err
	}
	tok := a.Issue(pass, 2, time.Minute) // a new key's passphrase is asked twice: given, and confirmed
	defer a.Revoke(tok)
	ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
	defer cancel()
	if out, err := keygen(ctx, a.Env(tok), "-q", "-t", "ed25519", "-C", person+"@daftard", "-f", k.Path(person)); err != nil {
		_ = os.Remove(k.Path(person))
		return "", fmt.Errorf("ssh-keygen: %v %s", err, strings.TrimSpace(out))
	}
	return k.Fingerprint(person)
}

// Fingerprint is a person's key's fingerprint, as OpenSSH prints it: SHA256:…
func (k Keys) Fingerprint(person string) (string, error) { return fingerprint(k.Path(person)) }

func fingerprint(path string) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	out, err := keygen(ctx, nil, "-l", "-f", path+".pub")
	if err != nil {
		return "", fmt.Errorf("ssh-keygen -l: %v %s", err, strings.TrimSpace(out))
	}
	if f := regexp.MustCompile(`SHA256:[A-Za-z0-9+/]{43}`).FindString(out); f != "" {
		return f, nil
	}
	return "", fmt.Errorf("ssh-keygen -l printed no fingerprint: %s", strings.TrimSpace(out))
}

// Unlocks says whether a person's key opens to the passphrase: what a sitting is begun on.
func (k Keys) Unlocks(person, pass string, a *Askpass) bool {
	if !personRe.MatchString(person) || !k.Has(person) {
		return false
	}
	tok := a.Issue(pass, 1, 30*time.Second)
	defer a.Revoke(tok)
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	out, err := keygen(ctx, a.Env(tok), "-y", "-f", k.Path(person))
	return err == nil && strings.HasPrefix(strings.TrimSpace(out), "ssh-")
}

// SignEnv is what a git commit made in a person's sitting runs with: authored and committed as them, and signed with
// their key, its passphrase asked of daftard by `tok`.
func (k Keys) SignEnv(person, name, email, tok string, a *Askpass) []string {
	return append([]string{
		"GIT_AUTHOR_NAME=" + name, "GIT_AUTHOR_EMAIL=" + email, "GIT_COMMITTER_NAME=" + name, "GIT_COMMITTER_EMAIL=" + email,
		"GIT_CONFIG_COUNT=3",
		"GIT_CONFIG_KEY_0=gpg.format", "GIT_CONFIG_VALUE_0=ssh",
		"GIT_CONFIG_KEY_1=user.signingkey", "GIT_CONFIG_VALUE_1=" + k.Path(person),
		"GIT_CONFIG_KEY_2=commit.gpgsign", "GIT_CONFIG_VALUE_2=true",
	}, a.Env(tok)...)
}

// THE MACHINE'S OWN KEY (design §6.5) signs only what the machine did on its own — a merge with no conflict (class I),
// a mailbox receipt — never a person's word. It is made on first use, with no passphrase, since nobody sits to give
// one; it lies in daftard's state folder, readable by this account alone, under a name no bean's id can take. Its
// fingerprint is added by the gardener to the bean of the host it is (class F), and a receiver takes what it signed
// only as far as that host's grants go.
func (k Keys) MachinePath() string { return filepath.Join(k.Dir, ".machine") }

// Machine makes the machine's key where there is none, and returns its fingerprint.
func (k Keys) Machine() (string, error) {
	if _, err := os.Stat(k.MachinePath()); err != nil {
		if err := os.MkdirAll(k.Dir, 0o700); err != nil {
			return "", err
		}
		if err := os.Chmod(k.Dir, 0o700); err != nil { // a folder made wider by someone else is narrowed first
			return "", err
		}
		ctx, cancel := context.WithTimeout(context.Background(), time.Minute)
		defer cancel()
		if out, err := keygen(ctx, nil, "-q", "-t", "ed25519", "-N", "", "-C", "machine@daftard", "-f", k.MachinePath()); err != nil {
			_ = os.Remove(k.MachinePath())
			return "", fmt.Errorf("ssh-keygen: %v %s", err, strings.TrimSpace(out))
		}
	}
	return fingerprint(k.MachinePath())
}

// MachineSignEnv is what a commit the machine makes on its own runs with: authored and committed as the host's bean,
// signed with the machine's key, which asks nothing.
func (k Keys) MachineSignEnv(host, email string) []string {
	return []string{
		"GIT_AUTHOR_NAME=" + host, "GIT_AUTHOR_EMAIL=" + email, "GIT_COMMITTER_NAME=" + host, "GIT_COMMITTER_EMAIL=" + email,
		"GIT_CONFIG_COUNT=3",
		"GIT_CONFIG_KEY_0=gpg.format", "GIT_CONFIG_VALUE_0=ssh",
		"GIT_CONFIG_KEY_1=user.signingkey", "GIT_CONFIG_VALUE_1=" + k.MachinePath(),
		"GIT_CONFIG_KEY_2=commit.gpgsign", "GIT_CONFIG_VALUE_2=true",
	}
}

// ---------------------------------------------------------------------------------------------- the sittings

// Sitting is one person at the keyboard.
type Sitting struct {
	Person string
	pass   string
	Since  time.Time
	last   time.Time
}

// Pass is the passphrase the sitting was begun with, held in memory for its saves.
func (s *Sitting) Pass() string { return s.pass }

// Sittings are this daftard's, each by the cookie its page holds.
type Sittings struct {
	Pause time.Duration
	mu    sync.Mutex
	by    map[string]*Sitting
}

// NewSittings ends a sitting after `pause` with nothing done in it.
func NewSittings(pause time.Duration) *Sittings {
	return &Sittings{Pause: pause, by: map[string]*Sitting{}}
}

// Begin begins a person's sitting, its passphrase already checked against their key; the cookie names it.
func (s *Sittings) Begin(person, pass string) string {
	s.mu.Lock()
	defer s.mu.Unlock()
	c := token()
	now := time.Now()
	s.by[c] = &Sitting{Person: person, pass: pass, Since: now, last: now}
	return c
}

// Get is the sitting the cookie names, if it has not ended; asking keeps it going.
func (s *Sittings) Get(cookie string) (*Sitting, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	st, ok := s.by[cookie]
	if !ok {
		return nil, false
	}
	if time.Since(st.last) > s.Pause {
		delete(s.by, cookie)
		return nil, false
	}
	st.last = time.Now()
	return st, true
}

// End ends a sitting: its passphrase is forgotten.
func (s *Sittings) End(cookie string) {
	s.mu.Lock()
	defer s.mu.Unlock()
	delete(s.by, cookie)
}
