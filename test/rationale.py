#!/usr/bin/env python3
"""The law and its reasons are kept apart and related by key.

LAW says what is in force; RATIONALE says why; the RECORD says what happened. This holds the separation: the law's
front matter carries no free commentary, every reason names something the law still says, and the narrative that
still sits INSIDE the law's data (`meaning:` / `why:` strings that tell a story) may shrink and may not grow.
"""
import os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bin"))
import dmwhy, dmparse
FAILS = []

def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:700]))
    if not cond:
        FAILS.append(name)

fm = dmparse.split_front_matter(open(dmwhy.LAW, encoding="utf-8").read())[0]
TITLE = re.compile(r'^\s*# == [^=]+ ==$')

def comment_of(line):
    q = None
    for i, ch in enumerate(line):
        if ch in "\"'":
            q = None if q == ch else (q or ch)
        if ch == "#" and q is None and (i == 0 or line[i - 1] in " \t"):
            return line[i:]
    return None

stray = [l for l in fm.split("\n") if comment_of(l) and not TITLE.match(l)]
check("the law's front matter carries no commentary — only section titles", not stray, stray[:4])
titles = [l.strip() for l in fm.split("\n") if TITLE.match(l)]
check("...and a title is a title: no date, no version, no sentence",
      not [t for t in titles if re.search(r"\d\.\d|20\d\d|\(|—|\. ", t)], [t for t in titles if re.search(r"\d\.\d|20\d\d|\(|—|\. ", t)][:5])
why = dmwhy.rationale()
check("the rationale is not empty, and every reason names something the law still says", len(why) > 100 and not dmwhy.orphans(), dmwhy.orphans()[:6])
check("no reason is blank", not [k for k, v in why.items() if not v.strip()], [k for k, v in why.items() if not v.strip()][:5])

# A RATCHET, NOT A VERDICT. Stories also sit inside the law's DATA — a `meaning:` or a `why:` that says when a thing was
# found and by whom. Moving each is an edit to a sentence, so it is done by hand; this number may only go DOWN.
NARRATIVE_IN_DATA = 14
story = re.compile(r"\b20\d\d-\d\d-\d\d\b|\bfirst draft\b|\bthe operator\b|\bthis estate\b|\bthis garden\b|\bwithin the hour\b|\b(until|since) \d+\.\d\b", re.I)
hits = [l.strip()[:90] for l in fm.split("\n") if re.search(r"^\s*(-\s*)?[\w\"' .-]*(meaning|why|note|form_note|decision|case)\"?\s*:", l) and story.search(l)]
check(f"narrative inside the law's data has not grown (now {len(hits)}, ceiling {NARRATIVE_IN_DATA})", len(hits) <= NARRATIVE_IN_DATA, hits[:4])
print(f"      (the ceiling can come down to {len(hits)})")

# ---------------------------------------------------------------- LEAKS BETWEEN THE LAYERS, one direction at a time
# UP: a layer may point DOWN to the one beneath, never the other way. A law that says "see the rationale" cannot be
# applied alone, and "clear and brief, for usability" means it can.
import glob
data_lines = [l for l in fm.split("\n") if not TITLE.match(l)]
PROSE = re.compile(r"(meaning|why|note|form_note|refusal|pattern_why|extent_why)\"?\s*:")      # what a reader is TOLD; where the
up = [l.strip()[:100] for l in data_lines if PROSE.search(l)                                  # journal lives is itself law
      and re.search(r"RATIONALE|HISTORY\.md|log/journal|the journal entry|pull request|daftar#\d|\bPR ?#?\d", l)]
check("the law points at no layer beneath it: it can be applied alone", not up, up[:4])
# THE GATE READS LAW AND NOTHING ELSE. If a verdict ever depended on the reasoning, the reasoning would be law without
# being ratified as law.
readers = [os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "bin", "dm*.py")) if "RATIONALE" in open(f, encoding="utf-8").read()]
check("only the reader of reasons opens the reasoning: no verdict can depend on it", readers == ["dmwhy.py"], readers)
# SIDEWAYS: a reason that speaks of a law name the law no longer has is no longer a reason; it is an account of what
# used to be, which is a journal's business. A ratchet, because sorting them is editorial work.
STALE_REASONS = 7
st = dmwhy.stale()
check(f"reasons that have become journal have not grown (now {len(st)}, ceiling {STALE_REASONS})", len(st) <= STALE_REASONS, list(st.items())[:3])
print(f"      (the ceiling can come down to {len(st)})")

print("\nrationale: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
