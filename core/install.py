#!/usr/bin/env python3
"""install — the core's gate into this clone, for a garden written in the core's statements.

    python3 core/install.py

(`python` on Windows.) It runs bin/install.py's install first: the hooks it versions, the Python they run, recorded per
clone. Then it puts core/hooks/pre-commit in the place of that pre-commit, so a commit here meets the core's gate
(`core/check.py --staged`) whatever GARDEN.md pins: for rehearsing the core on a copy that still pins std-vocab. A
garden needs only bin/install.py, whose hooks take the gate of the law its pin names (v1 part 3)."""
import os
import stat
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bin'))
import install as hooks  # noqa: E402 — bin/install.py: the copy that keeps LF, and the Python chosen once


def main():
    top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], capture_output=True, text=True)
    if top.returncode != 0:
        print("core install: not inside a git repository", file=sys.stderr)
        return 1
    repo = top.stdout.strip()
    hooks.install(repo, quiet=True)
    gd = subprocess.run(['git', '-C', repo, 'rev-parse', '--git-common-dir'], capture_output=True, text=True).stdout.strip()
    gd = gd if os.path.isabs(gd) else os.path.join(repo, gd or '.git')
    dst = os.path.join(gd, 'hooks', 'pre-commit')
    hooks.copy_lf(os.path.join(repo, 'core', 'hooks', 'pre-commit'), dst)
    os.chmod(dst, os.stat(dst).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    print(f"installed {os.path.relpath(dst, repo)} — the core's gate (core/check.py --staged)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
