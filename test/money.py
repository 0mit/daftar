#!/usr/bin/env python3
"""Money (std-vocab 21.0): an amount is a count in one currency, exact; the parts of a whole add up to it exactly; what
is owed is READ from what moved (bin/dmledger.py), never stored; and two currencies meet only at a rate someone observed.

Every name here is neutral (sam, ali, ben) and every amount is in XTS — the code ISO 4217 keeps for testing — or in a
real currency only where the test is about that currency's decimal places or about crossing between two.
"""
import io, os, re, sys, subprocess, tempfile, shutil, tokenize, datetime
from fractions import Fraction
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmunits
import dmledger
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmmoney-"); G = os.path.join(T, "g")
r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "sam", cwd=ROOT)
check("a garden germinates, kept by sam", r.returncode == 0 and os.path.isfile(os.path.join(G, "beans", "sam.md")), r.stdout + r.stderr)

def person(bid):
    with open(os.path.join(G, "beans", bid + ".md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f'---\nbean: {bid}\nkind: person\ntitle: "{bid}"\nstatus: active\nsummary: "a person"\nnature: living\n'
                 f'owned_by: {{ legal: {{ crown: love }} }}\nresponsibility: {{ legal: {{ self: true }} }}\n'
                 f'identity: {{ status: confirmed, anchors: [ {{ key: person_id, value: "person:{bid}", class: logical, establishing: true }} ] }}\n'
                 f'provenance: {{ src: asserted-by-human, by: sam, as_of: 2026-09-01 }}\n---\n{bid}.\n')
person("ali"); person("ben")

def agreement(bid, transactions="", clauses="", parties=("sam", "ali")):
    """An agreement between parties, crowned (owned by none of them) and answered for by them, as 21.0 writes one."""
    body = "\n".join(f"  {p}: {{ who: {{ bean: {p} }}, accepted: 2026-09-01 }}" for p in parties)
    with open(os.path.join(G, "beans", bid + ".md"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"""---
bean: {bid}
kind: contract
title: "{bid}"
status: active
summary: "an agreement between {' and '.join(parties)}"
nature: metaphysical
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: contract_id, value: "contract:{bid}", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: sam, as_of: 2026-09-01 }}
parties:
{body}
words: {{ form: spoken, agreed: 2026-09-01 }}
""" + (f"transactions:\n{transactions}\n" if transactions else "") + (f"clauses:\n{clauses}\n" if clauses else "") + "---\nAn agreement.\n")

def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

def ledger(*a):
    r = run(sys.executable, os.path.join(G, "bin", "dmledger.py"), *a, cwd=G)
    return r.returncode, r.stdout + r.stderr

ok = lambda out: "0 error" in out
def one(tx):
    """A single transaction, as the only one of an agreement, judged by the gate."""
    agreement("deal", "  t: " + tx)
    return gate()

# ---------------------------------------------------------------- AN AMOUNT, AT THE GATE
out = one('{ what: "a test", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam } ] }')
check("the gate accepts an amount in XTS, the code kept for testing", ok(out), out[-600:])
out = one('{ what: "a meal", amount: { count: "12.50", unit: EUR }, paid_by: [ { party: sam } ] }')
check("...and in a real currency, as a decimal string within its places", ok(out), out[-600:])
out = one('{ what: "a meal", amount: { count: 12.5, unit: EUR }, paid_by: [ { party: sam } ] }')
check("a FLOAT is refused: a decimal is written as a string", "a float has no canonical form" in out, out[-600:])
out = one('{ what: "a meal", amount: { count: "12.505", unit: EUR }, paid_by: [ { party: sam } ] }')
check("MORE decimal places than the currency is written with is refused", "has 3 decimal places, and EUR is written with at most 2" in out, out[-600:])
out = one('{ what: "a meal", amount: { count: 1500, unit: JPY }, paid_by: [ { party: sam } ] }')
check("a whole number in a currency of NO decimal places (JPY) passes", ok(out), out[-600:])
out = one('{ what: "a meal", amount: { count: "1500.5", unit: JPY }, paid_by: [ { party: sam } ] }')
check("...and a fraction of one is refused", "JPY is written with at most 0" in out, out[-600:])
out = one('{ what: "a meal", amount: { count: 10, unit: QQQ }, paid_by: [ { party: sam } ] }')
check("a code no currency has is refused", "'QQQ' is not in the `units` registry" in out, out[-600:])
out = one('{ what: "a meal", amount: { count: 10, unit: metre }, paid_by: [ { party: sam } ] }')
check("a unit of ANOTHER quantity is refused: a metre is not an amount", "measures length, and this attribute is a money" in out, out[-400:])

# ---------------------------------------------------------------- THE PARTS OF A WHOLE ADD UP TO IT, EXACTLY
out = one('{ what: "shared", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam, amount: { count: "600.10", unit: XTS } }, { party: ali, amount: { count: "299.90", unit: XTS } } ] }')
check("`sums`: parts that add up to the whole pass", ok(out), out[-600:])
out = one('{ what: "shared", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam, amount: { count: 600, unit: XTS } }, { party: ali, amount: { count: "299.99", unit: XTS } } ] }')
check("...parts that do not are refused, exactly — one hundredth short", "adds up to" in out and "the parts of a whole add up to it exactly" in out, out[-600:])
out = one('{ what: "shared", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam, amount: { count: 600, unit: XTS } }, { party: ali, amount: { count: 300, unit: EUR } } ] }')
check("...parts in ANOTHER currency are refused: two currencies are never added", "the parts of an amount are in its own currency" in out, out[-600:])
out = one('{ what: "shared", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam } ] }')
check("...a single payer who states no amount holds the whole", ok(out), out[-600:])
out = one('{ what: "a ticket", amount: { count: 100, unit: USD }, charged: { count: "91.73", unit: EUR }, paid_by: [ { party: sam, amount: { count: "91.73", unit: EUR } } ] }')
check("...a `charged` amount in another currency is the whole the parts add up to", ok(out), out[-600:])
out = one('{ what: "a ticket", amount: { count: 100, unit: USD }, charged: { count: "91.73", unit: EUR }, paid_by: [ { party: sam, amount: { count: 100, unit: USD } } ] }')
check("...so parts in the priced currency are refused once it was charged in another", "and charged in EUR" in out, out[-600:])

# ---------------------------------------------------------------- WHAT IS OWED IS READ
def owes_lines(out):
    return [l.strip() for l in out.splitlines() if " owes " in l and "settled" not in l]

os.remove(os.path.join(G, "beans", "deal.md"))            # the last probe above was refused on purpose
agreement("groceries", '  week-one: { what: "the groceries", amount: { count: 900, unit: XTS }, '
                       'paid_by: [ { party: sam } ], borne_by: [ { party: sam, share: 2 }, { party: ali, share: 1 } ] }')
out = gate()
check("an agreement with a transaction borne two to one passes the gate", ok(out), out[-800:])
def snapshot():
    return {os.path.join(d, f): open(os.path.join(d, f), "rb").read() for d, ds, fs in os.walk(G)
            for f in fs if ".git" not in d.split(os.sep) and "__pycache__" not in d.split(os.sep)}
before = snapshot()
code, out = ledger("groceries")
check("900 XTS paid by sam, borne sam 2 / ali 1: 'ali owes sam 300 XTS', exactly", owes_lines(out) == ["ali owes sam 300 XTS"], out)
check("...each party's position is what it paid less what it bears", "ali -300 XTS" in out and "sam +300 XTS" in out, out)
check("...and dmledger exits 0 and writes nothing — what is owed is read, never stored", code == 0 and snapshot() == before, out)

agreement("dinner", '  one: { what: "a dinner", amount: { count: 100, unit: XTS }, paid_by: [ { party: sam } ], '
                    'borne_by: [ { party: ali, share: 2 }, { party: sam, share: 1 } ] }')
code, out = ledger("dinner")
check("100 XTS borne two to one: 200/3, printed as the fraction it is — never rounded",
      "ali owes sam 200/3 XTS (does not come out even in XTS's 2 places — who takes the remainder is a clause)" in owes_lines(out), out)

agreement("groceries", '  week-one: { what: "the groceries", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam } ], '
                       'borne_by: [ { party: sam, share: 2 }, { party: ali, share: 1 } ] }\n'
                       '  repaid: { what: "ali pays sam back", amount: { count: 300, unit: XTS }, paid_by: [ { party: ali } ], '
                       'borne_by: [ { party: sam, share: 1 } ] }')
out = gate()
check("a repayment is a transaction like any other: paid by ali, borne by sam", ok(out), out[-600:])
code, out = ledger("groceries")
check("...and it SETTLES what was owed: nobody owes anybody", owes_lines(out) == [] and "XTS: settled" in out, out)

# NETTING ACROSS AGREEMENTS: what ali owes sam under one is set against what sam owes ali under another.
os.remove(os.path.join(G, "beans", "dinner.md"))
agreement("groceries", '  week-one: { what: "the groceries", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam } ], '
                       'borne_by: [ { party: sam, share: 2 }, { party: ali, share: 1 } ] }')
agreement("a-loan", '  lent: { what: "ali lends sam", amount: { count: 100, unit: XTS }, paid_by: [ { party: ali } ], '
                    'borne_by: [ { party: sam, share: 1 } ] }')
out = gate()
check("two agreements between the same parties pass the gate", ok(out), out[-600:])
code, out = ledger("--between", "sam", "ali")
check("--between nets across the two agreements: 300 one way, 100 the other, 200 net",
      "groceries: sam owes ali" not in out and "groceries: ali owes sam 300 XTS" in out and "a-loan: sam owes ali 100 XTS" in out
      and "net, across 2 agreements" in out and out.rstrip().endswith("ali owes sam 200 XTS"), out)

# MORE THAN TWO PARTIES: each bearer owes each payer its share of what that payer put in.
agreement("trip", '  fuel: { what: "fuel", amount: { count: 90, unit: XTS }, paid_by: [ { party: sam } ], '
                  'borne_by: [ { party: sam, share: 1 }, { party: ali, share: 1 }, { party: ben, share: 1 } ] }',
          parties=("sam", "ali", "ben"))
code, out = ledger("trip")
check("three parties, borne equally: ali and ben each owe sam 30 XTS", sorted(owes_lines(out)) == ["ali owes sam 30 XTS", "ben owes sam 30 XTS"], out)

# A CHARGE IN ANOTHER CURRENCY: the rate is read, exactly, and never stored.
agreement("abroad", '  ticket: { what: "a ticket", amount: { count: 100, unit: USD }, charged: { count: "91.73", unit: EUR }, '
                    'paid_by: [ { party: sam } ], borne_by: [ { party: ali, share: 1 } ] }\n'
                    '  fee: { what: "a fee", amount: { count: 3, unit: USD }, charged: { count: 10, unit: EUR }, paid_by: [ { party: sam } ] }')
out = gate()
check("a transaction priced in USD and charged in EUR passes", ok(out), out[-600:])
code, out = ledger("abroad")
check("a charged amount shows its implied rate exactly: 91.73 EUR for 100 USD is 0.9173 EUR per USD",
      "0.9173 EUR per USD" in out and "ali owes sam 91.73 EUR" in owes_lines(out), out)
check("...and one that does not terminate as the fraction it is: 10 EUR for 3 USD is 10/3 EUR per USD",
      "10/3 EUR per USD" in out, out)
check("...and the debt is in the currency that moved, never added to another", not any("USD" in l for l in owes_lines(out)), out)

# WHAT THE GATE CANNOT SEE IS NOT GUESSED AT: two payers, amounts not recorded.
agreement("unclear", '  split: { what: "a bill", amount: { count: 50, unit: XTS }, paid_by: [ { party: sam }, { party: ali } ] }')
code, out = ledger("unclear")
check("two payers whose amounts are not recorded: the transaction is left out, and said to be", "left out" in out and not owes_lines(out), out)

# CLAUSES IN FORCE: when each falls due, and next falls due; a met one is silent.
today = datetime.date.today()
due_soon = (today + datetime.timedelta(days=3)).isoformat()
agreement("instalments", clauses=f'''  repay: {{ what: "ali repays sam", by: ali, to: sam, amount: {{ count: 300, unit: XTS }}, due: {due_soon} }}
  done: {{ what: "a deposit", by: ali, to: sam, due: 2026-09-02, state: met }}
  monthly: {{ what: "ali pays sam 50 XTS a month", by: ali, to: sam, amount: {{ count: 50, unit: XTS }}, due: 2026-01-10, every: {{ of: time, in: gregorian-civil, each: month, at: "10" }} }}
  late: {{ what: "interest on a late payment", by: ali, to: sam, amount: {{ count: 2, unit: percent }}, when: "a payment is late" }}''')
out = gate()
check("an agreement's clauses — a date, a repetition, a ratio, a condition — pass the gate", ok(out), out[-800:])
code, out = ledger("instalments")
check("a clause in force is listed with its due date", "repay" in out and f"due {due_soon} (in 3 days)" in out, out)
check("...a met one is not listed", "a deposit" not in out, out)
check("...a repeating one with its NEXT occurrence, walked in its own calendar",
      re.search(r"each month in gregorian-civil at 10 — next \d{4}-\d{2}-10", out), out)
check("...a conditional one with its condition, and what is not yet known", 'when: "a payment is late"' in out and "not yet known: due" in out, out)

# ---------------------------------------------------------------- THE ARITHMETIC ITSELF IS FRACTIONS
units = dmunits.law()[0]
rule = dict(wholes=["charged", "amount"], parts="paid_by", part_amount="amount", party="party", dates=[], said_as=["what"])
tx = dmledger.read_transaction("t", {"what": "x", "amount": {"count": 100, "unit": "XTS"}, "paid_by": [{"party": "sam"}],
                                     "borne_by": [{"party": "ali", "share": 2}, {"party": "sam", "share": 1}]}, rule, units)
o = dmledger.owed(tx)
check("the library: what ali owes is Fraction(200, 3), a fraction and not a float", o == {("ali", "sam"): Fraction(200, 3)}
      and all(type(v) is Fraction for v in o.values()), o)
tx = dmledger.read_transaction("t", {"what": "x", "amount": {"count": 100.0, "unit": "XTS"}, "paid_by": [{"party": "sam"}]}, rule, units)
check("...and a float count is not read at all", tx["paid"] is None and tx["notes"], tx)

# ---------------------------------------------------------------- TWO CURRENCIES MEET ONLY AT AN OBSERVED RATE
r = run(sys.executable, os.path.join(ROOT, "bin", "dmunits.py"), "100", "XTS", "EUR")
check("dmunits refuses 100 XTS to EUR without a rate", r.returncode == 1 and "a rate is a fact someone observed" in r.stdout, r.stdout)
r = run(sys.executable, os.path.join(ROOT, "bin", "dmunits.py"), "100", "XTS", "EUR", "--rate", "0.9173")
check("...and with one the result is exact", r.returncode == 0 and r.stdout.strip() == "91.73 EUR", r.stdout)
big = "123456789012345678901234567890.12"
check("...exact at a size a float would ruin: thirty digits times a rate of thirty places",
      dmunits.convert(big, "XTS", "EUR", "1.000000000000000000000000000001") == Fraction(big) * Fraction("1.000000000000000000000000000001"))
def refused(f):
    try:
        f(); return False
    except ValueError:
        return True
check("...a rate written as a float, an exponent or a fraction is refused", refused(lambda: dmunits.convert("1", "XTS", "EUR", 0.9))
      and refused(lambda: dmunits.convert("1", "XTS", "EUR", "9e-1")) and refused(lambda: dmunits.convert("1", "XTS", "EUR", "1/3")))
check("...and a rate where the law holds a factor is refused: a metre is a thousand millimetres, not what someone saw",
      refused(lambda: dmunits.convert("1", "metre", "millimetre", "2")))
check("...a currency is still not a length", refused(lambda: dmunits.convert("1", "XTS", "metre", "1")))

# ---------------------------------------------------------------- THE SOURCE: NO FLOAT ANYWHERE IN MONEY CODE
def floats_in(text, strict):
    """Float literals, `float(` calls — and, where `strict`, the division operator and any rounding at all. Read with the
    tokenizer, so a `1.5` in a docstring is prose and a `1.5` in code is not."""
    found, toks = [], [t for t in tokenize.generate_tokens(io.StringIO(text).readline)
                       if t.type not in (tokenize.NL, tokenize.NEWLINE, tokenize.COMMENT, tokenize.INDENT, tokenize.DEDENT)]
    for i, t in enumerate(toks):
        nxt = toks[i + 1].string if i + 1 < len(toks) else ''
        if t.type == tokenize.NUMBER and not t.string.lower().startswith(("0x", "0o", "0b")) and re.search(r"[.eEjJ]", t.string):
            found.append(f"line {t.start[0]}: float literal {t.string}")
        elif t.type == tokenize.NAME and t.string == "float" and (strict or nxt == "("):
            found.append(f"line {t.start[0]}: float")
        elif strict and t.type == tokenize.OP and t.string in ("/", "/="):
            found.append(f"line {t.start[0]}: true division")
        elif strict and t.type == tokenize.NAME and t.string in ("round", "math", "decimal"):
            found.append(f"line {t.start[0]}: {t.string}")
    return found
check("the scan finds what it looks for (a scan that finds nothing proves nothing)",
      len(floats_in("x = 0.5\ny = float('1')\nz = a / b\nw = round(z)\n", True)) == 4)
led = floats_in(open(os.path.join(ROOT, "bin", "dmledger.py"), encoding="utf-8").read(), True)
check("bin/dmledger.py holds no float literal, no float, no division operator and no rounding", not led, led)
uni = floats_in(open(os.path.join(ROOT, "bin", "dmunits.py"), encoding="utf-8").read(), False)
check("bin/dmunits.py holds no float literal and calls no float()", not uni, uni)

shutil.rmtree(T, ignore_errors=True)
print("\nmoney: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
