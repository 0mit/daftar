#!/usr/bin/env python3
"""The catalogue: every part of the language, how the parts relate, and what each is held to — generated, never kept.

bin/dmcatalog.py reads the release's own sources each time it runs. This holds it to what it says:

  every file      every file the tree would commit is a part, in the layer the law's map places it in, or named among
                  the files in no layer, which are the ones bin/dmpass.py names
  the law         every term of the law and of its profiles is a part, and carries the rules bin/dmrules.py prints for
                  it; every registry, section, profile and layer is a part; no part claims an item the law lacks
  every relation  both ends of every relation are parts, and every relation is of a kind the tool names
  read, not said  one known relation of each kind is found where it is written — an import, a module loaded by its path,
                  a directory put on sys.path, a hook's run and not what it only says to run, a run through a helper
                  function, a help text that names a tool and runs nothing, a reason, a layer, a domain, a suite, an
                  example block, an asset
  the same bytes  two runs give byte-identical JSON; the parts and the relations are sorted, and each list of findings
                  by its own key; a name the law gives two items is one finding, and a mention of it counts for both
  one part        `--part` shows a term and a tool, and refuses a name no part has
  a garden        in a garden it maps the garden's copy of the language — the files the release keeps, and the whole law
                  — and nothing of the garden's own

Every name is neutral (sam), and the garden is grown in a temporary directory.
"""
import contextlib, io, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmparse, dmpass, dmcatalog
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


TOOL = os.path.join(ROOT, "bin", "dmcatalog.py")
r1, r2 = run(sys.executable, TOOL, "--json", cwd=ROOT), run(sys.executable, TOOL, "--json", cwd=ROOT)
check("the catalogue is written as JSON (exit 0)", r1.returncode == 0 and r1.stdout.startswith("{"), r1.stderr[-600:])
check("two runs give byte-identical JSON", r1.stdout == r2.stdout and len(r1.stdout) > 10000, len(r1.stdout))
d = json.loads(r1.stdout) if r1.returncode == 0 else {"parts": {}, "relations": [], "unplaced": [], "findings": {}}
parts, rels = d["parts"], d["relations"]

# ---------------------------------------------------------------- every file, in its layer or named as in none
M = dmpass.Map.here(ROOT)
missing = [f for f in M.files if f not in parts]
check(f"every file the tree would commit is a part ({len(M.files)})", M.files and not missing, missing[:10])
wrong = [f for f in M.files if f in parts and parts[f]["contents"].get("layer") != M.layer_of(f)[0]]
check("...each in the layer the law's map places it in", not wrong, wrong[:10])
_by, _none = M.placed()
check("...and the files in no layer are named, and are the ones bin/dmpass.py names",
      sorted(d["unplaced"]) == sorted(_none) and all(parts[f]["contents"].get("layer") is None for f in d["unplaced"]),
      sorted(set(d["unplaced"]) ^ set(_none))[:10])
held = [f for f in M.files if f in parts and parts[f]["contents"].get("layer") is None and f not in d["unplaced"]]
check("...so every file is placed in a layer, or named as in none", not held, held[:10])

# ---------------------------------------------------------------- the law, whole
law = dmparse.loads(dmparse.split_front_matter(open(os.path.join(ROOT, "seed", "std-vocab.md"), encoding="utf-8").read())[0])
names = [t["term"] for t in law["terms"]] + [t["term"] for p in law["profiles"].values() for t in p.get("terms") or []]
absent = [n for n in names if "term:" + n not in parts]
check(f"every term of the law and of its profiles is a part ({len(names)})", names and not absent, absent)
extra = sorted(p[5:] for p in parts if p.startswith("term:") and p[5:] not in names)
check("...and no term is a part the law does not have", not extra, extra)
norules = [n for n in names if "term:" + n in parts and not parts["term:" + n]["checklists"]["rules"]]
check("...and each carries the rules bin/dmrules.py prints for it, a profile's terms included", not norules, norules)
items = (["registry:" + k for k, v in law.items() if isinstance(v, list) and k != "terms"]
         + ["section:" + k for k, v in law.items() if isinstance(v, dict) and k != "profiles"]
         + ["profile:" + p for p in law["profiles"]] + ["layer:" + r["layer"] for r in law["layers"]])
check(f"every registry, section, profile and layer of the law is a part ({len(items)})",
      all(i in parts for i in items), [i for i in items if i not in parts])
claimed = [p for p, v in parts.items() if v["kind"] in dmcatalog.LAW_KINDS and v["kind"] != "term" and p not in items]
check("...and no part claims an item the law does not have", not claimed, claimed)

# ---------------------------------------------------------------- every relation
dangling = [r for r in rels if r["from"] not in parts or r["to"] not in parts]
check(f"both ends of every relation are parts ({len(rels)} relations)", rels and not dangling, dangling[:5])
kinds = {r["rel"] for r in rels}
check("every relation is of a kind the tool names, and every kind is found", kinds == set(dmcatalog.RELATIONS),
      sorted(kinds ^ set(dmcatalog.RELATIONS)))


def has(rel, a, b):
    return any(r["rel"] == rel and r["from"] == a and r["to"] == b for r in rels)


check("an import is read: the gate imports the one loader", has("imports", "bin/dmcheck.py", "bin/dmparse.py"))
check("a module loaded by its path is an import: the view's model loads each adapter beside it",
      has("imports", "assets/view/lib/view_model.py", "assets/view/lib/sources/http.py")
      and has("imports", "assets/view/lib/view_model.py", "assets/view/lib/sources/prometheus.py"))
check("an import is looked for where the importer put sys.path: test/terminology.py imports site/terminology.py, "
      "not itself", has("imports", "test/terminology.py", "site/terminology.py"))
_hook = open(os.path.join(ROOT, "bin", "hooks", "pre-commit"), encoding="utf-8").read()
check("a hook runs what its lines run: the pre-commit hook runs the gate", has("runs", "bin/hooks/pre-commit", "bin/dmcheck.py"))
check("...and not what it only tells a person to run, nor what a comment names",
      "bin/install.py" in _hook and not has("runs", "bin/hooks/pre-commit", "bin/install.py"))
check("a run through a function of the suite's own is read: test/save.py runs bin/dmsave.py",
      has("runs", "test/save.py", "bin/dmsave.py"))
_rules = open(os.path.join(ROOT, "bin", "dmrules.py"), encoding="utf-8").read()
check("a help text that names a tool runs nothing: bin/dmrules.py names the gate and does not run it",
      "bin/dmcheck.py" in _rules and not has("runs", "bin/dmrules.py", "bin/dmcheck.py"))
_ci = re.findall(r"python3 (test/[a-z_]+\.py)", open(os.path.join(ROOT, ".github", "workflows", "ci.yml"), encoding="utf-8").read())
check("the release's workflow runs each suite it lists", _ci and all(has("runs", ".github/workflows/ci.yml", t) for t in _ci),
      [t for t in _ci if not has("runs", ".github/workflows/ci.yml", t)])
check("a reason explains the law item its path names", has("explains", "seed/RATIONALE.md", "term:capabilities"))
check("a layer holds its files, this tool among the gate's", has("holds", "layer:gate", "bin/dmcatalog.py"))
check("a term uses what its attributes take their values in: an aspect's rows, a registry",
      has("uses", "term:capabilities", "registry:aspects") and has("uses", "term:capabilities", "registry:knowledge_schemes"))
check("a suite covers the tool it runs, and this suite covers the catalogue",
      has("covers", "test/save.py", "bin/dmsave.py") and has("covers", "test/catalogue.py", "bin/dmcatalog.py"))
check("a document states the terms it writes as keys in an example: the forms show `owned_by`",
      has("states", "seed/FORMS.md", "term:owned_by") and "\nowned_by:" in open(os.path.join(ROOT, "seed", "FORMS.md"), encoding="utf-8").read())
check("a file mentions the law items it names whole in backticks or quotes: MODEL.md, the `manifest` and `consent`",
      has("mentions", "MODEL.md", "section:manifest") and has("mentions", "MODEL.md", "term:consent"))
check("a profile ships its asset", has("ships", "profile:view", "assets/view/bin/dmview.py"))

# ---------------------------------------------------------------- sorted, so a diff between two maps is the change
check("the parts are sorted, and the relations", list(parts) == sorted(parts)
      and rels == sorted(rels, key=lambda r: (r["rel"], r["from"], r["to"], r.get("via", ""))))
F = d["findings"]
ORDER = {"unreferenced": lambda x: x["part"], "untested_tools": lambda x: x["part"],
         "one_domain_many_names": lambda x: (-x["similarity"], x["domain"], x["names"]),
         "odd_siblings": lambda x: (x["group"], x["part"]), "own_bean_walks": lambda x: (-x["walks"], x["part"]),
         "one_name_many_items": lambda x: x["name"]}
check("the findings are the six the tool names", set(F) == set(ORDER), sorted(F))
check("...and each list is sorted by its own key", not [k for k, key in ORDER.items() if F.get(k) != sorted(F.get(k, []), key=key)],
      [k for k, key in ORDER.items() if F.get(k) != sorted(F.get(k, []), key=key)])
check("...and a tool a suite runs is not found untested: the catalogue is not",
      "bin/dmcatalog.py" not in [x["part"] for x in F.get("untested_tools", [])])
_twice = sorted(n for n in set(names) & {k for k, v in law.items() if isinstance(v, list)})
check("...and a name the law gives a term and a registry is found as one, and a mention of it counts for both",
      all(any(x["name"] == n and x["parts"] == ["registry:" + n, "term:" + n] for x in F.get("one_name_many_items", []))
          for n in _twice)
      and all(p not in [x["part"] for x in F.get("unreferenced", [])] for n in _twice for p in ("registry:" + n, "term:" + n)),
      _twice)

# ---------------------------------------------------------------- what a person reads
cat = dmcatalog.Catalogue()
for _args, _want in ((["--part", "capabilities"], ("term:capabilities — term", "permission: aspect:permission",
                                                     "rules (bin/dmrules.py)", "explained by")),
                     (["--part", "dmsave"], ("bin/dmsave.py — tool, in the gate layer", "run by", "suite checks that name it"))):
    _out = io.StringIO()
    with contextlib.redirect_stdout(_out):
        for _pid in dmcatalog.find(cat, _args[1]):
            dmcatalog.show_part(cat, _pid)
    check(f"`--part {_args[1]}` shows the part, its relations both ways, and what it is held to",
          all(w in _out.getvalue() for w in _want), _out.getvalue()[:400])
r = run(sys.executable, TOOL, "--part", "no-such-part", cwd=ROOT)
check("...and a name no part has is refused, saying what a name can be", r.returncode == 1 and "no part is named" in r.stderr,
      r.stdout[-200:] + r.stderr[-300:])
_out = io.StringIO()
with contextlib.redirect_stdout(_out):
    dmcatalog.report(cat)
check("the report groups the files under their layers, then the law's items, then the findings",
      "\ngate — " in _out.getvalue() and "\nthe law's items" in _out.getvalue() and "\nfindings — " in _out.getvalue())

# ---------------------------------------------------------------- in a garden: its copy of the language
T = tempfile.mkdtemp(prefix="dmcat-")
G = os.path.join(T, "g")
r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "sam", cwd=T)
check("a garden germinates, and receives the catalogue", r.returncode == 0 and os.path.isfile(os.path.join(G, "bin", "dmcatalog.py")),
      r.stdout[-300:] + r.stderr[-300:])
r = run(sys.executable, os.path.join(G, "bin", "dmcatalog.py"), "--json", cwd=G)
gd = json.loads(r.stdout) if r.returncode == 0 else {"catalogue": {}, "parts": {}}
gp = gd["parts"]
gm = dmpass.Map.here(G)
kept = [f for f in gm.files if gm.keeper_of(f) == "release"]
check("in a garden it maps the garden's copy of the language: every file the release keeps",
      gd["catalogue"].get("of") == "garden" and kept and all(f in gp for f in kept), [f for f in kept if f not in gp][:5])
own = [f for f in gp if gp[f]["kind"] not in dmcatalog.LAW_KINDS and f not in kept]
check("...and nothing of the garden's own: no bean, no journal, no manifest",
      not own and os.path.isfile(os.path.join(G, "beans", "sam.md")), own[:5])
check("...and the whole law", all("term:" + n in gp for n in names), [n for n in names if "term:" + n not in gp][:5])
_gm = dmparse.loads(dmparse.split_front_matter(open(os.path.join(G, "GARDEN.md"), encoding="utf-8").read())[0]) or {}
check("...and the release it names is the one the garden adopted, as its GARDEN.md says and the gate prints, never "
      "what the garden's own history describes", _gm.get("daftar_release")
      and gd["catalogue"].get("release") == str(_gm["daftar_release"]), (gd["catalogue"].get("release"), _gm.get("daftar_release")))
r = run(sys.executable, os.path.join(G, "bin", "dmrules.py"), cwd=G)
check("...and bin/dmrules.py names the same release", r.stdout.startswith("daftar %s rules" % _gm.get("daftar_release")),
      r.stdout[:160])
shutil.rmtree(T, ignore_errors=True)

print("\ncatalogue: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
