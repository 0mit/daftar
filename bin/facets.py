#!/usr/bin/env python3
"""facets — the keys of `details` a merge would reach, and their shapes.

There is no merge facet to declare in a garden of the core: the statement merge keeps a bean's statements as a set and
merges its header and `details` three-way (MERGE.md). This says so, and names the keys of `details` whose shape
differs from bean to bean — where two gardens' values of one key would meet in two shapes.

Usage: python3 bin/facets.py
"""
import collections, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as dmparse
import garden as dmgarden  # noqa: E402 — the one garden model: where its documents are
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---- a garden of the core (v1 part 9) -------------------------------------------------------------------------------
# The statement merge (core/merge.py, MERGE.md) keeps a bean's statements as a set — both sides kept, two that
# differ side by side — and merges its header and its `details` three-way, refusing a true conflict for a person. It
# has no shape fallback, so no facet is declared and none would ratify or change anything: this says so, with what the
# merge reaches, and names the `details` keys whose shape differs from bean to bean — where a three-way merge refuses
# what today's fallback guessed, and which statements may say better.

def shape_of(v):
    return 'mapping' if isinstance(v, dict) else 'list' if isinstance(v, list) else 'scalar'


def core_main():
    sys.path.insert(0, ROOT)
    from core import read
    beans = statements = 0
    header, details = collections.Counter(), collections.defaultdict(lambda: {'shapes': collections.Counter(),
                                                                              'where': set()})
    for path in dmgarden.paths(ROOT):
        fm = read.document(path)[0] or {}
        beans += 1
        statements += len(fm.get('statements') or [])
        header.update(k for k in fm if k not in ('statements', 'details'))
        for k, v in (fm.get('details') or {}).items() if isinstance(fm.get('details'), dict) else ():
            details[k]['shapes'][shape_of(v)] += 1
            details[k]['where'].add(os.path.basename(path)[:-3])
    mixed = sorted((k, r) for k, r in details.items() if len(r['shapes']) > 1)
    print(f"facets — a garden of the core declares no merge facet: the statement merge keeps {statements} statements "
          f"of {beans} beans as a set, and merges {len(header)} header keys and {len(details)} keys of `details` "
          f"three-way, a true conflict refused for a person (MERGE.md). Nothing ratifies, and nothing moves.")
    print(f"\n`details` keys whose shape differs from bean to bean ({len(mixed)}) — a merge of two such values is a "
          f"conflict, and statements may say them better:")
    for k, r in mixed if '--all' in sys.argv else mixed[:20]:
        print(f"  {k:28} {dict(r['shapes'])}  ({len(r['where'])} beans)")
    if len(mixed) > 20 and '--all' not in sys.argv:
        print(f"  … and {len(mixed) - 20} more (--all)")
    return 0


def main():
    return core_main()


if __name__ == '__main__':
    sys.exit(main())
