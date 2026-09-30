#!/usr/bin/env python3
"""The root (std-vocab 31.0, and the base, 32.0): the dot and its divisions, the frame of place and time, the ladder from
the frame to the crown, life, the life chain as vias ending at the Creator, and ownership without facets.

Grows a garden, then: the gardener is a body (soma) held by the crown, agape; a nature the law retired and a crown chosen
by nature are refused naming what took their place; a body's genos names its level, a sayable one names none, and a
part never stands above its whole; a genos's life is said in one of four ways; every place or time system says how its
positions find their other half, and a garden says where it reckons its days; a division is in its form, names the rule
that judges it, and a garden's own is judged by the gate, exactly.
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


T = tempfile.mkdtemp(prefix="dmroot-")
G = os.path.join(T, "g")
r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "sam", "--zone", "Europe/Istanbul", cwd=ROOT)
check("a garden germinates with its zone, and the root passes its own checks", r.returncode == 0, r.stdout + r.stderr)


def gate():
    x = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return (x.stdout + x.stderr).replace("\n      — ", " — ")


def put(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(text)


def get(rel):
    return open(os.path.join(G, rel), encoding="utf-8").read()


def ok(out):
    return " 0 error(s)" in out and "Traceback" not in out


SAM, VOCAB, GARDEN = get("beans/sam.md"), get("VOCAB.md"), get("GARDEN.md")
check("the gardener is a body held by no bean — `nature: soma`, `crown: true` — and the garden says where it reckons its "
      "days", "nature: soma" in SAM and "crown: true" in SAM and "zone: Europe/Istanbul" in GARDEN, (SAM[:600], GARDEN[:400]))
check("...and it passes the gate", ok(gate()), gate()[-600:])

# --- natures and the crown
put("beans/sam.md", SAM.replace("nature: soma", "nature: empsychon"))
out = gate()
check("a bean still `empsychon` is refused, naming what took its place", "empsychon" in out and "retired: `soma` for a person" in out,
      out[-700:])
put("beans/sam.md", SAM.replace("crown: true", "crown: agape"))
out = gate()
check("a crown named as a value is refused: the crown is one, `theone`, and a being it holds says only `crown: true`",
      "agape" in out and not ok(out), out[-700:])
put("beans/sam.md", SAM.replace("crown: true", "crown: theone"))
out = gate()
check("...and THE ONE is named by no bean", "theone" in out and not ok(out), out[-700:])
put("beans/sam.md", SAM)


def bean(bid, genos, nature, extra="", anchor=None):
    a = anchor or f"{genos}:{bid}"
    return f"""---
bean: {bid}
genos: {genos}
title: "{bid}"
status: active
summary: "{bid}, invented"
nature: {nature}
identity:
  status: provisional
  anchors:
    - {{ key: identifier, value: "{a}", class: logical, establishing: false }}
provenance: {{ src: asserted-by-human, by: "sam", as_of: 2026-09-30 }}
owned_by: {{ owner: {{ bean: sam }} }}
{extra}---
{bid}, invented.
"""


# --- the order of bodies
put("VOCAB.md", VOCAB.replace("local_gene: []", "local_gene:\n  - { genos: rack, of_nature: soma, level: installation, "
                              "alive_while: { known: always, by: \"while it stands\" }, meaning: \"a frame devices are "
                              "mounted in, invented\" }"))
put("beans/rack-1.md", bean("rack-1", "rack", "soma"))
put("beans/host-1.md", bean("host-1", "host", "soma", "part_of: { bean: rack-1 }\n"))
out = gate()
check("a device is part of an installation: a part stands on what its whole stands on", ok(out), out[-700:])
put("beans/host-1.md", bean("host-1", "host", "soma", "part_of: { bean: sam }\n"))
out = gate()
check("...and a device is never part of an organism: a part never stands above its whole",
      "a part never stands above its whole" in out, out[-700:])
put("beans/host-1.md", bean("host-1", "host", "soma", "part_of: { bean: rack-1 }\n"))
for text, want, name in (
        ("{ genos: gizmo, of_nature: soma, meaning: \"invented\" }", "a body names the level it stands at",
         "a body's genos with no level is refused"),
        ("{ genos: gizmo, of_nature: soma, level: universe-entire, meaning: \"invented\" }", "a body names the level it stands at",
         "...and one at a level the law does not have"),
        ("{ genos: notion, of_nature: lekton, level: cell, meaning: \"invented\" }", "only a body stands among bodies",
         "a sayable genos with a level is refused"),
        ("{ genos: gizmo, of_nature: soma, level: device, alive_while: { known: guessed }, meaning: \"invented\" }",
         "alive_while", "a life said in no way the law has is refused")):
    put("VOCAB.md", VOCAB.replace("local_gene: []", "local_gene:\n  - " + text))
    out = gate()
    check(name, want in out and not ok(out), out[-700:])
put("VOCAB.md", VOCAB.replace("local_gene: []", "local_gene:\n  - { genos: rack, of_nature: soma, level: installation, "
                              "meaning: \"a frame devices are mounted in, invented\" }"))

# --- the frame
put("GARDEN.md", re.sub(r"(?m)^zone:.*\n", "", GARDEN))
out = gate()
check("a garden that does not say where it reckons its days is refused", "zone" in out and not ok(out), out[-700:])
put("GARDEN.md", GARDEN)
_sys = """registry_additions:
  anchor_systems:
    - system: harvest-count
      dimension: time
      %s
      neighbours: counted
      meaning: "harvests counted from the first, invented"
      pattern: '^harvest:[0-9]+$'
      example: "harvest:3"
      establishes: false
      why: "a harvest says when, roughly"
"""
put("VOCAB.md", get("VOCAB.md").replace("local_gene:", _sys % "" + "local_gene:"))
out = gate()
check("a time system that does not say how its positions find their place is refused", "harvest-count" in out
      and "complement" in out and not ok(out), out[-700:])
put("VOCAB.md", get("VOCAB.md").replace("      dimension: time\n      \n", "      dimension: time\n      complement: [bearer]\n")
    .replace("local_gene:", "vacancies:\n  - { at: \"registry:anchor_systems\", position: harvest-count, reason: prediction, why: \"the first harvest is next year\" }\nlocal_gene:", 1))
out = gate()
check("...and one that does passes", ok(out), out[-700:])

# --- divisions
_div = """  divisions:
    - { division: shelf-load, whole: { term: load, attr: mass }, parts: { via: part_of, term: load, attr: mass }, covers: false, disjoint: true, wholeness: { aggregate: sum, is: at_most }, checked_by: division }
"""
_load = """local_terms:
  - term: load
    meaning: "the mass a being bears, invented"
    context_keys: [load]
    schema:
      shape: mapping
      attrs:
        mass: { required: true, in: { quantity: mass }, meaning: "how much" }
"""
_v = get("VOCAB.md").replace("registry_additions:\n", "registry_additions:\n" + _div).replace("local_terms: []\n", _load)
put("VOCAB.md", _v)
put("beans/rack-1.md", bean("rack-1", "rack", "soma", "load: { mass: { count: 10, unit: kilogram } }\n"))
put("beans/host-1.md", bean("host-1", "host", "soma", "part_of: { bean: rack-1 }\nload: { mass: { count: 6, unit: kilogram } }\n"))
put("beans/host-2.md", bean("host-2", "host", "soma", "part_of: { bean: rack-1 }\nload: { mass: { count: 5000, unit: gram } }\n"))
out = gate()
check("a garden's own division is judged exactly, in the whole's unit: 6 kg and 5000 g are more than the rack's 10 kg",
      "shelf-load" in out and "11" in out and not ok(out), out[-900:])
put("beans/host-2.md", bean("host-2", "host", "soma", "part_of: { bean: rack-1 }\nload: { mass: { count: 4000, unit: gram } }\n"))
out = gate()
check("...and 6 kg and 4000 g are within it", ok(out), out[-900:])
put("VOCAB.md", _v.replace("checked_by: division", "checked_by: \"terms[nothing-of-the-kind]\""))
out = gate()
check("a division naming no rule of the law is refused", "names no rule of the law" in out, out[-700:])
put("VOCAB.md", _v.replace("aggregate: sum", "aggregate: guess"))
out = gate()
check("...and one whose wholeness is no aggregate", "no row of `aggregates`" in out, out[-700:])

# --- 32.0: the ladder, its rules, the life chain, and ownership without facets
put("VOCAB.md", VOCAB)
for b in ("rack-1", "host-1", "host-2"):
    if os.path.exists(os.path.join(G, "beans", b + ".md")):
        os.remove(os.path.join(G, "beans", b + ".md"))
LOCAL = """local_gene:
  - { genos: tree, of_nature: soma, level: organism, alive_while: { known: said, by: "while it grows" }, meaning: "a tree, invented" }
  - { genos: herd, of_nature: soma, level: population, alive_while: { known: said, by: "while it keeps together" }, meaning: "a herd, invented" }
  - { genos: machine, of_nature: soma, level: device, alive_while: { known: said, by: "while it runs" }, meaning: "a machine, invented" }
"""
V32 = VOCAB.replace("local_gene: []\n", LOCAL)
put("VOCAB.md", V32)
out = gate()
check("32.0: a garden's own bodies at the ladder's levels pass", ok(out), out[-700:])
put("VOCAB.md", V32.replace("level: device, alive_while", "level: logos, alive_while"))
out = gate()
check("a body at `logos` is refused: no body stands there, a person's body is an organism",
      "a body names the level it stands at among bodies" in out and not ok(out), out[-700:])
put("VOCAB.md", V32.replace("level: device, alive_while", "level: device, rung: organism, alive_while"))
out = gate()
check("...and a `rung` names only a step that holds no body", "names a step that holds no body" in out, out[-700:])
put("VOCAB.md", V32)
put("beans/herd-1.md", bean("herd-1", "herd", "soma"))
put("beans/tree-1.md", bean("tree-1", "tree", "soma", "part_of: { bean: herd-1 }\n"))
out = gate()
check("a living part of a population passes: the part is what its whole is made of", ok(out), out[-700:])
os.remove(os.path.join(G, "beans", "herd-1.md"))
put("beans/tree-1.md", bean("tree-1", "tree", "soma"))

# weight: every body has it, a sayable being none of its own
LOAD = """local_terms:
  - term: load
    meaning: "the mass a being bears, invented"
    context_keys: [load]
    schema:
      shape: mapping
      attrs:
        mass: { required: true, in: { quantity: mass }, meaning: "how much" }
"""
V32L = V32.replace("local_terms: []\n", LOAD)
put("VOCAB.md", V32L)
put("beans/doc-1.md", bean("doc-1", "design", "lekton", "load: { mass: { count: 2, unit: kilogram } }\n"))
out = gate()
check("weight: a sayable being's own mass is refused — the rule holds for bodies, from space∞time",
      "has no mass of its own" in out and "weight" in out, out[-700:])
put("VOCAB.md", V32L.replace('in: { quantity: mass }, meaning: "how much"', 'in: { quantity: mass }, of_bodies: true, meaning: "how much each of its units weighs"'))
out = gate()
check("...and allowed where the attribute says it measures the bodies the being stands for (`of_bodies`)", ok(out), out[-700:])
os.remove(os.path.join(G, "beans", "doc-1.md"))
put("VOCAB.md", V32)

# the life chain: vias, ending at the Creator
put("beans/m-1.md", bean("m-1", "machine", "soma"))
put("beans/doc-2.md", bean("doc-2", "design", "lekton", "via: [{ bean: sam }]\n"))
out = gate()
check("a said thing that came through a person passes", ok(out), out[-700:])
put("beans/doc-2.md", bean("doc-2", "design", "lekton", "via: [{ bean: m-1 }]\n"))
out = gate()
check("...one through a machine whose own chain stops there is refused: a said thing comes through hands",
      "stops at m-1" in out and "hands" in out, out[-700:])
put("beans/m-1.md", bean("m-1", "machine", "soma", "via: [{ bean: sam }]\n"))
out = gate()
check("...and passes once the machine's own via goes on to the person it acted for", ok(out), out[-700:])
put("beans/m-1.md", bean("m-1", "machine", "soma", 'via: [{ someone: person, outside: "HPE" }]\n'))
out = gate()
check("an unknown maker is someone, reached through what is known: a person at HPE", ok(out), out[-700:])
put("beans/m-1.md", bean("m-1", "machine", "soma", "via: [{ someone: person }]\n"))
out = gate()
check("...and someone reached through nothing is refused, as no fact at all", "reached through nothing" in out, out[-700:])
put("beans/m-1.md", bean("m-1", "machine", "soma"))
put("beans/doc-2.md", bean("doc-2", "design", "lekton", "via: [{ bean: sam }]\n"))
put("beans/tree-1.md", bean("tree-1", "tree", "soma", "via: [{ bean: m-1 }]\n"))
out = gate()
check("a living being through a machine is refused: life comes through the living", "a living being" in out
      and "tree-1" in out, out[-700:])
put("beans/tree-1.md", bean("tree-1", "tree", "soma", "via: [{ bean: sam }]\n"))
out = gate()
check("...and one planted by a person passes", ok(out), out[-700:])
put("beans/doc-2.md", bean("doc-2", "design", "lekton", "via: [{ bean: nobody-here }]\n"))
out = gate()
check("a via naming no bean of the garden is refused, naming the form for someone not held here",
      "nobody-here" in out and "someone" in out, out[-700:])
put("beans/doc-2.md", bean("doc-2", "design", "lekton", "creator: { bean: sam }\n"))
out = gate()
check("the retired `creator` is refused, naming `via`", "creator" in out and "via" in out and not ok(out), out[-700:])
os.remove(os.path.join(G, "beans", "doc-2.md"))

# ownership has no facets; answering is care
D = bean("doc-3", "design", "lekton")
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }", "owned_by: { legal: { owner: { bean: sam } } }"))
out = gate()
check("ownership in a facet is refused, naming the one-owner form", "legal" in out and "`owner`" in out and not ok(out), out[-700:])
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }", "owned_by: { owner: { bean: sam }, crown: true }"))
out = gate()
check("...and two owners at once", not ok(out), out[-700:])
put("beans/doc-3.md", D + "")
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }\n",
                                "owned_by: { owner: { bean: sam } }\nresponsibility: { legal: { holder: { bean: sam } } }\n"))
out = gate()
check("a legal answerer who is the owner is a placeholder, and refused", "is a placeholder" in out, out[-700:])
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }\n", 'owned_by: { external: "a publisher" }\n'))
out = gate()
check("a being owned outside this ledger with nobody here answering is refused", "nobody here answers" in out, out[-700:])
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }\n",
                                'owned_by: { external: "a publisher" }\nresponsibility: { legal: { holder: { bean: sam } } }\n'))
out = gate()
check("...and passes once someone here answers for it", ok(out), out[-700:])
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }\n",
                                "owned_by: { owner: { bean: sam } }\nresponsibility: { technical: { holder: { bean: sam } } }\n"))
out = gate()
check("a technical answerer on a record nobody runs is refused: the facet applies only where something runs or is kept",
      "applies only to" in out, out[-700:])
put("beans/doc-3.md", D)
put("beans/m-1.md", bean("m-1", "machine", "soma", "responsibility: { technical: { holder: { bean: sam } } }\n"))
out = gate()
check("...and on a machine it passes", ok(out), out[-700:])
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }\n",
                                "owned_by: { owner: { bean: sam } }\nacquired: { from: { bean: sam }, as: given }\n"))
out = gate()
check("the acquisition says from whom a being came to us", ok(out), out[-700:])
put("beans/doc-3.md", D.replace("owned_by: { owner: { bean: sam } }\n",
                                "owned_by: { owner: { bean: sam } }\nacquired: { as: given }\n"))
out = gate()
check("...and one from no one is refused", "acquired" in out and not ok(out), out[-700:])
for b in ("doc-3", "m-1", "tree-1"):
    os.remove(os.path.join(G, "beans", b + ".md"))
put("VOCAB.md", VOCAB)

# --- the names layer: each language a sibling, every row an item of the law
put("VOCAB.md", _v)
EN, FA = get("seed/names/en.tsv"), get("seed/names/fa.tsv")
check("the names layer: nine languages, the same items in each, all of the law — and a garden grown with it passes",
      len(os.listdir(os.path.join(G, "seed", "names"))) == 9 and EN.count("\n") == FA.count("\n") > 60 and ok(gate()), gate()[-600:])
put("seed/names/en.tsv", EN + "term:nothing-of-the-kind\tnothing\t\tproposed\tsam\n")
out = gate()
check("a name for no item of the law is refused", "`term:nothing-of-the-kind` is no item of the law" in out, out[-600:])
put("seed/names/en.tsv", EN.replace("\tproposed\t", "\tapproved\t", 1))
out = gate()
check("...a status neither proposed nor confirmed", "is `proposed` or `confirmed`" in out, out[-600:])
put("seed/names/en.tsv", EN)
put("seed/names/fa.tsv", "\n".join(l for l in FA.split("\n") if not l.startswith("natures:lekton\t")))
out = gate()
check("...a language that names fewer items than its siblings, naming what it lacks",
      "seed/names/fa.tsv names" in out and "natures:lekton" in out, out[-600:])
put("seed/names/fa.tsv", FA)
put("seed/names/xx.tsv", "item\tname\troots\tstatus\tby\n")
out = gate()
check("...and a file in no language of the form", "seed/names/xx.tsv" in out and "one of the form's languages" in out, out[-600:])
os.remove(os.path.join(G, "seed", "names", "xx.tsv"))

check("NOTHING above ended in a traceback", True)
shutil.rmtree(T, ignore_errors=True)
print("\nroot: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
