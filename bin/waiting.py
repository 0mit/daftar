#!/usr/bin/env python3
"""waiting — what waits: every need not met, by whose it is, by its class, by the being it concerns, read from the needs
each time it is asked and never stored (MODEL.md: readings; manifesto: once); log/pending.md's view, written from them;
and the move of a queue's open entries to needs on the beans they concern.

    python3 bin/waiting.py [--for <person>] [--json]               # what waits
    python3 bin/waiting.py --write                                  # log/pending.md's view, written from the needs
    python3 bin/waiting.py migrate [--map <file>] [--json]          # the queue's open entries placed: a count, nothing written
    python3 bin/waiting.py migrate --by <being> --write [--map <file>]   # ...and moved to the beans

(`python` on Windows.) WHAT WAITS IS A NEED ON THE BEAN IT CONCERNS (MODEL.md, the Contract of Parts): an agent that
meets what it may not decide writes `- need: { id, by: self, of: <what>, from: <whose>, note: "class <letter>" }` on
that bean, its neighbourhood and its recommendation in the bean's `details.waiting.<id>`, known by the agent's own act;
the person whose it is meets it (`- meet: { by: <person>, of: <id> }`, known by that person's `say`); a need taken out,
its removal named by the commit's entry, is withdrawn. A NEED WAITS when:
  - no `meet` names it — in its bean by its id, or from another bean as `<bean>#<id>`;
  - and it waits on someone: it names whose it is (`from`), or what it asks is not beings alone — words, an amount, or
    another need. A need of beings alone, whose nobody is named (a program needs its framework, a probe reaches a
    host), is a dependency: the garden reads it as a relation (bin/where.py, the probes), and it waits on nobody;
  - and it is not sealed (`held`), and has an id: one with none, which nothing can meet or name, is a relation too.
How badly is its strength, a position on the necessity square said of it from any bean: of none, it BLOCKS; `contingent`,
it does not (parked); `impossible`, it cannot be met. A need whose `of` names another need not yet met is BLOCKED by it,
and waits on that one first: a need of a need.

WHOSE IT IS: its `from`, where that is a person; a being that is not a person (a codebase, an organisation) by whoever
keeps it (`answer … as: keeping`), else its owner; and where it names none, whoever keeps the being that needs it, else
its owner, else the gardener. Beside them, whoever a `grant … as: ratify, class: <its class>` of the gardener's opens its
class to. Its CLASS is the first `class <letter>` its `note` says (A to K, the Contract of Parts).

THE VIEW. log/pending.md, once it holds the mark `--write` writes, is a view: an entry `## <bean>#<need> · …` for each
need that waits, written from the needs, never by hand, at the top; and below them, each entry whose heading holds no
`#`, the queue as it stood before its open entries were moved, history, kept as it was. bin/save.py writes the view again
in each save that changes a need, so the commit that parks or meets one carries it.

THE MOVE (`migrate`, the next machinery's design, IV.4, the gardener's act at a garden's adoption of core 3.7). Each
entry of log/pending.md is read by its last mark — its last `- status:` line, or a later `- re-evaluated …:` line — as one of:
  closed    the mark's first word says it: closed, done, fixed, enacted, resolved, ratified, superseded, retired,
            withdrawn, discharged, answered, decided, moot; an `acked` one that says done, fixed, enacted, closed,
            resolved, superseded, retired or withdrawn. It stays where it is, history
  proposed  `proposed`, or a re-evaluation `STILL OPEN`: a need
  acked     `acked`, saying none of those: a need still open
  parked    `parked`: a need of a lower strength (`contingent` of it)
  blocked   `blocked`: a need of a need — what blocks it a need of its own, from its `- next:` line where it has one,
            else its mark's words, and the entry's need asks it
  partly    `partly` or `in part`: split into parts — a need for each part still open, one where the entry names none
            apart (the map may name them)
and an entry whose mark says none of these, or that has none, is not placed, and is told. Each open entry is placed on
the bean its neighbourhood names (its `- neighbourhood:` line: the first `[[bean]]`, `beans/<bean>.md` or `` `bean` `` it
names that the garden holds, else the first word that is a bean's id), else on the session that parked it (`- parked
by:`, or the session its heading's author names), else it is not placed, and is told. Its words are carried whole, into
`details.waiting.<id>.words`; the need asks what its heading says needs deciding, from the gardener, its class in its
note; the act that knows them is the mover's `make` (`--by`). The closed entries stay, history, and a last entry lists
where each open one went. A map (`--map`, lines `<entry>⇥<key>⇥<value>`) may place an entry on another bean (`bean`),
read its mark as another kind (`as`), or name its parts (`part`, once for each).

Without `--write` nothing is written: each open entry's placement is counted, and each that cannot be placed told, with
why. With it, the beans and log/pending.md are written in the working tree and the entry is left for the mover's save,
which the tool prints. It writes nothing outside the garden, and opens no network path.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402 — its import sets UTF-8 on stdout and stderr
import importlib  # noqa: E402
dmpass = importlib.import_module('pass')  # noqa: E402 — `pass` is a keyword: imported by name

PENDING = os.path.join('log', 'pending.md')
MARK = ('<!-- what waits, written by `python3 bin/waiting.py --write` from the needs on the beans: each entry `## '
        '<bean>#<need>` is the view, changed by changing the needs and never here; the entries below them, whose headings '
        'hold no `#`, are the queue as it stood, history -->')
HEAD = ("What waits is a need on the bean it concerns (MODEL.md, the Contract of Parts): an agent that meets what it "
        "may not decide writes it there, `need … from:` whose it is and `note:` its class, its neighbourhood and "
        "recommendation in that bean's `details.waiting`, does everything safe around it, and carries on; the person "
        "whose it is meets it with their `say`. `python3 bin/waiting.py` reads what waits. This file is a view written "
        "from the needs, and below it the queue as it stood, history.")
POSITIONS = ('necessary', 'contingent', 'possible', 'impossible')
CLASS = re.compile(r'\bclass(?:es)?:?\s+([A-K])(?![A-Za-z])')


def listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


# ------------------------------------------------------------------------------------------------------ the reading
def _ref(x, bid):
    """`<bean>#<id>` of a statement named from bean `bid`, or None where `x` names none."""
    return x if isinstance(x, str) and '#' in x else (f"{bid}#{x}" if isinstance(x, str) else None)


def read(root=ROOT):
    """Every need of the garden at root that waits: [{about, need, ref, what, whose, for, class, strength, blocked_by,
    title}], in the beans' order and each bean's statements'; and beside them how many needs are dependencies."""
    import seq as dmseq
    L, G = dmseq.core(root)
    gardener = dmpass.gardener_of(root)

    def person(x):
        b = G.beans.get(x) if isinstance(x, str) else None
        return bool(b) and (L.kinds.get(b.kind) or {}).get('rung') == 'reason'

    def keepers(bid):
        b = G.beans.get(bid)
        items = b.items if b else []
        kept = [str(x) for _i, v, a in items if v == 'answer' and a.get('as') == 'keeping'
                and a.get('of') in (None, 'self', bid) for x in listed(a.get('by')) if isinstance(x, str)]
        owned = [str(x) for _i, v, a in items if v == 'own' and a.get('of') in (None, 'self', bid)
                 for x in listed(a.get('by')) if isinstance(x, str) and x not in L.crown]
        return kept or owned

    met, strength, needs, ratifiers = set(), {}, [], {}
    for bid, b in G.beans.items():
        for _i, verb, r in b.items:
            if verb == 'meet':
                met.update(x for x in (_ref(o, bid) for o in listed(r.get('of'))) if x)
            elif verb in POSITIONS:
                for o in listed(r.get('of')):
                    if _ref(o, bid):
                        strength[_ref(o, bid)] = verb
            elif verb == 'grant' and r.get('as') == 'ratify' and 'held' not in r:
                for c in listed(r.get('class')):
                    ratifiers.setdefault(str(c), set()).update(str(x) for x in listed(r.get('to')) if isinstance(x, str))
    dependencies = 0
    for bid, b in sorted(G.beans.items()):
        for _i, verb, r in b.items:
            if verb != 'need' or 'held' in r:
                continue
            if not isinstance(r.get('id'), str):
                dependencies += 1                       # nothing can meet or name it: a relation, as a dependency is
                continue
            ref = f"{bid}#{r['id']}"
            if ref in met:
                continue
            asks = listed(r.get('of'))
            beings = [x for x in asks if isinstance(x, str) and (x == 'self' or x in G.beans or x in L.crown)
                      and not (x in b.ids or '#' in x)]
            if 'from' not in r and asks and len(beings) == len(asks):
                dependencies += 1
                continue
            needs.append((bid, b, r, ref, asks))
    out = []
    waits = {ref for _bid, _b, _r, ref, _a in needs}
    for bid, b, r, ref, asks in needs:
        whose = [str(x) for x in listed(r.get('from'))]
        cls = (CLASS.search(str(r.get('note') or '')) or [None, ''])[1]
        people = []
        for w in whose:
            people += [w] if person(w) else keepers(w) if w in G.beans else []
        if not whose:
            people = keepers(bid)
        if not people and gardener:
            people = [gardener]
        people = sorted(set(people) | ratifiers.get(cls, set()))
        blocked = [x for x in (_ref(o, bid) for o in asks if isinstance(o, str) and (o in b.ids or '#' in o)) if x in waits]
        what = '; '.join(str(x) for x in asks if not (isinstance(x, str) and (x in b.ids or '#' in x)) and isinstance(x, str))
        out.append({'about': bid, 'need': r['id'], 'ref': ref, 'what': what or r['id'], 'whose': whose, 'for': people,
                    'class': cls, 'strength': {'contingent': 'contingent', 'impossible': 'impossible'}.get(
                        strength.get(ref), 'blocks'),
                    'blocked_by': blocked, 'title': str(b.header.get('title') or '')})
    return out, dependencies


def details_of(root, bid, nid):
    """`details.waiting.<nid>` of bean `bid`: its neighbourhood and recommendation, or the words it was moved with."""
    import seq as dmseq
    _L, G = dmseq.core(root)
    b = G.beans.get(bid)
    d = (b.header.get('details') if b else None) or {}
    w = d.get('waiting') if isinstance(d, dict) else None
    x = w.get(nid) if isinstance(w, dict) else None
    return x if isinstance(x, dict) else {}


def _strength(x):
    if x['blocked_by']:
        return f"blocked by {', '.join(x['blocked_by'])}"
    return {'blocks': 'it blocks', 'contingent': 'parked: it does not block',
            'impossible': 'it cannot be met'}[x['strength']]


def text(items, dependencies, who=None, left=0):
    """The reading, as a person or a model reads it: by whose it is, by class, by the being it concerns."""
    say = dmparse.said
    out = ["waiting — every need not met, read from the garden now and never stored", ""]
    people = sorted({p for x in items for p in x['for']} | ({who} if who else set()))
    for p in people:
        mine = [x for x in items if p in x['for']]
        if who and p != who:
            continue
        out.append(f"for {p}: {len(mine)}")
        for cls in sorted({x['class'] for x in mine}, key=lambda c: (c == '', c)):
            these = [x for x in mine if x['class'] == cls]
            out.append(f"  class {cls or 'unsaid'}: {len(these)}")
            for x in sorted(these, key=lambda x: x['ref']):
                out.append(say(f"    {x['ref']} · {x['what']}" + (f" (from {', '.join(x['whose'])})" if x['whose']
                                                                  else '') + f" — {_strength(x)}"))
        out.append("")
    shown = [x for x in items if not who or who in x['for']]
    out.append(f"needs that wait: {len(shown)}" + (f" for {who}" if who else '') + f"; dependencies of beings alone, "
               f"which wait on nobody: {dependencies}")
    if left:
        out.append(f"log/pending.md still holds {left} open entr{'y' if left == 1 else 'ies'} not moved to needs: "
                   f"`python3 bin/waiting.py migrate` counts them, `--by <being> --write` moves them")
    return '\n'.join(out)


# -------------------------------------------------------------------------------------------------------- the view
def entries(content):
    """(preamble, [(heading line, entry text)]) of log/pending.md: an entry runs from its `## ` heading to the next, a
    heading inside a fenced block (an example of an entry) being none."""
    pre, out, fenced = [], [], False
    for ln in content.splitlines(keepends=True):
        if ln.lstrip().startswith('```'):
            fenced = not fenced
        if ln.startswith('## ') and not fenced:
            out.append([ln])
        elif out:
            out[-1].append(ln)
        else:
            pre.append(ln)
    return ''.join(pre), [(e[0].rstrip('\r\n'), ''.join(e)) for e in out]


def _is_view(heading):
    return '#' in heading[3:].split(' · ', 1)[0]


def view_entries(root, items):
    """The view's entries, `## <bean>#<need> · <what> · <whose and class>`, each with its strength and its details."""
    out = []
    for x in sorted(items, key=lambda x: (x['class'] == '', x['class'], x['ref'])):
        d = details_of(root, x['about'], x['need'])
        head = ' · '.join([x['ref'], x['what'].replace('\n', ' ')] + [', '.join(
            ([f"from {', '.join(x['whose'])}"] if x['whose'] else []) + ([f"class {x['class']}"] if x['class'] else []))
            or 'whose unsaid'])
        lines = [f"## {head}", f"- for: {', '.join(x['for']) or 'nobody named'}", f"- strength: {_strength(x)}",
                 f"- on: [[{x['about']}]]" + (f" — {x['title']}" if x['title'] else '')]
        for k in ('neighbourhood', 'recommendation'):
            if isinstance(d.get(k), str):
                lines.append(f"- {k}: {d[k]}".replace('\n', ' '))
        if isinstance(d.get('words'), str):
            lines.append(f"- its words: [[{x['about']}]] details.waiting.{x['need']}.words"
                         + (f", moved from the queue's entry {d['queue']}" if isinstance(d.get('queue'), str) else ''))
        out.append('\n'.join(dmparse.said(ln) for ln in lines) + '\n')
    return out


def view(root, content, items):
    """log/pending.md's text with its view written from `items` — or None where the file holds no mark of the view."""
    if MARK not in content:
        return None
    pre, kept = entries(content)
    history = [e for h, e in kept if not _is_view(h)]
    body = [e if e.endswith('\n\n') else e.rstrip('\n') + '\n\n' for e in view_entries(root, items) + history]
    return pre.rstrip('\n') + '\n\n' + ''.join(body).rstrip('\n') + '\n'


def write_view(root=ROOT):
    """Write log/pending.md's view where it holds the mark; True where it changed."""
    path = os.path.join(root, PENDING)
    try:
        with open(path, encoding='utf-8') as fh:
            content = fh.read()
    except OSError:
        return False
    items, _dep = read(root)
    new = view(root, content, items)
    if new is None or new == content:
        return False
    import safe as dmsafe
    dmsafe.write_atomic(path, new)
    return True


# --------------------------------------------------------------------------------------------------------- the move
CLOSED = ('closed', 'done', 'fixed', 'enacted', 'resolved', 'ratified', 'superseded', 'retired', 'withdrawn',
          'discharged', 'answered', 'decided', 'moot')
ACKED_CLOSED = re.compile(r'\b(done|fixed|enacted|closed|resolved|superseded|retired|withdrawn)\b', re.I)
MARK_LINE = re.compile(r'^\s*-\s*\**\s*(status|re-evaluated)\b[^:]*:\**\s*(.*)$', re.I)
FIELD = re.compile(r'^- \**([a-z][a-z _-]*?)\**:\s?(.*)$', re.I)
KINDS = ('closed', 'proposed', 'acked', 'parked', 'blocked', 'partly')


def read_mark(entry):
    """(kind, the mark's line) of a queue entry, by its last `- status:` or `- re-evaluated …:` line; kind None where
    it has none, or says none of the kinds."""
    marks = [ln for ln in entry.splitlines()[1:] if MARK_LINE.match(ln)]
    if not marks:
        return None, ''
    line = marks[-1].strip()
    key, said = MARK_LINE.match(line).groups()
    said = said.replace('*', '').strip()
    if key.lower() == 're-evaluated':
        said = re.sub(r'^\([^)]*\)\s*:?\s*', '', said)
    low = said.lower()
    if re.search(r'\bpartly\b|\bin part\b', low):
        return 'partly', line
    if re.search(r'\bstill open\b|\breopened\b', low):
        return 'proposed', line
    first = re.sub(r'[^a-z-]', '', (low.split() or [''])[0])
    if first == 'acked':
        return ('closed' if ACKED_CLOSED.search(said) else 'acked'), line
    if first in CLOSED:
        return 'closed', line
    if first in ('proposed', 'parked', 'blocked'):
        return first, line
    return None, line


def fields(entry):
    """{field: [its text, …]} of an entry's own `- <field>: …` lines, as written."""
    out = {}
    for ln in entry.splitlines()[1:]:
        m = FIELD.match(ln)
        if m:
            out.setdefault(m.group(1).strip().lower(), []).append(m.group(2).strip())
    return out


def place(entry, heading, G):
    """(bean, why) where the entry goes: the bean its neighbourhood names, else the session that parked it."""
    f = fields(entry)
    near = ' '.join(f.get('neighbourhood', []) + f.get('neighborhood', []) + f.get('the neighbourhood', []))
    for how, pattern in (('a link', r'\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]'),
                         ('a path', r'\b(?:beans|mappings)/([A-Za-z0-9_.-]+)\.md\b'),
                         ('a name in backquotes', r'`([a-z0-9][a-z0-9_-]*)`'),
                         ('a name', r'(?<![\w@./`-])([a-z0-9]+(?:-[a-z0-9]+)+)(?![\w@/`-]|\.\w)')):
        hit = next((x for x in re.findall(pattern, near) if x in G.beans), None)
        if hit:
            return hit, f'its neighbourhood names it, as {how}'
    who = ' '.join(f.get('parked by', []) + [heading.split(' · ')[-1] if ' · ' in heading else ''])
    for w in re.findall(r'[a-z0-9][a-z0-9_.-]*[a-z0-9]', who):
        for c in (w, f"session-{w}"):
            if c in G.beans and G.beans[c].kind == 'session':
                return c, 'the session that parked it'
    return None, ("its neighbourhood names no bean of the garden" if near else "it has no neighbourhood") + \
        ", and it names no session of the garden that parked it"


def read_map(path):
    """{entry: {bean: …, as: …, part: [...]}} of a map's lines `<entry>⇥<key>⇥<value>` (`#` begins a comment)."""
    out = {}
    if not path:
        return out
    with open(path, encoding='utf-8') as fh:
        for n, ln in enumerate(fh, 1):
            if not ln.strip() or ln.lstrip().startswith('#'):
                continue
            parts = ln.rstrip('\r\n').split('\t')
            if len(parts) != 3 or parts[1] not in ('bean', 'as', 'part') or not parts[2].strip():
                raise SystemExit(f"waiting: {path}:{n}: a map's line is `<entry>⇥bean|as|part⇥<value>`")
            if parts[1] == 'as' and parts[2] not in KINDS:
                raise SystemExit(f"waiting: {path}:{n}: `as` is one of {', '.join(KINDS)}")
            e = out.setdefault(parts[0], {'part': []})
            if parts[1] == 'part':
                e['part'].append(parts[2])
            else:
                e[parts[1]] = parts[2]
    return out


def plan(root=ROOT, mapped=None):
    """Each entry of log/pending.md, read and placed: [{entry, heading, kind, mark, bean, why, needs, words}] — `bean`
    None where an open entry cannot be placed, `needs` the statements it becomes."""
    import seq as dmseq
    _L, G = dmseq.core(root)
    mapped = mapped or {}
    gardener = dmpass.gardener_of(root)
    try:
        with open(os.path.join(root, PENDING), encoding='utf-8') as fh:
            content = fh.read()
    except OSError:
        return [], ''
    _pre, kept = entries(content)
    taken = {bid: set(b.ids) for bid, b in G.beans.items()}
    out = []
    for heading, entry in kept:
        if _is_view(heading):
            continue
        slug = heading[3:].split(' · ')[0].strip()
        kind, mark = read_mark(entry)
        m = mapped.get(slug, {})
        kind = m.get('as', kind)
        row = {'entry': slug, 'heading': heading, 'kind': kind, 'mark': mark, 'bean': None, 'why': '', 'needs': [],
               'words': entry.rstrip('\n') + '\n'}
        out.append(row)
        if kind == 'closed':
            continue
        if kind is None:
            row['why'] = ("its last mark says none of " + ', '.join(KINDS) + f": {mark}") if mark else \
                "it has no `- status:` line"
            continue
        bean, why = (m['bean'], 'the map places it') if m.get('bean') else place(entry, heading, G)
        if bean is not None and bean not in G.beans:
            bean, why = None, f"the map places it on {bean}, which the garden does not hold"
        if bean is not None and writable(G.beans[bean].path):
            bean, why = None, f"its bean {bean} {writable(G.beans[bean].path)}"
        row['bean'], row['why'] = bean, why
        if bean is None:
            continue
        f = fields(entry)
        cls = (f.get('class') or [''])[0]
        what = heading[3:].split(' · ')[1].strip() if heading.count(' · ') >= 1 else slug

        def fresh(base):
            base = re.sub(r'-+', '-', re.sub(r'[^a-z0-9_-]', '-', base.lower())).strip('-') or 'waits'
            nid, n = base, 1
            while nid in taken[bean]:
                n += 1
                nid = f"{base}-{n}"
            taken[bean].add(nid)
            return nid
        nid = fresh(slug)
        need = {'id': nid, 'by': 'self', 'of': what, 'from': gardener, 'note': f"class {cls}" if cls else None}
        parts = m.get('part') or []
        if kind == 'partly' and parts:
            row['needs'] = [dict(need, id=fresh(f"{slug}-{i}") if i > 1 else nid, of=p)
                            for i, p in enumerate(parts, 1)]
        elif kind == 'blocked':
            first = dict(need, id=fresh(f"{slug}-first"), of=(f.get('next') or [re.sub(
                r'^\s*-\s*\**\s*status:?\**\s*', '', mark)])[-1])
            row['needs'] = [first, dict(need, of=[what, first['id']])]
        else:
            row['needs'] = [need]
        if kind == 'parked':
            row['needs'][0]['contingent'] = fresh(f"{nid}-parked")
    return out, content


def writable(path):
    """'' where a tool may add statements and `details.waiting` to the bean at path, else why not: its statements, and
    its `details` where it has them, are written as blocks of YAML, one item to a line."""
    try:
        with open(path, encoding='utf-8') as fh:
            lines = fh.read().split('\n')
        fence = next(i for i in range(1, len(lines)) if lines[i].rstrip() == '---')
    except (OSError, StopIteration):
        return "cannot be read as a bean"
    st = [ln for ln in lines[1:fence] if re.match(r'^statements:', ln)]
    if st and st[0].rstrip() not in ('statements:', 'statements: []'):
        return "has its statements written in flow (`statements: [ … ]`): a tool adds one to a line"
    dt = [ln for ln in lines[1:fence] if re.match(r'^details:', ln)]
    if dt and dt[0].rstrip() != 'details:':
        return "has its `details` written in flow: a tool adds to a block of YAML"
    return ''


def _flow(v):
    return json.dumps(v, ensure_ascii=False)


def _statement(n):
    roles = [f"id: {n['id']}", "by: self", f"of: {_flow(n['of'])}"] + ([f"from: {n['from']}"] if n.get('from') else []) \
        + ([f"note: {_flow(n['note'])}"] if n.get('note') else [])
    out = f"- need: {{ {', '.join(roles)} }}\n"
    if n.get('contingent'):
        out += f"- contingent: {{ id: {n['contingent']}, of: {n['id']} }}\n"
    return out


def _details_block(records, indent):
    """`records` ({id: {queue, read_as, words}}) as block YAML at `indent`, the words a literal block scalar."""
    pad = ' ' * indent
    out = []
    for nid, rec in records.items():
        out.append(f"{pad}{nid}:\n")
        out.append(f"{pad}  queue: {_flow(rec['queue'])}\n")
        out.append(f"{pad}  read_as: {rec['read_as']}\n")
        out.append(f"{pad}  words: |-\n")
        out += [f"{pad}    {ln}\n" if ln else '\n' for ln in rec['words'].rstrip('\n').split('\n')]
    return ''.join(out)


def _add_details(path, records):
    """Write `records` under the bean's `details.waiting`, made where it has none; refused where `details` is not
    written as a block of YAML."""
    import safe as dmsafe

    def t(text):
        lines = text.split('\n')
        fence = next(i for i in range(1, len(lines)) if lines[i].rstrip() == '---')
        top = next((i for i in range(1, fence) if re.match(r'^details:', lines[i])), None)
        if top is None:
            return '\n'.join(lines[:fence]) + '\ndetails:\n  waiting:\n' + _details_block(records, 4) + \
                '\n'.join(lines[fence:])
        if lines[top].rstrip() != 'details:':
            raise dmsafe.UnsafeEdit("its `details` is not written as a block of YAML")
        end = top + 1
        while end < fence and (not lines[end].strip() or lines[end].startswith(' ')):
            end += 1
        while end > top + 1 and not lines[end - 1].strip():
            end -= 1
        w = next((i for i in range(top + 1, end) if re.match(r'^  waiting:\s*$', lines[i])), None)
        if w is None:
            return '\n'.join(lines[:end]) + '\n  waiting:\n' + _details_block(records, 4) + '\n'.join(lines[end:])
        wend = w + 1
        while wend < end and (not lines[wend].strip() or lines[wend].startswith('   ')):
            wend += 1
        while wend > w + 1 and not lines[wend - 1].strip():
            wend -= 1
        return '\n'.join(lines[:wend]) + '\n' + _details_block(records, 4) + '\n'.join(lines[wend:])
    dmsafe.edit(path, t)


def migrate(root, rows, content, by):
    """Move each placed open entry to its bean, and write log/pending.md as the view and the history. Returns the lines
    of the journal entry the move's save carries."""
    import safe as dmsafe
    import seq as dmseq
    _L, G = dmseq.core(root)
    if by not in G.beans:
        raise SystemExit(f"waiting: --by {by}: the garden holds no such bean — the act that knows the needs is a being's")
    beans = {}
    for row in rows:
        if row['bean'] and row['needs']:
            beans.setdefault(row['bean'], []).append(row)
    said = []
    for bid, these in beans.items():
        path = G.beans[bid].path
        ids = [i for row in these for n in row['needs'] for i in (n['id'], n.get('contingent')) if i]
        block = ''.join(_statement(n) for row in these for n in row['needs'])
        block += f"- make: {{ by: {by}, of: [{', '.join(ids)}], at: now, note: {_flow('moved from log/pending.md by bin/waiting.py migrate: ' + ', '.join(r['entry'] for r in these))} }}\n"
        dmsafe.add_statements(path, block)
        _add_details(path, {row['needs'][-1]['id']: {'queue': row['entry'], 'read_as': row['kind'],
                                                      'words': row['words']} for row in these})
        written = dmgarden_fm(path)
        w = ((written.get('details') or {}).get('waiting') or {})
        for row in these:
            if (w.get(row['needs'][-1]['id']) or {}).get('words') != row['words'].rstrip('\n'):
                raise SystemExit(f"waiting: {bid}: the words of {row['entry']} did not read back whole — nothing more "
                                 f"is written; the beans written so far are in the working tree for `git checkout`")
        said.append(f"- added: [[{bid}]] {', '.join(ids)}")
    pre, kept = entries(content)
    moved = {row['entry'] for row in rows if row['bean'] and row['needs']}
    history = [e for h, e in kept if not _is_view(h) and h[3:].split(' · ')[0].strip() not in moved]
    import datetime
    pointer = (f"## moved-to-needs · the queue's open entries, moved to needs on the beans they concern · "
               f"{datetime.date.today().isoformat()} by {by}\n"
               "- status: closed — a record of the move, history\n"
               + ''.join(f"- {row['entry']}: [[{row['bean']}]] {row['needs'][-1]['id']}\n"
                         for row in rows if row['entry'] in moved))
    title = re.match(r'#\s+(.+?)\s+—', pre)
    name = title.group(1) if title else os.path.basename(os.path.abspath(root))
    head = f"# {name} — what waits\n\n{HEAD}\n\n{MARK}\n"
    text = head + '\n' + ''.join(e if e.endswith('\n\n') else e.rstrip('\n') + '\n\n' for e in history + [pointer])
    dmsafe.write_atomic(os.path.join(root, PENDING), text.rstrip('\n') + '\n')
    dmseq._CORE.clear()
    write_view(root)
    return said + [f"- changed: log/pending.md — a view written from the needs; {len(moved)} open entr"
                   f"{'y' if len(moved) == 1 else 'ies'} moved to needs, the closed ones kept as they were, history"]


def dmgarden_fm(path):
    import garden as dmgarden
    d = dmgarden.document(path)
    return d.fm if isinstance(d.fm, dict) else {}


def open_left(root=ROOT):
    """How many entries of log/pending.md are open and not moved to needs (the move's own reading of their marks)."""
    try:
        with open(os.path.join(root, PENDING), encoding='utf-8') as fh:
            content = fh.read()
    except OSError:
        return 0
    return sum(1 for h, e in entries(content)[1] if not _is_view(h) and read_mark(e)[0] not in ('closed', None))


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    opt = lambda k: argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else None
    if argv[:1] == ['migrate']:
        rows, content = plan(ROOT, read_map(opt('--map')))
        open_rows = [r for r in rows if r['kind'] != 'closed']
        placed = [r for r in open_rows if r['bean']]
        if '--json' in argv:
            print(json.dumps([{k: r[k] for k in ('entry', 'kind', 'bean', 'why', 'needs')} for r in rows],
                             ensure_ascii=False, indent=1))
        else:
            for r in open_rows:
                print(dmparse.said(f"{r['entry']} · {r['kind'] or 'unread'} · " + (
                    f"on {r['bean']} as {', '.join(n['id'] for n in r['needs'])}" if r['bean']
                    else f"NOT PLACED: {r['why']}")))
            counts = {k: sum(1 for r in rows if r['kind'] == k) for k in KINDS}
            print(f"entries: {len(rows)} — closed {counts['closed']}, kept as history; open {len(open_rows)}: "
                  + ', '.join(f"{k} {counts[k]}" for k in KINDS[1:]) + f", unread {sum(1 for r in rows if r['kind'] is None)}")
            print(f"placed: {len(placed)} of {len(open_rows)}, on {len({r['bean'] for r in placed})} bean(s), as "
                  f"{sum(len(r['needs']) for r in placed)} need(s); not placed: {len(open_rows) - len(placed)}")
        if '--write' not in argv:
            return 0
        by = opt('--by')
        if not by:
            raise SystemExit("waiting: migrate --write names the being whose act knows the needs: --by <being>")
        lines = migrate(ROOT, rows, content, by)
        body = os.path.join(ROOT, '.git', 'daftar-waiting-entry.md') if os.path.isdir(os.path.join(ROOT, '.git')) \
            else os.path.join(ROOT, 'waiting-entry.md')
        with open(body, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write('\n'.join(lines) + '\n- action: the queue\'s open entries moved to needs by bin/waiting.py migrate\n')
        print(f"written in the working tree; the entry is in {body} — save it:\n"
              f"  python3 bin/save.py \"{by}\" \"what waits: the queue's open entries moved to needs\" < {body}")
        return 0
    if '--write' in argv:
        print("waiting: log/pending.md's view written" if write_view(ROOT) else
              "waiting: log/pending.md unchanged" + ('' if MARK in _read(os.path.join(ROOT, PENDING)) else
                                                     " — it holds no mark of the view (`migrate` writes it)"))
        return 0
    items, dependencies = read(ROOT)
    who = opt('--for')
    if '--json' in argv:
        print(json.dumps([x for x in items if not who or who in x['for']], ensure_ascii=False, indent=1))
    else:
        print(text(items, dependencies, who, open_left(ROOT)))
    return 0


def _read(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read()
    except OSError:
        return ''


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
