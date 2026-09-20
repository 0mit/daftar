#!/usr/bin/env python3
"""Quantities (std-vocab 17.0): a product of powers of base dimensions — so area, volume, speed, acceleration, a data rate
and an attenuation are one construct; and an extent's measure spans as many lines as its unit has powers."""
import os, sys, subprocess, tempfile, shutil
from fractions import Fraction
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmunits
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

units, quantities = dmunits.law()
check("every unit names a quantity the law declares, and an exact factor",
      all(u.get("quantity") in quantities and isinstance(u.get("factor"), list) and len(u["factor"]) == 2 and all(isinstance(x, int) and x > 0 for x in u["factor"]) for u in units.values()))
check("speed is length per time, acceleration length per time SQUARED, area length squared, volume length cubed",
      quantities["speed"]["of"] == {"length": 1, "time": -1} and quantities["acceleration"]["of"] == {"length": 1, "time": -2}
      and quantities["area"]["of"] == {"length": 2} and quantities["volume"]["of"] == {"length": 3})
check("every quantity has a coherent unit (factor 1)", all(any(u["quantity"] == q and u["factor"] == [1, 1] for u in units.values()) for q in quantities))
for args, want in ((("90", "kilometre-per-hour", "metre-per-second"), 25), (("1.5", "hectare", "square-metre"), 15000),
                   (("2", "cubic-metre", "litre"), 2000), (("1", "day", "minute"), 1440), (("3", "decibel-per-kilometre", "decibel-per-metre"), Fraction(3, 1000)),
                   (("8", "megabit-per-second", "byte"), None)):
    try:
        got = dmunits.convert(*args)
    except ValueError:
        got = None
    check(f"{args[0]} {args[1]} -> {args[2]}: {want if want is not None else 'REFUSED, a rate is not an amount'}", got == want, got)

# ---------------------------------------------------------------- TRUNCATION CANNOT BITE
import itertools
bad = []
for q in quantities:
    names = [n for n, u in units.items() if u["quantity"] == q]
    for a_, b_ in itertools.permutations(names, 2):
        for x in ("1", "0.1", "7", "123456789012345678901234567890.123456789"):
            if dmunits.convert(dmunits.convert(x, a_, b_), b_, a_) != Fraction(x):
                bad.append((x, a_, b_))
check("EVERY conversion, between every pair of units of every quantity, comes back EXACTLY — even thirty digits", not bad, bad[:3])
check("a result is printed exactly, not through a float: thirty digits survive",
      dmunits.show(dmunits.convert("123456789012345678901234567890.5", "metre", "millimetre")) == "123456789012345678901234567890500")
check("...a terminating decimal in full", dmunits.show(dmunits.convert("1", "gibibyte", "gigabyte")) == "1.073741824")
check("...and what does not terminate as a fraction of whole numbers, never rounded",
      dmunits.show(dmunits.convert("1", "metre-per-second", "kilometre-per-hour")) == "3.6"
      and dmunits.show(dmunits.convert("1", "minute", "day")) == "1/1440")
src = open(os.path.join(ROOT, "bin", "dmunits.py")).read() + open(os.path.join(ROOT, "bin", "dmcal.py")).read()
check("neither converter uses a float anywhere: no `float(`, no true division of counts",
      "float(" not in src and "math.ceil(" not in src, [l for l in src.split("\n") if "float(" in l or "math.ceil(" in l][:3])

def refuses(f):
    try:
        f(); return False
    except ValueError:
        return True
check("the converter refuses a float: what a float lost is lost before anything can check it",
      refuses(lambda: dmunits.convert(0.1, "metre", "millimetre")) and refuses(lambda: dmunits.convert("1e3", "metre", "millimetre")))

T = tempfile.mkdtemp(prefix="dmqty-"); G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, cwd=ROOT)
v = os.path.join(G, "VOCAB.md"); s = open(v).read()
assert s.count("local_terms: []") == 1
open(v, "w").write(s.replace("local_terms: []", """local_terms:
  - term: motion
    meaning: "how a thing moves, and the ground it covers"
    context_keys: [motion]
    schema:
      shape: mapping
      attrs:
        speed:        { in: { quantity: speed } }
        acceleration: { in: { quantity: acceleration } }
        loss:         { in: { quantity: attenuation } }
        covers:       { in: extent }
        lasts:        { in: extent }
    merge: { cardinality: single, order: none }"""))

def gate(motion):
    open(os.path.join(G, "beans", "box.md"), "w").write(f"""---
bean: box
kind: host
title: "a machine"
status: active
summary: "probe"
nature: physical
identity: {{ status: confirmed, anchors: [ {{ key: serial, value: "SN-QTY-1", class: hardware, establishing: true }} ] }}
provenance: {{ src: observed, by: probe, as_of: 2026-09-20 }}
owned_by: {{ legal: {{ external: "someone" }} }}
responsibility: {{ legal: {{ external: "someone" }} }}
motion: {motion}
---

probe.
""")
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr
ok = lambda o: "0 error" in o
check("a SPEED and an ACCELERATION are recorded painlessly", ok(gate('{ speed: { count: 90, unit: kilometre-per-hour }, acceleration: { count: "-9.81", unit: metre-per-second-squared } }')))
out = gate('{ speed: { count: 9, unit: metre-per-second-squared } }')
check("an acceleration is not a speed", "measures acceleration, and this attribute is a speed" in out, out[-500:])
sv = os.path.join(G, "seed", "std-vocab.md"); law_text = open(sv).read()
for wrong, why in (("factor: [0.277778, 1]", "a rounded decimal"), ("factor: [10, 36]", "not in lowest terms")):
    assert law_text.count("factor: [5, 18]") == 1
    open(sv, "w").write(law_text.replace("factor: [5, 18]", wrong))
    out = gate('{ speed: { count: 1, unit: metre-per-second } }')
    check(f"the LAW cannot declare a truncated factor: {why} is refused by the gate", "units 'kilometre-per-hour'" in out, out[-400:])
open(sv, "w").write(law_text)
out = gate('{ speed: { count: 12.5, unit: metre-per-second } }')
check("a float is refused: a decimal is written as a string", "a float has no canonical form" in out, out[-500:])
check("an ATTENUATION — decibels per kilometre", ok(gate('{ loss: { count: "0.35", unit: decibel-per-kilometre } }')))
check("an AREA on place: an extent whose measure spans two lines", ok(gate('{ covers: { of: place, in: geographic, measure: { count: 2, unit: hectare } } }')))
check("a VOLUME: three lines, and `geographic` has three", ok(gate('{ covers: { of: place, in: geographic, measure: { count: 40, unit: cubic-metre } } }')))
out = gate('{ lasts: { of: time, measure: { count: 3, unit: square-metre } } }')
check("an area is not a duration", "measures area, but aspect 'time' meters time" in out, out[-500:])
out = gate('{ covers: { of: place, in: geographic, measure: { count: 5, unit: metre-per-second } } }')
check("a speed is not a region", "measures speed, but aspect 'place' meters length" in out, out[-500:])
check("a duration is still a duration", ok(gate('{ lasts: { of: time, measure: { count: 204, unit: day } } }')))

shutil.rmtree(T, ignore_errors=True)
print("\nquantities: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
