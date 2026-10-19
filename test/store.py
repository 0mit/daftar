#!/usr/bin/env python3
"""The store: statements kept off git, as rows, on the host that keeps them, one universe with the beans (core 2.10).

Grows a garden of the core from a release made of this tree (test/grow.py), and keeps statements in stores beside it
with bin/store.py, each step run in the garden as a tool would run it:

  open      a store read only by its writer is kept in WAL; one another user reads, with a rollback journal and readable
  put       a row is judged as the gate judges a bean's statement: its verb's roles, the shapes and natures of its
            fillers, its act; named by its form when given no id, so the same statement twice is one row; another form
            under one id refused; text with a control character refused, a name in bytes written `escaped`; nothing a
            seal would take
  pointer   the gate: a bean names a being kept only in a store, `store:<kind>:<id>`, and one of its statements; a kind
            that is none, or not its bean's, refused
  check     the union of git and the stores: a pointer that resolves passes, one that does not is found; a name given
            once naming two beings across a bean and a store; a cycle through a bean's part and a store's; one id, two
            forms; an act kept nowhere — judged whole by the engine when small, and by queries when large
  between   the round trips: a row into a bean and back (one statement, two acts); a bean into a store and back
            (nothing new); a series' part into a store and back (the same bytes); an overlap read as one statement
  writers   eight processes writing at once: every row kept, none lost
  bulk      a tool's thousands at once, named and judged as one row is
  snapshot  a long read from a copy made in steps
  gone      a statement out of a store, its removal recorded; a form under its id is free again
  here      a store a host's bean declares (`details.stores`), found and opened by its name on that host

Run: python3 test/store.py   (0 = green; about a minute)
"""
import json
import os
import shutil
import socket
import stat
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable
B3 = '6437b3ac38465133ffb63b75273a8db548c558465d79db03fd359c6cd5bd9d85'     # BLAKE3("abc")


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def doc(bid, kind, *statements, details=''):
    return (f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{bid}\"\nstatements:\n" + ''.join(f"  - {s}\n" for s in statements)
            + details + f"---\n{bid}, invented.\n")


def write(rel, text):
    os.makedirs(os.path.dirname(os.path.join(G, rel)), exist_ok=True)
    with open(os.path.join(G, rel), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


# THE PROGRAM run in the garden: each step's answer one JSON line
PROGRAM = r'''
import json, os, sys, subprocess
sys.path.insert(0, 'bin'); sys.path.insert(0, '.')
import store
from store import Store, StoreError
def say(**k):
    print(json.dumps(k, default=str), flush=True)
def refused(f):
    try:
        f()
    except StoreError as e:
        return str(e)
    return None
step, path = sys.argv[1], sys.argv[2]
B3 = '6437b3ac38465133ffb63b75273a8db548c558465d79db03fd359c6cd5bd9d85'
if step == 'open':
    a = Store(path + '/solo.sqlite')
    b = Store(path + '/shared.sqlite', readers=['sam', 'some-other-user'])
    say(solo=a.db.execute('PRAGMA journal_mode').fetchone()[0], shared=b.db.execute('PRAGMA journal_mode').fetchone()[0],
        mode=oct(os.stat(path + '/shared.sqlite').st_mode & 0o777))
elif step == 'put':
    s = Store(path + '/cat.sqlite')
    s.being('vol-a', 'volume', 'a volume, invented')
    s.being('d-1', 'folder'); s.being('d-2', 'folder'); s.being('c-1', 'content')
    act = s.put('vol-a', 'read', {'id': 'scan-1', 'by': 'nas', 'from': 'vol-a', 'at': '2026-10-18T10:00:00+03:00'})
    A = 'vol-a#scan-1'
    ids = [s.put('c-1', 'name', {'by': 'blake3', 'of': 'self', 'as': B3}, act=A),
           s.put('c-1', 'measure', {'of': 'self', 'as': 'information', 'value': {'count': '3', 'unit': 'By'}}, act=A),
           s.put('d-1', 'part', {'by': 'self', 'of': 'vol-a'}, act=A),
           s.put('d-1', 'hold', {'by': 'self', 'of': 'c-1', 'as': store.escape(b'IMG\xff%.CR2')}, act=A)]
    again = s.put('d-1', 'hold', {'by': 'self', 'of': 'c-1', 'as': store.escape(b'IMG\xff%.CR2')}, act=A)
    rows = s.get('d-1')
    say(act=act, ids=ids, again=again, n=s.count(), d1=rows,
        minted=all(i.startswith(v + '-') and len(i) == len(v) + 17 for i, v in zip(ids, ['name', 'measure', 'part', 'hold'])),
        escaped=store.escape(b'IMG\xff%\n.CR2'), back=store.unescape(store.escape(b'IMG\xff%\n.CR2')).hex(),
        other_form=refused(lambda: s.put('d-1', 'hold', {'id': ids[3], 'by': 'self', 'of': 'c-1', 'as': 'other'}, act=A)),
        no_act=refused(lambda: s.put('d-1', 'hold', {'by': 'self', 'of': 'c-1', 'as': 'b'})),
        bad_role=refused(lambda: s.put('d-1', 'hold', {'by': 'self', 'of': 'c-1', 'to': 'nas'}, act=A)),
        bad_nature=refused(lambda: s.put('vol-a', 'read', {'id': 'scan-2', 'by': 'd-1', 'at': '2026-10-18T11:00:00+03:00'})),
        no_being=refused(lambda: s.put('d-1', 'hold', {'by': 'self', 'of': 'c-404', 'as': 'c'}, act=A)),
        act_missing=refused(lambda: s.put('d-1', 'hold', {'by': 'self', 'of': 'c-1', 'as': 'd'}, act='vol-a#scan-9')),
        not_an_act=refused(lambda: s.put('d-1', 'hold', {'by': 'self', 'of': 'c-1', 'as': 'e'}, act='d-1#' + ids[2])),
        control=refused(lambda: s.put('d-1', 'hold', {'by': 'self', 'of': 'c-1', 'as': 'IMG\n.CR2'}, act=A)),
        sealed=refused(lambda: s.put('d-1', 'hold', {'held': 'root:vault/0123456789abcdef0123456789abcdef'}, act=A)),
        government=refused(lambda: s.put('c-1', 'name', {'by': 'tr-tckn', 'of': 'self', 'as': '10000000146'}, act=A)),
        kind_kept=refused(lambda: s.being('c-1', 'folder')))
elif step == 'check':
    s = Store(path + '/cat.sqlite')
    found = store.check([s])
    small = sorted({r for r, w, m in found})
    store.UNION_ROWS = 0
    s2 = Store(path + '/cat.sqlite')
    big = store.check([s2])
    say(found=found, small=small, big=big)
elif step == 'conflicts':
    s = Store(path + '/cat.sqlite')
    A = 'vol-a#scan-1'
    s.being('d-3', 'folder')
    s.put('d-2', 'part', {'by': 'self', 'of': 'd-3'}, act=A)
    s.put('d-3', 'part', {'by': 'self', 'of': 'd-2'}, act=A)
    s.put('c-1', 'name', {'by': 'sha-256', 'of': 'self', 'as': 'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad'}, act=A)
    s.put('note-1', 'hold', {'id': 'h1', 'by': 'nas', 'of': 'c-1', 'as': 'a different name'}, act=A)
    small = store.check([s])
    store.UNION_ROWS = 0
    big = store.check([Store(path + '/cat.sqlite')])
    say(small=small, big=big)
elif step == 'beside':
    s = Store(path + '/cat.sqlite')
    s.bulk('measure', [('c-1', {'of': 'c-1', 'as': 'mass', 'value': {'count': '3', 'unit': 'kg'}})], act='vol-a#scan-1',
           beings=('of',), judge_every=0)          # a row no put would keep: only the engine's whole judging finds it
    alone = store.check([s])
    n = s.count() + s.db.execute('SELECT COUNT(*) FROM being').fetchone()[0]
    b = Store(path + '/big.sqlite')
    b.being('vol-b', 'volume')
    b.put('vol-b', 'read', {'id': 'scan', 'by': 'nas', 'from': 'vol-b', 'at': '2026-10-18T10:00:00+03:00'})
    b.beings([(f'd-b{i}', 'folder') for i in range(n + 5)])
    b.bulk('part', [(f'd-b{i}', {'by': f'd-b{i}', 'of': 'vol-b'}) for i in range(n + 5)], act='vol-b#scan',
           beings=('by', 'of'))
    store.UNION_ROWS = n + 2
    both = store.check([b, Store(path + '/cat.sqlite')])
    say(alone=alone, both=both, n=n)
elif step == 'export':
    s = Store(path + '/cat.sqlite')
    sts, act = s.export('d-1', by='session-t')
    p = store.write_bean('.', 'd-1', sts, act, kind='folder', title='a folder, invented')
    say(sts=sts, act=act, wrote=os.path.exists(p))
elif step == 'reimport':
    s = Store(path + '/cat.sqlite')
    before = s.get('d-1')
    n = s.import_bean('d-1')
    after = s.get('d-1')
    nas_n = s.import_bean('nas')
    sts, act = s.export('nas', by='session-t')
    u = store.union_of('d-1', [s])
    say(before=before, after=after, n=n, nas_n=nas_n, nas_new=sts, nas_act=act, union=u,
        series=s.series_import('nas', 'temps', '0'), back=s.series_export('nas', 'temps', '0').decode('utf-8'))
elif step == 'writers':
    import multiprocessing
    def one(k):
        t = Store(path + '/many.sqlite')
        t.being('host-' + str(k), 'host')
        a = t.put('host-' + str(k), 'make', {'id': 'made', 'by': 'nas', 'at': '2026-10-18T12:00:00+03:00'})
        for j in range(50):
            t.put('host-' + str(k), 'hold', {'by': 'self', 'of': {'count': str(j + 1), 'unit': 'GBy'}}, act='host-%d#made' % k)
        t.close()
    Store(path + '/many.sqlite').close()
    ps = [multiprocessing.Process(target=one, args=(k,)) for k in range(8)]
    [p.start() for p in ps]; [p.join() for p in ps]
    t = Store(path + '/many.sqlite')
    say(rows=t.count(), codes=[p.exitcode for p in ps], snap=t.snapshot().execute('SELECT COUNT(*) FROM v_hold').fetchone()[0])
elif step == 'bulk':
    s = Store(path + '/bulk.sqlite')
    s.beings([('vol-b', 'volume'), ('d-9', 'folder')] + [('c-%04d' % i, 'content') for i in range(1000)])
    s.put('vol-b', 'read', {'id': 'scan-1', 'by': 'nas', 'from': 'vol-b', 'at': '2026-10-18T10:00:00+03:00'})
    rows = [('d-9', {'by': 'd-9', 'of': 'c-%04d' % i, 'as': 'f%04d.jpg' % i}) for i in range(1000)]
    rows.append(('d-9', {'by': 'd-9', 'of': 'unknown', 'as': 'unread.jpg'}))
    new = s.bulk('hold', rows, act='vol-b#scan-1', beings=('by', 'of'), judge_every=100)
    again = s.bulk('hold', rows, act='vol-b#scan-1', beings=('by', 'of'), judge_every=100)
    one = s.put('d-9', 'hold', {'by': 'self', 'of': 'c-0007', 'as': 'f0007.jpg'}, act='vol-b#scan-1')
    got = [r for v, r, a in s.get('d-9') if r.get('as') in ('f0007.jpg', 'unread.jpg')]
    bad = refused(lambda: s.bulk('hold', [('d-9', {'by': 'd-9', 'of': 'c-0001', 'to': 'x'})], act='vol-b#scan-1',
                                 beings=('by', 'of')))
    say(new=new, again=again, one=one, got=got, holds=s.db.execute('SELECT COUNT(*) FROM v_hold').fetchone()[0],
        bad=bad, check=store.check([s, Store(path + '/cat.sqlite')]))
elif step == 'gone':
    s = Store(path + '/cat.sqlite')
    sid = [r['id'] for v, r, a in s.get('d-1') if v == 'hold'][0]
    s.gone('d-1', sid, by='session-t', why='the file was moved')
    rec = s.db.execute('SELECT verb, being, id, by, why FROM gone').fetchall()
    free = s.put('d-1', 'hold', {'id': sid, 'by': 'self', 'of': 'c-1', 'as': 'moved.CR2'}, act='vol-a#scan-1')
    say(rec=rec, free=free, why_needed=refused(lambda: s.gone('d-1', sid, by='session-t', why='')))
elif step == 'here':
    kept = store.kept_here('.')
    s = store.open_store('t', root='.')
    s.being('c-1', 'content')
    s.put('c-1', 'make', {'id': 'm', 'by': 'nas', 'at': '2026-10-18T12:00:00+03:00'})
    s.being('vol-t', 'volume', 'the second disk')
    s.being('vol-u', 'volume')
    open('reading.yaml', 'w').write('what: "the volume titled the second disk"\nsteps:\n'
                                    '  - { id: v, op: select, kind: volume, store: t, where: [ { path: title, "=": "the second disk" } ] }\n')
    titled = subprocess.run([sys.executable, 'bin/reckon.py', '--ad-hoc', 'reading.yaml'], capture_output=True, text=True).stdout
    sys.path.insert(0, sys.argv[3])
    import view_model as vm
    vm.ROOT = os.path.abspath('.')
    say(kept={k: [v[0], v[2]] for k, v in kept.items()}, path=s.path, titled=titled, fm=vm.stored_fm('vol-t'),
        none=vm.stored_fm('vol-nowhere'), made=vm.stored_fm('c-1'))
'''


def probe(step, path, env=None):
    r = grow.run(PY, '-c', PROGRAM, step, path, os.path.join(ROOT, 'assets', 'view', 'lib'), cwd=G, env=env)
    lines = [l for l in r.stdout.splitlines() if l.startswith('{')]
    if r.returncode or not lines:
        return None, r
    return json.loads(lines[-1]), r


def save(what, body):
    return grow.run(PY, 'bin/save.py', 'sam', what, '--body', body, cwd=G)


T = tempfile.mkdtemp(prefix='core-store-')
G = os.path.join(T, 'g')
S = os.path.join(T, 'stores')
os.makedirs(S)
try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam')
    check("a garden of the core grows, and carries the store's tool", r.returncode == 0
          and os.path.isfile(os.path.join(G, 'bin', 'store.py')), r.out[-600:])
    me = socket.gethostname().lower().split('.')[0]
    write('beans/nas.md', doc('nas', 'host', 'say: { by: sam, at: now }',
                              f'name: {{ by: dns, of: self, as: "{me}.example.org" }}',
                              details=f"details:\n  roots:\n    test:\n      system: unix-filesystem\n      at: \"{me}:{S}\"\n"
                                      f"  stores:\n    t:\n      at: \"root:test/t.sqlite\"\n      form: sqlite\n"))
    write('beans/note-1.md', doc('note-1', 'document', 'say: { by: sam, at: now }', 'hold: { id: h1, by: nas, of: self }'))
    write('beans/session-t.md', doc('session-t', 'session', 'make: { by: self, at: now }'))
    r = save('the fixtures', '- action: wrote [[nas]], [[note-1]], [[session-t]]')
    check("the fixtures are saved", r.returncode == 0, r.out[-800:])

    # ---- open
    j, r = probe('open', S)
    check("open: a store read only by its writer is kept in WAL; one another user reads, with a rollback journal and "
          "readable by others", j and j['solo'] == 'wal' and j['shared'] == 'delete' and j['mode'] == '0o644',
          (j, r.out[-800:]))

    # ---- put
    j, r = probe('put', S)
    ok = j is not None
    check("put: rows judged and kept; given no id, each named by its verb and sixteen digits of its form",
          ok and j['n'] == 5 and j['minted'] and j['act'] == 'scan-1', (j, r.out[-1200:]))
    check("...the same statement put twice is one row", ok and j['again'] == j['ids'][3] and j['n'] == 5, j)
    check("...a being's statements read back as kept, each with the act that knows it",
          ok and any(v == 'hold' and rr.get('of') == 'c-1' and a == ['vol-a#scan-1'] for v, rr, a in j['d1']), j and j['d1'])
    check("...a name in bytes written `escaped`, and read back to its bytes",
          ok and j['escaped'] == 'IMG%FF%25%0A.CR2' and j['back'] == b'IMG\xff%\n.CR2'.hex(), j)
    for key, says in (('other_form', 'kept already as another statement'), ('no_act', 'known by no act'),
                      ('bad_role', 'no role'), ('bad_nature', 'takes a being that is body'),
                      ('no_being', "no bean of this garden"), ('act_missing', 'kept nowhere'),
                      ('not_an_act', 'a knowing act'), ('control', 'control character'),
                      ('sealed', 'no sealed material'), ('government', 'held store'), ('kind_kept', 'keeps its kind')):
        check(f"...refused: {key.replace('_', ' ')}", ok and j[key] and says in j[key], (j or {}).get(key))

    # ---- the pointer, through the gate
    write('beans/note-2.md', doc('note-2', 'document', 'say: { by: sam, at: now }',
                                 'hold: { id: h2, by: nas, of: "store:content:c-1", as: "IMG_0001.CR2" }',
                                 'derive: { by: session-t, of: [d2], from: ["store:volume:vol-a#scan-1"], at: now }',
                                 'part: { id: d2, by: "store:folder:d-1", of: "store:volume:vol-a" }'))
    r = save('a note naming beings kept in a store', '- action: wrote [[note-2]]')
    check("pointer: a bean names beings kept only in a store, `store:<kind>:<id>`, and a statement of one: the gate "
          "passes it", r.returncode == 0, r.out[-800:])
    for name, line, says in (
            ("a kind that is none", 'hold: { by: nas, of: "store:gizmo:c-1" }', 'no kind of the law'),
            ("a kind not its bean's", 'hold: { by: nas, of: "store:content:nas" }', 'a being keeps its kind'),
            ("a statement where a being goes", 'hold: { by: nas, of: "store:content:c-1#x" }', 'names a statement'),
            ("a nature its role does not take", 'read: { by: "store:folder:d-1", at: now }', 'takes a being that is body')):
        write('beans/note-3.md', doc('note-3', 'document', 'say: { by: sam, at: now }', line))
        r = save('a bad pointer', '- action: wrote [[note-3]]')
        check(f"...refused by the gate: {name}", r.returncode != 0 and says in r.out, r.out[-600:])
        grow.run('git', 'reset', '-q', '--hard', cwd=G)
        grow.run('git', 'clean', '-qfd', 'beans', cwd=G)

    # ---- check: the union
    j, r = probe('check', S)
    ok = j is not None
    check("check: the union of git and a store whose pointers resolve has nothing to say, judged whole and by queries",
          ok and j['found'] == [] and [f for f in j['big'] if f[0] != 'size'] == [], (j, r.out[-1200:]))
    write('beans/note-4.md', doc('note-4', 'document', 'say: { by: sam, at: now }',
                                 'hold: { by: nas, of: "store:content:c-77" }'))
    save('a pointer to nothing kept', '- action: wrote [[note-4]]')
    write('beans/doc-a.md', doc('doc-a', 'document', 'say: { by: sam, at: now }',
                                f'name: {{ by: blake3, of: self, as: "{B3}" }}'))
    write('beans/d-2.md', doc('d-2', 'folder', 'say: { by: sam, at: now }', 'part: { by: self, of: "store:folder:d-3" }'))
    r = save('a bean named as a store keeps a content, and a folder', '- action: wrote [[doc-a]], [[d-2]]')
    j, r = probe('conflicts', S)
    ok = j is not None
    for mode in ('small', 'big'):
        f = (j or {}).get(mode) or []
        check(f"check ({'judged whole by the engine' if mode == 'small' else 'by queries, as for a large store'}): a "
              f"pointer that resolves nowhere here is found", ok and any(r == 'names' and 'c-77' in m for r, w, m in f), f)
        check("...a name given once naming a bean and a being of the store",
              ok and any(r == 'names' and 'doc-a' in m and 'c-1' in m for r, w, m in f), f)
        check("...a cycle through a store's part and a bean's", ok and any(r == 'order' and 'd-2' in m and 'd-3' in m
                                                                         for r, w, m in f), f)
        check("...one id, two forms: a bean's statement and a row of its being", ok and any(
            r == 'form' and 'note-1#h1' in w for r, w, m in f), f)
    j, r = probe('beside', S)
    ok = j is not None
    engine = [f for f in (j or {}).get('alone', []) if f[0] not in ('names', 'order', 'form', 'knowing', 'size')]
    check("check beside a large store: a small one is still judged whole, beside git — what only the engine's own rules "
          "find in it is found, and it is named in no note of what went unjudged",
          ok and engine and all(f in [tuple(x) for x in j['both']] or list(f) in j['both'] for f in engine)
          and not any(f[0] == 'size' and 'cat' in f[1] for f in j['both']), (j, r.out[-1500:]))
    grow.run('git', 'reset', '-q', '--hard', 'HEAD~2', cwd=G)

    # ---- between keepings
    for x in ('', '-wal', '-shm'):                      # a store begun again: its file and what WAL kept beside it
        if os.path.exists(os.path.join(S, 'cat.sqlite' + x)):
            os.remove(os.path.join(S, 'cat.sqlite' + x))
    j, r = probe('put', S)
    j, r = probe('export', S)
    ok = j is not None and j['wrote']
    check("export: a being kept only in the store gains a bean of its rows, its fillers pointers where they have no bean, "
          "known by one `derive` from the act that knew them",
          ok and j['act']['derive']['from'] == ['store:volume:vol-a#scan-1'] and len(j['sts']) == 2
          and any('store:content:c-1' in json.dumps(s) for s in j['sts']), (j, r.out[-1200:]))
    r = save('a folder exported from the store', '- action: wrote [[d-1]], from the store')
    check("...and the gate passes the bean the export wrote", r.returncode == 0, r.out[-800:])
    write('series/nas/temps/0.tsv', "at\tc\n0\t21.5\n1\t21.7\n")
    j, r = probe('reimport', S)
    ok = j is not None
    held = [a for v, rr, a in (j or {}).get('after', []) if v == 'hold']
    check("between: a row into a bean and back is one statement, now known by two acts: the store's and the bean's "
          "(the bean's act kept as a row beside it)",
          ok and [v for v, rr, a in j['after'] if v != 'derive'] == [v for v, rr, a in j['before']]
          and [v for v, rr, a in j['after'] if v == 'derive'] == ['derive'] and held and len(held[0]) == 2
          and held[0][0] == 'vol-a#scan-1' and held[0][1].startswith('d-1#derive-'), (j, r.out[-1200:]))
    check("...a bean into the store and back adds nothing to it", ok and j['nas_n'] >= 2 and j['nas_new'] == []
          and j['nas_act'] is None, j)
    check("...a series' part into the store and back is the same bytes", ok and j['back'] == "at\tc\n0\t21.5\n1\t21.7\n", j)
    check("...a statement kept in a bean and in a store reads as one", ok and len(j['union']) == len(
        {json.dumps(x, sort_keys=True) for x in j['union']}) and sum(1 for x in j['union'] if 'hold' in x) == 1,
        (j or {}).get('union'))

    # ---- many writers, a snapshot
    j, r = probe('writers', S)
    check("writers: eight processes writing one store at once, every row kept", j and j['rows'] == 8 * 51
          and j['codes'] == [0] * 8, (j, r.out[-800:]))
    check("snapshot: a long read is made from a copy taken in steps", j and j['snap'] == 8 * 50, j)

    # ---- bulk
    j, r = probe('bulk', S)
    ok = j is not None
    check("bulk: a tool's thousands kept in one transaction, every hundredth judged; again, none new; a row named as `put` "
          "names the same statement", ok and j['new'] == 1001 and j['again'] == 0 and j['holds'] == 1001
          and any(g['id'] == j['one'] for g in j['got']), (j, r.out[-1200:]))
    check("...a content not read is held as `unknown`, and a row out of its verb's form is refused even in bulk",
          ok and any(g.get('of') == 'unknown' for g in j['got']) and j['bad'] and 'no role' in j['bad'], j)
    check("...and the check of the union — git, this store and the other one kept here — finds nothing to say of it",
          ok and j['check'] == [], j and j['check'])

    # ---- gone
    j, r = probe('gone', S)
    check("gone: a statement leaves a store with who, when and why recorded, and its id is free for another form",
          j and j['rec'] and j['rec'][0][3] == 'session-t' and j['rec'][0][4] == 'the file was moved' and j['free']
          and 'reason' in (j['why_needed'] or ''), (j, r.out[-800:]))

    # ---- here
    j, r = probe('here', S)
    check("here: the store a host's bean declares is found on that host by its name, and opened there",
          j and j['kept'].get('t', [None])[0] == os.path.join(S, 't.sqlite') and j['path'] == os.path.join(S, 't.sqlite'),
          (j, r.out[-800:]))
    check("...a reading of it reads what the store says of each being: its kind and title, a `where` on the title "
          "selects the volume titled so and not the other", j and 'vol-t' in j['titled'] and 'vol-u' not in j['titled'],
          j and j.get('titled'))
    check("...and a page reads a being kept only in it as its bean would hold it — kind, title, statements — so a "
          "table of a store's reading has its cells; a being no store keeps reads as none",
          j and j['fm'] == {'bean': 'vol-t', 'kind': 'volume', 'title': 'the second disk', 'statements': []}
          and j['none'] == {} and j['made'].get('statements') and 'make' in j['made']['statements'][0], j and j.get('fm'))
    r = grow.run(PY, 'bin/store.py', 'check', 't', cwd=G)
    check("...and `store.py check` judges it over git", 'store check: 1 store(s)' in r.out, r.out[-600:])
    shutil.rmtree(S)
    shutil.rmtree(os.path.join(G, 'series'), ignore_errors=True)
    r = grow.run(PY, 'core/check.py', cwd=G)
    check("the gate's verdict needs no store: it passes with every store file gone", r.returncode == 0, r.out[-400:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nstore: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
