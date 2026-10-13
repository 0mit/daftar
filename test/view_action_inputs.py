#!/usr/bin/env python3
"""An action's inputs, as a page asks them of a person (ratified by the operator 2026-10-13): a value chosen among a
reading's members or a scheme's rows (`of`), several of them (`many`), one the host fills from the element the button
sits on (`from`), a file the person chooses (the type `file`, kept off git under its SHA-256) and a day, read in the
reader's calendar — and the rows of a sheet as elements an action sits on, one button a row.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps receipts on a machine, each
holding a payment; a scheme of the garden's own names its shelves (a group heading two shelves, in Persian beside
English); a walk files a receipt's payment on a shelf, with its helpers, a day and a scan (its tool written on
bin/walktool.py). A page draws the receipts as a table; its action sits on each payment a receipt's sheet shows (`pay`),
the payment filled from the row, the shelf chosen from the scheme, the helpers from a reading of the people, a day and
a scan given. Then:

  the law      the action's input holds `of`, `many` and `from`; the law's types hold `file`
  the check    `view check` takes the page; it refuses an input whose `of` names no reading and no scheme, a `from` on
               the clock's input, and an action on a row of a verb the law has not
  the page     the receipt's sheet carries the action on its `pay` rows: the shelf's choices the scheme's rows by their
               names in Persian, the group a heading never chosen; the helpers the reading's members by title; the
               payment's input filled from the row, never asked
  the start    the run started on a payment: the payment filled by the host from the row (a forged one ignored), the
               shelf, the helpers a list, the day, the scan's SHA-256 — the file kept off git under it, its bytes exact,
               readable by its owner alone, git none the wiser; refused, nothing started: a heading, a shelf the scheme
               has not, a helper the reading has not, a row the receipt has not, a row of another verb, a file over the
               host's bound
  the run      ratified: the tool files the payment on the shelf with its helpers, its day and its scan's bytes (read by
               bin/walktool.py `file`), read back
  bin/act.py   an input named twice is a list
  a browser    Sam's sheet in Persian: a button on each payment row; pressed, the shelf a choice of the scheme's rows by
               their Persian names (the group disabled), the helpers a check box each, the day in the reader's
               calendar, the scan a file chooser; started, the host asked with the row, the choices, the list and the
               file's bytes

Run: python3 test/view_action_inputs.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import base64, hashlib, html, json, os, re, shutil, socket, stat, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []
HOST = socket.gethostname()
ADA, BEN = 'p-0a0a0a0a', 'p-0b0b0b0b'
FRONT, BACK, STORE = 'قفسهٔ جلو', 'قفسهٔ پشت', 'انبار'
SCAN = b'a scanned receipt\n'


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
bean: action-file
kind: procedure
title: "action-file — a receipt's payment filed on a shelf"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: file-tool }
  - step: { id: plan, as: "what would be written, writing nothing", by: engine, to: [show] }
  - step: { id: show, as: "the plan, line by line", by: engine, to: [check] }
  - step: { id: check, as: "the shelf and the scan are there", by: engine, to: [ratify] }
  - step: { id: ratify, as: "a person ratifies what they were shown", by: ratifier, to: [apply, show] }
  - step: { id: apply, as: "filed", by: engine, to: [verify] }
  - step: { id: verify, as: "read back", by: engine, to: [done] }
  - step: { id: done, as: "filed", walk: { final: "true" } }
  - step: { id: refused, as: "nothing was changed", walk: { exit: "true", reasons: [cannot-plan, check-failed, declined] } }
  - step: { id: rolled-back, as: "restored", walk: { exit: "true", reasons: [apply-failed, verify-mismatch] } }
---
How a payment is filed.
'''

TOOL = r'''import hashlib, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))      # the garden's own bin/: the release's library
import walktool as W


def line():
    i = W.inputs()
    scan = open(W.file(i['scan']), 'rb').read()
    return 'Filed: %s on %s by %s on %s, scan %s' % (i['of'], i['shelf'], '+'.join(i['helpers']), i['day'],
                                                     hashlib.sha256(scan).hexdigest()[:16])


def plan(bean, course):
    print('+ ' + bean + ': ' + line())


def check(bean, course):
    if not W.inputs().get('shelf'):
        raise W.Refused('no shelf')


def apply(bean, course):
    open(W.shown()).read()
    with open(os.path.join('beans', bean + '.md'), 'a', encoding='utf-8') as fh:
        fh.write(line() + '\n')
    W.save('sam', 'filed ' + bean, ['- action: filed a payment of [[' + bean + ']] on its shelf'])


def verify(bean, course):
    if line() not in open(os.path.join('beans', bean + '.md'), encoding='utf-8').read():
        raise W.Refused('not read back')


def restore(bean, course):
    pass


sys.exit(W.main('file', {'plan': plan, 'check': check, 'apply': apply, 'verify': verify, 'restore': restore}))
'''

STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
NOTE = 'بایگانی این پرداخت'
INPUTS = ('[ { name: of, origin: { act: say }, from: self, note: "پرداخت" }, '
          '{ name: shelf, origin: { act: say }, of: "scheme:shelf", note: "قفسه" }, '
          '{ name: helpers, origin: { act: say }, of: people, many: "true", note: "یاری‌کنندگان" }, '
          '{ name: day, origin: { act: say }, type: position, note: "روز بایگانی" }, '
          '{ name: scan, origin: { act: say }, type: file, note: "تصویر رسید" } ]')
ACTIONS = 'actions: [ { element: pay, tool: file, note: "%s", inputs: %s } ]' % (NOTE, INPUTS)
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
else:
    out = h.decide(*args)
print(json.dumps(out, default=str, ensure_ascii=False))"""

T = tempfile.mkdtemp(prefix='view-inputs-')
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
    lines = yaml.safe_load(open(os.path.join(ROOT, 'core', 'law', 'lines.yaml'), encoding='utf-8'))
    ftype = next((t for t in lines.get('types') or [] if t.get('type') == 'file'), None)
    check("the law: an action's input holds `of`, `many` and `from`; the law's types hold `file`",
          {'of', 'many', 'from'} <= set(ins) and ftype is not None and re.fullmatch(ftype.get('pattern', 'x'), '0' * 64),
          (sorted(ins), ftype))

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
    put('extracts/shelf.tsv', 'code\tlevel\tparent\tname\tname_fa\n'
                              f'1\tstore\t\tThe store\t{STORE}\n'
                              f'11\tshelf\t1\tFront shelf\t{FRONT}\n'
                              f'12\tshelf\t1\tBack shelf\t{BACK}\n')
    put('tools/file.py', TOOL)
    put('beans/box.md', f'---\nbean: box\nkind: host\ntitle: "box — the machine the garden is served from"\nstatements:\n'
        f'  - read: {{ by: sam, at: now }}\n  - own:  {{ by: sam, of: self }}\n  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}\n---\nThe machine.\n')
    put('beans/file-tool.md', f'---\nbean: file-tool\nkind: program\ntitle: "file-tool — what files a payment"\nstatements:\n'
        f'  - make: {{ by: sam, at: now }}\n  - be:   {{ by: self, at: "{HOST}:{G}/tools/file.py", as: location }}\n---\nThe tool.\n')
    put('mappings/action-file.md', WALK)
    put('beans/receipt-1.md', '---\nbean: receipt-1\nkind: document\ntitle: "receipt-1 — a receipt of a repair"\n'
        'statements:\n  - say: { by: sam, at: now }\n  - own: { id: owner, by: sam, of: self }\n'
        '  - pay: { id: paid, by: sam, of: { count: "40.00", unit: XTS } }\n'
        '  - pay: { id: tip, by: sam, of: { count: "5.00", unit: XTS } }\n---\nA receipt.\n')
    for pid in (ADA, BEN):
        put(f'beans/{pid}.md', f'---\nbean: {pid}\nkind: person\ntitle: "{pid}"\nsummary: "a helper"\nstatements:\n'
            '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\nA helper.\n')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's receipts"
summary: "the receipts, and where each payment is filed"
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
    rc, out = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a walk that files a payment, a scheme of shelves, a page', '--body',
                  '- action: RULE-CHANGE — VOCAB.md adds the kind procedure, the namespace anchor-hostname and the scheme '
                  f'shelf; wrote [[box]], [[file-tool]], [[action-file]], [[receipt-1]], [[{ADA}]], [[{BEN}]] and [[page]]',
                  '- ratified_by: sam')
    check("the walk, its tool, the shelves, the receipt, two helpers and the page are saved through the gate",
          rc == 0 and '0 error(s)' in out, out[-1500:])

    # ------------------------------------------------------------------ the check
    rc, out = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
    check("view check: an action on a sheet's `pay` rows, its inputs chosen, listed, filled from the row, a day and a file",
          rc == 0, out[-800:])
    bad = {'an input whose `of` names no reading and no scheme': ('of: people,', 'of: nobody,'),
           'a `from` on the clock\'s input': ('{ name: day, origin: { act: say }', '{ name: day, from: self, origin: { act: read, nature: soma, by: reader }'),
           'an action on a row of a verb the law has not': ('element: pay', 'element: nosuchverb')}
    said = {}
    for what, (a, b) in bad.items():
        put('beans/page.md', get('beans/page.md').replace(a, b, 1))
        rc2, out2 = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
        rc3, out3 = run(PY, 'core/check.py')
        run('git', 'checkout', '--', 'beans/page.md')
        said[what] = (rc2 != 0 or rc3 != 0, (out2 + out3)[-300:])
    check("...and refuses " + "; ".join(said), all(x[0] for x in said.values()), said)

    # ------------------------------------------------------------------ the page
    CFG = os.path.join(T, 'host', 'serve.json')
    run(PY, 'assets/view/bin/view.py', 'serve-init', '--config', CFG, '--user', 'sam', '--bean', 'sam')
    C = json.load(open(CFG))
    C['tools'] = {'file': {'walk': 'action-file'}}
    C['users']['sam']['lang'] = 'fa'               # Sam reads in Persian: the scheme's rows by their Persian names
    json.dump(C, open(CFG, 'w'))

    def host(what, args):
        f = os.path.join(T, 'args.json')
        with open(f, 'w', encoding='utf-8') as fh:
            json.dump(args, fh)
        return last_json(run(PY, '-c', HOSTPY, CFG, what, f)[1])

    P = host('page', ['sam'])
    S = ((P.get('sam') or {}).get('sheets') or {}).get('receipt-1') or {}
    act = next((a for a in S.get('actions') or [] if a.get('tool') == 'file'), {})
    by = {i.get('name'): i for i in act.get('inputs') or []}
    shelf = by.get('shelf') or {}
    helpers = by.get('helpers') or {}
    check("the page: the receipt's sheet carries the action on its `pay` rows, the shelf's choices the scheme's rows (the "
          "store a heading never chosen), the helpers the reading's members, the payment filled from the row",
          act.get('el') == 'pay' and [c.get('value') for c in shelf.get('choices') or []] == ['shelf:1', 'shelf:11', 'shelf:12']
          and [bool(c.get('disabled')) for c in shelf.get('choices') or []] == [True, False, False]
          and {c.get('value') for c in helpers.get('choices') or []} == {ADA, BEN} and helpers.get('many') in ('true', True)
          and (by.get('of') or {}).get('from') == 'self', (act, P.get('error')))

    # ------------------------------------------------------------------ the start
    good = {'of': 'receipt-1#tip', 'shelf': 'shelf:11', 'helpers': [ADA, BEN], 'day': '2026-10-01',
            'scan': {'name': 'scan.txt', 'data': base64.b64encode(SCAN).decode()}}
    refusals = {'a heading': dict(good, shelf='shelf:1'), 'a shelf the scheme has not': dict(good, shelf='shelf:99'),
                'a helper the reading has not': dict(good, helpers=[ADA, 'sam'])}
    no = {k: host('start', ['sam', 'ledger', 'pay', 'file', 'receipt-1#paid', x]) for k, x in refusals.items()}
    no['a row the receipt has not'] = host('start', ['sam', 'ledger', 'pay', 'file', 'receipt-1#nosuch', good])
    no['a row of another verb'] = host('start', ['sam', 'ledger', 'pay', 'file', 'receipt-1#owner', good])
    C = json.load(open(CFG))
    C['file_bound'] = 8
    json.dump(C, open(CFG, 'w'))
    no['a file over the host\'s bound'] = host('start', ['sam', 'ledger', 'pay', 'file', 'receipt-1#paid', good])
    C.pop('file_bound')
    json.dump(C, open(CFG, 'w'))
    head = run('git', 'rev-parse', 'HEAD')[1].strip()
    check("refused, nothing started: " + "; ".join(no), all(isinstance(r, list) and r[0] >= 400 for r in no.values())
          and run('git', 'rev-parse', 'HEAD')[1].strip() == head, {k: r for k, r in no.items()})
    st = host('start', ['sam', 'ledger', 'pay', 'file', 'receipt-1#paid', good])
    ans = st[1] if isinstance(st, list) and len(st) > 1 else {}
    cap = [f for f in os.listdir(os.path.join(G, 'captures', 'actions')) if f.startswith('receipt-1.') and '.inputs.' in f] \
        if os.path.isdir(os.path.join(G, 'captures', 'actions')) else []
    given = json.load(open(os.path.join(G, 'captures', 'actions', cap[0]), encoding='utf-8')) if cap else {}
    sha = hashlib.sha256(SCAN).hexdigest()
    gitdir = run('git', 'rev-parse', '--absolute-git-dir')[1].strip()
    kept = os.path.join(gitdir, 'daftar-inputs', sha)
    check("the start: the payment filled by the host from the row (the forged one ignored), the shelf, the helpers a list, "
          "the day, the scan's SHA-256", isinstance(st, list) and st[0] == 200
          and given == {'of': 'receipt-1#paid', 'shelf': 'shelf:11', 'helpers': [ADA, BEN], 'day': '2026-10-01', 'scan': sha},
          (st, given))
    check("...the scan kept off git under its SHA-256, its bytes exact, readable by its owner alone; git none the wiser",
          os.path.isfile(kept) and open(kept, 'rb').read() == SCAN and stat.S_IMODE(os.stat(kept).st_mode) == 0o600
          and sha[:12] not in run('git', 'ls-files')[1] and not run('git', 'status', '--porcelain')[1].strip(),
          (kept, os.path.exists(kept)))
    dec = host('decide', ['sam', 'receipt-1', ans.get('course') or 'run-1', 'ratify'])
    check("the run, ratified: the payment filed on its shelf with its helpers, its day and its scan's bytes, read back",
          isinstance(dec, list) and dec[0] == 200
          and f'Filed: receipt-1#paid on shelf:11 by {ADA}+{BEN} on 2026-10-01, scan {sha[:16]}' in get('beans/receipt-1.md'),
          (dec, get('beans/receipt-1.md')[-300:]))

    # ------------------------------------------------------------------ bin/act.py
    rc, out = run(PY, 'bin/act.py', 'receipt-1', '--start', 'action-file', '--by', 'sam', '--input', 'of=receipt-1#tip',
                  '--input', 'shelf=shelf:12', '--input', f'helpers={ADA}', '--input', f'helpers={BEN}', '--input',
                  'day=2026-10-02', '--input', f'scan={sha}')
    caps = sorted(f for f in os.listdir(os.path.join(G, 'captures', 'actions')) if '.inputs.' in f)
    last = json.load(open(os.path.join(G, 'captures', 'actions', caps[-1]), encoding='utf-8')) if caps else {}
    check("bin/act.py: an input named twice is a list", rc == 0 and last.get('helpers') == [ADA, BEN], (out[-400:], last))

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
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
(async () => {
try {
  E.settings = Object.assign({}, E.settings || {}, {reader: {locale: 'fa-u-ca-persian'}});
  const t = window.daftarEngraved.tools({engraved: E, act: b => { out.sent = b; return new Promise(() => {}); }});
  const el = document.getElementById('s');
  window.daftarArchetypes.sheet(el, E.sheets['receipt-1'], t, null);
  const btns = [...el.querySelectorAll('[data-act-row]')];
  out.rows = btns.map(b => b.getAttribute('data-act-row'));
  out.label = btns[0] ? btns[0].textContent : null;
  btns[0].click();
  const box = el.querySelector('[data-act-box]');
  const sel = box.querySelector('select[name="act.shelf"]');
  out.shelf = sel ? [...sel.options].filter(o => o.value).map(o => [o.value, o.textContent, o.disabled]) : null;
  out.helpers = [...box.querySelectorAll('input[name="act.helpers"]')].map(x => x.value);
  out.askedOf = !!box.querySelector('[name="act.of"]');
  const day = box.querySelector('[name="act.day"]');
  out.dayWidget = day ? day.className : null;
  if (sel) sel.value = 'shelf:12';
  box.querySelectorAll('input[name="act.helpers"]').forEach(x => { x.checked = true; });
  if (day) day.value = '۱۴۰۵/۷/۹';
  const f = box.querySelector('input[type="file"][name="act.scan"]');
  if (f) { const dt = new DataTransfer(); dt.items.add(new File(['a scan'], 'scan.txt')); f.files = dt.files; }
  box.querySelector('[data-act-start]').click();
  await new Promise(r => setTimeout(r, 300));
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
})();
</script></body></html>"""
        path = os.path.join(T, 'inputs.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(sam, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        Bx = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        sent = Bx.get('sent') or {}
        check("in Persian: a button on each payment row, by the action's note; pressed, the shelf a choice of the scheme's "
              "rows by their Persian names (the store disabled), the helpers a box each, the payment never asked, the day "
              "a day in the reader's calendar, the scan a file chooser",
              not Bx.get('errs') and Bx.get('rows') == ['paid', 'tip'] and NOTE in (Bx.get('label') or '')
              and Bx.get('shelf') == [['shelf:1', STORE, True], ['shelf:11', FRONT, False], ['shelf:12', BACK, False]]
              and sorted(Bx.get('helpers') or []) == sorted([ADA, BEN]) and Bx.get('askedOf') is False
              and 'w-moment' in str(Bx.get('dayWidget')), Bx)
        ins = sent.get('inputs') or {}
        check("...started: the host asked with the row, the shelf, the helpers a list, the day as the law writes it, and the "
              "file's name and bytes", sent.get('bean') == 'receipt-1#paid' and sent.get('el') == 'pay'
              and ins.get('shelf') == 'shelf:12' and sorted(ins.get('helpers') or []) == sorted([ADA, BEN])
              and ins.get('day') == '2026-10-01' and 'of' not in ins
              and (ins.get('scan') or {}).get('name') == 'scan.txt'
              and base64.b64decode((ins.get('scan') or {}).get('data') or '') == b'a scan', (sent, Bx.get('errs')))
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_action_inputs: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
