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

THE CHECK. `check` judges the union of git and every store this host keeps. A union small enough is judged by the
core's own engine — every rule, over the beans and the stores' beings read as beans — and what it finds beyond git's own
findings is the store's. A larger one is judged by queries: `names` (a name given once names one being), `order` (no
cycle through own, part, be at, need), each act a row names (a knowing act, here or in git), each being's kind against
its bean's, the overlaps (one `(being, id)`, one form), and every pointer in git. The relations those queries do not
judge are named, never passed over in silence. The gate never reads a store: a gate that judged one machine's disk
would pass on one and fail on another.

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

from core import engine  # noqa: E402
from core.engine import listed, shapes_of  # noqa: E402

FORMS = ('sqlite',)                       # the occupants of a store's `form` (core/law/layers.yaml `store_shape`)
ID = engine.ID
POINTER = re.compile(r'^store:([a-z][a-z0-9-]*):([a-z0-9][a-z0-9_-]*)(?:#([a-z0-9][a-z0-9_-]*))?$')
REF = re.compile(r'^([a-z0-9][a-z0-9._-]*)#([a-z0-9][a-z0-9_-]*)$')
BESIDE = ('while', 'why', 'note')
UNION_ROWS = 200_000                      # a union of at most this many rows is judged by the core's engine whole
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
_KEEP = re.compile(rb'[\x00-\x1f\x7f%]')


def escape(raw):
    """A name the world gives in bytes, as text (`escaped`): UTF-8, and `%XX` for a byte that is no part of well-formed
    UTF-8, a control character (C0, DEL, C1) and `%` itself."""
    if isinstance(raw, str):
        raw = os.fsencode(raw)
    out = []
    text = raw.decode('utf-8', 'surrogateescape')
    for ch in text:
        o = ord(ch)
        if 0xDC80 <= o <= 0xDCFF:                       # a byte surrogateescape kept: not well-formed UTF-8
            out.append('%%%02X' % (o - 0xDC00))
        elif o < 0x20 or o == 0x7F or 0x80 <= o <= 0x9F or ch == '%':
            for b in ch.encode('utf-8'):
                out.append('%%%02X' % b)
        else:
            out.append(ch)
    return ''.join(out)


def unescape(text):
    """The bytes a text written `escaped` stands for."""
    out, i = bytearray(), 0
    while i < len(text):
        if text[i] == '%' and re.match(r'^[0-9A-F]{2}$', text[i + 1:i + 3]):
            out.append(int(text[i + 1:i + 3], 16))
            i += 3
        else:
            out += text[i].encode('utf-8')
            i += 1
    return bytes(out)


# ------------------------------------------------------------------------------------------------ forms and ids
def canonical(verb, roles):
    """A statement's form, as MERGE.md 1 compares it: its verb and every role, qualifier and key but `id`, each map's
    keys sorted."""
    r = {k: v for k, v in roles.items() if k != 'id'}
    return json.dumps({verb: r}, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def mint(verb, roles):
    """The id a statement given none is named by: its verb and 16 hexadecimal digits of its form's SHA-256."""
    return f"{verb}-{hashlib.sha256(canonical(verb, roles).encode('utf-8')).hexdigest()[:16]}"


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

    def __init__(self, path, *, root=ROOT, create=True, readers=None, name=None, law=None, garden=None):
        self.path, self.root, self.name = path, root, name or os.path.splitext(os.path.basename(path))[0]
        new = not os.path.exists(path)
        if new and not create:
            raise NotHere(f"no store at {path}")
        if new:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.db = sqlite3.connect(path, timeout=60, isolation_level=None)
        self.db.execute('PRAGMA busy_timeout=60000')
        self.db.execute('PRAGMA foreign_keys=OFF')
        self._law, self._garden, self._judge = law, garden, None
        self._beings = {}                  # id -> (n, kind)
        self._cols = {}                    # verb -> {role: (has b_, ...)}
        self._acts = {}                    # ref -> n
        self._depth = 0
        if new:
            shared = bool(readers) and any(r != _me() for r in listed(readers))
            self.db.execute('PRAGMA journal_mode=' + ('DELETE' if shared else 'WAL'))
            self._base()
            self.db.execute("INSERT OR REPLACE INTO meta (k, v) VALUES ('name', ?), ('schema', ?), ('created', ?), "
                            "('readers', ?)", (self.name, SCHEMA_VERSION, now(), json.dumps(listed(readers))))
            if shared:
                os.chmod(path, 0o644)
        else:
            self._base()

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
        ver = self.db.execute('PRAGMA schema_version').fetchone()[0]
        if getattr(self, '_verbs_at', None) != ver:
            self._verbs = sorted(r[0][2:] for r in self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'v\\_%' ESCAPE '\\'"))
            self._verbs_at = ver
        return self._verbs

    def _verb_of_table(self, table):
        return table[2:]

    def columns(self, verb):
        """{role or qualifier: (being column or None, text column)} of the verb's relation, made at its first row."""
        if verb in self._cols:
            return self._cols[verb]
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
            for k, (bc, _tc) in cols.items():
                if bc:
                    self.db.execute(f"CREATE INDEX IF NOT EXISTS {_q(table + '_' + bc)} ON {_q(table)} ({bc})")
        else:
            for k, (bc, tc) in cols.items():     # a row of the law that grew a role since: its column added
                for c in (bc, tc):
                    if c and c not in have:
                        self.db.execute(f"ALTER TABLE {_q(table)} ADD COLUMN {c}")
        self._cols[verb] = cols
        return cols

    # -------------------------------------------------------------------------------------------- beings
    def has_being(self, bid):
        return self._being_row(bid) is not None

    def _being_row(self, bid):
        if bid in self._beings:
            return self._beings[bid]
        r = self.db.execute('SELECT n, kind FROM being WHERE id=?', (bid,)).fetchone()
        if r:
            self._beings[bid] = (r[0], r[1])
            return self._beings[bid]
        return None

    def kind_of(self, bid):
        r = self._being_row(bid)
        if r and r[1]:
            return r[1]
        b = self.garden.beans.get(bid)
        return b.kind if b is not None else None

    def being(self, bid, kind=None, title=None, summary=None):
        """The being `bid` kept here, with its kind (and title, summary): its number. A kind once kept is kept."""
        if not isinstance(bid, str) or not ID.match(bid):
            raise StoreError(f"{bid!r}: a being's id is one word — `^[a-z0-9][a-z0-9_-]*$`")
        if kind is not None and kind not in self.law.kinds:
            raise StoreError(f"`{kind}` is no kind of the law")
        bean = self.garden.beans.get(bid)
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
        return isinstance(x, str) and (x in self.garden.beans or self.has_being(x))

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
        return {k: json.loads(v) for k, v in self.db.execute('SELECT key, value FROM detail WHERE being=?', (r[0],))}

    # -------------------------------------------------------------------------------------------- fillers
    def normalize(self, being, verb, roles):
        """A statement's roles as a store keeps them: `self` the being, a statement of the being `<being>#<id>`, a
        pointer the plain id (its kind kept)."""
        spec = (self.law.verbs.get(verb) or {})
        allr = dict(spec.get('roles') or {}, **(spec.get('qualifiers') or {}))
        out = {}
        for k, v in roles.items():
            if k in ('id',) + BESIDE:
                out[k] = v
                continue
            shapes = shapes_of(allr.get(k) or {})
            out[k] = self._norm(v, being, shapes)
        return out

    def _norm(self, v, being, shapes):
        if isinstance(v, list):
            return [self._norm(x, being, shapes) for x in v]
        if not isinstance(v, str):
            return v
        if v == 'self' and 'being' in shapes:
            return being
        m = POINTER.match(v)
        if m:
            kind, bid, sid = m.groups()
            if 'being' in shapes or 'statement' in shapes:
                self.being(bid, kind)
                return f"{bid}#{sid}" if sid else bid
        if 'statement' in shapes and '#' not in v and ID.match(v) and not self._known_being(v):
            return f"{being}#{v}"
        return v

    def denormalize(self, being, verb, roles):
        """A row's roles as `being`'s bean writes them: the being `self`, its own statements by their id, a being with
        no bean in git a pointer."""
        spec = (self.law.verbs.get(verb) or {})
        allr = dict(spec.get('roles') or {}, **(spec.get('qualifiers') or {}))
        return {k: (v if k in ('id',) + BESIDE else self._denorm(v, being, shapes_of(allr.get(k) or {})))
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
            if b not in self.garden.beans and self.has_being(b):
                return f"store:{self.kind_of(b)}:{b}#{sid}"
            return v
        if 'being' in shapes and ID.match(v) and v not in self.garden.beans and self.has_being(v) and \
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
        r = self.db.execute('SELECT id FROM being WHERE n=?', (n,)).fetchone()
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
        r = self.db.execute('SELECT ref FROM act WHERE n=?', (n,)).fetchone()
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
        bean = self.garden.beans.get(b)
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
            cur = self.db.execute(f"SELECT * FROM {_q('v_' + _col(verb))} WHERE being=? AND id=?", (r[0], sid))
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
            cur = self.db.execute(f"SELECT * FROM {_q('v_' + _col(verb))} WHERE being=? ORDER BY n", (r[0],))
            names = [d[0] for d in cur.description]
            for row in cur.fetchall():
                sid, roles, known, n, _b = self._decode(verb, row, names)
                acts = [self._act_ref(known)] if known else []
                acts += [self._act_ref(a) for (a,) in self.db.execute(
                    'SELECT act FROM known_also WHERE verb=? AND row=? ORDER BY act', (verb, n))]
                out.append((verb, dict(roles, id=sid), acts))
        return out

    def count(self):
        return sum(self.db.execute(f"SELECT COUNT(*) FROM {_q('v_' + _col(v))}").fetchone()[0] for v in self.verbs())

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
        J = self.judge
        J.out = []
        b = engine.Bean(being, header={'bean': being, 'kind': self.kind_of(being), 'statements': [{verb: r}]})
        J.one(b, 0, verb, r)
        for k, v in r.items():
            for s in (v if isinstance(v, list) else [v]):
                if isinstance(s, str) and engine.dmparse.CONTROL.search(s.replace('\t', '')):
                    J.err('form', f"{being}#{r.get('id')} {verb}", f"`{k}` holds a control character: text holds none "
                                                                    f"but a tab — a name in bytes is written `escaped`")
        if verb == 'name' and isinstance(r.get('by'), str) and (self.law.namespaces.get(r['by']) or {}).get('kept') == 'held':
            J.err('harm', f"{being}#{r.get('id')} name", f"a name {r['by']} gives is kept only in the held store")
        marked = J._marked()
        if marked and any(s in marked for s in J._codes(r)):
            J.err('harm', f"{being}#{r.get('id')} {verb}", "holds a code of a scheme marked special-category")
        if J.out:
            raise StoreError('; '.join(f"{rule} {where}: {msg}" for rule, where, msg in J.out))

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
        `put` judges one; a row kept already is kept once. Returns how many rows were new."""
        cols = self.columns(verb)
        if verb not in self.law.knowing:
            self._check_act(act)
        a = self._act(act) if act else None
        table = 'v_' + _col(verb)
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

        with self.batch():
            self.db.executemany(sql, args())
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
        bean = self.garden.beans.get(being) if into is None else into
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
    """[(rule, where, message)] of the union of git and `stores`: what the store adds to git's own findings."""
    garden = garden or engine.Garden.read(root)
    if law is None:
        from core import check as core_check
        rel = root if os.path.isfile(os.path.join(root, 'core', 'law', 'core.yaml')) else None
        law = core_check.garden_law(root, rel)
    for s in stores:
        s._law, s._garden = law, garden
    out = []
    kept = {}                                # being -> [(store, verb, roles, acts)]
    for s in stores:
        for (bid, kind) in s.db.execute('SELECT id, kind FROM being'):
            bean = garden.beans.get(bid)
            if bean is not None and kind and bean.kind != kind:
                out.append(('form', f"{s.name}:{bid}", f"kept as `{kind}`, and its bean is a `{bean.kind}`"))
            if bean is None and kind is None and _has_rows(s, bid):
                out.append(('form', f"{s.name}:{bid}", "kept with no kind, and no bean gives it one"))
    out += _acts_resolve(stores)
    out += _overlaps(stores, garden, law)
    out += _pointers(stores, garden)
    total = sum(s.count() + s.db.execute('SELECT COUNT(*) FROM being').fetchone()[0] for s in stores)
    if total <= UNION_ROWS:
        out += _union_judged(stores, garden, law)
    else:
        out += _names_once(stores, garden, law)
        out += _cycles(stores, garden)
        judged = {'hold', 'name', 'part', 'measure', 'own', 'need', 'be', 'derive', 'read', 'make', 'say'}
        rest = sorted({v for s in stores for v in s.verbs()} - judged)
        if rest:
            out.append(('size', ', '.join(s.name for s in stores),
                        f"{total} rows: judged by queries (names, order, acts, kinds, overlaps, pointers), each row "
                        f"judged at its put; the rules of {', '.join(rest)} over the union are not judged at this size"))
    return out


def _has_rows(s, bid):
    n = s._being_row(bid)
    return n is not None and any(s.db.execute(f"SELECT 1 FROM {_q('v_' + _col(v))} WHERE being=? LIMIT 1",
                                              (n[0],)).fetchone() for v in s.verbs())


def _acts_resolve(stores):
    out = []
    for s in stores:
        for (ref,) in s.db.execute('SELECT ref FROM act'):
            hit = None
            for t in stores:
                hit = t.resolve(ref)
                if hit:
                    break
            if hit is None:
                out.append(('knowing', f"{s.name}", f"rows are known by {ref}, which is kept nowhere this host reads"))
            elif hit[1] not in s.law.knowing:
                out.append(('knowing', f"{s.name}", f"rows are known by {ref}, a `{hit[1]}`: no knowing act"))
    return out


def _overlaps(stores, garden, law):
    """One `(being, id)`, one form, across git and every store."""
    out = []
    for s in stores:
        for (bid,) in s.db.execute('SELECT id FROM being'):
            bean = garden.beans.get(bid)
            if bean is None:
                continue
            ids = {}
            for _i, v, r in bean.items:
                if 'held' in r:
                    continue
                sid = r['id'] if isinstance(r.get('id'), str) else mint(v, s.normalize(bid, v, r))
                ids[sid] = (v, s.normalize(bid, v, r))
            for verb, roles, _acts in s.get(bid):
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


def _union_judged(stores, garden, law):
    """The union of git and the stores, judged whole by the core's engine: every finding git alone does not have, and
    none of `knowing` at a store's row (a row names its act; `_acts_resolve` judges it). In the union every being is a
    bean, so every filler is its plain id."""
    G = garden.copy()
    added = {}                               # bean id -> index from which its statements are the store's
    for bid, bean in list(G.beans.items()):  # a bean that names a being by a pointer, read with the plain id
        if bean.unread or 'store:' not in json.dumps(bean.statements, default=str):
            continue
        G.beans[bid] = engine.Bean(bid, path=bean.path, header=dict(bean.header, statements=_plain_statements(
            bean.statements)), raw=None)
    for s in stores:
        for (bid, kind, title, summary) in s.db.execute('SELECT id, kind, title, summary FROM being').fetchall():
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
    if not added:
        return []
    base = {(r, w, m) for r, w, m in engine.Judge(law, garden).run()}
    out = []
    for rule, where, msg in engine.Judge(law, G).run():
        if (rule, where, msg) in base:
            continue
        m = re.match(r'^([a-z0-9][a-z0-9._-]*)\[(\d+)\]', where)
        if rule == 'knowing' and m and m.group(1) in added and int(m.group(2)) >= added[m.group(1)]:
            continue
        if rule == 'knowing' and where in added and added[where] == 0:
            continue
        out.append((rule, where, msg))
    return out


def _names_once(stores, garden, law):
    """A name a namespace gives once names one being, over git and every store (SQL)."""
    once = sorted(n for n, r in law.namespaces.items() if r.get('once') == 'true')
    given = {}
    for b in garden.beans.values():
        for i, v, r in b.items:
            if v == 'name' and r.get('by') in once and isinstance(r.get('as'), str) and r.get('as') != 'unknown' \
                    and 'held' not in r:
                of = b.id if r.get('of') == 'self' else _plainid(r.get('of'))
                given.setdefault((r['by'], r['as']), set()).add(str(of))
    out = []
    for s in stores:
        if 'name' not in s.verbs():
            continue
        marks = ','.join('?' * len(once))
        rows = s.db.execute(f"SELECT t_by, t_as, (SELECT id FROM being WHERE n=COALESCE(b_of, -1)), t_of FROM v_name "
                            f"WHERE t_by IN ({marks}) AND t_as IS NOT NULL AND t_as != 'unknown'", once)
        for ns, nm, of_b, of_t in rows:
            given.setdefault((ns, nm), set()).add(str(of_b or of_t))
    for (ns, nm), beings in sorted(given.items()):
        if len(beings) > 1:
            out.append(('names', f"{ns}:{nm}", f"{ns} gives {nm!r} once, and it names {', '.join(sorted(beings))}"))
    return out


def _cycles(stores, garden):
    """Nothing owns itself, is part of itself, is at itself or needs itself through others: the chains of git and every
    store (engine.ORDERED), walked over the beings' numbers."""
    out = []
    for verb, low, high, says in engine.ORDERED:
        graph = {}
        for b in garden.beans.values():
            for _i, v, r in b.items:
                if v != verb or 'held' in r:
                    continue
                for a in [b.id if r.get(k) == 'self' else _plainid(r.get(k)) for k in low]:
                    for c in [b.id if r.get(k) == 'self' else _plainid(r.get(k)) for k in high]:
                        for x in (a if isinstance(a, list) else [a]):
                            for y in (c if isinstance(c, list) else [c]):
                                if isinstance(x, str) and isinstance(y, str):
                                    graph.setdefault(x, set()).add(y)
        for s in stores:
            if verb not in s.verbs():
                continue
            cols = s.columns(verb)
            for lo in low:
                for hi in high:
                    if lo not in cols or hi not in cols or not cols[lo][0] or not cols[hi][0]:
                        continue
                    q = (f"SELECT a.id, c.id FROM {_q('v_' + _col(verb))} t JOIN being a ON a.n = t.{cols[lo][0]} "
                         f"JOIN being c ON c.n = t.{cols[hi][0]}")
                    for x, y in s.db.execute(q):
                        graph.setdefault(x, set()).add(y)
        state, found = {}, set()
        for start in list(graph):
            if start in state:
                continue
            stack = [(start, iter(sorted(graph.get(start, ()))))]
            state[start], path = 1, [start]
            while stack:
                node, it = stack[-1]
                nxt = next(it, None)
                if nxt is None:
                    state[node] = 2
                    stack.pop()
                    path.pop()
                    continue
                st = state.get(nxt)
                if st == 1:
                    loop = path[path.index(nxt):] + [nxt]
                    key = frozenset(loop)
                    if key not in found:
                        found.add(key)
                        out.append(('order', f"{verb}", f"{' → '.join(loop)}: nothing {says} itself through others"))
                elif st is None:
                    state[nxt] = 1
                    path.append(nxt)
                    stack.append((nxt, iter(sorted(graph.get(nxt, ())))))
    return out


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
        if cmd == 'check':
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
