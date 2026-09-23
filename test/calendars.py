#!/usr/bin/env python3
"""Calendars and coordinates (std-vocab 16.0).

A calendar is one partition of the line of days; every calendar here meets the others at THE DAY, and `bin/dmcal.py`
converts through it for every calendar that reckons by rule, refusing the ones that do not. A position by coordinates
names its reference system and its body. The law's registry and the two tools are held to each other.
"""
import datetime, os, re, sys, subprocess, tempfile, shutil
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmcal, dmgeo
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

sv = yaml.safe_load(re.match(r'^---\n(.*?)\n---', open(os.path.join(ROOT, "seed", "std-vocab.md")).read(), re.S).group(1))
cals = [r for r in sv["anchor_systems"] if r.get("calendar")]

# ---------------------------------------------------------------- the list is CLDR's, and the law and the tool agree
CLDR = {"buddhist", "chinese", "coptic", "dangi", "ethioaa", "ethiopic", "gregory", "hebrew", "indian", "islamic",
        "islamic-umalqura", "islamic-tbla", "islamic-civil", "islamic-rgsa", "iso8601", "japanese", "persian", "roc"}
OTHERS = {"julian", "julian-day", "mayan-long-count", "bahai", "french-republican"}     # the ones GNU Emacs's calendar also knows
check("every calendar Unicode CLDR identifies is declared, and beside them the Julian, the day number, the Mayan long count, the Badi and the French Republican",
      {r["calendar"] for r in cals} == CLDR | OTHERS, sorted({r["calendar"] for r in cals} ^ (CLDR | OTHERS)))
by_rule = {r["calendar"] for r in cals if r.get("reckoning") == "arithmetic"}
check("the law's `reckoning: arithmetic` is EXACTLY what the tool converts, and the rest is exactly what it refuses",
      by_rule == set(dmcal.EVERY) and {r["calendar"] for r in cals} - by_rule == set(dmcal.NOT_BY_RULE),
      (sorted(by_rule ^ set(dmcal.EVERY)), sorted(({r['calendar'] for r in cals} - by_rule) ^ set(dmcal.NOT_BY_RULE))))
check("every calendar but the interchange one shares the Gregorian ground and says how it is crossed",
      all(r.get("same_ground_as") == ["gregorian-civil"] and r.get("crosswalk") for r in cals if r["calendar"] != "gregory"))
check("a MONTH is never metric, in any calendar — and a day always is",
      all(not l.get("unit") for r in cals for l in r.get("levels", []) if l["level"] in ("month", "year", "era", "week"))
      and all(l.get("unit") == "day" for r in cals for l in r.get("levels", []) if l["level"] == "day"))
check("the calendars whose day begins at SUNSET say so — and the astronomers' day begins at NOON",
      {r["calendar"] for r in cals if r.get("day_begins") == "sunset"} == {"hebrew", "islamic", "islamic-civil", "islamic-tbla", "islamic-rgsa", "islamic-umalqura", "bahai"}
      and {r["calendar"] for r in cals if r.get("day_begins") == "noon"} == {"julian-day"})
check("NO CALENDAR IS PRIVILEGED: the law marks none as the one to store in",
      not [r["system"] for r in sv["anchor_systems"] if "interchange" in r])

# one form per system, and BETWEEN systems forms that cannot be mistaken for each other
times = [r for r in sv["anchor_systems"] if r.get("dimension") == "time" and r.get("example")]
clash = [(a["system"], b["system"]) for a in times for b in times
         if a is not b and b.get("pattern") not in (None, "none") and re.match(b["pattern"], a["example"], re.ASCII)]
check("no calendar's example can be read as a position in another calendar", not clash, clash)
check("...in particular a Persian date is NOT a Gregorian one, which untagged it would be",
      re.match(next(r["pattern"] for r in cals if r["calendar"] == "gregory"), "1405-06-29") is not None
      and not re.match(next(r["pattern"] for r in cals if r["calendar"] == "gregory"), "persian:1405-06-29"))
same_day = {dmcal.to_day(r["example"].split(" ")[0]) for r in cals if r["calendar"] in by_rule}
check("the examples of every rule-reckoned calendar are ONE day, computed and not typed", len(same_day) == 1, same_day)

# ---------------------------------------------------------------- the reckoning itself
for pos, cal, want in (("persian:1357-11-22", "gregory", "1979-02-11"), ("persian:1405-01-01", "gregory", "2026-03-21"),
                       ("persian:1403-12-30", "gregory", "2025-03-20"), ("hebrew:5787-01-01", "gregory", "2026-09-12"),
                       ("coptic:1743-01-01", "gregory", "2026-09-11"), ("ethiopic:2019-01-01", "gregory", "2026-09-11"),
                       ("indian:1948-01-01", "gregory", "2026-03-22"), ("2026-09-20", "julian", "julian:2026-09-07"),
                       ("2026-09-20", "iso8601", "2026-W38-7"), ("2026-09-20", "japanese", "japanese:reiwa-8-09-20"),
                       ("2026-09-20", "roc", "roc:115-09-20"), ("2026-09-20", "buddhist", "buddhist:2569-09-20"),
                       ("2026-09-20", "ethioaa", "ethioaa:7519-01-10"), ("2000-01-01", "julian-day", "jdn:2451545"),
                       ("2012-12-21", "mayan-long-count", "mayan:13.0.0.0.0"), ("mayan:13.0.0.0.0", "julian-day", "jdn:2456283")):
    check(f"{pos} is {want}", dmcal.convert(pos, cal) == want, dmcal.convert(pos, cal))
n = datetime.date(1996, 2, 25).toordinal()
check("the published sample day (R.D. 728714) reads the same in six calendars as in Dershowitz & Reingold's table",
      n == 728714 and [dmcal.from_day(n, c) for c in ("julian", "islamic-civil", "persian", "coptic", "ethiopic", "hebrew")]
      == ["julian:1996-02-12", "islamic-civil:1416-10-05", "persian:1374-12-06", "coptic:1712-06-17",
          "ethiopic:1988-06-17", "hebrew:5756-07-05"])
bad = sum(1 for d in range(datetime.date(1950, 1, 1).toordinal(), datetime.date(2050, 1, 1).toordinal())
          for c in dmcal.EVERY if dmcal.to_day(dmcal.from_day(d, c)) != d)
check("every day of a century round-trips through every rule-reckoned calendar", bad == 0, bad)
for pos in ("chinese:4723-01-01", "islamic:1448-04-08", "islamic-umalqura:1448-04-08", "bahai:183-10-13", "french-republican:234-13-04"):
    try:
        dmcal.to_day(pos); ok = False
    except dmcal.NotByRule:
        ok = True
    check(f"{pos.split(':')[0]} is REFUSED, not approximated — it is not reckoned by rule", ok)
try:
    dmcal.to_day("hebrew:5786-06-01"); ok = False
except ValueError:
    ok = True
check("a common Hebrew year has no month 6 (5786), and a leap year has one (5787): Adar I exists only then", ok and dmcal.to_day("hebrew:5787-06-01") > 0)
try:
    dmcal.to_day("persian:9999-01-01"); ok = False
except ValueError:
    ok = True
check("the Persian reckoning REFUSES a year outside the range it is good for", ok)

# ---------------------------------------------------------------- a day that does not exist is REFUSED, never moved
def refusal(f):
    """The message of the ValueError `f` raises, or what went otherwise (a traceback of another kind is a failure)."""
    try:
        return "no refusal: " + repr(f())
    except ValueError as e:
        return "ValueError: " + str(e)
    except Exception as e:                     # noqa: BLE001 — anything else is the defect being tested for
        return f"{type(e).__name__}: {e}"
_none = [("persian:1404-12-30", "persian:1405-01-01"), ("julian:2026-02-29", "julian:2026-03-01"),
         ("coptic:1742-13-99", "coptic:1743-04-04"), ("islamic-civil:1448-12-30", "islamic-civil:1449-01-01"),
         ("ethiopic:2018-13-06", "ethiopic:2019-01-01"), ("buddhist:2569-02-29", ""), ("roc:115-02-30", ""),
         ("indian:1948-12-31", ""), ("coptic:1742-00-10", ""), ("julian:2026-01-00", ""), ("2026-02-30", ""),
         ("2026-13-01", ""), ("japanese:reiwa-8-02-30", ""), ("2027-W53-1", ""), ("hebrew:5786-02-30", "")]
_got = [(p, moved, refusal(lambda p=p: dmcal.to_day(p))) for p, moved in _none]
check("A DAY ITS CALENDAR DOES NOT HAVE IS REFUSED — the 30th of a 29-day Esfand, a Julian 29 February in a common year, "
      "a Coptic 13th month of 99 days, a month 0, a day 0 — each a ValueError, never read as the day after",
      all(g.startswith("ValueError") for p, m, g in _got), [(p, g[:90]) for p, m, g in _got if not g.startswith("ValueError")])
check("...and the refusal says the day arithmetic would have moved it to, so the reader sees what was nearly done",
      all(m in g for p, m, g in _got if m), [(p, m, g[:160]) for p, m, g in _got if m and m not in g])
check("...while the day before it, and the leap day a leap year has, still read",
      dmcal.convert("persian:1404-12-29", "gregory") == "2026-03-20" and dmcal.convert("persian:1403-12-30", "gregory") == "2025-03-20"
      and dmcal.convert("julian:2028-02-29", "julian") == "julian:2028-02-29" and dmcal.convert("ethiopic:2015-13-06", "ethiopic") == "ethiopic:2015-13-06")

# ---------------------------------------------------------------- every calendar reckons the same days, and no others
import time
check("the days reckoned here run from jdn:0 to 9999-12-31, and the ends are written as themselves",
      dmcal.to_day("jdn:0") == dmcal.FIRST_DAY and dmcal.from_day(dmcal.LAST_DAY, "gregory") == "9999-12-31"
      and dmcal.from_day(dmcal.FIRST_DAY, "julian-day") == "jdn:0")
_far = ["hebrew:1000000000000000-01-01", "hebrew:" + "9" * 5000 + "-01-01", "julian:99999999-01-01", "coptic:-99999999-01-01",
        "jdn:99999999999", "mayan:99999999.0.0.0.0", "japanese:reiwa-99999999999999999999-01-01", "islamic-civil:20000-01-01",
        "persian:3178-01-01", "0000-01-01"]
_t0 = time.time()
_got = [(p[:40], refusal(lambda p=p: dmcal.to_day(p))) for p in _far]
check("A YEAR BEYOND THE DAYS RECKONED IS REFUSED, in every calendar and at once — a Hebrew year of sixteen digits, one of "
      "five thousand, a day count of eleven: a ValueError each, never a hang and never an OverflowError",
      all(g.startswith("ValueError") for p, g in _got) and time.time() - _t0 < 2,
      ([(p, g[:90]) for p, g in _got if not g.startswith("ValueError")], round(time.time() - _t0, 2)))
_got = [(c, n, refusal(lambda c=c, n=n: dmcal.from_day(n, c))) for c in dmcal.EVERY
        for n in (dmcal.LAST_DAY + 1, dmcal.FIRST_DAY - 1, 10 ** 20, -10 ** 20)]
check("...and a day beyond them is refused by every calendar's writer, as a ValueError — the kind every reader catches",
      all(g.startswith("ValueError") for c, n, g in _got), [(c, n, g[:90]) for c, n, g in _got if not g.startswith("ValueError")][:4])
check("...as is a day before the first its own calendar holds: 0001-01-01 for the Gregorian, 0.0.0.0.0 for the long count",
      refusal(lambda: dmcal.from_day(0, "gregory")).startswith("ValueError")
      and refusal(lambda: dmcal.from_day(dmcal.MAYAN_EPOCH - 1, "mayan-long-count")).startswith("ValueError")
      and refusal(lambda: dmcal.from_day(1, "no-such-calendar")).startswith("ValueError"))
_ends = [d for d in range(dmcal.FIRST_DAY, dmcal.FIRST_DAY + 400)] + [d for d in range(dmcal.LAST_DAY - 400, dmcal.LAST_DAY + 1)]
_bad = []
for c in dmcal.EVERY:
    for d in _ends:
        try:
            p = dmcal.from_day(d, c)
        except ValueError:
            continue                            # a day this calendar does not write — said, and tested above
        if dmcal.to_day(p) != d:
            _bad.append((c, d, p))
check("...and within them, every day at either end round-trips through every calendar that writes it", not _bad, _bad[:3])

# THE HEBREW YEAR IS ESTIMATED FROM THE MEAN YEAR, never counted up to: every new year of every year reckoned, and the day
# before it, falls in the year it should — and the whole walk takes well under the time one year of sixteen digits took.
_t0, _bad = time.time(), []
_lo, _hi = dmcal.hebrew_from_day(dmcal.FIRST_DAY)[0], dmcal.hebrew_from_day(dmcal.LAST_DAY)[0]
for _y in range(_lo + 1, _hi + 1):
    _ny = dmcal._h_new_year(_y)
    if dmcal.hebrew_from_day(_ny) != (_y, 1, 1) or dmcal.hebrew_from_day(_ny - 1)[0] != _y - 1:
        _bad.append(_y)
check(f"every Hebrew new year from {_lo + 1} to {_hi} reads as the first of Tishri of its year, and the day before as the "
      f"year before — the year estimated from the mean year, in one step either way", not _bad and time.time() - _t0 < 10,
      (_bad[:5], round(time.time() - _t0, 2)))

# ---------------------------------------------------------------- the command: UTF-8 through any pipe, and its refusals
def dmcal_cmd(*a, env=None):
    r = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "dmcal.py")] + list(a), capture_output=True, env=env)
    return r.returncode, r.stdout.decode("utf-8", "replace") + r.stderr.decode("utf-8", "replace")
_code, _out = dmcal_cmd("hebrew:5787-01-09", env=dict(os.environ, PYTHONIOENCODING="ascii"))
check("dmcal writes UTF-8 through a pipe whose encoding has no `—` (as a Windows pipe in the ANSI code page has none)",
      _code == 0 and "Traceback" not in _out and "islamic-umalqura — not reckoned by rule" in _out, _out[-400:])
_code, _out = dmcal_cmd("persian:1404-12-30")
check("...refuses a day that does not exist, saying so", _code == 1 and "is not a day of the persian calendar" in _out, _out)
_code, _out = dmcal_cmd("--day", "x")
check("...and a day number that is not one, with the form it takes — no traceback", _code == 2 and "Traceback" not in _out
      and "--day takes a day number" in _out, _out)
import io, contextlib
import dmparse  # noqa: F401 — what dmcal.main imports, imported before the platform is imitated below
_buf, _os_name = io.StringIO(), os.name
try:
    os.name = "nt"
    with contextlib.redirect_stdout(_buf):
        dmcal.main(["--help"])
finally:
    os.name = _os_name
check("...and its help names the interpreter as it is named where it runs: `python` on Windows",
      "    python bin/dmcal.py 2026-09-20" in _buf.getvalue() and "python3 bin/" not in _buf.getvalue(), _buf.getvalue()[:300])

# ---------------------------------------------------------------- where, by coordinates
check("the tool's bodies are the law's, to the metre", {b["body"]: b["mean_radius_m"] for b in sv["bodies"]} == dmgeo.BODIES)
check("the tool's reference systems are rows of the law's, with the same body, kind and frame",
      all(any(r["crs"] == k and (r["body"], r["kind"], r["frame"]) == (v["body"], v["kind"], v["frame"]) for r in sv["reference_systems"])
          for k, v in dmgeo.SYSTEMS.items()))
try:
    dmgeo.parse("35.6892,51.3890"); ok = False
except ValueError:
    ok = True
check("A COORDINATE IS NEVER BARE: no reference system, no position", ok)
check("the geohash of the published example", dmgeo.geohash(57.64911, 10.40744, 11) == "u4pruydqqvj")
d = dmgeo.distance("EPSG:4326;35.6892,51.3890", "EPSG:4326;41.0082,28.9784") / 1000
check("a distance is measured ON THE BODY the system names — Tehran to Istanbul", 2000 < d < 2070, d)
dm = dmgeo.distance("IAU_2015:49900;0,0", "IAU_2015:49900;0,180") / 1000
check("...and the same machinery on Mars gives half of MARS's circumference", abs(dm - 3.141592653589793 * 3389.5) < 1, dm)
root = {r["system"]: r for r in sv["anchor_systems"]}
ident = ["iso-3166", "osm", "postal-code", "street-address", "local-frame", "geohash", "plus-code", "network-segment"]
check("every way of saying where BY IDENTIFIER resolves through coordinates, and none of them establishes but a published code",
      all(root[s].get("resolves_through") == "geographic" for s in ident)
      and [s for s in ident if root[s].get("establishes")] == ["iso-3166"], [(s, root[s].get("establishes")) for s in ident])

# ---------------------------------------------------------------- the gate: one set of digits, and an example in its own form
def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)
T = tempfile.mkdtemp(prefix="dmcal-"); G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
STD = os.path.join(G, "seed", "std-vocab.md"); ORIG = open(STD).read()
def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G); return r.stdout + r.stderr
def bean(as_of):
    open(os.path.join(G, "beans", "box.md"), "w").write(f"""---
bean: box
kind: host
title: "a machine"
status: active
summary: "probe"
nature: physical
identity: {{ status: confirmed, anchors: [ {{ key: serial, value: "SN-CAL-1", class: hardware, establishing: true }} ] }}
provenance: {{ src: observed, by: probe, as_of: 2026-09-20 }}
owned_by: {{ legal: {{ external: "someone" }} }}
responsibility: {{ legal: {{ external: "someone" }} }}
located_at:
  - {{ system: geographic, at: "{as_of}", openness: here, observed: 2026-09-20 }}
---

probe.
""")
    return gate()
check("a position by coordinates that names its reference system passes", "0 error" in bean("EPSG:4326;35.6892,51.3890@2026.72"), bean("EPSG:4326;35.6892,51.3890@2026.72")[-600:])
out = bean("35.6892,51.3890")
check("...and a bare latitude and longitude is refused by the gate", "is not in the one canonical form 'geographic' declares" in out, out[-600:])
out = bean("EPSG:4326;۳۵.۶۸۹۲,۵۱.۳۸۹۰")
check("ONE FORM MEANS ONE SET OF DIGITS: Persian digits are not a second spelling of a position", "is not in the one canonical form" in out, out[-600:])
# a fact is dated in the calendar it was KNOWN in: every dated attribute of the standard takes any calendar's day
def dated(observed):
    open(os.path.join(G, "beans", "box.md"), "w").write(f"""---
bean: box
kind: host
title: "a machine"
status: active
summary: "probe"
nature: physical
identity: {{ status: confirmed, anchors: [ {{ key: serial, value: "SN-CAL-1", class: hardware, establishing: true }} ] }}
provenance: {{ src: observed, by: probe, as_of: 2026-09-20 }}
owned_by: {{ legal: {{ external: "someone" }} }}
responsibility: {{ legal: {{ external: "someone" }} }}
located_at:
  - {{ system: geographic, at: "EPSG:4326;35.6892,51.3890", openness: here, observed: {observed} }}
---

probe.
""")
    return gate()
for d in ("2026-09-20", '"persian:1405-06-29"', '"hebrew:5787-01-09"', "2026-W38-7", '"islamic:1448-04-08"'):
    check(f"`observed: {d}` is a date — NO CALENDAR IS THE ONE A DATE MUST BE IN", "0 error" in dated(d), dated(d)[-400:])
for d, why in (('"1405-06-29 12:00"', "a clock time is finer than a day"), ('"29 Shahrivar 1405"', "prose"), ("1758369600000", "a system with no day level"),
               ('"persian:۱۴۰۵-۰۶-۲۹"', "another script's digits")):
    check(f"`observed: {d}` is refused ({why})", "must be an ABSOLUTE date held to the day" in dated(d), dated(d)[-400:])

assert ORIG.count('    example: "2026-W38-7"\n') == 1
open(STD, "w").write(ORIG.replace('    example: "2026-W38-7"\n', '    example: "2026-38-7"\n'))
check("a system's own example is held to its own pattern", "its own `example` '2026-38-7' is not in the form" in gate(), gate()[-500:])
open(STD, "w").write(ORIG)
shutil.rmtree(T, ignore_errors=True)

# ---------------------------------------------------------------- 18.0: an instant is contained in ANY calendar
import dmmerge as _M
_p, _h = dmcal.convert("2026-09-19", "persian"), dmcal.convert("2026-09-19", "hebrew")
_cases = [("2026-09-19", "2026-09-19 22:50+03:00", True), (_p, "2026-09-19 22:50+03:00", True),
          (_p, _p + " 22:50+03:30", True), ("2026-09-19", _p + " 22:50", True), (_h, _h + " 22:50", True),
          ("2026-09-19 23:00+00:00", "2026-09-20 02:00:10+03:00", True), ("2026-W38-6", "2026-09-19 10:00", True),
          ("2026-09-20", "2026-09-19 22:50", False), ("2026-09-19", "2026-09-19", False)]
_bad = [(a, b) for a, b, w in _cases if bool(_M._instant_contains(a, b)) != w]
check("a day CONTAINS a finer reading of it, in whatever calendar either is written — they meet at the day", not _bad, _bad)
check("...but a day that begins at SUNSET does not contain another calendar's clock time by arithmetic: unordered",
      not _M._instant_contains(_h, "2026-09-19 22:50+03:00"))
check("the order follows what a value IS: a reading in any calendar is an instant", _M.leaf_order("whenever", _p + " 22:50") == "instant")

print("\ncalendars: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
