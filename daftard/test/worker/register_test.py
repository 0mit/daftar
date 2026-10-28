#!/usr/bin/env python3
"""A register read live (design §10.2, §15.6; python/register.py): for a garden whose daftard.json names a register,
the data calls of Odoo's client are asked of the register itself, as the reader may ask them, and nothing it answers is
kept. Against a stand-in register speaking Odoo 19's JSON-2 (its records invented, every value carrying a mark):

- who may read it is the garden's own `may` on the register's bean: the gardener; a reader a grant opens it to, while
  the grant holds; nobody else — and for them nothing is asked at all;
- every domain is ANDed with the reader's grants, and every field a domain, a specification, an order, a group or an
  aggregate names is held to the fields the garden captured (a field the register has and the views do not show is
  refused, and never asked); a read with no fields asks only the captured ones;
- the context is cut to the reader's language and the garden's zone and a read's switches; the account's key goes in
  its header and the database in its own; a write, or any call not a read, is refused and never reaches the register;
  the garden's past is not the register's (as of a commit: refused);
- the register's own words in a refusal are never repeated; a key file others may read is refused; plain HTTP beyond
  this machine is refused;
- nothing the register answered is left in the garden (its working tree and every object of its history), in the
  worker's folder or in its log.
And each of these fails when its guard is taken out of the worker (the mutations at the end).

    python3 test/worker/register_test.py [<daftar tree>]     # a daftar tree to grow the garden from (default ~/daftar)
"""
import http.server
import json
import os
import secrets
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, '..', '..', 'python'))
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test
import odoo_rpc  # noqa: E402 — the stand-in register answers with daftard's own answerer over its invented records
from odoo_worker import Worker  # noqa: E402

FAILS = []
MARK = 'mk' + str(secrets.randbelow(10 ** 12)).zfill(12)   # digits: a hex marker once spelled "ada", a name searched
KEY = 'k' + secrets.token_hex(20)


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + json.dumps(detail, ensure_ascii=False,
                                                                                       default=str)[-900:]))
    if not cond:
        FAILS.append(name)


# ---- the stand-in register: Odoo 19's JSON-2 over invented records, every request it gets recorded
FIELDS = {
    'people.person': {'id': {'type': 'integer'}, 'name': {'type': 'char', 'string': 'Name'},
                      'display_name': {'type': 'char'}, 'city': {'type': 'char', 'string': 'City'},
                      'active': {'type': 'boolean'}, 'country_id': {'type': 'many2one', 'relation': 'people.country'},
                      'secret_note': {'type': 'char', 'string': 'Not shown'}},
    'people.country': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                       'code': {'type': 'char'}},
    # a model the register searches the way people type: it keeps a folded index, and ranks with its own `suggest`
    'people.role': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                    'suggest_index': {'type': 'text'}},
    # a model whose records carry 19's properties with no parent to hold their definitions (as res.partner's)
    'people.card': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                    'properties': {'type': 'properties', 'definition_record': 'properties_base_definition_id',
                                   'definition_record_field': 'properties_definition'},
                    'properties_base_definition_id': {'type': 'many2one', 'relation': 'properties.base.definition'}}}
RECORDS = {
    'people.person': [{'id': i, 'name': f'{n} {MARK}', 'display_name': f'{n} {MARK}', 'city': c, 'active': True,
                       'country_id': [k, kn], 'secret_note': f'note {MARK} {i}'}
                      for i, (n, c, k, kn) in enumerate([('Ada', 'Izmir', 1, 'Turkey'), ('Bo', 'Shiraz', 2, 'Iran'),
                                                         ('Cy', 'Izmir', 1, 'Turkey')], start=1)],
    'people.country': [{'id': 1, 'name': 'Turkey', 'display_name': 'Turkey', 'code': f'TR{MARK}'},
                       {'id': 2, 'name': 'Iran', 'display_name': 'Iran', 'code': 'IR'}],
    'people.role': [{'id': i, 'name': f'{n} {MARK}', 'display_name': f'{n} {MARK}', 'suggest_index': n.lower()}
                    for i, n in enumerate(['Cook', 'Kebab cook', 'Dishes'], start=1)]}
engine = odoo_rpc.Answerer(lambda m: RECORDS.get(m, []), lambda m: FIELDS.get(m, {}), lambda m, w: {})
asked = []


class Register(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def answer(self, code, body):
        b = json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])) or b'{}')
        _, _json, _two, model, method = self.path.split('/')
        asked.append({'model': model, 'method': method, 'body': json.loads(json.dumps(body)),
                      'auth': self.headers.get('Authorization'), 'db': self.headers.get('X-Odoo-Database')})
        if self.headers.get('Authorization') != 'bearer ' + KEY:
            return self.answer(401, {'name': 'werkzeug.exceptions.Unauthorized', 'message': 'no'})
        if any(isinstance(t, list) and t[:2] == ['city', '='] and t[2] == 'boom' for t in body.get('domain') or []):
            return self.answer(422, {'name': 'odoo.exceptions.ValidationError',
                                     'message': f'the record {MARK} cannot be read', 'arguments': [MARK]})
        ids = body.pop('ids', None)
        body.pop('context', None)
        try:
            if method == 'name_search':                  # 19's own signature
                d = body.get('domain') or []
                got = engine.search(model, d + ([('display_name', 'ilike', body['name'])] if body.get('name') else []), {})
                return self.answer(200, [[r['id'], r['display_name']] for r in got][:body.get('limit') or 100])
            if method == 'web_read_group':
                return self.answer(200, {'groups': [], 'length': 0})
            if method == 'suggest':                      # the register's own ranking: an order no ilike gives
                if body.get('query') == 'malformed':
                    return self.answer(200, [{'record': 'people.person(1,)', 'score': 1.0}])
                return self.answer(200, [{'score': 1.0, 'field': 'name', 'match': 'typo', 'record': 'people.role(3,)'},
                                         {'score': 0.6, 'field': 'name', 'match': 'partial', 'record': 'people.role(1,)'}])
            out = engine.call(model, method, [ids] if ids is not None else [], body)
        except Exception as e:  # noqa: BLE001
            return self.answer(422, {'name': type(e).__name__, 'message': f'{e} {MARK}'})
        self.answer(200, out)


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Register)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_address[1]}'

T = Path(tempfile.mkdtemp(prefix='worker-register-'))
w = None
try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    (G / 'beans' / 'people-register.md').write_text(
        '---\nbean: people-register\nkind: instance\ntitle: "The people register"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n---\nAn invented register of people.\n',
        encoding='utf-8')
    for p, name in (('ana', 'Ana'), ('bo', 'Bo'), ('cy', 'Cy')):
        (G / 'beans' / f'{p}.md').write_text(
            f'---\nbean: {p}\nkind: person\ntitle: "{name}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
            '  - own: { by: theone, of: self }\n  - answer: { by: self, of: self, as: law }\n---\n' + name + '.\n',
            encoding='utf-8')
        (G / 'beans' / f'{p}-consent.md').write_text(
            f'---\nbean: {p}-consent\nkind: contract\ntitle: "{name} agrees to be kept here by name"\nstatements:\n'
            '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
            f'  - agree: {{ id: {p}-agrees, by: {p}, of: "kept here by name", through: spoken }}\n'
            f'  - agree: {{ id: sam-agrees, by: sam, of: "kept here by name", through: spoken }}\n---\nTheir word.\n',
            encoding='utf-8')
    sam = (G / 'beans' / 'sam.md').read_text(encoding='utf-8')
    (G / 'beans' / 'sam.md').write_text(sam.replace('\n---\n', (
        '\n  - grant: { id: ana-register, by: self, as: read, of: [people-register], to: [ana] }\n'
        '  - grant: { id: cy-register, by: self, as: read, of: [people-register], to: [cy], at: "2026-01-01/2026-02-01" }\n'
        '  - say: { by: sam, of: [ana-register, cy-register], at: now }\n---\n'), 1), encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'The people register, and who may read it', '--body',
                 '- action: wrote [[people-register]], [[ana]], [[bo]] and [[cy]] (each kept on their word, [[ana-consent]], '
                 '[[bo-consent]], [[cy-consent]]); [[sam]] opens the register to Ana, and to Cy for January 2026', cwd=str(G))
    check('the garden holds the register, three readers, and its grants, through its gate',
          r.returncode == 0 and s.returncode == 0, getattr(r, 'out', '')[-400:] + getattr(s, 'out', '')[-1200:])
    # what the garden captured of the register's models: the views show people's name, city and country, not the note
    cap = G / 'captures' / 'views' / 'odoo-19.0'
    for m, f in (('people.person', ['name', 'city', 'active', 'country_id']), ('people.country', ['name']),
                 ('people.role', ['name', 'suggest_index']),
                 ('people.card', ['name', 'properties', 'properties_base_definition_id'])):
        (cap / m).mkdir(parents=True, exist_ok=True)
        (cap / m / 'fields.json').write_text(json.dumps({k: FIELDS[m][k] for k in f}), encoding='utf-8')
        (cap / m / 'list.xml').write_text(f'<list string="{m}">' + ''.join(f'<field name="{k}"/>' for k in f) + '</list>\n',
                                          encoding='utf-8')
    (cap / 'CAPTURE.json').write_text('{"series": "19.0"}\n', encoding='utf-8')
    ZONE = next(ln.split(':', 1)[1].split('#')[0].strip().strip('"')
                for ln in (G / 'GARDEN.md').read_text(encoding='utf-8').splitlines() if ln.startswith('zone:'))
    CLIENT_ZONE = 'America/Lima' if ZONE != 'America/Lima' else 'Asia/Tokyo'      # never the garden's own
    keys = T / 'state' / 'registers'
    keys.mkdir(parents=True)
    (keys / 'g.key').write_text(KEY + '\n', encoding='utf-8')
    os.chmod(keys / 'g.key', 0o600)
    conf = {'series': '19.0', 'url': URL, 'db': 'peopledb', 'bean': 'people-register', 'key_file': str(keys / 'g.key')}
    log = open(T / 'worker.log', 'w', encoding='utf-8')

    def worker(mutate=None, c=None):
        return Worker(G, mutate=mutate, scratch=str(T), series='19.0', env={'DAFTAR_REGISTER': json.dumps(c or conf)},
                      stderr=None if log.closed else log)
    w = worker()
    P = 'people.person'
    SPEC = {'name': {}, 'city': {}, 'country_id': {'fields': {'display_name': {}}}}
    CLIENT_CTX = {'lang': 'fa_IR', 'tz': CLIENT_ZONE, 'uid': 2, 'allowed_company_ids': [1], 'bin_size': True,
                  'junk': 'not for the register'}

    def ask(reader, method, args=(), lang='fa_IR', asof=None, model=None, **kw):
        n, m = len(asked), model or P
        got = w.rpc(reader, f'/web/dataset/call_kw/{m}/{method}', {'model': m, 'method': method, 'args': list(args),
                    'kwargs': dict(kw, context=CLIENT_CTX)}, asof=asof, lang=lang)
        return got, asked[n:]

    got, sent = ask('ana', 'web_search_read', domain=[('city', '=', 'Izmir')], specification=SPEC, limit=80)
    check('a reader the register is open to reads its records, asked of it live',
          isinstance(got, dict) and sorted(x['name'] for x in got.get('records', [])) == [f'Ada {MARK}', f'Cy {MARK}']
          and got['records'][0]['country_id'] == {'id': 1, 'display_name': 'Turkey'}, got)
    b = sent[0]['body'] if sent else {}
    check('...by one JSON-2 call: the domain the grants and the client make, the specification as asked',
          len(sent) == 1 and sent[0]['method'] == 'web_search_read' and b.get('domain') == [['city', '=', 'Izmir']]
          and b.get('specification') == {'name': {}, 'city': {}, 'country_id': {'fields': {'display_name': {}}}}, sent)
    check("...the context cut to the reader's language and the garden's zone and a read's switch, nothing else",
          b.get('context') == {'lang': 'fa_IR', 'tz': ZONE, 'bin_size': True}, (b.get('context'), ZONE))
    check("...the account's key in its header, the database in its own", sent and sent[0]['auth'] == 'bearer ' + KEY
          and sent[0]['db'] == 'peopledb', sent and {k: sent[0][k] != None for k in ('auth', 'db')})  # noqa: E711
    for who, why in (('bo', 'a reader no grant opens it to'), ('cy', 'a reader whose grant has ended'),
                     ('nobody', 'a reader the garden does not name'), ('../sam', 'a reader that is no name')):
        got, sent = ask(who, 'web_search_read', domain=[], specification={'name': {}})
        check(f'{why}: refused, and nothing is asked of the register', isinstance(got, dict) and 'error' in got
              and got['error'].get('status') == 403 and not sent, (got, sent))
    got, sent = ask('sam', 'search_count', [[]])
    check('the gardener reads it with no grant', got == 3 and len(sent) == 1, (got, sent))
    for what, kw in (("a domain on a field the garden's views do not show", {'domain': [('secret_note', 'ilike', 'x')]}),
                     ('...through a relation to such a field', {'domain': [('country_id.code', '=', 'TR')]}),
                     ("...inside an `any`", {'domain': [('country_id', 'any', [('code', '=', 'TR')])]}),
                     ('a specification naming one', {'domain': [], 'specification': {'secret_note': {}}}),
                     ("...in a relation's own", {'domain': [], 'specification': {'country_id': {'fields': {'code': {}}}}}),
                     ('an order by one', {'domain': [], 'specification': {'name': {}}, 'order': 'secret_note desc'})):
        got, sent = ask('ana', 'web_search_read', **kw)
        check(f'{what}: refused, never asked', isinstance(got, dict) and got.get('error', {}).get('status') == 403
              and not sent, (got, sent))
    for what, method, kw in (('a group by one', 'web_read_group', {'domain': [], 'groupby': ['secret_note']}),
                             ('an aggregate of one', 'web_read_group', {'domain': [], 'groupby': ['city'],
                                                                         'aggregates': ['secret_note:count']})):
        got, sent = ask('ana', method, **kw)
        check(f'{what}: refused, never asked', isinstance(got, dict) and got.get('error', {}).get('status') == 403
              and not sent, (got, sent))
    got, sent = ask('ana', 'web_read_group', domain=[('active', '=', True)], groupby=['city'], aggregates=['__count'],
                    auto_unfold=True, unfold_read_specification={'name': {}})
    check("19's group read, asked with its own named arguments", isinstance(got, dict) and len(sent) == 1
          and sent[0]['body'].get('groupby') == ['city'] and sent[0]['body'].get('auto_unfold') is True
          and sent[0]['body'].get('unfold_read_specification') == {'name': {}}, (got, sent))
    got, sent = ask('ana', 'read', [[1]])
    check('a read naming no fields asks only the fields the garden captured', isinstance(got, list) and len(sent) == 1
          and sent[0]['body'].get('ids') == [1] and sorted(sent[0]['body'].get('fields') or []) ==
          ['active', 'city', 'country_id', 'name'] and 'secret_note' not in got[0], (got, sent))
    got, sent = ask('ana', 'web_read', [[2]], specification={'name': {}})
    check('a form\'s read: its ids, its specification', isinstance(got, list) and got[0]['name'] == f'Bo {MARK}'
          and sent[0]['body'].get('ids') == [2], (got, sent))
    got, sent = ask('ana', 'name_search', name='Ada', domain=[], operator='ilike', limit=8)
    check("a many2one's suggestions, by 19's own name_search", got == [[1, f'Ada {MARK}']] and len(sent) == 1
          and sent[0]['body'].get('domain') == [], (got, sent))
    got, sent = ask('ana', 'search_panel_select_range', ['country_id'], search_domain=[('city', '=', 'Izmir')],
                    enable_counters=True, expand=False)
    check("the search panel: its base domain ANDed with the grants", len(sent) == 1
          and sent[0]['body'].get('search_domain') == [['city', '=', 'Izmir']], (got, sent))
    R = 'people.role'
    got, sent = ask('ana', 'name_search', model=R, name='kebap', domain=[], operator='ilike', limit=8)
    check("a many2one's suggestions of a model the register ranks: the register's own ranking, in its order",
          got == [[3, f'Dishes {MARK}'], [1, f'Cook {MARK}']], got)
    check("...asked of its own `suggest`, the reader's grants ANDed into its domain, then read by their ids",
          [x['method'] for x in sent] == ['suggest', 'web_read'] and sent[0]['body'].get('query') == 'kebap'
          and sent[0]['body'].get('domain') == [] and sent[1]['body'].get('ids') == [3, 1], sent)
    got, sent = ask('ana', 'web_name_search', model=R, name='kebap', specification={'display_name': {}}, domain=[],
                    operator='ilike', limit=8)
    check("19's web_name_search, the same ranking", [x['id'] for x in got] == [3, 1]
          and got[0].get('__formatted_display_name') == f'Dishes {MARK}', got)
    got, sent = ask('ana', 'name_search', model=R, name='malformed', domain=[], operator='ilike', limit=8)
    check('a ranking in a shape daftard does not read (another model\'s record): refused',
          isinstance(got, dict) and got.get('error', {}).get('status') == 502, got)
    got, sent = ask('ana', 'name_search', model=R, name='Cook', domain=[], operator='=', limit=8)
    check('another operator than ilike: the plain name_search', [x['method'] for x in sent] == ['name_search'], sent)
    got, sent = ask('ana', 'name_search', name='Ada', domain=[], operator='ilike', limit=8)
    check('a model the register does not rank: the plain name_search', [x['method'] for x in sent] == ['name_search'], sent)
    bo_ = ask('bo', 'name_search', model=R, name='kebap', domain=[], operator='ilike', limit=8)
    check('...and the ranking too is closed to a reader no grant opens it to', isinstance(bo_[0], dict)
          and bo_[0].get('error', {}).get('status') == 403 and not bo_[1], bo_)
    for method in ('write', 'unlink', 'create', 'web_save', 'onchange', 'action_archive', 'copy'):
        got, sent = ask('ana', method, [[1]], vals={'name': 'x'})
        check(f'{method}: refused, never reaching the register', isinstance(got, dict) and 'error' in got and not sent,
              (got, sent))
    got, sent = ask('ana', 'get_properties_base_definition', ['people.card', 'properties'],
                    model='properties.base.definition')
    check("a properties field's definitions (19's search editor asks them): none, answered here, nothing asked of the "
          "register", got == {'length': 0, 'records': []} and not sent, (got, sent))
    n = len(asked)                                       # a form's button: Odoo's client calls it by its own path
    got = w.rpc('ana', f'/web/dataset/call_button/{P}/action_archive', {'model': P, 'method': 'action_archive',
                'args': [[1]], 'kwargs': {'context': CLIENT_CTX}}, lang='fa_IR')
    check("a form's button: refused as the register's writes are, said so, never reaching the register",
          isinstance(got, dict) and got.get('error', {}).get('status') == 501 and 'writes nothing' in json.dumps(got)
          and len(asked) == n, got)
    got, sent = ask('ana', 'web_search_read', asof='c' * 40, domain=[], specification={'name': {}})
    check("as of a commit of the garden: refused, the register's past is not in the garden",
          isinstance(got, dict) and got.get('error', {}).get('status') in (404, 409) and not sent, (got, sent))
    got, sent = ask('ana', 'web_search_read', domain=[('city', '=', 'boom')], specification={'name': {}})
    check("the register's refusal: said, with the kind of its exception, never its own words",
          isinstance(got, dict) and 'error' in got and MARK not in json.dumps(got) and 'ValidationError' in json.dumps(got),
          got)
    os.chmod(keys / 'g.key', 0o644)
    got, sent = ask('ana', 'web_search_read', domain=[], specification={'name': {}})
    os.chmod(keys / 'g.key', 0o600)
    check('a key file others may read: refused, nothing asked', isinstance(got, dict) and 'error' in got and not sent,
          (got, sent))
    w.close()
    w = worker(c=dict(conf, url='http://203.0.113.10:8069'))
    got, sent = ask('ana', 'web_search_read', domain=[], specification={'name': {}})
    check('plain HTTP beyond this machine: refused, nothing sent', isinstance(got, dict) and 'error' in got and not sent,
          (got, sent))
    w.close()
    w = None
    log.close()
    # nothing the register answered is left: the garden (its working tree, every object of its history), the
    # worker's folders and its log
    found = []
    for f in [p for p in T.rglob('*') if p.is_file() and 'release' not in p.parts]:
        try:
            if MARK.encode() in f.read_bytes():
                found.append(str(f.relative_to(T)))
        except OSError:
            pass
    objs = subprocess.run(['git', 'cat-file', '--batch-all-objects', '--batch'], cwd=G, capture_output=True).stdout
    check('nothing the register answered is in the garden, its history, the worker\'s folder or its log',
          not found and MARK.encode() not in objs, found)

    # each guard, taken out of the worker, lets its check fail
    def mutated(file, old, new, run):
        global w
        w = worker(mutate={file: (old, new)})
        try:
            return run()
        finally:
            w.close()
            w = None
    got = mutated('garden_worker.py', "open_ = bool(PERSON.fullmatch(reader or '')) and _may(reader, 'read', r.bean).granted",
                  'open_ = True', lambda: ask('bo', 'web_search_read', domain=[], specification={'name': {}}))
    check('...without the grant check, a reader no grant opens it to reads it (the check above would fail)',
          isinstance(got[0], dict) and 'records' in got[0], got)
    got = mutated('register.py', "if not FIELD.fullmatch(str(name)) or name not in self.allowed(model):",
                  "if not FIELD.fullmatch(str(name)):",
                  lambda: ask('ana', 'web_search_read', domain=[], specification={'secret_note': {}}))
    check("...without the captured fields' check, the note the views do not show is read",
          isinstance(got[0], dict) and MARK in json.dumps(got[0].get('records')), got)
    got = mutated('register.py', "ctx = self.context(kw.pop('context', None))", "ctx = kw.pop('context', None) or {}",
                  lambda: ask('ana', 'search_count', [[]]))
    check("...without the context cut, the client's own context reaches the register",
          got[1] and 'junk' in got[1][0]['body'].get('context', {}), got)
    got = mutated('register.py', "    return kind_of(got) or str(e.code)", "    return json.dumps(got)",
                  lambda: ask('ana', 'web_search_read', domain=[('city', '=', 'boom')], specification={'name': {}}))
    check("...repeating the register's words, a value of its records reaches the reader's error",
          MARK in json.dumps(got[0]), got)
    got = mutated('register.py', "        if method in ('name_search', 'web_name_search') and self.ranks(model, named):",
                  "        if False:", lambda: ask('ana', 'name_search', model=R, name='kebap', domain=[], operator='ilike',
                                                    limit=8))
    check("...without the register's own ranking, a plain ilike: nothing found for what was typed",
          got[0] != [[3, f'Dishes {MARK}'], [1, f'Cook {MARK}']], got)
    got = mutated('register.py', "        if method in ('read', 'search_read'):", "        if False:",
                  lambda: ask('ana', 'read', [[1]]))
    check("...asking a read with no fields as it came, the register answers every field, the note included",
          isinstance(got[0], list) and 'secret_note' in got[0][0], got)
finally:
    if w:
        w.close()
    srv.shutdown()
    shutil.rmtree(T, ignore_errors=True)
print(f"\nregister: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
