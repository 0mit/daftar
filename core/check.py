#!/usr/bin/env python3
"""check — judge a garden written in the core's statements, by the core's thirteen rules.

    python3 core/check.py [<garden>]      # every bean of the garden at <garden> (here, if none is named)
    python3 core/check.py --law           # the law alone: the face, the verbs' rows and the levels, proved together

(`python` on Windows.) The beans are `beans/**/*.md`, the zone the days are reckoned in is GARDEN.md's `zone`, and the
garden's own rows — kinds, levels, namespaces, flows, the layers' standing, verbs, rows added to a table — are VOCAB.md's
(core/law.py says which keys). Each finding is an error, printed as `<rule>  <where>: <what>`; the last line counts
them, and the exit status is 1 when there is one. This command runs beside today's gate (`bin/dmcheck.py`), which it
does not replace until a garden adopts the core."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import engine, read  # noqa: E402
from core.law import Law       # noqa: E402


def garden_law(root):
    """The release's law, extended by the rows of the garden at `root` (its VOCAB.md, where it has one)."""
    p = os.path.join(root, 'VOCAB.md')
    return Law.load(('VOCAB.md', read.document(p)[0])) if os.path.exists(p) else Law.load()


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    if argv[:1] == ['--law']:
        law = Law.load()
        found = law.problems()
        for rule, where, msg in found:
            print(f"{rule:<11} {where}: {msg}")
        print(f"core law: {len(law.verbs)} verbs, {len(law.levels)} levels, {len(law.rules)} rules — {len(found)} error(s)")
        return 1 if found else 0
    root = os.path.abspath(argv[0] if argv else '.')
    try:
        law = garden_law(root)
    except read.Unread as e:
        print(f"form        VOCAB.md: {e}")
        return 1
    garden = engine.Garden.read(root)
    found = engine.judge(law, garden)
    for rule, where, msg in found:
        print(f"{rule:<11} {where}: {msg}")
    n = sum(len(b.statements) for b in garden.beans.values())
    print(f"core check: {os.path.basename(root)}: {len(garden.beans)} beans, {n} statements — {len(found)} error(s)")
    return 1 if found else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
