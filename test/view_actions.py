#!/usr/bin/env python3
"""A run started from a page, with what a person gives it: an action on a drawing engraved from a reading (a table's
line, a sheet) names a tool the host maps to a walk of the garden; pressing it starts the walk (bin/act.py `--start`)
with the inputs the action declares, kept as the run's own capture and handed to the walk's tool at every step
(bin/walktool.py `inputs`); the plan is shown, and nothing changes until a person ratifies it.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it on a machine, and two receipts;
a walk stamps a receipt with words a person gives (its tool written on bin/walktool.py: its plan says what it would
write, its check refuses empty words, its apply writes them into the receipt and saves, its verify reads them back). A
page draws the receipts as a table whose lines carry the action, asking for the words. The host maps the action's tool
to the walk. A reader may read the receipts and act on none. Then:

  the check     `view check` takes an action on a table's line; one on an element the table does not give is refused
  the page      each receipt's sheet carries the action for Sam, its button and its question in the page's words; for the
                reader, none
  the start     Sam starts it with the words: a course of the walk placed in the receipt, the words kept as the run's
                capture, the engine at `ratify`, the plan (it holds the words) answered — one commit; nothing written in
                the receipt yet. Missing words, words the action does not declare, a tool no action declares, one the
                host maps to no walk, a reader the law gives no `enact`: each refused, nothing started
  the decision  Sam ratifies: the tool applies the plan, the words in the receipt, the run at `done`; a second run
                declined is refused, nothing changed
  bin/act.py    `--start` at the terminal, with `--input`s: the same; and refused, starting nothing, to whom the law
                gives no `enact`
  a browser     the sheet in Persian: the action's button by its note; pressed, the words asked by their note; started,
                the plan shown with «تأیید و اجرا» and «رد»; ratified, the host asked to decide that run

Run: python3 test/view_actions.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, socket, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []
HOST = socket.gethostname()
READER = 'p-0a0a0a0a'


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
bean: action-stamp
kind: procedure
title: "action-stamp — a receipt stamped with words a person gives"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: stamp-tool }
  - step: { id: plan, as: "what would be written, writing nothing", by: engine, to: [show] }
  - step: { id: show, as: "the plan, line by line", by: engine, to: [check] }
  - step: { id: check, as: "the words are there", by: engine, to: [ratify] }
  - step: { id: ratify, as: "a person ratifies what they were shown", by: ratifier, to: [apply, show] }
  - step: { id: apply, as: "the words written", by: engine, to: [verify] }
  - step: { id: verify, as: "read back", by: engine, to: [done] }
  - step: { id: done, as: "stamped", walk: { final: "true" } }
  - step: { id: refused, as: "nothing was changed", walk: { exit: "true", reasons: [cannot-plan, check-failed, declined] } }
  - step: { id: rolled-back, as: "restored", walk: { exit: "true", reasons: [apply-failed, verify-mismatch] } }
---
How a receipt is stamped.
'''

STAMP = r'''import os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))      # the garden's own bin/: the release's library
import walktool as W


def words():
    return W.inputs().get('words', '').strip()


def plan(bean, course):
    print('+ ' + bean + ': Stamped: ' + words())


def check(bean, course):
    if not words():
        raise W.Refused('no words to stamp with')


def apply(bean, course):
    open(W.shown()).read()
    with open(os.path.join('beans', bean + '.md'), 'a', encoding='utf-8') as fh:
        fh.write('Stamped: ' + words() + '\n')
    W.save('sam', 'stamped ' + bean, ['- action: stamped [[' + bean + ']] with the words its run was given'])


def verify(bean, course):
    if 'Stamped: ' + words() not in open(os.path.join('beans', bean + '.md'), encoding='utf-8').read():
        raise W.Refused('the words are not read back')


def restore(bean, course):
    pass


sys.exit(W.main('stamp', {'plan': plan, 'check': check, 'apply': apply, 'verify': verify, 'restore': restore}))
'''

STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
WORDS, NOTE, ASK = 'paid in full', 'مهر رسید', 'رسید با این کلمات مهر شود؟'
ACTIONS = ('actions: [ { element: line, tool: stamp, note: "%s", confirm: "%s", inputs: [ { name: words, origin: { act: say }, '
           'type: text, note: "کلمات مهر" } ] } ]' % (NOTE, ASK))
# the host, as `view serve` runs it: its configuration made by serve-init, its tools the walks a page may start
HOSTPY = """import json, os, sys
sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_serve as vs, view_engraved as ve
vm.init('.', 'page')
h = vs.Host(sys.argv[1])
what, args = sys.argv[2], json.loads(sys.argv[3])
if what == 'page':
    out = {u: ve.scoped(h, u) for u in args}
elif what == 'start':
    out = h.start(*args[:5], inputs=args[5])
else:
    out = h.decide(*args)
print(json.dumps(out, default=str, ensure_ascii=False))"""

T = tempfile.mkdtemp(prefix='view-actions-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    v = get('VOCAB.md')
    rows = {'kinds': '  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n',
            'namespaces': '  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for itself" }\n'}
    for key, row in rows.items():                # a row of the garden's own: under its key, or the key made
        if re.search(r'^%s: \[\]\n' % key, v, re.M):
            v = re.sub(r'^%s: \[\]\n' % key, key + ':\n' + row, v, count=1, flags=re.M)
        elif re.search(r'^%s:\n' % key, v, re.M):
            v = re.sub(r'^%s:\n' % key, key + ':\n' + row, v, count=1, flags=re.M)
        else:
            v = v.replace('---\n', '---\n' + key + ':\n' + row, 1)
    put('VOCAB.md', v)
    put('tools/stamp.py', STAMP)
    put('beans/box.md', f'''---
bean: box
kind: host
title: "box — the machine the garden is served from"
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}
---
The machine.
''')
    put('beans/stamp-tool.md', f'''---
bean: stamp-tool
kind: program
title: "stamp-tool — what stamps a receipt"
statements:
  - make: {{ by: sam, at: now }}
  - be:   {{ by: self, at: "{HOST}:{G}/tools/stamp.py", as: location }}
---
The tool.
''')
    put('mappings/action-stamp.md', WALK)
    for r in ('receipt-1', 'receipt-2'):
        put(f'beans/{r}.md', f'''---
bean: {r}
kind: document
title: "{r} — a receipt of a repair"
statements:
  - say: {{ by: sam, at: now }}
  - own: {{ by: sam, of: self }}
---
A receipt.
''')
    put(f'beans/{READER}.md', f'''---
bean: {READER}
kind: person
title: "{READER}"
summary: "a reader of the garden's pages"
statements:
  - say: {{ by: sam, at: now }}
  - own: {{ by: theone, of: self }}
---
A reader.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's receipts"
summary: "the receipts, and their stamps"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - reckon: {{ id: receipts, reading: {{ what: "the receipts", steps: [ {{ id: d, op: select, kind: document }} ] }} }}
  - draw:   {{ id: ledger, by: self, of: [sam], drawing: {{ label: Receipts, archetype: table, selection: receipts, columns: [ {{ label: Receipt, path: title }} ], {ACTIONS}, {STORY.format(p='the receipts')} }} }}
  - draw:   {{ id: page, by: self, of: [ledger], page: {{ visibility: private, fields: [ {{ kind: document, fact: title, shown_from: understand }} ] }} }}
---
A page.
''')
    put('beans/sam.md', get('beans/sam.md').replace('\n---\n', '\n  - grant: { id: reader-reads, by: self, to: [%s], of: '
                                                   '[page, sam, receipt-1, receipt-2], as: read }\n  - say: { by: sam, of: '
                                                   '[reader-reads], at: now }\n---\n' % READER, 1))
    rc, out = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a walk that stamps a receipt, the receipts and a page', '--body',
                  '- action: RULE-CHANGE — VOCAB.md adds the kind procedure and the namespace anchor-hostname; wrote '
                  f'[[box]], [[stamp-tool]], [[action-stamp]], [[receipt-1]], [[receipt-2]], [[{READER}]] and [[page]]; '
                  f'[[sam]] grants the reader to read them',
                  '- ratified_by: sam')
    check("the walk, its tool, the receipts, a reader and the page are saved through the gate", rc == 0 and '0 error(s)' in out,
          out[-1500:])

    rc, out = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
    check("view check: an action on a table's line is the page's to declare", rc == 0, out[-800:])
    put('beans/page.md', get('beans/page.md').replace('element: line', 'element: sheet', 1))
    rc2, out2 = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
    run('git', 'checkout', '--', 'beans/page.md')
    check("...and one on an element a table does not give is refused", rc2 != 0 and 'not an action element' in out2, out2[-600:])

    CFG = os.path.join(T, 'host', 'serve.json')
    for user, bean in (('sam', 'sam'), ('reader', READER)):
        run(PY, 'assets/view/bin/view.py', 'serve-init', '--config', CFG, '--user', user, '--bean', bean)
    C = json.load(open(CFG))
    C['tools'] = {'stamp': {'walk': 'action-stamp'}, 'nowhere': {}}
    json.dump(C, open(CFG, 'w'))

    def host(what, args):
        return last_json(run(PY, '-c', HOSTPY, CFG, what, json.dumps(args))[1])

    P = host('page', ['sam', 'reader'])
    acts = ((P.get('sam') or {}).get('sheets') or {}).get('receipt-1', {}).get('actions') or []
    check("the page: each receipt's sheet carries the action for Sam — its tool, its button and its question in the page's "
          "words, the words it asks for", len(acts) == 1 and acts[0].get('tool') == 'stamp' and acts[0].get('note') == NOTE
          and acts[0].get('confirm') == ASK and [i.get('name') for i in acts[0].get('inputs') or []] == ['words'],
          (acts, P.get('error')))
    racts = ((P.get('reader') or {}).get('sheets') or {}).get('receipt-1', {}).get('actions')
    check("...and for the reader, whom the law gives no `enact`, none", racts == [], racts)

    head0 = run('git', 'rev-parse', 'HEAD')[1].strip()
    bad = [host('start', ['sam', 'ledger', 'line', 'stamp', 'receipt-1', {}]),
           host('start', ['sam', 'ledger', 'line', 'stamp', 'receipt-1', {'words': 'x', 'colour': 'red'}]),
           host('start', ['sam', 'ledger', 'line', 'nowhere', 'receipt-1', {'words': 'x'}]),
           host('start', ['reader', 'ledger', 'line', 'stamp', 'receipt-1', {'words': 'x'}])]
    check("the start: missing words, words the action does not declare, a tool no action declares, a reader the law "
          "gives no `enact` — each refused, nothing started", [b[0] for b in bad] == [400, 400, 404, 403]
          and run('git', 'rev-parse', 'HEAD')[1].strip() == head0, bad)
    C['tools'] = {'stamp': {}}                 # the host knows the tool, and starts no walk for it
    json.dump(C, open(CFG, 'w'))
    nowalk = host('start', ['sam', 'ledger', 'line', 'stamp', 'receipt-1', {'words': 'x'}])
    C['tools'] = {'stamp': {'walk': 'action-stamp'}}
    json.dump(C, open(CFG, 'w'))
    check("...and a tool the host maps to no walk: nothing runs — what a page may start is the host's to say",
          isinstance(nowalk, list) and nowalk[0] == 403 and 'no walk' in json.dumps(nowalk)
          and run('git', 'rev-parse', 'HEAD')[1].strip() == head0, nowalk)
    S = host('start', ['sam', 'ledger', 'line', 'stamp', 'receipt-1', {'words': WORDS}])
    code, ans = (S[0], S[1]) if isinstance(S, list) else (None, S)
    caps = os.listdir(os.path.join(G, 'captures', 'actions')) if os.path.isdir(os.path.join(G, 'captures', 'actions')) else []
    inputs = [c for c in caps if c.startswith('receipt-1.run-1.inputs.')]
    check("Sam starts it with the words: a course of the walk placed in the receipt, the words kept as the run's capture, "
          "the engine at `ratify`, the plan (it holds the words) answered — one commit, nothing written in the receipt yet",
          code == 200 and ans.get('course') == 'run-1' and 'ratify' in str(ans.get('stands')) and WORDS in str(ans.get('plan'))
          and inputs and WORDS in open(os.path.join(G, 'captures', 'actions', inputs[0]), encoding='utf-8').read()
          and 'id: run-1' in get('beans/receipt-1.md') and 'Stamped' not in get('beans/receipt-1.md')
          and run('git', 'rev-list', '--count', f'{head0}..HEAD')[1].strip() == '1', (S, caps))
    D = host('decide', ['sam', 'receipt-1', 'run-1', 'ratify'])
    stands = run(PY, 'bin/seq.py', 'course', 'receipt-1')[1]
    check("the decision: Sam ratifies — the tool applies the plan, the words in the receipt, the run at `done`",
          isinstance(D, list) and D[0] == 200 and f'Stamped: {WORDS}' in get('beans/receipt-1.md') and "at 'done'" in stands,
          (D, stands[-400:]))
    S2 = host('start', ['sam', 'ledger', 'line', 'stamp', 'receipt-2', {'words': 'never'}])
    D2 = host('decide', ['sam', 'receipt-2', 'run-1', 'decline'])
    check("...a second run declined is refused, nothing changed", isinstance(D2, list) and D2[0] == 200
          and 'Stamped' not in get('beans/receipt-2.md') and "at 'refused'" in run(PY, 'bin/seq.py', 'course', 'receipt-2')[1],
          (S2, D2))
    rc, out = run(PY, 'bin/act.py', 'receipt-2', '--start', 'action-stamp', '--by', 'sam', '--input', 'words=by hand')
    check("bin/act.py --start at the terminal, with its --input: the same — the engine at ratify, the plan with the words",
          rc == 0 and 'run-2' in out and 'ratify' in out, out[-600:])
    rc, out = run(PY, 'bin/act.py', 'receipt-2', '--start', 'action-stamp', '--by', READER, '--input', 'words=no')
    check("...and refused, starting nothing, to whom the law gives no `enact`", rc != 0 and 'may not act' in out
          and 'run-3' not in get('beans/receipt-2.md'), out[-600:])

    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the sheet was not drawn in a browser: none on this machine")
    else:
        P = host('page', ['sam'])
        E = (P.get('sam') or {})
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: [], asked: []}, E = %(payload)s;
E.settings.garden = Object.assign({}, E.settings.garden, {lang: 'fa'});
window.addEventListener('error', e => out.errs.push(String(e.message)));
const act = b => { out.asked.push(b); return Promise.resolve(b.do ? {status: 422, answer: {error: 'not here'}}   // no reload
  : {status: 200, answer: {course: 'run-9', bean: b.bean, stands: 'stopped at ratify', plan: '+ receipt-2: Stamped: ' + b.inputs.words}}); };
const tick = () => new Promise(r => setTimeout(r, 50));
(async () => {
  try {
    const el = document.getElementById('s');
    window.daftarArchetypes.sheet(el, E.sheets['receipt-2'], window.daftarEngraved.tools({engraved: E, act}), null);
    const btn = el.querySelector('[data-act-open]');
    out.button = btn ? btn.innerText : null;
    btn.click();
    out.form = el.querySelector('.eg-act-body').innerText;
    el.querySelector('[name="act.words"]').value = 'ثبت شد';
    el.querySelector('[data-act-start]').click();
    await tick(); await tick();
    out.plan = (el.querySelector('.eg-plan') || {}).innerText || null;
    out.buttons = [...el.querySelectorAll('[data-act-do]')].map(x => x.innerText);
    el.querySelector('[data-act-do="ratify"]').click();
    await tick();
  } catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
  const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
})();
</script></body></html>"""
        path = os.path.join(T, 'actions.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(E, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        asked = B.get('asked') or []
        check("in Persian: the action's button by its note; pressed, its question and the words asked by their note",
              not B['errs'] and B.get('button') == NOTE and ASK in (B.get('form') or '') and 'کلمات مهر' in (B.get('form') or ''), B)
        check("...started with the words given, the plan shown with «تأیید و اجرا» and «رد»; ratified, the host asked to "
              "decide that run", len(asked) == 2 and asked[0].get('inputs') == {'words': 'ثبت شد'} and asked[0].get('tool') == 'stamp'
              and 'ثبت شد' in (B.get('plan') or '') and B.get('buttons') == ['تأیید و اجرا', 'رد']
              and asked[1] == {'do': 'ratify', 'bean': 'receipt-2', 'course': 'run-9'}, B)
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_actions: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
