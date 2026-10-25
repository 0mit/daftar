#!/usr/bin/env python3
"""A commit judged the same everywhere, and who said it (core 3.5; the next machinery's design, bodies II and V).

The language held to its pin (II.2): the release carries the SHA-256 of every file seed/LANGUAGE ships
(seed/LANGUAGE.sha256), which `bin/pass.py --digests --check` holds to this tree, and no text a release ships keeps a
CRLF. In a garden grown from it: nothing differs, and the gate says nothing of it; a file patched there is said first by
the gate, on stderr, and a commit of it is refused by rule `kept` though it says RULE-CHANGE; the digests changed by hand
are refused; the adoption's own commit — GARDEN.md's `daftar_release` moved, RULE-CHANGE said — brings a file and its
digest together; and a line end a checkout turned is no divergence.

Who wrote it (V.1): a save whose writer is no bean the garden holds is refused before anything is written.

A pin naming another repository (V.4): the gate takes a pin `through` a codebase, whose commit is no commit of this
garden; bin/where.py reads it against the clone this host keeps at its root — PINNED, NOT-IN-CLONE — and HOPED where
this host keeps none.

Run: python3 test/core_commit.py   (0 = green; under a minute)
"""
import os, re, shutil, socket, subprocess, sys, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))   # last: test/core.py is no package `core`
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
import importlib  # noqa: E402
dmpass = importlib.import_module('pass')    # noqa: E402 — bin/pass.py, the one reader of seed/LANGUAGE
FAILS = []
PY = sys.executable
ME = socket.gethostname().lower().split('.')[0]


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='core-commit-')
G = os.path.join(T, 'g')


def run(*a, cwd=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G)
    r.out = r.stdout + r.stderr
    return r


def write(rel, text, root=None, newline='\n'):
    p = os.path.join(root or G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline=newline) as fh:
        fh.write(text)


def text(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def head():
    return run('git', 'rev-parse', 'HEAD').stdout.strip()


def undo():
    """The working tree and the index as HEAD holds them: what a refused save left, taken back."""
    run('git', 'reset', '-q', '--hard', 'HEAD')
    run('git', 'clean', '-qfd')


SAM = """---
bean: sam
kind: person
title: "Sam — keeps this garden"
summary: "The gardener."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Sam keeps this ledger.
"""

try:
    # ---- THE RELEASE: its digests are its tree's, and no text it ships keeps a CRLF
    r = run(PY, 'bin/pass.py', '--digests', '--check', cwd=ROOT)
    check("the release carries the SHA-256 of every file its seed/LANGUAGE ships, and they are this tree's "
          "(bin/pass.py --digests --check)", r.returncode == 0 and 'holds this tree' in r.out, r.out[-400:])
    want = dmpass.digests_of(open(os.path.join(ROOT, *dmpass.DIGESTS.split('/')), encoding='utf-8').read())
    shipped = dmpass.release_files(ROOT)
    check(f"...one line for each of the {len(shipped)} files, the digests' own file aside",
          sorted(want) == sorted(shipped) and dmpass.DIGESTS not in want, sorted(set(want) ^ set(shipped))[:5])
    stored = {}
    for f in shipped:
        b = subprocess.run(['git', '-C', ROOT, 'show', f":{f}"], capture_output=True).stdout
        stored[f] = b
    crlf = [f for f, b in stored.items() if b'\0' not in b[:8000] and b'\r\n' in b]
    check("...and no text the release ships keeps a CRLF, so a digest read with a turned line end as LF is the file's",
          not crlf, crlf)

    # ---- A GARDEN GROWN FROM IT
    r = run('sh', os.path.join(ROOT, 'seed', 'germinate.sh'), G, cwd=ROOT)
    check("a garden germinates through its gate", r.returncode == 0, r.out[-800:])
    run('git', 'config', 'user.name', 'sam')
    run('git', 'config', 'user.email', 'sam@example.invalid')
    write('GARDEN.md', text('GARDEN.md').replace('\ngardener:', '\ngardener: sam', 1))
    write('beans/sam.md', SAM)
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: the gardener', '--body',
            '- action: RULE-CHANGE, sam keeps the garden: [[sam]]; ratified by sam')
    check("(the gardener named, through the gate)", r.returncode == 0, r.out[-800:])
    check("the garden holds its release's digests, and nothing it holds differs from them",
          os.path.isfile(os.path.join(G, *dmpass.DIGESTS.split('/'))) and dmpass.diverged(G) == [], dmpass.diverged(G))
    r = run(PY, 'bin/check.py')
    check("...so the gate says nothing of its copy", r.returncode == 0 and 'differs from its release' not in r.out,
          r.out[-400:])

    # ---- WHO WROTE IT IS A BEING (V.1)
    j0 = text('log/journal.md')
    write('beans/note.md', '---\nbean: note\nkind: document\ntitle: "A note"\nstatements:\n  - say: { by: sam, at: now }\n'
                           '---\nA note.\n')
    r = run(PY, 'bin/save.py', 'agent (some model)', 'a note', '--body', '- action: [[note]]')
    check("a save whose writer is no bean the garden holds is refused before anything is written, saying what to write",
          r.returncode != 0 and 'is no being this garden holds, and nothing written' in r.out
          and text('log/journal.md') == j0, r.out[-600:])
    r = run(PY, 'bin/save.py', 'sam', 'a note', '--body', '- action: [[note]]')
    check("...and saved by a being the garden holds", r.returncode == 0, r.out[-600:])

    # ---- THE LANGUAGE HELD TO ITS PIN (II.2)
    why = text('bin/why.py')
    write('bin/why.py', why + "# a line of this garden's own\n")
    r = run(PY, 'bin/check.py')
    check("a file of the language patched in the garden is said first by the gate, on stderr, naming it",
          'differs from its release in 1 file(s) — bin/why.py' in r.stderr and 'differs' not in r.stdout, r.out[-600:])
    before = head()
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: why patched', '--body',
            '- action: RULE-CHANGE, bin/why.py patched in the garden; ratified by sam')
    check("...and a commit of it is refused by `kept`, though it says RULE-CHANGE: a file the release keeps is as its "
          "release made it", r.returncode != 0 and "differs from the release's own" in r.out and head() == before,
          r.out[-800:])
    undo()
    dig = text(dmpass.DIGESTS)
    write(dmpass.DIGESTS, dig.replace(dig[:64], 'f' * 64, 1))
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: the digests', '--body',
            '- action: RULE-CHANGE, the digests moved by hand; ratified by sam')
    check("the digests changed by hand are refused: they change only with the release GARDEN.md records",
          r.returncode != 0 and 'the digests of the release change' in r.out and head() == before, r.out[-800:])
    undo()
    write('bin/why.py', why + "# the next release's line\n")
    write(dmpass.DIGESTS, dmpass.digests_text(G))
    g0 = text('GARDEN.md')
    write('GARDEN.md', re.sub(r'(?m)^daftar_release:.*$', 'daftar_release: "v9.9.9"', g0, count=1)
          if re.search(r'(?m)^daftar_release:', g0) else g0.replace('\nextends:', '\ndaftar_release: "v9.9.9"\nextends:', 1))
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: adopted v9.9.9', '--body',
            '- action: RULE-CHANGE, the release v9.9.9 adopted, its files and digests with it; ratified by sam')
    check("the adoption's own commit — GARDEN.md's `daftar_release` moved, RULE-CHANGE said — brings a file and its digest "
          "together", r.returncode == 0 and head() != before and dmpass.diverged(G) == [], r.out[-800:])
    write('bin/why.py', text('bin/why.py').replace('\n', '\r\n'), newline='')
    check("a line end a checkout turned (CRLF, as Git for Windows writes text) is no divergence",
          b'\r\n' in open(os.path.join(G, 'bin', 'why.py'), 'rb').read() and dmpass.diverged(G) == [], dmpass.diverged(G))
    undo()

    # ---- A PIN NAMING ANOTHER REPOSITORY (V.4)
    app = os.path.join(T, 'app')
    os.makedirs(app)
    for step in (('init', '-q'), ('config', 'user.name', 'sam'), ('config', 'user.email', 'sam@example.invalid'),
                 ('commit', '-q', '--allow-empty', '-m', 'the app, begun')):
        run('git', *step, cwd=app)
    c1 = run('git', 'rev-parse', 'HEAD', cwd=app).stdout.strip()
    v = text('VOCAB.md')
    row = '  - { namespace: anchor-hostname, meaning: "what a machine calls itself" }\n'
    write('VOCAB.md', re.sub(r'(?m)^namespaces:.*\n', lambda m: 'namespaces:\n' + row, v, count=1)
          if re.search(r'(?m)^namespaces:', v) else v.replace('---\n', '---\nnamespaces:\n' + row, 1))
    write('beans/here.md', f"""---
bean: here
kind: host
title: "here — the machine this runs on"
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {ME} }}
details:
  roots:
    app-clone: {{ system: unix-filesystem, at: '{ME}:{app}' }}
---
The machine.
""")
    write('beans/app.md', '---\nbean: app\nkind: codebase\ntitle: "app — the shop\'s code"\nstatements:\n'
                          '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n---\nThe code.\n')
    write('beans/build.md', f"""---
bean: build
kind: document
title: "A build of the app"
statements:
  - say: {{ by: sam, at: now }}
  - do: {{ id: c, by: sam, as: workstation }}
  - pin: {{ id: built, by: sam, of: [c], through: app, at: [now, "app-clone@{c1}"] }}
  - pin: {{ id: wrong, by: sam, of: [c], through: app, at: [now, "app-clone@{'0' * 40}"] }}
  - pin: {{ id: away, by: sam, of: [c], through: app, at: [now, "app-elsewhere@{c1}"] }}
---
Pinned to the app's commits.
""")
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: the app, its build pinned', '--body',
            '- action: RULE-CHANGE, VOCAB.md adds the namespace anchor-hostname; [[here]], [[app]] and [[build]], '
            'pinned through the app; ratified by sam')
    check("the gate takes a pin `through` a codebase: its commit is another repository's, which no gate refuses",
          r.returncode == 0, r.out[-900:])
    r = run(PY, 'bin/where.py', 'build')
    lines = {ln.split()[2] + ' ' + ln.split()[3]: ln.split()[0] for ln in r.stdout.split('\n')
             if len(ln.split()) > 3 and ln.split()[2] == 'pin'}
    check("bin/where.py reads each against the clone this host keeps at its root: PINNED where it reaches the commit, "
          "NOT-IN-CLONE where it does not, HOPED where this host keeps none — and fails on none",
          r.returncode == 0 and lines == {'pin built': 'PINNED', 'pin wrong': 'NOT-IN-CLONE', 'pin away': 'HOPED'},
          (lines, r.out[-900:]))
finally:
    shutil.rmtree(T, ignore_errors=True)

print("\ncore_commit: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
