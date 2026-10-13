#!/usr/bin/env python3
"""The view's `books` archetype: an entity's books drawn as the accounting profile's asset reads them — per currency,
the trial balance in the chart's order (opening, debit, credit, the balance in each element's sense, the totals) and the
ledger of each account that posts — its columns along the reader's line, debit before credit, every account by its name
in the reader's language.

A garden of the core is grown here (test/grow.py) taking the view and accounting profiles: Sam keeps a chart of his
own, each account's Persian name in a `name_fa` column beside its name; the books' opening, a salary received into the
bank and a dinner paid by card are booked. A page draws Sam's books. Then:

  the chart     a chart's row may carry an account's name in a language (`name_fa`), as any scheme's may
  the page      the books' drawing carries, per currency, each account's opening, debit, credit and balance — the bank
                1500, the card a liability of 90, the salary an income of 1000 — the totals balanced, and each posting
                account's ledger with its running balance; each account by its Persian name; a reader who may not read
                Sam is drawn none of it
  a browser     in Persian, right to left: the debit's column at the right of the credit's, the accounts by their
                Persian names, an account opening its ledger

Run: python3 test/view_books.py   (0 = green; a NOTE, and no browser check, where no Chromium is on the machine)
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


def bean(bid, kind, title, *statements):
    put(f'beans/{bid}.md', f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{title}\"\nsummary: \"{title}, invented.\"\n"
                           "statements:\n" + ''.join(f"  - {s}\n" for s in statements) + f"---\n{title}.\n")


T = tempfile.mkdtemp(prefix='view-books-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')
STORY = ('purpose: "{p}", outcome: "{p}", stages: [{{label: Read, doer: the view}}, {{label: Draw, doer: the view}}, '
         '{{label: Open, doer: the reader}}], questions: [{{lens: orient, ask: "{p}"}}], blind: [{{what: "what nobody wrote down"}}]')
BANK, CARD, FOOD = 'حساب بانکی', 'کارت اعتباری', 'خوراک'
PAGE = """import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_engraved as ve
vm.init('.', 'page')
p = ve.page(lambda *a, **k: True, 'sam')
nobody = ve.page(lambda what, bid=None, *a, **k: bid not in ('sam',), 'someone')
ve.localize(p, 'fa')
print(json.dumps({'page': p, 'nobody': nobody['drawings'].get('books')}, default=str, ensure_ascii=False))"""

try:
    grow.release(REL)
    rc, out = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                  '--profile', 'view', '--profile', 'accounting', cwd=T)
    check("a garden of the core grows taking the view and accounting profiles, kept by Sam", rc == 0, out[-800:])
    run(PY, 'bin/install.py')
    v = get('VOCAB.md')
    rows = ('schemes:\n- scheme: books\n  classifies: "Sam\'s chart of accounts"\n  holding: extract\n'
            '  publisher: the gardener\n  url: "file:extracts/books.tsv"\n  levels: [{level: group}, {level: account}]\n'
            '  neighbours: none\n  sources: extracts/books.tsv\n  form: chart\n'
            'files:\n- {registry: books, file: extracts/books.tsv, key: code}\n')
    v = re.sub(r'^schemes: \[\]\n', '', v, flags=re.M)
    v = re.sub(r'^files: \[\]\n', '', v, flags=re.M)
    put('VOCAB.md', v.replace('---\n', '---\n' + rows, 1))
    put('extracts/books.tsv', 'code\tlevel\tparent\tname\tname_fa\telement\tstands_for\n'
                              '1\tgroup\t\tAssets\tدارایی‌ها\tasset\t\n'
                              f'11\taccount\t1\tThe bank account\t{BANK}\t\tbank-a\n'
                              '2\tgroup\t\tLiabilities\tبدهی‌ها\tliability\t\n'
                              f'21\taccount\t2\tThe card\t{CARD}\t\tcard-a\n'
                              '3\tgroup\t\tEquity\tسرمایه\tequity\t\n'
                              '31\taccount\t3\tOpening balances\tتراز افتتاحیه\t\t\n'
                              '4\tgroup\t\tIncome\tدرآمد\tincome\t\n'
                              '41\taccount\t4\tSalary\tحقوق\t\t\n'
                              '6\tgroup\t\tExpenses\tهزینه‌ها\texpense\t\n'
                              f'61\taccount\t6\tFood\t{FOOD}\t\t\n')
    bean('bank-a', 'contract', "Sam's account at a bank", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('card-a', 'contract', "Sam's card", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('salary', 'document', "March's salary", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: march, by: { someone: org }, to: sam, of: { count: "1000.00", unit: XTS }, through: bank-a, '
         'at: "2025-03-01" }')
    bean('dinner', 'document', 'a dinner, paid by card', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: meal, by: sam, of: { count: "90.00", unit: XTS }, through: card-a, at: "2025-03-03" }')
    bean('books-sam', 'document', "Sam's books", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'open: { id: opened, by: sam, of: self, at: "2025-02-28" }',
         'book: { id: o1, of: opened, from: "books:31", to: "books:11", share: { count: "500.00", unit: XTS } }',
         'book: { id: b1, of: "salary#march", from: "books:41" }', 'book: { id: b2, of: "dinner#meal", to: "books:61" }')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's books"
summary: "what Sam's books hold"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw:   {{ id: books, by: self, of: [sam], drawing: {{ label: Books, archetype: books, {STORY.format(p='what the books hold')} }} }}
  - draw:   {{ id: page, by: self, of: [books], page: {{ fields: [ {{ kind: document, fact: title, shown_from: understand }}, {{ kind: document, fact: pay, shown_from: understand }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', "Sam's chart, his books and their page", '--body',
                  '- action: wrote [[bank-a]], [[card-a]], [[salary]], [[dinner]], [[books-sam]] and [[page]]. '
                  'RULE-CHANGE: VOCAB.md holds the chart of Sam\'s books, a scheme of the garden naming the form chart, '
                  'and extracts/books.tsv its table, each account\'s Persian name beside it')
    check("the chart — each account's Persian name in a `name_fa` column — the books and a page drawing them are saved "
          "through the gate", rc == 0 and '0 error(s)' in out, out[-1500:])

    R = last_json(run(PY, '-c', PAGE)[1])
    P = R.get('page') or {}
    D = (P.get('drawings') or {}).get('books') or {}
    cur = (D.get('currencies') or [{}])[0]
    bal = {r['code']: r['balance'] for r in cur.get('rows') or []}
    check("the page's books: per currency, each account in its chart's order with its balance in its element's sense — "
          "the bank 1500, the card a liability of 90, opening balances 500, the salary an income of 1000, food 90",
          cur.get('unit') == 'XTS' and [r['code'] for r in cur.get('rows') or []] ==
          ['books:1', 'books:11', 'books:2', 'books:21', 'books:3', 'books:31', 'books:4', 'books:41', 'books:6', 'books:61']
          and (bal.get('books:11'), bal.get('books:21'), bal.get('books:31'), bal.get('books:41'), bal.get('books:61')) ==
          ('1500', '90', '500', '1000', '90'), (D, R.get('error')))
    L = (cur.get('ledgers') or {}).get('books:11') or {}
    check("...the totals balanced, and the bank's ledger line by line with its running balance, each line naming the "
          "bean it rests on", cur.get('balanced') and [x['balance'] for x in L.get('lines') or []] == ['500', '1500']
          and [x['bean'] for x in L.get('lines') or []] == ['books-sam', 'salary'], cur)
    check("...each account by its Persian name, from the chart's own column", ((P.get('codes') or {}).get('books:11') or {})
          .get('name') == BANK and ((P.get('codes') or {}).get('books:61') or {}).get('name') == FOOD, P.get('codes'))
    check("...and a reader who may not read Sam is drawn none of his books", R.get('nobody') is not None
          and not (R['nobody'].get('currencies')), R.get('nobody'))

    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the page was not drawn in a browser: none on this machine")
    elif P:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_books.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="b" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E}), A = window.daftarArchetypes, el = document.getElementById('b');
  A.books(el, E.drawings.books, t, null);
  const heads = [...el.querySelectorAll('.eg-books-trial thead th')];
  out.heads = heads.map(x => x.innerText.trim());
  out.x = heads.map(x => x.getBoundingClientRect().left);
  out.rows = [...el.querySelectorAll('.eg-books-trial tbody th')].map(x => x.innerText.trim());
  out.closed = [...el.querySelectorAll('details.eg-ledger')].map(d => d.open);
  el.querySelector('button[data-ledger="books:11"]').click();
  out.opened = [...el.querySelectorAll('details.eg-ledger')].filter(d => d.open).map(d => d.getAttribute('data-ledger'));
  out.text = el.innerText;
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        P['settings']['garden']['lang'] = 'fa'
        path = os.path.join(T, 'books.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(P, ensure_ascii=False)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180)
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        heads, x = B.get('heads') or [], B.get('x') or []
        check("in Persian, right to left: the columns in the books' order — account, opening, debit, credit, balance — "
              "the debit's at the right of the credit's", not B['errs'] and heads == ['حساب', 'مانده اول دوره', 'بدهکار',
                                                                                   'بستانکار', 'مانده'] and len(x) == 5
              and x[2] > x[3] and x[0] > x[4], B)
        check("...the accounts by their Persian names, never their codes", BANK in (B.get('rows') or []) and CARD in
              (B.get('rows') or []) and 'books:11' not in (B.get('text') or ''), B.get('rows'))
        check("...each ledger closed until its account is opened: the bank's opens from its line",
              B.get('closed') and not any(B['closed']) and B.get('opened') == ['books:11'], B)
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_books: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
