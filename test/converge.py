#!/usr/bin/env python3
"""converge — several gardens diverge, are packaged, and one remote garden pulls them all back.

WHY THIS EXISTS. Every other suite tests one garden. This is the only one that exercises what the whole
MERGE design is FOR: independent sessions recording the same estate, offline, converging later. Run as a
one-off rehearsal it found four real defects in an afternoon, every one invisible to the other suites:

  * `seed/germinate.sh` never copied `.gitattributes`, so EVERY germinated garden text-merged its beans
    and conflicted on its own append-only journal. The driver was configured in each and invoked in none.
    Git warns neither when an attribute names a missing driver nor when a configured driver is named by
    nothing, so this was silent in both directions.
  * The driver emitted YAML block sequences at the SAME column as their key — legal YAML that defeats
    every indentation-based span finder, so the next edit landed inside the block and the file stopped
    parsing.
  * When a member had to be appended, the anchor member was re-emitted from OUR value rather than the
    merged one, quietly undoing a merge that had just happened.
  * A position where theirs differs but the MERGED RESULT equals ours was still written, handing dmsafe a
    block identical to the text it replaced.

Nothing here is mocked: real germination, real clones, real `git bundle`, real `git merge` through the
driver `.gitattributes` names. Roughly 15 seconds.

Run: python3 test/converge.py   (0 = green)
"""
import os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import dmparse
import yaml

results = []


def check(name, ok, detail=''):
    results.append(ok)
    print(("PASS " if ok else "*** FAIL *** ") + name + (f"  [{detail}]" if detail and not ok else ''))


def git(*a, cwd):
    return subprocess.run(('git',) + a, capture_output=True, text=True, cwd=cwd)


def commit(cwd, who, msg):
    with open(os.path.join(cwd, 'log', 'journal.md'), 'a', encoding='utf-8') as fh:
        fh.write(f"\n## 2026-08-02 · agent · {who}\n- action: {msg}\n- refs: beans/relay.md\n")
    git('add', '-A', cwd=cwd)
    return git('-c', 'user.name=' + who, '-c', f'user.email={who}@g', 'commit', '-q', '-m', msg, cwd=cwd)


def edit(cwd, fn):
    p = os.path.join(cwd, 'beans', 'relay.md')
    text = open(p, encoding='utf-8').read()          # READ then write; 'w' truncates at call time
    open(p, 'w', encoding='utf-8').write(fn(text))


RELAY = """---
bean: relay
kind: host
title: "relay — the shared mail relay every garden observes"
status: active
summary: "A relay recorded in the origin garden, so gardens cloned from it observe the same object independently and their records must converge on one being rather than three."
identity:
  status: confirmed
  anchors:
    - {{ key: serial, value: "SN-RELAY-001", class: hardware, establishing: true, scope: global, observed: 2026-08-02, authority: operator-asserted }}
provenance: {{ src: observed, by: "agent/origin", as_of: 2026-08-02 }}
nature: physical
owns:
  os: "AlmaLinux 9"
  roles: [relay]
  contact: "noc@example.org"          # NOBODY edits this — it and its comment must survive untouched
---
The shared relay.
"""

TMP = tempfile.mkdtemp(prefix='dmconv-')
ORIGIN = os.path.join(TMP, 'origin')

r = subprocess.run(['sh', os.path.join(ROOT, 'seed', 'germinate.sh'), ORIGIN],
                   capture_output=True, text=True, cwd=ROOT)
check("an origin garden germinates from the seed", r.returncode == 0, (r.stdout + r.stderr)[-300:])
check("...and it dispatches bean merges to the semantic driver, journal merges to union",
      'daftar' in git('check-attr', 'merge', '--', 'beans/x.md', cwd=ORIGIN).stdout
      and 'union' in git('check-attr', 'merge', '--', 'log/journal.md', cwd=ORIGIN).stdout,
      "`.gitattributes` did not travel — every garden would text-merge its beans")

open(os.path.join(ORIGIN, 'beans', 'relay.md'), 'w', encoding='utf-8').write(RELAY.format())
commit(ORIGIN, 'origin', 'recorded the relay every garden observes')
BASE = git('rev-parse', 'HEAD', cwd=ORIGIN).stdout.strip()

GARDENS = ('site-a', 'site-b', 'site-c')
for g in GARDENS:
    git('clone', '-q', ORIGIN, os.path.join(TMP, g), cwd=TMP)
    subprocess.run(['sh', 'bin/install.sh'], capture_output=True, cwd=os.path.join(TMP, g))

# Three independent migrations. NO VERSION MOVES — the pin stays put, which is also what keeps them
# mergeable at all: a merge across two Tier-0 versions is refused by design.
edit(os.path.join(TMP, 'site-a'), lambda t: t.replace('  os: "AlmaLinux 9"', '  os: "AlmaLinux 9.4"')
     .replace('roles: [relay]', 'roles: [relay, submission]'))
commit(os.path.join(TMP, 'site-a'), 'site-a', 'refined os to 9.4 and added the submission role')

edit(os.path.join(TMP, 'site-b'),
     lambda t: t.replace('roles: [relay]', 'roles: [relay, dkim-signing]\n  site: "Site B DC"'))
commit(os.path.join(TMP, 'site-b'), 'site-b', 'added dkim-signing and site Site B DC')

edit(os.path.join(TMP, 'site-c'), lambda t: t.replace('roles: [relay]', 'roles: [relay]\n  site: "Site C DC"')
     .replace('nature: physical', 'nature: physical\ncapabilities:\n  open-relay: { permission: forbidden,'
                                  ' feasibility: possible, why: "must never accept third-party mail" }'))
commit(os.path.join(TMP, 'site-c'), 'site-c', 'recorded site Site C DC and forbade open-relay')

gates = {g: subprocess.run([sys.executable, 'bin/dmcheck.py'], capture_output=True, text=True,
                           cwd=os.path.join(TMP, g)) for g in GARDENS}
check("each garden passes its OWN gate after its own migration",
      all(r.returncode == 0 for r in gates.values()),
      '; '.join(f"{g}: {r.stdout.strip()[-90:]}" for g, r in gates.items() if r.returncode))

# ---- PACKAGE: a git bundle per garden. Git's own offline transport — one file, no server. -------------
PKG = os.path.join(TMP, 'package')
os.makedirs(PKG)
for g in GARDENS:
    git('bundle', 'create', '-q', os.path.join(PKG, g + '.bundle'), f'{BASE}..HEAD', cwd=os.path.join(TMP, g))
_v = yaml.safe_load(dmparse.read(os.path.join(ORIGIN, 'VOCAB.md'))[0])
check("the package is one self-verifying bundle per garden",
      all(os.path.exists(os.path.join(PKG, g + '.bundle')) for g in GARDENS)
      and all('is okay' in git('bundle', 'verify', os.path.join(PKG, g + '.bundle'), cwd=ORIGIN).stdout
              or git('bundle', 'verify', os.path.join(PKG, g + '.bundle'), cwd=ORIGIN).returncode == 0
              for g in GARDENS))

# ---- PULL BACK: one last remote garden takes all three ------------------------------------------------
REMOTE = os.path.join(TMP, 'remote')
git('clone', '-q', ORIGIN, REMOTE, cwd=TMP)
subprocess.run(['sh', 'bin/install.sh'], capture_output=True, cwd=REMOTE)
drove = []
for g in GARDENS:
    git('fetch', '-q', os.path.join(PKG, g + '.bundle'), f'HEAD:refs/heads/from-{g}', cwd=REMOTE)
    m = git('-c', 'user.name=remote', '-c', 'user.email=r@r', 'merge', f'from-{g}',
            '-m', f'pull back {g}', cwd=REMOTE)
    drove.append((g, m.returncode, m.stdout + m.stderr))

check("every garden PULLS BACK cleanly — no git-level conflict anywhere",
      all(rc == 0 for _g, rc, _o in drove),
      '; '.join(f"{g}: {o.strip()[:150]}" for g, rc, o in drove if rc))
check("...and the semantic driver, not git's text merge, did the work",
      sum('dmmerge:' in o for _g, _rc, o in drove) >= 2,
      '; '.join(o.strip()[:120] for _g, _rc, o in drove))

head, _body = dmparse.read(os.path.join(REMOTE, 'beans', 'relay.md'))
fm = yaml.safe_load(head)
owns = fm['owns']
check("a REFINEMENT subsumes: origin's 'AlmaLinux 9' and site-a's '9.4' resolve to 9.4, not a conflict",
      owns['os'] == 'AlmaLinux 9.4', str(owns['os']))
check("a SET unions across all three gardens",
      sorted(owns['roles']) == ['dkim-signing', 'relay', 'submission'], str(owns['roles']))
check("a genuine DISAGREEMENT keeps both values rather than picking one",
      isinstance(owns.get('site'), dict) and sorted(owns['site']['conflict']) == ['Site B DC', 'Site C DC'],
      str(owns.get('site')))
check("...and the bean is marked unclean, naming the path a human must settle",
      # `status` is deliberately NOT the marker (Phase 5, D22): it is a `single` merged term, so the
      # driver writing its own flag there collided with the algebra on one key. It must survive the merge
      # carrying what the gardens actually said.
      fm.get('merge_open') is True and fm['merge_conflicts'] == ['owns.site']
      and fm.get('status') != 'at-risk',
      f"status={fm.get('status')} conflicts={fm.get('merge_conflicts')}")
check("a top-level key only ONE garden had arrives whole",
      list((fm.get('capabilities') or {})) == ['open-relay'], str(list(fm.get('capabilities') or {})))
check("a fact NOBODY edited is untouched, comment and all",
      owns['contact'] == 'noc@example.org' and 'NOBODY edits this' in head)

jr = open(os.path.join(REMOTE, 'log', 'journal.md'), encoding='utf-8').read()
check("every garden's journal entry survives — the log merges by union, losing none",
      all(g in jr for g in GARDENS) and 'origin' in jr)

g = subprocess.run([sys.executable, 'bin/dmcheck.py'], capture_output=True, text=True, cwd=REMOTE)
check("the converged garden passes its gate", g.returncode == 0, g.stdout.strip()[-200:])
check("...and the gate WARNS about the unresolved conflict rather than staying silent (MERGE.md §10)",
      'left UNCLEAN by a semantic merge' in g.stdout, g.stdout.strip()[-200:])

shutil.rmtree(TMP, ignore_errors=True)
print(f"\nconverge: {sum(results)}/{len(results)} checks passed")
sys.exit(0 if all(results) else 1)
