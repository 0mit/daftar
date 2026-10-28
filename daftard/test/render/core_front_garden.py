#!/usr/bin/env python3
"""core_front_garden — the gardens test/render/core_front.mjs serves: gardens of the core alone, grown from a daftar
tree. Not a suite: core_front.mjs runs it.

    python3 test/render/core_front_garden.py <daftar tree> <folder>      # prints {"register": …, "bare": …}

One keeps a register (an Odoo instance, its bean saved through the gate) and the views of Odoo 19's res.partner it
captured; the other is as germinated, offering nothing yet. Invented, and nothing of a register's records in either.
"""
import json
import os
import sys

tree, folder = sys.argv[1], sys.argv[2]
sys.path.insert(0, os.path.join(tree, 'test'))
import grow  # noqa: E402

rel = grow.release(os.path.join(folder, 'release'))
out = {}
for name in ('register', 'bare'):
    G = os.path.join(folder, name)
    r = grow.garden(rel, G, 'sam', '--gardener-name', 'Sam')
    if r.returncode != 0:
        raise SystemExit(r.out[-1500:])
    out[name] = G
G = out['register']
with open(os.path.join(G, 'beans', 'register.md'), 'w', encoding='utf-8') as fh:
    fh.write('---\nbean: register\nkind: instance\ntitle: "The register"\nstatements:\n  - say: { by: sam, at: now }\n'
             '  - own: { by: sam, of: self }\n---\nAn Odoo instance read live.\n')
s = grow.run(sys.executable, 'bin/save.py', 'sam', 'The register', '--body', '- action: wrote [[register]]', cwd=G)
if s.returncode != 0:
    raise SystemExit(s.out[-1500:])
cap = os.path.join(G, 'captures', 'views', 'odoo-19.0', 'res.partner')
os.makedirs(cap)
with open(os.path.join(cap, 'fields.json'), 'w', encoding='utf-8') as fh:
    json.dump({'name': {'type': 'char', 'string': 'Name'}}, fh)
with open(os.path.join(cap, 'list.xml'), 'w', encoding='utf-8') as fh:
    fh.write('<list string="Contacts"><field name="name"/></list>\n')
with open(os.path.join(G, 'captures', 'views', 'odoo-19.0', 'CAPTURE.json'), 'w', encoding='utf-8') as fh:
    fh.write('{"series": "19.0"}\n')
print(json.dumps(out))
