#!/usr/bin/env python3
"""expiry — a term declares which of its dates runs out, and the tool reads the LAW to find them.

WHY THIS EXISTS. `bin/dmstale.py` named `registration` and `expires` in its own source. That was never
decided: the term was born in one garden's local vocabulary and the tool was extended for it the same
day, and when the term was PROMOTED to Tier-0 nobody came back. A cold-start drill found the cost in
fifteen minutes — a stranger declared its own `rental` term for a rented server, the GATE enforced its
date exactly (refusing "early October", refusing a missing attr, citing the garden's own VOCAB as the
authority), and dmstale said nothing at all about a renewal thirteen days away. First-class to the gate,
invisible to the tool. Its verdict turned on it: "the best feature in the system only works on facts the
maintainers anticipated."

So this asserts the two halves that must both hold:
  +  a GARDEN'S OWN term with `schema.expiry` is warned about, exactly as Tier-0's registration is
  -  a term WITHOUT the declaration is never warned about, however many iso_date attrs it carries —
     nine of the ten dates in the standard are `observed` or `as_of`, and a tool that warned about all
     of them would be wrong nine times in ten
"""
import os, re, sys, subprocess, tempfile, shutil, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:600]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmexp-")
G = os.path.join(T, "g")
run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)

def stale(*args):
    return run(sys.executable, os.path.join(G, "bin", "dmstale.py"), *args, cwd=G).stdout

OWN = ('owned_by: { legal: { owner: { bean: keeper } } }\n'
       'responsibility: { legal: { holder: { bean: keeper } } }\n')
open(os.path.join(G, "beans", "keeper.md"), "w").write(
    '---\nbean: keeper\nkind: person\ntitle: "the keeper"\nstatus: active\nsummary: "p"\nnature: living\n'
    'identity: { status: confirmed, anchors: [ { key: person_id, value: "person:keeper", class: logical, '
    'establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { crown: love } }\nresponsibility: { legal: { self: true } }\n---\nA person.\n')

# ---- a GARDEN'S OWN term, the drill's case, reproduced -------------------------------------------------
# Declared in local_terms with an expiry, exactly as a stranger would write it after reading
# `schema_language` — no release, no code, no Tier-0 involvement.
SOON = (datetime.date.today() + datetime.timedelta(days=13)).isoformat()
FAR  = (datetime.date.today() + datetime.timedelta(days=900)).isoformat()

def vocab(term_yaml):
    v = os.path.join(G, "VOCAB.md")
    s = open(v, encoding="utf-8").read()
    # the template's line carries a trailing comment, so match the KEY and replace the whole line
    s = re.sub(r'^local_terms: \[\].*$', 'local_terms:\n' + term_yaml.rstrip('\n'), s, count=1, flags=re.M)
    assert 'local_terms:\n' in s, "VOCAB.md template no longer holds `local_terms: []`"

    open(v, "w", encoding="utf-8").write(s)

RENTAL = """  - term: rental
    meaning: "what a rented machine costs and when it next charges"
    context_keys: ["rental"]
    schema:
      shape: mapping
      attrs:
        provider: { required: true, in: prose }
        renews:   { required: true, in: { type: date } }
        period:   { in: extent }
      expiry:
        attr: renews
        notice: { of: time, measure: { count: 30, unit: day } }
        why: "a rental that lapses takes the machine with it"
    merge: { cardinality: single, order: none }
"""
vocab(RENTAL)

def host(rental_block, bean="vps"):
    open(os.path.join(G, "beans", f"{bean}.md"), "w").write(
        f'---\nbean: {bean}\nkind: virtual-host\ntitle: "a rented machine"\nstatus: active\nsummary: "s"\n'
        'nature: living\n'
        'identity: { status: confirmed, anchors: [ { key: fqdn, value: "' + bean + '.example.org", '
        'class: logical, establishing: true } ] }\n'
        'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n' + OWN + rental_block +
        f'---\nA machine.\n')

host(f'rental: {{ provider: "someone", renews: "{SOON}" }}\n')
out = stale()
check("a GARDEN'S OWN term with an expiry is warned about — no release, no code",
      "EXPIRING" in out and "vps.rental" in out and "renews " + SOON in out, out[-700:])
check("...and the warning carries the CONSEQUENCE the term declared, not just a date",
      "a rental that lapses takes the machine with it" in out, out[-700:])

# NO CALENDAR IS PRIVILEGED (16.0): the same rent, dated in the calendar its contract is written in, ages the same way.
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmcal as _dmcal
_soon_fa = _dmcal.convert(SOON, "persian")
host(f'rental: {{ provider: "someone", renews: "{_soon_fa}" }}\n')
out = stale()
check("an expiry stated in the Persian calendar is aged THROUGH THE DAY, exactly as a Gregorian one is",
      "EXPIRING" in out and "vps.rental" in out and "13 day" in out, out[-700:])
host(f'rental: {{ provider: "someone", renews: "islamic:1448-05-01" }}\n')
check("...and one in a calendar that is NOT reckoned by rule is left alone rather than guessed at",
      "vps.rental" not in stale() and "Traceback" not in stale(), stale()[-500:])

# The term's own horizon governs: 13 days is inside rental's 30 and would be inside a domain's 90 too,
# so push it out to a date only the term's own horizon could judge.
host(f'rental: {{ provider: "someone", renews: "{FAR}" }}\n')
check("a date beyond the TERM's own horizon is quiet", "EXPIRING" not in stale(), stale()[-400:])
check("...and --days overrides every term's horizon at once",
      "EXPIRING" in stale("--days", "1000") and "overriding every term" in stale("--days", "1000"),
      stale("--days", "1000")[-500:])

# ---- the negative half: silence is not free, it is DECLARED --------------------------------------------
# Take the SAME term and delete only its two `expiry:` lines — nothing else moves, so the difference
# between warned-about and silent is exactly the declaration and cannot be anything else.
v = os.path.join(G, "VOCAB.md")
_s = open(v, encoding="utf-8").read()
_DECL = ('      expiry:\n        attr: renews\n        notice: { of: time, measure: { count: 30, unit: day } }\n        why: "a rental that lapses takes the machine with it"\n')
assert _DECL in _s, "the expiry declaration was not where this test put it"
open(v, "w", encoding="utf-8").write(_s.replace(_DECL, ""))
host(f'rental: {{ provider: "someone", renews: "{SOON}" }}\n')
out = stale()
check("a term WITHOUT the declaration is never warned about, though its date is an enforced iso_date",
      "vps.rental" not in out, out[-500:])
check("...and the gate still enforces that date, so the silence is the TOOL's, not a gap in the law",
      "0 error" in run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout,
      "gate should pass")

# ---- and the standard's own dates stay quiet, which is why this is not inferred from iso_date ----------
import yaml
sys.path.insert(0, os.path.join(G, "bin"))
import dmparse
sv = yaml.safe_load(dmparse.read(os.path.join(G, "seed", "std-vocab.md"))[0])
terms = list(sv["terms"]) + [x for p in sv["profiles"].values() for x in p["terms"]]
dated, declared = [], []
for t_ in terms:
    s = (t_.get("schema") or {})
    if [k for k, v in (s.get("attrs") or {}).items()
        if isinstance((v or {}).get("in"), dict) and v["in"].get("type") in ("date", "iso_date")]:
        dated.append(t_["term"])
    if (s.get("expiry") or {}).get("attr"):
        declared.append(t_["term"])
check("the standard carries many dates and declares few expiries — the reason nothing is inferred",
      len(dated) > len(declared) and declared, f"dated={sorted(dated)} declared={sorted(declared)}")

# ---- EXTENT: the region `figures` declared possible, and every rule read from the aspect ---------------
# Each negative below is refused for a reason the ASPECT gives, not one written into the gate — which is
# the whole claim. A new aspect gets regions with no code change; an aspect that should not have them
# refuses them in its own words.
def period(block, bean="vps2"):
    open(os.path.join(G, "beans", f"{bean}.md"), "w").write(
        f'---\nbean: {bean}\nkind: virtual-host\ntitle: "a rented machine"\nstatus: active\nsummary: "s"\n'
        'nature: living\n'
        'identity: { status: confirmed, anchors: [ { key: fqdn, value: "' + bean + '.example.org", '
        'class: logical, establishing: true } ] }\n'
        'provenance: { src: observed, by: t, as_of: 2026-01-01 }\n' + OWN +
        f'rental: {{ provider: "someone", renews: "{FAR}", period: {block} }}\n'
        '---\nA machine.\n')
    return run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout

# put the declaration back for this half
_s = open(v, encoding="utf-8").read()
if "expiry:" not in _s:
    _anchor = "        period:   { in: extent }\n"
    assert _s.count(_anchor) == 1, "the anchor this test restores the declaration after has moved"   # a replace that
    open(v, "w", encoding="utf-8").write(_s.replace(_anchor, _anchor + _DECL))                        # matches nothing is a bug

check("a LENGTH with no fixed ends is a region — 'for N days', which most real durations are",
      "0 error" in period('{ of: time, measure: { count: 204, unit: day } }'),
      period('{ of: time, measure: { count: 204, unit: day } }')[-400:])
check("...and so is a region bounded at both ends",
      "0 error" in period('{ of: time, from: "2026-01-01", to: "2026-03-31" }'),
      period('{ of: time, from: "2026-01-01", to: "2026-03-31" }')[-400:])
check("...and one open at an end",
      "0 error" in period('{ of: time, from: "2026-01-01" }'),
      period('{ of: time, from: "2026-01-01" }')[-400:])

out = period('{ of: time }')
check("a region with neither bound and no length is refused", "at least one of from / to / measure" in out,
      out[-400:])
out = period('{ of: necessity, measure: { count: 3, unit: day } }')
check("a region on an OPPOSITION is refused IN THE FIGURE'S OWN WORDS — modalities have no between",
      "carries no region" in out and "modalities" in out, out[-400:])
out = period('{ of: walk, measure: { count: 3, unit: day } }')
check("a length on an UNMETERED aspect is refused — a stretch of a walk has no duration",
      "metered: none" in out, out[-400:])
out = period('{ of: time, measure: { count: 1, unit: month } }')
check("a unit the registry does not hold is refused — a month is 28 to 31 days and is not a measure",
      "not in the `units` registry" in out, out[-400:])
out = period('{ of: time, measure: { count: 0, unit: day } }')
check("a non-positive count is refused", "positive whole number" in out, out[-400:])
out = period('{ of: time, from: "early October" }')
check("a boundary that is no position in the aspect's domain is refused",
      "is not a position in any system" in out, out[-400:])
out = period('{ of: teleportation, measure: { count: 1, unit: day } }')
check("an aspect that does not exist is refused, and the message lists the ones that do",
      "names no aspect" in out, out[-400:])

# ---- and the LAW's own extents are judged by the same rule -------------------------------------------
# Put a VALID region back first: the last negative left a broken bean, and an error from it would mask
# the one this check is about — a test that passes on the wrong error has proved nothing.
period('{ of: time, measure: { count: 204, unit: day } }')
# The garden's OWN term is the right target: this garden does not opt into the `domain` profile, so
# Tier-0's `registration` is not in force here — and a check that fired only on the standard would miss
# exactly the case this release is for, which is a garden writing its own rule.
_v = open(v, encoding="utf-8").read()
open(v, "w", encoding="utf-8").write(
    _v.replace("notice: { of: time, measure: { count: 30, unit: day } }",
               "notice: { of: time, measure: { count: 30, unit: fortnight } }", 1))
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout
check("an extent the LAW ITSELF writes is checked — a rule the gate cannot see is the defect, not the fix",
      "VOCAB rental.schema.expiry.notice" in out and "units` registry" in out, out[-500:])
open(v, "w", encoding="utf-8").write(_v)

# ---- OBLIGATIONS (21.0): an expiry on a term of ENTRIES is each entry's -----------------------------------
# An agreement's clauses are an open map, and the law's `clauses` term declares its expiry per entry: `due`, repeating
# by `every`, silenced by `state: met | waived | broken`, with a notice of seven days. Nothing here names the term.
open(os.path.join(G, "beans", "ali.md"), "w").write(
    '---\nbean: ali\nkind: person\ntitle: "ali"\nstatus: active\nsummary: "p"\nnature: living\n'
    'identity: { status: confirmed, anchors: [ { key: person_id, value: "person:ali", class: logical, establishing: true } ] }\n'
    'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\n'
    'owned_by: { legal: { crown: love } }\nresponsibility: { legal: { self: true } }\n---\nA person.\n')
today = datetime.date.today()
IN3 = (today + datetime.timedelta(days=3)).isoformat()
IN10 = (today + datetime.timedelta(days=10)).isoformat()
# a day one to six days ahead that every month has, and the same day of the month before it: a monthly clause first due
# then falls due next on it — inside the notice, though its first due date is weeks gone
for _k in range(1, 7):
    NEXT = today + datetime.timedelta(days=_k)
    if NEXT.day <= 28:
        break
FIRST = (NEXT.replace(day=1) - datetime.timedelta(days=1)).replace(day=NEXT.day)
open(os.path.join(G, "beans", "deal.md"), "w").write(f"""---
bean: deal
kind: contract
title: "an agreement"
status: active
summary: "what ali owes the keeper"
nature: metaphysical
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: contract_id, value: "contract:deal", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: t, as_of: 2026-01-01 }}
parties:
  keeper: {{ who: {{ bean: keeper }} }}
  ali: {{ who: {{ bean: ali }} }}
words: {{ form: spoken }}
clauses:
  soon:    {{ what: "ali repays the keeper", by: ali, to: keeper, due: {IN3} }}
  paid:    {{ what: "a deposit", by: ali, to: keeper, due: {IN3}, state: met }}
  later:   {{ what: "a second payment", by: ali, to: keeper, due: {IN10} }}
  monthly: {{ what: "ali pays each month", by: ali, to: keeper, due: {FIRST.isoformat()}, every: {{ of: time, in: gregorian-civil, each: month }} }}
  once:    {{ what: "ali pays once", by: ali, to: keeper, due: {FIRST.isoformat()} }}
  moon:    {{ what: "ali pays by the moon", by: ali, to: keeper, due: 2026-01-01, every: {{ of: time, in: islamic-calendar, each: month }} }}
---
An agreement.
""")
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout
check("an agreement whose clauses fall due passes the gate", "0 error" in out, out[-800:])
out = stale()
line = lambda key: next((l for l in out.splitlines() if f"deal.clauses[{key}]" in l), "")
check("a clause due within its notice warns — each ENTRY by itself, with the consequence the term declares",
      line("soon").startswith("EXPIRING") and IN3 in line("soon") and "a clause falls due" in line("soon"), out[-900:])
check("...a `met` one is silent: the law's `unless` names a debt already met", line("paid") == "", out[-900:])
check("...one beyond the TERM's notice (seven days) is quiet", line("later").startswith("OK"), out[-900:])
check("a monthly clause warns before its NEXT occurrence, though its first due date is weeks gone",
      line("monthly").startswith("EXPIRING") and NEXT.isoformat() in line("monthly") and "occurrence 2" in line("monthly"), out[-900:])
check("...where the same date that does not repeat is EXPIRED — the repetition is what moved it", line("once").startswith("EXPIRED"), out[-900:])
check("...and one counted in a calendar that is not reckoned by rule is a NOTE, never a guess",
      line("moon").startswith("NOTE") and "not by rule" in line("moon") and "Traceback" not in out, out[-900:])

# ---- THE WALK ITSELF, on fixed days: the library bin/dmledger.py shares -------------------------------------------------
# Asked in-process of this garden's own copy, so the systems and units are the law this garden loaded, and `today` is a
# fixed day rather than the clock's — each answer below is one a person can check on a calendar.
import time
import dmstale as _st
_d = _dmcal.to_day
def nd(first, rec, today, skipped=None):
    return _st.next_due(_d(first), dict(rec, of="time"), _d(today), skipped=skipped)
# A refusal is asked in a process of its own, with a deadline: the defect it guards against was a walk that never ended,
# and a suite that hangs on the regression it exists to catch reports nothing.
_PROBE = r"""
import json, sys, time
sys.path.insert(0, 'bin')
import dmcal, dmstale
first, rec, today = json.loads(sys.argv[1])
t0 = time.time()
try:
    dmstale.next_due(dmcal.to_day(first), rec, dmcal.to_day(today))
    print(json.dumps(['no refusal', time.time() - t0]))
except dmstale.Unreckoned as e:
    print(json.dumps([str(e), time.time() - t0]))
"""
def unreckoned(first, rec, today="2026-09-23"):
    import json
    try:
        r = subprocess.run([sys.executable, "-c", _PROBE, json.dumps([first, dict(rec, of="time"), today])],
                           capture_output=True, text=True, cwd=G, timeout=30)
    except subprocess.TimeoutExpired:
        return "did not end in 30 seconds", 30.0
    return tuple(json.loads(r.stdout)) if r.stdout.strip() else (r.stderr[-300:], 0.0)

YEARLY = {"in": "gregorian-civil", "each": "year", "at": "12-01"}
check("a YEARLY clause first due 2026-01-10 at 12-01 falls due next on 2026-12-01 — in its own first year, not a year late",
      nd("2026-01-10", YEARLY, "2026-09-23")[:2] == (_d("2026-12-01"), 2), nd("2026-01-10", YEARLY, "2026-09-23"))
check("...and with `times: 2`, 2026-12-01 is the second payment and the last",
      nd("2026-01-10", dict(YEARLY, times=2), "2026-12-02") == (_d("2026-12-01"), 2, 2, True))
check("...as a month and a week always did: a later place in the first's own cell is the next occurrence",
      nd("2026-01-10", {"in": "gregorian-civil", "each": "month", "at": "15"}, "2026-01-11")[:2] == (_d("2026-01-15"), 2)
      and nd("2026-09-01", {"in": "iso-week", "each": "week", "at": "5"}, "2026-09-02")[:2] == (_d("2026-09-04"), 2))

# A PLACE NO CELL HAS. The gate cannot refuse it (`at` is prose to the gate), and the walk once never ended on one.
_never = [({"in": "coptic-calendar", "each": "month", "at": "31"}, "(the longest runs to 30)"),
          ({"in": "hebrew-calendar", "each": "month", "at": "31"}, "(the longest runs to 30)"),
          ({"in": "gregorian-civil", "each": "month", "at": "32"}, "(the longest runs to 31)"),
          ({"in": "gregorian-civil", "each": "month", "at": "0"}, "place 0"),
          ({"in": "gregorian-civil", "each": "year", "at": "02-30"}, "place 02-30"),
          ({"in": "gregorian-civil", "each": "year", "at": "00-00"}, "place 00-00"),
          ({"in": "iso-week", "each": "week", "at": "8"}, "(the longest runs to 7)")]
_got = [(r, want) + unreckoned("2026-01-31", r) for r, want in _never]
check("a place no cell of the calendar has — the 31st of a Coptic or Hebrew month, the 32nd, the 0th, 02-30, day 8 of a week — "
      "ENDS, in well under a second each, and says why",
      all(want in why and "a place its calendar does not have" in why and secs < 2 for r, want, why, secs in _got),
      [(r["in"], r["at"], why[:120], round(secs, 2)) for r, want, why, secs in _got])

# A CELL WITHOUT THE PLACE IS SKIPPED — and the reader is told, rather than left to wonder about November.
_sk = []
_nd = nd("2026-01-31", {"in": "gregorian-civil", "each": "month"}, "2026-11-20", _sk)
check("rent first due 2026-01-31, read on 2026-11-20: next 2026-12-31, and November — which has no 31st — is NAMED as skipped",
      _nd[0] == _d("2026-12-31") and [c[2] for c in _sk] == ["2026-11"] and "no occurrence in 2026-11 — it has no 31" in _st.skip_words(_sk[0]),
      (_nd, _sk))

# THE LEVELS ARE THE LAW'S: no calendar is named in the tool, so a Japanese month is walked from its own form, and a week
# only where the system has one.
check("a Japanese month is walked from the calendar's own form: the 15th after 2026-09-23 is 2026-10-15",
      nd("2026-01-01", {"in": "japanese-calendar", "each": "month", "at": "15"}, "2026-09-23")[0] == _d("2026-10-15"))
check("...a system without the level named is refused in the law's words",
      "gregorian-civil has no level `week`" in unreckoned("2026-01-01", {"in": "gregorian-civil", "each": "week"})[0])
_src = open(os.path.join(G, "bin", "dmstale.py"), encoding="utf-8").read()
check("...and dmstale's source names neither `japanese` nor `iso8601`", "'japanese'" not in _src and "'iso8601'" not in _src)
check("a stride whose count is a decimal STRING is read (`count: \"2\"`), and one that is not a whole number of days is said "
      "to be that — not 'finer than the day'",
      nd("2026-01-01", {"every": {"count": "2", "unit": "day"}}, "2026-01-02")[0] == _d("2026-01-03")
      and "not a whole number of days" in unreckoned("2026-01-01", {"every": {"count": 2160, "unit": "minute"}})[0])

# ---- AND THE TOOLS, on a garden holding such clauses ------------------------------------------------------------------
line = lambda key, bean="odd": next((l for l in out.splitlines() if f"{bean}.clauses[{key}]" in l), "")
open(os.path.join(G, "beans", "odd.md"), "w").write(f"""---
bean: odd
kind: contract
title: "an agreement with places no calendar has"
status: active
summary: "clauses the gate accepts and the walk must end on"
nature: metaphysical
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: contract_id, value: "contract:odd", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: t, as_of: 2026-01-01 }}
parties:
  keeper: {{ who: {{ bean: keeper }} }}
  ali: {{ who: {{ bean: ali }} }}
words: {{ form: spoken }}
clauses:
  coptic:  {{ what: "rent", by: ali, to: keeper, due: 2026-01-31, every: {{ of: time, in: coptic-calendar, each: month, at: "31" }} }}
  feb-30:  {{ what: "a fee", by: ali, to: keeper, due: 2026-01-31, every: {{ of: time, in: gregorian-civil, each: year, at: "02-30" }} }}
  leap:    {{ what: "a leap-day fee", by: ali, to: keeper, due: 2024-02-29, every: {{ of: time, in: gregorian-civil, each: year }} }}
---
An agreement.
""")
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout
check("the gate accepts clauses whose place no calendar has (`at` is prose to it) — so the tools must end on them",
      "0 error" in out, out[-600:])
try:
    r = subprocess.run([sys.executable, os.path.join(G, "bin", "dmstale.py")], capture_output=True, text=True, cwd=G, timeout=60)
    out, ended = r.stdout, True
except subprocess.TimeoutExpired:
    out, ended = "(killed after 60 s)", False
check("...dmstale ENDS on them, each a NOTE with the reason", ended and "Traceback" not in out
      and line("coptic").startswith("NOTE") and "a place its calendar does not have" in line("coptic")
      and line("feb-30").startswith("NOTE"), out[-900:])
check("...and a leap-day fee names the years it skips beside its row",
      any(l.startswith("NOTE") and "odd.clauses[leap]" in l and "it has no 02-29" in l for l in out.splitlines()), out[-900:])
try:
    r = subprocess.run([sys.executable, os.path.join(G, "bin", "dmledger.py"), "odd"], capture_output=True, text=True, cwd=G, timeout=60)
    lout, ended = r.stdout + r.stderr, True
except subprocess.TimeoutExpired:
    lout, ended = "(killed after 60 s)", False
check("...and so does dmledger, which walks with the same function", ended and "Traceback" not in lout
      and "cannot be walked here" in lout and "NOTE no occurrence in" in lout, lout[-900:])
os.remove(os.path.join(G, "beans", "odd.md"))

# ---- A DAY THAT DOES NOT EXIST, AND A DAY NO READER CAN WRITE: each a NOTE, and every other warning still printed ------
# Written in the working tree, where these tools read: the gate refuses most of them, and a reader must not die on what the
# gate would refuse, nor let one entry cost the garden every other warning — `deal`'s clause due in three days among them.
_BEGIN = (FIRST.replace(day=1) + datetime.timedelta(days=40)).replace(day=FIRST.day)      # a month after FIRST, same day
_LATER = (today + datetime.timedelta(days=200)).isoformat()                              # past every term's horizon
open(os.path.join(G, "beans", "beyond.md"), "w").write(f"""---
bean: beyond
kind: contract
title: "an agreement whose days are not all days"
status: active
summary: "clauses a reader must end on, and say it could not read"
nature: metaphysical
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: contract_id, value: "contract:beyond", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: t, as_of: 2026-01-01 }}
parties:
  keeper: {{ who: {{ bean: keeper }} }}
  ali: {{ who: {{ bean: ali }} }}
words: {{ form: spoken }}
clauses:
  feb-30:    {{ what: "a fee", by: ali, to: keeper, due: '2026-02-30' }}
  esfand-30: {{ what: "rent", by: ali, to: keeper, due: 'persian:1404-12-30', every: {{ of: time, in: persian-calendar, each: month }} }}
  far-year:  {{ what: "rent", by: ali, to: keeper, due: 'hebrew:1000000000000000-01-01', every: {{ of: time, in: hebrew-calendar, each: month }} }}
  stride:    {{ what: "rent", by: ali, to: keeper, due: 2026-09-01, every: {{ of: time, in: gregorian-civil, every: {{ count: 3000000, unit: day }} }} }}
  day-count: {{ what: "a fee", by: ali, to: keeper, due: 'jdn:99999999999' }}
  day-zero:  {{ what: "a fee", by: ali, to: keeper, due: 'jdn:0' }}
  begins:    {{ what: "rent", by: ali, to: keeper, due: {FIRST.isoformat()}, every: {{ of: time, in: gregorian-civil, each: month, from: {_BEGIN.isoformat()} }} }}
  disputed:  {{ conflict: [ {{ what: "rent", by: ali, to: keeper, due: '2026-02-30' }},
                            {{ what: "rent", by: ali, to: keeper, due: 2026-09-01, every: {{ of: time, in: gregorian-civil, every: {{ count: 3000000, unit: day }} }} }},
                            {{ what: "rent", by: ali, to: keeper, due: {_LATER} }} ] }}
  unwalkable: {{ conflict: [ {{ what: "a fee", by: ali, to: keeper, due: 'jdn:99999999999' }},
                             {{ what: "a fee", by: ali, to: keeper, due: '{"9" * 200}' }} ] }}
---
An agreement.
""")
try:
    r = subprocess.run([sys.executable, os.path.join(G, "bin", "dmstale.py")], capture_output=True, text=True, cwd=G, timeout=60)
    out, ended = r.stdout + r.stderr, True
except subprocess.TimeoutExpired:
    out, ended = "(killed after 60 s)", False
line = lambda key, bean="beyond": next((l for l in out.splitlines() if f"{bean}.clauses[{key}]" in l), "")
check("dmstale ENDS on a day that does not exist and on days beyond 9999 — no traceback, no hang",
      ended and "Traceback" not in out, out[-900:])
check("...a day its calendar does not have is a NOTE saying so — never dropped in silence, never moved to the day after",
      line("feb-30").startswith("NOTE") and "not a day of the Gregorian calendar" in line("feb-30")
      and line("esfand-30").startswith("NOTE") and "persian:1405-01-01" in line("esfand-30") and "not a day of the persian" in line("esfand-30"),
      [line("feb-30"), line("esfand-30")])
check("...a year of sixteen digits, and a day count of eleven, are NOTEs: outside the days reckoned",
      all(line(k).startswith("NOTE") and "outside the days reckoned here" in line(k) for k in ("far-year", "day-count")),
      [line("far-year"), line("day-count")])
check("...a stride that lands past 9999-12-31 is a NOTE: no reader could write the day",
      line("stride").startswith("NOTE") and "so no reader could write it" in line("stride"), line("stride"))
check("...a day the Gregorian calendar cannot write (jdn:0, in 4713 BCE) is warned of by its day number, with a NOTE beside it",
      line("day-zero").startswith("EXPIRED") and "day -1721425" in line("day-zero")
      and any(l.startswith("NOTE") and "beyond.clauses[day-zero]" in l and "shown as its day number" in l for l in out.splitlines()),
      [l for l in out.splitlines() if "day-zero" in l])
check("...a repetition whose `from` names another day than its `due` is walked from `due`, and the reader is told",
      any(l.startswith("NOTE") and "beyond.clauses[begins]" in l and f"`from: {_BEGIN.isoformat()}`" in l for l in out.splitlines()),
      [l for l in out.splitlines() if "begins" in l])
check("...and EVERY OTHER WARNING STILL PRINTS: the clause of another agreement due in three days",
      line("soon", bean="deal").startswith("EXPIRING"), out[-900:])
_disp = [l for l in out.splitlines() if "beyond.clauses[disputed]" in l]
check("a MERGE CONFLICT with a side on a day that does not exist and a side whose stride lands past 9999 does not drop them in "
      "silence: the row shown is the earliest of the others, says so, and each side it could not walk is a NOTE of its own",
      len(_disp) == 3 and _disp[0].startswith("OK") and f"due {_LATER}" in _disp[0]
      and "2 sides cannot be walked here (NOTE), and the earliest of the others is shown" in _disp[0]
      and any(l.startswith("NOTE") and "due 2026-02-30 is not a day this can read" in l
              and "not a day of the Gregorian calendar" in l for l in _disp)
      and any(l.startswith("NOTE") and "due 2026-09-01, then every 3000000 day" in l and "so no reader could write it" in l
              for l in _disp), _disp)
check("...and where NO side can be walked, each reason is its own — a day beyond what is reckoned is not a day this can read, "
      "not one 'aged by rule' — and a value of two hundred characters is told of by its length, not printed whole",
      line("unwalkable").startswith("NOTE") and "no due date among them can be walked here" in line("unwalkable")
      and "due jdn:99999999999 is not a day this can read" in line("unwalkable") and "by rule" not in line("unwalkable")
      and "(200 characters)" in line("unwalkable") and "9" * 200 not in line("unwalkable"), line("unwalkable"))
try:
    r = subprocess.run([sys.executable, os.path.join(G, "bin", "dmstale.py"), "--quiet"], capture_output=True, text=True, cwd=G,
                       timeout=60)
    qout = r.stdout + r.stderr
except subprocess.TimeoutExpired:
    qout = "(killed after 60 s)"
check("...and under --quiet, where an OK row is not printed, the sides it could not walk still are",
      "Traceback" not in qout and sum(1 for l in qout.splitlines() if l.startswith("NOTE") and "beyond.clauses[disputed]" in l
                                      and "a side of this merge conflict cannot be walked here" in l) == 2, qout[-900:])
try:
    r = subprocess.run([sys.executable, os.path.join(G, "bin", "dmledger.py"), "beyond"], capture_output=True, text=True, cwd=G, timeout=60)
    lout, ended = r.stdout + r.stderr, True
except subprocess.TimeoutExpired:
    lout, ended = "(killed after 60 s)", False
check("dmledger ENDS on the same clauses, and says of each what it could not read", ended and r.returncode == 0
      and "Traceback" not in lout and "not a day of the persian calendar" in lout and "outside the days reckoned here" in lout
      and "so no reader could write it" in lout and "not a day of the Gregorian calendar" in lout, lout[-1200:])
check("...and tells of the `from` that differs, as dmstale does", f"`from: {_BEGIN.isoformat()}`" in lout, lout[-900:])
os.remove(os.path.join(G, "beans", "beyond.md"))
_far = unreckoned("2026-09-01", {"in": "gregorian-civil", "every": {"count": 3000000, "unit": "day"}})
check("the walk itself (the library both readers share) says a stride past 9999-12-31 cannot be walked — Unreckoned, not a "
      "ValueError", "so no reader could write it" in _far[0], _far)
check("...a count longer than a count may be is refused by the walk the same way, not read",
      "longer than a count may be" in unreckoned("2026-09-01", {"every": {"count": "1" * 5000, "unit": "day"}})[0])
_notes = []
check("...and a day nobody can write is shown by its number, with the reason for a NOTE — never a traceback",
      _st.show_day(_dmcal.LAST_DAY + 10, notes=_notes) == f"day {_dmcal.LAST_DAY + 10}" and _notes and "outside the days" in _notes[0],
      _notes)
r = run(sys.executable, os.path.join(G, "bin", "dmstale.py"), "--days", "x", cwd=G)
check("`--days x` is refused with the form it takes — no traceback", r.returncode == 2 and "Traceback" not in r.stderr
      and "--days takes a whole number" in r.stdout, r.stdout + r.stderr[-300:])

# ---- A DISAGREEMENT A MERGE LEFT: the earliest date any side still owes is the one warned of --------------------------
open(os.path.join(G, "beans", "merged.md"), "w").write(f"""---
bean: merged
kind: contract
title: "an agreement two records disagree about"
status: active
summary: "two clauses in a merge conflict"
nature: metaphysical
owned_by: {{ legal: {{ crown: logos }} }}
responsibility: {{ legal: {{ parties: true }} }}
identity: {{ status: confirmed, anchors: [ {{ key: contract_id, value: "contract:merged", class: logical, establishing: true }} ] }}
provenance: {{ src: asserted-by-human, by: t, as_of: 2026-01-01 }}
parties:
  keeper: {{ who: {{ bean: keeper }} }}
  ali: {{ who: {{ bean: ali }} }}
words: {{ form: spoken }}
clauses:
  one-says-met: {{ conflict: [ {{ what: "a payment", by: ali, to: keeper, due: {IN3}, state: met }}, {{ what: "a payment", by: ali, to: keeper, due: {IN3} }} ] }}
  two-days:     {{ conflict: [ {{ what: "a payment", by: ali, to: keeper, due: {IN10} }}, {{ what: "a payment", by: ali, to: keeper, due: {IN3} }} ] }}
  both-met:     {{ conflict: [ {{ what: "a payment", by: ali, to: keeper, due: {IN3}, state: met }}, {{ what: "a payment", by: ali, to: keeper, due: {IN3}, state: waived }} ] }}
---
An agreement.
""")
out = stale()
line = lambda key, bean="merged": next((l for l in out.splitlines() if f"{bean}.clauses[{key}]" in l), "")
check("a clause in a merge conflict where ONE side says met is still warned of — until a person chooses, it may be owed",
      line("one-says-met").startswith("EXPIRING") and "merge conflict" in line("one-says-met"), out[-900:])
check("...where the sides give two days, the EARLIER is the one warned of", line("two-days").startswith("EXPIRING")
      and IN3 in line("two-days") and "the earliest is shown" in line("two-days"), out[-900:])
check("...and where every side is met or waived, it is silent, as one would be", line("both-met") == "", out[-900:])
os.remove(os.path.join(G, "beans", "merged.md"))

shutil.rmtree(T, ignore_errors=True)
print("\nexpiry: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
