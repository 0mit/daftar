#!/usr/bin/env python3
"""merge — a bean merged by the statement merge (MERGE.md).

    python3 bin/merge.py --file <base> <ours> <theirs> [<path>]   # git's merge driver (%O %A %B %P): ours, in place
    python3 bin/merge.py <arguments>                               # by hand: core/merge.py's

(`python` on Windows; `python3 bin/daftar.py merge` runs this too.) `.gitattributes` sends `beans/*.md` and
`mappings/*.md` to the driver `daftar`, which bin/install.py configures to run this. git hands a driver three blobs of
one file and not three commits, so what each side is written in is read from the bean itself: in statements (its header
the core's: bean, kind, title, summary, tags, details, statements), the statement merge takes it (core/merge.py). A side
written in today's words — a branch made before its garden adopted the core, merged after — is refused, ours is left
as it was, and git leaves the bean for a person: it is merged once it is written in statements (bin/reform.py).

THE TWO LOGS, log/journal.md and log/pending.md, are lists of entries, each from its `## ` heading to the next, and
are merged here entry by entry, never line by line: every entry of ours stays where it was, and each entry only
theirs holds is appended after them, in their order, whole. An entry one side changed (only the queue changes one)
comes through changed; one both sides changed apart, or one side removed and the other changed, is a conflict for a
person: both versions are kept side by side between git's markers, and git leaves the file to them. git's line union,
which these files were merged with, keeps a line both sides' additions share once — two items parked apart, each
ending `- status: proposed`, kept that line once (2026-10-09)."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from core import read  # noqa: E402
from core.engine import HEADER  # noqa: E402
import parse as dmparse  # noqa: E402


def written_in(path):
    """'core' for a bean in statements, 'today' for one in today's words, None for one that says neither, or no bean."""
    try:
        with open(path, encoding='utf-8') as fh:
            head = dmparse.split_front_matter(fh.read().replace('\r\n', '\n'))[0]
        fm = read.loads(head) if head is not None else None
    except (OSError, UnicodeDecodeError, read.Unread):
        return None
    if not isinstance(fm, dict) or not fm:
        return None
    if any(k not in HEADER for k in fm):
        return 'today'
    return 'core' if 'statements' in fm else None


LOGS = ('log/journal.md', 'log/pending.md')


def entries(text):
    """(what stands before the first entry, [(heading, entry)]): an entry runs from its `## ` heading to the next."""
    pre, out = [], []
    for ln in text.splitlines(keepends=True):
        if ln.startswith('## '):
            out.append([ln])
        elif out:
            out[-1].append(ln)
        else:
            pre.append(ln)
    seen, keyed = {}, []
    for e in out:                       # a heading written twice is two entries: the second keyed by its place
        h = e[0].rstrip('\r\n')
        seen[h] = seen.get(h, 0) + 1
        keyed.append(((h, seen[h]), ''.join(e)))
    return ''.join(pre), keyed


def merge_log(base, ours, theirs):
    """(the merged text, how many conflicts): `ours`' entries in their places, as written; those only `theirs` holds
    appended after them, whole, a blank line before each."""
    same = lambda a, b: (a or '').rstrip() == (b or '').rstrip()
    end = lambda s: s if not s or s.endswith('\n') else s + '\n'
    (bp, be), (op, oe), (tp, te) = entries(base), entries(ours), entries(theirs)
    B, O, T = dict(be), dict(oe), dict(te)
    conflicts = 0

    def three(b, o, t):
        """One entry, three ways: what changed on one side; the two side by side where both changed it apart."""
        nonlocal conflicts
        if same(o, t) or same(t, b):
            return o, False
        if same(o, b):
            return t, False
        conflicts += 1
        return f"<<<<<<< ours\n{end(o or '')}=======\n{end(t or '')}>>>>>>> theirs\n", True
    parts = [three(bp, op, tp)]                  # (text, set apart): a part set apart has a blank line before it
    for k, o in oe:
        if k in T:
            parts.append(three(B.get(k), o, T[k]))
        elif k in B and not same(o, B[k]):       # theirs took out what ours changed
            parts.append(three(B[k], o, ''))
        elif k not in B:                         # ours alone added it
            parts.append((o, False))
        # in base, unchanged by ours, taken out by theirs: it goes
    for k, t in te:
        if k in O:
            continue
        if k in B:
            if not same(t, B[k]):                # ours took out what theirs changed
                parts.append(three(B[k], '', t))
            continue
        parts.append((t, True))                  # theirs alone added it
    text = ''
    for part, apart in parts:
        if part and (apart or part.startswith('<<<<<<<')) and text:
            text = end(text)
            text += '' if text.endswith('\n\n') else '\n'
        text += part
    return text, conflicts


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    if argv[:1] == ['--file'] and len(argv) >= 5 and argv[4].replace('\\', '/') in LOGS:
        texts = []
        for p in argv[1:4]:
            with open(p, encoding='utf-8', newline='') as fh:
                texts.append(fh.read())
        merged, conflicts = merge_log(*texts)
        with open(argv[2], 'w', encoding='utf-8', newline='') as fh:
            fh.write(merged)
        if conflicts:
            print(f"merge: {argv[4]}: {conflicts} entr{'y' if conflicts == 1 else 'ies'} both sides changed apart, kept "
                  f"side by side for a person", file=sys.stderr)
        return 1 if conflicts else 0
    if argv[:1] == ['--file'] and len(argv) >= 4 and 'today' in {written_in(p) for p in argv[1:4]}:
        what = argv[4] if len(argv) > 4 else os.path.basename(argv[2])
        print(f"merge: refusing to merge {what} — a side is written in today's words: a branch from before the garden "
              f"adopted the core is merged after it is written in statements (`python3 bin/reform.py <bean>`). Ours is "
              f"left as it was.", file=sys.stderr)
        return 1
    tool = os.path.join(ROOT, 'core', 'merge.py')
    return subprocess.run([sys.executable, tool, *argv]).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
