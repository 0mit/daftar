#!/usr/bin/env python3
"""dmsafe — edit a front-matter document without silently destroying it.

WHY THIS EXISTS. Beans, VOCAB.md and std-vocab.md are STRUCTURED documents edited with TEXT surgery,
because their comments and layout carry meaning that a YAML round-trip would flatten. Text surgery is
blind to structure, and in one session it drew blood five times:

  1. an insert placed between a key and its indented block  -> invalid YAML, 9 documents broken at once
  2. a stop-pattern that ran too far                        -> VALID yaml, four blocks silently lost
  3. cuts ordered against anchors already removed           -> the script raised (self-caught)
  4. open(f,'w').write(open(f).read())                      -> the file truncated before the read
  5. a blind replace matching at the wrong indent depth     -> invalid YAML across a whole vocabulary

Every one was caught eventually by the gate or the tests, and NONE reached history — but "eventually"
means after other edits had piled on top, and after the damage had to be diagnosed rather than merely
seen. This closes the window: an edit that breaks a document, empties it, or loses content you did not
say you were removing is ROLLED BACK at write time, with the loss named.

The check that matters most is the second one. A broken document announces itself; a document that still
parses while quietly missing four blocks does not. So dmsafe compares LEAF PATHS before and after, and
any path that disappears must be declared in `allow_remove`. Removing is fine — removing by accident
is not, and the difference is whether you said so.

Library — PREFER the structure-aware operations; they make the incident shapes unexpressible rather
than merely caught, because they address a document by KEY instead of by offset, pattern or indent:
    dmsafe.insert_after(path, 'owned_by', block)      # lands after the WHOLE block, never inside it
    dmsafe.replace_block(path, 'code_paths', block)
    dmsafe.remove_block(path, 'tags')                 # the removal is declared by calling this
Fall back to the general form only when no operation fits:
    dmsafe.edit(path, lambda text: text.replace(...), allow_remove=['owns.stale_key'])

CLI — the same operations for a person at a shell; a block is read from standard input:
    python3 bin/dmsafe.py count <path> <dotted>                       # measure first: how many places
    python3 bin/dmsafe.py insert-after  <path> <key>   < block.yaml
    python3 bin/dmsafe.py replace-block <path> <key>   < block.yaml
    python3 bin/dmsafe.py remove-block  <path> <key>
    python3 bin/dmsafe.py set-nested    <path> <dotted> --expect N   < block.yaml
    python3 bin/dmsafe.py flow-set      <path> <dotted> <value> --expect N
    python3 bin/dmsafe.py verify [path ...]                           # parse-check (default: the whole garden)
Each write prints what it removed and what it added, as leaf paths; a refused edit says why and changes nothing.
"""
import glob, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


_MUST_STATE = object()   # a sentinel, so a missing `expect` teaches instead of raising a TypeError


class UnsafeEdit(Exception):
    """Raised when an edit would break a document or lose undeclared content. The write is rolled back."""


def parse(text):
    """(front-matter, body) or raise. A document that does not parse is not a document."""
    head, body = dmparse.split_front_matter(text)
    if head is None:
        raise UnsafeEdit("no front-matter fences — the document is empty or its fences were destroyed")
    fm = dmparse.loads(head)
    if not isinstance(fm, dict):
        raise UnsafeEdit(f"front-matter is not a mapping (got {type(fm).__name__})")
    return fm, body


def leaf_paths(node, prefix=''):
    """Every path to a leaf. Comparing these is what catches a document that still parses but has
    quietly lost content — the failure mode a syntax check cannot see."""
    out = set()
    if isinstance(node, dict):
        for k, v in node.items():
            out |= leaf_paths(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out |= leaf_paths(v, f"{prefix}[{i}]")
    else:
        out.add(prefix)
    return out


# ---- STRUCTURE-AWARE OPERATIONS -----------------------------------------------------------------
# `edit()` above CATCHES a bad edit. These PREVENT the five shapes that caused every incident, because
# they address a document by KEY rather than by offset, pattern or indent depth:
#   an insert lands after a key's WHOLE BLOCK, never between the key and its children (incident 1)
#   a span is computed from the structure, so it cannot run too far (incident 2)
#   operations are named, so they cannot be ordered against a landmark already removed (incident 3)
#   dmsafe owns the write, so a truncating open() is not reachable (incident 4)
#   nothing matches on leading whitespace, so indent depth cannot be confused (incident 5)

def top_level_span(text, key):
    """(start, end) of a top-level `key:` INCLUDING its indented block, within the front matter.

    The end is the crucial part and the part I got wrong: a key's block runs to the next line that
    starts a new top-level key OR a column-0 comment introducing one — not to the next blank line, and
    not to the first line that merely looks like a boundary."""
    fences = [i for i, l in enumerate(text.splitlines(keepends=True)) if l.rstrip('\r\n') == '---']
    lines = text.splitlines(keepends=True)
    if len(fences) < 2:
        raise UnsafeEdit("cannot locate front-matter fences")
    lo, hi = fences[0] + 1, fences[1]
    found = [i for i in range(lo, hi) if re.match(rf'^{re.escape(key)}:', lines[i])]
    if not found:
        raise UnsafeEdit(f"no top-level key '{key}' in the front matter")
    if len(found) > 1:
        raise UnsafeEdit(f"top-level key '{key}' appears {len(found)} times (lines "
                         f"{[i + 1 for i in found]}) — refusing to guess which you meant")
    start = found[0]
    end = hi
    for i in range(start + 1, hi):
        if re.match(r'^[A-Za-z_][\w-]*:', lines[i]) or lines[i].startswith('#'):
            end = i
            break
    while end > start + 1 and not lines[end - 1].strip():
        end -= 1                                   # do not swallow the blank line before the next key
    return sum(len(l) for l in lines[:start]), sum(len(l) for l in lines[:end])


def nested_spans(text, dotted):
    """Every (start, end) span for a NESTED key addressed by PATH — `a.b`, or `a[].b` to reach into each
    item of a list. Ancestry is what anchors the match, NOT an indentation string.

    Incident 5 was a nested edit: a replace meant for ONE `poles:` matched FOUR, because the pattern was
    anchored to leading whitespace rather than to a parent. Addressing by path removes that class, and
    RETURNING ALL SPANS lets the caller say how many it expected — which is the actual safeguard, since
    the bug was not the depth but matching more places than intended and nothing saying so."""
    lines = text.splitlines(keepends=True)
    fences = [i for i, l in enumerate(lines) if l.rstrip('\r\n') == '---']
    if len(fences) < 2:
        raise UnsafeEdit("cannot locate front-matter fences")

    def indent_of(i):
        return len(lines[i]) - len(lines[i].lstrip(' '))

    def block_end(i, ind):
        j = i + 1
        while j < fences[1] and (not lines[j].strip() or indent_of(j) > ind):
            j += 1
        while j > i + 1 and not lines[j - 1].strip():
            j -= 1
        return j

    def descend(lo, hi, ind, segs):
        seg, rest = segs[0], segs[1:]
        listy = seg.endswith('[]')
        name = seg[:-2] if listy else seg
        out = []
        i = lo
        while i < hi:
            if lines[i].strip() and indent_of(i) == ind and re.match(rf'^ {{{ind}}}{re.escape(name)}:', lines[i]):
                end = block_end(i, ind)
                if not rest and not listy:
                    out.append((i, end))
                elif listy:
                    # list items sit one level in, each `- ` starting an item whose keys align after it
                    j = i + 1
                    while j < end:
                        if re.match(rf'^ *- ', lines[j]):
                            item_ind = indent_of(j) + 2
                            k = block_end(j, indent_of(j))
                            if rest:
                                out += descend(j, k, item_ind, rest) if not re.match(
                                    rf'^ *- .*{re.escape(rest[0])}:', lines[j]) else _inline(j, rest)
                            else:
                                out.append((j, k))
                            j = k
                        else:
                            j += 1
                else:
                    out += descend(i + 1, end, ind + 2, rest)
                i = end
            else:
                i += 1
        return out

    def _inline(j, rest):
        raise UnsafeEdit(
            f"'{dotted}' is inside a FLOW mapping on line {j + 1} — a line-addressed operation cannot "
            f"reach into `{{a: 1, b: 2}}`. Edit that line as a whole, or convert it to block form.")

    spans = descend(fences[0] + 1, fences[1], 0, dotted.split('.'))
    return [(sum(len(l) for l in lines[:a]), sum(len(l) for l in lines[:b])) for a, b in spans]


def _require_expect(expect, dotted):
    if expect is _MUST_STATE:
        raise UnsafeEdit(
            f"state expect=N for '{dotted}'. The COUNT is the safeguard, not the addressing: across six "
            f"incidents the cause was never where an edit landed but that it landed in more places than "
            f"intended. Measure first — dmsafe.count(path, '{dotted}') — then say the number.")
    if not isinstance(expect, int) or expect < 1:
        raise UnsafeEdit(f"expect must be a positive integer, got {expect!r}")


def count(path, dotted):
    """How many locations `dotted` addresses, so you can MEASURE before you act. Returns (n, kind)."""
    text = open(path, encoding='utf-8').read()
    try:
        n = len(nested_spans(text, dotted))
        if n:
            return n, 'block'
    except UnsafeEdit:
        pass
    try:
        n = len(flow_spans(text, dotted))
        return (n, 'flow') if n else (0, 'none')
    except UnsafeEdit:
        return 0, 'none'


def _flow_pairs(text, lo, hi):
    """[(key, key_span, value_span)] for a flow mapping `{...}` spanning text[lo:hi].

    Scans with quote and nesting awareness rather than splitting on commas, because a value may itself
    contain a comma, a brace or a quoted comma — all three occur in this garden's anchors."""
    inner_lo, inner_hi = lo + 1, hi - 1
    parts, depth, q, seg = [], 0, None, inner_lo
    i = inner_lo
    while i < inner_hi:
        c = text[i]
        if q:
            if c == q:
                # escaped only by an ODD run of backslashes, and only in double quotes: `"C:\\"` ends a Windows path,
                # and a single-quoted scalar has no backslash escape at all
                n = 0
                while q == '"' and text[i - 1 - n] == '\\':
                    n += 1
                if n % 2 == 0:
                    q = None
        elif c in '"\'':
            q = c
        elif c in '{[':
            depth += 1
        elif c in '}]':
            depth -= 1
        elif c == ',' and depth == 0:
            parts.append((seg, i)); seg = i + 1
        i += 1
    parts.append((seg, inner_hi))
    out = []
    for a, b in parts:
        chunk = text[a:b]
        m = re.match(r'^(\s*)([\w.-]+)(\s*:\s*)', chunk)
        if not m:
            continue
        ks = a + len(m.group(1))
        vs = a + m.end()
        ve = b
        while ve > vs and text[ve - 1] in ' \t':
            ve -= 1                       # the value ends at its last byte, not at the space before `}`
        out.append((m.group(2), (ks, ks + len(m.group(2))), (vs, ve)))
    return out


def flow_spans(text, dotted):
    """Locate a key INSIDE one-line flow mappings, addressed as `a.b[].k` or `a.b[sel=val].k`.

    Line-addressed operations cannot reach into `{ a: 1, b: 2 }`, and most anchors in this garden are
    exactly that. This reaches them by scanning the flow mapping itself, and returns the VALUE span of
    each match so an edit replaces only the value and leaves every other byte — quoting, spacing,
    key order, trailing comment — untouched."""
    segs = dotted.split('.')
    leaf = segs[-1]
    container = '.'.join(segs[:-1])
    sel = None
    m = re.match(r'^(.*)\[([\w.-]+)=([^\]]+)\]$', container)
    if m:
        container, sel = m.group(1) + '[]', (m.group(2), m.group(3))
    lines = text.splitlines(keepends=True)
    offs, acc = [], 0
    for l in lines:
        offs.append(acc); acc += len(l)
    hits = []
    for a, b in nested_spans(text, container) if not container.endswith('[]') else _item_lines(text, container):
        chunk = text[a:b]
        for lm in re.finditer(r'\{', chunk):
            start = a + lm.start()
            depth, j, q = 0, start, None
            while j < b:
                c = text[j]
                if q:
                    if c == q and text[j - 1] != '\\':
                        q = None
                elif c in '"\'':
                    q = c
                elif c == '{':
                    depth += 1
                elif c == '}':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            pairs = _flow_pairs(text, start, j + 1)
            if sel:
                got = dict((k, text[v[0]:v[1]].strip().strip('"\'')) for k, _ks, v in pairs)
                if got.get(sel[0]) != sel[1]:
                    break
            for k, _ks, vspan in pairs:
                if k == leaf:
                    hits.append(vspan)
            break
    return hits


def _item_lines(text, container):
    """Spans of each `- ` item under a container path ending in `[]`."""
    base = container[:-2]
    lines = text.splitlines(keepends=True)
    out = []
    for a, b in nested_spans(text, base):
        seg = text[a:b]
        off = a
        for ln in seg.splitlines(keepends=True):
            if re.match(r'^\s*- ', ln):
                out.append((off, off + len(ln)))
            off += len(ln)
    return out


def flow_set(path, dotted, value, expect=_MUST_STATE, **kw):
    """Set a key's value inside flow mappings, replacing ONLY the value bytes."""
    _require_expect(expect, dotted)

    def t(text):
        spans = flow_spans(text, dotted)
        if len(spans) != expect:
            raise UnsafeEdit(f"'{dotted}' matched {len(spans)} flow location(s), expected {expect}")
        out, prev = [], 0
        for s_, e_ in spans:
            out.append(text[prev:s_]); out.append(str(value)); prev = e_
        out.append(text[prev:])
        return ''.join(out)
    return edit(path, t, **kw)


def flow_insert(path, dotted, key, value, after=None, expect=_MUST_STATE, **kw):
    """Add a key to flow mappings, optionally right AFTER a named key — the P4 anchor migration's shape."""
    _require_expect(expect, f"{dotted}.{after or key}")

    def t(text):
        anchor_key = after or key
        spans = flow_spans(text, f"{dotted}.{anchor_key}")
        if len(spans) != expect:
            raise UnsafeEdit(f"'{dotted}.{anchor_key}' matched {len(spans)} flow location(s), "
                             f"expected {expect}")
        out, prev = [], 0
        for s_, e_ in spans:
            out.append(text[prev:e_]); out.append(f", {key}: {value}"); prev = e_
        out.append(text[prev:])
        return ''.join(out)
    return edit(path, t, **kw)


def set_nested(path, dotted, block, expect=_MUST_STATE, **kw):
    """Replace every span of a nested key — refusing unless EXACTLY `expect` locations match. Stating the
    count is the safeguard: incident 5 intended one location and silently changed four."""
    _require_expect(expect, dotted)

    def t(text):
        spans = nested_spans(text, dotted)
        if len(spans) != expect:
            raise UnsafeEdit(f"'{dotted}' matched {len(spans)} location(s), expected {expect} — "
                             f"say which you mean before changing any of them")
        out, prev = [], 0
        for s_, e_ in spans:
            out.append(text[prev:s_]); out.append(block if block.endswith('\n') else block + '\n')
            prev = e_
        out.append(text[prev:])
        return ''.join(out)
    return edit(path, t, **kw)


def insert_after(path, key, block, **kw):
    """Insert `block` after the COMPLETE block of a top-level key. This is incident 1 made unexpressible."""
    def t(text):
        _s, e = top_level_span(text, key)
        return text[:e] + (block if block.endswith('\n') else block + '\n') + text[e:]
    return edit(path, t, **kw)


def replace_block(path, key, block, **kw):
    """Replace a top-level key's whole block. The span comes from the structure, not from a stop-pattern."""
    def t(text):
        s_, e = top_level_span(text, key)
        return text[:s_] + (block if block.endswith('\n') else block + '\n') + text[e:]
    return edit(path, t, **kw)


def remove_block(path, key, **kw):
    """Remove a top-level key and its block. The removal is declared by CALLING this, not by a flag."""
    def t(text):
        s_, e = top_level_span(text, key)
        return text[:s_] + text[e:]
    kw.setdefault('allow_remove', ())
    kw['allow_remove'] = tuple(kw['allow_remove']) + (key,)
    return edit(path, t, **kw)


def edit(path, transform, allow_remove=(), allow_empty_body=False):
    """Apply `transform` to the file's text, keeping the write ONLY if the result is a document that
    parses and has lost nothing undeclared. Returns (removed, added) leaf paths on success."""
    original = open(path, encoding='utf-8').read()
    try:
        before_fm, _ = parse(original)
    except UnsafeEdit as e:
        raise UnsafeEdit(f"{path}: REFUSING to edit — it is already broken: {e}")

    new_text = transform(original)
    if new_text == original:
        raise UnsafeEdit(f"{path}: the edit changed nothing — a pattern that matched nothing is a bug, "
                         f"not a no-op (this is how a 'fixed' file silently stays unfixed)")

    open(path, 'w', encoding='utf-8').write(new_text)
    try:
        after_fm, after_body = parse(new_text)
        if not allow_empty_body and not after_body.strip():
            raise UnsafeEdit("the human body was emptied (Rule 6: a bean reads on paper)")
        before, after = leaf_paths(before_fm), leaf_paths(after_fm)
        lost = {p for p in before - after
                if not any(p == a or p.startswith(a + '.') or p.startswith(a + '[')
                           for a in allow_remove)}
        if lost:
            raise UnsafeEdit(
                f"the edit would LOSE {len(lost)} leaf path(s) you did not declare: "
                f"{sorted(lost)[:6]}{' …' if len(lost) > 6 else ''} — pass them in allow_remove if the "
                f"removal is intended")
        return sorted(before - after), sorted(after - before)
    except Exception as e:
        open(path, 'w', encoding='utf-8').write(original)          # roll back, always
        raise UnsafeEdit(f"{path}: ROLLED BACK — {e}") from None


def verify(paths):
    """Parse-check documents. Returns a list of (path, problem)."""
    bad = []
    for p in paths:
        try:
            parse(open(p, encoding='utf-8').read())
        except Exception as e:
            bad.append((p, str(e)))
    return bad


def _cli(argv):
    """The operations at a shell. Returns an exit status."""
    if not argv:
        return None                       # no arguments: parse-check the garden, as it always did
    if argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    op, rest = argv[0], argv[1:]
    expect = _MUST_STATE
    if '--expect' in rest:
        i = rest.index('--expect'); expect = int(rest[i + 1]); del rest[i:i + 2]
    def _block():
        b = sys.stdin.read()
        if not b.strip():
            sys.exit("dmsafe: the block comes on standard input, and it is empty")
        return b
    def _report(result):
        removed, added = result
        print(f"dmsafe: removed {removed or 'nothing'}; added {added or 'nothing'}")
        return 0
    try:
        if op == 'count' and len(rest) == 2:
            n, kind = count(rest[0], rest[1]); print(f"{n} {kind}"); return 0
        if op == 'insert-after' and len(rest) == 2:
            return _report(insert_after(rest[0], rest[1], _block()))
        if op == 'replace-block' and len(rest) == 2:
            return _report(replace_block(rest[0], rest[1], _block()))
        if op == 'remove-block' and len(rest) == 2:
            return _report(remove_block(rest[0], rest[1]))
        if op == 'set-nested' and len(rest) == 2:
            return _report(set_nested(rest[0], rest[1], _block(), expect=expect))
        if op == 'flow-set' and len(rest) == 3:
            return _report(flow_set(rest[0], rest[1], rest[2], expect=expect))
    except UnsafeEdit as e:
        print(f"dmsafe: REFUSED — {e}"); return 1
    if op not in ('verify', '--verify'):
        print(f"dmsafe: unknown operation or wrong arguments: {' '.join(argv)}\n"); print(__doc__); return 2
    return None


if __name__ == '__main__':
    _rc = _cli(sys.argv[1:])
    if _rc is not None:
        sys.exit(_rc)
    args = [a for a in sys.argv[1:] if not a.startswith('--') and a != 'verify']
    targets = args or (sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) +
                       sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))) +
                       [os.path.join(ROOT, f) for f in ('VOCAB.md', 'GARDEN.md')] +
                       [os.path.join(ROOT, 'seed', 'std-vocab.md')])
    targets = [t for t in targets if os.path.exists(t)]
    problems = verify(targets)
    for p, why in problems:
        print(f"BROKEN  {os.path.relpath(p, ROOT)}: {why}")
    print(f"\ndmsafe: {len(targets) - len(problems)}/{len(targets)} documents parse")
    sys.exit(1 if problems else 0)
