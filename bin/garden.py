#!/usr/bin/env python3
"""garden — the one garden model: where a garden's documents are, and what each says, read once.

    python3 bin/garden.py                  # what this garden holds: its law, and each space with how many documents
    python3 bin/garden.py --paths [SPACE]  # every document's path, a space's or all, in the order every tool reads them

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
    documents(root, spaces)      -> [Doc]             Doc(path, space, id, fm, body, error): parsed by bin/parse.py
    document(path)               -> Doc               one, from the same cache

A document that does not parse is still given, with `fm` None and the reason in `error`: whether that is refused is the
gate's to say, never this reader's. It writes nothing, and opens no network path.

IN A GARDEN OF THE CORE (v1 part 6) the documents are where they were, and a bean is read by the engine (core/engine.py
`Garden.read`). A tool whose terms the core keeps whole in `details` until their part gives them a form — an analysis's
cache, a host's roots, an expiry — reads a bean through `terms(b)`: what `details` keeps, under today's names, with its
header, its locations (`be` as location) as `located_at`, and its names in `dns` or the hostname's namespace as the
anchors a host was known by. One view, built here, so no tool reads the core's beans its own way.

    runs_core(root)              -> bool              GARDEN.md pins the core (bin/check.py, the one reader of the pin)
    core_garden(root)            -> engine.Garden     the beans as the engine reads them, read once per process
    terms(b)                     -> dict              a bean of the core as today's terms that `details` keeps
"""
import collections
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import parse as dmparse  # noqa: E402 — the one front-matter splitter

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
    """One document, parsed by bin/parse.py — from the cache while its size and time are what they were."""
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


# ------------------------------------------------------------------------------------------------ a garden of the core
_CORE = {}
HOSTNAME = {'dns': 'fqdn', 'anchor-fqdn': 'fqdn', 'anchor-hostname': 'hostname'}   # the namespaces a machine's names
# are given in: DNS, where the name establishes, and the garden's own rows today's anchors became (core/translate.py
# `anchors_namespace`), where it only corroborates


def runs_core(root=ROOT):
    import check
    return check.runs_core(check.pin(root))


def core_garden(root=ROOT):
    if root not in _CORE:
        sys.path.insert(0, os.path.dirname(HERE))
        from core import engine
        _CORE[root] = engine.Garden.read(root)
    return _CORE[root]


_TABLES = {}


def law_tables(root=ROOT):
    """The tables the readers of a clause's days ask by today's names — `TERMS` (a clause's form and how it runs out,
    `clauses`), `UNITS`, `QUANTITIES` and `SYSTEMS` — from the law the garden at `root` runs, the core's (v1 part 13)."""
    if root not in _TABLES:
        sys.path.insert(0, os.path.dirname(HERE))
        from core import check as core_check, lines, measures
        L = core_check.garden_law(root, root if os.path.isfile(os.path.join(root, 'core', 'law', 'core.yaml')) else None)
        v = lines.law_view(L, root)
        _TABLES[root] = {'TERMS': {'clauses': measures.clause_term(L)}, 'UNITS': v.units, 'QUANTITIES': v.quantities,
                         'SYSTEMS': v.systems}
    return _TABLES[root]


def _split_position(text):
    """(system, the position as today's `at` wrote it) of a location: the tag a position carries dropped."""
    try:
        from core import frame, standards
        p = frame.read(text, standards.here().systems, None)
        return p.system, text[len(p.system) + 1:] if text.startswith(p.system + ':') else text
    except Exception:
        return None, text


def terms(b, beans=()):
    """A bean of the core as the terms `details` keeps under today's names — with its header (`bean` or `mapping`,
    `kind`, `title`, `summary`), each `be` as location as an entry of `located_at` (what `details.located_at` keeps of
    it beside, its host — a being of `beans` in its `at` — and its form, `placed`), each clause (`can`) as an entry of
    `clauses` (core/measures.py), and each name a namespace of a machine gives as an anchor (`identity.anchors`)."""
    sys.path.insert(0, os.path.dirname(HERE))
    from core import measures
    details = b.header.get('details') if isinstance(b.header.get('details'), dict) else {}
    v = {k: x for k, x in details.items() if k != 'located_at'}
    space = os.path.basename(os.path.dirname(b.path)) if b.path else 'beans'
    v['mapping' if space == 'mappings' else 'bean'] = b.id
    for k in ('kind', 'title', 'summary', 'tags'):
        if k in b.header:
            v[k] = b.header[k]
    kept = details.get('located_at') if isinstance(details.get('located_at'), dict) else {}
    located, anchors = [], []
    for e in details.get('located_at') if isinstance(details.get('located_at'), list) else []:
        located.append(e)                          # an entry no position was read from (`openness: unknown`), whole
    for _i, verb, r in b.items:
        if 'held' in r:
            continue
        if verb == 'be' and r.get('as') == 'location':
            for at in (r.get('at') if isinstance(r.get('at'), list) else [r.get('at')]):
                if isinstance(at, str) and '#' not in at and at not in beans:
                    system, pos = _split_position(at)
                    e = dict(kept.get(r.get('id')) or {}, at=pos, system=system, **measures.placed_of(r, ROOT, beans))
                    if 'note' in r:
                        e['note'] = r['note']
                    located.append(e)
        if verb == 'name' and r.get('by') in HOSTNAME and isinstance(r.get('as'), str):
            anchors.append({'key': HOSTNAME[r['by']], 'value': r['as']})
    if located:
        v['located_at'] = located
    clauses = measures.clauses_of(b, ROOT)
    if clauses:
        v['clauses'] = clauses
    v['identity'] = {'anchors': anchors}           # the names the core gives: what `details` kept of today's identity
    return v                                       # is read from `details` itself, never as a host's anchors


def main(argv):
    root = ROOT
    if not argv and runs_core(root):
        G = core_garden(root)
        sys.path.insert(0, os.path.dirname(HERE))
        from core.check import garden_law
        L = garden_law(root)
        unread = sum(1 for b in G.beans.values() if b.unread)
        print(f"{os.path.basename(os.path.abspath(root))}: the core, core@{L.version} — " + ', '.join(
            f"{len(paths(root, (s,)))} {s}" for s in SPACES)
            + f"; {sum(len(b.items) for b in G.beans.values())} statements" + (f", {unread} not read" if unread else ''))
        return 0
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
