#!/usr/bin/env python3
"""dmreckon — the one reckoner: a reading declared in the law's grammar (`selection_form`), read each time it is asked.

    python3 bin/dmreckon.py <bean>:<selection> [--input name=value ...] [--at <commit> --moment <moment>]
    python3 bin/dmreckon.py --ad-hoc <file.yaml> [--bean <bean>] [--input name=value ...]   # a reading nobody committed
    python3 bin/dmreckon.py weigh <bean>:<weighing>          # a weighing's weights and its consistency, read
    python3 bin/dmreckon.py order <key> <items.tsv>          # items ordered by an ordering key of the law
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
`rotate` until PLACE's pole rows land; a distance between places (`within` a place, `neighbour-of` by distance,
`travelled` on a map) until PLACE's bin/dmgeo.py reads one; an input read from another garden until AGREE's
bin/dmacross.py lands.

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
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse  # noqa: E402 — the one reader of a path, a table and a front matter
import dmcal    # noqa: E402 — positions in any calendar, moments, civil offsets
import dmseq    # noqa: E402 — a series' rows and what a channel holds between them

ROOT = os.path.dirname(HERE)
PY = 'python' if os.name == 'nt' else 'python3'
KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$', re.ASCII)
COMMIT = re.compile(r'^[0-9a-f]{7,40}$', re.ASCII)
PREC = 40                                          # the digits a value that is not exact is carried to, never printed

Pin = collections.namedtuple('Pin', 'commit at garden')
Result = collections.namedtuple('Result', 'kind value u unit lines pin notes')
Member = collections.namedtuple('Member', 'id node bean')   # a bean (node = its front matter) or one of its entries


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
    """The gate's reading of the law (dmseq's Law: units, quantities, systems, a registry by name)."""
    if not _LAW:
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
class Garden:
    """The front matter of every bean and mapping of one garden, as it stands now or at a commit."""

    def __init__(self, root=ROOT, pin=None):
        self.root, self.pin = root, pin
        self.fm, self.kind = {}, {}
        if pin is not None:
            self._check_pin()
            names = self._git('ls-tree', '-r', '--name-only', pin.commit, '--', 'beans', 'mappings').split('\n')
            for p in names:
                if p.endswith('.md') and p.count('/') == 1:
                    self._add(p, self._git('show', f"{pin.commit}:{p}"))
        else:
            for d in ('beans', 'mappings'):
                full = os.path.join(root, d)
                for n in sorted(os.listdir(full)) if os.path.isdir(full) else []:
                    if n.endswith('.md'):
                        try:
                            head, _ = dmparse.read(os.path.join(full, n))
                        except Exception:
                            continue
                        self._put(f"{d}/{n}", head)

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
            self.fm[str(i)], self.kind[str(i)] = fm, path.split('/')[0]

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


def walk(garden, node, text, at=None):
    """[(value, where)] at a field path from `node` (the front matter or an entry of bean `at`) — `where` the path to
    each value as `<bean>:<keys>`, so a member of a set can be named."""
    segs = dmparse.path_read(text)
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
            if isinstance(v, dict):
                items = v.items() if s.star else ([(s.key, v[s.key])] if s.key in v else [])
                for k, x in items:
                    out.append((x, f"{w}{sep}{k}"))
            elif isinstance(v, list) and (s.star or s.key == 'entries'):
                for n, x in enumerate(v):
                    ident = x.get('id') if isinstance(x, dict) and isinstance(x.get('id'), str) else n
                    out.append((x, f"{w}[{ident}]"))
            elif isinstance(v, list):
                for n, x in enumerate(v):   # a key into a list reads each entry that holds it
                    if isinstance(x, dict) and s.key in x:
                        out.append((x[s.key], f"{w}[{x.get('id', n)}].{s.key}"))
        if s.match:
            a, want = s.match
            out = [(x, w) for x, w in _flatten(out) if isinstance(x, dict) and str(x.get(a)) == want]
        cur = out
    return cur


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
def _pos(x, zone, notes):
    """A position as ('ms', milliseconds) for a moment, or ('day', n) for a day — or None."""
    s = str(x).strip()
    try:
        return ('ms', dmcal.moment(s).ms)
    except (ValueError, dmcal.NotByRule):
        pass
    try:
        return ('day', dmcal.to_day(s))
    except (ValueError, dmcal.NotByRule):
        return None


def _local_day(ms, zone, instant):
    off = dmcal.offset(zone, instant) if zone else 0
    return (ms + off * 60000) // dmcal.DAY_MS


def pos_cmp(a, b, zone):
    """-1, 0 or 1: two positions ordered — a moment against a day through the day it falls on in the reading's zone."""
    pa, pb = _pos(a, zone, []), _pos(b, zone, [])
    if pa is None or pb is None:
        raise Refused(f"{a!r} and {b!r} are not two positions of time this reader orders")
    if pa[0] != pb[0]:
        if not zone:
            raise Refused(f"{a!r} against {b!r}: a moment is read against a day in a civil zone — the reading states `zone`")
        pa = ('day', _local_day(pa[1], zone, a)) if pa[0] == 'ms' else pa
        pb = ('day', _local_day(pb[1], zone, b)) if pb[0] == 'ms' else pb
    return (pa[1] > pb[1]) - (pa[1] < pb[1])


# ============================================================================ the gate's check (pure)
def _takes_check(where, step, row, env, law_):
    """A step against its operation's row: its keys are those the row takes, the required ones present, a name a step
    reads an earlier step or an input, a path a path, an enum a value of it."""
    out = []
    takes = row.get('takes') or {}
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
        if isinstance(dom, dict) and dom.get('type') == 'kebab' and k in ('of', 'with', 'series'):
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


def check_weighing(where, entry):
    """Every pair of criteria judged once, each pair naming criteria; CR ≤ 0.10, or `why_inconsistent` says why not."""
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
        if cr > Fraction(1, 10) and not entry.get('why_inconsistent'):
            out.append(('error', f"{where}: its consistency ratio is {dmseq.rounded(cr, 2)}, above 0.10 — the judgments "
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
    def __init__(self, garden, bean=None, inputs=None, pin=None, zone=None, now=None):
        self.g, self.bean, self.pin, self.zone = garden, bean, pin, zone
        self.given = dict(inputs or {})
        self.now = now
        self.env, self.lines, self.notes = {}, [], []
        self.entered = {}          # member id -> the moment it entered, where a `reached` condition read one (AGREE)
        self.reg = law().registry
        self.ops = op_rows(self.reg)
        self.k = k_factor(self.reg)

    # -- inputs
    def bind_inputs(self, decls):
        for d in decls or []:
            if not isinstance(d, dict):
                continue
            n, o = d.get('name'), d.get('origin')
            if o == 'clock':
                at = self.pin.at if self.pin else (self.now or _now())
                self.env[n] = V(at)
                self.lines.append(f"input {n}: the clock, {at}")
            elif o == 'garden':
                # ACROSS GARDENS (N35): read at a commit the other garden published and granted, never copied here; a
                # pin naming that garden reads it again at the pinned commit.
                import dmacross
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
            elif n in self.given:
                self.env[n] = self._given(n, self.given[n], d)
                self.lines.append(f"input {n} ({o}): {show(self.env[n])}")
            else:
                raise Refused(f"the reading takes the input '{n}' ({o}), and it is not given — "
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
    def op_select(self, s):
        if 'of' in s:
            base = self.arg(s, 'of', 'set')
        else:
            base = [Member(i, fm, i) for i, fm in sorted(self.g.fm.items()) if self.g.kind[i] == 'beans'
                    and ('genos' not in s or fm.get('genos') == s['genos'])]
        if s.get('entries'):
            out = []
            for m in base:
                for x, w in _flatten(walk(self.g, m.node, s['entries'], at=m.bean)):
                    out.append(Member(w, x, m.bean))
            base = out
        return [m for m in base if self.meets(m, s.get('where') or [])]

    def meets(self, m, conds):
        for c in conds:
            comp = next(k for k in c if k != 'path')
            if not self.cond(m, c['path'], comp, self.operand(c[comp])):
                return False
        return True

    def cond(self, m, path, comp, operand):
        found = walk(self.g, m.node, path, at=m.bean)
        vals = [x for x, _ in found]
        if comp == 'exists':
            return bool(vals) and any(x is not None for x in vals)
        if comp == 'absent':
            return not vals or all(x is None for x in vals)
        if comp in ('reached', 'at_step'):
            return any(self._course(m, w, comp, operand) for x, w in found)
        return any(self._one_cond(x, comp, operand) for x in vals)

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
                try:
                    b = to_unit(b, a.unit, 'a comparison')
                except Refused:
                    return None
            return (a.v > b.v) - (a.v < b.v)
        if isinstance(a.v, str) and isinstance(b.v, str):
            try:
                return pos_cmp(a.v, b.v, self.zone)
            except Refused:
                return None
        return None

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
            at = str(hit[0]['at'])
            prev = self.entered.get(m.id)
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
            return V(sum(v.v for v in vs), unit, hyp(*[v.u for v in vs]),
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

        def cmp(a, b):
            c = self._cmp(a[0], b[0])
            if c is None:
                raise Refused(f"step {s['id']}: {a[1].id} and {b[1].id} are not ordered one against the other")
            return c
        keyed.sort(key=functools.cmp_to_key(cmp), reverse=s.get('direction') == 'descending')
        return [m for _v, m in keyed]

    def op_group(self, s):
        out = {}
        for m in self.arg(s, 'of', 'set'):
            found = walk(self.g, m.node, s['path'], at=m.bean)
            if len(found) != 1:
                raise Refused(f"step {s['id']}: {m.id} holds {len(found)} values at `{s['path']}`, where one groups it")
            x = found[0][0]
            label = self._cell(x, s) if s.get('level') else (x.get('bean') if isinstance(x, dict) and 'bean' in x else str(x))
            out.setdefault(label, []).append(m)
        return dict(sorted(out.items()))

    def _cell(self, x, s):
        """The cell of a calendar level a moment or a day falls in, read in the reading's zone."""
        cal = s.get('system') or 'gregory'
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
            ud = hyp(a.u, b.u)
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
        return V(a.v - b.v, a.unit, hyp(a.u, b.u), a.approx or b.approx, {**a.budget, **b.budget} or budget(
            **{s.get('of'): a.u, s.get('with'): b.u}))

    def _rel(self, r, a, b, na, nb):
        """The relative rule: u(r)/|r| = √((u(a)/a)² + (u(b)/b)²)."""
        parts = {}
        for n, x in ((na, a), (nb, b)):
            if x is not None and x.u is not None and x.v:
                parts[n] = (x.u / abs(x.v)) ** 2 * r * r
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
            rows = [r for r in rows if any(isinstance(w, dict) and str(w.get('code')) == str(code) for w in r.get('where') or [])]
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
        u = hyp(*[sqrt(r * r / 12)[0] for r in res.values()])
        return to_unit(V(secs, 'second', u), s['unit'], f"step {s['id']}")

    def op_within(self, s):
        if 'place' in s:
            raise Refused(f"step {s['id']}: `within` a place reads a distance, and that is PLACE's bin/dmgeo.py, not here yet")
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
            if isinstance(n, dict) and n.get('scheme') and n.get('code') is not None:
                out.append((n['scheme'], str(n['code']), m))
            else:
                raise Refused(f"step {s['id']}: {m.id} is not a code of a scheme ({{scheme, code}})")
        return out

    def op_ancestor_at_level(self, s):
        out = []
        for scheme, code, m in self._code_members(s):
            rows = {str(r.get('code', r.get('unit'))): r for r in (self.reg(scheme) or []) if isinstance(r, dict)}
            c, seen = code, set()
            while c in rows and c not in seen:
                seen.add(c)
                r = rows[c]
                if s['level'] in (r.get('level'), r.get('rank')):
                    out.append(Member(f"{scheme}:{c}", {'scheme': scheme, 'code': c}, m.bean))
                    break
                c = str(r.get('parent') or '')
            else:
                raise Refused(f"step {s['id']}: {scheme}:{code} has no ancestor at the level '{s['level']}'")
        return out

    def op_neighbour_of(self, s):
        if 'distance' in s:
            raise Refused(f"step {s['id']}: `neighbour-of` by distance reads PLACE's bin/dmgeo.py, not here yet")
        rel = self.reg(s['relation']) or []
        out, ids = [], set()
        for scheme, code, m in self._code_members(s):
            for r in rel:
                if not isinstance(r, dict) or r.get('rel') != 'adjacent':
                    continue
                for a, b in ((r.get('from'), r.get('to')), (r.get('to'), r.get('from'))):
                    if str(a) == code and f"{scheme}:{b}" not in ids:
                        ids.add(f"{scheme}:{b}")
                        out.append(Member(f"{scheme}:{b}", {'scheme': scheme, 'code': b}, m.bean))
        return out

    # a series' reads (S7)
    def _series(self, s, key='series'):
        path = s[key]
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
        f = {'mean': lambda: V(sum(x for _p, x, _r in rows) / n, unit, u / sqrt(Fraction(n))[0] if u else None),
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
        d = V(v1 - v0, ser.channels[ch].get('unit'), hyp(u, u) if u else None)
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
            raise Refused(f"step {s['id']}: {name}.{ch} holds no position read as a number — a position on a map is "
                          f"measured by PLACE's bin/dmgeo.py, not here yet")
        total = sum(abs(b[1] - a[1]) for a, b in zip(rows, rows[1:]))
        return V(total, ser.channels[ch].get('unit'), None, False)

    def op_join(self, s):
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
            ud = hyp(ua, ub)
            verdict = 'agree' if d == 0 else 'compatible' if ud and d <= self.k * ud else 'differ'
            out.append(Member(f"@{dmseq.show(p)}", {'verdict': verdict, 'difference': dmseq.show(d)}, None))
        return out

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
            y, m, _d = (int(x) for x in dmcal.from_day(day_at, 'gregory').split('-'))
            n = w['count'] - 1
            if w['level'] == 'year':
                lo = dmcal.to_day(f"{y - n:04d}-01-01")
            else:
                k = y * 12 + m - 1 - n
                lo = dmcal.to_day(f"{k // 12:04d}-{k % 12 + 1:02d}-01")
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
        self.lines.append(f"  the window: {dmcal.from_day(lo, 'gregory')} to {dmcal.from_day(day_at, 'gregory')}")
        return V(used, 'day') if used else V(Fraction(counted), 'item')

    def op_weigh(self, s):
        ref = s['weighing']
        bean, key = (ref.split(':', 1) if ':' in ref else (self.bean, ref))
        entry = ((self.g.bean(bean).get('weighings') or {}).get(key))
        if not isinstance(entry, dict):
            raise Refused(f"step {s['id']}: no weighing '{ref}'")
        crit, w, lam, ci, cr = weights(entry)
        self.lines.append(f"  λmax ≈ {dmseq.rounded(lam, 4)}, CI ≈ {dmseq.rounded(ci, 4)}, CR ≈ {dmseq.rounded(cr, 3)}")
        return {a: V(w[a], 'one', None, True) for a in crit}

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
                    if not isinstance(e, dict) or e.get('scheme') != scheme:
                        continue
                    r = rows.get(str(e.get('code')))
                    f = (r or {}).get('formula')
                    if not f or f in ('-', 'none'):
                        raise Refused(f"step {s['id']}: {e.get('code')} has no formula in {scheme} (a polymer, a "
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

    def op_choose(self, s):
        mechs = [r for r in (self.reg('mechanisms') or []) if isinstance(r, dict)
                 and ((r.get('computes') or {}).get('property') or {}).get('code') == s['computes']]
        if not mechs:
            raise Refused(f"step {s['id']}: no mechanism of the law computes '{s['computes']}'")
        member = self.arg(s, 'of', 'set') if s.get('of') in self.env and isinstance(self.env[s['of']], list) else None
        if member is not None and len(member) != 1:
            raise Refused(f"step {s['id']}: `of` holds {len(member)} beings, and a mechanism reads one")
        codes = set()
        for x, _w in _flatten(walk(self.g, member[0].node, 'is', at=member[0].bean)) if member else []:
            if isinstance(x, dict):
                codes.add((x.get('scheme'), str(x.get('code'))))
        covering, why = [], []
        for r in mechs:
            v = r.get('valid') or {}
            wants = {(w.get('scheme'), str(w.get('code'))) for w in v.get('where') or [] if isinstance(w, dict)}
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
        raise Refused(f"step {s['id']}: `rotate` reads a pole's rows, which PLACE brings (part 9) — not here yet")

    def op_position_to(self, s):
        try:
            import pyproj  # noqa: F401
        except ImportError:
            raise Refused(f"step {s['id']}: `position-to` needs PROJ (pyproj), and this machine has none — no "
                          f"transformation is guessed") from None
        raise Refused(f"step {s['id']}: `position-to` through PROJ lands with PLACE (part 9)")


_FORMULA = re.compile(r'([A-Z][a-z]?)([0-9]*)|(\()|(\))([0-9]*)', re.ASCII)


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
            at = str(m.node['at'])
        out.append((m.id, at))
    return out


def used(bean, clause, attr, *, at, root=ROOT, pin=None, zone=None):
    """(V, lines) — how much of a clause's allowance the members of its `used_by` selection use inside the window of
    its `within` ending at `at`, read from each member's `attr` (N9, read for AGREE's ledger)."""
    g = Garden(root, pin)
    c = (g.bean(bean).get('clauses') or {}).get(clause) or {}
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
          + (" — above 0.10" if cr > Fraction(1, 10) else ''))
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
        if args[:1] == ['weigh'] and len(args) == 2 and ':' in args[1]:
            weigh(*args[1].split(':', 1))
            return 0
        if args[:1] == ['order'] and len(args) == 3:
            order(args[1], args[2])
            return 0
        if (at is None) != (moment is None):
            raise Refused("a pinned reading names both the commit (`--at`) and the moment it was read at (`--moment`)")
        pin = Pin(at, moment, None) if at else None
        if adhoc:
            entry = dmparse.loads(open(adhoc, encoding='utf-8').read())
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
