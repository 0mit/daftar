#!/usr/bin/env python3
"""core_readings — the rules as readings (core 3.0, the next version's design, P4): order, life and necessity stated in the
law's reading grammar, read by the one reckoner (core/reckon.py), their code gone from core/engine.py.

C1: each rule names its reading, and a copy of the law without that reading lets the rule's refusal cases of
test/core-cases.yaml pass and changes no other case. C6: each refusal carries the statements and the law's rows it
rests on, and `daftar why <rule> <place>` prints them. Beside them: the grammar's new operations, each by its test
vectors (join of two sets, cycle, reach, first, last, describe, an input said by the law); a rule's reading checked
against the grammar; the reckoner's old path; and a law older than 3.0, which this engine refuses to judge. Invented
beings; nothing here is a fact. (`python` on Windows.)"""
import copy
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
import yaml  # noqa: E402
from core import engine, lines, read, reckon  # noqa: E402
from core.law import Law  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=''):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
READ = ('order', 'life', 'necessity')                     # the rules core 3.0 states as readings


def bean(bid, kind, statements, header=None):
    h = {'bean': bid, 'kind': kind, 'title': bid, 'statements': statements}
    h.update(header or {})
    return engine.Bean(bid, header=h)


def garden(extra=()):
    beans = {bid: bean(bid, b['kind'], b['statements']) for bid, b in CASES['garden'].items()}
    for b in extra:
        beans[b.id] = b
    return engine.Garden(beans, CASES['zone'], files=['VOCAB.md', 'GARDEN.md', 'log/journal.md'],
                         manifest={'gardener': 'sam'})


def judged(law, extra=()):
    return engine.Judge(law, garden(extra)).run()


CASED = [('garden', None, [])] + [(f"{k} {c.get('rule', '')} {c['bean']}".replace('  ', ' '), c,
                                   [bean(c['bean'], c['kind'], c['statements'], c.get('header'))])
                                  for k in ('good', 'bad', 'disk') for c in CASES[k]]

# ------------------------------------------------------------------------------------------------ each rule its reading
check(f"each of {', '.join(READ)} names its reading in the law, and the law proves it in the grammar of every reading",
      all(r in LAW.readings for r in READ) and not [p for p in LAW.problems() if p[1] == 'core.yaml'],
      (sorted(LAW.readings), [p for p in LAW.problems() if p[1] == 'core.yaml']))
check("...and no code of theirs is left in core/engine.py: no rule is stated twice",
      not any(hasattr(engine.Judge, m) for m in ('order', 'life', 'cycles', 'necessity_and_squares')),
      [m for m in ('order', 'life', 'cycles', 'necessity_and_squares') if hasattr(engine.Judge, m)])
check("...and each `says` stays, the rule's reason, beside its reading",
      all(isinstance(r.get('says'), str) and r.get('reading') for r in read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['rules']
          if r['rule'] in READ))

# ------------------------------------------------------------------------------------------------ C1: the law without one
base = {name: judged(LAW, extra) for name, _c, extra in CASED}
for rule in READ:
    bare = copy.copy(LAW)
    bare.readings = {k: v for k, v in LAW.readings.items() if k != rule}
    mine = [name for name, c, _e in CASED if c is not None and c.get('rule') == rule and name.startswith('bad')]
    let, changed = [], []
    for name, c, extra in CASED:
        got = judged(bare, extra)
        if name in mine:              # refused by the rule no more, and by nothing else than before
            if got != [f for f in base[name] if f[0] != rule] or not any(f[0] == rule for f in base[name]):
                let.append((name, got))
        elif got != base[name]:
            changed.append((name, [f for f in base[name] if f not in got], [f for f in got if f not in base[name]]))
    check(f"C1 {rule}: the law without its reading lets its {len(mine)} refusal cases pass ({', '.join(m.split()[-1] for m in mine)})",
          mine and not let, let)
    check(f"C1 {rule}: ...and changes no other case of the {len(CASED) - len(mine)}", not changed, changed[:3])

# ------------------------------------------------------------------------------------------------ C6: the proof
def resolves(item, G, law):
    """Whether a proof's item names a statement of the garden, a bean's kind, or a row or a table of the law."""
    m = reckon_place(item)
    if m:
        b = G.beans.get(m[0])
        return b is not None and any(j == m[1] and v == m[2] for j, v, _r in b.items)
    if item.endswith(':kind'):
        return item[:-5] in G.beans
    if item.startswith('law:') and '[' not in item:
        return item[4:] in law.declared_tables() or item[4:] == 'stands'
    return reckon.law_row(law, item) is not None


def reckon_place(item):
    import re
    m = re.match(r'^(.+)\[([0-9]+)\] (\S+)$', item)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else None


bad = [c for c in CASES['bad'] if c['rule'] in READ]
G6 = garden([bean(c['bean'], c['kind'], c['statements'], c.get('header')) for c in bad])
found = [f for f in engine.Judge(LAW, G6).run() if f[0] in READ]
check(f"C6: each of the {len(found)} refusals of {', '.join(READ)} over their bad cases carries a proof, the statement "
      f"it is told at first", found and all(getattr(f, 'proof', ()) and f.proof[0] == f[1] for f in found),
      [f for f in found if not getattr(f, 'proof', ()) or f.proof[0] != f[1]])
check("...and every item of each proof is a statement of the garden, a bean's kind, or a row or a table of the law",
      all(resolves(i, G6, LAW) for f in found for i in f.proof),
      [(f[1], i) for f in found for i in f.proof if not resolves(i, G6, LAW)])
loop = next((f for f in found if f[1] == 'x7[1] stand'), None)
check("...and a stand on itself through the law's ladder rests on the ladder's rows it goes round by",
      loop is not None and sum(1 for i in loop.proof if i.startswith('law:levels[')) >= 2, loop and loop.proof)
x27 = [f for f in found if f[1].startswith('x27[')]
check("...and an own loop rests on both statements that make it",
      len(x27) == 2 and all({'x27[1] own', 'x27[2] own'} <= set(f.proof) for f in x27), [f.proof for f in x27])

T = tempfile.mkdtemp(prefix='core-readings-')
try:
    G = os.path.join(T, 'g')
    os.makedirs(os.path.join(G, 'beans'))
    with open(os.path.join(G, 'GARDEN.md'), 'w', encoding='utf-8') as fh:
        fh.write('---\n' + yaml.safe_dump({'garden': 'readings', 'extends': f"core@{LAW.version}", 'gardener': 'sam',
                                          'zone': CASES['zone']}, sort_keys=False) + '---\n')
    with open(os.path.join(G, 'VOCAB.md'), 'w', encoding='utf-8') as fh:
        fh.write('---\n' + yaml.safe_dump(CASES['vocab'], allow_unicode=True, sort_keys=False, width=200) + '---\n')
    for bid, c in list(CASES['garden'].items()) + [(c['bean'], c) for c in bad]:
        h = {'bean': bid, 'kind': c['kind'], 'title': bid, 'statements': c['statements']}
        with open(os.path.join(G, 'beans', f"{bid}.md"), 'w', encoding='utf-8') as fh:
            fh.write('---\n' + yaml.safe_dump(h, allow_unicode=True, sort_keys=False, width=200) + '---\n\nWords.\n')
    on_disk = [f for f in engine.Judge(LAW, engine.Garden._fresh(G)).run() if f[0] in READ]
    check("C6: the garden written as files is refused alike", sorted(on_disk) == sorted(found),
          (sorted(set(on_disk) ^ set(found)))[:4])
    shown = []
    for f in on_disk:
        r = subprocess.run([PY, os.path.join(ROOT, 'bin', 'daftar.py'), 'why', f[0], f[1], '--garden', G],
                           capture_output=True, text=True, encoding='utf-8', errors='replace')
        out = r.stdout + r.stderr
        if r.returncode != 0 or f[2] not in out or not all(f"    {i}:" in out for i in f.proof) or 'the rule: ' not in out:
            shown.append((f[0], f[1], r.returncode, out[-600:]))
    check(f"C6: `daftar why <rule> <place>` prints each of the {len(on_disk)} refusals, every statement and row of the "
          f"law it rests on, and the rule's reason", on_disk and not shown, shown[:2])
    r = subprocess.run([PY, os.path.join(ROOT, 'bin', 'why.py'), 'order', 'ada[0] say', '--garden', G],
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    check("...and says so, exit 1, where the rule refuses nothing at the place", r.returncode == 1 and 'refuses nothing' in r.stdout,
          r.stdout + r.stderr)
finally:
    shutil.rmtree(T, ignore_errors=True)


# ------------------------------------------------------------------------------------------------ the operations' vectors
def reading(statements, steps, inputs=()):
    """The members of each step of a reading over a garden of one bean `v` holding `statements`, read as a rule's is."""
    b = engine.Bean('v', header={'bean': 'v', 'kind': 'host', 'title': 'v', 'statements': statements})
    w = engine.Bean('w', header={'bean': 'w', 'kind': 'person', 'title': 'w', 'statements': [{'say': {'by': 'w', 'at': 'now'}}]})
    J = engine.Judge(LAW, engine.Garden({'v': b, 'w': w}, CASES['zone'], manifest={'gardener': 'w'}))
    rk = reckon.Reckoner(reckon.Judged(J), rules_law=LAW)
    rk.run(lines.worded({'inputs': [{'name': n, 'origin': {'act': 'say', 'nature': 'sayable', 'by': 'law'}} for n in inputs],
                         'steps': steps}))
    return rk.env


SAY = {'say': {'by': 'w', 'at': 'now'}}
env = reading([SAY, {'need': {'by': 'self', 'of': 'w'}}, {'need': {'by': 'w', 'of': 'v'}}, {'own': {'by': 'w', 'of': 'self'}}],
              [{'id': 'n', 'op': 'select', 'entries': 'need'}, {'id': 'o', 'op': 'select', 'entries': 'own'},
               {'id': 'both', 'op': 'join', 'of': 'n', 'with': 'o', 'on': {'by': 'of'}, 'keep': 'both', 'as': ['x', 'y']},
               {'id': 'm', 'op': 'join', 'of': 'n', 'with': 'o', 'on': {'by': 'of'}, 'keep': 'matched'},
               {'id': 'u', 'op': 'join', 'of': 'n', 'with': 'o', 'on': {'by': 'of'}, 'keep': 'unmatched'}])
check("join of two sets: `self` read as its bean — the need by v pairs with the own of v, kept both, matched, unmatched",
      [m.place for m in env['both']] == ['v[1] need'] and env['both'][0].node['y'].get('by') == 'w'
      and [m.place for m in env['m']] == ['v[1] need'] and [m.place for m in env['u']] == ['v[2] need']
      and env['m'][0].proof == ('v[1] need', 'v[3] own'), [(m.place, m.proof) for k in ('both', 'm', 'u') for m in env[k]])
env = reading([SAY, {'need': {'by': 'self', 'of': 'w'}}, {'need': {'by': 'w', 'of': 'v'}}, {'need': {'by': 'w', 'of': 'w'}}],
              [{'id': 'n', 'op': 'select', 'entries': 'need'}, {'id': 'b', 'op': 'select'},
               {'id': 'c', 'op': 'cycle', 'of': 'n', 'from': 'by', 'to': 'of', 'within': 'b'}])
got = sorted((m.node['start'], m.node['next'], tuple(m.node['way']), tuple(m.node['loop'])) for m in env['c'])
check("cycle: each edge on a loop, with its way back and the loop whole; an edge to itself is its own loop",
      got == [('v', 'w', ('w',), ('v', 'w', 'v')), ('w', 'v', ('v',), ('w', 'v', 'w')), ('w', 'w', ('w',), ('w', 'w'))], got)
env = reading([SAY, {'part': {'by': 'self', 'of': 'w'}}],
              [{'id': 'p', 'op': 'select', 'entries': 'part'},
               {'id': 'mo', 'op': 'select', 'of': 'stands', 'where': [{'path': 'as', '=': 'made-of'}]},
               {'id': 'r', 'op': 'reach', 'of': 'p', 'at': 'of', 'through': 'mo', 'from': 'by', 'to': 'at'},
               {'id': 'org', 'op': 'reach', 'of': 'mo', 'at': 'by', 'through': 'mo', 'from': 'by', 'to': 'at'}], ('stands',))
reached = {(m.node['start'], m.node['reached']) for m in env['org']}
check("reach: a start reaches itself and what the ladder's made-of leads to — an organism its cells and atoms, never what it is possible on",
      ('organism', 'organism') in reached and ('organism', 'cell') in reached and ('organism', 'atom') in reached
      and ('organism', 'reason') not in reached and ('w', 'w') in {(m.node['start'], m.node['reached']) for m in env['r']},
      sorted(reached)[:6])
env = reading([SAY, {'need': {'by': 'self', 'of': 'w', 'note': 'one'}}, {'need': {'by': 'self', 'of': 'w', 'note': 'two'}},
               {'need': {'by': 'w', 'of': 'v'}}],
              [{'id': 'n', 'op': 'select', 'entries': 'need'},
               {'id': 'f', 'op': 'first', 'of': 'n', 'by': ['by', 'of']}, {'id': 'l', 'op': 'last', 'of': 'n', 'by': ['by', 'of']},
               {'id': 'fv', 'op': 'first', 'of': 'n', 'by': 'by', 'groups': 'values'}])
check("first and last: one member of each group, the first or the last as the garden reads them; `groups: values` "
      "gives the groups in the order of their values",
      [m.place for m in env['f']] == ['v[1] need', 'v[3] need'] and [m.place for m in env['l']] == ['v[2] need', 'v[3] need']
      and [m.node['by'] for m in env['fv']] == ['self', 'w'], [[m.place for m in env[k]] for k in ('f', 'l', 'fv')])
env = reading([SAY, {'come': {'by': 'self', 'through': ['w', {'someone': 'person'}, 'theone', 'no-such']}}],
              [{'id': 'c', 'op': 'select', 'entries': 'come'}, {'id': 'd', 'op': 'describe', 'of': 'c', 'at': 'through', 'as': 'via'}])
cols = [(m.node['via']['kind'], m.node['via']['organisation'], m.node['via']['bios'], m.node['via']['rung'],
         m.node['via']['matter']) for m in env['d']]
check("describe: a member for each being of a list, with its kind and its position on each line of the ladder, a "
      "column a line (core 4.0) — none for the crown or a word",
      cols == [('person', 'organism', 'living', 'reason', None)] * 2 + [(None,) * 5] * 2
      and 'line' not in env['d'][0].node['via']
      and reckon.written('{via} is', env['d'][1]) == 'person is', cols)
check("an input said by the law: its table's rows, each with its proof; one no rule reads is refused by name",
      [m.id for m in reckon.law_table(LAW, 'crown')] == ['law:crown[theone]']
      and isinstance(reckon.law_table(LAW, 'stands')[0].proof[0], str), [m.id for m in reckon.law_table(LAW, 'crown')])
try:
    reckon.law_table(LAW, 'no-such-table')
    check("...", False, 'no refusal')
except reckon.Refused as e:
    check("...and a table the law's columns do not declare is refused, naming those they do",
          "a table the law's columns declare" in str(e) and 'crown' in str(e) and 'verbs' in str(e), e)

# ------------------------------------------------------------------------------------------------ the grammar's check
view = lines.law_view(LAW)
order = LAW.readings['order']
for name, broken, says in (
        ('an input not of the law', dict(order, inputs=[{'name': 'stands', 'origin': {'act': 'say'}}]), 'said by the law'),
        ('a refusal naming no step', dict(order, refuse=[{'of': 'nothing-here', 'message': 'x'}]), 'a refusal is'),
        ('an operation outside the closed list', dict(order, steps=order['steps'] + [{'id': 'g', 'op': 'guess', 'of': 'stand'}]),
         'is not an operation of the law'),
        ('a join of a series and a set at once', dict(order, steps=order['steps'] + [
            {'id': 'j', 'op': 'join', 'of': 'stand', 'series': 'x:series.y', 'with': 'part', 'on': {'by': 'by'}}]), 'two series'),
        ('a step naming a later one', dict(order, steps=[{'id': 'a', 'op': 'cycle', 'of': 'b', 'from': 'by', 'to': 'at'},
                                                          {'id': 'b', 'op': 'select', 'entries': 'stand'}]), 'names no earlier step')):
    got = reckon.check_rule('rules[order].reading', broken, view)
    check(f"a rule's reading is checked as any reading is: {name} is refused", any(says in t for _l, t in got), got)

# ------------------------------------------------------------------------------------------------ the old path, an old law
r = subprocess.run([PY, os.path.join(ROOT, 'bin', 'reckon.py'), '--help'], capture_output=True, text=True, encoding='utf-8')
import reckon as by_old_name  # noqa: E402
check("the reckoner's old path runs it, and `import reckon` is the core's one module",
      r.returncode == 0 and 'the one reckoner' in r.stdout and by_old_name is reckon, (r.returncode, r.stdout[:200]))
old = copy.copy(LAW)
old.version, old.readings = '2.25', {}
got = engine.Judge(old, garden()).run()
check("a law older than 3.0, which holds no rule's reading, is refused by name rather than judged without them",
      [f[:2] for f in got] == [('form', 'core/law/core.yaml')] and 'older than this judge' in got[0][2], got)

print(f"core_readings: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
