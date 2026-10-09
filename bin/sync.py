#!/usr/bin/env python3
"""sync — keep this clone of the garden in step with its peers: fetch each, judge what it brings, merge what passes.

    python3 bin/sync.py [<remote> ...]     # every remote of this clone, or those named

EVERY MACHINE OF A GARDEN IS A PEER (design §7.1), and the receiver judges what it receives. For each peer — a git
remote of this clone — its branch of the same name as this one is fetched into a quarantine ref,
`refs/daftar/incoming/<remote>`, and every commit it brings that this clone's own branches do not is judged by the
hub's own rules (bin/hub.py `receive`): signed by a key a writer's bean carries as the garden stood at its parent,
within that writer's rights, and the gate on the tree it would make. A peer that brings a commit that fails is left
out, nothing merged, and the refusal said (the writer's to fix, then the gardener's). What passes is merged: a
fast-forward where this clone has nothing of its own, else a merge commit made by the garden's own merge driver and
saved with its entry through the gate (bin/save.py); a merge that stops on a conflict is taken back whole and said —
a person's to settle (class J).

Nothing is pushed into a peer's working copy: each peer fetches for itself. A remote this clone pushes to is one
marked as a hub, `git config remote.<name>.daftar-push true` (a bare repository that judges what it takes). And never
over someone's work: a working tree with changes not yet saved waits, nothing fetched into it.

Exit 0 when every peer was in step or taken, 1 when one was refused or stopped.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr
import hub as dmhub  # noqa: E402 — the one judge of a commit: the hub's rules, at every receiver


def git(*a, check=False):
    r = subprocess.run(['git', *a], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(a)}: {(r.stdout + r.stderr).strip()[-300:]}")
    return r


def ancestor(a, b):
    return git('merge-base', '--is-ancestor', a, b).returncode == 0


def step(remote, branch):
    """One peer: fetched, judged, merged. (ok, what was done)."""
    ref = f"refs/daftar/incoming/{remote}"
    f = git('fetch', '-q', '--no-tags', remote, f"+{branch}:{ref}")
    if f.returncode != 0:
        return True, f"{remote}: not reached, or no branch {branch} there — nothing taken ({f.stderr.strip()[-160:]})"
    head = git('rev-parse', 'HEAD').stdout.strip()
    theirs = git('rev-parse', ref).stdout.strip()
    if theirs == head or ancestor(theirs, head):
        return True, f"{remote}: in step"
    refused = dmhub.receive(ref)
    if refused:
        return False, f"{remote}: REFUSED, nothing merged —\n  " + '\n  '.join(refused)
    n = git('rev-list', '--count', f"{head}..{theirs}").stdout.strip()
    if ancestor(head, theirs):
        git('merge', '--ff-only', '-q', theirs, check=True)
        return True, f"{remote}: merged {n} commit(s), a fast-forward — each judged first"
    m = git('merge', '--no-commit', '--no-ff', theirs)
    if m.returncode != 0:
        git('merge', '--abort')
        return False, f"{remote}: the merge stops on a conflict, taken back whole — a person's to settle (class J)"
    names = git('diff', '--cached', '--name-only', 'HEAD', '--', 'beans', 'mappings').stdout.split()
    beans = [os.path.basename(p)[:-3] for p in names if p.endswith('.md')]     # its entry names every bean it brings
    s = subprocess.run([sys.executable, os.path.join(HERE, 'save.py'), 'sync', f"merged {remote}'s {n} commit(s)",
                        '--body', f"- action: merged {n} commit(s) from {remote}, each judged first by the hub's rules "
                                  f"(bin/hub.py receive), each bean by its statements (bin/merge.py): "
                                  + (', '.join(f'[[{b}]]' for b in beans) or 'no bean')],
                       cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace')
    if s.returncode != 0:
        git('merge', '--abort')
        git('reset', '-q', '--hard', head)
        return False, f"{remote}: the merge was refused at its save, taken back — {(s.stdout + s.stderr).strip()[-400:]}"
    return True, f"{remote}: merged {n} commit(s), each judged first"


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    if git('status', '--porcelain').stdout.strip():
        print("sync: this working tree has changes not yet saved — it waits; nothing was fetched into it", file=sys.stderr)
        return 1
    branch = git('symbolic-ref', '--short', 'HEAD').stdout.strip()
    if not branch:
        print("sync: this clone is on no branch", file=sys.stderr)
        return 1
    remotes = argv or [r for r in git('remote').stdout.split() if r]
    ok = True
    for remote in remotes:
        good, said = step(remote, branch)
        ok = ok and good
        print(f"sync: {said}")
        if good and git('config', '--bool', f"remote.{remote}.daftar-push").stdout.strip() == 'true':
            p = git('push', '-q', remote, branch)
            print(f"sync: {remote}: " + ('pushed' if p.returncode == 0 else f"not pushed — {p.stderr.strip()[-300:]}"))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
