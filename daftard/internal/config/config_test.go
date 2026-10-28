package config

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

// a host key of no host's: made for this test by ssh-keygen, and the line ssh-keygen -H hashed for
// register.example.org — ssh's own hashing, not this package's, to hold PinnedIn to
const testKey = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGjCMmqNQtxRPFwT+M+YYT9ifckH9U7mkGsMFoORWvVc"
const hashedLine = "|1|a7cnAsdk019dy65ueHPT67BmewQ=|aiOdRaXjq8FQd6gNk/HW9XwcfcM= ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGjCMmqNQtxRPFwT+M+YYT9ifckH9U7mkGsMFoORWvVc"

// A REGISTER BY ROUTES: `url` alone is still one route; each route is held to what the one address was held to; an ssh
// route is taken only where its host's key is pinned in the state folder, in a file nobody else may change.
func TestRegisterRoutes(t *testing.T) {
	t.Setenv("DAFTARD_STATE", t.TempDir())
	r := &Register{Series: "19.0", DB: "db", Bean: "the-register"}
	_ = os.MkdirAll(filepath.Dir(r.KnownHostsFile("g")), 0o700)
	pin := func(text string) {
		if err := os.WriteFile(r.KnownHostsFile("g"), []byte(text), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	ssh := func(host string, port int) Route {
		return Route{Via: "ssh", Host: host, Port: port, User: "tunnel", To: "127.0.0.1:8069"}
	}
	pin("register.example.org " + testKey + "\n[register.example.org]:2222 " + testKey + "\n")
	good := map[string]Register{
		"url alone, as before":          {URL: "https://register.example.org"},
		"url on the loopback, plain":    {URL: "http://127.0.0.1:8069"},
		"https, then ssh":               {Routes: []Route{{Via: "https", URL: "https://register.example.org:8443/"}, ssh("register.example.org", 0)}},
		"ssh at another port":           {Routes: []Route{ssh("register.example.org", 2222)}},
		"plain on the loopback, as one": {Routes: []Route{{Via: "https", URL: "http://localhost:18080"}}},
	}
	for name, c := range good {
		c.Series, c.DB, c.Bean = r.Series, r.DB, r.Bean
		if err := c.Check("g"); err != nil {
			t.Errorf("%s: refused: %v", name, err)
		}
	}
	bad := map[string]Register{
		"plain HTTP beyond the loopback": {Routes: []Route{{Via: "https", URL: "http://203.0.113.10:8069"}}},
		"a path":                         {Routes: []Route{{Via: "https", URL: "https://register.example.org/odoo"}}},
		"a name and password":            {Routes: []Route{{Via: "https", URL: "https://a:b@register.example.org"}}},
		"a query":                        {Routes: []Route{{Via: "https", URL: "https://register.example.org/?db=x"}}},
		"no address":                     {},
		"both url and routes":            {URL: "https://register.example.org", Routes: []Route{{Via: "https", URL: "https://register.example.org"}}},
		"a route of no kind":             {Routes: []Route{{Via: "vpn", URL: "https://register.example.org"}}},
		"an https route with a host":     {Routes: []Route{{Via: "https", URL: "https://register.example.org", Host: "x"}}},
		"an ssh route with a url":        {Routes: []Route{{Via: "ssh", URL: "https://x", Host: "register.example.org", User: "tunnel", To: "127.0.0.1:8069"}}},
		"ssh to a host not pinned":       {Routes: []Route{ssh("other.example.org", 0)}},
		"ssh at a port not pinned":       {Routes: []Route{ssh("register.example.org", 2200)}},
		"ssh to an option":               {Routes: []Route{ssh("-oProxyCommand=x", 0)}},
		"ssh as an option":               {Routes: []Route{{Via: "ssh", Host: "register.example.org", User: "-l", To: "127.0.0.1:8069"}}},
		"ssh as user@":                   {Routes: []Route{{Via: "ssh", Host: "register.example.org", User: "a@b", To: "127.0.0.1:8069"}}},
		"ssh forwarding nowhere":         {Routes: []Route{{Via: "ssh", Host: "register.example.org", User: "tunnel", To: "127.0.0.1"}}},
		"ssh forwarding to a bad port":   {Routes: []Route{{Via: "ssh", Host: "register.example.org", User: "tunnel", To: "127.0.0.1:0"}}},
		"too many routes":                {Routes: make([]Route, MaxRoutes+1)},
	}
	for name, c := range bad {
		c.Series, c.DB, c.Bean = r.Series, r.DB, r.Bean
		if err := c.Check("g"); err == nil {
			t.Errorf("%s: taken", name)
		}
	}
	one := Register{Series: "19.0", DB: "db", Bean: "b", Routes: []Route{ssh("register.example.org", 0)}}
	for name, text := range map[string]string{
		"hashed, as ssh-keygen -H writes it": hashedLine + "\n",
		"by a pattern":                       "*.example.org,!other.example.org " + testKey + "\n",
		"as a certificate authority":         "@cert-authority register.example.org " + testKey + "\n",
	} {
		pin(text)
		if err := one.Check("g"); err != nil {
			t.Errorf("pinned %s: refused: %v", name, err)
		}
	}
	for name, text := range map[string]string{
		"revoked":                     "@revoked register.example.org " + testKey + "\n",
		"negated":                     "*.example.org,!register.example.org " + testKey + "\n",
		"a name and no key":           "register.example.org\n",
		"hashed for another host":     strings.Replace(hashedLine, "|1|", "|1|A", 1) + "\n",
		"another port's, taken as 22": "[register.example.org]:2222 " + testKey + "\n",
		"commented out":               "#register.example.org " + testKey + "\n",
	} {
		pin(text)
		if err := one.Check("g"); err == nil {
			t.Errorf("pinned %s: taken", name)
		}
	}
	_ = os.Remove(r.KnownHostsFile("g"))
	if err := one.Check("g"); err == nil || !strings.Contains(err.Error(), "no host key pinned") {
		t.Errorf("no known_hosts at all: %v", err)
	}
	if runtime.GOOS != "windows" {
		pin("register.example.org " + testKey + "\n")
		_ = os.Chmod(r.KnownHostsFile("g"), 0o666)
		if err := one.Check("g"); err == nil || !strings.Contains(err.Error(), "0600") {
			t.Errorf("a pin others may change: %v", err)
		}
	}
	if w := (&Register{URL: "https://register.example.org"}).Ways(); len(w) != 1 || w[0].Via != "https" || w[0].URL != "https://register.example.org" {
		t.Errorf("url alone is one https route: %+v", w)
	}
}
