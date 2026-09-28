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
               pattern, soft, extent, ref, pointer, bean_id, entries, keyed_by, one_of, origin, stamped, meaning
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
    'type':        "in: { type: <value type>, unit?: <unit> }      a row of `value_types` — its pattern, and for a time type its system and unit; `unit` holds a position to that unit or a finer one, and is what the save writes for `now`",
    'form_of':     "in: { form_of: <registry>, keyed_by: <attr>, take: pattern }   a position in the system a SIBLING attr names, in that system's one form",
    'system':      "in: { system: <anchor system> }                a position in ONE named system, written in that system's one form (`unix-epoch`, `geographic`)",
    'key_of':      "in: { key_of: <term> }                         a key of that term's mapping ON THIS BEAN, or `<bean>:<key>` on another — resolved by the gate, and not an edge",
    'entries':     "in: { entries: { <attr>: {required?, in, meaning} }, keyed_by?: <attr> | [<attr>, ...], one_of?: [<attr>, ...], at_most_one_of?: [[<attr>, ...], ...] }   entries INSIDE an entry: a list of them, or one mapping — each judged as an entry, by the attributes written here; `keyed_by`: one entry per value (or combination of values) of those attributes; `one_of`/`at_most_one_of`: at least one of these, at most one of each group",
    'bean_id':     "in: bean_id | { bean_id: { gene: [...] } }    the bare id of a bean this garden holds (of those gene): resolved by the gate, and not an edge (an edge is a `ref`)",
    'any':         "in: any                                        DELIBERATELY any value: its type is some other attribute's business. A decision, where `untyped` is a debt",
    'pattern':     "in: { pattern: '<regex>' }                     a form this term owns; with `soft: true` and a `why` it WARNS instead of refusing",
    'quantity':    "in: { quantity: <name> }                       a measured value { count, unit } whose unit measures that quantity",
    'extent':      "in: extent                                     a bounded region of an aspect's domain (`extent_form`)",
    'recurrence':  "in: recurrence                                 a repetition over a sequence: every Nth neighbour, every N units, or the same place in each cell of a level (`recurrence_form`)",
    'ref':         "in: ref                                        a {bean|mapping[, field]} ref, resolved by the gate",
    'origin':      "in: origin                                     where a value comes from, `{act, nature?, by?}`: a row of `acts`, a row of `natures` or a list of them, and one of the names the act's row lists",
    'pointer':     "in: { pointer: bean_field_pointer }            '<section>.<key>' on this bean, {bean, field} on another, or 'file:<path>'",
    'id':          "in: id                                         the id of a bean or mapping — a key of the ref FORM itself, which the gate resolves",
    'prose':       "in: prose | { prose: named }                   a reason, a description, a remark: deliberately not a position. `why`, `what`, `note`; `named`: one text, or texts under names",
    'untyped':     "in: untyped                                    a position whose domain nobody has declared yet — a standing debt, visible as one",
}


def _domain(d):
    """(facet, rule) for one attribute's `in:` — the internal record the interpreter has always read."""
    if isinstance(d, list):
        return 'values', list(d)
    if d in ('extent', 'ref', 'recurrence', 'bean_id'):
        return d, True
    if d == 'origin':
        return 'origin_of', True             # a value that IS an origin; `origin` is the facet saying a position's own
    if d == 'prose':
        return 'prose', True                 # words: any text, and only text — never a list or a map
    if d in ('untyped', 'id', 'any') or d is None:
        return None, None
    if isinstance(d, dict):
        if 'aspect' in d:
            return 'aspect', dict(d)
        if 'type' in d:
            return 'type', d['type']
        if 'entries' in d:
            return 'entries', dict(d['entries'] or {})
        if 'bean_id' in d:
            return 'bean_id', dict(d['bean_id'] or {})
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
        if d.get('prose') == 'named':
            return 'prose', 'named'          # one text, or texts under the names of what they say
    return 'unknown', d


def domain_kind(d):
    """The domain an attribute's `in:` names, as `schema_language.attr_domains` names it — `values`, `registry` (and
    `registry_from`), `pattern` (soft or not), `form_of`, … — or None where it names none the language offers. The key
    a domain's origin is read by: a position's origin is its domain's unless its record states one."""
    if isinstance(d, list):
        return 'values'
    if d is None:
        return 'untyped'
    if isinstance(d, str):
        return d if d in ('extent', 'ref', 'recurrence', 'bean_id', 'origin', 'prose', 'untyped', 'id', 'any') else None
    if isinstance(d, dict):
        for k in ('aspect', 'type', 'entries', 'bean_id', 'system', 'key_of', 'form_of', 'pattern', 'registry',
                  'registry_from', 'quantity', 'pointer', 'prose'):
            if k in d:
                return 'registry' if k == 'registry_from' else k
    return None


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
            'at_most': [list(g) for g in (sch.get('at_most_one_of') or []) if isinstance(g, list)],
            'keyed_by': ([sch['keyed_by']] if isinstance(sch.get('keyed_by'), str) else list(sch.get('keyed_by') or [])),
            'exclusive': dict(sch['exclusive']) if isinstance(sch.get('exclusive'), dict) else None,
            'matches': {'entry': list(sch.get('entry_must_match') or []),
                        'form_from_genos': sch.get('entry_form_from_genos_attr'),
                        'equal_genos_attr': sch.get('must_equal_genos_attr')},
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
        if facet_name == 'type' and rec['in'].get('unit') is not None:
            put('held_to', name, rec['in']['unit'])                         # 27.0: a position held to this unit or finer
        if facet_name == 'entries' and rec['in'].get('keyed_by') is not None:
            put('keyed_by', name, rec['in']['keyed_by'])
        if facet_name == 'entries' and rec['in'].get('one_of') is not None:
            put('nested_one_of', name, list(rec['in']['one_of']))            # 24.0: each entry inside carries one of these
        if facet_name == 'entries' and rec['in'].get('at_most_one_of') is not None:
            put('nested_at_most', name, [list(g) for g in rec['in']['at_most_one_of']])   # 24.0: and at most one of each group
        if isinstance(rec.get('default_from'), dict):
            put('default_from', name, dict(rec['default_from']))
        if rec.get('origin') is not None:
            put('origin', name, rec['origin'])  # where a value here comes from, where its domain's is wrong (`origin`)
            if isinstance(rec['origin'], dict) and rec['origin'].get('act') == 'read' and rec['origin'].get('by') == 'save':
                put('stamped', name, True)      # read from the clock by the save, never typed (dmpass.SAVE)
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


# ONE SENSE PER NAME (24.0; `senses`). What an attribute name means is read from its domain, across every term the law
# and a garden declare. A name with two domains, or one spelled as a term or a table that takes none of it, is a FINDING, and a finding is judged once, by a row of `senses` stating the one sense its uses share. A finding
# no row judges is a second sense; a row no finding calls for is stale — no judgment outlives its cause.
def sense_types(law):
    """{value type: the sense it gives}: a type on a dimension gives the dimension — its own, its system's, or the one
    its `either` members share — so a day and a moment are one sense, a position in time, at two precisions."""
    systems = {str(r.get('system')): r.get('dimension') for r in law.get('anchor_systems') or [] if isinstance(r, dict)}
    rows = {str(r.get('type')): r for r in law.get('value_types') or [] if isinstance(r, dict)}

    def dim(t, seen=()):
        r = rows.get(t) or {}
        d = r.get('dimension') or systems.get(str(r.get('system')))
        if d is None and isinstance(r.get('either'), list) and t not in seen:
            ds = {dim(str(x), seen + (t,)) for x in r['either']}
            d = ds.pop() if len(ds) == 1 else None
        return d
    return {t: ('dimension:' + str(dim(t))) if dim(t) else ('type:' + t) for t in rows}


def sense_domain(rec, types=None):
    """The sense an attribute's domain gives its name: the facet, and for a registry or a value type which one."""
    f, r = _domain(rec.get('in')) if isinstance(rec, dict) else (None, None)
    if f == 'registry':
        return 'registry:' + str(r.get('registry') or r.get('registry_from'))
    return ((types or {}).get(str(r)) or ('type:' + str(r))) if f == 'type' else str(f)


def sense_uses(terms, law=None):
    """{name: [(domain, where, facet, rule)]} for every attribute of the terms given, entries inside entries included."""
    out = {}
    types = sense_types(law or {})

    def walk(attrs, where):
        for n, rec in (attrs or {}).items() if isinstance(attrs, dict) else []:
            f, r = _domain(rec.get('in')) if isinstance(rec, dict) else (None, None)
            out.setdefault(str(n), []).append((sense_domain(rec, types), where, f, r))
            if f == 'entries':
                walk(r, f"{where}.{n}")
    for t in terms:
        if isinstance(t, dict) and t.get('term'):
            walk((t.get('schema') or {}).get('attrs'), str(t['term']))
    return out


def sense_findings(terms, law):
    """{name: why} for every name whose sense a row of `senses` must judge. `terms` are every term in force — the law's,
    its profiles', a garden's own; `law` is the front matter whose tables are names too. An attribute spelled as a table
    or a term is in its sense STRUCTURALLY where it takes a row of that table (or one of a table named for many of it),
    of the table whose key column carries its name, or a key of that term, or where it is the attribute of the term it
    names. A domain nobody has declared (`untyped`, `any`) gives no sense to compare, and a retired name is retired at
    its own position, which no attribute inside a term is."""
    tables = {k: v for k, v in law.items() if isinstance(v, list) and v and isinstance(v[0], dict)}
    keys = {k: next(iter(v[0]), None) for k, v in tables.items()}
    keys.update({str(rf.get('registry')): rf.get('key') for rf in law.get('registry_files') or [] if isinstance(rf, dict)})
    declared = {}
    for t in terms:
        if isinstance(t, dict) and t.get('term'):
            declared[str(t['term'])] = declared.get(str(t['term']), 0) + 1
    names = set(declared) | set(keys)
    out = {}
    for n, c in declared.items():
        if c > 1:
            out[n] = f"declared as a term {c} times"
    for n, uses in sorted(sense_uses(terms, law).items()):
        doms = sorted({d for d, _w, f, _r in uses if f is not None})
        if len(doms) > 1:
            out[n] = f"{len(doms)} domains: " + '; '.join(
                f"{d} ({', '.join(sorted({w for dd, w, _f, _r in uses if dd == d})[:3])})" for d in doms)
            continue
        if n in names:
            def structural(where, f, r):
                took = str(r.get('registry')) if f == 'registry' else str(r) if f == 'key_of' else None
                return took in (n, n + 's') or (f == 'registry' and str(keys.get(took)) == n) or where == n
            loose = sorted({w for _d, w, f, r in uses if not structural(w, f, r)})
            if loose:
                out[n] = f"a name the law gives a term or a table, used as {(doms or ['undeclared'])[0]} ({', '.join(loose[:3])})"
    return out


def sense_verdicts(terms, law, rows, own=None, law_terms=None):
    """(errors, judged): the findings no row of `senses` judges, and the rows no finding calls for, each as a sentence.
    `own` are a garden's rows among `rows`, the rest the law's; without `own`, every row is judged over these terms.
    With `law_terms`, the law's rows judged the domains those terms give: a garden's term giving a name the law judged
    another domain is a finding its own row judges, and a garden's row is stale where nothing of its own calls for it —
    the law's rows are judged over every profile, by the release, since a profile a garden leaves is still law."""
    found = sense_findings(terms, law)
    mine = [r for r in own or []]
    theirs = [r for r in rows or [] if not any(r is m for m in mine)] if own is not None else list(rows or [])
    errors, law_has, own_has = [], {}, {}
    for group, have in ((theirs, law_has), (mine, own_has)):
        for r in group:
            n = str(r.get('name')) if isinstance(r, dict) and r.get('name') else None
            if not n or not isinstance(r.get('sense'), str) or not r['sense'].strip():
                errors.append(f"senses: {r!r} is not {{name, sense}} with the sense in words")
            elif n in have:
                errors.append(f"senses: `{n}` is judged twice — one name, one sense")
            else:
                have[n] = r['sense']
    added = {}
    if law_terms is not None:
        was, now = sense_uses(law_terms, law), sense_uses(terms, law)
        for n in law_has:
            more = sorted({d for d, _w, f, _r in now.get(n, []) if f is not None} -
                          {d for d, _w, f, _r in was.get(n, []) if f is not None})
            if more:
                added[n] = f"{', '.join(more)} ({', '.join(sorted({w for d, w, _f, _r in now[n] if d in more})[:3])})"
    for n, why in sorted(found.items()):
        if n not in law_has and n not in own_has:
            errors.append(f"`{n}` has a second sense — {why}: rename one use, or judge the one sense its uses share "
                          f"in a row of `senses`")
    for n, why in sorted(added.items()):
        if n not in own_has:
            errors.append(f"`{n}` has a second sense — {why}, a domain the law's row does not judge: rename it, or "
                          f"judge in VOCAB.md's `senses` that this use is in the law's sense")
    calls = (set(found) - set(law_has)) | set(added) if own is not None else set(found)
    for n in sorted((set(own_has) if own is not None else set(law_has)) - calls):
        errors.append(f"senses: `{n}` is judged, and no longer a finding — the row outlives its cause; remove it")
    return errors, sorted((set(law_has) | set(own_has)) & (set(found) | set(added)))
