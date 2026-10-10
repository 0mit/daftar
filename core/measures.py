"""measures — the forms of a measure, judged by rule `measured` (v1 part 7).

What is measured is held in the core in four places, each in its form (core/law/measures.yaml):

  a quantity    `{ count, unit }`, and how well it is known INSIDE it: `u`, its standard uncertainty, a positive count in
                a unit of its own quantity (or of ratio, for a relative one), or `accuracy`, as its maker stated it, with
                its kind (`accuracy_kinds`) — at most one (`uncertainty_form`). The shape `quantity`, rule valency.
  an extent     one region of a line (`extent_form`): `of` the line, `in` a system, bounded `from` / `to`, or by its
                length — a `measure` in the unit the line meters, or `level` and `count`, cells of a level — never both.
  a recurrence  a repetition along a line (`recurrence_form`): `every` N neighbours or units, or `each` cell of a level
                of the system named; where it starts and ends, its closures, its places in the cell, its occurrences.
  a clause      `can: { by, of: <its words>, to?, clause: <form clause> }`, or a position on the permission square of the
                statement it asks (`obligatory: { of: <a pay>, through: <the agreement>, clause }`) — the day it falls
                due (`due`), how it repeats (`every`, a recurrence), when it falls due relative to a position
                (`falls_due`), how long before a reader is told (`notice`), its window (`during`), an allowance (`amount`
                `within` an extent, `used_by` a reading), what it occurs for (`each`, a reading), what brings it into
                force (`when`), its state.
  a placement   `be: { by, at: [<host>, <position>], as, placed: <form placement> }` — how far it is known to reach
                (`openness`), how well its position is known (`u`, `u_vertical`, `accuracy`), its zone, its window
                (`during`), and what it takes of its host (`takes`).

Rule `measured` judges each of them by the tables the release carries — the lines a region lies on (`lines`), the
systems (the standards' and the garden's own), the units in UCUM with their factors, the quantities and their
dimensions, the kinds of accuracy — and sums what is placed in a host against what it holds (`hold`): room past it is
refused, as two beings taking the same room at once are; shares past it are a host's to promise (a hypervisor
overcommits its memory), and pass. Nothing here names a system, a unit or a line."""
import os
import re
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import frame  # noqa: E402
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bin'))
import units as dmunits  # noqa: E402 — a count, read exactly: the one reader

WHOLE = re.compile(r'^[0-9]+$')


def listed(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


# ------------------------------------------------------------------------------------------------ units, exactly
def unit_row(L, unit):
    """The row of `unit` — a UCUM code of the law or the garden — or of a currency (quantity money, factor one)."""
    u = str(unit)
    if u in L.units:
        return L.units[u]
    if u in L.std.currencies:
        q = next((n for n, r in L.std.quantities.items() if isinstance(r.get('units_from'), dict)), 'money')
        return {'unit': u, 'quantity': q, 'factor': ['1', '1']}
    return None


def factor(L, unit):
    """The size of `unit` in its quantity's coherent unit, exactly; None where the law gives none."""
    f = (unit_row(L, unit) or {}).get('factor')
    if isinstance(f, list) and len(f) == 2 and all(WHOLE.match(str(x)) for x in f) and str(f[1]) != '0':
        return Fraction(int(f[0]), int(f[1]))
    return None


def exact(text):
    """A count as an exact Fraction, or None: plain decimal digits as the one reader of a count reads them
    (bin/units.py `exact`) — no leading zero, which YAML 1.1's readers take for octal, and at most 40 digits a side."""
    if not isinstance(text, str):
        return None
    try:
        return dmunits.exact(text)
    except ValueError:
        return None


def count_why(text):
    """Why `text` is not a count in its form, said to the writer."""
    if isinstance(text, str) and re.fullmatch(r'-?0[0-9]+(\.[0-9]+)?', text):
        return f"its count {text!r} begins with a zero, which a YAML 1.1 reader takes for octal: write it without"
    try:
        dmunits.exact(text if isinstance(text, str) else '')
    except ValueError as e:
        return f"its count: {e}"
    return f"its count {text!r} is not plain decimal digits, read exactly"


def power(L, unit, dimension):
    """How many times `unit` meters `dimension` — 1 for a length, 2 for an area — or None where its quantity is of
    another dimension too, or of none."""
    qname = str((unit_row(L, unit) or {}).get('quantity'))
    if dimension in L.std.quantities and dimension not in {str(d.get('dimension')) for d in
                                                           L.std.tables.get('dimensions') or [] if isinstance(d, dict)}:
        return 1 if qname == dimension else None        # a line metered by a kind (`potential`: a voltage), once
    q = L.std.quantities.get(qname)
    of = (q or {}).get('of') if isinstance((q or {}).get('of'), dict) else {}
    if set(of) != {dimension}:
        return None
    try:
        return int(of[dimension])
    except (TypeError, ValueError):
        return None


def quantity_why(L, x, want=None):
    """'' when `x` is a quantity in its form, else why not: `{ count, unit }` with at most one of `u` and `accuracy`, or a
    bare number (a count of the unit one). `want` is the quantity it must measure, where its place says."""
    if isinstance(x, str):
        return '' if exact(x) is not None else f"{x!r}: a bare number is a count of the unit one, in plain decimal digits"
    if not isinstance(x, dict) or not {'count', 'unit'} <= set(x) or set(x) - {'count', 'unit', 'u', 'accuracy'}:
        return "a quantity is `{ count, unit }`, with how well it is known inside it — one of `u` and `accuracy` — or a " \
               "bare number (a count of the unit one)"
    if exact(x['count']) is None:
        return count_why(x['count'])
    why = L.has('units', x['unit'])
    if why:
        return why
    places = (getattr(L.std, 'currency_digits', None) or {}).get(x['unit'])
    if places is not None and len((x['count'].split('.') + [''])[1]) > places:
        return f"{x['count']} {x['unit']} is written with more decimal places than {x['unit']} has ({places}, ISO 4217's " \
               f"minor unit): an amount is a count of what can be paid"
    q = (unit_row(L, x['unit']) or {}).get('quantity')
    if want not in (None, 'any') and q != want:
        return f"its unit {x['unit']} measures {q}, and a {want} is asked here"
    if 'u' in x and 'accuracy' in x:
        return "it states both `u` and `accuracy`: at most one (`uncertainty_form`) — a reader turns an accuracy into u, " \
               "and a writer never does"
    for k in ('u', 'accuracy'):
        if k in x:
            why = uncertainty_why(L, k, x[k], q)
            if why:
                return why
    return ''


def uncertainty_why(L, k, v, quantity):
    keys = {'count', 'unit'} | ({'kind'} if k == 'accuracy' else set())
    if not isinstance(v, dict) or set(v) != keys:
        return f"its `{k}` is `{{ {', '.join(sorted(keys))} }}` (`uncertainty_form.{k}`)"
    c = exact(v['count'])
    if c is None or c <= 0:
        return f"its `{k}` count {v['count']!r} is a positive count: a value known exactly states none"
    why = L.has('units', v['unit'])
    if why:
        return f"its `{k}`: {why}"
    q = (unit_row(L, v['unit']) or {}).get('quantity')
    if quantity not in (None, 'any') and q not in (quantity, 'ratio'):
        return f"its `{k}` is in {v['unit']}, which measures {q}: an uncertainty is in a unit of the value's own " \
               f"quantity, {quantity}, or of ratio for a relative one"
    if k == 'accuracy':
        kinds = [r.get('kind') for r in L.std.tables.get('accuracy_kinds') or [] if isinstance(r, dict)]
        if v['kind'] not in kinds:
            return f"its accuracy's kind {v['kind']!r} is not one of {', '.join(kinds)} (`accuracy_kinds`)"
    return ''


# ------------------------------------------------------------------------------------------------ a region, a repetition
class Measures:
    """The tables a measure is read by: the lines (`lines`), what each placement takes (`takes`), the systems."""

    def __init__(self, L, zone=None):
        ml = getattr(L, 'measure_law', None) or {}
        self.L, self.zone = L, zone
        self.lines = {str(r['line']): r for r in ml.get('lines') or [] if isinstance(r, dict) and r.get('line')}
        self.takes = {str(r['placement']): str(r.get('takes')) for r in ml.get('takes') or [] if isinstance(r, dict)}
        self.systems = L.systems

    def line(self, where, x):
        """(the line `of` names, [problem]) — None where it names none, or one with no regions."""
        ln = x.get('of')
        row = self.lines.get(ln) if isinstance(ln, str) else None
        if row is None:
            return None, [(where, f"`of: {ln!r}` names no line: one of {', '.join(sorted(self.lines))}")]
        if row.get('region') != 'true':
            return None, [(where, f"`{ln}` holds no region and nothing on it repeats — {row.get('why')}")]
        return row, []

    def system(self, where, x, row):
        """(the system `in` names, [problem]); (None, []) where it names none."""
        sn = x.get('in')
        if sn is None:
            return None, []
        srow = self.systems.get(sn) if isinstance(sn, str) else None
        if srow is None:
            return False, [(where, f"`in: {sn!r}` names no system of positions")]
        if srow.get('dimension') not in (row.get('systems'), 'any'):
            return False, [(where, f"`{sn}` positions in {srow.get('dimension')}, and the line `{row['line']}` holds "
                                   f"{row.get('systems')}")]
        return srow, []

    def position(self, where, text, srow, row):
        """[problem] of a position written in the system `srow` names, or in one of the line's dimension."""
        if not isinstance(text, str):
            return [(where, f"{text!r} is a position written as text")]
        try:
            p = frame.read(f"{srow['system']}:{text}" if srow and not text.startswith(srow['system'] + ':') else text,
                           self.systems, self.zone)
        except frame.Refused as e:
            return [(where, f"{text!r}: {e}")]
        dim = (self.systems.get(p.system) or {}).get('dimension')
        if srow and p.system != srow['system']:
            return [(where, f"{text!r} is a position of {p.system}, and it is counted in {srow['system']}")]
        if dim not in (row.get('systems'), 'any'):
            return [(where, f"{text!r} is a position in {dim}, and the line `{row['line']}` holds {row.get('systems')}")]
        return []

    def metered(self, srow, row):
        return ((srow or {}).get('restrictions') or {}).get('metered') if srow else row.get('metered')

    def levels(self, srow):
        return [str(lv.get('level')) for lv in listed((srow or {}).get('levels')) if isinstance(lv, dict)]

    def extent(self, where, x):
        """[problem] of `x` as an extent."""
        if not isinstance(x, dict):
            return [(where, "an extent is a mapping of of, in, from, to, measure, level and count (`extent_form`)")]
        extra = set(x) - {'of', 'in', 'from', 'to', 'measure', 'level', 'count'}
        if extra:
            return [(where, f"{', '.join(sorted(extra))}: no attribute of an extent, which holds of, in, from, to, measure, "
                            f"level and count")]
        row, out = self.line(where, x)
        if row is None:
            return out
        if not any(x.get(k) is not None for k in ('from', 'to', 'measure', 'level')):
            out.append((where, "an extent is bounded at an end (`from`, `to`) or by its length (`measure`, or `level` and "
                               "`count`): a region with neither is no region"))
        srow, more = self.system(where, x, row)
        out += more
        if 'level' in x or 'count' in x:
            if 'measure' in x:
                out.append((where, "it states both `measure` and `level`: a length is one or the other"))
            if 'level' not in x or 'count' not in x:
                out.append((where, "`level` and `count` go together: how many cells, of which level"))
            elif srow is None:
                out.append((where, f"`level: {x['level']}`: a level belongs to its system, and `in` names none"))
            elif srow and str(x['level']) not in self.levels(srow):
                out.append((where, f"`level: {x['level']}` is no level of {srow['system']}: {', '.join(self.levels(srow))}"))
            if 'count' in x and not (isinstance(x['count'], str) and WHOLE.match(x['count']) and int(x['count']) > 0):
                out.append((where, f"`count: {x['count']!r}` is a positive whole number of cells"))
        if 'measure' in x:
            m, met = x['measure'], self.metered(srow, row)
            why = quantity_why(self.L, m)
            if not met or met == 'none':
                out.append((where, f"the line `{row['line']}` is metered by nothing here, so a region on it has no length: "
                                   f"drop `measure`, or bound it with from and to"))
            elif why or not isinstance(m, dict):
                out.append((f"{where}.measure", why or "a length is `{ count, unit }`"))
            elif power(self.L, m['unit'], met) is None:
                out.append((f"{where}.measure", f"{m['unit']} is no unit of {met}, which `{row['line']}` meters"))
            else:
                lines = ((srow or {}).get('restrictions') or {}).get('lines') if srow else row.get('lines')
                if isinstance(lines, str) and lines.isdigit() and power(self.L, m['unit'], met) > int(lines):
                    out.append((f"{where}.measure", f"{m['unit']} spans {power(self.L, m['unit'], met)} lines, and "
                                                    f"{srow['system'] if srow else row['line']} has {lines}"))
                if not (exact(m['count']) or 0) > 0:
                    out.append((f"{where}.measure", f"a length is a positive count, not {m['count']!r}"))
        for side in ('from', 'to'):
            if x.get(side) is not None and srow is not False:
                out += self.position(f"{where}.{side}", x[side], srow, row)
        return out

    def recurrence(self, where, x):
        """[problem] of `x` as a recurrence."""
        if not isinstance(x, dict):
            return [(where, "a recurrence is a mapping of of, in, every or each, at, lasts, closures, from, to and times "
                            "(`recurrence_form`)")]
        extra = set(x) - {'of', 'in', 'every', 'each', 'at', 'lasts', 'closures', 'from', 'to', 'times'}
        if extra:
            return [(where, f"{', '.join(sorted(extra))}: no attribute of a recurrence, which holds of, in, every or "
                            f"each, at, lasts, closures, from, to and times")]
        row, out = self.line(where, x)
        if row is None:
            return out
        srow, more = self.system(where, x, row)
        out += more
        if srow is False:
            return out
        for side in ('from', 'to'):
            if x.get(side) is not None:
                out += self.position(f"{where}.{side}", x[side], srow, row)
        at = x.get('at')
        if isinstance(at, list):
            if not at or not all(isinstance(a, str) for a in at):
                out.append((f"{where}.at", "a list of places is a non-empty list of places as the system writes them"))
            elif len(set(at)) != len(at):
                out.append((f"{where}.at", "it names one place twice: each place is one occurrence"))
        elif at is not None and not isinstance(at, str):
            out.append((f"{where}.at", "a place in the cell as the system writes it (`15`, `W-5`), or a list of them"))
        if x.get('lasts') is not None:
            out += self.extent(f"{where}.lasts", x['lasts'])
        if x.get('closures') is not None:
            if not isinstance(x['closures'], list):
                out.append((f"{where}.closures", "a list of positions or extents on which no occurrence falls"))
            else:
                for i, c in enumerate(x['closures']):
                    out += self.extent(f"{where}.closures[{i}]", c) if isinstance(c, dict) else \
                        self.position(f"{where}.closures[{i}]", c, srow, row)
        t = x.get('times')
        if t is not None and not (isinstance(t, str) and WHOLE.match(t) and int(t) > 0):
            out.append((f"{where}.times", f"{t!r} is a positive whole number: how many occurrences in all"))
        every, each = x.get('every'), x.get('each')
        if (every is None) == (each is None):
            out.append((where, "a recurrence strides by one rule: `every` N neighbours or units, or `each` cell of a "
                               "level — exactly one"))
            return out
        if each is not None:
            if srow is None:
                out.append((where, f"`each: {each}` names a level, and a level belongs to its system: say whose, `in`"))
            elif str(each) not in self.levels(srow):
                out.append((where, f"`each: {each}` is no level of {srow['system']}: "
                                   f"{', '.join(self.levels(srow)) or 'it declares none'}"))
            return out
        if not (isinstance(every, dict) and set(every) <= {'count', 'unit'} and isinstance(every.get('count'), str)
                and WHOLE.match(every['count']) and int(every['count']) > 0):
            out.append((f"{where}.every", "`{ count }` (every Nth neighbour) or `{ count, unit }` (every N units), its "
                                          "count a positive whole number"))
            return out
        if 'unit' not in every:
            if srow and srow.get('neighbours') in (None, 'none'):
                out.append((where, f"{srow['system']} declares no neighbours, so there is no Nth"))
            return out
        met = self.metered(srow, row)
        why = self.L.has('units', every['unit'])
        if why:
            out.append((f"{where}.every", why))
        elif not met or met == 'none':
            out.append((where, f"neither `{row['line']}` nor the system it names is metered, so a stride has no length: "
                               f"stride by neighbours, or name a metered system with `in`"))
        elif power(self.L, every['unit'], met) != 1:
            out.append((f"{where}.every", f"{every['unit']} is no stride along {met}"))
        return out


# ------------------------------------------------------------------------------------------------ a clause, a placement
def _reading(b, G, ref):
    """True when `ref` names a `reckon` statement — of this bean by its id, or of another, `<bean>#<id>`."""
    if not isinstance(ref, str):
        return False
    bean, sid = ref.split('#', 1) if '#' in ref else (b.id, ref)
    other = G.beans.get(bean)
    hit = other.ids.get(sid) if other else None
    return bool(hit) and hit[1] == 'reckon'


def clause_problems(J, M, b, where, r):
    from core import lines
    c = r['clause']
    out = lines.attrs_problems(f"{where}.clause", c, J.L.forms.get('clause') or {})
    if not isinstance(c, dict):
        return out
    w = f"{where}.clause"
    if c.get('every') is not None:
        out += M.recurrence(f"{w}.every", c['every'])
    for k in ('during', 'within'):
        if c.get(k) is not None:
            out += M.extent(f"{w}.{k}", c[k])
    for k, want in (('notice', 'duration'), ('amount', None)):
        if c.get(k) is not None:
            why = quantity_why(J.L, c[k], want)
            if why:
                out.append((f"{w}.{k}", why))
    for n, e in enumerate(listed(c.get('falls_due'))):
        if isinstance(e, dict):
            for k in ('after', 'before'):
                if e.get(k) is not None:
                    out += M.extent(f"{w}.falls_due[{n}].{k}", e[k])
    if c.get('due') is not None:
        try:
            frame.read(c['due'], M.systems, J.G.zone)
        except frame.Refused as e:
            out.append((f"{w}.due", str(e)))
    if c.get('falls_due') is not None and c.get('due') is not None:
        out.append((w, "`falls_due` is instead of the day it falls due (`due`): it falls due on a day, or relative to "
                       "a position — one"))
    for k in ('used_by', 'each'):
        if c.get(k) is not None and not _reading(b, J.G, c[k]):
            out.append((f"{w}.{k}", f"{c[k]!r} names no reading (`reckon`) of this bean, nor `<bean>#<id>` of another"))
    when = c.get('when')
    if isinstance(when, dict) and when.get('selection') is not None and not _reading(b, J.G, when['selection']):
        out.append((f"{w}.when", f"{when['selection']!r} names no reading (`reckon`) of this bean, nor `<bean>#<id>`"))
    if c.get('used_by') is not None and c.get('within') is None:
        out.append((w, "`used_by` counts an allowance `within` a window: name the window"))
    asked = J.statement(r.get('of'), b) if r is not None and isinstance(r.get('of'), str) else None
    if c.get('within') is not None and c.get('amount') is None and not (asked and isinstance(asked[3].get('of'), dict)):
        out.append((w, "`within` is the window an `amount` is counted in: state the amount, or ask a statement that "
                       "holds it (a `pay`, a `hold`)"))
    if c.get('of') is not None and c.get('each') is None:
        out.append((w, "`of` is read from each occurrence: with `each`, the reading it occurs for"))
    return out


def placement_problems(J, M, b, where, r):
    from core import lines
    p = r['placed']
    out = lines.attrs_problems(f"{where}.placed", p, J.L.forms.get('placement') or {})
    if not isinstance(p, dict):
        return out
    w = f"{where}.placed"
    if 'u' in p and 'accuracy' in p:
        out.append((w, "it states both `u` and `accuracy`: at most one (`uncertainty_form`)"))
    for k in ('u', 'u_vertical', 'accuracy'):
        if p.get(k) is not None:
            why = uncertainty_why(J.L, k if k == 'accuracy' else 'u', p[k], 'length')
            if why:
                out.append((f"{w}.{k}", why))
    if p.get('zone') is not None and p['zone'] not in J.L.std.zones:
        out.append((f"{w}.zone", f"{p['zone']!r} is no zone of the IANA time zone database"))
    if p.get('during') is not None:
        out += M.extent(f"{w}.during", p['during'])
    if p.get('observed') is not None:
        try:
            frame.read(p['observed'], M.systems, J.G.zone)
        except frame.Refused as e:
            out.append((f"{w}.observed", str(e)))
    takes = p.get('takes')
    if takes is not None:
        if M.takes.get(str(r.get('as'))) in (None, 'none'):
            out.append((f"{w}.takes", f"a being placed as {r.get('as') or 'place'} takes nothing of where it is placed: "
                                      f"what is placed so is placed without limiting its host"))
        hosts = [x for x in listed(r.get('at')) if isinstance(x, str) and (x in J.G.beans or x == 'self')]
        if not hosts:
            out.append((f"{w}.takes", "room or a share is taken of a being: name the host in `at`"))
        for n, q in enumerate(listed(takes)):
            why = quantity_why(J.L, q)
            if why or not isinstance(q, dict):
                out.append((f"{w}.takes[{n}]", why or "what is taken is `{ count, unit }`"))
    return out


def capacity(J):
    """[(where, message)]: what is placed in a host as room, summed exactly in each unit of what it holds, past it."""
    M = Measures(J.L, J.G.zone)
    takers = {}
    for b in J.G.beans.values():
        for i, verb, r in b.items:
            p = r.get('placed') if verb == 'be' and 'held' not in r else None
            if not isinstance(p, dict) or not isinstance(p.get('takes'), list):
                continue
            if M.takes.get(str(r.get('as'))) != 'room':
                continue
            if isinstance(p.get('during'), dict) and p['during'].get('to') is not None:
                continue                       # a placement that has ended takes nothing now
            for h in listed(r.get('at')):
                h = b.id if h == 'self' else h
                if isinstance(h, str) and h in J.G.beans:
                    takers.setdefault(h, []).append((f"{b.id}[{i}] be", p['takes']))
    out = []
    for host, ts in sorted(takers.items()):
        hb = J.G.beans[host]
        for i, verb, r in hb.items:
            if verb != 'hold' or 'held' in r or r.get('by') not in ('self', host):
                continue
            for cap in listed(r.get('of')):
                cf = factor(J.L, cap.get('unit')) if isinstance(cap, dict) else None
                cq = (unit_row(J.L, cap.get('unit')) or {}).get('quantity') if isinstance(cap, dict) else None
                if cf is None or exact(cap.get('count')) is None:
                    continue
                total, who = Fraction(0), []
                for where, takes in ts:
                    for q in takes:
                        f = factor(J.L, q.get('unit')) if isinstance(q, dict) else None
                        if f is None or exact(q.get('count')) is None or \
                                (unit_row(J.L, q.get('unit')) or {}).get('quantity') != cq:
                            continue
                        total += exact(q['count']) * f / cf
                        who.append(f"{where} ({q['count']} {q['unit']})")
                if total > exact(cap['count']):
                    shown = str(total.numerator) if total.denominator == 1 else f"{total.numerator}/{total.denominator}"
                    out.append((f"{host}[{i}] hold", f"it holds {cap['count']} {cap['unit']}, and what is placed in it "
                                                     f"as room takes {shown} {cap['unit']} — {'; '.join(who)}: room is "
                                                     f"taken once, and two beings do not take the same room at once"))
    return out


def problems(J, b):
    """[(where, message)] of rule `measured` for bean `b`: each clause's form, each placement's."""
    M = Measures(J.L, J.G.zone)
    out = []
    for i, verb, r in b.items:
        if 'held' in r:
            continue
        where = f"{b.id}[{i}] {verb}"
        if (verb == 'can' or verb in FIGURE_PERMISSION) and r.get('clause') is not None:
            out += clause_problems(J, M, b, where, r)
        if verb == 'be' and r.get('placed') is not None:
            out += placement_problems(J, M, b, where, r)
        if verb == 'pay':
            out += payment_problems(J, b, where, r)
        if verb == 'mark':
            out += mark_problems(J, b, where, r)
        if verb == 'weigh' and r.get('weighing') is not None:
            out += weighing_problems(J, where, r)
        if (verb == 'can' or verb in FIGURE_PERMISSION) and isinstance(r.get('clause'), dict) and \
                isinstance(r['clause'].get('by_role'), str):
            roles = {rr.get('as') for _j, v, rr in b.items if v == 'agree' and 'held' not in rr}
            if r['clause']['by_role'] not in roles:
                out.append((f"{where}.clause.by_role", f"binds every party that agreed as "
                                                       f"`{r['clause']['by_role']}`, and no `agree` of this bean is `as` "
                                                       f"it ({', '.join(sorted(str(x) for x in roles if x)) or 'none says'})"))
    return out


def _clause(J, b, ref):
    """True when `ref` names a clause: a `can`, or a position on the permission square, holding the form `clause` or
    not — of this bean by its id, or of another, `<bean>#<id>`."""
    hit = J.statement(ref, b) if isinstance(ref, str) else None
    return bool(hit) and (hit[2] == 'can' or hit[2] in FIGURE_PERMISSION)


def _boundaries(J, system):
    """{boundary: its row} of the table a system's `boundaries_in` names, or None where it names none."""
    row = J.systems.get(system) or {}
    bi = row.get('boundaries_in') if isinstance(row, dict) else None
    if not isinstance(bi, dict):
        return None
    try:
        rows = J.L.std.knowledge.rows(bi.get('registry'))
    except Exception:
        rows = []
    return {str(r.get(bi.get('take'))): r for r in rows if isinstance(r, dict)}


def mark_problems(J, b, where, r):
    """A boundary marked in a being (v1 part 12b, today's `fixes`): the base of a cell its system's table lists as
    `marked` — and, where the table names the being, this one — at a position along this being."""
    of = r.get('of')
    try:
        p = frame.read(of, J.systems, J.G.zone) if isinstance(of, str) else None
    except frame.Refused:
        p = None
    if p is None:
        return []                                 # a boundary in words is a mark the law has no table for
    table = _boundaries(J, p.system)
    if table is None:
        return [(f"{where}.of", f"{of} is a position of {p.system}, which lists no boundaries (`boundaries_in`): a mark "
                                f"fixes the base of a cell its system's table names")]
    cell = of.split(':', 1)[1] if ':' in of else of
    row = table.get(cell)
    if row is None:
        return [(f"{where}.of", f"'{cell}' is the base of no cell of {p.system}'s table of boundaries")]
    out = []
    if row.get('fixing') != 'marked':
        out.append((f"{where}.of", f"{p.system}'s table says the base of '{cell}' is fixed `{row.get('fixing')}`: a "
                                   f"boundary declared as a value is marked in no being"))
    if row.get('being') and str(row['being']) != b.id:
        out.append((f"{where}.of", f"{p.system}'s table says the base of '{cell}' is marked in {row['being']}"))
    at = r.get('at')
    m = re.match(r'^([a-z0-9][a-z0-9-]*)/', at) if isinstance(at, str) else None
    if m and m.group(1) != b.id:
        out.append((f"{where}.at", f"'{at}' is along another being: a mark is in the being that holds it"))
    return out


def marks_held(J):
    """The other end: a boundary a table says is marked in a being of this garden is marked by it."""
    marked = set()
    for b in J.G.beans.values():
        for _i, v, r in b.items:
            if v == 'mark' and 'held' not in r and isinstance(r.get('of'), str) and ':' in r['of']:
                marked.add((b.id, r['of'].split(':', 1)[1]))
    out = []
    for name in sorted(J.systems):
        table = _boundaries(J, name) if isinstance(J.systems.get(name), dict) else None
        for cell, row in sorted((table or {}).items()):
            being = str(row.get('being') or '')
            if being in J.G.beans and (being, cell) not in marked:
                out.append((f"{name} boundaries", f"the base of '{cell}' is marked in {being}, which holds no `mark` of "
                                                   f"it: a mark is said at both ends"))
    return out


def payment_problems(J, b, where, r):
    """What a payment holds beside its roles (v1 part 12b): what it was `charged` in another currency, and what it
    `settles` — each an occurrence of a clause, and how much of it."""
    from core import lines
    out = []
    q, ch = r.get('of'), r.get('charged')
    if ch is not None and isinstance(q, dict) and isinstance(ch, dict) and not quantity_why(J.L, ch):
        qu, cu = str(q.get('unit')), str(ch.get('unit'))
        cur = J.L.std.currencies
        if qu == cu:
            out.append((f"{where}.charged", f"is in {cu}, the unit it was priced in: `charged` is what it came to in "
                                            f"another currency, from which the rate is read — in the same one it says "
                                            f"nothing"))
        elif (qu in cur) != (cu in cur) or (qu not in cur and (unit_row(J.L, qu) or {}).get('quantity') != (unit_row(J.L, cu) or {}).get('quantity')):
            out.append((f"{where}.charged", f"{qu} and {cu} are not two measures of one quantity: what it was charged "
                                            f"in is the same thing in another unit"))
        elif exact(str(ch.get('count'))) == 0 and exact(str(q.get('count'))) != 0:
            out.append((f"{where}.charged", "is nothing, for a price that is something: no rate is implied by zero"))
    form = J.L.forms.get('settlement') or {}
    for n, e in enumerate(listed(r.get('settles'))):
        w = f"{where}.settles[{n}]"
        got = lines.attrs_problems(w, e, form)
        out += got
        if got or not isinstance(e, dict):
            continue
        if not _clause(J, b, e.get('clause')):
            out.append((f"{w}.clause", f"{e.get('clause')!r} names no clause: a `can`, or a position on the permission "
                                       f"square, of this bean by its id or of another (`<bean>#<id>`)"))
        occ = str(e.get('occurrence'))
        if not re.match((form.get('entries') or {}).get('occurrence', {}).get('in', {}).get('pattern', '.*'), occ):
            out.append((f"{w}.occurrence", f"{occ!r} is not an occurrence: the member's bean, or a place in it"))
        if e.get('amount') is not None:
            why = quantity_why(J.L, e['amount'])
            if why:
                out.append((f"{w}.amount", why))
    keys = [(str(e.get('clause')), str(e.get('occurrence'))) for e in listed(r.get('settles')) if isinstance(e, dict)]
    for k in sorted({k for k in keys if keys.count(k) > 1}):
        out.append((f"{where}.settles", f"settles {k[1]} of {k[0]} twice: one entry for each occurrence of each clause"))
    return out


def weighing_problems(J, where, r):
    """A weighing's form, and its judgments (bin/reckon.py `check_weighing`, the one judge of a weighing): every pair
    judged once, each naming criteria, consistent or saying why it stands (v1 part 12b)."""
    from core import lines
    out = lines.attrs_problems(f"{where}.weighing", r['weighing'], J.L.forms.get('weighing') or {})
    if out:
        return out
    import reckon as dmreckon
    return [(f"{where}.weighing", what.split(': ', 1)[-1]) for level, what in dmreckon.check_weighing('', r['weighing'])
            if level == 'error']


# ------------------------------------------------------------------------------------------------ the view in today's words
# The read tools that walk a repetition, count an allowance or warn before a day (bin/stale.py, bin/reckon.py,
# bin/ledger.py) read an entry in the shape today's term held it. These give a clause and a placement so, from their
# statements: one code reads both laws, and each unit is given by the English name the law attaches to its UCUM code
# (core/law/units.yaml), which is today's name of it.
_NAMES = {}
FIGURE_PERMISSION = {'obligatory': 'required', 'omissible': 'omissible', 'permitted': 'permitted',
                     'forbidden': 'forbidden'}


def clause_term(L):
    """A clause as the readers of its days take it (bin/stale.py, bin/ledger.py): the core's form `clause`
    (core/law/measures.yaml), its attributes and how it runs out (`expiry`), typed as they read it and with each stance
    in the word the view gives a clause's `permission` (FIGURE_PERMISSION)."""
    from core.lines import typed
    f = (getattr(L, 'forms', None) or {}).get('clause') or {}
    exp = typed(f.get('expiry') or {})
    for k in ('why', 'lapses_why'):
        if isinstance(exp.get(k), dict):
            exp[k] = {FIGURE_PERMISSION.get(p, p): w for p, w in exp[k].items()}
    return {'term': 'clauses', 'schema': {'shape': 'open_map_of_entries', 'key_form': 'kebab',
                                          'attrs': typed(f.get('attrs') or {}), 'expiry': exp}}


def unit_names(root):
    """{UCUM code: the law's English name} of the release at `root` and the garden's own units."""
    if root not in _NAMES:
        from core import read
        names = {}
        for p in (os.path.join(root, 'core', 'law', 'units.yaml'), os.path.join(os.path.dirname(HERE), 'core', 'law',
                                                                               'units.yaml')):
            if os.path.isfile(p):
                for r in read.data(p).get('units') or []:
                    if isinstance(r, dict) and r.get('name'):
                        names.setdefault(str(r['unit']), str(r['name']))
        try:
            for r in read.document(os.path.join(root, 'VOCAB.md'))[0].get('units') or []:
                if isinstance(r, dict) and r.get('name'):
                    names.setdefault(str(r['unit']), str(r['name']))
        except Exception:
            pass
        _NAMES[root] = names
    return _NAMES[root]


def in_today_words(x, names):
    """`x` with each unit named as today's law names it, and each count and number of times a whole number where it is
    one — as today's readers take them."""
    if isinstance(x, dict):
        return {k: (names.get(v, v) if k == 'unit' and isinstance(v, str)
                    else int(v) if k in ('count', 'times') and isinstance(v, str) and WHOLE.match(v)
                    else in_today_words(v, names)) for k, v in x.items()}
    if isinstance(x, list):
        return [in_today_words(v, names) for v in x]
    return x


def clauses_of(b, root):
    """{id: clause entry} of a bean, in today's shape, over what `details.clauses` keeps of each: each `can` — `what`
    (its `of`), `by`, `to`, `note`, `permission` (the figure it stands under) and its form, its figure's form beside —
    and each position on the permission square of a statement that is no `can` (`obligatory: { of: <a pay> }`), by its
    own id: `what` its note, `by` and `to` the asked statement's, `amount` what a `pay` asks, and its form."""
    names = unit_names(root)
    kept = ((b.header.get('details') or {}).get('clauses') if isinstance(b.header.get('details'), dict) else None) or {}
    stmts = {r['id']: (verb, r) for _i, verb, r in b.items if isinstance(r.get('id'), str) and 'held' not in r}
    figs = {}
    for _i, verb, r in b.items:
        if verb in FIGURE_PERMISSION and isinstance(r.get('of'), str) and 'held' not in r:
            figs.setdefault(r['of'], (FIGURE_PERMISSION[verb], r))
    out = {}

    def entry(key):
        return dict(kept.get(key) or {}) if isinstance(kept.get(key), dict) else {}
    for _i, verb, r in b.items:
        if verb != 'can' or 'held' in r or not isinstance(r.get('id'), str):
            continue
        e = entry(r['id'])
        e['what'] = r.get('of')
        for role in ('by', 'to', 'note'):
            if r.get(role) is not None and r.get(role) != 'unknown':
                e[role] = r[role]
        fig, fr = figs.get(r['id'], (None, {}))
        if fig:
            e['permission'] = fig
        for form in (fr.get('clause'), r.get('clause')):
            if isinstance(form, dict):
                e.update(in_today_words(form, names))
        out[r['id']] = e
    for _i, verb, r in b.items:
        if verb not in FIGURE_PERMISSION or 'held' in r or not isinstance(r.get('of'), str) \
                or stmts.get(r['of'], (None,))[0] in (None, 'can'):
            continue
        av, ar = stmts[r['of']]
        key = r.get('id') if isinstance(r.get('id'), str) else r['of']
        e = entry(key)
        e['what'] = r.get('note') or ar.get('note') or f"{av} {r['of']}"
        for role in ('by', 'to'):
            if isinstance(ar.get(role), str) and ar[role] != 'unknown':
                e[role] = ar[role]
        if av in ('pay', 'hold') and isinstance(ar.get('of'), dict):
            e.setdefault('amount', in_today_words(ar['of'], names))
        e['permission'] = FIGURE_PERMISSION[verb]
        if isinstance(r.get('clause'), dict):
            e.update(in_today_words(r['clause'], names))
        out[key] = e
    return out


def placed_of(r, root, beans):
    """What a `be`'s form says beside its position, in today's shape: its host (`{bean}`, the being of the garden's
    `beans` in its `at`), and its form's attributes."""
    e = {}
    host = next((x for x in listed(r.get('at')) if isinstance(x, str) and x in beans), None)
    if host:
        e['host'] = {'bean': host}
    if isinstance(r.get('placed'), dict):
        e.update(in_today_words(r['placed'], unit_names(root)))
    return e
