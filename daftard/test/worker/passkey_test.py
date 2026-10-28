#!/usr/bin/env python3
"""The worker's passkeys, in a real garden of the core whose law has the namespace `passkey`: a passkey Ana made is
laid outside the garden and waits as a lead; the gardener's save names it in her bean (class F) through the garden's
own gate; from then the sign-in reads it there, and nothing else.

    python3 test/worker/passkey_test.py [<daftar tree with the passkey namespace>]   (default ~/daftar-passkey)
"""
import base64
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
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar-passkey')
sys.path.insert(0, os.path.join(TREE, 'test'))
import grow  # noqa: E402

T = Path(tempfile.mkdtemp(prefix='worker-passkey-'))
FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-1200:]))
    if not cond:
        FAILS.append(name)


b64 = lambda b: base64.urlsafe_b64encode(b).decode().rstrip('=')
try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam')
    (G / 'beans' / 'ana.md').write_text(
        '---\nbean: ana\nkind: person\ntitle: "Ana"\nstatements:\n  - say: { by: sam, at: now }\n'
        '  - own: { by: theone, of: self }\n  - answer: { by: self, of: self, as: law }\n---\nAna.\n', encoding='utf-8')
    (G / 'beans' / 'ana-consent.md').write_text(
        '---\nbean: ana-consent\nkind: contract\ntitle: "Ana agrees to be kept here by name"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
        '  - agree: { id: ana-agrees, by: ana, of: "kept here by name", through: spoken }\n'
        '  - agree: { id: sam-agrees, by: sam, of: "kept here by name", through: spoken }\n---\nHer word.\n', encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'Ana, kept on her word', '--body',
                 '- action: wrote [[ana]], kept on her word ([[ana-consent]])', cwd=str(G))
    check('the garden holds Ana, through its gate', r.returncode == 0 and s.returncode == 0, r.out[-400:] + s.out[-800:])
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

    ns = dict(re=re, os=os, sys=sys, json=json, time=time, shutil=shutil, subprocess=subprocess, Path=Path, ROOT=G,
              Refused=Refused, SLUG=re.compile(r'[a-z0-9][a-z0-9-]{0,120}'), BUSY='busy', git=git, run_save=run_save,
              title_of=lambda b: b.title(), identity=lambda: {'garden_id': '0123456789ab'}, gardener=lambda: 'sam',
              clock=lambda p: {'may': True}, save_lock=lambda wait=10: Lock(), already=lambda rid: '',
              request_id=lambda p: uuid.uuid4().hex, refused_save=lambda said: Refused(said[-800:], 422))
    exec(compile(part, 'garden_worker.py', 'exec'), ns)

    cose = bytes([0xa5, 0x01, 0x02, 0x03, 0x26, 0x20, 0x01, 0x21, 0x58, 0x20]) + os.urandom(32) + bytes([0x22, 0x58, 0x20]) + os.urandom(32)
    anchor = b64(os.urandom(32)) + '.' + b64(cose)
    check('a passkey her bean does not name signs nothing in', ns['served_passkeys']({'person': 'ana'}) == [])
    head = git('rev-parse', 'HEAD')
    laid = ns['passkey_lay']({'person': 'ana', 'anchor': anchor})
    check('the passkey she made is laid outside the garden, nothing written in it',
          laid['laid'] and git('rev-parse', 'HEAD') == head and git('status', '--porcelain') == '', laid)
    leads = ns['passkey_leads']()
    check('it waits as a lead for the gardener', len(leads) == 1 and leads[0]['kind'] == 'passkey', leads)
    try:
        ns['passkey_lay']({'person': 'ana', 'anchor': 'not-a-passkey'})
        check('what is no passkey is refused', False)
    except Refused:
        check('what is no passkey is refused', True)
    taken = ns['take_passkey']({'id': laid['laid'], 'request': uuid.uuid4().hex})
    bean = (G / 'beans' / 'ana.md').read_text(encoding='utf-8')
    g = subprocess.run([sys.executable, 'bin/check.py'], cwd=G, capture_output=True, text=True, encoding='utf-8')
    check("the gardener's save names it in her bean (class F), through the garden's own gate",
          taken['saved'] and 'by: passkey' in bean and anchor in bean and g.returncode == 0, bean + g.stdout[-600:])
    check('from then the sign-in reads it from her bean', ns['served_passkeys']({'person': 'ana'}) == [anchor])
    check('and it no longer waits', ns['passkey_leads']() == [])
    again = ns['passkey_lay']({'person': 'ana', 'anchor': anchor})
    check('the same passkey laid again is said to be hers already, nothing laid', again['laid'] == '', again)

    # every read of a bean is the garden's own parser, loaded once (the worker is restarted when a sync brings new code)
    exec(compile(src[src.index('def person(params):'):src.index('METHODS = {')], 'garden_worker.py', 'exec'), ns)
    import importlib.util
    loads, spec_of = [], importlib.util.spec_from_file_location

    def counted(name, location, *a, **k):
        if Path(location).parts[-2:] == ('bin', 'parse.py'):
            loads.append(name)
        return spec_of(name, location, *a, **k)
    importlib.util.spec_from_file_location = counted
    try:
        read = [(ns['served_passkeys']({'person': 'ana'}), ns['person']({'id': 'ana'})) for _ in range(2)]
    finally:
        importlib.util.spec_from_file_location = spec_of
    check("her passkeys and her name, read twice each, load the garden's parser once at most",
          len(loads) <= 1 and read[1] == ([anchor], {'id': 'ana', 'title': 'Ana', 'mail': ''}), (loads, read))
finally:
    os.chdir('/')
    shutil.rmtree(T, ignore_errors=True)

print(f"\npasskey: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
