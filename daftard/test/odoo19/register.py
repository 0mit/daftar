#!/usr/bin/env python3
"""register — a real Odoo 19 Community instance read as a garden's register, live, through daftard (design §10.2,
§15.6; python/register.py), and nothing of it kept.

    ODOO_PASSWORD=<admin's> python3 test/odoo19/register.py --url http://127.0.0.1:<port> --db <db> --login admin \\
        --tree <daftar tree>

On the instance (a throwaway; it only adds what a register's keeper would): an internal account of its own, which reads
and is given nothing else, and that account's API key, made as Odoo makes one (its own session, its identity checked);
invented records whose every name carries a mark (test/odoo19/invented.py --mark). Then a garden of the core, grown from
the daftar tree, with the register's bean and a grant of it, its captures of Odoo's own models written from the
instance's own description of them; and daftard, built from this tree, serving it, the key in its state folder.

- **Through daftard** (its door, the seat on Odoo's origin, the worker): the gardener's calls are answered by the
  register — the list, a read, a many2one's suggestions, 19's group read, the search panel — each equal to what the
  account itself is answered by JSON-2 for the same call; a field the garden did not capture is refused.
- **As the garden's readers** (the worker as daftard runs it): a reader the grant opens it to reads it; one it does not,
  nothing, and nothing is asked.
- **Nothing kept**: no mark of a record and not the key in daftard's state folder (its log, its errors), in the garden
  (its working tree and every object of its history) or in the scratch the run used — the key's own file aside.
"""
import argparse
import http.cookiejar
import itertools
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
ap = argparse.ArgumentParser()
ap.add_argument('--url', required=True)
ap.add_argument('--db', required=True)
ap.add_argument('--login', required=True)
ap.add_argument('--tree', required=True)
a = ap.parse_args()
URL = a.url.rstrip('/')
MARK = 'mk' + secrets.token_hex(6)
FAILS = []
sys.path.insert(0, os.path.join(a.tree, 'test'))
sys.path.insert(0, str(REPO / 'test' / 'worker'))
import grow  # noqa: E402
from odoo_worker import Worker  # noqa: E402


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + json.dumps(detail, ensure_ascii=False,
                                                                                       default=str)[-900:]))
    if not cond:
        FAILS.append(name)


class Session:
    """A session on the instance, as its own web client has one."""

    def __init__(self, login, password):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.seq = itertools.count(1)
        got = self.post('/web/session/authenticate', {'db': a.db, 'login': login, 'password': password})
        if not (got or {}).get('uid'):
            raise SystemExit(f'register: the instance refused the login {login}')
        self.uid = got['uid']

    def post(self, path, params):
        body = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': next(self.seq), 'params': params}).encode()
        got = json.loads(self.op.open(urllib.request.Request(URL + path, body, {'Content-Type': 'application/json'}),
                                      timeout=120).read())
        if got.get('error'):
            raise RuntimeError(json.dumps(got['error'].get('data', {}).get('message') or got['error'])[:500])
        return got.get('result')

    def kw(self, model, method, args=(), **kw):
        return self.post(f'/web/dataset/call_kw/{model}/{method}', {'model': model, 'method': method, 'args': list(args),
                                                                    'kwargs': kw})


def json2(key, model, method, **body):
    req = urllib.request.Request(f'{URL}/json/2/{model}/{method}', json.dumps(body).encode(), {
        'Content-Type': 'application/json', 'Authorization': 'bearer ' + key, 'X-Odoo-Database': a.db})
    return json.loads(urllib.request.urlopen(req, timeout=120).read())


T = Path(tempfile.mkdtemp(prefix='odoo19-register-'))
os.environ['TMPDIR'] = str(T / 'tmp')
(T / 'tmp').mkdir()
daftard = None
try:
    # ---- on the instance: the register's account, its key, and invented records with the mark
    admin = Session(a.login, os.environ['ODOO_PASSWORD'])
    login, pw = 'daftard-register-test', secrets.token_urlsafe(18)
    gu = admin.kw('ir.model.data', 'search_read', [], domain=[('module', '=', 'base'), ('name', '=', 'group_user')],
                  fields=['res_id'])[0]['res_id']
    found = admin.kw('res.users', 'search', [], domain=[('login', '=', login)], context={'active_test': False})
    if found:
        admin.kw('res.users', 'write', [found, {'password': pw, 'active': True}])
    else:
        admin.kw('res.users', 'create', [{'name': 'daftard register reader (test)', 'login': login, 'password': pw,
                                          'group_ids': [(6, 0, [gu])]}])
    me = Session(login, pw)                                # its key, made in its own session, its identity checked
    desc = me.kw('res.users.apikeys.description', 'create', [{'name': 'daftard register test'}])
    act = me.kw('res.users.apikeys.description', 'make_key', [[desc]])
    if act.get('res_model') == 'res.users.identitycheck':
        act = me.kw('res.users.identitycheck', 'run_check', [[act['res_id']]], context={'password': pw})
    KEY = (act.get('context') or {}).get('default_key')
    check("the register's account has its own API key, made as Odoo makes one", isinstance(KEY, str) and len(KEY) > 20,
          sorted(act))
    made = json.loads(subprocess.run([sys.executable, str(HERE / 'invented.py'), '--url', URL, '--db', a.db, '--login',
                                      a.login, '--mark', MARK], capture_output=True, text=True, check=True).stdout)
    check('invented records with the mark', len(made['people']) == 6, made)

    # ---- the garden: the register's bean, a grant of it, and what it captured of Odoo's own models
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam')
    (G / 'beans' / 'register.md').write_text(
        '---\nbean: register\nkind: instance\ntitle: "The register"\nstatements:\n  - say: { by: sam, at: now }\n'
        '  - own: { by: sam, of: self }\n---\nAn Odoo instance read live.\n', encoding='utf-8')
    for p, n in (('ana', 'Ana'), ('bo', 'Bo')):
        (G / 'beans' / f'{p}.md').write_text(
            f'---\nbean: {p}\nkind: person\ntitle: "{n}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
            '  - own: { by: theone, of: self }\n  - answer: { by: self, of: self, as: law }\n---\n' + n + '.\n',
            encoding='utf-8')
        (G / 'beans' / f'{p}-consent.md').write_text(
            f'---\nbean: {p}-consent\nkind: contract\ntitle: "{n} agrees to be kept here by name"\nstatements:\n'
            '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
            f'  - agree: {{ id: {p}-agrees, by: {p}, of: "kept here by name", through: spoken }}\n'
            f'  - agree: {{ id: sam-agrees, by: sam, of: "kept here by name", through: spoken }}\n---\nTheir word.\n',
            encoding='utf-8')
    sam = (G / 'beans' / 'sam.md').read_text(encoding='utf-8')
    (G / 'beans' / 'sam.md').write_text(sam.replace('\n---\n', '\n  - grant: { id: ana-register, by: self, as: read, '
                                                    'of: [register], to: [ana] }\n  - say: { by: sam, of: [ana-register], '
                                                    'at: now }\n---\n', 1), encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'The register, and Ana reading it', '--body',
                 '- action: wrote [[register]], [[ana]] and [[bo]] (on their word, [[ana-consent]], [[bo-consent]]); '
                 '[[sam]] opens the register to Ana', cwd=str(G))
    check('the garden, through its gate', s.returncode == 0, getattr(s, 'out', '')[-800:])
    cap = G / 'captures' / 'views' / 'odoo-19.0'
    shown = {'res.partner': ['name', 'country_id', 'type', 'parent_id', 'category_id', 'is_company', 'active', 'properties',
                             'properties_base_definition_id'],
             'res.country': ['name', 'code'], 'res.partner.category': ['name']}
    for m, names in shown.items():                        # a capture of the views' fields, as the instance describes them
        desc = admin.kw(m, 'fields_get', [names])
        (cap / m).mkdir(parents=True, exist_ok=True)
        (cap / m / 'fields.json').write_text(json.dumps(desc), encoding='utf-8')
        (cap / m / 'list.xml').write_text(f'<list string="{m}">' + ''.join(f'<field name="{n}"/>' for n in names)
                                          + '</list>\n', encoding='utf-8')
    (cap / 'CAPTURE.json').write_text('{"series": "19.0"}\n', encoding='utf-8')

    # ---- daftard from this tree, serving the garden, the register named, its key in the state folder
    state = T / 'state'
    (state / 'registers').mkdir(parents=True)
    (state / 'registers' / 'g.key').write_text(KEY + '\n', encoding='utf-8')
    os.chmod(state / 'registers' / 'g.key', 0o600)
    (state / 'odoo' / '19.0').mkdir(parents=True)
    (state / 'odoo' / '19.0' / 'CLIENT.json').write_text('{}', encoding='utf-8')

    def free():
        s_ = socket.socket()
        s_.bind(('127.0.0.1', 0))
        p_ = s_.getsockname()[1]
        s_.close()
        return p_
    port, oport = free(), free()
    reg = {'series': '19.0', 'url': URL, 'db': a.db, 'bean': 'register'}
    (state / 'daftard.json').write_text(json.dumps({'listen': f'127.0.0.1:{port}', 'odoo_listen': f'127.0.0.1:{oport}',
        'gardens': [{'name': 'g', 'path': str(G), 'python': sys.executable, 'title': 'g', 'kind': 'core', 'lang': 'en',
                     'gardener': 'sam', 'register': reg}]}), encoding='utf-8')
    subprocess.run(['go', 'build', '-o', str(T / 'daftard'), './cmd/daftard'], cwd=REPO, check=True)
    daftard = subprocess.Popen([str(T / 'daftard'), 'serve'], env=dict(os.environ, DAFTARD_NOTIFY='off', DAFTARD_STATE=str(state),
                               PYTHONDONTWRITEBYTECODE='1'), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    base = f'http://127.0.0.1:{port}'
    for _ in range(300):
        try:
            if urllib.request.urlopen(base + '/health', timeout=2).status == 200:
                break
        except OSError:
            time.sleep(0.1)
    machine_key = (state / 'key').read_text().strip()
    jar = http.cookiejar.CookieJar()
    web = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    once = json.loads(web.open(urllib.request.Request(base + '/door', b'', {'X-Daftard-Key': machine_key})).read())['once']
    web.open(f'{base}/?once={once}&to=' + urllib.request.quote('/odoo?g=g&series=19.0', safe=''))  # to Odoo's origin
    origin = f'http://localhost:{oport}'

    def through(model, method, args=(), **kw):
        body = json.dumps({'jsonrpc': '2.0', 'id': 1, 'method': 'call', 'params': {
            'model': model, 'method': method, 'args': list(args), 'kwargs': dict(kw, context={'lang': 'en_US'})}}).encode()
        got = json.loads(web.open(urllib.request.Request(f'{origin}/web/dataset/call_kw/{model}/{method}', body, {
            'Content-Type': 'application/json', 'Origin': origin})).read())
        return got.get('result', got.get('error'))

    P = 'res.partner'
    spec = {'name': {}, 'country_id': {'fields': {'display_name': {}}}, 'type': {}, 'category_id': {'fields': {'display_name': {}}}}
    dom = [('name', 'ilike', MARK)]
    for what, model, method, args, kw in (
            ('the list', P, 'web_search_read', (), {'domain': dom, 'specification': spec, 'limit': 80, 'order': 'name'}),
            ('a read', P, 'web_read', ([made['people'][0]],), {'specification': spec}),
            ("a many2one's suggestions", P, 'name_search', (), {'name': MARK, 'domain': [], 'operator': 'ilike', 'limit': 8}),
            ("19's group read", P, 'web_read_group', (), {'domain': dom, 'groupby': ['country_id'], 'aggregates': ['__count'],
                                                          'auto_unfold': True, 'unfold_read_specification': {'name': {}}}),
            ('the search panel', P, 'search_panel_select_range', ('country_id',), {'search_domain': dom,
                                                                                   'enable_counters': True})):
        got = through(model, method, args, **kw)
        want = json2(KEY, model, method, **({'ids': list(args[0])} if method == 'web_read' else
                                            {'field_name': args[0]} if args else {}), **kw, context={'lang': 'en_US'})
        marked = MARK in json.dumps(got) if method != 'search_panel_select_range' else \
            sum(v.get('__count', 0) for v in (got or {}).get('values', [])) == 8     # the panel counts them, by country
        check(f"through daftard, {what}: the register's own answer", got == want and marked, (got, want))
    got = through('properties.base.definition', 'get_properties_base_definition', [P, 'properties'])
    want = json2(KEY, 'properties.base.definition', 'get_properties_base_definition', model_name=P, field_name='properties')
    defs = [d for r in want.get('records', []) for d in r.get('properties_definition') or []]
    check("res.partner's property definitions (19's search editor asks them): none, answered by daftard and not asked "
          "of the register" + ('' if not defs else f' — the register defines {len(defs)}, which daftard offers none of'),
          got == {'length': 0, 'records': []} and isinstance(want, dict), (got, want))
    got = through(P, 'web_search_read', domain=[('email', 'ilike', 'x')], specification={'name': {}})
    check('a field the garden did not capture: refused', isinstance(got, dict) and 'not a field' in json.dumps(got), got)

    w = Worker(G, series='19.0', scratch=str(T), env={'DAFTAR_REGISTER': json.dumps(dict(reg, key_file=str(
        state / 'registers' / 'g.key')))})
    try:
        ana = w.kw('ana', P, 'search_count', [dom])
        bo = w.kw('bo', P, 'search_count', [dom])
        check('a reader the grant opens it to reads it; one it does not, nothing',
              ana == 8 and isinstance(bo, dict) and bo.get('error', {}).get('status') == 403, (ana, bo))
    finally:
        w.close()
    daftard.terminate()
    daftard.wait(timeout=30)
    daftard = None
    hits = []
    for f in [p for p in T.rglob('*') if p.is_file() and 'release' not in p.parts and p.name != 'g.key'
              and p.name != 'daftard']:
        try:
            b = f.read_bytes()
        except OSError:
            continue
        if MARK.encode() in b or KEY.encode() in b:
            hits.append(str(f.relative_to(T)))
    objs = subprocess.run(['git', 'cat-file', '--batch-all-objects', '--batch'], cwd=G, capture_output=True).stdout
    check("nothing of the register's records, and not its key, in daftard's state, the garden or the run's scratch",
          not hits and MARK.encode() not in objs and KEY.encode() not in objs, hits)
finally:
    if daftard:
        daftard.kill()
    shutil.rmtree(T, ignore_errors=True)
print(f"\nregister (live): {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
