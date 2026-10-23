#!/usr/bin/env python3
"""check — judge a garden written in the core's statements, by the core's twenty-one rules.

    python3 core/check.py [<garden>]      # every bean of the garden at <garden> (here, if none is named)
    python3 core/check.py --staged        # what a commit would hold: the INDEX, and the commit's own rules
    python3 core/check.py --law           # the law alone: the face, the verbs' rows and the levels, proved together
    python3 core/check.py ... --json      # the same verdict as one JSON document: {found, printed}

(`python` on Windows.) The beans are `beans/**/*.md`, the zone the days are reckoned in is GARDEN.md's `zone`, and the
garden's own rows — kinds, levels, namespaces, flows, the layers' standing, verbs, rows added to a table — are VOCAB.md's
(core/law.py says which keys). Each finding is an error, printed as `<rule>  <where>: <what>`; the last line counts
them, and the exit status is 1 when there is one.

`--staged` is the commit's gate, run by bin/hooks/pre-commit through bin/check.py (bin/install.py installs it): every staged file
is copied out of the index into a temporary directory and judged there, with the law the commit stages, so what is
judged is what is committed; then the commit's own rules (core/commit.py): each changed bean named by the entry the
commit adds, its new statements known at that entry's moment, and a change to the law said to be a RULE-CHANGE. This
command is the gate bin/check.py runs. Every verdict is the one judge's (core/judge.py): this file only prints it."""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import read  # noqa: E402
from core.judge import Scope, garden_law, judge  # noqa: E402,F401 — garden_law: every tool reads a garden's law here


GROUPED = 5          # findings of one rule saying one thing in this many places or more are printed as one line


def report(found, line):
    """Each finding as `<rule> <where>: <what>`; but where one rule says one thing of many places, one line, its places
    shown as their groups' lines (core 2.15, the grouping `names`): a refusal naming a thousand beans names their
    groups. Each place is still named once, under the line, past the first few, with `DAFTAR_GATE_ALL=1`."""
    for rule, where, msg, n in grouped(found):
        print(f"{rule:<11} {where}: {msg}" + (f"   (× {n:,})" if n > 1 else ''))
    print(line + f" — {len(found)} error(s)")
    return 1 if found else 0


def grouped(found):
    """[(rule, where, what, how many)]: findings of one rule whose message is one but for the place it names, GROUPED
    or more, as one, its places in their lines; every other finding as it is, in the order found."""
    import re
    keyed, order = {}, []
    for rule, where, msg in found:
        stem = str(where).split(':', 1)[0].split()[0] if where else ''
        key = (rule, msg.replace(stem, '…') if stem and len(stem) > 3 else msg)
        if key not in keyed:
            keyed[key] = []
            order.append(key)
        keyed[key].append((where, msg))
    out = []
    for key in order:
        items = keyed[key]
        if len(items) < GROUPED or os.environ.get('DAFTAR_GATE_ALL'):
            out += [(key[0], w, m, 1) for w, m in items]
            continue
        try:
            from core import groupings
            gs = groupings.fit([(i, str(w), None) for i, (w, _m) in enumerate(items)], [], {})
            where = '; '.join(groupings.line(g, ['range', 'count', 'missing']) for g in
                              sorted(gs, key=lambda g: -len(g['members']))[:4]) + (' …' if len(gs) > 4 else '')
        except Exception:      # noqa: BLE001 — the gate never fails for want of a preview: the places, listed
            where = ', '.join(str(w) for w, _m in items[:6]) + ' …'
        out.append((key[0], where, re.sub(r'\s+', ' ', key[1]), len(items)))
    return out


def staged(root, as_json=False):
    """The index, judged as the commit would hold it (core/judge.py, the scope `staged`)."""
    scope = Scope.staged(root)
    found = judge(None, scope)
    if scope.unread is not None:
        print(f"form        index: {scope.unread}")
        return 1
    g = scope.garden
    line = "core check --staged" + (f": {len(g.beans)} beans, {sum(len(b.statements) for b in g.beans.values())} "
                                    f"statements" if g is not None else '')
    return verdict(found, line, as_json)


def verdict(found, line, as_json):
    """The verdict as the gate prints it (`report`), or with --json as one document: the findings and those words."""
    if not as_json:
        return report(found, line)
    import contextlib
    import io
    words = io.StringIO()
    with contextlib.redirect_stdout(words):
        code = report(found, line)
    print(json.dumps({'found': [list(f) for f in found], 'printed': words.getvalue()}, ensure_ascii=False))
    return code


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    as_json = '--json' in argv
    argv = [a for a in argv if a != '--json']
    if argv[:1] == ['--law']:
        from core.law import Law
        law = Law.load()
        return verdict(law.problems(), f"core law: {len(law.verbs)} verbs, {len(law.levels)} levels, {len(law.rules)} "
                                       f"rules", as_json)
    if argv[:1] == ['--staged']:
        top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        return staged(top.stdout.strip() if top.returncode == 0 else os.getcwd(), as_json)
    root = os.path.abspath(argv[0] if argv else '.')
    try:
        law = garden_law(root)
    except read.Unread as e:
        return verdict([('form', 'VOCAB.md', str(e))], "core check", as_json)
    scope = Scope.tree(root)
    found = judge(law, scope)
    n = sum(len(b.statements) for b in scope.garden.beans.values())
    return verdict(found, f"core check: {os.path.basename(root)}: {len(scope.garden.beans)} beans, {n} statements",
                   as_json)


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
