#!/usr/bin/env python3
"""core_conformance — one verdict at every door (core 2.24, D13: one judge), over the conformance corpus.

The corpus is test/core-cases.yaml: its garden, its good cases, its bad ones and its faults judged as files, and its
`clauses` — each rule's `says` cut at its sentences and semicolons, every clause named with what breaks it. A garden is
grown on disk from the cases, as test/core_save.py grows one, and each fault is judged at each door:

    save, again   bin/save.py and --again: the pre-commit hook's refusal, as an agent reads it
    staged        the one judge, the scope `staged`: the tree's verdict and the commit's own rules after it, nothing else
    tree          the one judge, the scope `tree` (core/check.py, bin/check.py --all)
    propose       bin/propose.py's read of a proposal, here one that takes nothing
    store         bin/store.py's check, the union of git and no store: the tree's verdict, and what the keepings add
    hub           bin/hub.py's gate and the one judge's scope `commits`: the commit checked out, judged by its own gate
    replay        the one judge's scope `replay`, which the hub runs after its gate: the commit's own rules replayed against
                  its parent, all but the clock's register (core 3.5, II.3) — the commit's doors' verdict, there

A fault of the tree is the same finding at every door. A fault of a commit (`commit`) is refused at the commit's
doors alike, the hub's replay among them, and passes the tree's, whose rules it does not break. Every clause names a fault, and every fault is
refused by the clause's rule, naming the bean it breaks. (`python` on Windows.)"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
import machine  # noqa: E402
machine.ensure()      # its time source and standards cache, not the machine's
import yaml  # noqa: E402
from core import read  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=''):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


CASES = read.data(os.path.join(ROOT, 'test', 'core-cases.yaml'))
LAW = read.data(os.path.join(ROOT, 'core', 'law', 'core.yaml'))
RULES = [str(r['rule']) for r in LAW['rules']]


def clauses(says):
    """A rule's `says` cut into its clauses: at each sentence's end, and at each semicolon."""
    return [c for c in re.split(r'(?<=[a-z0-9`)\'"])(?:; |\. )(?=[A-Za-z`])', says) if c]


# ------------------------------------------------------------------------------------------------ the map of clauses
KINDS = ('bad', 'disk', 'good', 'garden', 'commit', 'suite')
BAD = {(str(c['rule']), str(c['bean'])): c for c in CASES['bad'] + CASES['disk']}
GOOD = {str(c['bean']): c for c in CASES['good']}
wrong = []
for r in LAW['rules']:
    rule, mine = str(r['rule']), CASES['clauses'].get(str(r['rule'])) or []
    cut = clauses(str(r['says']))
    if len(cut) != len(mine):
        wrong.append(f"{rule}: {len(cut)} clauses, {len(mine)} named")
        continue
    for c, m in zip(cut, mine):
        if not c.startswith(str(m.get('says'))):
            wrong.append(f"{rule}: {c[:60]!r} is named {m.get('says')!r}")
        if not any(m.get(k) for k in KINDS) or set(m) - set(KINDS) - {'says'}:
            wrong.append(f"{rule}: {c[:60]!r} names no fault of {', '.join(KINDS)}")
        for b in m.get('bad') or []:
            if (rule, str(b)) not in BAD:
                wrong.append(f"{rule}: the case {b} is no bad case of {rule}")
        for b in m.get('good') or []:
            if str(b) not in GOOD:
                wrong.append(f"{rule}: the case {b} is no good case")
        for s in m.get('suite') or []:
            p = os.path.join(ROOT, s)
            if not os.path.isfile(p) or rule not in open(p, encoding='utf-8').read():
                wrong.append(f"{rule}: {s} does not judge it")
check(f"every clause of the law's {len(RULES)} rules ({sum(len(clauses(str(r['says']))) for r in LAW['rules'])}) "
      f"names what breaks it, in the order its rule says it, and every case it names is one", not wrong, wrong)
check("...and the rules the map names are the law's, all of them", list(CASES['clauses']) == RULES,
      (list(CASES['clauses']), RULES))

# ------------------------------------------------------------------------------------------------ the garden, grown
T = tempfile.mkdtemp(prefix='core-conformance-')
G = os.path.join(T, 'g')
ENV = dict(os.environ, DAFTAR_GATE_ALL='1', PYTHONDONTWRITEBYTECODE='1')


def git(*a):
    return subprocess.run(['git', '-C', G, *a], capture_output=True, text=True, encoding='utf-8', errors='replace')


def run(*a):
    r = subprocess.run(list(a), cwd=G, capture_output=True, text=True, encoding='utf-8', errors='replace', env=ENV)
    return r.returncode, r.stdout + r.stderr


KNOWING = ('say', 'read', 'derive', 'make')


def saved(statements):
    """The statements as a save writes them first: a knowing act at `now`, whose moment the save writes. (A garden made
    in memory may say a moment; one committed says the save's.)"""
    return [{v: dict(r, at='now') if v in KNOWING and isinstance(r, dict) and isinstance(r.get('at'), str) else r
             for v, r in st.items()} for st in statements]


def doc(bid, c, body='\nWords.\n'):
    h = {'bean': bid, 'kind': c['kind'], 'title': bid, 'statements': c['statements']}
    h.update(c.get('header') or {})
    return '---\n' + yaml.safe_dump(h, allow_unicode=True, sort_keys=False, width=200) + '---\n' + body


def write(rel, text):
    if text is None:                                # a file the case takes out
        os.remove(os.path.join(G, rel))
        return
    os.makedirs(os.path.dirname(os.path.join(G, rel)) or G, exist_ok=True)
    with open(os.path.join(G, rel), 'w', encoding='utf-8', newline='') as fh:
        fh.write(text)


def found_lines(text):
    """The findings a door printed: `<rule>  <where>: <what>`, every place named (DAFTAR_GATE_ALL)."""
    pat = re.compile(r'^(' + '|'.join(sorted(RULES + ['gate'], key=len, reverse=True)) + r')\s+\S')
    return sorted(ln.rstrip() for ln in text.split('\n') if pat.match(ln))


def lines_of(found):
    return sorted(f"{r:<11} {w}: {m}" for r, w, m in found)


DRIVER = r'''
import os, sys
sys.path[:0] = [os.getcwd(), os.path.join(os.getcwd(), 'bin')]
if sys.argv[1] == 'propose':
    import propose
    propose._core_apply = lambda a, tmp: None
    print('\n'.join(propose.core_gate({})[1]))
else:
    import hub
    try:
        hub.gate(os.popen('git rev-parse HEAD').read().strip(), dict(os.environ, GIT_DIR=os.path.join(os.getcwd(), '.git')), '.')
        print('ACCEPTED')
    except hub.Refused as x:
        print('REFUSED ' + str(x))
'''


def doors(what, body):
    """Each door's findings over the faults written in the working tree, as lines; the commit's doors save them."""
    sys.path[:0] = [G, os.path.join(G, 'bin')]
    from core import commit, engine, judge as dmjudge
    import store as dmstore
    out, before = {}, git('rev-parse', 'HEAD').stdout.strip()
    out['save'] = run(PY, 'bin/save.py', 'sam', what, '--body', body)
    out['again'] = run(PY, 'bin/save.py', '--again')
    scope = dmjudge.Scope.staged(G)
    staged = dmjudge.judge(None, scope)
    law = dmjudge.garden_law(G, dmjudge.carried(G))
    tree = dmjudge.judge(law, dmjudge.Scope.tree(G))
    out['commit'] = commit.findings(G, law, garden=scope.garden)
    out['staged'], out['tree'] = staged, tree
    out['store'] = dmstore.check([], root=G, law=law)
    out['keepings'] = dmstore._check([], engine.Garden.read(G), law, tree)   # with no store, the pointers' queries
    out['propose'] = run(PY, '-c', DRIVER, 'propose')
    git('add', '-A')
    git('commit', '-q', '--no-verify', '-m', 'the faults, past the gate')
    head = git('rev-parse', 'HEAD').stdout.strip()
    out['judge'] = dmjudge.judge(None, dmjudge.Scope.commits([head], dict(os.environ, GIT_DIR=os.path.join(G, '.git'))))
    out['replay'] = dmjudge.judge(None, dmjudge.Scope.replay([head], dict(os.environ, GIT_DIR=os.path.join(G, '.git'))))
    out['hub'] = run(PY, '-c', DRIVER, 'hub')
    git('reset', '-q', '--hard', before)            # the garden as it was: what the save or the hub's commit made, undone
    git('clean', '-qfd')
    del sys.path[:2]
    return out


def agree(name, d, tree_rules=True):
    """The doors over one set of faults: the commit's doors alike; the tree's alike; the two apart by the commit's
    rules alone. With `tree_rules` False the faults are the commit's, and the tree's doors pass them."""
    save, again = found_lines(d['save'][1]), found_lines(d['again'][1])
    staged, tree = lines_of(d['staged']), lines_of(d['tree'])
    check(f"{name}: the save and its --again refuse, alike, with the staged scope's verdict",
          d['save'][0] == 1 and d['again'][0] == 1 and save == again == staged, (d['save'][1][-900:], save, staged))
    check(f"{name}: the staged scope is the tree's verdict and then the commit's own rules, nothing else",
          d['staged'] == d['tree'] + d['commit'], (len(d['staged']), len(d['tree']), len(d['commit'])))
    union = d['tree'] + [f for f in dict.fromkeys(d['keepings']) if f not in d['tree']]
    check(f"{name}: the tree's doors agree — propose, the hub's checkout and the one judge's commits; the store's union is "
          f"the tree's verdict and what the keepings add (here, with no store, the pointers' queries)",
          found_lines(d['propose'][1]) == tree and lines_of(d['judge']) == tree and d['store'] == union
          and d['hub'][1].startswith('REFUSED' if tree else 'ACCEPTED'),
          (found_lines(d['propose'][1])[:3], lines_of(d['judge'])[:3], d['hub'][1][:300], tree[:3]))
    check(f"{name}: the hub's replay of the commit's own rules against its parent gives the commit's verdict",
          lines_of(d['replay']) == lines_of(d['commit']), (lines_of(d['replay'])[:3], lines_of(d['commit'])[:3]))
    if not tree_rules:
        check(f"{name}: the tree's doors pass what only a commit breaks", not tree, tree)


def refused(d, rule, bean, says=''):
    return any(r == rule and str(w).split('[')[0].split(':')[0] == bean and says in m for r, w, m in d['tree'])


try:
    os.makedirs(G)
    git('init', '-q')
    git('config', 'user.name', 'sam')
    git('config', 'user.email', 'sam@example.invalid')
    ignore = shutil.ignore_patterns('__pycache__')
    for d in ('bin', 'core', 'seed'):              # the release's own tools, law and seed, as a garden carries them
        shutil.copytree(os.path.join(ROOT, d), os.path.join(G, d), ignore=ignore)
    write('GARDEN.md', '---\n' + yaml.safe_dump({'garden': 'conformance', 'extends': f"core@{LAW['version']}",
                                                'gardener': 'sam', 'zone': CASES['zone']}, sort_keys=False) + '---\n')
    vocab = {k: [dict(r, vacant=r.get('vacant') or "the cases' row") if k in ('kinds', 'namespaces') and
                 isinstance(r, dict) else r for r in v] if isinstance(v, list) else v for k, v in CASES['vocab'].items()}
    VOCAB = '---\n' + yaml.safe_dump(vocab, allow_unicode=True, sort_keys=False, width=200) + '---\n'
    write('VOCAB.md', VOCAB)
    write('log/journal.md', '# Journal\n')
    git('add', '-A')
    git('commit', '-q', '--no-verify', '-m', 'the garden, before its first bean')
    code, out = run(PY, 'bin/install.py')
    check("the conformance garden is grown, its gate installed", code == 0, out)
    for bid, c in CASES['garden'].items():
        write(f"beans/{bid}.md", doc(bid, dict(c, statements=saved(c['statements']))))
    code, out = run(PY, 'bin/save.py', 'sam', 'the cases\' garden',
                    '--body', '- action: wrote ' + ', '.join(f"[[{b}]]" for b in CASES['garden']))
    check(f"...and the cases' garden ({len(CASES['garden'])} beans) saved through it", code == 0, out[-1500:])

    # ---- THE GOOD CASES: every door takes them (a sealed one asks a store this garden has not: test/core.py's alone)
    good = [c for c in CASES['good'] if not any('held' in r for st in c['statements'] for r in st.values())]
    for c in good:
        write(f"beans/{c['bean']}.md", doc(c['bean'], dict(c, statements=saved(c['statements']))))
    d = doors('the good cases', '- action: wrote ' + ', '.join(f"[[{c['bean']}]]" for c in good))
    check(f"the {len(good)} good cases written as files are saved, and no door refuses them",
          d['save'][0] == 0 and not d['tree'] and not d['judge'] and d['hub'][1].startswith('ACCEPTED')
          and not found_lines(d['propose'][1]), (d['save'][1][-900:], d['tree'][:4]))

    # ---- THE FAULTS OF THE TREE, in as few gardens as their beans' ids allow, each at every door
    left, n = list(CASES['bad']) + list(CASES['disk']), 0
    while left:
        part, ids = [], set()
        for c in left:
            if c['bean'] not in ids:
                part.append(c)
                ids.add(c['bean'])
        left = [c for c in left if c not in part]
        n += 1
        for c in part:
            write(f"beans/{c['bean']}.md", doc(c['bean'], c))
        d = doors(f'faults {n}', '- action: wrote ' + ', '.join(f"[[{c['bean']}]]" for c in part))
        agree(f"{len(part)} faults of the tree (garden {n})", d)
        missed = [f"{c['rule']} {c['bean']}" for c in part if not refused(d, c['rule'], c['bean'], str(c.get('says', '')))]
        check(f"...each refused by its rule, naming its bean ({len(part)})", not missed, missed)

    # ---- THE GARDEN'S OWN FILES: GARDEN.md and VOCAB.md
    manifest = open(os.path.join(G, 'GARDEN.md'), encoding='utf-8').read()
    for name, files, rule, where in (
            ('manifest-key', {'GARDEN.md': manifest.replace('gardener:', 'colour: red\ngardener:', 1)}, 'form', 'GARDEN.md'),
            ('pin-moved', {'GARDEN.md': manifest.replace(f"core@{LAW['version']}", 'core@0.1', 1)}, 'form', 'GARDEN.md'),
            ('no-gardener', {'GARDEN.md': manifest.replace('gardener: sam', 'gardener: nobody', 1)}, 'form', 'GARDEN.md'),
            ('two-layers', {'VOCAB.md': VOCAB.replace('\n---\n', '\nstanding:\n- { layer: history, holds: ["beans/sam.md"] }\n---\n', 1)},
             'layers', 'beans/sam.md'),
            ('unused-row', {'VOCAB.md': VOCAB.replace('kinds:\n', 'kinds:\n- { kind: kiln, nature: body, organisation: device }\n', 1)},
             'vacancy', 'VOCAB.md')):
        for rel, text in files.items():
            write(rel, text)
        d = doors(name, f"- action: RULE-CHANGE, the garden's {', '.join(files)} ({name}); ratified by sam")
        agree(f"the garden's fault {name}", d)
        check(f"...refused by {rule} at {where}", any(r == rule and str(w).startswith(where) for r, w, _m in d['tree']),
              d['tree'][:4])

    # ---- THE FAULTS OF A COMMIT: refused at the commit's doors, passed by the tree's
    j = open(os.path.join(G, 'log', 'journal.md'), encoding='utf-8').read()
    say = {'say': {'by': 'sam', 'at': 'now'}}
    pem = '-----BEGIN ' + 'OPENSSH PRIVATE KEY-----\nb3BlbnNzaA==\n'       # in two parts, so this file never holds one
    renamed = {'kind': 'document', 'statements': [{'say': {'by': 'sam', 'at': '2026-10-01 10:00+03:30'}},
                                                  {'do': {'id': 'job', 'by': 'sam', 'as': 'workstation'}}]}
    WHY = open(os.path.join(G, 'bin', 'why.py'), encoding='utf-8').read()
    DIGESTS = open(os.path.join(G, 'seed', 'LANGUAGE.sha256'), encoding='utf-8').read()
    for name, files, setup, entry, rule, says in (
            ('law-unsaid', {'VOCAB.md': VOCAB.replace('kinds:\n', 'kinds:\n- { kind: kiln, nature: body, organisation: device, vacant: "a case" }\n', 1)},
             None, '- action: VOCAB.md adds the kind kiln', 'ratify', 'RULE-CHANGE'),
            ('future-whereabouts', {'beans/e1.md': doc('e1', {'kind': 'event', 'statements': [
                say, {'be': {'by': 'self', 'at': '2099-06-01 18:00+03:30/2099-06-01 22:00+03:30'}},
                {'be': {'by': 'self', 'at': '192.0.2.40', 'as': 'location'}}, {'attend': {'by': 'ben', 'of': 'self'}}]})},
             None, '- action: [[e1]]', 'consent', 'in the future'),
            ('private-key', {'notes.txt': 'kept here\n' + pem}, None, '- action: a note', 'harm', 'private-key block'),
            ('seal-unsaid', {'beans/h1.md': doc('h1', {'kind': 'document', 'statements': [
                say, {'measure': {'id': 'w', 'held': 'root:vault/0123456789abcdef0123456789abcdef'}}]})},
             None, '- action: [[h1]]', 'harm', '- held: h1 w added'),
            ('journal-rewritten', {'log/journal.md': j.replace('# Journal', '# The Journal', 1)}, None,
             '- action: the title', 'kept', 'never rewritten'),
            ('journal-line-break', {'log/journal.md': j + '- action: a line\x0bwith a vertical tab\n'}, None,
             '- action: written by hand above', 'kept', 'some readers take'),
            ('part-rewritten', {'series/rain/sept/0001.tsv': 'rain\n1\n'}, {'series/rain/sept/0001.tsv': 'rain\n0\n'},
             '- action: the part again', 'kept', "series' part"),
            ('statement-taken', {'beans/k2.md': doc('k2', {'kind': 'document', 'statements': [say, {'do': {'by': 'sam', 'as': 'workstation'}}]})},
             {'beans/k2.md': doc('k2', {'kind': 'document', 'statements': [{'say': {'by': 'sam', 'at': '2026-10-01 10:00+03:30'}},
                                                                            {'do': {'id': 'job', 'by': 'sam', 'as': 'workstation'}}]})},
             '- action: [[k2]] tidied', 'kept', 'the statement `job` is taken out'),
            ('no-body', {'beans/k1.md': doc('k1', {'kind': 'document', 'statements': [say]}, body='')}, None,
             '- action: [[k1]]', 'kept', 'no body'),
            ('renamed-unsaid', {'beans/r1.md': None, 'beans/r2.md': doc('r2', renamed)}, {'beans/r1.md': doc('r1', renamed)},
             '- action: [[r1]] is [[r2]] now', 'knowing', 'is no moment this commit'),
            ('relay-taken-from-origin', {'beans/r3.md': doc('r3', {'kind': 'document', 'statements': [
                {'say': {'by': 'ben', 'at': ['2026-10-01 10:00+03:30', 'garden-a', 'garden-z']}},
                {'take': {'id': 't', 'by': 'sam', 'of': 'self', 'from': 'garden-a', 'through': 'sha256:' + '0' * 64,
                          'at': 'now'}}, {'say': {'by': 'sam', 'of': ['t'], 'at': 'now'}}]})},
             {'beans/garden-z.md': doc('garden-z', {'kind': 'garden', 'statements': [say]})},
             '- action: [[r3]], come from garden-a through garden-z', 'knowing', 'come through garden-z'),
            ('who-no-being', {'beans/w1.md': doc('w1', {'kind': 'document', 'statements': [say]})}, None,
             '- action: [[w1]], and the entry before it by nobody', 'knowing', "names its writer 'nobody'"),
            ('language-patched', {'bin/why.py': WHY + "# a line of this garden's own\n"}, None,
             "- action: RULE-CHANGE, bin/why.py patched here; ratified by sam", 'kept', "differs from the release's own"),
            ('digests-moved', {'seed/LANGUAGE.sha256': DIGESTS.replace(DIGESTS[:64], '0' * 64, 1)}, None,
             "- action: RULE-CHANGE, the digests moved by hand; ratified by sam", 'kept', 'the digests of the release change'),
            ('pass-log-unnamed', {'captures/passes/nobody.jsonl': '{"from": {"layer": "instructions"}, "to": '
                                  '{"bean": "sam", "at": "say"}, "through": "say", "as": "say", '
                                  '"metadata": {"quoted": 1}}\n'}, None,
             '- action: a pass log, claimed by no session', 'layers', 'no session bean names'),
            ('language-deleted', {'bin/why.py': None}, None,
             "- action: RULE-CHANGE, bin/why.py taken out here; ratified by sam", 'kept', 'receives it from its release'),
            ('adoption-unproved', {'bin/why.py': WHY + "# a line of the next release's\n",
                                   'seed/LANGUAGE.sha256': re.sub(r'(?m)^[0-9a-f]{64}(?=  bin/why\.py$)', lambda m: __import__(
                                       'hashlib').sha256((WHY + "# a line of the next release's\n").encode()).hexdigest(),
                                       DIGESTS),
                                   'GARDEN.md': None}, None,
             "- action: RULE-CHANGE, the release v9.9.9 adopted by hand, a file and its digest together; ratified by sam",
             'kept', 'does not name them as the release laid them')):
        if name == 'adoption-unproved':             # GARDEN.md records the release this commit would adopt
            files['GARDEN.md'] = open(os.path.join(G, 'GARDEN.md'), encoding='utf-8').read().replace(
                'gardener:', 'daftar_release: "v9.9.9"\ngardener:', 1)
        if name == 'who-no-being':                  # a heading the clock wrote, its writer no being: a save never writes one
            code, out = run(PY, 'bin/journal.py', 'nobody', 'a note', '--body', '- action: [[w1]] noted')
            check("(the heading by nobody is written by the clock, as bin/journal.py writes any)", code == 0, out)
        if setup:
            for rel, text in setup.items():
                write(rel, text)
            git('add', '-A')
            git('commit', '-q', '--no-verify', '-m', 'the case, before it')
        for rel, text in files.items():
            write(rel, text)
        d = doors(name, entry)
        agree(f"the commit's fault {name}", d, tree_rules=False)
        check(f"...refused by {rule} at the commit: {says}", any(r == rule and says in m for r, _w, m in d['commit']),
              d['commit'][:4])
        if setup:
            git('reset', '-q', '--hard', 'HEAD~1')

    # ---- A BEAN RENAMED, ITS ENTRY SAYING SO (core 3.5, II.1): read as a merge reads a parent, its acts known as they were
    write('beans/r1.md', doc('r1', renamed))
    git('add', '-A')
    git('commit', '-q', '--no-verify', '-m', 'the case, before it')
    write('beans/r1.md', None)
    write('beans/r2.md', doc('r2', renamed))
    code, out = run(PY, 'bin/save.py', 'sam', 'r1 renamed', '--body', '- renamed: [[r1]] → [[r2]]')
    head = git('rev-parse', 'HEAD').stdout.strip()
    sys.path[:0] = [G, os.path.join(G, 'bin')]
    from core import judge as dmjudge
    replayed = dmjudge.judge(None, dmjudge.Scope.replay([head], dict(os.environ, GIT_DIR=os.path.join(G, '.git'))))
    del sys.path[:2]
    check("a bean renamed by a commit whose entry says `- renamed: [[r1]] → [[r2]]` keeps the moments its acts were known "
          "at: saved through the gate, and the hub's replay of the commit refuses nothing", code == 0 and not replayed,
          (out[-900:], replayed))
    git('reset', '-q', '--hard', 'HEAD~2')
finally:
    shutil.rmtree(T, ignore_errors=True)

print("\ncore_conformance: %d failed" % len(FAILS))
sys.exit(1 if FAILS else 0)
