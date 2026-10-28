#!/usr/bin/env python3
"""Runs: every job a tool starts, a course on the standard walk, its registry the store `runs` (core 2.11).

Grows a garden of the core from a release made of this tree (test/grow.py), writes the walk into it (`run.py setup`),
and runs bin/run.py there against a registry made for the test:

  setup     the walk written into the garden, the gate passing it; a walk that differs from the standard refused
  start     a run started, waited for, done; its exit code, a signal and a time limit end it as the walk says
  names     a run named by its id or an exact name, never by a prefix; a second run on a held key refused, one queued
            for it started when it is free
  stop      a run stopped, every process it started with it and nothing else; a script kept in its folder, its stdin
            /dev/null so a command inside cannot eat the rest
  tasks     a task that raises ends failed (raised); a task whose process died is lost, by reconcile; child runs
  identity  a run's process held by (boot, pid, start ticks): a pid that names another process is refused
  store     the course and the moves are statements of the being the run acts on, known by the run's own act, its
            columns that being's detail; the store's check over git judges every move against the walk; a reader of
            another user opens it read-only, with read permission alone; the export passes the gate
  writers   runs started at once, each supervisor writing its own moves: every move kept, in order

Run: python3 test/run.py   (0 = green; about a minute). Where the machine gives a run no freezer cgroup, a run is its
own session, as bin/run.py says, and the suite says which it tested.
"""
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='core-run-')
G = os.path.join(T, 'g')
REG = os.path.join(T, 'registry')
ENV = dict(grow.ENV, DAFTAR_RUNS=REG, DAFTAR_RUNS_QUIET='1', DAFTAR_HOST='box-a', DAFTAR_BY='session-t')


def R(*args, timeout=60, env=None, cwd=None):
    return grow.run(PY, 'bin/run.py', *args, cwd=cwd or G, env=env or ENV)


def rid(r):
    out = [l for l in r.stdout.strip().splitlines() if l.startswith('run-')]
    return out[-1].split()[0] if out else None          # a run that ended at once still printed its id


def step(i):
    r = R('show', i, '--json')
    try:
        return json.loads(r.stdout)['step']
    except (ValueError, KeyError):
        return None


def alive(pid):
    try:
        with open(f'/proc/{pid}/stat') as fh:
            return fh.read().split(') ')[1][0] != 'Z'
    except OSError:
        return False


try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam')
    check("a garden of the core grows, and carries run.py", r.returncode == 0 and os.path.isfile(f'{G}/bin/run.py'),
          r.out[-600:])
    with open(f'{G}/beans/session-t.md', 'w', encoding='utf-8') as fh:
        fh.write('---\nbean: session-t\nkind: session\ntitle: "session-t"\nstatements:\n  - make: { by: self, at: now }\n'
                 '---\nA session, invented.\n')
    with open(f'{G}/beans/box-a.md', 'w', encoding='utf-8') as fh:       # the machine the runs run on
        fh.write('---\nbean: box-a\nkind: host\ntitle: "box-a"\nstatements:\n  - say: { by: sam, at: now }\n'
                 '---\nA machine, invented.\n')

    # ---- setup
    r = R('setup', '--by', 'session-t')
    s = grow.run(PY, 'bin/save.py', 'sam', 'the walk of a run', '--body',
                 '- action: wrote [[session-t]], [[box-a]] and [[walk-run]]', cwd=G)
    check("setup: the walk written into the garden's mappings, of the law's kind `procedure` with no row of the "
          "garden's own, and the gate passes it",
          r.returncode == 0 and os.path.isfile(f'{G}/mappings/walk-run.md') and s.returncode == 0
          and 'procedure' not in open(f'{G}/VOCAB.md', encoding='utf-8').read(), r.out + s.out[-600:])
    r = R('setup')
    check("...setup again finds the garden's walk the standard's", r.returncode == 0 and "the standard's" in r.out, r.out)
    w = open(f'{G}/mappings/walk-run.md', encoding='utf-8').read()
    open(f'{G}/mappings/walk-run.md', 'w', encoding='utf-8').write(w.replace('reasons: [asked, timeout]',
                                                                             'reasons: [asked]'))
    r = R('setup')
    check("...a walk that differs from the standard is refused, naming the difference",
          r.returncode != 0 and 'stopped: reasons' in r.out, r.out)
    open(f'{G}/mappings/walk-run.md', 'w', encoding='utf-8').write(w)

    # ---- start
    a = rid(R('start', '--name', 'a sleep', '--', 'sleep', '1'))
    r = R('wait', a or '-', '--timeout', '20')
    check("start: a run started, waited for, done", a and r.returncode == 0 and step(a) == 'done', (a, r.out))
    e = rid(R('start', '--name', 'exits 3', '--', 'sh', '-c', 'exit 3'))
    R('wait', e or '-', '--timeout', '20')
    k = rid(R('start', '--name', 'killed', '--', 'sh', '-c', 'kill -9 $$'))
    R('wait', k or '-', '--timeout', '20')
    tl = rid(R('start', '--name', 'too long', '--timeout', '1', '--grace', '1', '--', 'sleep', '30'))
    R('wait', tl or '-', '--timeout', '30')
    js = {i: json.loads(R('show', i, '--json').stdout) for i in (e, k, tl) if i}
    check("...an exit code, a signal and a time limit end it as the walk says",
          len(js) == 3 and (js[e]['step'], js[e]['reason']) == ('failed', 'exit-code')
          and (js[k]['step'], js[k]['reason']) == ('failed', 'signal')
          and (js[tl]['step'], js[tl]['reason']) == ('stopped', 'timeout'),
          {i: (j['step'], j['reason']) for i, j in js.items()})

    # ---- names and keys
    l1 = rid(R('start', '--name', 'llm-dl', '--', 'sleep', '60'))
    r1 = R('stop', '--name', 'llm')
    r2 = R('stop', (l1 or '-')[:14])
    check("names: a run is named by its id or an exact name, never by a beginning",
          r1.returncode == 4 and r2.returncode == 4 and step(l1) == 'running', (r1.out, r2.out))
    R('stop', l1 or '-', '--why', 'a test')
    h = rid(R('start', '--name', 'holder', '--key', 'test:k', '--', 'sleep', '2'))
    b = R('start', '--name', 'second', '--key', 'test:k', '--', 'true')
    q = rid(R('start', '--name', 'queued', '--key', 'test:k', '--wait-key', '--', 'true'))
    R('wait', q or '-', '--timeout', '30')
    check("...a second run on a held key refused, naming the holder; one queued for it started when it is free",
          b.returncode == 3 and 'holder' in b.out and step(q) == 'done', (b.out, step(q)))

    # ---- stop, a script
    # a length no other process on the machine sleeps for, so the check gathers only this run's own (nb-s3-open 9)
    nap = f"60.{os.getpid() % 1000:03d}"
    tree = rid(R('start', '--name', 'a tree', '--', 'sh', '-c', f'setsid sleep {nap} & sleep {nap} & wait'))
    time.sleep(1)
    kids = [int(p) for p in subprocess.run(['pgrep', '-f', f'^sleep {re.escape(nap)}$'], capture_output=True, text=True,
                                           encoding='utf-8').stdout.split()]
    R('stop', tree or '-', '--why', 'a test', '--grace', '2')
    time.sleep(0.5)
    with open(f'{T}/script.sh', 'w') as fh:
        fh.write('cat >/dev/null\necho second-step\n')
    sc = rid(grow.run(PY, 'bin/run.py', 'start', '--name', 'a script', '--script', '-', cwd=G, env=ENV,
                      stdin=open(f'{T}/script.sh').read()))
    R('wait', sc or '-', '--timeout', '20')
    tail = R('tail', sc or '-').out
    cg = subprocess.run([PY, '-c', f"import sys; sys.path.insert(0, 'bin'); import run; print(run.cgroup_root())"],
                        cwd=G, capture_output=True, text=True, encoding='utf-8', env=ENV).stdout.strip()
    check(f"stop: a run stopped whole — what it started, even in a session of its own — and nothing else "
          f"({'a freezer cgroup' if cg != 'None' else 'its own session: no freezer cgroup here'})",
          step(tree) == 'stopped' and (not kids or not any(alive(p) for p in kids) or cg == 'None'), (kids, cg))
    check("...a script kept in its folder, its stdin /dev/null: a command inside cannot eat the rest",
          step(sc) == 'done' and 'second-step' in tail, tail)

    # ---- tasks, children, a lost run
    prog = (f"import sys, os; sys.path.insert(0, 'bin'); import run\n"
            f"try:\n    with run.task('a task', of='session-t') as t:\n        t.progress(done=5, total=10, unit='files')\n"
            f"        raise ValueError('on purpose')\nexcept ValueError:\n    pass\n"
            f"with run.task('a task that dies'):\n    os.kill(os.getpid(), 9)\n")
    grow.run(PY, '-c', prog, cwd=G, env=ENV)
    probe = (f"import sys, json; sys.path.insert(0, 'bin'); import run\nreg = run.Registry()\n"
             f"a = run.Run(reg.ids(\"name = 'a task'\")[0], reg); d = run.Run(reg.ids(\"name = 'a task that dies'\")[0], reg)\n"
             f"print(json.dumps([a.step(), reg.last(a.id)['reason'], a.progress().get('done'), run.reconcile_one(d), "
             f"len(reg.ids('name LIKE ?', ('A TASK%',))), len(reg.ids(\"name LIKE 'a_task'\"))]))")
    o = grow.run(PY, '-c', probe, cwd=G, env=ENV)
    got = json.loads(o.stdout.strip().splitlines()[-1]) if o.returncode == 0 and o.stdout.strip() else None
    check("tasks: a task that raises ends failed (raised), its progress kept; one whose process died is lost",
          got and got[:4] == ['failed', 'raised', 5, 'lost'], (got, o.out[-600:]))
    check("...the registry found by a name's pattern, as SQL's LIKE reads it (`%`, `_`, letters in either case)",
          got and got[4:] == [2, 1], got)
    par = (f"import sys, time; sys.path.insert(0, 'bin'); import run\n"
           f"[run.start(['sleep', '60'], name=f'child {{i}}') for i in range(2)]\ntime.sleep(60)\n")
    p = rid(R('start', '--name', 'a parent', '--', PY, '-c', par))
    time.sleep(2.5)
    R('stop', p or '-', '--tree', '--why', 'a test')
    o = grow.run(PY, '-c', f"import sys, json; sys.path.insert(0, 'bin'); import run\nr = run.Run({p!r})\n"
                           f"print(json.dumps([r.step()] + [c.step() for c in r.children()]))", cwd=G, env=ENV)
    got = json.loads(o.stdout.strip().splitlines()[-1]) if o.returncode == 0 and o.stdout.strip() else None
    check("...runs started inside a run are its children, and stop --tree ends them first",
          got == ['stopped', 'stopped', 'stopped'], (got, o.out[-400:]))

    # ---- identity
    o = grow.run(PY, '-c', "import sys, os; sys.path.insert(0, 'bin'); import run\n"
                           "r = run.start(['sleep', '30'], name='an identity')\nc = r.c\n"
                           "r.reg.set(r.id, ticks=c['ticks'] + 1)\n"          # as if its pid now named another process
                           "try:\n    run.stop(r, why='a test')\n    print('signalled')\nexcept run.Refused as e:\n"
                           "    print('refused', e.code)\n"
                           "os.kill(c['pid'], 9)\n", cwd=G, env=ENV)
    check("identity: a pid whose start ticks are not the run's names another process, and is refused (exit 5)",
          'refused 5' in o.stdout, o.out[-400:])

    # ---- the store (once every run of the tests above has ended, each supervisor's last move written)
    for _ in range(100):
        live = [d for d in json.loads(R('list', '--all', '--json').stdout or '[]') if d['step'] not in
                ('done', 'failed', 'stopped', 'lost')]
        if not live:
            break
        time.sleep(0.2)
    f = f'{REG}/store.sqlite'
    import sqlite3
    db = sqlite3.connect(f'file:{f}?mode=ro', uri=True)
    courses = db.execute("SELECT count(*) FROM v_be").fetchone()[0]
    acts = db.execute("SELECT count(*) FROM v_make WHERE id LIKE 'run-%-made'").fetchone()[0]
    moves = db.execute("SELECT count(*) FROM v_move").fetchone()[0]
    details = db.execute("SELECT count(*) FROM detail WHERE key LIKE 'runs.%'").fetchone()[0]
    mode = db.execute('PRAGMA journal_mode').fetchone()[0]
    db.close()
    check("store: each run's course a `be` on walk-run, known by its own act, its moves `move`s, its columns a detail of "
          "its being", courses == acts == details and courses >= 15 and moves >= 4 * courses - 5,
          (courses, acts, details, moves))
    check("...kept with a rollback journal, readable by others", mode == 'delete' and
          oct(os.stat(f).st_mode & 0o777) == '0o644', (mode, oct(os.stat(f).st_mode)))
    ro = os.path.join(T, 'ro')
    os.makedirs(ro)
    shutil.copy(f, f'{ro}/store.sqlite')
    os.chmod(f'{ro}/store.sqlite', 0o444)
    os.chmod(ro, 0o555)
    o = grow.run(PY, '-c', "import sys, json; sys.path.insert(0, 'bin'); import run\n"
                           f"print(json.dumps([len(run.listing(run.Registry({ro!r}, write=False), True))]))", cwd=G,
                 env=ENV)
    os.chmod(ro, 0o755)
    check("...a reader with read permission alone lists every run (the runs page, as another user)",
          o.returncode == 0 and json.loads(o.stdout.strip().splitlines()[-1])[0] >= 15, o.out[-600:])
    c = grow.run(PY, 'bin/store.py', 'check', '--path', f, cwd=G, env=ENV)
    check("...the store's check over git judges every course and move against the walk: nothing to say", c.returncode == 0
          and '0 finding(s)' in c.out, c.out[-1500:])
    x = R('export', a or '-', '--self')
    with open(f'{G}/beans/session-t.md', encoding='utf-8') as fh:
        bean = fh.read()
    head, _, rest = bean.partition('\n---\n')
    with open(f'{G}/beans/an-export.md', 'w', encoding='utf-8') as fh:
        fh.write('---\nbean: an-export\nkind: document\ntitle: "an export"\nstatements:\n'
                 '  - derive: { by: session-t, from: unknown, at: now }\n' + x.stdout + '---\nAn export.\n')
    s = grow.run(PY, 'bin/save.py', 'sam', 'a run exported', '--body', '- action: wrote [[an-export]]', cwd=G)
    check("...a run exported into a bean passes the gate", x.returncode == 0 and s.returncode == 0, x.out + s.out[-800:])

    # ---- a failing watcher's notices, one a window; the folders of old runs pruned, their statements kept
    fake = os.path.join(T, 'fakebin')
    os.makedirs(fake)
    with open(f'{fake}/notify-send', 'w') as fh:
        fh.write(f'#!/bin/sh\necho "$@" >> {T}/notices\n')
    os.chmod(f'{fake}/notify-send', 0o755)
    loud = {k: v for k, v in ENV.items() if k != 'DAFTAR_RUNS_QUIET'}
    loud['PATH'] = fake + ':' + loud.get('PATH', '')
    for i in range(3):
        f3 = rid(R('start', '--name', 'a failing pass', '--', 'sh', '-c', 'exit 1', env=loud))
        R('wait', f3 or '-', '--timeout', '20', env=loud)
    told = open(f'{T}/notices').read().count('a failing pass: failed') if os.path.exists(f'{T}/notices') else 0
    f4 = rid(R('start', '--name', 'a failing pass', '--', 'sh', '-c', 'exit 1', env=dict(loud, DAFTAR_RUNS_NOTICE_EVERY='0')))
    R('wait', f4 or '-', '--timeout', '20', env=loud)
    after = open(f'{T}/notices').read() if os.path.exists(f'{T}/notices') else ''
    check("notices: a run name failing three times in a window tells the desktop once; the next notice after the window "
          "says how many were held back", told == 1 and after.count('a failing pass: failed') == 2
          and '2 more failed of a failing pass held back' in after, after)
    before = sorted(d for d in os.listdir(REG) if d.startswith('run-'))
    pr = R('prune', '--days', '0')
    left = sorted(d for d in os.listdir(REG) if d.startswith('run-'))
    listed = R('list', '--all', '--json')
    check("prune: the folders of runs ended are taken out, the last run of each name keeps its own, and every run's "
          "statements stay in the store", pr.returncode == 0 and len(left) < len(before) and f4 in left
          and f3 not in left and len(json.loads(listed.stdout)) >= len(before) - 2, (pr.out, len(before), len(left)))

    # ---- many writers
    many = [rid(R('start', '--name', f'together {i}', '--', 'sh', '-c', 'sleep 0.3')) for i in range(8)]
    for i in many:
        R('wait', i or '-', '--timeout', '30')
    o = grow.run(PY, '-c', "import sys, json; sys.path.insert(0, 'bin'); import run\nreg = run.Registry()\n"
                           f"print(json.dumps([[m['step'] for m in reg.moves(i)] for i in {many!r}]))", cwd=G, env=ENV)
    got = json.loads(o.stdout.strip().splitlines()[-1]) if o.returncode == 0 and o.stdout.strip() else []
    check("writers: eight runs together, each supervisor writing its own moves — every move kept, in order",
          len(got) == 8 and all(m == ['queued', 'starting', 'running', 'done'] for m in got), got)
finally:
    for d in (os.path.join(T, 'ro'),):
        if os.path.isdir(d):
            os.chmod(d, 0o755)
    subprocess.run([PY, 'bin/run.py', 'reconcile'], cwd=G, env=ENV, capture_output=True) if os.path.isdir(G) else None
    shutil.rmtree(T, ignore_errors=True)

# ---- an adopted process of another user: its name alone is kept (an argument can hold a secret under any flag)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import importlib
R = importlib.import_module('run')
saved = (R.uid_of, R.comm_of, R.cmdline)
try:
    R.cmdline, R.comm_of = (lambda pid: ['odoo', '-w', 'not-a-real-one', '--db_password=x']), (lambda pid: 'odoo')
    R.uid_of = lambda pid: os.getuid() + 1
    other = R.shown_argv(4242)
    R.uid_of = lambda pid: os.getuid()
    own = R.shown_argv(4242)
finally:
    R.uid_of, R.comm_of, R.cmdline = saved
check("adopt: a process whose user the machine names none (a container's) is kept by the user's number",
      R.user_name(os.getuid()) == R.LOGIN and R.user_name(2 ** 31 - 7) == str(2 ** 31 - 7), R.user_name(2 ** 31 - 7))
check("adopt: another user's process is kept by its name alone — `-w <password>` is no flag a mask knows; one's own "
      "is kept masked where a flag's name says secret", other == ['odoo'] and own == ['odoo', '-w', 'not-a-real-one',
                                                                                      '--db_password=***'], (other, own))

print(f"\nrun: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
