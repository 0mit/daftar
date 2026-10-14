#!/usr/bin/env python3
"""The garden held: a process that reads its garden again is given what it read before while nothing it was read from
has changed, and never a garden older than its files.

Grows a garden of the core from a release made of this tree (test/grow.py) and asks core/engine.py `Garden.read`, in
one process in the garden, as daftard's worker does a hundred times for one page:

  same     read twice with nothing changed: the same beans at the same version, and no document parsed or git
           process started again
  own      a reader that filters its garden's mapping or adds to it (the Odoo reader does) changes only its own
  changed  a bean rewritten in place to the same length within the same second (its stat alone could hide it): read
           again, its new words; and only that document parsed again
  added    a bean added, a bean removed, GARDEN.md's zone changed, a file staged with `git add`: each seen by the next read
  where    `.` read from two folders is two gardens, each with its own paths
  fresh    DAFTAR_HELD=0: a garden read afresh each time
  guard    DAFTAR_HELD_CHECK=1: a reader that changes a garden held is named at the next hand-out (HeldChanged)
  tree     a session's worktree (its .git a file, its index elsewhere) is held as its main copy is

Run: python3 test/core_held.py   (0 = green; under a minute)
"""
import json
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def doc(bid, kind, *statements):
    return (f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{bid}\"\nstatements:\n" + ''.join(f"  - {s}\n" for s in statements)
            + f"---\n{bid}, invented.\n")


# the program run in the garden: each step's answer one JSON line
PROGRAM = r'''
import json, os, subprocess, sys
sys.path.insert(0, '.')
from core import engine, read
G0 = os.getcwd()
parsed, runs = [], []
_doc, _run = read.document, subprocess.run
def counted_doc(p):
    parsed.append(os.path.basename(p))
    return _doc(p)
def counted_run(*a, **k):
    runs.append(a[0][:3] if a and isinstance(a[0], list) else a)
    return _run(*a, **k)
read.document, subprocess.run = counted_doc, counted_run
engine.subprocess.run = counted_run
def say(**k):
    print(json.dumps(k), flush=True)
def write(rel, text):
    with open(rel, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)

step = sys.argv[1]
if step == 'same':
    a = engine.Garden.read('.')
    parsed.clear(); runs.clear()
    b = engine.Garden.read('.')
    say(same=a.held is not None and a.held is b.held and all(a.beans[k] is b.beans[k] for k in a.beans),
        parsed=len(parsed), runs=len(runs), beans=len(b.beans))
elif step == 'changed':
    import time
    t = open('beans/note-1.md', encoding='utf-8').read()
    T = time.time_ns()                    # two writes within one tick of the file's clock: the same stat both times
    os.utime('beans/note-1.md', ns=(T, T))
    a = engine.Garden.read('.')
    write('beans/note-1.md', t.replace('note-1, invented.', 'note-1, rewritten'))   # the same length, the same file
    os.utime('beans/note-1.md', ns=(T, T))
    st_same = os.stat('beans/note-1.md').st_mtime_ns == T
    parsed.clear()
    b = engine.Garden.read('.')
    say(same_len=len(t) == len(open('beans/note-1.md', encoding='utf-8').read()) and st_same,
        body=b.beans['note-1'].body.strip(), parsed=[p for p in parsed if p != 'GARDEN.md'],
        other_kept=a.beans['note-2'] is b.beans['note-2'])
elif step == 'added':
    a = engine.Garden.read('.')
    write('beans/note-new.md', '---\nbean: note-new\nkind: document\ntitle: "note-new"\nstatements:\n  - say: { by: sam, at: now }\n---\nnew.\n')
    os.remove('beans/note-2.md')
    b = engine.Garden.read('.')
    m = open('GARDEN.md', encoding='utf-8').read()
    zone0 = b.zone
    write('GARDEN.md', m.replace('zone: ' + str(zone0), 'zone: Asia/Tehran') if zone0 else m.replace('---\n', '---\nzone: Asia/Tehran\n', 1))
    c = engine.Garden.read('.')
    write('extra.txt', 'x\n')
    d0 = 'extra.txt' in c.files
    subprocess.check_call(['git', 'add', 'extra.txt'])
    d = engine.Garden.read('.')
    say(new='note-new' in b.beans, gone='note-2' not in b.beans, zone=c.zone, was=zone0, untracked=d0,
        staged='extra.txt' in d.files)
elif step == 'where':
    a = engine.Garden.read('.')
    os.chdir('beans')
    os.makedirs('beans', exist_ok=True)
    b = engine.Garden.read('.')
    os.chdir(G0)
    say(two=a is not b, a=len(a.beans), b=len(b.beans))
elif step == 'fresh':
    a, b = engine.Garden.read('.'), engine.Garden.read('.')
    say(fresh=a is not b, same_beans=sorted(a.beans) == sorted(b.beans))
elif step == 'own':
    a = engine.Garden.read('.')
    a.beans = {k: v for k, v in a.beans.items() if k == 'note-1'}      # a reader's filter, as the Odoo reader's
    a.beans['x'] = a.beans['note-1']
    a.files.append('x.md')
    b = engine.Garden.read('.')
    say(whole=len(b.beans) >= 10 and 'x' not in b.beans and 'x.md' not in b.files, same=a.held is b.held)
elif step in ('guard', 'guard-late'):
    a = engine.Garden.read('.')
    a.beans['note-3'].header['title'] = 'changed by a reader'
    if step == 'guard-late':              # the files' recent window over: the garden is made again, of the same beans
        import time
        time.sleep(engine.RACY + 0.5)
    try:
        engine.Garden.read('.')
        say(raised=None)
    except engine.HeldChanged as e:
        say(raised=str(e))
'''


def probe(step, cwd, env=None):
    r = grow.run(PY, '-c', PROGRAM, step, cwd=cwd, env=env)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]), r
    except (ValueError, IndexError):
        return None, r


T = tempfile.mkdtemp(prefix='core-held-')
G = os.path.join(T, 'g')
try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam')
    check("a garden of the core grows", r.returncode == 0, r.out[-600:])
    os.makedirs(os.path.join(G, 'beans'), exist_ok=True)
    for n in range(1, 11):
        with open(os.path.join(G, 'beans', f'note-{n}.md'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(doc(f'note-{n}', 'document', 'say: { by: sam, at: now }'))
    r = grow.run(PY, 'bin/save.py', 'sam', 'ten notes', '--body', '- action: wrote ' +
                 ', '.join(f'[[note-{n}]]' for n in range(1, 11)), cwd=G)
    check("ten notes are saved", r.returncode == 0 and grow.run('git', 'status', '--porcelain', cwd=G).out == '',
          r.out[-600:])
    ENV = {k: v for k, v in os.environ.items() if not k.startswith('DAFTAR_HELD')}

    j, r = probe('same', G, ENV)
    check("same: read again with nothing changed, the same beans at the same version — no document parsed, no git "
          "process started",
          j and j['same'] and j['parsed'] == 0 and j['runs'] == 0 and j['beans'] >= 10, (j, r.out[-600:]))

    j, r = probe('own', G, dict(ENV, DAFTAR_HELD_CHECK='1'))
    check("own: a reader that filters its garden's mapping, puts a bean in it or adds a file changes only its own: "
          "the next reader is given the whole garden, and the guard finds nothing changed",
          j and j['whole'] and j['same'], (j, r.out[-600:]))

    j, r = probe('changed', G, ENV)
    check("changed: a bean rewritten to the same length with the same stat is read again by its bytes, its new words "
          "seen; only it is parsed again, every other bean kept",
          j and j['same_len'] and j['body'] == 'note-1, rewritten' and j['parsed'] == ['note-1.md'] and j['other_kept'],
          (j, r.out[-600:]))
    grow.run('git', 'checkout', '--', 'beans/note-1.md', cwd=G)

    j, r = probe('added', G, ENV)
    check("added: a bean added and one removed, GARDEN.md's zone changed, a file staged — each seen by the next read",
          j and j['new'] and j['gone'] and j['zone'] == 'Asia/Tehran' and not j['untracked'] and j['staged'],
          (j, r.out[-600:]))
    grow.run('git', 'reset', '-q', '--hard', cwd=G)
    grow.run('git', 'clean', '-qfd', cwd=G)

    j, r = probe('where', G, ENV)
    check("where: `.` read from two folders is two gardens, each read where it is",
          j and j['two'] and j['a'] >= 10 and j['b'] == 0, (j, r.out[-600:]))
    shutil.rmtree(os.path.join(G, 'beans', 'beans'), ignore_errors=True)

    j, r = probe('fresh', G, dict(ENV, DAFTAR_HELD='0'))
    check("fresh: with DAFTAR_HELD=0 each read is a garden read afresh, the same beans",
          j and j['fresh'] and j['same_beans'], (j, r.out[-600:]))

    j, r = probe('guard', G, dict(ENV, DAFTAR_HELD_CHECK='1'))
    check("guard: with DAFTAR_HELD_CHECK=1 a reader that changes a garden held is named at the next hand-out",
          j and j['raised'] and 'never written' in j['raised'], (j, r.out[-600:]))
    grow.run('touch', 'beans/note-5.md', cwd=G)          # a file written lately: the next garden is made again
    j, r = probe('guard-late', G, dict(ENV, DAFTAR_HELD_CHECK='1'))
    check("...and when the garden is made again over the same beans (a recent write's window over), the bean changed "
          "is still named", j and j['raised'] and 'note-3' in j['raised'], (j, r.out[-600:]))
    j, r = probe('guard', G, ENV)
    check("...and without it nothing is checked (a reader's change goes unseen: the guard is for the tests)",
          j and j['raised'] is None, (j, r.out[-600:]))

    W = os.path.join(T, 'w')
    r = grow.run('git', 'worktree', 'add', '-q', '-b', 'side', W, cwd=G)
    j, r2 = probe('same', W, ENV)
    check("tree: a worktree (its .git a file) is held as its main copy is", r.returncode == 0 and j and j['same']
          and j['parsed'] == 0 and j['runs'] == 0, (j, r.out[-300:], r2.out[-600:]))
    j, r2 = probe('changed', W, ENV)
    check("...and a bean changed in it is seen", j and j['body'] == 'note-1, rewritten', (j, r2.out[-600:]))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_held: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
