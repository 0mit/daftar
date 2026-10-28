// Package hubkey is this machine's hub of a garden as daftard holds it: the hub's own key, and the signing of what
// daftard writes for the garden on its own (the operator's decision of 2026-10-13: "each garden hub, when it is
// initialized for a garden, makes its own unique signing key, and every commit the hub itself writes is signed with
// it").
//
// THE KEY IS MADE BY THE GARDEN'S OWN TOOL, never here: `bin/hub.py install <working copy>` is the hub's init, and makes
// it once — ed25519, no passphrase, since nobody sits to give one — in this account's daftar state folder, which is
// daftard's own (state.Dir: DAFTARD_STATE, %LOCALAPPDATA%\Daftar, or $XDG_STATE_HOME/daftar), under hubs/<garden id>/:
// outside every working copy and every repository, so no copy, backup or synchronised folder of the garden carries it.
// Its fingerprint goes on the hub's bean in the garden, `name: { by: ssh, of: self, as: "SHA256:…" }`, which the
// gardener adds (class F), and a hub takes what it signs as far as that bean's grants go (bin/hub.py), like any
// writer's. What a person decides is never signed with it: that is the person's, with their own key in their sitting.
package hubkey

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"strings"
	"time"

	gardenfm "github.com/0mit/daftar/daftard/internal/garden"
	"github.com/0mit/daftar/daftard/internal/private"
	"github.com/0mit/daftar/daftard/internal/proc"
)

var idRe = regexp.MustCompile(`^[0-9a-f]{12}$`)
var beanRe = regexp.MustCompile(`^[a-z0-9][a-z0-9-]{0,63}$`)
var fprRe = regexp.MustCompile(`SHA256:[A-Za-z0-9+/]{43}`)

// ID is a garden's id, read as its gate reads it (bin/parse.py garden_id): the first twelve hexadecimal digits of the
// root of its first-parent history; "" where git cannot say, or the clone is shallow and cannot see its root.
func ID(garden string) string {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	if out, err := proc.CommandContext(ctx, proc.Git(), "-C", garden, "rev-parse", "--is-shallow-repository").Output(); err != nil ||
		strings.TrimSpace(string(out)) == "true" {
		return ""
	}
	out, err := proc.CommandContext(ctx, proc.Git(), "-C", garden, "rev-list", "--first-parent", "--max-parents=0", "HEAD").Output()
	if err != nil {
		return ""
	}
	roots := strings.Fields(string(out))
	if len(roots) == 0 || len(roots[len(roots)-1]) < 12 {
		return ""
	}
	return roots[len(roots)-1][:12]
}

// Path is where the hub's key of the garden `id` lies, in the state folder `state`; its public half is Path + ".pub".
func Path(state, id string) string { return filepath.Join(state, "hubs", id, "key") }

// Key is a garden's hub key on this machine.
type Key struct {
	Path        string // the private key, which git hands ssh-keygen and nothing else ever reads
	Fingerprint string // SHA256:…, as the hub's bean names it
	Public      string // the public line
}

// ErrNone is a garden whose hub on this machine has no key yet: bin/hub.py install makes it.
var ErrNone = errors.New("this machine's hub of the garden has no key yet")

// Find is the hub's key of the garden at `garden`, as `bin/hub.py install` made it in the state folder `state`. Its
// folder and the key are narrowed to this account again first (a wider mode set since is closed, as the state folder
// is on every start), and a key another account could still read is refused: what any other account may read signs as
// nobody's hub. ErrNone where there is no key.
func Find(state, garden string) (Key, error) {
	id := ID(garden)
	if !idRe.MatchString(id) {
		return Key{}, fmt.Errorf("%s: no garden id to find its hub's key by (not a repository, or a shallow clone)", garden)
	}
	p := Path(state, id)
	if _, err := os.Stat(p); errors.Is(err, os.ErrNotExist) {
		return Key{}, ErrNone
	} else if err != nil {
		return Key{}, err
	}
	if runtime.GOOS != "windows" {
		_ = os.Chmod(filepath.Dir(p), 0o700)
		_ = os.Chmod(p, 0o600)
	}
	for _, x := range []string{filepath.Dir(p), p} {
		if err := private.Check(x); err != nil {
			return Key{}, fmt.Errorf("the hub's key is not this account's alone, and signs nothing: %v", err)
		}
	}
	pub, err := os.ReadFile(p + ".pub")
	if err != nil {
		return Key{}, fmt.Errorf("the hub's key has no public half beside it: %v", err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	out, err := proc.CommandContext(ctx, "ssh-keygen", "-l", "-f", p+".pub").CombinedOutput()
	f := fprRe.FindString(string(out))
	if err != nil || f == "" {
		return Key{}, fmt.Errorf("ssh-keygen -l: %v %s", err, strings.TrimSpace(string(out)))
	}
	return Key{Path: p, Fingerprint: f, Public: strings.TrimSpace(string(pub))}, nil
}

// Statement is what the gardener adds to the hub's bean (class F): its key, a name the namespace ssh gives once.
func (k Key) Statement() string {
	return fmt.Sprintf(`name: { by: ssh, of: self, as: "%s" }`, k.Fingerprint)
}

// SignEnv is what a commit the hub writes runs with: authored and committed as the hub's bean, and signed with the
// hub's key by git's own SSH signing, which asks nothing.
func (k Key) SignEnv(bean, email string) []string {
	return []string{
		"GIT_AUTHOR_NAME=" + bean, "GIT_AUTHOR_EMAIL=" + email, "GIT_COMMITTER_NAME=" + bean, "GIT_COMMITTER_EMAIL=" + email,
		"GIT_CONFIG_COUNT=3",
		"GIT_CONFIG_KEY_0=gpg.format", "GIT_CONFIG_VALUE_0=ssh",
		"GIT_CONFIG_KEY_1=user.signingkey", "GIT_CONFIG_VALUE_1=" + k.Path,
		"GIT_CONFIG_KEY_2=commit.gpgsign", "GIT_CONFIG_VALUE_2=true",
	}
}

// Params are what a step daftard takes on its own for a garden is asked with, the worker's way (`by` and `sign`): the
// hub's bean, whom the commit is by, and the hub's signing. `email` is the bean's address in the garden's own name,
// one nobody's mail reaches.
func (k Key) Params(bean, garden string) map[string]any {
	sign := map[string]string{}
	for _, kv := range k.SignEnv(bean, bean+"@"+garden+".daftar.invalid") {
		if name, v, ok := strings.Cut(kv, "="); ok {
			sign[name] = v
		}
	}
	return map[string]any{"by": bean, "sign": sign}
}

// Install is the hub's init on this machine for the garden at `garden`: the garden's own `bin/hub.py install`, run on
// its working copy with the garden's Python and this account's state folder (`state`, which hub.py reads as
// DAFTARD_STATE), making the hub's key where there is none. What it printed is returned for the person installing:
// the fingerprint and the statement for the hub's bean, never the key. A release whose bin/hub.py makes no key yet is
// left alone (its `install` would write a hook into the working copy's tree), and said so: the hub then signs nothing.
func Install(python, garden, state string) (string, error) {
	tool := filepath.Join(garden, "bin", "hub.py")
	if _, err := os.Stat(tool); err != nil {
		return "", fmt.Errorf("%s has no bin/hub.py: the garden's release keeps no hub", garden)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Minute)
	defer cancel()
	run := func(args ...string) (string, int, error) {
		c := proc.CommandContext(ctx, python, append([]string{tool}, args...)...)
		c.Dir = garden
		c.Env = append(os.Environ(), "DAFTARD_STATE="+state, "PYTHONUTF8=1", "PYTHONIOENCODING=utf-8")
		out, err := c.CombinedOutput()
		code := 0
		var ee *exec.ExitError
		if errors.As(err, &ee) {
			code, err = ee.ExitCode(), nil
		}
		return string(out), code, err
	}
	// `key` is the command a release that makes hub keys has; an older one answers it with its usage, and exit 2
	if _, code, err := run("key", garden); err != nil {
		return "", err
	} else if code == 2 {
		return "", errors.New("this garden's release makes no hub key yet (bin/hub.py has no `key`): daftard signs " +
			"nothing as the hub until the garden adopts a release that does")
	}
	out, code, err := run("install", garden)
	if err != nil {
		return out, err
	}
	if code != 0 {
		return out, fmt.Errorf("bin/hub.py install: exit %d", code)
	}
	return out, nil
}

// Named says whether the garden, as its last commit holds it, names this key on the hub's bean `bean`: a `name` the
// namespace ssh gives, of the bean itself, not sealed; or, in a garden in today's words, an identity anchor
// `ssh_key_fingerprint` — as bin/hub.py finds a writer (`writer_of`). A hub judges a merge's writer at its first
// parent, the clone's last commit, so what that commit does not name, a hub refuses: daftard signs as the hub only
// once it is named there, and until then the hub merges nothing, and a merge waits.
func (k Key) Named(garden, bean string) (bool, error) {
	if !beanRe.MatchString(bean) {
		return false, fmt.Errorf("%q is no bean's id", bean)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	out, err := proc.CommandContext(ctx, proc.Git(), "-C", garden, "show", "HEAD:beans/"+bean+".md").Output()
	if err != nil {
		return false, nil // no such bean at the last commit: nothing names the key
	}
	text := strings.ReplaceAll(strings.ReplaceAll(string(out), "\r\n", "\n"), "\r", "\n")
	front, _, ok := gardenfm.SplitFrontMatter(text)
	if !ok {
		return false, nil
	}
	v, err := gardenfm.Load(front)
	if err != nil {
		return false, fmt.Errorf("beans/%s.md: %v", bean, err)
	}
	m, isMap := v.(*gardenfm.Map)
	if !isMap {
		return false, nil
	}
	if list, ok := m.Get("statements").([]any); ok {
		for _, x := range list {
			sm, ok := x.(*gardenfm.Map)
			if !ok || len(sm.Keys) != 1 || sm.Keys[0] != "name" {
				continue
			}
			r, ok := sm.Vals["name"].(*gardenfm.Map)
			if !ok || r.Get("held") != nil {
				continue
			}
			of, _ := r.Get("of").(string)
			if r.Get("by") == "ssh" && r.Get("as") == k.Fingerprint && (r.Get("of") == nil || of == "self" || of == bean) {
				return true, nil
			}
		}
	}
	if id, ok := m.Get("identity").(*gardenfm.Map); ok { // a garden in today's words: its identity anchors
		if list, ok := id.Get("anchors").([]any); ok {
			for _, x := range list {
				a, ok := x.(*gardenfm.Map)
				if ok && a.Get("key") == "ssh_key_fingerprint" && a.Get("value") == k.Fingerprint {
					return true, nil
				}
			}
		}
	}
	return false, nil
}

// ValidBean says whether s can be a hub's bean in daftard.json: a bean's id.
func ValidBean(s string) bool { return beanRe.MatchString(s) }
