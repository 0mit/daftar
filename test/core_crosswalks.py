#!/usr/bin/env python3
"""The crosswalks (core/law/crosswalks.yaml, P5.3): a foreign system's records read from a garden's statements.

A garden grown from this tree keeps a company (an organisation its gardener represents), two departments under it and
one under another organisation, which is no company of the garden's. Odoo 17's `res.company` and `hr.department` are
read through core/crosswalk.py, the one reader: what each record says, how one record points at another, and that
nothing the garden does not say is in a record. Then `hr.employee`: a person employed by two of the garden's companies
and once by the supplier, each employment a record, read through paths that run through beans; her identity number and
private mail sealed in this host's store, read only where the host resolves them, never from git. Then the law refuses
crosswalks that break their form.

Run: python3 test/core_crosswalks.py   (0 = green)
"""
import os
import shutil
import socket
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
        R.records('hr.job')
        check("a model the law does not cross is refused, never guessed", False)
    except crosswalk.Refused as e:
        check("a model the law does not cross is refused, never guessed", 'no crosswalk of hr.job' in str(e), e)

    # ---- hr.employee: an employment agreement, and the person who agreed to it as employee
    HOST = socket.gethostname().lower()
    write(G, 'VOCAB.md', '---\nnamespaces:\n  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own '
          'name for itself" }\n---\n# the garden\'s own rows\n')
    write(G, 'beans/laptop.md', f'---\nbean: laptop\nkind: host\ntitle: "laptop — the machine this garden is kept on"\n'
          f'statements:\n  - read: {{ by: sam, at: now }}\n  - own: {{ by: sam, of: self }}\n'
          f'  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}\ndetails:\n  roots:\n'
          f'    vault: {{ system: unix-filesystem, at: "{HOST}:{T}/vault", keeps: special-category, readable_from: this-host }}\n'
          f'---\nThe laptop.\n')
    write(G, 'beans/beta.md', org('beta', 'Betamax', 'represent: { by: sam, of: self, as: "keeps its books" }'))
    write(G, 'beans/lale.md', '---\nbean: lale\nkind: person\ntitle: "Lale Demir"\nstatements:\n  - say: { by: sam, at: now }\n'
          '  - own: { by: theone, of: self }\n  - answer: { by: self, of: self, as: law }\n'
          '  - name: { by: mail, of: self, as: "lale@acme.example" }\n  - name: { by: e164, of: self, as: "+15555550147" }\n'
          '  - name: { id: tckn, by: tr-tckn, of: self, as: "10000000146" }\n'
          '  - name: { id: home-mail, by: mail, of: self, as: "lale@home.example" }\n---\nLale.\n')

    def employment(bid, employer, title, job, dept=None):
        return (f'---\nbean: {bid}\nkind: contract\ntitle: "{title}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
                f'  - own: {{ by: theone, of: self }}\n  - answer: {{ by: {employer}, of: self, as: law }}\n'
                f'  - answer: {{ by: lale, of: self, as: law }}\n'
                f'  - agree: {{ by: {employer}, of: self, through: written, as: employer, at: 2026-03-01 }}\n'
                f'  - agree: {{ id: employed, by: lale, of: self, through: written, as: employee, at: 2026-03-01 }}\n'
                f'  - represent: {{ by: lale, of: {employer}, as: "{job}" }}\n'
                + (f'  - part: {{ by: self, of: {dept} }}\n' if dept else '') + '---\nHer employment.\n')
    write(G, 'beans/lale-acme.md', employment('lale-acme', 'acme', 'Lale works for Acme', 'tester', 'qa'))
    write(G, 'beans/lale-beta.md', employment('lale-beta', 'beta', 'Lale works for Betamax on Fridays', 'bookkeeper'))
    write(G, 'beans/lale-supplier.md', employment('lale-supplier', 'supplier', "Lale once worked for the supplier", 'packer'))
    for sid in ('tckn', 'home-mail'):
        r = grow.run(PY, 'bin/held.py', 'put', 'lale', sid, '--basis', 'lale-acme#employed', cwd=G)
        check(f"Lale's {sid} is sealed in this host's store", r.returncode == 0, r.out[-500:])
    r = grow.run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: Lale, employed by two of the companies and once by the supplier',
                 '--body', '- action: RULE-CHANGE — VOCAB.md names the namespace anchor-hostname; [[laptop]] keeps a vault; '
                 'wrote [[beta]], [[lale]], [[lale-acme]], [[lale-beta]] and [[lale-supplier]]', '- ratified_by: sam',
                 '- held: lale tckn added', '- held: lale home-mail added', cwd=G)
    check("...an employee, her employments and her sealed numbers pass the gate", r.returncode == 0, r.out[-1500:])
    git_text = grow.run('git', 'grep', '-I', '-e', '10000000146', '-e', 'lale@home.example', 'HEAD', cwd=G).out
    check("...and nothing of what is sealed is in git", git_text.strip() == '', git_text)

    import importlib
    sys.path.insert(0, os.path.join(G, 'bin'))
    held = importlib.import_module('held')

    def unseal(bean, verb, roles):          # the host's resolution of a sealed statement: what its store holds
        try:
            rec = held.resolve(roles['held'], root=G)
        except Exception:
            return None
        return dict(rec.get('entry') or {}) if rec.get('verb') == verb else None
    R = crosswalk.Reader(G, 'odoo', '17.0')
    emp = sorted(R.records('hr.employee'), key=lambda e: e['company_id'][1])
    check("hr.employee: each employment of one of the garden's companies is a record — two for Lale, none for the "
          "supplier's — named as she is, at her work mail and phone",
          [(e['name'], e['company_id'][1]) for e in emp] == [('Lale Demir', 'Acme'), ('Lale Demir', 'Betamax')]
          and all(e['work_email'] == 'lale@acme.example' and e['work_phone'] == '+15555550147' for e in emp), emp)
    a = emp[0] if emp else {}
    check("...her job title what she acts for the employer as, her department the one the employment is part of",
          a.get('job_title') == 'tester' and a.get('department_id') == [deps['Quality']['id'], 'Engineering / Quality']
          and emp[-1].get('department_id') is False, emp)
    check("...and what is held is not read from git: her identity number and private mail are empty to a reader that "
          "resolves no sealed statement", a.get('identification_id') is False and a.get('private_email') is False, a)
    U = crosswalk.Reader(G, 'odoo', '17.0', unseal=unseal).records('hr.employee', beans={'lale-acme'})
    check("...and read where the host resolves them, from its own store",
          U and U[0]['identification_id'] == '10000000146' and U[0]['private_email'] == 'lale@home.example'
          and U[0]['work_email'] == 'lale@acme.example', U)

    L = Law.load(('VOCAB.md', {}))
    kept = dict(L.crosswalks)
    bad = dict(kept['odoo-17.0-hr.department'], kind='department', select={'within': {'along': 'part.over', 'model': 'res.partner'}},
               fields={'name': {'from': 'tittle'}, 'parent_id': {'from': 'part.of', 'inverse': True},
                       'complete_name': {'from': 'title', 'join': ' / '}, 'x': {'from': 'title', 'value': 1}})
    L.crosswalks['odoo-17.0-hr.department'] = bad
    L.crosswalks['odoo-17.0-hr.employee'] = dict(kept['odoo-17.0-hr.employee'], fields={
        'name': {'from': 'name[by=mail].as/title'}, 'x': {'from': 'title', 'held': True},
        'y': {'from': 'part.of', 'model': 'hr.department', 'held': True}})
    probs = [m for _w, m in L.crosswalk_problems()]
    L.crosswalks.clear(); L.crosswalks.update(kept)
    check("the law refuses a crosswalk out of form: a kind it lacks, a path of no role, a model nothing crosses, a "
          "misspelt field, `inverse` without a model, `join` without `along`, a field both read and given",
          any('no kind of the law' in m for m in probs) and any('no role of part' in m for m in probs)
          and any("'res.partner'" in m for m in probs) and any("'tittle' is no path" in m for m in probs)
          and any('`inverse` and `chain`' in m for m in probs) and any('`join` and `along`' in m for m in probs)
          and any('never both' in m for m in probs)
          and any("reads no being, so no path goes on from it" in m for m in probs)
          and sum('a held field reads the role of a sealed statement' in m for m in probs) == 2, probs)
    check("...and the law as it stands passes", not L.crosswalk_problems(), L.crosswalk_problems())
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_crosswalks: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
