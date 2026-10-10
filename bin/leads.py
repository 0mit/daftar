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
             overdue where the step's `usually` has passed (bin/seq.py `where`); where nobody took that part, the
             gardener's, saying so
  obligation a clause of an agreement (or any term the law gives an expiry) falling due within its notice, or past
             it, as bin/stale.py reads it: the party it binds — who makes the payment it asks — else the gardener
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


def pending(root):
    """[(id, class, status)] of log/pending.md's entries, as each writes them: `## <id> · …`, `- class: X …`,
    `- status: …`."""
    path = os.path.join(root, 'log', 'pending.md')
    out, cur = [], None
    try:
        lines = open(path, encoding='utf-8').read().splitlines()
    except OSError:
        return out
    for ln in lines:
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
            if not w.get('step') or w.get('final'):
                continue
            parties = [p.strip() for p in str(w.get('party') or '').split(',') if p.strip()]
            base = {'kind': 'case', 'about': bid, 'course': course, 'step': w['step'], 'walk': w.get('walk'),
                    'since': w.get('at'), 'overdue': w.get('overdue') is True}
            late = ', past its usual time' if base['overdue'] else ''
            if parties:
                for who in parties:
                    leads.append(dict(base, **{'for': who, 'why': f"{bid} waits at {w['step']} for you, as its "
                                                                 f"{w.get('by')}{late}"}))
            elif gardener:
                leads.append(dict(base, **{'for': gardener, 'why': f"{bid} waits at {w['step']}, whose part "
                                                                   f"({w.get('by') or 'unsaid'}) nobody took{late}"}))

    # OBLIGATIONS: what falls due within its notice, read by bin/stale.py (the one reader of what falls due); bound
    # on the party who makes the payment the clause asks
    import datetime
    import stale as dmstale
    today = datetime.date.today().toordinal()
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
                own = held.get('notice') if isinstance(held, dict) and isinstance(held.get('notice'), dict) else None
                notice = dmstale.notice_days({'of': 'time', 'measure': own} if own else decl.get('notice'))
                days = day - today
                if days > notice:
                    continue
                cid = str(held.get('id') or label.strip('[].')) if isinstance(held, dict) else label.strip('[].')
                bound = []
                for _i, verb, r in (b.items if b else []):
                    if r.get('id') == cid and isinstance(r.get('of'), str):
                        paid = next((pr for _j, pv, pr in b.items if pv == 'pay' and pr.get('id') == r['of']), None)
                        bound = [str(x) for x in listed((paid or {}).get('by')) if isinstance(x, str)]
                for who in bound or ([gardener] if gardener else []):
                    leads.append({'for': who, 'kind': 'obligation', 'about': bid, 'clause': cid, 'due': shown,
                                  'days': days, 'why': (f"{bid} {cid} falls due on {shown}, in {days} day(s)" if days >= 0
                                                        else f"{bid} {cid} fell due on {shown}, {-days} day(s) ago")})

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
