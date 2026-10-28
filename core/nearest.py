"""nearest — the one ordering of the candidates that hold one case: nearest or most specific first, by the keys its
use's row of core/law/lines.yaml `nearest` names, read in order, and — at each use — what a tie of the nearest does,
as that row declares: `refuse` (none of them decides), `both` (every one of them stands) or `order` (the first of them).

Five uses read it, each the code of its own keys' measures: the flow table's rows that hold a pass (core/law.py
`decide`), a scheme's pattern rows a name fits and the wholes a member inherits a code from (core/groupings.py `fit`,
`inherit`), the beans whose location covers a path (bin/cursor.py), and the methods' decisions on whether material may
come from a layer to a layer at all (bin/pass.py `CoreFlows.direction`). Which keys a use ranks by, in which order, and
what its tie does, are the law's; a key's measure is its use's.

    use(law, name)                      -> (keys, tie), from the law's row (a core.law.Law, or lines.yaml's data)
    rank(items, keys, measures)         -> the items nearest first, the order given kept between equals
    nearest(items, keys, measures, tie) -> (what stands, the nearest as near), each in the order given
    tied(items, tie)                    -> what stands of candidates as near, in the order given
    problems(law)                       -> [(where, message)]: the rows held to the closed lists below
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
USES = {                        # each use, and the keys it has a measure for: the closed list a row names keys from
    'flows': ('as',),
    'patterns': ('literal', 'slots'),
    'wholes': ('way',),         # the walk up is the measure: a whole met before another on its way is nearer
    'locations': ('length',),
    'directions': ('grant',),   # whether material may come from a layer to a layer at all, by any method (core 4.10)
}
TIES = ('refuse', 'both', 'order')
_RELEASED = []                  # the release's own rows, read once: for a law older than these rows


def _lines(law):
    """lines.yaml's data: a core.law.Law's, the data given, or the release's own where the law holds no `nearest`."""
    d = getattr(law, 'line_law', law) if law is not None else None
    if isinstance(d, dict) and isinstance(d.get('nearest'), dict):
        return d
    if not _RELEASED:
        from core import read
        _RELEASED.append(read.data(os.path.join(HERE, 'law', 'lines.yaml')) or {})
    return _RELEASED[0]


def use(law, name):
    """(keys, tie) of the use `name`, as the law's row of `nearest` declares them."""
    for r in (_lines(law).get('nearest') or {}).get('uses') or []:
        if isinstance(r, dict) and r.get('use') == name:
            return tuple(str(k.get('key')) for k in r.get('keys') or [] if isinstance(k, dict)), str(r.get('tie'))
    raise KeyError(f"the law names no use `{name}` of the nearest (core/law/lines.yaml `nearest.uses`)")


def rank(items, keys, measures):
    """The items nearest first by `keys`, each one's measure (`measures[key](item)`) lower nearer, read in the order the
    keys are named; items alike in every key keep the order they were given in."""
    return sorted(items, key=lambda x: tuple(measures[k](x) for k in keys))


def tied(items, tie):
    """What stands of candidates as near as one another, in the order given: all of them (`both`), the first (`order`),
    or none where there are two or more (`refuse`)."""
    if len(items) <= 1 or tie == 'both':
        return list(items)
    if tie == 'order':
        return list(items[:1])
    return []


def nearest(items, keys, measures, tie):
    """(what stands, the nearest as near as one another): the candidates whose measures are the least by `keys`, and of
    them what the tie lets stand — each in the order the candidates were given."""
    if not items:
        return [], []
    m = [(tuple(measures[k](x) for k in keys), x) for x in items]
    top = min(k for k, _x in m)
    near = [x for k, x in m if k == top]
    return tied(near, tie), near


def problems(law):
    """[(where, message)]: the rows of `nearest` — each tie of the closed list `TIES`, and each use one this code has,
    with keys of that use, in an order, and a tie of the list; and a row for every use."""
    out = []
    where = 'core/law/lines.yaml nearest'
    d = getattr(law, 'line_law', law)
    n = d.get('nearest') if isinstance(d, dict) else None
    if not isinstance(n, dict):
        return [(where, "is missing: each use of the nearest declares its keys and its tie here")]
    ties = [str(r.get('tie')) for r in n.get('ties') or [] if isinstance(r, dict)]
    if sorted(ties) != sorted(TIES):
        out.append((f"{where}.ties", f"the ties are {', '.join(TIES)}, each once, each with its meaning: these hold "
                                     f"{', '.join(ties) or 'none'}"))
    seen = []
    for r in n.get('uses') or []:
        u = r.get('use') if isinstance(r, dict) else None
        if u not in USES:
            out.append((f"{where}.uses", f"`{u}` is no use of the nearest: the uses are {', '.join(USES)}"))
            continue
        if u in seen:
            out.append((f"{where}.uses[{u}]", "is named twice: a use has one row"))
        seen.append(u)
        keys = [k.get('key') if isinstance(k, dict) else k for k in r.get('keys') or []]
        if not keys or any(k not in USES[u] for k in keys) or len(set(keys)) != len(keys):
            out.append((f"{where}.uses[{u}].keys", f"names {', '.join(map(str, keys)) or 'no key'}: a use ranks by keys "
                                                   f"of its own, each once — {u} has {', '.join(USES[u])}"))
        if r.get('tie') not in TIES:
            out.append((f"{where}.uses[{u}].tie", f"`{r.get('tie')}` is no tie: {', '.join(TIES)}"))
    for u in USES:
        if u not in seen:
            out.append((f"{where}.uses", f"names no row for `{u}`: each use declares its keys and its tie"))
    return out
