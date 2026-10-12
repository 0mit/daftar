#!/usr/bin/env python3
"""Actions: a ratified action run on daftar's own sequence machinery (bin/act.py) — a walk, a course, its moves.

Grows a garden of the core with the walk every action shares (`plan, show, check, ratify, apply, verify, done`, and the
exits `refused` and `rolled-back`), a tool for it on this machine (a program bean `be`ing here), and a certificate
placed on the walk four times. Then: the engine runs plan, show and check and stops at ratify, a lead to the gardener;
a ratification runs apply and verify to done, the thing changed and read back; a check that fails refuses the run with
its reason and changes nothing; a verify that mismatches rolls back, `restore` run; a plan declined is refused; a plan
that changed since it was shown goes back to show; and someone no grant names may not ratify. Every move is judged by
the gate's rule `line` at its commit, and where each run stands is read by bin/seq.py.

Run: python3 test/act.py   (0 = green)
"""
import json, os, re, shutil, socket, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS = []
HOST = socket.gethostname()


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def write(g, rel, text):
    p = os.path.join(g, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def text(g, rel):
    with open(os.path.join(g, rel), encoding='utf-8') as fh:
        return fh.read()


WALK = '''---
bean: %s
kind: procedure
title: "%s — %s, with its proof"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: %s }
  - step: { id: plan, as: "what would change, changing nothing", by: engine, to: [show] }
  - step: { id: show, as: "the plan, line by line", by: engine, to: [check] }
  - step: { id: check, as: "the tool's own checks", by: engine, to: [ratify] }
  - step: { id: ratify, as: "a person ratifies what they were shown", by: ratifier, to: [apply, show] }
  - step: { id: apply, as: "the plan and nothing else", by: engine, to: [verify] }
  - step: { id: verify, as: "read back from the live thing", by: engine, to: [done] }
  - step: { id: done, as: "deployed and read back", walk: { final: "true" } }
  - step: { id: refused, as: "nothing was changed", walk: { exit: "true", reasons: [cannot-plan, check-failed, declined] } }
  - step: { id: rolled-back, as: "restored and read back", walk: { exit: "true", reasons: [apply-failed, verify-mismatch] } }
---
The walk every one of them takes.
'''

TOOL = r'''import os, sys
step, bean, course = sys.argv[1:4]
live = os.environ.get('LIVE_DIR', '/nonexistent')
target = os.path.join(live, course + '.pem')
want = 'certificate v2 for ' + course
if step == 'plan':
    print('+ ' + target + ': ' + want)
    print('- ' + target + ': ' + (open(target).read().strip() if os.path.exists(target) else '(none)'))
    print('changed plan' if os.path.exists(os.path.join(live, course + '.changed')) else '')
elif step == 'check':
    sys.exit(1 if os.path.exists(os.path.join(live, course + '.check-fails')) else 0)
elif step == 'apply':
    assert os.environ.get('DAFTAR_ACTION_PLAN'), 'apply runs the plan it was given'
    if os.path.exists(target):
        open(target + '.bak', 'w').write(open(target).read())
    open(target, 'w').write(want if not os.path.exists(os.path.join(live, course + '.apply-writes-wrong')) else 'wrong')
elif step == 'verify':
    sys.exit(0 if open(target).read() == want else 1)
elif step == 'restore':
    if os.path.exists(target + '.bak'):
        open(target, 'w').write(open(target + '.bak').read())
    elif os.path.exists(target):
        os.remove(target)
'''

STAMP = r'''import os, socket, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))      # the garden's own bin/: the release's library
import walktool as W
live = os.environ['LIVE_DIR']


def plan(bean, course):
    walk, steps = W.course(bean, course)
    print(f"walk {walk}: steps {','.join(sorted(steps))}; host {W.this_host()}; instances "
          f"{','.join(W.instances('technology:samba'))}; here {W.here(W.this_host() + ':' + live)} and {W.here('far:/x')}; "
          f"by this machine's name {W.here(socket.gethostname() + ':' + live)}")
    print('+ stamp ' + bean)


def check(bean, course):
    if os.path.exists(os.path.join(live, bean + '.refuse')):
        raise W.Refused('a refusal flag is set for ' + course)


def apply(bean, course):
    open(W.shown()).read()
    open(os.path.join(live, bean + '.stamp'), 'w').write('stamped')


def verify(bean, course):
    if not os.path.exists(os.path.join(live, bean + '.stamp')):
        raise W.Refused('no stamp read back')


def restore(bean, course):
    if os.path.exists(os.path.join(live, bean + '.stamp')):
        os.remove(os.path.join(live, bean + '.stamp'))


def note(argv):             # a command of the tool's own: a line added to a bean, saved as the engine saves
    open(os.path.join('beans', argv[0] + '.md'), 'a').write('A note.\n')
    print('saved: ' + W.save('sam', 'a note on ' + argv[0], ['- action: noted [[' + argv[0] + ']]']).strip()[-200:])


def cannot(argv):
    raise W.Refused('nothing here to run with', 2)


sys.exit(W.main('stamp', {'plan': plan, 'check': check, 'apply': apply, 'verify': verify, 'restore': restore},
                more={'note': note, 'cannot': cannot}))
'''

SCRIBE = r'''import json, os, sys
sys.path.insert(0, os.path.join(os.getcwd(), 'bin'))      # the garden's own bin/: the release's library
import walktool as W


def plan(bean, course):           # what the run writes: given by the test, as a page's inputs would be
    with open(os.path.join(os.environ['LIVE_DIR'], bean + '.write.json')) as fh:
        W.plan_writes(json.load(fh))


sys.exit(W.main('scribe', {'plan': plan, 'check': lambda b, c: None, 'apply': W.apply_writes,
                           'verify': W.verify_writes, 'restore': W.restore_writes}))
'''

T = tempfile.mkdtemp(prefix='core-act-')
LIVE = os.path.join(T, 'live')
os.makedirs(LIVE)
os.environ['LIVE_DIR'] = LIVE
grow.ENV['LIVE_DIR'] = LIVE    # what the tool's commands run with: grow copied the environment at its import
try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'tools/cert.py', TOOL)
    write(G, 'VOCAB.md', '---\nkinds:\n  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n'
                         'namespaces:\n  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for itself" }\n'
                         '---\n# the garden\'s own rows\n')
    write(G, 'beans/box.md', f'''---
bean: box
kind: host
title: "box — the machine the actions run on"
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}
---
The machine.
''')
    write(G, 'beans/cert-tool.md', f'''---
bean: cert-tool
kind: program
title: "cert-tool — what deploys a certificate"
statements:
  - make: {{ by: sam, at: now }}
  - be:   {{ by: self, at: "{HOST}:{G}/tools/cert.py", as: location }}
---
The tool.
''')
    write(G, 'mappings/action-cert-deploy.md', WALK % ('action-cert-deploy', 'action-cert-deploy', 'a certificate deployed', 'cert-tool'))
    courses = ('deploy-a', 'deploy-b', 'deploy-c', 'deploy-d', 'deploy-e')
    for c in courses:               # a bean each: a save of a bean waits for the minute its last save is not
        write(G, f'beans/cert-{c}.md', f'---\nbean: cert-{c}\nkind: document\ntitle: "cert-{c} — a certificate"\n'
              f'statements:\n  - say: {{ by: sam, at: now }}\n  - be: {{ id: {c}, by: self, at: action-cert-deploy, as: order }}\n'
              '---\nA certificate.\n')
    r = grow.run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: an action and what it acts on', '--body',
                 '- action: RULE-CHANGE — VOCAB.md adds the kind procedure and the namespace anchor-hostname; wrote '
                 '[[box]], [[cert-tool]], [[action-cert-deploy]], ' + ', '.join(f'[[cert-{c}]]' for c in courses), '- ratified_by: sam', cwd=G)
    check("the garden holds the walk, the tool, the machine and five courses, through its gate", r.returncode == 0,
          r.out[-900:])

    def act(course, *a):
        return grow.run(PY, 'bin/act.py', f'cert-{course}', course, *a, cwd=G)

    def bean(course):
        return text(G, f'beans/cert-{course}.md')

    def at(course):
        return grow.run(PY, 'bin/seq.py', 'course', f'cert-{course}', cwd=G).out

    # ---- a run to done
    r = act('deploy-a')
    stands = at('deploy-a')
    check("act: the engine runs plan, show and check, and stops at ratify — a person's step (bin/seq.py: who acts next)",
          r.returncode == 0 and 'stopped at ratify' in r.out and "at 'ratify'" in stands and 'who acts next: ratifier' in stands
          and not os.path.exists(os.path.join(LIVE, 'deploy-a.pem')), r.out[-600:] + stands[-600:])
    r = act('deploy-a', '--ratify', 'sam')
    live = open(os.path.join(LIVE, 'deploy-a.pem')).read() if os.path.exists(os.path.join(LIVE, 'deploy-a.pem')) else ''
    log = grow.run('git', 'log', '--format=%an %s', '-4', cwd=G).out
    check("act: ratified, the engine applies and verifies to done — the thing changed and read back, each run a commit "
          "through the gate", r.returncode == 0 and 'stopped at done' in r.out and live == 'certificate v2 for deploy-a'
          and 'ratified' in log, r.out[-800:] + log)
    caps = sorted(os.listdir(os.path.join(G, 'captures', 'actions')))
    check("...each step's output kept in history, the plan's SHA-256 on its move",
          any(c.startswith('cert-deploy-a.deploy-a.plan.') for c in caps) and any(c.startswith('cert-deploy-a.deploy-a.verify.') for c in caps)
          and 'sha-256 ' in bean('deploy-a'), caps)

    # ---- a check that fails
    open(os.path.join(LIVE, 'deploy-b.check-fails'), 'w').close()
    r = act('deploy-b')
    check("act: a check that fails refuses the run with its reason, and nothing is changed",
          r.returncode == 0 and 'stopped at refused' in r.out and 'as: check-failed' in bean('deploy-b')
          and not os.path.exists(os.path.join(LIVE, 'deploy-b.pem')), r.out[-600:])

    # ---- a verify that mismatches
    open(os.path.join(LIVE, 'deploy-c.pem'), 'w').write('certificate v1')
    open(os.path.join(LIVE, 'deploy-c.apply-writes-wrong'), 'w').close()
    act('deploy-c')
    r = act('deploy-c', '--ratify', 'sam')
    check("act: a verify that does not read back what was meant rolls back — `restore` run, the old one in place",
          'stopped at rolled-back' in r.out and 'as: verify-mismatch' in bean('deploy-c')
          and open(os.path.join(LIVE, 'deploy-c.pem')).read() == 'certificate v1', r.out[-600:])

    # ---- declined; changed since shown; nobody's to ratify
    act('deploy-d')
    r = act('deploy-d', '--ratify', 'eve')
    check("act: someone no grant names may not ratify", r.returncode != 0 and 'may not ratify' in r.out, r.out[-400:])
    r = act('deploy-d', '--decline', 'sam')
    check("act: a plan declined is refused, nothing changed", r.returncode == 0 and 'as: declined' in bean('deploy-d')
          and not os.path.exists(os.path.join(LIVE, 'deploy-d.pem')), r.out[-600:])
    act('deploy-e')
    open(os.path.join(LIVE, 'deploy-e.changed'), 'w').close()
    r = act('deploy-e', '--ratify', 'sam')
    check("act: a plan that changed since it was shown goes back to show, and waits to be ratified again",
          'changed since it was shown' in r.out and not os.path.exists(os.path.join(LIVE, 'deploy-e.pem')), r.out[-600:])
    stands = {c: at(c) for c in courses}
    check("seq: where each run stands is read by the one reader — done, refused, rolled-back, refused, ratify",
          "at 'done'" in stands['deploy-a'] and "at 'refused'" in stands['deploy-b'] and "at 'rolled-back'" in stands['deploy-c']
          and "at 'refused'" in stands['deploy-d'] and "at 'ratify'" in stands['deploy-e'], stands)
    g = grow.run(PY, 'bin/check.py', cwd=G)
    check("the garden passes its gate after every run", g.returncode == 0 and '0 error(s)' in g.out, g.out[-600:])

    # ---- THE TOOL SIDE, ONCE (bin/walktool.py): a tool written on it names nothing of the garden, and reads its walk,
    #      this host, a position here and the instances on this host as the engine reads them
    write(G, 'tools/stamp.py', STAMP)
    for bid, kind, extra in (('far', 'host', ''), ('samba-box', 'instance', '  - be:   { by: self, at: box, as: habitat }\n'
                                                                            '  - use:  { by: self, of: "technology:samba" }\n'),
                             ('samba-far', 'instance', '  - be:   { by: self, at: far, as: habitat }\n'
                                                       '  - use:  { by: self, of: "technology:samba" }\n'),
                             ('stamp-tool', 'program', f'  - be:   {{ by: self, at: "{HOST}:{G}/tools/stamp.py", as: location }}\n')):
        write(G, f'beans/{bid}.md', f'---\nbean: {bid}\nkind: {kind}\ntitle: "{bid}"\nstatements:\n  - make: {{ by: sam, at: now }}\n'
              f'  - own:  {{ by: sam, of: self }}\n{extra}---\n{bid}.\n')
    write(G, 'mappings/action-stamp.md', WALK % ('action-stamp', 'action-stamp', 'a stamp put', 'stamp-tool'))
    for c in ('stamp-a', 'stamp-b'):
        write(G, f'beans/{c}.md', f'---\nbean: {c}\nkind: document\ntitle: "{c}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
              f'  - be: {{ id: run, by: self, at: action-stamp, as: order }}\n---\nA stamp.\n')
    r = grow.run(PY, 'bin/save.py', 'sam', 'a walk whose tool stands on bin/walktool.py', '--body', '- action: wrote [[far]], '
                 '[[samba-box]], [[samba-far]], [[stamp-tool]], [[action-stamp]], [[stamp-a]] and [[stamp-b]]', cwd=G)
    check("walktool: a second walk, its tool written on bin/walktool.py, two instances of one technology on two hosts",
          r.returncode == 0, r.out[-800:])
    grow.run(PY, 'bin/act.py', 'stamp-a', 'run', cwd=G)
    r = grow.run(PY, 'bin/act.py', 'stamp-a', 'run', '--ratify', 'sam', cwd=G)
    plan = next((text(G, os.path.join('captures', 'actions', c)) for c in sorted(os.listdir(os.path.join(G, 'captures', 'actions')))
                 if c.startswith('stamp-a.run.plan.')), '')
    check("walktool: the tool's course runs to done through bin/act.py; it read its walk and steps (course), this machine's "
          "host bean (this_host), the instances using samba on this host and not the other's (instances), a position here "
          "and one elsewhere (here), and applied only the plan it was shown (shown)",
          'stopped at done' in r.out and 'walk action-stamp: steps apply,check,done,plan,ratify,refused,rolled-back,show,verify'
          in plan and 'host box' in plan and 'instances samba-box;' in plan and 'here ' + LIVE + ' and None' in plan
          and "by this machine's name " + LIVE in plan
          and open(os.path.join(LIVE, 'stamp-a.stamp')).read() == 'stamped', r.out[-800:] + plan)
    open(os.path.join(LIVE, 'stamp-b.refuse'), 'w').close()
    r = grow.run(PY, 'bin/act.py', 'stamp-b', 'run', cwd=G)
    said = ''.join(text(G, os.path.join('captures', 'actions', c)) for c in os.listdir(os.path.join(G, 'captures', 'actions'))
                   if c.startswith('stamp-b.run.check.'))
    check("walktool: a step that raises Refused is the tool's refusal — said as its own word, exit 1, and the engine "
          "refuses the run with it", 'stopped at refused' in r.out and 'stamp: a refusal flag is set for run' in said
          and 'as: check-failed' in text(G, 'beans/stamp-b.md'), r.out[-800:] + said)
    r = grow.run(PY, 'tools/stamp.py', 'nonsense', cwd=G)
    check("walktool: anything else is the usage, exit 2", r.returncode == 2 and 'usage: stamp {plan|check|apply|verify|restore} '
          '<bean> <course> | note … | cannot …' in r.out, r.out[-300:])
    r = grow.run(PY, 'tools/stamp.py', 'apply', 'stamp-b', 'run', cwd=G, env=dict(grow.ENV, DAFTAR_ACTION_PLAN=''))
    check("walktool: apply given no plan to run is refused (shown), exit 1, and changes nothing",
          r.returncode == 1 and 'stamp: apply runs the plan it was shown' in r.out
          and not os.path.exists(os.path.join(LIVE, 'stamp-b.stamp')), r.out[-300:])
    head = grow.run('git', 'rev-parse', 'HEAD', cwd=G).out.strip()
    r = grow.run(PY, 'tools/stamp.py', 'note', 'stamp-a', cwd=G)
    log = grow.run('git', 'log', '-1', '--format=%s', cwd=G).out.strip()
    check("walktool: a command of the tool's own (more) saves as the engine saves (save): one commit, the gate passed, "
          "what save said given back", r.returncode == 0 and 'saved: ' in r.out and log == 'a note on stamp-a'
          and grow.run('git', 'rev-parse', 'HEAD~1', cwd=G).out.strip() == head, r.out[-400:] + log)
    head = grow.run('git', 'rev-parse', 'HEAD', cwd=G).out.strip()
    _sa = text(G, 'beans/stamp-a.md')
    write(G, 'beans/stamp-a.md', _sa.replace('kind: document', 'kind: no-such-kind', 1))
    r = grow.run(PY, 'tools/stamp.py', 'note', 'stamp-a', cwd=G)
    check("walktool: a save the gate refuses is the tool's refusal, said with what the gate said, exit 1, nothing committed",
          r.returncode == 1 and 'stamp: the save was refused:' in r.out
          and grow.run('git', 'rev-parse', 'HEAD', cwd=G).out.strip() == head, r.out[-400:])
    grow.run('git', 'reset', '-q', '--hard', 'HEAD', cwd=G)     # a refused save leaves its entry and files staged
    r = grow.run(PY, 'tools/stamp.py', 'cannot', cwd=G)
    check("walktool: a tool that could not run says so, exit 2 (Refused(why, 2))",
          r.returncode == 2 and 'stamp: nothing here to run with' in r.out, r.out[-300:])

    # ---- A PLAN THAT IS A WRITE (walktool's plan_writes, apply_writes, verify_writes, restore_writes): the tool says
    #      what it would write, and the rest is the release's — written as shown, known by who ratified it, one save
    write(G, 'tools/scribe.py', SCRIBE)
    write(G, 'beans/scribe-tool.md', f'---\nbean: scribe-tool\nkind: program\ntitle: "scribe-tool"\nstatements:\n'
          f'  - make: {{ by: sam, at: now }}\n  - be:   {{ by: self, at: "{HOST}:{G}/tools/scribe.py", as: location }}\n'
          '---\nWhat writes a plan.\n')
    write(G, 'mappings/action-scribe.md', WALK % ('action-scribe', 'action-scribe', 'a write made', 'scribe-tool'))
    write(G, 'beans/kitty.md', '---\nbean: kitty\nkind: contract\ntitle: "kitty — what Sam keeps for the house"\n'
          'statements:\n  - say:   { by: sam, at: now }\n  - own:   { by: sam, of: self }\n'
          '  - pay:   { id: p0, by: sam, of: { count: "3", unit: EUR }, note: "a mistake" }\n'
          '  - say:   { by: sam, of: [p0], at: now }\n'
          '  - pay:   { id: p3, by: sam, of: { count: "4", unit: EUR } }\n'
          '  - pay:   { id: p4, by: sam, of: { count: "6", unit: EUR } }\n'
          '  - say:   { by: sam, of: [p3, p4], at: now }\n---\nThe kitty.\n')
    for c in ('scribe-a', 'scribe-b', 'scribe-c'):
        write(G, f'beans/{c}.md', f'---\nbean: {c}\nkind: document\ntitle: "{c}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
              f'  - be: {{ id: run, by: self, at: action-scribe, as: order }}\n---\nA run.\n')
    r = grow.run(PY, 'bin/save.py', 'sam', 'a walk whose plan is a write', '--body', '- action: wrote [[scribe-tool]], '
                 '[[action-scribe]], [[kitty]], [[scribe-a]], [[scribe-b]] and [[scribe-c]]', cwd=G)
    check("write: a third walk, whose tool says only what it would write", r.returncode == 0, r.out[-800:])
    W1 = {'what': 'the kitty, put right', 'body': ['- action: the kitty put right'], 'beans': [
        {'bean': 'kitty', 'remove': ['p0'], 'add': ['pay: { id: p1, by: sam, of: { count: "5", unit: EUR }, note: "the bread" }']},
        {'bean': 'receipt-1', 'new': {'head': 'bean: receipt-1\nkind: document\ntitle: "receipt-1 — the bread\'s receipt"',
                                     'body': 'The receipt.'}, 'add': ['own: { id: o1, by: sam, of: self }'],
         'known': {'act': 'read', 'from': 'kitty', 'through': 'the paper slip'}}]}
    open(os.path.join(LIVE, 'scribe-a.write.json'), 'w').write(json.dumps(W1))
    grow.run(PY, 'bin/act.py', 'scribe-a', 'run', cwd=G)
    shown_plan = next((text(G, os.path.join('captures', 'actions', c)) for c in
                       sorted(os.listdir(os.path.join(G, 'captures', 'actions'))) if c.startswith('scribe-a.run.plan.')), '')
    before = grow.run('git', 'rev-parse', 'HEAD', cwd=G).out.strip()
    r = grow.run(PY, 'bin/act.py', 'scribe-a', 'run', '--ratify', 'sam', cwd=G)
    kitty = text(G, 'beans/kitty.md')
    log = grow.run('git', 'log', '--format=%s', f'{before}..HEAD', cwd=G).out.split('\n')
    entry = grow.run('git', 'show', 'HEAD~1', '--', 'log/journal.md', cwd=G).out
    check("write: the plan shown is the write, in words and as data, byte for byte what the person ratifies",
          '  - kitty: pay#p0' in shown_plan and '  + kitty: pay: { id: p1,' in shown_plan
          and '  + the bean receipt-1, made' in shown_plan and '-- the write, as data --' in shown_plan, shown_plan)
    check("write: ratified, the release writes exactly the plan shown — one save of the write, known by who ratified it "
          "(a `read` from its source where the plan says so), its entry naming each bean and what it took out — and the "
          "engine's own save of the run after it",
          'stopped at done' in r.out and 'id: p1' in kitty and 'id: p0' not in kitty and 'a mistake' not in kitty
          and re.search(r'- say: \{ by: sam, of: \[p1\], at: "?\d{4}-', kitty) is not None
          and re.search(r'- read: \{ by: sam, of: \[o1\], from: kitty, through: "the paper slip", at:', text(G, 'beans/receipt-1.md'))
          is not None and log[1:2] == ['the kitty, put right'] and 'scribe-a run: ratified' in log[0]
          and '[[kitty]] p0, and the say that knew only them' in entry and '[[receipt-1]]' in entry,
          r.out[-800:] + str(log) + entry[-1200:])
    check("...and the run's ratification is the engine's to save: the write's commit leaves the course's bean as it was",
          grow.run('git', 'diff', '--name-only', 'HEAD~2', 'HEAD~1', cwd=G).out.split() == ['beans/kitty.md', 'beans/receipt-1.md',
                                                                                             'log/journal.md']
          or 'beans/scribe-a.md' not in grow.run('git', 'diff', '--name-only', 'HEAD~2', 'HEAD~1', cwd=G).out,
          grow.run('git', 'diff', '--name-only', 'HEAD~2', 'HEAD~1', cwd=G).out)
    plan_a = sorted(c for c in os.listdir(os.path.join(G, 'captures', 'actions')) if c.startswith('scribe-a.run.plan.'))[-1]
    r = grow.run(PY, 'tools/scribe.py', 'restore', 'scribe-a', 'run', cwd=G,
                 env=dict(grow.ENV, DAFTAR_ACTION_PLAN=os.path.join(G, 'captures', 'actions', plan_a)))
    check("write: restore takes out what the plan added, in a save of its own — and says that what it took out is in git, "
          "for a person to restate (exit 1)",
          r.returncode == 1 and 'restored in part' in r.out and 'id: p1' not in text(G, 'beans/kitty.md')
          and not os.path.exists(os.path.join(G, 'beans', 'receipt-1.md')) and 'id: p0' not in text(G, 'beans/kitty.md')
          and grow.run(PY, 'bin/check.py', cwd=G).returncode == 0, r.out[-800:])
    W2 = {'what': 'a write the gate refuses', 'beans': [{'bean': 'kitty', 'add': ['frobnicate: { id: f1, of: self }']}]}
    open(os.path.join(LIVE, 'scribe-b.write.json'), 'w').write(json.dumps(W2))
    grow.run(PY, 'bin/act.py', 'scribe-b', 'run', cwd=G)
    k_before = text(G, 'beans/kitty.md')
    r = grow.run(PY, 'bin/act.py', 'scribe-b', 'run', '--ratify', 'sam', cwd=G)
    caps = ''.join(text(G, os.path.join('captures', 'actions', c)) for c in os.listdir(os.path.join(G, 'captures', 'actions'))
                   if c.startswith('scribe-b.run.apply.'))
    check("write: a write the gate refuses puts back every file it touched and unstages all: the run rolls back "
          "(apply-failed), what the gate said in the apply's capture, nothing of it kept",
          'stopped at rolled-back' in r.out and 'as: apply-failed' in text(G, 'beans/scribe-b.md')
          and text(G, 'beans/kitty.md') == k_before and 'frobnicate' not in text(G, 'beans/kitty.md')
          and 'nothing written' in caps and grow.run('git', 'status', '--porcelain', cwd=G).out.strip() == ''
          and grow.run(PY, 'bin/check.py', cwd=G).returncode == 0, r.out[-800:] + caps[-800:])
    W3 = {'what': 'half of what one act knows', 'beans': [{'bean': 'kitty', 'remove': ['p3']}]}
    open(os.path.join(LIVE, 'scribe-c.write.json'), 'w').write(json.dumps(W3))
    r = grow.run(PY, 'bin/act.py', 'scribe-c', 'run', cwd=G)
    caps = ''.join(text(G, os.path.join('captures', 'actions', c)) for c in os.listdir(os.path.join(G, 'captures', 'actions'))
                   if c.startswith('scribe-c.run.plan.'))
    check("write: a plan that would take out part of what one knowing act knows is refused at the plan — a knowing act "
          "is never rewritten — and nothing is changed",
          'stopped at refused' in r.out and 'as: cannot-plan' in text(G, 'beans/scribe-c.md')
          and 'knows p3, taken out, and p4, kept' in caps and 'id: p3' in text(G, 'beans/kitty.md'), r.out[-600:] + caps[-600:])
    W4 = {'what': 'a source that is no being', 'beans': [{'bean': 'kitty', 'add': ['pay: { id: p9, by: sam, of: { count: "1", unit: EUR } }'],
                                                         'known': {'act': 'read', 'from': 'kitty, by: eve'}}]}
    open(os.path.join(LIVE, 'scribe-c.write.json'), 'w').write(json.dumps(W4))
    r = grow.run(PY, 'tools/scribe.py', 'plan', 'scribe-c', 'run', cwd=G)
    check("write: a plan whose additions would be known otherwise than by `say`, or by `read` from a being named by its "
          "id, is refused at the plan", r.returncode == 1 and 'known by `say`, or by `read` from a being' in r.out, r.out[-400:])
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nact: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
