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

THE ACCOUNTING PROFILE'S BOOKINGS. A booking moves an amount from one account to another (`from`, `to`), or says where
an entity's part of a payment belongs along a plan (`to` an analytic code); a match says payments are one movement. What
each account holds is read, never stored, so the gate judges only what a booking says: what it rests on, that its codes
are postable accounts of one chart open on its day, that its amounts add up, and that a match agrees and is made once.

    problems(J, b)        -> [(where, message)]   rule `profile` for one bean, judged by the engine J
    charts(J)             -> [(where, message)]   rule `profile` for the garden whole: a chart's beings, a match once
    page_of(b)            -> (id, roles) | None   the page's own `draw`, or None where the bean is no page
    drawings_of(b)        -> [(id, roles)]        each drawing's `draw`, in the order the page shows them
    taken(L)              -> [name]               the profiles the garden takes
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bin'))
import parse as dmparse  # noqa: E402 — the one matcher of a pattern of the law


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
    # THE ACCOUNTING PROFILE'S BOOKINGS AND MATCHES: each booking a move from one account to another, or a share of
    # what it books along a plan (v1 part 12b: today's analytic distribution); under one plan shares all, or amounts
    # all, that add up to the entity's part; a match, records of one movement that agree
    out += _bookings(J, b)
    # THE VIEW PROFILE'S FORMS: the page and its drawings, judged by their forms and by what they name
    draws = _live(b, 'draw')
    if not draws or 'view' not in have:
        return out
    pages = [(i, r) for i, r in draws if isinstance(r.get('page'), dict)]
    drawings = {r.get('id'): (i, r) for i, r in draws if isinstance(r.get('drawing'), dict) and isinstance(r.get('id'), str)}
    readings = {r.get('id') for _i, r in _live(b, 'reckon') if isinstance(r.get('id'), str)}
    held_forms = {q: spec['form'] for q, spec in ((L.verbs.get('draw') or {}).get('qualifiers') or {}).items()
                  if isinstance(spec, dict) and spec.get('form')}        # page, drawing, preferences: each its form
    for i, r in draws:
        where = f"{b.id}: statements[{i}] draw"
        for q, fname in held_forms.items():
            if isinstance(r.get(q), dict):
                got = lines.attrs_problems(f"{where}.{q}", r[q], L.forms.get(fname) or {})
                out += got or domain_problems(J, b, f"{where}.{q}", r[q], (L.forms.get(fname) or {}).get('attrs') or {})
        if isinstance(r.get('drawing'), dict):
            out += _action_inputs(J, b, f"{where}.drawing", r['drawing'], readings)
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
    # A SHEET SHOWS WHAT ITS PAGE SAYS A SHEET OF ITS KIND SHOWS (the view finished for a handplace): a sheet drawing's
    # being, and each kind a drawing may make (`new`), have the facts the page's `fields` names for their kind; and an
    # entry form of a verb (`writes`) names a verb the law has, presets only roles the verb takes, and names a verb or a
    # term of today's words, one of the two
    page_form = pages[0][1]['page'] if pages else {}
    shown = {str(e.get('kind')) for e in _listed(page_form.get('fields')) if isinstance(e, dict)}
    for did, (i, r) in drawings.items():
        where = f"{b.id}: statements[{i}] draw.drawing"
        d = r['drawing']
        if str(d.get('archetype')) == 'sheet':
            target = next((x for x in _listed(r.get('of')) if isinstance(x, str)), None)
            k = J.kind_of(target, b) if target else None
            if k and k not in shown:
                out.append((where, f"a sheet of {target} shows the facts its page names for a {k} (the page's `fields`), "
                                   f"and the page names none"))
        for k in _listed(d.get('new')):
            if isinstance(k, str) and k in L.kinds and k not in shown:
                out.append((f"{where}.new", f"a new {k} opens as a sheet of the facts its page names for a {k} (the "
                                            f"page's `fields`), and the page names none"))
        for n, w in enumerate(_listed(d.get('writes'))):
            if not isinstance(w, dict):
                continue
            ww = f"{where}.writes[{n}]"
            if ('verb' in w) == ('term' in w):
                out.append((ww, "an entry form names a verb of the law, or a term of today's words: one of the two"))
            elif 'preset' in w and 'verb' not in w:
                out.append((ww, "`preset` fills roles of a verb: it stands with `verb`"))
            row = L.verbs.get(str(w.get('verb'))) if 'verb' in w else None
            if isinstance(row, dict) and w.get('preset') is not None:
                if not isinstance(w['preset'], dict):
                    out.append((f"{ww}.preset", "is a mapping of the verb's roles to what fills them"))
                else:
                    takes = set(row.get('roles') or {}) | set(row.get('qualifiers') or {})
                    for role in w['preset']:
                        if role not in takes:
                            out.append((f"{ww}.preset.{role}", f"`{w['verb']}` takes no `{role}`: it takes "
                                                               f"{', '.join(sorted(takes))}"))
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


CLOCK = {'act': 'read', 'nature': 'soma', 'by': 'reader'}


def _action_inputs(J, b, where, drawing, readings):
    """AN ACTION'S INPUTS, ASKED AS A PAGE ASKS THEM (ratified 2026-10-13): a value chosen `of` a reading this page
    declares or a scheme the garden knows (`scheme:<name>`); one filled `from` the element, only where a person would
    give it (never the clock's), and never both filled and chosen. One a person may leave empty (`optional`, ratified
    the same day: "meaningful optional inputs") is never one the tool cannot run without — filled `from` the element,
    or the clock's; what else its tool needs is the tool's to refuse when it plans, as the host maps the tool, not the
    ledger."""
    out = []
    for n, a in enumerate(_listed(drawing.get('actions'))):
        if not isinstance(a, dict):
            continue
        for m, i in enumerate(_listed(a.get('inputs'))):
            if not isinstance(i, dict):
                continue
            w = f"{where}.actions[{n}].inputs[{m}]"
            of = i.get('of')
            if isinstance(of, str):
                if of.startswith('scheme:'):
                    try:
                        known = J.L.std.knowledge.schemes
                    except Exception:
                        known = {}
                    if of[7:] not in known:
                        out.append((f"{w}.of", f"{of!r}: no scheme the garden knows (its VOCAB.md `schemes`, or the law's)"))
                elif of not in readings:
                    out.append((f"{w}.of", f"{of!r}: no reading this page declares (a `reckon` of its bean), and no "
                                           f"`scheme:<name>`"))
            if i.get('from') is not None:
                if i.get('origin') == CLOCK:
                    out.append((f"{w}.from", "the clock's input is read by the reader, never filled from the element"))
                if of is not None:
                    out.append((f"{w}.from", "an input filled from the element is not chosen too: `from` or `of`"))
            if i.get('optional') in ('true', True):
                if i.get('from') is not None:
                    out.append((f"{w}.optional", "an input filled from the element is the host's to fill, never left "
                                                 "empty: the tool acts on it"))
                if i.get('origin') == CLOCK:
                    out.append((f"{w}.optional", "the clock's input is read by the reader, never left empty"))
            # A LIST BESIDE A LIST (ratified 2026-10-14): two lists of one action, given row by row — a person beside
            # their share. Both lists; the one it stands beside is one of this action's, and beside none itself.
            if i.get('beside') is not None:
                by_name = {x.get('name'): x for x in _listed(a.get('inputs')) if isinstance(x, dict)}
                other = by_name.get(i.get('beside'))
                if i.get('many') not in ('true', True):
                    out.append((f"{w}.beside", "an input given beside a list is a list itself: `many: \"true\"`"))
                if other is None or other is i:
                    out.append((f"{w}.beside", f"{i.get('beside')!r}: no other input of this action"))
                elif other.get('many') not in ('true', True):
                    out.append((f"{w}.beside", f"{i.get('beside')!r} is no list: what a list stands beside is a list"))
                elif other.get('beside') is not None:
                    out.append((f"{w}.beside", f"{i.get('beside')!r} stands beside another itself: one list, one beside it"))
                elif i.get('from') is not None or other.get('from') is not None:
                    out.append((f"{w}.beside", "lists given row by row are a person's to give, never filled from the element"))
    return out


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
    if reg in ('lenses', 'archetypes', 'aspects', 'planes', 'date_styles', 'currency_displays') and L.has(reg, s):
        return [(where, L.has(reg, s))]
    if dom.get('type') == 'locale_tag':        # A READER'S WAY OF READING: one tag, as the law's type writes it
        row = next((t for t in (getattr(L, 'line_law', {}) or {}).get('types') or []
                    if isinstance(t, dict) and t.get('type') == 'locale_tag'), {})
        if row.get('pattern') and not (isinstance(v, str) and dmparse.law_match(row['pattern'], v)):
            return [(where, f"{v!r} {row.get('refusal') or 'is no locale_tag'}")]
    if reg == 'orientations':                  # AN ORDER RUNS ON ITS OWN AXIS (the drawing's `axes`): its row says which
        row = next((r for r in L.profile_tables.get('orientations') or [] if str(r.get('order')) == s), None)
        if row is None:
            return [(where, L.has(reg, s) or f"{s!r} is no order of `orientations`")]
        axes = [str(a) for a in _listed((dom.get('where') or {}).get('axis'))]
        if axes and str(row.get('axis')) not in axes:
            return [(where, f"`{s}` runs on the {row.get('axis')} axis (its row of `orientations`), never {' or '.join(axes)}"
                            + (": a body's frame never turns with the reader's script" if str(row.get('follows')) != 'true'
                               else ''))]
    if reg == 'verbs' and s not in L.verbs:
        return [(where, f"{s!r} is no verb of the law (core/law/core.yaml, core/law/verbs.yaml, or the garden's VOCAB.md)")]
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


BOOKS_OF = ('pay', 'measure', 'open', 'book')       # what a booking rests on: what moved or is asked, a measure, the
#                                                   books' opening, another booking


def _chart(J, sch):
    """(rows by code, the codes that are some code's parent, the scheme's form) of scheme `sch`, or None."""
    try:
        K = J.L.std.knowledge
        rows = {str(x.get('code')): x for x in K.rows(sch) if isinstance(x, dict)}
        form = (K.schemes.get(sch) or {}).get('form')
    except Exception:
        return None
    return rows, {str(x.get('parent') or '') for x in rows.values()}, form


def _plan_of(J, sch, c):
    """The plan an analytic code is under: its ancestor at the scheme's first level."""
    try:
        K = J.L.std.knowledge
        rows = {str(x.get('code')): x for x in K.rows(sch) if isinstance(x, dict)}
        levels = ((K.schemes.get(sch) or {}).get('levels') or [{}])
    except Exception:
        return c
    first = (levels[0] or {}).get('level') if isinstance(levels, list) and levels else None
    plan, seen = c, set()
    while plan in rows and plan not in seen and first and rows[plan].get('level') != first:
        seen.add(plan)
        plan = str(rows[plan].get('parent') or '')
    return plan


def _day_of(J, r, b):
    """The day a booking is booked on: its `at`, else the day of what it books, as written; None where neither says."""
    if isinstance(r.get('at'), str):
        return r['at']
    hit = J.statement(r.get('of'), b)
    at = hit[3].get('at') if hit else None
    return at if isinstance(at, str) else (at[0] if isinstance(at, list) and at and isinstance(at[0], str) else None)


def _part(J, hit, entity, whole):
    """The entity's part of a payment's whole: its share of what the payment's bearers bear (`bear` of it, in its bean;
    else of its agreement, core/shares.py), or the whole where none bears it or the entity bears none — exact, or None
    where a share is not read."""
    from core import measures, shares as dmshares
    pb, _i, _v, p = hit
    shares = {}
    own = [r for _j, r in _live(pb, 'bear') if r.get('of') in (p.get('id'), f"{pb.id}#{p.get('id')}")]
    for r in dmshares.of_payment(J.G, pb.id, p, own)[0]:
        s = r.get('share')
        n = measures.exact(str(s.get('count') if isinstance(s, dict) else s)) if s is not None else 1
        if n is None:
            return None
        shares[str(r.get('by'))] = shares.get(str(r.get('by')), 0) + n
    total = sum(shares.values())
    if entity not in shares or not total:
        return whole
    return whole * shares[entity] / total


def _bookings(J, b):
    """The accounting profile's bookings of bean `b`, judged (rule `profile`): a booking rests on what moved, is asked or
    was measured, the books' opening, or another booking; it names `to`, `from` or both, each a code of a scheme or a
    being — or none, booking in the reverse sense (`sense: "-1"`) the move of what it books, from a day it says; a code
    of a chart is a postable account (no code has it for its parent), not closed on the day it is booked on; an analytic
    code is booked `to`, never `from`; its two sides are of one chart; a booking that names both sides moves an amount,
    or a share of a payment. Under one plan of an entity, the bookings of one statement are shares all, or amounts all:
    an analytic plan's adding up to the entity's part of the payment, a chart's side to no more than it — the rest waits
    in the account `awaiting`."""
    from core import measures
    out, books = [], {}
    for i, verb, r in b.items:
        if verb == 'book' and isinstance(r, dict) and 'held' not in r and isinstance(r.get('of'), str):
            books.setdefault(r['of'], []).append((i, r))
    for pid, bs in books.items():
        hit = J.statement(pid, b)
        if not hit or hit[2] not in BOOKS_OF:
            out.append((f"{b.id}: statements[{bs[0][0]}] book.of", f"`{pid}` is none of what a booking rests on: a payment "
                                                                   f"(made, or asked by a clause), a `measure`, the books' "
                                                                   f"`open`, another booking"))
            continue
        q = hit[3].get('of') if hit[2] == 'pay' else None
        unit = str(q.get('unit')) if isinstance(q, dict) else None
        whole = measures.exact(str(q.get('count'))) if isinstance(q, dict) else None
        plans = {}
        for i, r in bs:
            w = f"{b.id}: statements[{i}] book"
            if r.get('to') is None and r.get('from') is None:
                if str(r.get('sense')) == '-1':
                    if r.get('at') is None:
                        out.append((f"{w}.at", "the reverse of a move is read from a day on: say the day (`at`)"))
                    continue
                out.append((w, "a booking names where it goes, `to`, where it comes from, `from`, or both — or, with "
                               "`sense: \"-1\"`, it books the move of what it books in the reverse sense"))
                continue
            if r.get('sense') is not None and str(r.get('sense')) != '1':
                out.append((w, "a booking that names a side moves along it: the reverse of a move is a booking of it, "
                               "`sense: \"-1\"`, naming no side"))
            sides, charts = {}, set()
            for role in ('from', 'to'):
                code = r.get(role)
                if not (isinstance(code, str) and ':' in code):
                    continue                             # a being booked to, or words: read through the chart
                sch, c = code.split(':', 1)
                ch = _chart(J, sch)
                if ch is None or c not in ch[0]:
                    out.append((f"{w}.{role}", f"'{c}' is not a code of {sch}"))
                    continue
                rows, parents, form = ch
                sides[role] = (sch, c, form)
                if form == 'chart':
                    charts.add(sch)
                    if c in parents:
                        out.append((f"{w}.{role}", f"{sch}:{c} has accounts beneath it: a booking names a postable "
                                                   f"account, one with none"))
                    closed, day = str(rows[c].get('closed') or ''), _day_of(J, r, b)
                    if closed and day and day[:10] > closed[:10]:
                        out.append((f"{w}.{role}", f"{sch}:{c} closed on {closed}; this is booked on {day}"))
                elif role == 'from':
                    out.append((f"{w}.from", f"{sch} is no chart: an analytic code says where a part belongs, booked "
                                             f"`to` it, never `from`"))
            if len(charts) > 1:
                out.append((w, f"its two sides are of two charts, {' and '.join(sorted(charts))}: a booking moves an "
                               f"amount within one set of books"))
            s_ = r.get('share')
            kind = 'amount' if isinstance(s_, dict) and (not unit or (str(s_.get('unit')) == unit and unit != '1')) \
                else 'share'
            if 'from' in sides and 'to' in sides and s_ is None and hit[2] != 'pay':
                out.append((w, "a booking that names both sides of what is no payment moves an amount: "
                               "`share: { count, unit }`"))
            entity = str(r.get('by') or J.G.gardener or '')
            if 'to' in sides and 'from' not in sides:
                sch, c, form = sides['to']
                key = (entity, sch, sch if form == 'chart' else _plan_of(J, sch, c), form == 'chart')
                plans.setdefault(key, []).append((w, kind, s_))
            elif 'from' in sides and 'to' not in sides:
                key = (entity, sides['from'][0], f"{sides['from'][0]} from", True)
                plans.setdefault(key, []).append((w, kind, s_))
        for (entity, _sch, plan, chart), xs in sorted(plans.items()):
            kinds = {k for _w, k, _s in xs}
            if len(kinds) > 1:
                out.append((xs[0][0], f"the plan {plan} states amounts for some of its parts and shares for others: no "
                                      f"whole anyone can judge"))
            elif kinds == {'amount'} and whole is not None:
                got = [measures.exact(str(s.get('count'))) for _w, _k, s in xs]
                part = _part(J, hit, entity, whole)
                if None in got or part is None:
                    continue
                show, total = measures.dmunits.show, sum(got)
                of = f"the payment is {show(whole)} {unit}" + ('' if part == whole else
                                                              f", {entity}'s part of it {show(part)} {unit}")
                if chart and total > part:
                    out.append((xs[0][0], f"the bookings to {plan} add up to {show(total)} {unit}, more than its part: "
                                          f"{of}"))
                elif not chart and total != part:
                    out.append((xs[0][0], f"the bookings in the plan {plan} add up to {show(total)} {unit}, and {of}"))
    out += _matches(J, b)
    return out


def _known(b, sid):
    """The verb of the knowing act that knows statement `sid` of bean `b`: the one naming it, else one naming nothing."""
    acts = ('say', 'read', 'derive', 'make')
    named = [v for _i, v, r in b.items if v in acts and isinstance(r, dict) and sid in _listed(r.get('of'))]
    if named:
        return named[0]
    return next((v for _i, v, r in b.items if v in acts and isinstance(r, dict) and r.get('of') is None), None)


def _matches(J, b):
    """A match names two payments or more, records of one movement: what was read of it (a line a source gave) and what
    was said agree in amount per currency."""
    from core import measures
    out = []
    for i, r in _live(b, 'match'):
        w = f"{b.id}: statements[{i}] match"
        refs = [x for x in _listed(r.get('of')) if isinstance(x, str)]
        if len(refs) < 2:
            out.append((w, "a match names two statements or more: records of one movement"))
            continue
        sums = {'read': {}, 'said': {}}
        for x in refs:
            hit = J.statement(x, b)
            if not hit or hit[2] != 'pay' or not isinstance(hit[3].get('of'), dict):
                out.append((f"{w}.of", f"`{x}` is no payment: a match names payments"))
                continue
            q = hit[3].get('charged') if isinstance(hit[3].get('charged'), dict) else hit[3]['of']
            side = 'read' if _known(hit[0], hit[3].get('id')) == 'read' else 'said'
            n = measures.exact(str(q.get('count')))
            if n is not None:
                sums[side][str(q.get('unit'))] = sums[side].get(str(q.get('unit')), 0) + n
        if sums['read'] and sums['said'] and sums['read'] != sums['said']:
            show = lambda d: ', '.join(f"{n} {u}" for u, n in sorted(d.items()))
            out.append((w, f"what was read ({show(sums['read'])}) and what was said ({show(sums['said'])}) do not agree: "
                           f"a match counts one movement once"))
    return out


def charts(J):
    """[(where, message)] of the garden's whole (rule `profile`): each being an account of a chart stands for is one the
    garden holds; a payment is matched once in an entity's books, wherever the match is written."""
    out = []
    try:
        K = J.L.std.knowledge
        schemes = sorted(s for s, row in K.schemes.items() if isinstance(row, dict) and row.get('form') == 'chart')
    except Exception:
        schemes = []
    for sch in schemes:
        try:
            rows = list(K.rows(sch))
        except Exception:
            continue
        for r in rows:
            sf = str(r.get('stands_for') or '') if isinstance(r, dict) else ''
            if sf and sf not in J.G.beans:
                out.append((f"scheme {sch} {r.get('code')}", f"stands for {sf}, which is no bean of this garden"))
    seen = {}
    for bid in sorted(J.G.beans):
        b = J.G.beans[bid]
        if b.unread:
            continue
        for i, r in _live(b, 'match'):
            for x in _listed(r.get('of')):
                if not isinstance(x, str):
                    continue
                key = (str(r.get('by') or J.G.gardener or ''), x if '#' in x else f"{bid}#{x}")
                if key in seen:
                    out.append((f"{bid}: statements[{i}] match", f"`{x}` is matched already ({seen[key]}): a movement "
                                                                 f"is counted once"))
                else:
                    seen[key] = f"{bid}: statements[{i}]"
    return out
