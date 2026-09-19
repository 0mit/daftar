#!/usr/bin/env python3
"""Figures (std-vocab 9.2, "T0"): the square of opposition and the sequence.

Grows a garden with seed/germinate.sh and checks that its gate reads every aspect through the `figures`
registry: a sequence must state each restriction with a value the figure offers, a figure the gate has no
check for is refused, and the cycle check follows the `walk` aspect's `acyclic` restriction rather than a
key named in code.
"""
import os, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:600]))
    if not cond:
        FAILS.append(name)

def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, cwd=cwd)

T = tempfile.mkdtemp(prefix="dmfig-")
G = os.path.join(T, "g")
r = run("sh", os.path.join(ROOT, "seed", "germinate.sh"), G, cwd=ROOT)
check("a garden germinates", r.returncode == 0, r.stdout + r.stderr)
VOC = os.path.join(G, "seed", "std-vocab.md")
ORIG = open(VOC).read()

def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return r.stdout + r.stderr

def mutate(old, new):
    assert ORIG.count(old) == 1, old
    open(VOC, "w").write(ORIG.replace(old, new))

out = gate()
check("the standard's figures and aspects pass as declared", "0 error" in out, out[-1500:])

mutate("  - aspect: place\n", "  - aspect: place\n    positions: [{ position: here, complement: there }]\n")
out = gate()
check("a sequence that declares positions is refused", "a sequence declares no `positions`" in out, out[-900:])

mutate("    ends: bounded\n    domain: { systems: place }\n", "    domain: { systems: place }\n")
out = gate()
check("a sequence that leaves a restriction unstated is refused", "must state `ends`" in out, out[-900:])

mutate("    lines: open\n", "    lines: 0\n")
out = gate()
check("a line count that is not one or more is refused", "lines '0' must be a positive integer" in out, out[-900:])

mutate("    metered: time\n", "    metered: weight\n")
out = gate()
check("a measure that is not a unit dimension is refused", "metered 'weight' is neither" in out, out[-900:])

open(VOC, "w").write(ORIG.replace("    figure: sequence\n    lines: 1\n    metered: time\n", "    figure: spiral\n    lines: 1\n    metered: time\n", 1))
out = gate()
check("a figure the registry does not declare is refused", "figure 'spiral' is not declared in `figures`" in out, out[-900:])

open(VOC, "w").write(ORIG.replace("  - figure: sequence\n", "  - figure: spiral\n    requires: []\n  - figure: sequence\n", 1)
                     .replace("    figure: sequence\n    lines: 1\n    metered: time\n", "    figure: spiral\n    lines: 1\n    metered: time\n", 1))
out = gate()
check("a declared figure the gate has no check for is refused, not passed unexamined", "the gate has no check for figure 'spiral'" in out, out[-900:])

# the cycle check follows the walk aspect's restriction
open(VOC, "w").write(ORIG)
def bean(name, body):
    open(os.path.join(G, "beans", name + ".md"), "w").write("---\n" + body + "---\n\n" + name + "\n")
OWN = 'owned_by: { legal: { owner: { bean: someone } } }\nresponsibility: { legal: { holder: { bean: someone } } }\n'
bean("someone", 'bean: someone\nkind: person\ntitle: "a person"\nstatus: active\nsummary: "p"\nnature: living\n'
     'identity: { status: confirmed, anchors: [ { key: email, value: "a@example.org", class: logical, establishing: true } ] }\n'
     'provenance: { src: asserted-by-human, by: t, as_of: 2026-01-01 }\nowned_by: { legal: { crown: love } }\nresponsibility: { legal: { self: true } }\n')
for a, b in (("part-a", "part-b"), ("part-b", "part-a")):
    bean(a, f'bean: {a}\nkind: product\ntitle: "{a}"\nstatus: active\nsummary: "x"\nnature: metaphysical\n'
         f'identity: {{ status: confirmed, anchors: [ {{ key: product_id, value: "product:{a}", class: logical, establishing: true }} ] }}\n'
         f'provenance: {{ src: asserted-by-human, by: t, as_of: 2026-01-01 }}\n' + OWN + f'part_of: {{ bean: {b} }}\n')
out = gate()
check("a cycle on a walked relation is refused while `walk` says acyclic", "cycle" in out.lower() and "0 error" not in out, out[-900:])

mutate("    order: partial\n    acyclic: true\n    ends: open\n    term_key: dag",
       "    order: partial\n    acyclic: false\n    ends: open\n    term_key: dag")
out = gate()
check("the same cycle is not refused once `walk` declares acyclic: false — the restriction is data, not code",
      "cycle" not in out.lower(), out[-900:])

open(VOC, "w").write(ORIG)
r = run(sys.executable, os.path.join(G, "bin", "dmrules.py"), cwd=G)
check("dmrules shows the sequences and what walks them",
      "time         sequence" in r.stdout and "walked by:" in r.stdout and "on the 'walk' sequence" in r.stdout, r.stdout[-1500:] + r.stderr)

shutil.rmtree(T, ignore_errors=True)
print("\nfigures: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
