#!/usr/bin/env python3
"""The records behind Odoo's views (design §10.2, P5.3): the worker's `odoo_records` reads them from a real garden of
the core through the law's crosswalks (the garden's own core/crosswalk.py), keeps only the beans the reader's grants
open, and lets no field point at a record the reader may not read. Then Odoo's own calls are answered over them, by the
worker as daftard runs it (test/worker/odoo_worker.py). Each call's grants are proved in test/worker/odoo_grants_test.py.

    python3 test/worker/records_test.py [<daftar tree>]     # a tree whose law has crosswalks (default ~/daftar)
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test

FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-1200:]))
    if not cond:
        FAILS.append(name)


if not os.path.isfile(os.path.join(TREE, 'core', 'law', 'crosswalks.yaml')):
    print(f"records: {TREE} has no core/law/crosswalks.yaml — give a tree whose law crosses Odoo's models")
    sys.exit(2)
T = Path(tempfile.mkdtemp(prefix='worker-records-'))
try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam')


    def org(bid, title, *st):
        (G / 'beans' / f'{bid}.md').write_text(f'---\nbean: {bid}\nkind: org\ntitle: "{title}"\nstatements:\n'
                                               '  - say: { by: sam, at: now }\n' + ''.join(f'  - {x}\n' for x in st)
                                               + f'---\n{title}.\n', encoding='utf-8')


    org('acme', 'Acme', 'represent: { by: sam, of: self, as: "keeps its garden" }')
    org('eng', 'Engineering', 'part: { by: self, of: acme }')
    org('qa', 'Quality', 'part: { by: self, of: eng }')
    (G / 'beans' / 'ana.md').write_text('---\nbean: ana\nkind: person\ntitle: "Ana"\nstatements:\n  - say: { by: sam, at: now }\n'
                                         '  - own: { by: theone, of: self }\n  - answer: { by: self, of: self, as: law }\n---\nAna.\n',
                                         encoding='utf-8')
    (G / 'beans' / 'ana-consent.md').write_text(
        '---\nbean: ana-consent\nkind: contract\ntitle: "Ana agrees to be kept here by name"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
        '  - agree: { id: ana-agrees, by: ana, of: "kept here by name", through: spoken }\n'
        '  - agree: { id: sam-agrees, by: sam, of: "kept here by name", through: spoken }\n---\nHer word.\n', encoding='utf-8')
    sam = (G / 'beans' / 'sam.md').read_text(encoding='utf-8')
    (G / 'beans' / 'sam.md').write_text(sam.replace('\n---\n', '\n  - grant: { id: ana-eng, by: self, as: read, of: [acme, eng], to: [ana] }\n'
                                                    '  - say: { by: sam, of: [ana-eng], at: now }\n---\n', 1), encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'Acme, its departments, and Ana reading one', '--body',
                 '- action: wrote [[acme]], [[eng]], [[qa]] and [[ana]] (kept on her word, [[ana-consent]]); [[sam]] opens '
                 'Acme and [[eng]] to Ana', cwd=str(G))
    check('the garden holds a company, two departments and Ana, who may read one, through its gate',
          r.returncode == 0 and s.returncode == 0, r.out[-600:] + s.out[-1200:])

    # the worker as daftard runs it, in that garden, answering Odoo's calls; its records are read through a reading
    fields = {'hr.department': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                                'complete_name': {'type': 'char'}, 'active': {'type': 'boolean'},
                                'parent_id': {'type': 'many2one', 'relation': 'hr.department'},
                                'child_ids': {'type': 'one2many', 'relation': 'hr.department'},
                                'company_id': {'type': 'many2one', 'relation': 'res.company'}},
              'res.company': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'}}}
    cap = G / 'captures' / 'views' / 'odoo-17.0'
    for m, f in fields.items():
        (cap / m).mkdir(parents=True, exist_ok=True)
        (cap / m / 'fields.json').write_text(json.dumps(f), encoding='utf-8')
    (cap / 'CAPTURE.json').write_text('{"series": "17.0"}\n', encoding='utf-8')
    sys.path.insert(0, HERE)
    from odoo_worker import Worker  # noqa: E402
    w = Worker(G, scratch=str(T))
    SPEC = {'name': {}, 'complete_name': {}, 'child_ids': {}, 'parent_id': {'fields': {'display_name': {}}},
            'company_id': {'fields': {'display_name': {}}}}


    def records(model, reader):
        got = w.kw(reader, model, 'web_search_read', [], domain=[], specification=SPEC if model == 'hr.department' else {'name': {}})
        return got.get('records') if isinstance(got, dict) and 'records' in got else got


    deps = {d['name']: d for d in records('hr.department', 'sam')}
    co = records('res.company', 'sam')
    check("the gardener reads Acme and both its departments, as the garden's crosswalks read them",
          [c['name'] for c in co] == ['Acme'] and sorted(deps) == ['Engineering', 'Quality']
          and deps['Quality']['parent_id'] == {'id': deps['Engineering']['id'], 'display_name': 'Engineering'}
          and deps['Engineering']['company_id'] == {'id': co[0]['id'], 'display_name': 'Acme'}, (co, deps))
    ana = records('hr.department', 'ana')
    check("Ana reads only the department her grant opens, in the company it opens; it names no child she may not read",
          [d['name'] for d in ana] == ['Engineering'] and ana[0]['company_id']['display_name'] == 'Acme'
          and ana[0]['child_ids'] == [], ana)
    check("...and of the companies, only the one opened to her", [c['name'] for c in records('res.company', 'ana')] == ['Acme'])
    check("a reader the garden does not name, and a model the law does not cross, read nothing",
          records('hr.department', 'nobody') == [] and records('hr.department', '../sam') == []
          and records('hr.job', 'sam') == [], ana)
    got = [x['complete_name'] for x in w.kw('sam', 'hr.department', 'web_search_read', [], domain=[('parent_id', '!=', False)],
                                             specification={'complete_name': {}})['records']]
    check("Odoo's own search over them: the departments under another department", got == ['Engineering / Quality'], got)
    got = [x['name'] for x in w.kw('sam', 'hr.department', 'web_search_read', [], domain=[('company_id.name', 'ilike', 'acm')],
                                    specification={'name': {}})['records']]
    check("...and through a relation, the departments of a company whose name is like 'acm'",
          sorted(got) == ['Engineering', 'Quality'], got)
    w.close()
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nrecords: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
