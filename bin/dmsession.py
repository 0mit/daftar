#!/usr/bin/env python3
"""dmsession — open, list and close daftar sessions that can run SIDE BY SIDE on one host.

THE PROBLEM THIS SOLVES, stated because the fix looks like bureaucracy until you have hit it. Two
sessions working one clone share one git INDEX. `git add -A` from either stages the other's
half-finished edits, and the gate reads the STAGED blobs — so session A can be refused for session B's
mistake, or worse, commit B's unfinished bean under A's message with A's journal entry attached. Nothing
in the ledger's own rules catches that: both writes are individually legal.

A git WORKTREE gives each session its own working copy and its OWN INDEX while sharing one object store.
So the sessions cannot stage over each other, and they can still see and merge one another's branches
without a network round trip — which is the "sync / pass ability between sessions" half of the ask.

Hooks are shared from the common git directory, so the gate installed by bin/install.sh applies in every
worktree automatically. That is checked by `open`, not assumed: a session running without the gate is
worse than no session, and this tool refuses to create one.

    python3 bin/dmsession.py open  <slug> --purpose "..."   # branch + worktree + session bean
    python3 bin/dmsession.py list                           # what is open, where, and how far along
    python3 bin/dmsession.py close <slug>                   # gate, merge back, retire the worktree
"""
import argparse
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse

def _main_working_copy():
    """The MAIN working copy, never whichever one this script happens to be sitting in.

    ROOT used to be derived from `__file__`, which is wrong the moment somebody runs
    `python3 bin/dmsession.py close <slug>` from inside the session worktree — the natural thing to do,
    since that is where they have been working. Every git call then operated on the WORKTREE: the merge
    became the branch merging into itself ("already up to date", exit 0, nothing merged), and
    `worktree remove` deleted the caller's own current directory out from under them. Recovered by
    merging by hand; the branch had the commit, so nothing was lost but the trust.
    `git worktree list` names the main copy first, always, whichever copy asks.
    """
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = subprocess.run(('git', 'worktree', 'list', '--porcelain'),
                         cwd=here, capture_output=True, text=True)
    for line in out.stdout.splitlines():
        if line.startswith('worktree '):
            return line[len('worktree '):]
    return here


ROOT = _main_working_copy()
SESSIONS_DIR = os.path.abspath(os.path.join(ROOT, os.pardir, 'daftar-sessions'))
SLUG = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')


def git(*args, cwd=ROOT, check=True):
    """BOTH STREAMS ON FAILURE. This reported `r.stderr` alone, and git writes `CONFLICT (content):
    ...` to STDOUT — so the one failure this tool can actually cause printed
    `git merge --no-ff session/beta -m close session beta failed:` and then NOTHING. An operator was
    told a command failed and not one word about what, where, or that their main working copy was now
    sitting mid-merge. Measured 2026-08-08 in a sandbox; the empty line is the whole reason `close`
    was undiagnosable."""
    r = subprocess.run(('git',) + args, cwd=cwd, capture_output=True, text=True)
    if check and r.returncode:
        detail = '\n'.join(s.strip() for s in (r.stdout, r.stderr) if s.strip())
        sys.exit(f"git {' '.join(args)} failed:\n{detail or '(git said nothing on either stream)'}")
    return r.stdout.strip()


def worktrees():
    """Every worktree this repository has, as {path: branch}."""
    out, cur = {}, None
    for line in git('worktree', 'list', '--porcelain').splitlines():
        if line.startswith('worktree '):
            cur = line[len('worktree '):]
        elif line.startswith('branch ') and cur:
            out[cur] = line[len('branch refs/heads/'):]
    return out


def gate_is_installed():
    """The gate is a shared hook, but SHARED IS NOT INSTALLED — a fresh clone has no .git/hooks content
    at all, which is exactly why bin/hooks/pre-commit is versioned. Checked rather than believed."""
    common = git('rev-parse', '--git-common-dir')
    if not os.path.isabs(common):
        common = os.path.join(ROOT, common)
    return os.path.exists(os.path.join(common, 'hooks', 'pre-commit'))


def _bean_kind(bean):
    """The `kind` of beans/<bean>.md in the main copy, or None when there is no such bean."""
    path = os.path.join(ROOT, 'beans', f'{bean}.md')
    if not os.path.isfile(path):
        return None
    fm = dmparse.loads(dmparse.read(path)[0] or '') or {}
    return fm.get('kind') if isinstance(fm, dict) else None


def resolve_edge(flag, name, want_kind=None):
    """Which bean the session bean names as its `host` or its `owner`: the flag, else this clone's
    `git config daftar.<name>`, else a refusal.

    NO DEFAULT, AND NO GUESS. This template once wrote one operator and one machine into every session bean, which was
    right for one clone of one garden and five dangling-ref errors in every other: a germinated garden
    opened its first session already red. The host is a fact about the MACHINE this clone lives on, so it
    is kept in the clone's own git config, set once per clone, and never in text every clone shares."""
    value = flag or git('config', '--get', f'daftar.{name}', check=False)
    if not value:
        sys.exit(f"REFUSING: the session bean needs a {name} and none is known. Pass --{name} <bean>, or set it\n"
                 f"once for this clone: git config daftar.{name} <bean>")
    kind = _bean_kind(value)
    if kind is None:
        sys.exit(f"REFUSING: {name} '{value}' has no bean in beans/ — the session bean would open with a dangling "
                 f"ref. Name an existing bean, or write that one first.")
    if want_kind and kind not in (want_kind if isinstance(want_kind, tuple) else (want_kind,)):
        sys.exit(f"REFUSING: {name} '{value}' is kind '{kind}', not '{want_kind}'.")
    return value


def cmd_open(a):
    if not SLUG.match(a.slug):
        sys.exit(f"'{a.slug}' is not kebab-case. A session is named for its PURPOSE — "
                 "'split-api-for-multi-version-support', not a date and a host.")
    if not gate_is_installed():
        sys.exit("REFUSING: no pre-commit hook in the shared git dir. Run `sh bin/install.sh` first — "
                 "a session that can commit past the gate is worse than no session.")
    branch = f'session/{a.slug}'
    path = os.path.join(SESSIONS_DIR, a.slug)
    if branch in worktrees().values():
        sys.exit(f"REFUSING: {branch} is already checked out. `list` shows where.")
    if os.path.exists(path):
        sys.exit(f"REFUSING: {path} already exists — it is another session's copy or its leftovers.")
    dirty = git('status', '--porcelain')
    if dirty:
        sys.exit("REFUSING: the main working copy has uncommitted changes.\n"
                 f"{dirty}\n"
                 "A worktree branches from HEAD, so the new session would start WITHOUT them and its first\n"
                 "commit would silently revert nothing while missing everything. Found the hard way: the\n"
                 "first session this tool opened branched past an unstaged vocabulary change and wrote a\n"
                 "bean using a term its own copy of the law did not yet have. Commit or stash, then open.")
    host = resolve_edge(a.host, 'host', want_kind=('host', 'virtual-host'))      # before anything is created
    owner = resolve_edge(a.owner, 'owner')
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    git('worktree', 'add', '-b', branch, path)
    bean = os.path.join(path, 'beans', f'session-{a.slug}.md')
    if not os.path.exists(bean):
        with open(bean, 'w', encoding='utf-8') as f:
            f.write(_bean_template(a.slug, a.purpose, owner, host))
    print(f"opened  {branch}\n"
          f"  at    {path}\n"
          f"  bean  beans/session-{a.slug}.md (skeleton — fill `owns.opened_with` before working)\n"
          f"  gate  shared hook confirmed present\n\n"
          f"  cd {path}\n"
          f"  python3 bin/dmcheck.py")


def _bean_template(slug, purpose, owner, host):
    now = int(time.time() * 1000)
    return f"""---
bean: session-{slug}
kind: session
title: "{purpose or slug}"
status: active
summary: "OPENED AND NOT YET DESCRIBED. Replace this line with what the session is actually for — a summary that still says 'opened and not yet described' at close is the session admitting it never knew."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - {{ key: session_id, value: "session:{slug}", class: logical, establishing: true, observed: {time.strftime('%Y-%m-%d')} }}
provenance: {{ src: observed, by: "agent (fill in), opened by bin/dmsession.py", as_of: {time.strftime('%Y-%m-%d')} }}
owned_by: {{ legal: {{owner: {{bean: {owner}}}}}, technical: {{owner: {{bean: {owner}}}}} }}
responsibility: {{ legal: {{holder: {{bean: {owner}}}}}, technical: {{holder: {{bean: {owner}}}}} }}
workspace:
  host: {{ bean: {host} }}
  at: "root:daftar-sessions/{slug}"
  branch: "session/{slug}"
  opened_at: {now}
timing:
  start:
    system: unix-epoch
    at: "{now}"
    unit: millisecond
    by: "bin/dmsession.py open — stamped by the tool, not typed by a reader. A session's own start time is the one moment nobody should be estimating."
open:
  - "OPENED, NOT DESCRIBED. Fill `summary`, `owns.opened_with` and `owns.what_it_did` before closing."
---

Opened by `bin/dmsession.py`. Replace this body before the session closes: a session bean is how the
next one learns what happened, and a skeleton left in place teaches it nothing.
"""


def cmd_list(a):
    wt = worktrees()
    main = git('rev-parse', '--show-toplevel')
    print(f"{'BRANCH':<44} {'AHEAD':>5}  PATH")
    for path, branch in sorted(wt.items(), key=lambda kv: kv[1]):
        base = 'master' if branch != 'master' else '@{u}'
        try:
            ahead = git('rev-list', '--count', f'{base}..{branch}', check=False) or '?'
        except SystemExit:
            ahead = '?'
        tag = '  (main)' if os.path.abspath(path) == os.path.abspath(main) else ''
        print(f"{branch:<44} {ahead:>5}  {path}{tag}")
    if len(wt) == 1:
        print("\nonly the main working copy — no side sessions open")


def main_copy_is_mid_merge():
    """A merge left half-finished in the MAIN copy — by a previous failed close, or by a hand-merge.

    Checked because `close` merges INTO the main copy, which is shared by every session on the host:
    stacking a second merge onto an unresolved one is how one session's conflict becomes everybody's.
    """
    d = git('rev-parse', '--git-dir')
    if not os.path.isabs(d):
        d = os.path.join(ROOT, d)
    return os.path.exists(os.path.join(d, 'MERGE_HEAD'))


def cmd_close(a):
    branch = f'session/{a.slug}'
    wt = worktrees()
    path = next((p for p, b in wt.items() if b == branch), None)
    if path is None:
        sys.exit(f"no open worktree for {branch}. `list` shows what is open.")
    # THE GUARD `open` HAS AND `close` DID NOT. `open` refuses a dirty main copy because a worktree
    # branching from HEAD would start without its changes. `close` MERGES INTO that same copy and
    # checked only the worktree it was closing — so it could land on top of somebody's uncommitted work,
    # or on top of the half-merge a previous failed close left behind, and the main copy is shared.
    if main_copy_is_mid_merge():
        sys.exit(f"REFUSING: the main copy at {ROOT} is MID-MERGE — a previous close or a hand-merge\n"
                 f"stopped at a conflict and nothing finished it. Merging onto that would stack this\n"
                 f"session's work on an unresolved one. Finish or abandon it first:\n"
                 f"  cd {ROOT} && git status          # what is unresolved\n"
                 f"  cd {ROOT} && git merge --abort   # or resolve, git add, git commit\n"
                 f"Nothing here is lost: {branch} and its worktree are untouched.")
    dirty_main = git('status', '--porcelain')
    if dirty_main:
        sys.exit(f"REFUSING: the main copy at {ROOT} has uncommitted changes.\n"
                 f"{dirty_main}\n"
                 f"A merge lands in that tree, so somebody else's unsaved work would be mixed into this\n"
                 f"session's close and attributed to it. Commit or stash there, then close.")
    if os.path.abspath(os.getcwd()).startswith(os.path.abspath(path)):
        sys.exit(f"REFUSING: you are standing INSIDE {path}, which this command deletes.\n"
                 f"Even with ROOT resolved correctly, removing the caller's own working directory leaves\n"
                 f"a shell whose cwd no longer exists and every later command failing with 'Unable to\n"
                 f"read current working directory'. Run it from the main copy:\n"
                 f"  cd {ROOT} && python3 bin/dmsession.py close {a.slug}")
    r = subprocess.run(['python3', 'bin/dmcheck.py'], cwd=path, capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode:
        sys.exit("REFUSING to close: the session's own gate does not pass. Fix it in the worktree first.")
    if git('status', '--porcelain', cwd=path):
        sys.exit("REFUSING to close: the worktree has uncommitted changes. A session closes on a commit, "
                 "not on a working tree — otherwise what merges back is whatever happened to be saved.")
    m = subprocess.run(('git', 'merge', '--no-ff', branch, '-m', f'close session {a.slug}'),
                       cwd=ROOT, capture_output=True, text=True)
    if m.returncode:
        # NOT AUTO-ABORTED, deliberately. The merge state IS the information — both sides sit in the
        # index and `git status` names every unresolved file — and MERGE.md §10's principle is lossless
        # capture first, human choice after. Aborting would make that choice for them and hand back a
        # clean tree that says nothing about what disagreed. What was missing was never the abort; it
        # was being TOLD. So: say what happened, name the files, print both ways out, and stop.
        conflicted = subprocess.run(('git', 'diff', '--name-only', '--diff-filter=U'),
                                    cwd=ROOT, capture_output=True, text=True).stdout.strip()
        said = '\n'.join(s.strip() for s in (m.stdout, m.stderr) if s.strip())
        sys.exit(f"MERGE DID NOT COMPLETE — {branch} is NOT closed and NOTHING IS LOST.\n"
                 f"{said}\n\n"
                 + (f"unresolved:\n" + '\n'.join('  ' + f for f in conflicted.splitlines()) + "\n\n"
                    if conflicted else "")
                 + f"The main copy at {ROOT} is now mid-merge, and it is shared — every other session\n"
                 f"on this host is blocked until it is settled. Two ways out, from the MAIN copy:\n"
                 f"  cd {ROOT} && git merge --abort            # back to before, decide later\n"
                 f"  cd {ROOT} && <resolve> && git add -A && git commit    # finish it by hand\n"
                 f"Either way {branch} and its worktree at\n  {path}\nare untouched — re-run "
                 f"`close {a.slug}` once the main copy is clean.\n\n"
                 f"If the conflict is in log/journal.md or a bean, check first that this clone HAS the\n"
                 f"merge dispatch: `git check-attr merge -- log/journal.md beans/<any>.md` must say\n"
                 f"union and daftar. Both were missing from 2026-08-07 to 2026-08-08 and every\n"
                 f"additive close conflicted for that reason alone.")
    git('worktree', 'remove', path)
    git('branch', '-d', branch)
    print(f"closed {branch}: merged into master, worktree removed, branch deleted.\n"
          "The session BEAN survives — it is the record. Only its working copy is gone.")


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = p.add_subparsers(dest='cmd', required=True)
    o = sp.add_parser('open'); o.add_argument('slug'); o.add_argument('--purpose', default='')
    o.add_argument('--host', help='host bean this session runs on (default: git config daftar.host)')
    o.add_argument('--owner', help='bean that owns and answers for the session (default: git config daftar.owner)')
    o.set_defaults(fn=cmd_open)
    l = sp.add_parser('list'); l.set_defaults(fn=cmd_list)
    c = sp.add_parser('close'); c.add_argument('slug'); c.set_defaults(fn=cmd_close)
    args = p.parse_args()
    args.fn(args)
