#!/usr/bin/env python3
"""daftar write-gate validator.

Session/model-agnostic gate, in two halves (v2 P2 / plan D4):

  CORE        the bean GRAMMAR, which is not a per-term rule and so stays in code: front-matter shape,
              id == filename, kebab ids, required keys, provenance shape, the identity capsule +
              establishing-anchor dedup, vocab-driven ip dedup, the std-vocab `extends:` pin, link
              integrity over the generic ref sections, the acyclic check, journal<->commit binding.

  INTERPRETER ONE generic loop that enforces every vocabulary term from its `schema:` block. There are
              NO per-term blocks here. A type rule is changed by editing VOCAB.md — a human-ratified
              rule-change — never by editing this file. Terms are read from BOTH tiers (the skill's
              std-vocab and the garden's VOCAB); a term with no `schema:` is documentation only.
              The schema language is documented in VOCAB.md under `schema_language:`.

Run manually and via the git pre-commit hook. 0=clean 1=errors 2=setup.
"""
import glob, os, re, sys, fnmatch, ipaddress, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmsafe          # the staged-state checks below run dmsafe's OWN comparison, not a copy of it
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def _product():
    """`daftar v<tag>` — DERIVED from git, because the version lives in an annotated tag and nowhere else.
    Every version this repo ever typed into prose rotted (four titles reading v1.0 over v2 bodies, two
    stale pins); the two that stayed correct were derived. A tag has no second copy to disagree with.

    IN A GARDEN, the garden's own name and the release it adopted: `GARDEN.md` names both (`garden:` and
    `daftar_release:`, written by germinate.sh and dmupgrade.py). A garden's git history carries no daftar
    tags, so describing it printed "daftar (untagged)" on every garden anyone grew."""
    _g = load(os.path.join(ROOT, 'GARDEN.md'))[0] if os.path.isfile(os.path.join(ROOT, 'GARDEN.md')) else None
    if isinstance(_g, dict) and _g.get('garden') and _g.get('daftar_release'):
        return f"{_g['garden']} (daftar {_g['daftar_release']})"
    try:
        v = subprocess.run(['git', '-C', ROOT, 'describe', '--tags', '--always', '--dirty'],
                           capture_output=True, text=True, timeout=5).stdout.strip()
        return f"daftar {v}" if v else "daftar (untagged)"
    except Exception:
        return "daftar (untagged)"

# The sections a bean states its OWN facts in. Three checks ask this same question — the float scan, the
# IP collector and the single-owner duplicate scan — and each used to carry its own copy of the answer.
# `section_keys()` further down deliberately does NOT use this: it asks a different question.
_AUTHORITATIVE = ('owns', 'attributes', 'details')
# P4: `refs`, `depends_on` and `consumes` used to be hardcoded here. They are declared vocabulary terms
# now, so the gate no longer names a single relation — every edge it resolves comes from a schema.
errors, warns = [], []
LANGUAGE_PATTERNS = []

# ---- THE STATE THE PLIES SHARE, AND THE ONLY STATE THEY SHARE -------------------------------------
# Each name below is PUBLISHED by exactly one ply and READ by later ones; `PLIES` at the foot of the
# file states that dependency in the same order and says why each ply cannot move earlier.
#
#   docs, bean_ids, map_ids           <- build_docs
#   est_owner                         <- check_identity_capsule
#   ALL_FM, TARGETS_OF                <- build_all_fm_and_targets
#   VACANCY_REASONS                   <- check_vacancy_reasons_declared
#   DAG_TERMS, dep_graph              <- check_link_integrity
#   DOCUMENTISH, LAW_DOCS, FRONT_MATTER_DOCS
#                                     <- build_staged_constants
#
# They are deliberately NOT pre-bound to empty defaults: a ply that runs out of order must raise
# NameError rather than quietly judge an empty corpus and print `0 error(s)`, which is the same
# refusal-over-silence rule `law_carrier` and the no-index check already make. Everything ELSE a ply
# computes is its own local. These functions were carved out of top-level script code and the carve
# left every loop variable behind as a module global — 109 names, none with a second reader, any one
# of which could have been read across plies with nothing saying so.


def _row(reg, key):
    """A registry lookup keyed by BEAN DATA, which after a semantic merge may be a conflict record.

    `{'conflict': [...]}` is unhashable, and handing it to a dict lookup killed the gate outright —
    no verdict, none of the accumulated errors printed, and, because the pre-commit hook runs this
    file, no way to commit the edit that would resolve the merge. The gate stopped being a gate and
    became a wall. A non-scalar can never match a registry row, so it resolves to None and lands in
    the branch that already exists for a value the vocabulary does not declare.
    """
    return reg.get(key) if isinstance(key, (str, int, bool)) else None


def _is_conflict(v):
    return isinstance(v, dict) and isinstance(v.get('conflict'), list)


def _captured(fm, key):
    """True when `key` holds a conflict the merge driver DECLARED with `merge_open: true`.

    MERGE.md §10 makes a captured conflict committable — lossless capture first, human choice after —
    so the per-term rules stand down on a value nobody has chosen yet, and the single unclean warning
    speaks for the bean. Only a DECLARED capture earns this. A conflict record with no marker is an
    undeclared merge and is an error, raised where the unclean report is built.
    """
    return bool(fm.get('merge_open')) and _is_conflict(fm.get(key))


def load(f):
    # line-anchored fences (bin/dmparse.py) — a `---`/`----` inside a value or the body never truncates
    head, body = dmparse.read(f)
    if head is None:
        return None, ''
    try:
        return dmparse.loads(head), body
    except Exception as e:
        return {'__err__': str(e)}, ''


# ============================== VOCABULARY ==============================
# THE LAW HAS ONE PATH AND NO FALLBACK. A gate that cannot find the vocabulary must refuse, not quietly
# load a different copy: falling back substitutes a different law, which is worse than failing. This is
# not hypothetical — the fallback resolved to a sibling clone pinned two majors behind.
STD = os.path.join(ROOT, 'seed', 'std-vocab.md')
std_ver, ip_patterns = None, []
std_fm = {}
if os.path.exists(STD):
    std_fm = load(STD)[0] or {}
    std_ver = str(std_fm.get('version'))
    for t in std_fm.get('terms', []):
        if t.get('term') == 'ip':
            ip_patterns = t.get('context_keys', [])
else:
    errors.append(f"std-vocab not found at {STD} — the law has ONE path and there is no fallback")

vocab_fm = load(os.path.join(ROOT, 'VOCAB.md'))[0] or {}


_FILE_REGISTRIES = {}

def _registry_file(name):
    """Rows of a registry kept in a DATA FILE rather than in the law's prose (9.1). A classification of four
    hundred occupations is data the law POINTS at, not text it restates: `registry_files: [{registry, file,
    key}]` in the vocabulary names a tab-separated file (relative to the garden root), whose header row gives
    the columns. The file must exist — a registry the law declares and cannot find is an error, never an
    empty list, for the same reason the vocabulary itself has no fallback."""
    if name in _FILE_REGISTRIES:
        return _FILE_REGISTRIES[name]
    decl = next((r for r in (list(vocab_fm.get('registry_files') or []) + list(std_fm.get('registry_files') or []))
                 if isinstance(r, dict) and r.get('registry') == name), None)
    if decl is None:
        _FILE_REGISTRIES[name] = None
        return None
    path = os.path.join(ROOT, decl.get('file', ''))
    rows = []
    try:
        with open(path, encoding='utf-8') as fh:
            head = fh.readline().rstrip('\n').split('\t')
            for line in fh:
                if line.strip():
                    rows.append(dict(zip(head, line.rstrip('\n').split('\t'))))
    except OSError:
        errors.append(f"registry_files: registry '{name}' is declared at {decl.get('file')} and that file is missing "
                      f"— a declared registry is never read as empty")
    _FILE_REGISTRIES[name] = rows
    return rows

def registry(name):
    """A top-level registry, from the garden if it declares one, else from Tier-0 — plus any rows the garden
    ADDS under `registry_additions: {<name>: [...]}`. A registry may also live in a data file (`registry_files`, 9.1).

    Replacing a registry wholesale is still possible, and it is the wrong tool for adding one row: a garden
    that needed one operating system Tier-0 lacks had to copy the whole registry and then declare a vacancy
    for every row it had copied and did not use (found by the v0.3.1 cold-start drill). An addition names
    only what is new, so the garden accounts only for what it declared."""
    base = vocab_fm.get(name) if vocab_fm.get(name) is not None else (std_fm.get(name) or [])
    if not base:
        base = _registry_file(name) or []
    # An added row the base already has is NOT added twice: `check_local_additions` reports it by name, and a
    # doubled row would otherwise surface as a misleading "exported enum has drifted".
    def _dup(row):
        return isinstance(row, dict) and row and any(
            isinstance(b, dict) and b.get(next(iter(row))) == row[next(iter(row))] for b in base)
    return list(base) + [r for r in ((vocab_fm.get('registry_additions') or {}).get(name) or []) if not _dup(r)]

# TERMS: every vocabulary term from both tiers, garden-local last so a garden may refine a std term.
def _overlay(base, over):
    """Garden-local overlay on a Tier-0 term: local keys win, `schema` merges key-by-key.

    `schema.values_add: [...]` APPENDS to the Tier-0 enum instead of replacing it, so a garden adds one value
    without restating (and then having to account for) every value Tier-0 already offers."""
    out = dict(base)
    for k, v in over.items():
        if k == 'schema' and isinstance(v, dict) and isinstance(base.get('schema'), dict):
            out['schema'] = {**base['schema'], **v}
        else:
            out[k] = v
    _s = out.get('schema')
    if isinstance(_s, dict) and _s.get('values_add'):
        _s['values'] = list(_s.get('values') or []) + [x for x in _s['values_add'] if x not in (_s.get('values') or [])]
    return out

# PROFILES (2.0/E4): Tier-0 terms a garden must OPT IN to. A garden that manages no code should not
# inherit code terms — and their vacancies come with them, so opting in never imports unexplained debt.
PROFILE_TERMS, PROFILE_VAC = [], []
for _pname in (vocab_fm.get('extends_profiles') or []):
    _prof = (std_fm.get('profiles') or {}).get(_pname)
    if _prof is None:
        errors.append(f"VOCAB extends_profiles: '{_pname}' is not a profile std-vocab@{std_ver} offers")
        continue
    PROFILE_TERMS += (_prof.get('terms') or [])
    PROFILE_VAC += (_prof.get('vacancies') or [])

TERMS, TIER0_TERMS = {}, set()
for t in (std_fm.get('terms') or []) + PROFILE_TERMS:
    if isinstance(t, dict) and t.get('term'):
        TERMS[t['term']] = t
        TIER0_TERMS.add(t['term'])
for t in (vocab_fm.get('local_terms') or []):
    if isinstance(t, dict) and t.get('term'):
        TERMS[t['term']] = _overlay(TERMS[t['term']], t) if t['term'] in TERMS else t
SCHEMAS = {n: t['schema'] for n, t in TERMS.items() if isinstance(t.get('schema'), dict)}

# KINDS registry: what each kind IS, including the nature it refines (P3/D1 `of_nature`).
KINDS = {}
for k in (std_fm.get('kinds') or []) + (registry('local_kinds') or []):
    if isinstance(k, dict) and k.get('kind'):
        KINDS[k['kind']] = k
# IDENTITY POLICY: which bean axis selects an identity/anchor policy row, and from which registry.
# Declared in VOCAB (`identity_policy`) so the gate names neither the axis nor the registry (P3/D1).
IDP = vocab_fm.get('identity_policy') or std_fm.get('identity_policy') or {}
_axis, _reg = IDP.get('keyed_by'), IDP.get('registry')
POLICY = {}
if _axis and _reg:
    POLICY = {r[_axis]: r for r in (registry(_reg) or [])
              if isinstance(r, dict) and r.get(_axis)}


def term_values(name):
    """The enum a term exports (for values_from / key_form: values_from:<term>)."""
    return list((SCHEMAS.get(name) or {}).get('values') or [])


def allowed_values(sch):
    if sch.get('values_from'):
        return term_values(sch['values_from'])
    return list(sch.get('values') or [])


# --- vocab self-consistency: an exported enum must not drift from its own definition -------------
# Declared by the term itself (`schema.values_consistent_with: [<path>...]`), so this names no term.
# A path is either `attr` (a list) or `attr[].sub` (a list of mappings, take each `sub`).
def collect_path(node, path):
    if path.startswith('registry:'):          # a top-level registry (either tier) rather than a path inside the term
        path = path[len('registry:'):]
        head0 = path.split('[].')[0]
        node = {head0: registry(head0)}
    head, _, sub = path.partition('[].')
    seq = node.get(head) or []
    if not sub:
        return [v for v in seq if not isinstance(v, (dict, list))]
    return [i.get(sub) for i in seq if isinstance(i, dict) and i.get(sub) is not None]

def check_vocab_enum_drift():
    for _name, _term in TERMS.items():
        _paths = (_term.get('schema') or {}).get('values_consistent_with')
        if not _paths:
            continue
        want = [v for p in _paths for v in collect_path(_term, p)]
        have = term_values(_name)
        if sorted(want) != sorted(have):
            errors.append(f"VOCAB {_name}: schema.values {sorted(have)} != {' + '.join(_paths)} {sorted(want)} "
                          f"— the exported enum has drifted from its definition")


# --- the schema language must describe itself (std-vocab 11.3) -----------------------------------------------------
# The reverse gate holds every TERM to its occupants; nothing held the schema language to the gate. Measured
# 2026-09-20: four constructs were interpreted here and declared nowhere (`path`, `alt_form`, `attr_types`,
# `canonical_note`) — a cold-start drill found one of them by reading this file, which is not where a stranger
# should have to look. The other direction is the dangerous one: a key the language does not declare is a key no
# controller reads, so `entry_require_attrs` (one letter short) has always passed while enforcing nothing.
# AN ERROR since 12.0 (it was a warning for one release, 11.3, so that release could stay minor). The operator's
# ruling, 2026-09-20: a rule that silently enforces nothing is worse than a refusal, because the vocabulary SAYS it
# is in force. The same choice he made for an undeclared top-level key on a bean, one level up.
def check_schema_language():
    _declared = set(std_fm.get('schema_language') or {})
    if not _declared:
        return                      # the law did not load; the one-path refusal says so, once
    for _name, _sch in sorted(SCHEMAS.items()):
        for _k in sorted(set(_sch) - _declared):
            errors.append(f"VOCAB {_name}: schema key `{_k}` is not declared in schema_language — no controller "
                         f"reads an undeclared construct, so this rule enforces NOTHING. Check the spelling "
                         f"against `schema_language` in seed/std-vocab.md")


# --- a garden's local ADDITION that the standard now carries itself (v0.5.0) --------------------------------------
# The contribution path is: prove a value locally with values_add / registry_additions, propose it, and it lands in
# Tier-0. The garden that proved it then carried a duplicate, and the gate said only "the exported enum has drifted"
# (found by the second cold-start drill). This names the actual situation and the one-line fix.
def check_local_additions():
    _tier0 = {t['term']: (t.get('schema') or {}) for t in (std_fm.get('terms') or []) + PROFILE_TERMS
              if isinstance(t, dict) and t.get('term')}
    for _t in (vocab_fm.get('local_terms') or []):
        if not isinstance(_t, dict):
            continue
        for _v in ((_t.get('schema') or {}).get('values_add') or []):
            if _v in ((_tier0.get(_t.get('term')) or {}).get('values') or []):
                errors.append(f"VOCAB {_t.get('term')}: '{_v}' is in values_add, but std-vocab@{std_ver} already offers it — "
                              f"remove it from values_add in VOCAB.md (and its row from registry_additions, if any)")
    for _name, _rows in ((vocab_fm.get('registry_additions') or {}).items()):
        _base = std_fm.get(_name) or []
        for _row in (_rows or []):
            if not isinstance(_row, dict) or not _row:
                continue
            _k = next(iter(_row))
            if any(isinstance(_b, dict) and _b.get(_k) == _row[_k] for _b in _base):
                errors.append(f"VOCAB registry_additions.{_name}: the row {_k}={_row[_k]!r} is already in std-vocab@{std_ver} — "
                              f"remove it from registry_additions in VOCAB.md")


# --- a list's merge identity must name fields its entries actually carry (std-vocab@8.0) -----------------
# `merge.order: by-<field>[+<field>...]` is how dmmerge matches the members of a list across gardens. Three
# terms declared `by-key` over entries that have no `key`, and the merge silently matched each member by its
# whole content instead. Nothing could see it: the declaration was well-formed and no bean was wrong. Read
# from the declarations, so this names no term; the ref attrs are CORE (every self-ref entry is one).
REF_ATTRS = {'bean', 'mapping', 'field'}

def check_merge_identity():
    for _name, _term in TERMS.items():
        _m, _s = _term.get('merge') or {}, _term.get('schema') or {}
        if not isinstance(_m, dict) or _m.get('cardinality') != 'multi' or _s.get('shape') != 'list_of_entries':
            continue
        _ident = dmparse.identity_fields(_m.get('order'))
        if not _ident:
            errors.append(f"VOCAB {_name}: a list of entries merged member by member needs `order: by-<field>"
                          f"[+<field>...]`, not '{_m.get('order')}' — without one, members are matched by content")
            continue
        _required = set(_s.get('entry_required_attrs') or [])
        _declared = (_required | set(_term.get('entry_attrs') or {})
                     | {a for r in (_s.get('entry_required_if') or []) for a in (r.get('requires') or [])}
                     | (REF_ATTRS if 'self' in (_s.get('entry_ref_fields') or []) else set()))
        for _f, _may_lack in _ident:
            if _f not in _declared:
                errors.append(f"VOCAB {_name}: merge identity '{_m['order']}' names '{_f}', which no entry of this "
                              f"term declares")
            elif _may_lack and _f in _required:
                errors.append(f"VOCAB {_name}: merge identity marks '{_f}?' as possibly absent, but every entry "
                              f"must carry it — the `?` claims an absence the schema forbids")
            elif not _may_lack and _f not in _required:
                errors.append(f"VOCAB {_name}: merge identity '{_m['order']}' needs '{_f}' on every entry, but the "
                              f"schema does not require it — require it, or write '{_f}?' if its absence is a "
                              f"legitimate state")


# --- ASPECT SANITY RULES (2.1). An aspect is a CLOSED figure: its positions must exhaust it, each must
# know its complement, the complements must be mutual, and its poles must be a genuine contradictory pair.
# A figure with a loose end cannot say what a being is NOT, which is half of what a classification is for.
# VALUE TYPES (10.0): the patterns `entry_types` / `attr_types` name are rows of the law, not constants here.
VALUE_TYPES = {t['type']: t for t in (registry('value_types') or []) if isinstance(t, dict) and t.get('type')}
# No copy of a pattern lives here. Without the row, check_value_types reports the missing law ONCE, and the
# per-value checks stand down rather than refuse every id in the garden for a cause they cannot name.
KEBAB = re.compile(VALUE_TYPES['kebab']['pattern']) if 'kebab' in VALUE_TYPES else None

def check_law_extents():
    """Extents written in the VOCABULARY, not on a bean — today, `expiry.notice`.

    A LAW THE GATE CANNOT SEE IS THE DEFECT THIS REPOSITORY KEEPS FINDING. `notice` is a region like any
    other, and if nothing checked it a term could declare a notice period in a unit that does not exist
    and no run would ever say so — the rule would be in force and unenforced, which is exactly what
    v0.14.0 and v0.15.0 were each spent undoing. It costs one function to judge the law by its own rule.
    """
    for _name, _term in (TERMS or {}).items():
        _n = ((_term or {}).get('schema') or {}).get('expiry') or {}
        if isinstance(_n, dict) and _n.get('notice') is not None:
            check_extent(f"VOCAB {_name}.schema.expiry.notice", _n['notice'])


def check_value_types():
    for _t in ('iso_date', 'kebab'):
        if _t not in VALUE_TYPES:
            errors.append(f"VOCAB: no `value_types` row for '{_t}' — the gate reads its type patterns from the law "
                          f"and has no copy of its own")
# `journal` is one mapping, not a registry of rows, so it is read as the garden states it, else as the standard does.
JOURNAL = (vocab_fm.get('journal') if isinstance(vocab_fm.get('journal'), dict) else None) or \
          (std_fm.get('journal') if isinstance(std_fm.get('journal'), dict) else {})

def check_value_type(where, attr, val, typ):
    """A value against a declared value type. An undeclared type is itself an error: a schema naming a type
    the law does not define would otherwise check nothing and look as if it did."""
    t = VALUE_TYPES.get(typ)
    if not t and not VALUE_TYPES:
        return                      # the law itself is missing; check_value_types has said so once
    if not t:
        errors.append(f"{where}.{attr}: type '{typ}' is not declared in `value_types` {sorted(VALUE_TYPES)}")
    elif not re.match(t['pattern'], str(val)):
        errors.append(f"{where}.{attr}" + ("" if typ != 'kebab' else f" '{val}'") + f" {t.get('refusal') or 'does not match its type ' + typ}")

ASPECTS = {a['aspect']: a for a in (registry('aspects') or []) if isinstance(a, dict) and a.get('aspect')}
FIGURES = {f['figure']: f for f in (registry('figures') or []) if isinstance(f, dict) and f.get('figure')}

UNITS = {u['unit']: u for u in (registry('units') or []) if isinstance(u, dict) and u.get('unit')}
SYSTEMS = {s['system']: s for s in (registry('anchor_systems') or []) if isinstance(s, dict) and s.get('system')}


def check_extent(where, node):
    """One EXTENT against the aspect it names (11.2). Returns nothing; appends what is wrong.

    Every rule here is read from the aspect and its figure rather than written down: whether a region is
    possible at all (`figures[].extent`), whether it may carry a length (`aspects[].metered`), which unit
    that length is in (the metered dimension), and which forms a boundary may take (`aspects[].domain`,
    then the anchor system's own pattern). So a new aspect gets extents with no change here, and an
    aspect that should not have them refuses them for its own stated reason.
    """
    if not isinstance(node, dict):
        errors.append(f"{where}: an extent is a mapping {{of, from?, to?, measure?}} (`extent_form`)")
        return
    an = node.get('of')
    asp = ASPECTS.get(an)
    if not asp:
        errors.append(f"{where}: extent `of: {an!r}` names no aspect — {sorted(ASPECTS)}")
        return
    fig = FIGURES.get(asp.get('figure')) or {}
    if fig.get('extent') != 'possible':
        errors.append(f"{where}: aspect '{an}' is a {asp.get('figure')} and carries no region — "
                      f"{fig.get('extent_why') or 'its figure declares extent: ' + str(fig.get('extent'))}")
        return
    if not any(node.get(k) is not None for k in ('from', 'to', 'measure')):
        errors.append(f"{where}: an extent needs at least one of from / to / measure — "
                      f"a region with neither bound and no length is not a region (`extent_form.requires`)")
    m = node.get('measure')
    if m is not None:
        metered = asp.get('metered')
        if not metered or metered == 'none':
            errors.append(f"{where}: aspect '{an}' declares `metered: {metered}`, so a region on it has no "
                          f"length — drop `measure`, or bound it with from/to")
        elif not isinstance(m, dict) or m.get('count') is None or not m.get('unit'):
            errors.append(f"{where}.measure: must be {{count, unit}}")
        else:
            u = UNITS.get(str(m['unit']))
            if not u:
                errors.append(f"{where}.measure.unit '{m['unit']}' is not in the `units` registry "
                              f"{sorted(UNITS)}")
            elif u.get('dimension') != metered:
                errors.append(f"{where}.measure.unit '{m['unit']}' measures {u.get('dimension')}, but "
                              f"aspect '{an}' meters {metered}")
            if not isinstance(m.get('count'), int) or isinstance(m.get('count'), bool) or m['count'] <= 0:
                errors.append(f"{where}.measure.count must be a positive whole number of "
                              f"{m.get('unit')}s, not {m.get('count')!r}")
    # A BOUNDARY IS A POSITION, and which forms it may take is the aspect's domain, not this function's.
    dim = ((asp.get('domain') or {}).get('systems'))
    for side in ('from', 'to'):
        v = node.get(side)
        if v is None:
            continue
        ok = [s for s in SYSTEMS.values()
              if s.get('dimension') in (dim, 'any') and re.match(s.get('pattern') or '(?!)', str(v))]
        if not ok:
            errors.append(f"{where}.{side} '{v}' is not a position in any system of dimension "
                          f"'{dim}' — " + ', '.join(sorted(s['system'] for s in SYSTEMS.values()
                                                           if s.get('dimension') in (dim, 'any'))))


def ctl_extents(c):
    """`attr_extents:` — attrs of the mapping that hold a region of some aspect's domain."""
    for attr, _ in _facet(attribute_form(c.term, c.sch), 'extent') if attribute_form(c.term, c.sch)['scope'] == 'self' else []:
        v = c.node.get(attr) if isinstance(c.node, dict) else None
        if v is not None:
            check_extent(f"{c.base}: {c.term}.{attr}", v)
    return None


def walk_keys():
    """{schema key: aspect} for every SEQUENCE aspect that places terms on itself through a schema key (9.2).
    `dag: true` is read through this: the key is data in the vocabulary, and whether a cycle is refused is
    the aspect's `acyclic` restriction, not a rule written here."""
    return {a['term_key']: a for a in ASPECTS.values() if a.get('term_key')}

def on_walk(sch, acyclic_only=False):
    """True when a term's schema places its edges on a walk aspect (and, if asked, one declared acyclic)."""
    return any(sch.get(k) is True and (not acyclic_only or a.get('acyclic') is True) for k, a in walk_keys().items())

def check_sequence_figure(_an, _a, _fig):
    """A SEQUENCE is declared only by its restrictions (9.2): every one stated, each a value the figure
    offers. It has no positions and no poles, because it is not a closed set of modalities."""
    for _k in ('positions', 'poles'):
        if _a.get(_k):
            errors.append(f"aspect '{_an}': a sequence declares no `{_k}` — its positions are points in a domain, "
                          f"not a closed set of modalities")
    _lines = _a.get('lines')
    if not (_lines == 'open' or (isinstance(_lines, int) and not isinstance(_lines, bool) and _lines > 0)):
        errors.append(f"aspect '{_an}': lines '{_lines}' must be a positive integer or `open`")
    _dims = {u.get('dimension') for u in (registry('units') or []) if isinstance(u, dict)}
    if _a.get('metered') != 'none' and _a.get('metered') not in _dims:
        errors.append(f"aspect '{_an}': metered '{_a.get('metered')}' is neither `none` nor a dimension in `units` {sorted(d for d in _dims if d)}")
    if _a.get('order') not in (_fig.get('order_values') or []):
        errors.append(f"aspect '{_an}': order '{_a.get('order')}' is not one of {_fig.get('order_values')}")
    if not isinstance(_a.get('acyclic'), bool):
        errors.append(f"aspect '{_an}': acyclic must be true or false, stated")
    if _a.get('ends') not in (_fig.get('ends_values') or []):
        errors.append(f"aspect '{_an}': ends '{_a.get('ends')}' is not one of {_fig.get('ends_values')}")
    _sys = (_a.get('domain') or {}).get('systems') if isinstance(_a.get('domain'), dict) else None
    _sdims = {s.get('dimension') for s in (registry('anchor_systems') or []) if isinstance(s, dict)}
    if _sys != 'none' and _sys not in _sdims:
        errors.append(f"aspect '{_an}': domain.systems '{_sys}' is neither `none` nor a dimension of `anchor_systems` {sorted(d for d in _sdims if d)}")

def check_aspect_sanity():
    _keys = {}
    for _an, _a in ASPECTS.items():
        _fig = FIGURES.get(_a.get('figure'))
        if not _fig:
            errors.append(f"aspect '{_an}': figure '{_a.get('figure')}' is not declared in `figures` {sorted(FIGURES)}")
            continue
        for _req in _fig.get('requires') or []:
            if _a.get(_req) is None:
                errors.append(f"aspect '{_an}': a {_a['figure']} must state `{_req}` — an unstated restriction "
                              f"is how a model silently becomes narrower than the world")
        if _a.get('term_key'):
            if _a['term_key'] in _keys:
                errors.append(f"aspect '{_an}': term_key '{_a['term_key']}' is already claimed by aspect '{_keys[_a['term_key']]}'")
            _keys[_a['term_key']] = _an
        if _a['figure'] == 'sequence':
            check_sequence_figure(_an, _a, _fig)
            continue
        if _a['figure'] != 'opposition':
            errors.append(f"aspect '{_an}': the gate has no check for figure '{_a['figure']}' — a new figure is "
                          f"declared together with its checker, or its aspects would pass unexamined")
            continue
        _pos = {p['position']: p for p in (_a.get('positions') or []) if isinstance(p, dict) and p.get('position')}
        if not _pos:
            errors.append(f"aspect '{_an}': declares no positions — an aspect with no positions classifies nothing")
        for _pn, _p in _pos.items():
            _c = _p.get('complement')
            if not _c:
                errors.append(f"aspect '{_an}': position '{_pn}' names no complement — a position that cannot "
                              f"say what it is NOT leaves the figure open")
            elif _c not in _pos:
                errors.append(f"aspect '{_an}': position '{_pn}' complements '{_c}', which is not a position of "
                              f"this aspect (the figure does not close)")
            elif _pos[_c].get('complement') != _pn:
                errors.append(f"aspect '{_an}': '{_pn}' complements '{_c}' but '{_c}' complements "
                              f"'{_pos[_c].get('complement')}' — complements must be mutual")
        # ORIENTATION, dimension-agnostically. `poles` is ONE axis (a contradictory pair) or a LIST of axes.
        # The gate does not care HOW MANY: a figure may be 1-dimensional (a simple binary), 2 (a square), 3
        # (a cube) or more. What it requires is that EVERY declared axis is a genuine contradictory pair, so
        # that a position is addressable along it. The dimensionality is DERIVED from what is declared, never
        # assumed — assuming a count is what makes a square silently mis-model a cube.
        _raw = _a.get('poles') or []
        _axes = _raw if (_raw and isinstance(_raw[0], list)) else ([_raw] if _raw else [])
        if not _axes:
            errors.append(f"aspect '{_an}': declares no axis — without one, a position cannot be addressed "
                          f"by direction and the figure has no orientation")
        for _ax in _axes:
            if len(_ax) != 2:
                errors.append(f"aspect '{_an}': axis {_ax} must be a PAIR — an axis runs between two opposites, "
                              f"however many axes the figure has")
                continue
            for _p in _ax:
                if _p not in _pos:
                    errors.append(f"aspect '{_an}': pole '{_p}' is not one of its positions")
            if all(p in _pos for p in _ax) and _pos[_ax[0]].get('complement') != _ax[1]:
                errors.append(f"aspect '{_an}': axis {_ax} is not a contradictory pair — an orientation must "
                              f"run between opposites, or a position on the figure is ambiguous")



# --- extends pin (GARDEN.md / VOCAB.md) ---------------------------------------------------------
def check_extends_pin():
    for f in ('GARDEN.md', 'VOCAB.md'):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        ext = (load(p)[0] or {}).get('extends')
        if ext:
            m = re.match(r'std-vocab@(.+)', str(ext))
            if not m:
                errors.append(f"{f}: extends must be 'std-vocab@<version>'")
            elif std_ver and m.group(1) != std_ver:
                errors.append(f"{f}: pins std-vocab@{m.group(1)} but installed is @{std_ver} (bump is a logged rule-change)")
        elif f == 'VOCAB.md':
            warns.append("VOCAB.md: missing `extends: std-vocab@<ver>` pin")



# ============================== CORE — bean grammar ==============================
def _has_float(x):
    if isinstance(x, float): return True
    if isinstance(x, dict): return any(_has_float(v) for v in x.values())
    if isinstance(x, list): return any(_has_float(v) for v in x)
    return False


def build_docs():
    global docs, bean_ids, map_ids
    docs, bean_ids, map_ids = {}, set(), set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
             sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))):
        base = os.path.basename(f)[:-3]
        is_bean = os.sep + 'beans' + os.sep in f
        idkey = 'bean' if is_bean else 'mapping'
        fm, body = load(f)
        if not isinstance(fm, dict) or '__err__' in fm:
            errors.append(f"{base}: front-matter invalid ({(fm or {}).get('__err__', 'no --- fences')})")
            continue
        if str(fm.get(idkey)) != base:
            errors.append(f"{base}: {idkey} '{fm.get(idkey)}' must equal filename (quote if numeric/reserved)")
        if KEBAB and not KEBAB.match(base):
            errors.append(f"{base}: id must be kebab-case")
        req = ['bean', 'kind', 'title', 'status', 'summary'] if is_bean else ['mapping', 'kind', 'summary']
        for k in req:
            if not fm.get(k):
                (warns if k == 'summary' else errors).append(f"{base}: missing '{k}'")
        if is_bean and not body.strip():
            warns.append(f"{base}: no human body (Rule 6 paper-durable)")
        prov = fm.get('provenance')
        if is_bean and not isinstance(prov, dict):
            warns.append(f"{base}: missing provenance {{src,by,as_of}}")
        elif isinstance(prov, dict) and not prov.get('src'):
            errors.append(f"{base}: provenance.src missing")
        for sect in _AUTHORITATIVE:
            if _has_float(fm.get(sect)):
                warns.append(f"{base}: {sect} has a float — breaks canonical determinism; use an integer or {{value,unit}}")
        (bean_ids if is_bean else map_ids).add(base)
        docs[(is_bean, base)] = (fm, body)

# ---- every top-level key is declared, and no key is written twice (2026-09-17, human-ratified) ----------
# A key no vocabulary declares IS a vocabulary proposal — it says a new kind of fact exists — and it passed
# the gate unnoticed: `runs_on` sat on a session bean for six weeks beside the `refs.host` that already said
# the same thing. What counts as declared is read from the vocabulary, not listed here: a term's own name,
# and the top-level head of each literal `context_keys` entry (`id` declares `bean` and `mapping`;
# `identity.status` declares `identity`). A glob or a file path in context_keys locates values, not keys.
def declared_top_level_keys():
    out = set(TERMS)
    for _t in TERMS.values():
        for _ck in (_t.get('context_keys') or []):
            if isinstance(_ck, str) and '*' not in _ck and '/' not in _ck:
                out.add(_ck.split('.')[0].split('[')[0])
    return out

def check_undeclared_keys():
    if not std_fm:
        return      # no law loaded: the refusal is already stated, and judging every key against nothing buries it
    _declared = declared_top_level_keys()
    for (_is_bean, _base), (_fm, _body) in sorted(docs.items()):
        for _k in _fm:
            if _k not in _declared:
                errors.append(f"{_base}: top-level key '{_k}' is declared by no vocabulary term. A fact that fits "
                              f"no term belongs in details: or attributes: (ground rule 2); a new KIND of fact "
                              f"is a vocabulary proposal — park it in log/pending.md")

# YAML keeps the LAST of two equal keys and drops the first silently, so the loss happens before any check on
# the parsed document can see it. Read from the node graph instead — beans, mappings, and the law itself,
# where the first run of this check found two.
def check_duplicate_keys():
    _paths = (sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md')))
              + [STD, os.path.join(ROOT, 'VOCAB.md'), os.path.join(ROOT, 'GARDEN.md')])
    for _f in _paths:
        if not os.path.exists(_f):
            continue
        _head = dmparse.read(_f)[0]
        if not _head:
            continue
        try:
            _dups = dmparse.duplicate_keys(_head)
        except Exception:
            continue                          # unparseable: build_docs reports it, with the parser's reason
        for _path, _first, _again in _dups:
            errors.append(f"{os.path.relpath(_f, ROOT)}: key '{_path}' is written twice (lines {_first} and "
                          f"{_again}) — YAML keeps the second and silently discards the first")


def check_id_space_collision():
    for b in bean_ids & map_ids:
        errors.append(f"'{b}': same basename in beans/ AND mappings/ — ids unique per (space,base)")


# ---- identity capsule + establishing-anchor dedup ----
def check_identity_capsule():
    global est_owner
    est_owner = {}
    for (is_bean, base), (fm, body) in docs.items():
        if not is_bean:
            continue
        ident = fm.get('identity')
        if not isinstance(ident, dict):
            warns.append(f"{base}: no identity capsule (MERGE.md §4)")
            continue
        if not ident.get('status'):
            errors.append(f"{base}: identity.status missing")
        n_est = 0
        for a in (ident.get('anchors') or []):
            # D2/P4: the load-bearing distinction is `establishing` (establish vs corroborate), stated on the
            # anchor. `class` survives only as an optional hint at WHY it establishes — it no longer decides.
            if not isinstance(a, dict) or not all(k in a for k in ('key', 'value', 'establishing')):
                errors.append(f"{base}: each anchor needs key,value,establishing"); continue
            if not isinstance(a['establishing'], bool):
                errors.append(f"{base}: anchor '{a['key']}'.establishing must be true or false, not "
                              f"{a['establishing']!r} (VOCAB: establish vs corroborate is the load-bearing split)")
            # a vocabulary term that declares an anchor policy OVERRULES the bean: this is what keeps a
            # role anchor (one that migrates between objects) corroborating-only, whatever a bean claims.
            pol = (TERMS.get(a['key']) or {}).get('anchor')
            if isinstance(pol, dict) and 'establishing' in pol and a.get('establishing') != pol['establishing']:
                _dir = ("promote a corroborating anchor to establishing" if a.get('establishing')
                        else "demote an establishing anchor to corroborating")
                errors.append(f"{base}: anchor '{a['key']}'.establishing is {a.get('establishing')} but the "
                              f"vocabulary declares {pol['establishing']} for that term — a bean may not "
                              f"{_dir}; write establishing: {str(pol['establishing']).lower()} (VOCAB {a['key']}.anchor)")
            if a.get('establishing') is True:
                n_est += 1
                est_owner.setdefault((a['key'], compare_value(a['key'], a['value'])), []).append(base)
        # min-anchor policy attaches to the root axis, not the kind (P3/D1) — read it from the declared registry.
        pol = _row(POLICY, fm.get(_axis)) if _axis else None
        need = (pol or {}).get('min_establishing_anchors')
        if need and ident.get('status') == IDP.get('applies_at_identity_status') and n_est < need:
            warns.append(f"{base}: {_axis} '{fm.get(_axis)}' requires {need} establishing anchor(s) when "
                         f"'{ident.get('status')}' but has {n_est} (VOCAB {_reg}.min_establishing_anchors)")

# HOW AN ANCHOR IS COMPARED (std-vocab 9.0, human-ratified). A term that governs an anchor may declare
# `compare_form`; uniqueness is then judged on that form, so `SYN-0042` and `syn-0042 ` are one object. A
# cold-start drill committed exactly that typo duplicate with 0 errors. Read from the vocabulary; names no key.
COMPARE_FORMS = dmparse.COMPARE_FORMS      # one definition, shared with bin/dmmerge.py

def compare_value(key, value):
    return dmparse.compare_anchor(TERMS.values(), key, value)


def check_establishing_anchor_dedup():
    for (k, v), bs in sorted(est_owner.items()):
        bs = sorted(set(bs))       # one bean carrying two spellings of one anchor is not a duplicate of itself
        if len(bs) > 1:
            errors.append(f"establishing anchor {k}={v} on {bs} — same object in one garden. If they ARE one "
                          f"object, keep one bean and move the other's facts into it (MERGE.md); if they are "
                          f"two, one of the anchor values is wrong")



# ============================== THE INTERPRETER ==============================
# ONE loop, driven entirely by `schema:` blocks in the vocabulary. No term is named in this code.

def _aspects_of(sch):
    """A term may sit on ONE aspect or SEVERAL: `on_aspect` takes a mapping or a list of them."""
    a = sch.get('on_aspect')
    if isinstance(a, dict):
        a = [a]
    return [x for x in (a or []) if isinstance(x, dict) and x.get('aspect')]


def path_values(fm, path):
    """Scalar values at a dotted path; a `[]` suffix iterates a list (e.g. identity.anchors[].class)."""
    nodes = [fm]
    for part in path.split('.'):
        listy = part.endswith('[]')
        key = part[:-2] if listy else part
        nxt = []
        for n in nodes:
            if not isinstance(n, dict):
                continue
            v = n.get(key)
            if listy:
                if isinstance(v, list):
                    nxt.extend(v)
            elif v is not None:
                nxt.append(v)
        nodes = nxt
    return [n for n in nodes if not isinstance(n, (dict, list))]


def entries_of(shape, node):
    """Normalize a term's value into [(label, entry)] pairs for per-entry rules."""
    if shape == 'list_of_entries' and isinstance(node, list):
        return [(str(i), e) for i, e in enumerate(node)]
    if shape in ('open_map_of_entries', 'mapping') and isinstance(node, dict):
        return [(str(k), v) for k, v in node.items()]
    return []


# --- the per-ENTRY rules, one controller per declared entry key ---------------------------------------
# Same split as the term controllers, one level down: named after the schema key, never after a term.
# ============================== THE ATTRIBUTE FORM (S1 of the figure grammar) ==============================
# The schema language says one sentence in a dozen spellings: "this attribute is a position in that domain".
# `entry_values`, `entry_types`, `entry_in_registry`, `on_aspect`, `entry_pattern`… are each a map keyed by
# ATTRIBUTE, so one attribute's law is scattered across as many constructs as it has properties, and stated a
# second time, for people, in the term's `entry_attrs:`. This turns the matrix the other way IN MEMORY: one record
# per attribute, saying what it is a position in, whether it is required, and what it means. The interpreter below
# reads ONLY this form. The law's text is unchanged — that is step S2, and it may not start until this form has
# been shown to reproduce the old gate byte for byte (test/diffgate.py in a garden), because a form that cannot
# carry today's law exactly is not the law's form.
#
# FACETS, each the old construct it came from. `order` keeps each construct's own attribute order, so findings
# print in the order they always did: the normal form is keyed by attribute, the WALK is still facet by facet.
_ENTRY_FACETS = (('required', 'entry_required_attrs'), ('values', 'entry_values'), ('type', 'entry_types'),
                 ('pattern', 'entry_pattern'), ('soft', 'entry_soft_pattern'), ('registry', 'entry_in_registry'),
                 ('extent', 'entry_extents'), ('pointer', 'pointer_fields'), ('ref', 'entry_ref_fields'),
                 ('one_of', 'entry_one_of'))
_SELF_FACETS = (('required', 'required_attrs'), ('type', 'attr_types'), ('extent', 'attr_extents'),
                ('ref', 'ref_fields'))
_NORM = {}


def attribute_form(term, sch):
    """The term's law, keyed by attribute: {scope, attrs: {name: {facet: rule}}, order: {facet: [names]}, cells}."""
    if term in _NORM and _NORM[term][0] is sch:
        return _NORM[term][1]
    _t = TERMS.get(term) or {}
    _entry = any(sch.get(k) for _f, k in _ENTRY_FACETS if k != 'pointer_fields') or sch.get('on_aspect') \
        or sch.get('entry_pattern_from_registry') or sch.get('shape') in ('list_of_entries', 'open_map_of_entries')
    form = {'scope': 'entry' if _entry else 'self', 'attrs': {}, 'order': {}, 'cells': [], 'self_ref': False}

    def put(facet, name, rule):
        form['attrs'].setdefault(name, {})[facet] = rule
        form['order'].setdefault(facet, []).append(name)

    for facet, key in (_ENTRY_FACETS if _entry else _SELF_FACETS + (('pointer', 'pointer_fields'),)):
        _v = sch.get(key)
        for name in (_v if isinstance(_v, (list, dict)) else []):
            if name == 'self' and facet == 'ref':
                form['self_ref'] = True          # the MARKER "the value is itself a ref" — not an attribute
            else:
                put(facet, name, _v[name] if isinstance(_v, dict) else True)
    if not _entry and sch.get('ref_fields') and 'self' in sch['ref_fields']:
        form['self_ref'] = True
    for _a in _aspects_of(sch):
        put('aspect', _a.get('attr') or _a.get('aspect'), _a)
    _pfr = sch.get('entry_pattern_from_registry')
    if isinstance(_pfr, dict) and _pfr.get('attr'):
        put('system_from', _pfr['attr'], _pfr)
    for name, meaning in list((_t.get('entry_attrs') or {}).items()) + list((_t.get('attrs') or {}).items()):
        put('meaning', name, meaning)
    # CELLS: a combination of what an entry holds that may not stand (error) or should not (warning). Three old
    # constructs, one idea. `phase` only keeps each where it always ran, either side of `entry_one_of`.
    for _kind, _sev in (('incoherent', 'error'), ('in_breach', 'warn')):
        for _c in ((sch.get('cross_aspect') or {}).get(_kind) or []):
            form['cells'].append({'phase': 'cross', 'origin': _kind, 'severity': _sev, 'why': _c.get('why'),
                                  'when': {k: ('is', v) for k, v in _c.items() if k != 'why'}, 'lacks': []})
    for _r in (sch.get('entry_required_if') or []):
        form['cells'].append({'phase': 'cond', 'origin': 'required_if', 'severity': 'error', 'why': None,
                              'when': {_r.get('attr'): ('is', _r.get('equals'))},
                              'lacks': list(_r.get('requires') or [])})
    for _r in (sch.get('entry_expect_if') or []):
        form['cells'].append({'phase': 'cond', 'origin': 'expect_if', 'severity': 'warn', 'why': _r.get('why'),
                              'when': {_r.get('attr'): ('starts', _r.get('starts_with'))},
                              'lacks': [_r.get('expects')]})
    _NORM[term] = (sch, form)
    return form


def _facet(form, facet):
    """(attribute, rule) for every attribute carrying this facet, in the order the law stated them."""
    return [(n, form['attrs'][n][facet]) for n in form['order'].get(facet, [])]


# The cell carries `eff` — each aspect's EFFECTIVE position, stated or defaulted — because `on_aspect`
# and `cross_aspect` used to compute that separately from the same inputs. Two derivations of one fact
# can disagree about what a default means, and the one that disagrees silently is the dangerous one.
class _ECell:
    """One entry under inspection."""
    __slots__ = ('base', 'term', 'label', 'entry', 'sch', 'form', 'ref', 'eff')

    def __init__(self, base, term, label, entry, sch):
        self.base, self.term, self.label = base, term, label
        self.entry, self.sch = entry, sch
        self.form = attribute_form(term, sch)
        self.ref = f"{term}[{label}]"
        self.eff = {}                       # filled by ectl_on_aspect, read by ectl_cross_aspect


# --- STRUCTURE BEFORE PROSE: an entry carries only the attributes its term declares (std-vocab 12.0) ------------------
# A bean's top-level keys have been closed since 2026-09-17: a key no term declares is refused. One level down the
# door was still open, and what came through it was free text wearing a key's clothes — measured in one garden,
# forty attributes no term knew, among them `what_this_does_NOT_establish:` and `instrument_lesson:`, a sentence
# promoted to a field name so that it would look like data. Nothing can read such a key, merge it by identity, or
# ask every bean for it. The rule: an attribute is DECLARED by its term — typed by a schema construct, or described
# in the term's `entry_attrs:` / `attrs:` — or it is refused. Prose is not forbidden; it goes in an attribute the
# term declares FOR prose (`note`, `why`), where a reader knows to look. A term that declares no attribute at all
# (`owns`, `details`, `attributes`) is a free container by declaration and is left alone.
_REF_FORM = ('bean', 'mapping', 'field')


def declared_attrs(term, sch):
    """Every attribute the term declares — which, since S1, is simply every attribute in its attribute form."""
    _form = attribute_form(term, sch)
    out = set(_form['attrs'])
    if isinstance(sch.get('alt_form'), dict):
        out.add(sch['alt_form'].get('key'))
    if _form['self_ref'] and out:
        out |= set(_REF_FORM)               # the value IS a ref, so the link form's own keys belong to it
    if out:
        out.add('provenance')               # MODEL.md: "a fact whose source differs from the bean's default
                                            # carries its own record" — any entry may, so no term restates it
    return out, _form['self_ref']


def undeclared_attrs(base, term, where, node, sch):
    _decl, _self = declared_attrs(term, sch)
    if not _decl or not isinstance(node, dict):
        return                              # a free container, or a pure ref: nothing is declared to hold it to
    for _k in node:
        if _k not in _decl:
            errors.append(f"{base}: {where} carries `{_k}`, which the term `{term}` does not declare — an entry "
                          f"holds only declared attributes {sorted(_decl - set(_REF_FORM) - {'provenance'})}. Prose belongs in "
                          f"the attribute the term declares for it (`note`, `why`); a new kind of fact is "
                          f"proposed as a new attribute, not written as a new key")


def ectl_declared_attrs(e):
    undeclared_attrs(e.base, e.term, e.ref, e.entry, e.sch)


def ectl_entry_required_attrs(e):
    missing = [k for k, _ in _facet(e.form, 'required') if k not in e.entry]
    if missing:
        errors.append(f"{e.base}: {e.ref} missing {missing} "
                      f"(VOCAB {e.term}.schema.entry_required_attrs)")


UNKNOWN_VALUE_HINT = (" — if the value is real and the vocabulary lacks it, keep it under `attributes:` for now "
                      "and propose it, or add it for this garden with `schema: {values_add: [...]}` in a VOCAB.md "
                      "local_terms entry (see seed/COOKBOOK.md)")


def ectl_entry_values(e):
    for attr, allowed in _facet(e.form, 'values'):
        if e.entry.get(attr) is not None and e.entry[attr] not in allowed:
            errors.append(f"{e.base}: {e.ref}.{attr} '{e.entry[attr]}' not in {allowed} "
                          f"(VOCAB {e.term}.schema.entry_values)")


def ectl_entry_types(e):
    for attr, typ in _facet(e.form, 'type'):
        if e.entry.get(attr) is None:
            continue
        check_value_type(f"{e.base}: {e.ref}", attr, e.entry[attr], typ)


def ectl_entry_pattern(e):
    """`entry_pattern:` (11.0) — an entry attr must match a form the TERM owns (a position whose system owns
    its form uses `entry_pattern_from_registry` instead)."""
    for attr, pat in _facet(e.form, 'pattern'):
        v = e.entry.get(attr)
        if v is not None and not re.match(pat, str(v)):
            errors.append(f"{e.base}: {e.ref}.{attr} '{v}' is not in the form this term declares ({pat})")
    return None


def ectl_entry_soft_pattern(e):
    """`entry_soft_pattern:` (11.0) — the same as a WARNING: the form a value SHOULD take while a corpus is
    migrated onto it. A warning says what to fix; an error would refuse a garden's next commit for a value it
    has carried for months."""
    for attr, rule in _facet(e.form, 'soft'):
        vals = e.entry.get(attr)
        for v in (vals if isinstance(vals, list) else [vals]):
            if v is not None and not re.match(rule.get('pattern', ''), str(v)):
                warns.append(f"{e.base}: {e.ref}.{attr} '{v}' — {rule.get('why') or 'not in the form this term expects'}")
    return None


def ectl_entry_must_match(e):
    """An entry attr pinned to a registry row selected by a field on the bean (e.g. crown <- nature)."""
    for rule in (e.sch.get('entry_must_match') or []):
        val = e.entry.get(rule.get('attr'))
        if val is None:
            continue
        key = ALL_FM.get(e.base, {}).get(rule.get('keyed_by'))
        row = next((r for r in (registry(rule.get('registry')) or [])
                    if isinstance(r, dict) and r.get(rule.get('keyed_by')) == key), None)
        if row is None:
            errors.append(f"{e.base}: {e.ref}.{rule['attr']} cannot be checked — no {rule['registry']} "
                          f"row for {rule['keyed_by']} '{key}'")
        elif val != row.get(rule.get('take')):
            errors.append(f"{e.base}: {e.ref}.{rule['attr']} '{val}' does not match {rule['keyed_by']} "
                          f"'{key}', which routes to '{row.get(rule.get('take'))}' "
                          f"(VOCAB {e.term}.schema.entry_must_match)")


def ectl_entry_in_registry(e):
    """An entry attr whose value must be a row of a REGISTRY — so the registry is the enum's one owner.

    The alternative is restating the list in `entry_values`, which is a second copy that can disagree with
    the registry it was copied from. This is the argument `values_consistent_with` already makes for a
    term's own enum, applied one level down to an entry's.
    """
    for attr, rule in _facet(e.form, 'registry'):
        val = e.entry.get(attr)
        if val is None:
            continue
        # `registry_from: <attr>` (9.1): the registry is NAMED by another field of the same entry — a code is
        # checked against the scheme the entry says it is in, so one term serves every classification
        rname = str(e.entry.get(rule['registry_from'])) if rule.get('registry_from') else rule.get('registry')
        rows = registry(rname) or []
        allowed = [r.get(rule.get('take')) for r in rows if isinstance(r, dict)]
        if str(val) not in [str(a) for a in allowed]:
            if len(allowed) > 40:
                allowed = allowed[:12] + ['… %d more' % (len(allowed) - 12)]
            errors.append(f"{e.base}: {e.ref}.{attr} '{val}' is not a declared {rname} "
                          f"— known: {sorted(v for v in allowed if v)} "
                          f"(VOCAB {e.term}.schema.entry_in_registry)")


def ectl_entry_pattern_from_registry(e):
    """A position must be written in the ONE form its own system declares.

    The system owns its format and nothing else may spell a position its own way — the failure this
    prevents is already in the corpus: `staleness_key` carries four unowned spellings (`git-head:`,
    `git-commit:`, `digest:`, `manual:`), and one analysis acquired two verdicts because of it.

    NB `keyed_by` selects the registry row using a field of the ENTRY, where `entry_must_match` selects it
    using a field of the BEAN. The two rules ask different questions — which system is this position in,
    versus which row does this bean route to — and conflating them would make a position's form depend on
    the document that happens to carry it.

    A system with genuinely no canonical form declares `pattern: none`, and that DELIBERATE absence is
    honoured rather than treated as an unstated one — the same distinction `enforced_by: none` draws.
    """
    rule = next((r for _n, r in _facet(e.form, 'system_from')), None)
    if not rule:
        return
    val = e.entry.get(rule.get('attr'))
    if val is None:
        return
    key = e.entry.get(rule.get('keyed_by'))
    row = next((r for r in (registry(rule.get('registry')) or [])
                if isinstance(r, dict) and r.get(rule.get('keyed_by')) == key), None)
    if row is None:
        errors.append(f"{e.base}: {e.ref}.{rule['attr']} cannot be checked — no "
                      f"{rule['registry']} row for {rule['keyed_by']} '{key}'")
        return
    pat = row.get(rule.get('take'))
    if pat is None or pat == 'none':
        return
    if not re.match(str(pat), str(val)):
        errors.append(f"{e.base}: {e.ref}.{rule['attr']} '{val}' is not in the one canonical form "
                      f"'{key}' declares — {rule['registry']}.{key}.{rule['take']} is {pat!r}. A system "
                      f"owns its format so nothing invents a second spelling of it.")


def ectl_entry_form_from_kind_attr(e):
    """A kind may PIN which form its entries must use — and pinning also RESERVES that form.

    Any form some kind pins is available ONLY to kinds that pin it, so no bean can short-circuit its
    ownership chain straight to the axiom: the crown is reachable through your chain, not instead of it.
    """
    _fk = e.sch.get('entry_form_from_kind_attr')
    if not _fk:
        return
    _kind = ALL_FM.get(e.base, {}).get('kind')
    _form = (_row(KINDS, _kind) or {}).get(_fk)
    _reserved = {k[_fk] for k in KINDS.values() if isinstance(k, dict) and k.get(_fk)}
    if _form and _form not in e.entry:
        errors.append(f"{e.base}: {e.ref} must use the '{_form}' form — kind '{_kind}' pins "
                      f"{e.term}.{_fk} to it (VOCAB kinds.{_kind}.{_fk}){_termination_hint(e.term, e.base)}")
    for _used in (_reserved & set(e.entry)):
        if _used != _form:
            _allowed = sorted(k['kind'] for k in KINDS.values()
                              if isinstance(k, dict) and k.get(_fk) == _used)
            errors.append(f"{e.base}: {e.ref} uses the '{_used}' form, which is RESERVED to kind(s) "
                          f"{_allowed} — kind '{_kind}' must own through a being, not terminate "
                          f"at the axiom directly (VOCAB {e.term}.schema.{_fk})")


def ectl_on_aspect(e):
    """`on_aspect:` — the entry's position must be ON the closed figure it claims.

    This also RECORDS each aspect's effective position on the cell, because `cross_aspect` needs exactly
    the same derivation and used to repeat it.
    """
    for _aattr, _asp in _facet(e.form, 'aspect'):
        _adef = ASPECTS.get(_asp['aspect']) or {}
        _apos = {p['position'] for p in (_adef.get('positions') or []) if isinstance(p, dict)}
        _val = e.entry.get(_aattr, _asp.get('default'))
        e.eff[_aattr] = _val
        if _apos and _val not in _apos:
            errors.append(f"{e.base}: {e.ref}.{_aattr} '{_val}' is not a position on aspect "
                          f"'{_asp['aspect']}' {sorted(_apos)}")


def _cell_holds(e, cell):
    """Does this entry sit IN the cell? A `cross` cell reads each aspect's EFFECTIVE position (stated, else the
    declared default) and, FOR NOW, nothing else — exactly what `cross_aspect` could see. That blindness is the
    known over-fire on loopback endpoints (the cell cannot see `exposure`); lifting it changes verdicts, so it is
    a later, separately ratified step and not part of proving this form equivalent."""
    for attr, (how, want) in cell['when'].items():
        have = e.eff.get(attr) if cell['phase'] == 'cross' else e.entry.get(attr)
        if how == 'is' and have != want:
            return False
        if how == 'starts' and not str(have or '').startswith(str(want)):
            return False
    return bool(cell['when'])


def _cells(e, phase):
    """A CELL is a combination of what an entry holds that may not stand (an error) or should not (a warning).
    `cross_aspect`, `entry_required_if` and `entry_expect_if` were three constructs for this one idea. Two aspects
    span a GRID, and a grid has cells neither square sees; a form that implies an attribute is the same shape."""
    for cell in e.form['cells']:
        if cell['phase'] != phase or not _cell_holds(e, cell):
            continue
        lack = [k for k in cell['lacks'] if not e.entry.get(k)]
        if cell['lacks'] and not lack:
            continue
        sink = errors if cell['severity'] == 'error' else warns
        if phase == 'cross':
            sink.append(f"{e.base}: {e.ref} is {cell['origin'].upper().replace('_', ' ')} — "
                        + ', '.join(f'{k}:{v[1]}' for k, v in cell['when'].items())
                        + f" — {cell['why'] or 'the two positions do not sit together'}")
            continue
        (attr, (_how, want)), = cell['when'].items()
        if cell['origin'] == 'required_if':
            sink.append(f"{e.base}: {e.ref} declares {attr}:{want} but carries no {', '.join(lack)}")
        else:
            sink.append(f"{e.base}: {e.ref} has a {attr} starting '{want}' "
                        f"but no {lack[0]} — {cell['why'] or 'unverifiable'}")


def ectl_cross_aspect(e):
    _cells(e, 'cross')


def ectl_entry_one_of(e):
    one_of = list(e.sch.get('entry_one_of') or [])
    if one_of and not any(k in e.entry for k in one_of):
        errors.append(f"{e.base}: {e.ref} needs one of {one_of} (VOCAB {e.term}.schema.entry_one_of)")


def ectl_entry_required_if(e):
    _cells(e, 'cond')


def ectl_pointer_fields(e):
    """`pointer_fields:` — '<section>.<key>' on this bean | {bean,field} elsewhere | 'file:<path>'."""
    for attr, ptype in _facet(e.form, 'pointer'):
        if ptype != 'bean_field_pointer':
            continue
        val = e.entry.get(attr)
        for ptr in (val if isinstance(val, list) else [val] if val is not None else []):
            if not isinstance(ptr, str):
                continue                       # {bean,field} pointers resolve in the link pass below
            if ptr.startswith('file:'):
                _fp = ptr[5:]
                if not os.path.exists(os.path.join(ROOT, _fp)):
                    errors.append(f"{e.base}: {e.term}[{e.label}].{attr} '{ptr}' does not resolve — no "
                                  f"such file in this garden")
                continue
            sect, _, key = ptr.partition('.')
            node = ALL_FM[e.base].get(sect)
            if not key or not isinstance(node, dict) or key not in node:
                errors.append(f"{e.base}: {e.term}[{e.label}].{attr} '{ptr}' does not resolve — use "
                              f"'<section>.<key>' on this bean, {{bean,field}} for another bean, or "
                              f"'file:<path>'")


# Declaration order IS execution order, and it is the order these rules ran in before. `on_aspect` must
# precede `cross_aspect`: the second reads what the first computed.
def ectl_entry_extents(c):
    """`entry_extents:` — attrs INSIDE an entry that hold a region (11.2)."""
    for attr, _ in _facet(c.form, 'extent'):
        v = c.entry.get(attr)
        if v is not None:
            check_extent(f"{c.base}: {c.term}[{c.label}].{attr}", v)


ENTRY_CONTROLLERS = (
    ('declared_attrs', ectl_declared_attrs),
    ('entry_required_attrs', ectl_entry_required_attrs),
    ('entry_values', ectl_entry_values),
    ('entry_types', ectl_entry_types),
    ('entry_pattern', ectl_entry_pattern),
    ('entry_soft_pattern', ectl_entry_soft_pattern),
    ('entry_must_match', ectl_entry_must_match),
    ('entry_in_registry', ectl_entry_in_registry),
    ('entry_pattern_from_registry', ectl_entry_pattern_from_registry),
    ('entry_form_from_kind_attr', ectl_entry_form_from_kind_attr),
    ('on_aspect', ectl_on_aspect),
    ('cross_aspect', ectl_cross_aspect),
    ('entry_one_of', ectl_entry_one_of),
    ('entry_required_if', ectl_entry_required_if),
    ('entry_extents', ectl_entry_extents),
    ('pointer_fields', ectl_pointer_fields),
)


def check_entry(base, term, label, entry, sch):
    """Every per-entry rule the schema language can express."""
    if not isinstance(entry, dict):
        req = list(sch.get('entry_required_attrs') or [])
        errors.append(f"{base}: {term}[{label}] must be a mapping with {req}")
        return
    cell = _ECell(base, term, label, entry, sch)
    for _key, _controller in ENTRY_CONTROLLERS:
        _controller(cell)


def build_all_fm_and_targets():
    global ALL_FM, TARGETS_OF
    ALL_FM = {base: fm for (_ib, base), (fm, _) in docs.items()}   # mappings included: they carry terms too
    # `required_on_targets_of: <term>` — a bean POINTED AT by that relation must carry the declaring term.
    TARGETS_OF = {}
    for (_is_bean, _base), (_fm, _b) in docs.items():
        for _t, _s in SCHEMAS.items():
            _n = _fm.get(_t)
            if isinstance(_n, dict) and _n.get('bean'):
                TARGETS_OF.setdefault(_t, set()).add(_n['bean'])

# --- the interpreter, as controllers dispatched by schema key ----------------------------------------
# One controller per key the schema language defines, named after the KEY and never after a term, so a
# new key is a new controller and a new TERM is no code at all. A controller returns STOP when the term
# needs no further plies; before this those were seven bare `continue`s, which is the same control flow
# with nothing saying so. Two of them are load-bearing rather than tidy:
#   * alt_form  — the inherited `via` form legitimately carries no facet keys, so the per-key rules must
#                 not ask it for any. 6 of 61 documents use that form; drop this and every one fails.
#   * required  — a term that is missing has nothing for the shape, key and entry rules to judge, and
#                 reporting all four for one absence buries the one that matters.
STOP = 'stop'


class _Cell:
    """One (document, term) pair under inspection — the state every controller shares."""
    __slots__ = ('base', 'fm', 'is_bean', 'term', 'sch', 'node')

    def __init__(self, base, fm, is_bean, term, sch):
        self.base, self.fm, self.is_bean = base, fm, is_bean
        self.term, self.sch = term, sch
        self.node = fm.get(term)


def ctl_path(c):
    """`path:` — a nested field addressed by path rather than by its own name."""
    if not c.sch.get('path'):
        return None
    allowed = allowed_values(c.sch)
    for val in path_values(c.fm, c.sch['path']):
        if allowed and val not in allowed:
            errors.append(f"{c.base}: {c.sch['path']} '{val}' not in {sorted(allowed)} "
                          f"(VOCAB {c.term}.schema.values)" + UNKNOWN_VALUE_HINT)
    return STOP


def ctl_governs_anchor(c):
    """`governs_anchor:` — a term may govern the FORMAT of the anchor values carrying its name."""
    _ga = c.sch.get('governs_anchor')
    if not _ga:
        return None
    for _a in ((c.fm.get('identity') or {}).get('anchors') or []):
        if not isinstance(_a, dict) or _a.get('key') != _ga:
            continue
        _v = str(_a.get('value', ''))
        _pat = c.sch.get('value_pattern')
        if _pat and not re.match(_pat, _v):
            errors.append(f"{c.base}: anchor {_ga}='{_v}' is not in canonical form "
                          f"({c.sch.get('canonical_note', _pat)}) (VOCAB {c.term}.schema.value_pattern)")
        _cf = c.sch.get('compare_form')
        if _cf in COMPARE_FORMS and COMPARE_FORMS[_cf](_v) != _v:
            warns.append(f"{c.base}: anchor {_ga}='{_v}' is compared as '{COMPARE_FORMS[_cf](_v)}' — store it in that "
                         f"form (VOCAB {c.term}.schema.compare_form: {_cf})")
        _vr = c.sch.get('value_in_registry')
        if _vr:
            # (9.1) an anchor that IS a code of a published classification must be one of its codes
            _known = {str(r.get(_vr.get('take'))) for r in (registry(_vr.get('registry')) or []) if isinstance(r, dict)}
            if _v not in _known:
                errors.append(f"{c.base}: anchor {_ga}='{_v}' is not a {_vr.get('registry')} code "
                              f"(VOCAB {c.term}.schema.value_in_registry)")
        if c.sch.get('value_form') == 'ip':
            try:
                ipaddress.ip_address(_v)
            except ValueError:
                errors.append(f"{c.base}: anchor {_ga}='{_v}' is not a valid IP "
                              f"(VOCAB {c.term}.schema.value_form)")
    return STOP


def ctl_required(c):
    """`required:` / `required_on_<axis>s:` / `required_on_targets_of:` — must this term be here at all?

    The AXIS comes from the vocabulary key, not from this code, so `required_on_kinds` and
    `required_on_natures` (and any future axis) need no interpreter change.

    MULTI-VALUED AXES (2026-08-07, human-ratified, std-vocab@7.0). The loop below read the axis as a
    SCALAR, which is the whole reason `router` had to be a kind rather than a role: a machine holds one
    kind and one nature, but it holds SEVERAL roles — a mail server may have five — and `x in vals` cannot express that.
    Rather than add a bespoke `required_on_roles`, the axis mechanism itself is generalised, so an axis may
    now be carried three ways and any future one inherits it:
      · a scalar          — `kind: host`
      · a list of scalars — `roles: [router, mail]`
      · a list of entries — `roles: [{role: router, why: ...}]`, each naming the axis
    The requirement fires if ANY held value matches, which is the only reading that makes sense for a
    collection: a machine that is a router among other things is still a router.
    """
    sch, fm, base, term, is_bean, node = c.sch, c.fm, c.base, c.term, c.is_bean, c.node
    why = "every bean" if (is_bean and sch.get('required') is True) else None
    _rt = sch.get('required_on_targets_of')
    if is_bean and _rt and base in TARGETS_OF.get(_rt, set()):
        why = f"being the target of a {_rt} edge"
    for key, vals in sch.items():
        if is_bean and key.startswith('required_on_') and isinstance(vals, list):
            axis = key[len('required_on_'):-1]          # kinds -> kind, natures -> nature, roles -> role
            plural = key[len('required_on_'):]          # the TERM carrying it may be plural (`roles`)
            held = fm.get(axis) if fm.get(axis) is not None else fm.get(plural)
            held = held if isinstance(held, list) else [held]
            hit = [h.get(axis) if isinstance(h, dict) else h for h in held]
            hit = [h for h in hit if h is not None and h in vals]
            if hit:
                why = f"{axis} " + " / ".join(f"'{h}'" for h in hit)
    if why and (node is None or node == [] or node == {} or node == ''):
        errors.append(f"{base}: {why} requires a non-empty {term} (VOCAB {term} term)")
        return STOP                 # DECLARED: one absence, one finding — not four
    if node is None:
        return STOP                 # not required and not present: nothing to judge
    if _captured(fm, term):
        return STOP                 # a value nobody has chosen yet is not checkable (MERGE.md §10)
    return None


def ctl_must_equal_kind_attr(c):
    """`must_equal_kind_attr:` — the value must agree with the registry row for this bean's kind."""
    mk = c.sch.get('must_equal_kind_attr')
    if not mk:
        return None
    kreg = _row(KINDS, c.fm.get('kind'))
    if kreg is None and _captured(c.fm, 'kind'):
        return STOP                 # kind is mid-merge; the unclean warning already names it
    if kreg is None:
        errors.append(f"{c.base}: kind '{c.fm.get('kind')}' is not declared in the vocabulary, so its "
                      f"{c.term} cannot be checked (every bean kind needs a `kinds` entry with {mk})")
    elif kreg.get(mk) is None:
        errors.append(f"VOCAB kind '{c.fm.get('kind')}': missing '{mk}' (required to check {c.term})")
    elif c.node != kreg[mk]:
        errors.append(f"{c.base}: {c.term} '{c.node}' contradicts kind '{c.fm.get('kind')}' which refines "
                      f"{mk} '{kreg[mk]}' (VOCAB {c.term}.schema.must_equal_kind_attr)")
    return None


def ctl_shape(c):
    """`shape:` — scalar, list_of_entries, mapping, open_map_of_entries."""
    shape = c.sch.get('shape')
    if shape == 'scalar':
        allowed = allowed_values(c.sch)
        if allowed and c.node not in allowed:
            errors.append(f"{c.base}: {c.term} '{c.node}' not in {sorted(allowed)} "
                          f"(VOCAB {c.term}.schema.values)" + UNKNOWN_VALUE_HINT)
        return STOP
    if shape == 'list_of_entries' and not isinstance(c.node, list):
        errors.append(f"{c.base}: {c.term} must be a LIST of entries (VOCAB {c.term}.schema.shape)")
        return STOP
    if shape in ('mapping', 'open_map_of_entries') and not isinstance(c.node, dict):
        errors.append(f"{c.base}: {c.term} must be a MAPPING (VOCAB {c.term}.schema.shape)")
        return STOP
    return None


def ctl_alt_form(c):
    """`alt_form:` — an alternative single-key form (e.g. `owned_by: {via: ...}`)."""
    alt = c.sch.get('alt_form') or {}
    if alt.get('key') and isinstance(c.node, dict) and alt['key'] in c.node:
        return STOP                 # DECLARED: the inherited form carries no facet keys to check
    return None


def ctl_required_attrs(c):
    """`required_attrs:` — attributes the mapping itself must carry. And, since 12.0, ONLY declared ones."""
    if c.sch.get('shape') == 'mapping' and not c.sch.get('key_form') and not c.sch.get('entry_one_of'):
        undeclared_attrs(c.base, c.term, c.term, c.node, c.sch)
    for attr, _ in _facet(attribute_form(c.term, c.sch), 'required') if attribute_form(c.term, c.sch)['scope'] == 'self' else []:
        if isinstance(c.node, dict) and attr not in c.node:
            errors.append(f"{c.base}: {c.term} requires '{attr}' (VOCAB {c.term}.schema.required_attrs)")
    return None


def ctl_attr_types(c):
    """`attr_types:` — types for the mapping's OWN attrs."""
    for attr, typ in _facet(attribute_form(c.term, c.sch), 'type') if attribute_form(c.term, c.sch)['scope'] == 'self' else []:
        v = c.node.get(attr) if isinstance(c.node, dict) else None
        if v is not None:
            check_value_type(f"{c.base}: {c.term}", attr, v, typ)
    return None


def ctl_key_form(c):
    """`key_form:` — what the mapping's keys must look like when the key set is open."""
    kf = str(c.sch.get('key_form') or '')
    if not (kf and isinstance(c.node, dict)):
        return None
    for k in c.node:
        if kf == 'kebab' and KEBAB and not KEBAB.match(str(k)):
            errors.append(f"{c.base}: {c.term} key '{k}' must be kebab-case "
                          f"(the key is open, but still paper-durable)")
        elif kf.startswith('values_from:'):
            allowed = term_values(kf.split(':', 1)[1])
            if allowed and k not in allowed:
                errors.append(f"{c.base}: {c.term} key '{k}' not in declared {kf.split(':', 1)[1]} "
                              f"{sorted(allowed)}")
        elif kf == 'values':
            allowed = allowed_values(c.sch)
            if allowed and k not in allowed:
                errors.append(f"{c.base}: {c.term} key '{k}' not in {sorted(allowed)}")
    return None


def ctl_on_sequence(c):
    """`on_sequence:` (10.1, T4) — the value is a walk on a SEQUENCE aspect: prose lines in list order, or step
    entries whose `next` lists are CLOSED neighbourhoods (these branches and no others). The aspect's own
    restrictions decide the rest: whether a loop is allowed is its `acyclic`, whether an end is owed is `ends`."""
    _asp = c.sch.get('on_sequence')
    if not _asp or c.node is None:
        return None
    _a = ASPECTS.get(_asp) or {}
    if _a.get('figure') != 'sequence':
        errors.append(f"VOCAB {c.term}: on_sequence '{_asp}' is not a sequence aspect")
        return None
    where = f"{c.base}: {c.term}"
    if not isinstance(c.node, list):
        errors.append(f"{where} must be a list — prose lines, or step entries {{id, do, next}}"); return None
    _prose = [x for x in c.node if isinstance(x, str)]
    _steps = [x for x in c.node if isinstance(x, dict)]
    if _prose and _steps or len(_prose) + len(_steps) != len(c.node):
        errors.append(f"{where} mixes prose lines and step entries — write one form: a routine read half by list "
                      f"order and half by `next` has no single order"); return None
    if not _steps:
        return None                                   # prose: the list order IS the sequence, as before
    ids, nexts = [], {}
    for i, st in enumerate(_steps):
        sid = st.get('id')
        if not sid or not (KEBAB is None or KEBAB.match(str(sid))):
            errors.append(f"{where}[{i}] needs a kebab-case `id`"); continue
        if sid in nexts:
            errors.append(f"{where}: two steps are '{sid}' — a step is named once"); continue
        if not isinstance(st.get('do'), str) or not st['do'].strip():
            errors.append(f"{where}.{sid} needs `do`: what the step does")
        _n = st.get('next') or []
        if not isinstance(_n, list) or not all(isinstance(x, dict) and x.get('to') for x in _n):
            errors.append(f"{where}.{sid}.next must be a list of {{to, when?}}"); _n = []
        if len(_n) > 1:
            for x in _n:
                if not str(x.get('when') or '').strip():
                    errors.append(f"{where}.{sid}: a branch to '{x.get('to')}' names no `when` — with two or more "
                                  f"ways on, each must say when it is taken")
        ids.append(sid); nexts[sid] = [x['to'] for x in _n]
    for sid, tos in nexts.items():
        for t in tos:
            if t not in nexts:
                errors.append(f"{where}.{sid}: next '{t}' names no step of this routine (a branch to nowhere)")
    if not ids:
        return None
    seen, todo = set(), [ids[0]]
    while todo:
        n = todo.pop()
        if n in seen or n not in nexts:
            continue
        seen.add(n); todo.extend(nexts[n])
    for sid in ids:
        if sid not in seen:
            errors.append(f"{where}.{sid}: no step reaches it from '{ids[0]}', where the routine starts")
    if _a.get('ends') in ('bounded', 'open-start') and not any(not nexts[s] for s in ids):
        errors.append(f"{where}: no step ends the routine — give at least one step no `next`")
    if _a.get('acyclic') is True and _cycles({k: v for k, v in nexts.items()}):
        errors.append(f"{where}: loops, and '{_asp}' declares acyclic")
    return None


def ctl_entries(c):
    """The per-ENTRY rules, for any shape that has entries at all."""
    shape = c.sch.get('shape')
    if shape in ('list_of_entries', 'open_map_of_entries') or c.sch.get('entry_one_of') \
            or c.sch.get('entry_required_attrs'):
        for label, entry in entries_of(shape, c.node):
            check_entry(c.base, c.term, label, entry, c.sch)
    return None


# The order is the order the rules ran in before, written down. A key that is absent from a schema costs
# its controller one `return None`, which is why adding a key never touches any other controller.
CONTROLLERS = (
    ('path', ctl_path),
    ('governs_anchor', ctl_governs_anchor),
    ('required', ctl_required),
    ('must_equal_kind_attr', ctl_must_equal_kind_attr),
    ('shape', ctl_shape),
    ('alt_form', ctl_alt_form),
    ('required_attrs', ctl_required_attrs),
    ('attr_types', ctl_attr_types),
    ('attr_extents', ctl_extents),
    ('key_form', ctl_key_form),
    ('entries', ctl_entries),
    ('on_sequence', ctl_on_sequence),
)


def check_terms():
    """Every document, against every term the vocabulary declares."""
    for (is_bean, base), (fm, body) in docs.items():
        for term, sch in SCHEMAS.items():
            cell = _Cell(base, fm, is_bean, term, sch)
            for _key, _controller in CONTROLLERS:
                if _controller(cell) is STOP:
                    break


# --- facet parity: two arcs of one loop must carry the same facets (schema `facet_parity_with`; P7) ---
# Ownership is meaningful only where responsibility covers it on the opposite aspect. A facet owned but
# unanswered-for is a loose end; a facet answered for but unowned is orphaned.
def _facet_shape(node, alt):
    """The set of facets a node carries, or the INHERITED form's key when it uses that form instead.

    `alt` comes from the term's own `alt_form.key`, never from a literal here: the interpreter reads
    that declaration generically everywhere else, and this check was the one place that knew the name
    by heart — a second copy of a declared datum, sitting three functions from where it is read.
    """
    if not isinstance(node, dict):
        return None
    return alt if (alt and alt in node) else frozenset(node)


def _alt_key(term):
    return ((SCHEMAS.get(term) or {}).get('alt_form') or {}).get('key')


def _shape_str(shape, alt):
    return alt if shape == alt else sorted(shape)

def check_facet_parity():
    for _term, _sch in SCHEMAS.items():
        _par = _sch.get('facet_parity_with')
        if not _par:
            continue
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean:
                continue
            _a, _o = _fm.get(_term), _fm.get(_par)
            if _a is None and _o is None:
                continue
            if _a is None:
                errors.append(f"{_base}: has {_par} but no {_term} — an ownership claim nothing answers for "
                              f"is a loose end (VOCAB {_term}.rules.parity)")
            elif _o is None:
                errors.append(f"{_base}: has {_term} but no {_par} — a duty nobody owns is orphaned "
                              f"(VOCAB {_term}.rules.parity)")
            else:
                _ka, _ko = _alt_key(_term), _alt_key(_par)
                _sa, _so = _facet_shape(_a, _ka), _facet_shape(_o, _ko)
                if _sa is None or _so is None:
                    # One of the two is not a mapping at all, so it has no facet SHAPE to compare. The
                    # `must be a MAPPING` rule owns that error; comparing anyway crashed the gate on
                    # `sorted(None)` — reachable since this check was written, and reached for the first
                    # time by the coverage pass that was measuring what the suite never fires.
                    continue
                if _sa != _so:
                    errors.append(f"{_base}: {_term} and {_par} disagree on facets "
                                  f"({_shape_str(_sa, _ka)} vs {_shape_str(_so, _ko)}) — "
                                  f"the two arcs must close (VOCAB {_term}.rules.parity)")



# --- declared inverse relations must agree (schema `inverse_of`; P4/D3) ----------------------------
# A convenience edge that mirrors a fact must not be able to drift from the fact it mirrors.
def _inverse_of(sch):
    """(term, cardinality) from `inverse_of`, which is a bare name or a mapping.

    A bare name means one-to-one and the mirror is enforced both ways — that is what it always meant,
    and it was wrong for `runtime`, whose type side cannot point back at three instances through one
    mapping. Declaring the cardinality is the fix; reading it in one place is what stops the two plies
    from disagreeing about what was declared.
    """
    inv = sch.get('inverse_of')
    if isinstance(inv, dict):
        return inv.get('term'), inv.get('cardinality', 'one-to-one')
    return inv, 'one-to-one'


def check_inverse_relations():
    for _term, _sch in SCHEMAS.items():
        _inv, _card = _inverse_of(_sch)
        if not _inv:
            continue
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean or not isinstance(_fm.get(_term), dict):
                continue
            _tgt = _fm[_term].get('bean')
            if not _tgt or (True, _tgt) not in docs:
                continue                                  # dangling target is reported by link integrity
            _back = docs[(True, _tgt)][0].get(_inv)
            if not (isinstance(_back, dict) and _back.get('bean') == _base):
                errors.append(f"{_base}: {_term} -> '{_tgt}', but {_tgt}.{_inv} does not point back to "
                              f"'{_base}' (VOCAB {_term}.schema.inverse_of: {_inv})")



# ============================== THE REVERSE GATE (P3.5) ==============================
# The interpreter above asks whether each OBJECT is passed by the rules. This asks the converse:
# whether each RULE is passed by the objects. A declared position with no occupant is a blind region —
# it may be a prediction, an impossibility, or simply out of context, but it must SAY WHICH. Silence is
# how a vocabulary quietly accumulates possibilities nothing is looking for. Positions are derived from
# the schemas themselves, so this names no term (rule: the machinery never names an aspect).
def check_vacancy_reasons_declared():
    global VACANCY_REASONS
    VACANCY_REASONS = set(std_fm.get('vacancy_reasons') or ())
    if not VACANCY_REASONS:
        # No fallback, deliberately, and for the reason law_carrier already gives: a gate that cannot load
        # the law must ERROR rather than substitute one of its own. A default set here would silently accept
        # whatever this file happened to believe on a garden whose vocabulary says something else.
        errors.append("seed/std-vocab.md declares no `vacancy_reasons:` — the gate will not check a "
                      "vacancy's reason against a list of its own invention. Declare them in the "
                      "vocabulary (law_carrier: there is exactly one path to the law).")

LOCAL_ADDED = set()      # (source, position) a garden added with `values_add` — the garden accounts for exactly these


def _declared_positions():
    """Every position the VOCABULARY offers: {source: {position}}, and which sources are the garden's.

    A source is `<term>.values`, `<term>.<entry attr>`, `aspect:<name>` or `<term>.entry_one_of` — the
    address a vacancy is declared `at`. The second return is the subset this garden DECLARED itself.
    """
    declared_pos, local_pos = {}, set()
    LOCAL_ADDED.clear()
    # WHOEVER DECLARES A POSITION ACCOUNTS FOR IT (P6/B2). A garden's occupancy claim covers only the
    # positions IT declared: Tier-0 positions are Tier-0's to account for, in its own vacancies block.
    # Without this a fresh garden fails its first gate run, ordered to justify `nature: physical` before it
    # has written a bean — which is precisely the debt promotion must not export.
    LOCAL_SCHEMA = {t['term']: (t.get('schema') or {})
                    for t in (vocab_fm.get('local_terms') or []) if isinstance(t, dict) and t.get('term')}

    def _declare(src, vals, local):
        declared_pos.setdefault(src, set()).update(v for v in (vals or []) if not isinstance(v, (dict, list)))
        if local:
            local_pos.add(src)

    for term, sch in SCHEMAS.items():
        _loc = LOCAL_SCHEMA.get(term, {})
        if sch.get('values'):
            if 'values' not in _loc and _loc.get('values_add'):
                # ONLY the added values are the garden's to account for; the rest stay Tier-0's.
                _t0 = next((t.get('schema') or {} for t in (std_fm.get('terms') or []) + PROFILE_TERMS
                            if isinstance(t, dict) and t.get('term') == term), {})
                _added = set(_loc['values_add']) - set(_t0.get('values') or [])   # already Tier-0's: not the garden's
                _declare(f"{term}.values", [v for v in sch['values'] if v not in _added], False)
                declared_pos[f"{term}.values"].update(_added)
                LOCAL_ADDED.update((f"{term}.values", v) for v in _added)
            else:
                _declare(f"{term}.values", sch['values'], 'values' in _loc)
        for attr, vals in (sch.get('entry_values') or {}).items():
            _declare(f"{term}.{attr}", vals, attr in (_loc.get('entry_values') or {}))
        for _asp in _aspects_of(sch):
            if _asp['aspect'] in ASPECTS:
                _declare(f"aspect:{_asp['aspect']}",
                         [p['position'] for p in (ASPECTS[_asp['aspect']].get('positions') or [])
                          if isinstance(p, dict)], False)
        # `entry_one_of` forms are positions too. The law offers a shape — `owner`, `contract`,
        # `external`, `crown` — and a shape nothing takes is the same blind region as an enum value
        # nobody occupies. Nothing counted them until 2026-08-03, and all three that turned out to be
        # empty are genuinely empty rather than overlooked.
        if sch.get('entry_one_of'):
            _declare(f"{term}.entry_one_of", list(sch['entry_one_of']), 'entry_one_of' in _loc)
    return declared_pos, local_pos


def _enum_owner(reg_name, take):
    """The term that OWNS a registry-backed enum: the one holding its `values` equal to that registry.

    DERIVED, never listed. A table mapping registries to owner terms would be a third copy of a
    relationship the two ends already state, and this garden has paid for that shape before.
    """
    want = f"registry:{reg_name}[].{take}"
    for _t, _s in SCHEMAS.items():
        if want in (_s.get('values_consistent_with') or []):
            return _t
    return None


def _occupied_positions():
    """Every position the CORPUS takes, addressed the same way `_declared_positions` addresses them."""
    occupied_pos = {}

    def _occupy(src, vals):
        occupied_pos.setdefault(src, set()).update(v for v in vals if v is not None)

    for (is_bean, base), (fm, _body) in docs.items():
        for term, sch in SCHEMAS.items():
            if sch.get('path'):
                _occupy(f"{term}.values", path_values(fm, sch['path']))
                continue
            node = fm.get(term)
            if node is None:
                continue
            if sch.get('shape') == 'scalar' and sch.get('values'):
                _occupy(f"{term}.values", [node])
            kf = str(sch.get('key_form') or '')
            if kf.startswith('values_from:') and isinstance(node, dict):
                alt = (sch.get('alt_form') or {}).get('key')      # the inherited form is not a position
                _occupy(f"{kf.split(':', 1)[1]}.values", [k for k in node if k != alt])
            _asps = _aspects_of(sch)
            _alt_k = (sch.get('alt_form') or {}).get('key')
            _forms = list(sch.get('entry_one_of') or [])
            if _forms and isinstance(node, dict) and not (_alt_k and _alt_k in node):
                # the INHERITED form carries no facets and therefore takes no position
                for _facet in node.values():
                    if isinstance(_facet, dict):
                        _occupy(f"{term}.entry_one_of", [f for f in _forms if f in _facet])
            for _lbl, entry in entries_of(sch.get('shape'), node):
                if isinstance(entry, dict):
                    for attr in (sch.get('entry_values') or {}):
                        if entry.get(attr) is not None:
                            _occupy(f"{term}.{attr}", [entry[attr]])
                    # An `entry_in_registry` attr takes a position in the enum the REGISTRY defines, and
                    # that enum is owned by whichever term holds its `values` equal to it. Counting it
                    # against the owner is what lets a registry-backed enum be declared ONCE: without
                    # this the owner term looks wholly vacant, because it is never carried on a bean —
                    # it exists to own the list, and the list is occupied through other terms' entries.
                    for attr, _rule in (sch.get('entry_in_registry') or {}).items():
                        _owner = _enum_owner(_rule.get('registry'), _rule.get('take'))
                        if _owner and entry.get(attr) is not None:
                            _occupy(f"{_owner}.values", [entry[attr]])
                    for _asp in _asps:
                        # A DEFAULT DOES NOT OCCUPY (ratified 2026-08-03). This read `entry.get(attr,
                        # default)`, so a position nothing ever stated looked exercised because the gate's
                        # own default landed on it — the reverse gate believing itself. Occupancy is now
                        # STATEMENT: only a value an entry actually carries takes the position. What that
                        # leaves empty is a vacancy like any other, declared in `vacancies:` with a reason,
                        # and anti-rot then warns the day something really occupies it.
                        _aattr = _asp.get('attr', _asp['aspect'])
                        if entry.get(_aattr) is not None:
                            _occupy(f"aspect:{_asp['aspect']}", [entry[_aattr]])
    return occupied_pos


def _vacancy_index():
    """The declared vacancies, {(at, position): entry}, CHECKED for reason and why as they are indexed.

    Checked here rather than in the comparison below because these two rules are about the vacancy
    RECORD itself — a reason off the declared list, a missing why — and hold whether or not the
    position turns out to be occupied. The second return is the subset this garden declared, which is
    the only subset anti-rot may raise as an error.
    """
    vac_index, local_vac = {}, set()
    for _tier, _vs in (('tier0', (std_fm.get('vacancies') or []) + PROFILE_VAC),
                       ('local', vocab_fm.get('vacancies') or [])):
        for v in _vs:
            if not isinstance(v, dict):
                continue
            _key = (str(v.get('at')), v.get('position'))
            vac_index[_key] = v
            if _tier == 'local':
                local_vac.add(_key)
            if v.get('reason') not in VACANCY_REASONS:
                errors.append(f"{_tier} vacancies: {v.get('at')} = '{v.get('position')}' has reason "
                              f"'{v.get('reason')}' not in {sorted(VACANCY_REASONS)}")
            if not str(v.get('why') or '').strip():
                errors.append(f"{_tier} vacancies: {v.get('at')} = '{v.get('position')}' needs a 'why' — "
                              f"a vacancy is information only when it carries its reason")
    return vac_index, local_vac


def check_reverse_gate():
    """Offered, taken, and accounted for — the three sets, compared.

    The three are built by the helpers above rather than in one 100-line pass, because they answer
    three separate questions and only the comparison needs all three at once. Their ORDER is still
    load-bearing: `_vacancy_index` reports on the vacancy records themselves and must do so before
    this loop reports on the positions, or a garden with a malformed vacancy reads its consequences
    before its cause.
    """
    declared_pos, local_pos = _declared_positions()
    occupied_pos = _occupied_positions()
    vac_index, local_vac = _vacancy_index()

    for src, decl in sorted(declared_pos.items()):
        occ = occupied_pos.get(src, set())
        for pos in sorted(decl - occ, key=str):
            if src not in local_pos and (src, pos) not in LOCAL_ADDED:
                continue
            if (src, pos) not in vac_index:
                errors.append(f"VOCAB {src}: position '{pos}' is declared but NO bean occupies it — give it "
                              f"an occupant, or declare it in `vacancies:` with a reason")
        for pos in sorted(decl & occ, key=str):
            # A Tier-0 vacancy that this garden OCCUPIES is a prediction coming true. It cannot be an error —
            # the garden may not edit Tier-0 — but silence would let Tier-0 vacancies rot unnoticed, which is
            # the very failure anti-rot exists to prevent. So: warn, addressed to whoever maintains Tier-0.
            if (src, pos) in vac_index and (src, pos) not in local_vac:
                warns.append(f"{src}: position '{pos}' is declared vacant at TIER-0 but is OCCUPIED here — "
                             f"the prediction came true; whoever maintains std-vocab should withdraw it")
            if (src, pos) in local_vac:      # anti-rot: only a vacancy THIS garden declared can be an error
                errors.append(f"VOCAB vacancies: {src} = '{pos}' is declared vacant but IS occupied — "
                              f"remove the stale vacancy")
    for at, pos in sorted(vac_index, key=str):
        if pos not in declared_pos.get(at, set()):
            errors.append(f"VOCAB vacancies: {at} = '{pos}' is not a declared position (stale or misspelt)")



# ============================== link integrity + acyclic check ==============================
def schema_edges(fm):
    """Ref edges declared by the vocabulary (schema ref_fields / entry_ref_fields / pointer_fields).

    EVERY edge the gate resolves comes from here (P4) — there is no second source, and no relation is
    named in this file. A one-line `edges()` wrapper used to sit in front of it saying exactly that,
    which left two names for one generator and let a reader think the two differed.
    """
    for term, sch in SCHEMAS.items():
        node = fm.get(term)
        if node is None:
            continue
        alt = sch.get('alt_form') or {}
        if alt.get('key') and isinstance(node, dict) and alt['key'] in node:
            for attr in (alt.get('ref_fields') or []):
                it = node.get(attr)
                if isinstance(it, dict) and 'bean' in it:
                    yield 'bean', it.get('bean'), None, term
            continue
        for attr in (sch.get('ref_fields') or []):
            it = node if attr == 'self' else (node.get(attr) if isinstance(node, dict) else None)
            if isinstance(it, dict) and 'bean' in it:
                yield 'bean', it.get('bean'), it.get('field'), term
        for label, entry in entries_of(sch.get('shape'), node):
            if not isinstance(entry, dict):
                continue
            for attr in (sch.get('entry_ref_fields') or []):
                it = entry if attr == 'self' else entry.get(attr)
                if isinstance(it, dict):
                    for space in ('bean', 'mapping'):
                        if space in it:
                            yield space, it.get(space), it.get('field'), term
            for attr, ptype in (sch.get('pointer_fields') or {}).items():
                if ptype != 'bean_field_pointer':
                    continue
                val = entry.get(attr)
                for ptr in (val if isinstance(val, list) else [val] if val is not None else []):
                    if isinstance(ptr, dict) and 'bean' in ptr:
                        yield 'bean', ptr.get('bean'), ptr.get('field'), f"{term}[{label}].{attr}"


def section_keys(fm):
    # DELIBERATELY WIDER THAN _AUTHORITATIVE, and not an oversight. This answers "what key names does
    # this document use", so that a `{bean: X, field: K}` ref can be resolved — and a ref may legitimately
    # point into `refs` or `access`, which carry no authoritative values of their own. Stated because an
    # undeclared difference between two nearly-identical lists reads as a bug and invites a tidy-up.
    s = set(fm.keys())
    for sect in ('owns', 'attributes', 'refs', 'access', 'details'):
        if isinstance(fm.get(sect), dict):
            s |= set(fm[sect].keys())
    return s


def _cycles(graph):
    """Every back edge in `graph`, as the trail of ids that reaches it.

    ONE walk with two callers: `check_acyclic` runs it over the graph MERGED from every dag-declared
    relation, and `check_acyclic_per_relation` runs it over each relation alone. Same algorithm, same
    order, different graph and different sink — so it is written once rather than twice, which is the
    rule this file applies to derived facts applied to the derivation itself. Colour 2 marks a node
    already finished: reaching it again is a diamond, not a cycle.
    """
    colour, trails = {}, []

    def walk(n, trail):
        colour[n] = 1
        for m in graph.get(n, []):
            if colour.get(m, 0) == 1:
                trails.append(trail + [n, m])
            elif colour.get(m, 0) == 0:
                walk(m, trail + [n])
        colour[n] = 2

    for n in list(graph):
        if colour.get(n, 0) == 0:
            walk(n, [])
    return trails


def check_link_integrity():
    global DAG_TERMS, dep_graph
    DAG_TERMS = {n for n, s in SCHEMAS.items() if on_walk(s, acyclic_only=True)}
    dep_graph = {}
    for (is_bean, base), (fm, body) in docs.items():
        for space, tgt, field, sect in schema_edges(fm):
            pool = bean_ids if space == 'bean' else map_ids
            if not isinstance(tgt, str):
                errors.append(f"{base}: {sect} target not a string id ({tgt!r}) — quote it"); continue
            if tgt not in pool:
                errors.append(f"{base}: {sect} -> {space} '{tgt}' does not exist (dangling)"); continue
            tgt_fm = docs[(space == 'bean', tgt)][0]
            if field and field not in section_keys(tgt_fm):
                errors.append(f"{base}: {sect} -> {tgt}.{field} — field not present in '{tgt}'")
            if field and isinstance(tgt_fm.get('refs'), dict) and field in tgt_fm['refs']:
                warns.append(f"{base}: {sect} -> {tgt}.{field} points at a ref (ref-to-ref)")
            if sect in DAG_TERMS and space == 'bean':
                dep_graph.setdefault(base, []).append(tgt)


def check_acyclic():
    for trail in _cycles(dep_graph):
        errors.append(f"cycle ({'/'.join(sorted(DAG_TERMS))}): {' -> '.join(trail)}")



# ============================== ip dedup (vocab-driven, std-vocab 'ip' context_keys) ==============================
def collect_ips(fm):
    out = []
    def consider(kp, val):
        if any(fnmatch.fnmatch(kp, p) for p in ip_patterns):
            for v in (val if isinstance(val, list) else [val]):
                if isinstance(v, str):
                    out.append(v)
    for sect in _AUTHORITATIVE:
        d = fm.get(sect)
        if isinstance(d, dict):
            for k, v in d.items():
                consider(k, v)
                if k == 'identifiers' and isinstance(v, dict):
                    for k2, v2 in v.items():
                        consider(f'identifiers.{k2}', v2)
    return out


def check_duplicate_authoritative_ip():
    owner = {}
    for (is_bean, base), (fm, body) in docs.items():
        if not is_bean:
            continue
        shared = set(fm.get('shared_identifiers') or [])
        scope = fm.get('scope') or fm.get('network') or ''
        for v in collect_ips(fm):
            if v in shared:
                continue
            try:
                norm = str(ipaddress.ip_address(v))
            except ValueError:
                warns.append(f"{base}: value '{v}' under an ip key is not a valid IP"); continue
            owner.setdefault((norm, scope), []).append(base)
    for (ip, scope), bs in sorted(owner.items()):
        if len(bs) > 1:
            errors.append(f"duplicate authoritative IP {ip}{'@'+scope if scope else ''} owned by {bs} "
                          f"(ref it, or shared_identifiers/scope per VOCAB 'ip')")



# ---- single owner of a fact: the same long value stated authoritatively in two beans ----------------


def _long_values(fm):
    def walk(node, path):
        if isinstance(node, dict):
            for k, v in node.items():
                yield from walk(v, f"{path}.{k}" if path else str(k))
        elif isinstance(node, list):
            for i, v in enumerate(node):
                yield from walk(v, f"{path}[{i}]")
        elif isinstance(node, str) and len(node.strip()) > 60:
            yield path, node.strip()
    for sect in _AUTHORITATIVE:
        if isinstance(fm.get(sect), dict):
            yield from walk(fm[sect], sect)


def check_single_owner_of_a_fact():
    _value_owner = {}
    for (is_bean, base), (fm, _b) in docs.items():
        for path, val in _long_values(fm):
            _value_owner.setdefault(val, []).append(f"{base}.{path}")
    for _val, _where in sorted(_value_owner.items()):
        if len({w.split('.')[0] for w in _where}) > 1:
            warns.append(f"the same authoritative value is stated in {sorted({w.split('.')[0] for w in _where})} "
                         f"({', '.join(_where[:3])}) — one owner of a fact: keep it in one bean and `ref` it "
                         f"from the others. Value begins: {_val[:70]}…")



# ============================== pre-commit: the staged state must be sound ==============================
# Everything above reads the WORKING TREE. What gets committed is the INDEX, and they are not the same
# thing under partial staging. These two checks read the staged blobs, so what is committed is what was
# checked. The second closes the edit->gate window that text surgery kept slipping through: an edit that
# destroys a document, or silently drops a whole top-level key, cannot reach history.
# Both go through `_git` below: it is the one place that knows how to run git in ROOT and how to report
# an unanswered question. These two used to call subprocess directly, so a third reading of the same
# index went through a second, slightly different code path — and the callers here genuinely do not care
# WHY a blob is absent (a path not staged and a path deleted in the index are both "nothing to read"),
# which is exactly the distinction `_git` returns and these two discard on purpose.
def _staged_text(p):
    return _git('show', f':{p}')[0]


def _head_text(p):
    return _git('show', f'HEAD:{p}')[0]


def build_staged_constants():
    global DOCUMENTISH, LAW_DOCS, FRONT_MATTER_DOCS
    DOCUMENTISH = ('beans/', 'mappings/')

    # WHICH DOCUMENTS ARE LAW — DERIVED, never listed. This was a hardcoded tuple of three filenames while
    # `beans/daftar.md` declared FIVE documents `standing: law`, so MODEL.md, CHECKLIST.md and MERGE.md could
    # each be committed with no journal entry at all — the most consequential writes in the system, and the
    # only ones exempt from logging. Two lists that can disagree did disagree, in both directions.
    # The gate names no document now, exactly as it names no term: a garden says what its law is, and the
    # duty follows automatically when a document's standing changes.
    _STRUCTURAL_LAW = {os.path.relpath(STD, ROOT), 'VOCAB.md', 'GARDEN.md'}
    # Structural because the gate reads all three as law on EVERY run, in every garden, including one with no
    # beans at all to declare anything. GARDEN.md earns it for a different reason than the other two: it
    # carries the `extends:` pin, and moving a pin adopts a different law wholesale.
    LAW_DOCS = set(_STRUCTURAL_LAW)
    for _fm in ALL_FM.values():
        for _e in (_fm.get('standing') or []):
            if isinstance(_e, dict) and _e.get('standing') == 'law' and isinstance(_e.get('doc'), str):
                LAW_DOCS.add(_e['doc'][5:] if _e['doc'].startswith('file:') else _e['doc'])
    # THE RELEASE'S OWN FILES ARE LAW TOO (v0.5.0, human-ratified). Everything seed/LANGUAGE lists arrived from a
    # daftar release — the model, the checklist, the tools, the gate itself. A garden may still patch one
    # locally, but never silently: a cold-start drill committed an edit to bin/dmcheck.py with no journal entry.
    global LANGUAGE_PATTERNS
    _lang = os.path.join(ROOT, 'seed', 'LANGUAGE')
    LANGUAGE_PATTERNS = ([l.strip() for l in open(_lang, encoding='utf-8')
                          if l.strip() and not l.lstrip().startswith('#')] if os.path.isfile(_lang) else [])

    # NOT the same set, and deliberately so. The integrity check below parses front matter and refuses a
    # document that has lost it; MODEL.md and CHECKLIST.md are prose and carry none, so holding them to it
    # would refuse them as "destroyed" on every commit. Law is about what a change MEANS; this is about what
    # a file must still BE.
    FRONT_MATTER_DOCS = ('VOCAB.md', 'GARDEN.md', 'std-vocab.md')

# The commit-time half of this gate reads the STAGED blobs, so it needs an index to read them from.
# Being unable to ASK is not the same as being told the index is empty, and until 2026-08-03 this code
# could not tell those apart: the whole block sat inside a bare `except Exception: pass`. In any tree
# with no .git — a `cp -r`, an unpacked tarball, a copy carried to another machine — five Part-A rules
# silently did not run and the gate still printed `0 error(s)`. Reproduced before the fix: a copy of
# this garden with .git removed and the entire `owns:` block deleted from beans/daftar.md — the block
# carrying `invariant_no_silent_fallback` itself — reported `58 docs, 0 error(s)`, exit 0. The hole was
# not unknown: test/germinate.py's own docstring names it, and that test was built AROUND it.
# A gate that cannot verify must REFUSE. That is not a new rule — it is what `law_carrier` already says
# about the vocabulary, applied to the transport the other half of the law arrives on.
def _git(*args):
    """Run git in ROOT. Returns (stdout, None) on success, (None, why) when the question went unanswered."""
    try:
        r = subprocess.run(['git', '-C', ROOT, *args], capture_output=True, text=True, timeout=5)
    except Exception as e:                    # git absent, or it hung — still an unanswered question
        return None, f"{e.__class__.__name__}: {e}"
    if r.returncode != 0:
        _lines = (r.stderr or '').strip().splitlines()
        return None, _lines[0] if _lines else f"git exited {r.returncode}"
    return r.stdout, None


# Probe with rev-parse rather than with the diff itself: outside a repository `git diff` silently becomes
# `--no-index` and complains about the FLAG, which names the wrong problem to whoever reads the error.
def check_staged_state():
    _out, _why = _git('rev-parse', '--git-dir')
    if not _why:
        _out, _why = _git('diff', '--cached', '--name-only')

    if _why:
        errors.append(f"NO INDEX at {ROOT} — this is not a readable git working copy ({_why}). The five "
                      f"commit-time rules (provenance duty, "
                      f"RULE-CHANGE duty, undeclared top-level removal, gutted subtree, emptied body) "
                      f"CANNOT run here, so this run has NOT checked what a commit would contain. This is a "
                      f"refusal, not a pass: a garden is a git-backed ledger, and a tree with no index is a "
                      f"copy of one. Run the gate in the working copy, or `git init` this tree.")
        staged = []
    else:
        staged = _out.split()

    if staged:
        # (K) provenance duty — a state-change must be logged
        sc = [p for p in staged if p.startswith(DOCUMENTISH)]
        if sc and 'log/journal.md' not in staged:
            errors.append(f"state-change staged ({', '.join(sc[:3])}…) but log/journal.md not updated — provenance duty. "
                          f"Append an entry naming what changed and why, e.g.\n"
                          f"      ## <YYYY-MM-DD> · <human (name) | agent> · <one line>\n"
                          f"      - action: <what was done to {sc[0]}>")
        # ...and a RULE-CHANGE all the more so: it is human-ratified and must be logged DISTINCTLY.
        rc = [p for p in staged if p in LAW_DOCS or any(fnmatch.fnmatch(p, _pat) for _pat in LANGUAGE_PATTERNS)]
        if rc and 'log/journal.md' not in staged:
            errors.append(f"RULE-CHANGE staged ({', '.join(rc)}) but log/journal.md not updated — a change "
                          f"to the vocabulary or the law is human-ratified and must be logged distinctly, "
                          f"more than an ordinary state-change, not less")

        # ONLY the ADDED lines count as the declaration. Matching the whole diff would match its context
        # lines too, so on an append-only journal any common word would look "mentioned" — a false
        # negative that quietly disarms the rule. (Found by AB3: `tags` appeared in nearby context.)
        _jraw = _git('diff', '--cached', '--unified=0', '--', 'log/journal.md')[0] or ''
        jdiff = '\n'.join(l[1:] for l in _jraw.splitlines()
                           if l.startswith('+') and not l.startswith('+++'))

        # THE ENTRY MUST SAY WHAT IT RECORDS (2026-09-17, human-ratified). Until v0.4.0 these three duties were
        # satisfied by ANY byte added to the journal: a cold-start drill appended the single line `x` and
        # committed a bean change, and committed a vocabulary change whose entry never said RULE-CHANGE, while
        # MODEL.md, the journal template and dmrules all described both as enforced. A garden's FIRST commit —
        # germination, which has no HEAD to compare against — is exempt: nothing in it was decided by anyone yet.
        if 'log/journal.md' in staged and _git('rev-parse', '--verify', '-q', 'HEAD')[0]:
            if rc and 'RULE-CHANGE' not in jdiff:
                errors.append(f"RULE-CHANGE staged ({', '.join(rc)}) but the staged journal entry never says RULE-CHANGE — "
                              f"a change to the law is logged DISTINCTLY. Put the word RULE-CHANGE in the entry.")
            for _p in sc:
                _id = os.path.basename(_p)[:-3] if _p.endswith('.md') else _p
                if not re.search(r'(?<![\w-])' + re.escape(_id) + r'(?![\w-])', jdiff):
                    errors.append(f"{_p}: staged, but the staged journal entry never names it — write '{_id}' "
                                  f"(or [[{_id}]]) in the entry, so the record says WHICH bean changed")
            if '(fill in' in jdiff:
                errors.append("the staged journal entry still contains '(fill in' — a template field was left "
                              "unfilled; say who ratified the change and why before committing")
            # THE HEADING IS A POSITION IN TIME (10.0). Only headings this commit ADDS: history is never rewritten.
            _hp = JOURNAL.get('heading_pattern')
            if _hp:
                for _h in (l for l in jdiff.splitlines() if l.startswith('## ')):
                    if not re.match(_hp, _h):
                        errors.append(f"journal heading '{_h[:70]}' is not a position in time — write "
                                      f"{JOURNAL.get('heading_form')}, read from the clock (e.g. "
                                      f"`date '+%Y-%m-%d %H:%M%:z'`), not typed from memory")
        for p in staged:
            if not (p.startswith(DOCUMENTISH) or p.endswith(FRONT_MATTER_DOCS)):
                continue
            cur = _staged_text(p)
            if cur is None:
                continue                              # deleted in the index
            head_fm, _hb = dmparse.split_front_matter(cur)
            if head_fm is None:
                errors.append(f"{p}: STAGED content has no front-matter fences — refusing to commit a "
                              f"destroyed document"); continue
            try:
                now = dmparse.loads(head_fm)
                assert isinstance(now, dict)
            except Exception as e:
                errors.append(f"{p}: STAGED content does not parse ({e}) — refusing to commit a broken "
                              f"document"); continue
            prev_text = _head_text(p)
            if prev_text is None:
                continue                              # new file: nothing to lose
            prev_head, _pb = dmparse.split_front_matter(prev_text)
            try:
                prev = dmparse.loads(prev_head) if prev_head else None
            except Exception:
                prev = None
            if not isinstance(prev, dict):
                continue
            lost = [k for k in prev if k not in now]
            unmentioned = [k for k in lost if k not in jdiff]
            if unmentioned:
                errors.append(f"{p}: staged edit REMOVES top-level {unmentioned} and the staged journal "
                              f"entry does not mention {'it' if len(unmentioned) == 1 else 'them'} — "
                              f"say why in log/journal.md, or restore what the edit dropped")
            # ...and the case a top-level check CANNOT see: the key survives while its SUBTREE is gutted.
            # This is what dmsafe catches at write time, and dmsafe is opt-in — it protects only the
            # writes someone remembered to route through it. Measured over 35 commits: flat leaf-loss is
            # routine (61 edits, median 6% of leaves) and would be noise, while a gutted subtree occurred
            # ZERO times. So that is the signal, and the comparison is dmsafe's own rather than a copy.
            for k in prev:
                if k not in now:
                    continue
                la, lb = dmsafe.leaf_paths(prev[k]), dmsafe.leaf_paths(now[k])
                gutted = (len(la) >= 3 and not (lb - {''})) or (len(la) >= 6 and len(lb) <= len(la) * 0.2)
                if gutted and k not in jdiff:
                    errors.append(f"{p}: staged edit GUTS '{k}' — {len(la)} recorded value(s) reduced to "
                                  f"{len(lb)}, while the key itself survives so a top-level check cannot "
                                  f"see it. Name '{k}' in the staged journal entry if that is intended.")
            # a bean whose human body was emptied is unreadable on paper (Rule 6), and no commit in this
            # garden's history has ever done it — so requiring it costs nothing and closes the last gap.
            if p.startswith('beans/'):
                _sb = dmparse.split_front_matter(cur)[1]
                if not (_sb or '').strip():
                    errors.append(f"{p}: staged edit leaves the bean with NO human body (Rule 6: it must "
                                  f"read on paper). Restore it, or the document is only machine-legible.")


# ---- a bean the semantic merge left UNCLEAN (MERGE.md §10) ------------------------------------------
# "an unresolved conflict COMMITS (lossless capture) but the seed is marked unclean — the gate WARNS,
# never hard-fails." It never warned: nothing outside dmmerge.py had ever mentioned `merge_open`, so a
# merge that captured a real disagreement landed in history with no signal but a `status:` value. That
# was harmless while the driver was unarmed and is not now. A warning, deliberately — blocking would
# violate the losslessness rule that lets the conflict be committed in the first place.
def _conflicted(fm):
    """Top-level keys whose value is a conflict record the merge driver wrote."""
    return sorted(k for k, v in fm.items() if _is_conflict(v))


def check_unclean_merge():
    for _b, _fm in ALL_FM.items():
        _held = _conflicted(_fm)
        if _fm.get('merge_open'):
            _paths = _fm.get('merge_conflicts') or []
            _at = ', '.join(map(str, _paths)) or 'an unrecorded path'
            warns.append(f"{_b}: left UNCLEAN by a semantic merge — {len(_paths)} unresolved conflict(s) at "
                         f"{_at}. Both values are kept; a human picks one, then clears merge_open and "
                         f"merge_conflicts."
                         + (f" The value is still a conflict record at: {', '.join(_held)}." if _held else ""))
        elif _held:
            # No `merge_open`, yet a value is a conflict record. Nothing declared this, so nothing captured
            # it: either the marker was cleared while the values were left, or the document was mangled.
            # Undeclared is the whole difference — MERGE.md §10 protects a DECLARED capture, not a silent one.
            errors.append(f"{_b}: holds an unresolved merge at {', '.join(_held)} with no `merge_open: true` "
                          f"to declare it. A captured conflict warns and may commit; an undeclared one is a "
                          f"document nobody is answering for. Restore the marker, or pick a value.")



def drawn_edges():
    """term -> {(space, target id)} over EVERY edge the vocabulary declares.

    Deliberately WIDER than `TARGETS_OF`, which sees only a term whose own value is a mapping with a
    `bean`: this walks `schema_edges()`, so an edge reached through an entry or a pointer field counts
    too, and one drawn under `owned_by[legal].owner` is credited to `owned_by`.

    The two phase-3 plies that need it want DIFFERENT slices — one wants bean targets to look up, the
    other only wants to know which relations were drawn at all, mappings included — so each filters
    here at its own call site. Building the walk twice, once per slice, is what let the difference sit
    unstated in two loops that looked like copies of each other.

    A relation with a MALFORMED target still registers its key: it was drawn, whatever it hit. Its
    target is left out of the set, because a non-string id is unhashable and the link pass owns that
    error already — the same reason `_row` refuses to hand a conflict record to a dict lookup.
    """
    out = {}
    for (_is_bean, _base), (_fm, _b) in docs.items():
        for _space, _tgt, _field, _sect in schema_edges(_fm):
            _drawn = out.setdefault(_sect.split('[')[0], set())
            if isinstance(_tgt, str):
                _drawn.add((_space, _tgt))
    return out


# ============================== PHASE 3 — the plies the corpus already justifies ==============================
# Seven checks the vocabulary declares and the gate did not run. Each is a WARNING for one cycle: Part B
# says a signal earns enforcement with evidence, and this garden has already promoted one on fixture
# evidence and had to withdraw it. The journal entry that promotes any of these must carry what it found.


def check_acyclic_per_relation():
    """`schema.dag` per relation — the merged walk cannot say WHICH relation cycled.

    `check_acyclic` walks one graph merged from every dag-declared relation, so its error has to name
    all five. A cycle inside ONE relation is a different and more serious fact than a cycle that only
    exists once five relations are superimposed, and the merged walk cannot tell them apart.
    """
    for _rel in sorted(DAG_TERMS):
        _g = {}
        for (_ib, _base), (_fm, _b) in docs.items():
            for _space, _tgt, _field, _sect in schema_edges(_fm):
                if _sect == _rel and _space == 'bean' and isinstance(_tgt, str):
                    _g.setdefault(_base, []).append(_tgt)
        for _trail in _cycles(_g):
            warns.append(f"cycle in '{_rel}' alone: {' -> '.join(_trail)} — a relation "
                         f"declared acyclic (VOCAB {_rel}.schema.dag) contains a cycle by itself")


def check_inverse_completeness():
    """`inverse_of` in BOTH directions — the existing ply only walks one.

    It checks that A.term -> B implies B.inv -> A. The mirror case, B.inv -> A with no A.term -> B, is
    the same drift seen from the other end and nothing looked for it.
    """
    for _term, _sch in SCHEMAS.items():
        _inv, _card = _inverse_of(_sch)
        if not _inv or _card != 'one-to-one':
            # MANY-TO-ONE HAS NO MIRROR TO CHECK. Many instances point at one type, and the type cannot
            # point back at all of them through a single mapping. Enforcing it warned nine times about a
            # rule that was unsatisfiable from the day it was written (log/pending.md,
            # `inverse-of-assumes-a-bijection`, operator-ratified 2026-08-03).
            continue
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean or not isinstance(_fm.get(_inv), dict):
                continue
            _tgt = _fm[_inv].get('bean')
            if not _tgt or (True, _tgt) not in docs:
                continue                              # dangling target is reported by link integrity
            _fwd = docs[(True, _tgt)][0].get(_term)
            if not (isinstance(_fwd, dict) and _fwd.get('bean') == _base):
                warns.append(f"{_base}: {_inv} -> '{_tgt}', but {_tgt}.{_term} does not point back to "
                             f"'{_base}' — the mirror of VOCAB {_term}.schema.inverse_of, unchecked "
                             f"until now")


def check_target_obligation_widened():
    """`required_on_targets_of` over EVERY declared edge, not only direct mapping refs.

    `TARGETS_OF` is built from `fm[term]` being a mapping with a `bean` — which misses every edge that
    lives inside an ENTRY or a pointer field. `schema_edges()` already yields all of them, and it is the
    same graph the link pass resolves, so the narrow set was a second and smaller answer to one question.
    """
    _wide = {_rel: {_t for _s, _t in _e if _s == 'bean'} for _rel, _e in drawn_edges().items()}
    for _term, _sch in SCHEMAS.items():
        _rt = _sch.get('required_on_targets_of')
        if not _rt:
            continue
        for _tgt in sorted(_wide.get(_rt, set()) - TARGETS_OF.get(_rt, set())):
            if (True, _tgt) not in docs:
                continue
            if not docs[(True, _tgt)][0].get(_term):
                warns.append(f"{_tgt}: is the target of a {_rt} edge and carries no {_term} — reached "
                             f"through an entry or pointer field, which the narrow target set never saw "
                             f"(VOCAB {_term}.schema.required_on_targets_of)")


def _termination_hint(term, bean):
    """The line that would terminate a chain at `bean`, when the vocabulary pins that bean's form — read from
    the kind's `ownership_form`, the nature's crown branch, and the term's own terminal forms, naming none."""
    fm = ALL_FM.get(bean) or {}
    if (KINDS.get(fm.get('kind')) or {}).get('ownership_form') != 'crown':
        return ''
    one_of = (SCHEMAS.get(term) or {}).get('entry_one_of') or []
    if 'crown' in one_of:
        branch = next((r.get('crown') for r in (registry('natures') or [])
                       if isinstance(r, dict) and r.get('nature') == fm.get('nature')), None)
        return f". A kind:{fm.get('kind')} bean states its own: {term}: {{ legal: {{ crown: {branch} }} }}" if branch else ''
    if 'self' in one_of:
        return f". A kind:{fm.get('kind')} bean answers for itself: {term}: {{ legal: {{ self: true }} }}"
    return ''


def check_chain_termination():
    """MODEL.md: "every chain terminates there". The gate only checked that no chain LOOPS.

    A chain that simply stops — a bean whose owner names a bean that carries no ownership of its own —
    is neither a cycle nor a termination. It is a dangling claim, and it read as fine.

    AN ERROR SINCE 2026-09-17 (human-ratified). It was a warning here while the pre-commit hook's
    test/fast.py refused the same chain, so a new garden was told "0 error(s)" and then had its commit
    refused. One rule, one severity: the gate now says what the hook always enforced, and names the line to
    write when the bean the chain stops at is of a kind whose form is pinned (a person states the crown).
    """
    for _term, _sch in SCHEMAS.items():
        if not on_walk(_sch) or not _sch.get('entry_one_of'):
            continue
        # THE TERM SAYS WHICH FORMS END A CHAIN: `entry_one_of` offers the forms and `entry_ref_fields`
        # names the ones that point at another bean, so the difference IS the terminal set. Listed by hand
        # here (as ('external','crown','self')) and differently in the hook's fast subset (which accepted
        # `contract`), one rule had two answers, and the vocabulary's — `contract` is a ref, so a chain
        # through it continues — was neither of them.
        _terminal = set(_sch['entry_one_of']) - set(_sch.get('entry_ref_fields') or [])
        if not _terminal:
            continue
        _alt = (_sch.get('alt_form') or {}).get('key')
        for (_is_bean, _base), (_fm, _b) in docs.items():
            if not _is_bean:
                continue
            _seen, _at, _hops = set(), _base, 0
            while _at and _hops < 50:
                _node = ALL_FM.get(_at, {}).get(_term)
                if not isinstance(_node, dict):
                    if _at != _base:
                        errors.append(f"{_base}: its {_term} chain reaches '{_at}', which carries no "
                                      f"{_term} at all — the chain neither terminates nor loops "
                                      f"(MODEL.md: every chain terminates){_termination_hint(_term, _at)}")
                    break
                if _alt and _alt in _node:
                    _nxt = (_node[_alt] or {}).get('bean') if isinstance(_node[_alt], dict) else None
                elif any(f in _terminal for _facet in _node.values()
                         if isinstance(_facet, dict) for f in _facet):
                    break                                        # a facet terminates outside or at the axiom
                else:
                    # WHICH FIELD CARRIES THE CHAIN ONWARD is the term's `entry_ref_fields`, not two facet
                    # key names written here — the same declaration the terminal set above is derived from.
                    _refs = _sch.get('entry_ref_fields') or []
                    _nxt = next((( _f.get(_r) or {}).get('bean')
                                 for _f in _node.values() if isinstance(_f, dict)
                                 for _r in _refs if isinstance(_f.get(_r), dict)), None)
                if _at in _seen:
                    break                                        # the acyclic ply owns cycles
                _seen.add(_at)
                _at, _hops = _nxt, _hops + 1


def check_relation_occupancy():
    """A declared relation no bean instantiates is a blind region, exactly as an unoccupied enum is.

    The reverse gate accounts for every VALUE a term declares. It does not account for the terms that
    ARE relations: the vocabulary can offer an edge nothing has ever drawn, and nothing asks why.

    ONLY THE GARDEN'S OWN RELATIONS (2026-09-17, human-ratified). A garden accounts for the positions IT
    declares — the rule already recorded for Tier-0 vacancies. Warning about every Tier-0 relation a garden
    has not drawn yet greeted a newly germinated garden with nine warnings about edges a small estate may
    never need, and taught it on day one that warnings are noise. Those are information, and
    `bin/dmreview.py` lists them.
    """
    _used = set(drawn_edges())        # every space, mappings included: an edge drawn is an edge drawn
    for _term, _sch in SCHEMAS.items():
        if not (_sch.get('ref_fields') or _sch.get('entry_ref_fields')):
            continue
        if _term in TIER0_TERMS:
            continue
        if _term not in _used:
            warns.append(f"declared relation '{_term}' is drawn by no bean — either it wants an "
                         f"occupant or it wants a vacancy with a reason (the reverse gate's rule, "
                         f"applied to relations rather than to values)")


# `check_asserted_vs_defaulted_occupancy` STOOD HERE and is deleted (ratified 2026-08-03). It existed to
# report the gap between stated and defaulted occupancy while the reverse gate still counted defaults as
# occupants — a second mechanism watching the first one be wrong. Now that occupancy IS statement, the gap
# it reported cannot open: a position nothing states is simply unoccupied, and `vacancies:` is where an
# unoccupied position accounts for itself. Keeping both would be the two-mechanisms-for-one-rule that the
# entry-form change on 2026-08-03 already deleted a ply for.


# ============================== THE PLIES, IN ORDER ==============================
# Execution order used to be wherever a paragraph happened to sit in this file, and it was correct BY
# ACCIDENT: `ALL_FM` was assigned at line 487 and read at 369, so any reordering raised NameError and the
# dependency was discovered rather than declared. This is the same order, written down, with the reason
# each ply cannot move earlier. A new ply is added here, not wedged between two paragraphs.
PLIES = (
    (check_local_additions,
     "a local addition the standard already carries — named as that, before anything else reads the enum"),
    (check_vocab_enum_drift,
     "the vocabulary must agree with itself before anything is judged by it"),
    (check_schema_language,
     "a construct the language does not declare is a rule nothing reads — said before any term is interpreted"),
    (check_merge_identity,
     "a list term's merge identity must name fields its entries carry — the same self-agreement, for merging"),
    (check_value_types,
     "the value types the schemas name are declared in the law"),
    (check_law_extents,
     "an extent the LAW itself writes is judged by the same rule as one on a bean"),
    (check_aspect_sanity,
     "an aspect is a closed figure — check the figure before using its positions"),
    (check_extends_pin,
     "which law is in force; everything downstream is judged under it"),
    (build_docs,
     "loads every document — `docs`, `bean_ids`, `map_ids`. Every ply below reads them"),
    (check_duplicate_keys,
     "reads the raw node graph, because the parsed `docs` above have already lost the first value"),
    (check_undeclared_keys,
     "needs `docs`; judged under the terms the pin put in force"),
    (check_id_space_collision,
     "needs both id spaces built"),
    (check_identity_capsule,
     "builds `est_owner` for the ply after it"),
    (check_establishing_anchor_dedup,
     "consumes `est_owner`"),
    (build_all_fm_and_targets,
     "`ALL_FM` and `TARGETS_OF` — read by check_entry and by the term loop"),
    (check_terms,
     "the interpreter: every schema rule, per document"),
    (check_facet_parity,
     "the two arcs of the ownership loop must carry the same facets"),
    (check_inverse_relations,
     "a convenience edge may not drift from the fact it mirrors"),
    (check_vacancy_reasons_declared,
     "sets `VACANCY_REASONS`, which the reverse gate below reads"),
    (check_reverse_gate,
     "every rule must be passed by the objects, or declared vacant with a reason"),
    (check_link_integrity,
     "builds `dep_graph` while resolving every edge"),
    (check_acyclic,
     "walks the `dep_graph` the ply above built"),
    (check_duplicate_authoritative_ip,
     "one owner per address"),
    (check_single_owner_of_a_fact,
     "the same long value stated authoritatively in two beans"),
    (build_staged_constants,
     "`DOCUMENTISH`, `LAW_DOCS`, `FRONT_MATTER_DOCS` — LAW_DOCS is derived from `standing`, so it needs ALL_FM"),
    (check_staged_state,
     "the commit-time half: it reads the index, and refuses if it cannot"),
    (check_unclean_merge,
     "reports a captured conflict, or refuses an undeclared one"),
    (check_acyclic_per_relation,
     "PHASE 3 (warn): names WHICH relation cycled; the merged walk above cannot"),
    (check_inverse_completeness,
     "PHASE 3 (warn): the mirror direction of inverse_of, which the ply above does not walk"),
    (check_target_obligation_widened,
     "PHASE 3 (warn): needs TARGETS_OF built, and widens it to every declared edge"),
    (check_chain_termination,
     "a chain that stops is neither a cycle nor a termination (an error since 2026-09-17: the hook refused it already)"),
    (check_relation_occupancy,
     "PHASE 3 (warn): the reverse gate's rule applied to the relations the GARDEN declares"),
)

def main():
    """Run every ply in the declared order, report, and set the exit status.

    Under `if __name__ == '__main__'` so that IMPORTING this file cannot run the gate or kill the
    process: `test/golden.py` spawns it as a subprocess for every negative case it checks, which is
    the only way to observe a gate whose verdict is `sys.exit`, and a suite that wanted to call one
    ply directly had no way to do it. (The vocabulary above still loads at import — it is what the
    module IS, and the same refusal-over-fallback rule governs it either way.)
    """
    for _ply, _why in PLIES:
        _ply()
    # ONE FINDING, ONE LINE. Several plies can reach the same fact by different walks — one broken ownership edge
    # printed the same cycle four times — and a repeated line reads as four problems.
    warns[:] = list(dict.fromkeys(warns))
    errors[:] = list(dict.fromkeys(errors))
    for w in warns:  print("WARN ", w)
    for e in errors: print("ERROR", e)
    print(f"\n{_product()}: {len(docs)} docs, {len(errors)} error(s), {len(warns)} warning(s)")
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
