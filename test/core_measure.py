#!/usr/bin/env python3
"""The measure tools in a garden of the core (v1 part 7): cal, geo, units, knowledge, crosswalk — and the forms of a
measure they read: a clause's terms (`can`'s `clause`: a recurrence, a notice, a due relative to a position, an
allowance), a placement's (`be`'s `placed`: what it takes of its host, how well its position is known), a quantity's
uncertainty, and a garden's own systems, schemes and files (VOCAB.md `systems`, `schemes`, `files`), judged by the core's
rule `measured`.

Builds what it needs, as test/core_read.py does: a release of the core made from this tree (v1.0.0), and a GARDEN grown
from it, keeping two hives at sites of its own apiary system and a lease paid each month, a rack that holds two slots and
a machine in one of them.

law: core/law/measures.yaml is what std-vocab generates, each unit's factor std-vocab's, the law whole with its twenty
rules. gate: the garden saved through the core's gate; each form's breach refused by rule `measured`, by name. units: a
conversion by UCUM code and by the English name, exactly. cal: a day in another calendar. geo: a distance on the body the
core's places name. knowledge: a code of the garden's own scheme, and a bean's codes from its statements. stale and
ledger: a clause's recurrence and notice read from its form. where: a position in the garden's own system. crosswalk: a
FHIR observation carried to a `measure` and back. translate: today's clause, placement and own rows written in these
forms, every value placed.

Run: python3 test/core_measure.py   (0 = green; about a minute)
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read  # noqa: E402
import dmparse, dmpass  # noqa: E402

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
kinds:
  - { kind: hive, nature: body, level: population, meaning: "a colony of bees, and the box it lives in" }
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
    law = dmparse.loads(dmparse.split_front_matter(text('seed/std-vocab.md', ROOT))[0])
    os.makedirs(REL)
    for f in dmpass.kept([f for f in dmpass.tracked(ROOT) if os.path.isfile(os.path.join(ROOT, f))],
                         dmpass.language(text('seed/LANGUAGE', ROOT)), dmpass.offered(law)):
        os.makedirs(os.path.join(REL, os.path.dirname(f)), exist_ok=True)
        shutil.copy2(os.path.join(ROOT, f), os.path.join(REL, f))
    for f in ('GARDEN.md.template', 'VOCAB.md.template'):
        shutil.copy2(os.path.join(ROOT, 'core', 'guide', f), os.path.join(REL, 'seed', f))
    for c in (('git', 'init', '-q'), ('git', 'add', '-A'), ('git', 'commit', '-qm', 'the core'), ('git', 'tag', 'v1.0.0')):
        run(*c, cwd=REL)
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam', cwd=T)
    check(f"a garden grows from v1.0.0 in the core (core@{VERSION}), the measure tools in it",
          r.returncode == 0 and f'core@{VERSION}' in text('GARDEN.md')
          and all(os.path.isfile(os.path.join(G, 'bin', f"{v}.py")) and os.path.isfile(os.path.join(G, 'bin', f"dm{v}.py"))
                  for v in ('cal', 'geo', 'units', 'knowledge', 'crosswalk')), r.out[-800:])
    run(PY, 'bin/install.py')

    # ---- THE LAW: measures.yaml generated from std-vocab; each unit's factor std-vocab's; twenty rules
    gen = run(PY, 'core/translate.py', 'measures', cwd=ROOT)
    check("law: core/law/measures.yaml is what std-vocab generates (its lines, extent, recurrence, uncertainty, forms)",
          gen.returncode == 0 and gen.out == text('core/law/measures.yaml', ROOT), gen.out[:300])
    old = {u['unit']: u.get('factor') for u in law.get('units') or []}
    rows = read.data(os.path.join(ROOT, 'core', 'law', 'units.yaml'))['units']
    differ = [r['unit'] for r in rows if [int(x) for x in r.get('factor') or []] != old.get(r['name'])]
    check(f"law: each of the core's {len(rows)} units in UCUM carries std-vocab's factor, exactly", not differ, differ)
    r = run(PY, 'core/check.py', '--law')
    check("law: the core's law holds together — the forms of a measure and rule `measured`",
          r.returncode == 0 and '20 rules — 0 error(s)' in r.out, r.out[-400:])

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

    # ---- THE TOOLS
    r = run(PY, 'bin/units.py', '90', 'km/h', 'm/s')
    r2 = run(PY, 'bin/dmunits.py', '90', 'kilometre-per-hour', 'metre-per-second')
    check("units: 90 km/h is 25 m/s exactly — by the UCUM codes, and by the English names through the alias",
          r.returncode == 0 and r.out.startswith('25 m/s') and r2.returncode == 0 and r2.out.startswith('25 '),
          r.out + r2.out)
    r = run(PY, 'bin/units.py', '1', 'h', 'kg')
    check("units: an hour is no mass, refused", r.returncode == 1 and 'nothing converts' in r.out, r.out)
    r = run(PY, 'bin/cal.py', '2026-09-20', 'persian')
    check("cal: 2026-09-20 is persian:1405-06-29", r.returncode == 0 and '1405-06-29' in r.out, r.out)
    r = run(PY, 'bin/geo.py', 'EPSG:4326;35.6892,51.3890', 'EPSG:4326;41.0082,28.9784')
    check("geo: a distance on the body the core's places name (Tehran to Istanbul, about 2,000 km)",
          r.returncode == 0 and 'km' in r.out and 'earth' in r.out.lower(), r.out[-600:])
    r = run(PY, 'bin/knowledge.py', 'show', 'hive-checks', 'varroa-drop')
    check("knowledge: a code of the garden's own scheme (`schemes`, its file in `files`)",
          r.returncode == 0 and 'mites fallen' in r.out, r.out[-600:])
    r = run(PY, 'bin/dmknowledge.py', 'bean', 'hive-1')
    check("knowledge: a bean's codes are its statements — `classify` — read through the alias",
          r.returncode == 0 and 'queen-seen' in r.out and 'classified_as' in r.out, r.out[-600:])
    r = run(PY, 'bin/ledger.py', 'lease')
    check("ledger: a clause's recurrence, notice and amount are read from its form",
          r.returncode == 0 and 'rent' in r.out and 'month' in r.out and '300' in r.out, r.out[-1200:])
    r = run(PY, 'bin/stale.py', '--days', '4000')
    check("stale: a clause that repeats is warned about before its next occurrence, read from its form",
          'lease' in r.out and 'rent' in r.out, r.out[-1200:])
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
    r = run(PY, os.path.join(ROOT, 'seed', 'germinate.py'), OLD, '--gardener', 'sam', cwd=ROOT)
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
