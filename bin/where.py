#!/usr/bin/env python3
"""dmwhere — resolve a bean's recorded LOCATIONS against the machine you are actually standing on.

WHY THIS EXISTS. Until std-vocab@5.1 a location in this ledger was a bare absolute path: 69 of them
across 14 beans, and not one named a host. That is a position in one anchor system written as though it
were the location itself, and it failed twice in one day — a commit reported to exist on NO branch and
NOT on disk (true of the machine searched, false of the estate), and one analysis reported FRESH on one laptop
and STALE on another the same minute.

WHAT IT DOES. A bean states where a thing is in a PORTABLE form (`root:src/app`). A HOST
states what that root means on itself (`roots:` on the host's own bean). This resolves the first through
the second and reports, per position, one of:

  HERE        resolved on this machine, and the thing is actually there
  MISSING     resolved on this machine, and the thing is NOT there  (the bean is wrong, or the tree moved)
  ELSEWHERE   a position on another machine — correctly not resolvable from here
  NO-ROOT     this host declares no resolution for that root — it does not hold the thing
  UNKNOWN     the bean itself says nobody has established where it is

A MOMENT THAT SAYS WHERE IT WAS (27.0) and names the zone in force there is read against that zone: the offset it was
written with must be the one the zone kept at that moment. The zone's rule is read from THIS machine's copy of the time
zone database, never from the ledger — which is why this tool reads it, and the gate does not: a gate whose verdict
depended on a machine's copy would pass on one and fail on another.

  OFFSET-OK         the offset written is the one the zone kept then
  OFFSET-DISAGREES  it is not: the moment or its zone is wrong (a clock read on a +03 host written for a +03:30 place)
  NO-ZONE-DATA      this machine holds no zone database, so it cannot say — an answer, like NO-ROOT

NO-ROOT AND UNKNOWN ARE ANSWERS, NOT FAILURES. That is the whole point: "not measured here" is a true
statement, where "stale" was a false one. A reader who is told a thing is not on this machine has learned
something; a reader shown a path that does not resolve has been misled with the same confident output.

THIS TOOL NEVER WRITES. It reports.

Usage:
  python3 bin/dmwhere.py                 # every located_at position in the garden, resolved for this host
  python3 bin/dmwhere.py <bean>          # just that bean
  python3 bin/dmwhere.py --root <name>   # what one logical root means here
  python3 bin/dmwhere.py <position> [--at <moment>]   # what a position is IN (24.0): its cells, boundaries, nearest

A POSITION, READ FOR WHAT IT IS IN (24.0, PLACE). Given a position rather than a bean:
    python3 bin/dmwhere.py bp1950:3.93ka          # an age: the cells it lies in, and the boundary that fixes the finest
    python3 bin/dmwhere.py b2k:4.25ka             # the same line from another datum (b2k = bp-1950 + 50 a, computed)
    python3 bin/dmwhere.py ics:Meghalayan         # a cell: its span, its ancestry, and where its base is marked
    python3 bin/dmwhere.py "EPSG:4326;10.1,20.2"  # a place: its grid cells and the fixed beings nearest it
    python3 bin/dmwhere.py marker-a+3.2,-1.5      # a place stated from another being, resolved first
    python3 bin/dmwhere.py "EPSG:4326;10.1,20.2" --at 2026-03-01   # the beings that were fixed there THEN

`AT` IS BEING-IN (در بودن). A position is never a point with no size: it names the cell the thing is IN, at the
level it is held to — a coordinate is in its grid cells, an age in its stage, its epoch, its era; a finer position is
only a smaller cell. So the anchors of a position are the cells it is in, coarse to fine, and where it lies within a
margin it is in both cells beside it, and this reader chooses neither.

TIME AND PLACE ARE ONE MECHANISM (24.0, ratified 2026-09-26), and this reader holds no branch for either. What it asks
of a position is asked of its SYSTEM's row in the law:
  datum          an offset from a being named in the position (`relative`), from a datum a host defines (`host`: a
                 root of its `roots`, or the host itself — a path), or from a position of another system, before or
                 after it (`bp-1950` from 1950, `b2k` from 2000). Two systems over one ground whose datums are in one
                 system are crosswalked by computing, never by a stated constant.
  cells_in       the table whose rows are its cells (ICS units, a garden's parishes), at the system's levels.
  boundaries_in  the table of what FIXES each cell's base (`fixing`): a mark in a being at a place — a golden spike,
                 a point along a rock section — or a value declared on the line itself.
  neighbours     the beings nearest a place; the boundaries nearest an age.
A margin the table states is an accuracy as its maker stated it (`uncertainty_form`, kind `unstated`): kept as said,
never read as a standard uncertainty. Where a position lies within a boundary's margin, or within the span between
two datums that the table's own zero leaves open, both cells beside it are named and neither is chosen.

A path on a host and a coordinate on a body are both answers to "where is it": the first is resolved against the machine
this runs on, the second is read for the cells it is in. The coordinate arithmetic is bin/dmgeo.py's; the tables are
read as bin/dmknowledge.py reads them.
"""
import os, re, socket, sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmgarden  # noqa: E402 — the one garden model: where its documents are
import dmknowledge
import dmcal     # noqa: E402 — a moment, and the offset a zone kept at it

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    """Every managed document — beans AND mappings; in a garden of the core, each as today's terms its `details` keeps,
    with its locations and names (bin/garden.py `terms`, the one view of them).

    Both, because both can carry `located_at` and `.gitattributes` already dispatches both to the same
    merge driver. This garden has paid for the beans-only glob once already: `dmmerge.load_garden`
    scanned `beans/*.md` alone, so the corpus merge never saw a mapping, and it was found by a check
    that asserted over the whole corpus rather than over what the tool under test happened to read.
    """
    out = {}
    if dmgarden.runs_core(ROOT):
        G = dmgarden.core_garden(ROOT)
        return {bid: dmgarden.terms(b, G.beans) for bid, b in sorted(G.beans.items()) if not b.unread}
    for space, key in (('beans', 'bean'), ('mappings', 'mapping')):
        for f in dmgarden.paths(ROOT, space):
            fm, _ = dmparse.read(f)
            try:
                d = dmparse.loads(fm) if fm else None
            except yaml.YAMLError:
                continue
            if isinstance(d, dict) and d.get(key):
                out[d[key]] = d
    return out


def this_host(beans):
    """The bean whose hostname/fqdn anchor names the machine this is running on.

    Matched against the ANCHORS rather than against a bean id, because a bean id is a garden-local label
    and the anchor is the thing that claims to identify the machine. A host with no bean resolves to
    None, and every position then reports NO-ROOT — which is correct and is why it is not an error: the
    ledger genuinely does not know what a root means on a machine it has never been told about.
    """
    me = socket.gethostname().lower()
    for bid, d in beans.items():
        for a in ((d.get('identity') or {}).get('anchors') or []):
            if a.get('key') in ('hostname', 'fqdn'):
                v = str(a.get('value', '')).lower()
                if v == me or v.split('.')[0] == me.split('.')[0]:
                    return bid, d
    return None, None


def names_of(hid, host_fm):
    """What a machine is called: its host bean's id, its hostname/fqdn anchors and their first labels, lowercased —
    and, for the machine this runs on, what it calls itself."""
    names = {str(hid).lower()} if hid else set()
    for a in ((host_fm or {}).get('identity') or {}).get('anchors') or []:
        if a.get('key') in ('hostname', 'fqdn'):
            v = str(a.get('value', '')).lower()
            names |= {v, v.split('.')[0]}
    return names


def here(beans=None):
    """(host bean id, its front matter, every name this machine goes by)."""
    hid, hfm = this_host(load() if beans is None else beans)
    me = socket.gethostname().lower()
    return hid, hfm, names_of(hid, hfm) | {me, me.split('.')[0]}


def roots_of(host_fm):
    return (host_fm or {}).get('roots') or {}


# ---- a position on a host: an offset from a datum the host defines (`datum: host`; 24.0) ----------------------------
def host_bound(root=ROOT):
    """The systems whose positions are offsets from a datum a host defines — every row that says `datum: host`.
    Read from the law: the list this replaced named three systems by heart, and a garden's own filesystem system
    would have been read as a coordinate."""
    return {n for n, r in Law(root).systems.items() if r.get('datum') == 'host'}


ROOT_FORM = re.compile(r'^root:([a-z0-9][a-z0-9-]*)(?:/(.*))?$')
OBJECT_FORM = re.compile(r'^([a-z0-9][a-z0-9._-]*)@([0-9a-f]{7,40})$')
HOST_FORM = re.compile(r'^([a-z0-9][a-z0-9.-]*):(/.*|[A-Za-z]:\\.*)$')


def on_host(position, roots, names=()):
    """ONE RESOLVER FOR EVERY DATUM A HOST DEFINES: a position -> (literal path here, object, why not).

      root:<name>[/<rel>]   an offset from the root <name>, which this host defines in its own `roots`
      <root>@<object>       an object reachable from that root (the path is the root's; the object is returned)
      <host>:<path>         an offset from the host itself, named in the position: here only when it is this one

    A position the host does not hold gives (None, None, why): an answer, not a failure. A position in none of
    these forms raises ValueError — it is no offset from a host, and the caller reads it as what it is."""
    if not isinstance(position, str):
        raise ValueError(f"{position!r} is not a position")
    m = ROOT_FORM.match(position) or OBJECT_FORM.match(position)
    if m:
        name, rest = m.group(1), m.group(2)
        oid = rest if m.re is OBJECT_FORM else None
        row = roots.get(name)
        if not isinstance(row, dict):
            return None, oid, f"this host declares no root '{name}'"
        # The root's own `at` is `<host>:<path>` on the host that declares it: that host IS the datum, so its
        # name is not asked again here.
        base = str(row.get('at', ''))
        _host, _, path = base.partition(':')
        if not path:
            return None, oid, f"root '{name}' resolves to {base!r}, which names no path"
        return (os.path.join(path, rest) if rest and not oid else path), oid, None
    m = HOST_FORM.match(position)
    if m:
        host = m.group(1).lower()
        if host in names or host.split('.')[0] in names:
            return m.group(2), None, None
        return None, None, f"a position on {m.group(1)}"
    raise ValueError(f"'{position}' is no offset from a host: not `root:<name>/…`, `<root>@<object>` or `<host>:<path>`")


def resolve(at, roots):
    """A `root:<name>[/<rel>]` position -> (literal path on this host, None) or (None, why not)."""
    try:
        path, _o, why = on_host(at, roots)
    except ValueError:
        return None, 'not a root: position'
    return path, why


def reachable_in_git(repo_path, oid):
    """Is this object REACHABLE here — not, is it checked out.

    The distinction is the entire staleness defect: `git-head:<sha>` compared a recorded key against
    whatever tree the reader happened to have checked out, so one analysis had as many verdicts as there
    were hosts. An object's presence is a fact about the repository and every clone that has it agrees.
    """
    import subprocess
    try:
        return subprocess.run(['git', '-C', repo_path, 'cat-file', '-e', oid + '^{object}'],
                              capture_output=True, timeout=15).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def classify(entry, roots, names=None, bound=None):
    """One position -> a verdict about THIS machine.

    MISSING is reserved for the one case that means the LEDGER IS WRONG: the bean claims the thing is
    here and it is not. A position the bean already declares `elsewhere` and which is indeed not here is
    AGREEMENT, and reporting it as a defect would bury the real ones under every host's normal state.
    """
    openness, at = entry.get('openness'), entry.get('at')
    system = entry.get('system')
    if openness == 'unknown':
        return 'UNKNOWN', 'the bean states that nobody has established where this is'
    if openness == 'unreachable':
        return 'ELSEWHERE', f"{at} — declared unreachable; not checked from here"

    if system not in (host_bound() if bound is None else bound):
        # A COORDINATE, AN AGE, A PARISH NAMES NO MACHINE: `EPSG:4326;…` was once read here as a path on a host
        # called EPSG. Such a position is in a cell of its own system, and `dmwhere <position>` reads which.
        return 'PLACED', f"{at} — in {system}; `dmwhere.py {at}` reads what it is in"

    if not (str(at).startswith('root:') or HOST_FORM.match(str(at)) or re.match(r'^[a-z0-9][a-z0-9._-]*@[0-9a-f]{7,40}$', str(at))):
        # A POSITION ON A HOST THAT IS NO PATH (29.0): a slot in a rack, a repository as a client fetches it. Its datum is
        # the host, and it is not a file this machine resolves — placed, as a coordinate is, never reported missing
        return 'PLACED', f"{at} — on a host, in {system}; not a path this machine resolves"
    try:
        path, oid, why = on_host(at, roots, here()[2] if names is None else names)
    except ValueError as e:
        return 'NO-ROOT', str(e)
    if path is None:
        return ('ELSEWHERE' if HOST_FORM.match(at) else 'NO-ROOT'), f"{at} — {why}"
    if oid:
        if reachable_in_git(path, oid):
            return 'HERE', f"{oid} reachable in {path}"
        return ('MISSING' if openness == 'here' else 'ELSEWHERE', f"{oid} NOT reachable in {path}")
    if os.path.exists(path):
        return 'HERE', path
    return ('MISSING' if openness == 'here' else 'ELSEWHERE',
            path if HOST_FORM.match(at) else f"{path} — not on this host, which is what the bean says")


# ============================================================== what a position is IN (24.0, PLACE; `at` is being-in)
class Law:
    """The systems, units and tables of one garden (or of the standard), as the law and the garden declare them."""

    def __init__(self, root=ROOT):
        self.root = root
        law = dmknowledge._fm(os.path.join(root, 'seed', 'std-vocab.md'))
        garden = dmknowledge._fm(os.path.join(root, 'VOCAB.md'))
        adds = garden.get('registry_additions') or {}
        # a garden's own systems: today's `registry_additions.anchor_systems`, or the core's rows `systems` (v1 part 7)
        self.systems = {r['system']: r for r in list(law.get('anchor_systems') or []) + list(adds.get('anchor_systems') or [])
                        + list(garden.get('systems') or []) if isinstance(r, dict) and r.get('system')}
        self.units = {u['unit']: u for u in list(law.get('units') or []) + list(adds.get('units') or [])
                      if isinstance(u, dict) and u.get('unit')}
        self._k = None

    @property
    def k(self):
        if self._k is None:
            self._k = dmknowledge.Knowledge(self.root)
        return self._k

    def rows(self, registry):
        try:
            return self.k.rows(registry)
        except (KeyError, OSError):
            return []

    def system_of(self, position):
        """The one system whose form the position is in — no two systems' forms take one spelling (test/place.py)."""
        hits = [n for n, r in self.systems.items() if r.get('pattern') not in (None, 'none')
                and r.get('dimension') in ('place', 'time') and dmparse.law_match(r['pattern'], position)]
        if len(hits) != 1:
            raise ValueError(f"'{position}' is in the form of {', '.join(sorted(hits)) or 'no place or time system'}"
                             + (" — one position is in one system" if hits else ""))
        return hits[0]

    def factor(self, unit):
        f = (self.units.get(unit) or {}).get('factor')
        return Fraction(int(f[0]), int(f[1])) if isinstance(f, list) and len(f) == 2 else None

    def cells(self, row):
        """{cell: its row}, the overlay's rows winning over the base's (N24)."""
        take = (row.get('cells_in') or {}).get('take')
        out = {str(r.get(take)): r for r in self.rows((row.get('cells_in') or {}).get('registry'))}
        if (row.get('overlay') or {}).get('registry'):
            out.update({str(r.get(take)): dict(r, _overlay=True) for r in self.rows(row['overlay']['registry'])})
        return out

    def boundaries(self, row):
        bi = row.get('boundaries_in') or {}
        return {str(r.get(bi.get('take'))): r for r in self.rows(bi.get('registry'))} if bi else {}


# ---- the time line: an offset from a datum, carried  to the ground every table on that line is read in ----------
def offset(law, name, position):
    """(years, datum row) — how far from the system's datum a position is, in anni, signed so that `before` is
    positive. The unit is the symbol's, read from `unit_symbols` and turned into anni by the units' own factors."""
    row = law.systems[name]
    m = re.match(r'^[^:]+:(\d+(?:\.\d+)?)([A-Za-z]+)$', position)
    sym = (row.get('unit_symbols') or {})
    if not m or m.group(2) not in sym:
        raise ValueError(f"'{position}' names no unit symbol of {name} {sorted(sym)}")
    f, a = law.factor(sym[m.group(2)]), law.factor('annus')
    return Fraction(m.group(1)) * f / a, row.get('datum')


def year_of_datum(datum):
    return int(str(datum['at'])[:4])


def before_ground(law, name, position, ground):
    """The position as anni before the datum of `ground` (bp-1950 for the ICS chart): computed from the two
    datums, which is what `crosswalk: computed` means — never a constant written beside them."""
    years, o = offset(law, name, position)
    go = law.systems[ground].get('datum')
    if not isinstance(o, dict) or not isinstance(go, dict) or o.get('system') != go.get('system'):
        raise ValueError(f"{name} and {ground} state no datums in one system: no crosswalk is computed")
    sign = 1 if o.get('direction') == 'before' else -1
    ce = year_of_datum(o) - sign * years                      # a year of the common era, as a number
    return (year_of_datum(go) - ce) if go.get('direction') == 'before' else (ce - year_of_datum(go))


def _ma(r, k):
    return Fraction(str(r.get(k + '_ma'))) if r.get(k + '_ma') not in (None, '') else Fraction(0)


def time_anchors(law, name, position):
    out = {'system': name, 'position': position, 'cells': [], 'boundaries': []}
    for cname, crow in sorted(law.systems.items()):
        if not crow.get('cells_in') or crow.get('dimension') != 'time':
            continue
        ground = next((g for g in crow.get('same_ground_as') or [] if isinstance(law.systems.get(g, {}).get('datum'), dict)), None)
        if ground is None:
            continue
        bp = before_ground(law, name, position, ground)
        ma = bp / 10 ** 6
        out.setdefault('before', []).append((ground, bp))
        slack = lambda r, e: max(Fraction(str(r.get(e + '_margin_ma') or 0)), Fraction(50, 10 ** 6))
        cells = law.cells(crow)
        inside = [r for r in cells.values() if r.get('begins_ma')
                  and _ma(r, 'ends') - slack(r, 'ends') <= ma <= _ma(r, 'begins') + slack(r, 'begins')]
        inside.sort(key=lambda r: (_ma(r, 'begins') - _ma(r, 'ends'), str(r.get('unit'))))
        take = crow['cells_in']['take']
        for r in inside:
            edge = [e for e in ('begins', 'ends') if abs(ma - _ma(r, e)) <= slack(r, e)]
            out['cells'].append({'system': cname, 'cell': r.get(take), 'level': r.get('rank') or r.get('level'),
                                 'begins_ma': r.get('begins_ma'), 'ends_ma': r.get('ends_ma') or '0',
                                 'margins': (r.get('begins_margin_ma') or None, r.get('ends_margin_ma') or None),
                                 'on_edge': edge[0] if edge else None})
        # the boundaries nearest the age: the base of the finest cell holding it, and the base of the next younger
        bounds = law.boundaries(crow)
        near = sorted(((abs(ma - _ma(r, 'begins')), r) for r in cells.values() if r.get('begins_ma')),
                      key=lambda x: (x[0], str(x[1].get(take))))
        seen = set()
        for _d, r in near:
            b = bounds.get(str(r.get(take)))
            if b and r.get('begins_ma') not in seen:
                seen.add(r.get('begins_ma'))
                out['boundaries'].append(dict(b, base_of=r.get(take), begins_ma=r.get('begins_ma'),
                                              margin=r.get('begins_margin_ma') or None))
            if len(seen) == 2:
                break
    return out


def cell_anchors(law, name, position):
    row = law.systems[name]
    cell = position.split(':', 1)[-1]
    cells = law.cells(row)
    if cell not in cells:
        raise ValueError(f"{cell} is no cell of {name}")
    chain, c, seen = [], cell, set()
    while c in cells and c not in seen:
        seen.add(c)
        chain.append(cells[c])
        c = str(cells[c].get('parent') or '')
    b = law.boundaries(row).get(cell)
    return {'system': name, 'position': position, 'chain': chain, 'base': b}


# ---- the place line --------------------------------------------------------------------------------------------------
def place_anchors(law, name, position, moment=None):
    import dmgeo
    at = dmgeo.resolve_relative(position, root=law.root) if name == 'relative' else position
    p = dmgeo.parse(at, law.root)
    out = {'system': name, 'position': position, 'resolved': at if at != position else None, 'cells': [], 'nearest': []}
    if p['known'] and p['kind'].startswith('geographic') and p['body'] == 'earth':
        g = dmgeo.geohash(p['coordinates'][0], p['coordinates'][1])
        out['cells'] = [('geohash', g[:n]) for n in (2, 4, 6, 9)]
    out['nearest'] = dmgeo.nearest(at, root=law.root, moment=moment)
    return out


def anchors(position, *, root=ROOT, moment=None):
    law = Law(root)
    try:
        name = law.system_of(position)
    except ValueError:
        # A LOGICAL ROOT CROSSES SYSTEMS ON PURPOSE: `root:<name>/…` is one spelling in every filesystem a host defines
        # (windows-filesystem's form_note), so it is in all of them, and the host's own `roots` entry says which.
        hits = [n for n, r in law.systems.items() if r.get('pattern') not in (None, 'none')
                and dmparse.law_match(r['pattern'], position)]
        if not hits or any(law.systems[n].get('datum') != 'host' for n in hits):
            raise
        name = '/'.join(sorted(hits))
        hid, hfm, names = here()
        row = roots_of(hfm).get(ROOT_FORM.match(position).group(1)) if ROOT_FORM.match(position) else None
        name = row.get('system', name) if isinstance(row, dict) else name
        path, oid, why = on_host(position, roots_of(hfm), names)
        return {'position': position, 'system': name, 'host': hid, 'path': path, 'object': oid, 'why': why}
    row = law.systems[name]
    if row.get('cells_in'):
        return cell_anchors(law, name, position)
    # ONE RESOLVER PER DATUM, read from the system's row: an offset before or after another system's position, one
    # from a being (and the ground such offsets resolve through), one from a datum a host defines.
    datum = row.get('datum')
    if row.get('dimension') == 'time' and isinstance(datum, dict):
        return time_anchors(law, name, position)
    if row.get('dimension') == 'place' and (datum == 'being' or any(
            r.get('datum') == 'being' and r.get('resolves_through') == name for r in law.systems.values())):
        return place_anchors(law, name, position, moment)
    if datum == 'host':
        hid, hfm, names = here()
        path, oid, why = on_host(position, roots_of(hfm), names)
        return {'position': position, 'system': name, 'host': hid, 'path': path, 'object': oid, 'why': why}
    raise ValueError(f"{name}: this reader computes no anchors for it yet — a system with `cells_in`, a `datum`, or a "
                     f"coordinate is what it reads")


def _num(x):
    return format(float(x), '.10g')


def show(a):
    lines = []
    if 'path' in a:
        on = f"on {a['host'] or socket.gethostname() + ' (no host bean)'}"
        if a['path'] is None:
            lines.append(f"{a['position']} ({a['system']}): not resolvable {on} — {a['why']}")
        else:
            lines.append(f"{a['position']} ({a['system']}) {on}: {a['path']}" + (f", object {a['object']}" if a['object'] else "")
                         + ("" if os.path.exists(a['path']) else "  — NOT THERE"))
    elif 'before' in a:
        for g, bp in a['before']:
            lines.append(f"{a['position']} is {_num(bp)} a before the datum of {g}")
        for c in a['cells']:
            m = [x for x in c['margins'] if x]
            lines.append(f"  {c['system']} {c['cell']:<22} {str(c['level']):<10} {c['begins_ma']}–{c['ends_ma']} Ma"
                         + (f"   ± {'/'.join(m)} Ma as the chart states (kind unstated)" if m else "")
                         + (f"   ON ITS {c['on_edge'].upper()}: the cell beside it may hold the age" if c['on_edge'] else ""))
        for b in a['boundaries']:
            lines.append(f"  base of {b['base_of']} at {b['begins_ma']} Ma" + (f" ± {b['margin']}" if b.get('margin') else "")
                         + f": {b.get('fixing')}, {b.get('status')}"
                         + (f" — at {b['at']}" if b.get('at') else "") + (f", {b['level']}" if b.get('level') else "")
                         + (f", {b['location']}" if b.get('location') else ""))
    elif 'chain' in a:
        c = a['chain'][0]
        span = f" {c['begins_ma']}–{c.get('ends_ma') or '0'} Ma" if c.get('begins_ma') not in (None, '') else ""   # a place cell has none
        lines.append(f"{a['position']}: {c.get('rank') or c.get('level') or ''}{span}".rstrip()
                     + (f" — {c['name']}" if c.get('name') else "")
                     + (f"   (an overlay row: {c.get('source')})" if c.get('_overlay') else ""))
        lines.append("  within: " + " ⊂ ".join(str(r.get('unit') or r.get('code')) for r in a['chain'][1:]) if a['chain'][1:] else "  a top cell")
        b = a['base']
        if b:
            lines.append(f"  its base is {b.get('fixing')} ({b.get('status')})" + (f" at {b['at']}" if b.get('at') else "")
                         + (f", {b['level']}" if b.get('level') else "") + (f", {b['location']}" if b.get('location') else "")
                         + (f" — {b['cite']}" if b.get('cite') else ""))
    else:
        if a.get('resolved'):
            lines.append(f"{a['position']} resolves to {a['resolved']} (≈: laid on the body's mean sphere)")
        if a['cells']:
            lines.append("  cells, coarse to fine: " + ", ".join(f"{s}:{c}" for s, c in a['cells']))
        lines.append("  nearest fixed beings: " + (", ".join(f"{b} ≈ {m:.1f} m" for b, m in a['nearest']) or "none"))
    return "\n".join(lines)



def placed_moments(node, path=''):
    """[(path, position)] of every position a front matter holds that says where it was: a `timing` entry, or a day
    written long, with a `where` (27.0)."""
    out = []
    if isinstance(node, dict):
        if {'system', 'at', 'unit'} <= set(node) and isinstance(node.get('where'), dict):
            out.append((path, node))
        for k, v in node.items():
            out += placed_moments(v, f"{path}.{k}" if path else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out += placed_moments(v, f"{path}[{i}]")
    return out


def zone_verdict(position):
    """(verdict, detail) for a moment whose place names its zone — or None where there is nothing to compare: no zone, or
    a position that is no moment (a day, or one placed by its neighbours, which carries no offset)."""
    zone = position['where'].get('zone')
    if not zone:
        return None
    try:
        m = dmcal.moment(position)
    except (ValueError, dmcal.NotByRule):
        return None
    if m.offset is None:
        return None
    try:
        kept = dmcal.offset(zone, position)
    except dmcal.NoZoneData as e:
        return 'NO-ZONE-DATA', str(e)
    except ValueError as e:
        return 'OFFSET-DISAGREES', str(e)
    said = 0 if m.offset == 'Z' else (1 if m.offset[0] == '+' else -1) * (int(m.offset[1:3]) * 60 + int(m.offset[4:6]))
    shown = f"{'+' if kept >= 0 else '-'}{abs(kept) // 60:02d}:{abs(kept) % 60:02d}"
    if said == kept:
        return 'OFFSET-OK', f"{dmcal.shown(position)} — {zone} kept {shown} then"
    return 'OFFSET-DISAGREES', (f"{dmcal.shown(position)} is written at {m.offset}, and {zone} kept {shown} at that moment — "
                                f"the moment or its zone is wrong")


def main():
    beans = load()
    hid, hfm, names = here(beans)
    roots, bound = roots_of(hfm), host_bound()
    me = socket.gethostname()

    if '--root' in sys.argv:
        name = sys.argv[sys.argv.index('--root') + 1]
        row = roots.get(name)
        print(f"{name} on {me}: {row.get('at') if row else 'NOT DECLARED — this host does not hold it'}")
        return 0

    only = next((a for a in sys.argv[1:] if not a.startswith('-')), None)
    if only and only not in beans and '--at' not in (only,):
        moment = sys.argv[sys.argv.index('--at') + 1] if '--at' in sys.argv[:-1] else None
        try:
            a = anchors(only, moment=moment)
        except ValueError as e:
            print(f"dmwhere: {e}"); return 1
        print(show(a))
        return 0
    print(f"host {me} -> bean {hid or 'NONE (this machine has no bean; every root is unresolvable)'}"
          f"  |  {len(roots)} root(s) declared here\n")

    counts, rows = {}, []
    for bid, d in sorted(beans.items()):
        if only and bid != only:
            continue
        for e in (d.get('located_at') or []):
            if not isinstance(e, dict):
                continue
            verdict, detail = classify(e, roots, names, bound)
            counts[verdict] = counts.get(verdict, 0) + 1
            rows.append((verdict, bid, e.get('system'), detail))

    for bid, d in sorted(beans.items()):
        if only and bid != only:
            continue
        for path, pos in placed_moments(d):
            zv = zone_verdict(pos)
            if zv:
                counts[zv[0]] = counts.get(zv[0], 0) + 1
                rows.append((zv[0], bid, path, zv[1]))

    for v, bid, sysname, detail in rows:
        print(f"  {v:10s} {bid:14s} {str(sysname):19s} {detail}")

    if not rows:
        print("  (no bean carries located_at yet)")
    print("\n" + ", ".join(f"{n} {k.lower()}" for k, n in sorted(counts.items())))
    # MISSING is the only verdict that means the LEDGER is wrong. NO-ROOT and ELSEWHERE are facts about
    # this machine, and exiting non-zero on them would train a reader to ignore the tool on every host
    # that does not happen to hold everything.
    return 1 if counts.get('MISSING') or counts.get('OFFSET-DISAGREES') else 0


if __name__ == '__main__':
    sys.exit(main())
