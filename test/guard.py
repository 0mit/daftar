"""The agent's own door (P6 of the next version, steps 1 and 2 of the design of one shell): the law's closed table of
guards, each held to its vectors; the gardener's instruction as a clause of the agents' work agreement, read through the
one judge; the seed's default; and bin/hook.py refusing, before it runs, every recorded case of one interpreter's text inside
another's quotes, naming the instruction and the file to write instead, and letting every form the plan allows through.
Its `start` gives the instructions; its install writes the harness's shell for the system it runs on.

Short, and run on Linux, macOS and Windows (ci.yml's `guard` job): a release of the core made from this tree, a garden
grown from it, every replay a PreToolUse event on bin/hook.py's standard input.

Run: python3 test/guard.py   (0 = green; under a minute)
"""
import json, os, re, shlex, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import grow  # noqa: E402 — a release of the core made from this tree
from core import guards, judge, read  # noqa: E402
from core.law import Law  # noqa: E402

FAILS = []
PY = sys.executable
SYSTEM = 'windows' if os.name == 'nt' else 'macos' if sys.platform == 'darwin' else 'linux'


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


# THE RECORDED CASES (the one-shell design's measured cases), each by where it is recorded and the command form the
# law's vectors replay it as: the journal's mistakes of the zsh-and-bash kind, the memory note on --body, and the four
# commands zsh refused in the design conversation. Each is refused before it runs.
RECORDED = {
    "journal #27 (2026-10-17 21:01): an apostrophe in a single-quoted bash -c; the script did not run, the save went on":
        "bash -c 'python3 tools/choices.py beans/x.md \"the gardener's choices\"'; python3 bin/save.py agent \"x: the "
        "choices\" --body \"- action: x gained the choices\"",
    "journal #29 (2026-10-17 21:35): backquoted words run by zsh inside a double-quoted bash -c":
        "bash -c \"python3 tools/messages.py --set 'a copy goes under `Other`, by `folder`'\"",
    "journal #32 (2026-10-17 23:03): a backquoted word dropped from a docstring, inside a double-quoted bash -c":
        "bash -c \"sed -i 's/by date/by their `classes`/' lib/groups.py\"",
    "journal #49 (2026-10-22 21:03): a quote in a heredoc inside bash -c closed the outer quote; PowerShell unparsed":
        "bash -c 'ssh host powershell -Command - <<EOF\nGet-Service | Where-Object { $_.Name -eq 'svc' }\nEOF'",
    "the memory note dmsave-backquotes: a `word` in a double-quoted --body run as a command":
        "python3 bin/save.py agent \"the store\" --body \"- action: wrote `held` into the store\"",
    "design conversation: a heredoc inside bash -c for a journal entry":
        "bash -c 'cat > entry.md <<EOF\n- action: the plan written\nEOF\npython3 bin/save.py agent \"the plan\" < entry.md'",
    "design conversation: a query with quotes":
        "bash -c 'python3 -c \"import json; print(json.load(open(\\\"x.json\\\"))[\\\"a\\\"])\"'",
    "design conversation: an append to log/pending.md":
        "bash -c \"printf '%s\\n' '## an item · proposed' >> log/pending.md\"",
    "design conversation: an edit script":
        "bash -c 'python3 - <<PY\nimport re\np = \"beans/x.md\"\nPY'",
}
# THE FORMS THE PLAN NAMES AS ALLOWED (the one-shell design's guard): the file the refusal tells the agent to
# write, passed as the plan says. Each is let through.
PLANNED = ["bash script.sh", "python3 bin/save.py agent \"the store\" < entry.md", "ssh host bash -s < script.sh",
           "powershell -File script.ps1"]

T = tempfile.mkdtemp(prefix='guard-')
G = os.path.join(T, 'g')


class R:
    def __init__(self, p):
        self.returncode, self.out = p.returncode, p.stdout + p.stderr


def run(*a, cwd=None, stdin=None, env=None):
    e = dict(os.environ, GIT_AUTHOR_NAME='sam', GIT_AUTHOR_EMAIL='sam@x', GIT_COMMITTER_NAME='sam',
             GIT_COMMITTER_EMAIL='sam@x', PYTHONIOENCODING='utf-8')
    for k, v in (env or {}).items():
        if v is None:
            e.pop(k, None)
        else:
            e[k] = v
    return R(subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e,
                            input=stdin))


SHELL_ENV = {}            # the harness's shell as install sets it here, for the replays


def hook(verb, command='', tool='Bash', env=None):
    ev = {'session_id': 'abc123def456', 'cwd': G, 'hook_event_name': verb, 'tool_name': tool,
          'tool_input': {'command': command}}
    return run(PY, os.path.join(G, 'bin', 'hook.py'), verb, stdin=json.dumps(ev), env=dict(SHELL_ENV, **(env or {})))


def event(verb, tool, inp, sid='abc123def456', cwd=None, env=None):
    ev = {'session_id': sid, 'cwd': cwd or G, 'hook_event_name': verb, 'tool_name': tool, 'tool_input': inp}
    return run(PY, os.path.join(G, 'bin', 'hook.py'), verb, stdin=json.dumps(ev), env=dict(SHELL_ENV, **(env or {})))


def sh(path):
    """A path as the garden's shell takes it whole, on every system."""
    return shlex.quote(str(path).replace('\\', '/'))


# THE GARDENER'S CLAUSES naming the guards that take an operand, as a gardener would write them (operands of this test's
# own garden), the guard own-worktree, and a clause no guard reads
EXTRA = (
    "  - can:        { id: command-lines, by: { someone: session }, of: \"print another process's command line\" }\n"
    "  - forbidden:  { id: process-command-line, of: command-lines, through: self, clause: { guard: process-command-line, "
    "operand: { hosts: [db1] } } }\n"
    "  - can:        { id: secret-columns, by: { someone: session }, of: \"select a column that holds a secret\" }\n"
    "  - forbidden:  { id: secret-column, of: secret-columns, through: self, clause: { guard: secret-column, operand: "
    "{ columns: [password] } } }\n"
    "  - can:        { id: credential-files, by: { someone: session }, of: \"print a file that holds credentials\" }\n"
    "  - forbidden:  { id: credential-file, of: credential-files, through: self, clause: { guard: credential-file, "
    "operand: { files: [/root/rdp-launch] } } }\n"
    "  - can:        { id: other-copies, by: { someone: session }, of: \"write the garden only in its own session's "
    "worktree\" }\n"
    "  - obligatory: { id: own-worktree, of: other-copies, through: self, clause: { guard: own-worktree } }\n"
    "  - can:        { id: tmux-exact, by: { someone: session }, of: \"name a tmux target exactly\" }\n"
    "  - obligatory: { id: tmux-targets-exact, of: tmux-exact, through: self }\n")


def agreement(text=None):
    p = os.path.join(G, 'beans', 'agents-work.md')
    if text is None:
        with open(p, encoding='utf-8') as fh:
            return fh.read()
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


try:
    # ---- THE LAW: the table closed, each row held to its vectors
    law = Law.load()
    rows = guards.table(law)
    check("the law's table of guards holds its seven rows, each its stance and what it reads (core 3.6: III.1, III.2)",
          list(rows) == ['one-text-one-parser', 'shell-is', 'process-command-line', 'secret-column', 'credential-file',
                         'own-worktree', 'no-memory-write']
          and [rows[g]['stance'] for g in rows] == ['forbidden', 'obligatory', 'forbidden', 'forbidden', 'forbidden',
                                                    'obligatory', 'forbidden']
          and [rows[g]['reads'] for g in rows] == ['command', 'shell', 'command', 'command', 'command', 'path', 'path'],
          {g: (r.get('stance'), r.get('reads')) for g, r in rows.items()})
    check("every guard has its function and every function its row, and each row's vectors hold (the law's self-check)",
          not guards.problems(law) and not [p for p in law.problems() if 'guards' in p[1]], guards.problems(law))
    vec = rows['one-text-one-parser']['vectors']
    cmds = {v['command']: v['refused'] for v in vec}
    check(f"K1: each of the {len(RECORDED)} recorded cases is a vector of the law, refused",
          all(cmds.get(c) == 'true' for c in RECORDED.values()), [k for k, c in RECORDED.items() if cmds.get(c) != 'true'])
    check(f"...and each of the {len(PLANNED)} forms the plan names as allowed is a vector, let through",
          all(cmds.get(c) == 'false' for c in PLANNED), [c for c in PLANNED if cmds.get(c) != 'false'])
    broken = dict(law.guards['shell-is'], vectors=[{'operand': {'shell': 'bash', 'floor': '5.0'}, 'shell': 'zsh',
                                                    'version': '5.9', 'refused': 'false'}])
    fake = type('L', (), {'guards': dict(law.guards, **{'shell-is': broken}, extra={'guard': 'extra'})})()
    found = guards.problems(fake)
    check("a vector the function does not keep, and a row with no function, are the law's own problems",
          any('vectors[0]' in w for w, _m in found) and any('extra' in w for w, _m in found), found)

    # ---- A GARDEN, grown with the seed's agents' work agreement
    rel = grow.release(os.path.join(T, 'release'))
    r = grow.garden(rel, G, 'sam', '--zone', 'Europe/Istanbul')   # a runner may name its zone otherwise (`UTC`)
    check("a garden grows with the agents' work agreement planted beside its gardener, through its gate",
          r.returncode == 0 and os.path.isfile(os.path.join(G, 'beans', 'agents-work.md')) and '0 error(s)' in r.out,
          r.out[-1500:])
    if not os.path.isdir(G):
        raise RuntimeError("no garden grew, so nothing more can be judged")
    ins, bad = judge.instructions(None, judge.Scope.tree(G))
    check("the one judge reads the gardener's three instructions from it, and nothing it cannot read",
          sorted((i.guard, i.stance, i.where) for i in ins) == [
              ('no-memory-write', 'forbidden', 'agents-work#no-memory-write'),
              ('one-text-one-parser', 'forbidden', 'agents-work#one-text-one-parser'),
              ('shell-is', 'obligatory', 'agents-work#shell-is')] and not bad and not any(i.seed for i in ins),
          (ins, bad))
    settings = os.path.join(G, '.claude', 'settings.local.json')
    cfg = json.load(open(settings, encoding='utf-8')) if os.path.isfile(settings) else {}
    events = sorted((cfg.get('hooks') or {}))
    check("germination installs the agent's own door in the clone's own settings: the five events, start among them",
          events == ['PostToolUse', 'PreToolUse', 'SessionEnd', 'SessionStart', 'UserPromptSubmit'], cfg)
    import hook as dmhook  # noqa: E402 — this tree's, for the harness's rule and the shell it finds
    key = 'CLAUDE_CODE_GIT_BASH_PATH' if SYSTEM == 'windows' else 'CLAUDE_CODE_SHELL'
    path, why = dmhook.find_shell('bash', '5.0')
    set_to = (cfg.get('env') or {}).get(key)
    v = dmhook.shell_version(set_to) if set_to else None
    if path:
        check(f"K2 ({SYSTEM}): the install sets {key} to a bash at or above the floor, {set_to} ({v})",
              set_to == path and v and guards.version_of(v) >= (5, 0)
              and not (SYSTEM == 'macos' and set_to == '/bin/bash'), (cfg.get('env'), path, v))
        SHELL_ENV[key] = set_to
        r1 = run(PY, os.path.join(G, 'bin', 'hook.py'), 'install', 'claude-code', '--guard')
        r2 = run(PY, os.path.join(G, 'bin', 'hook.py'), 'install', 'claude-code')
        kept = json.load(open(settings, encoding='utf-8'))
        cmds = [x.get('command', '') for gs in (kept.get('hooks') or {}).values() for g in gs for x in g.get('hooks', [])]
        check("an install again — an upgrade's — keeps the guard the clone chose (`--guard`): the start and the guard",
              r1.returncode == 0 and r2.returncode == 0 and sorted(kept.get('hooks') or {}) == ['PreToolUse', 'SessionStart']
              and any(c.endswith(' guard') for c in cmds), (r1.out, r2.out, kept))
        with open(settings, 'w', encoding='utf-8', newline='\n') as fh:   # the five events again, for what follows
            json.dump(cfg, fh, indent=2)
            fh.write('\n')
    else:
        r = run(PY, os.path.join(G, 'bin', 'hook.py'), 'install', 'claude-code')
        check(f"K2 ({SYSTEM}): with no bash at the floor here, the install refuses, saying what to install, and sets "
              f"no shell", r.returncode == 1 and ('brew install bash' in r.out if SYSTEM == 'macos' else 'install' in r.out)
              and key not in (cfg.get('env') or {}), r.out)
        omissible = agreement().replace("  - obligatory: { id: shell-is,", "  - omissible: { id: shell-is,")
        agreement(omissible)                              # the replays below judge the command alone
        print(f"note  no bash 5.0 or later on this {SYSTEM} runner ({why}); shell-is lifted for the replays")

    # ---- THE HOOK: every recorded case refused before it runs, every allowed form let through
    for name, c in RECORDED.items():
        r = hook('pre', c)
        check(f"K1/C9: refused before it runs, naming the instruction and the file to write instead — {name}",
              r.returncode == 2 and 'agents-work#one-text-one-parser' in r.out and 'Instead, write' in r.out
              and 'with the file tools' in r.out, r.out)
    allowed = [v['command'] for v in vec if v['refused'] == 'false']
    wrong = [(c, hook('pre', c).out) for c in allowed]
    wrong = [(c, o) for c, o in wrong if o.strip()]
    check(f"no false refusal: each of the {len(allowed)} forms the law lets through passes the hook, the plan's "
          f"{len(PLANNED)} among them", not wrong, wrong)
    refused = [v['command'] for v in vec if v['refused'] == 'true' and v['command'] not in RECORDED.values()]
    missed = [c for c in refused if hook('pre', c).returncode != 2]
    check(f"...and each of the law's {len(refused)} other refused forms is refused by the hook", not missed, missed)

    # ---- THE GARDENER'S WORD: what lifts a guard, and what is no instruction
    base = agreement()
    agreement(base.replace("  - forbidden:  { id: one-text-one-parser,", "  - permitted:  { id: one-text-one-parser,"))
    r = hook('pre', RECORDED["the memory note dmsave-backquotes: a `word` in a double-quoted --body run as a command"])
    check("the gardener's `permitted` of the act lifts the guard: the command passes", r.returncode == 0, r.out)
    agreement(base)
    with open(os.path.join(G, 'beans', 'note.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write("---\nbean: note\nkind: contract\ntitle: \"a note an agent wrote\"\nsummary: \"Not the gardener's word.\"\n"
                 "statements:\n  - make: { by: { someone: session }, at: \"2026-10-23 12:00+03:00\" }\n"
                 "  - own: { by: sam, of: self }\n"
                 "  - can: { id: quoted-text, by: { someone: session }, of: \"quote freely\" }\n"
                 "  - permitted: { id: lift, of: quoted-text, through: self, clause: { guard: one-text-one-parser } }\n"
                 "---\nA note.\n")
    r = hook('pre', RECORDED["the memory note dmsave-backquotes: a `word` in a double-quoted --body run as a command"])
    check("a clause no `say` of the gardener covers is no instruction: written by an agent, it lifts nothing",
          r.returncode == 2 and 'agents-work#one-text-one-parser' in r.out, r.out)
    os.remove(os.path.join(G, 'beans', 'note.md'))
    os.rename(os.path.join(G, 'beans', 'agents-work.md'), os.path.join(T, 'agents-work.md'))
    r = hook('pre', RECORDED["journal #29 (2026-10-17 21:35): backquoted words run by zsh inside a double-quoted bash -c"])
    check("with no instruction of the garden naming a guard, the seed's default holds, and the refusal says so",
          r.returncode == 2 and "the seed's default instruction seed/agents-work.md.template#"
          + ('one-text-one-parser' if SHELL_ENV else 'shell-is') in r.out, r.out)   # with no bash here, its shell first
    os.rename(os.path.join(T, 'agents-work.md'), os.path.join(G, 'beans', 'agents-work.md'))
    agreement(base.replace("clause: { guard: one-text-one-parser }", "clause: { guard: one-text-two-parsers }"))
    r = hook('pre', 'ls')
    g = run(PY, os.path.join(G, 'bin', 'check.py'))
    check("a clause naming no guard of the law is refused by the gate (rule measured), and the door, failing closed, "
          "runs no command until it is corrected", r.returncode == 2 and 'cannot be read' in r.out
          and 'one-text-two-parsers' in r.out and g.returncode != 0 and 'no guard of the law' in g.out, (r.out, g.out[-600:]))
    for wrong, says in ((base.replace("operand: { shell: bash, floor: \"5.0\" }", "operand: { shell: tcsh, floor: \"5.0\" }"),
                         "no code of `technology`"),
                        (base.replace("floor: \"5.0\"", "floor: five"), "is not written as"),
                        (base.replace("operand: { shell: bash, floor: \"5.0\" }", "operand: { floor: \"5.0\" }"),
                         "`shell` is required"),
                        (base.replace("clause: { guard: one-text-one-parser }",
                                      "clause: { guard: one-text-one-parser, operand: { shell: bash } }"), "no attribute"),
                        (re.sub(r"  - (?:obligatory|omissible): \{ id: shell-is,", "  - permitted: { id: shell-is,", base),
                         "is neither"),
                        (base.replace("clause: { guard: one-text-one-parser }", "clause: { operand: { shell: bash } }"),
                         "name the guard")):
        agreement(wrong)
        g = run(PY, os.path.join(G, 'bin', 'check.py'))
        check(f"the gate refuses an instruction out of its form: {says}", g.returncode != 0 and says in g.out, g.out[-800:])
    agreement(base)

    # ---- SHELL-IS: the harness's shell, by its own rule
    if SHELL_ENV:
        fakes = os.path.join(T, 'shells')
        os.makedirs(fakes)
        if SYSTEM == 'windows':
            r = hook('pre', 'ls', env={'CLAUDE_CODE_GIT_BASH_PATH': os.path.join(fakes, 'no-such', 'bash.exe')})
            check("shell-is: where the harness would find no bash, every command is refused, naming the instruction",
                  r.returncode == 2 and 'agents-work#shell-is' in r.out and 'no shell' in r.out, r.out)
        else:
            for name, says, expect in (('zsh', 'zsh 5.9 (x86_64-pc-linux-gnu)', 'not bash'),
                                       ('bash', 'GNU bash, version 3.2.57(1)-release', 'below the floor 5.0')):
                p = os.path.join(fakes, name)
                with open(p, 'w', encoding='utf-8', newline='\n') as fh:
                    fh.write(f"#!/bin/sh\necho '{says}'\n")
                os.chmod(p, 0o755)
                r = hook('pre', 'ls', env={'CLAUDE_CODE_SHELL': p})
                check(f"shell-is: a harness whose shell is {says.split('(')[0].strip()} has every command refused, "
                      f"naming the instruction and what sets it", r.returncode == 2 and 'agents-work#shell-is' in r.out
                      and expect in r.out and 'bin/hook.py install claude-code' in r.out, r.out)
        r = hook('pre', 'ls')
        check("shell-is: the shell the install set meets it, and the command passes", r.returncode == 0, r.out)
    r = hook('start')
    try:
        said = json.loads(r.out)['hookSpecificOutput']['additionalContext']
    except (ValueError, KeyError, TypeError):
        said = ''
    check("start: the session begins with the gardener's instructions, each named, the shell's met or not",
          r.returncode == 0 and 'agents-work#one-text-one-parser' in said
          and (('agents-work#shell-is' in said and 'met, bash' in said) if SHELL_ENV
               else 'lifted by the gardener: shell-is' in said), r.out)
    r = hook('guard', RECORDED["design conversation: an append to log/pending.md"])
    r2 = hook('guard', "git -C ../release commit -q -m x")
    check("guard: the guards alone — a recorded case refused, a commit in another repository let through",
          r.returncode == 2 and 'agents-work#one-text-one-parser' in r.out and r2.returncode == 0, (r.out, r2.out))

    # ---- III.3: A COMMIT IS JUDGED BY THE REPOSITORY THE COMMAND NAMES, not by the folder the session stands in
    other = os.path.join(T, 'other-repo')
    run('git', 'init', '-q', other, cwd=T)
    for c, refused, what in (
            (f"git -C {sh(other)} commit -q --allow-empty -m x", False, "a commit in another repository, named by -C"),
            (f"cd {sh(other)} && git commit -q --allow-empty -m x", False, "a commit after a cd into another repository"),
            (f"git -C {sh(other)} push --no-verify origin main", False, "--no-verify in another repository"),
            ("git -C ../release commit -q -m x", False, "a commit in a folder that is no garden"),
            ("git commit -qm x", True, "a commit by hand in the garden the session stands in"),
            (f"cd {sh(other)} && git -C {sh(G)} commit -qm x", True, "a commit in the garden, named by -C from elsewhere"),
            (f"cd {sh(other)} && cd {sh(G)} && git commit --no-verify -qm x", True, "--no-verify in the garden, two cds on"),
            ("git -c core.hooksPath=/dev/null commit -qm x", True, "a hooks path of its own, in the garden"),
            ("git commit -nqm x", True, "a commit's -n in a cluster, in the garden"),
            ("git push --no-ver origin master", True, "--no-verify abbreviated, in the garden"),
            ("python3 bin/save.py sam \"fix\" --body \"- action: git commit by hand is refused\"", False,
             "a `git commit` inside another's text, which runs no git"),
            ("git commit -m \"--no-verify is the name of the flag\"", True, "a message that says --no-verify is a commit")):
        r = hook('pre', c)
        check(f"III.3 pre: {'refused' if refused else 'let through'} — {what}",
              (r.returncode == 2 and 'bin/save.py' in r.out) if refused else r.returncode == 0, (c, r.out))

    # ---- THE GARDENER'S CLAUSES naming the other guards, each with its operand, and one naming none
    W = os.path.join(T, 'sessions', 's1')
    run('git', 'worktree', 'add', '-q', '-b', 'session/s1', W)
    settings = os.path.join(G, '.claude', 'settings.local.json')
    was = open(settings, encoding='utf-8').read() if os.path.isfile(settings) else None
    r = run(PY, 'bin/install.py', cwd=W)
    check("install from a session's copy installs no agent's door: the main copy's settings stay as they were, and it "
          "says where the door is installed", r.returncode == 0 and "not installed from a session's copy" in r.out and
          (open(settings, encoding='utf-8').read() if os.path.isfile(settings) else None) == was, r.out[-800:])
    more = base.replace("---\nWhat every agent", EXTRA + "---\nWhat every agent")
    agreement(more)
    with open(os.path.join(W, 'beans', 'agents-work.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(more)
    g = run(PY, os.path.join(G, 'bin', 'check.py'))
    check("the gardener's clauses naming the five new guards, each with its operand, and a clause naming none, pass "
          "the gate", g.returncode == 0 and '0 error(s)' in g.out, g.out[-1200:])
    ins, bad = judge.instructions(None, judge.Scope.tree(G))
    cl = judge.clauses(None, judge.Scope.tree(G))
    check("...the one judge reads seven instructions from it, and the clause no guard reads among the agreement's other "
          "clauses", len(ins) == 7 and not bad and [c.where for c in cl] == ['agents-work#tmux-targets-exact']
          and cl[0].says == 'name a tmux target exactly', (ins, bad, cl))
    for wrong, says in ((more.replace("hosts: [db1]", "hosts: []"), "names none"),
                        (more.replace("columns: [password]", "columns: [\"pass word\"]"), "is not written as"),
                        (more.replace("files: [/root/rdp-launch]", "files: [rdp-launch]"), "is not written as"),
                        (more.replace("hosts: [db1]", "hosts: [{ name: db1 }]"), "is one value, written as text"),
                        (more.replace("clause: { guard: own-worktree }", "clause: { guard: own-worktree, operand: "
                                      "{ hosts: [db1] } }"), "no attribute")):
        agreement(wrong)
        g = run(PY, os.path.join(G, 'bin', 'check.py'))
        check(f"the gate refuses a new guard's operand out of its form: {says}", g.returncode != 0 and says in g.out,
              g.out[-800:])
    agreement(more)

    # ---- III.4: START gives every clause, and where the work stands
    r = hook('start')
    try:
        said = json.loads(r.out)['hookSpecificOutput']['additionalContext']
    except (ValueError, KeyError, TypeError):
        said = ''
    check("III.4 start: every clause of the agreement — those a guard checks, and the one the session keeps itself — "
          "and then now: the open session, the decisions, the courses, the latest handover",
          r.returncode == 0 and all(f'agents-work#{x}' in said for x in (
              'one-text-one-parser', 'no-memory-write', 'process-command-line', 'secret-column', 'credential-file',
              'own-worktree', 'tmux-targets-exact')) and 'no guard reads it: the session keeps it' in said
          and 'now — where the work stands' in said and 'open sessions: 1' in said and 'session-s1' in said
          and 'waiting on the gardener (sam)' in said and 'the latest handover' in said, r.out[-3000:])
    r = run(PY, os.path.join(G, 'bin', 'now.py'))
    check("ledger step 3: `now` is a tool of the garden, read and never stored, and says the same as start gave",
          r.returncode == 0 and r.out.strip() and r.out.strip() in said, r.out[-1500:])
    r = run(PY, os.path.join(G, 'bin', 'daftar.py'), 'now', '--json')
    try:
        nj = json.loads(r.out)
    except ValueError:
        nj = {}
    check("...`daftar now --json` gives it as data", r.returncode == 0 and nj.get('gardener') == 'sam'
          and [s['slug'] for s in nj.get('sessions') or []] == ['s1'], r.out[-1500:])

    # ---- C9: the journal's recorded breaches refused before they run, each naming the gardener's instruction
    CASES = {
        "2026-10-11: a process's command line printed on a host, `pgrep -af`": ("ssh db1 pgrep -af erp",
                                                                               'process-command-line'),
        "2026-10-10: a password column printed by a substring meant to keep its scheme":
            ("mysql mail -N -e \"SELECT username, SUBSTRING_INDEX(password, '$', 3) FROM mailbox\"", 'secret-column'),
        "2026-10-21: a credential file printed through a keyword filter":
            ("ssh db1 grep -v -i -E 'pass|token|secret|key|auth' /root/rdp-launch", 'credential-file'),
    }
    for name, (c, g_) in CASES.items():
        r = hook('pre', c)
        check(f"C9: refused before it runs, naming the instruction and what to do instead — {name}",
              r.returncode == 2 and f'agents-work#{g_}' in r.out and 'Instead,' in r.out, r.out)
    os.environ.update(SHELL_ENV)
    RG = os.path.realpath(G)
    OPERANDS = {'process-command-line': {'hosts': ['db1']}, 'secret-column': {'columns': ['password']},
                'credential-file': {'files': ['/root/rdp-launch']}}
    for g_, op in OPERANDS.items():
        vs = [v for v in rows[g_]['vectors'] if v.get('operand') == op and 'host' not in v]
        got = [(v, dmhook.guarded(RG, v['command'], [], {'session_id': 'abc123def456', 'cwd': RG})) for v in vs]
        wrong = [(v['command'], why) for v, why in got
                 if (bool(why) and f'agents-work#{g_}' in why) != (v['refused'] == 'true')]
        check(f"the door gives each of the law's {len(vs)} vectors of {g_} under the gardener's operand the verdict "
              f"the law gives it", vs and not wrong, wrong)

    # ---- III.2 and ledger step 5: A WRITE'S PATH — the harness's memory folder
    conf = os.path.join(T, 'claude-config')
    mem = os.path.join(conf, 'projects', '-x-garden', 'memory')
    os.makedirs(mem)
    ENV = {'CLAUDE_CONFIG_DIR': conf}
    r = event('pre', 'Write', {'file_path': os.path.join(mem, 'job-search.md')}, env=ENV)
    check("ledger step 5: a write into the harness's memory folder is refused, naming the instruction and the garden "
          "to write in instead", r.returncode == 2 and 'agents-work#no-memory-write' in r.out and 'bin/now.py' in r.out
          and 'bin/save.py' in r.out, r.out)
    for c, what in ((f"echo x >> {sh(os.path.join(mem, 'MEMORY.md'))}", "a shell's redirection into it"),
                    (f"cd {sh(mem)} && printf x > note.md", "a redirection a cd before it places there")):
        r = hook('pre', c, env=ENV)
        check(f"III.2: ...and so is {what}", r.returncode == 2 and 'agents-work#no-memory-write' in r.out, r.out)
    r = event('guard', 'Edit', {'file_path': os.path.join(mem, 'x.md')}, env=ENV)
    check("III.2 guard: the guards alone judge a write tool's path too", r.returncode == 2
          and 'agents-work#no-memory-write' in r.out, r.out)
    r = event('pre', 'Write', {'file_path': os.path.join(T, 'notes.md')}, env=ENV)
    check("...a write outside it passes", r.returncode == 0, r.out)
    cfg = json.load(open(settings, encoding='utf-8'))
    with open(settings, 'w', encoding='utf-8') as fh:
        json.dump(dict(cfg, autoMemoryDirectory=os.path.join(T, 'kept-by-the-harness')), fh)
    r = event('pre', 'Write', {'file_path': os.path.join(T, 'kept-by-the-harness', 'a.md')}, env=ENV)
    check("...and so is a write into the folder its autoMemoryDirectory setting names", r.returncode == 2
          and 'agents-work#no-memory-write' in r.out, r.out)
    with open(settings, 'w', encoding='utf-8') as fh:
        json.dump(cfg, fh)

    # ---- III.1 own-worktree: a session writes the garden only in its own worktree
    r = event('pre', 'Write', {'file_path': os.path.join(W, 'beans', 'x.md')})
    check("a write into a worktree of this garden is no write into another garden: one git directory",
          r.returncode == 0, r.out)
    claimed = dmhook.claim(RG, 's1', env={'CLAUDE_CODE_SESSION_ID': 'abc123def456'})
    r = event('pre', 'Write', {'file_path': os.path.join(G, 'beans', 'x.md')})
    check("own-worktree: the session's write into the main copy is refused, naming its own worktree", claimed ==
          ['claude-code'] and r.returncode == 2 and 'agents-work#own-worktree' in r.out and 's1' in r.out, r.out)
    for c, refused, what in (("printf x > beans/y.md", True, "a redirection into the main copy"),
                             (f"cd {sh(W)} && printf x > beans/y.md", False, "a redirection into its own worktree")):
        r = hook('pre', c)
        check(f"own-worktree: {'refused' if refused else 'let through'} — {what}",
              (r.returncode == 2 and 'agents-work#own-worktree' in r.out) if refused else r.returncode == 0, r.out)
    for inp, sid, cwd, refused, what in (
            ({'file_path': os.path.join(W, 'beans', 'x.md')}, 'abc123def456', G, False, "its write in its own worktree"),
            ({'file_path': os.path.join(T, 'scratch.txt')}, 'abc123def456', G, False, "a write outside every copy"),
            ({'file_path': os.path.join(G, 'beans', 'x.md')}, 'zzz999', G, False,
             "an agent the door knows no session of, writing the main copy"),
            ({'file_path': os.path.join(G, 'beans', 'x.md')}, 'zzz999', W, True,
             "an agent standing in a session's worktree is that session")):
        r = event('pre', 'Write', inp, sid=sid, cwd=cwd)
        check(f"own-worktree: {'refused' if refused else 'let through'} — {what}",
              (r.returncode == 2 and 'agents-work#own-worktree' in r.out) if refused else r.returncode == 0, r.out)
    # A SHELL NO ADAPTER READS (nv-s2-open 8): the harness's PowerShell tool goes unguarded — let through, said, and
    # recorded for the session it works in, whose close holds its bean to saying so
    r = event('pre', 'PowerShell', {'command': 'Get-Content secrets.txt | Write-Output'})
    r2 = event('guard', 'PowerShell', {'command': 'Remove-Item beans/x.md'})
    sys.path.insert(0, os.path.join(G, 'bin'))
    import session as dmsession
    dmsession.ROOT = RG
    went = dmsession.unguarded('s1')
    check("a PowerShell command, whose grammar no adapter reads, goes UNGUARDED at `pre` and at `guard` — let through, "
          "said to the model, and recorded for the session it works in", r.returncode == 0 and r2.returncode == 0
          and 'UNGUARDED' in r.out and 'UNGUARDED' in r2.out and len(went) == 2
          and {w.get('slug') for w in went} == {'s1'}, (r.out, r2.out, went))
    check("...and the session's close is held to its bean saying so (`details.unguarded`)",
          not dmsession.said_unguarded(W, 's1'), W)
    dmsession.unguarded('s1', release=True)
    check("...and forgotten once the session closes", dmsession.unguarded('s1') == [])
    dmhook.claim(RG, 's1', release=True)
    r = event('pre', 'Write', {'file_path': os.path.join(G, 'beans', 'x.md')})
    check("own-worktree: released as the session closes, the record no longer holds", r.returncode == 0, r.out)
    # THE WATERMARK (ledger step 5, nb-s5-open 5): at `end`, of the session's prompts, those no save traced a value to,
    # counted, kept beside its material, said to the person; `watermark` reads them back
    W2 = os.path.join(T, 'wm')
    r = grow.garden(rel, W2, 'sam', '--zone', 'Europe/Istanbul')
    hk = os.path.join(W2, 'bin', 'hook.py')

    def wm(verb, **ev):
        return run(PY, hk, verb, stdin=json.dumps(dict({'session_id': 'wm0123456789', 'cwd': W2, 'hook_event_name': verb},
                                                       **ev)), env=dict(SHELL_ENV))
    r1 = wm('prompt', prompt='the kiosk on the shop floor answers at 192.0.2.77')
    r2 = wm('prompt', prompt='and keep the notes short')
    with open(os.path.join(W2, 'beans', 'kiosk.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('---\nbean: kiosk\nkind: host\ntitle: "the kiosk"\nstatements:\n  - say: { by: sam, at: now }\n'
                 '  - be: { by: self, at: 192.0.2.77, as: location }\n---\nThe kiosk on the shop floor.\n')
    r3 = run(PY, os.path.join(W2, 'bin', 'save.py'), 'sam', 'the kiosk and where it answers', '--body',
             '- action: [[kiosk]] where it answers', cwd=W2)
    r4 = wm('end')
    r5 = run(PY, hk, 'watermark', '--json', cwd=W2)
    try:
        ends = json.loads(r5.out)
    except ValueError:
        ends = r5.out
    check("the watermark: at `end`, of the session's two prompts the one no save traced a value to is counted and said "
          "to the person, and `watermark` reads it back", r.returncode == 0 and r1.returncode == 0 and r2.returncode == 0
          and r3.returncode == 0 and r4.returncode == 0 and "of this session's 2 prompt(s), 1 reached no save" in r4.out
          and isinstance(ends, list) and len(ends) == 1 and (ends[0].get('prompts'), ends[0].get('drawn'),
                                                             ends[0].get('untraced')) == (2, 1, 1),
          (r3.out[-600:], r4.out, ends))
    r = run(PY, os.path.join(G, 'bin', 'hook.py'), 'uninstall', 'claude-code')
    cfg = json.load(open(settings, encoding='utf-8'))
    check("uninstall takes the hooks out and keeps the shell it set", r.returncode == 0 and 'hooks' not in cfg
          and (not SHELL_ENV or cfg.get('env', {}).get(key) == SHELL_ENV.get(key)), (r.out, cfg))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nguard: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
