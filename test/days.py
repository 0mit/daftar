#!/usr/bin/env python3
"""A day is a position, in either of its forms, and a moment is in time and place together (std-vocab 27.0).

Grows a garden and writes an agreement whose days are written LONG — as one entry of `timing` — in the Gregorian and the
Persian calendars, and placed only by what they followed. Checks that the gate judges the long form as it judges the
short (its unit, its system, the day itself), that an acceptance nobody dated is an acceptance and counts as consent,
that the readers read a long day as the short one and say of one placed by its neighbours that it names no day, and that
the retired `iso_date` is refused with where it went, and translated by the upgrade. Then the moment's place: a `timing`
entry and a day written long say where they were, the location resolver reads a moment's offset against the zone in
force there, a meter is a system's own, and a calendar whose day begins somewhere says which place it resolves through.
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


T = tempfile.mkdtemp(prefix="dmdays-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "sam", cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
BEANS = os.path.join(G, "beans")
HEAD = """---
bean: {bean}
genos: {genos}
title: "{bean}"
status: active
summary: "probe"
nature: {nature}
identity:
  status: confirmed
  anchors:
    - {{ key: identifier, value: "{genos}:{bean}", class: logical, establishing: true }}
provenance: {{ src: asserted-by-human, by: "sam", as_of: 2026-09-28 }}
"""
open(os.path.join(BEANS, "dinner-at-sams.md"), "w").write(HEAD.format(bean="dinner-at-sams", genos="event", nature="lekton") + """\
owned_by: { legal: { crown: logos } }
responsibility: { legal: { holder: { bean: sam } } }
timing:
  start: { system: gregorian-civil, at: "2026-09-12 19:30+03:00", unit: minute }
refs:
  host: { bean: sam, rel: host }
---
A dinner.
""")
open(os.path.join(BEANS, "ali.md"), "w").write(HEAD.format(bean="ali", genos="person", nature="empsychon") + """\
consent: { bean: phone-loan }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
---
Ali.
""")
ALI = '{ system: event-anchored, at: "after:dinner-at-sams", unit: day, note: "on the call; its day was not said" }'
LOAN = HEAD.format(bean="phone-loan", genos="contract", nature="lekton") + """\
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, role: lender, accepted: { system: gregorian-civil, at: 2026-09-14, unit: day, by: "sam", where: { system: iso-3166, at: IR, zone: Asia/Tehran } } }
  ali: { who: { bean: ali }, role: borrower, accepted: %(ali)s }
words: { form: spoken, agreed: { system: persian-calendar, at: "persian:1405-06-23", unit: day } }
clauses:
  first:
    what: "Ali repays 20 XTS"
    by: ali
    to: sam
    amount: { count: "20.00", unit: XTS }
    due: %(due)s
  second:
    what: "Ali repays the rest once her shop opens"
    by: ali
    to: sam
    amount: { count: "100.00", unit: XTS }
    due: { system: event-anchored, at: "after:the day her shop opens", unit: day }
transactions:
  the-loan:
    what: "Sam paid the shop for Ali's phone"
    amount: { count: "120.00", unit: XTS }
    day: { system: gregorian-civil, at: 2026-09-15, unit: day }
    paid_by:
      - { party: sam }
    borne_by:
      - { party: ali, share: 1 }
---
Agreed on the phone.
"""
DUE = "{ system: gregorian-civil, at: 2099-01-15, unit: day }"


def gate(ali=ALI, due=DUE):
    open(os.path.join(BEANS, "phone-loan.md"), "w").write(LOAN % {"ali": ali, "due": due})
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr


out = gate()
check("days written long — a Gregorian day, a Persian one, one placed by what it followed — pass the gate as the short "
      "form does, and an acceptance nobody dated is an acceptance: Ali is kept by name on it",
      " 0 error(s), 0 warning(s)" in out, out[-900:])
out = gate(due='"2099-01-15 09:00+03:00"')
check("...beside a `due` written short, which stays as it was", " 0 error(s)" in out, out[-600:])
out = gate(due='{ system: gregorian-civil, at: "2099-01-15 09:00+03:00", unit: minute }')
check("...and a `date_or_moment` written long at unit minute is a moment", " 0 error(s)" in out, out[-600:])

# ---- the long form is judged as the short one, and as an entry of `timing` -------------------------------------------
for why, ali, want in (
        ("its unit is the type's: a date is held to the day", '{ system: gregorian-civil, at: 2026-09-14, unit: minute }',
         "parties[ali].accepted.unit is `minute`, and a date is held to `day`"),
        ("its `at` is in the form of the system it names", '{ system: persian-calendar, at: 2026-09-14, unit: day }',
         "is not in the one canonical form 'persian-calendar' declares"),
        ("it holds only what an entry of `timing` declares", '{ system: gregorian-civil, at: 2026-09-14, unit: day, said: "yes" }',
         "carries `said`, which the term `timing` does not declare"),
        ("a day its calendar lacks is no date, written long as short", '{ system: persian-calendar, at: "persian:1404-12-30", unit: day }',
         "is no day of persian-calendar"),
        ("a clock reading on a date is finer than the type", '{ system: gregorian-civil, at: "2026-09-14 10:00+03:00", unit: day }',
         "parties[ali].accepted.at '2026-09-14 10:00+03:00' must be an ABSOLUTE date"),
        ("a position with no `at` is none", '{ system: gregorian-civil, unit: day }', "missing ['at']"),
        ("a neighbour is written as itself, never as a placeholder in angle brackets",
         '{ system: event-anchored, at: "after:<what it followed>", unit: day }',
         "is not in the one canonical form 'event-anchored' declares"),
):
    out = gate(ali=ali)
    check("the long form is refused where the short would be: " + why, want in out and " 1 error(s)" in out, out[-900:])
out = gate(due='{ system: gregorian-civil, at: 2099-01-15, unit: hour }')
check("...and a `date_or_moment` written long is held to a day, or to a minute or finer — not to the hour",
      "clauses[first].due.unit is `hour`, and a date_or_moment is held to `day` or `minute` or finer" in out, out[-700:])

# ---- consent: without an acceptance, the refusal names the long form -------------------------------------------------
_nodate = LOAN.replace("role: borrower, accepted: %(ali)s", "role: borrower")
open(os.path.join(BEANS, "phone-loan.md"), "w").write(_nodate % {"due": DUE})
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
out = out.stdout + out.stderr
check("a party with no `accepted` has no acceptance on record, and Ali is not kept by name on it — the message says how "
      "a yes nobody dated is written", "ali: names a person who is not the gardener, and no consent of theirs is recorded" in out
      and 'system: event-anchored, at: "after:<what it followed>", unit: day' in out, out[-900:])

# ---- the readers read the long form as the short, and say a day placed by its neighbours names none -------------------
gate()
led = run(sys.executable, os.path.join(G, "bin", "dmledger.py"), "phone-loan", cwd=G)
lo = led.stdout + led.stderr
check("the ledger shows a transaction's day written long as the day", led.returncode == 0 and "the-loan  2026-09-15" in lo
      and "{system" not in lo, lo[-900:])
check("...a due written long as its day, and one placed by what it followed as that, with no day reckoned",
      "due 2099-01-15" in lo and "due after the day her shop opens — placed by what it follows, on no day this can reckon" in lo,
      lo[-900:])
st = run(sys.executable, os.path.join(G, "bin", "dmstale.py"), cwd=G)
so = st.stdout + st.stderr
check("what falls due reads a due written long as the day it names", st.returncode == 0
      and re.search(r"OK +phone-loan\.clauses\[first\] +due 2099-01-15", so), so[-900:])
check("...and says of one placed by what it followed that it falls on no day it can reckon — never a traceback, never "
      "a guessed day", re.search(r"NOTE +phone-loan\.clauses\[second\] +due after the day her shop opens — placed by what it "
                                 r"follows, on no day this can reckon", so) and "Traceback" not in so, so[-900:])

sys.path.insert(0, os.path.join(G, "bin"))
import dmcal, dmreckon  # noqa: E402
_long = {"system": "gregorian-civil", "at": "2026-09-20", "unit": "day"}
_after = {"system": "event-anchored", "at": "after:the call", "unit": "day", "note": "nobody said"}
check("one reader: a day written long is the day its short form names, in any calendar",
      dmcal.to_day(_long) == dmcal.to_day("2026-09-20")
      and dmcal.to_day({"system": "persian-calendar", "at": "persian:1405-06-29", "unit": "day"}) == dmcal.to_day("persian:1405-06-29")
      and dmcal.moment({"system": "gregorian-civil", "at": "2026-09-20 14:05+03:30", "unit": "minute"})
      == dmcal.moment("2026-09-20 14:05+03:30"))
try:
    dmcal.to_day(_after)
    _un = None
except dmcal.Unplaced as e:
    _un = str(e)
check("...one placed by its neighbours raises Unplaced, a ValueError, saying what it follows", _un is not None
      and issubclass(dmcal.Unplaced, ValueError) and "after the call" in _un, _un)
check("...and is shown as words, never as a mapping", dmcal.shown(_after) == "after the call" and dmcal.shown(_long) == "2026-09-20"
      and dmcal.shown("2026-09-20") == "2026-09-20")
check("the reckoner reads a day written long as the short one, and one placed by its neighbours as no position",
      dmreckon._pos(_long, None, []) == dmreckon._pos("2026-09-20", None, []) and dmreckon._pos(_after, None, []) is None
      and dmreckon.value_of(_long, "x", []).v == "2026-09-20" and dmreckon.value_of(_after, "x", []).v is None)

# ---- iso_date is retired: refused with where it went, and translated ---------------------------------------------------
v = os.path.join(G, "VOCAB.md")
_voc = open(v).read()
open(v, "w").write(_voc.replace("local_terms: []", """local_terms:
  - term: rental
    meaning: "what a rented machine is rented from, and when the rent next falls due"
    context_keys: [rental]
    schema:
      shape: mapping
      attrs:
        provider: { required: true, in: prose, meaning: "who it is rented from" }
        renews:   { required: true, in: { type: iso_date }, meaning: "the day the next payment is due" }
    merge: { cardinality: single, order: none }""", 1))
open(os.path.join(BEANS, "box.md"), "w").write(HEAD.format(bean="box", genos="host", nature="soma").replace(
    'value: "host:box", class: logical', 'value: "SN-1", class: hardware').replace("key: identifier", "key: serial") + """\
owned_by: { legal: { external: "a hosting company" } }
responsibility: { legal: { external: "a hosting company" } }
rental: { provider: "a hosting company", renews: 2027-01-15 }
---
A rented machine.
""")
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
out = out.stdout + out.stderr
check("a garden's own term typed `iso_date` is refused, and the refusal says where the type went",
      "type 'iso_date' is not declared in `value_types`" in out and "retired: `date`" in out, out[-900:])
import dmupgrade  # noqa: E402
_new, _done = dmupgrade.renamed(open(v).read(), dmupgrade.vocab_rule_27)
check("...and the upgrade's 27.0 step types it `date`, touching nothing else",
      "in: { type: date }" in _new and "iso_date" not in _new and len(_done) == 1, _done)
open(v, "w").write(_new)
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
out = out.stdout + out.stderr
check("...after which the same bean passes: every Gregorian day the old type held, `date` holds",
      " 0 error(s)" in out, out[-600:])

rules = run(sys.executable, os.path.join(G, "bin", "dmrules.py"), cwd=G).stdout
check("the rules a garden prints say a day may be written long", re.search(
    r"^  date +a position to the day in any system of time — or written long, as one entry of `timing` at that unit$", rules, re.M))
check("...and that a length along place is measured, as one along time is: place in length, time in time",
      re.search(r"^  place +sequence +lines open · metered length", rules, re.M)
      and re.search(r"^  time +sequence +lines 1 · metered time", rules, re.M), [l for l in rules.splitlines() if "sequence " in l])

# ---- a moment is in time and in place ----------------------------------------------------------------------------------
DIN = os.path.join(BEANS, "dinner-at-sams.md")
_din = open(DIN).read()
_START = 'start: { system: gregorian-civil, at: "2026-09-12 19:30+03:00", unit: minute }'


def moment(start):
    open(DIN, "w").write(_din.replace(_START, start))
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr


out = moment('start: { system: gregorian-civil, at: "2026-09-12 19:30+03:30", unit: minute, '
             'where: { system: geographic, at: "EPSG:4326;35.6892,51.3890", zone: Asia/Tehran, u: { count: 50, unit: metre } } }')
check("a moment says where it was, beside its time in one entry — and a day written long does too (Sam's yes, in IR)",
      " 0 error(s)" in out, out[-700:])
for why, start, want in (
        ("a place is a position in a system of PLACE", 'start: { system: gregorian-civil, at: "2026-09-12 19:30+03:30", '
         'unit: minute, where: { system: persian-calendar, at: "persian:1405-06-21" } }', "is not a declared anchor_systems where dimension is place"),
        ("in that system's one form", 'start: { system: gregorian-civil, at: "2026-09-12 19:30+03:30", unit: minute, '
         'where: { system: iso-3166, at: "Iran" } }', "is not in the one canonical form 'iso-3166' declares"),
        ("and holds nothing that is a being's alone — whether it can be reached", 'start: { system: gregorian-civil, '
         'at: "2026-09-12 19:30+03:30", unit: minute, where: { system: iso-3166, at: IR, openness: here } }', "carries `openness`")):
    out = moment(start)
    check("a moment's place is refused where a place would be: " + why, want in out and " 1 error(s)" in out, out[-700:])

moment('start: { system: gregorian-civil, at: "2026-09-12 19:30+03:00", unit: minute, where: { system: iso-3166, at: IR, zone: Asia/Tehran } }\n'
       '  end: { system: gregorian-civil, at: "2026-09-12 22:30+03:30", unit: minute, where: { system: iso-3166, at: IR, zone: Asia/Tehran } }')
wh = run(sys.executable, os.path.join(G, "bin", "dmwhere.py"), cwd=G)
wo = wh.stdout + wh.stderr
try:
    dmcal.offset("Asia/Tehran", "2026-09-12 19:30+03:00")
    _zones = True
except dmcal.NoZoneData:
    _zones = False
if _zones:
    check("the location resolver reads a moment's offset against the zone in force at its place: +03:00 in Tehran in "
          "September 2026 disagrees, and says so, and the tool exits 1 — +03:30 agrees",
          wh.returncode == 1 and re.search(r"OFFSET-DISAGREES dinner-at-sams timing\.start .*written at \+03:00, and "
                                           r"Asia/Tehran kept \+03:30", wo)
          and re.search(r"OFFSET-OK +dinner-at-sams timing\.end", wo), wo[-900:])
else:
    check("with no zone database on this machine the resolver says so, and guesses no offset", "NO-ZONE-DATA" in wo, wo[-900:])
_g = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
check("...and the gate, which reads no zone database, passes the same garden: its verdict never depends on a machine",
      " 0 error(s)" in _g.stdout + _g.stderr, (_g.stdout + _g.stderr)[-500:])
open(DIN, "w").write(_din)

# ---- a meter is a system's own; a day that begins somewhere is read from a place -----------------------------------------
_voc = open(v).read()
def systems(rows):
    open(v, "w").write(_voc.replace("local_gene: []", "local_gene: []\nregistry_additions:\n  anchor_systems:\n" + rows, 1))
    # the system is a position the garden declares, so a bean occupies it: the dinner as the hobbits dated it
    open(DIN, "w").write(_din.replace(_START, _START + '\n  told: { system: shire-reckoning, at: "shire:1420-100", unit: day }'))
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr
ROW = """    - system: shire-reckoning
      dimension: time
      calendar: shire
      reckoning: tabulated
      day_begins: sunset
%s      levels: [ { level: year }, { level: day, unit: day } ]
      neighbours: metered
      restrictions: { lines: 1, order: partial%s }
      meaning: "a probe calendar"
      pattern: '^shire:[0-9]{4}-[0-9]{3}$'
      establishes: false
      why: "a probe"
"""
out = systems(ROW % ("      resolves_through: geographic\n", ", metered: time"))
check("a garden's own calendar that states its meter and the place its day begins in passes", " 0 error(s)" in out, out[-700:])
out = systems(ROW % ("      resolves_through: geographic\n", ""))
check("...one whose neighbours are metered and which states no meter is refused: a system inherits none from its aspect",
      "its neighbours are `metered`, and it states no meter" in out, out[-700:])
out = systems(ROW % ("", ", metered: time"))
check("...and one whose day begins at a moment of some place, and which resolves through none, is refused: no time is "
      "absolute", "its day begins at sunset, a moment of some place, and it resolves" in out, out[-700:])
open(v, "w").write(_voc)
open(DIN, "w").write(_din)

shutil.rmtree(T, ignore_errors=True)
print("\ndays: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
