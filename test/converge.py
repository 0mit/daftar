#!/usr/bin/env python3
"""converge — several clones of a garden of the core diverge offline, are packaged, and one remote pulls them all back
(v1 part 12: today's suite, ported to the core and its statement merge).

WHY THIS EXISTS. Every other suite tests one garden, or one merge of two branches (test/core_merge.py). This is the one
that exercises what the merge is FOR: independent sessions recording the same estate, offline, converging later. As
today's version of it found, a defect here is invisible elsewhere: a merge driver configured in no clone, a journal
that conflicts on its own appends, a bean that only one side wrote lost on the way back.

Nothing is mocked: a garden of the core grown from a release made of this tree, real clones, real `git bundle`, real
`git merge` through the statement merge (bin/merge.py, git's driver `daftar`) and the core's gate at every commit.

  + an origin garden keeps a relay (a host bean, a comment above one of its statements); three clones of it each record
    something of the relay, committed through their own gate: site-a one mass, site-b another (a disagreement), and a
    role; site-c a role and a bean of its own
  + each is packaged as one self-verifying bundle, and a remote clone of the origin pulls the three back: no git-level
    conflict anywhere, the statement merge doing the work, each merge committed through the core's gate with an entry
    of its own
  + the relay holds the union of what every garden said; the two masses both stand, side by side, each known by its
    garden's act; the bean only site-c wrote arrives whole; the statement nobody edited is untouched, its comment with
    it; every garden's journal entry survives, the journal merged by union
  + the converged garden passes the core's gate whole — and a second remote that pulls the three back in the other
    order holds the same statements

What today's suite held of its semantic merge — a refinement that subsumes, a rank of provenance, readings of a day that
nest, one serial spelt two ways — the statement merge does not do: a bean's statements are a set, and a disagreement is
two statements side by side (daftar-v1-plan.md, the fourth fork; test/ported.yaml says where each promise went).

Run: python3 test/converge.py   (0 = green)
"""
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1200]))
    if not cond:
        FAILS.append(name)


def text(g, rel):
    with open(os.path.join(g, rel), encoding='utf-8') as fh:
        return fh.read()


def write(g, rel, t):
    os.makedirs(os.path.dirname(os.path.join(g, rel)), exist_ok=True)
    with open(os.path.join(g, rel), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def commit(g, what, body):
    """A save without the wait for the minute: the clock's heading written by bin/journal.py, its moment in place of each
    `at: now`, and one commit, through the hook (the core's gate)."""
    grow.run(PY, 'bin/journal.py', 'sam', what, '--body', body, cwd=g)
    m = [ln for ln in text(g, 'log/journal.md').split('\n') if ln.startswith('## ')][-1][3:].split(' · ', 1)[0]
    for f in os.listdir(os.path.join(g, 'beans')):
        t = text(g, f'beans/{f}')
        if 'at: now' in t:
            write(g, f'beans/{f}', t.replace('at: now', f'at: "{m}"'))
    grow.run('git', 'add', '-A', cwd=g)
    return grow.run('git', 'commit', '-q', '-m', what, cwd=g)


def add(g, rel, *lines):
    """Statements put at the end of a bean's list, one to a line."""
    t = text(g, rel)
    head, sep, body = t.partition('\n---\n')
    write(g, rel, head + ''.join(f'\n  - {ln}' for ln in lines) + sep + body)


def statements(g, rel):
    return sorted(ln.strip() for ln in text(g, rel).split('\n---\n', 1)[0].split('\n') if ln.startswith('  - '))


RELAY = """---
bean: relay
kind: host
title: "relay — the mail relay"
summary: "A relay recorded in the origin garden, so its clones observe one being and converge on it."
statements:
  - say:  { by: sam, at: now }
  # the owner: nobody edits this line, and its comment travels with it
  - own:  { by: sam, of: self }
  - name: { by: dns, of: self, as: relay.example.org }
---
The relay.
"""

T = tempfile.mkdtemp(prefix='converge-')
SITES = ('site-a', 'site-b', 'site-c')
try:
    REL = grow.release(os.path.join(T, 'release'))
    ORIGIN = os.path.join(T, 'origin')
    r = grow.garden(REL, ORIGIN, 'sam', '--name', 'relay-garden')
    check(f"an origin garden of the core grows from this tree (core@{grow.VERSION})", r.returncode == 0, r.out[-600:])
    attrs = text(ORIGIN, '.gitattributes')
    check("...its beans go to the statement merge and its journal to git's union",
          re.search(r'(?m)^beans/\*\*?\S* +merge=daftar', attrs) and re.search(r'(?m)^log/journal\.md +merge=union', attrs),
          attrs)
    write(ORIGIN, 'beans/relay.md', RELAY)
    r = commit(ORIGIN, 'the relay', '- action: wrote [[relay]]')
    check("the origin's relay is committed through its gate", r.returncode == 0, r.out[-600:])
    BASE = grow.run('git', 'rev-parse', 'HEAD', cwd=ORIGIN).stdout.strip()

    # ---- DIVERGE: three clones, each records the relay as it sees it, offline, through its own gate
    said = {
        'site-a': ('read: { by: sam, of: [mass-a], at: now }',
                   'measure: { id: mass-a, of: self, as: mass, value: { count: "4.2", unit: kg }, at: 2026-09-01 }'),
        'site-b': ('read: { by: sam, of: [mass-b, smtp], at: now }',
                   'measure: { id: mass-b, of: self, as: mass, value: { count: "4.3", unit: kg }, at: 2026-09-01 }',
                   'do: { id: smtp, by: self, as: mail-primary }'),
        'site-c': ('read: { by: sam, of: [dns], at: now }', 'do: { id: dns, by: self, as: dns-resolver }'),
    }
    ok = []
    for s in SITES:
        g = os.path.join(T, s)
        grow.run('git', 'clone', '-q', ORIGIN, g, cwd=T)
        grow.run(PY, 'bin/install.py', cwd=g)               # hooks and git's driver are a clone's own, never cloned
        add(g, 'beans/relay.md', *said[s])
        if s == 'site-c':
            write(g, 'beans/rack-c.md', '---\nbean: rack-c\nkind: host\ntitle: "rack-c — site-c\'s rack"\nstatements:\n'
                                        '  - say: { by: sam, at: now }\n  - own: { by: sam, of: self }\n---\nThe rack.\n')
        r = commit(g, f'{s}: the relay as seen there',
                   f'- action: {s} recorded [[relay]]' + (' and [[rack-c]]' if s == 'site-c' else ''))
        ok.append((s, r.returncode, r.out[-300:]))
    check("each clone's record is committed through its own gate", all(rc == 0 for _s, rc, _o in ok), ok)

    # ---- PACKAGE: one bundle per clone, git's own offline transport
    PKG = os.path.join(T, 'pkg')
    os.makedirs(PKG)
    for s in SITES:
        grow.run('git', 'bundle', 'create', '-q', os.path.join(PKG, s + '.bundle'), f'{BASE}..HEAD', cwd=os.path.join(T, s))
    check("the package is one self-verifying bundle per clone",
          all(grow.run('git', 'bundle', 'verify', os.path.join(PKG, s + '.bundle'), cwd=ORIGIN).returncode == 0
              for s in SITES), os.listdir(PKG))

    # ---- PULL BACK: a remote clone of the origin takes all three
    def pull_back(name, order):
        rem = os.path.join(T, name)
        grow.run('git', 'clone', '-q', ORIGIN, rem, cwd=T)
        grow.run(PY, 'bin/install.py', cwd=rem)
        out = []
        for s in order:
            grow.run('git', 'fetch', '-q', os.path.join(PKG, s + '.bundle'), f'HEAD:refs/heads/from-{s}', cwd=rem)
            m = grow.run('git', 'merge', '--no-commit', '--no-ff', f'from-{s}', cwd=rem)
            c = commit(rem, f'merged {s}', f'- action: merged {s}: [[relay]]' + (' and [[rack-c]]' if s == 'site-c' else ''))
            out.append((s, m.returncode, m.out, c.returncode, c.out))
        return rem, out

    REMOTE, merges = pull_back('remote', SITES)
    check("every clone pulls back cleanly: no git-level conflict anywhere",
          all(mrc == 0 and 'CONFLICT' not in mo for _s, mrc, mo, _c, _co in merges), merges)
    check("...the statement merge, not git's text merge, did the work", any('merge: relay' in mo for _s, _m, mo, _c, _co in merges),
          [mo for _s, _m, mo, _c, _co in merges])
    check("...and each merge is committed through the core's gate, with an entry of its own and two parents",
          all(crc == 0 for _s, _m, _mo, crc, _co in merges)
          and len(grow.run('git', 'log', '-1', '--format=%P', cwd=REMOTE).stdout.split()) == 2,
          [(s, co[-300:]) for s, _m, _mo, crc, co in merges if crc])
    relay = text(REMOTE, 'beans/relay.md')
    check("the relay holds the union of what every garden said: both masses, both roles",
          all(f'id: {i}' in relay for i in ('mass-a', 'mass-b', 'smtp', 'dns')), relay)
    check("...the two masses a disagreement, side by side: both values stand, each known by its garden's act",
          '"4.2"' in relay and '"4.3"' in relay and 'of: [mass-a]' in relay and 'of: [mass-b, smtp]' in relay, relay)
    check("a bean only one garden wrote arrives whole",
          os.path.isfile(os.path.join(REMOTE, 'beans/rack-c.md'))
          and text(REMOTE, 'beans/rack-c.md') == text(os.path.join(T, 'site-c'), 'beans/rack-c.md'))
    check("a statement nobody edited is untouched, its comment with it",
          '  # the owner: nobody edits this line, and its comment travels with it\n  - own:  { by: sam, of: self }' in relay
          or '  # the owner: nobody edits this line, and its comment travels with it\n  - own: { by: sam, of: self }' in relay,
          relay)
    journal = text(REMOTE, 'log/journal.md')
    check("every garden's journal entry survives: the journal merges by union, losing none",
          all(f'{s}: the relay as seen there' in journal for s in SITES)
          and all(f'merged {s}' in journal for s in SITES), journal[-1500:])
    r = grow.run(PY, 'core/check.py', '.', cwd=REMOTE)
    check("the converged garden passes the core's gate whole", r.returncode == 0 and '0 error(s)' in r.out, r.out[-800:])
    REMOTE2, merges2 = pull_back('remote-2', tuple(reversed(SITES)))
    check("...and a second remote that pulls the three back in the other order holds the same statements",
          all(crc == 0 for _s, _m, _mo, crc, _co in merges2)
          and statements(REMOTE2, 'beans/relay.md') == statements(REMOTE, 'beans/relay.md'),
          (statements(REMOTE2, 'beans/relay.md'), merges2[-1][4][-300:]))
except Exception as e:  # noqa: BLE001 — a crash of the suite is a failure of it, said once
    import traceback
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False, traceback.format_exc()[-900:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nconverge: {len(FAILS)} failed" + (": " + ", ".join(FAILS) if FAILS else ""))
sys.exit(1 if FAILS else 0)
