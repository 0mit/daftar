#!/usr/bin/env python3
"""One sense per name (24.0, `senses`): the gate's ply over the terms in force in a garden.

Grows a garden and gives it a term of its own. A name the term uses in a domain the law does not give it, or spells
as a term it does not take, is refused as a second sense; a row of VOCAB.md's `senses` judging it lets it stand; a
row there that judges nothing is refused as stale; and the law's own rows, some for profiles this garden does not
extend, are never stale here; and a name the law judged, given another domain by the garden's term, is refused
unless VOCAB.md judges that use too. The law's rows over every profile are judged by test/assets.py.
"""
import os, re, sys, subprocess, tempfile, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=cwd)


T = tempfile.mkdtemp(prefix="dmsenses-")
G = os.path.join(T, "g")
r = run(sys.executable, os.path.join(ROOT, "seed", "germinate.py"), G, "--gardener", "keeper", cwd=T)
check("a garden germinates, the law's rows of `senses` judging what it holds", r.returncode == 0, r.stdout + r.stderr)
VOC = os.path.join(G, "VOCAB.md")
ORIG = open(VOC, encoding="utf-8").read()


def gate():
    r = run(sys.executable, os.path.join(G, "bin", "dmcheck.py"), "--all", cwd=G)
    return re.sub(r"\s*\n\s+— ", " — ", r.stdout + r.stderr)


def vocab(terms, senses=None):
    new = ORIG.replace("local_terms: []\n", "local_terms:\n" + terms + (f"senses:\n{senses}" if senses else ""), 1)
    open(VOC, "w", encoding="utf-8").write(new)


out = gate()
check("the law's rows for profiles this garden does not extend are not stale here", "is judged, and no longer" not in out,
      out[-900:])

TERM = ('  - term: tally\n    meaning: "a count the keeper makes"\n    schema:\n      attrs:\n'
        '        genos: { in: prose, meaning: "what kind of thing is counted" }\n'
        '        count: { in: { type: count }, meaning: "how many" }\n')
vocab(TERM)
out = gate()
check("a garden's term spelling `genos`, a term, as prose is refused as a second sense",
      "`genos` has a second sense" in out, out[-900:])

vocab(TERM, '  - { name: genos, sense: "the kind of a thing, in words or as a row of `gene`" }\n')
out = gate()
check("...and a row of VOCAB.md's `senses` judging it lets it stand", "`genos` has a second sense" not in out
      and "senses" not in out.split("error(s)")[0].split("\n")[-1], out[-900:])

vocab(TERM, '  - { name: genos, sense: "the kind of a thing" }\n  - { name: tallies, sense: "nothing uses it" }\n')
out = gate()
check("a row of VOCAB.md's `senses` no finding calls for is refused as stale",
      "`tallies` is judged, and no longer a finding" in out, out[-900:])

vocab(TERM.replace('genos: { in: prose', 'at: { in: prose'))
out = gate()
check("a name the law judged, given by a garden's term a domain the law's row did not judge, is a second sense",
      "`at` has a second sense — prose (tally)" in out, out[-900:])

vocab(TERM.replace('genos: { in: prose', 'at: { in: prose'), '  - { name: at, sense: "where it was counted, in words" }\n')
out = gate()
check("...and a row of VOCAB.md's judging that use in the law's sense lets it stand", "`at` has a second sense" not in out
      and "`at` is judged" not in out, out[-900:])

vocab(TERM.replace('genos: { in: prose', 'at: { in: { type: date }'), '  - { name: at, sense: "the day it was counted" }\n')
out = gate()
check("...given a domain the law's row judged, it stands with no row of its own, and a row of its own is stale",
      "`at` has a second sense" not in out and "`at` is judged, and no longer a finding" in out, out[-900:])

shutil.rmtree(T, ignore_errors=True)
print(f"\nsenses: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
