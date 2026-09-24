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

def _front(path):
    """A document's front matter, read as the gate reads it: (mapping or None, why it does not read)."""
    try:
        head_ = dmparse.read(path)[0]
    except dmparse.NotUTF8 as e:
        return None, str(e)
    except OSError as e:
        return None, f"cannot be read ({e.strerror})"
    if head_ is None:
        return None, "no --- fences"
    try:
        fm = dmparse.loads(head_)
    except Exception as e:
        return None, dmparse.escaped(str(e).splitlines()[0] if str(e) else type(e).__name__)
    return (fm if isinstance(fm, dict) else None), (None if isinstance(fm, dict) or fm is None else "not a mapping")


std, _why = _front(STD)
if std is None:
    # THE LAW HAS ONE PATH: a law that does not read has no rules to list, and listing none would say there are none
    sys.exit(f"seed/std-vocab.md: its front matter does not read ({_why or 'empty'}) — the law has one path and no "
             f"fallback, so no rule is listed until it reads")
# The garden's own vocabulary, read as the gate reads it (bin/dmparse.py `vocab_read`): a VOCAB.md that does not read is
# read as nothing, and an entry that is not in its shape is left out — so no rule is listed that the gate does not
# enforce, and what it refuses is listed, at the end, as refused.
loc, _why = _front(os.path.join(ROOT, 'VOCAB.md'))
NOT_READ = []
if loc is None:
    if _why:
        NOT_READ.append(f"VOCAB.md: its front matter does not read ({_why}) — this garden's own vocabulary is a mapping "
                        f"of what it adds to the law; the rules below are the law's alone")
    loc = {}
NOT_READ += dmparse.vocab_read(loc)
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
    n = t.get('term') if isinstance(t, dict) else None
    if not isinstance(n, str) or not n:
        continue                         # an entry the gate refuses by name is no rule in force
    if n in TERMS:                       # a garden overlay merges onto its Tier-0 base
        base = dict(TERMS[n])
        sch = {**(base.get('schema') or {}), **(t.get('schema') or {})}
        base.update(t); base['schema'] = sch
        TERMS[n] = base; TIER[n] = TIER[n] + '+overlay'
    else:
        TERMS[n] = t; TIER[n] = tier
_RESTATED = {}


def reg(k):
    """A registry as the gate reads it: the garden's restatement (its rows in their shape) or the law's, and the rows
    the garden adds that the base does not already hold."""
    if k not in _RESTATED:
        _RESTATED[k], _why = dmparse.restated_rows(loc, k)
        NOT_READ.extend(_why)
    base = _RESTATED[k] if _RESTATED[k] is not None else [r for r in (std.get(k) or []) if isinstance(r, dict)]
    base = [r for r in base if isinstance(r, dict) and r]
    _add = [r for r in ((loc.get('registry_additions') or {}).get(k) or [])
            if not any(b.get(next(iter(r))) == r[next(iter(r))] for b in base)]
    return list(base) + _add


def _m(x):
    """A field a registry row holds as a mapping, or none: a row the gate refuses for its shape is listed as far as it
    reads, never a traceback."""
    return x if isinstance(x, dict) else {}


def _seq(x):
    return x if isinstance(x, list) else []
want = set(a for a in sys.argv[1:] if a.startswith('--')) or {'--terms', '--core'}


def quantity_rule(qname):
    """What a count of this quantity is held to: its units, from the law or from a registry with their places."""
    if qname == 'any':
        return "any quantity the law declares"
    q = next((x for x in reg('quantities') if isinstance(x, dict) and x.get('quantity') == qname), None)
    if not q:
        return f"'{qname}' is NO quantity the law declares"
    uf = q.get('units_from') if isinstance(q.get('units_from'), dict) else None
    if uf:
        return (f"a unit is a `{uf.get('take')}` of the `{uf.get('registry')}` registry, with at most its `{uf.get('digits')}` "
                f"decimal places; no factor joins two (crosswalk: {q.get('crosswalk')})")
    units = [u.get('unit') for u in reg('units') if u.get('quantity') == qname]
    return f"units {units}, each an exact ratio to the others"


# EVERY LINE IS PRINTED SPELT OUT: a name or a meaning a garden wrote reaches this listing, and a control character in it
# would drive the terminal of the person reading the rules (bin/dmparse.py `said`; the gate refuses such a character).
_print = print


def print(*a, **k):
    _print(*(dmparse.said(x) for x in a), **k)


def head(s):
    _print(f"\n\033[1m{dmparse.said(s)}\033[0m" if sys.stdout.isatty() else f"\n{dmparse.said(s)}")
    print('─' * len(s))


print(f"{_product()} rules — {loc.get('extends')} + garden '{loc.get('vocab')}'"
      f"{' + profiles ' + ', '.join(prof_names) if prof_names else ''}")

head("AXIS — nature routes every bean to the crown")
for n in reg('natures'):
    print(f"  {str(n.get('nature')):14} → crown '{n.get('crown')}'   anchors {n.get('establishing_anchor_family')}"
          f"   min establishing when confirmed: {n.get('min_establishing_anchors')}")
idp = _m(loc.get('identity_policy') or std.get('identity_policy'))
print(f"  identity: an anchor's key {'must be a term that declares anchor:' if idp.get('anchor_key') == 'term' else 'is free text'}"
      f" · the family above is {'ENFORCED — an establishing anchor of a confirmed bean is of it' if idp.get('establishing_family') == 'enforced' else 'guidance; only the count is checked'}")
_mint = _m(idp.get('minted'))
if _mint:
    print(f"  minted: a term whose anchor says `minted: true` admits names a garden gives — a value in the form "
          f"{_mint.get('form')} whose genos is a row of `{_mint.get('form_genos')}` (the garden's local_{_mint.get('form_genos')} too). "
          f"BARE it identifies within its garden only; QUALIFIED by a {_mint.get('qualified_by')} ({_mint.get('pattern')}) "
          f"everywhere, and the prefix is this garden's id or a `garden` bean's. Any other value was assigned outside every "
          f"garden: it identifies wherever it is written and is never qualified")
cr = reg('crown')
print(f"  crown: {' , '.join(str(c.get('branch')) + (' (root, never nameable)' if c.get('root') else '') for c in cr)}")
gene = [k for k in _seq(std.get('gene')) + list(loc.get('local_gene') or []) if isinstance(k, dict)]
print(f"  gene: " + ' , '.join(f"{k.get('genos')}→{k.get('of_nature')}"
                               + ('*' if k.get('ownership_form') else '') for k in gene))
_pinned = next((k['ownership_form'] for k in gene if k.get('ownership_form')), None)
if _pinned:
    print(f"         (* pinned to the '{_pinned}' ownership form, which also RESERVES it)")

head("ASPECTS — oppositions are closed figures (a position names its mutual complement); sequences are walked")
WALK_KEYS = {a['term_key']: a for a in reg('aspects') if isinstance(a.get('term_key'), str)}
for a in reg('aspects'):
    if a.get('figure') == 'sequence':
        on = [n for n, t in TERMS.items() for k in WALK_KEYS
              if WALK_KEYS[k] is a and (t.get('schema') or {}).get(k) is True]
        print(f"  {str(a.get('aspect')):12} sequence   lines {a.get('lines')} · metered {a.get('metered')} · order "
              f"{a.get('order')} · acyclic {a.get('acyclic')} · ends {a.get('ends')} · domain "
              f"{_m(a.get('domain')).get('systems')}")
        if on:
            print(f"               walked by: " + ', '.join(on))
        continue
    pos = [p for p in _seq(a.get('positions')) if isinstance(p, dict)]
    _raw = _seq(a.get('poles'))
    _axes = _raw if (_raw and isinstance(_raw[0], list)) else ([_raw] if _raw else [])
    print(f"  {str(a.get('aspect')):12} {a.get('figure')}   {len(_axes)}-axis   "
          + ' , '.join(f"{ax[0]} ↔ {ax[1]}" for ax in _axes if isinstance(ax, list) and len(ax) == 2))
    seen = set()
    for p in pos:
        pair = tuple(sorted((str(p.get('position')), str(p.get('complement')))))
        if pair in seen:
            continue
        seen.add(pair)
        print(f"               {p.get('position')} ↔ {p.get('complement')}")
    print(f"               used by: " + ', '.join(
        n for n, t in TERMS.items()
        for x in dmform.aspects_of(t.get('schema'))
        if x.get('aspect') == a.get('aspect')))

if '--terms' in want:
    head("TERMS — every rule below is enforced by the generic interpreter")
    for n in sorted(TERMS):
        t = TERMS[n]; s = t.get('schema') or {}
        if not s:
            # A term with no `schema:` carries no bean-shape rule — but if it declares an `anchor:`
            # policy, CORE still enforces that, and saying "not enforced" would be false.
            eb = t.get('enforced_by')
            _anc = t.get('anchor') or {}
            if _anc.get('minted'):
                print(f"  {n:20} [{TIER[n]}]  anchor term, MINTED — CORE enforces establishing={_anc.get('establishing', 'the bean’s to say')}; "
                      f"a qualified value is `<garden_id>/<genos>:<name>`, by a garden this garden knows (see AXIS: minted)")
                continue
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
            if k.startswith('only_on_'):
                bits.append(f"carried ONLY on {k[len('only_on_'):]} {v}")
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
        # 13.0: every attribute says what it is a position IN, so the listing can say it for ALL of them. Until
        # then this printed the enums, the types and the aspects and was silent about registries, forms and refs.
        _w = 'entry' if F['scope'] == 'entry' else 'value'
        for a_, v in dmform.facet(F, 'type'):
            det.append(f"{_w}.{a_} is {v}")
        for a_, r in dmform.facet(F, 'registry'):
            det.append(f"{_w}.{a_} is a row of " + (f"the registry its `{r['registry_from']}` names" if r.get('registry_from')
                                                     else f"registry '{r.get('registry')}'")
                       + (' where ' + ', '.join(f"{k} is {v}" for k, v in r['where'].items()) if r.get('where') else ''))
        for a_, r in dmform.facet(F, 'default_from'):
            det.append(f"{_w}.{a_}, when the entry is silent, is read from {r.get('registry')}.{r.get('take')} "
                       f"(the row its `{r.get('keyed_by')}` names)")
        for a_, r in dmform.facet(F, 'system_from'):
            det.append(f"{_w}.{a_} is written in the one form its `{r.get('keyed_by')}` declares ({r.get('registry')})")
        for a_, r in dmform.facet(F, 'pattern'):
            det.append(f"{_w}.{a_} matches {r}")
        for a_, r in dmform.facet(F, 'soft'):
            det.append(f"{_w}.{a_} SHOULD match {r.get('pattern')} (a warning)")
        for a_, _r in dmform.facet(F, 'ref'):
            det.append(f"{_w}.{a_} is a ref — resolved")
        for a_, _r in dmform.facet(F, 'pointer'):
            det.append(f"{_w}.{a_} is a pointer — resolved")
        for a_, _r in dmform.facet(F, 'extent'):
            det.append(f"{_w}.{a_} is an extent")
        for a_, _r in dmform.facet(F, 'recurrence'):
            det.append(f"{_w}.{a_} is a recurrence")
        for a_, q in dmform.facet(F, 'quantity'):
            det.append(f"{_w}.{a_} is a measured value {{count, unit}} of {q}: " + quantity_rule(q))
        for a_, r in dmform.facet(F, 'key_of'):
            det.append(f"{_w}.{a_} is a key of `{r}` on this bean, or `<bean>:<key>` on another — resolved")
        for a_, r in dmform.facet(F, 'bean_id'):
            det.append(f"{_w}.{a_} is the id of a bean this garden holds"
                       + (f", of genos {' or '.join(map(str, r['gene']))}" if isinstance(r, dict) and r.get('gene') else ''))
        _keyed = dict(dmform.facet(F, 'keyed_by'))
        for a_, r in dmform.facet(F, 'entries'):
            det.append(f"{_w}.{a_} holds entries, each judged by {sorted(map(str, r))}"
                       + (f"; ONE per `{_keyed[a_]}`, in no order" if a_ in _keyed else ''))
        if isinstance(s.get('sums'), dict):
            _wh = s['sums'].get('whole')
            det.append(f"sums: each entry's {s['sums'].get('parts')} add up EXACTLY to its "
                       f"{' or '.join(_wh) if isinstance(_wh, list) else _wh} (the first it states), in the whole's unit")
        _typed = {'values', 'registry', 'aspect', 'type', 'system_from', 'pattern', 'soft', 'extent', 'ref', 'pointer'}
        _raw = (s.get('attrs') or {})
        _untyped = [a_ for a_, r in _raw.items() if isinstance(r, dict) and r.get('in') == 'untyped']
        if _untyped:                     det.append(f"UNTYPED — no domain declared yet: {_untyped}")
        if F['cells']:                   det.append(f"{len(F['cells'])} cell(s): combinations an entry may not, or should not, hold")
        if F['one_of']:                  det.append(f"each entry has one of {F['one_of']}")
        if s.get('key_form'):            det.append(f"keys: {s['key_form']}")
        if F['mirror']['parity_with']:   det.append(f"same facets as '{F['mirror']['parity_with']}'")
        if F['mirror']['inverse_of']:    det.append(f"inverse of '{F['mirror']['inverse_of']}' — held consistent")
        if F['matches']['equal_genos_attr']: det.append(f"must equal genos.{F['matches']['equal_genos_attr']}")
        if s.get('required_on_targets_of'): det.append(f"required on targets of '{s['required_on_targets_of']}'")
        if V.get('governs_anchor'):
            det.append(f"anchor '{V['governs_anchor']}' must be in canonical form: "
                       f"{V.get('canonical_note') or V.get('form')}")
        if F['matches']['form_from_genos']: det.append(f"form pinned by genos.{F['matches']['form_from_genos']}")
        for _an, x in dmform.facet(F, 'aspect', 'entry'):
            det.append(f"entry.{_an} is a position on aspect '{x['aspect']}'"
                       f" (default {x.get('default')})")
        for d in det:
            print(f"      · {d}")

head("QUANTITIES — a measured value is { count, unit }, and the unit measures the quantity")
_vt = {r.get('type'): r for r in reg('value_types') if isinstance(r.get('type'), str)}
print(f"  count: {_m(_vt.get('count')).get('pattern', 'NO value_types[count] — the gate refuses every count')} "
      f"— never a float; a decimal is written as a string")
for q in reg('quantities'):
    if isinstance(q, dict) and q.get('quantity'):
        print(f"  {q['quantity']:14} {quantity_rule(q['quantity'])}")

head("TEXT AND DAYS — what every key and string is, and which positions are days")
_tx = _m(_vt.get('text'))
if _tx.get('holds_no'):
    print(f"  text: every key and string value of a bean, a mapping, GARDEN.md and VOCAB.md holds no character of Unicode "
          f"category {_tx['holds_no']} but {', '.join(repr(c) for c in _seq(_tx.get('but'))) or 'none'}, and a line feed "
          f"only in a {_tx.get('lines_in')} scalar (`|` or `>`) — the character is named, never echoed")
else:
    print("  text: NO value_types[text] — the gate reports the missing row")
_ex = _seq(_m(_m(_vt.get('date')).get('exists')).get('reckoning'))
_rows = [r for r in reg('anchor_systems') if r.get('calendar')]
print(f"  a day: a position held to a day — a date, where a repetition starts and ends, a bound in time — is a day its "
      f"calendar has. In a calendar reckoned {' or '.join(map(str, _ex)) or '(none named)'} the day it names, written back, "
      f"is the position written, and a year the reckoning cannot reach is refused; judged: "
      f"{', '.join(str(r.get('system')) for r in _rows if r.get('reckoning') in _ex) or 'none'}")
_not = [f"{r.get('system')} ({r.get('reckoning')})" for r in _rows if r.get('reckoning') not in _ex]
if _not:
    print(f"         not judged by arithmetic, as their reckoning says: {', '.join(_not)}")

head("MANIFEST — GARDEN.md, judged as itself")
_mf = std.get('manifest') or {}
for a_, r in (_mf.get('attrs') or {}).items():
    r = r if isinstance(r, dict) else {}
    print(f"  {a_:15} {'REQUIRED · ' if r.get('required') else ''}in: {r.get('in')}")
print("  any other key is refused; a retired one says where it went (below). Once the garden holds a bean it names its "
      "gardener")

head("RETIRED — names the law took back, and where each went")
for r in std.get('retired') or []:
    if isinstance(r, dict):
        print(f"  {str(r.get('name')):24} (on {r.get('at')}) → {r.get('instead')}")

head("PROVENANCE RECORD — on a bean, an anchor or an entry")
_pr = std.get('provenance_record') or {}
print(f"  a record carries only {_pr.get('attrs')}; each record in `from` only {_pr.get('from_attrs')}, with a `src`")
print("  `garden` names another garden this one knows (a `garden` bean's garden_id); a record made here carries none (warned)")

head("REVERSE GATE — the rules must be passed by the objects")
print("  every position a term declares — a closed list on an entry's attribute or on a mapping's own, an aspect, a "
      "registry's rows, an entry form — must be OCCUPIED by a bean, or declared vacant with a reason")
print(f"  reasons: {' | '.join(std.get('vacancy_reasons') or ['NONE DECLARED — the gate refuses'])}"
      f" ; a vacancy also needs a `why`")
print("  a garden accounts only for positions IT declared — Tier-0 accounts for its own")
print("  a local vacancy that becomes occupied is an ERROR; a Tier-0 one WARNS")
for tier, vs in (('tier0', (std.get('vacancies') or []) + prof_vacs),
                 ('garden', loc.get('vacancies') or [])):
    for v in vs:
        print(f"    [{tier}] {v.get('at')} = '{v.get('position')}'  ({v.get('reason')})")

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
                 "a `file:` pointer must resolve to a file that exists in this garden",
                 "a bean, a mapping, GARDEN.md and VOCAB.md are UTF-8 — any other encoding is refused by name",
                 "every entry of VOCAB.md is in its own shape: a term's or a genos's name is text, a schema, its attrs and "
                 "a merge are mappings, context_keys a list of text, a cell says one verdict (incoherent | in_breach), "
                 "requirement or expectation, a vacancy's reason and why are text, and every pattern it writes is a "
                 "regular expression; one of another shape is refused and left unread (listed under NOT READ)",
                 "a conflict record stands the rules down only as the merge driver captured it: `merge_open: true`, its "
                 "path in `merge_conflicts`, `{conflict: [...]}` alone with two or more different values — any other "
                 "is refused at its path"]:
        print(f"  · {line}")

if NOT_READ:
    head("NOT READ — what the gate refuses in this garden's VOCAB.md, and so enforces no rule of")
    for line in NOT_READ:
        print(f"  · {line}")
