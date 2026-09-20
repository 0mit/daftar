#!/usr/bin/env python3
"""dmform — the ATTRIBUTE FORM: a term's law, keyed by attribute.

A term's schema says, for each attribute, ONE thing: what the attribute is a position IN (`attrs.<name>.in`),
whether it is required, and what it means. This module reads that spelling and hands every tool the same
record — the gate, `dmrules`, `dmcursor`, `dmpos`, `dmreview`, `dmparse`. It is the ONLY file that knows how
the law spells an attribute; `bin/dmreform.py` is the only one that knows how it USED to (std-vocab <= 12.0).

It is PURE: it reads a term's definition and returns data. It loads nothing and names no term.

THE FORM
    scope      'entry' | 'self'  — what the term's attributes describe (each entry, or the value itself)
    attrs      {name: {facet: rule, 'scope': …}}    facets: required, values, registry, aspect, type, system_from,
               pattern, soft, extent, ref, pointer, one_of, meaning
    order      {(scope, facet): [names]}   the law's attribute order, per facet
    cells      combinations an entry may not hold (error) or should not (warning)
    value      the rule on the term's OWN value: values, values_from, consistent_with, governs_anchor, pattern,
               form, in_registry, compare_form, canonical_note
    self_ref   the value (or each entry) IS itself a ref
    alt        the alternative whole-value form {key, refs}
    one_of     the forms an entry may take
    matches    values fixed by a registry row another field selects
    mirror     another term this one must agree with: the same facets (parity_with), or the mirrored edge
    unknown    attributes whose `in:` names no domain the language offers — the gate refuses them
"""

VALUE_KEYS = (('values', 'values'), ('values_from', 'values_from'), ('consistent_with', 'values_consistent_with'),
              ('governs_anchor', 'governs_anchor'), ('pattern', 'value_pattern'), ('form', 'value_form'),
              ('in_registry', 'value_in_registry'), ('compare_form', 'compare_form'),
              ('canonical_note', 'canonical_note'))
ENTRY_SHAPES = ('list_of_entries', 'open_map_of_entries')


def aspects_of(sch):
    """The aspects a term's entries take positions on: [{aspect, attr, default}], in the order the law lists the
    attributes. A term may sit on ONE aspect or SEVERAL."""
    out = []
    for name, rec in ((sch or {}).get('attrs') or {}).items():
        d = (rec or {}).get('in') if isinstance(rec, dict) else None
        if isinstance(d, dict) and d.get('aspect'):
            out.append({'aspect': d['aspect'], 'attr': name, 'default': d.get('default')})
    return out


# ============================== THE LAW'S OWN SPELLING (std-vocab 13.0) ==============================
# schema:
#   shape: list_of_entries
#   is_ref: true                      # the value (or each entry) IS itself a {bean|mapping[, field]} ref
#   attrs:
#     <name>: { required: true, in: <domain>, meaning: "…" }
#   cells:
#     - { when: {<attr>: <value>, …}, verdict: incoherent | in_breach, why: "…" }
#     - { when: {<attr>: <value>}, requires: [<attr>…] }                       # an error
#     - { when: {<attr>: {starts_with: "…"}}, expects: [<attr>…], why: "…" }   # a warning
#
# EVERY ATTRIBUTE IS A POSITION IN EXACTLY ONE DOMAIN. Measured over every term of std-vocab 12.0 and one garden's
# overlay before this spelling was chosen: no attribute carried two. `in:` is therefore one thing, and it is never
# absent — an attribute nobody has given a domain says `untyped`, so an oversight and a decision stop looking alike
# (the rule `enforced_by: none` and `pattern: none` already apply one level up).
DOMAINS = {
    'values':      "in: [a, b, c]                                  one of a closed list written here",
    'registry':    "in: { registry: <name>, take: <field> }        a row of a registry (or `registry_from: <attr>`: the registry another attr names)",
    'aspect':      "in: { aspect: <name>, default: <position> }    a position on an opposition; the default applies when the entry is silent",
    'type':        "in: { type: <value type> }                     a row of `value_types` — its pattern, and for a time type its system and unit",
    'form_of':     "in: { form_of: <registry>, keyed_by: <attr>, take: pattern }   a position in the system a SIBLING attr names, in that system's one form",
    'system':      "in: { system: <anchor system> }                a position in ONE named system, written in that system's one form (`unix-epoch`, `geographic`)",
    'key_of':      "in: { key_of: <term> }                         a key of that term's mapping ON THIS BEAN, or `<bean>:<key>` on another — resolved by the gate, and not an edge",
    'entries':     "in: { entries: { <attr>: {required?, in, meaning} } }   entries INSIDE an entry: a list of them, or one mapping — each judged as an entry, by the attributes written here",
    'bean_id':     "in: bean_id                                    the bare id of a bean this garden holds: resolved by the gate, and not an edge (an edge is a `ref`)",
    'any':         "in: any                                        DELIBERATELY any value: its type is some other attribute's business. A decision, where `untyped` is a debt",
    'pattern':     "in: { pattern: '<regex>' }                     a form this term owns; with `soft: true` and a `why` it WARNS instead of refusing",
    'quantity':    "in: { quantity: <name> }                       a measured value { count, unit } whose unit measures that quantity",
    'extent':      "in: extent                                     a bounded region of an aspect's domain (`extent_form`)",
    'recurrence':  "in: recurrence                                 a repetition over a sequence: every Nth neighbour, every N units, or the same place in each cell of a level (`recurrence_form`)",
    'ref':         "in: ref                                        a {bean|mapping[, field]} ref, resolved by the gate",
    'pointer':     "in: { pointer: bean_field_pointer }            '<section>.<key>' on this bean, {bean, field} on another, or 'file:<path>'",
    'id':          "in: id                                         the id of a bean or mapping — a key of the ref FORM itself, which the gate resolves",
    'prose':       "in: prose                                      a reason, a description, a remark: deliberately not a position. `why`, `what`, `note`",
    'untyped':     "in: untyped                                    a position whose domain nobody has declared yet — a standing debt, visible as one",
}


def _domain(d):
    """(facet, rule) for one attribute's `in:` — the internal record the interpreter has always read."""
    if isinstance(d, list):
        return 'values', list(d)
    if d in ('extent', 'ref', 'recurrence', 'bean_id'):
        return d, True
    if d in ('prose', 'untyped', 'id', 'any') or d is None:
        return None, None
    if isinstance(d, dict):
        if 'aspect' in d:
            return 'aspect', dict(d)
        if 'type' in d:
            return 'type', d['type']
        if 'entries' in d:
            return 'entries', dict(d['entries'] or {})
        if 'system' in d:
            return 'system', d['system']
        if 'key_of' in d:
            return 'key_of', d['key_of']
        if 'form_of' in d:
            return 'system_from', {'registry': d['form_of'], 'keyed_by': d.get('keyed_by'), 'take': d.get('take')}
        if 'pattern' in d:
            if d.get('soft'):
                return 'soft', {k: v for k, v in (('pattern', d['pattern']), ('why', d.get('why'))) if v is not None}
            return 'pattern', d['pattern']
        if 'registry' in d or 'registry_from' in d:
            return 'registry', {k: d[k] for k in ('registry', 'registry_from', 'take', 'where') if k in d}
        if 'quantity' in d:
            return 'quantity', d['quantity']
        if 'pointer' in d:
            return 'pointer', d['pointer']
    return 'unknown', d


def scope_of(sch):
    """What a term's `attrs` describe: each ENTRY (a list, an open map, a faceted mapping) or the value ITSELF."""
    if sch.get('shape') in ENTRY_SHAPES or sch.get('key_form') or sch.get('entry_one_of'):
        return 'entry'
    return 'self'


def attribute_form(term_def, sch):
    """The law of one term, keyed by attribute — read from the law's own spelling."""
    sch = sch or {}
    scope = scope_of(sch)
    form = {'scope': scope, 'attrs': {}, 'order': {}, 'cells': [],
            'self_ref': bool(sch.get('is_ref')), 'value': {}, 'alt': None,
            'one_of': list(sch.get('entry_one_of') or []),
            'matches': {'entry': list(sch.get('entry_must_match') or []),
                        'form_from_kind': sch.get('entry_form_from_kind_attr'),
                        'equal_kind_attr': sch.get('must_equal_kind_attr')},
            'mirror': {'parity_with': sch.get('facet_parity_with'), 'inverse_of': sch.get('inverse_of')},
            'unknown': []}

    def put(facet, name, rule):
        form['attrs'].setdefault(name, {'scope': scope})[facet] = rule
        form['order'].setdefault((scope, facet), []).append(name)

    for name, rec in (sch.get('attrs') or {}).items():
        rec = rec if isinstance(rec, dict) else {}
        form['attrs'].setdefault(name, {'scope': scope})
        if rec.get('required') is True:
            put('required', name, True)
        facet_name, rule = _domain(rec.get('in'))
        if facet_name == 'unknown' or 'in' not in rec:
            form['unknown'].append(name)
        elif facet_name == 'system_from':
            put('system_from', name, dict(rule, attr=name))
        elif facet_name:
            put(facet_name, name, rule)
        if isinstance(rec.get('default_from'), dict):
            put('default_from', name, dict(rec['default_from']))
        if rec.get('meaning') is not None:
            put('meaning', name, rec['meaning'])
    for name in form['one_of']:
        put('one_of', name, True)

    cross, cond = [], []
    for c in (sch.get('cells') or []):
        if not isinstance(c, dict):
            continue
        when = {k: (('starts', v['starts_with']) if isinstance(v, dict) and 'starts_with' in v else ('is', v))
                for k, v in (c.get('when') or {}).items()}
        if c.get('requires') is not None:
            cond.append((0, {'phase': 'cond', 'origin': 'required_if', 'severity': 'error', 'why': None,
                             'when': when, 'lacks': list(c['requires'])}))
        elif c.get('expects') is not None:
            cond.append((1, {'phase': 'cond', 'origin': 'expect_if', 'severity': 'warn', 'why': c.get('why'),
                             'when': when, 'lacks': list(c['expects'])}))
        else:
            kind = c.get('verdict')
            cross.append((0 if kind == 'incoherent' else 1,
                          {'phase': 'cross', 'origin': kind, 'severity': 'error' if kind == 'incoherent' else 'warn',
                           'why': c.get('why'), 'when': when, 'lacks': []}))
    form['cells'] = [c for _o, c in sorted(cross, key=lambda x: x[0])] + [c for _o, c in sorted(cond, key=lambda x: x[0])]

    for name, key in VALUE_KEYS:
        if sch.get(key) is not None:
            form['value'][name] = sch[key]
    alt = sch.get('alt_form')
    if isinstance(alt, dict):
        form['alt'] = {'key': alt.get('key'), 'refs': list(alt.get('ref_fields') or [])}
    return form


def row_matches(row, where):
    """Does a registry row satisfy a domain's `where:`? Each field must equal the value, or be one of the list."""
    for k, want in (where or {}).items():
        if row.get(k) not in (want if isinstance(want, list) else [want]):
            return False
    return True


def facet(form, name, scope=None):
    """(attribute, rule) for every attribute carrying this facet, in the order the law stated them."""
    scope = scope or form['scope']
    return [(n, form['attrs'][n][name]) for n in form['order'].get((scope, name), [])]


def ref_attrs(form, scope):
    """The attributes of this scope that hold a ref, with 'self' first when the value itself is one — exactly the
    list `ref_fields` / `entry_ref_fields` used to be, so a walker draws the same edges in the same order."""
    names = [n for n, _ in facet(form, 'ref', scope)]
    return (['self'] if form['self_ref'] and scope == form['scope'] else []) + names
