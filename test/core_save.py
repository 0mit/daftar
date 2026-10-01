#!/usr/bin/env python3
"""The core's save: today's bin/dmsave.py commits a garden written in statements, with the core's gate at the commit.

Grows a garden of the core's beans (bin/, core/ and the standards copied from this release), installs the core's
pre-commit gate (core/install.py), and saves through bin/dmsave.py, which journals, stamps, stages and commits in one
call. Checks that a knowing act's `at: now` is written as the moment of the heading the save wrote; that a moment typed
there is refused, and saved once it is `now`; that a bean the entry does not name is refused; that a statement added
under an old act is refused until an act of this commit knows it; that a change to the law is refused until an entry
says RULE-CHANGE; that the engine's own refusals stop the commit; that a heading typed into the journal by hand is
refused; and that what is judged is the index, not the working tree.
"""
import os, re, shutil, subprocess, sys, tempfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from core import read  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1200]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='dmcoresave-')
G = os.path.join(T, 'g')


def run(*a, stdin=None):
    return subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=G, input=stdin)


def git(*a):
    return run('git', *a)


def write(rel, head, body='\nWords.\n'):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        fh.write('---\n' + yaml.safe_dump(head, allow_unicode=True, sort_keys=False, width=200) + '---\n' + body)


def text(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def bean(bid, kind, statements):
    write(f"beans/{bid}.md", {'bean': bid, 'kind': kind, 'title': bid, 'statements': statements})


def save(who, what, body):
    r = run(PY, 'bin/dmsave.py', who, what, '--body', body)
    r.out = r.stdout + r.stderr          # git hands a hook's output to stderr
    return r


def head_bean(bid):
    show = git('show', f"HEAD:beans/{bid}.md").stdout
    return read.loads(show.split('---\n')[1]) if show.startswith('---') else {}


def last_heading():
    return [l for l in text('log/journal.md').split('\n') if l.startswith('## ')][-1]


def reset():
    git('reset', '-q', '--hard', 'HEAD')
    git('clean', '-qfd')


try:
    os.makedirs(G)
    git('init', '-q')
    git('config', 'user.name', 'sam')
    git('config', 'user.email', 'sam@example.invalid')
    ignore = shutil.ignore_patterns('__pycache__')
    shutil.copytree(os.path.join(ROOT, 'bin'), os.path.join(G, 'bin'), ignore=ignore)
    shutil.copytree(os.path.join(ROOT, 'core'), os.path.join(G, 'core'), ignore=ignore)
    os.makedirs(os.path.join(G, 'seed'))
    for f in ('std-vocab.md', 'LANGUAGE'):
        shutil.copy(os.path.join(ROOT, 'seed', f), os.path.join(G, 'seed', f))
    shutil.copytree(os.path.join(ROOT, 'seed', 'knowledge'), os.path.join(G, 'seed', 'knowledge'))
    CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
    write('GARDEN.md', {'garden': 'core-save', 'extends': 'std-vocab@32.0', 'gardener': 'sam', 'zone': 'Asia/Tehran'}, '')
    write('VOCAB.md', dict({'vocab': 'core-save', 'extends': 'std-vocab@32.0'}, **CASES['vocab']), '')
    os.makedirs(os.path.join(G, 'log'))
    with open(os.path.join(G, 'log', 'journal.md'), 'w', encoding='utf-8') as fh:
        fh.write('# Journal\n')
    git('add', '-A')
    git('commit', '-q', '--no-verify', '-m', 'the garden, before its first bean')
    r = run(PY, 'core/install.py')
    check("core/install.py installs the core's gate as this clone's pre-commit",
          r.returncode == 0 and 'core/check.py --staged' in open(os.path.join(G, '.git', 'hooks', 'pre-commit')).read(),
          r.stdout + r.stderr)

    # A FIRST BEAN: `at: now` becomes the moment of the heading the save wrote
    bean('sam', 'person', [{'say': {'by': 'sam', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = save('sam', "sam's own record", '- action: wrote [[sam]], the gardener')
    h = last_heading()
    moment = h[3:].split(' · ', 1)[0]
    at = (head_bean('sam').get('statements') or [{}])[0].get('say', {}).get('at')
    check(f"a save commits a bean of statements, its `at: now` written as the heading's moment ({moment})",
          r.returncode == 0 and at == moment, (r.returncode, at, moment, r.stdout + r.stderr))

    # A MOMENT TYPED IS REFUSED, AND SAVED ONCE IT IS `now`
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': '2026-10-01 10:00+03:30'}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = save('sam', "ben's record", '- action: wrote [[ben]]')
    check("a knowing act's moment typed by hand is refused: the moment is the save's",
          r.returncode == 1 and 'knowing' in r.out and 'is no moment' in r.out, r.stdout + r.stderr)
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = run(PY, 'bin/dmsave.py', '--again')
    at = (head_bean('ben').get('statements') or [{}])[0].get('say', {}).get('at')
    check("...and once it says `now`, --again saves it at the waiting entry's moment",
          r.returncode == 0 and at == last_heading()[3:].split(' · ', 1)[0], (r.returncode, at, r.stdout + r.stderr))

    # A BEAN NO ENTRY NAMES
    bean('ada', 'person', [{'say': {'by': 'ada', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = save('sam', 'a record', '- action: wrote a record')
    check("a bean the entry does not name is refused", r.returncode == 1 and 'named by no journal entry' in r.out,
          r.stdout + r.stderr)
    reset()

    # A STATEMENT ADDED UNDER AN OLD ACT
    bean('sam', 'person', [{'say': {'by': 'sam', 'at': moment}}, {'own': {'by': 'theone', 'of': 'self'}},
                           {'do': {'by': 'self', 'as': 'workstation'}}])
    r = save('sam', 'what sam does', '- action: [[sam]] does a job')
    check("a statement added under an old act is refused: its act's moment is older than it",
          r.returncode == 1 and 'known by no act it adds' in r.out, r.stdout + r.stderr)
    bean('sam', 'person', [{'say': {'by': 'sam', 'at': moment}}, {'own': {'by': 'theone', 'of': 'self'}},
                           {'say': {'by': 'sam', 'of': ['job'], 'at': 'now'}}, {'do': {'id': 'job', 'by': 'self', 'as': 'workstation'}}])
    r = run(PY, 'bin/dmsave.py', '--again')
    check("...and saved once an act of this commit knows it", r.returncode == 0, r.stdout + r.stderr)

    # THE LAW: a RULE-CHANGE
    with open(os.path.join(G, 'VOCAB.md'), encoding='utf-8') as fh:
        v = fh.read()
    with open(os.path.join(G, 'VOCAB.md'), 'w', encoding='utf-8') as fh:
        fh.write(v.replace('kinds:\n', 'kinds:\n- {kind: boat, nature: body, line: made, level: device}\n', 1))
    r = save('sam', 'a boat is a kind', '- action: the kind boat, for the garden')
    check("a change to the law with no RULE-CHANGE said is refused by `ratify`",
          r.returncode == 1 and 'ratify' in r.out, r.stdout + r.stderr)
    r = run(PY, 'bin/dmjournal.py', 'sam', 'RULE-CHANGE ratified', '--body', '- action: RULE-CHANGE, the kind boat; ratified by sam')
    r = run(PY, 'bin/dmsave.py', '--again')
    check("...and saved once an entry says RULE-CHANGE", r.returncode == 0, r.stdout + r.stderr)

    # THE ENGINE'S OWN REFUSALS STOP THE COMMIT
    bean('x', 'document', [{'say': {'by': 'sam', 'at': 'now'}}, {'pay': {'by': 'nobody', 'of': {'count': '1', 'unit': 'XTS'}}}])
    r = save('sam', 'a payment', '- action: [[x]] records a payment')
    check("a bean the engine refuses (a being that is no bean) is not committed",
          r.returncode == 1 and 'valency' in r.out and "'nobody' is no bean" in r.out, r.stdout + r.stderr)
    reset()

    # A HEADING TYPED BY HAND
    with open(os.path.join(G, 'log', 'journal.md'), 'a', encoding='utf-8') as fh:
        fh.write('\n## 2026-10-01 10:00+03:30 · sam · typed\n- action: a heading typed by hand\n')
    git('add', '-A')
    r = git('commit', '-q', '-m', 'typed')
    check("a heading typed into the journal by hand is refused: the clock writes it",
          r.returncode != 0 and 'not written by the clock' in r.stdout + r.stderr, r.stdout + r.stderr)
    reset()

    # THE INDEX IS JUDGED, NOT THE WORKING TREE
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}},
                           {'pay': {'by': 'ghost', 'of': '1'}}])
    git('add', 'beans/ben.md')
    bean('ben', 'person', [{'say': {'by': 'ben', 'at': 'now'}}, {'own': {'by': 'theone', 'of': 'self'}}])
    r = run(PY, 'core/check.py', '--staged')
    check("core/check.py --staged judges what is staged, not what the working tree holds",
          r.returncode == 1 and "'ghost' is no bean" in r.stdout, r.stdout)
    reset()
    r = run(PY, 'core/check.py')
    check("the garden as saved passes the core's check", r.returncode == 0, r.stdout)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_save: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
