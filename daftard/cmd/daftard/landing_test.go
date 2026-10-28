package main

import "testing"

func TestLanding(t *testing.T) {
	good := map[string]string{
		"daftar://go/home/pending/example-decision":              "/go/home/pending/example-decision",
		"daftar://go/home/pending/example-decision/":             "/go/home/pending/example-decision/",
		"daftar://go/home":                                       "/go/home",
		"daftar:go/home/sync":                                    "/go/home/sync",
		"DAFTAR://go/home/error/E-7K2M-Q9XD":                     "/go/home/error/E-7K2M-Q9XD",
		"daftar://go/home/proposal/PROPOSAL-other-20261008-1200": "/go/home/proposal/PROPOSAL-other-20261008-1200",
		"/go/my-garden/case/c-2026-001":                          "/go/my-garden/case/c-2026-001",
		// the page of Odoo's own client for a garden (OdooRe), as a daftar: link or as its path
		"daftar://odoo?g=home&series=19.0":         "/odoo?g=home&series=19.0",
		"daftar:odoo?g=home&series=19.0":           "/odoo?g=home&series=19.0",
		"daftar:/odoo?g=home":                      "/odoo?g=home",
		"/odoo?g=my-garden&series=19.0":            "/odoo?g=my-garden&series=19.0",
		"/odoo?g=home&series=17.0&asof=2026-10-01": "/odoo?g=home&series=17.0&asof=2026-10-01",
	}
	for in, want := range good {
		if got, ok := landing(in); !ok || got != want {
			t.Errorf("landing(%q) = %q, %v; want %q", in, got, ok, want)
		}
	}
	for _, in := range []string{
		"daftar://evil.example/go/home", "https://evil.example/go/home", "//evil.example/go/home", "/go//evil.example",
		"daftar://go/home/delete/everything", "daftar://go/home/pending/../../api/stop", "daftar://go/home/pending/a b",
		"daftar://go/home/pending/x?then=/api/stop", "javascript:alert(1)", "home", "", "/go/",
		"/odoo?g=home&series=19.0&then=/api/stop", "/odoo?series=19.0&g=home", "/odoo?g=", "/odoo", "/odoo/?g=home",
		"/odoo?g=home%0d%0aSet-Cookie:a=b", "/odoo/web?g=home", "//evil.example/odoo?g=home", "daftar://odoo/x?g=home",
		"daftar://odoo?g=home#top", "daftar://evil.example/odoo?g=home", "daftar://user@odoo?g=home",
		"https://evil.example/odoo?g=home", "daftar://odoo?g=home&series=19", "daftar:odoo/web?g=home",
	} {
		if got, ok := landing(in); ok {
			t.Errorf("landing(%q) = %q; want refused", in, got)
		}
	}
}

// `daftard open` passes a landing on as the page's `to`, a garden's name as its `g`, and anything else not at all.
func TestOpenAddress(t *testing.T) {
	const base = "http://127.0.0.1:8770"
	cases := map[string]string{
		"/odoo?g=home&series=19.0":         "/?once=c&to=%2Fodoo%3Fg%3Dhome%26series%3D19.0",
		"daftar://odoo?g=home&series=19.0": "/?once=c&to=%2Fodoo%3Fg%3Dhome%26series%3D19.0",
		"daftar://go/home/pending/x":       "/?once=c&to=%2Fgo%2Fhome%2Fpending%2Fx",
		"home":                             "/?once=c&g=home",
	}
	for in, want := range cases {
		if got, read := address(base, "c", []string{in}); got != base+want || !read {
			t.Errorf("open %q → %s, %v; want %s", in, got, read, base+want)
		}
	}
	// not OdooRe's one form, nor a landing, nor a garden's name: the front page, the address passed on nowhere
	for _, in := range []string{"/odoo?series=19.0&g=home", "/odoo?g=home&then=/api/stop", "daftar://evil.example/go/home",
		"home/../x"} {
		if got, read := address(base, "c", []string{in}); got != base+"/?once=c" || read {
			t.Errorf("open %q → %s, %v; want the front page, unread", in, got, read)
		}
	}
	if got, read := address(base, "c", nil); got != base+"/?once=c" || !read {
		t.Errorf("open → %s", got)
	}
}
