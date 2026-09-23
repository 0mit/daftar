#!/usr/bin/env python3
"""dmreform — rewrite a vocabulary from the old schema constructs into the law's own spelling (std-vocab 13.0).

    python3 bin/dmreform.py <vocabulary.md> [...]      # rewrite in place, then PROVE it
    python3 bin/dmreform.py --check <vocabulary.md>    # exit 1 if the document still uses an old construct

Until 13.0 one attribute's law was scattered across as many constructs as it had properties —
`entry_required_attrs`, `entry_values`, `entry_types`, `entry_in_registry`, `on_aspect`, `pointer_fields`… —
and stated again, for people, in the term's `entry_attrs:`. 13.0 states it once:

    attrs:
      <name>: { required: true, in: <domain>, meaning: "…" }

THE TRANSLATION IS A PURE FUNCTION of the term, so a garden never rewrites its own `local_terms` by hand:
`bin/dmupgrade.py` runs this when an upgrade crosses 13.0, inside its rollback.

IT PROVES ITSELF, per term, before it keeps anything: the form the OLD reader derives from the old text must
equal the form the NEW reader derives from the new text (`legacy_form` vs `dmform.attribute_form`). A
term that does not round-trip is reported and the whole file is left untouched.

COMMENTS SURVIVE. A comment inside a construct that is removed is not dropped: every comment line and trailing
comment in a removed span is re-emitted, verbatim and in order, directly above the new `attrs:` block. These
documents are edited as text because their comments carry the reasons; a translator that ate them would be the
seventh incident of its kind.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yaml
import dmform, dmparse

PROSE_HINT = ('why', 'what', 'note', 'meaning', 'consequence', 'evidence', 'defines', 'of', 'redactions',
              'restores', 'resolution', 'feasibility_why', 'relevant_scope', 'topic', 'source', 'owned_by_them',
              'registrar', 'registrant', 'mirrors_allowed')
REF_FORM_KEYS = ('bean', 'mapping', 'field')


# ------------------------------------------------------------------ THE OLD SPELLING (std-vocab <= 12.0)
# Its reader lives HERE and nowhere else: `bin/dmform.py` knows only how the law is spelled now.
ENTRY_FACETS = (('required', 'entry_required_attrs'), ('values', 'entry_values'), ('type', 'entry_types'),
                ('pattern', 'entry_pattern'), ('soft', 'entry_soft_pattern'), ('registry', 'entry_in_registry'),
                ('extent', 'entry_extents'), ('ref', 'entry_ref_fields'), ('one_of', 'entry_one_of'))
SELF_FACETS = (('required', 'required_attrs'), ('type', 'attr_types'), ('extent', 'attr_extents'),
               ('ref', 'ref_fields'))

def _legacy_aspects(sch):
    a = (sch or {}).get('on_aspect')
    if isinstance(a, dict):
        a = [a]
    return [x for x in (a or []) if isinstance(x, dict) and x.get('aspect')]



def legacy_form(term_def, sch):
    """THE OLD SPELLING's reader (std-vocab <= 12.0). Kept for `bin/dmreform.py`, which translates a vocabulary,
    and for the proof that the translation lost nothing. Nothing else may call it.
    The law of one term, keyed by attribute. `term_def` is the term's whole definition (for the meanings it
    gives its attributes); `sch` is the schema in force for it, overlays applied."""
    term_def, sch = term_def or {}, sch or {}
    has_entries = (sch.get('shape') in dmform.ENTRY_SHAPES or sch.get('on_aspect') or sch.get('entry_pattern_from_registry')
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
    for a in _legacy_aspects(sch):
        put('entry', 'aspect', a.get('attr') or a.get('aspect'),
            {k: v for k, v in a.items() if k != 'attr'})
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

    for name, key in dmform.VALUE_KEYS:
        if sch.get(key) is not None:
            form['value'][name] = sch[key]
    alt = sch.get('alt_form')
    if isinstance(alt, dict):
        form['alt'] = {'key': alt.get('key'), 'refs': list(alt.get('ref_fields') or [])}
    return form



# the constructs 13.0 retires, and the term-level doc maps that restated them
OLD_SCHEMA_KEYS = tuple(k for _f, k in ENTRY_FACETS if k != 'entry_one_of') + \
    tuple(k for _f, k in SELF_FACETS) + ('pointer_fields', 'on_aspect', 'entry_pattern_from_registry',
                                                'cross_aspect', 'entry_required_if', 'entry_expect_if')
OLD_TERM_KEYS = ('entry_attrs', 'attrs')


class CannotTranslate(Exception):
    pass


def _merge_orders(orders):
    """One attribute order that every given order is a sub-sequence of. Measured over std-vocab 12.0: the old
    constructs never disagree, so this always exists; if a garden's do, that is reported, not guessed at."""
    out, seen = [], set()
    before = {}
    for o in orders:
        for i, x in enumerate(o):
            before.setdefault(x, set()).update(o[:i])
    pending = []
    for o in orders:
        for x in o:
            if x not in pending:
                pending.append(x)
    while pending:
        ready = [x for x in pending if before[x] <= seen]
        if not ready:
            raise CannotTranslate(f"the old constructs list these attributes in contradictory orders: {pending}")
        x = ready[0]
        out.append(x); seen.add(x); pending.remove(x)
    return out


def new_schema_parts(term_def):
    """(attrs, cells, is_ref) — the new spelling's data for one term, from its old constructs."""
    sch = term_def.get('schema') or {}
    F = legacy_form(term_def, sch)
    facet_orders = [names for (sc, f), names in F['order'].items() if f not in ('meaning', 'one_of')]
    doc_order = [n for (sc, f), names in F['order'].items() if f == 'meaning' for n in names]
    names = _merge_orders(facet_orders + [[n for n in doc_order if not any(n in o for o in facet_orders)]])
    # keep the doc map's reading order wherever the constructs do not care
    attrs = {}
    for n in names:
        r = F['attrs'][n]
        if set(r) <= {'scope', 'one_of'}:
            continue                                   # a bare entry form: `entry_one_of` still declares it
        rec = {}
        if r.get('required'):
            rec['required'] = True
        if 'values' in r:        rec['in'] = list(r['values'])
        elif 'registry' in r:    rec['in'] = dict(r['registry'])
        elif 'aspect' in r:      rec['in'] = {k: v for k, v in r['aspect'].items() if k in ('aspect', 'default')}
        elif 'type' in r:        rec['in'] = {'type': r['type']}
        elif 'system_from' in r: rec['in'] = {'form_of': r['system_from'].get('registry'),
                                              'keyed_by': r['system_from'].get('keyed_by'),
                                              'take': r['system_from'].get('take')}
        elif 'pattern' in r:     rec['in'] = {'pattern': r['pattern']}
        elif 'soft' in r:        rec['in'] = dict({'pattern': r['soft'].get('pattern'), 'soft': True},
                                                  **({'why': r['soft']['why']} if r['soft'].get('why') else {}))
        elif 'extent' in r:      rec['in'] = 'extent'
        elif 'ref' in r:         rec['in'] = 'ref'
        elif 'pointer' in r:     rec['in'] = {'pointer': r['pointer']}
        elif F['self_ref'] and n in REF_FORM_KEYS:
            rec['in'] = 'id'
        else:                    rec['in'] = 'prose' if n in PROSE_HINT else 'untyped'
        if r.get('meaning') is not None:
            rec['meaning'] = r['meaning'] if isinstance(r['meaning'], str) else r['meaning']
        attrs[n] = rec
    cells = []
    for c in F['cells']:
        when = {k: ({'starts_with': v} if how == 'starts' else v) for k, (how, v) in c['when'].items()}
        if c['origin'] == 'required_if':
            cells.append({'when': when, 'requires': list(c['lacks'])})
        elif c['origin'] == 'expect_if':
            cells.append(dict({'when': when, 'expects': list(c['lacks'])}, **({'why': c['why']} if c['why'] else {})))
        else:
            cells.append(dict({'when': when, 'verdict': c['origin']}, **({'why': c['why']} if c['why'] else {})))
    return attrs, cells, F['self_ref']


def _comparable(form):
    """A form as the round trip compares it. `in: prose` is left out: the old spelling had no word for "words", and the
    translation says it of `what`/`why`/`note` — which adds one refusal, a list or a map where words belong, that the
    old form never read as words either. Everything else must come back as it went."""
    f = {k: v for k, v in form.items() if k != 'unknown'}
    f['order'] = {k: v for k, v in form['order'].items() if k[1] not in ('meaning', 'prose')}
    f['attrs'] = {n: {fk: fv for fk, fv in a.items() if fk != 'prose'} for n, a in (form.get('attrs') or {}).items()}
    return f


def translate_term(term_def):
    """The term's definition in the new spelling (data). Raises if it does not round-trip."""
    sch = term_def.get('schema')
    if not isinstance(sch, dict):
        return None
    if not any(k in sch for k in OLD_SCHEMA_KEYS) and not any(k in term_def for k in OLD_TERM_KEYS):
        return None
    attrs, cells, is_ref = new_schema_parts(term_def)
    new_sch = {k: v for k, v in sch.items() if k not in OLD_SCHEMA_KEYS}
    if is_ref:
        new_sch['is_ref'] = True
    if attrs:
        new_sch['attrs'] = attrs
    if cells:
        new_sch['cells'] = cells
    new_def = {k: v for k, v in term_def.items() if k not in OLD_TERM_KEYS}
    new_def['schema'] = new_sch
    old_f, new_f = legacy_form(term_def, sch), dmform.attribute_form(new_def, new_sch)
    if _comparable(old_f) != _comparable(new_f):
        diff = [k for k in _comparable(old_f) if _comparable(old_f)[k] != _comparable(new_f).get(k)]
        raise CannotTranslate(f"term `{term_def.get('term')}` does not round-trip; differs in {diff}: "
                              f"old={ {k: _comparable(old_f)[k] for k in diff} } new={ {k: _comparable(new_f).get(k) for k in diff} }")
    return new_def


# ------------------------------------------------------------------ emitting YAML text
_PLAIN = re.compile(r'^[A-Za-z0-9_][A-Za-z0-9_./-]*$')


def _scalar(v):
    if v is True:  return 'true'
    if v is False: return 'false'
    if v is None:  return 'null'
    if isinstance(v, (int, float)): return str(v)
    v = str(v)
    if _PLAIN.match(v) and v.lower() not in ('true', 'false', 'null', 'yes', 'no', 'on', 'off', 'none', '~'):
        return v
    if '\\' in v or '"' in v:
        if '\n' not in v:
            return "'" + v.replace("'", "''") + "'"
    import json
    return json.dumps(v, ensure_ascii=False)


def _flow(v):
    if isinstance(v, dict):
        return '{ ' + ', '.join(f"{_scalar(k)}: {_flow(x)}" for k, x in v.items()) + ' }'
    if isinstance(v, list):
        return '[' + ', '.join(_flow(x) for x in v) + ']'
    return _scalar(v)


def _block(new_sch_parts, indent):
    """The generated lines for is_ref / attrs / cells, at `indent` spaces."""
    attrs, cells, is_ref = new_sch_parts
    pad, out = ' ' * indent, []
    if is_ref:
        out.append(f"{pad}is_ref: true")
    if attrs:
        out.append(f"{pad}attrs:")
        width = max(len(n) for n in attrs) + 1
        for n, rec in attrs.items():
            out.append(f"{pad}  {(_scalar(n) + ':').ljust(width + 1)} {_flow(rec)}")
    if cells:
        out.append(f"{pad}cells:")
        for c in cells:
            out.append(f"{pad}  - {_flow(c)}")
    return out


def _span_end(lines, start, col):
    """First line after `start` that is not part of the block opened at `start` (whose key sits at column col)."""
    e = start + 1
    while e < len(lines):
        ln = lines[e]
        if ln.strip() and not ln.lstrip().startswith('#') and len(ln) - len(ln.lstrip()) <= col:
            break
        if ln.strip() == '---':
            break
        e += 1
    # give back trailing blank / comment lines that belong to whatever comes next
    while e - 1 > start and (not lines[e - 1].strip() or (lines[e - 1].lstrip().startswith('#')
                                                         and len(lines[e - 1]) - len(lines[e - 1].lstrip()) <= col)):
        e -= 1
    return e


def _comments(chunk):
    out = []
    for ln in chunk:
        st = ln.strip()
        if st.startswith('#'):
            out.append(st)
        else:
            m = re.search(r'\s#\s?(.*)$', ln)
            # a '#' inside quotes is not a comment: only take it when the text before it has balanced quotes
            if m:
                head = ln[:m.start()]
                if head.count('"') % 2 == 0 and head.count("'") % 2 == 0:
                    out.append('# ' + m.group(1).strip())
    return out


def _term_nodes(root):
    """Every term mapping node in a vocabulary document, wherever the law keeps terms."""
    def child(node, key):
        if isinstance(node, yaml.MappingNode):
            for k, v in node.value:
                if k.value == key:
                    return v
        return None
    seqs = [child(root, 'terms'), child(root, 'local_terms')]
    profs = child(root, 'profiles')
    if isinstance(profs, yaml.MappingNode):
        seqs += [child(v, 'terms') for _k, v in profs.value]
    for seq in seqs:
        if isinstance(seq, yaml.SequenceNode):
            for t in seq.value:
                if isinstance(t, yaml.MappingNode):
                    yield t


# The five terms that existed only to hold a copy of a registry's column (retired at 18.0), and the registry each stood for.
RETIRED_OWNERS = {'anchor_system': 'anchor_systems', 'unit': 'units', 'role': 'roles',
                  'storage_format': 'storage_formats', 'net_protocol': 'net_protocols'}
_OWNER_AT = re.compile(r'^(\s*(?:-\s+)?)at:\s*["\']?(%s)\.values["\']?\s*$' % '|'.join(RETIRED_OWNERS))


def rewrite_text(text):
    """(new_text, [terms rewritten]). Raises CannotTranslate, leaving the caller's file alone."""
    m = re.match(r'^---\n(.*?)\n---[ \t]*$', text, re.S | re.M)
    if not m:
        raise CannotTranslate("no front matter")
    fm_text = m.group(1)
    root = yaml.compose(fm_text)
    lines = text.split('\n')
    OFF = 1                                            # the opening fence
    edits, done = [], []
    for tnode in _term_nodes(root):
        tdef = yaml.safe_load(yaml.serialize(tnode))
        new_def = translate_term(tdef)
        if new_def is None:
            continue
        parts = new_schema_parts(tdef)
        keys = {k.value: (k, v) for k, v in tnode.value}
        sk, sv = keys['schema']
        harvested = []
        if sv.flow_style:
            # a one-line schema: regenerate it as a block, keeping the keys that survive in their order
            s0 = sk.start_mark.line + OFF
            s1 = sv.end_mark.line + OFF + 1
            harvested += _comments(lines[s0:s1])
            col = sk.start_mark.column
            kept = {k: v for k, v in (tdef.get('schema') or {}).items() if k not in OLD_SCHEMA_KEYS}
            new = [' ' * col + 'schema:'] + [f"{' ' * (col + 2)}{k}: {_flow(v)}" for k, v in kept.items()] \
                + _block(parts, col + 2)
            edits.append((s0, s1, new, harvested, col + 2, 1 + len(kept)))
        else:
            ccol = sv.value[0][0].start_mark.column if sv.value else sk.start_mark.column + 2
            last_end = None
            for k, v in sv.value:
                if k.value in OLD_SCHEMA_KEYS:
                    a = k.start_mark.line + OFF
                    b = _span_end(lines, a, ccol)
                    harvested += _comments(lines[a:b])
                    edits.append((a, b, [], None, None, None))
            s_end = _span_end(lines, sk.start_mark.line + OFF, sk.start_mark.column)
            edits.append((s_end, s_end, _block(parts, ccol), harvested, ccol, 0))
        for dk in OLD_TERM_KEYS:
            if dk in keys:
                k, v = keys[dk]
                a = k.start_mark.line + OFF
                b = _span_end(lines, a, k.start_mark.column) if not v.flow_style else v.end_mark.line + OFF + 1
                # the doc map's OWN comments travel too
                harvested += [c for c in _comments(lines[a:b]) if c not in harvested and not _is_value_line(c)]
                edits.append((a, b, [], None, None, None))
        done.append(tdef.get('term'))
    for a, b, new, harvested, col, at in sorted(edits, key=lambda e: (e[0], e[1]), reverse=True):
        block = list(new)
        if harvested:
            note = [' ' * col + c for c in harvested]
            block = block[:at] + note + block[at:]
        lines[a:b] = block
    # 18.0 — a registry is its own enum owner: a vacancy for an unused row is addressed AT the registry.
    for i, line in enumerate(lines):
        mm = _OWNER_AT.match(line)
        if mm:
            lines[i] = f'{mm.group(1)}at: "registry:{RETIRED_OWNERS[mm.group(2)]}"'
            if 'vacancies' not in done:
                done.append('vacancies')
    return '\n'.join(lines), done


def _is_value_line(_c):
    return False


def uses_old_constructs(text):
    fm, _ = dmparse.split_front_matter(text)
    data = yaml.safe_load(fm) or {}
    terms = list(data.get('terms') or []) + list(data.get('local_terms') or [])
    for p in (data.get('profiles') or {}).values():
        terms += list((p or {}).get('terms') or [])
    bad = [('vacancies', [str(v.get('at'))]) for v in (data.get('vacancies') or [])
           if isinstance(v, dict) and str(v.get('at') or '').split('.values')[0] in RETIRED_OWNERS and str(v.get('at')).endswith('.values')]
    for t in terms:
        if isinstance(t, dict):
            hit = [k for k in OLD_SCHEMA_KEYS if k in (t.get('schema') or {})] + \
                  [k for k in OLD_TERM_KEYS if k in t]
            if hit:
                bad.append((t.get('term'), hit))
    return bad


def rewrite_file(path):
    import dmsafe
    text = open(path, encoding='utf-8').read()
    new_text, done = rewrite_text(text)
    if not done:
        return []
    # the proof, on the TEXT that will be written: every term parses, and none still uses an old construct
    left = uses_old_constructs(new_text)
    if left:
        raise CannotTranslate(f"{path}: still uses old constructs after rewriting: {left}")
    old_fm, new_fm = yaml.safe_load(dmparse.split_front_matter(text)[0]), yaml.safe_load(dmparse.split_front_matter(new_text)[0])

    def terms_of(d):
        ts = list(d.get('terms') or []) + list(d.get('local_terms') or [])
        for p in (d.get('profiles') or {}).values():
            ts += list((p or {}).get('terms') or [])
        return {t['term'] + '#' + str(i): t for i, t in enumerate(ts) if isinstance(t, dict) and t.get('term')}
    o, n = terms_of(old_fm), terms_of(new_fm)
    if list(o) != list(n):
        raise CannotTranslate(f"{path}: the rewrite changed which terms exist")
    for k in o:
        of = legacy_form(o[k], o[k].get('schema') or {}) if uses_old_term(o[k]) else dmform.attribute_form(o[k], o[k].get('schema') or {})
        nf = dmform.attribute_form(n[k], n[k].get('schema') or {})
        if _comparable(of) != _comparable(nf):
            raise CannotTranslate(f"{path}: `{k}` reads differently after the rewrite")
        rest_o = {a: b for a, b in o[k].items() if a not in OLD_TERM_KEYS + ('schema',)}
        rest_n = {a: b for a, b in n[k].items() if a != 'schema'}
        if rest_o != rest_n:
            raise CannotTranslate(f"{path}: `{k}` lost or changed something outside its schema: "
                                  f"{sorted(set(rest_o) ^ set(rest_n)) or 'a value'}")
    open(path, 'w', encoding='utf-8').write(new_text)
    return done


def uses_old_term(t):
    return any(k in (t.get('schema') or {}) for k in OLD_SCHEMA_KEYS) or any(k in t for k in OLD_TERM_KEYS)


def main(argv):
    check = '--check' in argv
    paths = [a for a in argv if not a.startswith('--')]
    if not paths:
        print(__doc__); return 2
    rc = 0
    for p in paths:
        if check:
            bad = uses_old_constructs(open(p, encoding='utf-8').read())
            for term, hit in bad:
                print(f"{p}: `{term}` still uses {hit}")
            rc |= 1 if bad else 0
            continue
        try:
            done = rewrite_file(p)
            print(f"{p}: {len(done)} term(s) rewritten" + (f" — {', '.join(done)}" if done else ""))
        except CannotTranslate as e:
            print(f"{p}: NOT REWRITTEN — {e}"); rc = 1
    return rc


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
