#!/usr/bin/env python3
"""routines — a machine's routines: what runs where and when, whether it may run now, and the one engine that runs it.

    python3 bin/routines.py [list] [--at <moment>] [--readings <file> ...] [--json]
    python3 bin/routines.py due [--at <moment>] [--readings <file> ...] [--json]    # this machine's: due now, waiting, why
    python3 bin/routines.py tick [--at <moment>] [--readings <file> ...] [--json]   # the engine, once: what a host's
                                                                                     # daftard calls each minute
    python3 bin/routines.py needs <bean> [--of <bean>] [--readings <file> ...] [--json]   # a being's needs, read now
    python3 bin/routines.py cross [--readings <file> ...] [--json]     # needs read against the probes: crossings written
    python3 bin/routines.py tools [--json]                               # the tools this machine holds: what daftard probes
    python3 bin/routines.py propose <bean> <walk> [--why <words>]       # a walk proposed for a being by a person: placed and
                                                                       # run to its first person's step or pause
    python3 bin/routines.py adopt cron <crontab> --host <bean> [--user <name>] [--at <day>]   # a proposal, written nowhere
    python3 bin/routines.py render cron --host <bean> [--user <name>] [--live <crontab>]   # the lines the garden says

(`python` on Windows.) A ROUTINE IS NO NEW THING: it is what the law already says of a walk, a clause and a need
(core/law/; MODEL.md: "Lines", "Agreements and money"). In the bean of the being it acts on:

    - run:        { id: restart-each-week, by: <the machine that runs it>, of: <the walk> }
    - obligatory: { id: restart-each-week-due, of: restart-each-week, through: <who asks it>,
                    clause: { due: "2026-10-18 05:45", every: { of: time, in: iso-week, each: week, at: "7",
                                                                lasts: { of: time, measure: { count: "30", unit: min } } } } }

- WHAT runs is the walk (a mapping whose `step`s are its steps; bin/act.py runs it): its tool is what it `use`s.
- WHEN: the clause's `due` is the first occurrence, a moment; `every` its recurrence (core/law/measures.yaml
  `recurrence_form`), read in the bearer's zone — the machine's placement `zone`, else GARDEN.md's — so a routine kept at
  03:30 stays at 03:30 when the clocks change; `lasts` is the WINDOW each occurrence may start in (one minute where it
  says none, as cron's). `obligatory`: it runs at each occurrence; `permitted`: it may run in each window, when
  something proposes it.
- ITS INTERLOCKS are the walk's needs: each `need` the walk states that a `reckon` reading `meet`s — the reading's
  `inputs` are probe readings (the tool's `probe --json`: `{"tool", "at", "readings": [{"key", "being", "property",
  "value": {"count", "unit"}, "at", "instrument", "quality", "detail"?}]}`; an input named as the probe's key, `.` and
  `_` read as `-`, its origin `by` the tool), so "no file open for writing" is a reading of a number, never a word. A
  reading's `detail`, where its tool gives one, is what it saw in words (which services are down, which differences it
  counted): never part of what is judged, kept in the note of the `measure` a crossing writes, so a lead says what
  crossed and not only how much. It reaches git with that note: a tool puts in it nothing the garden may not hold (no
  secret, no person's name, address or other value — ids and kinds, never values).
  Needs sharing an `as` are alternatives. A need no reading meets is not read here, and is said so.
- ITS PROOF is the acted being's own needs, read the same way after the walk's verify: the being's health, which `cross`
  reads at any time as well.
- WHO RUNS IT is read from the garden, never configured. This machine's engine runs it only where a `grant … as:
  enact` of the walk to the machine stands, by the gardener: an automatic run is named, never assumed. A walk present
  in another runner's register (`be: { by: self, at: "<host>:<crontab>", as: presence }`, its record in that register)
  is that runner's: the engine leaves it alone, and `render cron` writes its line from the garden. Both at once is a
  refusal, never two runs.

A RUN IS A COURSE (bin/act.py): each occurrence places the acted being on the walk, `be: { id: <run>-<YYYYMMDD-HHMM>,
by: self, at: <walk>, as: order }`, and the engine moves it. Its interlocks are read at `check` and again before
`apply`: where one does not hold, the course moves to the walk's pause `waits` (reason `interlock-held`) — a lead to
whoever keeps the being — and each tick reads them again; held, it returns to the step it came from; never forced.
Where the window closes first, it moves to `skipped` (reason `window-passed`). A proof that fails rolls it back
(`restore` run where the tool has one) and writes the crossing: the `measure` that showed it and a `fail` through it.
A walk with a person's step stops there: the routine proposes, the person ratifies (a lead, the plan beside it).

A CROSSING (`cross`): a being's need, read against the latest probe readings, that stops holding writes once the
`measure` that showed it and a `fail` through it (bin/leads.py: a health lead for its keeper); holding again, the
`measure` and a `repair` of it. Every other sample stays in the probe cache: the garden keeps what a person acts on.
Where a `repair … of: <the need>, at: <a walk>` names the walk that remedies it, a crossing places the being on that
walk: its plan proposed to the keeper, or run where the walk is granted.

ADOPTION (`adopt cron`) reads a crontab into routines as a PROPOSAL — the statements and the journal lines a person
saves — and proves, line by line, that the garden's rendering is the live line byte for byte: a line it cannot say, or
would spell otherwise, is refused with its number and why, never dropped silently. `render cron` writes the lines of a
host's routines present in its crontab; with `--live`, it says what differs.

`list`, `due`, `needs` and `render` write nothing. `tick` and `cross` write through bin/save.py, as the machine this is
(its host bean, named by its hostname): every act is the machine's, journalled.
"""
import datetime
import importlib
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
import cal as dmcal  # noqa: E402 — moments, in any calendar
import stale as dmstale  # noqa: E402 — the one reader of when a repetition falls due
import seq as dmseq  # noqa: E402 — the garden as the engine reads it, and where a course stands
dmpass = importlib.import_module('pass')  # noqa: E402 — `pass` is a keyword: imported by name

SQUARE = ('obligatory', 'permitted')
WINDOW_MS = 60_000                   # an occurrence with no `lasts` may start within its minute, as cron's would
PROBE_TIMEOUT = 120


class Refused(Exception):
    """Why nothing was done: said, and nothing written."""


def listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def now_ms():
    return int(datetime.datetime.now(datetime.timezone.utc).timestamp() * 1000)


def moment_ms(text):
    """UNIX milliseconds of a moment written with its offset."""
    return dmcal.moment(text).ms - dmcal.UNIX_DAY * dmcal.DAY_MS


def shown(ms, zone=None):
    """A moment for a reader: in `zone` where one is given, with its offset."""
    t = datetime.datetime.fromtimestamp(ms / 1000, datetime.timezone.utc)
    if zone:
        try:
            import zoneinfo
            t = t.astimezone(zoneinfo.ZoneInfo(zone))
        except Exception:      # noqa: BLE001 — no zone data: shown in UTC, and the offset says so
            pass
    return t.isoformat(timespec='minutes').replace('T', ' ')


def stamp_ms(day, hhmm, zone=None):
    """The UNIX milliseconds of a run's name (`20261018`, `0545`), read as wall time in `zone` — or None."""
    try:
        import zoneinfo
        tz = zoneinfo.ZoneInfo(zone) if zone else datetime.timezone.utc
        t = datetime.datetime(int(day[:4]), int(day[4:6]), int(day[6:]), int(hhmm[:2]), int(hhmm[2:]), tzinfo=tz)
        return int(t.timestamp() * 1000)
    except Exception:      # noqa: BLE001 — a name that names no moment
        return None


def stamp(ms, zone=None):
    """The run's name for its occurrence: its local wall clock, `20261018-0545`."""
    return re.sub(r'[^0-9]', '', shown(ms, zone)[:16])[:8] + '-' + re.sub(r'[^0-9]', '', shown(ms, zone)[11:16])


# ======================================================================================================== the garden
def garden(root=ROOT):
    dmseq._CORE.clear()
    return dmseq.core(root)[1]


def statements(b, verb):
    return [r for _i, v, r in b.items if v == verb and 'held' not in r]


def is_walk(G, wid):
    w = G.beans.get(str(wid))
    return bool(w and statements(w, 'step'))


def host_here(G):
    """The bean of the machine this runs on (bin/where.py: its hostname anchor), or None."""
    import where as dmwhere
    try:
        return dmwhere.here()[0]
    except Exception:      # noqa: BLE001 — a garden that holds no bean for this machine
        return None


def zone_of(G, machine):
    """The zone a machine's routines are kept in: its own placement's `zone`, else the garden's (GARDEN.md)."""
    m = G.beans.get(str(machine))
    for r in statements(m, 'be') if m else []:
        z = (r.get('placed') or {}).get('zone') if isinstance(r.get('placed'), dict) else None
        if isinstance(z, str):
            return z
    return G.zone


def granted(G, walk, machine, root=ROOT):
    """The grant that opens `enact` of the walk to the machine, said by the gardener — or None."""
    gardener = dmpass.gardener_of(root)
    for bid, b in G.beans.items():
        for r in statements(b, 'grant'):
            by = bid if r.get('by') == 'self' else r.get('by')
            if r.get('as') == 'enact' and str(machine) in map(str, listed(r.get('to'))) \
                    and str(walk) in map(str, listed(r.get('of'))) and by == gardener:
                return f"{bid}#{r.get('id')}" if r.get('id') else bid
    return None


def presence(G, walk):
    """The registers the walk's record is in (`be … as: presence`): [(position, statement id)]."""
    w = G.beans.get(str(walk))
    return [(str(r.get('at')), r.get('id')) for r in statements(w, 'be') if r.get('as') == 'presence'] if w else []


def routines(G, root=ROOT):
    """Every routine of the garden: a `run` of a walk, with the clauses on its permission-square positions."""
    out = []
    for bid, b in sorted(G.beans.items()):
        for r in statements(b, 'run'):
            if not (isinstance(r.get('id'), str) and is_walk(G, r.get('of'))):
                continue
            clauses = [(v, c) for _i, v, c in b.items if v in SQUARE and c.get('of') == r['id']
                       and isinstance(c.get('clause'), dict) and 'held' not in c]
            machine = bid if r.get('by') == 'self' else str(r.get('by'))     # a machine's own routine: `by: self`
            walk = str(r.get('of'))
            grant, regs = granted(G, walk, machine, root), presence(G, walk)
            runner = ('two runners' if grant and regs else 'this machine\'s engine' if grant
                      else f"its register: {regs[0][0]}" if regs else 'nobody')
            out.append({'bean': bid, 'id': r['id'], 'machine': machine, 'walk': walk, 'clauses': clauses,
                        'zone': zone_of(G, machine), 'grant': grant, 'registers': regs, 'runner': runner,
                        'person_step': person_step(G, walk)})
    return out


def person_step(G, walk):
    """The first step of the walk a person acts at (its `by` is neither the engine nor empty), or None."""
    w = G.beans.get(str(walk))
    for s in statements(w, 'step') if w else []:
        if s.get('by') not in (None, 'engine') and not (s.get('walk') or {}).get('exit') \
                and not (s.get('walk') or {}).get('resumes') and not (s.get('walk') or {}).get('final'):
            return s.get('id')
    return None


def occurrences(rt, start, end, limit=None):
    """[(clause verb, clause id, begin, end)] of a routine's occurrences open at some instant of [start, end) — the first
    `limit` of each clause, where one is given."""
    out = []
    for verb, c in rt['clauses']:
        cl = c['clause']
        first = cl.get('due') or (cl.get('every') or {}).get('from')
        if first is None:
            continue
        rec = cl.get('every') if isinstance(cl.get('every'), dict) else None
        for b, e in dmstale.moments(first, rec, start, end, zone=rt['zone'], window=WINDOW_MS, limit=limit):
            out.append((verb, c.get('id'), b, e))
    return sorted(out, key=lambda x: x[2])


def describe(rt):
    """A routine's schedule in words."""
    out = []
    for verb, c in rt['clauses']:
        cl = c['clause']
        w = dmstale.describe(cl['every']) if isinstance(cl.get('every'), dict) else 'once'
        out.append(f"{'runs' if verb == 'obligatory' else 'may run'} {w}, first {cl.get('due')}")
    return '; '.join(out) or 'no schedule: run when something proposes it'


# ========================================================================================================== readings
def norm(key):
    return re.sub(r'[._]+', '-', str(key).strip().lower())


def load_readings(paths):
    """The readings given: each file a probe's document (`{"readings": [...]}`, as `probe --json` prints it) or a list
    of them."""
    out = []
    for p in paths or []:
        with open(p, encoding='utf-8') as fh:
            doc = json.load(fh)
        for d in (doc if isinstance(doc, list) else [doc]):
            for r in (d.get('readings') or []) if isinstance(d, dict) else []:
                if isinstance(r, dict) and r.get('key') is not None:
                    out.append(dict(r, tool=d.get('tool')))
    return out


def tool_path(G, tool):
    """Where the tool is on this machine (its program bean's `be … as: location`), or None."""
    import where as dmwhere
    tb = G.beans.get(str(tool))
    try:
        _hid, hfm, names = dmwhere.here()
    except Exception:      # noqa: BLE001
        return None
    for r in statements(tb, 'be') if tb else []:
        if r.get('as') == 'location' and isinstance(r.get('at'), str):
            try:
                got = dmwhere.on_host(r['at'], dmwhere.roots_of(hfm), names)[0]
            except ValueError:
                got = None
            if got:
                return got
    return None


def probe(G, tool):
    """The tool's readings, read now: `<tool> probe --json` where the tool is on this machine; [] where it is not."""
    path = tool_path(G, tool)
    if not path:
        return []
    cmd = [sys.executable, path] if path.endswith('.py') else [path]
    try:
        r = subprocess.run(cmd + ['probe', '--json'], capture_output=True, text=True, encoding='utf-8',
                           errors='replace', timeout=PROBE_TIMEOUT, cwd=ROOT)
        doc = json.loads(r.stdout)
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return []
    return [dict(x, tool=str(tool)) for x in (doc.get('readings') or []) if isinstance(x, dict)]


class Readings:
    """The readings a need is read against: those given, else each tool's probe, read once now. With `after` (UNIX ms),
    only a reading taken after that moment counts — a proof is read after the apply, never from before it — and a tool
    whose given readings are older is probed now."""

    def __init__(self, G, given=None, fresh=True, after=None):
        self.G, self.given, self.fresh, self.read, self.after = G, list(given or []), fresh, {}, after

    def again(self, after=None):
        """The same sources, read afresh: what a tool's probe said a moment ago is not what it says now."""
        return Readings(self.G, self.given, self.fresh, after if after is not None else self.after)

    def _recent(self, r):
        if self.after is None:
            return True
        try:
            return moment_ms(str(r.get('at')).replace('T', ' ')) >= self.after - 1000
        except Exception:      # noqa: BLE001 — a reading that says no moment is no reading after the apply
            return False

    def value(self, name, origin, being):
        """(the value as `{count, unit}` or a text, the reading it came from) for an input, or (None, why)."""
        pool = [r for r in self.given if self._recent(r)]
        tool = origin.get('by') if isinstance(origin, dict) else None
        if not [r for r in pool if norm(r.get('key')) == norm(name)] and self.fresh and tool:
            if tool not in self.read:
                self.read[tool] = [r for r in probe(self.G, tool) if self._recent(r)]
            pool = self.read[tool]
        cands = [r for r in pool if norm(r.get('key')) == norm(name)]
        # THE BEING'S OWN READING FIRST: a key read of several beings (each server's sessions) is read of this one alone,
        # never of a sibling; a key read of one being (the USB drive a walk on the NAS needs) is that being's
        own = [r for r in cands if r.get('being') == being]
        if not own and len({r.get('being') for r in cands}) == 1:
            own = cands
        if not own:
            return None, f"no reading of `{name}`" + (f" by {tool}" if tool else '')
        r = own[0]
        if r.get('quality', 'ok') != 'ok':
            return None, f"`{name}` read {r.get('quality')}: {r.get('why') or 'no reason given'}"
        return r.get('value'), r


def need_rows(G, holder):
    """The needs a bean states that a reading meets: [(need statement, [the reckon ids that meet it])]."""
    b = G.beans.get(str(holder))
    if not b:
        return [], []
    meets = {}
    for r in statements(b, 'meet'):
        meets.setdefault(str(r.get('of')), []).append(str(r.get('by')))
    readings = {str(r.get('id')) for r in statements(b, 'reckon') if r.get('id')}
    read, unread = [], []
    for n in statements(b, 'need'):
        by = [m for m in meets.get(str(n.get('id')), []) if m in readings]
        (read if by else unread).append((n, by))
    return read, unread


def read_needs(G, holder, being, readings, root=ROOT):
    """Each need of `holder` a reading meets, read for `being`: [{need, of, as, holds, why, inputs}] — `holds` True,
    False, or None where it could not be read (an input not given, a reading not known): what is not known does not
    hold, and nothing is forced. Needs sharing an `as` are alternatives: `group_holds` reads them together."""
    import reckon as dmreckon
    b = G.beans.get(str(holder))
    rows, _unread = need_rows(G, holder)
    out = []
    for n, by in rows:
        if n.get('while') is not None and n['while'] in {r.get('id') for r in statements(b, 'reckon')}:
            try:
                if dmreckon.holds(f"{holder}:{n['while']}", root=root) is not True:
                    continue               # needed only while its reading holds: not now
            except Exception:      # noqa: BLE001 — a `while` that cannot be read leaves the need in force
                pass
        verdicts, whys, used = [], [], {}
        for rid in by:
            entry = next((r for r in statements(b, 'reckon') if r.get('id') == rid), {})
            given, missing = {}, []
            for d in (entry.get('reading') or {}).get('inputs') or []:
                if not isinstance(d, dict) or not d.get('name'):
                    continue
                o = d.get('origin') if isinstance(d.get('origin'), dict) else {}
                if o.get('by') in (dmpass.READER, dmpass.GARDEN):
                    continue                # the clock, another garden: the reckoner reads them itself
                v, src = readings.value(d['name'], o, being)
                if v is None:
                    missing.append(src)
                    continue
                given[d['name']] = v
                used[d['name']] = {'value': v, 'at': src.get('at'), 'instrument': src.get('instrument'),
                                   'tool': src.get('tool'), 'property': src.get('property') or d.get('quantity'),
                                   'key': src.get('key'), 'detail': src.get('detail')}
            if missing:
                verdicts.append(None)
                whys.append('; '.join(missing))
                continue
            try:
                v = dmreckon.holds(f"{holder}:{rid}", root=root, inputs=given)
            except Exception as e:      # noqa: BLE001 — a reading that cannot be read is not known, and said
                v = None
                whys.append(f"{rid} not read: {e}")
            verdicts.append(v)
            if v is False:
                whys.append(f"{rid} does not hold (" + ', '.join(f"{k} = {_val(x['value'])}" for k, x in used.items()) + ')')
            elif v is None and not whys:
                whys.append(f"{rid} is not known")
        holds = True if True in verdicts else False if verdicts and all(x is False for x in verdicts) else None
        out.append({'need': n.get('id'), 'of': n.get('of'), 'as': n.get('as'), 'from': n.get('from'), 'holds': holds,
                    'why': '; '.join(whys), 'inputs': used, 'holder': str(holder)})
    return out


def _val(v):
    return f"{v.get('count')} {v.get('unit')}".strip() if isinstance(v, dict) else str(v)


def group_holds(rows):
    """(whether every need holds — alternatives sharing an `as` held by any one — and the needs that do not)."""
    groups = {}
    for r in rows:
        groups.setdefault(r['as'] or f"\0{r['need']}", []).append(r)
    failing = []
    for _k, g in groups.items():
        if not any(r['holds'] is True for r in g):
            failing += g
    return not failing, failing


def interlocks(G, walk, being, readings, root=ROOT):
    """(whether the walk may go on now, the needs that hold it back): the walk's needs, read for the being it acts on."""
    return group_holds(read_needs(G, walk, being, readings, root))


def proof(G, being, readings, root=ROOT):
    """(whether the being's own needs hold, the ones that do not): what a run proves after its verify."""
    return group_holds(read_needs(G, being, being, readings, root))


# ======================================================================================================== crossings
class undone:
    """`with undone(path, …):` — what the block writes in these beans, and the journal entry a refused save leaves
    written and staged for a person to fix, are taken back if the block does not finish (a save refused, a run
    refused): the machine's own write never committed would leave the garden dirty, and its sync waiting on it."""

    def __init__(self, *paths, root=ROOT):
        self.root = root
        journal = os.path.join(root, 'log', 'journal.md')
        self.before = {p: open(p, encoding='utf-8').read() for p in (*paths, journal) if os.path.isfile(p)}
        self.captures = set(self._captures())

    def _captures(self):
        d = os.path.join(self.root, 'captures', 'actions')
        return [os.path.join(d, f) for f in os.listdir(d)] if os.path.isdir(d) else []

    def __enter__(self):
        return self

    def __exit__(self, kind, _value, _tb):
        if kind is not None:
            for p, text in self.before.items():
                with open(p, 'w', encoding='utf-8', newline='\n') as fh:
                    fh.write(text)
            for p in set(self._captures()) - self.captures:      # a run's captures, kept only with its commit
                try:
                    os.remove(p)
                except OSError:
                    pass
            subprocess.run(['git', 'reset', '-q', '--'] + [os.path.relpath(p, self.root) for p in self.before]
                           + (['captures/actions'] if os.path.isdir(os.path.join(self.root, 'captures', 'actions')) else []),
                           cwd=self.root, capture_output=True)
        return False


def mint(b, base):
    ids = {r.get('id') for _i, _v, r in b.items}
    n, out = 1, base
    while out in ids:
        n += 1
        out = f"{base}-{n}"
    return out


def open_fails(b, need):
    """The fails of a need this bean holds (`<need>-<stamp>`, through a measure) that no repair answers."""
    repaired = {str(r.get('of')) for r in statements(b, 'repair')}
    return [r for r in statements(b, 'fail') if str(r.get('id', '')).startswith(f"{need}-")
            and str(r.get('id')) not in repaired and r.get('through')]


def crossing_block(G, bean, row, machine, at_text, holds):
    """The statements a crossing writes in the being's bean, and the ids it mints: the `measure` that showed it, and a
    `fail` through it (not holding) or a `repair` of each fail still open (holding again)."""
    b = G.beans[str(bean)]
    sid = re.sub(r'[^0-9]', '', at_text)[:12]
    block, ids = [], []
    mids = []
    for name, x in (row['inputs'] or {}).items():
        mid = mint(b, f"{row['need']}-{sid}-{norm(name)}"[:120])
        while mid in ids:
            mid += '-x'
        mids.append(mid)
        v = x['value'] if isinstance(x['value'], dict) else {'count': str(x['value']), 'unit': '{item}'}
        prop = x.get('property') or 'number'
        tool = x.get('tool')
        block.append(f"- measure: {{ id: {mid}, by: {machine}, of: self, as: {prop}, value: {{ count: \"{v.get('count')}\", "
                     f"unit: \"{v.get('unit')}\" }}, at: \"{x.get('at') or at_text}\"" + (f", through: {tool}" if tool else '')
                     + f", note: {json.dumps(_note(name, x, row))} }}")
        ids.append(mid)
    if holds:
        for f in open_fails(b, row['need']):
            rid = mint(b, f"{f['id']}-repaired")
            block.append(f"- repair: {{ id: {rid}, by: {machine}, of: {f['id']}, note: \"{row['need']} holds again\" }}")
            ids.append(rid)
        if len(ids) == len(mids):
            return [], []              # nothing was open: nothing is written
    else:
        fid = mint(b, f"{row['need']}-{sid}")
        words = row['of'] if isinstance(row['of'], str) else ', '.join(map(str, listed(row['of'])))
        block.append(f"- fail: {{ id: {fid}, by: self, as: {json.dumps(f'{words}: does not hold')}, "
                     f"through: {mids[0] if mids else row['need']}, at: \"{at_text}\" }}")
        ids.append(fid)
    know = []
    if mids:
        know.append(f"- read: {{ by: {machine}, of: [{', '.join(mids)}], at: now }}")
    rest = [i for i in ids if i not in mids]
    if rest:
        know.append(f"- derive: {{ by: {machine}, of: [{', '.join(rest)}], from: [{', '.join(mids) or row['need']}], at: now }}")
    return block + know, ids


DETAIL_MAX = 600                     # what a measure's note keeps of a reading's words


def _words(text, limit=DETAIL_MAX):
    """A reading's words as one line of a note: every control character a space, at most `limit` characters."""
    s = re.sub(r'\s+', ' ', re.sub(r'[\x00-\x1f\x7f]', ' ', str(text))).strip()
    return s if len(s) <= limit else s[:limit - 1].rstrip() + '…'


def _note(name, x, row):
    return (f"{name} = {_val(x['value'])}, read by {x.get('instrument') or x.get('tool') or 'its probe'}"
            f" (probe key {x.get('key')}) for {row['holder']}#{row['need']}"
            + (f": {_words(x['detail'])}" if x.get('detail') else ''))


def at_now():
    return datetime.datetime.now().astimezone().isoformat(timespec='minutes').replace('T', ' ')


def save(who, what, lines, root=ROOT):
    r = subprocess.run([sys.executable, os.path.join(HERE, 'save.py'), who, what, '--body', '\n'.join(lines)], cwd=root,
                       capture_output=True, text=True, encoding='utf-8', errors='replace')
    if r.returncode != 0:
        raise Refused(f"the save was refused: {(r.stdout + r.stderr).strip()[-800:]}")


def cross(G, readings, root=ROOT, write=True):
    """Every being's needs that a probe reading meets, read now: a need that stops holding writes its crossing once; one
    holding again writes its repair; a remedy walk named for it is proposed. [what changed]."""
    import safe as dmsafe
    machine = host_here(G)
    if machine is None:
        raise Refused("this machine has no bean in the garden (a host named by its hostname): its acts are nobody's")
    walks = {bid for bid in G.beans if is_walk(G, bid)}
    changed, lines, at_text = [], [], at_now()
    remedies, touched, pending = [], [], []
    for bid, b in sorted(G.beans.items()):
        if bid in walks:
            continue                              # a walk's needs are its interlocks, read only when it runs
        rows = [r for r in read_needs(G, bid, bid, readings, root) if r['inputs']]
        for row in rows:
            if row['holds'] is None:
                continue                          # not known: no crossing either way
            was_open = bool(open_fails(b, row['need']))
            if row['holds'] is False and not was_open or row['holds'] is True and was_open:
                block, ids = crossing_block(G, bid, row, machine, at_text, row['holds'])
                if not block:
                    continue
                changed.append({'bean': bid, 'need': row['need'], 'holds': row['holds'], 'ids': ids, 'why': row['why']})
                if write:
                    touched.append(b.path)
                    pending.append((b.path, '\n'.join(block) + '\n'))
                lines.append(f"- action: [[{bid}]] {row['need']} " + ('holds again' if row['holds'] else
                                                                       f"does not hold: {row['why']}"))
                if row['holds'] is False:
                    for rr in statements(b, 'repair'):
                        if rr.get('of') == row['need'] and is_walk(G, rr.get('at')):
                            remedies.append((bid, str(rr['at']), row['need']))
    if write and changed:
        with undone(*sorted(set(touched))):
            for path, block in pending:
                dmsafe.add_statements(path, block)
            save(machine, f"crossings: {', '.join(c['bean'] + ' ' + c['need'] for c in changed)}"[:200], lines, root)
    for bid, walk, need in remedies:
        changed.append(propose(bid, walk, f"{need} does not hold", root) if write else
                       {'bean': bid, 'walk': walk, 'proposed': 'not written'})
    return changed


def propose(bean, walk, why, root=ROOT):
    """A walk placed on the being as a new course — the trigger that proposes it — and its engine run: to its
    person's step (a lead, its plan beside it), or through, where the walk is granted."""
    import act as dmact
    import safe as dmsafe
    G = garden(root)
    machine = host_here(G)
    b = G.beans[str(bean)]
    course = mint(b, f"remedy-{stamp(now_ms(), G.zone)}")
    with undone(b.path):
        dmsafe.add_statements(b.path, f"- be: {{ id: {course}, by: self, at: {walk}, as: order, note: {json.dumps(why)} }}\n"
                                      f"- make: {{ by: {machine}, of: [{course}], at: now }}\n")
        at, said = dmact.engine(bean, course)
    return {'bean': bean, 'walk': walk, 'course': course, 'stopped': at, 'said': said}


# ============================================================================================================ the engine
def in_progress(G, bean, course):
    """Whether a course's last move entered its pause citing `in-progress`: a step under way, run again each tick."""
    moves = [r for r in statements(G.beans[str(bean)], 'move') if r.get('through') == course]
    return bool(moves) and moves[-1].get('as') == 'in-progress'


def course_ids(b, walk, rid):
    return [r.get('id') for r in statements(b, 'be') if r.get('as') == 'order' and str(r.get('at')) == str(walk)
            and str(r.get('id', '')).startswith(f"{rid}-")]


def due(G, at_ms, readings, root=ROOT, here=None):
    """This machine's routines at a moment: [{routine, state, why, occurrence}] — `due` (its window open, its interlocks
    holding), `waits` (its window open, an interlock not holding: which, and the value read), `running` (a course of this
    occurrence stands on its walk), `not due` (the next occurrence), or `not this engine's` (who runs it)."""
    here = here if here is not None else host_here(G)
    out = []
    for rt in routines(G, root):
        if here is not None and rt['machine'] != here:
            continue
        row = {'routine': f"{rt['bean']}#{rt['id']}", 'walk': rt['walk'], 'machine': rt['machine'], 'runner': rt['runner'],
               'schedule': describe(rt), 'zone': rt['zone']}
        try:
            occ = [o for o in occurrences(rt, at_ms, at_ms + 1) if o[0] == 'obligatory']
            nxt = occurrences(rt, at_ms, at_ms + 400 * 86_400_000, limit=1)[:1]
        except dmstale.Unreckoned as e:
            out.append(dict(row, state='not read', why=str(e)))
            continue
        if nxt:
            row['next'] = shown(nxt[0][2], rt['zone'])
        if rt['runner'] != "this machine's engine":
            out.append(dict(row, state="not this engine's", why=rt['runner'] if rt['runner'] != 'nobody' else
                            "no `grant … as: enact` of its walk to this machine, and no register it is present in"))
            continue
        if not occ:
            out.append(dict(row, state='not due'))
            continue
        _v, _cid, b, e = occ[0]
        row['occurrence'] = shown(b, rt['zone'])
        row['window_closes'] = shown(e, rt['zone'])
        course = f"{rt['id']}-{stamp(b, rt['zone'])}"
        if course in course_ids(G.beans[rt['bean']], rt['walk'], rt['id']):
            w = dmseq.where(root, rt['bean'], course)
            out.append(dict(row, state='running' if w.get('step') != 'waits' else 'waits', course=course, step=w.get('step'),
                            why=f"course {course} at {w.get('step')}"))
            continue
        ok, failing = interlocks(G, rt['walk'], rt['bean'], readings, root)
        out.append(dict(row, state='due' if ok else 'waits', course=course,
                        why='' if ok else '; '.join(f"{f['need']} ({f['of']}): {f['why'] or 'not known'}" for f in failing)))
    return out


def advance_notices(G, at_ms, here, root=ROOT):
    """A clause's `notice` — how long before it falls due a reader is told (core/law/measures.yaml `clause`): from that
    much before each occurrence until it starts, the walk's tool tells whoever the run will affect (`<tool> notice <bean>
    <course>`, the course named as the occurrence's will be, so the notice names its real day), and what it said is
    recorded in the being's bean as the machine's `produce` of those words. Once per occurrence. A notice its moment
    passed without (no tick then, or its tool failing) is given at the next tick before the run — late, and said to be
    late — never after the run has started."""
    import act as dmact
    import safe as dmsafe
    done = []
    for rt in routines(G, root):
        if rt['machine'] != here or rt['runner'] != "this machine's engine":
            continue
        for verb, c in rt['clauses']:
            notice = c['clause'].get('notice')
            first = c['clause'].get('due')
            if verb != 'obligatory' or not isinstance(notice, dict) or first is None:
                continue
            try:
                ahead = dmstale._ms_of(dmstale._law('UNITS'), notice, 'the notice')
            except dmstale.Unreckoned:
                ahead = None
            if not ahead:
                continue
            rec = c['clause'].get('every') if isinstance(c['clause'].get('every'), dict) else None
            try:
                occ = dmstale.moments(first, rec, at_ms, at_ms + ahead + 1, zone=rt['zone'], window=WINDOW_MS)
            except dmstale.Unreckoned:
                continue
            for b0, _e in occ:
                if not at_ms < b0 <= at_ms + ahead:
                    continue                      # not yet within its notice, or already started: no notice after the run
                late = b0 - at_ms < ahead - WINDOW_MS
                when = (f"{notice.get('count')} {notice.get('unit')} before it" if not late else
                        f"{(b0 - at_ms) // 3_600_000} h {(b0 - at_ms) // 60_000 % 60} min before it — late: its "
                        f"{notice.get('count')} {notice.get('unit')} passed with no notice given")
                course = f"{rt['id']}-{stamp(b0, rt['zone'])}"
                nid = f"{course}-notice"
                b = garden(root).beans[rt['bean']]
                if nid in {r.get('id') for _i, _v, r in b.items}:
                    continue
                path = next((tool_path(G, str(u.get('of'))) for u in statements(G.beans[rt['walk']], 'use')
                             if tool_path(G, str(u.get('of')))), None)
                if not path:
                    done.append({'routine': f"{rt['bean']}#{rt['id']}", 'did': 'not noticed', 'why': 'its walk uses no tool here'})
                    continue
                code, out = dmact.run_tool(path, 'notice', rt['bean'], course)
                words = ' '.join(out.split())[:400]
                if code != 0:
                    done.append({'routine': f"{rt['bean']}#{rt['id']}", 'did': 'notice failed', 'course': course, 'why': words[-200:]})
                    continue
                tool_bean = next((str(u.get('of')) for u in statements(G.beans[rt['walk']], 'use')
                                  if tool_path(G, str(u.get('of')))), None)
                try:
                    with undone(b.path):
                        dmsafe.add_statements(b.path, f"- produce: {{ id: {nid}, by: {here}, of: {json.dumps(words, ensure_ascii=False)}, "
                                                      f"through: {tool_bean}, note: \"the notice of the run of {shown(b0, rt['zone'])}"
                                                      + (' (late)' if late else '') + f"\" }}\n"
                                                      f"- make: {{ by: {here}, of: [{nid}], at: now }}\n")
                        save(here, f"{rt['bean']} {course}: noticed", [f"- action: [[{rt['bean']}]]'s people told of the run "
                                                                      f"of {shown(b0, rt['zone'])} ({rt['id']}), {when}, by "
                                                                      f"its walk's tool"], root)
                except Refused as e:
                    done.append({'routine': f"{rt['bean']}#{rt['id']}", 'did': 'told, not recorded', 'course': course,
                                 'why': str(e)[:300]})
                    continue
                done.append({'routine': f"{rt['bean']}#{rt['id']}", 'did': 'noticed late' if late else 'noticed', 'course': course})
    return done


def tick(G, at_ms, readings, root=ROOT):
    """The engine, once: each routine of this machine whose window is open is started (a course placed and run), one
    waiting is read again, and one whose window closed while it waited is skipped. [what it did]."""
    import act as dmact
    import safe as dmsafe
    here = host_here(G)
    if here is None:
        raise Refused("this machine has no bean in the garden (a host named by its hostname): its acts are nobody's")
    done = []
    done += advance_notices(G, at_ms, here, root)
    G = garden(root)
    for rt in routines(G, root):
        if rt['machine'] != here:
            continue
        if rt['runner'] == 'two runners':
            done.append({'routine': f"{rt['bean']}#{rt['id']}", 'did': 'refused',
                         'why': f"its walk is granted to this machine AND present in {rt['registers'][0][0]}: two runners "
                                f"would run it twice — the garden says one"})
            continue
        if rt['runner'] != "this machine's engine":
            continue
        b = G.beans[rt['bean']]
        # windows that closed on a run still waiting: skipped
        for c in course_ids(b, rt['walk'], rt['id']):
            w = dmseq.where(root, rt['bean'], c)
            if w.get('step') != 'waits':
                continue
            m = re.search(r'(\d{8})-(\d{4})$', c)
            try:
                near = stamp_ms(m.group(1), m.group(2), rt['zone']) if m else None
                occ = [o for o in occurrences(rt, near - 86_400_000, near + 86_400_000)
                       if stamp(o[2], rt['zone']) == f"{m.group(1)}-{m.group(2)}"] if near is not None else []
            except dmstale.Unreckoned:
                occ = []
            try:
                if occ and occ[0][3] <= at_ms:
                    with undone(b.path):
                        dmact.move(rt['bean'], c, 'skipped', 'window-passed', here,
                                   f"its window closed at {shown(occ[0][3], rt['zone'])} with an interlock still not holding")
                    done.append({'routine': f"{rt['bean']}#{rt['id']}", 'course': c, 'did': 'skipped', 'why': 'window-passed'})
                elif occ:
                    ok, failing = interlocks(garden(root), rt['walk'], rt['bean'], readings.again(), root)
                    if ok or in_progress(garden(root), rt['bean'], c):
                        with undone(b.path):
                            at, said = dmact.resume(rt['bean'], c, readings=readings.again())
                        done.append({'routine': f"{rt['bean']}#{rt['id']}", 'course': c, 'did': 'resumed', 'stopped': at})
            except (dmact.Refused, Refused) as e:
                done.append({'routine': f"{rt['bean']}#{rt['id']}", 'course': c, 'did': 'not moved', 'why': str(e)[:300]})
        G = garden(root)
        b = G.beans[rt['bean']]
        try:
            occ = [o for o in occurrences(rt, at_ms, at_ms + 1) if o[0] == 'obligatory']
        except dmstale.Unreckoned as e:
            done.append({'routine': f"{rt['bean']}#{rt['id']}", 'did': 'not read', 'why': str(e)})
            continue
        for _v, _cid, start, end in occ:
            course = f"{rt['id']}-{stamp(start, rt['zone'])}"
            if course in course_ids(b, rt['walk'], rt['id']):
                continue
            try:
                with undone(b.path):
                    dmsafe.add_statements(b.path, f"- be: {{ id: {course}, by: self, at: {rt['walk']}, as: order, note: \"the "
                                                  f"occurrence of {shown(start, rt['zone'])}, its window to "
                                                  f"{shown(end, rt['zone'])[11:]}\" }}\n- make: {{ by: {here}, of: [{course}], at: now }}\n")
                    at, said = dmact.engine(rt['bean'], course, readings=readings)
            except (dmact.Refused, Refused) as e:
                done.append({'routine': f"{rt['bean']}#{rt['id']}", 'did': 'not started', 'course': course, 'why': str(e)[:300]})
                continue
            done.append({'routine': f"{rt['bean']}#{rt['id']}", 'course': course, 'did': 'started', 'stopped': at})
            G = garden(root)
            b = G.beans[rt['bean']]
    # runs no routine owns — a walk a crossing proposed — waiting at a pause: back as soon as their interlocks hold
    owned = [(rt['bean'], rt['id']) for rt in routines(G, root)]
    for bid, b in sorted(G.beans.items()):
        for r in statements(b, 'be'):
            c = r.get('id')
            if r.get('as') != 'order' or not isinstance(c, str) or not is_walk(G, r.get('at')) \
                    or any(bid == ob and c.startswith(f"{oid}-") for ob, oid in owned):
                continue
            try:
                w = dmseq.where(root, bid, c)
            except Exception:      # noqa: BLE001 — a course this cannot place is the gate's to judge
                continue
            st = next((s for s in statements(G.beans[str(r['at'])], 'step') if s.get('id') == w.get('step')), {})
            if str((st.get('walk') or {}).get('resumes')) != 'true':
                continue
            ok, _failing = interlocks(G, str(r['at']), bid, readings.again(), root)
            if ok or in_progress(G, bid, c):
                try:
                    with undone(b.path):
                        at, _said = dmact.resume(bid, c, readings=readings.again())
                except (dmact.Refused, Refused) as e:
                    done.append({'routine': f"{bid}#{c}", 'course': c, 'did': 'not resumed', 'why': str(e)})
                    continue
                done.append({'routine': f"{bid}#{c}", 'course': c, 'did': 'resumed', 'stopped': at})
                G = garden(root)
    return done


# ================================================================================================= cron: adopt, render
DOW = ['sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
CRON = re.compile(r'^\s*(?P<spec>(?:\S+\s+){4}\S+)\s+(?P<cmd>\S.*?)\s*$')
ENV = re.compile(r'^\s*[A-Za-z_][A-Za-z0-9_]*\s*=')


def _num(s, lo, hi):
    if not re.fullmatch(r'[0-9]+', s) or not lo <= int(s) <= hi:
        raise Refused(f"`{s}` is not a number from {lo} to {hi}")
    return int(s)


def _dows(s):
    """Days of the week of a cron field, as ISO 8601 numbers (Monday 1): `fri`, `5`, `1-5`, `sat,sun`."""
    out = []
    for part in s.lower().split(','):
        ends = part.split('-')
        if len(ends) > 2 or not all(ends):
            raise Refused(f"`{s}` is no day of the week cron writes")
        vals = []
        for x in ends:
            if x in DOW:
                vals.append(DOW.index(x))
            else:
                vals.append(_num(x, 0, 7) % 7)
        rng = range(vals[0], vals[-1] + 1) if len(vals) == 2 else vals
        if len(vals) == 2 and vals[1] < vals[0]:
            raise Refused(f"`{part}` runs backwards")
        out += [7 if d == 0 else d for d in rng]
    return sorted(set(out))


def cron_to_clause(spec, at_day):
    """A cron schedule (five fields) as a clause — `due` (the first occurrence on or after `at_day`, a gregorian day) and
    `every` — or Refused saying why it cannot be said."""
    mi, h, dom, mon, dow = spec.split()
    if dom != '*' or mon != '*':
        if mon == '*' and dow == '*' and re.fullmatch(r'[0-9]+', dom) and re.fullmatch(r'[0-9]+', mi) and re.fullmatch(r'[0-9]+', h):
            d = _num(dom, 1, 31)
            first = next(n for n in range(at_day, at_day + 400) if datetime.date.fromordinal(n).day == d)
            return {'due': _day(first) + f" {_num(h, 0, 23):02d}:{_num(mi, 0, 59):02d}",
                    'every': {'of': 'time', 'in': 'gregorian-civil', 'each': 'month', 'at': str(d)}}
        raise Refused("a day of the month with a month, or with a day of the week, is a schedule this does not say yet")
    m_stride = re.fullmatch(r'\*/([0-9]+)', mi)
    if m_stride and h == '*' and dow == '*':
        n = _num(m_stride.group(1), 1, 59)
        if 60 % n:
            raise Refused(f"`*/{n}` restarts at each hour, so its gaps are not all {n} minutes: no stride says it")
        return {'due': _day(at_day) + ' 00:00', 'every': {'of': 'time', 'every': {'count': str(n), 'unit': 'min'}}}
    if mi == '*' and h == '*' and dow == '*':
        return {'due': _day(at_day) + ' 00:00', 'every': {'of': 'time', 'every': {'count': '1', 'unit': 'min'}}}
    if mi == '*':
        raise Refused("every minute of some hours is a schedule this does not say")
    minute = _num(mi, 0, 59)
    h_stride = re.fullmatch(r'\*/([0-9]+)', h)
    if (h == '*' or h_stride) and dow == '*':
        n = _num(h_stride.group(1), 1, 23) if h_stride else 1
        if 24 % n:
            raise Refused(f"`*/{n}` hours restarts each day, so its gaps are not all {n} hours: no stride says it")
        return {'due': _day(at_day) + f" 00:{minute:02d}", 'every': {'of': 'time', 'every': {'count': str(n), 'unit': 'h'}}}
    hour = _num(h, 0, 23)
    if dow == '*':
        return {'due': _day(at_day) + f" {hour:02d}:{minute:02d}",
                'every': {'of': 'time', 'in': 'gregorian-civil', 'each': 'day'}}
    days = _dows(dow)
    wd = datetime.date.fromordinal(at_day).isoweekday()
    first = min(at_day + ((d - wd) % 7) for d in days)
    return {'due': _day(first) + f" {hour:02d}:{minute:02d}",
            'every': {'of': 'time', 'in': 'iso-week', 'each': 'week', 'at': str(days[0]) if len(days) == 1 else [str(d) for d in days]}}


def _day(n):
    return datetime.date.fromordinal(n).isoformat()


def clause_to_cron(cl):
    """The five cron fields of a clause, spelled one way: numbers without a leading zero, `*/N` for a stride, the day of
    the week by its three letters. Refused for what cron cannot say."""
    every = cl.get('every') or {}
    due = str(cl.get('due') or '')
    m = re.match(r'^(\d{4}-\d{2}-\d{2})[T ](\d{2}):(\d{2})$', due)
    if not m:
        raise Refused(f"`due: {due}` is no clock reading cron can keep (`YYYY-MM-DD HH:MM`, the machine's own time)")
    hh, mm = int(m.group(2)), int(m.group(3))
    st = every.get('every') if isinstance(every.get('every'), dict) else None
    if st:
        n, unit = str(st.get('count')), st.get('unit')
        if unit in ('min', 'minute') and hh == 0 and mm == 0 and 60 % int(n) == 0:
            return "* * * * *" if n == '1' else f"*/{n} * * * *"
        if unit in ('h', 'hour') and hh == 0:
            return f"{mm} * * * *" if n == '1' else f"{mm} */{n} * * *"
        raise Refused(f"a stride of {n} {unit} from {due} is not one cron writes")
    each, at = every.get('each'), every.get('at')
    places = []                     # each place's day; a time of day it names is the due's, the one a cron line keeps
    for a in listed(at):
        try:
            place, clock = dmcal.place_clock(a)
        except ValueError as e:
            raise Refused(str(e)) from None
        if clock is not None and clock != (hh, mm):
            raise Refused(f"`at: {a}` names a time of day of its own, and a cron line keeps one, its due's "
                          f"({hh:02d}:{mm:02d}): one line each, or the same time of day")
        places.append(place)
    if not all(p.isdigit() and p.isascii() for p in places) and not (each == 'day' and not any(places)):
        raise Refused(f"`at: {', '.join(map(str, listed(at)))}` is no day cron writes")
    if each == 'day' and every.get('in') == 'gregorian-civil' and not any(places):
        return f"{mm} {hh} * * *"
    if each == 'week' and every.get('in') == 'iso-week':
        days = [int(x) for x in places] or [datetime.date.fromisoformat(m.group(1)).isoweekday()]
        return f"{mm} {hh} * * " + ','.join(DOW[d % 7] for d in days)
    if each == 'month' and every.get('in') == 'gregorian-civil' and len(places) == 1:
        return f"{mm} {hh} {int(places[0])} * *"
    raise Refused(f"{dmstale.describe(every)} is not a schedule cron writes")


def crontab_lines(text):
    """[(line number, the line, its schedule, its command)] of a crontab's jobs; comments, blank lines and settings are
    not jobs, and are kept by whatever writes the file."""
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith('#') or ENV.match(line):
            continue
        if s.startswith('@'):
            out.append((n, line, None, s))
            continue
        m = CRON.match(line)
        out.append((n, line, m.group('spec') if m else None, m.group('cmd') if m else s))
    return out


def walk_command(G, walk):
    """The command a walk present in a crontab runs: its one step's `as`, as cron runs it."""
    steps = statements(G.beans[str(walk)], 'step') if G.beans.get(str(walk)) else []
    if len(steps) != 1:
        raise Refused(f"{walk} has {len(steps)} steps: a crontab runs one command, a walk of one step")
    return str(steps[0].get('as'))


def render_crontab(live, owned):
    """The crontab the garden says, from the live one: `owned` maps each command a routine of the garden runs to the
    schedule cron should run it at, written as `clause_to_cron` writes it — or to None, where the routine is no longer in
    this crontab (moved to the engine). A live line whose command a routine runs, at the schedule the garden says, is kept
    byte for byte, as it is spelled (`00` and two spaces mean what `0` and one mean, and are not written again); one at
    another schedule is written anew; one moved off cron is taken out; a routine not yet live is added at the end. Every
    other line — a comment, a setting, a job no routine runs — is kept as it is: what the garden does not own it never
    touches, and `check` names it. (the text, [what changed])"""
    out, changes, seen = [], [], set()
    for line in live.splitlines(keepends=True):
        body = line.rstrip('\n')
        jobs = crontab_lines(body)
        if not jobs or jobs[0][2] is None or jobs[0][3] not in owned:
            out.append(line)
            continue
        _n, _l, spec, cmd = jobs[0]
        want = owned[cmd]
        seen.add(cmd)
        try:
            have = clause_to_cron(cron_to_clause(spec, datetime.date.today().toordinal()))
        except Refused:
            have = None
        if want is None:
            changes.append(f"- {body}    (moved off cron)")
        elif have == want:
            out.append(line)
        else:
            out.append(f"{want} {cmd}\n")
            changes.append(f"- {body}\n+ {want} {cmd}")
    if out and not out[-1].endswith('\n'):
        out[-1] += '\n'
    for cmd, want in owned.items():
        if want is not None and cmd not in seen:
            out.append(f"{want} {cmd}\n")
            changes.append(f"+ {want} {cmd}")
    return ''.join(out), changes


def adopt_cron(text, host, user, at_day, crontab_path):
    """A crontab's jobs as routines, PROPOSED: [{n, line, slug, clause, command} or {n, line, refused}]. Each job is
    proved: rendered from what is proposed, the crontab is the live one byte for byte (`render_crontab`), or the line
    is refused with why, never dropped silently."""
    out, used = [], set()
    jobs = crontab_lines(text)
    twice = {}
    for n, _l, s, cmd in jobs:
        if s is not None:
            twice.setdefault(cmd, []).append(n)
    for n, line, spec, cmd in jobs:
        row = {'n': n, 'line': line}
        if spec is None:
            out.append(dict(row, refused="a schedule that is not five fields (`@reboot`, `@daily` …): `@reboot` is the "
                                          "machine's start, not a recurrence, and a name is a spelling this does not read"))
            continue
        if len(twice[cmd]) > 1:
            out.append(dict(row, refused=f"lines {', '.join(map(str, twice[cmd]))} run one command: a routine is known in "
                                          f"the crontab by what it runs — one command, one line — so neither is adopted"))
            continue
        try:
            cl = cron_to_clause(spec, at_day)
            canon = clause_to_cron(cl)
        except Refused as e:
            out.append(dict(row, refused=str(e)))
            continue
        base = re.sub(r'[^a-z0-9]+', '-', os.path.basename(cmd.split()[0]).lower().rsplit('.', 1)[0]).strip('-') or 'job'
        slug, k = f"cron-{base}", 1
        while slug in used:
            k += 1
            slug = f"cron-{base}-{k}"
        used.add(slug)
        out.append(dict(row, slug=slug, clause=cl, command=cmd, canonical=canon,
                        spelled=None if canon == spec else spec))
    owned = {r['command']: r['canonical'] for r in out if not r.get('refused')}
    again, changes = render_crontab(text, owned)
    if again != text:          # the proof: never true unless this code is wrong, and then nothing is proposed
        for r in out:
            if not r.get('refused'):
                r['refused'] = "the crontab rendered from the proposal is not the live one: " + '; '.join(changes)[:300]
    return out


def proposal_text(rows, host, user, crontab_path):
    """The statements a person would save for adopted jobs: for each, a walk (the job as cron runs it, present in the
    crontab) and, in the host's bean, its `run` and its clause."""
    parts = []
    for r in rows:
        if r.get('refused'):
            continue
        cl = r['clause']
        every = _flow(cl['every'])
        parts.append(f"# mappings/{r['slug']}.md (kind procedure) — line {r['n']} of {crontab_path}"
                     + (f", spelled `{r['spelled']}` and kept as spelled" if r.get('spelled') else '') + "\n"
                     f"  - say:  {{ by: <who adopts it>, at: now }}\n"
                     f"  - be:   {{ id: in-crontab, by: self, at: \"{host}:{crontab_path}\", as: presence }}\n"
                     f"  - step: {{ id: run, as: {json.dumps(r['command'])}, by: engine }}\n"
                     f"# beans/{host}.md\n"
                     f"  - run:        {{ id: {r['slug']}, by: self, of: {r['slug']} }}\n"
                     f"  - obligatory: {{ id: {r['slug']}-due, of: {r['slug']}, through: <who asks it>, clause: "
                     f"{{ due: \"{cl['due']}\", every: {every} }} }}\n")
    return '\n'.join(parts)


def _flow(v):
    if isinstance(v, dict):
        return '{ ' + ', '.join(f"{k}: {_flow(x)}" for k, x in v.items()) + ' }'
    if isinstance(v, list):
        return '[' + ', '.join(_flow(x) for x in v) + ']'
    return json.dumps(str(v)) if not re.fullmatch(r'[a-z][a-z0-9-]*', str(v)) else str(v)


def owned_commands(G, host, crontab_path=None, root=ROOT):
    """{command: the cron schedule, or None} of every routine the host runs whose walk is one command: the schedule
    where its walk is present in the crontab, None where it is not (the engine's, or nobody's, now)."""
    owned = {}
    for rt in routines(G, root):
        if rt['machine'] != str(host):
            continue
        try:
            cmd = walk_command(G, rt['walk'])
        except Refused:
            continue
        here = [pos for pos, _sid in rt['registers'] if not crontab_path or pos.endswith(':' + crontab_path) or pos == crontab_path]
        if not here:
            if rt['grant'] and not rt['registers']:
                owned.setdefault(cmd, None)        # moved to the engine: cron runs it no more
            continue
        for verb, c in rt['clauses']:
            if verb == 'obligatory':
                owned[cmd] = clause_to_cron(c['clause'])
    return owned


def render_cron(G, host, crontab_path=None, root=ROOT):
    """[(command, the cron line)] the garden says for a host's crontab."""
    return [(cmd, f"{spec} {cmd}") for cmd, spec in owned_commands(G, host, crontab_path, root).items() if spec]


# ========================================================================================================= the command
def _flag(argv, name, many=False):
    vals = [argv[i + 1] for i, a in enumerate(argv) if a == name and i + 1 < len(argv)]
    return vals if many else (vals[-1] if vals else None)


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    cmd = argv[0] if argv and not argv[0].startswith('--') else 'list'
    as_json = '--json' in argv
    at = _flag(argv, '--at')
    try:
        at_ms = moment_ms(at) if at else now_ms()
    except (ValueError, dmcal.NotByRule) as e:
        print(f"routines: `--at {at}` is no moment: {e}", file=sys.stderr)
        return 2
    try:
        G = garden()
        readings = Readings(G, load_readings(_flag(argv, '--readings', many=True)))
        if cmd == 'list':
            rows = []
            for rt in routines(G):
                try:
                    nxt = occurrences(rt, at_ms, at_ms + 400 * 86_400_000, limit=1)[:1]
                except dmstale.Unreckoned as e:
                    nxt, err = [], str(e)
                else:
                    err = None
                ilk = [{'need': n.get('id'), 'of': n.get('of'), 'read_by': by} for n, by in need_rows(G, rt['walk'])[0]]
                pr = [{'need': n.get('id'), 'of': n.get('of'), 'read_by': by} for n, by in need_rows(G, rt['bean'])[0]]
                unread = [n.get('id') for n, _ in need_rows(G, rt['walk'])[1]]
                rows.append({'routine': f"{rt['bean']}#{rt['id']}", 'machine': rt['machine'], 'walk': rt['walk'],
                             'schedule': describe(rt), 'zone': rt['zone'], 'runner': rt['runner'],
                             'next': shown(nxt[0][2], rt['zone']) if nxt else None,
                             'window': (f"{(nxt[0][3] - nxt[0][2]) // 60000} min") if nxt else None,
                             'interlocks': ilk, 'unread_needs': unread, 'proof': pr,
                             'person_step': rt['person_step'], 'error': err})
            if as_json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
                return 0
            for r in rows:
                print(f"{r['routine']} — {r['walk']} on {r['machine']}: {r['schedule']} ({r['zone']})")
                print(f"  next: {r['next'] or 'none'}" + (f", its window {r['window']}" if r['window'] else '')
                      + (f" — not read: {r['error']}" if r['error'] else ''))
                print(f"  run by: {r['runner']}" + (f"; stops for a person at `{r['person_step']}`" if r['person_step'] else ''))
                for i in r['interlocks']:
                    print(f"  interlock {i['need']}: {i['of']} (read by {', '.join(i['read_by'])})")
                for i in r['unread_needs']:
                    print(f"  need {i}: no reading meets it, so it is not read")
                for p in r['proof']:
                    print(f"  proof {p['need']}: {p['of']} (read by {', '.join(p['read_by'])})")
            print(f"routines: {len(rows)}")
            return 0
        if cmd == 'due':
            rows = due(G, at_ms, readings)
            if as_json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
                return 0
            for r in rows:
                print(f"{r['routine']}\t{r['state']}\t" + (r.get('occurrence') or r.get('next') or '') + (f"\t{r['why']}" if r.get('why') else ''))
            print(f"routines on this machine: {len(rows)}, due {sum(r['state'] == 'due' for r in rows)}, waiting "
                  f"{sum(r['state'] == 'waits' for r in rows)}")
            return 0
        if cmd == 'tick':
            done = tick(G, at_ms, readings)
            print(json.dumps(done, ensure_ascii=False, indent=1) if as_json else
                  '\n'.join(f"{d['routine']}\t{d['did']}\t{d.get('course', '')}\t{d.get('stopped') or d.get('why') or ''}"
                            for d in done) + f"\nroutines: {len(done)} acted on")
            return 0
        if cmd == 'needs':
            if len(argv) < 2:
                raise Refused("needs <bean>")
            holder = argv[1]
            rows = read_needs(G, holder, _flag(argv, '--of') or holder, readings)
            if as_json:
                print(json.dumps(rows, ensure_ascii=False, indent=1))
                return 0
            for r in rows:
                print(f"{r['need']}\t{ {True: 'holds', False: 'DOES NOT HOLD', None: 'not known'}[r['holds']] }\t{r['of']}"
                      + (f"\t{r['why']}" if r['why'] else ''))
            ok, failing = group_holds(rows)
            print(f"needs of {holder}: {len(rows)} read, " + ('all hold' if ok else f"{len(failing)} not holding"))
            return 0 if ok else 1
        if cmd == 'cross':
            done = cross(G, readings, write='--dry-run' not in argv)
            print(json.dumps(done, ensure_ascii=False, indent=1) if as_json else
                  '\n'.join(f"{d.get('bean')}\t{d.get('need') or d.get('walk')}\t"
                            + ('holds again' if d.get('holds') else d.get('stopped') or 'does not hold') for d in done)
                  + f"\ncrossings: {len(done)}")
            return 0
        if cmd == 'tools':
            rows = [{'tool': bid, 'path': tool_path(G, bid)} for bid, b in sorted(G.beans.items())
                    if b.kind == 'program' and tool_path(G, bid)]
            print(json.dumps(rows, ensure_ascii=False, indent=1) if as_json else
                  '\n'.join(f"{r['tool']}\t{r['path']}" for r in rows) + f"\ntools on this machine: {len(rows)}")
            return 0
        if cmd == 'propose':
            if len(argv) < 3 or argv[2].startswith('--'):
                raise Refused("propose <bean> <walk>")
            if argv[1] not in G.beans or not is_walk(G, argv[2]):
                raise Refused(f"{argv[1]} is no bean here, or {argv[2]} no walk")
            got = propose(argv[1], argv[2], _flag(argv, '--why') or 'proposed by a person')
            print(json.dumps(got, ensure_ascii=False, indent=1) if as_json else
                  f"{got['bean']}: course {got['course']} on {got['walk']} — {got['said']}")
            return 0
        if cmd in ('adopt', 'render'):
            if argv[1:2] != ['cron']:
                raise Refused(f"{cmd} reads one register yet: `{cmd} cron` (Task Scheduler, systemd timers and Odoo's "
                              f"ir.cron are its siblings, each a format of its own: not yet written)")
            host = _flag(argv, '--host')
            user = _flag(argv, '--user') or 'root'
            path = _flag(argv, '--crontab') or f"/var/spool/cron/crontabs/{user}"
            if not host:
                raise Refused("--host <the machine's bean>")
            if cmd == 'adopt':
                if len(argv) < 3:
                    raise Refused("adopt cron <crontab file> --host <bean>")
                text = open(argv[2], encoding='utf-8').read()
                day = dmcal.to_day(at[:10]) if at else datetime.date.today().toordinal()
                rows = adopt_cron(text, host, user, day, path)
                if as_json:
                    print(json.dumps(rows, ensure_ascii=False, indent=1))
                else:
                    for r in rows:
                        print(f"line {r['n']}: " + (f"REFUSED — {r['refused']}" if r.get('refused') else
                                                    f"adopted as {r['slug']}: renders byte for byte"))
                    print(proposal_text(rows, host, user, path))
                    print(f"adopt: {sum(1 for r in rows if not r.get('refused'))} of {len(rows)} job line(s) proposed; "
                          f"nothing written")
                return 0 if not any(r.get('refused') for r in rows) else 1
            live = _flag(argv, '--live')
            if not live:
                for _c, line in render_cron(G, host, path):
                    print(line)
                return 0
            text = open(live, encoding='utf-8').read()
            new, changes = render_crontab(text, owned_commands(G, host, path))
            owned = owned_commands(G, host, path)
            unowned = [l for _n, l, s, c in crontab_lines(text) if c not in owned]
            out = _flag(argv, '--write')
            if out:
                with open(out, 'w', encoding='utf-8', newline='') as fh:
                    fh.write(new)
            if as_json:
                print(json.dumps({'changes': changes, 'unowned': unowned, 'same': new == text}, ensure_ascii=False, indent=1))
            else:
                for c in changes:
                    print(c)
                for l in unowned:
                    print(f"  {l}    (no routine of the garden runs it: kept as it is)")
                print(f"render cron: {len(changes)} change(s) to the live crontab, {len(unowned)} line(s) the garden does "
                      f"not own" + (f"; written to {out}" if out else ''))
            return 0 if not changes else 1
        raise Refused(f"no command {cmd!r}: list, due, tick, needs, cross, adopt cron, render cron")
    except Refused as e:
        print(f"routines: NOT DONE: {e}", file=sys.stderr)
        return 1
    except dmstale.Unreckoned as e:
        print(f"routines: not read: {e}", file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
