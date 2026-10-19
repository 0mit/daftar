#!/usr/bin/env python3
"""check — judge a garden written in the core's statements, by the core's twenty-one rules.

    python3 core/check.py [<garden>]      # every bean of the garden at <garden> (here, if none is named)
    python3 core/check.py --staged        # what a commit would hold: the INDEX, and the commit's own rules
    python3 core/check.py --law           # the law alone: the face, the verbs' rows and the levels, proved together

(`python` on Windows.) The beans are `beans/**/*.md`, the zone the days are reckoned in is GARDEN.md's `zone`, and the
garden's own rows — kinds, levels, namespaces, flows, the layers' standing, verbs, rows added to a table — are VOCAB.md's
(core/law.py says which keys). Each finding is an error, printed as `<rule>  <where>: <what>`; the last line counts
them, and the exit status is 1 when there is one.

`--staged` is the commit's gate, run by bin/hooks/pre-commit through bin/check.py (bin/install.py installs it): every staged file
is copied out of the index into a temporary directory and judged there, with the law the commit stages, so what is
judged is what is committed; then the commit's own rules (core/commit.py): each changed bean named by the entry the
commit adds, its new statements known at that entry's moment, and a change to the law said to be a RULE-CHANGE. This
command is the gate bin/check.py runs."""
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import commit, engine, read, standards  # noqa: E402
from core.law import Law       # noqa: E402


def garden_law(root, release=None):
    """The law of the release at `release` (this one, if none), extended by the rows of the garden at `root` (its
    VOCAB.md, where it has one). The standards are the garden's where it carries a law (`standards.carried`): a scheme of
    codes it holds as its own is read there, as knowledge reads it."""
    p = os.path.join(root, 'VOCAB.md')
    ext = (('VOCAB.md', read.document(p)[0]),) if os.path.exists(p) else ()
    std = standards.here(root) if standards.carried(root) else None
    return Law.load(*ext, root=release, std=std)


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


def staged(root):
    """The index, judged as the commit would hold it."""
    snap = tempfile.mkdtemp(prefix='daftar-core-staged-')
    try:
        r = subprocess.run(['git', '-C', root, 'checkout-index', '--all', '--prefix=' + snap.replace(os.sep, '/') + '/'],
                           capture_output=True, text=True)
        if r.returncode != 0:
            print(f"form        index: the index could not be read — {r.stderr.strip()}")
            return 1
        release = snap if os.path.isfile(os.path.join(snap, 'core', 'law', 'core.yaml')) else None
        try:
            law = garden_law(snap, release)
        except read.Unread as e:
            return report([('form', 'VOCAB.md', str(e))], "core check --staged")
        garden = engine.Garden.read(snap)
        try:                       # THE GARDEN'S ID is its clone's: the copy of the index has no history to read it from
            garden.gid = engine.dmparse.garden_id(root)
        except Exception:
            garden.gid = None
        found = engine.judge(law, garden) + commit.findings(root, law, garden=garden)
        n = sum(len(b.statements) for b in garden.beans.values())
        return report(found, f"core check --staged: {len(garden.beans)} beans, {n} statements")
    finally:
        shutil.rmtree(snap, ignore_errors=True)


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    if argv[:1] == ['--law']:
        law = Law.load()
        return report(law.problems(), f"core law: {len(law.verbs)} verbs, {len(law.levels)} levels, {len(law.rules)} rules")
    if argv[:1] == ['--staged']:
        top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
        return staged(top.stdout.strip() if top.returncode == 0 else os.getcwd())
    root = os.path.abspath(argv[0] if argv else '.')
    try:
        law = garden_law(root)
    except read.Unread as e:
        return report([('form', 'VOCAB.md', str(e))], "core check")
    garden = engine.Garden.read(root)
    n = sum(len(b.statements) for b in garden.beans.values())
    return report(engine.judge(law, garden), f"core check: {os.path.basename(root)}: {len(garden.beans)} beans, {n} statements")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
