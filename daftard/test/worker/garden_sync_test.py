#!/usr/bin/env python3
"""A dashboard garden's own hub step is its dashboard/sync.py, whatever else of that name the garden holds.

A garden that carries its own handplace code is synced by that code (garden_worker.py: `sync_step`, the garden's
dashboard/sync.py). Upgraded to a release of the core, the same garden also holds the release's bin/sync.py — another
tool, of the same name — and its own dashboard/model.py, imported first, puts bin/ at the head of the import path. Found
on a garden's upgrade (2026-10-14): the worker's `import sync` took bin/sync.py, and every hub step failed with "module
'sync' has no attribute 'Busy'". Here a stand-in garden of that shape asks the worker for a hub step:

  its own     the step is the dashboard's: its answer, not an error, though bin/sync.py is there and bin/ leads the path
  busy        the dashboard's own Busy is the one the worker catches: a step it refuses as busy says `busy`

    python3 test/worker/garden_sync_test.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, '..', '..', 'python', 'garden_worker.py')
FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


MODEL = '''import sys, threading
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / 'bin'))     # as a dashboard's own model does: the garden's bin/ first
class xc:
    class Busy(Exception):
        pass
dmsafe = None
LOCK = threading.RLock()
class Refused(ValueError):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status
'''
DASHBOARD_SYNC = '''import os
class Busy(Exception):
    pass
def step():
    if os.environ.get('SYNC_BUSY'):
        raise Busy()
    return {'state': 'current', 'by': 'the dashboard'}
'''
RELEASE_SYNC = '''"""a release's own sync tool, another of the same name: no hub step of a dashboard's"""
def main():
    raise SystemExit('not a dashboard step')
'''


def ask(root, env_extra=None):
    env = dict(os.environ, DAFTAR_KIND='dashboard', PYTHONUTF8='1', **(env_extra or {}))
    r = subprocess.run([sys.executable, WORKER], cwd=root, input=json.dumps({'id': 1, 'method': 'sync_step', 'params': {}}) + '\n',
                       capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
    for line in r.stdout.splitlines():
        try:
            return json.loads(line), r.stderr
        except ValueError:
            continue
    return {}, r.stdout[-800:] + r.stderr[-1500:]


T = Path(tempfile.mkdtemp(prefix='worker-garden-sync-'))
try:
    for rel, text in (('dashboard/model.py', MODEL), ('dashboard/sync.py', DASHBOARD_SYNC), ('bin/sync.py', RELEASE_SYNC)):
        p = T / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')
    (T / 'exchange').mkdir()
    got, err = ask(T)
    check("its own: the hub step is the dashboard's own, though the release's bin/sync.py is there and bin/ leads the "
          "import path", got.get('ok') and (got.get('result') or {}).get('by') == 'the dashboard', (got, err))
    got, err = ask(T, {'SYNC_BUSY': '1'})
    check("busy: the dashboard's own Busy is the one caught, and the step says `busy`",
          got.get('ok') and (got.get('result') or {}).get('state') == 'busy', (got, err))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ngarden_sync_test: {len(FAILS)} failed" + (': ' + ', '.join(FAILS) if FAILS else ''))
sys.exit(1 if FAILS else 0)
