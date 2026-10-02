#!/usr/bin/env python3
"""why — the law and its reasons, read together.

    python3 bin/why.py clause.state           # an item of core/law/ or the garden's VOCAB.md rows, found by name
    python3 bin/why.py 'core/law/verbs.yaml: verbs[be]'   # or by its key, as this prints it
    python3 bin/why.py --check                # every reason names something the law still says (exit 1 if not)
    python3 bin/why.py --stale                # reasons that speak of a law name the law no longer has
    python3 bin/why.py --take-comments        # a garden's VOCAB.md comments moved to its reasons, each under its name

The layers daftar's words stand in: manifesto: layers. What each holds, and which files are law: MODEL.md. This reads two
of them together: a law item, and its reasoning in `seed/RATIONALE.md`, keyed by the item — `core/law/<file>: <path>`, the
path as this prints it — or a clause of `MANIFESTO.md` (or a section of another prose law document) and its reasoning, by
`doc:MANIFESTO.md#<key>`. A garden keeps its own reasons beside its VOCAB.md (`RATIONALE.md`), keyed by VOCAB.md's paths.

The law and its reasoning are RELATED, not merged: neither contains the other, and the key between them is checked. A
name finds an item — a rule, a verb, a table or a row of one, a form or its attribute (`clause.state`), a unit by its
code or its English name — printed in the law's words, with the law's vacancies at it, and its reasons.
"""
import glob, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as dmparse          # the one loader, and UTF-8 streams on every platform

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE_LAW = os.path.join(ROOT, 'core', 'law')
# A law and its reasoning come in PAIRS: the standard's, which every garden receives (core/law/ and seed/RATIONALE.md),
# and a garden's own rows, whose reasoning is the garden's to keep (`RATIONALE.md` beside its `VOCAB.md`). The same
# key's check for both.
PAIRS = [(CORE_LAW, os.path.join(ROOT, 'seed', 'RATIONALE.md')),
         (os.path.join(ROOT, 'VOCAB.md'), os.path.join(ROOT, 'RATIONALE.md'))]
PAIRS = [p for p in PAIRS if os.path.exists(p[0]) and os.path.exists(p[1])]
LAW, WHY = PAIRS[0] if PAIRS else (None, None)
CORE_KEY = re.compile(r'^(core/law/[a-z_]+\.yaml): (.+)$')


def each_pair():
    """Run the rest of this tool once per pair, the pair in force held in LAW and WHY."""
    global LAW, WHY
    for LAW, WHY in PAIRS:
        yield os.path.relpath(LAW, ROOT), os.path.relpath(WHY, ROOT)
_SEG = re.compile(r'\.?([^.\[\]]+)|\[([^\]]*)\]')


def law():
    """The law of the pair in force as data: a garden's VOCAB.md front matter; {} for the standard's, whose items are
    named by their keys (`core_keys`)."""
    if LAW is None or os.path.isdir(LAW):
        return {}
    return dmparse.loads(dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0]) or {}


_KEYS = {}


def core_keys(root=ROOT):
    """{key: node}: each item of the core's law by the key a reason names it with, `core/law/<file>: <path>`."""
    if root not in _KEYS:
        _KEYS[root] = {f"{w}: {p}": n for w, p, n in core_items(root) if w != 'VOCAB.md'}
    return _KEYS[root]


def rationale():
    out, key = {}, None
    for ln in open(WHY, encoding='utf-8').read().split('\n'):
        if ln.startswith('## '):
            key = ln[3:].strip(); out[key] = []
        elif key is not None:
            out[key].append(ln)
    return {k: '\n'.join(v).strip() for k, v in out.items()}


def resolve(data, path):
    """The law item a path names, or raise KeyError. `[x]` picks the list item one of whose fields equals x."""
    if path.startswith('doc:'):
        # a PROSE law document has no paths, but it has numbered sections: `doc:MERGE.md#5.1`. The reason is an orphan
        # the day that section is gone — the same promise a path makes, kept for law that is not data.
        name, _, sect = path[4:].partition('#')
        f = os.path.join(ROOT, name)
        if not os.path.exists(f):
            raise KeyError(path)
        want = re.compile(r'^#+ ' + re.escape(sect) + r'(\.|\s|$)') if sect else None
        if want and not any(want.match(l) for l in open(f, encoding='utf-8')):
            raise KeyError(path)
        return name
    if CORE_KEY.match(path):
        keys = core_keys()                 # an item core_items names, or a field of one, walked as a path is below
        head = next((k for k in sorted(keys, key=len, reverse=True)
                     if path == k or path.startswith(k + '.') or path.startswith(k + '[')), None)
        if head is None:
            raise KeyError(path)
        data, path = keys[head], path[len(head):]
        if not path:
            return data
    node = data
    for name, ident in _SEG.findall(path):
        if name:
            if not isinstance(node, dict) or name not in node:
                raise KeyError(path)
            node = node[name]
        else:
            if not isinstance(node, list):
                raise KeyError(path)
            if ident in ('', '·'):
                continue
            hit = [x for x in node if isinstance(x, dict) and any(str(v) == ident for v in x.values() if not isinstance(v, (dict, list)))]
            if not hit:
                raise KeyError(path)
            node = hit[0]
    return node


def orphans():
    data = law()
    bad = []
    for k in rationale():
        try:
            resolve(data, k)
        except KeyError:
            bad.append(k)
    return bad


def garden_orphans(root):
    """(the reasoning's path, [its orphaned keys]) of a garden's own pair at `root` — asked by the gate, which reads law
    and nothing else, so that only this reader opens the reasoning. (None, []) where the garden keeps none."""
    global LAW, WHY
    law_p, why_p = os.path.join(root, 'VOCAB.md'), os.path.join(root, 'RATIONALE.md')
    if not (os.path.exists(law_p) and os.path.exists(why_p)):
        return None, []
    was = (LAW, WHY)
    LAW, WHY = law_p, why_p
    try:
        return os.path.relpath(why_p, root).replace(os.sep, '/'), orphans()
    finally:
        LAW, WHY = was


def stale():
    """Reasons that speak of a law name the law no longer has. A reason that names a RETIRED construct or a removed
    registry has become journal — an account of what used to be — and is sitting one layer too high. Found by the
    names written in backticks that look like the law's own (`snake_case`) and appear nowhere in the law's text.

    A reason written of today's law (std-vocab 32) speaks of today's names; where the item it explains went keeps its
    reasons, and this counts what they speak of that the law no longer says."""
    if os.path.isdir(LAW):
        law_text = ''.join(open(f, encoding='utf-8').read() for f in sorted(glob.glob(os.path.join(LAW, '*.yaml'))))
    else:
        law_text = dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0]
    out = {}
    for k, v in rationale().items():
        gone = sorted({t for t in re.findall(r'`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`', v) if t not in law_text})
        if gone:
            out[k] = gone
    return out


HEAD = "---\nrationale_for: VOCAB.md\n---\n# why this garden's own terms are as they are\n"


def take_comments(root):
    """THE LAW CARRIES NO STORY (24.0): each comment in the front matter of `root`'s VOCAB.md moved to the reasoning kept
    beside it, under the finest path it sits on that the law resolves — a reason already there keeps its words, and the
    comment's are added after them. Section titles stay. VOCAB.md is written only where its front matter reads the same
    after. Returns (the reasoning's name, [(path, text)]); (None, []) where there is nothing to move, or VOCAB.md would
    read otherwise without its comments."""
    law_p, name = os.path.join(root, 'VOCAB.md'), 'RATIONALE.md'
    why_p = os.path.join(root, name)
    if not os.path.isfile(law_p):
        return None, []
    text = open(law_p, encoding='utf-8', newline='').read()
    head, _body = dmparse.split_front_matter(text)
    if head is None:
        return None, []
    found = dmparse.comments(head)
    if not found:
        return None, []
    data = dmparse.loads(head) or {}
    lines, moved = head.split('\n'), []
    for n, c, said, paths in found:
        key = next((p for p in paths if _resolves(data, p)), None) or next(iter(data), 'local_terms')
        if said:
            moved.append((key, said))
        lines[n] = lines[n][:c].rstrip() if lines[n][:c].strip() else None
    new_head = '\n'.join(l for l in lines if l is not None)
    new_text = text.replace(head, new_head, 1)
    if dmparse.loads(new_head) != data:
        return None, []
    old = open(why_p, encoding='utf-8', newline='').read() if os.path.isfile(why_p) else HEAD
    out = old.split('\n')
    for key, said in moved:
        at = next((i for i, l in enumerate(out) if l.rstrip('\r') == '## ' + key), None)
        if at is None:
            out += (['', f'## {key}', '', said] if out[-1].strip() else [f'## {key}', '', said])
            continue
        end = next((i for i in range(at + 1, len(out)) if out[i].startswith('## ')), len(out))
        while end > at + 1 and not out[end - 1].strip():
            end -= 1
        out[end:end] = ['', said]
    for p, s in ((why_p, '\n'.join(out).rstrip('\n') + '\n'), (law_p, new_text)):
        with open(p + '.tmp', 'w', encoding='utf-8', newline='') as fh:
            fh.write(s)
        os.replace(p + '.tmp', p)
    return name, moved


def _resolves(data, path):
    try:
        resolve(data, path)
        return True
    except KeyError:
        return False


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    if argv[0] == '--check':
        total = 0
        for _law, _why in each_pair():
            bad = orphans(); total += len(bad)
            for k in bad:
                print(f"ORPHAN  {k} — {_why} explains something {_law} no longer says")
            print(f"why: {_why}: {len(rationale())} reasons, {len(bad)} orphaned")
        return 1 if total else 0
    if argv[0] == '--take-comments':
        name, moved = take_comments(ROOT)
        for key, said in moved:
            print(f"MOVED   VOCAB.md → {name} ## {key}: {said[:80]}")
        print(f"why: {len(moved)} comment(s) of VOCAB.md moved to the reasoning beside it" if moved else
              "why: VOCAB.md's front matter carries no comment to move (or would read otherwise without them)")
        return 0
    if argv[0] == '--stale':
        for _law, _why in each_pair():
            st = stale()
            for k, gone in st.items():
                print(f"STALE   {k} — speaks of {', '.join('`'+g+'`' for g in gone)}, which {_law} no longer has")
            print(f"why: {_why}: {len(st)} reasons speak of something the law no longer says — they have become journal")
        return 0
    return core_show(argv[0])


def core_items(root=ROOT):
    """[(where, path, node)]: every item of the core's law — each table of each file of core/law/ (the garden's copy,
    else this release's), each of its rows by its name, each form and attribute of a form — and each row the garden
    adds in its VOCAB.md."""
    sys.path.insert(0, ROOT)
    from core import read
    from core.law import ROW_KEYS
    d = os.path.join(root, 'core', 'law')
    d = d if os.path.isdir(d) else os.path.join(ROOT, 'core', 'law')
    out = []

    def rows(where, key, val):
        out.append((where, key, val))
        if isinstance(val, list):
            for r in val:
                if isinstance(r, dict) and r:
                    out.append((where, f"{key}[{r[next(iter(r))]}]", r))
                elif isinstance(r, str):
                    out.append((where, f"{key}[{r}]", r))
        elif isinstance(val, dict):
            for k, v in val.items():
                out.append((where, f"{key}.{k}", v))
                for r in v if isinstance(v, list) and key == 'tables' else ():
                    if isinstance(r, str):
                        out.append((where, f"{key}.{k}[{r}]", r))
                attrs = (v.get('attrs') or {}) if key == 'forms' and isinstance(v, dict) else {}
                for a, rec in attrs.items() if isinstance(attrs, dict) else ():
                    out.append((where, f"{key}.{k}.attrs.{a}", rec))
    for name in sorted(os.listdir(d)):
        if name.endswith('.yaml'):
            for key, val in read.data(os.path.join(d, name)).items():
                rows(f"core/law/{name}", key, val)
    v = os.path.join(root, 'VOCAB.md')
    if os.path.isfile(v):
        for key, val in (read.document(v)[0] or {}).items():
            if key in ROW_KEYS:
                rows('VOCAB.md', key, val)
    return out


def _named(want, path, node=None):
    """True when `want` names the item at `path`: the path, a segment of it, or its tail (`clause.state` names
    `forms.clause.attrs.state`); a unit by its English name too."""
    for p in (path, path.replace('.attrs.', '.')):
        if want == p or re.search(r'(^|[.\[])' + re.escape(want) + r'($|[.\]])', p):
            return True
    return path.startswith('units[') and isinstance(node, dict) and node.get('name') == want


def vacant_at(path, node, every):
    """The law's vacancies (core/law/vacancies.yaml) at the item at `path`: a table's, a figure's, a form's or one of
    its attributes', or the row of a table a vacancy names."""
    rows = next((n for _w, p, n in every if p == 'vacancies'), None) or []
    m = re.match(r'([a-z_]+)\[([^\]]+)\]$', path)
    here = {'figure:' + m.group(2)} if m and m.group(1) == 'figures' else set()
    here |= {'form:' + path[len('forms.'):].replace('.attrs.', '.')} if path.startswith('forms.') else set()
    here |= {'table:' + path, 'table:' + path.split('.')[-1]}
    out = [v for v in rows if isinstance(v, dict) and v.get('at') in here]
    if m:
        out += [v for v in rows if isinstance(v, dict) and v.get('at') == 'table:' + m.group(1)
                and str(v.get('position')) == m.group(2)]
    return out


def core_show(want):
    items = [it for it in core_items() if _named(want, it[1], it[2]) or f"{it[0]}: {it[1]}" == want]
    if not items:
        print(f"why: no item of the core's law (core/law/, VOCAB.md) is named '{want}' — `python3 bin/rules.py` lists "
              f"them, and `python3 bin/catalog.py --part <name>` says one")
        return 1
    reasons = {}
    for _law, _why in each_pair():
        reasons.update(rationale())
    every = core_items()
    for where, path, node in items:
        print(f"== {where}: {path}")
        if isinstance(node, dict):
            for role, spec in (node.get('roles') or {}).items() if isinstance(node.get('roles'), dict) else ():
                print(f"   LAW role {role}: " + ', '.join(f"{k} {v}" for k, v in (spec or {}).items()))
            for f in ('says', 'meaning', 'why', 'vacant'):
                if node.get(f):
                    print(f"   LAW {f}: {' '.join(str(node[f]).split())}")
            if not any(node.get(f) for f in ('says', 'meaning', 'why')):
                for k, v in node.items():
                    if isinstance(v, str) or (isinstance(v, list) and all(isinstance(x, str) for x in v)):
                        print(f"   LAW {k}: {v}")
        elif isinstance(node, list):
            print(f"   LAW: {', '.join(str(x) if not isinstance(x, dict) else str(x.get(next(iter(x)))) for x in node[:30])}"
                  + (' …' if len(node) > 30 else ''))
        else:
            print(f"   LAW: {node}")
        for v in vacant_at(path, node, every):
            print(f"   VACANT {v.get('position')} ({v.get('reason')}): {v.get('why')}")
        key = f"{where}: {path}" if where != 'VOCAB.md' else path
        keys = [k for k in reasons if k == key or k.startswith(key + '.') or k.startswith(key + '[')]
        for k in keys:
            print(f"   -- {k}\n      " + reasons[k].replace('\n', '\n      '))
        print()
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
