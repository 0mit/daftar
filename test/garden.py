#!/usr/bin/env python3
"""The one garden model, bin/dmgarden.py, and the one entry, bin/daftar.py.

In a garden grown from this checkout:
  1. `paths` lists what a glob of `beans/*.md` and `mappings/*.md` lists, in the same order — a hidden file, a file of
     another kind and a directory left out — and a space asked alone gives that space alone;
  2. `listed` gives what git holds: the index, and a commit, each `<space>/<id>.md`, a document in a subdirectory left
     out; `untracked` the new documents git does not track, and not what it ignores;
  3. `document` parses once, reads a document again when it changes, and gives a document that does not parse with its
     reason, never a traceback;
  4. every tool of bin/ has a verb in the law's `verbs`, each verb a family, and `daftar <verb>` runs the verb's tool;
  5. no tool of this checkout lists the beans itself: the catalogue finds no file that walks them outside the model.
"""
import glob, json, os, shutil, subprocess, sys, tempfile, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmgarden  # noqa: E402
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1200]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    return subprocess.run(a, cwd=cwd, capture_output=True, text=True, encoding='utf-8')


T = tempfile.mkdtemp(prefix='garden-model-')
try:
    G = os.path.join(T, 'g')
    r = run(sys.executable, os.path.join(ROOT, 'seed', 'germinate.py'), G, '--gardener', 'sam')
    check("(setup) a garden grows from this checkout", r.returncode == 0 and os.path.isdir(os.path.join(G, 'beans')),
          r.stdout + r.stderr)
    for rel, text in (('beans/b-two.md', '---\nbean: b-two\n---\n'), ('beans/a-one.md', '---\nbean: a-one\n---\n'),
                      ('mappings/m-one.md', '---\nmapping: m-one\n---\n'), ('beans/.hidden.md', 'x'),
                      ('beans/notes.txt', 'x'), ('beans/sub/deep.md', '---\nbean: deep\n---\n')):
        os.makedirs(os.path.dirname(os.path.join(G, rel)), exist_ok=True)
        open(os.path.join(G, rel), 'w', encoding='utf-8').write(text)
    os.makedirs(os.path.join(G, 'beans', 'dir.md'), exist_ok=True)

    # ---- 1. the working tree
    want = sorted(glob.glob(os.path.join(G, 'beans', '*.md'))) + sorted(glob.glob(os.path.join(G, 'mappings', '*.md')))
    want = [p for p in want if os.path.isfile(p)]
    got = dmgarden.paths(G)
    check("paths lists what a glob lists, in its order, less a directory named like a document", got == want,
          (got, want))
    check("...and leaves out a hidden file, a file of another kind and a document in a subdirectory",
          not any(os.path.basename(p) in ('.hidden.md', 'notes.txt', 'deep.md') for p in got), got)
    check("a space asked alone gives that space alone, in the order of its names",
          [os.path.basename(p) for p in dmgarden.paths(G, 'mappings')] == ['m-one.md']
          and dmgarden.ids(G, 'beans')[:2] == ['a-one', 'b-two'], dmgarden.ids(G, 'beans'))

    # ---- 2. what git holds
    run('git', 'add', 'beans/a-one.md', 'beans/sub/deep.md', cwd=G)
    idx = dmgarden.listed(G, ('beans', 'mappings'), at='index')
    check("listed at the index gives the staged documents, `<space>/<id>.md`, a subdirectory's left out",
          'beans/a-one.md' in idx and 'beans/sub/deep.md' not in idx and 'beans/b-two.md' not in idx, idx)
    new = dmgarden.untracked(G)
    check("untracked gives the new documents, in each space", 'beans/b-two.md' in new and 'mappings/m-one.md' in new
          and 'beans/a-one.md' not in new and 'beans/notes.txt' not in new, new)
    open(os.path.join(G, '.gitignore'), 'a', encoding='utf-8').write('\nbeans/b-two.md\n')
    check("...and not what git ignores", 'beans/b-two.md' not in dmgarden.untracked(G), dmgarden.untracked(G))
    run('git', '-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x', '--no-verify', cwd=G)
    head = run('git', 'rev-parse', 'HEAD', cwd=G).stdout.strip()
    at = dmgarden.listed(G, 'beans', at=head)
    check("listed at a commit gives that commit's documents", 'beans/a-one.md' in at and 'beans/b-two.md' not in at, at)

    # ---- 3. parsed once, read again when changed
    p = os.path.join(G, 'beans', 'a-one.md')
    d1 = dmgarden.document(p)
    check("a document is parsed by the one splitter", d1.fm == {'bean': 'a-one'} and d1.id == 'a-one'
          and d1.space == 'beans' and d1.error is None, d1)
    check("...and asked again, it is the same object, from the cache", dmgarden.document(p) is d1)
    time.sleep(0.01)
    open(p, 'w', encoding='utf-8').write('---\nbean: a-one\ntitle: again\n---\nchanged, and longer\n')
    d2 = dmgarden.document(p)
    check("...and read again once it has changed", d2.fm.get('title') == 'again', d2)
    open(p, 'w', encoding='utf-8').write('---\nbean: [unclosed\n---\n')
    d3 = dmgarden.document(p)
    check("a document that does not parse is given with its reason, never a traceback", d3.fm is None and d3.error, d3)
    r = run(sys.executable, os.path.join(G, 'bin', 'dmgarden.py'), '--paths', 'mappings', cwd=G)
    check("the command lists a space's paths, as the tools read them", r.stdout.split() == ['mappings/m-one.md'],
          r.stdout + r.stderr)
finally:
    shutil.rmtree(T, ignore_errors=True)

# ---- 4. the one entry: every tool has a verb, and a verb runs its tool
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse  # noqa: E402
law = dmparse.loads(dmparse.read(os.path.join(ROOT, 'seed', 'std-vocab.md'))[0])
verbs = {v['verb']: v['family'] for v in law.get('verbs') or []}
tools = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, 'bin', 'dm*.py'))) + ['install.py']
lost = [t for t in tools if (t[2:-3] if t.startswith('dm') else t[:-3]) not in verbs]
check(f"every tool of bin/ has a verb in the law's `verbs` ({len(tools)})", not lost, lost)
fams = {f['family'] for f in law.get('tool_families') or []}
check("...and every verb a family the law declares", all(f in fams for f in verbs.values()),
      {v: f for v, f in verbs.items() if f not in fams})
r = run(sys.executable, os.path.join(ROOT, 'bin', 'daftar.py'))
check("`daftar` lists every verb under its family, with what its tool says it does",
      r.returncode == 0 and all(f"\n  {v} " in r.stdout for v in verbs) and "check " in r.stdout, r.stdout[-600:])
r = run(sys.executable, os.path.join(ROOT, 'bin', 'daftar.py'), 'chek')
check("a word that is no verb is refused with the nearest", r.returncode == 2 and 'check' in r.stderr, r.stderr)
T2 = tempfile.mkdtemp(prefix='garden-entry-')
try:
    G2 = os.path.join(T2, 'g')
    run(sys.executable, os.path.join(ROOT, 'seed', 'germinate.py'), G2, '--gardener', 'sam')
    r = run(sys.executable, os.path.join(G2, 'bin', 'daftar.py'), 'check', '--all', cwd=G2)
    check("`daftar check --all`, in a grown garden, is the gate's own run", r.returncode == 0 and '0 error(s)' in r.stdout,
          r.stdout[-400:] + r.stderr[-400:])
finally:
    shutil.rmtree(T2, ignore_errors=True)

# ---- 5. every tool reads through the model
r = run(sys.executable, os.path.join(ROOT, 'bin', 'dmcatalog.py'), '--json', cwd=ROOT)
walks = json.loads(r.stdout)['findings']['own_bean_walks'] if r.returncode == 0 else ['(no catalogue)']
check("no tool of this checkout lists the beans itself: each reads them through bin/dmgarden.py", not walks, walks[:5])

print(f"\ngarden: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
