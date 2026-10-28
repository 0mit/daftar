#!/usr/bin/env python3
"""store_rows — a store at size judged as its rows were put (the next version's nv-s6-open items 2, 3, 4 and 7): every
row of a large store as its put judges one, a name's form at its put, the knowing acts the rows name, one snapshot of
every store a check reads, and an import that reads a being's rows once.

  rows      every case of test/core-cases.yaml of a rule a statement breaks alone — its form, its valency, its frame, a
            name's form — its bean kept as a store's rows unjudged (as a load that judges a sample keeps them), and kept
            half in git and half in the store: the check of the union as a large one names exactly the rows the put
            refuses, each at its place in the union, in the put's words (`row_findings`), and the case's own rule among
            them wherever the put refuses its row
  put       a name not in its namespace's form, and one holding a bidi control, are refused at their put in the words of
            the rule `names`; a load that keeps them unjudged leaves them to the check, which names them
  knowing   an act no row names any more — every row it knew taken out — is said nothing of; an act a row names that is
            kept nowhere still is
  snapshot  the check reads every store through one connection, in one transaction: a writer's commit after it began
            is seen by none of its reads — its queries, its union's SQL, and the engine's reading of the rows alike
  import    an import into a store that keeps a being's rows already reads them once an import, never again at each
            record (a series' millions of observations each read again at every one), and still fills what an earlier
            import left `unknown`

Invented beings; nothing here is a fact.

Run: python3 test/store_rows.py   (0 = green)
"""
import os
import shutil
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
from core import engine, read  # noqa: E402
from core.law import Law  # noqa: E402
import store  # noqa: E402

FAILS = []
RLO_NAME = 'AB12' + chr(0x202E) + 'CD'       # a name holding a bidi control, written as an escape
CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
ZONE = CASES['zone']
ACT = 'scan-0#s0'
ALONE = ('form', 'valency', 'frame', 'names')       # the rules a statement can break alone


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-2500:]))
    if not cond:
        FAILS.append(name)


def bean(bid, kind, statements, header=None):
    h = {'bean': bid, 'kind': kind, 'title': bid, 'statements': statements}
    h.update(header or {})
    return engine.Bean(bid, header=h)


def garden(beans):
    return engine.Garden(dict(beans), ZONE, files=['VOCAB.md', 'GARDEN.md', 'log/journal.md'],
                         manifest={'gardener': 'sam'})


def kept(path, git, rows, beings):
    """A store at `path`: `beings` declared, then each of `rows` [(being, verb, roles)] put unjudged, known by one act.
    A row it cannot keep at all (a key that is no column of its verb) stays out."""
    for x in (path, path + '-wal', path + '-shm'):
        if os.path.exists(x):
            os.remove(x)
    s = store.Store(path, law=LAW, garden=git)
    s.put('scan-0', 'say', {'id': 's0', 'by': 'sam', 'at': '2026-10-01T09:00:00+03:30'}, judge=False)
    s.beings([(b, k, b) for b, k in beings])
    out = []
    for b, verb, roles in rows:
        try:
            s.put(b, verb, roles, act=ACT, judge=False)
            out.append((b, verb, roles))
        except store.StoreError:
            pass
    return s, out


def keepable(verb, roles):
    row = LAW.verbs.get(verb)
    return row is not None and 'held' not in roles and all(
        k in (row.get('roles') or {}) or k in (row.get('qualifiers') or {}) or k in ('id', 'while', 'why', 'note')
        for k in roles) and (roles.get('id') is None or (isinstance(roles['id'], str) and engine.ID.match(roles['id'])))


def large(stores, git):
    """The check of the union, read as a large one, beyond git's own findings."""
    own = {tuple(f) for f in engine.Judge(LAW, git).run()}
    keep = store.UNION_ROWS
    store.UNION_ROWS = -1
    try:
        return store._check(stores, git, LAW, own)
    finally:
        store.UNION_ROWS = keep


def put_says(s, U, k):
    """What the put says of each row of store `s` (the union's keeping `k`), told at the row's place in the union."""
    out = []
    for verb in s.verbs():
        for (n, sid, being) in s.db.execute(f"SELECT t.n, t.id, b.id FROM {store._q('v_' + store._col(verb))} t JOIN "
                                            f"being b ON b.n = t.being ORDER BY t.n").fetchall():
            if (verb, n) in U.K[k].skip:
                continue
            _v, r = s.statement(being, sid)
            i = U.index(k + 1, being, verb, n)
            out += s.row_findings(being, verb, r, i=i, place=f"{being}[{i}] {verb}")
    return out


T = tempfile.mkdtemp(prefix='store-rows-')
try:
    # ---- rows: every case a statement breaks alone, kept in a store unjudged
    base = {bid: bean(bid, b['kind'], b['statements']) for bid, b in CASES['garden'].items()}
    differ, judged, caught, missed, said = [], 0, 0, [], 0
    for c in [c for c in CASES['bad'] if c['rule'] in ALONE]:
        for way in ('store', 'split'):
            beans = dict(base)
            stmts = [st for st in c['statements'] if isinstance(st, dict) and len(st) == 1
                     and isinstance(next(iter(st.values())), dict)]
            rows = [(c['bean'], v, dict(r)) for j, st in enumerate(stmts) for v, r in st.items()
                    if keepable(v, r) and (way == 'store' or j % 2)]
            rest = [st for j, st in enumerate(c['statements']) if not (
                isinstance(st, dict) and len(st) == 1 and isinstance(next(iter(st.values())), dict)
                and keepable(*next(iter(st.items()))) and (way == 'store' or j % 2))]
            if rest or way == 'split':
                beans[c['bean']] = bean(c['bean'], c['kind'], rest, c.get('header'))
            else:
                beans.pop(c['bean'], None)
            git = garden(beans)
            s, rows = kept(os.path.join(T, f"rows-{way}.sqlite"), git, rows, [(c['bean'], c['kind'] or 'document')])
            if not rows:
                s.close()
                continue
            judged += 1
            with store.compiled([s], git, LAW) as U:
                want = put_says(s, U, 0)
                got = store._rows_judged(U, 0, s)
            said += len(want)
            whole = large([s], git)
            if sorted(set(got)) != sorted(set(want)) or not set(want) <= set(whole):
                differ.append((c['bean'], way, sorted(set(want) - set(got)), sorted(set(got) - set(want)),
                               sorted(set(want) - set(whole))))
            if any(f[0] == c['rule'] for f in want):
                caught += 1
                if not any(f[0] == c['rule'] for f in got):
                    missed.append((c['bean'], way))
            s.close()
    check(f"rows: every case of a rule a statement breaks alone, kept as a store's rows unjudged — the case's bean wholly "
          f"in the store, and half in git ({judged} unions): the check of the union as a large one names exactly what "
          f"the put says of each row, at its place in the union, in its words ({said} findings), and its whole check "
          f"says each", not differ and said, differ[:3])
    check(f"rows: ...and wherever the put refuses a case's row by the case's own rule ({caught}), so does the check",
          caught and not missed, missed[:5])
    git = garden(base)
    s, _rows = kept(os.path.join(T, 'line.sqlite'), git, [('d-7', 'part', {'by': 'self', 'of': 'd-8'})],
                    [('d-7', 'folder'), ('d-8', 'folder')])
    line = [m for r, _w, m in large([s], git) if r == 'size']
    check("rows: the size line says every row is judged as its put judges one, and names no rule as judged by sample",
          line and 'every row as its put judges one' in line[0] and 'sampled' not in line[0], line)
    s.close()

    # ---- put: a name's form at its put, and a load's names at the check
    L2 = Law.load(('VOCAB.md', dict(CASES['vocab'], namespaces=list(CASES['vocab']['namespaces']) + [
        {'namespace': 'serial', 'pattern': '^[A-Z0-9]{4,12}$', 'meaning': "an invented maker's serial"}])))
    git = garden(base)
    p = os.path.join(T, 'names.sqlite')
    s = store.Store(p, law=L2, garden=git)
    s.put('scan-0', 'say', {'id': 's0', 'by': 'sam', 'at': '2026-10-01T09:00:00+03:30'}, judge=False)
    s.beings([('c-1', 'part'), ('c-2', 'part'), ('c-3', 'part')])
    refused = {}
    for bid, name in (('c-1', 'AB12CD'), ('c-2', 'ab-12'), ('c-3', RLO_NAME)):
        try:
            s.put(bid, 'name', {'by': 'serial', 'of': bid, 'as': name}, act=ACT)
            refused[bid] = None
        except store.StoreError as e:
            refused[bid] = str(e)
    check("put: a name in its namespace's form is kept; one not in it, and one holding a bidi control, are refused in "
          "the words of the rule `names`", refused['c-1'] is None and refused['c-2'] and refused['c-2'].startswith('names ')
          and refused['c-3'] and 'bidi control' in refused['c-3'], refused)
    s.bulk('name', [('c-2', {'by': 'serial', 'of': 'c-2', 'as': 'ab-12'}), ('c-3', {'by': 'serial', 'of': 'c-3',
                                                                                   'as': RLO_NAME})],
           act=ACT, beings=('of',), judge_every=0)
    own = {tuple(f) for f in engine.Judge(L2, git).run()}
    keep = store.UNION_ROWS
    store.UNION_ROWS = -1
    try:
        found = [f for f in store._check([s], git, L2, own) if f[0] == 'names']
    finally:
        store.UNION_ROWS = keep
    check("put: ...and a load that kept them unjudged leaves them to the check of a large store, which names each at "
          "its place", sorted(w for _r, w, _m in found) == ['c-2[0] name', 'c-3[0] name'], found)
    s.close()

    # ---- knowing: an act no row names any more, and one kept nowhere
    git = garden(base)
    p = os.path.join(T, 'knowing.sqlite')
    s = store.Store(p, law=LAW, garden=git)
    s.put('scan-0', 'say', {'id': 's0', 'by': 'sam', 'at': '2026-10-01T09:00:00+03:30'}, judge=False)
    s.beings([('d-1', 'folder'), ('d-2', 'folder')])
    s.put('scan-1', 'make', {'id': 'm1', 'by': 'sam', 'at': '2026-10-02T09:00:00+03:30'}, judge=False)
    s.put('d-1', 'part', {'by': 'self', 'of': 'd-2'}, act='scan-1#m1')
    sid = s.get('d-1')[0][1]['id']
    s.gone('d-1', sid, by='sam', why='taken out')
    s.gone('scan-1', 'm1', by='sam', why='taken out')
    before = [f for f in store._acts_resolve([s])]
    s.put('d-2', 'part', {'by': 'self', 'of': 'd-1'}, act='scan-0#s0')
    s.db.execute("INSERT INTO act (ref) VALUES ('scan-9#nowhere')")
    n9 = s.db.execute("SELECT n FROM act WHERE ref = 'scan-9#nowhere'").fetchone()[0]
    s.db.execute("UPDATE v_part SET known = ? WHERE being = (SELECT n FROM being WHERE id = 'd-2')", (n9,))
    after = [m for _r, _w, m in store._acts_resolve([s])]
    check("knowing: an act every row of which was taken out, itself taken out too, is said nothing of; an act a row "
          "names, kept nowhere, still is", before == [] and after == ['rows are known by scan-9#nowhere, which is kept '
                                                                      'nowhere this host reads'], (before, after))
    s.close()

    # ---- snapshot: a commit after the check began is seen by none of its reads
    git = garden(base)
    p = os.path.join(T, 'snap.sqlite')
    s, _r = kept(p, git, [('d-7', 'part', {'by': 'self', 'of': 'd-8'})], [('d-7', 'folder'), ('d-8', 'folder')])
    w = store.Store(p, law=LAW, garden=git)
    seen = {}
    with store.one_snapshot([s]) as db:
        seen['count'] = s.count()
        w.put('d-8', 'part', {'by': 'self', 'of': 'd-9'}, act=ACT, judge=False)      # another writer commits
        seen['count after'] = s.count()
        seen['get'] = len(s.get('d-8'))
        seen['one connection'] = db is s.db
        with store.compiled([s], git, LAW) as U:
            seen['union'] = U.db is db
            seen['sql'] = U.db.execute(f"SELECT COUNT(*) FROM {U.K[0].schema}.v_part").fetchone()[0]
    seen['own, after'] = s.count()
    check("snapshot: the check reads its store through one connection, in one transaction begun before a writer "
          "committed: its queries, the engine's reading of a being and the union's SQL see the store as it was, and "
          "the store's own connection, after, the row written", seen == {'count': 2, 'count after': 2, 'get': 0,
                                                                         'one connection': True, 'union': True,
                                                                         'sql': 1, 'own, after': 3}, seen)
    w.close()
    s.close()

    # ---- import: a being's rows read once an import
    import importlib
    dmimport = importlib.import_module('import')
    imp = dmimport.Import.__new__(dmimport.Import)
    git = garden(base)
    p = os.path.join(T, 'import.sqlite')
    s = store.Store(p, law=LAW, garden=git)
    s.put('scan-0', 'say', {'id': 's0', 'by': 'sam', 'at': '2026-10-01T09:00:00+03:30'}, judge=False)
    s.beings([('d-1', 'folder'), ('d-2', 'folder')])
    s.put('d-1', 'part', {'id': 'p0', 'by': 'unknown', 'of': 'd-2'}, act=ACT, judge=False)
    for k in range(50):
        s.put('d-1', 'part', {'id': f'p{k + 1}', 'by': f'd-{k + 3}', 'of': 'd-2'}, act=ACT, judge=False)
    imp.store, imp._unk, imp.unknown_filled, imp._hid = s, {}, 0, 'sam'
    reads = []
    real_get = store.Store.get
    store.Store.get = lambda self, being: reads.append(being) or real_get(self, being)
    try:
        for k in range(20):
            imp._unknown_filled('d-1', 'part', {'by': f'd-{k + 3}', 'of': 'd-2'})
        imp._unknown_filled('d-1', 'part', {'by': 'nas', 'of': 'd-2'})
    finally:
        store.Store.get = real_get
    gone = s.db.execute("SELECT id, why FROM gone").fetchall()
    check("import: twenty-one records of a being whose rows a store keeps read none of them whole; the row an earlier "
          "import left `unknown` is filled, and taken out with its reason", reads == [] and imp.unknown_filled == 1
          and gone == [('p0', 'filled: by named since')], (reads, imp.unknown_filled, gone))
    s.close()
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nstore_rows: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
