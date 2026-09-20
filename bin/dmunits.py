#!/usr/bin/env python3
"""dmunits — a measured value, converted WITHIN its quantity, exactly.

    python3 bin/dmunits.py 90 kilometre-per-hour metre-per-second      # -> 25
    python3 bin/dmunits.py 1.5 hectare square-metre                    # -> 15000
    python3 bin/dmunits.py 3 decibel-per-kilometre decibel-per-metre   # -> 0.003

A unit names the QUANTITY it measures and its FACTOR to that quantity's coherent unit, as a pair of whole numbers, so a
conversion is exact arithmetic and never a rounded float — and the result is PRINTED exactly too: a terminating decimal in
full, anything else as a fraction of whole numbers. Beside a fraction it prints a rounded decimal for the
reader, marked `≈` (`--digits N`, six by default) — an aid to the eye, which the gate would refuse as a count. A CONVERSION IS A READING, NEVER A RECORD: a bean keeps a value in the
unit it was measured in, and every conversion starts from that, so errors cannot accumulate through a chain of them. It converts within one quantity and REFUSES across two: a speed
is not an acceleration however the numbers line up. Everything it knows is read from `seed/std-vocab.md`.
"""
import decimal, os, re, sys
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml, dmparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def law():
    fm = yaml.safe_load(dmparse.split_front_matter(open(os.path.join(ROOT, 'seed', 'std-vocab.md'), encoding='utf-8').read())[0])
    return ({u['unit']: u for u in fm.get('units') or []}, {q['quantity']: q for q in fm.get('quantities') or []})


def convert(count, unit, to):
    units, _q = law()
    for n in (unit, to):
        if n not in units:
            raise ValueError(f"'{n}' is not a unit the law declares")
    if not isinstance(count, Fraction) and (isinstance(count, (float, bool)) or not re.match(r'^-?[0-9]+(\.[0-9]+)?$', str(count))):
        raise ValueError(f"{count!r}: a count is a whole number or a decimal written as a string — a float has already lost what it lost")
    a, b = units[unit], units[to]
    if a['quantity'] != b['quantity']:
        raise ValueError(f"{unit} measures {a['quantity']} and {to} measures {b['quantity']}: nothing converts one into the other")
    return (count if isinstance(count, Fraction) else Fraction(str(count))) * Fraction(*a['factor']) / Fraction(*b['factor'])


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
    digits = 6
    if '--digits' in argv:
        i = argv.index('--digits'); digits = int(argv[i + 1]); argv = argv[:i] + argv[i + 2:]
    if len(argv) != 3:
        print(__doc__); return 0 if not argv else 2
    try:
        x = convert(argv[0], argv[1], argv[2]); a = approx(x, digits)
        print(show(x), argv[2] + (f"   (≈ {a})" if a else "")); return 0
    except ValueError as e:
        print(f"dmunits: {e}"); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
