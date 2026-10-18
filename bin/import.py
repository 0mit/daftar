#!/usr/bin/env python3
"""import — records of another system brought in as statements, through a crosswalk of the law, known by one act.

    python3 bin/import.py <crosswalk> <source> [<source> ...]     # the statements, and the account: nothing written
    python3 bin/import.py <crosswalk> <source> --into store:<name> [--path <file>]   # kept in a store this host keeps
    python3 bin/import.py <crosswalk> <source> --into bean --write # written into the beans, for your save
    python3 bin/import.py file-tree <index.sqlite> --volume <id> --carrier <disk> --into store:<name>   # a reader's rows
    python3 bin/import.py --list                                  # the crosswalks that say how their records come
    python3 bin/import.py daftar <bean> ... --into store:<name>   # the garden's own statements: a bean into a store
    python3 bin/import.py daftar rows.jsonl --into store:<name> --act <ref>   # a store's own rows (bin/store.py put)
    python3 bin/import.py proposal <file> [--take [--as-test]]    # another garden's proposal: read, or taken

(`python` on Windows.) Also `--format <format>` where a crosswalk takes several, `--from <layer>` (`world`, the
default for a reading; `words` for a document a person gave), `--act '<json>'` for the roles of the act (`in`, the
being it is kept in; `id`; and the verb's own roles), `--root <dir>` with `--volume` for the files `exiftool` read, and
`--named [<field>=]<namespace>` for a field read `named: given`: the namespace of the garden's own to look it up in.

ONE MACHINERY (MODEL.md, Imports and exports). A source is read in its FORMAT (core/law/formats.yaml), its records given
by a READER where the format alone cannot say them, each record written into the statements its CROSSWALK says
(core/law/crosswalks.yaml, read both ways by core/crosswalk.py), every statement known by the ACT the crosswalk names
(`read`, `say`, `derive`, `make`: one for all an import keeps, or one a record), and kept where it is told: a store, or
a bean. The flow law is asked for the pass before anything is written, and a pass it does not grant writes nothing.

THE SAME SOURCE AGAIN changes nothing: a row is named by its form, so a statement put twice is one row, and gains the
act of the second reading where it is another. A record a later reading does not hold keeps its rows and the act that
knew them: "not seen since" is a reading, never stored. Where an import wrote `unknown` in a role it can fill now, the
statement it wrote is taken out by `gone`, its reason the statement that fills it.

SET-WISE, INSIDE THE STORE'S ENGINE. Where a reader has a set form (the `file-tree` reader's, over a listing kept as a
database) and each crosswalk of its models compiles, the import is one INSERT … SELECT a statement, over the records
as the store's own temporary tables: the same rows, named by the same form, known by the same act, as record by record
— and many times faster, since only a digest and a name in bytes are left to Python. A large import into a store makes
the relations' indexes once, after every row is in (`Store.loading`).

THE ACCOUNT. Every value of every record is carried, or listed as not carried with why, and counted by its field when
there are many: nothing is passed over in silence. A crosswalk marked `whole` fails on any value it lists.

DAFTAR'S OWN FORMS need no crossing, and their own tools keep them: `daftar` (a bean's statements, a store's rows) is
bin/store.py's import and put, `proposal` is bin/propose.py's read and take. This door hands each to its tool.
"""
import collections
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr

from core import formats  # noqa: E402
from core.crosswalk import Carry, Refused  # noqa: E402

THROUGH = {'read': ('record',), 'say': ('record', 'say'), 'derive': ('derive',), 'make': ('make', 'edit')}


def now():
    t = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    return t[:-2] + ':' + t[-2:]


class Account:
    """What an import carried and what it did not: each value listed by the record it is in and its field, and counted
    by field once the records are many."""

    def __init__(self, keep_each=200):
        self.records, self.carried, self.keep_each = 0, 0, keep_each
        self.each, self.count, self.notes, self.unnamed = [], collections.Counter(), collections.Counter(), {}

    def missed(self, at, field, why):
        self.count[(field, why)] += 1
        if len(self.each) < self.keep_each:
            self.each.append((at, field, why))

    def note(self, field, why):
        self.notes[(field, why)] += 1

    def lines(self, each=None):
        each = self.records <= 20 if each is None else each
        out = [f"not carried: {at}: {f}" + (f" ({w})" if w and w != 'no field of the crosswalk reads it' else '')
               for at, f, w in self.each] if each else \
            [f"not carried: {f} × {n}" + (f" ({w})" if w and w != 'no field of the crosswalk reads it' else '')
             for (f, w), n in sorted(self.count.items(), key=lambda x: (-x[1], x[0]))]
        out += [f"note: {f} × {n}: {w}" for (f, w), n in sorted(self.notes.items(), key=lambda x: (-x[1], x[0]))]
        return out


class Import:
    """One import: its crosswalks (one, or every one a reader's models are crossed by), where it keeps what it writes,
    and the acts that know it. As a library: `Import(root, 'file-tree', keep=store, reader_args={...}).source(path)`,
    then `.done()`; `.record(model, rec)` keeps one record (a copier's, one at a time)."""

    def __init__(self, root=ROOT, crosswalk=None, *, keep=None, store=None, acts=None, reader_args=None, fmt=None,
                 source_layer=None, judge_every=10000, law=None, write=False, named=None):
        from core.check import garden_law
        self.root = root
        self.law = law or garden_law(root, root if os.path.isfile(os.path.join(root, 'core', 'law', 'core.yaml')) else None)
        self.reader = None
        if crosswalk in self.law.readers:
            self.reader = crosswalk
            names = [n for n, r in self.law.crosswalks.items() if str(r.get('reader')) == crosswalk]
            systems = {(str(r.get('system')), str(r.get('series'))) for n, r in self.law.crosswalks.items() if n in names}
            models = [str(m) for m in (self.law.readers[crosswalk].get('models') or [])]
            names += [n for n, r in self.law.crosswalks.items() if n not in names and str(r.get('model')) in models
                      and (str(r.get('system')), str(r.get('series'))) in systems]   # each model it gives, crossed
        elif crosswalk in self.law.crosswalks:
            names = [crosswalk]
            self.reader = self.law.crosswalks[crosswalk].get('reader')
        else:
            raise Refused(f"`{crosswalk}` is no crosswalk and no reader of the law (`--list` names them)")
        self.store, self.keep, self.write = store, keep or ('store' if store is not None else 'bean'), write
        schemes = self._schemes()
        self.carry = {}
        for n in names:
            c = Carry(self.law, n, names=self.named, named_as=None, schemes=schemes, given_names=named)
            self.carry[str(c.row.get('model'))] = c
        self.fmt, self.reader_args = fmt, dict(reader_args or {})
        self.acts, self.made = dict(acts or {}), {}       # verb -> roles given; (verb, source) -> the act's ref
        self.layer = source_layer
        self.judge_every = judge_every
        self.account = Account()
        self.beans_out = collections.OrderedDict()       # being -> [statements], for a bean
        self.reads = []                                   # the reading acts of this import, a derive's `from`
        self._names = {}
        self._garden = None
        self._known_folders = set()
        self.unknown_filled = 0
        self._source = None                               # (key, the roles of its reading act) of the source being read
        self.later = collections.OrderedDict()            # what a `derive` knows, kept once every reading is in
        self.already = []                                 # the sources imported already, each by its act
        self._takes_being = {}
        self._later_tables = set()                        # the set-wise records a derive knows, kept at done()

    # -------------------------------------------------------------------------------------------- what the law says
    def _schemes(self):
        try:
            import knowledge as dmknowledge
            return list(dmknowledge.Knowledge(self.root).schemes.values())
        except Exception:                      # noqa: BLE001 — a garden with no knowledge reads no coding
            return []

    @property
    def garden(self):
        if self._garden is None:
            from core import engine
            self._garden = engine.Garden.read(self.root)
        return self._garden

    def named(self, namespace, value):
        """The being `namespace` names by `value`, in git or in the store: None where none is."""
        key = (namespace, value)
        if key in self._names:
            return self._names[key]
        hit = None
        if not self._names.get(('*', namespace)):
            for b in self.garden.beans.values():
                for _i, v, r in b.items:
                    if v == 'name' and r.get('by') == namespace and r.get('of') in ('self', b.id) and 'held' not in r:
                        self._names[(namespace, str(r.get('as')))] = b.id
            self._names[('*', namespace)] = True
            hit = self._names.get(key)
        if hit is None and self.store is not None and 'name' in self.store.verbs():
            r = self.store.db.execute("SELECT (SELECT id FROM being WHERE n = b_of) FROM v_name WHERE t_by = ? AND "
                                      "t_as = ? LIMIT 1", (namespace, value)).fetchone()
            hit = r[0] if r else None
        self._names[key] = hit
        return hit

    def flow(self, verb):
        """The flow row that grants this import's pass, or Refused: from the source's layer to the keeping's, through
        the method its act is made by, as that act."""
        frm = self.layer or ('words' if verb == 'say' else 'store' if verb == 'derive' and self.store else 'world')
        to = 'store' if self.keep == 'store' else 'estate'
        for through in THROUGH.get(verb, (verb,)):
            ok, grant, rows = self.law.decide(frm, to, through, verb)
            if ok:
                return rows[0] if rows else grant
        raise Refused(f"the flow law grants no pass from {frm} to {to} for statements known by `{verb}` "
                      f"(core/law/flows.yaml): nothing is written")

    # -------------------------------------------------------------------------------------------- the acts
    def act(self, verb):
        """The ref `<being>#<id>` of the act of `verb` for this import, put first where it is kept: a reading's one a
        source (the roles the run gives that source), a derive's one for the import, from every reading of it."""
        reading = verb in ('read', 'say')
        key = (verb, self._source[0] if reading and self._source else None)
        if key in self.made:
            return self.made[key]
        self.flow(verb)
        given = dict(self.acts.get(verb) or {})
        if reading and self._source:
            given.update(self._source[1] or {})
        where = given.pop('in', None)
        roles = {k: v for k, v in given.items()}
        if verb == 'read':
            roles.setdefault('by', self._host())
        elif verb == 'derive':
            roles.setdefault('by', self._host())
            roles.setdefault('from', list(self.reads))
        elif verb == 'make':
            roles.setdefault('by', self._host())
        roles.setdefault('at', now())
        where = where or roles.get('from') if verb == 'read' and isinstance(roles.get('from'), str) else where
        where = where or (roles.get('by') if verb != 'derive' else None) or self._host()
        if self.keep == 'store':
            import store as dmstore
            sid = roles.get('id') or dmstore.mint(verb, self.store.normalize(where, verb, roles))
            if self.store.statement(where, sid) is not None:
                self.already.append((key[1], f"{where}#{sid}"))
            sid = self.store.put(where, verb, roles)
            ref = f"{where}#{sid}"
        else:
            ref = None
            self.beans_out.setdefault('__acts__', []).append((where, {verb: roles}))
        self.made[key] = ref
        if verb in ('read', 'say') and ref:
            self.reads.append(ref)
        return ref

    def _host(self):
        if not hasattr(self, '_hid'):
            try:
                import where as dmwhere
                import held as dmheld
                self._hid = dmwhere.this_host(dmheld._terms(self.root))[0]
            except Exception:                  # noqa: BLE001 — a garden that records no host here
                self._hid = None
        return self._hid or 'unknown'

    # -------------------------------------------------------------------------------------------- records
    def records_of(self, path, fmt=None):
        """The records of a source as its crosswalk's models: through its reader, or read in its format."""
        rows = list(self.carry.values())
        allowed = sorted({str(f) for c in rows for f in (c.row.get('format') if isinstance(c.row.get('format'), list)
                                                          else [c.row.get('format')])})
        fmt = fmt or self.fmt or formats.format_of(path, allowed)
        if fmt not in allowed:
            raise Refused(f"{path}: the crosswalk reads {', '.join(allowed)}, not {fmt}")
        spec = next((c.row.get('records') for c in rows if c.row.get('records')), None)
        if self.reader == 'file-tree' and fmt == 'sqlite' and not spec:
            spec = {'table': 'entry'}
        if self.reader == 'copies' and not spec:
            spec = {'table': 'copied', 'order': 'at', 'live': True}
        raw = formats.read(fmt, path, spec)
        if not self.reader:
            model = next(iter(self.carry))
            for rec in raw:
                rec.model = model
                yield rec
            return
        from core import readers
        fn = readers.IMPORTED.get(self.reader)
        if fn is None:
            raise Refused(f"the reader `{self.reader}` is not in this release")
        takes = TAKES.get(self.reader)
        if takes:
            raw = self._counted(raw, takes)
        args = dict(self.reader_args)
        if self.reader == 'copies':
            args.setdefault('known', self._known_folders)
            args.setdefault('ref', self._ref)
        if self.reader == 'exiftool':
            args.setdefault('find', self._find)
        yield from fn(raw, **args)

    def _counted(self, raw, takes):
        """The raw records, each value a reader does not take counted in the account as not carried."""
        for rec in raw:
            for k in rec:
                if k not in takes:
                    self.account.count[(k, 'not read by the reader')] += 1
            yield rec

    def _ref(self, verb, being, roles):
        import store as dmstore
        return f"{being}#{dmstore.mint(verb, roles)}"

    def _find(self, holder, name):
        """The content a folder holds under a name, in the store this import keeps into."""
        if self.store is None or 'hold' not in self.store.verbs():
            return None
        r = self.store.db.execute("SELECT (SELECT id FROM being WHERE n = h.b_of) FROM v_hold h WHERE h.being = "
                                  "(SELECT n FROM being WHERE id = ?) AND h.t_as = ? LIMIT 1", (holder, name)).fetchone()
        return r[0] if r else None

    # -------------------------------------------------------------------------------------------- keeping
    def source(self, path, fmt=None, act=None, **reader_args):
        """Import one source whole: `act` the roles of its reading (its `in`, `id`, `from`, `through`, `at`), else the
        import's. A source whose reading is kept already, in the same form, was imported: it is said, and skipped."""
        saved = dict(self.reader_args)
        self.reader_args.update(reader_args)
        self._source = (path, act)
        try:
            if act is not None and self.keep == 'store':
                verbs = {(c.row.get('act') or {}).get('verb') for c in self.carry.values()} & {'read', 'say'}
                for verb in verbs:
                    n = len(self.already)
                    self.act(verb)
                    if len(self.already) > n:
                        return False
            if self._setwise(path, fmt):                   # the crosswalk run set-wise, inside the store's engine
                return True
            groups = collections.OrderedDict()             # (verb, act ref, being roles) -> [(being, roles)]
            beings = {}
            for rec in self.records_of(path, fmt):
                self.record(rec.model, rec, groups=groups, beings=beings)
            self._flush(groups, beings)
            return True
        finally:
            self.reader_args = saved
            self._source = None

    # -------------------------------------------------------------------------------------------- set-wise
    # A CROSSWALK RUN INSIDE THE STORE'S ENGINE. Where the reader has a set form (core/readers.py SETWISE) and each row
    # of its models compiles — plain fields, `escaped`, a unit, `with`, filters, `self` — the rows are written by one
    # INSERT … SELECT a statement of a row, over the reader's records as temporary tables: the same statements, named
    # by the same form, known by the same act, as the record-by-record path writes; a record with an empty role goes
    # that path. Python is called only for what SQL has not: a digest, a name in bytes written `escaped`.
    def _compile(self, c):
        """[group] of a row's statements, each {verb, filters, roles: {role: spec}}, or None where the row does not
        compile. A spec is ('col', column, conversion), ('const', value), ('unit', column, conversion, unit)."""
        from core import formats
        if c.compose or c.given or c.row.get('self'):
            return None
        groups = {}
        cols_of = {}
        for fname, spec, kind, frm, _plain, deep in c._compiled():
            conv = formats.conversion(spec.get('as'))[0]
            if kind not in ('bean', 'role', 'path') or deep or conv not in (None, 'escaped') or spec.get('map') \
                    or spec.get('drop') is not None:
                return None
            cols_of[fname] = conv
        for fname, spec, kind, frm, _plain, _deep in c._compiled():
            if kind == 'bean':
                continue
            conv = cols_of[fname]
            val = ('unit', fname, conv, str(spec['unit'])) if spec.get('unit') is not None else ('col', fname, conv)
            if kind == 'role':
                if '.' in frm:
                    return None
                g = groups.setdefault((c.verb, tuple(sorted(c.filters.items()))), {'verb': c.verb, 'filters': dict(c.filters),
                                                                                  'roles': {}})
                g['roles'][frm] = val
                continue
            verb, key, one, role = c._paths[fname]
            g = groups.setdefault(key, {'verb': verb, 'filters': dict(one), 'roles': {}})
            g['roles'][role] = val
            for r2, f2 in (spec.get('with') or {}).items():
                if f2 not in cols_of:
                    return None
                g['roles'][r2] = ('col', f2, cols_of[f2])
        return list(groups.values())

    def _setwise(self, path, fmt=None):
        from core import readers
        S = self.store
        form = readers.SETWISE.get(self.reader) if self.reader else None
        if self.keep != 'store' or form is None or str(path).endswith(('.tsv', '.csv', '.jsonl')) or \
                (fmt and fmt != 'sqlite'):
            return False
        plans = {m: self._compile(c) for m, c in self.carry.items()}
        if any(p is None for p in plans.values()):
            return False
        db = S.db
        db.create_function('io_esc', 1, lambda b: formats.escape(b) if b is not None else None, deterministic=True)
        db.create_function('io_mint', 2, lambda verb, j: self._mint(verb, j), deterministic=True)
        import store as dmstore
        db.execute("ATTACH ? AS io_src", (dmstore._uri(path, 'ro'),))
        try:
            tables, missed = form(db, 'io_src', **self.reader_args)
            self._tables = tables
            for col, n in missed.items():
                self.account.count[(col, 'not read by the reader')] += n
            for model, table in tables.items():
                c = self.carry.get(model)
                if c is None:
                    continue
                verb = (c.row.get('act') or {}).get('verb')
                if model == 'content' and verb == 'derive':
                    self._later_tables.add((model, table))         # known once every reading is in (done)
                    continue
                self._write_table(c, plans[model], table, self.act(verb) if verb else None)
        finally:
            db.execute("DETACH io_src")
        return True

    def _mint(self, verb, j):
        """A statement's id from its form as SQLite's json_object writes it, keys sorted: where nothing in it is escaped,
        that is the canonical form byte for byte (MERGE.md 1); anything else is read back and written canonically."""
        import hashlib
        import store as dmstore
        if '\\' not in j:
            form = '{' + json.dumps(verb) + ':' + j + '}'
            return f"{verb}-{hashlib.sha256(form.encode('utf-8')).hexdigest()[:16]}"
        return dmstore.mint(verb, json.loads(j))

    @staticmethod
    def _raw(spec):
        """(the SQL of a role's value as text, its arguments): a column of the records, read through its conversion, or a
        value given."""
        if spec[0] == 'const':
            return '?', [spec[1]]
        col = f't."{spec[1]}"'
        return (f'io_esc({col})' if spec[2] == 'escaped' else col), []

    def _write_table(self, c, groups, table, ref):
        """Each group of a row's statements written from the table of its records: the beings first, then one
        INSERT … SELECT a group, known by `ref`."""
        S, db = self.store, self.store.db
        bcol = c._bean_field
        n = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        self.account.records += n
        if not n:
            return
        kind = c.row.get('kind')
        with S.batch():                                     # the beings: each record's, of its kind; then the others
            if kind:
                db.execute(f'INSERT OR IGNORE INTO being (id, kind) SELECT DISTINCT t."{bcol}", ? FROM {table} t', (kind,))
                db.execute(f'UPDATE being SET kind = ? WHERE kind IS NULL AND id IN (SELECT "{bcol}" FROM {table})', (kind,))
            else:
                db.execute(f'INSERT OR IGNORE INTO being (id) SELECT DISTINCT t."{bcol}" FROM {table} t')
        S._beings.clear()
        others = set()
        for g in groups:                                    # a being another model's records hold: of that model's kind
            for role, spec in g['roles'].items():
                if spec[0] != 'col' or 'being' not in c._shapes(g['verb'], role):
                    continue
                for m2, t2 in (getattr(self, '_tables', None) or {}).items():
                    c2 = self.carry.get(m2)
                    if t2 == table or c2 is None or not c2.row.get('kind') or not c2._bean_field:
                        continue
                    with S.batch():
                        db.execute(f'INSERT OR IGNORE INTO being (id, kind) SELECT DISTINCT t."{spec[1]}", ? FROM {table} t '
                                   f'WHERE t."{spec[1]}" IN (SELECT "{c2._bean_field}" FROM {t2})', (c2.row['kind'],))
        for g in groups:
            for role, spec in list(g['roles'].items()) + [(k, ('const', v)) for k, v in g['filters'].items()]:
                if spec[0] == 'col' and 'being' in c._shapes(g['verb'], role):
                    others |= {r[0] for r in db.execute(f'SELECT DISTINCT t."{spec[1]}" FROM {table} t WHERE t."{spec[1]}" '
                                                        f"NOT IN (SELECT id FROM being) AND t.\"{spec[1]}\" != 'unknown'")}
        if others:
            self._declare({b: None for b in others}, [])
        a = S._act(ref) if ref else None
        have = [d[1] for d in db.execute(f"PRAGMA {table.split('.')[0]}.table_info({table.split('.')[1]})")]
        for g in groups:                                    # a conversion read once a record, into its own column
            for role, spec in list(g['roles'].items()):
                if spec[0] in ('col', 'unit') and spec[2] == 'escaped':
                    col = f"{spec[1]}__escaped"
                    if col not in have:
                        with S.batch():
                            db.execute(f'ALTER TABLE {table} ADD COLUMN "{col}"')
                            db.execute(f'UPDATE {table} SET "{col}" = io_esc("{spec[1]}")')
                        have.append(col)
                    g['roles'][role] = (spec[0], col, None) + tuple(spec[3:])
        for g in groups:
            self._insert_group(c, g, table, bcol, a, ref)

    def _insert_group(self, c, g, table, bcol, a, ref):
        S, db = self.store, self.store.db
        verb = g['verb']
        roles = dict(g['roles'])
        for k, v in g['filters'].items():
            roles[k] = ('const', v)
        sr = c._self_role(verb, roles)
        if sr:
            roles[sr] = ('col', bcol, None)
        cols = S.columns(verb)
        rel = 'v_' + re.sub(r'[^a-z0-9_]', '_', verb)
        S._unindex(rel)
        before = db.execute(f'SELECT COUNT(*) FROM "{rel}"').fetchone()[0]
        form_parts, form_args, names, exprs, args, need = [], [], ['being', 'id'], [], [], []
        for role in sorted(roles):                          # the form: its keys sorted, as MERGE.md 1 compares it
            spec = roles[role]
            raw, a2 = self._raw(spec)
            if spec[0] == 'unit':
                form_parts.append(f"'{role}', json_object('count', {raw}, 'unit', ?)")
                form_args += a2 + [spec[3]]
            else:
                form_parts.append(f"'{role}', {raw}")
                form_args += a2
            if spec[0] != 'const':
                need += [f'{raw} IS NOT NULL', f"{raw} != ''"]
        form = f"json_object({', '.join(form_parts)})"
        for role, spec in roles.items():
            bc, tc = cols[role]
            raw, a2 = self._raw(spec)
            being = self._being_role(verb, role, spec[1]) if spec[0] == 'const' else \
                (spec[0] == 'col' and 'being' in c._shapes(verb, role))
            if bc and being:
                names += [bc, tc]
                exprs += [f"CASE WHEN {raw} = 'unknown' THEN NULL ELSE (SELECT n FROM being WHERE id = {raw}) END",
                          f"CASE WHEN {raw} = 'unknown' THEN 'unknown' END"]
                args += a2 * 3
            elif spec[0] == 'unit':                         # a quantity, kept as the store keeps a mapping: its JSON
                if bc:
                    names.append(bc)
                    exprs.append('NULL')
                names.append(tc)
                exprs.append(f"CAST('{{\"count\": ' || json_quote({raw}) || ', \"unit\": ' || json_quote(?) || '}}' "
                             f"AS BLOB)")
                args += a2 + [spec[3]]
            else:
                if bc:
                    names.append(bc)
                    exprs.append('NULL')
                names.append(tc)
                exprs.append(raw)
                args += a2
        names.append('known')
        exprs.append('?')
        args.append(a)
        where = ' AND '.join(need) or '1'
        sel = (f'SELECT (SELECT n FROM being WHERE id = t."{bcol}"), io_mint(?, {form}), {", ".join(exprs)} '
               f'FROM {table} t WHERE {where}')
        with S.batch():
            db.execute(f'INSERT OR IGNORE INTO "{rel}" ({", ".join(names)}) {sel}', [verb] + form_args + args)
            if before and a is not None:                    # a second reading: its act on each row it read again
                db.execute(f'INSERT OR IGNORE INTO known_also (verb, row, act) SELECT ?, v.n, ? FROM {table} t JOIN '
                           f'"{rel}" v ON v.being = (SELECT n FROM being WHERE id = t."{bcol}") AND v.id = io_mint(?, '
                           f'{form}) WHERE {where} AND v.known IS NOT ?', [verb, a, verb] + form_args + [a])
            if any(spec[0] == 'col' for spec in roles.values()):   # a record with an empty role: the record's own path
                rest = db.execute(f'SELECT * FROM {table} t WHERE NOT ({where})').fetchall()
                if rest:
                    names_t = [d[1] for d in db.execute(f"PRAGMA {table.split('.')[0]}.table_info({table.split('.')[1]})")]
                    for row in rest:
                        rec = formats.Record({k: v for k, v in zip(names_t, row) if v is not None})
                        self._one_off(c, rec, ref)
        self._judge_sample(c, g, table, bcol, roles)

    def _one_off(self, c, rec, ref):
        """A record the set-wise statement passed over, written by the record's own path, its other statements one row
        each (the same form, so the rows are kept once), known by the same act."""
        being, statements, listed, notes, act_roles, header = c.into(rec)
        if being is None:
            return
        self._declare({being: c.row.get('kind')}, statements)
        for v, r in statements:
            self.store.put(being, v, r, act=ref, judge=False)

    def _judge_sample(self, c, g, table, bcol, roles):
        """Every `judge_every`th record's statement judged as a put judges one (`Store._judge_one`)."""
        if not self.judge_every:
            return
        db = self.store.db
        names_t = [d[1] for d in db.execute(f"PRAGMA {table.split('.')[0]}.table_info({table.split('.')[1]})")]
        for row in db.execute(f'SELECT * FROM {table} WHERE rowid % ? = 1', (self.judge_every,)).fetchall():
            rec = formats.Record({k: v for k, v in zip(names_t, row) if v is not None})
            being, statements, *_ = c.into(rec)
            for v, r in statements:
                if v == g['verb']:
                    r = {k: (being if x == 'self' else x) for k, x in r.items()}
                    self.store._judge_one(being, v, dict(r, id=self._mint(v, json.dumps(r))))

    def record(self, model, rec, groups=None, beings=None):
        """Keep one record of `model`: alone (`groups` None: a copier's record, put at once), or gathered for a bulk."""
        c = self.carry.get(model)
        if c is None:
            self.account.missed(getattr(rec, 'at', None) or 'a record', model, "no crosswalk crosses this model")
            return
        self.account.records += 1
        being, statements, listed, notes, act_roles, header = c.into(rec)
        at = getattr(rec, 'at', None) or f"record {self.account.records}"
        for f, why in listed:
            self.account.missed(at, f, why)
        for f, why in notes:
            self.account.note(f, why)
        if str(c.row.get('whole', '')).lower() == 'true' and listed:
            raise Refused(f"{c.name} is carried whole, and {at} holds what it does not carry: {listed[0][0]}")
        if being is None:
            self.account.missed(at, 'the whole record', 'it names no being')
            return
        self.account.carried += len(statements)
        verb = (c.row.get('act') or {}).get('verb')
        kind = c.row.get('kind')
        if not statements and self.keep == 'store':           # a being of its kind, and nothing said of it here
            if groups is None:
                self._declare({being: kind}, [])
            else:
                beings[being] = kind or beings.get(being)
            return
        if self.keep != 'store':
            self.beans_out.setdefault(being, []).extend({v: r} for v, r in statements)
            if kind:
                self.beans_out.setdefault('__kinds__', {})[being] = (kind, header.get('title'))
            return
        if str((c.row.get('act') or {}).get('per')) == 'record':
            self._per_record(c, being, kind, statements, act_roles, verb)
            return
        given = self.acts.get(model)
        if isinstance(given, str):                             # the run names the act this model's records are known by
            ref = given
        elif verb == 'derive' and groups is not None:          # known once every reading is in
            got = self.later.setdefault(being, [kind, []])
            got[1].extend(statements)
            return
        else:
            ref = self.act(verb)
        fills = self._fills(c)
        if groups is None:
            n = self.account.records
            with self.store.batch():
                self._declare({being: kind}, statements, c)
                for v, r in statements:
                    if fills:
                        self._unknown_filled(being, v, r)
                    self.store.put(being, v, r, act=ref, judge=bool(self.judge_every and n % self.judge_every == 1))
            return
        if kind:
            beings[being] = kind
        else:
            beings.setdefault(being, None)
        for v, r in statements:
            r = {k: (being if x == 'self' else x) for k, x in r.items()}    # a bulk names every being by its id
            if fills:
                self._unknown_filled(being, v, r)
            roles = tuple(sorted(k for k in r if self._being_role(v, k, r[k])))
            groups.setdefault((v, ref, roles), []).append((being, r))

    def _fills(self, c):
        """Whether the row can fill a role an earlier import left `unknown`: it names a being by a namespace."""
        key = ('fills', c.name)
        if key not in self._takes_being:
            self._takes_being[key] = any(isinstance(sp, dict) and formats.conversion(sp.get('as'))[0] == 'named'
                                         for sp in c.fields.values())
        return self._takes_being[key]

    def _being_role(self, verb, role, value):
        key = (verb, role)
        takes = self._takes_being.get(key)
        if takes is None:
            spec = (((self.law.verbs.get(verb) or {}).get('roles') or {}).get(role)) or {}
            sh = spec.get('shape') if isinstance(spec, dict) else None
            takes = self._takes_being[key] = 'being' in (sh if isinstance(sh, list) else [sh])
        if not takes or not isinstance(value, str) or value in ('unknown', 'self'):
            return False
        return value not in self.law.namespaces

    def _declare(self, beings, statements, c=None):
        """Every being the statements name kept in the store before them, with the kind it is known by: its record's,
        or its bean's; a being met first where nothing said its kind takes the one known later."""
        out = dict(beings)
        for v, r in statements:
            for k, x in r.items():
                if self._being_role(v, k, x) and x not in out:
                    out[x] = None
        if not out:
            return
        beans = self._bean_ids()
        rows = []
        for b, kind in out.items():
            if kind is None and b in beans:
                bean = self.store.bean(b)
                kind = bean.kind if bean is not None else None
            rows.append((b, kind))
        self.store.beings(rows)                         # a being kept already keeps what it has
        kinds = [(k, b) for b, k in rows if k is not None]
        if kinds:
            with self.store.batch():
                self.store.db.executemany("UPDATE being SET kind = ? WHERE id = ? AND kind IS NULL", kinds)
            self.store._beings.clear()

    def _bean_ids(self):
        """The ids of the garden's beans and mappings, read from their folders once."""
        if getattr(self, '_beans', None) is None:
            import garden as dmgarden                   # the one lister of a garden's documents
            self._beans = {os.path.basename(p)[:-3] for p in dmgarden.paths(self.root, ('beans', 'mappings'))}
        return self._beans

    def _flush(self, groups, beings):
        if self.keep != 'store' or not groups:
            return
        for (v, ref, roles), rows in groups.items():
            for _b, r in rows:
                for k in roles:
                    if r[k] not in beings:
                        beings[r[k]] = None
        self._declare(beings, [])
        for (v, ref, roles), rows in groups.items():
            self.store.bulk(v, rows, act=ref, beings=roles, judge_every=self.judge_every)

    def _per_record(self, c, being, kind, statements, act_roles, verb):
        """A record known by an act of its own (a copy's `make`): the act names what it makes, and its source where
        the store keeps it."""
        S = self.store
        import store as dmstore
        with S.batch():
            self._declare({being: kind}, statements)
            for v, r in statements:
                sid = dmstore.mint(v, S.normalize(being, v, r))
                roles = dict(self.acts.get(verb) or {})
                roles.pop('in', None)
                roles.update(act_roles)
                roles.setdefault('by', self._host())
                roles['of'] = [sid]
                src = roles.get('from')
                if src is not None:
                    srcs = [x for x in (src if isinstance(src, list) else [src]) if x and S.resolve(x) is not None]
                    if srcs:
                        roles['from'] = srcs
                    else:
                        roles.pop('from')
                        self.account.note('source', "its source is kept nowhere here: `from` left out")
                order = ['by', 'of', 'from', 'through', 'at', 'note']
                roles = {k: roles[k] for k in sorted(roles, key=lambda k: order.index(k) if k in order else 9)}
                n = self.account.records
                act = S.put(being, verb, roles, judge=False)
                S.put(being, v, r, act=f"{being}#{act}", judge=(self.judge_every and n % self.judge_every == 1))

    def _unknown_filled(self, being, verb, roles):
        """A statement this crosswalk wrote with `unknown` in a role this one fills: taken out, its reason this one."""
        S = self.store
        if verb not in S.verbs():
            return
        for v2, r2, _acts in S.get(being):
            if v2 != verb:
                continue
            gaps = [k for k, x in r2.items() if x == 'unknown' and roles.get(k) not in (None, 'unknown')]
            same = all(r2.get(k) == x for k, x in roles.items() if k not in gaps and k != 'id')
            if gaps and same:
                S.gone(being, r2['id'], by=self._host(), why=f"filled: {', '.join(gaps)} named since")
                self.unknown_filled += 1

    def done(self):
        """What a derive knows, kept now that every reading is in, by one act from them all. Returns the account."""
        if self.keep == 'store' and self._later_tables:
            ref = self.act('derive')
            for model, table in sorted(self._later_tables):
                self._write_table(self.carry[model], self._compile(self.carry[model]), table, ref)
                self.store.db.execute(f"DROP TABLE IF EXISTS {table}")
            self._later_tables.clear()
        if self.keep == 'store' and self.later:
            ref = self.act('derive')
            groups, beings = collections.OrderedDict(), {}
            seen = set()
            for being, (kind, statements) in self.later.items():
                beings[being] = kind
                for v, r in statements:
                    r = {k: (being if x == 'self' else x) for k, x in r.items()}
                    key = (being, v, repr(sorted(r.items())))
                    if key in seen:
                        continue
                    seen.add(key)
                    roles = tuple(sorted(k for k in r if self._being_role(v, k, r[k])))
                    groups.setdefault((v, ref, roles), []).append((being, r))
            self.later.clear()
            self._flush(groups, beings)
        return self.account

    def beans_text(self, with_act=True):
        """The statements for each bean, as its front matter writes them."""
        import yaml
        out = []
        acts = self.beans_out.get('__acts__') or []
        for being, sts in self.beans_out.items():
            if being.startswith('__'):
                continue
            body = list(sts) + ([a for _w, a in acts[:1]] if with_act and acts else [])
            out.append(f"# beans/{being}.md")
            out.append(yaml.safe_dump({'statements': body}, sort_keys=False, allow_unicode=True,
                                      default_flow_style=None).rstrip())
        return '\n'.join(out) + ('\n' if out else '')

    def write_beans(self):
        """Each bean's statements and the act written into its file (made where there is none), for the person's save."""
        import store as dmstore
        acts = self.beans_out.get('__acts__') or []
        kinds = self.beans_out.get('__kinds__') or {}
        paths = []
        for being, sts in self.beans_out.items():
            if being.startswith('__'):
                continue
            act = acts[0][1] if acts else {'read': {'by': self._host(), 'at': 'now'}}
            act = {v: dict(r, at='now') for v, r in act.items()}
            kind, title = kinds.get(being, (None, None))
            paths.append(dmstore.write_bean(self.root, being, list(sts), act, kind=kind or 'document', title=title))
        return paths


TAKES = {'file-tree': {'path', 'type', 'size', 'hash'},
         'copies': {'h', 'dest', 'size', 'class', 'src_vol', 'src_path', 'day', 'day_from', 'at'}}


def _arg(argv, flag, default=None, many=False):
    vals = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == flag]
    return vals if many else (vals[-1] if vals else default)


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0 if argv else 2
    from core.check import garden_law
    if argv[0] == '--list':
        law = garden_law(ROOT, ROOT if os.path.isfile(os.path.join(ROOT, 'core', 'law', 'core.yaml')) else None)
        for n, r in sorted(law.crosswalks.items()):
            if r.get('format') is not None:
                fm = r['format'] if isinstance(r['format'], list) else [r['format']]
                print(f"  {n:<22} {r.get('system')} {r.get('series')} {r.get('model'):<12} {', '.join(map(str, fm))}"
                      + (f" — reader {r['reader']}" if r.get('reader') else ''))
        return 0
    if argv[0] == 'proposal':                                 # another garden's proposal: its own tool reads and takes it
        import propose as dmpropose
        rest = [a for a in argv[1:] if a not in ('--take',)]
        return dmpropose.main((['take'] if '--take' in argv else ['read']) + rest)
    if argv[0] == 'daftar':                                   # the garden's own statements, into a store: store.py's
        import store as dmstore
        into = _arg(argv, '--into', '')
        if not into.startswith('store:'):
            print("import: the garden's own statements go into a store: --into store:<name>", file=sys.stderr)
            return 2
        names = [a for i, a in enumerate(argv[1:], 1) if not a.startswith('--') and argv[i - 1] not in ('--into', '--act')]
        if len(names) == 1 and names[0].endswith('.jsonl'):
            with open(names[0], encoding='utf-8') as fh:
                sys.stdin = fh
                return dmstore.main(['put', into.split(':', 1)[1]] + (['--act', _arg(argv, '--act')] if _arg(argv, '--act')
                                                                      else []))
        return dmstore.main(['import', into.split(':', 1)[1]] + names)
    flags = {'--into', '--path', '--format', '--from', '--act', '--root', '--volume', '--carrier', '--judge-every',
             '--named'}
    pos, i = [], 0
    while i < len(argv):
        if argv[i] in flags:
            i += 2
            continue
        if argv[i] in ('--write',):
            i += 1
            continue
        pos.append(argv[i])
        i += 1
    if len(pos) < 2:
        print("import: <crosswalk> <source> ...", file=sys.stderr)
        return 2
    into = _arg(argv, '--into', 'bean')
    S = None
    try:
        if into.startswith('store:') or _arg(argv, '--path'):
            import store as dmstore
            S = dmstore.open_store(into.split(':', 1)[1] if into.startswith('store:') else None,
                                   path=_arg(argv, '--path'), root=ROOT)
        acts = {}
        for a in _arg(argv, '--act', many=True):
            d = json.loads(a)
            acts[d.pop('verb', 'read')] = d
        rargs = {k: _arg(argv, f"--{k}") for k in ('volume', 'carrier', 'root') if _arg(argv, f"--{k}")}
        imp = Import(ROOT, pos[0], keep='store' if S else 'bean', store=S, acts=acts, reader_args=rargs,
                     fmt=_arg(argv, '--format'), source_layer=_arg(argv, '--from'),
                     judge_every=int(_arg(argv, '--judge-every', '10000')),
                     named=dict(x.split('=', 1) if '=' in x else ('*', x) for x in _arg(argv, '--named', many=True)))
        if S is not None:
            with S.loading():                                 # its indexes made once, after every source is in
                for src in pos[1:]:
                    imp.source(src)
                imp.done()
        else:
            for src in pos[1:]:
                imp.source(src)
            imp.done()
        if S is None:
            if '--write' in argv:
                for p in imp.write_beans():
                    print(f"wrote {os.path.relpath(p, ROOT)}")
            else:
                sys.stdout.write(imp.beans_text())
        else:
            print(f"import: {imp.account.records:,} records, {imp.account.carried:,} statements kept in {S.name}")
    except (Refused, formats.Refused) as e:
        print(f"import: refused — {e}", file=sys.stderr)
        return 1
    for line in imp.account.lines():
        print(line, file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
