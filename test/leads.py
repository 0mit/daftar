#!/usr/bin/env python3
"""Leads: what waits, and for whom — a reading of the garden for each person, never stored, read from what the garden
already says (bin/leads.py). Who is told is never configured.

Grows a garden of the core and writes in it: a decision parked for the gardener (`status: proposed`, class G); one of
class F, which a `grant … as: ratify, class: F` of the gardener's opens to another person; a bicycle repair on a walk,
waiting at a step whose `by` names the part the repairer took in its agreement, and past the step's `usually`; a step
whose part nobody took; a case at a final step; and an agent session left open. Then each lead is for whom the garden
says, and `--for` reads one person's alone.

Run: python3 test/leads.py   (0 = green)
"""
import json, os, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1200:]))
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


T = tempfile.mkdtemp(prefix='core-leads-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'VOCAB.md', '---\nkinds:\n  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n'
                         '---\n# the garden\'s own rows\n')
    write(G, 'beans/p-1a2b3c4d.md', '---\nbean: p-1a2b3c4d\nkind: person\ntitle: "p-1a2b3c4d"\nstatements:\n'
                                    '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\np-1a2b3c4d\n')
    write(G, 'mappings/walk-repair.md', '''---
bean: walk-repair
kind: procedure
title: "walk-repair — how a bicycle repair goes"
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "the owner brings the bicycle", by: owner, to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", by: repairer, to: [mended], walk: { usually: { of: time, measure: { count: "2", unit: d } } } }
  - step: { id: mended, as: "it is mended", by: mechanic, to: [collected] }
  - step: { id: collected, as: "the owner takes it home", by: owner, walk: { final: "true" } }
---
The steps of a repair.
''')
    agreement = '''---
bean: {bean}
kind: contract
title: "{bean} — a bicycle repaired"
statements:
  - say:    {{ by: sam, at: now }}
  - own:    {{ by: theone, of: self }}
  - answer: {{ by: sam, of: self, as: law }}
  - answer: {{ by: p-1a2b3c4d, of: self, as: law }}
  - agree:  {{ by: sam, of: "the bicycle", through: spoken, as: repairer }}
  - agree:  {{ by: p-1a2b3c4d, of: "the bicycle", through: spoken, as: owner }}
  - be:     {{ id: repair, by: self, at: walk-repair, as: order }}
{moves}---
A repair.
'''
    move = '  - move:   {{ by: {by}, of: self, through: repair, at: ["{at}", "walk-repair#{step}"] }}\n'
    write(G, 'beans/repair-waiting.md', agreement.format(bean='repair-waiting', moves=''.join(
        move.format(by=b, at=a, step=s) for b, a, s in (('p-1a2b3c4d', '2026-10-01 10:00+03:00', 'handed-over'),
                                                         ('sam', '2026-10-01 11:00+03:00', 'looked-at')))))
    write(G, 'beans/repair-nobody.md', agreement.format(bean='repair-nobody', moves=''.join(
        move.format(by=b, at=a, step=s) for b, a, s in (('p-1a2b3c4d', '2026-10-02 10:00+03:00', 'handed-over'),
                                                         ('sam', '2026-10-02 11:00+03:00', 'looked-at'),
                                                         ('sam', '2026-10-03 11:00+03:00', 'mended')))))
    write(G, 'beans/repair-done.md', agreement.format(bean='repair-done', moves=''.join(
        move.format(by=b, at=a, step=s) for b, a, s in (('p-1a2b3c4d', '2026-09-01 10:00+03:00', 'handed-over'),
                                                         ('sam', '2026-09-01 11:00+03:00', 'looked-at'),
                                                         ('sam', '2026-09-02 11:00+03:00', 'mended'),
                                                         ('p-1a2b3c4d', '2026-09-03 11:00+03:00', 'collected')))))
    write(G, 'beans/sam.md', text(G, 'beans/sam.md').replace(
        '---\nSam', '  - grant: { id: ratify-f, by: self, as: ratify, class: F, to: [p-1a2b3c4d] }\n'
                    '  - say: { by: sam, of: [ratify-f], at: now }\n---\nSam', 1))
    write(G, 'log/pending.md', text(G, 'log/pending.md').rstrip('\n') + '''

## rows-for-hives · a garden row for hives · proposed 2026-10-09 by agent (a session)
- class: G
- status: proposed

## a-new-name · a name that establishes an identity · proposed 2026-10-09 by agent (a session)
- class: F (a name)
- status: proposed

## settled-already · a decision taken · proposed 2026-10-01 by agent (a session)
- class: G
- status: ratified
''')
    write(G, 'beans/session-open.md', '''---
bean: session-open
kind: session
title: "session-open — an agent's work, left open"
statements:
  - make: { by: self, at: now }
  - open: { id: opened, of: self, at: "2026-10-09T10:00:00+03:00" }
  - own:  { by: sam, of: self }
details:
  status: active
---
An agent's session.
''')
    write(G, 'beans/session-closed.md', '''---
bean: session-closed
kind: session
title: "session-closed — an agent's work, closed"
statements:
  - make: { by: self, at: now }
  - open: { id: opened, of: self, at: "2026-10-08T10:00:00+03:00" }
  - own:  { by: sam, of: self }
  - be:   { id: present, by: self, at: "2026-10-08T10:00:00+03:00/2026-10-08T12:00:00+03:00", as: presence }
details:
  status: active
---
An agent's session, closed (its status left as it was, as bin/session.py leaves it).
''')
    import datetime
    soon = (datetime.date.today() + datetime.timedelta(days=3)).isoformat()
    later = (datetime.date.today() + datetime.timedelta(days=300)).isoformat()
    write(G, 'beans/flat-lease.md', f'''---
bean: flat-lease
kind: contract
title: "flat-lease — a room let"
statements:
  - say:        {{ by: sam, at: now }}
  - own:        {{ by: theone, of: self }}
  - answer:     {{ by: sam, of: self, as: law }}
  - answer:     {{ by: p-1a2b3c4d, of: self, as: law }}
  - agree:      {{ by: sam, of: "the room", through: spoken, as: landlord }}
  - agree:      {{ by: p-1a2b3c4d, of: "the room", through: spoken, as: tenant }}
  - pay:        {{ id: rent, by: p-1a2b3c4d, to: sam, of: {{ count: "100.00", unit: XTS }} }}
  - obligatory: {{ id: rent-due, of: rent, through: self, clause: {{ due: "{soon}" }} }}
  - pay:        {{ id: deposit-back, by: sam, to: p-1a2b3c4d, of: {{ count: "200.00", unit: XTS }} }}
  - obligatory: {{ id: deposit-due, of: deposit-back, through: self, clause: {{ due: "{later}" }} }}
---
A room let.
''')
    host = """---
bean: {bean}
kind: host
title: "{bean} — a machine"
statements:
  - read:    {{ by: sam, at: now }}
  - own:     {{ by: sam, of: self }}
  - answer:  {{ by: p-1a2b3c4d, of: self, as: keeping }}
{more}---
A machine.
"""
    write(G, 'beans/box-slow.md', host.format(bean='box-slow', more=(
        '  - measure: { id: clock-offset, of: self, as: duration, value: { count: "31", unit: s }, at: 2026-10-09 }\n'
        '  - fail:    { id: clock-drift, by: self, as: "the clock runs past the 30 s a stamp is taken within", through: clock-offset, at: 2026-10-09 }\n')))
    write(G, 'beans/box-mended.md', host.format(bean='box-mended', more=(
        '  - measure: { id: clock-offset, of: self, as: duration, value: { count: "45", unit: s }, at: 2026-10-01 }\n'
        '  - fail:    { id: clock-drift, by: self, as: "the clock ran slow", through: clock-offset, at: 2026-10-01 }\n'
        '  - repair:  { by: sam, of: clock-drift }\n')))
    write(G, 'beans/box-finding.md', host.format(bean='box-finding', more=(
        '  - fail:    { id: no-firewall, by: self, as: "no firewall is active", at: 2026-09-11 }\n')))
    r = grow.run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a repair walk, three repairs, a ratify grant and an open session',
                 '--body', '- action: RULE-CHANGE — VOCAB.md adds the kind procedure; wrote [[p-1a2b3c4d]], [[walk-repair]], '
                 '[[repair-waiting]], [[repair-nobody]], [[repair-done]], [[sam]], [[session-open]], [[session-closed]], [[flat-lease]], '
                 '[[box-slow]], [[box-mended]] and [[box-finding]]', '- ratified_by: sam', cwd=G)
    check("the garden holds them, through its gate", r.returncode == 0, r.out[-900:])

    grow.run('git', 'worktree', 'add', '-q', '-b', 'session/open-work', os.path.join(T, 'open-work'), cwd=G)
    r = grow.run(PY, 'bin/leads.py', '--json', cwd=G)
    try:
        leads = json.loads(r.out[r.out.index('['):])
    except ValueError:
        leads = []
    by = lambda kind, about: [x for x in leads if x.get('kind') == kind and x.get('about') == about]
    check("leads: a decision parked for the gardener is the gardener's, its class said",
          [x['for'] for x in by('decision', 'rows-for-hives')] == ['sam'] and by('decision', 'rows-for-hives')[0]['class'] == 'G',
          leads)
    check("...one of a class a ratify grant opens is the grant's holder's too",
          sorted(x['for'] for x in by('decision', 'a-new-name')) == ['p-1a2b3c4d', 'sam'], by('decision', 'a-new-name'))
    check("...and one taken already is nobody's", not by('decision', 'settled-already'), leads)
    w = by('case', 'repair-waiting')
    check("leads: a case at a step is the party's whose part the step names — the repairer's — and overdue past its usual",
          [x['for'] for x in w] == ['sam'] and w[0]['step'] == 'looked-at' and w[0]['overdue'] is True
          and w[0]['walk'] == 'walk-repair', w)
    n = by('case', 'repair-nobody')
    check("...a step whose part nobody took is the gardener's, saying so", [x['for'] for x in n] == ['sam']
          and 'nobody' in n[0]['why'], n)
    check("...and a case at a final step is nobody's", not by('case', 'repair-done'), leads)
    check("leads: an agent session left open (its worktree, as bin/session.py lists it) is the gardener's, to close or "
          "ratify; a session bean alone, open or closed in its own words, is no lead",
          [x['for'] for x in by('session', 'session-open-work')] == ['sam'] and not by('session', 'session-open')
          and not by('session', 'session-closed'), leads)
    o = by('obligation', 'flat-lease')
    check("leads: an obligation falling due within its notice is the party's it binds — who pays what it asks — and one "
          "far off is nobody's yet", [(x['for'], x.get('clause')) for x in o] == [('p-1a2b3c4d', 'rent-due')]
          and o[0].get('due') == soon, o)
    hl = [x for x in leads if x.get('kind') == 'health']
    check("leads: a failure a reading shows, not yet repaired, is the keeper's — and one repaired, or a finding with no "
          "reading behind it, is nobody's", [(x['for'], x['about'], x['fail']) for x in hl] == [('p-1a2b3c4d', 'box-slow', 'clock-drift')]
          and 'duration 31 s' in hl[0]['why'], hl)
    r2 = grow.run(PY, 'bin/leads.py', '--json', '--for', 'p-1a2b3c4d', cwd=G)
    mine = json.loads(r2.out[r2.out.index('['):]) if '[' in r2.out else []
    check("--for reads one person's leads alone", mine and {x['for'] for x in mine} == {'p-1a2b3c4d'}, r2.out[-600:])
    r3 = grow.run(PY, 'bin/leads.py', cwd=G)
    check("without --json each lead is a line for a person to read", r3.returncode == 0 and 'sam' in r3.out
          and 'looked-at' in r3.out and 'rows-for-hives' in r3.out, r3.out[-800:])
    check("a reading writes nothing", grow.run('git', 'status', '--porcelain', cwd=G).out.strip() == '',
          grow.run('git', 'status', '--porcelain', cwd=G).out)
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nleads: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
