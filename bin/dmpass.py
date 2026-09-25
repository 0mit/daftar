#!/usr/bin/env python3
"""dmpass — where every file sits: the law's layer map, read once, for every tool that asks.

    python3 bin/dmpass.py --layers            # each layer with the files it holds, and the files in none
    python3 bin/dmpass.py --layers --json     # the same, for a tool
    python3 bin/dmpass.py <path> ...          # the layer and the keeper of each path

THE MAP IS LAW (manifesto: layers). The law's `layers` place what every garden has, and a garden places the rest with
`standing`, a list on any of its beans. A pattern is matched as a release's `seed/LANGUAGE` is matched — `*` crosses `/`
— and case by case on every platform; a doc with no `*`, `?` or `[` names one file, compared whole. A file the law
places, the law places: a garden's entry that says otherwise is the gate's to refuse, and this reads the law's placement
first. So is a file two of the law's rows hold, a file two of a garden's entries place in two layers, and a doc that is
not in the one form a path is written in here. This names each; the gate refuses them.

THE KEEPER IS ANOTHER AXIS. Whether a file came from a release is read from `seed/LANGUAGE`: it is what the release
keeps, and a change to it is a RULE-CHANGE whatever its layer. Every other file is kept here, by the tree that holds it.
A file in the law's `law` or `manifesto` layer carries the same duty, wherever it came from (`ruled`).

A FILE IN NO LAYER IS COUNTED AND SHOWN, never refused: the law cannot name every file a garden keeps, and a garden
that has not placed a file has not broken anything. It is the one place a flow cannot be judged from, so it is shown.

It reads the law at the one path it has, and refuses rather than guess when the law does not parse. It opens no
network path and writes nothing.
"""
import fnmatch, json, os, posixpath, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAW = 'seed/std-vocab.md'
LANGUAGE = 'seed/LANGUAGE'
DOCUMENTS = ('beans/', 'mappings/')
RULED = ('law', 'manifesto')            # the layers a change to which is a RULE-CHANGE, whoever keeps the file
_WILD = set('*?[')


def _front(text):
    fm = dmparse.split_front_matter(text or '')[0]
    if fm is None:
        return None
    try:
        d = dmparse.loads(fm)
    except Exception:
        return None
    return d if isinstance(d, dict) else None


def _patterns(text):
    return [l.strip() for l in (text or '').splitlines() if l.strip() and not l.lstrip().startswith('#')]


def _doc(entry):
    """`file:<path or pattern>` -> the path or pattern; anything else -> None."""
    d = entry.get('doc') if isinstance(entry, dict) else None
    return d[5:] if isinstance(d, str) and d.startswith('file:') else None


def _one(entry):
    """An entry that places: a mapping whose `standing` is one layer's name."""
    return isinstance(entry, dict) and isinstance(entry.get('standing'), str)


def matches(pattern, path):
    """A pattern with no `*`, `?` or `[` names one file, compared whole; any other is matched as seed/LANGUAGE's are,
    `*` crossing `/`, and case by case whatever the platform — a verdict must not change with the machine that gives it."""
    pattern = str(pattern)
    return pattern == path if not (_WILD & set(pattern)) else fnmatch.fnmatchcase(path, pattern)


def unwritten(doc):
    """Why a path or pattern is not in the one form a path is written in here, or '' when it is: relative, `/` between
    names, no `.` or `..` segment, no empty segment, no trailing `/` (a directory is `dir/*`)."""
    if not doc:
        return 'it is empty'
    if '\\' in doc:
        return 'a backslash: names are separated by `/`, on every platform'
    if doc.startswith('/'):
        return 'an absolute path: a doc is relative to the garden'
    if doc.endswith('/'):
        return 'a trailing `/`: a directory is written `dir/*`'
    if any(s in ('', '.', '..') for s in doc.split('/')):
        return 'an empty, `.` or `..` segment: write the path as ' + repr(posixpath.normpath(doc))
    return ''


class Map:
    """The layer map of one tree. `read(path) -> text or None` and `files` (the tree's paths, `/`-separated) are all it
    needs, so a tree at a git ref is read the same way as the working tree. `standing`, when given, is the list of
    (document, index, entry) a caller has already read — the gate has every bean parsed, and reading them twice costs
    as much as reading them once. AN ENTRY PLACES A FILE IN ONE LAYER, NAMED: one whose `standing` is not one name (a
    list a merge left, a record) places nothing here, and the term refuses it by name — read as a layer, it would be a
    layer no row has, and every reader that files a path under its layer would fail on it."""

    def __init__(self, read, files, standing=None):
        self.files = sorted(set(files))
        law = _front(read(LAW))
        if law is None:
            raise ValueError(f"{LAW} is not there or does not parse: there is no map without the law")
        self.version = str(law.get('version'))
        self.rows = [r for r in (law.get('layers') or []) if isinstance(r, dict) and isinstance(r.get('layer'), str)]
        self.layers = {r['layer']: r for r in self.rows}
        self.journal_path = law['journal'].get('path') if isinstance(law.get('journal'), dict) else None
        self.language = _patterns(read(LANGUAGE))
        if standing is not None:
            self.standing = [(f, i, e) for f, i, e in standing if _one(e)]
        else:
            self.standing = []
            for f in self.files:
                if f.startswith(DOCUMENTS) and f.endswith('.md'):
                    for i, e in enumerate((_front(read(f)) or {}).get('standing') or []):
                        if _one(e):
                            self.standing.append((f, i, e))

    @classmethod
    def here(cls, root=ROOT, standing=None):
        def read(p):
            try:
                with open(os.path.join(root, *p.split('/')), encoding='utf-8') as fh:
                    return fh.read()
            except (OSError, UnicodeDecodeError):
                return None
        return cls(read, tracked(root), standing)

    # -- the law's own placement
    def _holds(self, row):
        h = row.get('holds')
        return [p for p in h if isinstance(p, str)] if isinstance(h, list) else []

    def law_layers_of(self, path):
        """Every law row whose `holds` matches the path — more than one is the gate's to refuse."""
        return [r['layer'] for r in self.rows for p in self._holds(r) if matches(p, path)]

    def law_layer_of(self, path):
        hit = self.law_layers_of(path)
        return hit[0] if hit else None

    def garden_layers_of(self, path):
        """[(layer, document, index)] for every `standing` entry whose doc matches the path."""
        return [(e.get('standing'), f, i) for f, i, e in self.standing
                if _doc(e) is not None and matches(_doc(e), path)]

    def layer_of(self, path):
        """(layer, who placed it) — the law first, then the garden; (None, None) for a file in no layer. Where a
        garden's entries disagree the gate refuses (garden_overlaps); until then the first entry is read."""
        law = self.law_layer_of(path)
        if law:
            return law, 'law'
        for layer, f, _i in self.garden_layers_of(path):
            return layer, f
        return None, None

    def keeper_of(self, path):
        """'release' when a release ships the file (its `seed/LANGUAGE` matches it), else 'here': kept by this tree.
        Case by case on every platform, as the gate matches it: the keeper whose duty the gate applies is the one named here."""
        return 'release' if any(fnmatch.fnmatchcase(path, p) for p in self.language) else 'here'

    def ruled(self):
        """The files a change to which is a RULE-CHANGE by their layer: those the law or a garden places in `law` or
        `manifesto`. (What a release ships carries the duty by its keeper, read from `seed/LANGUAGE`, besides.)"""
        return {f for f in self.files if self.layer_of(f)[0] in RULED}

    # -- what the gate refuses, as data
    def law_problems(self):
        """[text] — the law's map is malformed: a row whose `holds` is not a list of text, a row that holds files and
        says it holds none, a layer named twice, a `beneath` that names no row, or a chain with no top, two tops, or a
        loop. The gate refuses each, before any file is judged by a map it cannot read."""
        out, seen = [], set()
        for r in self.rows:
            n = r['layer']
            if n in seen:
                out.append(f"`{n}` is named by two rows")
            seen.add(n)
            h = r.get('holds')
            if h is not None and not (isinstance(h, list) and all(isinstance(p, str) and p for p in h)):
                out.append(f"`{n}`'s holds is not a list of patterns: {h!r}")
            if h and not r.get('files'):
                out.append(f"`{n}` holds files and is marked `files: false`")
            for p in self._holds(r):
                why = unwritten(p)
                if why:
                    out.append(f"`{n}` holds {p!r}: {why}")
            b = r.get('beneath')
            if b is not None and b not in self.layers:
                out.append(f"`{n}` stands on `{b}`, which is no row")
        try:
            self.chain()
        except ValueError as e:
            out.append(str(e))
        return out

    def law_overlaps(self):
        """[(path, [layer, ...])] — a file two of the law's rows hold."""
        out = []
        for f in self.files:
            hit = sorted(set(self.law_layers_of(f)))
            if len(hit) > 1:
                out.append((f, hit))
        return out

    def garden_overlaps(self):
        """[(path, [(layer, document, index), ...])] — a file the law does not place that a garden's entries place in two
        or more layers: which one it sits in would depend on the order the entries were read in."""
        out = []
        for f in self.files:
            if self.law_layer_of(f):
                continue
            hit = self.garden_layers_of(f)
            if len({h[0] for h in hit}) > 1:
                out.append((f, hit))
        return out

    def standing_conflicts(self):
        """[(document, index, doc, garden's layer, law's layer, path)] — a garden entry that places a file the law places
        elsewhere. A pattern entry conflicts through any file it matches; an entry that matches no file conflicts only
        where its doc is itself a path the law places."""
        out = []
        for f, i, e in self.standing:
            doc, mine = _doc(e), e.get('standing')
            if doc is None or not mine:
                continue
            for p in [p for p in self.files if matches(doc, p)] or [doc]:
                law = self.law_layer_of(p)
                if law and law != mine:
                    out.append((f, i, 'file:' + doc, mine, law, p))
                    break
        return out

    def doc_problems(self):
        """[(document, index, doc, why)] — a doc not in the one form a path is written in, or one that names a single
        file this tree does not hold (a mistyped name places nothing, and says nothing about it)."""
        out = []
        for f, i, e in self.standing:
            doc = _doc(e)
            if doc is None:
                continue
            why = unwritten(doc)
            if not why and not (_WILD & set(doc)) and doc not in self.files:
                why = 'no file of this garden has that name'
            if why:
                out.append((f, i, 'file:' + doc, why))
        return out

    def chain(self):
        """The layers that stand one on another, top first: from the one row no row names `beneath`, down its links.
        Raises ValueError when there is no such row, or more than one, or the links loop."""
        linked = [r for r in self.rows if r.get('beneath')]
        if not linked:
            return []
        named = {r.get('beneath') for r in linked}
        tops = [r['layer'] for r in linked if r['layer'] not in named]
        if len(tops) != 1:
            raise ValueError(f"the chain of `beneath` has {len(tops)} tops ({', '.join(tops) or 'none: it loops'}), "
                             f"where one layer stands above the rest")
        out, at = [], tops[0]
        while at:
            if at in out:
                raise ValueError(f"the chain of `beneath` loops at `{at}`")
            out.append(at)
            at = (self.layers.get(at) or {}).get('beneath')
        return out

    def placed(self):
        """{layer: [path]} and [path in no layer], over the tree's files."""
        by, none = {r['layer']: [] for r in self.rows}, []
        for f in self.files:
            layer, _who = self.layer_of(f)
            (by.setdefault(layer, []) if layer else none).append(f)
        return by, none


def tracked(root=ROOT):
    """The tree's files: what git tracks and what it would track (not ignored), when `root` is the top of its own
    repository; else every file under it, `.git` left out. A garden copied without its `.git` into another repository is
    still read as itself."""
    try:
        top = subprocess.run(['git', '-C', root, 'rev-parse', '--show-toplevel'], capture_output=True, timeout=30)
        if top.returncode == 0 and os.path.realpath(top.stdout.decode('utf-8', 'replace').strip()) == os.path.realpath(root):
            r = subprocess.run(['git', '-C', root, 'ls-files', '--cached', '--others', '--exclude-standard', '-z'],
                               capture_output=True, timeout=30)
            if r.returncode == 0:
                return sorted({p for p in r.stdout.decode('utf-8', 'replace').split('\0') if p})
    except (OSError, subprocess.SubprocessError):
        pass
    return sorted(os.path.relpath(os.path.join(d, f), root).replace(os.sep, '/')
                  for d, _s, fs in os.walk(root) if '.git' not in d.split(os.sep) for f in fs)


def _kept(m, p):
    return 'by the release' if m.keeper_of(p) == 'release' else 'here'


def main(argv):
    try:
        m = Map.here()
    except ValueError as e:
        print(f"dmpass: {e}", file=sys.stderr)
        return 2
    try:
        chain, broken = m.chain(), None
    except ValueError as e:
        chain, broken = None, str(e)
    if '--layers' in argv:
        by, none = m.placed()
        if '--json' in argv:
            print(json.dumps({'version': m.version, 'chain': chain, 'chain_broken': broken,
                              'placed_twice': {p: [h[0] for h in hit] for p, hit in m.garden_overlaps()},
                              'layers': {k: [{'path': p, 'kept': m.keeper_of(p), 'placed_by': m.layer_of(p)[1]}
                                             for p in v] for k, v in by.items()},
                              'in_no_layer': none}, ensure_ascii=False, indent=1))
            return 0
        print(f"the layer map of std-vocab {m.version}: "
              + (f"{' > '.join(chain)}, and beside them the rest" if chain is not None else f"NO CHAIN — {broken}"))
        twice = dict(m.garden_overlaps())
        for name in list(m.layers) + [k for k in by if k not in m.layers]:
            r, fs = m.layers.get(name) or {}, by.get(name) or []
            kind = '' if r.get('files', True) else '  (no file: a place material comes from or goes to)'
            print(f"\n{name}: {len(fs)}{kind}{'' if name in m.layers else '  (no row of the law names it)'}")
            for p in fs:
                who = m.layer_of(p)[1]
                print(f"  {p}  [kept {_kept(m, p)}{'' if who == 'law' else ', placed by ' + who}]"
                      + (f"  PLACED IN {len({h[0] for h in twice[p]})} LAYERS by the garden — the gate refuses it"
                         if p in twice else ''))
        print(f"\nin no layer: {len(none)} — shown, never refused; a garden places what it keeps with `standing`")
        for p in none:
            print(f"  {p}  [kept {_kept(m, p)}]")
        return 0
    paths = [a for a in argv if not a.startswith('-')]
    if not paths:
        print(__doc__.split('\n\n')[1])
        return 0
    for a in paths:
        # A PATH IS READ WHERE THE PERSON STANDS: `./MODEL.md`, an absolute path, or one given from a subdirectory
        # names the same file of the tree; one outside the tree is said to be so, never placed.
        try:
            p = os.path.relpath(os.path.realpath(a), os.path.realpath(ROOT)).replace(os.sep, '/')
        except ValueError:                  # another drive: no path from here to there
            p = '..'
        if p == '..' or p.startswith('../'):
            print(f"{a}: outside this tree ({ROOT})")
            continue
        layer, who = m.layer_of(p)
        hit = {h[0] for h in m.garden_layers_of(p)} if who not in (None, 'law') else set()
        print(f"{p}: {layer or 'in no layer'}{'' if who in (None, 'law') else ' (placed by ' + who + ')'}, kept {_kept(m, p)}"
              + (f" — AND in {', '.join(sorted(hit - {layer}))} by another entry: the gate refuses a file placed twice"
                 if len(hit) > 1 else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
