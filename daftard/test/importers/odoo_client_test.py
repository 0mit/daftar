#!/usr/bin/env python3
"""importers/odoo/client.py against a stand-in Odoo (an HTTP server playing the routes it asks), as series 17 and as
series 19 answer them: the client's bundle and every file its stylesheets name, Odoo's translations of it from each
series' own address (19 has no path segment, and answers the old one 404), and from 19 the bundles its client loads
only when a page needs one (their definitions and files) and what each kind of view is called in each language; and
CLIENT.json saying what was taken, holding no password.

    python3 test/importers/odoo_client_test.py
"""
import http.server
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(HERE, '..', '..', 'importers', 'odoo', 'client.py')
SERIES = [17]
VIEW_INFO = {'en_US': {'list': {'display_name': 'List', 'icon': 'oi oi-view-list', 'multi_record': True}},
             'fa_IR': {'list': {'display_name': 'فهرست', 'icon': 'oi oi-view-list', 'multi_record': True}}}
FILES = {'/web/assets/debug/web.assets_web.js': b'console.log("web")',
         '/web/assets/debug/web.assets_web.css': b'a{background:url(/web/static/img/a.png)}',
         '/web/assets/debug/web.assets_web.rtl.css': b'a{background:url("/web/static/img/a.png")}',
         '/web/static/img/a.png': b'\x89PNG',
         '/web/assets/debug/web.assets_emoji.js': b'console.log("emoji")',
         '/web/assets/debug/web.chartjs_lib.js': b'console.log("chart")',
         '/web/assets/debug/web.fullcalendar_lib.css': b'b{background:url(/web/static/img/b.svg)}',
         '/web/static/img/b.svg': b'<svg/>'}
BUNDLES = {'web.assets_emoji': [{'type': 'script', 'src': '/web/assets/debug/web.assets_emoji.js'}],
           'web.chartjs_lib': [{'type': 'script', 'src': '/web/assets/debug/web.chartjs_lib.js'}],
           'web.fullcalendar_lib': [{'type': 'link', 'src': '/web/assets/debug/web.fullcalendar_lib.css'}],
           'web.ace_lib': [], 'web_tour.interactive': []}
asked = []


class Odoo(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype='application/json'):
        b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(b)))
        if self.path == '/web/session/authenticate':
            self.send_header('Set-Cookie', 'session_id=s; Path=/')
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urllib.parse.urlsplit(self.path)
        q = dict(urllib.parse.parse_qsl(u.query))
        asked.append(u.path)
        if u.path in FILES:
            return self.send(200, FILES[u.path], 'application/octet-stream')
        lang_route = '/web/webclient/translations' if SERIES[0] >= 19 else '/web/webclient/translations/daftar'
        if u.path == lang_route:
            return self.send(200, {'lang': q.get('lang'), 'lang_parameters': {'code': q.get('lang'), 'direction': 'rtl'},
                                   'modules': {'web': {'messages': [{'id': 'List', 'string': 'فهرست'}]}}})
        if SERIES[0] >= 19 and u.path.startswith('/web/bundle/') and q.get('debug') == 'assets':
            name = u.path[len('/web/bundle/'):]
            if name in BUNDLES:
                return self.send(200, BUNDLES[name])
        self.send(404, b'not found', 'text/plain')

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
        p = body.get('params') or {}
        asked.append(self.path)
        if self.path == '/web/session/authenticate':
            ok = (p.get('db'), p.get('login'), p.get('password')) == ('d', 'admin', 'pw')
            v = [SERIES[0], 0, 0, 'final', 0, '']
            return self.send(200, {'result': {'uid': 2, 'server_version': f'{SERIES[0]}.0', 'server_version_info': v}
                                   if ok else {}})
        if self.headers.get('Cookie') != 'session_id=s':
            return self.send(200, {'error': {'message': 'Session expired'}})
        if self.path.startswith('/web/dataset/call_kw'):
            if (p.get('model'), p.get('method')) == ('ir.module.module', 'search_read'):
                return self.send(200, {'result': [{'name': 'web', 'installed_version': f'{SERIES[0]}.0.1.0'}]})
            if SERIES[0] >= 19 and (p.get('model'), p.get('method'), p.get('args')) == ('ir.ui.view', 'get_view_info', [[]]):
                return self.send(200, {'result': VIEW_INFO[p['kwargs']['context']['lang']]})
        self.send(200, {'error': {'message': 'not here', 'data': {'message': 'not here'}}})


srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Odoo)
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f'http://127.0.0.1:{srv.server_address[1]}'
out = tempfile.mkdtemp(prefix='odoo-client-')


def run(series, dest):
    SERIES[0] = series
    asked.clear()
    return subprocess.run([sys.executable, TOOL, '--url', url, '--db', 'd', '--login', 'admin', '--out', dest,
                           '--lang', 'fa_IR'], capture_output=True, text=True, encoding='utf-8',
                          env=dict(os.environ, ODOO_PASSWORD='pw'))


try:
    seventeen = os.path.join(out, '17.0')
    r = run(17, seventeen)
    assert r.returncode == 0, ('series 17', r.stdout, r.stderr[-800:])
    c = json.load(open(os.path.join(seventeen, 'CLIENT.json'), encoding='utf-8'))
    assert set(c['files']) == {'/web/assets/debug/web.assets_web.js', '/web/assets/debug/web.assets_web.css',
                               '/web/assets/debug/web.assets_web.rtl.css', '/web/static/img/a.png',
                               '/translations/fa_IR.json'}, ('17: the bundle, what its sheets name, the translations', c['files'])
    assert c['languages'] == {'fa_IR': 'rtl'} and 'bundles' not in c and 'view_info' not in c, c
    assert '/web/webclient/translations/daftar' in asked and not any(a.startswith('/web/bundle/') for a in asked), asked
    assert 'pw' not in json.dumps(c), 'no password in what was written'

    nineteen = os.path.join(out, '19.0')
    r = run(19, nineteen)
    assert r.returncode == 0, ('series 19: everything taken', r.stdout, r.stderr[-800:])
    c = json.load(open(os.path.join(nineteen, 'CLIENT.json'), encoding='utf-8'))
    tr = json.load(open(os.path.join(nineteen, 'translations', 'fa_IR.json'), encoding='utf-8'))
    assert tr['lang_parameters']['code'] == 'fa_IR' and c['languages'] == {'fa_IR': 'rtl'}, \
        ("19: the translations from 19's own address", c['languages'])
    assert c['bundles'] == {'web.assets_emoji': ['/web/assets/debug/web.assets_emoji.js'],
                            'web.chartjs_lib': ['/web/assets/debug/web.chartjs_lib.js'],
                            'web.fullcalendar_lib': ['/web/assets/debug/web.fullcalendar_lib.css'],
                            'web.ace_lib': [], 'web_tour.interactive': []}, ('19: the lazy bundles', c['bundles'])
    for f in ('/web/assets/debug/web.assets_emoji.js', '/web/assets/debug/web.fullcalendar_lib.css', '/web/static/img/b.svg',
              '/bundles/web.assets_emoji.json'):
        assert f in c['files'] and os.path.isfile(os.path.join(nineteen, f.lstrip('/'))), ('19: taken', f)
    assert json.load(open(os.path.join(nineteen, 'bundles', 'web.assets_emoji.json'), encoding='utf-8')) == \
        BUNDLES['web.assets_emoji'], "a bundle's definition, as the instance gave it"
    assert c['view_info'] == VIEW_INFO, ('19: what each view is called, in each language', c['view_info'])
    assert 'pw' not in json.dumps(c) and not c['not_taken'], c['not_taken']
    print("PASS: importers/odoo/client — series 17 as before; series 19: its translations from its own address, the "
          "bundles its client loads when a page needs one, and what each view is called in each language; no password")
finally:
    shutil.rmtree(out, ignore_errors=True)
    srv.shutdown()
