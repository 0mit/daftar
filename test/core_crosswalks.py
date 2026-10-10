#!/usr/bin/env python3
"""The crosswalks (core/law/crosswalks.yaml, P5.3): a foreign system's records read from a garden's statements.

A garden grown from this tree keeps a company (an organisation its gardener represents), two departments under it and
one under another organisation, which is no company of the garden's. Odoo 17's `res.company` and `hr.department` are
read through core/crosswalk.py, the one reader: what each record says, how one record points at another, and that
nothing the garden does not say is in a record. Then the law refuses crosswalks that break their form.

Run: python3 test/core_crosswalks.py   (0 = green)
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
sys.path.insert(0, ROOT)
import grow  # noqa: E402
from core import crosswalk  # noqa: E402
from core.law import Law  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1200:]))
    if not cond:
        FAILS.append(name)


def write(g, rel, text):
    p = os.path.join(g, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def org(bid, title, *statements):
    return (f'---\nbean: {bid}\nkind: org\ntitle: "{title}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
            + ''.join(f'  - {s}\n' for s in statements) + f'---\n{title}.\n')


T = tempfile.mkdtemp(prefix='core-crosswalk-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'beans/acme.md', org('acme', 'Acme', 'represent: { by: sam, of: self, as: "keeps its garden" }',
                                  'name: { by: dns, of: self, as: acme.example }'))
    write(G, 'beans/eng.md', org('eng', 'Engineering', 'part: { by: self, of: acme }'))
    write(G, 'beans/qa.md', org('qa', 'Quality', 'part: { by: self, of: eng }'))
    write(G, 'beans/supplier.md', org('supplier', 'A supplier'))
    write(G, 'beans/supplier-sales.md', org('supplier-sales', "The supplier's sales", 'part: { by: self, of: supplier }'))
    r = grow.run(PY, 'bin/save.py', 'sam', 'a company, its departments, and a supplier', '--body',
                 '- action: [[acme]], [[eng]], [[qa]], [[supplier]], [[supplier-sales]]', cwd=G)
    check("...its company, two departments and a supplier pass its gate", r.returncode == 0, r.out[-900:])

    R = crosswalk.Reader(G, 'odoo', '17.0')
    co = R.records('res.company')
    check("res.company: the one organisation the gardener represents, never the supplier, with its name and website",
          [c['name'] for c in co] == ['Acme'] and co[0]['website'] == 'acme.example' and co[0]['email'] is False
          and co[0]['parent_id'] is False and co[0]['child_ids'] == [] and co[0]['active'] is True, co)
    deps = {d['name']: d for d in R.records('hr.department')}
    acme = [co[0]['id'], 'Acme']
    check("hr.department: the organisations under the company, through part … of, and none under the supplier",
          sorted(deps) == ['Engineering', 'Quality'], sorted(deps))
    eng, qa = deps.get('Engineering', {}), deps.get('Quality', {})
    check("...each in its company, and a department's parent is a department, never the company",
          eng.get('company_id') == acme and qa.get('company_id') == acme and eng.get('parent_id') is False
          and qa.get('parent_id') == [eng.get('id'), 'Engineering'], (eng, qa))
    check("...its complete name the titles down from the farthest department, and its children read backwards",
          qa.get('complete_name') == 'Engineering / Quality' and eng.get('complete_name') == 'Engineering'
          and eng.get('child_ids') == [qa.get('id')], (eng, qa))
    check("...the same bean is the same record number every time, and different beans differ",
          crosswalk.number('hr.department', 'eng') == eng.get('id') != qa.get('id')
          and crosswalk.Reader(G, 'odoo', '17.0').records('hr.department', beans={'qa'})[0]['id'] == qa.get('id'))
    try:
        R.records('hr.employee')
        check("a model the law does not cross is refused, never guessed", False)
    except crosswalk.Refused as e:
        check("a model the law does not cross is refused, never guessed", 'no crosswalk of hr.employee' in str(e), e)

    L = Law.load(('VOCAB.md', {}))
    kept = dict(L.crosswalks)
    bad = dict(kept['odoo-17.0-hr.department'], kind='department', select={'within': {'along': 'part.over', 'model': 'res.partner'}},
               fields={'name': {'from': 'tittle'}, 'parent_id': {'from': 'part.of', 'inverse': True},
                       'complete_name': {'from': 'title', 'join': ' / '}, 'x': {'from': 'title', 'value': 1}})
    L.crosswalks['odoo-17.0-hr.department'] = bad
    probs = [m for _w, m in L.crosswalk_problems()]
    L.crosswalks.clear(); L.crosswalks.update(kept)
    check("the law refuses a crosswalk out of form: a kind it lacks, a path of no role, a model nothing crosses, a "
          "misspelt field, `inverse` without a model, `join` without `along`, a field both read and given",
          any('no kind of the law' in m for m in probs) and any('no role of part' in m for m in probs)
          and any("'res.partner'" in m for m in probs) and any("'tittle' is no path" in m for m in probs)
          and any('`inverse` and `chain`' in m for m in probs) and any('`join` and `along`' in m for m in probs)
          and any('never both' in m for m in probs), probs)
    check("...and the law as it stands passes", not L.crosswalk_problems(), L.crosswalk_problems())
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_crosswalks: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
