#!/usr/bin/env python3
"""hook — the guards a garden can set in another maker's agent loop: advisory, and failing closed.

    python3 bin/hook.py install claude-code      # this clone's hooks and the harness's shell, in .claude/settings.local.json,
                                                 # kept off git (bin/install.py runs it in a garden's clone)
    python3 bin/hook.py install claude-code --guard   # `start`, and the guards alone before each tool that writes
    python3 bin/hook.py uninstall claude-code
    python3 bin/hook.py start|prompt|pre|post|end   # what the harness calls, its event on standard input
    python3 bin/hook.py guard                    # the guards alone, before a shell command or a write (below)

(`python` on Windows; `bin/hook.py`, today's name, runs this too until v1's part 13, and a hook installed by either
name is the other's to remove.) Where daftar does not run the loop (`bin/launch.py` does), the harness that does may call a
hook before and after each tool. What a hook can see is the harness's to give, so these guards are ADVISORY: a harness
that skips its hooks skips them, and the gate at the commit is what holds. Where they run, they FAIL CLOSED — a hook that
cannot read its event, or breaks, refuses (exit 2) rather than let a tool through unjudged.

  start   the session begins: every standing instruction the gardener gave agents, read from the garden — each clause
          of the agents' work agreement, those a guard checks with whether this harness meets it (the shell it runs
          commands in, found by its rule), and those no guard reads, which the session keeps itself — and then where the
          work stands (bin/now.py), given to the model as context.
  prompt  keeps the person's prompt as the session's `instructions` material, per clone and off git (bin/launch.py's
          store), so the save can trace a said value to it.
  pre     refuses (exit 2, the reason to the model): a commit made past the save (bin/save.py), or with --no-verify, in a
          garden — the repository the command names (its `git -C`, a `cd` before it on the line), not the folder the
          session stands in, so a commit in another repository is that repository's; a write into another garden
          (CHECKLIST.md Part F — what you would give it is a proposal); a read of a file of this garden in no layer (R4).
          A file read again only warns: the harness may have dropped it from its context. And before each shell command
          and each write, each GUARD the gardener's instructions hold (core/law/guards.yaml): a clause of the agents'
          work agreement, the gardener's own word, read through the one judge (core/judge.py `instructions`), or, for a
          guard no instruction of the garden names, the seed's default (seed/agents-work.md.template). A guard reads
          the command, the harness's shell, or the path a write targets — a write tool's file, or a shell redirection's
          target. The refusal names the instruction, what was found, and what to do instead.
  guard   the guards of `pre` alone, before each shell command and each write: for a session that starts in a garden
          and does work beyond it — a release built in a worktree of daftar, committed and pushed there — where the
          garden's own checks of a read would refuse acts that are not the garden's. `install --guard` hooks it before
          every tool that writes.
  post    keeps what a read returned as material, in its layer; looks at a shell's or a search's output by content for a
          line of a file a request may not carry, and warns the model, recording it (POST warns until it is measured).
  end     the session is over: a save here is no longer traced against it.

A harness's names for its events and tools are that harness's, so its table is here, in this tool, and written into a
clone's own settings — never into the law. So are its memory folders (claude-code's: `projects/*/memory` in its
configuration folder, and the folder its `autoMemoryDirectory` setting names), and the variable by which it tells the
commands it runs which of its sessions runs them (`bin/session.py open` records the garden session that session works
in, off git: `claim`). So is its rule for the shell it runs commands in, and install writes the
shell the gardener's `shell-is` names, per system: on Linux the first bash at or above the floor (CLAUDE_CODE_SHELL); on
macOS Homebrew's, since Apple's /bin/bash is below it, or a refusal saying what to install; on Windows Git for Windows'
bash, its version checked (CLAUDE_CODE_GIT_BASH_PATH).

A garden is either law's (v1 part 10): its gate is here (`bin/check.py`, or today's `bin/dmcheck.py`) and its own law
(GARDEN.md, or today's VOCAB.md); a refusal names the tools of the law it runs — in a garden of the core the save
`bin/save.py` and a proposal `bin/propose.py` — and the layer map and the flow law are that law's (bin/pass.py).
"""
import glob
import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr
import importlib
dmpass = importlib.import_module('pass')  # noqa: E402 — bin/pass.py (`pass` is a keyword of Python)
import launch  # noqa: E402

PY = 'python' if os.name == 'nt' else 'python3'
RELEASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))     # the release this hook is
sys.path.insert(0, RELEASE)
SEED_AGENTS = os.path.join(RELEASE, 'seed', 'agents-work.md.template')    # the seed's default instructions
HARNESSES = {
    'claude-code': {
        'settings': '.claude/settings.local.json',
        'events': {'SessionStart': ('start', None),
                   'UserPromptSubmit': ('prompt', None),
                   'PreToolUse': ('pre', 'Bash|Read|Write|Edit|MultiEdit|NotebookEdit'),
                   'PostToolUse': ('post', 'Read|Bash|Grep'),
                   'SessionEnd': ('end', None)},
        'guard_events': {'SessionStart': ('start', None),
                         'PreToolUse': ('guard', 'Bash|Write|Edit|MultiEdit|NotebookEdit')},
        'shell': 'Bash', 'read': 'Read', 'search': 'Grep', 'writes': ('Write', 'Edit', 'MultiEdit', 'NotebookEdit'),
        # ITS MEMORY, by its own rule (Claude Code 2.1, read from its build): `projects/<folder>/memory` in its
        # configuration folder (CLAUDE_CONFIG_DIR, else ~/.claude), and the folder `autoMemoryDirectory` names in its
        # settings — the user's, and the clone's shared and own; and the variable naming its session to the commands
        # it runs
        'config': 'CLAUDE_CONFIG_DIR', 'memory': ('projects', '*', 'memory'), 'memory_setting': 'autoMemoryDirectory',
        'session_env': 'CLAUDE_CODE_SESSION_ID',
        # THE SHELL ITS BASH TOOL RUNS, by its own rule (Claude Code 2.1, read from its build): the override where it
        # names an executable bash or zsh; else $SHELL where it is one, else of the two zsh first unless $SHELL names
        # bash, in these folders; on Windows Git for Windows' bash, at the path its variable names or beside git
        'override': 'CLAUDE_CODE_SHELL', 'runs': ('bash', 'zsh'),
        'folders': ('/bin', '/usr/bin', '/usr/local/bin', '/opt/homebrew/bin'),
        'windows': 'CLAUDE_CODE_GIT_BASH_PATH',
    },
}
H = HARNESSES['claude-code']
GIT_VALUED = ('-C', '-c', '--git-dir', '--work-tree', '--namespace', '--exec-path', '--config-env', '--super-prefix')


def git_acts(command, cwd):
    """[(folder, what)]: each git a command line runs on this machine that steps past a gate or commits by hand — `what`
    is `no-verify` (--no-verify as git takes it, abbreviated too; a commit's `-n`, alone or in a cluster; a hooks path
    of its own, which runs no hook at all) or `commit` — and the repository it names: its `-C` (or `--work-tree`),
    made whole against the folder a `cd` before it on the line leaves, else the session's own folder; None where that
    cannot be placed without running the shell. A word in quotes is the word git is given: a message that says
    `--no-verify` is a message, and a `git commit` inside another's text (`save.py "w" --body "…"`) runs no git."""
    from core import guards
    home = os.path.expanduser('~')
    out = []
    for act in guards.acts(command, None, cwd, home):
        ws = act.cmd.words
        at = next((n for n, w in enumerate(ws) if guards._name(w) == 'git'), None)
        if act.remote or at is None:
            continue
        texts = [guards.text(w) for w in ws]
        where, n, sub = act.cwd, at + 1, None
        while n < len(ws):
            t = texts[n]
            key = t.split('=', 1)[0]
            if key in GIT_VALUED:
                value = t.split('=', 1)[1] if '=' in t else (texts[n + 1] if n + 1 < len(ws) else '')
                if key in ('-C', '--work-tree'):
                    where = guards.place(value, where, home)
                elif key == '--git-dir':
                    top = guards.place(value, where, home)
                    where = os.path.dirname(top) if top and os.path.basename(top) == '.git' else top
                n += 1 if '=' in t else 2
                continue
            if t.startswith('-'):
                n += 1
                continue
            sub = t
            break
        after = texts[n + 1:] if sub else []
        if any('hookspath' in t.lower() for t in texts[at + 1:]) or any(
                len(t) >= 6 and '--no-verify'.startswith(t) for t in texts[at + 1:]) or (
                sub == 'commit' and any(re.fullmatch(r'-[A-Za-z]*n[A-Za-z]*', t) for t in after)):
            out.append((where, 'no-verify'))
        elif sub == 'commit':
            out.append((where, 'commit'))
    return out


def written(command, cwd):
    """The paths a shell command's redirections write here, each as the system resolves it — on Windows a drive Git
    for Windows' bash writes `/c/…` read as `c:/…`, and a short name (`RUNNER~1`) as the long one."""
    from core import guards
    out = []
    for p in guards.written(command, cwd, os.path.expanduser('~')):
        if os.name == 'nt':
            m = re.match(r'^/([A-Za-z])(/.*)?$', p)
            p = f"{m.group(1)}:{m.group(2) or '/'}" if m else p
        out.append(os.path.realpath(p))
    return out


def _q(path):
    """A path as the harness's shell takes it whole, a space and all: double quotes on Windows, a shell's quoting else."""
    return f'"{path}"' if os.name == 'nt' else shlex.quote(path)


def deny(why):
    print(dmparse.said(f"hook: refused — {why}"), file=sys.stderr)
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


def common_dir(top):
    """The git directory every working copy of the repository at `top` shares, made whole, or None."""
    r = launch.git(top, 'rev-parse', '--git-common-dir')
    d = r.stdout.strip() if r is not None and r.returncode == 0 else ''
    return os.path.realpath(os.path.join(top, d)) if d else None


def copies(root):
    """[(path, branch)] of every working copy of the garden at `root`, its main copy first, as git lists them."""
    r = launch.git(root, 'worktree', 'list', '--porcelain')
    out = []
    for block in (r.stdout if r is not None and r.returncode == 0 else '').split('\n\n'):
        p = re.search(r'(?m)^worktree (.+)$', block)
        b = re.search(r'(?m)^branch refs/heads/(.+)$', block)
        if p:
            out.append((os.path.realpath(p.group(1)), b.group(1) if b else ''))
    return out


def _sid(value):
    return re.sub(r'[^A-Za-z0-9-]', '', str(value or ''))[:64]


def _claims(root):
    """The folder where the garden sessions harness sessions work in are recorded: off git, shared by its copies."""
    d = common_dir(root)
    return os.path.join(d, 'daftar', 'agents') if d else None


def claim(root, slug, env=None, release=False):
    """Record that the harness session whose command runs this works in the garden session `slug` — each harness by
    the variable it names its session in (`session_env`) — or, with `release`, forget every record of `slug`.
    [harness]: the harnesses recorded (none on release)."""
    env = os.environ if env is None else env
    d = _claims(root)
    if not d:
        return []
    if release:
        for p in glob.glob(os.path.join(d, '*.json')):
            try:
                with open(p, encoding='utf-8') as fh:
                    mine = json.load(fh).get('slug') == slug
                if mine:                             # closed first: Windows removes no file that is open
                    os.remove(p)
            except (OSError, ValueError, AttributeError):
                pass
        return []
    out = []
    for name, h in HARNESSES.items():
        sid = _sid(env.get(h.get('session_env') or ''))
        if sid:
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, f"{name}-{sid}.json"), 'w', encoding='utf-8') as fh:
                json.dump({'slug': slug, 'harness': name, 'session': sid}, fh)
            out.append(name)
    return out


def agent_session(root, ev, wts=None):
    """The worktree of the garden session this agent works in, or None: the one its harness session opened (`claim`),
    while its worktree stands; else the session's worktree its event's folder lies in."""
    wts = copies(root) if wts is None else wts
    d, sid = _claims(root), _sid(ev.get('session_id'))
    slug = None
    if d and sid:
        try:
            with open(os.path.join(d, f"claude-code-{sid}.json"), encoding='utf-8') as fh:
                slug = json.load(fh).get('slug')
        except (OSError, ValueError, AttributeError):
            slug = None
    if slug:
        return next((p for p, b in wts if b == f"session/{slug}"), None)
    from core import guards
    here = guards.norm(os.path.realpath(ev.get('cwd') or os.getcwd()))
    return next((p for p, b in wts if b.startswith('session/') and guards.under(here, guards.norm(p))), None)


def memory_folders(root, env=None):
    """The folders the harness keeps as its memory, by its own rule (the table's `memory`, `memory_setting`)."""
    env = os.environ if env is None else env
    config = env.get(H['config']) or os.path.join(os.path.expanduser('~'), '.claude')
    out = [os.path.join(os.path.realpath(config), *H['memory'])]
    for p in (os.path.join(config, 'settings.json'), os.path.join(root, '.claude', 'settings.json'),
              os.path.join(root, '.claude', 'settings.local.json')):
        try:
            with open(p, encoding='utf-8') as fh:
                v = json.load(fh).get(H['memory_setting'])
        except (OSError, ValueError, AttributeError):
            continue
        if isinstance(v, str) and v.strip():
            out.append(os.path.realpath(os.path.expanduser(v.strip())))
    return out


def path_context(root, ev):
    """What a guard that reads a path is given beside it: the garden's copies, the agent's own session's worktree and
    the harness's memory folders."""
    wts = copies(root)
    return {'copies': [p for p, _b in wts], 'worktree': agent_session(root, ev, wts), 'memory': memory_folders(root)}


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


# ------------------------------------------------------------------------------------------------ the agent's own door
def system():
    """linux, macos or windows: the system the harness runs on, where it picks its shell by a rule of its own."""
    return 'windows' if os.name == 'nt' else 'macos' if sys.platform == 'darwin' else 'linux'


def _base(path):
    b = re.split(r'[\\/]', str(path or ''))[-1].lower()
    return b[:-4] if b.endswith('.exe') else b


def _runs(path):
    return bool(path) and os.path.isfile(path) and os.access(path, os.X_OK)


def shell_version(path):
    """The version a shell says of itself (`<shell> --version`), or None."""
    try:
        r = subprocess.run([path, '--version'], capture_output=True, text=True, encoding='utf-8', errors='replace',
                           timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None
    m = re.search(r'([0-9]+(?:\.[0-9]+)+)', r.stdout + r.stderr)
    return m.group(1) if m else None


def git_bash(env):
    """Git for Windows' bash: where CLAUDE_CODE_GIT_BASH_PATH names it, or beside the git on the PATH
    (`<Git>\\cmd\\git.exe`, `<Git>\\mingw64\\bin\\git.exe`: `<Git>\\bin\\bash.exe`), or where its installer puts it."""
    named = env.get(H['windows'])
    if named:
        return named if os.path.isfile(named) else None
    tops = []
    g = shutil.which('git', path=env.get('PATH'))
    if g:
        d = os.path.dirname(os.path.realpath(g))
        tops += [os.path.dirname(d), os.path.dirname(os.path.dirname(d))]
    tops += [os.path.join(env.get(k) or '', 'Git') for k in ('ProgramFiles', 'ProgramW6432', 'ProgramFiles(x86)')
             if env.get(k)]
    for top in tops:
        p = os.path.join(top, 'bin', 'bash.exe')
        if os.path.isfile(p):
            return p
    return None


def harness_shell(env=None, sysname=None):
    """(name, version, path) of the shell claude-code's Bash tool runs commands in, by the harness's own rule; or None
    where it would find none."""
    env = os.environ if env is None else env
    if (sysname or system()) == 'windows':
        p = git_bash(env)
    else:
        o, sh = env.get(H['override']), env.get('SHELL') or ''
        p = o if _runs(o) and _base(o) in H['runs'] else sh if _runs(sh) and _base(sh) in H['runs'] else None
        if p is None:
            for name in (('bash', 'zsh') if _base(sh) == 'bash' else ('zsh', 'bash')):
                p = next((c for c in (os.path.join(d, name) for d in H['folders']) if _runs(c)), None)
                if p:
                    break
    return (_base(p), shell_version(p) or '', p) if p else None


def find_shell(want, floor, sysname=None, env=None):
    """(path, None) of the shell to set the harness to — `want`, at or above `floor` — or (None, what to do)."""
    from core import guards
    env = os.environ if env is None else env
    sysname = sysname or system()
    at_least = f"{want} {floor} or later" if floor else want
    if want not in H['runs']:
        return None, f"claude-code runs its commands in {' or '.join(H['runs'])} only, not {want}"
    if sysname == 'windows':
        if want != 'bash':
            return None, "claude-code runs its commands on Windows in Git for Windows' bash only"
        found = [git_bash(env)]
    else:
        first = ('/opt/homebrew/bin', '/usr/local/bin') if sysname == 'macos' else ()
        found = [os.path.join(d, want) for d in first] + [shutil.which(want, path=env.get('PATH'))] + \
                [os.path.join(d, want) for d in H['folders']]
    seen = []
    for p in found:
        if not p or p in seen or not os.path.isfile(p):
            continue
        seen.append(p)
        if guards.shell_is({'shell': want, 'floor': floor} if floor else {'shell': want},
                           (_base(p), shell_version(p) or '', p)) is None:
            return p, None
    have = ', '.join(f"{p} ({shell_version(p) or 'no version'})" for p in seen) or 'none'
    if sysname == 'macos':
        return None, (f"no {at_least} here (found: {have}; Apple's /bin/bash is 3.2) — install Homebrew's: "
                      f"`brew install {want}`, then `{PY} bin/hook.py install claude-code` again")
    if sysname == 'windows':
        return None, (f"no Git for Windows bash at {floor or 'any version'} or later here (found: {have}) — install "
                      f"Git for Windows (git-scm.com), or name its bash.exe in {H['windows']}, then install again")
    return None, (f"no {at_least} here (found: {have}) — install it with the system's package manager, then "
                  f"`{PY} bin/hook.py install claude-code` again")


def _kept_at(root):
    """Where the instructions read for this state of the garden and of this release are kept: `<git dir>/daftar/guards/
    <digest>.json`, the digest of every document's stat, the index and HEAD (the garden held, core/engine.py) and of
    this release's code and law; or None outside a clone."""
    from core import engine
    dirs = engine._gitdirs((root, None), root)
    if dirs is None:
        return None
    h = hashlib.sha256(repr(engine._token(root, dirs)[0]).encode('utf-8'))
    for p in sorted(glob.glob(os.path.join(RELEASE, 'core', '*.py')) + glob.glob(os.path.join(RELEASE, 'core', 'law', '*.yaml'))
                    + glob.glob(os.path.join(RELEASE, 'seed', 'knowledge', '*.tsv'))) + [SEED_AGENTS, __file__]:
        h.update(repr((p, engine._stat(p))).encode('utf-8'))
    return os.path.join(dirs[0], 'daftar', 'guards', h.hexdigest()[:40] + '.json')


def standing(root):
    """(holding, table, bad, clauses): {guard: [Instruction]} the guards the garden at `root` holds, the law's rows of
    them, [(rule, where, message)] what keeps an instruction from being read, and [Instruction] the gardener's other
    clauses to agents, which no guard reads — read through the one judge, with the seed's default for each guard no
    instruction of the garden names; kept for the garden as it stands (`_kept_at`)."""
    from core import guards, judge
    keep = _kept_at(root)
    if keep and os.path.isfile(keep):
        try:
            with open(keep, encoding='utf-8') as fh:
                d = json.load(fh)
            return ({g: [guards.Instruction(**i) for i in ins] for g, ins in d['holding'].items()}, d['table'],
                    [tuple(x) for x in d['bad']], [guards.Instruction(**i) for i in d['clauses']])
        except (OSError, ValueError, KeyError, TypeError):
            pass
    law = judge.garden_law(root)
    scope = judge.Scope.tree(root)
    ins, bad = judge.instructions(law, scope, seed=SEED_AGENTS)
    holding, table, clauses = guards.holding(law, ins), guards.table(law), judge.clauses(law, scope)
    if keep:
        try:
            os.makedirs(os.path.dirname(keep), exist_ok=True)
            for old in sorted(glob.glob(os.path.join(os.path.dirname(keep), '*.json')), key=os.path.getmtime)[:-8]:
                os.remove(old)
            tmp = f"{keep}.{os.getpid()}"
            with open(tmp, 'w', encoding='utf-8') as fh:
                json.dump({'holding': {g: [i._asdict() for i in v] for g, v in holding.items()}, 'table': table,
                           'bad': bad, 'clauses': [i._asdict() for i in clauses]}, fh, ensure_ascii=False)
            os.replace(tmp, keep)
        except OSError:
            pass
    return holding, table, bad, clauses


def said_of(i):
    """An instruction as a refusal names it: whose word it is, where it is, and what it says."""
    whose = (f"the gardener's instruction {i.where}" if not i.seed else
             f"the seed's default instruction {i.where}, which holds while the gardener of this garden has said none "
             f"naming `{i.guard}`")
    if i.guard is None:
        return f"{whose} ({i.stance}: {i.says or 'as its clause says'}; no guard reads it: the session keeps it)"
    return f"{whose} ({i.stance}: {i.says or i.guard}; guard `{i.guard}`, core/law/guards.yaml)"


def shell_fix(operand):
    want, floor = operand.get('shell'), operand.get('floor')
    path, why = find_shell(str(want), floor)
    if path:
        return (f"set this harness's shell to {want}{f' {floor} or later' if floor else ''} — `{PY} bin/hook.py install "
                f"claude-code` writes {path} into {H['settings']} — and start a new session")
    return why


def ev_cwd(ev):
    """The folder the harness's shell stands in for this event."""
    return os.path.realpath(ev.get('cwd') or os.getcwd())


def this_host():
    """This machine's name, as it says it: the host a command run here runs on."""
    import platform
    return platform.node()


def guarded(root, command=None, paths=(), ev=None):
    """Why the act may not happen, by the guards the garden holds, or None: a shell command (`command`, its shell and
    the paths its redirections write), or a write tool's write (`paths` alone)."""
    from core import guards
    holding, table, bad = standing(root)[:3]
    if bad:
        where, msg = bad[0][1], bad[0][2]
        return (f"the gardener's instructions to agents cannot be read, so no command is judged and none runs: {where}: "
                f"{msg} — correct the clause (a file edit), then run the command again")
    law = types.SimpleNamespace(guards=table)
    shell, ctx, ev = None, None, ev or {}
    for name in sorted(holding, key=lambda g: (table.get(g, {}).get('reads') != 'shell', g)):
        reads = table.get(name, {}).get('reads')
        for i in holding[name]:
            if reads == 'shell':
                if command is None:
                    continue                         # the shell is the commands' guard; a write tool runs none
                shell = shell or harness_shell() or ()
                r = guards.refusal(law, name, i.operand, shell=shell)
                if r:
                    return f"{said_of(i)}: {r.found}. Every command is refused until it is met: {shell_fix(i.operand)}"
            elif reads == 'path':
                if paths and ctx is None:
                    ctx = path_context(root, ev)
                for p in paths:
                    r = guards.refusal(law, name, i.operand, path=p, **ctx)
                    if r:
                        return f"{said_of(i)}: {r.found}. Instead, {r.instead}"
            elif command is not None:
                r = guards.refusal(law, name, i.operand, command=command, host=this_host(), cwd=ev_cwd(ev),
                                   home=os.path.expanduser('~'))
                if r:
                    return f"{said_of(i)}: {r.found}. Instead, {r.instead}"
    return None


def on_start(ev, root):
    """Every standing instruction the gardener gave agents, given to the model as the session begins — those a guard
    checks, each with whether it is met, and those the session keeps itself — and where the work stands (bin/now.py)."""
    from core import guards
    holding, table, bad, clauses = standing(root)
    lines = []
    for name in sorted(holding):
        for i in holding[name]:
            line = f"- {said_of(i)}"
            if table.get(name, {}).get('reads') == 'shell':
                shell = harness_shell()
                r = guards.refusal(types.SimpleNamespace(guards=table), name, i.operand, shell=shell or ())
                line += (f": NOT MET — {r.found}; every shell command will be refused until {shell_fix(i.operand)}" if r
                         else f": met, {shell[0]} {shell[1]} ({shell[2]})")
            lines.append(line)
    lines += [f"- {said_of(i)}" for i in clauses]
    lifted = sorted(g for g, v in holding.items() if not v)
    if lifted:
        lines.append(f"- lifted by the gardener: {', '.join(lifted)}")
    for _rule, where, msg in bad:
        lines.append(f"- an instruction cannot be read, and every shell command will be refused until it is corrected: "
                     f"{where}: {msg}")
    say = []
    if lines:
        say.append("The standing instructions to agents in this garden — its gardener's, read from it, or the seed's "
                   "default where the gardener has said none; bin/hook.py checks each that names a guard before every "
                   "shell command and write, and refuses what it forbids:\n" + '\n'.join(lines))
    try:
        import now as dmnow
        say.append(dmnow.text(dmnow.read(root)))
    except Exception as e:      # noqa: BLE001 — the session still begins, told that where the work stands was not read
        say.append(f"now: where the work stands could not be read ({type(e).__name__}: {e}); run `{PY} bin/now.py`")
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'SessionStart', 'additionalContext': '\n\n'.join(say)}}))


def on_prompt(ev, root):
    s = session(ev, root)
    s.open()
    if str(ev.get('prompt') or '').strip():
        s.add(str(ev['prompt']), {'layer': 'instructions'}, 'instructions')


def write_of(a):
    """The path a write tool targets, as the system resolves it, or None."""
    path = a.get('file_path') or a.get('notebook_path') or ''
    return os.path.realpath(path) if path else None


def on_pre(ev, root):
    tool, a = ev.get('tool_name'), ev.get('tool_input') or {}
    if tool == H['shell']:
        command, cwd = str(a.get('command') or ''), ev_cwd(ev)
        for where, what in git_acts(command, cwd):
            top = top_of(where) if where else root      # a repository the line names; else, unread, the session's own
            if not (top and is_garden(top)):
                continue                                 # another repository's commit is that repository's
            if what == 'no-verify':
                deny(f"--no-verify (or -n, or a hooks path of its own) steps past the gate; a garden's commit is judged "
                     f"by it — save through {tool_of(root, 'save')}")
            # the save commits from inside its own process, so no command line the model runs is ever its commit: a
            # `git commit` in one is by hand, whatever else the line mentions
            deny(f"a commit here is made by the save, which journals and is traced: {PY} {tool_of(root, 'save')} "
                 f"\"<who>\" \"<what>\" < entry.md")
        why = guarded(root, command, written(command, cwd), ev)
        if why:
            deny(why)
    elif tool in H['writes']:
        path = write_of(a)
        top = top_of(path) if path else None
        if top and top != root and is_garden(top) and common_dir(top) != common_dir(root):
            deny(f"{path} is in another garden ({top}); it is not yours to write — what you would give it is a proposal "
                 f"(CHECKLIST.md Part F: {tool_of(root, 'propose')})")
        why = guarded(root, None, [path] if path else [], ev)
        if why:
            deny(why)
    elif tool == H['read']:
        rel = rel_in(root, str(a.get('file_path') or ''))
        if rel and not rel.startswith('.git/') and os.path.isfile(os.path.join(root, rel)):
            m = dmpass.Map.here(root)
            if m.layer_of(rel)[0] is None:
                deny(f"{rel} is in no layer, and a file in no layer is not read into a request (R4) — ask the gardener "
                     f"to place it")
            s = session(ev, root)
            if any(e.get('from') == {'file': rel} for e in s.index()):
                print(json.dumps({'systemMessage': f"hook: {rel} was read before in this session"}))


def on_guard(ev, root):
    tool, a = ev.get('tool_name'), ev.get('tool_input') or {}
    if tool == H['shell']:
        command = str(a.get('command') or '')
        why = guarded(root, command, written(command, ev_cwd(ev)), ev)
    elif tool in H['writes']:
        path = write_of(a)
        why = guarded(root, None, [path] if path else [], ev)
    else:
        return
    if why:
        deny(why)


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
        say = (f"hook POST: this output holds lines of {', '.join(f'{p} ({n})' for p, n in sorted(hits.items()))} — "
               f"files a request may not carry. Do not carry them into the garden or on; recorded.")
        print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': say}}))


def install(root, harness, on=True, guard=False):
    """This clone's hooks for the harness, in its own settings, kept off git: every event's (`events`), or with
    `guard` the session's start and the guards alone before each tool that writes (`guard_events`); off, none."""
    h = HARNESSES.get(harness)
    if h is None:
        sys.exit(f"hook: no harness `{harness}` — {', '.join(HARNESSES)}")
    p = os.path.join(root, *h['settings'].split('/'))
    try:
        with open(p, encoding='utf-8') as fh:
            cfg = json.load(fh)
    except FileNotFoundError:
        cfg = {}
    except ValueError:
        sys.exit(f"hook: {h['settings']} is not JSON; nothing changed")
    me = os.path.abspath(__file__)
    hooks = cfg.setdefault('hooks', {})
    wanted = h['guard_events'] if guard else h['events']
    for event in h['events']:
        keep = [g for g in hooks.get(event, []) if not any(re.search(r'\b(?:dm)?hook\.py\b', str(x.get('command', '')))
                                                            for x in g.get('hooks', []))]
        if on and event in wanted:
            verb, matcher = wanted[event]
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
    refused = None
    if on and harness == 'claude-code':
        refused = shell_setting(root, cfg)
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
    print(f"hook: {'installed in' if on else 'removed from'} {h['settings']} (this clone's own, kept off git)"
          + ('' if on else "; the shell it names is kept"))
    if refused:
        print(f"hook: the hooks are installed and refuse every shell command until the shell is set: {refused}",
              file=sys.stderr)
        return 1
    return 0


def shell_setting(root, cfg):
    """The shell the garden's `shell-is` names, written into the harness's settings for this system: on Windows Git for
    Windows' bash (CLAUDE_CODE_GIT_BASH_PATH), else CLAUDE_CODE_SHELL. None, or why it could not be."""
    holding, _table, bad = standing(root)[:3]
    if bad:
        return f"the gardener's instructions cannot be read: {bad[0][1]}: {bad[0][2]}"
    for i in holding.get('shell-is') or []:
        path, why = find_shell(str(i.operand.get('shell')), i.operand.get('floor'))
        if why:
            return why
        key = H['windows'] if system() == 'windows' else H['override']
        cfg.setdefault('env', {})[key] = path
        print(f"hook: {key} = {cfg['env'][key]} ({_base(path)} {shell_version(path)}), as {i.where} says")
    return None


def main(argv):
    if argv[:1] in (['install'], ['uninstall']):
        root = launch.git(os.getcwd(), 'rev-parse', '--show-toplevel').stdout.strip()
        if not root:
            sys.exit("hook: not inside a garden's git working copy")
        names = [x for x in argv[1:] if not x.startswith('--')]
        return install(root, names[0] if names else 'claude-code', argv[0] == 'install', guard='--guard' in argv)
    verbs = {'start': on_start, 'prompt': on_prompt, 'pre': on_pre, 'guard': on_guard, 'post': on_post, 'end': None}
    if argv[:1] == [] or argv[0] not in verbs:
        sys.exit(f"hook: install [--guard]|uninstall <harness>, or {'|'.join(verbs)} with the event on standard input")
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
