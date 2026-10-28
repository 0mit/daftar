package garden

import (
	"os"
	"path/filepath"
	"testing"
)

func TestStatements(t *testing.T) {
	dir := t.TempDir()
	f := filepath.Join(dir, "x.md")
	text := "\ufeff---\nbean: x\nkind: event\ntitle: \"x\"\nstatements:\n  - say: { by: sam, at: now }\n" +
		"  - be: { by: self, at: [now, \"walk#step\"] }\n  - not-one-verb\n---\nThe body.\n"
	if err := os.WriteFile(f, []byte(text), 0o644); err != nil {
		t.Fatal(err)
	}
	b, err := ReadBean(f)
	if err != nil {
		t.Fatal(err)
	}
	if b.ID != "x" || b.Kind != "event" || b.Title != "x" || b.Body != "\nThe body.\n" || len(b.Statements) != 2 {
		t.Fatalf("a bean's header, body and statements: %+v", b)
	}
	if s := b.Statements[1]; s.Verb != "be" || s.Roles.Get("by") != "self" ||
		len(s.Roles.Get("at").([]any)) != 2 || s.Roles.Keys[1] != "at" {
		t.Fatalf("a statement is its verb and its roles, in order: %+v", s)
	}
	if _, _, ok := SplitFrontMatter("no fence\n---\n"); ok {
		t.Fatal("a document that does not open with a fence has no front matter")
	}
}
