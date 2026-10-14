#!/usr/bin/env python3
"""A payment's shares in its form (the operator, 2026-10-14: "one button, one form"; the share walk's form on the
payment's own line — a person beside their `share`).

A sheet of a payment of 90 is drawn in a browser, in Persian, its shares as they stand (Sam 2/3, Ali 1/3), with the share
walk's action on its line. Its form:

  prefilled   opens with each one's share as it stands now, in whole parts over the shares' common denominator: Sam 2,
              Ali 1 — the form shows what is, before anyone changes it
  live        beside each row, that one's part of the whole as the fraction it is and the amount it comes to — Sam 2/3
              (60), Ali 1/3 (30) — and again as the form is changed: given 1 and 1, a half each, 45 each
  amounts     shares that add up to the payment are each one's amount: 70 and 20, read 7/9 (70) and 2/9 (20)
  only its    a form whose rows are not the share walk's (no input `share`) is drawn as it was: no column of parts

Run: python3 test/view_share_form.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [os.path.join(ROOT, 'assets', 'view', 'lib'), os.path.join(ROOT, 'bin'), ROOT]
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


SAY = {'act': 'say'}
CHOICES = [{'value': 'sam', 'label': 'سام'}, {'value': 'ali', 'label': 'علی'}]
SHARE = {'el': 'pay', 'tool': 'share', 'note': 'سهم‌ها', 'drawing': 'card', 'inputs': [
    {'name': 'of', 'origin': SAY, 'from': 'self'},
    {'name': 'who', 'origin': SAY, 'of': 'sharers', 'many': 'true', 'note': 'چه کسی', 'choices': CHOICES},
    {'name': 'share', 'origin': SAY, 'type': 'count', 'many': 'true', 'beside': 'who', 'note': 'سهم'}]}
OTHER = dict(SHARE, tool='parts', inputs=[SHARE['inputs'][0], SHARE['inputs'][1],
                                          dict(SHARE['inputs'][2], name='parts')])
PAY = {'key': 'pay#meal', 'verb': 'pay', 'id': 'meal', 'may': True, 'known': None, 'dependents': [], 'defaults': [],
       'roles': {'by': 'sam', 'of': {'count': '90', 'unit': 'XTS'}, 'at': '2026-10-03'},
       'shares': {'source': 'payment', 'unit': 'XTS', 'owes': [],
                  'bearers': [{'bean': 'sam', 'title': 'سام', 'share': '2/3', 'amount': '60'},
                              {'bean': 'ali', 'title': 'علی', 'share': '1/3', 'amount': '30'}]}}


def sheet(action):
    return {'bean': 'dinner', 'kind': 'contract', 'title': 'شام', 'forms': {}, 'header': {}, 'details': {}, 'records': [],
            'labels': {}, 'said': {}, 'courses': [], 'statements': ['meal'], 'new': False, 'may_write': True,
            'rows': [{'verb': 'pay', 'statements': [PAY], 'may_add': True}],
            'verbs': {'pay': {'roles': {'by': {'shape': ['being']}, 'of': {'shape': ['quantity']}}, 'qualifiers': {},
                              'required': ['by', 'of'], 'meaning': ''}},
            'actions': [action], 'readings': []}


E = {'settings': {'garden': {'lang': 'fa'}, 'currencies': [{'code': 'XTS', 'places': 2}]},
     'sheets': {'dinner': sheet(SHARE), 'other': sheet(OTHER)},
     'beings': [{'id': 'sam', 'title': 'سام', 'kind': 'person'}, {'id': 'ali', 'title': 'علی', 'kind': 'person'}]}

browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
if not browser:
    print("NOTE  the form was not drawn in a browser: none on this machine")
else:
    T = tempfile.mkdtemp(prefix='view-share-form-')
    try:
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="s" class="vw light" dir="rtl"></div><div id="o" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E, act: () => new Promise(() => {})});
  const el = document.getElementById('s');
  window.daftarArchetypes.sheet(el, E.sheets.dinner, t, null);
  el.querySelector('[data-act-row]').click();
  const table = el.querySelector('table.eg-rows'), rows = () => [...table.tBodies[0].rows];
  const read = () => rows().map(tr => [tr.querySelector('[data-row-value]').getAttribute('data-row-value'),
                                       tr.querySelector('[name="act.share"]').value, tr.querySelector('td.eg-part').textContent.trim()]);
  out.heads = [...table.tHead.rows[0].cells].map(c => c.textContent.trim());
  out.prefilled = read();
  const set = (a, b) => { const [r1, r2] = rows(); r1.querySelector('[name="act.share"]').value = a; r2.querySelector('[name="act.share"]').value = b;
                          table.dispatchEvent(new Event('input', {bubbles: true})); };
  set('1', '1'); out.halves = read();
  set('70', '20'); out.amounts = read();
  const o = document.getElementById('o');
  window.daftarArchetypes.sheet(o, E.sheets.other, t, null);
  o.querySelector('[data-act-row]').click();
  out.otherHeads = [...o.querySelector('table.eg-rows').tHead.rows[0].cells].map(c => c.textContent.trim());
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'form.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(E, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180, env=dict(os.environ, TMPDIR=T))
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        fa = lambda s: s.translate(str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹'))
        part = lambda rows: {who: re.sub(r'\s+', ' ', p) for who, _v, p in rows or []}
        pre = B.get('prefilled') or []
        check("prefilled: the form opens with each one's share as it stands, in whole parts — Sam 2, Ali 1 — and a column "
              "of each one's part", not B['errs'] and B.get('heads') == ['چه کسی', 'سهم', 'سهم از کل']
              and {who: v for who, v, _p in pre} == {'sam': '2', 'ali': '1'}, B)
        p0 = part(pre)
        check("live: beside each row, its part of the whole as the fraction it is and the amount it comes to — Sam 2/3 "
              "(60), Ali 1/3 (30)", fa('2') in p0.get('sam', '') and fa('3') in p0.get('sam', '') and fa('60') in p0.get('sam', '')
              and fa('30') in p0.get('ali', ''), p0)
        p1 = part(B.get('halves'))
        check("...and again as the form is changed: given 1 and 1, a half each, 45 each",
              all(fa('45') in p1.get(k, '') and fa('2') in p1.get(k, '') for k in ('sam', 'ali')), p1)
        p2 = part(B.get('amounts'))
        check("amounts: shares that add up to the payment are each one's amount — 70 and 20, read 7/9 (70) and 2/9 (20)",
              fa('70') in p2.get('sam', '') and fa('9') in p2.get('sam', '') and fa('20') in p2.get('ali', ''), p2)
        check("only its own: a form whose rows are not the share walk's is drawn as it was, with no column of parts",
              B.get('otherHeads') == ['چه کسی', 'سهم'], B.get('otherHeads'))
    finally:
        shutil.rmtree(T, ignore_errors=True)

print(f"\nview_share_form: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
