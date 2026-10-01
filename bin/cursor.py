#!/usr/bin/env python3
"""cursor — a pointer that carries the attention its target requires.

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

IN A GARDEN OF THE CORE (v1 part 5) the same four are read from statements. A file resolves to the bean whose `be`, as
location, places it (a position in a filesystem system, `root:<name>/…` resolved through this host's roots), and what
the translation kept of it — its role, its scan policy, the analyses cached of it — is read from `details`. What must be
attended to is the bean's figures: a statement `forbidden` or `obligatory`, beside what is `possible`, `impossible` or
`contingent` of the same, and what is `impossible` or `contingent` of what it needs; with the notes `details.safety`
keeps, and the sensitivity the core derives. The chains it inherits along are the ones the core's order holds acyclic
(core/engine.py `ORDERED`): what it is at, what it needs, what it is part of, and who owns it.

Usage:
    python3 bin/cursor.py <bean-id>
    python3 bin/cursor.py /home/user/src/app/models/invoice.py
    (`bin/dmcursor.py`, today's name, runs this too until v1's part 13)
"""
import os, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmgarden  # noqa: E402 — the one garden model: where its documents are
import dmform
import dmstale                       # the ONE implementation of the staleness verdict
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOLD = (lambda s: f"\033[1m{s}\033[0m") if sys.stdout.isatty() else (lambda s: s)

BEANS = {}
for _f in dmgarden.paths(ROOT):
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
    """A bean id, or a filesystem path resolved back to the bean whose LOCATION COVERS it (`located_at`; `code_paths`
    until 29.0, when a code bean's trees became its locations and a framework's tree its own bean's).

    The reverse lookup is the point: you are about to touch a file, and the question is which being owns
    it and what that being requires you to know. Longest matching path wins, so an own-source tree beats
    the framework tree it sits beside.

    THE DECLARED PATH IS A POSITION, NOT A LITERAL PATH, since std-vocab 11.0 (place): a code bean's trees
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
        for cp in (fm.get('located_at') or [] if isinstance(fm.get('located_at'), list) else []):
            pos = str(cp.get('at') or '') if isinstance(cp, dict) else ""
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
    _form = dmform.attribute_form(None, sch)
    fields = dmform.ref_attrs(_form, 'self') + list((_form['alt'] or {}).get('refs') or [])
    entry_fields = dmform.ref_attrs(_form, 'entry')
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
    print(BOLD(f"cursor -> {bean}") + f"   {fm.get('genos')} · {fm.get('nature')}"
          + (f" · living in {(fm.get('lives_in') or {}).get('bean')}" if fm.get('lives_in') else ''))
    print(f"  {fm.get('title', '')}")
    # HOW MUCH HARM IT CAN DO (24.0, step 1): derived by bin/dmpass.py, never stored; special material is named by its
    # path and shown `[special]`, never by its value.
    try:
        import dmpass, dmheld
        _lv, _why = dmpass.sensitivity(fm, dmheld.types_law(dmpass.ROOT))
    except Exception:
        _lv, _why = None, []
    if _lv and _lv != 'none':
        print(f"  sensitivity {_lv}" + (" [special]" if _lv == 'special-category' else '') + (f" — {'; '.join(_why)}" if _why else ''))
    if covering:
        print(f"\n  resolved from a FILE: covered by located_at {covering.get('at')} "
              f"(role {covering.get('role')}, scan_policy {covering.get('scan_policy')})")

    # ---- MEASURED: what is known and still true --------------------------------------------------
    print("\n" + BOLD("MEASURED") + "  — what is already known, and whether it still holds")
    cps = [e for e in (fm.get('located_at') or [] if isinstance(fm.get('located_at'), list) else [])
           if isinstance(e, dict) and e.get('scan_policy')]
    for cp in cps:
        pol = cp.get('scan_policy')
        verdict = "WALK IT" if pol == 'index' else ("DO NOT WALK — read by summary" if pol == 'reference-only'
                                                    else "structure only")
        # THE POSITION AND, WHERE IT RESOLVES, THE LITERAL PATH. A `root:` position is what the ledger
        # declares and what merges; the path is what the reader has to type. Printing only the position
        # would hand a reader `root:<some-name>` and leave them to look up what it means on this machine,
        # which is the work this tool exists to save.
        _here = dmstale.resolve_here(str(cp.get('at') or ''))
        _where = f"  ->  {_here}" if _here and _here != cp.get('at') else ""
        print(f"  path   {cp.get('at')}{_where}\n         role {cp.get('role')} · {pol} -> {verdict}")
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


# ==== A GARDEN OF THE CORE (v1 part 5) ============================================================================
PERMISSION = ('forbidden', 'obligatory')                      # what the rule asks
NECESSITY = ('necessary', 'possible', 'impossible', 'contingent')   # what holds whatever the rule asks
RISK = {('forbidden', 'possible'): " <-- LIVE RISK: only the rule prevents it",
        ('forbidden', 'impossible'): " (already prevented elsewhere)",
        ('obligatory', 'contingent'): " <-- UNENFORCED: nothing holds it in place"}


def runs_core():
    import check                                 # the one reader of a garden's pin (bin/check.py)
    return check.runs_core(check.pin(ROOT))


def _beans(x, G):
    return [v for v in (x if isinstance(x, list) else [x]) if isinstance(v, str) and v in G.beans]


def core_resolve(target, G):
    """A bean id, or a path resolved to the bean whose `be`, as location, holds the longest position covering it."""
    if target in G.beans:
        return target, None
    ap = os.path.abspath(target)
    best, best_len, covering = None, -1, None
    for b in G.beans.values():
        for _i, v, r in b.items:
            if v != 'be' or r.get('as') != 'location' or 'held' in r:
                continue
            for at in (r.get('at') if isinstance(r.get('at'), list) else [r.get('at')]):
                if not isinstance(at, str) or at in G.beans:
                    continue
                tagged = re.match(r'^[a-z][a-z0-9-]*:(.+)$', at)
                here = dmstale.resolve_here(tagged.group(1)) if tagged else None
                here = here or dmstale.resolve_here(at)
                if here and (ap == here or ap.startswith(here.rstrip('/') + '/')) and len(here) > best_len:
                    kept = ((b.header.get('details') or {}).get('located_at') or {}).get(r.get('id')) or {}
                    best, best_len, covering = b.id, len(here), dict(kept, at=at, id=r.get('id'))
    return best, covering


def core_attention(bid, G):
    """(constraints, notes) of a bean: each figure on one of its statements or on the bean, paired as the square pairs
    them, and the notes `details.safety` keeps."""
    b = G.beans[bid]
    on = {}
    for _i, v, r in b.items:
        if v in PERMISSION + NECESSITY and 'held' not in r:
            for of in (r.get('of') if isinstance(r.get('of'), list) else [r.get('of')]):
                on.setdefault(of, {})[v] = r
    out = []
    for of, figs in on.items():
        target = b.ids.get(of) if isinstance(of, str) else None
        aim = (target[2].get('of') or target[2].get('at') or '') if target else ''
        what = (f"{target[1]} {', '.join(map(str, aim)) if isinstance(aim, list) else aim}".strip() if target else str(of))
        perm = next((p for p in PERMISSION if p in figs), None)
        feas = next((n for n in NECESSITY if n in figs), None)
        if perm:
            r = figs[perm]
            out.append((perm, what, RISK.get((perm, feas), ''), r.get('why') or (figs.get(feas) or {}).get('why') or '',
                        r.get('through') if r.get('through') not in (None, 'unknown') else None))
        elif feas in ('impossible', 'contingent'):
            out.append((feas, what, '', figs[feas].get('why') or '', None))
    notes = [str(n) for n in ((b.header.get('details') or {}).get('safety') or [])]
    return out, notes


def core_main(target):
    sys.path.insert(0, ROOT)
    from core import engine
    from core.check import garden_law
    G = engine.Garden.read(ROOT)
    bean, covering = core_resolve(target, G)
    if not bean:
        print(f"no bean points at {target!r} — nothing in the garden claims it")
        return 2
    b = G.beans[bean]
    if b.unread:
        print(f"cursor -> {bean}: it cannot be read — {b.unread}")
        return 2
    law = garden_law(ROOT)
    habitat = [r.get('at') for _i, v, r in b.items if v == 'be' and r.get('as') == 'habitat']
    print(BOLD(f"cursor -> {bean}") + f"   {b.kind} · {(law.kinds.get(b.kind) or {}).get('nature', '?')}"
          + (f" · living in {', '.join(map(str, habitat))}" if habitat else ''))
    print(f"  {b.header.get('title', '')}")
    try:
        level = engine.Judge(law, G).derived(bean)
    except Exception:
        level = None
    if level and level != 'none':
        print(f"  sensitivity {level}" + (" [special]" if level == 'special-category' else ''))
    if covering:
        print(f"\n  resolved from a FILE: covered by `be` {covering.get('id')}, at {covering.get('at')} "
              f"(role {covering.get('role')}, scan_policy {covering.get('scan_policy')})")

    print("\n" + BOLD("MEASURED") + "  — what is already known, and whether it still holds")
    details = b.header.get('details') if isinstance(b.header.get('details'), dict) else {}
    for sid, e in sorted((details.get('located_at') or {}).items()):
        pol = e.get('scan_policy') if isinstance(e, dict) else None
        if not pol:
            continue
        at = next((r.get('at') for r in [b.ids.get(sid, (0, 0, {}))[2]]), None)
        verdict = "WALK IT" if pol == 'index' else ("DO NOT WALK — read by summary" if pol == 'reference-only'
                                                    else "structure only")
        tagged = re.match(r'^[a-z][a-z0-9-]*:(.+)$', str(at or ''))
        here = dmstale.resolve_here(tagged.group(1) if tagged else str(at or ''))
        print(f"  path   {at}" + (f"  ->  {here}" if here else '') + f"\n         role {e.get('role')} · {pol} -> {verdict}")
    cache = details.get('analysis_cache') or {}
    if not cache:
        print("  cache  none — this being has no recorded analysis; reading is unavoidable")
    for ctype, e in sorted(cache.items()):
        state, detail = dmstale.verdict(e)
        print(f"  cache  {ctype:22} {state:8} -> " +
              ("USE IT, do not re-derive" if state == 'FRESH' else
               "RE-ANALYSE, then refresh the entry" if state == 'STALE' else
               "not on this host — a fact about THIS MACHINE, not about the analysis"
               if state == 'NOT-HERE' else "unverifiable: " + detail))
        if state == 'FRESH' and e.get('summary_ref'):
            print(f"         reads: {e.get('summary_ref')}")

    def shown_(bid, rows, notes, indent):
        for fig, what, risk, why, through in rows:
            print(f"{indent}{fig.upper():10} {what}{risk}" + (f"   [through {through}]" if through else ''))
            if why:
                print(f"{indent}           {str(why)[:150]}")
        for n in notes[:4]:
            print(f"{indent}note       {n[:150]}")

    rows, notes = core_attention(bean, G)
    print("\n" + BOLD("ATTENTION") + " — required before touching it")
    if not (rows or notes):
        print("  none recorded on this being")
    shown_(bean, rows, notes, '  ')

    print("\n" + BOLD("INHERITED") + " — along every chain the core's order holds acyclic")
    any_inherited = False
    for verb, low, high, says in engine.ORDERED:
        walked, seen, frontier = [], {bean}, [bean]
        while frontier:
            nxt = []
            for x in frontier:
                for _i, v, r in G.beans[x].items:
                    if v != verb or 'held' in r or not any(
                            (r.get(k) == 'self' or x in _beans(r.get(k), G)) for k in low):
                        continue
                    for k in high:
                        for t in _beans(r.get(k), G):
                            if t not in seen:
                                seen.add(t); walked.append(t); nxt.append(t)
            frontier = nxt
        shown = False
        for h in walked:
            hrows, _hn = core_attention(h, G)
            if hrows:
                if not shown:
                    print(f"  via {verb} ({says}): {' -> '.join([bean] + walked)}"); shown = True
                any_inherited = True
                print(f"    {h}:")
                shown_(h, hrows, [], '      ')
    if not any_inherited:
        print("  nothing constraining inherited from any chain")
    print()
    return 0


if __name__ == '__main__':
    if len(sys.argv) >= 2 and runs_core():
        sys.exit(core_main(sys.argv[1]))
    if len(sys.argv) < 2:
        print(__doc__.strip().splitlines()[-3].strip()); sys.exit(2)
    sys.exit(main(sys.argv[1]))
