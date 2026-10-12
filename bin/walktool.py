#!/usr/bin/env python3
"""walktool — the tool side of a walk, once. bin/act.py runs a walk's tool as `<tool> <step> <bean> <course>` in the
garden (the tool is the program the walk `use`s, `be`ing on this host); what every such tool reads and writes the same
way is here, read the way the engine reads it, so a tool keeps only what is its own — its plan, check, apply, verify and
restore, its service's model — and names nothing of a garden in its code.

    import walktool as W                       # in a tool: the garden's bin/ on the path, the tool run in the garden
    W.course(bean, course)   -> (walk, steps)   the walk the course is on and its steps by id (bin/act.py's reading)
    W.this_host()            -> host bean id    this machine: the host bean whose hostname anchor names it (bin/where.py)
    W.here(position)         -> path or None    a position (`<host>:<path>`, `root:<name>/…`) as a path on this machine
    W.instances(of, host)    -> [instance id]   the instances `use`ing `of` (a technology's code, or a program), each one
                                                `be`ing at `host` (this host where none is said), as their beans say
    W.shown()                -> path            the plan this apply was given to run (DAFTAR_ACTION_PLAN), or a refusal
    W.save(who, what, body)                     bin/save.py: the change journalled and committed, or the tool stopped
    W.seal(bean, ids)        -> [journal line]  bin/held.py: each statement sealed in this host's store
    W.main(name, steps, more)                   `<step> <bean> <course>` to `steps[step](bean, course)`, `<command> …`
                                                to `more[command](argv)`, anything else the usage; a refusal (Refused)
                                                said as the tool's own, exit 1
A refusal is `raise W.Refused(why)` anywhere in a step: main says it as `<tool>: <why>` and exits 1 (the engine moves
the course to its exit, the reason the tool said), or `W.Refused(why, 2)` where the tool could not run.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)


class Refused(Exception):
    """A step that will not, or cannot, go on: said by main as the tool's own word; `code` 1 (refused) or 2 (could not)."""

    def __init__(self, why, code=1):
        super().__init__(why)
        self.code = code


def _garden():
    import seq as dmseq
    return dmseq.core(ROOT)[1]


def course(bean, course_id):
    """(the walk's bean id, its steps by id) of the course `course_id` placed in `bean` — read as bin/act.py reads it."""
    import act as dmact
    try:
        walk, steps, _path, _host = dmact.walk_of(bean, course_id)
    except dmact.Refused as e:
        raise Refused(str(e))
    return walk, steps


def this_host():
    """This machine's host bean: the one whose hostname anchor names it. A refusal where none does — a step changes a
    thing only on the host the garden says it is on, and an unnamed machine is nobody's."""
    import where as dmwhere
    hid, _hfm, _names = dmwhere.here()
    if not hid:
        raise Refused("this machine has no host bean here (named by its hostname): nobody's to act on", 2)
    return hid


def here(position):
    """`position` (a string: `<host>:<path>`, `root:<name>/…`) as a literal path on this machine, or None where it is on
    another — the engine's own resolver (bin/where.py `on_host`), never a comparison of host names."""
    import where as dmwhere
    _hid, hfm, names = dmwhere.here()
    try:
        path, _obj, _why = dmwhere.on_host(str(position), dmwhere.roots_of(hfm), names)
    except ValueError:
        return None
    return path


def instances(of, host=None):
    """The instances whose bean `use`s `of` (`technology:postfix`, or a program's bean id) and `be`s at `host` (a host
    bean; this host's where none is given), sorted: the beings a tool's statements are `by`, read from the garden."""
    host = host or this_host()
    G = _garden()
    out = []
    for bid, b in G.beans.items():
        if b.header.get('kind') != 'instance':
            continue
        uses = {str(r.get('of')) for _i, v, r in b.items if v == 'use'}
        at = {str(r.get('at')) for _i, v, r in b.items if v == 'be' and r.get('as') == 'habitat'}
        if str(of) in uses and host in at:
            out.append(bid)
    return sorted(out)


def shown():
    """The plan this apply runs — the one the person was shown and ratified, which the engine names in
    DAFTAR_ACTION_PLAN — or a refusal: apply never plans anew."""
    p = os.environ.get('DAFTAR_ACTION_PLAN')
    if not p or not os.path.isfile(p):
        raise Refused("apply runs the plan it was shown: DAFTAR_ACTION_PLAN names none")
    return p


def save(who, what, body):
    """bin/save.py `who` `what` --body `body` (a string, or lines): the change journalled and committed through the
    garden's gate; a refusal, with what the gate said, where it is not."""
    body = body if isinstance(body, str) else '\n'.join(body)
    r = subprocess.run([sys.executable, os.path.join(HERE, 'save.py'), who, what, '--body', body], cwd=ROOT,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode:
        raise Refused(f"the save was refused: {(r.stdout + r.stderr).strip()[-800:]}")
    return r.stdout


def seal(bean, ids):
    """Each statement of `ids` in `bean` sealed in this host's store (bin/held.py `put_core`): [its journal line]."""
    import held as dmheld
    return [dmheld.put_core(bean, sid, root=ROOT)[1] for sid in ids]


def main(name, steps, more=None, argv=None):
    """The tool's command line, as the engine and a person call it. Returns the exit code."""
    a = list(sys.argv[1:] if argv is None else argv)
    more = more or {}
    try:
        if len(a) == 3 and a[0] in steps:
            return steps[a[0]](a[1], a[2]) or 0
        if a[:1] and a[0] in more:
            return more[a[0]](a[1:]) or 0
    except Refused as e:
        print(f"{name}: {e}", file=sys.stderr)
        return e.code
    usage = '|'.join(steps)
    print(f"usage: {name} {{{usage}}} <bean> <course>" + ''.join(f" | {c} …" for c in more), file=sys.stderr)
    return 2
