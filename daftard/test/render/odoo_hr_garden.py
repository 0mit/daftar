#!/usr/bin/env python3
"""odoo_hr_garden — the garden test/render/odoo_hr.mjs serves: invented people of an invented company, grown from a
daftar tree whose law crosses Odoo 17's hr.employee and hr.leave, in two saves (so the page can be read as of the
first). Not a suite: odoo_hr.mjs runs it.

    python3 test/render/odoo_hr_garden.py <daftar tree> <folder>      # prints {"garden": …, "first": <commit>}

Acme Tiles (the company Sam keeps the garden for) has a workshop and an office. Lale Demir tiles in the workshop and
Mo Karimi keeps the books in the office, each by an employment agreement, which is also each one's word to be kept
here by name. Lale's identity number and private mail are sealed in this host's store. In the second save, each takes
leave under their employment's allowance: Lale's summer, approved on the leave walk; Mo's three days, asked.
"""
import json
import os
import socket
import subprocess
import sys

tree, folder = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(tree, 'test'))
import grow  # noqa: E402

PY = sys.executable
G = os.path.join(folder, 'garden')
HOST = socket.gethostname().lower()


def write(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def bean(bid, kind, title, *statements, body=None, where='beans', details=''):
    write(f'{where}/{bid}.md', f'---\nbean: {bid}\nkind: {kind}\ntitle: "{title}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
          + ''.join(f'  - {s}\n' for s in statements) + (f'details:\n{details}' if details else '') + f'---\n{body or title}.\n')


def must(r, what):
    if r.returncode:
        sys.exit(f'odoo_hr_garden: {what}: ' + r.out[-1500:])


rel = grow.release(os.path.join(folder, 'release'))
must(grow.garden(rel, G, 'sam', '--gardener-name', 'Sam'), 'the garden did not grow')
write('VOCAB.md', '---\nkinds:\n  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n'
      'namespaces:\n  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for itself" }\n---\n'
      "# the garden's own rows\n")
bean('laptop', 'host', 'laptop — the machine this garden is kept on', 'own: { by: sam, of: self }',
     f'name: {{ by: anchor-hostname, of: self, as: {HOST} }}',
     details=f'  roots:\n    vault: {{ system: unix-filesystem, at: "{HOST}:{folder}/vault", keeps: special-category, '
             f'readable_from: this-host }}\n')
bean('acme', 'org', 'Acme Tiles', 'represent: { by: sam, of: self, as: "keeps its garden" }',
     'name: { by: dns, of: self, as: acme.example }')
bean('workshop', 'org', 'Workshop', 'part: { by: self, of: acme }')
bean('office', 'org', 'Office', 'part: { by: self, of: acme }')
for pid, name, mail, phone in (('lale', 'Lale Demir', 'lale@acme.example', '+15555550147'),
                               ('mo', 'Mo Karimi', 'mo@acme.example', '+15555550148')):
    extra = ['name: { id: tckn, by: tr-tckn, of: self, as: "10000000146" }',
             'name: { id: home-mail, by: mail, of: self, as: "lale@home.example" }'] if pid == 'lale' else []
    bean(pid, 'person', name, 'own: { by: theone, of: self }', 'answer: { by: self, of: self, as: law }',
         f'name: {{ by: mail, of: self, as: "{mail}" }}', f'name: {{ by: e164, of: self, as: "{phone}" }}', *extra)
for pid, job, dept in (('lale', 'Tiler', 'workshop'), ('mo', 'Bookkeeper', 'office')):
    bean(f'{pid}-acme', 'contract', f'{pid}-acme — {job} at Acme Tiles', 'own: { by: theone, of: self }',
         'answer: { by: acme, of: self, as: law }', f'answer: {{ by: {pid}, of: self, as: law }}',
         'agree: { by: acme, of: self, through: written, as: employer, at: 2026-03-01 }',
         f'agree: {{ id: employed, by: {pid}, of: self, through: written, as: employee, at: 2026-03-01 }}',
         f'represent: {{ by: {pid}, of: acme, as: "{job}" }}', f'part: {{ by: self, of: {dept} }}',
         f'hold: {{ id: allowance, by: {pid}, of: {{ count: "20", unit: d }} }}',
         'obligatory: { id: leave, of: allowance, through: self, note: "twenty days of leave in each year" }')
bean('walk-leave', 'procedure', 'walk-leave — how a leave is asked for and decided',
     'step: { id: asked, as: "the employee asks for the days", by: employee, to: [approved, refused] }',
     'step: { id: approved, as: "the employer approves them", by: employer, walk: { final: "true" } }',
     'step: { id: refused, as: "the employer refuses them", by: employer, walk: { exit: "true" } }', where='mappings')
for sid in ('tckn', 'home-mail'):
    must(grow.run(PY, 'bin/held.py', 'put', 'lale', sid, '--basis', 'lale-acme#employed', cwd=G), f'sealing {sid}')
must(grow.run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: Acme Tiles, its two departments, and Lale and Mo employed', '--body',
              '- action: RULE-CHANGE — VOCAB.md names the kind procedure and the namespace anchor-hostname; wrote '
              '[[laptop]], whose vault keeps material off git, [[acme]], [[workshop]], [[office]], [[lale]], [[mo]], '
              '[[lale-acme]], [[mo-acme]] (each one\'s word to be kept here by name) and [[walk-leave]]',
              '- ratified_by: sam', '- held: lale tckn added', '- held: lale home-mail added', cwd=G), 'the first save')
first = grow.run('git', 'rev-parse', 'HEAD', cwd=G).stdout.strip()
bean('lale-summer', 'event', 'Summer leave', 'own: { by: theone, of: self }', 'concern: { of: lale }',
     'be: { by: self, at: 2026-07-06/2026-07-17, as: presence }', 'use: { by: self, of: "lale-acme#allowance" }',
     'be: { id: decided, by: self, at: walk-leave, as: order }',
     'move: { by: lale, of: self, through: decided, at: [now, "walk-leave#asked"] }',
     'move: { by: sam, of: self, through: decided, at: [now, "walk-leave#approved"] }')
bean('mo-flu', 'event', 'Three days off', 'own: { by: theone, of: self }', 'concern: { of: mo }',
     'be: { by: self, at: 2026-10-05/2026-10-07, as: presence }', 'use: { by: self, of: "mo-acme#allowance" }',
     'be: { id: decided, by: self, at: walk-leave, as: order }',
     'move: { by: mo, of: self, through: decided, at: [now, "walk-leave#asked"] }')
must(grow.run(PY, 'bin/save.py', 'sam', "Lale's summer leave, approved; Mo's three days, asked", '--body',
              '- action: wrote [[lale-summer]], approved on [[walk-leave]], and [[mo-flu]], asked', cwd=G), 'the second save')
print(json.dumps({'garden': G, 'first': first}))
