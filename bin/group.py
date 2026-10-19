#!/usr/bin/env python3
"""group — groupings over a garden and the stores its host keeps (core 2.15; MODEL.md, Groupings): the engine of
core/groupings.py at the scale of a store, offline, the same answer every time.

    python3 bin/group.py match <name> ...                       the pattern row each name fits, and what its slots hold
    python3 bin/group.py line <name> ... | --stdin              the lines of any list of names (the grouping `names`)
    python3 bin/group.py of <being> [--store <store>]           a folder's runs of names; a being's codes, and whence
    python3 bin/group.py mine [--store <store>] [--top N] [--min K] [--json]
                                                                the templates the largest folders' names make, ranked
    python3 bin/group.py root <being> --scheme <scheme> [--store <store>] [--json]
                                                                what a code said of a root holds beneath it, and what
                                                                is set apart, with why (the grouping `root`)
    python3 bin/group.py measure [--store <store>]              the whole store fitted, with its timings

(`python` on Windows.) The patterns are the garden's own schemes of the form `pattern`, read first, then the release's
(`name-patterns`); the classes the schemes of the form `class`; a code said of a being is a `classify` in its bean. A
store is read in one snapshot (bin/store.py: WAL, a long read holds up no writer) and never written. IT WRITES NOTHING:
a pattern the operator accepts is a row of the garden's extract, written by hand or by the helper and saved with its
journal entry (bin/save.py), never by this tool."""
import argparse
import collections
import json
import os
import sqlite3
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path[:0] = [ROOT, HERE]
import parse as dmparse  # noqa: E402,F401 — UTF-8 on stdout and stderr
from core import formats, groupings, read as core_read  # noqa: E402

SIZE = "CAST(json_extract(CAST(m.q_value AS TEXT), '$.count') AS INTEGER)"


def text(name):
    """A name the store keeps `escaped`, as the text a person reads: its bytes, a byte no UTF-8 holds shown as one."""
    return formats.unescape(name).decode('utf-8', 'replace') if '%' in name else name


class Law:
    """What the engine reads of the law and the garden: the slots, the systems of time reckoned by rule, the groupings,
    the clock epochs, and the pattern and class schemes — the garden's own first."""

    def __init__(self, root=ROOT):
        law_dir = os.path.join(root, 'core', 'law')
        law_dir = law_dir if os.path.isfile(os.path.join(law_dir, 'lines.yaml')) else os.path.join(ROOT, 'core', 'law')
        lines = core_read.data(os.path.join(law_dir, 'lines.yaml')) or {}
        systems = core_read.data(os.path.join(law_dir, 'systems.yaml')) or {}
        formats = core_read.data(os.path.join(law_dir, 'formats.yaml')) or {}
        registries = core_read.data(os.path.join(law_dir, 'registries.yaml')) or {}
        self.slots = {str(r['slot']): r for r in lines.get('slots') or [] if isinstance(r, dict)}
        self.groupings = {str(r['grouping']): r for r in lines.get('groupings') or [] if isinstance(r, dict)}
        self.systems = {str(r['system']): r for r in systems.get('systems') or []
                        if isinstance(r, dict) and r.get('dimension') == 'time' and r.get('reckoning') == 'arithmetic'}
        self.epochs = [r for r in formats.get('clock_epochs') or [] if isinstance(r, dict)]
        import knowledge as dmknowledge
        self.K = dmknowledge.Knowledge(root)
        released = {str(r.get('scheme')) for r in registries.get('knowledge_schemes') or [] if isinstance(r, dict)}
        mine, theirs, classes = [], [], {}
        for name, row in sorted(self.K.schemes.items()):
            form = row.get('form') if isinstance(row, dict) else None
            try:
                if form == 'pattern':
                    (theirs if name in released else mine).append((name, self.K.rows(name)))
                elif form == 'class':
                    classes[name] = {str(r.get('code')): r for r in self.K.rows(name)}
            except (KeyError, OSError):
                continue
        self.schemes, self.classes = mine + theirs, classes
        self.rows = groupings.rows_of(self.schemes, self.slots, self.systems)
        self.apart = {f"{s}:{c}" for s, rows in classes.items() for c, r in rows.items()
                      if str(r.get('apart') or '') == 'true'}

    def fits(self, text, reads='as', within=()):
        """The first row a text fits, and what its slots hold: (row, values) or (None, None). A row that applies only
        `within` a whole of a code is tried where one of `within` (the codes the text's wholes hold) is it or a code
        above it; a row that applies only `beside` siblings is not tried here."""
        for r in self.rows:
            if (r.reads or 'as') != reads or r.beside or (r.within and r.within not in within):
                continue
            got = r.template.match(text)
            if got is not None:
                return r, got
        return None, None


class Catalogue:
    """A store read as a filesystem's being: its folders and their names and parents, the holdings each folder holds,
    each content's size and what made it — in one snapshot, never written."""

    def __init__(self, path):
        self.path = path
        self.db = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=30)
        self.db.execute('PRAGMA cache_size = -800000')
        self.db.execute('BEGIN')                               # one snapshot for every read that follows
        self._tree = None

    def n_of(self, bid):
        r = self.db.execute('SELECT n FROM being WHERE id = ?', (bid,)).fetchone()
        return r[0] if r else None

    def id_of(self, n):
        r = self.db.execute('SELECT id FROM being WHERE n = ?', (n,)).fetchone()
        return r[0] if r else None

    def tree(self):
        """({folder n: name}, {folder n: parent n}, {parent n: [children]}) of every folder, read once."""
        if self._tree is None:
            name, parent, kids = {}, {}, collections.defaultdict(list)
            for of, by, nm in self.db.execute("SELECT b_of, b_by, t_as FROM v_name WHERE t_by IS NULL AND b_by IS NOT NULL"):
                name[of], parent[of] = text(nm), by
                kids[by].append(of)
            self._tree = (name, parent, kids)
        return self._tree

    def holdings(self, folders):
        """{folder n: [(name, content n, size)]} of the folders given, read in one query through a temporary table."""
        self.db.execute('CREATE TEMP TABLE IF NOT EXISTS gf (n INTEGER PRIMARY KEY)')
        self.db.execute('DELETE FROM temp.gf')
        self.db.executemany('INSERT OR IGNORE INTO temp.gf VALUES (?)', ((n,) for n in folders))
        out = collections.defaultdict(list)
        for by, nm, of, sz in self.db.execute(
                f"SELECT h.b_by, h.t_as, h.b_of, coalesce({SIZE}, 0) FROM temp.gf JOIN v_hold h ON h.b_by = temp.gf.n "
                f"LEFT JOIN v_measure m ON m.b_of = h.b_of WHERE h.t_as IS NOT NULL"):
            out[by].append((text(nm), of, sz or 0))
        return out

    def made(self, contents):
        """{content n: (moment, maker n)} of the contents given that a `produce` says were made."""
        if 'v_produce' not in {r[0] for r in self.db.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}:
            return {}
        self.db.execute('CREATE TEMP TABLE IF NOT EXISTS gc (n INTEGER PRIMARY KEY)')
        self.db.execute('DELETE FROM temp.gc')
        self.db.executemany('INSERT OR IGNORE INTO temp.gc VALUES (?)', ((n,) for n in contents))
        return {of: (at, by) for of, at, by in self.db.execute(
            "SELECT p.b_of, p.t_at, p.b_by FROM temp.gc JOIN v_produce p ON p.b_of = temp.gc.n")}


def store_path(name, root=ROOT):
    import store as dmstore
    kept = dmstore.kept_here(root)
    if name not in kept:
        raise SystemExit(f"group: the store {name!r} is not kept on this host: {', '.join(sorted(kept)) or 'none'}")
    st = dmstore.open_store(name, root=root, create=False)
    path = st.path
    st.close()
    return path


# ------------------------------------------------------------------------------------------------ the commands
def cmd_match(L, names):
    for n in names:
        r, got = L.fits(n)
        print(f"{n}\t{r.coding + ' ' + r.template.text + ' ' + json.dumps(got, ensure_ascii=False) if r else '(none)'}")
    return 0


def cmd_line(L, names, fields=None):
    items = [(n, n, None) for n in names if n.strip()]
    fields = fields or L.groupings['names']['line']
    for g in sorted(groupings.fit(items, L.rows, L.systems), key=lambda g: -len(g['members'])):
        print(groupings.line(g, fields))
    return 0


def said_codes(root=ROOT):
    """{being: [code]} of every `classify` a bean of the garden says — a folder or a content of a store gains a bean
    under its own id when a person first speaks of it (MODEL.md, The store)."""
    import reckon as dmreckon
    g = dmreckon.Garden(root)
    out = collections.defaultdict(list)
    for b, fm in g.fm.items():
        if g.kind.get(b) != 'beans':
            continue
        for x, _w in dmreckon._flatten(dmreckon.walk(g, fm, 'classify', at=b)):
            if isinstance(x, dict) and x.get('as'):
                who = dmreckon._own(x.get('of'), b)
                if isinstance(x.get('of'), str) and x['of'].startswith('store:'):
                    who = x['of'].split(':')[2].split('#')[0]
                out[who].append(str(x['as']))
    return out


class Writers:
    """How a line's fields that read the store are written: the days its members' contents were made on, and the
    maker they agree on."""

    def __init__(self, C, made, titles=None):
        self.C, self.made, self.titles = C, made, titles or {}

    def cells(self, group, path):
        days = sorted({str(self.made[c][0])[:10] for c in group.get('contents') or [] if c in self.made
                       and self.made[c][0]})
        if not days:
            return None
        return days[0] if len(days) == 1 else f"{days[0]}–{days[-1]} ({len(days)} days)"

    def agree(self, group, path):
        makers = {self.made[c][1] for c in group.get('contents') or [] if c in self.made}
        if len(makers) != 1:
            return None
        m = next(iter(makers))
        bid = self.C.id_of(m) if isinstance(m, int) else m
        return self.titles.get(bid, bid) if bid and bid != 'unknown' else None

    def table(self):
        return {'cells': self.cells, 'agree': self.agree}


def runs_of(L, C, folder, hold=None):
    """The groups of one folder's files, each with its contents: `fit` within the folder, the registry first."""
    hold = hold if hold is not None else C.holdings([folder])
    rows = hold.get(folder) or []
    gs = groupings.fit([(i, nm, folder) for i, (nm, _of, _sz) in enumerate(rows)], L.rows, L.systems)
    for g in gs:
        g['contents'] = [rows[i][1] for i in g['members']]
        g['bytes'] = sum(rows[i][2] for i in g['members'])
    return gs


def cmd_of(L, C, bid):
    """A folder's runs of names, each in its line; a content's places, and the run it is one of in each."""
    n = C.n_of(bid)
    if n is None:
        raise SystemExit(f"group: no being {bid!r} in this store")
    kind = C.db.execute('SELECT kind FROM being WHERE n = ?', (n,)).fetchone()[0]
    fields = L.groupings['name-series']['line']
    if kind in ('folder', 'volume'):
        gs = runs_of(L, C, n)
        W = Writers(C, C.made({c for g in gs for c in g['contents'] if c}))
        print(f"{bid} ({kind}): {sum(len(g['members']) for g in gs):,} files in {len(gs):,} groups")
        for g in sorted(gs, key=lambda g: -len(g['members'])):
            print(f"  {groupings.line(g, fields, W.table())}" + (f"   [{g['code']}]" if g['code'] else ''))
        return 0
    rows = C.db.execute("SELECT h.b_by, h.t_as FROM v_hold h WHERE h.b_of = ? AND h.t_as IS NOT NULL", (n,)).fetchall()
    print(f"{bid} ({kind}): held under {len(rows):,} names")
    name, parent, _kids = C.tree()
    for by, nm in rows[:20]:
        gs = runs_of(L, C, by)
        mine = next((g for g in gs if text(nm) in g['texts']), None)
        W = Writers(C, C.made({c for c in (mine or {}).get('contents') or [] if c}))
        path, f = [], by
        while f in name:
            path.append(name[f])
            f = parent[f]
        print(f"  {'/'.join(reversed(path))}/{text(nm)}" + (f"\n    in {groupings.line(mine, fields, W.table())}" if mine else ''))
    return 0


def weigh(L, C, root_n, scheme, code=None):
    """What a code said of the folder `root_n` holds beneath it (the grouping `root`): every content of the subtree
    held by it, and what is set apart, with why — a folder or a file whose name fits a pattern suggesting an `apart`
    code, a folder a nearer code is said of, or a file that does not fit the root by two of kind, day and shape (the
    grouping's `weighs`)."""
    import bisect
    import datetime
    import knowledge as dmknowledge
    name, parent, kids = C.tree()
    sub, stack = [], [root_n]
    while stack:
        f = stack.pop()
        sub.append(f)
        stack.extend(kids.get(f, ()))
    hold = C.holdings(sub)
    try:
        media = groupings.Media(dmknowledge.Knowledge(ROOT).rows('media-types'))
    except KeyError:
        media = groupings.Media([])
    w = (L.groupings.get('root') or {}).get('weighs') or {}
    kind_w = w.get('kind') or {}
    share_b, share_f = float(kind_w.get('bytes') or 0.02), float(kind_w.get('files') or 0.05)
    largest = int(kind_w.get('largest') or 2)
    need = int(w.get('of') or 2)
    fam_b, fam_f = collections.Counter(), collections.Counter()
    total_b = total_f = 0
    for f in sub:
        for nm, of, sz in hold.get(f) or []:
            fam = media.of(nm)[1]
            fam_b[fam] += sz
            fam_f[fam] += 1
            total_b += sz
            total_f += 1
    top = {x for x, _ in fam_b.most_common(largest)}
    made = C.made({of for f in sub for _nm, of, _sz in hold.get(f) or [] if of})
    ords = sorted({datetime.date.fromisoformat(str(at)[:10]).toordinal() for at, _by in made.values()
                   if at and len(str(at)) >= 10 and str(at)[4] == '-'})
    said = said_codes()
    rid = C.id_of(root_n)
    if code:
        said = dict(said)
        said[rid] = [code]

    def fits_kind(nm):
        fam = media.of(nm)[1]
        return fam in top or fam_b[fam] >= share_b * max(total_b, 1) or fam_f[fam] >= share_f * max(total_f, 1)

    def fits_day(of):
        at = made.get(of, (None, None))[0]
        if not at or not ords:
            return True
        try:
            d = datetime.date.fromisoformat(str(at)[:10]).toordinal()
        except ValueError:
            return True
        i = bisect.bisect_left(ords, d)
        return min(abs(d - ords[j]) for j in (i - 1, i) if 0 <= j < len(ords)) <= 365

    out = {'root': rid, 'code': (said.get(rid) or [None])[0], 'files': total_f, 'bytes': total_b,
           'families': fam_b.most_common(5), 'members': 0, 'held': 0, 'apart': collections.defaultdict(list),
           'apart_files': 0, 'apart_bytes': 0}
    order = {root_n: 0}
    for f in sub:
        for k in kids.get(f, ()):
            order[k] = order.get(f, 0) + 1
    tally = {}                                         # each folder's files and bytes at any depth, bottom up
    for f in sorted(sub, key=lambda x: -order.get(x, 0)):
        nf = len(hold.get(f) or [])
        nb = sum(sz for _nm, _of, sz in hold.get(f) or [])
        for k in kids.get(f, ()):
            nf, nb = nf + tally.get(k, (0, 0))[0], nb + tally.get(k, (0, 0))[1]
        tally[f] = (nf, nb)
    # A TREE OF CODE is marked by a file a build or a package manager keeps (a row that `marks` the folder holding
    # it); beneath one, the rows that apply only `within` a code tree are tried (a `bin`, a `debug`)
    marked = set()
    for f in sub:
        for nm, _of, _sz in hold.get(f) or []:
            for r in L.rows:
                if r.marks == 'by' and r.template.match(nm) is not None:
                    marked.update({f} if any(c.endswith(':code-tree') for c in r.suggests) else set())
                    break
            if f in marked:
                break
    in_code = {}
    for f in sorted(sub, key=lambda x: order.get(x, 0)):
        in_code[f] = f in marked or in_code.get(parent.get(f), False)
    code_codes = {c for r in L.rows if r.marks == 'by' for c in r.suggests if c.endswith(':code-tree')}
    kept_apart = set()

    def put_apart(why, f):
        kept_apart.add(f)
        nf, nb = tally.get(f, (0, 0))
        out['apart'][why].append((name.get(f, '?'), nb, nf))
        out['apart_files'] += nf
        out['apart_bytes'] += nb
    for f in sorted(sub, key=lambda x: order.get(x, 0)):
        if parent.get(f) in kept_apart:
            kept_apart.add(f)
            continue
        if f != root_n:
            within = code_codes if in_code.get(parent.get(f)) else ()
            r, _got = L.fits(name.get(f, ''), reads='name.as', within=within)
            if r and any(c in L.apart for c in r.suggests):
                put_apart(f"folder {r.coding} → {', '.join(r.suggests)}", f)
                continue
            own = [c for c in said.get(C.id_of(f)) or [] if c.split(':', 1)[0] == scheme]
            if own:
                put_apart(f"said nearer: {', '.join(own)}", f)
                continue
        rows = hold.get(f) or []
        shapes = collections.Counter(groupings.shape(nm)[0] for nm, _of, _sz in rows)
        most = shapes.most_common(1)[0] if shapes else (None, 0)
        for nm, of, sz in rows:
            r, _got = L.fits(nm)
            if r and any(c in L.apart for c in r.suggests):
                out['apart'][f"{r.coding} → {', '.join(r.suggests)}"].append((nm, sz, 1))
                out['apart_files'] += 1
                out['apart_bytes'] += sz
                continue
            misfit = []
            if not fits_kind(nm):
                misfit.append('kind')
            if not fits_day(of):
                misfit.append('day')
            if len(rows) >= 10 and most[1] >= 0.8 * len(rows) and groupings.shape(nm)[0] != most[0]:
                misfit.append('shape')
            if len(misfit) >= need:
                out['apart'][f"not fitting by {' and '.join(misfit)} ({media.of(nm)[1]})"].append((nm, sz, 1))
                out['apart_files'] += 1
                out['apart_bytes'] += sz
                continue
            out['members'] += 1
            out['held'] += sz
    return out


def cmd_root(L, C, bid, scheme, code, as_json):
    n = C.n_of(bid)
    if n is None:
        raise SystemExit(f"group: no being {bid!r} in this store")
    t0 = time.time()
    got = weigh(L, C, n, scheme, code)
    secs = time.time() - t0
    if as_json:
        print(json.dumps(dict(got, apart=dict(got['apart']), seconds=round(secs, 1)), ensure_ascii=False, indent=1))
        return 0
    fams = ', '.join(f"{f.replace('-x-generic', '').replace('x-office-', '')} {100 * b / max(got['bytes'], 1):.0f}%"
                     for f, b in got['families'][:3])
    print(f"{got['code'] or '(no code said: --code reads one as said)'} · {got['members']:,} · "
          f"{got['held'] / 1e9:.2f} GB · {fams} · {got['apart_files']:,} set apart ({got['apart_bytes'] / 1e9:.2f} GB)"
          f"   ({bid}, {secs:.1f} s)")
    for why, items in sorted(got['apart'].items(), key=lambda kv: -sum(x[2] for x in kv[1]))[:30]:
        names = sorted({x[0] for x in items})
        nf, nb = sum(x[2] for x in items), sum(x[1] for x in items)
        print(f"  {nf:>8,} files {nb / 1e9:7.2f} GB  {why}" + (f" — {len(items):,} folders" if why.startswith('folder')
              or why.startswith('said') else '') + f"   e.g. {', '.join(names[:3])}{' …' if len(names) > 3 else ''}")
    return 0


def cmd_mine(L, C, top, least, as_json):
    """Candidates from the largest folders: each folder's names fitted — the registry first — and the groups no row
    knows made templates, the same template met in several folders counted once a folder, ranked by names and then by
    folders ("follow the lead of big directories")."""
    t0 = time.time()
    sizes = collections.Counter(r[0] for r in C.db.execute("SELECT b_by FROM v_hold WHERE t_as IS NOT NULL"))
    biggest = [f for f, _n in sizes.most_common(top)]
    hold = C.holdings(biggest)
    cand, known = {}, collections.Counter()
    for f in biggest:
        for g in runs_of(L, C, f, hold):
            if g['code']:
                known[g['code']] += len(g['members'])
                continue
            if len(g['members']) < least or not g['slots']:
                continue
            c = cand.setdefault(g['template'], {'template': g['template'], 'names': 0, 'folders': 0, 'examples': []})
            c['names'] += len(g['members'])
            c['folders'] += 1
            if len(c['examples']) < 3:
                c['examples'].append(g['texts'][0])
    ranked = sorted(cand.values(), key=lambda c: (-c['names'], -c['folders'], c['template']))
    secs = time.time() - t0
    if as_json:
        print(json.dumps({'seconds': round(secs, 1), 'folders': len(biggest), 'known': dict(known), 'candidates': ranked},
                         ensure_ascii=False, indent=1))
        return 0
    print(f"mine: the {len(biggest):,} largest folders, {sum(sizes[f] for f in biggest):,} names, {secs:.1f} s; "
          f"{sum(known.values()):,} names fit a row the registry holds")
    for c in ranked[:60]:
        print(f"{c['names']:>9,} names {c['folders']:>6,} folders  {c['template']}   e.g. {', '.join(c['examples'])}")
    return 0


def _measure_part(args):
    """One worker's part of `measure`: the folders whose numbers fall in [lo, hi), fitted."""
    path, lo, hi = args
    L = Law(ROOT)
    db = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=30)
    t_fit = 0.0
    folders = names = groups = known = 0
    items = []
    cur = None

    def flush():
        nonlocal t_fit, groups, known, folders
        a = time.time()
        gs = groupings.fit(items, L.rows, L.systems)
        t_fit += time.time() - a
        groups += len(gs)
        known += sum(len(g['members']) for g in gs if g['code'])
        folders += 1
    for by, nm in db.execute("SELECT b_by, t_as FROM v_hold WHERE t_as IS NOT NULL AND b_by >= ? AND b_by < ? "
                             "ORDER BY b_by", (lo, hi)):
        if by != cur and items:
            flush()
            items = []
        cur = by
        items.append((names, text(nm), by))
        names += 1
    if items:
        flush()
    return names, folders, groups, known, t_fit


def cmd_measure(L, C, jobs):
    """The whole store fitted: every folder's files by the registry and their shape, spread over `jobs` processes by
    ranges of folders, with the time each took."""
    import concurrent.futures
    t0 = time.time()
    lo, hi = C.db.execute("SELECT min(b_by), max(b_by) FROM v_hold").fetchone()
    step = (hi - lo) // (jobs * 8) + 1
    parts = [(C.path, a, min(a + step, hi + 1)) for a in range(lo, hi + 1, step)]
    tot = [0, 0, 0, 0, 0.0]
    with concurrent.futures.ProcessPoolExecutor(max_workers=jobs) as ex:
        for got in ex.map(_measure_part, parts):
            tot = [x + y for x, y in zip(tot, got)]
    names, folders, groups, known, t_fit = tot
    print(f"measure: {names:,} names in {folders:,} folders, {groups:,} groups ({known:,} names fit a row) — "
          f"{time.time() - t0:.1f} s on {jobs} processes ({t_fit:.0f} s of fitting in all)")
    return 0


def main(argv):
    ap = argparse.ArgumentParser(prog='group', description=__doc__.split('\n')[0])
    ap.add_argument('command', choices=['match', 'line', 'of', 'mine', 'root', 'measure'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--store', default=None)
    ap.add_argument('--path', default=None, help='a store file named directly, as a test does')
    ap.add_argument('--scheme', default=None)
    ap.add_argument('--top', type=int, default=2000)
    ap.add_argument('--min', type=int, default=3)
    ap.add_argument('--stdin', action='store_true')
    ap.add_argument('--json', action='store_true')
    ap.add_argument('--code', default=None, help="root: read this code as said of the root, as a person would say it")
    ap.add_argument('-j', '--jobs', type=int, default=8)
    a = ap.parse_args(argv)
    L = Law(ROOT)
    if a.command == 'match':
        return cmd_match(L, a.args)
    if a.command == 'line':
        names = [ln.rstrip('\n') for ln in sys.stdin] if a.stdin or a.args == ['-'] else a.args
        return cmd_line(L, names)
    path = a.path or (store_path(a.store) if a.store else None)
    if path is None:
        raise SystemExit("group: name a store (--store <name>) or its file (--path <file>)")
    C = Catalogue(path)
    if a.command == 'mine':
        return cmd_mine(L, C, a.top, a.min, a.json)
    if a.command == 'measure':
        return cmd_measure(L, C, a.jobs)
    if a.command == 'of':
        return cmd_of(L, C, a.args[0])
    if a.command == 'root':
        if not (a.scheme or a.code):
            raise SystemExit("group: root names the class scheme it reads (--scheme), or a code to read as said (--code)")
        return cmd_root(L, C, a.args[0], a.scheme or a.code.split(':', 1)[0], a.code, a.json)
    raise SystemExit(f"group: `{a.command}` is not built")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
