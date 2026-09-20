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
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, cwd=ROOT)
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

print("\ncalendars: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
