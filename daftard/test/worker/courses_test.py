#!/usr/bin/env python3
"""The worker's `courses`: a being's courses as its garden's own release reads them (bin/seq.py `courses`, daftar
2.22), the page a lead of a garden of the core opens — in a real garden grown from a daftar tree: a repair placed on a
walk, at its second step, past the step's usual time; a being on no walk has none; a name that is no bean id is
refused.

    python3 test/worker/courses_test.py [<daftar tree>]     # the tree a garden is grown from (default ~/daftar)
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test

FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-1200:]))
    if not cond:
        FAILS.append(name)


T = Path(tempfile.mkdtemp(prefix='worker-courses-'))
try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam')
    check('a garden grows from the tree', r.returncode == 0, r.out[-600:])
    if 'kind: procedure,' not in (G / 'core' / 'law' / 'kinds.yaml').read_text(encoding='utf-8'):   # the law's since 4.7
        (G / 'VOCAB.md').write_text('---\nkinds:\n  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, '
                                    'step by step: a walk" }\n---\n# the garden\'s own rows\n', encoding='utf-8')
    (G / 'mappings').mkdir(exist_ok=True)
    (G / 'mappings' / 'walk-repair.md').write_text('''---
bean: walk-repair
kind: procedure
title: "walk-repair — how a repair goes"
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "it is brought", to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", to: [mended], walk: { usually: { of: time, measure: { count: "2", unit: d } } } }
  - step: { id: mended, as: "it is mended", walk: { final: "true" } }
---
The steps of a repair.
''', encoding='utf-8')
    (G / 'beans' / 'repair-1.md').write_text('''---
bean: repair-1
kind: design
title: "repair-1 — a bicycle repaired"
summary: "A bicycle on its way back to its owner."
statements:
  - say:  { by: sam, at: now }
  - own:  { by: sam, of: self }
  - be:   { id: repair, by: self, at: walk-repair, as: order }
  - move: { by: sam, of: self, through: repair, at: ["2026-10-01T10:00:00+03:00", "walk-repair#handed-over"] }
  - move: { by: sam, of: self, through: repair, at: ["2026-10-01T11:00:00+03:00", "walk-repair#looked-at"] }
---
A repair.
''', encoding='utf-8')
    src = open(os.path.join(HERE, '..', '..', 'python', 'garden_worker.py'), encoding='utf-8').read()
    part = src[src.index('COURSES = r"""'):src.index('def action(params):')]

    class Refused(Exception):
        pass

    def front(path):
        sys.path.insert(0, str(G / 'bin'))
        import parse
        return parse.loads(parse.split_front_matter(Path(path).read_text(encoding='utf-8'))[0]) or {}
    ns = {'re': re, 'json': json, 'subprocess': subprocess, 'sys': sys, 'ROOT': G, 'Refused': Refused, 'front': front,
          'SLUG': re.compile(r'[a-z0-9][a-z0-9-]{0,120}'), 'title_of': lambda b: str(front(G / 'beans' / f'{b}.md').get('title') or b)}
    exec(compile(src[src.index('_SPACES = []'):src.index('def need_landing(')], 'garden_worker.py', 'exec'), ns)  # bean_file
    exec(compile(part, 'garden_worker.py', 'exec'), ns)
    got = ns['courses']({'id': 'repair-1'})
    c = (got.get('courses') or [{}])[0]
    check("courses: a being's course as its garden's release reads it — its walk's steps in their order, the step it "
          "stands at, overdue past the step's usual time — with its title and summary",
          got['title'].startswith('repair-1') and got['summary'] == 'A bicycle on its way back to its owner.'
          and c.get('walk') == 'walk-repair' and c.get('step') == 'looked-at' and c.get('overdue') is True
          and [s['id'] for s in c.get('steps') or []] == ['handed-over', 'looked-at', 'mended'], got)
    check('...a being on no walk has no course', ns['courses']({'id': 'sam'})['courses'] == [], ns['courses']({'id': 'sam'}))
    try:
        ns['courses']({'id': '../etc'})
        refused = False
    except Refused:
        refused = True
    check('...and a name that is no bean id is refused', refused)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncourses: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
