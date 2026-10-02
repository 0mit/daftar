#!/usr/bin/env python3
"""check — the gate: judges a garden by the core's law, and refuses what breaks it.

    python3 bin/check.py [--all]          # the whole garden, as the working tree holds it
    python3 bin/check.py --staged         # what a commit would hold: the index (the pre-commit hook runs this)
    python3 bin/check.py --merge-commit   # a merge git commits itself (the pre-merge-commit hook runs this)
    python3 bin/check.py --law            # the core's law alone, proved one law (a release's own tree too)

(`python` on Windows; `python3 bin/daftar.py check` runs this too.) The law a garden runs is GARDEN.md's `extends`,
`core@<version>`, and the gate is the core's, core/check.py: its rules over the statements, and at a commit the commit's
own. With --staged and --merge-commit the pin is the index's, so the commit that adopts the core is judged by the core.
A merge git commits itself runs the pre-merge-commit hook and not the pre-commit one, and is judged there too, since the
gate covers what a merge makes (MERGE.md §5).

A garden in today's words (`std-vocab@<version>`) is not judged here: it runs its own copy of today's gate until it
adopts the core (`bin/dmupgrade.py <a release of the core>`, v1 part 13)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402
try:
    from core import read  # noqa: E402 — every value read as written (core spec §2)
    _loads, _unread = read.loads, read.Unread
except ImportError:        # a tree that carries no core/ runs today's law alone, and its pin is read all the same
    _loads, _unread = dmparse.loads, Exception

CORE_ONLY = ('--law',)


def pin(root, ref=None):
    """GARDEN.md's `extends`: in the working tree (ref None), at a commit (`HEAD`), or in the index (''); '' where none."""
    if ref is None:
        p = os.path.join(root, 'GARDEN.md')
        try:
            with open(p, encoding='utf-8') as fh:
                text = fh.read()
        except OSError:
            return ''
    else:
        r = subprocess.run(['git', '-C', root, 'show', f"{ref}:GARDEN.md"], capture_output=True)
        if r.returncode != 0:
            return ''
        text = r.stdout.decode('utf-8', 'replace')
    try:
        fm = _loads(dmparse.split_front_matter(text)[0] or '') or {}
    except _unread:
        return ''
    return str(fm.get('extends') or '') if isinstance(fm, dict) else ''


def runs_core(p):
    """True but for a garden in today's words (`std-vocab@…`): a garden of the core, and a release's own tree, which pins
    nothing and carries the core's law (v1 part 13). No tool of this release reads today's words: such a garden adopts
    the core first (bin/dmupgrade.py), and its own copy of today's tools runs until it has."""
    return not p.startswith('std-vocab@')


def toplevel():
    r = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    return r.stdout.strip() if r.returncode == 0 else ROOT


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    staged = '--staged' in argv or '--merge-commit' in argv
    p = pin(toplevel(), '') if staged else pin(ROOT)
    if not runs_core(p):
        print(f"check: this garden runs today's words ({p}), and this release's gate judges the core's statements: adopt "
              f"the core first (`python3 bin/dmupgrade.py <a release of the core>`); until then its own gate judges it",
              file=sys.stderr)
        return 2
    if '--merge-commit' in argv:
        argv = ['--staged']
    rest = [a for a in argv if a != '--all']
    if [a for a in rest if a not in ('--staged',) + CORE_ONLY] or len(rest) > 1:
        print(f"check: the core's gate judges a whole garden (`--all`, or nothing), the index (`--staged`) or the law "
              f"(`--law`), and not {' '.join(rest)}", file=sys.stderr)
        return 2
    if not p and rest != ['--law']:
        print("check: no GARDEN.md here pins a law: the gate judges a garden (`--law` proves this release's law)",
              file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, os.path.join(ROOT, 'core', 'check.py')] + (rest or [ROOT])).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
