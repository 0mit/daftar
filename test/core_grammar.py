#!/usr/bin/env python3
"""core_grammar — the reading grammar, part one (core 3.2, the next machinery's design, body I: I.1, I.3, I.4, I.5, I.6 and
I.9's set words), and the two values the law now holds (body VIII).

Each by its vectors: `describe` of a statement — the member itself, or a value naming one; the comparator `fits` and
the law's table of checks, closed both ways and held to its vectors, the designations among them; one spelling, one
system, as the law's own check, with the two collisions decided and the translator that moves a garden past them; an
input from an earlier rule and from any table the law's columns declare, the manifest among them; a refusal's words
writing a set; the weighing's bound and the pass log's folder read from the law; and the store's SQL, which calls the
law's own `fits` and names what it has no form for. Invented beings; nothing here is a fact. (`python` on Windows.)"""
import copy
import os
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
import parse as dmparse  # noqa: E402
from core import engine, law as core_law, lines, read, reckon, translate, union  # noqa: E402
from core.law import Law  # noqa: E402

FAILS = []


def check(name, cond, detail=''):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
SAY = {'say': {'by': 'w', 'at': 'now'}}


def judge(statements, law=LAW, manifest=None):
    b = engine.Bean('v', header={'bean': 'v', 'kind': 'host', 'title': 'v', 'statements': statements})
    w = engine.Bean('w', header={'bean': 'w', 'kind': 'person', 'title': 'w', 'statements': [SAY]})
    return engine.Judge(law, engine.Garden({'v': b, 'w': w}, CASES['zone'], manifest=manifest or {'gardener': 'w'}))


def reading(statements, steps, inputs=(), law=LAW, manifest=None, J=None):
    """The members of each step of a reading over a garden of one bean `v` holding `statements`, read as a rule's is."""
    J = J or judge(statements, law, manifest)
    rk = reckon.Reckoner(reckon.Judged(J), rules_law=law)
    rk.run(lines.worded({'inputs': [i if isinstance(i, dict) else
                                    {'name': i, 'origin': {'act': 'say', 'nature': 'sayable', 'by': 'law'}} for i in inputs],
                         'steps': steps}))
    return rk.env


# ------------------------------------------------------------------------------------------------ I.1 describe of a statement
env = reading([SAY, {'need': {'id': 'n1', 'by': 'self', 'of': 'w'}}, {'need': {'by': 'w', 'of': 'v'}},
               {'necessary': {'of': 'n1', 'through': 'w'}}, {'necessary': {'of': 'w#nope', 'through': 'w'}},
               {'possible': {'of': 'v#n1', 'through': 'w'}}],
              [{'id': 'n', 'op': 'select', 'entries': 'need'}, {'id': 'me', 'op': 'describe', 'of': 'n', 'as': 's'},
               {'id': 'nec', 'op': 'select', 'entries': 'necessary'},
               {'id': 'it', 'op': 'describe', 'of': 'nec', 'at': 'of', 'as': 'o'},
               {'id': 'pos', 'op': 'select', 'entries': 'possible'},
               {'id': 'far', 'op': 'describe', 'of': 'pos', 'at': 'of', 'as': 'o'}])
me = [{k: m.node['s'][k] for k in ('bean', 'verb', 'index', 'place', 'id')} for m in env['me']]
check("describe, no `at`: the member itself, a statement — its bean, verb, index, place and id (none where it has no id)",
      me == [{'bean': 'v', 'verb': 'need', 'index': '1', 'place': 'v[1] need', 'id': 'n1'},
             {'bean': 'v', 'verb': 'need', 'index': '2', 'place': 'v[2] need', 'id': None}], me)
it = [(m.node['o']['being'], m.node['o']['place'], m.node['o']['id']) for m in env['it']]
check("describe of a value naming a statement by its id in its bean: that statement's columns; none for one that names "
      "no statement, which keeps the being's columns as written",
      it == [('n1', 'v[1] need', 'n1'), ('w#nope', None, None)], it)
far = env['far'][0].node['o']
check("...and a statement named `<bean>#<id>` is that bean's statement; its place is in the member's proof",
      (far['bean'], far['place']) == ('v', 'v[1] need') and 'v[1] need' in env['far'][0].proof, (far, env['far'][0].proof))
check("a refusal's words write a described statement by its place where it names no being, a being as it is written",
      reckon.written('{s} / {o}', reckon.Row(None, {'s': env['me'][0].node['s'], 'o': env['it'][0].node['o']}, 'v'))
      == 'v[1] need / n1', reckon.written('{s} / {o}', reckon.Row(None, {'s': env['me'][0].node['s'],
                                                                           'o': env['it'][0].node['o']}, 'v')))

# ------------------------------------------------------------------------------------------------ I.9 a set in the words
m = reckon.Row(None, {'of': ['c', 'a', 'b', 'a'], 'x': {'via': 'z'}}, 'v')
check("a refusal's words write a set: `{<path>:set}`, each value once, in the order of its characters, with commas — "
      "beside `{<path>}`, a way with arrows",
      reckon.written('{of:set} | {of} | {x.via:set} | {nothing:set}.', m) == 'a, b, c | c → a → b → a | z | .',
      reckon.written('{of:set} | {of} | {x.via:set} | {nothing:set}.', m))

# ------------------------------------------------------------------------------------------------ I.3 fits, the checks
F = [({'namespace': 'orcid'}, '0000-0002-1825-0097', True), ({'namespace': 'orcid'}, '0000-0002-1825-0098', False),
     ({'namespace': 'orcid'}, '0000-0002-1825', False), ({'namespace': 'dns'}, 'example.org', True),
     ({'type': 'kebab'}, 'a-b', True), ({'type': 'kebab'}, 'A-b', False),
     ({'type': 'text'}, 'a\tb', True), ({'type': 'text'}, 'a\x07b', False),
     ({'type': 'coding'}, 'isco-08:2522', True), ({'type': 'coding'}, 'isco-08:25\u202e22', False),
     ({'system': 'ipv4'}, '192.0.2.10', True), ({'system': 'ipv4'}, '192.0.2.010', False),
     ({'system': 'osm'}, 'relation/1234567', True), ({'holds': 'Bidi_Control'}, 'ab\u202ec', True),
     ({'holds': 'Bidi_Control'}, 'abc', False), ({'holds': 'Cc'}, 'a\x07', True), ({'holds': 'L'}, '123', False)]
got = [(s, v, LAW.fits(s, v)) for s, v, _w in F]
check("fits: a namespace's pattern and check, a type's pattern and `holds_no` (but a tab in text), a system's pattern "
      "or `checked_by`, a Unicode property alone",
      [g[2] for g in got] == [w for _s, _v, w in F], [g for g, (_s, _v, w) in zip(got, F) if g[2] != w])
bad = []
for spec in ({'namespace': 'garden'}, {'type': 'position'}, {'system': 'no-such'}, {'holds': 'Bidi'}, {'colour': 'x'},
             {'namespace': 'dns', 'type': 'kebab'}):
    try:
        LAW.fits(spec, 'x')
        bad.append(spec)
    except ValueError:
        pass
check("...and a row that states no form, no row, a property Unicode does not have, or two rows at once fit nothing: "
      "refused, never false", not bad, bad)
env = reading([SAY, {'name': {'by': 'orcid', 'of': 'self', 'as': '0000-0002-1825-0097'}},
               {'name': {'by': 'orcid', 'of': 'w', 'as': '0000-0002-1825-0098'}}],
              [{'id': 'nm', 'op': 'select', 'entries': 'name'},
               {'id': 'out', 'op': 'select', 'of': 'nm', 'where': [{'path': 'as', 'fits': {'namespace': 'orcid'}}]}])
check("fits in a reading's condition: the names in their namespace's form, its check holding",
      [m.place for m in env['out']] == ['v[1] name'], [m.place for m in env['out']])
got = reckon.check_selection('r', {'steps': [{'id': 'a', 'op': 'select', 'entries': 'name',
                                               'where': [{'path': 'as', 'fits': 'orcid'}]}]}, lines.law_view(LAW))
check("...and a reading's check refuses a `fits` that names no row", any('`fits` names one row' in t for _l, t in got), got)
ck = LAW.checks
check("the checks are a closed table of the law: the seven that call a library, each with its function, and the "
      "designations, each a pattern — no problem in the law as released",
      {n for n, r in ck.items() if r.get('calls')} == set(dmparse.FORM_CHECKS)
      and {n for n, r in ck.items() if r.get('reads') == 'designation'}
      == {'rolling-bearing', 'metric-thread', 'o-ring', 'lip-seal', 'steel-grade', 'polymer'}
      and not LAW.checks_problems(), (sorted(ck), LAW.checks_problems()))
L2 = copy.copy(LAW)
L2.checks = copy.deepcopy(LAW.checks)
L2.checks['no-function'] = {'check': 'no-function', 'reads': 'name', 'calls': 'nothing', 'meaning': 'x',
                            'vectors': {'holds': ['a'], 'refuses': ['b']}}
L2.checks['polymer']['vectors']['holds'].append('pa66')
L2.checks['both'] = {'check': 'both', 'reads': 'colour', 'calls': 'x', 'pattern': '^x$', 'meaning': 'x', 'vectors': {}}
del L2.checks['tckimlik']
got = [m for _w, m in L2.checks_problems()]
check("...and a row with no function, a function with no row, a row both or neither, and a vector the row does not "
      "hold are each refused",
      any('has no function' in m for m in got) and any('`tckimlik`, which is no row' in m for m in got)
      and any('one of the two' in m for m in got) and any("'pa66' is refused" in m for m in got), got)
check("bin/parse.py applies a check by the law's row: a designation by its pattern, a library's by its function",
      dmparse.checked('rolling-bearing', '6203') is True and dmparse.checked('rolling-bearing', '6203-2RS') is False
      and dmparse.checked('ipaddress-v4', '192.0.2.1') is True and dmparse.checked('no-such', 'x') is None)

# ------------------------------------------------------------------------------------------------ I.4 one spelling
check("one spelling, one system: no sample a system teaches is in a second system's form, as the law is released",
      not core_law.spelling_problems(LAW), core_law.spelling_problems(LAW))
L3 = copy.copy(LAW)
_std = dict(LAW.std_systems(), **{'old-segment': {
    'system': 'old-segment', 'dimension': 'place', 'pattern': '^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9.:-]*$',
    'establishes': 'false', 'why': 'x', 'meaning': 'x'}})
L3.std_systems = lambda: _std
got = core_law.spelling_problems(L3)
check("...and a row whose form reads another's sample is an error of the law, naming both (the old network-segment)",
      any(w.endswith('systems.yaml osm') and 'old-segment' in m for w, m in got), got)
L4 = copy.copy(LAW)
L4.own = dict(LAW.own, systems=list(LAW.own.get('systems') or []) + [dict(_std['old-segment'])])
L4._systems = None
check("...and a garden's own system is not judged by it: a garden's rows are the garden's (parked: nb-s1-open)",
      not core_law.spelling_problems(L4) and 'old-segment' in L4.systems, core_law.spelling_problems(L4))
S = LAW.systems
check("the two collisions decided: a network is never named node, way or relation; git-remote keeps its ssh forms, "
      "and a URL is a uri",
      not dmparse.in_form(S['network-segment'], 'relation/1234567') and dmparse.in_form(S['network-segment'], 'office/vlan-13')
      and not dmparse.in_form(S['git-remote'], 'https://example.org/ledger.git')
      and dmparse.in_form(S['git-remote'], 'me@host-a:ledger') and dmparse.in_form(S['git-remote'], 'host-a:git/ledger.git')
      and dmparse.in_form(S['uri'], 'https://example.org/ledger.git'))
T = tempfile.mkdtemp(prefix='core-grammar-')
try:
    os.makedirs(os.path.join(T, 'beans'))
    body = ("---\nbean: r\nkind: document\ntitle: r\nstatements:\n  - say: { by: w, at: now }\n"
            "  - be: { by: self, at: 'git-remote:https://example.org/r.git', as: location }\n"
            "  - be: { by: self, at: 'git-remote:me@host-a:r', as: location }\n---\n\n"
            "A body that says git-remote:https://example.org/r.git stays as written.\n")
    with open(os.path.join(T, 'beans', 'r.md'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(body)
    first = translate.between('3.1', '3.2', T)
    text = open(os.path.join(T, 'beans', 'r.md'), encoding='utf-8').read()
    again = translate.between('3.1', '3.2', T)
    later = translate.between('3.2', '3.3', T)
    check("the translator moves a garden past the collision: each `git-remote:<URL>` of a statement written "
          "`uri:<URL>`, an ssh remote and the body as they were, once",
          first == ['beans/r.md'] and "'uri:https://example.org/r.git'" in text and "'git-remote:me@host-a:r'" in text
          and 'says git-remote:https://example.org/r.git' in text and again == [] and later == [], (first, text, again))
finally:
    shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------------------------------------ I.6 any law table
env = reading([SAY], [{'id': 'v', 'op': 'select', 'of': 'verbs', 'where': [{'path': 'figure', '=': 'permission'}]},
                      {'id': 'own', 'op': 'select', 'of': 'kinds', 'where': [{'path': 'garden', '=': 'true'}]},
                      {'id': 'g', 'op': 'select', 'of': 'manifest', 'where': [{'path': 'key', '=': 'gardener'}]}],
              ('verbs', 'kinds', 'manifest'), manifest={'gardener': 'w', 'zone': 'Asia/Tehran'})
mine = sorted(m.node['kind'] for m in env['own'])
vocab_kinds = sorted(str(r['kind']) for r in CASES['vocab'].get('kinds') or [] if isinstance(r, dict))
check("an input said by the law names any table its columns declare: the verbs' rows (the four on the permission "
      "square), the kinds with the garden's own marked `garden: true`, the manifest with the garden's value",
      sorted(m.node['verb'] for m in env['v']) == ['forbidden', 'obligatory', 'omissible', 'permitted']
      and mine == vocab_kinds and [m.node.get('value') for m in env['g']] == ['w']
      and env['g'][0].id == 'law:manifest[gardener]', (sorted(m.node['verb'] for m in env['v']), mine, vocab_kinds,
                                                        [m.node for m in env['g']]))
check("...each with its proof, which `daftar why` resolves to the law's row",
      reckon.law_row(LAW, 'law:verbs[forbidden]') is LAW.verbs['forbidden']
      and reckon.law_row(LAW, 'law:checks[polymer]') == LAW.checks['polymer'], reckon.law_row(LAW, 'law:checks[polymer]'))
check("...the tables the law's columns declare, the face's first: its figures, the namespaces, the checks, the systems",
      {'figures', 'namespaces', 'checks', 'systems', 'crown', 'lines', 'kinds', 'verbs', 'manifest'} <= set(LAW.declared_tables())
      and LAW.declared_tables()['lines'][0] == 'core.yaml', sorted(LAW.declared_tables()))

# ------------------------------------------------------------------------------------------------ I.5 an earlier rule
L5 = copy.copy(LAW)
L5.readings = dict(LAW.readings)
nec = copy.deepcopy(LAW.readings['necessity'])
nec['inputs'] = nec['inputs'] + [{'name': 'stood', 'from': {'rule': 'order', 'step': 'stand'}}]
nec['steps'] = nec['steps'] + [{'id': 'stood-twice', 'op': 'join', 'of': 'stood', 'with': 'stood', 'on': {'by': 'at'},
                                'keep': 'matched'}]
nec['refuse'] = nec['refuse'] + [{'of': 'stood-twice', 'message': "{by} stands at what stands at it: {at}"}]
L5.readings['necessity'] = nec
J = judge([SAY, {'stand': {'by': 'self', 'at': 'w', 'as': 'made-of'}}, {'stand': {'by': 'w', 'at': 'self', 'as': 'made-of'}}], L5)
got = [f for f in J.run() if f[0] == 'necessity']
check("an input from an earlier rule: necessity reads order's step `stand` as it was read, before it in the law's order",
      [f[1] for f in got] == ['v[1] stand', 'v[2] stand'] and 'stand' in J._steps['order'], got)
view = lines.law_view(LAW)
for name, inp, says in (
        ('a later rule', {'name': 'x', 'from': {'rule': 'squares', 'step': 'stand'}}, 'an input from an earlier rule'),
        ('no such step', {'name': 'x', 'from': {'rule': 'order', 'step': 'nothing'}}, 'an input from an earlier rule'),
        ('a table no columns declare', {'name': 'nothing', 'origin': {'act': 'say', 'nature': 'sayable', 'by': 'law'}},
         "a table the law's columns declare")):
    r = dict(nec, inputs=LAW.readings['necessity']['inputs'] + [inp])
    got = reckon.check_rule('rules[necessity].reading', r, view, law=LAW, earlier={'order': LAW.readings['order']})
    check(f"...and a rule's reading taking {name} is refused by the law's check", any(says in t for _l, t in got), got)

# ------------------------------------------------------------------------------------------------ VIII the two values
form = dict(LAW.forms['weighing'], at_most={'consistency_ratio': '7'})
entry = {'criteria': [{'name': n, 'what': n} for n in ('a', 'b', 'c')],
         'pairwise': [{'a': 'a', 'b': 'b', 'judged': '9'}, {'a': 'b', 'b': 'c', 'judged': '9'}, {'a': 'a', 'b': 'c', 'judged': '1/9'}]}
check("a weighing's bound is its form's row of the law: 0.10 as released; a law that states another judges by it",
      reckon.consistency_bound()[0] == '0.10' and reckon.check_weighing('w', entry)
      and not reckon.check_weighing('w', entry, form) and 'above 0.10' in reckon.check_weighing('w', entry)[0][1],
      (reckon.consistency_bound(), reckon.check_weighing('w', entry)))
check("a session's pass log is kept under the folder the flow law names (core/law/flows.yaml `pass_logs`)",
      LAW.pass_logs.get('session', {}).get('folder') == 'captures/passes/', LAW.pass_logs)

# ------------------------------------------------------------------------------------------------ the store's SQL
try:
    union._statement_columns_read({'steps': [{'id': 'a', 'op': 'select', 'entries': 'need'},
                                             {'id': 'b', 'op': 'describe', 'of': 'a', 'as': 's'}], 'refuse': []})
    said = None
except union.NoSQL as e:
    said = str(e)
try:
    union._statement_columns_read({'steps': [{'id': 'a', 'op': 'select', 'entries': 'need'},
                                             {'id': 'b', 'op': 'describe', 'of': 'a', 'at': 'of', 'as': 'o'}],
                                   'refuse': [{'of': 'b', 'message': '{o.place}'}]})
    said2 = None
except union.NoSQL as e:
    said2 = str(e)
check("the store's SQL names what it has no form for yet — describe of a statement — so a rule reading one is named "
      "as not judged at size, never judged without it",
      said and 'no SQL form' in said and said2 and 'o.place' in said2, (said, said2))
check("...and its `fits` is the law's own, a registered function", 'fits' in union.WORD_SIGNS
      and union.Union._fits.__doc__ and 'Law.fits' in union.Union._fits.__doc__)

print(f"core_grammar: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
