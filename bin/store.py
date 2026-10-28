#!/usr/bin/env python3
"""store — statements kept off git, as rows, on the host that keeps them (core 2.10; MODEL.md, The store).

    python3 bin/store.py list                                         # the stores this host keeps, and where
    python3 bin/store.py open <store>                                 # its file made where this host keeps it
    python3 bin/store.py get <store> <being> [--json]                 # a being's statements, as its bean holds them
    python3 bin/store.py query <store> "<sql>" [<param> ...]          # read-only SQL over its relations
    python3 bin/store.py check [<store> ...] [--json]                 # the union: git and the stores kept here
    python3 bin/store.py export <store> <being> --by <being> [--write] # its rows as statements for its bean
    python3 bin/store.py import <store> <bean> ...                    # beans' statements in, with the acts that know them
    python3 bin/store.py put <store> --act <ref> < rows.jsonl         # rows in, one JSON object a line (below)
    python3 bin/store.py gone <store> <being> <id> --by <being> --why "<why>"   # a statement out, its removal recorded
    python3 bin/store.py series <store> import|export <bean> <key> <part>       # a series' part in, and back

(`python` on Windows.) Each takes `--path <file>` in place of a store's name: the file named directly, as a test does.

ONE UNIVERSE (MODEL.md, The store). A being has one id wherever it is kept: a bean, rows in one store or several, or
both. Where a statement is kept is a choice of keeping, not a kind of fact, and a being's statements are the union of
every keeping, as a set: two statements are one when their forms are one (MERGE.md 1), and under one `(being, id)`
two forms are a conflict a person settles. A store is the keeping for what a tool reads off the world or makes, in
numbers git cannot carry; what a person says goes into a bean.

WHERE A STORE IS. A host keeps a store when its bean says where, beside its `roots`:
`details.stores.<name>: { at: <a position on the host>, form: sqlite, readers: [<user>, ...] }`. `form` names the form
the file is kept in, and `sqlite` is its one occupant today. `readers` names who reads it beside its writer: a store
another user reads is kept with a rollback journal, its file readable by others, so reading it needs read permission
alone; any other is kept in WAL, where a long read is a snapshot and never holds up a writer.

THE FORM. One relation a verb, `v_<verb>`: the being whose statement it is (`being`), its `id`, a column a role and
a qualifier of the verb's row, `while`, `why`, `note`, and `known`. A filler is written as a bean writes it, and read
back the same: a being by its id (kept as an integer into `being`, so a join over millions is an integer join), a
statement `<being>#<id>`, a position in its system's form, text as text, and a list, a map or a quantity as JSON. A
being is kept with its kind (a nature is judged without git), and its title, summary and `details` where it has them.
A store keeps no sealed material: what rule `harm` would seal is refused at its put.

A NAME IN BYTES (`escaped`, `escape`/`unescape` here): a name the world gives in bytes that need not be UTF-8 — a
file's — is written UTF-8, a byte no part of a well-formed UTF-8 sequence, a control character and `%` itself as `%XX`.

KNOWING. In a bean an act names what it knows (`of`); a row names its act instead, `known` (a reference `<being>#<id>`
to a `say`, `read`, `derive` or `make`, kept here or in a bean). A statement known twice names both. One act covers
everything a run put, so a scan of a million files is one `read`.

IDS. A writer may give an id. A row given none is named from its form, `<verb>-<16 hexadecimal digits of the SHA-256
of its canonical form>` (`mint`): the same statement put twice is one row, and a statement of a bean that has no id is
named, from here, by the same digest of its form, so an act or a statement in git is referred to though its bean gave
it no id.

NOTHING CHANGES UNRECORDED. A store is appended to. A statement leaves it only by `gone`, which records who, when and
why beside the rows; a row's form is never changed in place.

THE POINTER. In git a bean names a being kept only in a store `store:<kind>:<id>`, and one of its statements
`store:<kind>:<id>#<id>`. The gate checks the shape and the kind; whether it resolves is this tool's check, on a host
that keeps the store. In a store every being is its plain id: `import` reads a pointer back as the id, and `export`
writes one for a being that has no bean.

THE CHECK. `check` judges the union of git and every store this host keeps, by the one judge every door asks
(core/judge.py, the scope `union`): git's own findings first, then what the stores add. A union small enough is judged by the
core's own engine — every rule, over the beans and the stores' beings read as beans — and what it finds beyond git's own
findings is the store's; in a larger one, each store small enough is still judged so, beside git, alone. Over the whole
union, however large, each rule that is a reading of the law is judged by its reading compiled to SQL (core/union.py),
by the same operations, with the engine's words and places; a name a namespace gives once by the engine's own code,
the SQL finding the names given twice; by queries, each act a row names (a knowing act, here or in git), each being's
kind against its bean's, the overlaps (one `(being, id)`, one form), and every pointer in git; and every row of a large
store as its put judges one (`row_findings`): the rows its put may refuse found set-wise — by SQL what a row's columns
alone decide, by the engine's own code once for each distinct filler of a column — and each found judged by the put's
own judgement, told at its place in the union. So a load that judged a sample (`bulk`, an import set-wise) is judged
whole here. Each rule judged neither way at that size is named, never passed over in silence. Every store is read
through one connection, in one transaction: one snapshot of each, the same for the queries, the SQL and the engine's
reading of its rows, so a writer at work is seen before or after, whole. The gate never reads a store: a gate that
judged one machine's disk would pass on one and fail on another.

AT SIZE, AS MEASURED (daftar v4.9.1, on one machine, the files in memory). The check's time grows with the rows, and
most with the distinct values of a role that takes a position, a statement or a quantity (a moment is read in about
40 µs, once a value), and with the rows of a being kept both in a bean and in a store, which making the union reads
whole (about 17 µs a row: a series with a bean, its observations in the store). An invented store of
a year of 300 newsrooms' feeds, read each hour something was new, beside three years of one-minute observations of five
series — 20.8 M rows, 74.9 M second knowings of them, 2.6 M acts, 4.1 M beings, 6.7 GB — was checked in 659 s, holding
5.0 GB at most; a disk catalogue of 37.7 M rows and 9.2 M beings in 251 s, holding 2.2 GB. A reading that selects from a
store reads each row of the verb it selects, and holds the members it selects: one newsroom's year of items, among
2.06 M, in 24 s and 1.9 GB; one series' 1.58 M observations counted in 85 s and 7.5 GB. An import of a series'
observations takes the same time a day whatever the series held before (0.16 s for 1,440). The gate reads no store:
its time over the garden beside such a store is the garden's alone.

ROWS IN (`put`, standard input): `{"being": "<id>", "verb": "<verb>", "roles": {...}, "id": "<id>"?, "while"?, "why"?,
"note"?}`, one a line; `{"being": "<id>", "kind": "<kind>", "title"?, "summary"?}` declares a being first. `--act`
names the act that knows them all; a line that is itself a knowing act is put first and needs none.
"""
import contextlib
import hashlib
import json
import os
import re
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)

from core import engine, judge as dmjudge  # noqa: E402
from core.engine import listed, shapes_of  # noqa: E402

FORMS = ('sqlite',)                       # the occupants of a store's `form` (core/law/layers.yaml `store_shape`)
ID = engine.ID
POINTER = re.compile(r'^store:([a-z][a-z0-9-]*):([a-z0-9][a-z0-9_-]*)(?:#([a-z0-9][a-z0-9_-]*))?$')
REF = re.compile(r'^([a-z0-9][a-z0-9._-]*)#([a-z0-9][a-z0-9_-]*)$')
BESIDE = ('while', 'why', 'note')
UNION_ROWS = 200_000                      # a union of at most this many rows is judged by the core's engine whole
QUERIED = ('form', 'valency', 'knowing', 'frame', 'names', 'harm')   # the code rules a large union's check judges by
                                                                    # its queries or at a row's put: the size line says how
SCHEMA_VERSION = '1'


class StoreError(Exception):
    """A row refused, or a store that cannot be opened: the message says why."""


class NotHere(StoreError):
    """This host keeps no store of that name."""


def now():
    """The moment of a write, to the second, with its offset."""
    t = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    return t[:-2] + ':' + t[-2:]


# ------------------------------------------------------------------------------------------------ a name in bytes
from core.formats import escape, unescape  # noqa: E402,F401 — the one form of a name in bytes (core/formats.py)


# ------------------------------------------------------------------------------------------------ forms and ids
def canonical(verb, roles):
    """A statement's form, as MERGE.md 1 compares it: its verb and every role, qualifier and key but `id`, each map's
    keys sorted."""
    r = {k: v for k, v in roles.items() if k != 'id'}
    return json.dumps({verb: r}, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def mint(verb, roles):
    """The id a statement given none is named by: its verb and 16 hexadecimal digits of its form's SHA-256."""
    return f"{verb}-{hashlib.sha256(canonical(verb, roles).encode('utf-8')).hexdigest()[:16]}"


def _uri(path, mode=None):
    """A file's SQLite URI: `file:` and its path, `%`, `?` and `#` in it written `%XX`, so none is read as a parameter."""
    p = os.path.abspath(path).replace('%', '%25').replace('?', '%3F').replace('#', '%23')
    return 'file:' + p + (f'?mode={mode}' if mode else '')


def _col(name):
    return re.sub(r'[^a-z0-9_]', '_', name)


def _q(name):
    return '"' + name.replace('"', '""') + '"'


# ------------------------------------------------------------------------------------------------ where stores are
def _host(root):
    import held as dmheld
    import where as dmwhere
    beans = dmheld._terms(root)
    hid, hfm = dmwhere.this_host(beans)
    return hid, hfm, dmwhere


def kept_here(root=ROOT):
    """{name: (path or None, row, why not)} of every store this host's bean declares (`details.stores`)."""
    hid, hfm, dmwhere = _host(root)
    out = {}
    names = dmwhere.names_of(hid, hfm) if hid else set()
    for name, row in (((hfm or {}).get('stores')) or {}).items():
        if not isinstance(row, dict) or not isinstance(row.get('at'), str):
            out[name] = (None, row, "declares no `at`")
            continue
        try:
            path, _o, why = dmwhere.on_host(row['at'], dmwhere.roots_of(hfm), names)
        except ValueError as e:
            path, why = None, str(e)
        out[name] = (path, row, why)
    return out


def open_store(name=None, *, path=None, root=ROOT, create=True, readers=None):
    """The store `name` as this host keeps it — or the file at `path`, named directly."""
    if path is None:
        hit = kept_here(root).get(name)
        if not hit:
            raise NotHere(f"this host keeps no store `{name}`: its bean says where in `details.stores`")
        path, row, why = hit
        if not path:
            raise NotHere(f"the store `{name}` is not here: {why}")
        if (row.get('form') or 'sqlite') not in FORMS:
            raise StoreError(f"the store `{name}` is kept in the form `{row.get('form')}`, and this tool keeps "
                             f"{', '.join(FORMS)}")
        readers = row.get('readers') if readers is None else readers
    return Store(path, root=root, create=create, readers=readers, name=name)


# ------------------------------------------------------------------------------------------------ the store
class _RowJudge(engine.Judge):
    """The gate's own judge of one statement, for a row: a being the store keeps is a being, of the kind it keeps it
    as; a statement the store keeps is a statement."""

    def __init__(self, store):
        super().__init__(store.law, store.garden)
        self.S = store

    def kind_of(self, x, b):
        if isinstance(x, str) and x != 'self' and x not in self.G.beans and self.S.has_being(x):
            return self.S.kind_of(x)
        return super().kind_of(x, b)

    def _being(self, x, spec, b):
        if isinstance(x, str) and x != 'self' and x not in self.G.beans and x not in self.L.crown \
                and not POINTER.match(x) and self.S.has_being(x):
            kind = self.S.kind_of(x)
            if kind is None:
                return ''                  # a being kept here whose kind is not known yet: the check judges it
            if kind not in self.L.kinds:
                return f"{x!r} is kept as `{kind}`, no kind of the law"
            nat = self.nature(kind)
            if spec.get('nature') and nat not in listed(spec['nature']):
                return f"this role takes a being that is {' or '.join(listed(spec['nature']))}; {x} is {nat}"
            return ''
        return super()._being(x, spec, b)

    def statement(self, ref, b):
        hit = super().statement(ref, b)
        if hit is not None:
            return hit
        if not isinstance(ref, str):
            return None
        being, _, sid = ref.partition('#') if '#' in ref else (b.id, '', ref)
        st = self.S.statement(being, sid)
        if st is None:
            return None
        verb, roles = st
        return (engine.Bean(being, header={'bean': being, 'statements': [{verb: roles}]}), 0, verb, roles)


class Store:
    """One store's file: its relations, its beings, its acts."""

    def __init__(self, path, *, root=ROOT, create=True, readers=None, name=None, law=None, garden=None, readonly=False):
        self.path, self.root, self.name = path, root, name or os.path.splitext(os.path.basename(path))[0]
        self.readonly = readonly
        new = not os.path.exists(path)
        if new and (not create or readonly):
            raise NotHere(f"no store at {path}")
        if new:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        if readonly:                       # a reader, maybe of another user: read permission alone, nothing written
            self.db = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=60, isolation_level=None)
            self.db.execute('PRAGMA query_only=ON')
        else:                              # by its URI, so a source can be attached to it read-only (bin/import.py)
            self.db = sqlite3.connect(_uri(path), uri=True, timeout=60, isolation_level=None)
        self.db.execute('PRAGMA busy_timeout=60000')
        self.db.execute('PRAGMA foreign_keys=OFF')
        self._law, self._garden, self._judge = law, garden, None
        self._beings = {}                  # id -> (n, kind)
        self._cols = {}                    # verb -> {role: (has b_, ...)}
        self._acts = {}                    # ref -> n
        self._depth = 0
        self._s = ''                       # the schema its reads name, read through the check's one connection
        if readonly:
            pass
        elif new:
            shared = bool(readers) and any(r != _me() for r in listed(readers))
            self.db.execute('PRAGMA journal_mode=' + ('DELETE' if shared else 'WAL'))
            self._base()
            self.db.execute("INSERT OR REPLACE INTO meta (k, v) VALUES ('name', ?), ('schema', ?), ('created', ?), "
                            "('readers', ?)", (self.name, SCHEMA_VERSION, now(), json.dumps(listed(readers))))
            if shared:
                os.chmod(path, 0o644)
        else:
            self._base()
            self._heal()

    # -------------------------------------------------------------------------------------------- the law and git
    @property
    def law(self):
        if self._law is None:
            from core import check as core_check
            rel = self.root if os.path.isfile(os.path.join(self.root, 'core', 'law', 'core.yaml')) else None
            self._law = core_check.garden_law(self.root, rel)
        return self._law

    @property
    def garden(self):
        if self._garden is None:
            self._garden = engine.Garden.read(self.root)
        return self._garden

    def bean(self, bid):
        """The bean of `bid` in git, read alone from its file (beans/ or mappings/), or None: what a writer asks of a
        being, without reading the whole garden."""
        if self._garden is not None:
            return self._garden.beans.get(bid)
        cache = self.__dict__.setdefault('_beans_read', {})
        if bid not in cache:
            cache[bid] = None
            if isinstance(bid, str) and ID.match(bid):
                for space in ('beans', 'mappings'):
                    p = os.path.join(self.root, space, bid + '.md')
                    if os.path.isfile(p):
                        cache[bid] = engine._bean(p, bid)
                        break
        return cache[bid]

    def has_bean(self, bid):
        return self.bean(bid) is not None

    @property
    def judge(self):
        if self._judge is None:
            self._judge = _RowJudge(self)
        return self._judge

    # -------------------------------------------------------------------------------------------- the file
    def _base(self):
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT) WITHOUT ROWID;
            CREATE TABLE IF NOT EXISTS being (n INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE, kind TEXT, title TEXT,
                                              summary TEXT);
            CREATE TABLE IF NOT EXISTS detail (being INTEGER NOT NULL, key TEXT NOT NULL, value BLOB,
                                               PRIMARY KEY (being, key)) WITHOUT ROWID;
            CREATE TABLE IF NOT EXISTS act (n INTEGER PRIMARY KEY, ref TEXT NOT NULL UNIQUE);
            CREATE TABLE IF NOT EXISTS known_also (verb TEXT NOT NULL, row INTEGER NOT NULL, act INTEGER NOT NULL,
                                                   PRIMARY KEY (verb, row, act)) WITHOUT ROWID;
            CREATE TABLE IF NOT EXISTS gone (verb TEXT, being TEXT, id TEXT, form TEXT, by TEXT, at TEXT, why TEXT);
            CREATE TABLE IF NOT EXISTS series_part (being TEXT NOT NULL, key TEXT NOT NULL, part TEXT NOT NULL,
                                                    sha256 TEXT NOT NULL, bytes BLOB NOT NULL,
                                                    PRIMARY KEY (being, key, part)) WITHOUT ROWID;
        """)

    def close(self):
        self.db.close()

    # -------------------------------------------------------------------------------------------- a load of many rows
    @contextlib.contextmanager
    def loading(self):
        """For a load of many rows: each relation's secondary indexes are dropped at its first bulk inside this, and made
        again when it ends — never the unique `(being, id)` a put is named by, nor the beings'. A load cut short leaves
        what it dropped in `meta`, and the next writer to open the store makes them again."""
        if getattr(self, '_loading', None) is not None:
            yield self
            return
        self._loading = {}
        try:
            yield self
        finally:
            dropped, self._loading = self._loading, None
            for table, sqls in dropped.items():
                with self.batch():
                    for sql in sqls:
                        self.db.execute(sql.replace('CREATE INDEX ', 'CREATE INDEX IF NOT EXISTS ', 1))
                    self.db.execute("DELETE FROM meta WHERE k = ?", (f'loading:{table}',))

    def _unindex(self, table):
        """Inside `loading`, drop the relation's secondary indexes once, keeping what made them."""
        if getattr(self, '_loading', None) is None or table in self._loading:
            return
        sqls = [r[0] for r in self.db.execute("SELECT sql FROM sqlite_master WHERE type = 'index' AND tbl_name = ? AND "
                                              "sql IS NOT NULL", (table,))]
        self._loading[table] = sqls
        if sqls:
            with self.batch():
                self.db.execute("INSERT OR REPLACE INTO meta (k, v) VALUES (?, ?)", (f'loading:{table}', json.dumps(sqls)))
                for (name,) in self.db.execute("SELECT name FROM sqlite_master WHERE type = 'index' AND tbl_name = ? AND "
                                               "sql IS NOT NULL", (table,)).fetchall():
                    self.db.execute(f"DROP INDEX {_q(name)}")

    def _heal(self):
        """The indexes a load cut short dropped, made again."""
        rows = self.db.execute("SELECT k, v FROM meta WHERE k LIKE 'loading:%'").fetchall()
        for k, v in rows:
            with self.batch():
                for sql in json.loads(v):
                    self.db.execute(sql.replace('CREATE INDEX ', 'CREATE INDEX IF NOT EXISTS ', 1))
                self.db.execute("DELETE FROM meta WHERE k = ?", (k,))

    @contextlib.contextmanager
    def batch(self):
        """One transaction for every write inside it: all of them, or none."""
        if self._depth == 0:
            self.db.execute('BEGIN IMMEDIATE')
        self._depth += 1
        try:
            yield self
        except BaseException:
            self._depth -= 1
            if self._depth == 0:
                self.db.execute('ROLLBACK')
                self._beings.clear()
                self._acts.clear()
            raise
        else:
            self._depth -= 1
            if self._depth == 0:
                self.db.execute('COMMIT')

    def verbs(self):
        """The verbs this store keeps a relation of (read again when the schema changed: another writer may add one)."""
        ver = self.db.execute(f'PRAGMA {self._s}schema_version').fetchone()[0]
        if getattr(self, '_verbs_at', None) != ver:
            self._verbs = sorted(r[0][2:] for r in self.db.execute(
                f"SELECT name FROM {self._s}sqlite_master WHERE type='table' AND name LIKE 'v\\_%' ESCAPE '\\'"))
            self._verbs_at = ver
        return self._verbs

    def _verb_of_table(self, table):
        return table[2:]

    def columns(self, verb):
        """{role or qualifier: (being column or None, text column)} of the verb's relation, made at its first row. A
        reader reads them from the file itself, and needs no law: only a writer makes a relation, by its verb's row."""
        if verb in self._cols:
            return self._cols[verb]
        if self.readonly or self._s or (self._law is None and self._stored_shapes(verb) is not None):
            have = [r[1] for r in self.db.execute(f"PRAGMA {self._s}table_info({_q('v_' + _col(verb))})")]
            cols = {}
            for c in have:
                if c[:2] in ('b_', 't_', 'q_'):
                    k = c[2:]
                    bc, tc = cols.get(k, (None, None))
                    cols[k] = (c if c.startswith('b_') else bc, c if not c.startswith('b_') else tc)
            self._cols[verb] = cols
            return cols
        row = self.law.verbs.get(verb)
        if row is None:
            raise StoreError(f"`{verb}` is no verb of the law")
        cols = {}
        for k, spec in (row.get('roles') or {}).items():
            cols[k] = (('b_' + _col(k)) if 'being' in shapes_of(spec) else None, 't_' + _col(k))
        for k in (row.get('qualifiers') or {}):
            cols[k] = (None, 'q_' + _col(k))
        table = 'v_' + _col(verb)
        have = {r[1] for r in self.db.execute(f"PRAGMA table_info({_q(table)})")}
        if not have:
            defs = ['n INTEGER PRIMARY KEY', 'being INTEGER NOT NULL', 'id TEXT NOT NULL']
            for k, (bc, tc) in cols.items():
                if bc:
                    defs.append(f"{bc} INTEGER")
                defs.append(tc)
            defs += ['c_while', 'c_why', 'c_note', 'known INTEGER', 'UNIQUE (being, id)']
            self.db.execute(f"CREATE TABLE IF NOT EXISTS {_q(table)} ({', '.join(defs)})")
            shapes = {k: shapes_of(spec) for k, spec in list((row.get('roles') or {}).items()) +
                      list((row.get('qualifiers') or {}).items())}
            self.db.execute("INSERT OR REPLACE INTO meta (k, v) VALUES (?, ?)", (f'shapes:{verb}', json.dumps(shapes)))
            self.db.execute(f"CREATE INDEX IF NOT EXISTS {_q(table + '_id')} ON {_q(table)} (id)")   # a statement by id
            for k, (bc, tc) in cols.items():
                if bc:
                    self.db.execute(f"CREATE INDEX IF NOT EXISTS {_q(table + '_' + bc)} ON {_q(table)} ({bc})")
                elif shapes_of((row.get('roles') or {}).get(k) or {}) == ['statement']:     # what names a statement
                    self.db.execute(f"CREATE INDEX IF NOT EXISTS {_q(table + '_' + tc)} ON {_q(table)} ({tc})")
        else:
            grew = False
            for k, (bc, tc) in cols.items():     # a row of the law that grew a role since: its column added
                for c in (bc, tc):
                    if c and c not in have:
                        self.db.execute(f"ALTER TABLE {_q(table)} ADD COLUMN {c}")
                        grew = True
                        if c == bc:
                            self.db.execute(f"CREATE INDEX IF NOT EXISTS {_q(table + '_' + bc)} ON {_q(table)} ({bc})")
                        elif not bc and shapes_of((row.get('roles') or {}).get(k) or {}) == ['statement']:
                            self.db.execute(f"CREATE INDEX IF NOT EXISTS {_q(table + '_' + tc)} ON {_q(table)} ({tc})")
            if grew:                             # its shapes as the law now says them, for a reader with no law
                shapes = {k: shapes_of(spec) for k, spec in list((row.get('roles') or {}).items()) +
                          list((row.get('qualifiers') or {}).items())}
                self.db.execute("INSERT OR REPLACE INTO meta (k, v) VALUES (?, ?)", (f'shapes:{verb}', json.dumps(shapes)))
        self._cols[verb] = cols
        return cols

    # -------------------------------------------------------------------------------------------- beings
    def _t(self, name):
        """A relation of this store as a read names it: under its schema where the check reads it (`one_snapshot`)."""
        return self._s + _q(name)

    def has_being(self, bid):
        return self._being_row(bid) is not None

    def _being_row(self, bid):
        if bid in self._beings:
            return self._beings[bid]
        r = self.db.execute(f'SELECT n, kind FROM {self._s}being WHERE id=?', (bid,)).fetchone()
        if r:
            self._beings[bid] = (r[0], r[1])
            return self._beings[bid]
        return None

    def kind_of(self, bid):
        r = self._being_row(bid)
        if r and r[1]:
            return r[1]
        b = self.bean(bid)
        return b.kind if b is not None else None

    def being(self, bid, kind=None, title=None, summary=None):
        """The being `bid` kept here, with its kind (and title, summary): its number. A kind once kept is kept."""
        if not isinstance(bid, str) or not ID.match(bid):
            raise StoreError(f"{bid!r}: a being's id is one word — `^[a-z0-9][a-z0-9_-]*$`")
        if kind is not None and kind not in self.law.kinds:
            raise StoreError(f"`{kind}` is no kind of the law")
        bean = self.bean(bid)
        if bean is not None and kind is not None and bean.kind != kind:
            raise StoreError(f"{bid} has a bean of the kind `{bean.kind}`: it is kept as that, not `{kind}`")
        hit = self._being_row(bid)
        if hit:
            n, k = hit
            if kind is not None and k is not None and k != kind:
                raise StoreError(f"{bid} is kept as `{k}`, and a being keeps its kind: not `{kind}`")
            if (kind is not None and k is None) or title is not None or summary is not None:
                self.db.execute('UPDATE being SET kind=COALESCE(kind, ?), title=COALESCE(?, title), '
                                'summary=COALESCE(?, summary) WHERE n=?', (kind, title, summary, n))
                self._beings[bid] = (n, k or kind)
            return n
        k = kind or (bean.kind if bean is not None else None)
        cur = self.db.execute('INSERT INTO being (id, kind, title, summary) VALUES (?, ?, ?, ?)', (bid, k, title, summary))
        self._beings[bid] = (cur.lastrowid, k)
        return cur.lastrowid

    def _known_being(self, x):
        return isinstance(x, str) and (self.has_bean(x) or self.has_being(x))

    def detail(self, bid, key, *value):
        """A being's detail `key` (its `details`, as a bean keeps them), read — or written, given a value (None takes it
        out)."""
        n = self.being(bid)
        if not value:
            r = self.db.execute('SELECT value FROM detail WHERE being=? AND key=?', (n, key)).fetchone()
            return json.loads(r[0]) if r else None
        if value[0] is None:
            self.db.execute('DELETE FROM detail WHERE being=? AND key=?', (n, key))
        else:
            self.db.execute('INSERT OR REPLACE INTO detail (being, key, value) VALUES (?, ?, ?)',
                            (n, key, json.dumps(value[0], ensure_ascii=False, sort_keys=True)))

    def details(self, bid):
        r = self._being_row(bid)
        if not r:
            return {}
        return {k: json.loads(v) for k, v in self.db.execute(f'SELECT key, value FROM {self._s}detail WHERE being=?', (r[0],))}

    # -------------------------------------------------------------------------------------------- fillers
    def _stored_shapes(self, verb):
        """{role: [shapes]} kept with the verb's relation when it was made, or None (a relation made before 2.11.3, or
        none yet)."""
        cache = self.__dict__.setdefault('_shapes', {})
        if verb not in cache:
            r = self.db.execute(f"SELECT v FROM {self._s}meta WHERE k = ?", (f'shapes:{verb}',)).fetchone()
            cache[verb] = json.loads(r[0]) if r else None
        return cache[verb]

    def shapes(self, verb):
        """{role or qualifier: [shapes]} of a verb: kept with its relation, else read from the law."""
        got = self._stored_shapes(verb)
        if got is not None:
            return got
        spec = (self.law.verbs.get(verb) or {})
        return {k: shapes_of(v) for k, v in list((spec.get('roles') or {}).items()) +
                list((spec.get('qualifiers') or {}).items())}

    def normalize(self, being, verb, roles):
        """A statement's roles as a store keeps them: `self` the being, a statement of the being `<being>#<id>`, a
        pointer the plain id (its kind kept)."""
        allr = self.shapes(verb)
        out = {}
        for k, v in roles.items():
            if k in ('id',) + BESIDE:
                out[k] = v
                continue
            out[k] = self._norm(v, being, allr.get(k) or [])
        return out

    def _norm(self, v, being, shapes):
        if isinstance(v, list):
            return [self._norm(x, being, shapes) for x in v]
        if not isinstance(v, str):
            return v
        if v == 'self' and 'being' in shapes:
            return being
        m = POINTER.match(v)
        if m:                                # the plain id; a writer declares the being first (`_declare`), a reader never
            kind, bid, sid = m.groups()
            if 'being' in shapes or 'statement' in shapes:
                return f"{bid}#{sid}" if sid else bid
        if 'statement' in shapes and '#' not in v and ID.match(v) and not self._known_being(v):
            return f"{being}#{v}"
        return v

    def _declare(self, roles):
        """Each being a pointer in `roles` names, kept here with the kind the pointer gives: what a writer does before
        it normalizes a statement."""
        for v in roles.values():
            for x in (v if isinstance(v, list) else [v]):
                m = POINTER.match(x) if isinstance(x, str) else None
                if m:
                    self.being(m.group(2), m.group(1))

    def denormalize(self, being, verb, roles):
        """A row's roles as `being`'s bean writes them: the being `self`, its own statements by their id, a being with
        no bean in git a pointer."""
        allr = self.shapes(verb)
        return {k: (v if k in ('id',) + BESIDE else self._denorm(v, being, allr.get(k) or []))
                for k, v in roles.items()}

    def _denorm(self, v, being, shapes):
        if isinstance(v, list):
            return [self._denorm(x, being, shapes) for x in v]
        if not isinstance(v, str):
            return v
        if 'being' in shapes and v == being:
            return 'self'
        m = REF.match(v)
        if 'statement' in shapes and m:
            b, sid = m.groups()
            if b == being:
                return sid
            if not self.has_bean(b) and self.has_being(b):
                return f"store:{self.kind_of(b)}:{b}#{sid}"
            return v
        if 'being' in shapes and ID.match(v) and not self.has_bean(v) and self.has_being(v) and \
                v not in self.law.crown and v != 'unknown':
            k = self.kind_of(v)
            return f"store:{k}:{v}" if k else v
        return v

    def _encode(self, verb, roles):
        cols, vals = [], []
        spec = self.columns(verb)
        for k, v in roles.items():
            if k == 'id':
                continue
            if k in BESIDE:
                cols.append('c_' + k)
                vals.append(v)
                continue
            if k not in spec and self._law is None and not self.readonly:   # read from the file: the law may have
                self._cols.pop(verb, None)                                     # given the verb a role since — ask it
                self.law
                spec = self.columns(verb)
            if k not in spec:
                raise StoreError(f"`{k}` is no role or qualifier `{verb}` takes")
            bc, tc = spec[k]
            if bc and isinstance(v, str) and v != 'unknown' and self._known_being(v):
                cols.append(bc)
                vals.append(self.being(v))
            elif isinstance(v, str):
                cols.append(tc)
                vals.append(v)
            else:
                cols.append(tc)
                vals.append(json.dumps(v, ensure_ascii=False, sort_keys=True).encode('utf-8'))
        return cols, vals

    def _decode(self, verb, row, names):
        """(id, roles, known act n) from a row of `v_<verb>` read with `SELECT *`."""
        rec = dict(zip(names, row))
        roles = {}
        for k, (bc, tc) in self.columns(verb).items():
            if bc and rec.get(bc) is not None:
                roles[k] = self._id_of(rec[bc])
            elif rec.get(tc) is not None:
                v = rec[tc]
                roles[k] = json.loads(v) if isinstance(v, bytes) else v
        for k in BESIDE:
            if rec.get('c_' + k) is not None:
                roles[k] = rec['c_' + k]
        return rec['id'], roles, rec.get('known'), rec['n'], self._id_of(rec['being'])

    def _id_of(self, n):
        r = self.db.execute(f'SELECT id FROM {self._s}being WHERE n=?', (n,)).fetchone()
        return r[0] if r else None

    # -------------------------------------------------------------------------------------------- acts
    def _act(self, ref):
        if ref in self._acts:
            return self._acts[ref]
        r = self.db.execute('SELECT n FROM act WHERE ref=?', (ref,)).fetchone()
        n = r[0] if r else self.db.execute('INSERT INTO act (ref) VALUES (?)', (ref,)).lastrowid
        self._acts[ref] = n
        return n

    def _act_ref(self, n):
        r = self.db.execute(f'SELECT ref FROM {self._s}act WHERE n=?', (n,)).fetchone()
        return r[0] if r else None

    def resolve(self, ref):
        """(where, verb, roles) of the statement `<being>#<id>` names — kept here ('store') or in git ('git') — or
        None. A statement of a bean that gave it no id is found by its minted id."""
        m = REF.match(ref) if isinstance(ref, str) else None
        if not m:
            return None
        b, sid = m.groups()
        st = self.statement(b, sid)
        if st:
            return ('store',) + st
        return self._in_git(b, sid)

    def _in_git(self, b, sid):
        """('git', verb, roles) of the statement `<b>#<sid>` of a bean in git, or None."""
        bean = self.bean(b)
        if bean is not None:
            for _i, verb, r in bean.items:
                if r.get('id') == sid or (r.get('id') is None and mint(verb, self.normalize(b, verb, r)) == sid):
                    return ('git', verb, r)
        return None

    def _check_act(self, ref):
        hit = self.resolve(ref)
        if hit is None:
            raise StoreError(f"the act {ref} is kept nowhere this store or git reads: put it first, or name it as "
                             f"`<being>#<id>`")
        if hit[1] not in self.law.knowing:
            raise StoreError(f"{ref} is a `{hit[1]}`, and a row is known by a knowing act "
                             f"({', '.join(self.law.knowing)})")

    # -------------------------------------------------------------------------------------------- statements
    def statement(self, being, sid):
        """(verb, roles) of the statement `(being, id)` this store keeps, or None."""
        r = self._being_row(being)
        if not r:
            return None
        for verb in self.verbs():
            cur = self.db.execute(f"SELECT * FROM {self._t('v_' + _col(verb))} WHERE being=? AND id=?", (r[0], sid))
            row = cur.fetchone()
            if row:
                _id, roles, _k, _n, _b = self._decode(verb, row, [d[0] for d in cur.description])
                return verb, dict(roles, id=_id)
        return None

    def get(self, being):
        """[(verb, roles with their id, [act refs])] of every statement this store keeps of `being`."""
        r = self._being_row(being)
        if not r:
            return []
        out = []
        for verb in self.verbs():
            cur = self.db.execute(f"SELECT * FROM {self._t('v_' + _col(verb))} WHERE being=? ORDER BY n", (r[0],))
            names = [d[0] for d in cur.description]
            for row in cur.fetchall():
                sid, roles, known, n, _b = self._decode(verb, row, names)
                acts = [self._act_ref(known)] if known else []
                acts += [self._act_ref(a) for (a,) in self.db.execute(
                    f'SELECT act FROM {self._s}known_also WHERE verb=? AND row=? ORDER BY act', (verb, n))]
                out.append((verb, dict(roles, id=sid), acts))
        return out

    def statements_of(self, verb, acts=False):
        """(being, id, roles) of every statement of `verb` this store keeps, in the order they were put: what a reading
        selects as entries (bin/reckon.py `select … store`). A verb the store keeps none of gives none. Read as known
        at a moment (`known_at`), only the rows known then. With `acts`, each with the refs of the acts that know it."""
        if verb not in self.verbs():
            return
        cur = self.db.execute(f"SELECT * FROM {self._t('v_' + _col(verb))} ORDER BY n")
        names = [d[0] for d in cur.description]
        until = getattr(self, '_until', None)
        for row in cur.fetchall() if until is not None else cur:
            sid, roles, known, n, being = self._decode(verb, row, names)
            if until is None or self._row_known(verb, n, known, roles):
                yield (being, sid, roles, self._row_acts(verb, n, known)) if acts else (being, sid, roles)

    def _row_acts(self, verb, n, known):
        return ([self._act_ref(known)] if known is not None else []) + [self._act_ref(a) for (a,) in self.db.execute(
            f'SELECT act FROM {self._s}known_also WHERE verb=? AND row=? ORDER BY act', (verb, n)).fetchall()]

    # A STORE AS KNOWN AT A MOMENT (core 4.9): a row is known where one of the acts that know it — its `known`, and each
    # of `known_also` — is at or before the moment, wherever the act is kept; a knowing act's own row, at its own `at`.
    # The reckoner reads a reading that names its `known` input so (core/reckon.py `known_garden`, the beans alike).
    def known_at(self, until, moment):
        """Read from now on as known at `until` (UNIX ms); `moment` reads an act's `at` as UNIX ms, or None."""
        self._until, self._moment, self._act_on, self._beings_on = until, moment, {}, None

    def _act_known(self, n):
        if n not in self._act_on:
            ref = self._act_ref(n)
            hit = self.resolve(ref) if ref else None
            m = self._moment(hit[2].get('at')) if hit else None
            self._act_on[n] = m is not None and m <= self._until
        return self._act_on[n]

    def _row_known(self, verb, n, known, roles):
        if verb in self.law.knowing:
            m = self._moment(roles.get('at'))
            return m is not None and m <= self._until
        if known is not None and self._act_known(known):
            return True
        return any(self._act_known(a) for (a,) in self.db.execute(
            f'SELECT act FROM {self._s}known_also WHERE verb=? AND row=?', (verb, n)).fetchall())

    def known_beings(self):
        """Read as known at a moment, the beings one of whose rows was known then; else None."""
        if getattr(self, '_until', None) is None:
            return None
        if self._beings_on is None:
            self._beings_on = {b for v in self.verbs() for b, _sid, _r in self.statements_of(v)}
        return self._beings_on

    def count(self):
        return sum(self.db.execute(f"SELECT COUNT(*) FROM {self._t('v_' + _col(v))}").fetchone()[0] for v in self.verbs())

    def put(self, being, verb, roles, *, act=None, judge=True):
        """Keep one statement of `being`: judged as the gate judges a bean's, named by its id or its form, known by
        `act` (a knowing act needs none). Returns its id. The same statement again adds its act; another form under
        the same id is refused."""
        if not isinstance(roles, dict):
            raise StoreError("a statement's roles are a mapping")
        roles = dict(roles)
        if 'held' in roles:
            raise StoreError("a store keeps no sealed material: a sealed statement stays in its bean, its pointer in git")
        if 'at' in roles and roles['at'] == 'now':
            roles['at'] = now()
        self.being(being)
        self._declare(roles)
        nr = self.normalize(being, verb, roles)
        sid = nr.pop('id', None)
        if sid is not None and (not isinstance(sid, str) or not ID.match(sid)):
            raise StoreError(f"{sid!r}: a statement's id is one word")
        sid = sid or mint(verb, nr)
        knowing = verb in self.law.knowing
        if act is None and not knowing:
            raise StoreError(f"{being}#{sid} ({verb}) is known by no act: name the act that read, made, derived or "
                             f"said it (`act`)")
        if judge:
            self._judge_one(being, verb, dict(nr, id=sid))
        with self.batch():
            if act is not None:
                self._check_act(act)
            cols, vals = self._encode(verb, nr)
            table = 'v_' + _col(verb)
            n_being = self.being(being)
            old = self.db.execute(f"SELECT * FROM {_q(table)} WHERE being=? AND id=?", (n_being, sid))
            have = old.fetchone()
            if have:
                _id, oroles, oknown, on, _b = self._decode(verb, have, [d[0] for d in old.description])
                if canonical(verb, oroles) != canonical(verb, nr):
                    raise StoreError(f"{being}#{sid} is kept already as another statement: an id names one statement "
                                     f"(MERGE.md 3) — give this one an id of its own, or take the other out (`gone`)")
                if act is not None:
                    a = self._act(act)
                    if oknown is None:
                        self.db.execute(f"UPDATE {_q(table)} SET known=? WHERE n=?", (a, on))
                    elif a != oknown:
                        self.db.execute('INSERT OR IGNORE INTO known_also (verb, row, act) VALUES (?, ?, ?)', (verb, on, a))
                return sid
            for other in self.verbs():
                if other != verb and self.db.execute(f"SELECT 1 FROM {_q('v_' + _col(other))} WHERE being=? AND id=?",
                                                     (n_being, sid)).fetchone():
                    raise StoreError(f"{being}#{sid} is kept already as a `{other}`: an id names one statement")
            cols = ['being', 'id'] + cols + (['known'] if act is not None else [])
            vals = [n_being, sid] + vals + ([self._act(act)] if act is not None else [])
            self.db.execute(f"INSERT INTO {_q(table)} ({', '.join(cols)}) VALUES ({', '.join('?' * len(vals))})", vals)
        return sid

    def _judge_one(self, being, verb, r):
        out = self.row_findings(being, verb, r)
        if out:
            raise StoreError('; '.join(f"{rule} {where}: {msg}" for rule, where, msg in out))

    def row_findings(self, being, verb, r, i=0, place=None):
        """[(rule, where, message)] of one row as its put judges it: the statement's own form, valency and frame and its
        fillers' natures (the engine's `one`, the statement alone in its bean, at index `i`), the form of a name it gives
        (rule `names`, the engine's `name_form`), and the clauses of a row: a control character, a name kept only in the
        held store, a code of a scheme marked special-category. Each is told at `place` where one is given (the check
        gives a row's place in the union), else at the row."""
        J = self.judge
        b = engine.Bean(being, header={'bean': being, 'kind': self.kind_of(being), 'statements': [{verb: r}]})
        J.out = dmjudge.statement(self.law, self.garden, b, i, verb, r, by=J)    # the one judge's door of a statement
        at = place or f"{being}#{r.get('id')} {verb}"
        for k, v in r.items():
            for s in (v if isinstance(v, list) else [v]):
                if isinstance(s, str) and engine.dmparse.CONTROL.search(s.replace('\t', '')):
                    J.err('form', at, f"`{k}` holds a control character: text holds none but a tab — a name in bytes "
                                      f"is written `escaped`")
        if verb == 'name':
            why, _bidi = J.name_form(r)
            if why:
                J.err('names', at, why)
        if verb == 'name' and isinstance(r.get('by'), str) and (self.law.namespaces.get(r['by']) or {}).get('kept') == 'held':
            J.err('harm', at, f"a name {r['by']} gives is kept only in the held store")
        marked = J._marked()
        if marked and any(s in marked for s in J._codes(r)):
            J.err('harm', at, "holds a code of a scheme marked special-category")
        out, J.out = J.out, []
        return out

    def put_many(self, rows, *, act=None, judge=True):
        """Keep many statements in one transaction: `rows` of (being, verb, roles). Returns their ids."""
        with self.batch():
            return [self.put(b, v, r, act=act, judge=judge) for b, v, r in rows]

    def beings(self, rows):
        """Keep many beings at once: (id, kind) or (id, kind, title, summary). A being kept already keeps what it has;
        the check compares each kind with its bean's."""
        with self.batch():
            self.db.executemany('INSERT OR IGNORE INTO being (id, kind, title, summary) VALUES (?, ?, ?, ?)',
                                ((r[0], r[1], r[2] if len(r) > 2 else None, r[3] if len(r) > 3 else None) for r in rows))
        self._beings.clear()

    def bulk(self, verb, rows, *, act, beings=(), judge_every=10000):
        """Keep many statements of one verb fast, for a tool that writes millions: `rows` of (being, roles), every
        being a filler names declared first (`beings`), the roles in `beings` naming beings by their ids (`unknown`
        apart), each row named by its form unless it gives an id. Every `judge_every`th row (and the first) is judged as
        `put` judges one; a row kept already is kept once, and gains `act` where another act knew it (a second reading
        of what was read before). Returns how many rows were new."""
        cols = self.columns(verb)
        if verb not in self.law.knowing:
            self._check_act(act)
        a = self._act(act) if act else None
        table = 'v_' + _col(verb)
        self._unindex(table)
        before = self.db.execute(f"SELECT COUNT(*) FROM {_q(table)}").fetchone()[0]
        names = ['being', 'id']
        order = []
        for k, (bc, tc) in cols.items():
            if bc:
                names.append(bc)
            names.append(tc)
            order.append(k)
        names += ['c_while', 'c_why', 'c_note', 'known']
        sub = '(SELECT n FROM being WHERE id=?)'
        marks = [sub, '?']
        for k in order:
            if cols[k][0]:
                marks.append(sub if k in beings else '?')
            marks.append('?')
        marks += ['?', '?', '?', '?']
        sql = f"INSERT OR IGNORE INTO {_q(table)} ({', '.join(names)}) VALUES ({', '.join(marks)})"

        def args():
            for i, (being, roles) in enumerate(rows):
                roles = dict(roles)
                sid = roles.pop('id', None)
                if sid is None:
                    sid = mint(verb, roles)
                if judge_every and i % judge_every == 0:
                    self._judge_one(being, verb, dict(roles, id=sid))
                out = [being, sid]
                for k in order:
                    v = roles.get(k)
                    bc = cols[k][0]
                    if bc:
                        if k in beings and v is not None and v != 'unknown':
                            out += [v, None]
                            continue
                        out.append(None)
                    out.append(v if (v is None or isinstance(v, str)) else
                               json.dumps(v, ensure_ascii=False, sort_keys=True).encode('utf-8'))
                out += [roles.get('while'), roles.get('why'), roles.get('note'), a]
                yield out

        also = (f"INSERT OR IGNORE INTO known_also (verb, row, act) SELECT ?, n, ? FROM {_q(table)} "
                f"WHERE being = (SELECT n FROM being WHERE id = ?) AND id = ? AND known IS NOT ?")
        with self.batch():
            if not before or a is None:                     # a relation empty before: no row of it is kept already
                self.db.executemany(sql, args())
            else:
                chunk = []
                for out in args():
                    chunk.append(out)
                    if len(chunk) >= 50000:
                        self.db.executemany(sql, chunk)
                        self.db.executemany(also, [(verb, a, r[0], r[1], a) for r in chunk])
                        chunk = []
                if chunk:
                    self.db.executemany(sql, chunk)
                    self.db.executemany(also, [(verb, a, r[0], r[1], a) for r in chunk])
        return self.db.execute(f"SELECT COUNT(*) FROM {_q(table)}").fetchone()[0] - before

    def gone(self, being, sid, *, by, why, at=None):
        """Take the statement `(being, id)` out, recording who, when and why."""
        st = self.statement(being, sid)
        if st is None:
            raise StoreError(f"{being}#{sid} is kept nowhere in this store")
        if not (isinstance(why, str) and why.strip()):
            raise StoreError("a statement leaves a store with its reason (`why`)")
        verb, roles = st
        n = self._being_row(being)[0]
        with self.batch():
            row = self.db.execute(f"SELECT n FROM {_q('v_' + _col(verb))} WHERE being=? AND id=?", (n, sid)).fetchone()
            self.db.execute('DELETE FROM known_also WHERE verb=? AND row=?', (verb, row[0]))
            self.db.execute(f"DELETE FROM {_q('v_' + _col(verb))} WHERE n=?", (row[0],))
            self.db.execute('INSERT INTO gone (verb, being, id, form, by, at, why) VALUES (?, ?, ?, ?, ?, ?, ?)',
                            (verb, being, sid, canonical(verb, roles), by, at or now(), why))

    # -------------------------------------------------------------------------------------------- between keepings
    def export(self, being, *, by, ids=None, into=None):
        """The rows of `being` as statements for its bean, each known there by one act the export adds: `derive`, by
        `by`, from the acts that knew the rows, at the save's moment. What the bean holds already is left out. Returns
        ([statements as {verb: roles}], the act, or None when nothing is new)."""
        bean = self.bean(being) if into is None else into
        have = set()
        if bean is not None:
            for _i, v, r in bean.items:
                nr = self.normalize(being, v, r)
                have.add(canonical(v, nr))
                if isinstance(r.get('id'), str):
                    have.add((v, r['id']))
        out, acts, sids = [], [], []
        for verb, roles, known in self.get(being):
            sid = roles['id']
            if ids and sid not in ids:
                continue
            if verb in self.law.knowing:
                continue                     # an act of the store stays its own: the bean knows by its own act
            plain = {k: v for k, v in roles.items() if k != 'id'}
            if canonical(verb, plain) in have or (verb, sid) in have:
                continue
            r = self.denormalize(being, verb, roles)
            out.append({verb: r})
            sids.append(sid)
            for a in known:
                if a not in acts:
                    acts.append(a)
        if not out:
            return [], None
        frm = [self._denorm(a, being, ['statement']) for a in acts] or ['unknown']
        act = {'derive': {'by': by, 'of': sids, 'from': frm, 'at': 'now',
                          'note': f"exported from the store `{self.name}` (bin/store.py export)"}}
        return out, act

    def import_bean(self, bean_id, *, judge=True):
        """Keep the statements of the bean `bean_id` here, each known by the act of the bean that covers it (named by
        its id, or the digest of its form), and those acts as rows too. Sealed statements stay in git. Returns the
        number of statements kept."""
        b = self.garden.beans.get(bean_id)
        if b is None or b.unread:
            raise StoreError(f"no bean {bean_id} is read in this garden")
        J = engine.Judge(self.law, self.garden)
        self.being(bean_id, b.kind, b.header.get('title'), b.header.get('summary'))

        def ref(verb, r):
            return f"{bean_id}#{r['id'] if isinstance(r.get('id'), str) else mint(verb, self.normalize(bean_id, verb, r))}"

        n = 0
        with self.batch():
            for i, verb, r in b.items:              # the acts first: a row names an act kept
                if verb in self.law.knowing and 'held' not in r:
                    self.put(bean_id, verb, r, judge=judge)
                    n += 1
            for i, verb, r in b.items:
                if verb in self.law.knowing or 'held' in r:
                    continue
                acts = [ref(v, rr) for v, rr in J._acts_of(b, i, r)]
                if not acts:
                    raise StoreError(f"{bean_id}[{i}] {verb} is known by no act in its bean")
                sid = None
                for a in acts:
                    sid = self.put(bean_id, verb, r, act=a, judge=judge)
                n += 1
        return n

    def series_import(self, bean_id, key, part):
        """Keep a series' part here byte for byte (`series/<bean>/<key>/<part>.tsv`)."""
        p = os.path.join(self.root, 'series', bean_id, key, part + '.tsv')
        with open(p, 'rb') as fh:
            data = fh.read()
        sha = hashlib.sha256(data).hexdigest()
        with self.batch():
            have = self.db.execute('SELECT sha256 FROM series_part WHERE being=? AND key=? AND part=?',
                                   (bean_id, key, part)).fetchone()
            if have and have[0] != sha:
                raise StoreError(f"the part {bean_id}/{key}/{part} is kept here with other bytes: a part, once "
                                 f"written, stays as it is (rule `kept`)")
            self.db.execute('INSERT OR IGNORE INTO series_part (being, key, part, sha256, bytes) VALUES (?, ?, ?, ?, ?)',
                            (bean_id, key, part, sha, data))
        return sha

    def series_export(self, bean_id, key, part, dest=None):
        r = self.db.execute('SELECT sha256, bytes FROM series_part WHERE being=? AND key=? AND part=?',
                            (bean_id, key, part)).fetchone()
        if not r:
            raise StoreError(f"no part {bean_id}/{key}/{part} is kept here")
        data = bytes(r[1])
        if hashlib.sha256(data).hexdigest() != r[0]:
            raise StoreError(f"the part {bean_id}/{key}/{part} no longer has the bytes it was kept with")
        if dest:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as fh:
                fh.write(data)
        return data

    # -------------------------------------------------------------------------------------------- reading
    def query(self, sql, params=()):
        """Rows of a read-only query over this store's relations."""
        ro = sqlite3.connect(f"file:{self.path}?mode=ro", uri=True, timeout=60)
        try:
            ro.execute('PRAGMA query_only=ON')
            cur = ro.execute(sql, params)
            return [d[0] for d in cur.description or []], cur.fetchall()
        finally:
            ro.close()

    def snapshot(self, pages=2048):
        """A copy of the whole store in memory, read in steps so a writer is held up only between them: for a long
        read of a store another user reads (memory: live SQLite reads)."""
        mem = sqlite3.connect(':memory:')
        self.db.backup(mem, pages=pages, sleep=0.005)
        return mem


def _me():
    try:
        import pwd
        return pwd.getpwuid(os.getuid()).pw_name
    except Exception:
        return os.environ.get('USER', '')


# ------------------------------------------------------------------------------------------------ the check
def check(stores, *, root=ROOT, law=None, garden=None):
    """[(rule, where, message)] of the union of git and `stores`, by the one judge (core/judge.py, the scope `union`):
    git's own findings, then what the stores add to them."""
    from core import judge as dmjudge
    garden = garden or engine.Garden.read(root)
    if law is None:
        law = dmjudge.garden_law(root, dmjudge.carried(root))
    for s in stores:
        s._law, s._garden, s._judge = law, garden, None
    with one_snapshot(stores):
        return dmjudge.judge(law, dmjudge.Scope.union(garden, lambda law, garden, base: _check(stores, garden, law, base),
                                                      root=root))


@contextlib.contextmanager
def one_snapshot(stores):
    """Every read of `stores` through one connection, each store's file attached to it read-only under `s<k>`, in one
    transaction begun by reading each: one snapshot of each store for the whole check — its queries, its union's SQL
    and the engine's reading of its rows alike — so a writer at work is seen before or after, whole, and the same by
    each. A store with a write of its own open is read through its own connection, which alone sees that write."""
    if not stores or any(s._depth for s in stores):
        yield None
        return
    db = sqlite3.connect('file::memory:', uri=True, isolation_level=None)
    was = [(s.db, s._s) for s in stores]
    try:
        for k, s in enumerate(stores):
            db.execute(f"ATTACH DATABASE ? AS s{k}", (_uri(s.path, 'ro'),))
        db.execute('BEGIN')
        for k in range(len(stores)):
            db.execute(f"SELECT COUNT(*) FROM s{k}.sqlite_master").fetchone()
        for k, s in enumerate(stores):
            s.db, s._s = db, f"s{k}."
        yield db
    finally:
        for s, (sdb, sch) in zip(stores, was):
            s.db, s._s = sdb, sch
        if db.in_transaction:
            db.execute('ROLLBACK')         # nothing was written: the check only reads
        db.close()


def _check(stores, garden, law, base):
    """What the stores add to git's own findings (`base`)."""
    out = []
    for s in stores:
        out += _kinds(s, garden)
    out += _acts_resolve(stores)
    out += _overlaps(stores, garden, law)
    out += _pointers(stores, garden)
    size = {s.name: s.count() + s.db.execute(f'SELECT COUNT(*) FROM {s._s}being').fetchone()[0] for s in stores}
    total = sum(size.values())
    if total <= UNION_ROWS:
        out += _union_judged(stores, garden, law, base)
        return out
    # EACH STORE SMALL ENOUGH IS JUDGED WHOLE, beside git, alone: a large one beside it does not put the small one into
    # the queries' mode; the rules that span stores are judged by queries over all of them
    large = [s for s in stores if size[s.name] > UNION_ROWS]
    for s in stores:
        if s not in large:
            out += _union_judged([s], garden, law, base)
    with compiled(stores, garden, law) as U:        # EVERY RULE THAT IS A READING, by its SQL over the whole union
        found, unjudged = _readings(U, law, base)
        out += found
        out += _names_given(U, garden, law, base)
        for k, s in enumerate(stores):              # EVERY ROW OF A LARGE STORE, as its put judges one
            if s in large:
                out += _rows_judged(U, k, s)
    read = [r for r in (getattr(law, 'readings', None) or {}) if r not in dict(unjudged)]
    rest = [r for r in law.rules if r not in read and r not in QUERIED]
    if rest:
        out.append(('size', ', '.join(s.name for s in large),
                    f"{sum(size[s.name] for s in large)} rows: judged over the union by their readings, as SQL "
                    f"(core/union.py): {', '.join(read) or 'none'}; by its queries: knowing (each act a row names), "
                    f"names (a name a namespace gives once), form (each being's kind, one form an id, each pointer); "
                    f"every row as its put judges one (`row_findings`, found set-wise): form, valency and frame, names (a "
                    f"name's form) and harm (a row's clauses); not judged over the union at this size: {', '.join(rest)}"
                    + ''.join(f"; {r}'s reading has no SQL form here ({why})" for r, why in unjudged)))
    seen, kept = set(), []
    for f in out:                                      # a finding the engine and a query both make is said once
        if f not in seen:
            seen.add(f)
            kept.append(f)
    return kept


# EVERY ROW OF A LARGE STORE, AS ITS PUT JUDGES ONE (the next version's nv-s6-open, item 3). A load of many rows judges a
# sample at its put (`bulk`, an import set-wise); the check judges every row. Which rows the put would refuse is found
# set-wise, a superset of them: by SQL, what a row's columns alone decide; by the engine's own code, once for each set of
# columns a relation's rows fill and once for each distinct filler of a column — a being kept in a store by the kind it is
# kept as, any other value by itself — and each distinct name a namespace gives. Each row so found is judged again by the
# put's own judgement (`Store.row_findings`), told at its place in the union, in the put's words; a row that passes it
# is said nothing of. A row the union does not hold (git, or a store before it, holds the same statement) is judged where
# that statement is held.
_GLOBS = {}


def _glob(name):
    """A GLOB character class of what a check of the law matches one character at a time — `control`, a control
    character as core/engine.py's row clause reads it (the tab apart, and NUL, which a GLOB cannot hold), `bidi`, a
    bidi control — made by asking that check of every character once."""
    if name not in _GLOBS:
        if name == 'control':
            hit = [c for c in range(1, 0x110000) if c != 9 and engine.dmparse.CONTROL.match(chr(c))]
        else:
            hit = sorted(ord(c) for c in engine.dmparse.BIDI_CONTROL)
        ranges, start = [], None
        for i, c in enumerate(hit):
            if start is None:
                start = c
            if i + 1 == len(hit) or hit[i + 1] != c + 1:
                ranges.append(chr(start) if start == c else f"{chr(start)}-{chr(c)}")
                start = None
        _GLOBS[name] = '*[' + ''.join(ranges) + ']*'
    return _GLOBS[name]


def _rows_judged(U, k, s):
    """[(rule, where, message)] of every row of store `s` (the union's keeping `k`) its put would refuse: found
    set-wise (`_suspects`), each judged again as its put judges one (`Store.row_findings`), at its place in the union."""
    out = []
    skip = U.K[k].skip
    for verb in s.verbs():
        table = s._t('v_' + _col(verb))
        for n in sorted(_suspects(s, verb, table)):
            if (verb, n) in skip:
                continue
            sid, being = s.db.execute(f"SELECT t.id, b.id FROM {table} t JOIN {s._s}being b ON b.n = t.being "
                                      f"WHERE t.n = ?", (n,)).fetchone()
            _v, r = s.statement(being, sid)
            i = U.index(k + 1, being, verb, n)
            out += s.row_findings(being, verb, r, i=i, place=f"{being}[{i}] {verb}")
    return out


def _suspects(s, verb, table):
    """The rows (their `n`) of `verb` in store `s` its put may refuse: every row it refuses, and maybe others."""
    J, law = s.judge, s.law
    v = law.verbs.get(verb)
    rows = lambda where='', args=(): {n for (n,) in s.db.execute(f"SELECT t.n FROM {table} t {where}", args)}  # noqa
    if v is None:
        return rows()                                  # no verb of the law: every row
    cols = s.columns(verb)
    shapes = {**(v.get('roles') or {}), **(v.get('qualifiers') or {})}
    required = set(listed(v.get('required'))) | set(listed((v.get('choice') or {}).get('one_of')))
    filled = {key: (f"({bc} IS NOT NULL OR {tc} IS NOT NULL)" if bc else f"({tc} IS NOT NULL)")
              for key, (bc, tc) in cols.items()}
    filled.update({key: f"(c_{key} IS NOT NULL)" for key in BESIDE})
    out = set()
    # THE COLUMNS A ROW FILLS: a role its verb's row has not, a required role left out, a choice — the engine's own
    # `keys`, asked once of each set of columns the rows fill
    keys = list(filled)
    sets = s.db.execute(f"SELECT DISTINCT {', '.join(filled[x] for x in keys)} FROM {table}").fetchall()
    for got in sets:
        J.out = []
        held = {x: True for x, on in zip(keys, got) if on}
        J.keys('x', verb, v, held)
        J.keys('x', verb, v, held, counted=True)
        said, J.out = bool(J.out), []
        if said:
            out |= rows('WHERE ' + ' AND '.join(filled[x] if on else f"NOT {filled[x]}" for x, on in zip(keys, got)))
    # PROSE BESIDE IT, AND WHAT IT IS HELD WHILE: `why` and `note` are text; a `while` is read by the engine row by row
    out |= rows("WHERE (c_why IS NOT NULL AND typeof(c_why) != 'text') OR (c_note IS NOT NULL AND typeof(c_note) != "
                "'text') OR c_while IS NOT NULL")
    # A CONTROL CHARACTER in a text it holds, its id among them
    texts = ['id'] + [tc for _bc, tc in cols.values()] + [f"c_{x}" for x in BESIDE]
    cond = ' OR '.join(f"(typeof({c}) = 'text' AND ({c} GLOB ? OR instr({c}, char(0)) > 0))" for c in texts)
    out |= rows('WHERE ' + cond, tuple(_glob('control') for _c in texts))
    # A CODE OF A SCHEME MARKED SPECIAL-CATEGORY, wherever it holds one
    for scheme in sorted(J._marked()):
        out |= rows('WHERE ' + ' OR '.join(f"instr(CAST({tc} AS TEXT), ?) > 0" for _bc, tc in cols.values()),
                    tuple(scheme + ':' for _c in cols))
    # EACH FILLER, by the engine's own `fill`: once a kind for a being kept in a store and named nowhere else, once a
    # value for any other
    s.db.execute("CREATE TEMP TABLE IF NOT EXISTS rj_named (id TEXT PRIMARY KEY)")    # named elsewhere than here
    s.db.execute("DELETE FROM temp.rj_named")
    s.db.executemany("INSERT OR IGNORE INTO temp.rj_named VALUES (?)",
                     ((x,) for x in set(law.crown) | {'self', 'now', 'unknown'} | set(s.garden.beans)))
    s.db.execute("CREATE TEMP TABLE IF NOT EXISTS rj_bad (v)")       # the values of a column the put refuses

    def bad_rows(column, values, where=''):
        """The rows whose `column` holds one of `values`, read in one pass."""
        s.db.execute("DELETE FROM temp.rj_bad")
        s.db.executemany("INSERT INTO temp.rj_bad VALUES (?)", ((x,) for x in values))
        return rows(f"WHERE {where}{column} IN (SELECT v FROM temp.rj_bad)")
    first = s.db.execute(f"SELECT b.id FROM {table} t JOIN {s._s}being b ON b.n = t.being ORDER BY t.n LIMIT 1").fetchone()
    if first is None:
        return out
    b = engine.Bean(first[0], header={'bean': first[0], 'kind': s.kind_of(first[0]), 'statements': []})
    for key, (bc, tc) in cols.items():
        spec = shapes.get(key)
        if spec is None:
            continue                                   # a role its row has not: the columns above
        req = key in required

        def refused(value):
            """Whether the engine's `fill` refuses `value` in this role: of no row but through `self` or a statement
            of its own bean, which are read row by row (below)."""
            J.out = []
            J.fill('x', key, spec, value, req, b)
            said, J.out = bool(J.out), []
            return said
        if bc:
            elsewhere = f"(f.id IN (SELECT id FROM temp.rj_named) OR f.id LIKE 'store:%')"
            for kind, n in s.db.execute(f"SELECT f.kind, MIN(t.n) FROM {table} t JOIN {s._s}being f ON f.n = t.{bc} "
                                        f"WHERE NOT {elsewhere} GROUP BY f.kind").fetchall():
                x = s.db.execute(f"SELECT f.id FROM {table} t JOIN {s._s}being f ON f.n = t.{bc} WHERE t.n = ?",
                                 (n,)).fetchone()[0]
                if refused(x):                         # kept here alone: as the kind it is kept as
                    out |= rows(f"JOIN {s._s}being f ON f.n = t.{bc} WHERE f.kind IS ?", (kind,))
            for (x,) in s.db.execute(f"SELECT DISTINCT f.id FROM {s._s}being f WHERE {elsewhere} AND EXISTS (SELECT 1 "
                                     f"FROM {table} t WHERE t.{bc} = f.n)").fetchall():
                if refused(x):                         # a being named elsewhere too: by itself
                    out |= rows(f"JOIN {s._s}being f ON f.n = t.{bc} WHERE f.id = ?", (x,))
        any_text = 'text' in shapes_of(spec) and spec.get('keyed') != engine.TRUE
        if any_text:                                   # any string is text: only `now`, `unknown` and `self` say anything
            values = s.db.execute(f"SELECT DISTINCT {tc} FROM {table} WHERE typeof({tc}) = 'text' AND {tc} IN "
                                  f"('now', 'unknown', 'self') UNION SELECT DISTINCT {tc} FROM {table} WHERE {tc} IS "
                                  f"NOT NULL AND typeof({tc}) != 'text'")
        else:
            values = s.db.execute(f"SELECT DISTINCT {tc} FROM {table} WHERE {tc} IS NOT NULL")
        bad, each = [], {}
        many = spec.get('many') == engine.TRUE

        def own(x):                                    # its own bean: read row by row (a statement of it written
            return x == 'self'                         # without `#` is refused below by the bean that holds none)

        def item(x):
            """Whether a list's item is refused: `fill` refuses a list where it refuses one of its items alone, and a
            row's clause where an item is a text holding a control character — each item asked once."""
            key = json.dumps(x, sort_keys=True, ensure_ascii=False)
            if key not in each:
                each[key] = own(x) or refused([x]) or (isinstance(x, str) and bool(
                    engine.dmparse.CONTROL.search(x.replace('\t', ''))))
            return each[key]
        for (raw,) in values:
            value = json.loads(raw) if isinstance(raw, bytes) else raw
            if isinstance(value, list) and value and many:
                if any(item(x) for x in value):
                    bad.append(raw)
            elif own(value) or refused(value) or (isinstance(value, list) and any(
                    isinstance(x, str) and engine.dmparse.CONTROL.search(x.replace('\t', '')) for x in value)):
                bad.append(raw)
        if bad:
            out |= bad_rows(tc, bad)
    # A NAME'S FORM (rule `names`, the engine's `name_form`), and a name kept only in the held store
    if verb == 'name' and 'by' in cols and 'as' in cols:
        by, nm = cols['by'][1], cols['as'][1]
        held = sorted(x for x, r in law.namespaces.items() if (r or {}).get('kept') == 'held')
        if held:
            out |= rows(f"WHERE {by} IN ({', '.join('?' * len(held))})", tuple(held))
        out |= rows(f"WHERE typeof({nm}) = 'text' AND {nm} GLOB ?", (_glob('bidi'),))
        shaped = sorted(x for x, r in law.namespaces.items() if (r or {}).get('pattern') and x not in ('garden-id', 'garden'))
        ns_of = f"COALESCE({by}, (SELECT id FROM {s._s}being WHERE n = {cols['by'][0]}))" if cols['by'][0] else by
        for ns in shaped:
            bad = [name for (name,) in s.db.execute(f"SELECT DISTINCT {nm} FROM {table} WHERE {ns_of} = ? AND {nm} IS "
                                                    f"NOT NULL", (ns,))
                   if J.name_form({'by': ns, 'as': json.loads(name) if isinstance(name, bytes) else name})[0]]
            if bad:
                out |= bad_rows(nm, bad, f"{ns_of} = '{ns}' AND ")
    s.db.execute("DROP TABLE IF EXISTS temp.rj_named")
    s.db.execute("DROP TABLE IF EXISTS temp.rj_bad")
    return out


def _kinds(s, garden):
    """Each being a store keeps, its kind against its bean's, and one kept with no kind that no bean gives one and that
    has rows: found set-wise, in the order the store keeps its beings."""
    s.db.execute("CREATE TEMP TABLE IF NOT EXISTS rj_git (id TEXT PRIMARY KEY, kind TEXT)")
    s.db.execute("DELETE FROM temp.rj_git")
    s.db.executemany("INSERT INTO temp.rj_git VALUES (?, ?)", ((b.id, b.kind) for b in garden.beans.values()))
    has = ' OR '.join(f"EXISTS (SELECT 1 FROM {s._t('v_' + _col(v))} WHERE being = b.n)" for v in s.verbs()) or '0'
    out = []
    for bid, kind, bean, gkind in s.db.execute(
            f"SELECT b.id, b.kind, g.id IS NOT NULL, g.kind FROM {s._s}being b LEFT JOIN temp.rj_git g ON g.id = b.id "
            f"WHERE (g.id IS NOT NULL AND b.kind IS NOT NULL AND b.kind != '' AND g.kind IS NOT b.kind) OR "
            f"(g.id IS NULL AND b.kind IS NULL AND ({has})) ORDER BY b.n").fetchall():
        if bean:
            out.append(('form', f"{s.name}:{bid}", f"kept as `{kind}`, and its bean is a `{gkind}`"))
        else:
            out.append(('form', f"{s.name}:{bid}", "kept with no kind, and no bean gives it one"))
    s.db.execute("DROP TABLE temp.rj_git")
    return out


def _has_rows(s, bid):
    n = s._being_row(bid)
    return n is not None and any(s.db.execute(f"SELECT 1 FROM {s._t('v_' + _col(v))} WHERE being=? LIMIT 1",
                                              (n[0],)).fetchone() for v in s.verbs())


def _acts_resolve(stores):
    """Rule `knowing` at a store's rows: each act a row is known by (its `known`, each of `known_also`) is a knowing act
    kept in a store here or in git. An act no row names — every row it knew taken out (`gone`) — knows nothing here,
    and is not asked."""
    out = []
    for s in stores:
        named = ' UNION '.join([f"SELECT known FROM {s._t('v_' + _col(v))}" for v in s.verbs()] +
                               [f"SELECT act FROM {s._s}known_also"])
        acts = s.db.execute(f"SELECT n, ref FROM {s._s}act WHERE n IN ({named}) ORDER BY n").fetchall()
        kept = [_kept_as(s, t, acts) for t in stores]
        for n, ref in acts:
            hit = None
            for t, k in zip(stores, kept):
                if k is None:
                    hit = t.resolve(ref)
                elif REF.match(ref):              # the store's own statement, found set-wise, else its bean's in git
                    hit = ('store', k[n]) if n in k else t._in_git(*REF.match(ref).groups())
                if hit:
                    break
            if hit is None:
                out.append(('knowing', f"{s.name}", f"rows are known by {ref}, which is kept nowhere this host reads"))
            elif hit[1] not in s.law.knowing:
                out.append(('knowing', f"{s.name}", f"rows are known by {ref}, a `{hit[1]}`: no knowing act"))
    return out


def _kept_as(s, t, acts):
    """{act n: verb} of each act of store `s` (`acts`, [(n, ref)]) that names a statement store `t` keeps, found
    set-wise, as `Store.statement` finds one: the first verb, in `t`'s order, whose relation holds `(being, id)`. None
    where the two are not read through one connection (`one_snapshot`), and each act is asked by itself."""
    if not acts or not (s._s and t._s and s.db is t.db):
        return None
    s.db.execute("CREATE TEMP TABLE IF NOT EXISTS rj_acts (n INTEGER PRIMARY KEY, being TEXT, id TEXT)")
    s.db.execute("DELETE FROM temp.rj_acts")
    s.db.executemany("INSERT INTO temp.rj_acts VALUES (?, ?, ?)",
                     ((n,) + REF.match(ref).groups() for n, ref in acts if isinstance(ref, str) and REF.match(ref)))
    out = {}
    for v in t.verbs():
        for (n,) in s.db.execute(f"SELECT a.n FROM temp.rj_acts a JOIN {t._s}being b ON b.id = a.being JOIN "
                                 f"{t._t('v_' + _col(v))} r ON r.being = b.n AND r.id = a.id"):
            out.setdefault(n, v)
    s.db.execute("DROP TABLE temp.rj_acts")
    return out


def _overlaps(stores, garden, law):
    """One `(being, id)`, one form, across git and every store."""
    out = []
    for s in stores:
        for (bid,) in s.db.execute(f'SELECT id FROM {s._s}being'):
            bean = garden.beans.get(bid)
            if bean is None:
                continue
            ids = {}
            for _i, v, r in bean.items:
                if 'held' in r:
                    continue
                sid = r['id'] if isinstance(r.get('id'), str) else mint(v, s.normalize(bid, v, r))
                ids[sid] = (v, s.normalize(bid, v, r))
            for verb, roles in _rows_of_ids(s, bid, ids):
                sid = roles['id']
                if sid in ids:
                    gv, gr = ids[sid]
                    plain = {k: x for k, x in roles.items() if k != 'id'}
                    gplain = {k: x for k, x in gr.items() if k != 'id'}
                    if gv != verb or canonical(gv, gplain) != canonical(verb, plain):
                        out.append(('form', f"{bid}#{sid}", f"its bean and the store `{s.name}` keep two statements "
                                                            f"under one id: a person settles which (MERGE.md 6)"))
    return out


def _pointers(stores, garden):
    """Every `store:<kind>:<id>` in git names a being a store here keeps, of that kind (and the statement, with `#`)."""
    out = []
    for b in garden.beans.values():
        for i, verb, r in b.items:
            for k, v in r.items():
                for x in (v if isinstance(v, list) else [v]):
                    m = POINTER.match(x) if isinstance(x, str) else None
                    if not m:
                        continue
                    kind, bid, sid = m.groups()
                    hit = next((s for s in stores if s.has_being(bid)), None)
                    if hit is None and bid not in garden.beans:
                        out.append(('names', f"{b.id}[{i}] {verb}", f"`{k}`: {x} names a being no store here keeps"))
                        continue
                    k2 = hit.kind_of(bid) if hit else garden.beans[bid].kind
                    if k2 and k2 != kind:
                        out.append(('names', f"{b.id}[{i}] {verb}", f"`{k}`: {x} — {bid} is kept as `{k2}`"))
                    if sid and not any(s.statement(bid, sid) for s in stores) and not (
                            bid in garden.beans and sid in garden.beans[bid].ids):
                        out.append(('names', f"{b.id}[{i}] {verb}", f"`{k}`: {x} names a statement kept nowhere here"))
    return out


def _rows_of_ids(s, bid, ids):
    """[(verb, roles with their id)] of the rows of `bid` a store keeps under one of `ids`, in the order `get` gives
    them (by verb, then as put): each found by its `(being, id)`, never by reading every row of the being — a series'
    millions of observations, of which its bean names a few."""
    r = s._being_row(bid)
    if not r or not ids:
        return []
    out = []
    for verb in s.verbs():
        table = s._t('v_' + _col(verb))
        names = [c[1] for c in s.db.execute(f"PRAGMA {s._s}table_info({_q('v_' + _col(verb))})")]
        got = []
        for sid in ids:
            row = s.db.execute(f"SELECT {', '.join(_q(c) for c in names)} FROM {table} WHERE being=? AND id=?",
                               (r[0], sid)).fetchone()
            if row:
                rid, roles, _known, n, _b = s._decode(verb, row, names)
                got.append((n, dict(roles, id=rid)))
        out += [(verb, roles) for _n, roles in sorted(got, key=lambda x: x[0])]
    return out


def _plainid(x):
    """A filler with every pointer read as the plain id it names: in the union every being is one id."""
    if isinstance(x, list):
        return [_plainid(v) for v in x]
    if isinstance(x, dict):
        return {k: _plainid(v) for k, v in x.items()}
    m = POINTER.match(x) if isinstance(x, str) else None
    return (f"{m.group(2)}#{m.group(3)}" if m.group(3) else m.group(2)) if m else x


def _plain_statements(statements):
    return [{v: {k: _plainid(x) for k, x in r.items()}} if isinstance(r, dict) else {v: r}
            for st in statements if isinstance(st, dict) and len(st) == 1 for v, r in st.items()]


def _union_garden(stores, garden):
    """(G, added): the union of git and `stores`, read as beans — every bean of git, a pointer in it read as the plain
    id; each being a store keeps, a bean, its rows its statements after git's own, each a statement no keeping before
    it holds — and, for each bean a store added to, the index from which its statements are the store's."""
    G = garden.copy()
    added = {}                               # bean id -> index from which its statements are the store's
    for bid, bean in list(G.beans.items()):  # a bean that names a being by a pointer, read with the plain id
        if bean.unread or 'store:' not in json.dumps(bean.statements, default=str):
            continue
        G.beans[bid] = engine.Bean(bid, path=bean.path, header=dict(bean.header, statements=_plain_statements(
            bean.statements)), raw=None)
    for s in stores:
        for (bid, kind, title, summary) in s.db.execute(f'SELECT id, kind, title, summary FROM {s._s}being').fetchall():
            rows = s.get(bid)
            bean = G.beans.get(bid)
            if not rows and (bean is not None or bid in added):
                continue
            if bean is not None:
                have = {canonical(v, s.normalize(bid, v, r)) for _i, v, r in bean.items}
                ids = {r.get('id') for _i, v, r in bean.items}
                extra = [{v: _plainid(s.denormalize(bid, v, r))} for v, r, _a in rows
                         if canonical(v, {k: x for k, x in r.items() if k != 'id'}) not in have and r['id'] not in ids]
                if not extra:
                    continue
                header = dict(bean.header, statements=list(bean.statements) + extra)
                added[bid] = len(bean.statements)
            else:
                k = kind or 'document'
                header = {'bean': bid, 'kind': k, 'title': title or bid,
                          'statements': [{v: _plainid(s.denormalize(bid, v, dict(r)))} for v, r, _a in rows]}
                if summary:
                    header['summary'] = summary
                added[bid] = 0
            nb = engine.Bean(bid, path=(bean.path if bean is not None else None), header=header, raw=None)
            G.beans[bid] = nb
    return G, added


def _union_judged(stores, garden, law, base):
    """The union of git and the stores, judged whole by the core's engine: every finding git alone does not have, and
    none of `knowing` at a store's row (a row names its act; `_acts_resolve` judges it). In the union every being is a
    bean, so every filler is its plain id."""
    G, added = _union_garden(stores, garden)
    if not added:
        return []
    from core import judge as dmjudge
    base = set(base)                                  # git's own findings (the law's own problems among them)
    out = []
    for rule, where, msg in dmjudge.judge(law, dmjudge.Scope.tree(garden=G)):
        if (rule, where, msg) in base:
            continue
        m = re.match(r'^([a-z0-9][a-z0-9._-]*)\[(\d+)\]', where)
        if rule == 'knowing' and m and m.group(1) in added and int(m.group(2)) >= added[m.group(1)]:
            continue
        if rule == 'knowing' and where in added and added[where] == 0:
            continue
        out.append((rule, where, msg))
    return out


def _rows_n(s, bid):
    """[(verb, n, roles with their id)] of every row of `bid` a store keeps, in the order `get` gives them."""
    r = s._being_row(bid)
    if not r:
        return []
    out = []
    for verb in s.verbs():
        cur = s.db.execute(f"SELECT * FROM {s._t('v_' + _col(verb))} WHERE being=? ORDER BY n", (r[0],))
        names = [d[0] for d in cur.description]
        for row in cur.fetchall():
            sid, roles, _known, n, _b = s._decode(verb, row, names)
            out.append((verb, n, dict(roles, id=sid)))
    return out


def _kept_by(s, bid):
    return s.db.execute(f'SELECT 1 FROM {s._s}being WHERE id=?', (bid,)).fetchone() is not None


def _skips(stores, garden):
    """For each store, the rows (verb, n) the union does not hold, as `_union_garden` reads it: a row whose statement
    its being's bean, or a store before it, holds already — one form, or one id. Only a being git has a bean for, or
    two stores keep, can have one."""
    skips = [set() for _ in stores]
    both = {bid for bid in garden.beans if any(_kept_by(s, bid) for s in stores)}
    for k, s in enumerate(stores):                    # a being two stores keep: read from the one keeping fewer
        for e in stores[:k]:
            small, big = sorted((s, e), key=lambda x: x.db.execute(f'SELECT COUNT(*) FROM {x._s}being').fetchone()[0])
            both |= {bid for (bid,) in small.db.execute(f'SELECT id FROM {small._s}being') if _kept_by(big, bid)}
    for bid in sorted(both):
        bean = garden.beans.get(bid)
        items = None
        if bean is not None:
            if not bean.unread and 'store:' in json.dumps(bean.statements, default=str):
                bean = engine.Bean(bid, header=dict(bean.header, statements=_plain_statements(bean.statements)))
            items = [(v, r) for _i, v, r in bean.items]
        for k, s in enumerate(stores):
            if not _kept_by(s, bid):
                continue
            rows = _rows_n(s, bid)
            if items is None:                         # the first keeping of a being git has no bean for: all its rows
                items = [(v, _plainid(s.denormalize(bid, v, r))) for v, _n, r in rows]
                continue
            have = {canonical(v, s.normalize(bid, v, r)) for v, r in items}
            ids = {r.get('id') for v, r in items}
            kept = []
            for v, n, r in rows:
                if canonical(v, {x: y for x, y in r.items() if x != 'id'}) not in have and r['id'] not in ids:
                    kept.append((v, _plainid(s.denormalize(bid, v, r))))
                else:
                    skips[k].add((v, n))
            items = items + kept
    return skips


@contextlib.contextmanager
def compiled(stores, garden, law):
    """The union of git and `stores` as core/union.py reads it: each store's file attached read-only under `s<k>`, in
    one transaction — the check's one connection where the stores are read through it (`one_snapshot`), else a
    connection of its own; the Union over them."""
    from core import union as dmunion
    shared = bool(stores) and all(s._s and s.db is stores[0].db for s in stores)   # the check's one connection
    db = stores[0].db if shared else sqlite3.connect('file::memory:', uri=True, isolation_level=None)
    try:
        if not shared:
            for k, s in enumerate(stores):
                db.execute(f"ATTACH DATABASE ? AS s{k}", (_uri(s.path, 'ro'),))
            db.execute('BEGIN')
        keeps = []
        for k, (s, skip) in enumerate(zip(stores, _skips(stores, garden))):
            verbs = s.verbs()
            keeps.append(dmunion.Keeping(s._s[:-1] if shared else f"s{k}", verbs, {v: 'v_' + _col(v) for v in verbs},
                                         {v: s.columns(v) for v in verbs}, {v: s.shapes(v) for v in verbs}, skip))
        U = dmunion.Union(db, engine.Judge(law, garden), keeps)
        try:
            yield U
        finally:
            U.close()
    finally:
        if not shared:
            db.close()


def _readings(U, law, base):
    """([(rule, where, message)], [(rule, why)]): what each rule that is a reading of the law refuses over the union,
    by its SQL (core/union.py), with what git alone finds left out; and each such rule whose reading has no SQL form
    there, with the step that has none."""
    from core import union as dmunion
    out, unjudged = [], []
    for rule, reading in (getattr(law, 'readings', None) or {}).items():
        try:
            found = U.refusals(reading, rule)
        except dmunion.NoSQL as e:
            unjudged.append((rule, str(e)))
            continue
        except dmunion.reckon.Refused as e:         # as the engine says a reading it cannot read (core/engine.py)
            found = [('core.yaml', f"its reading cannot be read here: {e}")]
        out += [(rule, where, msg) for where, msg in found if (rule, where, msg) not in base]
    return out, unjudged


def _names_given(U, garden, law, base):
    """Rule `names`' once clause over the union, by the engine's own (core/engine.py `names`): a name a namespace
    gives once, given in a store, where over the union it names more than one being. The SQL finds those names; the
    engine says the refusal."""
    once = sorted(n for n, r in law.namespaces.items() if r.get('once') == 'true')
    st = U.statements('name')
    w = {k: _q(st.cols[k][0]) for k in ('by', 'as', 'held')}
    n_of, marks = _q(st.cols['of'][1]), ','.join('?' * len(once))
    given = (f"FROM {_q(st.name)} WHERE typeof({w['by']}) = 'text' AND {w['by']} IN ({marks}) AND {w['held']} IS NULL "
             f"AND ({w['as']} IS NULL OR {w['as']} != 'unknown')")
    many = U.db.execute(f"SELECT {w['by']}, {w['as']} {given} GROUP BY {w['by']}, {w['as']} "
                        f"HAVING COUNT(DISTINCT {n_of}) > 1 AND MAX(_src) > 0", once).fetchall()
    if not many:
        return []
    U.db.execute("CREATE TEMP TABLE u_many (ns, nm)")
    U.db.executemany("INSERT INTO u_many VALUES (?, ?)", many)
    from core import union as dmunion
    also = []
    for ns, nm, of, src, bean, verb, i, bo1, bo2 in U.db.execute(
            f"SELECT {w['by']}, {w['as']}, {n_of}, _src, _bean, _verb, _i, _bo1, _bo2 {given} AND _src > 0 AND "
            f"EXISTS (SELECT 1 FROM u_many WHERE ns = {w['by']} AND nm IS {w['as']}) ORDER BY _bo1, _bo2, _src, _vr, _i",
            once).fetchall():
        k = U.index(src, bean, verb, i)
        also.append((ns, dmunion.dec(nm), of, f"{bean}[{k}] {verb}", (bo1, bo2, k)))
    U.db.execute("DROP TABLE temp.u_many")
    J = engine.Judge(law, garden)
    J.names(also=also)
    return [(r, wh, m) for r, wh, m in J.out if r == 'names' and (r, wh, m) not in base]


def union_of(being, stores, *, garden=None):
    """Every statement of `being`, wherever it is kept — its bean and each store — as one set: a statement kept in two
    keepings is one ({verb: roles}, as its bean writes it; an id a store minted is kept)."""
    garden = garden or (stores[0].garden if stores else engine.Garden.read(ROOT))
    out, seen = [], set()
    bean = garden.beans.get(being)
    s0 = stores[0] if stores else None
    if bean is not None:
        for _i, v, r in bean.items:
            nr = s0.normalize(being, v, r) if s0 else r
            key = canonical(v, {k: x for k, x in nr.items() if k != 'id'})
            if key not in seen:
                seen.add(key)
                out.append({v: dict(r)})
    for s in stores:
        for v, r, _a in s.get(being):
            key = canonical(v, {k: x for k, x in r.items() if k != 'id'})
            if key not in seen:
                seen.add(key)
                out.append({v: s.denormalize(being, v, r)})
    return out


def check_here(names=None, *, root=ROOT):
    """The check of every store this host keeps (or those named), together, over git."""
    stores, out = [], []
    for name, (path, _row, why) in sorted(kept_here(root).items()):
        if names and name not in names:
            continue
        if not path:
            out.append(('store', name, f"not here: {why}"))
            continue
        if not os.path.exists(path):
            out.append(('store', name, f"declared at {path}, and no file is there (`open` makes it)"))
            continue
        stores.append(open_store(name, root=root, create=False))
    return stores, out


# ------------------------------------------------------------------------------------------------ the bean's file
def _flow(value):
    """A value in YAML's flow style, as the beans write their statements."""
    if isinstance(value, dict):
        return '{ ' + ', '.join(f"{k}: {_flow(v)}" for k, v in value.items()) + ' }'
    if isinstance(value, list):
        return '[' + ', '.join(_flow(v) for v in value) + ']'
    s = str(value)
    if re.match(r'^[A-Za-z0-9][A-Za-z0-9_.@/+-]*$', s) and s not in ('true', 'false', 'null', 'yes', 'no', 'on', 'off') \
            and not re.match(r'^[0-9][0-9:.-]*$', s):
        return s
    return json.dumps(s, ensure_ascii=False)


def statement_line(st):
    (verb, roles), = st.items()
    return f"  - {verb}: {_flow(roles)}"


def write_bean(root, being, statements, act, kind=None, title=None):
    """Add `statements` and their `act` at the end of the being's bean's statements (the bean made where there is
    none), and prove it: read back, its statements are the old ones and these, in order, and nothing else changed."""
    path = os.path.join(root, 'beans', being + '.md')
    lines = [statement_line(s) for s in statements + [act]]
    if not os.path.exists(path):
        text = (f"---\nbean: {being}\nkind: {kind}\ntitle: {json.dumps(title or being, ensure_ascii=False)}\n"
                f"statements:\n" + '\n'.join(lines) + "\n---\n\nKept first in a store; its statements exported by "
                f"bin/store.py.\n")
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(text)
        return path
    with open(path, encoding='utf-8') as fh:
        old = fh.read()
    head = old.split('\n')
    if head[0].strip() != '---':
        raise StoreError(f"{path}: no front matter")
    end = next(i for i in range(1, len(head)) if head[i].strip() == '---')
    st = next((i for i in range(1, end) if head[i].startswith('statements:')), None)
    if st is None:
        raise StoreError(f"{path}: no `statements:` in its front matter")
    j = st + 1
    while j < end and (head[j].startswith('  ') or head[j].startswith('- ') or not head[j].strip()):
        j += 1
    while j > st + 1 and not head[j - 1].strip():
        j -= 1
    new = '\n'.join(head[:j] + lines + head[j:])
    before = engine._bean(path, being).statements
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(new)
    after = engine._bean(path, being).statements
    want = list(before) + [dict(s) for s in statements + [act]]
    if json.dumps(after, sort_keys=True, default=str) != json.dumps(want, sort_keys=True, default=str):
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(old)
        raise StoreError(f"{path}: the bean read back is not the old one with these statements added; put back")
    return path


# ------------------------------------------------------------------------------------------------ the command
def _arg(argv, flag, default=None):
    if flag in argv:
        i = argv.index(flag)
        v = argv[i + 1] if i + 1 < len(argv) else None
        del argv[i:i + 2]
        return v
    return default


def _flag(argv, flag):
    if flag in argv:
        argv.remove(flag)
        return True
    return False


def main(argv):
    argv = list(argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0
    path = _arg(argv, '--path')
    as_json = _flag(argv, '--json')
    cmd, rest = argv[0], argv[1:]

    def opened(name, create=True):
        return open_store(None if path else name, path=path, create=create)

    try:
        if cmd == 'list':
            for name, (p, row, why) in sorted(kept_here().items()):
                print(f"{name}\t{p or '-'}\t{row.get('form', 'sqlite')}\t{why or ('kept' if p and os.path.exists(p) else 'not made')}")
            return 0
        if cmd == 'open':
            s = opened(rest[0] if rest else None)
            print(f"store {s.name}: {s.path} — {len(s.verbs())} relation(s), {s.count()} row(s)")
            return 0
        if cmd == 'get':
            s = opened(rest[0], create=False) if not path else opened(None, create=False)
            being = rest[-1]
            rows = s.get(being)
            if as_json:
                print(json.dumps([{'verb': v, 'roles': r, 'known': a} for v, r, a in rows], ensure_ascii=False, indent=1))
            else:
                for v, r, a in rows:
                    print(statement_line({v: s.denormalize(being, v, r)}) + (f"   # known by {', '.join(a)}" if a else ''))
            return 0
        if cmd == 'query':
            s = opened(rest[0] if not path else None, create=False)
            sql = rest[1] if not path else rest[0]
            params = rest[2:] if not path else rest[1:]
            names, rows = s.query(sql, params)
            if as_json:
                print(json.dumps([dict(zip(names, r)) for r in rows], ensure_ascii=False, default=str))
            else:
                print('\t'.join(names))
                for r in rows:
                    print('\t'.join('' if x is None else str(x) for x in r))
            return 0
        if cmd == 'check':                   # the union of git and the stores, judged whole: git's findings, then theirs
            if path:
                stores, pre = [Store(path, create=False)], []
            else:
                stores, pre = check_here(rest or None)
            found = pre + check(stores)
            if as_json:
                print(json.dumps([{'rule': r, 'where': w, 'says': m} for r, w, m in found], ensure_ascii=False))
            else:
                for r, w, m in found:
                    print(f"{r:<11} {w}: {m}")
                n = sum(s.count() for s in stores)
                print(f"store check: {len(stores)} store(s), {n} row(s), over git — {len(found)} finding(s)")
            return 1 if found else 0
        if cmd == 'export':
            by = _arg(rest, '--by')
            write = _flag(rest, '--write')
            s = opened(rest[0] if not path else None, create=False)
            being = rest[-1]
            if not by:
                print("store export: name the session or tool the export is by: --by <being>", file=sys.stderr)
                return 2
            sts, act = s.export(being, by=by)
            if act is None:
                print(f"store export: the bean of {being} holds every statement the store keeps of it")
                return 0
            if write:
                p = write_bean(s.root, being, sts, act, kind=s.kind_of(being),
                               title=(s.db.execute('SELECT title FROM being WHERE id=?', (being,)).fetchone() or [None])[0])
                print(f"store export: {len(sts)} statement(s) and their act written into {os.path.relpath(p, s.root)}")
            else:
                for st in sts + [act]:
                    print(statement_line(st))
            return 0
        if cmd == 'import':
            s = opened(rest[0] if not path else None)
            beans = rest[1:] if not path else rest
            n = sum(s.import_bean(b) for b in beans)
            print(f"store import: {n} statement(s) of {len(beans)} bean(s) kept in {s.name}")
            return 0
        if cmd == 'put':
            act = _arg(rest, '--act')
            s = opened(rest[0] if rest and not path else None)
            n = 0
            with s.batch():
                for line in sys.stdin:
                    if not line.strip():
                        continue
                    o = json.loads(line)
                    if 'verb' not in o:
                        s.being(o['being'], o.get('kind'), o.get('title'), o.get('summary'))
                        continue
                    roles = dict(o.get('roles') or {})
                    for k in ('id',) + BESIDE:
                        if k in o:
                            roles[k] = o[k]
                    s.put(o['being'], o['verb'], roles, act=None if o['verb'] in s.law.knowing else act)
                    n += 1
            print(f"store put: {n} statement(s) kept in {s.name}")
            return 0
        if cmd == 'gone':
            by, why = _arg(rest, '--by'), _arg(rest, '--why')
            s = opened(rest[0] if not path else None, create=False)
            being, sid = rest[-2], rest[-1]
            s.gone(being, sid, by=by, why=why)
            print(f"store gone: {being}#{sid} taken out of {s.name}, recorded")
            return 0
        if cmd == 'series':
            s = opened(rest[0] if not path else None)
            op, bean, key, part = rest[-4:]
            if op == 'import':
                print(f"store series: {bean}/{key}/{part} kept, sha-256 {s.series_import(bean, key, part)}")
            else:
                dest = os.path.join(s.root, 'series', bean, key, part + '.tsv')
                s.series_export(bean, key, part, dest)
                print(f"store series: {bean}/{key}/{part} written back to {os.path.relpath(dest, s.root)}")
            return 0
    except StoreError as e:
        print(f"store {cmd}: {e}", file=sys.stderr)
        return 1
    print(f"store: no command `{cmd}` — {__doc__.splitlines()[0]}", file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
