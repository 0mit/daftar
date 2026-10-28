#!/usr/bin/env python3
"""A register reached by more than one route (python/register.py; internal/register keeps the routes' health): daftard
hands each call of Odoo's client the healthy routes in the order to try them, and the worker reads by them. Against
stand-in registers speaking Odoo 19's JSON-2, each of which answers, refuses the connection, resets it, takes it and
answers nothing, answers 401, or redirects:

- a read goes by the first route handed; one that fails at the connection (refused, reset, timed out) is asked once
  more, of the next route — never a third — and never where the route answered, even to refuse (401) or to redirect
  (which is not followed: the key would go where it says);
- a route that failed is not asked again in the same call; no route handed (none is healthy): refused at once, nothing
  asked; a route handed by plain HTTP beyond this machine: refused, nothing asked;
- a call waits ATTEMPT seconds on a route and BUDGET in all, at most; no proxy the environment names is used;
- what each route did goes back with the answer (`register` beside `result`): which answered, which missed and how,
  or that none was handed — never a record;
- only reads reach a register: a write asked of register.Register itself is refused and sent nowhere;
and each guard, taken out (the mutations at the end), lets its check fail.

    python3 test/worker/routes_test.py [<daftar tree>]     # a daftar tree to grow the garden from (default ~/daftar)
"""
import http.server
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
PY = os.path.join(HERE, '..', '..', 'python')
sys.path.insert(0, os.path.join(TREE, 'test'))
sys.path.insert(0, HERE)
sys.path.insert(0, PY)
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test
from odoo_worker import Worker  # noqa: E402

FAILS = []
KEY = 'k' + secrets.token_hex(20)


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + json.dumps(detail, ensure_ascii=False,
                                                                                       default=str)[-900:]))
    if not cond:
        FAILS.append(name)


class Stand:
    """A stand-in register on 127.0.0.1, in one of its modes, writing down each connection and each request."""

    def __init__(self):
        self.mode, self.connections, self.asked, self.redirect_to = 'ok', 0, [], ''
        self.sock = socket.socket()
        self.sock.bind(('127.0.0.1', 0))
        self.sock.listen(16)
        self.url = f'http://127.0.0.1:{self.sock.getsockname()[1]}'
        threading.Thread(target=self.serve, daemon=True).start()

    def serve(self):
        while True:
            try:
                c, _ = self.sock.accept()
            except OSError:
                return
            self.connections += 1
            threading.Thread(target=self.one, args=(c,), daemon=True).start()

    def one(self, c):
        with c:
            if self.mode == 'reset':                       # takes the connection and drops it
                return
            if self.mode == 'hang':                        # takes it and answers nothing
                time.sleep(20)
                return
            f = c.makefile('rb')
            head = f.readline().decode()
            headers = {}
            for line in iter(lambda: f.readline().decode(), '\r\n'):
                if not line:
                    return
                k, _, v = line.partition(':')
                headers[k.strip().lower()] = v.strip()
            body = json.loads(f.read(int(headers.get('content-length') or 0)) or b'{}')
            path = head.split()[1]
            self.asked.append({'path': path, 'auth': headers.get('authorization'), 'proxy': path.startswith('http')})
            if self.mode == '401':
                out, code = {'name': 'werkzeug.exceptions.Unauthorized', 'message': 'no key like it'}, 401
            elif self.mode == 'redirect':
                c.sendall(f'HTTP/1.1 307 Temporary Redirect\r\nLocation: {self.redirect_to}{path}\r\n'
                          'Content-Length: 0\r\nConnection: close\r\n\r\n'.encode())
                return
            else:
                model, method = path.split('/')[3:5]
                out, code = ({'suggest': [{'record': f'{model}(2,)', 'score': 1.0}],
                              'web_read': [{'id': i, 'display_name': f'Role {i}'} for i in body.get('ids') or []],
                              'search_count': 3}.get(method, [])), 200
            b = json.dumps(out).encode()
            c.sendall(f'HTTP/1.1 {code} X\r\nContent-Type: application/json\r\nContent-Length: {len(b)}\r\n'
                      'Connection: close\r\n\r\n'.encode() + b)

    def close(self):                                     # it listens no more: a connection to it is refused
        try:
            self.sock.shutdown(socket.SHUT_RDWR)             # wakes the accept that would keep the socket listening
        except OSError:
            pass
        self.sock.close()


def dead_url():
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return f'http://127.0.0.1:{port}'


T = Path(tempfile.mkdtemp(prefix='worker-routes-'))
w = None
stands = []
try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    (G / 'beans' / 'people-register.md').write_text(
        '---\nbean: people-register\nkind: instance\ntitle: "The people register"\nstatements:\n'
        '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n---\nAn invented register of people.\n',
        encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'The people register', '--body',
                 '- action: wrote [[people-register]]', cwd=str(G))
    check('a garden with its register, through its gate', r.returncode == 0 and s.returncode == 0,
          getattr(r, 'out', '')[-400:] + getattr(s, 'out', '')[-800:])
    cap = G / 'captures' / 'views' / 'odoo-19.0'
    for m, fields in (('people.person', {'name': {'type': 'char'}}),
                      ('people.role', {'name': {'type': 'char'}, 'suggest_index': {'type': 'text'}})):
        (cap / m).mkdir(parents=True, exist_ok=True)
        (cap / m / 'fields.json').write_text(json.dumps(fields), encoding='utf-8')
        (cap / m / 'list.xml').write_text(f'<list string="{m}"><field name="name"/></list>\n', encoding='utf-8')
    (cap / 'CAPTURE.json').write_text('{"series": "19.0"}\n', encoding='utf-8')
    keys = T / 'state' / 'registers'
    keys.mkdir(parents=True)
    (keys / 'g.key').write_text(KEY + '\n', encoding='utf-8')
    os.chmod(keys / 'g.key', 0o600)
    # daftard.json names the register by routes: no one url in what the worker is handed at its start
    conf = {'series': '19.0', 'url': '', 'db': 'peopledb', 'bean': 'people-register', 'key_file': str(keys / 'g.key')}
    proxy = dead_url()                                  # a proxy the environment names: never used

    def worker(mutate=None):
        return Worker(G, mutate=mutate, scratch=str(T), series='19.0', env={
            'DAFTAR_REGISTER': json.dumps(conf), 'http_proxy': proxy, 'https_proxy': proxy, 'HTTP_PROXY': proxy,
            'no_proxy': '', 'NO_PROXY': ''})

    def ask(routes, method='search_count', model='people.person', **kw):
        """One call of the client as daftard hands it, with the routes: (its answer, the routes' notes, seconds)."""
        w.n += 1
        payload = {'model': model, 'method': method, 'args': [], 'kwargs': dict(kw or {'domain': []}, context={})}
        params = {'path': f'/web/dataset/call_kw/{model}/{method}', 'reader': 'sam', 'series': '19.0', 'lang': 'en_US',
                  'payload': payload}
        if routes is not None:
            params['routes'] = routes
        t0 = time.monotonic()
        w.p.stdin.write(json.dumps({'id': w.n, 'method': 'odoo_rpc', 'params': params}) + '\n')
        w.p.stdin.flush()
        got = json.loads(w.p.stdout.readline())
        return (got.get('result') if got.get('ok') else {'error': got.get('error')}), got.get('register'), \
            time.monotonic() - t0

    def routes(*urls):
        return [{'route': i, 'url': u} for i, u in enumerate(urls, start=1)]

    def fresh(n):
        for x in stands:
            x.close()
        stands[:] = [Stand() for _ in range(n)]
        return stands

    def status(got):
        return (got.get('error') or {}).get('status') if isinstance(got, dict) else None

    w = worker()
    a, b = fresh(2)
    got, notes, _ = ask(routes(a.url, b.url))
    check('both healthy: read by the first route, and only by it', got == 3 and len(a.asked) == 1 and not b.asked
          and notes == [{'route': 1, 'answered': True}], (got, notes, a.asked, b.asked))
    check("...the account's key in its header; no proxy the environment names", bool(a.asked)
          and a.asked[0]['auth'] == 'bearer ' + KEY and not a.asked[0]['proxy'], a.asked)

    a.close()
    got, notes, _ = ask(routes(a.url, b.url))
    check('the first refuses the connection: asked once more, of the next, which answers',
          got == 3 and len(b.asked) == 1 and notes == [{'route': 1, 'missed': 'refused'}, {'route': 2, 'answered': True}],
          (got, notes))

    a, b = fresh(2)
    a.mode = 'reset'
    got, notes, _ = ask(routes(a.url, b.url), 'name_search', 'people.role', name='cook', domain=[], operator='ilike',
                        limit=8)
    check("the first drops the connection: the next answers — and the call's second read (a ranking's records) goes "
          "to it straight, the first not asked again in the call",
          got == [[2, 'Role 2']] and a.connections == 1 and [x['path'].split('/')[-1] for x in b.asked] == ['suggest', 'web_read']
          and notes == [{'route': 1, 'missed': 'reset'}, {'route': 2, 'answered': True}, {'route': 2, 'answered': True}],
          (got, notes, a.connections, b.asked))

    a, b, c = fresh(3)
    a.mode = b.mode = 'reset'
    got, notes, _ = ask(routes(a.url, b.url, c.url))
    check('two that fail at the connection: refused, said so — one retry at most, the third never asked',
          status(got) == 504 and 'did not answer by any of its routes' in json.dumps(got) and not c.connections
          and a.connections == 1 and b.connections == 1
          and notes == [{'route': 1, 'missed': 'reset'}, {'route': 2, 'missed': 'reset'}], (got, notes))

    a, b = fresh(2)
    a.mode = '401'
    got, notes, _ = ask(routes(a.url, b.url))
    check('the first answers 401: its refusal said, never asked of the next', status(got) == 401 and not b.connections
          and notes == [{'route': 1, 'answered': True}] and 'no key like it' not in json.dumps(got), (got, notes))

    a, b = fresh(2)
    a.mode, a.redirect_to = 'redirect', b.url
    got, notes, _ = ask(routes(a.url, dead_url()))
    check('the first redirects: an answer, refused as such — not followed, the key never sent where it says, and not '
          'asked of the next route', status(got) == 502 and not b.connections and notes == [{'route': 1, 'answered': True}],
          (got, notes, b.asked))

    a, b = fresh(2)
    got, notes, _ = ask([])
    check('no route handed (none is healthy): refused at once, nothing asked, daftard told',
          status(got) == 503 and 'none of its routes answers' in json.dumps(got) and not a.connections
          and notes == [{'none': True}], (got, notes))
    got, notes, _ = ask([{'route': 1, 'url': 'http://203.0.113.10:8069'}])
    check('a route by plain HTTP beyond this machine: refused, nothing sent', status(got) == 500 and notes is None, got)
    got, notes, _ = ask(None)
    check('no routes handed at all and no url: refused, nothing sent', status(got) == 500, got)
    w.close()

    # waiting: a route that takes the connection and answers nothing, with ATTEMPT and BUDGET made short
    w = worker({'register.py': ('ATTEMPT = 14 ', 'ATTEMPT = 2 ')})
    a, b = fresh(2)
    a.mode = 'hang'
    got, notes, took = ask(routes(a.url, b.url))
    check('the first hangs: the next answers after ATTEMPT, not before and not much after', got == 3
          and 2 <= took < 4 and notes == [{'route': 1, 'missed': 'timeout'}, {'route': 2, 'answered': True}],
          (got, notes, took))
    b.mode = 'hang'
    got, notes, took = ask(routes(a.url, b.url))
    check('both hang: said within twice ATTEMPT', status(got) == 504 and 4 <= took < 6
          and notes == [{'route': 1, 'missed': 'timeout'}, {'route': 2, 'missed': 'timeout'}], (got, notes, took))
    w.close()
    w = worker({'register.py': ('ATTEMPT = 14 ', 'ATTEMPT = 2 '), 'garden_worker.py': (
        "        r = register.Register(register.settings(), routes, REGISTER_NOTES)",
        "        r = register.Register(register.settings(), routes, REGISTER_NOTES)\n"
        "        r.deadline = __import__('time').monotonic() + 3.5")})
    a, b = fresh(2)
    a.mode = b.mode = 'hang'
    got, notes, took = ask(routes(a.url, b.url))
    check('...and never longer than BUDGET in all: the second route waited only what was left', status(got) == 504
          and 3.3 <= took < 4.5 and notes == [{'route': 1, 'missed': 'timeout'}, {'route': 2, 'missed': 'timeout'}],
          (got, notes, took))
    w.close()
    w = None

    # only reads reach a register: asked of register.Register itself, a write is refused and sent nowhere
    sys.path.insert(0, PY)
    import register  # noqa: E402
    a, = fresh(1)
    try:
        register.Register(conf, routes(a.url)).call('people.person', 'write', [1], vals={'name': 'x'})
        said = None
    except register.Refused as e:
        said = (str(e), e.status)
    check('a write asked of the register reader: refused, sent nowhere', said and said[1] == 501 and not a.connections,
          (said, a.connections))

    # each guard, taken out, lets its check fail
    def mutated(file, old, new, run):
        global w
        w = worker({file: (old, new)})
        try:
            return run()
        finally:
            w.close()
            w = None

    def refused_first():
        a, b = fresh(2)
        a.close()
        return ask(routes(a.url, b.url))
    got = mutated('register.py', "if r['route'] not in self.down][:2]:", "if r['route'] not in self.down][:1]:",
                  refused_first)
    check('...without the second chance, a read the next route would answer is refused', status(got[0]) == 504, got)
    def refusing_first():
        a, b = fresh(2)
        a.mode = '401'
        return ask(routes(a.url, b.url))
    got = mutated('register.py', "            raise Refused(f'the register refused the call ({refusal_kind(e)})', status) from None",
                  "            raise Unreached('refused') from None", refusing_first)
    check('...taking an HTTP refusal for no answer, the next route is asked where the first answered 401',
          got[0] == 3 and stands[1].connections == 1, got)
    a, = fresh(1)
    m = Worker(G, mutate={'register.py': ('        if method not in READS:', '        if False:')}, scratch=str(T),
               series='19.0', env={'DAFTAR_REGISTER': json.dumps(conf)})
    m.close()
    src = (Path(m.dir) / 'register.py').read_text(encoding='utf-8')
    ns = {'__name__': 'register_mutated'}
    exec(compile(src, 'register_mutated.py', 'exec'), ns)  # noqa: S102 — the module, its guard taken out
    try:
        ns['Register'](conf, routes(a.url)).call('people.person', 'write', [1], vals={'name': 'x'})
    except Exception:  # noqa: BLE001
        pass
    check("...without the reads' guard, a write reaches the register", len(a.asked) == 1 and a.asked[0]['path'].endswith(
        '/write'), a.asked)
finally:
    if w:
        w.close()
    for x in stands:
        x.close()
    shutil.rmtree(T, ignore_errors=True)
print(f"\nroutes: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
