"""shares — the shares a payment is borne in (the verb `bear`), read one way by every reader that reads them: who owes
whom (bin/ledger.py), the books (assets/accounting), the gate's part of a payment (core/profiles.py), the books a commit
touches (core/commit.py) and a page's sheet (assets/view).

    of_payment(G, bid, p, own)   # (bears, source) for the payment `p` held in bean `bid`, `own` its own bears
    of_agreement(G, bid)         # the bears that name the agreement `bid` as a whole, else its nearest whole's

A PAYMENT'S OWN SHARES FIRST: a `bear` whose `of` names the payment. Where it names none, AN AGREEMENT'S SHARES: a `bear`
whose `of` names an agreement as a whole — its bean, `self` in it — holds for each payment that bean holds, and each a
bean holds that is `part` of it (nearest first), unless the payment pays one of those bearers: a transfer between the
parties is no cost they share. Where neither speaks, THE LAW'S DEFAULT: whoever paid bears it, alone (the verb's
`default`, core/law/verbs.yaml)."""


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _live(b, verb):
    return [r for _i, v, r in b.items if v == verb and isinstance(r, dict) and 'held' not in r]


def wholes(G):
    """{bean: [bear roles]} — each bear that names a bean as a whole (`of` a bean of the garden, or `self`: the bean it is
    written in), wherever it is written — never one whose `of` is a statement of its own bean by that id; kept on the
    garden read, so a reader asks it once per version."""
    kept = getattr(G, '_shares_wholes', None)
    if kept is not None:
        return kept
    out = {}
    for bid, b in G.beans.items():
        if getattr(b, 'unread', None):
            continue
        ids = {r.get('id') for _i, _v, r in b.items if isinstance(r, dict) and isinstance(r.get('id'), str)}
        for r in _live(b, 'bear'):
            of = r.get('of')
            # a statement of the bean by that id is what it names first: a payment may share its bean's name
            target = bid if of == 'self' else of if isinstance(of, str) and of in G.beans and of not in ids else None
            if target is not None:
                out.setdefault(target, []).append(r)
    try:
        G._shares_wholes = out
    except AttributeError:
        pass
    return out


def of_agreement(G, bid, seen=None):
    """[bear roles] — the shares an agreement names for every payment it holds: the bears naming bean `bid` as a whole,
    else those of the nearest agreement it is `part` of (`part: { by: self, of: <agreement> }`); [] where none does."""
    seen = set(seen or ())
    if bid in seen or bid not in G.beans:
        return []
    seen.add(bid)
    named = wholes(G).get(bid) or []
    if named:
        return named
    for r in _live(G.beans[bid], 'part'):
        if r.get('by') in ('self', bid) and isinstance(r.get('of'), str):
            got = of_agreement(G, r['of'], seen)
            if got:
                return got
    return []


def of_payment(G, bid, p, own):
    """(bears, source) — the shares the payment `p` (the roles of a `pay` held in bean `bid`) is borne in: its own bears
    (`own`, as the reader found them), `payment`; else its agreement's, `agreement`, unless it pays one of their bearers
    (a transfer between the parties); else ([], None), and the law's default holds."""
    if own:
        return list(own), 'payment'
    named = of_agreement(G, bid)
    if named and not (isinstance(p.get('to'), str) and p['to'] in {str(r.get('by')) for r in named}):
        return list(named), 'agreement'
    return [], None
