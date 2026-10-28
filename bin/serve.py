#!/usr/bin/env python3
"""serve — this machine's daftard: the gardens' pages and board, their sync, what waits and for whom, their routines.

    python3 bin/serve.py                       # `daftard serve`: run it here, in the foreground
    python3 bin/serve.py <command> [args ...]  # any of daftard's own: status, stop, open, leads, error, version, help, ...
    python3 bin/serve.py --help                # this, and daftard's own commands

(`python` on Windows.) daftard is one per machine: it starts one daemon for each garden its daftard.json names, serves
their pages and the board on this machine's loopback, keeps each in step with its hub where it is told to, says what
waits and for whom, and each minute asks a garden whose settings say `routines: true` to run its routines
(`bin/routines.py tick`). `python3 bin/install.py --daftard` lays its binary in this account's daftar state folder,
serves the garden it is run in, and has the system keep it running; this runs that binary, or one on the PATH where
none is laid. Whatever it prints, and how it ends, are daftard's own.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import install as dminstall  # noqa: E402 — where the install lays daftard


def binary():
    """The daftard this account runs: the one the install laid in its state folder, else one on the PATH; or None."""
    laid = dminstall.daftard_path()
    return laid if os.path.isfile(laid) else shutil.which('daftard')


def run(exe, args):
    """daftard run with this process's own standard handles given it by name. On Windows daftard is a windowed program
    (no console of its own), and what it prints reaches this one's output only through the handles it is given."""
    sys.stdout.flush()
    try:
        std = {'stdin': sys.stdin, 'stdout': sys.stdout, 'stderr': sys.stderr}
        for f in std.values():
            f.fileno()
    except (AttributeError, OSError, ValueError):
        std = {}
    return subprocess.run([exe, *args], **std).returncode


def main(argv):
    exe = binary()
    if argv and argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        if exe:
            print(f"\ndaftard, at {exe}:\n")
            run(exe, ['help'])
        return 0
    if exe is None:
        print("serve: daftard is not installed for this account on this machine: run `python3 bin/install.py --daftard` "
              "in a garden", file=sys.stderr)
        return 2
    return run(exe, argv or ['serve'])


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    except KeyboardInterrupt:
        sys.exit(130)
