#!/usr/bin/env python3
"""dmwhere — resolve a bean's recorded LOCATIONS against the machine you are actually standing on.

WHY THIS EXISTS. Until std-vocab@5.1 a location in this ledger was a bare absolute path: 69 of them
across 14 beans, and not one named a host. That is a position in one anchor system written as though it
were the location itself, and it failed twice in one day — a commit reported to exist on NO branch and
NOT on disk (true of the machine searched, false of the estate), and one analysis reported FRESH on one laptop
and STALE on another the same minute.

WHAT IT DOES. A bean states where a thing is in a PORTABLE form (`root:addin/CloudApi`). A HOST
states what that root means on itself (`roots:` on the host's own bean). This resolves the first through
the second and reports, per position, one of:

  HERE        resolved on this machine, and the thing is actually there
  MISSING     resolved on this machine, and the thing is NOT there  (the bean is wrong, or the tree moved)
  ELSEWHERE   a position on another machine — correctly not resolvable from here
  NO-ROOT     this host declares no resolution for that root — it does not hold the thing
  UNKNOWN     the bean itself says nobody has established where it is

NO-ROOT AND UNKNOWN ARE ANSWERS, NOT FAILURES. That is the whole point: "not measured here" is a true
statement, where "stale" was a false one. A reader who is told a thing is not on this machine has learned
something; a reader shown a path that does not resolve has been misled with the same confident output.

THIS TOOL NEVER WRITES. It reports.

Usage:
  python3 bin/dmwhere.py                 # every located_at position in the garden, resolved for this host
  python3 bin/dmwhere.py <bean>          # just that bean
  python3 bin/dmwhere.py --root <name>   # what one logical root means here
"""
import glob, os, socket, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load():
    """Every managed document — beans AND mappings.

    Both, because both can carry `located_at` and `.gitattributes` already dispatches both to the same
    merge driver. This garden has paid for the beans-only glob once already: `dmmerge.load_garden`
    scanned `beans/*.md` alone, so the corpus merge never saw a mapping, and it was found by a check
    that asserted over the whole corpus rather than over what the tool under test happened to read.
    """
    out = {}
    for space, key in (('beans', 'bean'), ('mappings', 'mapping')):
        for f in sorted(glob.glob(os.path.join(ROOT, space, '*.md'))):
            fm, _ = dmparse.read(f)
            try:
                d = dmparse.loads(fm) if fm else None
            except yaml.YAMLError:
                continue
            if isinstance(d, dict) and d.get(key):
                out[d[key]] = d
    return out


def this_host(beans):
    """The bean whose hostname/fqdn anchor names the machine this is running on.

    Matched against the ANCHORS rather than against a bean id, because a bean id is a garden-local label
    and the anchor is the thing that claims to identify the machine. A host with no bean resolves to
    None, and every position then reports NO-ROOT — which is correct and is why it is not an error: the
    ledger genuinely does not know what a root means on a machine it has never been told about.
    """
    me = socket.gethostname().lower()
    for bid, d in beans.items():
        for a in ((d.get('identity') or {}).get('anchors') or []):
            if a.get('key') in ('hostname', 'fqdn'):
                v = str(a.get('value', '')).lower()
                if v == me or v.split('.')[0] == me.split('.')[0]:
                    return bid, d
    return None, None


def roots_of(host_fm):
    return (host_fm or {}).get('roots') or {}


def resolve(at, roots):
    """A `root:<name>[/<rel>]` position -> (literal path on this host, note) or (None, why not)."""
    if not isinstance(at, str) or not at.startswith('root:'):
        return None, 'not a root: position'
    rest = at[len('root:'):]
    name, _, rel = rest.partition('/')
    row = roots.get(name)
    if not row:
        return None, f"this host declares no root '{name}'"
    base = str(row.get('at', ''))
    _host, _, path = base.partition(':')
    if not path:
        return None, f"root '{name}' resolves to {base!r}, which names no path"
    return os.path.join(path, rel) if rel else path, None


def reachable_in_git(repo_path, oid):
    """Is this object REACHABLE here — not, is it checked out.

    The distinction is the entire staleness defect: `git-head:<sha>` compared a recorded key against
    whatever tree the reader happened to have checked out, so one analysis had as many verdicts as there
    were hosts. An object's presence is a fact about the repository and every clone that has it agrees.
    """
    import subprocess
    try:
        return subprocess.run(['git', '-C', repo_path, 'cat-file', '-e', oid + '^{object}'],
                              capture_output=True, timeout=15).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False


def classify(entry, roots):
    """One position -> a verdict about THIS machine.

    MISSING is reserved for the one case that means the LEDGER IS WRONG: the bean claims the thing is
    here and it is not. A position the bean already declares `elsewhere` and which is indeed not here is
    AGREEMENT, and reporting it as a defect would bury the real ones under every host's normal state.
    """
    openness, at = entry.get('openness'), entry.get('at')
    system = entry.get('system')
    if openness == 'unknown':
        return 'UNKNOWN', 'the bean states that nobody has established where this is'
    if openness == 'unreachable':
        return 'ELSEWHERE', f"{at} — declared unreachable; not checked from here"

    if system == 'git-object-graph' and isinstance(at, str) and '@' in at:
        repo, _, oid = at.partition('@')
        path, why = resolve('root:' + repo, roots)
        if path is None:
            return 'NO-ROOT', f"{at} — {why}"
        if reachable_in_git(path, oid):
            return 'HERE', f"{oid} reachable in {path}"
        return ('MISSING' if openness == 'here' else 'ELSEWHERE',
                f"{oid} NOT reachable in {path}")

    if isinstance(at, str) and not at.startswith('root:'):
        host, _, literal = at.partition(':')
        if host.lower().split('.')[0] != socket.gethostname().lower().split('.')[0]:
            return 'ELSEWHERE', f"{at} — a position on {host}"
        return ('HERE', literal) if os.path.exists(literal) else (
            'MISSING' if openness == 'here' else 'ELSEWHERE', literal)

    path, why = resolve(at, roots)
    if path is None:
        return 'NO-ROOT', f"{at} — {why}"
    if os.path.exists(path):
        return 'HERE', path
    return ('MISSING' if openness == 'here' else 'ELSEWHERE',
            f"{path} — not on this host, which is what the bean says")


def main():
    beans = load()
    hid, hfm = this_host(beans)
    roots = roots_of(hfm)
    me = socket.gethostname()

    if '--root' in sys.argv:
        name = sys.argv[sys.argv.index('--root') + 1]
        row = roots.get(name)
        print(f"{name} on {me}: {row.get('at') if row else 'NOT DECLARED — this host does not hold it'}")
        return 0

    only = next((a for a in sys.argv[1:] if not a.startswith('-')), None)
    print(f"host {me} -> bean {hid or 'NONE (this machine has no bean; every root is unresolvable)'}"
          f"  |  {len(roots)} root(s) declared here\n")

    counts, rows = {}, []
    for bid, d in sorted(beans.items()):
        if only and bid != only:
            continue
        for e in (d.get('located_at') or []):
            if not isinstance(e, dict):
                continue
            verdict, detail = classify(e, roots)
            counts[verdict] = counts.get(verdict, 0) + 1
            rows.append((verdict, bid, e.get('system'), detail))

    for v, bid, sysname, detail in rows:
        print(f"  {v:10s} {bid:14s} {str(sysname):19s} {detail}")

    if not rows:
        print("  (no bean carries located_at yet)")
    print("\n" + ", ".join(f"{n} {k.lower()}" for k, n in sorted(counts.items())))
    # MISSING is the only verdict that means the LEDGER is wrong. NO-ROOT and ELSEWHERE are facts about
    # this machine, and exiting non-zero on them would train a reader to ignore the tool on every host
    # that does not happen to hold everything.
    return 1 if counts.get('MISSING') else 0


if __name__ == '__main__':
    sys.exit(main())
