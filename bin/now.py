#!/usr/bin/env python3
"""now — where the work stands: the open sessions, what waits on the gardener, the open courses and the latest
handover, read from the garden each time it is asked and never stored (MODEL.md: readings; manifesto: once).

    python3 bin/now.py [--json]

(`python` on Windows.) Each part is read from what the garden already says, by the reader of what waits
(bin/leads.py) where it reads it, so no second list can disagree with the garden:

  sessions   each agent's session left open: a worktree of the garden on a `session/<slug>` branch, as bin/session.py
             opens it, with what its bean in that worktree says it is for and when it was opened
  waiting    the decisions parked for the gardener: log/pending.md's entries whose status is `proposed`, each by its id,
             its class and the title its heading gives it
  courses    each course on a walk at a step that is not final, and whose part it waits for
  handover   the latest session closed in this copy: its bean's title and body, which is its handover — a session's
             handover is its bean's body, never a loose file

A harness that runs daftar's hooks is given this as a session begins (`bin/hook.py start`); an agent whose harness runs
none reads it first (AGENTS.md).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parse as dmparse  # noqa: E402 — its import sets UTF-8 on stdout and stderr
import garden as dmgarden  # noqa: E402 — the one reader of the garden's documents
import leads as dmleads  # noqa: E402 — the reader of what waits, and for whom
import importlib  # noqa: E402
dmpass = importlib.import_module('pass')  # noqa: E402 — `pass` is a keyword: imported by name


def _front(path):
    """(front matter, body) of a bean on disk, or ({}, '') where it cannot be read (the gate's to judge)."""
    if not os.path.isfile(path):
        return {}, ''
    d = dmgarden.document(path)
    return (d.fm if isinstance(d.fm, dict) else {}), d.body or ''


def _statements(fm):
    """[(verb, roles)] of a bean in statements."""
    out = []
    for s in fm.get('statements') or []:
        if isinstance(s, dict) and len(s) == 1:
            verb, roles = next(iter(s.items()))
            out.append((verb, roles if isinstance(roles, dict) else {}))
    return out


def sessions(root):
    """[{slug, branch, path, ahead, title, opened}]: each session's worktree of the garden, as git lists it."""
    out = subprocess.run(['git', 'worktree', 'list', '--porcelain'], cwd=root, capture_output=True, text=True,
                         encoding='utf-8', errors='replace').stdout
    main = (re.findall(r'(?m)^HEAD ([0-9a-f]{40})$', out) or ['HEAD'])[0]     # the main working copy is listed first
    found = []
    for block in out.split('\n\n'):
        path = re.search(r'(?m)^worktree (.+)$', block)
        branch = re.search(r'(?m)^branch refs/heads/(session/\S+)$', block)
        if not (path and branch):
            continue
        slug = branch.group(1)[len('session/'):]
        ahead = subprocess.run(['git', 'rev-list', '--count', f'{main}..{branch.group(1)}'], cwd=root,
                               capture_output=True, text=True, encoding='utf-8', errors='replace').stdout.strip()
        fm, _body = _front(os.path.join(path.group(1), 'beans', f'session-{slug}.md'))
        opened = next((str(r.get('at')) for v, r in _statements(fm) if v == 'open' and r.get('at')), '')
        found.append({'slug': slug, 'branch': branch.group(1), 'path': path.group(1), 'ahead': ahead or '?',
                      'title': str(fm.get('title') or ''), 'opened': opened})
    return found


def titles(root):
    """{id: title} of log/pending.md's entries, from each heading: `## <id> · <title> · …`."""
    out = {}
    try:
        lines = open(os.path.join(root, 'log', 'pending.md'), encoding='utf-8').read().splitlines()
    except OSError:
        return out
    fenced = False
    for ln in lines:
        if ln.lstrip().startswith('```'):
            fenced = not fenced
        elif not fenced and ln.startswith('## '):
            parts = [p.strip() for p in ln[3:].split(' · ')]
            out.setdefault(parts[0], parts[1] if len(parts) > 1 else '')
    return out


def handover(root):
    """{bean, title, closed, body} of the session closed last in this copy — the end of its presence (`be … as:
    presence`, written as it closes) — or None where no session has closed."""
    best = None
    for path in dmgarden.paths(root, ('beans',)):
        if not os.path.basename(path).startswith('session-'):
            continue
        fm, body = _front(path)
        for v, r in _statements(fm):
            at = str(r.get('at') or '')
            if v == 'be' and r.get('as') == 'presence' and '/' in at:
                closed = at.split('/', 1)[1]
                if best is None or closed > best['closed']:
                    best = {'bean': str(fm.get('bean') or os.path.basename(path)[:-3]),
                            'title': str(fm.get('title') or ''), 'closed': closed, 'body': body.strip()}
    return best


def read(root=ROOT):
    """Where the work stands in the garden at root: {gardener, sessions, waiting, courses, handover}."""
    gardener = dmpass.gardener_of(root)
    leads = dmleads.read(root)
    named = titles(root)
    waiting = [{'id': x['about'], 'class': x.get('class') or '', 'title': named.get(x['about'], '')}
               for x in leads if x['kind'] == 'decision' and x['for'] == gardener]
    courses = [{k: x.get(k) for k in ('about', 'course', 'step', 'walk', 'since', 'overdue', 'for')}
               for x in leads if x['kind'] == 'case']
    return {'gardener': gardener, 'sessions': sessions(root), 'waiting': waiting, 'courses': courses,
            'handover': handover(root)}


def text(now):
    """The reading, as a person or a model reads it."""
    say = dmparse.said
    out = ["now — where the work stands, read from the garden now and never stored", ""]
    out.append(f"open sessions: {len(now['sessions'])}")
    for s in now['sessions']:
        out.append(say(f"  session-{s['slug']} ({s['branch']}, {s['ahead']} commit(s) not yet in the main copy"
                       + (f", opened {s['opened']}" if s['opened'] else '') + f"), at {s['path']}"))
        if s['title']:
            out.append(say(f"    {s['title']}"))
    out.append("")
    out.append(f"waiting on the gardener ({now['gardener'] or 'none named'}): {len(now['waiting'])} decision(s) "
               f"parked in log/pending.md")
    for w in now['waiting']:
        out.append(say(f"  {w['id']}" + (f" (class {w['class']})" if w['class'] else '')
                       + (f" · {w['title']}" if w['title'] else '')))
    out.append("")
    out.append(f"open courses: {len(now['courses'])}")
    for c in now['courses']:
        out.append(say(f"  {c['about']} at {c['step']} of {c['walk'] or 'its walk'}, for {c['for']}"
                       + (f", since {c['since']}" if c.get('since') else '')
                       + (", past its usual time" if c.get('overdue') else '')))
    out.append("")
    h = now['handover']
    if h:
        out.append(say(f"the latest handover: {h['bean']}, closed {h['closed']}"))
        if h['title']:
            out.append(say(f"  {h['title']}"))
        out += [say(f"  {ln}") if ln else '' for ln in h['body'].splitlines()]
    else:
        out.append("the latest handover: none — no session has closed in this copy")
    return '\n'.join(out).rstrip()


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    now = read(ROOT)
    if '--json' in argv:
        print(json.dumps(now, ensure_ascii=False, indent=1))
    else:
        print(text(now))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
