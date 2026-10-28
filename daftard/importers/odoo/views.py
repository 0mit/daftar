#!/usr/bin/env python3
"""views — take an Odoo series' own views of each model, as that Odoo resolves them, into captures (design §10.2).

    python3 importers/odoo/views.py --url <http://host:port> --db <name> --login <user> --out <dir> \\
        --model <model> [--model …] [--type list --type form …] [--lang tr_TR --lang fa_IR …]
    (the password is read from ODOO_PASSWORD, never from the command line)

AN IMPORTED VIEW IS A CAPTURE (MODEL, ground rule 3: captured knowingly): what one Odoo instance, at its version, with
its modules, resolved for a model — read with `get_views`, every inheritance applied — dated and kept as it came,
never authoritative and never edited: re-taken instead. Each importer runs that series' own Odoo, a throwaway
Community instance with the owners' addons (never Enterprise), so what is taken is what that series would show.

WHAT IS TAKEN for each model and view type: the arch as the instance resolved it, with every `groups` attribute
taken off — a capture shows what the view holds, and who may see a part of it is the garden's grants, never an Odoo
group — and the fields the view's model describes, whole, as the instance described them to its own web client (names,
types, strings, selections, relations: what the search and the views read). The user it reads as is given every group first, so nothing a group hides is missing. Written
to `<out>/<model>/<type>.xml`, `<out>/<model>/fields.json` and `related.json` (the fields of each other model the views
show: a one2many's own list in a form) — and, for each language asked (loaded on the instance first), as the instance
resolves them in it: `<type>.<lang>.xml`, `fields.<lang>.json` and `related.<lang>.json` — and `<out>/CAPTURE.json` says what was read: the
series and server version, the modules installed with their versions, the moment, and the instance's address — no
password, no record.

Exit 0 when every view was taken, 1 when one could not be, 2 for a usage error.
"""
import argparse
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
import xmlrpc.client

TYPES = ('list', 'form', 'search', 'kanban')


def stripped(arch):
    """The arch with every `groups` attribute taken off, as text."""
    root = ET.fromstring(arch)
    for el in root.iter():
        el.attrib.pop('groups', None)
    return ET.tostring(root, encoding='unicode')


def fields_of(desc):
    """The fields as the instance described them to its web client, whole, in a stable order."""
    return {name: dict(sorted(f.items())) for name, f in sorted(desc.items()) if isinstance(f, dict)}


class Odoo:
    def __init__(self, url, db, login, password):
        self.url, self.db, self.password = url.rstrip('/'), db, password
        common = xmlrpc.client.ServerProxy(self.url + '/xmlrpc/2/common', allow_none=True)
        self.version = common.version()
        self.uid = common.authenticate(db, login, password, {})
        if not self.uid:
            raise SystemExit("views: the instance refused that login")
        self.obj = xmlrpc.client.ServerProxy(self.url + '/xmlrpc/2/object', allow_none=True)

    def call(self, model, method, *args, **kw):
        return self.obj.execute_kw(self.db, self.uid, self.password, model, method, list(args), kw)


USER_TYPES = ('group_user', 'group_portal', 'group_public')     # base's three user types: a user has exactly one


def series_major(version):
    """The series' major number, from what the instance says of itself (`server_serie`: '17.0', '19.0', 'saas~18.4')."""
    import re
    m = re.search(r'(\d+)\.\d+$', str((version or {}).get('server_serie') or ''))
    return int(m.group(1)) if m else 0


def every_group(odoo):
    """Give the reading user every group but the user types, so nothing a group hides is missing from what is taken.
    From series 19 a group hangs off a privilege (no `category_id`), and a user's groups are `group_ids`: the user types
    are named by their ids in base, and a group that implies another user type than the reader's own (an addon's group
    for its portal users implies portal) is left out too, since 19 refuses a user two of them. Before 19, they are the
    groups of base's user-type category, and `groups_id`."""
    if series_major(odoo.version) >= 19:
        types = {t['name']: t['res_id'] for t in odoo.call(
            'ir.model.data', 'search_read', [('module', '=', 'base'), ('model', '=', 'res.groups'),
                                             ('name', 'in', list(USER_TYPES))], fields=['name', 'res_id'])}
        others = [types[n] for n in ('group_portal', 'group_public') if n in types]
        groups = odoo.call('res.groups', 'search', [('id', 'not in', list(types.values())),
                                                    ('all_implied_ids', 'not in', others)])
        odoo.call('res.users', 'write', [odoo.uid], {'group_ids': [(4, g) for g in groups]})
        return
    kind = odoo.call('ir.model.data', 'search_read', [('module', '=', 'base'), ('name', '=', 'module_category_user_type')],
                     fields=['res_id'])
    groups = odoo.call('res.groups', 'search', [('category_id', '!=', kind[0]['res_id'])] if kind else [])
    odoo.call('res.users', 'write', [odoo.uid], {'groups_id': [(4, g) for g in groups]})


def take(odoo, models, types, out, langs=()):
    """Every view of every model, in English and in each of `langs`, written under `out`; (taken, failed)."""
    # nothing hidden by a group: the user is given every group but the user types (internal, portal, public), of which
    # a user has one
    every_group(odoo)
    taken, failed = [], []
    for model in models:
        d = os.path.join(out, model)
        os.makedirs(d, exist_ok=True)
        for lang in ('',) + tuple(langs):
            suffix = f'.{lang}' if lang else ''
            try:
                got = odoo.call(model, 'get_views', [[False, t] for t in types],
                                options={'toolbar': False, 'load_filters': False}, context={'lang': lang or 'en_US'})
            except xmlrpc.client.Fault as e:
                failed.append((model, '*' + suffix, e.faultString.strip().splitlines()[-1][:300]))
                continue
            for t in types:
                v = (got.get('views') or {}).get(t)
                if not v:
                    failed.append((model, t + suffix, 'no view of this type'))
                    continue
                with open(os.path.join(d, f'{t}{suffix}.xml'), 'w', encoding='utf-8', newline='\n') as fh:
                    fh.write(stripped(v['arch']) + '\n')
                taken.append((model, t + suffix, v.get('id') or None))
            models = got.get('models') or {}
            fields = models.get(model) or {}
            fields = fields.get('fields', fields) if isinstance(fields, dict) else {}
            with open(os.path.join(d, f'fields{suffix}.json'), 'w', encoding='utf-8', newline='\n') as fh:
                json.dump(fields_of(fields), fh, ensure_ascii=False, indent=1, sort_keys=True)
                fh.write('\n')
            # the fields of every other model the views show, as the instance described them with these views: a
            # one2many's own list or form in a view is read with its model's fields
            related = {m: fields_of(f.get('fields', f)) for m, f in sorted(models.items()) if m != model and isinstance(f, dict)}
            with open(os.path.join(d, f'related{suffix}.json'), 'w', encoding='utf-8', newline='\n') as fh:
                json.dump(related, fh, ensure_ascii=False, indent=1, sort_keys=True)
                fh.write('\n')
    return taken, failed


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--url', required=True)
    ap.add_argument('--db', required=True)
    ap.add_argument('--login', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--model', action='append', required=True)
    ap.add_argument('--type', action='append', choices=TYPES)
    ap.add_argument('--lang', action='append', default=[])
    a = ap.parse_args(argv)
    password = os.environ.get('ODOO_PASSWORD')
    if not password:
        print("views: the password is read from ODOO_PASSWORD", file=sys.stderr)
        return 2
    odoo = Odoo(a.url, a.db, a.login, password)
    taken, failed = take(odoo, a.model, tuple(a.type or TYPES), a.out, tuple(a.lang))
    mods = odoo.call('ir.module.module', 'search_read', [('state', '=', 'installed')], fields=['name', 'installed_version'])
    capture = {'what': 'views of an Odoo instance, as it resolved them (get_views), groups taken off',
               'series': odoo.version.get('server_serie'), 'server_version': odoo.version.get('server_version'),
               'instance': a.url, 'database': a.db, 'read_as': a.login,
               'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'languages': ['en_US'] + list(a.lang),
               'modules': {m['name']: m['installed_version'] for m in sorted(mods, key=lambda m: m['name'])},
               'taken': [{'model': m, 'type': t, 'view_id': i} for m, t, i in taken],
               'not_taken': [{'model': m, 'type': t, 'why': w} for m, t, w in failed]}
    with open(os.path.join(a.out, 'CAPTURE.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(capture, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    for m, t, w in failed:
        print(f"views: {m} {t}: not taken — {w}")
    print(f"views: {len(taken)} taken from {capture['series']} ({capture['server_version']}), {len(failed)} not, into {a.out}")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
