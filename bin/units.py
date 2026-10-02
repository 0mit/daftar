#!/usr/bin/env python3
"""units — a measured value, converted WITHIN its quantity, exactly.

    python3 bin/units.py 90 kilometre-per-hour metre-per-second      # -> 25
    python3 bin/units.py 1.5 hectare square-metre                    # -> 15000
    python3 bin/units.py 3 decibel-per-kilometre decibel-per-metre   # -> 0.003
    python3 bin/units.py 100 XTS EUR --rate 0.9173                   # -> 91.73: two currencies meet only at a rate

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
                       and all(str(x).isdigit() for x in f) else None}
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
    if not a.get('from_registry'):
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
