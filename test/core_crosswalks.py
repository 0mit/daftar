#!/usr/bin/env python3
"""The crosswalks (core/law/crosswalks.yaml, P5.3): a foreign system's records read from a garden's statements.

A garden grown from this tree keeps a company (an organisation its gardener represents), two departments under it and
one under another organisation, which is no company of the garden's. Odoo 17's `res.company` and `hr.department` are
read through core/crosswalk.py, the one reader: what each record says, how one record points at another, and that
nothing the garden does not say is in a record. Then `hr.employee`: a person employed by two of the garden's companies
and once by the supplier, each employment a record, read through paths that run through beans; her identity number and
private mail sealed in this host's store, read only where the host resolves them, never from git. Then `hr.leave`: her
absences over extents of days, one written in the Persian calendar, each using an employment's allowance and decided on
a walk. Then `hr.leave.type`: the kinds of time off her employers grant, each the terms a company owns and an allowance
of an employment holds, and each absence's type the one the allowance it uses holds — a path's step that names a
statement reaches that statement. Then the law refuses crosswalks that break their form.

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
                + (f'  - part: {{ by: self, of: {dept} }}\n' if dept else '')
                + '  - hold: { id: allowance, by: lale, of: { count: "20", unit: d } }\n---\nHer employment.\n')
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

    # ---- hr.leave: an absence over an extent of days, using an employment's allowance, decided on a walk
    write(G, 'VOCAB.md', '---\nnamespaces:\n  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for '
          'itself" }\n---\n# the garden\'s own rows\n')
    write(G, 'mappings/walk-leave.md', '---\nbean: walk-leave\nkind: procedure\ntitle: "walk-leave — how a leave is decided"\n'
          'statements:\n  - say: { by: sam, at: now }\n'
          '  - step: { id: asked, as: "the employee asks for the days", by: employee, to: [approved, refused] }\n'
          '  - step: { id: approved, as: "the employer approves them", by: employer, walk: { final: "true" } }\n'
          '  - step: { id: refused, as: "the employer refuses them", by: employer, walk: { exit: "true" } }\n---\nLeave.\n')

    def leave(bid, title, at, employment, *moves, allowance='allowance'):
        write(G, f'beans/{bid}.md', f'---\nbean: {bid}\nkind: event\ntitle: "{title}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
              f'  - own: {{ by: theone, of: self }}\n  - concern: {{ of: lale }}\n'
              f'  - be: {{ by: self, at: {at}, as: presence }}\n'
              f'  - use: {{ by: self, of: "{employment}#{allowance}" }}\n'
              + ('  - be: { id: decided, by: self, at: walk-leave, as: order }\n' if moves else '')
              + ''.join(f'  - move: {{ by: lale, of: self, through: decided, at: [now, "walk-leave#{m}"] }}\n' for m in moves)
              + '---\nLeave.\n')
    leave('summer', 'Summer', '2026-07-06/2026-07-17', 'lale-acme', 'asked', 'approved')
    leave('summer-persian', 'Summer, in the Persian calendar', 'persian:1405-04-15/1405-04-26', 'lale-acme', 'asked')
    leave('autumn', 'Autumn', '2026-10-05/2026-10-07', 'lale-beta', 'asked', 'refused')
    leave('winter', 'Winter', '2026-12-28/2027-01-02', 'lale-acme')
    leave('packing', 'Packing season', '2026-05-01/2026-05-03', 'lale-supplier', 'asked')
    r = grow.run(PY, 'bin/save.py', 'sam', "RULE-CHANGE: Lale's leaves, on the leave walk", '--body',
                 '- action: RULE-CHANGE — VOCAB.md names the kind procedure; wrote [[walk-leave]], [[summer]], '
                 '[[summer-persian]], [[autumn]], [[winter]] and [[packing]]', '- ratified_by: sam', cwd=G)
    check("...and her leaves, under her employments, on a walk, pass the gate", r.returncode == 0, r.out[-1500:])
    R = crosswalk.Reader(G, 'odoo', '17.0')
    lv = {x['name']: x for x in R.records('hr.leave')}
    acme_lale = [crosswalk.number('hr.employee', 'lale-acme'), 'Lale Demir']
    s_ = lv.get('Summer', {})
    check("hr.leave: each absence under an employment of the garden's companies — never the supplier's — its employee "
          "the employment, its department the employment's",
          sorted(lv) == ['Autumn', 'Summer', 'Summer, in the Persian calendar', 'Winter']
          and s_.get('employee_id') == acme_lale and s_.get('all_employee_ids') == [acme_lale[0]]
          and s_.get('department_id') == [deps['Quality']['id'], 'Engineering / Quality']
          and lv.get('Autumn', {}).get('department_id') is False, lv)
    import datetime
    from zoneinfo import ZoneInfo
    from core import read as core_read
    zone = ZoneInfo(str(core_read.document(os.path.join(G, 'GARDEN.md'))[0]['zone']))   # the garden's, whatever machine

    def utc(*t):
        return datetime.datetime(*t, tzinfo=zone).astimezone(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    check("...its days read from its extent: the first and last, how many, and its moments in the garden's zone, in UTC",
          s_.get('request_date_from') == '2026-07-06' and s_.get('request_date_to') == '2026-07-17'
          and s_.get('number_of_days') == 12 and s_.get('date_from') == utc(2026, 7, 6)
          and s_.get('date_to') == utc(2026, 7, 17, 23, 59, 59), (s_, utc(2026, 7, 6)))
    p_ = lv.get('Summer, in the Persian calendar', {})
    check("...in whatever calendar it was written: the same days written in the Persian calendar read the same",
          (p_.get('request_date_from'), p_.get('request_date_to'), p_.get('number_of_days')) == ('2026-07-06', '2026-07-17', 12), p_)
    check("...its state where its course stands on its walk: approved at a final step, refused at an exit, to approve at "
          "a step, to submit before its first move",
          [lv.get(n, {}).get('state') for n in ('Summer', 'Autumn', 'Summer, in the Persian calendar', 'Winter')]
          == ['validate', 'refuse', 'confirm', 'draft'], {n: x.get('state') for n, x in lv.items()})

    # ---- hr.leave.type: which allowance an absence uses. A kind of time off is the terms an employer gives, a document
    #      it owns; an employment holds an allowance of one (`hold … of`, its statement); an absence uses one of the
    #      employment's allowances by its id, and its type is what that allowance holds. Each employment's first
    #      allowance holds only an amount, so a path that read the employment's first `hold` would read no type at all
    def terms(bid, title, owner):
        write(G, f'beans/{bid}.md', f'---\nbean: {bid}\nkind: document\ntitle: "{title}"\nstatements:\n'
              f'  - say: {{ by: sam, at: now }}\n  - own: {{ by: {owner}, of: self }}\n---\n{title}.\n')
    terms('acme-paid', 'Paid time off', 'acme')
    terms('acme-sick', 'Sick time off', 'acme')
    terms('unpaid-leave', 'Unpaid leave', 'sam')                    # every company's: none of the garden's owns it
    terms('acme-handbook', "Acme's handbook", 'acme')               # a document of the company no allowance holds
    terms('supplier-paid', "The supplier's paid leave", 'supplier')  # held only under the supplier's employment

    def holds(employment, *allowances):
        p = os.path.join(G, 'beans', f'{employment}.md')
        with open(p, encoding='utf-8') as fh:
            text = fh.read()
        said = ', '.join(sid for sid, _of in allowances)
        write(G, f'beans/{employment}.md', text.replace('---\nHer employment.', ''.join(
            f'  - hold: {{ id: {sid}, by: lale, of: {of} }}\n' for sid, of in allowances)
            + f'  - say: {{ by: sam, of: [{said}], at: now }}\n---\nHer employment.'))
    holds('lale-acme', ('paid', 'acme-paid'), ('sick', 'acme-sick'))
    holds('lale-beta', ('unpaid', 'unpaid-leave'))
    holds('lale-supplier', ('paid', 'supplier-paid'))
    leave('flu', 'Flu', '2026-11-02/2026-11-04', 'lale-acme', 'asked', 'approved', allowance='sick')
    leave('spring', 'Spring', '2026-04-06/2026-04-10', 'lale-acme', 'asked', allowance='paid')
    leave('friday', 'A Friday off', '2026-10-16/2026-10-16', 'lale-beta', allowance='unpaid')
    r = grow.run(PY, 'bin/save.py', 'sam', "Lale's kinds of time off, her allowances of them, and absences under them",
                 '--body', '- action: wrote [[acme-paid]], [[acme-sick]], [[unpaid-leave]], [[acme-handbook]] and '
                 '[[supplier-paid]]; [[lale-acme]], [[lale-beta]] and [[lale-supplier]] hold allowances of them; wrote '
                 '[[flu]], [[spring]] and [[friday]]', cwd=G)
    check("...and the kinds of time off, the allowances that hold them and the absences taken under them pass the gate",
          r.returncode == 0, r.out[-1500:])
    R = crosswalk.Reader(G, 'odoo', '17.0')
    try:
        ty = {t['name']: t for t in R.records('hr.leave.type')}
    except crosswalk.Refused as e:
        ty = {'refused': str(e)}
    check("hr.leave.type: the kinds of time off the garden's companies grant — each a document an allowance of one of "
          "their employments holds; never one held only under the supplier's employment, nor one no allowance holds",
          sorted(ty) == ['Paid time off', 'Sick time off', 'Unpaid leave'], ty)
    paid, unpaid = ty.get('Paid time off', {}), ty.get('Unpaid leave', {})
    check("...its company the one of the garden's that owns its terms, none where none does, and its number the same "
          "for its bean every time",
          paid.get('company_id') == acme and ty.get('Sick time off', {}).get('company_id') == acme
          and unpaid.get('company_id') is False and paid.get('display_name') == 'Paid time off'
          and paid.get('active') is True and paid.get('id') == crosswalk.number('hr.leave.type', 'acme-paid'), ty)
    lv = {x['name']: x for x in R.records('hr.leave')}

    def type_of(bid, title):
        return [crosswalk.number('hr.leave.type', bid), title]
    check("hr.leave: an absence's type is what the allowance it uses holds — of an employment's three allowances, the "
          "one it names, never the employment's first",
          lv.get('Flu', {}).get('holiday_status_id') == type_of('acme-sick', 'Sick time off')
          and lv.get('Spring', {}).get('holiday_status_id') == type_of('acme-paid', 'Paid time off')
          and lv.get('A Friday off', {}).get('holiday_status_id') == type_of('unpaid-leave', 'Unpaid leave'),
          {n: x.get('holiday_status_id') for n, x in lv.items()})
    check("...an absence under an allowance that holds only an amount has no type: the garden names none",
          [lv.get(n, {}).get('holiday_status_id', 'unread') for n in ('Summer', 'Autumn', 'Winter')] == [False] * 3,
          {n: x.get('holiday_status_id', 'unread') for n, x in lv.items()})
    check("...and through the employment's other statements it reads the employment as before: its employee, its "
          "department",
          lv.get('Flu', {}).get('employee_id') == acme_lale
          and lv.get('Flu', {}).get('department_id') == [deps['Quality']['id'], 'Engineering / Quality']
          and lv.get('A Friday off', {}).get('department_id') is False, lv.get('Flu'))
    B = R.G.beans
    check("a path's step that names a statement (`<bean>#<id>`) reaches that statement: a next step of its verb reads "
          "it alone, one of another verb the bean it is in",
          crosswalk.follow(B['flu'], 'use.of/hold.of', B) == 'acme-sick'
          and crosswalk.follow(B['flu'], 'use.of/hold[by=sam].of', B) is None
          and crosswalk.follow(B['flu'], 'use.of/part.of', B) == 'qa'
          and crosswalk.follow(B['flu'], 'use.of/hold.of/title', B) == 'Sick time off',
          [crosswalk.follow(B['flu'], p, B) for p in ('use.of/hold.of', 'use.of/hold[by=sam].of', 'use.of/part.of',
                                                       'use.of/hold.of/title')])

    L = Law.load(('VOCAB.md', {}))
    kept = dict(L.crosswalks)
    bad = dict(kept['odoo-17.0-hr.department'], kind='department', select={'within': {'along': 'part.over', 'model': 'res.partner'}},
               fields={'name': {'from': 'tittle'}, 'parent_id': {'from': 'part.of', 'inverse': True},
                       'complete_name': {'from': 'title', 'join': ' / '}, 'x': {'from': 'title', 'value': 1}})
    L.crosswalks['odoo-17.0-hr.department'] = bad
    L.crosswalks['odoo-17.0-hr.employee'] = dict(kept['odoo-17.0-hr.employee'], fields={
        'name': {'from': 'name[by=mail].as/title'}, 'x': {'from': 'title', 'held': True},
        'y': {'from': 'part.of', 'model': 'hr.department', 'held': True}})
    L.crosswalks['odoo-17.0-hr.leave'] = dict(kept['odoo-17.0-hr.leave'], fields={
        'a': {'from': 'use.of', 'many': True}, 'b': {'from': 'be.at', 'position': 'week'},
        'c': {'stands': {'none': 'draft', 'later': 'x'}}})
    probs = [m for _w, m in L.crosswalk_problems()]
    L.crosswalks.clear(); L.crosswalks.update(kept)
    check("the law refuses a crosswalk out of form: a kind it lacks, a path of no role, a model nothing crosses, a "
          "misspelt field, `inverse` without a model, `join` without `along`, a field both read and given",
          any('no kind of the law' in m for m in probs) and any('no role of part' in m for m in probs)
          and any("'res.partner'" in m for m in probs) and any("'tittle' is no path" in m for m in probs)
          and any('`inverse` and `chain`' in m for m in probs) and any('`join` and `along`' in m for m in probs)
          and any('never both' in m for m in probs)
          and any("reads no being, so no path goes on from it" in m for m in probs)
          and sum('a held field reads the role of a sealed statement' in m for m in probs) == 2
          and any('`many` is true, with the `model`' in m for m in probs) and any('`position` is one of' in m for m in probs)
          and any('`stands` names' in m for m in probs), probs)
    check("...and the law as it stands passes", not L.crosswalk_problems(), L.crosswalk_problems())
    L.crosswalks['odoo-17.0-hr.leave.type'] = dict(
        kept.get('odoo-17.0-hr.leave.type') or kept['odoo-17.0-hr.department'], crosswalk='odoo-17.0-hr.leave.type',
        model='hr.leave.type', select={'reached': {'along': 'hold.over', 'model': 'res.partner'},
                                       'beside': {'along': 'hold.of', 'model': 'hr.employee'}})
    probs = [m for _w, m in L.crosswalk_problems()]
    L.crosswalks.clear(); L.crosswalks.update(kept)
    check("...and a select by what reaches the bean (`reached`) held to the form `within` is: a path of the law's "
          "verbs and roles, a model a row of its series crosses; a select by a key the form lacks refused",
          any("'hold.over': over is no role of hold" in m for m in probs)
          and any("select.reached names 'res.partner', which no crosswalk of its series crosses" in m for m in probs)
          and any('select.beside is none of with, without, within, reached' in m for m in probs), probs)

    # ---- A GARDEN'S OWN CROSSWALK: a row of its VOCAB.md in the core's form, read by the one reader beside the
    #      standard's; never a name nor a model the standard crosses; used by a bean of its kind, or vacant with its why
    PARTNER = ('crosswalks:\n'
               '  - crosswalk: odoo-17.0-res.partner\n    system: odoo\n    series: "17.0"\n    model: res.partner\n'
               '    kind: org\n    fields:\n      name: { from: title }\n      website: { from: "name[by=dns].as" }\n'
               '      is_company: { value: true }\n      parent_id: { from: part.of, model: res.partner }\n'
               '      company_ids: { from: part.of, model: res.company, many: true }\n'
               '    meaning: "an organisation as Odoo\'s partner: every organisation the garden keeps"\n')
    PRODUCT = ('  - crosswalk: odoo-17.0-product.template\n    system: odoo\n    series: "17.0"\n'
               '    model: product.template\n    kind: product\n    fields:\n      name: { from: title }\n'
               '    meaning: "a product the garden keeps, as Odoo\'s product"\n')
    with open(os.path.join(G, 'VOCAB.md'), encoding='utf-8') as fh:
        VOCAB = fh.read()
    write(G, 'VOCAB.md', VOCAB.replace('---\n', '---\n' + PARTNER, 1))
    r = grow.run(PY, 'bin/save.py', 'sam', "RULE-CHANGE: the garden's own crosswalk of Odoo's partners", '--body',
                 '- action: RULE-CHANGE — VOCAB.md adds the crosswalk odoo-17.0-res.partner\n- ratified_by: sam', cwd=G)
    check("a garden's VOCAB.md takes a crosswalk of its own, in the core's form, and the gate saves it",
          r.returncode == 0, r.out[-900:])
    orgs = sorted(b[:-3] for b in os.listdir(os.path.join(G, 'beans'))
                  if 'kind: org\n' in open(os.path.join(G, 'beans', b), encoding='utf-8').read())
    R = crosswalk.Reader(G, 'odoo', '17.0')
    try:
        pa = {p_['name']: p_ for p_ in R.records('res.partner')}
    except crosswalk.Refused as e:
        pa = {'refused': str(e)}
    acme_n = crosswalk.number('res.partner', 'acme')
    check("...read by the one reader beside the standard's: every organisation a partner, with what the garden says of "
          "it, pointing at a record of its own model and at one of the standard's",
          len(pa) == len(orgs) >= 5 and pa.get('Acme', {}).get('website') == 'acme.example'
          and pa.get('Acme', {}).get('is_company') is True and pa.get('Engineering', {}).get('parent_id') == [acme_n, 'Acme']
          and pa.get('Engineering', {}).get('company_ids') == [crosswalk.number('res.company', 'acme')]
          and sorted(c['name'] for c in R.records('res.company')) == ['Acme', 'Betamax'], (orgs, pa))
    std = Law.load()
    dept = dict(std.crosswalks['odoo-17.0-hr.department'])
    own = lambda *rows: Law.load(('VOCAB.md', {'crosswalks': list(rows)}))
    said = lambda L_: [m for _r, _w, m in L_.found] + [m for _w, m in L_.crosswalk_problems()]
    named, crossed = said(own(dept)), said(own(dict(dept, crosswalk='own-departments')))
    twice = said(own(dict(dept, crosswalk='a', model='x.one'), dict(dept, crosswalk='a', model='x.two'),
                     dict(dept, crosswalk='b', model='x.one')))
    out_of_form = said(own(dict(dept, crosswalk='c', model='x.three', kind='no-such-kind', colour='blue')))
    check("...and never a name the standard has, nor a model a row of its system and series crosses already, nor one "
          "of its own twice; and held to the core's form as the standard's rows are",
          any("`odoo-17.0-hr.department` is a crosswalk of the standard already" in m for m in named)
          and any("crosses hr.department of odoo 17.0, which odoo-17.0-hr.department crosses already" in m for m in crossed)
          and any("`a` is given twice" in m for m in twice) and any("crosses x.one of odoo 17.0, which a crosses" in m for m in twice)
          and any("its kind 'no-such-kind' is no kind of the law" in m for m in out_of_form)
          and any("`colour` is no key of a crosswalk" in m for m in out_of_form)
          and not said(own(dict(dept, crosswalk='d', model='x.four'))), (named, crossed, twice, out_of_form))
    products = [b for b in os.listdir(os.path.join(G, 'beans'))
                if 'kind: product\n' in open(os.path.join(G, 'beans', b), encoding='utf-8').read()]
    write(G, 'VOCAB.md', VOCAB.replace('---\n', '---\n' + PARTNER + PRODUCT, 1))
    g = grow.run(PY, 'core/check.py', cwd=G)
    write(G, 'VOCAB.md', VOCAB.replace('---\n', '---\n' + PARTNER + PRODUCT + '    vacant: "no product is kept here yet"\n', 1))
    g2 = grow.run(PY, 'core/check.py', cwd=G)
    write(G, 'VOCAB.md', VOCAB.replace('---\n', '---\n' + PARTNER, 1))
    check("...and used, by a bean of its kind, or vacant with its why: a crosswalk of products in a garden that keeps "
          "none is refused (vacancy) until it says why", not products and 'vacancy' in g.out
          and 'odoo-17.0-product.template' in g.out and g2.returncode == 0, (products, g.out[-700:], g2.out[-500:]))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_crosswalks: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
