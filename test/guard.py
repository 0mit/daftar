"""The agent's own door (P6 of the next version, steps 1 and 2 of the design of one shell): the law's closed table of
guards, each held to its vectors; the gardener's instruction as a clause of the agents' work agreement, read through the
one judge; the seed's default; and bin/hook.py refusing, before it runs, every recorded case of one interpreter's text inside
another's quotes, naming the instruction and the file to write instead, and letting every form the plan allows through.
Its `start` gives the instructions; its install writes the harness's shell for the system it runs on.

Short, and run on Linux, macOS and Windows (ci.yml's `guard` job): a release of the core made from this tree, a garden
grown from it, every replay a PreToolUse event on bin/hook.py's standard input.

Run: python3 test/guard.py   (0 = green; under a minute)
"""
import json, os, re, shutil, subprocess, sys, tempfile

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
    check("the law's table of guards holds one-text-one-parser and shell-is, each its stance, what it reads and takes",
          list(rows) == ['one-text-one-parser', 'shell-is']
          and [rows[g]['stance'] for g in rows] == ['forbidden', 'obligatory']
          and [rows[g]['reads'] for g in rows] == ['command', 'shell'], {g: (r.get('stance'), r.get('reads'))
                                                                          for g, r in rows.items()})
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
    check("the one judge reads the gardener's two instructions from it, and nothing it cannot read",
          sorted((i.guard, i.stance, i.where) for i in ins) == [
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
    r3 = hook('pre', "git -C ../release commit -q -m x")
    check("guard: the guards alone — a recorded case refused, a commit in another repository let through, which `pre` "
          "refuses as a commit by hand in the garden", r.returncode == 2 and 'agents-work#one-text-one-parser' in r.out
          and r2.returncode == 0 and r3.returncode == 2, (r.out, r2.out, r3.out))
    r = run(PY, os.path.join(G, 'bin', 'hook.py'), 'uninstall', 'claude-code')
    cfg = json.load(open(settings, encoding='utf-8'))
    check("uninstall takes the hooks out and keeps the shell it set", r.returncode == 0 and 'hooks' not in cfg
          and (not SHELL_ENV or cfg.get('env', {}).get(key) == SHELL_ENV.get(key)), (r.out, cfg))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nguard: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
