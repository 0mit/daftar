#!/usr/bin/env python3
"""A code of a scheme shown by its name: what a page holds as `<scheme>:<code>` — an account a payment is booked to, a
code a being is classified by — is drawn by its name in the scheme's own table, read by the one reader
(bin/knowledge.py), in the reader's language where the table carries it; the code itself is kept beside the name, for
whoever needs it.

A garden of the core is grown here (test/grow.py) taking the view and accounting profiles: Sam keeps a bicycle shop
and its own chart of accounts (a scheme of the garden, its table an extract with a Persian name for each account); a
repair's receipt books what was paid to two accounts. A page draws the receipts as a table, each line opening its sheet.
Then:

  the page      the page's readings carry each account the receipts are booked to by its name: in Persian, the
                table's Persian; with no language, the table's own
  a browser     in Persian, the table's cell and the sheet's booking read the accounts' names, never `till:1010`; the
                code is beside each, in its title

Run: python3 test/view_code_names.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
"""
import html, json, os, re, shutil, subprocess, sys, tempfile

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


def get(rel):
    with open(os.path.join(G, rel), encoding='utf-8') as fh:
        return fh.read()


def last_json(out):
    try:
        return json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'error': out[-1500:]}


T = tempfile.mkdtemp(prefix='view-code-names-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
CASH, INCOME = 'صندوق کارگاه', 'درآمد تعمیر'
PAGE = """import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_engraved as ve
vm.init('.', 'page')
p = ve.page(lambda *a, **k: True, 'sam')
plain = dict(p.get('codes') or {})
ve.localize(p, 'fa')
print(json.dumps({'plain': plain, 'fa': p.get('codes') or {}, 'page': p}, default=str, ensure_ascii=False))"""

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', '--profile', 'accounting', cwd=T)
    check("a garden of the core grows taking the view and accounting profiles, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    v = get('VOCAB.md')
    rows = ('schemes:\n- scheme: till\n  classifies: "Sam\'s chart of accounts for the shop: groups, and the accounts a booking '
            'names"\n  holding: extract\n  publisher: the gardener\n  url: "file:extracts/till.tsv"\n'
            '  levels: [{level: group}, {level: account}]\n  neighbours: none\n  sources: extracts/till.tsv\n'
            'files:\n- {registry: till, file: extracts/till.tsv, key: code}\n')
    v = re.sub(r'^schemes: \[\]\n', '', v, flags=re.M)
    v = re.sub(r'^files: \[\]\n', '', v, flags=re.M)
    put('VOCAB.md', v.replace('---\n', '---\n' + rows, 1))
    put('extracts/till.tsv', 'code\tlevel\tparent\tname\tname_fa\n'
                             '1\tgroup\t\tAssets\tدارایی‌ها\n'
                             f'1010\taccount\t1\tWorkshop cash box\t{CASH}\n'
                             '4\tgroup\t\tIncome\tدرآمد\n'
                             f'4010\taccount\t4\tRepair income\t{INCOME}\n')
    put('beans/receipt-1.md', '''---
bean: receipt-1
kind: document
title: "receipt-1 — the receipt of a bicycle's repair"
summary: "what was paid for a repair, and where it is booked"
statements:
  - say:  { by: sam, at: now }
  - own:  { by: sam, of: self }
  - pay:  { id: paid, by: unknown, to: sam, of: { count: "20.00", unit: XTS } }
  - book: { id: to-cash, of: paid, to: "till:1010" }
  - book: { id: to-income, of: paid, to: "till:4010" }
---
A receipt.
''')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's books"
summary: "where what was paid is booked"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - reckon: {{ id: booked, reading: {{ what: "the receipts", steps: [ {{ id: d, op: select, kind: document }} ] }} }}
  - draw:   {{ id: ledger, by: self, of: [sam], drawing: {{ label: Books, archetype: table, selection: booked, columns: [ {{ label: Receipt, path: title }}, {{ label: Accounts, path: book.to }} ], {STORY.format(p='where it is booked')} }} }}
  - draw:   {{ id: page, by: self, of: [ledger], page: {{ fields: [ {{ kind: document, fact: title, shown_from: understand }}, {{ kind: document, fact: pay, shown_from: understand }}, {{ kind: document, fact: book, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', 'the chart of the shop, a receipt and a page', '--body',
                  '- action: wrote [[receipt-1]] and [[page]]. RULE-CHANGE: VOCAB.md holds the chart of the shop, a scheme '
                  'of the garden, and extracts/till.tsv its table')
    check("the chart, the receipt and the page are saved through the gate", rc == 0 and '0 error(s)' in out, out[-1500:])

    R = last_json(run(PY, '-c', PAGE)[1])
    fa, plain = R.get('fa') or {}, R.get('plain') or {}
    check("the page's readings carry each account by its name: in Persian the table's Persian, with no language its own",
          (fa.get('till:1010') or {}).get('name') == CASH and (fa.get('till:4010') or {}).get('name') == INCOME
          and (plain.get('till:1010') or {}).get('name') == 'Workshop cash box', (fa, plain, R.get('error')))

    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the page was not drawn in a browser: none on this machine")
    elif R.get('page'):
        P = R['page']
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_table.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="t" class="vw light" dir="rtl"></div><div id="s" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E}), A = window.daftarArchetypes;
  A.table(document.getElementById('t'), E.drawings.ledger, t, null);
  out.cells = [...document.querySelectorAll('#t td')].map(x => x.innerText);
  out.titles = [...document.querySelectorAll('#t .eg-code')].map(x => x.getAttribute('title'));
  A.sheet(document.getElementById('s'), E.sheets['receipt-1'], t, null);
  out.sheet = document.getElementById('s').innerText;
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        P['codes'] = R.get('fa') or {}
        P['settings']['garden']['lang'] = 'fa'
        path = os.path.join(T, 'codes.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(P, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        cells = ' '.join(B.get('cells') or [])
        check("in Persian, the table's cell reads the accounts' names, never their codes; each code beside its name",
              not B['errs'] and CASH in cells and INCOME in cells and 'till:1010' not in cells and 'till:4010' not in cells
              and 'till:1010' in (B.get('titles') or []), B)
        check("...the sheet's bookings likewise", CASH in (B.get('sheet') or '') and INCOME in (B.get('sheet') or '')
              and 'till:1010' not in (B.get('sheet') or ''), B)
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_code_names: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
