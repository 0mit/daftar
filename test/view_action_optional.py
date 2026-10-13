#!/usr/bin/env python3
"""An action's input a person may leave empty (`optional`, ratified by the operator 2026-10-13: "meaningful optional
inputs"): where empty has a meaning the tool states — no note, no shelf, nobody helping, today's day, no scan — the
person may leave it so, and the tool is then given no value of that name: absent, never an empty one it would have to
guess about. Never an input filled from the element, nor the clock's: a tool cannot run without them.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps receipts, each holding payments,
one paid to a shop; a scheme of the garden's own names its shelves; a walk notes a payment (its tool written on
bin/walktool.py), reading each input it was given and stating what an absent one means. A page draws the receipts as a
table; on each payment a receipt's sheet shows (`pay`) sits the action that notes it — the payment and its payee filled
from the row, a note, a shelf, the helpers, a day and a scan each optional, a reason asked — and the same walk under a
second tool whose page declares the reason optional, which the walk needs; on the table's line, a tool the host runs
by its argv, its words asked and a note optional. Then:

  the law      an action's input holds `optional`, "true" its one value
  the check    `view check` and the gate take the page; they refuse `optional` on an input filled from the element, on
               the clock's input, and any value but "true"
  the page     the sheet's action carries `optional` on the five inputs that may be left empty, never on the reason
  the start    the five left empty (an empty word, blanks, no helper, a file not chosen): the run started, its inputs
               the payment, its payee and the reason, nothing of the five — no key, no empty word, no empty list;
               ratified, the tool read each absent and wrote what its absence means
               refused, nothing started: the reason left empty, blanks, or not sent; a shelf no choice offers (left
               optional, a value given is still held to the choices); a row whose payee the element does not give
               given, each reaches the tool as it was given — the helpers a list, of one too
  bin/act.py   an input `--list` names is a list, of one too (the host names each `many` so)
  the walk     a page that declares optional what the walk needs: the run starts, and the walk refuses when it plans,
               nothing written
  a tool's argv  the note left empty is no key of what the tool reads; its words left empty, or blanks, refused
  a browser    the sheet in Persian: the reason marked required, the five not; started with the reason empty, the
               field says so and nothing is sent; with the reason only, the host is asked with it and nothing else

Run: python3 test/view_action_optional.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import base64, hashlib, html, json, os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []
HOST = socket.gethostname()
ADA, BEN = 'p-0a0a0a0a', 'p-0b0b0b0b'
SCAN = b'a scanned receipt\n'
WHY = 'counted twice'


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=grow.ENV)
    out = r.stdout + r.stderr
    if 'Traceback' in out:
        TRACES.append(out[-1200:])
    return r.returncode, out


def put(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def get(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def last_json(out):
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


WALK = '''---
bean: action-note
kind: procedure
title: "action-note — a receipt's payment noted"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: note-tool }
  - step: { id: plan, as: "what would be written, writing nothing", by: engine, to: [show] }
  - step: { id: show, as: "the plan, line by line", by: engine, to: [check] }
  - step: { id: check, as: "the payment is there", by: engine, to: [ratify] }
  - step: { id: ratify, as: "a person ratifies what they were shown", by: ratifier, to: [apply, show] }
  - step: { id: apply, as: "noted", by: engine, to: [verify] }
  - step: { id: verify, as: "read back", by: engine, to: [done] }
  - step: { id: done, as: "noted", walk: { final: "true" } }
  - step: { id: refused, as: "nothing was changed", walk: { exit: "true", reasons: [cannot-plan, check-failed, declined] } }
  - step: { id: rolled-back, as: "restored", walk: { exit: "true", reasons: [apply-failed, verify-mismatch] } }
---
How a payment is noted.
'''

# The walk states what each absent input means; the reason it needs, and refuses without, when it plans.
TOOL = r'''import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))      # the garden's own bin/: the release's library
import walktool as W


def line():
    i = W.inputs()
    return 'Noted %s to %s: note %s, shelf %s, helpers %s, day %s, scan %s; given %s; because %s' % (
        i['of'], i['payee'], i.get('note', 'none'), i.get('shelf', 'none'), '+'.join(i.get('helpers', [])) or 'nobody',
        i.get('day', 'today'), i['scan'][:16] if 'scan' in i else 'none', ','.join(sorted(i)), i['reason'])


def plan(bean, course):
    if not W.inputs().get('reason'):
        raise W.Refused('reason: say why it is noted')
    print('+ ' + bean + ': ' + line())


def check(bean, course):
    pass


def apply(bean, course):
    open(W.shown()).read()
    with open(os.path.join('beans', bean + '.md'), 'a', encoding='utf-8') as fh:
        fh.write(line() + '\n')
    W.save('sam', 'noted ' + bean, ['- action: noted a payment of [[' + bean + ']]'])


def verify(bean, course):
    if line() not in open(os.path.join('beans', bean + '.md'), encoding='utf-8').read():
        raise W.Refused('not read back')


def restore(bean, course):
    pass


sys.exit(W.main('note', {'plan': plan, 'check': check, 'apply': apply, 'verify': verify, 'restore': restore}))
'''

STAMP = "import json, sys; d = json.load(sys.stdin); print('GIVEN ' + json.dumps(d['inputs'], sort_keys=True))"

STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
NOTE = 'یادداشت این پرداخت'
OPT = ('{ name: note, origin: { act: say }, optional: "true", note: "یادداشت" }, '
       '{ name: shelf, origin: { act: say }, of: "scheme:shelf", optional: "true", note: "قفسه" }, '
       '{ name: helpers, origin: { act: say }, of: people, many: "true", optional: "true", note: "یاری‌کنندگان" }, '
       '{ name: day, origin: { act: say }, type: position, optional: "true", note: "روز" }, '
       '{ name: scan, origin: { act: say }, type: file, optional: "true", note: "تصویر رسید" }')
INPUTS = ('[ { name: of, origin: { act: say }, from: self, note: "پرداخت" }, '
          '{ name: payee, origin: { act: say }, from: to, note: "گیرنده" }, ' + OPT + ', '
          '{ name: reason, origin: { act: say }, note: "علت" } ]')
LOOSE = ('[ { name: of, origin: { act: say }, from: self }, { name: payee, origin: { act: say }, from: to }, '
         '{ name: reason, origin: { act: say }, optional: "true" } ]')
STAMPS = ('[ { name: words, origin: { act: say } }, { name: note, origin: { act: say }, optional: "true" }, '
          '{ name: when, origin: { act: read, nature: soma, by: reader } } ]')
ACTIONS = ('actions: [ { element: pay, tool: note, note: "%s", inputs: %s }, { element: pay, tool: note-loose, inputs: %s }, '
           '{ element: line, tool: stamp, acts_on: receipt-1, inputs: %s } ]' % (NOTE, INPUTS, LOOSE, STAMPS))
HOSTPY = """import json, os, sys
sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_serve as vs, view_engraved as ve
vm.init('.', 'page')
h = vs.Host(sys.argv[1])
what, args = sys.argv[2], json.loads(open(sys.argv[3], encoding='utf-8').read())
if what == 'page':
    out = {u: ve.scoped(h, u) for u in args}
elif what == 'start':
    out = h.start(*args[:5], inputs=args[5])
elif what == 'act':
    out = h.act(*args[:3], inputs=args[3])
else:
    out = h.decide(*args)
print(json.dumps(out, default=str, ensure_ascii=False))"""

T = tempfile.mkdtemp(prefix='view-optional-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')

    # ------------------------------------------------------------------ the law
    sys.path[:0] = [ROOT]
    import yaml  # noqa: E402
    prof = yaml.safe_load(open(os.path.join(ROOT, 'core', 'law', 'profiles.yaml'), encoding='utf-8'))
    ins = ((((prof['forms']['drawing']['attrs'].get('actions') or {}).get('in') or {}).get('entries') or {})
           .get('inputs') or {}).get('in', {}).get('entries') or {}
    check("the law: an action's input holds `optional`, \"true\" its one value",
          (ins.get('optional') or {}).get('in') == ['true'], sorted(ins))

    v = get('VOCAB.md')
    rows = {'kinds': '  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n',
            'namespaces': '  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for itself" }\n'}
    for key, row in rows.items():
        if re.search(r'^%s: \[\]\n' % key, v, re.M):
            v = re.sub(r'^%s: \[\]\n' % key, key + ':\n' + row, v, count=1, flags=re.M)
        elif re.search(r'^%s:\n' % key, v, re.M):
            v = re.sub(r'^%s:\n' % key, key + ':\n' + row, v, count=1, flags=re.M)
        else:
            v = v.replace('---\n', '---\n' + key + ':\n' + row, 1)
    v = re.sub(r'^schemes: \[\]\n', '', v, flags=re.M)
    v = re.sub(r'^files: \[\]\n', '', v, flags=re.M)
    v = v.replace('---\n', '---\nschemes:\n- scheme: shelf\n  classifies: "the shelves receipts are filed on: a store, and '
                  'its shelves"\n  holding: extract\n  publisher: the gardener\n  url: "file:extracts/shelf.tsv"\n'
                  '  levels: [{level: store}, {level: shelf}]\n  neighbours: none\n  sources: extracts/shelf.tsv\n'
                  'files:\n- {registry: shelf, file: extracts/shelf.tsv, key: code}\n', 1)
    put('VOCAB.md', v)
    put('extracts/shelf.tsv', 'code\tlevel\tparent\tname\tname_fa\n1\tstore\t\tThe store\tانبار\n'
                              '11\tshelf\t1\tFront shelf\tقفسهٔ جلو\n12\tshelf\t1\tBack shelf\tقفسهٔ پشت\n')
    put('tools/note.py', TOOL)
    put('beans/box.md', f'---\nbean: box\nkind: host\ntitle: "box — the machine the garden is served from"\nstatements:\n'
        f'  - read: {{ by: sam, at: now }}\n  - own:  {{ by: sam, of: self }}\n  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}\n---\nThe machine.\n')
    put('beans/note-tool.md', f'---\nbean: note-tool\nkind: program\ntitle: "note-tool — what notes a payment"\nstatements:\n'
        f'  - make: {{ by: sam, at: now }}\n  - be:   {{ by: self, at: "{HOST}:{G}/tools/note.py", as: location }}\n---\nThe tool.\n')
    put('mappings/action-note.md', WALK)
    put('beans/shop.md', '---\nbean: shop\nkind: org\ntitle: "shop — a repair shop"\nstatements:\n'
        '  - say: { by: sam, at: now }\n---\nA shop.\n')
    put('beans/receipt-1.md', '---\nbean: receipt-1\nkind: document\ntitle: "receipt-1 — a receipt of a repair"\n'
        'statements:\n  - say: { by: sam, at: now }\n  - own: { id: owner, by: sam, of: self }\n'
        '  - pay: { id: paid, by: sam, of: { count: "40.00", unit: XTS }, to: shop }\n'
        '  - pay: { id: tip, by: sam, of: { count: "5.00", unit: XTS } }\n---\nA receipt.\n')
    for pid in (ADA, BEN):
        put(f'beans/{pid}.md', f'---\nbean: {pid}\nkind: person\ntitle: "{pid}"\nsummary: "a helper"\nstatements:\n'
            '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\nA helper.\n')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's receipts"
summary: "the receipts, and a note on each payment"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - reckon: {{ id: receipts, reading: {{ what: "the receipts", steps: [ {{ id: d, op: select, kind: document }} ] }} }}
  - reckon: {{ id: people, reading: {{ what: "the helpers", steps: [ {{ id: p, op: select, kind: person, where: [ {{ path: summary, "=": "a helper" }} ] }} ] }} }}
  - draw:   {{ id: ledger, by: self, of: [sam], drawing: {{ label: Receipts, archetype: table, selection: receipts, columns: [ {{ label: Receipt, path: title }} ], {ACTIONS}, {STORY.format(p='the receipts')} }} }}
  - draw:   {{ id: page, by: self, of: [ledger], page: {{ visibility: private, fields: [ {{ kind: document, fact: title, shown_from: understand }}, {{ kind: document, fact: pay, shown_from: understand, label: "پرداخت‌ها" }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a walk that notes a payment, a scheme of shelves, a page', '--body',
                  '- action: RULE-CHANGE — VOCAB.md adds the kind procedure, the namespace anchor-hostname and the scheme '
                  f'shelf; wrote [[box]], [[note-tool]], [[action-note]], [[shop]], [[receipt-1]], [[{ADA}]], [[{BEN}]] '
                  'and [[page]]', '- ratified_by: sam')
    check("the walk, its tool, the shelves, the shop, the receipt, two helpers and the page with its optional inputs are "
          "saved through the gate", rc == 0 and '0 error(s)' in out, out[-1500:])

    # ------------------------------------------------------------------ the check
    rc, out = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
    check("view check: an action on a sheet's `pay` rows, five of its inputs optional", rc == 0, out[-800:])
    bad = {'`optional` on an input filled from the element': (
               '{ name: of, origin: { act: say }, from: self, note:', '{ name: of, origin: { act: say }, from: self, optional: "true", note:'),
           'on the clock\'s input': (
               '{ name: when, origin: { act: read, nature: soma, by: reader } }',
               '{ name: when, origin: { act: read, nature: soma, by: reader }, optional: "true" }'),
           'any value but "true"': ('optional: "true", note: "یادداشت"', 'optional: "false", note: "یادداشت"')}
    said = {}
    for what, (a, b) in bad.items():
        assert a in get('beans/page.md'), a
        put('beans/page.md', get('beans/page.md').replace(a, b, 1))
        rc2, out2 = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
        rc3, out3 = run(PY, 'core/check.py')
        run('git', 'checkout', '--', 'beans/page.md')
        said[what] = (rc2 != 0 or rc3 != 0, out2 + out3)
    check("...and refuses " + "; ".join(said), all(x[0] for x in said.values())
          and all('never left empty' in said[w][1] for w in list(said)[:2]),
          {w: (x[0], x[1][-300:]) for w, x in said.items()})

    # ------------------------------------------------------------------ the page
    CFG = os.path.join(T, 'host', 'serve.json')
    run(PY, 'assets/view/bin/view.py', 'serve-init', '--config', CFG, '--user', 'sam', '--bean', 'sam')
    C = json.load(open(CFG))
    C['tools'] = {'note': {'walk': 'action-note'}, 'note-loose': {'walk': 'action-note'},
                  'stamp': {'argv': [PY, '-c', STAMP], 'enabled': True, 'timeout': 60}}
    C['users']['sam']['lang'] = 'fa'
    json.dump(C, open(CFG, 'w'))

    def host(what, args):
        f = os.path.join(T, 'args.json')
        with open(f, 'w', encoding='utf-8') as fh:
            json.dump(args, fh)
        return last_json(run(PY, '-c', HOSTPY, CFG, what, f)[1])

    def inputs_of(course):
        d = os.path.join(G, 'captures', 'actions')
        got = sorted(f for f in os.listdir(d) if f.startswith('receipt-1.%s.inputs.' % course)) if os.path.isdir(d) else []
        return json.load(open(os.path.join(d, got[-1]), encoding='utf-8')) if got else None

    P = host('page', ['sam'])
    S = ((P.get('sam') or {}).get('sheets') or {}).get('receipt-1') or {}
    act = next((a for a in S.get('actions') or [] if a.get('tool') == 'note'), {})
    opt = {i.get('name'): i.get('optional') for i in act.get('inputs') or []}
    check("the page: the sheet's action carries `optional` on the note, the shelf, the helpers, the day and the scan, "
          "never on the payment, its payee or the reason", act.get('el') == 'pay'
          and {n for n, o in opt.items() if o in ('true', True)} == {'note', 'shelf', 'helpers', 'day', 'scan'}
          and set(opt) == {'of', 'payee', 'note', 'shelf', 'helpers', 'day', 'scan', 'reason'}, (act, P.get('error')))

    # ------------------------------------------------------------------ the start
    empty = {'of': 'receipt-1#tip', 'note': '', 'shelf': '', 'helpers': [], 'day': '   ', 'reason': WHY}
    st = host('start', ['sam', 'ledger', 'pay', 'note', 'receipt-1#paid', empty])
    ans = st[1] if isinstance(st, list) and len(st) > 1 else {}
    given = inputs_of(ans.get('course') or 'run-1')
    check("the five left empty (an empty word, blanks, no helper, no file): the run started, its inputs the payment (the "
          "forged one ignored), its payee and the reason — nothing of the five, no key, no empty word, no empty list",
          isinstance(st, list) and st[0] == 200 and given == {'of': 'receipt-1#paid', 'payee': 'shop', 'reason': WHY},
          (st, given))
    dec = host('decide', ['sam', 'receipt-1', ans.get('course') or 'run-1', 'ratify'])
    check("...ratified: the tool read each of the five absent and wrote what its absence means",
          isinstance(dec, list) and dec[0] == 200
          and ('Noted receipt-1#paid to shop: note none, shelf none, helpers nobody, day today, scan none; '
               f'given of,payee,reason; because {WHY}') in get('beans/receipt-1.md'), (dec, get('beans/receipt-1.md')[-400:]))

    head = run('git', 'rev-parse', 'HEAD')[1].strip()
    no = {'the reason left empty': host('start', ['sam', 'ledger', 'pay', 'note', 'receipt-1#paid', dict(empty, reason='')]),
          'blanks': host('start', ['sam', 'ledger', 'pay', 'note', 'receipt-1#paid', dict(empty, reason=' \t ')]),
          'not sent': host('start', ['sam', 'ledger', 'pay', 'note', 'receipt-1#paid', {}]),
          'a shelf no choice offers (the store, a heading)':
              host('start', ['sam', 'ledger', 'pay', 'note', 'receipt-1#paid', dict(empty, shelf='shelf:1')]),
          'a row whose payee the element does not give':
              host('start', ['sam', 'ledger', 'pay', 'note', 'receipt-1#tip', {'reason': WHY}])}
    words = {k: (r[1] or {}).get('error', '') if isinstance(r, list) and len(r) > 1 else '' for k, r in no.items()}
    check("refused, nothing started: " + "; ".join(no), all(isinstance(r, list) and r[0] == 400 for r in no.values())
          and all('reason' in words[k] for k in ('the reason left empty', 'blanks', 'not sent'))
          and 'shelf' in words['a shelf no choice offers (the store, a heading)']
          and 'payee: the element gives none' in words['a row whose payee the element does not give']
          and run('git', 'rev-parse', 'HEAD')[1].strip() == head, no)

    full = {'note': 'paid at the counter', 'shelf': 'shelf:11', 'helpers': [ADA], 'day': '2026-10-01', 'reason': WHY,
            'scan': {'name': 'scan.txt', 'data': base64.b64encode(SCAN).decode()}}
    st = host('start', ['sam', 'ledger', 'pay', 'note', 'receipt-1#paid', full])
    ans = st[1] if isinstance(st, list) and len(st) > 1 else {}
    given = inputs_of(ans.get('course') or 'run-2')
    check("given, each reaches the walk as it was given, the helpers a list of one", isinstance(st, list) and st[0] == 200
          and given == {'of': 'receipt-1#paid', 'payee': 'shop', 'note': 'paid at the counter', 'shelf': 'shelf:11',
                        'helpers': [ADA], 'day': '2026-10-01', 'scan': hashlib.sha256(SCAN).hexdigest(), 'reason': WHY},
          (st, given))
    host('decide', ['sam', 'receipt-1', ans.get('course') or 'run-2', 'decline'])
    rc, out = run(PY, 'bin/act.py', 'receipt-1', '--start', 'action-note', '--by', 'sam', '--input', 'of=receipt-1#paid',
                  '--input', 'payee=shop', '--input', f'reason={WHY}', '--input', f'helpers={ADA}', '--list', 'helpers')
    course = re.search(r'^act: \S+ (run-\d+):', out, re.M)
    given = inputs_of(course.group(1) if course else 'none')
    check("bin/act.py: an input `--list` names is a list, of one too", rc == 0 and (given or {}).get('helpers') == [ADA],
          (out[-400:], given))
    if course:
        host('decide', ['sam', 'receipt-1', course.group(1), 'decline'])

    # ------------------------------------------------------------------ the walk
    before = get('beans/receipt-1.md').count('Noted ')
    st = host('start', ['sam', 'ledger', 'pay', 'note-loose', 'receipt-1#paid', {'reason': ''}])
    ans = st[1] if isinstance(st, list) and len(st) > 1 else {}
    given = inputs_of(ans.get('course') or 'run-3')
    loose = ' '.join(str(x) for x in (st if isinstance(st, list) else [st]))
    check("a page that declares optional what the walk needs: the run starts without it, and the walk refuses when it "
          "plans — nothing written", given == {'of': 'receipt-1#paid', 'payee': 'shop'}
          and 'reason: say why it is noted' in loose and get('beans/receipt-1.md').count('Noted ') == before,
          (st, given))

    # ------------------------------------------------------------------ a tool's argv
    got = host('act', ['sam', 'ledger', 'line', {'words': 'stamped', 'note': ''}])
    out = (got[1] or {}).get('output', '') if isinstance(got, list) and len(got) > 1 else ''
    nos = [host('act', ['sam', 'ledger', 'line', {'words': w, 'note': 'x'}]) for w in ('', '  ')]
    check("a tool the host runs by its argv: the note left empty is no key of what it reads; its words left empty, or "
          "blanks, refused", isinstance(got, list) and got[0] == 200 and 'GIVEN {"words": "stamped"}' in out
          and all(isinstance(r, list) and r[0] == 400 and 'words' in (r[1] or {}).get('error', '') for r in nos),
          (got, nos))

    # ------------------------------------------------------------------ a browser
    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the sheet was not drawn in a browser: none on this machine")
    else:
        P = host('page', ['sam'])
        sam = P.get('sam') or {}
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: [], sent: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
(async () => {
try {
  E.settings = Object.assign({}, E.settings || {}, {reader: {locale: 'fa-u-ca-persian'}});
  const t = window.daftarEngraved.tools({engraved: E, act: b => { out.sent.push(b); return new Promise(() => {}); }});
  const el = document.getElementById('s');
  window.daftarArchetypes.sheet(el, E.sheets['receipt-1'], t, null);
  const btn = [...el.querySelectorAll('[data-act-row]')].find(b => b.textContent.includes(%(note)s));
  btn.click();
  const box = btn.nextElementSibling;
  out.marked = [...box.querySelectorAll('.eg-field')].map(f => [f.getAttribute('data-role'), !!f.querySelector('.eg-req-word')]);
  box.querySelector('[data-act-start]').click();
  await new Promise(r => setTimeout(r, 200));
  out.first = out.sent.length;
  out.said = (box.querySelector('[data-err="act.reason"]') || {}).textContent || '';
  box.querySelector('[name="act.reason"]').value = %(why)s;
  box.querySelector('[data-act-start]').click();
  await new Promise(r => setTimeout(r, 300));
  out.after = (box.querySelector('[data-err="act.reason"]') || {}).textContent || '';
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
})();
</script></body></html>"""
        path = os.path.join(T, 'optional.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(sam, ensure_ascii=False), 'note': json.dumps(NOTE),
                             'why': json.dumps(WHY)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        Bx = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        check("in Persian: the reason marked required, the note, the shelf, the helpers, the day and the scan not; started "
              "with the reason empty, its field says so and nothing is sent",
              not Bx.get('errs') and dict(Bx.get('marked') or []) == {'note': False, 'shelf': False, 'helpers': False,
                                                                      'day': False, 'scan': False, 'reason': True}
              and Bx.get('first') == 0 and Bx.get('said') in ('این بخش لازم است.', 'This is required.'), Bx)
        sent = (Bx.get('sent') or [{}])[-1]
        check("...with the reason only: the host asked with the row and the reason, nothing of the five — no empty word, no "
              "empty list", len(Bx.get('sent') or []) == 1 and sent.get('bean') == 'receipt-1#paid' and sent.get('tool') == 'note'
              and sent.get('inputs') == {'reason': WHY} and not Bx.get('after'), (sent, Bx.get('errs')))
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_action_optional: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
