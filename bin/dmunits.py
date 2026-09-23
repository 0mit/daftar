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
import copy, decimal, functools, os, re, sys
from fractions import Fraction
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml, dmparse

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
    # IN A GARDEN, THE LAW IS WHAT THE GATE LOADED: the standard, the garden's overlays, and every row it added under
    # `registry_additions` — a currency among them. Reading the seed files instead made a currency the gate accepted
    # one this tool called undeclared: two readers of one law, disagreeing. Only the standard's own repository, which
    # has no VOCAB.md, is read from the standard alone — there the standard IS the law. No fallback from the first
    # to the second: a garden whose law cannot be loaded is an error, not a reason to read another law.
    if os.path.exists(os.path.join(ROOT, 'VOCAB.md')):
        import dmcheck
        return dict(dmcheck.UNITS), dict(dmcheck.QUANTITIES)
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
    units, quantities = _law()                  # read, never changed: no copy, so a round trip of every pair stays fast
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
            print(speakable(f"dmunits: --digits {d!r}: the rounded reading is given to a whole number of significant "
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
        d = _law()[0][argv[2]].get('digits')
        if rate is not None and str(d).isdigit() and (x * 10 ** int(d)).denominator != 1:
            print(f"   a reading at the rate given: {argv[2]} is written with {d} places, and who takes the remainder is a clause")
        return 0
    except ValueError as e:
        print(speakable(f"dmunits: {e}")); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
