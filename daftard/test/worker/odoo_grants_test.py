#!/usr/bin/env python3
"""Every answer daftard gives Odoo's client is made of what the reader may read (design §10.2, P5.4): the worker, run as
daftard runs it, over a garden grown from a daftar tree whose law crosses res.company and hr.department.

A reader granted part of the garden (Ana: one of its two companies and two of its departments) asks each call Odoo's
client makes; each answer must hold her part and nothing of the rest — no record, count, sum, group, panel value or
counter, and no name in a many2one or a department's complete name — and her favourites, never another's. The same
calls asked by the gardener show what the rest is, so no check passes by being empty.

Then the checks are run again against copies of the worker with the grant check REMOVED: once from the reading itself
(every bean opened), when every check must fail; and once from each call alone (that call answered as the gardener
reads), when that call's check must fail and every other still pass. So each check is shown to rest on the grant check
of its own call.

    python3 test/worker/odoo_grants_test.py <daftar tree>     # a tree whose law has core/law/crosswalks.yaml
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~/daftar')
sys.path.insert(0, os.path.join(TREE, 'test'))
FAILS = []


def check(name, cond, detail=''):
    print(('PASS  ' if cond else 'FAIL  ') + name + ('' if cond else '  — ' + str(detail)[-900:]))
    if not cond:
        FAILS.append(name)


if not os.path.isfile(os.path.join(TREE, 'core', 'law', 'crosswalks.yaml')):
    print(f"odoo_grants: {TREE} has no core/law/crosswalks.yaml — give a tree whose law crosses Odoo's models")
    sys.exit(2)
import grow  # noqa: E402 — the daftar tree's own way of growing a garden for a test
sys.path.insert(0, str(HERE))
from odoo_worker import Worker as _Worker  # noqa: E402 — the worker as daftard runs it

T = Path(tempfile.mkdtemp(prefix='odoo-grants-'))
G = T / 'garden'


def write(rel, text):
    p = G / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding='utf-8')


def org(bid, title, *st):
    write(f'beans/{bid}.md', f'---\nbean: {bid}\nkind: org\ntitle: "{title}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
          + ''.join(f'  - {x}\n' for x in st) + f'---\n{title}.\n')


def git(*a, stdin=None):
    return subprocess.run(['git', *a], cwd=G, capture_output=True, text=True, input=stdin, env=grow.ENV).stdout.strip()


def favourites(person, favs):
    """The person's own customisations ref holding their favourites, as daftard keeps them (labels.json)."""
    doc = json.dumps({'person': person, 'labels': {}, 'favourites': favs}, indent=1) + '\n'
    blob = git('hash-object', '-w', '--stdin', stdin=doc)
    tree = git('mktree', stdin=f'100644 blob {blob}\tlabels.json\n')
    commit = git('commit-tree', tree, '-m', f'{person}: favourites')
    git('update-ref', f'refs/daftar/custom/{person}', commit)


try:
    rel = grow.release(str(T / 'release'))
    r = grow.garden(rel, str(G), 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    org('acme', 'Acme', 'represent: { by: sam, of: self, as: "keeps its garden" }')
    org('beta', 'Betamax', 'represent: { by: sam, of: self, as: "keeps its books" }')
    org('eng', 'Engineering', 'part: { by: self, of: acme }')
    org('qa', 'Quality', 'part: { by: self, of: eng }')
    org('lab', 'Laboratory', 'part: { by: self, of: qa }')
    org('ops', 'Operations', 'part: { by: self, of: acme }')
    org('beta-sales', 'Betamax sales', 'part: { by: self, of: beta }')
    write('beans/ana.md', '---\nbean: ana\nkind: person\ntitle: "Ana"\nstatements:\n  - say: { by: sam, at: now }\n'
          '  - own: { by: theone, of: self }\n  - answer: { by: self, of: self, as: law }\n---\nAna.\n')
    write('beans/ana-consent.md', '---\nbean: ana-consent\nkind: contract\ntitle: "Ana agrees to be kept here by name"\n'
          'statements:\n  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n'
          '  - agree: { id: ana-agrees, by: ana, of: "kept here by name", through: spoken }\n'
          '  - agree: { id: sam-agrees, by: sam, of: "kept here by name", through: spoken }\n---\nHer word.\n')
    sam = (G / 'beans' / 'sam.md').read_text(encoding='utf-8')
    (G / 'beans' / 'sam.md').write_text(sam.replace(
        '\n---\n', '\n  - grant: { id: ana-reads, by: self, as: read, of: [acme, eng, ops, lab], to: [ana] }\n'
        '  - say: { by: sam, of: [ana-reads], at: now }\n---\n', 1), encoding='utf-8')
    s = grow.run(sys.executable, 'bin/save.py', 'sam', 'two companies, their departments, and Ana reading a part',
                 '--body', '- action: wrote [[acme]], [[beta]], [[eng]], [[qa]], [[lab]], [[ops]], [[beta-sales]] and '
                 '[[ana]] (kept on her word, [[ana-consent]]); [[sam]] opens Acme, Engineering, Operations and the '
                 'Laboratory to Ana', cwd=str(G))
    check('a garden of two companies and five departments, and Ana granted a part, passes its gate',
          r.returncode == 0 and s.returncode == 0, r.out[-500:] + s.out[-1500:])

    # the views the garden captured, as importers/odoo/views.py lays them (the fields only: these answers read no arch)
    cap = G / 'captures' / 'views' / 'odoo-17.0'
    rel_ = lambda m: {'type': 'many2one', 'relation': m, 'string': m}  # noqa: E731
    fields = {
        'hr.department': {'id': {'type': 'integer', 'string': 'ID'}, 'name': {'type': 'char', 'string': 'Name'},
                          'display_name': {'type': 'char'}, 'complete_name': {'type': 'char'},
                          'active': {'type': 'boolean'}, 'parent_id': rel_('hr.department'),
                          'company_id': rel_('res.company'),
                          'child_ids': {'type': 'one2many', 'relation': 'hr.department'}},
        'res.company': {'id': {'type': 'integer'}, 'name': {'type': 'char'}, 'display_name': {'type': 'char'},
                        'parent_id': rel_('res.company'), 'child_ids': {'type': 'one2many', 'relation': 'res.company'}}}
    for m, f in fields.items():
        (cap / m).mkdir(parents=True, exist_ok=True)
        (cap / m / 'fields.json').write_text(json.dumps(f), encoding='utf-8')
        (cap / m / 'search.xml').write_text('<search><field name="name"/></search>\n', encoding='utf-8')
        (cap / m / 'list.xml').write_text('<tree><field name="name"/></tree>\n', encoding='utf-8')
    (cap / 'CAPTURE.json').write_text('{"series": "17.0"}\n', encoding='utf-8')
    favourites('sam', {'s1': {'model': 'hr.department', 'name': "Sam's departments", 'domain': "[('name', 'ilike', 'a')]",
                              'at': '2026-10-11T00:00:00.000000000Z'}})
    favourites('ana', {'a1': {'model': 'hr.department', 'name': "Ana's search", 'domain': '[]',
                              'at': '2026-10-11T00:00:00.000000000Z'}})

    import hashlib

    def Worker(mutate=None):
        return _Worker(G, mutate, scratch=T)

    def num(model, bean):          # a record's number, as the law's crosswalk reader gives it
        return int.from_bytes(hashlib.sha256(f'{model}:{bean}'.encode()).digest()[:4], 'big') & 0x7fffffff

    D = 'hr.department'
    every = [num(D, b) for b in ('eng', 'qa', 'lab', 'ops', 'beta-sales')]
    closed_names = ('Quality', 'Laboratory', 'Betamax')
    closed_ids = {num(D, b) for b in ('qa', 'lab', 'beta-sales')} | {num('res.company', 'beta')}
    spec = {'name': {}, 'complete_name': {}, 'display_name': {}, 'child_ids': {},
            'parent_id': {'fields': {'display_name': {}}}, 'company_id': {'fields': {'display_name': {}}}}

    def clean(answer):
        """Nothing of what is closed to Ana: no closed department's or company's name, and no closed record's number."""
        text = json.dumps(answer)
        nums = {int(x) for x in re.findall(r'(?<![\w.])\d{5,}(?![\w.])', text)}
        return not any(n in text for n in closed_names) and not (nums & closed_ids) and 'error' not in str(answer)[:9]

    # Each call: what Ana must get, asked as the client asks it. Each check also asks the gardener the same, who must
    # get more — so no check passes by being empty. A refusal, or an answer of another shape, fails the check.
    def names(recs):
        return sorted(str(x.get('name')) for x in recs if isinstance(x, dict)) if isinstance(recs, list) else ['(refused)']

    def c_web_search_read(w):
        a = w.kw('ana', D, 'web_search_read', [], domain=[], specification=spec)
        g = w.kw('sam', D, 'web_search_read', [], domain=[], specification=spec)
        return names(a['records']) == ['Engineering', 'Operations'] and a['length'] == 2 and g['length'] == 5 \
            and clean(a), (a, g)

    def c_web_read(w):
        a, g = w.kw('ana', D, 'web_read', [every], specification=spec), w.kw('sam', D, 'web_read', [every], specification=spec)
        return names(a) == ['Engineering', 'Operations'] and len(g) == 5 and clean(a), (a, g)

    def c_read(w):
        f = ['name', 'complete_name', 'parent_id', 'child_ids', 'company_id']
        a, g = w.kw('ana', D, 'read', [every, f]), w.kw('sam', D, 'read', [every, f])
        return names(a) == ['Engineering', 'Operations'] and len(g) == 5 and clean(a), (a, g)

    def c_search_count(w):
        a, g = w.kw('ana', D, 'search_count', [[]]), w.kw('sam', D, 'search_count', [[]])
        return a == 2 and g == 5, (a, g)

    def c_search_read(w):
        a, g = w.kw('ana', D, 'search_read', [[], ['name', 'parent_id']]), w.kw('sam', D, 'search_read', [[], ['name']])
        return names(a) == ['Engineering', 'Operations'] and len(g) == 5 and clean(a), (a, g)

    def c_name_search(w):
        a, g = w.kw('ana', D, 'name_search', [], name='', limit=8), w.kw('sam', D, 'name_search', [], name='', limit=8)
        q = w.kw('ana', D, 'name_search', [], name='Qual')
        return sorted(x[1] for x in a) == ['Engineering', 'Operations'] and len(g) == 5 and q == [] and clean(a), (a, g, q)

    def c_web_read_group(w):
        kw = dict(domain=[], fields=['id:sum', 'parent_id:count_distinct'], groupby=['company_id'])
        a, g = w.kw('ana', D, 'web_read_group', [], **kw), w.kw('sam', D, 'web_read_group', [], **kw)
        one = a['groups'][0]
        return a['length'] == 1 and one['company_id'] == [num('res.company', 'acme'), 'Acme'] \
            and one['company_id_count'] == 2 and one['id'] == num(D, 'eng') + num(D, 'ops') and g['length'] == 2 \
            and clean(a), (a, g)

    def c_read_group(w):
        a = w.kw('ana', D, 'read_group', [[], ['id:sum'], ['company_id', 'parent_id']], lazy=False)
        g = w.kw('sam', D, 'read_group', [[], ['id:sum'], ['company_id', 'parent_id']], lazy=False)
        return sum(x['__count'] for x in a) == 2 and sum(x['id'] for x in a) == num(D, 'eng') + num(D, 'ops') \
            and sum(x['__count'] for x in g) == 5 and clean(a), (a, g)

    def c_search_panel_select_range(w):
        kw = dict(enable_counters=True, expand=True, search_domain=[])
        a, g = w.kw('ana', D, 'search_panel_select_range', ['parent_id'], **kw), w.kw('sam', D, 'search_panel_select_range', ['parent_id'], **kw)
        c = w.kw('ana', D, 'search_panel_select_range', ['company_id'], **kw)
        return sorted(v['display_name'] for v in a['values']) == ['Engineering', 'Operations'] \
            and [(v['display_name'], v['__count']) for v in c['values']] == [('Acme', 2)] and len(g['values']) == 5 \
            and clean(a) and clean(c), (a, c, g)

    def c_search_panel_select_multi_range(w):
        kw = dict(enable_counters=True, expand=True, search_domain=[])
        a = w.kw('ana', D, 'search_panel_select_multi_range', ['company_id'], **kw)
        g = w.kw('sam', D, 'search_panel_select_multi_range', ['company_id'], **kw)
        return [(v['display_name'], v['__count']) for v in a['values']] == [('Acme', 2)] and len(g['values']) == 2 \
            and clean(a), (a, g)

    def c_ir_filters(w):
        a = w.kw('ana', D, 'get_views', [], views=[[False, 'search'], [False, 'list']], options={'load_filters': True})
        f, gf = w.kw('ana', 'ir.filters', 'get_filters', [D]), w.kw('sam', 'ir.filters', 'get_filters', [D])
        return [x['name'] for x in a['views']['search']['filters']] == ["Ana's search"] \
            and [x['name'] for x in f] == ["Ana's search"] and [x['name'] for x in gf] == ["Sam's departments"], (a, f, gf)

    CHECKS = {'web_search_read': c_web_search_read, 'web_read': c_web_read, 'read': c_read,
              'search_count': c_search_count, 'search_read': c_search_read, 'name_search': c_name_search,
              'web_read_group': c_web_read_group, 'read_group': c_read_group,
              'search_panel_select_range': c_search_panel_select_range,
              'search_panel_select_multi_range': c_search_panel_select_multi_range, 'ir.filters': c_ir_filters}

    def calls(w):
        out = {}
        for name, fn in CHECKS.items():
            try:
                out[name] = fn(w)
            except Exception as e:                    # an answer of another shape than Odoo's
                out[name] = (False, f'{type(e).__name__}: {e}')
        return out

    w = Worker()
    got = calls(w)
    w.close()
    for name, (ok, detail) in got.items():
        check(f"{name}: Ana is answered her part of the garden, and nothing of the rest", ok, detail)

    # THE CHECKS REST ON THE GRANT CHECK. With it removed from the reading, every bean is open and every check fails.
    reading = ("        self.readable = {b for b in G.beans\n"
               "                         if dmpass.may(self.reader, 'read', b, root=str(ROOT), beans=now, gardener=keeper).granted}\n")
    w = Worker({'garden_worker.py': (reading, "        self.readable = set(G.beans)\n")})
    got = calls(w)
    w.close()
    check("with the grant check removed from the reading, every check of a record fails",
          not any(ok for name, (ok, _d) in got.items() if name != 'ir.filters'), {k: v[0] for k, v in got.items()})
    # ...and with it removed from one call at a time (that call answered as the gardener reads), that call's check
    # fails and every other passes
    dispatch = "        reading = OdooReading(series, reader, asof)        # one reading for the whole call: the reader's part of the garden\n"
    for call in [k for k in got if k != 'ir.filters']:
        w = Worker({'garden_worker.py': (dispatch, f"        reading = OdooReading(series, gardener() if method == {call!r} "
                                                   f"else reader, asof)\n")})
        mut = calls(w)
        w.close()
        others = [k for k, (ok, _d) in mut.items() if k != call and not ok]
        check(f"{call}: with the grant check removed from it alone, its check fails and no other does",
              not mut[call][0] and not others, (mut[call][0], others))
    fav = "lambda m, action_id=None: odoo_favourites(reader, m, action_id))"
    w = Worker({'garden_worker.py': (fav, "lambda m, action_id=None: odoo_favourites(gardener(), m, action_id))")})
    mut = calls(w)
    w.close()
    check("ir.filters: answered another's favourites in place of the reader's own, its check fails and no other does",
          not mut['ir.filters'][0] and all(ok for k, (ok, _d) in mut.items() if k != 'ir.filters'),
          {k: v[0] for k, v in mut.items()})
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nodoo_grants: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
