#!/usr/bin/env python3
"""dmmerge — daftar semantic merge (MERGE.md).

Merges N gardens (each a dir of beans, or a list of bean dicts) into canonical SEEDS via:
  identity resolution (union-find over ESTABLISHING anchors)
  -> per-field CRDT lattice join (union -> reduce to antichain under a per-key subsumption order)
  -> canonical JSON projection (JCS-lite: sorted keys, NFC strings, normalized values, no now())
  -> SHA-256 fingerprint.
By construction the merge is lossless (every value + its contributing gardens preserved),
order-agnostic (commutative+associative — everything sorted canonically), and idempotent.

CLI: dmmerge.py <garden_dir> [<garden_dir> ...]   # prints seeds + fingerprint
Library: merge_gardens(list_of_beanlists) -> {seed_id: seed_dict}, canonical_fingerprint(seeds)
"""
import sys, os, re, glob, json, hashlib, unicodedata, ipaddress, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import yaml

# P4 (2026-08-02, human-ratified): identity is established by the `establishing` BOOLEAN on the anchor,
# not by its `class`. `class` survives only as a hint at WHY. These agreed for as long as they did only
# because every anchor in the corpus it was built against happened to carry both keys consistently — a coincidence of the
# corpus, not a property of the model. Absent flag == not establishing, exactly as the gate reads it.
def _est(a):
    return isinstance(a, dict) and a.get('establishing') is True
# THE SOURCE RANK IS DECLARED, NOT KEPT HERE. Until 2026-09-20 this line was a dict of four numbers — the only
# place the order `generated-by-tool < inferred < observed < asserted-by-human` was written down. MODEL.md and
# MERGE.md state the GUARD (an inferred value never overrides an asserted-by-human one); the rank that
# implements it, and that also decides which src a value agreed on by several gardens keeps, was a constant in
# a tool. `provenance_src` declares it now, the way `anchor_authority` has always declared its own, and
# `_src_rank` reads it the way `_authority_rank` does.
DEFAULT_SRC = 'observed'     # what a bean that states no src is read as; the one owner of that default

# ---------- normalization ----------
def norm(v):
    if isinstance(v, str):
        s = unicodedata.normalize('NFC', v).strip()
        try:
            return str(ipaddress.ip_address(s))      # canonical IP form if it is one
        except ValueError:
            return s
    # A DATE IS A PER-TYPE CANONICALIZER CASE (MERGE.md §6), and it was missing. PyYAML resolves an
    # unquoted `2026-08-02` to datetime.date, which json cannot serialise — so the canonical projection
    # raised on any bean carrying an absolute date, which Rule 6 asks for everywhere. ISO 8601 is the
    # canonical form: it round-trips, sorts correctly, and is what the beans already spell.
    if isinstance(v, (datetime.date, datetime.datetime)):
        return v.isoformat()
    # AND IT MUST RECURSE. A fact's value is very often a nested capsule (`details.registration.expires`),
    # so canonicalising only the top level left every nested date, IP and unnormalised string untouched —
    # which is what actually made the live corpus unmergeable. `norm` is the canonicaliser for a VALUE,
    # and a value is a tree.
    if isinstance(v, dict):
        return {norm(k): norm(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [norm(x) for x in v]
    return v

# ---------- load ----------
def load_garden(path, gid):
    beans = []
    for f in sorted(glob.glob(os.path.join(path, 'beans', '*.md'))):
        fm = dmparse.loads(dmparse.read(f)[0] or '') or {}
        beans.append({'garden': gid, 'id': fm.get('bean', os.path.basename(f)[:-3]), 'fm': fm})
    return beans

# ---------- identity resolution ----------
def est_anchors(fm):
    out = set()
    for a in (fm.get('identity') or {}).get('anchors') or []:
        if _est(a):
            out.add((a['key'], dmparse.compare_anchor(TERMS.values(), a['key'], norm(a['value']))))
    return out

def components(beans):
    parent = {}
    def find(x):
        parent.setdefault(x, x); r = x
        while parent[r] != r: r = parent[r]
        while parent[x] != r: parent[x], x = r, parent[x]
        return r
    def union(a, b): parent[find(a)] = find(b)
    nodes = {(b['garden'], b['id']): b for b in beans}
    for n in nodes: find(n)
    anchor_node = {}
    for n, b in nodes.items():
        for anc in est_anchors(b['fm']):
            if anc in anchor_node: union(n, anchor_node[anc])
            else: anchor_node[anc] = n
    comps = {}
    for n, b in nodes.items():
        comps.setdefault(find(n), []).append(b)
    return list(comps.values())

# ---------- merge facets: DATA, not code ----------
# MERGE.md §5: "`⊑`, cardinality, and tie-break live in the VOCAB `merge:` facet so MERGE stays a thin
# driver and conflict logic is *not* duplicated in code." It said so from the beginning; this module
# hardcoded a guess instead, and the guess covered three sections of a bean out of forty-eight keys.
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_terms():
    """Every vocabulary term from both tiers, by name. Read the same way the gate reads them, so the
    merge and the gate cannot disagree about what a term is."""
    out = {}
    for path in (os.path.join(ROOT, 'seed', 'std-vocab.md'), os.path.join(ROOT, 'VOCAB.md')):
        if not os.path.exists(path):
            continue
        fm = dmparse.loads(dmparse.read(path)[0] or '') or {}
        for t in (list(fm.get('terms') or [])
                  + [t for p in (fm.get('profiles') or {}).values() for t in (p.get('terms') or [])]
                  + list(fm.get('local_terms') or [])):
            if isinstance(t, dict) and t.get('term'):
                out.setdefault(t['term'], {}).update(t)
    return out


ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TERMS = load_terms()
# The subsumption orders, read from the law rather than known by name. No fallback: an empty registry
# means no key is ordered, which is a visible loss of merging rather than a silent one.
def load_leaf_orders():
    path = os.path.join(ROOT, 'seed', 'std-vocab.md')
    if not os.path.exists(path):
        return []
    fm = dmparse.loads(dmparse.read(path)[0] or '') or {}
    return [r for r in (fm.get('leaf_orders') or []) if isinstance(r, dict)]


LEAF_ORDERS = load_leaf_orders()


def load_system_patterns():
    """{anchor system: its ONE canonical pattern}, read from the law. A leaf order may apply to every value
    that is a position in a system (9.3), so the order follows what a value IS, not what its key is called."""
    path = os.path.join(ROOT, 'seed', 'std-vocab.md')
    if not os.path.exists(path):
        return {}
    fm = dmparse.loads(dmparse.read(path)[0] or '') or {}
    return {r['system']: r.get('pattern') for r in (fm.get('anchor_systems') or [])
            if isinstance(r, dict) and r.get('system') and r.get('pattern') not in (None, 'none')}


SYSTEM_PATTERNS = load_system_patterns()
UNDECLARED = set()          # keys merged by shape because no term declares a facet — reported, not hidden


def facet(key, val, member=False):
    """(cardinality, order) for a value at `key`. The vocabulary decides; shape is the fallback.

    A term declaring `merge: {cardinality: multi, order: by-<field>}` is a COLLECTION whose members merge
    independently — by-facet, by-capability, by-cache-type, by-key over a mapping; by-path, by-bean over a
    list of entries. `single` merges the whole value as one atom, so two gardens disagreeing about it is a
    real conflict rather than a silent pick.

    A MEMBER is never governed by a term that merely shares its name. Terms describe top-level keys; the
    keys inside `owns`/`details` are facts, which Phase 6 of the design ratified by refusing to declare them.
    Looking members up by bare name worked only while no term happened to collide: std-vocab@7.0 added the
    top-level `roles` term (a list of entries, multi/by-key), and every `owns.roles: [mail]` silently
    stopped being a set and merged as one atom — three gardens' roles became a conflict instead of a union."""
    m = None if member else (TERMS.get(key) or {}).get('merge')
    if isinstance(m, dict) and m.get('cardinality'):
        return m['cardinality'], m.get('order', 'none')
    # SHAPE FALLBACK. Honest defaults for a key no term describes: a mapping is a collection of members
    # (which is what `owns`, `attributes` and `details` always were), a list unions, a scalar is atomic.
    if isinstance(val, dict):
        return 'multi', 'by-key'
    if isinstance(val, list):
        return 'set', 'none'
    return 'single', 'none'


# Every order this module can APPLY, named once. `leaf_order` used to whitelist a different set from the one
# `subsumes` implements: `prefix` and `subsumes` were accepted and do nothing, while `instant` and
# `containment` (std-vocab 9.3 and 11.0) were implemented and could not be declared on a TERM — a term saying
# `merge: {order: instant}` was silently unordered. One list, read by both.
ORDERS = ('cidr', 'version', 'instant', 'containment', 'ranked')


def ranked_order(key):
    """A declared RANK — `merge: {order: "a<b<c"}` — as a list, or None. The vocabulary has carried one since
    `anchor_authority` was declared (`scanned<operator-asserted<external`) and NOTHING READ IT: measured
    2026-09-20, `leaf_order('authority', …)` answered `none`. A law the code ignores is worse than a rule in
    code, because the vocabulary says it is in force."""
    m = (TERMS.get(key) or {}).get('merge') or {}
    o = str(m.get('order') or '')
    return [p.strip() for p in o.split('<')] if '<' in o else None


def leaf_order(key, val):
    """The subsumption order for a LEAF value. The term's own declaration wins; otherwise the `leaf_orders`
    registry decides, by key name or by the anchor system a value is written in."""
    if ranked_order(key):
        return 'ranked'
    m = (TERMS.get(key) or {}).get('merge')
    if isinstance(m, dict) and m.get('order') in ORDERS:
        return m['order']
    for rule in LEAF_ORDERS:
        sfx = rule.get('suffix')
        if (sfx and str(key).endswith(sfx)) or key in (rule.get('exact') or []):
            return rule.get('order', 'none')
        for _sys in [rule.get('system')] + list(rule.get('also_systems') or []):
            pat = SYSTEM_PATTERNS.get(_sys)
            if pat and isinstance(val, str) and re.match(pat, val):
                return rule.get('order', 'none')
    return 'none'


def members(key, order, val):
    """Split a `multi` value into {member-key: member-value}. A mapping keys by its own keys; a list of
    entries keys by the field the `order` names (`by-path` -> entry['path']), so two gardens describing
    the same path merge that path rather than unioning two near-identical entries."""
    if isinstance(val, dict):
        return {str(k): v for k, v in val.items()}
    if isinstance(val, list):
        ident = dmparse.identity_fields(order)
        out = {}
        for i, e in enumerate(val):
            if not ident:
                mk = canonical(norm(e))
            else:
                # NO FALLBACK TO THE WHOLE ENTRY. Keying a member by its content when its identity field was
                # missing is how `roles`, declared by-key over entries with no `key`, merged one role with two
                # different `why`s into two roles and said nothing (fixed in std-vocab@8.0). A field marked
                # `?` may be absent, and then its absence is part of the identity.
                missing = [f for f, may_lack in ident if not may_lack
                           and not (isinstance(e, dict) and e.get(f) is not None)]
                if missing:
                    raise ValueError(f"'{key}' entry {i} has no {', '.join(missing)}, which its identity "
                                     f"'{order}' requires — refused rather than matched by its whole content. "
                                     f"Give the entry the field, or mark it `?` in the vocabulary if its "
                                     f"absence is a legitimate state.")
                vals = [e.get(f) for f, _ in ident]
                # One required field keeps the plain string key every earlier seed was written with.
                mk = str(vals[0]) if len(ident) == 1 and not ident[0][1] else canonical(norm(vals))
            if mk in out:
                # A duplicate inside ONE garden's value is as lossy as a dropped event: the first entry
                # simply disappeared, with nothing said. Refuse — the driver turns any exception into a
                # refusal that leaves the file untouched and lets a human resolve it.
                raise ValueError(f"'{key}' has two entries keyed '{mk}' under order '{order}' — one "
                                 f"would silently overwrite the other. Give them distinct "
                                 f"{order[3:] if str(order).startswith('by-') else 'keys'}, or "
                                 f"merge them by hand.")
            out[mk] = e
        return out
    return {'': val}

_CIVIL = re.compile(r'^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2})(?:\.(\d{1,3}))?)?'
                    r'(Z|[+-]\d{2}:\d{2})?)?$')


def _civil(s):
    """A calendar reading as (its components, its offset in minutes or None). The components are the parts
    actually WRITTEN: `2026-09-19` has three, `2026-09-19 22:50+03:00` five. Fewer parts is a coarser
    reading, never a reading at midnight."""
    m = _CIVIL.match(str(s))
    if not m:
        return None, None
    y, mo, d, h, mi, sec, ms, off = m.groups()
    parts = [int(y), int(mo), int(d)] + [int(x) for x in (h, mi, sec) if x is not None]
    if ms is not None:
        parts.append(int(ms.ljust(3, '0')))
    if off is None:
        return parts, None
    return parts, 0 if off == 'Z' else (1 if off[0] == '+' else -1) * (int(off[1:3]) * 60 + int(off[4:6]))


def _instant_contains(a, b):
    """True when calendar reading `a` CONTAINS the finer reading `b`: `2026-09-19` contains
    `2026-09-19 22:50+03:00`. The `time` aspect's order is PARTIAL, so every other pair is unordered: two
    readings that do not nest are a disagreement for a person, never silently ordered. A reading with an
    offset contains only readings that state one, compared in its own offset; a reading with none is a
    civil date in an unstated frame and is compared with `b` as `b` was written."""
    pa, oa = _civil(a)
    pb, ob = _civil(b)
    if pa is None or pb is None or len(pb) <= len(pa):
        return False
    if oa is not None:
        if ob is None:
            return False
        full = (pb + [0, 0, 0, 0])[:7]
        t = datetime.datetime(full[0], full[1], full[2], full[3], full[4], full[5], full[6] * 1000)
        t += datetime.timedelta(minutes=oa - ob)
        pb = [t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond // 1000][:len(pb)]
    return pb[:len(pa)] == pa


def _place_contains(a, b):
    """True when place position `a` CONTAINS the finer position `b`: a tree contains a subtree, in the SAME
    system and under the same host or logical root. `host-a:/home/user` contains `host-a:/home/user/tree` and
    contains nothing on another host — two trees at the same path on two machines are not the same place, which
    is the defect this order exists to keep visible (13 such paths in the garden it grew in)."""
    ha, _, pa = str(a).partition(':')
    hb, _, pb = str(b).partition(':')
    if not pa or not pb or ha != hb:
        return False
    sa, sb = pa.rstrip('/'), pb.rstrip('/')
    sep = '\\' if (sa[1:3] == ':\\' or '\\' in sa) else '/'
    return sb.startswith(sa + sep)


def subsumes(a, b, order, key=None):     # True if a is subsumed by (more-general-or-equal) b, b != a
    if a == b: return False
    if order == 'ranked':
        rank = ranked_order(key) or []
        return a in rank and b in rank and rank.index(a) < rank.index(b)
    if order == 'containment':
        return _place_contains(a, b)
    if order == 'instant':
        return _instant_contains(a, b)
    if order == 'version':
        return str(b).startswith(str(a))                     # "AlmaLinux 9" ⊑ "AlmaLinux 9.8"
    if order == 'cidr':
        try:
            na, nb = ipaddress.ip_network(str(a), False), ipaddress.ip_network(str(b), False)
            return na != nb and na.subnet_of(nb)
        except Exception:
            return False
    return False

def _apply_prov(path, items):
    """Stamp each item with the provenance its own bean recorded for this path, where there is one.

    The bean's default `provenance.src` is the fallback. A merged bean's default is
    `generated-by-tool`, so without this every value it carries would be re-asserted as the merger's.
    """
    out = []
    for it in items:
        # UNFOLD FIRST. A captured conflict is several values, and the record is keyed by VALUE — looking
        # it up before unfolding compares against `{conflict: [...]}` as a whole and never matches.
        carried = set()
        for one, _p in _unfold(it['value']):
            rec = _prov_lookup(it.get('fm') or {}, path, one)
            e = dict(it, value=one)
            if rec:
                if rec.get('src'):
                    e['src'] = rec['src']
                if rec.get('seen_in'):
                    e['_origin'] = list(rec['seen_in'])
            carried.add(canonical(norm(one)))
            out.append(e)
        # A record may name a value the DOCUMENT no longer shows — a subsumed one. Re-contributing it
        # lets the antichain absorb it again and reach the same seed a one-shot merge would.
        for rec in ((it.get('fm') or {}).get('provenance_of') or {}).get(path) or []:
            if not isinstance(rec, dict) or canonical(norm(rec.get('value'))) in carried:
                continue
            e = dict(it, value=rec.get('value'))
            if rec.get('src'):
                e['src'] = rec['src']
            if rec.get('seen_in'):
                e['_origin'] = list(rec['seen_in'])
            out.append(e)
    return out


def merge_key(key, items):
    """Merge one TOP-LEVEL key across the gardens that recorded it.

    `multi` splits into members and merges each independently — so two gardens that each know a different
    facet of `owned_by`, a different capability, or a different cached analysis end up with both, while
    two that disagree about the SAME member get a conflict on that member alone. `single` and `set` fall
    through to the leaf join. This is what makes the merge generic: nothing here names a term."""
    if not isinstance((TERMS.get(key) or {}).get('merge'), dict):
        # Recorded at the TOP LEVEL only. The keys INSIDE `owns`/`details` are facts, not terms, and are
        # not expected to declare anything; listing them would bury the real gap in three hundred names.
        UNDECLARED.add(key)
    card, order = facet(key, items[0]['value'])
    if card != 'multi':
        return merge_field(key, _apply_prov(key, items))
    per = {}
    for it in items:
        for mk, mv in members(key, order, it['value']).items():
            per.setdefault(mk, []).append({'value': mv, 'src': it['src'], 'garden': it['garden'],
                                           'fm': it.get('fm')})
    return {'members': {mk: merge_field(mk, _apply_prov(f"{key}.{mk}", its), member=True)
                        for mk, its in sorted(per.items())},
            'keyed_by': order}


_SRC_RANK = None


def _src_rank(src):
    """Where a fact's `src` sits in the rank `provenance_src` declares. A vocabulary that declares none is
    REFUSED rather than read as "all equal": with no rank the provenance guard silently stops guarding, and a
    merge that cannot tell an inference from an assertion is worse than one that does not run."""
    global _SRC_RANK
    if _SRC_RANK is None:
        _SRC_RANK = ranked_order('provenance_src')
        if not _SRC_RANK:
            raise SystemExit("dmmerge: the vocabulary declares no rank for `provenance_src` "
                             "(merge: {order: \"a<b<c\"}) — refusing to merge without the provenance guard")
    return _SRC_RANK.index(src if src in _SRC_RANK else DEFAULT_SRC)


_AUTHORITY_RANK = None


def _authority_rank(anchor):
    """Where an anchor's authority sits in the rank the vocabulary declares. An anchor that states none
    ranks lowest: a value whose weight nobody recorded cannot outweigh one whose weight was."""
    global _AUTHORITY_RANK
    if _AUTHORITY_RANK is None:
        _AUTHORITY_RANK = ranked_order('anchor_authority') or []
    a = anchor.get('authority')
    return _AUTHORITY_RANK.index(a) if a in _AUTHORITY_RANK else -1


def _rank_only(old, new):
    """True when two records of one anchor differ ONLY in their authority — the case the declared rank is
    for. Any other disagreement is still a disagreement, and is recorded rather than ranked away."""
    return {k: v for k, v in old.items() if k != 'authority'} == {k: v for k, v in new.items() if k != 'authority'}


def merge_field(key, items, member=False):
    """items: [{'value','src','garden'}]. Returns a canonical, lossless merged LEAF."""
    # A captured conflict read back off disk is not one value — it is the several it stands for. See
    # `_unfold`: treating the record as an atom is what made the rendered form not closed under the join.
    _expanded = []
    for it in items:
        for one, _p in _unfold(it['value']):
            _expanded.append(dict(it, value=one))
    items = _expanded
    kind, _ = facet(key, items[0]['value'], member)
    order = leaf_order(key, items[0]['value'])
    if kind == 'set':
        vals, seen = set(), set()
        for it in items:
            for e in (it['value'] if isinstance(it['value'], list) else [it['value']]):
                vals.add(json.dumps(norm(e), sort_keys=True, ensure_ascii=False))
            seen.update(it.get('_origin') or [it['garden']])
        # Sort the CANONICAL STRINGS, not the parsed values. Sorting parsed values raises on a set whose
        # members are mappings (`standing`, `code_paths`) and orders numbers by their digits when a set is
        # heterogeneous; a canonical-string sort is total over every JSON type. The antichain branch below
        # has always sorted this way, so this also makes the two paths agree.
        return {'set': [json.loads(x) for x in sorted(vals)], 'seen_in': sorted(seen)}
    # single-valued: dedup identical values (keep highest-authority src + all contributing gardens)
    by_val = {}
    for it in items:
        k = json.dumps(norm(it['value']), sort_keys=True, ensure_ascii=False)
        e = by_val.setdefault(k, {'value': norm(it['value']), 'src': it['src'], 'seen_in': set()})
        e['seen_in'].update(it.get('_origin') or [it['garden']])
        if _src_rank(it['src']) > _src_rank(e['src']): e['src'] = it['src']
    vals = list(by_val.values())
    # antichain: drop v dominated by w, but an asserted-by-human value is never dropped by a lower src
    keep, swallowed = [], {}
    for v in vals:
        dom = None
        for w in vals:
            if w is v: continue
            if subsumes(v['value'], w['value'], order, key):
                # THE GUARD: a value at the TOP of the declared rank is never dropped by one below it. The top is
                # `asserted-by-human` because the vocabulary says so, not because this line names it.
                _rv, _rw = _src_rank(v['src']), _src_rank(w['src'])
                if not (_rv == len(_SRC_RANK) - 1 and _rw < _rv):
                    dom = w; break
        if dom is None:
            keep.append(v)
        else:
            # MERGE.md invariant 1: "even an auto-subsumed value is preserved in provenance
            # (recoverable)". It was being dropped outright, which is the linchpin guard — an `inferred`
            # value may never override an `asserted-by-human` one — losing the evidence it rests on.
            swallowed.setdefault(canonical(dom['value']), []).append(
                {'value': v['value'], 'src': v['src'], 'seen_in': sorted(v['seen_in'])})
    for e in keep:
        _sub = swallowed.get(canonical(e['value']))
        if _sub:
            e['subsumed'] = sorted(_sub, key=canonical)
    for e in keep: e['seen_in'] = sorted(e['seen_in'])
    keep.sort(key=lambda e: json.dumps(e['value'], sort_keys=True, ensure_ascii=False))
    if len(keep) == 1:
        return keep[0]
    return {'conflict': keep}

# ---------- merge a component into a seed ----------
def slug(s):
    return ''.join(c if c.isalnum() else '-' for c in str(s).lower()).strip('-')

# The only keys NOT merged as facts, because each is machinery rather than a claim about the object:
#   bean       — a garden-local filename; it becomes an `aka`
#   identity   — the merge KEY itself; anchors union, aka union (see below)
#   provenance — per-garden metadata about the RECORD, not about the object. Kept per garden rather than
#                merged, because two gardens having different provenance is not a disagreement about the
#                world; merging it would manufacture a conflict on every fused seed.
def _unfold(v):
    """A value read back off disk, as the members it actually asserts.

    A CAPTURED CONFLICT IS NOT AN ATOM. `resolved()` renders an unresolved disagreement as
    `{conflict: [a, b]}`, and re-reading that as a single opaque value is what made the rendered form
    not closed under the join: merging it against `a` produced `{conflict: [a, {conflict: [a, b]}]}`,
    and again, and again — at-least-once delivery did not merely fail to converge, it DIVERGED. Reading
    the record back as the two values it stands for makes re-merging a no-op instead.

    This does not replace the architectural rule (a cursor should recompute from retained originals
    rather than fold events into rendered beans). It removes the unbounded growth if anything does.
    """
    if isinstance(v, dict) and isinstance(v.get('conflict'), list) and len(v) == 1:
        out = []
        for m in v['conflict']:
            inner = m.get('value') if isinstance(m, dict) and 'value' in m else m
            out.extend(_unfold(inner))
        return out
    return [(v, None)]


# ...and the merge driver's OWN state. `merge_open` and `merge_conflicts` describe a merge in progress,
# not the estate: merging them as facts made a re-merged bean carry `merge_conflicts: {seen_in: [acc],
# set: [owns.site]}` as though which paths were once conflicted were a property of the world. They are
# rewritten from scratch by whoever renders the merge, which is the only place that knows them.
STRUCTURAL = {'bean', 'mapping', 'identity', 'provenance', 'merge_open',
              'merge_conflicts', 'provenance_of'}


def provenance_of(node, prefix=''):
    """The merged tree as {dotted-path: [{value, src, seen_in}]} — every leaf, not only the contested.

    Uniformity is the whole point. The previous attempt recorded provenance only where a conflict had
    forced a record to exist, so a value that arrived as the accumulator's own kept the accumulator's
    name — and that partial preservation made incremental merging depend on which garden happened to be
    read first. A leaf is a leaf.
    """
    out = {}
    if not isinstance(node, dict):
        return out
    if 'members' in node:
        for mk, mv in node['members'].items():
            out.update(provenance_of(mv, f"{prefix}.{mk}" if prefix else mk))
        return out
    if 'conflict' in node:
        out[prefix] = [{'value': c['value'], 'src': c.get('src'),
                        'seen_in': sorted(c.get('seen_in') or [])} for c in node['conflict']]
        return out
    if 'set' in node:
        out[prefix] = [{'value': node['set'], 'src': None, 'seen_in': sorted(node.get('seen_in') or [])}]
        return out
    if 'value' in node:
        recs = [{'value': node['value'], 'src': node.get('src'),
                 'seen_in': sorted(node.get('seen_in') or [])}]
        # A SUBSUMED VALUE LIVES ONLY HERE. `resolved()` writes the winner, so "AlmaLinux 9" absorbed by
        # "AlmaLinux 9.8" leaves no trace in the document — and MERGE.md invariant 1 requires even an
        # auto-subsumed value to stay recoverable. Recording it is what lets a re-read put it back.
        for s in (node.get('subsumed') or []):
            recs.append({'value': s.get('value'), 'src': s.get('src'),
                         'seen_in': sorted(s.get('seen_in') or []), 'subsumed': True})
        out[prefix] = recs
    return out


def _prov_lookup(fm, path, value):
    """The recorded provenance for one value at one path, or None if this bean carries no record."""
    rec = (fm.get('provenance_of') or {}).get(path)
    if not isinstance(rec, list):
        return None
    cv = canonical(norm(value))
    for r in rec:
        if isinstance(r, dict) and canonical(norm(r.get('value'))) == cv:
            return r
    return None


def merge_component(comp):
    """Merge one identity-component into a seed, GENERIC over top-level keys.

    This used to gather `owns`/`attributes`/`details` and seven named keys, and drop everything else — 31
    of the corpus's 48 top-level keys, including `nature`, both ownership arcs, `capabilities` and the
    whole relation algebra. Nothing here names a term now: what a key IS comes from its vocabulary
    `merge:` facet, and a key no term describes is merged by shape and reported in UNDECLARED."""
    fields, anchors, anchor_conflicts = {}, {}, set()
    aka, gardens, provs = set(), set(), {}

    for b in comp:
        fm = b['fm']
        prov = fm.get('provenance') or {}
        src = prov.get('src', DEFAULT_SRC)
        gardens.add(b['garden']); aka.add(b['id'])
        provs[b['garden']] = norm(prov)      # carries an `as_of` date; canonicalise it like any value

        for k, v in fm.items():
            if k in STRUCTURAL or v is None:
                continue
            # a fact may carry its own provenance record {value, src, ...}, which outranks the bean's
            if isinstance(v, dict) and 'value' in v and 'src' in v:
                fields.setdefault(k, []).append({'value': v['value'], 'src': v['src'], 'garden': b['garden'],
                                                 'fm': fm})
            else:
                for _one, _prov in _unfold(v):
                    _it = {'value': _one, 'src': (_prov or {}).get('src') or src, 'garden': b['garden'], 'fm': fm}
                    if (_prov or {}).get('seen_in'):
                        _it['_origin'] = list(_prov['seen_in'])
                    fields.setdefault(k, []).append(_it)

        for a in (fm.get('identity') or {}).get('anchors') or []:
            if isinstance(a, dict):
                # Compared — and STORED — in the vocabulary's compare form where it declares one, so two gardens
                # spelling one serial differently fuse into one anchor instead of recording a disagreement.
                _ak = (a['key'], dmparse.compare_anchor(TERMS.values(), a['key'], norm(a['value'])))
                _new = {'key': a['key'],
                        'value': _ak[1] if dmparse.anchor_compare_form(TERMS.values(), a['key']) else norm(a['value']),
                        'establishing': a.get('establishing') is True, 'class': a.get('class')}
                # AUTHORITY SURVIVES THE MERGE (2026-09-20). `anchor_authority` means "how much weight an
                # anchor's value carries on merge" and declares a rank — and the merge dropped the attribute
                # on the floor, so the rank had nothing to weigh and no reader could tell a SCANNED anchor
                # from one a person asserted. Two gardens that disagree about it resolve by the DECLARED
                # rank, which is the vocabulary deciding rather than arrival order.
                if a.get('authority') is not None:
                    _new['authority'] = a['authority']
                _old = anchors.get(_ak)
                if _old is not None and _old != _new and _rank_only(_old, _new):
                    _new = max((_old, _new), key=_authority_rank)
                    _old = None if _new is not _old else _old
                    anchors[_ak] = _new
                    continue
                if _old is not None and _old != _new:
                    # TWO GARDENS DISAGREE ABOUT WHAT THIS ANCHOR IS. Overwriting made the seed id, the
                    # id_basis and auto-merge eligibility depend on ITERATION ORDER, which breaks the
                    # hard determinism invariant with no queue involved at all. Resolve deterministically
                    # — the canonically-least record wins, so the result is the same whichever garden
                    # arrives first — and RECORD the disagreement, because whether an anchor establishes
                    # identity is class F and no algebra may decide it quietly.
                    # SORTED, not [old, new]: the arrival order is not a fact about the estate,
                    # and recording it made the fingerprint depend on which garden was read first
                    # — the very determinism this fix exists to restore.
                    anchor_conflicts.add(canonical(sorted([_old, _new], key=canonical)))
                    _new = min((_old, _new), key=canonical)
                anchors[_ak] = _new
        for a2 in (fm.get('identity') or {}).get('aka') or []:
            aka.add(a2)

    merged = {k: merge_key(k, its) for k, its in sorted(fields.items())}

    # `kind` selects the seed-id prefix, so it is resolved here as well as carried as a fact. A component
    # whose members disagree about kind used to emit a LIST, which `dmcheck` cannot resolve; it is a
    # conflict like any other now, and the id takes the lexicographically-least for determinism.
    kinds = sorted({b['fm'].get('kind') for b in comp if b['fm'].get('kind')})

    # Canonical seed id = kind-slug of the lexicographically-least ESTABLISHING anchor value. Where a
    # component has NO establishing anchor it falls back to the least garden-local id — and that fallback
    # is NOT identity-bearing: MERGE.md is explicit that garden-local ids may legitimately collide, and
    # id != identity. `id_basis` records which of the two produced this id, because the two are
    # indistinguishable by looking at the string and mean entirely different things.
    est = sorted(str(v['value']) for v in anchors.values() if _est(v))
    base = slug(est[0]) if est else slug(sorted(aka)[0])
    seed_id = f"{kinds[0]}-{base}" if kinds else base
    return {
        'seed': seed_id,
        'kind': kinds[0] if len(kinds) == 1 else (kinds or None),
        'identity': dict({'anchors': [anchors[k] for k in sorted(anchors)], 'aka': sorted(aka),
                          'id_basis': 'anchor' if est else 'garden-local'},
                         # Only present when two gardens genuinely disagreed about what an anchor IS.
                         # The resolution above is deterministic so the merge converges; this is the
                         # part that must not be silent, because whether an anchor establishes identity
                         # is class F and belongs to the operator, not to an algebra.
                         **({'anchor_conflicts': [json.loads(c) for c in sorted(anchor_conflicts)]}
                            if anchor_conflicts else {})),
        'provenance': {g: provs[g] for g in sorted(provs)},
        'facts': merged,
        'gardens': sorted(gardens),
    }

# ---------- vocabulary reconciliation: merging BEANS is only half a merge ----------
# dmmerge converged two gardens' data while their TYPE SYSTEMS stayed divergent, so a merged corpus could
# contain a bean whose kind the receiving garden does not declare — checked by nobody, because each
# garden's gate only ever saw its own half. Promoting kinds to Tier-0 shrank this; it did not close it.
# A garden's law is its Tier-0 PIN, the profiles it opted into, and its local overlay. All three must
# reconcile before the beans mean anything.

def std_fm_of(path):
    """A garden's Tier-0 law, read from the one path `law_carrier` names."""
    p = os.path.join(path, 'seed', 'std-vocab.md')
    return (dmparse.loads(dmparse.read(p)[0] or '') or {}) if os.path.exists(p) else {}


def load_vocab(path, gid=None):
    """One garden's declared law."""
    def head(f):
        p = os.path.join(path, f)
        return (dmparse.loads(dmparse.read(p)[0] or '') or {}) if os.path.exists(p) else {}
    v, g = head('VOCAB.md'), head('GARDEN.md')
    return {
        'garden': gid or g.get('garden') or v.get('vocab') or os.path.basename(path.rstrip('/')),
        'pin': v.get('extends'), 'garden_pin': g.get('extends'),
        'profiles': sorted(v.get('extends_profiles') or []),
        'terms': {t['term']: t for t in (v.get('local_terms') or []) if isinstance(t, dict) and t.get('term')},
        'kinds': {k['kind']: k for k in (v.get('local_kinds') or []) if isinstance(k, dict) and k.get('kind')},
    }


def merge_vocabs(vocabs):
    """Reconcile N gardens' law. Returns (merged, blocking, conflicts).

    BLOCKING is not a conflict to be recorded and carried — it is a reason the merge should not happen.
    Two gardens pinning different Tier-0 versions are not speaking the same language, and merging their
    beans would apply one garden's law to the other's data. The fix is to move a pin, which is a
    human-ratified rule-change, not something a merge tool may do on someone's behalf.

    A CONFLICT is two gardens defining the SAME local term differently. A term is law; two readings of it
    cannot both hold, and picking one silently would re-classify beans in the garden that loses."""
    blocking, conflicts = [], []

    pins = {}
    for v in vocabs:
        for which in ('pin', 'garden_pin'):
            if v.get(which):
                pins.setdefault(str(v[which]), []).append(f"{v['garden']}/{which}")
    if len(pins) > 1:
        blocking.append("gardens pin DIFFERENT Tier-0 versions — " + "; ".join(
            f"{p} ({', '.join(w)})" for p, w in sorted(pins.items()))
            + ". Move the older pin first: adopting a vocabulary version is a logged rule-change, and "
              "merging across it would validate one garden's beans against the other's law.")

    merged = {'pin': next(iter(pins), None),
              'profiles': sorted({p for v in vocabs for p in v['profiles']}),
              'terms': {}, 'kinds': {}}
    for space in ('terms', 'kinds'):
        for v in vocabs:
            for name, defn in v[space].items():
                prev = merged[space].get(name)
                if prev is None:
                    merged[space][name] = defn
                elif canonical(norm(prev)) != canonical(norm(defn)):
                    conflicts.append(f"local {space[:-1]} '{name}' is defined DIFFERENTLY by the gardens "
                                     f"that declare it — a term is law, so one reading must be ratified")
    # A profile only one garden opted into becomes an obligation for BOTH once merged. That is correct —
    # the beans that need it are now in the corpus — but it is not silent.
    for v in vocabs:
        extra = sorted(set(merged['profiles']) - set(v['profiles']))
        if extra:
            conflicts.append(f"garden '{v['garden']}' had not opted into profile(s) {', '.join(extra)}; "
                             f"the merged garden inherits them, and their obligations, from another")
    return merged, blocking, conflicts


def uncovered(seeds, merged_vocab, std_fm):
    """Kinds and top-level keys the merged corpus USES that the merged law does not DECLARE.

    This is the question the divergence actually raises. Reconciling the vocabularies is the mechanism;
    this is the check that says whether it worked, asked of the merged data rather than of the inputs."""
    kinds = set(k['kind'] for k in (std_fm.get('kinds') or []) if isinstance(k, dict)) | set(merged_vocab['kinds'])

    # THE TERM SET THE MERGED LAW WOULD ACTUALLY ENFORCE: Tier-0 core, plus ONLY the profiles the merged
    # garden opted into, plus the local overlay. Not the module-level TERMS — that one loads every
    # profile unconditionally, because for reading a `merge:` facet opt-in is irrelevant. It is not
    # irrelevant here: built from TERMS, this reported that a garden owed `code_paths` for a profile it
    # had never opted into, which is the precise mistake the profile mechanism exists to prevent.
    defs = {t['term']: t for t in (std_fm.get('terms') or []) if isinstance(t, dict) and t.get('term')}
    for p in merged_vocab['profiles']:
        for t in ((std_fm.get('profiles') or {}).get(p, {}).get('terms') or []):
            defs[t['term']] = t
    defs.update(merged_vocab['terms'])
    terms = set(defs)

    bad_kinds, bad_keys, unmet = set(), set(), set()
    for s in seeds.values():
        skinds = [s['kind']] if isinstance(s['kind'], str) else (s['kind'] or [])
        for k in skinds:
            if k and k not in kinds:
                bad_kinds.add(k)
        bad_keys |= {k for k in s['facts'] if k not in terms}
        # THE OBLIGATION LEG, and the one the divergence actually bites on. A garden that never declared
        # `registration` writes a `domain` bean without it quite legitimately; merged into a garden that
        # DOES declare it required, that bean is suddenly in breach — of a rule it was never subject to.
        # Neither garden's gate could see this, because each only ever validated its own half.
        for name, t in defs.items():
            req = (t.get('schema') or {}).get('required_on_kinds') or []
            if set(skinds) & set(req) and name not in s['facts']:
                unmet.add(f"{s['seed']} (kind {'/'.join(skinds)}) owes '{name}'")
    return sorted(bad_kinds), sorted(bad_keys), sorted(unmet)


def at(seed, path):
    """A merged node by dotted path — `at(s, 'owns.os')`, `at(s, 'owned_by.legal')`. Walks `members`
    transparently, so a caller need not know whether a key is a collection."""
    node = seed['facts']
    for part in str(path).split('.'):
        if isinstance(node, dict) and 'members' in node:
            node = node['members']
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def component_key(comp):
    """A component's identity as its sorted set of (garden, bean-id) members.

    Components PARTITION the node set — every node belongs to exactly one — so two distinct components can
    never share this value. That is what makes it a sound tie-break rather than a hope: uniqueness is a
    property of the partition, not of a hash."""
    return canonical(sorted([b['garden'], b['id']] for b in comp))


def merge_gardens(garden_beanlists):
    """Merge N gardens into seeds keyed by seed id.

    ONE SEED PER COMPONENT, ALWAYS. This used to key the result dict directly by `s['seed']`, and two
    components whose ids both fell back to a garden-local bean id collided on that key — the second
    silently overwrote the first, so two genuinely distinct beings went in and one came out, with the
    other neither merged nor reported. That breaks losslessness (MERGE.md invariant 1) in the one place
    nothing was watching, and it is reachable exactly when identity is weakest.

    A colliding id is disambiguated by the component's own membership, which is deterministic and
    order-agnostic, so invariant 4a still holds. Anchor-derived ids never collide and are never suffixed,
    so this changes nothing for a garden whose beans carry establishing anchors."""
    beans = [b for lst in garden_beanlists for b in lst]
    made = [(comp, merge_component(comp)) for comp in components(beans)]

    by_id = {}
    for comp, s in made:
        by_id.setdefault(s['seed'], []).append((comp, s))

    seeds = {}
    for sid, group in by_id.items():
        if len(group) > 1:
            for comp, s in group:
                disc = hashlib.sha256(component_key(comp).encode()).hexdigest()[:8]
                s['seed'] = f"{sid}-x{disc}"
                s['identity']['id_collision'] = sid    # what it would have been, so the tie is legible
        for _comp, s in group:
            seeds[s['seed']] = s

    # THE INVARIANT, asserted rather than assumed. Whatever the id scheme, a component must never vanish
    # into another's key. Failing loudly beats returning a garden with a host quietly missing from it.
    if len(seeds) != len(made):
        raise AssertionError(
            f"dmmerge: {len(made)} components produced only {len(seeds)} seeds — ids collided after "
            f"disambiguation. No bean may be dropped; this is a bug, not a merge outcome.")
    return seeds

# ---------- canonical projection + fingerprint (determinism oracle) ----------
def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

def fingerprint(seeds):
    # sorted set of per-seed canonical hashes -> one hash for the whole merged garden
    per = sorted(hashlib.sha256(canonical(s).encode()).hexdigest() for s in seeds.values())
    return hashlib.sha256('\n'.join(per).encode()).hexdigest(), per

# ---------- git merge-driver mode: 3-way merge of ONE bean file ----------
def parse_file(path):
    head, body = dmparse.read(path)          # line-anchored fences (bin/dmparse.py)
    return (dmparse.loads(head or '') or {}), body

def resolved(v, orig=None):
    """A merged node back as a bean value. A conflict keeps EVERY value — losing one to make the file
    parse would be the loss this whole module exists to prevent — and the seed is marked unclean."""
    if not isinstance(v, dict):
        return v
    if 'members' in v:
        out = {mk: resolved(mv) for mk, mv in v['members'].items()}
        # a collection that came in as a LIST goes back as a list, in the members' canonical order
        return list(out.values()) if isinstance(orig, list) else out
    if 'set' in v:
        return v['set']
    if 'conflict' in v:
        return {'conflict': [c['value'] for c in v['conflict']]}
    return v.get('value')


def conflict_paths(node, prefix=''):
    """Every path in the merged tree that holds an unresolved conflict, so the bean can name them."""
    if not isinstance(node, dict):
        return []
    if 'conflict' in node:
        return [prefix]
    if 'members' in node:
        return [p for mk, mv in node['members'].items() for p in conflict_paths(mv, f"{prefix}.{mk}" if prefix else mk)]
    return []


def render_bean(seed, fmA, fmB, bodyA, bodyB):
    """Write the merged component back as a bean, carrying EVERY top-level key either side had.

    The old version wrote ten fixed keys and folded every fact into `owns`, so a merge of two real beans
    returned one stripped of its nature and both ownership arcs. It is driven by the merged tree now, so
    what comes out is what went in."""
    facts = seed['facts']
    conflicts = sorted(p for k, v in facts.items() for p in conflict_paths(v, k))
    st = [(fm.get('identity') or {}).get('status', 'confirmed') for fm in (fmA, fmB)]

    fm = {'bean': fmA.get('bean') or fmB.get('bean')}
    for k, v in sorted(facts.items()):
        fm[k] = resolved(v, fmA.get(k, fmB.get(k)))
    fm['identity'] = {'status': 'provisional' if 'provisional' in st else 'confirmed',
                      'anchors': seed['identity']['anchors'], 'aka': seed['identity']['aka']}
    fm['provenance'] = {'src': 'generated-by-tool', 'by': 'dmmerge', 'as_of': 'merged',
                        'from': seed['provenance']}
    # PER-LEAF PROVENANCE, BESIDE THE VALUES AND NEVER INSIDE THEM. `owns.os: AlmaLinux 9.8` stays what a
    # human reads; this block says who said it. Inlining would turn every scalar into {value, src,
    # seen_in} and make the document unreadable, which Rule 6 forbids more strongly than it asks for
    # provenance. Without it, a merged bean read back can only be re-merged as the READER's assertion —
    # every value restamped `generated-by-tool`, which disarms the guard that an `inferred` value may
    # never override an `asserted-by-human` one, because the declared src rank is what enforces that.
    _pv = {}
    for k, v in sorted(facts.items()):
        _pv.update(provenance_of(v, k))
    if _pv:
        fm['provenance_of'] = _pv
    if conflicts:
        # `status` is itself a `single`-cardinality merged term, so writing the unclean marker into
        # it made the driver's own flag collide with the algebra on the same key: the next event's
        # `status: active` turns `status` into a conflict, merge_in_place then tries to write the scalar
        # back, and dmsafe rolls the whole edit away. The marker lives on keys nothing merges.
        fm['merge_conflicts'] = conflicts
        fm['merge_open'] = True

    front = yaml.safe_dump(fm, sort_keys=True, allow_unicode=True, default_flow_style=False)
    body = "\n<!-- merged by dmmerge (ours) -->\n" + (bodyA or '').strip() + \
           "\n\n<!-- theirs -->\n" + (bodyB or '').strip() + "\n"
    return "---\n" + front + "---\n" + body


def _inline_comment(line):
    """The comment part of one YAML line, or '' — the `#` that STARTS a comment, never one in a value.

    Splitting on the first `#` would cut a value in half: this garden has `#` inside quoted values (a
    URL fragment, a shell line quoted inside a safety note), and half a value promoted to a comment is
    a silently corrupted document. So the scan tracks quoting, and applies YAML's own rule that a `#`
    opens a comment only at the start of a line or after whitespace — `a#b` is the value `a#b`.
    """
    quote = None
    for i, ch in enumerate(line):
        if quote:
            if ch == quote:
                quote = None
        elif ch in '"\'':
            quote = ch
        elif ch == '#' and (i == 0 or line[i - 1] in ' \t'):
            return line[i:].rstrip('\r\n')
    return ''


def merge_in_place(A, fmA, fmB, bodyB, seed):
    """SURGICAL merge into A's own text: rewrite only the keys that actually changed.

    Rendering the whole bean with `yaml.safe_dump` produced a correct document and destroyed something the
    gate cannot see — the COMMENTS. 42 of this garden's 58 documents carry front-matter comments, 137
    lines of them, and they hold exactly the context that does not fit in a value ("provisioned
    2026-07-30; reputation-clean", "the authoritative MASTER token on this host"). MODEL.md's guardrails
    say it outright: no auto-reformatting, it strips the comments that carry context. A merge driver that
    silently reformats 72% of the corpus is not a merge driver, it is a reformatter with a merge feature.

    So: start from A's bytes and touch only what differs, through `dmsafe` — the same structured-edit
    machinery every other write in this repo goes through, for the same reason. A key both sides agree on
    keeps its text, its comments and its layout exactly."""
    import dmsafe
    changed, added = [], []

    # A leaf legitimately changes SHAPE here — `owns.os` is a scalar on both sides and becomes
    # `owns.os.conflict[0..1]` when they disagree — and dmsafe refuses an undeclared leaf loss, which is
    # exactly why it exists. Every `allow_remove` below is therefore computed narrowly, for the position
    # being written and only when that position actually differs. `lost_keys` re-reads the file
    # afterwards and compares against both inputs, so the guarantee never rests on the declaration.
    def dump(name, val, indent=0):
        """One key as YAML, unwrapped. The default 80-column wrap reflows every long string in the file
        into a different shape with identical content — pure churn in a diff a human has to read."""
        s = yaml.safe_dump({name: val}, sort_keys=True, allow_unicode=True,
                           default_flow_style=False, width=10 ** 6)
        lines = s.rstrip('\n').split('\n')
        # INDENT THE VALUE UNDER ITS KEY. PyYAML emits a block sequence at the SAME column as the key it
        # belongs to — `roles:` then `- relay` both at indent 2. That is legal YAML and it defeats every
        # indentation-based span finder, dmsafe's included: the block looks like it ends at its own first
        # line, so a later edit addressed to a sibling lands inside it and the file stops parsing. Two
        # extra spaces on the continuation lines removes the ambiguity without changing the value.
        return ''.join(' ' * indent + ln + '\n' for ln in lines[:1]) + \
               ''.join(' ' * (indent + 2) + ln + '\n' for ln in lines[1:])

    def keep_comments(dotted, block, indent):
        """Carry the comments in `dotted`'s current span onto the `block` about to replace it.

        THE ONE CASE THE COMMENT GUARANTEE ABOVE DID NOT COVER, and it bit where it costs most. That
        guarantee is about keys the merge does not touch; a key the merge DOES rewrite has its whole
        span replaced, comment included. So `os: "Distro 9.7 (Codename)"   # measured
        2026-08-04; this key said 9.8` became a bare `conflict:` block, and the note recording when
        the value was measured — the provenance of one of the two values a human is now being asked
        to choose between — was deleted at exactly that moment. MERGE.md §10 calls the capture
        LOSSLESS; it was lossy, in the most expensive direction.

        The comment on the key's own line goes back on the key's own line. Comments from INSIDE a
        multi-line span go above the block, at the key's indent: they can no longer sit beside the
        line they annotated, because that line is gone, and a comment moved is recoverable while a
        comment deleted is not. Placed above rather than below so a reader meets the note before the
        value it qualifies.
        """
        try:
            text = open(A, encoding='utf-8').read()
            spans = dmsafe.nested_spans(text, dotted)
        except Exception:
            return block                      # no span to read: nothing to carry, and never a reason to fail
        if len(spans) != 1:
            return block                      # ambiguous; the caller's own expect=1 owns that complaint
        # CHARACTER offsets, not line indices — `nested_spans` converts before returning, and reading
        # them as lines indexes past the end of the file on any bean big enough to matter. Caught by
        # the driver's own refusal, which left the working file untouched exactly as it promises.
        span = text[spans[0][0]:spans[0][1]].splitlines()
        head = _inline_comment(span[0]) if span else ''
        inner = [c for ln in span[1:] if (c := _inline_comment(ln))]
        out = block
        if head:
            first, _, rest = out.partition('\n')
            out = f"{first}   {head}\n{rest}"
        return ''.join(' ' * indent + c + '\n' for c in inner) + out

    def rewrite(dotted, name, old, new, indent, log):
        # TWO GATES, and both are needed. The caller already established that THEIRS differs from ours —
        # that is what makes this position worth merging at all. This is the second: the merged RESULT
        # may still equal ours, and then there is nothing to write. It happens whenever ours already
        # subsumes theirs (we hold the union of the roles they are adding one of), and writing anyway
        # hands dmsafe a block identical to the text it replaces, which it refuses — correctly, since a
        # pattern that matched nothing is how a 'fixed' file silently stays unfixed.
        if old == new:
            return
        gone = [p for p in dmsafe.leaf_paths({name: old})
                if p not in set(dmsafe.leaf_paths({name: new}))]
        prefix = dotted[:-len(name)] if dotted != name else ''
        dmsafe.set_nested(A, dotted, keep_comments(dotted, dump(name, new, indent), indent), expect=1,
                          allow_remove=[prefix + p for p in gone])
        log.append(dotted)

    # ONLY WHAT THEIRS ACTUALLY CHANGED. The test is `A differs from B`, never `A differs from the
    # canonical form` — canonical form is for the fingerprint, not for the working file. Comparing
    # against canon rewrote keys neither side had touched, sorting `extra_ips` and reflowing four
    # paragraphs of safety notes purely because the merge canonicaliser would have. A merge driver that
    # reformats what nobody edited buries the real change in a diff nobody can read.
    for k in sorted(set(fmA) | set(fmB)):
        if k in STRUCTURAL or k not in seed['facts']:
            continue
        if k not in fmB:
            continue                                     # only ours has it — keep ours, verbatim
        if k not in fmA:
            dmsafe.insert_after(A, sorted(fmA)[-1], dump(k, norm(fmB[k]))); added.append(k); continue
        if norm(fmA[k]) == norm(fmB[k]):
            continue                                     # both sides agree — leave ours untouched

        want_k = resolved(seed['facts'][k], fmA[k])
        card, _order = facet(k, fmA[k])
        # A `multi` term merges PER MEMBER, so rewrite per member: replacing the whole block would
        # reformat every sibling and take its comments with it. `owns` alone carries half of this bean's
        # comment lines while only one of its members changed.
        if card == 'multi' and isinstance(fmA[k], dict) and isinstance(want_k, dict) \
                and set(fmA[k]) <= set(want_k):
            for mk in sorted(set(want_k) & set(fmA[k])):
                if norm(fmA[k].get(mk)) == norm((fmB.get(k) or {}).get(mk)):
                    continue
                rewrite(f"{k}.{mk}", mk, norm(fmA[k].get(mk)), want_k[mk], 2, changed)
            # A member only THEIRS has must be inserted, and `dmsafe.insert_after` addresses top-level
            # keys only. Rewriting the block's LAST member as itself-plus-the-additions appends without
            # touching any sibling, so at most one inline comment is at risk instead of all of them.
            fresh = sorted(set(want_k) - set(fmA[k]))
            if fresh:
                anchor = sorted(fmA[k])[-1]
                # the anchor's MERGED value, not ours — the member loop above may have just rewritten it,
                # and re-emitting our original here would quietly undo that.
                keep = want_k[anchor] if anchor in want_k else norm(fmA[k][anchor])
                blk = dump(anchor, keep, 2) + ''.join(dump(m, want_k[m], 2) for m in fresh)
                # the anchor member is REWRITTEN here to append after it, so its comment is at the same
                # risk as any other rewritten key — the comment above says at most one is at risk, and
                # this is the one.
                dmsafe.set_nested(A, f"{k}.{anchor}", keep_comments(f"{k}.{anchor}", blk, 2), expect=1)
                added += [f"{k}.{m}" for m in fresh]
            continue
        rewrite(k, k, norm(fmA[k]), want_k, 0, changed)

    conflicts = sorted(p for k, v in seed['facts'].items() for p in conflict_paths(v, k))
    if conflicts:
        # MERGE.md §10: an unresolved conflict COMMITS (lossless capture) and the bean is marked unclean.
        dmsafe.insert_after(A, 'status', 'merge_conflicts: ' + json.dumps(conflicts) + '\nmerge_open: true\n')

    # theirs' body, appended rather than merged: prose is explicitly outside the determinism guarantee
    # (MERGE.md §6), so it is kept whole for a human instead of being reconciled by a tool.
    if (bodyB or '').strip() and (bodyB or '').strip() not in open(A, encoding='utf-8').read():
        with open(A, 'a', encoding='utf-8') as fh:
            fh.write("\n<!-- theirs -->\n" + (bodyB or '').strip() + "\n")
    return changed, added, conflicts


def lost_keys(fmA, fmB, rendered_fm):
    """Top-level keys present on either side but absent from the rendered result.

    MEASURED, not declared. This replaced a hand-written list of what the driver could carry — a list is a
    claim that goes stale the moment a term is added, while this asks the actual output. It should always
    be empty; the driver refuses if it is not, because overwriting a working file with a bean that lost a
    key is the one outcome a merge must never have."""
    return sorted((set(fmA) | set(fmB)) - set(rendered_fm))


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--file':      # git merge driver: %O %A %B
        _O, A, B = sys.argv[2], sys.argv[3], sys.argv[4]

        # LAW FIRST, ON THIS PATH TOO. The multi-garden CLI below reconciles vocabularies before it
        # touches a bean, and blocks if they cannot be reconciled. This path — the only incremental,
        # one-file-at-a-time one in the repository — never reached that check, so a bean could be merged
        # under a law neither side's gate had ever applied. It cannot compare two gardens' vocabularies
        # (it is handed three blobs of ONE file), so it checks the thing it can see: that the working
        # tree's pin agrees with the vocabulary actually installed. A mismatch means the beans about to
        # be merged are judged by a law this tree does not have.
        try:
            # `std_fm_of` APPENDS seed/std-vocab.md to what it is given, so passing it the file's own path
            # asked for `…/seed/std-vocab.md/seed/std-vocab.md` and always read {} — measured 2026-09-20:
            # this refusal could never fire, on the only incremental merge path there is.
            _std = std_fm_of(ROOT_DIR)
            _loc = dmparse.loads(dmparse.read(os.path.join(ROOT_DIR, 'VOCAB.md'))[0] or '') or {}
            _pin = str((_loc or {}).get('extends') or '')
            _ver = str((_std or {}).get('version') or '')
            if _ver and _pin and _pin != f'std-vocab@{_ver}':
                print(f"dmmerge: REFUSING to merge — this tree pins {_pin} and the installed vocabulary "
                      f"is std-vocab@{_ver}. Merging beans while the law is unsettled converges data "
                      f"that neither gate checked. Reconcile the pin first; the file is untouched.",
                      file=sys.stderr)
                sys.exit(1)
        except SystemExit:
            raise
        except Exception as _e:
            print(f"dmmerge: REFUSING to merge — cannot read this tree's vocabulary ({_e}). "
                  f"There is one path to the law and no fallback.", file=sys.stderr)
            sys.exit(1)
        fmA, bodyA = parse_file(A); fmB, bodyB = parse_file(B)
        bid = fmA.get('bean') or fmB.get('bean')
        seed = merge_component([{'garden': 'ours', 'id': bid, 'fm': fmA},
                                {'garden': 'theirs', 'id': bid, 'fm': fmB}])
        before = open(A, encoding='utf-8').read()
        try:
            changed, added, conflicts = merge_in_place(A, fmA, fmB, bodyB, seed)
            after_fm, after_body = parse_file(A)
        except Exception as e:                             # any structured-edit failure is a refusal
            open(A, 'w', encoding='utf-8').write(before)
            print(f"dmmerge: refusing to merge {bid} — {e}. The file is untouched.", file=sys.stderr)
            sys.exit(1)

        # REFUSE RATHER THAN CLOBBER — and check the RESULT ON DISK rather than trust the code that made
        # it. A driver returning non-zero leaves the file alone and lets git record an ordinary conflict
        # for a human. A driver that writes back a bean missing a key has destroyed the working copy, and
        # the pre-commit gate that would refuse that bean only runs afterwards.
        lost = lost_keys(fmA, fmB, after_fm)
        if lost or not after_body.strip():
            open(A, 'w', encoding='utf-8').write(before)
            why = f"would lose {len(lost)} key(s) ({', '.join(lost)})" if lost else "would lose the body"
            print(f"dmmerge: refusing to merge {bid} — the merged result {why}. "
                  f"Resolve by hand; the file is untouched.", file=sys.stderr)
            sys.exit(1)
        print(f"dmmerge: {bid} — {len(changed)} key(s) rewritten, {len(added)} added, "
              f"{len(conflicts)} conflict(s)" + (f": {', '.join(conflicts)}" if conflicts else "")
              + ". Every untouched key kept its text and its comments.", file=sys.stderr)
        sys.exit(0)                                        # conflicts are captured and marked merge_open
    paths = sys.argv[1:]
    gl = [load_garden(p, os.path.basename(p.rstrip('/'))) for p in paths]

    # LAW FIRST. Merging beans while the type systems diverge converges the data and leaves it
    # unchecked — each garden's gate only ever saw its own half. Reconcile the vocabularies, and stop
    # before touching the beans if they cannot be reconciled.
    vocabs = [load_vocab(p, os.path.basename(p.rstrip('/'))) for p in paths]
    mv, blocking, vconflicts = merge_vocabs(vocabs)
    if blocking:
        print("MERGE REFUSED — the gardens do not share a law:\n  " + "\n  ".join(blocking),
              file=sys.stderr)
        sys.exit(1)

    seeds = merge_gardens(gl)
    bad_kinds, bad_keys, unmet = uncovered(seeds, mv, std_fm_of(paths[0]))
    fp, per = fingerprint(seeds)
    for sid in sorted(seeds):
        print(f"\n=== seed {sid} ===")
        print(canonical(seeds[sid]))
    print(f"\nfingerprint: {fp}  ({len(seeds)} seeds)")
    # A seed whose id came from a garden-local name is NOT identified — say so rather than let the id's
    # shape imply otherwise. Silence here reads as "everything is anchored", which is the wrong default.
    local = sorted(s['seed'] for s in seeds.values() if s['identity'].get('id_basis') == 'garden-local')
    tied = sorted(s['seed'] for s in seeds.values() if s['identity'].get('id_collision'))
    if local:
        print(f"\n{len(local)} seed(s) have a GARDEN-LOCAL id — no establishing anchor, so the id names a "
              f"filename, not an object:\n  " + "\n  ".join(local))
        print("  These are `identity: provisional` by policy and must never be auto-merged; give them an "
              "establishing anchor to identify them.")
    if tied:
        print(f"\n{len(tied)} of those collided with another component and were disambiguated by "
              f"membership (see identity.id_collision for the shared name).")
    # NO SILENT FALLBACK. A key merged by shape rather than by declaration may still be merged WRONGLY —
    # a mapping treated as a collection when it is really one atom, say. Naming them is how the gap gets
    # closed instead of forgotten; each wants a `merge: {cardinality, order}` on its term.
    if UNDECLARED:
        print(f"\n{len(UNDECLARED)} top-level key(s) were merged by SHAPE because no vocabulary term "
              f"declares a `merge:` facet for them:\n  " + ', '.join(sorted(UNDECLARED)))

    # THE OTHER HALF OF THE MERGE. Beans converged above; this says whether the LAW did, and whether the
    # merged law actually covers the merged corpus. A merge that reports only the data is reporting half.
    print(f"\nVOCABULARY — {len(vocabs)} garden(s) reconciled at {mv['pin']}"
          + (f", profiles {', '.join(mv['profiles'])}" if mv['profiles'] else ", no profiles")
          + f", {len(mv['terms'])} local term(s), {len(mv['kinds'])} local kind(s)")
    for c in vconflicts:
        print(f"  RATIFY  {c}")
    if bad_kinds:
        print(f"  UNCOVERED KIND(S): {', '.join(bad_kinds)} — the merged corpus contains beans of a "
              f"kind the merged law does not declare")
    if bad_keys:
        print(f"  UNCOVERED KEY(S): {', '.join(bad_keys)} — used by a bean, declared by no term")
    for u in unmet:
        print(f"  UNMET       {u} — required by the merged law, which the contributing garden had "
              f"not adopted")
    if bad_kinds or bad_keys or unmet:
        print("  The merged garden would NOT pass its own gate. Reconcile before adopting.")
    elif not vconflicts:
        print("  CLEAN — the laws reconcile, and every kind, key and obligation of the merged corpus "
              "is covered by the merged law.")
    sys.exit(1 if (bad_kinds or bad_keys or unmet) else 0)
