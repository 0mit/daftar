#!/usr/bin/env python3
"""storage — the storage profile's readings at a store's scale (core 2.19; assets/storage/README.md): what each
content's keepings leave open, which folders hold one dataset, the events of a tree's contents, a tree's manifest.

    python3 assets/storage/bin/storage.py keepings [--store S] [--scheme <keep scheme>] [--of <being>] [--now <moment>]
                                                   [--json]
    python3 assets/storage/bin/storage.py datasets [--store S] [--of <folder>] [--same] [--json]
    python3 assets/storage/bin/storage.py events --gap "36 h" [--store S] [--of <volume or folder>] [--json]
    python3 assets/storage/bin/storage.py manifest <folder> [--store S]          a tree's manifest, to standard output

The rules are the law's and the garden's: the keeping properties (core/law/profiles.yaml `keeping_properties`), the
garden's risks (VOCAB.md `risks`), a policy scheme of the form `keep`, the groupings `keepings`, `datasets` and
`events` (core/law/lines.yaml); core/storage.py judges. The store is read in one snapshot and never written; what a
person says — a policy code of a root, a disk's place, that a key is held — is read from the garden's beans.
`--store` names a store this host keeps (`details.stores`), or a path; absent, the only one a host keeps that holds
holdings.
"""
import argparse
import collections
import json
import os
import re
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
GARDEN = os.environ.get('DAFTAR_GARDEN') or os.getcwd()
sys.path[:0] = [ROOT, os.path.join(ROOT, 'bin')]
import parse as dmparse  # noqa: E402,F401 — UTF-8 on stdout and stderr
from core import formats, groupings, storage  # noqa: E402

SIZE = "CAST(json_extract(CAST(m.q_value AS TEXT), '$.count') AS INTEGER)"


def secs(position):
    """Seconds since the epoch of a moment `2026-10-19T22:21:28+03:00` (its fraction kept), or of a day's first moment
    in UTC; None for what is no position of time."""
    import datetime
    s = str(position or '').strip()
    try:
        return datetime.datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp() if 'T' in s else \
            datetime.datetime.fromisoformat(s + 'T00:00:00+00:00').timestamp()
    except ValueError:
        return None


def duration(text):
    """Seconds in `<count> <unit>` (`36 h`, `365 d`)."""
    m = re.fullmatch(r'\s*(\d+(?:\.\d+)?) ?(s|min|h|d|wk)\s*', str(text or ''))
    if not m:
        raise SystemExit(f"storage: {text!r} is no length of time: a count and a unit of s, min, h, d, wk")
    return float(m.group(1)) * {'s': 1, 'min': 60, 'h': 3600, 'd': 86400, 'wk': 604800}[m.group(2)]


# ------------------------------------------------------------------------------------------------ the garden's words
class Words:
    """What the garden's beans say that the readings need: the codes said of beings (a `classify`, a store's being by
    its pointer), the hosts, what is part of a host, the disks' places, the keys a carrier needs and who holds them, the
    garden's risks and its policy schemes."""

    def __init__(self, root):
        import reckon as dmreckon
        g = dmreckon.Garden(root)
        self.said = collections.defaultdict(list)
        self.kind, self.parts, self.places = {}, collections.defaultdict(set), collections.defaultdict(set)
        self.needs, self.keepers = collections.defaultdict(set), collections.defaultdict(set)

        def own(v, b):
            if isinstance(v, str) and v.startswith('store:'):
                return v.split(':', 2)[2].split('#')[0]
            return dmreckon._own(v, b)
        for b, fm in g.fm.items():
            if g.kind.get(b) != 'beans':
                continue
            self.kind[b] = str((fm or {}).get('kind') or '')
            for verb in ('classify', 'part', 'be', 'need', 'hold'):
                for x, _w in dmreckon._flatten(dmreckon.walk(g, fm, verb, at=b)):
                    if not isinstance(x, dict):
                        continue
                    if verb == 'classify' and x.get('as'):
                        self.said[own(x.get('of'), b)].append(str(x['as']))
                    elif verb == 'part' and x.get('of'):
                        self.parts[own(x.get('by'), b)].add(own(x['of'], b))
                    elif verb == 'be' and x.get('as') == 'location' and x.get('at'):
                        self.places[own(x.get('by'), b)].add(str(x['at']))
                    elif verb == 'need':
                        for k in x.get('of') if isinstance(x.get('of'), list) else [x.get('of')]:
                            if k:
                                self.needs[own(x.get('by'), b)].add(own(k, b))
                    elif verb == 'hold' and x.get('of') and x.get('as') is None:
                        for k in x['of'] if isinstance(x['of'], list) else [x['of']]:
                            if isinstance(k, str):
                                self.keepers[own(k, b)].add(own(x.get('by'), b))
        from core import check as core_check
        L = core_check.garden_law(root)
        self.risks = {str(r['risk']): [w for w in r.get('resolved_by') or [] if isinstance(w, dict)]
                      for r in (getattr(L, 'profile_tables', {}) or {}).get('risks') or [] if isinstance(r, dict)}
        import knowledge as dmknowledge
        self.K = dmknowledge.Knowledge(root)

    def hosts(self):
        return {b for b, k in self.kind.items() if k == 'host'}

    def policy(self, scheme):
        if not scheme:
            return {}
        try:
            return {str(r.get('code')): r for r in self.K.rows(scheme)}
        except (KeyError, OSError) as e:
            raise SystemExit(f"storage: the scheme {scheme} cannot be read here: {e}")


# ------------------------------------------------------------------------------------------------ the store
class Store:
    """A store read as storage: its volumes and folders, each folder's volume, each volume's carriers, the holdings of
    each content — in one snapshot, never written."""

    def __init__(self, path):
        self.db = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=30)
        self.db.execute('PRAGMA cache_size = -800000')
        self.db.execute('BEGIN')
        self.tables = {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.ids, self.kinds = {}, {}
        for n, bid, kind in self.db.execute('SELECT n, id, kind FROM being WHERE kind IN ("volume", "host")'):
            self.ids[n], self.kinds[n] = bid, kind
        self._parent = None
        self._vol = {}

    def n_of(self, bid):
        r = self.db.execute('SELECT n, kind FROM being WHERE id = ?', (bid,)).fetchone()
        if r:
            self.ids.setdefault(r[0], bid)
            self.kinds.setdefault(r[0], r[1])
        return r[0] if r else None

    def id_of(self, n):
        if n not in self.ids:
            r = self.db.execute('SELECT id, kind FROM being WHERE n = ?', (n,)).fetchone()
            self.ids[n], self.kinds[n] = (r[0], r[1]) if r else (None, None)
        return self.ids[n]

    def parent(self):
        """{folder n: (parent n, name)}: every folder named by the folder or the volume it is part of."""
        if self._parent is None:
            self._parent = {of: (by, nm) for of, by, nm in self.db.execute(
                f"SELECT b_of, b_by, t_as FROM v_name WHERE {formats.OWN_NAME}")}
        return self._parent

    def volume_of(self, f):
        """The volume a folder is of, climbing its parents; the being itself where it is a volume."""
        P, path = self.parent(), []
        while f not in self._vol:
            if self.kinds.get(f) == 'volume' or f not in P:
                self._vol[f] = f
                break
            path.append(f)
            f = P[f][0]
        for x in path:
            self._vol[x] = self._vol[f]
        return self._vol[f]

    def carriers(self):
        """{volume n: [carrier n]}: what holds each volume — a disk, or a content that carries it."""
        out = collections.defaultdict(list)
        vols = [n for n, k in self.kinds.items() if k == 'volume']
        for by, of in self.db.execute(f"SELECT b_by, b_of FROM v_hold WHERE t_as IS NULL AND b_of IN "
                                      f"({','.join('?' * len(vols))})", vols):
            out[of].append(by)
        return out

    def scanned(self):
        """{volume n: the last moment a reading of it read its bytes (a scan), in seconds}."""
        out = {}
        if 'v_read' in self.tables:
            for being, at in self.db.execute("SELECT being, max(t_at) FROM v_read GROUP BY being"):
                out[being] = secs(at)
        return out

    def made_at(self):
        """{act n: seconds} of each knowing act that is a `make` (a copy checked by its digest when it was made)."""
        out = {}
        if 'v_make' not in self.tables:
            return out
        for n, at in self.db.execute("SELECT a.n, m.t_at FROM v_make m JOIN being b ON b.n = m.being "
                                     "JOIN act a ON a.ref = b.id || '#' || m.id"):
            out[n] = secs(at)
        return out

    def holdings(self, contents=None, names=False):
        """(content n, folder n, through, act n[, name]) of every holding under a name, content by content."""
        th = "t_through" if self._has('v_hold', 't_through') else "NULL"
        if contents is None:
            yield from self.db.execute(f"SELECT b_of, b_by, {th}, known{', t_as' if names else ''} FROM v_hold "
                                       "WHERE t_as IS NOT NULL AND b_of IS NOT NULL ORDER BY b_of")
            return
        self.db.execute('CREATE TEMP TABLE IF NOT EXISTS kc (n INTEGER PRIMARY KEY)')
        self.db.execute('DELETE FROM temp.kc')
        self.db.executemany('INSERT OR IGNORE INTO temp.kc VALUES (?)', ((n,) for n in contents))
        yield from self.db.execute(f"SELECT h.b_of, h.b_by, {th.replace('t_', 'h.t_') if th != 'NULL' else th}, "
                                   f"h.known{', h.t_as' if names else ''} FROM temp.kc JOIN v_hold h ON "
                                   "h.b_of = temp.kc.n WHERE h.t_as IS NOT NULL ORDER BY h.b_of").fetchall()

    def _has(self, table, col):
        return col in {r[1] for r in self.db.execute(f'PRAGMA table_info({table})')}

    def sizes(self, contents):
        out = {}
        for n, sz in self.db.execute(f"SELECT m.being, {SIZE} FROM v_measure m WHERE m.t_as = 'information' AND "
                                     f"m.being IN ({','.join('?' * len(contents))})", list(contents)):
            out[n] = sz or 0
        return out

    def beneath(self, n):
        """Every folder beneath a folder or a volume, and itself."""
        kids = collections.defaultdict(list)
        for f, (p, _nm) in self.parent().items():
            kids[p].append(f)
        out, stack = [], [n]
        while stack:
            x = stack.pop()
            out.append(x)
            stack.extend(kids.get(x, ()))
        return out


def dmgroup_text(name):
    """A name the store keeps `escaped`, as the text a pattern reads."""
    return formats.unescape(name).decode('utf-8', 'replace') if '%' in name else name


def store_path(name, root):
    if name and os.path.sep in name:
        return name
    import store as dmstore
    kept = dmstore.kept_here(root)
    if name is None:
        if len(kept) != 1:
            raise SystemExit(f"storage: say which store (`--store`): {', '.join(sorted(kept)) or 'none is kept here'}")
        name = next(iter(kept))
    if name not in kept:
        raise SystemExit(f"storage: the store {name!r} is not kept on this host: {', '.join(sorted(kept)) or 'none'}")
    st = dmstore.open_store(name, root=root, create=False)
    path = st.path
    st.close()
    return path


# ------------------------------------------------------------------------------------------------ keepings
def keepings(S, W, scheme=None, of=None, now=None, each=None):
    """{(code, open line): [contents, bytes]}, and with `each` the judgement of every content of `of`. A content's code
    is the nearest said of it or of a folder that holds it, up its parents — a code of the policy scheme, or the code
    whose `for` names a code said there, or an `apart` code a pattern the folder's name fits suggests (a program's
    tree), as `inherit` reads them; else the code whose `for` names a code a pattern a name of the content fits
    suggests (its media class)."""
    policy = W.policy(scheme)
    forcode = {c: f"{scheme}:{k}" for k, r in policy.items() for c in str(r.get('for') or '').split()}
    L = media = None
    fitted = {}
    if scheme:
        import group as dmgroup                    # the garden's pattern rows, its own first (bin/group.py)
        from core import groupings
        L = dmgroup.Law(GARDEN)
        try:                                       # a file's media type, by shared-mime-info's rows (`media-types`)
            media = groupings.Media(L.K.rows('media-types'))
        except (KeyError, OSError):
            media = groupings.Media([])

    def suggests(text, reads='as'):
        """The codes the first pattern row a name fits suggests, each name fitted once."""
        key = (text, reads)
        if key not in fitted:
            r = L.fits(text, reads=reads)[0]
            fitted[key] = r.suggests if r else ()
            if len(fitted) > 2_000_000:
                fitted.clear()
        return fitted[key]
    path_rows = [r for r in L.rows if r.reads == 'path'] if L is not None else []
    paths = {}

    def path_suggests(f, name):
        """The codes the rows that read a path suggest for a name its folder `f` holds."""
        if f not in paths:
            p = formats.path_of(S.db, f)
            if p is None and f in P:                 # a store read before core 2.22: the path walked up the parents
                chain, x = [], f
                while x in P:
                    chain.append(P[x][1])
                    x = P[x][0]
                p = '/'.join(reversed(chain))
            if len(paths) > 500_000:
                paths.clear()
            paths[f] = dmgroup_text(p) if p is not None else None
        p = paths[f]
        return groupings.path_codes(path_rows, f"{p}/{name}" if p else name)
    hosts, P = W.hosts(), S.parent()
    carriers, scanned, made = S.carriers(), S.scanned(), S.made_at()
    now = time.time() if now is None else now

    def disks(v, seen=()):
        out = set()
        for c in carriers.get(v, ()):
            cid = S.id_of(c)
            if cid in hosts or S.kinds.get(c) == 'host':
                out.add(cid)
            elif c not in seen:                    # a content that carries the volume: its keepings' disks
                for (f,) in S.db.execute('SELECT b_by FROM v_hold WHERE b_of = ? AND t_as IS NOT NULL', (c,)).fetchall():
                    out |= disks(S.volume_of(f), seen + (c,))
        return out
    vdisks = {}
    code_of = {}

    def folder_code(f):
        chain = []
        while f is not None and f not in code_of:
            chain.append(f)
            fid = S.id_of(f)
            mine = [c for c in W.said.get(fid, []) if scheme and c.startswith(scheme + ':')]
            if mine:
                code_of[f] = mine[0]
                break
            other = W.said.get(fid, [])
            hit = [forcode[c] for c in other if c in forcode]
            if not hit and L is not None and f in P:         # a folder's name sets its tree apart (a program's tree);
                hit = [forcode[c] for c in suggests(dmgroup_text(P[f][1]), 'name.as')   # a class is a file's own
                       if c in forcode and c in L.apart]
            if hit:
                code_of[f] = hit[0]
                break
            f = P.get(f, (None,))[0]
        found = code_of.get(f) if f is not None else None
        for x in chain:
            code_of[x] = found
        return found
    groups = collections.defaultdict(lambda: [0, 0])
    judged = []
    batch = []

    def flush():
        sz = S.sizes([c for c, _k in batch]) if batch else {}
        for c, keeps_ in batch:
            cid = S.id_of(c)
            code = next((x for x in W.said.get(cid, []) if scheme and x.startswith(scheme + ':')), None)
            if code is None and scheme:
                codes = [folder_code(f) for f in keeps_['folders']]
                code = next((x for x in codes if x), None)
            if code is None and L is not None:
                for nm in keeps_['names']:              # a media class is read of a picture, a video or a sound
                    t = dmgroup_text(nm)
                    if media.of(t)[1].split('-')[0] not in ('image', 'video', 'audio') and \
                            media.of(t)[0].split('/')[0] not in ('image', 'video', 'audio'):
                        continue
                    hit = [forcode[c] for c in suggests(t) if c in forcode]
                    if not hit and path_rows:            # ...or by its path beneath its volume (`reads: path`)
                        hit = [forcode[c] for c in path_suggests(keeps_['folders'][keeps_['names'].index(nm)], t)
                               if c in forcode]
                    if hit:
                        code = hit[0]
                        break
            row = policy.get(code.split(':', 1)[1]) if code else None
            covers = str(row.get('covers') or '').split() if row else None
            within = duration(row['within']) if row and row.get('within') else None
            j = storage.judge(keeps_['keeps'], W.risks, covers, within, now)
            line = ('safe' if covers is not None and not j['open'] else
                    '; '.join(storage.lacking(e) for e in j['open']) if j['open'] else
                    'resolves ' + (', '.join(j['resolved']) or 'nothing'))
            g = groups[(code or 'no policy', line)]
            g[0] += 1
            g[1] += sz.get(c, 0)
            if each is not None:
                judged.append({'content': cid, 'code': code, 'line': line, 'bytes': sz.get(c, 0),
                               'keepings': [{'volume': S.id_of(k.volume), 'disks': sorted(k.disks),
                                             'places': sorted(k.places), 'offline': k.offline,
                                             'verified': k.verified, 'key': k.key} for k in keeps_['keeps']]})
        batch.clear()
    contents = None
    if of is not None:
        n = S.n_of(of)
        if n is None:
            raise SystemExit(f"storage: {of!r} is kept in no store here")
        if S.kinds.get(n) == 'content' or of.startswith('c-'):
            contents = [n]
        else:
            fs = S.beneath(n)
            S.db.execute('CREATE TEMP TABLE IF NOT EXISTS kf (n INTEGER PRIMARY KEY)')
            S.db.execute('DELETE FROM temp.kf')
            S.db.executemany('INSERT OR IGNORE INTO temp.kf VALUES (?)', ((x,) for x in fs))
            contents = [r[0] for r in S.db.execute("SELECT DISTINCT h.b_of FROM temp.kf JOIN v_hold h ON h.b_by = "
                                                   "temp.kf.n WHERE h.t_as IS NOT NULL AND h.b_of IS NOT NULL")]
    cur, keeps, seen = None, None, set()
    for c, f, through, act, nm in S.holdings(contents, names=True):
        if c != cur:
            if cur is not None:
                batch.append((cur, keeps))
                if len(batch) >= 5000:
                    flush()
            cur, keeps, seen = c, {'keeps': [], 'folders': [], 'names': []}, set()
        keeps['folders'].append(f)
        keeps['names'].append(nm)
        if through:
            if through in seen:
                continue
            seen.add(through)
        v = S.volume_of(f)
        if v not in vdisks:
            vdisks[v] = disks(v)
        ds = vdisks[v]
        need = set().union(*[W.needs.get(x, set()) for x in ds | {S.id_of(v)}]) if ds else set()
        key_ok = all(len(W.keepers.get(k, ())) >= 2 for k in need)
        offline = bool(ds) and not any(W.parts.get(d, set()) & hosts for d in ds)
        verified = made.get(act) or scanned.get(v)
        keeps['keeps'].append(storage.Keeping(v, ds, set().union(*[W.places.get(d, set()) for d in ds]) if ds else (),
                                              offline=offline, verified=verified, key=key_ok))
    if cur is not None:
        batch.append((cur, keeps))
    flush()
    return groups, judged


# ------------------------------------------------------------------------------------------------ datasets
def trees(S, of=None):
    """(Trees, the folders asked): every folder beneath `of` (or of every volume) with its files' names and digests."""
    P = S.parent()
    roots = [S.n_of(of)] if of else [n for n, k in S.kinds.items() if k == 'volume']
    if None in roots:
        raise SystemExit(f"storage: {of!r} is kept in no store here")
    fs = [x for r in roots for x in S.beneath(r)]
    S.db.execute('CREATE TEMP TABLE IF NOT EXISTS tf (n INTEGER PRIMARY KEY)')
    S.db.execute('DELETE FROM temp.tf')
    S.db.executemany('INSERT OR IGNORE INTO temp.tf VALUES (?)', ((x,) for x in fs))
    files = []
    for by, nm, b3, sz in S.db.execute(
            "SELECT h.b_by, h.t_as, nb.t_as, " + SIZE.replace('m.', 'm.') + " FROM temp.tf JOIN v_hold h ON h.b_by = "
            "temp.tf.n LEFT JOIN v_name nb ON nb.being = h.b_of AND nb.t_by = 'blake3' LEFT JOIN v_measure m ON "
            "m.being = h.b_of AND m.t_as = 'information' WHERE h.t_as IS NOT NULL"):
        files.append((by, formats.unescape(nm), b3, sz))
    folders = {x: (P[x][0] if x in P and x not in roots else None) for x in fs}
    names = {x: formats.unescape(P[x][1]) for x in fs if x in P}
    return storage.Trees(folders, files, names), fs


# ------------------------------------------------------------------------------------------------ events
def events(S, of, gap, zone=None):
    """[(first, last, [(content, maker)])]: the contents beneath `of` by their moments, a new event after a longer gap;
    a content's moment its `produce.at`, else a date its name holds; and the contents with none."""
    from core import groupings
    n = S.n_of(of)
    if n is None:
        raise SystemExit(f"storage: {of!r} is kept in no store here")
    fs = S.beneath(n)
    S.db.execute('CREATE TEMP TABLE IF NOT EXISTS ef (n INTEGER PRIMARY KEY)')
    S.db.execute('DELETE FROM temp.ef')
    S.db.executemany('INSERT OR IGNORE INTO temp.ef VALUES (?)', ((x,) for x in fs))
    rows = S.db.execute("SELECT DISTINCT h.b_of, h.t_as, h.b_by FROM temp.ef JOIN v_hold h ON h.b_by = temp.ef.n "
                        "WHERE h.t_as IS NOT NULL AND h.b_of IS NOT NULL").fetchall()
    made = {}
    if 'v_produce' in S.tables:
        S.db.execute('CREATE TEMP TABLE IF NOT EXISTS ec (n INTEGER PRIMARY KEY)')
        S.db.execute('DELETE FROM temp.ec')
        S.db.executemany('INSERT OR IGNORE INTO temp.ec VALUES (?)', ((c,) for c, _n, _f in rows))
        for c, at, by in S.db.execute("SELECT p.b_of, p.t_at, coalesce(b.id, p.t_by) FROM temp.ec JOIN v_produce p ON "
                                      "p.b_of = temp.ec.n LEFT JOIN being b ON b.n = p.b_by"):
            made[c] = (at, by)
    day = re.compile(r'(?<!\d)((?:19|20)\d\d)[-_.]?(0[1-9]|1[0-2])[-_.]?(0[1-9]|[12]\d|3[01])(?!\d)')
    P, folder_day = S.parent(), {}

    def day_of_folder(f):
        """The day the nearest of a folder's names, up its parents, holds; or None."""
        chain = []
        while f is not None and f not in folder_day and f in P:
            chain.append(f)
            m = day.search(formats.unescape(P[f][1]).decode('utf-8', 'replace'))
            if m:
                folder_day[f] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
                break
            f = P[f][0]
        found = folder_day.get(f)
        for x in chain:
            folder_day[x] = found
        return found
    rows = S.db.execute("SELECT DISTINCT h.b_of, h.t_as, h.b_by FROM temp.ef JOIN v_hold h ON h.b_by = temp.ef.n "
                        "WHERE h.t_as IS NOT NULL AND h.b_of IS NOT NULL").fetchall()
    spans, none, seen = [], [], set()
    for c, nm, folder in rows:
        if c in seen:
            continue
        at, by = made.get(c, (None, None))
        start = secs(at) if at else None
        end = start + (86399.999 if at and 'T' not in str(at) else 0) if start is not None else None
        if start is None:
            m = day.search(formats.unescape(nm).decode('utf-8', 'replace'))
            d = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else day_of_folder(folder)
            if d:
                start = secs(d)
                end = start + 86399.999 if start is not None else None
        if start is None:
            continue                                # a name may hold its day where another of its names does not
        seen.add(c)
        spans.append((start, end, (S.id_of(c), by)))
    none = [S.id_of(c) for c, _n, _f in rows if c not in seen]
    out = []
    for g in storage.gap_groups(spans, gap):
        ss = [x for x in spans if x[2] in set(g)]
        out.append((min(x[0] for x in ss), max(x[1] for x in ss), g))
    return out, sorted(set(none))


# ------------------------------------------------------------------------------------------------ schemas
DAY = re.compile(r'(?<!\d)((?:19|20)\d\d)[-_.]?(0[1-9]|1[0-2])[-_.]?(0[1-9]|[12]\d|3[01])(?!\d)')
BLOBS_DIR = b'.blobs'


def layout(S, W, scheme, of, schema=None, sample=8):
    """How the members beneath a folder stand against the schema said of it (core 2.21, the operation `layout`):
    {node: {'in place': n, 'to link': n, 'out of place': n, 'samples': {...}}, '(no node)': ..., 'names out of place'}
    and the plan of a box: the names its nodes give that are not held yet (`to link`), each with the content's blob."""
    rows = [dict(r) for r in W.K.rows(scheme)]
    n = S.n_of(of)
    if n is None:
        raise SystemExit(f"storage: {of!r} is kept in no store here")
    if schema is None:
        said = [c.split(':', 1)[1] for c in W.said.get(of, []) if c.startswith(scheme + ':')]
        if not said:
            raise SystemExit(f"storage: no schema of {scheme} is said of {of} (`classify` of it)")
        schema = said[0]
    nodes = storage.nodes_of(rows, schema)
    box = any(str(r.get('links') or '') == 'true' for _c, _l, r in nodes)
    P = S.parent()
    fs = S.beneath(n)
    rel = {n: b''}
    for f in fs:                                       # each folder's path from the schema's directory
        if f in rel:
            continue
        chain, x = [], f
        while x not in rel and x in P:
            chain.append(x)
            x = P[x][0]
        base = rel.get(x, b'')
        for y in reversed(chain):
            nm = formats.unescape(P[y][1])
            base = base + b'/' + nm if base else nm
            rel[y] = base
    S.db.execute('CREATE TEMP TABLE IF NOT EXISTS lf (n INTEGER PRIMARY KEY)')
    S.db.execute('DELETE FROM temp.lf')
    S.db.executemany('INSERT OR IGNORE INTO temp.lf VALUES (?)', ((x,) for x in fs))
    members = S.db.execute(
        "SELECT h.b_by, h.t_as, h.b_of, h.known, nb.t_as FROM temp.lf JOIN v_hold h ON h.b_by = temp.lf.n "
        "LEFT JOIN v_name nb ON nb.being = h.b_of AND nb.t_by = 'blake3' WHERE h.t_as IS NOT NULL").fetchall()
    contents = {m[2] for m in members}
    made = {}
    if 'v_produce' in S.tables:
        S.db.execute('CREATE TEMP TABLE IF NOT EXISTS lc (n INTEGER PRIMARY KEY)')
        S.db.execute('DELETE FROM temp.lc')
        S.db.executemany('INSERT OR IGNORE INTO temp.lc VALUES (?)', ((c,) for c in contents if c))
        for c, at, by in S.db.execute("SELECT p.b_of, p.t_at, coalesce(b.id, p.t_by) FROM temp.lc JOIN v_produce p "
                                      "ON p.b_of = temp.lc.n LEFT JOIN being b ON b.n = p.b_by"):
            made[c] = (at, by)
    acts = {m[3] for m in members if m[3]}
    source = {}                                        # the act a copy is known by -> the holding it was made from
    if acts and 'v_make' in S.tables:
        for an in acts:
            ref = S.db.execute('SELECT ref FROM act WHERE n = ?', (an,)).fetchone()
            if not ref or '#' not in ref[0]:
                continue
            mb, mid = ref[0].split('#', 1)
            row = S.db.execute("SELECT m.t_from FROM v_make m JOIN being b ON b.n = m.being WHERE b.id = ? AND m.id = ?",
                               (mb, mid)).fetchone()
            try:
                frm = json.loads(row[0]) if row and row[0] and str(row[0]).startswith('[') else [row[0]] if row else []
            except ValueError:
                frm = []
            if frm and '#' in str(frm[0]):
                sb, sid = str(frm[0]).split('#', 1)
                r = S.db.execute("SELECT h.b_by FROM v_hold h JOIN being b ON b.n = h.being WHERE b.id = ? AND h.id = ?",
                                 (sb, sid)).fetchone()
                if r:
                    source[an] = r[0]
    import group as dmgroup
    L = dmgroup.Law(GARDEN)
    fitted = {}

    def suggests(text):
        if text not in fitted:
            r = L.fits(text)[0]
            fitted[text] = tuple(r.suggests) if r else ()
        return fitted[text]
    path_rows = [r for r in L.rows if r.reads == 'path']

    def path_suggests(path):
        return groupings.path_codes(path_rows, path.decode('utf-8', 'replace')) if path_rows else ()

    def chain_of(f):
        """[(folder n, its name)] from a folder up to its volume."""
        out = []
        while f in P:
            out.append((f, formats.unescape(P[f][1])))
            f = P[f][0]
        return out

    def day_of(folders, name):
        m = DAY.search(name.decode('utf-8', 'replace'))
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        for _f, nm in folders:
            m = DAY.search(nm.decode('utf-8', 'replace'))
            if m:
                return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        return None
    held = collections.defaultdict(dict)               # path -> the BLAKE3 it holds there
    for f, nm, c, _a, b3 in members:
        held[(rel.get(f, b'') + b'/' if rel.get(f) else b'') + formats.unescape(nm)] = b3
    out = collections.defaultdict(lambda: {'in place': 0, 'to link': 0, 'out of place': 0, 'samples': []})
    expected_names = set()
    plan = []
    if box:                                            # a box's member is a content, read once: by its names but its blob
        by_content = collections.OrderedDict()
        for m in sorted(members, key=lambda m: (rel.get(m[0], b''), m[1])):
            if rel.get(m[0], b'') == BLOBS_DIR:
                by_content.setdefault(m[2], [])
                continue
            by_content.setdefault(m[2], []).append(m)
        blob_of = {m[2]: m for m in members if rel.get(m[0], b'') == BLOBS_DIR}
        members = [ms[0] if ms else blob_of[c] for c, ms in by_content.items()]
    for f, nm, c, act, b3 in members:
        name = formats.unescape(nm)
        actual = (rel.get(f, b'') + b'/' if rel.get(f) else b'') + name
        mine = chain_of(f)
        src = source.get(act)
        srcchain = chain_of(src) if src else []
        codes = set(W.said.get(S.id_of(c), [])) if c else set()
        for x, _nm in mine + srcchain:
            codes |= set(W.said.get(S.id_of(x), []))
        codes |= set(suggests(name.decode('utf-8', 'replace')))
        for chain in (mine, srcchain):                 # its path beneath its volume, and its source's (`reads: path`)
            if chain or chain is mine:
                codes |= set(path_suggests(b'/'.join([nm2 for _x, nm2 in reversed(chain)] + [name])))
        at, by = made.get(c, (None, None))
        day = str(at)[:10] if at else (day_of(mine, name) or day_of(srcchain, b''))
        found = b'/'.join(nm2 for _x, nm2 in reversed(srcchain)) if srcchain else None
        facts = {'day': day, 'maker': by or 'unknown', 'found': found, 'name': name, 'blake3': b3}
        hits = storage.belongs(nodes, codes, box)
        if not hits:
            g = out['(no node)']
            g['out of place'] += 1
            if len(g['samples']) < sample:
                g['samples'].append(actual.decode('utf-8', 'replace'))
            continue
        for code, lay, row in hits:
            want = [x for x in str(row.get('matches') or '').split()]
            within = None
            for i, (x, _nm) in enumerate(srcchain or mine):
                if set(W.said.get(S.id_of(x), [])) & set(want):
                    within = b'/'.join(nm2 for _y, nm2 in reversed((srcchain or mine)[:i + 1]))
                    break
            p = lay.path(dict(facts, within=within))
            g = out[code]
            if p is None:
                g['out of place'] += 1
                if len(g['samples']) < sample:
                    g['samples'].append(f"{actual.decode('utf-8', 'replace')} (a fact its template needs is missing)")
                continue
            expected_names.add(p)
            if held.get(p) == b3:
                g['in place'] += 1
            elif box:
                g['to link'] += 1
                plan.append((p, b3, actual))
            else:
                g['out of place'] += 1
                if len(g['samples']) < sample:
                    g['samples'].append(f"{actual.decode('utf-8', 'replace')} -> {p.decode('utf-8', 'replace')}")
    stray = [p for p in held if p not in expected_names]
    out['(names no node gives)'] = {'in place': 0, 'to link': 0, 'out of place': len(stray),
                                    'samples': [p.decode('utf-8', 'replace') for p in stray[:sample]]}
    return schema, box, dict(out), plan


def shown(t):
    return time.strftime('%Y-%m-%d %H:%M', time.gmtime(t)) + 'Z'


def main(argv):
    ap = argparse.ArgumentParser(prog='storage.py', description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    for name in ('keepings', 'datasets', 'events', 'manifest', 'layout'):
        x = sub.add_parser(name)
        x.add_argument('--store')
        x.add_argument('--json', action='store_true')
        if name == 'keepings':
            x.add_argument('--scheme')
            x.add_argument('--of')
            x.add_argument('--now')
        elif name == 'datasets':
            x.add_argument('--of')
            x.add_argument('--same', action='store_true', help='only the datasets more than one folder holds')
        elif name == 'events':
            x.add_argument('--of', required=True)
            x.add_argument('--gap', required=True)
        elif name == 'layout':
            x.add_argument('--of', required=True)
            x.add_argument('--scheme', required=True)
            x.add_argument('--schema')
            x.add_argument('--plan', help='write the plan of a box (path, blob, from) as JSON lines to this file')
        else:
            x.add_argument('folder')
    a = ap.parse_args(argv)
    S = Store(store_path(a.store, GARDEN))
    t0 = time.time()
    if a.cmd == 'keepings':
        W = Words(GARDEN)
        groups, judged = keepings(S, W, a.scheme, a.of, secs(a.now) if a.now else None, each=[] if a.of else None)
        if a.json:
            print(json.dumps({'groups': [{'code': c, 'line': ln, 'contents': n, 'bytes': b}
                                         for (c, ln), (n, b) in sorted(groups.items())], 'contents': judged},
                             ensure_ascii=False, indent=1))
            return 0
        for (code, line), (n, b) in sorted(groups.items(), key=lambda x: -x[1][1]):
            print(f"{code} · {n:,} contents · {b / 1e9:,.2f} GB · {line}")
        for j in judged[:50]:
            print(f"  {j['content']}  {j['code'] or 'no policy'} · {j['line']}")
    elif a.cmd == 'datasets':
        T, fs = trees(S, a.of)
        by = collections.defaultdict(list)
        for f in fs:
            fp = T.fingerprint(f)
            if fp:
                by[fp].append(f)
        rows = []
        for fp, members in by.items():
            if a.same and len(members) < 2:
                continue
            man = T.manifest(members[0])
            rows.append({'dataset': formats.blake3_hex(man), 'folders': [S.id_of(x) for x in members],
                         'volumes': sorted({S.id_of(S.volume_of(x)) for x in members}), 'files': man.count(b'\n')})
        rows.sort(key=lambda r: (-len(r['folders']), -r['files']))
        if a.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for r in rows[:200]:
                print(f"{r['dataset'][:16]}… · {len(r['folders'])} folder(s) on {', '.join(r['volumes'])} · {r['files']:,} files")
    elif a.cmd == 'events':
        evs, none = events(S, a.of, duration(a.gap))
        if a.json:
            print(json.dumps({'events': [{'first': shown(f), 'last': shown(l), 'count': len(g),
                                          'by': collections.Counter(str(b) for _c, b in g).most_common()}
                                         for f, l, g in evs], 'no moment': len(none)}, ensure_ascii=False, indent=1))
        else:
            for f, l, g in evs:
                each = ', '.join(f"{b or 'no maker said'} {n:,}" for b, n in collections.Counter(b for _c, b in g).most_common(4))
                print(f"{shown(f)}–{shown(l)} · {len(g):,} · {each}")
            print(f"{len(evs):,} events; {len(none):,} contents with no moment, in none")
    elif a.cmd == 'layout':
        W = Words(GARDEN)
        schema, box, res, plan = layout(S, W, a.scheme, a.of, a.schema)
        if a.plan:
            with open(a.plan, 'w', encoding='utf-8') as fh:
                for p, b3, frm in plan:
                    fh.write(json.dumps({'path': formats.escape(p), 'blob': b3, 'from': formats.escape(frm)}) + '\n')
        if a.json:
            print(json.dumps({'schema': schema, 'box': box, 'nodes': res, 'to link': len(plan)}, ensure_ascii=False,
                             indent=1))
        else:
            print(f"{a.of}: the schema {a.scheme}:{schema}{' (a box)' if box else ''}")
            for node, g in res.items():
                print(f"  {node:24} in place {g['in place']:>8,}  to link {g['to link']:>8,}  out of place "
                      f"{g['out of place']:>8,}")
                for s_ in g['samples'][:4]:
                    print(f"      {s_}")
    else:
        T, _fs = trees(S, a.folder)
        man = T.manifest(S.n_of(a.folder))
        if man is None:
            raise SystemExit("storage: a file beneath it holds a content nobody read, or it holds none: no manifest")
        sys.stdout.buffer.write(man)
    print(f"({time.time() - t0:.1f} s)", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
