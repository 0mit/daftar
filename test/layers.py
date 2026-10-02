#!/usr/bin/env python3
"""The layer map in a garden of the core (v1 part 12: today's suite, ported): every file sits where the law says, or
where its garden says, and nowhere a tool must guess.

The core's map is core/law/layers.yaml's `standing` rows; a garden places the rest with rows of its own (VOCAB.md
`standing`); bin/pass.py is the one reader of both. It holds:

  the map    over what a release of this tree ships and what a new garden of the core holds, no file is held by two
             rows; no pattern reaches into a hidden directory; and every pattern names a file the release or a new
             garden has, but for the paths a garden grows (its captures, its names), said below with why
  a garden   `pass --layers` places the manifest and the garden's rows in law, the queue in queue, the journal in journal
             and a bean in estate; a garden's own row places a file the law does not (`notes/*`, in work); one that
             places a file the law places (GARDEN.md) is refused by the core's rule `layers`; a path given from a
             subdirectory is read from the garden's top

Today's checks of the law's own map — its `beneath` chain, the changelog's form — were of today's law text, which the
release keeps until part 13 moves its law into core/law/ (test/ported.yaml).

Run: python3 test/layers.py   (0 = green)
"""
import json
import os
import shutil
import sys
import tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "test"))
import grow  # noqa: E402
import dmpass  # noqa: E402 — test/grow.py put bin/ on the path

FAILS = []
# A GARDEN GROWS THESE: no release ships a file under them, and a new garden holds none until it writes one.
GROWN = {"captures/*": "what a garden captures from the world",
         "seed/names/*.tsv": "the names a garden gives, written as it gives them",
         "RATIONALE.md": "a garden's own reasons, beside its VOCAB.md, once it writes one",
         "README.md": "a garden's own page about itself, once it writes one",
         "series/*": "a series' parts, once a garden records one (core/law/lines.yaml)",
         "extracts/*": "the extract of a scheme a garden holds as its own (VOCAB.md `schemes`)",
         "mappings/*": "a garden's mappings in today's words, which a garden of the core writes as beans"}


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:900]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix="core-layers-")
try:
    REL = grow.release(os.path.join(T, "release"))
    G = os.path.join(T, "g")
    r = grow.garden(REL, G, "sam")
    check(f"a garden of the core grows (core@{grow.VERSION}), kept by sam", r.returncode == 0, r.out[-400:])

    # ---- the map
    ROWS = yaml.safe_load(open(os.path.join(ROOT, "core", "law", "layers.yaml"), encoding="utf-8"))["standing"]
    files = sorted(set(grow.files()) | set(dmpass.tracked(G)))
    twice = [(f, [r["layer"] for r in ROWS if any(dmpass.matches(p, f) for p in r["holds"])]) for f in files]
    twice = [(f, ls) for f, ls in twice if len(ls) > 1]
    check(f"no file a release ships or a new garden holds is held by two rows of the core's map ({len(files)} files)",
          files and not twice, twice[:5])
    hidden = [p for r in ROWS for p in r["holds"] if any(s.startswith(".") for s in p.split("/")[:-1])]
    check("...no pattern reaches into a hidden directory", not hidden, hidden)
    empty = [p for r in ROWS for p in r["holds"] if p not in GROWN and not any(dmpass.matches(p, f) for f in files)]
    check("...and every pattern names a file the release or a new garden has, but for the paths a garden grows",
          not empty, empty)

    # ---- a garden
    def pass_cli(*a, cwd=None):
        return grow.run(sys.executable, os.path.join(G, "bin", "pass.py"), *a, cwd=cwd or G)
    r = pass_cli("--layers", "--json")
    try:
        at = {e["path"]: layer for layer, es in json.loads(r.stdout)["layers"].items() for e in es}
    except (ValueError, KeyError, TypeError):
        at = {"error": r.out[-400:]}
    want = {"GARDEN.md": "law", "VOCAB.md": "law", "log/pending.md": "queue", "log/journal.md": "journal",
            "beans/sam.md": "estate"}
    check("`pass --layers` places the manifest and the garden's rows in law, the queue in queue, the journal in journal, "
          "and a bean in estate", {p: at.get(p) for p in want} == want, {p: at.get(p) for p in want})
    V = os.path.join(G, "VOCAB.md")
    v0 = open(V, encoding="utf-8").read()
    with open(V, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(v0.replace("\n---\n", '\nstanding:\n  - { layer: work, holds: ["notes/*"] }\n---\n', 1))
    os.makedirs(os.path.join(G, "notes"))
    with open(os.path.join(G, "notes", "a.md"), "w", encoding="utf-8") as fh:
        fh.write("a note\n")
    r = pass_cli("notes/a.md")
    check("a garden's own row places a file the law does not: notes/a.md stands in work", "work" in r.out and r.returncode == 0,
          r.out[-400:])
    sub = pass_cli("a.md", cwd=os.path.join(G, "notes"))
    check("...and a path given from a subdirectory is read from the garden's top: a.md, given in notes/, is notes/a.md",
          sub.out == r.out, (sub.out, r.out))
    with open(V, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(v0.replace("\n---\n", '\nstanding:\n  - { layer: work, holds: ["GARDEN.md"] }\n---\n', 1))
    r = grow.run(sys.executable, os.path.join(G, "core", "check.py"), ".", cwd=G)
    check("a garden's row that places a file the law places is refused by the core's rule `layers`, naming both layers",
          r.returncode == 1 and any(ln.startswith("layers") and "GARDEN.md" in ln and "law" in ln and "work" in ln
                                    for ln in r.out.splitlines()), r.out[-500:])
except Exception as e:  # noqa: BLE001 — a crash of the suite is a failure of it, said once
    import traceback
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False, traceback.format_exc()[-900:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nlayers: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
