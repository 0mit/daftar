#!/usr/bin/env python3
"""The ordinal line: a sequence that holds at no time (std-vocab 28.0).

Grows a garden and writes two times two as a series on the ordinal line — two nodes of 2 whose whole is 4 — by a grid
and as a listed series. Checks that the gate reads the whole exactly (by sum, by product, by count) and refuses a wrong
one; that a gap leaves a whole it cannot check; that a series on a counted line states no unit and strides by
neighbours; that an ordinal number counts on every line (the meetings of a series, on time) and never stands alone (a
day, a moment, a place); that three system choosers take only the dimension their meaning names; and that the reckoner
reads the equation: the count of nodes times a node is the whole.
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


T = tempfile.mkdtemp(prefix="dmord-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "sam", cwd=ROOT)
check("a garden germinates, and the law with the ordinal line passes its own checks", r.returncode == 0, r.stdout + r.stderr)
BEAN = os.path.join(G, "beans", "two-times-two.md")
FACT = """---
bean: two-times-two
genos: document
title: "two times two"
status: active
summary: "two nodes of 2, whose whole is 4"
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: identifier, value: "document:two-times-two", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-28 }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
located_at: [ { system: iso-3166, openness: unknown } ]
series:
  by-grid:
    grid: { of: ordinal, in: ordinal-number, from: "ordinal:1", every: { count: 1 } }
    holds: [ { name: value, quantity: number, unit: item, stands_for: point } ]
    rows: |
      value
      2
      2
    whole: [ { value: { count: 4, unit: item }, of: value, by: sum }, { value: { count: 4, unit: item }, of: value, by: product }, { value: { count: 2, unit: item }, of: value, by: count } ]
  listed:
    span: { of: ordinal, in: ordinal-number, from: "ordinal:1", to: "ordinal:2" }
    holds: [ { name: value, quantity: number, unit: item, stands_for: point } ]
    rows: |
      at	value
      0	2
      1	2
    whole: { value: { count: 4, unit: item }, of: value, by: sum }
---
Two times two is four: a sequence of two nodes, each holding 2.
"""


def gate(old=None, new=None, text=FACT):
    t = text if old is None else text.replace(old, new, 1)
    assert old is None or old in text, old
    open(BEAN, "w").write(t)
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr


out = gate()
check("two times two is a series on the ordinal line — two nodes of 2 whose whole is 4 by sum, 4 by product, 2 by count, "
      "by a grid and as a listed series", " 0 error(s), 0 warning(s)" in out, out[-900:])
out = gate("{ value: { count: 4, unit: item }, of: value, by: sum }, { value", "{ value: { count: 5, unit: item }, of: value, by: sum }, { value")
check("a whole the rows do not make is refused, with what they make", "series[by-grid].whole[0]" in out and "says 5 item, and the "
      "sum of `value` over its 2 row(s) is 4 item" in out, out[-900:])
out = gate("      value\n      2\n      2\n", "      value\n      2\n      -\n")
check("a gap in a node leaves a whole nobody can check, and that is said — the count still holds", " 0 error(s), 2 warning(s)" in out
      and "the whole cannot be checked" in out, out[-900:])
out = gate('    grid: { of: ordinal, in: ordinal-number, from: "ordinal:1", every: { count: 1 } }\n',
           '    grid: { of: ordinal, in: ordinal-number, from: "ordinal:1", every: { count: 1 } }\n    unit: item\n')
check("a series on a counted line states no unit: an offset there is a count of neighbours", "series[by-grid].unit" in out
      and "no unit measures it" in out, out[-900:])
out = gate('every: { count: 1 } }', 'every: { count: 1, unit: day } }')
check("...and a grid there strides by neighbours, never by a measure", "series[by-grid].grid.every" in out, out[-900:])
out = gate('    whole: { value: { count: 4, unit: item }, of: value, by: sum }\n---',
           '    whole: { value: { count: 4, unit: item }, of: nothing, by: sum }\n---')
check("a whole names a channel of its series", "series[listed].whole.of" in out and "names 'nothing'" in out, out[-900:])

# ---- an ordinal number counts on every line, and never stands alone ------------------------------------------------------
out = gate("  listed:", '''  meetings:
    span: { of: time, in: ordinal-number, from: "ordinal:1", to: "ordinal:3" }
    holds: [ { name: came, quantity: number, unit: item, stands_for: point } ]
    rows: |
      at	came
      0	5
      2	7
    whole: { value: { count: 12, unit: item }, of: came, by: sum }
  listed:''')
check("an ordinal number counts on every line: the first to the third meeting of a series on time, whose whole is 12",
      " 0 error(s), 0 warning(s)" in out, out[-900:])
for why, old, new, want in (
        ("as a place", "located_at: [ { system: iso-3166, openness: unknown } ]",
         'located_at: [ { system: ordinal-number, openness: here, at: "ordinal:2" } ]', "located_at[0].system `ordinal-number` counts from "
         "the first of a line"),
        ("as a moment of `timing`", "located_at: [ { system: iso-3166, openness: unknown } ]",
         'located_at: [ { system: iso-3166, openness: unknown } ]\ntiming:\n  start: { system: ordinal-number, at: "ordinal:2", unit: day }',
         "timing[start].system `ordinal-number` counts from the first of a line")):
    out = gate(old, new)
    check("an ordinal number standing alone lies on no line, and is refused " + why, want in out, out[-900:])
open(os.path.join(G, "beans", "deal.md"), "w").write("""---
bean: deal
genos: contract
title: "deal"
status: active
summary: "probe"
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: identifier, value: "contract:deal", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-28 }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, accepted: { system: ordinal-number, at: "ordinal:2", unit: day } }
words: { form: spoken }
---
d
""")
out = gate()
check("...and as the long form of a day: a yes on \"the second\" of nothing", "timing[parties[sam].accepted].system `ordinal-number` "
      "counts from the first of a line" in out, out[-900:])
os.remove(os.path.join(G, "beans", "deal.md"))

# ---- three system choosers take only the dimension their meaning names ---------------------------------------------------
for why, old, new, want in (
        ("a moment of `timing` is in time", "located_at: [ { system: iso-3166, openness: unknown } ]",
         "located_at: [ { system: iso-3166, openness: unknown } ]\ntiming:\n  start: { system: iso-3166, at: IR, unit: day }",
         "timing[start].system 'iso-3166' is not a declared anchor_systems where dimension is ['time', 'any']"),
        ("a location is a place", "located_at: [ { system: iso-3166, openness: unknown } ]",
         'located_at: [ { system: gregorian-civil, openness: here, at: "2026-09-28" } ]',
         "located_at[0].system 'gregorian-civil' is not a declared anchor_systems where dimension is ['place']")):
    out = gate(old, new)
    check("a system chooser takes the dimension its meaning names: " + why, want in out, out[-900:])

# ---- the reckoner reads the equation -------------------------------------------------------------------------------------
gate()
def reading(steps, name):
    p = os.path.join(T, name + ".yaml")
    open(p, "w").write("steps:\n" + "".join(f"  - {s}\n" for s in steps))
    r = run(sys.executable, os.path.join(G, "bin", "dmreckon.py"), "--ad-hoc", p, "--bean", "two-times-two", cwd=G)
    return r.stdout + r.stderr
got = {by: re.search(r"^= (.*)$", reading([f'{{ id: w, op: window, series: "series.by-grid", channel: value, by: {by} }}'], by), re.M)
       for by in ("sum", "product", "count")}
check("the reckoner's window reads a sequence's whole by the law's aggregates: sum 4, product 4, count 2",
      all(got.values()) and got["sum"].group(1) == "4 item" and got["product"].group(1) == "4 item"
      and got["count"].group(1) == "2 item", {k: v.group(1) if v else None for k, v in got.items()})
out = reading(['{ id: n, op: window, series: "series.by-grid", channel: value, by: count }',
               '{ id: each, op: window, series: "series.by-grid", channel: value, by: first }',
               '{ id: times, op: multiply, of: n, with: each }',
               '{ id: whole, op: window, series: "series.by-grid", channel: value, by: sum }',
               '{ id: holds, op: compare, of: times, with: whole, is: equal }'], "equation")
check("...and the equation holds: the count of nodes times a node is the whole", re.search(r"^= true$", out, re.M), out[-600:])

# ---- the law holds its new words to themselves ---------------------------------------------------------------------------
std = os.path.join(G, "seed", "std-vocab.md")
law = open(std).read()
open(std, "w").write(law.replace("  - system: ordinal-number\n    dimension: any\n", "  - system: ordinal-number\n    dimension: time\n", 1))
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
out = out.stdout + out.stderr
check("`datum: line` belongs to a system of dimension `any`: one of time has a first of its own",
      "`datum: line` counts from the first of whatever line it is read on, and this system is one of 'time'" in out, out[-700:])
open(std, "w").write(law.replace("  - system: ordinal-number\n    dimension: any\n    datum: line\n",
                                  "  - system: ordinal-number\n    dimension: any\n    datum: named\n", 1))
out = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
out = out.stdout + out.stderr
check("`datum: named` belongs to a system whose form names the position it follows or precedes (`event-anchored`)",
      "`datum: named` is the position a position names" in out, out[-700:])
open(std, "w").write(law)
rules = run(sys.executable, os.path.join(G, "bin", "dmrules.py"), cwd=G).stdout
check("the rules a garden prints show the ordinal line, of domain any", re.search(
    r"^  ordinal +sequence +lines 1 · metered none · order total · acyclic True · ends open-end · domain any", rules, re.M))

shutil.rmtree(T, ignore_errors=True)
print("\nordinal: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
