#!/usr/bin/env python3
"""The adoption of the core (v1 part 4): a garden in today's words adopts a release of the core through
bin/dmupgrade.py, in place and in one commit; a garden grown from a release of the core starts in it.

Builds what it needs, as test/upgrade.py does: a RELEASE made from this tree (v0.1.0, today's words) and the same
language with the core's templates in seed/ (v1.0.0, a release of the core: its seed/GARDEN.md.template pins `core@`),
and a GARDEN grown from v0.1.0 with a gardener and a laptop, saved through today's gate.

The adoption is planned before anything is touched: a profile moved in the same run, a bean not committed, and a garden
that fails its own gate are refused, the tree as it was; a translator refuses a garden in words it does not read. A
release whose core refuses the translation puts every file back and today's hooks with them. Then v1.0.0 is adopted:
the beans in statements, the count quoted, GARDEN.md pinning the core's version, VOCAB.md without a pin, the hooks the
ones that take the law by the pin, nothing committed. The commit is refused while the entry holds its `fill in`s, and
passes the core's gate once a person has filled them — the acts carrying the moments history recorded, granted that
once. Afterwards the gate is the core's, and the same release again is nothing to do.

A garden grown from v1.0.0 pins the core from its first commit, its gardener (a person, or an organisation) planted in
statements and saved with the moment the clock read; a profile and a name out of the core's form are refused before
anything is made, and a bean out of the core's words is refused by its hook. The core's manifest holds GARDEN.md to its
keys and forms, and a header key in today's words is refused naming the verb that took it over.

Run: python3 test/core_adopt.py   (0 = green; about a minute)
"""
import os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
import dmparse, dmpass  # noqa: E402

FAILS = []
PY = sys.executable
VERSION = str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version'])
PIN = f"core@{VERSION}"


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None, env=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x', **(env or {}))
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e))


def text(path, root=None):
    with open(os.path.join(root or G, path), encoding='utf-8') as fh:
        return fh.read()


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def clean():
    return run('git', 'status', '--porcelain').out.strip() == ''


T = tempfile.mkdtemp(prefix='core-adopt-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden')

LAPTOP = """---
bean: laptop
genos: host
title: "laptop — Sam's ThinkPad"
status: active
summary: "Sam's daily laptop."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "PF-12345", class: hardware, establishing: true }
    - { key: hostname, value: "laptop", class: network, establishing: false }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { owner: { bean: sam } }
responsibility: { technical: { holder: { bean: sam } } }
via: [{ someone: person, outside: "Lenovo" }]
---
The laptop.
"""

try:
    # ---- THE RELEASES: v0.1.0, this tree's language in today's words; v1.0.0, the same with the core's templates
    law = dmparse.loads(dmparse.split_front_matter(text('seed/std-vocab.md', ROOT))[0])
    os.makedirs(REL)
    for f in dmpass.kept([f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, f))],
                         dmpass.language(text('seed/LANGUAGE', ROOT)), dmpass.offered(law)):
        os.makedirs(os.path.join(REL, os.path.dirname(f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(REL, f))

    def tag(t, msg):
        run('git', 'add', '-A', cwd=REL)
        run('git', 'commit', '-qm', msg, cwd=REL)
        run('git', 'tag', t, cwd=REL)
    run('git', 'init', '-q', cwd=REL)
    tag('v0.1.0', "today's words")
    for f in ('GARDEN.md.template', 'VOCAB.md.template'):
        shutil.copy2(os.path.join(ROOT, 'core', 'guide', f), os.path.join(REL, 'seed', f))
    tag('v1.0.0', 'the core')
    # ...and a release whose core forgot the manifest's `origin`: a translation it refuses
    write('core/law/core.yaml', re.sub(r'(?m)^  - \{ key: origin,[^\n]*\n', '', text('core/law/core.yaml', REL)), REL)
    tag('v1.0.1', 'a core that forgot origin')
    run('git', 'checkout', '-q', 'v0.1.0', cwd=REL)

    # ---- THE GARDEN, grown from v0.1.0, with its gardener and a laptop
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam', cwd=T)
    check("a garden grows from v0.1.0 in today's words", r.returncode == 0 and 'std-vocab@' in text('GARDEN.md'), r.out[-600:])
    write('beans/laptop.md', LAPTOP)
    write('GARDEN.md', text('GARDEN.md').replace('\nzone:', '\norigin: "a test of the adoption"\nzone:', 1))
    r = run(PY, 'bin/dmsave.py', 'sam', 'RULE-CHANGE: the laptop', '--body',
            '- action: added [[laptop]]; RULE-CHANGE: GARDEN.md says where the garden began')
    check("...and saves a laptop through today's gate", r.returncode == 0, r.out[-800:])
    head = run('git', 'rev-parse', 'HEAD').out.strip()
    run('git', 'checkout', '-q', 'v1.0.0', cwd=REL)

    def adopt(*extra, t='v1.0.0'):
        return run(PY, 'bin/dmupgrade.py', t, '--from', REL, *extra)

    def untouched():
        return clean() and run('git', 'rev-parse', 'HEAD').out.strip() == head and 'std-vocab@' in text('GARDEN.md')

    # ---- PLANNED FIRST: EACH REFUSAL TOUCHES NOTHING
    r = adopt('--extend', 'knowledge')
    check("adopting while moving a profile is refused: a profile moves in a run of its own",
          r.returncode != 0 and 'a run of its own' in r.out and untouched(), r.out[-600:])
    write('beans/loose.md', LAPTOP.replace('bean: laptop', 'bean: loose'))
    r = adopt()
    check("a bean not committed is refused, named, and nothing is touched",
          r.returncode != 0 and 'beans/loose.md' in r.out and 'not committed' in r.out
          and run('git', 'status', '--porcelain').out.strip() == '?? beans/loose.md', r.out[-600:])
    os.remove(os.path.join(G, 'beans', 'loose.md'))
    write('beans/laptop.md', LAPTOP.replace('genos: host', 'genos: no-such-genos'))
    run('git', 'commit', '-qam', 'broken, past the gate', '--no-verify')
    r = adopt()
    check("a garden that fails its own gate is refused, naming what it fails, and nothing is touched",
          r.returncode != 0 and 'does not pass its own gate' in r.out and 'no-such-genos' in r.out and clean(), r.out[-800:])
    run('git', 'reset', '-q', '--hard', head)
    c = os.path.join(T, 'old')
    shutil.copytree(G, c, ignore=shutil.ignore_patterns('.git'))
    write('seed/std-vocab.md', re.sub(r'(?m)^version: "[^"]*"', 'version: "31.0"', text('seed/std-vocab.md', c), count=1), c)
    r = run(PY, os.path.join(REL, 'core', 'translate.py'), 'garden', c, os.path.join(T, 'old-copy'))
    check("the translator refuses a garden in words it does not read (std-vocab 31), writing no copy",
          r.returncode != 0 and 'std-vocab 31.0' in r.out and 'reads the words of std-vocab 32' in r.out
          and not os.path.exists(os.path.join(T, 'old-copy')), r.out[-600:])

    # ---- A CORE THAT REFUSES THE TRANSLATION: EVERY FILE PUT BACK, AND TODAY'S HOOKS
    hooks = lambda: [open(os.path.join(G, '.git', 'hooks', h), 'rb').read() for h in sorted(os.listdir(
        os.path.join(G, '.git', 'hooks'))) if not h.endswith('.sample')]
    was = hooks()
    r = adopt(t='v1.0.1')
    check("a release whose core refuses the translation puts every file back (`origin` is no key of its manifest), and "
          "the garden's own hooks", r.returncode == 1 and 'NOT ADOPTED' in r.out and '`origin` is no key of the manifest'
          in r.out and untouched() and hooks() == was, r.out[-1200:] + run('git', 'status', '--porcelain').out)

    # ---- THE ADOPTION
    r = adopt()
    check("v1.0.0 is adopted: the count says every value placed, and the core's gate passes the garden",
          r.returncode == 0 and 'adopted the core at v1.0.0' in r.out and re.search(r'(\d+) values, \1 placed', r.out)
          and '0 problem(s)' in r.out and re.search(r'core check: garden: 2 beans, \d+ statements — 0 error\(s\)', r.out),
          r.out[-1200:])
    g, v = text('GARDEN.md'), text('VOCAB.md')
    check(f"GARDEN.md pins the core's version ({PIN}) and records the release; VOCAB.md holds no pin",
          re.search(rf'(?m)^extends: {re.escape(PIN)}\s*$', g) and 'daftar_release: "v1.0.0"' in g
          and not re.search(r'(?m)^extends:', v), g[:300] + v[:300])
    sam, laptop = (read.document(os.path.join(G, 'beans', b + '.md'))[0] for b in ('sam', 'laptop'))
    verbs = [next(iter(s)) for s in laptop.get('statements') or []]
    check("the beans are in statements: the laptop read, named, owned and answered for",
          laptop.get('kind') == 'host' and {'read', 'name', 'own', 'answer'} <= set(verbs) and 'genos' not in laptop
          and sam.get('kind') == 'person', verbs)
    hook = open(os.path.join(G, '.git', 'hooks', 'pre-commit'), encoding='utf-8').read()
    check("the hooks are the ones that take the law by the pin (bin/check.py), and the merge driver is installed",
          'bin/check.py' in hook and os.path.isfile(os.path.join(G, '.git', 'hooks', 'pre-merge-commit'))
          and 'bin/merge.py' in run('git', 'config', '--get', 'merge.daftar.driver').out, hook[-300:])
    entry = text('log/journal.md').split('\n## ')[-1]
    check("nothing is committed; the entry says RULE-CHANGE, quotes the count, names every bean and asks a person two "
          "things", run('git', 'rev-parse', 'HEAD').out.strip() == head and 'RULE-CHANGE' in entry
          and '- count: ' in entry and re.search(r'- beans: .*\blaptop\b', entry) and re.search(r'- beans: .*\bsam\b', entry)
          and entry.count('(fill in') == 2, entry[:1200])
    run('git', 'add', '-A')
    r = run('git', 'commit', '-qm', 'the core adopted')
    check("the commit is refused while the entry holds its `fill in`s", r.returncode != 0 and 'kept' in r.out
          and '(fill in' in r.out and run('git', 'rev-parse', 'HEAD').out.strip() == head, r.out[-800:])
    write('log/journal.md', text('log/journal.md').replace(
        "- ratified_by: (fill in who ratified — the gardener's word, given here)", '- ratified_by: sam, here').replace(
        '- why: (fill in — what adopting the core brings this garden)', '- why: the core is the language'))
    run('git', 'add', '-A')
    r = run('git', 'commit', '-qm', 'RULE-CHANGE: the core adopted')
    check("...and passes the core's gate once a person has filled them",
          r.returncode == 0 and re.search(r'core check --staged: 2 beans, \d+ statements — 0 error\(s\)', r.out), r.out[-1200:])
    laptop = read.document(os.path.join(G, 'beans', 'laptop.md'))[0]
    at = next((next(iter(s.values())).get('at') for s in laptop['statements'] if next(iter(s)) == 'read'), None)
    first = [ln[3:].split(' · ', 1)[0] for ln in text('log/journal.md').split('\n') if ln.startswith('## ')]
    check("the laptop's act carries the moment history recorded (its save's heading), granted to the adoption once",
          isinstance(at, str) and at in first[:-1], (at, first))

    # ---- AFTERWARDS
    r = run(PY, 'bin/daftar.py', 'check')
    check("afterwards `daftar check` is the core's gate", r.returncode == 0 and 'core check: garden' in r.out, r.out[-400:])
    r = adopt()
    check("...and adopting v1.0.0 again is nothing to do", r.returncode == 0 and 'nothing to do' in r.out and clean(),
          r.out[-400:])

    # ---- A GARDEN GROWN FROM A RELEASE OF THE CORE STARTS IN IT
    N = os.path.join(T, 'grown')
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), N, '--gardener', 'ada', '--gardener-name', 'Ada', cwd=T)
    log = run('git', 'log', '--format=%s', cwd=N).out.strip().split('\n')
    ada = read.document(os.path.join(N, 'beans', 'ada.md'))[0] if os.path.isfile(os.path.join(N, 'beans', 'ada.md')) else {}
    say = next((next(iter(s.values())) for s in ada.get('statements') or [] if next(iter(s)) == 'say'), {})
    check(f"a garden grown from v1.0.0 pins {PIN} from its first commit, and its gate is the core's",
          r.returncode == 0 and f'({PIN}, daftar v1.0.0)' in r.out and 'core check: grown: 1 beans' in r.out
          and re.search(rf'(?m)^extends: {re.escape(PIN)}', text('GARDEN.md', N)) and log[-1].endswith(f'at {PIN}. No beans.'),
          r.out[-800:])
    check("...its gardener planted in statements and saved, the moment the clock read in place of `now`",
          ada.get('kind') == 'person' and say.get('by') == 'ada' and say.get('at') not in (None, 'now')
          and log[0] == 'the gardener: [[ada]]' and '(fill in' not in text('log/journal.md', N), (ada, log))
    write('beans/box.md', LAPTOP.replace('bean: laptop', 'bean: box'), N)
    r = run(PY, 'bin/dmsave.py', 'ada', 'a box', '--body', '- action: added [[box]]', cwd=N)
    check("...and a bean in today's words is refused by its hook, the core's gate naming the verb that took a word over",
          r.returncode != 0 and 'core check --staged' in r.out and '`owned_by` is the verb `own` of the face' in r.out,
          r.out[-1200:])
    O = os.path.join(T, 'grown-org')
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), O, '--gardener', 'acme', '--gardener-name', 'Acme Ltd',
            '--gardener-genos', 'org', cwd=T)
    acme = read.document(os.path.join(O, 'beans', 'acme.md'))[0] if os.path.isfile(os.path.join(O, 'beans', 'acme.md')) else {}
    owns = [next(iter(s.values())) for s in acme.get('statements') or [] if next(iter(s)) == 'own']
    check("...an organisation that keeps one is owned by its members, outside the garden",
          r.returncode == 0 and acme.get('kind') == 'org' and owns and owns[0].get('by') == {'someone': 'person'}, r.out[-800:])
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), os.path.join(T, 'p'), '--profile', 'knowledge', cwd=T)
    r2 = run(PY, os.path.join(REL, 'seed', 'germinate.py'), os.path.join(T, 'Bad_Name'), cwd=T)
    check("...a profile at birth waits for part 11, and a name out of the core's form is refused; nothing is made",
          r.returncode != 0 and 'part 11' in r.out and r2.returncode != 0 and 'kebab-case' in r2.out
          and not os.path.exists(os.path.join(T, 'p')) and not os.path.exists(os.path.join(T, 'Bad_Name')), r.out + r2.out)

    # ---- THE LAW'S VERSION AND THE MANIFEST'S FORMS, proved with the law
    from core.law import Law
    face = read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))
    face = dict(face, version='one', manifest=face['manifest'] + [{'key': 'motto', 'form': 'slogan'}])
    probs = Law(face, read.data(os.path.join(ROOT, 'core', 'law', 'verbs.yaml'))).problems()
    check("the law proves its version (`<major>.<minor>`, which a garden pins) and that each key of the manifest has a "
          "form", any(w == 'core.yaml version' for _r, w, _m in probs)
          and any(w == 'core.yaml manifest motto' and 'slogan' in m for _r, w, m in probs), probs)

    # ---- THE CORE'S MANIFEST, judged on a garden of the core
    M = os.path.join(T, 'manifest')
    shutil.copytree(N, M, ignore=shutil.ignore_patterns('.git'))
    os.remove(os.path.join(M, 'beans', 'box.md'))
    write('GARDEN.md', text('GARDEN.md', M).replace(f'extends: {PIN}', 'extends: core@0.9').replace(
        'daftar_release: "v1.0.0"', 'daftar_release: "1.0"').replace('\nzone:', '\nmodels: [x]\nzone:'), M)
    r = run(PY, os.path.join(ROOT, 'core', 'check.py'), M, cwd=M)
    check("the core holds GARDEN.md to the manifest: its keys alone, the law's own pin, a release's form",
          r.returncode == 1 and '`models` is no key of the manifest' in r.out
          and f'`extends: core@0.9` — a garden of statements runs this law, `{PIN}`' in r.out
          and '`daftar_release: 1.0` — a release' in r.out, r.out)
    write('GARDEN.md', re.sub(r'(?m)^zone:.*\n', '', text('GARDEN.md', M)), M)
    r = run(PY, os.path.join(ROOT, 'core', 'check.py'), M, cwd=M)
    check("...and a key it requires", '`zone:` is missing — the manifest requires it' in r.out, r.out)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_adopt: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
