#!/usr/bin/env python3
"""A statement taken out through the view's one write path (assets/view/lib/view_write.py), and the knowing acts that
named it: an act whose `of` names only what the write takes out goes with it, and the entry names it — left, it would
name what is not there, and emptied of its `of` it would cover every statement no other act names; an act that knows a
statement that stays too, or any other statement that names one taken out, refuses the write before anything is
written.

A garden of the core is grown here (test/grow.py) taking the view profile: Sam keeps it, and a plan of a site holds a
point made with it, known by a `say` with no `of`; points added through the write path one at a time and two together,
each write known by a `say` of what it added; a point read by Sam, its `read` known by a `say` of its own; a point
known as `<bean>#<id>`; and a point another statement names. Then, each write through the one write path and the gate:

  alone         a point added on its own is taken out, and the `say` that knew only it goes with it, the entry naming it
  together      one of the two points said together is refused, naming the other and the act, and nothing is written;
                both taken out in one write, their `say` goes
  in turn       a point whose `read` a `say` knows: the point taken out, the `read` goes, and the `say` of it in turn
  by its bean   a point a `say` names as `<bean>#<id>`, beside the `say` of its id: taken out, both go
  named         a point another statement names in its `of` is refused, naming that statement; taken out with it, it goes
  no `of`       the point made with the plan is taken out and the `say` with no `of` stays: it covers what no act names

Run: python3 test/view_unsay.py   (0 = green)
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS, TRACES = [], []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    r = subprocess.run(list(a), capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=grow.ENV)
    out = r.stdout + r.stderr
    if 'Traceback' in out:
        TRACES.append(out[-1200:])
    return r.returncode, out


def put(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def text():
    with open(os.path.join(G, 'beans', 'plan.md'), encoding='utf-8') as fh:
        return fh.read()


def acts():
    """The plan's statements, as (verb, roles)."""
    import yaml
    head = text().split('\n---\n', 1)[0]
    return [next(iter(st.items())) for st in yaml.safe_load(head.lstrip('-\n')).get('statements') or []]


def write(ops):
    """The one write path, as a served page's Save calls it, for Sam; and the entry it saved, where it saved one."""
    rc, out = run(PY, '-c', "import json, os, sys; sys.path[:0] = [os.path.join('.', 'assets', 'view', 'lib'), 'bin']; "
                  "import view_write; print(json.dumps(view_write.write('.', 'sam', 'plan', %r), default=str))" % (ops,))
    try:
        res = json.loads(out.strip().splitlines()[-1])
    except (ValueError, IndexError):
        res = {'ok': False, 'output': out[-1500:]}
    with open(os.path.join(G, 'log', 'journal.md'), encoding='utf-8') as fh:
        res['entry'] = fh.read().rstrip().rsplit('\n## ', 1)[-1] if res.get('ok') else ''
    return res


def point(p):
    return {'op': 'add', 'verb': 'be', 'id': p, 'roles': {'by': 'self', 'at': 'site', 'as': 'place'}}


def out(*keys):
    return [{'op': 'remove', 'key': k} for k in keys]


def says_of():
    return [r.get('of') for v, r in acts() if v == 'say']


def clean():
    return run('git', 'status', '--porcelain')[1].strip() == ''


T = tempfile.mkdtemp(prefix='view-unsay-')
REL, G = os.path.join(T, 'release'), os.path.join(T, 'garden-sam')

try:
    grow.release(REL)
    rc, o = run(PY, os.path.join(REL, 'seed', 'germinate.py'), G, '--gardener', 'sam', '--gardener-name', 'Sam',
                '--profile', 'view', cwd=T)
    check("a garden of the core grows taking the view profile, kept by Sam", rc == 0, o[-800:])
    run(PY, 'bin/install.py')
    put('beans/site.md', '''---
bean: site
kind: site
title: "A site"
statements:
  - say: { by: sam, at: now }
  - own: { by: sam, of: self }
---
A site.
''')
    put('beans/plan.md', '''---
bean: plan
kind: design
title: "A plan of the site"
statements:
  - say: { by: sam, at: now }
  - be:  { id: p-1, by: self, at: site, as: place }
---
A plan.
''')
    rc, o = run(PY, 'bin/save.py', 'sam', 'a site and a plan of it', '--body', '- action: wrote [[site]] and [[plan]]')
    check("the site and its plan are saved through the core's gate", rc == 0 and '0 error(s)' in o, o[-1500:])
    r2, r34 = write([point('p-2')]), write([point('p-3'), point('p-4')])
    check("a point added on its own, and two together, each known by a `say` of what the write added",
          r2.get('ok') and r34.get('ok') and says_of() == [None, ['p-2'], ['p-3', 'p-4']], (r2, r34, acts()))
    with open(os.path.join(G, 'beans', 'plan.md'), encoding='utf-8') as fh:
        t = fh.read()
    put('beans/plan.md', t.replace('\n---\nA plan.', '''
  - be:   { id: p-5, by: self, at: site, as: place }
  - read: { id: seen, by: sam, of: [p-5], from: site, at: now }
  - say:  { by: sam, of: [seen], at: now }
  - be:   { id: p-6, by: self, at: site, as: place }
  - say:  { by: sam, of: [p-6], at: now }
  - say:  { by: sam, of: [plan#p-6], at: now }
  - be:   { id: p-7, by: self, at: site, as: place }
  - say:  { by: sam, of: [p-7], at: now }
  - contingent: { id: may-fail, of: p-7 }
  - say:  { by: sam, of: [may-fail], at: now }
---
A plan.''', 1))
    rc, o = run(PY, 'bin/save.py', 'sam', 'points read, named by their bean, and named by another statement', '--body',
                '- action: [[plan]] given p-5, read; p-6, said also as plan#p-6; and p-7, which `contingent#may-fail` names')
    check("...a point read, one said as `<bean>#<id>`, and one another statement names, saved through the gate",
          rc == 0 and '0 error(s)' in o, o[-1500:])

    # ALONE: the `say` that knew only the point goes with it, and the entry names it
    res = write(out('be#p-2'))
    check("a point added on its own is taken out through the gate, and the `say` that knew only it goes with it",
          res.get('ok') is True and ['p-2'] not in says_of() and 'p-2' not in text(), res)
    check("...the entry names the point and the `say` taken out",
          'removed `be#p-2`' in res['entry'] and 'took out the `say` by sam' in res['entry']
          and 'which knew only `be#p-2`' in res['entry'], res['entry'])

    # TOGETHER: one of two said together is refused, before anything is written; the two in one write go with their say
    before = text()
    res = write(out('be#p-3'))
    why = next((x for x in res.get('refusals') or [] if x.get('fact') == 'be#p-3'), {})
    check("one of two points said together is refused at the op that takes it out, naming the other and the act",
          res.get('ok') is False and why.get('op') == 0 and '`be#p-4`' in why.get('message', '')
          and "sam's `say`" in why.get('message', ''), res)
    check("...and nothing is written: the plan as it was, the garden clean", text() == before and clean(), text())
    res = write(out('be#p-3', 'be#p-4'))
    check("both taken out in one write go through the gate, and the `say` of the two goes with them",
          res.get('ok') is True and ['p-3', 'p-4'] not in says_of() and 'which knew only `be#p-3`, `be#p-4`' in res['entry'],
          res)

    # IN TURN: the `read` that knew only the point goes, and the `say` that knew only the `read`
    res = write(out('be#p-5'))
    check("a point taken out takes its `read`, and the `say` of that `read` in turn",
          res.get('ok') is True and not any(v == 'read' for v, _r in acts()) and ['seen'] not in says_of()
          and 'took out the `read` by sam' in res['entry'] and 'which knew only `read#seen`' in res['entry'], res)

    # BY ITS BEAN: a `say` that names the point as `<bean>#<id>`
    res = write(out('be#p-6'))
    check("a point a `say` names as `<bean>#<id>` is taken out, and that `say` goes, as does the one that names its id",
          res.get('ok') is True and ['plan#p-6'] not in says_of() and ['p-6'] not in says_of(), res)

    # NAMED: another statement names the point; refused, and taken out with it, both go
    before = text()
    res = write(out('be#p-7'))
    why = next((x for x in res.get('refusals') or [] if x.get('fact') == 'be#p-7'), {})
    check("a point another statement names in its `of` is refused, naming it, and nothing is written",
          res.get('ok') is False and '`contingent#may-fail`' in why.get('message', '') and text() == before and clean(), res)
    res = write(out('be#p-7', 'contingent#may-fail'))
    check("...taken out with that statement, both go, and each `say` that knew only one of them",
          res.get('ok') is True and 'p-7' not in text() and 'may-fail' not in text() and says_of() == [None], res)

    # NO `OF`: the act that covers what no other act names stays
    res = write(out('be#p-1'))
    check("the point made with the plan is taken out, and the `say` with no `of` stays",
          res.get('ok') is True and acts() == [('say', acts()[0][1])] and 'of' not in acts()[0][1]
          and 'took out' not in res['entry'], (res, acts()))
    rc, o = run(PY, 'bin/check.py')
    check("the garden passes its gate after every write", rc == 0 and '0 error(s)' in o, o[-1500:])
finally:
    if TRACES:
        print("TRACEBACKS:\n" + "\n---\n".join(TRACES[:3]))
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_unsay: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS or TRACES else 0)
