#!/usr/bin/env python3
"""invented — records of Odoo's own Community models, invented, in a throwaway 19 instance, for the tests of this folder
and of test/render/odoo19.mjs: people and companies (each a `res.partner`: a country, a kind of address, tags, a parent
company), three tags, and a currency's rates on days across a year (`res.currency.rate`: a date, a rate). Nobody real:
the names are a test's, the mails and phones are none, the countries are the instance's own table.

    ODOO_PASSWORD=… python3 test/odoo19/invented.py --url http://127.0.0.1:<port> --db <db> --login admin [--mark TOKEN]

`--mark` adds a token to every name it writes, so a test can look for it anywhere it must not be. Prints a JSON summary
(the ids made); a second run makes nothing twice (it finds by name what the first made).
"""
import argparse
import itertools
import json
import os
import sys
import urllib.request


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', required=True)
    ap.add_argument('--db', required=True)
    ap.add_argument('--login', required=True)
    ap.add_argument('--mark', default='')
    a = ap.parse_args(argv)
    seq = itertools.count(1)

    def rpc(service, method, *args):
        body = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': next(seq),
                           'params': {'service': service, 'method': method, 'args': list(args)}}).encode()
        got = json.loads(urllib.request.urlopen(urllib.request.Request(
            a.url.rstrip('/') + '/jsonrpc', body, {'Content-Type': 'application/json'}), timeout=120).read())
        if got.get('error'):
            raise SystemExit('invented: ' + json.dumps(got['error'].get('data', {}).get('message') or got['error'])[:600])
        return got.get('result')

    pw = os.environ['ODOO_PASSWORD']
    uid = rpc('common', 'authenticate', a.db, a.login, pw, {})
    if not uid:
        raise SystemExit('invented: the instance refused that login')

    def call(model, method, *args, **kw):
        return rpc('object', 'execute_kw', a.db, uid, pw, model, method, list(args), kw)

    mark = (' ' + a.mark) if a.mark else ''

    def make(model, vals, key='name'):
        got = call(model, 'search', [(key, '=', vals[key])], limit=1, context={'active_test': False})
        return got[0] if got else call(model, 'create', vals)

    country = {c['code']: c['id'] for c in call('res.country', 'search_read', [('code', 'in', ['TR', 'IR', 'DE'])],
                                               fields=['code'])}
    tags = [make('res.partner.category', {'name': f'Invented tag {x}{mark}'}) for x in 'ABC']
    acme = make('res.partner', {'name': f'Acme Tiles{mark}', 'is_company': True, 'country_id': country['TR'],
                                'category_id': [(6, 0, [tags[0]])]})
    bolt = make('res.partner', {'name': f'Bolt Works{mark}', 'is_company': True, 'country_id': country['DE']})
    people = []
    for i, (n, c, kind, parent, tag) in enumerate([
            ('Ada Example', 'TR', 'contact', acme, [0, 1]), ('Bo Sample', 'IR', 'invoice', acme, [1]),
            ('Cy Invented', 'IR', 'delivery', bolt, []), ('Di Madeup', 'DE', 'contact', bolt, [2]),
            ('Ed Fictive', 'TR', 'other', False, [0, 2]), ('Fa Testcase', 'IR', 'contact', False, [])]):
        people.append(make('res.partner', {'name': f'{n}{mark}', 'country_id': country[c], 'type': kind,
                                           'parent_id': parent, 'category_id': [(6, 0, [tags[t] for t in tag])]}))
    # a currency's rates on days across a year: a date to group by, a rate to sum and average
    cur = call('res.currency', 'search', [('name', '=', 'EUR')], limit=1, context={'active_test': False})
    rates = []
    if cur:
        for day, rate in [('2026-01-05', '0.0004'), ('2026-01-19', '0.0005'), ('2026-02-02', '0.0005'),
                          ('2026-04-14', '0.0006'), ('2026-07-01', '0.0007'), ('2026-07-02', '0.0007'),
                          ('2026-10-11', '0.0008'), ('2026-12-31', '0.0009')]:
            got = call('res.currency.rate', 'search', [('currency_id', '=', cur[0]), ('name', '=', day)], limit=1)
            rates.append(got[0] if got else call('res.currency.rate', 'create', {'currency_id': cur[0], 'name': day,
                                                                                   'rate': float(rate)}))
    print(json.dumps({'tags': tags, 'companies': [acme, bolt], 'people': people, 'currency': cur[:1], 'rates': rates,
                      'mark': a.mark}))


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
