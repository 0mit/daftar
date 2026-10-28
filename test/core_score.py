#!/usr/bin/env python3
"""core_score — a forecast scored against what came (core 4.7): a `possible` with a `chance` within an extent, what came
said on the same square, and the reading's operation `score` (core/law/lines.yaml), read each time and never stored.

Grows a garden of the core from a release made of this tree (test/grow.py) and writes in it a courier's estimates that
ten parcels come late, each a `possible` of a `fail` with a chance, and the receipts that say on the necessity square
what came: `necessary` of a parcel that came late, `impossible` of one that did not. Then reads the scores, whose values
are worked out by hand below:

  resolved   six: chances 0.9, 0.7 and 0.5 of parcels that came late, 0.7, 0.2 and 0.1 of parcels that did not
  brier      (0.01 + 0.09 + 0.25 + 0.49 + 0.04 + 0.01) / 6 = 0.89 / 6 = 89/600
  base rate  three of six came: 1/2; always saying it scores 1/2 × 1/2 = 1/4, so the skill is 1 − (89/600) / (1/4) = 61/150
  log        −(ln 0.9 + ln 0.7 + ln 0.5 + ln 0.3 + ln 0.8 + ln 0.9) / 6, and the base rate's ln 2
  bins       in two bins: 0.1 and 0.2 below 0.5, none came; 0.5, 0.7, 0.7 and 0.9 from 0.5, three came
  the rest   one whose extent has not ended (open), one ended with nothing said (due), one with both outcomes said
             (disputed), and one whose outcome only its own forecaster said (due, and named)

Beside them: a chance of 1 given against what came makes the log score unbounded, and names the forecast; a member with
no chance, and a number of bins that is no whole number, are refused; the gate passes the garden. Invented beings;
nothing here is a fact. (`python` on Windows.)

Run: python3 test/core_score.py   (0 = green)
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'test')]
import grow  # noqa: E402
from core import reckon  # noqa: E402

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


# parcel: (the estimate's chance that it comes late, the day its estimate ends, what came: 1, 0, 'both', 'own' or None)
PARCELS = {1: ('0.9', '2026-11-05', 1), 2: ('0.7', '2026-11-05', 1), 3: ('0.7', '2026-11-05', 0),
           4: ('0.2', '2026-11-05', 0), 5: ('0.1', '2026-11-05', 0), 6: ('0.5', '2026-11-05', 1),
           7: ('0.4', '2026-12-31', None), 8: ('0.6', '2026-11-20', None), 9: ('0.3', '2026-11-05', 'both'),
           10: ('0.8', '2026-11-05', 'own')}
NOW = '2026-12-01T00:00Z'

T = tempfile.mkdtemp(prefix='core-score-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'beans/shop.md', '---\nbean: shop\nkind: org\ntitle: "shop"\nstatements:\n  - say: { by: sam, at: now }\n'
                              '---\nA shop that sends parcels, invented.\n')
    write(G, 'beans/parcels.md', '---\nbean: parcels\nkind: document\ntitle: "parcels — ten parcels and their days"\n'
          'statements:\n  - say: { by: sam, at: now }\n'
          + ''.join(f'  - fail: {{ id: late-{n}, by: shop, as: "parcel {n} comes after its day" }}\n' for n in PARCELS)
          + '---\nTen parcels, each of which may come after its day.\n')
    write(G, 'beans/eta-model.md', '---\nbean: eta-model\nkind: model\ntitle: "eta-model — a courier\'s estimates"\n'
          'statements:\n  - say: { by: sam, at: now }\n'
          + ''.join(f'  - possible: {{ id: f{n}, of: "parcels#late-{n}", through: self, chance: "{c}", within: '
                    f'{{ of: time, from: "2026-11-01", to: "{end}" }} }}\n' for n, (c, end, _o) in PARCELS.items())
          + '  - reckon: { id: scores, reading: { what: "the estimates against what came", steps: [ { id: mine, op: '
            'select, kind: model, where: [ { path: bean, "=": eta-model } ] }, { id: forecasts, op: select, of: mine, '
            'entries: possible }, { id: score, op: score, of: forecasts } ] } }\n'
            '  - reckon: { id: halves, reading: { what: "the same, calibrated in two bins", steps: [ { id: mine, op: '
            'select, kind: model, where: [ { path: bean, "=": eta-model } ] }, { id: forecasts, op: select, of: mine, '
            'entries: possible }, { id: score, op: score, of: forecasts, bins: 2 } ] } }\n'
          + '---\nA model of when parcels come, invented: what it gives is derived through it.\n')
    said = {1: 'necessary', 0: 'impossible'}
    write(G, 'beans/receipts.md', '---\nbean: receipts\nkind: document\ntitle: "receipts — what came"\nstatements:\n'
          '  - say: { by: sam, at: now }\n'
          + ''.join(f'  - {said[o]}: {{ of: "parcels#late-{n}", through: self }}\n' for n, (_c, _e, o) in PARCELS.items()
                    if o in (0, 1))
          + '  - necessary: { of: "parcels#late-9", through: self }\n'
            '  - impossible: { of: "parcels#late-9", through: sam }\n'
            '  - necessary: { of: "parcels#late-10", through: eta-model }\n'
          + '---\nWhat came, as the receipts say.\n')
    write(G, 'beans/sure-model.md', '---\nbean: sure-model\nkind: model\ntitle: "sure-model — a model too sure"\n'
          'statements:\n  - say: { by: sam, at: now }\n'
          '  - possible: { id: s3, of: "parcels#late-3", through: self, chance: { count: "100", unit: "%" } }\n'
          '  - possible: { id: s1, of: "parcels#late-1", through: self, chance: "1" }\n'
          '  - reckon: { id: scores, reading: { what: "its estimates against what came", steps: [ { id: mine, op: '
          'select, kind: model, where: [ { path: bean, "=": sure-model } ] }, { id: forecasts, op: select, of: mine, '
          'entries: possible }, { id: score, op: score, of: forecasts } ] } }\n'
          '---\nA model that gives no doubt, invented.\n')
    write(G, 'beans/risks.md', '---\nbean: risks\nkind: document\ntitle: "risks — what may fail"\nstatements:\n'
          '  - say: { by: sam, at: now }\n  - possible: { of: "parcels#late-4" }\n---\nA possible with no degree.\n')
    g = subprocess.run([PY, 'core/check.py'], cwd=G, capture_output=True, text=True, encoding='utf-8', errors='replace')
    check("the gate passes the garden: each chance a ratio from 0 to 1, each `within` an extent, and what came said on "
          "the same square through another source than the estimate's own", g.returncode == 0 and '0 error(s)' in g.stdout,
          g.stdout[-1500:] + g.stderr[-600:])

    res = reckon.evaluate('eta-model:scores', root=G, now=NOW)
    v, text = res.value, '\n'.join(res.lines)

    def val(k):
        x = v.get(k) if isinstance(v, dict) else None
        return x.v if isinstance(x, reckon.V) else x
    check("the reading gives groups: six resolved, three came", res.kind == 'groups' and val('resolved') == 6
          and val('came') == 3, (res.kind, v))
    check("the Brier score: the mean of the squared differences, exactly 89/600", val('brier') == Fraction(89, 600),
          val('brier'))
    check("the base rate 1/2, always saying it scores 1/4, and the skill against it 61/150, exactly",
          val('base-rate') == Fraction(1, 2) and val('base-rate-brier') == Fraction(1, 4)
          and val('skill') == Fraction(61, 150), (val('base-rate'), val('base-rate-brier'), val('skill')))
    by_hand = -sum(math.log(x) for x in (0.9, 0.7, 0.5, 0.3, 0.8, 0.9)) / 6
    check("the log score: the mean of −ln of the chance given to what came, as by hand, and the base rate's ln 2",
          val('log') is not None and abs(float(val('log')) - by_hand) < 1e-12
          and abs(float(val('base-rate-log')) - math.log(2)) < 1e-12 and v['log'].approx,
          (val('log'), by_hand, val('base-rate-log')))
    check("the rest are named and not scored: open while its extent has not ended, due once it ended with nothing said, "
          "disputed where both were said",
          [m.id for m in v['open']] == ['eta-model:possible[f7]'] and [m.id for m in v['disputed']] == ['eta-model:possible[f9]']
          and sorted(m.id for m in v['due']) == ['eta-model:possible[f10]', 'eta-model:possible[f8]'], v)
    check("...and an outcome said through the estimate's own source is not read as what came, and is named",
          'receipts:necessary' in text and "said through the forecast's own source (self)" in text, text)
    check("calibration in ten bins: each bin with how many, their mean chance and how many came",
          'calibration 0.7 to 0.8: 2 forecast(s), mean chance 0.7, came 1 of 2' in text
          and 'calibration 0.9 to 1: 1 forecast(s), mean chance 0.9, came 1 of 1' in text
          and 'calibration 0.1 to 0.2: 1 forecast(s), mean chance 0.1, came 0 of 1' in text, text)
    h = reckon.evaluate('eta-model:halves', root=G, now=NOW)
    ht = '\n'.join(h.lines)
    check("...and in two: below one half none of two came, from one half three of four, the last bin holding 1",
          'calibration 0 to 0.5: 2 forecast(s), mean chance 0.15, came 0 of 2' in ht
          and 'calibration 0.5 to 1: 4 forecast(s), mean chance 0.7, came 3 of 4' in ht
          and h.value['brier'].v == Fraction(89, 600), ht)
    early = reckon.evaluate('eta-model:scores', root=G, now='2026-11-10T00:00Z')
    check("read before the eighth estimate's extent ended, it is open, not due: the moment read decides, and the scores "
          "rest on what was said", [m.id for m in early.value['due']] == ['eta-model:possible[f10]']
          and len(early.value['open']) == 2 and early.value['brier'].v == Fraction(89, 600), early.value)
    s = reckon.evaluate('sure-model:scores', root=G, now=NOW)
    st = '\n'.join(s.lines)
    check("a chance of 1 (100 %) given against what came makes the log score unbounded, naming the forecast; the Brier "
          "score stays (0 + 1) / 2",
          s.value['log'].v == 'unbounded'
          and 'log: unbounded — a chance of 0 or 1 given against what came: sure-model:possible[s3]\n' in st
          and s.value['brier'].v == Fraction(1, 2), (s.value, st))
    try:
        reckon.evaluate('x', root=G, now=NOW, bean='eta-model', entry={'steps': [
            {'id': 'all', 'op': 'select', 'entries': 'possible'}, {'id': 's', 'op': 'score', 'of': 'all'}]})
        refused = ''
    except reckon.Refused as e:
        refused = str(e)
    check("a member with no chance is refused, and nothing is scored: a forecast says how likely",
          'risks:possible' in refused and 'no `possible` with a `chance`' in refused, refused)
    try:
        reckon.evaluate('x', root=G, now=NOW, bean='eta-model', entry={'steps': [
            {'id': 'mine', 'op': 'select', 'kind': 'model', 'where': [{'path': 'bean', 'is': 'eta-model'}]},
            {'id': 'all', 'op': 'select', 'of': 'mine', 'entries': 'possible'},
            {'id': 's', 'op': 'score', 'of': 'all', 'bins': 0}]})
        refused = ''
    except reckon.Refused as e:
        refused = str(e)
    check("no bins is refused: `bins` is a whole number, one or more", '`bins` is a whole number' in refused, refused)
    probs = reckon.check_selection('x', {'steps': [{'id': 'all', 'op': 'select', 'entries': 'possible'},
                                                   {'id': 's', 'op': 'score', 'of': 'all', 'bins': 'many'}]},
                                   reckon.law())
    check("...and a reading whose bins are no count is refused by the grammar's check, which the gate calls",
          any('`bins:' in t and 'not a count' in t for _lv, t in probs), probs)
    def files():
        return {os.path.join(d, f): os.stat(os.path.join(d, f)).st_mtime_ns for d, ds, fs in os.walk(G)
                for f in fs if '.git' not in d.split(os.sep) and '__pycache__' not in d.split(os.sep)}
    before = files()
    c = subprocess.run([PY, 'bin/reckon.py', 'eta-model:scores'], cwd=G, capture_output=True, text=True,
                       encoding='utf-8', errors='replace')
    check("the garden's own reckoner reads it at the command line, read and never stored: no file of the garden "
          "written", c.returncode == 0 and 'brier: 89/600' in c.stdout and 'resolved: 6' in c.stdout
          and files() == before, c.stdout[-1500:] + c.stderr[-600:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_score: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
