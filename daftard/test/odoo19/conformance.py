#!/usr/bin/env python3
"""conformance — daftard's answers to Odoo 19's client, held to Odoo 19's own: the answerer (python/odoo_rpc.py, series
19) is handed the records of a 19 Community instance and must answer each call the client makes exactly as that
instance answers it for the same records — a list's page and count, a dotted domain, a form's read, the many2one's
suggestions, and the groups 19 redesigned (their values, domains, counts and sums; by a many2one, a many2many, a
selection and a date at each granularity; a group opened into its records or into its subgroups; a limited level)
— and a properties field's definitions, as the client builds them from either answer.

    ODOO_PASSWORD=… python3 test/odoo19/conformance.py --url http://127.0.0.1:<port> --db <db> --login admin

The instance is a throwaway 19 Community one with invented records of Odoo's own models (test/odoo19/invented.py makes
them). This only reads, but for one setting of the throwaway's: English made active, the language the answerer words a
date's group in.
"""
import argparse
import itertools
import json
import os
import sys
import urllib.request
from http.cookiejar import CookieJar

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..', 'python'))
import odoo_rpc  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('--url', required=True)
ap.add_argument('--db', required=True)
ap.add_argument('--login', required=True)
a = ap.parse_args()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
seq = itertools.count(1)


def post(path, params):
    body = json.dumps({'jsonrpc': '2.0', 'method': 'call', 'id': next(seq), 'params': params}).encode()
    got = json.loads(op.open(urllib.request.Request(a.url + path, body, {'Content-Type': 'application/json'}), timeout=120).read())
    if got.get('error'):
        raise RuntimeError(json.dumps(got['error'].get('data', {}).get('message') or got['error'], ensure_ascii=False)[:600])
    return got.get('result')


if not (post('/web/session/authenticate', {'db': a.db, 'login': a.login, 'password': os.environ['ODOO_PASSWORD']}) or {}).get('uid'):
    sys.exit('the instance refused that login')
# English, the language the answerer words a date's group in, active on the instance (a throwaway's own setting)
_en = post('/web/dataset/call_kw/res.lang/search_read', {'model': 'res.lang', 'method': 'search_read', 'args': [],
           'kwargs': {'domain': [('code', '=', 'en_US'), ('active', 'in', [True, False])], 'fields': ['active']}})
if _en and not _en[0]['active']:
    _w = post('/web/dataset/call_kw/base.language.install/create', {'model': 'base.language.install', 'method': 'create',
              'args': [{'lang_ids': [(6, 0, [_en[0]['id']])]}], 'kwargs': {}})
    post('/web/dataset/call_kw/base.language.install/lang_install', {'model': 'base.language.install',
         'method': 'lang_install', 'args': [[_w]], 'kwargs': {}})
CTX = {'lang': 'en_US', 'tz': 'Asia/Tehran'}


def server(model, method, args=(), **kw):
    return post(f'/web/dataset/call_kw/{model}/{method}', {'model': model, 'method': method, 'args': list(args),
                                                           'kwargs': dict(kw, context=dict(CTX, **kw.get('context', {})))})


FIELDS, RECORDS = {}, {}


def fields(model):
    if model not in FIELDS:
        FIELDS[model] = server(model, 'fields_get', [], attributes=['type', 'relation', 'selection', 'string', 'aggregator',
                                                                     'store'])
    return FIELDS[model]


def records(model):
    """The instance's records of a model as Odoo's client reads them — what daftard's provider hands the answerer."""
    if model not in RECORDS:
        names = [n for n, d in fields(model).items() if d.get('type') not in ('binary', 'properties', 'properties_definition',
                                                                            'json', 'html') and n != 'id']
        RECORDS[model] = server(model, 'search_read', [], domain=[], fields=names + ['display_name'],
                                context={'active_test': False})
    return RECORDS[model]


import inspect  # noqa: E402
_week = int(server('res.lang', 'search_read', [], domain=[('code', '=', 'en_US')], fields=['week_start'])[0]['week_start'])
_takes = inspect.signature(odoo_rpc.Answerer).parameters      # an answerer that knows no series is asked as it is
answerer = odoo_rpc.Answerer(records, fields, lambda m, wanted: {'views': {}, 'models': {}},
                             **({'series': '19.0', 'week_start': _week} if 'series' in _takes else {}))


def ours(model, method, args=(), **kw):
    return json.loads(json.dumps(answerer.call(model, method, list(args), dict(kw, context=dict(CTX, **kw.get('context', {}))))))


checks, failed = 0, []


def same(what, model, method, args=(), **kw):
    """The call answered by the instance and by daftard's answerer, for the same records, compared whole."""
    global checks
    checks += 1
    want = server(model, method, args, **kw)
    try:
        got = ours(model, method, args, **kw)
    except Exception as e:  # noqa: BLE001 — an answer it could not give fails this check, and the next is asked
        got = f'{type(e).__name__}: {e}'
    if got != want:
        failed.append(what)
        print(f'FAIL {what}\n  odoo:    {json.dumps(want, ensure_ascii=False)[:900]}\n  daftard: {json.dumps(got, ensure_ascii=False)[:900]}')


P, R = 'res.partner', 'res.currency.rate'
people = {'name': {}, 'country_id': {'fields': {'display_name': {}}}, 'type': {}, 'parent_id': {'fields': {'display_name': {}}},
          'category_id': {'fields': {'display_name': {}}}, 'is_company': {}}
same('the list of people and companies, its page and count', P, 'web_search_read', specification=people, offset=0, limit=80,
     order='', count_limit=10001, domain=[])
same('a page of two, ordered by name descending, and its count', P, 'web_search_read', specification=people, offset=1,
     limit=2, order='name DESC', count_limit=10001, domain=[])
same("a domain through a relation: those whose country's code is IR", P, 'web_search_read',
     specification={'name': {}}, domain=[('country_id.code', '=', 'IR')])
some = [r['id'] for r in records(P) if r.get('parent_id')][:2]
same("a form's read, its many2one and many2many read by the specification", P, 'web_read', [some],
     specification={'name': {}, 'parent_id': {'fields': {'display_name': {}}}, 'category_id': {'fields': {'display_name': {}}},
                     'display_name': {}})
same('how many are companies', P, 'search_count', [[('is_company', '=', True)]])
same("the people a many2one offers, by 19's own name_search", P, 'name_search', [], name='', domain=[],
     operator='ilike', limit=8)
same('the people a many2one offers for a word', P, 'name_search', [], name='Ex', domain=[], operator='ilike', limit=8)
same("19's web_name_search, display names", P, 'web_name_search', [], name='', specification={'display_name': {}},
     domain=[('is_company', '=', True)], operator='ilike', limit=8)
same('grouped by country', P, 'web_read_group', [], domain=[], groupby=['country_id'], aggregates=[])
same('grouped by the kind of address (a selection)', P, 'web_read_group', [], domain=[], groupby=['type'], aggregates=[])
same('grouped by tag (a many2many)', P, 'web_read_group', [], domain=[], groupby=['category_id'], aggregates=[])
same('grouped by parent company', P, 'web_read_group', [], domain=[], groupby=['parent_id'], aggregates=['__count'])
same('two levels, the first opened into its subgroups (a kanban unfolds)', P, 'web_read_group', [], domain=[],
     groupby=['country_id', 'type'], aggregates=['__count'], auto_unfold=True, unfold_read_specification={'name': {}})
same('one level opened into its records as the client asks (opening_info)', P, 'web_read_group', [], domain=[],
     groupby=['country_id'], aggregates=[],
     opening_info=[{'value': next(r['country_id'][0] for r in records(P) if r.get('country_id')), 'folded': False,
                    'limit': 80, 'offset': 0}], unfold_read_specification={'name': {}, 'type': {}})
same('a limited first level, its length the whole count', P, 'web_read_group', [], domain=[], groupby=['country_id'],
     aggregates=[], limit=2)
same('groups ordered by their count, descending', P, 'web_read_group', [], domain=[], groupby=['country_id'],
     aggregates=['__count'], order='__count DESC')
for gran in ('day', 'week', 'month', 'quarter', 'year'):
    same(f"a currency's rates grouped by the {gran} of their date, summed and averaged", R, 'web_read_group', [],
         domain=[], groupby=[f'name:{gran}'], aggregates=['rate:sum', 'rate:avg'])
same("19's formatted_read_group, by currency and quarter", R, 'formatted_read_group', [], domain=[],
     groupby=['currency_id', 'name:quarter'], aggregates=['rate:max', '__count'])


def definitions(answer):
    """The property definitions 19's client builds from an answer of get_properties_base_definition (its own
    web/core/field_service.js: each record's `properties_definition`, by name), or 'refused'."""
    if not isinstance(answer, dict) or not isinstance(answer.get('records'), list):
        return 'refused'
    return sorted([d.get('name'), d.get('type')] for r in answer['records'] for d in (r.get('properties_definition') or []))


def both(model, method, args):
    """The instance's answer and daftard's, each a refusal where it refuses."""
    out = []
    for ask in (server, ours):
        try:
            out.append(ask(model, method, args))
        except Exception:  # noqa: BLE001 — the instance's AccessError or KeyError, daftard's Denied: a refusal each
            out.append('refused')
    return out


# A PROPERTIES FIELD'S DEFINITIONS, which 19's search editor asks wherever it lists a model's fields. The instance reads
# them from its base definition record; the answerer holds none and answers as 19 does where there is none. The client
# builds the same definitions from either answer where the instance defines no property; where it defines some, daftard
# offers none of them (said, not failed: their definitions are not among what a garden holds).
want, got = both('properties.base.definition', 'get_properties_base_definition', [P, 'properties'])
checks += 1
if definitions(want) == 'refused' or definitions(got) != []:
    failed.append("res.partner's property definitions")
    print(f"FAIL res.partner's property definitions\n  odoo:    {json.dumps(want, ensure_ascii=False)[:600]}\n"
          f"  daftard: {json.dumps(got, ensure_ascii=False)[:600]}")
elif definitions(want):
    print(f"NOTE the instance defines {len(definitions(want))} property of res.partner; daftard offers none of them")
want, got = both('properties.base.definition', 'get_properties_base_definition', [P, 'name'])
checks += 1
if want != 'refused' or got != 'refused':
    failed.append('the definitions of a field that is no properties field: refused by both')
    print(f'FAIL the definitions of a field that is no properties field\n  odoo: {want}\n  daftard: {got}')
print(f"{'PASS' if not failed else 'FAIL'}: odoo19 conformance — {checks - len(failed)} of {checks} calls answered as "
      f"Odoo 19 answers them for the same records" + (f"; differ: {failed}" if failed else ''))
sys.exit(1 if failed else 0)
