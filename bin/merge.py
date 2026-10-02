#!/usr/bin/env python3
"""merge — a bean merged by the statement merge (MERGE.md).

    python3 bin/merge.py --file <base> <ours> <theirs> [<path>]   # git's merge driver (%O %A %B %P): ours, in place
    python3 bin/merge.py <arguments>                               # by hand: core/merge.py's

(`python` on Windows; `python3 bin/daftar.py merge` runs this too.) `.gitattributes` sends `beans/*.md` and
`mappings/*.md` to the driver `daftar`, which bin/install.py configures to run this. git hands a driver three blobs of
one file and not three commits, so what each side is written in is read from the bean itself: in statements (its header
the core's: bean, kind, title, summary, tags, details, statements), the statement merge takes it (core/merge.py). A side
written in today's words — a branch made before its garden adopted the core, merged after — is refused, ours is left
as it was, and git leaves the bean for a person: it is merged once it is written in statements (bin/reform.py)."""
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


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__.strip())
        return 0
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
