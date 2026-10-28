#!/usr/bin/env python3
"""python/odoo_rpc.py: Odoo's domain language as Odoo decides it, and the calls its client makes — over a record set.

    python3 test/worker/odoo_rpc_test.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'python'))
from odoo_rpc import Answerer, Domain, Unsupported  # noqa: E402

FIELDS = {
    'people': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
               'active': {'type': 'boolean'}, 'age': {'type': 'integer'}, 'salary': {'type': 'float'},
               'state': {'type': 'selection', 'selection': [['a', 'Alpha'], ['b', 'Beta']]},
               'team_id': {'type': 'many2one', 'relation': 'team'}, 'tag_ids': {'type': 'many2many', 'relation': 'tag'}},
    'team': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'}},
    'tag': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'}},
}
RECORDS = {
    'people': [
        {'id': 1, 'name': 'Ana', 'display_name': 'Ana', 'active': True, 'age': 34, 'salary': 0.1, 'state': 'a', 'team_id': [1, 'Red'], 'tag_ids': [5]},
        {'id': 2, 'name': 'Ben', 'display_name': 'Ben', 'active': True, 'age': 19, 'salary': 0.2, 'state': 'b', 'team_id': [2, 'Blue sky'], 'tag_ids': []},
        {'id': 3, 'name': 'Dana', 'display_name': 'Dana', 'active': True, 'age': 41, 'salary': 0.2, 'state': 'a', 'team_id': [1, 'Red'], 'tag_ids': [5, 6]},
        {'id': 4, 'name': 'Eve', 'display_name': 'Eve', 'active': False, 'age': 50, 'salary': 1, 'state': 'b', 'team_id': False, 'tag_ids': []},
        {'id': 5, 'name': 'Fay', 'display_name': 'Fay', 'active': True, 'age': False, 'salary': 0, 'state': False, 'team_id': False, 'tag_ids': [6]},
    ],
    'team': [{'id': 1, 'name': 'Red', 'display_name': 'Red'}, {'id': 2, 'name': 'Blue sky', 'display_name': 'Blue sky'}],
    'tag': [{'id': 5, 'name': 'x', 'display_name': 'x'}, {'id': 6, 'name': 'y', 'display_name': 'y'}],
}
A = Answerer(lambda m: RECORDS.get(m, []), lambda m: FIELDS.get(m, {}), lambda m, w: {'views': {}, 'models': {m: FIELDS[m]}})


def ids(domain, ctx=None, order=None):
    return [r['id'] for r in A.search('people', domain, ctx, order)]


cases = [
    ("nothing asked: every active record", [], [1, 2, 3, 5]),
    ("the implicit & between terms", [('age', '>', 30), ('state', '=', 'a')], [1, 3]),
    ("| of two", ['|', ('name', 'ilike', 'an'), ('age', '<', 20)], [1, 2, 3]),
    ("! of one", ['!', ('state', '=', 'a')], [2, 5]),
    ("ilike is a case-insensitive part", [('name', 'ilike', 'AN')], [1, 3]),
    ("=ilike is a whole pattern", [('name', '=ilike', 'an%')], [1]),
    ("like: _ is any one character", [('name', 'like', 'B_n')], [2]),
    ("a many2one by its id", [('team_id', '=', 2)], [2]),
    ("a many2one by its name", [('team_id', 'ilike', 'blue')], [2]),
    ("a many2one that is not set", [('team_id', '=', False)], [5]),
    ("a many2one in ids", [('team_id', 'in', [1, 2])], [1, 2, 3]),
    ("a dotted path through the relation", [('team_id.name', '=', 'Red')], [1, 3]),
    ("any of the related records", [('team_id', 'any', [('name', 'like', 'sky')])], [2]),
    ("not any", [('team_id', 'not any', [('name', '=', 'Red')])], [2, 5]),
    ("a many2many holding one of", [('tag_ids', 'in', [5])], [1, 3]),
    ("a many2many with none", [('tag_ids', '=', False)], [2]),
    ("=? with False asks nothing", [('state', '=?', False)], [1, 2, 3, 5]),
    ("an integer not set is no number", [('age', '<', 100)], [1, 2, 3]),
    ("!= False is set", [('state', '!=', False)], [1, 2, 3]),
    ("in, with False among them", [('state', 'in', ['b', False])], [2, 5]),
    ("naming active shows the inactive", [('active', '=', False)], [4]),
    ("the true and false leaves", ['|', (0, '=', 1), (1, '=', 1)], [1, 2, 3, 5]),
]
bad = [(name, want, ids(dom)) for name, dom, want in cases if ids(dom) != want]
assert not bad, bad
assert ids([], {'active_test': False}) == [1, 2, 3, 4, 5], 'active_test False shows every record'
assert ids([], order='age desc') == [5, 3, 1, 2], 'descending, the unset first, as PostgreSQL orders'
assert ids([], order='age asc') == [2, 1, 3, 5] and ids([], order='age desc nulls last') == [3, 1, 2, 5]
assert ids([], order='state, name desc') == [3, 1, 2, 5], ids([], order='state, name desc')
try:
    ids([('name', 'regex', 'a')])
    raise AssertionError('an operator Odoo does not have is refused')
except Unsupported:
    pass
try:
    ids([('nope', '=', 1)])
    raise AssertionError('a field the model does not have is refused')
except Unsupported:
    pass

got = A.call('people', 'web_search_read', [], {'domain': [('state', '=', 'a')], 'specification': {'name': {}, 'team_id': {'fields': {'display_name': {}}}},
                                                'offset': 1, 'limit': 1, 'order': 'name asc'})
assert got == {'length': 2, 'records': [{'id': 3, 'name': 'Dana', 'team_id': {'id': 1, 'display_name': 'Red'}}]}, got
g = A.call('people', 'web_read_group', [], {'domain': [], 'fields': ['salary:sum'], 'groupby': ['team_id']})
red = [x for x in g['groups'] if x['team_id'] == [1, 'Red']][0]
assert red['salary'] == 0.30000000000000004 - 0.00000000000000004 and red['team_id_count'] == 2, red
assert 0.1 + 0.2 != 0.3 and red['salary'] == 0.3, 'summed exactly, not as floats are'
assert g['length'] == 3 and [x['team_id_count'] for x in g['groups']] == [2, 1, 1], g      # Odoo's lazy count key
assert [x['team_id'] for x in g['groups']] == [[1, 'Red'], [2, 'Blue sky'], False], 'in the order of the teams, unset last'
assert g['groups'][0]['__domain'] == [('team_id', '=', 1)], g['groups'][0]
e = A.call('people', 'read_group', [[], ['age:max'], ['state', 'team_id']], {'lazy': False})
assert {(x['state'], tuple(x['team_id']) if x['team_id'] else False): (x['__count'], x['age']) for x in e} == {
    ('a', (1, 'Red')): (2, 41), ('b', (2, 'Blue sky')): (1, 19), (False, False): (1, False)}, e
assert A.call('people', 'read', [[3, 99, 1], ['name', 'team_id']], {}) == [
    {'id': 3, 'name': 'Dana', 'team_id': [1, 'Red']}, {'id': 1, 'name': 'Ana', 'team_id': [1, 'Red']}], 'read: in order, none unknown'
assert A.call('people', 'fields_get', [['age', 'nope'], ['type']], {}) == {'age': {'type': 'integer'}}
p = A.call('people', 'search_panel_select_range', ['team_id'], {'enable_counters': True, 'search_domain': []})
assert p['values'] == [{'id': 1, 'display_name': 'Red', '__count': 2}, {'id': 2, 'display_name': 'Blue sky', '__count': 1}], p
s = A.call('people', 'search_panel_select_range', ['state'], {'enable_counters': True, 'search_domain': [('age', '>', 20)]})
assert s['values'] == [{'id': 'a', 'display_name': 'Alpha', '__count': 2}], 'not expanded: only the values taken' + str(s)
s = A.call('people', 'search_panel_select_range', ['state'], {'enable_counters': True, 'expand': True, 'search_domain': [('age', '>', 20)]})
assert s['values'] == [{'id': 'a', 'display_name': 'Alpha', '__count': 2}, {'id': 'b', 'display_name': 'Beta', '__count': 0}], s
assert A.call('people', 'search_count', [[('state', '=', 'a')]], {}) == 2
assert A.call('people', 'name_search', [], {'name': 'a', 'limit': 2}) == [[1, 'Ana'], [3, 'Dana']]
# Odoo's own server test of the panel's hierarchy (odoo/addons/test_search_panel/tests/test_search_panel_select_range.py,
# its first case): a folder counts its own records and those of the folders under it
FOLDERS = {'source': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                      'folder_id': {'type': 'many2one', 'relation': 'folder'}},
           'folder': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                      'parent_id': {'type': 'many2one', 'relation': 'folder'}}}
F = {'folder': [{'id': 1, 'name': 'Folder 1', 'display_name': 'Folder 1', 'parent_id': False},
                {'id': 2, 'name': 'Folder 2', 'display_name': 'Folder 2', 'parent_id': False},
                {'id': 3, 'name': 'Folder 3', 'display_name': 'Folder 3', 'parent_id': [1, 'Folder 1']},
                {'id': 4, 'name': 'Folder 4', 'display_name': 'Folder 4', 'parent_id': [2, 'Folder 2']}],
     'source': [{'id': 1, 'name': 'Rec 1', 'folder_id': [1, 'Folder 1']}, {'id': 2, 'name': 'Rec 2', 'folder_id': [3, 'Folder 3']},
                {'id': 3, 'name': 'Rec 3', 'folder_id': [4, 'Folder 4']}, {'id': 4, 'name': 'Rec 4', 'folder_id': False}]}
P = Answerer(lambda m: F.get(m, []), lambda m: FOLDERS.get(m, {}), lambda m, w: {})
got = P.call('source', 'search_panel_select_range', ['folder_id'], {'enable_counters': True, 'expand': True})
assert got == {'parent_field': 'parent_id', 'values': [
    {'id': 1, 'display_name': 'Folder 1', 'parent_id': False, '__count': 2},
    {'id': 2, 'display_name': 'Folder 2', 'parent_id': False, '__count': 1},
    {'id': 3, 'display_name': 'Folder 3', 'parent_id': 1, '__count': 1},
    {'id': 4, 'display_name': 'Folder 4', 'parent_id': 2, '__count': 1}]}, got
got = P.call('source', 'search_panel_select_range', ['folder_id'], {'enable_counters': True, 'expand': True,
                                                                     'search_domain': [['id', 'in', [1, 3]]]})
assert [v['__count'] for v in got['values']] == [1, 1, 0, 1], got
assert P.call('source', 'search_panel_select_range', ['folder_id'], {'enable_counters': True, 'expand': True, 'limit': 2}) == \
    {'error_msg': 'Too many items to display.'}
print('PASS: odoo_rpc — Odoo\'s domain language as Odoo decides it (22 cases), active records, order; the client\'s '
      'search, read, groups summed exactly, search panel with counters, as Odoo\'s own server test of its hierarchy '
      'has them; what it does not take, refused')
