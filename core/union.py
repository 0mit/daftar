#!/usr/bin/env python3
"""union — a rule's reading compiled to SQL over the union of git and the stores a host keeps (the next version's P5:
the union judged by the same rules at every size).

A store's check (bin/store.py `check`) judges the union of git and every store a host keeps. A union small enough is
judged whole by the core's engine, each being a store keeps read as a bean. A larger one is not read into memory, and
each rule that is a reading of the law (core.yaml `reading`) is compiled here, step by step, into SQL over the same
union. Each step is read by the same operation core/reckon.py reads it by, so the reading gives the refusals the engine
gives over the union read as beans: each told at the place of its statement, in the order of the reading's `refuse` and
of each step's members, in the same words. Nothing is written into a store: the steps are temporary relations of the
reading's own connection, each store attached to it read-only.

THE UNION, AS THE ENGINE READS IT (bin/store.py `_union_garden`). Every bean of git, a pointer in it read as the plain
id. Each being a store keeps is a bean: where git has none, one of its own, of the kind the store keeps it as
(`document` where it keeps none), after git's beans, the stores in their order and each in the order it keeps its
beings; where git has one, that bean. A being's rows are its bean's statements after git's own, each a row no keeping
before it holds (`Keeping.skip`), in the order the store gives them: by verb, then as they were put. A row's filler is
written as its bean would write it: the being itself `self`, a statement of its own being by its id.

A MEMBER, AS A ROW. Each step is a relation of the members it gives. A value a later step, a condition or a refusal's
words reads is a column: as written and, for a filler, as the being it names (core/engine.py `norm`): one text, or a
list kept as JSON, as a store keeps a list, a map, a number or a truth. Beside them are the columns of the member's
order (`keys`), of where the garden reads its statement (`seq`), and of the statement itself: whose (`_src`, 0 for git,
else 1 and the store's place), its bean, its verb, its index and its place.

THE OPERATIONS. Those the rules' readings are written in (core/law/lines.yaml): `select` of a verb's statements, of the
beans, or of a step, by `exists`, `absent`, `is` and `≠`; `describe`, a being's kind, nature, line and rung from the
law's kinds; `join` of two sets, matched, unmatched or both; `minus`; `first` and `last`; and the two walks, walked
by core/reach.py, the one walk: `cycle` over what SQL leaves of its edges once every one that cannot lie on a cycle
is dropped, `reach` over its relation's edges as SQL reads them. Any other operation, a condition by another comparator, or a path into a filler's own parts has no SQL form here:
`NoSQL` names the step, and the store's check names the rule as not judged at that size.

ONE CASE IS READ OTHERWISE. A store keeps a being's id and a statement's id apart (bin/store.py `normalize`): a filler
it keeps as a being, a list, or a text it keeps outside a statement of its own being is read as it keeps it. The engine
reads every written name alike, and would read such an id as a statement of the bean, where the bean holds a statement
of that id. A statement of its own being the store keeps is read as the engine reads it — that statement where the
bean holds it, else the name — and a bean's own fillers in git are read as the engine reads them."""
import json
import re

from core import reach as _reach
from core import reckon


class NoSQL(Exception):
    """A step, a condition or a path of a reading with no SQL form here: the rule is not judged by its SQL."""


SEQ = ('_bo1', '_bo2', '_src', '_vr', '_i')            # where the garden reads a statement: bean, keeping, verb, row
CARRIED = ('_src', '_bean', '_verb', '_i', '_place', '_bkind')   # what a statement's members carry: its place, and
                                                                    # the kind its bean is of in the union
WORD_SIGNS = {'exists', 'absent', 'is', '≠', 'fits'}
STATEMENT_COLUMNS = ('bean', 'verb', 'index', 'place', 'id')   # describe's columns of a statement (core 3.2): no SQL form yet


def q(name):
    return '"' + str(name).replace('"', '""') + '"'


def enc(v):
    """A value as the union's relations keep it: a text as text, nothing as NULL, anything else as JSON."""
    if v is None or isinstance(v, str):
        return v
    return json.dumps(v, ensure_ascii=False).encode('utf-8')


def dec(v):
    if isinstance(v, bytes):
        return json.loads(v.decode('utf-8'))
    return v


class Keeping:
    """A store as the union reads it: the schema its file is attached as; the verbs it keeps a relation of, in the
    order it gives a being's rows; each verb's relation (`tables`), its columns ({role: (being column or None, text
    column)}) and its roles' shapes ({role: [shapes]}); and `skip`, the rows (verb, n) the union does not hold, git or
    a keeping before it holding the same statement already."""

    def __init__(self, schema, verbs, tables, columns, shapes, skip=()):
        self.schema, self.verbs, self.tables, self.columns, self.shapes = schema, list(verbs), tables, columns, shapes
        self.skip = set(skip)


class Step:
    """A step's members, as a relation: `name`; `cols`, {path: (column as written, column as named)}; `keys`, the
    columns of the members' order; `seq`, those of where the garden reads each member's statement, or None; `kind`:
    `statement` (its members carry their statement's place), `bean`, `law` or `walk` — each path's third column, where
    it has one, the kind of the being a store keeps there (what `describe` reads); `lineage`, what its members
    are, so `minus` compares members of one lineage; `plain`, a select of every bean, which `within` reads as one;
    `foreign`, the paths of a pair read in another statement's bean."""

    def __init__(self, name, cols, keys, seq, kind, lineage, plain=False, foreign=()):
        self.name, self.cols, self.keys, self.seq = name, cols, list(keys), list(seq) if seq else None
        self.kind, self.lineage, self.plain, self.foreign = kind, lineage, plain, set(foreign)


class Union:
    """The union of git (`J`, the engine's Judge of git: its law and its garden) and the stores of `keepings`, each
    attached to the connection `db` under its schema; a rule's reading read over it by `refusals`."""

    def __init__(self, db, J, keepings):
        self.db, self.J, self.L, self.G = db, J, J.L, J.G
        self.K = list(keepings)
        self._n, self._made, self._verbs = 0, [], {}
        self._rk = reckon.Reckoner(None, rules_law=self.L)
        db.create_function('dm_eq', 2, self._eq, deterministic=True)
        db.create_function('dm_written', 4, _written, deterministic=True)
        db.create_function('dm_fits', 2, self._fits, deterministic=True)   # the law's one judge of a form (3.2)
        self._load()

    # ------------------------------------------------------------------------------------------------ the union
    def _name(self, what):
        self._n += 1
        return f"u_{what}_{self._n}"

    def _temp(self, name, cols, rows, index=()):
        self.db.execute(f"CREATE TEMP TABLE {q(name)} ({', '.join(q(c) for c in cols)})")
        self.db.executemany(f"INSERT INTO {q(name)} VALUES ({', '.join('?' * len(cols))})", rows)
        for k, c in enumerate(index):
            self.db.execute(f"CREATE INDEX {q(name + '_' + str(k))} ON {q(name)} ({', '.join(q(x) for x in c)})")
        self._made.append(('TABLE', name))

    def close(self):
        for what, name in reversed(self._made):
            self.db.execute(f"DROP {what} IF EXISTS temp.{q(name)}")
        self._made = []

    def _load(self):
        """git's beans, each with its kind, its place in the garden's order and how many statements it holds; the ids
        each keeps beside the rows a store adds to it; and the law's kinds, each with its line."""
        self._temp('u_git', ('id', 'kind', 'bo', 'nst'),
                   [(b.id, b.kind, k, len(b.statements)) for k, b in enumerate(self.G.beans.values())])
        self.db.execute(f"CREATE UNIQUE INDEX {q('u_git_id1')} ON {q('u_git')} (id)")
        self.extra = {}                      # a bean of git -> the ids of the rows the stores add to it
        for k, K in enumerate(self.K):
            for verb in K.verbs:
                skip = {n for v, n in K.skip if v == verb}
                for bid, sid, n in self.db.execute(
                        f"SELECT g.id, t.id, t.n FROM u_git g JOIN {K.schema}.being b ON b.id = g.id "
                        f"JOIN {K.schema}.{q(K.tables[verb])} t ON t.being = b.n"):
                    if n not in skip:
                        self.extra.setdefault(bid, set()).add(sid)
        rows = []
        for kind, r in self.L.kinds.items():
            r = r or {}
            line = r.get('line') or (self.L.level_line(r['level']) if r.get('level') else None)
            rows.append((kind, enc(r.get('nature')), enc(line), enc(r.get('rung'))))
        self._temp('u_kinds', ('kind', 'nature', 'line', 'rung'), rows, [('kind',)])

    def _bean_kind(self, x):
        """The SQL of the kind of the being an id (an SQL expression) names in the union, or NULL."""
        out = f"CASE WHEN EXISTS (SELECT 1 FROM u_git WHERE id = {x}) THEN (SELECT kind FROM u_git WHERE id = {x})"
        for K in self.K:
            out += (f" WHEN EXISTS (SELECT 1 FROM {K.schema}.being WHERE id = {x}) THEN "
                    f"(SELECT COALESCE(kind, 'document') FROM {K.schema}.being WHERE id = {x})")
        return out + " END"

    def _is_bean(self, x):
        """The SQL of whether an id (an SQL expression) names a bean of the union."""
        return '(' + ' OR '.join([f"EXISTS (SELECT 1 FROM u_git WHERE id = {x})"] +
                                 [f"EXISTS (SELECT 1 FROM {K.schema}.being WHERE id = {x})" for K in self.K]) + ')'

    # ------------------------------------------------------------------------------------------------ a verb's statements
    def statements(self, verb):
        """The union's statements of `verb`, as a view: git's (a temporary table) and each keeping's rows."""
        if verb in self._verbs:
            return self._verbs[verb]
        roles = list((self.L.verbs.get(verb) or {}).get('roles') or {}) + \
            list((self.L.verbs.get(verb) or {}).get('qualifiers') or {})
        for b in self.G.beans.values():
            for _i, v, r in b.items:
                if v == verb:
                    roles += [k for k in r if k not in roles]
        for k in ('id',) + tuple(sorted(self.L.beside)):
            if k not in roles:
                roles.append(k)
        for K in self.K:
            for k in (K.columns.get(verb) or {}):
                if k not in roles:
                    roles.append(k)
        cols = {r: (f"w{n}", f"n{n}", f"k{n}") for n, r in enumerate(roles)}
        names = list(SEQ) + ['_bean', '_verb', '_place', '_bkind'] + [c for r in roles for c in cols[r]]
        git = self._name('git')
        rows = []
        for k, b in enumerate(self.G.beans.values()):
            for i, v, r in b.items:
                if v != verb:
                    continue
                row = [0, k, 0, 0, i, b.id, verb, f"{b.id}[{i}] {verb}", b.kind]
                for role in roles:
                    x = _plain(r[role]) if role in r else None
                    row += [enc(x), enc(self._named(x, b)) if role in r else None, None]
                rows.append(row)
        self._temp(git, names, rows)
        parts = [f"SELECT {', '.join(q(c) for c in names)} FROM {q(git)}"]
        for k, K in enumerate(self.K):
            if verb not in K.verbs:
                continue
            parts.append(self._rows_of(k, K, verb, roles, cols))
        view = self._name('verb')
        self.db.execute(f"CREATE TEMP VIEW {q(view)} AS " + ' UNION ALL '.join(parts))
        self._made.append(('VIEW', view))
        st = Step(view, {r: cols[r] for r in roles}, SEQ, SEQ, 'statement', ('statement', verb))
        self._verbs[verb] = st
        return st

    def _named(self, x, b):
        """A filler of bean `b`'s statement as the being it names, in the union (core/engine.py `norm`): a text, a list
        of texts (None for an item that names none), or None."""
        ids = self.extra.get(b.id, ())

        def one(v):
            if v == 'self':
                return b.id
            if isinstance(v, str) and (v in b.ids or v in ids):
                return f"{b.id}#{v}"
            m = self.J.stored(v)
            if m:
                return f"{m[1]}#{m[2]}" if m[2] else m[1]
            return v if isinstance(v, str) else None
        if isinstance(x, list):
            return [one(v) for v in x]
        return one(x)

    def _rows_of(self, k, K, verb, roles, cols):
        """The SELECT of a keeping's rows of `verb`, in the columns of the union's relation: each being it keeps a
        filler as joined once, with the kind the union reads it as."""
        s, t = K.schema, K.tables[verb]
        earlier = self.K[:k]

        def union_kind(alias, gk):
            out = f"CASE WHEN {gk}.id IS NOT NULL THEN {gk}.kind"
            for E in earlier:
                out += (f" WHEN EXISTS (SELECT 1 FROM {E.schema}.being WHERE id = {alias}.id) THEN "
                        f"(SELECT COALESCE(kind, 'document') FROM {E.schema}.being WHERE id = {alias}.id)")
            return out + f" ELSE COALESCE({alias}.kind, 'document') END"
        bo1 = "CASE WHEN g.bo IS NOT NULL THEN 0"
        bo2 = "CASE WHEN g.bo IS NOT NULL THEN g.bo"
        for j, E in enumerate(earlier):
            bo1 += f" WHEN EXISTS (SELECT 1 FROM {E.schema}.being WHERE id = b.id) THEN {1 + j}"
            bo2 += (f" WHEN EXISTS (SELECT 1 FROM {E.schema}.being WHERE id = b.id) THEN "
                    f"(SELECT n FROM {E.schema}.being WHERE id = b.id)")
        bo1 += f" ELSE {1 + k} END"
        bo2 += " ELSE b.n END"
        sel = [bo1, bo2, str(1 + k), str(K.verbs.index(verb)), 't.n', 'b.id', f"'{verb}'", 'NULL',
               union_kind('b', 'g')]
        joins = [f"JOIN {s}.being b ON b.n = t.being", "LEFT JOIN u_git g ON g.id = b.id"]
        spec = K.columns.get(verb) or {}
        shapes = K.shapes.get(verb) or {}
        for role in roles:
            if role == 'id':
                sel += ['t.id', 't.id', 'NULL']
                continue
            if role in ('while', 'why', 'note'):
                sel += [f"t.{q('c_' + role)}"] * 2 + ['NULL']
                continue
            if role not in spec:
                sel += ['NULL', 'NULL', 'NULL']
                continue
            bc, tc = spec[role]
            sh = shapes.get(role) or []
            val = f"t.{q(tc)}"
            if bc:
                a, gk = f"r{len(joins)}", f"rg{len(joins)}"
                joins += [f"LEFT JOIN {s}.being {a} ON {a}.n = t.{q(bc)}", f"LEFT JOIN u_git {gk} ON {gk}.id = {a}.id"]
                kept, kind = f"COALESCE({a}.id, {val})", f"CASE WHEN {a}.id IS NOT NULL THEN {union_kind(a, gk)} END"
            else:
                kept, kind = val, 'NULL'
            bflag, sflag = int('being' in sh), int('statement' in sh)
            written = f"CASE WHEN typeof({kept}) = 'blob' THEN dm_written({kept}, b.id, {bflag}, {sflag})"
            if bflag:
                written += f" WHEN {kept} = b.id THEN 'self'"
            if sflag:
                written += (f" WHEN typeof({kept}) = 'text' AND substr({kept}, 1, length(b.id) + 1) = b.id || '#' "
                            f"THEN substr({kept}, length(b.id) + 2)")
            written += f" ELSE {kept} END"
            # AS THE ENGINE READS WHAT IS WRITTEN (core/engine.py `norm`): `self` the bean, an id of one of its own
            # statements that statement; a being kept as a being, and a list, as the store keeps them
            if sflag:
                own = f"typeof({val}) = 'text' AND substr({val}, 1, length(b.id) + 1) = b.id || '#'"
                local = self._local(K, 'b.id', 't.being', f"substr({val}, length(b.id) + 2)")
                named = (f"CASE WHEN {kept} IS NULL THEN NULL WHEN typeof({kept}) = 'blob' THEN {kept} "
                         f"WHEN {kept} = b.id AND {bflag} THEN b.id WHEN {own} AND NOT {local} "
                         f"THEN substr({val}, length(b.id) + 2) ELSE {kept} END")
            else:
                named = kept
            sel += [written, named, kind]
        where = ''
        skip = sorted(n for v, n in K.skip if v == verb)
        if skip:
            where = f" WHERE t.n NOT IN ({', '.join(str(n) for n in skip)})"
        return f"SELECT {', '.join(sel)} FROM {s}.{q(t)} t {' '.join(joins)}{where}"

    def _local(self, K, bean, being_n, val):
        """The SQL of whether `val` is the id of a statement of the bean `bean` in the union: git's, or a store's row."""
        self._git_ids()
        out = [f"EXISTS (SELECT 1 FROM u_ids WHERE bean = {bean} AND id = {val})"]
        for E in self.K:
            for verb in E.verbs:
                if E is K:
                    out.append(f"EXISTS (SELECT 1 FROM {E.schema}.{q(E.tables[verb])} x WHERE x.being = {being_n} "
                               f"AND x.id = {val})")
                else:
                    out.append(f"EXISTS (SELECT 1 FROM {E.schema}.{q(E.tables[verb])} x JOIN {E.schema}.being y "
                               f"ON y.n = x.being WHERE y.id = {bean} AND x.id = {val})")
        return '(' + ' OR '.join(out or ['0']) + ')'

    def _git_ids(self):
        """The ids of git's statements, by bean: a temporary table, made once."""
        if not getattr(self, '_ids', False):
            self._temp('u_ids', ('bean', 'id'), [(b.id, i) for b in self.G.beans.values() for i in b.ids],
                       [('bean', 'id')])
            self._ids = True

    def _eq(self, x, o):
        return 1 if self._rk._eq(dec(x), o) else 0

    def _fits(self, x, spec):
        """`fits` over the union: the value, or any item of a list, in the one form of the row `spec` names (core/law.py
        `Law.fits`, the function the reckoner calls)."""
        v = dec(x)
        return 1 if any(self.L.fits(json.loads(spec), y) for y in (v if isinstance(v, list) else [v])) else 0

    # ------------------------------------------------------------------------------------------------ the steps
    def refusals(self, reading, rule=None):
        """[(place, words)]: what a rule's reading refuses in the union, in the order of its `refuse` and of each step's
        members — the engine's refusals over the union read as beans. `NoSQL` where a step has no SQL form here. Its
        steps are kept under `rule`, for a later rule that takes one as an input (core 3.2)."""
        from core import lines
        reading = lines.worded(reading)
        _statement_columns_read(reading)
        self.env, self._uses = {}, {}
        if not hasattr(self, '_steps'):
            self._steps = {}
        for s in reading.get('steps') or []:
            for k in ('of', 'with', 'through', 'within'):
                if isinstance(s.get(k), str):
                    self._uses[s[k]] = self._uses.get(s[k], 0) + 1
        for d in reading.get('inputs') or []:
            o = d.get('origin') if isinstance(d, dict) and isinstance(d.get('origin'), dict) else {}
            if isinstance(d, dict) and isinstance(d.get('from'), dict):     # a step of an earlier rule, as compiled
                got = (self._steps.get(d['from'].get('rule')) or {}).get(d['from'].get('step'))
                if got is None:
                    raise NoSQL(f"input {d.get('name')}: the step {d['from'].get('step')} of the rule "
                                f"{d['from'].get('rule')} was not compiled before this one")
                self.env[d['name']] = got
                continue
            if not (o.get('act') == 'say' and o.get('by') == 'law'):
                raise NoSQL(f"input {d.get('name') if isinstance(d, dict) else d}: a rule's input is a table of the law")
            self.env[d['name']] = self._law_table(d['name'])
        for s in reading.get('steps') or []:
            fn = getattr(self, '_op_' + str(s.get('op')).replace('-', '_'), None)
            if fn is None:
                raise NoSQL(f"step {s.get('id')}: `{s.get('op')}` has no SQL form here")
            self.env[s['id']] = fn(s)
        if rule is not None:
            self._steps[rule] = dict(self.env)
        out = []
        for ref in reading.get('refuse') or []:
            st = self.env.get(ref.get('of'))
            for place, node in self._members(st):
                out.append((place, reckon.written(str(ref.get('message') or ''), reckon.Member(None, node, None))))
        return out

    def _arg(self, s, key):
        st = self.env.get(s.get(key))
        if st is None:
            raise NoSQL(f"step {s.get('id')}: `{key}: {s.get(key)}` names no earlier step")
        return st

    def _col(self, st, path, sid, named=False):
        """The column of `path` in step `st` (its value as the being it names, with `named`): a column, or NULL where
        no member holds the path. A path into a filler's own parts has no SQL form here."""
        if path in st.cols:
            return q(st.cols[path][1 if named else 0])
        segs = str(path).split('.')
        for k in range(1, len(segs)):
            if '.'.join(segs[:k]) in st.cols:
                raise NoSQL(f"step {sid}: `{path}` reads into a value's own parts")
        return 'NULL'

    def _view(self, sql, cols, keys, seq, kind, lineage, plain=False, table=False, foreign=()):
        name = self._name('step')
        self.db.execute(f"CREATE TEMP {'TABLE' if table else 'VIEW'} {q(name)} AS {sql}")
        self._made.append(('TABLE' if table else 'VIEW', name))
        return Step(name, cols, keys, seq, kind, lineage, plain, foreign)

    @staticmethod
    def _names(st):
        """Every column of a step's values: as written, as named, and the kind, each once."""
        return list(dict.fromkeys(c for v in st.cols.values() for c in v if c))

    def _carried(self, st):
        """The columns a step's members carry beside their values: their order, their statement's order and place."""
        out = list(st.keys)
        for c in (st.seq or []):
            if c not in out:
                out.append(c)
        if st.kind == 'statement':
            out += [c for c in CARRIED if c not in out]
        return out

    def _law_table(self, name):
        rows = reckon.law_table(self.L, name, self.G.manifest)
        paths = []
        for r in rows:
            paths += [k for k in r.node if k not in paths]
        cols = {p: (f"w{n}", f"w{n}", None) for n, p in enumerate(paths)}
        table = self._name('law')
        self._temp(table, ['_r'] + [cols[p][0] for p in paths],
                   [[k] + [enc(r.node.get(p)) for p in paths] for k, r in enumerate(rows)])
        return Step(table, cols, ['_r'], None, 'law', ('law', name))

    # select
    def _op_select(self, s):
        for k in s:
            if k not in ('id', 'op', 'of', 'entries', 'where'):
                raise NoSQL(f"step {s['id']}: `select` by `{k}` has no SQL form here")
        if 'of' in s:
            if s.get('entries'):
                raise NoSQL(f"step {s['id']}: the entries of a step's members have no SQL form here")
            base = self._arg(s, 'of')
        elif s.get('entries'):
            if not isinstance(s['entries'], str) or s['entries'] not in self.L.verbs:
                raise NoSQL(f"step {s['id']}: `entries: {s['entries']}` is not one verb")
            base = self.statements(s['entries'])
        else:
            base = self._beans()
        conds = [self._cond(base, c, s['id']) for c in s.get('where') or []]
        if not conds:
            return base
        cols = [q(c) for c in self._carried(base)] + [q(c) for c in self._names(base)]
        return self._view(f"SELECT {', '.join(dict.fromkeys(cols))} FROM {q(base.name)} WHERE {' AND '.join(conds)}",
                          base.cols, base.keys, base.seq, base.kind, base.lineage, table=self._shared(s['id']),
                          foreign=base.foreign)

    def _cond(self, st, c, sid):
        comp = next((k for k in c if k != 'path'), None)
        if comp not in WORD_SIGNS:
            raise NoSQL(f"step {sid}: the condition `{comp}` has no SQL form here")
        w = self._col(st, c['path'], sid)
        if comp == 'fits':
            try:
                self.L.fits_row(c[comp])              # a row the law has, as the reckoner holds it
            except ValueError as e:
                raise NoSQL(f"step {sid}: {e}") from None
            lit = "'" + json.dumps(c[comp], sort_keys=True).replace("'", "''") + "'"
            return f"({w} IS NOT NULL AND dm_fits({w}, {lit}) = 1)"
        if comp == 'exists':
            return f"{w} IS NOT NULL"
        if comp == 'absent':
            return f"{w} IS NULL"
        o = c[comp]
        if not isinstance(o, str):
            raise NoSQL(f"step {sid}: a condition's operand that is not one word has no SQL form here")
        lit = "'" + o.replace("'", "''") + "'"
        eq = f"(CASE typeof({w}) WHEN 'text' THEN {w} = {lit} WHEN 'blob' THEN dm_eq({w}, {lit}) ELSE 0 END)"
        return eq if comp == 'is' else f"({w} IS NULL OR NOT {eq})"

    def _beans(self):
        if getattr(self, '_beans_step', None) is None:
            parts = ["SELECT 0 AS _bo1, bo AS _bo2, id AS w0, kind AS w1 FROM u_git"]
            for k, K in enumerate(self.K):
                cond = [f"NOT EXISTS (SELECT 1 FROM u_git WHERE id = b.id)"] + \
                    [f"NOT EXISTS (SELECT 1 FROM {E.schema}.being WHERE id = b.id)" for E in self.K[:k]]
                parts.append(f"SELECT {1 + k}, b.n, b.id, COALESCE(b.kind, 'document') FROM {K.schema}.being b "
                             f"WHERE {' AND '.join(cond)}")
            self._beans_step = self._view(' UNION ALL '.join(parts), {'bean': ('w0', 'w0', None),
                                                                       'kind': ('w1', 'w1', None)},
                                          ['_bo1', '_bo2'], None, 'bean', ('bean',), plain=True)
        return self._beans_step

    # describe
    def _op_describe(self, s):
        st = self._arg(s, 'of')
        name, at = s['as'], s['at']
        if at not in st.cols:
            self._col(st, at, s['id'])
            return self._view(f"SELECT * FROM {q(st.name)} WHERE 0", st.cols, st.keys, st.seq, st.kind, st.lineage)
        if st.kind != 'statement' or any(at == p or at.startswith(p + '.') for p in st.foreign):
            raise NoSQL(f"step {s['id']}: a being described where no statement's bean says how `self` reads")
        w, nc, kc = st.cols[at]
        w, nc = q(w), q(nc)
        self._n += 1
        n = self._n
        dk, being, named, kind, known = f"_d{n}", f"b{n}", f"m{n}", f"k{n}", f"x{n}"
        mcols = ', '.join('m.' + q(c) for c in dict.fromkeys(self._carried(st) + self._names(st)))
        one = (f"SELECT {mcols}, 0 AS {dk}, m.{w} AS {being}, m.{nc} AS {named}, {f'm.{q(kc)}' if kc else 'NULL'} AS "
               f"{known} FROM {q(st.name)} m WHERE m.{w} IS NOT NULL AND (typeof(m.{w}) != 'blob' OR "
               f"json_type(CAST(m.{w} AS TEXT)) != 'array')")
        many = (f"SELECT {mcols}, j.key AS {dk}, CASE j.type WHEN 'text' THEN j.value WHEN 'null' THEN NULL "
                f"WHEN 'true' THEN CAST('true' AS BLOB) WHEN 'false' THEN CAST('false' AS BLOB) "
                f"WHEN 'object' THEN CAST(j.value AS BLOB) WHEN 'array' THEN CAST(j.value AS BLOB) "
                f"ELSE CAST(json_quote(j.value) AS BLOB) END AS {being}, "
                f"CASE WHEN typeof(m.{nc}) = 'blob' THEN json_extract(CAST(m.{nc} AS TEXT), '$[' || j.key || ']') END "
                f"AS {named}, NULL AS {known} FROM {q(st.name)} m, json_each(CASE WHEN typeof(m.{w}) = 'blob' AND "
                f"json_type(CAST(m.{w} AS TEXT)) = 'array' THEN CAST(m.{w} AS TEXT) ELSE '[]' END) j "
                f"WHERE typeof(m.{w}) = 'blob'")
        # THE KIND OF WHAT IS WRITTEN (core/engine.py `kind_of`): `self` its bean's, a being the store keeps there the
        # kind it keeps it as, any other name its bean's or its being's, `{someone: <kind>}` that kind
        kd = (f"CASE WHEN typeof(x.{being}) = 'blob' THEN json_extract(CAST(x.{being} AS TEXT), '$.someone') "
              f"WHEN x.{being} = 'self' THEN x._bkind WHEN x.{known} IS NOT NULL THEN x.{known} "
              f"WHEN typeof(x.{being}) = 'text' THEN {self._bean_kind('x.' + being)} END")
        sql = (f"SELECT y.*, k.nature AS nat{n}, k.line AS lin{n}, k.rung AS run{n}, NULL AS nul{n} FROM (SELECT x.*, {kd} AS {kind} "
               f"FROM ({one} UNION ALL {many}) x) y LEFT JOIN u_kinds k ON k.kind = y.{kind}")
        cols = {p: v for p, v in st.cols.items() if p != name and not p.startswith(name + '.')}
        cols[f"{name}.being"] = (being, named, kind)
        for key, c in (('kind', kind), ('nature', f"nat{n}"), ('line', f"lin{n}"), ('rung', f"run{n}")):
            cols[f"{name}.{key}"] = (c, c, None)
        for key in STATEMENT_COLUMNS:                # a being's member has none; a reading that reads one is NoSQL
            cols[f"{name}.{key}"] = (f"nul{n}", f"nul{n}", None)
        return self._view(sql, cols, st.keys + [dk], st.seq, st.kind, st.lineage + ('describe', s['id']),
                          table=self._shared(s['id']), foreign=st.foreign)

    # join, minus
    def _on(self, s, left, right, la='l', ra='r'):
        on = list(s['on'].items()) if isinstance(s.get('on'), dict) and s['on'] else None
        if not on:
            raise NoSQL(f"step {s['id']}: two sets are joined on equal columns")
        out = []
        for a, b in on:
            ca, cb = self._col(left, a, s['id'], named=True), self._col(right, b, s['id'], named=True)
            if 'NULL' in (ca, cb):
                return '0'
            out.append(f"typeof({la}.{ca}) = 'text' AND {la}.{ca} = {ra}.{cb}")
        return ' AND '.join(out)

    def _op_join(self, s):
        if 'of' not in s or 'series' in s:
            raise NoSQL(f"step {s['id']}: a join of two series has no SQL form here")
        left, right = self._arg(s, 'of'), self._arg(s, 'with')
        keep = s.get('keep') or 'both'
        cond = self._on(s, left, right)
        lcols = list(dict.fromkeys([q(c) for c in self._carried(left)] + [q(c) for c in self._names(left)]))
        if keep in ('matched', 'unmatched'):
            ex = 'EXISTS' if keep == 'matched' else 'NOT EXISTS'
            return self._view(f"SELECT {', '.join('l.' + c for c in lcols)} FROM {q(left.name)} l WHERE {ex} "
                              f"(SELECT 1 FROM {q(right.name)} r WHERE {cond})", left.cols, left.keys, left.seq,
                              left.kind, left.lineage, table=self._shared(s['id']), foreign=left.foreign)
        names = s.get('as')
        if not (isinstance(names, list) and len(names) == 2 and all(isinstance(x, str) for x in names)):
            raise NoSQL(f"step {s['id']}: a pair is read under two names")
        x, y = names
        self._n += 1
        n = self._n
        cols, sel = {}, [f"l.{c}" for c in lcols]
        for p, v in left.cols.items():
            cols[f"{x}.{p}"] = v
        rkeys = []
        for k, c in enumerate(right.keys):
            sel.append(f"r.{q(c)} AS {q(f'_j{n}_{k}')}")
            rkeys.append(f"_j{n}_{k}")
        done = {}
        for p, v in right.cols.items():
            for c in v:
                if c and c not in done:
                    done[c] = f"j{n}_{len(done)}"
                    sel.append(f"r.{q(c)} AS {q(done[c])}")
            cols[f"{y}.{p}"] = tuple(done[c] if c else None for c in v)
        return self._view(f"SELECT {', '.join(sel)} FROM {q(left.name)} l CROSS JOIN {q(right.name)} r ON {cond}", cols,
                          left.keys + rkeys, left.seq, left.kind, left.lineage + ('pair', s['id']),
                          table=self._shared(s['id']), foreign={f"{x}.{p}" for p in left.foreign} | {y})

    def _op_minus(self, s):
        a, b = self._arg(s, 'of'), self._arg(s, 'with')
        if a.lineage[:len(b.lineage)] != b.lineage[:len(a.lineage)] or a.keys != b.keys[:len(a.keys)]:
            raise NoSQL(f"step {s['id']}: `minus` of two sets of different members has no SQL form here")
        eq = ' AND '.join(f"l.{q(c)} IS r.{q(c)}" for c in a.keys)
        cols = list(dict.fromkeys([q(c) for c in self._carried(a)] + [q(c) for c in self._names(a)]))
        return self._view(f"SELECT {', '.join('l.' + c for c in cols)} FROM {q(a.name)} l WHERE NOT EXISTS "
                          f"(SELECT 1 FROM {q(b.name)} r WHERE {eq})", a.cols, a.keys, a.seq, a.kind, a.lineage,
                          table=self._shared(s['id']), foreign=a.foreign)

    def _shared(self, sid):
        """Whether a step is read by more than one later step: kept as a table, read once."""
        return self._uses.get(sid, 0) > 1

    # the walks
    def _edges(self, st, froms, tos, within, sid, bare=False):
        """The SQL of the edges a step's members make, from each being at a path of `froms` to each at one of `tos`
        (core/reckon.py `_edges`): each member's keys, the edge's place among its edges, and its two ends; `bare`, the
        two ends alone. With `within`, both ends among its beans."""
        if within is not None and within.kind != 'bean':
            raise NoSQL(f"step {sid}: `within` names a set of beings, the beans")

        def inside(x, kept=None):
            if within is None:
                return '1'
            if within.plain:        # a being a store keeps there is a bean of the union: read so, never looked up
                return f"({kept} IS NOT NULL OR {self._is_bean(x)})" if kept else self._is_bean(x)
            return f"EXISTS (SELECT 1 FROM {q(within.name)} w WHERE w.{q(within.cols['bean'][0])} = {x})"

        def items(path, j):
            c = f"m.{self._col(st, path, sid, named=True)}"
            kc = st.cols[path][2] if path in st.cols else None
            single = ('', f"typeof({c}) = 'text'", '0', c, f"m.{q(kc)}" if kc else None)
            listed = (f", json_each(CASE WHEN typeof({c}) = 'blob' AND json_type(CAST({c} AS TEXT)) = 'array' THEN "
                      f"CAST({c} AS TEXT) ELSE '[]' END) {j}", f"typeof({c}) = 'blob' AND {j}.type = 'text'",
                      f"{j}.key", f"{j}.value", None)
            return (single, listed)
        keys = [] if bare else [f"m.{q(c)} AS {q(c)}" for c in st.keys]
        parts = []
        for fi, f in enumerate(froms):
            if self._col(st, f, sid, named=True) == 'NULL':
                continue
            for ti, t in enumerate(tos):
                if self._col(st, t, sid, named=True) == 'NULL':
                    continue
                for fa, wa, ka, va, xa in items(f, 'ja'):
                    for fc, wc, kc, vc, xc in items(t, 'jc'):
                        order = [] if bare else [f"{fi} AS _ef", f"{ka} AS _ea", f"{ti} AS _et", f"{kc} AS _ec"]
                        parts.append(f"SELECT {', '.join(keys + order + [f'{va} AS a', f'{vc} AS c'])} "
                                     f"FROM {q(st.name)} m{fa}{fc} WHERE {wa} AND {wc} AND {inside(va, xa)} AND "
                                     f"{inside(vc, xc)}")
        if not parts:
            none = [] if bare else [f"NULL AS {q(c)}" for c in st.keys] + ['NULL AS _ef', 'NULL AS _ea', 'NULL AS _et',
                                                                            'NULL AS _ec']
            return f"SELECT {', '.join(none + ['NULL AS a', 'NULL AS c'])} WHERE 0"
        return ' UNION ALL '.join(parts)

    def _op_cycle(self, s):
        of = self._arg(s, 'of')
        more = self._arg(s, 'with') if s.get('with') else None
        within = self._arg(s, 'within') if s.get('within') else None
        froms, tos = reckon._paths(s['from']), reckon._paths(s['to'])
        self._n += 1
        n = self._n
        me, e = f"u_me_{n}", f"u_e_{n}"
        self.db.execute(f"CREATE TEMP TABLE {me} AS {self._edges(of, froms, tos, within, s['id'])}")
        self._made.append(('TABLE', me))
        both = f"SELECT a, c FROM {me}"
        if more is not None:
            both += ' UNION ALL ' + self._edges(more, froms, tos, within, s['id'], bare=True)
        self.db.execute(f"CREATE TEMP TABLE {e} AS SELECT DISTINCT a, c FROM ({both})")
        self._made.append(('TABLE', e))
        self.db.execute(f"CREATE INDEX {e}_a ON {e} (a)")
        self.db.execute(f"CREATE INDEX {e}_c ON {e} (c)")
        while True:          # WHAT CAN LIE ON A CYCLE: an edge whose start is reached and whose end leads on, again
            cur = self.db.execute(f"DELETE FROM {e} WHERE NOT EXISTS (SELECT 1 FROM {e} x WHERE x.c = {e}.a) "
                                  f"OR NOT EXISTS (SELECT 1 FROM {e} x WHERE x.a = {e}.c)")
            if cur.rowcount == 0:
                break
        graph = {}
        for a, c in self.db.execute(f"SELECT a, c FROM {e}"):
            graph.setdefault(a, set()).add(c)
        order = ', '.join([q(c) for c in of.keys] + ['_ef', '_ea', '_et', '_ec'])
        hits = self.db.execute(f"SELECT {', '.join([q(c) for c in of.keys] + ['a', 'c'])} FROM {me} WHERE EXISTS "
                               f"(SELECT 1 FROM {e} WHERE {e}.a = {me}.a AND {e}.c = {me}.c) ORDER BY {order}").fetchall()
        k = len(of.keys)
        found = []
        for h in hits:
            a, c = h[k], h[k + 1]
            path = [a] if a == c else _reach.way(c, a, lambda x: sorted(graph.get(x, ())))
            if path:
                found.append((tuple(h[:k]), a, c, [c] + path[:-1], [a, c] + path[:-1] + ([a] if a != c else [])))
        return self._walked(of, found, s['id'])

    def _walked(self, of, found, sid):
        """The members of `of` a cycle found, each with its start, next, way and loop: a table, in their order."""
        new = ('start', 'next', 'way', 'loop')
        cols = {p: v for p, v in of.cols.items() if p.split('.')[0] not in new}
        carried = self._carried(of)
        vals = list(dict.fromkeys(c for v in cols.values() for c in v if c))
        self._n += 1
        n = self._n
        got = {}
        if found:
            want = f"u_want_{n}"
            self._temp(want, list(of.keys), sorted({f[0] for f in found}, key=_sortable))
            on = ' AND '.join(f"m.{q(c)} IS w.{q(c)}" for c in of.keys)
            take = list(dict.fromkeys(carried + vals))
            for r in self.db.execute(f"SELECT {', '.join('m.' + q(c) for c in list(of.keys) + take)} FROM "
                                     f"{q(of.name)} m JOIN {q(want)} w ON {on}"):
                got[tuple(r[:len(of.keys)])] = dict(zip(take, r[len(of.keys):]))
        take = list(dict.fromkeys(carried + vals))
        rows = []
        for key, a, c, way, loop in found:
            r = got.get(key)
            if r is not None:
                rows.append([len(rows)] + [r[x] for x in take] + [a, c, enc(way), enc(loop)])
        name = self._name('cycle')
        self._temp(name, [f"_c{n}"] + take + [f"c{n}_{p}" for p in new], rows)
        for p in new:
            cols[p] = (f"c{n}_{p}", f"c{n}_{p}", None)
        return Step(name, cols, [f"_c{n}"], of.seq, of.kind, of.lineage + ('cycle', sid), foreign=of.foreign)

    def _op_reach(self, s):
        rel, of = self._arg(s, 'through'), self._arg(s, 'of')
        froms, tos = reckon._paths(s['from']), reckon._paths(s['to'])
        graph = {}
        for a, c in self.db.execute(self._edges(rel, froms, tos, None, s['id'], bare=True)):
            graph.setdefault(a, set()).add(c)
        at = self._col(of, s['at'], s['id'], named=True)
        starts, seen = [], set()
        if at != 'NULL':
            keys = ', '.join('m.' + q(c) for c in of.keys)
            sql = (f"SELECT v FROM (SELECT {keys}, 0 AS _k, m.{at} AS v FROM {q(of.name)} m WHERE typeof(m.{at}) = "
                   f"'text' UNION ALL SELECT {keys}, j.key, j.value FROM {q(of.name)} m, json_each(CASE WHEN "
                   f"typeof(m.{at}) = 'blob' AND json_type(CAST(m.{at} AS TEXT)) = 'array' THEN CAST(m.{at} AS TEXT) "
                   f"ELSE '[]' END) j WHERE j.type = 'text') ORDER BY {', '.join([q(c) for c in of.keys] + ['_k'])}")
            for (v,) in self.db.execute(sql):
                if v not in seen:
                    seen.add(v)
                    starts.append(v)
        rows = []
        for st in starts:
            rows.append([len(rows), st, st, enc([])])
            r = _reach.Reach(st, lambda x: sorted(graph.get(x, ())))
            for x, _via in r:
                rows.append([len(rows), st, x, enc(r.path(x))])
        name = self._name('reach')
        self._temp(name, ['_r', 'start', 'reached', 'way'], rows)
        return Step(name, {'start': ('start', 'start'), 'reached': ('reached', 'reached'), 'way': ('way', 'way')},
                    ['_r'], None, 'walk', ('reach', s['id']))

    # first, last
    def _op_first(self, s, last=False):
        st = self._arg(s, 'of')
        gs = []
        for p in reckon._paths(s['by']):
            c = self._col(st, p, s['id'], named=True)
            gs.append('NULL' if c == 'NULL' else f"CASE WHEN typeof(m.{c}) = 'text' THEN m.{c} END")
        self._n += 1
        n = self._n
        g = [f"g{n}_{k}" for k in range(len(gs))]
        keys = [q(c) for c in st.keys]
        part = ', '.join(g) or '1'
        group = (', '.join(f"({x} IS NOT NULL), COALESCE({x}, '')" for x in g) or '1') \
            if s.get('groups') == 'values' else '_gp'
        way = ' DESC' if last else ''
        within = ', '.join(c + way for c in [q(x) for x in (st.seq or [])] + keys)
        keep = ', '.join(q(c) for c in dict.fromkeys(self._carried(st) + self._names(st)))
        grouped = ', '.join(f'{x} AS {gn}' for x, gn in zip(gs, g))
        sql = (f"SELECT ROW_NUMBER() OVER (ORDER BY {group}) - 1 AS _g{n}, {keep} FROM ("
               f"SELECT y.*, ROW_NUMBER() OVER (PARTITION BY {part} ORDER BY {within}) AS _rn, "
               f"MIN(_pos) OVER (PARTITION BY {part}) AS _gp FROM ("
               f"SELECT m.*, {grouped + ', ' if grouped else ''}"
               f"ROW_NUMBER() OVER (ORDER BY {', '.join('m.' + k for k in keys)}) AS _pos FROM {q(st.name)} m) y) "
               f"WHERE _rn = 1")
        return self._view(sql, st.cols, [f"_g{n}"], st.seq, st.kind, st.lineage + ('first', s['id']), table=True,
                          foreign=st.foreign)

    def _op_last(self, s):
        return self._op_first(s, last=True)

    # ------------------------------------------------------------------------------------------------ the refusals
    def _members(self, st):
        """(place, node) of each member of a step, in its order: the place of its statement, and its values."""
        carried = self._carried(st)
        paths = list(st.cols)
        cols = list(dict.fromkeys(carried + [st.cols[p][0] for p in paths]))
        at = {c: k for k, c in enumerate(cols)}
        out = []
        for r in self.db.execute(f"SELECT {', '.join(q(c) for c in cols)} FROM {q(st.name)} "
                                 f"ORDER BY {', '.join(q(c) for c in st.keys)}").fetchall():
            node = {}
            for p in paths:
                segs = p.split('.')
                cur = node
                for x in segs[:-1]:
                    if not isinstance(cur.get(x), dict):
                        cur[x] = {}
                    cur = cur[x]
                cur[segs[-1]] = dec(r[at[st.cols[p][0]]])
            place = None
            if st.kind == 'statement':
                src = r[at['_src']]
                place = r[at['_place']] if src == 0 else self._place(src, r[at['_bean']], r[at['_verb']], r[at['_i']])
            out.append((place, node))
        return out

    def _place(self, src, bean, verb, n):
        """`<bean>[<i>] <verb>`: where a store's row stands among its bean's statements in the union."""
        return f"{bean}[{self.index(src, bean, verb, n)}] {verb}"

    def index(self, src, bean, verb, n):
        """Where the row `n` of `verb` a keeping (`src`, 1 and its place) keeps of `bean` stands among the bean's
        statements in the union: after git's own, after an earlier keeping's, by verb, then as put."""
        got = self.db.execute("SELECT nst FROM u_git WHERE id = ?", (bean,)).fetchone()
        i = got[0] if got else 0
        for j, K in enumerate(self.K[:src]):
            b = self.db.execute(f"SELECT n FROM {K.schema}.being WHERE id = ?", (bean,)).fetchone()
            if not b:
                continue
            for v in K.verbs:
                last = j == src - 1 and v == verb
                rows = self.db.execute(f"SELECT n FROM {K.schema}.{q(K.tables[v])} WHERE being = ?"
                                       + (" AND n < ?" if last else ''), (b[0], n) if last else (b[0],)).fetchall()
                i += sum(1 for (x,) in rows if (v, x) not in K.skip)
                if last:
                    break
        return i


def _statement_columns_read(reading):
    """NoSQL where a rule's reading describes a statement (core 3.2, I.1): a `describe` with no `at`, or a path, a
    condition, a key or a refusal's words reading a statement's column of a description. Their SQL form is not written
    yet, so the rule is named as not judged at that size rather than judged without them."""
    steps = [s for s in reading.get('steps') or [] if isinstance(s, dict)]
    names = {s.get('as') for s in steps if s.get('op') == 'describe' and isinstance(s.get('as'), str)}
    for s in steps:
        if s.get('op') == 'describe' and 'at' not in s:
            raise NoSQL(f"step {s.get('id')}: `describe` of the member itself, a statement, has no SQL form here")
    texts = [str(r.get('message') or '') for r in reading.get('refuse') or [] if isinstance(r, dict)]
    for s in steps:
        for k, v in s.items():
            if k in ('id', 'op'):
                continue
            texts += [json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v]
    for t in texts:
        for m in re.finditer(r'([a-z0-9_-]+)\.(' + '|'.join(STATEMENT_COLUMNS) + r')\b', t):
            if m.group(1) in names:
                raise NoSQL(f"`{m.group(0)}`: a statement's column of a description has no SQL form here")


def _sortable(key):
    return tuple((x is None, '' if x is None else str(type(x)), x if x is not None else 0) for x in key)


POINTER = re.compile(r'^store:([a-z][a-z0-9-]*):([a-z0-9][a-z0-9_-]*)(?:#([a-z0-9][a-z0-9_-]*))?$')


def _plain(x):
    """A filler with every pointer read as the plain id it names (bin/store.py `_plainid`): in the union every being is
    one id."""
    if isinstance(x, list):
        return [_plain(v) for v in x]
    if isinstance(x, dict):
        return {k: _plain(v) for k, v in x.items()}
    m = POINTER.match(x) if isinstance(x, str) else None
    return (f"{m.group(2)}#{m.group(3)}" if m.group(3) else m.group(2)) if m else x


def _written(blob, bean, being, statement):
    """A list a store keeps, as its bean writes it (bin/store.py `denormalize`): the being itself `self`, a statement
    of its own being by its id."""
    try:
        v = json.loads(blob.decode('utf-8') if isinstance(blob, bytes) else blob)
    except ValueError:
        return blob
    if not isinstance(v, list):
        return blob

    def one(x):
        if not isinstance(x, str):
            return x
        if being and x == bean:
            return 'self'
        if statement and x.startswith(bean + '#'):
            return x[len(bean) + 1:]
        return x
    return enc([one(x) for x in v])
