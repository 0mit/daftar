#!/usr/bin/env python3
"""core_grammar — the reading grammar, part one (core 3.2, the next machinery's design, body I: I.1, I.3, I.4, I.5, I.6 and
I.9's set words), part two (core 3.3: I.2, I.7, I.8) and part three (core 3.4: I.9, a refusal told at a path), and the
two values the law now holds (body VIII).

Each by its vectors: `describe` of a statement — the member itself, or a value naming one; the comparator `fits` and
the law's table of checks, closed both ways and held to its vectors, the designations among them; one spelling, one
system, as the law's own check, with the two collisions decided and the translator that moves a garden past them; an
input from an earlier rule and from any table the law's columns declare, the manifest among them; a refusal's words
writing a set; the weighing's bound and the pass log's folder read from the law; a path through every depth, `describe`
of a position and the operation `overlap`; a refusal told at a path inside its statement; and the store's SQL, which has
a form for each and names what it has none for. Invented beings; nothing here is a fact. (`python` on Windows.)"""
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
    # THE LADDER BY ITS LINES (core 4.0): a garden's own kinds and levels of an earlier core, rewritten by positions
    vocab = ("---\nkinds:\n"
             "  - { kind: hive, nature: body, level: population, meaning: \"a colony of bees\" }   # its bees\n"
             "  - { kind: cell, nature: body, line: living, level: cell, vacant: \"a case\" }\n"
             "  - kind: boat\n    nature: body\n    line: made\n    level: device\n"
             "  - { kind: component, nature: body, level: device }\n"
             "  - { kind: grain, nature: body, line: matter, level: molecule }\n"
             "  - { kind: clause, nature: sayable, line: said, level: statement }\n"
             "  - { kind: mind, nature: body, level: colony, rung: reason }\n"
             "  - { kind: helper, nature: sayable }\n"
             "levels:\n  - { level: colony, line: living, stands: [ { at: organism, as: made-of } ], meaning: \"x\" }\n"
             "---\n# the garden's own rows\n")
    with open(os.path.join(T, 'VOCAB.md'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(vocab)
    moved = translate.between('3.7', '4.0', T)
    text = open(os.path.join(T, 'VOCAB.md'), encoding='utf-8').read()
    rows = dmparse.loads(dmparse.split_front_matter(text)[0])
    kinds = {str(r['kind']): r for r in rows['kinds']}
    again = translate.between('3.7', '4.0', T)
    check("the translator moves a garden's own kinds to core 4.0: each level a position on its line now, a level of the "
          "living also bios living, a rung on the rung line, a block row written on one line, its comment kept; one the "
          "law holds as written (cell) is the law's; one written otherwise (component at device) stays for the gate to "
          "name; a level of its own on organisation; once",
          moved == ['VOCAB.md'] and 'cell' not in kinds
          and kinds['hive'] == {'kind': 'hive', 'nature': 'body', 'organisation': 'population', 'bios': 'living',
                                'meaning': 'a colony of bees'} and '# its bees' in text
          and kinds['boat'] == {'kind': 'boat', 'nature': 'body', 'organisation': 'device'}
          and kinds['component'] == {'kind': 'component', 'nature': 'body', 'organisation': 'device'}
          and kinds['grain'] == {'kind': 'grain', 'nature': 'body', 'matter': 'molecule'}
          and kinds['clause'] == {'kind': 'clause', 'nature': 'sayable', 'organisation': 'statement'}
          and kinds['mind'] == {'kind': 'mind', 'nature': 'body', 'organisation': 'colony', 'bios': 'living',
                                'rung': 'reason'}
          and kinds['helper'] == {'kind': 'helper', 'nature': 'sayable'}
          and rows['levels'][0]['line'] == 'organisation' and again == [], (moved, text, again))
    # WHOM A RECORD CONCERNS, AND WHAT IT IS ABOUT (core 4.1, D16): `concern` a person's alone, the rest `about`
    os.makedirs(os.path.join(T, 'mappings'))

    def doc(space, bid, kind, *sts):
        with open(os.path.join(T, space, bid + '.md'), 'w', encoding='utf-8', newline='') as fh:
            fh.write(f"---\nbean: {bid}\nkind: {kind}\ntitle: {bid}\nstatements:\n  - say: {{ by: w, at: now }}\n"
                     + ''.join(f"  - {s}\n" for s in sts) + "---\n\nIt concerns: h1, as words, unchanged.\n")
    doc('beans', 'p1', 'person')
    doc('beans', 'h1', 'host')
    doc('beans', 'm1', 'mind')
    doc('mappings', 'mp', 'host')
    doc('beans', 'd1', 'document', 'concern: { of: [h1, p1, mp, m1] }   # the people and the machines')
    doc('beans', 'd2', 'document', 'concern: { id: c2, by: w, of: [h1] }')
    doc('beans', 'd3', 'document', 'concern: { of: [p1] }')
    doc('beans', 'd4', 'document', 'concern: { of: [h1, nobody-here] }')
    doc('beans', 'd5', 'document', 'concern: { of: [{ someone: person }, self] }')
    moved = translate.between('4.0', '4.1', T)
    got = {b: [ln.strip() for ln in open(os.path.join(T, 'beans', b + '.md'), encoding='utf-8').read().split('\n')
               if ln.strip().startswith(('- concern:', '- about:'))] for b in ('d1', 'd2', 'd3', 'd4', 'd5')}
    again = translate.between('4.0', '4.1', T)
    check("the translator moves a garden's `concern` to core 4.1: the persons it names stay (a kind at reason, a mapping's "
          "being read as a bean's), each other being goes to an `about` beside it with its `by`, and a concern of no person "
          "is `about` whole, its id kept; one naming what is no bean here stays for the gate; its body unchanged; once",
          moved == ['beans/d1.md', 'beans/d2.md', 'beans/d5.md']
          and got['d1'] == ['- concern: { of: [p1, m1] }   # the people and the machines', '- about: { of: [h1, mp] }']
          and got['d2'] == ['- about: { id: c2, by: w, of: [h1] }'] and got['d3'] == ['- concern: { of: [p1] }']
          and got['d4'] == ['- concern: { of: [h1, nobody-here] }']
          and got['d5'] == ['- concern: { of: [{ someone: person }] }', '- about: { of: [self] }']
          and 'It concerns: h1, as words' in open(os.path.join(T, 'beans', 'd1.md'), encoding='utf-8').read()
          and again == [], (moved, got, again))
    # THE KINDS THE LAW TOOK (core 4.7): a garden's own row of a kind the law now holds goes
    vocab = ("---\n# == THE CORE'S ROWS ==\nkinds:\n- kind: checklist\n  nature: sayable\n- kind: procedure\n"
             "  nature: sayable\n"
             "- { kind: series, nature: sayable, meaning: \"the garden's own words\", vacant: \"a case\" }\n"
             "- { kind: site, nature: sayable }   # written otherwise: the law's site is a body\n"
             "- { kind: model, nature: body, organisation: device }\n"
             "flows:\n- flow: sent-out\n  from: estate\n  to: remote\n---\n# the garden's own rows\n")
    with open(os.path.join(T, 'VOCAB.md'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(vocab)
    moved = translate.between('4.6', '4.7', T)
    text = open(os.path.join(T, 'VOCAB.md'), encoding='utf-8').read()
    kinds = {str(r['kind']): r for r in dmparse.loads(dmparse.split_front_matter(text)[0])['kinds']}
    again = translate.between('4.6', '4.7', T)
    with open(os.path.join(T, 'VOCAB.md'), 'w', encoding='utf-8', newline='') as fh:
        fh.write("---\nkinds:\n  - { kind: procedure, nature: sayable, meaning: \"a way a thing is done, step by step: "
                 "a walk\" }\nnamespaces:\n  - { namespace: anchor-hostname, once: \"false\" }\n---\n# rows\n")
    alone = translate.between('4.6', '4.7', T)
    left = open(os.path.join(T, 'VOCAB.md'), encoding='utf-8').read()
    check("the translator moves a garden's own kinds to core 4.7: a row of a kind the law now holds with the same nature "
          "and positions is the law's and goes (procedure in a block, series on one line, its meaning and `vacant` "
          "aside); one written otherwise (site a sayable, model a body) stays for the gate to name, its comment kept; "
          "the rest of the file as it was; once; and a list left with no row goes with its key",
          moved == ['VOCAB.md'] and sorted(kinds) == ['checklist', 'model', 'site']
          and '# written otherwise' in text and 'flows:\n- flow: sent-out\n' in text and "# == THE CORE'S ROWS ==" in text
          and again == [] and alone == ['VOCAB.md'] and 'kinds' not in left
          and 'namespaces:\n  - { namespace: anchor-hostname' in left, (moved, text, again, left))
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

# ------------------------------------------------------------------------------------------------ part two (core 3.3)
# I.7, a path segment for every depth
segs = dmparse.path_read('details.**.b')
check("a path's segment `**` reads every key and item below, at any depth: the one path reader, and the law's "
      "`field_path` (and `***` is no segment)",
      [s.key for s in segs] == ['details', '**', 'b'] and LAW.fits({'type': 'field_path'}, 'details.**.b')
      and LAW.fits({'type': 'field_path'}, '**') and not LAW.fits({'type': 'field_path'}, 'a.***')
      and dmparse.path_problem('a.***'), segs)
below = reckon.walk(None, {'a': [{'b': 'x', 'id': 'q'}, 'y'], 'c': {'d': 'z'}}, '**', at='v')
check("...each value of a map and each item of a list, each before what it holds, where it is named as any path names it",
      below == [([{'b': 'x', 'id': 'q'}, 'y'], 'v:a'), ({'b': 'x', 'id': 'q'}, 'v:a[q]'), ('x', 'v:a[q].b'),
                ('q', 'v:a[q].id'), ('y', 'v:a[1]'), ({'d': 'z'}, 'v:c'), ('z', 'v:c.d')], below)
check("...and a key after it is read at every depth: `**.b`",
      [v for v, _w in reckon.walk(None, {'b': 1, 'a': [{'b': 2, 'c': {'b': 3}}]}, '**.b')] == [2, 3],
      reckon.walk(None, {'b': 1, 'a': [{'b': 2, 'c': {'b': 3}}]}, '**.b'))


def judged(statements, details=None, also=()):
    h = {'bean': 'v', 'kind': 'host', 'title': 'v', 'statements': statements}
    if details is not None:
        h['details'] = details
    beans = {'v': engine.Bean('v', header=h),
             'w': engine.Bean('w', header={'bean': 'w', 'kind': 'person', 'title': 'w', 'statements': [SAY]})}
    for b in also:
        beans[b.id] = b
    return engine.Judge(LAW, engine.Garden(beans, CASES['zone'], manifest={'gardener': 'w'}))


env = reading(None, [{'id': 'hay', 'op': 'select', 'where': [{'path': '**', '=': 'needle'}]},
                     {'id': 'title', 'op': 'select', 'where': [{'path': 'title', '=': 'w'}]}],
              J=judged([SAY], details={'deep': [{'x': 'needle'}]}))
check("...over a rule's garden, whose beans are their whole header and their verbs: a text in `details`, at any depth, "
      "and a bean's title", [m.id for m in env['hay']] == ['v'] and [m.id for m in env['title']] == ['w'],
      (env['hay'], env['title']))

# I.2, describe of a position
AT = ['2026-10-01', 'w', '2026-10-01 10:00+03:30', '2026-10-01/2026-10-03', '192.0.2.10', 'now', 'zz!']
env = reading([SAY, {'be': {'by': 'self', 'at': AT, 'as': 'location'}}],
              [{'id': 'be', 'op': 'select', 'entries': 'be'}, {'id': 'p', 'op': 'describe', 'of': 'be', 'at': 'at', 'as': 'p'}])
cols = [tuple(m.node['p'][k] for k in ('system', 'point', 'from', 'to')) for m in env['p']]
check("describe of a position: its system, whether it names a point, and its span to the moment — a day its whole, a "
      "moment itself, an extent to the end of its end — written in UTC; a place no span; none for a being, `now`, or "
      "what no system reads",
      cols == [('gregorian-civil', 'true', '2026-10-01 00:00:00.000Z', '2026-10-02 00:00:00.000Z'),
               (None,) * 4, ('gregorian-civil', 'true', '2026-10-01 06:30:00.000Z', '2026-10-01 06:30:00.000Z'),
               ('gregorian-civil', 'true', '2026-10-01 00:00:00.000Z', '2026-10-04 00:00:00.000Z'),
               ('ipv4', 'true', None, None), (None,) * 4, (None,) * 4], cols)
area = next((n for n, r in LAW.systems.items() if isinstance(r, dict) and r.get('covers') == 'area'), None)
J = judge([SAY])
p = engine.frame.read('192.0.2.10', LAW.systems, None)
check("...`point` by its system's `covers`, as rule room reads it (core/frame.py `covers_point`, the one reader): an "
      "area holds many", J.at_point(p) and engine.frame.covers_point(p, LAW.systems)
      and (area is None or not engine.frame.covers_point(engine.frame.Position('x', area), LAW.systems)), area)

# I.8, overlap
ATT = [('w', '2026-10-01 10:00+03:30/2026-10-01 12:00+03:30'), ('w', '2026-10-01 11:00+03:30/2026-10-01 13:00+03:30'),
       ('w', '2026-10-01 09:00+03:30/2026-10-01 10:30+03:30'), ('self', '2026-10-01 09:00+03:30/2026-10-01 10:30+03:30'),
       ('w', '2026-10-01 13:00+03:30/2026-10-01 14:00+03:30'), ('w', '2026-10-01')]
steps = [{'id': 'att', 'op': 'select', 'entries': 'attend'}, {'id': 't', 'op': 'describe', 'of': 'att', 'at': 'at', 'as': 't'},
         {'id': 'who', 'op': 'describe', 'of': 't', 'at': 'by', 'as': 'who'}]
env = reading([SAY] + [{'attend': {'by': b, 'of': 'v', 'at': a}} for b, a in ATT],
              steps + [{'id': 'all', 'op': 'overlap', 'of': 'who', 'from': 't.from', 'to': 't.to', 'by': 'who.being',
                        'as': ['a', 'b']},
                       {'id': 'first', 'op': 'overlap', 'of': 'who', 'from': 't.from', 'to': 't.to', 'by': 'who.being',
                        'first': 'true', 'as': ['a', 'b']},
                       {'id': 'held', 'op': 'overlap', 'of': 'who', 'by': 'who.being', 'groups': 'values',
                        'as': ['a', 'b']}])
pairs = lambda k: [(m.place, m.node['a']['who']['being'], m.node['a']['t']['being'][11:16],  # noqa: E731
                    m.node['b']['t']['being'][11:16]) for m in env[k]]
check("overlap: the pairs of one group (`by`, each value the being it names) whose spans overlap — touching ends do not "
      "— in the order of their starts, each told at the later's place; a day overlaps its hours",
      pairs('all') == [('v[3] attend', 'w', '', '09:00'), ('v[1] attend', 'w', '', '10:00'),
                       ('v[2] attend', 'w', '', '11:00'), ('v[5] attend', 'w', '', '13:00'),
                       ('v[1] attend', 'w', '09:00', '10:00'), ('v[2] attend', 'w', '10:00', '11:00')], pairs('all'))
check("...with `first`, the first alone with each later one",
      pairs('first') == [('v[3] attend', 'w', '', '09:00'), ('v[1] attend', 'w', '', '10:00'),
                         ('v[2] attend', 'w', '', '11:00'), ('v[5] attend', 'w', '', '13:00')], pairs('first'))
check("...and with no span, every two of a group, the groups in the order of their values ('self' read as its bean)",
      [p[:2] for p in pairs('held')] == [('v[2] attend', 'w'), ('v[3] attend', 'w'), ('v[5] attend', 'w'),
                                         ('v[6] attend', 'w'), ('v[3] attend', 'w'), ('v[5] attend', 'w'),
                                         ('v[6] attend', 'w'), ('v[5] attend', 'w'), ('v[6] attend', 'w'),
                                         ('v[6] attend', 'w')] and len(env['held']) == 10, pairs('held'))
got = reckon.check_rule('x', {'steps': steps + [{'id': 'o', 'op': 'overlap', 'of': 'who', 'as': ['a', 'b'],
                                                 'first': 'maybe'}], 'refuse': [{'of': 'o', 'message': 'm'}]},
                        lines.law_view(LAW).registry, LAW)
check("...a step of the law's closed list, its takes checked as any operation's", any('first' in t for _l, t in got), got)
try:
    reading([SAY], [{'id': 'a', 'op': 'select', 'entries': 'attend'},
                    {'id': 'o', 'op': 'overlap', 'of': 'a', 'from': 'at', 'as': ['a', 'b']}])
    said = None
except reckon.Refused as e:
    said = str(e)
check("...and a span is read from two paths or none", said and 'from' in said and 'to' in said, said)

# ------------------------------------------------------------------------------------------------ part three (core 3.4)
# I.9, a refusal told at a path inside its statement
RULE = {'steps': [{'id': 'pay', 'op': 'select', 'entries': 'pay'},
                  {'id': 'xts', 'op': 'select', 'of': 'pay', 'where': [{'path': 'of.unit', '=': 'XTS'}]},
                  {'id': 'beans', 'op': 'select', 'kind': 'person'}],
        'refuse': [{'of': 'xts', 'at': 'of.unit', 'message': "{of.count} {of.unit}"},
                   {'of': 'xts', 'message': "{of.unit}"},
                   {'of': 'beans', 'at': 'title', 'message': "{bean}"}]}
J = judge([SAY, {'pay': {'by': 'w', 'of': {'count': '3', 'unit': 'XTS'}}},
           {'pay': {'by': 'w', 'of': {'count': '1', 'unit': 'USD'}}}])
got = [(w, m) for w, m, _p in reckon.refusals(J, RULE)]
check("a refusal told at a path (`at`): at that path inside its statement, `<bean>[<i>] <verb>.<at>`; one with none at "
      "its statement; a member that is no statement has no place, and none is made for it",
      got == [('v[1] pay.of.unit', '3 XTS'), ('v[1] pay', 'XTS'), (None, 'w')], got)
view = lines.law_view(LAW).registry
check("...and the law's check takes `{of, at, message}`, `at` a path of the statement's keys",
      not [t for lv, t in reckon.check_rule('r', RULE, view, LAW) if lv == 'error'],
      reckon.check_rule('r', RULE, view, LAW))
for bad in ('**', 'of.*', 'of>kind', 'v:of', 'of[unit=XTS]', 'Of', 3, ''):
    r = dict(RULE, refuse=[{'of': 'xts', 'at': bad, 'message': 'm'}])
    got = [t for lv, t in reckon.check_rule('r', r, view, LAW) if lv == 'error']
    check(f"...and refuses `at: {bad!r}`: each segment one key, as a place names it",
          any('`at` is a path' in t for t in got), got)
got = [t for lv, t in reckon.check_rule('r', dict(RULE, refuse=[{'of': 'xts', 'at': 'of', 'message': 'm', 'why': 'x'}]),
                                        view, LAW) if lv == 'error']
check("...and a refusal holds nothing else", any('at?: <path>' in t for t in got), got)

# ------------------------------------------------------------------------------------------------ the store's SQL
check("the store's SQL has a form for each column, comparator and operation the grammar gained — a statement's and "
      "a position's columns, a bean's header, `**` and a value's parts, `fits`, `overlap`, a refusal's `at` — each read "
      "by the reckoner's own reader through a function the connection registers (test/store_union.py holds each to "
      "the reckoner over every case kept five ways)",
      hasattr(union.Union, '_op_overlap') and 'fits' in union.WORD_SIGNS and 'Law.fits' in union.Union._fits.__doc__
      and union.STATEMENT_COLUMNS == reckon.STATEMENT_COLUMNS and union.POSITION_COLUMNS == reckon.POSITION_COLUMNS
      and not hasattr(union, '_statement_columns_read'))
check("...a description's statement and position columns computed only where a reading reads them — named, or the "
      "description read whole, or read through `**` — so order, which reads its descriptions' kinds alone, pays none "
      "over a store's millions of rows",
      union._wanted(LAW.readings['order']) == set() and union._wanted(LAW.readings['life']) == {'who', 'via'}
      and union._wanted({'steps': [{'id': 'a', 'op': 'describe', 'of': 'x', 'at': 'of', 'as': 'o'},
                                   {'id': 'b', 'op': 'describe', 'of': 'a', 'at': 'by', 'as': 'p'}],
                         'refuse': [{'of': 'b', 'message': '{o.place} {p.kind}'}]}) == {'o'},
      (union._wanted(LAW.readings['order']), union._wanted(LAW.readings['life'])))
st = union.Step('s', {'of': ('w0', 'n0', None)}, ['k'], None, 'statement', ('statement', 'pay'), nodes=[('=', '_raw')])
beans = union.Step('b', {'bean': ('w0', 'w0', None)}, ['k'], None, 'bean', ('bean',),
                   nodes=[('?bean', 'w0')], thin=[('', ('bean', 'kind') + union.HEADER)])
said = []
for step, path in ((st, 'of>kind'), (st, 'v:of'), (beans, 'pay.of'), (beans, '**')):
    try:
        union.Union._path_ok(None, step, path, 'here')
        said.append(None)
    except union.NoSQL as e:
        said.append(str(e))
check("...and names what it still has none for — a path that starts at another bean or follows a ref, and a "
      "bean's statements, which no step carries — so a rule reading one is named as not judged at size, never judged "
      "without it",
      all(said) and 'follows a ref' in said[0] and 'statements' in said[2], said)

print(f"core_grammar: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
