#!/usr/bin/env python3
"""dmwhy — the law and its reasons, read together.

    python3 bin/dmwhy.py endpoints              # a term, a system, a registry row … found by name
    python3 bin/dmwhy.py aspects[place].metered # or by the exact path
    python3 bin/dmwhy.py --check                # every reason names something the law still says (exit 1 if not)

daftar keeps its own material in FOUR places, and a thing belongs in exactly one:

  LAW        seed/std-vocab.md (and a garden's VOCAB.md): what is in force. Present tense. Each item carries, as DATA,
             the `meaning:` and `why:` a reader needs in order to apply it. No dates, no names, no "until".
  RATIONALE  seed/RATIONALE.md: why the law is the way it is — the argument, what was considered and refused, the
             incident a rule answers. Keyed by the PATH of the law item it explains.
  RECORD     the changelog at the foot of the law, HISTORY.md, and a garden's log/journal.md: what happened, when, by whom.
  GUIDE      README, seed/COOKBOOK.md: how to do a thing. Nothing reads a guide, so nothing in one is load-bearing.

The law and its rationale are RELATED, not merged: neither contains the other, and the key between them is checked.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml, dmparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAW, WHY = os.path.join(ROOT, 'seed', 'std-vocab.md'), os.path.join(ROOT, 'seed', 'RATIONALE.md')
_SEG = re.compile(r'\.?([^.\[\]]+)|\[([^\]]*)\]')


def law():
    return yaml.safe_load(dmparse.split_front_matter(open(LAW, encoding='utf-8').read())[0]) or {}


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


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    if argv[0] == '--check':
        bad = orphans()
        for k in bad:
            print(f"ORPHAN  {k} — the rationale explains something the law no longer says")
        print(f"dmwhy: {len(rationale())} reasons, {len(bad)} orphaned")
        return 1 if bad else 0
    want, data, why = argv[0], law(), rationale()
    keys = [k for k in why if k == want or re.search(r'(^|[.\[])' + re.escape(want) + r'($|[.\]])', k)]
    if not keys:
        print(f"dmwhy: no rationale names '{want}'"); return 1
    for k in keys:
        print(f"== {k}")
        try:
            node = resolve(data, k)
            for f in ('meaning', 'why'):
                if isinstance(node, dict) and node.get(f):
                    print(f"   LAW {f}: {str(node[f]).strip()}")
            if not isinstance(node, (dict, list)):
                print(f"   LAW: {node}")
        except KeyError:
            print("   (ORPHAN: the law no longer says this)")
        print('   ' + why[k].replace('\n', '\n   ') + '\n')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
