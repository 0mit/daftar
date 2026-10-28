#!/usr/bin/env python3
"""client — take an Odoo series' own web client, as its Community instance compiles it, for daftard to serve (§10.2).

    python3 importers/odoo/client.py --url <http://host:port> --db <name> --login <user> --out <dir> \
        [--lang tr_TR --lang fa_IR …]     (the password is read from ODOO_PASSWORD)

ODOO'S OWN SEARCH COMPONENTS RUN UNCHANGED (design §10.2): `WithSearch`, `SearchBar`, `SearchBarMenu`, `SearchPanel` and
the views that hold them are Odoo's (LGPL-3), compiled by that series' own Community instance with the owners' addons —
never Enterprise — into the bundle its `/web` page loads. This takes that bundle (`web.assets_web.js` and `.css`) and
every file its stylesheet names (fonts, images) — and its right-to-left stylesheet, for a language written so — and,
for each language asked, Odoo's own translations of the client as that instance gives them (`translations/<lang>.json`,
the language loaded there first), and writes them under `<out>/`, with CLIENT.json: the series and server version, the
modules installed, the languages, the moment, and each file's SHA-256. daftard serves them as they came and answers the
calls they make itself; nothing of the instance is needed after. Code, not facts: it is kept outside every garden,
fetched for a machine, never shipped in daftard.

FROM SERIES 19 the client loads some bundles only when a page needs them (`/web/bundle/<name>`: the emoji of the
chatter, chart.js for a graph, fullcalendar, the code editor, the tours), names its translations without a path segment
(`/web/webclient/translations?lang=`), and is told what each kind of view is called in the reader's language
(`view_info`, part of its session). So for 19 each of LAZY is taken too — its definition (`bundles/<name>.json`) and its
files — the translations from 19's own address, and `view_info` in English and each language asked (in CLIENT.json).

Exit 0 when the bundle and every file it names were taken, 1 when a file could not be.
"""
import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

BUNDLE = ('/web/assets/debug/web.assets_web.js', '/web/assets/debug/web.assets_web.css',
          '/web/assets/debug/web.assets_web.rtl.css')
# the bundles 19's client loads only when a page needs one (its own `loadBundle` calls), as the debug build names them
LAZY = ('web.assets_emoji', 'web.chartjs_lib', 'web.fullcalendar_lib', 'web.ace_lib', 'web_tour.interactive')
URL_IN_CSS = re.compile(r'url\(\s*["\']?(/[^"\')?#]+)')


def session(url, db, login, password):
    jar = http.cookiejar.CookieJar()
    op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    body = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {'db': db, 'login': login, 'password': password}})
    r = op.open(urllib.request.Request(url + '/web/session/authenticate', body.encode(),
                                       {'Content-Type': 'application/json'}), timeout=60)
    got = json.loads(r.read())
    if not (got.get('result') or {}).get('uid'):
        raise SystemExit('client: the instance refused that login')
    return op, got['result']


def take(op, url, path, out):
    """One file of the instance, written under `out` at its own path; its SHA-256."""
    data = op.open(url + path, timeout=300).read()
    dest = os.path.join(out, path.lstrip('/'))
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, 'wb') as fh:
        fh.write(data)
    return hashlib.sha256(data).hexdigest(), data


def take_css(op, url, path, out, files, failed):
    """A stylesheet, and every file it names."""
    files[path], data = take(op, url, path, out)
    for p in sorted({urllib.parse.unquote(m) for m in URL_IN_CSS.findall(data.decode('utf-8', 'replace'))}):
        try:
            files[p], _ = take(op, url, p, out)
        except Exception as e:  # noqa: BLE001 — a file the stylesheet names and the instance does not have
            failed.append((p, str(e)[:160]))


def call_kw(op, url, model, method, args, kwargs):
    body = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {'model': model, 'method': method, 'args': args,
                                                                      'kwargs': kwargs}})
    got = json.loads(op.open(urllib.request.Request(url + f'/web/dataset/call_kw/{model}/{method}', body.encode(),
                                                    {'Content-Type': 'application/json'}), timeout=60).read())
    if got.get('error'):
        raise RuntimeError(str((got['error'].get('data') or {}).get('message') or got['error'])[:300])
    return got['result']


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--url', required=True)
    ap.add_argument('--db', required=True)
    ap.add_argument('--login', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--lang', action='append', default=[])
    a = ap.parse_args(argv)
    password = os.environ.get('ODOO_PASSWORD')
    if not password:
        print('client: the password is read from ODOO_PASSWORD', file=sys.stderr)
        return 2
    url = a.url.rstrip('/')
    op, info = session(url, a.db, a.login, password)
    major = (info.get('server_version_info') or [0])[0]
    major = major if isinstance(major, int) else 0
    files, failed = {}, []
    for path in BUNDLE:
        if path.endswith('.css'):
            take_css(op, url, path, a.out, files, failed)
        else:
            files[path], _ = take(op, url, path, a.out)
    lazy, view_info = {}, {}
    if major >= 19:
        for name in LAZY:                           # each bundle's definition, as the debug client asks it, and its files
            try:
                data = op.open(f'{url}/web/bundle/{urllib.parse.quote(name)}?debug=assets', timeout=120).read()
                parts = [x for x in json.loads(data) if isinstance(x, dict) and str(x.get('src', '')).startswith('/')]
            except Exception as e:  # noqa: BLE001 — a bundle this instance does not build
                failed.append((f'/web/bundle/{name}', str(e)[:160]))
                continue
            for x in parts:
                src = urllib.parse.urlsplit(x['src']).path
                try:
                    if src.endswith('.css'):
                        take_css(op, url, src, a.out, files, failed)
                    else:
                        files[src], _ = take(op, url, src, a.out)
                except Exception as e:  # noqa: BLE001
                    failed.append((src, str(e)[:160]))
            dest = os.path.join(a.out, 'bundles', f'{name}.json')
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            with open(dest, 'wb') as fh:
                fh.write(data)
            files[f'/bundles/{name}.json'] = hashlib.sha256(data).hexdigest()
            lazy[name] = [urllib.parse.urlsplit(x['src']).path for x in parts]
        for lang in ['en_US'] + [x for x in a.lang if x != 'en_US']:
            try:
                view_info[lang] = call_kw(op, url, 'ir.ui.view', 'get_view_info', [[]], {'context': {'lang': lang}})
            except Exception as e:  # noqa: BLE001
                failed.append((f'view_info {lang}', str(e)[:160]))
    langs = {}
    for lang in a.lang:
        where = '/web/webclient/translations?' if major >= 19 else '/web/webclient/translations/daftar?'
        data = op.open(f'{url}{where}lang={urllib.parse.quote(lang)}', timeout=120).read()
        got = json.loads(data)
        if (got.get('lang_parameters') or {}).get('code') != lang:
            failed.append((f'translations/{lang}.json', 'that language is not loaded on the instance'))
            continue
        dest = os.path.join(a.out, 'translations', f'{lang}.json')
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, 'wb') as fh:
            fh.write(data)
        files[f'/translations/{lang}.json'] = hashlib.sha256(data).hexdigest()
        langs[lang] = got['lang_parameters'].get('direction', 'ltr')
    body = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': {'model': 'ir.module.module', 'method': 'search_read',
                       'args': [[['state', '=', 'installed']]], 'kwargs': {'fields': ['name', 'installed_version']}}})
    mods = json.loads(op.open(urllib.request.Request(url + '/web/dataset/call_kw', body.encode(),
                                                     {'Content-Type': 'application/json'}), timeout=60).read())['result']
    client = {'what': "an Odoo series' own web client, as its Community instance compiled it",
              'series': '.'.join(map(str, info.get('server_version_info', [])[:2])), 'server_version': info.get('server_version'),
              'instance': url, 'at': time.strftime('%Y-%m-%dT%H:%M:%S%z'),
              'modules': {m['name']: m['installed_version'] for m in sorted(mods, key=lambda m: m['name'])},
              'languages': langs,
              **({'bundles': lazy, 'view_info': view_info} if major >= 19 else {}),
              'files': dict(sorted(files.items())), 'not_taken': [{'path': p, 'why': w} for p, w in failed]}
    with open(os.path.join(a.out, 'CLIENT.json'), 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(client, fh, ensure_ascii=False, indent=1)
        fh.write('\n')
    for p, w in failed:
        print(f'client: {p}: not taken — {w}')
    print(f"client: {len(files)} file(s) of {client['series']} ({client['server_version']}) taken into {a.out}, "
          f"{len(failed)} not")
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
