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
import json, os, shutil, socket, sys, tempfile

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
    write(G, 'mappings/action-cert-deploy.md', '''---
bean: action-cert-deploy
kind: procedure
title: "action-cert-deploy — a certificate deployed, with its proof"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: cert-tool }
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
The walk every certificate's deployment takes.
''')
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
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nact: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
