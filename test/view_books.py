#!/usr/bin/env python3
"""A table over a chart's codes (the drawing's `chart`, the operator's choice of 2026-10-13): an entity's books drawn as
the accounting profile's asset reads them — per currency, an account a line in the chart's order, each column a figure
of it (opening, debit, credit, the balance in its element's sense), the totals, and the ledger of each account that
posts — its columns along the reader's line, debit before credit, every account by its name in the reader's language.

A garden of the core is grown here (test/grow.py) taking the view and accounting profiles: Sam keeps a chart of his
own, each account's Persian name in a `name_fa` column beside its name; the books' opening, a salary received into the
bank and a dinner paid by card are booked. A page draws Sam's books as a table over the chart's codes. Then:

  the chart     a chart's row may carry an account's name in a language (`name_fa`), as any scheme's may; an account
                holds persons (`parties: person`)
  the page      the table carries, per currency, each account's figures in the columns it names — the bank's balance
                1500, the card a liability of 90, the salary an income of 1000 — the totals balanced, and each posting
                account's ledger with its running balance; each account by its Persian name; a reader who may not read
                Sam is drawn none of it; a column that is no figure of an account, and a table of a reading and a chart
                at once, are refused by the page's check
  a person      the account that holds persons has a line for each person beneath it — Ali, who owes Sam 30 of the
                dinner — and one for its lines that name nobody (a coffee's 7), each opening its own ledger; its ledger
                names each line's person and why the line is there; Ali's sheet shows his account, read by the page's
                reading of him (`fields` … `reading`, the books' step with `party`): who owes whom, and its lines; where
                the books and the agreements read a person's account otherwise, the table says so
  a browser     in Persian, right to left: the debit's column at the right of the credit's, the accounts by their
                Persian names, an account opening its ledger; Ali's line beneath the persons' account, the line naming
                nobody marked; Ali's sheet says in Persian that he owes Sam 30, his lines naming the dinner and his share

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
BANK, CARD, FOOD, PERSONS = 'حساب بانکی', 'کارت اعتباری', 'خوراک', 'حساب جاری اشخاص'
PAGE = """import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']
import view_model as vm, view_engraved as ve
vm.init('.', 'page')
p = ve.page(lambda *a, **k: True, 'sam')
nobody = ve.page(lambda what, bid=None, *a, **k: bid not in ('sam',), 'someone')
v = dict(vm.views_raw())['books']
ok = ve.problems('books', v)[0]
odd = ve.problems('books', dict(v, columns=[{'label': 'x', 'path': 'colour'}]))[0]
both = ve.problems('books', dict(v, selection='booked'))[0]
ve.localize(p, 'fa')
print(json.dumps({'page': p, 'nobody': nobody['drawings'].get('books'), 'ok': ok, 'odd': odd, 'both': both},
                 default=str, ensure_ascii=False))"""

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
    put('extracts/books.tsv', 'code\tlevel\tparent\tname\tname_fa\telement\tstands_for\tparties\n'
                              '1\tgroup\t\tAssets\tدارایی‌ها\tasset\t\t\n'
                              f'11\taccount\t1\tThe bank account\t{BANK}\t\tbank-a\t\n'
                              f'13\taccount\t1\tPeople Sam deals with\t{PERSONS}\t\t\tperson\n'
                              '2\tgroup\t\tLiabilities\tبدهی‌ها\tliability\t\t\n'
                              f'21\taccount\t2\tThe card\t{CARD}\t\tcard-a\t\n'
                              '3\tgroup\t\tEquity\tسرمایه\tequity\t\t\n'
                              '31\taccount\t3\tOpening balances\tتراز افتتاحیه\t\t\t\n'
                              '4\tgroup\t\tIncome\tدرآمد\tincome\t\t\n'
                              '41\taccount\t4\tSalary\tحقوق\t\t\t\n'
                              '6\tgroup\t\tExpenses\tهزینه‌ها\texpense\t\t\n'
                              f'61\taccount\t6\tFood\t{FOOD}\t\t\t\n')
    bean('ali', 'person', 'Ali', 'say: { by: sam, at: now }', 'own: { by: theone, of: self }')
    bean('bank-a', 'contract', "Sam's account at a bank", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('card-a', 'contract', "Sam's card", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('salary', 'document', "March's salary", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: march, by: { someone: org }, to: sam, of: { count: "1000.00", unit: XTS }, through: bank-a, '
         'at: "2025-03-01" }')
    bean('dinner', 'contract', 'a dinner Sam and Ali share, paid by card', 'say: { by: sam, at: now }',
         'own: { by: theone, of: self }', 'answer: { by: sam, of: self, as: law }', 'answer: { by: ali, of: self, as: law }',
         'agree: { by: [sam, ali], of: "a dinner shared", through: spoken }',
         'pay: { id: meal, by: sam, of: { count: "90.00", unit: XTS }, through: card-a, at: "2025-03-03" }',
         'bear: { by: sam, of: meal, share: "2" }', 'bear: { by: ali, of: meal, share: "1" }',
         'pay: { id: coffee, by: sam, of: { count: "7.00", unit: XTS }, through: card-a, at: "2025-03-04" }')
    bean('books-sam', 'document', "Sam's books", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'open: { id: opened, by: sam, of: self, at: "2025-02-28" }',
         'book: { id: o1, of: opened, from: "books:31", to: "books:11", share: { count: "500.00", unit: XTS } }',
         'book: { id: b1, of: "salary#march", from: "books:41" }', 'book: { id: b2, of: "dinner#meal", to: "books:61" }',
         'book: { id: b3, of: "dinner#coffee", to: "books:13" }')
    put('beans/page.md', f'''---
bean: page
kind: service
title: "Sam's books"
summary: "what Sam's books hold"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - be:     {{ by: self, at: "uri:https://garden.example.org/", as: location }}
  - draw:   {{ id: books, by: self, of: [sam], drawing: {{ label: Books, archetype: table, chart: books, columns: [ {{ label: "حساب", path: name }}, {{ label: "مانده اول دوره", path: opening }}, {{ label: "بدهکار", path: debit }}, {{ label: "بستانکار", path: credit }}, {{ label: "مانده", path: balance }} ], {STORY.format(p='what the books hold')} }} }}
  - reckon: {{ id: account-of, reading: {{ what: "a person's account in Sam's books", inputs: [ {{ name: who, origin: {{ act: say }} }}, {{ name: today, origin: {{ act: read, by: reader }} }} ], steps: [ {{ id: acct, op: books, to: today, party: who }} ] }} }}
  - draw:   {{ id: page, by: self, of: [books], page: {{ fields: [ {{ kind: document, fact: title, shown_from: understand }}, {{ kind: document, fact: pay, shown_from: understand }}, {{ kind: contract, fact: title, shown_from: understand }}, {{ kind: contract, fact: pay, shown_from: understand }}, {{ kind: person, fact: title, shown_from: understand }}, {{ kind: person, fact: account, reading: account-of, shown_from: understand, label: "حساب جاری" }} ] }} }}
---
A page.
''')
    rc, out = run(PY, 'bin/save.py', 'sam', "Sam's chart, his books and their page", '--body',
                  '- action: wrote [[ali]], [[bank-a]], [[card-a]], [[salary]], [[dinner]], [[books-sam]] and [[page]]. '
                  'RULE-CHANGE: VOCAB.md holds the chart of Sam\'s books, a scheme of the garden naming the form chart, '
                  'and extracts/books.tsv its table, each account\'s Persian name beside it')
    check("the chart — each account's Persian name in a `name_fa` column — the books and a page drawing them are saved "
          "through the gate", rc == 0 and '0 error(s)' in out, out[-1500:])

    R = last_json(run(PY, '-c', PAGE)[1])
    P = R.get('page') or {}
    D = (P.get('drawings') or {}).get('books') or {}
    cur = (D.get('currencies') or [{}])[0]
    bal = {r['code']: r['cells'][4] for r in cur.get('lines') or []}
    check("the page's table of the chart: per currency, an account a line in the chart's order, its balance in its "
          "element's sense — the bank 1500, the card a liability of 97, opening balances 500, the salary an income of "
          "1000, food 60 (Sam's part of the dinner)", D.get('chart') == 'books' and cur.get('unit') == 'XTS'
          and [r['code'] for r in cur.get('lines') or []] ==
          ['books:1', 'books:11', 'books:13', 'books:13|ali', 'books:13|', 'books:2', 'books:21', 'books:3', 'books:31',
           'books:4', 'books:41', 'books:6', 'books:61']
          and (bal.get('books:11'), bal.get('books:21'), bal.get('books:31'), bal.get('books:41'), bal.get('books:61')) ==
          ('1500', '97', '500', '1000', '60'), (D, R.get('error')))
    per = {r['code']: r for r in cur.get('lines') or []}
    check("...the account that holds persons a line for each beneath it — Ali, who owes Sam his 30 of the dinner — and "
          "one for its lines naming nobody, the coffee's 7, each said as what it is and never as an id",
          bal.get('books:13') == '37' and bal.get('books:13|ali') == '30' and bal.get('books:13|') == '7'
          and (per.get('books:13|ali') or {}).get('party') == {'bean': 'ali', 'title': 'Ali'}
          and (per.get('books:13|ali') or {}).get('owes') == 'party'
          and (per.get('books:13|') or {}).get('party') == {'bean': None, 'title': None, 'nobody': True}
          and (per.get('books:13') or {}).get('holds'), [per.get(k) for k in ('books:13', 'books:13|ali', 'books:13|')])
    L13 = (cur.get('ledgers') or {}).get('books:13') or {}
    La = (cur.get('ledgers') or {}).get('books:13|ali') or {}
    check("...its ledger names each line's person and why it is there — Ali's share of the dinner — and Ali's own ledger "
          "holds his line alone", L13.get('holds') and [(x.get('party') or {}).get('bean') for x in L13.get('lines') or []]
          == ['ali', None] and (L13['lines'][0].get('why') or {}).get('as') == 'share'
          and [x['bean'] for x in La.get('lines') or []] == ['dinner'] and La.get('closing') == '30', (L13, La))
    check("...and where the books and the agreements read Ali's account alike (30 each), nothing is said of it",
          'disagree' not in cur, cur.get('disagree'))
    bean('lent', 'document', 'five Sam lent Ali, in his books only', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'book: { id: l1, of: "books-sam#opened", from: "books:31", to: ali, share: { count: "5.00", unit: XTS } }')
    R2 = last_json(run(PY, '-c', PAGE)[1])
    os.remove(os.path.join(G, 'beans', 'lent.md'))
    cur2 = ((((R2.get('page') or {}).get('drawings') or {}).get('books') or {}).get('currencies') or [{}])[0]
    check("...but a line of the books naming Ali that no agreement holds — five lent him, booked from the opening — is "
          "said under the table: the books read 35, the agreements 30", cur2.get('disagree') == [
              {'party': {'bean': 'ali', 'title': 'Ali'}, 'books': '35', 'agreements': '30'}], cur2.get('disagree'))
    meal = next((x for r in ((P.get('sheets') or {}).get('dinner') or {}).get('rows') or [] if r['verb'] == 'pay'
                 for x in r['statements'] if x.get('id') == 'meal'), {})
    sh = meal.get('shares') or {}
    check("a payment's shares in one line of its sheet: each bearer's part as the fraction it is and an amount — Sam 2/3 "
          "(60), Ali 1/3 (30) — its own shares, and what Ali then owes Sam",
          sh.get('source') == 'payment' and sh.get('unit') == 'XTS'
          and sorted((b.get('bean'), b.get('share'), b.get('amount')) for b in sh.get('bearers') or []) ==
          [('ali', '1/3', '30'), ('sam', '2/3', '60')]
          and [((o['from'] or {}).get('bean'), (o['to'] or {}).get('bean'), o['amount']) for o in sh.get('owes') or []] ==
          [('ali', 'sam', '30')], meal)
    A = ((P.get('sheets') or {}).get('ali') or {}).get('readings') or [{}]
    acc = (A[0].get('accounts') or [{}])[0]
    check("Ali's sheet shows his account, read by the page's reading of him: the persons' account, 30 he owes Sam, its "
          "one line the dinner, his share", A[0].get('books') and A[0].get('label') == 'حساب جاری'
          and acc.get('code') == 'books:13' and acc.get('balance') == '30' and acc.get('owes') == 'party'
          and [(x['bean'], (x.get('why') or {}).get('as')) for x in acc.get('lines') or []] == [('dinner', 'share')]
          and (A[0].get('entity') or {}).get('you'), A)
    L = (cur.get('ledgers') or {}).get('books:11') or {}
    check("...the totals balanced, and the bank's ledger line by line with its running balance, each line naming the "
          "bean it rests on", cur.get('balanced') and [x['balance'] for x in L.get('lines') or []] == ['500', '1500']
          and [x['bean'] for x in L.get('lines') or []] == ['books-sam', 'salary'], cur.get('ledgers', {}).get('books:11'))
    check("...each account by its Persian name, from the chart's own column", ((P.get('codes') or {}).get('books:11') or {})
          .get('name') == BANK and ((P.get('codes') or {}).get('books:61') or {}).get('name') == FOOD, P.get('codes'))
    check("...and a reader who may not read Sam is drawn none of his books", R.get('nobody') is not None
          and not (R['nobody'].get('currencies')), R.get('nobody'))
    check("the page's check passes the table, and refuses a column that is no figure of an account and a table of a "
          "reading and a chart at once", R.get('ok') == [] and any('a figure of an account' in e for e in R.get('odd') or [])
          and any('one of them' in e for e in R.get('both') or []), (R.get('ok'), R.get('odd'), R.get('both')))

    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome', 'google-chrome-stable') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the page was not drawn in a browser: none on this machine")
    elif P:
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'view', 'lib'))
        import view_widgets
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_table.js', 'view_sheet.js'))
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="b" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E}), A = window.daftarArchetypes, el = document.getElementById('b');
  A.table(el, E.drawings.books, t, null);
  const heads = [...el.querySelectorAll('.eg-chart-table thead th')];
  out.heads = heads.map(x => x.innerText.trim());
  out.x = heads.map(x => x.getBoundingClientRect().left);
  out.rows = [...el.querySelectorAll('.eg-chart-table tbody th')].map(x => x.innerText.trim());
  out.closed = [...el.querySelectorAll('details.eg-ledger')].map(d => d.open);
  el.querySelector('button[data-ledger="books:11"]').click();
  out.opened = [...el.querySelectorAll('details.eg-ledger')].filter(d => d.open).map(d => d.getAttribute('data-ledger'));
  out.text = el.innerText;
  out.ali = (el.querySelector('tr[data-code="books:13|ali"] th') || {}).innerText;
  out.nobody = (el.querySelector('tr[data-code="books:13|"]') || {}).className;
  out.who = [...el.querySelectorAll('details[data-ledger="books:13"] td.eg-who')].map(x => x.textContent.trim());
  out.why = [...el.querySelectorAll('details[data-ledger="books:13"] .eg-why')].map(x => x.textContent.trim());
  const s = document.createElement('div'); document.body.appendChild(s);
  A.sheet(s, E.sheets.ali, t, null);
  out.says = (s.querySelector('.eg-account-says') || {}).innerText;
  const d = document.createElement('div'); document.body.appendChild(d);
  A.sheet(d, E.sheets.dinner, t, null);
  out.shares = (d.querySelector('.eg-shares') || {}).textContent;
  out.bearDeps = d.querySelectorAll('.eg-dependent').length;
  out.lines = [...s.querySelectorAll('.eg-account td.eg-what')].map(x => x.textContent.trim());
  const per = el.querySelector('.eg-chart-period');
  out.period = per ? {text: per.innerText, days: [...per.querySelectorAll('time.w-moment')].map(x => x.getAttribute('datetime'))} : null;
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
        check("in Persian, right to left: the columns as the page lists them — account, opening, debit, credit, balance — "
              "the debit's at the right of the credit's", not B['errs'] and heads == ['حساب', 'مانده اول دوره', 'بدهکار',
                                                                                   'بستانکار', 'مانده'] and len(x) == 5
              and x[2] > x[3] and x[0] > x[4], B)
        check("...the accounts by their Persian names, never their codes", BANK in (B.get('rows') or []) and CARD in
              (B.get('rows') or []) and 'books:11' not in (B.get('text') or ''), B.get('rows'))
        check("...each ledger closed until its account is opened: the bank's opens from its line",
              B.get('closed') and not any(B['closed']) and B.get('opened') == ['books:11'], B)
        check("...Ali's line beneath the persons' account by his name, the line naming nobody marked to be booked to a "
              "person, and the persons' ledger naming each line's person and why it is there, in Persian",
              B.get('ali') == 'Ali' and 'eg-warn' in (B.get('nobody') or '') and B.get('who') == ['Ali', 'بدون شخص']
              and B.get('why') == ['سهم Ali'], {k: B.get(k) for k in ('ali', 'nobody', 'who', 'why', 'errs')})
        check("...and Ali's sheet says in Persian that he owes Sam 30, the amount drawn in its currency, his one line the "
              "dinner and his share", re.fullmatch(r'Ali .*۳۰.* به شما بدهکار است', (B.get('says') or '').replace('\n', ' '))
              is not None and len(B.get('lines') or []) == 1 and 'سهم Ali' in B['lines'][0], (B.get('says'), B.get('lines')))
        check("...and the dinner's shares drawn as one line, in Persian, the fractions as fractions, with who owes whom: "
              "no line of its own for each share", re.search(r'[۰-۹]/[۰-۹]|[۰-۹]⁄[۰-۹]', B.get('shares') or '')
              and 'Ali' in (B.get('shares') or '') and 'بدهکار است' in (B.get('shares') or '')
              and B.get('bearDeps') == 0, (B.get('shares'), B.get('bearDeps')))
        Pd = B.get('period') or {}
        check("...the day it is read to drawn as a day, in the reader's calendar and digits — never the ISO day as text, "
              "which a right-to-left line reverses (14-10-2026)", bool(Pd.get('days')) and re.search(r'[۰-۹]', Pd.get('text') or '')
              and not re.search(r'[0-9]', Pd.get('text') or ''), Pd)
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_books: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
