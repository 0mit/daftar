#!/usr/bin/env python3
"""The prose documents say nothing the repository can show to be false.

The law is held consistent by the other suites; the prose around it was checked by nobody. This one checks what
can be COMPUTED about a document: that it names no construct the language has retired, that every tool and suite
it names exists, that the suites a contributor is told to run are the suites the release runs, and that a page made of
another's text — the skill of AGENTS.md, the forms of the cookbook's recipes — holds it byte for byte. Whether a
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
         ".claude/skills/daftar/SKILL.md", ".github/pull_request_template.md", "AGENTS.md", "seed/WELCOME.md",
         "seed/FORMS.md"]
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
_retired = {str(r["name"]): r.get("at") for r in (_law.get("retired") or []) if isinstance(r, dict)
            and r.get("at") in ("bean", "anchor", "manifest")}
assert len(_retired) >= 8, "the law's list of retired keys was not found"
# A NAME RETIRED IN ONE PLACE MAY BE LIVE IN ANOTHER: `created` left the manifest and is still a registration's date;
# `authority` left the anchor and is still a term. Such a name is looked for only where it was retired — at the head
# of a GARDEN.md block's line, inside an anchor's mapping, at the head of a bean's line — and any other is looked for
# wherever a key is written.
_live = set()
def _collect(node):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "attrs" and isinstance(v, (dict, list)):
                _live.update(str(x) for x in v if isinstance(x, (str, int)))
            if k in ("term", "kind", "genos") and isinstance(v, str):
                _live.add(v)
            _collect(v)
    elif isinstance(node, list):
        for x in node:
            _collect(x)
_collect({k: v for k, v in _law.items() if k != "retired"})
_live.update(str(k) for k in _law)
assert "created" in _live and "scope" not in _live, "the law's live names were not read"
_FENCE = re.compile(r"(?ms)^(`{3,})[^\n]*\n(.*?)^\1[ \t]*$")
def _manifest_blocks(t):
    """The fenced blocks of a document that are a GARDEN.md: marked as one, or pinning the standard as it does."""
    out = []
    for m in _FENCE.finditer(t):
        lead = t[:m.start()].rstrip("\n").rsplit("\n", 1)[-1]          # the line just above the fence
        if "GARDEN.md" in lead or "extends: std-vocab@" in m.group(2):
            out.append(m.group(2))
    return out
def _written(w, at, t):
    e = re.escape(w)
    if w not in _live:
        return re.search(r"(?m)^%s:|[{,]\s*%s:|`%s:" % (e, e, e), t)
    if at == "anchor":
        return re.search(r"(?m)^.*\bkey:.*\bvalue:.*[{,]\s*%s:|^.*[{,]\s*%s:.*\bkey:.*\bvalue:" % (e, e), t)
    if at == "manifest":
        return any(re.search(r"(?m)^%s:" % e, b) for b in _manifest_blocks(t))
    return re.search(r"(?m)^%s:" % e, t)
for d, t in text.items():
    hit = sorted(w for w, at in _retired.items() if _written(w, at, t))
    check(f"{d} writes no key the law retired", not hit, hit)
_probe = "```yaml\nregistration: { created: 2020-01-15 }\n```\n<!-- example-front-matter: GARDEN.md -->\n```yaml\ngardener: sam\n```\n"
check("...and a name the law retired in one place is not taken for a key where it is still live",
      not _written("created", "manifest", _probe) and _written("created", "manifest", _probe.replace("gardener: sam", "created: x"))
      and not _written("authority", "anchor", "authority: { source: x }\n")
      and _written("authority", "anchor", "  - { key: fqdn, value: x, authority: scanned }\n"),
      "the context of a retired name that is live elsewhere is not read")

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

# THE FORMS ARE THE COOKBOOK'S OWN RECIPES, NOT A SECOND COPY THAT CAN DRIFT (v0.34.1). seed/FORMS.md is what an agent
# reads before writing: six recipes of the cookbook, cut from it unchanged, and the forms for what nobody said. A recipe
# changed in one and not the other fails here, by name; the fix is to copy the cookbook's section into the forms again.
def _sections(t):
    return {s.split("\n", 1)[0]: s for s in t.split("\n## ")[1:]}
_ck, _fo = _sections(text["seed/COOKBOOK.md"]), _sections(text["seed/FORMS.md"])
_recipes = [h for h in _fo if h in _ck]
_drift = [h for h in _recipes if _fo[h] != _ck[h]]
check("seed/FORMS.md holds six recipes of seed/COOKBOOK.md, each byte for byte as the cookbook has it",
      len(_recipes) == 6 and not _drift and _recipes[0] == "The gardener, first",
      f"recipes {_recipes}; differing from the cookbook (copy its section again): {_drift}")
check("...and nothing else but the forms for what nobody said", set(_fo) - set(_recipes) == {"What nobody said"},
      sorted(set(_fo) - set(_recipes)))
_ord = [h for h in _ck if h in _recipes]
check("...in the cookbook's own order, so they can be followed from the top", _recipes == _ord, (_recipes, _ord))
_top = "\n".join(text["seed/FORMS.md"].split("\n## ", 1)[0].splitlines())
# ONE COMMAND SAVES (v0.34.1): the entry, `git add -A` and the commit were three calls, and a refused one needed two more.
check("...and its opening says how a bean is saved — one command, and `--again` after a refusal — and that the law is "
      "read only for what it does not answer",
      'python3 bin/dmsave.py "<who>" "<what you did>" --body "' in _top and "python3 bin/dmsave.py --again" in _top
      and "AGENTS.md" in _top and len(_top) < 2000, _top[:400])
check("AGENTS.md saves a write in one command, and says what to run after a refusal",
      'python3 bin/dmsave.py "<who>" "<what changed>" --body "' in text["AGENTS.md"]
      and "python3 bin/dmsave.py --again" in text["AGENTS.md"], "")
check("AGENTS.md puts the forms first for writing, and the law after them, on demand",
      0 <= text["AGENTS.md"].find("seed/FORMS.md") < text["AGENTS.md"].find("## On demand")
      < text["AGENTS.md"].find("`MODEL.md`", text["AGENTS.md"].find("## On demand")), "")

ci = open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8").read()
ci_suites = set(re.findall(r"python3 (test/[a-z_]+\.py)", ci))
assert ci_suites, "no suite was found in the workflow"
told = set(re.findall(r"(?m)^\s*python3 (test/[a-z_]+\.py)\s*$", text["CONTRIBUTING.md"]))  # one command a line
check("CONTRIBUTING.md tells a contributor to run exactly the suites the release runs",
      told == ci_suites, f"only in CI: {sorted(ci_suites - told)}; only in the document: {sorted(told - ci_suites)}")
on_disk = {"test/" + f for f in os.listdir(os.path.join(ROOT, "test")) if f.endswith(".py")}
check("...and the release runs every suite that is shipped", on_disk - GARDEN_ONLY == ci_suites,
      f"not run: {sorted(on_disk - GARDEN_ONLY - ci_suites)}; run but absent: {sorted(ci_suites - on_disk)}")

print("\ndocs: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
