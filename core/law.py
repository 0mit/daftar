"""law — the face and the rows, loaded as one law and proved consistent with itself.

The face is `core/law/core.yaml`: the seven roles, the shapes, the grammar's words, the two figures, the order (natures,
lines, levels, conditions, the crown), the face's verbs and the eighteen rules. The verbs beyond the face are rows,
`core/law/verbs.yaml`. A garden adds rows of its own in its VOCAB.md, under these keys only:

  kinds         { kind, nature, line?, level?, rung?, meaning? }       what a bean records
  levels        { level, line, stands: [{ at, as, while? }], meaning? } the detailed steps of the lines (our knowledge tree)
  namespaces    { namespace, once?, meaning? }                         who gives names, and whether once (beside the
                                                                       standards' own, core/law/namespaces.yaml)
  flows         { flow?, from, to, through, grant, why? }              the flow table: which passes stand
  flow_sources  [ name, … ]                                            the flow law's sources beside the layers
  standing      { layer, holds: [pattern, …], meaning? }               which files sit in which layer
  verbs         rows in the form of verbs.yaml                         a garden's own verbs
  units         { unit, name, quantity, ucum?, why? }                  a unit in UCUM, its English name attached
  tables        { <table>: [row, …] }                                  rows added to a verbs' table or a standard's
  exclusive     { verb, why? }                                         a verb whose `at` holds one being once (rule room)

A garden's kind, level, namespace, verb or unit may say `vacant: <why>`: a row no bean uses yet (rule vacancy).

A row may not take a name the face or another row has: the law is one, and a second row of one name is two laws.
Every value is a string (core/read.py): a flag is the string `true`. A key of VOCAB.md that is none of these is today's
law's (std-vocab 32.0), which today's gate reads; this law passes it by."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from core import read, standards  # noqa: E402

LAW_DIR = os.path.join(HERE, 'law')
GENERATED = ('levels.yaml', 'layers.yaml', 'kinds.yaml')   # rows generated from today's law: the bodies' levels, the
                                                           # layers and standing, and the kinds (the standards' tables,
                                                           # generated too, are read by core/standards.py)
ROW_FILES = GENERATED + ('units.yaml', 'namespaces.yaml')  # and the units in UCUM, each with the law's English name,
                                                           # and the namespaces the standards give names in
ROW_KEYS = {'kinds': 'kind', 'levels': 'level', 'namespaces': 'namespace', 'flows': None, 'flow_sources': None,
            'standing': 'layer', 'verbs': 'verb', 'tables': None, 'units': 'unit', 'exclusive': 'verb'}
ROW_FIELDS = {
    'kinds': {'kind', 'nature', 'line', 'level', 'rung', 'meaning', 'vacant'},
    'levels': {'level', 'line', 'stands', 'meaning', 'frame_of', 'vacant'},
    'namespaces': {'namespace', 'once', 'meaning', 'vacant'},
    'flows': {'flow', 'from', 'to', 'through', 'grant', 'why'},
    'standing': {'layer', 'holds', 'meaning'},
    'verbs': {'verb', 'meaning', 'roles', 'qualifiers', 'required', 'choice', 'default', 'replaces', 'home', 'figure',
              'vacant'},
    'units': {'unit', 'name', 'quantity', 'ucum', 'why', 'vacant'},
    'exclusive': {'verb', 'why'},
}
GARDEN = 'VOCAB.md'                                        # where a garden's own rows are read from
SPEC_KEYS = {'shape', 'table', 'nature', 'rung', 'many', 'keyed'}
FACE_TABLES = ('ways', 'modes', 'acquisitions', 'placements', 'complements')
TRUE = 'true'


def listed(x):
    """A value that may be written as one or as a list, as a list."""
    if x is None:
        return []
    return list(x) if isinstance(x, list) else [x]


def shapes_of(spec):
    return listed(spec.get('shape')) if isinstance(spec, dict) else []


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
        self.levels, self.kinds, self.namespaces, self.verbs, self.units = {}, {}, {}, {}, {}
        self.flows, self.flow_sources, self.standing, self.exclusive = [], [], [], []
        self.garden_rows = []                               # (key, name, row) of each row a garden added (rule vacancy)
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
        rows = tuple((f"core/law/{n}", read.data(os.path.join(d, n))) for n in ROW_FILES)
        return cls(read.data(os.path.join(d, 'core.yaml')), read.data(os.path.join(d, 'verbs.yaml')),
                   rows + tuple(extensions), std or (standards.here(root) if root else None))

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
            if key not in ROW_KEYS:
                continue
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
                elif key == 'standing':
                    self.standing.append(row)
                elif key == 'exclusive':
                    self.exclusive.append(row)
                else:
                    self._put({'kinds': self.kinds, 'levels': self.levels, 'namespaces': self.namespaces,
                               'verbs': self.verbs, 'units': self.units}[key], row[name_key], row, at)

    # ------------------------------------------------------------------------------------------------ tables
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
        if len(self.roles) != 7:
            bad('core.yaml roles', f"the core has seven roles, and this law {len(self.roles)}")
        known_rules = ['form', 'valency', 'knowing', 'placeholder', 'order', 'life', 'necessity', 'squares', 'weight',
                       'frame', 'names', 'layers', 'ratify', 'consent', 'harm', 'room', 'vacancy', 'kept']
        for x in self.exclusive:
            if x.get('verb') not in self.verbs:
                bad('exclusive', f"`{x.get('verb')}` is no verb of the law: what is exclusive is a verb's `at`")
        if self.rules != known_rules:
            bad('core.yaml rules', f"the engine applies {', '.join(known_rules)}; the law lists {', '.join(self.rules)}")
        for name, v in self.verbs.items():
            self._verb_problems(name, v, bad)
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
            if f.get('grant') not in ('granted', 'refused'):
                bad(f"flow {f.get('flow', i)}", "its grant is `granted` or `refused`")
        for i, s in enumerate(self.standing):
            if s.get('layer') not in layers:
                bad(f"standing {i}", f"{s.get('layer')!r} is no layer")
            for h in listed(s.get('holds')):
                if not isinstance(h, str) or not h:
                    bad(f"standing {i}", f"{h!r}: a pattern of a path")
        names = {}
        for u, row in self.units.items():
            names.setdefault(row.get('name'), []).append(u)
            if row.get('quantity') not in self.std.quantities:
                bad(f"unit {u}", f"its quantity {row.get('quantity')!r} is no quantity of the law")
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
            if r not in roles:
                bad(where, f"requires `{r}`, which it does not take")
        ch = v.get('choice')
        if ch is not None:
            if not isinstance(ch, dict) or set(ch) != {'one_of'} or any(r not in roles for r in listed(ch['one_of'])):
                bad(where, "a choice is `{ one_of: [roles it takes] }`")
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
