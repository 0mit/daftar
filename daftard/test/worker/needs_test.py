#!/usr/bin/env python3
"""The worker's leads of what waits (core 3.7: what waits is a need on the bean it concerns): each need not met, as
the garden's own bin/waiting.py reads it, is a decision whose landing is `<bean>.<need>`, beside log/pending.md's
entries still proposed; a garden of a core before 3.7, which carries no bin/waiting.py, has the queue's entries alone;
the view the release writes of the needs (`## <bean>#<need> · …`) is never read as an entry of its own.

    python3 test/worker/needs_test.py
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', '..', 'python', 'garden_worker.py'), encoding='utf-8').read()
part = src[src.index('PENDING = ROOT /'):src.index('def release_leads(')]
T = Path(tempfile.mkdtemp(prefix='worker-needs-'))
try:
    (T / 'log').mkdir()
    (T / 'log' / 'pending.md').write_text(
        '# What waits\n\n'
        '## roof#ratify-it · the roof, to ratify · waits\n- class: G\n\n'
        '## queued-one · a decision still in the queue · proposed 2026-10-01 by sam\n- class: D\n- status: proposed\n\n'
        '## closed-one · a decision taken · proposed 2026-09-01 by sam\n- status: proposed\n- status: done\n',
        encoding='utf-8')

    def worker():
        ns = {'ROOT': T, 'hashlib': hashlib, 'json': json, 'os': os, 're': re, 'subprocess': subprocess, 'sys': sys,
              'time': time, 'Path': Path, 'exchange_folder': lambda: None, 'release_leads': lambda: [],
              'form_leads': lambda: [], 'passkey_leads': lambda: []}
        exec(compile(part, 'garden_worker.py', 'exec'), ns)
        return ns

    ns = worker()
    assert ns['waiting_needs']() is None
    got = ns['leads']({})
    assert [(x['kind'], x['id']) for x in got] == [('pending', 'queued-one')], got
    print('PASS: worker needs — a garden before core 3.7: the queue\'s entries still proposed, and nothing else')

    (T / 'bin').mkdir()
    said = [
        {'about': 'roof', 'need': 'ratify-it', 'what': 'the roof, to ratify', 'whose': ['ana'], 'for': ['ana', 'ben'],
         'class': 'G', 'strength': 'blocks', 'blocked_by': [], 'title': 'the roof'},
        {'about': 'roof', 'need': 'after-it', 'what': 'after the roof', 'whose': ['ana'], 'for': ['ana'], 'class': '',
         'strength': 'contingent', 'blocked_by': ['roof#ratify-it'], 'title': 'the roof'},
        {'about': '../etc', 'need': 'x', 'what': 'no bean id'},
        {'about': 'roof', 'need': 'a.b', 'what': 'no need id a landing can name'},
    ]
    (T / 'bin' / 'waiting.py').write_text('import json\nprint(json.dumps(' + repr(said) + '))\n', encoding='utf-8')
    ns = worker()
    got = ns['leads']({})
    assert [(x['kind'], x['id']) for x in got] == [('pending', 'queued-one'), ('pending', 'roof.ratify-it'),
                                                   ('pending', 'roof.after-it')], got
    need = got[1]
    assert (need['title'], need['class'], need['for'], need['about'], need['strength']) == \
        ('the roof, to ratify', 'G', 'ana, ben', 'roof', 'blocks'), need
    assert got[2]['blocked_by'] == ['roof#ratify-it'], got[2]
    assert all(ns['NEED_LEAD'].fullmatch(x['id']) for x in got[1:]) and not ns['NEED_LEAD'].fullmatch('queued-one')
    print('PASS: worker needs — each need not met is a decision landing at <bean>.<need>, whose and how badly; '
          'the view\'s entries are not read twice; what no landing can name is left out')

    (T / 'bin' / 'waiting.py').write_text('raise SystemExit("the law could not be read")\n', encoding='utf-8')
    ns = worker()
    assert ns['waiting_needs']() == [] and [x['id'] for x in ns['leads']({})] == ['queued-one']
    print('PASS: worker needs — a reading that fails shows no need, and the queue\'s entries still')
finally:
    shutil.rmtree(T, ignore_errors=True)
