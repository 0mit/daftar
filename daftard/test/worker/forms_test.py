#!/usr/bin/env python3
"""The worker's served forms (design §10.5), in a real garden of the core: a form opened to Ana by a `grant … as: write`
for an extent; she sees its questions and nothing else; her answers are laid outside the garden, never written into it;
they wait as a lead for the gardener; and the gardener's save takes them as a document of her own words, through the
garden's own gate. A form whose grant has ended, or one never opened to her, is not hers to answer.

    python3 test/worker/forms_test.py [<daftar tree>]     # the tree a garden is grown from (default ~/daftar)

The worker's code under test is exec'd from python/garden_worker.py; what it stands on outside (the board's title
reader, the save lock, the clock check) is stood in for, and the garden's own tools are real.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test

T = Path(tempfile.mkdtemp(prefix='worker-forms-'))
FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-1200:]))
    if not cond:
        FAILS.append(name)


try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    today = time.strftime('%Y-%m-%d')
    (G / 'beans' / 'ana.md').write_text(
        '---\nbean: ana\nkind: person\ntitle: "Ana"\nstatements:\n  - say: { by: sam, at: now }\n'
        '  - own: { by: theone, of: self }\n  - answer: { by: self, of: self, as: law }\n---\nAna.\n', encoding='utf-8')
    (G / 'beans' / 'ana-consent.md').write_text(
        '---\nbean: ana-consent\nkind: contract\ntitle: "Ana agrees to be kept here by name"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
        '  - agree: { id: ana-agrees, by: ana, of: "kept here by name", through: spoken }\n'
        '  - agree: { id: sam-agrees, by: sam, of: "kept here by name", through: spoken }\n---\nHer word.\n', encoding='utf-8')
    for form, title in (('intake', 'the intake questions'), ('old-survey', 'last year\'s survey'), ('books', 'the books')):
        (G / 'beans' / f'{form}.md').write_text(
            f'---\nbean: {form}\nkind: document\ntitle: "{title}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
            f'  - own: {{ by: sam, of: self }}\n---\n# {title}\n\n1. What do you do?\n\n---\n\n2. What do you need from us?\n',
            encoding='utf-8')                       # a rule between the questions is the text's own, not a fence
    sam = (G / 'beans' / 'sam.md').read_text(encoding='utf-8')
    (G / 'beans' / 'sam.md').write_text(sam.replace('\n---\n', (
        f'\n  - grant: {{ id: ana-intake, by: self, as: write, of: [intake], to: [ana], at: "{today}/2099-12-31" }}\n'
        '  - grant: { id: ana-old, by: self, as: write, of: [old-survey], to: [ana], at: "2020-01-01/2020-12-31" }\n'
        '  - say: { by: sam, of: [ana-intake, ana-old], at: now }\n---\n'), 1), encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'Ana, and two forms opened to her', '--body',
                 '- action: wrote [[ana]] (kept on her word, [[ana-consent]]), [[intake]], [[old-survey]] and [[books]]; [[sam]] opens [[intake]] to Ana '
                 'from today, and opened [[old-survey]] in 2020', cwd=str(G))
    check('the garden holds Ana, the forms and the grants, through its gate', r.returncode == 0 and s.returncode == 0,
          r.out[-600:] + s.out[-1200:])

    # the worker's served part, run in that garden
    os.chdir(G)
    os.environ['DAFTAR_MAILBOX'] = str(T / 'mailboxes')
    src = open(os.path.join(HERE, '..', '..', 'python', 'garden_worker.py'), encoding='utf-8').read()
    part = src[src.index('PERSON = re.compile('):src.index("ACTION_ID = re.compile(")]

    class Refused(Exception):
        def __init__(self, message, status=400):
            super().__init__(message)
            self.status = status

    class Lock:
        def __exit__(self, *a):
            return False

    def git(*args):
        return subprocess.run(['git', *args], cwd=G, capture_output=True, text=True, encoding='utf-8').stdout.strip()

    def run_save(who, what, body):
        p = subprocess.run([sys.executable, 'bin/save.py', who, what, '--body', *body], cwd=G, capture_output=True,
                           text=True, encoding='utf-8', env=grow.ENV)
        return p.returncode == 0, p.stdout + p.stderr

    def title_of(b):
        m = re.search(r'^title: "?(.*?)"?$', (G / 'beans' / f'{b}.md').read_text(encoding='utf-8'), re.M)
        return m.group(1) if m else b

    ns = dict(re=re, os=os, sys=sys, json=json, time=time, shutil=shutil, Path=Path, ROOT=G, Refused=Refused,
              SLUG=re.compile(r'[a-z0-9][a-z0-9-]{0,120}'), BUSY='busy', title_of=title_of, git=git, run_save=run_save,
              identity=lambda: {'garden_id': '0123456789ab'}, gardener=lambda: 'sam', clock=lambda p: {'may': True},
              save_lock=lambda wait=10: Lock(), already=lambda rid: '', request_id=lambda p: uuid.uuid4().hex,
              refused_save=lambda said: Refused(said[-600:], 422))
    exec(compile(part, 'garden_worker.py', 'exec'), ns)

    forms = ns['served_forms']({'person': 'ana'})
    check("Ana sees the form opened to her now, with its questions, a rule between them read as text — not one whose "
          "grant ended, nor one never opened",
          [f['id'] for f in forms] == ['intake'] and forms[0]['questions'] == ['What do you do?', 'What do you need from us?'],
          forms)
    for form in ('books', 'old-survey'):
        try:
            ns['served_submit']({'person': 'ana', 'id': form, 'answers': ['a', 'b']})
            check(f'answering {form} is refused', False)
        except Refused as e:
            check(f'answering {form}, which is not open to her, is refused', e.status == 403, e)
    try:
        ns['served_submit']({'person': 'ana', 'id': 'intake', 'answers': ['I teach', 'a room\u202e']})
        check('an answer carrying a bidi control is refused', False)
    except Refused as e:
        check('an answer carrying a bidi control is refused, nothing laid', e.status == 400
              and not (T / 'mailboxes').exists(), e)
    head = git('rev-parse', 'HEAD')
    got = ns['served_submit']({'person': 'ana', 'id': 'intake', 'answers': ['I teach yoga.', 'A room on Tuesdays.\nAnd a key.']})
    box = T / 'mailboxes' / '0123456789ab' / 'forms'
    check('her answers are laid outside the garden, nothing written in it', got['laid'] and (box / (got['laid'] + '.md')).is_file()
          and git('rev-parse', 'HEAD') == head and git('status', '--porcelain') == '', got)
    again = ns['served_forms']({'person': 'ana'})
    check('the page shows her what she gave, while it waits', again[0]['given'] == ['I teach yoga.', 'A room on Tuesdays.\nAnd a key.'],
          again)
    leads = ns['form_leads']()
    check('it waits as a lead for the gardener', len(leads) == 1 and leads[0]['kind'] == 'form'
          and leads[0]['id'] == got['laid'], leads)
    shown = ns['form_answers']({'id': got['laid']})
    check("the gardener's page reads it: who, which form, when, each question with its answer",
          shown['person'] == 'ana' and shown['questions'][1]['a'].endswith('And a key.'), shown)
    taken = ns['take_form']({'id': got['laid'], 'request': uuid.uuid4().hex})
    bean = (G / 'beans' / f"{taken['bean']}.md").read_text(encoding='utf-8')
    g = subprocess.run([sys.executable, 'bin/check.py'], cwd=G, capture_output=True, text=True, encoding='utf-8')
    check("the gardener's save takes it: a document of her own words, as given, through the garden's gate",
          taken['saved'] and git('rev-parse', 'HEAD') != head and 'A room on Tuesdays.' in bean and 'concern:' in bean
          and 'through: served' in bean and g.returncode == 0 and not (box / (got['laid'] + '.md')).exists()
          and (box / 'taken' / (got['laid'] + '.md')).is_file(), bean + g.stdout[-600:])
    check('and no longer waits', ns['form_leads']() == [], ns['form_leads']())
finally:
    os.chdir('/')
    shutil.rmtree(T, ignore_errors=True)

print(f"\nforms: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
