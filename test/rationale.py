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
# found and by whom. Moving each is an edit to a sentence, so it is done by hand; the count may only go DOWN.
#
# THE PARSED LAW, NOT ITS LINES. This counted lines of the file until 21.0, and a line grep sees only the first line of
# a folded `>` block: it read fourteen while forty-five sat in the law, and the one spare it was set with was spent
# unseen. It now reads every string under a key the law TELLS a reader (bin/dmreview.py `story_in`: the one
# definition, which `dmreview --law` lists for whoever ratifies). Its CEILING is the count in the release this branch
# started from, read from git — not a number typed here, which is a second copy of a fact git holds, and which drifted.
# The constant is only for a clone with no tags (a shallow CI checkout): the count at the release it was written in.
import subprocess
import dmreview
NARRATIVE_IN_DATA = 45
hits = dmreview.story_in(dmparse.loads(fm))
_tag = subprocess.run(["git", "-C", ROOT, "describe", "--tags", "--abbrev=0"], capture_output=True, text=True).stdout.strip()
_at_tag = dmreview.law_at(_tag) if _tag else None
ceiling, since = (len(dmreview.story_in(_at_tag)), _tag) if _at_tag else (NARRATIVE_IN_DATA, "no tag here: the constant")
check(f"narrative inside the law's data has not grown (now {len(hits)}, ceiling {ceiling} — {since})",
      len(hits) <= ceiling, [f"{p}: «{h}»" for p, h, _s in hits][:6])
print(f"      (the next release's ceiling is {len(hits)}; `python3 bin/dmreview.py --law` lists every one by path)")
_folded = {"terms": [{"term": "t", "meaning": "a first line that tells nothing,\nand a second that says what was found on 2020-01-01"}]}
check("...read from the parsed law: a date on the second line of a folded block is counted, which a line grep missed",
      len(dmreview.story_in(_folded)) == 1, dmreview.story_in(_folded))
_example = {"terms": [{"term": "t", "meaning": "a day in the civil calendar, written `2020-01-01`",
                       "schema": {"attrs": {"a": {"in": "prose", "canonical_note": "since 7.0 the form is fixed"}}}}]}
check("...a date inside backticks is an example of a value and is not counted; a suffixed key (`canonical_note`) is read",
      [p for p, _h, _s in dmreview.story_in(_example)] == ["terms[t].schema.attrs.a.canonical_note"], dmreview.story_in(_example))
_r = subprocess.run([sys.executable, os.path.join(ROOT, "bin", "dmreview.py"), "--law"] + (["--against", _tag] if _tag else []),
                    capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
_first = (_r.stdout.split("\n") or [""])[0]
check("dmreview --law prints the preconditions as evidence and exits 0, whatever it finds",
      _r.returncode == 0 and "the preconditions of beauty in the law, counted — the person who merges judges" in _first,
      (_r.stdout + _r.stderr)[-500:])
_n = re.search(r"(?m)^STORY IN THE LAW.*\n  strings\s+(\d+)", _r.stdout)
check("...and the story it lists is the story this ratchet counts: one definition, read by both",
      _n is not None and int(_n.group(1)) == len(hits), _n.group(0) if _n else _r.stdout[-400:])
if _tag:
    check("...and with --against, each line says how it moved since that ref", "(was " in _r.stdout or "(unchanged)" in _r.stdout,
          _r.stdout[:600])

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

# ---------------------------------------------------------------- 18.1: the PROSE law documents, the same way
_why = dmwhy.rationale()
_doc = [k for k in _why if k.startswith("doc:")]
check("a prose law document's reasons are keyed by its numbered SECTION, and every one names a section that exists",
      len(_doc) >= 8 and not [k for k in dmwhy.orphans() if k.startswith("doc:")], str(_doc))
def _gone(k):
    try:
        dmwhy.resolve({}, k); return False
    except KeyError:
        return True
check("...and a reason whose section is gone is an orphan, like a reason whose path is gone",
      _gone("doc:MERGE.md#99") and _gone("doc:NO-SUCH.md#1") and not _gone("doc:MERGE.md#5.1"))
_story = re.compile(r"\(20[0-9]{2}-[0-9]{2}-[0-9]{2}|added 20[0-9]{2}|[Uu]ntil this date|used to |was found to|— deleted$|— superseded$")
for _name in ("MODEL.md", "CHECKLIST.md", "MERGE.md"):
    _hits = [l.strip()[:90] for l in open(os.path.join(ROOT, _name), encoding="utf-8") if _story.search(l)]
    check("%s states what is in force and tells no story of how it came to be" % _name, not _hits, str(_hits[:3]))

# ---------------------------------------------------------------- 18.0: a GARDEN's overlay has its reasoning too
import subprocess, tempfile, shutil
_T = tempfile.mkdtemp(prefix="dmwhy-"); _G = os.path.join(_T, "g")
subprocess.run(["sh", os.path.join(ROOT, "seed", "germinate.sh"), _G, "--gardener", "keeper"], cwd=ROOT, capture_output=True, text=True)
_v = os.path.join(_G, "VOCAB.md"); _s = open(_v).read(); assert _s.count("local_terms: []") == 1
open(_v, "w").write(_s.replace("local_terms: []", """local_terms:
  - term: shelf
    meaning: "which shelf a thing is kept on"
    context_keys: [shelf]
    merge: { cardinality: single, order: none }"""))
def _why(text):
    open(os.path.join(_G, "RATIONALE.md"), "w").write(text)
    r = subprocess.run([sys.executable, os.path.join(_G, "bin", "dmwhy.py"), "--check"], cwd=_G, capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr
_rc, _o = _why("# why this garden's terms are as they are\n\n## local_terms[shelf]\n\nthings were being lost.\n")
check("a garden keeps the reasoning for ITS OWN terms beside its VOCAB.md, under the same key and the same check",
      _rc == 0 and "RATIONALE.md: 1 reasons, 0 orphaned" in _o and "seed/RATIONALE.md" in _o, _o[-400:])
_rc, _o = _why("## local_terms[shelf]\n\nthings were being lost.\n\n## local_terms[drawer].meaning\n\na term that is gone.\n")
check("...and a reason whose law is gone is refused there as well", _rc == 1 and "ORPHAN  local_terms[drawer].meaning" in _o, _o[-400:])
shutil.rmtree(_T, ignore_errors=True)

print("\nrationale: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
