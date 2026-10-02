#!/usr/bin/env python3
"""Where each of today's suites went in v1 (parts 12 and 13b), held to what the tree shows (test/ported.yaml).

Part 12 of v1 ported today's suites to the core's statements, or replaced them by suites of the core that hold the same
promise; part 13 deleted today's law, gate and merge, and part 13b moved the last that waited. test/ported.yaml says,
for each of today's suites, what became of it, and this holds the file to the tree:

  retired   a suite the core's suites replace is gone from the tree, from the workflow's list and from CONTRIBUTING.md;
            each of its promises is `held` by checks the tree has — `<suite>: <words of a check>`, the words found in
            that suite's source, and the suite one the release runs — or `gone`, or `left`, each saying why
  ported    a suite rewritten in a garden of the core is one the release runs, and it reaches none of today's words
  today     a suite whose subject is a garden in today's words reads them from the last release that had them
            (`from: v0.49.0`, through test/grow.py) — or holds that the release carries none (`from: gone`); every
            other suite the release runs reaches none of today's words: no `seed/std-vocab.md`, no today's gate or merge
            (`bin/dmcheck.py`, `bin/dmmerge.py`), no tool by today's name (`bin/dm<verb>.py`, but the door
            `bin/dmupgrade.py`)
  none waits no suite is `waiting` for a part of v1 any more
  the gate  each of today's gate's checks (v0.49.0's bin/dmcheck.py, every `check_*`, read from that tag) is named once,
            and went to a rule the core has, to the law's own proof, to a tool the release has — each saying how — or
            is gone, saying why
  the count  the suites part 12 met reading today's words are all accounted for, each once

Run: python3 test/core_ported.py   (0 = green; under a second)
"""
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def text(rel):
    with open(os.path.join(ROOT, *rel.split("/")), encoding="utf-8") as fh:
        return fh.read()


MAP = yaml.safe_load(text("test/ported.yaml"))
CI = re.findall(r"python3 (test/[a-z_]+\.py)", text(".github/workflows/ci.yml"))
TOLD = re.findall(r"(?m)^\s*python3 (test/[a-z_]+\.py)\s*$", text("CONTRIBUTING.md"))
SOURCE = {}


def source(suite):
    if suite not in SOURCE:
        SOURCE[suite] = text(suite) if os.path.isfile(os.path.join(ROOT, suite)) else ""
    return SOURCE[suite]


# TODAY'S WORDS, AS A SUITE WOULD REACH THEM: today's law, today's gate and merge, a tool by today's name — all of
# them the last release's in today's words (v0.49.0) since part 13, and none this tree's; and where a suite takes them
TODAY = [("seed/std-vocab.md", re.compile(r"std-vocab\.md")),
         ("today's gate or merge", re.compile(r"dmcheck|dmmerge")),
         ("a tool by today's name", re.compile(r"\bdm(?!upgrade\b)[a-z]+\.py"))]
FROM_TODAY = re.compile(r"grow\.today(?:_file)?\(|grow_today\(")


def reaches(suite):
    return [what for what, rx in TODAY if rx.search(source(suite))] + \
        (["v0.49.0, through test/grow.py"] if FROM_TODAY.search(source(suite)) else [])


retired = MAP.get("retired") or []
ported = MAP.get("ported") or []
today = MAP.get("today") or []

# ---- retired
gone_still = [r["suite"] for r in retired if os.path.isfile(os.path.join(ROOT, r["suite"])) or r["suite"] in CI
              or r["suite"] in TOLD]
check(f"each of the {len(retired)} retired suites is gone from the tree, the workflow's list and CONTRIBUTING.md",
      retired and not gone_still, gone_still)
bad_promise, bad_held = [], []
for r in retired:
    for p in r.get("promises") or []:
        kinds = [k for k in ("held", "gone", "left") if p.get(k)]
        if not p.get("promise") or len(kinds) != 1:
            bad_promise.append((r["suite"], p.get("promise"), kinds))
        for ref in p.get("held") or []:
            suite, _sep, words = str(ref).partition(": ")
            listed_ok = suite in CI or suite == "test/core-cases.yaml"
            if not (words and listed_ok and words in source(suite)):
                bad_held.append((r["suite"], ref))
    if not r.get("promises"):
        bad_promise.append((r["suite"], "no promise named", []))
check("each promise is said, and is held, gone or left — one of the three, with what or why",
      not bad_promise, bad_promise[:6])
n_held = sum(len(p.get("held") or []) for r in retired for p in r.get("promises") or [])
check(f"each of the {n_held} checks a promise is held by is in a suite the release runs (or the core's cases), in "
      f"the words the map quotes", n_held and not bad_held, bad_held[:8])

# ---- ported
not_run = [p["suite"] for p in ported if p["suite"] not in CI and p["suite"] not in (MAP.get("not_listed") or [])]
reaching = [(p["suite"], reaches(p["suite"])) for p in ported if reaches(p["suite"])]
check(f"each of the {len(ported)} suites ported in place is one the release runs, and reaches none of today's words",
      ported and not not_run and not reaching, (not_run, reaching))

# ---- today's words: read from v0.49.0, or held gone — and by no other suite
check("no suite waits for a part of v1: `waiting` is gone from the map", "waiting" not in MAP, MAP.get("waiting"))
named = {w["suite"] for w in today}
bad_today = [w for w in today if not (w.get("why") and w.get("from") in ("v0.49.0", "gone") and w["suite"] in CI)
             or (w.get("from") == "v0.49.0" and not FROM_TODAY.search(source(w["suite"])))]
check(f"each of the {len(today)} suites that read today's words says why, is one the release runs, and reads them from "
      f"v0.49.0 through test/grow.py (or holds that they are gone)", today and not bad_today, bad_today)
listed = sorted(set(CI) | set(MAP.get("not_listed", [])))
stray = [(s, reaches(s)) for s in listed if s not in named and s != "test/core_ported.py" and reaches(s)]
check(f"every other suite the release runs ({len(listed) - len(named)}) reaches none of today's words: no today's law, "
      f"no today's gate or merge, no tool by today's name, nothing of v0.49.0", not stray, stray)
idle = [s for s in named if not reaches(s)]
check("...and a suite said to read them does (else it says nothing of today's words, and leaves the list)", not idle, idle)

# ---- today's gate: where each of its checks went
import ast  # noqa: E402
sys.path.append(os.path.join(ROOT, "test"))
import grow  # noqa: E402 — v0.49.0's files, read from the tag
TODAY_GATE = sorted(n.name[len("check_"):] for n in ast.parse(grow.today_file("bin/dmcheck.py")).body
                    if isinstance(n, ast.FunctionDef) and n.name.startswith("check_"))
RULES = {r["rule"] for r in yaml.safe_load(text("core/law/core.yaml"))["rules"]}
gate = MAP.get("gate") or []
names = [g.get("check") for g in gate]
check(f"each of today's gate's {len(TODAY_GATE)} checks (v0.49.0's bin/dmcheck.py) is named once in the map",
      sorted(names) == TODAY_GATE and len(set(names)) == len(names),
      {"unnamed": sorted(set(TODAY_GATE) - set(names)), "no such check": sorted(set(names) - set(TODAY_GATE)),
       "twice": sorted({n for n in names if names.count(n) > 1})})
bad_gate = []
for g in gate:
    kinds = [k for k in ("rule", "law", "tool", "gone") if g.get(k)]
    if len(kinds) != 1:
        bad_gate.append((g.get("check"), "not one of rule, law, tool, gone"))
    elif kinds == ["rule"] and (g["rule"] not in RULES or not g.get("how")):
        bad_gate.append((g.get("check"), f"rule {g['rule']!r}: no rule of the core's, or no how"))
    elif kinds == ["tool"] and (not os.path.isfile(os.path.join(ROOT, *str(g["tool"]).split("/"))) or not g.get("how")):
        bad_gate.append((g.get("check"), f"tool {g['tool']!r}: not in the release, or no how"))
went = {k: sum(1 for g in gate if g.get(k)) for k in ("rule", "law", "tool", "gone")}
check(f"...each went to a rule of the core ({went['rule']}), the law's own proof ({went['law']}) or a tool of the "
      f"release ({went['tool']}), saying how — or is gone, saying why ({went['gone']})", gate and not bad_gate, bad_gate)

# ---- the count
met = MAP.get("met") or []
accounted = [r["suite"] for r in retired] + [p["suite"] for p in ported]
check(f"the {len(met)} suites part 12 met reading today's words are each accounted for once: retired, or ported", met and sorted(met) == sorted(accounted) and len(set(accounted)) == len(accounted),
      {"unaccounted": sorted(set(met) - set(accounted)), "not met": sorted(set(accounted) - set(met)),
       "twice": sorted({s for s in accounted if accounted.count(s) > 1})})

print(f"\ncore_ported: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
