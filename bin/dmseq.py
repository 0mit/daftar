#!/usr/bin/env python3
"""dmseq — the reader of a series and of a course: what a line held at each position, and where a being stands on a walk.

    python3 bin/dmseq.py show <bean> <key>              # each row at its position, every value with its unit
    python3 bin/dmseq.py rows <bean> <key>              # the rows as one table: the position, then each channel
    python3 bin/dmseq.py at <bean> <key> <position>     # what each channel holds there: an offset, or a position
    python3 bin/dmseq.py course <bean> [<course>]         # where the being stands on each walk, since when, who acts next
    python3 bin/dmseq.py check [<bean> ...]             # every series and course, judged as the gate judges them
    python3 bin/dmseq.py compare <bean> <key> <bean> <key> [--k 2]   # two recordings of one line, row by row
    add --exact to print a value read between two rows exactly, rather than to its uncertainty's digits

(`python` on Windows.) It writes nothing, and nothing it prints is stored anywhere (manifesto: once): a series holds what
was read, and whatever is read from it — a value between two rows, where a course stands, how long since — is read
again each time. It reads the garden whose tools it is, by the law the gate loads.

A SERIES (std-vocab `series`) is a line whose positions hold values. Its positions are a rule — a `grid`, a recurrence
whose occurrences are the rows in order — or listed in a `span`, an extent from whose `from` each row writes its
offset in the series' `unit`. `holds` names the channels, one column each: a measured value (`quantity` and `unit`), a
position (`system`, written in its one form less a `prefix` and `suffix`, or a whole offset from `from`), or a code of
a published scheme (`scheme`). The rows are one table (bin/dmparse.py reads it), inline in the bean or in the parts
`series/<bean>/<key>/<part>.tsv`. Every number printed comes with the rows it came from.

WHAT IS READ BETWEEN ROWS is what the channel says: a `point` with `between: linear` on a straight line between its two
neighbouring readings — only where the line and the channel are both metered; a `state` holds until the next row; a
`mean`, `sum`, `min` or `max` over its row's region is read inside that region, said as what it is. Nothing is read
before the first row or after the last: it NEVER EXTRAPOLATES. A cell set aside (`excluded`) is shown, with its judge
and why, and read by nothing.

PRECISION. A value read between rows is exact as arithmetic, and printed to the digits of the channel's uncertainty (u
to at most two significant digits, the value rounded to the same place: GUM 7.2.6), `--exact` printing the exact
fraction. A value a row holds is printed as it was written. A channel with no `u` is printed exactly. A stated
`accuracy` is turned into a u here, never by a writer: a bound `a` gives a/√3, a 68 % radius itself, a 95 % radius R/1.96,
and an accuracy whose kind is `unstated` gives none.

TIME is counted in days of 86400 seconds, as bin/dmcal.py counts it: no leap second is counted, so a grid of seconds
across one reads the second after it.

A COURSE (std-vocab `courses`, `moves`) is a series along time whose value at each move is a step of the walk it names.
Where the being stands is the step of its last move; how long since, the time from that move to now; who acts next, the
step's `by`, read as a party of the being where it has `parties`; and whether the step has run past its `usually`.

THE API other tools call, reading this garden:
    rows(root, bean, key)          -> [{'n', 'at', 'position', 'cells', 'excluded', 'source'}], in the order of the line
    read_at(root, bean, key, at)   -> {channel: {'value', 'how', 'rows', 'why'}}: what each channel holds at one position
    where(root, bean, course, now)  -> {'step', 'since', 'by', 'party', 'overdue', 'moves'}: where a course stands
    check_series(law, bean, key, entry, parts)   -> [(level, where, what)]: the gate's judgment of one series entry
    walk_problems(steps, systems), check_moves(moves, steps, walk): its judgments of a walk's steps and of one course
"""
import decimal
import glob
import math
import os
import re
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dmparse  # noqa: E402 — the one reader of a table, and UTF-8 streams on every platform
import dmcal    # noqa: E402 — positions in any calendar, and moments below the day

ROOT = os.path.dirname(HERE)
PY = 'python' if os.name == 'nt' else 'python3'
SERIES_DIR = 'series'                     # a series' parts: series/<bean>/<key>/<part>.tsv, in the estate
PART = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
WHOLE = re.compile(r'^(0|[1-9][0-9]{0,39})$')
SIGNED = re.compile(r'^-?(0|[1-9][0-9]{0,39})$')
POSITION_COLUMNS = ('at', 'from', 'to')
K = 2                                     # the coverage factor two readings are compared at: D42's k, overridden by --k


# ============================================================================ the law, as the gate reads it
class Law:
    """What a series is read by: the units, quantities, systems, aspects and figures the gate loaded — the standard's
    and this garden's own rows — and a registry by name. The gate hands its own; standing alone, this reads the gate's."""

    def __init__(self, units, quantities, systems, aspects, figures, registry):
        self.units, self.quantities, self.systems = units, quantities, systems
        self.aspects, self.figures, self.registry = aspects, figures, registry

    @classmethod
    def of_garden(cls):
        import dmcheck                    # the gate's reading of the law, overlays and additions included
        return cls(dmcheck.UNITS, dmcheck.QUANTITIES, dmcheck.SYSTEMS, dmcheck.ASPECTS, dmcheck.FIGURES,
                   dmcheck.registry)

    def value_type(self, name):
        return next((r for r in (self.registry('value_types') or []) if isinstance(r, dict) and r.get('type') == name), {})

    def gaps(self):
        return {str(r['token']): r for r in (self.registry('gap_tokens') or []) if isinstance(r, dict) and r.get('token')}

    def count_ok(self, c):
        pat = self.value_type('count').get('pattern')
        return bool(pat) and bool(dmparse.law_match(pat, c))

    def codes(self, scheme):
        return {str(r.get('code')) for r in (self.registry(scheme) or []) if isinstance(r, dict) and r.get('code') is not None}

    def factor(self, unit):
        """A unit's exact ratio to its quantity's coherent unit, or None (a currency, a unit the law lacks)."""
        u = self.units.get(unit) if isinstance(unit, str) else None
        f = (u or {}).get('factor')
        return Fraction(f[0], f[1]) if isinstance(f, list) and len(f) == 2 and all(isinstance(x, int) for x in f) else None

    def quantity_of(self, unit):
        return ((self.units.get(unit) if isinstance(unit, str) else None) or {}).get('quantity')

    def measures(self, unit, dimension):
        """True when `unit` measures `dimension` to the first power and nothing else: a length, a duration."""
        q = self.quantities.get(self.quantity_of(unit)) or {}
        return dict(q.get('of') or {}) == {dimension: 1}

    def coherent(self, quantity):
        """The unit of `quantity` whose factor is one: what every other unit of it is converted into, exactly."""
        return next((n for n, u in self.units.items() if u.get('quantity') == quantity and u.get('factor') == [1, 1]), None)


# ============================================================================ numbers, exactly
def exact(c):
    """A count as a Fraction, or None — never through a float."""
    if isinstance(c, bool):
        return None
    if isinstance(c, int):
        return Fraction(c)
    if isinstance(c, str) and re.fullmatch(r'-?(0|[1-9][0-9]*)(\.[0-9]+)?', c, re.ASCII):
        return Fraction(c)
    return None


def show(x):
    """A Fraction exactly: a terminating decimal in full, else n/d."""
    n, d = x.numerator, x.denominator
    if d == 1:
        return str(n)
    r = d
    for p in (2, 5):
        while r % p == 0:
            r //= p
    if r != 1:
        return f"{n}/{d}"
    k = 0
    while (10 ** k) % d:
        k += 1
    digits = str(abs(n) * (10 ** k) // d).rjust(k + 1, '0')
    return ('-' if n < 0 else '') + digits[:-k] + '.' + digits[-k:].rstrip('0')


def u_places(u):
    """The decimal place an uncertainty's last digit is at, at most two significant digits (GUM 7.2.6): 0.05 -> 2,
    0.052 -> 3, 0.0523 -> 3, 1.3 -> 1, 23 -> 0, 230 -> -1."""
    if u is None or u <= 0:
        return None
    with decimal.localcontext() as c:
        c.prec = 60
        d = decimal.Decimal(u.numerator) / decimal.Decimal(u.denominator)
    e = d.adjusted()                      # the exponent of its first significant digit
    written = exact_places(u)
    two = 1 - e                           # the place of the second significant digit
    return min(written, two) if written is not None else two


def exact_places(x):
    """How many decimal places a Fraction takes written exactly, or None when it does not terminate."""
    s = show(x)
    return None if '/' in s else (len(s.split('.', 1)[1]) if '.' in s else 0)


def rounded(x, place):
    """`x` rounded half to even at a decimal place (a negative place is tens, hundreds), as text."""
    with decimal.localcontext() as c:
        c.prec = 200
        d = decimal.Decimal(x.numerator) / decimal.Decimal(x.denominator)
        q = decimal.Decimal(1).scaleb(-place)
        r = d.quantize(q, rounding=decimal.ROUND_HALF_EVEN)
    return format(r, 'f')


# ============================================================================ a series, read
class Series:
    """One entry of a series term, read against the law: its line, its channels, its rows. `problems` holds what is
    wrong, as (level, where, what) with `where` inside the entry — the gate prints them under the bean and the key."""

    def __init__(self, law, bean, key, entry, parts=None, form=True):
        self.law, self.bean, self.key, self.entry = law, bean, key, entry if isinstance(entry, dict) else {}
        self.parts = parts or {}
        self.problems = []
        self.channels, self.rows = {}, []
        self.kind = self.node = self.aspect = self.system = self.metered = self.unit = None
        self.stride = self.length = None
        self.cells = self.entry.get('placement') or 'point'
        self.read_form = form
        self._read()

    # -- what is wrong
    def err(self, where, what):
        self.problems.append(('error', where, what))

    def warn(self, where, what):
        self.problems.append(('warn', where, what))

    # -- the line
    def _read(self):
        e = self.entry
        if 'held' in e:
            self.kind = 'held'
            other = sorted(k for k in e if k != 'held')
            if other:
                self.err('', f"holds {other} beside `held`: a series kept off git is sealed whole — its line, channels "
                             f"and rows are kept with it in the held layer, and the entry says nothing but where")
            return
        if 'grid' in e and 'span' in e:
            self.err('', "states both a `grid` and a `span`: its positions are given by a rule or listed, never both")
            return
        self.kind = 'grid' if 'grid' in e else 'span' if 'span' in e else None
        if self.kind is None:
            return                                           # `entry_one_of` refuses it, by name
        self.node = e[self.kind] if isinstance(e[self.kind], dict) else None
        if self.node is None:
            return                                           # the recurrence's or extent's own check refuses it
        an = self.node.get('of')
        self.aspect = self.law.aspects.get(an) if isinstance(an, str) else None
        if not self.aspect:
            return                                           # refused as an extent or a recurrence already
        fig = self.law.figures.get(self.aspect.get('figure')) or {}
        if fig.get('holds') != 'possible':
            self.err(f".{self.kind}", f"lies on aspect '{an}', a {self.aspect.get('figure')}, and nothing is held at its "
                                      f"positions — {fig.get('holds_why') or 'its figure says so'}")
            return
        sn = self.node.get('in')
        if isinstance(sn, str):
            self.system = self.law.systems.get(sn)
        elif self.node.get('from') is not None:
            dim = (self.aspect.get('domain') or {}).get('systems')
            self.system = next((s for s in self.law.systems.values() if s.get('dimension') in (dim, 'any')
                                and dmparse.in_form(s, self.node['from'])), None)
        # the system's meter where one is named (27.0: a meter is the system's); else the aspect's
        m = ((self.system.get('restrictions') or {}).get('metered') if self.system else self.aspect.get('metered'))
        self.metered = None if m in (None, 'none') else m
        _f = self.node.get('from')
        if self.system and _f is not None and dmparse.in_form(self.system, _f) is False:
            self.err(f".{self.kind}.from", f"'{_f}' is not a position in the one form '{self.system.get('system')}' "
                                           f"writes ({self.system.get('form_note') or dmparse.form_said(self.system)}): "
                                           f"the series counts its positions `in: {self.system.get('system')}`")
            return
        if self.node.get('from') is None:
            self.err(f".{self.kind}", f"states no `from`: {'a grid' if self.kind == 'grid' else 'a listed series'} "
                                      f"counts its rows from the position it begins at")
        self.unit = e.get('unit')
        if not self.metered:
            self.err(f".{self.kind}", f"lies on a line with no measure ({'system ' + repr(self.system.get('system')) if self.system else 'aspect ' + repr(an)}"
                                      f" is metered in nothing): a series counts its positions in a unit of the line's "
                                      f"length — a count along a line with no measure is a local frame's, and a walk's "
                                      f"steps are a course's")
        elif not self.unit:
            self.err('', f"states no `unit`: what an offset counts, and the resolution held — a unit of {self.metered}")
        elif self.law.factor(self.unit) is None or not self.law.measures(self.unit, self.metered):
            self.err('.unit', f"'{self.unit}' measures {self.law.quantity_of(self.unit)}, and the line is metered in "
                              f"{self.metered}: an offset counts a unit of the line's own length")
        else:
            self._stride()
        self._channels()
        if not self.problems or all(p[0] == 'warn' for p in self.problems):
            self._table()

    def _stride(self):
        """The grid's stride in whole units, and a listed series' length where the extent states one."""
        n, u = self.node, self.law.factor(self.unit)
        if self.kind == 'grid':
            for k in ('to', 'times', 'at', 'lasts', 'closures'):
                if n.get(k) is not None:
                    self.err(f".grid.{k}", f"a grid's rows say where it ends and where in each stride they lie — "
                                           f"`{k}` is a repetition's, not a series'")
            ev, each = n.get('every'), n.get('each')
            if isinstance(ev, dict) and ev.get('unit') is not None:
                f = self.law.factor(ev.get('unit'))
                if f is None or not isinstance(ev.get('count'), int):
                    return                                   # the recurrence's own check refuses it
                s = ev['count'] * f / u
            elif isinstance(ev, dict):
                self.err('.grid.every', "strides by neighbours alone: a series' grid strides by a measure "
                                        "(`every: { count, unit }`) or by a level with a length (`each: day`)")
                return
            elif each is not None:
                lv = next((l for l in ((self.system or {}).get('levels') or []) if isinstance(l, dict)
                           and l.get('level') == each), None)
                if not lv or not lv.get('unit') or self.law.factor(lv['unit']) is None:
                    self.err('.grid.each', f"strides by the cells of '{each}', a level with no fixed length: a series' "
                                           f"grid strides by a measure, or by a level that has one (a day, an hour)")
                    return
                s = self.law.factor(lv['unit']) / u
            else:
                return
            if s.denominator != 1 or s <= 0:
                self.err('.grid', f"strides {show(s)} {self.unit}s: a stride is a whole number of the unit held — "
                                  f"choose the unit it is whole in")
                return
            self.stride = int(s)
        else:
            m = n.get('measure')
            if isinstance(m, dict) and self.law.factor(m.get('unit')) is not None and exact(m.get('count')) is not None:
                self.length = exact(m['count']) * self.law.factor(m['unit']) / u
            elif n.get('to') is not None:
                a, b = self.offset_of(n.get('from')), self.offset_of(n.get('to'))
                if a is not None and b is not None:
                    self.length = b - a

    # -- positions on the line
    def _ms(self):
        """Milliseconds in one unit held, where the line is time and a unit is a whole number of them."""
        f = self.law.factor(self.unit)
        if f is None or self.metered != 'time':
            return None
        ms = f * 1000
        return int(ms) if ms.denominator == 1 else None

    def position(self, offset):
        """The position `offset` units from the line's `from`, in the line's own system form, or None where no
        arithmetic here writes it."""
        start = (self.node or {}).get('from')
        if start is None or offset is None:
            return None
        if isinstance(offset, Fraction) and offset.denominator != 1:
            return None
        offset = int(offset)
        if self.metered == 'time':
            ms = self._ms()
            if ms is None:
                return None
            try:
                mo = dmcal.moment(start)
                res = mo.resolution
                step = offset * ms
                if res == 'minute' and step % 60000:
                    res = 'second' if not step % 1000 else 'millisecond'
                elif res == 'second' and step % 1000:
                    res = 'millisecond'
                return dmcal.write_moment(mo.ms + step, mo.calendar, mo.offset, res)
            except (ValueError, dmcal.NotByRule):
                pass
            if ms % dmcal.DAY_MS == 0:
                try:
                    return dmcal.from_day(dmcal.to_day(start) + offset * (ms // dmcal.DAY_MS), dmcal.calendar_of(start))
                except (ValueError, dmcal.NotByRule):
                    return None
            return None
        if self.metered == 'length' and (self.system or {}).get('system') == 'along':
            m = re.match(r'^(.*\+)(.*)$', str(start))
            f = self.law.factor(self.unit)
            if not m or f is None or exact(m.group(2)) is None:
                return None
            at = exact(m.group(2)) + offset * f
            s = show(at)
            return None if '/' in s else m.group(1) + s
        return None

    def offset_of(self, position):
        """The offset of a position on the line, in units held — a Fraction — or None."""
        start = (self.node or {}).get('from')
        if position is None or start is None:
            return None
        if SIGNED.match(str(position)):
            return Fraction(int(str(position)))
        if self.metered == 'time':
            ms = self._ms()
            if not ms:
                return None
            try:
                return Fraction(dmcal.moment(position).ms - dmcal.moment(start).ms, ms)
            except (ValueError, dmcal.NotByRule):
                pass
            try:
                return Fraction((dmcal.to_day(str(position)) - dmcal.to_day(str(start))) * dmcal.DAY_MS, ms)
            except (ValueError, dmcal.NotByRule):
                return None
        if self.metered == 'length' and (self.system or {}).get('system') == 'along':
            a, b = re.match(r'^(.*)\+(.*)$', str(start)), re.match(r'^(.*)\+(.*)$', str(position))
            f = self.law.factor(self.unit)
            if a and b and a.group(1) == b.group(1) and f and exact(a.group(2)) is not None and exact(b.group(2)) is not None:
                return (exact(b.group(2)) - exact(a.group(2))) / f
        return None

    # -- the channels
    def _channels(self):
        hs = self.entry.get('holds')
        if hs is None:
            self.err('', "names no channels (`holds`): a series holds something at each of its positions")
            return
        for i, ch in enumerate(hs if isinstance(hs, list) else [hs]):
            if not isinstance(ch, dict) or not isinstance(ch.get('name'), str):
                continue                                     # the entries' own check refuses it
            w = f".holds[{ch['name']}]"
            if ch['name'] in POSITION_COLUMNS:
                self.err(w, f"is named '{ch['name']}', a name the table keeps for a row's position")
            kinds = [k for k in ('quantity', 'system', 'scheme') if ch.get(k) is not None]
            if len(kinds) != 1:
                self.err(w, f"holds {' and '.join(kinds) or 'nothing'}: a channel holds exactly one of a measured value "
                            f"(`quantity` with its `unit`), a position (`system`) or a code (`scheme`)")
                continue
            kind = kinds[0]
            c = dict(ch)
            if kind == 'quantity':
                c['kind'] = 'quantity'
                if not ch.get('unit'):
                    self.err(w, f"is a {ch['quantity']} with no `unit`: every cell is counted in one unit, named once")
                elif self.law.quantity_of(ch['unit']) not in (None, ch['quantity']):
                    self.err(w + '.unit', f"'{ch['unit']}' measures {self.law.quantity_of(ch['unit'])}, and the channel "
                                          f"is a {ch['quantity']}")
                for k in ('from', 'prefix', 'suffix'):
                    if ch.get(k) is not None:
                        self.err(w + f'.{k}', f"is a position's — a measured value is written as a count")
            elif kind == 'system':
                row = self.law.systems.get(ch['system'])
                c['row'] = row
                if ch.get('from') is not None or ch.get('unit') is not None:
                    c['kind'] = 'offset'
                    if ch.get('from') is None or ch.get('unit') is None:
                        self.err(w, "writes offsets with only one of `from` and `unit`: an offset counts a unit from a "
                                    "position, and both are said once")
                    for k in ('prefix', 'suffix'):
                        if ch.get(k) is not None:
                            self.err(w + f'.{k}', "is a position's written form, and this channel writes offsets")
                    rm = self.metered_in(row)
                    if row and ch.get('unit') and (rm in (None, 'none') or not self.law.measures(ch['unit'], rm)):
                        self.err(w + '.unit', f"'{ch['unit']}' counts no length of system '{ch['system']}'"
                                              + (f", which is metered in {rm}" if rm not in (None, 'none') else ", which has none"))
                else:
                    c['kind'] = 'position'
            else:
                c['kind'] = 'code'
                if not self.law.codes(ch['scheme']):
                    self.err(w + '.scheme', f"'{ch['scheme']}' has no codes this garden can read")
            if c['kind'] in ('position', 'code') and ch.get('unit') is not None and kind != 'system':
                self.err(w + '.unit', "a code has no unit")
            # what a cell stands for, against where a row sits
            sf = ch.get('stands_for')
            region = self.cells in ('bounds', 'preceding', 'following')
            position = self.cells in ('point', 'preceding', 'following')
            if sf in ('mean', 'sum', 'min', 'max') and not region:
                self.err(w + '.stands_for', f"'{sf}' is over a region, and the series' rows sit at points (`placement: "
                                            f"{self.cells}`): say where a row's region is with `placement`")
            if sf in ('point', 'instant') and not position:
                self.err(w + '.stands_for', f"'{sf}' is at a position, and the series' rows sit over regions (`placement: "
                                            f"bounds`) with none")
            if ch.get('between') == 'linear':
                numeric = c['kind'] in ('quantity', 'offset')
                if sf != 'point':
                    self.err(w + '.between', f"is linear, and the channel stands for '{sf}': a straight line is read "
                                             f"between two readings of a point")
                elif not numeric or not self.metered:
                    self.err(w + '.between', "is linear where " + ("the channel holds no measure" if not numeric else
                             "the line has none") + ": a value is read between two rows only where the line and the "
                             "channel are both metered — anything else invents a measure")
            # uncertainty: its form is `uncertainty_form`'s, judged by the gate's one check of it (`check_uncertainty`);
            # what only a channel can say is that a position or a code states none here
            for k in ('u', 'accuracy'):
                if ch.get(k) is not None and c['kind'] in ('position', 'code'):
                    self.err(w + f'.{k}', f"is a measured {k}, and the channel holds " + ("codes" if c['kind'] == 'code'
                             else "positions in their written form; state it where the position's system does"))
            for k in ('limits', 'monotone'):
                if ch.get(k) is not None and c['kind'] not in ('quantity', 'offset'):
                    self.err(w + f'.{k}', f"`{k}` is a measured channel's, and this one holds "
                                          f"{'codes' if c['kind'] == 'code' else 'positions in their written form'}")
            self.channels[ch['name']] = c

    def metered_in(self, row):
        """The dimension a system's line is metered in: its own, which it states (27.0) — a system inherits no meter."""
        if not isinstance(row, dict):
            return None
        m = (row.get('restrictions') or {}).get('metered')
        return None if m in (None, 'none') else m

    # -- the table
    def columns(self):
        return [] if self.kind == 'grid' else ['from', 'to'] if self.cells == 'bounds' else ['at']

    def _table(self):
        e, sources = self.entry, []
        if e.get('rows') is not None and self.parts:
            self.err('.rows', f"is inline, and the series has parts in files too ({', '.join(sorted(self.parts))}): its "
                              f"rows are one table — in the bean, or in its parts")
            return
        if e.get('rows') is not None:
            sources = [('rows', None, e['rows'])]
        elif self.parts:
            for name, text in sorted(self.parts.items()):
                if not PART.match(name) or (self.kind == 'grid' and not WHOLE.match(name)):
                    self.err(f" part {name}.tsv", "is not named as a part is: " + ("a grid's part is named by the number "
                             "of its first row, `0.tsv`, `1440.tsv`" if self.kind == 'grid' else "a kebab name, `2026-06` "
                             "or `download-3`"))
                    continue
                sources.append(('part', name, text))
        else:
            self.err('', f"holds no rows: write them inline (`rows: |`, a table), or in its parts "
                         f"`{SERIES_DIR}/{self.bean}/{self.key}/<part>.tsv`")
            return
        cols = self.columns()
        want = cols + sorted(self.channels)
        seen = {}
        for src, name, text in sources:
            where = '.rows' if src == 'rows' else f" part {name}.tsv"
            bad = dmparse.table_problems(text)
            if bad:
                if self.read_form or src == 'part':
                    self.err(where, f"is not a table in its one form: {bad[0]}")
                continue
            head, rows = dmparse.table_read(text)
            if head[:len(cols)] != cols or sorted(head[len(cols):]) != sorted(self.channels):
                self.err(where, f"names the columns {head}: its header is " + (' '.join(f'`{c}`' for c in cols) + ", then "
                         if cols else "") + f"each channel once ({', '.join(sorted(self.channels)) or 'none named'})"
                         + (" — a grid's rows write no position: row n is at occurrence n" if self.kind == 'grid' and
                            head and head[0] in POSITION_COLUMNS else ""))
                continue
            first = int(name) if (self.kind == 'grid' and name is not None) else 0
            for i, cells in enumerate(rows):
                line = i + 2
                cell = dict(zip(head, cells))
                if self.kind == 'grid':
                    at = first + i
                    key = at
                else:
                    pos = [cell[c] for c in cols]
                    bad = [p for p in pos if not WHOLE.match(p)]
                    if bad:
                        self.err(f"{where} line {line}", f"writes its position as {bad[0]!r}: an offset is a whole number "
                                                         f"of {self.unit}s from the series' `from`, never a gap")
                        continue
                    at = tuple(Fraction(int(p)) for p in pos) if len(pos) > 1 else Fraction(int(pos[0]))
                    key = at
                vals = {c: cell[c] for c in self.channels}
                for c, v in vals.items():
                    why = self.cell_problem(self.channels[c], v)
                    if why:
                        self.err(f"{where} line {line}", f"column `{c}` holds {v!r}: {why}")
                if key in seen:
                    if seen[key]['cells'] != vals:
                        self.err(f"{where} line {line}", f"is at the position {self._said(key)} a row of "
                                                         f"{seen[key]['source']} holds with other values — a position "
                                                         f"holds one row; two recordings are two series")
                    continue
                seen[key] = {'n': None, 'at': at, 'cells': vals, 'source': where.strip() + f" line {line}"}
        order = sorted(seen.values(), key=lambda r: r['at'] if not isinstance(r['at'], tuple) else r['at'][0])
        prev = None
        for n, r in enumerate(order):
            r['n'] = n if self.kind != 'grid' else r['at']
            if self.kind != 'grid' and isinstance(r['at'], tuple):
                a, b = r['at']
                if not a < b:
                    self.err(f" {r['source']}", f"runs from {show(a)} to {show(b)}: a region runs forward, from before to")
                if prev is not None and isinstance(prev['at'], tuple) and a < prev['at'][1]:
                    self.err(f" {r['source']}", f"begins at {show(a)}, inside the row before it (to {show(prev['at'][1])}): "
                                                f"two regions of one series do not overlap")
            last = r['at'][1] if isinstance(r['at'], tuple) else r['at']
            if self.length is not None and self.kind == 'span' and last > self.length:
                self.err(f" {r['source']}", f"lies at {show(last)} {self.unit}s, beyond the span's end "
                                            f"({show(self.length)}): a listed row lies within the span")
            prev = r
        if self.kind == 'grid':
            gaps = [n for n in range(len(order)) if order[n]['at'] != n] if order else []
            if gaps:
                self.err('', f"holds no row {gaps[0]}: a grid's rows run from 0 without a hole — a row nobody read is "
                             f"written, its cells gap tokens")
        self.rows = order
        self._monotone()
        self._excluded()

    def _said(self, key):
        return f"{show(key[0])}–{show(key[1])}" if isinstance(key, tuple) else (show(key) if isinstance(key, Fraction) else str(key))

    def cell_problem(self, ch, v):
        """Why a cell is not one its channel holds, or None."""
        gaps = self.law.gaps()
        if v in gaps:
            if gaps[v].get('takes') and not (ch.get('limits') or {}).get('below' if v == '<' else 'above'):
                return (f"a bare `{v}` stands for the channel's `limits`, and it states none — write the limit after it, "
                        f"`{v}0.5`")
            if gaps[v].get('takes') and ch['kind'] not in ('quantity', 'offset'):
                return f"`{v}` says a measured value lies beyond a limit, and this channel holds no measure"
            return None
        if v[:1] in gaps and (gaps.get(v[:1]) or {}).get('takes'):
            if ch['kind'] not in ('quantity', 'offset'):
                return f"`{v[:1]}` says a measured value lies beyond a limit, and this channel holds no measure"
            return None if self.law.count_ok(v[1:]) else f"`{v[:1]}` is followed by the limit, a count"
        if ch['kind'] == 'quantity':
            return None if self.law.count_ok(v) else ("a measured value is a count in plain decimal digits, or a gap "
                                                      f"token ({' '.join(sorted(gaps))})")
        if ch['kind'] == 'offset':
            return None if SIGNED.match(v) else f"an offset is a whole number of {ch.get('unit')}s from {ch.get('from')}"
        if ch['kind'] == 'code':
            return None if v in self.law.codes(ch['scheme']) else f"it is no code of {ch['scheme']}"
        row = ch.get('row')
        full = str(ch.get('prefix') or '') + v + str(ch.get('suffix') or '')
        if row and dmparse.in_form(row, full) is False:
            return (f"{full!r} is not a position in the one form '{row.get('system')}' writes "
                    f"({row.get('form_note') or dmparse.form_said(row)})")
        return None

    def _monotone(self):
        excl = self.excluded_cells()
        for name, ch in self.channels.items():
            way = ch.get('monotone')
            if way not in ('increasing', 'decreasing'):
                continue
            prev = None
            for r in self.rows:
                v = exact(r['cells'].get(name)) if ch['kind'] in ('quantity', 'offset') else None
                if v is None or (self._row_key(r), name) in excl or (self._row_key(r), None) in excl:
                    continue
                if prev is not None and ((way == 'increasing' and v < prev[0]) or (way == 'decreasing' and v > prev[0])):
                    self.err(f" {r['source']}", f"`{name}` goes back ({prev[1]} then {r['cells'][name]}), and the channel "
                                                f"is {way}: exclude the cell, naming its judge and why, if it is kept")
                prev = (v, r['cells'][name])

    def _row_key(self, r):
        """How an exclusion names a row: its number on a grid, its offset (its `from`) on a listed series."""
        return Fraction(r['at']) if self.kind == 'grid' else (r['at'][0] if isinstance(r['at'], tuple) else r['at'])

    def excluded_cells(self):
        out = {}
        for x in self.entry.get('excluded') or []:
            if isinstance(x, dict) and exact(x.get('at')) is not None:
                out[(exact(x['at']), x.get('channel'))] = x
        return out

    def _excluded(self):
        keys = {self._row_key(r) for r in self.rows}
        for i, x in enumerate(self.entry.get('excluded') or []):
            if not isinstance(x, dict):
                continue
            at = exact(x.get('at'))
            if at is not None and at not in keys:
                self.err(f".excluded[{i}]", f"sets aside a cell at {x.get('at')}, where no row is: `at` is a row's "
                                            f"{'number (the first 0)' if self.kind == 'grid' else 'offset, its `from` under `bounds`'}")
            if x.get('channel') is not None and x['channel'] not in self.channels:
                self.err(f".excluded[{i}].channel", f"'{x['channel']}' is no channel of the series "
                                                    f"({', '.join(sorted(self.channels))})")

    # -- reading
    def u_of(self, name):
        """A channel's standard uncertainty in its own unit, as a Fraction, or None."""
        ch = self.channels.get(name) or {}
        own = self.law.factor(ch.get('unit'))
        v = ch.get('u')
        if isinstance(v, dict) and exact(v.get('count')) is not None and own and self.law.factor(v.get('unit')):
            return exact(v['count']) * self.law.factor(v['unit']) / own
        a = ch.get('accuracy')
        if isinstance(a, dict) and exact(a.get('count')) is not None and own and self.law.factor(a.get('unit')):
            x = exact(a['count']) * self.law.factor(a['unit']) / own
            k = a.get('kind')
            if k == 'bound':
                return Fraction(decimal.Decimal(x.numerator) / decimal.Decimal(x.denominator) / decimal.Decimal(3).sqrt())
            if k == 'radius-68':
                return x
            if k == 'radius-95':
                return x / Fraction(196, 100)
        return None

    def places(self):
        """[(position, region start, region end, row)] in the order of the line: a row's position (None under `bounds`)
        and the region it stands for — its own under `bounds`, back to the row before under `preceding`, on to the next
        under `following` (a grid's last row one stride on). A point's region is its position alone."""
        pts = []
        for r in self.rows:
            if self.kind == 'grid':
                a = Fraction(r['at'] * self.stride) if self.stride else None
                if a is None:
                    continue
                pts.append((None, a, a + self.stride, r) if self.cells == 'bounds' else (a, a, a, r))
            elif isinstance(r['at'], tuple):
                pts.append((None, r['at'][0], r['at'][1], r))
            else:
                pts.append((r['at'], r['at'], r['at'], r))
        if self.cells not in ('following', 'preceding'):
            return pts
        step = self.stride if self.kind == 'grid' and self.stride else 0
        out = []
        for i, (p, _a, _b, r) in enumerate(pts):
            if self.cells == 'following':
                out.append((p, p, pts[i + 1][0] if i + 1 < len(pts) else p + step, r))
            else:
                out.append((p, pts[i - 1][0] if i else p - step, p, r))
        return out

    def read(self, at):
        """{channel: reading} at an offset (a Fraction, in units held) — never beyond the first or the last row."""
        excl = self.excluded_cells()
        places = self.places()
        out = {}
        for name, ch in self.channels.items():
            live = [t for t in places if (self._row_key(t[3]), name) not in excl and (self._row_key(t[3]), None) not in excl]
            out[name] = self._read_one(name, ch, live, at)
        return out

    def _read_one(self, name, ch, live, x):
        gaps = self.law.gaps()

        def said(v, how, rows):
            if v in gaps or (v[:1] in gaps and (gaps.get(v[:1]) or {}).get('takes')):
                g = gaps.get(v) or gaps.get(v[:1]) or {}
                return {'value': v, 'how': 'beyond a limit' if g.get('takes') else 'gap', 'rows': rows, 'why': g.get('meaning', '')}
            return {'value': v, 'how': how, 'rows': rows, 'why': ''}
        if not live:
            return {'value': None, 'how': 'not read', 'rows': [], 'why': "no row holds a value that is read"}
        if x < min(t[1] for t in live) or x > max(t[2] for t in live):
            return {'value': None, 'how': 'not read', 'rows': [], 'why': "beyond the first or the last row: nothing is "
                                                                          "extrapolated"}
        sf, cells = ch.get('stands_for'), self.cells
        for p, a, b, r in live:                              # a row's own position
            if p is not None and p == x:
                return said(r['cells'][name], 'row', [r['source']])
        if sf in ('mean', 'sum', 'min', 'max') or (sf == 'state' and cells == 'bounds'):
            for p, a, b, r in live:                          # inside a row's region: what the row stands for over it
                inside = (a <= x < b) if cells in ('bounds', 'following') else (a < x <= b)
                if a != b and inside:
                    return said(r['cells'][name], f"over the row's region, as its {sf}", [r['source']])
        before = [t for t in live if t[0] is not None and t[0] < x]
        after = [t for t in live if t[0] is not None and t[0] > x]
        if not before or not after:
            return {'value': None, 'how': 'not read', 'rows': [], 'why': "no row's position or region holds it"}
        (p0, _a0, _b0, r0), (p1, _a1, _b1, r1) = before[-1], after[0]
        v0, v1 = r0['cells'][name], r1['cells'][name]
        if sf == 'state':
            return said(v0, 'state, held from the row before', [r0['source']])
        if sf == 'point' and ch.get('between') == 'linear':
            e0, e1 = exact(v0), exact(v1)
            if e0 is None or e1 is None:
                return {'value': None, 'how': 'not read', 'rows': [r0['source'], r1['source']],
                        'why': "a neighbouring row holds no value — a line is drawn between two readings"}
            return {'value': e0 + (e1 - e0) * (x - p0) / (p1 - p0), 'how': 'linear, between two rows',
                    'rows': [r0['source'], r1['source']], 'why': ''}
        return {'value': None, 'how': 'not read', 'rows': [r0['source'], r1['source']],
                'why': f"between two rows, and the channel stands for '{sf}'"
                       + (" with nothing read between rows (`between: none`)" if sf == 'point' else '')}


def check_series(law, bean, key, entry, parts=None, form=True):
    """[(level, where, what)] for one entry of a series term: `where` inside the entry, `level` 'error' or 'warn'. `form`
    False leaves the inline table's own form to the value type's check, which the gate runs beside this."""
    return Series(law, bean, key, entry, parts, form=form).problems


# ============================================================================ walks and courses
def walk_problems(steps, law_systems=None):
    """What is wrong with a walk's step attributes the gate's entry rules cannot say: [(step id, what)]. The step
    entries are the ones that are mappings; the ids, `next` and reachability are the walk's own check."""
    out = []
    law_systems = law_systems or {}
    for st in steps:
        if not isinstance(st, dict) or not isinstance(st.get('id'), str):
            continue
        sid = st['id']
        if st.get('resumes') is True and st.get('next'):
            out.append((sid, "is a pause (`resumes`) with a `next`: the move after a pause returns to the step it was "
                             "entered from, so it names no way on"))
        if st.get('final') is True and st.get('next'):
            out.append((sid, "is `final` and names a `next`: nothing follows a final step"))
        if st.get('final') is True and st.get('resumes') is True:
            out.append((sid, "is both `final` and a pause: a pause is returned from, and nothing follows a final step"))
        rs = st.get('reasons')
        if rs is not None:
            if not isinstance(rs, list) or not rs or not all(isinstance(x, str) and re.fullmatch(r'[a-z0-9]+(-[a-z0-9]+)*', x)
                                                           for x in rs):
                out.append((sid, f"`reasons` is {rs!r}: a list of kebab words, each a reason a move into the step may "
                                 f"cite — `reasons: [sold-elsewhere, withdrawn-by-author]`"))
            elif len(set(rs)) != len(rs):
                out.append((sid, "`reasons` names one reason twice: each is listed once"))
        u = st.get('usually')
        if u is not None:
            why = _usually_problem(u, law_systems)
            if why:
                out.append((sid, f"`usually` {why}"))
    return out


def _usually_problem(u, systems):
    """What only a step can say of its `usually`: the extent's own form is judged as an extent (`in: extent`, the gate's
    `check_extent`), and a length a step takes is on time and has no ends."""
    if not isinstance(u, dict):
        return None                                   # not an extent at all: refused as one, by name
    if u.get('of') != 'time':
        return f"is an extent on '{u.get('of')}': how long a step takes is an extent on time"
    ends = sorted(set(u) & {'from', 'to'})
    return f"holds {ends}: how long a step takes has no ends — a `measure`, or a `level` and a `count`" if ends else None


def walk_ends(steps):
    """The step ids a walk may end at: a step with no `next` that is not a pause."""
    return [st['id'] for st in steps if isinstance(st, dict) and isinstance(st.get('id'), str)
            and not st.get('next') and st.get('resumes') is not True]


def reached_without_next(st):
    """A way out (`exit`) and a pause (`resumes`) are reached from any step, with no `next` naming them."""
    return isinstance(st, dict) and (st.get('exit') is True or st.get('resumes') is True)


def check_moves(moves, steps, walk_name):
    """[(index, level, what)] for one course's moves, in the order written, against the walk's steps."""
    out = []
    by_id = {st['id']: st for st in steps if isinstance(st, dict) and isinstance(st.get('id'), str)}
    ids = [st['id'] for st in steps if isinstance(st, dict) and isinstance(st.get('id'), str)]
    prev, pause_from, prev_ms = None, None, None
    seen = {}
    for i, mv in moves:
        sid = mv.get('step')
        # A MOVE IS TOLD FROM ANOTHER BY ITS MOMENT: two moves of one course to one step at one moment are one move written
        # twice, and a merge, which keys a move by its course, moment and step, could not tell them apart
        _k = (dmcal.shown(mv.get('at')), str(sid))     # a moment in either form (27.0) is one moment
        if _k in seen:
            out.append((i, 'error', f"reaches '{sid}' at {dmcal.shown(mv.get('at'))}, as move {seen[_k]} does: a move is told from "
                                    f"another by its moment — one move is written once, and a step visited again is "
                                    f"visited at a later moment"))
        seen.setdefault(_k, i)
        st = by_id.get(sid)
        if st is None:
            out.append((i, 'error', f"reaches '{sid}', which is no step of the walk {walk_name} ({', '.join(ids)})"))
            prev = None
            continue
        try:
            ms = dmcal.moment(mv.get('at')).ms
        except Exception:
            ms = None                                        # its form is the type's to refuse, by name
        if ms is not None and prev_ms is not None and ms < prev_ms:
            out.append((i, 'error', f"is at {dmcal.shown(mv.get('at'))}, before the move it follows: a course's moments never go back "
                                    f"— each move is written when it is made"))
        offered = None
        if prev is None:
            if sid != (ids[0] if ids else None) and not reached_without_next(st):
                offered = f"the walk begins at '{ids[0]}'"
        else:
            p = by_id.get(prev)
            if p is not None and p.get('final') is True:
                out.append((i, 'error', f"follows '{prev}', a final step: nothing follows it — a case that goes on is "
                                        f"a new course, or the walk's end is not final"))
            elif p is not None and p.get('resumes') is True:
                if sid != pause_from and st.get('exit') is not True:
                    offered = f"'{prev}' is a pause, and the move after it returns to '{pause_from}', where it was entered from"
            elif p is not None and not p.get('next'):
                pass                                         # an end that is not final may be left
            elif p is not None:
                tos = [n.get('to') for n in p.get('next') or [] if isinstance(n, dict)]
                if sid not in tos and not reached_without_next(st):
                    offered = f"'{prev}' leads on to {', '.join(repr(t) for t in tos)} only"
        if offered:
            if str(mv.get('why') or '').strip():
                out.append((i, 'warn', f"reaches '{sid}', a move the walk does not offer ({offered}); its `why` says why"))
            else:
                out.append((i, 'error', f"reaches '{sid}', a move the walk does not offer ({offered}): write why in "
                                        f"`why`, or move along the walk"))
        r = mv.get('reason')
        if r is not None:
            rs = st.get('reasons') if isinstance(st.get('reasons'), list) else None
            if not rs:
                out.append((i, 'error', f"cites the reason '{r}', and the step '{sid}' lists none (`reasons`): a reason "
                                        f"is one of the step's, and words go in `why`"))
            elif r not in rs:
                out.append((i, 'error', f"cites the reason '{r}', which is not one of the step '{sid}''s: {', '.join(rs)}"))
        if st.get('resumes') is True and prev is not None:
            pause_from = prev if not (by_id.get(prev) or {}).get('resumes') else pause_from
        prev, prev_ms = sid, ms if ms is not None else prev_ms
    return out


# ============================================================================ reading from a garden
def _front(path):
    try:
        head, body = dmparse.read(path)
        fm = dmparse.loads(head) if head else None
        return fm if isinstance(fm, dict) else None
    except Exception:
        return None


def _doc(root, bean):
    fm = _front(os.path.join(root, 'beans', bean + '.md'))
    if fm is None:
        raise ValueError(f"no bean '{bean}' here (beans/{bean}.md)")
    return fm


def parts_of(root, bean, key):
    """{part name: its text} for the files `series/<bean>/<key>/*.tsv`, read as they are."""
    out = {}
    for f in sorted(glob.glob(os.path.join(root, SERIES_DIR, bean, key, '*'))):
        name = os.path.basename(f)
        if os.path.isfile(f):
            try:
                out[name[:-4] if name.endswith('.tsv') else name] = open(f, encoding='utf-8', newline='').read()
            except (OSError, UnicodeDecodeError):
                out[name] = None
    return out


def _series_terms():
    import dmcheck
    return [t for t, s in dmcheck.SCHEMAS.items() if s.get('series') is True]


def series_of(root, bean, key, law=None):
    if root is not None and os.path.realpath(root) != os.path.realpath(ROOT):
        raise ValueError(f"dmseq reads the garden whose tools it is ({ROOT}); read {root} with its own bin/dmseq.py")
    law = law or Law.of_garden()
    fm = _doc(ROOT, bean)
    for t in _series_terms():
        node = fm.get(t)
        if isinstance(node, dict) and key in node:
            return Series(law, bean, key, node[key], parts_of(ROOT, bean, key))
    raise ValueError(f"bean '{bean}' holds no series '{key}'")


def rows(root, bean, key):
    """The rows of one series, in the order of its line: each {'n', 'at' (offset in units held, or (from, to)),
    'position' (in the line's system form, where it can be written), 'cells', 'excluded', 'source'}."""
    s = series_of(root, bean, key)
    excl = s.excluded_cells()
    out = []
    for r in s.rows:
        off = Fraction(r['at'] * s.stride) if s.kind == 'grid' and s.stride else r['at']
        pos = (s.position(off[0]), s.position(off[1])) if isinstance(off, tuple) else s.position(off)
        k = s._row_key(r)
        out.append({'n': r['n'], 'at': off, 'position': pos, 'cells': dict(r['cells']), 'source': r['source'],
                    'excluded': {c: (x.get('by'), x.get('why')) for (a, c), x in excl.items() if a == k}})
    return out


def read_at(root, bean, key, at):
    """What each channel of one series holds at one position: `at` an offset in the units held (a count), or a position
    in the line's form. {channel: {'value', 'how', 'rows', 'why'}}; `value` a Fraction where it was read between rows."""
    s = series_of(root, bean, key)
    x = s.offset_of(at)
    if x is None:
        raise ValueError(f"{at!r} is neither an offset in {s.unit}s nor a position on this series' line")
    return s.read(x)


def where(root, bean, course, now=None):
    """Where one course of a bean stands: {'step', 'at', 'since' (ms, or None), 'by', 'party', 'usually', 'overdue',
    'moves'} — read from its moves and its walk, never stored."""
    fm = _doc(root or ROOT, bean)
    tr = (fm.get('courses') or {}).get(course) if isinstance(fm.get('courses'), dict) else None
    if not isinstance(tr, dict):
        raise ValueError(f"bean '{bean}' has no course '{course}'")
    ref = tr.get('walk') or {}
    wid = ref.get('mapping') or ref.get('bean')
    wfm = _front(os.path.join(root or ROOT, 'mappings' if 'mapping' in ref else 'beans', f"{wid}.md")) or {}
    steps = [s for s in (wfm.get('steps') or []) if isinstance(s, dict)]
    mv = [m for m in (fm.get('moves') or []) if isinstance(m, dict) and m.get('course') == course]
    if not mv:
        return {'step': None, 'moves': 0}
    last = mv[-1]
    st = next((s for s in steps if s.get('id') == last.get('step')), {})
    now_ms = dmcal.moment(now).ms if now else _now_ms()
    try:
        since = now_ms - dmcal.moment(last.get('at')).ms
    except Exception:
        since = None
    party = None
    if st.get('by') and isinstance(fm.get('parties'), dict):
        p = fm['parties'].get(st['by'])
        party = ((p or {}).get('who') or {}).get('bean') or (p or {}).get('external')
    over = None
    u = st.get('usually')
    if since is not None and isinstance(u, dict) and isinstance(u.get('measure'), dict):
        law = Law.of_garden()
        f = law.factor(u['measure'].get('unit'))
        if f is not None and exact(u['measure'].get('count')) is not None and law.quantity_of(u['measure'].get('unit')) == 'duration':
            over = Fraction(since, 1000) > exact(u['measure']['count']) * f
    return {'step': last.get('step'), 'at': dmcal.shown(last.get('at')), 'since': since, 'by': st.get('by'), 'party': party,
            'usually': u, 'overdue': over, 'final': st.get('final') is True, 'moves': len(mv), 'walk': wid}


def _now_ms():
    import datetime
    t = datetime.datetime.now().astimezone()
    return dmcal.moment(t.isoformat(timespec='milliseconds').replace('T', ' ')).ms


def _since(ms):
    if ms is None:
        return 'not known'
    m = ms // 60000
    d, h, mi = m // 1440, (m % 1440) // 60, m % 60
    return (f"{d} day(s) " if d else '') + (f"{h} hour(s) " if h or d else '') + f"{mi} minute(s)"


# ============================================================================ the command line
def _print_value(s, name, v, exact_):
    ch = s.channels.get(name) or {}
    unit = f" {ch['unit']}" if ch.get('kind') == 'quantity' and ch.get('unit') else ''
    gaps = s.law.gaps()
    if isinstance(v, str) and v in gaps and not gaps[v].get('takes'):
        return f"{v} ({gaps[v].get('meaning')})"
    if isinstance(v, str) and v[:1] in gaps and gaps[v[:1]].get('takes'):
        lim = v[1:] or str(((ch.get('limits') or {}).get('below' if v[:1] == '<' else 'above')))
        return f"{v[:1]} {lim}{unit} ({'below' if v[:1] == '<' else 'above'} a limit)"
    if isinstance(v, str) and ch.get('kind') == 'offset' and SIGNED.match(v):
        pos = None
        try:
            f = s.law.factor(ch.get('unit'))
            mo = dmcal.moment(ch.get('from'))
            ms = int(v) * f * 1000 if f is not None else None
            if ms is not None and ms.denominator == 1 and s.law.quantity_of(ch.get('unit')) == 'duration':
                pos = dmcal.write_moment(mo.ms + int(ms), mo.calendar, mo.offset, mo.resolution)
        except (ValueError, dmcal.NotByRule, TypeError):
            pos = None
        return f"{v} {ch.get('unit')}(s) from {ch.get('from')}" + (f" = {pos}" if pos else '')
    if isinstance(v, Fraction):
        u = s.u_of(name)
        p = u_places(u) if u is not None else None
        if exact_ or u is None:
            return f"{show(v)}{unit}" + (f" (u {show(u) if exact_places(u) is not None else rounded(u, 4)})" if u is not None else '')
        return f"{rounded(v, p)}{unit} (u {rounded(u, p)}, printed to its digits; --exact for the exact value)"
    return f"{v}{unit}" if v is not None else '—'


def _problems_out(bean, key, term, s):
    for level, where_, what in s.problems:
        print(dmparse.said(f"{'ERROR' if level == 'error' else 'WARN '} {bean}: {term}[{key}]{where_} — {what}"))


def main(argv):
    exact_ = '--exact' in argv
    argv = [a for a in argv if a != '--exact']
    k = K
    if '--k' in argv:
        i = argv.index('--k')
        try:
            k = Fraction(argv[i + 1])
        except (IndexError, ValueError):
            print("dmseq: --k takes a number, the coverage factor: `--k 2`", file=sys.stderr)
            return 2
        argv = argv[:i] + argv[i + 2:]
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.split('\n\nA SERIES')[0].replace('python3 bin/', PY + ' bin/'))
        return 0 if argv else 2
    cmd, rest = argv[0], argv[1:]
    try:
        if cmd in ('show', 'rows') and len(rest) == 2:
            s = series_of(ROOT, rest[0], rest[1])
            if s.kind == 'held':
                print(f"{rest[0]}: series {rest[1]} is kept off git, in the held layer, at {s.entry.get('held')} — "
                      f"it is read where it is kept")
                return 0
            _problems_out(rest[0], rest[1], 'series', s)
            rs = rows(ROOT, rest[0], rest[1])
            names = sorted(s.channels)
            if cmd == 'rows':
                bounds = any(isinstance(r['at'], tuple) for r in rs)
                print('\t'.join((['from', 'to'] if bounds else ['position']) + names))
                for r in rs:
                    at, pos = r['at'], r['position']
                    cols = ([str(pos[0] or show(at[0])), str(pos[1] or show(at[1]))] if isinstance(at, tuple)
                            else [str(pos or show(Fraction(at)))])
                    print('\t'.join(cols + [r['cells'][n] for n in names]))
                return 0
            line = s.system.get('system') if s.system else (s.node or {}).get('of')
            print(f"{rest[0]}: series {rest[1]} — {len(rs)} row(s) on {line}, from {(s.node or {}).get('from')}, "
                  f"counted in {s.unit}s" + (f", a row every {s.stride}" if s.stride else '')
                  + ("; days of 86400 seconds, no leap second counted" if s.metered == 'time' else ''))
            for r in rs:
                pos = r['position'] if not isinstance(r['position'], tuple) else f"{r['position'][0]} to {r['position'][1]}"
                off = r['at'] if not isinstance(r['at'], tuple) else r['at']
                print(f"  {pos or ('offset ' + (show(off) if not isinstance(off, tuple) else show(off[0]) + '–' + show(off[1])))}"
                      f"   [{r['source']}]")
                for n in names:
                    x = r['excluded'].get(n) or r['excluded'].get(None)
                    print(f"      {n}: {_print_value(s, n, r['cells'][n], exact_)}"
                          + (f"   SET ASIDE by {x[0]}: {x[1]}" if x else ''))
            return 1 if any(p[0] == 'error' for p in s.problems) else 0
        if cmd == 'at' and len(rest) == 3:
            s = series_of(ROOT, rest[0], rest[1])
            got = read_at(ROOT, rest[0], rest[1], rest[2])
            x = s.offset_of(rest[2])
            print(f"{rest[0]}: series {rest[1]} at {rest[2]} (offset {show(x)} {s.unit}s from {(s.node or {}).get('from')})")
            for n, r in sorted(got.items()):
                print(f"  {n}: {_print_value(s, n, r['value'], exact_)} — {r['how']}"
                      + (f" ({'; '.join(r['rows'])})" if r['rows'] else '') + (f" — {r['why']}" if r['why'] else ''))
            return 0
        if cmd == 'course' and rest:
            fm = _doc(ROOT, rest[0])
            names = [rest[1]] if len(rest) > 1 else sorted((fm.get('courses') or {}) if isinstance(fm.get('courses'), dict) else [])
            if not names:
                print(f"{rest[0]}: no course")
                return 0
            for t in names:
                w = where(ROOT, rest[0], t)
                if not w.get('step'):
                    print(f"{rest[0]}: course {t} — no move yet")
                    continue
                print(f"{rest[0]}: course {t} on walk {w['walk']} — at '{w['step']}' since {w['at']} "
                      f"({_since(w['since'])} ago; {w['moves']} move(s))"
                      + ("; a final step: nothing follows" if w['final'] else
                         f"; who acts next: {w['by']}" + (f" ({w['party']})" if w['party'] else '') if w['by'] else '')
                      + (f"; it usually takes {w['usually']['measure']['count']} {w['usually']['measure']['unit']}(s)"
                         + (" — PAST that" if w['overdue'] else '') if isinstance(w.get('usually'), dict)
                         and isinstance(w['usually'].get('measure'), dict) else ''))
            return 0
        if cmd == 'check':
            import dmcheck
            law = Law.of_garden()
            dmcheck.build_docs()
            dmcheck.build_all_fm_and_targets()
            want = set(rest) or {b for (ib, b) in dmcheck.docs if ib}
            n = 0
            for (ib, b), (fm, _body) in sorted(dmcheck.docs.items()):
                if not ib or b not in want:
                    continue
                for t in _series_terms():
                    for key, e in ((fm.get(t) or {}).items() if isinstance(fm.get(t), dict) else []):
                        s = Series(law, b, key, e, parts_of(ROOT, b, key))
                        _problems_out(b, key, t, s)
                        n += sum(1 for p in s.problems if p[0] == 'error')
            print(f"dmseq check: {n} error(s) in the series of {len(want)} bean(s) — the gate judges courses and walks "
                  f"with the rest: `{PY} bin/dmcheck.py`")
            return 1 if n else 0
        if cmd == 'compare' and len(rest) == 4:
            a, b = series_of(ROOT, rest[0], rest[1]), series_of(ROOT, rest[2], rest[3])
            ra, rb = rows(ROOT, rest[0], rest[1]), rows(ROOT, rest[2], rest[3])
            ia = {str(r['position']): r for r in ra}
            ib_ = {str(r['position']): r for r in rb}
            common = sorted(set(a.channels) & set(b.channels))
            print(f"compare {rest[0]}/{rest[1]} with {rest[2]}/{rest[3]}: {len(common)} channel(s) in both, k = {show(k)}")
            for pos in sorted(set(ia) | set(ib_)):
                if pos not in ia or pos not in ib_:
                    print(f"  {pos}: held by {'the first' if pos in ia else 'the second'} only")
                    continue
                for n in common:
                    x, y = ia[pos]['cells'][n], ib_[pos]['cells'][n]
                    fa, fb = a.law.factor(a.channels[n].get('unit')), b.law.factor(b.channels[n].get('unit'))
                    ex, ey = exact(x), exact(y)
                    if ex is None or ey is None or fa is None or fb is None:
                        print(f"  {pos} {n}: {'agree' if x == y else 'differ'} ({x} | {y})")
                        continue
                    d = ex * fa - ey * fb
                    ua, ub = a.u_of(n), b.u_of(n)
                    if d == 0:
                        lab = 'agree'
                    elif ua is not None and ub is not None and d * d <= k * k * ((ua * fa) ** 2 + (ub * fb) ** 2):
                        lab = f'compatible within k·u (k = {show(k)}) — labelled, never merged'
                    else:
                        lab = 'differ'
                    print(f"  {pos} {n}: {lab} ({x} {a.channels[n].get('unit')} | {y} {b.channels[n].get('unit')})")
            return 0
    except ValueError as e:
        print(dmparse.said(f"dmseq: {e}"), file=sys.stderr)
        return 2
    print(f"dmseq: {' '.join(argv)!r} — see `{PY} bin/dmseq.py --help`", file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
