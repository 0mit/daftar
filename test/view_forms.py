#!/usr/bin/env python3
"""A form's value on a sheet, drawn by its entries (assets/view/lib/widgets/form.js, recurrence.js): what a clause holds
beside its words — the day it falls due, how it repeats, its notice, its state — and what a payment settles, each
attribute by the widget that implements its value (core/law/values.yaml `implements`), never a JSON text to type into.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it; a class meets each Tuesday of
an ISO week, its first session an attendance at a moment and its repetition a clause over it that lasts ninety minutes;
a rent falls due each month, and a payment settles its first; a person who pays it is kept under an opaque id; a page
draws a sheet of each. Then:

  the reading   a sheet carries the forms its verbs' qualifiers hold, each attribute with the value it holds: a clause's
                `due` a moment, `every` a repetition, `notice` a length of time, `state` a choice of the law's rows; a
                settlement's `clause` a choice of the bean's own clauses, its `amount` a quantity; and the page's settings
                carry the law's time systems a repetition is counted in, and its units of a length of time
  a browser     drawn in Persian, right to left: the class's repetition is said in the reader's words, calendar and
                digits («هر هفته …», ۹۰), the rent's settlement by its entries, and no form's value as JSON; Edit draws the
                repetition's days of the week as the reader's region begins a week, and no JSON text field; Thursday is
                added and Save sends one change of the clause, its other attributes as written
  the write     that change, written through the view's one write path (view_write), passes the core's gate: the clause
                now repeats on Tuesday and Thursday, and nothing else of it changed
  bidi          the repetition said in Persian inside a right-to-left line reads as written: its numbers whole and in
                their place

Run: python3 test/view_forms.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import datetime, html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []


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


def py(code):
    """What the view reads in the garden, as JSON: `code` an expression over view_model (vm) and view_engraved (ve)."""
    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
                  "import view_model as vm, view_engraved as ve; vm.init('.', 'page'); may = lambda *a, **k: True; "
                  "print(json.dumps(%s, default=str, ensure_ascii=False))" % code)
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


T = tempfile.mkdtemp(prefix='view-forms-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
TODAY = datetime.date.today()
FIRST = TODAY - datetime.timedelta(days=(TODAY.isoweekday() - 2) % 7)   # the latest Tuesday
WEEK = f"{FIRST.isocalendar()[0]}-W{FIRST.isocalendar()[1]:02d}-2"
PAYER = 'p-0a1b2c3d'
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    put(f'beans/{PAYER}.md', f'''---
bean: {PAYER}
kind: person
title: "{PAYER}"
summary: "who rents the room, kept under an opaque id"
statements:
  - say: {{ by: sam, at: now }}
  - own: {{ by: theone, of: self }}
---
A person.
''')
    put('beans/class-yoga.md', f'''---
bean: class-yoga
kind: event
title: "class-yoga"
summary: "a class Sam attends each Tuesday"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - attend: {{ id: attends, by: sam, of: self, at: "{FIRST.isoformat()}T18:00+03:00/{FIRST.isoformat()}T19:30+03:00" }}
  - can:    {{ id: weekly, by: sam, of: attends, clause: {{ due: "{FIRST.isoformat()}", every: {{ of: time, in: iso-week, each: week, at: ["2"], from: "{WEEK}", lasts: {{ of: time, measure: {{ count: "90", unit: min }} }} }} }} }}
---
A class.
''')
    put('beans/rent.md', f'''---
bean: rent
kind: contract
title: "rent"
summary: "a room rented from Sam"
statements:
  - say:         {{ by: sam, at: now }}
  - own:         {{ by: theone, of: self }}
  - agree:       {{ id: a, by: [sam, {PAYER}], of: self, through: spoken, at: "{FIRST.isoformat()}" }}
  - reckon:      {{ id: months, reading: {{ what: "the lease itself, once", steps: [ {{ id: p, op: select, kind: contract, where: [ {{ path: bean, "=": rent }} ] }} ] }} }}
  - pay:         {{ id: monthly, by: {PAYER}, to: sam, of: {{ count: "400.00", unit: XTS }} }}
  - obligatory:  {{ id: rent-due, of: monthly, through: a, clause: {{ each: months }} }}
  - pay:         {{ id: paid-first, by: {PAYER}, to: sam, of: {{ count: "400.00", unit: XTS }}, at: "{FIRST.isoformat()}", settles: [ {{ clause: rent-due, occurrence: rent, amount: {{ count: "400.00", unit: XTS }} }} ] }}
---
A rent.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's page"
summary: "the class and the rent"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw:   {{ id: yoga, by: self, of: [class-yoga], drawing: {{ label: Class, archetype: sheet, {STORY.format(p='the class')} }} }}
  - draw:   {{ id: room, by: self, of: [rent], drawing: {{ label: Rent, archetype: sheet, {STORY.format(p='the rent')} }} }}
  - draw:   {{ id: page, by: self, of: [yoga, room], page: {{ fields: [ {{ kind: event, fact: attend, shown_from: understand }}, {{ kind: event, fact: can, shown_from: understand }}, {{ kind: contract, fact: pay, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'a class, a rent and a page of their sheets', '--body',
                  f'- action: wrote [[{PAYER}]], [[class-yoga]], [[rent]] and [[page]]')
    check("the class, the rent and the page are saved through the core's gate", rc == 0 and '0 error(s)' in out, out[-1500:])

    # ------------------------------------------------------------------ the reading
    R = py("{'yoga': ve.sheet('class-yoga', may), 'rent': ve.sheet('rent', may), 'settings': ve.settings()}")
    clause = (((R.get('yoga') or {}).get('forms') or {}).get('clause') or {}).get('attrs') or {}
    check("a sheet carries the clause's form: `due` a moment, `every` a repetition, `notice` a length of time, `state` a "
          "choice of the law's rows", (clause.get('due') or {}).get('value') in ('moment', 'day')
          and (clause.get('every') or {}).get('value') == 'recurrence' and (clause.get('notice') or {}).get('value') == 'duration'
          and (clause.get('state') or {}).get('value') == 'choice' and 'met' in ((clause.get('state') or {}).get('rows') or []),
          {k: clause.get(k) for k in ('due', 'every', 'notice', 'state')} or R.get('error'))
    sett = (((R.get('rent') or {}).get('forms') or {}).get('settlement') or {}).get('attrs') or {}
    check("...and the settlement's: `clause` a choice of the bean's own clauses, `amount` a quantity",
          (sett.get('clause') or {}).get('rows') == ['rent-due'] and (sett.get('amount') or {}).get('value') == 'quantity', sett)
    S = R.get('settings') or {}
    systems = {s.get('system'): s for s in S.get('systems') or []}
    check("the page's settings carry the law's time systems a repetition is counted in (ISO weeks with a week, the "
          "Persian calendar by its prefix) and its units of a length of time",
          (systems.get('iso-week') or {}).get('week') is True and (systems.get('persian-calendar') or {}).get('prefix') == 'persian:'
          and {'min', 'h', 'd'} <= {d.get('unit') for d in S.get('durations') or []}, (sorted(systems), S.get('durations')))

    # ------------------------------------------------------------------ a browser
    browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
    body = None
    if not browser:
        print("NOTE  the sheets were not drawn in a browser: none on this machine")
    else:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s
body{font:18px system-ui,'Noto Sans Arabic',sans-serif}</style></head><body><div id="yoga" class="vw" dir="rtl"></div>
<div id="rent" class="vw" dir="rtl"></div><script>%(js)s</script><script>
const SKIP = /[\\u200e\\u200f\\u061c\\u2066-\\u2069\\u202a-\\u202e]/;
function visual(el) {
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), glyphs = [];
  for (let n = w.nextNode(); n; n = w.nextNode()) for (let i = 0; i < n.data.length; i++) {
    const ch = n.data[i]; if (SKIP.test(ch)) continue;
    const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); const b = r.getBoundingClientRect();
    if (b.width > 0 || ch.trim()) glyphs.push([b.left + b.width / 2, ch]); }
  glyphs.sort((a, b) => a[0] - b[0]);
  return glyphs.map(g => g[1]).join('').replace(/\\s+/g, ' ').trim();
}
const out = {errs: []}, E = {settings: Object.assign({}, %(settings)s, {garden: {lang: 'fa', calendar: 'persian'}}), names: {}};
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const A = window.daftarArchetypes, t = state => window.daftarEngraved.tools(Object.assign({engraved: E}, state || {}));
  const yoga = document.getElementById('yoga'), rent = document.getElementById('rent');
  A.sheet(rent, %(rent)s, t(), null);
  const settles = rent.querySelector('[data-fact="pay#paid-first"] [data-role="settles"]');
  out.settles = settles ? settles.innerText : null;
  out.settlesForm = !!(settles && settles.querySelector('.w-form'));
  A.sheet(yoga, %(yoga)s, t({write: body => { out.body = body; return new Promise(() => {}); }}), null);
  const said = yoga.querySelector('[data-fact="can#weekly"] [data-role="clause"]');
  out.said = said ? said.innerText : null;
  const rec = said && said.querySelector('.w-recurrence');
  out.bidi = rec ? {visual: visual(rec), logical: rec.textContent} : null;
  out.jsonShown = /[{}"]/.test(out.said || '') || /[{}"]/.test(out.settles || '');
  yoga.querySelector('[data-do="edit"]').click();
  const field = yoga.querySelector('[data-fact="can#weekly"] [data-role="clause"]');
  out.jsonField = !!(field && field.querySelector('textarea, [name$=".json"]'));
  const days = field ? [...field.querySelectorAll('input[type="checkbox"][name$=".every.at"]')] : [];
  out.days = days.map(b => b.value); out.checked = days.filter(b => b.checked).map(b => b.value);
  const thu = days.find(b => b.value === '4'); if (thu) thu.click();
  yoga.querySelector('[data-do="save"]').click();
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'forms.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'settings': json.dumps(S, ensure_ascii=False),
                             'yoga': json.dumps(R.get('yoga') or {}, ensure_ascii=False),
                             'rent': json.dumps(R.get('rent') or {}, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        check("in Persian, the class's repetition is said in the reader's words, calendar and digits — «هر هفته», ۹۰ — "
              "and no form's value is shown as JSON", not B['errs'] and 'هر هفته' in (B.get('said') or '')
              and '۹۰' in (B.get('said') or '') and not re.search('[0-9]', re.sub(r'\d{4}-\d{2}-\d{2}', '', B.get('said') or ''))
              and not B.get('jsonShown'), B)
        check("...the rent's settlement drawn by its entries — its clause, its amount in Persian digits", B.get('settlesForm')
              and 'rent-due' in (B.get('settles') or '') and '۴۰۰' in (B.get('settles') or ''), B)
        week = [str(d) for d in (6, 7, 1, 2, 3, 4, 5)]          # Saturday first: CLDR's first day for a Persian reader
        check("Edit draws the repetition's days of the week, as the reader's region begins a week, Tuesday checked, and "
              "no JSON text field", not B['errs'] and not B.get('jsonField') and B.get('days') == week
              and B.get('checked') == ['2'], B)
        body = B.get('body') or {}
        ops = body.get('ops') or []
        check("Thursday added, Save sends one change of the clause, its other attributes as written",
              body.get('bean') == 'class-yoga' and len(ops) == 1 and ops[0].get('op') == 'change'
              and ops[0].get('key') == 'can#weekly'
              and (ops[0].get('roles') or {}).get('clause', {}).get('every', {}).get('at') == ['2', '4']
              and (ops[0].get('roles') or {}).get('clause', {}).get('every', {}).get('lasts') == {'of': 'time', 'measure': {'count': '90', 'unit': 'min'}}
              and (ops[0].get('roles') or {}).get('clause', {}).get('due') == FIRST.isoformat(), body)
        bd = B.get('bidi') or {}
        logical = re.sub('[\u2066-\u2069\u200e\u200f]', '', bd.get('logical') or '').strip()
        # read right to left, a Persian line is its letters in reverse, each number — a day's ۱۴۰۵/۰۷/۱۴ too — kept whole,
        # in its own order
        want = ''.join(reversed(re.findall('[۰-۹]+(?:[/٫٬:][۰-۹]+)*|.', logical, re.S)))
        check("bidi: the repetition said in Persian, in a right-to-left line, reads as written — its numbers whole and in "
              "their place", bd and re.sub(r'\s+', ' ', bd.get('visual') or '') == re.sub(r'\s+', ' ', want).strip(), bd)

    # ------------------------------------------------------------------ the write
    if body:
        code = ("import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; import view_write; "
                "print(json.dumps(view_write.write('.', 'sam', %r, %r), default=str))" % (body.get('bean'), body.get('ops')))
        rc, out = run(PY, '-c', code)
        try:
            W = json.loads(out.strip().splitlines()[-1])
        except (ValueError, IndexError):
            W = {'ok': False, 'output': out[-1500:]}
        after = py("[r for _i, v, r in vm.CORE.G.beans['class-yoga'].items if v == 'can'][0]")
        check("that change, through the view's one write path, passes the core's gate: the class repeats on Tuesday and "
              "Thursday, and nothing else of its clause changed", W.get('ok') is True
              and (after.get('clause') or {}).get('every') == {'of': 'time', 'in': 'iso-week', 'each': 'week', 'at': ['2', '4'],
                                                             'from': WEEK, 'lasts': {'of': 'time', 'measure': {'count': '90', 'unit': 'min'}}}
              and (after.get('clause') or {}).get('due') == FIRST.isoformat(), (W, after))
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_forms: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
