#!/usr/bin/env python3
"""pass — where every file sits: the law's layer map, read once, for every tool that asks.

    python3 bin/pass.py --layers            # each layer with the files it holds, and the files in none
    python3 bin/pass.py --layers --json     # the same, for a tool
    python3 bin/pass.py <path> ...          # the layer and the keeper of each path
    python3 bin/pass.py --flows [--json]    # each row of the flow law, and how far it is guarded
    python3 bin/pass.py --digests [--write | --check]   # the SHA-256 of every file this release ships (seed/LANGUAGE.sha256)

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

AND THE FLOW LAW (24.0): `CoreFlows.decide(from, to, method)` — whether a pass is granted, closed by default —
and `--flows`, each row with its guard, computed from the `GUARDS` the tools declare and the hooks that run them.

AND LEG 2 (24.0): `trace` — where a said value the save is about to commit came from, through every relay to its
terminal source — and `denied_lines`/`post_hits`, POST's look at a tool's output by content. They judge what they are
handed; the launcher and the hook keep the material.

It reads the law at the one path it has, and refuses rather than guess when the law does not parse. It opens no
network path and writes nothing.
"""
import fnmatch, json, os, posixpath, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as dmparse
import garden as dmgarden  # noqa: E402 — the one garden model: where its documents are
import form as dmform   # the one reader of how the law spells an attribute

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
    """The profiles a law offers: the names under its `profiles` — today's law's, a mapping by name, or the core's
    (core/law/profiles.yaml, v1 part 11), a list of rows each naming its `profile`."""
    p = law.get('profiles') if isinstance(law, dict) else None
    if isinstance(p, list):
        return sorted(str(r['profile']) for r in p if isinstance(r, dict) and r.get('profile'))
    return sorted(str(k) for k in p) if isinstance(p, dict) else []


def offered_in(read):
    """The profiles the release a tree carries offers, `read` reading its files: the core's (core/law/profiles.yaml)."""
    core = read('core/law/profiles.yaml')
    if core:
        import yaml
        return offered(yaml.load(core, Loader=yaml.BaseLoader) or {})
    return []


def extended(vocab):
    """The profiles a garden's VOCAB.md takes, as it states them: the core's `profiles` (v1 part 11), else today's
    `extends_profiles`."""
    p = vocab.get('profiles') if isinstance(vocab, dict) and isinstance(vocab.get('profiles'), list) else \
        vocab.get('extends_profiles') if isinstance(vocab, dict) else None
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


# -- the language held to its pin (core 3.5, II.2): the SHA-256 of every file the release ships, carried in its own tree
#    and so signed by its tag; laid into a garden with the rest, and changed there only by the commit that adopts a release
DIGESTS = 'seed/LANGUAGE.sha256'


def release_files(root):
    """The files of the release at `root` that its seed/LANGUAGE ships, every profile its law offers read — the digests'
    own file aside: what `git ls-files` lists in a clone, else every file under `root` but git's and Python's caches."""
    r = subprocess.run(['git', '-C', root, 'ls-files', '-z'], capture_output=True)
    if r.returncode == 0 and r.stdout:
        files = [f for f in r.stdout.decode('utf-8', 'replace').split('\0') if f]
    else:
        files = []
        for d, ds, fs in os.walk(root):
            ds[:] = [x for x in ds if x not in ('.git', '__pycache__')]
            files += [os.path.relpath(os.path.join(d, f), root).replace(os.sep, '/') for f in fs if not f.endswith('.pyc')]

    def read(p):
        p = os.path.join(root, p)
        return open(p, encoding='utf-8').read() if os.path.isfile(p) else ''
    return [f for f in kept(files, language(read('seed/LANGUAGE')), offered_in(read)) if f != DIGESTS]


def sha256_of(path=None, data=None):
    """The SHA-256 of a file as git keeps it: in text (no NUL byte, as git tells text) a CRLF is read as LF, so a checkout
    that turned its line ends (Git for Windows, core.autocrlf) holds the release's file still — and no text a release
    ships keeps a CRLF (test/digests.py)."""
    import hashlib
    if data is None:
        with open(path, 'rb') as fh:
            data = fh.read()
    return hashlib.sha256(data if b'\0' in data[:8000] else data.replace(b'\r\n', b'\n')).hexdigest()


def digests_text(root):
    """The digests of the release at `root`, as `sha256sum` writes them: `<SHA-256>  <path>`, one file a line, by path."""
    return ''.join(f"{sha256_of(os.path.join(root, f))}  {f}\n" for f in sorted(release_files(root)))


def digests_of(text):
    """{path: SHA-256} of a digests file's text; lines that are not `<64 hex digits>  <path>` are left out."""
    out = {}
    for line in (text or '').split('\n'):
        m = re.fullmatch(r'([0-9a-f]{64})  (\S.*)', line.rstrip('\r'))
        if m:
            out[m.group(2)] = m.group(1)
    return out


def diverged(root):
    """[path] of each file the digests at `root` name that `root` holds with other content: the copy of the language
    there is not the release's. [] where the copy carries no digests (a release from before core 3.5, or none)."""
    p = os.path.join(root, *DIGESTS.split('/'))
    if not os.path.isfile(p):
        return []
    with open(p, encoding='utf-8', errors='replace') as fh:
        want = digests_of(fh.read())
    return [f for f, h in sorted(want.items())
            if os.path.isfile(os.path.join(root, f)) and sha256_of(os.path.join(root, f)) != h]


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
        # IN A GARDEN OF THE CORE (v1 part 8) the map is core/law/layers.yaml's, and the garden places the rest by its
        # VOCAB.md `standing` rows, and the profiles a release offers are core/law/profiles.yaml's (part 11)
        self.core = True                  # the map is the core's law's (core/law/layers.yaml) and the garden's rows
        self._core(read, standing)

    def _core(self, read, standing):
        import yaml
        face = yaml.load(read('core/law/core.yaml') or '', Loader=yaml.BaseLoader) or {}
        lay = yaml.load(read('core/law/layers.yaml') or '', Loader=yaml.BaseLoader) or {}
        if not face or not lay:
            raise ValueError("core/law/core.yaml or core/law/layers.yaml is not there or does not parse: there is no map "
                             "without the law")
        self.version = f"core@{face.get('version')}"
        self.rows = [{'layer': r['layer'], 'holds': _list(r.get('holds')), 'files': True}
                     for r in lay.get('standing') or [] if isinstance(r, dict) and isinstance(r.get('layer'), str)]
        named = {r['layer'] for r in self.rows}
        self.rows += [{'layer': x, 'files': False} for x in _list(face.get('layers')) + _list(lay.get('flow_sources'))
                      if x not in named]
        self.layers = {r['layer']: r for r in self.rows}
        self.journal_path = 'log/journal.md'
        self.language = expand(language(read(LANGUAGE)), offered_in(read))
        vocab = _front(read('VOCAB.md')) or {}
        self.standing = list(standing) if standing is not None else [
            ('VOCAB.md', i, {'doc': 'file:' + str(h), 'standing': r['layer']})
            for i, r in enumerate(vocab.get('standing') or []) if isinstance(r, dict) and isinstance(r.get('layer'), str)
            for h in _list(r.get('holds'))]

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
        loop. The gate refuses each, before any file is judged by a map it cannot read. The core's map is judged by the
        core's own law (`core/check.py --law`)."""
        if self.core:
            return []
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
        sys.path.insert(0, ROOT)
        from core import reach
        out, loop = reach.chain(tops[0], lambda at: [b] if (b := (self.layers.get(at) or {}).get('beneath')) else [])
        if loop is not None:
            raise ValueError(f"the chain of `beneath` loops at `{loop}`")
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


def flows(root=ROOT):
    """The flow law the garden at `root` runs: the core's (CoreFlows), with the garden's own rows."""
    return CoreFlows(core_law(root))


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
    """(level, why): the derived level, which a stated `sensitivity` raises — or lowers, on a person's own word only.
    A bean of the core's statements is the core's to judge (core_sensitivity)."""
    if isinstance(fm, dict) and isinstance(fm.get('statements'), list):
        return core_sensitivity(fm, gardener=gardener)
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


def today_in(zone):
    """Today's day number (cal's count) in `zone`, the civil time zone a garden reckons its days in (GARDEN.md `zone`):
    the day its people are living, which east of UTC begins hours before UTC's and west of it ends hours after. UTC's
    where no zone is named, or the one named is not read here."""
    import time
    import stale as dmstale
    now = int(time.time() * 1000)
    try:
        return dmstale.local_day(now, zone or 'UTC')
    except dmstale.Unreckoned:
        return dmstale.local_day(now, 'UTC')


def _day(x, zone=None):
    """The day number of a position: a day as written, a moment the day it falls on in `zone` (UTC's where none)."""
    import cal as dmcal
    s = str(x).strip()
    try:
        ms = dmcal.moment(s).ms
    except Exception:
        return dmcal.to_day(s)
    import stale as dmstale
    try:
        return dmstale.local_day(ms - dmcal.UNIX_DAY * dmcal.DAY_MS, zone or 'UTC')
    except dmstale.Unreckoned:
        return ms // dmcal.DAY_MS


def _during(d, at, zone=None):
    """Whether a grant's `during` holds on the day of `at` (today when absent), its days the garden's: read in `zone`.
    None where a bound is not read."""
    if not isinstance(d, dict):
        return True
    try:
        # TODAY IN THE SAME COUNT AS THE BOUNDS: cal's day number. It was the count of days since 1970, and a bound's is
        # cal's (about 739,000 now against about 20,700), so a grant with a `to` never ended and one with a `from`
        # never began, wherever no `at` was given — the view host, the hub, the gate.
        # AND IN THE GARDEN'S ZONE (2026-10-14): today, and the day a moment falls on, were UTC's, so east of UTC a
        # grant whose last day had ended still opened until UTC's midnight — hours into the next day where its people
        # live — and one whose first day had begun opened nothing until then; west of UTC, the reverse.
        now = _day(at, zone) if at else today_in(zone)
        lo = _day(d['from'], zone) if d.get('from') is not None else None
        hi = _day(d['to'], zone) if d.get('to') is not None else None
    except Exception:
        return None
    return (lo is None or lo <= now) and (hi is None or now <= hi)


def zone_of(root=ROOT):
    """The civil time zone GARDEN.md says the garden reckons its days in, or None."""
    try:
        with open(os.path.join(root, 'GARDEN.md'), encoding='utf-8') as fh:
            g = _front(fh.read())
    except OSError:
        return None
    return g.get('zone') if isinstance(g, dict) and isinstance(g.get('zone'), str) else None


def _windowed(span, window, at, zone, root):
    """(holds, why not) of a grant with a `window` at `at` — a moment, or now where it names none: the moment lies in
    the grant's `at`, read in `zone` (a day there is the zone's day, a moment its instant), and in an occurrence of its
    window (bin/stale.py `in_window`), by the law the garden at `root` runs. A window, or a moment, this cannot read
    holds nothing, and says why."""
    import time
    import stale as dmstale
    try:
        t = int(time.time() * 1000) if at is None else dmstale.instant(at, zone)
    except dmstale.Unreckoned as e:
        return False, f"its window is judged at a moment, and none is read in what was asked ({e})"
    try:
        for side, bound in zip(('from', 'to'), span.split('/', 1) if span and '/' in span else ()):
            if not bound:
                continue
            try:
                b = dmstale.instant(bound, zone)
                ok = t >= b if side == 'from' else t <= b
            except dmstale.Unreckoned:                  # a day: the zone's, the moment's day in it
                d, n = dmstale.day_of(bound), dmstale.local_day(t, zone)
                ok = n >= d if side == 'from' else n <= d
            if not ok:
                return False, None
    except (dmstale.Unreckoned, ValueError, dmstale.dmcal.NotByRule) as e:
        return False, f"its `at` is not read here ({e}), so it opens nothing"
    try:
        tables = dmgarden.law_tables(root)
    except Exception as e:      # noqa: BLE001 — a law that does not load opens nothing through a window
        return False, f"its window is not read here: the garden's law is not read ({e}), so it opens nothing"
    try:
        if dmstale.in_window(window, t, zone, tables.get('SYSTEMS') or {}, tables.get('UNITS') or {}) is None:
            return False, "its window is closed then"
    except (dmstale.Unreckoned, ValueError, OverflowError, KeyError, dmstale.dmcal.NotByRule) as e:
        return False, f"its window is not read here ({e}), so it opens nothing"
    return True, None


def _select(holder, key, root):
    import reckon as dmreckon
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
    and a reader of another garden meets both, so both are read. A bean of the core's statements: its `own`'s `by`."""
    if isinstance(fm, dict) and isinstance(fm.get('statements'), list):
        return next((r['by'] for _i, v, r in statements(fm) if v == 'own' and isinstance(r.get('by'), str)
                     and r.get('of') in (None, 'self', fm.get('bean')) and 'held' not in r), None)
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


def may(actor, act, bean, *, positions=None, at=None, reason=None, root=ROOT, beans=None, gardener=None, held=False,
        readings=None):
    """Whether `actor` may `act` (read, write, act:<tool>, ratify:<class>) on `bean` — at `positions`, or the whole bean;
    with `held`, at positions that hold a value held off git, which only a grant naming them opens (`may_core`).
    CLOSED BY DEFAULT: the gardener is granted; nobody is granted what no grant opens. A grant counts when its holder may
    decide it — the gardener; the person the bean is of or `about`; an agreement, over its own bean and what a party who
    accepted it owns or is the record of (`shares`) — and it matches the act, holds the bean (`over`, or the bean holding
    it), covers the positions, names the actor and holds at `at` (a day or a moment; now where it names none). A
    `forbidden` one refuses whatever a `permitted` one opens. `readings` is the garden a grant's reading of the beans it
    covers is read over, where it is not `root`'s: a hub's, the tree a commit leaves for a bean the commit makes, whose
    grants are still `beans`' (bin/hub.py `rights`)."""
    gardener = gardener if gardener is not None else gardener_of(root)
    if runs_core(root):
        return may_core(actor, act, bean, positions=positions, at=at, reason=reason, root=root, beans=beans,
                        gardener=gardener, held=held, readings=readings)
    if actor is None:
        return Answer(False, "nobody named: an actor no one can name is granted nothing")
    if actor == gardener:
        return Answer(True, f"{actor} is the gardener, who keeps the garden")
    beans = beans if beans is not None else beans_here(root)
    fm = beans.get(bean) or {}
    subjects = _subjects(bean, fm)
    read, forbid, permit, notes = [], [], [], []
    zone = zone_of(root)                                # a grant's days are the garden's
    for holder, hfm in sorted(beans.items()):
        gs = hfm.get('grants')
        if not isinstance(gs, dict):
            continue
        may_decide = holder == gardener or holder in subjects or \
            (hfm.get('genos') == 'contract' and shares(holder, hfm, bean, fm))
        for key, g in sorted(gs.items()):
            if not isinstance(g, dict) or g.get('act') != act or not may_decide:
                continue
            over = {holder} if g.get('over') is None else _select(holder, g['over'], readings or root)
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
            held = _during(g.get('during'), at, zone)
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
# The launcher (bin/launch.py) and the hook (bin/hook.py) keep a session's material, per clone and off git; the save
# (bin/save.py) traces each said value it is about to commit back through it. The judging is here, and reads only
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
    """(verdict, source, method, quoted, decision, distinct, entry): `words` — found in a person's words or instructions, the
    pass take-down; `granted` — found only where another granted row holds (a run's capture, by `record`); `refused` —
    found, by a distinctive needle, only where the flow law refuses it; `nowhere` — found nowhere quoted, HOPED.
    `distinct` counts the finds by a needle that names one thing (`distinctive`): a `words` found only by a short word
    or a small number is `distinct: 0`, and the record says the attribution is weak rather than claim it. `entry` is the
    material's own entry it was found in (its `sha`, its `layer`): the prompt a said value came from, which the session's
    watermark counts (bin/launch.py `Session.watermark`)."""
    __slots__ = ()

    def __new__(cls, verdict, source, method, n, decision=None, distinct=0, entry=None):
        return tuple.__new__(cls, (verdict, source, method, n, decision, distinct, entry))

    verdict = property(lambda s: s[0])
    source = property(lambda s: s[1])
    method = property(lambda s: s[2])
    quoted = property(lambda s: s[3])
    decision = property(lambda s: s[4])
    distinct = property(lambda s: s[5])
    entry = property(lambda s: s[6])


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
                return Trace('words', src, 'take-down', n, d, k, e)
        others.append((e, n, k))
    refused = None
    for e, n, k in others:
        d = fl.direction(e['layer'], dest)
        if d.granted:
            row = next((r for r in fl.rows if r.get('flow') in d.rows and r.get('grant') == 'granted'), {})
            return Trace('granted', e['from'], (_list(row.get('method', row.get('through'))) or [None])[0], n, d, k)
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


# ============================== IN A GARDEN OF THE CORE (v1 part 8) ==============================
# One tool for both laws, by the pin GARDEN.md names. In a garden of the core the flow law is core/law/flows.yaml, decided
# by the core's own `Law.decide`; the layer map is core/law/layers.yaml and VOCAB.md's `standing` rows (Map); who may do
# what is read from `grant` statements; a bean's sensitivity is derived as the engine derives it, and raised by `rate`;
# its owner is `own`'s `by`; and a said value is a role of a statement a `say` knows. Today's paths serve a garden in
# today's words until part 13.
CORE_ACTS = {'said': 'say', 'read': 'read', 'derived': 'derive', 'made': 'make'}
CORE_METHODS = {'take-down': 'say', 'pass-on': 'forward', 'upgrade': 'adopt'}
CORE_GRANTS = {'read': 'read', 'write': 'write'}        # today's act -> the core's `as`; `act:<tool>` is enact, and
                                                        # `ratify:<class>` ratify with its class


def runs_core(root=ROOT):
    """True but for a garden in today's words (`std-vocab@…`), which this release's tools do not read: a garden of the
    core, and a release's own tree, which pins nothing (bin/check.py, the one reader of the pin)."""
    import check
    return check.runs_core(check.pin(root))


def core_law(root=ROOT):
    """The law a garden of the core runs: its release's (the core it carries), extended by its VOCAB.md."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from core import check as core_check
    return core_check.garden_law(root, root if os.path.isfile(os.path.join(root, 'core', 'law', 'core.yaml')) else None)


def statements(fm):
    """[(index, verb, roles)] of a bean of the core's statements."""
    out = []
    for i, st in enumerate(fm.get('statements') or [] if isinstance(fm, dict) else []):
        if isinstance(st, dict) and len(st) == 1:
            (v, r), = st.items()
            if isinstance(r, dict):
                out.append((i, v, r))
    return out


def _leaves(x, path):
    if isinstance(x, dict):
        return [lf for k, v in x.items() for lf in _leaves(v, f"{path}.{k}")]
    if isinstance(x, list):
        return [lf for i, v in enumerate(x) for lf in _leaves(v, f"{path}[{i}]")]
    return [(path, x)]


class CoreFlows:
    """The core's flow law, with the face its readers ask of it — `decide`, `direction`, `rows`, `local`,
    `methods`, `said_values`, `origin_at`, `problems`. A destination in the estate is (ESTATE, act), the act a knowing
    verb; today's origin `{act: said}` and method `take-down` are read in the core's words (`say`)."""

    def __init__(self, law):
        self.law = law
        self.local = list(law.garden_flows)
        self.rows = [r for r in law.flows if not any(r is g for g in self.local)]
        self.methods = list(law.methods) + ['say', 'derive', 'make', 'take', 'serve', 'hold']
        self.metadata = {k: r.get('in') for k, r in law.pass_metadata.items()}
        self.layers = {x: {'layer': x} for x in law.table('layers')}
        self.forms = list(law.tables.get('forms') or [])

    @staticmethod
    def act(dest):
        if isinstance(dest, tuple):
            o = dest[1].get('act') if isinstance(dest[1], dict) else dest[1]
            return dest[0], CORE_ACTS.get(o, o)
        return dest, None

    def decide(self, src, dest, method, keeper=None, party=None):
        to, as_ = self.act(dest)
        return Decision(*self.law.decide(src, to, CORE_METHODS.get(method, method), as_, keeper, party))

    def direction(self, src, dest, keeper=None):
        """Whether material may come from `src` to `dest` at all, by whichever method: a use of the nearest
        (core/nearest.py; core/law/lines.yaml `nearest`, its use `directions`) over the methods' decisions, in their
        order — a grant nearest, then a refusal, then a pass no row holds — its tie the first."""
        from core import nearest
        ds = [self.decide(src, dest, m, keeper) for m in self.methods]
        keys, tie = nearest.use(self.law, 'directions')
        measure = {'grant': lambda d: 0 if d.granted else 2 if d.grant == 'closed' else 1}
        return nearest.nearest(ds, keys, measure, tie)[0][0] if ds else None

    def origin_at(self, at):
        return 'say'                       # said_values names only what a `say` knows

    def problems(self):
        return []                          # the core's law is judged by core/check.py --law

    def said_values(self, fm, beans=()):
        """{(path, value as JSON)} of each value of a statement a `say` knows — `<verb>#<id>.<role>`, or `<verb>@<n>`
        for the n-th of its verb with no id — but what is a being, a statement or a row of the law (the law owns those:
        no pass carries them), and `now`, `unknown` and `self`."""
        sts = statements(fm)
        said, covered, blanket = set(), set(), False
        for _i, v, r in sts:
            if v in self.law.knowing:
                ids = {x.split('#', 1)[1] if x.startswith(f"{fm.get('bean')}#") else x     # its own bean's, `<bean>#<id>`
                       for x in _list(r.get('of')) if isinstance(x, str)}
                covered |= ids
                if v == 'say':
                    said |= ids
                    blanket = blanket or 'of' not in r
        out, n = set(), {}
        for _i, v, r in sts:
            n[v] = n.get(v, 0) + 1
            sid = r.get('id') if isinstance(r.get('id'), str) else None
            if v in self.law.knowing or 'held' in r or not (sid in said or (blanket and sid not in covered)):
                continue
            row = self.law.verbs.get(v) or {}
            specs = dict(row.get('qualifiers') or {}, **(row.get('roles') or {}))
            for role, x in r.items():
                sp = specs.get(role)
                if not isinstance(sp, dict) or set(_list(sp.get('shape'))) <= {'row', 'being', 'statement'}:
                    continue
                for path, leaf in _leaves(x, f"{v}#{sid}.{role}" if sid else f"{v}@{n[v]}.{role}"):
                    if leaf in ('now', 'unknown', 'self') or leaf in beans or isinstance(leaf, bool):
                        continue
                    out.add((path, json.dumps(leaf, sort_keys=True, default=str)))
        return out


def core_sensitivity(fm, gardener=None, schemes=None):
    """(level, why) of a bean of the core: SPECIAL-CATEGORY where an unsealed statement holds a code of a scheme marked
    so; PERSONAL where it is the bean of a person who is not the gardener, or `concern`s one (the engine's `derived`); a
    `rate` raises it, and lowers it only where a person said it (rule harm)."""
    marked = set(schemes) if schemes is not None else _marked_schemes()
    sts = statements(fm)
    special = [f"a code of {sc} at {v}#{r.get('id', i)}" for i, v, r in sts if 'held' not in r
               for _p, leaf in _leaves(r, '') if isinstance(leaf, str) and ':' in leaf
               for sc in [leaf.split(':', 1)[0]] if sc in marked]
    level, why = ('special-category', special) if special else ('none', [])
    if level == 'none':
        person = fm.get('kind') == 'person' and fm.get('bean') != gardener
        others = [x for _i, v, r in sts if v == 'concern' for x in _list(r.get('of')) if x != gardener]
        if person or others:
            level = 'personal'
            why = (["the bean of a person who is not the gardener"] if person else []) + \
                  [f"concerns {x}, who is not the gardener" for x in others]
    for _i, v, r in sts:
        if v == 'rate' and r.get('as') in LEVELS and 'held' not in r:
            if _rank(r['as']) > _rank(level):
                level, why = r['as'], why + [f"raised by {r.get('by')}: {r.get('why') or r.get('note') or ''}".rstrip(': ')]
    return level, why


def _marked_schemes(root=ROOT):
    try:
        law = core_law(root)
        return {str(k) for k, r in (law.std.schemes or {}).items() if isinstance(r, dict)
                and r.get('sensitive') == 'special-category'} | \
               {str(r.get('scheme')) for r in law.own.get('schemes') or [] if r.get('sensitive') == 'special-category'}
    except Exception:
        return set()


def may_core(actor, act, bean, *, positions=None, at=None, reason=None, root=ROOT, beans=None, gardener=None, held=False,
             readings=None):
    """`may` in a garden of the core. A `grant` statement opens an act — `as` read, write, enact or ratify; `of` the
    beans or the statements it covers (an id in its own bean, `<bean>#<id>` in another; none: its own bean); `to` whom;
    `at` the extent it holds over — where its holder may decide it: the gardener; the person the bean is, or concerns;
    an agreement, over its own bean and what a party who agreed to it owns or is. A position on the permission square
    that forbids the grant (`forbidden: { of: <its id> }`) refuses what any grant opens. Closed by default.

    A grant `of` a reading (a `reckon` statement) covers each bean the reading holds, and one `to` a reading opens to
    each member it holds, read each time it is asked; its `cover` (v1 part 12b) opens only the parts it names — a key of
    the header, `body`, a verb's statements, a verb's narrowed by their `as` — so the whole bean, asked, is not opened by
    it, and a part asked is, as is a statement of a verb it names; `reason: asked` asks each use its reason. A reading
    `of` is read over `readings` where it is given (a hub's, for a bean the commit makes), the grants themselves and a
    reading `to` over `root` still.

    A grant with a `window` (a recurrence each of whose occurrences lasts: office hours on working days) holds at a
    MOMENT that lies in its `at` and in an occurrence of its window, both read in the garden's zone (GARDEN.md `zone`):
    asked with a day, or with nothing it can read, it opens nothing, and the answer says why. A grant without one holds
    over the days of its `at`, as it always has.

    A HELD VALUE (`held`: the positions asked hold what is kept off git — a sealed statement, by its id, or the part of
    the bean a record held off git is pointed to from, `body` or `details.<key>`) is opened only by a grant that NAMES
    it: its `cover` naming the part (a statement's id, its verb, its verb narrowed by its `as`), or its `of` naming the
    statement (`<bean>#<id>`). A grant of the whole bean opens what the bean holds, never by itself what is held of it
    elsewhere; the gardener aside (RULE-CHANGE 2026-10-12), and the person it is held of, who reads what is held of
    them in their own bean. Asked with no positions, nothing held is opened."""
    if actor is None:
        return Answer(False, "nobody named: an actor no one can name is granted nothing")
    if actor == gardener:
        return Answer(True, f"{actor} is the gardener, who keeps the garden")
    asked = CORE_GRANTS.get(act) or ('enact' if str(act).startswith('act:') else 'ratify' if str(act).startswith('ratify:')
                                     else act)
    if held and asked == 'read' and positions and actor == bean and \
            ((beans if beans is not None else beans_here(root)).get(bean) or {}).get('kind') == 'person':
        return Answer(True, f"{actor} reads what is held of them, in their own bean")
    klass = str(act).split(':', 1)[1] if str(act).startswith('ratify:') else None
    beans = beans if beans is not None else beans_here(root)
    fm = beans.get(bean) or {}
    sts = statements(fm)
    subjects = ({bean} if fm.get('kind') == 'person' else set()) | \
               {x for _i, v, r in sts if v == 'concern' for x in _list(r.get('of')) if isinstance(x, str)}
    owners = {r.get('by') for _i, v, r in sts if v == 'own' and r.get('of') in (None, 'self', bean)
              and isinstance(r.get('by'), str)}               # an owner nobody names (`{ someone: org }`) decides nothing
    read, forbid, permit, asks, notes, zone = [], [], [], set(), [], False
    verbs_of = {str(r.get('id')): (v, r) for _i, v, r in sts if isinstance(r.get('id'), str)}

    def members(b_, sid, over=root):
        """The beans a reading holds over the garden at `over`, or None where the statement is no reading or cannot be
        read."""
        if not any(v == 'reckon' and r.get('id') == sid for _i, v, r in statements(beans.get(b_) or {})):
            return None
        return _select(b_, sid, over)

    def part_holds(p, parts):
        """Whether the asked position `p` — a part's name, or a statement of the bean by its id — is among `parts`."""
        if p in parts or any(p.startswith(q + '.') for q in parts if q in ('details',)):
            return True
        v, r = verbs_of.get(p, (None, {}))
        return v is not None and (v in parts or f"{v}.{r.get('as')}" in parts)
    for holder, hfm in sorted(beans.items()):
        hs = statements(hfm)
        agreed = {x for _i, v, r in hs if v == 'agree' for x in _list(r.get('by')) if isinstance(x, str)}
        decides = holder == gardener or holder in subjects or (
            hfm.get('kind') == 'contract' and (holder == bean or bool(agreed & (owners | subjects))))
        if not decides:
            continue
        refused = {str(r.get('of')) for _i, v, r in hs if v == 'forbidden'}
        for i, v, r in hs:
            if v != 'grant' or 'held' in r or r.get('as') != asked or (klass and r.get('class') not in (None, klass)):
                continue
            cover, parts = False, set()
            for x in map(str, _list(r.get('of')) or ['self']):
                if '#' in x:
                    b_, sid = x.split('#', 1)
                elif x == 'self' or x in beans:
                    b_, sid = (holder if x == 'self' else x), ''
                else:                                       # a statement of the holder's own bean, by its id
                    b_, sid = holder, x
                held_by = members(b_, sid, readings or root) if sid else None
                if held_by is not None:                     # a reading: each bean it holds, read now
                    cover = cover or bean in held_by
                elif b_ == bean:
                    cover = cover or not sid
                    parts |= {sid} if sid else set()
            cv = r.get('cover') if isinstance(r.get('cover'), dict) else {}
            named = {str(p) for p in _list(cv.get('parts'))}
            if cover and named:                             # the parts it opens of each bean it covers
                if not positions or not all(part_holds(str(p), named) for p in positions):
                    continue
            elif not cover and not (parts and positions and set(positions) <= parts):
                continue
            elif cover and held:                            # the whole bean: what it holds, never what is held of it
                continue
            to = set()
            for x in map(str, _list(r.get('to'))):
                b_, sid = x.split('#', 1) if '#' in x else (holder, x)
                got = members(b_, sid) if (x not in beans and x != 'self') else None
                to |= set(got) if got is not None else {x}
            if actor not in to:
                continue
            gid = r.get('id') if isinstance(r.get('id'), str) else f"grant@{i}"
            span = str(r.get('at')) if r.get('at') else None
            if zone is False:
                zone = zone_of(root)                        # its days, and its window, are the garden's
            if r.get('window') is None:
                holds = _during({'from': span.split('/')[0] or None, 'to': span.split('/')[1] or None}
                                if span and '/' in span else None, at, zone)
            else:                                           # in its `at`, and in an occurrence of its window
                holds, why = _windowed(span, r['window'], at, zone, root)
                if why:
                    notes.append(f"{holder}#{gid}: {why}")
            if not holds:
                continue
            read.append((holder, gid))
            if cv.get('reason') == 'asked':
                asks.add((holder, gid))
            (forbid if gid in refused or f"{holder}#{gid}" in refused else permit).append((holder, gid))
    tail = ('; ' + '; '.join(notes)) if notes else ''
    if forbid:
        return Answer(False, f"{forbid[0][0]}#{forbid[0][1]} would open it, and is forbidden" + tail, read)
    if permit:
        return Answer(True, f"granted by {permit[0][0]}#{permit[0][1]}" + tail, read, permit[0] in asks)
    return Answer(False, f"no grant {'names' if held else 'opens'} {asked} on {bean}"
                  + (f" at {', '.join(positions)}" if positions else '') + f" to {actor}"
                  + (", held off git: only a grant naming it opens it" if held else " — closed by default") + tail, read)


def main(argv):
    if '--digests' in argv:                       # a release's own tree: no garden, no map
        text = digests_text(ROOT)
        if '--write' in argv:
            with open(os.path.join(ROOT, *DIGESTS.split('/')), 'w', encoding='utf-8', newline='\n') as fh:
                fh.write(text)
            print(f"pass: {DIGESTS} written, {text.count(chr(10))} files")
            return 0
        if '--check' in argv:
            p = os.path.join(ROOT, *DIGESTS.split('/'))
            have = open(p, encoding='utf-8').read() if os.path.isfile(p) else ''
            if have != text:
                print(f"pass: {DIGESTS} is not this tree's — write it again: python3 bin/pass.py --digests --write",
                      file=sys.stderr)
                return 1
            print(f"pass: {DIGESTS} holds this tree's {text.count(chr(10))} files")
            return 0
        sys.stdout.write(text)
        return 0
    try:
        m = Map.here()
    except ValueError as e:
        print(f"pass: {e}", file=sys.stderr)
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
        rows = {r.get('flow'): {'from': r.get('from'), 'to': r.get('to'), 'method': r.get('method', r.get('through')),
                                'grant': r.get('grant'),
                                'guard': st[r.get('flow')][0], 'when': st[r.get('flow')][1], 'by': st[r.get('flow')][2]}
                for r in fl.rows}
        stray = sorted({g[0] for g in regs} - set(rows))
        if '--json' in argv:
            print(json.dumps({'version': m.version, 'flows': rows, 'problems': fl.problems(), 'unreadable': bad,
                              'unknown': stray}, ensure_ascii=False, indent=1))
            return 0
        print(f"the flow law of {m.version if m.core else 'std-vocab ' + m.version}: {len(rows)} rows, a pass no row "
              f"holds refused")
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
