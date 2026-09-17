#!/usr/bin/env python3
"""dmfacets — the split report: which merge facets would RATIFY current behaviour, and which would CHANGE it.

Phase 6 proposes declaring `merge: {cardinality, order}` for the member keys that carry this estate's
actual facts. The design record is explicit that the report comes first and the declarations after,
because the cost of the phase is not the number of keys — it is how many of them MOVE.

  A declaration that MATCHES what the shape fallback already does ratifies existing behaviour. Nothing
  merges differently afterwards, so it is safe to enact under delegation.

  A declaration that CHANGES it retroactively re-classifies beans that already passed the gate. That is
  a MAJOR bump by this garden's own versioning rule and it belongs to the operator.

The dangerous middle is the point of the whole exercise: `facet()` reads cardinality from
`items[0]['value']` — the FIRST garden's value — so a key whose shape differs between gardens merges by
whichever one arrived first. For those keys there is no "current behaviour" to ratify; declaring one
picks a winner, and that is a decision, not a tidy-up.

This tool imports bin/dmmerge.py rather than restating its rules: the fallback it reports must be the
fallback that runs.

Usage: python3 bin/dmfacets.py [--all] [--csv]
"""
import os, sys, glob, collections

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmmerge as M
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def shape_of(v):
    return 'mapping' if isinstance(v, dict) else 'list' if isinstance(v, list) else 'scalar'


def walk():
    """Every (key, value) a merge would actually reach: top-level keys, then the members of multi ones."""
    seen = collections.defaultdict(lambda: {'shapes': collections.Counter(), 'where': set(),
                                            'top': False, 'declarable': False, 'parents': set()})
    for path in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
            sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))):
        fm = dmparse.loads(dmparse.read(path)[0] or '') or {}
        base = os.path.basename(path)[:-3]
        for k, v in fm.items():
            if k in M.STRUCTURAL:
                continue
            rec = seen[k]
            rec['shapes'][shape_of(v)] += 1
            rec['where'].add(base)
            rec['top'] = True
            card, order = M.facet(k, v)
            if card != 'multi':
                continue
            try:
                members = M.members(k, order, v)
            except ValueError:
                continue                      # a duplicate member key: Phase 5 refuses it, not our business
            for mk, mv in members.items():
                r = seen[mk]
                r['shapes'][shape_of(mv)] += 1
                r['where'].add(f"{base}.{k}")
                # A member reached BY-KEY is a NAME someone could declare a term for (`owns.os`,
                # `details.safety`). A member reached by-path / by-bean / by-facet is a DATA VALUE — a
                # filesystem path, a bean id — and no vocabulary can carry a term per instance of one.
                # Those are governed by their parent's declaration, which already exists. Conflating the
                # two is how "214 undeclared keys" turns into a number nobody can act on.
                r['declarable'] = r.get('declarable', False) or (order == 'by-key')
                r.setdefault('parents', set()).add(k)
    return seen


def classify(key, rec):
    """DECLARED / RATIFIES / MOVES — and the reason, which is the only part worth reading."""
    m = (M.TERMS.get(key) or {}).get('merge')
    if isinstance(m, dict) and m.get('cardinality'):
        return 'DECLARED', f"{m['cardinality']}/{m.get('order', 'none')}", "the vocabulary already says"
    shapes = list(rec['shapes'])
    fallback = {'mapping': 'multi/by-key', 'list': 'set/none', 'scalar': 'single/none'}
    # THE ORDER IS NOT ALWAYS 'none', AND GETTING THIS WRONG WOULD CAUSE THE REGRESSION THIS REPORT
    # EXISTS TO PREVENT. `leaf_order()` returns 'cidr' or 'version' for keys it recognises BY NAME, and
    # it consults a declared order FIRST — so declaring `order: none` for one of them silently switches
    # the subsumption off. `192.168.0.0/24` would stop being absorbed by `192.168.0.0/16`, and
    # `AlmaLinux 9` would stop losing to `AlmaLinux 9.8`: both become conflicts where today they merge.
    inferred = M.leaf_order(key, None)
    if len(shapes) == 1:
        card = fallback[shapes[0]].split('/')[0]
        if inferred != 'none':
            return 'RATIFIES', f"{card}/{inferred}", \
                (f"one shape everywhere ({shapes[0]}, {sum(rec['shapes'].values())}x) — and the order "
                 f"must be '{inferred}', which leaf_order() infers from the NAME today. Declaring "
                 f"'none' here would DISABLE subsumption, not ratify it.")
        return 'RATIFIES', fallback[shapes[0]], f"one shape everywhere ({shapes[0]}, {sum(rec['shapes'].values())}x)"
    counts = ', '.join(f"{s}x{n}" for s, n in sorted(rec['shapes'].items()))
    return 'MOVES', ' | '.join(sorted({fallback[s] for s in shapes})), \
        f"SHAPE VARIES ({counts}) — the fallback reads the FIRST garden's value, so this key merges by " \
        f"arrival order today and any declaration picks a winner"


NAME_HEURISTIC = "leaf_order() infers this from the KEY'S NAME, not from a declaration"


def name_ordered(key):
    """Does this key get a subsumption order from the registry rather than from a term?

    This used to be a COPY of the two heuristics that lived in dmmerge — a second copy of a rule, in the
    tool whose job is to report where rules live. It asks dmmerge now, and dmmerge asks the vocabulary.
    """
    return M.leaf_order(key, None) != 'none'


def main():
    show_all = '--all' in sys.argv
    seen = walk()
    buckets = collections.defaultdict(list)
    opaque = []
    for key, rec in sorted(seen.items()):
        verdict, facet, why = classify(key, rec)
        n = sum(rec['shapes'].values())
        if verdict != 'DECLARED' and not rec['top'] and not rec['declarable']:
            opaque.append((key, sorted(rec['parents'])))
            continue
        buckets[verdict].append((key, facet, why, n, sorted(rec['where'])))

    if '--csv' in sys.argv:
        print("verdict,key,facet,instances,why")
        for verdict in ('MOVES', 'RATIFIES', 'DECLARED'):
            for key, facet, why, n, _w in buckets[verdict]:
                print(f'{verdict},{key},"{facet}",{n},"{why}"')
        return 0

    total = sum(len(v) for v in buckets.values())
    print(f"\ndmfacets — {total} keys a merge of this corpus would reach\n")

    print("MOVES — declaring one of these CHANGES how an existing bean merges. The operator's.")
    if not buckets['MOVES']:
        print("      (none)")
    for key, facet, why, n, where in buckets['MOVES']:
        print(f"  {key:<28} {facet:<26} {n:>4}x")
        print(f"      {why}")
        print(f"      seen in: {', '.join(where[:6])}{' …' if len(where) > 6 else ''}")

    heur = [k for k, _f, _w, _n, _wh in buckets['RATIFIES'] + buckets['DECLARED'] if name_ordered(k)]
    print(f"\nRATIFIES — one shape everywhere, so declaring the fallback changes nothing. Delegated. "
          f"({len(buckets['RATIFIES'])} keys)")
    for key, facet, why, n, where in (buckets['RATIFIES'] if show_all else buckets['RATIFIES'][:12]):
        print(f"  {key:<28} {facet:<26} {n:>4}x   {why}")
    if not show_all and len(buckets['RATIFIES']) > 12:
        print(f"  … {len(buckets['RATIFIES']) - 12} more (--all to list them)")

    print(f"\nDECLARED — a term already carries a merge facet. ({len(buckets['DECLARED'])} keys)")
    for key, facet, _why, n, _w in buckets['DECLARED']:
        print(f"  {key:<28} {facet:<26} {n:>4}x")

    if heur:
        print(f"\nORDER TAKEN FROM A NAME, NOT A DECLARATION — {len(heur)} key(s). `leaf_order()` says so "
              f"itself:\n  \"the last hardcoded merge knowledge here, and they belong in the vocabulary\".")
        for k in sorted(heur):
            print(f"  {k}")

    byparent = collections.Counter(p for _k, ps in opaque for p in ps)
    print(f"\nNOT DECLARABLE — {len(opaque)} member(s) reached by a data field rather than by name: "
          f"{', '.join(f'{p} x{n}' for p, n in byparent.most_common())}.")
    print("  These are paths, bean ids and facet names — VALUES. A vocabulary cannot carry a term per\n"
          "  instance, and it does not need to: they are governed by their parent's declaration, which\n"
          "  every one of those parents already has. Counting them as 'undeclared keys' inflates the\n"
          "  phase with work nobody can do.")

    print(f"\nTHE SPLIT (declarable keys only): {len(buckets['MOVES'])} move · "
          f"{len(buckets['RATIFIES'])} ratify · {len(buckets['DECLARED'])} already declared")
    print("\nMEASURED ON ONE GARDEN, WHICH IS THE LIMIT OF THIS REPORT. `facet()` reads the FIRST\n"
          "garden's value, so the risk it measures is disagreement BETWEEN gardens. This corpus can only\n"
          "show where one garden is already inconsistent with itself. A key listed as RATIFIES here is\n"
          "safe to declare AS THIS GARDEN MERGES TODAY; a second garden may still disagree about it, and\n"
          "that is exactly what a declaration would settle.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
