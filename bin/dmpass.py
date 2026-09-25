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

ONE READER OF seed/LANGUAGE, TWO QUESTIONS. A line holding `<profile>` stands for one line per profile, and is read
here and nowhere else: `received` answers what a garden receives — the placeholder read as each profile the garden
extends that the law offers — and `kept` what the release keeps — read as every profile the law offers. Germination
copies what a garden receives; an upgrade copies it (`want`) and takes away what the garden held that it no longer
receives, out of what the release keeps (`have`); the keeper and the RULE-CHANGE duty read `kept`. So leaving a profile
takes its files away, an edit to one of them is a RULE-CHANGE, and a file of the garden's own beside them is never the
release's.

A FILE IN NO LAYER IS COUNTED AND SHOWN, never refused: the law cannot name every file a garden keeps, and a garden
that has not placed a file has not broken anything. It is the one place a flow cannot be judged from, so it is shown.

TWO MORE QUESTIONS OF A BEAN (24.0), answered here and by no copy: `sensitivity(fm, law)` — how much harm it can do a
person, derived from what it holds and never stored — and `may(actor, act, bean)` — whether a grant opens it, closed
by default.

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


# -- what a release ships: seed/LANGUAGE, read here and nowhere else
PLACE = '<profile>'           # in a line of seed/LANGUAGE: each profile a garden extends, and no other


def language(text):
    """The lines of a release's seed/LANGUAGE: one pattern a line, with comments and blank lines left out."""
    return _patterns(text)


def offered(law):
    """The profiles a law offers: the names under its `profiles`."""
    p = law.get('profiles') if isinstance(law, dict) else None
    return sorted(str(k) for k in p) if isinstance(p, dict) else []


def extended(vocab):
    """The profiles a garden's VOCAB.md extends (`extends_profiles`), as it states them."""
    p = vocab.get('extends_profiles') if isinstance(vocab, dict) else None
    return [str(x) for x in p] if isinstance(p, list) else []


def expand(lines, profiles):
    """The patterns the lines stand for: a line holding the placeholder once for each profile given, in order of name,
    and every other line as it is."""
    out = []
    for line in lines:
        out += [line.replace(PLACE, p) for p in sorted(set(profiles))] if PLACE in line else [line]
    return out


def _shipped(files, patterns):
    return sorted(f for f in files if any(matches(p, f) for p in patterns))


def received(files, lines, extends, offers):
    """The files, out of `files`, a garden receives from a release: the placeholder read as each profile it extends
    that the law offers."""
    return _shipped(files, expand(lines, set(extends) & set(offers)))


def kept(files, lines, offers):
    """The files, out of `files`, a release keeps: the placeholder read as every profile the law offers."""
    return _shipped(files, expand(lines, offers))


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
        self.language = expand(language(read(LANGUAGE)), offered(law))       # what the release keeps
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
        """'release' when a release keeps the file (`kept`: its `seed/LANGUAGE` matches it), else 'here': kept by this tree.
        Case by case on every platform, as the gate matches it: the keeper whose duty the gate applies is the one named here."""
        return 'release' if any(matches(p, path) for p in self.language) else 'here'

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


# ============================== WHO MAY SEE WHAT, AND HOW MUCH HARM IT CAN DO (24.0; step 1, N31) ==============================
# Two questions every reader asks of a bean, answered here and by no copy: how sensitive it is — DERIVED from what it
# holds, never stored — and whether an actor may read, write, act on or ratify it, read from the garden's `grants`.
LEVELS = ('none', 'personal', 'special-category')
POSITIONS_ALWAYS = ('title', 'summary', 'body')     # positions every bean has that no term declares


def _rank(level):
    return LEVELS.index(level) if level in LEVELS else 0


def gardener_of(root=ROOT):
    """The gardener GARDEN.md names, or None."""
    try:
        with open(os.path.join(root, 'GARDEN.md'), encoding='utf-8') as fh:
            g = _front(fh.read())
    except OSError:
        return None
    return g.get('gardener') if isinstance(g, dict) and isinstance(g.get('gardener'), str) else None


def _registry(law, name):
    r = law.registry(name) if hasattr(law, 'registry') else (law.get(name) if isinstance(law, dict) else None)
    return r if isinstance(r, list) else []


def _codes(node, path=''):
    """(path, scheme) of every code a front matter holds: a mapping that names a `scheme`, wherever it is."""
    if isinstance(node, dict):
        if isinstance(node.get('scheme'), str):
            yield path, node['scheme']
        for k, v in node.items():
            if path == '' and k == 'sensitivity':
                continue
            yield from _codes(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _codes(v, f"{path}[{i}]")


def derived_sensitivity(fm, law, gardener=None):
    """(level, why) as the law derives it from what the bean holds: SPECIAL-CATEGORY — a code of a scheme marked
    `sensitive: special-category`; PERSONAL — a record `about` a person who is not the gardener, or such a person's own
    bean. The whys name paths, never values."""
    gardener = gardener if gardener is not None else getattr(law, 'gardener', None)
    marked = {r.get('scheme') for r in _registry(law, 'knowledge_schemes')
              if isinstance(r, dict) and r.get('sensitive') == 'special-category'}
    special = [f"a code of {s} at {p}" for p, s in _codes(fm) if s in marked]
    if special:
        return 'special-category', special
    personal = [f"about {e['who']}, who is not the gardener" for e in (fm.get('about') or [] if isinstance(fm.get('about'), list) else [])
                if isinstance(e, dict) and isinstance(e.get('who'), str) and e['who'] != gardener]
    if fm.get('genos') == 'person' and fm.get('bean') != gardener:
        personal.append("the bean of a person who is not the gardener")
    return ('personal', personal) if personal else ('none', [])


def by_a_person(fm):
    """Whether the bean's own provenance says a person stated it (`asserted-by-human`)."""
    p = fm.get('provenance')
    return isinstance(p, dict) and p.get('src') == 'asserted-by-human'


def sensitivity(fm, law, gardener=None):
    """(level, why): the derived level, which a stated `sensitivity` raises — or lowers, on a person's own word only."""
    level, why = derived_sensitivity(fm, law, gardener)
    s = fm.get('sensitivity')
    if isinstance(s, dict) and s.get('is') in LEVELS:
        if _rank(s['is']) > _rank(level):
            return s['is'], why + [f"raised by a person: {s.get('why')}"]
        if _rank(s['is']) < _rank(level) and by_a_person(fm):
            return s['is'], [f"lowered on a person's own word: {s.get('why')}"] + why
    return level, why


class Answer(tuple):
    """(granted, why, grants, reason_asked) — `grants` the (holder, key) of every grant the answer read."""
    __slots__ = ()

    def __new__(cls, granted, why, grants=(), reason_asked=False):
        return tuple.__new__(cls, (bool(granted), why, list(grants), bool(reason_asked)))

    granted, why, grants, reason_asked = (property(lambda s, i=i: s[i]) for i in range(4))


def beans_here(root=ROOT):
    """{id: front matter} of every bean in the working tree."""
    out, d = {}, os.path.join(root, 'beans')
    for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
        if f.endswith('.md'):
            try:
                with open(os.path.join(d, f), encoding='utf-8') as fh:
                    fm = _front(fh.read())
            except (OSError, UnicodeDecodeError):
                fm = None
            if fm:
                out[str(fm.get('bean') or f[:-3])] = fm
    return out


def _covers(granted, asked):
    """Whether a grant's `positions` cover the positions asked: absent, every one; `x.*` every path under `x`."""
    if granted is None:
        return True
    paths = [e.get('path') for e in (granted if isinstance(granted, list) else [granted]) if isinstance(e, dict)]
    if asked is None:
        return False                      # the whole bean asked, and the grant opens part of it
    return all(any(a == p or a.startswith(p[:-1] if p.endswith('.*') else p + '.') for p in paths if isinstance(p, str))
               for a in asked)


def _day(x):
    import dmcal
    s = str(x).strip()
    try:
        return dmcal.moment(s).ms // dmcal.DAY_MS
    except Exception:
        return dmcal.to_day(s)


def _during(d, at):
    """Whether a grant's `during` holds on the day of `at` (today when absent). None where a bound is not read."""
    if not isinstance(d, dict):
        return True
    import time
    try:
        now = _day(at) if at else int(time.time() // 86400)
        lo = _day(d['from']) if d.get('from') is not None else None
        hi = _day(d['to']) if d.get('to') is not None else None
    except Exception:
        return None
    return (lo is None or lo <= now) and (hi is None or now <= hi)


def _select(holder, key, root):
    import dmreckon
    ref = key if ':' in str(key) else f"{holder}:{key}"
    try:
        return set(dmreckon.select(ref, root=root))
    except Exception:
        return None


def may(actor, act, bean, *, positions=None, at=None, reason=None, root=ROOT, beans=None, gardener=None):
    """Whether `actor` may `act` (read, write, act:<tool>, ratify:<class>) on `bean` — at `positions`, or the whole bean.
    CLOSED BY DEFAULT: the gardener is granted; nobody is granted what no grant opens. A grant counts when its holder may
    decide it — the gardener, the person the bean is of or `about`, an agreement — and it matches the act, holds the
    bean (`over`, or the bean holding it), covers the positions, names the actor and holds at `at`. A `forbidden` one
    refuses whatever a `permitted` one opens."""
    gardener = gardener if gardener is not None else gardener_of(root)
    if actor is None:
        return Answer(False, "nobody named: an actor no one can name is granted nothing")
    if actor == gardener:
        return Answer(True, f"{actor} is the gardener, who keeps the garden")
    beans = beans if beans is not None else beans_here(root)
    fm = beans.get(bean) or {}
    subjects = {e.get('who') for e in fm.get('about') or [] if isinstance(e, dict)} if isinstance(fm.get('about'), list) else set()
    if fm.get('genos') == 'person':
        subjects.add(bean)
    read, forbid, permit, notes = [], [], [], []
    for holder, hfm in sorted(beans.items()):
        gs = hfm.get('grants')
        if not isinstance(gs, dict):
            continue
        may_decide = holder == gardener or holder in subjects or hfm.get('genos') == 'contract'
        for key, g in sorted(gs.items()):
            if not isinstance(g, dict) or g.get('act') != act or not may_decide:
                continue
            over = {holder} if g.get('over') is None else _select(holder, g['over'], root)
            if over is None:
                notes.append(f"{holder}:grants[{key}] — its `over` could not be read, so it opens nothing")
                continue
            if bean not in over or not _covers(g.get('positions'), positions):
                continue
            aud = g.get('audience')
            aud = aud if isinstance(aud, list) else [aud] if isinstance(aud, dict) else []
            if not any(a.get('who') == actor or (a.get('selection') is not None and actor in (_select(holder, a['selection'], root) or ()))
                       for a in aud if isinstance(a, dict)):
                continue
            held = _during(g.get('during'), at)
            if held is None:
                notes.append(f"{holder}:grants[{key}] — its `during` is not read here, so it opens nothing")
            if not held:
                continue
            read.append((holder, key))
            (forbid if g.get('stance') == 'forbidden' else permit).append((holder, key, g))
    tail = ('; ' + '; '.join(notes)) if notes else ''
    if forbid:
        h, k, _g = forbid[0]
        return Answer(False, f"forbidden by {h}:grants[{k}], which no permitted grant passes" + tail, read)
    if permit:
        h, k, g = permit[0]
        asked = g.get('reason') == 'asked'
        if asked and not reason:
            return Answer(False, f"{h}:grants[{k}] opens it with a reason stated, and none was" + tail, read, True)
        return Answer(True, f"granted by {h}:grants[{k}]" + tail, read, asked)
    return Answer(False, f"no grant opens {act} on {bean}" + (f" at {', '.join(positions)}" if positions else '')
                  + " to " + actor + " — closed by default" + tail, read)


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
