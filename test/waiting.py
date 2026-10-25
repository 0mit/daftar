#!/usr/bin/env python3
"""What waits is a need (core 3.7, the next machinery's design, body IV): the reading `waiting` (bin/waiting.py), leads'
decisions and `now` reading it, log/pending.md a view written from it by each save, the rule `knowing` holding a `meet`
by a person to that person's `say`, and the move of a queue's open entries to needs.

Grows a garden of the core and writes in it a plan with a need of each kind — one that blocks, one parked (`contingent`
of it), one that cannot be met, one blocked by another need, one met by the gardener's word, one whose nobody is named,
one from a codebase another person keeps, and a dependency of beings alone —; then holds what `waiting` reads, that
leads' decisions and `now` say the same, that the save wrote the view and writes it again when a need is met, and that
a `meet` by a person another's act knows is refused. Then a queue in the old form, an entry of each mark the move reads:
counted with nothing written, placed by its neighbourhood or the session that parked it, one placed by a map and one
split into parts by it, moved with its words whole, the closed entries kept as they were, saved through the gate.

Run: python3 test/waiting.py   (0 = green)
"""
import json, os, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import grow  # noqa: E402
import waiting as dmwaiting  # noqa: E402

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


def js(r):
    try:
        return json.loads(r.out[r.out.index('['):] if r.out.lstrip()[:1] == '[' else r.out[r.out.index('{'):])
    except ValueError:
        return None


def save(g, what, *body):
    return grow.run(PY, 'bin/save.py', 'sam', what, '--body', *body, cwd=g)


T = tempfile.mkdtemp(prefix='core-waiting-')
try:
    check("the seed's log/pending.md is the view's head and its mark, the text bin/waiting.py writes, zero entries",
          text(ROOT, 'seed/pending.md.template') == f"# @@GARDEN@@ — what waits\n\n{dmwaiting.HEAD}\n\n{dmwaiting.MARK}\n",
          text(ROOT, 'seed/pending.md.template'))
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'beans/p-1a2b3c4d.md', '---\nbean: p-1a2b3c4d\nkind: person\ntitle: "p-1a2b3c4d"\nstatements:\n'
                                    '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\np-1a2b3c4d\n')
    write(G, 'beans/session-plan.md', '''---
bean: session-plan
kind: session
title: "session-plan — an agent's work on the plan"
statements:
  - make: { by: self, at: now }
  - open: { id: opened, of: self, at: "2026-10-20T10:00:00+03:00" }
  - own:  { by: sam, of: self }
---
An agent's session.
''')
    write(G, 'beans/box.md', '---\nbean: box\nkind: host\ntitle: "box — a machine"\nstatements:\n'
                             '  - read: { by: sam, at: now }\n  - own: { by: sam, of: self }\n---\nA machine.\n')
    write(G, 'beans/tool-x.md', '''---
bean: tool-x
kind: codebase
title: "tool-x — a program"
statements:
  - read:   { by: sam, at: now }
  - own:    { by: sam, of: self }
  - answer: { by: p-1a2b3c4d, of: self, as: keeping }
---
A program.
''')
    write(G, 'beans/plan.md', '''---
bean: plan
kind: design
title: "plan — what the plan waits on"
statements:
  - make:        { by: session-plan, at: now }
  - own:         { by: sam, of: self }
  - need:        { id: a-row, by: self, of: "a garden row for hives", from: sam, note: "class G: a row of VOCAB.md" }
  - need:        { id: later, by: self, of: "a colour for the hives", from: sam, note: "class G" }
  - contingent:  { id: later-parked, of: later }
  - need:        { id: never, by: self, of: "a hive on the moon", from: sam }
  - impossible:  { id: never-cannot, of: never }
  - need:        { id: first, by: self, of: "the bees bought", from: sam }
  - need:        { id: second, by: self, of: ["the bees housed", first], from: sam }
  - need:        { id: done-one, by: self, of: "a place for the hives", from: sam, note: "class F" }
  - meet:        { id: done, by: sam, of: done-one }
  - say:         { by: sam, of: [done], at: now }
  - need:        { id: unsaid, by: self, of: "how many hives" }
  - need:        { id: from-tool, by: self, of: "an export of the hive counts", from: tool-x }
  - need:        { id: runs-on, by: self, of: [box] }
details:
  waiting:
    a-row:
      neighbourhood: "VOCAB.md's kinds; the bean of the hives"
      recommendation: "a kind hive, a body at the level of a made thing"
---
What the plan waits on.
''')
    r = save(G, 'a plan, its needs, a session, a machine and a program',
             '- action: wrote [[p-1a2b3c4d]], [[session-plan]], [[box]], [[tool-x]] and [[plan]]')
    check("the garden holds them, through its gate", r.returncode == 0, r.out[-900:])

    r = grow.run(PY, 'bin/waiting.py', '--json', cwd=G)
    items = {x['need']: x for x in (js(r) or [])}
    check("waiting: every need not met that waits on someone, and none met, nor a dependency of beings alone",
          sorted(items) == ['a-row', 'first', 'from-tool', 'later', 'never', 'second', 'unsaid'], r.out[-1200:])
    check("...its class read from its note, whose from its `from`, for the person it names",
          items.get('a-row', {}).get('class') == 'G' and items['a-row']['whose'] == ['sam'] and items['a-row']['for'] == ['sam']
          and items['a-row']['strength'] == 'blocks', items.get('a-row'))
    check("...a need `contingent` of which is parked, and one `impossible` cannot be met",
          items.get('later', {}).get('strength') == 'contingent' and items.get('never', {}).get('strength') == 'impossible',
          (items.get('later'), items.get('never')))
    check("...a need whose `of` names another need not met is blocked by it: a need of a need",
          items.get('second', {}).get('blocked_by') == ['plan#first'] and items['second']['what'] == 'the bees housed'
          and not items['first']['blocked_by'], items.get('second'))
    check("...one whose nobody is named is for whoever keeps or owns the being that needs it; one from a codebase for "
          "whoever keeps that", items.get('unsaid', {}).get('for') == ['sam']
          and items.get('from-tool', {}).get('for') == ['p-1a2b3c4d'], (items.get('unsaid'), items.get('from-tool')))
    r = grow.run(PY, 'bin/waiting.py', cwd=G)
    check("without --json it reads by whose, by class and by bean, and counts the dependencies apart",
          r.returncode == 0 and 'for sam: 6' in r.out and 'for p-1a2b3c4d: 1' in r.out and 'class G: 2' in r.out
          and 'plan#second' in r.out and 'blocked by plan#first' in r.out and 'which wait on nobody: 1' in r.out, r.out)
    leads = js(grow.run(PY, 'bin/leads.py', '--json', cwd=G)) or []
    dec = sorted((f"{x['about']}#{x['need']}", x['for']) for x in leads if x['kind'] == 'decision')
    check("leads' decisions are what waits, each for whom it is for",
          dec == sorted((x['ref'], p) for x in items.values() for p in x['for']), dec)
    now = js(grow.run(PY, 'bin/now.py', '--json', cwd=G)) or {}
    check("now: what waits on the gardener, each by its bean and id, its class and what it asks",
          sorted(w['id'] for w in now.get('waiting', [])) == sorted(x['ref'] for x in items.values() if 'sam' in x['for'])
          and any(w['id'] == 'plan#a-row' and w['class'] == 'G' and w['title'] == 'a garden row for hives'
                  for w in now.get('waiting', [])) and now.get('queue_left') == 0, now.get('waiting'))
    pend = text(G, 'log/pending.md')
    check("the save wrote log/pending.md's view from the needs: an entry for each that waits, with its strength and its "
          "neighbourhood", '## plan#a-row · a garden row for hives · from sam, class G' in pend
          and '- strength: parked: it does not block' in pend and "- neighbourhood: VOCAB.md's kinds" in pend
          and '## plan#done-one' not in pend and '## plan#runs-on' not in pend
          and grow.run('git', 'status', '--porcelain', cwd=G).out.strip() == '', pend[-1500:])

    # a need met by the gardener's word leaves the view in the save that meets it
    write(G, 'beans/plan.md', text(G, 'beans/plan.md').replace(
        '  - need:        { id: unsaid,',
        '  - meet:        { id: rowed, by: sam, of: a-row }\n'
        '  - say:         { by: sam, of: [rowed], at: now }\n  - need:        { id: unsaid,', 1))
    r = save(G, 'sam meets a-row', '- action: [[plan]] a-row met by sam')
    check("a need met by its person's `say` waits no more, and the save that meets it writes the view again",
          r.returncode == 0 and '## plan#a-row' not in text(G, 'log/pending.md')
          and '## plan#later' in text(G, 'log/pending.md'), r.out[-800:])

    # rule knowing: a meet by a person is known by that person's say, not by another's act
    before = text(G, 'beans/plan.md')
    write(G, 'beans/plan.md', before.replace('  - need:        { id: runs-on,',
                                             '  - meet:        { id: by-another, by: sam, of: later }\n'
                                             '  - need:        { id: runs-on,', 1))
    r = grow.run(PY, 'core/check.py', '.', cwd=G)
    check("knowing: a `meet` by a person that only another's act knows (the session's) is refused, naming whose word "
          "it is", r.returncode != 0 and 'plan[' in r.out and "a need met by sam is sam's word" in r.out, r.out[-800:])
    write(G, 'beans/plan.md', before.replace('  - need:        { id: runs-on,',
                                             '  - meet:        { id: by-tool, by: tool-x, of: later }\n'
                                             '  - need:        { id: runs-on,', 1))
    r = grow.run(PY, 'core/check.py', '.', cwd=G)
    check("...and a `meet` by a being that is not a person is known as any statement is", r.returncode == 0, r.out[-800:])
    write(G, 'beans/plan.md', before)

    # THE MOVE: a queue in the old form, an entry of each mark
    write(G, 'log/pending.md', '''# hives — pending-decisions queue

The old queue's head.

```
## <slug> · <what needs deciding> · proposed <YYYY-MM-DD> by <actor>
- status: proposed
```

---

## hive-kind · a kind for a hive · proposed 2026-10-01 by agent
- class: G-vocab-law
- neighbourhood: [[plan]] details; VOCAB.md
- proposal: a kind hive
- status: proposed

## old-fix · a fix made long ago · proposed 2026-09-01 by agent
- class: G
- neighbourhood: [[plan]]
- status: **acked — FIXED 2026-09-02**

## acked-still · decided, not built · proposed 2026-09-03 by agent
- class: G
- neighbourhood: `box`
- status: acked — DECIDED: build it

## a-colour · a colour for the boxes · parked 2026-09-04 by agent
- neighbourhood: beans/box.md
- status: parked.

## the-fence · a fence round the hives · proposed 2026-09-05 by agent
- neighbourhood: [[plan]]
- next: a post-hole digger, borrowed
- status: blocked

## half-built · a shed, half built · proposed 2026-09-06 by agent
- neighbourhood: [[plan]]
- status: proposed
- re-evaluated 2026-09-29 (c0mit): PARTLY DONE, verified: the roof is on; the walls wait

## still-open · a gate in the fence · proposed 2026-09-07 by agent
- neighbourhood: [[box]]
- status: proposed
- re-evaluated 2026-09-29 (c0mit): STILL OPEN, checked: nothing built

## all-done · a path · proposed 2026-09-08 by agent
- neighbourhood: [[plan]]
- status: done 2026-09-09.

## by-a-session · what the session left · proposed 2026-09-10 by agent (an agent, session-plan)
- found: nothing named
- status: proposed

## nowhere · named nowhere · proposed 2026-09-11 by agent
- found: no bean
- status: proposed

## odd-mark · its mark says nothing the move reads · proposed 2026-09-12 by agent
- neighbourhood: [[plan]]
- status: someday

## flow-bean · on a bean written in flow · proposed 2026-09-13 by agent
- neighbourhood: [[flowy]]
- status: proposed
''')
    write(G, 'beans/flowy.md', '---\nbean: flowy\nkind: host\ntitle: "flowy — a machine written in flow"\n'
                               'statements: [ { read: { by: sam, at: now } }, { own: { by: sam, of: self } } ]\n---\nA machine.\n')
    r = save(G, 'the queue in its old form', '- action: log/pending.md written in the old form, to be moved; [[flowy]] '
             'written')
    check("a queue in the old form is saved as it is: the save writes no view where the file holds no mark",
          r.returncode == 0 and '## plan#' not in text(G, 'log/pending.md'), r.out[-600:])
    r = grow.run(PY, 'bin/waiting.py', '--json', cwd=G)
    after_meet = sorted(x['ref'] for x in (js(r) or []))
    r = grow.run(PY, 'bin/now.py', cwd=G)
    check("now tells how many open entries the queue still holds, not moved", 'still holds 9 open entries' in r.out, r.out)
    r = grow.run(PY, 'bin/waiting.py', 'migrate', '--json', cwd=G)
    rows = {x['entry']: x for x in (js(r) or [])}
    kinds = {k: rows[k]['kind'] for k in rows}
    check("the move reads each entry by its last mark: proposed, acked still open, parked, blocked, partly, a STILL OPEN "
          "re-evaluation, and the closed ones, the fenced example none",
          kinds == {'hive-kind': 'proposed', 'old-fix': 'closed', 'acked-still': 'acked', 'a-colour': 'parked',
                    'the-fence': 'blocked', 'half-built': 'partly', 'still-open': 'proposed', 'all-done': 'closed',
                    'by-a-session': 'proposed', 'nowhere': 'proposed', 'odd-mark': None, 'flow-bean': 'proposed'}, kinds)
    beans = {k: rows[k]['bean'] for k in rows if rows[k]['kind'] not in ('closed', None)}
    check("...and places each on the bean its neighbourhood names — a link, a name in backquotes, a path —, else the "
          "session that parked it; one that names neither is not placed, and says why",
          beans == {'hive-kind': 'plan', 'acked-still': 'box', 'a-colour': 'box', 'the-fence': 'plan',
                    'half-built': 'plan', 'still-open': 'box', 'by-a-session': 'session-plan', 'nowhere': None,
                    'flow-bean': None}
          and 'no session' in rows['nowhere']['why'] and 'none of' in rows['odd-mark']['why']
          and 'flow' in rows['flow-bean']['why'], (beans, rows['nowhere'], rows['flow-bean']))
    check("...a blocked entry is a need of a need: what blocks it, from its `next:`, a need the entry's need asks",
          [(n['id'], n['of']) for n in rows['the-fence']['needs']] ==
          [('the-fence-first', 'a post-hole digger, borrowed'), ('the-fence', ['a fence round the hives', 'the-fence-first'])],
          rows['the-fence']['needs'])
    check("...a parked one a need of a lower strength", rows['a-colour']['needs'][0].get('contingent') == 'a-colour-parked',
          rows['a-colour']['needs'])
    check("...and the count writes nothing", grow.run('git', 'status', '--porcelain', cwd=G).out.strip() == '',
          grow.run('git', 'status', '--porcelain', cwd=G).out)
    write(T, 'map.tsv', '# where the move cannot place\nnowhere\tbean\tplan\nhalf-built\tpart\tthe walls\n'
                        'half-built\tpart\tthe door\nodd-mark\tas\tproposed\nflow-bean\tbean\tbox\n')
    r = grow.run(PY, 'bin/waiting.py', 'migrate', '--map', os.path.join(T, 'map.tsv'), cwd=G)
    check("a map places an entry, reads a mark as another kind, and splits a partly one into its parts",
          'placed: 10 of 10' in r.out and 'not placed: 0' in r.out and 'half-built-2' in r.out, r.out[-900:])
    r = grow.run(PY, 'bin/waiting.py', 'migrate', '--map', os.path.join(T, 'map.tsv'), '--write', cwd=G)
    check("--write names the being whose act knows the needs", r.returncode != 0 and '--by' in r.out, r.out[-400:])
    old = text(G, 'log/pending.md')
    r = grow.run(PY, 'bin/waiting.py', 'migrate', '--map', os.path.join(T, 'map.tsv'), '--by', 'session-plan', '--write',
                 cwd=G)
    check("the move writes the beans and log/pending.md, and leaves the entry for the mover's save",
          r.returncode == 0 and 'bin/save.py' in r.out, r.out[-800:])
    import yaml
    fm = yaml.safe_load(text(G, 'beans/plan.md').split('\n---', 1)[0][4:])
    words = (fm.get('details') or {}).get('waiting') or {}
    _pre, entries = dmwaiting.entries(old)
    whole = {h[3:].split(' · ')[0]: e.rstrip('\n') for h, e in entries}
    check("...each entry's words carried whole, into details.waiting.<id>.words, beside the entry it was and how it was read",
          words.get('hive-kind', {}).get('words') == whole['hive-kind'] and words['hive-kind']['queue'] == 'hive-kind'
          and words.get('the-fence', {}).get('read_as') == 'blocked' and words.get('nowhere', {}).get('words') == whole['nowhere']
          and words.get('a-row', {}).get('neighbourhood'), sorted(words))
    pend = text(G, 'log/pending.md')
    check("...log/pending.md now the view and, below it, the closed entries as they were, history, and where each open "
          "one went", pend.startswith('# hives — what waits\n') and dmwaiting.MARK in pend
          and whole['old-fix'] + '\n' in pend and whole['all-done'] + '\n' in pend and '## hive-kind ·' not in pend
          and '- hive-kind: [[plan]] hive-kind' in pend and '## plan#hive-kind · a kind for a hive · from sam, class G' in pend
          and '```' not in pend, pend[:2500])
    entry = r.out.split(' < ')[-1].strip()
    r = grow.run(PY, 'bin/save.py', 'session-plan', "what waits: the queue's open entries moved to needs", cwd=G,
                 stdin=open(entry, encoding='utf-8').read())
    check("the mover's save carries it through the gate", r.returncode == 0, r.out[-1200:])
    r = grow.run(PY, 'bin/waiting.py', '--json', cwd=G)
    moved = {x['ref']: x for x in (js(r) or [])}
    check("what waits after the move: what waited before, and a need for each entry moved — parked, blocked and the "
          "parts as the mapping says", set(after_meet) <= set(moved)
          and moved.get('box#a-colour', {}).get('strength') == 'contingent'
          and moved.get('plan#the-fence', {}).get('blocked_by') == ['plan#the-fence-first']
          and moved.get('plan#half-built', {}).get('what') == 'the walls' and moved.get('plan#half-built-2', {}).get('what') == 'the door'
          and 'session-plan#by-a-session' in moved and 'plan#nowhere' in moved and 'box#acked-still' in moved, sorted(moved))
    leads = js(grow.run(PY, 'bin/leads.py', '--json', cwd=G)) or []
    dec = sorted((f"{x['about']}#{x['need']}", x['for']) for x in leads if x['kind'] == 'decision')
    check("...and leads' decisions are still what waits", dec == sorted((x['ref'], p) for x in moved.values() for p in x['for']),
          dec)
    r = grow.run(PY, 'bin/waiting.py', 'migrate', cwd=G)
    check("...and a second move finds nothing open left to move", 'open 0' in r.out and 'placed: 0 of 0' in r.out, r.out[-400:])
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nwaiting: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
