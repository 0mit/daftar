#!/usr/bin/env python3
"""The measures (QTY, 24.0): positions by coordinates in one, two or three axes; temperature as a position and its rise
as a quantity; how well a value is known (`u`, `accuracy`), inside a quantity and beside a position; counts of things;
and a measured value merged by its value, however it was written.

Grows a garden and declares one local term, `works`, holding a length, an extent, a temperature and a count. Every
example is invented: a well, a footbridge, a kiln, and two seats at a recital.
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)

T = tempfile.mkdtemp(prefix="dmqty-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates from the release, and the new law loads", r.returncode == 0 and "0 error" in r.stdout, r.stdout + r.stderr)

TERM = """  - term: works
    meaning: "what an invented works department measured, each entry one thing"
    context_keys: [works]
    schema:
      shape: open_map_of_entries
      attrs:
        span:  { in: { quantity: length }, meaning: "how long it is" }
        rise:  { in: extent, meaning: "how far a temperature rose" }
        peak:  { in: { system: celsius-scale }, meaning: "the hottest it read" }
        seats: { in: { quantity: number }, meaning: "how many seats" }
        note:  { in: prose, meaning: "a note" }
    merge: { cardinality: multi, order: by-key }
senses:
  - { name: span, sense: "how far it reaches: a length measured, or the region of a line a series covers" }
"""
V = os.path.join(G, "VOCAB.md")
VOCAB0 = open(V, encoding="utf-8").read()
assert "local_terms: []" in VOCAB0, "the germinated VOCAB.md no longer says `local_terms: []`"
open(V, "w", encoding="utf-8", newline="\n").write(VOCAB0.replace("local_terms: []", "local_terms:\n" + TERM, 1))

BEAN = os.path.join(G, "beans", "works-book.md")
WELL = '{ system: geographic, at: "EPSG:5773;-12.5", openness: elsewhere }'
BRIDGE = '{ span: { count: "42.0", unit: centimetre, u: { count: "0.3", unit: centimetre } } }'
KILN = '{ peak: "C:1240", rise: { of: temperature, in: celsius-scale, measure: { count: "2.5", unit: kelvin } } }'
RECITAL = '{ seats: { count: 2, unit: item } }'

def text(located=(WELL,), works=None):
    works = works or {"bridge": BRIDGE, "kiln": KILN, "recital": RECITAL}
    return ("""---
bean: works-book
genos: org
title: "the works book"
status: active
summary: "an invented works department's book of what it measured"
nature: lekton
owned_by: { owner: { bean: keeper } }
identity: { status: provisional, anchors: [] }
provenance: { src: asserted-by-human, by: keeper, as_of: 2026-09-25 }
located_at:
""" + "".join(f"  - {x}\n" for x in located) + "works:\n" + "".join(f"  {k}: {v}\n" for k, v in works.items())
            + "---\n\nThe works book.\n")

def gate(**kw):
    open(BEAN, "w", encoding="utf-8", newline="\n").write(text(**kw))
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

def ok(out):
    return "0 error(s)" in out and "Traceback" not in out

out = gate()
check("a well at a depth, a footbridge's span with its u, a kiln's peak and rise, two seats: all pass", ok(out), out[-900:])

# ---------------------------------------------------------------- Q-1: one, two or three axes
out = gate(located=(WELL, '{ system: geographic, at: "EPSG:4326+5773;10.1,20.2,-3.5", openness: elsewhere }'))
check("a compound position, horizontal + vertical, three coordinates, passes", ok(out), out[-900:])
out = gate(located=('{ system: geographic, at: "EPSG:4326;1,2,3,4", openness: elsewhere }',))
check("four coordinates are refused", "EPSG:4326;1,2,3,4" in out and not ok(out), out[-900:])
r = run(sys.executable, os.path.join(G, "bin", "dmgeo.py"), "EPSG:4326;10.1,20.2", cwd=G)
check("dmgeo prints WGS 84's ensemble accuracy, 2 m, read from the law", "accurate to 2 metre" in r.stdout, r.stdout + r.stderr)
_law = os.path.join(G, "seed", "std-vocab.md")
_law0 = open(_law, encoding="utf-8").read()
open(_law, "w", encoding="utf-8", newline="\n").write(_law0.replace('ensemble_accuracy: { count: "2", unit: metre }',
                                                                    'ensemble_accuracy: { count: "2", unit: second }', 1))
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G).stdout
check("an ensemble accuracy that is not a length is refused by name",
      "reference_systems 'EPSG:4326'.ensemble_accuracy.unit 'second' measures duration" in out, out[-900:])
open(_law, "w", encoding="utf-8", newline="\n").write(_law0)

# ---------------------------------------------------------------- Q-2: temperature is a position; its rise a quantity
out = gate(works={"kiln": KILN.replace('unit: kelvin', 'unit: metre')})
check("a rise measured in metres is refused: the temperature line is metered in kelvin",
      "measures length, but aspect 'temperature' meters temperature" in out, out[-900:])
out = gate(works={"kiln": KILN.replace('"C:1240"', '"K:-3"')})
check("a kelvin reading below zero is refused by the scale's own form", "peak" in out and not ok(out), out[-900:])
out = gate(works={"kiln": KILN.replace('"C:1240"', '"1240"')})
check("a bare number is no temperature: the scale is named in the reading", "peak" in out and not ok(out), out[-900:])
out = gate(works={"kiln": KILN.replace('count: "2.5"', 'count: "0"')})
check("a rise of nothing is refused: a length is a positive count", "measure.count must be a positive count" in out, out[-900:])
r = run(sys.executable, os.path.join(G, "bin", "dmunits.py"), "1", "annus", "second", cwd=G)
check("dmunits: one annus is 31556925.445 seconds", r.stdout.startswith("31556925.445 second"), r.stdout + r.stderr)
r = run(sys.executable, os.path.join(G, "bin", "dmunits.py"), "750", "millimetre-of-mercury", "kilopascal", cwd=G)
check("dmunits: 750 mmHg is 99.99179056125 kPa, exactly", r.stdout.startswith("99.99179056125 kilopascal"), r.stdout + r.stderr)
r = run(sys.executable, os.path.join(G, "bin", "dmunits.py"), "36.4", "kelvin", "degree", cwd=G)
check("dmunits refuses a temperature difference as an angle", "nothing converts one into the other" in r.stdout, r.stdout)

# ---------------------------------------------------------------- Q-3: how well a value is known
_B = BRIDGE
for bad, want, why in (
        (_B.replace('u: { count: "0.3", unit: centimetre }', 'u: { count: "0.3", unit: second }'),
         "u.unit 'second' measures duration", "a u in a unit of another quantity"),
        (_B.replace('u: { count: "0.3", unit: centimetre }', 'u: { count: "0.3", unit: centimetre }, accuracy: { count: "1", unit: centimetre, kind: bound }'),
         "states both `u` and `accuracy`", "u beside accuracy"),
        (_B.replace('u: { count: "0.3", unit: centimetre }', 'u: { count: "0", unit: centimetre }'),
         "is a positive count", "a u of nothing"),
        (_B.replace('u: { count: "0.3", unit: centimetre }', 'note: "tape"'),
         "carries note, and a quantity holds count, unit and one of u / accuracy", "a key beside count and unit"),
        (_B.replace('u: { count: "0.3", unit: centimetre }', 'accuracy: { count: "1", unit: centimetre, kind: sigma }'),
         "accuracy.kind 'sigma' is not a row of `accuracy_kinds`", "an accuracy of a kind the law does not have")):
    out = gate(works={"bridge": bad})
    check(f"refused: {why}", want in out, out[-900:])
out = gate(works={"bridge": _B.replace('u: { count: "0.3", unit: centimetre }', 'u: { count: "2", unit: percent }')})
check("a RELATIVE u, in percent, passes", ok(out), out[-900:])
out = gate(works={"bridge": _B.replace('u: { count: "0.3", unit: centimetre }', 'accuracy: { count: "1", unit: centimetre, kind: bound }')})
check("an accuracy with its kind passes in place of u", ok(out), out[-900:])
FIX = '{ system: geographic, at: "EPSG:4326;10.1,20.2@2026.7", openness: elsewhere, accuracy: { count: "4.9", unit: metre, kind: radius-68 } }'
out = gate(located=(WELL, FIX))
check("a phone's fix with its stated accuracy, radius-68, passes", ok(out), out[-900:])
out = gate(located=(FIX.replace("radius-68", "sigma"),))
check("...and with kind `sigma`, is refused", "sigma" in out and not ok(out), out[-900:])
out = gate(located=(FIX.replace("accuracy:", 'u: { count: "3", unit: metre }, accuracy:'),))
check("...and a u beside it is refused: at most one", "states `u` and `accuracy`" in out, out[-900:])
out = gate(located=(WELL.replace("openness: elsewhere", 'openness: elsewhere, u: { count: "0.02", unit: metre }, u_vertical: { count: "0.05", unit: metre }'),))
check("a survey's horizontal and vertical u pass", ok(out), out[-900:])
out = gate(located=(WELL.replace("openness: elsewhere", 'openness: elsewhere, u_vertical: { count: "0", unit: metre }'),))
check("...and a vertical u of nothing is refused, named as `u_vertical`", "(u_vertical).u.count" in out and "positive count" in out, out[-900:])
out = gate(located=(WELL.replace("openness: elsewhere", 'openness: elsewhere, u: { count: "3", unit: second }'),))
check("...and a position's u in seconds is refused", "u.unit 'second' measures duration" in out, out[-900:])

# ---------------------------------------------------------------- Q-5: counts
out = gate(works={"recital": RECITAL.replace("unit: item", "unit: percent")})
check("a count of seats in percent is refused: a count is not a share", "measures ratio, and this attribute is a number" in out, out[-900:])

# ---------------------------------------------------------------- Q-4 (D17): one value, however written
sys.path.insert(0, os.path.join(G, "bin"))
import dmunits
from fractions import Fraction
check("dmunits.canonical: 12.5 metre and 12500 millimetre are one value",
      dmunits.canonical({"count": "12.5", "unit": "metre"}) == dmunits.canonical({"count": 12500, "unit": "millimetre"})
      == ("length", Fraction(25, 2), "metre"))
check("...an amount stays in its own currency", dmunits.canonical({"count": "900.00", "unit": "XTS"}) == ("money", Fraction(900), "XTS"))
open(BEAN, "w", encoding="utf-8", newline="\n").write(text(works={"kiln": KILN}))
_O, _A, _Bf = (os.path.join(T, n) for n in ("O.md", "A.md", "B.md"))
_base = text(works={"kiln": KILN})

def merge(a, b):
    open(_O, "w", encoding="utf-8", newline="\n").write(_base)
    open(_A, "w", encoding="utf-8", newline="\n").write(text(works={"kiln": KILN, "bridge": a}))
    open(_Bf, "w", encoding="utf-8", newline="\n").write(text(works={"kiln": KILN, "bridge": b}))
    r = run(sys.executable, os.path.join(G, "bin", "dmmerge.py"), "--file", _O, _A, _Bf, cwd=G)
    return r, open(_A, encoding="utf-8").read()

r, merged = merge('{ span: { count: "12.5", unit: metre } }', '{ span: { count: 12500, unit: millimetre } }')
check("two clones write one span in metres and in millimetres: the merge is clean, and keeps the first's bytes",
      r.returncode == 0 and "conflict" not in merged and 'count: "12.5", unit: metre' in merged.replace("'", '"'),
      r.stdout + r.stderr + merged[-600:])
r, merged = merge('{ span: { count: "12.5", unit: metre } }', '{ span: { count: 12, unit: metre } }')
check("...12.5 metre against 12 metre is a captured disagreement", "conflict" in merged, r.stdout + r.stderr + merged[-600:])
r, merged = merge('{ span: { count: "12.5", unit: metre, u: { count: "0.3", unit: centimetre } } }',
                  '{ span: { count: 12500, unit: millimetre, u: { count: 3, unit: millimetre } } }')
check("...and its u, written in two units, is one u", r.returncode == 0 and "conflict" not in merged, r.stdout + r.stderr + merged[-600:])
r, merged = merge('{ span: { count: "12.5", unit: metre, u: { count: "0.3", unit: centimetre } } }',
                  '{ span: { count: 12500, unit: millimetre, u: { count: 4, unit: millimetre } } }')
check("...and two different u are a disagreement", "conflict" in merged, r.stdout + r.stderr + merged[-600:])

shutil.rmtree(T, ignore_errors=True)
print(f"\nuncertainty: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
