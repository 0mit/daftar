#!/usr/bin/env python3
"""fast — corpus integrity, in under two seconds, for the pre-commit hook.

WHY A SECOND SUITE. test/golden.py takes ~66 seconds because it spawns a gate subprocess per negative
case and builds throwaway git repos: it tests whether the MACHINERY BEHAVES. A hook that slow invites
`--no-verify`, which is the failure mode a hook must avoid — and on 2026-08-02 a commit went through
with a failing test for exactly that reason.

This asks a different and cheaper question: IS THE CORPUS SOUND RIGHT NOW. It reads every document once,
in-process, and asserts the properties that must hold of the data — never the gate's negative
behaviours, which is what makes it fast and what keeps it from duplicating golden.py's job. Anything
here that fails means the garden is wrong, not that a rule is wrong.

Run: python3 test/fast.py   (0 = green)
"""
import glob, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse
import dmform           # a term's law is read THROUGH the attribute form, here as everywhere (13.0)
import yaml

results = []
def check(name, ok, detail=''):
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{detail}]" if detail and not ok else ''))

BEANS, MAPS, BAD = {}, {}, []
for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
         sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))):
    base = os.path.basename(f)[:-3]
    is_bean = os.sep + 'beans' + os.sep in f
    head, body = dmparse.read(f)
    if head is None:
        BAD.append(f"{base}: no fences"); continue
    try:
        fm = yaml.safe_load(head)
    except Exception as e:
        BAD.append(f"{base}: {e}"); continue
    if not isinstance(fm, dict):
        BAD.append(f"{base}: front-matter not a mapping"); continue
    if str(fm.get('bean' if is_bean else 'mapping')) != base:
        BAD.append(f"{base}: id != filename")
    if is_bean and not body.strip():
        BAD.append(f"{base}: no human body")
    (BEANS if is_bean else MAPS)[base] = fm

ALL = {**BEANS, **MAPS}
check(f"every one of {len(ALL)} documents parses, is named after its id, and keeps its body",
      not BAD, '; '.join(BAD[:4]))

# ---- the vocabulary loads and its pins agree -------------------------------------------------------
STD = os.path.join(ROOT, 'seed', 'std-vocab.md')
sv = yaml.safe_load(dmparse.read(STD)[0]) or {}
lv = yaml.safe_load(dmparse.read(os.path.join(ROOT, 'VOCAB.md'))[0]) or {}
gd = yaml.safe_load(dmparse.read(os.path.join(ROOT, 'GARDEN.md'))[0]) or {}
ver = str(sv.get('version'))
check(f"the vocabulary loads and both pins match std-vocab@{ver}",
      lv.get('extends') == f'std-vocab@{ver}' and gd.get('extends') == f'std-vocab@{ver}',
      f"VOCAB={lv.get('extends')} GARDEN={gd.get('extends')}")

TERMS = {t['term']: t for t in (list(sv.get('terms') or [])
         + [t for p in (sv.get('profiles') or {}).values() for t in (p.get('terms') or [])]
         + list(lv.get('local_terms') or [])) if isinstance(t, dict) and t.get('term')}
check("every term states a rule, a core-enforcement, or an explicit none",
      not [n for n, t in TERMS.items() if not (t.get('schema') or t.get('enforced_by') or t.get('anchor'))],
      ', '.join(n for n, t in TERMS.items() if not (t.get('schema') or t.get('enforced_by') or t.get('anchor'))))

# ---- ownership closes, in both arcs and all the way up ---------------------------------------------
# WHICH FORMS END A CHAIN AND WHICH CONTINUE IT ARE DERIVED, not listed. The term says both: `entry_one_of`
# offers the forms, the attributes that are `in: ref` point at another bean, and the difference IS the
# terminal set. Listed by hand, the two halves of one rule drifted: this file accepted `contract` as an
# ending while the gate did not, and the vocabulary declares `contract` a ref — so the day a facet is owned
# through a contract, the hook would have passed a chain the gate refuses. Nothing said which was right.
_OB_SCHEMA = (next((t for t in (sv.get('terms') or []) if t.get('term') == 'owned_by'), {}).get('schema') or {})
# READ THROUGH dmform, AND REFUSED WHEN IT COMES BACK EMPTY. v0.22.0 shipped this file still reading
# `entry_ref_fields`, a construct 13.0 had retired an hour earlier: `_REFS` was silently the empty set, so EVERY
# form counted as an ending and this check passed while checking less. A derivation that can come back empty
# without anyone noticing is the defect, so it asserts.
_OB_FORM = dmform.attribute_form(None, _OB_SCHEMA)
_REFS = set(dmform.ref_attrs(_OB_FORM, 'entry'))
_ENDS = set(_OB_FORM['one_of']) - _REFS
_ALT = {'key': (_OB_FORM['alt'] or {}).get('key')}
check("the ownership term still says which forms CONTINUE a chain and which END it — neither set is empty",
      bool(_REFS) and bool(_ENDS), f"refs={sorted(_REFS)} ends={sorted(_ENDS)}")
half = [b for b, fm in BEANS.items() if (fm.get('owned_by') is None) != (fm.get('responsibility') is None)]
check("every bean carries BOTH ownership arcs", not half, ', '.join(half[:5]))
# The ARC's partner and the inherited form's key are the term's own declarations (`facet_parity_with`,
# `alt_form.key`), read here rather than spelled again — the gate stopped keeping its own copy of the second
# one in 8.x for the same reason.
_PARTNER = _OB_SCHEMA.get('facet_parity_with') or 'responsibility'
shape = lambda n: _ALT.get('key') if (_ALT.get('key') and _ALT['key'] in n) else frozenset(n)
mismatch = [b for b, fm in BEANS.items() if fm.get('owned_by')
            and shape(fm['owned_by']) != shape(fm.get(_PARTNER) or {})]
check("the two arcs agree on facets everywhere", not mismatch, ', '.join(mismatch[:5]))



def terminus(b, seen=()):
    if b in seen or b not in BEANS:
        return 'CYCLE'
    ob = BEANS[b].get('owned_by') or {}
    _altkey = _ALT.get('key')
    if _altkey and _altkey in ob:
        return terminus(ob[_altkey]['bean'], seen + (b,))
    for spec in ob.values():
        for k in _ENDS:
            if k in spec:
                return k
        for k in _REFS:
            if k in spec:
                return terminus(spec[k]['bean'], seen + (b,))
    return 'DANGLING'
# WHICH kinds owe an owner at all is DERIVED from the term, never listed here. A `kind: person` carries no
# `owned_by` and is not dangling: the crown owns the living while alive, and the term does not require the
# key. Hardcoding a list here would be a second copy of the obligation that can disagree with the first —
# and this check called a perfectly correct person DANGLING until test/germinate.py wrote one.
_ob = (next((t for t in (sv.get('terms') or []) if t.get('term') == 'owned_by'), {}).get('schema') or {})
OWES = set(_ob.get('required_on_kinds') or [])
ends = {b: terminus(b) for b, fm in BEANS.items()
        if fm.get('owned_by') is not None or fm.get('kind') in OWES}
check("every ownership chain that is owed terminates at the crown or outside — none dangles or loops",
      all(e in _ENDS for e in ends.values()),
      str({b: e for b, e in ends.items() if e not in _ENDS}))

# ---- Rule 6: the capsule reads on paper --------------------------------------------------------------
# A key name that pins the key to a MOMENT — a date or a version — cannot be superseded: the next reader
# adds a second pinned key beside the first instead of correcting it. This scanned only the three fact
# sections and never the TOP level, where it happened twice on one bean: `status_2026_08_02` was
# superseded by `status_2_0` rather than corrected, which is the failure the rule exists to prevent,
# demonstrated in the corpus the rule was meant to protect. Both forms, both places, now.
PINNED = re.compile(r'\d{4}[_-]\d{2}|_v?\d+_\d+$')
dated = ([f"{b}.{k}" for b, fm in ALL.items() for k in fm if PINNED.search(str(k))]
         + [f"{b}.{s}.{k}" for b, fm in ALL.items() for s in ('details', 'attributes', 'owns')
            for k in (fm.get(s) or {}) if PINNED.search(str(k))])
check("no key NAME is pinned to a date or a version, at any level (it could never be superseded)",
      not dated, ', '.join(dated[:4]))

# ---- one owner of a fact ------------------------------------------------------------------------------
restating = []
for b, fm in BEANS.items():
    src = ((fm.get('details') or {}).get('logs') or {}).get('source')
    cp = [c.get('path') for c in (fm.get('code_paths') or []) if c.get('role') == 'own-source']
    gr = {a['key']: a['value'] for a in ((fm.get('identity') or {}).get('anchors') or [])}.get('git_remote')
    if src and cp and gr and cp[0] in str(src) and str(gr) in str(src):
        restating.append(b)
check("no bean restates its own code_path and git_remote as prose", not restating, ', '.join(restating))

# ---- caches are addressable, and anchors are classed -------------------------------------------------
_STALENESS = dict(dmform.facet(dmform.attribute_form(TERMS.get('analysis_cache'),
                                                     (TERMS.get('analysis_cache') or {}).get('schema')),
                               'pattern', 'entry')).get(
    'staleness_key') or r'(?!)'      # no pattern in the law -> nothing matches, and the law's absence shows
badcache = [f"{b}/{c}" for b, fm in BEANS.items() for c, e in (fm.get('analysis_cache') or {}).items()
            # THE PATTERN IS THE TERM'S, read from it. Kept here as a literal, it was left behind when the
            # law moved in 11.0 and this file refused a garden for migrating its keys exactly as the new law
            # required — the gate saying one thing and the hook another, about one rule.
            if not re.match(_STALENESS, str(e.get('staleness_key', '')), re.ASCII)]
check("every cache entry carries a checkable staleness key", not badcache, ', '.join(badcache[:4]))
noflag = [b for b, fm in ALL.items() for a in ((fm.get('identity') or {}).get('anchors') or [])
          if not isinstance(a.get('establishing'), bool)]
check("every anchor states whether it establishes identity", not noflag, ', '.join(noflag[:4]))

# ---- the version lives in git, and in exactly one place ------------------------------------------------
# THIS is what makes "the version is a git tag" structural rather than a matter of discipline. Every
# version this repo ever TYPED rotted — four titles reading v1.0 over v2 bodies, two prose pins two majors
# stale — while the two that were DERIVED stayed correct. log/journal.md is exempt: it is history, and a
# dated entry naming the version it was written under is a record, not a second copy.
VERSION_IN_PROSE = re.compile(r'daftar\s+v?\d+\.\d+')
stated = []
for f in glob.glob(os.path.join(ROOT, '**', '*.md'), recursive=True):
    if os.sep + '.git' + os.sep in f or f.endswith(os.path.join('log', 'journal.md')):
        continue
    for i, line in enumerate(open(f, encoding='utf-8'), 1):
        if VERSION_IN_PROSE.search(line):
            stated.append(f"{os.path.relpath(f, ROOT)}:{i}")
check("no document states the product version — it is a git tag and nothing else",
      not stated, ', '.join(stated[:5]))

# ---- a declared law_carrier must name the path the gate ACTUALLY reads --------------------------------
# THIS FILE TRAVELS. `germinate.sh` copies it into every new garden, so it may assert only what is true of
# ANY garden — never a fact about this estate. A check that named `beans/daftar.md` failed in a germinated
# garden on its first run, correctly: that bean is this garden's and never travels.
# So the universal form: a bean MAY declare where the law is, and if it does, the two sources must agree.
# That is a cross-check between the bean and the tool, not a presence assertion — the failure it catches
# is the bean claiming the law lives somewhere the gate does not look, which is the one way this single
# bootstrap datum can be wrong without anything else noticing.
carriers = [(b, str((fm.get('law_carrier') or {}).get('path', '')))
            for b, fm in BEANS.items() if fm.get('law_carrier')]
disagree = [f"{b}: bean says {p!r}, gate reads 'file:{os.path.relpath(STD, ROOT)}'"
            for b, p in carriers if p != 'file:' + os.path.relpath(STD, ROOT)]
check(f"every declared law_carrier ({len(carriers)}) names the path the gate actually reads",
      not disagree, '; '.join(disagree))
nostanding = [b for b, _ in carriers if not (BEANS[b].get('standing') or [])]
check("a bean that carries the law's address also states which documents are law",
      not nostanding, ', '.join(nostanding))

print(f"\nfast: {sum(results)}/{len(results)} corpus checks passed")
sys.exit(0 if all(results) else 1)
