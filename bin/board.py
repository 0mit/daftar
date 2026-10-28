#!/usr/bin/env python3
"""board — this garden's board in the browser: a cursor kept while the aspect turns, served by this machine's daftard.

    python3 bin/board.py                   # this garden's board
    python3 bin/board.py --garden <name>   # another garden this machine's daftard serves, by its name
    python3 bin/board.py --help

(`python` on Windows.) The board is the view profile's archetype `cursor`, read (assets/view/README.md): a garden that
takes no view profile has none, and its page says so. It is daftard's page, `/board?g=<garden>`: this asks daftard to
open it (`daftard open`), which starts daftard if it is not running and opens the page by a one-time code, so no
command line and no browser history holds the machine's key. The garden is found in daftard.json by its working copy's
path; one it does not serve is served by `python3 bin/install.py --daftard`, run in that garden.
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import install as dminstall  # noqa: E402 — where daftard's state is
import serve as dmserve  # noqa: E402 — which daftard runs


def served(path):
    """The name daftard.json gives the garden whose working copy is at `path` (the main copy, a session's is not
    served), or (None, why)."""
    conf = os.path.join(dminstall.state_dir(), 'daftard.json')
    try:
        with open(conf, encoding='utf-8') as fh:
            gardens = json.load(fh).get('gardens') or []
    except OSError:
        return None, f"this machine's daftard serves no garden yet ({conf} is not there)"
    except ValueError as e:
        return None, f"{conf} does not read: {e}"
    main = os.path.realpath(dminstall.main_worktree(path))
    for g in gardens:
        if isinstance(g, dict) and g.get('path') and os.path.realpath(g['path']) == main:
            return g.get('name') or os.path.basename(g['path']), ''
    return None, f"this machine's daftard does not serve the garden at {main}"


def main(argv):
    ap = argparse.ArgumentParser(prog='board', description=__doc__.split('\n', 1)[0],
                                 formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__.split('\n\n', 2)[2])
    ap.add_argument('--garden', help='another garden this machine\'s daftard serves, by the name daftard.json gives it')
    a = ap.parse_args(argv)
    exe = dmserve.binary()
    if exe is None:
        print("board: daftard is not installed for this account on this machine: run `python3 bin/install.py "
              "--daftard` in this garden", file=sys.stderr)
        return 2
    name, why = (a.garden, '') if a.garden else served(ROOT)
    if not name:
        print(f"board: {why}: run `python3 bin/install.py --daftard` in it", file=sys.stderr)
        return 2
    return dmserve.run(exe, ['open', f'/board?g={name}'])


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
