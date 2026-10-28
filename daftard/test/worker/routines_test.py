#!/usr/bin/env python3
"""The worker's routines: `routines_tick` (bin/routines.py tick, with what it did), `probe_round` (each tool the garden
places on this machine probed on its catalogue's cadence, never faster than daftard's floor; a tool that gives no
readings said, its last document kept) and `routines_cross` (the crossings read against the readings daftard keeps,
never a path that is not a kept document) — and a release without bin/routines.py off, said once.

    python3 test/worker/routines_test.py
"""
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
part = src[src.index('def _routines_tool('):src.index('def pending(params):')]
T = Path(tempfile.mkdtemp(prefix='worker-routines-'))
FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-800:]))
    if not cond:
        FAILS.append(name)


def load(root):
    ns = {'re': re, 'json': json, 'subprocess': subprocess, 'sys': sys, 'time': time, 'Path': Path, 'ROOT': root,
          'SLUG': re.compile(r'[a-z0-9][a-z0-9-]{0,120}')}
    exec(compile(part, 'garden_worker.py', 'exec'), ns)
    return ns


try:
    # an older release: no bin/routines.py
    old = T / 'old'
    (old / 'bin').mkdir(parents=True)
    ns = load(old)
    got = ns['routines_tick']({})
    check("a release without bin/routines.py is off, said once", got.get('state') == 'off' and 'bin/routines.py' in got.get('why', ''), got)

    g = T / 'garden'
    (g / 'bin').mkdir(parents=True)
    tools = T / 'tools'
    tools.mkdir()
    count = T / 'probed'
    (tools / 'fastctl.py').write_text(f'''import json, sys
if sys.argv[1:3] == ['probe', '--list']:
    print(json.dumps({{'catalogue': [{{'key': 'a.b', 'cadence': 60}}, {{'key': 'a.c', 'cadence': 'on-change'}}]}})); sys.exit(0)
open({str(count)!r}, 'a').write('x')
print(json.dumps({{'tool': 'fastctl', 'readings': [{{'key': 'a.b', 'value': {{'count': '3', 'unit': '{{item}}'}}}}]}}))
''', encoding='utf-8')
    (tools / 'mutectl.py').write_text('import sys\nprint("not a document")\nsys.exit(2)\n', encoding='utf-8')
    asked = T / 'asked.json'
    (g / 'bin' / 'routines.py').write_text(f'''import json, sys
open({str(asked)!r}, 'a').write(json.dumps(sys.argv[1:]) + "\\n")
if sys.argv[1] == 'tick':
    print(json.dumps([{{'routine': 'server-a#restart-window', 'did': 'started', 'course': 'c', 'stopped': 'waits'}}]))
elif sys.argv[1] == 'tools':
    print(json.dumps([{{'tool': 'fastctl', 'path': {str(tools / 'fastctl.py')!r}}},
                      {{'tool': 'mutectl', 'path': {str(tools / 'mutectl.py')!r}}},
                      {{'tool': '../evil', 'path': '/bin/true'}}]))
elif sys.argv[1] == 'cross':
    print(json.dumps([{{'bean': 'nas-a', 'need': 'below-gate', 'holds': False, 'files': sys.argv[2:]}}]))
''', encoding='utf-8')
    ns = load(g)

    got = ns['routines_tick']({})
    check("routines_tick: bin/routines.py tick --json, its document carried as what was done",
          got.get('state') == 'ran' and got['done'][0]['stopped'] == 'waits'
          and json.loads(asked.read_text().splitlines()[-1]) == ['tick', '--json'], got)

    d = T / 'state'
    d.mkdir()
    got = ns['probe_round']({'dir': str(d), 'every': 30})
    check("probe_round: each tool here probed, its document returned; a tool that gives no readings said; a name that "
          "is no bean id never run", got['read'] == ['fastctl'] and got['tools']['fastctl']['readings'][0]['key'] == 'a.b'
          and 'mutectl' in got['why'] and '../evil' not in json.dumps(got), got)
    (d / 'fastctl.json').write_text(json.dumps(got['tools']['fastctl']), encoding='utf-8')   # what daftard keeps
    got2 = ns['probe_round']({'dir': str(d), 'every': 30})
    check("probe_round: within its cadence (its catalogue's fastest, 60 s) a tool is not probed again; its last document stands",
          got2['read'] == [] and count.read_text() == 'x' and 'fastctl' in got2['tools'], got2)
    old_t = time.time() - 61
    os.utime(d / 'fastctl.json', (old_t, old_t))
    got3 = ns['probe_round']({'dir': str(d), 'every': 30})
    check("probe_round: past its cadence it is probed again", got3['read'] == ['fastctl'] and count.read_text() == 'xx', got3)

    (d / '.fastctl.list.json').write_text('{}', encoding='utf-8')
    got = ns['routines_cross']({'readings': [str(d / 'fastctl.json'), str(d / '.fastctl.list.json'), '/etc/passwd',
                                             str(d / 'missing.json')]})
    check("routines_cross: bin/routines.py cross with the kept documents only — never a dotfile, a path that is no "
          "document or one that does not exist", got['done'][0]['files'] == ['--json', '--readings', str(d / 'fastctl.json')], got)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nworker routines: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
