#!/usr/bin/env python3
"""dmreview — gather the evidence a Part B judgment needs. It does NOT judge.

Part A is what a machine checks. Part B is what only a person can. But "unenforceable" is not the same
as "unsupportable": a gate cannot tell whether provenance is HONEST or whether prose reads correctly
cold — and it can still put in front of you every place where that question arises, so the judging is
quick and complete instead of a hunt.

Everything printed here is a QUESTION, not a violation. Most of it will be fine, and that is expected:
these are the places where being wrong would be invisible to the gate, not places that are wrong.

IT ALWAYS EXITS 0, deliberately. A judgment aid that can fail a build becomes a rule, and a rule that
encodes a judgment nobody made is worse than no rule — it launders an opinion into an enforcement.
If a signal here ever earns enforcement, it belongs in the gate with evidence, and it leaves this file.

Usage: python3 bin/dmreview.py [--all]     (--all lists every occurrence rather than a sample)
"""
import difflib, glob, os, re, sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL = '--all' in sys.argv
FACTUAL = ('owns', 'attributes', 'details')

DOCS = {}
for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
         sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))):
    h, body = dmparse.read(f)
    if h is None:
        continue
    try:
        fm = dmparse.loads(h) or {}
    except Exception:
        continue
    i = fm.get('bean') or fm.get('mapping')
    if i:
        DOCS[i] = (fm, body)


def leaves(node, prefix=''):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from leaves(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from leaves(v, f"{prefix}[{i}]")
    elif isinstance(node, str):
        yield prefix, node


def factual():
    for b, (fm, _) in DOCS.items():
        for p, v in leaves(fm):
            if p.split('.')[0] in FACTUAL:
                yield b, p, v


def head(item, question):
    print(f"\n\033[1m{item}\033[0m" if sys.stdout.isatty() else f"\n{item}")
    print(f"  ? {question}")


def sample(rows, n=6):
    for r in (rows if ALL else rows[:n]):
        print(f"    {r}")
    if not ALL and len(rows) > n:
        print(f"    … {len(rows) - n} more (--all)")


print("dmreview — evidence for the judgments the gate cannot make. Nothing here is a violation.")

# ---- Rule 6: paper-durable ----------------------------------------------------------------------
head("CAPSULE / PAPER-DURABLE",
     "does this still read correctly cold, years later? A relative time word fixes prose to the day "
     "it was written, and the reader will not know which day that was.")
REL = re.compile(r'\b(currently|current|today|yesterday|recently|now|at present|these days|soon|lately)\b', re.I)
rows = [f"{b}.{p} -> '{REL.search(v).group(0)}'  {v[:70]}…" for b, p, v in factual() if REL.search(v)]
print(f"  {len(rows)} occurrence(s) of a relative time word in a recorded fact")
sample(rows)

# ---- Rule 6: a key that carries a date ------------------------------------------------------------
head("CAPSULE / KEY NAMES",
     "a key with a date in its NAME cannot be superseded — the next reader adds a second dated key "
     "rather than correcting the first. Is the date part of the fact, or part of when you learned it?")
dated = [f"{b}.{sect}.{k}" for b, (fm, _) in DOCS.items() for sect in ('details', 'attributes', 'owns')
         for k in (fm.get(sect) or {}) if re.search(r'\d{4}[_-]\d{2}', str(k))]
print(f"  {len(dated)} key(s) with a date baked into the name")
sample(dated)

# ---- external truth referenced, not mirrored -------------------------------------------------------
head("EXTERNAL TRUTH REFERENCED, NOT MIRRORED",
     "the gate catches a VERBATIM duplicate. This is the paraphrase it cannot: two beans saying nearly "
     "the same thing, where one should own the fact and the other point at it. Structural similarity "
     "(sibling addons sharing a manifest shape) is fine — restated CONTENT is not.")
# A transcription of external truth that is POINTED AT by a staleness-keyed cache entry is a CACHE,
# not a mirror: it knows when it goes stale, and bin/dmstale.py checks. That is the legitimate form the
# Part B item asks for, so those are marked rather than raised — an aid that keeps surfacing a settled
# case teaches the reader to skim past the ones that matter.
# THE FORM IS THE TERM'S, READ FROM IT. This test was a literal tuple of prefixes until 2026-09-20 —
# `('git-head:', 'digest:')` — and std-vocab 11.0 replaced both with `<repo>@<sha>` without anyone
# coming back here. Every tracked cache then failed the test, so this aid reported 0 CACHES and asked
# the reader to judge 38 pairs it had already settled: the exact harm the note above warns about,
# produced by the aid itself. `manual:` keys count too — an entry a person re-checks by hand is
# tracked, just not machine-checkable, which is a different question and dmstale's to answer.
import dmcheck as _law
_STALENESS = dict(_law.dmform.facet(_law.form_of('analysis_cache'), 'pattern', 'entry')
                  ).get('staleness_key') or r'(?!)'   # no pattern in the law -> nothing matches, and
                                                       # the law's absence shows rather than passing
cached = set()
for _b, (_fm, _) in DOCS.items():
    for _ct, _e in (_fm.get('analysis_cache') or {}).items():
        if not re.match(_STALENESS, str(_e.get('staleness_key', ''))):
            continue
        _r = _e.get('summary_ref') or []
        for _ptr in (_r if isinstance(_r, list) else [_r]):
            if isinstance(_ptr, str) and '.' in _ptr:
                cached.add(f"{_b}.{_ptr}")

vals = [(b, p, v) for b, p, v in factual() if len(v) > 80]
pairs = []
_LO = 0.72
# NEAR-DUPLICATE DETECTION, PAIRWISE — and difflib.ratio() is O(n*m) in the STRING LENGTHS, not in the
# number of values. On 2026-08-07 this stopped terminating: the pair count grows as the square of the
# corpus while each comparison grows as the product of two prose lengths, and a release that added a
# lot of long prose pushed it past any useful runtime. It was NOT introduced by that release — the
# committed version hangs on the same corpus — it was made reachable by it.
#
# THE FILTERS BELOW CHANGE NOTHING THAT IS REPORTED. Both are EXACT upper bounds on ratio():
#   - 2*min(len)/(len_a+len_b) is the best ratio two strings of those lengths could possibly reach,
#     since ratio() = 2*M/T and M cannot exceed the shorter string;
#   - quick_ratio() is documented as an upper bound, computed on the multiset of characters, O(n).
# A pair whose upper bound cannot reach the threshold cannot be a finding, so skipping it is not a
# heuristic and loses no pair. Verified by comparing the full output against the unfiltered
# implementation on a subset the slow one can still finish.
#
# seq2 is held fixed in the outer loop because SequenceMatcher caches the b2j index for its SECOND
# sequence; varying seq1 inside reuses that work instead of rebuilding it for every pair.
#
# `autojunk` is left at its DEFAULT. An earlier attempt here passed autojunk=False, which is not a
# speed knob: it changes which elements ratio() treats as junk and therefore changes the ratio itself,
# so it would have silently altered which pairs are reported. A performance fix that moves a finding
# is not a performance fix.
_sm = difflib.SequenceMatcher(None)
_ctr = [Counter(v) for _b, _p, v in vals]      # the character multiset, computed ONCE per value rather
                                               # than rebuilt inside every pair, which is what
                                               # SequenceMatcher.quick_ratio() has to do after set_seq1
for j in range(len(vals)):
    _sm.set_seq2(vals[j][2])
    _lj, _cj = len(vals[j][2]), _ctr[j]
    for i in range(j):
        if vals[i][0] == vals[j][0]:
            continue
        _li = len(vals[i][2])
        if 2.0 * min(_li, _lj) / (_li + _lj) <= _LO:      # exact length bound — cannot reach threshold
            continue
        if 2.0 * sum((_ctr[i] & _cj).values()) / (_li + _lj) <= _LO:   # quick_ratio's bound, cached
            continue
        _sm.set_seq1(vals[i][2])
        r = _sm.ratio()
        if _LO < r < 1.0:
            pairs.append((r, f"{vals[i][0]}.{vals[i][1]}", f"{vals[j][0]}.{vals[j][1]}"))
pairs.sort(reverse=True)
tracked = [p for p in pairs if p[1] in cached and p[2] in cached]
raw = [p for p in pairs if p not in tracked]
bykey = Counter(p[1].split('.', 1)[1] for p in raw)
print(f"  {len(tracked)} pair(s) are staleness-keyed CACHES of external truth — tracked, not mirrored, "
      f"and dmstale verifies them. Not a question.")
print(f"  {len(raw)} pair(s) remain to judge"
      + (f"; most concentrated in: " + ", ".join(f"{k} ({n})" for k, n in bykey.most_common(3))
         if raw else ""))
sample([f"{r:.0%}  {a}\n           {b}" for r, a, b in raw])

# ---- provenance honest -----------------------------------------------------------------------------
head("PROVENANCE HONEST",
     "an anchor may carry its own provenance where its source differs from its bean's — the model supports it, "
     "and the gate deliberately does NOT judge it (a rule to do so was tested and rejected). But it is "
     "also exactly where an agent can write `asserted-by-human` on a value it minted itself. Did a "
     "person actually assert these?")
rows = [f"{b}: anchor {a['key']} provenance={a['provenance']}  (bean provenance src={src}, by={by[:44]})"
        for b, (fm, _) in DOCS.items()
        for src, by in [((fm.get('provenance') or {}).get('src'), str((fm.get('provenance') or {}).get('by', '')))]
        for a in ((fm.get('identity') or {}).get('anchors') or [])
        if isinstance(a.get('provenance'), dict) and a['provenance'].get('src') == 'asserted-by-human' and src != 'asserted-by-human']
print(f"  {len(rows)} anchor(s) asserted by a person on a bean a person did not assert")
sample(rows)

# ---- abstraction, not force-fit ---------------------------------------------------------------------
head("ABSTRACTION, NOT FORCE-FIT",
     "a key used exactly once is either a genuinely unique datum kept intact — which is correct — or a "
     "fact bent to fit a shape that nearly suited it. Only a reader can tell which.")
kc = Counter(f"{sect}.{k}" for _b, (fm, _) in DOCS.items() for sect in ('attributes', 'details')
             for k in (fm.get(sect) or {}))
once = sorted(k for k, n in kc.items() if n == 1)
print(f"  {len(once)} of {len(kc)} keys in attributes/details are used exactly once")
sample(once, 8)

# ---- the safety/risk split (added 2026-08-08, human-ratified reservation) ------------------------
head("SAFETY NOTES THAT LOOK LIKE FINDINGS",
     "`details.safety` is RESERVED for mechanisms, lessons and constraints — how a thing works and what "
     "breaks it. A live defect belongs in `risks`, on the bean that owns the failing thing. Only a reader "
     "can tell which a sentence is, so these are the ones worth re-reading, not the ones that are wrong.")
# WHY THIS SIGNAL EXISTS. On 2026-08-08 a consolidation swept every STRUCTURED risk carrier and missed
# four live risks sitting in prose — the worst on a bean that already carried `risks` after the sweep.
# The words below are the ones those four actually used; this is a regex over English and it will both
# over- and under-fire, which is exactly why it prints questions and never fails a build.
RISKY = re.compile(r'STILL OPEN|remains? open|rotation (is )?(still )?owed|is owed|un(pinned|guarded'
                   r'|proven|rotated)\b|SPOF|not (yet )?(fixed|closed|rotated)', re.I)
flagged = []
for _b, (fm, _) in DOCS.items():
    notes = (fm.get('details') or {}).get('safety') or []
    if isinstance(notes, str):
        notes = [notes]
    has_risks = 'risks' in fm
    for s in notes:
        if isinstance(s, str) and RISKY.search(s):
            flagged.append(f"{_b}{'' if has_risks else '  (no `risks` term at all)'}: {s[:96]}")
print(f"  {len(flagged)} safety note(s) carry risk-shaped language")
sample(flagged, 8)
if not flagged:
    print("    none — which is a claim about this REGEX, not about the prose. A finding worded in words "
          "it does not match is still sitting there.")

# ---- Tier-0 relations this garden has not drawn (moved here from the gate, 2026-09-17) ------------------
head("TIER-0 RELATIONS NOBODY DRAWS",
     "the standard offers these edges and no bean in this garden uses one. A young or small garden may never "
     "need them, which is why the gate no longer warns. Is one of them the right way to say something a "
     "bean currently says in prose?")
_gate = _law                         # already imported above, for the staleness form
_gate.build_docs()
_drawn = set(_gate.drawn_edges())
_undrawn = sorted(t for t, s in _gate.SCHEMAS.items()
                  if (lambda _f: _gate.dmform.ref_attrs(_f, 'self') or _gate.dmform.ref_attrs(_f, 'entry'))(
                      _gate.dmform.attribute_form(None, s)) and t in _gate.TIER0_TERMS and t not in _drawn)
print(f"  {len(_undrawn)} Tier-0 relation(s) drawn by no bean")
sample(_undrawn, 12)

print("\n— nothing above is a finding. If any of it becomes checkable with evidence, it belongs in the "
      "gate and leaves this file.")
sys.exit(0)
