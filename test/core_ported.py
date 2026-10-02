#!/usr/bin/env python3
"""Where each of today's suites went in v1 (part 12), held to what the tree shows (test/ported.yaml).

Part 12 of v1 ported today's suites to the core's statements, or replaced them by suites of the core that hold the same
promise, so that the release that deletes seed/std-vocab.md and bin/dmcheck.py (part 13) can do so with the whole list
green. test/ported.yaml says, for each of today's suites, what became of it, and this holds the file to the tree:

  retired   a suite the core's suites replace is gone from the tree, from the workflow's list and from CONTRIBUTING.md;
            each of its promises is `held` by checks the tree has — `<suite>: <words of a check>`, the words found in
            that suite's source, and the suite one the release runs — or `gone`, or `left`, each saying why
  ported    a suite rewritten in a garden of the core is one the release runs, and it grows no garden in today's words,
            runs no today's gate and reads no today's law
  waiting   a suite that still reads today's law is named with the part that takes it and why — and every other suite
            the release runs reads none of it: no `seed/std-vocab.md`, no `bin/dmcheck.py`, no `seed/germinate.sh`, and
            no garden germinated from this tree's own seed (which pins today's law until part 13)
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


# TODAY'S WORDS, AS A SUITE WOULD REACH THEM: today's law, today's gate, a garden germinated in today's words
TODAY = [("seed/std-vocab.md", re.compile(r"std-vocab\.md")),
         ("bin/dmcheck.py", re.compile(r"dmcheck\.py|['\"]dmcheck['\"]|import dmcheck")),
         ("seed/germinate.sh", re.compile(r"germinate\.sh")),
         ("this tree's seed/germinate.py", re.compile(r"ROOT,\s*['\"]seed['\"],\s*['\"]germinate\.py|"
                                                      r"ROOT,\s*['\"]seed/germinate\.py"))]


def reaches(suite):
    return [what for what, rx in TODAY if rx.search(source(suite))]


retired = MAP.get("retired") or []
ported = MAP.get("ported") or []
waiting = MAP.get("waiting") or []

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

# ---- waiting, and every other suite reads none of today's words
named = {w["suite"] for w in waiting}
bad_wait = [w for w in waiting if not (w.get("part") and w.get("why") and (w["suite"] in CI or w["suite"] in
                                                                             MAP.get("not_listed", [])))]
check(f"each of the {len(waiting)} suites still reading today's law names the part that takes it, and why",
      not bad_wait, bad_wait)
listed = sorted(set(CI) | set(MAP.get("not_listed", [])))
stray = [(s, reaches(s)) for s in listed if s not in named and s != "test/core_ported.py" and reaches(s)]
check(f"every other suite the release runs ({len(listed) - len(named)}) reaches none of today's words: no today's law, "
      f"no today's gate, no garden germinated in today's words", not stray, stray)
idle = [s for s in named if not reaches(s)]
check("...and a suite said to be waiting does still reach them (else it is ported, and says so)", not idle, idle)

# ---- the count
met = MAP.get("met") or []
accounted = [r["suite"] for r in retired] + [p["suite"] for p in ported] + \
            [w["suite"] for w in waiting if not os.path.basename(w["suite"]).startswith("core")]
check(f"the {len(met)} suites part 12 met reading today's words are each accounted for once: retired, ported, or "
      f"waiting", met and sorted(met) == sorted(accounted) and len(set(accounted)) == len(accounted),
      {"unaccounted": sorted(set(met) - set(accounted)), "not met": sorted(set(accounted) - set(met)),
       "twice": sorted({s for s in accounted if accounted.count(s) > 1})})

print(f"\ncore_ported: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
