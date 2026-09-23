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
def refused(f):
    try:
        f(); return False
    except ValueError:
        return True
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
check("...a conditional one with the condition that brings it into force — and no due date called missing, for it has none",
      'in force when: "a payment is late"' in out and "not yet known: due" not in out, out)
agreement("someday", clauses='  repay: { what: "ali repays sam when they agree a day", by: ali, to: sam }')
code, out = ledger("someday")
check("...while a clause with neither a due date nor a condition still says what is not yet known",
      "not yet known: amount, due" in out, out)
os.remove(os.path.join(G, "beans", "someday.md"))

# ---------------------------------------------------------------- A DATED TRANSACTION: the gate, the merge, the ledger
# The day a transaction happened was once named `on`, which YAML 1.1 reads as the boolean true: it crashed the gate on
# any stray key beside it, and the merge's canonical form on any bean that dated a transaction. It is `day` — and it is
# exercised here end to end, because a suite that never wrote one could not see either crash.
DATED = ('  groceries: { what: "the groceries", day: 2026-09-01, amount: { count: 900, unit: XTS }, paid_by: [ { party: sam } ], '
         'borne_by: [ { party: sam, share: 2 }, { party: ali, share: 1 } ] }')
agreement("dated", DATED)
out = gate()
check("a DATED transaction (`day:`) passes the gate", ok(out) and "Traceback" not in out, out[-800:])
code, out = ledger("dated")
check("...and dmledger reads it, with its day", code == 0 and "groceries  2026-09-01  900 XTS" in out
      and owes_lines(out) == ["ali owes sam 300 XTS"], out)
sys.path.insert(0, os.path.join(G, "bin"))
import dmparse as _dmparse, dmmerge as _dmmerge
_fm = _dmparse.loads(_dmparse.read(os.path.join(G, "beans", "dated.md"))[0])
try:
    _canon = _dmmerge.canonical(_dmmerge.norm(_fm))
except TypeError as _e:
    _canon = f"TypeError: {_e}"
check("...and the merge's canonical form of it is made — the date is `\"day\":\"2026-09-01\"`", '"day":"2026-09-01"' in _canon, _canon[:400])
G2 = os.path.join(T, "g2")
shutil.copytree(G, G2)                        # the same garden (its history came with it), one fact apart
_p2 = os.path.join(G2, "beans", "dated.md")
_t2 = open(_p2, encoding="utf-8").read().replace("day: 2026-09-01", "day: 2026-09-02")
open(_p2, "w", encoding="utf-8", newline="\n").write(_t2)
r = run(sys.executable, os.path.join(G, "bin", "dmmerge.py"), G, G2, cwd=G)
check("...and two copies of the garden that date it differently MERGE, the two days kept as a disagreement",
      r.returncode == 0 and "Traceback" not in r.stderr and '"day":"2026-09-01"' in r.stdout and '"day":"2026-09-02"' in r.stdout
      and "fingerprint:" in r.stdout, (r.stdout[-600:] + r.stderr[-600:]))
shutil.rmtree(G2, ignore_errors=True)
out = one('{ what: "a meal", on: 2026-09-01, amount: { count: 10, unit: XTS }, paid_by: [ { party: sam } ] }')
check("the old name `on` is REFUSED, never crashed on: YAML read it as true, and a key that is not text is said to be",
      "Traceback" not in out and "is not text" in out and not ok(out), out[-600:])
os.remove(os.path.join(G, "beans", "deal.md"))

# ---------------------------------------------------------------- WHAT IS NOT READ IS SAID, AND NEVER CRASHES
# dmledger reads the WORKING TREE, where an uncommitted mistake is: it leaves such a thing out and says so.
agreement("slip", '  t: { what: "a slip", amount: { count: "--5", unit: XTS }, paid_by: [ { party: sam } ] }')
code, out = ledger("slip")
check("a count of `--5` (two signs) is left out with a NOTE — the gate's own pattern, not a traceback",
      code == 0 and "Traceback" not in out and "not a count this can read exactly" in out, out)
check("...and dmledger's reader refuses exactly what the gate refuses",
      all(dmledger.count_of({"count": c}) is None for c in ("--5", "-", "1e3", "1.", ".5", "+5", "١٢", 1.5, True))
      and dmledger.count_of({"count": "-12.50"}) == Fraction(-25, 2) and dmledger.count_of({"count": 7}) == 7)
os.remove(os.path.join(G, "beans", "slip.md"))

# WHATEVER A READER IS HANDED, IT READS OR SAYS IT DID NOT — never a traceback that ends the reading for every agreement. A
# count or a share of five thousand digits passed the gate once and ended dmledger in Python's own ValueError (its limit
# is 4300 digits); the law bounds a count at forty digits on each side of the point, and so does every reader here.
_big = "1" * 5000
for _label, _tx in (("a count of 5000 digits", f'{{ what: "x", amount: {{ count: "{_big}", unit: XTS }}, paid_by: [ {{ party: sam }} ] }}'),
                    ("a count of 41", '{ what: "x", amount: { count: "' + "9" * 41 + '", unit: XTS }, paid_by: [ { party: sam } ] }'),
                    ("a paid part of 5000", f'{{ what: "x", amount: {{ count: 900, unit: XTS }}, paid_by: [ {{ party: sam, amount: {{ count: "{_big}", unit: XTS }} }}, {{ party: ali }} ] }}')):
    agreement("huge", "  t: " + _tx)
    code, out = ledger("huge")
    check(f"{_label} is LEFT OUT with a NOTE saying why — dmledger exits 0, no traceback",
          code == 0 and "Traceback" not in out and "longer than a count may be" in out and "left out" in out, out[-600:])
agreement("huge", '  t: { what: "x", amount: { count: 900, unit: XTS }, paid_by: [ { party: sam } ], '
                  f'borne_by: [ {{ party: sam, share: "{_big}" }}, {{ party: ali, share: 1 }} ] }}')
code, out = ledger("huge")
check("...and a SHARE of 5000 digits too — its value shown by its start and its length, not printed whole",
      code == 0 and "Traceback" not in out and "is not a whole number of parts" in out and "(5000 characters)" in out
      and len(out) < 2000, out[-600:])
os.remove(os.path.join(G, "beans", "huge.md"))
check("the library: dmunits refuses a count longer than a count may be with a ValueError that says so, and dmledger's reader "
      "turns it into None — at forty digits it reads, at forty-one it does not",
      refused(lambda: dmunits.exact(_big)) and refused(lambda: dmunits.exact(10 ** 40)) and refused(lambda: dmunits.exact("0." + "1" * 41))
      and dmunits.exact("9" * 40 + "." + "9" * 40) == Fraction("9" * 40 + "." + "9" * 40)
      and dmledger.count_of({"count": _big}) is None and dmledger.count_of({"count": 10 ** 5000}) is None)
check("...and what a YAML 1.1 reader would have read as another number, handed as the text written, is not read as any: "
      "`0x64`, `1:30`, `0b11`, `1_000` — and `010`, eight to YAML 1.1 and ten to a person, is written without its zero",
      all(dmunits.exact(c) is None for c in ("0x64", "1:30", "0b11", "1_000", "0o10", "+5", "010", "00.5"))
      and dmunits.exact("0.50") == Fraction(1, 2) and dmunits.exact("-0") == 0)
import yaml
_rule = dict(dmledger.money_terms({t["term"]: t for t in yaml.safe_load(_dmparse.read(os.path.join(ROOT, "seed", "std-vocab.md"))[0])["terms"]}))["transactions"]
_u = dmunits.law()[0]
def _bearing(*shares):
    return dmledger.read_transaction("t", {"what": "x", "amount": {"count": 900, "unit": "XTS"}, "paid_by": [{"party": "sam"}],
                                           "borne_by": [dict({"party": p}, **({"share": s} if s is not ... else {})) for p, s in shares]}, _rule, _u)
_bad = {k: _bearing(("sam", s), ("ali", 1)) for k, s in (("an int of 5001 digits", 10 ** 5000), ("'010'", "010"), ("'1.5'", "1.5"),
                                                          ("41 digits", "1" * 41), ("an int of 41 digits", 10 ** 40),
                                                          ("1.5", 1.5), ("True", True), ("'yes'", "yes"), ("'٢'", "٢"), ("'0'", "0"), ("-1", -1))}
check("a share is read as the law's own pattern for it reads one, and no longer than a count may be: five thousand digits, "
      "forty-one, `010`, 1.5, yes, a digit of another script, 0 and -1 are each left out with a NOTE — never a traceback, "
      "never read as something nobody wrote",
      all(t["paid"] is None and any("not a whole number of parts" in n for n in t["notes"]) for t in _bad.values())
      and _bearing(("sam", "2"), ("ali", 1))["borne"] == {"sam": 600, "ali": 300},
      {k: t["notes"] for k, t in _bad.items() if t["paid"] is not None or not t["notes"]})
check("...and each is said as it is written, in backticks — `true`, `010` — or, too long to write out, by what "
      "it is; never Python's own spelling of it",
      any("sam's share `true` is not" in n for n in _bad["True"]["notes"]) and any("sam's share `010` is not" in n for n in _bad["'010'"]["notes"])
      and any("sam's share a number of more than" in n for n in _bad["an int of 5001 digits"]["notes"])
      and not any("True" in n or "'" in n.split("share ", 1)[1].split(" is not")[0] for t in _bad.values() for n in t["notes"]),
      {k: t["notes"] for k, t in _bad.items()})
_t = _bearing(("sam", ...), ("ali", 1))
check("...a bearer that names no share is said to name none — not 'a share of None'",
      _t["paid"] is None and any("sam is named as bearing it and names no share" in n for n in _t["notes"])
      and not any("None" in n for n in _t["notes"]), _t["notes"])

# A PART THAT IS NOT AN ENTRY IS SAID TO BE: `paid_by: [sam, {party: ali, …}]` was read as "paid by ali", sam left out in
# silence; `paid_by: [sam]` was read as nobody. Each is now left out with a NOTE naming what is not an entry.
# It is said in the reader's words: `sam`, an empty entry, a list [sam] — never Python's 'sam', None or ['sam'].
for _label, _paid, _said in (("a bare name beside an entry", '[ sam, { party: ali, amount: { count: 900, unit: XTS } } ]', "`sam`"),
                             ("a bare name as the only payer", '[ sam ]', "`sam`"),
                             ("a bare name that is not even a list", 'sam', "`sam`"),
                             ("an empty entry (`null`)", '[ null ]', "an empty entry"),
                             ("a list where an entry goes", '[ [ sam ] ]', "a list [sam]")):
    agreement("bare", f'  t: {{ what: "x", amount: {{ count: 900, unit: XTS }}, paid_by: {_paid} }}')
    code, out = ledger("bare")
    check(f"{_label} in paid_by is LEFT OUT with a NOTE — the payer is not silently dropped — and said as {_said}",
          code == 0 and "Traceback" not in out and f"paid_by holds {_said}, which is not an entry" in out and "paid by" not in out
          and "None" not in out and "['" not in out, out[-500:])
for _borne, _said in (("[ ali ]", "`ali`"), ("[ null ]", "an empty entry")):
    agreement("bare", f'  t: {{ what: "x", amount: {{ count: 900, unit: XTS }}, paid_by: [ {{ party: sam }} ], borne_by: {_borne} }}')
    code, out = ledger("bare")
    check(f"...and so in borne_by: {_said}", f"borne_by holds {_said}, which is not an entry" in out and "Traceback" not in out
          and "None" not in out, out[-500:])
os.remove(os.path.join(G, "beans", "bare.md"))

agreement("nothing", '  t: { what: "a wash", amount: { count: 0, unit: XTS }, paid_by: [ { party: sam, amount: { count: 100, unit: XTS } }, '
                     '{ party: ali, amount: { count: "-100", unit: XTS } } ] }')
out = gate()
check("(the gate lets such a transaction through: its parts do add up to its whole)", ok(out), out[-600:])
code, out = ledger("nothing")
check("a whole of 0 whose parts are not (+100, -100) is left out, said to be — the positions and the debts cannot disagree",
      "no share of nothing" in out and not owes_lines(out) and "position" not in out, out)
os.remove(os.path.join(G, "beans", "nothing.md"))

with open(os.path.join(G, "beans", "broken.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("---\nbean: broken\nkind: contract\ntransactions: { t: { what: [unclosed }\n---\nbroken.\n")
code, out = ledger("--between", "sam", "ali")
check("a bean whose front matter does not parse is NOTED, not skipped in silence: a total without it says so",
      code == 0 and "NOTE beans/broken.md is not read" in out, out)
code, out = ledger("broken")
check("...and naming it is 'cannot be read', not 'no bean'", code == 2 and "cannot be read" in out and "no bean" not in out, out)
os.remove(os.path.join(G, "beans", "broken.md"))

r = run(sys.executable, os.path.join(ROOT, "bin", "dmledger.py"), cwd=ROOT)
check("outside a garden (no VOCAB.md) dmledger says so and exits 2 — no traceback",
      r.returncode == 2 and "not in a garden" in r.stdout and "Traceback" not in r.stderr, r.stdout + r.stderr[-400:])

# ---------------------------------------------------------------- A DISAGREEMENT A MERGE LEFT FOR A PERSON
# bin/dmmerge.py records a disagreement on ONE member of a keyed collection: `transactions: {t: {conflict: [a, b]}}`,
# and the same for a clause and a party. Made here by the merge driver itself, so the shape read is the shape written.
_base = open(os.path.join(G, "beans", "dated.md"), encoding="utf-8").read().replace(
    "---\nAn agreement.", "clauses:\n  repay: { what: \"ali repays sam\", by: ali, to: sam, due: 2026-10-01 }\n---\nAn agreement.")
_O, _A, _B = (os.path.join(T, n) for n in ("O.md", "A.md", "B.md"))
open(_O, "w", encoding="utf-8", newline="\n").write(_base)
open(_A, "w", encoding="utf-8", newline="\n").write(_base.replace("day: 2026-09-01", "day: 2026-09-02")
                                                   .replace("due: 2026-10-01 }", "due: 2026-10-01, state: met }")
                                                   .replace("ali: { who: { bean: ali }, accepted: 2026-09-01 }", "ali: { who: { bean: ali }, accepted: 2026-09-03 }"))
open(_B, "w", encoding="utf-8", newline="\n").write(_base.replace("day: 2026-09-01", "day: 2026-09-05").replace("due: 2026-10-01 }", "due: 2026-10-02 }")
                                                   .replace("ali: { who: { bean: ali }, accepted: 2026-09-01 }", "ali: { who: { bean: ali }, accepted: 2026-09-04 }"))
r = run(sys.executable, os.path.join(G, "bin", "dmmerge.py"), "--file", _O, _A, _B, cwd=G)
shutil.copyfile(_A, os.path.join(G, "beans", "dated.md"))
code, out = ledger("dated")
check("the merge driver records the disagreements member by member", r.returncode == 0 and "conflict" in open(_A, encoding="utf-8").read(),
      r.stdout + r.stderr)
check("a transaction in a merge conflict is left out and NAMED as one — not misread as 'not a count'",
      "groceries  — holds a merge conflict" in out and "differing in: day" in out and "not a count" not in out
      and not owes_lines(out), out)
check("...a clause in one is neither in force nor met: listed apart, with what the sides differ on",
      "clauses in a merge conflict (1)" in out and "repay  NOTE 2 sides, differing in: due, state" in out
      and "clauses in force" not in out, out)
check("...and a party in one whose sides name the same bean is still that bean", "party ali holds a merge conflict, differing in: accepted — who it is agrees" in out, out)
# --between NETS ACROSS AGREEMENTS, and one of them holds a transaction two gardens recorded two ways: left out of the net,
# said to be, and the net called PARTIAL. Silent, the net was simply wrong — and said it was across every agreement.
code, out = ledger("--between", "sam", "ali")
check("--between says what it left out: the transaction in a merge conflict is a NOTE under its agreement, with why and "
      "where to look, and the net is PARTIAL — while every clean agreement is still netted",
      code == 0 and "NOTE dated: transaction groceries: holds a merge conflict — 2 sides, differing in: day" in out
      and "not in this net; `python" in out and "bin/dmledger.py dated` shows it" in out
      and re.search(r"net, across \d+ agreements — PARTIAL: \d+ agreements? left something out \(NOTE above\), so this is "
                    r"not the whole of what is owed:", out)
      and "groceries: ali owes sam 300 XTS" in out and "a-loan: sam owes ali 100 XTS" in out, out)
agreement("who-is-it", '  t: { what: "a lamp", amount: { count: 60, unit: XTS }, paid_by: [ { party: sam } ], '
                      'borne_by: [ { party: ali, share: 1 } ] }')
_w = open(os.path.join(G, "beans", "who-is-it.md"), encoding="utf-8").read()
with open(os.path.join(G, "beans", "who-is-it.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(_w.replace("  ali: { who: { bean: ali }, accepted: 2026-09-01 }",
                        "  ali: { conflict: [ { who: { bean: ali } }, { who: { bean: ben } } ] }"))
code, out = ledger("--between", "sam", "ali")
check("...and an agreement where WHO a party is waits for a person (its sides name ali and ben) is not passed over as "
      "not theirs: it may be between them, is named, and the net is PARTIAL",
      code == 0 and "NOTE who-is-it: may be between sam and ali — who a party is waits for a person" in out
      and "PARTIAL: 3 agreements left something out" in out, out)
os.remove(os.path.join(G, "beans", "who-is-it.md"))
agreement("dated", DATED)

# ---------------------------------------------------------------- WHAT A BEAN SAYS IS SHOWN, NEVER OBEYED
# A title that climbs back a line, erases it and writes a debt the other way round, then conceals all that follows; a
# transaction's `what` and a clause's `what` that do the same, or retitle the window. Written as YAML writes such a
# character (`\e`), so it is in the VALUE — what another garden's proposal can carry. Printed raw, it was an instruction
# to the reader's terminal; through the readers' one escaper it is text: `\x1b`.
with open(os.path.join(G, "beans", "loud.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write('---\nbean: loud\nkind: contract\ntitle: "a note\\e[2A\\e[2K\\r   sam owes ali 3000 XTS\\e[8m"\nstatus: active\n'
             'summary: "an agreement"\nnature: metaphysical\nowned_by: { legal: { crown: logos } }\n'
             'responsibility: { legal: { parties: true } }\n'
             'identity: { status: confirmed, anchors: [ { key: contract_id, value: "contract:loud", class: logical, establishing: true } ] }\n'
             'provenance: { src: asserted-by-human, by: sam, as_of: 2026-09-01 }\n'
             'parties:\n  sam: { who: { bean: sam }, accepted: 2026-09-01 }\n  ali: { who: { bean: ali }, accepted: 2026-09-01 }\n'
             'words: { form: spoken, agreed: 2026-09-01 }\n'
             'transactions:\n  t: { what: "a coffee\\e[8m", day: 2026-09-01, amount: { count: 3, unit: XTS }, paid_by: [ { party: sam } ], '
             'borne_by: [ { party: ali, share: 1 } ] }\n'
             f'clauses:\n  c: {{ what: "call\\e]0;owned\\a", by: ali, to: sam, due: {(datetime.date.today() + datetime.timedelta(days=3)).isoformat()} }}\n'
             '---\nAn agreement.\n')
_raw = {name: subprocess.run([sys.executable, os.path.join(G, "bin", name)] + args, capture_output=True, cwd=G).stdout
        for name, args in (("dmledger.py", []), ("dmstale.py", []))}
_between = subprocess.run([sys.executable, os.path.join(G, "bin", "dmledger.py"), "--between", "sam", "ali"], capture_output=True, cwd=G).stdout
check("a title, a transaction's `what` and a clause's `what` holding ESC sequences reach NEITHER reader's terminal: "
      "dmledger's and dmstale's stdout hold no ESC byte, and each is shown as its escape, `\\x1b`",
      all(b"\x1b" not in v and b"\x07" not in v for v in list(_raw.values()) + [_between])
      and b"a note\\x1b[2A\\x1b[2K\\x0d   sam owes ali 3000 XTS\\x1b[8m" in _raw["dmledger.py"]
      and b'"a coffee\\x1b[8m"' in _raw["dmledger.py"] and b'"call\\x1b]0;owned\\x07"' in _raw["dmledger.py"]
      and b"loud.clauses[c]" in _raw["dmstale.py"], {k: v[-600:] for k, v in _raw.items()})
_t = open(os.path.join(G, "beans", "loud.md"), encoding="utf-8").read()
with open(os.path.join(G, "beans", "loud.md"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write(re.sub(r'(?m)^title: .*$', 'title: { conflict: [ "The loud note", "A loud note" ] }', _t, count=1))
code, out = ledger("loud")
check("a title two gardens wrote two ways is said to be in a merge conflict — never Python's spelling of the record",
      code == 0 and "== loud — (its title is in a merge conflict, 2 sides, until a person chooses)" in out
      and "{'conflict'" not in out, out[:400])
os.remove(os.path.join(G, "beans", "loud.md"))

# ---------------------------------------------------------------- THE LAW IS READ, NOT NAMED
_terms = {"parties": {"schema": {"attrs": {"person": {"in": "ref"}, "external": {"in": "prose"}}}}}
check("the party's bean is read through whichever attribute the parties term declares a `ref` (here `person`, not `who`)",
      dmledger.party_refs(_terms, ["parties"]) == {"parties": "person"}
      and dmledger.read_agreement("x", {"parties": {"s": {"person": {"bean": "sam"}}}}, [], [], {"parties": "person"}, {})["parties"] == {"s": "sam"})
import yaml
_std = {t["term"]: t for t in yaml.safe_load(_dmparse.read(os.path.join(ROOT, "seed", "std-vocab.md"))[0])["terms"]}
_mt = dict(dmledger.money_terms(_std))
check("...and who bears a transaction is the `key_of: parties` attribute of its bearers' entries, found as a payer's is",
      _mt.get("transactions", {}).get("bearer") == "party" and _mt["transactions"]["party"] == "party", _mt.get("transactions"))

# ---------------------------------------------------------------- A CURRENCY THE GARDEN ADDED IS ONE CURRENCY TO EVERY READER
_v = os.path.join(G, "VOCAB.md")
_vtext = open(_v, encoding="utf-8").read()
assert "registry_additions" not in _vtext and _vtext.count("\n---") == 1, "the VOCAB.md template has moved: this test adds the row"
open(_v, "w", encoding="utf-8", newline="\n").write(_vtext.replace("\n---", "\nregistry_additions:\n  currencies:\n    - { code: XQA, "
                                                     "numeric: '', digits: 3, name: \"a garden's own unit of account\", status: special }\n---", 1))
agreement("own-unit", '  t: { what: "a token", amount: { count: "9.001", unit: XQA }, paid_by: [ { party: sam } ], borne_by: [ { party: ali, share: 1 } ] }')
out = gate()
check("a currency the garden added under `registry_additions` passes the gate", ok(out), out[-700:])
code, out = ledger("own-unit")
check("...dmledger reads it with its own three places", "ali owes sam 9.001 XQA" in owes_lines(out), out)
r = run(sys.executable, os.path.join(G, "bin", "dmunits.py"), "9.001", "XQA", "XQA", cwd=G)
check("...and dmunits, in the garden, knows it too: the law the gate loaded, not the seed files beside it",
      r.returncode == 0 and r.stdout.strip() == "9.001 XQA", r.stdout + r.stderr)
r = run(sys.executable, os.path.join(G, "bin", "dmunits.py"), "9.0001", "XQA", "XQA", cwd=G)
check("...with its places: a fourth is refused", r.returncode == 1 and "more decimal places than XQA's 3" in r.stdout, r.stdout)
os.remove(os.path.join(G, "beans", "own-unit.md"))
open(_v, "w", encoding="utf-8", newline="\n").write(_vtext)

# ---------------------------------------------------------------- A PIPE ON WINDOWS
# Python on Windows writes a pipe in the ANSI code page (cp1252), which has no `≈`: printing one raised, and an agent reads
# through a pipe. Imitated here by naming the encoding.
_env = dict(os.environ, PYTHONIOENCODING="cp1252")
# The tools write UTF-8 whatever the platform (bin/dmparse.py sets it once), so what arrives is the exact text — a `≈`, and
# a Persian name, which no glyph fallback could have saved in cp1252.
r = subprocess.run([sys.executable, os.path.join(G, "bin", "dmledger.py"), "abroad"], capture_output=True, text=True, cwd=G, env=_env,
                   encoding="utf-8", errors="replace")
check("dmledger prints a rate that does not terminate through a cp1252 pipe — no UnicodeEncodeError, the text intact in UTF-8",
      r.returncode == 0 and "Traceback" not in r.stderr and ("10/3 EUR per USD (≈ 3.33333)" in r.stdout or "10/3 EUR per USD (~ 3.33333)" in r.stdout), r.stdout[-500:] + r.stderr[-500:])
r = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "dmunits.py"), "1", "minute", "day"], capture_output=True, text=True,
                   env=_env, encoding="utf-8", errors="replace")
check("...and so does dmunits", r.returncode == 0 and ("1/1440 day   (≈ 0.000694444)" in r.stdout or "1/1440 day   (~ 0.000694444)" in r.stdout), r.stdout + r.stderr[-400:])

# ---------------------------------------------------------------- THE ARITHMETIC ITSELF IS FRACTIONS
units = dmunits.law()[0]
rule = dict(wholes=["charged", "amount"], parts="paid_by", part_amount="amount", party="party", bearer="party", dates=[], said_as=["what"])
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
check("...a rate written as a float, an exponent or a fraction is refused", refused(lambda: dmunits.convert("1", "XTS", "EUR", 0.9))
      and refused(lambda: dmunits.convert("1", "XTS", "EUR", "9e-1")) and refused(lambda: dmunits.convert("1", "XTS", "EUR", "1/3")))
check("...and a rate where the law holds a factor is refused: a metre is a thousand millimetres, not what someone saw",
      refused(lambda: dmunits.convert("1", "metre", "millimetre", "2")))
check("...a currency is still not a length", refused(lambda: dmunits.convert("1", "XTS", "metre", "1")))
try:
    dmunits.convert("1", "XTS", "EUR", "-1"); _neg = ""
except ValueError as _e:
    _neg = str(_e)
check("...a negative rate is refused for what it is: a rate between two currencies is positive", "is positive" in _neg, _neg)
r = run(sys.executable, os.path.join(ROOT, "bin", "dmunits.py"), "1", "XTS", "EUR", "--rate", "1", "--digits", "x")
check("`--digits x` is refused with the form it takes — no traceback", r.returncode == 2 and "Traceback" not in r.stderr
      and "--digits 'x'" in r.stdout, r.stdout + r.stderr[-300:])

# A PRINTED COMMAND NAMES THE INTERPRETER AS IT IS NAMED WHERE IT RUNS: `python3` may be the Microsoft Store's alias on
# Windows. Imitated here by naming the platform, in-process.
import contextlib
def _help_on_windows(main):
    buf, was = io.StringIO(), os.name
    try:
        os.name = "nt"
        with contextlib.redirect_stdout(buf):
            main(["--help"])
    finally:
        os.name = was
    return buf.getvalue()
_h = _help_on_windows(dmledger.main) + _help_on_windows(dmunits.main)
check("dmledger's and dmunits' help print `python bin/…` on Windows", "python bin/dmledger.py" in _h and "python bin/dmunits.py" in _h
      and "python3 bin/" not in _h, _h[:400])
_u = dmunits.law()[0]
_u["XTS"]["digits"] = "9"; _u["metre"]["factor"].append(7)
check("law() hands the caller its own copy: changing it changes nothing for the rest of the process",
      dmunits.law()[0]["XTS"]["digits"] == "2" and dmunits.law()[0]["metre"]["factor"] == [1, 1]
      and dmunits.convert("1.5", "kilometre", "metre") == 1500)

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
# EVERY OTHER PLACE A COUNT IS READ OR COMPARED: the gate's quantity check and its sums, the merge's canonical form (where two
# amounts are found equal or not: `norm`, and every function of bin/dmmerge.py whose name says it canonicalises), and the
# stride of a repetition. Read, never changed: each function is taken by its name from the file that owns it, so one that
# is renamed or gone fails here rather than going unscanned.
import ast
def functions(rel, wanted):
    text = open(os.path.join(ROOT, rel), encoding="utf-8").read()
    return {f"{rel}:{n.name}": ast.get_source_segment(text, n) for n in ast.walk(ast.parse(text))
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and wanted(n.name)}
_scanned = {**functions("bin/dmcheck.py", lambda n: n in ("check_quantity", "ectl_sums")),
            **functions("bin/dmmerge.py", lambda n: n == "norm" or "canon" in n),
            **functions("bin/dmstale.py", lambda n: n == "_after_first")}
check("the scan finds each function it names", all(k in _scanned for k in ("bin/dmcheck.py:check_quantity", "bin/dmcheck.py:ectl_sums",
      "bin/dmmerge.py:norm", "bin/dmmerge.py:canonical", "bin/dmstale.py:_after_first")), sorted(_scanned))
_found = {k: floats_in(v, True) for k, v in _scanned.items()}
check("...and none of them holds a float literal, a float, a division operator or any rounding: " + ", ".join(sorted(_scanned)),
      not any(_found.values()), {k: v for k, v in _found.items() if v})

shutil.rmtree(T, ignore_errors=True)
print("\nmoney: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
