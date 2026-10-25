#!/usr/bin/env python3
"""The measure tools in a garden of the core (v1 part 7): cal, geo, units, knowledge, crosswalk — and the forms of a
measure they read: a clause's terms (`can`'s `clause`: a recurrence, a notice, a due relative to a position, an
allowance), a placement's (`be`'s `placed`: what it takes of its host, how well its position is known), a quantity's
uncertainty, and a garden's own systems, schemes and files (VOCAB.md `systems`, `schemes`, `files`), judged by the core's
rule `measured`.

Builds what it needs, as test/core_read.py does: a release of the core made from this tree (v1.0.0), and a GARDEN grown
from it, keeping two hives at sites of its own apiary system and a lease paid each month, a rack that holds two slots and
a machine in one of them.

law: a clause's form says how it runs out (`expiry`), and the law holds together with its rules. gate: the garden saved through the core's gate; each form's breach refused by rule `measured`, by name. units: a
conversion by UCUM code and by the English name, exactly. cal: a day in another calendar. geo: a distance on the body the
core's places name. knowledge: a code of the garden's own scheme, and a bean's codes from its statements. stale and
ledger: a clause's recurrence and notice read from its form. where: a position in the garden's own system. crosswalk: a
FHIR observation carried to a `measure` and back. translate: today's clause, placement and own rows written in these
forms, every value placed — the old garden grown from the release in today's words (v0.49.0).

Run: python3 test/core_measure.py   (0 = green; about a minute)
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
import grow  # noqa: E402 — a release of the core, and the release in today's words
import importlib
import parse as dmparse
dmpass = importlib.import_module('pass')  # noqa: E402

FAILS = []
PY = sys.executable
VERSION = str(read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))['version'])


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x', PYTHONIOENCODING='utf-8')
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e))


def text(path, root=None):
    with open(os.path.join(root or G, path), encoding='utf-8') as fh:
        return fh.read()


def write(path, t, root=None):
    p = os.path.join(root or G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def clean():
    return run('git', 'status', '--porcelain').out.strip() == ''


def refused(path, old, new, says, rule='measured'):
    """The gate's verdict on the bean at `path` with `old` written as `new`: (refused by `rule` saying `says`, output);
    the bean put back."""
    keep = text(path)
    assert old in keep, old
    write(path, keep.replace(old, new, 1))
    r = run(PY, 'bin/check.py')
    write(path, keep)
    return r.returncode != 0 and any(ln.startswith(rule) and says in ln for ln in r.out.split('\n')), r.out[-900:]


T = tempfile.mkdtemp(prefix='core-measure-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden')

VOCAB = """---
profiles: [knowledge]
kinds:
  - { kind: hive, nature: body, organisation: population, bios: living, meaning: "a colony of bees, and the box it lives in" }
systems:
  - system: apiary-site
    dimension: place
    complement: [stated, bearer]
    levels: [ { level: valley }, { level: site } ]
    neighbours: counted
    cells_in: { registry: apiary-sites, take: code }
    meaning: "the co-op's apiary sites, as its register tabulates them"
    pattern: '^apiary:[A-Z]+(-[0-9]+)?$'
    form_note: "`apiary:<code>` — `apiary:EAST-1`"
    example: "apiary:EAST-1"
    establishes: false
    why: "a site says roughly where, never which hive"
schemes:
  - scheme: hive-checks
    classifies: what a beekeeper reads of a hive at an inspection, and how
    holding: extract
    licence: CC0-1.0
    publisher: the co-op
    url: "https://example.org/hive-checks"
    levels: [ { level: check } ]
    neighbours: none
    sources: extracts/hive-checks.tsv
files:
  - { registry: apiary-sites, file: extracts/apiary-sites.tsv, key: code }
  - { registry: hive-checks, file: extracts/hive-checks.tsv, key: code }
---
# garden — the garden's own rows
"""

SITES = "code\tparent\tlevel\tname\tpoint\nEAST\t\tvalley\tthe east valley\tEPSG:4326;10.42,20.31\n" \
        "EAST-1\tEAST\tsite\tthe orchard\tEPSG:4326;10.421,20.312\n"
CHECKS = "code\tname\nvarroa-drop\tmites fallen on the sticky board\nqueen-seen\tthe queen seen\n" \
         "sticky-board\ta board under the mesh floor\nhive-weight\tthe hive weighed whole\n"

HIVE = """---
bean: hive-1
kind: hive
title: "hive-1 — the hive in the orchard"
summary: "A colony Sam keeps at the orchard site."
statements:
  - say:      { by: sam, at: now }
  - own:      { by: sam, of: self }
  - be:       { id: site, by: self, at: "apiary:EAST-1", as: location, placed: { openness: elsewhere, mobility: fixed } }
  - classify: { of: self, as: "hive-checks:queen-seen" }
  - measure:  { id: mites-june, by: sam, of: self, as: "hive-checks:varroa-drop", value: { count: "14", unit: "{item}", u: { count: "3", unit: "{item}" } }, method: "hive-checks:sticky-board", at: 2026-06-12 }
  - measure:  { id: queen-june, by: sam, of: self, as: "hive-checks:queen-seen", presence: present, at: 2026-06-12 }
---
A strong colony.
"""

RACK = """---
bean: rack
kind: host
title: "rack — the shed's rack"
summary: "A rack of two slots."
statements:
  - read: { by: sam, at: now }
  - own:  { by: sam, of: self }
  - hold: { by: self, of: [ { count: "2", unit: "{item}" } ] }
---
The rack.
"""

NAS = """---
bean: nas
kind: host
title: "nas — the shed's file server"
summary: "A file server in the rack's first slot."
statements:
  - read: { by: sam, at: now }
  - own:  { by: sam, of: self }
  - be:   { id: slot, by: self, at: [rack, "rack#u1"], as: location, placed: { takes: [ { count: "1", unit: "{item}" } ], u: { count: "1", unit: cm } } }
---
The file server.
"""

LANDLORD = """---
bean: landlord
kind: org
title: "landlord — the shed's owner"
summary: "The firm that lets the shed."
statements:
  - say: { by: sam, at: now }
---
The landlord.
"""

LEASE = """---
bean: lease
kind: contract
title: "lease — the shed, let by the month"
summary: "Sam rents the shed from the landlord: six payments, one each month."
statements:
  - say:        { by: sam, at: now }
  - agree:      { id: agreed, by: [sam], of: ["the shed, for six months"] }
  - can:        { id: rent, by: sam, of: "pay the month's rent", to: landlord, clause: { due: 2026-10-15, every: { of: time, in: gregorian-civil, each: month, at: "15", times: "6" }, notice: { count: "10", unit: d }, amount: { count: "300", unit: XTS } } }
  - obligatory: { of: rent, through: agreed }
---
The lease.
"""

FHIR = [{"resourceType": "Observation", "id": "mites-july", "status": "final",
         "code": {"coding": [{"system": "https://example.org/hive-checks", "code": "hive-weight"}]},
         "subject": {"reference": "Patient/hive-1"}, "effectiveDateTime": "2026-07-12",
         "valueQuantity": {"value": 31.5, "system": "http://unitsofmeasure.org", "code": "kg"},
         "note": [{"text": "a dry week"}]}]

try:
    # ---- THE RELEASE: v1.0.0, a release of the core made from this tree, and a garden grown from it
    grow.release(REL)
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
            '--zone', 'Europe/Berlin', cwd=T)
    check(f"a garden grows from v1.0.0 in the core (core@{VERSION}), the measure tools in it",
          r.returncode == 0 and f'core@{VERSION}' in text('GARDEN.md')
          and all(os.path.isfile(os.path.join(G, 'bin', f"{v}.py")) and not os.path.exists(os.path.join(G, 'bin', f"dm{v}.py"))
                  for v in ('cal', 'geo', 'units', 'knowledge', 'crosswalk')), r.out[-800:])
    run(PY, 'bin/install.py')

    # ---- THE LAW: the forms of a measure, a clause's expiry, and the law's rules
    clause = read.data(os.path.join(ROOT, 'core', 'law', 'measures.yaml'))['forms']['clause']
    check("law: a clause says how it runs out (`expiry`: the day it falls due, lapses, repeats, its notice), which the "
          "stale reader and the ledger read", (clause.get('expiry') or {}).get('attr') == 'due'
          and (clause['expiry'].get('notice') or {}).get('measure') == {'count': '7', 'unit': 'd'}, clause.get('expiry'))
    r = run(PY, 'core/check.py', '--law')
    check("law: the core's law holds together — the forms of a measure and rule `measured`",
          r.returncode == 0 and '21 rules — 0 error(s)' in r.out, r.out[-400:])

    # ---- THE GATE: the forms saved through the core's gate
    write('VOCAB.md', VOCAB)
    write('extracts/apiary-sites.tsv', SITES)
    write('extracts/hive-checks.tsv', CHECKS)
    for p, t in (('beans/hive-1.md', HIVE), ('beans/rack.md', RACK), ('beans/nas.md', NAS),
                 ('beans/landlord.md', LANDLORD), ('beans/lease.md', LEASE)):
        write(p, t)
    r = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: hives, an apiary system and a scheme of checks; a lease, a rack',
            '--body', '- action: RULE-CHANGE — VOCAB.md adds the kind hive, the system apiary-site, the scheme hive-checks and their files; wrote [[hive-1]], [[rack]], '
            '[[nas]], [[landlord]] and [[lease]]')
    check("gate: a clause's recurrence and notice, a placement's room and uncertainty, a reading's uncertainty, a "
          "position in the garden's own system and codes of its own scheme are saved through the core's gate",
          r.returncode == 0 and clean(), r.out[-1500:])
    lp, np_, hp = 'beans/lease.md', 'beans/nas.md', 'beans/hive-1.md'
    for name, path, old_, new, says, rule in (
            ("a recurrence that strides by no rule", lp, 'each: month, at: "15", ', '', "strides by one rule", 'measured'),
            ("a level its system does not have", lp, 'each: month', 'each: fortnight', "no level of gregorian-civil",
             'measured'),
            ("a notice that is no duration", lp, 'unit: d }', 'unit: kg }', "a duration is asked here", 'measured'),
            ("a due both on a day and relative to a position", lp, 'amount: { count: "300", unit: XTS } }',
             'amount: { count: "300", unit: XTS }, falls_due: [ { from: "over.shed", after: { of: time, measure: '
             '{ count: "3", unit: d } } } ] }', "instead of the day it falls due", 'measured'),
            ("a due that is no day of its calendar", lp, 'due: 2026-10-15', 'due: 2026-02-30', "not a day", 'measured'),
            ("an allowance's window with no amount", lp, 'amount: { count: "300", unit: XTS } }',
             'within: { of: time, measure: { count: "90", unit: d } } }', "state the amount", 'measured'),
            ("an extent on a line that has no regions", lp, 'times: "6" }', 'times: "6", lasts: { of: necessity, '
             'measure: { count: "1", unit: d } } }', "holds no region", 'measured'),
            ("more room taken than the host holds", np_, 'count: "1", unit: "{item}"', 'count: "3", unit: "{item}"',
             "room is taken once", 'measured'),
            ("both u and accuracy beside a position", np_, 'u: { count: "1", unit: cm }',
             'u: { count: "1", unit: cm }, accuracy: { count: "5", unit: cm, kind: bound }', "at most one", 'measured'),
            ("an uncertainty in a unit of another quantity", hp, 'u: { count: "3", unit: "{item}" }',
             'u: { count: "3", unit: kg }', "uncertainty is in a unit of the value's own quantity", 'valency'),
            ("a kind of accuracy the table does not have", hp, 'u: { count: "3", unit: "{item}" }',
             'accuracy: { count: "3", unit: "{item}", kind: guess }', "accuracy_kinds", 'valency'),
            ("a position in the garden's own system, in no form of it", hp, '"apiary:EAST-1"', '"apiary:east-1"',
             "in no system's form", 'valency')):
        ok, out = refused(path, old_, new, says, rule)
        check(f"gate: {name} is refused by rule `{rule}`", ok, out)

    # ---- A GRANT'S WINDOW: it holds at a moment in its `at` and in an occurrence of its window, in the garden's zone
    # (Europe/Berlin: +02:00 until the clocks go back on 2026-10-25, +01:00 after)
    sp = 'beans/sam.md'
    write('beans/p-0000aaaa.md', '---\nbean: p-0000aaaa\nkind: person\ntitle: "p-0000aaaa"\nstatements:\n'
                                 '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\np-0000aaaa\n')
    write(sp, text(sp).replace('\n---\nSam keeps', """
  - grant:  { id: office-hours, by: self, to: [p-0000aaaa], of: [hive-1], as: read, at: "2026-10-19/2026-10-30", window: { of: time, in: iso-week, each: week, at: ["1T08:30", "2T08:30", "3T08:30", "4T08:30", "5T08:30"], lasts: { of: time, measure: { count: "10", unit: h } } } }
  - grant:  { id: night-watch, by: self, to: [p-0000aaaa], of: [rack], as: read, at: "2026-10-19/2026-10-23", window: { of: time, in: gregorian-civil, each: day, at: "T22:00", lasts: { of: time, measure: { count: "4", unit: h } } } }
  - grant:  { id: whole-days, by: self, to: [p-0000aaaa], of: [nas], as: read, at: "2026-10-19/2026-10-30" }
  - say:    { by: sam, of: [office-hours, night-watch, whole-days], at: now }
---
Sam keeps""", 1))
    r = run(PY, 'bin/save.py', 'sam', 'a person kept by an opaque id, and what the gardener opens to them, and when',
            '--body', '- action: wrote [[p-0000aaaa]]; [[sam]] grants them the hive in office hours, the rack by night '
                      'and the file server by the day')
    check("gate: a grant held in a recurring window — office hours on working days, a night that crosses midnight — "
          "is saved through the core's gate", r.returncode == 0 and clean(), r.out[-1500:])
    oh = 'lasts: { of: time, measure: { count: "10", unit: h } }'
    for name, old_, new, says in (
            ("a window that says not how long each occurrence lasts", ', ' + oh, '', "says how long"),
            ("a window whose occurrences last cells of a level, not a length", 'measure: { count: "10", unit: h }',
             'level: day, count: "1", in: iso-week', "a length of time"),
            ("a time of day out of its form", '"1T08:30"', '"1T8:30"', "time of day"),
            ("a window that strides with no start", 'each: week, at: ["1T08:30", "2T08:30", "3T08:30", "4T08:30", '
             '"5T08:30"]', 'every: { count: "1", unit: d }', "from"),
            ("a window that strides by neighbours, not by a length of time", 'each: week, at: ["1T08:30", "2T08:30", '
             '"3T08:30", "4T08:30", "5T08:30"]', 'every: { count: "1" }, from: "2026-W43-1"', "a length of time"),
            ("a window counted in a calendar whose day begins at sunset", 'in: iso-week, each: week',
             'in: hebrew-calendar, each: month', "sunset"),
            ("a window in cells finer than a day", 'in: gregorian-civil, each: day, at: "T22:00"',
             'in: gregorian-civil, each: hour', "finer than the day")):
        ok, out = refused(sp, old_, new, says)
        check(f"gate: {name} is refused by rule `measured`", ok, out)

    def may(bean, at, beans=None):
        return dmpass.may('p-0000aaaa', 'read', bean, at=at, root=G, beans=beans)
    for name, bean, inside, outside in (
            ("on a working day, from its time of day for as long as it lasts — read in the garden's zone, whatever "
             "offset the moment is written in", 'hive-1',
             ['2026-10-19 08:30+02:00', '2026-10-19 06:30Z', '2026-10-23 18:29+02:00', '2026-10-20 09:00'],
             ['2026-10-19 08:29+02:00', '2026-10-19 06:29Z', '2026-10-23 18:30+02:00', '2026-10-20 07:00']),
            ("not at the weekend", 'hive-1', [], ['2026-10-24 10:00+02:00', '2026-10-25 10:00+01:00']),
            ("by the zone's rule on each day: after the clocks go back, 08:30 is 07:30Z", 'hive-1',
             ['2026-10-26 07:30Z', '2026-10-30 08:30+01:00'], ['2026-10-26 06:30Z', '2026-10-26 07:29Z']),
            ("never outside its `at`, though the window is open then", 'hive-1', [],
             ['2026-10-16 10:00+02:00', '2026-11-02 10:00+01:00']),
            ("across midnight: an occurrence from 22:00 for four hours holds on into the next day", 'rack',
             ['2026-10-20 22:00+02:00', '2026-10-20 23:30+02:00', '2026-10-21 01:59+02:00'],
             ['2026-10-20 21:59+02:00', '2026-10-21 02:00+02:00', '2026-10-21 12:00+02:00']),
            ("and its `at` bounds that too: the last day's occurrence holds until its midnight, not past it", 'rack',
             ['2026-10-23 23:59+02:00'], ['2026-10-24 01:00+02:00', '2026-10-18 23:00+02:00']),
            ("a grant without a window holds as it did, at any moment of its days", 'nas',
             ['2026-10-24 03:00+02:00', '2026-10-30'], ['2026-10-31']),
            ("a grant without a window holds over its days in the garden's zone: in the small hours east of UTC, a "
             "moment of its first day is inside it and one of the day after its last outside, whatever day it is in "
             "UTC", 'nas', ['2026-10-19 00:30+02:00', '2026-10-18 22:30Z'], ['2026-10-31 00:30+01:00', '2026-10-30 23:30Z'])):
        got = {t: may(bean, t) for t in inside + outside}
        check(f"may: a grant in a window opens {name}" if bean != 'nas' else f"may: {name}",
              all(got[t].granted for t in inside) and not any(got[t].granted for t in outside),
              {t: (a.granted, a.why) for t, a in got.items()})
    # ...AND TODAY IS THE GARDEN'S: asked with no moment, a grant's days are read against today in the garden's zone, as
    # what is due to be erased is — the clock held in the small hours of a Berlin day that is still yesterday in UTC
    probe = r"""import sys, time, json; sys.path.insert(0, 'bin'); import cal, importlib
dmpass = importlib.import_module('pass'); import held
out = {}
for t in ('2026-10-18 22:30Z', '2026-10-30 23:30Z'):
    time.time = lambda t=t: (cal.moment(t).ms - cal.UNIX_DAY * cal.DAY_MS) / 1000
    out[t] = [dmpass.may('p-0000aaaa', 'read', 'nas', root='.').granted,
              dmpass.today_in(dmpass.zone_of('.')) - cal.to_day('2026-10-01') if hasattr(dmpass, 'today_in') else None,
              held.due(root='.', beans={'x': {'records': {'a': {'held': 'root:vault/' + '0' * 32, 'until': '2026-10-31'}}}}, days=0)]
print(json.dumps(out))"""
    r = grow.run(PY, '-c', probe, cwd=G)
    try:
        got = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        got = {}
    check("may: asked with no moment, a grant's days are read against TODAY IN THE GARDEN'S ZONE, and what is due to be "
          "erased too — at 22:30Z on 18 October it is the 19th in Berlin, the grant's first day; at 23:30Z on 30 October "
          "the 31st, the day after its last, when an entry kept until the 31st is due",
          got.get('2026-10-18 22:30Z') == [True, 18, []]
          and got.get('2026-10-30 23:30Z') == [False, 30, [['x', 'records', 'a', 0]]], (got, r.out[-800:]))
    a = may('hive-1', '2026-10-20')
    check("may: a grant in a window is judged at a moment — a day asked opens nothing through it, and says why",
          not a.granted and 'window' in a.why, a)
    beans = dmpass.beans_here(G)
    beans['sam'] = dict(beans['sam'], statements=list(beans['sam']['statements']) + [
        {'grant': {'id': 'unread-window', 'by': 'self', 'to': ['p-0000aaaa'], 'of': ['landlord'], 'as': 'read',
                   'window': {'of': 'time', 'in': 'iso-week', 'each': 'week', 'at': '1T08:30'}}}])
    a = may('landlord', '2026-10-19 09:00+02:00', beans)
    check("may: a window it cannot read (no `lasts`, which the gate refuses) opens nothing, and the answer says why",
          not a.granted and 'unread-window' in a.why and 'window' in a.why, a)

    # ---- A RECURRENCE'S TIME OF DAY, read by each reader in the garden, by the law it runs: the day where only the day
    # matters (bin/stale.py's walk), the clock where it does (a routine's moments, its cron line)
    probe = r"""import sys, json; sys.path.insert(0, 'bin'); import stale, cal, routines
def ms(t): return cal.moment(t).ms - cal.UNIX_DAY * cal.DAY_MS
def shown(b): return cal.write_moment(b + cal.UNIX_DAY * cal.DAY_MS, 'gregory', '+01:00' if b >= ms('2026-10-25 01:00Z') else '+02:00')
def tried(f):
    try: return f()
    except routines.Refused as e: return 'refused: ' + str(e)
    except Exception as e: return repr(e)
two = {'of': 'time', 'in': 'iso-week', 'each': 'week', 'at': ['1T08:30', '5T17:45']}
lasts = {'of': 'time', 'measure': {'count': '30', 'unit': 'min'}}
print(json.dumps({
  'days': tried(lambda: [cal.from_day(n, 'gregory') for n, _ in zip(stale.occurrences(stale.day_of('2026-10-19'), two), range(4))]),
  'six': tried(lambda: len([n for n, _ in zip(stale.occurrences(stale.day_of('2026-10-15'), {'of': 'time', 'in': 'gregorian-civil', 'each': 'month', 'at': '15T09:00', 'times': '6'}), range(12))])),
  'moments': tried(lambda: [shown(b) for b, _e in stale.moments('2026-10-19 08:30', dict(two, lasts=lasts), ms('2026-10-19 00:00+02:00'), ms('2026-10-31 00:00+01:00'), zone='Europe/Berlin')]),
  'cron': tried(lambda: routines.clause_to_cron({'due': '2026-10-23 17:45', 'every': {'of': 'time', 'in': 'iso-week', 'each': 'week', 'at': '5T17:45'}})),
  'two_clocks': tried(lambda: routines.clause_to_cron({'due': '2026-10-19 08:30', 'every': two}))}))
"""
    r = run(PY, '-c', probe)
    got = json.loads(r.out) if r.returncode == 0 and r.out.strip().startswith('{') else {}
    check("stale: a place with a time of day is read as its day where only the day matters — Mondays and Fridays; the "
          "15th of each month, six times", got.get('days') == ['2026-10-19', '2026-10-23', '2026-10-26', '2026-10-30']
          and got.get('six') == 6, got or r.out[-800:])
    check("moments: a routine's occurrences fall at the time of day each place names, in its zone",
          got.get('moments') == ['2026-10-19 08:30+02:00', '2026-10-23 17:45+02:00', '2026-10-26 08:30+01:00',
                                 '2026-10-30 17:45+01:00'], got.get('moments') or r.out[-800:])
    check("cron: a place with its due's time of day is one line; two times of day are refused, never one of them kept",
          got.get('cron') == '45 17 * * fri' and str(got.get('two_clocks')).startswith('refused: ')
          and 'time of day' in str(got.get('two_clocks')), (got.get('cron'), got.get('two_clocks')))

    # ---- THE TOOLS
    r = run(PY, 'bin/units.py', '90', 'km/h', 'm/s')
    r2 = run(PY, 'bin/units.py', '90', 'kilometre-per-hour', 'metre-per-second')
    check("units: 90 km/h is 25 m/s exactly — by the UCUM codes, and by the English names through the alias",
          r.returncode == 0 and r.out.startswith('25 m/s') and r2.returncode == 0 and r2.out.startswith('25 '),
          r.out + r2.out)
    r = run(PY, 'bin/units.py', '1', 'h', 'kg')
    check("units: an hour is no mass, refused", r.returncode == 1 and 'nothing converts' in r.out, r.out)
    r = run(PY, 'bin/units.py', '120', 'mm[Hg]', 'cm[H2O]')
    r2 = run(PY, 'bin/units.py', '1', '[psi]', 'kPa')
    r3 = run(PY, 'bin/units.py', '25000', 'IRT', 'IRR')
    check("units: the ladder's units convert exactly — a column of mercury into one of water, a psi into kilopascals, "
          "the toman into the rials it is counted in",
          r.out.startswith('163.1412 cm[H2O]') and r2.out.startswith('8896443230521/1290320000000 kPa')
          and r3.out.startswith('250000 IRR'), r.out + r2.out + r3.out)
    r = run(PY, 'bin/units.py', '1', 'rad', 'deg')
    r2 = run(PY, 'bin/units.py', '1', 'IRT', 'USD')
    check("units: a radian meets a degree only through π, and the toman another currency only through an observed rate",
          r.returncode == 1 and 'no factor' in r.out and r2.returncode == 1 and 'rate' in r2.out, r.out + r2.out)
    r = run(PY, 'bin/cal.py', '2026-09-20', 'persian')
    check("cal: 2026-09-20 is persian:1405-06-29", r.returncode == 0 and '1405-06-29' in r.out, r.out)
    r = run(PY, 'bin/geo.py', 'EPSG:4326;35.6892,51.3890', 'EPSG:4326;41.0082,28.9784')
    check("geo: a distance on the body the core's places name (Tehran to Istanbul, about 2,000 km)",
          r.returncode == 0 and 'km' in r.out and 'earth' in r.out.lower(), r.out[-600:])
    r = run(PY, 'bin/knowledge.py', 'show', 'hive-checks', 'varroa-drop')
    check("knowledge: a code of the garden's own scheme (`schemes`, its file in `files`)",
          r.returncode == 0 and 'mites fallen' in r.out, r.out[-600:])
    r = run(PY, 'bin/knowledge.py', 'bean', 'hive-1')
    check("knowledge: a bean's codes are its statements — `classify` — read through the alias",
          r.returncode == 0 and 'queen-seen' in r.out and 'classified_as' in r.out, r.out[-600:])
    r = run(PY, 'bin/ledger.py', 'lease')
    check("ledger: a clause's recurrence, notice and amount are read from its form",
          r.returncode == 0 and 'rent' in r.out and 'month' in r.out and '300' in r.out, r.out[-1200:])
    r = run(PY, 'bin/stale.py', '--days', '4000')
    check("stale: a clause that repeats is warned about before its next occurrence, read from its form",
          'lease' in r.out and 'rent' in r.out, r.out[-1200:])
    r = run(PY, '-c', 'import sys; sys.path.insert(0, "bin"); import stale; '
            'rec = {"of": "time", "in": "gregorian-civil", "each": "month", "at": "15", "times": "6"}; '
            'print(len([n for n, _ in zip(stale.occurrences(stale.day_of("2026-10-15"), rec), range(12))]))')
    check("stale: `times` as the core reads it, as text, is counted — the lease's rent falls due six times, not on",
          r.returncode == 0 and r.out.strip() == '6', r.out[-600:])
    r = run(PY, 'bin/where.py', 'apiary:EAST-1')
    check("where: a position in the garden's own system (`systems`), its cell from the garden's file",
          r.returncode == 0 and 'orchard' in r.out, r.out[-800:])

    # ---- THE CROSSWALK: a FHIR observation to a `measure`, and back
    write('in/obs.json', json.dumps(FHIR), T)
    r = run(PY, 'bin/crosswalk.py', 'to', 'fhir', os.path.join(T, 'in', 'obs.json'))
    check("crosswalk: a FHIR observation is carried to a `measure` — its code the `as`, its value in UCUM",
          r.returncode == 0 and 'measure:' in r.out and 'hive-checks:hive-weight' in r.out and "unit: kg" in r.out,
          r.out[-1200:])
    keep = text(hp)
    stmt = "  - measure:  { id: mites-july, by: sam, of: self, as: \"hive-checks:hive-weight\", value: { count: \"31.5\", " \
           "unit: kg }, at: 2026-07-12, note: \"a dry week\" }\n"
    write(hp, keep.replace("---\nA strong colony.", stmt + "---\nA strong colony."))
    r = run(PY, 'bin/crosswalk.py', 'back', 'fhir', 'hive-1', 'mites-july')
    back = json.loads(r.out.split('\nnot carried')[0]) if r.returncode == 0 and r.out.lstrip().startswith('[') else []
    rec = back[0] if back else {}
    check("crosswalk: a `measure` is carried back to a FHIR observation, field for field",
          rec.get('id') == 'mites-july' and (rec.get('valueQuantity') or {}).get('code') == 'kg'
          and ((rec.get('code') or {}).get('coding') or [{}])[0].get('code') == 'hive-weight'
          and rec.get('effectiveDateTime') == '2026-07-12', r.out[-1200:])
    write(hp, keep)

    # ---- TRANSLATE: today's clause, placement and own rows written in these forms, every value placed
    OLD = os.path.join(T, 'old')
    TODAY = grow.today(os.path.join(T, 'today'))            # a garden in today's words grows from v0.49.0
    r = run(PY, os.path.join(TODAY, 'seed', 'germinate.py'), OLD, '--gardener', 'sam', cwd=T)
    old_vocab = text('VOCAB.md', OLD)
    head_, sep, rest = old_vocab.partition('\n---\n')
    head_ = '\n'.join(ln for ln in head_.split('\n') if not ln.startswith(('registry_additions:', 'registry_files:')))
    write('VOCAB.md', head_ + """
registry_additions:
  anchor_systems:
    - { system: apiary-site, dimension: place, complement: [stated, bearer], levels: [ { level: site } ], neighbours: counted, meaning: "the co-op's sites", pattern: '^apiary:[A-Z]+(-[0-9]+)?$', form_note: "`apiary:<code>`", example: "apiary:EAST-1", establishes: false, why: "a site says roughly where" }
registry_files:
  - { registry: apiary-sites, file: extracts/apiary-sites.tsv, key: code }
""" + sep + rest, OLD)
    write('beans/lease.md', """---
bean: lease
kind: contract
status: active
title: "lease — the shed"
summary: "Sam rents the shed."
parties:
  tenant: { who: { bean: sam }, role: tenant, accepted: 2026-09-01 }
clauses:
  rent: { what: "pay the month's rent", by: tenant, due: 2026-10-15, every: { of: time, in: gregorian-civil, each: month, at: "15", times: 6 }, notice: { count: 10, unit: day }, amount: { count: "300", unit: XTS } }
provenance: { source: asserted-by-human, by: sam, as_of: 2026-09-01 }
---
The lease.
""", OLD)
    write('beans/hive-1.md', """---
bean: hive-1
kind: host
status: active
title: "hive-1"
summary: "A hive at a site."
located_at:
  - { system: apiary-site, at: "apiary:EAST-1", openness: elsewhere, u: { count: 30, unit: metre } }
provenance: { source: asserted-by-human, by: sam, as_of: 2026-09-01 }
---
A hive.
""", OLD)
    write('extracts/apiary-sites.tsv', SITES, OLD)
    for c in (('git', 'add', '-A'), ('git', 'commit', '-qm', 'the old words', '--no-verify')):
        run(*c, cwd=OLD)
    NEW = os.path.join(T, 'new')
    r = run(PY, os.path.join(ROOT, 'core', 'translate.py'), 'garden', OLD, NEW, cwd=ROOT)
    lease = text('beans/lease.md', NEW) if os.path.isfile(os.path.join(NEW, 'beans', 'lease.md')) else ''
    hive = text('beans/hive-1.md', NEW) if os.path.isfile(os.path.join(NEW, 'beans', 'hive-1.md')) else ''
    vocab = read.document(os.path.join(NEW, 'VOCAB.md'))[0] if os.path.isfile(os.path.join(NEW, 'VOCAB.md')) else {}
    check("translate: every value placed, nothing to say", r.returncode == 0 and '0 problem(s)' in r.out, r.out[-800:])
    check("translate: a clause is `can` — its words, whom it binds; its due, recurrence, notice and amount its form",
          "due: '2026-10-15'" in lease and "clause:" in lease and "each: month" in lease and "unit: d" in lease
          and "times: '6'" in lease, lease)
    check("translate: a placement is `be` as location — how far it reaches and how well it is known in `placed`",
          "placed: {openness: elsewhere, u: {count: '30', unit: m}}" in hive, hive)
    check("translate: the garden's own system and its file are the core's rows `systems` and `files`",
          [s.get('system') for s in vocab.get('systems') or []] == ['apiary-site']
          and [f.get('registry') for f in vocab.get('files') or []] == ['apiary-sites'], vocab)
except Exception as e:
    import traceback
    traceback.print_exc()
    FAILS.append(f"the suite raised {type(e).__name__}: {e}")
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_measure: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
