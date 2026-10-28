package web

import (
	"strings"
	"testing"
)

// DAFTARD SPEAKS ITS READER'S LANGUAGE (the operator, 2026-10-14: the UI in English too): a refusal to a page of an
// English garden is in English, of a Persian garden in Persian, and where no garden tells, in both.
func TestARefusalIsInTheGardensLanguage(t *testing.T) {
	v := newViewRig(t, "view")
	if w := v.do("GET", "/api/view/page?g=g&page=..%2Fbeans", "", true); !strings.Contains(w.Body.String(), "این صفحه در این دفتر نیست") {
		t.Fatalf("a Persian garden: %s", w.Body.String())
	}
	v.s.Gardens[0].Conf.Lang = "en"
	w := v.do("GET", "/api/view/page?g=g&page=..%2Fbeans", "", true)
	if !strings.Contains(w.Body.String(), "This page is not in this garden") || strings.ContainsAny(w.Body.String(), "این") {
		t.Fatalf("an English garden: %s", w.Body.String())
	}
	if got := T(nil, "پیدا نشد.", "Not found."); got != "پیدا نشد. — Not found." {
		t.Fatalf("no garden to ask: both — %q", got)
	}
}
