#!/usr/bin/env python3
"""reckon — the one reckoner: a reading declared in the law's grammar (`selection_form`), read each time it is asked.

    python3 bin/reckon.py <bean>:<selection> [--input name=value ...] [--at <commit> --moment <moment>]
    python3 bin/reckon.py --ad-hoc <file.yaml> [--bean <bean>] [--input name=value ...]   # a reading nobody committed
    python3 bin/reckon.py weigh <bean>:<weighing>          # a weighing's weights and its consistency, read
    python3 bin/reckon.py order <key> <items.tsv>          # items ordered by an ordering key of the law
    add --exact to print every value exactly, rather than to its uncertainty's digits

(`python` on Windows.) A reading is a list of steps, each ONE operation of the law's closed list `operations`, over what
earlier steps gave, the reading's inputs and the beans the garden holds. No formula is written and no string is
evaluated: an operation the list does not hold is refused, and a step never names a later one, so a reading never loops.

WHAT IT PRINTS. Every number with its lines — the beans and paths it was read from, and each step that made it
(manifesto: never-pathless). A value's uncertainty u to at most two significant digits and the value to the same place
(GUM 7.2.6); exact where exact; `≈` where an operation on its path is not; a budget of the variance's shares where more
than one u meets; and the seconds it took. A truth is true, false, or NOT KNOWN — a difference within a band that its
uncertainty cannot resolve is not known, and never rounded to either.

IT WRITES NOTHING, and extrapolates nothing: a series is never read beyond its first or last row. A reading is never
written back as a fact (manifesto: once). An act that fixes a reading records the commit and the moment it was read at
(`pin_form`); `--at` reads every bean as it stood at that commit, and takes the clock as `--moment`.

NOT HERE YET, and refused by name rather than guessed: a position in another reference system where PROJ is absent;
`rotate` until a pole's published rows are held (a vacancy: PLACE carried none); an input read from another garden until AGREE's
bin/across.py lands.

IN A GARDEN OF THE CORE (v1 part 6) a reading is a `reckon` statement, named by its id (`<bean>#<id>`, or `<bean>:<id>`),
its `reading` the form core/law/lines.yaml gives. Its paths are read over statements: a bean is its header (`kind`,
`bean`, `title`, `summary`, `tags`, `details`) and its verbs, each verb the list of its statements' roles — `pay.of` is
what each `pay` gave, `select` takes `kind` where today's took `genos`, and a condition names its comparator by the
core's sign (`=`, `∈`, `≥`, `≤`, `∃`, `∄`, and `≠`, `<`, `>`, which today's words lacked) or by a word the core has no
sign for (`reached`, `at_step`, `refers_to`). `reached` and `at_step` read the bean's moves (path `move`) against the
step named as a statement, `<walk>#<step>`; a series is named `<bean>#<id>`. core/lines.py gives the beans in that
view, and the law a line is read by.

THE API other tools call (the contract's §4):
    evaluate(ref, *, root, inputs, pin) -> Result(kind, value, u, unit, lines, pin, notes)
    select(ref, **kw) -> [member ids]; holds(ref, **kw) -> True | False | None (None: not known)
    path_values(fm, path, *, root, pin) -> [values]; occurrences(bean, clause, *, root, pin) -> [(member, at)]
    check_selection(where, entry, law) -> [(level, text)]; check_each(where, entry, law) -> [(level, text)]
    check_weighing(where, entry) -> [(level, text)]; check_pin(where, pin, *, root, days) -> [(level, text)]
"""
import collections
import decimal
import os
import re
import subprocess
import sys
import time
import unicodedata
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'bin'))     # the tools it reads with: in the core since core 3.0, they stay there
import parse as dmparse  # noqa: E402 — the one reader of a path, a table and a front matter
import garden as dmgarden  # noqa: E402 — the one garden model: where its documents are
import cal as dmcal    # noqa: E402 — positions in any calendar, moments, civil offsets
import seq as dmseq    # noqa: E402 — a series' rows and what a channel holds between them
import importlib
dmpass = importlib.import_module('pass')   # noqa: E402 — where a value comes from: an input's `origin`
import held as dmheld   # noqa: E402 — what a garden keeps off git, read back on the host that holds it

PY ='python' if os.name == 'nt' else 'python3'
KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$', re.ASCII)
COMMIT = re.compile(r'^[0-9a-f]{7,40}$', re.ASCII)
PREC = 40                                          # the digits a value that is not exact is carried to, never printed

Pin = collections.namedtuple('Pin', 'commit at garden')
Result = collections.namedtuple('Result', 'kind value u unit lines pin notes')
Member = collections.namedtuple('Member', 'id node bean')   # a bean (node = its front matter) or one of its entries


class Row(Member):
    """A member as the operations of a rule's reading read it (core 3.0): beside its id, its node and its bean, `place`,
    the statement it is (`<bean>[<i>] <verb>`, where a refusal is told); `seq`, where the garden reads it, in its order;
    `beans`, the bean each part of its node was written in (`''` for the node, a name of `as` for a pair's), so a value
    is read as the being it names there; and `proof`, the statements and the law's rows it rests on."""

    def __new__(cls, id, node, bean, place=None, seq=None, beans=None, proof=()):
        r = super().__new__(cls, id, node, bean)
        r.place, r.seq, r.beans, r.proof = place, seq, beans if beans is not None else {'': bean}, tuple(proof)
        return r


def as_row(m):
    """A member as a Row: itself, or a member of a reading of another kind with no place, order or proof."""
    return m if isinstance(m, Row) else Row(m.id, m.node, m.bean)


def _paths(x):
    """A step's path or list of paths, as a list."""
    if isinstance(x, str):
        return [x]
    return [p for p in x if isinstance(p, str)] if isinstance(x, list) else []


def _proof(*parts):
    """The proofs given, in order, each item once."""
    out = []
    for p in parts:
        for x in p:
            if x not in out:
                out.append(x)
    return tuple(out)


class Refused(Exception):
    """A reading that cannot be read as asked: the words say why, and what would do."""


class V:
    """A value: `v` a Fraction (or text, a position, a code), in `unit`, with its standard uncertainty `u` in the same
    unit (None: exact as written, or not stated), `approx` where an operation on its path is not exact, and `budget`
    {source: variance} where it combined several."""
    __slots__ = ('v', 'unit', 'u', 'approx', 'budget', 'member')

    def __init__(self, v, unit=None, u=None, approx=False, budget=None, member=None):
        self.v, self.unit, self.u, self.approx, self.budget, self.member = v, unit, u, approx, budget or {}, member

    def __repr__(self):
        return f"V({self.v!r}, {self.unit!r}, u={self.u!r}{', ≈' if self.approx else ''})"


# ============================================================================ numbers, never through a float
def D(x):
    with decimal.localcontext() as c:
        c.prec = PREC
        return decimal.Decimal(x.numerator) / decimal.Decimal(x.denominator) if isinstance(x, Fraction) else decimal.Decimal(x)


def F(d):
    return Fraction(d) if not isinstance(d, Fraction) else d


def sqrt(x):
    """√x of a Fraction, exact where it is a square of one, else to PREC digits — and whether it was exact."""
    if x < 0:
        raise Refused(f"the square root of {dmseq.show(x)}, a negative number, is no value")
    n, d = x.numerator, x.denominator
    rn, rd = _isqrt(n), _isqrt(d)
    if rn * rn == n and rd * rd == d:
        return Fraction(rn, rd), True
    with decimal.localcontext() as c:
        c.prec = PREC
        return F(D(x).sqrt()), False


def _isqrt(n):
    import math                                    # an integer square root: exact, and no float in it
    return math.isqrt(n)


def hyp(*us):
    """√(Σ u²) of the uncertainties stated, or None where none is."""
    s = [u for u in us if u is not None]
    return sqrt(sum(u * u for u in s))[0] if s else None


def budget(**shares):
    """{source: variance}, the sources that carried a u."""
    return {k: v * v for k, v in shares.items() if v is not None and v != 0}


def show(v, exact_=False):
    """A value as printed: u to two significant digits and the value to that place; exact where it is."""
    if isinstance(v.v, tuple):
        return ', '.join(show(V(x, v.unit, v.u, v.approx), exact_) for x in v.v)
    if not isinstance(v.v, Fraction):
        return f"{v.v}" + (f" {v.unit}" if v.unit else '')
    unit = f" {v.unit}" if v.unit and v.unit != 'one' else ''
    if v.u is not None and v.u > 0 and not exact_:
        p = dmseq.u_places(v.u)
        return f"{'≈ ' if v.approx else ''}{dmseq.rounded(v.v, p)}{unit} (u {dmseq.rounded(v.u, p)}{unit})"
    if v.approx and not exact_:
        return f"≈ {dmseq.rounded(v.v, 6 - D(abs(v.v) or Fraction(1)).adjusted())}{unit}"
    s = dmseq.show(v.v)
    return s + unit + ('' if v.u is not None or v.approx else '')


# ============================================================================ the law, as the gate reads it
_LAW = []


def law():
    """The gate's reading of the law (seq's Law: units, quantities, systems, a registry by name); in a garden of the
    core, the law a line is read by (core/lines.py `law_view`)."""
    if not _LAW:
        if dmseq.runs_core(ROOT):
            from core import lines
            _LAW.append(lines.law_view(dmseq.core(ROOT)[0], ROOT))
        else:
            _LAW.append(dmseq.Law.of_garden())
    return _LAW[0]


def op_rows(registry):
    return {r['op']: r for r in (registry('operations') or []) if isinstance(r, dict) and isinstance(r.get('op'), str)}


def comparator_rows(registry):
    return {r['comparator']: r for r in (registry('comparators') or []) if isinstance(r, dict) and r.get('comparator')}


def k_factor(registry):
    """`compatibility.multiple`: the coverage factor two values are called compatible at. A garden may state another."""
    c = registry('compatibility')
    c = c if isinstance(c, dict) else {}
    return Fraction(c.get('multiple')) if isinstance(c.get('multiple'), int) else Fraction(2)


# ============================================================================ the garden, now or at a pin
NEGATED = {'≠': 'is'}                     # a sign the core reads that today's words lacked: not equal


_VIEWED = {}        # a garden's root -> (the version held, its beans' views, their folders, their print or None)


def _viewprint(fm):
    import hashlib
    return hashlib.blake2b(repr(sorted(fm.items(), key=lambda kv: kv[0])).encode(), digest_size=20).digest()


class Garden:
    """The front matter of every bean and mapping of one garden, as it stands now or at a commit."""

    def __init__(self, root=ROOT, pin=None):
        self.root, self.pin = root, pin
        self.fm, self.kind = {}, {}
        if dmseq.runs_core(root):
            self._core()
            return
        if pin is not None:
            self._check_pin()
            for p in dmgarden.listed(root, ('beans', 'mappings'), at=pin.commit):
                self._add(p, self._git('show', f"{pin.commit}:{p}"))
        else:
            for path in dmgarden.paths(root):
                try:
                    head, _ = dmparse.read(path)
                except Exception:
                    continue
                self._put(f"{os.path.basename(os.path.dirname(path))}/{os.path.basename(path)}", head)

    def _core(self):
        """A garden of the core, now or at the pin's commit: each bean as core/lines.py views it.

        Now, the views are made once per garden held (core/engine.py `Garden.read`): a page's hundred readings of one
        garden share them, each reading with its own mappings of them; DAFTAR_HELD_CHECK=1 names a reading that
        changes a view it shares."""
        sys.path.insert(0, ROOT)
        from core import engine, lines, read
        if self.pin is None:
            G = engine.Garden.read(self.root)
            kept = _VIEWED.get(self.root)
            check = os.environ.get('DAFTAR_HELD_CHECK') == '1'
            if kept is not None and G.held is not None and kept[0] is G.held:
                if check and _viewprint(kept[1]) != kept[3]:
                    raise engine.HeldChanged(f"a reading changed the views held for {self.root!r}: they are read, "
                                             f"never written")
                self.fm, self.kind = dict(kept[1]), dict(kept[2])
                return
            for bid, b in G.beans.items():
                if not b.unread:
                    self.fm[bid] = lines.view(b, G)
                    self.kind[bid] = os.path.basename(os.path.dirname(b.path)) if b.path else 'beans'
            if G.held is not None:
                _VIEWED[self.root] = (G.held, dict(self.fm), dict(self.kind), _viewprint(self.fm) if check else None)
            return
        else:
            self._check_pin()
            beans = {}
            for p in dmgarden.listed(self.root, ('beans', 'mappings'), at=self.pin.commit):
                bid = os.path.basename(p)[:-3]
                try:
                    head = dmparse.split_front_matter(self._git('show', f"{self.pin.commit}:{p}").replace('\r\n', '\n'))[0]
                    beans[bid] = engine.Bean(bid, p, read.loads(head or '', p) or {})
                except read.Unread as e:
                    beans[bid] = engine.Bean(bid, p, unread=str(e))
            G = engine.Garden(beans, root=self.root)
        for bid, b in G.beans.items():
            if not b.unread:
                self.fm[bid] = lines.view(b, G)
                self.kind[bid] = os.path.basename(os.path.dirname(b.path)) if b.path else 'beans'

    def _git(self, *a):
        r = subprocess.run(['git', '-C', self.root, *a], capture_output=True, text=True, encoding='utf-8')
        if r.returncode:
            raise Refused(f"git {' '.join(a[:2])}: {r.stderr.strip()[:200]}")
        return r.stdout

    def _check_pin(self):
        if not COMMIT.match(str(self.pin.commit)):
            raise Refused(f"a pin names a commit by its object id, 7 to 40 hex digits — not {self.pin.commit!r}")
        if subprocess.run(['git', '-C', self.root, 'merge-base', '--is-ancestor', self.pin.commit, 'HEAD'],
                          capture_output=True).returncode:
            raise Refused(f"the pin's commit {self.pin.commit} is not an ancestor of this garden's HEAD: "
                          f"a reading is pinned to a commit the garden has")

    def _add(self, path, text):
        head, _ = dmparse.split_front_matter(text.replace('\r\n', '\n'))
        self._put(path, head)

    def _put(self, path, head):
        try:
            fm = dmparse.loads(head) if head else None
        except Exception:
            fm = None
        if isinstance(fm, dict):
            i = fm.get('bean') or fm.get('mapping') or os.path.basename(path)[:-3]
            # A SEALED ENTRY IS READ WHERE IT IS HELD (24.0, DOCS D-2): on the host whose store holds it, a reading
            # reads the entry itself; elsewhere, or erased, the pointer, and nothing is known of it.
            self.fm[str(i)], self.kind[str(i)] = dmheld.unsealed(fm, root=self.root), path.split('/')[0]

    def bean(self, i):
        if i not in self.fm:
            raise Refused(f"no bean or mapping '{i}' here" + (f" at {self.pin.commit}" if self.pin else ''))
        return self.fm[i]

    def parts(self, bean, key):
        """A series' parts, `series/<bean>/<key>/*.tsv`, as they stand here."""
        if self.pin is None:
            return dmseq.parts_of(self.root, bean, key)
        out = {}
        for p in self._git('ls-tree', '-r', '--name-only', self.pin.commit, '--', f"series/{bean}/{key}").split('\n'):
            if p:
                n = os.path.basename(p)
                out[n[:-4] if n.endswith('.tsv') else n] = self._git('show', f"{self.pin.commit}:{p}")
        return out


# ============================================================================ paths
def _ref_bean(v):
    """The bean a ref or an id names, or None."""
    if isinstance(v, dict) and isinstance(v.get('bean'), str):
        return v['bean']
    if isinstance(v, str) and KEBAB.match(v):
        return v
    return None


def _own(v, bean):
    """The being a role names, `self` (or nothing) read as the bean the statement is in."""
    if v in (None, 'self'):
        return bean
    return _ref_bean(v) or bean


_PATHS = {}         # a path's text -> its segments (bin/parse.py `path_read`), read once a process


def walk(garden, node, text, at=None):
    """[(value, where)] at a field path from `node` (the front matter or an entry of bean `at`) — `where` the path to
    each value as `<bean>:<keys>`, so a member of a set can be named."""
    segs = _PATHS.get(text) if isinstance(text, str) else None
    if segs is None:
        segs = dmparse.path_read(text)
        if isinstance(text, str):
            _PATHS[text] = tuple(segs)       # a path reads the same each time: read once (its segments never change)
    if segs and segs[0].key == '@occurrence':
        raise Refused("`@occurrence` is read inside a clause that occurs for each member, by AGREE's reader")
    cur = [(node, f"{at}:" if at else '')]
    for i, s in enumerate(segs):
        if s.bean:
            cur = [(garden.bean(s.bean), f"{s.bean}:")]
        if s.follow:
            nxt = []
            for v, _w in cur:
                b = _ref_bean(v)
                if b and b in garden.fm:
                    nxt.append((garden.fm[b], f"{b}:"))
            cur = nxt
        out = []
        for v, w in cur:
            sep = '' if w.endswith(':') else '.'
            if s.key == '**':                   # every value below, at any depth, each before what it holds (I.7)
                out.extend(_below(v, w))
            elif isinstance(v, dict):
                items = v.items() if s.star else ([(s.key, v[s.key])] if s.key in v else [])
                for k, x in items:
                    out.append((x, f"{w}{sep}{k}"))
            elif isinstance(v, list) and (s.star or s.key == 'entries'):
                for n, x in enumerate(v):
                    ident = x.get('id') if isinstance(x, dict) and isinstance(x.get('id'), str) else n
                    out.append((x, f"{w}[{ident}]"))
            elif isinstance(v, list) and not (i and segs[i - 1].key == '**'):   # after `**`, its items are read too
                for n, x in enumerate(v):   # a key into a list reads each entry that holds it
                    if isinstance(x, dict) and s.key in x:
                        out.append((x[s.key], f"{w}[{x.get('id', n)}].{s.key}"))
        if s.match:
            a, want = s.match
            out = [(x, w) for x, w in _flatten(out) if isinstance(x, dict) and str(x.get(a)) == want]
        cur = out
    return cur


def _below(v, w):
    """[(value, where)] for every value below `v`, read at `w`: each value of a map and each item of a list, each before
    the values it holds, at any depth (the path segment `**`, core 3.3, I.7)."""
    out = []

    def go(x, at):
        sep = '' if at.endswith(':') else '.'
        if isinstance(x, dict):
            kids = [(y, f"{at}{sep}{k}") for k, y in x.items()]
        elif isinstance(x, list):
            kids = [(y, f"{at}[{y.get('id') if isinstance(y, dict) and isinstance(y.get('id'), str) else n}]")
                    for n, y in enumerate(x)]
        else:
            return
        for y, where in kids:
            out.append((y, where))
            go(y, where)
    go(v, w)
    return out


def _flatten(pairs):
    out = []
    for x, w in pairs:
        if isinstance(x, list):
            out.extend((y, f"{w}[{y.get('id', n) if isinstance(y, dict) else n}]") for n, y in enumerate(x))
        else:
            out.append((x, w))
    return out


def path_values(fm, path, *, root=ROOT, pin=None, garden=None):
    """The values at a field path of one bean's front matter: a list, empty where the path holds none."""
    garden = garden or Garden(root, pin)
    return [v for v, _w in walk(garden, fm, path, at=fm.get('bean') if isinstance(fm, dict) else None)]


# ============================================================================ values
def value_of(node, where, notes):
    """A V from what a path holds: a measured value with its u (an accuracy turned into u, and said), a count, text."""
    if isinstance(node, dict) and 'count' in node and 'unit' in node:
        x = dmseq.exact(node.get('count'))
        if x is None:
            raise Refused(f"{where}: {node.get('count')!r} is not a count read exactly")
        return V(x, node['unit'], _u_of(node, node['unit'], where, notes))
    if _long(node):
        node = _text(node)                  # a position written long is read as its short form (27.0)
        node = str(node) if node is not None and not isinstance(node, str) else node
    if isinstance(node, bool) or node is None:
        return V(node)
    if isinstance(node, int):
        return V(Fraction(node))
    if isinstance(node, str):
        x = dmseq.exact(node)
        return V(x if x is not None and not KEBAB.match(node) or (x is not None and node.isdigit()) else node)
    return V(node)


def _u_of(node, unit, where, notes):
    """The standard uncertainty a quantity states, in the value's unit: `u`, or an `accuracy` turned into u by its kind."""
    lw = law()
    own = lw.factor(unit)
    u = node.get('u')
    if isinstance(u, dict) and dmseq.exact(u.get('count')) is not None:
        f = lw.factor(u.get('unit'))
        if own and f:
            return dmseq.exact(u['count']) * f / own
        if u.get('unit') == unit:
            return dmseq.exact(u['count'])
    a = node.get('accuracy')
    if isinstance(a, dict) and dmseq.exact(a.get('count')) is not None and own and lw.factor(a.get('unit')):
        x = dmseq.exact(a['count']) * lw.factor(a['unit']) / own
        k = a.get('kind')
        r = {'bound': lambda: sqrt(x * x / 3)[0], 'radius-68': lambda: x,
             'radius-95': lambda: x * Fraction(100, 196)}.get(k)
        if r:
            ux = r()
            notes.append(f"{where}: accuracy {k} {dmseq.show(x)} {unit} → u {dmseq.rounded(ux, dmseq.u_places(ux))} {unit}")
            return ux
        notes.append(f"{where}: an accuracy of kind '{k}' is kept as said, and read as no u")
    return None


def to_unit(v, unit, what):
    """`v` in `unit`, exactly — within one quantity, and one currency."""
    if v.unit == unit or unit is None:
        return v
    lw = law()
    fa, fb = lw.factor(v.unit), lw.factor(unit)
    if v.unit is None and lw.quantity_of(unit) in ('ratio', 'number'):
        return V(v.v, unit, v.u, v.approx, v.budget)
    if fa is None or fb is None or lw.quantity_of(v.unit) != lw.quantity_of(unit):
        raise Refused(f"{what}: {v.unit} and {unit} are not one quantity — nothing converts one into the other")
    r = fa / fb
    return V(v.v * r, unit, None if v.u is None else v.u * r, v.approx, {k: s * r * r for k, s in v.budget.items()})


def _dims(unit):
    lw = law()
    if unit is None:
        return {}
    q = lw.quantities.get(lw.quantity_of(unit)) or {}
    return dict(q.get('of') or {}) if 'of' in q else None


def _unit_for(dims, what):
    """The coherent unit of the quantity whose dimensions these are — or refused, where the law has none."""
    lw = law()
    dims = {k: v for k, v in dims.items() if v}
    if not dims:
        return 'one'
    for qn, q in lw.quantities.items():
        if dict(q.get('of') or {}) == dims:
            c = lw.coherent(qn)
            if c:
                return c
    raise Refused(f"{what}: no quantity of the law measures {dims} — the law's `quantities` would name it first")


def _coherent(v, what):
    """`v` in its quantity's coherent unit, with that unit (a dimensionless or a currency value as it is)."""
    lw = law()
    if v.unit is None or not isinstance(v.v, Fraction):
        return v
    if lw.factor(v.unit) is None:
        return v
    return to_unit(v, lw.coherent(lw.quantity_of(v.unit)) or v.unit, what)


# ============================================================================ positions
_LONG = frozenset(('system', 'at', 'unit', 'by', 'note'))


def _long(x):
    """Whether `x` is a position written LONG (27.0): one entry of `timing`, `{system, at, unit, by?, note?}` — a day
    position's long form, and a timing entry itself, which is the same thing."""
    return isinstance(x, dict) and {'system', 'at', 'unit'} <= set(x) and set(x) <= _LONG


def _text(x):
    """A position as a calendar reads it: the long form by its `at` (cal.written), anything else as it is — and None
    for one placed only by its neighbours, which names no day."""
    try:
        return dmcal.written(x) if _long(x) else x
    except ValueError:
        return None


def _pos(x, zone, notes):
    """A position as ('ms', milliseconds) for a moment, or ('day', n) for a day — or None. Either form of a position."""
    x = _text(x)
    if x is None:
        return None
    s = str(x).strip()
    try:
        return ('ms', dmcal.moment(s).ms)
    except (ValueError, dmcal.NotByRule):
        pass
    try:
        return ('day', dmcal.to_day(s))
    except (ValueError, dmcal.NotByRule):
        return None


def _duration_seconds(q):
    """Seconds in a quantity of duration `{count, unit}` (core/law/units.yaml, its factor to the second), or None."""
    if not isinstance(q, dict):
        return None
    secs = {'ms': 0.001, 's': 1, 'min': 60, 'h': 3600, 'd': 86400, 'wk': 604800}.get(str(q.get('unit')))
    try:
        return float(q.get('count')) * secs if secs else None
    except (TypeError, ValueError):
        return None


def _shown_secs(t):
    """A count of seconds since the calendar's day 0 as a UTC moment, to the second."""
    import datetime
    d = datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(seconds=t - dmcal.DAY_MS / 1000)
    return d.strftime('%Y-%m-%dT%H:%M:%SZ')


def _local_day(ms, zone, instant):
    off = dmcal.offset(zone, instant) if zone else 0
    return (ms + off * 60000) // dmcal.DAY_MS


def pos_cmp(a, b, zone):
    """-1, 0 or 1: two positions ordered — a moment against a day through the day it falls on in the reading's zone."""
    pa, pb = _pos(a, zone, []), _pos(b, zone, [])
    if pa is None or pb is None:
        raise Refused(f"{dmcal.shown(a)!r} and {dmcal.shown(b)!r} are not two positions of time this reader orders")
    if pa[0] != pb[0]:
        if not zone:
            raise Refused(f"{a!r} against {b!r}: a moment is read against a day in a civil zone — the reading states `zone`")
        pa = ('day', _local_day(pa[1], zone, a)) if pa[0] == 'ms' else pa
        pb = ('day', _local_day(pb[1], zone, b)) if pb[0] == 'ms' else pb
    return (pa[1] > pb[1]) - (pa[1] < pb[1])


# ============================================================================ the gate's check (pure)
# A registry a garden extends by a key of its own (`local_gene`), not by `registry_additions`: the reader here does not
# hold those rows, and the gate judges the value against the garden's whole law.
_EXTENDED_ELSEWHERE = ('gene',)


def _registry_values(registry, dom):
    """The values a `{registry, take, where}` domain admits, read from the law's rows (a garden's added rows among them),
    or None where the registry cannot be read here."""
    try:
        rows = [r for r in (registry(dom['registry']) or []) if isinstance(r, dict)]
    except Exception:
        return None
    if not rows:
        return None
    wh = dom.get('where') if isinstance(dom.get('where'), dict) else {}
    take = dom.get('take') or dom['registry'].rstrip('s')
    return {str(r.get(take)) for r in rows if r.get(take) is not None
            and all(r.get(f) in (w if isinstance(w, list) else [w]) for f, w in wh.items())}


def _takes_check(where, step, row, env, law_):
    """A step against its operation's row: its keys are those the row takes, the required ones present, a name a step
    reads an earlier step or an input, a path a path, an enum a value of it, a registry's value one of its rows."""
    out = []
    takes = row.get('takes') or {}
    registry = getattr(law_, 'registry', law_)
    for k in step:
        if k not in ('id', 'op') and k not in takes:
            out.append(('error', f"{where}: `{k}` is not what `{row['op']}` takes — it takes {sorted(takes)}"))
    for k, decl in takes.items():
        decl = decl if isinstance(decl, dict) else {}
        if decl.get('required') and k not in step:
            out.append(('error', f"{where}: `{row['op']}` takes `{k}`, and it is missing"))
        if k not in step:
            continue
        v, dom = step[k], decl.get('in')
        if isinstance(v, dict) and set(v) == {'input'}:  # a value the asker gives: judged when the reading is read
            if v['input'] not in env:
                out.append(('error', f"{where}: `{k}: {{input: {v['input']}}}` names no input of the reading — "
                                     f"{sorted(env) or 'it declares none'}"))
            continue
        if isinstance(dom, dict) and dom.get('type') == 'kebab' and k in ('of', 'with', 'series', 'through', 'within') \
                or (k == 'with' and row.get('op') == 'join' and 'of' in step):     # a join of two sets: two names
            if not isinstance(v, str) or v not in env:
                out.append(('error', f"{where}: `{k}: {v}` names no earlier step and no input — a step reads what "
                                     f"came before it: {sorted(env) or 'nothing yet'}"))
        elif isinstance(dom, dict) and dom.get('type') == 'field_path':
            p = dmparse.path_problem(v) if isinstance(v, str) else "a path is text"
            if p:
                out.append(('error', f"{where}: `{k}: {v}` is not a field path — {p}"))
        elif isinstance(dom, list) and not (v in dom or (isinstance(v, list) and all(x in dom for x in v))):
            out.append(('error', f"{where}: `{k}: {v}` is not one of {dom}"))
        elif isinstance(dom, dict) and dom.get('type') == 'count' and not (isinstance(v, int) or dmseq.exact(v) is not None):
            out.append(('error', f"{where}: `{k}: {v!r}` is not a count"))
        elif isinstance(dom, dict) and isinstance(dom.get('registry'), str) and callable(registry) \
                and dom['registry'] not in _EXTENDED_ELSEWHERE:
            vals = _registry_values(registry, dom)
            if vals is not None and str(v) not in vals:
                # a calendar written by its CLDR name (`gregory`) is the row that carries it (`gregorian-civil`)
                row_of = next((str(r.get('system')) for r in (registry(dom['registry']) or [])
                               if isinstance(r, dict) and r.get('calendar') == v and str(r.get('system')) in vals), None)
                out.append(('error', f"{where}: `{k}: {v}` is not a row of `{dom['registry']}`"
                                     + (f" where {dom['where']}" if dom.get('where') else '')
                                     + (f" — write `{k}: {row_of}`, the system whose calendar is {v}" if row_of
                                        else f" — {', '.join(sorted(vals)[:12])}{', …' if len(vals) > 12 else ''}")))
    return out


def _cond_check(where, conds, env, comps):
    out = []
    if not isinstance(conds, list):
        return [('error', f"{where}: `where` is a list of conditions, each `{{path: <field path>, <comparator>: <operand>}}`")]
    for n, c in enumerate(conds):
        w = f"{where}.where[{n}]"
        if not isinstance(c, dict) or not isinstance(c.get('path'), str):
            out.append(('error', f"{w}: a condition is `{{path: <field path>, <comparator>: <operand>}}`"))
            continue
        p = dmparse.path_problem(c['path'])
        if p:
            out.append(('error', f"{w}: `path: {c['path']}` is not a field path — {p}"))
        cs = [k for k in c if k != 'path']
        if len(cs) != 1 or cs[0] not in comps:
            out.append(('error', f"{w}: a condition names exactly one comparator of the law — {sorted(comps)}; it names {cs}"))
            continue
        op = c[cs[0]]
        if cs[0] == 'fits' and not (isinstance(op, dict) and len(op) == 1 and next(iter(op)) in
                                    ('namespace', 'type', 'system', 'holds') and isinstance(next(iter(op.values())), str)):
            out.append(('error', f"{w}: `fits` names one row of the law, `{{namespace: <row>}}`, `{{type: <row>}}` or "
                                 f"`{{system: <row>}}`, or a Unicode property, `{{holds: <property>}}`"))
            continue
        if isinstance(op, dict) and ('step' in op or 'input' in op):
            if op.get('step', op.get('input')) not in env:
                out.append(('error', f"{w}: `{op}` names no earlier step and no input"))
    return out


def check_selection(where, entry, law_, extra_inputs=()):
    """[(level, text)] for one reading (a `selections` entry, a mechanism's or an ordering key's row) against the law's
    closed list: each step one operation, taking what its row takes, naming only what came before it."""
    registry = getattr(law_, 'registry', law_)
    ops, comps = op_rows(registry), comparator_rows(registry)
    out = []
    if not isinstance(entry, dict):
        return [('error', f"{where}: a reading is a mapping with `steps`")]
    env = set(extra_inputs)
    for i in entry.get('inputs') or []:
        if isinstance(i, dict) and isinstance(i.get('name'), str):
            env.add(i['name'])
    steps = entry.get('steps')
    if not isinstance(steps, list) or not steps:
        return out + [('error', f"{where}: `steps` is a list of one step or more, each `{{id, op, ...}}`")]
    ids = set()
    for n, s in enumerate(steps):
        w = f"{where}.steps[{s.get('id') if isinstance(s, dict) and s.get('id') else n}]"
        if not isinstance(s, dict):
            out.append(('error', f"{w}: a step is a mapping `{{id, op, ...}}`"))
            continue
        sid, op = s.get('id'), s.get('op')
        if not isinstance(sid, str) or not KEBAB.match(sid):
            out.append(('error', f"{w}: a step has an `id`, a kebab word"))
        elif sid in ids or sid in env:
            out.append(('error', f"{w}: the id '{sid}' is taken already — each step and input is named once"))
        if op not in ops:
            out.append(('error', f"{w}: `op: {op}` is not an operation of the law — the list is closed: {sorted(ops)}"))
        else:
            out.extend(_takes_check(w, s, ops[op], env, law_))
            if op == 'join' and ('series' in s) == ('of' in s):
                out.append(('error', f"{w}: `join` joins two series (`series`, `with`) or two sets (`of`, `with`, `on`)"))
            if 'where' in s:
                out.extend(_cond_check(w, s['where'], env, comps))
            if op == 'group' and s.get('level') and not entry.get('zone'):
                out.append(('error', f"{w}: a group by a calendar level reads a moment in a civil zone — the reading "
                                     f"states `zone`, a row of time-zones"))
        # a name later in the list is not in `env` yet: a step never reads one after it
        if isinstance(sid, str):
            ids.add(sid)
            env.add(sid)
    return out


def check_each(where, entry, law_):
    """A reading an `each` clause occurs by: every condition's comparator monotone, or `is` on `genos` — what has entered
    never leaves (AGREE, N3)."""
    registry = getattr(law_, 'registry', law_)
    comps = comparator_rows(registry)
    out = []
    for s in (entry or {}).get('steps') or []:
        if not isinstance(s, dict):
            continue
        for c in s.get('where') or []:
            if not isinstance(c, dict):
                continue
            for k in c:
                if k == 'path' or k not in comps:
                    continue
                if comps[k].get('monotone') is True or (k == 'is' and c.get('path') == 'genos'):
                    continue
                out.append(('error', f"{where}: its selection can lose an occurrence ({k} is not monotone): an `each` "
                                     f"clause occurs for what has entered, and what has entered never leaves"))
    return out


SAATY_RI = {1: Fraction(0), 2: Fraction(0), 3: Fraction(58, 100), 4: Fraction(90, 100), 5: Fraction(112, 100),
            6: Fraction(124, 100), 7: Fraction(132, 100), 8: Fraction(141, 100), 9: Fraction(145, 100),
            10: Fraction(149, 100)}   # Saaty's random index, the mean CI of random matrices of each order


def _judged(j):
    m = re.fullmatch(r'(1/)?([1-9])', str(j))
    return None if not m else (Fraction(1, int(m.group(2))) if m.group(1) else Fraction(int(m.group(2))))


def weights(entry):
    """(criteria, {criterion: weight}, λmax, CI, CR) of a weighing — the principal eigenvector, to PREC digits."""
    crit = [c['name'] for c in entry.get('criteria') or [] if isinstance(c, dict) and c.get('name')]
    n = len(crit)
    m = {(a, a): Fraction(1) for a in crit}
    for p in entry.get('pairwise') or []:
        if isinstance(p, dict) and p.get('a') in crit and p.get('b') in crit and _judged(p.get('judged')):
            m[(p['a'], p['b'])] = _judged(p['judged'])
            m[(p['b'], p['a'])] = 1 / _judged(p['judged'])
    with decimal.localcontext() as c:
        c.prec = PREC
        w = {a: decimal.Decimal(1) / n for a in crit}
        for _ in range(200):
            nw = {a: sum(D(m[(a, b)]) * w[b] for b in crit) for a in crit}
            s = sum(nw.values())
            nw = {a: x / s for a, x in nw.items()}
            if max(abs(nw[a] - w[a]) for a in crit) < decimal.Decimal(10) ** -30:
                w = nw
                break
            w = nw
        lam = sum(sum(D(m[(a, b)]) * w[b] for b in crit) / w[a] for a in crit) / n
    lam = F(lam)
    ci = (lam - n) / (n - 1) if n > 2 else Fraction(0)
    ri = SAATY_RI.get(n)
    cr = ci / ri if ri else Fraction(0)
    return crit, {a: F(x) for a, x in w.items()}, lam, ci, cr


def consistency_bound(form=None):
    """(the bound as written, as a Fraction): a weighing's consistency ratio at most, read from its form's row of the law
    (core/law/forms.yaml `weighing`, `at_most`) — the form given, or this release's."""
    if form is None:
        from core import read as _read
        form = ((_read.data(os.path.join(HERE, 'law', 'forms.yaml')) or {}).get('forms') or {}).get('weighing') or {}
    said = str(((form.get('at_most') or {}) if isinstance(form, dict) else {}).get('consistency_ratio'))
    return said, Fraction(said)


def check_weighing(where, entry, form=None):
    """Every pair of criteria judged once, each pair naming criteria; its consistency ratio at most the bound its form
    states (`consistency_bound`), or `why_inconsistent` says why not."""
    out = []
    if not isinstance(entry, dict):
        return out
    crit = [c.get('name') for c in entry.get('criteria') or [] if isinstance(c, dict)]
    seen = set()
    for p in entry.get('pairwise') or []:
        if not isinstance(p, dict):
            continue
        a, b = p.get('a'), p.get('b')
        for x in (a, b):
            if x not in crit:
                out.append(('error', f"{where}: the pair ({a}, {b}) names '{x}', which is not a criterion — {crit}"))
        if a == b:
            out.append(('error', f"{where}: a criterion is not judged against itself ({a})"))
        key = frozenset((a, b))
        if key in seen:
            out.append(('error', f"{where}: the pair ({a}, {b}) is judged twice — once each, in one direction"))
        seen.add(key)
    if out:
        return out
    missing = [(a, b) for i, a in enumerate(crit) for b in crit[i + 1:] if frozenset((a, b)) not in seen]
    if missing:
        return [('error', f"{where}: every pair of criteria is judged once — not judged: "
                          + ', '.join(f"({a}, {b})" for a, b in missing))]
    if len(crit) > 2:
        _c, _w, _l, _ci, cr = weights(entry)
        said, bound = consistency_bound(form)
        if cr > bound and not entry.get('why_inconsistent'):
            out.append(('error', f"{where}: its consistency ratio is {dmseq.rounded(cr, 2)}, above {said} — the judgments "
                                 f"contradict each other; judge again, or say in `why_inconsistent` why they stand"))
    return out


def check_pin(where, pin, *, root=ROOT, days=()):
    """A pin names a commit this garden has, an ancestor of HEAD, and a moment no later than the day it is recorded."""
    if not isinstance(pin, dict):
        return [('error', f"{where}: a pin is `{{commit, at}}` (pin_form)")]
    out = []
    c, at = pin.get('commit'), pin.get('at')
    if not isinstance(c, str) or not COMMIT.match(c):
        out.append(('error', f"{where}: the pin's commit is an object id, 7 to 40 hex digits — not {c!r}"))
    elif subprocess.run(['git', '-C', root, 'merge-base', '--is-ancestor', c, 'HEAD'], capture_output=True).returncode:
        out.append(('error', f"{where}: the pin's commit {c} is not an ancestor of HEAD — a reading is pinned to a "
                             f"commit the garden has"))
    if at != 'now':
        p = _pos(at, None, [])
        if p is None:
            out.append(('error', f"{where}: the pin's `at` is a moment, or `now` for the save to write — not {at!r}"))
        elif days:
            day = p[1] // dmcal.DAY_MS if p[0] == 'ms' else p[1]
            last = max(dmcal.to_day(d) for d in days)
            if day > last:
                out.append(('error', f"{where}: the pin's `at` ({at}) is later than the day this commit is stamped "
                                     f"({max(days)}) — a reading is not pinned to a moment still to come"))
    return out


# ============================================================================ the reckoner
class Reckoner:
    def __init__(self, garden, bean=None, inputs=None, pin=None, zone=None, now=None, rules_law=None):
        self.g, self.bean, self.pin, self.zone = garden, bean, pin, zone
        self.given = dict(inputs or {})
        self.now = now
        self.env, self.lines, self.notes = {}, [], []
        self.independent = False     # two or more uncertainties combined, each taken as independent of the others
        self.entered = {}          # member id -> the moment it entered, where a `reached` condition read one (AGREE)
        # A RULE'S READING is read by the law of the garden it judges (`rules_law`, a core.law.Law: the release's, with
        # the garden's own rows), never by the release's alone: the grammar, its tables and its inputs said by the law
        self.L = rules_law
        if rules_law is not None:
            from core import lines
            self.reg = lines.law_view(rules_law).registry
        else:
            self.reg = law().registry
        self.ops = op_rows(self.reg)
        self.k = k_factor(self.reg)

    # -- inputs
    def bind_inputs(self, decls):
        for d in decls or []:
            if not isinstance(d, dict):
                continue
            # WHERE AN INPUT COMES FROM (`origin`, `{act, nature?, alive?, by?}`): the reader's clock, another garden, or else
            # the asker's word — recorded on its line as said, and by what nature where the law says.
            n, o = d.get('name'), d.get('origin') if isinstance(d.get('origin'), dict) else {}
            if o.get('act') == 'read' and o.get('by') == dmpass.READER:
                at = self.pin.at if self.pin else (self.now or _now())
                self.env[n] = V(at)
                self.lines.append(f"input {n}: the clock, {at}")
            elif o.get('act') == 'said' and o.get('by') == dmpass.GARDEN:
                # ACROSS GARDENS (N35): read at a commit the other garden published and granted, never copied here; a
                # pin naming that garden reads it again at the pinned commit.
                import across as dmacross
                commit = self.pin.commit if self.pin and getattr(self.pin, 'garden', None) == d.get('garden') else None
                try:
                    got = dmacross.read(d.get('garden'), commit, d.get('path'), root=self.g.root)
                except (dmacross.NotHere, dmacross.NotPublished, dmacross.NotGranted) as e:
                    raise Refused(f"input {n} from the garden '{d.get('garden')}': {e}")
                if len(got) != 1:
                    raise Refused(f"input {n}: `{d.get('path')}` holds {len(got)} values in '{d.get('garden')}', where one is read")
                self.env[n] = value_of(got[0], f"{d.get('garden')}@{got.commit[:12]}:{d.get('path')}", self.notes)
                self.lines.append(f"input {n}: read in the garden {d.get('garden')} at {got.commit[:12]}, published and "
                                  f"granted — {show(self.env[n])}")
                self.across = getattr(self, 'across', []) + [(d.get('garden'), got.commit)]
            elif isinstance(d.get('from'), dict):
                # FROM AN EARLIER RULE (core 3.2, I.5): the members of a step of a rule before this one in the law's order
                r, st = d['from'].get('rule'), d['from'].get('step')
                done = (getattr(getattr(self.g, 'J', None), '_steps', None) or {}).get(r)
                if not isinstance(done, dict) or st not in done:
                    raise Refused(f"input {n}: the step `{st}` of the rule {r}, which was not read before this one")
                self.env[n] = done[st]
                self.lines.append(f"input {n}: the step {st} of the rule {r}, {self._said(done[st])}")
            elif o.get('act') == 'say' and o.get('by') == 'law':
                # SAID BY THE LAW (core 3.0; any table its columns declare, 3.2): the garden's own rows with it, each a
                # member, and the manifest's keys each with the garden's value
                J = getattr(self.g, 'J', None)
                self.env[n] = law_table(self._core_law(), n, getattr(getattr(J, 'G', None), 'manifest', None))
                self._sources[n] = f"law:{n}"
                self.lines.append(f"input {n}: the law's table, {len(self.env[n])} row(s)")
            elif n in self.given:
                self.env[n] = self._given(n, self.given[n], d)
                _nat = o.get('nature')
                self.lines.append(f"input {n}, said by the asker"
                                  + (f" ({'·'.join(_nat) if isinstance(_nat, list) else _nat})" if _nat else '')
                                  + f": {show(self.env[n])}")
            else:
                raise Refused(f"the reading takes the input '{n}', said by the asker, and it is not given — "
                              f"`--input {n}=<value>`" + (f", a value in {d['quantity']}" if d.get('quantity') else ''))

    def _given(self, n, raw, decl):
        if isinstance(raw, V):
            return raw
        if isinstance(raw, dict):
            return value_of(raw, f"input {n}", self.notes)
        s = str(raw).strip()
        m = re.fullmatch(r'(-?[0-9]+(?:\.[0-9]+)?)\s+([a-zA-Z][A-Za-z0-9_-]*)', s)
        if m:
            return V(dmseq.exact(m.group(1)), m.group(2))
        x = dmseq.exact(s)
        if x is not None:
            unit = law().coherent(decl.get('quantity')) if decl.get('quantity') else None
            return V(x, unit)
        return V(s)

    # -- names
    def arg(self, step, key, kind=None):
        n = step.get(key)
        if n not in self.env:
            raise Refused(f"step {step.get('id')}: `{key}: {n}` names no earlier step and no input")
        v = self.env[n]
        if kind == 'set' and not isinstance(v, list):
            raise Refused(f"step {step.get('id')}: `{key}: {n}` is not a set")
        return v

    def one(self, v, sid, key):
        if isinstance(v, list):
            if len(v) != 1:
                raise Refused(f"step {sid}: `{key}` holds {len(v)} members, where one value is read")
            return value_of(v[0].node, v[0].id, self.notes)
        if not isinstance(v, V):
            raise Refused(f"step {sid}: `{key}` is not a value")
        return v

    def operand(self, x):
        if isinstance(x, dict) and 'step' in x:
            v = self.env.get(x['step'])
            if v is None:
                raise Refused(f"`{x}` names no earlier step")
            return [m.id for m in v] if isinstance(v, list) else v
        if isinstance(x, dict) and 'input' in x:
            v = self.env.get(x['input'])
            if v is None:
                raise Refused(f"`{x}` names no input given")
            return v
        return x

    # -- the steps
    def run(self, entry):
        self.zone = entry.get('zone') or self.zone
        self.bind_inputs(entry.get('inputs'))
        last = None
        for s in entry.get('steps') or []:
            op = s.get('op')
            if op not in self.ops:
                raise Refused(f"step {s.get('id')}: `op: {op}` is not an operation of the law, and is not applied")
            fn = getattr(self, 'op_' + op.replace('-', '_'), None)
            if fn is None:
                raise Refused(f"step {s.get('id')}: the law lists `{op}`, and this reader does not apply it")
            last = (op, fn(s))
            self.env[s['id']] = last[1]
            self.lines.append(f"step {s['id']} ({op}): {self._said(last[1])}")
        return last

    def _said(self, v):
        if isinstance(v, list):
            return f"{len(v)} member(s)" + (': ' + ', '.join(m.id for m in v[:12]) + (' …' if len(v) > 12 else '') if v else '')
        if isinstance(v, dict):
            return '; '.join(f"{k}: {self._said(x)}" for k, x in v.items())
        if isinstance(v, V):
            return 'NOT KNOWN' if v.v is None and v.unit == 'truth' else show(v)
        if v is True or v is False:
            return str(v).lower()
        if v is None:
            return 'NOT KNOWN'
        return str(v)

    # sets
    def _core_law(self):
        """The core's law a rule's reading is read by, or the garden's own where the reading is a garden's."""
        if self.L is None and dmseq.runs_core(self.g.root or ROOT):
            self.L = dmseq.core(self.g.root or ROOT)[0]
        if self.L is None:
            raise Refused("an input said by the law is read in a garden of the core")
        return self.L

    def op_select(self, s):
        # THE ORDER THE GARDEN IS READ IN, where the garden says it (a rule's reading, `Judged`): else by id, as always
        seq = getattr(self.g, 'order', None)
        if 'of' in s:
            base = self.arg(s, 'of', 'set')
            if s['of'] in self._sources:               # rows of the law's table, still: an absence rests on it
                self._sources[s['id']] = self._sources[s['of']]
        else:
            base = [Member(i, fm, i) for i, fm in sorted(self.g.fm.items(), key=(lambda kv: seq[kv[0]]) if seq else None)
                    if self.g.kind[i] == 'beans'
                    and ('genos' not in s or fm.get('genos') == s['genos'])
                    and ('kind' not in s or fm.get('kind') == s['kind'])]
        if s.get('entries'):
            out = []
            places = getattr(self.g, 'places', None)
            for m in base:
                if m.bean in self._kept:
                    continue                       # a being of a store: its statements are read there, below
                for x, w in _flatten(walk(self.g, m.node, s['entries'], at=m.bean)):
                    hit = places.get(id(x)) if places is not None else None
                    out.append(Row(w, x, m.bean, place=hit[0], seq=hit[1], proof=(hit[0],)) if hit else
                               Member(w, x, m.bean))
            base = out
        if s.get('store') and 'of' not in s:      # ONE UNIVERSE: the beings and statements a store keeps, beside beans
            base = base + self._stored(s)
        elif s.get('store') and s.get('entries'):
            base = base + self._stored(s, of=[m.bean for m in self.arg(s, 'of', 'set') if m.bean in self._kept])
        return [m for m in base if self.meets(m, s.get('where') or [])]

    @property
    def _kept(self):
        return getattr(self, '_store_beings', set())

    def _stores(self, name):
        """The stores a step names — one this host declares, or `any`, each — opened read-only once a reading."""
        if not hasattr(self, '_opened'):
            self._opened = {}
        import store as dmstore
        names = sorted(dmstore.kept_here(self.g.root)) if name == 'any' else [name]
        out = []
        for n in names:
            if n not in self._opened:
                try:
                    self._opened[n] = dmstore.open_store(n, root=self.g.root, create=False)
                except Exception as e:          # noqa: BLE001 — a store not kept here is said, and read as empty
                    self.notes.append(f"the store {n} is not read here: {e}")
                    self._opened[n] = None
            if self._opened[n] is not None:
                out.append(self._opened[n])
        if name != 'any' and not out:
            raise Refused(f"the store `{name}` is not kept on this host: a reading that names it is read where it is")
        return out

    def _stored(self, s, of=None):
        """Members from the stores `s` names: its beings of the kind, or — with `entries`, a verb — their statements of
        that verb, each a member `<being>#<id>` whose node is its roles, as a bean's entry is."""
        out = []
        self._store_beings = set(self._kept)
        for st in self._stores(str(s['store'])):
            if of is None:                       # each being with what the store says of it: its kind, title, summary
                q = "SELECT id, kind, title, summary FROM being" + (" WHERE kind = ?" if s.get('kind') else "")
                rows = st.db.execute(q, (s['kind'],) if s.get('kind') else ()).fetchall()
            else:
                rows = [(i, None, None, None) for i in of]
            ids = [r[0] for r in rows]
            self._store_beings |= set(ids)
            verb = s.get('entries')
            if not verb:
                out += [Member(i, {k: v for k, v in (('bean', i), ('kind', kd), ('title', t), ('summary', sm)) if v}, i)
                        for i, kd, t, sm in rows]
                continue
            if verb not in st.verbs():
                continue
            want = set(ids)
            for being, sid, roles in st.statements_of(verb):
                if being in want:
                    out.append(Member(f"{being}#{sid}", roles, being))
        return out

    def meets(self, m, conds):
        for c in conds:
            comp = next(k for k in c if k != 'path')
            if not self.cond(m, c['path'], comp, self.operand(c[comp])):
                return False
        return True

    def cond(self, m, path, comp, operand):
        if comp in ('reached', 'at_step') and isinstance(operand, str) and '#' in operand:
            return self._core_course(m, comp, operand, path)   # a step named as a statement: a garden of the core
        found = walk(self.g, m.node, path, at=m.bean)
        vals = [x for x, _ in found]
        if comp in NEGATED:
            return not self.cond(m, path, NEGATED[comp], operand)
        if comp in ('<', '>'):
            return any((c := self._cmp(x, operand)) is not None and (c < 0 if comp == '<' else c > 0) for x in vals)
        if comp == 'exists':
            return bool(vals) and any(x is not None for x in vals)
        if comp == 'absent':
            return not vals or all(x is None for x in vals)
        if comp in ('reached', 'at_step'):
            return any(self._course(m, w, comp, operand) for x, w in found)
        if comp == 'fits':
            return any(self._fits(y, operand) for x in vals for y in (x if isinstance(x, list) else [x]))
        return any(self._one_cond(x, comp, operand) for x in vals)

    def _fits(self, x, spec):
        """Whether the value `x` is in the one form of the row `spec` names (core/law.py `Law.fits`, core 3.2, I.3)."""
        import parse as _p
        try:
            return self._core_law().fits(spec, x)
        except ValueError as e:
            raise Refused(f"`fits: {spec}`: {e}")
        except _p.CheckUnavailable as e:
            raise Refused(f"`fits: {spec}` cannot be read here: {e}")

    def _one_cond(self, x, comp, operand):
        if comp == 'is':
            return self._eq(x, operand)
        if comp == 'in':
            return any(self._eq(x, o) for o in (operand if isinstance(operand, list) else [operand]))
        if comp == 'refers_to':
            t = operand.v if isinstance(operand, V) else operand
            return _ref_bean(x) == (t.get('bean') if isinstance(t, dict) else t)
        if comp in ('at_least', 'at_most'):
            c = self._cmp(x, operand)
            return c is not None and (c >= 0 if comp == 'at_least' else c <= 0)
        raise Refused(f"the comparator `{comp}` is not one this reader applies")

    def _eq(self, x, o):
        o = o.v if isinstance(o, V) and o.unit is None else o
        x = _text(x) if _long(x) else x
        if isinstance(o, V) or (isinstance(x, dict) and 'count' in x):
            return self._cmp(x, o) == 0
        if isinstance(x, dict) and 'bean' in x:
            return x['bean'] == (o.get('bean') if isinstance(o, dict) else o)
        return str(x) == str(o) if not isinstance(o, (list, dict)) else x == o

    def _cmp(self, x, o):
        a = value_of(x, 'a value', self.notes) if not isinstance(x, V) else x
        b = o if isinstance(o, V) else value_of(o, 'an operand', self.notes)
        if isinstance(a.v, Fraction) and isinstance(b.v, Fraction):
            if a.unit != b.unit:
                # two quantities of different kinds are not compared, and a member is not quietly left out for it:
                # the reading is refused, as `min`, `max` and `order` refuse it (to_unit says which two)
                b = to_unit(b, a.unit, 'a comparison')
            return (a.v > b.v) - (a.v < b.v)
        if isinstance(a.v, str) and isinstance(b.v, str):
            try:
                return pos_cmp(a.v, b.v, self.zone)
            except Refused:
                return None
        return None

    def _core_course(self, m, comp, ref, path=''):
        """reached / at_step in a garden of the core: each course of the member's bean on the walk `ref` names
        (`<walk>#<step>`) — the one the path names, `be[id=<course>]`, where it names one — read from its moves."""
        wid, step = ref.split('#', 1)
        only = re.match(r'^be\[id=([a-z0-9][a-z0-9_-]*)\]$', path or '')
        fm = self.g.bean(m.bean)
        return any(self._course(m, f"{m.bean}:courses.{k}", comp, step)
                   for k, c in (fm.get('courses') or {}).items()
                   if c.get('walk') == wid and (not only or k == only.group(1)))

    def _course(self, m, where, comp, step):
        """reached / at_step on the course at `where` (`<bean>:courses.<key>`): read from the bean's moves and its walk."""
        bean = where.split(':', 1)[0]
        key = where.rsplit('.', 1)[-1]
        fm = self.g.bean(bean)
        course = (fm.get('courses') or {}).get(key) if isinstance(fm.get('courses'), dict) else None
        if not isinstance(course, dict):
            raise Refused(f"{where} is not a course: `reached` and `at_step` read a course's moves")
        moves = [x for x in fm.get('moves') or [] if isinstance(x, dict) and x.get('course') == key]
        if not moves:
            return False
        if comp == 'at_step':
            return moves[-1].get('step') == step
        ref = (course.get('walk') or {}) if isinstance(course.get('walk'), dict) else {'bean': course.get('walk')}
        wfm = self.g.fm.get(ref.get('mapping') or ref.get('bean')) or {}
        nxt = {x.get('id'): [n.get('to') for n in x.get('next') or [] if isinstance(n, dict)]
               for x in wfm.get('steps') or [] if isinstance(x, dict)}
        reach, todo = {step}, [step]
        while todo:
            for t in nxt.get(todo.pop(), []):
                if t not in reach:
                    reach.add(t)
                    todo.append(t)
        hit = [x for x in moves if x.get('step') in reach]
        if hit and hit[0].get('at') is not None:
            # WHEN IT ENTERED: the first move into the reach — the latest such moment across the conditions it meets
            at = _text(hit[0]['at'])
            prev = self.entered.get(m.id)
            if at is not None:                  # a move placed only by its neighbours (27.0) says no moment it entered
                at = str(at)
                self.entered[m.id] = at if prev is None or pos_cmp(prev, at, self.zone) < 0 else prev
        return bool(hit)

    def op_intersect(self, s):
        b = {m.id for m in self.arg(s, 'with', 'set')}
        return [m for m in self.arg(s, 'of', 'set') if m.id in b]

    def op_union(self, s):
        a = self.arg(s, 'of', 'set')
        ids = {m.id for m in a}
        return a + [m for m in self.arg(s, 'with', 'set') if m.id not in ids]

    def op_minus(self, s):
        b = {m.id for m in self.arg(s, 'with', 'set')}
        return [m for m in self.arg(s, 'of', 'set') if m.id not in b]

    def _each_group(self, s, fn):
        x = self.env.get(s.get('of'))
        if isinstance(x, dict):
            return {k: fn(v) for k, v in x.items()}
        return fn(self.arg(s, 'of', 'set'))

    def op_count(self, s):
        return self._each_group(s, lambda ms: V(Fraction(len(ms)), 'item'))

    def _at(self, m, path, sid):
        found = walk(self.g, m.node, path, at=m.bean)
        if len(found) != 1:
            raise Refused(f"step {sid}: {m.id} holds {len(found)} values at `{path}`, where one is read")
        v = value_of(found[0][0], found[0][1], self.notes)
        v.member = m.id
        self.lines.append(f"  {found[0][1]} = {show(v)}")
        return v

    def op_sum(self, s):
        def total(ms):
            vs = [self._at(m, s['path'], s['id']) for m in ms]
            bad = [v.member for v in vs if not isinstance(v.v, Fraction) or v.unit is None]
            if bad:
                raise Refused(f"step {s['id']}: the value at `{s['path']}` of {bad} is not a quantity, and the sum is refused")
            if not vs:
                return V(Fraction(0))
            unit = vs[0].unit
            vs = [to_unit(v, unit, f"step {s['id']}") for v in vs]
            return V(sum(v.v for v in vs), unit, self.hyp(*[v.u for v in vs]),
                     any(v.approx for v in vs), {v.member: v.u * v.u for v in vs if v.u})
        return self._each_group(s, total)

    def _extreme(self, s, pick):
        vs = [self._at(m, s['path'], s['id']) for m in self.arg(s, 'of', 'set')]
        if not vs:
            raise Refused(f"step {s['id']}: the set is empty, and holds no least or greatest value")
        best = vs[0]
        for v in vs[1:]:
            c = self._cmp(v, best)
            if c is None:
                raise Refused(f"step {s['id']}: {v.member} and {best.member} are not ordered one against the other")
            if pick(c):
                best = v
        self.lines.append(f"  held by {best.member}")
        return best

    def op_min(self, s):
        return self._extreme(s, lambda c: c < 0)

    def op_max(self, s):
        return self._extreme(s, lambda c: c > 0)

    def op_order(self, s):
        ms = self.arg(s, 'of', 'set')
        keyed = [(self._at(m, s['path'], s['id']), m) for m in sorted(ms, key=lambda m: m.id)]
        import functools

        def text(v):
            v = v.v if isinstance(v, V) else v
            return v if isinstance(v, str) else None

        def cmp(a, b):
            c = self._cmp(a[0], b[0])
            if c is None and text(a[0]) is not None and text(b[0]) is not None:
                # TEXT IS ORDERED BY ITS CHARACTERS — case aside first, then exactly — where it is no position of the
                # law's: a title, a name. Two positions of different systems are still not ordered.
                ka, kb = (unicodedata.normalize('NFC', text(x[0])) for x in (a, b))
                c = ((ka.casefold(), ka) > (kb.casefold(), kb)) - ((ka.casefold(), ka) < (kb.casefold(), kb))
            if c is None:
                raise Refused(f"step {s['id']}: {a[1].id} and {b[1].id} are not ordered one against the other")
            return c
        keyed.sort(key=functools.cmp_to_key(cmp), reverse=s.get('direction') == 'descending')
        return [m for _v, m in keyed]

    def op_group(self, s):
        if s.get('gap') is not None:
            return self._gap_groups(s)
        out = {}
        for m in self.arg(s, 'of', 'set'):
            found = walk(self.g, m.node, s['path'], at=m.bean)
            if len(found) != 1:
                raise Refused(f"step {s['id']}: {m.id} holds {len(found)} values at `{s['path']}`, where one groups it")
            x = found[0][0]
            label = self._cell(x, s) if s.get('level') else (x.get('bean') if isinstance(x, dict) and 'bean' in x else str(x))
            out.setdefault(label, []).append(m)
        return dict(sorted(out.items()))

    def _span(self, x):
        """(start, end) in seconds of a position: a moment its instant; a day the whole of it, in the reading's zone
        (UTC where it states none)."""
        p = _pos(x, self.zone, self.notes)
        if p is None:
            return None
        if p[0] == 'ms':
            return p[1] / 1000, p[1] / 1000
        off = dmcal.offset(self.zone, f"{dmcal.shown(x)}T12:00:00+00:00") if self.zone else 0
        start = (p[1] * dmcal.DAY_MS - off * 60000) / 1000
        return start, start + 86400 - 0.001

    def _gap_groups(self, s):
        """`group` with `gap`: the members in the order of the moment at the path, a new group after a longer gap."""
        from core import storage
        gap = self._value(s, 'gap')
        q = gap if isinstance(gap, dict) else None
        if q is None and isinstance(gap, str):
            m = re.fullmatch(r'\s*(\d+(?:\.\d+)?) (\S+)\s*', gap)
            q = {'count': m.group(1), 'unit': m.group(2)} if m else None
        secs = _duration_seconds(q)
        if secs is None:
            raise Refused(f"step {s['id']}: `gap` is a length of time, a count and a unit of duration: {gap!r}")
        spans, none = [], []
        for m in self.arg(s, 'of', 'set'):
            found = walk(self.g, m.node, s['path'], at=m.bean)
            sp = self._span(found[0][0]) if len(found) == 1 else None
            if sp is None:
                none.append(m)
            else:
                spans.append((sp[0], sp[1], m))
        out = {}
        for g in storage.gap_groups([(a, b, m) for a, b, m in spans], secs):
            first = min(self._span(walk(self.g, m.node, s['path'], at=m.bean)[0][0])[0] for m in g)
            last = max(self._span(walk(self.g, m.node, s['path'], at=m.bean)[0][0])[1] for m in g)
            out[f"{_shown_secs(first)}–{_shown_secs(last)}"] = g
        if none:
            self.notes.append(f"step {s['id']}: {len(none)} member(s) hold no moment at `{s['path']}`, in no group: "
                              + ', '.join(m.id for m in none[:8]) + ('…' if len(none) > 8 else ''))
        return out

    def _cell(self, x, s):
        """The cell of a calendar level a moment or a day falls in, read in the reading's zone. `system` is a row of the
        law's `anchor_systems`, read through the calendar that row names; absent, the civil Gregorian one."""
        sysname = s.get('system') or 'gregorian-civil'
        _row = next((r for r in (self.reg('anchor_systems') or []) if isinstance(r, dict) and r.get('system') == sysname), None)
        cal = (_row or {}).get('calendar') or sysname
        p = _pos(x, self.zone, self.notes)
        if p is None:
            raise Refused(f"step {s['id']}: {x!r} is no position of time, and falls in no {s['level']}")
        if p[0] == 'ms':
            if not self.zone:
                raise Refused(f"step {s['id']}: a moment falls in a {s['level']} of a civil zone — the reading states `zone`")
            day = _local_day(p[1], self.zone, x)
        else:
            day = p[1]
        parts = dmcal.from_day(day, cal).split('-')
        n = {'year': 1, 'month': 2, 'day': 3}.get(s['level'])
        if n is None or len(parts) < n:
            raise Refused(f"step {s['id']}: the level '{s['level']}' of {cal} is not one this reader cuts cells by "
                          f"(year, month, day)")
        return '-'.join(parts[:n])

    # truths
    def op_some(self, s):
        return any(self.meets(m, s.get('where') or []) for m in self.arg(s, 'of', 'set'))

    def op_all(self, s):
        return all(self.meets(m, s.get('where') or []) for m in self.arg(s, 'of', 'set'))

    def op_not(self, s):
        v = self.env.get(s['of'])
        if isinstance(v, list):
            return not v
        return None if v is None else not v

    def op_compare(self, s):
        a, b = self.one(self.arg(s, 'of'), s['id'], 'of'), self.one(self.arg(s, 'with'), s['id'], 'with')
        if not isinstance(a.v, Fraction) or not isinstance(b.v, Fraction):
            c = pos_cmp(a.v, b.v, self.zone)
            return {'less': c < 0, 'at-most': c <= 0, 'equal': c == 0, 'at-least': c >= 0, 'greater': c > 0}[s['is']]
        b = to_unit(b, a.unit, f"step {s['id']}") if a.unit != b.unit else b
        d = a.v - b.v
        if s['is'] == 'equal' and s.get('band') is not None:
            band = to_unit(value_of(s['band'], f"step {s['id']}.band", self.notes), a.unit, f"step {s['id']}.band").v
            ud = self.hyp(a.u, b.u)
            self.lines.append(f"  |Δ| = {dmseq.show(abs(d))}" + (f", u(Δ) {dmseq.rounded(ud, dmseq.u_places(ud))}, "
                              f"k·u(Δ) {dmseq.rounded(self.k * ud, dmseq.u_places(ud))}" if ud else '')
                              + f", band {dmseq.show(band)}")
            if abs(d) > band:
                return False
            if ud is not None and self.k * ud > band:
                self.notes.append(f"step {s['id']}: within the band, and its uncertainty cannot resolve it "
                                  f"(k·u(Δ) > band): NOT KNOWN")
                return None
            return True
        return {'less': d < 0, 'at-most': d <= 0, 'equal': d == 0, 'at-least': d >= 0, 'greater': d > 0}[s['is']]

    # values
    def op_read(self, s):
        if 'of' in s:
            ms = self.arg(s, 'of', 'set')
            if len(ms) != 1:
                raise Refused(f"step {s['id']}: `of` holds {len(ms)} members, and `read` reads the one")
            return self._at(ms[0], s['path'], s['id'])
        if not self.bean:
            raise Refused(f"step {s['id']}: `read` with no `of` reads the bean the reading is read from, and there is none")
        return self._at(Member(self.bean, self.g.bean(self.bean), self.bean), s['path'], s['id'])

    def op_constant(self, s):
        return value_of(s['value'], f"step {s['id']}.value", self.notes)

    def _two(self, s):
        return self.one(self.arg(s, 'of'), s['id'], 'of'), self.one(self.arg(s, 'with'), s['id'], 'with')

    def op_difference(self, s):
        a, b = self._two(s)
        b = to_unit(b, a.unit, f"step {s['id']}")
        return V(a.v - b.v, a.unit, self.hyp(a.u, b.u), a.approx or b.approx, {**a.budget, **b.budget} or budget(
            **{s.get('of'): a.u, s.get('with'): b.u}))

    def hyp(self, *us):
        """`hyp`, and a record that two or more uncertainties were combined as independent ones, which the result says."""
        if sum(u is not None for u in us) >= 2:
            self.independent = True
        return hyp(*us)

    def _rel(self, r, a, b, na, nb):
        """The relative rule: u(r)/|r| = √((u(a)/a)² + (u(b)/b)²)."""
        parts = {}
        for n, x in ((na, a), (nb, b)):
            if x is not None and x.u is not None and x.v:
                parts[n] = (x.u / abs(x.v)) ** 2 * r * r
        if len(parts) >= 2:
            self.independent = True
        u = sqrt(sum(parts.values()))[0] if parts else None
        return u, parts

    def op_multiply(self, s):
        a = self.one(self.arg(s, 'of'), s['id'], 'of')
        if 'with' in s:
            b = self.one(self.arg(s, 'with'), s['id'], 'with')
        elif 'coefficient' in s:
            b = self._coefficient(s['coefficient'], None, s['id'])
        elif 'count' in s:
            b = V(dmseq.exact(s['count']) if not isinstance(s['count'], int) else Fraction(s['count']))
        else:
            raise Refused(f"step {s['id']}: `multiply` takes `with`, `coefficient` or `count`")
        return self._product(a, b, 1, s)

    def _product(self, a, b, sign, s):
        what = f"step {s['id']}"
        lw = law()

        def bare(x):                                       # a count or a share: no dimension, and no currency
            return x.unit in (None, 'one', 'item') or lw.quantity_of(x.unit) in ('ratio', 'number')
        if bare(b) or (bare(a) and sign > 0):
            # a factor with no dimension scales the other and keeps ITS unit: 3 mm × 2 is 6 mm, not 0.006 m
            k, x = (b, a) if bare(b) else (a, b)
            kv = to_unit(k, 'one', what).v if k.unit not in (None, 'item') and lw.quantity_of(k.unit) == 'ratio' else k.v
            if sign < 0 and kv == 0:
                raise Refused(f"{what}: divided by zero")
            r = x.v * kv if sign > 0 else x.v / kv
            unit = x.unit if not bare(x) else ('item' if sign > 0 and 'item' in (a.unit, b.unit) else
                                               (None if x.unit is None and k.unit is None else 'one'))
            kk = V(kv, None, None if k.u is None else (k.u if k.unit in (None, 'item') or lw.quantity_of(k.unit) != 'ratio'
                                                        else to_unit(k, 'one', what).u))
            u, parts = self._rel(r, x, kk, s.get('of') if x is a else (s.get('with') or 'count'),
                                 s.get('with') or s.get('coefficient') or 'count' if k is b else s.get('of'))
            return V(r, unit, u, a.approx or b.approx, parts)
        ca, cb = _coherent(a, what), _coherent(b, what)
        da, db = _dims(ca.unit), _dims(cb.unit)
        money = [x for x in (ca, cb) if x.unit and lw.factor(x.unit) is None]
        if money:
            other = cb if money[0] is ca else ca
            if len(money) == 2 and sign > 0 or (other.unit and _dims(other.unit)):
                if not (sign < 0 and len(money) == 2 and ca.unit == cb.unit):
                    raise Refused(f"{what}: {a.unit} {'×' if sign > 0 else '÷'} {b.unit} — money is multiplied or divided "
                                  f"by a count or a share, and one currency by itself")
            if sign < 0 and len(money) == 2:
                unit = 'one'
            else:
                unit = money[0].unit
        else:
            if da is None or db is None:
                raise Refused(f"{what}: {a.unit} or {b.unit} is no unit of a quantity with dimensions")
            unit = _unit_for({k: da.get(k, 0) + sign * db.get(k, 0) for k in set(da) | set(db)}, what)
            if unit == 'one' and (ca.unit in ('item',) or cb.unit in ('item',)) and sign > 0:
                unit = 'item' if ca.unit == 'item' or cb.unit == 'item' else unit
        if sign < 0 and cb.v == 0:
            raise Refused(f"{what}: divided by zero")
        r = ca.v * cb.v if sign > 0 else ca.v / cb.v
        u, parts = self._rel(r, ca, cb, s.get('of'), s.get('with') or s.get('coefficient') or 'count')
        return V(r, unit, u, ca.approx or cb.approx, parts)

    def op_divide(self, s):
        a, b = self._two(s)
        return self._product(a, b, -1, s)

    def op_power(self, s):
        a = self.one(self.arg(s, 'of'), s['id'], 'of')
        e = s.get('exponent')
        e = Fraction(e) if isinstance(e, int) else dmseq.exact(e)
        if e is None:
            raise Refused(f"step {s['id']}: the exponent is a count")
        what = f"step {s['id']}"
        ca = _coherent(a, what)
        d = _dims(ca.unit) or {}
        if e.denominator == 1:
            if ca.v == 0 and e < 0:
                raise Refused(f"{what}: zero to a negative power")
            r, approx = ca.v ** int(e), ca.approx
        else:
            if ca.v <= 0:
                raise Refused(f"{what}: a power that is not whole of a value that is not positive")
            with decimal.localcontext() as c:
                c.prec = PREC
                r = F(D(ca.v) ** D(e))
            approx = True
        dims = {k: v * e for k, v in d.items()}
        if any(Fraction(v).denominator != 1 for v in dims.values()):
            raise Refused(f"{what}: {a.unit} to the power {dmseq.show(e)} has no unit in the law")
        unit = _unit_for({k: int(v) for k, v in dims.items()}, what) if dims else ca.unit if ca.unit in ('one', None) else 'one'
        u = abs(e) * ca.u / abs(ca.v) * abs(r) if ca.u is not None and ca.v else None
        return V(r, unit, u, approx)

    def op_square_root(self, s):
        a = _coherent(self.one(self.arg(s, 'of'), s['id'], 'of'), f"step {s['id']}")
        r, ex = sqrt(a.v)
        d = _dims(a.unit) or {}
        if any(v % 2 for v in d.values()):
            raise Refused(f"step {s['id']}: the square root of {a.unit} has no unit in the law")
        unit = _unit_for({k: v // 2 for k, v in d.items()}, f"step {s['id']}") if d else a.unit
        u = a.u / (2 * r) if a.u is not None and r else None
        return V(r, unit, u, a.approx or not ex)

    def _dimensionless(self, s):
        a = self.one(self.arg(s, 'of'), s['id'], 'of')
        if a.unit not in (None, 'one') and _dims(a.unit) != {}:
            raise Refused(f"step {s['id']}: `{s['op']}` reads a number with no dimension, and {a.unit} has one")
        return to_unit(a, 'one', f"step {s['id']}") if a.unit not in (None, 'one') else a

    def op_exp(self, s):
        a = self._dimensionless(s)
        with decimal.localcontext() as c:
            c.prec = PREC
            r = F(D(a.v).exp())
        return V(r, 'one', a.u * r if a.u is not None else None, True)

    def op_ln(self, s):
        a = self._dimensionless(s)
        if a.v <= 0:
            raise Refused(f"step {s['id']}: the logarithm of a value that is not positive")
        with decimal.localcontext() as c:
            c.prec = PREC
            r = F(D(a.v).ln())
        return V(r, 'one', a.u / a.v if a.u is not None else None, True)

    def op_convert(self, s):
        return to_unit(self.one(self.arg(s, 'of'), s['id'], 'of'), s['unit'], f"step {s['id']}")

    def _coefficient(self, name, code, sid):
        rows = [r for r in (self.reg('coefficients') or []) if isinstance(r, dict) and r.get('coefficient') == name]
        if code is not None:
            # a row's cases are codings (29.0); what is looked up is a coding, or a code alone where the path holds one
            rows = [r for r in rows if any(w == code if dmparse.split_coding(code)[0] else dmparse.split_coding(w)[1] == str(code)
                                           for w in r.get('where') or [])]
        if len(rows) != 1:
            raise Refused(f"step {sid}: {len(rows)} row(s) of `coefficients` are '{name}'"
                          + (f" where the code is {code}" if code is not None else '') + " — one is read")
        r = rows[0]
        v = V(dmseq.exact(r.get('count')), r.get('unit'))
        u = r.get('u')
        if isinstance(u, dict) and u.get('bounds'):
            lo, hi = (dmseq.exact(x) for x in u['bounds'])
            v.u = sqrt((hi - lo) ** 2 / 12)[0]
            self.notes.append(f"coefficient {name}: bounds read as a rectangle, u (b−a)/√12")
        elif u is not None:
            v.u = dmseq.exact(u.get('count') if isinstance(u, dict) else u)
        self.lines.append(f"  coefficient {name} = {show(v)} ({(r.get('source') or {}).get('cite', 'no source')})")
        return v

    def op_lookup(self, s):
        where = s['where']
        m = Member(self.bean, self.g.bean(self.bean), self.bean) if self.bean else None
        found = walk(self.g, m.node, where, at=m.bean) if m else []
        if len(found) != 1:
            raise Refused(f"step {s['id']}: `{where}` holds {len(found)} codes, where one selects the row")
        code = found[0][0].get('code') if isinstance(found[0][0], dict) else found[0][0]
        return self._coefficient(s['coefficient'], code, s['id'])

    def op_elapsed(self, s):
        a, b = self._two(s)
        pa, pb = _pos(a.v, self.zone, self.notes), _pos(b.v, self.zone, self.notes)
        if pa is None or pb is None or pa[0] != pb[0]:
            raise Refused(f"step {s['id']}: `elapsed` reads two positions of one time system — two moments, or two days")
        res = {}
        for n, x in (('of', a.v), ('with', b.v)):
            if pa[0] == 'day':
                res[n] = Fraction(86400)
            else:
                res[n] = {'minute': Fraction(60), 'second': Fraction(1), 'millisecond': Fraction(1, 1000)}[dmcal.moment(x).resolution]
        secs = Fraction(pa[1] - pb[1]) * (86400 if pa[0] == 'day' else Fraction(1, 1000))
        u = self.hyp(*[sqrt(r * r / 12)[0] for r in res.values()])
        return to_unit(V(secs, 'second', u), s['unit'], f"step {s['id']}")

    def _geo(self, position, sid):
        """A place position as a coordinate, a `relative` one resolved through the being it is stated from, at the
        reading's moment — place is read AT a time (24.0, PLACE)."""
        import geo as dmgeo
        try:
            if dmgeo.RELATIVE.match(str(position)):
                return dmgeo.resolve_relative(str(position), root=self.g.root, beans=self.g.fm, moment=self.now)
            dmgeo.parse(str(position), self.g.root)             # refused here if it is not a coordinate
            return str(position)
        except ValueError as e:
            raise Refused(f"step {sid}: {e}") from None

    def _metres(self, measure, sid):
        return to_unit(value_of(measure, sid, self.notes), 'metre', f"step {sid}").v

    def op_within(self, s):
        if 'place' in s:
            import geo as dmgeo
            pl = s['place'] if isinstance(s['place'], dict) else {}
            if pl.get('at') is None or not isinstance(pl.get('distance'), dict):
                raise Refused(f"step {s['id']}: `within` a place is {{at: <a place>, distance: {{count, unit}}}}")
            here, d = self._geo(pl['at'], s['id']), self._metres(pl['distance'], s['id'])
            out = []
            for m in self.arg(s, 'of', 'set'):
                for x, _w in walk(self.g, m.node, s['path'], at=m.bean):
                    try:
                        if dmgeo.distance(self._geo(x, s['id']), here, self.g.root) <= d:
                            out.append(m)
                            break
                    except ValueError as e:
                        raise Refused(f"step {s['id']}: {m.id}: {e}") from None
            self.notes.append(f"step {s['id']}: distances great-circle on the body's mean sphere (≈)")
            return out
        ext = s.get('extent') or {}
        a, b = ext.get('from'), ext.get('to')
        out = []
        for m in self.arg(s, 'of', 'set'):
            for x, _w in walk(self.g, m.node, s['path'], at=m.bean):
                if (a is None or pos_cmp(x, a, self.zone) >= 0) and (b is None or pos_cmp(x, b, self.zone) <= 0):
                    out.append(m)
                    break
        return out

    def _code_members(self, s):
        out = []
        for m in self.arg(s, 'of', 'set'):
            n = m.node
            sch, code = dmparse.split_coding(n)
            if sch is not None:
                out.append((sch, code, m))
            else:
                raise Refused(f"step {s['id']}: {m.id} is not a code with its scheme (`<scheme>:<code>`)")
        return out

    def _ancestor(self, scheme, code, level):
        """The code's ancestor at `level` in its scheme (the code itself where it is at that level), by `parent` — or None."""
        sys.path.insert(0, ROOT)
        from core import reach
        rows = {str(r.get('code', r.get('unit'))): r for r in (self.reg(scheme) or []) if isinstance(r, dict)}
        up = [str(code)] + [c for c, _via in reach.Reach(str(code), lambda c: [str(rows[c].get('parent') or '')]
                                                         if c in rows else [])]
        for c in up:
            if c not in rows:
                return None
            if level in (rows[c].get('level'), rows[c].get('rank')):
                return c
        return None

    def op_books(self, s):
        """EACH ACCOUNT'S NET CHARGE THROUGH A DAY (the accounting profile's): what arrived less what left, per account
        of the chart and per currency, read by the profile's asset (assets/accounting/lib/books_read.py) as the books
        read now — a reading of it pinned (`pin`) is the books closed through that day. With `party`, one party's alone:
        its part of each account that holds parties — the party a bean, or an input or step naming one (a page's sheet
        gives the being it shows). Refused in a garden that does not hold the asset: the books are read by it."""
        lib = os.path.join(ROOT, 'assets', 'accounting', 'lib')
        if not os.path.isfile(os.path.join(lib, 'books_read.py')):
            raise Refused(f"step {s['id']}: the books are read by the accounting profile's asset, which this garden "
                          f"does not hold (VOCAB.md `profiles: [accounting]`)")
        if lib not in sys.path:
            sys.path.insert(0, lib)
        import books_read
        import stale as dmstale
        through = s['to']
        if isinstance(through, str) and through in self.env:      # an input naming the day: the reader's clock, or said
            x = self.env[through]
            through = str(x.v) if isinstance(x, V) else str(x)
        try:
            to = dmstale.day_of(through)
            B = books_read.read(ROOT, entity=s.get('entity'), chart=s.get('chart'), today=to, pinned=False)
        except ValueError as e:
            raise Refused(f"step {s['id']}: {e}")
        party = s.get('party')
        if party is not None:
            pv = self.env.get(party, party)
            if isinstance(pv, list):
                if len(pv) != 1:
                    raise Refused(f"step {s['id']}: `party: {party}` holds {len(pv)} members, where one party is read")
                pv = pv[0].id
            pv = str(pv.v) if isinstance(pv, V) else str(pv)
            if pv not in self.g.kind:
                raise Refused(f"step {s['id']}: `party: {pv}` is no bean of this garden")
            party = pv
        out = {}
        for unit in sorted({v['unit'] for v in B.vouchers if v['unit']}):
            for r in books_read.trial(B, unit, None, to)['rows']:
                if party is not None:
                    q = next((x for x in r.get('parties') or [] if x['party'] == party), None)
                    if q is not None:
                        out[f"{r['code']} {unit}"] = V(q['closing'], unit)
                elif r['posts']:
                    out[f"{r['code']} {unit}"] = V(r['closing'], unit)
        self.lines.append(f"  the books of {B.entity} in {B.chart.scheme} through {through}"
                          + (f", {party}'s part" if party is not None else '') + f": {len(out)} account(s)")
        return out

    def op_apportion(self, s):
        """EACH CODE'S PART OF THE AMOUNTS (28.1): a member's amount shared over its entries at `over` — by an entry's share of
        its group's shares, a group being the codes under one ancestor at `per` (the scheme's first level: a plan), or by an
        entry's own amount — and summed per code, or per the ancestor at `level`. Exact, in fractions; `digits: true` writes
        each part in the currency's places, the cents a split leaves over going to the largest remainders, first code first.
        What an account holds is read here, never stored."""
        out, unit = {}, None
        firsts = {str(r.get('scheme')): ((r.get('levels') or [{}])[0] or {}).get('level')
                  for r in (self.reg('knowledge_schemes') or []) if isinstance(r, dict)}
        cur = {str(r.get('code')): r for r in (self.reg('currencies') or []) if isinstance(r, dict)}
        for m in self.arg(s, 'of', 'set'):
            got = [x for x, _w in walk(self.g, m.node, s['amount'], at=m.bean)]
            if len(got) != 1:
                raise Refused(f"step {s['id']}: {m.id} holds {len(got)} values at `{s['amount']}`, where one amount is shared")
            amt = value_of(got[0], f"{m.id}.{s['amount']}", self.notes)
            if not isinstance(amt.v, Fraction) or amt.unit is None:
                raise Refused(f"step {s['id']}: {m.id}.{s['amount']} is no amount")
            if unit is not None and amt.unit != unit:
                raise Refused(f"step {s['id']}: the amounts are in {unit} and {amt.unit} — apportion within one currency")
            unit = amt.unit
            groups = {}
            for d, _w in _flatten(walk(self.g, m.node, s['over'], at=m.bean)):
                if not isinstance(d, dict) or dmparse.split_coding(d.get('code'))[0] is None:
                    continue
                sch, code = dmparse.split_coding(d['code'])
                lv = s.get('per') or firsts.get(sch)
                k = self._ancestor(sch, code, lv) if lv else None
                if k is None:
                    raise Refused(f"step {s['id']}: {d['code']} of {m.id} has no ancestor at `{lv}`")
                groups.setdefault(k, []).append(d)
            for k, ds in groups.items():
                if all(d.get('amount') is not None for d in ds):
                    parts = [(d, value_of(d['amount'], f"{m.id}", self.notes).v) for d in ds]
                elif all(d.get('share') is not None for d in ds):
                    tot = sum(Fraction(int(str(d['share']))) for d in ds)
                    parts = [(d, amt.v * Fraction(int(str(d['share']))) / tot) for d in ds]
                    places = (cur.get(unit) or {}).get('digits')
                    if s.get('digits') and places is not None:
                        q = 10 ** int(places)
                        floors = [(d, Fraction(int(x * q), q), x) for d, x in parts]
                        left = int(amt.v * q) - sum(int(f * q) for _d, f, _x in floors)
                        order = sorted(range(len(floors)), key=lambda i: (-(floors[i][2] - floors[i][1]), i))
                        parts = [(d, f + (Fraction(1, q) if i in order[:left] else 0)) for i, (d, f, _x) in enumerate(floors)]
                else:
                    raise Refused(f"step {s['id']}: {m.id} states shares for some codes under {k} and amounts for others")
                for d, x in parts:
                    code = self._ancestor(*dmparse.split_coding(d['code']), s['level']) if s.get('level') \
                        else dmparse.split_coding(d['code'])[1]
                    out[code] = out.get(code, Fraction(0)) + x
        self.lines.append(f"  apportioned over {len(out)} code(s), in {unit or 'no currency'}")
        return {k: V(v, unit) for k, v in sorted(out.items())}

    def op_ancestor_at_level(self, s):
        out = []
        for scheme, code, m in self._code_members(s):
            rows = {str(r.get('code', r.get('unit'))): r for r in (self.reg(scheme) or []) if isinstance(r, dict)}
            c, seen = code, set()
            while c in rows and c not in seen:
                seen.add(c)
                r = rows[c]
                if s['level'] in (r.get('level'), r.get('rank')):
                    out.append(Member(f"{scheme}:{c}", f"{scheme}:{c}", m.bean))
                    break
                c = str(r.get('parent') or '')
            else:
                raise Refused(f"step {s['id']}: {scheme}:{code} has no ancestor at the level '{s['level']}'")
        return out

    def op_neighbour_of(self, s):
        if 'distance' in s:
            import geo as dmgeo
            d, out, ids = self._metres(s['distance'], s['id']), [], set()
            for m in self.arg(s, 'of', 'set'):
                try:
                    got = dmgeo.position_of(m.bean, self.g.fm, self.g.root, moment=self.now)
                except ValueError as e:
                    raise Refused(f"step {s['id']}: {m.bean}: {e}") from None
                if got is None:
                    raise Refused(f"step {s['id']}: {m.bean} holds no position to measure from at this moment")
                for b, metres in dmgeo.nearest(got[0], root=self.g.root, k=len(self.g.fm), fixed_only=False,
                                               beans=self.g.fm, moment=self.now):
                    if metres <= d and b != m.bean and b not in ids:
                        ids.add(b)
                        out.append(Member(b, self.g.fm[b], b))
            self.notes.append(f"step {s['id']}: distances great-circle on the body's mean sphere (≈)")
            return out
        rel = self.reg(s['relation']) or []
        out, ids = [], set()
        for scheme, code, m in self._code_members(s):
            for r in rel:
                if not isinstance(r, dict) or r.get('rel') != 'adjacent':
                    continue
                for a, b in ((r.get('from'), r.get('to')), (r.get('to'), r.get('from'))):
                    if str(a) == code and f"{scheme}:{b}" not in ids:
                        ids.add(f"{scheme}:{b}")
                        out.append(Member(f"{scheme}:{b}", f"{scheme}:{b}", m.bean))
        return out

    # a series' reads (S7)
    def _series(self, s, key='series'):
        path = s[key]
        if '#' in path and dmseq.runs_core(self.g.root):          # a series of the core: `<bean>#<id>`
            bean, k = path.split('#', 1)
            node = (self.g.bean(bean or self.bean).get('series') or {}).get(k)
            if not isinstance(node, dict):
                raise Refused(f"step {s['id']}: `{path}` records no series")
            ser = dmseq.Series(law(), bean or self.bean, k, node, self.g.parts(bean or self.bean, k))
            bad = [p for p in ser.problems if p[0] == 'error']
            if bad:
                raise Refused(f"step {s['id']}: the series {path} is not read — {bad[0][2]}")
            return ser, path
        segs = dmparse.path_read(path)
        bean = segs[0].bean or self.bean
        if not bean:
            raise Refused(f"step {s['id']}: `{key}: {path}` starts at a bean, `<bean>:<term>.<key>`")
        found = walk(self.g, self.g.bean(bean), path.split(':', 1)[-1], at=bean)
        if len(found) != 1 or not isinstance(found[0][0], dict):
            raise Refused(f"step {s['id']}: `{path}` holds no one series")
        k = path.rsplit('.', 1)[-1]
        ser = dmseq.Series(law(), bean, k, found[0][0], self.g.parts(bean, k))
        bad = [p for p in ser.problems if p[0] == 'error']
        if bad:
            raise Refused(f"step {s['id']}: the series {bean}:{k} is not read — {bad[0][2]}")
        return ser, f"{bean}:{k}"

    def _channel(self, ser, s, name, sid):
        ch = s.get('channel')
        if ch is None and len(ser.channels) == 1:
            ch = next(iter(ser.channels))
        if ch not in ser.channels:
            raise Refused(f"step {sid}: the series holds no channel '{ch}' — {sorted(ser.channels)}")
        return ch

    def _live(self, ser, ch):
        """[(offset, value)] of the rows whose cell of `ch` holds a number, excluded cells left out."""
        excl = ser.excluded_cells()
        out = []
        for p, a, b, r in ser.places():
            if (ser._row_key(r), ch) in excl or (ser._row_key(r), None) in excl:
                continue
            x = dmseq.exact(r['cells'].get(ch))
            if x is not None:
                out.append((p if p is not None else a, x, r['source']))
        return out

    def op_at(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        x = ser.offset_of(s['position'])
        if x is None:
            raise Refused(f"step {s['id']}: {s['position']!r} is no position on the line of {name}")
        r = ser.read(x)[ch]
        if r['value'] is None:
            raise Refused(f"step {s['id']}: {name}.{ch} at {s['position']} is not read — {r['why']}")
        self.lines.append(f"  {name}.{ch} at {s['position']}: {r['how']} ({', '.join(map(str, r['rows']))})")
        v = r['value'] if isinstance(r['value'], Fraction) else dmseq.exact(r['value'])
        return V(v if v is not None else r['value'], ser.channels[ch].get('unit'), ser.u_of(ch))

    def _extent(self, ser, ext, sid):
        a = ser.offset_of((ext or {}).get('from')) if (ext or {}).get('from') is not None else None
        b = ser.offset_of((ext or {}).get('to')) if (ext or {}).get('to') is not None else None
        return a, b

    def _in(self, live, a, b):
        return [t for t in live if (a is None or t[0] >= a) and (b is None or t[0] <= b)]

    def op_window(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        a, b = self._extent(ser, s.get('extent'), s['id'])
        rows = self._in(self._live(ser, ch), a, b)
        unit, u = ser.channels[ch].get('unit'), ser.u_of(ch)
        self.lines.append(f"  {name}.{ch}: {len(rows)} row(s) in the stretch")
        by = s.get('by') or ['mean']
        by = by if isinstance(by, list) else [by]
        if not rows and by != ['count']:
            raise Refused(f"step {s['id']}: the stretch of {name} holds no value of {ch}")
        n = len(rows)
        _dimless = law().quantity_of(unit) in ('number', 'ratio') if unit else True

        def _product():
            # A PRODUCT OF MEASURES IS ANOTHER QUANTITY (m·m is an area): a window multiplies only what has no dimension
            if not _dimless:
                raise Refused(f"step {s['id']}: the product of {ch} multiplies {unit}s into a unit of another quantity — "
                              f"a window multiplies only counts and ratios")
            p = Fraction(1)
            for _p, x, _r in rows:
                p *= x
            return V(p, unit)
        f = {'sum': lambda: V(sum((x for _p, x, _r in rows), Fraction(0)), unit, u * sqrt(Fraction(n))[0] if u else None),
             'product': _product,
             'mean': lambda: V(sum(x for _p, x, _r in rows) / n, unit, u / sqrt(Fraction(n))[0] if u else None),
             'min': lambda: V(min(x for _p, x, _r in rows), unit, u),
             'max': lambda: V(max(x for _p, x, _r in rows), unit, u),
             'count': lambda: V(Fraction(n), 'item'),
             'first': lambda: V(rows[0][1], unit, u), 'last': lambda: V(rows[-1][1], unit, u)}
        out = {k: f[k]() for k in by}
        return out[by[0]] if len(by) == 1 else out

    def op_integral(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        a, b = self._extent(ser, s.get('extent'), s['id'])
        rows = self._in(self._live(ser, ch), a, b)
        base = self.one(self.env[s['base']], s['id'], 'base') if isinstance(s.get('base'), str) and s['base'] in self.env \
            else (value_of(s['base'], 'base', self.notes) if s.get('base') is not None else None)
        unit = ser.channels[ch].get('unit')
        off = to_unit(base, unit, f"step {s['id']}").v if base is not None and base.unit else (base.v if base else 0)
        sf = ser.channels[ch].get('stands_for')
        if sf == 'sum':
            total = sum(x - off for _p, x, _r in rows)
            return V(total, unit)
        if sf != 'point' or ser.channels[ch].get('between') != 'linear':
            raise Refused(f"step {s['id']}: {name}.{ch} is summed along the line where it is a sum, or a point read "
                          f"linearly between rows — it stands for '{sf}'")
        total = sum((rows[i + 1][0] - rows[i][0]) * ((rows[i][1] - off) + (rows[i + 1][1] - off)) / 2
                    for i in range(len(rows) - 1))
        prod = self._product(V(total, unit), V(Fraction(1), ser.unit), 1, s)
        self.lines.append(f"  {name}.{ch}: {len(rows)} rows, the trapezoids between them summed")
        return prod

    def op_rate(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        x0, x1 = ser.offset_of(s['from']), ser.offset_of(s['to'])
        if x0 is None or x1 is None or x0 == x1:
            raise Refused(f"step {s['id']}: `from` and `to` are two positions on the line of {name}")
        r0, r1 = ser.read(x0)[ch], ser.read(x1)[ch]
        for r, p in ((r0, s['from']), (r1, s['to'])):
            if r['value'] is None:
                raise Refused(f"step {s['id']}: {name}.{ch} at {p} is not read — {r['why']}")
        v0, v1 = (x['value'] if isinstance(x['value'], Fraction) else dmseq.exact(x['value']) for x in (r0, r1))
        u = ser.u_of(ch)
        d = V(v1 - v0, ser.channels[ch].get('unit'), self.hyp(u, u) if u else None)
        return self._product(d, V(x1 - x0, ser.unit), -1, s)

    def op_trend(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        a, b = self._extent(ser, s.get('extent'), s['id'])
        rows = self._in(self._live(ser, ch), a, b)
        n = len(rows)
        if n < 3:
            raise Refused(f"step {s['id']}: a slope is fitted to three rows or more, and the stretch holds {n}")
        mx = sum(p for p, _x, _r in rows) / n
        my = sum(x for _p, x, _r in rows) / n
        sxx = sum((p - mx) ** 2 for p, _x, _r in rows)
        sxy = sum((p - mx) * (x - my) for p, x, _r in rows)
        slope = sxy / sxx
        sse = sum((x - my - slope * (p - mx)) ** 2 for p, x, _r in rows)
        s2 = sse / (n - 2)
        cu = ser.u_of(ch)
        sigma2 = s2 if s2 else (cu * cu if cu else Fraction(0))
        ub = sqrt(sigma2 / sxx)[0] if sigma2 else None
        span = rows[-1][0] - rows[0][0]
        slope_v = self._product(V(slope, ser.channels[ch].get('unit')), V(Fraction(1), ser.unit), -1, s)
        slope_v.u = ub * (slope_v.v / slope) if ub is not None and slope else ub
        slope_v.approx = True
        if ub is None or slope == 0 or abs(slope) > self.k * ub:
            if ub is not None and slope:
                self.lines.append(f"  |slope| > k·u: the slope is resolved over this span ({dmseq.show(span)} {ser.unit})")
        else:
            dens = Fraction(n) / span if span else Fraction(n)
            need = (12 * sigma2 * self.k ** 2 / (dens * slope * slope))
            with decimal.localcontext() as c:
                c.prec = PREC
                need_span = F(D(need) ** (decimal.Decimal(1) / 3))
            self.notes.append(f"step {s['id']}: the slope does not exceed k·u — it is not called a motion; RESOLVABLE "
                              f"over about {dmseq.rounded(need_span, 0)} {ser.unit}s at this density "
                              f"(this span {dmseq.show(span)})")
        return slope_v

    def op_through(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        ties = sorted(self._live(ser, ch))
        if len(ties) < 2:
            raise Refused(f"step {s['id']}: a tie series holds two ties or more")
        if s.get('back') is True:
            y = self.one(self.env[s['position']], s['id'], 'position').v if isinstance(s['position'], str) and s['position'] in self.env \
                else dmseq.exact(s['position'])
            ys = [x for _p, x, _r in ties]
            if not (all(a < b for a, b in zip(ys, ys[1:])) or all(a > b for a, b in zip(ys, ys[1:]))):
                raise Refused(f"step {s['id']}: {name}.{ch} is not monotone, and is not read back")
            for (p0, y0, r0), (p1, y1, r1) in zip(ties, ties[1:]):
                if min(y0, y1) <= y <= max(y0, y1):
                    x = p0 + (p1 - p0) * (y - y0) / (y1 - y0)
                    self.lines.append(f"  read back between the ties {r0} and {r1}")
                    return V(x, ser.unit)
            raise Refused(f"step {s['id']}: {dmseq.show(y)} lies beyond the outermost ties, and nothing is extrapolated")
        x = ser.offset_of(s['position'])
        if x is None or x < ties[0][0] or x > ties[-1][0]:
            raise Refused(f"step {s['id']}: {s['position']!r} lies beyond the outermost ties, and nothing is extrapolated")
        for (p0, y0, r0), (p1, y1, r1) in zip(ties, ties[1:]):
            if p0 <= x <= p1:
                self.lines.append(f"  read between the ties {r0} and {r1}")
                return V(y0 + (y1 - y0) * (x - p0) / (p1 - p0), ser.channels[ch].get('unit'), ser.u_of(ch))

    def op_gaps(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        a, b = self._extent(ser, s.get('extent'), s['id'])
        gaps, excl = ser.law.gaps(), ser.excluded_cells()
        out = []
        for p, lo, hi, r in ser.places():
            at = p if p is not None else lo
            if (a is not None and at < a) or (b is not None and at > b):
                continue
            v = r['cells'].get(ch)
            x = excl.get((ser._row_key(r), ch)) or excl.get((ser._row_key(r), None))
            if x:
                out.append(Member(f"{name}@{dmseq.show(at)}", {'reason': f"excluded by {x.get('by')}: {x.get('why')}"}, None))
            elif v in gaps:
                out.append(Member(f"{name}@{dmseq.show(at)}", {'reason': gaps[v].get('meaning', v)}, None))
        return out

    def op_travelled(self, s):
        ser, name = self._series(s)
        ch = self._channel(ser, s, name, s['id'])
        rows = self._live(ser, ch)
        if not rows:
            # A CHANNEL OF PLACES: the track a being made, each row where it was then — measured leg by leg on the map
            import geo as dmgeo
            excl = ser.excluded_cells()
            pts = [self._geo(r['cells'][ch], s['id']) for p, a, b, r in ser.places()
                   if r['cells'].get(ch) is not None and (ser._row_key(r), ch) not in excl and (ser._row_key(r), None) not in excl]
            if len(pts) < 2:
                raise Refused(f"step {s['id']}: {name}.{ch} holds fewer than two positions — nothing was travelled")
            try:
                total = sum(Fraction(dmgeo.distance(a, b, self.g.root)) for a, b in zip(pts, pts[1:]))
            except ValueError as e:
                raise Refused(f"step {s['id']}: {e}") from None
            self.notes.append(f"step {s['id']}: {len(pts) - 1} legs, great-circle on the body's mean sphere (≈)")
            return V(total, 'metre', None, True)
        total = sum(abs(b[1] - a[1]) for a, b in zip(rows, rows[1:]))
        return V(total, ser.channels[ch].get('unit'), None, False)

    def op_join(self, s):
        if 'series' not in s:
            return self._join_sets(s)
        sa, na = self._series(s)
        sb, nb = self._series(s, 'with')
        ch = self._channel(sa, s, na, s['id'])
        cb = s.get('channel') if s.get('channel') in sb.channels else self._channel(sb, {}, nb, s['id'])
        la = {p: (x, r) for p, x, r in self._live(sa, ch)}
        lb = {p: (x, r) for p, x, r in self._live(sb, cb)}
        ua, ub = sa.u_of(ch), sb.u_of(cb)
        out = []
        for p in sorted(set(la) | set(lb)):
            if p not in lb or p not in la:
                out.append(Member(f"@{dmseq.show(p)}", {'verdict': 'one only', 'in': na if p in la else nb}, None))
                continue
            d = abs(la[p][0] - lb[p][0])
            ud = self.hyp(ua, ub)
            verdict = 'agree' if d == 0 else 'compatible' if ud and d <= self.k * ud else 'differ'
            out.append(Member(f"@{dmseq.show(p)}", {'verdict': verdict, 'difference': dmseq.show(d)}, None))
        return out

    # -- THE RULES' OPERATIONS (core 3.0): two sets joined, cycle, reach, first, last, describe. Each reads a filler as
    # the being it names in the bean it was written in (core/engine.py `norm`: `self` the bean, a statement's id
    # `<bean>#<id>`, a store's pointer the being's id), and each member it gives carries its proof.
    def _bean_at(self, m, path):
        """The bean the value at `path` of member `m` was written in: its node's, or the part's of a pair."""
        beans = m.beans if isinstance(m, Row) else {'': m.bean}
        segs = path.split('.')
        for k in range(len(segs) - 1, -1, -1):
            pre = '.'.join(segs[:k])
            if pre in beans:
                return beans[pre]
        return m.bean

    def _read_as(self, v, bid):
        """`v`, written in the bean `bid`, as the being it names (core/engine.py `norm`), where the engine judges."""
        J = getattr(self.g, 'J', None)
        b = J.G.beans.get(bid) if J is not None and isinstance(bid, str) else None
        if b is not None:
            return J.norm(v, b)
        return bid if v == 'self' and isinstance(bid, str) else v

    def _named(self, m, path):
        """[(written, the being it names)] for each value at `path` of member `m`: a list, each of its items."""
        bid = self._bean_at(m, path)
        return [(v, self._read_as(v, bid)) for x, _w in walk(self.g, m.node, path, at=m.bean)
                for v in (x if isinstance(x, list) else [x])]

    def _one(self, m, path):
        """The one name at `path` of member `m`, as the being it names: None where the path holds nothing, several
        values, or one that is no name — a list, a `someone`, a number."""
        found = walk(self.g, m.node, path, at=m.bean)
        if len(found) != 1 or not isinstance(found[0][0], str):
            return None
        n = self._read_as(found[0][0], self._bean_at(m, path))
        return n if isinstance(n, str) else None

    def _join_sets(self, s):
        """`join` of two sets on equal columns: the members of `of` in their order, each with those of `with`, in
        theirs, that agree on every column of `on` — kept as `keep` says."""
        if 'of' not in s:
            raise Refused(f"step {s['id']}: `join` joins two series (`series`, `with`) or two sets (`of`, `with`)")
        left, right = self.arg(s, 'of', 'set'), self.arg(s, 'with', 'set')
        on = list(s['on'].items()) if isinstance(s.get('on'), dict) and s['on'] else None
        if not on:
            raise Refused(f"step {s['id']}: two sets are joined on the columns that are equal, `on: {{<path>: <path>}}`")
        keep = s.get('keep') or 'both'
        idx = {}
        for r in right:
            key = tuple(self._one(r, b) for _a, b in on)
            if None not in key:
                idx.setdefault(key, []).append(r)
        src = self._sources.get(s['with'])          # an absence from the law's table rests on the table
        out = []
        for m in left:
            key = tuple(self._one(m, a) for a, _b in on)
            hits = idx.get(key, []) if None not in key else []
            lr = as_row(m)
            if keep == 'matched':
                if hits:
                    out.append(Row(lr.id, lr.node, lr.bean, lr.place, lr.seq, lr.beans,
                                   _proof(lr.proof, as_row(hits[0]).proof)))
            elif keep == 'unmatched':
                if not hits:
                    out.append(Row(lr.id, lr.node, lr.bean, lr.place, lr.seq, lr.beans,
                                   _proof(lr.proof, (src,) if src else ())))
            else:
                names = s.get('as')
                if not (isinstance(names, list) and len(names) == 2 and all(isinstance(x, str) for x in names)):
                    raise Refused(f"step {s['id']}: a pair is read under two names, `as: [<of's>, <with's>]`")
                x, y = names
                for r in hits:
                    rr = as_row(r)
                    beans = {(f"{x}.{k}" if k else x): v for k, v in lr.beans.items()}
                    beans.update({(f"{y}.{k}" if k else y): v for k, v in rr.beans.items()})
                    out.append(Row(f"{lr.id} & {rr.id}", {x: lr.node, y: rr.node}, lr.bean, lr.place, lr.seq, beans,
                                   _proof(lr.proof, rr.proof)))
        return out

    @property
    def _sources(self):
        if not hasattr(self, '_source'):
            self._source = {}
        return self._source

    def _edges(self, m, froms, tos, within=None):
        """[(start, end)]: the edges member `m` makes, from each being at a path of `froms` to each at one of `tos`,
        each a name read as the being it names; with `within`, both ends among those beans."""
        out = []
        for f in froms:
            for _v, a in self._named(m, f):
                if not isinstance(a, str) or (within is not None and a not in within):
                    continue
                for t in tos:
                    for _w, c in self._named(m, t):
                        if isinstance(c, str) and (within is None or c in within):
                            out.append((a, c))
        return out

    def op_cycle(self, s):
        from core import reach as _reach
        of = self.arg(s, 'of', 'set')
        more = self.arg(s, 'with', 'set') if s.get('with') else []
        within = {m.id for m in self.arg(s, 'within', 'set')} if s.get('within') else None
        froms, tos = _paths(s['from']), _paths(s['to'])
        graph, why = {}, {}
        made = [(m, self._edges(m, froms, tos, within)) for m in list(more) + list(of)]
        for m, es in made:
            for e in es:
                graph.setdefault(e[0], set()).add(e[1])
                why.setdefault(e, as_row(m).proof)
        out = []
        for m, es in made[len(more):]:
            mr = as_row(m)
            for a, c in es:
                path = [a] if a == c else _reach.way(c, a, lambda n: sorted(graph.get(n, ())))
                if not path:
                    continue
                loop = [a, c] + path[:-1] + ([a] if a != c else [])
                proof = _proof(mr.proof, *[why.get(e, ()) for e in zip(loop, loop[1:])])
                out.append(Row(f"{a} → {c} · {mr.id}", dict(mr.node, start=a, next=c, way=[c] + path[:-1], loop=loop),
                               mr.bean, mr.place, mr.seq, mr.beans, proof))
        return out

    def op_reach(self, s):
        from core import reach as _reach
        rel = self.arg(s, 'through', 'set')
        froms, tos = _paths(s['from']), _paths(s['to'])
        graph, why = {}, {}
        for m in rel:
            for e in self._edges(m, froms, tos):
                graph.setdefault(e[0], set()).add(e[1])
                why.setdefault(e, as_row(m).proof)
        if s['through'] in self._sources:              # an absence from what it reaches rests on the relation
            self._sources[s['id']] = self._sources[s['through']]
        out, seen = [], set()
        for m in self.arg(s, 'of', 'set'):
            for _v, st in self._named(m, s['at']):
                if not isinstance(st, str) or st in seen:
                    continue
                seen.add(st)
                out.append(Row(f"{st} → {st}", {'start': st, 'reached': st, 'way': []}, None))
                r = _reach.Reach(st, lambda n: sorted(graph.get(n, ())))
                for x, _via in r:
                    way = r.path(x)
                    out.append(Row(f"{st} → {x}", {'start': st, 'reached': x, 'way': way}, None,
                                   proof=_proof(*[why.get(e, ()) for e in zip([st] + way, way)])))
        return out

    def op_first(self, s, last=False):
        ms = self.arg(s, 'of', 'set')
        by = _paths(s['by'])
        best, keys = {}, []
        for k, m in enumerate(ms):
            key = tuple(self._one(m, p) for p in by)
            seq = as_row(m).seq
            at = (seq if seq is not None else -1, k)       # where the garden reads it, then where the set holds it
            if key not in best:
                best[key] = (at, m)
                keys.append(key)
            elif (at > best[key][0]) if last else (at < best[key][0]):
                best[key] = (at, m)
        if s.get('groups') == 'values':                # the groups in the order of their values, each name's characters
            keys = sorted(keys, key=lambda k: tuple((x is not None, x or '') for x in k))
        return [best[key][1] for key in keys]

    def op_last(self, s):
        return self.op_first(s, last=True)

    def op_overlap(self, s):
        """`overlap` (core 3.3, I.8): the pairs of members whose spans overlap — one starting before the other ends,
        and ending after it starts — within each group of the members whose values at `by` are one; each pair a member
        read under `as`, the earlier first, told at the later's place. A group's members in the order of their starts
        (of their ends, where they start alike; then as the set holds them), and the pairs in the order of theirs. With
        `first`, only the group's first is paired, alone, with each later one. With no span (`from`, `to`), every two
        members of a group overlap: each holds what it holds at once."""
        ms = self.arg(s, 'of', 'set')
        names = s.get('as')
        if not (isinstance(names, list) and len(names) == 2 and all(isinstance(n, str) for n in names)):
            raise Refused(f"step {s['id']}: a pair is read under two names, `as: [<the earlier's>, <the later's>]`")
        if ('from' in s) != ('to' in s):
            raise Refused(f"step {s['id']}: a span is read from two paths, `from` and `to`, or from none")
        x, y = names
        by = _paths(s.get('by'))
        groups, keys = {}, []
        for k, m in enumerate(ms):
            sp = self._span_at(m, s['from'], s['to']) if 'from' in s else (0, 0)
            key = tuple(self._one(m, p) for p in by)
            if sp is None or None in key:
                continue                         # no span, or a value at `by` that is no name: in no group
            if key not in groups:
                groups[key] = []
                keys.append(key)
            groups[key].append((sp, k, m))
        if s.get('groups') == 'values':
            keys = sorted(keys)
        out = []
        for key in keys:
            g = sorted(groups[key], key=lambda e: (e[0], e[1]))
            for j in range(1 if str(s.get('first')) == 'true' and g else len(g)):
                (l1, h1), _k1, a = g[j]
                for (l2, h2), _k2, b in g[j + 1:]:
                    if 'from' in s and not (l2 < h1 and l1 < h2):
                        continue
                    ar, br = as_row(a), as_row(b)
                    beans = {(f"{x}.{n}" if n else x): v for n, v in ar.beans.items()}
                    beans.update({(f"{y}.{n}" if n else y): v for n, v in br.beans.items()})
                    out.append(Row(f"{ar.id} & {br.id}", {x: ar.node, y: br.node}, br.bean, br.place, br.seq, beans,
                                   _proof(ar.proof, br.proof)))
        return out

    def _span_at(self, m, frm, to):
        """(from, to) in milliseconds of member `m`'s span, read at two paths — each one moment, or a day (its start,
        and the end of its end) — or None where either holds no one position of time."""
        ends = []
        for path, end in ((frm, False), (to, True)):
            ms = span_end(walk(self.g, m.node, path, at=m.bean), end, self.zone, self.notes)
            if ms is None:
                return None
            ends.append(ms)
        return tuple(ends)

    def op_describe(self, s):
        L = self._core_law()
        name = s['as']
        out = []
        for m in self.arg(s, 'of', 'set'):
            mr = as_row(m)
            if 'at' not in s:                  # THE MEMBER ITSELF, a statement (core 3.2, I.1): its bean, verb, place
                cols = dict(dict.fromkeys(described(L)), **self._statement_cols(self._statement_at(mr.place)))
                beans = dict(mr.beans)
                beans[name] = mr.bean
                out.append(Row(mr.id, dict(mr.node if isinstance(mr.node, dict) else {}, **{name: cols}), mr.bean,
                               mr.place, mr.seq, beans, mr.proof))
                continue
            bid = self._bean_at(m, s['at'])
            vals = [v for v, _n in self._named(m, s['at'])]
            for k, v in enumerate(vals):
                kind, bean = self._kind(v, bid)
                row = L.kinds.get(kind) or {} if isinstance(kind, str) else {}
                held = L.positions(kind) if row else {}
                cols = dict({'being': v, 'kind': kind, 'nature': row.get('nature')}, **{ln: held.get(ln) for ln in L.facets})
                said = self._statement_named(v, bid)          # a value that names a statement: that statement (I.1)
                cols.update(self._statement_cols(said))
                cols.update(self._position_cols(v, kind is not None or bean is not None or said is not None))
                proof = _proof(mr.proof, (f"{bean}:kind",) if bean else (),
                               (f"law:kinds[{kind}]",) if isinstance(kind, str) and kind in L.kinds else (),
                               (said[3],) if said else ())
                beans = dict(mr.beans)
                beans[name] = bid
                out.append(Row(mr.id if len(vals) == 1 else f"{mr.id} @{k}",
                               dict(mr.node if isinstance(mr.node, dict) else {}, **{name: cols}), mr.bean,
                               mr.place, mr.seq, beans, proof))
        return out

    @staticmethod
    def _statement_cols(said):
        """The columns of a statement `said` (bean, index, verb, place, roles), or none where it is None (I.1)."""
        if not said:
            return dict.fromkeys(('bean', 'verb', 'index', 'place', 'id'))
        b, i, verb, place, roles = said
        sid = roles.get('id') if isinstance(roles, dict) and isinstance(roles.get('id'), str) else None
        return {'bean': b, 'verb': verb, 'index': str(i), 'place': place, 'id': sid}

    def _position_cols(self, v, named):
        """The columns of a position (core 3.3, I.2): its `system`; `point`, whether it names a point — its system
        covers one (core/frame.py `covers_point`); and its span, `from` and `to`, to the moment — a day its whole, an
        extent to the end of its end — each written as a moment in UTC to the millisecond. None for what is no position:
        a being, a statement, `now`, `unknown`, or a text no system reads."""
        if named:
            return dict.fromkeys(POSITION_COLUMNS)
        J = getattr(self.g, 'J', None)
        return position_cols(v, J.systems if J is not None else self._core_law().systems,
                             J.G.zone if J is not None else self.zone)

    def _statement_at(self, place):
        """(bean, index, verb, place, roles) of the statement told at `place` (`<bean>[<i>] <verb>`), or None."""
        J = getattr(self.g, 'J', None)
        m = re.match(r'^([^\[\]]+)\[([0-9]+)\] (\S+)$', place or '')
        b = J.G.beans.get(m.group(1)) if m and J is not None else None
        hit = next(((i, v, r) for i, v, r in b.items if i == int(m.group(2)) and v == m.group(3)), None) if b else None
        return (b.id, hit[0], hit[1], place, hit[2]) if hit else None

    def _statement_named(self, v, bid):
        """(bean, index, verb, place, roles) of the statement the value `v`, written in bean `bid`, names — an id of
        one of that bean's statements, or `<bean>#<id>` — or None (core/engine.py `statement`)."""
        J = getattr(self.g, 'J', None)
        b = J.G.beans.get(bid) if J is not None and isinstance(bid, str) else None
        hit = J.statement(v, b) if b is not None and isinstance(v, str) else None
        return (hit[0].id, hit[1], hit[2], f"{hit[0].id}[{hit[1]}] {hit[2]}", hit[3]) if hit else None

    def _kind(self, v, bid):
        """(the kind of the being `v` names, written in bean `bid`; the bean whose header says it, or None): None for
        the crown, `unknown`, or what names no being."""
        J = getattr(self.g, 'J', None)
        if J is not None:
            b = J.G.beans.get(bid) if isinstance(bid, str) else None
            kind = J.kind_of(v, b) if b is not None or v != 'self' else None
            named = (b.id if v == 'self' and b is not None else v if isinstance(v, str) and v in J.G.beans else None)
            return kind, named
        if isinstance(v, dict):
            return v.get('someone'), None
        i = bid if v == 'self' else v
        fm = self.g.fm.get(i) if isinstance(i, str) else None
        return (fm.get('kind'), i) if isinstance(fm, dict) else (None, None)

    def op_used_within(self, s):
        """The length of the members' extents inside the window of `within` ending at `at` — or, where the path holds
        a position rather than an extent, how many fall inside it (N9)."""
        at = self.operand(s['at']) if isinstance(s.get('at'), dict) else s.get('at')
        at = at.v if isinstance(at, V) else at
        p_at = _pos(at, self.zone, self.notes)
        if p_at is None:
            raise Refused(f"step {s['id']}: `at` is a moment or a day — the end of the window")
        day_at = p_at[1] if p_at[0] == 'day' else _local_day(p_at[1], self.zone, at)
        w = s.get('within') or {}
        if isinstance(w.get('measure'), dict):
            days = to_unit(value_of(w['measure'], 'within', self.notes), 'day', f"step {s['id']}").v
            if days.denominator != 1:
                raise Refused(f"step {s['id']}: a window is counted in whole days")
            lo = day_at - int(days) + 1
        elif w.get('level') in ('year', 'month') and isinstance(w.get('count'), int):
            # THE CALENDAR THE WINDOW NAMES (`in`, a time system of the law), read through the calendar its row carries:
            # a month of the Solar Hijri year is not a Gregorian one. A month is stepped back through that calendar's
            # own month starts, so a calendar of thirteen months is counted as it is.
            cal = self._calendar_of(w.get('in'), s['id'])
            n = w['count'] - 1
            def parts(day):
                txt = dmcal.from_day(day, cal)
                pre, _c, ymd = txt.rpartition(':')
                y, m, d = (int(x) for x in ymd.split('-'))
                return (pre + ':' if pre else ''), y, m, d
            pre, y, m, d = parts(day_at)
            if w['level'] == 'year':
                lo = dmcal.to_day(f"{pre}{y - n:04d}-01-01" if not pre else f"{pre}{y - n}-01-01")
            else:
                lo = day_at - (d - 1)
                for _i in range(n):
                    _p, _y, _m, _d = parts(lo - 1)
                    lo = lo - 1 - (_d - 1)
        else:
            raise Refused(f"step {s['id']}: `within` is a sliding `measure`, or `level: year | month` with a `count`")
        used, counted = Fraction(0), 0
        for m in self.arg(s, 'of', 'set'):
            for x, wh in walk(self.g, m.node, s['path'], at=m.bean):
                if isinstance(x, dict) and ('from' in x or 'to' in x):
                    a = _pos(x.get('from'), self.zone, self.notes)
                    b = _pos(x.get('to'), self.zone, self.notes)
                    if not a or not b or a[0] != 'day' or b[0] != 'day':
                        raise Refused(f"step {s['id']}: {wh} is an extent of days, from and to, each counted whole")
                    ov = min(b[1], day_at) - max(a[1], lo) + 1
                    if ov > 0:
                        used += ov
                        self.lines.append(f"  {wh}: {ov} day(s) inside")
                else:
                    p = _pos(x, self.zone, self.notes)
                    d = p and (p[1] if p[0] == 'day' else _local_day(p[1], self.zone, x))
                    if d is not None and lo <= d <= day_at:
                        counted += 1
                        self.lines.append(f"  {wh}: inside")
        _cal = self._calendar_of(w.get('in'), s['id']) if w.get('level') else 'gregory'
        self.lines.append(f"  the window: {dmcal.from_day(lo, _cal)} to {dmcal.from_day(day_at, _cal)}")
        return V(used, 'day') if used else V(Fraction(counted), 'item')

    def _calendar_of(self, system, sid):
        """The calendar a time system of the law names (its row's `calendar`); the civil Gregorian one where none is
        named. A system that is no time system of the law is refused."""
        if system is None:
            return 'gregory'
        row = next((r for r in (self.reg('anchor_systems') or []) if isinstance(r, dict) and r.get('system') == system
                    and r.get('dimension') == 'time'), None)
        if row is None or not row.get('calendar'):
            raise Refused(f"step {sid}: `in: {system}` is no time system of the law that names a calendar")
        return row['calendar']

    def op_weigh(self, s):
        ref = s['weighing']
        bean, key = (ref.split(':', 1) if ':' in ref else (self.bean, ref))
        entry = ((self.g.bean(bean).get('weighings') or {}).get(key))
        if not isinstance(entry, dict):
            raise Refused(f"step {s['id']}: no weighing '{ref}'")
        crit, w, lam, ci, cr = weights(entry)
        self.lines.append(f"  λmax ≈ {dmseq.rounded(lam, 4)}, CI ≈ {dmseq.rounded(ci, 4)}, CR ≈ {dmseq.rounded(cr, 3)}")
        return {a: V(w[a], 'one', None, True) for a in crit}

    def op_axes(self, s):
        """Each member on the three axes (core/courses.py): its needs, what needs it, what it remedies and the failures it
        makes possible, read from the garden's statements at the moment asked; with a weighing, its sum and its mark."""
        from core import courses
        from core.inforce import InForce
        members = [m.bean for m in self.arg(s, 'of', 'set')]
        weights_ = None
        if s.get('weighing'):
            ref = s['weighing']
            bean, key = (ref.split(':', 1) if ':' in ref else (self.bean, ref))
            entry = (self.g.bean(bean).get('weighings') or {}).get(key)
            if not isinstance(entry, dict):
                raise Refused(f"step {s['id']}: no weighing '{ref}'")
            crit, w, _lam, _ci, cr = weights(entry)
            missing = [c for c in courses.CRITERIA if c not in crit]
            if missing:
                raise Refused(f"step {s['id']}: the weighing {ref} weighs no {', '.join(missing)}: the axes are "
                              f"{', '.join(courses.CRITERIA)}")
            weights_ = {c: float(w[c]) for c in crit}
        F = InForce(self.g.root)
        stmts = {v: list(self._statements(v)) for v in ('need', 'meet', 'contingent', 'impossible', 'repair', 'fail',
                                                        'possible')}

        def ref(b, x):
            return x.split('#')[-1] if isinstance(x, str) and ('#' not in x or x.split('#')[0] == b) else x

        met = {(b, str(r.get('of')).split('#')[-1]) if '#' not in str(r.get('of')) else
               tuple(str(r.get('of')).split('#', 1)) for b, r in stmts['meet']}
        soft = {(b, ref(b, r.get('of'))) for b, r in stmts['contingent']}
        never = {(b, ref(b, r.get('of'))) for b, r in stmts['impossible']}
        possible = {(b, ref(b, r.get('of'))) for b, r in stmts['possible']}

        def held(b, r):
            """True where the need holds now, False where it does not, None where its `while` cannot be read: a blocking
            need not read still blocks, and one not read needs nothing now (core/courses.py)."""
            return F.holds(b, r)

        def need(b, r):
            of = r.get('of') if isinstance(r.get('of'), list) else [r.get('of')]
            amount = next((x for x in of if isinstance(x, dict) and 'count' in x), None)
            return {'id': r.get('id'), 'bean': b, 'blocking': (b, r.get('id')) not in soft,
                    'met': (b, r.get('id')) in met, 'impossible': (b, r.get('id')) in never,
                    'meetable': r.get('from') not in (None, 'unknown') and (b, r.get('id')) not in never,
                    'in_force': held(b, r), 'amount': amount}
        facts = []
        for m in members:
            own = [need(b, r) for b, r in stmts['need'] if b == m and r.get('id')]
            by = [need(b, r) for b, r in stmts['need'] if b != m and r.get('id')
                  and m in [x for x in (r.get('of') if isinstance(r.get('of'), list) else [r.get('of')]) if isinstance(x, str)]]
            repairs = sum(1 for b, r in stmts['repair'] if str(r.get('by')) == m)
            risks = sum(1 for b, r in stmts['fail'] if str(r.get('through')) == m and (b, r.get('id')) in possible)
            facts.append({'id': m, 'needs': own, 'needed_by': by, 'repairs': repairs, 'risks': risks})
        rows = courses.axes(facts, weights_)
        out = {}
        for r in rows:
            amounts = ', '.join(f"{dmseq.show(a)} {u}" for u, a in sorted(r['amounts'].items())) or 'none'
            self.lines.append(f"  {r['id']}: feasibility {dmseq.show(r['feasibility'])}, efficiency "
                              f"{dmseq.show(r['efficiency'])} (yield {dmseq.show(r['yield'])} × cost "
                              f"{dmseq.show(r['cost'])}), necessity {dmseq.show(r['necessity'])}"
                              + (f", sum {r['sum']:.3f}" if r['sum'] is not None else '')
                              + f" · amounts {amounts} · {r['evidence']}")
            out.setdefault(r['mark'] or ('unmarked' if weights_ else 'no weighing: no mark'), []).append(
                next(x for x in self.arg(s, 'of', 'set') if x.bean == r['id']))
        self.found_axes = getattr(self, 'found_axes', {})
        self.found_axes[s['id']] = rows
        return out

    def op_conservation(self, s):
        found = _flatten(walk(self.g, None, s['walk']))
        steps = [x for x, _w in found if isinstance(x, dict)]
        if not steps:
            raise Refused(f"step {s['id']}: `{s['walk']}` holds no steps")
        scheme = s['scheme']
        rows = {str(r.get('code')): r for r in (self.reg(scheme) or []) if isinstance(r, dict)}
        ok = True
        for st in steps:
            tally = {'takes': collections.Counter(), 'gives': collections.Counter()}
            for side in ('takes', 'gives'):
                for e in st.get(side) or []:
                    if not isinstance(e, dict) or dmparse.split_coding(e.get('code'))[0] != scheme:
                        continue
                    r = rows.get(dmparse.split_coding(e['code'])[1])
                    f = (r or {}).get('formula')
                    if not f or f in ('-', 'none'):
                        raise Refused(f"step {s['id']}: {dmparse.split_coding(e['code'])[1]} has no formula in {scheme} (a polymer, a "
                                      f"mixture) — conservation is read only over substances with one")
                    n = e.get('amount', {}).get('count', 1) if isinstance(e.get('amount'), dict) else 1
                    n = Fraction(n) if isinstance(n, int) else dmseq.exact(n)
                    for el, k in formula(f).items():
                        tally[side][el] += n * k
                    ch = dmseq.exact(str(r.get('charge') or '0').lstrip('+')) or 0
                    tally[side]['(charge)'] += n * ch
            diff = {el: tally['gives'][el] - tally['takes'][el] for el in set(tally['takes']) | set(tally['gives'])
                    if tally['gives'][el] != tally['takes'][el]}
            name = st.get('id', '?')
            if diff:
                ok = False
                self.lines.append(f"  step {name}: NOT conserved — " + ', '.join(
                    f"{el} {dmseq.show(tally['takes'][el])} in, {dmseq.show(tally['gives'][el])} out" for el in sorted(diff)))
            else:
                self.lines.append(f"  step {name}: every element and the charge conserved — " + ', '.join(
                    f"{el} {dmseq.show(v)}" for el, v in sorted(tally['takes'].items()) if v))
        return ok

    # groupings (core 2.15): patterns, classes and what several cursors share — core/groupings.py is their engine
    def _value(self, s, key):
        """What a step takes at `key`: as written, or the input it names, given by the asker."""
        v = s.get(key)
        if isinstance(v, dict) and set(v) == {'input'}:
            got = self.env.get(v['input'])
            if got is None:
                raise Refused(f"step {s['id']}: `{key}` names the input {v['input']!r}, and none was given")
            return got.v if isinstance(got, V) else got
        return v

    def _grouping_law(self):
        if not hasattr(self, '_gl'):
            from core import groupings, read as core_read
            law_dir = os.path.join(self.g.root, 'core', 'law')
            if not os.path.isfile(os.path.join(law_dir, 'lines.yaml')):
                law_dir = os.path.join(ROOT, 'core', 'law')
            lines = core_read.data(os.path.join(law_dir, 'lines.yaml')) or {}
            systems = core_read.data(os.path.join(law_dir, 'systems.yaml')) or {}
            self._gl = {'slots': {str(r['slot']): r for r in lines.get('slots') or [] if isinstance(r, dict)},
                        'systems': {str(r['system']): r for r in systems.get('systems') or []
                                    if isinstance(r, dict) and r.get('dimension') == 'time'
                                    and r.get('reckoning') == 'arithmetic'},
                        'groupings': {str(r['grouping']): r for r in lines.get('groupings') or [] if isinstance(r, dict)}}
            import knowledge as dmknowledge
            K = dmknowledge.Knowledge(self.g.root)
            mine, theirs = [], []
            released = {str(r.get('scheme')) for r in (core_read.data(os.path.join(law_dir, 'registries.yaml')) or {})
                        .get('knowledge_schemes') or [] if isinstance(r, dict)}
            for name, row in sorted(K.schemes.items()):
                if isinstance(row, dict) and row.get('form') == 'pattern':
                    try:
                        (theirs if name in released else mine).append((name, K.rows(name)))
                    except (KeyError, OSError):
                        continue
            self._gl['schemes'] = mine + theirs          # the garden's own first, then the release's
            self._gl['knowledge'] = K
            self._gl['rows'] = groupings.rows_of(self._gl['schemes'], self._gl['slots'], self._gl['systems'], lines)
            self._gl['lines'] = lines                    # the law's uses of the nearest, read with the rows
        return self._gl

    def op_fit(self, s):
        from core import groupings
        G = self._grouping_law()
        of = s.get('of')
        if isinstance(of, dict) and set(of) == {'input'}:
            given = self._value(s, 'of')
            given = given if isinstance(given, list) else re.split(r'[\n,]\s*', str(given).strip())
            items = [(t, t, None) for t in given if str(t).strip()]
        else:
            items = []
            for m in self.arg(s, 'of', 'set'):
                found = walk(self.g, m.node, s['path'], at=m.bean) if s.get('path') else [(m.id, None)]
                text = next((x for x, _w in found if isinstance(x, (str, int))), None)
                if text is None:
                    continue
                cont = _own(m.node.get(s['by']), m.bean) if s.get('by') and isinstance(m.node, dict) else None
                items.append((m, str(text), cont))
        rows = [r for r in G['rows'] if not s.get('scheme') or r.scheme == self._value(s, 'scheme')]
        groups = groupings.fit(items, rows, G['systems'], reads=s.get('path') or None)
        self.found_groups = getattr(self, 'found_groups', {})
        self.found_groups[s['id']] = groups
        out = {}
        for g in groups:
            label = groupings.ranged(g) + (f" in {g['container']}" if g.get('container') else '')
            out[label] = list(g['members'])
        return out

    def op_inherit(self, s):
        from core import groupings
        G = self._grouping_law()
        scheme = str(self._value(s, 'scheme'))
        K = G['knowledge']
        try:
            rows = {str(r.get('code')): r for r in K.rows(scheme)}
        except (KeyError, OSError) as e:
            raise Refused(f"step {s['id']}: the scheme {scheme} cannot be read here: {e}")
        loop = groupings.cycle({c: [str(r['parent'])] for c, r in rows.items() if r.get('parent')})
        if loop:
            raise Refused(f"step {s['id']}: the codes of {scheme} run in a cycle: {' → '.join(loop)}")
        said, wholes, names = collections.defaultdict(list), collections.defaultdict(list), collections.defaultdict(list)
        held_as, held_in = collections.defaultdict(list), collections.defaultdict(list)
        for b, fm in self.g.fm.items():
            if self.g.kind.get(b) != 'beans':
                continue
            for x, _w in _flatten(walk(self.g, fm, 'classify', at=b)):
                code = str(x.get('as') or '') if isinstance(x, dict) else ''
                sch, c = dmparse.split_coding(code)
                if sch == scheme:
                    said[_own(x.get('of'), b)].append(code)
            for x, _w in _flatten(walk(self.g, fm, 'part', at=b)):
                if isinstance(x, dict) and _own(x.get('of'), None):
                    wholes[_own(x.get('by'), b)].append(_own(x['of'], b))
            for x, _w in _flatten(walk(self.g, fm, 'hold', at=b)):
                if isinstance(x, dict) and _own(x.get('of'), None):
                    wholes[_own(x['of'], b)].append(_own(x.get('by'), b))
                    if x.get('as') is not None:
                        held_as[_own(x['of'], b)].append(str(x['as']))
                        held_in[_own(x['of'], b)].append((_own(x.get('by'), b), str(x['as'])))
            for x, _w in _flatten(walk(self.g, fm, 'name', at=b)):
                if isinstance(x, dict) and x.get('as') is not None:
                    names[_own(x.get('of'), b)].append((_own(x.get('by'), b), str(x['as'])))
        for st in getattr(self, '_opened', {}).values():     # what the stores a step read keep of these beings
            if st is None:
                continue
            for verb, store_to in (('part', wholes), ('hold', wholes)):
                if verb not in st.verbs():
                    continue
                for being, _sid, roles in st.statements_of(verb):
                    by, of = _ref_bean(roles.get('by')), _ref_bean(roles.get('of'))
                    if verb == 'part' and of:
                        wholes[by or being].append(of)
                    elif verb == 'hold' and of and by:
                        wholes[of].append(by)
                        if roles.get('as') is not None:
                            held_as[of].append(str(roles['as']))
                            held_in[of].append((by, str(roles['as'])))
            if 'name' in st.verbs():
                for being, _sid, roles in st.statements_of('name'):
                    if roles.get('as') is not None:
                        names[_ref_bean(roles.get('of')) or being].append((_ref_bean(roles.get('by')), str(roles['as'])))

        def top(b):
            """The volume a folder is beneath: its last whole up `part`."""
            seen = {b}
            while wholes.get(b) and wholes[b][0] not in seen:
                b = wholes[b][0]
                seen.add(b)
            return b

        def path_of(f):
            """A folder's path beneath its volume: the name its volume gives it (`reads: path`)."""
            v = top(f)
            return next((a for by, a in names.get(f) or [] if by == v and v != f), None)

        def own_names(b):
            """A being's names but its path: a name given by the volume above its whole is its path, read apart."""
            v = top(b)
            return [a for by, a in names.get(b) or [] if not (by == v and v not in (wholes.get(b) or []))]
        apart = set()                                         # the codes that set apart, of every class scheme
        for name, row in K.schemes.items():
            if isinstance(row, dict) and row.get('form') == 'class':
                try:
                    apart |= {f"{name}:{r.get('code')}" for r in K.rows(name) if str(r.get('apart') or '') == 'true'}
                except (KeyError, OSError):
                    continue

        def suggested(b):
            got = []
            for n in own_names(b):
                for hit, _v in groupings.fitting(G['rows'], n, lambda r: (r.reads or 'as') == 'name.as'):
                    got += hit.suggests
            for x in held_as.get(b) or []:                   # a content by the names its folders hold it by
                for hit, _v in groupings.fitting(G['rows'], x, lambda r: (r.reads or 'as') == 'as' and not r.marks):
                    got += hit.suggests
            for f, x in held_in.get(b) or []:                # ...and by each holding's path beneath its volume
                p = path_of(f)
                if f == top(f) or p is not None:
                    got += [c for c in groupings.path_codes(G['rows'], f"{p}/{x}" if p else x) if c not in got]
            return got

        from core import nearest
        tie = nearest.use(G['lines'], 'wholes')[1]      # wholes as near that hold codes, as the law's use says
        out = collections.OrderedDict()
        self.found_classes = getattr(self, 'found_classes', {})
        detail = {}
        for m in self.arg(s, 'of', 'set'):
            got = groupings.inherit(m.bean, lambda b: said.get(b), lambda b: wholes.get(b), suggested,
                                    lambda c: c in apart, scheme=scheme, tie=tie)
            detail[m.id] = got
            for code, source, through in got or [(None, 'nothing said, inherited or suggested', None)]:
                key = f"{code} ({source}{' from ' + through if through and through != m.bean else ''})" if code \
                    else f"(none: {source})"
                out.setdefault(key, []).append(m)
        self.found_classes[s['id']] = detail
        return dict(out)

    def _statements(self, verb):
        """(being, roles) of every `verb` statement the garden's beans and the stores a step read keep."""
        for b, fm in self.g.fm.items():
            for x, _w in _flatten(walk(self.g, fm, verb, at=b)):
                if isinstance(x, dict):
                    yield b, {k: (_own(v, b) if k in ('by', 'of', 'at') and isinstance(v, str) else v)
                              for k, v in x.items()}
        for st in getattr(self, '_opened', {}).values():
            if st is None or verb not in st.verbs():
                continue
            for being, _sid, roles in st.statements_of(verb):
                yield being, {k: (_ref_bean(v) or v if k in ('by', 'of', 'at') and isinstance(v, str) else v)
                              for k, v in roles.items()}

    def op_keepings(self, s):
        """Each content by its policy code and the risks it leaves open (core/storage.py `judge`)."""
        from core import storage
        G = self._grouping_law()
        risks = {str(r.get('risk')): [w for w in (r.get('resolved_by') or []) if isinstance(w, dict)]
                 for r in (self.reg('risks') or []) if isinstance(r, dict)}
        scheme = self._value(s, 'scheme') if s.get('scheme') is not None else None
        policy, said, wholes = {}, collections.defaultdict(list), collections.defaultdict(list)
        if scheme:
            try:
                policy = {str(r.get('code')): r for r in G['knowledge'].rows(str(scheme))}
            except (KeyError, OSError) as e:
                raise Refused(f"step {s['id']}: the scheme {scheme} cannot be read here: {e}")
        holders = collections.defaultdict(list)          # content -> [(folder, holding)]
        carried = collections.defaultdict(list)          # volume or folder -> its carriers or wholes
        for b, r in self._statements('classify'):
            sch, _c = dmparse.split_coding(str(r.get('as') or ''))
            if r.get('of'):
                said[str(r['of'])].append(str(r['as']))
        for b, r in self._statements('part'):
            if r.get('of'):
                wholes[str(r.get('by') or b)].append(str(r['of']))
        for b, r in self._statements('hold'):
            by, of = str(r.get('by') or b), r.get('of')
            if isinstance(of, str):
                if r.get('as') is not None or r.get('through'):
                    holders[of].append((by, r))
                else:
                    carried[of].append(by)
        places = collections.defaultdict(set)
        for b, r in self._statements('be'):
            if r.get('as') == 'location' and r.get('at'):
                places[str(r.get('by') or b)].add(str(r['at']))
        needs, keepers = collections.defaultdict(set), collections.defaultdict(set)
        for b, r in self._statements('need'):
            for k in (r.get('of') if isinstance(r.get('of'), list) else [r.get('of')]):
                if k:
                    needs[str(r.get('by') or b)].add(str(k))
        for k, holds in list(carried.items()):
            keepers[k] |= set(holds)
        hosts = {b for b, k in self.g.kind.items() if k == 'beans' and (self.g.fm.get(b) or {}).get('kind') == 'host'}

        def volume_of(f, seen=()):
            if f in carried or f in seen:
                return f
            ws = wholes.get(f) or []
            return volume_of(ws[0], seen + (f,)) if ws else f

        def disks_of(v, seen=()):
            """The disks a volume is on: each carrier that is a host; a content that carries it (a container), on
            the disks of every keeping of that content."""
            out = set()
            for c in carried.get(v) or []:
                if c in seen:
                    continue
                if c in hosts:
                    out.add(c)
                for folder, _h in holders.get(c, []):
                    out |= disks_of(volume_of(folder), seen + (v, c))
            return out

        within = None
        now = _pos(self.now or _now(), None, [])
        now = now[1] / 1000 if now and now[0] == 'ms' else None
        out = {}
        for m in self.arg(s, 'of', 'set'):
            keeps, seen = [], set()
            for folder, h in holders.get(m.id, []):
                if h.get('through'):
                    if h['through'] in seen:
                        continue
                    seen.add(h['through'])
                v = volume_of(folder)
                ds = disks_of(v)
                ks = set().union(*[needs.get(x, set()) for x in ds | {v}]) if (ds or v) else set()
                key_ok = all(len(keepers.get(k, ())) >= 2 for k in ks)
                offline = bool(ds) and not any(d in wholes and any(w in hosts for w in wholes[d]) for d in ds)
                keeps.append(storage.Keeping(v, ds, set().union(*[places.get(d, set()) for d in ds]) if ds else (),
                                             offline=offline, key=key_ok))
            codes = [c for c in said.get(m.id, []) if scheme and c.startswith(f"{scheme}:")]
            for folder, _h in holders.get(m.id, []) if scheme and not codes else []:
                f, path = folder, set()                   # the nearest whole a person classed, up `part`
                while f and f not in path and not codes:
                    path.add(f)
                    codes = [c for c in said.get(f, []) if c.startswith(f"{scheme}:")]
                    f = (wholes.get(f) or [None])[0]
            if not codes and scheme:
                mine = said.get(m.id, [])
                codes = [f"{scheme}:{c}" for c, r in policy.items() if set(str(r.get('for') or '').split()) & set(mine)]
            code = codes[0] if codes else None
            row = policy.get(code.split(':', 1)[1]) if code else None
            covers = str(row.get('covers') or '').split() if row else None
            if row and row.get('within'):
                n, u = str(row['within']).split()
                within = _duration_seconds({'count': n, 'unit': u})
            j = storage.judge(keeps, risks, covers, within, now)
            label = (code or 'no policy') + ' · ' + ('safe' if covers is not None and not j['open'] else
                                                    '; '.join(storage.lacking(e) for e in j['open'])
                                                    if j['open'] else 'resolves ' + (', '.join(j['resolved']) or 'nothing'))
            out.setdefault(label, []).append(m)
        return dict(sorted(out.items()))

    def op_datasets(self, s):
        """The folders by the dataset their tree is (core/storage.py `Trees`): a dataset the BLAKE3 of the manifest."""
        from core import formats, storage
        parent, names, files = {}, {}, []
        for b, r in self._statements('part'):
            if r.get('of'):
                parent[str(r.get('by') or b)] = str(r['of'])
        for b, r in self._statements('name'):
            if r.get('as') is not None and r.get('of'):
                names.setdefault(str(r['of']), formats.unescape(str(r['as'])))
        blake = {}
        for b, r in self._statements('name'):
            if r.get('by') == 'blake3' and r.get('of'):
                blake[str(r['of'])] = str(r['as'])
        for b, r in self._statements('hold'):
            by, of = str(r.get('by') or b), r.get('of')
            if isinstance(of, str) and r.get('as') is not None:
                parent.setdefault(by, None)
                files.append((by, formats.unescape(str(r['as'])), blake.get(of), None))
        T = storage.Trees(parent, files, names)
        out = {}
        for m in self.arg(s, 'of', 'set'):
            man = T.manifest(m.id)
            if man is None:
                self.notes.append(f"step {s['id']}: {m.id} holds a file whose content nobody read, or none: no dataset")
                continue
            out.setdefault(formats.blake3_hex(man), []).append(m)
        return dict(sorted(out.items()))

    def op_layout(self, s):
        """Each member beneath a folder a schema is said of, by the node it belongs at and how it stands there
        (core/storage.py `Layout`, `belongs`): over the garden's statements and the stores a step read."""
        from core import formats, storage
        G = self._grouping_law()
        scheme = str(self._value(s, 'scheme'))
        try:
            rows = [dict(r) for r in G['knowledge'].rows(scheme)]
        except (KeyError, OSError) as e:
            raise Refused(f"step {s['id']}: the scheme {scheme} cannot be read here: {e}")
        said, parent, names, holds, blake, made = (collections.defaultdict(list), {}, {}, collections.defaultdict(list),
                                                   {}, {})
        for b, r in self._statements('classify'):
            if r.get('of'):
                said[str(r['of']).split(':', 2)[-1].split('#')[0] if str(r['of']).startswith('store:') else str(r['of'])
                     ].append(str(r.get('as')))
        for b, r in self._statements('part'):
            if r.get('of'):
                parent[str(r.get('by') or b)] = str(r['of'])
        for b, r in self._statements('name'):
            if r.get('of') and r.get('as') is not None:
                if r.get('by') == 'blake3':
                    blake[str(r['of'])] = str(r['as'])
                elif '/' not in str(r['as']):              # a folder's own name: its volume's name of it is its path
                    names.setdefault(str(r['of']), formats.unescape(str(r['as'])))
        for b, r in self._statements('hold'):
            if isinstance(r.get('of'), str) and r.get('as') is not None:
                holds[str(r.get('by') or b)].append((formats.unescape(str(r['as'])), str(r['of'])))
        for b, r in self._statements('produce'):
            if r.get('of'):
                made[str(r['of'])] = (r.get('at'), r.get('by'))
        out = {}
        for m in self.arg(s, 'of', 'set'):
            codes = [c.split(':', 1)[1] for c in said.get(m.id, []) if c.startswith(scheme + ':')]
            if not codes:
                continue
            nodes = storage.nodes_of(rows, codes[0])
            box = any(str(r.get('links') or '') == 'true' for _c, _l, r in nodes)
            apart = set()                                 # the codes that set apart, of every class scheme (`class`)
            for name, srow in G['knowledge'].schemes.items():
                if isinstance(srow, dict) and srow.get('form') == 'class':
                    try:
                        apart |= {f"{name}:{x.get('code')}" for x in G['knowledge'].rows(name)
                                  if str(x.get('apart') or '') == 'true'}
                    except (KeyError, OSError):
                        continue
            kids = collections.defaultdict(list)
            for f, p in parent.items():
                kids[p].append(f)
            rel, stack = {m.id: b''}, [m.id]
            while stack:
                x = stack.pop()
                for k in kids.get(x, ()):
                    rel[k] = rel[x] + b'/' + names.get(k, b'') if rel[x] else names.get(k, b'')
                    stack.append(k)
            held = {(rel[f] + b'/' if rel[f] else b'') + nm: c for f in rel for nm, c in holds.get(f, ())}
            for path, c in sorted(held.items()):
                name = path.rpartition(b'/')[2]
                at, by = made.get(c, (None, None))
                dm = re.search(r'(?<!\d)((?:19|20)\d\d)-(\d\d)-(\d\d)(?!\d)', path.decode('utf-8', 'replace'))
                facts = {'day': str(at)[:10] if at else (dm.group(0) if dm else None), 'maker': by or 'unknown',
                         'name': name, 'blake3': blake.get(c)}
                for code, lay, row in storage.belongs(nodes, said.get(c, []), box, apart):
                    want = lay.path(facts)
                    how = 'in place' if want == path or (box and held.get(want) == c) else \
                        'to link' if box and want else 'out of place'
                    out.setdefault(f"{m.id} · {code} · {how}", []).append(m)
        return dict(sorted(out.items()))

    def op_shared(self, s):
        aspect = next((r for r in (self.reg('aspects') or []) if isinstance(r, dict) and r.get('aspect') == s['aspect']),
                      None)
        if aspect is None:
            from core import read as core_read
            P = core_read.data(os.path.join(ROOT, 'core', 'law', 'profiles.yaml')) or {}
            aspect = next((r for r in P.get('aspects') or [] if r.get('aspect') == s['aspect']), None)
        if aspect is None:
            raise Refused(f"step {s['id']}: `{s['aspect']}` is no aspect of the view's `aspects`")
        verb, role = str(aspect['follows']), str(aspect['points'])
        if verb in self._grouping_law()['groupings']:
            raise Refused(f"step {s['id']}: the aspect {s['aspect']} follows the grouping {verb}: what several cursors "
                          f"share by a grouping is read by bin/group.py, over its groups")
        other = {'by': 'of', 'of': 'by', 'from': 'of', 'to': 'by'}.get(role, 'of')
        cursors = self.arg(s, 'of', 'set')
        reach = collections.defaultdict(set)
        ids = {m.bean for m in cursors}
        for b, fm in self.g.fm.items():
            for x, _w in _flatten(walk(self.g, fm, verb, at=b)):
                if not isinstance(x, dict):
                    continue
                here, there = _own(x.get(role), b), _own(x.get(other), b)
                if here in ids and there:
                    reach[there].add(here)
        for st in getattr(self, '_opened', {}).values():
            if st is None or verb not in st.verbs():
                continue
            for being, _sid, roles in st.statements_of(verb):
                here = _ref_bean(roles.get(role)) or being
                there = _ref_bean(roles.get(other)) or being
                if here in ids and there:
                    reach[there].add(here)
        return {t: [m for m in cursors] for t, c in sorted(reach.items()) if c == ids}

    def op_choose(self, s):
        mechs = [r for r in (self.reg('mechanisms') or []) if isinstance(r, dict)
                 and s['computes'] in (dmparse.split_coding((r.get('computes') or {}).get('property'))[1],
                                       (r.get('computes') or {}).get('property'))]
        if not mechs:
            raise Refused(f"step {s['id']}: no mechanism of the law computes '{s['computes']}'")
        member = self.arg(s, 'of', 'set') if s.get('of') in self.env and isinstance(self.env[s['of']], list) else None
        if member is not None and len(member) != 1:
            raise Refused(f"step {s['id']}: `of` holds {len(member)} beings, and a mechanism reads one")
        codes = set()
        for x, _w in _flatten(walk(self.g, member[0].node, 'is', at=member[0].bean)) if member else []:
            if dmparse.split_coding(x)[0] is not None:
                codes.add(dmparse.split_coding(x))
        covering, why = [], []
        for r in mechs:
            v = r.get('valid') or {}
            wants = {dmparse.split_coding(w) for w in v.get('where') or [] if dmparse.split_coding(w)[0] is not None}
            if wants and not (wants & codes):
                why.append(f"{r['mechanism']}: valid where {sorted(c for _s, c in wants)}, and the being is {sorted(c for _s, c in codes) or 'none of them'}")
                continue
            vals, bad = {}, None
            for inp in r.get('inputs') or []:
                n = inp.get('name')
                if n not in self.env:
                    bad = f"{r['mechanism']}: its input '{n}' is not given"
                    break
                vals[n] = to_unit(self.one(self.env[n], s['id'], n), inp.get('unit'), f"{r['mechanism']}.{n}")
            if bad:
                why.append(bad)
                continue
            for rg in v.get('ranges') or []:
                x, e = vals.get(rg.get('input')), rg.get('extent') or {}
                lo = to_unit(value_of(e['from'], 'from', self.notes), x.unit, 'range').v if isinstance(e.get('from'), dict) else None
                hi = to_unit(value_of(e['to'], 'to', self.notes), x.unit, 'range').v if isinstance(e.get('to'), dict) else None
                if x is not None and ((lo is not None and x.v < lo) or (hi is not None and x.v > hi)):
                    bad = f"{r['mechanism']}: {rg.get('input')} {show(x)} lies outside the range it was fitted over"
            if bad:
                why.append(bad)
                continue
            covering.append((r, vals))
        if not covering:
            raise Refused(f"step {s['id']}: no mechanism is valid for this case — " + '; '.join(why)
                          + " — a reading outside a mechanism's domain is never guessed")
        results = []
        for r, vals in covering:
            sub = Reckoner(self.g, self.bean, vals, self.pin, self.zone, self.now)
            sub.env.update(vals)
            _op, v = sub.run({'steps': r.get('steps') or []})
            v = self.one(v, s['id'], r['mechanism'])
            res = r.get('residual') or {}
            sig = res.get('validated') or res.get('sigma')
            if isinstance(sig, dict):
                sv = dmseq.exact(sig.get('count'))
                form = res.get('form')
                if form == 'absolute':
                    v.u = to_unit(V(sv, sig.get('unit')), v.unit, 'residual').v
                elif form in ('relative', 'log'):
                    v.u = abs(v.v) * sv
                    v.approx = v.approx or form == 'log'
            results.append((sig and dmseq.exact(sig.get('count')) or Fraction(0), r['mechanism'], v, sub.lines))
        results.sort(key=lambda t: t[0])
        best = results[0]
        self.lines.extend('    ' + ln for ln in best[3])
        self.lines.append(f"  chosen: {best[1]} (the smallest validated error of {len(results)} valid)")
        for _e, name, v, _l in results[1:]:
            self.notes.append(f"step {s['id']}: {name} gives {show(v)} — the spread")
        return best[2]

    def op_rotate(self, s):
        raise Refused(f"step {s['id']}: `rotate` reads a pole's rows of `coefficients`, and the law holds none yet — a "
                      f"plate's published pole is added as coefficient rows with their source")

    def op_position_to(self, s):
        try:
            import pyproj  # noqa: F401
        except ImportError:
            raise Refused(f"step {s['id']}: `position-to` needs PROJ (pyproj), and this machine has none — no "
                          f"transformation is guessed") from None
        raise Refused(f"step {s['id']}: `position-to` through PROJ is not wired: no transformation is guessed, and none "
                      f"is read until a garden's tools carry PROJ and a test holds its result")


_FORMULA = re.compile(r'([A-Z][a-z]?)([0-9]*)|(\()|(\))([0-9]*)', re.ASCII)


# ============================================================================ a rule's reading (core 3.0)
def law_table(L, name, manifest=None):
    """The rows of the law's table `name` — any its columns declare (core 3.2, I.6) — the garden's own with them, each
    marked `garden: true`, each a member: its id and its proof `law:<table>[<row>]`; `stands`, each level's stands with
    its level as `by`; `manifest`, the manifest's keys, each with the value the garden's GARDEN.md gives it (`value`)."""
    from core.law import listed
    if name == 'stands':               # the law's own ladder: each level stands at what its rows say, as they say
        out = []
        for lv, r in L.levels.items():
            for k, st in enumerate(listed((r or {}).get('stands'))):
                if isinstance(st, dict):
                    w = f"law:levels[{lv}].stands[{k}]"
                    out.append(Row(w, dict(st, by=lv), None, proof=(w,)))
        return out
    got = L.input_rows(name)
    if got is None:
        raise Refused(f"`{name}` is no table of the law a reading takes: a table the law's columns declare "
                      f"({', '.join(sorted(L.declared_tables()))})")
    key, items = got
    out = []
    for k, r, mine in items:
        node = dict(r if isinstance(r, dict) else {}, **{key: k})
        if mine:
            node['garden'] = 'true'
        if name == 'manifest' and isinstance(manifest, dict) and manifest.get(k) is not None:
            node['value'] = manifest[k]
        out.append(Row(f"law:{name}[{k}]", node, None, proof=(f"law:{name}[{k}]",)))
    return out


_LAW_ROW = re.compile(r'^law:([a-z_]+)\[([^\]]+)\](?:\.stands\[([0-9]+)\])?$')


def law_row(L, item):
    """The row of the law a proof's item `law:<table>[<row>]` names (a level's stand: `law:levels[<level>].stands[<k>]`),
    or None — where the item names a table whole (`law:<table>`: a refusal that rests on no row of it agreeing)."""
    from core.law import listed
    m = _LAW_ROW.match(item)
    if not m:
        return None
    table, key, k = m.groups()
    got = L.input_rows(table) if table != 'levels' else ('level', [(n, r, False) for n, r in L.levels.items()])
    row = next((r for n, r, _g in (got[1] if got else []) if str(n) == key), None)
    if k is not None:
        stands = listed((row or {}).get('stands'))
        return stands[int(k)] if int(k) < len(stands) else None
    return row


class Judged:
    """The garden a rule's reading reads: every document the engine judges (core/engine.py `Garden`), beans and mappings
    alike, each viewed as its header and its verbs, in the order the garden is read in; and the engine's `Judge`, by
    which a filler is read as the being it names and a being's kind is known. Read once for a Judge."""

    def __init__(self, J):
        self.J, self.root, self.pin = J, J.G.root, None
        self.fm, self.kind, self.order, self.places = {}, {}, {}, {}
        n = 0
        for k, b in enumerate(J.G.beans.values()):
            v = {'bean': b.id}
            if b.kind is not None:
                v['kind'] = b.kind
            for key in ('title', 'summary', 'tags', 'details'):    # the rest of its header (core 3.3: `**` reads it)
                if isinstance(b.header, dict) and key in b.header:
                    v[key] = b.header[key]
            for i, verb, r in b.items:
                v.setdefault(verb, []).append(r)
                self.places[id(r)] = (f"{b.id}[{i}] {verb}", n)
                n += 1
            self.fm[b.id], self.kind[b.id], self.order[b.id] = v, 'beans', k

    def bean(self, i):
        if i not in self.fm:
            raise Refused(f"no bean or mapping '{i}' here")
        return self.fm[i]


_SLOT = re.compile(r'\{([a-z0-9_][a-z0-9_.-]*)(:set)?\}')
STATEMENT_COLUMNS = ('bean', 'verb', 'index', 'place', 'id')       # of a statement (core 3.2, I.1)
POSITION_COLUMNS = ('system', 'point', 'from', 'to')               # of a position (core 3.3, I.2)


def described(L):
    """describe's columns, in the order it writes them: a being's, its kind's position on each facet of the ladder, one
    column a line, named by the line (core 4.0), then a statement's and a position's."""
    return ('being', 'kind', 'nature') + tuple(getattr(L, 'facets', ()) or ()) + STATEMENT_COLUMNS + POSITION_COLUMNS


def position_cols(v, systems, zone):
    """The columns of a position (core 3.3, I.2) that the value `v` is, read by `systems` in `zone`: its `system`;
    `point`, whether it names a point — its system covers one (core/frame.py `covers_point`); and its span, `from` and
    `to`, to the moment — a day its whole, an extent to the end of its end — each written as a moment in UTC to the
    millisecond. None for `now`, `unknown`, `self`, or a text no system reads. The one reader of them: the reckoner's
    `describe` and the store's SQL (core/union.py) call it."""
    none = dict.fromkeys(POSITION_COLUMNS)
    if not isinstance(v, str) or v in ('self', 'now', 'unknown'):
        return none
    from core import frame
    try:
        p = frame.read(v, systems, zone)
    except frame.Refused:
        return none
    sp = frame.span(p)
    return {'system': p.system, 'point': 'true' if frame.covers_point(p, systems) else 'false',
            'from': dmcal.write_moment(sp[0], 'gregorian-civil', 'Z', 'millisecond') if sp else None,
            'to': dmcal.write_moment(sp[1], 'gregorian-civil', 'Z', 'millisecond') if sp else None}


def span_end(found, end, zone, notes):
    """One end of a span in milliseconds, from what a path found (`walk`): one moment, or a day — its start, or the end
    of it where `end` — else None. The one reader of an `overlap`'s span: the reckoner and the store's SQL call it."""
    p = _pos(found[0][0], zone, notes) if len(found) == 1 else None
    if p is None:
        return None
    return p[1] if p[0] == 'ms' else (p[1] + (1 if end else 0)) * dmcal.DAY_MS


def _writ(v):
    """A value of a refusal's words, as text: a list with ` → ` between its items; a being a `describe` read, as it was
    written, or a `someone` by its kind."""
    if isinstance(v, list):
        return ' → '.join(_writ(x) for x in v)
    if isinstance(v, dict) and {'being', 'kind', 'nature', *STATEMENT_COLUMNS, *POSITION_COLUMNS} <= set(v):
        return v['being'] if isinstance(v['being'], str) else v['place'] if v.get('place') else str(v['kind'])
    return str(v)


def written(message, m, garden=None):
    """A refusal's words: `message`, each `{<path>}` in it the value at that path of the member `m`, as text — and each
    `{<path>:set}` the values at the path, a list's items each, every one once and written as text, in the order of
    their characters, with `, ` between them (core 3.2, I.9). Nothing in it is evaluated."""
    def one(mo):
        found = walk(garden, m.node, mo.group(1), at=m.bean)
        if mo.group(2):
            return ', '.join(sorted({_writ(x) for v, _w in found for x in (v if isinstance(v, list) else [v])
                                     if x is not None}))
        return _writ(found[0][0]) if found else 'None'
    return _SLOT.sub(one, message)


def refusals(J, reading, rule=None):
    """[(place, words, proof)]: what a rule's reading refuses in the garden the engine's Judge `J` judges, by `J`'s law —
    each refusal at the place of its statement, in the order of the reading's `refuse` and of each step's members. Its
    steps are kept on `J` under `rule`, for a later rule that takes one as an input (core 3.2, I.5)."""
    g = getattr(J, '_judged', None)
    if g is None:
        g = J._judged = Judged(J)
    from core import lines
    rk = Reckoner(g, rules_law=J.L)
    rk.run(lines.worded(reading))                  # its conditions in the core's signs, each in the reader's word
    if rule is not None:
        if getattr(J, '_steps', None) is None:
            J._steps = {}
        J._steps[rule] = {k: v for k, v in rk.env.items() if isinstance(v, list)}
    out = []
    for ref in reading.get('refuse') or []:
        for m in rk.env.get(ref.get('of')) or []:
            mr = as_row(m)
            out.append((told_at(mr.place, ref), written(str(ref.get('message') or ''), mr, g), mr.proof))
    return out


AT_PATH = re.compile(r'^[a-z0-9_][a-z0-9_-]*(\.[a-z0-9_][a-z0-9_-]*)*$', re.ASCII)   # a refusal's `at`: keys alone


def told_at(place, ref):
    """Where a refusal of `ref` is told: the place of its member's statement (`<bean>[<i>] <verb>`) — with `at`, a path
    of the statement's keys, at that path inside it, `<bean>[<i>] <verb>.<at>` (core 3.4, I.9). A member that is no
    statement has no place, and none is made for it."""
    at = ref.get('at') if isinstance(ref, dict) else None
    return f"{place}.{at}" if place and isinstance(at, str) else place


def chains(reading):
    """[(verb, low, high, message)]: the chains a rule's reading holds acyclic — each `cycle` within the beans that judges
    one verb's statements, from its `from` paths to its `to` paths, and the words of the refusal it leads to. What the
    cursor walks and a store's check holds, read from the law and stated nowhere else."""
    if not isinstance(reading, dict):
        return []
    steps = {s.get('id'): s for s in reading.get('steps') or [] if isinstance(s, dict)}
    out = []
    for ref in reading.get('refuse') or []:
        s, seen = steps.get(ref.get('of')), set()
        while s is not None and s.get('op') != 'cycle' and s.get('id') not in seen:
            seen.add(s.get('id'))
            s = steps.get(s.get('of'))
        if s is None or not s.get('within'):
            continue
        sel = steps.get(s.get('of')) or {}
        if sel.get('op') == 'select' and isinstance(sel.get('entries'), str):
            out.append((sel['entries'], tuple(_paths(s.get('from'))), tuple(_paths(s.get('to'))),
                        str(ref.get('message') or '')))
    return out


def check_rule(where, reading, law_, law=None, earlier=None):
    """[(level, text)] for a rule's reading against the grammar: its steps as any reading's (`check_selection`); its
    inputs the law's tables, said by the law — any the law's columns declare, by `law` (a core.law.Law) — or a step of a
    rule before it in the law's order (`earlier`: {rule: its reading}); a row `fits` names one of the law; its `refuse`
    naming its steps, each with its words."""
    if not isinstance(reading, dict):
        return [('error', f"{where}: a rule's reading is a mapping of `inputs`, `steps` and `refuse`")]
    out = [('error', f"{where}: `{k}` is not what a rule's reading holds — `inputs`, `steps`, `refuse`")
           for k in reading if k not in ('inputs', 'steps', 'refuse')]
    for n, d in enumerate(reading.get('inputs') or []):
        o = d.get('origin') if isinstance(d, dict) and isinstance(d.get('origin'), dict) else {}
        f = d.get('from') if isinstance(d, dict) else None
        if isinstance(f, dict):
            r, st = f.get('rule'), f.get('step')
            steps = {s.get('id') for s in ((earlier or {}).get(r) or {}).get('steps') or [] if isinstance(s, dict)}
            if set(d) != {'name', 'from'} or set(f) != {'rule', 'step'} or st not in steps:
                out.append(('error', f"{where}.inputs[{n}]: an input from an earlier rule is `{{name, from: {{rule, "
                                     f"step}}}}`, a step of a rule that is a reading before this one in the law's order "
                                     f"({', '.join(earlier or {}) or 'none'})"))
            continue
        if not (o.get('act') == 'say' and o.get('by') == 'law') or not (
                law.declares(str(d.get('name'))) if law is not None else d.get('name') in ('crown', 'kinds', 'lines', 'stands')):
            out.append(('error', f"{where}.inputs[{n}]: a rule's reading takes the law's tables, said by the law "
                                 f"(`{{name: <table>, origin: {{act: say, nature: sayable, by: law}}}}`), a table the "
                                 f"law's columns declare, or a step of an earlier rule (`{{name, from: {{rule, step}}}}`)"))
    for s in reading.get('steps') or []:
        for c in (s.get('where') or []) if isinstance(s, dict) and isinstance(s.get('where'), list) else []:
            if isinstance(c, dict) and 'fits' in c and law is not None:
                try:
                    law.fits_row(c['fits'])
                except ValueError as e:
                    out.append(('error', f"{where}.steps[{s.get('id')}]: {e}"))
    from core import lines
    out += check_selection(where, lines.worded(reading), law_)
    ids = {s.get('id') for s in reading.get('steps') or [] if isinstance(s, dict)}
    refuse = reading.get('refuse')
    if not isinstance(refuse, list) or not refuse:
        out.append(('error', f"{where}: `refuse` names the steps whose members are the rule's refusals"))
    for n, r in enumerate(refuse if isinstance(refuse, list) else []):
        if not isinstance(r, dict) or set(r) - {'at'} != {'of', 'message'} or r.get('of') not in ids \
                or not isinstance(r.get('message'), str):
            out.append(('error', f"{where}.refuse[{n}]: a refusal is "
                                 f"`{{of: <a step>, at?: <path>, message: <words>}}`"))
        elif 'at' in r and not (isinstance(r['at'], str) and AT_PATH.match(r['at'])):
            out.append(('error', f"{where}.refuse[{n}]: `at` is a path of the statement's keys, each one key "
                                 f"(`clause.by_role`) — not {r['at']!r}"))
    return out


def formula(f):
    """{element: count} of a chemical formula — `C6H12O6`, `Ca(OH)2`."""
    stack, i = [collections.Counter()], 0
    while i < len(f):
        m = _FORMULA.match(f, i)
        if not m:
            raise Refused(f"'{f}' is not a formula this reader reads (at character {i + 1})")
        if m.group(1):
            stack[-1][m.group(1)] += int(m.group(2) or 1)
        elif m.group(3):
            stack.append(collections.Counter())
        else:
            inner = stack.pop()
            for k, v in inner.items():
                stack[-1][k] += v * int(m.group(5) or 1)
        i = m.end()
    return dict(stack[0])


# ============================================================================ the API
def _now():
    t = time.gmtime()
    return '%04d-%02d-%02dT%02d:%02dZ' % t[:5]


def _find(g, ref):
    if ref.startswith('ordering_keys:'):
        k = ref.split(':', 1)[1]
        row = next((r for r in law().registry('ordering_keys') or [] if isinstance(r, dict) and r.get('key') == k), None)
        if row is None:
            raise Refused(f"the law has no ordering key '{k}'")
        return None, row
    if '#' in ref and ':' not in ref:
        ref = ref.replace('#', ':', 1)                   # a reading of the core, named as a statement: <bean>#<id>
    if ':' not in ref:
        raise Refused(f"a reading is named `<bean>:<selection>` — not {ref!r}")
    bean, key = ref.split(':', 1)
    sel = g.bean(bean).get('selections')
    if not isinstance(sel, dict) or key not in sel:
        raise Refused(f"bean '{bean}' declares no reading '{key}'" + (f" — it declares {sorted(sel)}" if isinstance(sel, dict) else ''))
    return bean, sel[key]


def _result(kind, value, rk, pin):
    u = value.u if isinstance(value, V) else None
    unit = value.unit if isinstance(value, V) else None
    if rk.independent:
        rk.notes.append("u: uncertainties combined in quadrature, each input taken as independent of the others "
                        "(GUM 5.1.2) — inputs that are correlated would make it larger or smaller, and are not modelled")
    return Result(kind, value, u, unit, rk.lines, pin, rk.notes)


def evaluate(ref, *, root=ROOT, inputs=None, pin=None, entry=None, bean=None, now=None):
    """The reading `ref` (`<bean>:<key>`, or `ordering_keys:<key>`), read now — or at `pin`."""
    g = Garden(root, pin)
    if entry is None:
        bean, entry = _find(g, ref)
    rk = Reckoner(g, bean, inputs, pin, now=now)
    op, v = rk.run(entry)
    kind = next((r.get('gives') for o, r in rk.ops.items() if o == op), 'value')
    return _result(kind, v, rk, pin)


def select(ref, **kw):
    r = evaluate(ref, **kw)
    if not isinstance(r.value, list):
        raise Refused(f"{ref} gives a {r.kind}, not a set")
    return [m.id for m in r.value]


def holds(ref, **kw):
    r = evaluate(ref, **kw)
    if isinstance(r.value, list):
        return bool(r.value)
    return r.value if r.value in (True, False, None) else bool(r.value)


def occurrences(bean, clause, *, root=ROOT, pin=None, now=None):
    """[(member, at)] of an `each` clause: each member its selection holds, with the moment it entered — the first move
    of its course into the step `reached` names, or the member's own `at` — or None where nothing says when."""
    g = Garden(root, pin)
    c = (g.bean(bean).get('clauses') or {}).get(clause)
    if not isinstance(c, dict) or not c.get('each'):
        raise Refused(f"{bean} has no clause '{clause}' that occurs for each member of a selection")
    ref = c['each'] if ':' in c['each'] else f"{bean}:{c['each']}"
    sb, entry = _find(g, ref)
    rk = Reckoner(g, sb, None, pin, now=now)
    _op, v = rk.run(entry)
    if not isinstance(v, list):
        raise Refused(f"{ref} gives a value, not a set: an `each` clause occurs for the members of a set")
    out = []
    for m in v:
        at = rk.entered.get(m.id)
        if at is None and isinstance(m.node, dict) and m.node.get('at') is not None:
            at = _text(m.node['at'])
            at = str(at) if at is not None else None
        out.append((m.id, at))
    return out


def used(bean, clause, attr, *, at, root=ROOT, pin=None, zone=None):
    """(V, lines) — how much of a clause's allowance the members of its `used_by` selection use inside the window of
    its `within` ending at `at`, read from each member's `attr` (N9, read for AGREE's ledger)."""
    g = Garden(root, pin)
    c = (g.bean(bean).get('clauses') or {}).get(clause) or {}
    if not isinstance(c.get('used_by'), str) or not c['used_by']:
        raise Refused(f"{bean}:clauses.{clause} names no `used_by` — the selection of the entries that use its allowance")
    ref = c['used_by'] if ':' in c['used_by'] else f"{bean}:{c['used_by']}"
    sb, entry = _find(g, ref)
    rk = Reckoner(g, sb, None, pin, zone=zone)
    _op, v = rk.run(entry)
    if not isinstance(v, list):
        raise Refused(f"{ref} gives a value, not a set: `used_by` names the entries that use the allowance")
    rk.env['@used'] = v
    x = rk.op_used_within({'id': 'used', 'of': '@used', 'path': attr, 'within': c.get('within'), 'at': at})
    return x, rk.lines


# ============================================================================ the command line
def _print(r, t0, exact_=False, out=sys.stdout):
    for ln in r.lines:
        print(ln, file=out)
    v = r.value
    if isinstance(v, list):
        print(f"= a set of {len(v)}", file=out)
        for m in v:
            extra = ', '.join(f"{k}: {x}" for k, x in m.node.items()) if isinstance(m.node, dict) and m.bean is None else ''
            print(f"  {m.id}" + (f"  ({extra})" if extra else ''), file=out)
    elif isinstance(v, dict):
        print("= groups", file=out)
        for k, x in v.items():
            print(f"  {k}: {show(x, exact_) if isinstance(x, V) else (len(x) if isinstance(x, list) else x)}", file=out)
    elif v is True or v is False:
        print(f"= {str(v).lower()}", file=out)
    elif v is None:
        print("= NOT KNOWN", file=out)
    else:
        print(f"= {show(v, exact_)}", file=out)
        if isinstance(v, V) and len(v.budget) > 1:
            tot = sum(v.budget.values())
            print("  the variance's shares: " + ', '.join(f"{k} {dmseq.rounded(x * 100 / tot, 0)} %"
                                                          for k, x in sorted(v.budget.items(), key=lambda t: -t[1])), file=out)
        if isinstance(v, V) and v.u is None and isinstance(v.v, Fraction) and not v.approx:
            print("  exact (u not stated)", file=out)
    for n in r.notes:
        print(f"  note: {n}", file=out)
    if r.pin:
        print(f"  read at {r.pin.commit}, the clock {r.pin.at}", file=out)
    print(f"  ({dmseq.rounded(Fraction(time.monotonic_ns() - t0, 10 ** 9), 3)} s)", file=out)


def weigh(bean, key, root=ROOT):
    g = Garden(root)
    e = (g.bean(bean).get('weighings') or {}).get(key)
    if not isinstance(e, dict):
        raise Refused(f"{bean} has no weighing '{key}'")
    for lv, t in check_weighing(f"{bean}:{key}", e):
        print(f"{lv}: {t}")
    crit, w, lam, ci, cr = weights(e)
    print(f"the weighing {bean}:{key}, for `{e.get('for')}`, judged by {e.get('judge')}:")
    for a in sorted(crit, key=lambda a: -w[a]):
        print(f"  {a}: ≈ {dmseq.rounded(w[a], 3)}")
    print(f"  λmax ≈ {dmseq.rounded(lam, 4)}, CI ≈ {dmseq.rounded(ci, 4)}, CR ≈ {dmseq.rounded(cr, 3)}"
          + (f" — above {consistency_bound()[0]}" if cr > consistency_bound()[1] else ''))
    print("  (read, never stored: a weighing orders what a person is shown, and decides nothing)")


def order(key, tsv, root=ROOT):
    """Items (a table: `item`, then one column per input of the key) ordered by the key's reading, greatest first."""
    head, rows = dmparse.table_read(open(tsv, encoding='utf-8', newline='').read())
    if 'item' not in head:
        raise Refused(f"{tsv}: the table's first column is `item`")
    scored = []
    for r in rows:
        given = {h: c for h, c in zip(head, r) if h != 'item'}
        res = evaluate(f"ordering_keys:{key}", root=root, inputs=given)
        scored.append((res.value.v if isinstance(res.value, V) else Fraction(0), r[head.index('item')], res.value))
    scored.sort(key=lambda t: (-t[0], t[1]))
    for _s, item, v in scored:
        print(f"{item}\t{show(v)}")


def main(argv):
    args, inputs, at, moment, adhoc, bean, exact_ = [], {}, None, None, None, None, False
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--input' and i + 1 < len(argv):
            k, _, v = argv[i + 1].partition('=')
            inputs[k] = v
            i += 2
        elif a == '--at' and i + 1 < len(argv):
            at, i = argv[i + 1], i + 2
        elif a == '--moment' and i + 1 < len(argv):
            moment, i = argv[i + 1], i + 2
        elif a == '--ad-hoc' and i + 1 < len(argv):
            adhoc, i = argv[i + 1], i + 2
        elif a == '--bean' and i + 1 < len(argv):
            bean, i = argv[i + 1], i + 2
        elif a == '--exact':
            exact_, i = True, i + 1
        elif a in ('-h', '--help'):
            print(__doc__)
            return 0
        else:
            args.append(a)
            i += 1
    t0 = time.monotonic_ns()
    try:
        if args[:1] == ['weigh'] and len(args) == 2 and (':' in args[1] or '#' in args[1]):
            weigh(*re.split(r'[:#]', args[1], 1))             # `<bean>#<id>` names a `weigh` in a garden of the core
            return 0
        if args[:1] == ['order'] and len(args) == 3:
            order(args[1], args[2])
            return 0
        if (at is None) != (moment is None):
            raise Refused("a pinned reading names both the commit (`--at`) and the moment it was read at (`--moment`)")
        pin = Pin(at, moment, None) if at else None
        if adhoc:
            entry = dmparse.loads(open(adhoc, encoding='utf-8').read())
            if dmseq.runs_core(ROOT) and isinstance(entry, dict):
                from core import lines                    # the core's signs, in the words the reader applies
                from core import read as core_read        # read as the core reads: every value a string (part 12b:
                entry = core_read.loads(open(adhoc, encoding='utf-8').read(), adhoc) or entry   # `digits: true`)
                bad = lines.reading_problems(adhoc, entry, law(), dmseq.core(ROOT)[0].verbs)
                if bad:
                    for w, msg in bad:
                        print(f"error: {w}: {msg}")
                    return 1
                entry = lines.worded(lines.typed(entry))
            probs = check_selection(adhoc, entry, law())
            if probs:
                for lv, t in probs:
                    print(f"{lv}: {t}", file=sys.stderr)
                return 1
            r = evaluate(None, inputs=inputs, pin=pin, entry=entry, bean=bean)
            print(f"an ad-hoc reading ({adhoc}), committed by nobody:")
        elif len(args) == 1:
            r = evaluate(args[0], inputs=inputs, pin=pin)
        else:
            print(__doc__)
            return 2
        _print(r, t0, exact_)
        return 0
    except Refused as e:
        print(f"refused: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
