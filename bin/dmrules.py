#!/usr/bin/env python3
"""dmrules — print the rules this garden currently enforces.

DERIVED, never written by hand: everything below is read out of the vocabulary that bin/dmcheck.py
enforces, so this listing cannot drift from the law. If a rule appears here it is checked; if it is
checked it appears here. The only hand-written section is CORE, which is the bean grammar that is not
a per-term rule and so still lives in code.

Usage: python3 bin/dmrules.py [--terms] [--core]     (no flags = everything)
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmform          # a term's law keyed by attribute — the one reader of the schema constructs
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STD = os.path.join(ROOT, 'seed', 'std-vocab.md')
if not os.path.exists(STD):
    sys.exit(f"std-vocab not found at {STD} — the law has ONE path and there is no fallback")

def _product():
    """`daftar v<tag>` — DERIVED from git, because the version lives in an annotated tag and nowhere else.
    Every version this repo ever typed into prose rotted (four titles reading v1.0 over v2 bodies, two
    stale pins); the two that stayed correct were derived. A tag has no second copy to disagree with."""
    try:
        import subprocess as _sp
        v = _sp.run(['git', '-C', ROOT, 'describe', '--tags', '--always', '--dirty'],
                    capture_output=True, text=True, timeout=5).stdout.strip()
        return f"daftar {v}" if v else "daftar (untagged)"
    except Exception:
        return "daftar (untagged)"

std = dmparse.loads(dmparse.read(STD)[0]) or {}
loc = dmparse.loads(dmparse.read(os.path.join(ROOT, 'VOCAB.md'))[0]) or {}
prof_names = loc.get('extends_profiles') or []
prof_terms = [t for p in prof_names for t in ((std.get('profiles') or {}).get(p, {}).get('terms') or [])]
# A PROFILE'S VACANCIES ARE PART OF THE LAW IN FORCE and were never listed here. dmcheck has always read
# them — they join the tier0 bucket — so the GATE was right and only this REPORT was silent, which is the
# worse half to be wrong in: this is the file an agent reads to learn the rules. Three `code` vacancies had
# been invisible since profiles were introduced; `network` added two more and that is what exposed it.
prof_vacs = [v for p in prof_names for v in ((std.get('profiles') or {}).get(p, {}).get('vacancies') or [])]

TERMS, TIER = {}, {}
for t, tier in [(t, 'tier0') for t in (std.get('terms') or [])] + \
               [(t, f'profile:{",".join(prof_names)}') for t in prof_terms] + \
               [(t, 'garden') for t in (loc.get('local_terms') or [])]:
    n = t.get('term')
    if not n:
        continue
    if n in TERMS:                       # a garden overlay merges onto its Tier-0 base
        base = dict(TERMS[n])
        sch = {**(base.get('schema') or {}), **(t.get('schema') or {})}
        base.update(t); base['schema'] = sch
        TERMS[n] = base; TIER[n] = TIER[n] + '+overlay'
    else:
        TERMS[n] = t; TIER[n] = tier
reg = lambda k: loc.get(k) if loc.get(k) is not None else (std.get(k) or [])
want = set(a for a in sys.argv[1:] if a.startswith('--')) or {'--terms', '--core'}


def head(s):
    print(f"\n\033[1m{s}\033[0m" if sys.stdout.isatty() else f"\n{s}")
    print('─' * len(s))


print(f"{_product()} rules — {loc.get('extends')} + garden '{loc.get('vocab')}'"
      f"{' + profiles ' + ', '.join(prof_names) if prof_names else ''}")

head("AXIS — nature routes every bean to the crown")
for n in reg('natures'):
    print(f"  {n['nature']:14} → crown '{n['crown']}'   anchors {n.get('establishing_anchor_family')}"
          f"   min establishing when confirmed: {n.get('min_establishing_anchors')}")
cr = reg('crown')
print(f"  crown: {' , '.join(c['branch'] + (' (root, never nameable)' if c.get('root') else '') for c in cr)}")
kinds = list(std.get('kinds') or []) + list(loc.get('local_kinds') or [])
print(f"  kinds: " + ' , '.join(f"{k['kind']}→{k.get('of_nature')}"
                                + ('*' if k.get('ownership_form') else '') for k in kinds))
print(f"         (* pinned to the '{next(k['ownership_form'] for k in kinds if k.get('ownership_form'))}'"
      f" ownership form, which also RESERVES it)")

head("ASPECTS — oppositions are closed figures (a position names its mutual complement); sequences are walked")
WALK_KEYS = {a['term_key']: a for a in reg('aspects') if a.get('term_key')}
for a in reg('aspects'):
    if a.get('figure') == 'sequence':
        on = [n for n, t in TERMS.items() for k in WALK_KEYS
              if WALK_KEYS[k] is a and (t.get('schema') or {}).get(k) is True]
        print(f"  {a['aspect']:12} sequence   lines {a.get('lines')} · metered {a.get('metered')} · order "
              f"{a.get('order')} · acyclic {a.get('acyclic')} · ends {a.get('ends')} · domain "
              f"{(a.get('domain') or {}).get('systems')}")
        if on:
            print(f"               walked by: " + ', '.join(on))
        continue
    pos = a.get('positions') or []
    _raw = a.get('poles') or []
    _axes = _raw if (_raw and isinstance(_raw[0], list)) else ([_raw] if _raw else [])
    print(f"  {a['aspect']:12} {a.get('figure')}   {len(_axes)}-axis   "
          + ' , '.join(f"{ax[0]} ↔ {ax[1]}" for ax in _axes if len(ax) == 2))
    seen = set()
    for p in pos:
        pair = tuple(sorted((p['position'], p['complement'])))
        if pair in seen:
            continue
        seen.add(pair)
        print(f"               {p['position']} ↔ {p['complement']}")
    print(f"               used by: " + ', '.join(
        n for n, t in TERMS.items()
        for x in dmform.aspects_of(t.get('schema'))
        if x.get('aspect') == a['aspect']))

if '--terms' in want:
    head("TERMS — every rule below is enforced by the generic interpreter")
    for n in sorted(TERMS):
        t = TERMS[n]; s = t.get('schema') or {}
        if not s:
            # A term with no `schema:` carries no bean-shape rule — but if it declares an `anchor:`
            # policy, CORE still enforces that, and saying "not enforced" would be false.
            eb = t.get('enforced_by')
            if eb == 'core':
                print(f"  {n:20} [{TIER[n]}]  no schema — enforced by CORE (see the CORE section)")
                continue
            if eb == 'none':
                print(f"  {n:20} [{TIER[n]}]  no rule to check — declared explicitly, not an oversight")
                continue
            a = t.get('anchor') or {}
            if 'establishing' in a:
                print(f"  {n:20} [{TIER[n]}]  no schema — but CORE enforces its anchor policy: "
                      f"establishing={a['establishing']}"
                      f"{' (class ' + a['class'] + ')' if a.get('class') else ''}")
            else:
                print(f"  {n:20} [{TIER[n]}]  documentation only — no rule attached")
            continue
        F = dmform.attribute_form(TERMS.get(n), s)
        V = F['value']
        bits = []
        if V.get('governs_anchor'): bits.append("anchor format")
        if s.get('shape'):   bits.append(s['shape'])
        elif V.get('values') and not s.get('path'): bits.append("enum only (not carried on beans)")
        if s.get('path'):    bits.append(f"at {s['path']}")
        if s.get('required') is True: bits.append("REQUIRED on every bean")
        for k, v in s.items():
            if k.startswith('required_on_'):
                bits.append(f"required on {k[len('required_on_'):]} {v}")
        for _k, _a in WALK_KEYS.items():
            if s.get(_k) is True:
                bits.append(f"on the '{_a['aspect']}' sequence" + (" · must stay ACYCLIC" if _a.get('acyclic') else ""))
        print(f"  {n:20} [{TIER[n]}]  {' · '.join(bits)}")
        det = []
        _req_self = [a_ for a_, _ in dmform.facet(F, 'required', 'self')]
        _req_entry = [a_ for a_, _ in dmform.facet(F, 'required', 'entry')]
        if V.get('values'):              det.append(f"values {V['values']}")
        if V.get('values_from'):         det.append(f"values from term '{V['values_from']}'")
        if _req_self:                    det.append(f"needs {_req_self}")
        if _req_entry:                   det.append(f"each entry needs {_req_entry}")
        for a_, v in dmform.facet(F, 'values', 'entry'):
            det.append(f"entry.{a_} ∈ {v}")
        for a_, v in dmform.facet(F, 'type', 'entry'):
            det.append(f"entry.{a_} is {v}")
        if F['one_of']:                  det.append(f"each entry has one of {F['one_of']}")
        if s.get('key_form'):            det.append(f"keys: {s['key_form']}")
        if F['mirror']['parity_with']:   det.append(f"same facets as '{F['mirror']['parity_with']}'")
        if F['mirror']['inverse_of']:    det.append(f"inverse of '{F['mirror']['inverse_of']}' — held consistent")
        if F['matches']['equal_kind_attr']: det.append(f"must equal kind.{F['matches']['equal_kind_attr']}")
        if s.get('required_on_targets_of'): det.append(f"required on targets of '{s['required_on_targets_of']}'")
        if V.get('governs_anchor'):
            det.append(f"anchor '{V['governs_anchor']}' must be in canonical form: "
                       f"{V.get('canonical_note') or V.get('form')}")
        if F['matches']['form_from_kind']: det.append(f"form pinned by kind.{F['matches']['form_from_kind']}")
        for _an, x in dmform.facet(F, 'aspect', 'entry'):
            det.append(f"entry.{_an} is a position on aspect '{x['aspect']}'"
                       f" (default {x.get('default')})")
        for d in det:
            print(f"      · {d}")

head("REVERSE GATE — the rules must be passed by the objects")
print("  every position a term declares must be OCCUPIED by a bean, or declared vacant with a reason")
print(f"  reasons: {' | '.join(std.get('vacancy_reasons') or ['NONE DECLARED — the gate refuses'])}"
      f" ; a vacancy also needs a `why`")
print("  a garden accounts only for positions IT declared — Tier-0 accounts for its own")
print("  a local vacancy that becomes occupied is an ERROR; a Tier-0 one WARNS")
for tier, vs in (('tier0', (std.get('vacancies') or []) + prof_vacs),
                 ('garden', loc.get('vacancies') or [])):
    for v in vs:
        print(f"    [{tier}] {v['at']} = '{v['position']}'  ({v['reason']})")

if '--core' in want:
    head("CORE — bean grammar; the only rules not in the vocabulary")
    for line in ["front-matter parses; id == filename; ids kebab-case and unique per space",
                 "every top-level key is declared by a term (its name, or the head of a literal context_key)",
                 "no key is written twice in one mapping, at any depth — in beans, mappings and the law",
                 "required keys present; a bean keeps a human body (Rule 6, paper-durable)",
                 "provenance present; identity capsule present",
                 "anchors need key + value + establishing; a term's declared anchor policy OVERRULES the bean",
                 "establishing anchors dedup — the same anchor on two beans is one object, not two",
                 "every ref resolves; a named field must exist in the target",
                 "acyclicity across all dag-declared relations",
                 "no duplicate authoritative IP (vocab-driven from the std-vocab `ip` term)",
                 "a staged bean change requires a journal entry — provenance duty",
                 "a staged change to the vocabulary or the law must say RULE-CHANGE distinctly",
                 "a staged top-level key REMOVAL must be declared (allow_remove), never silent",
                 "a staged document must not lose its human body",
                 "std-vocab must be found at its one path — there is no fallback",
                 "a garden's `extends:` pin must equal the installed vocabulary version",
                 "a `file:` pointer must resolve to a file that exists in this garden"]:
        print(f"  · {line}")
