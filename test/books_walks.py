#!/usr/bin/env python3
"""The books' operations as walks (the accounting profile's asset, assets/accounting/bin/books.py): each started with
what a person gives it (bin/act.py `--start … --input`), its plan a write shown to them, ratified, written as shown and
read back by the books — in a garden of the core grown from a release made of this tree (test/grow.py).

  setup    the walks and their tool written into the garden as its own, refused until the garden has the kind
           `procedure` and a host bean naming this machine; in a garden whose path reads as a Windows path, the tool's
           place written as the law reads it, and found there
  book     a payment booked to an account and a plan's code; booked again to another while its period is open, the
           earlier booking replaced; after the period closed, what it placed moved by a booking of it on today, the
           closed period unchanged; a means the payment does not say; refused when nothing would change; several
           payments to one account in one plan, refused whole where one of them is booked there already
  reverse  a payment reversed from a day, with its reason; refused in a closed period
  entry    the books' opening and an entry of three lines, refused unbalanced; one in a garden's own money unit, and
           the gate's refusals of a unit it does not hold and of more decimal places than a currency has
  close    the books' reading through a day, pinned at the commit the plan read; refused for a day still to come and
           one closed already
  import   a bank's camt.053 file read into a statement bean of payments read through the bank account, opening + lines
           = closing; a file with a pending line refused whole, a file imported once; a file a page gave, by its SHA-256
           where the host keeps it; a bank's CSV by a mapping
  match    a line of it and the payment said, one movement; refused where their amounts differ
  chart    an account added beneath its parent, among its siblings, and one the books used renamed and named in
           Persian — a row of the garden's own table, committed with no RULE-CHANGE; refused where a used account would
           move, where a level or a parent does not fit, where the gate would refuse the row, where an input is no
           column; a walk's write never changes the law, a bean, the journal or a capture
  remove   a document taken out whole with what of the books named it (a booking, a reversal, an entry resting on the
           booking) and what the books kept beside it in `details`, a payment taken out of its bean (the last key of
           `details` with it, and `details`), a bank's statement taken out and its file importable again; refused
           where closed books read it (the gate's own words), where another statement names it, for another garden's
           word, for a sealed statement, for a line read from a source, for the run's own bean, the books' bean, a
           being's bean, with no reason, and where a `details` naming it is written otherwise than a tool writes it

Its runs save one bean several times within seconds, each save at its own second, so none waits for the minute to
turn.
Run: python3 test/books_walks.py   (0 = green; some minutes: its walks are many)
"""
import difflib
import json
import os
import re
import shutil
import socket
import sys
import tempfile
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable
HOST = socket.gethostname()


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='books-walks-')
G = os.path.join(T, 'g')


def run(*a):
    return grow.run(*a, cwd=G)


def write(rel, text):
    p = os.path.join(G, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def bean(bid, kind, title, *statements):
    write(f'beans/{bid}.md', f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{title}\"\nsummary: \"{title}, invented.\"\n"
                             "statements:\n" + ''.join(f"  - {s}\n" for s in statements) + f"---\n{title}.\n")


def save(what, *body):
    return run(PY, 'bin/save.py', 'sam', what, '--body', *body)


def books(*a):
    r = run(PY, 'assets/accounting/bin/books.py', *a, '--json')
    try:
        return json.loads(r.stdout)
    except ValueError:
        return {'error': r.out[-1200:]}


def voucher(ref):
    vs = books('vouchers')
    return next((v for v in vs if v['ref'] == ref), {}) if isinstance(vs, list) else {}


F = lambda x: Fraction(str(x))
lines_of = lambda v: sorted((ln['account'], F(ln['dr']), F(ln['cr'])) for ln in v.get('lines', []))


def start(on, op, **inputs):
    r = run(PY, 'bin/act.py', on, '--start', f'walk-books-{op}', '--by', 'sam',      # a list: the input given each time
            *[x for k, v in inputs.items() for w in (v if isinstance(v, list) else [v]) for x in ('--input', f'{k}={w}')])
    course = next((w.strip('.,():') for w in r.out.split() if w.startswith('run-')), None)
    return r, course


def plan_of(on, course, step='plan'):
    """What the run's step said, every capture of it (its plan, or its refusal)."""
    d = os.path.join(G, 'captures', 'actions')
    return ''.join(open(os.path.join(d, c), encoding='utf-8').read() for c in sorted(os.listdir(d))
                   if c.startswith(f'{on}.{course}.{step}')) if os.path.isdir(d) else ''


def ratify(on, course):
    return run(PY, 'bin/act.py', on, course or '(no run started)', '--ratify', 'sam')


def planned(op, on='box', **inputs):
    """What the operation would plan from `inputs` — its write, as data — or `REFUSED: <why>`: asked of the books' walks
    (lib/books_walks.py) as their tool asks them, for a run sitting on `on`; nothing started, nothing saved."""
    code = ("import datetime, json, os, sys\n"
            "sys.path[:0] = [os.path.join('assets', 'accounting', 'lib'), os.getcwd(), 'bin']\n"
            "import books_read as br, books_walks as bw, walktool as W\n"
            "try:\n"
            "    w = bw.PLANS[sys.argv[1]](br.read(os.getcwd()), json.loads(sys.argv[3]), "
            "datetime.date.today().toordinal(), (sys.argv[2], None))\n"
            "    print(json.dumps(w, ensure_ascii=False))\n"
            "except W.Refused as e:\n"
            "    print('REFUSED: ' + str(e))\n")
    return run(PY, '-c', code, op, on, json.dumps(inputs)).out


def entry_of(what):
    """The journal's last entry that says `what`: its heading and its lines."""
    j = open(os.path.join(G, 'log', 'journal.md'), encoding='utf-8').read()
    return next(('## ' + e for e in reversed(j.split('\n## ')) if what in e), '')


CAMT = """<?xml version="1.0" encoding="UTF-8"?>
<Document xmlns="urn:iso:std:iso:20022:tech:xsd:camt.053.001.08">
 <BkToCstmrStmt><GrpHdr><MsgId>S-1</MsgId><CreDtTm>2025-05-01T06:00:00</CreDtTm></GrpHdr>
  <Stmt><Id>S-1-1</Id><Acct><Id><IBAN>XX00TEST0000000000000001</IBAN></Id><Ccy>XTS</Ccy></Acct>
   <Bal><Tp><CdOrPrtry><Cd>OPBD</Cd></CdOrPrtry></Tp><Amt Ccy="XTS">500.00</Amt><CdtDbtInd>CRDT</CdtDbtInd><Dt><Dt>2025-04-30</Dt></Dt></Bal>
   <Bal><Tp><CdOrPrtry><Cd>CLBD</Cd></CdOrPrtry></Tp><Amt Ccy="XTS">587.50</Amt><CdtDbtInd>CRDT</CdtDbtInd><Dt><Dt>2025-05-31</Dt></Dt></Bal>
   <Ntry><NtryRef>1</NtryRef><Amt Ccy="XTS">100.00</Amt><CdtDbtInd>CRDT</CdtDbtInd><Sts><Cd>BOOK</Cd></Sts>
    <BookgDt><Dt>2025-05-02</Dt></BookgDt><AcctSvcrRef>REF-0001</AcctSvcrRef>
    <NtryDtls><TxDtls><RltdPties><Dbtr><Pty><Nm>A Client</Nm></Pty></Dbtr></RltdPties><RmtInf><Ustrd>a fee</Ustrd></RmtInf></TxDtls></NtryDtls></Ntry>
   <Ntry><NtryRef>2</NtryRef><Amt Ccy="XTS">12.50</Amt><CdtDbtInd>DBIT</CdtDbtInd><Sts><Cd>BOOK</Cd></Sts>
    <BookgDt><Dt>2025-05-05</Dt></BookgDt><AcctSvcrRef>REF-0002</AcctSvcrRef><AddtlNtryInf>the baker</AddtlNtryInf></Ntry>
%s  </Stmt>
 </BkToCstmrStmt>
</Document>
"""
PENDING = """   <Ntry><NtryRef>3</NtryRef><Amt Ccy="XTS">40.00</Amt><CdtDbtInd>DBIT</CdtDbtInd><Sts><Cd>PDNG</Cd></Sts>
    <BookgDt><Dt>2025-05-31</Dt></BookgDt><AcctSvcrRef>REF-0003</AcctSvcrRef></Ntry>
"""
ROWS = [['code', 'level', 'parent', 'name', 'element', 'stands_for', 'parties', 'role', 'closed'],
        ['1', 'group', '', 'assets', 'asset', '', '', '', ''],
        ['11', 'account', '1', 'the bank account', '', 'bank-a', '', '', ''],
        ['13', 'account', '1', 'people Sam deals with', '', '', 'person', '', ''],
        ['19', 'account', '1', 'awaiting an account', '', '', '', 'awaiting', ''],
        ['2', 'group', '', 'liabilities', 'liability', '', '', '', ''],
        ['21', 'account', '2', 'the card', '', 'card-a', '', '', ''],
        ['3', 'group', '', 'equity', 'equity', '', '', '', ''],
        ['31', 'account', '3', 'opening balances', '', '', '', 'earnings', ''],
        ['4', 'group', '', 'income', 'income', '', '', '', ''],
        ['41', 'account', '4', 'fees', '', '', '', '', ''],
        ['6', 'group', '', 'expenses', 'expense', '', '', '', ''],
        ['61', 'account', '6', 'food', '', '', '', '', ''],
        ['62', 'account', '6', 'household', '', '', '', '', '']]

try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam', '--profile', 'accounting')
    check(f"a garden of the core (core@{grow.VERSION}) grows taking the accounting profile", r.returncode == 0, r.out[-800:])
    write('VOCAB.md', """---
profiles: [accounting]
schemes:
  - { scheme: books, classifies: "Sam's chart of accounts", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/books", levels: [ { level: group }, { level: account } ], neighbours: none, sources: extracts/books.tsv, form: chart }
  - { scheme: centres, classifies: "where Sam's amounts belong", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/centres", levels: [ { level: plan }, { level: account } ], neighbours: none, sources: extracts/centres.tsv }
files:
  - { registry: books, file: extracts/books.tsv, key: code }
  - { registry: centres, file: extracts/centres.tsv, key: code }
---
# the garden's own rows
""")
    write('extracts/books.tsv', ''.join('\t'.join(r) + '\n' for r in ROWS))
    write('extracts/centres.tsv', 'code\tlevel\tparent\tname\nhome\tplan\t\thome\nkitchen\taccount\thome\tthe kitchen\n')
    bean('bank-a', 'contract', "Sam's account at a bank", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('card-a', 'contract', "Sam's card", 'say: { by: sam, at: now }', 'own: { by: sam, of: self }')
    bean('market', 'document', 'a receipt from the market', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: veg, by: sam, of: { count: "15.00", unit: XTS }, through: card-a, at: "2025-03-03", '
         'note: "vegetables" }')
    bean('shop', 'document', 'a receipt from a shop', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: lamp, by: sam, of: { count: "40.00", unit: XTS }, at: "2025-03-05", note: "a lamp" }')
    bean('cafe', 'document', 'a receipt from the baker', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: bread, by: sam, of: { count: "12.50", unit: XTS }, at: "2025-05-05" }',
         'pay: { id: cake, by: sam, of: { count: "13.00", unit: XTS }, at: "2025-05-05" }')
    r = save('RULE-CHANGE: Sam keeps books', '- action: RULE-CHANGE — VOCAB.md takes the accounting profile, a chart '
                                             'and a plan; wrote [[bank-a]], [[card-a]], [[market]], [[shop]], [[cafe]]',
             '- ratified_by: sam')
    check("the chart, the plan and three receipts not yet booked are saved", r.returncode == 0, r.out[-900:])

    # ---- SETUP: the walks and their tool, the garden's own
    r = run(PY, 'assets/accounting/bin/books.py', 'setup', '--by', 'sam')
    check("setup is refused until the garden has the kind `procedure` and a host bean naming this machine, saying so",
          r.returncode == 2 and 'kind: procedure' in r.out and HOST in r.out, r.out[-800:])
    v = open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read()
    write('VOCAB.md', v.replace('profiles: [accounting]\n', 'profiles: [accounting]\nkinds:\n  - { kind: procedure, '
                                'nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\nnamespaces:\n'
                                '  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for '
                                'itself" }\n', 1))
    bean('box', 'host', 'the machine the books are kept on', 'read: { by: sam, at: now }', 'own: { by: sam, of: self }',
         f'name: {{ by: anchor-hostname, of: self, as: {HOST} }}')
    r = save('RULE-CHANGE: a walk is a procedure; this machine', '- action: RULE-CHANGE — VOCAB.md adds the kind '
             'procedure and the namespace anchor-hostname; wrote [[box]]', '- ratified_by: sam')
    r = run(PY, 'assets/accounting/bin/books.py', 'setup', '--by', 'sam')
    wrote = sorted(f for f in os.listdir(os.path.join(G, 'mappings')) if f.startswith('walk-books-'))
    check("...then it writes the nine walks and the tool, and saves nothing", r.returncode == 0 and wrote ==
          [f'walk-books-{o}.md' for o in ('book', 'chart', 'close', 'entry', 'import', 'match', 'remove', 'reverse', 'share')]
          and os.path.isfile(os.path.join(G, 'beans', 'books-tool.md')) and 'not saved' in r.out, (r.out[-600:], wrote))
    r = save("the books' walks", '- action: wrote [[books-tool]], ' + ', '.join(f'[[{w[:-3]}]]' for w in wrote))
    check("...and they pass the gate as the garden's own", r.returncode == 0, r.out[-900:])
    W_ = os.path.join(T, 'C:\\v6-rehearsal\\20261014-042310\\garden')     # on Linux, one directory of that name
    shutil.copytree(G, W_, symlinks=True)
    for f in ['beans/books-tool.md'] + [f'mappings/{w}' for w in wrote]:
        os.remove(os.path.join(W_, *f.split('/')))
    r = grow.run(PY, 'assets/accounting/bin/books.py', 'setup', '--by', 'sam', cwd=W_)
    g = grow.run(PY, 'core/check.py', '.', cwd=W_)
    tool = open(os.path.join(W_, 'beans', 'books-tool.md'), encoding='utf-8').read()
    try:
        at = next(st['be']['at'] for st in json.loads(grow.run(PY, '-c', "import json, sys; sys.path.insert(0, 'bin'); "
                  "import parse; print(json.dumps(parse.loads(open('beans/books-tool.md', encoding='utf-8').read()"
                  ".split('---')[1])['statements']))", cwd=W_).stdout) if 'be' in st)
    except (ValueError, KeyError, StopIteration):
        at = None
    found = grow.run(PY, '-c', "import sys; sys.path[:0] = ['bin', '.']; import routines; from core import engine; "
                     "print(routines.tool_path(engine.Garden.read('.'), 'books-tool'))", cwd=W_).stdout.strip()
    here = os.path.join(W_, 'assets', 'accounting', 'bin', 'books.py')
    check("setup in a garden whose path reads as a Windows path (`C:\\v6-…\\2026…`): the tool's place is written in the "
          "law's form and quoted as the parser reads it back — the gate passes, the place reads back exactly, and the "
          "engine finds the tool there", r.returncode == 0 and g.returncode == 0 and at == f"{HOST.lower()}:{here}"
          and found == here, (r.out[-400:], g.out[-600:], at, found, tool[:400]))
    shutil.rmtree(W_, ignore_errors=True)

    # ---- BOOK
    r, c = start('market', 'book', of='market#veg', account='61', analytic='kitchen')
    p = plan_of('market', c)
    check("book: started with the account and the plan's code, the plan is a write shown — and nothing written yet",
          'stopped at ratify' in r.out and 'to: "books:61"' in p and 'to: "centres:kitchen"' in p
          and lines_of(voucher('market#veg')) == [('19', 15, 0), ('21', 0, 15)], r.out[-900:] + p[-600:])
    r = ratify('market', c)
    check("...ratified, it is booked as shown and read back: Cr the card 15, Dr food 15",
          'stopped at done' in r.out and lines_of(voucher('market#veg')) == [('21', 0, 15), ('61', 15, 0)], r.out[-900:])
    r, c = start('market', 'book', of='market#veg', account='food')
    check("...booked again to the same account (named by its name), the plan is refused: nothing would change",
          'stopped at refused' in r.out and 'booked to books:61 already' in r.out + plan_of('market', c), r.out[-900:])
    r, c = start('market', 'book', of='market#veg', account='13')
    check("...booked to the account that holds persons, naming nobody, the plan is refused, saying how a person is named",
          'stopped at refused' in r.out and 'books:13 holds persons: name the person' in r.out + plan_of('market', c, ''),
          r.out[-900:])
    r, c = start('shop', 'book', of='shop#lamp', account='62', means='21')
    r2 = ratify('shop', c)
    check("...a payment that says no means, booked with the means it was paid through: Cr the card 40, Dr household 40",
          'stopped at done' in r2.out and lines_of(voucher('shop#lamp')) == [('21', 0, 40), ('62', 40, 0)],
          r.out[-500:] + r2.out[-500:])
    r, c = start('market', 'book', of='market#veg', account='62')
    r2 = ratify('market', c)
    check("...booked again while its period is open: the earlier booking is replaced — Dr household 15",
          'stopped at done' in r2.out and lines_of(voucher('market#veg')) == [('21', 0, 15), ('62', 15, 0)],
          r.out[-500:] + r2.out[-500:] + plan_of('market', c, ''))

    # ---- A BOOKING KNOWN BY AN ACT WITH AN ID, BOOKED AGAIN: the act goes with what it knew, and the entry names it
    bean('rug', 'document', 'a receipt for a rug', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: bought, by: sam, of: { count: "60.00", unit: XTS }, through: card-a, at: "2025-03-06" }')
    b = open(os.path.join(G, 'beans', 'books-sam.md'), encoding='utf-8').read()
    write('beans/books-sam.md', b.replace('---\n', '---\n', 1).replace('\nstatements:\n', '\nstatements:\n'
          '  - book: { id: rug-a1, of: "rug#bought", to: "books:61" }\n'
          '  - book: { id: rug-c1, of: "rug#bought", to: "centres:kitchen" }\n'
          '  - say: { id: dashboard-1, by: sam, of: [rug-a1, rug-c1], at: now }\n', 1))
    r = save('a rug, booked from a page', '- action: wrote [[rug]] and [[books-sam]] rug-a1, rug-c1')
    r, c = start('rug', 'book', of='rug#bought', account='62')
    r2 = ratify('rug', c)
    kept = open(os.path.join(G, 'beans', 'books-sam.md'), encoding='utf-8').read()
    check("a booking known by an act with an id (a page's `say: { id: … }`), booked again while open: the act goes with "
          "what it knew, the entry names it by its id, the plan's other booking is written again as it was — Dr "
          "household 60", 'stopped at done' in r2.out and lines_of(voucher('rug#bought')) == [('21', 0, 60), ('62', 60, 0)]
          and 'dashboard-1' not in kept and 'id: rug-c1' in kept,
          r.out[-400:] + r2.out[-600:] + plan_of('rug', c, 'apply'))

    # ---- ENTRY: what no payment says, written whole
    r, c = start('bank-a', 'entry', day='2025-03-01', memo='opening balances', unit='XTS', lines='11 dr 500; 31 cr 400')
    check("entry: lines that do not balance are refused, saying so", 'stopped at refused' in r.out and 'do not balance'
          in r.out + plan_of('bank-a', c, ''), r.out[-600:])
    r, c = start('bank-a', 'entry', day='2025-03-01', memo='lent', unit='XTS', lines='13 dr 5; 11 cr 5')
    check("entry: a line in the account that holds persons naming nobody is refused, saying to name the person in its "
          "place", 'stopped at refused' in r.out and 'books:13 holds persons' in r.out + plan_of('bank-a', c, '')
          and '<person> dr|cr <amount>' in r.out + plan_of('bank-a', c, ''), r.out[-600:])
    r, c = start('bank-a', 'entry', day='2025-03-01', memo='opening balances', unit='XTS',
                 lines='11 dr 500; opening balances cr 500')
    p = plan_of('bank-a', c)
    r2 = ratify('bank-a', c)
    op = [v for v in books('vouchers') if v.get('as') == 'entry' and v.get('memo') == 'opening balances']
    check("...the books' opening, an account named by its name: the first entry writes the books' `open` and rests on "
          "it — Dr the bank 500, Cr opening balances 500", 'open: { id: opened' in p and 'stopped at done' in r2.out
          and len(op) == 1 and lines_of(op[0]) == [('11', 500, 0), ('31', 0, 500)], p[-600:] + r2.out[-500:] + str(op))
    r, c = start('card-a', 'entry', day='2025-03-10', memo='a gift of cash, spent', unit='XTS',
                 lines='62 dr 30; 61 dr 20; 31 cr 50')
    r2 = ratify('card-a', c)
    gift = [v for v in books('vouchers') if v.get('memo') == 'a gift of cash, spent']
    check("...a second entry on another day, three lines, is a voucher of its own beside the opening: each debit met "
          "by the credit, 30 and 20 from opening balances", 'stopped at done'
          in r2.out and len(gift) == 1 and lines_of(gift[0]) == [('31', 0, 20), ('31', 0, 30), ('61', 20, 0), ('62', 30, 0)],
          r.out[-400:] + r2.out[-400:] + str(gift))
    v = open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read()      # a money unit of the garden's own law
    write('VOCAB.md', v.replace('\nfiles:\n', '\nunits:\n  - { unit: XTOK, name: "a token Sam counts as money", quantity: '
                                'money, ucum: "false", why: "invented: a money unit of the garden\'s own" }\nfiles:\n', 1))
    bean('tokens', 'document', 'tokens Sam was given', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: given, by: { someone: person }, to: sam, of: { count: "1.23456789", unit: XTOK }, at: "2025-03-11" }')
    r = save('RULE-CHANGE: a token Sam counts as money', '- action: RULE-CHANGE — VOCAB.md adds the unit XTOK; wrote '
             '[[tokens]]', '- ratified_by: sam')
    check("...a money unit of the garden's own, added with what uses it", r.returncode == 0, r.out[-600:])
    r, c = start('card-a', 'entry', day='2025-03-11', memo='a token given', unit='XTOK', lines='62 dr 1.23456789; 31 cr '
                 '1.23456789')
    r2 = ratify('card-a', c)
    tok = [v for v in books('vouchers') if v.get('memo') == 'a token given']
    check("...an entry in a money unit of the garden's own law (four letters), read as the gate reads an amount",
          'stopped at done' in r2.out and len(tok) == 1 and tok[0]['unit'] == 'XTOK'
          and lines_of(tok[0]) == [('31', 0, F('1.23456789')), ('62', F('1.23456789'), 0)], r.out[-400:] + r2.out[-400:])
    r, c = start('shop', 'entry', day='2025-03-11', memo='a fee', unit='xtk', lines='62 dr 1; 31 cr 1')
    r2, c2 = start('market', 'entry', day='2025-03-11', memo='a fee', unit='USD', lines='62 dr 0.015; 31 cr 0.015')
    check("...refused, in the gate's words: a unit the law does not hold, and a count with more places than its currency "
          "has", 'stopped at refused' in r.out and "unit: 'xtk'" in r.out + plan_of('shop', c)
          and 'stopped at refused' in r2.out and 'more decimal places than USD has' in r2.out + plan_of('market', c2),
          r.out[-500:] + r2.out[-500:])

    # ---- REVERSE
    r, c = start('shop', 'reverse', of='shop#lamp', reason='taken back to the shop')
    r2 = ratify('shop', c)
    rv = [v for v in books('vouchers') if v.get('as') == 'reversal']
    check("reverse: a payment reversed from today with its reason, its move's ends exchanged: Dr the card 40, Cr "
          "household 40", 'stopped at done' in r2.out and len(rv) == 1 and lines_of(rv[0]) == [('21', 40, 0), ('62', 0, 40)],
          r.out[-500:] + r2.out[-500:] + str(rv))

    # ---- SHARE: who bears a payment's cost, each in whole parts (the operator, 2026-10-14: a card line put on another
    # as their debt, or shared among some in their proportions)
    write('beans/p-0a1b2c3d.md', '---\nbean: p-0a1b2c3d\nkind: person\ntitle: "p-0a1b2c3d"\nstatements:\n'
                                 '  - say: { by: sam, at: now }\n---\nA friend who shares costs, kept by an opaque id.\n')
    bean('club', 'org', 'a club that shares costs', 'say: { by: sam, at: now }')
    save('who shares costs', '- action: wrote [[p-0a1b2c3d]], [[club]]')
    no = [planned('share', on='shop', of='shop#lamp', who=['sam', 'p-0a1b2c3d'], share=['1']),
          planned('share', on='shop', of='shop#lamp', who=['p-0a1b2c3d'], share=['0']),
          planned('share', on='shop', of='shop#lamp', who=['p-0a1b2c3d'], share=['a half']),
          planned('share', on='shop', of='shop#lamp', who=['grocer-x'], share=['1']),
          planned('share', on='shop', of='shop#lamp', who=['sam', 'sam'], share=['1', '1'])]
    check("share: refused — a share for each who bears it, a number of parts more than nothing, a person or an "
          "organisation of the garden, each once",
          all(x.startswith('REFUSED') for x in no) and 'a share beside each' in no[0] and 'more than nothing' in no[1]
          and 'not a number of parts' in no[2] and 'no person or organisation' in no[3] and 'each one once' in no[4], no)
    r, c = start('shop', 'share', of='shop#lamp', who=['sam', 'p-0a1b2c3d'], share=['2', '1'])
    r2 = ratify('shop', c)
    shop = open(os.path.join(G, 'beans', 'shop.md'), encoding='utf-8').read()
    bears = re.findall(r'bear: \{ id: ([a-z0-9-]+), by: ([a-z0-9-]+), of: lamp, share: "(\d+)" \}', shop)
    check("share: the lamp's cost borne by sam in two parts and the friend in one — `bear` statements beside the payment, "
          "each with its id; nothing stored of what is owed",
          'stopped at done' in r2.out and sorted((b, s) for _i, b, s in bears) == [('p-0a1b2c3d', '1'), ('sam', '2')],
          r.out[-400:] + r2.out[-400:] + shop[-600:])
    r, c = start('shop', 'share', of='shop#lamp', who=['club'], share=['1'])
    r2 = ratify('shop', c)
    shop = open(os.path.join(G, 'beans', 'shop.md'), encoding='utf-8').read()
    bears = re.findall(r'bear: \{ id: ([a-z0-9-]+), by: ([a-z0-9-]+), of: lamp, share: "(\d+)" \}', shop)
    check("...shared again, put on another whole: the club bears it all, in place of the two before",
          'stopped at done' in r2.out and [(b, s) for _i, b, s in bears] == [('club', '1')], r2.out[-400:] + shop[-600:])
    r, c = start('shop', 'share', of='shop#lamp', who=['sam', 'p-0a1b2c3d'], share=['27.50', '12.50'])
    p = plan_of('shop', c)
    r2 = ratify('shop', c)
    shop = open(os.path.join(G, 'beans', 'shop.md'), encoding='utf-8').read()
    bears = re.findall(r'bear: \{ id: ([a-z0-9-]+), by: ([a-z0-9-]+), of: lamp, share: "([0-9.]+)" \}', shop)
    check("...and by amounts: shares that add up to the lamp's 40 are each one's amount — Sam 27.50 (11/16), the friend "
          "12.50 (5/16), each said in the plan before it is ratified",
          'stopped at done' in r2.out and sorted((b, s) for _i, b, s in bears) == [('p-0a1b2c3d', '12.50'), ('sam', '27.50')]
          and '11/16, 27.5 XTS' in p and '5/16, 12.5 XTS' in p, p[-600:] + r2.out[-400:] + shop[-600:])
    bean('household', 'contract', 'Sam and the friend share the house', 'say: { by: sam, at: now }',
         'own: { by: sam, of: self }',
         'pay: { id: rent, by: sam, of: { count: "900.00", unit: XTS }, at: "2025-03-01", note: "the rent" }')
    save('the house', '- action: wrote [[household]]')
    r, c = start('household', 'share', of='household', who=['sam', 'p-0a1b2c3d'], share=['1', '1'])
    r2 = ratify('household', c)
    house = open(os.path.join(G, 'beans', 'household.md'), encoding='utf-8').read()
    once = re.findall(r'bear: \{ id: ([a-z0-9-]+), by: ([a-z0-9-]+), of: self, share: "(\d+)" \}', house)
    rent = next((v for v in books('vouchers') if v.get('ref') == 'household#rent'), {})
    no = planned('share', on='shop', of='shop', who=['sam'], share=['1'])
    check("an agreement's shares, written once (`of` the agreement): each of its payments that names none of its own is "
          "borne by them — the rent half the friend's, read in the books as the friend's share; and a bean that is no "
          "agreement is refused",
          'stopped at done' in r2.out and sorted((b, s) for _i, b, s in once) == [('p-0a1b2c3d', '1'), ('sam', '1')]
          and any(ln.get('party') == 'p-0a1b2c3d' and ln.get('dr') == '450' for ln in rent.get('lines', []))
          and no.startswith('REFUSED') and 'of an agreement' in no, (r2.out[-400:], house[-500:], rent, no))

    # ---- A PAYMENT PUT ON A PERSON'S ACCOUNT (the operator, 2026-10-14: a card line assigned straight to another): the
    # account that holds persons and the person, its detail — the person bears it alone; the entity's own booking of it out
    bean('gift', 'document', 'a gift bought for the friend, on the card', 'say: { by: sam, at: now }',
         'own: { by: sam, of: self }',
         'pay: { id: scarf, by: sam, of: { count: "36.00", unit: XTS }, through: card-a, at: "2025-03-07", note: "a scarf" }')
    save('the gift', '- action: wrote [[gift]]')
    r, c = start('gift', 'book', of='gift#scarf', account='61')
    ratify('gift', c)
    no = [planned('book', on='gift', of='gift#scarf', account='13'),
          planned('book', on='gift', of='gift#scarf', account='61', party='p-0a1b2c3d'),
          planned('book', on='gift', of='gift#scarf', account='13', party='grocer-x')]
    check("book to a person: the persons' account naming nobody is refused, saying to name the person; a person beside "
          "an account that holds no persons, and a party that is no person of the garden, refused",
          all(x.startswith('REFUSED') for x in no) and '`party`' in no[0] and 'is held in books:13' in no[1]
          and 'no person or organisation' in no[2], no)
    r, c = start('gift', 'book', of='gift#scarf', account='13', party='p-0a1b2c3d')
    p = plan_of('gift', c)
    r2 = ratify('gift', c)
    gift = open(os.path.join(G, 'beans', 'gift.md'), encoding='utf-8').read()
    v = next((x for x in books('vouchers') if x.get('ref') == 'gift#scarf'), {})
    check("...the persons' account and the friend: the scarf borne by the friend alone, as the share walk writes it — "
          "Dr the persons' account 36 in the friend's name, Cr the card 36 — Sam's own booking of it to food taken out",
          'stopped at done' in r2.out and re.search(r'bear: \{ id: [a-z0-9-]+, by: p-0a1b2c3d, of: scarf, share: "1" \}', gift)
          and lines_of(v) == [('13', 36, 0), ('21', 0, 36)]
          and any(ln.get('party') == 'p-0a1b2c3d' for ln in v.get('lines', []))
          and not [ln for f in os.listdir(os.path.join(G, 'beans')) if f.endswith('.md')
                   for ln in open(os.path.join(G, 'beans', f), encoding='utf-8').read().splitlines()
                   if 'gift#scarf' in ln and 'books:61' in ln],
          p[-700:] + r2.out[-400:] + str(v))

    # ---- SEVERAL PAYMENTS, ONE ACCOUNT, ONE PLAN: the lines a person ticks on a statement's page
    bean('grocer', 'document', 'two receipts from the grocer', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: apples, by: sam, of: { count: "4.00", unit: XTS }, through: card-a, at: "2025-04-02" }',
         'pay: { id: pears, by: sam, of: { count: "6.50", unit: XTS }, through: card-a, at: "2025-04-03" }')
    save('the grocer', '- action: wrote [[grocer]]')
    r, c = start('grocer', 'book', of=['grocer#apples', 'grocer#pears'], account='61')
    p = plan_of('grocer', c)
    r2 = ratify('grocer', c)
    check("book several: two payments booked to one account in one plan, ratified once, written in one save — Dr food "
          "4 and 6.50", 'stopped at done' in r2.out and p.count('to: "books:61"') == 2
          and '2 payments booked to books:61' in open(os.path.join(G, 'log', 'journal.md'), encoding='utf-8').read()
          and lines_of(voucher('grocer#apples')) == [('21', 0, 4), ('61', 4, 0)]
          and lines_of(voucher('grocer#pears')) == [('21', 0, F('6.50')), ('61', F('6.50'), 0)],
          p[-700:] + r2.out[-500:])
    r, c = start('grocer', 'book', of=['grocer#apples', 'market#veg'], account='62')
    check("...refused whole, naming the one already booked there: nothing written", 'stopped at refused' in r.out
          and 'market#veg is booked to books:62 already' in r.out + plan_of('grocer', c, '')
          and lines_of(voucher('grocer#apples')) == [('21', 0, 4), ('61', 4, 0)], r.out[-600:])

    # ---- CLOSE
    r, c = start('box', 'close', day='2999-12-31')
    check("close: a day still to come is refused", 'stopped at refused' in r.out and 'still to come' in
          r.out + plan_of('box', c), r.out[-600:])
    r, c = start('box', 'close', day='2025-03-31')
    p = plan_of('box', c)
    r2 = ratify('box', c)
    cl = books('closes')
    check("...the books through 31 March: the plan shows each account through the day; ratified, their reading is "
          "pinned at the commit the plan read", 'as they are closed' in p and 'op: books' in p and 'garden@' in p
          and 'stopped at done' in r2.out and isinstance(cl, list) and [x['day'] for x in cl] == ['2025-03-31'],
          p[-900:] + r2.out[-600:] + str(cl))
    r, c = start('cafe', 'close', day='2025-03-15')
    check("...a day closed already is refused", 'stopped at refused' in r.out and 'closed through 2025-03-31 already'
          in r.out + plan_of('cafe', c), r.out[-600:])

    # ---- BOOK IN A CLOSED PERIOD: nothing closed is rewritten
    r, c = start('market', 'book', of='market#veg', account='61')
    p = plan_of('market', c)
    r2 = ratify('market', c)
    moved = [v for v in books('vouchers') if v.get('as') == 'entry' and v['ref'].startswith('books-sam#bk-')]
    check("book again after its period closed: the booking stays, and a booking of it moves what it placed from "
          "household to food on today — the closed period reads as it was", 'moved to books:61' in p
          and 'stopped at done' in r2.out and lines_of(voucher('market#veg')) == [('21', 0, 15), ('62', 15, 0)]
          and len(moved) == 1 and lines_of(moved[0]) == [('61', 15, 0), ('62', 0, 15)], p[-700:] + r2.out[-500:])
    r, c = start('shop', 'reverse', of='market#veg', day='2025-03-20', reason='a mistake')
    check("reverse: a day in a closed period is refused", 'stopped at refused' in r.out and 'closed through' in
          r.out + plan_of('shop', c), r.out[-600:])

    # ---- IMPORT
    write('statement-pending.xml', CAMT % PENDING)
    r, c = start('bank-a', 'import', file=os.path.join(G, 'statement-pending.xml'), format='camt.053', means='bank-a')
    check("import: a camt.053 file with a pending line is refused whole, the line named", 'stopped at refused' in r.out
          and 'not booked' in r.out + plan_of('bank-a', c), r.out[-700:])
    write('statement-05.xml', CAMT % '')
    r, c = start('bank-a', 'import', file=os.path.join(G, 'statement-05.xml'), format='camt.053', means='bank-a',
                 statement='bank-a-2025-05')
    r2 = ratify('bank-a', c)
    sv = [v for v in books('vouchers') if v['ref'].startswith('bank-a-2025-05#')]
    check("...a camt.053 file read into a statement bean, its lines payments read through the bank account: Dr the bank "
          "100, Cr the bank 12.50, each awaiting an account", 'stopped at done' in r2.out and sorted(
              tuple(lines_of(v)) for v in sv) == sorted([(('11', 100, 0), ('19', 0, 100)), (('11', 0, F('12.50')),
                                                                                             ('19', F('12.50'), 0))]),
          r.out[-500:] + r2.out[-700:] + str(sv))
    r, c = start('cafe', 'import', file=os.path.join(G, 'statement-05.xml'), format='camt.053', means='bank-a')
    check("...the same file again is refused: imported already", 'stopped at refused' in r.out and 'imported already' in
          r.out + plan_of('cafe', c), r.out[-600:])
    import hashlib                       # a file a page gave: kept by the host off git, under its SHA-256 (#202)
    kept = (CAMT % '').replace('S-1', 'S-2')
    sha = hashlib.sha256(kept.encode('utf-8')).hexdigest()
    gd = run('git', 'rev-parse', '--absolute-git-dir').out.strip()
    os.makedirs(os.path.join(gd, 'daftar-inputs'), exist_ok=True)
    with open(os.path.join(gd, 'daftar-inputs', sha), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(kept)
    r, c = start('card-a', 'import', file='0' * 64, format='camt.053', means='bank-a')
    check("...a file a page gave is read by its SHA-256 where the host keeps it, and refused where it keeps none",
          'stopped at refused' in r.out and 'is kept on this host' in r.out + plan_of('card-a', c), r.out[-600:])
    r, c = start('card-a', 'import', file=sha, format='camt.053', means='bank-a', statement='bank-a-2025-05-again')
    p = plan_of('card-a', c)
    r2 = ratify('card-a', c)
    b = os.path.join(G, 'beans', 'bank-a-2025-05-again.md')
    b = open(b, encoding='utf-8').read() if os.path.isfile(b) else ''
    check("...the file kept for a run, read into a statement bean as a path's would be: named by its SHA-256, and no "
          "file the garden commits holding it", 'stopped at done' in r2.out and f'through: "file:{sha}"' in b
          and f'"file": "{sha}"' in b and run('git', 'grep', '-l', 'S-2-1', 'HEAD').out.strip() == ''
          and len([v for v in books('vouchers') if v['ref'].startswith('bank-a-2025-05-again#')]) == 2,
          p[-600:] + r2.out[-500:])
    write('extracts/bank-csv.yaml', 'delimiter: ";"\ndecimal: ","\ncurrency: XTS\nday_format: dd.mm.yyyy\n'
                                     'columns: { day: Datum, text: Text, debit: Soll, credit: Haben, ref: Ref }\n')
    write('statement-06.csv', 'Datum;Text;Soll;Haben;Ref\n02.06.2025;a fee;;1.000,00;C-1\n03.06.2025;rent;300,00;;C-2\n')
    save('a mapping of the bank\'s CSV', '- action: wrote extracts/bank-csv.yaml')
    write('statement-07.csv', 'Date,Text,Amount\n02-07-2025,a fee,100.00\n')
    got = run(PY, '-c', "import json, sys; sys.path[:0] = ['assets/accounting/lib']; import statements as st\n"
              "cols = {'day': 'Date', 'text': 'Text', 'amount': 'Amount'}\n"
              "for m in ({'day_format': 'dd-mm-yyyy'}, {'day_format': 'mm-dd-yyyy'}, {'sign': 'negative'}):\n"
              "    try:\n        S = st.read('statement-07.csv', 'csv', dict(m, columns=cols, currency='XTS'))\n"
              "        print('read', [ln['day'] for ln in S['lines']], len(S['refused']))\n"
              "    except st.Unreadable as e:\n        print('refused', e)\n").out
    check("...a CSV's days written dd-mm-yyyy are read; a day format or a sign the adapter does not read is refused by "
          "name, never passed over", got.splitlines()[:1] == ["read ['2025-07-02'] 0"]
          and "refused day_format: 'mm-dd-yyyy' is none the adapter reads" in got
          and "refused sign: 'negative' is none the adapter reads" in got, got[-600:])
    r, c = start('card-a', 'import', file=os.path.join(G, 'statement-06.csv'), format='csv', mapping='extracts/bank-csv.yaml',
                 means='bank-a')
    r2 = ratify('card-a', c)
    st = [v for v in books('vouchers') if v['ref'].startswith('statement-')]
    check("...a bank's CSV read by a mapping of the garden's: a decimal comma, a debit and a credit column, a day "
          "written dd.mm.yyyy", 'stopped at done' in r2.out and sorted(F(ln['dr']) for v in st for ln in v['lines']
                                                                  if ln['account'] == '11') == [0, 1000],
          r.out[-500:] + r2.out[-600:] + str(st))

    # ---- CHART: an account of the chart, added or changed — a row of the garden's own table, by a walk
    tsv = lambda: open(os.path.join(G, 'extracts', 'books.tsv'), encoding='utf-8', newline='').read()
    row = lambda *cells: '\t'.join(cells) + '\n'
    was = tsv()
    r, c = start('box', 'chart', code='60', name='rent', parent='6')
    p = plan_of('box', c)
    r2 = ratify('box', c)
    t, e = tsv(), entry_of('books:60 added')
    check("chart: a new account beneath its parent, at the level after the parent's — the plan shows its row; ratified, "
          "it is written among its siblings in the order of their codes, the table's other rows as they were, committed "
          "with an entry that names the file and is no RULE-CHANGE", '+ extracts/books.tsv: 60\taccount\t6\trent' in p
          and 'stopped at done' in r2.out and t.replace(row('60', 'account', '6', 'rent', '', '', '', '', ''), '') == was
          and t.index('\n6\tgroup') < t.index('\n60\t') < t.index('\n61\t')
          and run('git', 'status', '--porcelain', '--', 'extracts').out.strip() == ''
          and '- changed: extracts/books.tsv, as the plan showed it' in e and 'RULE-CHANGE' not in e,
          p[-700:] + r2.out[-500:] + e[-600:])
    got = planned('book', 'cafe', of='cafe#cake', account='rent')
    check("...and the books' tools read it at once: a payment may be booked to it by its name",
          'to: \\"books:60\\"' in got, got[-500:])
    r, c = start('box', 'chart', code='62', name='the household', **{'name-fa': 'خانه'})
    r2 = ratify('box', c)
    t2 = tsv()
    changed = [d for d in difflib.ndiff(t.splitlines(), t2.splitlines()) if d[:2] in ('- ', '+ ')]
    check("...an account the books used, renamed and named in Persian: the header gains the column and the row its "
          "names, nothing else of the table changes, and the gate takes it", 'stopped at done' in r2.out
          and t2.split('\n', 1)[0] == '\t'.join(ROWS[0] + ['name_fa'])
          and row('62', 'account', '6', 'the household', '', '', '', '', '', 'خانه') in t2 and len(changed) == 4,
          r.out[-400:] + r2.out[-500:] + str(changed))
    r, c = start('bank-a', 'chart', code='61', parent='4')
    check("...an account the books used is not moved: its parent stays (close it, and add another)",
          'stopped at refused' in r.out and 'is used by the books' in r.out + plan_of('bank-a', c, ''), r.out[-500:])
    for why, inputs, said in (
            ("an account above one the books used keeps its element", dict(code='6', element='asset'),
             'is used by the books, beneath it'),
            ("an account at the chart's last level has nothing beneath it", dict(code='64', name='bus', parent='61'),
             "books's last level: nothing is beneath it"),
            ("an account with no parent stands at the chart's first level", dict(code='5', name='other', level='account'),
             "is not group, the level of an account with no parent"),
            ("a role another account takes, in the gate's own words", dict(code='63', name='fares', parent='6',
                                                                           role='awaiting'),
             'takes the role awaiting, which 19 takes'),
            ("an account closed before the last line the books read in it", dict(code='61', closed='2025-01-01'),
             'it closes on or after its last line'),
            ("an input that is no column of a chart", dict(code='63', nmae='fares'), 'nmae: no column of a chart'),
            ("a being stood for twice, in the gate's own words", {'code': '63', 'name': 'fares', 'parent': '6',
                                                                 'stands-for': 'card-a'},
             'stands for card-a, as 21 does'),
            ("a new account says its name", dict(code='63', parent='6'), 'is a new account, and says its name'),
            ("a change that changes nothing", dict(code='62', name='the household'), 'holds that already')):
        got = planned('chart', **inputs)
        check(f"...refused at its plan: {why}", got.startswith('REFUSED') and said in got, got[-500:])
    got = planned('chart', code=['63'], name=['fares'], parent='6')
    check("...an input given as a list of one, as a page's `many` gives it, is that one value",
          not got.startswith('REFUSED') and '63\\taccount\\t6\\tfares' in got, got[-500:])
    got = run(PY, '-c', "import sys; sys.path.insert(0, 'bin'); import walktool as W\n"
              "for p in ('VOCAB.md', 'beans/box.md', 'mappings/walk-books-book.md', 'log/journal.md', 'captures/x', "
              "'../x.tsv', 'extracts/books.tsv'):\n"
              "    try:\n        W.garden_file(p); print(p, 'written')\n"
              "    except W.Refused:\n        print(p, 'refused')\n").out
    check("...and a walk's write changes a file of the estate the garden keeps, never the law (VOCAB.md, a RULE-CHANGE), "
          "a bean, the journal, a capture or what lies outside the garden", got.split() == [
              'VOCAB.md', 'refused', 'beans/box.md', 'refused', 'mappings/walk-books-book.md', 'refused', 'log/journal.md',
              'refused', 'captures/x', 'refused', '../x.tsv', 'refused', 'extracts/books.tsv', 'written'], got[-600:])

    # ---- MATCH
    r, c = start('cafe', 'match', line='bank-a-2025-05#line-002', payment='cafe#cake')
    check("match: a line and a payment whose amounts differ are refused", 'stopped at refused' in r.out and
          'one movement has one amount' in r.out + plan_of('cafe', c), r.out[-600:])
    r, c = start('cafe', 'match', line='bank-a-2025-05#line-002', payment='cafe#bread')
    r2 = ratify('cafe', c)
    vs = books('vouchers')
    check("...the baker's line and the bread Sam said, one movement: the line is its evidence, and the bread is read "
          "through the bank", 'stopped at done' in r2.out and not any(v['ref'] == 'bank-a-2025-05#line-002' for v in vs)
          and lines_of(next((v for v in vs if v['ref'] == 'cafe#bread'), {})) == [('11', 0, F('12.50')),
                                                                                  ('19', F('12.50'), 0)],
          r.out[-500:] + r2.out[-600:])
    # ---- REMOVE: a document, or a payment recorded by mistake, taken out with what of the books names it
    bean('twice', 'document', 'a receipt entered twice', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: oops, by: sam, of: { count: "25.00", unit: XTS }, through: card-a, at: "2025-04-10" }')
    bean('heard', 'document', 'a receipt a friend confirmed', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: lent, by: sam, of: { count: "5.00", unit: XTS }, at: "2025-04-11" }',
         'respond: { by: sam, of: [lent], as: confirms }')
    save('two receipts', '- action: wrote [[twice]] and [[heard]]')
    r, c = start('twice', 'book', of='twice#oops', account='61')
    ratify('twice', c)
    r, c = start('heard', 'entry', day='2025-04-10', memo='a fee on the receipt', unit='XTS', lines='61 dr 2; 21 cr 2',
                 of='books-sam#bk-twice-oops')
    ratify('heard', c)
    r, c = start('box', 'reverse', of='twice#oops', reason='entered twice')
    ratify('box', c)
    sam = open(os.path.join(G, 'beans', 'books-sam.md'), encoding='utf-8').read()
    fee = next((ln.split('id: ', 1)[1].split(',', 1)[0] for ln in sam.splitlines() if 'a fee on the receipt' in ln), '?')
    import yaml                              # what a garden keeps beside its payments, written as a translation writes it
    D = type('D', (yaml.SafeDumper,), {})
    D.add_representer(str, lambda d, v: d.represent_scalar('tag:yaml.org,2002:str', v, style='|' if '\n' in v else None))
    kept = lambda x: yaml.dump({'details': x}, Dumper=D, allow_unicode=True, sort_keys=False, width=100000)
    write('beans/books-sam.md', sam.replace('\nstatements:\n', '\n' + kept({'transactions': {
        'twice#oops': {'category': 'a mistake', 'note': 'entered twice,\nby hand'},
        'cafe#cake': {'category': 'sweets'}}}) + 'statements:\n', 1))
    save('a category kept beside two payments', '- action: wrote [[books-sam]] details')
    r, c = start('box', 'remove', of='twice', reason='entered twice')
    p = plan_of('box', c)
    r2 = ratify('box', c)
    sam, e = open(os.path.join(G, 'beans', 'books-sam.md'), encoding='utf-8').read(), entry_of('twice taken out whole')
    vs = books('vouchers')
    check("remove: a document taken out whole, with what of Sam's books named it — its booking, the payment's reversal, "
          "and in turn the entry resting on the booking — shown in the plan, named in the entry; the books read none of "
          "it more", all(x in p for x in ('- the bean twice, taken out whole', '- books-sam: book#bk-twice-oops',
                                          '- books-sam: book#rv-twice-oops', f'- books-sam: book#{fee}'))
          and 'stopped at done' in r2.out and not os.path.exists(os.path.join(G, 'beans', 'twice.md'))
          and not any(x in sam for x in ('twice#oops', 'bk-twice-oops', 'rv-twice-oops', f'id: {fee},'))
          and not any('twice' in v['ref'] or v.get('memo') == 'a fee on the receipt' for v in vs)
          and all(x in e for x in ('[[twice]]', 'bk-twice-oops', 'rv-twice-oops', fee)),
          p[-900:] + r2.out[-500:] + e[-700:])
    check("...and what Sam's books kept beside its payment (`details`, keyed `twice#oops`) goes with it, shown in the "
          "plan and named in the entry; the rest of `details` stays byte for byte as it was written",
          '- books-sam: details › transactions › twice#oops' in p and 'details.transactions.twice#oops' in e
          and kept({'transactions': {'cafe#cake': {'category': 'sweets'}}}) in sam, p[-700:] + sam[:700])
    r, c = start('bank-a', 'remove', of='market', reason='a mistake')
    check("...a document the closed books read is refused in the gate's own words: reverse it instead",
          'stopped at refused' in r.out and 'closed through 2025-03-31' in r.out + plan_of('bank-a', c, '')
          and 'walk-books-reverse' in r.out + plan_of('bank-a', c, ''), r.out[-500:])
    for why, on, inputs, said in (
            ("a payment another statement still names (a response to it), naming it", 'box',
             dict(of='heard#lent', reason='never lent'), 'heard: respond still names what would go'),
            ("a line read from a source: its whole statement goes, or nothing", 'box',
             dict(of='bank-a-2025-05#line-001', reason='a mistake'), 'take out its statement, bank-a-2025-05, whole'),
            ("a document taken out whole by a run sitting on it", 'shop', dict(of='shop', reason='a mistake'),
             'the run sits on shop'),
            ("the books' own bean", 'box', dict(of='books-sam', reason='a mistake'), "is the books' own bean"),
            ("a being's bean", 'box', dict(of='card-a', reason='a mistake'), 'is a contract, no document'),
            ("a removal without its reason", 'box', dict(of='heard'), 'reason: say why'),
            ("two documents in one input", 'box', dict(of=['heard', 'shop'], reason='a mistake'), 'of: one value, not 2')):
        got = planned('remove', on, **inputs)
        check(f"...refused at its plan: {why}", got.startswith('REFUSED') and said in got, got[-500:])
    r, c = start('cafe', 'remove', of='cafe#cake', reason='recorded by mistake')
    r2 = ratify('cafe', c)
    cafe = open(os.path.join(G, 'beans', 'cafe.md'), encoding='utf-8').read()
    check("...a payment recorded by mistake taken out of its bean, the run sitting on that bean; the bean and its other "
          "payment stay", 'stopped at done' in r2.out and 'id: cake' not in cafe and 'id: bread' in cafe
          and not voucher('cafe#cake') and voucher('cafe#bread'), r.out[-400:] + r2.out[-500:])
    sam = open(os.path.join(G, 'beans', 'books-sam.md'), encoding='utf-8').read()
    check("...and the last key `details` held goes with its payment, `details` itself with it, named in the entry",
          'details' not in sam.split('\nstatements:\n', 1)[0] and 'cafe#cake' not in sam
          and '`details`, which held nothing more' in entry_of('cafe#cake taken out'), sam[:600])
    bean('loose', 'document', 'a receipt noted by hand', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: tip, by: sam, of: { count: "2.00", unit: XTS }, at: "2025-04-15" }')
    j = open(os.path.join(G, 'beans', 'heard.md'), encoding='utf-8').read()
    write('beans/heard.md', j.replace('\nstatements:\n', '\ndetails: { "loose#tip": { note: "by hand" } }\nstatements:\n', 1))
    save('a receipt, noted by hand beside another', '- action: wrote [[loose]] and [[heard]] details')
    r, c = start('box', 'remove', of='loose', reason='a mistake')
    check("...refused where a `details` naming what goes is not written as a tool writes it: a person's own save takes "
          "it out", 'stopped at refused' in r.out and 'heard: its `details` is not written as a tool writes it'
          in r.out + plan_of('box', c, '')
          and os.path.exists(os.path.join(G, 'beans', 'loose.md')), r.out[-600:])
    bean('kept-off', 'document', 'a receipt with a sealed line', 'say: { by: sam, at: now }', 'own: { by: sam, of: self }',
         'pay: { id: sealed, held: "root:held/0123456789abcdef0123456789abcdef" }')     # read, never saved
    got = planned('remove', of='kept-off', reason='a mistake') + \
        planned('remove', of='kept-off#sealed', reason='a mistake')
    os.remove(os.path.join(G, 'beans', 'kept-off.md'))
    check("...refused at its plan: a document or a payment that holds a statement sealed off git (erase it first)",
          got.count('REFUSED: kept-off#sealed is sealed, kept off git: erase it first') == 2, got[-600:])
    bean('afar', 'garden', "a friend's garden, met here", 'say: { by: sam, at: now }')     # read, never saved
    bean('their-bill', 'document', "a bill the friend's garden proposed", 'own: { by: sam, of: self }',
         'say: { by: sam, at: ["2025-04-12 10:00+00:00", afar] }',
         'pay: { id: owed, by: sam, to: afar, of: { count: "9.00", unit: XTS }, at: "2025-04-12" }')
    got = planned('remove', of='their-bill', reason='a mistake') + \
        planned('remove', of='their-bill#owed', reason='a mistake')
    for b_ in ('afar', 'their-bill'):
        os.remove(os.path.join(G, 'beans', f'{b_}.md'))
    check("...refused at its plan: another garden's word, taken from its proposal — disputed there, never taken out "
          "here", got.count("their-bill#owed (afar's): another garden's word") == 2, got[-600:])
    csv_bean = next((v['ref'].split('#', 1)[0] for v in books('vouchers') if v['ref'].startswith('statement-')), '?')
    r, c = start('box', 'remove', of=csv_bean, reason='imported by mistake')
    r2 = ratify('box', c)
    again = planned('import', 'card-a', file=os.path.join(G, 'statement-06.csv'), format='csv',
                    mapping='extracts/bank-csv.yaml', means='bank-a')
    check("...a bank's statement imported by mistake taken out whole: its lines leave the books, and the same file may "
          "be imported again", 'stopped at done' in r2.out
          and not os.path.exists(os.path.join(G, 'beans', f'{csv_bean}.md'))
          and not any(v['ref'].startswith(csv_bean) for v in books('vouchers')) and not again.startswith('REFUSED'),
          r.out[-400:] + r2.out[-500:] + again[-400:])

    g = run(PY, 'core/check.py', '.')
    check("the garden passes its gate after every run", g.returncode == 0, g.out[-800:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nbooks_walks: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
