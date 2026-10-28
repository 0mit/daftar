#!/usr/bin/env python3
"""Courses: every course of a being in one shape, the one way a course is drawn (core 2.22, the archetype `course`).

Grows a garden of the core and writes in it: a bicycle repair placed on a walk and moved along it; a loan repaid in six
monthly instalments, the first settled by a payment and the second past its day; a UPS whose standing need — its
runtime on battery — a reading meets, crossed by a probe (a `fail` through a `measure`, no `repair`); and a task whose
needs are one blocking and one not (`contingent` of it), one of an amount, one met. Then bin/seq.py `courses` reads
each in the one shape the archetype draws: the source, the steps in their order, the step it stands at, since when,
overdue, and the needs with their strength; a written course read as `where` reads it; nothing stored.

Run: python3 test/courses.py   (0 = green)
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def write(g, rel, text):
    p = os.path.join(g, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


READ = r'''
import json, sys
sys.path[:0] = ['bin', '.']
import seq
out = {b: seq.courses('.', b, now=sys.argv[1]) for b in sys.argv[2:]}
print(json.dumps(out, default=str))
'''

T = tempfile.mkdtemp(prefix='core-courses-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'beans/ali.md', '---\nbean: ali\nkind: person\ntitle: "ali"\nstatements:\n'
                             '  - say: { by: ali, at: now }\n  - own: { by: theone, of: self }\n---\nAli.\n')
    write(G, 'mappings/walk-repair.md', '''---
bean: walk-repair
kind: procedure
title: "walk-repair — how a bicycle repair goes"
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "the owner brings the bicycle", by: owner, to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", by: repairer, to: [mended], walk: { usually: { of: time, measure: { count: "2", unit: d } } } }
  - step: { id: mended, as: "it is mended", by: repairer, to: [collected] }
  - step: { id: collected, as: "the owner takes it home", by: owner, walk: { final: "true" } }
  - step: { id: dropped, as: "nobody goes on with it", walk: { exit: "true", final: "true" } }
---
The steps of a repair.
''')
    write(G, 'beans/repair-1.md', '''---
bean: repair-1
kind: contract
title: "repair-1 — a bicycle repaired"
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - answer: { by: ali, of: self, as: law }
  - agree:  { by: sam, of: "the bicycle", through: spoken, as: repairer }
  - agree:  { by: ali, of: "the bicycle", through: spoken, as: owner }
  - be:     { id: repair, by: self, at: walk-repair, as: order }
  - move:   { by: ali, of: self, through: repair, at: ["2026-10-01T10:00:00+03:00", "walk-repair#handed-over"] }
  - move:   { by: sam, of: self, through: repair, at: ["2026-10-01T11:00:00+03:00", "walk-repair#looked-at"] }
---
A repair.
''')
    write(G, 'beans/washer-loan.md', '''---
bean: washer-loan
kind: contract
title: "washer-loan — Sam lent Ali the price of a washing machine, repaid monthly"
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - answer:     { by: ali, of: self, as: law }
  - agree:      { by: sam, of: "the price of Ali's washing machine", through: spoken, as: lender }
  - agree:      { by: ali, of: "the price of Ali's washing machine", through: spoken, as: borrower }
  - pay:        { id: instalment, by: ali, to: sam, of: { count: "20.00", unit: XTS } }
  - obligatory: { id: instalments, of: instalment, through: self, clause: { due: "2026-08-01", every: { of: time, in: gregorian-civil, each: month, at: "1", times: "6" } } }
  - pay:        { id: first, by: ali, to: sam, of: { count: "20.00", unit: XTS }, at: "2026-08-01", settles: [ { clause: instalments, occurrence: "1" } ] }
  - pay:        { id: the-loan, by: sam, of: { count: "120.00", unit: XTS } }
  - bear:       { by: ali, of: the-loan, share: "1" }
---
Agreed in words.
''')
    write(G, 'beans/cash-loan.md', '''---
bean: cash-loan
kind: contract
title: "cash-loan — Ali lent Sam cash, and no day or terms were said"
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - agree:      { by: ali, of: "a cash loan", through: spoken, as: lender }
  - agree:      { by: sam, of: "a cash loan", through: spoken, as: borrower }
  - pay:        { id: lent, by: ali, of: { count: "80.00", unit: XTS } }
  - bear:       { by: sam, of: lent, share: "1" }
  - pay:        { id: back, by: sam, of: { count: "30.00", unit: XTS } }
  - bear:       { by: ali, of: back, share: "1" }
---
Ali lent Sam cash; Sam has paid some of it back.
''')
    write(G, 'beans/ups-1.md', '''---
bean: ups-1
kind: host
title: "ups-1 — the office's UPS"
statements:
  - say:     { by: sam, at: now }
  - own:     { by: sam, of: self }
  - need:    { id: runtime, by: self, of: "at least ten minutes on battery at the office's load" }
  - reckon:  { id: runtime-read, reading: { what: "at least ten minutes left on battery, as the probe last read them", inputs: [ { name: ups-minutes, origin: { act: read, nature: soma, by: ups-tool }, quantity: duration } ], steps: [ { id: ten, op: constant, value: { count: "10", unit: min } }, { id: ok, op: compare, of: ups-minutes, with: ten, is: at-least } ] } }
  - meet:    { by: runtime-read, of: runtime }
  - measure: { id: runtime-2026101012-minutes, by: sam, of: self, as: number, value: { count: "4", unit: min }, at: "2026-10-10T12:00:00+03:00" }
  - fail:    { id: runtime-2026101012, by: self, as: "at least ten minutes on battery: does not hold", through: runtime-2026101012-minutes, at: "2026-10-10T12:00:00+03:00" }
---
The UPS.
''')
    write(G, 'beans/battery-change.md', '''---
bean: battery-change
kind: design
title: "battery-change — the UPS's batteries replaced"
statements:
  - say:        { by: sam, at: now }
  - own:        { by: sam, of: self }
  - need:       { id: batteries, by: self, of: "four 12 V batteries", from: ali }
  - need:       { id: a-window, by: self, of: "an hour with the office's load off" }
  - contingent: { of: a-window }
  - meet:       { id: delivered, by: ali, of: batteries }
  - say:        { by: ali, of: [delivered], at: now }
  - need:       { id: price, by: self, of: { count: "4000", unit: XTS }, from: ali }
  - repair:     { id: fixes, by: self, of: "ups-1#runtime-2026101012" }
  - fail:       { id: load-drop, by: ups-1, as: "the load dropped during the swap", through: battery-change }
  - possible:   { of: load-drop }
  - weigh:      { id: weights, by: sam, to: "the UPS's options", weighing: { criteria: [ { name: feasibility, what: "it can be done" }, { name: efficiency, what: "it yields more than it costs" }, { name: necessity, what: "something needs it now" } ], pairwise: [ { a: necessity, b: feasibility, judged: "3" }, { a: necessity, b: efficiency, judged: "3" }, { a: feasibility, b: efficiency, judged: "1" } ] } }
  - reckon:     { id: options, reading: { what: "the UPS's options read on the three axes", steps: [ { id: m, op: select, kind: design }, { id: ax, op: axes, of: m, weighing: weights } ] } }
---
A task.
''')
    write(G, 'beans/battery-change-later.md', '''---
bean: battery-change-later
kind: design
title: "battery-change-later — the same, next year"
statements:
  - say:        { by: sam, at: now }
  - own:        { by: sam, of: self }
  - need:       { id: a-window, by: self, of: "a weekend with the office closed" }
  - need:       { id: price, by: self, of: { count: "4400", unit: XTS }, from: ali }
---
Another option.
''')
    ups = open(os.path.join(G, 'beans/ups-1.md'), encoding='utf-8').read()
    write(G, 'beans/ups-1.md', ups.replace('---\nThe UPS.', '  - need:    { id: renewed, by: self, of: [battery-change] }\n'
                                           '  - need:    { id: later, by: self, of: [battery-change-later], while: runtime-read }\n---\nThe UPS.'))
    g = subprocess.run([PY, 'core/check.py'], cwd=G, capture_output=True, text=True, encoding='utf-8', errors='replace')
    check("...and every bean of it passes the gate as written", g.returncode == 0, (g.stdout + g.stderr)[-1500:])
    j = None
    p = subprocess.run([PY, '-c', READ, '2026-10-20T12:00:00+03:00', 'repair-1', 'washer-loan', 'ups-1', 'battery-change', 'cash-loan'],
                       cwd=G, capture_output=True, text=True, encoding='utf-8', errors='replace')
    try:
        j = json.loads(p.stdout)
    except ValueError:
        pass
    check("courses: read for every being asked, writing nothing", j is not None, (p.stdout[-800:], p.stderr[-1500:]))
    j = j or {}
    rep = (j.get('repair-1') or [{}])[0]
    check("a written course: its walk's steps in their order, the step it stands at, who acts there, and overdue past "
          "the step's `usually` — as `where` reads it",
          rep.get('source') == 'course' and rep.get('walk') == 'walk-repair' and rep.get('step') == 'looked-at'
          and [s['id'] for s in rep.get('steps') or []] == ['handed-over', 'looked-at', 'mended', 'collected', 'dropped']
          and rep.get('by') == 'repairer' and rep.get('party') == 'sam' and rep.get('overdue') is True
          and any(s.get('exit') and s.get('final') for s in rep['steps']), rep)
    loan = j.get('washer-loan') or []
    steps = [(c.get('id'), c.get('step'), c.get('overdue')) for c in loan]
    check("a clause's occurrences read as courses: the first met by the payment that settles it, the others due from "
          "their day — past it overdue — and the one after today ahead, never written",
          steps[:4] == [('instalments:1', 'met', False), ('instalments:2', 'due', True), ('instalments:3', 'due', True),
                        ('instalments:4', 'ahead', False)] and len(loan) == 4
          and all(c.get('source') == 'clause' for c in loan) and loan[0].get('due') == '2026-08-01', steps)
    debt = j.get('cash-loan') or []
    check("a debt the ledger reads that no clause asks, read as a course: open at `owed`, by its debtor, what is owed "
          "netted, no day said; and a loan whose clauses ask its payments has none of its own",
          [(c.get('source'), c.get('id'), c.get('step'), c.get('by'), c.get('final'), c.get('overdue')) for c in debt]
          == [('debt', 'debt:sam:ali:XTS', 'owed', 'sam', False, None)]
          and [s['id'] for s in debt[0]['steps']] == ['owed', 'settled'] and '50' in str(debt[0].get('words'))
          and 'no day' in str(debt[0].get('words')) and not [c for c in loan if c.get('source') == 'debt'], debt)
    ups = j.get('ups-1') or []
    check("a standing need a reading meets, read as a course: crossed since the `fail` through a `measure` of it that "
          "no `repair` answers, with what failed in words",
          len(ups) == 1 and ups[0].get('source') == 'need' and ups[0].get('step') == 'crossed'
          and 'does not hold' in str(ups[0].get('words')), ups)
    write(G, 'beans/ups-1.md', open(os.path.join(G, 'beans/ups-1.md'), encoding='utf-8').read().replace(
        '---\nThe UPS.', '  - repair:  { by: sam, of: runtime-2026101012 }\n---\nThe UPS.'))
    p = subprocess.run([PY, '-c', READ, '2026-10-20T12:00:00+03:00', 'ups-1'], cwd=G, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    ups = (json.loads(p.stdout) if p.returncode == 0 else {}).get('ups-1') or []
    check("...and holding again once a `repair` answers the failure", len(ups) == 1 and ups[0].get('step') == 'holds',
          (ups, p.stderr[-600:]))
    task = (j.get('battery-change') or [])
    check("needs alone are no course: a being with needs and no walk, clause or standing need has none",
          all(c.get('source') != 'course' for c in task), task)
    r = subprocess.run([PY, 'bin/reckon.py', 'battery-change:options'], cwd=G, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    out = r.stdout + r.stderr
    check("axes: each option on feasibility, efficiency and necessity with its evidence — the change feasible (its "
          "blocking needs met or with a provider), needed now (the UPS's need of it, unmet), its cost its price over one "
          "more than the risk it makes possible; the later one half feasible (a window nobody provides) and needed by "
          "nothing known now (a need of it under a reading not read needs nothing yet) — weighed by the judge: the "
          "change `optimum here, now`, the later one `wasteful weight`",
          r.returncode == 0 and 'battery-change: feasibility 1, efficiency 0.5 (yield 1 × cost 0.5), necessity 1' in out
          and 'battery-change-later: feasibility 0.5, efficiency 5/11 (yield 0.5 × cost 10/11), necessity 0' in out and 'necessity 0' in out
          and 'optimum here, now' in out and 'wasteful weight' in out and '4000 XTS' in out
          and "'needed by, not read': ['ups-1#later']" in out, out[-2500:])
    import importlib
    sys.path[:0] = [os.path.join(G, 'bin'), G]
    seq = importlib.import_module('seq')
    from core import engine
    b = engine.Garden.read(G).beans['battery-change']
    needs = {n['id']: n for n in seq.needs_of(list(b.items))}
    check("a need's strength is its position on the necessity square: unmarked it blocks; `contingent` of it, it does "
          "not; met where a `meet` of it stands",
          needs.get('batteries', {}).get('blocking') is True and needs['batteries'].get('met') is True
          and needs.get('a-window', {}).get('blocking') is False and needs['a-window'].get('met') is False, needs)

    # ---- the one drawing: a table's `stands` column and a drawing of a being's courses, in a browser, right to left
    import html, re
    browser = next((x for x in ('chromium', 'chromium-browser', 'google-chrome') if shutil.which(x)), None)
    if not browser:
        print("NOTE  the courses were not drawn in a browser: none on this machine")
    else:
        LIB = os.path.join(ROOT, 'assets', 'view', 'lib')
        sys.path.insert(0, LIB)
        import view_widgets
        js = view_widgets.bundle() + ''.join(open(os.path.join(LIB, f), encoding='utf-8').read() for f in (
            os.path.join('widgets', 'direction.js'), 'view_engraved.js', 'view_course.js', 'view_table.js'))
        E = {'settings': {'garden': {'lang': 'fa'}},
             'drawings': {'t': {'columns': [{'path': 'title', 'label': 'نام'}, {'stands': 'walk-repair', 'label': 'کجا'}],
                                'rows': [{'bean': 'repair-1', 'title': 'تعمیر', 'cells': ['تعمیر', {'course': rep}]},
                                         {'bean': 'washer-loan', 'title': 'وام', 'cells': ['وام', {'course': None}]}]},
                          'c': {'bean': 'washer-loan', 'courses': loan}}}
        page = """<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>%(css)s</style></head>
<body><div id="t" class="vw light" dir="rtl"></div><div id="c" class="vw light" dir="rtl"></div><script>%(js)s</script><script>
const out = {errs: []}, E = %(payload)s;
window.addEventListener('error', e => out.errs.push(String(e.message)));
try {
  const t = window.daftarEngraved.tools({engraved: E}), el = document.getElementById('t'), ec = document.getElementById('c');
  window.daftarArchetypes.table(el, E.drawings.t, t, null);
  window.daftarArchetypes.course(ec, E.drawings.c, t, null);
  const row = el.querySelector('tbody tr[data-bean="repair-1"]');
  out.here = [...row.querySelectorAll('[aria-current="step"]')].map(x => x.textContent.trim());
  out.on = [...row.querySelectorAll('.eg-steps:not(.eg-steps-off) .eg-step')].map(x => x.textContent.trim());
  out.off = [...row.querySelectorAll('.eg-steps-off .eg-step')].map(x => x.textContent.trim());
  out.late = !!row.querySelector('.eg-course.eg-late');
  out.none = !!el.querySelector('tbody tr[data-bean="washer-loan"] .w-none');
  out.lines = [...ec.querySelectorAll('.eg-course')].map(x => [x.dataset.course, x.dataset.step, x.classList.contains('eg-late')]);
  out.rtl = getComputedStyle(row.querySelector('.eg-steps')).direction;
} catch (e) { out.errs.push('driver: ' + e.message + ' ' + (e.stack || '').split('\\n')[1]); }
const pre = document.createElement('pre'); pre.id = '__out'; pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
</script></body></html>"""
        path = os.path.join(T, 'courses.html')
        with open(path, 'w', encoding='utf-8') as fh:
            fh.write(page % {'css': view_widgets.css() + open(os.path.join(LIB, 'view_engraved.css'), encoding='utf-8').read(),
                             'js': js, 'payload': json.dumps(E, ensure_ascii=False, default=str)})
        r = subprocess.run([browser, '--headless=new', '--disable-gpu', '--no-sandbox', '--virtual-time-budget=5000',
                            '--dump-dom', 'file://' + path], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=180, env=dict(os.environ, TMPDIR=T))
        m = re.search(r'<pre id="__out">(.*?)</pre>', r.stdout, re.S)
        B = json.loads(html.unescape(m.group(1))) if m else {'errs': ['no result: ' + r.stderr[-600:]]}
        check("drawn: a table's `stands` column draws each line's course by the archetype `course` — its steps in their "
              "order, the one it stands at marked, the ways out apart, overdue marked; a line on no course an empty cell",
              not B['errs'] and B.get('here') == ['looked-at'] and B.get('on') == ['handed-over', 'looked-at', 'mended', 'collected']
              and B.get('off') == ['dropped'] and B.get('late') is True and B.get('none') is True, B)
        check("...and a drawing of a being's courses draws each the same way: the instalments, met, due and overdue, "
              "ahead, along a right-to-left reader's line",
              [x[:2] for x in B.get('lines') or []] == [['instalments:1', 'met'], ['instalments:2', 'due'],
                                                        ['instalments:3', 'due'], ['instalments:4', 'ahead']]
              and [x[2] for x in B['lines']] == [False, True, True, False] and B.get('rtl') == 'rtl', B)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncourses: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
