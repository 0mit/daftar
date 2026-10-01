#!/usr/bin/env python3
"""check — the gate: judges a garden by the law it runs, and refuses what breaks it.

    python3 bin/check.py [--all]          # the whole garden, as the working tree holds it
    python3 bin/check.py --staged         # what a commit would hold: the index (the pre-commit hook runs this)
    python3 bin/check.py --merge-commit   # a merge git commits itself (the pre-merge-commit hook runs this)
    python3 bin/check.py --law            # a garden of statements: the core's law alone, proved one law
    python3 bin/check.py <beans...> | -v  # a garden in today's words: what bin/dmcheck.py takes

(`python` on Windows; `python3 bin/daftar.py check` runs this too.) The law a garden runs is GARDEN.md's `extends`. A
garden that runs the core (`core@<version>`) is judged by the core's gate, core/check.py: its eighteen rules over the
statements, and at a commit the commit's own. A garden that runs today's language (`std-vocab@<version>`) is judged by
today's gate, bin/dmcheck.py, as it always was. With --staged and --merge-commit the pin is the index's, so the commit
that adopts the core is judged by the core.

A merge git commits itself runs the pre-merge-commit hook and not the pre-commit one. A garden of statements is judged
there too, since the gate covers what a merge makes (core/guide/MERGE.md §5); today's gate never judged such a merge,
and in a garden in today's words --merge-commit still judges nothing. bin/dmcheck.py stays whole until v1.0.0: it is
today's path."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import dmparse  # noqa: E402
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
    return p.startswith('core@')


def toplevel():
    r = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    return r.stdout.strip() if r.returncode == 0 else ROOT


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    staged = '--staged' in argv or '--merge-commit' in argv
    core = runs_core(pin(toplevel(), '') if staged else pin(ROOT))
    if '--merge-commit' in argv:
        if not core:
            return 0                     # today's gate never judged a merge git commits itself
        argv = ['--staged']
    if core:
        rest = [a for a in argv if a != '--all']
        if [a for a in rest if a not in ('--staged',) + CORE_ONLY] or len(rest) > 1:
            print(f"check: the core's gate judges a whole garden (`--all`, or nothing), the index (`--staged`) or the "
                  f"law (`--law`), and not {' '.join(rest)}: this garden runs the core ({pin(ROOT)})", file=sys.stderr)
            return 2
        return subprocess.run([sys.executable, os.path.join(ROOT, 'core', 'check.py')] + (rest or [ROOT])).returncode
    if [a for a in argv if a in CORE_ONLY]:
        print(f"check: {' '.join(a for a in argv if a in CORE_ONLY)} is the core's, and this garden runs "
              f"{pin(ROOT) or 'no pin'}: `python3 core/check.py --law` proves the core's law in any garden", file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, os.path.join(HERE, 'dmcheck.py'), *argv]).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
