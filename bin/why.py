#!/usr/bin/env python3
"""why — the law and its reasons, read together.

    python3 bin/why.py endpoints              # a term, a system, a registry row … found by name
    python3 bin/why.py aspects[place].metered # or by the exact path
    python3 bin/why.py --check                # every reason names something the law still says (exit 1 if not)
    python3 bin/why.py --stale                # reasons that speak of a law name the law no longer has
    python3 bin/why.py --take-comments        # a garden's VOCAB.md comments moved to its reasons, each under its name

The layers daftar's words stand in: manifesto: layers. What each holds, and which files are law: MODEL.md, "Five
layers" and "The journal and the gate". This reads two of them together: a law item, and its reasoning in
`seed/RATIONALE.md`, keyed by the item's PATH — or a clause of `MANIFESTO.md` and its reasoning, by
`doc:MANIFESTO.md#<key>`.

The law and its reasoning are RELATED, not merged: neither contains the other, and the key between them is checked.

IN A GARDEN OF THE CORE (v1 part 9) a name finds an item of core/law/ or of the garden's VOCAB.md rows — a rule, a verb,
a table or a row of one, a form or its attribute (`clause.state`), a unit by its code or its English name — printed in
the law's words, with the law's vacancies at it, and the reasons seed/RATIONALE.md keeps for what it came from: what its
row `replaces`, else the table of today's law it was generated from. The reasons stay keyed by today's paths until v1
part 13 keys them by the core's; `--check`, `--stale` and `--take-comments` read them as before.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse          # the one loader, and UTF-8 streams on every platform

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# A law and its reasoning come in PAIRS: the standard's, which every garden receives, and a garden's own overlay, whose
# reasoning is the garden's to keep (`RATIONALE.md` beside its `VOCAB.md`). The same key, the same check, for both.
PAIRS = [(os.path.join(ROOT, 'seed', 'std-vocab.md'), os.path.join(ROOT, 'seed', 'RATIONALE.md')),
         (os.path.join(ROOT, 'VOCAB.md'), os.path.join(ROOT, 'RATIONALE.md'))]
PAIRS = [p for p in PAIRS if os.path.exists(p[0]) and os.path.exists(p[1])]
LAW, WHY = PAIRS[0] if PAIRS else (None, None)


def each_pair():
    """Run the rest of this tool once per pair, the pair in force held in LAW and WHY."""
    global LAW, WHY
    for LAW, WHY in PAIRS:
        yield os.path.relpath(LAW, ROOT), os.path.relpath(WHY, ROOT)
_SEG = re.compile(r'\.?([^.\[\]]+)|\[([^\]]*)\]')


def law():
    return dmparse.loads(dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0]) or {}


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

    The law's `retired:` list is not read as the law SAYING a name: it names what the law took back. A reason that
    still speaks of `agreement_ref` found the name there and passed, which is how a description of the retired
    contract keys outlived them."""
    law_text = re.sub(r'(?ms)^retired:[ \t]*\n.*?(?=^[^\s#])', '', dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0])
    out = {}
    for k, v in rationale().items():
        if k == 'retired' or k.startswith('retired.') or k.startswith('retired['):
            continue                        # the reason for the retired list speaks of what it retired, by design
        gone = sorted({t for t in re.findall(r'`([a-z][a-z0-9]*(?:_[a-z0-9]+)+)`', v) if t not in law_text})
        if gone:
            out[k] = gone
    return out


def rekey(root, rules):
    """A garden's own reasons follow a rename of what they explain (bin/dmupgrade.py, crossing into a release that renamed
    a path of VOCAB.md): each heading of the reasoning kept beside `root`'s VOCAB.md whose KEY a rule matches is re-keyed —
    the heading line alone, since what a reason says is its writer's own words. `rules` are (compiled pattern,
    replacement) pairs applied in order to the key. The file keeps its line ends and byte-order mark, and is written whole
    beside itself, then swapped in. Returns (the file's name, [(old key, new key)]), or (None, []) where there is none."""
    name = 'RATIONALE.md'
    path = os.path.join(root, name)
    if not (os.path.isfile(path) and os.path.isfile(os.path.join(root, 'VOCAB.md'))):
        return None, []
    lines, done = open(path, encoding='utf-8', newline='').read().split('\n'), []
    for i, line in enumerate(lines):
        cr = '\r' if line.endswith('\r') else ''
        body = line[:len(line) - len(cr)]
        mark = '\ufeff' if i == 0 and body.startswith('\ufeff') else ''
        if not body[len(mark):].startswith('## '):
            continue
        key = new = body[len(mark) + 3:]
        for rx, to in rules:
            new = rx.sub(to, new)
        if new != key:
            lines[i] = mark + '## ' + new + cr
            done.append((key, new))
    if done:
        with open(path + '.tmp', 'w', encoding='utf-8', newline='') as fh:
            fh.write('\n'.join(lines))
        os.replace(path + '.tmp', path)
    return name, done


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
            print(f"dmwhy: {_why}: {len(rationale())} reasons, {len(bad)} orphaned")
        return 1 if total else 0
    if argv[0] == '--take-comments':
        name, moved = take_comments(ROOT)
        for key, said in moved:
            print(f"MOVED   VOCAB.md → {name} ## {key}: {said[:80]}")
        print(f"dmwhy: {len(moved)} comment(s) of VOCAB.md moved to the reasoning beside it" if moved else
              "dmwhy: VOCAB.md's front matter carries no comment to move (or would read otherwise without them)")
        return 0
    if argv[0] == '--stale':
        for _law, _why in each_pair():
            st = stale()
            for k, gone in st.items():
                print(f"STALE   {k} — speaks of {', '.join('`'+g+'`' for g in gone)}, which {_law} no longer has")
            print(f"dmwhy: {_why}: {len(st)} reasons speak of something the law no longer says — they have become journal")
        return 0
    if runs_core():
        return core_show(argv[0])
    found = 0
    for _law, _why in each_pair():
        found += _show(argv[0])
    if not found:
        print(f"dmwhy: no rationale names '{argv[0]}'"); return 1
    return 0


# ---- a garden of the core (v1 part 9) -------------------------------------------------------------------------------
# The law is core/law/ and the rows a garden adds (VOCAB.md); an item is named as the reasons name one — `verbs[be]`,
# `forms.clause.attrs.state`, `systems[geographic]` — or by its own name alone. Its reasons are still the ones
# seed/RATIONALE.md keeps under today's paths until v1 part 13 keys them by the core's: each item is shown with the
# reasons of what it came from — what its row `replaces` (a verb's terms, a form's term or section), or the table of
# today's law it was generated from (core/translate.py), else the same path — so a reason is read where it was written.
CORE_FROM = {'tools': 'verbs', 'families': 'tool_families', 'reasons': 'vacancy_reasons', 'kinds': 'gene',
             'comparisons': 'comparators', 'lines': 'aspects', 'levels': 'complexity', 'modes': 'facets'}


def runs_core():
    import check                                   # the one reader of a garden's pin (bin/check.py)
    return check.runs_core(check.pin(ROOT))


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


def core_from(where, path, node, today, form_of=None):
    """Today's paths the core's item came from: what its row `replaces`, else the table it was generated from, else the
    same path where today's law has it."""
    sys.path.insert(0, ROOT)
    from core import translate
    terms = {str(t.get('term')) for t in today.get('terms') or [] if isinstance(t, dict)}
    out = []
    if isinstance(node, dict):
        for w in node.get('replaces') or [] if isinstance(node.get('replaces'), list) else [node.get('replaces')]:
            if w:
                out.append(f"terms[{w}]" if str(w) in terms else str(w))
    fa = re.match(r'forms\.([a-z_]+)\.attrs\.([a-z_]+)$', path)
    if fa and form_of:                                  # an attribute of a form: the attribute of what the form replaces
        return [f"{w}.schema.attrs.{fa.group(2)}" if w.startswith('terms[') else f"{w}.{fa.group(2)}"
                for w in core_from(where, 'forms.' + fa.group(1), form_of(fa.group(1)), today)]
    m = re.match(r'([a-z_]+)(\[([^\]]+)\])?', path)
    head, name = (m.group(1), m.group(3)) if m else (path, None)
    if head == 'verbs' and name and where == 'core/law/core.yaml':
        face = translate_face_replaces()
        out += [f"terms[{w}]" for w in face.get(name, []) if w in terms]
    old = {new: o for _what, tables in translate.STANDARDS.values() for new, o in tables}.get(head) or CORE_FROM.get(head)
    if head == 'units' and isinstance(node, dict) and node.get('name'):
        name = str(node['name'])
    if head == 'modes' and name:
        name = {v: k for k, v in translate.MODES.items()}.get(name, name)
    if not out:
        cand = f"{old or head}[{name}]" if name else (old or head)
        try:
            resolve(today, cand)
            out.append(cand)
        except KeyError:
            pass
    return out


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


def translate_face_replaces():
    sys.path.insert(0, ROOT)
    from core import read
    return read.data(os.path.join(ROOT, 'core', 'law', 'verbs.yaml')).get('face_replaces') or {}


def core_show(want):
    items = [it for it in core_items() if _named(want, it[1], it[2])]
    if not items:
        print(f"why: no item of the core's law (core/law/, VOCAB.md) is named '{want}' — `python3 bin/rules.py` lists "
              f"them, and `python3 bin/catalog.py --part <name>` says one")
        return 1
    global LAW, WHY
    LAW, WHY = PAIRS[0] if PAIRS else (None, None)
    today = law() if LAW else {}
    reasons = rationale() if WHY else {}
    every = core_items()
    forms = {p[len('forms.'):]: n for _w, p, n in every if re.match(r'forms\.[a-z_]+$', p)}
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
        came = core_from(where, path, node, today, lambda f: forms.get(f)) if where != 'VOCAB.md' else []
        keys = [k for c in came for k in reasons if k == c or k.startswith(c + '.') or k.startswith(c + '[')]
        if came:
            print(f"   came from today's {', '.join(came)} — its reasons, in {os.path.relpath(WHY, ROOT) if WHY else '(none)'}:"
                  if keys else f"   came from today's {', '.join(came)}, which no reason explains")
        for k in dict.fromkeys(keys):
            print(f"   -- {k}\n      " + reasons[k].replace('\n', '\n      '))
        print()
    return 0


def names(want, why=None):
    """The reasons `dmwhy <want>` prints, by key: the one keyed `want`, and each whose path holds it as a segment."""
    return [k for k in (rationale() if why is None else why)
            if k == want or re.search(r'(^|[.\[])' + re.escape(want) + r'($|[.\]])', k)]


def answers(want):
    """True when `dmwhy <want>` finds a reason, in either pair — what a refusal asks before it offers the command."""
    global LAW, WHY
    _was = LAW, WHY
    try:
        return any(names(want) for _pair in each_pair())
    finally:
        LAW, WHY = _was


def _show(want):
    data, why = law(), rationale()
    keys = names(want, why)
    for k in keys:
        print(f"== {k}")
        try:
            node = resolve(data, k)
            for f in ('meaning', 'why'):
                if isinstance(node, dict) and node.get(f):
                    print(f"   LAW {f}: {str(node[f]).strip()}")
            if isinstance(node, dict) and not (node.get('meaning') or node.get('why')):
                # a block of positions (values_meaning, a registry row, an attrs map): the law's own words per key
                for _k, _v in node.items():
                    if isinstance(_v, (str, int, float, bool)):
                        print(f"   LAW {_k}: {str(_v).strip()}")
            if not isinstance(node, (dict, list)):
                print(f"   LAW: {node}")
        except KeyError:
            print("   (ORPHAN: the law no longer says this)")
        print('   ' + why[k].replace('\n', '\n   ') + '\n')
    return len(keys)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
