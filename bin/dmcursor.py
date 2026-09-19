#!/usr/bin/env python3
"""dmcursor — a pointer that carries the attention its target requires.

MEASURE, THEN ACT, made first-class. dmsafe applies that discipline to a WRITE; this applies it to the
step before: deciding what to look at, and knowing what must be held in mind while looking.

A cursor points at a being (or at a FILE, resolved back to whichever being owns it) and carries:

  POSITION   what it points at, and how that being is classed
  MEASURED   what is already known and still TRUE — cached analyses with their staleness verified against
             live sources, and which trees may be walked at all. This is the efficiency: the answer to
             "must I read this?" is usually NO, and the cache says so with evidence rather than hope.
  ATTENTION  what must be attended to before touching it: capabilities forbidden or required, edges that
             are impossible or in breach, safety notes, open questions.
  INHERITED  the same, gathered along EVERY CHAIN the vocabulary declares acyclic — habitat, dependency,
             composition, ownership. A token running on a host inherits that host's constraints (a VPS
             that cannot send mail directly means nothing running on it can either), and a being inherits
             from what it DEPENDS ON and from the whole it is PART OF. Those directions are DERIVED from
             `schema.dag` rather than declared again: a relation that must stay acyclic is exactly one you
             can walk, and restating that as a direction aspect would let the two disagree.

The attribute set is DYNAMIC (a codebase carries code paths and caches; a host carries capabilities and
habitat) and must be HARMONIC: the gate already refuses an incoherent combination across aspects, and a
cursor reports what survived that check rather than re-deriving it.

Usage:
    python3 bin/dmcursor.py <bean-id>
    python3 bin/dmcursor.py /home/user/src/app/models/invoice.py
"""
import glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmstale                       # the ONE implementation of the staleness verdict
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOLD = (lambda s: f"\033[1m{s}\033[0m") if sys.stdout.isatty() else (lambda s: s)

BEANS = {}
for _f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))) + \
          sorted(glob.glob(os.path.join(ROOT, 'mappings', '*.md'))):
    _h, _b = dmparse.read(_f)
    if _h is None:
        continue
    try:
        _fm = dmparse.loads(_h) or {}
    except Exception:
        continue
    _id = _fm.get('bean') or _fm.get('mapping')
    if _id:
        BEANS[_id] = _fm


def resolve(target):
    """A bean id, or a filesystem path resolved back to the bean whose code_paths COVER it.

    The reverse lookup is the point: you are about to touch a file, and the question is which being owns
    it and what that being requires you to know. Longest matching path wins, so an own-source tree beats
    the framework tree it sits beside.

    THE DECLARED PATH IS A POSITION, NOT A LITERAL PATH, since std-vocab 11.0 (place): `code_paths` now
    carry `root:<name>/<rel>` or `<host>:<path>`, and a bare absolute path names no machine. This lookup
    compared the argument against the raw string, so after a garden migrated its positions NOTHING
    resolved: `dmcursor /home/user/tree/models/x.py` answered "no bean points at it — nothing in the
    garden claims it" about a file a bean plainly claims. CHECKLIST Part D's first instruction is to
    point a cursor at the file you are about to touch, so this half of the tool was dead alongside the
    staleness half. `dmstale.resolve_here` already knows both forms and which host this is; ask it.
    """
    if target in BEANS:
        return target, None
    ap = os.path.abspath(target)
    best, best_len, covering = None, -1, None
    for b, fm in BEANS.items():
        for cp in (fm.get('code_paths') or []):
            pos = str(cp.get('path', ''))
            if not pos:
                continue
            here = dmstale.resolve_here(pos)
            # A position this host does not hold cannot cover a file on this host. Falling back to the
            # raw string would re-create the pre-11.0 behaviour of matching another machine's tree by
            # coincidence of spelling, which is the whole defect `root:` was introduced to end.
            if not here:
                continue
            if (ap == here or ap.startswith(here.rstrip('/') + '/')) and len(here) > best_len:
                best, best_len, covering = b, len(here), cp
    return best, covering


def dag_relations():
    """{term: schema} for the chains attention travels along — DERIVED, never declared a second time.

    A relation that must stay ACYCLIC is exactly a relation you can walk without looping, and the
    vocabulary already says which those are: a term on a WALK aspect (`schema.dag`, 9.2). A direction aspect would restate a fact the
    model already holds, and a fact stated twice is a fact that can disagree with itself."""
    std = dmparse.loads(dmparse.read(os.path.join(ROOT, 'seed', 'std-vocab.md'))[0]) or {}
    loc = dmparse.loads(dmparse.read(os.path.join(ROOT, 'VOCAB.md'))[0]) or {}
    terms = (list(std.get('terms') or [])
             + [t for p in (std.get('profiles') or {}).values() for t in (p.get('terms') or [])]
             + list(loc.get('local_terms') or []))
    # 9.2: the key that places a term on a walk is DATA, read from the sequence aspects that declare one
    # (`term_key`), not a name written here; `dag` is simply the one such key the standard declares today.
    keys = {a['term_key'] for a in (list(std.get('aspects') or []) + list(loc.get('aspects') or []))
            if isinstance(a, dict) and a.get('term_key')}
    return {t['term']: t['schema'] for t in terms if any((t.get('schema') or {}).get(k) is True for k in keys)}


def targets(fm, term, sch):
    """Every bean a relation points at — WHICH sub-keys hold a ref is read from the schema (`ref_fields`,
    `entry_ref_fields`, `alt_form.ref_fields`), not listed here. The gate resolves edges from exactly
    those declarations, so a cursor that hardcoded its own list would walk a different graph than the one
    the gate checks."""
    node = fm.get(term)
    if node is None:
        return []
    fields = list(sch.get('ref_fields') or []) + list((sch.get('alt_form') or {}).get('ref_fields') or [])
    entry_fields = list(sch.get('entry_ref_fields') or [])
    out = []

    def refs(n, keys):
        for k in keys:
            it = n if k == 'self' else (n.get(k) if isinstance(n, dict) else None)
            if isinstance(it, dict) and it.get('bean'):
                out.append(it['bean'])

    refs(node, fields)
    entries = node.values() if isinstance(node, dict) else (node if isinstance(node, list) else [])
    for e in entries:
        if isinstance(e, dict):
            refs(e, entry_fields or ['self'])
    return out


def chain(bean, term, sch):
    """Walk one relation from `bean`. Acyclicity is the vocabulary's guarantee, so a seen-set is only
    belt-and-braces against a document the gate has not yet seen."""
    out, seen, frontier = [], {bean}, [bean]
    while frontier:
        nxt = []
        for b in frontier:
            for t in targets(BEANS.get(b, {}), term, sch):
                if t not in seen and t in BEANS:
                    seen.add(t); out.append(t); nxt.append(t)
        frontier = nxt
    return out


def attention_of(bean):
    """What a being requires you to attend to. Returns (capabilities, edges, notes)."""
    fm = BEANS.get(bean, {})
    caps = []
    for cap, e in (fm.get('capabilities') or {}).items():
        perm = e.get('permission', 'permitted')
        feas = e.get('feasibility', 'possible')
        if perm in ('forbidden', 'required'):
            caps.append((cap, perm, feas, e.get('why', ''), e.get('by')))
    edges = []
    for term in ('depends_on', 'consumes'):
        node = fm.get(term)
        items = node.items() if isinstance(node, dict) else enumerate(node or [])
        for slot, e in items:
            if isinstance(e, dict) and e.get('necessity') in ('impossible', 'contingent'):
                edges.append((term, slot, e.get('bean'), e['necessity']))
    notes = [str(n) for n in ((fm.get('details') or {}).get('safety') or [])]
    return caps, edges, notes


def main(target):
    bean, covering = resolve(target)
    if not bean:
        print(f"no bean points at {target!r} — nothing in the garden claims it")
        return 2
    fm = BEANS[bean]
    print(BOLD(f"cursor -> {bean}") + f"   {fm.get('kind')} · {fm.get('nature')}"
          + (f" · living in {(fm.get('lives_in') or {}).get('bean')}" if fm.get('lives_in') else ''))
    print(f"  {fm.get('title', '')}")
    if covering:
        print(f"\n  resolved from a FILE: covered by code_paths {covering.get('path')} "
              f"(role {covering.get('role')}, scan_policy {covering.get('scan_policy')})")

    # ---- MEASURED: what is known and still true --------------------------------------------------
    print("\n" + BOLD("MEASURED") + "  — what is already known, and whether it still holds")
    cps = fm.get('code_paths') or []
    for cp in cps:
        pol = cp.get('scan_policy')
        verdict = "WALK IT" if pol == 'index' else ("DO NOT WALK — read by summary" if pol == 'reference-only'
                                                    else "structure only")
        # THE POSITION AND, WHERE IT RESOLVES, THE LITERAL PATH. A `root:` position is what the ledger
        # declares and what merges; the path is what the reader has to type. Printing only the position
        # would hand a reader `root:<some-name>` and leave them to look up what it means on this machine,
        # which is the work this tool exists to save.
        _here = dmstale.resolve_here(str(cp.get('path') or ''))
        _where = f"  ->  {_here}" if _here and _here != cp.get('path') else ""
        print(f"  path   {cp.get('path')}{_where}\n         role {cp.get('role')} · {pol} -> {verdict}")
    cache = fm.get('analysis_cache') or {}
    if not cache:
        print("  cache  none — this being has no recorded analysis; reading is unavoidable")
    # THE VERDICT IS ASKED OF dmstale, NOT RE-DERIVED HERE. This block used to carry its own, and it
    # knew only `git-head:<sha>` — the spelling std-vocab 11.0 replaced with `<repo>@<sha>`. After a
    # garden migrated its keys, every entry fell through to UNKNOWN and this tool answered "unverifiable
    # here" about analyses dmstale could verify in the same minute. CHECKLIST Part D opens by sending a
    # reader HERE and then tells them to trust a FRESH measurement, so a cursor that can no longer say
    # FRESH silently withdraws the offer and every tree gets re-read. One rule, one implementation.
    for ctype, e in sorted(cache.items()):
        state, detail = dmstale.verdict(e)
        print(f"  cache  {ctype:22} {state:8} -> " +
              ("USE IT, do not re-derive" if state == 'FRESH' else
               "RE-ANALYSE, then refresh the entry" if state == 'STALE' else
               "not on this host — a fact about THIS MACHINE, not about the analysis"
               if state == 'NOT-HERE' else "unverifiable: " + detail))
        if state == 'FRESH' and e.get('summary_ref'):
            print(f"         reads: {e.get('summary_ref')}")

    # ---- ATTENTION: what must be held in mind ----------------------------------------------------
    caps, edges, notes = attention_of(bean)
    print("\n" + BOLD("ATTENTION") + " — required before touching it")
    if not (caps or edges or notes):
        print("  none recorded on this being")
    for cap, perm, feas, why, by in caps:
        risk = " <-- LIVE RISK: only the rule prevents it" if (perm, feas) == ('forbidden', 'possible') else (
               " (already prevented elsewhere)" if (perm, feas) == ('forbidden', 'impossible') else (
               " <-- UNENFORCED: nothing holds it in place" if (perm, feas) == ('required', 'contingent') else ''))
        print(f"  {perm.upper():9} {cap}{risk}" + (f"   [by {by[:40]}]" if by else ''))
        print(f"            {why[:150]}")
    for term, slot, tgt, nec in edges:
        print(f"  {nec.upper():9} {term}.{slot} -> {tgt}")
    for n in notes[:4]:
        print(f"  note      {n[:150]}")

    # ---- INHERITED: attention gathered along the habitat chain ------------------------------------
    print("\n" + BOLD("INHERITED") + " — along every chain the vocabulary declares acyclic")
    any_inherited = False
    for term, sch in dag_relations().items():
        walked = chain(bean, term, sch)
        if not walked:
            continue
        shown = False
        for h in walked:
            hcaps, hedges, _hn = attention_of(h)
            for cap, perm, feas, why, by in hcaps:
                if not shown:
                    print(f"  via {term}: {' -> '.join([bean] + walked)}"); shown = True
                any_inherited = True
                print(f"    {h}: {perm.upper()} {cap}" + (f" [by {by[:36]}]" if by else ''))
                print(f"        {why[:140]}")
            for t2, slot, tgt, nec in hedges:
                if not shown:
                    print(f"  via {term}: {' -> '.join([bean] + walked)}"); shown = True
                any_inherited = True
                print(f"    {h}: {nec.upper()} {t2}.{slot} -> {tgt}")
    if not any_inherited:
        print("  nothing constraining inherited from any chain")
    print()
    return 0


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__.strip().splitlines()[-3].strip()); sys.exit(2)
    sys.exit(main(sys.argv[1]))
