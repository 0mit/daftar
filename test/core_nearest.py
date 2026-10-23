#!/usr/bin/env python3
"""core_nearest — one ordering of the candidates that hold one case (core 3.1): nearest or most specific first, by the
keys each use names in core/law/lines.yaml `nearest`, and at each use what a tie of the nearest does — refuse, both
stand, or the declared order — read from the law by the code of each use (core/nearest.py).

The mechanism by its test vectors; the law's check of the rows; and each of the four uses — the flow table's rows a pass
meets (core/law.py `decide`), the pattern rows a name fits and the wholes a member inherits from (core/groupings.py),
the locations that cover a path (bin/cursor.py) — judged under each of the three ties by a copy of the law, so the row
is shown to decide. The law as released keeps every verdict it gave before (its uses' ties: `both`, `order`, `both`,
`order`). Invented beings; nothing here is a fact. (`python` on Windows.)"""
import copy
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
from core import groupings, nearest, read  # noqa: E402
from core.law import Law  # noqa: E402

FAILS = []


def check(name, cond, detail=''):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


LAWDIR = os.path.join(ROOT, 'core', 'law')
LINES = read.data(os.path.join(LAWDIR, 'lines.yaml'))
SLOTS = {str(r['slot']): r for r in LINES['slots']}
SYSTEMS = {str(r['system']): r for r in read.data(os.path.join(LAWDIR, 'systems.yaml'))['systems']
           if r.get('dimension') == 'time' and r.get('reckoning') == 'arithmetic'}


def lines_with(use, tie=None, keys=None):
    """lines.yaml's data with one use's tie, or its keys, changed: the law a garden could ratify instead."""
    d = copy.deepcopy(LINES)
    for r in d['nearest']['uses']:
        if r['use'] == use:
            if tie is not None:
                r['tie'] = tie
            if keys is not None:
                r['keys'] = [{'key': k, 'meaning': k} for k in keys]
    return d


# ---- THE MECHANISM, by its vectors
M = {'a': lambda x: x[0], 'b': lambda x: x[1]}
items = [(1, 2, 'p'), (0, 5, 'q'), (0, 3, 'r'), (0, 3, 's')]
check("rank: nearest first by the keys in the order named, the order given kept between equals",
      nearest.rank(items, ('a', 'b'), M) == [(0, 3, 'r'), (0, 3, 's'), (0, 5, 'q'), (1, 2, 'p')]
      and nearest.rank(items, ('b', 'a'), M) == [(1, 2, 'p'), (0, 3, 'r'), (0, 3, 's'), (0, 5, 'q')])
check("nearest: the least by every key, and what each tie lets stand of those as near",
      nearest.nearest(items, ('a', 'b'), M, 'both') == ([(0, 3, 'r'), (0, 3, 's')], [(0, 3, 'r'), (0, 3, 's')])
      and nearest.nearest(items, ('a', 'b'), M, 'order')[0] == [(0, 3, 'r')]
      and nearest.nearest(items, ('a', 'b'), M, 'refuse') == ([], [(0, 3, 'r'), (0, 3, 's')])
      and nearest.nearest(items, ('a',), M, 'refuse')[0] == [])
check("nearest: one candidate stands under every tie, and none gives none",
      all(nearest.nearest([(0, 0, 'x')], ('a',), M, t)[0] == [(0, 0, 'x')] for t in nearest.TIES)
      and nearest.nearest([], ('a',), M, 'both') == ([], []))
check("tied: both — all, in their order; order — the first; refuse — none of two or more",
      nearest.tied(['x', 'y'], 'both') == ['x', 'y'] and nearest.tied(['x', 'y'], 'order') == ['x']
      and nearest.tied(['x', 'y'], 'refuse') == [] and nearest.tied(['x'], 'refuse') == ['x'])
check("use: each use's keys and tie read from the law's row",
      nearest.use(LINES, 'flows') == (('as',), 'both') and nearest.use(LINES, 'patterns') == (('literal', 'slots'), 'order')
      and nearest.use(LINES, 'wholes') == (('way',), 'both') and nearest.use(LINES, 'locations') == (('length',), 'order'))

# ---- THE LAW'S CHECK of the rows
check("the released rows hold: every use of the code has its row, each key its use's, each tie one of the three",
      nearest.problems(LINES) == [], nearest.problems(LINES))
bad = {
    'a use the code has none of': lambda d: d['nearest']['uses'].append({'use': 'elsewhere', 'keys': [{'key': 'as'}],
                                                                         'tie': 'both'}),
    'a key its use has not': lambda d: d['nearest']['uses'][0].__setitem__('keys', [{'key': 'length'}]),
    'a key twice': lambda d: d['nearest']['uses'][1].__setitem__('keys', [{'key': 'slots'}, {'key': 'slots'}]),
    'a tie of no meaning': lambda d: d['nearest']['uses'][2].__setitem__('tie', 'random'),
    'a use with no row': lambda d: d['nearest']['uses'].pop(3),
    'a tie the list lacks': lambda d: d['nearest']['ties'].pop(0),
    'no table': lambda d: d.pop('nearest'),
}
missed = []
for what, change in bad.items():
    d = copy.deepcopy(LINES)
    change(d)
    if not nearest.problems(d):
        missed.append(what)
check("...and each wrong row is refused: " + ', '.join(bad), not missed, missed)
L = Law.load()
check("the law's own check runs it: `core/check.py --law` reads no problem of the nearest in the released law",
      not [p for p in L.problems() if 'nearest' in p[1]], [p for p in L.problems() if 'nearest' in p[1]])

# ---- THE FLOWS: the rows a pass meets
pass_ = ('world', 'estate', 'record', 'read')          # world-read, a row that names `as`, grants it
check("flows, as released: a pass the nearest row grants is granted", L.decide(*pass_)[:2] == (True, 'granted'),
      L.decide(*pass_))
twin = {'flow': 'twin', 'from': 'world', 'to': 'estate', 'through': 'record', 'as': 'read', 'grant': 'refused',
        'why': 'a row as near that refuses'}
wide = {'flow': 'wide', 'from': 'world', 'to': 'estate', 'through': 'record', 'grant': 'refused',
        'why': 'a row that names only layers, farther'}


def flows_with(tie, *rows):
    L2 = copy.copy(L)
    L2.flows = list(L.flows) + list(rows)
    L2.line_law = lines_with('flows', tie=tie)
    return L2


d = flows_with('both', twin).decide(*pass_)
check("flows, both: two rows as near stand together, and the one that refuses refuses the pass, naming both",
      d[0] is False and d[1] == 'refused' and d[2] == ['world-read', 'twin'], d)
check("flows, both: a farther row that refuses does not decide where a nearer one grants",
      flows_with('both', wide).decide(*pass_)[:2] == (True, 'granted'))
check("flows, order: of two as near, the first in the table decides",
      flows_with('order', twin).decide(*pass_)[:3] == (True, 'granted', ['world-read']))
d = flows_with('refuse', twin).decide(*pass_)
check("flows, refuse: two as near decide nothing, and the pass is refused, naming both",
      d[:2] == (False, 'refused') and d[2] == ['world-read', 'twin'], d)
check("flows, refuse: one nearest row still decides alone", flows_with('refuse').decide(*pass_)[:2] == (True, 'granted'))

# ---- THE PATTERNS: the rows a name fits
schemes = [('mine', [{'code': 'one', 'template': 'IMG_{counter:4}.JPG'}, {'code': 'two', 'template': 'IMG_{counter:4}.JPG'},
                     {'code': 'loose', 'template': '{text}.JPG'}])]
names = [('a', 'IMG_0001.JPG', 'f'), ('b', 'IMG_0002.JPG', 'f'), ('c', 'notes.JPG', 'f')]


def codes(tie, keys=None):
    rows = groupings.rows_of(schemes, SLOTS, SYSTEMS, lines_with('patterns', tie=tie, keys=keys))
    gs = groupings.fit(names, rows, SYSTEMS)
    return sorted((g['code'] or 'mined', tuple(sorted(g['members']))) for g in gs)


check("patterns, as released: a name by the most specific row it fits, and of two as near the first read",
      codes(None) == [('mine:loose', ('c',)), ('mine:one', ('a', 'b'))], codes(None))
check("patterns, both: a name that fits two rows as near is in each row's group",
      codes('both') == [('mine:loose', ('c',)), ('mine:one', ('a', 'b')), ('mine:two', ('a', 'b'))], codes('both'))
check("patterns, refuse: a name two rows as near fit is by neither, nor by a farther row, and is mined with its shape",
      codes('refuse') == [('mine:loose', ('c',)), ('mined', ('a', 'b'))], codes('refuse'))
rows = groupings.rows_of(schemes, SLOTS, SYSTEMS, lines_with('patterns', keys=['slots', 'literal']))
check("patterns: the keys in the law's order rank the rows — fewer slots first, then more literal characters",
      [r.code for r in rows] == ['one', 'two', 'loose'] and rows.tie == 'order',
      [(r.code, r.near) for r in rows])
check("patterns: the one fitting, read by the store's grouping as by `fit` (bin/group.py `fits`)",
      [h[0].code for h in groupings.fitting(groupings.rows_of(schemes, SLOTS, SYSTEMS, lines_with('patterns', 'both')),
                                            'IMG_0003.JPG', lambda r: True)] == ['one', 'two'])

# ---- THE WHOLES: what a member inherits
said = {'w1': ['work:a'], 'w2': ['work:b'], 'top': ['work:c']}
wholes = {'m': ['w1', 'w2'], 'w1': ['top'], 'n': ['mid'], 'mid': ['top']}


def inh(b, tie):
    return groupings.inherit(b, said.get, wholes.get, lambda x: [], lambda x: False, scheme='work', tie=tie)


check("wholes, as released (both): a member held by two wholes that hold codes holds both, and none beyond them",
      sorted(x[0] for x in inh('m', nearest.use(LINES, 'wholes')[1])) == ['work:a', 'work:b'], inh('m', 'both'))
check("wholes, order: the first whole met stands", [x[0] for x in inh('m', 'order')] == ['work:a'], inh('m', 'order'))
check("wholes, refuse: two wholes as near give nothing inherited",
      not any(x[1] == 'inherited' for x in inh('m', 'refuse')), inh('m', 'refuse'))
check("wholes: one whole on the way is the nearest under every tie, the walk going no further past it",
      all(inh('n', t) == [('work:c', 'inherited', 'top')] for t in nearest.TIES), inh('n', 'refuse'))

# ---- THE LOCATIONS: the bean that covers a path
import cursor  # noqa: E402
from core import engine  # noqa: E402


class _B:
    def __init__(self, bid, at):
        self.id, self.header = bid, {}
        self.items = [(0, 'be', {'id': 'here', 'by': 'self', 'at': at, 'as': 'location'})]


G = engine.Garden({'short': _B('short', '/srv/x'), 'one': _B('one', '/srv/x/y'), 'two': _B('two', '/srv/x/y')})
_was = cursor.dmstale.resolve_here
cursor.dmstale.resolve_here = lambda p: p if isinstance(p, str) and p.startswith('/') else None
try:
    got = {t: cursor.core_resolve('/srv/x/y/z', G, lines_with('locations', tie=t))[0] for t in nearest.TIES}
    as_released = cursor.core_resolve('/srv/x/y/z', G)[0]
finally:
    cursor.dmstale.resolve_here = _was
check("locations: the longest position covering a path; of two as long, as the tie says — the first in the garden's "
      "order (as released), or none where the law says refuse",
      as_released == 'one' and got == {'order': 'one', 'both': 'one', 'refuse': None}, (as_released, got))

print()
print(f"core_nearest: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
