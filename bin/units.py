#!/usr/bin/env python3
"""units — a measured value, converted WITHIN its quantity, exactly.

    python3 bin/units.py 90 kilometre-per-hour metre-per-second      # -> 25
    python3 bin/units.py 1.5 hectare square-metre                    # -> 15000
    python3 bin/units.py 3 decibel-per-kilometre decibel-per-metre   # -> 0.003
    python3 bin/units.py 100 XTS EUR --rate 0.9173                   # -> 91.73: two currencies meet only at a rate
    python3 bin/units.py 12.5 unece-rec20:KGM                        # -> 12.5 kg: a standard's code, read as the law's
    python3 bin/units.py 12.5 unece-rec20:KGM g                      # -> 12500 g
    python3 bin/units.py 12.5 kg unece-rec20                         # -> 12.5 unece-rec20:KGM: written back
    python3 bin/units.py --codes unece-rec20                         # every code of it, and what each crosses to
    python3 bin/units.py --code unece-rec20:MON                      # what one code crosses to, or through its axes
    python3 bin/units.py --judge loinc:2345-7 95 mg/dL               # is this value what the code says one is

A unit names the QUANTITY it measures and its FACTOR to that quantity's coherent unit, as a pair of whole numbers, so a
conversion is exact arithmetic and never a rounded float — and the result is PRINTED exactly too: a terminating decimal in
full, anything else as a fraction of whole numbers. Beside a fraction it prints a rounded decimal for the
reader, marked `≈` (`--digits N`, six by default) — an aid to the eye, which the gate would refuse as a count. A CONVERSION IS A READING, NEVER A RECORD: a bean keeps a value in the
unit it was measured in, and every conversion starts from that, so errors cannot accumulate through a chain of them. It converts within one quantity and REFUSES across two: a speed
is not an acceleration however the numbers line up. Everything it knows is read from the law: `seed/std-vocab.md`, or
in a garden of the core (v1 part 7) the core's units in UCUM (core/law/units.yaml), each with the law's English name
and its factor attached — a unit is named by its code (`km/h`) or by that name (`kilometre-per-hour`), and is one unit.

MONEY (std-vocab 21.0). A currency is a unit of the `money` quantity, and the currencies are the rows of a registry the
law points at (`units_from`), each with the decimal places it is written in. NO FACTOR JOINS TWO OF THEM — the quantity
says `crosswalk: observed` — so a conversion between two currencies is REFUSED unless it is given the rate someone
observed (`--rate R`: units of the target per one of the source, a decimal string). With it the result is exact, and it
is a reading at that rate, never a record: the rate is a fact with a source and a day, and belongs in the ledger as one.

A STANDARD'S CODES (core/law/registries.yaml, `units_crosswalk_form`). A scheme whose row names a `units` registry
crosses each of its codes into the law: a unit, a kind, a line, a system's positions or its cells, a shape. A count
written with a code is read as the law writes it — `{count, unit}`, an extent's `level` and `count` for a calendar's
cells (a month on an invoice is a cell, never a duration), a position for a system's unit of position (`C:21.5`) — and
the law's value is written back with the code that crosses to it. Everything is read from the law's crossing; nothing
here names a standard.
"""
import copy, decimal, functools, os, re, sys
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as dmparse          # the one loader: the law read as the gate reads it

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# A COUNT AS THE GATE READS ONE: a whole number, or a decimal written as a string — ASCII digits, one optional sign, no
# exponent, and no leading zero: `010` is ten to a person and eight to a YAML 1.1 reader, and a count is what was
# written, so it is written without one. The one pattern every money reader here shares, so `--5` is refused in one
# place and not half-read in two.
COUNT = re.compile(r'-?(0|[1-9][0-9]*)(\.([0-9]+))?', re.ASCII)
# AND A COUNT IS BOUNDED, as the law bounds it: at most DIGITS digits before the point and DIGITS after, so that every
# reader, in any language on any machine, holds it exactly. Python would read further — to its own limit of 4300 digits,
# past which it refuses with a ValueError nobody expected — and a count one reader holds and another cannot is two
# readers disagreeing about an amount. What is longer is REFUSED, with the reason, and never half-read.
DIGITS = 40


def exact(count):
    """A count EXACTLY, as a Fraction — or None when it is not one: a float (it has already lost what it lost), a bool,
    an exponent, a second sign. Whatever is not read exactly is not read. A count longer than a count may be (DIGITS)
    raises ValueError, saying so: it is in a count's form, and it is still not read."""
    if isinstance(count, bool):
        return None
    if isinstance(count, int):
        if abs(count) >= 10 ** DIGITS:                  # compared, never printed: str() of a long int is what raises
            raise ValueError(f"a whole number of more than {DIGITS} digits is longer than a count may be")
        return Fraction(count)
    m = COUNT.fullmatch(count) if isinstance(count, str) else None
    if not m:
        return None
    if len(m.group(1)) > DIGITS or len(m.group(3) or '') > DIGITS:
        raise ValueError(f"a count of {len(m.group(1))} digits before the point and {len(m.group(3) or '')} after is "
                         f"longer than a count may be (at most {DIGITS} of each)")
    return Fraction(count)


def law():
    """(units, quantities) as the law declares them — the caller's own copy, which it may change without changing
    them for anyone else in the process."""
    units, quantities = _law()
    return copy.deepcopy(units), copy.deepcopy(quantities)


@functools.lru_cache(maxsize=1)
def _law():
    # ONE PARSE PER PROCESS. Every conversion asked for the law, and the law was parsed from its YAML each time: the
    # round trip of every pair of units in test/quantities.py spent two and a half minutes re-reading one file. Read
    # only here and by convert(), which changes nothing; law() hands everyone else a copy.
    #
    # THE LAW IS THE CORE'S, with the garden's own rows (VOCAB.md `units`) and every currency of ISO 4217: one reader
    # of one law, which the gate reads alike (v1 part 13; core/law/units.yaml).
    return _core_law()


def runs_core():
    """True in a garden that runs the core (GARDEN.md pins `core@…`, bin/check.py the one reader of the pin)."""
    try:
        import check
        return check.runs_core(check.pin(ROOT))
    except Exception:
        return False


def _core_law():
    """(units, quantities) of a garden of the core (v1 part 7): each unit by its UCUM code, its English name and its
    factor attached (core/law/units.yaml and the garden's own `units`), each currency of ISO 4217 a unit of the
    quantity whose units are a registry's rows, with its decimal places; the quantities core/law/quantities.yaml's."""
    sys.path.insert(0, ROOT)
    from core.check import garden_law
    L = garden_law(ROOT)
    units = {}
    for code, r in L.units.items():
        f = r.get('factor')
        units[code] = {'unit': code, 'name': r.get('name'), 'quantity': r.get('quantity'),
                       'factor': [int(f[0]), int(f[1])] if isinstance(f, list) and len(f) == 2
                       and all(str(x).isdigit() for x in f) else None, 'per': r.get('per')}
    quantities = {n: dict(q) for n, q in L.std.quantities.items()}
    for qn, q in quantities.items():
        uf = q.get('units_from') if isinstance(q.get('units_from'), dict) else None
        if not uf:
            continue
        for code, name in L.std.currencies.items():
            units.setdefault(code, {'unit': code, 'name': name, 'quantity': qn, 'from_registry': uf.get('registry')})
        files = {r.get('registry'): r.get('file') for r in L.std.tables.get('registry_files') or [] if isinstance(r, dict)}
        if uf.get('digits') and files.get(uf.get('registry')):
            with open(os.path.join(ROOT if os.path.isfile(os.path.join(ROOT, files[uf['registry']])) else
                                   os.path.dirname(os.path.dirname(os.path.abspath(__file__))), files[uf['registry']]),
                      encoding='utf-8') as fh:
                head = fh.readline().rstrip('\n').split('\t')
                for line in fh:
                    row = dict(zip(head, line.rstrip('\n').split('\t')))
                    if row.get(uf.get('take')) in units:
                        units[row[uf['take']]]['digits'] = row.get(uf['digits'])
    return units, quantities


def named(n, units):
    """The unit `n` names: a code of the law, or — in a garden of the core — the English name the law attaches to one."""
    if n in units:
        return n
    return next((c for c, r in units.items() if r.get('name') == n and not r.get('from_registry')), n)


def canonical(q, law=None):
    """A measured value `{count, unit}` as ONE value, however it was written (D17): (its quantity, its value in that
    quantity's coherent unit — the unit whose factor is one — as an exact Fraction, that unit's name). A unit with no
    factor, a currency, is its own: two currencies are never one value. `law` is (units, quantities) where the caller
    holds the law already (the merge does); otherwise it is read as `convert` reads it. ValueError for a unit the law
    does not declare, or a count that is not read exactly. A COMPARISON, never a record: the bean keeps what was
    written."""
    units, _quantities = law or _law()
    if not isinstance(q, dict) or not isinstance(q.get('unit'), str) or q['unit'] not in units:
        raise ValueError(f"{q!r} is not a measured value in a unit the law declares")
    u = units[q['unit']]
    x = q['count'] if isinstance(q.get('count'), Fraction) else exact(q.get('count'))
    if x is None:
        raise ValueError(f"{q.get('count')!r}: a count is a whole number or a decimal written as a string")
    f = u.get('factor')
    if u.get('from_registry') or not (isinstance(f, list) and len(f) == 2):
        return u['quantity'], x, q['unit']
    coherent = sorted(n for n, r in units.items() if r.get('quantity') == u['quantity'] and r.get('factor') == [1, 1])
    if not coherent:
        return u['quantity'], x, q['unit']
    return u['quantity'], x * Fraction(f[0], f[1]), coherent[0]


RATE_REFUSED = "a rate is a fact someone observed: pass the one you observed, and record it with its source"


def convert(count, unit, to, rate=None):
    units, quantities = _law()                  # read, never changed: no copy, so a round trip of every pair stays fast
    unit, to = named(unit, units), named(to, units)
    for n in (unit, to):
        if n not in units:
            raise ValueError(f"'{n}' is not a unit the law declares")
    if not isinstance(count, Fraction) and exact(count) is None:
        raise ValueError(f"{count!r}: a count is a whole number or a decimal written as a string — a float has already lost what it lost")
    a, b = units[unit], units[to]
    if a['quantity'] != b['quantity']:
        raise ValueError(f"{unit} measures {a['quantity']} and {to} measures {b['quantity']}: nothing converts one into the other")
    x = count if isinstance(count, Fraction) else exact(count)
    # A UNIT OF A CURRENCY (`per`: the toman, ten rials) is counted against that currency: carried into it, then on
    if a.get('per') or b.get('per'):
        base_a, base_b = a.get('per') or unit, b.get('per') or to
        fa = Fraction(*a['factor']) if a.get('per') else Fraction(1)
        fb = Fraction(*b['factor']) if b.get('per') else Fraction(1)
        if base_a == base_b:
            if rate is not None:
                raise ValueError(f"{unit} and {to} are one currency ({base_a}): a rate joins two")
            return x * fa / fb
        return convert(x * fa, base_a, base_b, rate) / fb
    if not a.get('from_registry'):
        if not (a.get('factor') and b.get('factor')):
            if unit == to:
                return x
            raise ValueError(f"{unit if not a.get('factor') else to} has no factor in the law: it converts only through "
                             f"what defines it (π, a reference, a level's own reference)")
        if rate is not None:
            raise ValueError(f"{a['quantity']} has factors in the law, and a rate would override them: drop --rate")
        return x * Fraction(*a['factor']) / Fraction(*b['factor'])
    # MONEY. A recorded count carries at most its currency's decimal places, as the gate holds it; a computed Fraction
    # is a reading and is taken as it is.
    d = a.get('digits')
    if not isinstance(count, Fraction) and str(d).isdigit() and '.' in str(count) and len(str(count).split('.', 1)[1]) > int(d):
        raise ValueError(f"'{count}' has more decimal places than {unit}'s {d}: a fraction of the smallest unit in use is not an amount anyone paid")
    if unit == to:
        if rate is not None:
            raise ValueError(f"{unit} to {to} is one currency: a rate joins two")
        return x
    if rate is None:
        q = quantities.get(a['quantity']) or {}
        raise ValueError(f"{unit} and {to} are two currencies, and no factor joins them (the law: `crosswalk: "
                         f"{q.get('crosswalk')}`) — {RATE_REFUSED}: --rate <units of {to} per 1 {unit}>")
    if isinstance(rate, Fraction):
        r = rate
    elif exact(rate) is None:
        raise ValueError(f"--rate {rate!r}: a rate is a decimal written as it was observed, `0.9173` — not a float, "
                         f"an exponent or a fraction")
    else:
        r = exact(rate)                         # a sign is read, so a negative rate is refused below for what it is
    if r <= 0:
        raise ValueError(f"--rate {rate}: a rate between two currencies is positive")
    return x * r


def show(x):
    """The value EXACTLY: as a decimal when it terminates, as a fraction of whole numbers when it does not. Never through
    a float — a float has 53 bits, and a conversion that silently drops the rest is an error nobody is told about."""
    n, d = x.numerator, x.denominator
    if d == 1:
        return str(n)
    k, r = 0, d
    for p in (2, 5):
        while r % p == 0:
            r //= p
    if r != 1:
        return f"{n}/{d}"                      # does not terminate: say so exactly rather than round it
    while (10 ** k) % d:
        k += 1
    digits = str(abs(n) * (10 ** k) // d).rjust(k + 1, '0')
    return ('-' if n < 0 else '') + digits[:-k] + '.' + digits[-k:].rstrip('0')


def approx(x, digits=6):
    """For a READER, beside the exact value and never instead of it: the value to `digits` significant digits, or None
    when the exact form is already that short. Computed in decimal arithmetic, so it is correctly rounded at any size.
    Always shown marked `≈`, which no count may contain — so a rounded number cannot be copied back into a record."""
    exact = show(x)
    if '/' not in exact and len(exact.lstrip('-').replace('.', '').strip('0')) <= digits:
        return None
    with decimal.localcontext() as c:
        c.prec = digits
        return format((decimal.Decimal(x.numerator) / decimal.Decimal(x.denominator)).normalize(), 'f')


# ------------------------------------------------------------------------------------------------ a standard's codes
# ONE TARGET A ROW, one row a code (registries.yaml `units_crosswalk_form`): a unit, a kind, a line, a system's positions
# (`in` alone) or its cells (`in` with `level`), a shape. A row with none crosses to nothing, and says why.
TARGETS = ('unit', 'quantity', 'line', 'in', 'shape')


@functools.lru_cache(maxsize=1)
def _crossings():
    """{scheme: {(axis, code): row}} — every scheme of the law and of the garden that names a `units` registry, each row
    as its file writes it, empty columns left out — and {scheme: why it cannot be read}."""
    K = _garden_law().std.knowledge
    out, unread = {}, {}
    for name, row in sorted(K.schemes.items()):
        reg = row.get('units') if isinstance(row, dict) else None
        if not reg:
            continue
        try:
            rows = K.rows(str(reg))
        except (KeyError, OSError) as e:
            unread[name] = f"its crossing {reg} cannot be read here: {e}"
            continue
        out[name] = {(r.get('axis') or '', str(r.get('code') or '')): {k: v for k, v in r.items() if v not in (None, '')}
                     for r in rows}
    return out, unread


def crossing(scheme):
    """{(axis, code): row} of `scheme`'s crossing into the law's units and kinds; ValueError where it has none."""
    rows, unread = _crossings()
    if scheme in rows:
        return rows[scheme]
    raise ValueError(unread.get(scheme) or f"{scheme!r} is no scheme whose codes cross into the law's units "
                                           f"(`units` on its row): one of {', '.join(sorted(rows)) or 'none'}")


def target(row):
    """The target a row crosses to, as {column: value}; {} where it crosses to nothing."""
    return {k: row[k] for k in TARGETS + ('level',) if row.get(k)}


def cross(scheme, code, axis=''):
    """(the row `code` of `scheme` crosses by, the decimals its own digit says, or None). A code of a family written with
    `n` for its last digit (`decimals: n`) is found by that family. ValueError where no row crosses it, or its row crosses
    to nothing — saying why."""
    rows = crossing(scheme)
    row, places = rows.get((axis or '', str(code))), None
    if row is None and str(code)[-1:].isdigit():
        fam = rows.get((axis or '', str(code)[:-1] + 'n'))
        if fam is not None and fam.get('decimals') == 'n':
            row, places = fam, int(str(code)[-1])
    if row is None:
        raise ValueError(f"{scheme}:{code} crosses into none of the law's units and kinds: no row of its crossing names "
                         f"it{' on the axis ' + axis if axis else ''}")
    if not target(row):
        raise ValueError(f"{scheme}:{code} crosses to nothing in the law"
                         + (f" (vacant: {row['vacant']})" if row.get('vacant') else '') + f" — {row.get('why', '')}")
    return row, places


def _line_of(system, L):
    """The one line whose positions `system` writes (measures.yaml `lines`, by the system's dimension)."""
    dim = (L.systems.get(system) or {}).get('dimension')
    found = [str(r['line']) for r in L.measure_law.get('lines') or [] if isinstance(r, dict) and r.get('systems') == dim]
    if len(found) != 1:
        raise ValueError(f"{system} positions in {dim}, which {len(found)} lines of the law hold: no one line is its")
    return found[0]


def position_tag(row):
    """What a system writes before a count to make a position of it — `C:` for celsius-scale — read from its own example
    (`C:36.4`): a word, a colon and a count; None where its example is not that (a calendar's moment, a potential with
    its ground). What it makes is held to the system's own pattern by its
    reader, frame.read."""
    tag, _, n = str((row or {}).get('example') or '').rpartition(':')
    try:
        return tag + ':' if re.fullmatch(r'[A-Za-z][A-Za-z0-9-]*', tag) and exact(n) is not None else None
    except ValueError:
        return None


def _tag(system, L):
    """`position_tag` of `system`; ValueError where it writes no position from a count."""
    tag = position_tag(L.systems.get(system))
    if tag is None:
        raise ValueError(f"{system} writes no position from a count (its example is "
                         f"{(L.systems.get(system) or {}).get('example')!r})")
    return tag


@functools.lru_cache(maxsize=1)
def _garden_law():
    """The law of the garden (or the release) this tool is in, its own rows beside the core's: read once per process."""
    sys.path.insert(0, ROOT)
    from core.check import garden_law
    return garden_law(ROOT)


def read(scheme, count, code, axis=''):
    """A count written with `code` of `scheme`, as the law writes it: `{count, unit}` for a unit; `{of, in, level, count}`,
    an extent's, for a calendar's cells; the position's text for a system's unit of position. A code whose family says
    its decimals (`decimals: n`) takes its count written without a point, and puts the point where its digit says.
    ValueError for a code that names a kind, a line or a shape (it says what is measured, never in what unit), one that
    crosses to nothing, and a count not written as one."""
    row, places = cross(scheme, code, axis)
    t = target(row)
    count = str(count)
    if places is not None:
        if not re.fullmatch(r'[0-9]+', count, re.ASCII):
            raise ValueError(f"{scheme}:{code} takes its value as digits without a point, and {count!r} is not")
        digits = count.lstrip('0').rjust(places + 1, '0')
        count = digits[:len(digits) - places] + ('.' + digits[-places:] if places else '')
    elif exact(count) is None:
        raise ValueError(f"{count!r}: a count is a whole number or a decimal written as a string")
    if 'unit' in t:
        return {'count': count, 'unit': t['unit']}
    if 'in' in t:
        L = _garden_law()
        if 'level' in t:
            if not re.fullmatch(r'[1-9][0-9]*', count, re.ASCII):
                raise ValueError(f"{scheme}:{code} counts the cells of {t['in']}'s {t['level']}, and {count!r} is no "
                                 f"positive whole number of them")
            return {'of': _line_of(t['in'], L), 'in': t['in'], 'level': t['level'], 'count': count}
        text = _tag(t['in'], L) + count
        from core import frame
        try:
            if frame.read(text, L.systems).system == t['in']:
                return text
        except frame.Refused:
            pass
        raise ValueError(f"{scheme}:{code} is a unit of position of {t['in']}, and {text!r} is no position of it")
    kind = next(iter(t.items()))
    raise ValueError(f"{scheme}:{code} names what is measured ({kind[0]} {kind[1]}), and not the unit a count is in: "
                     f"read its value with the unit that comes with it")


def code_of(scheme, want, axis=''):
    """The code of `scheme` the law's `want` is written back with — `want` a target, {unit: …}, {quantity: …},
    {line: …}, {in: …, level?: …}, {shape: …}: the one row crossing to it, or of several the one marked `back`.
    ValueError where none does, saying which codes cross to it."""
    rows = [(c, r) for (a, c), r in crossing(scheme).items() if a == (axis or '') and target(r) == want]
    if len(rows) > 1:
        rows = [(c, r) for c, r in rows if r.get('back') == 'true'] or rows
    if len(rows) != 1:
        shown = ', '.join(f"{k}: {v}" for k, v in want.items())
        raise ValueError(f"no code of {scheme} crosses from {shown}" if not rows else
                         f"{len(rows)} codes of {scheme} cross from {shown}, and none is marked `back`")
    return rows[0]


def write(scheme, value, axis=''):
    """(count, code): the law's `value` — `{count, unit}`, an extent's `{in, level, count}`, a position — written with the
    code of `scheme` that crosses to it. A family that says its decimals (`decimals: n`) is written with the digit of the
    value's own places, and the value without its point. ValueError where no code crosses to it."""
    if isinstance(value, dict) and 'unit' in value:
        count = str(value.get('count'))
        if exact(count) is None:
            raise ValueError(f"{count!r}: a count is a whole number or a decimal written as a string")
        code, row = code_of(scheme, {'unit': str(value['unit'])}, axis)
        if row.get('decimals') == 'n':
            whole, _, frac = count.partition('.')
            if whole.startswith('-') or len(frac) > 9:
                raise ValueError(f"{count} {value['unit']}: {scheme}:{code} writes an unsigned value with at most nine "
                                 f"places")
            return (whole + frac).lstrip('0') or '0', code[:-1] + str(len(frac))
        return count, code
    if isinstance(value, dict) and value.get('level'):
        return str(value.get('count')), code_of(scheme, {'in': str(value.get('in')), 'level': str(value['level'])}, axis)[0]
    if isinstance(value, str):
        L = _garden_law()
        sys.path.insert(0, ROOT)
        from core import frame
        try:
            p = frame.read(value, L.systems)
        except frame.Refused as e:
            raise ValueError(f"{value!r}: {e}") from None
        tag = _tag(p.system, L)
        if not value.startswith(tag):
            raise ValueError(f"{value!r} is a position of {p.system}, not written from a count")
        return value[len(tag):], code_of(scheme, {'in': p.system}, axis)[0]
    raise ValueError(f"{value!r} is no value of the law a code is written for: a quantity, an extent of cells, a position")


def through(scheme, code):
    """{axis: (the value its row writes on the axis, the target it crosses to, why)}: what `code` of `scheme` says, read
    through the values the scheme's own row for it writes on each axis its crossing names (LOINC's `property` and
    `scale`). A value whose row crosses to nothing gives an empty target and its row's why. The row is read from the
    scheme's own table, as bin/knowledge.py reads it — this machine's fetched copy, or the garden's extract. ValueError
    where the crossing names no axis, the table cannot be read here, the code is none of it, or a value on an axis is
    one no row names."""
    rows = crossing(scheme)
    axes = sorted({a for a, _c in rows if a})
    if not axes:
        raise ValueError(f"{scheme}'s crossing names no axis: each of its codes crosses by its own row")
    try:
        row = _garden_law().std.knowledge.row(scheme, code)
    except (KeyError, OSError) as e:
        raise ValueError(f"{scheme}'s own table cannot be read here: {e.args[0] if e.args else e}") from None
    if row is None:
        raise ValueError(f"{code!r} is no code of {scheme}")
    out = {}
    for a in axes:
        v = str(row.get(a) or '')
        r = rows.get((a, v))
        if r is None:
            raise ValueError(f"{scheme}:{code} writes {v!r} on its axis {a}, and no row of its crossing names it")
        out[a] = (v, target(r), r.get('why', ''))
    return out


def judge(scheme, code, value):
    """'' when `value` is what `code` of `scheme` says a value of it is — read through its axes where its crossing names
    them, else by its own row: a quantity of the kind it crosses to (or of a kind written in that kind's units), a
    position on the line, a value of the shape — else why not. ValueError where the code says nothing the law reads."""
    L = _garden_law()
    from core.measures import quantity_why, unit_row     # the gate's own judges of a quantity (they import this module)
    if any(a for a, _c in crossing(scheme)):
        said = {a: (v, t) for a, (v, t, _w) in through(scheme, code).items() if t}
        if not said:
            raise ValueError(f"{scheme}:{code} says nothing the law reads: " + '; '.join(
                f"its {a} {v} — {w}" for a, (v, _t, w) in through(scheme, code).items()))
    else:
        said = {'': (code, target(cross(scheme, code)[0]))}
    # A LINE WINS: read through axes, a line named on one makes the value a position on it, and a quantity or a kind
    # named on another says what is placed there — a temperature read as a number, a concentration read as 1+, 2+
    on_line = any('line' in t for _v, t in said.values())
    for axis, (v, t) in said.items():
        on = f"{scheme}:{code}" + (f" (its {axis} {v})" if axis else '')
        if on_line and axis and ('quantity' in t or t.get('shape') == 'quantity'):
            continue
        if 'unit' in t or 'quantity' in t or t.get('shape') == 'quantity':
            if not (isinstance(value, dict) and 'unit' in value) or quantity_why(L, value):
                return f"{on} is a quantity, and {value!r} is none: {quantity_why(L, value) or 'no unit'}"
            if 'unit' in t and str(value['unit']) != t['unit']:
                return f"{on} is written in {t['unit']}, and {value['unit']} is another unit"
            if 'quantity' in t:
                q = (unit_row(L, value['unit']) or {}).get('quantity')
                kinds = {t['quantity'], str((L.std.quantities.get(t['quantity']) or {}).get('units_of') or '')}
                if q not in kinds:
                    return f"{on} is a {t['quantity']}, and {value['unit']} measures {q}"
        elif 'line' in t or 'in' in t or t.get('shape') == 'position':
            if 'level' in t:
                if not (isinstance(value, dict) and value.get('in') == t['in'] and value.get('level') == t['level']):
                    return f"{on} counts the cells of {t['in']}'s {t['level']}, and {value!r} is no extent of them"
                continue
            sys.path.insert(0, ROOT)
            from core import frame
            try:
                p = frame.read(str(value), L.systems) if isinstance(value, str) else None
            except frame.Refused:
                p = None
            if p is None:
                return f"{on} is a position, and {value!r} is none"
            if 'in' in t and p.system != t['in']:
                return f"{on} is a position of {t['in']}, and {value!r} is one of {p.system}"
            if 'line' in t:
                dim = (L.systems.get(p.system) or {}).get('dimension')
                holds = {str(r.get('line')): r.get('systems') for r in L.measure_law.get('lines') or [] if isinstance(r, dict)}
                if holds.get(t['line']) not in (dim, 'any'):
                    return f"{on} is a position on the line {t['line']}, and {value!r} is one in {dim}"
        elif t.get('shape') == 'row':
            if not (isinstance(value, str) and dmparse.split_coding(value)[0]):
                return f"{on} is a code, `<scheme>:<code>`, and {value!r} is none"
        elif t.get('shape') == 'text':
            if not isinstance(value, str):
                return f"{on} is text, and {value!r} is none"
    return ''


def against(scheme, rows):
    """What a provider's table, read (`rows`, each with its `code` and the provider's `status` where it states one), says
    of `scheme`'s crossing: (how many of its codes cross, [crossed codes the table has not], [(crossed code, status)],
    {axis: [values its rows write on the axis that no row of the crossing names]})."""
    have = {str(r.get('code')): str(r.get('status') or '') for r in rows}
    crossing_rows = crossing(scheme)
    mine = {c: r for (a, c), r in crossing_rows.items() if not a and target(r)}
    fam = {c[:-1] for c, r in mine.items() if r.get('decimals') == 'n'}
    missing = [c for c in mine if c not in have and not (c[:-1] in fam and any(h[:-1] == c[:-1] for h in have))]
    marked = [(c, have[c]) for c in mine if have.get(c) in ('deprecated', 'deleted')]
    axes = sorted({a for a, _c in crossing_rows if a})
    unknown = {a: sorted({str(r.get(a) or '') for r in rows} - {c for (x, c) in crossing_rows if x == a} - {''})
               for a in axes}
    n = len([c for c in have if c in mine or c[:-1] in fam]) if not axes else \
        len([r for r in rows if all(target(crossing_rows.get((a, str(r.get(a) or '')), {})) for a in axes)])
    return n, sorted(missing), sorted(marked), {a: v for a, v in unknown.items() if v}


def speakable(text, stream=None):
    """`text` as `stream` can print it. A pipe on Windows is written in the ANSI code page, which has no `≈`: printing
    one there raised, and a tool that dies on a glyph dies exactly when an agent reads it through a pipe. So the mark is
    an ASCII `~` wherever the stream cannot carry it, and nothing else about the text changes."""
    enc = getattr(stream or sys.stdout, 'encoding', None) or 'utf-8'
    try:
        text.encode(enc)
        return text
    except (UnicodeEncodeError, LookupError):
        return text.replace('≈', '~').encode(enc, 'replace').decode(enc, 'replace')


def _coded(text):
    """(scheme, code) where `text` is a code of a scheme whose codes cross into the law's units, else None."""
    scheme, code = dmparse.split_coding(text)
    return (scheme, code) if scheme in _crossings()[0] or scheme in _crossings()[1] else None


def _shown(value):
    if isinstance(value, dict) and 'unit' in value:
        return f"{value['count']} {value['unit']}"
    if isinstance(value, dict):
        return (f"{value['count']} cells of {value['in']}'s {value['level']} — an extent, never a duration: "
                f"{{ of: {value['of']}, in: {value['in']}, level: {value['level']}, count: \"{value['count']}\" }}")
    return str(value)


def _crossed(argv, coded, rate, digits):
    """A count written with a standard's code, read as the law's (and converted, given a unit); or the law's value
    written back with a scheme's code."""
    try:
        if coded:
            value = read(coded[0], argv[0], coded[1])
            if len(argv) == 2:
                print(speakable(_shown(value)))
                return 0
            if not (isinstance(value, dict) and 'unit' in value):
                raise ValueError(f"{argv[1]} is read as {_shown(value)}: only a quantity converts into another unit")
            if argv[2] in _crossings()[0]:
                count, code = write(argv[2], value)
                print(speakable(f"{count} {argv[2]}:{code}"))
                return 0
            return main([value['count'], value['unit'], argv[2]] + (['--rate', rate] if rate is not None else [])
                        + ['--digits', str(digits)])
        unit = named(argv[1], _law()[0])
        count, code = write(argv[2], {'count': argv[0], 'unit': unit})
        print(speakable(f"{count} {argv[2]}:{code}"))
        return 0
    except ValueError as e:
        print(speakable(f"units: {e}")); return 1


def _code(text):
    """What one code crosses to: by its own row, or through the values it writes on its crossing's axes."""
    scheme, code = dmparse.split_coding(text) if ':' in text else (None, None)
    try:
        if not scheme:
            raise ValueError(f"{text!r} is no code written with its scheme, `<scheme>:<code>`")
        rows = crossing(scheme)
        if any(a for a, _c in rows):
            for axis, (v, t, why) in through(scheme, code).items():
                print(speakable(f"{axis} {v}: " + (', '.join(f"{k}: {x}" for k, x in t.items()) if t else 'nothing')
                                + (f" — {why}" if why else '')))
            return 0
        row, places = cross(scheme, code)
        print(speakable(', '.join(f"{k}: {x}" for k, x in target(row).items())
                        + (f" — its count written without a point, {places} digits after it" if places is not None else '')
                        + (f" — {row['why']}" if row.get('why') else '')))
        return 0
    except ValueError as e:
        print(speakable(f"units: {e}")); return 1


def _judge(text, value):
    """Whether a value — `<count> <unit>`, or a position — is what a code says a value of it is."""
    scheme, code = dmparse.split_coding(text) if ':' in text else (None, None)
    v = {'count': value[0], 'unit': named(value[1], _law()[0])} if len(value) == 2 else value[0]
    try:
        if not scheme:
            raise ValueError(f"{text!r} is no code written with its scheme, `<scheme>:<code>`")
        why = judge(scheme, code, v)
    except ValueError as e:
        print(speakable(f"units: {e}")); return 1
    shown = _shown(v) if isinstance(v, dict) else v
    unread = [f"its {a} {x} — {w}" for a, (x, tg, w) in (through(scheme, code).items()
                                                          if any(a for a, _c in crossing(scheme)) else []) if not tg]
    print(speakable(f"units: {shown} is not what {text} says: {why}" if why else
                    f"{shown} is what {text} says" + (", as far as the law reads it; not read: " + '; '.join(unread)
                                                     if unread else '')))
    return 1 if why else 0


def _codes(scheme):
    """Every row of `scheme`'s crossing: each code and what it crosses to, or why it crosses to nothing."""
    try:
        rows = crossing(scheme)
    except ValueError as e:
        print(speakable(f"units: {e}")); return 1
    for (axis, code), row in sorted(rows.items()):
        t = target(row)
        what = ', '.join(f"{k}: {v}" for k, v in t.items()) if t else \
            'nothing' + (f" (vacant: {row['vacant']})" if row.get('vacant') else '')
        extra = (' — written back' if row.get('back') == 'true' else '') + \
                (f" — its digit n the decimal places" if row.get('decimals') == 'n' else '')
        print(speakable(f"{(axis + ':') if axis else ''}{code}\t{what}{extra}" + (f"\t{row['why']}" if row.get('why') else '')))
    print(f"units: {len(rows)} codes of {scheme}, {sum(1 for r in rows.values() if target(r))} crossed into the law")
    return 0


def main(argv):
    digits, rate = 6, None
    if '--digits' in argv:
        i = argv.index('--digits'); d = argv[i + 1] if i + 1 < len(argv) else ''; argv = argv[:i] + argv[i + 2:]
        if not (d.isascii() and d.isdigit() and 1 <= int(d) <= 1000):
            print(speakable(f"units: --digits {d!r}: the rounded reading is given to a whole number of significant "
                            f"digits, 1 to 1000 — e.g. --digits 6")); return 2
        digits = int(d)
    if '--rate' in argv:
        i = argv.index('--rate'); rate = argv[i + 1] if i + 1 < len(argv) else ''; argv = argv[:i] + argv[i + 2:]
    if argv[:1] == ['--codes'] and len(argv) == 2:
        return _codes(argv[1])
    if argv[:1] == ['--code'] and len(argv) == 2:
        return _code(argv[1])
    if argv[:1] == ['--judge'] and len(argv) in (3, 4):
        return _judge(argv[1], argv[2:])
    coded = len(argv) in (2, 3) and _coded(argv[1])
    if coded or (len(argv) == 3 and argv[2] in _crossings()[0]):
        return _crossed(argv, coded, rate, digits)
    if len(argv) != 3:
        # the interpreter as it is named where this runs: `python3` may be the Microsoft Store's alias on Windows
        print(speakable(__doc__.replace('python3 bin/', ('python' if os.name == 'nt' else 'python3') + ' bin/')))
        return 0 if not argv or argv[0] in ('-h', '--help') else 2
    try:
        x = convert(argv[0], argv[1], argv[2], rate); a = approx(x, digits)
        print(speakable(show(x) + ' ' + argv[2] + (f"   (≈ {a})" if a else "")))
        d = _law()[0][named(argv[2], _law()[0])].get('digits')
        if rate is not None and str(d).isdigit() and (x * 10 ** int(d)).denominator != 1:
            print(f"   a reading at the rate given: {argv[2]} is written with {d} places, and who takes the remainder is a clause")
        return 0
    except ValueError as e:
        print(speakable(f"units: {e}")); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
