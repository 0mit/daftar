#!/usr/bin/env python3
"""install — this garden's git hooks and semantic merge driver, into this clone.

    python3 bin/install.py            # from anywhere inside the clone

Hooks and merge-driver config live in .git/, which is NOT cloned, so every fresh clone runs this once.
There is exactly ONE installer, and this is it; `bin/install.sh` only hands over to it. The versioned
hooks in bin/hooks/ are the source of truth and this script only copies them — copied, never generated,
so what runs is what is reviewed. A `.sh` file there is no hook but a part the hooks source (python.sh), and
is copied beside them, so an installed hook never depends on what the working tree happens to hold.

It is Python and not shell because a garden is grown on Windows too, where `sh` is not a given but the
Python that runs the gate is. The hooks themselves stay `sh`: git runs them with the shell it ships.

WHICH PYTHON the hooks and the merge driver run is CHOSEN, not assumed: the first that runs AND imports yaml,
of `git config daftar.python`, python3, python, `py -3` and, last, the Python running this. A name that is
found but does not run — on Windows, the Microsoft Store's App execution alias for `python3` or `python` — is
skipped, as is a Python without PyYAML. The choice is recorded per clone as `git config daftar.python`, which
bin/hooks/python.sh reads first; when nothing works, the refusal names each candidate and why.
"""
import os
import shutil
import stat
import subprocess
import sys

# The order bin/hooks/python.sh tries too; the recorded choice goes first, the running interpreter last.
CANDIDATES = (['python3'], ['python'], ['py', '-3'])
STORE_ALIAS = ("is the Microsoft Store alias (App execution aliases), which runs no Python — install Python from "
               "python.org, or turn the alias off in Settings > Apps > Advanced app settings > App execution aliases")


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True)


def _run(cmd, code):
    try:
        return subprocess.run(cmd + ['-c', code], capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None


def probe(cmd):
    """(the interpreter's own path, None) when `cmd` runs and imports yaml, else (None, why not)."""
    r = _run(cmd, 'import sys, yaml; print(sys.executable)')
    if r is not None and r.returncode == 0 and r.stdout.strip():
        # forward slashes: a path Git's sh (the hooks, the merge driver) and Windows both read
        return r.stdout.strip().splitlines()[-1].replace('\\', '/'), None
    shown = ' '.join(cmd) if cmd[0] == 'py' else (f'"{cmd[0]}"' if ' ' in cmd[0] else cmd[0])
    found = shutil.which(cmd[0])
    if not found and not os.path.isfile(cmd[0]):
        return None, 'not found'
    ran = _run(cmd, 'import sys')
    if ran is not None and ran.returncode == 0:
        return None, f'runs, but PyYAML is missing: {shown} -m pip install PyYAML'
    if 'WindowsApps' in (found or cmd[0]):
        return None, STORE_ALIAS
    return None, f'is at {found or cmd[0]} but does not run'


def choose_python(repo):
    """(path, None) for the Python this clone's tools run with, recorded as `git config daftar.python`;
    (None, the refusal naming each candidate and why) when none runs and imports yaml."""
    recorded = git('config', '--get', 'daftar.python', cwd=repo).stdout.strip()
    tried, why = [], []
    # a recorded `py -3` is the launcher and its switch; anything else is one name or path, which may hold a space
    cands = ([recorded.split() if recorded.startswith('py -') else [recorded]] if recorded else []) \
        + [list(c) for c in CANDIDATES] + [[sys.executable]]
    for cmd in cands:
        if cmd in tried:
            continue
        tried.append(cmd)
        exe, no = probe(cmd)
        if exe:
            if not (recorded and cmd == cands[0]):
                git('config', 'daftar.python', exe, cwd=repo)
            return exe, None
        label = ('git config daftar.python (' + recorded + ')' if recorded and cmd == cands[0] else
                 'the Python running this (' + sys.executable + ')' if cmd == [sys.executable] else ' '.join(cmd))
        why.append(f"  {label}: {no}")
    return None, ("no Python here runs the tools. Each candidate, and why:\n" + '\n'.join(why) +
                  "\nInstall Python 3 with PyYAML (pip install PyYAML), or name one that works:\n"
                  "  git config daftar.python <path-to-python>")


def install(repo=None, quiet=False):
    say = (lambda *a: None) if quiet else print
    if repo is None:
        r = git('rev-parse', '--show-toplevel')
        if r.returncode != 0:
            raise SystemExit("install: not inside a git repository")
        repo = r.stdout.strip()
    git_dir = git('rev-parse', '--git-common-dir', cwd=repo).stdout.strip() or '.git'
    if not os.path.isabs(git_dir):
        git_dir = os.path.join(repo, git_dir)
    hooks_dst = os.path.join(git_dir, 'hooks')
    os.makedirs(hooks_dst, exist_ok=True)

    # 1) the versioned hooks, and what they source
    for name in sorted(os.listdir(os.path.join(repo, 'bin', 'hooks'))):
        src, dst = os.path.join(repo, 'bin', 'hooks', name), os.path.join(hooks_dst, name)
        if name.endswith('.sh'):
            shutil.copyfile(src, dst)                       # sourced by the hooks, never run by git
            continue
        # THE GATE IS FOR A GARDEN. This repository can also BE the language itself (the daftar repo, or a
        # clone of it), which has no GARDEN.md and no beans: there the gate has nothing to judge and dies on
        # the missing vocabulary, taking the commit with it. The pre-push leak check belongs in BOTH.
        if name == 'pre-commit' and not os.path.isfile(os.path.join(repo, 'GARDEN.md')):
            say(f"skipped {os.path.relpath(hooks_dst, repo)}/pre-commit — no GARDEN.md here, so this repo is the language, not a garden")
            continue
        shutil.copyfile(src, dst)
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        say(f"installed {os.path.relpath(dst, repo)}")

    # 2) the Python they run: chosen once here, recorded for the hooks (they check it again on every run).
    py, refusal = choose_python(repo)
    if py:
        say(f"python for this clone: {py}  (git config daftar.python)")

    # 3) the semantic merge driver, referenced by .gitattributes (merge=daftar). Git does NOT warn when an
    #    attribute names a driver that is not configured — it silently text-merges instead. The attribute
    #    and this config must therefore always change together. The interpreter is named by its full path,
    #    because `python3` is not a name every machine has, and not every name on a PATH is a Python.
    driver = os.path.join(repo, 'bin', 'dmmerge.py')
    git('config', 'merge.daftar.name', 'daftar semantic merge (dmmerge)', cwd=repo)
    git('config', 'merge.daftar.driver', f'"{py or sys.executable}" "{driver}" --file %O %A %B', cwd=repo)
    say("configured merge driver 'daftar' -> bin/dmmerge.py")
    if refusal:
        # The hooks are installed all the same: a hook that refuses with this message is the gate still
        # standing; no hook at all would let every commit through unjudged.
        print(f"install: {refusal}", file=sys.stderr)
        return 1
    say(f"installed: pre-commit gate + semantic merge driver in {os.path.relpath(git_dir, repo)}")
    return 0


if __name__ == '__main__':
    sys.exit(install())
