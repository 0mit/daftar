#!/usr/bin/env python3
"""The root (std-vocab 31.0): the dot and its divisions, the frame of place and time, the order of bodies, life, and the
crown as the life chain.

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
check("the gardener is a body held by no bean — `nature: soma`, `crown: agape` — and the garden says where it reckons its "
      "days", "nature: soma" in SAM and "crown: agape" in SAM and "zone: Europe/Istanbul" in GARDEN, (SAM[:600], GARDEN[:400]))
check("...and it passes the gate", ok(gate()), gate()[-600:])

# --- natures and the crown
put("beans/sam.md", SAM.replace("nature: soma", "nature: empsychon"))
out = gate()
check("a bean still `empsychon` is refused, naming what took its place", "empsychon" in out and "retired: `soma` for a person" in out,
      out[-700:])
put("beans/sam.md", SAM.replace("crown: agape", "crown: logos"))
out = gate()
check("a crown chosen by nature is refused: the crown is the life chain, one branch", "logos" in out and not ok(out)
      and "retired: `agape`" in out, out[-700:])
put("beans/sam.md", SAM.replace("crown: agape", "crown: theos"))
out = gate()
check("...and its root, THE ONE, is named by no bean", "theos" in out and not ok(out), out[-700:])
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
owned_by: {{ legal: {{ owner: {{ bean: sam }} }} }}
responsibility: {{ legal: {{ holder: {{ bean: sam }} }} }}
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
        ("{ genos: gizmo, of_nature: soma, level: galaxy, meaning: \"invented\" }", "a body names the level it stands at",
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

check("NOTHING above ended in a traceback", True)
shutil.rmtree(T, ignore_errors=True)
print("\nroot: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
