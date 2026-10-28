#!/usr/bin/env python3
"""Odoo 19's client answered by the garden's worker (P7.1): the session 19's client reads (what each kind of view is
called, in the page's language; its mail store's start; no tour; and never `browser_cache_secret`, so the client keeps
nothing it was shown in the browser's disk cache), its menus and an action as 19 reads them, a captured view as 19's
`get_views` gives it, mail's start and a record's thread as 19's Store, and the data calls in 19's own signatures —
`web_read_group`, `formatted_read_group`, `web_name_search`, `name_search`'s `domain`, `has_access`, a properties
field's definitions (`get_properties_base_definition`: none, as 19 answers with no definition record). Their answers over
records are held to Odoo 19's own in test/worker/odoo19_conformance_test.py.

    python3 test/worker/odoo19_test.py [<daftar tree>]     # a daftar tree to grow the garden from (default ~/daftar)
"""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
sys.path.insert(0, HERE)
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test
from odoo_worker import Worker  # noqa: E402

FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + json.dumps(detail, ensure_ascii=False)[-900:]))
    if not cond:
        FAILS.append(name)


T = Path(tempfile.mkdtemp(prefix='worker-odoo19-'))
try:
    rel = grow.release(str(T / 'release'))
    G = T / 'garden'
    grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    # a capture of one model as importers/odoo/views.py writes it from a 19 instance (invented; no record)
    cap = G / 'captures' / 'views' / 'odoo-19.0'
    (cap / 'shop.need').mkdir(parents=True)
    (cap / 'CAPTURE.json').write_text(json.dumps({'series': '19.0', 'server_version': '19.0-20260908'}), encoding='utf-8')
    (cap / 'shop.need' / 'list.xml').write_text('<list string="Needs"><field name="name"/><field name="seats"/>'
                                                '<field name="state"/></list>\n', encoding='utf-8')
    (cap / 'shop.need' / 'form.xml').write_text('<form string="Need"><field name="name"/></form>\n', encoding='utf-8')
    (cap / 'shop.need' / 'search.xml').write_text('<search><field name="name"/></search>\n', encoding='utf-8')
    (cap / 'shop.need' / 'fields.json').write_text(json.dumps({
        'name': {'string': 'Name', 'type': 'char'}, 'seats': {'string': 'Seats', 'type': 'integer', 'aggregator': 'sum'},
        'state': {'string': 'State', 'type': 'selection', 'selection': [['open', 'Open'], ['filled', 'Filled']]},
        'date_start': {'string': 'From', 'type': 'date'},
        # 19's properties of a record with no parent (as res.partner's), described as 19's fields_get describes them
        'properties': {'string': 'Properties', 'type': 'properties', 'definition_record': 'properties_base_definition_id',
                       'definition_record_field': 'properties_definition'},
        'properties_base_definition_id': {'string': 'Properties Base Definition', 'type': 'many2one',
                                          'relation': 'properties.base.definition'}}), encoding='utf-8')
    (cap / 'shop.need' / 'related.json').write_text('{}', encoding='utf-8')
    VIEW_INFO = {'list': {'display_name': 'فهرست', 'icon': 'oi oi-view-list', 'multi_record': True}}
    w = Worker(G, series='19.0', scratch=str(T))
    try:
        s = w.call('odoo_session', {'reader': 'sam', 'series': '19.0', 'lang': 'fa_IR', 'view_info': VIEW_INFO})
        check("the session says what each view is called, in the page's language", s.get('view_info') == VIEW_INFO, s)
        check('the session is of series 19', (s.get('server_version_info') or [0])[0] == 19, s.get('server_version_info'))
        check("no browser_cache_secret: 19's client then keeps nothing it was shown on the reader's disk",
              'browser_cache_secret' not in s, sorted(s))
        store = (s.get('storeData') or {}).get('Store') or {}
        check("the mail store starts with the reader as its one partner", store.get('self_partner') == 1 and
              [p['name'] for p in s['storeData'].get('res.partner', []) if p['id'] == 1] == [s.get('name')], s.get('storeData'))
        check('no tour, and a version for its menus', s.get('tour_enabled') is False and len(s.get('registry_hash', '')) == 64, s)
        menus = w.rpc('sam', '/web/webclient/load_menus', {})
        check("19's menus (no path segment): an app per captured model, named by its view",
              menus.get('root', {}).get('children') == [1] and menus.get(1, menus.get('1', {})).get('name') == 'Needs', menus)
        act = w.rpc('sam', '/web/action/load', {'action_id': 1})
        check("an action as 19's action service reads it", act.get('res_model') == 'shop.need' and act.get('embedded_action_ids') == []
              and act.get('path') is False and act.get('display_name') == 'Needs', act)
        views = w.kw('sam', 'shop.need', 'get_views', views=[[False, 'list'], [False, 'search']], options={'load_filters': True})
        check("get_views as 19 gives it: each model's fields wrapped, each view with its toolbar",
              (views.get('models') or {}).get('shop.need', {}).get('fields', {}).get('seats', {}).get('type') == 'integer'
              and views['views']['list'].get('toolbar') == {} and 'filters' in views['views']['search'], views)
        md = w.rpc('sam', '/mail/data', {'fetch_params': ['failures', 'systray_get_activities', 'init_messaging']})
        check("mail starts as 19's store: nothing waits", (md.get('Store') or {}).get('inbox', {}).get('counter') == 0, md)
        th = w.rpc('sam', '/mail/data', {'fetch_params': [['mail.thread', {'thread_id': 7, 'thread_model': 'shop.need',
                                                                            'request_list': ['followers']}]]})
        check("a record's thread, read-only, closed where the reader reads no such record",
              [(x['id'], x['model'], x['hasReadAccess'], x['hasWriteAccess']) for x in th.get('mail.thread', [])]
              == [(7, 'shop.need', False, False)], th)
        check("a record's messages, in 19's Store shape", w.rpc('sam', '/mail/thread/messages', {'thread_id': 7,
              'thread_model': 'shop.need', 'fetch_params': {'limit': 30}}) == {'data': {}, 'messages': []})
        check('web_search_read: a page of nothing, as the garden holds no such record',
              w.kw('sam', 'shop.need', 'web_search_read', domain=[], specification={'name': {}}, limit=80) ==
              {'length': 0, 'records': []})
        check("19's web_read_group (domain, groupby, aggregates)", w.kw('sam', 'shop.need', 'web_read_group', domain=[],
              groupby=['state'], aggregates=['seats:sum'], auto_unfold=False) == {'groups': [], 'length': 0})
        check("19's formatted_read_group", w.kw('sam', 'shop.need', 'formatted_read_group', domain=[], groupby=['state'],
                                                aggregates=['__count']) == [])
        check("19's web_name_search", w.kw('sam', 'shop.need', 'web_name_search', name='x', specification={'display_name': {}},
                                           domain=[], operator='ilike', limit=8) == [])
        check("19's name_search names its domain `domain`", w.kw('sam', 'shop.need', 'name_search', name='', domain=[('state', '=', 'open')],
                                                               operator='ilike', limit=8) == [])
        check('has_access: reading, yes; nothing else', w.kw('sam', 'shop.need', 'has_access', [[]], operation='read') is True
              and w.kw('sam', 'shop.need', 'has_access', [[]], operation='write') is False)
        # what 19's search editor asks wherever it lists a model's fields: a properties field's definitions
        pd = w.kw('sam', 'properties.base.definition', 'get_properties_base_definition', ['shop.need', 'properties'])
        check("a properties field's definitions, as 19 answers where it holds no base definition record: none",
              pd == {'length': 0, 'records': []}, pd)
        for what, args in (('a field that is no properties field', ['shop.need', 'name']),
                           ('a field the capture does not describe', ['shop.need', 'nope']),
                           ('a model the garden captured no view of', ['res.users', 'properties'])):
            pd = w.kw('sam', 'properties.base.definition', 'get_properties_base_definition', args)
            check(f"...of {what}: refused, as 19 refuses it", isinstance(pd, dict) and (pd.get('error') or {}).get('status')
                  == 403 and 'can not read that field definition' in (pd['error'].get('message') or ''), pd)
    finally:
        w.close()
finally:
    shutil.rmtree(T, ignore_errors=True)
print(('FAIL: odoo19 — ' + ', '.join(FAILS)) if FAILS else
      "PASS: odoo19 — the session, menus, actions, views, mail's start and the data calls as Odoo 19's client asks them")
sys.exit(1 if FAILS else 0)
