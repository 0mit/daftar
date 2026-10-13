#!/usr/bin/env python3
"""view_engraved — the archetypes ENGRAVED FROM READINGS (the view finished for a handplace): a queue, a timeline, flows
and a sheet. No drawing module draws them; each is what a reading of the garden says, read each time it is asked and
never stored, and handed to its renderer (`view_queue.js`, `view_timeline.js`, `view_flows.js`, `view_sheet.js`) as data.

    queue(reader, may)        what waits for the reader: bin/leads.py's leads, grouped by what each waits on
    timeline(v, may)          the members of a reading at their moments: a happening's time, a clause's due day and each
                              occurrence of its repetition within the drawing's `span`, walked by bin/stale.py
    flows(v, may)             who owes whom (bin/ledger.py's reading, netted per currency), or what went between gardens
    sheet(bean, may, held)    one being: its header, its statements verb by verb with their dependents, its held values
    table(v, may)             a table of a reading on a page that names no drawing module: one line per member the
                              reader may read, each cell the values at its column's path as they are, each line opening
                              its being's sheet
    data(key, v, may, reader) the reading a drawing of the page draws, by its archetype

ONE QUESTION SCOPES EACH. `may(act, bean, positions=None)` answers whether the reader may read (or write) a being, or
some of its parts: the host's own (view_serve.Host.may), the offline report's (the gardener's, who drew the report). A
being the reader may not read is not named — a lead about it is left out, a debt in an agreement they may not read is
not netted, a party they may not read is drawn as `someone`; the machine that keeps a held value and the gardener
are named, and a default's payer given their title, only to a reader who may read them (what a bean they may read
states of another is its own, as on the rest of the served page) — and a held value is sent only where `held` says it
may be: by the host that holds its store, to a reader who may read that statement (view_serve). The report sends none.

THE LAW GIVES EACH FORM. A sheet carries the rows of the verbs it shows — their roles and the shape that fills each,
their qualifiers, what is required, the default the row derives — so a widget is chosen by shape in the browser and no
field is typed anywhere (core/law/values.yaml says which widget implements which value).
"""
import datetime, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import view_model as vm  # noqa: E402

ENGRAVED = ('queue', 'timeline', 'flows', 'sheet')
KNOWING = ('say', 'read', 'derive', 'make')
LEAD_ORDER = ('decision', 'case', 'obligation', 'health', 'session')
HEADER = ('title', 'summary', 'tags')
SPAN_DAYS = 42                       # a timeline's span where the drawing states none: six weeks (the law's meaning)


def engraved(v):
    """Whether a drawing is engraved from a reading: a queue, a timeline, flows or a sheet always; a table of a reading
    where its page names no drawing module — its lines are the reading's, and nothing is drawn for it but them."""
    if not isinstance(v, dict):
        return False
    return v.get('archetype') in ENGRAVED or (v.get('archetype') == 'table' and not vm.page_view().get('drawings'))


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _bean(bid):
    return vm.CORE.G.beans.get(bid) if vm.CORE is not None and isinstance(bid, str) else None


def title_of(bid):
    """How a being is called on a page: its title — and where its title is only its id, or its id and words after it
    (`<id> — <words>`), the words, else (but for a person) its summary's first sentence: an id is no name a reader
    reads. A person kept under an opaque id stays it here, and a page calls them by what they are (`opaque`)."""
    b = _bean(bid)
    t = b.header.get('title') if b is not None else None
    if not (isinstance(t, str) and t.strip()):
        return bid
    t = t.strip()
    if t == bid or t.startswith(bid + ' '):
        rest = t[len(bid):].strip().lstrip('—–-:').strip()
        if rest:
            return rest
        if b.kind == 'person':                  # a person kept under an opaque id is called by what they are, never by
            return t                            # words about them; a host that keeps their name gives it (`opaque`)
        summary = b.header.get('summary')
        if isinstance(summary, str) and summary.strip():
            first = re.split(r'(?<=[.!?؟])\s', summary.strip(), maxsplit=1)[0]
            return first if len(first) <= 80 else first[:79].rstrip() + '…'
    return t


def today():
    return datetime.date.today()


# --------------------------------------------------------------------------------------------------------------- queue
def queue(reader, may):
    """What waits for `reader`, as bin/leads.py reads it: each lead for them, grouped in the order decision, case,
    obligation, health, session; within a group the most urgent first (an obligation by the days left, a case overdue
    before one in time). A lead about a being the reader may not read is left out."""
    import leads as dmleads
    out = []
    for x in dmleads.read(vm.ROOT):
        if x.get('for') != reader:
            continue
        about = x.get('about')
        if _bean(about) is not None and not may('read', about):
            continue
        out.append(dict(x, title=title_of(about) if _bean(about) is not None else None, opens=about if _bean(about) is not None else None,
                        **said_of(x)))

    def urgency(x):
        k = x.get('kind')
        g = LEAD_ORDER.index(k) if k in LEAD_ORDER else len(LEAD_ORDER)
        if k == 'obligation':
            return (g, int(x.get('days') or 0), str(x.get('about')))
        if k == 'case':
            return (g, 0 if x.get('overdue') else 1, str(x.get('since') or ''), str(x.get('about')))
        return (g, str(x.get('since') or ''), str(x.get('about')))
    out.sort(key=urgency)
    return {'reader': reader, 'groups': [k for k in LEAD_ORDER if any(x.get('kind') == k for x in out)], 'leads': out}


def said_of(x):
    """What a lead's sentence says, read from the garden, for the reader's language to say it in (view_queue.js composes
    it from the widgets' sentences; bin/leads.py's own `why` is its English, kept beside): a case's step by its walk's
    own words; a clause by its words and the day it falls due, as a day of the Gregorian calendar the widgets convert
    from (a day written in another calendar, or as an ISO week's day, is read by bin/stale.py); a failure by its `as`."""
    k, out = x.get('kind'), {}
    if k == 'case' and isinstance(x.get('walk'), str):
        steps = (vm.fm(x['walk'], 'mappings') or vm.fm(x['walk'])).get('steps') or []
        st = next((s for s in steps if isinstance(s, dict) and s.get('id') == x.get('step')), {})
        if st.get('do'):
            out['step_says'] = str(st['do'])
    elif k == 'obligation':
        b = _bean(x.get('about'))
        if b is not None:
            from core import measures
            e = (measures.clauses_of(b, vm.ROOT) or {}).get(x.get('clause')) or {}
            w = e.get('what')
            if isinstance(w, str) and w and w not in {r.get('id') for _i, _v, r in b.items if isinstance(r, dict)}:
                out['what'] = w                       # words, never a statement's id standing in for them
        if x.get('due') is not None:
            m = _moment(str(x['due']))
            if m:
                out['day'] = m[0]
    elif k == 'health':
        b = _bean(x.get('about'))
        f = next((r for _i, v, r in (b.items if b is not None else []) if v == 'fail' and isinstance(r, dict)
                  and r.get('id') == x.get('fail')), None)
        if f and isinstance(f.get('as'), str):
            out['fails_as'] = f['as']
    return out


# ------------------------------------------------------------------------------------------------------------ timeline
def span_days(v):
    """How many days a timeline reaches on each side of today: its `span`, a length on time, else six weeks."""
    s = vm.seconds(v.get('span')) if isinstance(v.get('span'), dict) else None
    return SPAN_DAYS if not s else max(1, int(s // 86400))


def _moment(x):
    """(day, time) of a position a statement holds: its day as bin/stale.py reads it, in whatever calendar it is written
    (`2026-10-16 19:00+03:00`, `persian:1405-07-09` — no calendar privileged), as the Gregorian day a page converts from,
    and the time of day where it states one; an extent (`a/b`, a stay, a session) at its start. None for anything else:
    a place, a port, a day nobody said (`after:<bean>`)."""
    import stale as dmstale
    if not isinstance(x, str):
        return None
    head = x.split('/')[0] if not re.match(r'^[a-z][a-z0-9-]*:', x) or re.match(r'^[a-z][a-z0-9-]*:\d', x) else x
    try:
        n = dmstale.day_of(head)
    except Exception:                            # no day of a calendar: not placed on a timeline
        return None
    t = re.search(r'[T ](\d{2}:\d{2})', head)
    return datetime.date.fromordinal(n).isoformat(), (t.group(1) if t else None)


def timeline(v, may, on=None):
    """The members of the drawing's reading (`selection`) at their moments within its span: each happening's time (a `be`
    of it at a moment), and each clause's due day and every occurrence of its repetition, walked by bin/stale.py's
    `occurrences`. A member the reader may not read is left out; what cannot be walked is said, never guessed."""
    import stale as dmstale
    from core import measures
    day0 = on or today()
    n0 = day0.toordinal()
    reach = span_days(v)
    lo, hi = n0 - reach, n0 + reach
    events, notes = [], []
    try:
        members = vm.members(v['selection']) if v.get('selection') else []
    except Exception as e:                      # a reading the gate passed and this cannot read: said
        members, notes = [], [f"the reading {v.get('selection')} is not read: {e}"]
    for bid in members:
        b = _bean(bid)
        if b is None or not may('read', bid):
            continue
        t = title_of(bid)
        times = {}                              # a statement's own time of day, by its id: what a repetition of it keeps
        sessions = {}                           # the days a statement's own session is on, by its id
        for _i, verb, r in b.items:
            # A HAPPENING'S TIME: its `be` at a moment, or an attendance at its own moment (`attend … at`: a session of a
            # series, a sitting moved to another day) — each placed once, at the day of its own calendar
            if not isinstance(r, dict) or 'held' in r:
                continue
            if not (verb == 'be' and r.get('by') in ('self', bid) or verb == 'attend' and r.get('of') in ('self', bid)):
                continue
            for x in _listed(r.get('at')):
                m = _moment(x)
                if m and isinstance(r.get('id'), str):
                    times.setdefault(r['id'], m[1])
                    sessions.setdefault(r['id'], set()).add(m[0])
                if m and lo <= datetime.date.fromisoformat(m[0]).toordinal() <= hi and \
                        not any(e['bean'] == bid and e['day'] == m[0] and e['time'] == m[1] for e in events):
                    events.append({'day': m[0], 'time': m[1], 'at': x, 'bean': bid, 'title': t, 'kind': 'happening',
                                   'statement': r.get('id')})
        for cid, e in (measures.clauses_of(b, vm.ROOT) or {}).items():
            if not isinstance(e, dict) or e.get('state') in ('met', 'waived', 'broken') or e.get('due') is None:
                continue
            try:
                first = dmstale.day_of(e['due'])
            except Exception as why:            # a day this cannot read: said, as stale says it
                notes.append(f"{bid} {cid}: its due day {e['due']} is not walked here: {why}")
                continue
            rec = e.get('every') if isinstance(e.get('every'), dict) else None
            # A REPETITION OF A STATEMENT (a series' sessions: `can { of: <its attend> }` with an `every`): each occurrence
            # at that statement's own time of day, and its words the being's, never the statement's id
            of_statement = e.get('what') in times
            base = {'bean': bid, 'title': t, 'kind': 'due', 'clause': cid, 'what': None if of_statement else e.get('what'),
                    'by': e.get('by'), 'to': e.get('to'), 'amount': e.get('amount'), 'permission': e.get('permission'),
                    'at_time': times.get(e.get('what')) if of_statement else None}
            if rec is None:
                if lo <= first <= hi:
                    events.append(dict(base, day=datetime.date.fromordinal(first).isoformat(), time=base['at_time'], index=1, times='1'))
                continue
            try:
                for i, n in enumerate(dmstale.occurrences(first, rec), 1):
                    if n > hi:
                        break
                    day = datetime.date.fromordinal(n).isoformat()
                    # a series' occurrence on the day of its own statement's session is that session, drawn already; any
                    # other clause is drawn whatever else its being has that day (a rent due on the day of a meeting)
                    if n >= lo and not (of_statement and day in sessions.get(e.get('what'), ())):
                        events.append(dict(base, day=day, time=base['at_time'], index=i,
                                           times=None if rec.get('times') is None else str(rec.get('times'))))
            except dmstale.Unreckoned as why:
                notes.append(f"{bid} {cid}: its repetition is not walked here: {why}")
    events.sort(key=lambda x: (x['day'], x.get('time') or '', x['bean'], str(x.get('clause') or x.get('statement'))))
    return {'today': day0.isoformat(), 'from': datetime.date.fromordinal(lo).isoformat(),
            'to': datetime.date.fromordinal(hi).isoformat(), 'layouts': list(v.get('layouts') or ['week', 'month', 'list']),
            'events': events, 'notes': notes}


# --------------------------------------------------------------------------------------------------------------- flows
def flows(v, may):
    """What flows draw. `nodes: parties` — bin/ledger.py's reading of the agreements the drawing's reading holds (every
    agreement, where it names none) that the reader may read, netted across them per currency: an arrow from the one who
    owes to the one owed. `nodes: gardens` — this garden and each it records, an arrow for what went between them."""
    if v.get('nodes') == 'gardens':
        return crossings(may)
    import ledger as dmledger
    if v.get('selection'):
        try:
            chosen = vm.members(v['selection'])
        except Exception:
            chosen = []
    else:
        chosen = sorted(k for k, b in vm.CORE.G.beans.items() if not b.unread and any(vb == 'pay' for _i, vb, _r in b.items))
    seen = [k for k in chosen if _bean(k) is not None and may('read', k)]
    reading = dmledger.reading(seen)
    names, n = {}, 0
    for row in reading['net']:
        for p in (row['from'], row['to']):
            if p not in names:
                if _bean(p) is not None and may('read', p):
                    names[p] = {'id': p, 'title': title_of(p)}
                else:
                    n += 1
                    names[p] = {'id': None, 'title': None, 'someone': n}
    arrows = [dict(r, **{'from': names[r['from']]['id'] or f"someone-{names[r['from']]['someone']}",
                         'to': names[r['to']]['id'] or f"someone-{names[r['to']]['someone']}"}) for r in reading['net']]
    nodes = [dict(x, id=x['id'] or f"someone-{x['someone']}") for x in names.values()]
    return {'nodes_are': 'parties', 'nodes': nodes, 'arrows': arrows, 'partial': reading['partial'],
            'agreements': [{'bean': a['bean'], 'title': a['title'], 'debts': a['debts']} for a in reading['agreements']],
            'unread': sorted(reading['unread'])}


def crossings(may):
    """Gardens as nodes: this garden, and each garden a `take` here came from, a `propose` here went to, or a `pass`
    names as its `by`; an arrow for each way, with the beans that went. A garden is called by its title — never its id:
    this garden is the one the page is read in (`here`, no title), and one whose bean says no more of it than its id is
    `unnamed`, the page calling it another garden (`n`, its place among them where there are several)."""
    here = vm.garden_name()
    nodes, arrows, unnamed = {here: {'id': here, 'title': None, 'here': True}}, {}, []

    def node(g):
        if g not in nodes:
            t = title_of(g) if may('read', g) else None
            nodes[g] = {'id': g, 'title': t}
            if t == g:
                nodes[g].update(title=None, unnamed=True)
                unnamed.append(g)
        return g
    for bid, b in sorted(vm.CORE.G.beans.items()):
        if not may('read', bid):
            continue
        for _i, verb, r in b.items:
            if not isinstance(r, dict) or 'held' in r:
                continue
            if verb == 'take' and isinstance(r.get('from'), str):
                k = (node(r['from']), here)
                arrows.setdefault(k, set()).add(bid)
            elif verb == 'propose' and isinstance(r.get('to'), str):
                k = (here, node(r['to']))
                arrows.setdefault(k, set()).update(x for x in _listed(r.get('of')) if isinstance(x, str))
            elif verb == 'pass' and 'other-garden' in (r.get('from'), r.get('to')) and isinstance(r.get('by'), str):
                k = (node(r['by']), here) if r.get('from') == 'other-garden' else (here, node(r['by']))
                arrows.setdefault(k, set()).update(x for x in _listed(r.get('of')) if isinstance(x, str))
    if len(unnamed) > 1:
        for i, g in enumerate(unnamed, 1):
            nodes[g]['n'] = i
    return {'nodes_are': 'gardens', 'nodes': list(nodes.values()),
            'arrows': [{'from': a, 'to': b, 'what': sorted(w)} for (a, b), w in sorted(arrows.items())],
            'partial': False}


# --------------------------------------------------------------------------------------------------------------- table
def table(v, may):
    """A table of a reading with no module to draw it: one line per member of its `selection` the reader may read —
    the whole being, or every part its columns read, as a grant's `cover` may open parts alone — each cell the values
    at its column's path AS THEY ARE (a day, an amount, a being, text; a step a move reached by its walk's own words),
    for the line's widgets to show in the reader's calendar and digits, and each line opening its being's sheet. A table of a series is drawn by its module."""
    import reckon as dmreckon
    cols = [{'label': str(c.get('label') or c.get('path')), 'path': str(c.get('path'))}
            for c in v.get('columns') or [] if isinstance(c, dict) and c.get('path')]
    reads = sorted({re.split(r"[.\[>]", c['path'])[0] for c in cols if c['path'] not in ('at', 'position')})
    out = {'columns': cols, 'rows': [], 'notes': []}
    try:
        members = vm.members(v['selection']) if v.get('selection') else []
    except Exception as e:                      # a reading the gate passed and this cannot read: said
        members, out['notes'] = [], [f"the reading {v.get('selection')} is not read: {e}"]
    for m in members:
        if _bean(m) is None or not (may('read', m) or (reads and may('read', m, reads))):
            continue
        out['rows'].append({'bean': m, 'title': title_of(m),
                            'cells': [_steps_said(dmreckon.path_values(vm.fm(m), c['path'], root=vm.ROOT)) for c in cols]})
    return out


_STEP = re.compile(r'([a-z0-9][a-z0-9-]*)#([A-Za-z0-9][A-Za-z0-9_.-]*)')


def _steps_said(v):
    """A cell's values, a step of a walk (`<walk>#<step>`, where a move reached) said by the walk's own words for it,
    as the walk writes them; every other value as it is."""
    if isinstance(v, list):
        return [_steps_said(x) for x in v]
    m = _STEP.fullmatch(v) if isinstance(v, str) else None
    if m:
        steps = (vm.fm(m.group(1), 'mappings') or vm.fm(m.group(1)) or {}).get('steps') or []
        st = next((s for s in steps if isinstance(s, dict) and s.get('id') == m.group(2)), {})
        if st.get('do'):
            return str(st['do'])
    return v


# --------------------------------------------------------------------------------------------------------------- sheet
def verb_row(verb):
    """The row of a verb as a form is derived from it: its roles and qualifiers, each with the shapes that fill it,
    `many`, the table a row is chosen from (and its rows, where the law keeps them), the nature and kind it narrows to;
    what is required; one of a choice; the default it derives, in words. Nothing here is typed for a page."""
    L = vm.CORE.L
    row = L.verbs.get(verb) or {}

    def spec(s):
        s = s if isinstance(s, dict) else {}
        out = {'shape': [str(x) for x in _listed(s.get('shape'))]}
        for k in ('many', 'keyed', 'nature', 'rung', 'kind', 'form', 'table'):
            if s.get(k) is not None:
                out[k] = s[k] if k in ('nature', 'kind') else str(s[k])
        if s.get('table') and str(s['table']) not in getattr(L, 'standard_tables', ()):
            rows = L.table(str(s['table']))
            if isinstance(rows, list) and len(rows) <= 200:
                out['rows'] = [str(x) for x in rows]
        return out
    d = row.get('default') if isinstance(row.get('default'), dict) else None
    return {'verb': verb, 'meaning': str(row.get('meaning') or ''),
            'roles': {k: spec(s) for k, s in (row.get('roles') or {}).items()},
            'qualifiers': {k: spec(s) for k, s in (row.get('qualifiers') or {}).items()},
            'required': [str(x) for x in _listed(row.get('required'))],
            'one_of': [str(x) for x in _listed((row.get('choice') or {}).get('one_of'))] if isinstance(row.get('choice'), dict) else [],
            'default': {'says': str(d.get('says') or ''), 'fill': d.get('fill'), 'when': d.get('when'),
                        'alone': bool(d.get('alone'))} if d else None}


def value_of(dom, rows=None):
    """The value of the values tree (core/law/values.yaml) an attribute of a form holds, read from its domain in the law:
    a position is the value written as a position (`written: position`), a length of time `duration`, any other quantity
    `quantity`, a table's rows or a key of the bean's own (its readings, its clauses) a `choice`, prose `text`, a pattern
    or a path a `name`, a nested form its own entries. The browser draws it by the widget that implements that value."""
    L = vm.CORE.L
    written = {str(r.get('written')): v for v, r in (getattr(L, 'values', None) or {}).items() if r.get('written')}
    if isinstance(dom, dict) and 'in' in dom and len(dom) <= 3 and not ({'type', 'quantity', 'key_of', 'pattern', 'entries'} & set(dom)):
        dom = dom['in']                                  # an entry's own record: its domain is its `in`
    if dom in ('extent', 'recurrence'):
        return {'value': dom}
    if dom == 'prose' or dom is None:
        return {'value': 'text'}
    if isinstance(dom, list):
        return {'value': 'choice', 'rows': [str(x) for x in dom]}
    if isinstance(dom, dict):
        if 'quantity' in dom:
            return {'value': 'duration' if dom['quantity'] == 'duration' else 'quantity'}
        if 'key_of' in dom:
            return {'value': 'choice', 'rows': list((rows or {}).get(dom['key_of']) or [])}
        if dom.get('type') == 'clause':
            return {'value': 'statement', 'rows': list((rows or {}).get('clauses') or [])}
        if dom.get('type') in written:
            return {'value': written[dom['type']]}
        if 'entries' in dom:
            return dict(form_def_of(dom, rows), value='form')
        return {'value': 'name'}
    return {'value': 'text'}


def form_def_of(rec, rows=None):
    attrs = rec.get('attrs') or rec.get('entries') or {}
    return {'attrs': {str(k): dict(value_of(a, rows), required=str(a.get('required')) == 'true' if isinstance(a, dict) else False)
                      for k, a in attrs.items()},
            'one_of': [str(x) for x in _listed(rec.get('one_of'))], 'keyed_by': [str(x) for x in _listed(rec.get('keyed_by'))]}


def form_def(name, b=None):
    """A form of the law (`clause`, `settlement`, …) as a sheet's widget draws it: each attribute and the value it holds;
    a choice of the bean's own — its readings (`key_of: selections`), its clauses — given its rows from the bean."""
    rec = (vm.CORE.L.forms or {}).get(name)
    if not isinstance(rec, dict):
        return None
    rows = {}
    if b is not None:
        rows['selections'] = sorted(r['id'] for _i, v, r in b.items if v == 'reckon' and isinstance(r.get('id'), str))
        from core import measures
        rows['clauses'] = sorted((measures.clauses_of(b, vm.ROOT) or {}).keys())
    return dict(form_def_of(rec, rows), name=name)


def statement_key(verb, r, nth):
    """The key a statement is named by, as bin/safe.py names it: `<verb>#<id>`, or `<verb>@<n>` where it has no id."""
    return f"{verb}#{r['id']}" if isinstance(r.get('id'), str) else f"{verb}@{nth}"


def held_host(pointer):
    """The host whose `roots` declare the store a held pointer names, and the root's name: where it is kept."""
    m = re.match(r'^root:([a-z0-9][a-z0-9-]*)/', str(pointer))
    if not m:
        return None
    import garden as dmgarden
    for bid, b in sorted(vm.CORE.G.beans.items()):
        roots = (dmgarden.terms(b, vm.CORE.G.beans).get('roots') or {}) if b.kind == 'host' else {}
        if isinstance(roots, dict) and isinstance(roots.get(m.group(1)), dict) and roots[m.group(1)].get('keeps'):
            return bid
    return None


def facts_shown(kind):
    """The facts the page's `fields` names for a kind, in the page's order: [(fact, lens it is shown from)]."""
    return [(str(e.get('term')), str(e.get('shown_from') or '')) for _i, e in vm.entries_of_view('fields')
            if str(e.get('genos')) == str(kind) and e.get('term')]


def labels_shown(kind):
    """What the page calls each fact it names for a kind, in its own words (`fields` … `label`): {fact: label}."""
    return {str(e.get('term')): str(e['label']) for _i, e in vm.entries_of_view('fields')
            if str(e.get('genos')) == str(kind) and e.get('term') and isinstance(e.get('label'), str) and e['label'].strip()}


def details_at(b, fact):
    """What `details` keeps at a fact a page names: a key of it, or a path into it (`case.opened_on`),
    as it is held; None where it keeps nothing there."""
    node = b.header.get('details')
    for part in fact.split('.'):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


_REF = re.compile(r'([a-z0-9][a-z0-9-]*)#([A-Za-z0-9][A-Za-z0-9_.-]*)')


def words_of(b, sid, depth=0):
    """The words a statement is said by, for a reader who never reads its id: a step's `as`; a clause or a figure by what
    it is `of` (the words of the statement it is of, or its own words); a course on a walk by the walk's title; any other
    by its `as` or its note. None where it has no words."""
    r = next((r for _i, _v, r in b.items if isinstance(r, dict) and r.get('id') == sid), None) if b is not None else None
    if r is None or depth > 3:
        return None
    v = next(v for _i, v, x in b.items if x is r)
    if v == 'be' and r.get('as') == 'order' and _bean(r.get('at')) is not None:
        return title_of(r['at'])
    of = r.get('of')
    if isinstance(of, str) and of != 'self':
        if any(isinstance(x, dict) and x.get('id') == of for _i, _v, x in b.items):
            return words_of(b, of, depth + 1)
        if v not in ('move', 'concern', 'own') and _bean(of) is None:
            return of
    if v == 'step' and isinstance(r.get('as'), str) and r['as'].strip():
        return r['as']
    if isinstance(r.get('note'), str) and r['note'].strip():
        return r['note']
    return None


def said_refs(b, values):
    """{reference: words} for every statement a value names — `<bean>#<id>` (a walk's step), or an id of a statement of
    this bean — that has words."""
    out = {}

    def walk(x):
        if isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            for y in x.values():
                walk(y)
        elif isinstance(x, str) and x not in out:
            m = _REF.fullmatch(x)
            w = words_of(_bean(m.group(1)), m.group(2)) if m else words_of(b, x) if any(
                isinstance(r, dict) and r.get('id') == x for _i, _v, r in b.items) else None
            if w:
                out[x] = w
    walk(values)
    return out


def courses_of(b):
    """{course id: {walk, steps: [{ref, says}]}} — each walk the being is on (`be { id, at: <walk>, as: order }`), its
    steps in their order, each by its own words: what a move of it may reach."""
    out = {}
    for _i, v, r in b.items:
        if v == 'be' and isinstance(r, dict) and r.get('as') == 'order' and isinstance(r.get('id'), str):
            w = _bean(r.get('at'))
            if w is None:
                continue
            steps = [{'ref': f"{r['at']}#{x['id']}", 'says': str(x.get('as') or x['id'])}
                     for _j, sv, x in w.items if sv == 'step' and isinstance(x, dict) and isinstance(x.get('id'), str)]
            if steps:
                out[r['id']] = {'walk': r['at'], 'title': title_of(r['at']), 'steps': steps}
    return out


def sheet(bid, may, held=None):
    """One being as its sheet shows it: its header facts, then each verb the page's `fields` names for its kind, its
    statements of that verb in the order the bean holds them, each with the statements that take it as their `of`
    beneath it, who knows it (its knowing act) and, sealed, where it is kept — its roles only where `held(bean, sid)`
    gives them. `may` decides what is sent and what is offered to write: the whole bean, or the parts a grant covers."""
    b = _bean(bid)
    if b is None or not may('read', bid):
        return None
    L = vm.CORE.L
    whole_write = may('write', bid)
    items = [(i, v, r) for i, v, r in b.items if isinstance(r, dict)]
    nth, keyed = {}, []
    for i, v, r in items:
        keyed.append((statement_key(v, r, nth.get(v, 0)), i, v, r))
        if not isinstance(r.get('id'), str):
            nth[v] = nth.get(v, 0) + 1
    by_id = {r['id']: k for k, _i, _v, r in keyed if isinstance(r.get('id'), str)}
    covered = {}
    uncovered_act = None
    for k, _i, v, r in keyed:
        if v in KNOWING:
            ofs = [x for x in _listed(r.get('of')) if isinstance(x, str)]
            for x in ofs:
                covered.setdefault(x, (v, r))
            if not ofs:
                uncovered_act = uncovered_act or (v, r)

    def known(r):
        act = covered.get(r.get('id')) if isinstance(r.get('id'), str) else None
        act = act or uncovered_act
        if not act:
            return None
        v, a = act
        at = next((x for x in _listed(a.get('at')) if isinstance(x, str)), None)
        return {'act': v, 'by': a.get('by') if isinstance(a.get('by'), str) else None, 'at': at}

    def may_part(p):
        return whole_write or may('write', bid, [p])

    def one(k, v, r):
        out = {'key': k, 'verb': v, 'id': r.get('id') if isinstance(r.get('id'), str) else None, 'known': known(r),
               'may': may_part(r['id'] if isinstance(r.get('id'), str) else v)}
        if 'held' in r:
            sid = r.get('id')
            value = held(bid, sid, r) if held and isinstance(sid, str) else None
            host = held_host(r['held'])
            host = host if host and may('read', host) else None   # else "kept on a machine this page does not name"
            out['held'] = {'host': host, 'while': r.get('while'), 'here': value is not None}
            if value is not None:
                out['roles'] = value
        else:
            out['roles'] = {x: y for x, y in r.items() if x != 'id'}
        return out

    shown = facts_shown(b.kind)
    verbs_shown = [f for f, _l in shown if f in L.verbs]
    dependents, nested = {}, set()
    for k, _i, v, r in keyed:
        if v in KNOWING or 'held' in r:
            continue
        for x in _listed(r.get('of')):
            if isinstance(x, str) and x in by_id and by_id[x] != k:
                dependents.setdefault(by_id[x], []).append((k, v, r))
                nested.add(k)
    derived = defaults_of(bid, may)
    rows = []
    for f in verbs_shown:
        sts = []
        for k, _i, v, r in keyed:
            if v != f or k in nested:
                continue
            s = one(k, v, r)
            s['dependents'] = [one(dk, dv, dr) for dk, dv, dr in dependents.get(k, [])]
            s['defaults'] = derived.get(r.get('id'), []) if isinstance(r.get('id'), str) else []
            sts.append(s)
        rows.append({'verb': f, 'statements': sts, 'may_add': may_part(f)})
    verbs = sorted(set(verbs_shown) | {dv for ds in dependents.values() for _k, dv, _r in ds})
    header = {h: b.header.get(h) for h in HEADER if h in [f for f, _l in shown] or h == 'title'}
    forms = sorted({s['form'] for v in verbs for s in list(verb_row(v)['roles'].values()) + list(verb_row(v)['qualifiers'].values())
                    if s.get('form')})
    details = {f: details_at(b, f) for f, _l in shown if f not in L.verbs and f not in HEADER}
    return {'bean': bid, 'kind': b.kind, 'title': title_of(bid), 'forms': {f: form_def(f, b) for f in forms},
            'header': {h: {'value': x, 'may': may_part(h)} for h, x in header.items()},
            'details': {f: x for f, x in details.items() if x is not None},
            'labels': labels_shown(b.kind),
            'said': said_refs(b, [s.get('roles') for r in rows for s in r['statements']]
                              + [d.get('roles') for r in rows for s in r['statements'] for d in s['dependents']]),
            'courses': courses_of(b),
            'rows': rows, 'verbs': {v: verb_row(v) for v in verbs}, 'may_write': whole_write,
            'statements': sorted(by_id), 'new': False}


def defaults_of(bid, may=None):
    """{statement id: [default]} — what the law derives beside a statement where nothing is written, as the reading that
    applies it says: a payment bin/ledger.py reads as borne by its payer alone carries the default of the verb whose
    default fills its `by` from the statement it is `of` (`bear`: whoever paid bears it, alone), in the row's words. The
    payer is the payment's own word; their title is sent only where `may` lets the reader read them."""
    L = vm.CORE.L
    w = next((v for v, row in sorted(L.verbs.items()) if isinstance(row.get('default'), dict)
              and isinstance(row['default'].get('fill'), dict) and isinstance(row['default']['fill'].get('by'), dict)
              and row['default']['fill']['by'].get('the') == 'of'), None)
    if w is None or _bean(bid) is None or not any(v == 'pay' for _i, v, _r in _bean(bid).items):
        return {}
    import ledger as dmledger
    d = L.verbs[w]['default']
    out = {}
    for ag in dmledger.reading([bid])['agreements']:
        for t in ag['transactions'] + ag.get('asked', []):     # a payment made, or one a clause asks
            payers = [x['by'] for x in t.get('paid') or []]
            if t.get('borne_by_payer') and len(payers) == 1:
                shown = may is None or may('read', payers[0])
                out[t['id']] = [{'verb': w, 'says': str(d.get('says') or ''), 'by': payers[0],
                                 'title': title_of(payers[0]) if shown else None, 'alone': bool(d.get('alone'))}]
    return out


def blank(kind, may):
    """An empty sheet of a kind, for a new being: the facts the page shows for the kind, no statements, and the rows of
    their verbs; it may be written only where the reader may make a being (`may('write', '')`: a being no grant names
    yet, the gardener's alone)."""
    L = vm.CORE.L
    shown = facts_shown(kind)
    verbs = [f for f, _l in shown if f in L.verbs]
    allowed = may('write', '')
    return {'bean': None, 'kind': kind, 'title': None, 'new': True, 'may_write': allowed,
            'header': {h: {'value': None, 'may': allowed and not (h == 'title' and kind == 'person')}
                       for h in HEADER if h == 'title' or h in [f for f, _l in shown]},
            'details': {}, 'rows': [{'verb': f, 'statements': [], 'may_add': allowed} for f in verbs],
            'verbs': {v: verb_row(v) for v in verbs}, 'statements': []}


# ---------------------------------------------------------------------------------------------------- the page's part
def axes_of(v):
    """Where each order runs on a drawing: its own `axes`, else its archetype's row's (the law's default)."""
    a = v.get('axes') if isinstance(v.get('axes'), dict) else None
    return a or dict((vm.archetypes().get(v.get('archetype')) or {}).get('axes') or {})


def entry(key, v, levels, sheet_block):
    """A drawing engraved from a reading, as the runtime mounts it beside the drawn ones: its story, its questions, its
    title block — and, under `engraved`, its archetype, the axes it runs on, its layouts, its forms of a verb (each with
    the verb's row) and the kinds it may make. Its reading is the viewer's, added when the page is sent (`page`)."""
    kk, target, _f = vm.draws_of(v)
    a = v.get('archetype')
    forms = [dict(w=n, verb=w['verb'], preset=w.get('preset') or {}, row=verb_row(w['verb']))
             for n, w in enumerate(v.get('writes') or []) if isinstance(w, dict) and isinstance(w.get('verb'), str)
             and w['verb'] in vm.CORE.L.verbs]
    return {"key": key, "title": vm.kit.esc(v.get("label") or (title_of(target) if kk == 'bean' else '') or key),
            "claim": "", "caption": "", "rel": "engraved from a reading · %s" % vm.kit.esc(a), "svg": "",
            "uid": "view-%s" % key, "source": vm.draws_label(v), "draws_bean": target if kk == "bean" else None,
            "elements": [], "binds": [], "facts": {}, "steps": [], "legend": [], "patterns": [], "live_patterns": [],
            "actions": [], "writes": vm.writes(v), "levels": levels, "story": vm.resolve_story(v), "tiles": [], "parts": [],
            "questions": {q.get("lens"): q.get("ask") for q in (v.get("questions") or []) if isinstance(q, dict)},
            "operate": {"archetype": a, "notes": [n.get("note") for n in (v.get("notes") or []) if isinstance(n, dict)],
                        "blind": ["%s%s" % (b.get("what"), (" — " + b["why"]) if b.get("why") else "")
                                  for b in (v.get("blind") or []) if isinstance(b, dict)]},
            "wiring": None, "window": {"hours": 6, "step": 300}, "patternMeaning": {}, "opens": [], "details": [],
            "links": [], "frame": v.get("frame"), "proposed": a, "sheet": sheet_block, "changed": [], "alerts": [],
            "engraved": {"archetype": a, "axes": axes_of(v), "layouts": list(v.get("layouts") or []),
                         "forms": forms, "new": [str(k) for k in _listed(v.get("new"))]}}


def problems(key, v):
    """(errors, warnings) of a drawing engraved from a reading, beyond what the gate judges: what it draws is there,
    and a timeline's span is a length the walk can be bounded by."""
    errs, warns = [], []
    kk, target, folder = vm.draws_of(v)
    if not kk or not vm.fm(target, folder):
        errs.append("%s: draws %r, which is no bean or mapping of the garden" % (key, v.get("draws")))
    if v.get('archetype') == 'timeline' and isinstance(v.get('span'), dict) and not vm.seconds(v['span']):
        errs.append("%s: a timeline's span is a length on time (`measure`, in a unit of duration): the repetitions are "
                    "walked within it" % key)
    if v.get('archetype') == 'sheet' and kk != 'bean':
        errs.append("%s: a sheet draws one being, a bean of the garden; it draws %s" % (key, vm.draws_label(v)))
    return errs, warns


def page_problems():
    """(errors, warnings) of the page as a whole: a public page shows no held value. A card's fact that names a verb a
    being of its kind holds sealed would send it to whoever the page is published to."""
    errs = []
    if vm.private():
        return errs, []
    for _i, f in vm.entries_of_view('fields'):
        verb, kind = str(f.get('term') or ''), str(f.get('genos') or '')
        if verb not in vm.CORE.L.verbs:
            continue
        sealed = sorted(bid for bid, b in vm.CORE.G.beans.items() if b.kind == kind
                        and any(v == verb and isinstance(r, dict) and 'held' in r for _i2, v, r in b.items))
        if sealed:
            errs.append("page.fields: a card of a %s shows `%s`, which %s holds sealed — a public page shows no held value; "
                        "a page read only behind its host's sign-in says `visibility: private`, and its host sends the "
                        "value only to a reader who may read it" % (kind, verb, ", ".join(sealed)))
    return errs, []


def data(key, v, may, reader):
    a = v.get('archetype')
    if a == 'queue':
        return queue(reader, may)
    if a == 'timeline':
        return timeline(v, may)
    if a == 'flows':
        return flows(v, may)
    if a == 'table':
        return table(v, may)
    kk, target, _f = vm.draws_of(v)
    return {'bean': target if kk == 'bean' and may('read', target) else None}


NAMED = ('verbs', 'roles', 'qualifiers', 'beside_roles', 'kinds', 'header', 'forms')


def names(lang):
    """The law's words a page shows — each verb, role, qualifier, key beside the roles, kind, header key and attribute
    of a form (`forms:<form>.<attribute>`) — in the reader's language, as the names layer gives them
    (seed/names/<lang>.tsv, `<group>:<word>`, the language's own word for the item as the law uses it):
    {group: {word: name}}. A language with no table, or a word its table does not
    name, gives nothing, and the page shows the law's own word: no language stands in for another."""
    lang = str(lang or '').split('-')[0].lower()
    out = {g: {} for g in NAMED}
    path = os.path.join(vm.ROOT, 'seed', 'names', f'{lang}.tsv') if re.fullmatch(r'[a-z]{2,3}', lang) else None
    if not path or not os.path.isfile(path):
        return out
    with open(path, encoding='utf-8') as fh:
        for ln in fh.read().splitlines()[1:]:
            c = ln.split('\t')
            g, _sep, w = c[0].partition(':')
            if len(c) >= 2 and g in out and w and c[1].strip():
                out[g][w] = c[1].strip()
    return out


def localize(p, lang):
    """A page's readings for a reader of `lang`: the widgets' language, the law's words in it (`names`), and each code
    of a scheme the page holds by its label in it (`codes`)."""
    if isinstance(lang, str) and lang:
        p['settings']['garden']['lang'] = lang
        p['names'] = names(lang)
        p['codes'] = codes_of(p, lang.split('-')[0])
    return p


_CODE = re.compile(r'^([a-z][a-z0-9-]*):([^\s:]+)$')


def codes_of(p, lang=None):
    """{`<scheme>:<code>`: {name, by?}} — each code of a scheme the garden knows (the law's, or its own `schemes`) that
    the page's readings hold, by its name in the scheme's own table, read by the one reader (bin/knowledge.py): its
    label in `lang` where the table carries one (`by`, the words its publisher asks printed beside it), else its name.
    A code no table names here is left as it is written."""
    import knowledge as dmknowledge
    try:
        K = dmknowledge.Knowledge(vm.ROOT)
    except Exception:                           # no law to read schemes from here: nothing named, nothing guessed
        return {}
    out, seen = {}, set()

    def walk(x):
        if isinstance(x, dict):
            for y in x.values():
                walk(y)
        elif isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, str) and x not in seen:
            seen.add(x)
            m = _CODE.match(x)
            if not m or m.group(1) not in K.schemes:
                return
            try:
                name, by = K.label(m.group(1), m.group(2), lang) if lang else (K.name(K.row(m.group(1), m.group(2))), None)
            except (KeyError, OSError, ValueError):
                return
            if name:
                out[x] = dict({'name': str(name)}, **({'by': str(by)} if by else {}))
    walk(p.get('drawings'))
    walk(p.get('sheets'))
    return out


def settings():
    """What the widgets read, sent with the page (widgets/settings.js `configure`): the garden's gardener, zone and the
    day it is read on, each currency's places (the currencies table) — never a language, a calendar or a zone assumed
    for the reader; a host adds the reader's own where it knows them."""
    import ledger as dmledger
    g = vm.fm_path(os.path.join(vm.ROOT, 'GARDEN.md'))
    L = vm.CORE.L
    systems = []
    for sid, r in sorted((L.std_systems() or {}).items()):
        if r.get('dimension') != 'time' or not r.get('calendar'):
            continue
        levels = [str(lv.get('level')) for lv in r.get('levels') or [] if isinstance(lv, dict)]
        ex = str(r.get('example') or '')
        prefix = ex.split(':', 1)[0] + ':' if re.match(r'^[a-z][a-z0-9-]*:', ex) else ''
        systems.append({'system': sid, 'calendar': str(r['calendar']), 'prefix': prefix, 'week': 'week' in levels, 'levels': levels})
    return {'garden': {'gardener': str(g.get('gardener') or ''), 'zone': str(g.get('zone') or ''), 'title': vm.garden_name()},
            'asOf': today().isoformat(),
            # the systems a repetition may be counted in, and the units of a length of time: the law's, for the widgets
            'systems': systems,
            'durations': [{'unit': u, 'name': str(r.get('name') or u)} for u, r in (L.units or {}).items()
                          if r.get('quantity') == 'duration'],
            'currencies': [{'code': c, 'digits': r.get('digits')} for c, r in sorted(dmledger.core_units().items())
                           if str(r.get('digits') or '').isdigit()],
            # the reference systems a place is written in, and how well each is known, as the law states it
            'crs': reference_systems()}


def reference_systems():
    """For a place (widgets/place.js): each reference system of the law (places.yaml `reference_systems`, read by
    bin/geo.py) with its ensemble's accuracy, the unit named as CLDR names it (the law's own crossing, units-cldr-units)
    so the reader is shown it in their words beside a coordinate — WGS 84 is accurate to 2 m, and nothing finer is read
    from it."""
    import geo as dmgeo
    import units as dmunits
    out = []
    names = {str(r.get('name')): u for u, r in (vm.CORE.L.units or {}).items()}
    for crs, r in sorted(dmgeo.systems(vm.ROOT).items()):
        row = {'crs': crs}
        acc = r.get('ensemble_accuracy')
        if isinstance(acc, dict) and acc.get('count'):
            unit = str(acc.get('unit') or '')
            try:
                unit = dmunits.code_of('cldr-units', {'unit': names.get(unit, unit)})[0]
            except (ValueError, KeyError, OSError):
                pass                                # a unit CLDR does not name is shown as the law writes it
            row['accuracy'] = {'count': str(acc['count']), 'unit': unit}
        out.append(row)
    return out


_COORD = re.compile(r'^EPSG:4326;(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)(?:@\d{4}(?:\.\d+)?)?$')
_OSM = re.compile(r'^osm:((?:node|way|relation)/[1-9][0-9]*)$')
_GEONAMES = re.compile(r'^geonames:([1-9][0-9]{0,9})$')


def places(may):
    """THE GARDEN'S OWN PLACES a reader may read, carried with a served page for a place lookup (widgets/place.js),
    which offers them first and works with them alone offline: each being the reader may read whole whose `be … as:
    location` or `as: place`, not held, holds a coordinate in EPSG:4326, a map's element or a gazetteer's feature — by
    its title, and landing as the being itself, whose coordinates stay said once, in its own bean. Only a page that can
    write carries them (`scoped`): the offline report edits nothing, and may be published."""
    out = []
    for bid, b in sorted(vm.CORE.G.beans.items()):
        if b.unread or os.path.basename(os.path.dirname(b.path or '')) != 'beans' or not may('read', bid):
            continue
        p = {'id': bid, 'title': title_of(bid), 'kind': b.kind}
        for _i, verb, r in b.items:
            if verb != 'be' or 'held' in r or r.get('as') not in ('location', 'place'):
                continue
            for x in _listed(r.get('at')):
                m = _COORD.match(x) if isinstance(x, str) else None
                if m and 'point' not in p:
                    p['point'] = [float(m.group(1)), float(m.group(2))]
                m = _OSM.match(x) if isinstance(x, str) else None
                if m and 'osm' not in p:
                    p['osm'] = m.group(1)
                m = _GEONAMES.match(x) if isinstance(x, str) else None
                if m and 'geonames' not in p:
                    p['geonames'] = m.group(1)
        if any(k in p for k in ('point', 'osm', 'geonames')):
            out.append(p)
    return out


_CONTACT = re.compile(r'(root:[a-z0-9][a-z0-9-]*/[0-9a-f]{32})`?(?: on ([A-Za-z0-9][A-Za-z0-9_.-]*(?:#[A-Za-z0-9_.-]+)?))?')


def contact_of(bid):
    """(pointer, record, basis) of the contact a person kept off git under an opaque id holds here — what `bin/held.py
    person` writes: a record `{bean, term: person, key: contact, entry: {name, …}}` whose pointer the person's own bean
    names in its words, `Held: `<pointer>` on <basis>.`, the basis the word they were kept on (`--basis`: their agree,
    `<bean>#<id>`), None where none is written — or (None, None, None) where this host's stores hold none of theirs
    (another machine's, erased, or none)."""
    b = _bean(bid)
    if b is None or b.kind != 'person' or not b.path:
        return None, None, None
    import held as dmheld
    try:
        with open(b.path, encoding='utf-8') as fh:
            text = fh.read()
    except OSError:
        return None, None, None
    for pointer, basis in dict.fromkeys(_CONTACT.findall(text)):
        try:
            rec = dmheld.resolve(pointer, root=vm.ROOT)
        except (dmheld.NotHere, dmheld.Erased, ValueError, OSError):
            continue
        if isinstance(rec, dict) and rec.get('bean') == bid and rec.get('term') == 'person' and rec.get('key') == 'contact':
            return pointer, rec, basis.rstrip('.') or None
    return None, None, None


def stands(ref, bid):
    """Whether the word `ref` names still stands in the ledger: a statement (`<bean>#<id>`, or an id of `bid`'s own
    bean), or a bean of the garden — as a held statement's `while` is read."""
    if ref in vm.CORE.G.beans and not vm.CORE.G.beans[ref].unread:
        return True
    from core import engine
    return engine.Judge(vm.CORE.L, vm.CORE.G).statement(ref, _bean(bid)) is not None


def page(may, reader, held=None, keep=None, contact=None):
    """For one reader: each engraved drawing's reading (of those `keep` names, where it names some: the drawings the
    reader is sent), the sheet of every being one of them shows, an empty sheet of each kind a drawing makes, the beings
    a role may name, and the widgets' settings."""
    out = {'drawings': {}, 'sheets': {}, 'blank': {}, 'settings': settings(), 'reader': reader, 'codes': {}}
    show = set()
    for k, v in vm.views_raw():
        if not engraved(v) or (keep is not None and k not in keep):
            continue
        d = data(k, v, may, reader)
        out['drawings'][k] = d
        if v.get('archetype') == 'queue':
            show |= {x['opens'] for x in d['leads'] if x.get('opens')}
        elif v.get('archetype') == 'timeline':
            show |= {x['bean'] for x in d['events']}
        elif v.get('archetype') == 'flows':
            show |= {n['id'] for n in d['nodes'] if _bean(n['id']) is not None} | \
                    {a['bean'] for a in d.get('agreements') or []}
        elif v.get('archetype') == 'table':
            show |= {r['bean'] for r in d['rows']}
        elif d.get('bean'):
            show.add(d['bean'])
        for kind in _listed(v.get('new')):
            if isinstance(kind, str) and kind in vm.CORE.L.kinds:
                out['blank'][kind] = blank(kind, may)
    # A PERSON KEPT OFF GIT BY NAME (`bin/held.py person`): to a reader who may read them and whom their contact is
    # opened to (`contact`, the host's question: scoped's), the host that keeps it sends it — their name as how the page
    # calls them, their contact on their sheet, marked as kept here; every other host and reader has their opaque id, as
    # the ledger does. A page of one file (`contact` None) sends none.
    named = {}
    if contact:
        for bid, b in sorted(vm.CORE.G.beans.items()):
            if b.kind == 'person' and not b.unread and may('read', bid):
                c = contact(bid)
                if isinstance(c, dict) and str(c.get('name') or '').strip():
                    named[bid] = c
    for bid in sorted(show | set(named)):
        s = sheet(bid, may, held)
        if s is not None:
            if bid in named:
                s['contact'] = {k: str(x) for k, x in named[bid].items() if isinstance(x, (str, int))}
                s['title'] = str(named[bid]['name'])
            out['sheets'][bid] = s
    # THE BEINGS A ROLE MAY NAME: every bean the reader may read, by its title — what a sheet's picker offers
    # a person kept under an opaque id whose name this host does not hold is `opaque`: the page calls them by what they
    # are, never by the id
    out['beings'] = [dict({'id': bid, 'title': str(named[bid]['name']) if bid in named else title_of(bid), 'kind': b.kind},
                          **({'held_name': True} if bid in named else {}),
                          **({'opaque': True} if b.kind == 'person' and bid not in named and title_of(bid) == bid else {}))
                     for bid, b in sorted(vm.CORE.G.beans.items())
                     if not b.unread and os.path.basename(os.path.dirname(b.path or '')) == 'beans' and may('read', bid)]
    out['codes'] = codes_of(out)                   # each code of a scheme by its name: the reader's language, localize
    return out


# --------------------------------------------------------------------------------------------- the host's own questions
def scoped(host, user, keep=None):
    """`page` for a viewer of a host (view_serve.Host): read and write asked of the host's one function, `may`, which
    holds the host's ceiling under the law's grants; a held value sent only by the host whose store holds it, to a
    viewer a grant NAMES it to (bin/pass.py `may_core`, `held`: the gardener aside, never by a grant of the whole bean),
    while the word it is held on stands. Read once for each viewer at each ledger head and each day — a grant, a seal or
    a write moves the head — and kept on the host until either moves."""
    u = (host.cfg.get('users') or {}).get(user) or {}
    key = (user, today().isoformat(), tuple(sorted(keep or ())))
    kept = getattr(host, '_engraved', None)
    if not isinstance(kept, dict) or kept.get('head') != host.head:
        kept = {'head': host.head}
        host._engraved = kept
    if key in kept:
        return kept[key]

    def may(act, bean, positions=None, held=False):
        return host.may(user, bean, positions=positions, write=(act == 'write'), **({'held': True} if held else {}))[0]

    def held(bean, sid, r):
        import held as dmheld
        if not may('read', bean, [sid], held=True):        # a grant naming the statement, its verb, or its `as`
            return None
        b = _bean(bean)
        w = r.get('while')
        if isinstance(w, str):
            from core import engine
            if engine.Judge(vm.CORE.L, vm.CORE.G).statement(w, b) is None:
                return None                     # the word it is held on no longer stands: nothing is sent
        try:
            rec = dmheld.resolve(r['held'], root=vm.ROOT)
        except (dmheld.NotHere, dmheld.Erased, ValueError, OSError):
            return None
        e = rec.get('entry') if isinstance(rec, dict) and rec.get('key') == sid else None
        return {k: x for k, x in e.items() if k != 'while'} if isinstance(e, dict) else None
    def contact(bid):
        """A held person's name and ways to reach them, to the bar of every held value: sent to the gardener, or to a
        reader a grant names the part of the person's bean that says where they are held (`cover: { parts: [body] }`) —
        a grant of the whole bean opens the bean, never by itself what this host keeps of them — and only while the word
        they were kept on (`Held: … on <basis>`, bin/held.py --basis) stands, where one is written: once their consent is
        taken out, nobody has their name or contact, the gardener neither."""
        _pointer, rec, basis = contact_of(bid)
        if not (isinstance(rec, dict) and isinstance(rec.get('entry'), dict)):
            return None
        if not may('read', bid, ['body'], held=True):
            return None
        if basis and not stands(basis, bid):
            return None
        return rec['entry']
    p = page(may, u.get('bean'), held, keep, contact)
    p['places'] = places(may)                                     # what a place lookup offers first: the reader's own
    g = p['settings']['garden']
    if isinstance(u.get('calendar'), str) and u['calendar']:
        g['calendar'] = u['calendar']
    # THE READER'S OWN WAY OF READING, kept with their account on the host (view_prefs): their tag, its zone, how a day
    # is written and a currency named — what they did not set is their language's own; the law's words in their language
    import view_prefs
    p['settings']['reader'] = view_prefs.settings_of(u)
    localize(p, p['settings']['reader'].get('locale') or u.get('lang'))
    g['me'] = u.get('bean') or ''
    if g.get('gardener') and not may('read', g['gardener']):   # the gardener too is named only to whom may read them
        g['gardener'] = ''
    kept[key] = p
    return p


def serve_write(host, user, body):
    """(status, answer) for a write a served page sends with `ops` (view_serve, POST /api/write): a sheet's Save — `bean`
    and its ops, or `kind` and the ops of a new being — or a drawing's form of a verb (`m`, the drawing; `w`, the form),
    which adds only statements of its verb, its preset roles as the form fixes them, onto the being it draws. It is
    written by view_write.write as the viewer's being, every attempt audited with its answer."""
    import view_write
    u = (host.cfg.get('users') or {}).get(user) or {}
    actor = u.get('bean')
    ops, bean, kind = body.get('ops'), body.get('bean') or None, body.get('kind') or None
    base = {"user": user, "actor": actor, "act": "write", "bean": bean, "kind": kind, "head": (host.head or "")[:12]}
    if not u.get('actions'):
        host.audit(dict(base, mode="refused", why="this viewer may view but not act"))
        return 403, {"ok": False, "refusals": [{"op": None, "fact": None, "message": "this viewer may view but not write"}]}
    if body.get('m') is not None:
        v = host._bound(user, str(body.get('m')))
        form = next((f for f in ((v or {}).get('engraved') or {}).get('forms') or [] if str(f['w']) == str(body.get('w'))), None)
        if not form:
            return 404, {"ok": False, "refusals": [{"op": None, "fact": None, "message": "no such form on that drawing"}]}
        bean = bean or v.get('draws_bean')
        bad = [n for n, op in enumerate(ops if isinstance(ops, list) else [])
               if not isinstance(op, dict) or op.get('op') != 'add' or op.get('verb') != form['verb']
               or any((op.get('roles') or {}).get(r) != x for r, x in (form.get('preset') or {}).items())]
        if bad or not isinstance(ops, list):
            return 400, {"ok": False, "refusals": [{"op": n, "fact": None, "message": "this form adds a `%s` with %s as "
                                                    "it fixes them" % (form['verb'], json_words(form.get('preset')))}
                                                   for n in (bad or [None])]}

    def may(act, b, positions=None, held=False):
        return host.may(user, b, positions=positions, write=(act == 'write'), **({'held': True} if held else {}))[0]
    with host.wlock:
        r = view_write.write(vm.ROOT, actor, None if kind else bean, ops, kind=kind, may=may)
    host.audit(dict(base, bean=r.get('bean'), mode="saved" if r['ok'] else "refused", commit=r.get('commit'),
                    why=None if r['ok'] else "; ".join(x['message'] for x in r['refusals'])[:1500]))
    if r['ok']:
        host.refresh(force=True, reexec=False)
    return (200 if r['ok'] else 422), {k: x for k, x in r.items() if k != 'output' or not r['ok']}


def json_words(x):
    import json
    return json.dumps(x or {}, ensure_ascii=False)
