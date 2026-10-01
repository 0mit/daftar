#!/usr/bin/env python3
"""merge — the statement merge (core/guide/MERGE.md): two branches of one garden merge a bean by its statements.

    python3 core/merge.py --file <base> <ours> <theirs>    # git's merge driver (%O %A %B): ours is written in place
    python3 core/merge.py <base> <ours> <theirs>           # the merged bean printed, or each true conflict (exit 1)

(`python` on Windows.) git runs it through bin/merge.py, which `.gitattributes` names for `beans/*.md` and
`mappings/*.md` and bin/install.py configures; bin/merge.py sends a bean in today's words to bin/dmmerge.py.

A bean's statements are a set, merged three ways: one either side removed since the base is removed, one either side
added is kept, one both added is kept once, and two that disagree both stand, each with the act that knows it. Its
header merges key by key, `tags` as a set, `details` leaf by leaf, and its body line by line (`git merge-file`). A knowing
act one side added with no `of` is given one, the ids it covered on its own side, where the other side added what it
would otherwise cover too. A true conflict — a place both sides changed differently, an `id` that would name two
statements, a comment a rewritten key would drop — is refused: ours is left as it was, each conflict is named, and a
person settles it.

The result depends only on the three inputs: theirs merged into ours and ours into theirs give the same bytes, and a
bean merged with itself is itself. Each kept statement, header key and body keeps its text as one side wrote it; the
merged statements are the base's in the base's order, then those either side added, by their form.

    merge(base, ours, theirs, knowing) -> (text, report) | (None, [conflict])"""
import collections
import json
import os
import subprocess
import sys
import tempfile

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
from core.engine import HEADER  # noqa: E402
from core.translate import _blocked, block  # noqa: E402 — the one writer of a bean's text in statements
import dmparse  # noqa: E402 — the one splitter of a front matter, and the one finder of a comment

MISSING = object()


class Refused(ValueError):
    """A side the statement merge does not read: no front matter, YAML that does not parse, or not a bean in statements."""


def canon(x):
    """A value's form: every value a string (read.loads), every map's keys sorted, every list in its order."""
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def has_comment(text):
    return any(dmparse.comment_start(ln) >= 0 for ln in text.split('\n'))


def knowing_verbs(root=ROOT):
    """The face's knowing acts (core/law/core.yaml `knowing`): a garden adds no knowing act."""
    face = read.data(os.path.join(root, 'core', 'law', 'core.yaml'))
    k = face.get('knowing')
    return set(k if isinstance(k, list) else [k])


def shift(text, d):
    """`text` moved `d` columns (left where `d` is negative): a block scalar's lines keep their place beside one another."""
    out = []
    for ln in text.split('\n'):
        if not ln or d == 0:
            out.append(ln)
        elif d > 0:
            out.append(' ' * d + ln)
        else:
            out.append(ln[min(-d, len(ln) - len(ln.lstrip(' '))):])
    return '\n'.join(out)


class Item:
    """One statement as a side wrote it: its form, its text (moved to the left margin, so that two sides indenting
    alike are read alike), the indent it was written at, its verb, roles and id."""

    def __init__(self, value, text, indent):
        self.value, self.text, self.indent = value, shift(text, -indent), indent
        self.form = canon(value)
        one = isinstance(value, dict) and len(value) == 1 and isinstance(next(iter(value.values())), dict)
        self.verb, self.roles = (next(iter(value.items())) if one else (None, {}))
        self.id = self.roles.get('id') if isinstance(self.roles.get('id'), str) else None


def flow(x):
    return yaml.safe_dump(x, default_flow_style=True, width=10 ** 9, allow_unicode=True, sort_keys=False).strip()


def item_text(value, indent=2):
    """A statement's text where no side wrote one: one line, as the translator writes it (a block where prose has
    several lines)."""
    if isinstance(value, dict) and len(value) == 1 and isinstance(next(iter(value.values())), dict) \
            and not any('\n' in s for s in _strings(value)):
        (verb, roles), = value.items()
        return ' ' * indent + f"- {verb}: {flow(roles)}\n"
    return '\n'.join((' ' * indent + ln) if ln else ln for ln in _blocked([value], block).rstrip().split('\n')) + '\n'


def _strings(x):
    if isinstance(x, dict):
        for v in x.values():
            yield from _strings(v)
    elif isinstance(x, list):
        for v in x:
            yield from _strings(v)
    elif isinstance(x, str):
        yield x


class Side:
    """A bean as one side holds it: its header keys (each its value and its text), its statements, and its body."""

    def __init__(self, text, what):
        self.what, self.keys, self.order, self.items = what, {}, [], []
        self.spans = None                # (from, dash, to) per statement, the lines of the text: set when written in a block
        self.st_head, self.body, self.lead, self.indent, self.empty = None, '', '', None, not text.strip()
        if self.empty:
            return
        head, body = dmparse.split_front_matter(text)
        if head is None:
            raise Refused(f"{what} has no front matter: a bean opens with a line `---`, and closes its front matter with "
                          f"another")
        self.body = body
        try:
            fm = read.loads(head, what)
        except read.Unread as e:
            raise Refused(str(e)) from None
        fm = {} if fm is None else fm
        if not isinstance(fm, dict):
            raise Refused(f"{what}: its front matter is a {type(fm).__name__}, not a mapping of keys")
        extra = [k for k in fm if k not in HEADER]
        if extra:
            raise Refused(f"{what} holds {', '.join(f'`{k}`' for k in extra[:4])}: not a bean in statements, whose "
                          f"header is {', '.join(HEADER)}")
        lines = head.split('\n')
        root = yaml.compose(head, Loader=yaml.BaseLoader)
        pairs = root.value if isinstance(root, yaml.MappingNode) else []
        # A LINE OF ITS OWN THAT IS A COMMENT, OR BLANK, belongs to what follows it: it is moved with the key or the
        # statement below it. A line inside a block scalar (`|`, `>`) is the value's text, whatever it looks like.
        block, todo = set(), [root] if root is not None else []
        while todo:
            n = todo.pop()
            if isinstance(n, yaml.ScalarNode) and n.style in ('|', '>'):
                block.update(range(n.start_mark.line + 1, n.end_mark.line + (1 if n.end_mark.column else 0)))
            elif isinstance(n, yaml.MappingNode):
                todo += [x for kv in n.value for x in kv]
            elif isinstance(n, yaml.SequenceNode):
                todo += n.value
        self._loose = lambda i: i not in block and (not lines[i].strip() or lines[i].lstrip().startswith('#'))
        starts, prev = [], 1
        for k, _v in pairs:
            s = k.start_mark.line
            while s - 1 >= prev and self._loose(s - 1):
                s -= 1
            starts.append(s)
            prev = k.start_mark.line + 1
        last = len(lines) - 1
        if not pairs:
            self.lead = '\n'.join(lines[1:last]) + ('\n' if last > 1 else '')
            return
        if starts[0] > 1:                     # what stands above the first key travels with it
            starts[0] = 1
        for n, (k, v) in enumerate(pairs):
            lo, hi = starts[n], starts[n + 1] if n + 1 < len(pairs) else last
            text_k = '\n'.join(lines[lo:hi]) + '\n'
            self.order.append(k.value)
            self.keys[k.value] = (fm[k.value], text_k)
            if k.value == 'statements':
                self._statements(fm[k.value], v, lines, lo, hi, k.start_mark.line)

    def _statements(self, value, node, lines, lo, hi, key_line):
        values = value if isinstance(value, list) else []
        if not isinstance(node, yaml.SequenceNode) or node.flow_style or not node.value:
            # written in flow, or empty: each statement is written anew, one to a line
            self.st_head, self.indent = 'statements:\n', None
            self.items = [Item(x, item_text(x, 0).rstrip('\n'), 0) for x in values]
            return
        starts, prev = [], key_line
        for c in node.value:
            s = c.start_mark.line
            while s > key_line and not lines[s].lstrip().startswith('-'):
                s -= 1
            dash = s
            while s - 1 > prev and self._loose(s - 1):
                s -= 1
            starts.append((s, dash))
            prev = dash
        self.st_head = '\n'.join(lines[lo:starts[0][0]]) + '\n'
        self.spans = []
        for n, (s, dash) in enumerate(starts):
            e = starts[n + 1][0] if n + 1 < len(starts) else hi
            ind = len(lines[dash]) - len(lines[dash].lstrip(' '))
            self.items.append(Item(values[n], '\n'.join(lines[s:e]), ind))
            self.spans.append((s, dash, e))       # what stands above it from `s`, the statement itself from its dash
        inds = {it.indent for it in self.items}
        self.indent = inds.pop() if len(inds) == 1 else None

    def value(self, key):
        return self.keys[key][0] if key in self.keys else MISSING

    def text(self, key):
        return self.keys[key][1] if key in self.keys else None


def three(o, a, b):
    """The value three ways: (value, conflict?) — one side's change stands, both alike stand, both unlike conflict."""
    if a == b:
        return a, False
    if a == o:
        return b, False
    if b == o:
        return a, False
    return None, True


def pick(o, a, b):
    """The text of a result two sides may have written differently, for one value: the one a side changed, else the
    least, so the order the sides are named in changes nothing. Each of o, a, b is a text or None."""
    if a is None or b is None:
        return a if b is None else b
    if a == b:
        return a
    if a == o:
        return b
    if b == o:
        return a
    return min(a, b)


def shown(x):
    if x is MISSING:
        return '(none)'
    s = x if isinstance(x, str) else flow(x)
    return s if len(s) <= 120 else s[:117] + '...'


def leaves(x, path=()):
    """{path: value} of a `details`: a list is one leaf, and so is a value that is not a map, or an empty map."""
    if isinstance(x, dict) and x:
        out = {}
        for k, v in x.items():
            out.update(leaves(v, path + (k,)))
        return out
    return {path: x}


def build(paths, orders):
    """A `details` from its leaves, each map's keys in the base's order, then the rest by name. None where a leaf and a
    map both stand at one place (one side wrote a value where the other wrote keys under it)."""
    if () in paths:
        return paths[()] if len(paths) == 1 else None
    out = {}
    for p, v in paths.items():
        at = out
        for k in p[:-1]:
            nxt = at.setdefault(k, {})
            if not isinstance(nxt, dict):
                return None
            at = nxt
        if p[-1] in at:
            return None
        at[p[-1]] = v

    def order(d, path):
        if not isinstance(d, dict):
            return d
        base = orders.get(path, [])
        keys = [k for k in base if k in d] + sorted(k for k in d if k not in base)
        return {k: order(d[k], path + (k,)) for k in keys}
    return order(out, ())


def key_orders(x, path=(), out=None):
    out = {} if out is None else out
    if isinstance(x, dict):
        out[path] = list(x)
        for k, v in x.items():
            key_orders(v, path + (k,), out)
    return out


def body_merge(o, a, b):
    """(text, conflicts): the body three ways, line by line, by git's own merge of a file (`git merge-file`)."""
    if a == b:
        return a, 0
    if a == o:
        return b, 0
    if b == o:
        return a, 0
    d = tempfile.mkdtemp(prefix='daftar-merge-body-')
    try:
        paths = []
        for name, t in (('ours', a), ('base', o), ('theirs', b)):
            p = os.path.join(d, name)
            with open(p, 'w', encoding='utf-8', newline='') as fh:
                fh.write(t)
            paths.append(p)
        r = subprocess.run(['git', 'merge-file', '-p', '--quiet', '-L', 'ours', '-L', 'base', '-L', 'theirs', *paths],
                           capture_output=True)
        if r.returncode < 0 or r.returncode > 127:
            raise Refused(f"git merge-file failed: {r.stderr.decode('utf-8', 'replace').strip()}")
        return r.stdout.decode('utf-8'), r.returncode
    finally:
        for f in os.listdir(d):
            os.remove(os.path.join(d, f))
        os.rmdir(d)


RENDER = ('bean', 'kind', 'title', 'summary', 'tags', 'statements', 'details')     # the translator's order (render)


def arrange(keys, base_order):
    """The order the merged bean writes its keys in: the base's, each key it lacks placed as a bean is written."""
    out = [k for k in base_order if k in keys]
    for k in [k for k in RENDER if k in keys and k not in out]:
        before = [n for n, x in enumerate(out) if x in RENDER and RENDER.index(x) < RENDER.index(k)]
        out.insert(before[-1] + 1 if before else 0, k)
    return out


def merge(base, ours, theirs, knowing):
    """(the merged text, a report) — or (None, [conflict]) where a true conflict stands, each `(place, ours, theirs)`.
    Refused where a side is not a bean in statements."""
    if ours == theirs:
        return ours, {'kept': 'both sides alike'}
    if base == ours:
        return theirs, {'kept': 'theirs, ours being the base'}
    if base == theirs:
        return ours, {'kept': 'ours, theirs being the base'}
    crlf = all('\r\n' in t for t in (base, ours, theirs) if t.strip())
    O, A, B = (Side(t.replace('\r\n', '\n'), w) for t, w in ((base, 'the base'), (ours, 'ours'), (theirs, 'theirs')))
    conflicts, texts, report = [], {}, collections.Counter()

    def conflict(place, a, b):
        conflicts.append((place, a if isinstance(a, str) and a.startswith('(') else shown(a),
                          b if isinstance(b, str) and b.startswith('(') else shown(b)))

    # THE HEADER, key by key
    for key in [k for k in RENDER if k != 'statements' and (k in O.keys or k in A.keys or k in B.keys)]:
        o, a, b = O.value(key), A.value(key), B.value(key)
        if MISSING in (a, b) or not (key in ('tags', 'details') and all(
                isinstance(x, list if key == 'tags' else dict) or x is MISSING for x in (o, a, b))):
            val, bad = three(*(MISSING if x is MISSING else canon(x) for x in (o, a, b)))
            if bad:
                conflict(key, a, b)
                continue
            val = MISSING if val is MISSING else json.loads(val)
        elif key == 'tags':                                  # a set, as statements are
            ol = o if isinstance(o, list) else []
            kept = [t for t in ol if t in a and t in b]
            val = kept + sorted({t for t in a + b if t not in ol and t not in kept})
        else:                                                # `details`, leaf by leaf
            lo, la, lb = (leaves(x) if x is not MISSING else {} for x in (o, a, b))
            merged = {}
            for p in sorted(set(lo) | set(la) | set(lb), key=lambda p: [str(x) for x in p]):
                v, bad = three(*(canon(x.get(p)) if p in x else MISSING for x in (lo, la, lb)))
                if bad:
                    conflict(f"details.{'.'.join(p)}", la.get(p, MISSING), lb.get(p, MISSING))
                elif v is not MISSING:
                    merged[p] = json.loads(v)
            val = build(merged, key_orders(o if o is not MISSING else {})) if merged else {}
            if val is None:
                conflict('details (a value where the other side wrote keys under it)', a, b)
                continue
        if val is MISSING:
            continue
        same = lambda x: x is not MISSING and canon(x) == canon(val)
        t = pick(O.text(key) if same(o) else None, A.text(key) if same(a) else None, B.text(key) if same(b) else None)
        if t is None:                                        # no side wrote this value: it is written anew
            if any(has_comment(s.text(key) or '') for s in (A, B)):
                conflict(f"{key} (written anew, a comment in it would be lost)", A.text(key) or MISSING,
                         B.text(key) or MISSING)
                continue
            t = _blocked({key: val}, block).rstrip('\n') + '\n'
            report['keys written anew'] += 1
        texts[key] = t

    # THE STATEMENTS, a set three ways, counted: one is kept as often as all three hold it, and added as often as the
    # side that added it most did
    cO, cA, cB = (collections.Counter(i.form for i in s.items) for s in (O, A, B))
    keep = {f: min(cO[f], cA[f], cB[f]) for f in cO}
    add = {f: max(cA[f] - cO[f], cB[f] - cO[f], 0) for f in set(cA) | set(cB)}
    nth = lambda side, f, n: ([i for i in side.items if i.form == f][n:n + 1] or [None])[0]
    text_of = lambda i: i.text if i is not None else None
    merged, seen = [], collections.Counter()
    for it in O.items:                                       # the base's, in the base's order
        if seen[it.form] >= keep[it.form]:
            continue
        n = seen[it.form]
        seen[it.form] += 1
        merged.append((it, pick(it.text, text_of(nth(A, it.form, n)), text_of(nth(B, it.form, n)))))
    for f in sorted(f for f in add if add[f]):               # then what either side added, by its form
        for n in range(cO[f], cO[f] + add[f]):
            a, b = nth(A, f, n), nth(B, f, n)
            merged.append((a or b, pick(None, text_of(a), text_of(b))))
    report['statements'] = len(merged)
    report['added'] = len(merged) - sum(keep.values())

    # KNOWING IS KEPT. An act a side added with no `of` covered what that side added; the other side's additions would
    # fall under it in the merged bean, so the merge writes its `of`: the ids of what it covered on its own side
    added = {'ours': [i for i in A.items if cA[i.form] > cO[i.form]],
             'theirs': [i for i in B.items if cB[i.form] > cO[i.form]]}
    held = {'ours': A, 'theirs': B}
    rewrite = {}
    for s, other in (('ours', 'theirs'), ('theirs', 'ours')):
        forms_other = {j.form for j in added[other]}
        blanket = [i for i in added[s] if i.verb in knowing and 'of' not in i.roles and i.form not in forms_other]
        news = [i for i in added[other] if i.verb not in knowing and i.form not in {j.form for j in added[s]}]
        if not blanket or not news:
            continue
        named = {x for i in held[s].items if i.verb in knowing
                 for x in ([i.roles['of']] if isinstance(i.roles.get('of'), str) else i.roles.get('of') or [])}
        covered = [i for i in added[s] if i.verb not in knowing and (i.id is None or i.id not in named)]
        if len(blanket) > 1:
            conflict(f"statements: {s} added {len(blanket)} knowing acts with no `of`",
                     f"({', '.join(i.verb for i in blanket)})",
                     "(which of what that side added each knew cannot be told from the three sides: give each its "
                     "`of` on its branch, and merge again)")
            continue
        unnamed = [i for i in covered if i.id is None]
        if unnamed:
            conflict(f"statements: {s} added what its `{blanket[0].verb}` with no `of` knows, and the other side added "
                     f"more", unnamed[0].value, "(a statement with no id cannot be named in an `of`: give it an id on "
                                                "its branch, and merge again)")
            continue
        act, roles = blanket[0], {}
        for k, v in act.roles.items():
            roles[k] = v
            if k == 'by':
                roles['of'] = sorted(i.id for i in covered)
        roles.setdefault('of', sorted(i.id for i in covered))
        rewrite[act.form] = {act.verb: roles}
        report['acts given their `of`'] += 1

    # AN ID NAMES ONE STATEMENT
    ids = collections.defaultdict(set)
    for it, _t in merged:
        if it.id is not None:
            ids[it.id].add(it.form)
    for sid, forms in sorted(ids.items()):
        if len(forms) > 1:
            conflict(f"statements: the id `{sid}` would name {len(forms)} statements",
                     next((i.value for i in A.items if i.id == sid), MISSING),
                     next((i.value for i in B.items if i.id == sid), MISSING))

    # THE BODY, line by line
    body, n_body = body_merge(O.body, A.body, B.body)
    if n_body:
        conflict(f"the body: {n_body} place(s) both sides changed differently", '(ours)', '(theirs)')
    elif not body.strip() and (A.body.strip() or B.body.strip()):
        conflict('the body: the merge would leave it empty', '(ours)', '(theirs)')

    # THE LINES THAT OPEN THE STATEMENTS (`statements:`, and a comment above it)
    present = three(*(s.st_head is not None for s in (O, A, B)))[0] or bool(merged)
    st_head = None
    if present:
        heads = [s.st_head for s in (O, A, B)]
        if heads[1] is None or heads[2] is None:
            st_head = heads[1] or heads[2] or heads[0] or 'statements:\n'
        else:
            st_head, bad = three(*heads)
            if bad:
                conflict('statements (the lines that open them)', heads[1], heads[2])
    if conflicts:
        return None, conflicts

    # WRITTEN: the keys in the base's order, the statements at one indent, the body
    inds = {s.indent for s in (O, A, B) if s.items and s.indent is not None}
    indent = inds.pop() if len(inds) == 1 else 2
    if present:
        texts['statements'] = (st_head + ''.join(
            item_text(rewrite[it.form], indent) if it.form in rewrite else shift(t, indent).rstrip('\n') + '\n'
            for it, t in merged)) if merged else 'statements: []\n'
    lead = pick(O.lead, A.lead, B.lead) or ''
    text = '---\n' + lead + ''.join(texts[k] for k in arrange(texts, O.order)) + '---' + body
    if crlf:
        text = text.replace('\n', '\r\n')

    # LOSSLESS, measured on what is written: every statement the merge keeps is there, and nothing else
    want = collections.Counter(canon(rewrite.get(it.form, it.value)) for it, _t in merged)
    try:
        got = Side(text.replace('\r\n', '\n'), 'the merged bean')
    except Refused as e:
        return None, [('the merged bean', str(e), '')]
    if collections.Counter(i.form for i in got.items) != want:
        return None, [('statements', 'the merged bean would not hold what the merge keeps', '')]
    return text, dict(report)


def name_of(text):
    head = dmparse.split_front_matter(text.replace('\r\n', '\n'))[0]
    try:
        fm = read.loads(head or '') or {}
    except read.Unread:
        fm = {}
    return fm.get('bean') if isinstance(fm, dict) and isinstance(fm.get('bean'), str) else None


def readall(p):
    if not os.path.isfile(p):
        return ''
    with open(p, encoding='utf-8', newline='') as fh:
        return fh.read()


def main(argv):
    if argv[:1] in (['-h'], ['--help']) or len(argv) not in (3, 4, 5):
        print(__doc__.split('\n\n')[0] + '\n\n' + __doc__.split('\n\n')[1])
        return 0 if argv[:1] in (['-h'], ['--help']) else 2
    driver = argv[0] == '--file'
    o, a, b = argv[1:4] if driver else argv[:3]
    texts = [readall(p) for p in (o, a, b)]
    bid = name_of(texts[1]) or name_of(texts[2]) or os.path.basename(argv[4] if driver and len(argv) > 4 else a)
    try:
        text, said = merge(*texts, knowing_verbs())
    except Refused as e:
        print(f"merge: refusing to merge {bid} — {e}. Ours is left as it was.", file=sys.stderr)
        return 1
    if text is None:
        print(f"merge: {bid} — {len(said)} true conflict(s), for a person to settle (MERGE.md §6); ours is left as it "
              f"was:", file=sys.stderr)
        for place, x, y in said:
            print(f"  {place}: ours {x} | theirs {y}", file=sys.stderr)
        return 1
    if not driver:
        sys.stdout.write(text)
        return 0
    with open(a, 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)
    print(f"merge: {bid} — " + ', '.join(f"{v} {k}" if isinstance(v, int) else f"{k} {v}" for k, v in said.items())
          + " (the statement merge)", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
