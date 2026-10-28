#!/usr/bin/env python3
"""The worker's `core_sync`: a garden of the core kept in step by its own bin/sync.py, fast-forwards only where nobody makes a merge,
a merge made by the machine as its host (signed with its own key) or by a person at a sitting, and each peer's
line read into the state the handplace shows — off, current, pulled, merged, diverged, refused, busy, dirty.

    python3 test/worker/sync_test.py

The garden's tool is played here by a stand-in that prints what bin/sync.py prints (its own suite, in the daftar
repository, proves what it does); what is under test is that daftard runs it with `--ff-only` and reads it rightly.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, '..', '..', 'python', 'garden_worker.py'), encoding='utf-8').read()
start = src.index("SYNC_LINE = re.compile(")
end = src.index('def exchange_round(')
T = Path(tempfile.mkdtemp(prefix='worker-sync-'))


def git(*args):
    return subprocess.run(['git', *args], cwd=T, capture_output=True, text=True, encoding='utf-8',
                          errors='replace').stdout.strip()


ns = {'re': re, 'subprocess': subprocess, 'sys': sys, 'ROOT': T, 'git': git}
exec(compile(src[start:end], 'garden_worker.py', 'exec'), ns)   # the part under test, in a garden that stands in
core_sync = ns['core_sync']

STAND_IN = '''import os, subprocess, sys
s = os.environ['SCENARIO']
want = ['--by', 'box'] if s == 'machine' else ['--by', 'ada'] if s in ('merge', 'conflict') else ['--ff-only']
assert sys.argv[1:] == want, 'the loop takes fast-forwards only; a person merges, by name: ' + repr(sys.argv[1:])
if s in ('merge', 'machine'):
    subprocess.run(['git', 'commit', '-q', '--allow-empty', '-m', "merged other's 2 commit(s)"], check=True)
if s == 'pull':
    subprocess.run(['git', 'commit', '-q', '--allow-empty', '-m', 'from a peer'], check=True)
lines = {'current': ['sync: peer: in step'], 'machine': ['sync: other: merged 2 commit(s), each judged first'], 'merge': ['sync: other: merged 2 commit(s), each judged first'], 'pull': ['sync: peer: merged 1 commit(s), a fast-forward — each judged first'],
         'diverged': ['sync: peer: in step', 'sync: other: diverged — its 2 commit(s) are judged and good'],
         'refused': ['sync: peer: REFUSED, nothing merged —', '  abc: not signed'],
         'conflict': ["sync: other: the merge stops on a conflict, taken back whole — a person's to settle (class J)"],
         'busy': [], 'dirty': []}[s]
print('\\n'.join(lines))
if s == 'busy':
    print('sync: a save holds this clone — it waits; nothing was fetched into it', file=sys.stderr)
if s == 'dirty':
    print('sync: this working tree has changes not yet saved — it waits; nothing was fetched into it', file=sys.stderr)
sys.exit(0 if s in ('current', 'pull', 'merge', 'machine') else 1)
'''
try:
    for cmd in (['init', '-q'], ['config', 'user.name', 't'], ['config', 'user.email', 't@x'],
                ['commit', '-q', '--allow-empty', '-m', 'first']):
        git(*cmd)
    got = core_sync()
    assert got == {'state': 'off'}, ('a garden whose release carries no sync tool is off', got)
    (T / 'bin').mkdir()
    (T / 'bin' / 'sync.py').write_text(STAND_IN, encoding='utf-8')
    got = core_sync()
    assert got == {'state': 'off'}, ('a garden with no peer is off', got)
    git('remote', 'add', 'peer', str(T))
    want = {'current': 'current', 'pull': 'pulled', 'diverged': 'diverged', 'refused': 'refused', 'busy': 'busy',
            'dirty': 'dirty'}
    for scenario, state in want.items():
        os.environ['SCENARIO'] = scenario
        got = core_sync()
        assert got['state'] == state, (scenario, got)
    os.environ['SCENARIO'] = 'pull'
    got = core_sync()
    assert got['pulled'] == 1 and got['peers'] == {'peer': 'merged 1 commit(s), a fast-forward — each judged first'} \
        and got['restart'] is False, got
    os.environ['SCENARIO'] = 'diverged'
    got = core_sync()
    assert got['peers']['other'].startswith('diverged') and got['peers']['peer'] == 'in step', got
    os.environ['SCENARIO'] = 'merge'
    got = core_sync(by='ada')
    assert got['state'] == 'merged' and got['pulled'] == 1 and got['peers']['other'].startswith('merged'), got
    os.environ['SCENARIO'] = 'machine'
    got = core_sync(by='box')
    assert got['state'] == 'merged', ('the machine merges what needs no person, as its host', got)
    os.environ['SCENARIO'] = 'conflict'
    got = core_sync(by='ada')
    assert got['state'] == 'diverged', ('a merge that stops on a conflict is still diverged: a person settles it', got)
    print('PASS: worker core_sync — the garden\'s own sync; a merge the machine\'s or a person\'s, never nobody\'s; each peer read into the state shown')
finally:
    shutil.rmtree(T, ignore_errors=True)
