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
    W.inputs()               -> {name: words}   what the person who started the run gave it (DAFTAR_ACTION_INPUTS):
                                                a page's action's inputs, `--input`s at the terminal; {} where none
    W.save(who, what, body)  -> what it said    bin/act.py's save (bin/save.py): the change journalled and committed,
                                                or the tool stopped
    W.seal(bean, ids)        -> [journal line]  bin/held.py: each statement sealed in this host's store
    W.garden_file(path)      -> path            a file of the garden a write may change whole (`files`, below), or a
                                                refusal
    W.main(name, steps, more)                   `<step> <bean> <course>` to `steps[step](bean, course)`, `<command> …`
                                                to `more[command](argv)`, anything else the usage; a refusal (Refused)
                                                said as the tool's own, exit 1
A refusal is `raise W.Refused(why)` anywhere in a step: main says it as `<tool>: <why>` and exits 1, or 2 with
`W.Refused(why, 2)` where the tool could not run. The engine moves the course to the step's exit (`check-failed`, …)
alike for either, and keeps what the tool said in the step's capture. A step not finished yet (a copy of hours, in
slices) returns `W.IN_PROGRESS`: the walk pauses where its walk says, and the next tick runs the step again.

A PLAN THAT IS A WRITE. Where what a walk changes is the garden itself — statements added to beans, statements taken
out, a bean made or taken out whole — its plan is that write, and the steps are these:
    W.plan_writes(write)      -> the plan's text  print the write in words and, after the line PLAN_MARK, as data: what
                                                  the person is shown and ratifies, byte for byte
    W.apply_writes(bean, course)                  write exactly the plan shown, known by the person who ratified it, in
                                                  ONE save; a save the gate refuses puts back every file it touched
    W.verify_writes(bean, course)                 read it back from the garden as committed, or a refusal
    W.restore_writes(bean, course)                take out what apply added, in a save of its own; what apply took out
                                                  is in git, and only a person restates it
    (verify and restore read the plan the run applied: the one the engine names, else the course's last captured)
`write` is `{what, body, beans: [{bean, add, remove, new, gone, known}]}`: the save's one line and its journal lines;
per bean, the statements to add (`<verb>: { id: …, … }`, one a line, each with an id), the ids to take out, the head
and body of a bean made (`new: {head, body}`) or `gone: true` for one taken out whole, and how what it adds is known
(`known`: `{act: say}`, the default, or `{act: read, from: <a being>, through: <how>}` for what was read from a source).
And `files: [{path, before, after}]`: a file of the garden other than a bean — a scheme's table of the garden's own, a
mapping of a bank's columns — changed whole, its text as the plan read it (`before`; none for a file it makes) and as it
writes it (`after`); refused where the file is none a write changes (`garden_file`) or not as the plan read it, read
back as written, put back as it was on restore.
A statement is taken out only with the knowing acts that name nothing else: an act that also names a statement kept is
refused at the plan — a knowing act is never rewritten, and nobody's word is restated for them.
"""
import difflib
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
for _p in (HERE, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)
import act as dmact  # noqa: E402 — the engine's side of the protocol: walktool reads through it, never beside it

IN_PROGRESS = dmact.IN_PROGRESS     # a step's exit while it is not finished: the engine's own


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


def inputs():
    """What the run was started with — each input a page's action declares, or an `--input` at the terminal, by its
    name: its words (bin/act.py `--start`, captured with the run) — {} for a run started with none."""
    import json
    p = os.environ.get('DAFTAR_ACTION_INPUTS')
    if not p or not os.path.isfile(p):
        return {}
    with open(p, encoding='utf-8') as fh:
        got = json.load(fh)
    return {str(k): [str(x) for x in v] if isinstance(v, list) else str(v) for k, v in got.items()} \
        if isinstance(got, dict) else {}       # an input given several times (`many`) a list of its words


def file(sha):
    """The path of a file a person gave a run (an input of type `file`): kept by the host off git, under its SHA-256, in
    the garden's git directory (`daftar-inputs/<sha-256>`). Refused where none is kept here, or its bytes are not those."""
    import hashlib
    import re as _re
    import subprocess
    if not isinstance(sha, str) or not _re.fullmatch(r'[0-9a-f]{64}', sha):
        raise Refused(f"{sha!r} is no file's SHA-256")
    gd = subprocess.run(['git', 'rev-parse', '--absolute-git-dir'], capture_output=True, text=True, encoding='utf-8').stdout.strip()
    path = os.path.join(gd, 'daftar-inputs', sha)
    if not os.path.isfile(path):
        raise Refused(f"no file {sha[:16]}… is kept on this host for the run")
    with open(path, 'rb') as fh:
        if hashlib.sha256(fh.read()).hexdigest() != sha:
            raise Refused(f"the file kept as {sha[:16]}… is not the one given: its bytes changed")
    return path


def save(who, what, body):
    """bin/save.py `who` `what` --body `body` (a string, or lines), as the engine saves (bin/act.py `save`): the change
    journalled and committed through the garden's gate, and what save said; a refusal, with what the gate said, where
    it is not."""
    try:
        return dmact.save(who, what, body)
    except dmact.Refused as e:
        raise Refused(str(e))


def seal(bean, ids):
    """Each statement of `ids` in `bean` sealed in this host's store (bin/held.py `put_core`): [its journal line]."""
    import held as dmheld
    return [dmheld.put_core(bean, sid, root=ROOT)[1] for sid in ids]


# ----------------------------------------------------------------------------------------------- a plan that is a write
PLAN_MARK = '-- the write, as data --'      # the line after which a plan's text holds its write, one line of JSON
_ID = re.compile(r'^[a-z0-9][a-z0-9-]*$')
_KNOWING = ('say', 'read', 'derive', 'make')


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _statement(line):
    """(verb, roles) of one statement written as a line, `<verb>: { id: …, … }` — or a refusal."""
    import parse as dmparse
    try:
        x = dmparse.loads(line)
    except Exception as e:
        raise Refused(f"`{line[:80]}` is not one statement: {' '.join(str(e).split())[:160]}")
    if not (isinstance(x, dict) and len(x) == 1 and isinstance(next(iter(x.values())), dict)):
        raise Refused(f"`{line[:80]}` is not one statement, `<verb>: {{ … }}`")
    (verb, roles), = x.items()
    if not (isinstance(roles.get('id'), str) and _ID.match(roles['id'])):
        raise Refused(f"`{line[:80]}` names no id: a statement a plan writes has one, which the act knowing it names")
    return str(verb), roles


def _path(G, bid, new=False):
    """The file of the bean `bid`, as the garden reads it, or `beans/<bid>.md` for a bean a plan makes."""
    if not _ID.match(str(bid)):
        raise Refused(f"{bid!r} is no bean's id")
    b = G.beans.get(bid)
    if new:
        p = os.path.join(ROOT, 'beans', f"{bid}.md")
        if b is not None or os.path.exists(p):
            raise Refused(f"the bean {bid} is here already: a plan makes only a bean that is not")
        return p
    if b is None:
        raise Refused(f"no bean {bid!r} here")
    return b.path


def garden_file(rel):
    """The path of `rel`, a file of the garden a write changes whole: one its layer map places in the estate (the law's
    rows, core/law/layers.yaml, or the garden's own) and no release keeps — a scheme's table of the garden's own, a
    mapping of a bank's columns — and no bean, whose statements a write adds and takes out. A refusal for any other: a
    file of the law changes by a RULE-CHANGE, a person's own save; the journal, a capture, git's own are no write's."""
    import importlib
    dmpass = importlib.import_module('pass')
    rel = str(rel or '')
    why = dmpass.unwritten(rel)
    if why:
        raise Refused(f"{rel!r} is no path of a file of the garden: {why}")
    m = dmpass.Map.here(ROOT)
    layer, _placed = m.layer_of(rel)
    if layer != 'estate':
        raise Refused(f"{rel} stands in {'the layer ' + layer if layer else 'no layer'}: a write changes a file of the "
                      f"estate — one of the law changes by a RULE-CHANGE, a person's own save")
    if rel.startswith(dmpass.DOCUMENTS):
        raise Refused(f"{rel} is a bean's file: a write changes a bean by its statements")
    if m.keeper_of(rel) != 'here':
        raise Refused(f"{rel} is a release's: it changes with the release that keeps it")
    path = os.path.join(ROOT, *rel.split('/'))
    real = os.path.realpath(path)
    if os.path.commonpath([real, os.path.realpath(ROOT)]) != os.path.realpath(ROOT):
        raise Refused(f"{rel} leads out of the garden")
    return path


def _text(path):
    if not os.path.isfile(path):
        return None
    with open(path, encoding='utf-8', newline='') as fh:
        return fh.read()


def _taken_acts(b, remove):
    """The knowing acts of bean `b` that go with the statements `remove`: each names only statements taken out. An act
    that names one taken out and one kept is refused: a knowing act is never rewritten, and its word is its knower's."""
    out = []
    for i, v, r in b.items:
        named = set(str(x) for x in _listed(r.get('of'))) if v in _KNOWING else set()
        if named & remove:
            if named - remove:
                raise Refused(f"a `{v}` by {r.get('by')} in {b.id} knows {', '.join(sorted(named & remove))}, taken "
                              f"out, and {', '.join(sorted(named - remove))}, kept: take out all it knows, or none")
            out.append(i)
    return out


def _known(e):
    """How the statements a plan adds to a bean are known: `say` (the default), or `read` from a being of the garden, the
    source named by its id — never words that would write more than the act."""
    k = e.get('known') or {'act': 'say'}
    if k.get('act') not in ('say', 'read') or (k.get('act') == 'read' and not _ID.match(str(k.get('from') or ''))):
        raise Refused(f"what is added to {e.get('bean')} is known by `say`, or by `read` from a being named by its id")
    return k


def plan_writes(write):
    """Print the write — in words, then PLAN_MARK and the write as one line of JSON — and return that text: what the
    person is shown and ratifies. Refused where the garden is not as the write would have it."""
    _garden_fresh()
    G = _garden()
    words = [str(write.get('what') or '').strip() or 'a write']
    for e in write.get('beans') or []:
        bid = str(e.get('bean'))
        if e.get('new'):
            _path(G, bid, new=True)
            words.append(f"  + the bean {bid}, made")
        b = G.beans.get(bid)
        if b is None and not e.get('new'):
            raise Refused(f"no bean {bid!r} here")
        if e.get('gone'):
            words.append(f"  - the bean {bid}, taken out whole")
            continue
        remove = set(str(x) for x in e.get('remove') or [])
        for sid in sorted(remove):
            if b is None or sid not in b.ids:
                raise Refused(f"{bid} holds no statement {sid!r} to take out")
            words.append(f"  - {bid}: {b.ids[sid][1]}#{sid}")
        if b is not None:
            for i in _taken_acts(b, remove):
                words.append(f"  - {bid}: the {_acts_named(b, {i})[0]} that knew only what goes")
        for line in e.get('add') or []:
            _verb, roles = _statement(line)
            if b is not None and roles['id'] in b.ids and roles['id'] not in remove:
                raise Refused(f"{bid} holds a statement {roles['id']!r} already")
            words.append(f"  + {bid}: {line}")
        _known(e)
    seen = set()
    for f in write.get('files') or []:
        if not isinstance(f, dict) or not isinstance(f.get('after'), str) or f.get('path') in seen \
                or not isinstance(f.get('before'), (str, type(None))):
            raise Refused("a file a plan writes is `{path, before, after}`, its texts as read and as written, each "
                          "path once")
        seen.add(f['path'])
        if _text(garden_file(f['path'])) != f['before']:
            raise Refused(f"{f['path']} is not as the plan read it")
        if f['before'] is None:
            words.append(f"  + the file {f['path']}, made")
        for d in difflib.ndiff((f['before'] or '').splitlines(), f['after'].splitlines()):
            if d[:2] in ('- ', '+ '):
                words.append(f"  {d[0]} {f['path']}: {d[2:]}")
    text = '\n'.join(words) + '\n' + PLAN_MARK + '\n' + json.dumps(write, ensure_ascii=False, sort_keys=True) + '\n'
    print(text, end='')
    return text


def _plan_of(bean, course):
    """The plan this run applies: the one the engine names (DAFTAR_ACTION_PLAN, as it does for `apply`), else — for
    `verify` and `restore`, which it names none for — the course's last plan captured, the one it gave apply."""
    if os.environ.get('DAFTAR_ACTION_PLAN'):
        return shown()
    d = os.path.join(ROOT, 'captures', 'actions')
    pre = f"{bean}.{course}.plan."
    caps = [f for f in (os.listdir(d) if os.path.isdir(d) else []) if f.startswith(pre) and f[len(pre):-4].isdigit()]
    if not caps:
        raise Refused(f"no plan of {bean}'s course {course} is captured: nothing was applied")
    return os.path.join(d, max(caps, key=lambda f: int(f[len(pre):-4])))


def shown_write(bean, course):
    """The write of the plan this run applies (`_plan_of`), or a refusal."""
    with open(_plan_of(bean, course), encoding='utf-8') as fh:
        _words, mark, data = fh.read().partition('\n' + PLAN_MARK + '\n')
    if not mark:
        raise Refused("the plan shown carries no write: it was not made by plan_writes")
    try:
        return json.loads(data.strip())
    except ValueError as e:
        raise Refused(f"the plan's write does not read: {e}")


def ratifier(bean, course):
    """Who ratified the plan this run applies — the `by` of the course's last move to `apply` — or None."""
    for m in reversed(dmact.moves_so_far(bean, course)):
        if dmact.step_of(m) == 'apply':
            return str(m.get('by')) if m.get('by') else None
    return None


def _garden_fresh():
    dmact.fresh()


def _git(*a):
    return subprocess.run(['git', '-C', ROOT, *a], capture_output=True, text=True, encoding='utf-8', errors='replace')


def _set_aside(path):
    """The statements the bean at `path` holds beyond its last commit — the run's moves the engine wrote and saves after
    the tool's steps — taken out of the file, as the lines to put back: the write is saved without them, and the
    engine's own save, which carries them, finds the bean as it left it. Refused where it holds any other change."""
    from core import merge
    rel = os.path.relpath(path, ROOT).replace(os.sep, '/')
    with open(path, encoding='utf-8') as fh:
        now = fh.read().replace('\r\n', '\n')
    head = _git('show', f'HEAD:{rel}')
    if head.returncode != 0 or now == head.stdout:
        return ''
    a, b = merge.Side(head.stdout, rel), merge.Side(now, rel)
    lines, n = now.split('\n'), len(a.items)
    extra = [i for i in range(n, len(b.items))]
    kept = [ln for j, ln in enumerate(lines) if not any(b.spans[i][0] <= j < b.spans[i][2] for i in extra)]
    if '\n'.join(kept) != head.stdout:
        raise Refused(f"{rel} holds a change that is not this run's moves: save it, or put it back, first")
    with open(path, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(head.stdout)
    return '\n'.join(ln for i in extra for ln in lines[b.spans[i][0]:b.spans[i][2]]) + '\n'


def _guarded_save(paths, who, what, body, edit):
    """`edit()` then ONE save of `who`'s; a refusal — the gate's, or an edit bin/safe.py would not make — puts each of
    `paths` (and the journal) back as it was, unstages all, and is said as the tool's: nothing written."""
    import safe as dmsafe
    keep = {}
    for p in list(paths) + [os.path.join(ROOT, 'log', 'journal.md')]:
        if p not in keep:
            keep[p] = open(p, 'rb').read() if os.path.exists(p) else None
    try:
        said = edit()
        return save(who, what, list(body) + said)
    except (Refused, dmsafe.UnsafeEdit, OSError, KeyError, ValueError) as e:
        for p, was in keep.items():
            if was is None:
                if os.path.exists(p):
                    os.remove(p)
            else:
                with open(p, 'wb') as fh:
                    fh.write(was)
        _git('reset', '-q')
        raise Refused(f"nothing written: {e}")


def _take_out(path, b, ids):
    """Take the statements `ids` out of the bean `b` at `path`, with the knowing acts that knew only them; how each of
    those acts is named, for the entry that must name it (rule `kept`): its verb, and its id where it has one."""
    import safe as dmsafe
    acts = set(_taken_acts(b, ids))

    def change(lines, side):
        out, prev = [], 0
        for n, it in enumerate(side.items):
            if n in acts or str(it.roles.get('id')) in ids:
                s, _d, end = side.spans[n]
                out += lines[prev:s]
                prev = end
        return out + lines[prev:]
    dmsafe._lines_edit(path, change, allow_remove=('statements',))
    return _acts_named(b, acts)


def _acts_named(b, acts):
    """The knowing acts at the indexes `acts` of bean `b`, as an entry names what it takes out: `the <verb>` where none
    has an id, else each act with an id by its verb and its id (`the say dashboard-…`), so rule `kept` finds every
    statement taken out named — a page's acts carry ids, a hand's do not."""
    named = sorted({f"{v} {r['id']}" if isinstance(r.get('id'), str) else v for i, v, r in b.items if i in acts})
    return named


def apply_writes(bean, course):
    """Write exactly the plan shown, known by the person who ratified it, in ONE save; its entry names every bean it
    touches and each statement it takes out. The run's own moves (the ratification the engine wrote, unsaved) are set
    aside for it and put back after, for the engine's save. A refusal — the gate's, or a write bin/safe.py would not
    make — puts back every file it touched and unstages all, and says why."""
    import safe as dmsafe
    write = shown_write(bean, course)
    who = ratifier(bean, course)
    if not who:
        raise Refused("no person ratified this plan: a write in the garden is a person's word")
    _garden_fresh()
    G = _garden()
    entries = write.get('beans') or []
    paths = {str(e.get('bean')): _path(G, str(e.get('bean')), new=bool(e.get('new'))) for e in entries}
    files = [(f, garden_file(f.get('path'))) for f in write.get('files') or []]
    course_path, moves = _path(G, bean), []

    def edit():
        said = []
        moves.append(_set_aside(course_path))
        for e in entries:
            bid, p = str(e.get('bean')), paths[str(e.get('bean'))]
            if e.get('gone'):
                os.remove(p)
                said.append(f"- taken out: the bean [[{bid}]], whole")
                continue
            if e.get('new'):
                head, body = e['new'].get('head', ''), e['new'].get('body', '')
                with open(p, 'w', encoding='utf-8', newline='\n') as fh:
                    fh.write('---\n' + head.rstrip('\n') + '\n---\n' + body.rstrip('\n') + '\n')
            remove = set(str(x) for x in e.get('remove') or [])
            if remove:
                acts = _take_out(p, G.beans[bid], remove)
                said.append(f"- taken out: [[{bid}]] {', '.join(sorted(remove))}"
                            + (f", and the {' and the '.join(acts)} that knew only them" if acts else ''))
            ids = [_statement(line)[1]['id'] for line in e.get('add') or []]
            if ids:
                known = _known(e)
                if known.get('act') == 'read':
                    act = (f"- read: {{ by: {who}, of: [{', '.join(ids)}], from: {known['from']}, "
                           f"through: {json.dumps(str(known.get('through') or ''), ensure_ascii=False)}, at: now }}\n")
                else:
                    act = f"- say: {{ by: {who}, of: [{', '.join(ids)}], at: now }}\n"
                dmsafe.add_statements(p, ''.join(f"- {line}\n" for line in e['add']) + act)
                said.append(f"- added: [[{bid}]] {', '.join(ids)}")
        for f, p in files:
            if _text(p) != f.get('before'):
                raise Refused(f"{f['path']} changed since the plan was shown")
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, 'w', encoding='utf-8', newline='') as fh:
                fh.write(f['after'])
            said.append(f"- {'made' if f.get('before') is None else 'changed'}: {f['path']}, as the plan showed it")
        return said + [f"- action: the plan {who} ratified for the course {course} of {bean}, written as it was shown"]
    what = str(write.get('what') or f"{bean} {course}: applied")
    out = _guarded_save(list(paths.values()) + [p for _f, p in files] + [course_path], who, what,
                        write.get('body') or [], edit)
    if moves and moves[0]:
        dmsafe.add_statements(course_path, moves[0])
    print(out, end='')


def _same(planned, got):
    """A value the plan wrote and the value committed are the same: each `now` of the plan, wherever it stands — a role,
    or a member of a list (a pin's `at: [now, <commit>]`) — matching the moment the save wrote in its place."""
    if planned == 'now':
        return True
    if isinstance(planned, list) and isinstance(got, list):
        return len(planned) == len(got) and all(_same(p, g) for p, g in zip(planned, got))
    if isinstance(planned, dict) and isinstance(got, dict):
        return planned.keys() == got.keys() and all(_same(planned[k], got[k]) for k in planned)
    return planned == got


def verify_writes(bean, course):
    """The write read back from the garden as committed: each bean made is here and each taken out is not; each
    statement added holds what the plan wrote (each `now` the save turned into its moment, in a role or a list); each
    taken out is gone."""
    write = shown_write(bean, course)
    _garden_fresh()
    G = _garden()
    for e in write.get('beans') or []:
        bid = str(e.get('bean'))
        b = G.beans.get(bid)
        if e.get('gone'):
            if b is not None:
                raise Refused(f"the bean {bid} is still here")
            continue
        if b is None:
            raise Refused(f"the bean {bid} is not here")
        again = {_statement(line)[1]['id'] for line in e.get('add') or []}     # taken out and written anew: read below
        for sid in e.get('remove') or []:
            if str(sid) in b.ids and str(sid) not in again:
                raise Refused(f"{bid} still holds {sid}")
        for line in e.get('add') or []:
            verb, roles = _statement(line)
            hit = b.ids.get(roles['id'])
            if hit is None or hit[1] != verb or not _same(roles, hit[2]):
                raise Refused(f"{bid}: {verb}#{roles['id']} does not read back as it was written")
    for f in write.get('files') or []:
        if _text(garden_file(f.get('path'))) != f.get('after'):
            raise Refused(f"{f.get('path')} does not read back as the plan wrote it")
    print(f"read back: {len(write.get('beans') or [])} bean(s) and {len(write.get('files') or [])} file(s) as the plan "
          f"wrote them")


def restore_writes(bean, course):
    """Take out what apply added — each statement, the act it wrote to know them, each bean it made — and put each file it
    changed back as the plan read it (where it still reads as apply wrote it), in a save of its own. What apply took out
    is in git; only a person restates it, so a plan that took anything out is restored in part, and this says so and
    exits 1."""
    write = shown_write(bean, course)
    _garden_fresh()
    G = _garden()
    who = ratifier(bean, course) or 'unknown'
    gone = [str(e.get('bean')) for e in write.get('beans') or [] if e.get('gone') or e.get('remove')]
    todo = []
    for e in write.get('beans') or []:
        b = G.beans.get(str(e.get('bean')))
        if b is None or e.get('gone'):
            continue
        ids = {_statement(line)[1]['id'] for line in e.get('add') or []} & set(b.ids)
        if e.get('new') or ids:
            todo.append((b, bool(e.get('new')), ids))

    files = [(f, garden_file(f.get('path'))) for f in write.get('files') or []]
    files = [(f, p) for f, p in files if _text(p) == f.get('after') and f.get('before') != f.get('after')]

    def edit():
        said = []
        for f, p in files:
            if f.get('before') is None:
                os.remove(p)
            else:
                with open(p, 'w', encoding='utf-8', newline='') as fh:
                    fh.write(f['before'])
            said.append(f"- put back: {f['path']}, as it was before the plan")
        for b, made, ids in todo:
            if made:
                os.remove(b.path)
                said.append(f"- taken out: the bean [[{b.id}]], which the plan made")
                continue
            verbs = _take_out(b.path, b, ids)
            said.append(f"- taken out: [[{b.id}]] {', '.join(sorted(ids))}, as the plan added them"
                        + (f", and the {' and '.join(verbs)} that knew them" if verbs else ''))
        return said + [f"- action: the course {course} of {bean} restored: what its plan added is taken out"]
    out = _guarded_save([b.path for b, _m, _i in todo] + [p for _f, p in files], who,
                        f"{bean} {course}: what the plan added, taken out", [], edit) if todo or files else \
        "nothing the plan added is here: nothing to take out\n"
    print(out, end='')
    if gone:
        raise Refused(f"restored in part: what the plan took out of {', '.join(gone)} is in git, and only a person "
                      f"restates it")


def main(name, steps, more=None, argv=None):
    """The tool's command line, as the engine and a person call it. Returns the exit code."""
    a = list(sys.argv[1:] if argv is None else argv)
    more = more or {}
    exit_of = lambda r: int(r) if isinstance(r, int) else 0      # a step's text is no exit code
    try:
        if len(a) == 3 and a[0] in steps:
            return exit_of(steps[a[0]](a[1], a[2]))
        if a[:1] and a[0] in more:
            return exit_of(more[a[0]](a[1:]))
    except Refused as e:
        print(f"{name}: {e}", file=sys.stderr)
        return e.code
    usage = '|'.join(steps)
    print(f"usage: {name} {{{usage}}} <bean> <course>" + ''.join(f" | {c} …" for c in more), file=sys.stderr)
    return 2
