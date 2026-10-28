#!/usr/bin/env python3
"""importers/odoo/views.py against a stand-in Odoo (an XML-RPC server playing the two endpoints it calls): each view
written as the instance resolved it with every `groups` attribute taken off, the fields the search components read,
CAPTURE.json saying what was read and when and holding no password, the reading user given every group but the user
types, and a model the instance refuses recorded as not taken (exit 1). And series 19, where a group hangs off a
privilege, a user's groups are `group_ids`, and a user may not hold two user types — so a group that implies portal
or public is left out too.

    python3 test/importers/odoo_views_test.py
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from xmlrpc.server import SimpleXMLRPCServer

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, '..', '..', 'importers', 'odoo', 'views.py')
calls = []
SERIES = ['17.0']                      # what the stand-in says it is; the 19 part of the test turns it
USER_TYPES = {'group_user': 1, 'group_portal': 2, 'group_public': 3}
ARCH = ('<search string="People"><field name="name" groups="base.group_user"/>'
        '<filter name="mine" string="Mine" domain="[(\'user_id\', \'=\', uid)]" groups="base.group_no_one"/>'
        '<searchpanel><field name="team_id" groups="a.b,c.d"/></searchpanel></search>')


class Common:
    def version(self):
        return {'server_serie': SERIES[0], 'server_version': SERIES[0] + '-20240429'}

    def authenticate(self, db, login, password, ctx):
        return 2 if (db, login, password) == ('d', 'admin', 'pw') else False


class Obj:
    def execute_kw(self, db, uid, password, model, method, args, kw):
        calls.append((model, method, args, kw))
        if SERIES[0] == '19.0':
            return self.nineteen(model, method, args, kw)
        if model == 'ir.model.data':
            return [{'id': 1, 'res_id': 77}]
        if (model, method) == ('res.groups', 'search'):
            return [10, 11]
        if (model, method) == ('res.users', 'write'):
            return True
        if model == 'ir.module.module':
            return [{'id': 1, 'name': 'web', 'installed_version': '17.0.1.0'}, {'id': 2, 'name': 'base', 'installed_version': '17.0.1.3'}]
        if method == 'get_views' and model == 'people':
            arch = ARCH.replace('People', 'Kişiler') if (kw.get('context') or {}).get('lang') == 'tr_TR' else ARCH
            return {'views': {t: {'arch': arch, 'id': 5} for t in ('list', 'search')},
                    'models': {'people': {'fields': {'name': {'string': 'Name', 'type': 'char', 'store': True, 'secret_thing': 1},
                                                     'team_id': {'string': 'Team', 'type': 'many2one', 'relation': 'team'}}},
                               'team': {'fields': {'lead': {'string': 'Lead', 'type': 'char'}}}}}
        raise Exception('Model not found: ' + model)

    def nineteen(self, model, method, args, kw):
        """As 19 answers: no user-type category, `group_ids`, and two user types for one user refused."""
        if model == 'ir.model.data':
            names = dict((d[0], d[2]) for d in args[0] if isinstance(d, list))
            if names.get('name') == 'module_category_user_type':
                return []
            return [{'id': 9, 'name': n, 'res_id': USER_TYPES[n]} for n in names.get('name', []) if n in USER_TYPES]
        if (model, method) == ('res.groups', 'search'):
            dom = args[0]
            out = [g for g in (1, 2, 3, 10, 11, 12) if not any(
                d[0] == 'id' and d[1] == 'not in' and g in d[2] for d in dom)]
            implies = {12: [2]}                       # an addon's group for its portal users implies portal
            return [g for g in out if not any(d[0] == 'all_implied_ids' and d[1] == 'not in'
                                              and (set(implies.get(g, [])) | {g}) & set(d[2]) for d in dom)]
        if (model, method) == ('res.users', 'write'):
            vals = args[1]
            if 'groups_id' in vals:
                raise Exception("Invalid field 'groups_id' on model 'res.users'")
            given = {c[1] for c in vals.get('group_ids', [])}
            if given & {2, 3, 12} or not given:
                raise Exception("The user cannot have more than one user types.")
            return True
        if model == 'ir.module.module':
            return [{'id': 1, 'name': 'web', 'installed_version': '19.0.1.0'}]
        if method == 'get_views' and model == 'people':
            return {'views': {'list': {'arch': ARCH, 'id': 5, 'model': 'people', 'toolbar': {}}},
                    'models': {'people': {'fields': {'name': {'string': 'Name', 'type': 'char'}}}}}
        raise Exception('Model not found: ' + model)


srv = SimpleXMLRPCServer(('127.0.0.1', 0), logRequests=False, allow_none=True)
paths = {'/xmlrpc/2/common': Common(), '/xmlrpc/2/object': Obj()}


class Dispatch:
    def _dispatch(self, method, params):
        return getattr(paths[srv.current_path], method)(*params)


orig = srv.RequestHandlerClass
class Handler(orig):  # noqa: E302
    rpc_paths = tuple(paths)

    def do_POST(self):
        srv.current_path = self.path
        return orig.do_POST(self)


srv.RequestHandlerClass = Handler
srv.register_instance(Dispatch())
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{srv.server_address[1]}'
out = tempfile.mkdtemp(prefix='odoo-views-')
try:
    r = subprocess.run([sys.executable, TOOL, '--url', url, '--db', 'd', '--login', 'admin', '--out', out,
                        '--model', 'people', '--model', 'gone', '--type', 'list', '--type', 'search'],
                       capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, ODOO_PASSWORD='pw'))
    arch = open(os.path.join(out, 'people', 'search.xml'), encoding='utf-8').read()
    assert 'groups=' not in arch and 'name="mine"' in arch and '<searchpanel>' in arch, arch
    fields = json.load(open(os.path.join(out, 'people', 'fields.json'), encoding='utf-8'))
    assert fields == {'name': {'secret_thing': 1, 'store': True, 'string': 'Name', 'type': 'char'},
                      'team_id': {'relation': 'team', 'string': 'Team', 'type': 'many2one'}}, fields
    related = json.load(open(os.path.join(out, 'people', 'related.json'), encoding='utf-8'))
    assert related == {'team': {'lead': {'string': 'Lead', 'type': 'char'}}}, 'the fields of each other model the views show'
    cap = json.load(open(os.path.join(out, 'CAPTURE.json'), encoding='utf-8'))
    assert cap['series'] == '17.0' and cap['modules'] == {'base': '17.0.1.3', 'web': '17.0.1.0'} and cap['at'], cap
    assert [x['type'] for x in cap['taken']] == ['list', 'search'] and cap['not_taken'][0]['model'] == 'gone', cap
    assert 'pw' not in json.dumps(cap) and r.returncode == 1 and 'gone' in r.stdout, (r.returncode, r.stdout, r.stderr)
    write = [c for c in calls if c[:2] == ('res.users', 'write')][0]
    assert write[2] == [[2], {'groups_id': [[4, 10], [4, 11]]}], write
    grp = [c for c in calls if c[:2] == ('res.groups', 'search')][0]
    assert grp[2] == [[['category_id', '!=', 77]]], grp
    r3 = subprocess.run([sys.executable, TOOL, '--url', url, '--db', 'd', '--login', 'admin', '--out', out,
                         '--model', 'people', '--type', 'search', '--lang', 'tr_TR'],
                        capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, ODOO_PASSWORD='pw'))
    tr = open(os.path.join(out, 'people', 'search.tr_TR.xml'), encoding='utf-8').read()
    assert r3.returncode == 0 and 'Kişiler' in tr and 'People' in open(os.path.join(out, 'people', 'search.xml'), encoding='utf-8').read() \
        and os.path.isfile(os.path.join(out, 'people', 'fields.tr_TR.json')), (r3.stdout, tr)
    r2 = subprocess.run([sys.executable, TOOL, '--url', url, '--db', 'd', '--login', 'admin', '--out', out, '--model', 'people'],
                        capture_output=True, text=True, encoding='utf-8', env={k: v for k, v in os.environ.items() if k != 'ODOO_PASSWORD'})
    assert r2.returncode == 2 and 'ODOO_PASSWORD' in r2.stderr, r2.stderr
    SERIES[0] = '19.0'
    calls.clear()
    out19 = os.path.join(out, 'nineteen')
    r19 = subprocess.run([sys.executable, TOOL, '--url', url, '--db', 'd', '--login', 'admin', '--out', out19,
                          '--model', 'people', '--type', 'list'],
                         capture_output=True, text=True, encoding='utf-8', env=dict(os.environ, ODOO_PASSWORD='pw'))
    assert r19.returncode == 0, ('series 19: the reading user is given its groups as 19 names them', r19.stdout, r19.stderr[-600:])
    write = [c for c in calls if c[:2] == ('res.users', 'write')][0]
    assert write[2] == [[2], {'group_ids': [[4, 10], [4, 11]]}], ('every group but the user types and what implies '
                                                                  'portal or public', write)
    cap = json.load(open(os.path.join(out19, 'CAPTURE.json'), encoding='utf-8'))
    assert cap['series'] == '19.0' and cap['taken'] == [{'model': 'people', 'type': 'list', 'view_id': 5}], cap
    assert json.load(open(os.path.join(out19, 'people', 'fields.json'), encoding='utf-8')) == {
        'name': {'string': 'Name', 'type': 'char'}}, 'the fields as 19 wraps them, unwrapped'
    print('PASS: importers/odoo/views — each view as resolved, groups taken off; the fields as described; what was read and '
          'when, no password; every group but the user types; a refused model not taken; each language asked taken in it; the other models\' fields the views show; '
          'series 19: groups as 19 names them, the user types and what implies them left out')
finally:
    shutil.rmtree(out, ignore_errors=True)
    srv.shutdown()
