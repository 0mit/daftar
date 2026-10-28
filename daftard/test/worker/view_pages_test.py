#!/usr/bin/env python3
"""A garden whose handplace is its page beans (daftard.json `handplace: "view"`): the worker reads, scopes, draws and
writes each page by THE VIEW'S OWN CODE, from the release the garden runs — run here as daftard runs it, in a real
garden of the core grown from a daftar tree (its own test/grow.py), taking the view profile.

Sam keeps the garden: a repair of a bicycle, two page beans placed first and second — what waits (a queue) and the
repair (its sheet) — and a reader kept under an opaque id, granted the first page and Sam, whose queue it draws. Then:

  view_pages   the page beans in the order their `be … as: order` places them, and what the browser loads of the
               release: the widgets, the classic scripts and their styles, each a file of the garden's assets/view/lib
               that daftard's /release/ serves (its own pattern), none of the view's Python
  view_page    Sam's page of the repair: its drawings, the readings engraved for him, the repair's sheet, the widgets'
               settings in his language; the reader's page of what waits holds no sheet of the repair, which they may
               not read; the repair's page refused to the reader, and a page that is no slug refused
  view_write   Sam's Save — the repair's summary changed — is one commit through the gate; the reader's, who may not
               write, and one the view's write path refuses (an empty title), keep nothing: the head does not move
  view_html    the view's own page of a page bean, and the scripts its asset declares — each in the page as written,
               and never a script a bean's title carries; a garden of the core asked as a legacy garden is (no page, no
               handplace) has none, as before
  view_style   the kit's style, for a page's drawings
  view_act     a page's action: a walk this machine names for its tool (daftard.json `walks`) started by the garden's
               bin/act.py with what the person gave it, its plan returned, then ratified — the receipt stamped, each
               attempt in this machine's audit record; a walk this machine does not name, refused, nothing run

    python3 test/worker/view_pages_test.py [<daftar tree>]     # a tree whose view draws pages of readings (default ~/daftar)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test

FAILS = []
# what daftard's /release/<garden>/ serves of a garden's assets/view/lib (internal/web/viewpages.go `releaseFile`)
RELEASE_FILE = re.compile(r'^(widgets/[a-z]+\.(js|css|woff2)|view_[a-z]+\.(js|css))$')
READER = 'p-0a1b2c3d'


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-1200:]))
    if not cond:
        FAILS.append(name)


WALK = '''---
bean: action-stamp
kind: procedure
title: "action-stamp — a receipt stamped with words a person gives"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: stamp-tool }
  - step: { id: plan, as: "what would be written", by: engine, to: [show] }
  - step: { id: show, as: "the plan", by: engine, to: [check] }
  - step: { id: check, as: "the words are there", by: engine, to: [ratify] }
  - step: { id: ratify, as: "a person ratifies it", by: ratifier, to: [apply, show] }
  - step: { id: apply, as: "the words written", by: engine, to: [verify] }
  - step: { id: verify, as: "read back", by: engine, to: [done] }
  - step: { id: done, as: "stamped", walk: { final: "true" } }
  - step: { id: refused, as: "nothing was changed", walk: { exit: "true", reasons: [cannot-plan, check-failed, declined] } }
  - step: { id: rolled-back, as: "restored", walk: { exit: "true", reasons: [apply-failed, verify-mismatch] } }
---
How a receipt is stamped.
'''
STAMP = r'''import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))
import walktool as W
words = lambda: W.inputs().get('words', '').strip()
def plan(bean, course): print('+ ' + bean + ': Stamped: ' + words())
def check(bean, course):
    if not words(): raise W.Refused('no words')
def apply(bean, course):
    open(W.shown()).read()
    with open(os.path.join('beans', bean + '.md'), 'a', encoding='utf-8') as fh: fh.write('Stamped: ' + words() + chr(10))
    W.save('sam', 'stamped ' + bean, ['- action: stamped [[' + bean + ']]'])
def verify(bean, course):
    if 'Stamped: ' + words() not in open(os.path.join('beans', bean + '.md'), encoding='utf-8').read(): raise W.Refused('not read back')
def restore(bean, course): pass
sys.exit(W.main('stamp', {'plan': plan, 'check': check, 'apply': apply, 'verify': verify, 'restore': restore}))
'''

if not os.path.isfile(os.path.join(TREE, 'assets', 'view', 'lib', 'view_engraved.py')):
    print(f"view pages: {TREE} has no assets/view/lib/view_engraved.py — give a tree whose view draws pages of readings")
    sys.exit(2)
T = Path(tempfile.mkdtemp(prefix='worker-view-pages-'))
try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam', '--profile', 'view')
    STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
             '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')


    def put(rel_path, text):
        p = G / rel_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding='utf-8')


    def head():
        return subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=G, capture_output=True, text=True).stdout.strip()


    put(f'beans/{READER}.md', f'---\nbean: {READER}\nkind: person\ntitle: "{READER}"\nsummary: "a reader of the garden\'s '
        f'pages"\nstatements:\n  - say: {{ by: sam, at: now }}\n  - own: {{ by: theone, of: self }}\n---\nA reader.\n')
    put('beans/repair-1.md', '---\nbean: repair-1\nkind: contract\ntitle: "repair-1 <script>stolen()</script>"\nsummary: '
        '"Sam mends a bicycle"\nstatements:\n  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\nA repair.\n')
    for bid, place, draw in (
            ('page-now', 1, f'  - draw: {{ id: waits, by: self, of: [sam], drawing: {{ label: Now, archetype: queue, {STORY.format(p="what waits")} }} }}\n'
                            '  - draw: { id: page, by: self, of: [waits], page: { visibility: private } }\n'),
            ('page-repair', 2, f'  - draw: {{ id: repair, by: self, of: [repair-1], drawing: {{ label: Repair, archetype: sheet, {STORY.format(p="the repair")} }} }}\n'
                               '  - draw: { id: page, by: self, of: [repair], page: { visibility: private, fields: [ { kind: contract, fact: summary, shown_from: understand } ] } }\n')):
        put(f'beans/{bid}.md', f'---\nbean: {bid}\nkind: service\ntitle: "{bid}"\nsummary: "a page"\nstatements:\n'
            f'  - say: {{ by: sam, at: now }}\n  - own: {{ by: sam, of: self }}\n'
            f'  - be: {{ by: self, at: "uri:http://127.0.0.1:8770/", as: location }}\n'
            f'  - be: {{ by: self, at: "ordinal:{place}", as: order }}\n' + draw + '---\nA page.\n')
    sam = (G / 'beans' / 'sam.md').read_text(encoding='utf-8')
    (G / 'beans' / 'sam.md').write_text(sam.replace('\n---\n', f'\n  - grant: {{ id: reader-reads, by: self, to: [{READER}], of: [page-now, sam], as: read }}\n'
                                                    '  - say: { by: sam, of: [reader-reads], at: now }\n---\n', 1), encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'a repair, two pages, and a reader of the first', '--body',
                 f'- action: wrote [[repair-1]], [[page-now]], [[page-repair]] and [[{READER}]]; [[sam]] opens [[page-now]] to the reader',
                 cwd=str(G))
    check('a garden of the core taking the view profile holds a repair, two pages and a reader, through its gate',
          r.returncode == 0 and s.returncode == 0, r.out[-600:] + s.out[-1200:])

    sys.path.insert(0, HERE)
    from odoo_worker import Worker  # noqa: E402 — the worker as daftard runs it
    w = Worker(G, scratch=str(T))
    try:
        # ------------------------------------------------------------------ view_pages
        got = w.call('view_pages', {})
        pages = [p.get('bean') for p in (got or {}).get('pages') or []]
        a = (got or {}).get('assets') or {}
        files = [f'widgets/{n}.js' for n in a.get('widgets') or []] + list(a.get('scripts') or []) + list(a.get('styles') or [])
        lib = G / 'assets' / 'view' / 'lib'
        check("view_pages: the page beans in the order their `be … as: order` places them", pages == ['page-now', 'page-repair'], got)
        check("...and what the browser loads of the release: the widgets, the renderers, the runtime and their styles, each a "
              "file of the garden's assets/view/lib that daftard's /release/ serves, none of the view's Python",
              {'widgets/direction.js', 'view_engraved.js', 'view_queue.js', 'view_sheet.js', 'view_runtime.js', 'view_engraved.css'} <= set(files)
              and 'safe' in (a.get('widgets') or []) and all(RELEASE_FILE.match(f) and (lib / f).is_file() for f in files), files)

        # ------------------------------------------------------------------ view_page
        P = w.call('view_page', {'page': 'page-repair', 'reader': 'sam', 'lang': 'fa'}) or {}
        E = P.get('engraved') or {}
        check("view_page: Sam's page of the repair — its drawing, the repair's sheet, the widgets' settings in his language",
              'repair' in (P.get('views') or {}) and 'repair-1' in (E.get('sheets') or {})
              and ((E.get('settings') or {}).get('garden') or {}).get('lang') == 'fa', {k: P.get(k) for k in ('error', 'order')})
        Q = w.call('view_page', {'page': 'page-now', 'reader': READER, 'lang': 'en'}) or {}
        check("...the reader's page of what waits, and no sheet of the repair, which they may not read",
              'waits' in (Q.get('views') or {}) and 'repair-1' not in ((Q.get('engraved') or {}).get('sheets') or {})
              and 'Sam mends' not in str(Q), Q.get('error') or sorted(Q))
        X = w.call('view_page', {'page': 'page-repair', 'reader': READER, 'lang': 'en'}) or {}
        Y = w.call('view_page', {'page': '../beans', 'reader': 'sam', 'lang': 'en'}) or {}
        check("...the repair's page refused to the reader, and a page that is no slug refused", 'error' in X and 'views' not in X
              and 'error' in Y and 'views' not in Y, (X, Y))

        # ------------------------------------------------------------------ view_write
        before = head()
        ok = w.call('view_write', {'reader': 'sam', 'body': {'bean': 'repair-1', 'ops': [{'op': 'change', 'header': 'summary', 'value': 'mended, and collected'}]}}) or {}
        after = head()
        check("view_write: Sam's Save is one commit through the gate, by the view's write path",
              ok.get('ok') is True and after != before and 'summary: "mended, and collected"' in (G / 'beans' / 'repair-1.md').read_text(encoding='utf-8')
              and subprocess.run(['git', 'rev-list', '--count', f'{before}..{after}'], cwd=G, capture_output=True, text=True).stdout.strip() == '1', ok)
        no = w.call('view_write', {'reader': READER, 'body': {'bean': 'repair-1', 'ops': [{'op': 'change', 'header': 'summary', 'value': 'written by the reader'}]}}) or {}
        bad = w.call('view_write', {'reader': 'sam', 'body': {'bean': 'repair-1', 'ops': [{'op': 'change', 'header': 'title', 'value': ' '}]}}) or {}
        check("...the reader's, who may not write, and one the write path refuses (an empty title) keep nothing",
              no.get('ok') is False and bad.get('ok') is False and bool(bad.get('refusals')) and head() == after
              and 'written by the reader' not in (G / 'beans' / 'repair-1.md').read_text(encoding='utf-8'), (no, bad, head(), after))
        # daftard's read-back of a write is the one judge's, a statement alone (core/judge.py `statement`, from v4.11):
        # an `own` with no owner reads back as written, and the judge refuses it there, tied to its statement
        if 'def statement(' not in (G / 'core' / 'judge.py').read_text(encoding='utf-8'):
            print("NOTE  this tree's judge judges no statement alone: the read-back through it not asked")
        else:
            alone = w.call('view_write', {'reader': 'sam', 'body': {'bean': 'repair-1', 'ops': [
                {'op': 'add', 'verb': 'own', 'roles': {'of': 'self'}}]}}) or {}
            said = [x.get('message', '') for x in alone.get('refusals') or []]
            check("...one the one judge refuses at its read-back (an `own` with nobody owning) keeps nothing, its rule "
                  "tied to the statement it wrote",
                  alone.get('ok') is False and head() == after and any(m.startswith('valency: ') for m in said)
                  and any(str(x.get('fact') or '').startswith('own#') for x in alone.get('refusals') or []), alone)

        # ------------------------------------------------------------------ view_html, view_style
        V = w.call('view_html', {'page': 'page-repair', 'lang': 'fa'}) or {}
        sc = V.get('scripts') or []
        check("view_html: the view's own page of a page bean, and the scripts its asset declares — each in the page as "
              "written, never a script a bean's title carries", '<html' in (V.get('page') or '') and len(sc) >= 3
              and all(isinstance(x, str) and x in V['page'] for x in sc) and not any('stolen()' in x for x in sc), {k: (v if k != 'page' else len(v or '')) for k, v in V.items()})
        N = w.call('view_html', None) or {}
        H = w.call('view_html', {'handplace': 'view', 'lang': 'fa'}) or {}
        check("...asked as daftard asks a legacy garden (no page, no handplace), a garden of the core has no page here, as "
              "before #4; asked as a view garden with no page, the view itself says which of its two pages to name",
              'page' not in N and 'این بخش در این دفتر نیست' in str(N.get('error')) and 'page' not in H
              and 'page-now' in str(H.get('error')), ({k: str(v)[:200] for k, v in N.items()}, {k: str(v)[:200] for k, v in H.items()}))
        st = w.call('view_style', {'page': 'page-repair'}) or {}
        check("view_style: the kit's style for a page's drawings", len(st.get('css') or '') > 200, st)

        # ------------------------------------------------------------------ a reader's way of reading
        if not (G / 'assets' / 'view' / 'lib' / 'view_prefs.py').is_file():
            print("NOTE  this tree's view keeps no reader's preferences (view_prefs.py): prefs_check, prefs_zones not asked")
        else:
            ok = w.call('prefs_check', {'prefs': {'locale': 'fa-u-nu-latn-ca-gregory', 'date': 'long'}}) or {}
            no = w.call('prefs_check', {'prefs': {'locale': 'fa-u-ca-nonsense'}}) or {}
            check("prefs_check: the garden's own view keeps a good tag in its canonical order and refuses a bad one with a "
                  "sentence", ok.get('prefs') == {'locale': 'fa-u-ca-gregory-nu-latn', 'date': 'long'}
                  and (ok.get('reader') or {}).get('locale') == 'fa-u-ca-gregory-nu-latn'
                  and 'nonsense' in str((no.get('error') or {}).get('message')), (ok, no))
            zs = w.call('prefs_zones', {}) or []
            check("prefs_zones: CLDR's zones, each by its `tz` type and its IANA name", ['irthr', 'Asia/Tehran'] in zs, zs[:3])
            P = w.call('view_page', {'page': 'page-repair', 'reader': 'sam', 'lang': 'fa', 'prefs': ok.get('prefs')}) or {}
            check("view_page with the reader's preferences: the widgets' settings carry them; nothing of the garden moved",
                  ((P.get('engraved') or {}).get('settings') or {}).get('reader') == {'locale': 'fa-u-ca-gregory-nu-latn', 'date': 'long'}
                  and head() == after, (((P.get('engraved') or {}).get('settings') or {}).get('reader'), P.get('error')))
            vp_src = (G / 'assets' / 'view' / 'lib' / 'view_prefs.py').read_text(encoding='utf-8')
            if 'def to_bean' not in vp_src:
                print("NOTE  this tree's view writes no reader's preferences as a bean: prefs_bean, prefs_from_bean not asked")
            else:
                full = {'locale': 'en-u-ca-persian-hc-h12-nu-latn-tz-usnyc', 'date': 'full', 'currency': 'name'}
                B = w.call('prefs_bean', {'prefs': full, 'reader': 'sam'}) or {}
                R = w.call('prefs_from_bean', {'text': B.get('bean') or ''}) or {}
                gid = subprocess.run(['git', 'rev-list', '--first-parent', '--max-parents=0', 'HEAD'], cwd=G, capture_output=True,
                                     text=True).stdout.split()[-1][:12]
                check("prefs_bean / prefs_from_bean: a reader's way of reading written as a bean by the garden's own view, "
                      "with this garden's id, and read back the same; nothing of the garden moved",
                      'kind: document' in str(B.get('bean')) and R.get('prefs') == full and R.get('reader') == 'sam'
                      and R.get('garden') == gid and R.get('here') == gid and head() == after, (B, R))
                X = w.call('prefs_from_bean', {'text': str(B.get('bean')).replace('nu-latn', 'nu-nosuchdigits')}) or {}
                Y = w.call('prefs_bean', {'prefs': {'date': 'tiny'}, 'reader': 'sam'}) or {}
                check("...a bean whose tag CLDR has no type for, and preferences that are not, refused with a sentence",
                      'nosuchdigits' in str((X.get('error') or {}).get('message')) and 'tiny' in str((Y.get('error') or {}).get('message')),
                      (X, Y))

        # ------------------------------------------------------------------ a page's action (view_act)
        act_py = G / 'bin' / 'act.py'
        if '--start' not in act_py.read_text(encoding='utf-8'):
            print("NOTE  this tree's bin/act.py starts no run with inputs (--start): view_act not asked")
        else:
            import socket
            host = socket.gethostname()
            v = (G / 'VOCAB.md').read_text(encoding='utf-8')
            law = ''.join(f.read_text(encoding='utf-8') for f in (G / 'core' / 'law').glob('*.yaml'))
            for key, row in (('kinds', '  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n'),
                             ('namespaces', '  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for itself" }\n')):
                if re.search(r'\{ %s: ' % key[:-1] + re.escape(row.split(': ', 2)[1].split(',')[0]) + ',', law):
                    continue                # the law has it (procedure, since core 4.7): one name, one row
                if re.search(r'^%s: \[\]\n' % key, v, re.M):
                    v = re.sub(r'^%s: \[\]\n' % key, key + ':\n' + row, v, count=1, flags=re.M)
                elif re.search(r'^%s:\n' % key, v, re.M):
                    v = re.sub(r'^%s:\n' % key, key + ':\n' + row, v, count=1, flags=re.M)
                else:
                    v = v.replace('---\n', '---\n' + key + ':\n' + row, 1)
            put('VOCAB.md', v)
            put('tools/stamp.py', STAMP)
            put('beans/box.md', f'---\nbean: box\nkind: host\ntitle: "box — this machine"\nstatements:\n  - read: {{ by: sam, at: now }}\n'
                f'  - own: {{ by: sam, of: self }}\n  - name: {{ by: anchor-hostname, of: self, as: {host} }}\n---\nThe machine.\n')
            put('beans/stamp-tool.md', f'---\nbean: stamp-tool\nkind: program\ntitle: "stamp-tool — what stamps a receipt"\n'
                f'statements:\n  - make: {{ by: sam, at: now }}\n  - be: {{ by: self, at: "{host}:{G}/tools/stamp.py", as: location }}\n'
                '---\nThe tool.\n')
            put('mappings/action-stamp.md', WALK)
            put('beans/receipt-1.md', '---\nbean: receipt-1\nkind: document\ntitle: "receipt-1 — a receipt"\nstatements:\n'
                '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n---\nA receipt.\n')
            put('beans/page-books.md', '---\nbean: page-books\nkind: service\ntitle: "page-books"\nsummary: "the receipts"\n'
                'statements:\n  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n'
                '  - be: { by: self, at: "uri:http://127.0.0.1:8770/", as: location }\n  - be: { by: self, at: "ordinal:3", as: order }\n'
                '  - reckon: { id: receipts, reading: { what: "the receipts", steps: [ { id: d, op: select, kind: document } ] } }\n'
                f'  - draw: {{ id: ledger, by: self, of: [sam], drawing: {{ label: Receipts, archetype: table, selection: receipts, '
                f'columns: [ {{ label: Receipt, path: title }} ], actions: [ {{ element: line, tool: stamp, note: "stamp it", inputs: '
                f'[ {{ name: words, origin: {{ act: say }}, type: text }} ] }} ], {STORY.format(p="the receipts")} }} }}\n'
                '  - draw: { id: page, by: self, of: [ledger], page: { visibility: private, fields: [ { kind: document, fact: title, shown_from: understand } ] } }\n'
                '---\nA page.\n')
            s2 = grow.run(sys.executable, 'bin/save.py', 'sam', 'RULE-CHANGE: a walk that stamps a receipt, and a page of receipts',
                          '--body', '- action: RULE-CHANGE — VOCAB.md adds the kind procedure and the namespace anchor-hostname; '
                          'wrote [[box]], [[stamp-tool]], [[action-stamp]], [[receipt-1]] and [[page-books]]', '- ratified_by: sam',
                          cwd=str(G))
            audit = T / 'audit-g.jsonl'
            ask = lambda body, walks: w.call('view_act', {'body': dict(body, page='page-books'), 'reader': 'sam', 'lang': 'fa',
                                                          'walks': walks, 'audit': str(audit)}) or {}
            before = head()
            no = ask({'m': 'ledger', 'el': 'line', 'tool': 'stamp', 'bean': 'receipt-1', 'inputs': {'words': 'x'}}, {})
            check("view_act: a walk this machine does not name for the tool is refused, nothing run",
                  s2.returncode == 0 and no.get('status') == 403 and head() == before, (s2.out[-600:], no))
            st = ask({'m': 'ledger', 'el': 'line', 'tool': 'stamp', 'bean': 'receipt-1', 'inputs': {'words': 'paid in full'}},
                     {'stamp': 'action-stamp'})
            ans = st.get('answer') or {}
            check("view_act: the page's action starts the walk this machine names, with what the person gave it — its plan "
                  "returned, the run waiting to be ratified", st.get('status') == 200 and ans.get('course') == 'run-1'
                  and 'paid in full' in str(ans.get('plan')) and 'ratify' in str(ans.get('stands')), st)
            ok = ask({'do': 'ratify', 'bean': 'receipt-1', 'course': 'run-1'}, {'stamp': 'action-stamp'})
            lines = audit.read_text(encoding='utf-8').splitlines() if audit.is_file() else []
            check("view_act: ratified, the receipt is stamped; each attempt in this machine's audit record, never in git",
                  ok.get('status') == 200 and 'Stamped: paid in full' in (G / 'beans' / 'receipt-1.md').read_text(encoding='utf-8')
                  and len(lines) == 3 and 'audit' not in subprocess.run(['git', 'ls-files'], cwd=G, capture_output=True,
                                                                        text=True).stdout, (ok, lines[-1:] if lines else None))
    finally:
        w.close()
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview pages: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
