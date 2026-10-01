#!/usr/bin/env python3
"""merge — a bean merged by the law it is written in: the statement merge, or today's semantic merge (MERGE.md).

    python3 bin/merge.py --file <base> <ours> <theirs> [<path>]   # git's merge driver (%O %A %B %P): ours, in place
    python3 bin/merge.py <arguments>                               # by hand: core/merge.py's, or bin/dmmerge.py's

(`python` on Windows; `python3 bin/daftar.py merge` runs this too.) `.gitattributes` sends `beans/*.md` and
`mappings/*.md` to the driver `daftar`, which bin/install.py configures to run this. git hands a driver three blobs of
one file and not three commits, so the law each side runs is read from the bean itself. Written in statements (its
header the core's: bean, kind, title, summary, tags, details, statements), it is the core's, and the statement merge
takes it (core/merge.py, core/guide/MERGE.md). Written in today's words, it is std-vocab's, and bin/dmmerge.py takes it
as it always has. Where the sides are not in one law — a branch made before its garden adopted the core, merged after —
the driver refuses, ours is left as it was, and git leaves the bean for a person. A bean that says neither (a header
and no statement) is merged by the garden's own law, GARDEN.md's `extends` at HEAD. bin/dmmerge.py stays whole until
v1.0.0: it is today's path."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
from core import read  # noqa: E402
from core.engine import HEADER  # noqa: E402
import check  # noqa: E402 — the one reader of a garden's pin
import dmparse  # noqa: E402


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


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
    if argv[:1] == ['--file'] and len(argv) >= 4:
        forms = {written_in(p) for p in argv[1:4]} - {None}
        if len(forms) > 1:
            what = argv[4] if len(argv) > 4 else os.path.basename(argv[2])
            print(f"merge: refusing to merge {what} — its sides are written in two laws, one in statements and one in "
                  f"today's words: a branch from before the garden adopted the core is merged after it is written in "
                  f"statements (core/translate.py). Ours is left as it was.", file=sys.stderr)
            return 1
        core = forms == {'core'} or (not forms and check.runs_core(check.pin(check.toplevel(), 'HEAD')))
    else:
        core = check.runs_core(check.pin(ROOT))
    tool = os.path.join(ROOT, 'core', 'merge.py') if core else os.path.join(HERE, 'dmmerge.py')
    return subprocess.run([sys.executable, tool, *argv]).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
