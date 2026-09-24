#!/usr/bin/env python3
"""dmwhy — the law and its reasons, read together.

    python3 bin/dmwhy.py endpoints              # a term, a system, a registry row … found by name
    python3 bin/dmwhy.py aspects[place].metered # or by the exact path
    python3 bin/dmwhy.py --check                # every reason names something the law still says (exit 1 if not)
    python3 bin/dmwhy.py --stale                # reasons that speak of a law name the law no longer has

daftar keeps its own material in FOUR layers, and each stands on the one beneath it:

  LAWS       clear and brief, there for usability and efficiency: what is in force, in the present tense. An item
             carries, as DATA, the `meaning:` and `why:` a reader needs in order to APPLY it — and nothing else.
             (`seed/std-vocab.md`, a garden's `VOCAB.md`, MODEL.md, CHECKLIST.md, MERGE.md)
  REASONING  the backbone for the laws: why a law is the way it is — the argument, what was considered and refused.
             Keyed by the PATH of the law item it supports. (`seed/RATIONALE.md`)
  JOURNALS   the leads for the reasoning: what was done and why, by whom, entry by entry. Reasoning is drawn FROM these
             and cites them. (the changelog at the foot of the law; a garden's `log/journal.md`)
  HISTORY    the exact record of events, as accurate as it can be made, which the journals are written from: commits and
             their diffs, tags, captured outputs, a datum's own append-only record. It is never summarised.

A thing belongs in exactly ONE layer, and each layer points DOWN: a law item to its reasoning by path, reasoning to the
journal entries it was drawn from, a journal entry to the commits and captures it describes. A GUIDE (README, the
COOKBOOK) is outside the chain: nothing reads one, so nothing in one is load-bearing.

The law and its reasoning are RELATED, not merged: neither contains the other, and the key between them is checked.
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
    if argv[0] == '--stale':
        for _law, _why in each_pair():
            st = stale()
            for k, gone in st.items():
                print(f"STALE   {k} — speaks of {', '.join('`'+g+'`' for g in gone)}, which {_law} no longer has")
            print(f"dmwhy: {_why}: {len(st)} reasons speak of something the law no longer says — they have become journal")
        return 0
    found = 0
    for _law, _why in each_pair():
        found += _show(argv[0])
    if not found:
        print(f"dmwhy: no rationale names '{argv[0]}'"); return 1
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
