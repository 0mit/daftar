#!/usr/bin/env python3
"""dmpass — where every file sits: the law's layer map, read once, for every tool that asks.

    python3 bin/dmpass.py --layers            # each layer with the files it holds, and the files in none
    python3 bin/dmpass.py --layers --json     # the same, for a tool
    python3 bin/dmpass.py <path> ...          # the layer and the keeper of each path
    python3 bin/dmpass.py --flows [--json]    # each row of the flow law, and how far it is guarded

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

AND THE FLOW LAW (24.0): `Flows.decide(from, to, method)` — whether a pass is granted, closed by default —
and `--flows`, each row with its guard, computed from the `GUARDS` the tools declare and the hooks that run them.

AND LEG 2 (24.0): `trace` — where a said value the save is about to commit came from, through every relay to its
terminal source — and `denied_lines`/`post_hits`, POST's look at a tool's output by content. They judge what they are
handed; the launcher and the hook keep the material.

It reads the law at the one path it has, and refuses rather than guess when the law does not parse. It opens no
network path and writes nothing.
"""
import fnmatch, json, os, posixpath, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmgarden  # noqa: E402 — the one garden model: where its documents are
import dmform   # the one reader of how the law spells an attribute

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


# ============================== WHERE A VALUE COMES FROM (24.0; the Leviathan's Body 2; sources by nature) ==============================
# Every position has ONE origin, `{act, nature?, alive?, by?}`: the one its record states, or else its domain's (its record in
# `schema_language.attr_domains`, or its value type's row). Asked here and of no copy — the save's `now`, the forms'
# said days, the gate's clock checks and the merge's rank of sources read it, and no tool keeps a list of names. A
# position the law does not declare (a key of an open map, `details`) has none, and nothing here guesses one.
INNER = 'inner'         # a domain whose positions are its own entries', or the field's it tracks
SAVE, READER = 'save', 'reader'     # the `by` names of `read` the save and the reckoner answer to
LAW_BY, GARDEN = 'law', 'garden'    # the `by` names of `said`: the schema owns it; another garden said it


def _terms(fm, key):
    """The terms a front matter declares under `key`, with those of its profiles: each with a schema."""
    fm = fm if isinstance(fm, dict) else {}
    out = list(fm.get(key) or [])
    for p in ((fm.get('profiles') or {}).values() if isinstance(fm.get('profiles'), dict) else []):
        out += list(p.get('terms') or []) if isinstance(p, dict) else []
    return [t for t in out if isinstance(t, dict) and isinstance(t.get('schema'), dict)]


def _natures_of(o):
    """The natures an origin names, as a list — [] where it names none (any nature)."""
    n = o.get('nature') if isinstance(o, dict) else None
    return list(n) if isinstance(n, list) else [] if n is None else [n]


class Origins:
    """The law's acts and natures, and the origin of each position its terms and a garden's own declare. `law` is the
    standard's front matter, `local` a garden's VOCAB.md's; either may be None."""

    def __init__(self, law, local=None):
        law = law if isinstance(law, dict) else {}
        self.law = law
        self.acts = [r for r in (law.get('acts') or []) if isinstance(r, dict)] if isinstance(law.get('acts'), list) else []
        self.act_names = [r.get('act') for r in self.acts]
        # THE NATURES AS THE GATE READS THEM: a garden's restatement where it declares one, and the rows it adds
        _loc = local if isinstance(local, dict) else {}
        _rows = _loc.get('natures') if isinstance(_loc.get('natures'), list) else law.get('natures')
        _adds = _loc.get('registry_additions').get('natures') if isinstance(_loc.get('registry_additions'), dict) else None
        self.natures = [r.get('nature') for r in (list(_rows) if isinstance(_rows, list) else [])
                        + (list(_adds) if isinstance(_adds, list) else []) if isinstance(r, dict)]
        self.types = {t.get('type'): t for t in (law.get('value_types') or []) if isinstance(t, dict)}
        _sl = law.get('schema_language') if isinstance(law.get('schema_language'), dict) else {}
        self.domains = dict(_sl['attr_domains']) if isinstance(_sl.get('attr_domains'), dict) else {}
        self.sources = [('law', t) for t in _terms(law, 'terms')] + [('VOCAB', t) for t in _terms(local, 'local_terms')]
        # the positions of a record the law declares outside the terms: provenance's `as_of`, a journal's heading
        self.records = {k: (law.get(k) or {}).get('origin') if isinstance(law.get(k), dict) else None
                        for k in ('provenance_record', 'journal')}

    def by_names(self, act):
        """The `by` names an act's row lists."""
        r = next((r for r in self.acts if r.get('act') == act), None)
        return list(r['by']) if isinstance(r, dict) and isinstance(r.get('by'), dict) else []

    def invalid(self, o):
        """Why `o` is not an origin — `{act, nature?, alive?, by?}` against `acts` and `natures` — or None."""
        if not isinstance(o, dict):
            return f"{o!r} is not `{{act, nature?, alive?, by?}}`"
        extra = sorted(set(o) - {'act', 'nature', 'alive', 'by'})
        if extra:
            return f"{o!r} holds {extra}: an origin holds `act`, `nature`, `alive` and `by` only"
        if 'alive' in o and o['alive'] is not True:
            return f"alive {o['alive']!r}: an origin from a being in its living phase says `alive: true`, and otherwise says nothing"
        if o.get('act') not in self.act_names:
            return f"act {o.get('act')!r} is not a row of `acts` {self.act_names}"
        ns = _natures_of(o)
        if 'nature' in o and (not ns or len(set(map(str, ns))) != len(ns) or any(n not in self.natures for n in ns)):
            return f"nature {o.get('nature')!r} is not a row of `natures` {self.natures}, or a list of them each once"
        if 'by' in o and o['by'] not in self.by_names(o['act']):
            return f"by {o['by']!r} is not one of the names `acts[{o['act']}]` lists {self.by_names(o['act'])}"
        return None

    def default(self, d):
        """The origin a domain gives a position that states none: its value type's row's, else its domain's."""
        kind = dmform.domain_kind(d)
        if kind == 'type' and isinstance(d, dict):
            t = self.types.get(d.get('type'))
            if isinstance(t, dict) and t.get('origin') is not None:
                return t['origin']
        rec = self.domains.get(kind)
        return rec.get('origin') if isinstance(rec, dict) else None

    def of(self, rec):
        """The origin of the position whose attribute record is `rec`: stated, or its domain's; INNER, or None."""
        if not isinstance(rec, dict):
            return None
        return rec['origin'] if rec.get('origin') is not None else self.default(rec.get('in'))

    @staticmethod
    def clock(o):
        """How an origin reads the clock: 'judged' — the save reads it, and a value typed is refused; 'offered' — its
        recorder reads it, and `now` is offered; or None."""
        if not isinstance(o, dict) or o.get('act') != 'read':
            return None
        return 'judged' if o.get('by') == SAVE else 'offered' if o.get('by') is None else None

    @staticmethod
    def said(o):
        """True where a value in this position is someone's word, not a reading of the clock or the world."""
        return isinstance(o, dict) and o.get('act') == 'said'

    def judged(self, record, attr):
        """True where the law's `record` (`provenance_record`, `journal`) says the save reads `attr` from the clock."""
        m = self.records.get(record)
        return isinstance(m, dict) and self.clock(m.get(attr)) == 'judged'

    def rank(self, source):
        """A map of value to origin (`values_source`) as the values' order, lightest first: by the row of `acts`
        first, then by life — from a being in its living phase, which can be asked, above what cannot be — then by the
        row of `natures`; or None where two values would rank the same, or one is no origin."""
        if not isinstance(source, dict) or any(self.invalid(o) for o in source.values()):
            return None
        key = {v: (self.act_names.index(o['act']), 1 if o.get('alive') else 0,
                   min((self.natures.index(n) for n in _natures_of(o)), default=-1))
               for v, o in source.items()}
        if len(set(key.values())) != len(key):
            return None
        return sorted(key, key=key.get)

    def positions(self):
        """[(source, where, name, record)] of every attribute, at every depth, of every term the law and the garden declare."""
        out = []

        def walk(src, attrs, where):
            for n, rec in (attrs.items() if isinstance(attrs, dict) else []):
                if isinstance(rec, dict):
                    out.append((src, f"{where}.{n}", str(n), rec))
                    d = rec.get('in')
                    if isinstance(d, dict) and isinstance(d.get('entries'), dict):
                        walk(src, d['entries'], f"{where}.{n}")
        for src, t in self.sources:
            walk(src, t['schema'].get('attrs'), str(t.get('term') or t.get('name')))
        return out

    def unit(self, rec):
        """What the save writes at a clock position — 'day' or 'moment' — read from the unit the position is held to
        (27.0: `in: { type: position, unit: <unit> }`): a day, or a moment for a unit finer than the day. None where the
        position states no unit, so the save has no resolution to write `now` at."""
        d = rec.get('in') if isinstance(rec, dict) else None
        t = self.types.get(d.get('type')) if isinstance(d, dict) else None
        if not isinstance(t, dict) or not t.get('any_system') or d.get('unit') is None:
            return None
        return 'day' if d['unit'] == t.get('unit') else 'moment'

    def clocked(self):
        """{'day': names, 'moment': names}: the attributes — by name, at any depth — that may be written `now`, with
        what the save writes in its place: the reading of its heading, at the unit the position's type holds. A
        provenance record's `as_of` is a day. A name the law gives both units is in neither: the gate names it."""
        out = {'day': set(), 'moment': set()}
        for _s, _w, n, rec in self.positions():
            u = self.unit(rec)
            if u and self.clock(self.of(rec)):
                out[u].add(n)
        if self.judged('provenance_record', 'as_of'):
            out['day'].add('as_of')
        both = out['day'] & out['moment']
        return {k: v - both for k, v in out.items()}

    def problems(self):
        """[(source, why)] — what in the acts, the domains' origins, a position's origin or a source no reader can read."""
        out = []
        if not self.acts:
            return [('law', "no `acts` — no position can say where its value comes from")]
        bys = []
        for r in self.acts:
            a = r.get('act')
            if not isinstance(a, str) or not a or self.act_names.count(a) > 1:
                out.append(('law', f"acts: {a!r} is not one name no other row has"))
            if 'by' in r and not (isinstance(r['by'], dict) and r['by']
                                  and all(isinstance(k, str) and isinstance(v, str) for k, v in r['by'].items())):
                out.append(('law', f"acts[{a}].by is not a map of name to meaning"))
            bys += self.by_names(a)
        for b in sorted({b for b in bys if bys.count(b) > 1}):
            out.append(('law', f"acts: `by: {b}` is listed under two acts — a reader that asks `by` could not tell which"))
        if not self.natures:
            out.append(('law', "no `natures` — no origin can say what nature its source is"))
        for d, rec in self.domains.items():
            o = rec.get('origin') if isinstance(rec, dict) else None
            if not isinstance(rec, dict) or not isinstance(rec.get('form'), str):
                out.append(('law', f"schema_language.attr_domains.{d} is not `{{form, origin}}`"))
            elif o is None:
                out.append(('law', f"schema_language.attr_domains.{d} gives no origin — a position in it would have none"))
            elif o != INNER and self.invalid(o):
                out.append(('law', f"schema_language.attr_domains.{d}.origin: {self.invalid(o)}"))
        for t, row in self.types.items():
            if row.get('origin') is not None and self.invalid(row['origin']):
                out.append(('law', f"value_types[{t}].origin: {self.invalid(row['origin'])}"))
        for k, m in self.records.items():
            for attr, o in (m.items() if isinstance(m, dict) else []):
                if self.invalid(o):
                    out.append(('law', f"{k}.origin.{attr}: {self.invalid(o)}"))
            if m is not None and not isinstance(m, dict):
                out.append(('law', f"{k}.origin is not a map of attribute to origin"))
        _pa = (self.law.get('provenance_record') or {}).get('attrs') if isinstance(self.law.get('provenance_record'), dict) else None
        for attr in (self.records.get('provenance_record') or {}) if isinstance(self.records.get('provenance_record'), dict) else []:
            if attr not in (_pa or []):
                out.append(('law', f"provenance_record.origin.{attr}: not one of provenance_record.attrs {_pa}"))
        units = {}
        for src, where, n, rec in self.positions():
            stated = rec.get('origin')
            if stated is not None and self.invalid(stated):
                out.append((src, f"{where}.origin: {self.invalid(stated)}"))
                continue
            if stated is not None and stated == self.default(rec.get('in')):
                out.append((src, f"{where}.origin is {stated}, which its domain already gives — state an origin only "
                                 f"where the domain's is wrong"))
            o = self.of(rec)
            if o is None:
                out.append((src, f"{where}: its domain gives no origin, and it states none"))
            if self.clock(o) == 'judged' and self.unit(rec) is None:
                out.append((src, f"{where}.origin is read by the save from the clock, but its type holds neither a "
                                 f"day nor a moment — type it `date` or `moment`"))
            if self.clock(o) and self.unit(rec):
                units.setdefault(n, set()).add(self.unit(rec))
        if self.judged('provenance_record', 'as_of'):
            units.setdefault('as_of', set()).add('day')
        for n, us in sorted(units.items()):
            if len(us) > 1:
                out.append(('law', f"`{n}` is read from the clock as a day at one position and a moment at another — "
                                   f"the save finds a `now` by the attribute's name, and could not tell which to write"))
        # A TERM RANKED BY SOURCE: every value says where it comes from, and no two rank the same.
        for src, t in self.sources:
            m = t.get('merge') if isinstance(t.get('merge'), dict) else {}
            vs = t['schema'].get('values')
            if m.get('order') != 'source' and 'values_source' not in t:
                continue
            name = t.get('term') or t.get('name')
            srcmap = t.get('values_source')
            if m.get('order') != 'source':
                out.append((src, f"{name}: `values_source` with no `merge: {{order: source}}` — nothing reads it"))
            elif not isinstance(srcmap, dict) or not isinstance(vs, list) or set(srcmap) != set(vs):
                out.append((src, f"{name}: `merge: {{order: source}}` needs `values_source` naming each of its values "
                                 f"{vs} once, and nothing else"))
            elif self.rank(srcmap) is None:
                out.append((src, f"{name}.values_source: {next((f'{v}: {self.invalid(o)}' for v, o in srcmap.items() if self.invalid(o)), 'two values would rank the same (the same act and nature)')}"))
        # WHERE A SYSTEM'S OWN MACHINERY COMES FROM: each way a system is reckoned, walked or placed.
        shape = self.law.get('system_shape') if isinstance(self.law.get('system_shape'), dict) else {}
        for word, m in (shape.get('sources') or {}).items() if isinstance(shape.get('sources'), dict) else []:
            offered = shape.get(word)
            if isinstance(offered, list) and (not isinstance(m, dict) or set(m) != set(offered)):
                out.append(('law', f"system_shape.sources.{word}: names {sorted(m) if isinstance(m, dict) else m}, "
                                   f"and system_shape.{word} offers {offered}: each once"))
            for k, o in (m.items() if isinstance(m, dict) else []):
                if o is not None and self.invalid(o):
                    out.append(('law', f"system_shape.sources.{word}.{k}: {self.invalid(o)}"))
        for a in (self.law.get('aspects') or []) if isinstance(self.law.get('aspects'), list) else []:
            for p in (a.get('positions') or []) if isinstance(a, dict) else []:
                if isinstance(p, dict) and p.get('origin') is not None and self.invalid(p['origin']):
                    out.append(('law', f"aspects[{a.get('aspect')}].{p.get('position')}.origin: {self.invalid(p['origin'])}"))
        return out


def origins(root=ROOT):
    """The Origins of the law at its one path and of this garden's VOCAB.md. An unreadable law gives no rows, and every
    reader then finds no position that reads the clock — the gate names the law."""
    def fm(p):
        try:
            with open(os.path.join(root, *p.split('/')), encoding='utf-8') as fh:
                return _front(fh.read())
        except (OSError, UnicodeDecodeError):
            return None
    return Origins(fm(LAW), fm('VOCAB.md'))


# ============================== WHICH PASSES ARE GRANTED (24.0; the Leviathan's Body 3, the flow law) ==============================
# A pass is material moving from a SOURCE to a DESTINATION by a METHOD. The law's `flows` are closed rows of the three:
# a pass no row holds is refused, the nearest row that holds decides, and of two as near a refusal. A garden's own rows
# (VOCAB.md `flows`) only add refusals, or grant a named party where the standard says `ratified`. Asked here and of no
# copy: the gate judges a pointer and a pass log by it, and test/passes.py holds each row to a granted and a refused pass.
GRANTS = ('granted', 'refused', 'ratified')
KEEPERS = ('release',)
ROW_KEYS = ('flow', 'from', 'to', 'method', 'grant', 'keeper', 'why')     # `flow_form`, less its two sentences
LOCAL_KEYS = ROW_KEYS + ('party', 'basis')      # a garden's grant names its party and the basis it grants on
PASS_KEYS = ('from', 'to', 'method', 'metadata')
ESTATE = 'estate'


def _list(x):
    return list(x) if isinstance(x, list) else [] if x is None else [x]


class Decision(tuple):
    """(granted, grant, rows): whether the pass may be made; the standard's word on it — granted, refused, ratified, or
    `closed` where no row holds; and the names of the rows that decided."""

    def __new__(cls, granted, grant, rows):
        return super().__new__(cls, (bool(granted), grant, tuple(rows)))

    granted = property(lambda s: s[0])
    grant = property(lambda s: s[1])
    rows = property(lambda s: s[2])


class Flows:
    """The law's `flows`, and a garden's own. A destination is a layer's name, or `(ESTATE, origin)` for a value placed
    in the estate at a position of that origin (None where the law declares none)."""

    def __init__(self, law, local=None):
        law = law if isinstance(law, dict) else {}
        local = local if isinstance(local, dict) else {}
        self.origins = Origins(law, local)
        self.layers = {r.get('layer'): r for r in (law.get('layers') or []) if isinstance(r, dict)}
        self.methods = [r.get('method') for r in (law.get('methods') or []) if isinstance(r, dict)]
        self.rows = [r for r in (law.get('flows') or []) if isinstance(r, dict)] if isinstance(law.get('flows'), list) else []
        self.local = [r for r in (local.get('flows') or []) if isinstance(r, dict)] if isinstance(local.get('flows'), list) else []
        _k = self.origins.types.get('kebab') or {}
        self.kebab = _k.get('pattern') if isinstance(_k.get('pattern'), str) else r'[a-z0-9]+(-[a-z0-9]+)*'
        self.metadata = {r.get('key'): r.get('in') for r in (law.get('pass_metadata') or []) if isinstance(r, dict)}
        self.terms = {}
        for _src, t in self.origins.sources:
            for k in (t.get('context_keys') or [t.get('term') or t.get('name')]):
                self.terms.setdefault(k, t)
        _w = (self.terms.get('words') or {}).get('schema', {}).get('attrs', {}).get('form', {})
        self.forms = list(_w.get('in')) if isinstance(_w, dict) and isinstance(_w.get('in'), list) else []

    # -- judging one pass
    @staticmethod
    def near(row, dest):
        """How near a row's destination is to `dest`: 0 where it does not hold; 1 for a layer; 2 for an origin whose
        act is the value's, and 1 more for each of `nature` and `by` it names, where they are the value's too."""
        to = row.get('to')
        if isinstance(dest, tuple):
            o = dest[1]
            if not isinstance(to, dict):
                return 1 if ESTATE in _list(to) else 0
            if not isinstance(o, dict) or to.get('act') != o.get('act'):
                return 0
            n = 2
            if 'nature' in to:
                if not set(_natures_of(to)) & set(_natures_of(o)):
                    return 0
                n += 1
            if 'by' in to:
                if to['by'] != o.get('by'):
                    return 0
                n += 1
            return n
        return 1 if not isinstance(to, dict) and dest in _list(to) else 0

    @staticmethod
    def holds(row, src, method, keeper=None):
        return (src in _list(row.get('from')) and method in _list(row.get('method'))
                and (row.get('keeper') is None or row.get('keeper') == keeper))

    def decide(self, src, dest, method, keeper=None, party=None):
        """Whether a pass from the layer `src` to `dest` by `method` is granted — a Decision. `keeper` is the source
        file's (`release`, or None), `party` the bean of the party it goes to, where a garden's grant must name one."""
        mine = [r for r in self.local if self.holds(r, src, method, keeper) and self.near(r, dest)]
        refused = [r.get('flow') for r in mine if r.get('grant') == 'refused']
        hit = [(self.near(r, dest), r) for r in self.rows if self.holds(r, src, method, keeper)]
        hit = [(n, r) for n, r in hit if n]
        if not hit:
            return Decision(False, 'closed', refused)
        top = max(n for n, _ in hit)
        rows = [r for n, r in hit if n == top]
        said = {r.get('grant') for r in rows}
        grant = 'refused' if 'refused' in said or not said <= set(GRANTS) else 'ratified' if 'ratified' in said else 'granted'
        names = [r.get('flow') for r in rows]
        if refused:
            return Decision(False, grant, names + refused)
        if grant == 'ratified':
            ok = [r.get('flow') for r in mine if r.get('grant') == 'granted' and party is not None and r.get('party') == party]
            return Decision(bool(ok), grant, names + ok)
        return Decision(grant == 'granted', grant, names)

    def direction(self, src, dest, keeper=None):
        """Whether material may come from `src` to `dest` at all — a pointer says where a value came from, not how it
        was carried. The rows NEAREST the destination decide, by whichever method they name: of those, one that grants
        grants (a proposal taken, where another row refuses a copy by hand), else the refusal; `closed` where none holds.
        So a said value pointed at another bean meets `copied-is-not-said`, and not a merge's row for the estate."""
        top = {}
        for m in self.methods:
            n = max((self.near(r, dest) for r in self.rows if self.holds(r, src, m, keeper)), default=0)
            if n:
                top[m] = n
        if not top:
            return self.decide(src, dest, self.methods[0] if self.methods else None, keeper)
        n = max(top.values())
        ds = [self.decide(src, dest, m, keeper) for m in self.methods if top.get(m) == n]
        return next((d for d in ds if d.granted), ds[0])

    # -- where a pass's ends are
    def origin_at(self, at):
        """The origin of the position a bean's dotted path `at` names — `cost.amount`, `contacts.anna.email` — or None
        where the law declares none there. A segment no attribute names is an entry's key, or a list's place."""
        segs = [s for s in str(at).split('.') if s]
        t = self.terms.get(segs[0]) if segs else None
        if t is None:
            return None
        attrs, rec = t['schema'].get('attrs'), None
        for s in segs[1:]:
            if isinstance(attrs, dict) and isinstance(attrs.get(s), dict):
                rec = attrs[s]
                d = rec.get('in')
                attrs = d.get('entries') if isinstance(d, dict) else None
        return self.origins.of(rec) if rec is not None else None

    def endpoint(self, e, layer_of=None):
        """A pass's source or destination as the law judges it — a layer, or (ESTATE, origin) — or a str: why it is
        none. `layer_of(path)` gives a file's layer (the tree's map); without one a file cannot be placed."""
        if not isinstance(e, dict) or not e:
            return f"{e!r} is not one of `pass_form.from`'s forms"
        keys = set(e)
        if keys == {'file'} and isinstance(e['file'], str):
            layer = layer_of(e['file']) if layer_of else None
            return layer or f"file {e['file']!r} is in no layer: a pass cannot be judged from it"
        if 'bean' in e and keys <= {'bean', 'at'} and isinstance(e['bean'], str):
            return (ESTATE, self.origin_at(e['at'])) if 'at' in e else ESTATE
        if keys == {'garden'} and isinstance(e['garden'], str):
            return 'other-garden'
        if keys == {'layer'}:
            r = self.layers.get(e['layer'])
            if isinstance(r, dict) and r.get('files') is False:
                return e['layer']
            return f"layer {e['layer']!r} is not a layer that holds no files — name a file, a bean or a garden instead"
        return f"{e!r} is not one of `pass_form.from`'s forms: {{file}}, {{bean, at?}}, {{garden}} or {{layer}}"

    def pass_problems(self, p):
        """Why `p` is not a pass (`pass_form`), as a list: the four keys and nothing else, a known method, metadata
        from `pass_metadata` only."""
        if not isinstance(p, dict):
            return [f"{p!r} is not a pass: a map of {', '.join(PASS_KEYS)}"]
        out = []
        if set(p) != set(PASS_KEYS):
            out.append(f"a pass holds {', '.join(PASS_KEYS)} and nothing else; this one holds {sorted(p)}")
        if p.get('method') not in self.methods:
            out.append(f"method {p.get('method')!r} is not a row of `methods`")
        md = p.get('metadata', {})
        if not isinstance(md, dict):
            return out + ["`metadata` is not a map"]
        for k, v in md.items():
            kind = self.metadata.get(k)
            ok = (kind == 'count' and isinstance(v, int) and not isinstance(v, bool) and v >= 0
                  or kind == 'oid' and isinstance(v, str) and len(v) in (40, 64) and all(c in '0123456789abcdef' for c in v)
                  or kind == 'form' and v in self.forms
                  or kind == 'bean' and isinstance(v, str) and bool(v))
            if kind is None:
                out.append(f"metadata `{k}` is not a row of `pass_metadata` — a pass carries counts, locators and object ids, never the material")
            elif not ok:
                out.append(f"metadata `{k}`: {v!r} is not {'a ' + kind if kind != 'form' else 'a word of `words.form` ' + str(self.forms)}")
        return out

    def said_values(self, fm):
        """{(dotted path, value as JSON)} of every value a front matter holds at a position whose origin is `said` — a
        list's entry by its place, an open map's by its key. The gate's claim and the save's trace read this one."""
        out = set()

        def walk(path, entries, attrs):
            for lab, e in entries:
                if not isinstance(e, dict):
                    continue
                here = f"{path}.{lab}" if lab is not None else path
                for a, rec in attrs.items():
                    if not isinstance(rec, dict) or e.get(a) is None:
                        continue
                    d = rec.get('in')
                    if isinstance(d, dict) and isinstance(d.get('entries'), dict):
                        v = e[a]
                        walk(f"{here}.{a}", list(enumerate(v)) if isinstance(v, list) else [(None, v)], d['entries'])
                    elif isinstance(e[a], bool):
                        continue            # a form chosen (`crown: true`, `self: true`), not words: nothing to quote (32.0)
                    elif Origins.said(self.origins.of(rec)):
                        out.add((f"{here}.{a}", json.dumps(e[a], sort_keys=True, default=str)))
        for k, v in (fm.items() if isinstance(fm, dict) else []):
            t = self.terms.get(k)
            sch = t.get('schema') if isinstance(t, dict) else None
            if not isinstance(sch, dict) or not isinstance(sch.get('attrs'), dict):
                continue
            shape = sch.get('shape')
            es = (list(v.items()) if shape == 'open_map_of_entries' and isinstance(v, dict) else
                  list(enumerate(v)) if shape == 'list_of_entries' and isinstance(v, list) else [(None, v)])
            walk(str(k), es, sch['attrs'])
        return out

    # -- the law's own soundness
    def cells(self, row):
        """[(from, to, method, keeper)] a row covers, one per layer and method it names; `to` a layer, or its origin."""
        tos = [('o', tuple(sorted(row['to'].items(), key=str)))] if isinstance(row.get('to'), dict) else _list(row.get('to'))
        return [(s, t, m, row.get('keeper')) for s in _list(row.get('from')) for t in tos for m in _list(row.get('method'))]

    def problems(self):
        """[(source, why)] — what in the flow law, or a garden's own rows, no reader can judge by."""
        out = []
        if not self.rows:
            return [('law', "no `flows` — every pass would be refused, and none could be granted")]
        if not self.methods or len(set(self.methods)) != len(self.methods) or not all(isinstance(m, str) and m for m in self.methods):
            out.append(('law', f"methods: {self.methods} is not a list of names, each once"))
        for k, v in self.metadata.items():
            if v not in ('count', 'oid', 'form', 'bean'):
                out.append(('law', f"pass_metadata[{k}].in: {v!r} is not count, oid, form or bean"))
        names = []
        for src, rows, keys in (('law', self.rows, ROW_KEYS), ('VOCAB', self.local, LOCAL_KEYS)):
            for r in rows:
                n = r.get('flow')
                names.append(n)
                where = f"flows[{n}]"
                if not isinstance(n, str) or not re.fullmatch(self.kebab, n):
                    out.append((src, f"{where}: `flow` is not a kebab name"))
                extra = sorted(set(r) - set(keys))
                if extra:
                    out.append((src, f"{where} holds {extra}: a row holds {', '.join(keys)}"))
                for layer in _list(r.get('from')):
                    if layer not in self.layers:
                        out.append((src, f"{where}.from: {layer!r} is not a row of `layers`"))
                to = r.get('to')
                if isinstance(to, dict):
                    if self.origins.invalid(to):
                        out.append((src, f"{where}.to: {self.origins.invalid(to)}"))
                elif not _list(to) or any(t not in self.layers for t in _list(to)):
                    out.append((src, f"{where}.to: {to!r} is not a layer, a list of layers, or an origin"))
                if not _list(r.get('method')) or any(m not in self.methods for m in _list(r.get('method'))):
                    out.append((src, f"{where}.method: {r.get('method')!r} is not a row of `methods`, or a list of them"))
                if r.get('grant') not in GRANTS:
                    out.append((src, f"{where}.grant: {r.get('grant')!r} is not one of {', '.join(GRANTS)}"))
                if 'keeper' in r and r['keeper'] not in KEEPERS:
                    out.append((src, f"{where}.keeper: {r['keeper']!r} is not one of {', '.join(KEEPERS)}"))
                if not (isinstance(r.get('why'), str) and r['why'].strip()):
                    out.append((src, f"{where}: no `why` — a row says why it is as it is"))
        for n in sorted({n for n in names if names.count(n) > 1 and isinstance(n, str)}):
            out.append(('law', f"flows: `{n}` names two rows"))
        seen = {}
        for r in self.rows:
            for c in self.cells(r):
                if c in seen and seen[c] != r.get('flow'):
                    out.append(('law', f"flows[{r.get('flow')}] and flows[{seen[c]}] both decide {c[2]} from {c[0]} to "
                                       f"{c[1] if isinstance(c[1], str) else dict(c[1][1])}: one cell, one row"))
                seen.setdefault(c, r.get('flow'))
        # A GARDEN NEVER UNGUARDS THE STANDARD: its rows refuse, or grant a named party a cell the standard ratifies.
        for r in self.local:
            where = f"flows[{r.get('flow')}]"
            if r.get('grant') == 'refused':
                continue
            if r.get('grant') != 'granted':
                out.append(('VOCAB', f"{where}: a garden's row is `refused`, or `granted` to a party where the standard "
                                     f"says `ratified` — never {r.get('grant')!r}"))
                continue
            if not (isinstance(r.get('party'), str) and r['party']) or not (isinstance(r.get('basis'), str) and r['basis'].strip()):
                out.append(('VOCAB', f"{where}: a garden's grant names its `party` (a bean) and the `basis` it grants on"))
            for s, t, m, k in self.cells(r):
                dest = (ESTATE, dict(t[1])) if isinstance(t, tuple) else t
                d = self.decide(s, dest, m, k)
                if d.grant != 'ratified':
                    out.append(('VOCAB', f"{where}: grants {m} from {s} to {t if isinstance(t, str) else dict(t[1])}, which "
                                         f"the standard decides {d.grant} ({', '.join(d.rows) or 'no row'}) — a garden "
                                         f"grants only where the standard says `ratified`"))
        return out


def flows(root=ROOT):
    """The Flows of the law at its one path and of this garden's VOCAB.md."""
    o = origins(root)
    return Flows(o.law, _read_front(root, 'VOCAB.md'))


# ------------------------------ how far each row is guarded: COMPUTED, never typed ------------------------------
# A tool says which rows it checks in a module-level dict literal, `GUARDS = {flow: {checks, proof, label, when?}}`,
# and a review that only shows what it found says so in `EVIDENCE`. Where the tool runs places the check: at every
# commit where the pre-commit hook names it, at a push where the pre-push hook does, otherwise in that tool alone. A
# registration made `when: claimed` (a commit that claims its session) or `when: pointed` (where a value's pointer is
# kept) is weaker than one that holds always. A row no tool registers is `hoped`.
PLACES = ('hoped', 'evidence', 'tool', 'push', 'commit')    # weakest first
CONDITIONS = ('claimed', 'pointed')
HOOKS = (('commit', 'bin/hooks/pre-commit'), ('push', 'bin/hooks/pre-push'))
TOOL_GLOBS = ('bin/*.py', 'assets/*/bin/*.py', 'assets/*/lib/*.py')


def _registrations(path):
    """{name: literal} of the module-level `GUARDS` and `EVIDENCE` of one Python file, read without running it."""
    import ast
    try:
        with open(path, encoding='utf-8') as fh:
            tree = ast.parse(fh.read())
    except (OSError, UnicodeDecodeError, SyntaxError):
        return {}
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) \
                and node.targets[0].id in ('GUARDS', 'EVIDENCE'):
            try:
                out[node.targets[0].id] = ast.literal_eval(node.value)
            except ValueError:
                out[node.targets[0].id] = None
    return out


def guards(root=ROOT):
    """[(flow, tool, place, when, reg)] of every registration in this tree's tools, and [(tool, why)] of those that
    cannot be read. `reg` is the registration as the tool wrote it."""
    import glob
    hooks = {}
    for place, p in HOOKS:
        try:
            with open(os.path.join(root, *p.split('/')), encoding='utf-8') as fh:
                hooks[place] = fh.read()
        except OSError:
            hooks[place] = ''
    regs, bad = [], []
    for g in TOOL_GLOBS:
        for f in sorted(glob.glob(os.path.join(root, *g.split('/')))):
            tool = os.path.relpath(f, root).replace(os.sep, '/')
            found = _registrations(f)
            runs = next((place for place, text in hooks.items() if tool in text), 'tool')
            for name, place in (('GUARDS', runs), ('EVIDENCE', 'evidence')):
                lit = found.get(name)
                if name not in found:
                    continue
                if not isinstance(lit, dict):
                    bad.append((tool, f"`{name}` is not a dict literal of flow to registration"))
                    continue
                for flow, reg in lit.items():
                    if not isinstance(reg, dict) or not {'checks', 'proof', 'label'} <= set(reg) \
                            or not set(reg) <= {'checks', 'proof', 'label', 'when'} \
                            or reg.get('when', CONDITIONS[0]) not in CONDITIONS:
                        bad.append((tool, f"`{name}[{flow}]` is not {{checks, proof, label, when?}}, `when` one of {CONDITIONS}"))
                        continue
                    regs.append((flow, tool, place, reg.get('when'), reg))
    return regs, bad


def rank(place, when):
    """A guard's strength, for the ratchet: its place, and within it a check that always holds above one on a condition."""
    return PLACES.index(place) * 2 + (0 if when else 1) if place != 'hoped' else 0


def status(fl, regs):
    """{flow: (place, when, [tools])}: each row's strongest guard, `hoped` where none."""
    out = {}
    for r in fl.rows:
        mine = [g for g in regs if g[0] == r.get('flow')]
        if not mine:
            out[r.get('flow')] = ('hoped', None, [])
            continue
        top = max(rank(g[2], g[3]) for g in mine)
        best = [g for g in mine if rank(g[2], g[3]) == top]
        out[r.get('flow')] = (best[0][2], best[0][3], sorted({g[1] for g in best}))
    return out


def _read_front(root, p):
    try:
        with open(os.path.join(root, *p.split('/')), encoding='utf-8') as fh:
            return _front(fh.read())
    except (OSError, UnicodeDecodeError):
        return None


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
    """(path, scheme) of every code a front matter holds, wherever it is: a coding, `<scheme>:<code>` (29.0) — and a
    mapping that still names a `scheme`, so a special-category code is never missed in a garden not yet translated."""
    if isinstance(node, str):
        if dmparse.split_coding(node)[0] is not None:
            yield path, dmparse.split_coding(node)[0]
    elif isinstance(node, dict):
        if isinstance(node.get('scheme'), str):
            yield path, node['scheme']
        for k, v in node.items():
            # the bean's own verdict, and the questions its readings ask: a code in a selection says what is asked for,
            # and is no material about anyone (29.0: a question now names its code with its scheme, as a record does)
            if path == '' and k in ('sensitivity', 'selections'):
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
    for f in (os.path.basename(p) for p in dmgarden.paths(root, 'beans')):
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
        # TODAY IN THE SAME COUNT AS THE BOUNDS: dmcal's day number. It was the count of days since 1970, and a bound's is
        # dmcal's (about 739,000 now against about 20,700), so a grant with a `to` never ended and one with a `from`
        # never began, wherever no `at` was given — the view host, the hub, the gate.
        now = _day(at) if at else _day(time.strftime('%Y-%m-%d', time.gmtime(time.time())))
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


def _subjects(bid, fm):
    """The persons a bean is the record of: whoever it is `about`, and the person it is, for a person's own bean."""
    out = {e.get('who') for e in fm.get('about') or [] if isinstance(e, dict)} if isinstance(fm.get('about'), list) else set()
    if fm.get('genos') == 'person':
        out.add(bid)
    return out


def owner_of(fm):
    """The bean a bean's `owned_by` names as its owner, or None. Ownership has no facets (32.0): `owned_by: { owner:
    {bean} }`. A garden still at an earlier release writes it under its root facet, `owned_by: { legal: { owner: … } }`,
    and a reader of another garden meets both, so both are read."""
    ob = (fm or {}).get('owned_by')
    if not isinstance(ob, dict):
        return None
    e = ob if 'owner' in ob else ob.get('legal') if isinstance(ob.get('legal'), dict) else {}
    o = e.get('owner') if isinstance(e, dict) else None
    return o.get('bean') if isinstance(o, dict) and isinstance(o.get('bean'), str) else None


def _owners(fm):
    """The beans a bean's `owned_by` names as owner."""
    o = owner_of(fm)
    return {o} if o else set()


def shares(holder, hfm, bid, fm):
    """Whether the agreement `holder` may decide a grant over the bean `bid`: its own bean, and what a party who ACCEPTED
    it brings into it — a bean that party owns, or is the record of. Nothing else: an agreement is not a key to the
    garden, and a bean nobody who accepted it holds is not its to open."""
    if bid == holder:
        return True
    ps = hfm.get('parties')
    accepted = {e['who']['bean'] for e in (ps.values() if isinstance(ps, dict) else [])
                if isinstance(e, dict) and e.get('accepted') and isinstance(e.get('who'), dict)
                and isinstance(e['who'].get('bean'), str)}
    return bool(accepted & (_owners(fm) | _subjects(bid, fm)))


def may(actor, act, bean, *, positions=None, at=None, reason=None, root=ROOT, beans=None, gardener=None):
    """Whether `actor` may `act` (read, write, act:<tool>, ratify:<class>) on `bean` — at `positions`, or the whole bean.
    CLOSED BY DEFAULT: the gardener is granted; nobody is granted what no grant opens. A grant counts when its holder may
    decide it — the gardener; the person the bean is of or `about`; an agreement, over its own bean and what a party who
    accepted it owns or is the record of (`shares`) — and it matches the act, holds the bean (`over`, or the bean holding
    it), covers the positions, names the actor and holds at `at`. A `forbidden` one refuses whatever a `permitted` one
    opens."""
    gardener = gardener if gardener is not None else gardener_of(root)
    if actor is None:
        return Answer(False, "nobody named: an actor no one can name is granted nothing")
    if actor == gardener:
        return Answer(True, f"{actor} is the gardener, who keeps the garden")
    beans = beans if beans is not None else beans_here(root)
    fm = beans.get(bean) or {}
    subjects = _subjects(bean, fm)
    read, forbid, permit, notes = [], [], [], []
    for holder, hfm in sorted(beans.items()):
        gs = hfm.get('grants')
        if not isinstance(gs, dict):
            continue
        may_decide = holder == gardener or holder in subjects or \
            (hfm.get('genos') == 'contract' and shares(holder, hfm, bean, fm))
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
            (forbid if g.get('permission') == 'forbidden' else permit).append((holder, key, g))
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


# ============================== LEG 2 (24.0): what the save traces, and what POST looks for ==============================
# The launcher (bin/dmlaunch.py) and the hook (bin/dmhook.py) keep a session's material, per clone and off git; the save
# (bin/dmsave.py) traces each said value it is about to commit back through it. The judging is here, and reads only
# what it is handed: it opens no store and writes nothing.
RELAYS = ('self',)          # material that only carries: the model's own output. A session's own beans are named per call
PERSON = ('words', 'instructions')
DISTINCT = 8                # a needle this long names one thing; a shorter one is found everywhere, and decides nothing
_DAY = re.compile(r'^\d{4}-\d{2}-\d{2}')
_AMOUNT = re.compile(r'^-?\d[\d.,]{2,}$')


def needles(value, titles=None):
    """The strings a value would be found by in material, as written: each scalar in it, a day as the law writes it,
    and for a bean it names, the id and that bean's title (`titles`), since words name a party, not its id."""
    out = []

    def walk(v):
        if isinstance(v, dict):
            if isinstance(v.get('bean'), str):
                out.append(v['bean'])
                t = titles(v['bean']) if callable(titles) else (titles or {}).get(v['bean'])
                if isinstance(t, str) and t.strip():
                    out.append(t.strip())
            for k, x in v.items():
                if k != 'bean':
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, bool) or v is None:
            return
        else:
            s = v.isoformat() if hasattr(v, 'isoformat') else str(v)
            if s.strip():
                out.append(s.strip())
    walk(value)
    return list(dict.fromkeys(out))


def distinctive(n):
    """True where finding `n` in material says where it came from: a day, an amount of three digits or more, or a
    string of DISTINCT characters or more. A short word or a small number is in everything, and proves nothing."""
    return bool(_DAY.match(n) or _AMOUNT.match(n) or len(n) >= DISTINCT)


def quoted(n, text):
    """How often `n` stands in `text` as written — whole, not inside a longer word or number; case aside."""
    return len(re.findall(r'(?<![\w])' + re.escape(n) + r'(?![\w])', text or '', re.I)) if n else 0


class Trace(tuple):
    """(verdict, source, method, quoted, decision, distinct): `words` — found in a person's words or instructions, the
    pass take-down; `granted` — found only where another granted row holds (a run's capture, by `record`); `refused` —
    found, by a distinctive needle, only where the flow law refuses it; `nowhere` — found nowhere quoted, HOPED.
    `distinct` counts the finds by a needle that names one thing (`distinctive`): a `words` found only by a short word
    or a small number is `distinct: 0`, and the record says the attribution is weak rather than claim it."""
    __slots__ = ()

    def __new__(cls, verdict, source, method, n, decision=None, distinct=0):
        return tuple.__new__(cls, (verdict, source, method, n, decision, distinct))

    verdict = property(lambda s: s[0])
    source = property(lambda s: s[1])
    method = property(lambda s: s[2])
    quoted = property(lambda s: s[3])
    decision = property(lambda s: s[4])
    distinct = property(lambda s: s[5])


def trace(fl, value, origin, materials, skip=(), titles=None):
    """Where a said value the save is about to commit came from, traced THROUGH EVERY RELAY to its terminal source:
    the model's own output is skipped, and so are `skip` (the session's own beans, whose values were traced when they
    were written, and the bean itself). `materials` is [(entry, text)], an entry {source, layer}. A person's words win
    wherever they hold it; else a granted row; else a refusal where a distinctive needle was found; else nowhere."""
    ns = needles(value, titles)
    dest = (ESTATE, origin)
    others = []
    for e, text in materials:
        layer, src = e.get('layer'), e.get('from') or {}
        if layer in RELAYS or src.get('file') in skip or src.get('bean') in skip:
            continue
        n = sum(quoted(x, text) for x in ns)
        if not n:
            continue
        k = sum(quoted(x, text) for x in ns if distinctive(x))
        if layer in PERSON:
            d = fl.decide(layer, dest, 'take-down')
            if d.granted:
                return Trace('words', src, 'take-down', n, d, k)
        others.append((e, n, k))
    refused = None
    for e, n, k in others:
        d = fl.direction(e['layer'], dest)
        if d.granted:
            row = next((r for r in fl.rows if r.get('flow') in d.rows and r.get('grant') == 'granted'), {})
            return Trace('granted', e['from'], (_list(row.get('method')) or [None])[0], n, d, k)
        if k and refused is None:
            refused = Trace('refused', e['from'], None, n, d, k)
    return refused or Trace('nowhere', {'layer': 'instructions'}, 'take-down', 0, None, 0)


def _line_key(s):
    import hashlib
    return hashlib.sha256(s.encode('utf-8')).hexdigest()[:24]


POST_MIN = 12               # a line this long, stripped, is one line of one file; a shorter one is in many


def denied_lines(root, m, fl, files=None):
    """POST's index: {hash of a line: path} of every line of POST_MIN characters or more, of every file in the tree a
    request may not carry — one in no layer (R4: refused as a launcher's source), or in a layer the flow law does not
    let into a request by `render`. Derived from the law each time, and never kept."""
    out = {}
    for p in (files if files is not None else tracked(root)):
        layer = m.layer_of(p)[0]
        if layer and fl.decide(layer, 'request', 'render', 'release' if m.keeper_of(p) == 'release' else None).granted:
            continue
        f = os.path.join(root, *p.split('/'))
        try:
            if os.path.getsize(f) > 1 << 20:
                continue
            with open(f, encoding='utf-8') as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError, ValueError):
            continue
        for l in text.split('\n'):
            if len(l.strip()) >= POST_MIN:
                out.setdefault(_line_key(l.strip()), p)
    return out


def post_hits(text, index):
    """{path: lines} of the lines of `text` (a tool's output) that stand, whole, in a file POST's index holds."""
    out = {}
    for l in (text or '').split('\n'):
        p = index.get(_line_key(l.strip())) if len(l.strip()) >= POST_MIN else None
        if p:
            out[p] = out.get(p, 0) + 1
    return out


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
    if '--flows' in argv:
        fl = flows()
        regs, bad = guards()
        st = status(fl, regs)
        rows = {r.get('flow'): {'from': r.get('from'), 'to': r.get('to'), 'method': r.get('method'), 'grant': r.get('grant'),
                                'guard': st[r.get('flow')][0], 'when': st[r.get('flow')][1], 'by': st[r.get('flow')][2]}
                for r in fl.rows}
        stray = sorted({g[0] for g in regs} - set(rows))
        if '--json' in argv:
            print(json.dumps({'version': m.version, 'flows': rows, 'problems': fl.problems(), 'unreadable': bad,
                              'unknown': stray}, ensure_ascii=False, indent=1))
            return 0
        print(f"the flow law of std-vocab {m.version}: {len(rows)} rows, a pass no row holds refused")
        for name, r in rows.items():
            print(f"  {name:<24} {r['grant']:<9} {r['guard']}{' when ' + r['when'] if r['when'] else ''}"
                  + (f"  ({', '.join(r['by'])})" if r['by'] else ''))
        by = {}
        for r in rows.values():
            by[r['guard']] = by.get(r['guard'], 0) + 1
        print('  ' + ', '.join(f"{by[p]} {p}" for p in reversed(PLACES) if p in by))
        for src, why in fl.problems():
            print(f"  PROBLEM ({src}): {why}")
        for tool, why in bad:
            print(f"  UNREADABLE {tool}: {why}")
        for f in stray:
            print(f"  a tool registers `{f}`, which no row of the law names")
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
