#!/usr/bin/env python3
"""Bidi: the view's widgets and renderers in a browser, their VISUAL order in a right-to-left and a left-to-right page
(the view finished for a handplace, its §8; ported from a host's bidi lab, its method and its cases' shapes).

Each case is drawn in headless Chromium and read as it lands on the screen: one Range per character, sorted by the x of
its centre, so a case's text is read left to right as an eye would, whatever the logical order. A bidi control is not
read (it has no width). Then:

  the rules      what an isolate does, as plain HTML: a number isolated beside a currency's word, a negative one, a
                 fraction, inside a sentence of the other script, in a page of either direction, two side by side; a
                 right-to-left override held inside an isolate, and the same override, not held, reaching what follows
                 it — the lab's cases, their values invented
  the widgets    what money.js writes — an amount, an uneven one, a negative one — read in both directions, and never the
                 form the lab found broken (a conjunction or a plain slash inside a number, a mark in place of an
                 isolate)
  the drawings   the design's seven cases, drawn by the renderers themselves: a week row whose first day is the reader's
                 region's, at the start of the line in either script; a debt's arrow between two Persian names and
                 between a Persian and a Latin one; an amount with its currency inside right-to-left text, and an uneven
                 one; a sheet's label and a Latin value (a phone, a mail); a table's first column at the line's start in
                 a right-to-left page; a timeline's list in the reader's digits; a title in mixed scripts, held in its
                 isolate

Run: python3 test/bidi.py   (0 = green; a NOTE, and no check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
sys.path.insert(0, LIB)
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def read(path):
    with open(path, encoding='utf-8') as fh:
        return fh.read()


# THE RULES (the lab's `rules`, its values invented): (name, dir, html, the visual order read left to right)
N = 'dir="ltr" class="n"'
RULES = [
    ("a mixed number, isolated, then a currency's word", 'rtl', f'<bdi {N}>۱۲٬۳۴۵ ۱⁄۶</bdi> سکه', 'هکس ۱۲٬۳۴۵ ۱⁄۶'),
    ("a negative one", 'rtl', f'<bdi {N}>−۱٬۲۳۴</bdi> سکه', 'هکس −۱٬۲۳۴'),
    ("a negative fraction, then a currency's code", 'rtl', f'<bdi {N}>−۲⁄۳</bdi> XTS', 'XTS −۲⁄۳'),
    ("inside a Persian sentence", 'rtl', f'مانده <bdi {N}>۳۱۲٫۵۰</bdi> سکه است', 'تسا هکس ۳۱۲٫۵۰ هدنام'),
    ("the same amount in a left-to-right page", 'ltr', f'Balance <bdi {N}>−۱٬۲۳۴</bdi> سکه', 'Balance −۱٬۲۳۴ هکس'),
    ("two amounts side by side", 'rtl', f'<bdi {N}>۱۰۰</bdi> سکه، <bdi {N}>−۵۰</bdi> سکه', 'هکس −۵۰ ،هکس ۱۰۰'),
    ("a right-to-left override held inside an isolate", 'rtl', f'<bdi>abc\u202edef</bdi> <bdi {N}>۵</bdi>', '۵ abcfed'),
]
# the same override, NOT held: what it reaches is no longer what was written — read beside the same held in an isolate
LEAK = ('rtl', f'abc\u202edef <bdi {N}>۵</bdi> سکه', f'<bdi>abc\u202edef</bdi> <bdi {N}>۵</bdi> سکه')

PAGE = """<!doctype html><html lang="en" dir="ltr"><head><meta charset="utf-8"><style>%(css)s
body{font:20px system-ui,'Noto Sans Arabic',sans-serif}.box{width:960px;margin:4px;border:1px solid #ccc}</style>
<script type="application/json" id="orientations">%(orient)s</script></head><body><div id="static">%(static)s</div><div id="cases"></div>
<script>%(js)s</script>
<script>
const SKIP = /[\\u200e\\u200f\\u061c\\u2066-\\u2069\\u202a-\\u202e]/;
function visual(el) {
  const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), glyphs = [];
  for (let n = w.nextNode(); n; n = w.nextNode()) {
    if (n.parentElement && getComputedStyle(n.parentElement).display === 'none') continue;
    for (let i = 0; i < n.data.length; i++) {
      const ch = n.data[i]; if (SKIP.test(ch)) continue;
      const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1); const b = r.getBoundingClientRect();
      if (b.width > 0 || ch.trim()) glyphs.push([b.left + b.width / 2, ch]); } }
  glyphs.sort((a, b) => a[0] - b[0]);
  return glyphs.map(g => g[1]).join('').replace(/\\s+/g, ' ').trim();
}
const W = window.daftarWidgets, A = window.daftarArchetypes, out = {errs: [], static: {}, cases: {}};
window.addEventListener('error', e => out.errs.push(String(e.message)));
for (const b of document.querySelectorAll('#static .box')) out.static[b.id] = visual(b);
function page(dir, lang) { document.documentElement.dir = dir; document.documentElement.lang = lang;
  W.settings.configure({garden: {lang}, currencies: [{code: 'XTS', digits: '2'}]}); }
function box(dir) { const d = document.createElement('div'); d.className = 'box vw'; d.dir = dir; document.getElementById('cases').appendChild(d); return d; }
function tools(state) { return window.daftarEngraved.tools(state || {engraved: {}}); }
function x(el) { const b = el.getBoundingClientRect(); return b.left + b.width / 2; }
try {
  // 1. A WEEK ROW: the first day the reader's region begins a week on, at the start of the reader's line
  const week = (dir, lang) => { page(dir, lang); const d = box(dir);
    A.timeline(d, {today: '2026-10-14', from: '2026-09-01', to: '2026-11-30', layouts: ['week'], events: [], notes: []}, tools(), {engraved: {axes: {inline: 'time'}}});
    const cells = [...d.querySelectorAll('.eg-week .eg-day')], xs = cells.map(x);
    const first = cells[0], firstX = x(first), atStart = dir === 'rtl' ? firstX === Math.max(...xs) : firstX === Math.min(...xs);
    const later = dir === 'rtl' ? xs.every((v, i) => i === 0 || v < xs[i - 1]) : xs.every((v, i) => i === 0 || v > xs[i - 1]);
    return {first: first.dataset.day, weekday: new Date(first.dataset.day + 'T12:00Z').getUTCDay(), atStart, later,
            head: visual(first.querySelector('.eg-day-head'))}; };
  out.cases.weekFa = week('rtl', 'fa'); out.cases.weekGb = week('ltr', 'en-GB');
  // 2. A DEBT'S ARROW: from the one who owes, at the line's start, to the one owed, the glyph of `next` between
  const flow = (dir, lang, from, to) => { page(dir, lang); const d = box(dir);
    A.flows(d, {nodes_are: 'parties', nodes: [{id: 'p1', title: from}, {id: 'p2', title: to}], arrows: [{from: 'p1', to: 'p2', count: '200/3', unit: 'XTS', uneven: true}], partial: false}, tools(), {engraved: {axes: {inline: 'flow'}}});
    return visual(d.querySelector('.eg-ends')); };
  out.cases.flowFaFa = flow('rtl', 'fa', 'سام', 'علی'); out.cases.flowFaLatin = flow('rtl', 'fa', 'Sam', 'علی');
  out.cases.flowEn = flow('ltr', 'en', 'Sam', 'Ali');
  // 3. AN AMOUNT AND ITS CURRENCY INSIDE RIGHT-TO-LEFT TEXT, and one that does not come out even
  page('rtl', 'fa'); let d = box('rtl');
  W.safe.mount(d, W.safe.h`<span id="m1">مانده ${W.money.show('312.50', 'XTS')} است</span> <span id="m2">${W.money.show('200/3', 'XTS', {fraction: 'inline'})}</span>`);
  out.cases.amount = visual(d.querySelector('#m1')); out.cases.uneven = visual(d.querySelector('#m2'));
  page('ltr', 'en'); d = box('ltr');
  W.safe.mount(d, W.safe.h`<span id="m3">Balance ${W.money.show('-1234', 'XTS')}</span>`);
  out.cases.amountEn = visual(d.querySelector('#m3'));
  page('rtl', 'fa'); d = box('rtl');
  W.safe.mount(d, W.safe.h`<span id="f1">${W.money.show('200/3', 'XTS')}</span> <span id="f2">${W.money.show('-1234', 'XTS')}</span>`);
  out.cases.forms = ['#f1', '#f2'].map(s => { const n = d.querySelector(s + ' .w-num');
    return {text: n.textContent, isolate: n.tagName === 'BDI' && n.getAttribute('dir') === 'ltr'}; });
  // 4. A SHEET'S LABEL AND A LATIN VALUE: a phone and a mail, in a right-to-left page
  page('rtl', 'fa'); d = box('rtl');
  const sheet = {bean: 'ali', kind: 'person', title: 'علی', header: {title: {value: 'علی', may: false}}, details: {}, may_write: false, statements: ['phone', 'mail'],
    rows: [{verb: 'name', may_add: false, statements: [
      {key: 'name#phone', verb: 'name', id: 'phone', may: false, roles: {by: 'e164', of: 'self', as: '+1 555 555 0100'}, dependents: [], defaults: []},
      {key: 'name#mail', verb: 'name', id: 'mail', may: false, roles: {by: 'mail', of: 'self', as: 'ali@example.org'}, dependents: [], defaults: []}]}],
    verbs: {name: {verb: 'name', meaning: '', roles: {by: {shape: ['being', 'row']}, of: {shape: ['being']}, as: {shape: ['text']}}, qualifiers: {}, required: ['by', 'of', 'as']}}};
  A.sheet(d, sheet, tools(), null);
  const asOf = key => visual(d.querySelector('[data-fact="' + key + '"] [data-role="as"]'));
  out.cases.phone = asOf('name#phone'); out.cases.mail = asOf('name#mail');
  const lab = d.querySelector('[data-fact="name#phone"] [data-role="as"] .eg-role-name'), val = d.querySelector('[data-fact="name#phone"] [data-role="as"] .w-text');
  out.cases.labelFirst = x(lab) > x(val);
  // 5. A TABLE'S COLUMN ORDER IN A RIGHT-TO-LEFT PAGE: its first column at the start of the line
  page('rtl', 'fa'); d = box('rtl');
  window.viewMount(d, {title: 'جدول', claim: '', key: 't', levels: [{id: 'operate', form: 'health-chain', name: 'operate', question: ''}],
    operate: {archetype: 'table', table: {columns: ['نام', 'مبلغ'], rows: [{cells: ['علی', '12']}]}, notes: [], blind: [], correlate: []}}, {level: 'operate'});
  const ths = [...d.querySelectorAll('th')];
  out.cases.table = ths.length === 2 && x(ths[0]) > x(ths[1]);
  // 6. A TIMELINE'S LIST: each day in the reader's digits and calendar
  const list = (dir, lang) => { page(dir, lang); const dd = box(dir);
    A.timeline(dd, {today: '2026-10-14', from: '2026-10-01', to: '2026-10-31', layouts: ['list'], notes: [],
      events: [{day: '2026-10-14', bean: 'loan', title: 'loan', kind: 'due', what: 'قسط', index: 2, times: '6'}]}, tools(), {engraved: {axes: {inline: 'time'}}});
    return visual(dd.querySelector('.eg-list-when')); };
  out.cases.listFa = list('rtl', 'fa'); out.cases.listEn = list('ltr', 'en');
  // 7. A TITLE IN MIXED SCRIPTS, held in its isolate between a label and a number
  page('rtl', 'fa'); d = box('rtl');
  W.safe.mount(d, W.safe.h`<p id="t1">عنوان: ${W.text.show('loan — وام سام به علی، Sam to Ali')} ${W.number.show('3')}</p>`);
  out.cases.title = visual(d.querySelector('#t1')); out.cases.titleOnly = visual(d.querySelector('#t1 .w-text'));
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""

browser = next((b for b in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(b)), None)
if not browser:
    print("NOTE  no Chromium on this machine: the visual order is not read here")
    print("\nbidi: 0 failed")
    sys.exit(0)

import view_widgets  # noqa: E402
static = ''.join(f'<div class="box" id="r{i}" dir="{d}">{h}</div>' for i, (_n, d, h, _w) in enumerate(RULES)) + \
    f'<div class="box" id="leak" dir="{LEAK[0]}">{LEAK[1]}</div><div class="box" id="held" dir="{LEAK[0]}">{LEAK[2]}</div>'
js = view_widgets.bundle() + read(os.path.join(LIB, 'widgets', 'direction.js')) + ''.join(
    read(os.path.join(LIB, f)) for f in ('view_engraved.js', 'view_queue.js', 'view_timeline.js', 'view_flows.js',
                                         'view_sheet.js', 'view_runtime.js'))
sys.path.insert(0, ROOT)
from core.law import Law  # noqa: E402
orient = json.dumps([{k: r[k] for k in ('order', 'axis', 'sense', 'follows', 'commands') if k in r}
                     for r in Law.load().profile_tables.get('orientations') or []])
T = tempfile.mkdtemp(prefix='bidi-')
try:
    path = os.path.join(T, 'bidi.html')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(PAGE % {'css': view_widgets.css() + read(os.path.join(LIB, 'view_engraved.css')), 'orient': orient,
                         'static': static, 'js': js})
    r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                        '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                       timeout=180)
    m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
    out = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]], 'static': {}, 'cases': {}}
    S, C = out.get('static') or {}, out.get('cases') or {}
    check("the cases are drawn in Chromium with no exception", not out['errs'], out['errs'])
    for i, (name, d, _h, want) in enumerate(RULES):
        check(f"rule, {d}: {name} — reads «{want}»", S.get(f'r{i}') == want, S.get(f'r{i}'))
    check("rule: the same override NOT held in an isolate reaches what follows it — it is not read as the held one is",
          S.get('leak') and S.get('held') and S.get('leak') != S.get('held'), (S.get('leak'), S.get('held')))
    forms = C.get('forms') or [{}, {}]
    check("widget: money.js never writes the form that broke — no conjunction and no plain slash inside a number, no "
          "mark in place of an isolate: the number in a left-to-right isolate, an uneven one with the fraction slash",
          all(f.get('isolate') and not re.search('[\u0648/\u200e\u200f]', f.get('text', '/')) for f in forms)
          and '\u2044' in forms[0].get('text', ''), forms)
    wf, wg = C.get('weekFa') or {}, C.get('weekGb') or {}
    check("week, rtl (fa): the first day is Saturday — CLDR's first day for the reader's region — at the start of the "
          "line, the right, and each later day further along it", wf.get('weekday') == 6 and wf.get('atStart') and wf.get('later'), wf)
    check("week, ltr (en-GB): the first day is Monday, at the start of the line, the left", wg.get('weekday') == 1
          and wg.get('atStart') and wg.get('later'), wg)
    check("flow, rtl: between two Persian names the arrow points from the one who owes, at the line's start, to the one "
          "owed — «علی ← سام» read left to right", C.get('flowFaFa') == 'یلع ← ماس', C.get('flowFaFa'))
    check("flow, rtl: between a Latin and a Persian name the same — «Sam», then ←, then «علی»", C.get('flowFaLatin') == 'یلع ← Sam',
          C.get('flowFaLatin'))
    check("flow, ltr: the arrow turns with the script — «Sam → Ali»", C.get('flowEn') == 'Sam → Ali', C.get('flowEn'))
    check("amount, rtl: inside a Persian sentence the number reads as written and its code follows it on the line",
          C.get('amount') == 'تسا XTS ۳۱۲٫۵۰ هدنام', C.get('amount'))
    check("amount, rtl: one that does not come out even is the fraction it is, marked, never rounded — «۶۶ ۲⁄۳»",
          C.get('uneven') == 'XTS *۶۶ ۲⁄۳', C.get('uneven'))
    check("amount, ltr: a negative amount, its sign first", C.get('amountEn') == 'Balance −1,234.00 XTS', C.get('amountEn'))
    check("sheet, rtl: a phone reads left to right as it is written, beside its label", C.get('phone', '').endswith('+1 555 555 0100')
          or C.get('phone', '').startswith('+1 555 555 0100'), C.get('phone'))
    check("sheet, rtl: a mail reads as it is written, and the label stands at the line's start, the value after it",
          'ali@example.org' in (C.get('mail') or '') and C.get('labelFirst') is True, (C.get('mail'), C.get('labelFirst')))
    check("table, rtl: the first column stands at the start of the line, the right", C.get('table') is True, C.get('table'))
    check("timeline list, fa: the day in the reader's digits and calendar", re.search('[۰-۹]', C.get('listFa') or '')
          and not re.search('[0-9]', C.get('listFa') or '') and '۱۴۰۵' in (C.get('listFa') or ''), C.get('listFa'))
    check("timeline list, en: the same day in the Latin digits and the Gregorian calendar", '2026' in (C.get('listEn') or '')
          and not re.search('[۰-۹]', C.get('listEn') or ''), C.get('listEn'))
    t, t1 = C.get('title') or '', C.get('titleOnly') or ''
    check("title, rtl: a title in mixed scripts keeps its Latin words in order, and is held in its isolate — its letters "
          "one unbroken run between the label and the number", 'Sam to Ali' in t1 and t1 in t and 'loan' in t1, (t, t1))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nbidi: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
