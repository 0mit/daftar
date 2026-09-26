#!/usr/bin/env python3
"""dmwhere — resolve a bean's recorded LOCATIONS against the machine you are actually standing on.

WHY THIS EXISTS. Until std-vocab@5.1 a location in this ledger was a bare absolute path: 69 of them
across 14 beans, and not one named a host. That is a position in one anchor system written as though it
were the location itself, and it failed twice in one day — a commit reported to exist on NO branch and
NOT on disk (true of the machine searched, false of the estate), and one analysis reported FRESH on one laptop
and STALE on another the same minute.

WHAT IT DOES. A bean states where a thing is in a PORTABLE form (`root:addin/CloudApi`). A HOST
states what that root means on itself (`roots:` on the host's own bean). This resolves the first through
the second and reports, per position, one of:

  HERE        resolved on this machine, and the thing is actually there
  MISSING     resolved on this machine, and the thing is NOT there  (the bean is wrong, or the tree moved)
  ELSEWHERE   a position on another machine — correctly not resolvable from here
  NO-ROOT     this host declares no resolution for that root — it does not hold the thing
  UNKNOWN     the bean itself says nobody has established where it is

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
  datum          an offset from a being named in the position (`relative`), or from a position of another system,
                 before or after it (`bp-1950` from 1950, `b2k` from 2000). Two systems over one ground whose
                 datums are in one system are crosswalked by computing, never by a stated constant.
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
import glob, os, re, socket, sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmknowledge

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOST_BOUND = ('unix-filesystem', 'windows-filesystem', 'git-object-graph')   # positions that name a machine


def load():
    """Every managed document — beans AND mappings.

    Both, because both can carry `located_at` and `.gitattributes` already dispatches both to the same
    merge driver. This garden has paid for the beans-only glob once already: `dmmerge.load_garden`
    scanned `beans/*.md` alone, so the corpus merge never saw a mapping, and it was found by a check
    that asserted over the whole corpus rather than over what the tool under test happened to read.
    """
    out = {}
    for space, key in (('beans', 'bean'), ('mappings', 'mapping')):
        for f in sorted(glob.glob(os.path.join(ROOT, space, '*.md'))):
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


def roots_of(host_fm):
    return (host_fm or {}).get('roots') or {}


def resolve(at, roots):
    """A `root:<name>[/<rel>]` position -> (literal path on this host, note) or (None, why not)."""
    if not isinstance(at, str) or not at.startswith('root:'):
        return None, 'not a root: position'
    rest = at[len('root:'):]
    name, _, rel = rest.partition('/')
    row = roots.get(name)
    if not row:
        return None, f"this host declares no root '{name}'"
    base = str(row.get('at', ''))
    _host, _, path = base.partition(':')
    if not path:
        return None, f"root '{name}' resolves to {base!r}, which names no path"
    return os.path.join(path, rel) if rel else path, None


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


def classify(entry, roots):
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

    if system == 'git-object-graph' and isinstance(at, str) and '@' in at:
        repo, _, oid = at.partition('@')
        path, why = resolve('root:' + repo, roots)
        if path is None:
            return 'NO-ROOT', f"{at} — {why}"
        if reachable_in_git(path, oid):
            return 'HERE', f"{oid} reachable in {path}"
        return ('MISSING' if openness == 'here' else 'ELSEWHERE',
                f"{oid} NOT reachable in {path}")

    if system not in HOST_BOUND:
        # A COORDINATE, AN AGE, A PARISH NAMES NO MACHINE: `EPSG:4326;…` was once read here as a path on a host
        # called EPSG. Such a position is in a cell of its own system, and `dmwhere <position>` reads which.
        return 'PLACED', f"{at} — in {system}; `dmwhere.py {at}` reads what it is in"

    if isinstance(at, str) and not at.startswith('root:'):
        host, _, literal = at.partition(':')
        if host.lower().split('.')[0] != socket.gethostname().lower().split('.')[0]:
            return 'ELSEWHERE', f"{at} — a position on {host}"
        return ('HERE', literal) if os.path.exists(literal) else (
            'MISSING' if openness == 'here' else 'ELSEWHERE', literal)

    path, why = resolve(at, roots)
    if path is None:
        return 'NO-ROOT', f"{at} — {why}"
    if os.path.exists(path):
        return 'HERE', path
    return ('MISSING' if openness == 'here' else 'ELSEWHERE',
            f"{path} — not on this host, which is what the bean says")


# ============================================================== what a position is IN (24.0, PLACE; `at` is being-in)
class Law:
    """The systems, units and tables of one garden (or of the standard), as the law and the garden declare them."""

    def __init__(self, root=ROOT):
        self.root = root
        law = dmknowledge._fm(os.path.join(root, 'seed', 'std-vocab.md'))
        garden = dmknowledge._fm(os.path.join(root, 'VOCAB.md'))
        adds = garden.get('registry_additions') or {}
        self.systems = {r['system']: r for r in list(law.get('anchor_systems') or []) + list(adds.get('anchor_systems') or [])
                        if isinstance(r, dict) and r.get('system')}
        self.units = {u['unit']: u for u in list(law.get('units') or []) + list(adds.get('units') or [])
                      if isinstance(u, dict) and u.get('unit')}
        self.k = dmknowledge.Knowledge(root)

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
    sign = 1 if o.get('sense') == 'before' else -1
    ce = year_of_datum(o) - sign * years                      # a year of the common era, as a number
    return (year_of_datum(go) - ce) if go.get('sense') == 'before' else (ce - year_of_datum(go))


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
    name = law.system_of(position)
    row = law.systems[name]
    if row.get('cells_in'):
        return cell_anchors(law, name, position)
    if row.get('dimension') == 'time' and isinstance(row.get('datum'), dict):
        return time_anchors(law, name, position)
    if row.get('dimension') == 'place' and name in ('geographic', 'relative'):
        return place_anchors(law, name, position, moment)
    raise ValueError(f"{name}: this reader computes no anchors for it yet — a system with `cells_in`, a `datum`, or a "
                     f"coordinate is what it reads")


def _num(x):
    return format(float(x), '.10g')


def show(a):
    lines = []
    if 'before' in a:
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
        lines.append(f"{a['position']}: {c.get('rank') or c.get('level') or ''} {c.get('begins_ma', '')}–{c.get('ends_ma') or '0'} Ma".rstrip()
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



def main():
    beans = load()
    hid, hfm = this_host(beans)
    roots = roots_of(hfm)
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
            verdict, detail = classify(e, roots)
            counts[verdict] = counts.get(verdict, 0) + 1
            rows.append((verdict, bid, e.get('system'), detail))

    for v, bid, sysname, detail in rows:
        print(f"  {v:10s} {bid:14s} {str(sysname):19s} {detail}")

    if not rows:
        print("  (no bean carries located_at yet)")
    print("\n" + ", ".join(f"{n} {k.lower()}" for k, n in sorted(counts.items())))
    # MISSING is the only verdict that means the LEDGER is wrong. NO-ROOT and ELSEWHERE are facts about
    # this machine, and exiting non-zero on them would train a reader to ignore the tool on every host
    # that does not happen to hold everything.
    return 1 if counts.get('MISSING') else 0


if __name__ == '__main__':
    sys.exit(main())
