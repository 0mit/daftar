#!/usr/bin/env python3
"""dmgarden — the one garden model: where a garden's documents are, and what each says, read once.

    python3 bin/dmgarden.py                  # what this garden holds: its law, and each space with how many documents
    python3 bin/dmgarden.py --paths [SPACE]  # every document's path, a space's or all, in the order every tool reads them

(`python` on Windows.) A garden's documents live in its SPACES — `beans/` and `mappings/`, each one file per document,
`<id>.md`. Every tool that reads them asks this module for them, so they are listed in one order, by one rule, and a
document is parsed once per process however many tools of it ask: a tool that listed them itself once read a file the
others skipped, and a second reader of front matter is a reader that can disagree with the gate.

WHAT IT GIVES:
    paths(root, spaces)          -> [absolute path]   the working tree: sorted within a space, the spaces in the order
                                                      asked, a name beginning with a dot left out, as a glob leaves it
    listed(root, spaces, at)     -> ['<space>/<id>.md'] as git holds them: `at='index'` what is staged, or a commit's
    untracked(root, spaces)      -> ['<space>/<id>.md'] new documents git does not track yet, ignored ones left out
    ids(root, space)             -> [id]              each document's id, its file name without `.md`
    documents(root, spaces)      -> [Doc]             Doc(path, space, id, fm, body, error): parsed by bin/dmparse.py
    document(path)               -> Doc               one, from the same cache

A document that does not parse is still given, with `fm` None and the reason in `error`: whether that is refused is the
gate's to say, never this reader's. It writes nothing, and opens no network path.
"""
import collections
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse  # noqa: E402 — the one front-matter splitter

ROOT = os.path.dirname(HERE)
SPACES = ('beans', 'mappings')

Doc = collections.namedtuple('Doc', 'path space id fm body error')
_CACHE = {}                 # absolute path -> ((mtime_ns, size), Doc): a document read again only when it changed


def paths(root=ROOT, spaces=SPACES):
    """Every document of the spaces asked, `<space>/<id>.md`: sorted by name within a space, the spaces in order."""
    spaces = (spaces,) if isinstance(spaces, str) else spaces
    out = []
    for space in spaces:
        d = os.path.join(root, space)
        try:
            names = sorted(n for n in os.listdir(d) if n.endswith('.md') and not n.startswith('.')
                           and os.path.isfile(os.path.join(d, n)))
        except OSError:
            continue
        out += [os.path.join(d, n) for n in names]
    return out


def _git(root, *args):
    r = subprocess.run(['git', '-C', root, *args], capture_output=True, env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    return r.stdout.decode('utf-8', 'replace') if r.returncode == 0 else ''


def _documents_of(names, spaces):
    """The documents among git's names: `<space>/<id>.md`, directly in one of the spaces asked, in the spaces' order."""
    out = []
    for space in spaces:
        out += sorted(n for n in names if n.startswith(space + '/') and n.endswith('.md') and n.count('/') == 1)
    return out


def listed(root=ROOT, spaces=SPACES, at='index'):
    """The documents as git holds them: staged (`at='index'`), or at a commit. `<space>/<id>.md`, forward slashes."""
    spaces = (spaces,) if isinstance(spaces, str) else tuple(spaces)
    if at == 'index':
        names = _git(root, 'ls-files', '-z', '--', *spaces).split('\0')
    else:
        names = _git(root, 'ls-tree', '-r', '-z', '--name-only', at, '--', *spaces).split('\0')
    return _documents_of([n for n in names if n], spaces)


def untracked(root=ROOT, spaces=SPACES):
    """The documents git does not track yet, what it ignores left out: `<space>/<id>.md`."""
    spaces = (spaces,) if isinstance(spaces, str) else tuple(spaces)
    names = _git(root, 'ls-files', '-z', '--others', '--exclude-standard', '--', *spaces).split('\0')
    return _documents_of([n for n in names if n], spaces)


def ids(root=ROOT, space='beans'):
    return [os.path.basename(p)[:-3] for p in paths(root, (space,))]


def document(path):
    """One document, parsed by bin/dmparse.py — from the cache while its size and time are what they were."""
    path = os.path.abspath(path)
    try:
        st = os.stat(path)
        stamp = (st.st_mtime_ns, st.st_size)
    except OSError as e:
        return Doc(path, os.path.basename(os.path.dirname(path)), os.path.basename(path)[:-3], None, '', str(e))
    hit = _CACHE.get(path)
    if hit and hit[0] == stamp:
        return hit[1]
    fm, body, err = None, '', None
    try:
        head, body = dmparse.read(path)
        fm = dmparse.loads(head) if head else None
    except Exception as e:                  # the gate names what is wrong with it; a reader only says it could not
        err = str(e)
    doc = Doc(path, os.path.basename(os.path.dirname(path)), os.path.basename(path)[:-3], fm, body or '', err)
    _CACHE[path] = (stamp, doc)
    return doc


def documents(root=ROOT, spaces=SPACES):
    return [document(p) for p in paths(root, spaces)]


def main(argv):
    root = ROOT
    if argv[:1] == ['--paths']:
        for p in paths(root, tuple(argv[1:]) or SPACES):
            print(os.path.relpath(p, root).replace(os.sep, '/'))
        return 0
    if argv:
        print(__doc__.split('\n\n')[1].strip(), file=sys.stderr)
        return 2
    print(f"{os.path.basename(os.path.abspath(root))}: " + ', '.join(
        f"{len(paths(root, (s,)))} {s}" for s in SPACES))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
