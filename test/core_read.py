#!/usr/bin/env python3
"""The read tools in a garden of the core (v1 part 6): garden, where, stale, pos, seq, reckon, ledger — and the forms of
a line they read: a series (`record`), a walk (`step`), a course (`be` as order) and its moves (`move`), a reading
(`reckon`) and a pin (`pin`), judged by the core's rule `line`.

Builds what it needs, as test/core_write.py does: a release of the core made from this tree (v1.0.0), and a GARDEN grown
from it, holding a rain gauge that records a series, a walk of a bicycle repair, the repair itself (a course along the
walk, its moves, what was paid and who bears it, a clause, a reading and a pin), and a laptop that holds a root and a
codebase under it.

law: core/law/lines.yaml is what std-vocab generates, and the law holds together with its rules. gate: the
garden saved through the core's gate; each form's breach refused by rule `line`, by name. seq: the series read between
its rows, the course where it stands. reckon: a reading by its name, an ad-hoc one over `pay.of`, a comparator in today's
words refused, a reading at a pinned commit. ledger: positions and debts from `pay` and `bear`, exactly, and the net
between two. garden, where, stale, pos: the garden's law, a `root:` location resolved here, a cache's verdict, the
position index's named scans. cursor: a file under a root resolves to its bean (part 5 left it). The aliases run the
same tools. translate: today's series, walk, course, moves and reading written in statements, every value placed.

Run: python3 test/core_read.py   (0 = green; about a minute)
"""
import os, re, shutil, socket, subprocess, sys, tempfile

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
ME = socket.gethostname().lower().split('.')[0]


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None, stdin=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x')
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e,
                            input=stdin))


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


def head():
    return run('git', 'rev-parse', 'HEAD').out.strip()


def save(what, body):
    return run(PY, 'bin/save.py', 'sam', what, '--body', body)


def refused(path, old, new, says):
    """The gate's verdict on the bean at `path` with `old` written as `new`: (refused by rule `line` saying `says`,
    output); the bean put back."""
    keep = text(path)
    assert old in keep, old
    write(path, keep.replace(old, new, 1))
    r = run(PY, 'bin/check.py')
    write(path, keep)
    return r.returncode != 0 and any(ln.startswith('line') and says in ln for ln in r.out.split('\n')), r.out[-900:]


T = tempfile.mkdtemp(prefix='core-read-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden')

VOCAB = """---
kinds:
  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }
namespaces:
  - { namespace: anchor-hostname, meaning: "what a machine calls itself" }
---
# garden — the garden's own rows
"""

ALI = """---
bean: ali
kind: person
title: "Ali"
summary: "Ali mends bicycles."
statements:
  - say:    { by: ali, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Ali, who keeps her own garden and agreed to be written here by name.
"""

GAUGE = """---
bean: rain-gauge
kind: host
title: "rain-gauge — the rain gauge on the balcony"
summary: "A small logging rain gauge; it reads the rain of each hour, and its battery."
statements:
  - read: { by: sam, at: now }
  - own:  { by: sam, of: self }
  - record:
      id: september
      of: self
      series:
        grid: { of: time, in: gregorian-civil, every: { count: "1", unit: h }, from: "2026-09-14 06:00+02:00" }
        unit: h
        placement: following
        holds:
          - { name: rain, quantity: length, unit: mm, stands_for: sum, u: { count: "0.2", unit: mm } }
          - { name: battery, quantity: ratio, unit: "%", stands_for: point, between: linear }
        rows: |
          rain	battery
          0	84
          1.4	84
          3.2	83
          -	-
          0.6	81
      note: "the fourth hour was not read: the logger was off while its battery was changed"
---
The balcony's rain gauge.
"""

WALK = """---
bean: walk-bike-repair
kind: procedure
title: "walk-bike-repair — how a bicycle repair goes"
summary: "How a bicycle repair goes, each time: handed over, looked at, mended, collected."
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "the owner brings the bicycle", by: owner, to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", by: repairer, to: [mended, given-up], walk: { usually: { of: time, measure: { count: "2", unit: d } }, ways: [ { to: given-up, when: "it is not worth mending" } ] } }
  - step: { id: waiting-for-part, as: "a part is ordered, and the repair waits for it", walk: { resumes: "true", reasons: [part-ordered] } }
  - step: { id: mended, as: "it is mended and ridden round the block", by: repairer, to: [collected] }
  - step: { id: collected, as: "the owner takes it home", by: owner, walk: { final: "true" } }
  - step: { id: given-up, as: "the repair is abandoned", walk: { exit: "true", reasons: [not-worth-it] } }
---
The steps of a bicycle repair.
"""

REPAIR = """---
bean: bike-repair
kind: contract
title: "bike-repair — Ali mends Sam's bicycle"
summary: "Ali repairs Sam's bicycle; Sam pays for the parts, and a third of the tool they bought for it."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - answer: { by: ali, of: self, as: law }
  - agree:  { by: sam, of: "Sam's bicycle", through: spoken, as: owner }
  - agree:  { by: ali, of: "Sam's bicycle", through: spoken, as: repairer }
  - be:     { id: repair, by: self, at: walk-bike-repair, as: order }
  - move:   { by: sam, of: self, through: repair, at: ["2026-09-20 10:00+03:00", "walk-bike-repair#handed-over"] }
  - move:   { by: ali, of: self, through: repair, at: ["2026-09-21 11:00+03:00", "walk-bike-repair#looked-at"], why: "the rear hub grinds" }
  - move:   { by: ali, of: self, through: repair, at: [now, "walk-bike-repair#waiting-for-part"], as: part-ordered }
  - pay:    { id: parts, by: sam, of: { count: "30", unit: EUR }, to: ali, at: "2026-09-21" }
  - pay:    { id: tool, by: ali, of: { count: "90", unit: EUR }, at: "2026-09-22", note: "a hub tool" }
  - bear:   { by: ali, of: tool, share: "2" }
  - bear:   { by: sam, of: tool, share: "1" }
  - can:    { id: mend, by: ali, of: "mend the bicycle" }
  - obligatory: { of: mend, through: bike-repair }
  - reckon:
      id: waiting
      reading:
        what: "the repairs waiting for a part"
        steps:
          - { id: repairs, op: select, kind: contract, where: [ { path: move, at_step: "walk-bike-repair#waiting-for-part" } ] }
          - { id: how-many, op: count, of: repairs }
  - pin:    { by: sam, of: [parts], from: [waiting], at: [now, "garden@COMMIT"] }
---
Ali mends Sam's bicycle; the parts are Sam's to pay for.
"""

LAPTOP = """---
bean: laptop
kind: host
title: "laptop — the machine this runs on"
statements:
  - read: { by: sam, at: now }
  - own:  { by: sam, of: self }
  - name: { by: anchor-hostname, of: self, as: %s }
  - can:  { id: sends-mail, by: self, of: smtp }
  - forbidden: { of: sends-mail, through: sam, why: "the provider blocks port 25" }
  - possible: { of: sends-mail }
details:
  roots:
    src: { system: unix-filesystem, at: "%s:%s" }
---
The laptop.
"""

APP = """---
bean: app
kind: codebase
title: "app — the shop's code"
statements:
  - say: { by: sam, at: now }
  - own: { by: sam, of: self }
  - be:  { id: tree, by: self, at: "unix-filesystem:root:src/app", as: location }
details:
  located_at:
    tree: { role: own-source, scan_policy: index }
  analysis_cache:
    structure: { as_of: "2026-10-01", staleness_key: "manual: read by a person", policy: index }
---
The shop's code.
"""

try:
    # ---- THE RELEASE: v1.0.0, a release of the core made from this tree, and a garden grown from it
    grow.release(REL)
    r = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam', cwd=T)
    check(f"a garden grows from v1.0.0 in the core (core@{VERSION}), the read tools in it",
          r.returncode == 0 and f'core@{VERSION}' in text('GARDEN.md')
          and all(os.path.isfile(os.path.join(G, 'bin', f"{v}.py")) and not os.path.exists(os.path.join(G, 'bin', f"dm{v}.py"))
                  for v in ('garden', 'where', 'stale', 'pos', 'seq', 'reckon', 'ledger')), r.out[-800:])
    run(PY, 'bin/install.py')

    # ---- THE LAW: its rules
    r = run(PY, 'core/check.py', '--law')
    check("law: the core's law holds together — its new verbs (record, step, reckon, pin, move) and rule `line`",
          r.returncode == 0 and '21 rules — 0 error(s)' in r.out, r.out[-400:])

    # ---- THE GATE: the five forms saved through the core's gate
    write('VOCAB.md', VOCAB)
    for p, t in (('beans/ali.md', ALI), ('beans/rain-gauge.md', GAUGE), ('mappings/walk-bike-repair.md', WALK),
                 ('beans/laptop.md', LAPTOP % (ME, ME, os.path.join(T, 'src'))), ('beans/app.md', APP),
                 ('beans/bike-repair.md', REPAIR.replace('COMMIT', head()[:10]))):
        write(p, t)
    os.makedirs(os.path.join(T, 'src', 'app'))
    write('src/app/main.py', 'print("shop")\n', T)
    r = save('RULE-CHANGE: a walk is a procedure; a series, a walk, a course, a reading and a pin',
             '- action: RULE-CHANGE — VOCAB.md adds the kind procedure and the namespace anchor-hostname; wrote [[ali]], '
             '[[rain-gauge]], [[walk-bike-repair]], [[bike-repair]], [[laptop]] and [[app]]')
    check("gate: a series, a walk, a course with its moves, a reading and a pin are saved through the core's gate",
          r.returncode == 0 and clean(), r.out[-1500:])
    rp = 'beans/bike-repair.md'
    for name, path, old, new, says in (
            ("a move the walk does not offer, with no why", rp, '"walk-bike-repair#looked-at"], why: "the rear hub grinds"',
             '"walk-bike-repair#mended"]', "a move the walk does not offer"),
            ("a reason the step does not list", rp, 'as: part-ordered', 'as: lost-key', "which is not one of the step"),
            ("a move through no course", rp, 'through: repair, at: ["2026-09-21', 'through: elsewhere, at: ["2026-09-21',
             "is no course of this bean"),
            ("a reading's comparator in today's words", rp, 'at_step: "walk-bike-repair#waiting-for-part"', 'is: x',
             "is written by its sign in the core"),
            ("a reading's path in today's words", rp, '{ path: move, at_step', '{ path: moves, at_step',
             "reads today's words"),
            ("a pin to a commit the garden does not have", rp, ', "garden@', ', "garden@0000000',
             "is not an ancestor of HEAD"),
            ("a way on to no step of the walk", 'mappings/walk-bike-repair.md', 'to: [collected]',
             'to: [collected, nowhere]', "no step of this walk"),
            ("an attribute no step holds", 'mappings/walk-bike-repair.md', 'final: "true"', 'final: "true", colour: red',
             "is no attribute of it"),
            ("a series' row with a cell its channels do not hold", 'beans/rain-gauge.md', '0.6\t81', '0.6\t81\t7',
             "holds 3 cell(s)"),
            ("a series placed in no way the law knows", 'beans/rain-gauge.md', 'placement: following',
             'placement: sideways', "is not one of point")):
        ok, out = refused(path, old, new, says)
        check(f"gate: rule `line` refuses {name}", ok, out)

    # ---- SEQ: the series and the course
    r = run(PY, 'bin/seq.py', 'at', 'rain-gauge', 'september', '2026-09-14 07:30+02:00')
    check("seq: a series of the core read between rows — the battery on the line, the rain the sum over its hour",
          r.returncode == 0 and 'battery: 83.5 %' in r.out and 'rain: 1.4 mm — over the row' in r.out, r.out)
    r = run(PY, 'bin/seq.py', 'show', 'rain-gauge', 'september')
    check("seq: `show` prints each row at its moment, a gap as a gap, its unit by name",
          r.returncode == 0 and 'counted in hours' in r.out and '2026-09-14 09:00+02:00' in r.out
          and 'no reading was made' in r.out, r.out[:600])
    r = run(PY, 'bin/seq.py', 'course', 'bike-repair')
    check("seq: where the course stands is read from its moves: the step, and how many moves",
          r.returncode == 0 and "course repair on walk walk-bike-repair — at 'waiting-for-part'" in r.out
          and '3 move(s)' in r.out, r.out)
    r = run(PY, 'bin/seq.py', 'check')
    check("seq: `check` is the core's rule `line`, over every bean", r.returncode == 0 and '0 error(s)' in r.out, r.out)
    a, b = run(PY, 'bin/seq.py', 'course', 'bike-repair'), run(PY, 'bin/seq.py', 'course', 'bike-repair')
    check("seq: today's name, bin/seq.py, runs the same tool", a.out == b.out and b.returncode == 0, b.out)

    # ---- RECKON: a reading by its name, ad hoc, refused in today's words, at a pin
    r = run(PY, 'bin/reckon.py', 'bike-repair#waiting')
    check("reckon: a `reckon` statement read by its name — the repairs whose course is at a step of the walk",
          r.returncode == 0 and '= 1 item' in r.out and 'bike-repair' in r.out, r.out)
    write('sum.yaml', 'what: "what Sam paid"\nsteps:\n  - { id: pays, op: select, kind: contract, entries: pay, '
                      'where: [ { path: by, "=": sam } ] }\n  - { id: total, op: sum, of: pays, path: of }\n', T)
    r = run(PY, 'bin/reckon.py', '--ad-hoc', os.path.join(T, 'sum.yaml'))
    check("reckon: a path over statements — `pay.of` of each `pay` Sam made — summed exactly",
          r.returncode == 0 and '= 30 EUR' in r.out, r.out)
    write('old.yaml', text('sum.yaml', T).replace('"=": sam', 'is: sam'), T)
    r = run(PY, 'bin/reckon.py', '--ad-hoc', os.path.join(T, 'old.yaml'))
    check("reckon: a comparator in today's words is refused, naming the core's sign",
          r.returncode != 0 and 'written by its sign in the core: `=`' in r.out, r.out)
    write('ne.yaml', text('sum.yaml', T).replace('"=": sam', '"≠": sam'), T)
    r = run(PY, 'bin/reckon.py', '--ad-hoc', os.path.join(T, 'ne.yaml'))
    check("reckon: `≠`, a sign today's words lacked, is read", r.returncode == 0 and '= 90 EUR' in r.out, r.out)
    pinned = head()
    write('beans/bike-repair.md', text('beans/bike-repair.md').replace(
        '  - pay:    { id: tool,', '  - move:   { id: mended, by: ali, of: self, through: repair, '
                                   'at: [now, "walk-bike-repair#looked-at"] }\n'
                                   '  - say:    { by: ali, of: [mended], at: now }\n'
                                   '  - pay:    { id: tool,'))
    r = save('the bicycle is mended', '- action: [[bike-repair]] moved to mended')
    now = run(PY, 'bin/reckon.py', 'bike-repair#waiting')
    then = run(PY, 'bin/reckon.py', 'bike-repair#waiting', '--at', pinned, '--moment', '2026-10-01T12:00Z')
    check("reckon: read at a pinned commit, a reading gives what the garden held then (1), and now what it holds (0)",
          r.returncode == 0 and '= 0 item' in now.out and '= 1 item' in then.out, now.out + then.out + r.out[-400:])

    # ---- LEDGER: pay and bear
    r = run(PY, 'bin/ledger.py', 'bike-repair')
    check("ledger: what each paid less what each bears, per currency, exactly — and who owes whom",
          r.returncode == 0 and 'ali +30 EUR · sam -30 EUR' in r.out and 'sam owes ali 30 EUR' in r.out
          and 'borne by ali 60 EUR, sam 30 EUR' in r.out, r.out)
    check("ledger: a clause is its `can` and the figure it stands under", 'mend  obligatory: ali' in r.out, r.out)
    r = run(PY, 'bin/ledger.py', '--between', 'sam', 'ali')
    check("ledger: --between nets the two across the agreements they share (today's name, the same tool)",
          r.returncode == 0 and 'net, across 1 agreement' in r.out and 'sam owes ali 30 EUR' in r.out, r.out)

    # ---- GARDEN, WHERE, STALE, POS, CURSOR
    r = run(PY, 'bin/garden.py')
    check("garden: says it is a garden of the core, and what it holds", r.returncode == 0
          and f'the core, core@{VERSION}' in r.out and 'statements' in r.out, r.out)
    r = run(PY, 'bin/where.py', 'app')
    check("where: a `root:` location of the core resolved through this host's roots (kept in `details`): HERE",
          r.returncode == 0 and 'HERE' in r.out and os.path.join(T, 'src', 'app') in r.out, r.out)
    r = run(PY, 'bin/stale.py')
    check("stale: a cache `details` keeps is given its verdict (a key no machine can check: unknown)",
          'app.analysis_cache[structure]' in r.out and '1 unknown' in r.out, r.out)
    r = run(PY, 'bin/pos.py', '--verify')
    check("pos: the position index of the core — a statement a figure takes a stance on; the live risk found",
          r.returncode == 0 and re.search(r'1\s+LIVE RISK', r.out) is not None, r.out)
    r = run(PY, 'bin/cursor.py', os.path.join(T, 'src', 'app', 'main.py'))
    check("cursor: a file under a root resolves to the bean whose location covers it (part 5 left this to `where`)",
          r.returncode == 0 and 'cursor -> app' in r.out and 'resolved from a FILE' in r.out, r.out[:600])

    # ---- TRANSLATE: today's words of the forms, written in statements, every value placed
    O = os.path.join(T, 'old')
    for d in ('beans', 'mappings'):
        os.makedirs(os.path.join(O, d))
    run('git', 'init', '-q', cwd=O)
    write('GARDEN.md', "---\ngarden: old\nextends: std-vocab@32.1\ngardener: sam\nzone: Europe/Istanbul\n---\nx\n", O)
    write('mappings/walk.md', """---
mapping: walk
kind: procedure
title: "walk"
steps:
  - { id: asked, do: "asked", by: owner, next: [ { to: done, when: "yes" }, { to: dropped } ] }
  - { id: done, do: "done", final: true }
  - { id: dropped, do: "dropped", exit: true, reasons: [no-time] }
---
x
""", O)
    write('beans/case.md', """---
bean: case
genos: contract
title: "case"
courses:
  c: { walk: { mapping: walk } }
moves:
  - { course: c, at: "2026-09-20 10:00+03:00", step: asked, by: sam }
selections:
  open:
    what: "the open cases"
    steps:
      - { id: s, op: select, genos: contract, where: [ { path: genos, is: contract } ] }
series:
  temp:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: hour }, from: "2026-09-14 06:00+02:00" }
    unit: hour
    holds:
      - { name: t, quantity: temperature, unit: kelvin, stands_for: point }
    rows: |
      t
      290
---
x
""", O)
    from core import translate as TR, law as LAW, standards  # noqa: E402
    ctx = TR.Context(O, LAW.Law.load(), standards.here())
    got = {}
    for p in ('mappings/walk.md', 'beans/case.md'):
        t_, b_ = TR.translate_bean(os.path.join(O, p), p, ctx)
        got[p] = (t_, TR.verify(b_, t_))
    w, c = got['mappings/walk.md'][0], got['beans/case.md'][0]
    check("translate: every value of today's walk, course, moves, reading and series is placed (the count holds)",
          not got['mappings/walk.md'][1] and not got['beans/case.md'][1], [g[1] for g in got.values()])
    check("translate: a step is a `step` — `do` its `as`, `next` its `to`, a way's words in `walk.ways` — and a "
          "bean that said nobody knew it says so",
          "- step: {id: asked, as: asked, by: owner, to: [done, dropped], walk: {ways: [{to: done, when: 'yes'}]}}" in w
          and "final: 'true'" in w and 'say: {by: unknown' in w, w)
    check("translate: a course is `be` as order on the walk, a move reaches `<walk>#<step>` through it",
          "- be: {id: c, by: self, at: walk, as: order}" in c
          and "- move: {of: self, through: c, at: ['2026-09-20 10:00+03:00', walk#asked], by: sam}" in c, c)
    check("translate: a reading is `reckon` — `genos` its `kind`, a comparator by its sign — and a series `record`, "
          "its units UCUM's", "kind: contract, where: [{path: kind, '=': contract}]" in c and '- record:' in c
          and 'unit: h' in c and 'unit: K' in c, c)
except Exception as e:
    import traceback
    traceback.print_exc()
    FAILS.append(f"the suite raised {type(e).__name__}: {e}")
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_read: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
