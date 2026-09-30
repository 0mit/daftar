#!/usr/bin/env python3
"""Civil time zones (QTY, 24.0, N8): a position names the zone in force there, a row of the IANA database's canonical
zones, and an offset is READ from it for a moment — never stored, and never guessed where no zone database is.

Every example is invented: a ferry office on the far side of the world from any garden this was written in.
"""
import os, subprocess, sys, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)

sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmcal, zoneinfo

# ---------------------------------------------------------------- the file
TZ = os.path.join(ROOT, "seed", "knowledge", "time-zones.tsv")
lines = open(TZ, encoding="utf-8").read().split("\n")
head, rows = lines[0].split("\t"), [l.split("\t") for l in lines[1:] if l]
check("the zone file's header is zone, countries, coordinates, comment", head == ["zone", "countries", "coordinates", "comment"], head)
check("it holds the canonical zones, one row each, in order", len(rows) > 300 and [r[0] for r in rows] == sorted({r[0] for r in rows}), len(rows))
check("every row has four cells", all(len(r) == 4 for r in rows), [r for r in rows if len(r) != 4][:3])
check("it holds names and places, never an offset", not any("+" in r[0] or r[0].startswith("UTC+") for r in rows))
_unknown = [r[0] for r in rows if r[0] not in zoneinfo.available_timezones()]
check("every zone in it is one this machine's zone database names", not _unknown, _unknown[:5])
check("`Etc/UTC` is a row, for a reading in UTC itself", any(r[0] == "Etc/UTC" for r in rows))

# ---------------------------------------------------------------- dmcal.offset
check("Pacific/Auckland keeps +13:00 at 2026-04-04T13:30Z, in daylight time", dmcal.offset("Pacific/Auckland", "2026-04-04T13:30Z") == 780)
check("...and +12:00 an hour later, when daylight time has ended", dmcal.offset("Pacific/Auckland", "2026-04-04T14:30Z") == 720)
check("a moment written at an offset is read at its instant", dmcal.offset("Pacific/Auckland", "2026-04-05 02:30+13:00") == 780)
check("a zone west of UTC is negative", dmcal.offset("America/Lima", "2026-07-01T12:00Z") == -300)
for bad, why in (("Mars/Base", "a zone the database does not name"), ("../etc/passwd", "no zone name at all")):
    try:
        dmcal.offset(bad, "2026-04-04T13:30Z"); ok = False
    except ValueError:
        ok = True
    check(f"refused: {why} ({bad})", ok)
try:
    dmcal.offset("Pacific/Auckland", "2026-04-04"); ok = False
except ValueError:
    ok = True
check("a date alone is no moment, and has no one offset", ok)

# NO ZONE DATABASE: the offset is not guessed, and the fix is named
_zi, _av = zoneinfo.ZoneInfo, zoneinfo.available_timezones
def _none(*a, **k):
    raise zoneinfo.ZoneInfoNotFoundError("no time zone found")
zoneinfo.ZoneInfo, zoneinfo.available_timezones = _none, lambda: set()
try:
    dmcal.offset("Pacific/Auckland", "2026-04-04T13:30Z"); ok, msg = False, ""
except dmcal.NoZoneData as e:
    ok, msg = True, str(e)
finally:
    zoneinfo.ZoneInfo, zoneinfo.available_timezones = _zi, _av
check("with no zone database, NoZoneData names the fix, and no offset is guessed", ok and "pip install tzdata" in msg, msg)

r = run(sys.executable, os.path.join(ROOT, "bin", "dmcal.py"), "--offset", "Pacific/Auckland", "2026-04-04T14:30Z")
check("`dmcal.py --offset` prints the offset read", r.stdout.strip() == "Pacific/Auckland at 2026-04-04T14:30Z: +12:00", r.stdout + r.stderr)
r = run(sys.executable, os.path.join(ROOT, "bin", "dmcal.py"), "--offset", "Mars/Base", "2026-04-04T14:30Z")
check("...and refuses an unknown zone in words", r.returncode == 1 and "Traceback" not in r.stderr and "not a zone" in r.stdout, r.stdout + r.stderr)

# ---------------------------------------------------------------- a position names its zone
T = tempfile.mkdtemp(prefix="dmzones-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release", r.returncode == 0 and "0 error" in r.stdout, r.stdout + r.stderr)
BEAN = os.path.join(G, "beans", "ferry-office.md")

def gate(zone):
    open(BEAN, "w", encoding="utf-8", newline="\n").write(f"""---
bean: ferry-office
genos: org
title: "the ferry office"
status: active
summary: "an invented ferry office, and the zone its clocks keep"
nature: lekton
owned_by: {{ owner: {{ bean: keeper }} }}
identity: {{ status: provisional, anchors: [] }}
provenance: {{ src: asserted-by-human, by: keeper, as_of: 2026-09-25 }}
located_at:
  - {{ system: geographic, at: "EPSG:4326;-41.28,174.78@2026.7", openness: elsewhere, zone: {zone} }}
---

The ferry office.
""")
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

out = gate("Pacific/Auckland")
check("a position naming its zone, Pacific/Auckland, passes", "0 error(s)" in out, out[-900:])
out = gate("Mars/Base")
check("...a zone the database does not name is refused", "Mars/Base" in out and "0 error(s)" not in out, out[-900:])
out = gate('"+13:00"')
check("...and an offset in place of a zone is refused: an offset is read, never stored", "+13:00" in out and "0 error(s)" not in out, out[-900:])
shutil.rmtree(T, ignore_errors=True)

print(f"\nzones: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
