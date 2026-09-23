#!/usr/bin/env python3
"""Recurrence (std-vocab 16.2): a repetition strides by neighbours, by measure, or by the cells of a level — and which
it may use is read from the aspect and from the shape of the system it names, never from the gate."""
import os, sys, subprocess, tempfile, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmrec-"); G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, "--gardener", "keeper", cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
v = os.path.join(G, "VOCAB.md"); s = open(v).read()
TERM = """local_terms:
  - term: upkeep
    meaning: "something done to this being again and again, and the region it covers"
    context_keys: [upkeep]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        what:   { required: true, in: prose }
        when:   { required: true, in: recurrence }
        covers: { in: extent }
    merge: { cardinality: multi, order: by-key }"""
assert s.count("local_terms: []") == 1
open(v, "w").write(s.replace("local_terms: []", TERM))

def gate(when, covers=""):
    open(os.path.join(G, "beans", "box.md"), "w").write(f"""---
bean: box
kind: host
title: "a machine"
status: active
summary: "probe"
nature: physical
identity: {{ status: confirmed, anchors: [ {{ key: serial, value: "SN-REC-1", class: hardware, establishing: true }} ] }}
provenance: {{ src: observed, by: probe, as_of: 2026-09-20 }}
owned_by: {{ legal: {{ external: "someone" }} }}
responsibility: {{ legal: {{ external: "someone" }} }}
upkeep:
  a-thing: {{ what: "w", when: {when}{covers} }}
---

probe.
""")
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

ok = lambda out: "0 error" in out
check("every 5 minutes — a stride by MEASURE on time", ok(gate("{ of: time, every: { count: 5, unit: minute } }")))
check("every 5 METRES — the same construct on place, because `geographic` is metered and says so",
      ok(gate("{ of: place, in: geographic, every: { count: 5, unit: metre } }")))
out = gate("{ of: place, every: { count: 5, unit: metre } }")
check("...and without the system it is refused: `place` itself claims no measure", "neither aspect 'place' nor the system it names is metered" in out, out[-500:])
out = gate("{ of: place, in: geographic, every: { count: 5, unit: minute } }")
check("a minute is not a length", "measures duration, and a stride here is measured in length" in out, out[-500:])
check("every 10th RELEASE — a stride by NEIGHBOURS, on a sequence with no meter at all",
      ok(gate("{ of: time, in: event-anchored, every: { count: 10 } }")))
out = gate("{ of: place, in: osm, every: { count: 3 } }")
check("a system whose positions have no next one has no Nth", "declares `neighbours: none`" in out, out[-500:])
check("the 15th of each PERSIAN month — a stride by CELL, in the calendar whose month it is",
      ok(gate('{ of: time, in: persian-calendar, each: month, at: "15" }')))
check("each ISO week — a different partition of the same days", ok(gate('{ of: time, in: iso-week, each: week, at: "5" }')))
out = gate('{ of: time, each: month, at: "15" }')
check("`each: month` with no calendar is NOBODY'S month", "a level belongs to its system" in out, out[-600:])
out = gate('{ of: time, in: iso-week, each: month }')
check("the week calendar has no months", "has no level 'month'" in out, out[-500:])
out = gate('{ of: time, in: geographic, each: month }')
check("a system must position in the dimension its aspect holds", "positions in 'place', and aspect 'time' holds 'time'" in out, out[-500:])
out = gate("{ of: necessity, every: { count: 2 } }")
check("nothing repeats on an opposition: its positions have no neighbours", "its positions have no neighbours" in out, out[-500:])
out = gate("{ of: time, every: { count: 5, unit: minute }, each: day }")
check("a repetition strides ONE way", "exactly one" in out, out[-400:])
check("an EXTENT may name a system too: a region of 200 metres", ok(gate("{ of: time, every: { count: 1, unit: day } }", ", covers: { of: place, in: geographic, measure: { count: 200, unit: metre } }")))

# HOW MANY TIMES (21.0): six instalments, the first included — a count of occurrences, so a positive whole number.
check("`times: 6` — six occurrences in all, the first included",
      ok(gate('{ of: time, in: gregorian-civil, each: month, at: "15", times: 6 }')))
for bad in ("0", "1.5", "-2", "true", '"six"'):
    out = gate('{ of: time, in: gregorian-civil, each: month, at: "15", times: %s }' % bad)
    check(f"`times: {bad}` is refused: a count of occurrences is a positive whole number", "must be a positive whole number" in out, out[-500:])

shutil.rmtree(T, ignore_errors=True)
print("\nrecurrence: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
