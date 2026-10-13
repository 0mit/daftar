#!/usr/bin/env python3
"""act — run a ratified action, one step of its walk at a time, recorded by daftar's own sequence machinery.

    python3 bin/act.py <bean> <course>                  # the engine's steps, until a person's step, an end or an exit
    python3 bin/act.py <bean> <course> --ratify <who>   # a person ratifies the plan they were shown
    python3 bin/act.py <bean> <course> --decline <who>  # ...or declines it: the run is refused, nothing changed
    python3 bin/act.py <bean> --start <walk> --by <who> [--input <name>=<value>]...
                                                        # a run started, with what a person gave it: its course placed
                                                        # in the bean, its inputs kept, the engine run to its plan

A RUN STARTED, WITH ITS INPUTS (a page's action, or a person at the terminal): `--start` asks the law whether `who` may
act on the bean by the walk (`may … act:<walk>`: the gardener, or an `enact` grant of the bean), places a course of the
walk in the bean (`be: { id: run-<n>, by: self, at: <walk>, as: order }`, known by `who`'s `say`), keeps the inputs it
was given as the run's first capture (`captures/actions/<bean>.<course>.inputs.1.txt`, JSON: each name, its words), and
runs the engine from `plan`, all of it saved in the engine's one commit. Every step of its tool is given that capture in DAFTAR_ACTION_INPUTS
(bin/walktool.py `inputs`), as `apply` is given the plan it was shown.

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

A step whose `by` is `engine` is the engine's, and on arriving at it the engine runs the tool's verb of the same name
(all but `show`, which is the plan, captured); any other is a person's, and the run stops there: a lead to them
(bin/leads.py). THE TOOL is what the walk `use`s: a bean of kind `program`, `be`ing at a position on a host (`<host>:
<path>` or `root:<name>/…`) — run only on that host, as `<tool> <step> <bean> <course>` in the garden, `apply` with
the captured plan's path in DAFTAR_ACTION_PLAN (bin/walktool.py is that side of it, once: a tool written on it reads
its walk, this host, a position here and the plan it was shown as the engine reads them, and says a refusal as its
own). Each step's output is kept in captures/actions/ (history), and the moves
of one run are saved in one commit with their entry; the engine's moves are this machine's (its host bean's), a
ratification is the person's.

WHERE A STEP LEADS is its own `to` where the walk states one (the first, for the engine), and the shared order above
where it does not — so a walk may leave out `ratify` (`check` leading to `apply`): such a walk runs with nobody's
ratification, and the engine runs it only where a `grant … as: enact` of the walk to this machine stands, said by the
gardener (an automatic run is named, never assumed; bin/routines.py). WHAT A WALK NEEDS — each `need` of the walk a
`reckon` reading meets, its inputs probe readings — is its INTERLOCKS, read after the tool's `check` and again the moment
before `apply`: one that does not hold moves the course to the walk's pause (`resumes`, reason `interlock-held`) where
the walk has one, else refuses it (`check-failed`) — and so does a step before `apply` whose tool fails while one does
not hold (the key out at the check, or pulled while a copy runs); `bin/routines.py tick` reads them again and returns
it. WHAT THE
BEING NEEDS — the needs of the bean the course is in, read the same way — is the run's PROOF, read after the tool's
`verify`: one that does not hold rolls the run back (`verify-mismatch`, `restore` run), and its crossing is written
beside the moves: the `measure` that showed it and a `fail` through it (bin/leads.py: a health lead for the keeper).
Readings are those DAFTAR_READINGS names (files of probe readings, as `probe --json` prints them), else each tool's
`probe`, read now.
"""
import hashlib
import json
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
IN_PROGRESS = 75            # a tool's step not finished yet (EX_TEMPFAIL): the walk pauses, and the next tick runs it again
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


def inputs_of(bean, course):
    """The path of the inputs a run was started with (its `inputs` capture), or None."""
    d = os.path.join(ROOT, 'captures', 'actions')
    got = sorted(f for f in os.listdir(d) if f.startswith(f"{bean}.{course}.inputs.")) if os.path.isdir(d) else []
    return os.path.join(d, got[-1]) if got else None


def run_tool(path, step, bean, course, env=None):
    """(exit code, what it printed) of the tool's `step` — given the run's inputs where it was started with some."""
    given = inputs_of(bean, course)
    env = dict(env or {}, **({'DAFTAR_ACTION_INPUTS': given} if given else {}))
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
    """bin/save.py `who` `what` --body (the lines, or one string): what it said, or a refusal with what the gate said.
    A walk's tool saves through it too (bin/walktool.py)."""
    body = lines if isinstance(lines, str) else '\n'.join(lines)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'save.py'), who, what, '--body', body], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise Refused(f"the save was refused: {(r.stdout + r.stderr).strip()[-800:]}")
    return r.stdout


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
                  + (f', as: {reason}' if reason else '') + (f', note: {json.dumps(note, ensure_ascii=False)}' if note else '') + ' }\n')
    block += f'- {act}: {{ by: {knower}, of: [{", ".join(ids)}], at: now }}\n'
    dmsafe.add_statements(path, block)
    return ids


def where_now(bean, course):
    w = dmseq.where(ROOT, bean, course)
    return w.get('step'), w


ENDS = ('done', 'refused', 'rolled-back', 'skipped')


def fail_of(steps, step):
    """Where a failing engine step leads: the shared exits for plan, check, apply and verify; any other step of the walk
    (a copy made before the person ratifies) is refused, citing `<step>-failed` where its walk lists that reason."""
    if step in FAILS:
        return FAILS[step]
    rs = listed(((steps.get('refused') or {}).get('walk') or {}).get('reasons'))
    return 'refused', f"{step}-failed" if f"{step}-failed" in rs else 'check-failed'


def leads_to(steps, step):
    """Where the engine goes from a step: the walk's own first `to`, else the shared order (NEXT)."""
    to = listed((steps.get(step) or {}).get('to'))
    return str(to[0]) if to else NEXT.get(step)


def pause_of(steps, reason):
    """The walk's pause (`resumes`) a move may enter citing `reason`, or None."""
    for sid, s in steps.items():
        w = s.get('walk') if isinstance(s.get('walk'), dict) else {}
        if str(w.get('resumes')) == 'true' and reason in listed(w.get('reasons')):
            return sid
    return None


def automatic(steps):
    """True where no step of the walk is a person's: it would run from plan to its end with nobody's ratification."""
    for s in steps.values():
        w = s.get('walk') if isinstance(s.get('walk'), dict) else {}
        if s.get('by') not in (None, ENGINE) and not any(str(w.get(k)) == 'true' for k in ('exit', 'final', 'resumes')):
            return False
    return True


def readings_here(G):
    """The readings a walk's needs are read against: the files DAFTAR_READINGS names, else each tool's probe, now."""
    import routines as dmroutines
    paths = [p for p in os.environ.get('DAFTAR_READINGS', '').split(os.pathsep) if p]
    return dmroutines.Readings(G, dmroutines.load_readings(paths))


def fresh():
    """Read the garden again: a save made this run is part of what the next reading reads."""
    dmseq._CORE.clear()


def engine(bean, course, arrived=False, before=None, readings=None):
    """Run the engine's steps from where the course stands, until a person's step, an end, an exit or a pause: (where it
    stopped, why). A move is the course arriving at a step; an engine's step's tool runs on arrival. `arrived`: the course
    was just moved into its step by a person (apply, after a ratification), or returned from a pause, and its tool runs
    now; `before`, (who, the entry's lines[, the act's word: ratified, started]) of that act, written already and saved
    in the same commit as the engine's."""
    import routines as dmroutines
    fresh()
    wid, steps, tool, hid = walk_of(bean, course)
    if hid is None:
        raise Refused("this machine has no bean in the garden (a host named by its hostname): its acts are nobody's")
    _law, G = dmseq.core(ROOT)
    if automatic(steps) and not dmroutines.granted(G, wid, hid, ROOT):
        raise Refused(f"the walk {wid} has no person's step, so it would run with nobody's ratification, and no `grant … "
                      f"as: enact` of it to this machine ({hid}), said by the gardener, stands: an automatic run is named, "
                      f"never assumed — nothing was run")
    by = lambda step: str((steps.get(step) or {}).get('by') or '')
    at, _w = where_now(bean, course)
    moves, lines, beside = [], [], []
    got, applied = [], None

    def reads():
        if not got:
            got.append(readings or readings_here(G))
        return got[0]

    def held_back():
        got[0] = reads().again()           # read now: what was read at the last step is not what holds now
        ok, failing = dmroutines.interlocks(G, wid, bean, got[0], ROOT)
        return None if ok else '; '.join(f"{f['need']} ({f['of']}): {f['why'] or 'not known'}" for f in failing)

    def go(step, reason=None, note=None):
        if step not in steps:
            raise Refused(f"the walk {wid} has no step {step!r}: an action's walk takes plan, show, check, ratify, apply, "
                          f"verify, done, refused and rolled-back")
        moves.append([step, hid, reason, note])
        return step

    def wait(why):
        """An interlock that does not hold: the walk's pause where it has one — never forced — else refused."""
        lines.append(f"- interlock: {why} — nothing applied")
        p = pause_of(steps, 'interlock-held')
        return go(p, 'interlock-held', why[:300]) if p else go('refused', 'check-failed', why[:300])
    if at is None:
        at, arrived = go('plan'), True
    while at not in ENDS and by(at) == ENGINE:
        if arrived and at != 'show':          # an engine's step runs its tool's verb; `show` is the plan, captured
            if not tool:
                raise Refused(f"the walk {wid} uses no tool this machine holds (a program bean `be`ing here)")
            if at == 'apply':
                why = held_back()        # read again the moment before anything changes
                if why:
                    at = wait(why)
                    break
            env = {}
            if at == 'apply':
                plans = sorted(f for f in os.listdir(os.path.join(ROOT, 'captures', 'actions'))
                               if f.startswith(f"{bean}.{course}.plan.")) if os.path.isdir(
                    os.path.join(ROOT, 'captures', 'actions')) else []
                if plans:
                    env['DAFTAR_ACTION_PLAN'] = os.path.join(ROOT, 'captures', 'actions', plans[-1])
            code, out = run_tool(tool, at, bean, course, env)
            if at == 'apply':
                applied = dmroutines.now_ms()
            rel, sha = capture(bean, course, at, out)
            lines.append(f"- {at}: {'passed' if code == 0 else f'failed (exit {code})'} — {rel} (sha-256 {sha[:16]})")
            if at == 'plan' and moves:
                moves[-1][3] = f"sha-256 {sha}"           # what the person is shown, and ratifies
            if code == IN_PROGRESS and pause_of(steps, 'in-progress'):
                # A STEP NOT FINISHED (a copy of hours, in slices): the walk's pause, and the next tick runs it again
                at = go(pause_of(steps, 'in-progress'), 'in-progress', 'the step is under way: run again')
                break
            if code == 0 and at == 'check':
                why = held_back()
                if why:
                    at = wait(why)
                    break
            if code != 0 and at not in ('apply', 'verify'):
                why = held_back()           # a step that fails before anything changed while an interlock does not hold (a
                if why and pause_of(steps, 'interlock-held'):   # check with the key out, a copy with the key pulled): a wait
                    at = wait(why)
                    break
            failing = []
            if at == 'verify':         # the proof is read whether or not the tool's own read-back passed: its crossings say why
                after = reads().again(after=applied if applied else dmroutines.now_ms())   # read back, after the apply
                ok, failing = dmroutines.proof(G, bean, after, ROOT)
                rows = dmroutines.read_needs(G, bean, bean, after, ROOT)
                stamp = dmroutines.at_now()
                for row in rows:            # a crossing of each need the run left failing (once); a repair of each it mended
                    was_open = bool(dmroutines.open_fails(G.beans[bean], row['need']))
                    if row['inputs'] and row['holds'] is not None and (row['holds'] is False) != was_open:
                        block, _ids = dmroutines.crossing_block(G, bean, row, hid, stamp, row['holds'] is True)
                        beside += block
                if not ok:
                    lines.append("- proof: " + '; '.join(f"{f['need']} ({f['of']}): {f['why'] or 'not known'}" for f in failing))
            if code != 0 or failing:
                ex, reason = fail_of(steps, at)
                if ex == 'rolled-back':
                    rc, rout = run_tool(tool, 'restore', bean, course)
                    rrel, _ = capture(bean, course, 'restore', rout)
                    lines.append(f"- restore: {'passed' if rc == 0 else f'FAILED (exit {rc})'} — {rrel}")
                at = go(ex, reason)
                break
        nxt = leads_to(steps, at)
        if nxt is None:
            break
        at, arrived = go(nxt), True
    if not moves and not before:
        return at, f"nothing for the engine to do: the course is at {at}"
    if moves:
        add_moves(bean, wid, course, [tuple(m) for m in moves], hid, 'make')
    if beside:
        dmsafe.add_statements(os.path.join(ROOT, 'beans', bean + '.md'), '\n'.join(beside) + '\n')
    who, said = (before or (hid, []))[:2]
    word = before[2] if before and len(before) > 2 else 'ratified'       # the person's act: a ratification, or a start
    save(who, f"{bean} {course}: " + (word + (', then ' if moves else '') if before and before[0] != hid else '')
         + ', '.join(m[0] for m in moves), said + (
        [f"- action: the engine moved [[{bean}]]'s course {course} on [[{wid}]]: "
         + ' → '.join(m[0] + (f" ({m[2]})" if m[2] else '') for m in moves)] if moves else []) + lines)
    stood = steps.get(at) or {}
    kind = (" — a pause: read again on the next tick" if str((stood.get('walk') or {}).get('resumes')) == 'true'
            else " — a person's step: a lead to them" if at not in ENDS and by(at) not in ('', ENGINE) else '')
    return at, f"stopped at {at}" + kind


def step_of(move):
    """The step a move reached: the `<walk>#<step>` among its `at`."""
    return next((str(x).split('#', 1)[1] for x in listed(move.get('at')) if '#' in str(x)), None)


def move(bean, course, step, reason, who, note=None):
    """One move of a course, by `who` (this machine), saved with its entry: a run skipped when its window closed."""
    fresh()
    wid, steps, _tool, _hid = walk_of(bean, course)
    if step not in steps:
        raise Refused(f"the walk {wid} has no step {step!r}")
    add_moves(bean, wid, course, [(step, who, reason, note)], who, 'make')
    save(who, f"{bean} {course}: {step}", [f"- action: the engine moved [[{bean}]]'s course {course} on [[{wid}]] to "
                                           f"{step} ({reason})" + (f": {note}" if note else '')])
    return step


def resume(bean, course, readings=None):
    """A course at a pause, returned to the step it was entered from, and the engine run from there (its tool again)."""
    fresh()
    wid, steps, _tool, hid = walk_of(bean, course)
    so_far = moves_so_far(bean, course)
    seq = [step_of(m) for m in so_far]
    if not seq or str(((steps.get(seq[-1]) or {}).get('walk') or {}).get('resumes')) != 'true':
        raise Refused(f"{bean}'s course {course} is at {seq[-1] if seq else 'no step'}, not at a pause")
    back = next((s for s in reversed(seq) if str(((steps.get(s) or {}).get('walk') or {}).get('resumes')) != 'true'), None)
    if back is None:
        raise Refused(f"{bean}'s course {course} entered its pause from no step")
    why = 'its step was under way: run again' if so_far[-1].get('as') == 'in-progress' else 'its interlocks hold again'
    add_moves(bean, wid, course, [(back, hid, None, why)], hid, 'make')
    return engine(bean, course, arrived=True, readings=readings,
                  before=(hid, [f"- action: [[{bean}]]'s course {course} on [[{wid}]] returned from its pause to {back}: "
                                f"{why}"]))


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


_NAME = re.compile(r'^[a-z][a-z0-9-]{0,63}$')
_CTRL = re.compile('[\x00-\x1f\x7f-\x9f\u2028\u2029]')


def start(bean, walk, who, given):
    """A run of `walk` on `bean` started by `who` with `given` ({name: words}): (where the engine stopped, why, course).
    Refused, writing nothing, where the law does not open it to them, or the walk is no action's."""
    fresh()
    _law, G = dmseq.core(ROOT)
    b, w = G.beans.get(bean), G.beans.get(walk)
    if b is None:
        raise Refused(f"no bean {bean!r} here")
    if w is None or not any(v == 'step' and r.get('id') == 'plan' for _i, v, r in w.items):
        raise Refused(f"{walk!r} is no walk of an action here (a `procedure` whose steps begin at `plan`)")
    if not _NAME.match(str(who or '')):
        raise Refused("--by names who starts it: the id of their bean")
    for name, words in given.items():
        if not _NAME.match(name) or not isinstance(words, str) or _CTRL.search(words) or len(words) > 2000:
            raise Refused(f"an input is a name (one kebab word) and one line of words: {name!r}")
    ans = dmpass.may(who, f"act:{walk}", bean, root=ROOT)
    if not ans.granted:
        raise Refused(f"{who} may not act on {bean} by {walk}: {ans.why}")
    ids = {r.get('id') for _i, _v, r in b.items if isinstance(r.get('id'), str)}
    n = 1
    while f"run-{n}" in ids:
        n += 1
    course = f"run-{n}"
    rel, sha = capture(bean, course, 'inputs', json.dumps(given, ensure_ascii=False, sort_keys=True, indent=1) + '\n')
    dmsafe.add_statements(os.path.join(ROOT, 'beans', bean + '.md'),
                          f"- be: {{ id: {course}, by: self, at: {walk}, as: order }}\n"
                          f"- say: {{ by: {who}, of: [{course}], at: now }}\n")
    at, why = engine(bean, course, before=(who, [
        f"- action: [[{who}]] started [[{walk}]] on [[{bean}]] (its course {course})",
        f"- inputs: {', '.join(sorted(given)) or 'none'} — {rel} (sha-256 {sha[:16]})"], 'started'))
    return at, why, course


def main(argv):
    if len(argv) < 2 or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv[:1] in (['-h'], ['--help']) else 2
    if argv[1] == '--start':
        try:
            if len(argv) < 3 or '--by' not in argv or argv.index('--by') + 1 >= len(argv):
                raise Refused("--start <walk> --by <who> [--input <name>=<value>]...")
            given = {}
            for i, a in enumerate(argv):
                if a == '--input' and i + 1 < len(argv) and '=' in argv[i + 1]:
                    k, v = argv[i + 1].split('=', 1)
                    given[k] = v
            at, why, course = start(argv[0], argv[2], argv[argv.index('--by') + 1], given)
        except Refused as e:
            print(f"act: NOT STARTED: {e}", file=sys.stderr)
            return 1
        print(f"act: {argv[0]} {course}: {why}")
        return 0
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
