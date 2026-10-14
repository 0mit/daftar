#!/usr/bin/env python3
"""What makes the gate fast, held to what it must not change: the same verdicts, read the same way.

Grows a garden of the core from a release made of this tree (test/grow.py) and measures what can be counted — which
loader reads, how many processes start, how often a law file is read, how often a graph is built — rather than how long
anything takes:

  loader   core/read.py reads with libyaml's CBaseLoader where PyYAML has it, and with the pure BaseLoader where it has
           not (taken away here, as on a platform whose PyYAML lacks libyaml); both read every law file and every bean
           to the same objects, and the gate prints the same verdicts byte for byte either way
  held     the hook's question — does every pointer the index adds resolve on this host? — reads HEAD's copy of only
           the beans that hold a pointer, in one `git cat-file --batch`, not one `git show` per bean of the garden;
           and still refuses a pointer that resolves nowhere, and lets one HEAD already held pass
  one      `bin/check.py --staged --held`, as the hook runs it, judges the index and asks held in its own process: no
           second interpreter, the same verdict and exit as the gate and held asked one after the other
  law      the law's self-check over its tables' forms runs once per law version: a second gate reads no law file
           twice, and a law file changed is judged again, its fault found
  room     the room rule builds the part/at graph once per judge, not once for each pair of beings it compares

Run: python3 test/core_speed.py   (0 = green; under a minute)
"""
import json
import os
import shutil
import sys
import tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='core-speed-')
G = os.path.join(T, 'g')
NOLIB = ("import sys, runpy, yaml\n"
         "for n in ('CBaseLoader', 'CSafeLoader', 'CLoader', 'CFullLoader', 'CUnsafeLoader', 'CDumper', 'CSafeDumper'):\n"
         "    if hasattr(yaml, n): delattr(yaml, n)\n"
         "yaml.__with_libyaml__ = False\n")


def run(*a, cwd=None):
    return grow.run(*a, cwd=cwd or G)


def write(root, rel, text):
    p = os.path.join(root, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def doc(bid, kind, *statements):
    return (f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{bid}\"\nstatements:\n" + ''.join(f"  - {s}\n" for s in statements)
            + f"---\n{bid}, invented.\n")


def probe(code, *args, cwd=None):
    """A Python program run in the garden, its last line of output read as JSON."""
    r = run(PY, '-c', code, *args, cwd=cwd)
    try:
        return json.loads(r.stdout.strip().splitlines()[-1]), r
    except (ValueError, IndexError):
        return None, r


try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam')
    check("a garden of the core grows", r.returncode == 0, r.out[-600:])
    for n in range(1, 21):
        write(G, f'beans/note-{n}.md', doc(f'note-{n}', 'document', 'say: { by: sam, at: now }'))
    PTR1, PTR2 = 'root:vault/' + '1' * 32, 'root:vault/' + '2' * 32
    write(G, 'beans/sealed-1.md', doc('sealed-1', 'document', 'say: { by: sam, at: now }',
                                      f'measure: {{ id: w, held: "{PTR1}" }}'))
    r = run(PY, 'bin/save.py', 'sam', 'twenty notes, and one sealed', '--body', '- action: wrote ' +
            ', '.join(f'[[note-{n}]]' for n in range(1, 21)) + ', [[sealed-1]]', '- held: sealed-1 w added')
    if r.returncode != 0:                         # sealed where no store holds it: HEAD gets it as a fixture would
        run('git', 'commit', '-q', '--no-verify', '-m', 'twenty notes, and one sealed')
    check("twenty notes and a bean holding a sealed statement are committed", run('git', 'status', '--porcelain').out == '',
          r.out[-600:])

    # ---- LOADER
    code = ("import sys, json\n" + "{nolib}" + "sys.path.insert(0, '.')\nfrom core import read\n"
            "print(json.dumps({'loader': read.LOADER.__name__, 'doc': read.loads('a: 1\\nb: [on, 010, 2026-10-01, ~]\\n')}))")
    with_lib, r1 = probe(code.replace('{nolib}', ''))
    without, r2 = probe(code.replace('{nolib}', NOLIB))
    want = 'CBaseLoader' if hasattr(yaml, 'CBaseLoader') else 'BaseLoader'
    check(f"loader: core/read.py reads with libyaml's loader where PyYAML has it ({want} here), and with the pure "
          f"BaseLoader where it has not — every scalar a string either way",
          with_lib and without and with_lib['loader'] == want and without['loader'] == 'BaseLoader'
          and with_lib['doc'] == without['doc'] == {'a': '1', 'b': ['on', '010', '2026-10-01', '~']},
          (with_lib, without, r1.out[-400:], r2.out[-400:]))
    if hasattr(yaml, 'CBaseLoader'):
        sys.path.insert(0, os.path.join(ROOT, 'bin'))
        import parse as dmparse
        docs = [os.path.join(ROOT, 'core', 'law', f) for f in sorted(os.listdir(os.path.join(ROOT, 'core', 'law')))
                if f.endswith('.yaml')]
        docs += [os.path.join(d, f) for d in (os.path.join(G, 'beans'), os.path.join(ROOT, 'site')) if os.path.isdir(d)
                 for f in sorted(os.listdir(d)) if f.endswith(('.md', '.yaml'))]
        differ, n = [], 0
        for p in docs:
            text = open(p, encoding='utf-8').read()
            if p.endswith('.md'):
                text = dmparse.split_front_matter(text)[0]
                if text is None:
                    continue
            n += 1
            try:
                a = yaml.load(text, Loader=yaml.BaseLoader)
            except yaml.YAMLError as e:
                a = ('error', type(e).__name__)
            try:
                b = yaml.load(text, Loader=yaml.CBaseLoader)
            except yaml.YAMLError as e:
                b = ('error', type(e).__name__)
            if a != b:
                differ.append(os.path.relpath(p, ROOT if p.startswith(ROOT) else G))
        check(f"loader: both loaders read the same objects from every law file, every bean and the site's tables ({n})",
              n > 30 and not differ, differ)

    # a garden with faults to say, its verdicts compared: the gate with libyaml and without
    G2 = os.path.join(T, 'rooms')
    shutil.copytree(G, G2, ignore=shutil.ignore_patterns('.git'))
    for n in range(1, 9):
        write(G2, f'beans/box-{n}.md', doc(f'box-{n}', 'host', 'read: { by: sam, at: now }', 'own: { by: sam, of: self }',
                                           'be: { by: self, at: "192.0.2.10", as: location }',
                                           *(['part: { by: self, of: box-1 }'] if n in (2, 3) else [])))
    a = run(PY, 'core/check.py', G2)
    b = run(PY, '-c', NOLIB + "sys.argv = ['core/check.py', sys.argv[1]]\nrunpy.run_path('core/check.py', run_name='__main__')", G2)
    check("loader: the gate's verdicts on a garden with faults are the same byte for byte with libyaml and without it",
          a.stdout == b.stdout and a.returncode == b.returncode == 1 and 'room' in a.stdout, (a.out[-600:], b.out[-600:]))

    # ---- ROOM: the part/at graph, built once per judge
    code = r"""import sys, json; sys.path.insert(0, '.'); sys.path.insert(0, 'bin')
from core import engine
from core.check import garden_law
law, garden = garden_law(sys.argv[1]), engine.Garden.read(sys.argv[1])
J = engine.Judge(law, garden)
calls, related = [0], [0]
beans_in, rel = J._beans_in, J._related
def counted(*a, **k):
    if sys._getframe(1).f_code.co_name in ('_related', '_part_at'):
        calls[0] += 1
    return beans_in(*a, **k)
def counted_rel(*a, **k):
    related[0] += 1
    return rel(*a, **k)
J._beans_in, J._related = counted, counted_rel
J.room()
steps = sum(1 for b in garden.beans.values() for _i, v, r in b.items if (v == 'part' and 'of' in r) or (v == 'be' and 'at' in r))
print(json.dumps({'graph': calls[0], 'steps': steps, 'pairs': related[0], 'found': len(J.out)}))"""
    got, r = probe(code, G2)
    check("room: the part/at graph is built once per judge — each `part` and `be … at` read once, however many pairs of "
          "beings in one room it compares", got and got['pairs'] >= 6 and 0 < got['graph'] <= 2 * got['steps']
          and got['found'] >= 1, (got, r.out[-600:]))

    # ---- HELD: HEAD's copies of only the beans that hold a pointer, in one git process
    said = [ln.split('at: ', 1)[1].rstrip(' }') for ln in run('git', 'show', 'HEAD:beans/note-1.md').stdout.split('\n')
            if 'say:' in ln][0]                   # the act HEAD holds stays as it is; what is added, its own act knows
    write(G, 'beans/note-1.md', doc('note-1', 'document', f'say: {{ by: sam, at: {said} }}',
                                    'own: { id: o, by: sam, of: self }', 'say: { by: sam, of: [o], at: now }'))
    write(G, 'beans/sealed-2.md', doc('sealed-2', 'document', 'say: { by: sam, at: now }',
                                      f'measure: {{ id: w, held: "{PTR2}" }}'))
    run(PY, 'bin/journal.py', 'sam', 'a note changed, a second sealed', '--body', '- action: wrote [[note-1]], [[sealed-2]]',
        '- held: sealed-2 w added')
    run('git', 'add', '-A')
    code = r"""import sys, json, subprocess; sys.path.insert(0, 'bin')
calls, real = [], subprocess.run
def counted(a, *k, **kw):
    calls.append([str(x) for x in a])
    return real(a, *k, **kw)
subprocess.run = counted
import held
bad = held.unresolved_new(staged=True)
print(json.dumps({'bad': bad, 'git': [c for c in calls if c[:1] == ['git']]}))"""
    got, r = probe(code)
    shows = [c for c in (got or {}).get('git', []) if 'show' in c]
    check("held: the pointers the index adds are found reading HEAD's copy of only the beans that hold one, in one "
          "`git cat-file --batch` — no `git show` per bean of a 22-bean garden; a new pointer that resolves nowhere is "
          "refused, and one HEAD already held is not asked again",
          got is not None and not shows and sum(1 for c in got['git'] if 'cat-file' in c) <= 2
          and len(got['bad']) == 1 and got['bad'][0].startswith('sealed-2: '), (got, r.out[-600:]))

    # ---- ONE: the hook's gate and held in one process, its verdict theirs
    code = r"""import sys, json, subprocess, runpy; sys.path.insert(0, 'bin')
spawned, real = [], subprocess.Popen.__init__
def counted(self, a, *k, **kw):
    spawned.append([str(x) for x in (a if isinstance(a, (list, tuple)) else [a])])
    return real(self, a, *k, **kw)
subprocess.Popen.__init__ = counted
import io, contextlib
out, err = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    sys.argv = ['bin/check.py'] + sys.argv[1:]
    try:
        runpy.run_path('bin/check.py', run_name='__main__')
        code = 0
    except SystemExit as e:
        code = e.code
py = [a for a in spawned if 'python' in a[0].lower() or a[0] == sys.executable]
print(json.dumps({'code': code, 'out': out.getvalue(), 'err': err.getvalue(), 'pythons': py}))"""
    one, r = probe(code, '--staged', '--held')
    gate = run(PY, 'bin/check.py', '--staged')
    held_alone = run(PY, 'bin/held.py', 'new', '--staged')
    check("one: `bin/check.py --staged --held`, as the hook runs it, starts no second Python — and its verdict is the "
          "gate's and held's asked one after the other: the gate passes, held refuses the pointer, exit 1",
          one is not None and one['pythons'] == [] and one['code'] == 1 and gate.returncode == 0
          and held_alone.returncode == 1 and 'NOT COMMITTED: a pointer' in one['err'] and one['err'] == held_alone.stderr
          and one['out'] == gate.stdout, (one, gate.out[-400:], held_alone.out[-400:], r.out[-400:]))
    r = run(PY, 'bin/check.py', '--held')
    check("one: --held without --staged is refused: the gate itself never reads a store", r.returncode == 2
          and '--held' in r.stderr, r.out[-400:])
    run('git', 'reset', '-q', '--hard', 'HEAD')
    run('git', 'clean', '-qfd')

    # ---- LAW: the self-check over the tables' forms, once per law version
    code = r"""import sys, json, collections; sys.path.insert(0, '.'); sys.path.insert(0, 'bin')
from core import read, engine
reads, data = collections.Counter(), read.data
def counted(path):
    reads[path] += 1
    return data(path)
read.data = counted
from core.check import garden_law
found = engine.judge(garden_law('.'), engine.Garden.read('.'))
law = {p: n for p, n in reads.items() if '/core/law/' in p.replace('\\', '/')}
print(json.dumps({'found': [list(f) for f in found], 'twice': sorted(p for p, n in law.items() if n > 1), 'files': len(law)}))"""
    kept = os.path.join(G, '.git', 'daftar', 'law-checked')
    shutil.rmtree(kept, ignore_errors=True)
    first, r1 = probe(code)
    second, r2 = probe(code)
    check("law: the law's self-check over its tables' forms runs once per law version — the second gate reads no law "
          "file twice, and finds what the first found",
          first and second and second['twice'] == [] and second['found'] == first['found'] and second['files'] >= 15
          and os.path.isdir(kept) and len(os.listdir(kept)) == 1, (first and first['twice'], second, r2.out[-400:]))
    vp = os.path.join(G, 'core', 'law', 'values.yaml')
    was = open(vp, encoding='utf-8').read()
    write(G, 'core/law/values.yaml', was.replace('{ value: time-of-day, is: moment,', '{ value: time-of-day, odd: yes, '
                                                 'is: moment,', 1))
    third, r3 = probe(code)
    write(G, 'core/law/values.yaml', was)
    check("law: a law file changed is judged again — a column a table's form does not hold is found, not passed on the "
          "word of the version before", was.count('{ value: time-of-day, is: moment,') == 1 and third and any(
              'column `odd` is not in the table' in f[2] for f in third['found']), (third, r3.out[-400:]))
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_speed: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
