#!/usr/bin/env python3
"""act — run a ratified action, one step of its walk at a time, recorded by daftar's own sequence machinery.

    python3 bin/act.py <bean> <course>                  # the engine's steps, until a person's step, an end or an exit
    python3 bin/act.py <bean> <course> --ratify <who>   # a person ratifies the plan they were shown
    python3 bin/act.py <bean> <course> --decline <who>  # ...or declines it: the run is refused, nothing changed

AN ACTION IS A WALK, AND A RUN IS A COURSE (MODEL.md; nothing here is a second sequence). The action is a mapping of the
garden's `procedure` kind whose `step`s are its steps; the being it changes is placed on it, `be: { id: <course>, by:
self, at: <walk>, as: order }`, in its own bean; each step reached is a `move` through that course. Where a run stands
is read by bin/seq.py `where`, the one reader. The walk every action shares:

  plan      the engine runs the tool's `plan`: what it would change, changing nothing   → show; or refused, cannot-plan
  show      the plan, captured, is what the person is shown                             → check
  check     the engine runs the tool's `check`                                          → ratify; or refused, check-failed
  ratify    a person (the gardener, or one a `grant … as: ratify` names) — --ratify    → apply; or show, where the plan
            changed since it was shown; --decline                                       → refused, declined
  apply     the engine runs the tool's `apply`                                          → verify; or rolled-back,
                                                                                          apply-failed (`restore` run)
  verify    the engine runs the tool's `verify`, which reads back from the live thing   → done; or rolled-back,
                                                                                          verify-mismatch (`restore` run)
  done (final), refused and rolled-back (exits)

A step whose `by` is `engine` is the engine's; any other is a person's, and the run stops there: a lead to them
(bin/leads.py). THE TOOL is what the walk `use`s: a bean of kind `program`, `be`ing at a position on a host (`<host>:
<path>` or `root:<name>/…`) — run only on that host, as `<tool> <step> <bean> <course>` in the garden, `apply` with
the captured plan's path in DAFTAR_ACTION_PLAN. Each step's output is kept in captures/actions/ (history), and the moves
of one run are saved in one commit with their entry; the engine's moves are this machine's (its host bean's), a
ratification is the person's.
"""
import hashlib
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr
import importlib  # noqa: E402
dmpass = importlib.import_module('pass')  # noqa: E402 — `pass` is a keyword: imported by name
import seq as dmseq  # noqa: E402 — where a course stands
import safe as dmsafe  # noqa: E402 — a statement added, losing nothing
import where as dmwhere  # noqa: E402 — this host, and what a position means on it

ENGINE = 'engine'
NEXT = {'plan': 'show', 'show': 'check', 'check': 'ratify', 'apply': 'verify', 'verify': 'done'}
FAILS = {'plan': ('refused', 'cannot-plan'), 'check': ('refused', 'check-failed'),
         'apply': ('rolled-back', 'apply-failed'), 'verify': ('rolled-back', 'verify-mismatch')}


class Refused(Exception):
    """Why the engine did nothing: said to the person, and nothing written."""


def listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def walk_of(bean, course):
    """(walk id, its steps by id, the tool's path on this host) of a course."""
    _law, G = dmseq.core(ROOT)
    b = G.beans.get(bean)
    if b is None:
        raise Refused(f"no bean {bean!r} here")
    placed = next((r for _i, v, r in b.items if v == 'be' and r.get('id') == course and r.get('as') == 'order'), None)
    if not placed:
        raise Refused(f"{bean} has no course {course!r} (a `be` of it, as order, on a walk)")
    wid = str(placed.get('at'))
    w = G.beans.get(wid)
    if w is None:
        raise Refused(f"{course}'s walk {wid!r} is no bean of this garden")
    steps = {str(r.get('id')): r for _i, v, r in w.items if v == 'step' and r.get('id')}
    tools = [str(r.get('of')) for _i, v, r in w.items if v == 'use' and isinstance(r.get('of'), str)]
    path = None
    hid, hfm, names = dmwhere.here()
    for t in tools:
        tb = G.beans.get(t)
        for _i, v, r in (tb.items if tb else []):
            if v == 'be' and r.get('as') == 'location' and isinstance(r.get('at'), str):
                try:
                    got, _obj, _why = dmwhere.on_host(r['at'], dmwhere.roots_of(hfm), names)
                except ValueError:
                    got = None
                if got:
                    path = got
    return wid, steps, path, hid


def run_tool(path, step, bean, course, env=None):
    """(exit code, what it printed) of the tool's `step`."""
    r = subprocess.run([sys.executable, path, step, bean, course] if path.endswith('.py') else [path, step, bean, course],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=3600,
                       env=dict(os.environ, **(env or {})))
    return r.returncode, r.stdout + r.stderr


def capture(bean, course, step, text):
    """Keep a step's output in history; its path, relative to the garden, and its SHA-256."""
    d = os.path.join(ROOT, 'captures', 'actions')
    os.makedirs(d, exist_ok=True)
    n = len([f for f in os.listdir(d) if f.startswith(f"{bean}.{course}.{step}.")]) + 1
    rel = f"captures/actions/{bean}.{course}.{step}.{n}.txt"
    with open(os.path.join(ROOT, rel), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)
    return rel, hashlib.sha256(text.encode('utf-8')).hexdigest()


def moves_so_far(bean, course):
    _law, G = dmseq.core(ROOT)
    b = G.beans[bean]
    return [r for _i, v, r in b.items if v == 'move' and r.get('through') == course]


def save(who, what, lines):
    body = '\n'.join(lines)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'save.py'), who, what, '--body', body], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise Refused(f"the save was refused: {(r.stdout + r.stderr).strip()[-800:]}")


def add_moves(bean, wid, course, moves, knower, act):
    """Write the run's moves in the bean, with the act that knows them: [(step, by, reason or None, note)]."""
    path = os.path.join(ROOT, 'beans', bean + '.md')
    n = len(moves_so_far(bean, course))
    block, ids = '', []
    for step, by, reason, note in moves:
        n += 1
        mid = f"{course}-{n}"
        ids.append(mid)
        block += (f'- move: {{ id: {mid}, by: {by}, of: self, through: {course}, at: [now, "{wid}#{step}"]'
                  + (f', as: {reason}' if reason else '') + (f', note: "{note}"' if note else '') + ' }\n')
    block += f'- {act}: {{ by: {knower}, of: [{", ".join(ids)}], at: now }}\n'
    dmsafe.add_statements(path, block)
    return ids


def where_now(bean, course):
    w = dmseq.where(ROOT, bean, course)
    return w.get('step'), w


RUNS = ('plan', 'check', 'apply', 'verify')
ENDS = ('done', 'refused', 'rolled-back')


def fresh():
    """Read the garden again: a save made this run is part of what the next reading reads."""
    dmseq._CORE.clear()


def engine(bean, course, arrived=False, before=None):
    """Run the engine's steps from where the course stands, until a person's step, an end or an exit: (where it stopped,
    why). A move is the course arriving at a step; an engine's step's tool runs on arrival. `arrived`: the course was
    just moved into its step by a person (apply, after a ratification), whose tool runs now; `before`, (who, the
    entry's lines) of that person's act, written already and saved in the same commit as the engine's."""
    fresh()
    wid, steps, tool, hid = walk_of(bean, course)
    if hid is None:
        raise Refused("this machine has no bean in the garden (a host named by its hostname): its acts are nobody's")
    by = lambda step: str((steps.get(step) or {}).get('by') or '')
    at, _w = where_now(bean, course)
    moves, lines = [], []

    def go(step, reason=None, note=None):
        if step not in steps:
            raise Refused(f"the walk {wid} has no step {step!r}: an action's walk takes plan, show, check, ratify, apply, "
                          f"verify, done, refused and rolled-back")
        moves.append([step, hid, reason, note])
        return step
    if at is None:
        at, arrived = go('plan'), True
    while at not in ENDS and by(at) == ENGINE:
        if arrived and at in RUNS:
            if not tool:
                raise Refused(f"the walk {wid} uses no tool this machine holds (a program bean `be`ing here)")
            env = {}
            if at == 'apply':
                plans = sorted(f for f in os.listdir(os.path.join(ROOT, 'captures', 'actions'))
                               if f.startswith(f"{bean}.{course}.plan.")) if os.path.isdir(
                    os.path.join(ROOT, 'captures', 'actions')) else []
                if plans:
                    env['DAFTAR_ACTION_PLAN'] = os.path.join(ROOT, 'captures', 'actions', plans[-1])
            code, out = run_tool(tool, at, bean, course, env)
            rel, sha = capture(bean, course, at, out)
            lines.append(f"- {at}: {'passed' if code == 0 else f'failed (exit {code})'} — {rel} (sha-256 {sha[:16]})")
            if at == 'plan' and moves:
                moves[-1][3] = f"sha-256 {sha}"           # what the person is shown, and ratifies
            if code != 0:
                ex, reason = FAILS[at]
                if ex == 'rolled-back':
                    rc, rout = run_tool(tool, 'restore', bean, course)
                    rrel, _ = capture(bean, course, 'restore', rout)
                    lines.append(f"- restore: {'passed' if rc == 0 else f'FAILED (exit {rc})'} — {rrel}")
                at = go(ex, reason)
                break
        nxt = NEXT.get(at)
        if nxt is None:
            break
        at, arrived = go(nxt), True
    if not moves and not before:
        return at, f"nothing for the engine to do: the course is at {at}"
    if moves:
        add_moves(bean, wid, course, [tuple(m) for m in moves], hid, 'make')
    who, said = before or (hid, [])
    save(who, f"{bean} {course}: " + ('ratified' + (', then ' if moves else '') if before else '')
         + ', '.join(m[0] for m in moves), said + (
        [f"- action: the engine moved [[{bean}]]'s course {course} on [[{wid}]]: "
         + ' → '.join(m[0] + (f" ({m[2]})" if m[2] else '') for m in moves)] if moves else []) + lines)
    return at, f"stopped at {at}" + (" — a person's step: a lead to them" if at not in ENDS else '')


def ratify(bean, course, who, decline=False):
    """A person's ratification of the plan they were shown — or their refusal of it."""
    fresh()
    wid, steps, tool, _hid = walk_of(bean, course)
    step, _w = where_now(bean, course)
    if step != 'ratify':
        raise Refused(f"{bean}'s course {course} is at {step!r}, not waiting to be ratified")
    gardener = dmpass.gardener_of(ROOT)
    _law, G = dmseq.core(ROOT)
    may = {gardener} | {str(x) for b in G.beans.values() for _i, v, r in b.items
                        if v == 'grant' and r.get('as') == 'ratify' and 'held' not in r for x in listed(r.get('to'))}
    if who not in may:
        raise Refused(f"{who} may not ratify it: the gardener, or one a `grant … as: ratify` names")
    if decline:
        add_moves(bean, wid, course, [('refused', who, 'declined', None)], who, 'say')
        save(who, f"{bean} {course}: declined", [f"- decision: {who} declined [[{bean}]]'s course {course} on "
                                                 f"[[{wid}]]; nothing was changed"])
        return 'refused', 'declined: nothing was changed'
    shown = None
    for m in moves_so_far(bean, course):
        got = re.search(r'sha-256 ([0-9a-f]{64})', str(m.get('note') or ''))
        if got:
            shown = got.group(1)
    if tool:
        code, out = run_tool(tool, 'plan', bean, course)
        if code != 0 or hashlib.sha256(out.encode('utf-8')).hexdigest() != shown:
            rel, sha = capture(bean, course, 'plan', out)
            add_moves(bean, wid, course, [('show', who, None, f"sha-256 {sha}")], who, 'say')
            at, _ = engine(bean, course, before=(who, [f"- action: [[{bean}]]'s plan changed since {who} was shown it "
                                                        f"({rel}): back to show, to be ratified again"]))
            return at, 'the plan changed since it was shown: shown again'
    add_moves(bean, wid, course, [('apply', who, None, None)], who, 'say')
    return engine(bean, course, arrived=True, before=(who, [
        f"- ratified_by: {who}, the plan shown (sha-256 {shown or 'unread'})",
        f"- action: {who} ratified [[{bean}]]'s course {course} on [[{wid}]]"]))


def main(argv):
    if len(argv) < 2 or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv[:1] in (['-h'], ['--help']) else 2
    bean, course = argv[0], argv[1]
    try:
        if '--ratify' in argv or '--decline' in argv:
            flag = '--ratify' if '--ratify' in argv else '--decline'
            i = argv.index(flag)
            if i + 1 >= len(argv):
                raise Refused(f"{flag} names who")
            at, why = ratify(bean, course, argv[i + 1], decline=flag == '--decline')
        else:
            at, why = engine(bean, course)
    except Refused as e:
        print(f"act: NOT RUN: {e}", file=sys.stderr)
        return 1
    print(f"act: {bean} {course}: {why}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
