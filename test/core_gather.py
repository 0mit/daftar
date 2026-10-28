#!/usr/bin/env python3
"""core_gather — the grammar's packet (core 4.10): the gathering step, the garden's own rows as one input, a position's
unit and a code's scheme, the step that takes the first value present, the place of a bean's refusal, a statement role
narrowed by its verb, a role that refuses a rung, and a knowing act that
names its own bean's statement as `<bean>#<id>`.

Each by its vectors: `gather` groups as `first` does and writes several statements' values in one member's words
(`{<path>:set}`, `{<path>:list}`); `either` takes the first path that holds a value; `describe` gives `<as>.unit` and
`<as>.scheme`; the input `rows` gives each row a garden adds, told at `VOCAB.md <table>`; a bean's refusal is told at
its bean; the law's proof takes `verb` and `below` on a role and refuses them
misused; the gate refuses a `fail` whose `by` is a statement of another verb than `reckon`, and a person in `about`'s
`of`; and an act's `of: <its bean>#<id>` covers that statement. Invented beings; nothing here is a fact. (`python` on
Windows.)"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
from core import engine, lines, read, reckon, union  # noqa: E402
from core.law import Law  # noqa: E402

FAILS = []


def check(name, cond, detail=''):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = Law.load(('VOCAB.md', CASES['vocab']))
SAY = {'say': {'by': 'w', 'at': 'now'}}


def garden(statements, others=(), law=LAW):
    beans = {'v': engine.Bean('v', header={'bean': 'v', 'kind': 'host', 'title': 'v', 'statements': statements}),
             'w': engine.Bean('w', header={'bean': 'w', 'kind': 'person', 'title': 'w', 'statements': [SAY]})}
    for bid, kind, sts in others:
        beans[bid] = engine.Bean(bid, header={'bean': bid, 'kind': kind, 'title': bid, 'statements': sts})
    return engine.Judge(law, engine.Garden(beans, CASES['zone'], manifest={'gardener': 'w'}))


def reading(J, steps, inputs=()):
    rk = reckon.Reckoner(reckon.Judged(J), rules_law=J.L)
    rk.run(lines.worded({'inputs': [{'name': i, 'origin': {'act': 'say', 'nature': 'sayable', 'by': 'law'}}
                                    for i in inputs], 'steps': steps}))
    return rk.env


def found(J, rule=None):
    return [(r, w, m) for r, w, m in J.run() if rule is None or r == rule]


# ------------------------------------------------------------------------------------------------ gather
J = garden([SAY, {'name': {'id': 'n1', 'by': 'dns', 'of': 'self', 'as': 'a.example'}},
            {'name': {'id': 'n2', 'by': 'dns', 'of': 'x', 'as': 'b.example'}},
            {'name': {'id': 'n3', 'by': 'dns', 'of': ['x', 'self'], 'as': 'a.example'}},
            {'name': {'id': 'n4', 'by': 'dns', 'of': 'w', 'as': 'a.example'}}],
           [('x', 'host', [SAY])])
env = reading(J, [{'id': 'n', 'op': 'select', 'entries': 'name'},
                  {'id': 'g', 'op': 'gather', 'of': 'n', 'by': 'as', 'path': 'of', 'as': 'g'},
                  {'id': 'l', 'op': 'gather', 'of': 'n', 'by': ['by', 'as'], 'path': 'of', 'as': 'g', 'last': 'true'},
                  {'id': 'v', 'op': 'gather', 'of': 'n', 'by': 'as', 'path': 'of', 'as': 'g', 'groups': 'values'},
                  {'id': 'one', 'op': 'gather', 'of': 'n', 'path': 'as', 'as': 'g'},
                  {'id': 'two', 'op': 'select', 'of': 'g', 'where': [{'path': 'g.count', '>': {'count': '1', 'unit': 'item'}}]}])
got = [(m.place, m.node['g']['values'], m.node['g']['count']) for m in env['g']]
check("gather: one member of each group, its first, its values each read as the being it names, every one once, in the "
      "order the members are read in and a list's items in theirs, and how many in `item`",
      got == [('v[1] name', ['v', 'x', 'w'], {'count': '3', 'unit': 'item'}),
              ('v[2] name', ['x'], {'count': '1', 'unit': 'item'})], got)
got = [m.place for m in env['l']]
check("...and with `last: \"true\"`, the group's last stands for it, at its place", got == ['v[4] name', 'v[2] name'], got)
got = [m.node['as'] for m in env['v']]
check("...the groups in the order of their values with `groups: values`", got == ['a.example', 'b.example'], got)
got = [m.node['g']['values'] for m in env['one']]
check("...and with no `by`, every member of one group", got == [['a.example', 'b.example']], got)
got = [m.place for m in env['two']]
check("...and its count compared as a quantity", got == ['v[1] name'], got)
got = sorted(set(env['g'][0].proof))
check("...its proof every member's", got == ['v[1] name', 'v[3] name', 'v[4] name'], got)
m = reckon.as_row(env['g'][0])
got = (reckon.written("{as} names {g.values:set} ({g.count.count})", m, reckon.Judged(J)),
       reckon.written("{g.values:list}", m, reckon.Judged(J)), reckon.written("{g.values}", m, reckon.Judged(J)))
check("the words: `{<path>:set}` the values sorted, `{<path>:list}` in their order, each with `, ` between them, and "
      "`{<path>}` a list with ` → `", got == ('a.example names v, w, x (3)', 'v, x, w', 'v → x → w'), got)
view = lines.law_view(LAW).registry
RULE = {'steps': [{'id': 'n', 'op': 'select', 'entries': 'name'},
                  {'id': 'g', 'op': 'gather', 'of': 'n', 'by': 'as', 'path': 'of', 'as': 'g', 'last': 'true'}],
        'refuse': [{'of': 'g', 'message': "{g.values:list}"}]}
check("...and a rule's reading that gathers is in the grammar the law checks",
      not [t for lv, t in reckon.check_rule('r', RULE, view, LAW) if lv == 'error'],
      reckon.check_rule('r', RULE, view, LAW))
bad = dict(RULE, steps=[RULE['steps'][0], {'id': 'g', 'op': 'gather', 'of': 'n', 'by': 'as', 'as': 'g'}])
check("...and refuses a gathering with no `path`", [t for lv, t in reckon.check_rule('r', bad, view, LAW) if lv == 'error'])

# ------------------------------------------------------------------------------------------------ either
J = garden([SAY, {'attend': {'id': 'a1', 'by': 'w', 'of': 'h', 'at': '2026-10-01T10:00+03:00/2026-10-01T11:00+03:00'}},
            {'attend': {'id': 'a2', 'by': 'w', 'of': 'h'}}],
           [('h', 'happening', [SAY, {'be': {'by': 'self', 'at': '2026-10-02', 'as': 'time'}}])])
env = reading(J, [{'id': 'a', 'op': 'select', 'entries': 'attend'},
                  {'id': 'h', 'op': 'describe', 'of': 'a', 'at': 'of', 'as': 'h'},
                  {'id': 'b', 'op': 'select', 'entries': 'be'},
                  {'id': 'j', 'op': 'join', 'of': 'h', 'with': 'b', 'on': {'h.being': 'by'}, 'keep': 'both',
                   'as': ['att', 'hap']},
                  {'id': 'e', 'op': 'either', 'of': 'j', 'paths': ['att.at', 'hap.at'], 'as': 'time'},
                  {'id': 't', 'op': 'describe', 'of': 'e', 'at': 'time', 'as': 't'}])
got = [(m.place, m.node.get('time'), m.node['t']['unit']) for m in env['t']]
check("either: what the first path that holds a value holds — an attendance's own time, else its happening's",
      got == [('v[1] attend', '2026-10-01T10:00+03:00/2026-10-01T11:00+03:00', 'minute'),
              ('v[2] attend', '2026-10-02', 'day')], got)

# ------------------------------------------------------------------------------------------------ unit and scheme
J = garden([SAY, {'be': {'by': 'self', 'as': 'time', 'at': ['2026-10-01', '2026-10-01T10:00+03:00',
                                                            '2026-10-01T10:00:05+03:00', '2026-10-01T10:00:05.250+03:00',
                                                            '2026-10-01/2026-10-01T10:00+03:00', 'x', '192.0.2.10']}}])
env = reading(J, [{'id': 'b', 'op': 'select', 'entries': 'be'}, {'id': 'p', 'op': 'describe', 'of': 'b', 'at': 'at', 'as': 'p'}])
got = [m.node['p']['unit'] for m in env['p']]
check("describe of a position: `<as>.unit`, day, minute, second, millisecond; of an extent the coarser end's; none for a "
      "being or a position that is no time", got == ['day', 'minute', 'second', 'millisecond', 'day', None, None], got)
schemes = sorted(LAW.std.knowledge.schemes)
code = f"{schemes[0]}:x1"
J = garden([SAY, {'classify': {'by': 'self', 'as': code}}, {'be': {'by': 'self', 'as': 'location', 'at': 'x'}},
            {'be': {'by': 'self', 'as': 'location', 'at': 'nope-scheme:1'}}], [('x', 'host', [SAY])])
env = reading(J, [{'id': 'c', 'op': 'select', 'entries': 'classify'},
                  {'id': 'd', 'op': 'describe', 'of': 'c', 'at': 'as', 'as': 'd'},
                  {'id': 'b', 'op': 'select', 'entries': 'be'},
                  {'id': 'e', 'op': 'describe', 'of': 'b', 'at': 'at', 'as': 'e'}])
got = [m.node['d']['scheme'] for m in env['d']] + [m.node['e']['scheme'] for m in env['e']]
check("describe of a code: `<as>.scheme`, the scheme a `<scheme>:<code>` of the law's is a code of; none for a being, "
      "nor for a text whose head is no scheme", got == [schemes[0], None, None], got)

# ------------------------------------------------------------------------------------------------ rows
VOCAB = dict(CASES['vocab'])
law2 = Law.load(('VOCAB.md', {**VOCAB, 'kinds': list(VOCAB.get('kinds') or []) +
                              [{'kind': 'shed', 'nature': 'body', 'meaning': 'an invented kind'},
                               {'kind': 'barn', 'nature': 'body', 'meaning': 'another', 'vacant': 'none yet'}]}))
J = garden([SAY], law=law2)
env = reading(J, [{'id': 'r', 'op': 'select', 'of': 'rows', 'where': [{'path': 'table', '=': 'kinds'}]}], inputs=['rows'])
got = [(m.place, m.node['row'], m.node.get('vacant')) for m in env['r']]
check("the input `rows`: each row the garden adds, whatever its table, with its own columns, `table` and `row`, told at "
      "`VOCAB.md <table>`", ('VOCAB.md kinds', 'shed', None) in got and ('VOCAB.md kinds', 'barn', 'none yet') in got, got)
RULE = {'inputs': [{'name': 'rows', 'origin': {'act': 'say', 'nature': 'sayable', 'by': 'law'}}],
        'steps': [{'id': 'r', 'op': 'select', 'of': 'rows', 'where': [{'path': 'row', '=': 'shed'}]}],
        'refuse': [{'of': 'r', 'message': "`{row}` is a row this garden added"}]}
got = [(w, m) for w, m, _p in reckon.refusals(J, RULE)]
check("...a refusal of one told at its place", got == [('VOCAB.md kinds', '`shed` is a row this garden added')], got)
check("...and the law's check takes `rows` as a table the law says",
      not [t for lv, t in reckon.check_rule('r', RULE, lines.law_view(law2).registry, law2) if lv == 'error'])
check("...which the store's SQL names as having no form there",
      "input rows: the garden's own rows" in open(union.__file__, encoding='utf-8').read())

# ------------------------------------------------------------------------------------------------ a bean's place
J = garden([SAY, {'need': {'id': 'n1', 'by': 'self', 'of': 'w'}}], [('a', 'host', [SAY])])
RULE = {'steps': [{'id': 'n', 'op': 'select', 'entries': 'need'}, {'id': 'h', 'op': 'select', 'kind': 'host'}],
        'refuse': [{'of': 'h', 'message': "host"}, {'of': 'n', 'message': "need"}]}
got = [(w, m) for w, m, _p in reckon.refusals(J, RULE)]
check("a refusal of a bean told at its bean, in the order of `refuse` and of each step's members",
      got == [('v', 'host'), ('a', 'host'), ('v[1] need', 'need')], got)

# ------------------------------------------------------------------------------------------------ verb and below
law_rows = read.data(os.path.join(ROOT, 'core', 'law', 'verbs.yaml'))
spec = {r['verb']: r for r in law_rows['verbs']}
check("the law narrows `fail`'s and `meet`'s `by` to a statement of `reckon`, and refuses a body at reason in `about`'s "
      "`of`", spec['fail']['roles']['by'].get('verb') == ['reckon'] and spec['meet']['roles']['by'].get('verb') == ['reckon']
      and spec['about']['roles']['of'].get('below') == 'reason')
J = garden([SAY, {'reckon': {'id': 'r1', 'by': 'self', 'as': 'up', 'reading': {'what': 'x', 'steps': [
    {'id': 'b', 'op': 'select'}]}}}, {'need': {'id': 'n1', 'by': 'self', 'of': 'w'}},
            {'fail': {'by': 'r1', 'as': 'down'}}, {'fail': {'by': 'n1', 'as': 'down'}}])
got = [(w, m) for r, w, m in found(J, 'valency')]
check("valency: a `fail` whose `by` is a `reckon` stands, and one whose `by` is a statement of another verb is refused, "
      "saying which", got == [('v[4] fail', "`by`: not a being: 'n1' is no bean of this garden, nor `self`, nor the "
                                            "crown, nor a being kept in a store (`store:<kind>:<id>`); not a statement: "
                                            "'n1' is a `need`, and this role takes a statement of `reckon`")], got)
J = garden([SAY, {'about': {'by': 'd', 'of': ['x', 'w']}}], [('x', 'host', [SAY]), ('d', 'document', [SAY])])
got = [(w, m) for r, w, m in found(J, 'valency')]
check("...and an `about` naming a person is refused, a host it names standing",
      got == [('v[1] about', "`of`: a body fills this role only below reason; w is a person, at reason")], got)
bad = {**VOCAB, 'verbs': list(VOCAB.get('verbs') or []) + [
    {'verb': 'tally', 'meaning': 'an invented verb', 'roles': {'by': {'shape': 'being', 'verb': ['reckon']},
                                                                'of': {'shape': 'statement', 'verb': ['nope']},
                                                                'to': {'shape': 'being', 'rung': 'reason', 'below': 'reason'},
                                                                'at': {'shape': 'being', 'below': 'nope'}},
     'required': ['by']}]}
errs = [m for _r, w, m in Law.load(('VOCAB.md', bad)).problems() if 'tally' in w]
words = ' '.join(errs)
check("the law's proof refuses `verb` on a role that takes no statement, a verb it does not have, `rung` with `below`, and "
      "`below` at no level", all(w in words for w in ("narrows a role that takes a statement", "names 'nope', no verb",
                                                      "not both", "no level 'nope'")), errs)

# ------------------------------------------------------------------------------------------------ knowing
J = garden([{'say': {'by': 'w', 'at': 'now', 'of': ['v#s1', 's2']}}, {'need': {'id': 's1', 'by': 'self', 'of': 'w'}},
            {'need': {'id': 's2', 'by': 'self', 'of': 'w'}}, {'need': {'id': 's3', 'by': 'self', 'of': 'w'}}])
got = [(w, m[:20]) for r, w, m in found(J, 'knowing')]
check("knowing: an act's `of: <its own bean>#<id>` covers that statement, as its id does; a statement none names is "
      "refused", got == [('v[3] need', 'known by no act: say')], got)
J = garden([{'say': {'by': 'w', 'at': 'now', 'of': ['x#s1']}}, {'need': {'id': 's1', 'by': 'self', 'of': 'w'}}],
           [('x', 'host', [SAY, {'need': {'id': 's1', 'by': 'self', 'of': 'w'}}])])
got = [w for r, w, m in found(J, 'knowing')]
check("...and another bean's `<bean>#<id>` covers nothing here", got == ['v[1] need'], got)

print(f"\n{'FAIL' if FAILS else 'PASS'}: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
