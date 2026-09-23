#!/usr/bin/env python3
"""dmunits — a measured value, converted WITHIN its quantity, exactly.

    python3 bin/dmunits.py 90 kilometre-per-hour metre-per-second      # -> 25
    python3 bin/dmunits.py 1.5 hectare square-metre                    # -> 15000
    python3 bin/dmunits.py 3 decibel-per-kilometre decibel-per-metre   # -> 0.003
    python3 bin/dmunits.py 100 XTS EUR --rate 0.9173                   # -> 91.73: two currencies meet only at a rate

A unit names the QUANTITY it measures and its FACTOR to that quantity's coherent unit, as a pair of whole numbers, so a
conversion is exact arithmetic and never a rounded float — and the result is PRINTED exactly too: a terminating decimal in
full, anything else as a fraction of whole numbers. Beside a fraction it prints a rounded decimal for the
reader, marked `≈` (`--digits N`, six by default) — an aid to the eye, which the gate would refuse as a count. A CONVERSION IS A READING, NEVER A RECORD: a bean keeps a value in the
unit it was measured in, and every conversion starts from that, so errors cannot accumulate through a chain of them. It converts within one quantity and REFUSES across two: a speed
is not an acceleration however the numbers line up. Everything it knows is read from `seed/std-vocab.md`.

MONEY (std-vocab 21.0). A currency is a unit of the `money` quantity, and the currencies are the rows of a registry the
law points at (`units_from`), each with the decimal places it is written in. NO FACTOR JOINS TWO OF THEM — the quantity
says `crosswalk: observed` — so a conversion between two currencies is REFUSED unless it is given the rate someone
observed (`--rate R`: units of the target per one of the source, a decimal string). With it the result is exact, and it
is a reading at that rate, never a record: the rate is a fact with a source and a day, and belongs in the ledger as one.
"""
import decimal, functools, os, re, sys
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml, dmparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def law():
    """(units, quantities) as the law declares them — a fresh pair of tables over one parse of it."""
    units, quantities = _law()
    return dict(units), dict(quantities)


@functools.lru_cache(maxsize=1)
def _law():
    # ONE PARSE PER PROCESS. Every conversion asked for the law, and the law was parsed from its YAML each time: the
    # round trip of every pair of units in test/quantities.py spent two and a half minutes re-reading one file.
    fm = yaml.safe_load(dmparse.split_front_matter(open(os.path.join(ROOT, 'seed', 'std-vocab.md'), encoding='utf-8').read())[0])
    units = {u['unit']: u for u in fm.get('units') or []}
    quantities = {q['quantity']: q for q in fm.get('quantities') or []}
    # A QUANTITY WHOSE UNITS ARE A REGISTRY'S ROWS: each row is a unit with NO factor, carrying its decimal places —
    # read exactly as the gate reads it, from the file the law's `registry_files` names.
    files = {r.get('registry'): r.get('file') for r in fm.get('registry_files') or [] if isinstance(r, dict)}
    for qn, q in quantities.items():
        uf = q.get('units_from') if isinstance(q.get('units_from'), dict) else None
        if not uf or not files.get(uf.get('registry')):
            continue
        with open(os.path.join(ROOT, files[uf['registry']]), encoding='utf-8') as fh:
            head = fh.readline().rstrip('\n').split('\t')
            for line in fh:
                row = dict(zip(head, line.rstrip('\n').split('\t')))
                if row.get(uf.get('take')) and row[uf['take']] not in units:
                    units[row[uf['take']]] = {'unit': row[uf['take']], 'quantity': qn, 'from_registry': uf['registry'],
                                              'digits': row.get(uf.get('digits')) if uf.get('digits') else None}
    return units, quantities


RATE_REFUSED = "a rate is a fact someone observed: pass the one you observed, and record it with its source"


def convert(count, unit, to, rate=None):
    units, quantities = law()
    for n in (unit, to):
        if n not in units:
            raise ValueError(f"'{n}' is not a unit the law declares")
    if not isinstance(count, Fraction) and (isinstance(count, (float, bool)) or not re.match(r'^-?[0-9]+(\.[0-9]+)?$', str(count))):
        raise ValueError(f"{count!r}: a count is a whole number or a decimal written as a string — a float has already lost what it lost")
    a, b = units[unit], units[to]
    if a['quantity'] != b['quantity']:
        raise ValueError(f"{unit} measures {a['quantity']} and {to} measures {b['quantity']}: nothing converts one into the other")
    x = count if isinstance(count, Fraction) else Fraction(str(count))
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
    elif isinstance(rate, (float, bool)) or not re.match(r'^[0-9]+(\.[0-9]+)?$', str(rate)):
        raise ValueError(f"--rate {rate!r}: a rate is a decimal written as it was observed, `0.9173` — not a float, "
                         f"an exponent or a fraction")
    else:
        r = Fraction(str(rate))
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


def main(argv):
    digits, rate = 6, None
    if '--digits' in argv:
        i = argv.index('--digits'); digits = int(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    if '--rate' in argv:
        i = argv.index('--rate'); rate = argv[i + 1] if i + 1 < len(argv) else ''; argv = argv[:i] + argv[i + 2:]
    if len(argv) != 3:
        print(__doc__); return 0 if not argv else 2
    try:
        x = convert(argv[0], argv[1], argv[2], rate); a = approx(x, digits)
        print(show(x), argv[2] + (f"   (≈ {a})" if a else ""))
        d = law()[0][argv[2]].get('digits')
        if rate is not None and str(d).isdigit() and (x * 10 ** int(d)).denominator != 1:
            print(f"   a reading at the rate given: {argv[2]} is written with {d} places, and who takes the remainder is a clause")
        return 0
    except ValueError as e:
        print(f"dmunits: {e}"); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
