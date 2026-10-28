package sitting

import (
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/0mit/daftar/daftard/internal/private"
)

// The test binary is its own askpass, as daftard is: run with DAFTARD_ASKPASS set, it answers ssh-keygen and exits.
func TestMain(m *testing.M) {
	if os.Getenv(AskpassVar) != "" {
		os.Exit(AskpassMain(os.Args[1:]))
	}
	os.Exit(m.Run())
}

// an Askpass served on the loopback, as daftard serves it on its own listener
func served(t *testing.T) (*Askpass, string) {
	t.Helper()
	a := NewAskpass()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	mux := http.NewServeMux()
	mux.Handle(AskpassPath, a)
	srv := &http.Server{Handler: mux}
	go func() { _ = srv.Serve(ln) }()
	t.Cleanup(func() { _ = srv.Close() })
	exe, _ := os.Executable()
	a.Exe, a.Base = exe, "http://"+ln.Addr().String()
	return a, ln.Addr().String()
}

func git(t *testing.T, dir string, env []string, args ...string) string {
	t.Helper()
	c := exec.Command("git", args...)
	c.Dir = dir
	c.Env = append(os.Environ(), env...)
	out, err := c.CombinedOutput()
	if err != nil {
		t.Fatalf("git %v: %v %s", args, err, out)
	}
	return string(out)
}

func TestKeyMadeUnlockedAndSigning(t *testing.T) {
	if _, err := exec.LookPath("ssh-keygen"); err != nil {
		t.Skip("no ssh-keygen on this machine")
	}
	a, _ := served(t)
	k := Keys{Dir: t.TempDir()}
	fpr, err := k.Make("ada", "her own words", a)
	if err != nil || !strings.HasPrefix(fpr, "SHA256:") {
		t.Fatalf("a key is made under a passphrase, its fingerprint read: %q %v", fpr, err)
	}
	raw, _ := os.ReadFile(k.Path("ada"))
	if !strings.Contains(string(raw), "OPENSSH PRIVATE KEY") || k.Unlocks("ada", "", a) || k.Unlocks("ada", "not hers", a) {
		t.Fatalf("the key is kept in OpenSSH's own format, and opens to no other passphrase")
	}
	if !k.Unlocks("ada", "her own words", a) {
		t.Fatalf("the key opens to its own passphrase")
	}
	if _, err := k.Make("ada", "again", a); err == nil {
		t.Fatalf("a person's key is never made over another")
	}
	if len(a.answers) != 0 {
		t.Fatalf("every answer is taken back when what asked for it is done: %d left", len(a.answers))
	}

	// a commit made in her sitting is authored and signed by her, and verifies against her key
	dir := t.TempDir()
	git(t, dir, nil, "init", "-q")
	if err := os.WriteFile(filepath.Join(dir, "f"), []byte("x\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	git(t, dir, nil, "add", "f")
	tok := a.Issue("her own words", 4, time.Minute)
	defer a.Revoke(tok)
	git(t, dir, k.SignEnv("ada", "Ada", "ada@example.org", tok, a), "commit", "-q", "-m", "hers")
	pub, _ := os.ReadFile(k.Path("ada") + ".pub")
	allowed := filepath.Join(t.TempDir(), "allowed")
	if err := os.WriteFile(allowed, []byte("ada@example.org "+string(pub)), 0o644); err != nil {
		t.Fatal(err)
	}
	log := git(t, dir, nil, "-c", "gpg.ssh.allowedSignersFile="+allowed, "log", "--show-signature", "--format=%an <%ae>", "-1")
	if !strings.Contains(log, `Good "git" signature for ada@example.org`) || !strings.Contains(log, "Ada <ada@example.org>") {
		t.Fatalf("her commit is hers, signed by her key: %s", log)
	}
}

func TestAnswersAreOneTime(t *testing.T) {
	a, addr := served(t)
	tok := a.Issue("secret", 1, time.Minute)
	get := func(path string) (int, string) {
		resp, err := http.Get("http://" + addr + path)
		if err != nil {
			t.Fatal(err)
		}
		defer resp.Body.Close()
		b := make([]byte, 64)
		n, _ := resp.Body.Read(b)
		return resp.StatusCode, string(b[:n])
	}
	if code, body := get(AskpassPath + tok); code != 200 || body != "secret\n" {
		t.Fatalf("an answer is given once: %d %q", code, body)
	}
	if code, _ := get(AskpassPath + tok); code != 404 {
		t.Fatalf("and never twice: %d", code)
	}
	if code, _ := get(AskpassPath + "nonsense"); code != 404 {
		t.Fatalf("a token nobody issued is answered nothing: %d", code)
	}
	old := a.Issue("stale", 3, -time.Second)
	if code, _ := get(AskpassPath + old); code != 404 {
		t.Fatalf("an answer past its time is gone: %d", code)
	}
}

func TestSittings(t *testing.T) {
	s := NewSittings(time.Hour)
	c := s.Begin("ada", "her own words")
	if got, ok := s.Get(c); !ok || got.Person != "ada" || got.Pass() != "her own words" {
		t.Fatalf("a sitting is its person's, with their passphrase: %+v %v", got, ok)
	}
	if _, ok := s.Get("another cookie"); ok {
		t.Fatalf("no sitting answers to a cookie it did not give")
	}
	s.End(c)
	if _, ok := s.Get(c); ok {
		t.Fatalf("a sitting ended is gone")
	}
	short := NewSittings(time.Millisecond)
	c2 := short.Begin("ben", "his")
	time.Sleep(5 * time.Millisecond)
	if _, ok := short.Get(c2); ok {
		t.Fatalf("a sitting ends after its pause")
	}
}

// THE MACHINE'S OWN KEY: made once with no passphrase, never under a person's name, the same key every time after; a
// commit the machine makes on its own is authored as its host's bean and verifies against that key, asking nothing.
func TestTheMachinesOwnKey(t *testing.T) {
	if _, err := exec.LookPath("ssh-keygen"); err != nil {
		t.Skip("no ssh-keygen on this machine")
	}
	k := Keys{Dir: t.TempDir()}
	fpr, err := k.Machine()
	if err != nil || !strings.HasPrefix(fpr, "SHA256:") {
		t.Fatalf("the machine's key is made on first use, its fingerprint read: %q %v", fpr, err)
	}
	if again, err := k.Machine(); err != nil || again != fpr {
		t.Fatalf("and is the same key after: %q %v", again, err)
	}
	if personRe.MatchString(filepath.Base(k.MachinePath())) || k.Has(filepath.Base(k.MachinePath())) {
		t.Fatalf("its name is no bean's id, so no person's key is it")
	}
	if err := private.Check(k.Dir); err != nil { // its mode on Linux and macOS, its access list on Windows
		t.Fatalf("it lies in a folder this account alone reads: %v", err)
	}
	dir := t.TempDir()
	git(t, dir, nil, "init", "-q")
	git(t, dir, k.MachineSignEnv("box", "box@g.daftar.invalid"), "commit", "-q", "--allow-empty", "-m", "merged")
	pub, _ := os.ReadFile(k.MachinePath() + ".pub")
	allowed := filepath.Join(t.TempDir(), "allowed")
	if err := os.WriteFile(allowed, []byte("box@g.daftar.invalid "+string(pub)), 0o644); err != nil {
		t.Fatal(err)
	}
	log := git(t, dir, nil, "-c", "gpg.ssh.allowedSignersFile="+allowed, "log", "--show-signature", "--format=%an <%ae>", "-1")
	if !strings.Contains(log, `Good "git" signature for box@g.daftar.invalid`) || !strings.Contains(log, "box <box@g.daftar.invalid>") {
		t.Fatalf("a commit the machine made is its host's, signed by its key: %s", log)
	}
}
