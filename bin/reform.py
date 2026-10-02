#!/usr/bin/env python3
"""reform — a bean written in today's words, written in the core's statements in place, proved by the count.

    python3 bin/reform.py <bean.md> [...]            # a bean in today's words, in statements
    python3 bin/reform.py --check <bean.md> [...]    # ...exit 1 where one is still in today's words

What is written in old words in a garden of the core is a bean in today's words — from a branch made before the garden
adopted the core, merged after (bin/merge.py refuses to merge it until it is written in statements), or a proposal from
a garden that runs today's language. It is written in statements in place by the core's translator (core/translate.py
`translate_bean`), with the garden's own law, and proved as the adoption is: every value of the old front matter given
exactly one place, and found there when the written file is read back, or nothing is written. Its knowing acts are made
NOW, `at: now`, which the save writes: a statement a commit adds is known by an act the commit adds, and only the
adoption carries the moments history recorded; the day each knew it stays in `details`. A name the translation gives in
a namespace, or a kind, the garden's law has no row for is a change to the law, a RULE-CHANGE: it is named, and nothing
is written until a person adds the row.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Now:
    """The translator's journal for a reform: every act is made now, the day it carried kept in `details`."""

    def moment(self, bid, path, day):
        return 'now', f"reformed into statements, known now; its day, {day}, stays in details"


def reform_beans(paths, check_only):
    """A garden of the core: each bean in today's words written in statements, in place, proved by the count."""
    sys.path.insert(0, ROOT)
    from core import engine, read, standards, translate
    from core.check import garden_law
    from safe import write_atomic
    std = standards.here(ROOT) if standards.carried(ROOT) else standards.here()
    law = garden_law(ROOT)
    ctx = translate.Context(ROOT, law, std)
    ctx.journal = Now()
    rc = 0
    for p in paths:
        try:
            fm = read.document(p)[0]
        except read.Unread as e:
            print(f"{p}: NOT REFORMED — {e}"); rc = 1
            continue
        if all(k in engine.HEADER for k in fm):
            print(f"{p}: in statements already")
            continue
        if check_only:
            print(f"{p}: in today's words — {', '.join(sorted(k for k in fm if k not in engine.HEADER)[:6])}"); rc = 1
            continue
        known = set(ctx.namespaces)
        rel = os.path.relpath(os.path.abspath(p), ROOT).replace(os.sep, '/')
        try:
            text, b = translate.translate_bean(p, rel, ctx)
        except Exception as e:
            print(f"{p}: NOT REFORMED — the translator cannot read it: {type(e).__name__}: {e}"); rc = 1
            continue
        problems = translate.verify(b, text) + [str(n) for n in b.notes if 'reformed into statements' not in str(n)]
        rows = sorted(ns for ns in set(ctx.namespaces) - known if ns not in law.namespaces)
        kind = b.header.get('kind') if isinstance(getattr(b, 'header', None), dict) else None
        if kind and kind not in law.kinds:
            rows.append(f"the kind `{kind}`")
        if rows:
            problems.append(f"the garden's law has no row for {', '.join(f'`{r}`' if not r.startswith('the ') else r for r in rows)}: "
                            f"add it to VOCAB.md (a RULE-CHANGE, a person's to ratify), then reform this again")
        if problems:
            print(f"{p}: NOT REFORMED — nothing written:\n" + '\n'.join('  ' + x for x in problems[:12])); rc = 1
            continue
        write_atomic(p, text)
        print(f"{p}: reformed into statements — {len(b.statements)} statement(s), {len(translate.leaves(b.old))} value(s) "
              f"placed; save it, the entry naming `{b.id}`")
    return rc


def main(argv):
    check = '--check' in argv
    paths = [a for a in argv if not a.startswith('--')]
    if not paths:
        print(__doc__); return 2
    return reform_beans(paths, check)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
