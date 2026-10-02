#!/usr/bin/env python3
"""dmcrosswalk — another standard's records carried into beans and back, by a table of the law (24.0, step 11).

    python3 bin/dmcrosswalk.py to fhir <observations.json>      # FHIR R5 Observations -> `observations` entries
    python3 bin/dmcrosswalk.py to dwc <occurrences.csv>          # Darwin Core occurrences -> `located_at` entries
    python3 bin/dmcrosswalk.py back fhir <bean> [<key> ...]      # a bean's entries -> FHIR R5 Observations
    python3 bin/dmcrosswalk.py back dwc <bean> [<bean> ...]      # beans' positions -> Darwin Core occurrences

THE TABLE IS THE WHOLE CROSSWALK. Each is a registry of the law (`registry_files`, `crosswalk-<name>`), its rows
{<name>, daftar, note}. This tool reads them and knows no standard's field by name. A row is one of:
  <path>                   a field carried as it is written, to the entry path in `daftar`;
  <path>=<text with {}>    a field whose value has that form: only the part at `{}` is carried;
  <path>=<value>, daftar -  a value every record carried has, and every record carried back is given;
  <path>.coding            a coding {system, code}, carried as {scheme, code}: the scheme whose `url` is the system;
  <prefix>:<code>          a code crossed to `<attr>:<value>` wherever the entry path ends in that attr (a unit);
  form:<daftar path>       the form a value is composed in from parts, each part a row to `<daftar path>#<part>`;
  given:<daftar path>      a value given to every entry carried here, and required of every entry carried back.

IN A GARDEN OF THE CORE (v1 part 7) an entry the table gives is written as the core's statement — an observation a
`measure` (`property` its `as`, a coded result its `result`), a position a `be` as location with what it holds there in
`placed` — and read back from it; `to` prints the statements, and what a statement has no place for is listed too.

WHAT THE TABLE CANNOT CARRY IS LISTED, NEVER DROPPED: every field of a record that no row carried is printed as
`not carried: <path>`, in both directions. So a round trip gives back every field it did not list, equal field for
field — the proof is test/crosswalk.py.
"""
import csv, io, json, os, re, sys
from decimal import Decimal

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import yaml


def runs_core():
    """True in a garden that runs the core (GARDEN.md pins `core@…`, bin/check.py the one reader of the pin)."""
    try:
        import check
        return check.runs_core(check.pin(ROOT))
    except Exception:
        return False


def _law():
    if runs_core():                         # the core's registries (v1 part 7), with the garden's own schemes beside
        import dmknowledge
        k = dmknowledge.Knowledge(ROOT)
        return list(k.decl.values()), list(k.schemes.values())
    fm = dmparse.loads(dmparse.split_front_matter(open(os.path.join(ROOT, 'seed', 'std-vocab.md'), encoding='utf-8').read())[0])
    if os.path.exists(os.path.join(ROOT, 'VOCAB.md')):
        import dmcheck
        return fm.get('registry_files') or [], dmcheck.registry('knowledge_schemes') or []
    return fm.get('registry_files') or [], fm.get('knowledge_schemes') or []


class Table:
    """One crosswalk, read from its registry file."""

    def __init__(self, name):
        files, schemes = _law()
        row = next((r for r in files if isinstance(r, dict) and str(r.get('registry', '')).startswith('crosswalk-')
                    and r.get('key') == name), None)
        if row is None:
            raise SystemExit(f"dmcrosswalk: the law declares no crosswalk keyed by '{name}'")
        header, rows = dmparse.table_read(open(os.path.join(ROOT, row['file']), encoding='utf-8').read())
        self.name, self.prefix = name, None
        self.paths, self.consts, self.values, self.forms, self.given = [], [], {}, {}, {}
        for src, dst, _note in rows:
            if src.startswith('form:'):
                self.forms[src[5:]] = dst
            elif src.startswith('given:'):
                p, _, v = dst.partition('=')
                self.given[p] = v
            elif re.match(r'^[a-z]+:[^.]*$', src) and ':' in dst and not src.startswith(name + ':'):
                attr, _, v = dst.partition(':')
                self.values.setdefault(attr, {})[src.partition(':')[2]] = v
            else:
                path, eq, form = src.partition('=')
                if '.' in path and self.prefix is None and not path.startswith(name + ':'):
                    self.prefix = path.split('.')[0]
                path = path[len(self.prefix) + 1:] if self.prefix and path.startswith(self.prefix + '.') else \
                    path[len(name) + 1:] if path.startswith(name + ':') else path
                if dst == '-':
                    self.consts.append((path, form))
                else:
                    self.paths.append((path, form if eq else None, dst))
        self.by_url = {str(s.get('url')): s.get('scheme') for s in schemes if isinstance(s, dict) and s.get('url')}
        self.url_of = {v: k for k, v in self.by_url.items()}


def flatten(node, path=''):
    """{path: scalar} of a record: a list's items are `[i]`, so nothing in it is lost."""
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(flatten(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(flatten(v, f"{path}[{i}]"))
    else:
        out[path] = node
    return out


def _first(leaf):
    """the path with each `[0]` stepped through, or None where it goes through another item."""
    if re.search(r'\[[1-9][0-9]*\]', leaf):
        return None
    return leaf.replace('[0]', '')


def _set(d, path, v):
    parts = path.split('.')
    for p in parts[:-1]:
        d = d.setdefault(p, {})
    d[parts[-1]] = v


def _get(d, path):
    for p in path.split('.'):
        if not isinstance(d, dict) or p not in d:
            return None
        d = d[p]
    return d


def _pop(d, path):
    parts = path.split('.')
    for p in parts[:-1]:
        d = d.get(p, {})
    d.pop(parts[-1], None)


def _put(d, path, v):
    """into a record, stepping through a list at each step the standard makes a list of (a FHIR path's `coding`,
    `performer`, `note`): the path's own `[0]`s are restored from where the source had them."""
    cur = d
    parts = path.split('.')
    for i, p in enumerate(parts):
        last = i == len(parts) - 1
        name, idx = (p[:-3], True) if p.endswith('[0]') else (p, False)
        if last and not idx:
            cur[name] = v
        elif idx:
            lst = cur.setdefault(name, [{}])
            if last:
                lst[0] = v
            cur = lst[0]
        else:
            cur = cur.setdefault(name, {})


LISTS = {'fhir': ('coding', 'performer', 'note')}


def _listed(table, path):
    """a record path, with `[0]` after each part the standard writes as a list."""
    lists = LISTS.get(table.name, ())
    return '.'.join(p + '[0]' if p in lists else p for p in path.split('.'))


def to(table, record):
    """(bean, key or None, entry, not carried) — one record of the standard as one entry."""
    leaves = flatten(record)
    used, entry, bean, key, parts, listed = set(), {}, None, None, {}, []

    def take(path):
        return [(leaf, v) for leaf, v in leaves.items() if _first(leaf) == path]

    for path, form in table.consts:
        for leaf, v in take(path):
            if str(v) == form:
                used.add(leaf)
    for path, form, dst in table.paths:
        if path.endswith('.coding'):
            got = dict((leaf.rsplit('.', 1)[1], (leaf, v)) for leaf, v in leaves.items()
                       if _first(leaf.rsplit('.', 1)[0]) == path)
            sys_, code = got.get('system'), got.get('code')
            if sys_ and code and table.by_url.get(str(sys_[1])):
                _set(entry, dst.split('.', 1)[1] if '.' in dst else dst,
                     f"{table.by_url[str(sys_[1])]}:{code[1]}")
                used.update({sys_[0], code[0]})
            continue
        for leaf, v in take(path):
            v = str(v)
            if form:
                m = re.fullmatch(re.escape(form).replace(r'\{\}', '(.+)'), v)
                if not m:
                    continue
                v = m.group(1)
            attr = dst.rsplit('.', 1)[-1].split('#')[0]
            if attr in table.values:
                if v not in table.values[attr]:
                    continue
                v = table.values[attr][v]
            if dst == 'bean':
                bean = v
            elif dst == 'key':
                key = v
            elif '#' in dst:
                parts.setdefault(dst.split('#')[0], {})[dst.split('#')[1]] = v
            else:
                _set(entry, dst.split('.', 1)[1], v)
            used.add(leaf)
    for dst, got in parts.items():
        form = table.forms.get(dst, '')
        want = re.findall(r'\{(\w+)\}', form)
        if all(w in got for w in want):
            _set(entry, dst.split('.', 1)[1], form.format(**got))
        else:
            used -= {leaf for leaf in leaves if any(_first(leaf) == p for p, _f, d in table.paths if d.split('#')[0] == dst)}
    # A COUNT WITHOUT ITS UNIT IS NO VALUE: where the unit did not cross, the whole quantity is listed
    for path, _form, dst in table.paths:
        if dst.endswith('.count') and '.' in dst:
            rel = dst.split('.', 1)[1].rsplit('.', 1)[0]
            q = _get(entry, rel)
            if isinstance(q, dict) and 'unit' not in q and any(d == dst[:-6] + '.unit' for _p, _f, d in table.paths):
                _pop(entry, rel)
                src = path.rsplit('.', 1)[0]
                used -= {leaf for leaf in leaves if (_first(leaf) or '').startswith(src + '.')}
    for dst, v in table.given.items():
        rel = dst.split('.', 1)[1]
        parent = rel.rsplit('.', 1)[0] if '.' in rel else ''
        if not parent or _get(entry, parent) is not None:
            _set(entry, rel, v)
    listed = sorted(leaf for leaf in leaves if leaf not in used)
    return bean, key, entry, listed


def back(table, bean, key, entry):
    """(record, not carried) — one entry as one record of the standard."""
    rec, listed = {}, []
    ent = flatten(entry)
    used = set()
    for dst, v in table.given.items():
        rel = dst.split('.', 1)[1]
        if rel in ent:
            if str(ent[rel]) == v:
                used.add(rel)
    for path, form, dst in table.paths:
        if dst in ('bean', 'key'):
            v = bean if dst == 'bean' else key
        elif path.endswith('.coding'):
            rel = dst.split('.', 1)[1] if '.' in dst else dst
            c = _get(entry, rel)
            sch, code = dmparse.split_coding(c)
            if sch in table.url_of:
                _put(rec, _listed(table, path), {'system': table.url_of[sch], 'code': code})
                used.add(rel)
            continue
        elif '#' in dst:
            whole, part = dst.split('#')
            rel = whole.split('.', 1)[1]
            v = None
            if rel in ent:
                m = re.fullmatch(re.sub(r'\\\{(\w+)\\\}', r'(?P<\1>.+?)', re.escape(table.forms[whole])), str(ent[rel]))
                if m:
                    v = m.group(part)
                    used.add(rel)
        else:
            rel = dst.split('.', 1)[1]
            v = ent.get(rel)
            if v is None:
                continue
            attr = rel.rsplit('.', 1)[-1]
            if attr in table.values:
                inv = {u: c for c, u in table.values[attr].items()}
                if str(v) not in inv:
                    continue
                v = inv[str(v)]
            used.add(rel)
        if v is None:
            continue
        v = str(v)
        if form:
            v = form.replace('{}', v)
        _put(rec, _listed(table, path), v)
    for path, form in table.consts:
        parent = path.rsplit('.', 1)[0] if '.' in path else ''
        if not parent or _get(rec, parent) is not None:
            _put(rec, _listed(table, path), form)
    listed = sorted(p for p in ent if p not in used)
    return rec, listed


def _numbers(node):
    """a FHIR record's decimals as written: `value` is a JSON number there, a count's text here."""
    if isinstance(node, dict):
        return {k: (Decimal(v) if k == 'value' and isinstance(v, str) else _numbers(v)) for k, v in node.items()}
    if isinstance(node, list):
        return [_numbers(v) for v in node]
    return node


def dumps(node, indent=0):
    """JSON with each decimal as written."""
    pad = '  ' * (indent + 1)
    if isinstance(node, dict):
        return '{\n' + ',\n'.join(f"{pad}{json.dumps(k)}: {dumps(v, indent + 1)}" for k, v in node.items()) + \
            '\n' + '  ' * indent + '}'
    if isinstance(node, list):
        return '[\n' + ',\n'.join(pad + dumps(v, indent + 1) for v in node) + '\n' + '  ' * indent + ']'
    if isinstance(node, Decimal):
        return str(node)
    return json.dumps(node, ensure_ascii=False)


def read_records(name, text):
    if name == 'fhir':
        data = json.loads(text, parse_float=Decimal, parse_int=Decimal)
        return data if isinstance(data, list) else [data]
    return [{k: v for k, v in row.items() if v != ''} for row in csv.DictReader(io.StringIO(text))]


def term_of(table):
    dsts = [d for _p, _f, d in table.paths if '.' in d] + list(table.given)
    return dsts[0].split('.')[0].split('#')[0] if dsts else 'observations'


def carried_to(name, text):
    """{bean: {term: entries}}, and what was not carried."""
    table = Table(name)
    term = term_of(table)
    out, listed = {}, []
    for i, record in enumerate(read_records(name, text)):
        bean, key, entry, miss = to(table, record)
        listed += [f"record {i + 1}: {m}" for m in miss]
        if bean is None:
            listed.append(f"record {i + 1}: no bean — the whole record")
            continue
        got = out.setdefault(bean, {})
        if key is not None:
            got.setdefault(term, {})[key] = entry
        else:
            got.setdefault(term, []).append(entry)
    return out, listed


def carried_back(name, beans):
    """[record], and what was not carried: `beans` is {bean: front matter}."""
    table = Table(name)
    term = term_of(table)
    recs, listed = [], []
    for bean, fm in beans.items():
        got = fm.get(term) or ({} if any(d == 'key' for _p, _f, d in table.paths) else [])
        items = got.items() if isinstance(got, dict) else [(None, e) for e in got]
        for key, entry in items:
            rec, miss = back(table, bean, key, entry)
            listed += [f"{bean}:{term}{'.' + key if key else ''}: {m}" for m in miss]
            recs.append(_numbers(rec) if name == 'fhir' else rec)
    return recs, listed


def write_records(name, recs):
    if name == 'fhir':
        return dumps(recs) + '\n'
    cols = [p for p, _f, _d in Table(name).paths]
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=[c for c in cols if any(c in r for r in recs)], lineterminator='\n')
    w.writeheader()
    w.writerows(recs)
    return buf.getvalue()


# ============================================================================ a garden of the core (v1 part 7)
# The table carries a record to today's entry and back, and knows no statement: in a garden of the core an observation
# is a `measure` and a position a `be` as location, so each entry the table gives is written as its statement, and each
# statement read back as the entry (core/measures.py), the one map between the two. What the statement has no place for
# is listed, as the table lists what it cannot carry.
MEASURE_ROLES = (('property', 'as'), ('value', 'value'), ('at', 'at'), ('by', 'by'), ('method', 'method'),
                 ('code', 'result'), ('presence', 'presence'), ('note', 'note'))


def _ucum(x, codes):
    """`x` with each unit named by its UCUM code: the code the law attaches today's name to."""
    if isinstance(x, dict):
        return {k: (codes.get(v, v) if k == 'unit' and isinstance(v, str) else _ucum(v, codes)) for k, v in x.items()}
    if isinstance(x, list):
        return [_ucum(v, codes) for v in x]
    return str(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else x


def as_statements(term, entries):
    """([statement], [what has no place]) — today's entries of `term` written as the core's statements."""
    sys.path.insert(0, ROOT)
    from core import measures, frame, standards
    codes = {v: k for k, v in measures.unit_names(ROOT).items()}
    out, miss = [], []
    if term == 'observations':
        for key, e in (entries or {}).items():
            roles = {'id': key, 'of': 'self'}
            for attr, role in MEASURE_ROLES:
                if e.get(attr) is not None:
                    roles[role] = _ucum(e[attr], codes) if role == 'value' else str(e[attr])
            miss += [f"{term}.{key}.{a}: no role of `measure`" for a in e if a not in dict(MEASURE_ROLES)]
            out.append({'measure': roles})
    elif term == 'located_at':
        systems = standards.here(ROOT).systems
        attrs = set(((measures_form() or {}).get('attrs') or {}))
        for i, e in enumerate(entries or []):
            text = None
            for t in (str(e.get('at')), f"{e.get('system')}:{e.get('at')}"):
                try:
                    if frame.read(t, systems).system == e.get('system'):
                        text = t
                        break
                except frame.Refused:
                    continue
            if text is None:
                miss.append(f"{term}[{i}]: {e.get('system')}:{e.get('at')} is no position of the core's systems")
                continue
            roles = {'id': f"at-{i + 1}", 'by': 'self', 'at': text, 'as': 'location'}
            placed = {a: _ucum(v, codes) for a, v in e.items() if a in attrs}
            if placed:
                roles['placed'] = placed
            if e.get('note') is not None:
                roles['note'] = str(e['note'])
            miss += [f"{term}[{i}].{a}: no place in `be`" for a in e if a not in attrs | {'system', 'at', 'note'}]
            out.append({'be': roles})
    else:
        miss.append(f"{term}: no statement of the core is written for it here")
    return out, miss


def measures_form():
    sys.path.insert(0, ROOT)
    from core.check import garden_law
    return garden_law(ROOT).forms.get('placement')


def core_entries(bean, want=()):
    """{term: entries} of a bean of the core, read from its statements: each `measure` an entry of `observations`, each
    `be` as location one of `located_at` (bin/garden.py `terms`)."""
    sys.path.insert(0, ROOT)
    from core import measures, engine
    import dmgarden
    G = engine.Garden.read(ROOT)
    b = G.beans[bean]
    names = measures.unit_names(ROOT)
    obs = {}
    for _i, verb, r in b.items:
        if verb == 'measure' and 'held' not in r and isinstance(r.get('id'), str) and (not want or r['id'] in want):
            e = {attr: measures.in_today_words(r[role], names) if role == 'value' else r[role]
                 for attr, role in MEASURE_ROLES if r.get(role) is not None}
            obs[r['id']] = e
    located = [{k: v for k, v in e.items() if k != 'note' or v} for e in dmgarden.terms(b, G.beans).get('located_at') or []]
    return {'observations': obs, 'located_at': located}


def main(argv):
    if len(argv) < 3 or argv[0] not in ('to', 'back'):
        print(__doc__.strip().split('\n\n')[1])
        return 2
    name = argv[1]
    core = runs_core()
    if argv[0] == 'to':
        out, listed = carried_to(name, open(argv[2], encoding='utf-8').read())
        for bean, terms in out.items():
            print(f"# beans/{bean}.md")
            if core:
                stmts = []
                for term, entries in terms.items():
                    got, miss = as_statements(term, entries)
                    stmts += got
                    listed += [f"{bean}: {m}" for m in miss]
                print(yaml.safe_dump({'statements': stmts}, sort_keys=False, allow_unicode=True,
                                     default_flow_style=None).rstrip())
                continue
            print(yaml.safe_dump(terms, sort_keys=False, allow_unicode=True, default_flow_style=None).rstrip())
    else:
        want = argv[3:] if name == 'fhir' else []
        ids = [argv[2]] if name == 'fhir' else argv[2:]
        beans = {}
        for b in ids:
            if core:
                beans[b] = core_entries(b, want)
                continue
            fm = dmparse.loads(dmparse.split_front_matter(open(os.path.join(ROOT, 'beans', b + '.md'), encoding='utf-8').read())[0])
            if want:
                fm = {**fm, 'observations': {k: v for k, v in (fm.get('observations') or {}).items() if k in want}}
            beans[b] = fm
        recs, listed = carried_back(name, beans)
        sys.stdout.write(write_records(name, recs))
    for m in listed:
        print(f"not carried: {m}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
