"""The profiles in a garden of the core (v1 part 11): rule `profile`, and the readers of what a profile's forms hold.

A garden takes a profile by its name in its VOCAB.md, `profiles: [<name>, …]` — a RULE-CHANGE, as any line of the law a
garden adds. What the profile gives (core/law/profiles.yaml) is then the garden's to use: the verbs whose row names it as
their `home`, the attributes it adds to a form of the core (the code profile's `role`, `scan_policy`, `stack` and
`entrypoint` on a placement), its forms and its tables, and its asset (seed/LANGUAGE's `assets/<profile>/*`). A garden
that does not take it uses none of it, and the rule says which profile, and the one act that takes it.

THE VIEW PROFILE'S FORMS. A page is the bean that holds a `draw` of its drawings, its form `page` (today's `view`, its
monitors folded in); each drawing is a `draw` of what it draws, its form `drawing` (an entry of today's `views`, the live
values that sit on it folded in under `values`). The page's `draw` names the drawings of its bean in the order it shows
them, each once, and every one of them: a set of statements has no order, and the page's has. What a form names is
there: a value of the drawing (`key_of: values`), a drawing of the page (`key_of: drawings`), a reading of the bean
(`key_of: readings`, a `reckon`); and a value is named once on its page, since a page draws its values by their names.

    problems(J, b)        -> [(where, message)]   rule `profile` for one bean, judged by the engine J
    page_of(b)            -> (id, roles) | None   the page's own `draw`, or None where the bean is no page
    drawings_of(b)        -> [(id, roles)]        each drawing's `draw`, in the order the page shows them
    taken(L)              -> [name]               the profiles the garden takes
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def taken(L):
    return list(getattr(L, 'taken', None) or [])


def _live(b, verb):
    return [(i, r) for i, v, r in b.items if v == verb and isinstance(r, dict) and 'held' not in r]


def page_of(b):
    """(id, roles) of the bean's `draw` that holds the page's form, or None."""
    for _i, r in _live(b, 'draw'):
        if isinstance(r.get('page'), dict):
            return r.get('id'), r
    return None


def drawings_of(b):
    """[(id, roles)] of the bean's drawings: in the order its page names them, then any it does not name."""
    drawn = [(r.get('id'), r) for _i, r in _live(b, 'draw') if isinstance(r.get('drawing'), dict)]
    p = page_of(b)
    order = [x for x in _listed((p[1] if p else {}).get('of')) if isinstance(x, str)]
    by_id = {i: r for i, r in drawn if isinstance(i, str)}
    out = [(i, by_id[i]) for i in order if i in by_id]
    return out + [(i, r) for i, r in drawn if i not in order]


def _named(x, dom_attrs, path):
    """[(path, kind, name)] — each name a form's value gives where its form says `key_of` (values, drawings, readings)."""
    out = []
    if not isinstance(x, dict) or not isinstance(dom_attrs, dict):
        return out
    for k, v in x.items():
        spec = dom_attrs.get(k) if isinstance(dom_attrs.get(k), dict) else {}
        dom = spec.get('in')
        w = f"{path}.{k}"
        if isinstance(dom, dict) and dom.get('key_of'):
            out += [(w, dom['key_of'], n) for n in _listed(v) if isinstance(n, str)]
        elif isinstance(dom, dict) and isinstance(dom.get('entries'), dict):
            for n, e in enumerate(v if isinstance(v, list) else [v]):
                out += _named(e, dom['entries'], f"{w}[{n}]")
        elif isinstance(dom, dict) and isinstance(dom.get('map_of'), dict) and isinstance(v, dict):
            for n, e in v.items():
                out += _named(e, dom['map_of'], f"{w}.{n}")
    return out


def problems(J, b):
    """[(where, message)] of rule `profile` for bean `b`."""
    from core import lines
    L = J.L
    if not getattr(L, 'profiles', None):
        return []
    have = set(taken(L))
    out = []

    def take(p):
        return (f"it is the {p} profile's, which this garden does not take: taking it is a line of VOCAB.md, "
                f"`profiles: [{', '.join(sorted(have | {p}))}]`, a RULE-CHANGE the gardener ratifies")
    for i, verb, r in b.items:
        if not isinstance(r, dict) or 'held' in r:
            continue
        where = f"{b.id}: statements[{i}] {verb}"
        home = L.home(verb)
        if home and home not in have:
            out.append((where, f"`{verb}` — {take(home)}"))
        v = L.verbs.get(verb) or {}
        for q, spec in (v.get('qualifiers') or {}).items():
            if isinstance(spec, dict) and spec.get('form') and isinstance(r.get(q), dict):
                for a in r[q]:
                    p = L.added_by.get((spec['form'], a))
                    if p and p not in have:
                        out.append((f"{where}.{q}.{a}", f"`{a}` — {take(p)}"))
    # THE VIEW PROFILE'S FORMS: the page and its drawings, judged by their forms and by what they name
    draws = _live(b, 'draw')
    if not draws or 'view' not in have:
        return out
    pages = [(i, r) for i, r in draws if isinstance(r.get('page'), dict)]
    drawings = {r.get('id'): (i, r) for i, r in draws if isinstance(r.get('drawing'), dict) and isinstance(r.get('id'), str)}
    readings = {r.get('id') for _i, r in _live(b, 'reckon') if isinstance(r.get('id'), str)}
    for i, r in draws:
        where = f"{b.id}: statements[{i}] draw"
        for q in ('page', 'drawing'):
            if isinstance(r.get(q), dict):
                out += lines.attrs_problems(f"{where}.{q}", r[q], L.forms.get(q) or {})
        if 'drawing' in r and not isinstance(r.get('id'), str):
            out.append((where, "a drawing is named: its `draw` has an `id`, which its page and its drawing module name "
                               "it by"))
    if len(pages) > 1:
        out.append((f"{b.id}: statements[{pages[1][0]}] draw", "a bean is one page: one `draw` holds its form"))
    if drawings and not pages:
        i = next(iter(drawings.values()))[0]
        out.append((f"{b.id}: statements[{i}] draw", "a drawing is a page's: its bean holds the page's own `draw` "
                                                     "(its form `page`), which names its drawings in order"))
    for i, r in pages[:1]:
        where = f"{b.id}: statements[{i}] draw.of"
        named = _listed(r.get('of'))
        for n in named:
            if not isinstance(n, str) or n not in drawings:
                out.append((where, f"{n!r} is no drawing of this page: a page draws its drawings, each a `draw` of "
                                   f"its bean that holds the form `drawing`"))
        twice = sorted({n for n in named if isinstance(n, str) and named.count(n) > 1})
        if twice:
            out.append((where, f"{', '.join(twice)}: a drawing is named once"))
        left = [d for d in drawings if d not in named]
        if left:
            out.append((where, f"{', '.join(map(str, left))}: a drawing of this page the page does not name — it names "
                               f"every one, in the order it shows them"))
    seen = {}
    for did, (i, r) in drawings.items():
        where = f"{b.id}: statements[{i}] draw.drawing"
        vals = r['drawing'].get('values') if isinstance(r['drawing'].get('values'), dict) else {}
        for k in vals:
            if k in seen:
                out.append((f"{where}.values.{k}", f"`{k}` names a value of the drawing `{seen[k]}` already: a value is "
                                                   f"named once on its page"))
            seen.setdefault(k, did)
        for path, kind, n in _named(r['drawing'], (L.forms.get('drawing') or {}).get('attrs') or {}, where):
            if kind == 'values' and n not in vals:
                out.append((path, f"{n!r} is no value of this drawing ({', '.join(vals) or 'it has none'})"))
            elif kind == 'drawings' and n not in drawings:
                out.append((path, f"{n!r} is no drawing of this page ({', '.join(map(str, drawings))})"))
            elif kind == 'readings' and n not in readings:
                out.append((path, f"{n!r} is no reading of this bean (a `reckon` it holds by that id)"))
    return out
