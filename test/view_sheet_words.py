#!/usr/bin/env python3
"""A sheet in its reader's words: one sheet per being, each fact called what its page calls it, in the reader's language,
calendar and digits, and no id anywhere — not of the being, not of a person kept off git, not of a statement it links.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it and mends bicycles on a walk
(handed over, looked at, collected); a repair, titled only by its id, waits at its first step, its owner a person kept
under an opaque id whose name this host does not hold; Sam is to call the owner by a day; the repair keeps the day it was
brought in and how its owner came, in `details`. (A clause's day and repetition are drawn by their own widget, form.js.) A page names the repair's facts and calls each in Persian
(`fields` … `label`), a key inside `details` among them. Then:

  the reading   the gate takes a page's labels and a path into `details`; the sheet carries the labels, the value at
                each path, the words of each statement a value names (a step by its walk's words), the walk the repair
                is on with its steps, and the repair called by its summary, not its id; the owner is `opaque`
  a browser     in Persian, the sheet heads each fact by the page's word, says the step by the walk's words, calls the
                owner a person whose name is kept off git, writes its days in the Persian calendar, and shows no id —
                the repair's, the owner's, `self`, a course, a step's reference — and no day as the law writes it
  the editor    Edit draws the facts the reader keeps, by their words, the rest under «بیشتر»; a move made stays as it
                was; a new move is a step chosen by the walk's words; no field holds an id or a moment as the law writes
                it. The step chosen and the call's words changed, Save sends a move from now on the repair's course and
                the call with its owner as it was; written through the view's one write path, the gate takes them

Run: python3 test/view_sheet_words.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import datetime, html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []
OWNER = 'p-0a1b2c3d'
IDS = re.compile(r'p-0a1b2c3d|\bself\b|\bcourse\b|walk-repair#|repair-1|\d{4}-\d{2}-\d{2}')


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


T = tempfile.mkdtemp(prefix='view-sheet-words-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
DUE = (datetime.date.today() + datetime.timedelta(days=5)).isoformat()
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
LABELS = {'concern': 'صاحب دوچرخه', 'move': 'مرحله', 'can': 'پیگیری‌ها', 'case.opened_on': 'روز پذیرش',
          'case.channel': 'از چه راهی آمد'}

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put('mappings/walk-repair.md', '''---
bean: walk-repair
kind: procedure
title: "walk-repair — how a bicycle is mended"
summary: "how a bicycle repair goes"
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "the owner brings the bicycle", to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", to: [collected] }
  - step: { id: collected, as: "the owner takes it home", walk: { final: "true" } }
---
Steps.
''')
    put(f'beans/{OWNER}.md', f'---\nbean: {OWNER}\nkind: person\ntitle: "{OWNER}"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\nA person.\n')
    put('beans/repair-1.md', f'''---
bean: repair-1
kind: contract
title: "repair-1"
summary: "A bicycle with a bent wheel, brought in by its owner. Sam mends it."
details:
  case: {{ opened_on: "2026-09-24", channel: "a neighbour" }}
statements:
  - say:        {{ by: sam, at: now }}
  - own:        {{ by: theone, of: self }}
  - concern:    {{ by: sam, of: [{OWNER}] }}
  - be:         {{ id: course, by: self, at: walk-repair, as: order }}
  - move:       {{ by: sam, of: self, through: course, at: [now, "walk-repair#handed-over"] }}
  - can:        {{ id: call-back, by: sam, of: "call the owner when it is mended", to: {OWNER} }}
---
A repair.
''')
    fields = ', '.join(f'{{ kind: contract, fact: {f}, shown_from: understand, label: "{l}" }}' for f, l in LABELS.items())
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "a repair"
statements:
  - say:  {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - be:   {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw: {{ id: repair, by: self, of: [repair-1], drawing: {{ label: Repair, archetype: sheet, {STORY.format(p='the repair')} }} }}
  - draw: {{ id: page, by: self, of: [repair], page: {{ fields: [ {fields} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a repair on its walk, its owner, and a page of its sheet in Persian',
                  '--body', '- ratified_by: sam', f'- action: wrote [[walk-repair]], [[{OWNER}]], [[repair-1]] and [[page]]; '
                  'VOCAB.md holds the kind of a walk')
    check("the gate takes a page that calls each fact in its own words (`label`) and names a path into `details`",
          rc == 0 and '0 error(s)' in out, out[-1500:])
    rc, out = run(PY, 'assets/view/bin/view.py', 'check', '--page', 'page')
    check("...and so does `view check`: a path into `details` some being here holds is a fact the page may name",
          rc == 0 and 'the page and its drawings agree' in out, out[-800:])

    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
                  "import view_model as vm, view_engraved as ve; vm.init('.', 'page'); "
                  "print(json.dumps(ve.page(lambda *a, **k: True, 'sam'), default=str, ensure_ascii=False))")
    try:
        P = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        P = {'error': out[-1500:]}
    S = (P.get('sheets') or {}).get('repair-1') or {}
    check("the sheet carries the page's word for each fact, and the value at a path into `details`",
          S.get('labels') == LABELS and (S.get('details') or {}).get('case.opened_on') == '2026-09-24'
          and (S.get('details') or {}).get('case.channel') == 'a neighbour', {k: S.get(k) for k in ('labels', 'details')} or P.get('error'))
    check("...the words of each statement a value names — the step by its walk's words — and the walk it is on, its steps",
          (S.get('said') or {}).get('walk-repair#handed-over') == 'the owner brings the bicycle'
          and [x['says'] for x in ((S.get('courses') or {}).get('course') or {}).get('steps') or []]
          == ['the owner brings the bicycle', 'what is wrong is found', 'the owner takes it home'], {k: S.get(k) for k in ('said', 'courses')})
    owner = next((b for b in P.get('beings') or [] if b.get('id') == OWNER), {})
    check("...the repair called by its summary's first sentence, its title being only its id; the owner, with neither, `opaque`",
          S.get('title') == 'A bicycle with a bent wheel, brought in by its owner.' and owner.get('opaque') is True, (S.get('title'), owner))

    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    body = None
    if not browser:
        print("NOTE  the sheet was not drawn in a browser: none on this machine")
    else:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
E.settings.garden = Object.assign({}, E.settings.garden, {lang: 'fa', me: 'sam'});
window.addEventListener('error', e => out.errs.push(String(e.message)));
const visible = el => [el.innerText, ...[...el.querySelectorAll('input, textarea')].map(i => i.value),
  ...[...el.querySelectorAll('select')].map(x => x.selectedOptions[0] ? x.selectedOptions[0].textContent : '')].join('\\n');
try {
  const el = document.getElementById('s');
  window.daftarArchetypes.sheet(el, E.sheets['repair-1'], window.daftarEngraved.tools({engraved: E, write: b => { out.body = b; return new Promise(() => {}); }}), null);
  out.read = visible(el);
  out.heads = [...el.querySelectorAll('.eg-row[data-verb] h4')].map(x => x.textContent);
  el.querySelector('[data-do="edit"]').click();
  const open = el.querySelectorAll('details.eg-more[open]').length;
  out.more = el.querySelectorAll('details.eg-more').length;
  out.edit = visible(el);
  out.moveInputs = el.querySelectorAll('li[data-verb="move"]:not([data-add-op]) input:not([data-remove]), li[data-verb="move"]:not([data-add-op]) select').length;
  const topic = el.querySelector('li[data-verb="can"] [data-role="of"] input');
  if (topic) { topic.value = 'call the owner when the wheel is true'; }
  el.querySelector('.eg-row[data-verb="move"] [data-add="move"]').click();
  const step = el.querySelector('li[data-move] select');
  out.steps = step ? [...step.options].map(o => o.textContent).filter(x => x !== '—') : [];
  if (step) { step.value = [...step.options].find(o => o.textContent === 'what is wrong is found').value; }
  el.querySelector('[data-do="save"]').click();
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'words.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(P, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        rd, ed = B.get('read') or '', B.get('edit') or ''
        check("in Persian the sheet heads each fact by the page's word, says the step by the walk's words, and calls the "
              "owner a person whose name is kept off git", not B['errs'] and B.get('heads') == ['صاحب دوچرخه', 'مرحله', 'پیگیری‌ها']
              and 'the owner brings the bicycle' in rd and 'فردی که نامش بیرون از گیت است' in rd, B)
        check("...and shows no id — the repair's, the owner's, `self`, a course, a step's reference — and no day as the law "
              "writes it, its days in the Persian calendar", not IDS.search(rd) and re.search('[۰-۹]', rd), IDS.findall(rd) or rd)
        check("Edit: no field holds an id or a moment as the law writes it; the rest waits under «بیشتر»; a move made stays "
              "as it was", not IDS.search(ed) and B.get('more', 0) >= 1 and B.get('moveInputs') == 0 and 'بیشتر' in ed,
              (IDS.findall(ed), B.get('more'), B.get('moveInputs')))
        check("...a new move is a step chosen by the walk's own words", B.get('steps') == ['the owner brings the bicycle',
              'what is wrong is found', 'the owner takes it home'], B.get('steps'))
        body = B.get('body') or {}
        ops = body.get('ops') or []
        add = next((o for o in ops if o.get('op') == 'add'), {})
        chg = next((o for o in ops if o.get('op') == 'change'), {})
        check("Save sends a move from now on the repair's course to the step chosen, and the call with its new words, its "
              "owner and the one who calls as they were — nothing else", len(ops) == 2 and add.get('verb') == 'move'
              and add.get('roles') == {'of': 'self', 'through': 'course', 'by': 'sam', 'at': ['now', 'walk-repair#looked-at']}
              and chg.get('key') == 'can#call-back' and chg.get('roles') == {'by': 'sam', 'of': 'call the owner when the wheel is true',
                                                                           'to': OWNER}, body)
    if body:
        code = ("import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; import view_write; "
                "print(json.dumps(view_write.write('.', 'sam', %r, %r), default=str))" % (body.get('bean'), body.get('ops')))
        rc, out = run(PY, '-c', code)
        try:
            W = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            W = {'ok': False, 'output': out[-1500:]}
        bean = get('beans/repair-1.md')
        check("written through the view's one write path, the gate takes them: the repair has moved on, the call is in its "
              "new words to its owner as before", W.get('ok') is True and 'walk-repair#looked-at' in bean
              and 'call the owner when the wheel is true' in bean and f'to: {OWNER}' in bean, (W, bean[-600:]))
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_sheet_words: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
