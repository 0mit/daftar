#!/usr/bin/env python3
"""The prose documents say nothing the repository can show to be false.

The law is held consistent by the other suites; the prose around it was checked by nobody. This one checks what
can be COMPUTED about a document: that it names no construct the language has retired, that every tool and suite
it names exists, that the suites a contributor is told to run are the suites the release runs, and that a page made of
another's text — the skill of AGENTS.md, the forms of the cookbook's recipes — holds it byte for byte. Whether a
paragraph is true, or can be read two ways, is still a reader's work. The examples a document shows are committed
in a fresh garden by `test/germinate.py`; this does not repeat that.
"""
import subprocess
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

# HISTORY.md and the vocabulary's changelog are the record of what WAS: a retired name belongs there.
PROSE = ["README.md", "MODEL.md", "CHECKLIST.md", "MERGE.md", "CONTRIBUTING.md", "seed/README.md", "seed/COOKBOOK.md",
         ".claude/skills/daftar/SKILL.md", ".github/pull_request_template.md", "AGENTS.md", "seed/WELCOME.md",
         "seed/FORMS.md", "MANIFESTO.md", "CHARTER.md"]
# Named in a document as NOT shipped here: the maintainers' corpus tests, which need a garden's beans.
NOT_SHIPPED = {"test/golden.py", "test/diffgate.py"}
# Shipped, and run by every garden's own hook rather than by the release: it needs a garden around it.
GARDEN_ONLY = {"test/fast.py"}
# measurements, not suites: they run the suites (timings.py) or time the gate (cost.py), and CONTRIBUTING.md says how
MEASURES = {"test/timings.py", "test/cost.py"}
# a module the suites import, not a suite: test/grow.py grows a garden of the core (v1 part 12)
HELPERS = {"test/grow.py", "test/machine.py"}   # and the suites' time source

text = {}
for d in PROSE:
    p = os.path.join(ROOT, d)
    check(f"{d} exists", os.path.isfile(p))
    text[d] = open(p, encoding="utf-8").read() if os.path.isfile(p) else ""

sys.path.insert(0, os.path.join(ROOT, "bin"))
sys.path.insert(0, ROOT)
sys.path.append(os.path.join(ROOT, 'test'))   # last: test/core.py is no package `core`
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
# A BEAN IS WRITTEN IN THE CORE'S WORDS (v1 part 13). A bean a document shows holds the core's header — `bean` (or
# `mapping`), `kind`, `title`, `summary`, `tags`, `details`, `statements` — and nothing else at its head: one of today's
# terms there (each went somewhere in the core: core/law/terms.yaml) teaches a refusal.
from core.engine import HEADER  # noqa: E402
from core import read as _read  # noqa: E402
_today = {str(r["term"]) for r in _read.data(os.path.join(ROOT, "core", "law", "terms.yaml"))["terms"]}
assert len(_today) >= 50, "today's terms were not read"
_FENCE = re.compile(r"(?ms)^(`{3,})[^\n]*\n(.*?)^\1[ \t]*$")
for d, t in text.items():
    hit = set()
    for m in _FENCE.finditer(t):
        fm = re.match(r"---\n(.*?)\n---", m.group(2), re.S)
        if fm and re.search(r"(?m)^(bean|mapping):", fm.group(1)):
            hit |= {k for k in re.findall(r"(?m)^([a-z_]+):", fm.group(1)) if k not in HEADER}
    check(f"{d}'s beans hold the core's header and statements, and no key of today's", not hit, sorted(hit))
check("...and a word of today's is known by its place in core/law/terms.yaml", {"owned_by", "status", "nature"} <= _today)

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

# THE FORMS ARE THE COOKBOOK'S OWN EXAMPLES, NOT A SECOND COPY THAT CAN DRIFT (v0.34.1). seed/FORMS.md is what an agent
# reads before writing, so it is short: the misreadings agents make most, the shapes of six recipes — each recipe's
# example beans and commands, the fenced blocks with the marker above them, cut from the cookbook unchanged, under the
# recipe's heading and its first sentence — and the forms for what nobody said. The recipes' prose stays in the cookbook
# (it was two thirds of the page, and measured runs read all of it every session). A block changed in one and not the
# other fails here, by recipe; the fix is to copy the cookbook's blocks into the forms again.
def _sections(t):
    return {s.split("\n", 1)[0]: s for s in t.split("\n## ")[1:]}
def _blocks(sec):
    return re.findall(r"(?:^<!-- [^\n]*-->\n)?^```[^\n]*\n.*?^```$", sec, re.S | re.M)
_ck, _fo = _sections(text["seed/COOKBOOK.md"]), _sections(text["seed/FORMS.md"])
_recipes = [h for h in _fo if h in _ck]
# THE FORMS CARRY NO FACT (v0.34.1): each block is the cookbook's as the law derives it — a day someone said shown empty
# with the law's meaning beside it, `as_of: now`, no day inside an anchor — so the check is the derivation, not a copy.
_derived = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "forms.py"), "--check"], capture_output=True, text=True, encoding="utf-8", errors="replace")
check("seed/FORMS.md holds the gardener's own form and the shapes of five recipes of seed/COOKBOOK.md, every example "
      "block exactly as bin/forms.py derives it from the cookbook's by the core's law", len(_recipes) == 5
      and _derived.returncode == 0 and list(_fo)[1] == "The gardener, first", f"recipes {_recipes}; {_derived.stderr.strip()}")
_days = [l.strip() for l in text["seed/FORMS.md"].split("\n")
         if re.search(r"\b\d{4}-\d{2}-\d{2}\b", l) and "the example's — write the moment someone said" not in l]
check("...and no calendar day in them but a moment a role requires, which keeps the example's and says so: a day in a "
      "form is the day a writer copies", not _days, _days)
check("...and nothing else but the misreadings, first, and the forms for what nobody said",
      set(_fo) - set(_recipes) == {"What nobody said", "Common misreadings", "The gardener, first"}
      and list(_fo)[0] == "Common misreadings",
      sorted(set(_fo) - set(_recipes)))
_kept = [l for l in text["seed/FORMS.md"].split("\n") if "the example's — write the moment someone said" in l]
check("...and every moment a form keeps because its verb requires it says it is the example's, and the one to write is "
      "the moment someone said; no line says 'empty unless said' (the core has no empty value)",
      _kept and "empty unless said" not in text["seed/FORMS.md"], _kept)
check("...and it stays short: under 17,700 characters", len(text["seed/FORMS.md"]) < 17700, len(text["seed/FORMS.md"]))
_ord = [h for h in _ck if h in _recipes]
check("...in the cookbook's own order, so they can be followed from the top", _recipes == _ord, (_recipes, _ord))
_top = "\n".join(text["seed/FORMS.md"].split("\n## ", 1)[0].splitlines())
# ONE COMMAND SAVES (v0.34.1): the entry, `git add -A` and the commit were three calls, and a refused one needed two more.
check("...and its opening says how a bean is saved — one command, and `--again` after a refusal — and that the law is "
      "read only for what it does not answer",
      'python3 bin/save.py "<who>" "<what you did>" --body "' in _top and "python3 bin/save.py --again" in _top
      and "AGENTS.md" in _top and len(_top) < 2000, _top[:400])
check("AGENTS.md saves a write in one command, and says what to run after a refusal",
      'python3 bin/save.py "<who>" "<what changed>" --body "' in " ".join(text["AGENTS.md"].split())
      and "python3 bin/save.py --again" in " ".join(text["AGENTS.md"].split()), "")
check("AGENTS.md puts the forms first for writing, and the law after them, on demand",
      0 <= text["AGENTS.md"].find("seed/FORMS.md") < text["AGENTS.md"].find("## On demand")
      < text["AGENTS.md"].find("`MODEL.md`", text["AGENTS.md"].find("## On demand")), "")

# THE PROFILES MODEL.md NAMES ARE THE LAW'S. MODEL.md lists them for a reader who has not opened the law; a list kept by
# hand is a second statement, so it is held equal to what the law offers — a profile added to the law and not named
# here, or one named here the law no longer offers, fails by name.
_offered = sorted(_read.data(os.path.join(ROOT, "core", "law", "profiles.yaml")) and
                  [str(p["profile"]) for p in _read.data(os.path.join(ROOT, "core", "law", "profiles.yaml"))["profiles"]])
_listed = re.search(r"\*\*Profiles\*\* — ([a-z, ]+) — stand on the core", text["MODEL.md"])
_named = sorted(w.strip() for w in _listed.group(1).split(",")) if _listed else None
check("MODEL.md names exactly the profiles the law offers", _named == _offered and len(_offered) >= 5,
      f"MODEL.md: {_named}; the law: {_offered}")

ci = open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8").read()
ci_suites = set(re.findall(r"python3 (test/[a-z_]+\.py)", ci))
assert ci_suites, "no suite was found in the workflow"
told = set(re.findall(r"(?m)^\s*python3 (test/[a-z_]+\.py)\s*$", text["CONTRIBUTING.md"]))  # one command a line
check("CONTRIBUTING.md tells a contributor to run exactly the suites the release runs",
      told == ci_suites, f"only in CI: {sorted(ci_suites - told)}; only in the document: {sorted(told - ci_suites)}")
on_disk = {"test/" + f for f in os.listdir(os.path.join(ROOT, "test")) if f.endswith(".py")}
check("...and the release runs every suite that is shipped", on_disk - GARDEN_ONLY - MEASURES - HELPERS == ci_suites,
      f"not run: {sorted(on_disk - GARDEN_ONLY - MEASURES - HELPERS - ci_suites)}; run but absent: {sorted(ci_suites - on_disk)}")
check("...and every measurement shipped is one CONTRIBUTING.md says how to run",
      all(("python3 " + m) in text["CONTRIBUTING.md"] for m in MEASURES & on_disk), sorted(MEASURES & on_disk))
# A MEASUREMENT NAMES A SUITE THAT RUNS. test/timings.tsv is keyed by a suite's path, and the reckoner orders the loop by
# it; a row under a name no suite answers to any more is read by nothing (test/mycelium.py's, after it became peering).
_timed = {c[1] for c in (ln.split("\t") for ln in open(os.path.join(ROOT, "test", "timings.tsv"), encoding="utf-8").read()
                          .splitlines()[1:]) if len(c) == 5 and c[1].startswith("test/")}
check("...and every suite test/timings.tsv measures is one the release runs", _timed and not _timed - ci_suites,
      sorted(_timed - ci_suites))

# THE TERMS A GARDEN RECEIVES are daftar's own texts, byte for byte. A garden gets them under seed/ (`seed/LICENSE.md` and
# `seed/LICENSE-<id>.txt`), never at its root, where they would read as the garden's own licence and an upgrade would
# overwrite the gardener's. A copy is a second statement; this holds it equal to the first.
_lic = {os.path.relpath(f, ROOT).replace(os.sep, "/"): "LICENSES/" + os.path.basename(f)[len("LICENSE-"):]
        for f in glob.glob(os.path.join(ROOT, "seed", "LICENSE-*.txt"))}
_texts = {"LICENSES/" + os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "LICENSES", "*.txt"))}
_differ = [a for a, b in sorted(_lic.items()) if not os.path.isfile(os.path.join(ROOT, b))
           or open(os.path.join(ROOT, a), "rb").read() != open(os.path.join(ROOT, b), "rb").read()]
check("every licence text a garden receives under seed/ is the repository's own in LICENSES/, byte for byte, and "
      "every one of them is there", len(_lic) >= 6 and not _differ and set(_lic.values()) == _texts,
      f"differ: {_differ}; missing from seed/: {sorted(_texts - set(_lic.values()))}")
# NO DOCUMENT NAMES A LICENCE THE REPOSITORY IS NOT UNDER. A stale line saying another licence is a second statement of the
# terms, and read against whoever wrote it. NOTICE says, once, what the releases before it were under; the history is
# the record of what was.
_other = re.compile(r"Apache[- ]2\.0|Apache License|MIT License|\bGPL-2\.0|\bBSD-[23]-Clause")
_where = [f for f in subprocess.run(["git", "-C", ROOT, "ls-files"], capture_output=True, text=True,
                                    encoding="utf-8").stdout.split()
          if f.endswith((".md", ".html", ".py", ".toml")) and f not in ("HISTORY.md", "test/docs.py")
          and os.path.isfile(os.path.join(ROOT, f))
          and _other.search(open(os.path.join(ROOT, f), encoding="utf-8", errors="replace").read())]
check("no document names a licence the repository is not under (NOTICE says what came before)", not _where, _where)

print("\ndocs: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
