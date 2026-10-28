package garden

import (
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
)

// fence is a front matter's fence, as daftar's one splitter reads it (bin/parse.py FENCE): a line of three dashes.
var fence = regexp.MustCompile(`(?m)^---[ \t]*\r?$`)

// SplitFrontMatter is a fenced document's front matter and body, split as bin/parse.py split_front_matter splits it:
// the first line opens it (a byte-order mark before it is let go), the next fence line closes it; the front matter
// keeps the line break after the first fence, the body the one after the second. ok is false where it is not fenced.
func SplitFrontMatter(text string) (front, body string, ok bool) {
	text = strings.TrimPrefix(text, "\ufeff")
	m1 := fence.FindStringIndex(text)
	if m1 == nil || m1[0] != 0 {
		return "", text, false
	}
	m2 := fence.FindStringIndex(text[m1[1]:])
	if m2 == nil {
		return "", text, false
	}
	return text[m1[1] : m1[1]+m2[0]], text[m1[1]+m2[1]:], true
}

// Statement is one verb and its roles, as a bean writes it: `- <verb>: { <role>: …, … }`.
type Statement struct {
	Verb  string
	Roles *Map
}

// Bean is one document of a garden: its header (every key of its front matter), its statements, and its body.
type Bean struct {
	ID         string
	Kind       string
	Title      string
	Header     *Map
	Statements []Statement
	Body       string
}

// ReadBean reads a bean's file as the core reads it (core/read.py): its text as UTF-8 with its line ends made one, its
// front matter fenced and read with every scalar a string. A file the core would not read is an *Unread here too.
func ReadBean(path string) (*Bean, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	text := strings.ReplaceAll(strings.ReplaceAll(string(raw), "\r\n", "\n"), "\r", "\n")
	front, body, ok := SplitFrontMatter(text)
	if !ok {
		return nil, unread("%s has no front matter", path)
	}
	v, err := Load(front)
	if err != nil {
		return nil, err
	}
	m, isMap := v.(*Map)
	if v == nil {
		m, isMap = newMap(), true
	}
	if !isMap {
		return nil, unread("%s: its front matter is not a mapping of keys", path)
	}
	b := &Bean{Header: m, Body: body}
	b.ID, _ = m.Get("bean").(string)
	if b.ID == "" {
		b.ID = strings.TrimSuffix(filepath.Base(path), ".md")
	}
	b.Kind, _ = m.Get("kind").(string)
	b.Title, _ = m.Get("title").(string)
	if list, ok := m.Get("statements").([]any); ok {
		for _, x := range list {
			sm, ok := x.(*Map)
			if !ok || len(sm.Keys) != 1 {
				continue // not one verb: the core's gate says why (rule form)
			}
			roles, ok := sm.Vals[sm.Keys[0]].(*Map)
			if !ok {
				continue
			}
			b.Statements = append(b.Statements, Statement{Verb: sm.Keys[0], Roles: roles})
		}
	}
	return b, nil
}

// Beans are every bean and mapping of the garden at root, by id; and the files the core would not read, with why.
func Beans(root string) (map[string]*Bean, map[string]error) {
	out, bad := map[string]*Bean{}, map[string]error{}
	var files []string
	for _, dir := range []string{"beans", "mappings"} {
		got, _ := filepath.Glob(filepath.Join(root, dir, "*.md"))
		files = append(files, got...)
	}
	sort.Strings(files)
	for _, f := range files {
		b, err := ReadBean(f)
		if err != nil {
			bad[f] = err
			continue
		}
		out[b.ID] = b
	}
	return out, bad
}
