#!/usr/bin/env python3
"""daftar — one entry to every tool of the language: `daftar <verb> [its arguments]`.

    python3 bin/daftar.py                    # every verb, by family, each with what it does
    python3 bin/daftar.py <verb> [args ...]  # run that tool with those arguments: `daftar check --all`
    python3 bin/daftar.py help <verb>        # the tool's own help

(`python` on Windows.) The verbs and the family each belongs to are the law's — the core's `tools` and `families`
(core/law/tools.yaml) — so this file names no tool: a verb is the tool `bin/<verb>.py`, named by its verb (the one
exception is `upgrade`, whose tool keeps the name `bin/dmupgrade.py`: the door). What a tool does is
the first line of its own help, read from the tool, never restated. A tool runs under the same Python that runs this,
so the one command works alike wherever Python does — on Windows, where `python3` may be missing or be a store alias.
Every tool also runs by its own path, as it always has.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def law():
    """The families and the tools, each a row `{family, meaning}` / `{verb, family}`: the core's (core/law/tools.yaml)."""
    sys.path.insert(0, ROOT)
    from core import read
    d = read.data(os.path.join(ROOT, 'core', 'law', 'tools.yaml'))
    return {'tool_families': d.get('families') or [],
            'verbs': [{'verb': t.get('tool'), 'family': t.get('family')} for t in d.get('tools') or []]}


def tool_of(verb):
    """The file a verb runs: `bin/<verb>.py` — or, for `upgrade`, `bin/dmupgrade.py`, the door a garden in today's words
    hands over through, which keeps that name (v1 part 13) — None where neither is here."""
    for name in (f"{verb}.py", f"dm{verb}.py"):
        p = os.path.join(HERE, name)
        if os.path.isfile(p):
            return p
    return None


def said(path):
    """The first line of a tool's own docstring: what it does, in its words."""
    try:
        with open(path, encoding='utf-8') as fh:
            for line in fh:
                s = line.strip()
                if s.startswith(('"""', "'''")):
                    s = s[3:]
                    return s.split(' — ', 1)[-1].rstrip('"').strip() if ' — ' in s else s
    except OSError:
        pass
    return ''


def listing(L):
    fams = [f for f in (L.get('tool_families') or []) if isinstance(f, dict) and f.get('family')]
    verbs = [v for v in (L.get('verbs') or []) if isinstance(v, dict) and v.get('verb')]
    out = ["daftar <verb> [arguments] — `daftar help <verb>` for one tool's own help", ""]
    for f in fams:
        mine = [v for v in verbs if v.get('family') == f['family']]
        if not mine:
            continue
        out.append(f"{f['family']} — {f.get('meaning', '')}")
        for v in mine:
            p = tool_of(v['verb'])
            out.append(f"  {v['verb']:<11} {said(p) if p else '(its tool is not in this garden)'}")
        out.append("")
    return '\n'.join(out).rstrip()


def main(argv):
    L = law()
    known = {v['verb'] for v in (L.get('verbs') or []) if isinstance(v, dict) and v.get('verb')}
    if not argv or argv[0] in ('-h', '--help'):
        print(listing(L))
        return 0
    if argv[0] == 'help' and len(argv) == 2:
        argv = [argv[1], '--help']
    verb, rest = argv[0], argv[1:]
    if verb not in known:
        near = sorted(known, key=lambda k: (k[:1] != verb[:1], abs(len(k) - len(verb)), k))[:3]
        print(f"daftar: `{verb}` is no verb of the law (`verbs`) — the nearest: {', '.join(near)}; "
              f"`daftar` lists them all", file=sys.stderr)
        return 2
    p = tool_of(verb)
    if p is None:
        print(f"daftar: the verb `{verb}` runs bin/{verb}.py, and this garden does not hold it",
              file=sys.stderr)
        return 2
    return subprocess.run([sys.executable, p, *rest]).returncode


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
