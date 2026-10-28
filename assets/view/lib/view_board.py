"""view_board — the board: one being or several, the cursor, kept still while the aspect around it turns (the view
profile's archetype `cursor`; its aspects, core/law/profiles.yaml `aspects`). A reading: nothing here is written.

    python3 assets/view/bin/view.py board aspects                    the aspects this garden's board turns through
    python3 assets/view/bin/view.py board lens <aspect> <id> [<id>…] one aspect through a cursor, as groups
    python3 assets/view/bin/view.py board being <id>                 one being's sheet
    python3 assets/view/bin/view.py board find <text> <id> [<id>…]   what the cursor holds whose name has the text

daftard draws it as a page (`/board?g=<garden>`, three.js beneath its HTML), and asks these questions of the garden's
own release through its worker's methods board_aspects, board_lens, board_being and board_find; the command line
prints the same answers, a check without a server.

A BEING is named by its id wherever it is kept: a bean, or a being of a store this host keeps (a volume, a folder
`d-…`, a content `c-…`, the carrier that holds a volume); a store's pointer `store:<kind>:<id>` is read as its id. The
CURSOR is one being or several.

AN ASPECT is a row of the law (`aspects`) whose home is the core or a profile the garden takes: the verb it follows,
the role the cursor fills in it, the row of `orientations` it is laid out by, and the kinds of being it reads. A lens
through a cursor answers GROUPS of neighbours, each `before` or `after` the cursor along that order, and on the side of
one being of the cursor (its place in the cursor, from 0), or `shared` between several (what several hold in common, by
the folders it sits in); each
group with its relation, its head where one leads it, its members (at most LIMIT drawn, the rest counted) and a note.
The page lays them out from that alone, asking the orientation where before and after are, and names no side.

WHAT IT READS: the garden's beans and its law, and every store this host keeps (bin/store.py, `details.stores` on the
host's bean): each store through a connection that only reads, in one snapshot per question, which a writer at work is
seen before or after, whole. No path, port or store's name is its own: they are the garden's. A question over a large
store reads it at a store's scale, by its indexes; what several disks hold in common reads every holding beneath each,
which over millions of files takes seconds.

Each aspect it draws is read here; an aspect of the law it does not draw yet is listed with `drawn: false`, and a lens
through it answers no groups and says so.
"""
import collections
import importlib
import importlib.util
import json
import os
import re
import sqlite3
import sys

LIMIT = 300          # the members of one group drawn; the rest are counted
FOLLOW = 5000        # the most holdings, folders or makes read for one being
PAIRS = 30           # the pairs of folders drawn between several cursors: those holding the most in common
CURSORS = 8          # the most beings of one cursor
DRAWN = ('holds', 'carried-by', 'copies', 'in-backup', 'its-series', 'its-class', 'its-dataset', 'its-safety')
POINTER = re.compile(r'^store:[a-z][a-z0-9-]*:(.+)$')


class Refused(ValueError):
    """What the board will not read, said to the person."""


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _text(v):
    if isinstance(v, (bytes, bytearray, memoryview)):
        return bytes(v).decode('utf-8', 'replace')
    return '' if v is None else str(v)


def size(n):
    n = n or 0
    for u in ('B', 'kB', 'MB', 'GB', 'TB'):
        if n < 1000 or u == 'TB':
            return f'{n:.0f} {u}' if u == 'B' else f'{n:.1f} {u}'
        n /= 1000


def group(key, label, members, at='after', side=0, relation=None, head=None, total=None, note=None):
    members = list(members)
    return {'key': key, 'label': label, 'at': at, 'side': side, 'relation': relation, 'head': head,
            'members': members[:LIMIT], 'total': len(members) if total is None else total, 'note': note}


# ------------------------------------------------------------------------------------------------ a store, read
class Store:
    """One store this host keeps, read in one snapshot: its beings, their names, parts, holdings and makes."""

    OWN = "t_by IS NULL AND b_by IS NOT NULL AND instr(t_as, '/') = 0"       # core/formats.py OWN_NAME

    def __init__(self, name, path):
        self.name, self.path = name, path
        self.db = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=10, check_same_thread=False)
        self.db.execute('BEGIN')
        self.tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self._row = {}

    def close(self):
        try:
            self.db.rollback()
        finally:
            self.db.close()

    def q(self, sql, *args, need=()):
        if any(t not in self.tables for t in need):
            return []
        return self.db.execute(sql, args).fetchall()

    def n(self, bid):
        r = self.db.execute('SELECT n FROM being WHERE id = ?', (bid,)).fetchone()
        return r[0] if r else None

    def row(self, n):
        """(id, kind, title) of a being by its number."""
        if n not in self._row:
            r = self.db.execute('SELECT id, kind, title FROM being WHERE n = ?', (n,)).fetchone()
            self._row[n] = r or (None, None, None)
        return self._row[n]

    def id(self, n):
        return self.row(n)[0]

    def kind(self, n):
        return self.row(n)[1]

    def own_name(self, n):
        r = self.q(f"SELECT t_as FROM v_name WHERE b_of = ? AND {self.OWN} LIMIT 1", n, need=('v_name',))
        return _text(r[0][0]) if r else None

    def parent(self, n):
        r = self.q(f"SELECT b_by FROM v_name WHERE b_of = ? AND {self.OWN} LIMIT 1", n, need=('v_name',))
        if r:
            return r[0][0]
        r = self.q("SELECT b_of FROM v_part WHERE b_by = ? LIMIT 1", n, need=('v_part',))
        return r[0][0] if r else None

    def volume_path(self, n):
        """(volume n, its path beneath the volume) of a folder; (n, '') of a volume."""
        parts, x, hops = [], n, 0
        while x is not None and self.kind(x) == 'folder' and hops < 4096:
            parts.append(self.own_name(x) or '?')
            x, hops = self.parent(x), hops + 1
        return x, '/'.join(reversed(parts))

    def blake3(self, c):
        r = self.q("SELECT t_as FROM v_name WHERE b_of = ? AND t_by = 'blake3' LIMIT 1", c, need=('v_name',))
        return _text(r[0][0]) if r else None

    def bytes_of(self, c):
        r = self.q("SELECT CAST(json_extract(CAST(q_value AS TEXT), '$.count') AS INTEGER) FROM v_measure "
                   "WHERE being = ? AND t_as = 'information' LIMIT 1", c, need=('v_measure',))
        return r[0][0] if r else None

    def folders_in(self, n, limit=FOLLOW):
        return self.q(f"SELECT b_of, t_as FROM v_name WHERE b_by = ? AND {self.OWN} LIMIT ?", n, limit,
                      need=('v_name',))

    def held_in(self, n, limit=FOLLOW):
        """[(content n, name)] a folder or a volume holds under a name."""
        return self.q("SELECT b_of, t_as FROM v_hold WHERE b_by = ? AND t_as IS NOT NULL LIMIT ?", n, limit,
                      need=('v_hold',))

    def carries(self, n):
        """What a carrier holds whole (a volume), or what holds a volume: (by, of) of `hold` with no name."""
        return self.q("SELECT b_of FROM v_hold WHERE b_by = ? AND t_as IS NULL AND b_of IS NOT NULL", n,
                      need=('v_hold',))

    def carriers(self, n):
        return self.q("SELECT b_by FROM v_hold WHERE b_of = ? AND t_as IS NULL AND b_by IS NOT NULL", n,
                      need=('v_hold',))

    def holdings(self, c, limit=FOLLOW):
        """[(folder n, name, hold id)] of every holding of a content under a name."""
        return self.q("SELECT b_by, t_as, id FROM v_hold WHERE b_of = ? AND t_as IS NOT NULL LIMIT ?", c, limit,
                      need=('v_hold',))

    def made(self, folder, hold_id):
        """(its source holdings' refs, its moment) where a `make` says a holding was made from another: a copy."""
        ref = json.dumps([f'{self.id(folder)}#{hold_id}'])
        r = self.q("SELECT t_from, t_at FROM v_make WHERE being = ? AND CAST(t_of AS TEXT) = ? LIMIT 1", folder, ref,
                   need=('v_make',))
        if not r:
            return None
        return _refs(r[0][0]), _text(r[0][1])

    def makes_in(self, folder, limit=FOLLOW):
        """[(made refs, source refs, moment)] of the copies made into a folder."""
        return [(_refs(o), _refs(f), _text(a)) for o, f, a in
                self.q("SELECT t_of, t_from, t_at FROM v_make WHERE being = ? LIMIT ?", folder, limit,
                       need=('v_make',))]

    def counts(self, ns):
        """{folder n: (its folders, its files)} of the folders given, direct children only."""
        ns = list(ns)
        out = {n: [0, 0] for n in ns}
        for i in range(0, len(ns), 500):
            part = ns[i:i + 500]
            marks = ','.join('?' * len(part))
            for by, k in self.q(f"SELECT b_by, COUNT(*) FROM v_name WHERE b_by IN ({marks}) AND {self.OWN} "
                                f"GROUP BY b_by", *part, need=('v_name',)):
                out[by][0] = k
            for by, k in self.q(f"SELECT b_by, COUNT(*) FROM v_hold WHERE b_by IN ({marks}) AND t_as IS NOT NULL "
                                f"GROUP BY b_by", *part, need=('v_hold',)):
                out[by][1] = k
        return out

    def beneath(self, n):
        """Every folder beneath a folder or a volume, and itself; for a carrier, beneath every volume it holds."""
        starts = [n] if self.kind(n) in ('folder', 'volume') else [v for (v,) in self.carries(n)]
        out = []
        for s in starts:
            out += [x for (x,) in self.q(
                "WITH RECURSIVE t(n) AS (SELECT ? UNION SELECT p.b_by FROM v_part p JOIN t ON p.b_of = t.n) "
                "SELECT n FROM t", s, need=('v_part',))] or [s]
        return out


def _refs(v):
    t = _text(v)
    try:
        x = json.loads(t)
    except ValueError:
        return [t] if t else []
    return [str(r) for r in _listed(x)]


# ------------------------------------------------------------------------------------------------ the board
class Board:
    """The board over a garden at `root`: its law and beans read once, its stores in a snapshot per question."""

    def __init__(self, root, stores=None):
        self.root = os.path.abspath(root)
        for p in (os.path.join(self.root, 'bin'), self.root):
            if p not in sys.path:
                sys.path.insert(0, p)
        from core import judge
        self.L = judge.garden_law(self.root)
        self.taken = set(getattr(self.L, 'taken', None) or [])
        if 'view' not in self.taken:
            raise Refused("the board is the view profile's archetype `cursor`, and this garden does not take the view "
                          "profile (VOCAB.md `profiles`)")
        self.pass_ = importlib.import_module('pass')
        self.beans = self.pass_.beans_here(self.root)
        self.gardener = self.pass_.gardener_of(self.root)
        self.index = collections.defaultdict(list)       # (verb, role, being) -> [(bean, roles)]
        for b, fm in self.beans.items():
            for _i, verb, roles in self.pass_.statements(fm):
                for role in ('by', 'of', 'to', 'from'):
                    for v in _listed(roles.get(role)):
                        if isinstance(v, str):
                            self.index[(verb, role, b if v == 'self' else self._plain(v))].append((b, roles))
        if stores is None:
            import store as dmstore
            stores = {n: p for n, (p, _row, _why) in dmstore.kept_here(self.root).items() if p and os.path.isfile(p)}
        self.store_paths = dict(sorted(stores.items()))
        self.S = []

    # ---- the stores, one snapshot per question
    def __enter__(self):
        self.S = [Store(n, p) for n, p in self.store_paths.items()]
        return self

    def __exit__(self, *exc):
        for s in self.S:
            s.close()
        self.S = []

    @staticmethod
    def _plain(i):
        m = POINTER.match(str(i))
        return (m.group(1) if m else str(i)).split('#', 1)[0]

    def where(self, bid):
        """(store, n) of the first store that keeps the being, or (None, None)."""
        for s in self.S:
            n = s.n(bid)
            if n is not None:
                return s, n
        return None, None

    # ---- nodes
    def node(self, bid, sub=None, label=None, kind=None):
        fm = self.beans.get(bid)
        if fm is not None:
            return {'id': bid, 'kind': kind or str(fm.get('kind') or 'bean'), 'label': label or str(fm.get('title') or bid),
                    'sub': sub}
        s, n = self.where(bid)
        if s is None:
            return {'id': bid, 'kind': kind or 'unknown', 'label': label or bid, 'sub': sub}
        return self.snode(s, n, sub=sub, label=label)

    def snode(self, s, n, sub=None, label=None):
        bid, kind, title = s.row(n)
        fm = self.beans.get(bid)
        if fm is not None and not label:
            label = str(fm.get('title') or bid)
        if not label:
            if kind == 'folder':
                label = s.own_name(n) or bid
            elif kind == 'content':
                b3 = s.blake3(n)
                label = f'content {b3[:12]}' if b3 else bid
            else:
                label = title or bid
        return {'id': bid, 'kind': kind or 'unknown', 'label': label, 'sub': sub}

    def folder_node(self, s, f, sub=None):
        v, p = s.volume_path(f)
        where = f'{s.id(v)}:{p}' if p else s.id(v)
        return self.snode(s, f, sub=sub if sub is not None else where)

    # ---- what the page asks
    def aspects(self):
        rows = [r for r in _listed(self.L.profile_tables.get('aspects'))
                if isinstance(r, dict) and (r.get('home') == 'core' or r.get('home') in self.taken)]
        n = max(1, len(rows))
        out = [{'lens': str(r['aspect']), 'label': str(r['aspect']).replace('-', ' '), 'follows': r.get('follows'),
                'points': r.get('points'), 'order': r.get('order'), 'of': [str(k) for k in _listed(r.get('of'))],
                'says': r.get('meaning'), 'home': r.get('home'), 'turn': round(360 * i / n),
                'drawn': str(r['aspect']) in DRAWN} for i, r in enumerate(rows)]
        orient = [r for r in _listed(self.L.profile_tables.get('orientations')) if isinstance(r, dict)]
        with self:
            starts = self.starts()
        return {'aspects': out, 'orientations': orient, 'starts': starts, 'gardener': self.gardener,
                'stores': list(self.store_paths)}

    def starts(self):
        """Where a blank board may begin: what carries each volume the stores keep, else the volume itself."""
        out, seen = [], set()
        for s in self.S:
            for (v,) in s.q("SELECT n FROM being WHERE kind = 'volume' LIMIT 200"):
                cs = [c for (c,) in s.carriers(v)] or [v]
                for c in cs:
                    bid = s.id(c)
                    if bid not in seen:
                        seen.add(bid)
                        out.append(self.snode(s, c, sub=f'holds {s.id(v)}' if c != v else s.name))
        return out[:48]

    def lens(self, aspect, ids):
        row = next((a for a in self.aspects()['aspects'] if a['lens'] == aspect), None)
        if row is None:
            raise Refused(f"`{aspect}` is no aspect of this garden's board (the law's `aspects`, of the profiles it takes)")
        ids = [self._plain(i) for i in ids if str(i).strip()][:CURSORS]
        with self:
            cursor = [self.node(i) for i in ids]
            if not row['drawn']:
                return {'lens': aspect, 'cursor': cursor, 'groups': [],
                        'note': f'the aspect {aspect} is not drawn by this release yet'}
            fn = getattr(self, 'a_' + aspect.replace('-', '_'))
            groups = []
            for k, i in enumerate(ids):
                for g in fn(i):
                    g['side'] = k
                    groups.append(g)
            if len(ids) > 1 and aspect == 'holds':
                groups += self.shared(ids)
        return {'lens': aspect, 'cursor': cursor, 'groups': groups, 'note': None}

    # ---- the aspects
    def a_holds(self, i):
        out = []
        held =[(self._plain(r.get('of')), r) for _b, r in self.index.get(('hold', 'by', i), [])]
        if held:
            out.append(group(f'holds:{i}', 'holds, as the garden says', [self.node(o, sub=r.get('as')) for o, r in held
                                                                            if isinstance(r.get('of'), str)],
                             relation='hold'))
        s, n = self.where(i)
        if s is None:
            return out
        if s.kind(n) not in ('folder', 'volume'):
            vols = [v for (v,) in s.carries(n)]
            if vols:
                out.append(group(f'volumes:{i}', 'volumes', [self.snode(s, v, sub=f'on {i}') for v in vols],
                                 relation='hold'))
            return out
        kids = s.folders_in(n)
        cn = s.counts([f for f, _nm in kids])
        out.append(group(f'folders:{i}', 'folders', [self.snode(s, f, label=_text(nm), sub=f'{cn[f][0]:,} folders · '
                                                                  f'{cn[f][1]:,} files') for f, nm in kids],
                         relation='part', total=len(kids)))
        files, seen = [], set()
        for c, nm in s.held_in(n):
            if c in seen:
                continue
            seen.add(c)
            files.append(self.snode(s, c, label=_text(nm), sub=size(s.bytes_of(c))))
        out.append(group(f'files:{i}', 'files', files, relation='hold'))
        return [g for g in out if g['members'] or g['total']]

    def shared(self, ids):
        """What every being of the cursor holds beneath it, by the folders it sits in, the pairs holding most first."""
        sides = []
        for i in ids:
            s, n = self.where(i)
            if s is None or (sides and s is not sides[0][0]):
                return [group('shared', 'nothing held in common is read across two stores', [], side='shared',
                              relation='hold')]
            sides.append((s, n))
        s = sides[0][0]
        per = []
        for _s, n in sides:
            fs = s.beneath(n)
            where = {}
            for k in range(0, len(fs), 500):
                part = fs[k:k + 500]
                for by, c, nm in s.q(f"SELECT b_by, b_of, t_as FROM v_hold WHERE b_by IN ({','.join('?' * len(part))}) "
                                     "AND t_as IS NOT NULL", *part, need=('v_hold',)):
                    where.setdefault(c, (by, nm))
            per.append(where)
        common = set(per[0]).intersection(*per[1:])
        pairs = collections.defaultdict(list)
        for c in common:
            pairs[tuple(p[c][0] for p in per)].append(c)
        out = []
        for fs, cs in sorted(pairs.items(), key=lambda x: -len(x[1]))[:PAIRS]:
            label = ' · '.join((self.folder_node(s, f)['sub'] or '') for f in fs)
            out.append(group('shared:' + ','.join(s.id(f) for f in fs), label,
                             [self.snode(s, c, label=_text(per[0][c][1])) for c in cs], side='shared',
                             relation='hold', note=f'{len(cs):,} held by each'))
        if not out:
            out.append(group('shared', 'nothing held in common', [], side='shared', relation='hold'))
        return out

    def a_carried_by(self, i):
        out = []
        by = [self._plain(r.get('by')) for _b, r in self.index.get(('hold', 'of', i), []) if isinstance(r.get('by'), str)]
        whole = [self._plain(r.get('of')) for b, r in self.index.get(('part', 'by', i), []) if isinstance(r.get('of'), str)]
        if by:
            out.append(group(f'held-by:{i}', 'held by, as the garden says', [self.node(x) for x in by], at='before',
                             relation='hold'))
        if whole:
            out.append(group(f'part-of:{i}', 'part of', [self.node(x) for x in whole], at='before', relation='part'))
        s, n = self.where(i)
        if s is None:
            return out
        kind = s.kind(n)
        if kind == 'content':
            per = collections.defaultdict(list)
            for f, nm, _h in s.holdings(n):
                v, p = s.volume_path(f)
                per[v].append(self.snode(s, f, sub=f'{p}/{_text(nm)}' if p else _text(nm)))
            for v, members in per.items():
                cs = ', '.join(s.id(c) for (c,) in s.carriers(v))
                out.append(group(f'in:{s.id(v)}', f'{s.id(v)}' + (f' on {cs}' if cs else ''), members, at='before',
                                 relation='hold', head=self.snode(s, v)))
        elif kind == 'folder':
            p = s.parent(n)
            if p is not None:
                out.append(group(f'up:{i}', 'in', [self.folder_node(s, p) if s.kind(p) == 'folder' else self.snode(s, p)],
                                 at='before', relation='part'))
            v, _path = s.volume_path(n)
            if v is not None and v != p:
                out.append(group(f'vol:{i}', 'on the volume', [self.snode(s, v)], at='before', relation='part'))
        elif kind == 'volume':
            cs = [c for (c,) in s.carriers(n)]
            if cs:
                out.append(group(f'carriers:{i}', 'carried by', [self.snode(s, c) for c in cs], at='before',
                                 relation='hold'))
        return out

    def a_copies(self, i):
        s, n = self.where(i)
        if s is None or s.kind(n) != 'content':
            return []
        sources, copies = [], []
        for f, nm, h in s.holdings(n):
            made = s.made(f, h)
            where = self.folder_node(s, f)['sub']
            if made:
                src = ', '.join(self.folder_node(s, s.n(r.split('#', 1)[0]))['sub'] if s.n(r.split('#', 1)[0])
                                is not None else r.split('#', 1)[0] for r in made[0])
                copies.append(self.snode(s, f, sub=f'{where}/{_text(nm)} · copied {made[1]} from {src}'))
            else:
                sources.append(self.snode(s, f, sub=f'{where}/{_text(nm)}'))
        return [g for g in (group(f'held:{i}', 'held', sources, at='before', relation='hold'),
                            group(f'copied:{i}', 'copied to', copies, at='after', relation='make')) if g['members']]

    def a_in_backup(self, i):
        s, n = self.where(i)
        if s is None:
            return []
        if s.kind(n) == 'content':
            places = [f for f, _nm, h in s.holdings(n) if s.made(f, h)][:6]
        elif s.kind(n) in ('folder', 'volume'):
            places = [n]
        else:
            return []
        out = []
        for f in places:
            per = collections.defaultdict(list)
            names = {_text(h): (c, _text(nm)) for c, nm, h in
                     s.q("SELECT b_of, t_as, id FROM v_hold WHERE b_by = ? AND t_as IS NOT NULL", f, need=('v_hold',))}
            for made, src, _at in s.makes_in(f):
                c, nm = names.get(made[0].split('#', 1)[-1], (None, None)) if made else (None, None)
                if c is None or c == n:
                    continue
                sv = src[0].split('#', 1)[0] if src else ''
                vn = s.n(sv)
                vol = s.id(s.volume_path(vn)[0]) if vn is not None else sv or 'unknown'
                per[vol].append(self.snode(s, c, label=nm))
            head = self.folder_node(s, f)
            for vol, members in sorted(per.items(), key=lambda x: -len(x[1])):
                out.append(group(f'from:{s.id(f)}:{vol}', f'from {vol}', members, at='after', relation='make',
                                 head=head, note=f'copied into {head["sub"]}'))
        return out

    # ---- the aspects of groupings and storage, read by their own tools
    def _catalogue(self, s):
        import group as dmgroup
        C = dmgroup.Catalogue.__new__(dmgroup.Catalogue)
        C.path, C.db, C._tree = s.path, s.db, None
        return dmgroup, C

    def a_its_series(self, i):
        s, n = self.where(i)
        if s is None or s.kind(n) not in ('content', 'folder'):
            return []
        G, C = self._catalogue(s)
        L = G.Law(self.root)
        folders = [n] if s.kind(n) == 'folder' else [f for f, _nm, _h in s.holdings(n, limit=6)]
        out, shown = [], {}                 # a being is drawn once: a copy's series is said of the first, not drawn again
        for f in folders:
            runs = G.runs_of(L, C, f)
            if s.kind(n) == 'content':
                runs = [r for r in runs if n in r['contents']]
            W = G.Writers(C, C.made({c for r in runs for c in r['contents'] if c}))
            for r in sorted(runs, key=lambda r: -len(r['members']))[:12]:
                mine = frozenset(c for c in r['contents'] if c)
                if mine in shown:
                    g = shown[mine]
                    g['note'] += f" · the same {len(mine):,} contents in {self.folder_node(s, f)['sub']}"
                    continue
                line = G.groupings.line(r, L.groupings['name-series']['line'], W.table())
                members = [self.snode(s, c, label=t) for c, t in zip(r['contents'], r['texts']) if c]
                shown[mine] = group(f"series:{s.id(f)}:{r.get('template')}", line, members, relation='name-series',
                                    head=self.folder_node(s, f), total=len(r['members']),
                                    note=f"the row {r['code']}" if r.get('code') else 'its shape, mined')
                out.append(shown[mine])
        return out

    def a_its_class(self, i):
        s, n = self.where(i)
        if s is None or s.kind(n) not in ('content', 'folder', 'volume'):
            return []
        G, C = self._catalogue(s)
        out = []
        for scheme, code, source, through in G.classes_of(G.Law(self.root), C, n, G.said_codes(self.root)):
            tn = s.n(through) if through else None
            head = self.folder_node(s, tn) if tn is not None and tn != n and s.kind(tn) == 'folder' else None
            out.append(group(f'class:{scheme}', f"{code or scheme + ': —'} · {source}", [head] if head else [],
                             at='before', relation='root', note=f'{source} from' if head else source))
        return out

    def _storage(self):
        path = os.path.join(self.root, 'assets', 'storage', 'bin', 'storage.py')
        if 'storage' not in self.taken or not os.path.isfile(path):
            return None
        os.environ.setdefault('DAFTAR_GARDEN', self.root)
        spec = importlib.util.spec_from_file_location('storage_asset', path)
        ST = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(ST)
        return ST

    def _sstore(self, ST, s):
        St = ST.Store.__new__(ST.Store)
        St.db, St.tables, St.ids, St.kinds, St._parent, St._vol = s.db, s.tables, {}, {}, None, {}
        for n, bid, kind in s.db.execute("SELECT n, id, kind FROM being WHERE kind IN ('volume', 'host')"):
            St.ids[n], St.kinds[n] = bid, kind
        return St

    def a_its_dataset(self, i):
        s, n = self.where(i)
        ST = self._storage()
        if s is None or ST is None or s.kind(n) not in ('content', 'folder'):
            return []
        from core import formats
        St = self._sstore(ST, s)
        if s.kind(n) == 'folder':
            folders = [n] + self._same_tree(ST, St, s, n)
        else:
            folders = [f for f, _nm, _h in s.holdings(n, limit=12) if s.kind(f) == 'folder']
        per = collections.defaultdict(list)
        for f in folders:
            T, _fs = ST.trees(St, s.id(f))
            man = T.manifest(f)
            per[(formats.blake3_hex(man), man.count(b'\n')) if man else (None, 0)].append(f)
        out = []
        for (d, files), fs in per.items():
            vols = {s.volume_path(f)[0] for f in fs}
            out.append(group(f'dataset:{d}', f'{d[:16]}… · {files:,} files · {len(fs)} folder(s) on {len(vols)} '
                             f'volume(s)' if d else 'no dataset: a content in its tree was not read',
                             [self.folder_node(s, f) for f in fs], at='after' if n in fs else 'before',
                             relation='datasets', note='every folder found holding this tree'))
        return out

    def _same_tree(self, ST, St, s, n):
        """The other folders that hold the tree beneath `n`: found through the holders of its content held fewest
        times, climbed as far as that content sits below `n`, and kept where their trees' fingerprints are the same."""
        T, _fs = ST.trees(St, s.id(n))
        depth = {}
        for f in T.files:
            k, x = 0, f
            while x != n and x is not None and k < 4096:
                x, k = s.parent(x), k + 1
            depth[f] = k
        rare = None
        for f, lst in T.files.items():
            for _nm, b3 in lst[:400]:
                c = s.n('c-' + str(b3)[:24]) if b3 else None
                if c is None:
                    continue
                k = len(s.holdings(c, limit=401))
                if rare is None or k < rare[1]:
                    rare = (c, k, depth.get(f, 0))
        if rare is None or rare[1] > 400:
            return []
        fp, same = T.fingerprint(n), []
        for f, _nm, _h in s.holdings(rare[0]):
            x = f
            for _ in range(rare[2]):
                x = s.parent(x) if x is not None else None
            if x is None or x == n or x in same or s.kind(x) != 'folder':
                continue
            if ST.trees(St, s.id(x))[0].fingerprint(x) == fp:
                same.append(x)
        return same

    def a_its_safety(self, i):
        s, n = self.where(i)
        ST = self._storage()
        if s is None or ST is None or s.kind(n) not in ('content', 'folder', 'volume'):
            return []
        St, W = self._sstore(ST, s), ST.Words(self.root)
        scheme = next((k for k, r in getattr(W.K, 'schemes', {}).items() if isinstance(r, dict) and r.get('form') == 'keep'),
                      None)
        groups, judged = ST.keepings(St, W, scheme, s.id(n), None, each=[])
        if s.kind(n) == 'content':
            out = []
            for j in judged[:1]:
                out.append(group('safety:policy', f"{j['code'] or 'no policy'} · {j['line']}", [], at='before',
                                 relation='keepings'))
                for k in j['keepings']:
                    flags = ', '.join(x for x, y in (('offline', k.get('offline')), ('its key not held twice',
                                                     k.get('key') is False)) if y)
                    out.append(group(f"safety:{k['volume']}", f"{k['volume']} · disks {', '.join(k['disks']) or 'none said'}"
                                     + (f' · {flags}' if flags else ''), [], relation='keepings'))
            return out
        return [group(f'safety:{c}:{ln}', f'{c} · {k:,} contents · {size(b)} · {ln}', [], relation='keepings')
                for (c, ln), (k, b) in sorted(groups.items(), key=lambda x: -x[1][1])[:20]]

    # ---- the sheet, and finding
    def being(self, bid):
        bid = self._plain(bid)
        with self:
            node = self.node(bid)
            sheet = {'id': bid, 'kind': node['kind'], 'title': node['label'], 'sub': node.get('sub') or '',
                     'facts': [], 'lists': [], 'garden': None, 'from': []}
            fm = self.beans.get(bid)
            if fm is not None:
                sheet['garden'] = {'bean': bid, 'title': str(fm.get('title') or ''), 'summary': str(fm.get('summary') or ''),
                                   'statements': [f'{v}: ' + json.dumps(r, ensure_ascii=False, default=str)
                                                  for _i, v, r in self.pass_.statements(fm)][:200]}
                sheet['from'].append(f'the garden: beans/{bid}.md')
            s, n = self.where(bid)
            if s is not None:
                kind = s.kind(n)
                sheet['facts'].append(['kind', kind or ''])
                if kind == 'folder':
                    v, p = s.volume_path(n)
                    c = s.counts([n])[n]
                    sheet['facts'] += [['volume', s.id(v) or ''], ['path', p], ['folders', f'{c[0]:,}'],
                                       ['files', f'{c[1]:,}']]
                elif kind == 'volume':
                    sheet['facts'].append(['carried by', ', '.join(s.id(c) for (c,) in s.carriers(n)) or 'none said'])
                    sheet['facts'].append(['folders at its top', f'{len(s.folders_in(n)):,}'])
                elif kind == 'content':
                    sheet['facts'] += [['blake3', s.blake3(n) or 'not read'], ['size', size(s.bytes_of(n))]]
                    rows = []
                    for f, nm, _h in s.holdings(n, limit=50):
                        v, p = s.volume_path(f)
                        rows.append([s.id(v) or '', f'{p}/{_text(nm)}' if p else _text(nm)])
                    sheet['lists'].append({'title': 'held as', 'cols': ['volume', 'path'], 'rows': rows})
                else:
                    vols = [s.id(v) for (v,) in s.carries(n)]
                    if vols:
                        sheet['facts'].append(['holds', ', '.join(vols)])
                sheet['from'].append(f'the store {s.name}')
        return sheet

    def find(self, text, ids):
        text = str(text or '').strip()
        if len(text) < 3:
            raise Refused('a find needs three letters at least')
        like = '%' + text.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_') + '%'
        out = []
        with self:
            for k, i in enumerate([self._plain(x) for x in ids][:CURSORS]):
                s, n = self.where(i)
                if s is None:
                    continue
                fs = s.beneath(n)
                found, seen = [], set()
                for at in range(0, len(fs), 500):
                    part = fs[at:at + 500]
                    marks = ','.join('?' * len(part))
                    for f, c, nm in s.q(f"SELECT b_by, b_of, t_as FROM v_hold WHERE b_by IN ({marks}) AND t_as IS NOT "
                                        f"NULL AND t_as LIKE ? ESCAPE '\\' LIMIT ?", *part, like, LIMIT + 1,
                                        need=('v_hold',)):
                        if c not in seen:
                            seen.add(c)
                            found.append(self.snode(s, c, label=_text(nm), sub=self.folder_node(s, f)['sub']))
                    for f, nm in s.q(f"SELECT b_of, t_as FROM v_name WHERE b_by IN ({marks}) AND {Store.OWN} AND t_as "
                                     f"LIKE ? ESCAPE '\\' LIMIT ?", *part, like, LIMIT + 1, need=('v_name',)):
                        if f not in seen:
                            seen.add(f)
                            found.append(self.folder_node(s, f))
                    if len(found) > LIMIT:
                        break
                out.append(group(f'found:{i}', f'“{text}” in {i}', found, side=k, relation='find'))
        return {'groups': out}


def main(root, argv):
    """`view board …`: the board's answers printed, as the worker gives them to the page."""
    usage = ('usage: view board aspects | lens <aspect> <id>… | being <id> | find <text> <id>…')
    if not argv:
        print(usage, file=sys.stderr)
        return 2
    try:
        B = Board(root)
        cmd, rest = argv[0], argv[1:]
        if cmd == 'aspects':
            out = B.aspects()
        elif cmd == 'lens' and len(rest) >= 2:
            out = B.lens(rest[0], rest[1:])
        elif cmd == 'being' and len(rest) == 1:
            out = B.being(rest[0])
        elif cmd == 'find' and len(rest) >= 2:
            out = B.find(rest[0], rest[1:])
        else:
            print(usage, file=sys.stderr)
            return 2
    except Refused as e:
        print(f'board: {e}', file=sys.stderr)
        return 1
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    return 0
