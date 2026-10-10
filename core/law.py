"""law — the face and the rows, loaded as one law and proved consistent with itself.

The face is `core/law/core.yaml`: the seven roles, the shapes, the grammar's words, the two figures, the order (natures,
lines, levels, conditions, the crown), the face's verbs and the twenty-one rules. The verbs beyond the face are rows,
`core/law/verbs.yaml`. A garden adds rows of its own in its VOCAB.md, under these keys only:

  kinds         { kind, nature, line?, level?, rung?, meaning? }       what a bean records
  levels        { level, line, stands: [{ at, as, while? }], meaning? } the detailed steps of the lines (our knowledge tree)
  namespaces    { namespace, once?, meaning? }                         who gives names, and whether once (beside the
                                                                       standards' own, core/law/namespaces.yaml)
  flows         { flow?, from, to, through, as?, grant, why?,          the flow table: which passes stand. A garden's
                  party?, basis? }                                     row refuses, or grants the party it names where
                                                                       the core's row of its name is `ratified` (part 8)
  flow_sources  [ name, … ]                                            the flow law's sources beside the layers
  standing      { layer, holds: [pattern, …], meaning? }               which files sit in which layer
  verbs         rows in the form of verbs.yaml                         a garden's own verbs
  units         { unit, name, quantity, factor?, ucum?, why? }         a unit in UCUM, its English name attached,
                                                                       its size in the coherent unit (two whole numbers)
  systems       a row in the form of systems.yaml `systems`            a system of positions of the garden's own: its
                                                                       sites, its grid (v1 part 7)
  schemes       a row of `knowledge_schemes`                           a scheme of codes of the garden's own (part 7)
  files         { registry, file, key, format? }                       where the rows a system or a scheme of its own
                                                                       names are kept: extracts/ (part 7)
  tables        { <table>: [row, …] }                                  rows added to a verbs' table or a standard's
  exclusive     { verb, why? }                                         a verb whose `at` holds one being once (rule room)

A garden's kind, level, namespace, verb or unit may say `vacant: <why>`: a row no bean uses yet (rule vacancy).

A row may not take a name the face or another row has: the law is one, and a second row of one name is two laws.
Every value is a string (core/read.py): a flag is the string `true`."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import read, standards  # noqa: E402

LAW_DIR = os.path.join(HERE, 'law')
ROW_FILES = ('levels.yaml', 'layers.yaml', 'kinds.yaml',  # the bodies' levels, the layers and standing, the kinds (the
                                                           # standards' tables are read by core/standards.py),
             'units.yaml', 'namespaces.yaml', 'flows.yaml')  # and the units in UCUM, each with the law's
                                                           # English name, the namespaces the standards give names in,
                                                           # and the flow law: its methods and rows (v1 part 8)
FLOW_LAW = ('methods', 'metadata', 'dropped')              # what core/law/flows.yaml holds beside its rows, and a
                                                           # garden's VOCAB.md does not
GRANTS = ('granted', 'refused', 'ratified')
ROW_KEYS = {'kinds': 'kind', 'levels': 'level', 'namespaces': 'namespace', 'flows': None, 'flow_sources': None,
            'standing': 'layer', 'verbs': 'verb', 'tables': None, 'units': 'unit', 'exclusive': 'verb',
            'systems': 'system', 'schemes': 'scheme', 'files': 'registry'}
ROW_FIELDS = {
    'kinds': {'kind', 'nature', 'line', 'level', 'rung', 'meaning', 'vacant'},
    'levels': {'level', 'line', 'stands', 'meaning', 'frame_of', 'vacant'},
    'namespaces': {'namespace', 'once', 'pattern', 'checked_by', 'kept', 'meaning', 'vacant'},
    'flows': {'flow', 'from', 'to', 'through', 'as', 'grant', 'keeper', 'party', 'basis', 'why'},
    'standing': {'layer', 'holds', 'meaning'},
    'verbs': {'verb', 'meaning', 'roles', 'qualifiers', 'required', 'choice', 'default', 'replaces', 'home', 'figure',
              'vacant'},
    'units': {'unit', 'name', 'quantity', 'factor', 'per', 'ucum', 'why', 'vacant'},
    'systems': {'system', 'dimension', 'pattern', 'form_note', 'example', 'levels', 'restrictions', 'neighbours',
                'complement', 'calendar', 'reckoning', 'day_begins', 'datum', 'boundaries_in', 'cells_in', 'checked_by',
                'crosswalk', 'establishes', 'resolves_through', 'same_ground_as', 'transport', 'unit_symbols', 'within',
                'overlay', 'meaning', 'why', 'vacant'},
    'schemes': {'scheme', 'classifies', 'publisher', 'url', 'levels', 'neighbours', 'sources', 'holding', 'licence',
                'release', 'sensitive', 'code_pattern', 'relations', 'labels', 'crosswalk', 'same_ground_as', 'within',
                'file', 'key', 'format', 'meaning', 'vacant'},
    'files': {'registry', 'file', 'key', 'format'},
    'exclusive': {'verb', 'why'},
}
LINES = 'lines.yaml'                                       # the forms of a line and a reading's grammar (v1 part 6)
TOOLS, VACANCIES = 'tools.yaml', 'vacancies.yaml'          # the tools by their verbs; what nothing takes up yet (part 9)
PROFILES = 'profiles.yaml'                                 # what a garden takes up beside the core (v1 part 11)
FORMS = 'forms.yaml'                                       # the forms part 12b adds, written by hand: a grant's cover,
                                                           # a settlement, a weighing, a channel
VALUES = 'values.yaml'                                     # what a value is to a reader: the tree the widgets answer to
MEASURES = 'measures.yaml'                                 # the forms of a measure: a region, a repetition, a clause's
                                                           # terms and a placement's, how well a value is known (part 7)
GARDEN = 'VOCAB.md'                                        # where a garden's own rows are read from
SPEC_KEYS = {'shape', 'table', 'nature', 'rung', 'many', 'keyed', 'form'}
FACE_TABLES = ('ways', 'modes', 'acquisitions', 'placements', 'complements', 'knowing')
TRUE = 'true'
MANIFEST_FORMS = ('pin', 'bean', 'zone', 'text', 'texts')   # the manifest's forms the engine knows by name; a pattern's
                                                            # are core.yaml's `manifest_forms`


def listed(x):
    """A value that may be written as one or as a list, as a list."""
    if x is None:
        return []
    return list(x) if isinstance(x, list) else [x]


def shapes_of(spec):
    return listed(spec.get('shape')) if isinstance(spec, dict) else []


# THE TABLES KEEP THEIR FORMS (today's `registry_forms`, 26.0; the core's since v1 part 13): a table of rows declares its
# columns, each `required` or `optional`, and a row holds the required ones and no other. A column no form declares is a
# note riding on the law, or a fact of a new kind the form must first be given; a required one a row lacks leaves a
# reader of that row without what every sibling gives. The standards' files declare them under `forms`, the files of a
# line, a measure and the flow law under `columns` (their `forms` are the forms a qualifier holds).
COLUMNED = (('systems.yaml', 'forms'), ('places.yaml', 'forms'), ('protocols.yaml', 'forms'), ('quantities.yaml', 'forms'),
            ('registries.yaml', 'forms'), (LINES, 'columns'), (MEASURES, 'columns'), ('flows.yaml', 'columns'),
            (VALUES, 'columns'))


def columns_problems(law_dir, std_dir=None):
    """[(where, message)]: each table of rows in the files whose tables have forms, held to its form."""
    out = []
    for name, key in COLUMNED:
        d = std_dir if std_dir and key == 'forms' else law_dir
        path = os.path.join(d, name)
        if not os.path.isfile(path):
            continue
        data = read.data(path)
        forms = data.get(key) if isinstance(data.get(key), dict) else {}
        for table, rows in data.items():
            if table in ('forms', 'columns') or not (isinstance(rows, list) and rows
                                                     and all(isinstance(r, dict) for r in rows)):
                continue
            cols = forms.get(table)
            if not isinstance(cols, dict):
                out.append((f"core/law/{name} {table}", f"a table of rows with no form under `{key}`: its columns are "
                                                        f"declared there, each `required` or `optional`"))
                continue
            req = {c for c, v in cols.items() if v == 'required' or (isinstance(v, dict) and v.get('required') == 'true')}
            for row in rows:
                n = row.get(next(iter(row)))
                for k in sorted(set(row) - set(cols)):
                    out.append((f"core/law/{name} {table} {n!r}", f"column `{k}` is not in the table's form: it holds "
                                                                  f"{', '.join(cols)} (`{key}.{table}`)"))
                for k in sorted(req - set(row)):
                    out.append((f"core/law/{name} {table} {n!r}", f"holds no `{k}`, which every row of `{table}` holds "
                                                                  f"(`{key}.{table}`)"))
    return out


class Law:
    """One law: the face, the verbs' rows, and the rows of whoever extends them (a garden's VOCAB.md)."""

    def __init__(self, face, rows, extensions=(), std=None):
        self.face, self.rows = face, rows
        self.std = std or standards.here()
        self.found = []                                    # (rule, where, message) the loading itself met
        F = face
        self.roles = [r['role'] for r in F.get('roles') or []]
        self.shapes = {s['shape'] for s in F.get('shapes') or []}
        self.beside = {b['key'] for b in F.get('beside_roles') or []}
        self.words = {w['word'] for w in F.get('words') or []}
        self.knowing = listed(F.get('knowing'))
        self.provenance = list(F.get('provenance') or [])
        self.crown = {c['crown']: c for c in F.get('crown') or []}
        self.natures = {n['nature']: n for n in F.get('natures') or []}
        self.lines = {ln['line']: ln for ln in F.get('lines') or []}
        self.conditions = {c['condition'] for c in F.get('conditions') or []}
        self.foundations = list(F.get('foundations') or [])
        self.figures = list(F.get('figures') or [])
        self.rules = [r['rule'] for r in F.get('rules') or []]
        self.version = str(F.get('version') or '')         # what a garden that runs this law pins: `core@<version>`
        self.manifest = {m['key']: m for m in F.get('manifest') or []}            # GARDEN.md's keys, each in its form
        self.manifest_forms = {f['form']: f for f in F.get('manifest_forms') or []}
        self.line_law = {}                                  # core/law/lines.yaml: the forms of a line, a reading's grammar
        self.measure_law = {}                               # core/law/measures.yaml: the forms of a measure (part 7)
        self.forms = {}                                     # the forms a `form` role names, by name
        self.added_forms = {}                               # core/law/forms.yaml: the forms part 12b adds, by name
        self.levels, self.kinds, self.namespaces, self.verbs, self.units = {}, {}, {}, {}, {}
        self.namespace_shape = {}                           # core/law/namespaces.yaml: its checks, where kept
        self.flows, self.flow_sources, self.standing, self.exclusive = [], [], [], []
        self.garden_flows = []                              # the rows of `flows` a garden added (VOCAB.md)
        self.methods, self.pass_metadata, self.flows_dropped = {}, {}, {}   # core/law/flows.yaml beside its rows
        self.garden_rows = []                               # (key, name, row) of each row a garden added (rule vacancy)
        self.families, self.tools = {}, {}                  # core/law/tools.yaml (v1 part 9)
        self.vacancy_reasons, self.vacancies, self.vacancies_dropped = [], [], []   # core/law/vacancies.yaml
        self.own = {}                                       # a garden's own systems, schemes and files (part 7)
        self.profiles, self.profile_tables = {}, {}         # core/law/profiles.yaml: each profile, its tables' rows
        self.added_by = {}                                  # (form, attribute) -> the profile that adds it to the form
        self.taken, self.taken_where = [], None             # the profiles a garden takes (VOCAB.md `profiles`)
        self.tables = {t: listed(F.get(t)) for t in FACE_TABLES}
        self.tables['layers'] = listed(F.get('layers'))
        self.standard_tables = set(listed(rows.get('standard_tables')))
        self.added = {}                                     # rows a garden added to a standard's table
        self.origin = {}                                    # name -> where it was declared
        for lv in F.get('levels') or []:
            self._put(self.levels, lv['level'], lv, 'core.yaml levels')
        for v in F.get('verbs') or []:
            self._put(self.verbs, v['verb'], v, 'core.yaml verbs')
        for t, vals in (rows.get('tables') or {}).items():
            self._put(self.tables, t, listed(vals), 'verbs.yaml tables')
        for v in rows.get('verbs') or []:
            self._put(self.verbs, v['verb'], v, 'verbs.yaml verbs')
        self.replaces = []
        for v in rows.get('verbs') or []:
            self.replaces += [(w, v['verb']) for w in listed(v.get('replaces'))]
        for k, ws in (rows.get('face_replaces') or {}).items():
            self.replaces += [(w, f"face {k}") for w in listed(ws)]
        for k, ws in (rows.get('roles_replace') or {}).items():
            self.replaces += [(w, f"role {k}") for w in listed(ws)]
        self.replaces += [(w, 'dropped') for w in listed(rows.get('dropped'))]
        for where, ext in extensions:
            self.extend(ext, where)
        self.incompatible = set()
        for f in self.figures:
            pos = f.get('positions') or {}
            pairs = list(pos.items())[:1] + list((f.get('contradictory') or {}).items())
            for a, b in pairs:                              # the contraries above, and both contradictory pairs
                self.incompatible |= {(a, b), (b, a)}

    @classmethod
    def load(cls, *extensions, std=None, root=None):
        """The law of the release at `root` (this one, if none is named), extended by each (where, rows) given: a garden's
        VOCAB.md front matter."""
        d = os.path.join(root, 'core', 'law') if root else LAW_DIR
        _dir = d if os.path.isfile(os.path.join(d, LINES)) else LAW_DIR
        rows = tuple((f"core/law/{n}", read.data(os.path.join(d, n))) for n in ROW_FILES)
        law = cls(read.data(os.path.join(d, 'core.yaml')), read.data(os.path.join(d, 'verbs.yaml')),
                  rows + tuple(extensions), std or (standards.here(root) if root else None))
        lines = os.path.join(d, LINES) if os.path.isfile(os.path.join(d, LINES)) else os.path.join(LAW_DIR, LINES)
        law.dir = _dir
        law.line_law = read.data(lines)
        measures = os.path.join(d, MEASURES) if os.path.isfile(os.path.join(d, MEASURES)) else os.path.join(LAW_DIR, MEASURES)
        law.measure_law = read.data(measures)
        law.forms = dict(law.line_law.get('forms') or {}, **(law.measure_law.get('forms') or {}))
        forms = os.path.join(d, FORMS) if os.path.isfile(os.path.join(d, FORMS)) else os.path.join(LAW_DIR, FORMS)
        law.added_forms = {str(k): f for k, f in ((read.data(forms) or {}).get('forms') or {}).items() if isinstance(f, dict)}
        law.forms.update(law.added_forms)
        values = os.path.join(d, VALUES) if os.path.isfile(os.path.join(d, VALUES)) else os.path.join(LAW_DIR, VALUES)
        law.values = {str(v['value']): v for v in listed((read.data(values) or {}).get('values'))
                      if isinstance(v, dict) and 'value' in v} if os.path.isfile(values) else {}
        for name, put in ((TOOLS, law._tools), (VACANCIES, law._vacancies), (PROFILES, law._profiles)):
            put(read.data(os.path.join(d, name) if os.path.isfile(os.path.join(d, name)) else os.path.join(LAW_DIR, name)))
        return law

    def _tools(self, data):
        self.families = {str(f['family']): f for f in listed(data.get('families')) if isinstance(f, dict)}
        self.tools = {str(t['tool']): t for t in listed(data.get('tools')) if isinstance(t, dict)}

    def _vacancies(self, data):
        self.vacancy_reasons = [str(r) for r in listed(data.get('reasons'))]
        self.vacancies = [v for v in listed(data.get('vacancies')) if isinstance(v, dict)]
        self.vacancies_dropped = [v for v in listed(data.get('dropped')) if isinstance(v, dict)]

    def _profiles(self, data):
        """The profiles (v1 part 11): each by its name; its tables' rows, their names a table the verbs may name; the
        forms it brings; the attributes it adds to a form of the core, which the form holds for every garden and rule
        `profile` grants only where the garden takes the profile; its vacancies beside the law's own."""
        self.profiles = {str(p['profile']): p for p in listed(data.get('profiles')) if isinstance(p, dict)}
        keys = {'lenses': 'lens', 'archetypes': 'archetype', 'planes': 'plane'}
        for t, key in keys.items():
            rows = [r for r in listed(data.get(t)) if isinstance(r, dict)]
            self.profile_tables[t] = rows
            self.tables[t] = [str(r.get(key)) for r in rows]
        for name, f in (data.get('forms') or {}).items():
            if isinstance(f, dict) and 'attrs' in f:
                self.forms[name] = f
        for name, p in self.profiles.items():
            for form, add in (p.get('adds') or {}).items():
                base = self.forms.get(form)
                if not isinstance(base, dict) or not isinstance(add, dict):
                    self.found.append(('law', f"core/law/profiles.yaml {name}", f"adds to `{form}`, no form of the core"))
                    continue
                self.forms[form] = dict(base, attrs=dict(base.get('attrs') or {}, **(add.get('attrs') or {})),
                                        cells=listed(base.get('cells')) + listed(add.get('cells')))
                for a in add.get('attrs') or {}:
                    self.added_by[(form, a)] = name
            self.vacancies += [dict(v, profile=name) for v in listed(p.get('vacancies')) if isinstance(v, dict)]
            self.vacancies_dropped += [dict(v, profile=name) for v in listed(p.get('dropped')) if isinstance(v, dict)]

    def home(self, verb):
        """The profile a verb is the profile's own, or None for the core's."""
        h = (self.verbs.get(verb) or {}).get('home')
        return h if h in self.profiles else None

    def form_attr(self, form, path):
        """The record of an attribute of a form (`walk.exit`: an attribute of what `walk` holds), or None."""
        rec = {'in': self.forms.get(form)} if form in self.forms else None
        for seg in [s for s in path.split('.') if s]:
            dom = (rec or {}).get('in')
            attrs = (dom.get('attrs') or dom.get('entries') or dom.get('map_of')) if isinstance(dom, dict) else None
            rec = attrs.get(seg) if isinstance(attrs, dict) else None
            if not isinstance(rec, dict):                  # an attribute nested a level down, under any attribute
                found = [self.form_attr(form, f"{a}.{seg}") for a in (attrs or {}) if isinstance(attrs, dict)] \
                    if path.count('.') == 0 and attrs else []
                found = [f for f in found if f]
                return found[0] if len(found) == 1 else None
        return rec

    def vacancy_place(self, at, position):
        """'' when the law has the place a vacancy is at and the position is one there, else why not. What `details`
        keeps under today's term is today's law's to judge."""
        kind, _, rest = str(at).partition(':')
        if kind == 'details':
            return ''
        if kind == 'figure':
            f = next((f for f in self.figures if f.get('figure') == rest), None)
            if f is None:
                return f"`{rest}` is no figure of the law: one of {', '.join(x.get('figure') for x in self.figures)}"
            pos = [p for kv in (f.get('positions') or {}).items() for p in kv]
            return '' if position in pos else f"{position!r} is no position of the figure {rest}: one of {', '.join(pos)}"
        if kind == 'table':
            rows = self.std.tables.get(rest) if self.std and rest in self.std.tables else None
            if rest == 'systems':
                return '' if position in self.systems else f"{position!r} is no system of the law"
            if rows is not None:
                names = [str(r[next(iter(r))]) for r in rows if isinstance(r, dict) and r]
                return '' if position in names else f"{position!r} is not a row of `{rest}`"
            return self.has(rest, position)
        if kind == 'form':
            form, _, path = rest.partition('.')
            if form not in self.forms:
                return f"`{form}` is no form of the law: one of {', '.join(sorted(self.forms))}"
            if not path:
                one = listed(self.forms[form].get('one_of'))
                return '' if position in one else f"{position!r} is none of the form {form}'s: {', '.join(one)}"
            rec = self.form_attr(form, path)
            if rec is None:
                return f"`{path}` is no attribute of the form {form}"
            dom = rec.get('in')
            return '' if isinstance(dom, list) and position in dom else \
                f"{position!r} is not a value of {form}.{path}: {dom!r}"
        return f"{at!r} is at no place the law has: `table:`, `figure:`, `form:` or `details:`"

    def _put(self, table, name, row, where):
        if name in table:
            self.found.append(('law', where, f"`{name}` is declared already ({self.origin.get((id(table), name))}): one "
                                             f"name, one row"))
            return
        table[name] = row
        self.origin[(id(table), name)] = where

    def extend(self, ext, where):
        """Add a garden's rows to this law: the keys of ROW_KEYS only, each row in its form."""
        for key, val in ext.items():
            if key in FLOW_LAW and where != GARDEN:
                for row in listed(val):
                    if isinstance(row, dict):
                        {'methods': self.methods, 'metadata': self.pass_metadata,
                         'dropped': self.flows_dropped}[key][str(row.get({'methods': 'method', 'metadata': 'key',
                                                                          'dropped': 'flow'}[key]))] = row
                if key == 'methods':
                    self.tables['methods'] = list(self.methods)
                continue
            if key == 'namespace_shape' and where != GARDEN:   # what a namespace may name beside its pattern
                self.namespace_shape = val if isinstance(val, dict) else {}
                continue
            if key == 'profiles' and where == GARDEN:     # THE PROFILES A GARDEN TAKES (v1 part 11): names, judged
                self.taken_where = where                  # against the profiles the law offers once it is loaded
                if not isinstance(val, list) or not all(isinstance(x, str) for x in val):
                    self.found.append(('law', f"{where} profiles", "`profiles` is a list of the profiles the garden "
                                                                   "takes, each by its name"))
                    continue
                self.taken = list(val)
                continue
            if key not in ROW_KEYS:
                if where == GARDEN:                       # A GARDEN'S VOCAB.md SAYS NOTHING THE LAW DOES NOT READ (v1
                    self.found.append(('law', f"{where} {key}", f"`{key}` is no key of a garden's VOCAB.md: it holds "
                                       f"rows of {', '.join(sorted(ROW_KEYS))}, and the profiles it takes"))
                continue                                  # part 13): a key in today's words was translated at adoption
            if key == 'flow_sources':
                for s in listed(val):
                    if s in self.flow_sources or s in self.tables['layers']:
                        self.found.append(('law', f"{where} flow_sources", f"`{s}` is a layer or a source already"))
                    else:
                        self.flow_sources.append(s)
                continue
            if key == 'tables':
                for t, vals in (val or {}).items() if isinstance(val, dict) else []:
                    if t == 'units':
                        self.found.append(('law', f"{where} tables.units", "a unit is a row of `units`, `{ unit, name, "
                                                                           "quantity }`: its UCUM code and its name"))
                    elif t in FACE_TABLES or t == 'layers':
                        self.found.append(('law', f"{where} tables.{t}", f"`{t}` is a table of the face: a row added "
                                                                         f"to it is a change to the core"))
                    elif t in self.standard_tables:
                        self.added.setdefault(t, []).extend(listed(vals))
                    elif t in self.tables:
                        self.tables[t] = self.tables[t] + listed(vals)
                    if where == GARDEN and (t in self.standard_tables or t in self.tables):
                        self.garden_rows += [('tables', f"{t}:{v}", {}) for v in listed(vals)]
                    else:
                        self.found.append(('law', f"{where} tables.{t}", f"`{t}` is no table of the law: a garden adds "
                                                                         f"rows to a table the verbs name"))
                continue
            if not isinstance(val, list):
                self.found.append(('law', f"{where} {key}", f"`{key}` is a list of rows"))
                continue
            for i, row in enumerate(val):
                at = f"{where} {key}[{i}]"
                if not isinstance(row, dict):
                    self.found.append(('law', at, f"a row of `{key}` is a mapping, not {row!r}"))
                    continue
                extra = set(row) - ROW_FIELDS[key]
                if extra:
                    self.found.append(('law', at, f"{', '.join(sorted(extra))}: no field of a row of `{key}`, whose "
                                                  f"fields are {', '.join(sorted(ROW_FIELDS[key]))}"))
                name_key = ROW_KEYS[key]
                if name_key and not row.get(name_key):
                    self.found.append(('law', at, f"a row of `{key}` names itself in `{name_key}`"))
                    continue
                if where == GARDEN and key in ('kinds', 'levels', 'namespaces', 'verbs', 'units'):
                    self.garden_rows.append((key, row[name_key], row))
                if key == 'flows':
                    self.flows.append(row)
                    if where == GARDEN:
                        self.garden_flows.append(row)
                elif key == 'standing':
                    self.standing.append(row)
                elif key == 'exclusive':
                    self.exclusive.append(row)
                elif key in ('systems', 'schemes', 'files'):    # read by the standards, beside theirs (part 7)
                    if key == 'systems' and str(row['system']) in self.std_systems():
                        self.found.append(('law', at, f"`{row['system']}` is a system of the standards already: a "
                                                      f"garden's own system takes a name of its own"))
                    if key == 'systems' and not self._compiles(row.get('pattern'), at):
                        continue                              # a position is never matched against a broken pattern
                    self.own.setdefault(key, []).append(row)
                else:
                    if key == 'namespaces' and not self._compiles(row.get('pattern'), at):
                        continue                          # a name is never matched against a broken pattern
                    self._put({'kinds': self.kinds, 'levels': self.levels, 'namespaces': self.namespaces,
                               'verbs': self.verbs, 'units': self.units}[key], row[name_key], row, at)

    def _compiles(self, pattern, at):
        """Whether a row's `pattern` (a garden's own system's, a namespace's) is one text that compiles; a refusal is
        recorded where it is not."""
        if pattern is None:
            return True
        try:
            if not isinstance(pattern, str):
                raise re.error(f"it is a {type(pattern).__name__}, not one text")
            re.compile(pattern)
            return True
        except re.error as e:
            self.found.append(('law', at, f"`pattern` does not compile as a regular expression ({e}): the row is "
                                          f"left out, and nothing is read by it"))
            return False

    # ------------------------------------------------------------------------------------------------ the flow law
    def decide(self, frm, to, through, as_=None, keeper=None, party=None):
        """Whether a pass `from` a layer `to` a layer `through` a method or a verb, carrying statements known there by the
        act `as_`, stands: (granted, grant, rows). A row holds it where its `from`, `to` and `through` hold the pass's, its
        `keeper`, where it names one, is the file's, and its `as`, where it names one, the pass's act — and is then nearer
        than a row that names only layers. Of the core's rows that hold it the nearest decide, and of two as near a
        refusal; `ratified` is granted only to the party a garden's own row of that name grants; a garden's own row that
        holds it and refuses it refuses it. `closed` where no row of the core holds it (core/law/flows.yaml)."""
        def near(r):
            if not (frm in listed(r.get('from')) and to in listed(r.get('to')) and through in listed(r.get('through'))
                    and (r.get('keeper') is None or r.get('keeper') == keeper)):
                return 0
            if r.get('as') is None:
                return 1
            return 2 if as_ in listed(r.get('as')) else 0
        mine = [r for r in self.garden_flows if near(r)]
        core = [(near(r), r) for r in self.flows if not any(r is g for g in self.garden_flows)]
        core = [(n, r) for n, r in core if n]
        refused = [str(r.get('flow', '')) for r in mine if r.get('grant') == 'refused']
        if not core:
            return False, 'closed', refused
        top = max(n for n, _ in core)
        rows = [r for n, r in core if n == top]
        said = {r.get('grant') for r in rows}
        grant = 'refused' if 'refused' in said or not said <= set(GRANTS) else 'ratified' if 'ratified' in said \
            else 'granted'
        names = [str(r.get('flow', '')) for r in rows]
        if refused:
            return False, grant, names + refused
        if grant == 'ratified':
            ok = [str(r.get('flow', '')) for r in mine if r.get('grant') == 'granted' and party is not None
                  and r.get('party') == party and str(r.get('flow', '')) in names]
            return bool(ok), grant, names + ok
        return grant == 'granted', grant, names

    # ------------------------------------------------------------------------------------------------ tables
    def std_systems(self):
        return self.std.systems if self.std else {}

    @property
    def systems(self):
        """The systems of position a garden of this law writes in: the standards', and its own (VOCAB.md `systems`), each
        row as written (part 7)."""
        own = self.own.get('systems') or []
        if not own:
            return self.std_systems()
        if getattr(self, '_systems', None) is None or self._systems[0] is not own:
            self._systems = (own, dict(self.std_systems(), **{str(r['system']): r for r in own}))
        return self._systems[1]

    def name_why(self, namespace, value):
        """'' when `value` is a name the namespace `namespace` gives — in its form (`pattern`), and holding to the check a
        validator makes (`checked_by`) — or when the namespace states no form; else why not. The rule `names` judges a
        name by this, and so does the held store before it seals one: one judge. A name of a namespace kept `held` is
        never echoed."""
        row = self.namespaces.get(namespace) or {}
        pat = row.get('pattern')
        if not pat:
            return ''
        shown = 'the name' if row.get('kept') == 'held' else repr(value)
        if not (isinstance(value, str) and re.fullmatch(pat, value)):
            return f"{shown} is not a name {namespace} gives: its form is `{pat}` — {row.get('meaning', '')}"
        chk = row.get('checked_by')
        if not chk:
            return ''
        import parse as dmparse
        try:
            ok = dmparse.FORM_CHECKS[chk](value)
        except dmparse.CheckUnavailable as e:
            return f"a name {namespace} gives is checked by {chk}, which cannot run here: {e}"
        return '' if ok else (f"{shown} is not a name {namespace} gives: it is in its form, and fails its check ({chk}) "
                              f"— {row.get('meaning', '')}")

    def table(self, name):
        """The rows of a table the law keeps (None for a standard's, which `has` asks)."""
        if name == 'levels':
            return list(self.levels)
        if name == 'layers':
            return self.tables['layers'] + self.flow_sources
        if name == 'verbs':
            return list(self.verbs) + self.tables.get('methods', [])
        if name == 'namespaces':
            return list(self.namespaces)
        return self.tables.get(name)

    def has(self, name, value):
        """'' when `value` is a row of the table `name`, else why it is not."""
        if not isinstance(value, str):
            return f"a row is named by one word, not a {type(value).__name__}"
        if name in self.standard_tables:
            if value in self.added.get(name, ()):
                return ''
            if name == 'protocols':
                return '' if value in self.std.protocols else f"{value!r} is no protocol of `net_protocols` (IANA)"
            if name == 'units':
                if value in self.units or value in self.std.currencies:
                    return ''
                named = next((u for u, r in self.units.items() if r.get('name') == value), None)
                if named:
                    return f"{value!r} is the English name of `{named}`: a unit is written in UCUM, its name the law's"
                return f"{value!r} is no unit of the law in UCUM (core/law/units.yaml) and no currency of ISO 4217"
            if name == 'knowledge':
                return self.std.code(value)
            if name == 'properties':
                if value in self.std.quantities:
                    return ''
                why = self.std.code(value)
                return '' if not why else f"{value!r} is no quantity of the law and no code of a scheme: {why}"
            return f"`{name}` is a standard's table this engine has no reader for"
        rows = self.table(name)
        if rows is None:
            return f"`{name}` is no table of the law"
        return '' if value in rows else f"{value!r} is not a row of `{name}`: one of {', '.join(map(str, rows[:24]))}" \
                                        + (' …' if len(rows) > 24 else '')

    # ------------------------------------------------------------------------------------------------ the order
    def level_line(self, level):
        row = self.levels.get(level)
        return row.get('line') if row else None

    def holds(self, line):
        return listed((self.lines.get(line) or {}).get('holds'))

    def below(self, level, ways=('made-of', 'possible-on')):
        """Every level `level` stands on, through any number of steps, by the ways given."""
        out, todo = set(), [level]
        while todo:
            for s in listed((self.levels.get(todo.pop()) or {}).get('stands')):
                if isinstance(s, dict) and s.get('as') in ways and s.get('at') not in out:
                    out.add(s.get('at'))
                    todo.append(s.get('at'))
        return out

    # ------------------------------------------------------------------------------------------------ proof
    def problems(self):
        """[(rule, where, message)]: the law's own consistency. Each one is an error: a law that does not hold together
        judges nothing."""
        out = list(self.found)

        def bad(where, msg):
            out.append(('law', where, msg))
        for name, f in self.added_forms.items():               # each form part 12b adds is held where it says (forms.yaml)
            for held in listed(f.get('held_by')):
                verb, _, q = str(held).partition('.')
                spec = ((self.verbs.get(verb) or {}).get('qualifiers') or {}).get(q)
                if not isinstance(spec, dict) or spec.get('form') != name:
                    bad(f"core/law/forms.yaml {name}", f"is held by `{held}`, and no verb's qualifier of that name holds it")
            if f.get('rule') not in self.rules:
                bad(f"core/law/forms.yaml {name}", f"names no rule of the law to judge it ({f.get('rule')!r})")
        for where, msg in columns_problems(getattr(self, 'dir', LAW_DIR), getattr(self.std, 'law_dir', None)):
            bad(where, msg)
        types = {str(t.get('type')) for t in (getattr(self, 'line_law', {}) or {}).get('types') or [] if isinstance(t, dict)}
        values = getattr(self, 'values', None) or {}
        for name, v in values.items():                     # the values tree: each a kind of another, up to `value`
            parent = v.get('is')
            if parent is not None and str(parent) not in values:
                bad(f"core/law/values.yaml {name}", f"is a kind of `{parent}`, which is no value of the tree")
            if v.get('written') is not None and str(v['written']) not in types:
                bad(f"core/law/values.yaml {name}", f"is written as `{v['written']}`, which is no type of lines.yaml")
            seen, at = {name}, parent
            while at is not None and str(at) in values:
                if str(at) in seen:
                    bad(f"core/law/values.yaml {name}", "is a kind of itself, through the values it is a kind of")
                    break
                seen.add(str(at))
                at = values[str(at)].get('is')
        if values and [n for n, v in values.items() if v.get('is') is None] != ['value']:
            bad('core/law/values.yaml', "the tree has one root, `value`, a kind of nothing")
        import parse as dmparse                         # the one reader of a check a row names
        shape = getattr(self, 'namespace_shape', None) or {}
        for name, row in (self.namespaces or {}).items():  # a namespace's check is one a validator makes, and is named
            chk, kept = row.get('checked_by'), row.get('kept')
            if chk is not None and (str(chk) not in listed(shape.get('checked_by')) or str(chk) not in dmparse.FORM_CHECKS):
                bad(f"namespaces {name}", f"is checked by `{chk}`, which is no check of `namespace_shape.checked_by` "
                                          f"({', '.join(listed(shape.get('checked_by')))}) the reader has")
            if kept is not None and str(kept) not in listed(shape.get('kept')):
                bad(f"namespaces {name}", f"is kept `{kept}`, which is nowhere `namespace_shape.kept` names "
                                          f"({', '.join(listed(shape.get('kept')))})")
        for name, row in (self.systems or {}).items():         # a system's own example is in its own form (16.0)
            pat, ex = row.get('pattern'), row.get('example') if isinstance(row, dict) else None
            if isinstance(pat, str) and isinstance(ex, str):
                try:
                    if not re.match(pat, ex, re.ASCII) or re.match(pat, ex, re.ASCII).end() != len(ex):
                        bad(f"systems {name}", f"its own `example` {ex!r} is not in the form its `pattern` gives")
                except re.error:
                    pass                                        # a pattern that does not compile is refused where it is read
        if len(self.roles) != 7:
            bad('core.yaml roles', f"the core has seven roles, and this law {len(self.roles)}")
        known_rules = ['form', 'valency', 'knowing', 'placeholder', 'order', 'life', 'necessity', 'squares', 'bearer',
                       'frame', 'names', 'layers', 'ratify', 'consent', 'harm', 'room', 'vacancy', 'kept', 'line', 'measured',
                       'profile']
        for x in self.exclusive:
            if x.get('verb') not in self.verbs:
                bad('exclusive', f"`{x.get('verb')}` is no verb of the law: what is exclusive is a verb's `at`")
        if not re.fullmatch(r'[0-9]+\.[0-9]+', self.version):
            bad('core.yaml version', f"`{self.version}`: the law's version is `<major>.<minor>`, which a garden pins")
        for k, m in self.manifest.items():
            if m.get('form') not in MANIFEST_FORMS + tuple(self.manifest_forms):
                bad(f"core.yaml manifest {k}", f"`{m.get('form')}` is no form of the manifest's")
        for f, m in self.manifest_forms.items():
            try:
                re.compile(m.get('pattern') or '')
            except re.error as e:
                bad(f"core.yaml manifest_forms {f}", f"its pattern does not compile: {e}")
        if not {'garden', 'extends', 'gardener', 'zone'} <= set(self.manifest):
            bad('core.yaml manifest', "GARDEN.md names its garden, the law it runs, its gardener and its zone")
        if self.rules != known_rules:
            bad('core.yaml rules', f"the engine applies {', '.join(known_rules)}; the law lists {', '.join(self.rules)}")
        for name, v in self.verbs.items():
            self._verb_problems(name, v, bad)
            if self.profiles and v.get('home') not in (None, 'core') and v.get('home') not in self.profiles:
                bad(f"verb {name}", f"its home `{v.get('home')}` is the core or a profile of the law "
                                    f"({', '.join(self.profiles)})")
        for p in self.taken:
            if p not in self.profiles:
                bad(f"{self.taken_where} profiles", f"`{p}` is no profile the law offers: one of "
                                                    f"{', '.join(self.profiles)}")
        if len(set(self.taken)) != len(self.taken):
            bad(f"{self.taken_where} profiles", "a profile is taken once")
        for f in self.figures:
            names = set((f.get('positions') or {}).keys()) | set((f.get('positions') or {}).values())
            ops = {n for n, v in self.verbs.items() if v.get('figure') == f.get('figure')}
            if names != ops or len(names) != 4:
                bad(f"figure {f.get('figure')}", f"its four positions {sorted(names)} are its four operators {sorted(ops)}")
        for k in self.knowing:
            v = self.verbs.get(k)
            if not v:
                bad('core.yaml knowing', f"`{k}` is no verb")
            elif 'statement' not in shapes_of((v.get('roles') or {}).get('of')) or 'at' not in listed(v.get('required')):
                bad(f"verb {k}", "a knowing act takes statements as its `of`, and requires its `at`")
        for p in self.provenance:
            if p.get('act') not in self.knowing or p.get('nature') not in self.natures:
                bad('core.yaml provenance', f"{p!r}: an act of knowing, by a being of a nature")
        frames = {}
        for lv, row in self.levels.items():
            if row.get('frame_of'):
                frames[row['frame_of']] = lv
        for n, row in self.natures.items():
            fr = frames.get(n)
            if fr is None or row.get('frame') != fr or self.level_line(fr) != 'frame':
                bad(f"nature {n}", f"each nature takes its place in one frame, a level of the line `frame`; {n} names "
                                   f"{row.get('frame')!r}")
        if self.holds('frame'):
            bad('line frame', "the frame holds no being")
        for ln, row in self.lines.items():
            for n in self.holds(ln):
                if n not in self.natures:
                    bad(f"line {ln}", f"holds {n!r}, which is no nature")
        for lv, row in self.levels.items():
            if row.get('line') not in self.lines:
                bad(f"level {lv}", f"is on {row.get('line')!r}, which is no line")
            for s in listed(row.get('stands')):
                if not isinstance(s, dict) or s.get('at') not in self.levels or s.get('as') not in self.tables['ways'] \
                        or (s.get('while') is not None and s.get('while') not in self.conditions):
                    bad(f"level {lv}", f"stands on {s!r}: a level that exists, by a way of `ways`, while a condition")
            if lv in self.below(lv):
                bad(f"level {lv}", "stands on itself through the levels beneath it: the ladder is never a circle")
        for k, row in self.kinds.items():
            if row.get('nature') not in self.natures:
                bad(f"kind {k}", f"its nature {row.get('nature')!r} is none of {', '.join(self.natures)}")
                continue
            if row.get('level') is not None:
                ln = self.level_line(row['level'])
                if ln is None:
                    bad(f"kind {k}", f"its level {row['level']!r} is no level of the law")
                elif row['nature'] not in self.holds(ln) or (row.get('line') and row['line'] != ln):
                    bad(f"kind {k}", f"a kind's level is on a line that holds its nature: {row['level']} is on {ln}, "
                                     f"which holds {', '.join(self.holds(ln)) or 'no being'}, and {k} is a {row['nature']}")
            if row.get('rung') is not None and (self.level_line(row['rung']) is None or self.holds(self.level_line(row['rung']))):
                bad(f"kind {k}", f"its rung {row['rung']!r} is a level on a line that holds no being (reason)")
        for ns, row in self.namespaces.items():
            if row.get('once') not in (None, TRUE, 'false'):
                bad(f"namespace {ns}", "`once` is true or false")
        layers = self.table('layers')
        for i, f in enumerate(self.flows):
            for side in ('from', 'to'):
                for x in listed(f.get(side)):
                    if x not in layers:
                        bad(f"flow {f.get('flow', i)}", f"{side} {x!r}: not a layer or a source of the flow law")
            for x in listed(f.get('through')):
                if x not in self.table('verbs'):
                    bad(f"flow {f.get('flow', i)}", f"through {x!r}: not a verb or a method")
            name = f"flow {f.get('flow', i)}"
            if f.get('grant') not in GRANTS:
                bad(name, "its grant is `granted`, `refused` or `ratified`")
            for x in listed(f.get('as')):
                if x not in self.knowing:
                    bad(name, f"as {x!r}: what a pass carries into a layer is known there by a knowing act "
                              f"({', '.join(self.knowing)})")
            if f.get('keeper') not in (None, 'release'):
                bad(name, "`keeper` is `release`: the row holds only for a file the release keeps")
            if not any(f is g for g in self.garden_flows):
                if 'party' in f or 'basis' in f:
                    bad(name, "a row of the core grants no party: a garden grants one, by a row of its own")
                continue
            if f.get('grant') == 'refused':
                continue
            ratified = [r for r in self.flows if r.get('flow') == f.get('flow') and r.get('grant') == 'ratified'
                        and not any(r is g for g in self.garden_flows)]
            if f.get('grant') != 'granted' or not ratified or not f.get('party') or not f.get('basis'):
                bad(name, "a garden's own row refuses, or grants the party it names (`party`, with the `basis` it "
                          "grants on) a pass the core's row of the same name says is `ratified`: a garden never "
                          "unguards the core")
        for i, s in enumerate(self.standing):
            if s.get('layer') not in layers:
                bad(f"standing {i}", f"{s.get('layer')!r} is no layer")
            for h in listed(s.get('holds')):
                if not isinstance(h, str) or not h:
                    bad(f"standing {i}", f"{h!r}: a pattern of a path")
        # where each dimension and kind stands, and what it holds for (2026-10-10)
        dim_rows = {str(d.get('dimension')): d for d in (self.std.tables.get('dimensions') or []) if isinstance(d, dict)} \
            if self.std else {}

        def holds_ok(h):
            if h is None or (isinstance(h, str) and h in self.natures):
                return True
            return isinstance(h, dict) and h.get('level') in self.levels and set(h) <= {'level', 'while'} \
                and (h.get('while') is None or h.get('while') in self.conditions)
        for kind_of_row, rows in (('dimension', dim_rows), ('quantity', self.std.quantities if self.std else {})):
            for name, row in rows.items():
                for s in listed(row.get('stands')):
                    if not isinstance(s, dict) or (s.get('at') not in self.levels and s.get('at') not in dim_rows) \
                            or s.get('as') not in self.tables['ways'] \
                            or (s.get('while') is not None and s.get('while') not in self.conditions):
                        bad(f"{kind_of_row} {name}", f"stands on {s!r}: a level or a dimension that exists, by a way of "
                                                     f"`ways`, while a condition")
                if not holds_ok(row.get('holds_for')):
                    bad(f"{kind_of_row} {name}", f"holds for {row.get('holds_for')!r}: a nature, or {{ level, while? }}")
                if kind_of_row == 'quantity':
                    for d in (row.get('of') or {}):
                        if str(d) not in dim_rows:
                            bad(f"quantity {name}", f"is of {d!r}, which is no dimension of the law")
        for name in dim_rows:                               # the dimensions stand on one another without a circle
            seen, todo = set(), [name]
            while todo:
                for s in listed(dim_rows.get(todo.pop(), {}).get('stands')):
                    at = s.get('at') if isinstance(s, dict) else None
                    if at in dim_rows and at not in seen:
                        seen.add(at)
                        todo.append(at)
            if name in seen:
                bad(f"dimension {name}", "stands on itself through the dimensions beneath it: never a circle")
        names = {}
        for u, row in self.units.items():
            names.setdefault(row.get('name'), []).append(u)
            if row.get('quantity') not in self.std.quantities:
                bad(f"unit {u}", f"its quantity {row.get('quantity')!r} is no quantity of the law")
            if row.get('per') is not None and (not self.std or row['per'] not in self.std.currencies
                                               or row.get('quantity') != 'money' or not row.get('factor')):
                bad(f"unit {u}", "`per` names the currency a unit of money is counted against, with its factor")
            if row.get('ucum') not in (None, 'false') or (row.get('ucum') == 'false' and not row.get('why')):
                bad(f"unit {u}", "a code UCUM does not write says so, `ucum: false`, and why")
        for n, us in names.items():
            if len(us) > 1:
                bad('units', f"the name {n!r} is attached to {', '.join(us)}: one name, one unit")
        seen = {}
        for w, who in self.replaces:
            seen.setdefault(w, []).append(who)
        for w, whos in seen.items():
            if len(whos) > 1:
                bad('replaces', f"`{w}` is replaced by {' and by '.join(whos)}: a word of today's law goes one way")
        for t, vals in self.tables.items():
            if len(set(map(str, vals))) != len(vals):
                bad(f"table {t}", "a row is written twice")
        for t, row in self.tools.items():                  # the tools, each in a family (v1 part 9)
            if row.get('family') not in self.families:
                bad(f"tool {t}", f"its family {row.get('family')!r} is none of {', '.join(self.families)}")
        for i, v in enumerate(self.vacancies):             # a vacancy is at a place the law has, for a reason it gives
            if v.get('reason') not in self.vacancy_reasons:
                bad(f"vacancy {i}", f"its reason {v.get('reason')!r} is none of {', '.join(self.vacancy_reasons)}")
            why = self.vacancy_place(v.get('at'), str(v.get('position')))
            if why:
                bad(f"vacancy {i} ({v.get('at')} {v.get('position')})", why)
        return out

    def _verb_problems(self, name, v, bad):
        where = f"verb {name}"
        roles = v.get('roles') or {}
        quals = v.get('qualifiers') or {}
        if not isinstance(roles, dict) or not isinstance(quals, dict):
            bad(where, "its roles and qualifiers are mappings of name to spec")
            return
        for r in roles:
            if r not in self.roles:
                bad(where, f"`{r}` is none of the seven roles")
        for q in quals:
            if q in self.roles or q in self.beside:
                bad(where, f"the qualifier `{q}` has the name of a role or of a key beside them")
        for r, spec in list(roles.items()) + list(quals.items()):
            if not isinstance(spec, dict):
                bad(where, f"`{r}`: a spec is a mapping")
                continue
            if set(spec) - SPEC_KEYS:
                bad(where, f"`{r}`: {', '.join(sorted(set(spec) - SPEC_KEYS))} is no key of a spec")
            for s in shapes_of(spec):
                if s not in self.shapes:
                    bad(where, f"`{r}`: no shape {s!r}")
            if 'form' in shapes_of(spec) and self.forms and spec.get('form') not in self.forms:
                bad(where, f"`{r}`: a form names one of the forms of a line ({', '.join(sorted(self.forms))}), not "
                           f"{spec.get('form')!r}")
            if 'row' in shapes_of(spec):
                t = spec.get('table')
                if not t:
                    bad(where, f"`{r}`: a row names the table it is a row of")
                elif t not in self.standard_tables and self.table(t) is None:
                    bad(where, f"`{r}`: no table {t!r}")
            for n in listed(spec.get('nature')):
                if n not in self.natures:
                    bad(where, f"`{r}`: no nature {n!r}")
            if spec.get('rung') is not None and spec['rung'] not in self.levels:
                bad(where, f"`{r}`: no level {spec['rung']!r}")
            for flag in ('many', 'keyed'):
                if spec.get(flag) not in (None, TRUE):
                    bad(where, f"`{r}`: `{flag}` is written `true`, or not at all")
        for r in listed(v.get('required')):
            if r not in roles and r not in quals:
                bad(where, f"requires `{r}`, which it does not take")
        ch = v.get('choice')
        if ch is not None:
            if not isinstance(ch, dict) or set(ch) != {'one_of'} or any(r not in roles and r not in quals
                                                                       for r in listed(ch['one_of'])):
                bad(where, "a choice is `{ one_of: [roles or qualifiers it takes] }`")
        d = v.get('default')
        if d is not None:
            if not isinstance(d, dict) or not isinstance(d.get('fill'), dict) or set(d) - {'says', 'when', 'fill', 'alone'}:
                bad(where, "a default is `{ says, when?, fill: { <role>: <how> }, alone? }`")
                return
            for k in (d.get('when') or {}):
                if k not in roles:
                    bad(where, f"its default holds when `{k}`, which it does not take")
            for r, how in d['fill'].items():
                if r not in roles:
                    bad(where, f"its default fills `{r}`, which it does not take")
                ok = isinstance(how, dict) and how.get('take') and (
                    (set(how) == {'verb', 'match', 'take'} and how['verb'] in self.verbs and isinstance(how['match'], dict))
                    or (set(how) == {'the', 'take'} and how['the'] in roles))
                if not ok:
                    bad(where, f"its default fills `{r}` by {how!r}: `{{ verb, match: {{ <theirs>: <mine> }}, take }}` "
                               f"or `{{ the: <role>, take }}`")
        if v.get('figure') is not None and v['figure'] not in {f.get('figure') for f in self.figures}:
            bad(where, f"no figure {v['figure']!r}")
