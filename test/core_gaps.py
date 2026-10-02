#!/usr/bin/env python3
"""The gaps v1 part 12b closed, read by the tools in a garden of the core (2026-10-02).

Part 12 left some of today's promises unheld, because the core had no form for what they were about, or because no
garden of the core had been asked. This grows a garden of the core from a release made of this tree (test/grow.py,
reading no std-vocab), taking the accounting and knowledge profiles, with an analytic scheme of its own, and asks its
tools what today's suites asked of today's garden:

  ledger      a payment priced in one currency and charged in another, the rate it implies read; a clause that occurs
              for each member of a reading, settled occurrence by occurrence (`settles`); one who acts for a party
  weigh       a weighing's weights and its consistency, read and never stored (`reckon weigh <bean>#<id>`)
  series      a series' whole read exactly against its rows, and refused when wrong
  allowance   how much of an allowance is used within a window that slides (`used-within`)
  accounting  a payment booked to accounts of the garden's scheme, judged plan by plan, apportioned exactly and in the
              currency's cents by the largest remainders
  crosswalk   Darwin Core occurrences carried to `be` statements and back, column for column

Run: python3 test/core_gaps.py   (0 = green; about half a minute)
"""
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


T = tempfile.mkdtemp(prefix='core-gaps-')
G = os.path.join(T, 'g')


def run(*a, stdin=None):
    return grow.run(*a, cwd=G, stdin=stdin)


def write(rel, text):
    p = os.path.join(G, *rel.split('/'))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def text(rel):
    with open(os.path.join(G, *rel.split('/')), encoding='utf-8') as fh:
        return fh.read()


def bean(bid, kind, title, *statements, body=None):
    return (f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{title}\"\nsummary: \"{title}, invented.\"\nstatements:\n"
            + ''.join(f"  - {s}\n" for s in statements) + f"---\n{body or title + '.'}\n")


def gate():
    r = run(PY, 'core/check.py', '.')
    return [ln for ln in r.out.splitlines() if ln and not ln.startswith('core check')]


VOCAB = """---
profiles: [accounting, knowledge]
kinds:
  - { kind: tree, nature: body, line: living, level: organism, meaning: "a tree, where it was found", vacant: "the rowans the crosswalk carries come in a later commit" }
schemes:
  - scheme: analytic
    classifies: where the garden's money goes, plan by plan
    holding: extract
    licence: CC0-1.0
    publisher: the garden
    url: "https://example.org/analytic"
    levels: [ { level: plan }, { level: account } ]
    neighbours: none
    sources: extracts/analytic.tsv
files:
  - { registry: analytic, file: extracts/analytic.tsv, key: code }
---
# the garden's own rows
"""
ANALYTIC = ("code\tlevel\tparent\tname\nprojects\tplan\t\tProjects\ndepartments\tplan\t\tDepartments\n"
            "orchard\taccount\tprojects\tThe orchard\nworkshop\taccount\tprojects\tThe workshop\n"
            "bench\taccount\tprojects\tThe bench\nengineering\taccount\tdepartments\tEngineering\n")
GOOD = (("singable", "loved", "2"), ("singable", "new", "3"), ("singable", "cheap", "5"),
        ("loved", "new", "2"), ("loved", "cheap", "3"), ("new", "cheap", "2"))


def choir(pairs):
    return bean('choir', 'document', 'the choir', 'say: { by: sam, at: now }',
                'weigh: { id: programme, by: sam, to: improvements, weighing: { criteria: [ '
                '{ name: singable, what: "learnt in a term" }, { name: loved, what: "the audience loves it" }, '
                '{ name: new, what: "new to the choir" }, { name: cheap, what: "its scores cost little" } ], pairwise: [ '
                + ', '.join(f'{{ a: {a}, b: {b}, judged: "{j}" }}' for a, b, j in pairs) + ' ] } }')


GAUGE = '''---
bean: gauge
kind: host
title: "the rain gauge"
summary: "the rain gauge, invented."
statements:
  - say: { by: sam, at: now }
  - own: { by: sam, of: self }
  - record:
      id: week
      of: self
      series:
        grid: { of: time, in: gregorian-civil, every: { count: "1", unit: d }, from: "2026-09-14 06:00+02:00" }
        unit: d
        placement: following
        holds:
          - { name: rain, quantity: length, unit: mm, stands_for: sum }
        whole:
          - { value: { count: "%s", unit: mm }, of: rain, by: sum }
        rows: |
          rain
          1.5
          2.5
          4
---
The rain gauge.
'''

try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam', '--profile', 'accounting', '--profile', 'knowledge')
    check(f"a garden of the core (core@{grow.VERSION}) grows taking the accounting and knowledge profiles",
          r.returncode == 0, r.out[-800:])
    write('VOCAB.md', VOCAB)
    write('extracts/analytic.tsv', ANALYTIC)
    write('beans/ana.md', bean('ana', 'person', 'Ana', 'say: { by: sam, at: now }', 'own: { by: theone, of: self }',
                               'answer: { by: self, of: self, as: law }'))
    write('beans/rent.md', bean(
        'rent', 'contract', 'the rent', 'say: { by: sam, at: now }', 'own: { by: theone, of: self }',
        'agree: { id: a, by: [sam, ana], of: self, through: spoken, at: 2026-09-01 }',
        'represent: { by: ana, of: sam, as: agent, note: "she collects it while Sam travels" }',
        'reckon: { id: months, reading: { what: "the lease itself, once", steps: [ { id: p, op: select, kind: contract, '
        'where: [ { path: bean, "=": rent } ] } ] } }',
        'pay: { id: monthly, by: ana, to: sam, of: { count: "3400.00", unit: TRY } }',
        'obligatory: { id: rent-due, of: monthly, through: a, clause: { each: months } }',
        'pay: { id: paid-sept, by: ana, to: sam, of: { count: "100.00", unit: USD }, charged: { count: "3400.00", '
        'unit: TRY }, at: 2026-09-05, settles: [ { clause: rent-due, occurrence: rent, amount: { count: "3400.00", '
        'unit: TRY } } ] }',
        'pay: { id: repairs, by: sam, of: { count: "100.00", unit: TRY }, at: 2026-09-10 }',
        'book: { of: repairs, to: "analytic:orchard", share: "60" }',
        'book: { of: repairs, to: "analytic:workshop", share: "40" }',
        'book: { of: repairs, to: "analytic:engineering", share: "1" }',
        'pay: { id: thirds, by: sam, of: { count: "100.00", unit: TRY }, at: 2026-09-11 }',
        'book: { of: thirds, to: "analytic:orchard", share: "1" }',
        'book: { of: thirds, to: "analytic:workshop", share: "1" }',
        'book: { of: thirds, to: "analytic:bench", share: "1" }'))
    write('beans/choir.md', choir(GOOD))
    write('beans/gauge.md', GAUGE % '8')
    write('beans/studio.md', bean(
        'studio', 'contract', 'the studio pass', 'say: { by: sam, at: now }', 'own: { by: theone, of: self }',
        'agree: { by: [ana], of: self, at: 2026-09-30 }',
        *[f'attend: {{ by: ana, of: self, at: 2026-10-{d:02d} }}' for d in range(2, 15)],
        'reckon: { id: used, reading: { what: "the visits within the thirty days ending on the day asked", inputs: [ '
        '{ name: day, origin: { act: say }, type: position } ], steps: [ { id: all, op: select, kind: contract, where: '
        '[ { path: bean, "=": studio } ] }, { id: visits, op: select, of: all, entries: attend }, { id: in-window, '
        'op: used-within, of: visits, path: at, within: { of: time, measure: { count: "30", unit: day } }, at: { input: '
        'day } } ] } }'))
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: the garden\'s scheme; the rent, the choir, the gauge, the pass',
            '--body', '- action: RULE-CHANGE — VOCAB.md adds the kind tree and the scheme analytic; wrote [[ana]], '
            '[[rent]], [[choir]], [[gauge]] and [[studio]]')
    check("the rent (charged, settled, booked), the choir's weighing, the gauge's series and the studio pass are saved "
          "through the core's gate", r.returncode == 0, r.out[-1500:])

    # ---- LEDGER: the rate a payment implies; a clause's occurrences, each settled; who acts for whom
    r = run(PY, 'bin/ledger.py', 'rent')
    check("ledger: a payment priced in one currency and charged in another shows the rate it implies, exactly, and the "
          "positions are kept in what moved", r.returncode == 0 and 'charged' in r.out and 'priced' in r.out
          and '3400' in r.out and 'USD' in r.out, r.out[-1800:])
    check("ledger: a clause that occurs for each member of a reading is read occurrence by occurrence, with what each "
          "payment `settles` of it", 'occurs for each member of months: 1 occurrence' in r.out and 'rent' in r.out
          and re.search(r'settled|paid', r.out), r.out[-1800:])
    check("ledger: one who acts for a party is said: what she does binds the party", 'ana acts for sam' in r.out,
          r.out[-1800:])

    # ---- WEIGH: read, never stored
    r = run(PY, 'bin/reckon.py', 'weigh', 'choir#programme')
    cr = re.search(r'CR ≈ ([0-9.]+)', r.out)
    check("weigh: a weighing of the core's (`weigh` statement) — each weight marked ≈, a consistency ratio of about 0.02, "
          "none stored", r.returncode == 0 and cr and float(cr.group(1)) < 0.05 and 'singable: ≈ 0.' in r.out
          and 'never stored' in r.out, r.out[-800:])
    write('beans/choir.md', choir(GOOD[:1] + (("singable", "new", "1/5"),) + GOOD[2:]))
    got = [ln for ln in gate() if ln.startswith('measured')]
    check("weigh: a reversed judgment makes it inconsistent (CR above 0.10), refused by rule measured without "
          "`why_inconsistent`", got and any('above 0.10' in ln for ln in got), got or gate())
    write('beans/choir.md', choir(GOOD[:-1]))
    got = [ln for ln in gate() if ln.startswith('measured')]
    check("weigh: a pair left unjudged is refused, naming it", any('not judged: (new, cheap)' in ln for ln in got), got)
    run('git', 'checkout', '--', 'beans/choir.md')

    # ---- SERIES: its whole read exactly against its rows
    write('beans/gauge.md', GAUGE % '9')
    got = [ln for ln in gate() if ln.startswith('line')]
    check("series: a whole that is not what its rows add up to (1.5 + 2.5 + 4 is 8, not 9) is refused by rule line, "
          "exactly", got and any('whole' in ln for ln in got), got or gate())
    run('git', 'checkout', '--', 'beans/gauge.md')
    check("...and the whole they add up to passes", not gate(), gate())

    # ---- ALLOWANCE: counted within a window that slides
    r = run(PY, 'bin/reckon.py', 'studio#used', '--input', 'day=2026-10-30')
    check("allowance: the thirteen visits within the thirty days ending 2026-10-30 are counted, 13 items",
          r.returncode == 0 and '= 13 item' in r.out, r.out[-900:])
    r = run(PY, 'bin/reckon.py', 'studio#used', '--input', 'day=2026-11-10')
    check("...and a window that has slid on holds fewer: 3", r.returncode == 0 and '= 3 item' in r.out, r.out[-900:])

    # ---- ACCOUNTING: judged plan by plan, apportioned exactly and in cents
    def reading(name, extra):
        p = os.path.join(T, name + '.yaml')
        with open(p, 'w', encoding='utf-8') as fh:
            fh.write('what: "where the money went"\nsteps:\n'
                     '  - { id: this, op: select, kind: contract, where: [ { path: bean, "=": rent } ] }\n'
                     f'  - {{ id: paid, op: select, of: this, entries: pay, where: [ {{ path: id, "=": {name} }} ] }}\n'
                     f'  - {{ id: where, op: apportion, of: paid, amount: of, over: book{extra} }}\n')
        r = run(PY, 'bin/reckon.py', '--ad-hoc', p)
        return dict(re.findall(r'^  ([a-z-]+): (.*)$', r.out, re.M)), r.out
    got, out = reading('repairs', '')
    check("accounting: apportion reads each account's part exactly: 60 and 40 of the projects, the whole to engineering",
          got == {'orchard': '60 TRY', 'workshop': '40 TRY', 'engineering': '100 TRY'}, out[-800:])
    got, out = reading('repairs', ', level: plan')
    check("...rolled up to the plans, each plan holds the whole", got == {'projects': '100 TRY', 'departments': '100 TRY'},
          out[-800:])
    got, out = reading('thirds', '')
    check("...a split that is no whole number of cents is kept exact", got.get('orchard') == '100/3 TRY', out[-800:])
    got, out = reading('thirds', ', digits: true')
    check("...and written in the currency's cents, the cent left over to the largest remainder, the first code first",
          (got.get('orchard'), got.get('workshop'), got.get('bench')) == ('33.34 TRY', '33.33 TRY', '33.33 TRY'),
          out[-800:])
    keep = text('beans/rent.md')
    write('beans/rent.md', keep.replace('to: "analytic:orchard", share: "60"', 'to: "analytic:orchard", share: { count: '
                                        '"70.00", unit: TRY }').replace('to: "analytic:workshop", share: "40"', 'to: '
                                        '"analytic:workshop", share: { count: "20.00", unit: TRY }'))
    got = [ln for ln in gate() if ln.startswith('profile')]
    check("accounting: bookings in amounts are judged plan by plan — 70 and 20 make 90 TRY, and the payment is 100",
          any('the plan projects add up to 90' in ln for ln in got), got or gate())
    write('beans/rent.md', keep.replace('to: "analytic:orchard", share: "60"', 'to: "analytic:orchard", share: { count: '
                                        '"70.00", unit: TRY }'))
    got = [ln for ln in gate() if ln.startswith('profile')]
    check("...and a plan stated partly in amounts and partly in shares is no whole anyone can judge",
          any('amounts for some of its parts and shares for others' in ln for ln in got), got)
    write('beans/rent.md', keep.replace('analytic:engineering', 'analytic:nowhere'))
    got = [ln for ln in gate() if ln.startswith('profile')]
    check("...and an account is a code of the garden's scheme", any("'nowhere' is not a code of analytic" in ln
                                                                    for ln in got), got)
    run('git', 'checkout', '--', 'beans/rent.md')

    # ---- CROSSWALK: Darwin Core occurrences, into statements and back
    DWC = ("occurrenceID,eventDate,decimalLatitude,decimalLongitude,geodeticDatum,coordinateUncertaintyInMeters,locality,"
           "scientificName,recordedBy\n"
           "rowan-north,2026-05-02,57.1203,-6.1044,EPSG:4326,30,above the north landing,Sorbus aucuparia,keeper\n"
           "rowan-glen,2026-05-03,57.0981,-6.0877,EPSG:4326,,the glen by the old mill,Sorbus aucuparia,keeper\n")
    write('in/occ.csv', DWC)
    r = run(PY, 'bin/crosswalk.py', 'to', 'dwc', 'in/occ.csv')
    check("crosswalk: Darwin Core occurrences carried to the core's `be` statements, a coordinate in its system's one "
          "form, the uncertainty an accuracy of kind bound; a taxon and a recorder, which a `be` has no place for, listed",
          r.returncode == 0 and 'EPSG:4326;57.1203,-6.1044' in r.stdout and 'be:' in r.stdout and 'kind: bound' in r.stdout
          and 'scientificName' in r.stderr, r.out[-1500:])
    for bid, body in re.findall(r"# beans/([a-z-]+)\.md\nstatements:\n(.*?)(?=\n# beans/|\Z)", r.stdout, re.S):
        write(f"beans/{bid}.md", f"---\nbean: {bid}\nkind: tree\ntitle: \"{bid}\"\nsummary: \"a rowan on an invented "
                                 f"island\"\nstatements:\n  - read: {{ by: sam, at: now }}\n  - own: {{ by: sam, of: self }}\n"
                                 f"  - come: {{ by: self, through: [ {{ someone: tree }} ] }}\n"
                                 + ''.join('  ' + ln + '\n' for ln in body.rstrip().split('\n')) + f"---\n{bid}, invented.\n")
    r = run(PY, 'bin/save.py', 'sam', 'two rowans, carried from Darwin Core', '--body',
            '- action: wrote [[rowan-north]] and [[rowan-glen]] from a Darwin Core extract')
    check("crosswalk: the carried positions pass the core's gate", r.returncode == 0, r.out[:3000])
    r = run(PY, 'bin/crosswalk.py', 'back', 'dwc', 'rowan-north', 'rowan-glen')
    import csv
    import io
    rows = [{k: v for k, v in x.items() if v != ''} for x in csv.DictReader(io.StringIO(r.stdout))]
    want = [{k: v for k, v in x.items() if v != '' and k not in ('scientificName', 'recordedBy')}
            for x in csv.DictReader(io.StringIO(DWC))]
    check("crosswalk: the round trip — every column not listed comes back equal, and back lists nothing",
          rows == want and 'not carried' not in r.stderr, (rows, want, r.stderr[-600:]))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_gaps: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
