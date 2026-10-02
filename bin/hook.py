#!/usr/bin/env python3
"""hook — the guards a garden can set in another maker's agent loop: advisory, and failing closed.

    python3 bin/hook.py install claude-code      # this clone's hooks, in .claude/settings.local.json, kept off git
    python3 bin/hook.py uninstall claude-code
    python3 bin/hook.py prompt|pre|post|end      # what the harness calls, its event on standard input

(`python` on Windows; `bin/dmhook.py`, today's name, runs this too until v1's part 13, and a hook installed by either
name is the other's to remove.) Where daftar does not run the loop (`bin/launch.py` does), the harness that does may call a
hook before and after each tool. What a hook can see is the harness's to give, so these guards are ADVISORY: a harness
that skips its hooks skips them, and the gate at the commit is what holds. Where they run, they FAIL CLOSED — a hook that
cannot read its event, or breaks, refuses (exit 2) rather than let a tool through unjudged.

  prompt  keeps the person's prompt as the session's `instructions` material, per clone and off git (bin/launch.py's
          store), so the save can trace a said value to it.
  pre     refuses (exit 2, the reason to the model): a commit made past the save (bin/save.py), or with --no-verify; a write into
          another garden (CHECKLIST.md Part F — what you would give it is a proposal); a read of a file of this garden in
          no layer (R4). A file read again only warns: the harness may have dropped it from its context.
  post    keeps what a read returned as material, in its layer; looks at a shell's or a search's output by content for a
          line of a file a request may not carry, and warns the model, recording it (POST warns until it is measured).
  end     the session is over: a save here is no longer traced against it.

A harness's names for its events and tools are that harness's, so its table is here, in this tool, and written into a
clone's own settings — never into the law.

A garden is either law's (v1 part 10): its gate is here (`bin/check.py`, or today's `bin/dmcheck.py`) and its own law
(GARDEN.md, or today's VOCAB.md); a refusal names the tools of the law it runs — in a garden of the core the save
`bin/save.py` and a proposal `bin/propose.py` — and the layer map and the flow law are that law's (bin/pass.py).
"""
import json
import os
import re
import shlex
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr
import dmpass  # noqa: E402 — bin/pass.py (`pass` is a keyword of Python)
import launch  # noqa: E402

PY = 'python' if os.name == 'nt' else 'python3'
HARNESSES = {
    'claude-code': {
        'settings': '.claude/settings.local.json',
        'events': {'UserPromptSubmit': ('prompt', None),
                   'PreToolUse': ('pre', 'Bash|Read|Write|Edit|MultiEdit|NotebookEdit'),
                   'PostToolUse': ('post', 'Read|Bash|Grep'),
                   'SessionEnd': ('end', None)},
        'shell': 'Bash', 'read': 'Read', 'search': 'Grep', 'writes': ('Write', 'Edit', 'MultiEdit', 'NotebookEdit'),
    },
}
H = HARNESSES['claude-code']
COMMIT = re.compile(r'\bgit\b(?:\s+-[cC]\s+\S+|\s+--?[\w-]+(?:=\S+)?)*\s+commit\b')
# --no-verify as git takes it, abbreviated too (`--no-ver`); a commit's `-n` alone or in a cluster (`-nm`); and a
# hooks path pointed away from the garden's own, which runs no hook at all
NO_VERIFY = re.compile(r'\bgit\b[^|;&\n]*\s--no-v(?:e(?:r(?:i(?:fy?)?)?)?)?\b'
                       r'|\bcommit\b[^|;&\n]*\s-[A-Za-z]*n[A-Za-z]*\b'
                       r'|\bgit\b[^|;&\n]*core\.hooks[Pp]ath')


def unquoted(cmd):
    """The command with every quoted argument emptied: what a message says is not what runs (`dmsave.py "w" --body
    "…git commit…"` commits nothing by hand), and a word that only mentions the save is not the save."""
    return re.sub(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"", '""', cmd)


def _q(path):
    """A path as the harness's shell takes it whole, a space and all: double quotes on Windows, a shell's quoting else."""
    return f'"{path}"' if os.name == 'nt' else shlex.quote(path)


def deny(why):
    print(dmparse.said(f"dmhook: refused — {why}"), file=sys.stderr)
    sys.exit(2)


def top_of(path):
    """The top of the git working copy that holds `path` (existing or not), or None."""
    d = os.path.abspath(path)
    while d and not os.path.isdir(d):
        d = os.path.dirname(d)
    r = launch.git(d or '.', 'rev-parse', '--show-toplevel') if d else None
    return os.path.realpath(r.stdout.strip()) if r is not None and r.returncode == 0 and r.stdout.strip() else None


def is_garden(top):
    """A garden of either law: its gate is here (`bin/check.py`, or today's `bin/dmcheck.py`), and so is its own law
    (GARDEN.md, or today's VOCAB.md)."""
    return bool(top) and any(os.path.exists(os.path.join(top, 'bin', g)) for g in ('check.py', 'dmcheck.py')) and any(
        os.path.exists(os.path.join(top, f)) for f in ('GARDEN.md', 'VOCAB.md'))


def tool_of(root, verb):
    """The tool a refusal names, by the law the garden at `root` runs: the verb's own in a garden of the core
    (`bin/<verb>.py`), today's name in one in today's words (`bin/dm<verb>.py`, until v1's part 13)."""
    return f"bin/{verb}.py" if dmpass.runs_core(root) else f"bin/dm{verb}.py"


def session(ev, root):
    sid = re.sub(r'[^a-z0-9-]', '', str(ev.get('session_id') or '').lower())[:12]
    if not sid:
        deny("the event names no session")
    return launch.Session(root, f'hook-{sid}')


def rel_in(root, path):
    full = os.path.realpath(os.path.join(root, path))
    return os.path.relpath(full, root).replace(os.sep, '/') if full.startswith(root + os.sep) else None


def text_of(resp):
    """The text a tool returned, however the harness wrapped it."""
    if isinstance(resp, str):
        return resp
    out = []

    def walk(v):
        if isinstance(v, str):
            out.append(v)
        elif isinstance(v, dict):
            for k in ('content', 'stdout', 'stderr', 'output', 'text', 'file'):
                if k in v:
                    walk(v[k])
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(resp)
    return '\n'.join(out)


def denied_index(s, root):
    """POST's index, kept in the session's store for the commit it was made at."""
    head = launch.git(root, 'rev-parse', 'HEAD').stdout.strip() or 'none'
    p = os.path.join(s.dir, f'denied-{head}.json')
    try:
        with open(p, encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, ValueError):
        pass
    idx = dmpass.denied_lines(root, dmpass.Map.here(root), dmpass.flows(root))
    os.makedirs(s.dir, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as fh:
        json.dump(idx, fh)
    return idx


def on_prompt(ev, root):
    s = session(ev, root)
    s.open()
    if str(ev.get('prompt') or '').strip():
        s.add(str(ev['prompt']), {'layer': 'instructions'}, 'instructions')


def on_pre(ev, root):
    tool, a = ev.get('tool_name'), ev.get('tool_input') or {}
    if tool == H['shell']:
        cmd = unquoted(str(a.get('command') or ''))
        if NO_VERIFY.search(cmd):
            deny(f"--no-verify (or -n, or a hooks path of its own) steps past the gate; a garden's commit is judged by "
                 f"it — save through {tool_of(root, 'save')}")
        # the save commits from inside its own process, so no command line the model runs is ever its commit: a
        # `git commit` in one is by hand, whatever else the line mentions
        if COMMIT.search(cmd):
            deny(f"a commit here is made by the save, which journals and is traced: {PY} {tool_of(root, 'save')} \"<who>\" "
                 f"\"<what>\" --body \"- action: …\"")
    elif tool in H['writes']:
        path = a.get('file_path') or a.get('notebook_path') or ''
        top = top_of(path) if path else None
        if top and top != root and is_garden(top):
            deny(f"{path} is in another garden ({top}); it is not yours to write — what you would give it is a proposal "
                 f"(CHECKLIST.md Part F: {tool_of(root, 'propose')})")
    elif tool == H['read']:
        rel = rel_in(root, str(a.get('file_path') or ''))
        if rel and not rel.startswith('.git/') and os.path.isfile(os.path.join(root, rel)):
            m = dmpass.Map.here(root)
            if m.layer_of(rel)[0] is None:
                deny(f"{rel} is in no layer, and a file in no layer is not read into a request (R4) — ask the gardener "
                     f"to place it")
            s = session(ev, root)
            if any(e.get('from') == {'file': rel} for e in s.index()):
                print(json.dumps({'systemMessage': f"dmhook: {rel} was read before in this session"}))


def on_post(ev, root):
    tool, a = ev.get('tool_name'), ev.get('tool_input') or {}
    s = session(ev, root)
    if not s.state:
        s.open()
    text = text_of(ev.get('tool_response'))
    if tool == H['read']:
        rel = rel_in(root, str(a.get('file_path') or ''))
        layer = dmpass.Map.here(root).layer_of(rel)[0] if rel else None
        if rel and layer:
            s.add(text, {'file': rel}, layer)
        return
    hits = dmpass.post_hits(text, denied_index(s, root))
    if hits:
        s.post({'tool': tool, 'hits': hits})
        say = (f"dmhook POST: this output holds lines of {', '.join(f'{p} ({n})' for p, n in sorted(hits.items()))} — "
               f"files a request may not carry. Do not carry them into the garden or on; recorded.")
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': say}}))


def install(root, harness, on=True):
    h = HARNESSES.get(harness)
    if h is None:
        sys.exit(f"dmhook: no harness `{harness}` — {', '.join(HARNESSES)}")
    p = os.path.join(root, *h['settings'].split('/'))
    try:
        with open(p, encoding='utf-8') as fh:
            cfg = json.load(fh)
    except FileNotFoundError:
        cfg = {}
    except ValueError:
        sys.exit(f"dmhook: {h['settings']} is not JSON; nothing changed")
    me = os.path.abspath(__file__)
    hooks = cfg.setdefault('hooks', {})
    for event, (verb, matcher) in h['events'].items():
        keep = [g for g in hooks.get(event, []) if not any(re.search(r'\b(?:dm)?hook\.py\b', str(x.get('command', '')))
                                                            for x in g.get('hooks', []))]
        if on:
            g = {'hooks': [{'type': 'command', 'command': f'{_q(sys.executable)} {_q(me)} {verb}'}]}
            if matcher:
                g['matcher'] = matcher
            keep.append(g)
        if keep:
            hooks[event] = keep
        else:
            hooks.pop(event, None)
    if not hooks:
        cfg.pop('hooks')
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(cfg, fh, indent=2)
        fh.write('\n')
    ex = launch.git(root, 'rev-parse', '--git-path', 'info/exclude').stdout.strip()
    ex = ex if os.path.isabs(ex) else os.path.join(root, ex)
    try:
        with open(ex, encoding='utf-8') as fh:
            lines = fh.read().splitlines()
    except OSError:
        lines = []
    if '/' + h['settings'] not in lines:
        os.makedirs(os.path.dirname(ex), exist_ok=True)
        with open(ex, 'a', encoding='utf-8') as fh:
            fh.write('/' + h['settings'] + '\n')
    print(f"dmhook: {'installed in' if on else 'removed from'} {h['settings']} (this clone's own, kept off git)")
    return 0


def main(argv):
    if argv[:1] in (['install'], ['uninstall']):
        root = launch.git(os.getcwd(), 'rev-parse', '--show-toplevel').stdout.strip()
        if not root:
            sys.exit("dmhook: not inside a garden's git working copy")
        return install(root, argv[1] if len(argv) > 1 else 'claude-code', argv[0] == 'install')
    verbs = {'prompt': on_prompt, 'pre': on_pre, 'post': on_post, 'end': None}
    if argv[:1] == [] or argv[0] not in verbs:
        sys.exit(f"dmhook: install|uninstall <harness>, or {'|'.join(verbs)} with the event on standard input")
    try:
        ev = json.loads(sys.stdin.read() or '{}')
        if not isinstance(ev, dict):
            raise ValueError('the event is not an object')
        root = top_of(ev.get('cwd') or os.getcwd())
        if not is_garden(root):
            return 0                                   # not a garden: nothing of ours to judge
        if argv[0] == 'end':
            session(ev, root).end()
            return 0
        verbs[argv[0]](ev, root)
        return 0
    except SystemExit:
        raise
    except Exception as e:                             # FAILING CLOSED: a hook that breaks lets nothing through
        deny(f"the hook could not judge this ({type(e).__name__}: {e}); fix the hook, or uninstall it: "
             f"{PY} bin/hook.py uninstall claude-code")


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
