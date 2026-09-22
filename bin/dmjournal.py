#!/usr/bin/env python3
"""dmjournal — append a journal entry whose heading is read from the clock, never typed.

    python3 bin/dmjournal.py "<who>" "<what>" < entry.md      # the body on standard input
    python3 bin/dmjournal.py "<who>" "<what>" --body "- action: …"

The heading is `## <when> · <who> · <what>`, and <when> is the position in time the gate accepts — to the
minute, with its offset — read from this machine's clock at the moment of writing. A heading typed by hand
is a moment remembered rather than measured, and twice in one evening a writer typed the time before reading
it. The gate checks the FORM of a heading; only the clock can supply its truth, so the clock supplies it.

The body is appended as given. It is not checked here: the gate checks that it names each bean the commit
changes, that it says RULE-CHANGE where the law moved, and that no `(fill in` is left. Nothing is committed.

HOW THIS IS ENFORCED (std-vocab 20.0, `journal.heading: stamped`). Every heading this tool writes is also
recorded in the clone's git directory (`.git/daftar/journal-stamps`), and the gate refuses a heading a commit
adds that is not recorded there. The gate cannot tell a measured moment from a remembered one by looking at
it; it can tell whether the clock-reading tool wrote it. The register is per clone and never versioned: it
proves only that THIS clone's tool stamped the heading, which is all a pre-commit hook can honestly check.
"""
import datetime
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JOURNAL = os.path.join(ROOT, 'log', 'journal.md')


def stamps_path(root=ROOT):
    """The register, in the git directory every worktree of this clone shares."""
    r = subprocess.run(['git', '-C', root, 'rev-parse', '--git-common-dir'], capture_output=True, text=True)
    gd = r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else '.git'
    if not os.path.isabs(gd):
        gd = os.path.join(root, gd)
    return os.path.join(gd, 'daftar', 'journal-stamps')


def register(h, root=ROOT):
    p = stamps_path(root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'a', encoding='utf-8') as fh:
        fh.write(h + '\n')


def registered(root=ROOT):
    p = stamps_path(root)
    if not os.path.exists(p):
        return set()
    return {l.rstrip('\n') for l in open(p, encoding='utf-8')}


def heading(who, what, when=None):
    """The heading form (std-vocab 10.0): `## YYYY-MM-DD HH:MM+HH:MM · who · what`."""
    when = when or datetime.datetime.now().astimezone()
    return f"## {when.isoformat(timespec='minutes').replace('T', ' ')} · {who} · {what}"


def stamp(who, what, root=ROOT):
    """A heading read from the clock and registered, for a tool that appends its own body (dmupgrade)."""
    h = heading(who, what)
    register(h, root)
    return h


def append(who, what, body):
    body = body.rstrip('\n')
    if not body.strip():
        raise SystemExit("dmjournal: the entry has no body — what was done, and why, is the point of it")
    if '\n## ' in '\n' + body:
        raise SystemExit("dmjournal: the body contains a `## ` heading of its own — one entry per call")
    text = open(JOURNAL, encoding='utf-8').read()
    h = stamp(who, what)
    entry = ('' if text.endswith('\n\n') else ('\n' if text.endswith('\n') else '\n\n')) + h + '\n' + body + '\n'
    with open(JOURNAL, 'a', encoding='utf-8') as fh:
        fh.write(entry)
    return h


def main(argv):
    if len(argv) < 2 or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv and argv[0] in ('-h', '--help') else 2
    who, what = argv[0], argv[1]
    if '--body' in argv:
        body = argv[argv.index('--body') + 1]
    else:
        body = sys.stdin.read()
    if not os.path.exists(JOURNAL):
        raise SystemExit(f"dmjournal: no {os.path.relpath(JOURNAL, ROOT)} — is this a garden?")
    print(append(who, what, body))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
