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
    # THE NETWORK PROFILE'S FORM: a channel — where a listening surface or a link is bound, what it protects, what it
    # is for, who may reach it (v1 part 12b: today's endpoint and link attributes)
    for i, verb, r in b.items:
        if isinstance(r, dict) and 'held' not in r and r.get('channel') is not None and verb in ('serve', 'carry', 'route', 'translate', 'filter'):
            where = f"{b.id}: statements[{i}] {verb}.channel"
            out += lines.attrs_problems(where, r['channel'], L.forms.get('channel') or {})
            pl = r['channel'].get('plane') if isinstance(r['channel'], dict) else None
            if pl is not None and L.has('planes', pl):
                out.append((f"{where}.plane", L.has('planes', pl)))
            ob = r['channel'].get('observed') if isinstance(r['channel'], dict) else None
            if ob is not None:
                from core import frame
                try:
                    frame.read(ob, J.systems, J.G.zone)
                except frame.Refused as e:
                    out.append((f"{where}.observed", str(e)))
    # THE ACCOUNTING PROFILE'S BOOKINGS, judged plan by plan (v1 part 12b: today's analytic distribution): each books
    # a payment of this bean to an account of a scheme, in a share or an amount; the accounts under one plan (the
    # scheme's first level) are shares all, or amounts all — and amounts that add up to the payment
    out += _bookings(J, b)
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
                got = lines.attrs_problems(f"{where}.{q}", r[q], L.forms.get(q) or {})
                out += got or domain_problems(J, b, f"{where}.{q}", r[q], (L.forms.get(q) or {}).get('attrs') or {})
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
    # A DRAWING NAMES A VALUE OF ITS PAGE: its own, or one another drawing of the page holds, which a shape reads beside
    # its own (a race's band read against the grain's temperature) — a value being named once on its page (v1 part 12)
    for did, (i, r) in drawings.items():
        where = f"{b.id}: statements[{i}] draw.drawing"
        vals = r['drawing'].get('values') if isinstance(r['drawing'].get('values'), dict) else {}
        for path, kind, n in _named(r['drawing'], (L.forms.get('drawing') or {}).get('attrs') or {}, where):
            if kind == 'values' and n not in vals and n not in seen:
                out.append((path, f"{n!r} is no value of this page ({', '.join(seen) or 'it has none'})"))
            elif kind == 'drawings' and n not in drawings:
                out.append((path, f"{n!r} is no drawing of this page ({', '.join(map(str, drawings))})"))
            elif kind == 'readings' and n not in readings:
                out.append((path, f"{n!r} is no reading of this bean (a `reckon` it holds by that id)"))
    return out


# ------------------------------------------------------------------------------------------------ a domain a form names
# What a page's or a drawing's attribute holds is judged by the domain its form names (v1 part 12b; part 11 left these to
# the tool that reads each): a unit of the law, a technology of the catalogue, a quantity of the kind named, an extent and
# a repetition in their forms, a frame that is a line, a signal the catalogue publishes, a count, a lens, an archetype, a
# kind, a place system, a being of the garden. A pointer, a name of the page (`key_of`, judged above) and prose are not.
def _units_named(L):
    return {str(r.get('name')) for r in L.units.values() if isinstance(r, dict) and r.get('name')}


def _signals(L):
    return {str(r.get('signal')) for r in L.std._tsv(os.path.join('seed', 'knowledge', 'signals.tsv')) if r.get('signal')}


def domain_why(J, b, M, where, v, dom):
    """[(where, message)] for the value `v` of an attribute whose domain is `dom`."""
    from core import measures
    L = J.L
    if isinstance(dom, str):
        if dom == 'being' and isinstance(v, str) and J._being(v, {}, b):
            return [(where, J._being(v, {}, b))]
        if dom == 'extent' and isinstance(v, dict):
            return M.extent(where, v)
        if dom == 'recurrence' and isinstance(v, dict):
            return M.recurrence(where, v)
        return []
    if not isinstance(dom, dict):
        return []
    reg, s = dom.get('registry'), str(v)
    if reg == 'units' and not (measures.unit_row(L, s) or s in _units_named(L)):
        return [(where, f"{s!r} is no unit of the law (core/law/units.yaml, UCUM or the English name it attaches) and "
                        f"no currency of ISO 4217")]
    if reg == 'technology' and L.std.code(f"technology:{s}") and L.std.code(f"technology-daftar:{s}"):
        return [(where, f"{s!r} is no technology of the catalogue (seed/knowledge/technology.tsv)")]
    if reg == 'signals' and _signals(L) and s not in _signals(L):
        return [(where, f"{s!r} is no signal the catalogue publishes (seed/knowledge/signals.tsv)")]
    if reg == 'lines' and s not in M.lines:
        return [(where, f"{s!r} is no line a drawing can run along: one of {', '.join(sorted(M.lines))}")]
    if reg in ('lenses', 'archetypes', 'planes') and L.has(reg, s):
        return [(where, L.has(reg, s))]
    if reg == 'kinds' and s not in L.kinds:
        return [(where, f"{s!r} is no kind of the law")]
    if reg == 'systems' and s not in J.systems:
        return [(where, f"{s!r} is no system of positions the law or the garden declares")]
    if reg == 'quantities' and s not in L.std.quantities:
        return [(where, f"{s!r} is no quantity of the law")]
    if 'quantity' in dom:
        why = measures.quantity_why(L, v, None if dom['quantity'] == 'any' else dom['quantity'])
        return [(where, why)] if why else []
    if dom.get('type') == 'count' and measures.exact(v if isinstance(v, str) else '') is None:
        return [(where, measures.count_why(v))]          # the one count reader: plain decimal digits, read exactly
    if isinstance(dom.get('being'), dict) and isinstance(v, str):
        kinds = _listed(dom['being'].get('kind'))
        if J._being(v, {}, b):
            return [(where, J._being(v, {}, b))]
        if kinds and J.kind_of(v, b) not in kinds:
            return [(where, f"{v!r} is a {J.kind_of(v, b)}, not a {' or '.join(kinds)}")]
    return []


def domain_problems(J, b, where, x, attrs, M=None):
    """Walk a form's value beside its attributes, judging each leaf by its domain."""
    from core import measures
    M = M or measures.Measures(J.L, J.G.zone)
    out = []
    if not isinstance(x, dict) or not isinstance(attrs, dict):
        return out
    for k, v in x.items():
        spec = attrs.get(k) if isinstance(attrs.get(k), dict) else None
        if spec is None:
            continue
        dom, w = spec.get('in'), f"{where}.{k}"
        if isinstance(dom, dict) and isinstance(dom.get('entries'), dict):
            for n, e in enumerate(v if isinstance(v, list) else [v]):
                out += domain_problems(J, b, f"{w}[{n}]", e, dom['entries'], M)
        elif isinstance(dom, dict) and isinstance(dom.get('map_of'), dict) and isinstance(v, dict):
            for key, e in v.items():
                out += domain_problems(J, b, f"{w}.{key}", e, dom['map_of'], M)
        else:
            for n, e in enumerate(v if isinstance(v, list) and dom not in ('extent', 'recurrence') else [v]):
                out += domain_why(J, b, M, w if not isinstance(v, list) else f"{w}[{n}]", e, dom)
    return out


def _bookings(J, b):
    from core import measures
    out, books = [], {}
    for i, verb, r in b.items:
        if verb == 'book' and isinstance(r, dict) and 'held' not in r and isinstance(r.get('of'), str):
            books.setdefault(r['of'], []).append((i, r))
    for pid, bs in books.items():
        hit = J.statement(pid, b)
        if not hit or hit[2] != 'pay' or not isinstance(hit[3].get('of'), dict):
            out.append((f"{b.id}: statements[{bs[0][0]}] book.of", f"`{pid}` is no payment: a booking shares what a `pay` "
                                                                   f"gave"))
            continue
        q = hit[3]['of']
        unit, whole = str(q.get('unit')), measures.exact(str(q.get('count')))
        plans = {}
        for i, r in bs:
            w = f"{b.id}: statements[{i}] book"
            code = r.get('to')
            if not (isinstance(code, str) and ':' in code):
                continue                                 # a being booked to, or words: no account of a scheme
            sch, c = code.split(':', 1)
            try:
                rows = {str(x.get('code')): x for x in J.L.std.knowledge.rows(sch) if isinstance(x, dict)}
                levels = ((J.L.std.knowledge.schemes.get(sch) or {}).get('levels') or [{}])
            except Exception:
                rows, levels = {}, [{}]
            if c not in rows:
                out.append((f"{w}.to", f"'{c}' is not a code of {sch}"))
                continue
            first = (levels[0] or {}).get('level') if isinstance(levels, list) and levels else None
            plan, seen = c, set()
            while plan in rows and plan not in seen and first and rows[plan].get('level') != first:
                seen.add(plan)
                plan = str(rows[plan].get('parent') or '')
            s = r.get('share')
            kind = 'amount' if isinstance(s, dict) and str(s.get('unit')) == unit and unit != '1' else 'share'
            plans.setdefault(plan, []).append((w, kind, s))
        for plan, xs in sorted(plans.items()):
            kinds = {k for _w, k, _s in xs}
            if len(kinds) > 1:
                out.append((xs[0][0], f"the plan {plan} states amounts for some of its parts and shares for others: no "
                                      f"whole anyone can judge"))
            elif kinds == {'amount'} and whole is not None:
                got = [measures.exact(str(s.get('count'))) for _w, _k, s in xs]
                if None not in got and sum(got) != whole:
                    out.append((xs[0][0], f"the bookings in the plan {plan} add up to {sum(got)} {unit}, and the payment "
                                          f"is {whole} {unit}"))
    return out
