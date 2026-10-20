#!/usr/bin/env python3
"""leads — what waits, and for whom: a reading of the garden for each person, read each time it is asked and never
stored (MODEL.md: readings; manifesto: once).

    python3 bin/leads.py [--for <person>] [--json]

WHO IS TOLD IS NEVER CONFIGURED: it is read from what the garden already says, so nobody keeps a second list that
disagrees with the garden. A lead says what waits, whose it is, and what it is about:

  decision   a decision parked in log/pending.md (`status: proposed`): the gardener's, and also whoever a
             `grant … as: ratify, class: <its class>` of the gardener's opens it to
  case       a case on a walk (a course: a being `be`ing at a walk `as: order`) at a step that is not final: the
             party's whose part the step's `by` names (the `agree … as: <part>` of the case's agreement), said
             overdue where the step's `usually` has passed (bin/seq.py `where`); where nobody took that part, whoever
             keeps the being (`answer … as: keeping`) — a routine's run waiting on its interlocks, a run rolled back —
             else the gardener's, saying so
  obligation a clause of an agreement (or any term the law gives an expiry) falling due within its notice, or past
             it, as bin/stale.py reads it: the party it binds — who makes the payment it asks (`side: pays`) — else the
             gardener; and the party the payment is owed to (`to`), told it is owed and by whom (`side: owed`,
             `owed_by`), so what others owe a person reaches them too. A
             routine's clause (a clause of a `run`, bin/routines.py) is none: the machine keeps it, and a person is
             told of it only when a run waits, fails or is rolled back
  health     a failure a reading shows is happening — a `fail` whose `through` names a `measure` (a probe's
             reading: a disk's pending sectors, a clock's offset, a certificate's days left), with no `repair` of
             it: whoever answers for the being in keeping it (`answer … as: keeping`), else its owner, else the
             gardener. A failure recorded with no reading behind it is a finding, kept in the reading, not a lead
             (design §14: leads for what someone can act on)
  session    an agent's session left open — a worktree of the garden on a `session/<slug>` branch, as
             bin/session.py lists it (its close retires the worktree; a session bean's own words do not say it,
             since closing leaves `details.status` as it was): the gardener's, to close or to ratify what it did

A reading writes nothing. A host that serves the garden (daftard) asks it after each save and sync step, and tells
each person their own, by the passes the flow law grants (a notice on the machine; off it only where the gardener
granted that party).
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr
import importlib  # noqa: E402
dmpass = importlib.import_module('pass')  # noqa: E402 — `pass` is a keyword: imported by name
import seq as dmseq  # noqa: E402 — where a course stands, read from its moves and its walk

HEAD = re.compile(r'^## (.+?)(?: · |$)')



def stored_courses(root):
    """(being, course) of each course a store this host keeps holds of a being in no bean that may wait for a person: at
    a step that is not final, and not one the machine acts at (`machine`) unless the step has a usual time to pass —
    read from each store's moves at once, the walk's own steps saying which (a run's walk marks its machine's steps)."""
    out = []
    steps_of = {}
    try:
        import store as dmstore
        kept = dmstore.kept_here(root)
    except Exception:   # noqa: BLE001 — a garden that keeps no store
        return out
    for name, (path, _row, _why) in sorted(kept.items()):
        if not path or not os.path.isfile(path):
            continue
        try:
            S = dmstore.Store(path, root=root, create=False, readonly=True, name=name)
        except Exception:   # noqa: BLE001
            continue
        if 'be' not in S.verbs():
            continue
        last = {}                                        # (being, course) -> (moment, step) of its last move
        for being, _sid, roles in (S.statements_of('move') if 'move' in S.verbs() else []):
            at = roles.get('at')
            at = at if isinstance(at, list) else [at]
            step = next((str(x).split('#', 1)[1] for x in at if isinstance(x, str) and '#' in x), None)
            when = next((str(x) for x in at if isinstance(x, str) and '#' not in x), '')
            key = (being, str(roles.get('through') or '').split('#')[-1])
            if step and (key not in last or when >= last[key][0]):
                last[key] = (when, step)
        for being, sid, roles in S.statements_of('be'):
            walk = roles.get('at')
            if roles.get('as') != 'order' or not isinstance(walk, str):
                continue
            if walk not in steps_of:
                steps_of[walk] = {s['id']: s for s in dmseq.walk_steps(root, walk)}
            st = steps_of[walk].get((last.get((being, sid)) or (None, None))[1])
            if st is None or st.get('final') or (st.get('machine') and not st.get('usually')):
                continue
            out.append((being, sid))
    return out

def pending(root):
    """[(id, class, status)] of log/pending.md's entries, as each writes them: `## <id> · …`, `- class: X …`,
    `- status: …`. What a fenced block holds is the file's own example of an entry (the seed's "Entry shape"), never an
    entry: read, it was a decision `<slug>` waiting on every gardener of every garden grown from the seed."""
    path = os.path.join(root, 'log', 'pending.md')
    out, cur, fenced = [], None, False
    try:
        lines = open(path, encoding='utf-8').read().splitlines()
    except OSError:
        return out
    for ln in lines:
        if ln.lstrip().startswith('```'):
            fenced = not fenced
            continue
        if fenced:
            continue
        m = HEAD.match(ln)
        if m:
            cur = [m.group(1).strip(), '', '']
            out.append(cur)
            continue
        if cur is None:
            continue
        s = ln.strip()
        if s.startswith('- class:'):                  # a class of the Contract of Parts (MODEL.md): one letter, A to K
            m = re.match(r'([A-K])(?![A-Za-z])', s[len('- class:'):].strip())
            cur[1] = m.group(1) if m else ''
        elif s.startswith('- status:'):
            cur[2] = (s[len('- status:'):].strip().split() or [''])[0]
    return [tuple(x) for x in out]


def listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def keepers_of(b, bid):
    """Who keeps a being: the `by` of each `answer … as: keeping` of it, in its own bean."""
    return sorted({str(x) for _j, v, a in (b.items if b else []) if v == 'answer' and a.get('as') == 'keeping'
                   and a.get('of') in (None, 'self', bid) for x in listed(a.get('by')) if isinstance(x, str)})


def read(root=ROOT):
    """Every lead of the garden at root: [{for, kind, about, why, …}]."""
    gardener = dmpass.gardener_of(root)
    _law, G = dmseq.core(root)
    leads = []

    # DECISIONS: the gardener's, and whoever a ratify grant of their class opens them to
    ratifiers = {}
    for b in G.beans.values():
        for _i, verb, r in b.items:
            if verb == 'grant' and r.get('as') == 'ratify' and 'held' not in r:
                for c in listed(r.get('class')):
                    ratifiers.setdefault(str(c), set()).update(str(x) for x in listed(r.get('to')) if isinstance(x, str))
    for pid, cls, status in pending(root):
        if status != 'proposed':
            continue
        for who in sorted({gardener} | ratifiers.get(cls, set()) - {None}):
            leads.append({'for': who, 'kind': 'decision', 'about': pid, 'class': cls,
                          'why': f"a decision parked for you to take (class {cls or 'unsaid'}): log/pending.md {pid}"})

    # CASES: each course at a step that is not final, for the party whose part the step names
    for bid, b in sorted(G.beans.items()):
        courses = [r.get('id') for _i, verb, r in b.items
                   if verb == 'be' and r.get('as') == 'order' and isinstance(r.get('id'), str) and 'held' not in r]
        for course in courses:
            try:
                w = dmseq.where(root, bid, course)
            except Exception:   # noqa: BLE001 — a course this reader cannot place is the gate's to judge, not a lead
                continue
            if not w.get('step') or w.get('final') or (w.get('machine') and w.get('overdue') is not True):
                continue                                 # the machine's step, within its usual time: nobody's yet
            parties = [] if w.get('machine') else [p.strip() for p in str(w.get('party') or '').split(',') if p.strip()]
            base = {'kind': 'case', 'about': bid, 'course': course, 'step': w['step'], 'walk': w.get('walk'),
                    'since': w.get('at'), 'overdue': w.get('overdue') is True}
            late = ', past its usual time' if base['overdue'] else ''
            if parties:
                for who in parties:
                    leads.append(dict(base, **{'for': who, 'why': f"{bid} waits at {w['step']} for you, as its "
                                                                 f"{w.get('by')}{late}"}))
            elif keepers_of(b, bid):
                for who in keepers_of(b, bid):
                    leads.append(dict(base, **{'for': who, 'why': f"{bid} waits at {w['step']}, and you keep it{late}"}))
            elif gardener:
                leads.append(dict(base, **{'for': gardener, 'why': f"{bid} waits at {w['step']}, whose part "
                                                                   f"({w.get('by') or 'unsaid'}) nobody took{late}"}))

    # CASES KEPT IN A STORE: a course of a being kept only in a store this host keeps (a transfer on walk-transfer),
    # read the same way; a step the machine acts at is no lead while within its usual time, past it whoever keeps it
    for bid, course in stored_courses(root):
        if any(x.get('about') == bid and x.get('course') == course for x in leads):
            continue
        try:
            w = dmseq.where(root, bid, course)
        except Exception:   # noqa: BLE001
            continue
        if not w.get('step') or w.get('final') or (w.get('machine') and w.get('overdue') is not True):
            continue
        late = ', past its usual time' if w.get('overdue') is True else ''
        if gardener:
            leads.append({'kind': 'case', 'about': bid, 'course': course, 'step': w['step'], 'walk': w.get('walk'),
                          'since': w.get('at'), 'overdue': w.get('overdue') is True, 'for': gardener,
                          'why': f"{bid} waits at {w['step']} of {w.get('walk')}{late}"})

    # OBLIGATIONS: what falls due within its notice, read by bin/stale.py (the one reader of what falls due); bound
    # on the party who makes the payment the clause asks
    import datetime
    import stale as dmstale
    today = datetime.date.today().toordinal()
    routine = dmstale.routine_clauses()
    for fm in dmstale._fronts():
        bid = str(fm.get('bean') or '')
        b = G.beans.get(bid)
        for term, decl in dmstale.expiry_terms().items():
            try:
                due = dmstale.due_entries(fm, term, decl)
            except Exception:   # noqa: BLE001 — what bin/stale.py cannot read it says itself; no lead is made of it
                continue
            for label, held, day, shown, _detail, _why in due:
                if day is None:
                    continue
                if (bid, label.strip('[]')) in routine:
                    continue                  # a routine's clause: the machine keeps it (bin/routines.py)
                own = held.get('notice') if isinstance(held, dict) and isinstance(held.get('notice'), dict) else None
                notice = dmstale.notice_days({'of': 'time', 'measure': own} if own else decl.get('notice'))
                days = day - today
                if days > notice:
                    continue
                cid = str(held.get('id') or label.strip('[].')) if isinstance(held, dict) else label.strip('[].')
                bound, owed = [], []
                for _i, verb, r in (b.items if b else []):
                    if r.get('id') == cid and isinstance(r.get('of'), str):
                        paid = next((pr for _j, pv, pr in b.items if pv == 'pay' and pr.get('id') == r['of']), None)
                        bound = [str(x) for x in listed((paid or {}).get('by')) if isinstance(x, str)]
                        owed = [str(x) for x in listed((paid or {}).get('to')) if isinstance(x, str) and x not in bound]
                when = (f"falls due on {shown}, in {days} day(s)" if days >= 0 else f"fell due on {shown}, {-days} day(s) ago")
                for who in bound or ([gardener] if gardener else []):
                    leads.append({'for': who, 'kind': 'obligation', 'about': bid, 'clause': cid, 'due': shown,
                                  'days': days, 'side': 'pays', 'why': f"{bid} {cid} {when}"})
                for who in owed:                  # WHAT OTHERS OWE A PERSON reaches them too: the one it is owed to
                    leads.append({'for': who, 'kind': 'obligation', 'about': bid, 'clause': cid, 'due': shown,
                                  'days': days, 'side': 'owed', 'owed_by': bound,
                                  'why': f"{bid} {cid}, owed to {who} by {', '.join(bound) or 'nobody named'}, {when}"})

    # HEALTH: a failure a reading shows, not yet repaired — for whoever keeps the being
    repaired = {(str(r.get('of')) if '#' in str(r.get('of')) else f"{rb}#{r.get('of')}")   # a bare id is its own bean's
                for rb, b in G.beans.items() for _i, verb, r in b.items if verb == 'repair'}
    for bid, b in sorted(G.beans.items()):
        readings = {str(r.get('id')): r for _i, verb, r in b.items if verb == 'measure' and isinstance(r.get('id'), str)}
        for _i, verb, r in b.items:
            fid = r.get('id')
            if verb != 'fail' or 'held' in r or not isinstance(fid, str) or str(r.get('through')) not in readings \
                    or f"{bid}#{fid}" in repaired:
                continue
            keepers = [str(x) for _j, v, a in b.items if v == 'answer' and a.get('as') == 'keeping'
                       and a.get('of') in (None, 'self', bid) for x in listed(a.get('by')) if isinstance(x, str)]
            owners = [str(x) for _j, v, a in b.items if v == 'own' and a.get('of') in (None, 'self', bid)
                      for x in listed(a.get('by')) if isinstance(x, str) and x != 'theone']
            m = readings[str(r['through'])]
            value = m.get('value') if isinstance(m.get('value'), dict) else {}
            seen = f"{m.get('as')} {value.get('count', '')} {value.get('unit', '')}".strip()
            for who in sorted(set(keepers or owners or ([gardener] if gardener else []))):
                leads.append({'for': who, 'kind': 'health', 'about': bid, 'fail': fid, 'since': str(r.get('at') or m.get('at') or ''),
                              'why': f"{bid}: {r.get('as')} — read as {seen}" + (f" on {m.get('at')}" if m.get('at') else '')})

    # SESSIONS: an agent's work left open — a session's worktree, as bin/session.py lists it
    import subprocess
    out = subprocess.run(['git', 'worktree', 'list', '--porcelain'], cwd=root, capture_output=True, text=True,
                         encoding='utf-8', errors='replace').stdout
    main = (re.findall(r'(?m)^HEAD ([0-9a-f]{40})$', out) or ['HEAD'])[0]     # the main working copy is listed first
    for branch in re.findall(r'(?m)^branch refs/heads/(session/\S+)$', out):
        ahead = subprocess.run(['git', 'rev-list', '--count', f'{main}..{branch}'], cwd=root, capture_output=True,
                               text=True, encoding='utf-8', errors='replace').stdout.strip() or '?'
        slug = branch[len('session/'):]
        if gardener:
            leads.append({'for': gardener, 'kind': 'session', 'about': f"session-{slug}", 'branch': branch,
                          'ahead': ahead, 'why': f"an agent's session is open ({branch}, {ahead} commit(s) not yet "
                                                 f"in the main copy): close it, or ratify what it did"})
    return leads


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    who = argv[argv.index('--for') + 1] if '--for' in argv and argv.index('--for') + 1 < len(argv) else None
    leads = [x for x in read(ROOT) if who is None or x['for'] == who]
    if '--json' in argv:
        print(json.dumps(leads, ensure_ascii=False, indent=1))
        return 0
    for x in leads:
        print(f"{x['for']}\t{x['kind']}\t{x['about']}\t{x['why']}")
    print(f"leads: {len(leads)}" + (f" for {who}" if who else ''))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
