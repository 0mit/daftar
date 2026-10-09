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
