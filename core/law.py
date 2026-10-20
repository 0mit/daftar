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
from decimal import Decimal

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
            'systems': 'system', 'schemes': 'scheme', 'files': 'registry', 'crosswalks': 'crosswalk',
            'groupings': 'grouping', 'risks': 'risk'}
NAME_IN = re.compile(r'^name_[a-z]{2,3}(?:-[A-Za-z0-9]{1,8})*$')    # a code's name in a language: `name_fa`, `name_pt-BR`
ROW_FIELDS = {
    'kinds': {'kind', 'nature', 'line', 'level', 'rung', 'meaning', 'vacant'},
    'levels': {'level', 'line', 'stands', 'meaning', 'frame_of', 'vacant'},
    'namespaces': {'namespace', 'once', 'pattern', 'checked_by', 'kept', 'meaning', 'vacant'},
    'flows': {'flow', 'from', 'to', 'through', 'as', 'grant', 'keeper', 'party', 'basis', 'why'},
    'standing': {'layer', 'holds', 'meaning'},
    'verbs': {'verb', 'meaning', 'roles', 'qualifiers', 'required', 'choice', 'default', 'replaces', 'home', 'figure',
              'vacant'},
    'units': {'unit', 'name', 'quantity', 'factor', 'per', 'ucum', 'why', 'vacant'},
    'systems': {'system', 'dimension', 'covers', 'pattern', 'form_note', 'example', 'levels', 'restrictions', 'neighbours',
                'complement', 'calendar', 'reckoning', 'day_begins', 'datum', 'boundaries_in', 'cells_in', 'checked_by',
                'crosswalk', 'establishes', 'resolves_through', 'same_ground_as', 'transport', 'unit_symbols', 'within',
                'overlay', 'meaning', 'why', 'vacant'},
    'schemes': {'scheme', 'classifies', 'publisher', 'url', 'levels', 'neighbours', 'sources', 'holding', 'licence',
                'release', 'sensitive', 'code_pattern', 'relations', 'labels', 'crosswalk', 'same_ground_as', 'within',
                'file', 'key', 'format', 'meaning', 'units', 'form', 'vacant'},
    'files': {'registry', 'file', 'key', 'format'},
    'groupings': {'grouping', 'home', 'meaning', 'steps', 'line', 'inputs', 'weighs', 'vacant'},
    'risks': {'risk', 'meaning', 'resolved_by', 'vacant'},
    'exclusive': {'verb', 'why'},
}
LINES = 'lines.yaml'                                       # the forms of a line and a reading's grammar (v1 part 6)
TOOLS, VACANCIES = 'tools.yaml', 'vacancies.yaml'          # the tools by their verbs; what nothing takes up yet (part 9)
PROFILES = 'profiles.yaml'                                 # what a garden takes up beside the core (v1 part 11)
FORMS = 'forms.yaml'                                       # the forms part 12b adds, written by hand: a grant's cover,
                                                           # a settlement, a weighing, a channel
VALUES = 'values.yaml'                                     # what a value is to a reader: the tree the widgets answer to
CROSSWALKS = 'crosswalks.yaml'                             # a foreign system's records read from statements (P5.3)
FORMATS_LAW = 'formats.yaml'                               # the formats statements come in and go out in, the readers
                                                           # of a model's records, the conversions of a field (2.12)
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
            (VALUES, 'columns'), (PROFILES, 'forms'),     # the profiles' tables (lenses, archetypes, orientations…) too
            (FORMATS_LAW, 'columns'))                     # the formats, the readers, the conversions


def _columned(law_dir, std_dir):
    """[(name, key, path)] of each file whose tables have forms, where it is read from: the standards' from `std_dir`."""
    return [(name, key, os.path.join(std_dir if std_dir and key == 'forms' and name != PROFILES else law_dir, name))
            for name, key in COLUMNED]          # a profile is the law's own


def columns_problems(law_dir, std_dir=None):
    """[(where, message)]: each table of rows in the files whose tables have forms, held to its form — ONCE PER LAW
    VERSION (2026-10-14): what it found is kept in the clone's git directory under the SHA-256 of those files and of the
    code that judges them, and read back while both are unchanged. It re-read ten of the law's files at every gate, a
    tenth of a small garden's gate; a law that changes, or a judge that does, is judged again."""
    import hashlib
    import json
    files = _columned(law_dir, std_dir)
    h = hashlib.sha256()
    for code in (__file__, read.__file__):
        with open(code, 'rb') as fh:
            h.update(fh.read())
    for name, key, path in files:
        h.update(f"\0{name}\0{key}\0".encode('utf-8'))
        if os.path.isfile(path):
            with open(path, 'rb') as fh:
                h.update(fh.read())
    keep = _law_kept(h.hexdigest())
    if keep is not None and os.path.isfile(keep):
        try:
            with open(keep, encoding='utf-8') as fh:
                return [tuple(x) for x in json.load(fh)]
        except (OSError, ValueError):
            pass
    out = _columns_problems(files)
    if keep is not None:
        try:
            os.makedirs(os.path.dirname(keep), exist_ok=True)
            tmp = f"{keep}.{os.getpid()}"
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump(out, fh, ensure_ascii=False)
            os.replace(tmp, keep)
        except OSError:
            pass
    return out


def _law_kept(digest):
    """Where the self-check of the law of that digest is kept: `<git dir>/daftar/law-checked/<digest>.json` of the
    garden's clone the gate runs in (where every worktree of it reads it), or None outside a garden's clone — a release's
    own tree, a copy with no history: there nothing is kept, and the law is judged each time."""
    import subprocess
    try:
        r = subprocess.run(['git', 'rev-parse', '--show-toplevel', '--git-common-dir'], capture_output=True, text=True)
    except OSError:
        return None
    lines = r.stdout.strip().split('\n')
    if r.returncode != 0 or len(lines) != 2 or not os.path.isfile(os.path.join(lines[0], 'GARDEN.md')):
        return None
    return os.path.join(os.path.abspath(lines[1]), 'daftar', 'law-checked', f"{digest}.json")


def _columns_problems(files):
    out = []
    for name, key, path in files:
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
        self.store_shape = {}                               # core/law/layers.yaml: a store's pointer, forms, relation
        self.flows, self.flow_sources, self.standing, self.exclusive = [], [], [], []
        self.garden_flows = []                              # the rows of `flows` a garden added (VOCAB.md)
        self.methods, self.pass_metadata, self.flows_dropped = {}, {}, {}   # core/law/flows.yaml beside its rows
        self.garden_rows = []                               # (key, name, row) of each row a garden added (rule vacancy)
        self.garden_crosswalks = []                         # (where, row) of each crosswalk a garden's VOCAB.md adds
        self.formats, self.readers, self.conversions = {}, {}, {}   # core/law/formats.yaml (2.12)
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
        cw = os.path.join(d, CROSSWALKS) if os.path.isfile(os.path.join(d, CROSSWALKS)) else os.path.join(LAW_DIR, CROSSWALKS)
        cw_law = (read.data(cw) or {}) if os.path.isfile(cw) else {}
        law.crosswalk_forms = cw_law.get('forms') or {}
        law.crosswalks = {str(r['crosswalk']): r for r in listed(cw_law.get('crosswalks'))
                          if isinstance(r, dict) and 'crosswalk' in r}
        law.own_crosswalks()
        fm = os.path.join(d, FORMATS_LAW) if os.path.isfile(os.path.join(d, FORMATS_LAW)) else os.path.join(LAW_DIR, FORMATS_LAW)
        law._formats((read.data(fm) or {}) if os.path.isfile(fm) else {})
        for name, put in ((TOOLS, law._tools), (VACANCIES, law._vacancies), (PROFILES, law._profiles)):
            put(read.data(os.path.join(d, name) if os.path.isfile(os.path.join(d, name)) else os.path.join(LAW_DIR, name)))
        return law

    def own_crosswalks(self):
        """A GARDEN'S OWN CROSSWALKS (its VOCAB.md `crosswalks`) beside the standard's, read by the one reader
        (core/crosswalk.py) as the standard's are, and held to their form (crosswalk_problems). One name, one row: never
        a name the standard has, nor one of its own twice. One model, one row, a system and series: the reader keys a
        series' rows by their model, so a second row of one model would stand in for the first unseen."""
        std = set(self.crosswalks)
        for at, row in self.garden_crosswalks:
            name = str(row['crosswalk'])
            if name in self.crosswalks:
                self.found.append(('law', at, f"`{name}` is a crosswalk of the standard already: a garden's own takes "
                                              f"a name of its own" if name in std else
                                              f"`{name}` is given twice: one name, one row"))
                continue
            key = tuple(str(row.get(k)) for k in ('system', 'series', 'model'))
            by = next((n for n, r in self.crosswalks.items()
                       if tuple(str(r.get(k)) for k in ('system', 'series', 'model')) == key), None)
            if by is not None:
                self.found.append(('law', at, f"`{name}` crosses {key[2]} of {key[0]} {key[1]}, which {by} crosses "
                                              f"already: one model, one row, a system and series"))
                continue
            self.crosswalks[name] = row
            self.garden_rows.append(('crosswalks', name, row))

    def _formats(self, data):
        """core/law/formats.yaml: each format, reader and conversion by its name, and each a table a vacancy or a role may
        name (`table:formats`)."""
        for table, key, into in (('formats', 'format', self.formats), ('readers', 'reader', self.readers),
                                 ('conversions', 'conversion', self.conversions)):
            for r in listed(data.get(table)):
                if isinstance(r, dict) and r.get(key) is not None:
                    into[str(r[key])] = r
            self.tables[table] = list(into)

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
        keys = {'lenses': 'lens', 'archetypes': 'archetype', 'planes': 'plane', 'orientations': 'order',
                'elements': 'element', 'account_roles': 'role', 'date_styles': 'style', 'currency_displays': 'display',
                'aspects': 'aspect', 'keeping_properties': 'property', 'risks': 'risk', 'layout_slots': 'slot'}
        for t, key in keys.items():
            rows = [r for r in listed(data.get(t)) if isinstance(r, dict)]
            if t == 'risks':                          # the law's own, then a garden's (VOCAB.md `risks`), read first
                rows += [{k: v for k, v in r.items() if k != 'at'} for r in listed((self.own or {}).get('risks'))]
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
            if key == 'store_shape' and where != GARDEN:       # a store: its pointer, its forms, a row (MODEL.md)
                self.store_shape = val if isinstance(val, dict) else {}
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
                if key == 'crosswalks':                   # held to the core's form with the standard's rows, and set
                    if not row.get('crosswalk'):          # beside them once they are read (load, own_crosswalks)
                        self.found.append(('law', at, "a row of `crosswalks` names itself in `crosswalk`"))
                    else:
                        self.garden_crosswalks.append((at, row))
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
                elif key == 'groupings':                  # a garden's own standard readings, beside the law's: a
                    self.own.setdefault(key, []).append(dict(row, at=at))   # reading, not a word (rule vacancy)
                elif key == 'risks':                      # a garden's own risks: rows of the storage profile's table
                    self.own.setdefault(key, []).append(dict(row, at=at))
                    self.profile_tables.setdefault(key, []).append(row)
                    self.tables[key] = list(self.tables.get(key) or []) + [str(row['risk'])]
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

    @property
    def slots(self):
        """The slots of a name's template (core/law/lines.yaml `slots`), by name."""
        return {str(r['slot']): r for r in listed(getattr(self, 'line_law', {}).get('slots'))
                if isinstance(r, dict) and 'slot' in r}

    @property
    def groupings(self):
        """The groupings: the law's (core/law/lines.yaml `groupings`) and the garden's own (VOCAB.md `groupings`), by
        name, the garden's never one of the law's names."""
        out = {str(r['grouping']): r for r in listed(getattr(self, 'line_law', {}).get('groupings'))
               if isinstance(r, dict) and 'grouping' in r}
        for r in listed(self.own.get('groupings')):
            if isinstance(r, dict) and r.get('grouping') and str(r['grouping']) not in out:
                out[str(r['grouping'])] = {k: v for k, v in r.items() if k != 'at'}
        return out

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

    def given_twice(self, dim_rows):
        """ONE PATH, ONE STATEMENT: [(where, message)] for a stand that another of the row's stands already gives through
        the ladder — `made-of` through `made-of` alone, `possible-on` through either way, its condition on the path — and
        for a bearer another row already gives: a dimension's that copies what it stands on (`possible-on` lets the lower's
        categories stop; a copy says they recur), or that a foundation gives; a quantity's that one of its dimensions
        already gives; and a quantity's stand on the step its own bearer is made of."""
        out, quantities = [], (self.std.quantities if self.std else {})
        rows = {('level', n): r for n, r in self.levels.items()}
        rows.update({('dimension', n): r for n, r in dim_rows.items()})
        rows.update({('quantity', n): r for n, r in quantities.items()})

        def node(at):
            return ('dimension', at) if at in dim_rows else ('level', at)

        def stands(key):
            return [s for s in listed((rows.get(key) or {}).get('stands')) if isinstance(s, dict)]

        for key in rows:
            mine = stands(key)
            for e in mine:
                ways = ('made-of',) if e.get('as') == 'made-of' else ('made-of', 'possible-on')
                goal, cond = node(e.get('at')), e.get('while')
                todo = [(node(o.get('at')), cond is None or o.get('while') == cond) for o in mine
                        if o is not e and o.get('as') in ways]
                seen = set(todo)
                while todo:
                    n, met = todo.pop()
                    if n == goal and met:
                        out.append((f"{key[0]} {key[1]}", f"stands on {e.get('at')} as {e.get('as')}"
                                    f"{' while ' + cond if cond else ''}, which its other stands already give: one path, "
                                    f"one statement"))
                        break
                    for s in stands(n):
                        nxt = (node(s.get('at')), met or s.get('while') == cond)
                        if s.get('as') in ways and nxt not in seen:
                            seen.add(nxt)
                            todo.append(nxt)
        found = {str(f['property']): f for f in self.foundations if f.get('property')}

        def bearer_of(d):
            row = dim_rows.get(d) or {}
            return row.get('holds_for') if row.get('holds_for') is not None else (found.get(d) or {}).get('holds_for')

        def within(a, b):                                  # every being `a` lets bear is one `b` lets
            if a == b:
                return True
            if isinstance(a, dict) and isinstance(b, str):
                return b in self.holds(self.level_line(a.get('level')))
            if isinstance(a, dict) and isinstance(b, dict):
                return b.get('level') in self.below(a.get('level'), ways=('made-of',)) or \
                    (b.get('level') == a.get('level') and b.get('while') in (None, a.get('while')))
            return False
        for d, row in dim_rows.items():
            h = row.get('holds_for')
            if h is not None and d in found:
                out.append((f"dimension {d}", f"holds for {h!r}, which the foundation {found[d].get('foundation')} "
                                              f"already gives: one path, one statement"))
            for s in listed(row.get('stands')):
                at = s.get('at') if isinstance(s, dict) else None
                if h is not None and at in dim_rows and s.get('as') == 'possible-on' and bearer_of(at) == h:
                    out.append((f"dimension {d}", f"holds for {h!r}, a copy of what {at} holds for: standing on it "
                                                  f"possible-on, its bearer is its own — what it carries, never its "
                                                  f"carrier"))
        for q, row in quantities.items():
            h = row.get('holds_for')
            for d, power in (row.get('of') or {}).items():
                if h is not None and str(power) not in ('0', '') and str(d) in dim_rows and within(bearer_of(str(d)), h):
                    out.append((f"quantity {q}", f"holds for {h!r}, which its dimension {d} already gives: one path, "
                                                 f"one statement"))
            for s in listed(row.get('stands')):
                if isinstance(h, dict) and isinstance(s, dict) and s.get('as') == 'possible-on' and s.get('at') in \
                        {h.get('level')} | self.below(h.get('level'), ways=('made-of',)):
                    out.append((f"quantity {q}", f"stands on {s.get('at')}, which its bearer ({h!r}) is made of "
                                                 f"already: one path, one statement"))
        return out

    def crosswalk_problems(self):
        """[(where, message)]: each crosswalk held to its form — a kind of the law, paths of the law's verbs and roles,
        models that rows of its own system and series cross, `join` with `along`, `inverse` and `chain` with a model."""
        out, rows = [], getattr(self, 'crosswalks', {}) or {}
        forms = getattr(self, 'crosswalk_forms', {}) or {}
        row_keys, field_keys = set(forms.get('crosswalk') or {}), set(forms.get('field') or {})
        st_keys = set(forms.get('statements') or {})

        def verb_roles(verb):
            v = self.verbs.get(verb) or {}
            return set(v.get('roles') or {}) | set(v.get('qualifiers') or {})

        def statements_ok(where, spec, naming):
            """A `statements` form (core/inforce.py `matching`): its keys, a verb of the law, filters and the role that
            names the bean of that verb, an ending verb of the law. `naming` where the form must say which role names
            the bean it is read for (a select's, a field's), and never where its statements are the records."""
            if not isinstance(spec, dict):
                out.append((where, "`statements` is a mapping: { verb, with, naming, in_force_on, ended_by, standing }"))
                return None
            for k in spec:
                if st_keys and k not in st_keys:
                    out.append((where, f"`{k}` is no key of `statements` ({', '.join(sorted(st_keys))})"))
            verb = spec.get('verb')
            if verb not in self.verbs:
                out.append((where, f"`statements` reads statements of a verb: {verb!r} is no verb of the law"))
                return None
            mine = verb_roles(verb) | roles
            for k in (f.split('=', 1)[0].strip() for f in str(spec.get('with') or '').split(',') if '=' in f):
                if k not in mine:
                    out.append((where, f"`with` filters on `{k}`, which is no role of {verb}"))
            if naming and not spec.get('naming'):
                out.append((where, "`statements` here names the role that names the bean it is read for: `naming`"))
            elif not naming and spec.get('naming'):
                out.append((where, "statements that are the records name no bean: no `naming`"))
            if spec.get('naming') and spec['naming'] not in mine:
                out.append((where, f"`{spec['naming']}` is no role of {verb}"))
            if spec.get('ended_by') is not None and spec['ended_by'] not in self.verbs:
                out.append((where, f"`ended_by`: {spec['ended_by']!r} is no verb of the law"))
            if spec.get('standing') is not None and str(spec['standing']).lower() not in ('true', 'false'):
                out.append((where, "`standing` is true or false"))
            return verb
        path = re.compile(r'^([a-z][a-z-]*)(\[([a-z-]+=[^,\]]+(,[a-z-]+=[^,\]]+)*)\])?\.([a-z]+)$')
        roles = set(self.roles)

        def path_ok(where, p):
            from core.crosswalk import steps
            *through, last = steps(p)
            for step in through:                    # a step a path goes on from names a being, or a statement in one
                m = path.match(step)
                if not m:
                    out.append((where, f"{p!r}: {step!r} is no step a path goes on from: <verb>[<role>=<value>,…].<role>"))
                    continue
                spec = ((self.verbs.get(m.group(1)) or {}).get('roles') or {}).get(m.group(5)) or {}
                shape = spec.get('shape') if isinstance(spec, dict) else None
                shapes = shape if isinstance(shape, list) else [shape]
                if m.group(1) in self.verbs and not ({'being', 'statement'} & set(shapes)):
                    out.append((where, f"{p!r}: {step!r} reads no being, so no path goes on from it"))
                step_ok(where, step)
            step_ok(where, last)

        def step_ok(where, p):
            if p in ('title', 'summary', 'bean'):
                return
            m = path.match(str(p))
            if not m:
                out.append((where, f"{p!r} is no path: title, summary, bean, or <verb>[<role>=<value>,…].<role>"))
                return
            verb, role = m.group(1), m.group(5)
            if verb not in self.verbs:
                out.append((where, f"{p!r}: {verb} is no verb of the law"))
            elif role not in roles and role not in verb_roles(verb) | {'while', 'why', 'note'}:
                out.append((where, f"{p!r}: {role} is no role of {verb}"))
        for name, r in rows.items():
            where = f"crosswalk {name}"
            out += self._carried_row_problems(where, r)
            for k in r:
                if row_keys and k not in row_keys:
                    out.append((where, f"`{k}` is no key of a crosswalk ({', '.join(sorted(row_keys))})"))
            for k, need in (forms.get('crosswalk') or {}).items():
                if need == 'required' and k not in r:
                    out.append((where, f"has no `{k}`"))
            record_verb = None
            if (r.get('kind') is None) == (r.get('statements') is None):
                out.append((where, "a crosswalk's records are the beans of a `kind`, or the `statements` of a verb: one of "
                                   "`kind` and `statements`"))
            if r.get('statements') is not None:
                record_verb = statements_ok(where, r['statements'], naming=False)
                if r.get('select'):
                    out.append((where, "statements that are the records are chosen by their `statements` form: no `select`"))
            elif r.get('kind') not in self.kinds:
                out.append((where, f"its kind {r.get('kind')!r} is no kind of the law"))
            same = {str(o.get('model')) for o in rows.values()
                    if str(o.get('system')) == str(r.get('system')) and str(o.get('series')) == str(r.get('series'))}
            records_statements = {str(o.get('model')) for o in rows.values() if o.get('statements') is not None
                                  and str(o.get('model')) in same}
            sel = r.get('select') or {}
            for k, v in sel.items():
                if k in ('with', 'without'):
                    path_ok(where, v)
                elif k in ('within', 'reached') and isinstance(v, dict):
                    path_ok(where, v.get('along'))
                    if str(v.get('model')) not in same:
                        out.append((where, f"select.{k} names {v.get('model')!r}, which no crosswalk of its series crosses"))
                    elif str(v.get('model')) in records_statements:
                        out.append((where, f"select.{k} names {v.get('model')!r}, whose records are statements, and a path "
                                           f"reads beans: the beans a statement in force names are selected by `named_in`"))
                elif k == 'named_in':
                    statements_ok(f"{where} select.named_in", v, naming=True)
                else:
                    out.append((where, f"select.{k} is none of with, without, within, reached, named_in"))
            for fname, spec in (r.get('fields') or {}).items():
                fw = f"{where} field {fname}"
                if not isinstance(spec, dict):
                    out.append((fw, "is no field: { from | value, model?, inverse?, chain?, along?, join? }"))
                    continue
                for k in spec:
                    if field_keys and k not in field_keys:
                        out.append((fw, f"`{k}` is no key of a field ({', '.join(sorted(field_keys))})"))
                if 'map' in spec and not (isinstance(spec['map'], dict) and spec['map']):
                    out.append((fw, "`map` maps each value read to the one the system writes: a mapping, not empty"))
                if 'exists' in spec and (spec['exists'] not in (True, 'true') or 'statements' not in spec
                                         or {'from', 'model'} & set(spec)):
                    out.append((fw, "`exists` is true, with `statements`, and reads nothing else: whether one is in force"))
                frm = str(spec.get('from', ''))
                own_role = record_verb is not None and 'from' in spec and frm not in ('title', 'summary', 'bean') and \
                    '[' not in frm and '/' not in frm         # a role of the record's own statement, or a key inside it
                if 'statements' in spec:
                    fverb = statements_ok(fw, spec['statements'], naming=True)
                    if fverb and 'from' in spec and str(spec['from']) not in verb_roles(fverb) | roles:
                        out.append((fw, f"`{spec['from']}` is no role of {fverb}"))
                elif own_role:
                    if frm.split('.')[0] not in verb_roles(record_verb) | roles | {'id', 'while', 'why', 'note'}:
                        out.append((fw, f"`{frm}` is no role of {record_verb}"))
                elif 'from' in spec:
                    path_ok(fw, spec['from'])
                out += self._carried_field_problems(fw, r, fname, spec)
                if 'model' in spec and str(spec['model']) not in same:
                    out.append((fw, f"names {spec['model']!r}, which no crosswalk of its series crosses"))
                if ('inverse' in spec or 'chain' in spec) and 'model' not in spec:
                    out.append((fw, "`inverse` and `chain` read records of a `model`, and name none"))
                if ('join' in spec) != ('along' in spec):
                    out.append((fw, "`join` and `along` go together: the titles along a path, joined"))
                if 'along' in spec:
                    path_ok(fw, spec['along'])
                if 'value' in spec and 'from' in spec:
                    out.append((fw, "a field is read `from` the bean, or given as a `value`, never both"))
                if spec.get('many') is not None and ('model' not in spec or spec['many'] not in (True, 'true')):
                    out.append((fw, "`many` is true, with the `model` whose records the path reaches"))
                if 'position' in spec and spec['position'] not in ('from', 'to', 'days', 'moment-from', 'moment-to'):
                    out.append((fw, "`position` is one of from, to, days, moment-from, moment-to"))
                if 'stands' in spec:
                    st = spec['stands']
                    if not isinstance(st, dict) or not st or set(st) - {'none', 'step', 'final', 'exit'} or \
                            {'from', 'model', 'value'} & set(spec):
                        out.append((fw, "`stands` names, of none, step, final and exit, the value each gives, and reads "
                                        "nothing else"))
                if 'held' in spec:
                    from core.crosswalk import steps
                    last = steps(spec.get('from', 'title'))[-1]
                    if spec['held'] not in (True, 'true'):
                        out.append((fw, "`held` is true, or left out"))
                    elif last in ('title', 'summary', 'bean') or {'model', 'value', 'join'} & set(spec):
                        out.append((fw, "a held field reads the role of a sealed statement: a path to a verb's role, and "
                                        "no `model`, `value` or `join`"))
        return out

    def form_problems(self):
        """[(where, message)]: each scheme that names a form of a profile (`form`, registries.yaml) held to it: the form
        a profile's, and one the garden takes — a scheme the release carries is held to it in every garden; its columns
        the scheme's own (code, level, parent, name, a name in a language `name_<lang>`) and the form's. Then each form
        by its own: a CHART (the accounting profile's) — an element, a role, a kind of the law; a postable account (a
        code no other code has for its parent) saying what it is, itself or by an ancestor; one account standing for a
        being and one taking each role; that the being is one the garden holds is the garden's to say
        (core/profiles.py `charts`). A PATTERN (the knowledge profile's) — its template in the slots of
        core/law/lines.yaml, what it suggests codes of the schemes the garden reads, what it reads a field path, its
        calendar a system of time, its grouping a row of `groupings`, its `within` and `beside` codes. A CLASS — a
        being it stands for once, `apart` true or absent, and no cycle among its codes' parents."""
        out = []
        if not self.std:
            return out
        K = self.std.knowledge
        released = {str(r.get('scheme')) for r in self.std.tables.get('knowledge_schemes') or [] if isinstance(r, dict)}
        brought = sorted(f for p in self.profiles.values() for f in listed(p.get('forms')))
        for scheme, srow in sorted(K.schemes.items()):
            form = srow.get('form') if isinstance(srow, dict) else None
            if form is None:
                continue
            where = f"scheme {scheme} form {form}"
            owner = next((n for n, p in self.profiles.items() if form in listed(p.get('forms'))), None)
            spec = self.forms.get(str(form)) if owner else None
            if not owner or not isinstance(spec, dict):
                out.append((where, f"`{form}` is no form a profile brings: one of {', '.join(brought)}"))
                continue
            if self.taken_where is not None and owner not in self.taken and scheme not in released:
                out.append((where, f"`{form}` is the {owner} profile's, which this garden does not take"))
                continue
            try:
                rows = [dict(r) for r in K.rows(str(scheme))]
            except (KeyError, OSError, ValueError) as e:
                out.append((where, f"its rows cannot be read: {e}"))
                continue
            attrs = spec.get('attrs') or {}
            cols = {'code', 'level', 'parent', 'name'} | set(attrs)
            for r in rows:
                code = str(r.get('code') or '')
                odd = sorted(k for k, v in r.items() if k not in cols and v not in (None, '')
                             and not NAME_IN.match(str(k)))          # its name in a language (bin/knowledge.py `label`)
                if odd:
                    out.append((f"scheme {scheme} {code or '(no code)'}",
                                f"{', '.join(odd)}: no column of a {form} ({', '.join(sorted(cols))})"))
            judge = {'chart': self._chart_rows, 'pattern': self._pattern_rows, 'class': self._class_rows,
                     'keep': self._keep_rows, 'schema': self._schema_rows}.get(str(form))
            if judge:
                out += judge(scheme, rows)
        return out

    def _chart_rows(self, scheme, rows):
        out = []
        by = {str(r.get('code') or ''): r for r in rows}
        parents = {str(r.get('parent') or '') for r in rows}
        stands, roles = {}, {}
        for r in rows:
            code = str(r.get('code') or '')
            at = f"scheme {scheme} {code or '(no code)'}"
            el = str(r.get('element') or '')
            if el and self.has('elements', el):
                out.append((at, f"element: {self.has('elements', el)}"))
            ro = str(r.get('role') or '')
            if ro and self.has('account_roles', ro):
                out.append((at, f"role: {self.has('account_roles', ro)}"))
            elif ro and ro in roles:
                out.append((at, f"takes the role {ro}, which {roles[ro]} takes: one account a role"))
            elif ro:
                roles[ro] = code
            for k in str(r.get('parties') or '').split():
                if k not in self.kinds:
                    out.append((at, f"parties: {k!r} is no kind of the law"))
            sf = str(r.get('stands_for') or '')
            if sf and sf in stands:
                out.append((at, f"stands for {sf}, as {stands[sf]} does: one account of a chart a being"))
            elif sf:
                stands[sf] = code
            cl = str(r.get('closed') or '')
            if cl and not re.match(r'^\d{4}-\d{2}-\d{2}$', cl):
                out.append((at, f"closed: {cl!r} is no day, `YYYY-MM-DD`"))
            if code and code not in parents:
                c, seen = code, set()
                while c in by and c not in seen and not by[c].get('element'):
                    seen.add(c)
                    c = str(by[c].get('parent') or '')
                if not (c in by and by[c].get('element')):
                    out.append((at, "a postable account says what it is: its element, or an ancestor's"))
        return out

    def _pattern_rows(self, scheme, rows):
        from core import groupings
        import parse as dmparse                         # the one matcher of a pattern of the law
        out = []
        slots = self.slots
        times = {k for k, r in self.systems.items() if isinstance(r, dict) and r.get('dimension') == 'time'}
        names = set(self.groupings)
        fpath = next((t.get('pattern') for t in listed(self.line_law.get('types'))
                      if isinstance(t, dict) and t.get('type') == 'field_path'), None)
        for r in rows:
            code = str(r.get('code') or '')
            at = f"scheme {scheme} {code or '(no code)'}"
            t = r.get('template')
            if not t:
                if code and any(str(x.get('parent') or '') == code for x in rows):
                    continue                                  # a heading of patterns beneath it, a convention
                out.append((at, "holds no `template`: a pattern row is its template"))
                continue
            try:
                groupings.parse(str(t), slots)
            except groupings.TemplateError as e:
                out.append((at, f"template: {e}"))
            rd = r.get('reads')
            if rd and fpath and not dmparse.law_match(fpath, str(rd)):
                out.append((at, f"reads: {rd!r} is no field path"))
            if r.get('case') and r['case'] not in ('exact', 'any'):
                out.append((at, f"case: {r['case']!r} is `exact` or `any`"))
            if r.get('calendar') and r['calendar'] not in times:
                out.append((at, f"calendar: {r['calendar']!r} is no system of time"))
            if r.get('grouping') and r['grouping'] not in names:
                out.append((at, f"grouping: {r['grouping']!r} is no row of `groupings`"))
            if r.get('marks') and r['marks'] != 'by':
                out.append((at, f"marks: {r['marks']!r} — `by`, the folder that holds a file of this name, or absent"))
            if r.get('match') and r['match'] not in ('whole', 'part', 'word'):
                out.append((at, f"match: {r['match']!r} is `whole`, `part` or `word`"))
            if r.get('only') and r['only'] != 'suggests':
                out.append((at, f"only: {r['only']!r} — `suggests`, a row read for what it suggests alone, or absent"))
            for k in ('within', 'beside'):
                if r.get(k) and self.std.code(str(r[k])):
                    out.append((at, f"{k}: {self.std.code(str(r[k]))}"))
            for c in str(r.get('suggests') or '').split():
                if self.std.code(c):
                    out.append((at, f"suggests: {self.std.code(c)}"))
        return out

    def _keep_rows(self, scheme, rows):
        """A policy scheme's rows (the storage profile's form `keep`): what each covers a list of rows of `risks`, its
        `within` a length of time, its `for` codes of schemes the garden reads."""
        out = []
        for r in rows:
            at = f"scheme {scheme} {r.get('code') or '(no code)'}"
            for risk in str(r.get('covers') or '').split():
                if self.has('risks', risk):
                    out.append((at, f"covers: {risk!r} is no row of `risks` (the garden's own, VOCAB.md `risks`)"))
            if r.get('within') not in (None, ''):
                _q, why = self.duration(r['within'])
                if why:
                    out.append((at, f"within: {why}"))
            for c in str(r.get('for') or '').split():
                if self.std.code(c):
                    out.append((at, f"for: {self.std.code(c)}"))
        return out

    def _schema_rows(self, scheme, rows):
        """A directory's schema (the storage profile's form `schema`): each node a child of a schema, its template's slots
        rows of `layout_slots` in a form they have, what it matches codes the garden reads, `links` only `true`, its cap
        a count and a length of time; a schema's history a being, its gap a length of time."""
        out = []
        codes = {str(r.get('code') or ''): r for r in rows}
        slots = {str(r.get('slot')): r for r in listed(self.profile_tables.get('layout_slots'))}
        for r in rows:
            code = str(r.get('code') or '')
            at = f"scheme {scheme} {code or '(no code)'}"
            parent = str(r.get('parent') or '')
            if parent and (parent not in codes or codes[parent].get('parent')):
                out.append((at, f"parent: {parent!r} is no schema of {scheme} (a node's parent is a code with no parent)"))
            t = str(r.get('template') or '')
            if t and not parent:
                out.append((at, "template: a node's, beneath a schema; a schema holds none"))
            if parent and not t:
                out.append((at, "template: a node says where its members belong, `{day:yyyy}/{name}`"))
            for m in re.finditer(r'\{([^{}]*)\}', t):
                name, _, form = m.group(1).partition(':')
                if name not in slots:
                    out.append((at, f"template: {{{m.group(1)}}} names no slot of `layout_slots`: {', '.join(slots)}"))
                elif form and form not in listed(slots[name].get('forms')):
                    out.append((at, f"template: {{{m.group(1)}}}: `{name}` is written in {', '.join(listed(slots[name].get('forms'))) or 'no form'}"))
                elif not form and slots[name].get('forms'):
                    out.append((at, f"template: {{{name}}} names a form: {', '.join(listed(slots[name].get('forms')))}"))
            if re.sub(r'\{[^{}]*\}', '', t).count('{') or re.sub(r'\{[^{}]*\}', '', t).count('}'):
                out.append((at, "template: a brace stands alone"))
            for c in str(r.get('matches') or '').split():
                if self.std.code(c):
                    out.append((at, f"matches: {self.std.code(c)}"))
            if r.get('links') not in (None, '') and str(r['links']) != 'true':
                out.append((at, f"links: {r['links']!r} is `true`, or absent"))
            if r.get('versions') not in (None, '') and not re.fullmatch(r'[0-9]+', str(r['versions'])):
                out.append((at, f"versions: {r['versions']!r} is a count"))
            for k in ('age', 'gap'):
                if r.get(k) not in (None, ''):
                    _q, why = self.duration(r[k])
                    if why:
                        out.append((at, f"{k}: {why}"))
            for k in ('history', 'gap'):
                if r.get(k) not in (None, '') and parent:
                    out.append((at, f"{k}: a schema's, not a node's"))
        return out

    def _class_rows(self, scheme, rows):
        from core import groupings
        out, stands = [], {}
        for r in rows:
            code = str(r.get('code') or '')
            at = f"scheme {scheme} {code or '(no code)'}"
            sf = str(r.get('stands_for') or '')
            if sf and sf in stands:
                out.append((at, f"stands for {sf}, as {stands[sf]} does: one code a being"))
            elif sf:
                stands[sf] = code
            if r.get('apart') not in (None, '', 'true'):
                out.append((at, f"apart: {r['apart']!r} is `true`, or absent"))
        loop = groupings.cycle({str(r.get('code')): [str(r['parent'])] for r in rows if r.get('parent')})
        if loop:
            out.append((f"scheme {scheme}", f"its codes' parents run in a cycle: {' → '.join(loop)}"))
        return out

    def duration(self, text):
        """(count, unit) of a length of time written `<count> <unit>` (`365 d`), its unit one of the law's of duration;
        or (None, why not)."""
        m = re.fullmatch(r'(\d+(?:\.\d+)?) (\S+)', str(text or '').strip())
        if not m:
            return None, f"{text!r} is no length of time: a count and a unit, `365 d`"
        row = self.units.get(m.group(2))
        if not isinstance(row, dict) or row.get('quantity') != 'duration' or Decimal(m.group(1)) <= 0:
            return None, f"{text!r}: a positive count of a unit of duration (s, min, h, d …)"
        return (m.group(1), m.group(2)), None

    def risk_problems(self):
        """[(where, message)]: each risk a garden adds (VOCAB.md `risks`, the storage profile's table) in its form —
        named, said for a reader, resolved by a list of ways, each a map of keeping properties to a least count — and
        only where the garden takes the storage profile."""
        out = []
        props = set(self.tables.get('keeping_properties') or [])
        for r in listed(self.own.get('risks')):
            where = str(r.get('at') or 'VOCAB.md risks')
            if self.taken_where is not None and 'storage' not in self.taken:
                out.append((where, "`risks` are the storage profile's, which this garden does not take"))
                continue
            if not str(r.get('meaning') or '').strip():
                out.append((where, f"risk {r.get('risk')}: say what happens, in `meaning`"))
            ways = r.get('resolved_by')
            if not isinstance(ways, list) or not ways:
                out.append((where, f"risk {r.get('risk')}: `resolved_by` is a list of ways, each a map of keeping "
                                   f"properties to a least count: `[ {{ disk: 2 }}, {{ array: 1 }} ]`"))
                continue
            for way in ways:
                if not isinstance(way, dict) or not way:
                    out.append((where, f"risk {r.get('risk')}: {way!r} is no map of keeping properties to counts"))
                    continue
                for k, v in way.items():
                    if str(k) not in props:
                        out.append((where, f"risk {r.get('risk')}: `{k}` is no keeping property: one of "
                                           f"{', '.join(sorted(props))}"))
                    if not re.fullmatch(r'[1-9]\d*', str(v)):
                        out.append((where, f"risk {r.get('risk')}: {k}: {v!r} is a least count, a whole number from 1"))
        return out

    def grouping_problems(self):
        """[(where, message)]: each grouping (core/law/lines.yaml `groupings`, and a garden's own) a reading of the law's
        closed list (bin/reckon.py's check), its `home` core or a profile, each field of its `line` one a line has; each
        slot in its form; each aspect of the view following a verb or a grouping, laid out by a row of `orientations`,
        of kinds of the law, at home in core or a profile."""
        out = []
        homes = {'core'} | set(self.profiles)
        fields = {'range', 'count', 'missing', 'extent', 'values', 'code', 'apart'}
        try:
            from core import lines as core_lines
            view = core_lines.law_view(self)
        except Exception:          # noqa: BLE001 — a release without the reckoner judges the rest
            core_lines = view = None
        law_names = {str(r.get('grouping')) for r in listed(getattr(self, 'line_law', {}).get('groupings'))
                     if isinstance(r, dict)}
        for r in listed(self.own.get('groupings')):
            if isinstance(r, dict) and str(r.get('grouping')) in law_names:
                out.append((r.get('at') or 'VOCAB.md groupings', f"`{r['grouping']}` is a grouping of the law already: a "
                                                                 f"garden's own grouping takes a name of its own"))
        for name, g in sorted(self.groupings.items()):
            where = f"grouping {name}"
            if str(g.get('home')) not in homes:
                out.append((where, f"home: {g.get('home')!r} is `core` or a profile: {', '.join(sorted(homes - {'core'}))}"))
            for f in listed(g.get('line')):
                head, _, path = str(f).partition(':')
                if head in ('cells', 'agree', 'each', 'sum'):
                    if not path:
                        out.append((where, f"line: `{head}` names a path, `{head}:<path>`"))
                elif head not in fields:
                    out.append((where, f"line: `{f}` is no field of a line: {', '.join(sorted(fields))}, or "
                                       f"cells:/agree:/each:/sum: a path"))
            if core_lines is not None:                # read in the garden's zone (GARDEN.md `zone`): the reader gives it
                out += core_lines.reading_problems(where, dict(g, zone=g.get('zone') or 'Etc/UTC'), view, self.verbs)
        for name, row in sorted(self.slots.items()):
            if row.get('width') not in (None, 'allowed', 'required'):
                out.append((f"slot {name}", f"width: {row['width']!r} is `allowed` or `required`"))
            if row.get('matches') is not None and not self._compiles(row['matches'], f"slot {name}"):
                out.append((f"slot {name}", "matches: a pattern that compiles"))
        orders = {str(r.get('order')) for r in self.table('orientations') or [] if isinstance(r, dict)}
        for row in listed(self.table('aspects')):
            if not isinstance(row, dict):
                continue
            where = f"aspect {row.get('aspect')}"
            if str(row.get('home')) not in homes:
                out.append((where, f"home: {row.get('home')!r} is `core` or a profile"))
            f = str(row.get('follows'))
            if f not in self.verbs and f not in self.groupings:
                out.append((where, f"follows: {f!r} is neither a verb nor a grouping"))
            if str(row.get('order')) not in orders:
                out.append((where, f"order: {row.get('order')!r} is no row of `orientations`"))
            if row.get('points') not in ('by', 'of', 'from', 'to', 'through', 'at'):
                out.append((where, f"points: {row.get('points')!r} is the role the cursor fills"))
            for k in listed(row.get('of')):
                if str(k) not in self.kinds:
                    out.append((where, f"of: {k!r} is no kind of the law"))
        return out

    def formats_problems(self):
        """[(where, message)]: the formats law held together (core/law/formats.yaml): each reader reads formats of the
        table, and each scheme the law holds `fetched` names a reader of it that is no profile's."""
        out = []
        for name, r in self.readers.items():
            for f in listed(r.get('format')):
                if str(f) not in self.formats:
                    out.append((f"core/law/formats.yaml readers {name!r}", f"reads {f!r}, which is no format of the law"))
        reg = os.path.join(getattr(self, 'dir', None) or LAW_DIR, 'registries.yaml')
        for row in listed((read.data(reg) if os.path.isfile(reg) else {}).get('knowledge_schemes')):
            fetch = row.get('fetch') if isinstance(row, dict) else None
            if isinstance(fetch, dict) and fetch.get('reader') is not None:
                rd = self.readers.get(str(fetch['reader']))
                if rd is None or rd.get('home'):
                    out.append((f"core/law/registries.yaml knowledge_schemes {row.get('scheme')!r}",
                                f"fetch.reader {fetch['reader']!r} is no reader of core/law/formats.yaml `readers` the "
                                f"release reads with"))
        return out

    def _carried_row_problems(self, where, r):
        """[(where, message)]: what a crosswalk says of how its records come and go (2.12, core/law/formats.yaml): its
        formats and reader, the act its statements are known by, where they are kept, the forms its parts compose."""
        out = []
        fmts = [str(f) for f in listed(r.get('format'))]
        for f in fmts:
            if f not in self.formats:
                out.append((where, f"`format`: {f!r} is no format of the law ({', '.join(self.formats)})"))
        if r.get('reader') is not None:
            rd = self.readers.get(str(r['reader']))
            if rd is None:
                out.append((where, f"`reader`: {r['reader']!r} is no reader of the law ({', '.join(self.readers)})"))
            elif not fmts:
                out.append((where, "a crosswalk read through a reader names the format its records come in"))
            else:
                for f in fmts:
                    if f not in [str(x) for x in listed(rd.get('format'))]:
                        out.append((where, f"the reader {r['reader']} reads no {f}"))
        for k in ('records', 'act', 'compose', 'given'):
            if r.get(k) is not None and not isinstance(r[k], dict):
                out.append((where, f"`{k}` is a mapping"))
        act = r.get('act')
        if isinstance(act, dict):
            if act.get('verb') not in self.knowing:
                out.append((where, f"`act.verb` is a knowing act ({', '.join(self.knowing)}), not {act.get('verb')!r}"))
            if act.get('per') is not None and act['per'] not in ('import', 'record'):
                out.append((where, "`act.per` is `import` (one act for all it keeps) or `record` (an act a record)"))
        if r.get('keep') is not None and r['keep'] not in ('store', 'bean'):
            out.append((where, "`keep` is `store` or `bean`"))
        if r.get('whole') is not None and str(r['whole']).lower() not in ('true', 'false'):
            out.append((where, "`whole` is true or false"))
        if r.get('self') is not None and r['self'] not in self.roles:
            out.append((where, f"`self`: {r['self']!r} is no role"))
        if (r.get('format') is None) != (r.get('act') is None):
            out.append((where, "a crosswalk that says how its records come names both its `format` and its `act`"))
        parts = {str(spec.get('part')) for spec in (r.get('fields') or {}).values()
                 if isinstance(spec, dict) and spec.get('part') is not None}
        for path, form in (r.get('compose') or {}).items():
            want = set(re.findall(r'\{(\w+)\}', str(form)))
            if not want:
                out.append((f"{where} compose {path}", "a form names its parts in braces: `{crs};{lat},{lon}`"))
            for w in sorted(want - parts):
                out.append((f"{where} compose {path}", f"no field is the part `{w}`"))
        return out

    def _carried_field_problems(self, fw, r, fname, spec):
        """[(where, message)]: a field's conversion, part, unit, the fields it takes roles from, its reason dropped."""
        out = []
        if 'as' in spec:
            conv = spec['as']
            names = [conv] if isinstance(conv, str) else [k for k in conv if k in self.conversions] \
                if isinstance(conv, dict) else []
            if len(names) != 1 or names[0] not in self.conversions:
                out.append((fw, f"`as` names one conversion of the law ({', '.join(self.conversions)})"))
            elif isinstance(conv, dict) and set(conv) - {names[0], 'hint', 'none'}:
                out.append((fw, f"`as` holds its conversion and `hint`, `none`: not {', '.join(sorted(set(conv) - {names[0], 'hint', 'none'}))}"))
        if 'part' in spec:
            if str(spec.get('from')) not in {str(k) for k in (r.get('compose') or {})}:
                out.append((fw, "a part is read into a value the row's `compose` gives the form of, by its `from`"))
        if 'unit' in spec:
            why = self.has('units', str(spec['unit']))
            if why:
                out.append((fw, f"`unit`: {why}"))
        if 'with' in spec:
            fields = r.get('fields') or {}
            if not isinstance(spec['with'], dict) or not spec['with']:
                out.append((fw, "`with` names, for each other role of the statement, the field that fills it"))
            else:
                for role, f in spec['with'].items():
                    if role not in self.roles:
                        out.append((fw, f"`with`: {role!r} is no role"))
                    if str(f) not in fields:
                        out.append((fw, f"`with`: {f!r} is no field of the row"))
        if 'drop' in spec and ({'from', 'value'} & set(spec) or not str(spec['drop']).strip()):
            out.append((fw, "a field dropped says why (`drop`), and is read into nothing"))
        return out

    def units_crosswalk_problems(self):
        """[(where, message)]: each scheme's crossing into the law's units and kinds (`units`), held to
        registries.yaml's `units_crosswalk_form`: its registry declared and read, its columns the form's, and each row at
        most one target that is the law's — a unit, a kind, a line, a system of positions alone or with one of its
        levels, a shape — with `why` where it has none; `vacant` a vacancy's reason, on a row with no target; `decimals`
        `n` on a unit's row whose code ends in it; and of several rows crossing to one target, one marked `back`."""
        out = []
        if not self.std:
            return out
        import units as dmunits
        form = self.std.tables.get('units_crosswalk_form') or {}
        cols = set(form) - {'requires'}
        K = self.std.knowledge
        lines = {str(r.get('line')) for r in listed((self.measure_law or {}).get('lines')) if isinstance(r, dict)}
        systems = self.systems
        for scheme, srow in sorted(K.schemes.items()):
            reg = srow.get('units') if isinstance(srow, dict) else None
            if not reg:
                continue
            where = f"scheme {scheme} units {reg}"
            if reg not in K.decl:
                out.append((where, f"names {reg!r}, which no registry file declares (`registry_files`, `files`)"))
                continue
            try:
                rows = K.rows(str(reg))
            except (KeyError, OSError) as e:
                out.append((where, f"cannot be read: {e}"))
                continue
            if rows and set(rows[0]) - cols:
                out.append((where, f"{', '.join(sorted(set(rows[0]) - cols))}: no column of `units_crosswalk_form` "
                                   f"({', '.join(sorted(cols))})"))
            seen, targets = set(), {}
            for i, r in enumerate(rows):
                r = {k: v for k, v in r.items() if v not in (None, '')}
                code, axis = str(r.get('code') or ''), str(r.get('axis') or '')
                at = f"{where} {(axis + ':') if axis else ''}{code or f'[{i + 1}]'}"
                if not code:
                    out.append((at, "a row names its `code`"))
                    continue
                if (axis, code) in seen:
                    out.append((at, "is written twice: one row a code"))
                seen.add((axis, code))
                t = dmunits.target(r)
                named = [k for k in dmunits.TARGETS if k in t]
                if len(named) > 1:
                    out.append((at, f"crosses to {' and '.join(named)}: one target a row"))
                if 'level' in r and 'in' not in r:
                    out.append((at, "`level` is a level of the system `in` names, and it names none"))
                if not t and not r.get('why'):
                    out.append((at, "crosses to nothing, and says no `why`"))
                if r.get('vacant') is not None and (t or r['vacant'] not in self.vacancy_reasons):
                    out.append((at, f"`vacant: {r['vacant']}` is a vacancy's reason ({', '.join(self.vacancy_reasons)}) "
                                    f"on a row that crosses to nothing"))
                if 'unit' in r and r['unit'] not in self.units:
                    out.append((at, f"{r['unit']!r} is no unit of the law in UCUM (core/law/units.yaml)"))
                if 'quantity' in r and r['quantity'] not in self.std.quantities:
                    out.append((at, f"{r['quantity']!r} is no kind of the law (core/law/quantities.yaml)"))
                if 'line' in r and r['line'] not in lines:
                    out.append((at, f"{r['line']!r} is no line of the law: one of {', '.join(sorted(lines))}"))
                if 'shape' in r and r['shape'] not in self.shapes:
                    out.append((at, f"{r['shape']!r} is no shape of the core: one of {', '.join(sorted(self.shapes))}"))
                if 'in' in r:
                    srow = systems.get(r['in'])
                    lvls = [str(lv.get('level')) for lv in listed((srow or {}).get('levels')) if isinstance(lv, dict)]
                    if srow is None:
                        out.append((at, f"{r['in']!r} is no system of positions of the law"))
                    elif 'level' in r and r['level'] not in lvls:
                        out.append((at, f"{r['level']!r} is no level of {r['in']}: one of {', '.join(lvls)}"))
                    elif 'level' not in r and dmunits.position_tag(srow) is None:
                        out.append((at, f"{r['in']} writes no position from a count, so no code is its unit of "
                                        f"position: name one of its levels"))
                if 'decimals' in r and (r['decimals'] != 'n' or (t and 'unit' not in t) or not code.endswith('n')):
                    out.append((at, "`decimals: n` is a family's, its code written with `n` for its last digit, crossing "
                                    "to a unit or to nothing"))
                if r.get('back') not in (None, TRUE):
                    out.append((at, "`back` is written `true`, or not at all"))
                if t:
                    targets.setdefault((axis, tuple(sorted(t.items()))), []).append((code, r.get('back') == TRUE))
            for (axis, t), codes in sorted(targets.items()):
                backs = [c for c, b in codes if b]
                shown = ', '.join(f"{k}: {v}" for k, v in t)
                if len(codes) > 1 and len(backs) != 1:
                    out.append((where, f"{', '.join(c for c, _b in codes)} cross to {shown}, and "
                                       f"{'none is' if not backs else f'{len(backs)} are'} marked `back`: one is the "
                                       f"code it is written back as"))
                elif len(codes) == 1 and backs:
                    out.append((f"{where} {backs[0]}", f"is marked `back`, and is the one code crossing to {shown}"))
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
        store = getattr(self, 'store_shape', None) or {}         # A STORE'S SHAPE: a pointer that reads, forms named
        if store:
            pat = (store.get('pointer') or {}).get('pattern')
            try:
                rx = re.compile(str(pat))
                if rx.groups < 2 or not rx.match('store:content:c-0') or rx.match('root:x/y'):
                    bad('core/law/layers.yaml store_shape.pointer', "reads `store:<kind>:<id>`, its kind and its id, and "
                                                                    "nothing else")
            except re.error as e:
                bad('core/law/layers.yaml store_shape.pointer', f"its pattern is no regular expression: {e}")
            forms = [f.get('form') for f in listed(store.get('forms')) if isinstance(f, dict)]
            if not forms or len(forms) != len(set(forms)) or not all(isinstance(f, dict) and f.get('meaning')
                                                                     for f in listed(store.get('forms'))):
                bad('core/law/layers.yaml store_shape.forms', "names each form a store may be kept in once, with its "
                                                              "meaning")
            if 'store' in (self.systems or {}):
                bad('core/law/layers.yaml store_shape.pointer', "`store` is the pointer's word, and a system takes it")
            if 'store' not in self.flow_sources:
                bad('core/law/layers.yaml store_shape', "a store is a source of the flow law: `flow_sources` names it")
        covers = listed(((self.std.tables or {}).get('system_shape') or {}).get('covers')) if self.std else []
        for name, row in (self.systems or {}).items():         # WHAT A POSITION COVERS: a point or an area, the room rule's
            c = row.get('covers') if isinstance(row, dict) else None   # question; a pair of patterns where it holds both
            if c is None:
                if name in (self.std_systems() or {}) and str(row.get('dimension')) in ('place', 'any'):
                    bad(f"systems {name}", "a system a being is placed at says what its positions cover — `covers: point`, "
                                           "`area`, or `{ point: <pattern>, area: <pattern> }`")
                continue
            if isinstance(c, dict):
                if not c or set(c) - set(covers) or not all(isinstance(v, str) for v in c.values()):
                    bad(f"systems {name}", f"`covers` as patterns names each of {', '.join(covers)} it holds, a pattern "
                                           f"of its positions each")
                for v in c.values():
                    try:
                        re.compile(str(v))
                    except re.error as e:
                        bad(f"systems {name}", f"`covers` holds a pattern that does not compile: {e}")
            elif str(c) not in covers:
                bad(f"systems {name}", f"covers `{c}`, which `system_shape.covers` does not offer ({', '.join(covers)})")
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
        for where, msg in self.given_twice(dim_rows):
            bad(where, msg)
        for where, msg in self.crosswalk_problems():
            bad(where, msg)
        for where, msg in self.formats_problems():
            bad(where, msg)
        for where, msg in self.units_crosswalk_problems():
            bad(where, msg)
        for where, msg in self.form_problems():
            bad(where, msg)
        for where, msg in self.grouping_problems():
            bad(where, msg)
        for where, msg in self.risk_problems():
            bad(where, msg)
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
