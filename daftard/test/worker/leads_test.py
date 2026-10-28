#!/usr/bin/env python3
"""The worker's `release_leads`: what the garden's own bin/leads.py reads as waiting, carried to daftard — a case, an
action at ratify, a session, a failure a reading shows (health) and a clause falling due (obligation) — each with whose
it is, and nothing the handplace cannot land on.

    python3 test/worker/leads_test.py
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
src = open(os.path.join(HERE, '..', '..', 'python', 'garden_worker.py'), encoding='utf-8').read()
part = src[src.index('def release_leads('):src.index('ACTION_ID = re.compile(')]
T = Path(tempfile.mkdtemp(prefix='worker-leads-'))
try:
    (T / 'bin').mkdir()
    said = [
        {'for': 'sam', 'kind': 'case', 'about': 'repair-1', 'course': 'repair', 'step': 'looked-at', 'why': 'waits', 'since': '2026-10-01'},
        {'for': 'sam', 'kind': 'case', 'about': 'cert-a', 'course': 'deploy-a', 'step': 'ratify', 'why': 'a plan'},
        {'for': 'kay', 'kind': 'health', 'about': 'box-slow', 'fail': 'clock-drift', 'since': '2026-10-09', 'why': 'box-slow: the clock — read as duration 31 s'},
        {'for': 'ten', 'kind': 'obligation', 'about': 'flat-lease', 'clause': 'rent-due', 'due': '2026-10-12', 'why': 'rent falls due'},
        {'for': 'sam', 'kind': 'decision', 'about': 'rows', 'why': 'read by the queue already'},
        {'for': 'sam', 'kind': 'health', 'about': '../etc', 'why': 'no bean id'},
    ]
    (T / 'bin' / 'leads.py').write_text('import json\nprint(json.dumps(' + repr(said) + '))\n', encoding='utf-8')
    ns = {'re': re, 'json': json, 'subprocess': subprocess, 'sys': sys, 'ROOT': T,
          'SLUG': re.compile(r'[a-z0-9][a-z0-9-]{0,120}')}
    exec(compile(part, 'garden_worker.py', 'exec'), ns)
    got = ns['release_leads']()
    kinds = [(x['kind'], x['id'], x['for']) for x in got]
    assert kinds == [('case', 'repair-1', 'sam'), ('action', 'cert-a.deploy-a', 'sam'), ('health', 'box-slow', 'kay'),
                     ('obligation', 'flat-lease', 'ten')], kinds
    assert got[3]['since'] == '2026-10-12' and 'duration 31 s' in got[2]['title'], got
    print('PASS: worker release_leads — case, action, health and obligation carried with whose each is; '
          'decisions left to the queue; no lead the handplace cannot land on')
finally:
    shutil.rmtree(T, ignore_errors=True)
