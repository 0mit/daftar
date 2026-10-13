#!/usr/bin/env python3
"""The books (the accounting profile, core/law/profiles.yaml): a chart of accounts held to its form, a booking as a move
of value from one account to another, the reverse of a move as its reverse sense, and a match — judged by the gate in a
garden of the core grown from a release made of this tree (test/grow.py).

  the chart     a scheme that names the profile's form `chart` (`form: chart`, registries.yaml) holds its rows to it: the
                scheme's own columns and the form's, an element and a role of the profile's tables, a kind of the law
                for its parties, a day for `closed`; each postable account (a code no code has for its parent) says
                what it is, itself or by an ancestor; one account a being, one account a role; the being one the garden
                holds; the form a profile's, and one the garden takes
  a booking     rests on a payment (made or asked), a `measure`, the books' `open` or another booking; names `from`,
                `to` or both — a postable account of one chart, open on the day it is booked on, or a being — or none,
                booking the move of what it books in the reverse sense (`sense: "-1"`) from a day it says; an analytic
                code is booked `to`; a booking of both sides of what is no payment moves an amount; under one plan the
                amounts add up to the entity's part of the payment (its share of what its bearers bear), and to one
                side of a chart to no more than it
  a match       names two payments or more, what was read of the movement and what was said agreeing per currency; a
                payment is matched once in an entity's books, wherever the match is written

Run: python3 test/books.py   (0 = green; about half a minute)
"""
import json
import os
import shutil
import sys
import tempfile
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='books-')
G = os.path.join(T, 'g')


def run(*a):
    return grow.run(*a, cwd=G)


def write(rel, text):
    p = os.path.join(G, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def text(rel):
    with open(os.path.join(G, *rel.split('/')), encoding='utf-8') as fh:
        return fh.read()


def bean(bid, kind, title, *statements):
    write(f'beans/{bid}.md', f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{title}\"\nsummary: \"{title}, invented.\"\n"
                             "statements:\n" + ''.join(f"  - {s}\n" for s in statements) + f"---\n{title}.\n")


def gate():
    r = run(PY, 'core/check.py', '.')
    return [ln for ln in r.out.splitlines() if ln and not ln.startswith('core check')]


VOCAB = """---
profiles: [accounting]
schemes:
  - { scheme: books, classifies: "Sam's chart of accounts", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/books", levels: [ { level: group }, { level: account } ], neighbours: none, sources: extracts/books.tsv, form: chart }
  - { scheme: other, classifies: "a second chart, kept for another entity", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/other", levels: [ { level: account } ], neighbours: none, sources: extracts/other.tsv, form: chart }
  - { scheme: centres, classifies: "where Sam's amounts belong", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/centres", levels: [ { level: plan }, { level: account } ], neighbours: none, sources: extracts/centres.tsv }
files:
  - { registry: books, file: extracts/books.tsv, key: code }
  - { registry: other, file: extracts/other.tsv, key: code }
  - { registry: centres, file: extracts/centres.tsv, key: code }
---
# the garden's own rows
"""
COLS = ['code', 'level', 'parent', 'name', 'element', 'stands_for', 'parties', 'role', 'closed']
ROWS = [
    ['1', 'group', '', 'assets', 'asset', '', '', '', ''],
    ['11', 'account', '1', 'the bank account', '', 'bank-a', '', '', ''],
    ['13', 'account', '1', 'people who owe Sam, or whom Sam owes', '', '', 'person', '', ''],
    ['15', 'account', '1', 'the old cash box', '', '', '', '', '2026-09-15'],
    ['19', 'account', '1', 'awaiting an account', '', '', '', 'awaiting', ''],
    ['2', 'group', '', 'liabilities', 'liability', '', '', '', ''],
    ['21', 'account', '2', 'the card', '', 'card-a', '', '', ''],
    ['3', 'group', '', 'equity', 'equity', '', '', '', ''],
    ['31', 'account', '3', 'opening balances', '', '', '', 'earnings', ''],
    ['4', 'group', '', 'income', 'income', '', '', '', ''],
    ['41', 'account', '4', 'salary', '', '', '', '', ''],
    ['6', 'group', '', 'expenses', 'expense', '', '', '', ''],
    ['61', 'account', '6', 'food', '', '', '', '', ''],
    ['62', 'account', '6', 'rent', '', '', '', '', ''],
]


def chart(rows=ROWS, cols=COLS):
    write('extracts/books.tsv', '\t'.join(cols) + '\n' + ''.join('\t'.join(r) + '\n' for r in rows))


def refused(name, says, rule='profile'):
    got = gate()
    hit = next((ln for ln in got if ln.startswith(rule) and says in ln), None)
    check(f"{name} — {hit.split(None, 1)[1][:160] if hit else 'not refused'}", hit is not None, got)


BOOKS = [
    'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
    'open: { id: opened, by: sam, of: self, at: "2026-09-01" }',
    'book: { id: o1, of: opened, from: "books:31", to: "books:11", share: { count: "500.00", unit: XTS } }',
    'book: { id: b1, of: "dinner#meal", to: "books:61" }',
    'book: { id: b2, of: "dinner#meal", to: "centres:kitchen" }',
    'book: { id: b3, of: "salary#oct", from: "books:41" }',
    'book: { id: b4, of: "salary#lunch", to: "books:61", share: { count: "15.00", unit: XTS } }',
    'book: { id: b5, of: "salary#lunch", from: card-a }',
    'book: { id: b6, of: "stmt-10#l1", to: "books:61" }',
    'match: { id: m1, of: ["stmt-10#l2", "oct-rent#paid"], at: "2026-10-06" }',
    'book: { id: r1, of: "stmt-10#l1", sense: "-1", at: "2026-10-07", why: "the baker refunded it in cash" }',
    'book: { id: o3, of: opened, from: "books:31", to: "books:13", share: { count: "5.00", unit: XTS } }',
    'book: { id: r2, of: o3, sense: "-1", at: "2026-09-02", why: "the opening named a debt nobody had" }']

try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam', '--profile', 'accounting')
    check(f"a garden of the core (core@{grow.VERSION}) grows taking the accounting profile", r.returncode == 0, r.out[-800:])
    write('VOCAB.md', VOCAB)
    chart()
    write('extracts/other.tsv', 'code\tlevel\tparent\tname\telement\n1\taccount\t\tcash\tasset\n')
    write('extracts/centres.tsv', 'code\tlevel\tparent\tname\nhome\tplan\t\thome\nkitchen\taccount\thome\tthe kitchen\n')
    bean('ali', 'person', 'Ali', 'say: { by: sam, at: now }', 'own: { by: theone, of: self }')
    bean('landlord', 'org', 'the landlord, a firm', 'say: { by: sam, at: now }', 'own: { by: theone, of: self }')
    bean('bank-a', 'contract', "Sam's account at a bank", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('card-a', 'contract', "Sam's card", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('dinner', 'contract', 'a dinner Sam and Ali share', 'say: { by: sam, at: now }', 'own: { by: theone, of: self }',
         'answer: { by: sam, of: self, as: law }', 'answer: { by: ali, of: self, as: law }',
         'agree: { by: [sam, ali], of: "a dinner shared", through: spoken }',
         'pay: { id: meal, by: sam, of: { count: "90.00", unit: XTS }, through: card-a, at: "2026-10-03" }',
         'bear: { by: sam, of: meal, share: "2" }', 'bear: { by: ali, of: meal, share: "1" }')
    bean('salary', 'document', "October's salary", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: oct, by: { someone: org }, to: sam, of: { count: "1000.00", unit: XTS }, through: bank-a, '
         'at: "2026-10-01" }',
         'pay: { id: lunch, by: sam, of: { count: "20.00", unit: XTS }, at: "2026-10-04" }')
    bean('stmt-10', 'document', "the bank's statement for October", 'read: { by: sam, at: now }',
         'own: { by: { someone: org }, of: self }',
         'pay: { id: l1, by: sam, of: { count: "12.50", unit: XTS }, through: card-a, at: "2026-10-05", note: "the baker" }',
         'pay: { id: l2, by: sam, to: landlord, of: { count: "300.00", unit: XTS }, through: bank-a, at: "2026-10-02" }')
    bean('oct-rent', 'document', 'the October rent, as Sam recorded it', 'say: { by: sam, at: now }',
         'own: { by: sam, of: self }', 'pay: { id: paid, by: sam, to: landlord, of: { count: "300.00", unit: XTS }, '
                                       'at: "2026-10-02" }')
    bean('books-sam', 'document', "Sam's own books", *BOOKS)
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: Sam keeps books', '--body',
            '- action: RULE-CHANGE — VOCAB.md takes the accounting profile, two charts and a plan; wrote [[ali]], '
            '[[landlord]], [[bank-a]], [[card-a]], [[dinner]], [[salary]], [[stmt-10]], [[oct-rent]], [[books-sam]]',
            '- ratified_by: sam')
    check("a chart of accounts (`form: chart`) and the books written in it are saved through the gate: an opening moved "
          "from equity to the bank; a payment booked on one side, the other read from it; an analytic share beside it; "
          "a means named by the being its account stands for; a bank's line matched with the payment said; a move "
          "booked in the reverse sense, of a line and of a booking", r.returncode == 0, r.out[-2500:])
    clean = gate()
    check("...and the gate finds nothing in the garden", not clean, clean)

    # ---- THE CHART: its rows held to the form
    def row(code, **cells):
        return [[*(cells.get(c, x) for c, x in zip(COLS, rw))] if rw[0] == code else rw for rw in ROWS]

    chart(cols=COLS + ['colour'], rows=[rw + ['blue' if rw[0] == '61' else ''] for rw in ROWS])
    refused("the chart: a column neither the scheme's nor the form's is refused", 'colour: no column of a chart', 'law')
    chart(row('1', element='wealth'))
    refused("...an element none of the five", "element: 'wealth' is not a row of `elements`", 'law')
    chart(row('6', element=''))
    refused("...a postable account that says what it is neither itself nor by an ancestor", 'scheme books 61', 'law')
    chart(row('21', stands_for='bank-a'))
    refused("...two accounts standing for one being", 'one account of a chart a being', 'law')
    chart(row('41', role='awaiting'))
    refused("...two accounts taking one role", 'one account a role', 'law')
    chart(row('19', role='suspense'))
    refused("...a role none of the profile's", "role: 'suspense' is not a row of `account_roles`", 'law')
    chart(row('13', parties='person critter'))
    refused("...parties of a kind the law does not have", "parties: 'critter' is no kind of the law", 'law')
    chart(row('15', closed='mid-September'))
    refused("...a `closed` that is no day", "closed: 'mid-September' is no day", 'law')
    chart(row('21', stands_for='card-b'))
    refused("...an account standing for a being the garden holds no bean of", 'stands for card-b, which is no bean')
    chart()
    keep = text('VOCAB.md')
    write('VOCAB.md', keep.replace('form: chart }\n  - { scheme: other', 'form: ledger }\n  - { scheme: other'))
    refused("...a form no profile brings", '`ledger` is no form a profile brings', 'law')
    write('VOCAB.md', keep.replace('profiles: [accounting]', 'profiles: []'))
    refused("...the form of a profile the garden does not take", "the accounting profile's, which this garden does not "
                                                                  "take", 'law')
    write('VOCAB.md', keep)

    # ---- A BOOKING: a move from one account to another
    def books(*changes, add=()):
        st = list(BOOKS)
        for old, new in changes:
            st = [new if s == old else s for s in st]
        bean('books-sam', 'document', "Sam's own books", *st, *add)

    books(add=['book: { of: "salary#oct", to: "books:1" }'])
    refused("a booking: to an account with accounts beneath it is refused — it names a postable account",
            'books:1 has accounts beneath it')
    books(add=['book: { of: "salary#lunch", to: "books:15" }'])
    refused("...to an account closed before the day it is booked on (the day of what it books)",
            'books:15 closed on 2026-09-15; this is booked on 2026-10-04')
    books(add=['book: { of: "salary#lunch", from: "centres:kitchen" }'])
    refused("...from an analytic code: a part belongs to it, booked `to` it", 'centres is no chart')
    books(add=['book: { of: "salary#lunch", from: "books:21", to: "other:1" }'])
    refused("...with its two sides in two charts", 'its two sides are of two charts, books and other')
    books(add=['book: { of: "salary#lunch" }'])
    refused("...naming no side, and no reverse sense", 'a booking names where it goes')
    books(('book: { id: r2, of: o3, sense: "-1", at: "2026-09-02", why: "the opening named a debt nobody had" }',
           'book: { id: r2, of: o3, sense: "-1", why: "the opening named a debt nobody had" }'))
    refused("...the reverse of a move with no day it is read from", 'say the day')
    books(add=['book: { of: "salary#lunch", to: "books:61", sense: "-1", at: "2026-10-08" }'])
    refused("...a reverse sense with a side named: the reverse of a move names none", 'naming no side')
    books(add=['book: { of: "salary#lunch", to: "books:61", sense: "2" }'])
    refused("...a sense none of the two", "'2' is not a row of `senses`", 'valency')
    books(('book: { id: o1, of: opened, from: "books:31", to: "books:11", share: { count: "500.00", unit: XTS } }',
           'book: { id: o1, of: opened, from: "books:31", to: "books:11" }'))
    refused("...both sides of what is no payment (the books' opening) with no amount", 'moves an amount')
    books(add=['book: { of: m1, to: "books:61" }'])
    refused("...resting on a statement that moved, asked and measured nothing", 'is none of what a booking rests on')
    books(('book: { id: b4, of: "salary#lunch", to: "books:61", share: { count: "15.00", unit: XTS } }',
           'book: { id: b4, of: "salary#lunch", to: "books:61", share: { count: "25.00", unit: XTS } }'))
    refused("...one side of a chart in amounts adding up to more than the payment (25 of 20)",
            'the bookings to books add up to 25 XTS, more than its part: the payment is 20 XTS')
    books(('book: { id: b2, of: "dinner#meal", to: "centres:kitchen" }',
           'book: { id: b2, of: "dinner#meal", to: "centres:kitchen", share: { count: "90.00", unit: XTS } }'))
    refused("...an analytic plan in amounts that are not Sam's part of a payment borne two to one (90 of 60)",
            "the bookings in the plan home add up to 90 XTS, and the payment is 90 XTS, sam's part of it 60 XTS")
    books(('book: { id: b2, of: "dinner#meal", to: "centres:kitchen" }',
           'book: { id: b2, of: "dinner#meal", to: "centres:kitchen", share: { count: "60.00", unit: XTS } }'))
    got = gate()
    check("...and Sam's part of it, 60, passes", not got, got)

    # ---- A MATCH: records of one movement
    books(('match: { id: m1, of: ["stmt-10#l2", "oct-rent#paid"], at: "2026-10-06" }',
           'match: { id: m1, of: ["stmt-10#l2"], at: "2026-10-06" }'))
    refused("a match: of one statement — a match names records of one movement, two or more", 'two statements or more')
    books(('match: { id: m1, of: ["stmt-10#l2", "oct-rent#paid"], at: "2026-10-06" }',
           'match: { id: m1, of: ["stmt-10#l2", opened], at: "2026-10-06" }'))
    refused("...naming what is no payment", 'match.of: `opened` is no payment')
    books(('match: { id: m1, of: ["stmt-10#l2", "oct-rent#paid"], at: "2026-10-06" }',
           'match: { id: m1, of: ["stmt-10#l2", "salary#lunch"], at: "2026-10-06" }'))
    refused("...what was read (300) and what was said (20) not agreeing",
            'what was read (300 XTS) and what was said (20 XTS) do not agree')
    books()
    bean('later', 'document', 'a second look at October', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'match: { of: ["stmt-10#l2", "oct-rent#paid"], at: "2026-10-09" }')
    refused("...a payment matched twice in Sam's books, in another bean: one movement counted once",
            '`stmt-10#l2` is matched already (books-sam')
    os.remove(os.path.join(G, 'beans', 'later.md'))
    got = gate()
    check("the garden is whole again", not got, got)

    # ---- APPORTION: a part along a plan is a booking `to` an analytic code; a move's other side places none there
    bean('studio', 'contract', 'the studio Sam rents', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: sept, by: sam, of: { count: "300.00", unit: XTS }, through: bank-a, at: "2026-09-30" }',
         'book: { of: sept, to: "centres:kitchen" }', 'book: { of: sept, from: "books:11", to: "books:62" }',
         'book: { of: sept, from: "books:11" }')
    write('reading.yaml', 'what: "where the studio\'s rent belongs"\nsteps:\n'
                          '  - { id: this, op: select, kind: contract, where: [ { path: bean, "=": studio } ] }\n'
                          '  - { id: paid, op: select, of: this, entries: pay }\n'
                          '  - { id: where, op: apportion, of: paid, amount: of, over: book }\n')
    r = run(PY, 'bin/reckon.py', '--ad-hoc', 'reading.yaml')
    import re
    got = dict(re.findall(r'^  ([a-z0-9:-]+): (.*)$', r.out, re.M))
    check("apportion reads the parts booked `to` a code, each plan its whole — a booking that names only where the "
          "amount came from places nothing", r.returncode == 0 and got.get('kitchen') == '300 XTS'
          and got.get('62') == '300 XTS' and set(got) == {'kitchen', '62'} and 'None' not in r.out, r.out[-900:])
    os.remove(os.path.join(G, 'beans', 'studio.md'))
    os.remove(os.path.join(G, 'reading.yaml'))
    run('git', 'checkout', '--', 'beans/books-sam.md')      # as saved: the save wrote its knowing act's moment

    # ---- THE READINGS (the profile's asset): every figure read from the moves, exact, never stored
    def reading(*a):
        r = run(PY, 'assets/accounting/bin/books.py', *a, '--chart', 'books', '--today', '2026-10-12', '--json')
        try:
            return json.loads(r.stdout)
        except ValueError:
            return {'error': r.out[-1500:]}

    F = lambda x: Fraction(str(x))
    lines_of = lambda v: sorted((ln['account'], F(ln['dr']), F(ln['cr']), ln['party']) for ln in v.get('lines', []))
    vs = reading('vouchers')
    by = {v['ref']: v for v in vs} if isinstance(vs, list) else {}
    check("the asset is the garden's while it takes the profile, and every voucher it reads balances",
          os.path.isfile(os.path.join(G, 'assets', 'accounting', 'lib', 'books_read.py')) and by
          and all(v['balanced'] for v in vs), vs)
    check("the dinner, paid by card and borne two to one: Cr the card 90, Dr food 60 (Sam's part), Dr Ali's account 30",
          lines_of(by.get('dinner#meal', {})) == [('13', 30, 0, 'ali'), ('21', 0, 90, None), ('61', 60, 0, None)],
          by.get('dinner#meal'))
    check("the salary received into the bank, booked from salary: Dr the bank 1000, Cr salary 1000",
          lines_of(by.get('salary#oct', {})) == [('11', 1000, 0, None), ('41', 0, 1000, None)], by.get('salary#oct'))
    check("lunch, its means named by the card's being, 15 of it to food: Cr the card 20, Dr food 15, the 5 no booking "
          "places awaiting an account", lines_of(by.get('salary#lunch', {})) ==
          [('19', 5, 0, None), ('21', 0, 20, None), ('61', 15, 0, None)], by.get('salary#lunch'))
    check("the bank's line matched with the rent Sam said: counted once, the line its evidence and its means (the bank)",
          'stmt-10#l2' not in by and lines_of(by.get('oct-rent#paid', {})) == [('11', 0, 300, None),
                                                                             ('19', 300, 0, None)], by.get('oct-rent#paid'))
    check("a move in the reverse sense, no word of its own: the baker's line and an opening's line, ends exchanged on the "
          "reversal's day", lines_of(by.get('books-sam#r1', {})) == [('21', F('12.50'), 0, None), ('61', 0, F('12.50'), None)]
          and lines_of(by.get('books-sam#r2', {})) == [('13', 0, 5, None), ('31', 5, 0, None)]
          and by['books-sam#r1']['day'] == '2026-10-07', [by.get('books-sam#r1'), by.get('books-sam#r2')])
    t = reading('trial', '--unit', 'XTS')
    closing = {r['code']: F(r['closing']) for r in t.get('rows', [])}
    bal = {r['code']: F(r['balance']) for r in t.get('rows', [])}
    check("the trial balance balances, each account's closing what arrived less what left: the bank 500 + 1000 - 300",
          t.get('balanced') and closing.get('11') == 1200 and closing.get('13') == 30 and closing.get('19') == 305, t)
    check("...each balance read in its element's sense: the card a liability of 110, the salary an income of 1000, "
          "equity 500, food an expense of 75, the group of assets 1535", (bal.get('21'), bal.get('41'), bal.get('31'),
                                                                            bal.get('61'), bal.get('1')) ==
          (110, 1000, 500, 75, 1535), bal)
    pl = reading('pl', '--unit', 'XTS')
    b_ = reading('balance', '--unit', 'XTS', '--at', '2026-10-31')
    check("profit and loss: income 1000 less expense 75 = 925; the balance: what the assets hold, the liabilities, "
          "equity and the result", F(pl.get('result', 0)) == 925 and F(b_.get('result', 0)) == 925
          and [r['code'] for r in b_.get('assets', [])][:1] == ['1'], (pl, b_))
    L = reading('ledger', '11', '--unit', 'XTS')
    A = reading('ledger', '13', '--unit', 'XTS', '--party', 'ali')
    check("an account's ledger, its running balance: the bank's three lines ending at 1200; Ali's account 30",
          len(L.get('rows', [])) == 3 and F(L.get('closing', 0)) == 1200 and F(A.get('closing', 0)) == 30, (L, A))
    o = reading('open')
    check("open items: each line awaiting an account — lunch's 5 and the rent's 300", isinstance(o, list)
          and sorted((x['ref'], F(x['dr'])) for x in o) == [('oct-rent#paid', 300), ('salary#lunch', 5)], o)
    r = run(PY, 'assets/accounting/bin/books.py', 'trial', '--unit', 'XTS', '--chart', 'books', '--today', '2026-10-12')
    check("...and the trial balance printed for a person reads `balanced`", r.returncode == 0 and 'balanced' in r.out
          and '1200' in r.out, r.out[-900:])
    r = run(PY, 'assets/accounting/bin/books.py', 'trial', '--chart', 'books')
    check("...a reading in no currency is refused, saying why: two currencies are never added", r.returncode == 2
          and 'never added' in r.out, r.out)
    r = run(PY, 'assets/accounting/bin/books.py', 'vouchers')
    check("...and books read in no chart, where the garden keeps two, are refused, naming them", r.returncode == 2
          and 'this garden keeps 2 (books, other)' in r.out, r.out)

    # ---- A CLOSE: the books' reading through a day, pinned at a commit — no word of its own
    bean('old-receipt', 'document', 'a receipt from September, not yet booked', 'say: { by: sam, at: now }',
         'own: { by: sam, of: self }', 'pay: { id: old, by: sam, of: { count: "10.00", unit: XTS }, through: bank-a, '
                                       'at: "2026-09-15", note: "a September receipt" }')
    bean('gift', 'contract', "Ali's gift to the landlord, Sam's books none of it", 'say: { by: sam, at: now }',
         'own: { by: theone, of: self }', 'pay: { id: given, by: ali, to: landlord, of: { count: "7.00", unit: XTS }, '
                                          'at: "2026-09-20" }')
    r = run(PY, 'bin/save.py', 'sam', 'a September receipt, a gift', '--body', '- action: wrote [[old-receipt]] and '
                                                                              '[[gift]]')
    check("a receipt of September, and a gift between two others, are saved", r.returncode == 0, r.out[-900:])
    sha = run('git', 'rev-parse', 'HEAD').stdout.strip()
    bean('closing-09', 'document', 'September closed', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'reckon: { id: books-2026-09, reading: { what: "the books through September", steps: [ { id: through, op: '
         'books, to: "2026-09-30", chart: books } ] } }', f'pin: {{ id: closed-09, of: [books-2026-09], at: [now, "garden@{sha}"] }}')
    r = run(PY, 'bin/save.py', 'sam', 'September closed', '--body', '- action: wrote [[closing-09]]')
    check("a close — the books' reading through a day, pinned at the commit before it — is saved through the gate",
          r.returncode == 0, r.out[-900:])
    r = run(PY, 'bin/reckon.py', 'closing-09#books-2026-09')
    check("the reading `books` gives each account's net charge through the day: the bank 500 opened, 10 paid out",
          r.returncode == 0 and '11 XTS: 490' in r.out, r.out[-900:])
    c = reading('closes')
    check("...and the books know the close: its day, its commit", c == [{'day': '2026-09-30', 'commit': sha,
                                                                         'pin': 'closing-09#closed-09'}], c)
    keep = text('beans/old-receipt.md')
    write('beans/old-receipt.md', keep.replace('count: "10.00"', 'count: "11.00"'))
    r = run(PY, 'bin/save.py', 'sam', 'the receipt, changed', '--body', '- action: changed [[old-receipt]] old')
    check("a payment the closed books read is not changed: rule kept refuses it, by the commit",
          r.returncode != 0 and 'read by the books of sam closed through 2026-09-30' in r.out, r.out[-900:])
    run('git', 'reset', '-q', '--hard', 'HEAD')
    os.remove(os.path.join(G, 'beans', 'old-receipt.md'))
    r = run(PY, 'bin/save.py', 'sam', 'the receipt, taken out', '--body', '- action: took out [[old-receipt]] old')
    check("...nor taken out with its bean", r.returncode != 0 and 'read by the books of sam closed' in r.out, r.out[-900:])
    run('git', 'reset', '-q', '--hard', 'HEAD')
    keep = text('beans/gift.md')
    write('beans/gift.md', keep.replace('count: "7.00"', 'count: "8.00"').replace(
        '  - own: { by: theone, of: self }\n', '  - own: { by: theone, of: self }\n  - say: { by: sam, at: now, of: [given] }\n'))
    r = run(PY, 'bin/save.py', 'sam', 'the gift, corrected', '--body', '- action: changed [[gift]] given')
    check("...and a payment Sam's books do not read (Ali's, to the landlord) is changed as before", r.returncode == 0,
          r.out[-900:])
    bean('stmt-late', 'document', 'a bank line found after September closed', 'read: { by: sam, at: now }',
         'own: { by: { someone: org }, of: self }', 'pay: { id: fee, by: sam, of: { count: "2.00", unit: XTS }, '
                                                    'through: bank-a, at: "2026-09-29", note: "a bank fee" }')
    bean('books-late', 'document', "September's receipt booked after the close", 'say: { by: sam, at: now }',
         'own: { by: sam, of: self }', 'book: { id: b9, of: "old-receipt#old", to: "books:61" }')
    r = run(PY, 'bin/save.py', 'sam', 'a late line, a late booking', '--body', '- action: wrote [[stmt-late]] and '
                                                                              '[[books-late]]')
    vs = reading('vouchers')
    by = {v['ref']: v for v in vs} if isinstance(vs, list) else {}
    after = next((v for v in vs if v['as'] == 'after-close'), {}) if isinstance(vs, list) else {}
    check("the closed books keep September as the pinned commit read it — the receipt still awaiting an account — and "
          "what came after it with a September day, a bank fee and a booking, is read on 1 October, the difference",
          r.returncode == 0 and lines_of(by.get('old-receipt#old', {})) == [('11', 0, 10, None), ('19', 10, 0, None)]
          and after.get('day') == '2026-10-01' and 'stmt-late#fee' not in by
          and lines_of(after) == [('11', 0, 2, None), ('19', 0, 8, None), ('61', 10, 0, None)], (r.out[-600:], after))
    sha = run('git', 'rev-parse', 'HEAD').stdout.strip()
    bean('closing-10', 'document', 'October closed', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'reckon: { id: books-2026-10, reading: { what: "the books through October", steps: [ { id: through, op: '
         'books, to: "2026-10-31", chart: books } ] } }', f'pin: {{ id: closed-10, of: [books-2026-10], at: [now, "garden@{sha}"] }}')
    r = run(PY, 'bin/save.py', 'sam', 'October closed', '--body', '- action: wrote [[closing-10]]')
    t10 = reading('trial', '--unit', 'XTS', '--to', '2026-10-31')
    bean('stmt-later', 'document', 'another September line, found after October closed', 'read: { by: sam, at: now }',
         'own: { by: { someone: org }, of: self }', 'pay: { id: fee, by: sam, of: { count: "1.00", unit: XTS }, '
                                                    'through: bank-a, at: "2026-09-28", note: "another bank fee" }')
    r2 = run(PY, 'bin/save.py', 'sam', 'a later line', '--body', '- action: wrote [[stmt-later]]')
    vs = reading('vouchers')
    afters = sorted((v['ref'], v['day'], tuple(lines_of(v))) for v in vs if v['as'] == 'after-close') \
        if isinstance(vs, list) else []
    t10b = reading('trial', '--unit', 'XTS', '--to', '2026-10-31')
    check("two periods closed: each reads as its own pin — September's late fee and booking stay on 1 October, inside "
          "October's close — and a September line found after October closed is read on 1 November, the first open "
          "day; the books through October read the same before it and after",
          r.returncode == 0 and r2.returncode == 0 and afters == [
              ('closing-09#closed-09@after', '2026-10-01', (('11', 0, 2, None), ('19', 0, 8, None), ('61', 10, 0, None))),
              ('closing-10#closed-10@after', '2026-11-01', (('11', 0, 1, None), ('19', 1, 0, None)))]
          and t10.get('rows') and t10.get('rows') == t10b.get('rows'), (r.out[-300:], r2.out[-300:], afters))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nbooks: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
