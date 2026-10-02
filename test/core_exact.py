#!/usr/bin/env python3
"""A count is exact everywhere it is read (v1 part 12: what test/money.py held of it, ported to the core).

Money's promise was that an amount is a count, exact, in one currency, and that what is owed is read from what moved,
never stored and never rounded. In a garden of the core the gate holds an amount's form (test/refusals.py: a count in
plain decimal digits, at most forty a side; test/core.py's cases: no more decimal places than its currency has), and
test/core_read.py the ledger's reading of `pay` and `bear`, exactly. This holds the rest, which no garden is needed for:

  rates     two currencies meet only at a rate someone observed: bin/units.py refuses a conversion without one, and with
            one the result is exact — at thirty digits times a rate of thirty places; a rate written as a float, an
            exponent or a fraction, a negative one, and one where the law holds a factor are refused
  the source  no float anywhere a count is read: bin/ledger.py holds no float, no float literal, no true division and no
            rounding; bin/units.py and the core's code that reads, sums or compares a count (core/measures.py,
            core/lines.py, core/merge.py, core/engine.py, core/standards.py, bin/stale.py) hold no float literal and call
            no float() — read with the tokenizer, so a `1.5` in a docstring is prose

Run: python3 test/core_exact.py   (0 = green; a second)
"""
import io
import os
import re
import sys
import tokenize
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmunits  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def refused(f):
    try:
        f()
    except ValueError:
        return True
    return False


# ---- TWO CURRENCIES MEET ONLY AT AN OBSERVED RATE
check("bin/units.py refuses 100 XTS to EUR without a rate: a rate is a fact someone observed",
      refused(lambda: dmunits.convert("100", "XTS", "EUR")))
check("...and with one the result is exact", dmunits.convert("100", "XTS", "EUR", "0.9173") == Fraction("91.73"))
big = "123456789012345678901234567890.12"
check("...exact at a size a float would ruin: thirty digits times a rate of thirty places",
      dmunits.convert(big, "XTS", "EUR", "1.000000000000000000000000000001")
      == Fraction(big) * Fraction("1.000000000000000000000000000001"))
check("...a rate written as a float, an exponent or a fraction is refused",
      refused(lambda: dmunits.convert("1", "XTS", "EUR", 0.9)) and refused(lambda: dmunits.convert("1", "XTS", "EUR", "9e-1"))
      and refused(lambda: dmunits.convert("1", "XTS", "EUR", "1/3")))
check("...a rate where the law holds a factor is refused: a metre is a thousand millimetres, not what someone saw",
      refused(lambda: dmunits.convert("1", "metre", "millimetre", "2")))
check("...a currency is not a length", refused(lambda: dmunits.convert("1", "XTS", "metre", "1")))
try:
    dmunits.convert("1", "XTS", "EUR", "-1")
    _neg = ""
except ValueError as e:
    _neg = str(e)
check("...and a negative rate is refused for what it is: a rate between two currencies is positive", "is positive" in _neg,
      _neg)


# ---- THE SOURCE: NO FLOAT ANYWHERE A COUNT IS READ
def floats_in(text, strict):
    """Float literals, `float(` calls — and, where `strict`, the division operator and any rounding at all. Read with the
    tokenizer, so a `1.5` in a docstring is prose and a `1.5` in code is not."""
    found, toks = [], [t for t in tokenize.generate_tokens(io.StringIO(text).readline)
                       if t.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT)]
    for i, t in enumerate(toks):
        nxt = toks[i + 1].string if i + 1 < len(toks) else ''
        if t.type == tokenize.NUMBER and not t.string.lower().startswith(("0x", "0o", "0b")) \
                and re.search(r"[.eEjJ]", t.string):
            found.append(f"line {t.start[0]}: float literal {t.string}")
        elif t.type == tokenize.NAME and t.string == "float" and (strict or nxt == "("):
            found.append(f"line {t.start[0]}: float")
        elif strict and t.type == tokenize.OP and t.string in ("/", "/="):
            found.append(f"line {t.start[0]}: true division")
        elif strict and t.type == tokenize.NAME and t.string in ("round", "math", "decimal"):
            found.append(f"line {t.start[0]}: {t.string}")
    return found


check("the scan finds what it looks for (a scan that finds nothing proves nothing)",
      len(floats_in("x = 0.5\ny = float('1')\nz = a / b\nw = round(z)\n", True)) == 4
      and len(floats_in("x = 0.5\ny = float('1')\nz = a / b\n", False)) == 2)


def source(rel):
    with open(os.path.join(ROOT, rel), encoding='utf-8') as fh:
        return fh.read()


led = floats_in(source('bin/ledger.py'), True)
check("bin/ledger.py holds no float literal, no float, no true division and no rounding", not led, led)
found = {rel: floats_in(source(rel), False) for rel in ('bin/units.py', 'core/measures.py', 'core/lines.py',
                                                        'core/merge.py', 'core/engine.py', 'core/standards.py',
                                                        'bin/stale.py')}
check("...and the core's code that reads, sums or compares a count holds no float literal and calls no float(): "
      + ", ".join(found), not any(found.values()), {k: v for k, v in found.items() if v})

print(f"\ncore_exact: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
