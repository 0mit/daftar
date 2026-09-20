#!/usr/bin/env python3
"""dmform — the ATTRIBUTE FORM: a term's law, keyed by attribute.

The schema language says one sentence in a dozen spellings: "this attribute is a position in that domain".
`entry_values`, `entry_types`, `entry_in_registry`, `on_aspect`, `entry_pattern`, `pointer_fields`… are each a
map keyed by ATTRIBUTE, so one attribute's law is scattered across as many constructs as it has properties, and
is stated a second time, for people, in the term's `entry_attrs:`. This module turns that matrix the other way:
one record per attribute.

ONE MODULE, because five tools read a term's law — the gate, `dmrules`, `dmcursor`, `dmpos`, `dmreview` — and
until this existed each knew the old constructs by name (two of them carried their own copy of `aspects_of`).
When the law's TEXT is rewritten into this form (S2 of the figure grammar), this is the only file that learns
the new spelling; nothing that imports it changes.

It is PURE: it reads a term's definition and returns data. It loads nothing and names no term.

THE FORM
    scope      'entry' | 'self'  — what the term's attributes mostly describe (its entries, or its own value)
    attrs      {name: {facet: rule, 'scope': 'entry'|'self'}}
    order      {(scope, facet): [names]}   each old construct's own attribute order, so findings print as before
    cells      combinations an entry may not hold (error) or should not (warning)
    value      the rule on the term's OWN value: values, values_from, consistent_with, governs_anchor, pattern,
               form, in_registry, compare_form, canonical_note
    self_ref   the value (or each entry) IS itself a ref
    alt        the alternative whole-value form {key, refs}
    one_of     the forms an entry may take
    matches    values fixed by a registry row another field selects
    mirror     another term this one must agree with: the same facets (parity_with), or the mirrored edge (inverse_of)
"""

ENTRY_FACETS = (('required', 'entry_required_attrs'), ('values', 'entry_values'), ('type', 'entry_types'),
                ('pattern', 'entry_pattern'), ('soft', 'entry_soft_pattern'), ('registry', 'entry_in_registry'),
                ('extent', 'entry_extents'), ('ref', 'entry_ref_fields'), ('one_of', 'entry_one_of'))
SELF_FACETS = (('required', 'required_attrs'), ('type', 'attr_types'), ('extent', 'attr_extents'),
               ('ref', 'ref_fields'))
VALUE_KEYS = (('values', 'values'), ('values_from', 'values_from'), ('consistent_with', 'values_consistent_with'),
              ('governs_anchor', 'governs_anchor'), ('pattern', 'value_pattern'), ('form', 'value_form'),
              ('in_registry', 'value_in_registry'), ('compare_form', 'compare_form'),
              ('canonical_note', 'canonical_note'))
ENTRY_SHAPES = ('list_of_entries', 'open_map_of_entries')


def aspects_of(sch):
    """A term may sit on ONE aspect or SEVERAL: `on_aspect` takes a mapping or a list of them."""
    a = (sch or {}).get('on_aspect')
    if isinstance(a, dict):
        a = [a]
    return [x for x in (a or []) if isinstance(x, dict) and x.get('aspect')]


def attribute_form(term_def, sch):
    """The law of one term, keyed by attribute. `term_def` is the term's whole definition (for the meanings it
    gives its attributes); `sch` is the schema in force for it, overlays applied."""
    term_def, sch = term_def or {}, sch or {}
    has_entries = (sch.get('shape') in ENTRY_SHAPES or sch.get('on_aspect') or sch.get('entry_pattern_from_registry')
                   or any(sch.get(k) for _f, k in ENTRY_FACETS))
    form = {'scope': 'entry' if has_entries else 'self', 'attrs': {}, 'order': {}, 'cells': [],
            'self_ref': False, 'value': {}, 'alt': None, 'one_of': list(sch.get('entry_one_of') or []),
            'matches': {'entry': list(sch.get('entry_must_match') or []),
                        'form_from_kind': sch.get('entry_form_from_kind_attr'),
                        'equal_kind_attr': sch.get('must_equal_kind_attr')},
            'mirror': {'parity_with': sch.get('facet_parity_with'), 'inverse_of': sch.get('inverse_of')}}

    def put(scope, facet, name, rule):
        rec = form['attrs'].setdefault(name, {'scope': scope})
        rec[facet] = rule
        form['order'].setdefault((scope, facet), []).append(name)

    for scope, table in (('entry', ENTRY_FACETS), ('self', SELF_FACETS)):
        for facet, key in table:
            v = sch.get(key)
            for name in (v if isinstance(v, (list, dict)) else []):
                if name == 'self' and facet == 'ref':
                    form['self_ref'] = True      # the MARKER "the value is itself a ref" — not an attribute
                else:
                    put(scope, facet, name, v[name] if isinstance(v, dict) else True)
    for name, ptype in (sch.get('pointer_fields') or {}).items():
        put(form['scope'], 'pointer', name, ptype)
    for a in aspects_of(sch):
        put('entry', 'aspect', a.get('attr') or a.get('aspect'), a)
    pfr = sch.get('entry_pattern_from_registry')
    if isinstance(pfr, dict) and pfr.get('attr'):
        put('entry', 'system_from', pfr['attr'], pfr)
    for name, meaning in list((term_def.get('entry_attrs') or {}).items()) + list((term_def.get('attrs') or {}).items()):
        put(form['scope'], 'meaning', name, meaning)

    # CELLS: three old constructs, one idea. `phase` only keeps each where it always ran in the walk.
    for kind, sev in (('incoherent', 'error'), ('in_breach', 'warn')):
        for c in ((sch.get('cross_aspect') or {}).get(kind) or []):
            form['cells'].append({'phase': 'cross', 'origin': kind, 'severity': sev, 'why': c.get('why'),
                                  'when': {k: ('is', v) for k, v in c.items() if k != 'why'}, 'lacks': []})
    for r in (sch.get('entry_required_if') or []):
        form['cells'].append({'phase': 'cond', 'origin': 'required_if', 'severity': 'error', 'why': None,
                              'when': {r.get('attr'): ('is', r.get('equals'))},
                              'lacks': list(r.get('requires') or [])})
    for r in (sch.get('entry_expect_if') or []):
        form['cells'].append({'phase': 'cond', 'origin': 'expect_if', 'severity': 'warn', 'why': r.get('why'),
                              'when': {r.get('attr'): ('starts', r.get('starts_with'))},
                              'lacks': [r.get('expects')]})

    for name, key in VALUE_KEYS:
        if sch.get(key) is not None:
            form['value'][name] = sch[key]
    alt = sch.get('alt_form')
    if isinstance(alt, dict):
        form['alt'] = {'key': alt.get('key'), 'refs': list(alt.get('ref_fields') or [])}
    return form


def facet(form, name, scope=None):
    """(attribute, rule) for every attribute carrying this facet, in the order the law stated them."""
    scope = scope or form['scope']
    return [(n, form['attrs'][n][name]) for n in form['order'].get((scope, name), [])]


def ref_attrs(form, scope):
    """The attributes of this scope that hold a ref, with 'self' first when the value itself is one — exactly the
    list `ref_fields` / `entry_ref_fields` used to be, so a walker draws the same edges in the same order."""
    names = [n for n, _ in facet(form, 'ref', scope)]
    return (['self'] if form['self_ref'] and scope == form['scope'] else []) + names
