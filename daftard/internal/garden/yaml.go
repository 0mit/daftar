// Package garden reads a garden natively (design §5): a bean's front matter as the core reads it — YAML with every
// scalar a string (PyYAML's BaseLoader, core/read.py) — and its statements, each one verb and its roles. What it reads
// is held to the core's reader by a conformance test over real gardens (conformance_test.go): any bean the two read
// differently is a failure of this one.
package garden

import (
	"fmt"
	"strconv"
	"strings"
	"unicode/utf8"
)

// Unread is a document this reader will not read: YAML it does not parse, or a key written twice.
type Unread struct{ Why string }

func (u *Unread) Error() string { return u.Why }

func unread(format string, a ...any) error { return &Unread{fmt.Sprintf(format, a...)} }

// Map is a mapping in the order it was written.
type Map struct {
	Keys []string
	Vals map[string]any
}

// Get is the value under key, or nil.
func (m *Map) Get(key string) any {
	if m == nil {
		return nil
	}
	return m.Vals[key]
}

func newMap() *Map { return &Map{Vals: map[string]any{}} }

func (m *Map) put(key string, v any) error {
	if _, ok := m.Vals[key]; ok {
		return unread("`%s` is written twice, and YAML would keep only the last", key)
	}
	m.Keys = append(m.Keys, key)
	m.Vals[key] = v
	return nil
}

// Plain is a value as encoding/json writes it: a Map as an object, a sequence as an array, a scalar as a string.
func Plain(v any) any {
	switch x := v.(type) {
	case *Map:
		out := map[string]any{}
		for _, k := range x.Keys {
			out[k] = Plain(x.Vals[k])
		}
		return out
	case []any:
		out := make([]any, len(x))
		for i, e := range x {
			out[i] = Plain(e)
		}
		return out
	default:
		return v
	}
}

// ---------------------------------------------------------------------------------------------- lines

type line struct {
	n      int    // its number, from 1
	indent int    // the spaces before its content
	text   string // its content, the indent taken off
	raw    string
}

type parser struct {
	lines   []line
	i       int
	anchor  map[string]any
	aliases int // how many aliases the document has used: a few, never a billion laughs (security audit 2.8)
}

// maxAliases is how many aliases one document may use: they share their value, but whatever walks the tree after
// walks each one, so a document of nested aliases would grow without end when written out or compared.
const maxAliases = 64

// Load reads YAML text with every scalar a string: a *Map, a []any, a string, or nil for an empty document.
func Load(text string) (v any, err error) {
	defer func() {
		if r := recover(); r != nil {
			if u, ok := r.(*Unread); ok {
				v, err = nil, u
				return
			}
			panic(r)
		}
	}()
	p := &parser{anchor: map[string]any{}}
	for n, raw := range strings.Split(strings.ReplaceAll(text, "\r\n", "\n"), "\n") {
		if strings.ContainsRune(raw, '\t') && strings.TrimLeft(raw, " ") != raw && strings.HasPrefix(strings.TrimLeft(raw, " "), "\t") {
			panic(unread("line %d: a tab indents it, and YAML indents with spaces", n+1))
		}
		t := strings.TrimLeft(raw, " ")
		p.lines = append(p.lines, line{n: n + 1, indent: len(raw) - len(t), text: t, raw: raw})
	}
	p.skip()
	if p.i >= len(p.lines) {
		return nil, nil
	}
	if p.lines[p.i].text == "---" {
		p.i++
		p.skip()
	}
	if p.i >= len(p.lines) {
		return nil, nil
	}
	v = p.block(p.lines[p.i].indent, -1)
	p.skip()
	if p.i < len(p.lines) {
		if p.lines[p.i].text != "..." {
			panic(unread("line %d: %q is not where YAML expects it", p.lines[p.i].n, p.lines[p.i].text))
		}
	}
	return v, nil
}

func blank(t string) bool { return t == "" || strings.HasPrefix(t, "#") }

// skip passes blank and comment lines.
func (p *parser) skip() {
	for p.i < len(p.lines) && blank(p.lines[p.i].text) {
		p.i++
	}
}

// block reads the node that begins at the current line, at `indent`; `parent` is the indent of what holds it.
func (p *parser) block(indent, parent int) any {
	p.skip()
	if p.i >= len(p.lines) {
		return ""
	}
	l := p.lines[p.i]
	if isSeqItem(l.text) {
		return p.sequence(indent)
	}
	if _, _, ok := splitKey(l.text); ok {
		return p.mapping(indent)
	}
	if t := skipTag(l.text); strings.HasPrefix(t, "|") || strings.HasPrefix(t, ">") { // a list's item as a block scalar
		p.i++
		return p.blockScalar(t, parent)
	}
	// a node that is one scalar, or a flow collection, written at this indent
	v, rest := p.inline(l.text, indent, parent)
	if strings.TrimSpace(stripComment(rest)) != "" {
		panic(unread("line %d: %q follows a value", l.n, rest))
	}
	return v
}

func isSeqItem(t string) bool { return t == "-" || strings.HasPrefix(t, "- ") }

// stripComment is what stands before a comment: ` #` and what follows, outside quotes the caller has passed.
func stripComment(s string) string {
	if strings.HasPrefix(s, "#") {
		return ""
	}
	if i := strings.Index(s, " #"); i >= 0 {
		return s[:i]
	}
	return s
}

// ---------------------------------------------------------------------------------------------- block collections

func (p *parser) sequence(indent int) any {
	out := []any{}
	for {
		p.skip()
		if p.i >= len(p.lines) {
			return out
		}
		l := p.lines[p.i]
		if l.indent < indent || l.indent > indent || !isSeqItem(l.text) {
			if l.indent > indent {
				panic(unread("line %d: more indented than the list it is in", l.n))
			}
			return out
		}
		rest := strings.TrimPrefix(strings.TrimPrefix(l.text, "-"), " ")
		inner := indent + 1 + (len(l.text) - 1 - len(rest))
		if blank(strings.TrimSpace(rest)) || strings.HasPrefix(strings.TrimSpace(rest), "#") {
			p.i++
			p.skip()
			if p.i < len(p.lines) && p.lines[p.i].indent > indent {
				out = append(out, p.block(p.lines[p.i].indent, indent))
			} else {
				out = append(out, "")
			}
			continue
		}
		// the item's content as a line of its own, at its own column: `- say: {…}` is a mapping there
		p.lines[p.i] = line{n: l.n, indent: inner, text: rest, raw: l.raw}
		out = append(out, p.block(inner, indent))
	}
}

func (p *parser) mapping(indent int) any {
	m := newMap()
	for {
		p.skip()
		if p.i >= len(p.lines) {
			return m
		}
		l := p.lines[p.i]
		if l.indent < indent {
			return m
		}
		if l.indent > indent {
			panic(unread("line %d: more indented than the mapping it is in", l.n))
		}
		if isSeqItem(l.text) {
			return m
		}
		key, rest, ok := splitKey(l.text)
		if !ok {
			panic(unread("line %d: %q is no key of the mapping it is in", l.n, l.text))
		}
		v := p.value(rest, indent, l)
		if err := m.put(key, v); err != nil {
			panic(unread("line %d: %v", l.n, err))
		}
	}
}

// value reads what follows a key, `rest` on the key's own line, the key at `indent`.
func (p *parser) value(rest string, indent int, l line) any {
	r := strings.TrimLeft(rest, " ")
	anchor := ""
	if strings.HasPrefix(r, "&") {
		end := strings.IndexAny(r, " ")
		if end < 0 {
			end = len(r)
		}
		anchor, r = r[1:end], strings.TrimLeft(r[end:], " ")
	}
	r = skipTag(r)
	var v any
	switch {
	case blank(r):
		p.i++
		p.skip()
		switch {
		case p.i < len(p.lines) && p.lines[p.i].indent > indent:
			v = p.block(p.lines[p.i].indent, indent)
		case p.i < len(p.lines) && p.lines[p.i].indent == indent && isSeqItem(p.lines[p.i].text):
			v = p.sequence(indent) // `key:` and its list at the key's own indent
		default:
			v = ""
		}
	case strings.HasPrefix(r, "|") || strings.HasPrefix(r, ">"):
		p.i++
		v = p.blockScalar(r, indent)
	default:
		val, after := p.inline(r, indent, indent)
		if strings.TrimSpace(stripComment(after)) != "" {
			panic(unread("line %d: %q follows a value", l.n, after))
		}
		v = val
	}
	if anchor != "" {
		p.anchor[anchor] = v
	}
	return v
}

func skipTag(r string) string {
	if strings.HasPrefix(r, "!") {
		end := strings.IndexAny(r, " ")
		if end < 0 {
			return ""
		}
		return strings.TrimLeft(r[end:], " ")
	}
	return r
}

// splitKey is a block mapping's key and what follows its `:`.
func splitKey(t string) (string, string, bool) {
	if t == "" || t[0] == '#' || t[0] == '-' && (len(t) == 1 || t[1] == ' ') || t[0] == '{' || t[0] == '[' {
		return "", "", false
	}
	if t[0] == '"' || t[0] == '\'' {
		s, n, ok := quotedOneLine(t)
		if !ok {
			return "", "", false
		}
		rest := t[n:]
		if strings.HasPrefix(rest, ":") && (len(rest) == 1 || rest[1] == ' ') {
			return s, rest[1:], true
		}
		return "", "", false
	}
	for i := 0; i < len(t); i++ {
		if t[i] == ':' && (i+1 == len(t) || t[i+1] == ' ') {
			key := strings.TrimRight(t[:i], " ")
			if strings.Contains(key, " #") {
				return "", "", false
			}
			return key, t[i+1:], true
		}
		if t[i] == ' ' && i+1 < len(t) && t[i+1] == '#' {
			return "", "", false
		}
	}
	return "", "", false
}

func quotedOneLine(t string) (string, int, bool) {
	q := t[0]
	var b strings.Builder
	for i := 1; i < len(t); i++ {
		c := t[i]
		if q == '\'' && c == '\'' {
			if i+1 < len(t) && t[i+1] == '\'' {
				b.WriteByte('\'')
				i++
				continue
			}
			return b.String(), i + 1, true
		}
		if q == '"' && c == '\\' && i+1 < len(t) {
			s, n := escape(t, i)
			b.WriteString(s)
			i += n - 1
			continue
		}
		if q == '"' && c == '"' {
			return b.String(), i + 1, true
		}
		b.WriteByte(c)
	}
	return "", 0, false
}

// ---------------------------------------------------------------------------------------------- block scalars

func (p *parser) blockScalar(head string, indent int) string {
	style := head[0]
	chomp, explicit := byte(0), 0
	for _, c := range []byte(strings.TrimSpace(stripComment(head[1:]))) {
		switch {
		case c == '-' || c == '+':
			chomp = c
		case c >= '1' && c <= '9':
			explicit = int(c - '0')
		}
	}
	// the lines it holds: those more indented than its key, and the blank ones among them
	start := p.i
	content := -1
	if explicit > 0 {
		content = indent + explicit
	}
	end := start
	for end < len(p.lines) {
		l := p.lines[end]
		if strings.TrimSpace(l.raw) == "" {
			end++
			continue
		}
		if content < 0 {
			if l.indent <= indent {
				break
			}
			content = l.indent
		}
		if l.indent < content {
			break
		}
		end++
	}
	// trailing blank lines belong to it for chomping, not to what follows
	last := end
	for last > start && strings.TrimSpace(p.lines[last-1].raw) == "" {
		last--
	}
	p.i = end
	if content < 0 {
		content = indent + 1
	}
	var body []string
	for _, l := range p.lines[start:last] {
		if len(l.raw) >= content {
			body = append(body, l.raw[content:])
		} else {
			body = append(body, "")
		}
	}
	trailing := end - last
	var text string
	if style == '|' {
		text = strings.Join(body, "\n")
	} else {
		text = fold(body)
	}
	switch chomp {
	case '-':
		return text
	case '+':
		if len(body) == 0 {
			return strings.Repeat("\n", trailing)
		}
		return text + "\n" + strings.Repeat("\n", trailing)
	default:
		if len(body) == 0 {
			return ""
		}
		return text + "\n"
	}
}

// fold joins a folded block's lines: a break between two lines of text is a space, and blank lines between them are
// the breaks instead; a more-indented line keeps its breaks, and so do the blank lines beside it.
func fold(lines []string) string {
	more := func(s string) bool { return strings.HasPrefix(s, " ") || strings.HasPrefix(s, "\t") }
	var b strings.Builder
	for i, s := range lines {
		switch {
		case i == 0:
		case s == "":
			b.WriteByte('\n')
			continue
		case lines[i-1] == "":
			j := i - 1
			for j >= 0 && lines[j] == "" {
				j--
			}
			if j >= 0 && (more(lines[j]) || more(s)) {
				b.WriteByte('\n')
			}
		case more(lines[i-1]) || more(s):
			b.WriteByte('\n')
		default:
			b.WriteByte(' ')
		}
		b.WriteString(s)
	}
	return b.String()
}

// ---------------------------------------------------------------------------------------------- inline nodes

// inline reads a scalar or a flow collection that begins in `t` on the current line and may run on to later lines
// more indented than `parent`; it returns the value and what stands after it on the line it ends on, and leaves the
// parser on the line after.
func (p *parser) inline(t string, indent, parent int) (any, string) {
	sc := &scanner{p: p, parent: parent}
	sc.load(t)
	v := sc.node(false)
	rest := sc.restOfLine()
	p.i = sc.line + 1
	return v, rest
}

type scanner struct {
	p      *parser
	parent int
	line   int    // the line the scanner is on
	s      string // the text of that line from where it stands
	depth  int    // inside how many flow collections
}

func (sc *scanner) load(t string) {
	sc.line = sc.p.i
	sc.s = t
}

func (sc *scanner) restOfLine() string { return sc.s }

// next moves to the next line that continues this node: more indented than its parent, or any line inside a flow
// collection; false where none does.
func (sc *scanner) next() bool {
	for j := sc.line + 1; j < len(sc.p.lines); j++ {
		l := sc.p.lines[j]
		if strings.TrimSpace(l.raw) == "" {
			continue
		}
		if sc.depth == 0 && l.indent <= sc.parent {
			return false
		}
		sc.line, sc.s = j, l.text
		return true
	}
	return false
}

func (sc *scanner) spaces() {
	for {
		sc.s = strings.TrimLeft(sc.s, " ")
		if sc.s == "" || strings.HasPrefix(sc.s, "#") {
			if sc.depth > 0 {
				if !sc.next() {
					panic(unread("line %d: a flow collection that never closes", sc.p.lines[sc.line].n))
				}
				continue
			}
			sc.s = ""
		}
		return
	}
}

func (sc *scanner) node(key bool) any {
	sc.spaces()
	if sc.s == "" {
		return ""
	}
	anchor := ""
	if sc.s[0] == '&' {
		end := strings.IndexAny(sc.s, " ,]}")
		if end < 0 {
			end = len(sc.s)
		}
		anchor, sc.s = sc.s[1:end], sc.s[end:]
		sc.spaces()
	}
	if sc.s != "" && sc.s[0] == '!' {
		end := strings.IndexAny(sc.s, " ,]}")
		if end < 0 {
			end = len(sc.s)
		}
		sc.s = sc.s[end:]
		sc.spaces()
	}
	var v any
	switch {
	case sc.s == "":
		v = ""
	case sc.s[0] == '*':
		end := strings.IndexAny(sc.s, " ,]}")
		if end < 0 {
			end = len(sc.s)
		}
		name := sc.s[1:end]
		sc.s = sc.s[end:]
		got, ok := sc.p.anchor[name]
		if !ok {
			panic(unread("line %d: the alias *%s names no anchor", sc.p.lines[sc.line].n, name))
		}
		if sc.p.aliases++; sc.p.aliases > maxAliases {
			panic(unread("line %d: more than %d aliases in one document", sc.p.lines[sc.line].n, maxAliases))
		}
		return got
	case sc.s[0] == '{':
		v = sc.flowMap()
	case sc.s[0] == '[':
		v = sc.flowSeq()
	case sc.s[0] == '"' || sc.s[0] == '\'':
		v = sc.quoted()
	default:
		v = sc.plain(key)
	}
	if anchor != "" {
		sc.p.anchor[anchor] = v
	}
	return v
}

func (sc *scanner) flowMap() any {
	sc.s = sc.s[1:]
	sc.depth++
	m := newMap()
	for {
		sc.spaces()
		if strings.HasPrefix(sc.s, "}") {
			sc.s = sc.s[1:]
			sc.depth--
			return m
		}
		k := sc.node(true)
		key, ok := k.(string)
		if !ok {
			panic(unread("line %d: a key that is a collection", sc.p.lines[sc.line].n))
		}
		sc.spaces()
		var v any = ""
		if strings.HasPrefix(sc.s, ":") {
			sc.s = sc.s[1:]
			sc.spaces()
			if !strings.HasPrefix(sc.s, ",") && !strings.HasPrefix(sc.s, "}") {
				v = sc.node(false)
			}
		}
		if err := m.put(key, v); err != nil {
			panic(unread("line %d: %v", sc.p.lines[sc.line].n, err))
		}
		sc.spaces()
		switch {
		case strings.HasPrefix(sc.s, ","):
			sc.s = sc.s[1:]
		case strings.HasPrefix(sc.s, "}"):
		default:
			panic(unread("line %d: a flow mapping goes on with %q", sc.p.lines[sc.line].n, sc.s))
		}
	}
}

func (sc *scanner) flowSeq() any {
	sc.s = sc.s[1:]
	sc.depth++
	out := []any{}
	for {
		sc.spaces()
		if strings.HasPrefix(sc.s, "]") {
			sc.s = sc.s[1:]
			sc.depth--
			return out
		}
		v := sc.node(false)
		sc.spaces()
		if strings.HasPrefix(sc.s, ":") { // a single-pair mapping in a sequence: [a: b]
			sc.s = sc.s[1:]
			m := newMap()
			key, _ := v.(string)
			_ = m.put(key, sc.node(false))
			v = m
			sc.spaces()
		}
		out = append(out, v)
		switch {
		case strings.HasPrefix(sc.s, ","):
			sc.s = sc.s[1:]
		case strings.HasPrefix(sc.s, "]"):
		default:
			panic(unread("line %d: a flow sequence goes on with %q", sc.p.lines[sc.line].n, sc.s))
		}
	}
}

// plain reads a plain scalar: in a flow collection it ends at , [ ] { } ? and at `: `; anywhere at ` #` and at `: `;
// lines it runs on to fold into spaces, a blank line into a break.
func (sc *scanner) plain(key bool) string {
	var parts []string
	blanks := 0
	for {
		end := len(sc.s)
		for i := 0; i < len(sc.s); i++ {
			c := sc.s[i]
			if c == ':' && (i+1 == len(sc.s) || sc.s[i+1] == ' ' || sc.depth > 0 && strings.IndexByte(",[]{}", sc.s[i+1]) >= 0) {
				end = i
				break
			}
			if c == '#' && i > 0 && sc.s[i-1] == ' ' {
				end = i
				break
			}
			if sc.depth > 0 && strings.IndexByte(",[]{}?", c) >= 0 && !(c == '?' && i+1 < len(sc.s) && sc.s[i+1] != ' ') {
				end = i
				break
			}
		}
		word := strings.TrimRight(sc.s[:end], " ")
		if len(parts) > 0 {
			if blanks > 0 {
				parts = append(parts, strings.Repeat("\n", blanks))
			} else {
				parts = append(parts, " ")
			}
		}
		parts = append(parts, word)
		sc.s = sc.s[end:]
		if sc.s != "" || key {
			break
		}
		// on to the next line, where the scalar goes on if that line is no key, no item, and indented enough
		j, b := sc.line+1, 0
		for j < len(sc.p.lines) && strings.TrimSpace(sc.p.lines[j].raw) == "" {
			j++
			b++
		}
		if j >= len(sc.p.lines) {
			break
		}
		l := sc.p.lines[j]
		if (sc.depth == 0 && l.indent <= sc.parent) || blank(l.text) {
			break // a line more indented than the scalar's parent goes on with it, a leading `- ` and all
		}
		if _, _, ok := splitKey(l.text); ok && sc.depth == 0 {
			break
		}
		if sc.depth > 0 && strings.IndexByte(",]}", l.text[0]) >= 0 {
			sc.line, sc.s = j, l.text
			break
		}
		sc.line, sc.s, blanks = j, l.text, b
	}
	return strings.Join(parts, "")
}

// quoted reads a single- or double-quoted scalar, which may run on to later lines (folded as YAML folds them).
func (sc *scanner) quoted() string {
	q := sc.s[0]
	sc.s = sc.s[1:]
	var b strings.Builder
	for {
		i := 0
		for i < len(sc.s) {
			c := sc.s[i]
			if q == '\'' && c == '\'' {
				if i+1 < len(sc.s) && sc.s[i+1] == '\'' {
					b.WriteByte('\'')
					i += 2
					continue
				}
				sc.s = sc.s[i+1:]
				return b.String()
			}
			if q == '"' && c == '"' {
				sc.s = sc.s[i+1:]
				return b.String()
			}
			if q == '"' && c == '\\' {
				if i+1 == len(sc.s) { // an escaped line break: the next line goes on with no space
					if !sc.nextQuotedLine(&b, true) {
						panic(unread("line %d: a quoted value that never closes", sc.p.lines[sc.line].n))
					}
					i = 0
					continue
				}
				s, n := escape(sc.s, i)
				b.WriteString(s)
				i += n
				continue
			}
			b.WriteByte(c)
			i++
		}
		// the line ends inside the quotes: its trailing spaces go, and the break folds
		trimmed := strings.TrimRight(b.String(), " \t")
		b.Reset()
		b.WriteString(trimmed)
		if !sc.nextQuotedLine(&b, false) {
			panic(unread("line %d: a quoted value that never closes", sc.p.lines[sc.line].n))
		}
	}
}

// nextQuotedLine moves a quoted scalar on to its next line: a break is a space, each blank line a newline; an escaped
// break joins with nothing.
func (sc *scanner) nextQuotedLine(b *strings.Builder, escaped bool) bool {
	blanks := 0
	for j := sc.line + 1; j < len(sc.p.lines); j++ {
		l := sc.p.lines[j]
		if strings.TrimSpace(l.raw) == "" {
			blanks++
			continue
		}
		switch {
		case escaped && blanks == 0:
		case blanks > 0:
			b.WriteString(strings.Repeat("\n", blanks))
		default:
			b.WriteByte(' ')
		}
		sc.line, sc.s = j, strings.TrimLeft(l.raw, " \t")
		return true
	}
	return false
}

// escape is one escape of a double-quoted scalar at s[i] (a backslash): what it stands for, and how long it is.
func escape(s string, i int) (string, int) {
	if i+1 >= len(s) {
		return "\\", 1
	}
	simple := map[byte]string{'0': "\x00", 'a': "\a", 'b': "\b", 't': "\t", '\t': "\t", 'n': "\n", 'v': "\v",
		'f': "\f", 'r': "\r", 'e': "\x1b", ' ': " ", '"': "\"", '/': "/", '\\': "\\", 'N': "\u0085", '_': "\u00a0",
		'L': "\u2028", 'P': "\u2029"}
	c := s[i+1]
	if r, ok := simple[c]; ok {
		return r, 2
	}
	width := map[byte]int{'x': 2, 'u': 4, 'U': 8}[c]
	if width > 0 && i+2+width <= len(s) {
		if n, err := strconv.ParseUint(s[i+2:i+2+width], 16, 32); err == nil && utf8.ValidRune(rune(n)) {
			return string(rune(n)), 2 + width
		}
	}
	panic(unread("an escape %q that YAML does not have", s[i:min(len(s), i+2)]))
}
