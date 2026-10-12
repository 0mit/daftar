#!/usr/bin/env python3
"""Routines: a machine's routines read from the garden and run by the one engine (bin/routines.py, bin/act.py).

Grows a garden of the core in which this machine (`box`) runs a weekly restart of a server (`server-a`): a walk with no
person's step, granted to the machine (`grant … as: enact`), its interlocks the walk's needs (nobody signed in, no file
open: readings of the tool's probe), its proof the server's own need (its services up). Then, against a fake server the
tool reads and writes in a directory:

- the reading: when it falls due, at its clock time in the garden's zone, and its window; who runs it; what it needs;
- the moments: a weekly routine at 05:45 on Sundays; every five minutes; hourly at :15; a wall clock kept across a
  change of the clocks;
- the engine: its notice told 36 hours before (one missed, at the next tick before the run, said late); at its
  occurrence, with someone signed in, the run waits at the walk's pause and nothing is applied (a lead for the server's
  keeper); the next tick, nobody signed in, it returns and runs through to done, the server restarted and read back; a second occurrence whose window closes while it waits is skipped; a third whose proof fails
  is rolled back, its crossing written (a health lead), and its next failing run writes no second fail; a walk nobody
  granted is not run; a routine present in a crontab is cron's, never the engine's;
- crossings: a need of a being read against the probes writes its `measure` and `fail` once, and its `repair` when it
  holds again; a remedy walk named for the need is proposed, stopping at its person's step — and waiting, never
  refused, while its key is out, whether at its check or pulled while it copies;
- cron: a crontab adopted as routines, each line proved byte for byte, a line the garden cannot say refused with why;
  and `render cron` writes the routines present in the crontab;
- the readers: a routine's clause is no obligation lead and nothing `bin/stale.py` warns of.

Run: python3 test/routines.py   (0 = green)
"""
import json, os, shutil, socket, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
sys.path.insert(0, os.path.join(ROOT, 'bin'))
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


# THE FAKE SERVER: a directory the tool reads (its probe) and writes (a restart). `sessions`, `open-files` and
# `services-down` hold numbers; `restarts` counts the restarts applied; `after-down` is what a restart leaves down.
TOOL = r'''import json, os, sys, datetime
live = os.environ.get('LIVE_DIR', '/nonexistent')
def num(name, default='0'):
    p = os.path.join(live, name)
    return open(p).read().strip() if os.path.exists(p) else default
def put(name, v):
    open(os.path.join(live, name), 'w').write(str(v))
step = sys.argv[1]
if step == 'probe':
    at = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    out = []
    for being in ('server-a', 'server-b', 'server-c', 'server-u'):
        for key, name in (('server.sessions', 'sessions'), ('server.open_files', 'open-files'), ('server.services_down', 'services-down')):
            out.append({'key': key, 'being': being, 'property': 'number', 'value': {'count': num(name), 'unit': '{item}'},
                        'at': at, 'instrument': 'restart-tool:fake', 'quality': 'ok'})
            if name == 'services-down' and num(name) != '0' and num('down-detail', ''):
                out[-1]['detail'] = num('down-detail', '').replace('|', '\n')     # what the reading saw, in words
    print(json.dumps({'tool': 'restart-tool', 'version': '1', 'at': at, 'readings': out}))
    sys.exit(0)
bean, course = sys.argv[2:4]
if step == 'plan':
    print('restart ' + bean + ': ' + num('sessions') + ' signed in, ' + num('open-files') + ' file(s) open')
elif step == 'check':
    sys.exit(0)
elif step == 'apply':
    put('restarts', int(num('restarts')) + 1)
    put('services-down', num('after-down'))
elif step == 'verify':
    sys.exit(0)
elif step == 'restore':
    put('restored', int(num('restored')) + 1)
elif step == 'notice':
    put('notice', bean + ' ' + course)
    print('the restart of ' + bean + ' falls on ' + course.rsplit('-', 2)[1])
'''

# A DEPOT a crossing proposes to prune: its tool reads how full it is and whether the key (a USB drive) is in; its walk
# keeps what it would drop first (`stash`, a step of its own), then waits for a person to ratify the prune.
DEPOT_TOOL = r'''import json, os, sys, datetime
live = os.environ.get('LIVE_DIR', '/nonexistent')
def num(name, default='0'):
    p = os.path.join(live, name)
    return open(p).read().strip() if os.path.exists(p) else default
def put(name, v):
    open(os.path.join(live, name), 'w').write(str(v))
step = sys.argv[1]
if step == 'probe':
    at = datetime.datetime.now().astimezone().isoformat(timespec='seconds')
    print(json.dumps({'tool': 'depot-tool', 'version': '1', 'at': at, 'readings': [
        {'key': 'depot.fill', 'being': 'depot', 'property': num('depot-property', 'ratio'), 'value': {'count': num('depot-fill'), 'unit': '%'},
         'at': at, 'instrument': 'depot-tool:fake', 'quality': 'ok'},
        {'key': 'usb.present', 'being': 'depot', 'property': 'number', 'value': {'count': num('key'), 'unit': '{item}'},
         'at': at, 'instrument': 'depot-tool:fake', 'quality': 'ok'}]}))
    sys.exit(0)
if step == 'plan':
    print('prune the depot: it is at ' + num('depot-fill') + '%')
elif step == 'check':
    sys.exit(0 if num('key') == '1' else 1)          # the tool's own check fails while the key is out
elif step == 'stash':
    if num('pull-key') == '1':                       # the key pulled while the copy runs
        put('key', '0'); put('pull-key', '0'); sys.exit(1)
    put('stashed', int(num('stashed')) + 1)
elif step == 'apply':
    put('depot-fill', '40')
'''

T = tempfile.mkdtemp(prefix='core-routines-')
LIVE = os.path.join(T, 'live')
os.makedirs(LIVE)
os.environ['LIVE_DIR'] = LIVE
grow.ENV['LIVE_DIR'] = LIVE

WALK = '''---
bean: routine-restart
kind: procedure
title: "routine-restart — a server restarted when nobody would lose work, and read back"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: restart-tool }
  - step: { id: plan, as: "who and what a restart would interrupt", by: engine, to: [show] }
  - step: { id: show, as: "the plan, line by line", by: engine, to: [check] }
  - step: { id: check, as: "the tool's checks, and every interlock, read now", by: engine, to: [apply] }
  - step: { id: apply, as: "the restart", by: engine, to: [verify] }
  - step: { id: verify, as: "read back: the server's own needs hold again", by: engine, to: [done] }
  - step: { id: done, as: "restarted and read back", walk: { final: "true" } }
  - step: { id: waits, as: "an interlock does not hold: read again each minute of the window", by: keeper, walk: { resumes: "true", reasons: [interlock-held] } }
  - step: { id: skipped, as: "the window closed before the interlocks held: nothing was done", walk: { exit: "true", final: "true", reasons: [window-passed] } }
  - step: { id: refused, as: "nothing was changed", walk: { exit: "true", reasons: [cannot-plan, check-failed] } }
  - step: { id: rolled-back, as: "restored, and the crossing written", walk: { exit: "true", reasons: [apply-failed, verify-mismatch] } }
  - need: { id: no-sessions, by: self, of: "nobody signed in on the server", from: server-a }
  - meet: { by: none-signed-in, of: no-sessions }
  - reckon: { id: none-signed-in, reading: { what: "nobody is signed in on the server (its sessions, counted)", inputs: [ { name: server-sessions, origin: { act: read, nature: soma, by: restart-tool }, quantity: number } ], steps: [ { id: zero, op: constant, value: { count: "0", unit: "{item}" } }, { id: ok, op: compare, of: server-sessions, with: zero, is: at-most } ] } }
  - need: { id: no-open-files, by: self, of: "no file open on the server's shares", from: server-a }
  - meet: { by: none-open, of: no-open-files }
  - reckon: { id: none-open, reading: { what: "no file is open on the server's shares (counted)", inputs: [ { name: server-open-files, origin: { act: read, nature: soma, by: restart-tool }, quantity: number } ], steps: [ { id: zero, op: constant, value: { count: "0", unit: "{item}" } }, { id: ok, op: compare, of: server-open-files, with: zero, is: at-most } ] } }
---
The walk of a server's restart.
'''


def server(bid, due, day, extra=''):
    return f'''---
bean: {bid}
kind: host
title: "{bid} — a server box restarts"
statements:
  - read:   {{ by: sam, at: now }}
  - own:    {{ by: sam, of: self }}
  - run:    {{ id: restart-each-week, by: box, of: routine-restart }}
  - obligatory: {{ id: restart-each-week-due, of: restart-each-week, through: sam, clause: {{ due: "{due}", every: {{ of: time, in: iso-week, each: week, at: "{day}", lasts: {{ of: time, measure: {{ count: "30", unit: min }} }} }} }} }}
  - need:   {{ id: services-up, by: self, of: "every service of the server runs" }}
  - meet:   {{ by: none-down, of: services-up }}
  - reckon: {{ id: none-down, reading: {{ what: "no service of the server is down (counted)", inputs: [ {{ name: server-services-down, origin: {{ act: read, nature: soma, by: restart-tool }}, quantity: number }} ], steps: [ {{ id: zero, op: constant, value: {{ count: "0", unit: "{{item}}" }} }}, {{ id: ok, op: compare, of: server-services-down, with: zero, is: at-most }} ] }} }}
{extra}---
A server.
'''


def readings(path, sessions='0', open_files='0', down='0', being='server-a'):
    doc = {'tool': 'restart-tool', 'version': '1', 'at': '2026-10-18T05:46:00+03:00', 'readings': [
        {'key': 'server.sessions', 'being': being, 'property': 'number', 'value': {'count': sessions, 'unit': '{item}'},
         'at': '2026-10-18T05:46:00+03:00', 'instrument': 'restart-tool:fake', 'quality': 'ok'},
        {'key': 'server.open_files', 'being': being, 'property': 'number', 'value': {'count': open_files, 'unit': '{item}'},
         'at': '2026-10-18T05:46:00+03:00', 'instrument': 'restart-tool:fake', 'quality': 'ok'},
        {'key': 'server.services_down', 'being': being, 'property': 'number', 'value': {'count': down, 'unit': '{item}'},
         'at': '2026-10-18T05:46:00+03:00', 'instrument': 'restart-tool:fake', 'quality': 'ok'}]}
    with open(path, 'w', encoding='utf-8') as fh:
        json.dump(doc, fh)
    return path


def live(**kw):
    for k, v in kw.items():
        with open(os.path.join(LIVE, k.replace('_', '-')), 'w') as fh:
            fh.write(str(v))


def lv(name, default='0'):
    p = os.path.join(LIVE, name)
    return open(p).read().strip() if os.path.exists(p) else default


try:
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    # the garden's zone named, so the clocks below read the same wherever this runs (a CI runner keeps UTC)
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam', '--zone', 'Europe/Istanbul')
    check("a garden grows, kept by sam", r.returncode == 0, r.out[-600:])
    write(G, 'tools/restart.py', TOOL)
    write(G, 'tools/depot.py', DEPOT_TOOL)
    write(G, 'beans/depot-tool.md', f'''---
bean: depot-tool
kind: program
title: "depot-tool — what reads and prunes the depot"
statements:
  - make: {{ by: sam, at: now }}
  - be:   {{ by: self, at: "{HOST}:{G}/tools/depot.py", as: location }}
---
The tool.
''')
    write(G, 'mappings/depot-prune.md', '''---
bean: depot-prune
kind: procedure
title: "depot-prune — the depot pruned, what it drops kept first, ratified by a person"
statements:
  - say:  { by: sam, at: now }
  - use:  { by: self, of: depot-tool }
  - step: { id: plan, as: "what the prune would drop", by: engine, to: [show] }
  - step: { id: show, as: "the plan, line by line", by: engine, to: [check] }
  - step: { id: check, as: "the tool's checks, and the key in", by: engine, to: [stash] }
  - step: { id: stash, as: "what the prune drops, kept on the key first", by: engine, to: [ratify] }
  - step: { id: ratify, as: "a person ratifies the prune", by: ratifier, to: [apply, show] }
  - step: { id: apply, as: "the prune", by: engine, to: [verify] }
  - step: { id: verify, as: "read back", by: engine, to: [done] }
  - step: { id: done, as: "pruned and read back", walk: { final: "true" } }
  - step: { id: waits, as: "the key is not in: read again each tick", by: keeper, walk: { resumes: "true", reasons: [interlock-held] } }
  - step: { id: refused, as: "nothing was dropped", walk: { exit: "true", reasons: [cannot-plan, check-failed, stash-failed, declined] } }
  - step: { id: rolled-back, as: "put back", walk: { exit: "true", reasons: [apply-failed, verify-mismatch] } }
  - need: { id: key-in, by: self, of: "the key (a USB drive) is in", from: box }
  - meet: { by: key-present, of: key-in }
  - reckon: { id: key-present, reading: { what: "the key is in (counted)", inputs: [ { name: usb-present, origin: { act: read, nature: soma, by: depot-tool }, quantity: number } ], steps: [ { id: one, op: constant, value: { count: "1", unit: "{item}" } }, { id: ok, op: compare, of: usb-present, with: one, is: at-least } ] } }
---
The walk of a depot's prune.
''')
    write(G, 'beans/depot.md', '''---
bean: depot
kind: document
title: "depot — what the backups keep"
statements:
  - say:    { by: sam, at: now }
  - own:    { by: sam, of: self }
  - need:   { id: below-gate, by: self, of: "the depot below 85 in a hundred full" }
  - meet:   { by: below, of: below-gate }
  - reckon: { id: below, reading: { what: "the depot is less than 85 % full", inputs: [ { name: depot-fill, origin: { act: read, nature: soma, by: depot-tool }, quantity: ratio } ], steps: [ { id: gate, op: constant, value: { count: "85", unit: "%" } }, { id: ok, op: compare, of: depot-fill, with: gate, is: less } ] } }
  - repair: { id: prune-remedy, of: below-gate, at: depot-prune, note: "the walk that brings it below its gate" }
---
A depot.
''')
    write(G, 'VOCAB.md', '---\nkinds:\n  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }\n'
                         'namespaces:\n  - { namespace: anchor-hostname, once: "false", meaning: "a machine\'s own name for itself" }\n'
                         '---\n# the garden\'s own rows\n')
    write(G, 'beans/sam.md', text(G, 'beans/sam.md').replace(
        '---\nSam', '  - grant: { id: box-restarts, by: self, to: [box], of: [routine-restart], as: enact }\n'
                    '  - say: { by: sam, of: [box-restarts], at: now }\n---\nSam', 1))
    write(G, 'beans/box.md', f'''---
bean: box
kind: host
title: "box — the machine the routines run on"
statements:
  - read: {{ by: sam, at: now }}
  - own:  {{ by: sam, of: self }}
  - name: {{ by: anchor-hostname, of: self, as: {HOST} }}
  - run:  {{ id: cron-backup, by: self, of: cron-backup }}
  - obligatory: {{ id: cron-backup-due, of: cron-backup, through: sam, clause: {{ due: "2026-10-12 00:15", every: {{ of: time, in: gregorian-civil, each: day }} }} }}
---
The machine.
''')
    write(G, 'beans/restart-tool.md', f'''---
bean: restart-tool
kind: program
title: "restart-tool — what restarts a server and reads it back"
statements:
  - make: {{ by: sam, at: now }}
  - be:   {{ by: self, at: "{HOST}:{G}/tools/restart.py", as: location }}
---
The tool.
''')
    write(G, 'mappings/routine-restart.md', WALK)
    write(G, 'mappings/cron-backup.md', f'''---
bean: cron-backup
kind: procedure
title: "cron-backup — the nightly backup, as cron runs it"
statements:
  - say:  {{ by: sam, at: now }}
  - be:   {{ id: in-crontab, by: self, at: "{HOST}:/var/spool/cron/crontabs/root", as: presence }}
  - step: {{ id: run, as: "/root/backup.sh >/dev/null 2>&1", by: engine }}
---
A job cron runs.
''')
    write(G, 'mappings/routine-unseen.md', WALK.replace('routine-restart', 'routine-unseen').replace('restarted when', 'restarted, unseen, when'))
    write(G, 'beans/p-1a2b3c4d.md', '---\nbean: p-1a2b3c4d\nkind: person\ntitle: "p-1a2b3c4d"\nstatements:\n'
                                    '  - say: { by: sam, at: now }\n  - own: { by: theone, of: self }\n---\np-1a2b3c4d\n')
    write(G, 'beans/server-a.md', server('server-a', '2026-10-18 05:45', '7',
                                         '  - answer: { by: p-1a2b3c4d, of: self, as: keeping }\n').replace(
        'clause: { due:', 'clause: { notice: { count: "36", unit: h }, due:'))
    write(G, 'beans/server-b.md', server('server-b', '2026-10-24 05:45', '6'))
    write(G, 'beans/server-c.md', server('server-c', '2026-10-26 05:45', '1'))
    write(G, 'beans/server-u.md', server('server-u', '2026-10-27 05:45', '2').replace('of: routine-restart', 'of: routine-unseen'))
    r = grow.run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: a machine, its routines and their walks', '--body',
                 '- action: RULE-CHANGE — VOCAB.md adds the kind procedure and the namespace anchor-hostname; wrote [[box]], '
                 '[[restart-tool]], [[routine-restart]], [[routine-unseen]], [[cron-backup]], [[server-a]], [[server-b]], '
                 '[[server-c]], [[server-u]], [[p-1a2b3c4d]], [[depot]], [[depot-tool]], [[depot-prune]]; [[sam]] grants box enact '
                 'of the restart walk', '- ratified_by: sam', cwd=G)
    check("the garden holds the routines, their walks, the tool, the machine and its grant, through its gate — no new law",
          r.returncode == 0, r.out[-1200:])

    def rt(*a, cwd=G):
        return grow.run(PY, 'bin/routines.py', *a, cwd=cwd)

    # ---- the reading
    r = rt('list', '--at', '2026-10-11 12:00+03:00', '--json')
    rows = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip().startswith('[') else []
    a = next((x for x in rows if x['routine'] == 'server-a#restart-each-week'), {})
    check("list: a routine is read — its machine, walk, schedule, next occurrence at its clock time in the garden's zone, "
          "its window", a.get('machine') == 'box' and a.get('walk') == 'routine-restart'
          and a.get('next') == '2026-10-18 05:45+03:00' and a.get('window') == '30 min' and a.get('zone') == 'Europe/Istanbul',
          r.out[-1500:])
    check("list: who runs it is read from the garden — this machine's engine, by the grant; cron's job, by its presence; "
          "a walk nobody granted, nobody", a.get('runner') == "this machine's engine"
          and next((x['runner'] for x in rows if x['routine'] == 'box#cron-backup'), '').startswith('its register: ')
          and next((x['runner'] for x in rows if x['routine'] == 'server-u#restart-each-week'), '') == 'nobody', rows)
    check("list: its interlocks are the walk's needs a reading meets, its proof the server's own",
          [i['need'] for i in a.get('interlocks', [])] == ['no-sessions', 'no-open-files']
          and [p['need'] for p in a.get('proof', [])] == ['services-up'], a)

    # ---- the moments, read by bin/stale.py in the garden, by the law it runs
    probe = r"""import sys, json, datetime; sys.path.insert(0, 'bin'); import stale, cal
def ms(t): return cal.moment(t).ms - cal.UNIX_DAY * cal.DAY_MS
def loc(x, h): return (datetime.datetime.fromtimestamp(x / 1000, datetime.timezone(datetime.timedelta(hours=h)))).strftime('%Y-%m-%d %H:%M')
five = stale.moments('2026-10-11 00:00', {'of': 'time', 'every': {'count': '5', 'unit': 'min'}}, ms('2026-10-11 09:12+03:00'), ms('2026-10-11 09:30+03:00'), zone='Europe/Istanbul')
hourly = stale.moments('2026-10-01 00:15', {'of': 'time', 'every': {'count': '1', 'unit': 'h'}}, ms('2026-10-11 09:12+03:00'), ms('2026-10-11 12:00+03:00'), zone='Europe/Istanbul')
berlin = stale.moments('2026-10-20 02:30', {'of': 'time', 'in': 'gregorian-civil', 'each': 'day'}, ms('2026-10-24 00:00Z'), ms('2026-10-27 00:00Z'), zone='Europe/Berlin')
print(json.dumps({'five': [loc(b, 3) for b, e in five], 'hourly': [loc(b, 3) for b, e in hourly], 'berlin': [loc(b, 0) for b, e in berlin]}))
"""
    r = grow.run(PY, '-c', probe, cwd=G)
    mo = json.loads(r.stdout) if r.returncode == 0 else {}
    check("moments: every five minutes, and hourly at a quarter past — strides of instants",
          mo.get('five') == ['2026-10-11 09:15', '2026-10-11 09:20', '2026-10-11 09:25']
          and mo.get('hourly') == ['2026-10-11 09:15', '2026-10-11 10:15', '2026-10-11 11:15'], r.out[-800:])
    check("moments: a routine kept at 02:30 is at 02:30 on both sides of a change of the clocks",
          mo.get('berlin') == ['2026-10-24 00:30', '2026-10-25 00:30', '2026-10-26 01:30'], r.out[-800:])

    # ---- due
    rf = readings(os.path.join(T, 'r-busy.json'), sessions='2')
    r = rt('due', '--at', '2026-10-18 05:50+03:00', '--readings', rf, '--json')
    d = {x['routine']: x for x in json.loads(r.stdout)} if r.returncode == 0 else {}
    check("due: inside its window with someone signed in, it waits — which interlock, and the value read",
          d.get('server-a#restart-each-week', {}).get('state') == 'waits'
          and 'server-sessions = 2' in d.get('server-a#restart-each-week', {}).get('why', ''), r.out[-1200:])
    rf0 = readings(os.path.join(T, 'r-quiet.json'))
    r = rt('due', '--at', '2026-10-18 05:50+03:00', '--readings', rf0, '--json')
    d = {x['routine']: x for x in json.loads(r.stdout)} if r.returncode == 0 else {}
    check("due: with nobody signed in and nothing open it is due; a routine of cron's is not this engine's",
          d.get('server-a#restart-each-week', {}).get('state') == 'due'
          and d.get('box#cron-backup', {}).get('state') == "not this engine's", r.out[-1200:])
    r = rt('due', '--at', '2026-10-18 06:20+03:00', '--readings', rf0, '--json')
    d = {x['routine']: x for x in json.loads(r.stdout)} if r.returncode == 0 else {}
    check("due: after its window closes it is not due, and its next occurrence is said",
          d.get('server-a#restart-each-week', {}).get('state') == 'not due'
          and d.get('server-a#restart-each-week', {}).get('next') == '2026-10-25 05:45+03:00', r.out[-1200:])

    # ---- the advance notice: the clause's `notice`, 36 hours before
    r = rt('tick', '--at', '2026-10-16 17:45+03:00', '--json')
    sa = text(G, 'beans/server-a.md')
    check("tick: 36 hours before its run (the clause's `notice`), the walk's tool tells the server's people, naming the "
          "run's own day — recorded as the machine's `produce` of its words; nothing else is done",
          lv('notice') == 'server-a restart-each-week-20261018-0545' and '- produce: { id: restart-each-week-20261018-0545-notice' in sa
          and 'falls on 20261018' in sa and 'id: restart-each-week-20261018-0545,' not in sa, r.out[-1200:] + sa[-800:])
    r = rt('tick', '--at', '2026-10-16 17:45+03:00', '--json')
    check("tick: told once — the same minute again tells nobody twice", '"noticed"' not in r.out, r.out[-600:])

    # ---- the engine: waits, then runs
    live(sessions=2, open_files=0, services_down=0, after_down=0)
    r = rt('tick', '--at', '2026-10-18 05:46+03:00', '--json')
    course = 'restart-each-week-20261018-0545'
    sa = text(G, 'beans/server-a.md')
    check("tick: at its occurrence, someone signed in — the run is placed and waits at the walk's pause, citing "
          "interlock-held; nothing applied", r.returncode == 0 and f'id: {course}' in sa and 'as: interlock-held' in sa
          and lv('restarts') == '0', r.out[-1500:] + sa[-1500:])
    ld = grow.run(PY, 'bin/leads.py', '--json', cwd=G)
    leads = json.loads(ld.stdout) if ld.returncode == 0 else []
    check("leads: a run waiting on its interlock is a lead for the server's keeper (`answer … as: keeping`)",
          any(x['kind'] == 'case' and x['about'] == 'server-a' and x.get('step') == 'waits' and x['for'] == 'p-1a2b3c4d'
              for x in leads), ld.out[-800:])
    r = rt('tick', '--at', '2026-10-18 05:47+03:00', '--json')
    check("tick: still signed in — it waits on, and nothing is written", r.returncode == 0 and lv('restarts') == '0'
          and '"resumed"' not in r.out, r.out[-800:])
    live(sessions=0)
    r = rt('tick', '--at', '2026-10-18 05:52+03:00', '--json')
    st = grow.run(PY, 'bin/seq.py', 'course', 'server-a', cwd=G).out
    check("tick: nobody signed in — the run returns from its pause, applies and verifies to done: the server restarted",
          r.returncode == 0 and lv('restarts') == '1' and f"course {course}" in st and "at 'done'" in st, r.out[-1200:] + st[-800:])

    # ---- a notice its moment passed without: given at the next tick before its run, said to be late
    r = rt('tick', '--at', '2026-10-23 20:00+03:00', '--json')
    sa = text(G, 'beans/server-a.md')
    check("tick: a notice whose moment passed with no tick (the machine down) is given at the next tick before its run, "
          "naming the run's own day, and said to be late", lv('notice') == 'server-a restart-each-week-20261025-0545'
          and '- produce: { id: restart-each-week-20261025-0545-notice' in sa and '05:45+03:00 (late)' in sa, r.out[-1200:] + sa[-800:])

    # ---- skipped when its window closes while waiting
    live(sessions=1)
    rt('tick', '--at', '2026-10-24 05:46+03:00')
    r = rt('tick', '--at', '2026-10-24 06:16+03:00', '--json')
    sb = text(G, 'beans/server-b.md')
    check("tick: a run still waiting when its window closes is skipped, citing window-passed; nothing applied",
          'as: window-passed' in sb and lv('restarts') == '1', r.out[-1200:] + sb[-1200:])

    # ---- a proof that fails
    live(sessions=0, after_down=2)
    r = rt('tick', '--at', '2026-10-26 05:46+03:00', '--json')
    sc = text(G, 'beans/server-c.md')
    check("tick: a run whose proof fails — a service down after the restart — is rolled back (verify-mismatch), its "
          "tool's restore run", 'as: verify-mismatch' in sc and lv('restored') == '1', r.out[-1200:] + sc[-1500:])
    check("...and its crossing is written: the measure that showed it and a fail through it",
          '- measure: { id: services-up-' in sc and '- fail: { id: services-up-' in sc and 'through: services-up-' in sc, sc[-1500:])
    ld = grow.run(PY, 'bin/leads.py', '--json', cwd=G)
    leads = json.loads(ld.stdout) if ld.returncode == 0 else []
    check("leads: the failed proof is a health lead", any(x['kind'] == 'health' and x['about'] == 'server-c' for x in leads),
          ld.out[-800:])
    r = rt('tick', '--at', '2026-11-02 05:46+03:00', '--json')
    sc = text(G, 'beans/server-c.md')
    check("tick: the next run whose proof fails while its fail is still open is rolled back too, and writes no second "
          "fail: a crossing is the need ceasing to hold, once", sc.count('as: verify-mismatch') == 2 and lv('restored') == '2'
          and sc.count('- fail: { id: services-up-') == 1, r.out[-1200:] + sc[-1500:])

    # ---- crossings
    live(services_down=0)
    r = rt('cross', '--json')
    sc = text(G, 'beans/server-c.md')
    check("cross: the need holding again writes its repair", r.returncode == 0 and '- repair: { id: services-up-' in sc,
          r.out[-800:] + sc[-800:])
    live(services_down=3, down_detail='spooler stopped since 05:40|w32time stopped ' + 'x' * 900)
    r1 = rt('cross', '--json')
    r2 = rt('cross', '--json')
    sa = text(G, 'beans/server-a.md')
    check("cross: a need that stops holding writes its measure and its fail once, never each sample",
          sa.count('- fail: { id: services-up-') == 1 and '"need": "services-up"' in r1.out and '"need"' not in r2.out,
          r1.out[-600:] + r2.out[-600:])
    note = next((ln for ln in sa.splitlines() if '- measure: { id: services-up-' in ln and 'services-down' in ln), '')
    check("cross: what the reading saw in words (its `detail`) is kept in the measure's note — one line, bounded — so the "
          "lead says what crossed, not only how many",
          'spooler stopped since 05:40 w32time stopped xxx' in note and 'x' * 600 not in note and '\\n' not in note,
          note[:400] or sa[-800:])
    live(down_detail='')

    # ---- a crossing proposes its remedy, which waits for its key, then for a person
    live(depot_fill=90, key=0)
    r = rt('cross', '--json')
    dp = text(G, 'beans/depot.md')
    st = grow.run(PY, 'bin/seq.py', 'course', 'depot', cwd=G).out
    check("cross: the depot past its gate writes its crossing, and proposes the walk its repair names — which waits for "
          "the key (its tool's check failing with it out is a wait, not a refusal), nothing kept and nothing dropped", '- fail: { id: below-gate-' in dp and "at 'waits'" in st
          and lv('stashed') == '0' and lv('depot-fill') == '90', r.out[-1200:] + st[-600:])
    live(key=1, pull_key=1)
    r = rt('tick', '--at', '2026-10-28 08:58+03:00', '--json')
    st = grow.run(PY, 'bin/seq.py', 'course', 'depot', cwd=G).out
    dp = text(G, 'beans/depot.md')
    check("tick: the key pulled while the walk keeps what the prune would drop — its step failing with an interlock out — "
          "is a wait again, not a refusal: nothing kept, nothing dropped", "at 'waits'" in st and '#stash"' in dp
          and 'as: stash-failed' not in dp and lv('stashed') == '0' and lv('depot-fill') == '90', r.out[-1200:] + st[-600:])
    live(key=1)
    r = rt('tick', '--at', '2026-10-28 09:00+03:00', '--json')
    st = grow.run(PY, 'bin/seq.py', 'course', 'depot', cwd=G).out
    check("tick: the key in, the proposed run returns from its pause, keeps what the prune would drop (a step of its own), "
          "and stops for a person to ratify", "at 'ratify'" in st and lv('stashed') == '1' and lv('depot-fill') == '90',
          r.out[-1200:] + st[-600:])
    course = next((ln.split('course ')[1].split()[0] for ln in st.splitlines() if 'course remedy-' in ln), '')
    r = grow.run(PY, 'bin/act.py', 'depot', course, '--ratify', 'sam', cwd=G)
    st = grow.run(PY, 'bin/seq.py', 'course', 'depot', cwd=G).out
    check("act: ratified, the prune applies and its proof — the depot below its gate — holds: done", "at 'done'" in st
          and lv('depot-fill') == '40', r.out[-1200:] + st[-600:])
    r = rt('cross', '--json')
    check("cross: the depot below its gate again writes the repair of its crossing",
          '- repair: { id: below-gate-' in text(G, 'beans/depot.md'), r.out[-800:])

    # ---- a crossing the gate refuses leaves the garden as it was
    live(depot_fill=95, depot_property='no-such-property')
    before = text(G, 'beans/depot.md')
    r = rt('cross', '--json')
    st = grow.run('git', 'status', '--porcelain', cwd=G).out
    check("cross: a crossing the gate refuses (a reading of a property the law does not have) is taken back whole — the "
          "garden is left clean, nothing half-written for the next save or a sync to trip on",
          r.returncode != 0 and text(G, 'beans/depot.md') == before and not st.strip(), r.out[-600:] + st)
    live(depot_fill=40, depot_property='ratio')

    # ---- a walk nobody granted
    restarts = lv('restarts')
    r = grow.run(PY, '-c', "import sys; sys.path.insert(0, 'bin'); import act, safe; "
                           "safe.add_statements('beans/server-u.md', '- be: { id: by-hand, by: self, at: routine-unseen, as: order }\\n"
                           "- make: { by: box, of: [by-hand], at: now }\\n'); sys.exit(act.main(['server-u', 'by-hand']))", cwd=G)
    check("act: a walk with no person's step, granted to no machine, is not run — nothing planned, nothing applied",
          r.returncode == 1 and 'named, never assumed' in r.out and lv('restarts') == restarts, r.out[-800:])
    grow.run('git', 'checkout', '--', 'beans/server-u.md', cwd=G)

    # ---- cron
    tab = os.path.join(T, 'crontab')
    live_text = ('# the box\'s jobs\nMAILTO=""\n45 17 * * fri /root/monitoring_scripts/weekly.sh\n'
                 '15 * * * * /root/backup_scripts/hourly.sh\n*/5 * * * * /usr/local/sbin/ban.py\n'
                 '30 3 * * * /usr/local/sbin/spamtrain learn\n0 0 * * * /root/a.sh\n'
                 '30 03 * * * /root/leading-zero.sh\n0 9 1-7 * 1 /root/first-monday.sh\n@reboot /root/start.sh\n'
                 '*  * * * * /root/every-minute.sh\n00 * * * * /root/acc.sh\n45 18 * * * /root/a.sh\n')
    with open(tab, 'w', encoding='utf-8') as fh:
        fh.write(live_text)
    r = rt('adopt', 'cron', tab, '--host', 'box', '--at', '2026-10-11 12:00+03:00', '--json')
    rows = json.loads(r.stdout) if r.stdout.strip().startswith('[') else []
    ok_ = [x for x in rows if not x.get('refused')]
    bad = {x['n']: x['refused'] for x in rows if x.get('refused')}
    check("adopt cron: each job the garden can say is proposed, the crontab rendered from the proposal the live one byte "
          "for byte — `03`, `00` and two spaces kept as spelled", {x["n"] for x in ok_} == {3, 4, 5, 6, 8, 11, 12}
          and {x['n']: x.get('spelled') for x in ok_}.get(8) == '30 03 * * *', r.out[-1500:])
    check("adopt cron: what it cannot say, @reboot, and a command two lines run are refused, each with its line and "
          "why", set(bad) == {7, 9, 10, 13} and 'day of the month' in bad.get(9, '') and 'one command, one line' in bad.get(13, '')
          and 'one command, one line' in bad.get(7, '')
          and r.returncode == 1, bad)
    wk = next((x for x in ok_ if x['n'] == 3), {})
    check("adopt cron: Friday 17:45 becomes each week of iso-week at 5, first on the Friday after the day adopted",
          wk.get('clause', {}).get('due') == '2026-10-16 17:45' and wk['clause']['every'].get('at') == '5', wk)
    r = rt('render', 'cron', '--host', 'box')
    check("render cron: a routine present in the crontab is written as cron runs it",
          r.returncode == 0 and '15 0 * * * /root/backup.sh >/dev/null 2>&1' in r.out, r.out[-600:])
    for name, line, n in (('same', '15 0 * * * /root/backup.sh >/dev/null 2>&1', 0),
                          ('spelled', '15 00 * * *  /root/backup.sh >/dev/null 2>&1', None),
                          ('moved', '30 1 * * * /root/backup.sh >/dev/null 2>&1', 1)):
        with open(os.path.join(T, name), 'w') as fh:
            fh.write('# kept\nMAILTO=""\n' + line + '\n5 5 * * * /root/not-ours.sh\n')
    r0 = rt('render', 'cron', '--host', 'box', '--live', os.path.join(T, 'same'), '--json', '--write', os.path.join(T, 'same.out'))
    j0 = json.loads(r0.stdout) if r0.stdout.strip().startswith('{') else {}
    check("render cron --live: the garden's line live as it says — no change, the file written back byte for byte, a job "
          "no routine runs kept and named", r0.returncode == 0 and j0.get('same') is True
          and text(T, 'same.out') == text(T, 'same') and j0.get('unowned') == ['5 5 * * * /root/not-ours.sh'], r0.out[-600:])
    r2 = rt('render', 'cron', '--host', 'box', '--live', os.path.join(T, 'moved'), '--json')
    j2 = json.loads(r2.stdout) if r2.stdout.strip().startswith('{') else {}
    check("render cron --live: a line at another time than the garden says is written anew, and only it",
          r2.returncode == 1 and j2.get('changes') == ['- 30 1 * * * /root/backup.sh >/dev/null 2>&1\n+ 15 0 * * * /root/backup.sh >/dev/null 2>&1'],
          r2.out[-600:])
    probe = r"""import sys, json; sys.path.insert(0, 'bin'); import routines as R
live = '# kept\n15 00 * * *  /root/backup.sh\n5 5 * * * /root/not-ours.sh\n'
kept, c1 = R.render_crontab(live, {'/root/backup.sh': '15 0 * * *'})
gone, c2 = R.render_crontab(live, {'/root/backup.sh': None})
new, c3 = R.render_crontab(live, {'/root/backup.sh': '15 0 * * *', '/root/new.sh': '0 4 * * *'})
print(json.dumps({'kept': kept == live, 'gone': gone, 'new': new}))"""
    r = grow.run(PY, '-c', probe, cwd=G)
    j = json.loads(r.stdout) if r.returncode == 0 else {}
    check("render_crontab: a meaning-equal line is kept as spelled; a routine moved to the engine leaves cron; a new one "
          "is added at the end; nothing else moves", j.get('kept') is True
          and j.get('gone') == '# kept\n5 5 * * * /root/not-ours.sh\n'
          and j.get('new') == '# kept\n15 00 * * *  /root/backup.sh\n5 5 * * * /root/not-ours.sh\n0 4 * * * /root/new.sh\n',
          r.out[-600:])

    # ---- the readers
    ld = grow.run(PY, 'bin/leads.py', '--json', cwd=G)
    leads = json.loads(ld.stdout) if ld.returncode == 0 else []
    check("leads: a routine's clause is no obligation lead — the machine keeps it, and a person is told on a crossing",
          not any(x['kind'] == 'obligation' for x in leads), [x for x in leads if x['kind'] == 'obligation'])
    s = grow.run(PY, 'bin/stale.py', cwd=G)
    check("stale: a routine's clause is not warned of as expiring", 'restart-each-week-due' not in s.out
          and 'cron-backup-due' not in s.out, s.out[-800:])
    g = grow.run(PY, 'bin/check.py', cwd=G)
    check("the garden passes its gate after every run", g.returncode == 0 and '0 error(s)' in g.out, g.out[-800:])
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    check(f"the suite ran to its end ({type(e).__name__}: {e})", False)
finally:
    if os.environ.get('KEEP'):
        print(f"kept: {T}")
    else:
        shutil.rmtree(T, ignore_errors=True)

print(f"\nroutines: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
