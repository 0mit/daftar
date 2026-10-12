#!/usr/bin/env python3
"""What is in force (core/inforce.py), read once: a statement while it holds, a decision once its course stands at its
walk's final step, less what an ending statement ends, and, where asked, while its standing allows it — and the
crosswalks that read through it.

A garden grown from this tree keeps a workshop's people, two shares and two groups, all invented. Its decisions about
who may reach which share are placed on a walk: one decided, one decided later that revokes a grant of the first, one
only asked, one refused. Its people's accounts are names held while they arrived. Their groups are uses in their
employments, permitted through them, one forbidden through a decision. Their employments end by a withdrawal, one
with its day come and one with it still to come. The garden's own VOCAB.md rows say how a file server's records and an
ERP's users are read from all this: the rows of the two shapes the in-force reader was built for (a share's access, one
record per grant in force; a user, with the groups their uses in force open).

Then the reader asked directly: a `while` that holds, one that does not and one that cannot be read; the decisions in
force on the walk, in order, and with the request being planned; what ends what; a use's standing; and a walk tool's
policy. Then the law refuses `statements` forms out of form.

Run: python3 test/core_inforce.py   (0 = green)
"""
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
sys.path.insert(0, ROOT)
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


def bean(bid, kind, title, *statements, body='A bean.'):
    return (f'---\nbean: {bid}\nkind: {kind}\ntitle: "{title}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
            + ''.join(f'  - {s}\n' for s in statements) + f'---\n{body}\n')


VOCAB = '''---
kinds:
  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }
namespaces:
  - { namespace: erp-login, once: "true", pattern: "^[a-z][a-z.]{1,30}$", meaning: "a person's sign-in name in the workshop's ERP" }
  - { namespace: erp-group, once: "true", pattern: "^[a-z]+\\\\.[a-z]+$", meaning: "an ERP group, by its external id" }
verbs:
  - verb: revoke
    meaning: "to bring to an end, through a decision, what other statements hold: who revokes, which statements, through what"
    roles: { by: { shape: being }, of: { shape: statement, many: true }, through: { shape: [being, statement] }, at: { shape: position } }
    required: [of, through]
  - verb: withdraw
    meaning: "to end one's part in an agreement, or the agreement, from a day: who ends it, what it ends, the day"
    roles: { by: { shape: being }, of: { shape: [statement, being] }, at: { shape: position }, through: { shape: [being, text] } }
    required: [by, of, at]
crosswalks:
  - crosswalk: odoo-17.0-smb.share
    system: odoo
    series: "17.0"
    model: smb.share
    kind: service
    fields:
      name: { from: title }
    meaning: "a share of the workshop's file server"
  - crosswalk: odoo-17.0-smb.user
    system: odoo
    series: "17.0"
    model: smb.user
    kind: person
    select: { named_in: { verb: grant, with: "through=smb", naming: to, in_force_on: walk-shares, ended_by: revoke } }
    fields:
      name: { from: title }
    meaning: "a person a grant through smb in force reaches"
  - crosswalk: odoo-17.0-smb.access
    system: odoo
    series: "17.0"
    model: smb.access
    statements: { verb: grant, with: "through=smb", in_force_on: walk-shares, ended_by: revoke }
    fields:
      user_id: { from: to, model: smb.user }
      share_id: { from: of, model: smb.share }
      type: { from: as, map: { read: r, write: rw } }
    meaning: "who may reach which share: each grant through smb in force on the walk, one record each"
  - crosswalk: odoo-17.0-res.groups
    system: odoo
    series: "17.0"
    model: res.groups
    kind: service
    select: { with: "name[by=erp-group].as" }
    fields:
      name: { from: "name[by=erp-group].as" }
    meaning: "an ERP group the garden names"
  - crosswalk: odoo-17.0-res.users
    system: odoo
    series: "17.0"
    model: res.users
    kind: person
    select: { with: "name[by=erp-login].as" }
    fields:
      name: { from: title }
      login: { from: "name[by=erp-login].as" }
      groups_id: { statements: { verb: use, naming: by, standing: true }, from: of, model: res.groups, many: true }
      active: { statements: { verb: agree, with: "as=employee", naming: by, ended_by: withdraw }, exists: true }
    meaning: "a person's ERP user while their sign-in name holds: their groups, the uses in force; active while employed"
---
# the workshop's own rows
'''

WALK = bean('walk-shares', 'procedure', 'walk-shares — who may reach a share',
            'step: { id: asked, as: "someone asks", by: keeper, to: [decided, refused] }',
            'step: { id: decided, as: "the keeper decides", by: keeper, walk: { final: "true" } }',
            'step: { id: refused, as: "the keeper refuses", by: keeper, walk: { exit: "true" } }', body='How.')


def decision(bid, moves, *statements):
    return bean(bid, 'document', f'{bid} — who may reach a share', 'own: { by: sam, of: self }',
                'be: { id: run, by: self, at: walk-shares, as: order }',
                *[f'move: {{ by: sam, of: self, through: run, at: ["{at}", "walk-shares#{m}"] }}' for m, at in moves],
                *statements, body='A decision.')


def person(pid, *statements):
    return bean(pid, 'person', pid.capitalize(), 'own: { by: sam, of: self }', *statements, body='A person.')


def employment(bid, pid, *statements):
    return bean(bid, 'contract', f'{pid.capitalize()} works at the workshop', 'own: { by: sam, of: self }',
                f'agree: {{ by: workshop, of: self, through: written, as: employer, at: 2026-01-05 }}',
                f'agree: {{ id: employed, by: {pid}, of: self, through: written, as: employee, at: 2026-01-05 }}',
                *statements, body='An employment.')


def arrived(contract):
    return (f'reckon: {{ id: arrived, reading: {{ what: "the employment that says they arrived", steps: [ {{ id: p, '
            f'op: select, kind: contract, where: [ {{ path: bean, "=": {contract} }} ] }} ] }} }}')


T = tempfile.mkdtemp(prefix='core-inforce-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'VOCAB.md', VOCAB)
    write(G, 'mappings/walk-shares.md', WALK)
    write(G, 'beans/workshop.md', bean('workshop', 'org', 'The workshop', 'represent: { by: sam, of: self, as: "keeps it" }'))
    for sid, title in (('docs', 'Docs'), ('plans', 'Plans')):
        write(G, f'beans/{sid}.md', bean(sid, 'service', title, 'own: { by: workshop, of: self }', body='A share.'))
    for gid, ext in (('group-sales', 'sales.user'), ('group-plans', 'plans.user')):
        write(G, f'beans/{gid}.md', bean(gid, 'service', gid, 'own: { by: workshop, of: self }',
                                         f'name: {{ by: erp-group, of: self, as: {ext} }}', body='A group.'))
    write(G, 'beans/ada.md', person('ada', arrived('ada-work'),
                                    'name: { id: erp, by: erp-login, of: self, as: ada.l, while: arrived }'))
    write(G, 'beans/ben.md', person('ben', 'name: { id: erp, by: erp-login, of: self, as: ben.k }'))
    write(G, 'beans/cy.md', person('cy', 'name: { id: erp, by: erp-login, of: self, as: cy.m }'))
    write(G, 'beans/dee-offer.md', bean('dee-offer', 'contract', 'Dee is offered work at the workshop', 'own: { by: sam, of: self }',
                                        'agree: { by: workshop, of: self, through: written, as: employer, at: 2026-03-20 }',
                                        'agree: { by: dee, of: self, through: written, as: candidate, at: 2026-03-20 }',
                                        body='An offer.'))
    write(G, 'beans/dee.md', person('dee', arrived('dee-work'),
                                    'name: { id: erp, by: erp-login, of: self, as: dee.n, while: arrived }',
                                    'reckon: { id: signed-in, reading: { what: "whether she is signed in (counted)", '
                                    'inputs: [ { name: dee-sessions, origin: { act: read, nature: soma, by: sam }, '
                                    'quantity: number } ], steps: [ { id: zero, op: constant, value: { count: "0", '
                                    'unit: "{item}" } }, { id: ok, op: compare, of: dee-sessions, with: zero, is: '
                                    'greater } ] } }',
                                    'use: { id: desk, by: dee, of: docs, while: signed-in }'))
    write(G, 'beans/ada-work.md', employment('ada-work', 'ada',
                                             'use: { id: use-sales, by: ada, of: group-sales }',
                                             'permitted: { id: may-sales, of: use-sales, through: self }',
                                             'use: { id: use-plans, by: ada, of: group-plans }',
                                             'permitted: { id: may-plans, of: use-plans, through: self }'))
    write(G, 'beans/ben-work.md', employment('ben-work', 'ben', 'use: { id: use-sales, by: ben, of: group-sales }',
                                             'withdraw: { id: left, by: ben, of: employed, at: 2026-02-27 }'))
    write(G, 'beans/cy-work.md', employment('cy-work', 'cy', 'withdraw: { id: leaving, by: cy, of: employed, at: 2099-12-31 }'))
    write(G, 'beans/cut-ada.md', bean('cut-ada', 'document', "Ada's plans group closed", 'own: { by: sam, of: self }',
                                      'forbidden: { of: "ada-work#use-plans", through: self }', body='A decision.'))
    write(G, 'beans/first.md', decision('first', [('asked', '2026-03-02 09:00+03:00'), ('decided', '2026-03-02 10:00+03:00')],
                                        'grant: { id: ada-docs, by: workshop, to: ada, of: docs, through: smb, as: read }',
                                        'grant: { id: ben-docs, by: workshop, to: ben, of: docs, through: smb, as: write }',
                                        'grant: { id: ben-plans, by: workshop, to: ben, of: plans, through: smb, as: write }'))
    write(G, 'beans/second.md', decision('second', [('asked', '2026-03-09 09:00+03:00'), ('decided', '2026-03-09 10:00+03:00')],
                                         'revoke: { id: no-ben-plans, by: sam, of: "first#ben-plans", through: self }',
                                         'grant: { id: cy-plans, by: workshop, to: cy, of: plans, through: smb, as: read }'))
    write(G, 'beans/third.md', decision('third', [('asked', '2026-03-10 09:00+03:00')],
                                        'revoke: { id: no-ada-docs, by: sam, of: "first#ada-docs", through: self }',
                                        'grant: { id: dee-docs, by: workshop, to: dee, of: docs, through: smb, as: read }'))
    write(G, 'beans/fourth.md', decision('fourth', [('asked', '2026-03-11 09:00+03:00'), ('refused', '2026-03-11 10:00+03:00')],
                                         'grant: { id: dee-plans, by: workshop, to: dee, of: plans, through: smb, as: write }'))
    r = grow.run(PY, 'bin/save.py', 'sam', "RULE-CHANGE: the workshop's people, shares, groups and decisions", '--body',
                 '- action: RULE-CHANGE — VOCAB.md adds the kind procedure, two namespaces, the verbs revoke and withdraw, '
                 "and the crosswalks of a file server's and an ERP's records; wrote [[walk-shares]], [[workshop]], "
                 '[[docs]], [[plans]], [[group-sales]], [[group-plans]], [[ada]], [[ben]], [[cy]], [[dee]], [[ada-work]], '
                 '[[ben-work]], [[cy-work]], [[dee-offer]], [[cut-ada]], [[first]], [[second]], [[third]] and [[fourth]]\n'
                 '- ratified_by: sam', cwd=G)
    check("...its people, shares, groups, employments and decisions, and its own crosswalks of their records, pass the gate",
          r.returncode == 0, r.out[-2000:])

    # ---- the reader asked directly
    from core import crosswalk
    from core.inforce import InForce
    F = InForce(G)
    st = lambda b, sid: F.statement(f"{b}#{sid}")[2]        # noqa: E731
    check("a statement holds while what its `while` names holds: a reading that finds her employment; not one that finds "
          "none; not known (None) where the reading cannot be read (an input nobody gave); always with no `while`",
          (F.holds('ada', st('ada', 'erp')), F.holds('dee', st('dee', 'erp')), F.holds('dee', st('dee', 'desk')),
           F.holds('ben', st('ben', 'erp'))) == (True, False, None, True),
          (F.holds('ada', st('ada', 'erp')), F.holds('dee', st('dee', 'erp')), F.holds('dee', st('dee', 'desk'))))
    A = InForce(G, assume={'dee#arrived'})
    check("...and the garden as it would stand once a reading holds (`assume`: a plan's world): her name held while she "
          "arrived holds there, and nothing else moves", A.holds('dee', st('dee', 'erp')) is True
          and A.holds('ada', st('ada', 'erp')) is True and F.holds('dee', st('dee', 'erp')) is False)
    check("the decisions in force on the walk: those whose course stands at a step the walk marks final, in the order "
          "they came in — never one only asked, nor one refused — and the request being planned last",
          F.decisions('walk-shares') == ['first', 'second'] and F.decisions('walk-shares', 'third') == ['first', 'second',
                                                                                                     'third'],
          (F.decisions('walk-shares'), F.decisions('walk-shares', 'third')))
    order = F.decisions('walk-shares')
    check("what ends a statement: a revoke among the decisions in force ends what it names, and one of a decision only "
          "asked does not; a withdrawal whose day has come ends the agreement it names, and one whose day is to come "
          "does not yet",
          F.ended('first', st('first', 'ben-plans'), 'revoke', order) and not F.ended('first', st('first', 'ada-docs'), 'revoke', order)
          and F.ended('first', st('first', 'ada-docs'), 'revoke', order + ['third'])
          and F.ended('ben-work', st('ben-work', 'employed'), 'withdraw')
          and not F.ended('cy-work', st('cy-work', 'employed'), 'withdraw'))
    check("a use's standing: in force while a permitted of it holds and no forbidden of it does; a use nobody permitted, "
          "and one forbidden through a decision, are not",
          F.standing('ada-work', st('ada-work', 'use-sales')) and not F.standing('ada-work', st('ada-work', 'use-plans'))
          and not F.standing('ben-work', st('ben-work', 'use-sales')))
    p = F.policy('walk-shares', ended_by='revoke')
    q = F.policy('walk-shares', include='third', ended_by='revoke')
    kept = lambda pol: [f"{b}#{i}" for b, i, v, _r in pol.kept if v == 'grant']   # noqa: E731
    check("a walk tool's policy: the grants of the decisions in force, less what a revoke among them ends; with the "
          "request being planned, the garden as it would stand after it",
          kept(p) == ['first#ada-docs', 'first#ben-docs', 'second#cy-plans'] and p.ended == ['first#ben-plans']
          and kept(q) == ['first#ben-docs', 'second#cy-plans', 'third#dee-docs']
          and q.ended == ['first#ada-docs', 'first#ben-plans'], (p, q))

    # ---- the crosswalks that read through it
    R = crosswalk.Reader(G, 'odoo', '17.0')
    try:
        acc = R.records('smb.access')
        users = sorted(u['name'] for u in R.records('smb.user'))
        shares = {s['id']: s['name'] for s in R.records('smb.share')}
        names = {crosswalk.number('smb.user', b): b for b in ('ada', 'ben', 'cy', 'dee')}
        seen = sorted((names.get((a['user_id'] or [None])[0]), shares.get((a['share_id'] or [None])[0]), a['type'])
                      for a in acc)
    except crosswalk.Refused as e:
        seen, users = str(e), []
    check("a share's access, one record per grant through smb in force on the walk — less the grant a decision in force "
          "revoked, never one only asked or refused — each its user, its share and its type mapped",
          seen == [('ada', 'Docs', 'r'), ('ben', 'Docs', 'rw'), ('cy', 'Plans', 'r')], seen)
    check("...its users, the people such a grant reaches, and no one whose grant is not in force", users == ['Ada', 'Ben', 'Cy'],
          users)
    try:
        us = {u['login']: u for u in R.records('res.users')}
        grp = {g_['id']: g_['name'] for g_ in R.records('res.groups')}
    except crosswalk.Refused as e:
        us, grp = {}, {'refused': str(e)}
    check("an ERP's users: each person whose sign-in name holds, never one whose name is held while she arrived and she "
          "has not", sorted(us) == ['ada.l', 'ben.k', 'cy.m'], (us, grp))
    check("...their groups, the uses in force: permitted through the employment and not forbidden through a decision",
          [grp.get(i) for i in us.get('ada.l', {}).get('groups_id') or []] == ['sales.user']
          and us.get('ben.k', {}).get('groups_id') == [], {k: v.get('groups_id') for k, v in us.items()})
    check("...active while employed: an employment withdrawn from a day that has come is not; one whose day is still to "
          "come is", (us.get('ada.l', {}).get('active'), us.get('ben.k', {}).get('active'), us.get('cy.m', {}).get('active'))
          == (True, False, True), {k: v.get('active') for k, v in us.items()})

    # ---- the law refuses `statements` forms out of form
    from core.law import Law
    row = dict(Law.load(('VOCAB.md', {})).crosswalks['odoo-17.0-hr.department'], crosswalk='x', model='x.one')
    probs = lambda *rows: [m for _r, _w, m in Law.load(('VOCAB.md', {'crosswalks': list(rows)})).found] + \
        [m for _w, m in Law.load(('VOCAB.md', {'crosswalks': list(rows)})).crosswalk_problems()]   # noqa: E731
    bad = probs(dict(row, statements={'verb': 'nonesuch', 'naming': 'to', 'colour': 'blue'}),
                dict(row, crosswalk='y', model='x.two', kind=None,
                     statements={'verb': 'grant', 'naming': 'nobody', 'ended_by': 'nonesuch'},
                     fields={'a': {'from': 'zz'}, 'b': {'statements': {'verb': 'use'}, 'exists': 'maybe'},
                             'c': {'from': 'title', 'map': 'r'}}))
    check("...and the law refuses a `statements` form out of form: a row with both a kind and statements, a verb it lacks, a "
          "role the verb has not, a key of no such form, an ending verb it lacks, a role no statement of the row's verb "
          "has, `exists` not true, a `map` that maps nothing",
          any('one of `kind` and `statements`' in m for m in bad) and any("'nonesuch' is no verb of the law" in m for m in bad)
          and any("`nobody` is no role of grant" in m for m in bad) and any('`colour` is no key of `statements`' in m for m in bad)
          and any("`zz` is no role of grant" in m for m in bad) and any('`exists` is true' in m for m in bad)
          and any('`map` maps' in m for m in bad), bad)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_inforce: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
