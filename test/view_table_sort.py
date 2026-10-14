#!/usr/bin/env python3
"""A reading's table sorts by each of its columns (the operator, 2026-10-14: lists are better sortable).

A reading's table (view_table.js, the `table` archetype) is drawn in a browser, in Persian, from a reading of invented
lines — a title, an amount in a currency with places, a day and a word — and each column's head is pressed:

  heads      each column's head is a button, its `aria-sort` none until pressed
  amounts    pressed once, rising by the exact amount — 2/3 before 1 before 9650/3 — never by the digits drawn (۳٬۲۱۶٫۶۷
             would sort before ۹۰۰ as text); pressed again, falling; the empty cell last both ways
  days       by the day as the law writes it, not the Persian calendar's text
  words      in Persian's order (CLDR's collation), the being's title where the column is the title
  lines      the lines are moved, not drawn again: a line keeps its button that opens its being

Run: python3 test/view_table_sort.py   (0 = green; a NOTE, and no check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


LINES = [  # bean, title, amount, day, word
    ('l1', 'سیب', {'count': '9650/3', 'unit': 'TRY'}, '2026-10-01', 'بادام'),
    ('l2', 'انار', {'count': '1', 'unit': 'TRY'}, '2026-09-15', 'پسته'),
    ('l3', 'به', {'count': '2/3', 'unit': 'TRY'}, '2026-12-30', 'آلبالو'),
    ('l4', 'گیلاس', None, '2025-01-02', 'زرشک'),
    ('l5', 'آلو', {'count': '900', 'unit': 'TRY'}, '2026-03-21', 'توت'),
]
E = {'settings': {'garden': {'lang': 'fa'}, 'currencies': [{'code': 'TRY', 'digits': '2'}]},
     'drawings': {'t': {'columns': [{'path': 'title', 'label': 'نام'}, {'path': 'amount', 'label': 'مبلغ'},
                                    {'path': 'day', 'label': 'روز'}, {'path': 'word', 'label': 'واژه'}],
                        'rows': [{'bean': b, 'title': t, 'cells': [t, [a] if a else [], [d], [w]]} for b, t, a, d, w in LINES]}}}

browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
if not browser:
    print("NOTE  the table was not drawn in a browser: none on this machine")
else:
    T = tempfile.mkdtemp(prefix='view-table-sort-')
    try:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_table.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="t" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: [], orders: {}}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E}), el = document.getElementById('t');
  window.daftarArchetypes.table(el, E.drawings.t, t, null);
  const order = () => [...el.querySelectorAll('tbody tr')].map(tr => tr.dataset.bean);
  const press = i => el.querySelector('button.eg-sort[data-sort="' + i + '"]').click();
  out.heads = [...el.querySelectorAll('thead th')].map(th => [!!th.querySelector('button.eg-sort'), th.getAttribute('aria-sort')]);
  out.orders.start = order();
  press(1); out.orders.amountUp = order(); out.sort1 = el.querySelector('thead th[data-path="amount"]').getAttribute('aria-sort');
  press(1); out.orders.amountDown = order(); out.sort2 = el.querySelector('thead th[data-path="amount"]').getAttribute('aria-sort');
  press(2); out.orders.dayUp = order();
  press(3); out.orders.wordUp = order();
  press(0); out.orders.titleUp = order();
  out.openers = [...el.querySelectorAll('tbody tr')].map(tr => !!tr.querySelector('[data-action="open"], .w-being, button, a'));
  out.drawn = [...el.querySelectorAll('tbody tr')].map(tr => tr.dataset.line);
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'sort.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(E, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180, env=dict(os.environ, TMPDIR=T))     # what the browser leaves, in the folder that goes
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        O = B.get('orders') or {}
        check("heads: each column's head is a button, unsorted until pressed",
              not B['errs'] and B.get('heads') and all(b and s == 'none' for b, s in B['heads']), B)
        check("amounts: rising by the exact amount (2/3, 1, 900, 9650/3), the empty cell last; again, falling, the empty "
              "still last",
              O.get('amountUp') == ['l3', 'l2', 'l5', 'l1', 'l4'] and O.get('amountDown') == ['l1', 'l5', 'l2', 'l3', 'l4']
              and B.get('sort1') == 'ascending' and B.get('sort2') == 'descending', B)
        check("days: by the day as the law writes it", O.get('dayUp') == ['l4', 'l5', 'l2', 'l1', 'l3'], O)
        check("words: in Persian's order", O.get('wordUp') == ['l3', 'l1', 'l2', 'l5', 'l4'], O.get('wordUp'))
        check("titles: the being's title, in Persian's order", O.get('titleUp') == ['l5', 'l2', 'l3', 'l1', 'l4'], O)
        check("lines: moved, never drawn again — each keeps what opens its being", all(B.get('openers') or [False]), B)
    finally:
        shutil.rmtree(T, ignore_errors=True)

print(f"\nview_table_sort: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
