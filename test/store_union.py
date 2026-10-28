#!/usr/bin/env python3
"""store_union — the union judged by the same rules at every size (the next version's P5; core/union.py): each rule
that is a reading of the law, compiled to SQL over git and the stores, gives the refusals the core's engine gives over
the same union read as beans — the same words, at the same places, in the same order.

Every case of test/core-cases.yaml, the garden alone and each case beside it, is kept five ways, and each way is judged
both ways, the engine's verdict over the union (bin/store.py `_union_garden`, then the engine's readings) beside the
SQL's (bin/store.py `compiled`, then core/union.py `refusals`):

  git       every bean in git; a store keeps nothing of them
  store     every bean a being of one store, its statements its rows
  half      every other bean moved into the store
  split     every bean in git, every other statement of each a row of its being in the store (a being in both)
  two       every other bean in one of two stores, and a third of the rest's statements in the second (a being in
            two stores), each store's rows after the first's

And the store's check itself (bin/store.py `_check`) of each way of the garden and of every case of the readings and
of `names`, as a large union and whole: the same refusals of each reading, and of a name a namespace gives once — the
engine's own code, given the names the stores give.

Beside them: a cycle that runs through git and two stores; a row the store keeps twice over (a statement its bean
holds), which the union holds once; a reading with no SQL form here, named; and bin/store.py's check of a large union,
which names every core rule it does not judge at that size. Invented beings; nothing here is a fact.

Run: python3 test/store_union.py   (0 = green)
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
from core import engine, lines, read, reckon, union  # noqa: E402
from core.law import Law  # noqa: E402
import store  # noqa: E402

FAILS = []
CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
ZONE = CASES['zone']
ACT = 'scan-0#s0'


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
    """(a store at `path`: `beings` [(id, kind)] declared, then each of `rows` [(being, j, verb, roles)] put unjudged,
    known by one act; the (being, j) of each row the store refuses to keep — a kind that is none, a key no role)."""
    for x in (path, path + '-wal', path + '-shm'):
        if os.path.exists(x):
            os.remove(x)
    s = store.Store(path, law=LAW, garden=git)
    s.put('scan-0', 'say', {'id': 's0', 'by': 'sam', 'at': '2026-10-01T09:00:00+03:30'}, judge=False)
    s.beings([(b, k, b) for b, k in beings])
    refused = set()
    for b, j, verb, roles in rows:
        try:
            s.put(b, verb, roles, act=ACT, judge=False)
        except store.StoreError:
            refused.add((b, j))
    return s, refused


def both(git, stores):
    """(the engine's, the SQL's): [(rule, place, words)] of each rule that is a reading, over the union."""
    G, _added = store._union_garden(stores, git)
    J = engine.Judge(LAW, G)
    J.readings()
    engine_says = [tuple(f) for f in J.out]
    sql_says = []
    with store.compiled(stores, git, LAW) as U:
        for rule, reading in LAW.readings.items():
            sql_says += [(rule, w, m) for w, m in U.refusals(reading)]
    return engine_says, sql_says


# THE GRAMMAR'S COLUMNS AND OPERATIONS AT SIZE (core 3.2 to 3.4): readings no rule states yet, each written as a rule's
# reading is, that read what the grammar gained — a statement's columns, of the member itself and of a value naming one
# (I.1); a position's (I.2); a path through every depth and into a value's parts, and a bean's header (I.7); `overlap`
# (I.8); a refusal told at a path (I.9) — each held to the reckoner's own reading of the union read as beans
GRAMMAR = {
    'statements': {
        'steps': [{'id': 'd', 'op': 'select', 'entries': 'decline'},
                  {'id': 'me', 'op': 'describe', 'of': 'd', 'as': 's'},
                  {'id': 'it', 'op': 'describe', 'of': 'me', 'at': 'of', 'as': 'o'},
                  {'id': 'r', 'op': 'select', 'entries': 'respond'},
                  {'id': 'rs', 'op': 'describe', 'of': 'r', 'at': 'of', 'as': 'o'},
                  {'id': 'ag', 'op': 'select', 'entries': 'agree'},
                  {'id': 'ags', 'op': 'describe', 'of': 'ag', 'as': 's'}],
        'refuse': [{'of': 'it', 'at': 'of', 'message': "{s.place} {s.bean} {s.verb} {s.index} {s.id} -> {o.being} "
                                                        "{o.place} {o.bean} {o.verb} {o.index} {o.id} {o.kind}"},
                   {'of': 'rs', 'at': 'of', 'message': "{o.being} {o.place} {o.id} {o.system}"},
                   {'of': 'ags', 'message': "{s.place} {s.id} {by:set}"}]},
    'positions': {
        'steps': [{'id': 'b', 'op': 'select', 'entries': 'be'},
                  {'id': 'p', 'op': 'describe', 'of': 'b', 'at': 'at', 'as': 'p'},
                  {'id': 'pt', 'op': 'select', 'of': 'p', 'where': [{'path': 'p.system', '∃': 'true'}]},
                  {'id': 'a', 'op': 'select', 'entries': 'attend'},
                  {'id': 't', 'op': 'describe', 'of': 'a', 'at': 'at', 'as': 't'}],
        'refuse': [{'of': 'pt', 'at': 'at', 'message': "{p.being}: {p.system} {p.point} {p.from} {p.to} {p.unit}"},
                   {'of': 't', 'message': "{t.being}: {t.system} {t.point} {t.from} {t.to} {t.unit} {t.kind} {t.place}"}]},
    'codes': {                     # a code's scheme (core 4.10), beside a value that is no code
        'steps': [{'id': 'c', 'op': 'select', 'entries': 'classify'},
                  {'id': 'd', 'op': 'describe', 'of': 'c', 'at': 'as', 'as': 'd'},
                  {'id': 'all', 'op': 'select', 'entries': 'be'},
                  {'id': 'e', 'op': 'describe', 'of': 'all', 'at': 'at', 'as': 'e'}],
        'refuse': [{'of': 'd', 'message': "{d.being}: {d.scheme} {d.system}"},
                   {'of': 'e', 'message': "{e.being}: {e.scheme}"}]},
    'overlap': {
        'steps': [{'id': 'a', 'op': 'select', 'entries': 'attend'},
                  {'id': 't', 'op': 'describe', 'of': 'a', 'at': 'at', 'as': 't'},
                  {'id': 'who', 'op': 'describe', 'of': 't', 'at': 'by', 'as': 'who'},
                  {'id': 'all', 'op': 'overlap', 'of': 'who', 'from': 't.from', 'to': 't.to', 'by': 'who.being',
                   'as': ['e', 'l']},
                  {'id': 'first', 'op': 'overlap', 'of': 'who', 'from': 't.from', 'to': 't.to', 'by': 'who.being',
                   'first': 'true', 'as': ['e', 'l']},
                  {'id': 'held', 'op': 'overlap', 'of': 'who', 'by': ['who.being', 'of'], 'groups': 'values',
                   'as': ['e', 'l']},
                  {'id': 'raw', 'op': 'overlap', 'of': 'a', 'from': 'at', 'to': 'at', 'as': ['e', 'l']}],
        'refuse': [{'of': 'all', 'message': "{e.t.being} | {l.t.being} {e.who.being}"},
                   {'of': 'first', 'at': 'at', 'message': "{e.at} | {l.at}"},
                   {'of': 'held', 'message': "{e.of} {e.by} | {l.of} {l.by}"},
                   {'of': 'raw', 'message': "{e.at} | {l.at}"}]},
    'depths': {
        'steps': [{'id': 'beans', 'op': 'select'},
                  {'id': 'titled', 'op': 'select', 'of': 'beans', 'where': [{'path': 'title', '∃': 'true'}]},
                  {'id': 'deep', 'op': 'select', 'of': 'beans', 'where': [{'path': 'details.**', '=': 'needle'}]},
                  {'id': 'p', 'op': 'select', 'entries': 'pay'},
                  {'id': 'xts', 'op': 'select', 'of': 'p', 'where': [{'path': 'of.unit', '=': 'XTS'}]},
                  {'id': 'any', 'op': 'select', 'of': 'p', 'where': [{'path': '**', '=': 'sam'}]},
                  {'id': 'every', 'op': 'describe', 'of': 'p', 'at': '**', 'as': 'v'},
                  {'id': 'units', 'op': 'describe', 'of': 'p', 'at': 'of.unit', 'as': 'u'},
                  {'id': 'ag', 'op': 'select', 'entries': 'agree'},
                  {'id': 'parties', 'op': 'describe', 'of': 'ag', 'at': 'by', 'as': 'who'}],
        'refuse': [{'of': 'titled', 'message': "{bean} {kind} {title} {summary} {tags:set} {details.**:set}"},
                   {'of': 'deep', 'message': "{bean}"},
                   {'of': 'xts', 'at': 'of', 'message': "{of.count} {of.unit} {**:set}"},
                   {'of': 'any', 'message': "{by}"},
                   {'of': 'every', 'message': "{v.being} {v.kind} {v.place} {v.system}"},
                   {'of': 'units', 'message': "{u.being} {u.system}"},
                   {'of': 'parties', 'message': "{who.being} {who.kind}"}]},
}


def grammar(git, stores, said):
    """[(reading, the reckoner's, the SQL's)] of each reading of GRAMMAR whose two readings of the union differ, each
    [(place, words)]; `said` counts what each refuses."""
    G, _added = store._union_garden(stores, git)
    J = engine.Judge(LAW, G)
    out = []
    with store.compiled(stores, git, LAW) as U:
        for name, r in GRAMMAR.items():
            try:
                e = [(w, m) for w, m, _p in reckon.refusals(J, r)]
            except reckon.Refused as x:              # a reading that cannot be read: refused alike
                e = [('cannot be read', str(x))]
            try:
                s = U.refusals(r)
            except reckon.Refused as x:
                s = [('cannot be read', str(x))]
            said[name] = said.get(name, 0) + len(e)
            if e != s:
                out.append((name, e, s))
    return out


def keepable(verb, roles):
    """Whether a store can keep a statement: of a verb of the law, its every key a role, a qualifier or `id`, `while`,
    `why`, `note` — never sealed."""
    row = LAW.verbs.get(verb)
    return row is not None and all(k in (row.get('roles') or {}) or k in (row.get('qualifiers') or {})
                                   or k in ('id', 'while', 'why', 'note') for k in roles)


def ways(beans, T):
    """Each way of keeping `beans`: (name, git, [stores]). A sealed statement stays in git (a store keeps none), and so
    does one that is not one verb and its roles."""
    order = sorted(beans)

    def split(where, stuck):
        """(git, [(rows, beings)] a store each): `where(k, j)` says where the j-th statement of the k-th bean goes —
        None for git, else the store's number."""
        g, kept_, ids = {}, [([], []), ([], [])], set()
        for k, bid in enumerate(order):
            b = beans[bid]
            stay = []
            for j, st in enumerate(b.statements):
                to = where(k, j)
                ok = isinstance(st, dict) and len(st) == 1 and isinstance(next(iter(st.values())), dict) \
                    and keepable(*next(iter(st.items())))
                sid = next(iter(st.values())).get('id') if ok else None
                if ok and sid is not None:          # an id names one statement, and is one word: else git keeps it
                    ok = isinstance(sid, str) and engine.ID.match(sid) and (to, bid, sid) not in ids
                if to is None or not ok or (bid, j) in stuck:
                    stay.append(st)
                    continue
                ids.add((to, bid, sid))
                (v, r), = st.items()
                kept_[to][0].append((bid, j, v, dict(r)))
                if (bid, b.kind or 'document') not in kept_[to][1]:
                    kept_[to][1].append((bid, b.kind or 'document'))
            if stay or all(where(k, j) is None for j in range(len(b.statements))):
                g[bid] = bean(bid, b.kind, stay, {x: y for x, y in b.header.items()
                                                  if x not in ('bean', 'kind', 'title', 'statements')})
        return garden(g), kept_
    out = []
    for name, where, n in (('git', lambda k, j: None, 1), ('store', lambda k, j: 0, 1),
                           ('half', lambda k, j: 0 if k % 2 else None, 1),
                           ('split', lambda k, j: 0 if j % 2 else None, 1),
                           ('two', lambda k, j: 0 if k % 2 or j % 3 != 2 else 1, 2)):
        stuck = set()
        while True:                      # what a store refuses to keep stays in git, and the way is kept again
            git, ks = split(where, stuck)
            made = [kept(os.path.join(T, f"{name}-{x}.sqlite"), git, *ks[x]) for x in range(n)]
            more = set().union(*(r for _s, r in made)) - stuck
            if not more:
                break
            for s, _r in made:
                s.close()
            stuck |= more
        out.append((name, git, [s for s, _r in made]))
    return out


T = tempfile.mkdtemp(prefix='store-union-')
try:
    base = {bid: bean(bid, b['kind'], b['statements']) for bid, b in CASES['garden'].items()}
    cases = [('the garden alone', None)] + [(f"passes: {c.get('name') or c['bean']}", c) for c in CASES['good']] + \
        [(f"rule {c['rule']}: {c['bean']}" + (f" ({c['name']})" if c.get('name') else ''), c) for c in CASES['bad']]
    differ, judged, refused = [], 0, 0
    gdiffer, gsaid = [], {}
    for name, c in cases:
        beans = dict(base)
        if c is not None:
            beans[c['bean']] = bean(c['bean'], c['kind'], c['statements'], c.get('header'))
        for way, git, stores in ways(beans, T):
            e, s = both(git, stores)
            judged += 1
            refused += len(e)
            if e != s:
                differ.append((name, way, e, s))
            gdiffer += [(name, way) + g for g in grammar(git, stores, gsaid)]
            for x in stores:
                x.close()
    check(f"every case of test/core-cases.yaml, kept five ways ({judged} unions): each reading's SQL gives the engine's "
          f"refusals over the union, the same words at the same places in the same order ({refused} refusals)",
          not differ, differ[:3])
    registry = lines.law_view(LAW).registry
    bad = {k: [t for lv, t in reckon.check_rule(k, r, registry, LAW) if lv == 'error'] for k, r in GRAMMAR.items()}
    check("the readings of the grammar's columns and operations are rules' readings the law's check takes",
          not any(bad.values()), bad)
    check(f"...and each, compiled to SQL, gives the reckoner's refusals over the union read as beans — a statement's "
          f"columns and a position's, a bean's header, every depth and a value's parts, `overlap`, a refusal told at a "
          f"path — the same words at the same places in the same order, over every one of those unions "
          f"({', '.join(f'{k} {v}' for k, v in gsaid.items())} refusals)", not gdiffer and all(gsaid.values()),
          gdiffer[:2])
    extra = dict(base, **{'g-1': bean('g-1', 'document', [{'say': {'by': 'sam', 'at': 'now'}},
                                                          {'pay': {'by': 'sam', 'of': {'count': '3', 'unit': 'XTS'}}}],
                                      {'summary': 'a sum', 'tags': ['b', 'a'],
                                       'details': {'deep': [{'x': 'needle'}], 'n': '2'}})})
    hdiffer, hsaid, deep = [], {}, []
    for way, git, stores in ways(extra, T):
        hdiffer += [(way,) + g for g in grammar(git, stores, hsaid)]
        if way == 'git':
            G, _a = store._union_garden(stores, git)
            deep = [w for w, m, _p in reckon.refusals(engine.Judge(LAW, G), GRAMMAR['depths']) if m == 'g-1']
        for x in stores:
            x.close()
    check("...and over a bean whose header holds a summary, tags and a text deep in its details, kept five ways: a "
          "bean's header, and a text at any depth of it, read alike, a bean's refusal told at its bean (core 4.10)",
          not hdiffer and deep == ['g-1'], (hdiffer[:2], deep))
    rules = {c['rule'] for c in CASES['bad']}
    check("...and the cases hold a refusal of each rule that is a reading (order, life, necessity)",
          set(LAW.readings) <= rules, set(LAW.readings) - rules)

    # ---- the store's check of a large union, against the engine's of the same union whole
    def spoken(found):
        return [f for f in found if f[0] in LAW.readings or (f[0] == 'names' and 'once, and it names' in f[2])]
    differ, judged, refused = [], 0, 0
    for name, c in cases:
        if c is not None and c.get('rule') not in set(LAW.readings) | {'names'}:
            continue
        beans = dict(base)
        if c is not None:
            beans[c['bean']] = bean(c['bean'], c['kind'], c['statements'], c.get('header'))
        for way, git, stores in ways(beans, T):
            own = {tuple(f) for f in engine.Judge(LAW, git).run()}
            whole = spoken(store._check(stores, git, LAW, own))
            keep = store.UNION_ROWS
            store.UNION_ROWS = -1
            try:
                large = spoken(store._check(stores, git, LAW, own))
            finally:
                store.UNION_ROWS = keep
            judged += 1
            refused += len(whole)
            if whole != large:
                differ.append((name, way, whole, large))
            for x in stores:
                x.close()
    check(f"the store's check of a large union says what the engine says of it whole: the refusals of each reading and "
          f"each name a namespace gives once naming two beings, beyond git's own, for the garden and every case of those "
          f"rules kept five ways ({judged} unions, {refused} refusals)", not differ and refused, differ[:3])

    # ---- a cycle through git and two stores, the second's row after the first's
    git = garden(dict(base, **{'d-1': bean('d-1', 'folder', [{'say': {'by': 'sam', 'at': 'now'}},
                                                             {'part': {'by': 'self', 'of': 'd-2'}}])}))
    a, _r = kept(os.path.join(T, 'cyc-a.sqlite'), git, [('d-2', 0, 'part', {'by': 'self', 'of': 'd-3'})],
                 [('d-2', 'folder'), ('d-3', 'folder')])
    b, _r = kept(os.path.join(T, 'cyc-b.sqlite'), git, [('d-3', 0, 'part', {'by': 'self', 'of': 'd-1'}),
                                                         ('d-1', 1, 'part', {'by': 'self', 'of': 'd-2'})],
                 [('d-3', 'folder'), ('d-1', 'folder')])
    e, s = both(git, [a, b])
    check("a cycle through a bean's part and two stores' is found by the SQL as by the engine, at each of its three "
          "statements, in the order the garden reads them; the second store's row its bean's own already, held once",
          e == s and [w for r, w, m in s if r == 'order' and 'part of itself' in m] == ['d-1[1] part', 'd-2[0] part',
                                                                                       'd-3[0] part'], (e, s))
    a.close()
    b.close()

    # ---- a reading with no SQL form here
    L2 = Law.load(('VOCAB.md', CASES['vocab']))
    weird = dict(L2.readings['necessity'], steps=list(L2.readings['necessity']['steps']) + [
        {'id': 'n', 'op': 'count', 'of': 'necessary'}])
    s0, _r = kept(os.path.join(T, 'nosql.sqlite'), garden(base), [], [])
    with store.compiled([s0], garden(base), L2) as U:
        try:
            U.refusals(weird)
            said = None
        except union.NoSQL as x:
            said = str(x)
    check("a reading a step of which has no SQL form here is not read by SQL: the step and its operation are named",
          said and 'count' in said and 'step n' in said, said)
    s0.close()

    # ---- the check of a large union names each core rule it does not judge at that size
    git = garden(base)
    s1, _r = kept(os.path.join(T, 'large.sqlite'), git, [('d-7', 0, 'part', {'by': 'self', 'of': 'd-8'}),
                                                          ('d-8', 0, 'part', {'by': 'self', 'of': 'd-7'})],
                  [('d-7', 'folder'), ('d-8', 'folder')])
    small = store._check([s1], git, LAW, [])
    keep = store.UNION_ROWS
    store.UNION_ROWS = 0
    try:
        large = store._check([s1], git, LAW, [])
    finally:
        store.UNION_ROWS = keep
    size = [m for r, _w, m in large if r == 'size']
    not_judged = size[0].split('not judged over the union at this size: ')[1].split(';')[0].split(', ') if size else []
    check("the check of a large union: the cycle the engine finds whole, the SQL finds at the same place, in the same "
          "words", [f for f in small if f[0] == 'order'] == [f for f in large if f[0] == 'order']
          and any(f[0] == 'order' for f in small), (small, large))
    check("...and it names, rule by rule, each core rule it judges neither by a reading's SQL nor by its queries "
          f"({', '.join(not_judged)})", size and not_judged == [r for r in LAW.rules if r not in LAW.readings
                                                               and r not in store.QUERIED], size)
    s1.close()
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\n{len(FAILS)} failed" + (": " + "; ".join(FAILS) if FAILS else ''))
sys.exit(1 if FAILS else 0)
