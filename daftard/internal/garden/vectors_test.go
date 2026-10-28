package garden

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

// frontMatterVectors is daftar's test/vectors/front-matter.json, copied here byte for byte: each document's text and
// how bin/parse.py split_front_matter splits it — its front matter (null where it is not fenced) and its body.
const frontMatterVectors = "testdata/front-matter.json"

// TestFrontMatterVectors: this port splits every document of the vectors as daftar's one splitter does, so a bean
// cannot read one way here and another way in the garden's own tools.
func TestFrontMatterVectors(t *testing.T) {
	raw, err := os.ReadFile(frontMatterVectors)
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Cases []struct {
			Name  string  `json:"name"`
			Text  string  `json:"text"`
			Front *string `json:"front"`
			Body  string  `json:"body"`
		} `json:"cases"`
	}
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	if len(doc.Cases) < 17 {
		t.Fatalf("%d cases: the vectors are daftar's whole file, and it holds 17", len(doc.Cases))
	}
	for _, c := range doc.Cases { // the front matter and the body, each said where it differs
		front, body, ok := SplitFrontMatter(c.Text)
		switch {
		case c.Front == nil && ok:
			t.Errorf("%s: daftar finds no front matter, and this one finds %q", c.Name, front)
		case c.Front != nil && !ok:
			t.Errorf("%s: daftar finds the front matter %q, and this one none", c.Name, *c.Front)
		case c.Front != nil && front != *c.Front:
			t.Errorf("%s: the front matter is %q, and this one reads %q", c.Name, *c.Front, front)
		}
		if body != c.Body {
			t.Errorf("%s: the body is %q, and this one reads %q", c.Name, c.Body, body)
		}
	}
}

// TestFrontMatterVectorsAreDaftars: the copy here is the one of the daftar tree DAFTAR names, byte for byte, so a case
// daftar adds or changes is not missed here. The vectors came with daftar #162 (after v2.4.0): a tree from before them
// is refused by name.
func TestFrontMatterVectorsAreDaftars(t *testing.T) {
	tree := os.Getenv("DAFTAR")
	if tree == "" {
		t.Skip("DAFTAR names no daftar tree to hold the copy of its vectors to")
	}
	theirs, err := os.ReadFile(filepath.Join(tree, "test", "vectors", "front-matter.json"))
	if os.IsNotExist(err) {
		t.Fatalf("%s holds no test/vectors/front-matter.json: name a daftar tree from #162 on, where the vectors are", tree)
	} else if err != nil {
		t.Fatalf("the daftar tree %s: %v", tree, err)
	}
	ours, err := os.ReadFile(frontMatterVectors)
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(ours, theirs) {
		t.Fatalf("%s is not the copy of %s's test/vectors/front-matter.json: copy it again", frontMatterVectors, tree)
	}
}
