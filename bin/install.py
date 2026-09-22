#!/usr/bin/env python3
"""install — this garden's git hooks and semantic merge driver, into this clone.

    python3 bin/install.py            # from anywhere inside the clone

Hooks and merge-driver config live in .git/, which is NOT cloned, so every fresh clone runs this once.
There is exactly ONE installer, and this is it; `bin/install.sh` only hands over to it. The versioned
hooks in bin/hooks/ are the source of truth and this script only copies them — copied, never generated,
so what runs is what is reviewed.

It is Python and not shell because a garden is grown on Windows too, where `sh` is not a given but the
Python that runs the gate is. The hooks themselves stay `sh`: git runs them with the shell it ships.
"""
import os
import shutil
import stat
import subprocess
import sys


def git(*args, cwd=None):
    return subprocess.run(['git', *args], cwd=cwd, capture_output=True, text=True)


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

    # 1) the versioned hooks
    for name in sorted(os.listdir(os.path.join(repo, 'bin', 'hooks'))):
        if name.endswith('.sh'):
            continue
        # THE GATE IS FOR A GARDEN. This repository can also BE the language itself (the daftar repo, or a
        # clone of it), which has no GARDEN.md and no beans: there the gate has nothing to judge and dies on
        # the missing vocabulary, taking the commit with it. The pre-push leak check belongs in BOTH.
        if name == 'pre-commit' and not os.path.isfile(os.path.join(repo, 'GARDEN.md')):
            say(f"skipped {os.path.relpath(hooks_dst, repo)}/pre-commit — no GARDEN.md here, so this repo is the language, not a garden")
            continue
        src, dst = os.path.join(repo, 'bin', 'hooks', name), os.path.join(hooks_dst, name)
        shutil.copyfile(src, dst)
        os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        say(f"installed {os.path.relpath(dst, repo)}")

    # 2) the semantic merge driver, referenced by .gitattributes (merge=daftar). Git does NOT warn when an
    #    attribute names a driver that is not configured — it silently text-merges instead. The attribute
    #    and this config must therefore always change together. The interpreter is the one running this,
    #    by its full path, because `python3` is not a name every machine has.
    driver = os.path.join(repo, 'bin', 'dmmerge.py')
    git('config', 'merge.daftar.name', 'daftar semantic merge (dmmerge)', cwd=repo)
    git('config', 'merge.daftar.driver', f'"{sys.executable}" "{driver}" --file %O %A %B', cwd=repo)
    say("configured merge driver 'daftar' -> bin/dmmerge.py")
    say(f"installed: pre-commit gate + semantic merge driver in {os.path.relpath(git_dir, repo)}")
    return 0


if __name__ == '__main__':
    sys.exit(install())
