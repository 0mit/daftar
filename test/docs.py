#!/usr/bin/env python3
"""The prose documents say nothing the repository can show to be false.

The law is held consistent by the other suites; the prose around it was checked by nobody. This one checks what
can be COMPUTED about a document: that it names no construct the language has retired, that every tool and suite
it names exists, and that the suites a contributor is told to run are the suites the release runs. Whether a
paragraph is true, or can be read two ways, is still a reader's work. The examples a document shows are committed
in a fresh garden by `test/germinate.py`; this does not repeat that.
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

# HISTORY.md and the vocabulary's changelog are the record of what WAS: a retired name belongs there.
PROSE = ["README.md", "MODEL.md", "CHECKLIST.md", "MERGE.md", "CONTRIBUTING.md", "seed/README.md", "seed/COOKBOOK.md",
         ".claude/skills/daftar/SKILL.md", ".github/pull_request_template.md", "AGENTS.md", "seed/WELCOME.md"]
# Named in a document as NOT shipped here: the maintainers' corpus tests, which need a garden's beans.
NOT_SHIPPED = {"test/golden.py", "test/diffgate.py"}
# Shipped, and run by every garden's own hook rather than by the release: it needs a garden around it.
GARDEN_ONLY = {"test/fast.py"}

text = {}
for d in PROSE:
    p = os.path.join(ROOT, d)
    check(f"{d} exists", os.path.isfile(p))
    text[d] = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""

sys.path.insert(0, os.path.join(ROOT, "bin"))
src = open(os.path.join(ROOT, "bin", "dmcheck.py"), encoding="utf-8").read()
retired = eval(re.search(r"^RETIRED_CONSTRUCTS = (\(.*?\))\n", src, re.S | re.M).group(1))
assert len(retired) >= 10, "the retired-construct list was not found"            # an empty list would pass everything
import dmreform
owners = list(dmreform.RETIRED_OWNERS)
assert owners, "the retired-owner list was not found"

for d, t in text.items():
    hit = [w for w in retired if re.search(r"(?<![A-Za-z_])%s(?![A-Za-z_])" % re.escape(w), t)]
    check(f"{d} names no construct the schema language has retired", not hit, hit)
    # an owner term's name is often an ordinary word (`unit`, `role`); what is retired is the TERM, so look for the
    # two ways a document addresses a term: its positions (`unit.values`) and its declaration (`term: unit`).
    hit = [w for w in owners if re.search(r"(?<![A-Za-z_])%s\.values|term:\s*%s\b" % (w, w), t)]
    check(f"{d} addresses no owner term that a registry replaced", not hit, hit)

# A KEY THE LAW RETIRED IS NOT WRITTEN AS A KEY (21.0). The law lists what it took back (`retired:`), and the gate refuses
# each with where it went; a document that still writes one — `scope: global` in an example anchor, `attributes:` as
# the bag for a stray fact, a manifest's `seeds_from:` — teaches the refusal. A name at the head of a line, inside a
# flow mapping, or opening an inline code span is a key; the same word in a sentence is only a word.
import dmparse, yaml
_law = yaml.safe_load(dmparse.split_front_matter(open(os.path.join(ROOT, "seed", "std-vocab.md"), encoding="utf-8").read())[0])
_keys = sorted({str(r["name"]) for r in (_law.get("retired") or []) if isinstance(r, dict) and r.get("at") in ("bean", "anchor", "manifest")})
assert len(_keys) >= 8, "the law's list of retired keys was not found"
for d, t in text.items():
    hit = sorted({w for w in _keys if re.search(r"(?m)^%s:|[{,]\s*%s:|`%s:" % ((re.escape(w),) * 3), t)})
    check(f"{d} writes no key the law retired", not hit, hit)

for d, t in text.items():
    named = sorted(set(re.findall(r"(?<![A-Za-z0-9_/.-])((?:bin|test)/[A-Za-z0-9_./-]+\.(?:py|sh))", t)))
    gone = [n for n in named if n not in NOT_SHIPPED and not os.path.isfile(os.path.join(ROOT, n))]
    check(f"every tool and suite {d} names exists ({len(named)} named)", not gone, gone)

# THE DOORS. An agent with a shell has one text, wherever its tool looks for it; an assistant without one is told so
# before it is told anything else.
_skill = re.sub(r"^---\n.*?\n---\n\s*", "", text[".claude/skills/daftar/SKILL.md"], count=1, flags=re.S)
check("AGENTS.md and the daftar skill are ONE text: the skill is its front matter and then AGENTS.md, byte for byte",
      _skill == text["AGENTS.md"] and len(_skill) > 500, f"{len(_skill)} vs {len(text['AGENTS.md'])} bytes")
_top = "\n".join(text["seed/WELCOME.md"].splitlines()[:12])
check("seed/WELCOME.md says in its first lines that its reader cannot run the gate, and that what it reads is data",
      "cannot run the gate" in _top and "cannot write to the ledger" in _top and "data" in _top, _top[:300])
_opens = [p for p in re.findall(r"`([A-Za-z0-9_./-]+\.(?:md|py|sh))`", text["seed/WELCOME.md"])
          if not os.path.isfile(os.path.join(ROOT, p))]
check("...and names no file that does not exist", not _opens, _opens)

ci = open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8").read()
ci_suites = set(re.findall(r"python3 (test/[a-z_]+\.py)", ci))
assert ci_suites, "no suite was found in the workflow"
line = next((l for l in text["CONTRIBUTING.md"].splitlines() if "test/germinate.py" in l and "&&" in l), "")
told = set(re.findall(r"python3 (test/[a-z_]+\.py)", line))
check("CONTRIBUTING.md tells a contributor to run exactly the suites the release runs",
      told == ci_suites, f"only in CI: {sorted(ci_suites - told)}; only in the document: {sorted(told - ci_suites)}")
on_disk = {"test/" + f for f in os.listdir(os.path.join(ROOT, "test")) if f.endswith(".py")}
check("...and the release runs every suite that is shipped", on_disk - GARDEN_ONLY == ci_suites,
      f"not run: {sorted(on_disk - GARDEN_ONLY - ci_suites)}; run but absent: {sorted(ci_suites - on_disk)}")

print("\ndocs: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
