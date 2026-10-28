package garden

import (
	"strings"
	"testing"
)

// A document of nested aliases is refused, not walked (security audit 2026-10-10, 2.8); a few aliases still read.
func TestAliasesAreFew(t *testing.T) {
	var b strings.Builder
	b.WriteString("a: &a [x, x]\n")
	prev := "a"
	for i := 0; i < 40; i++ {
		n := "n" + strings.Repeat("i", i+1)
		b.WriteString(n + ": &" + n + " [*" + prev + ", *" + prev + "]\n")
		prev = n
	}
	if _, err := Load(b.String()); err == nil || !strings.Contains(err.Error(), "aliases") {
		t.Fatalf("nested aliases beyond the limit are refused: %v", err)
	}
	if v, err := Load("a: &a [x]\nb: *a\n"); err != nil || v == nil {
		t.Fatalf("a document with an alias still reads: %v", err)
	}
}
