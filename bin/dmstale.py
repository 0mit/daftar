#!/usr/bin/env python3
"""dmstale — report what has gone, or is going, out of date.

The VOCAB says an analysis_cache entry stands in for re-running its analysis ONLY while its
staleness_key still matches the live source at covers_paths. This is the tool that answers that
question, so the rule is checkable instead of merely written down.

  FRESH    the key still matches the live source  -> USE the cached summary, do NOT re-analyse
  STALE    the source moved past the key          -> re-analyse, then refresh as_of + staleness_key
  NOT-HERE the source is not on THIS machine — a fact about the reader, never about the analysis
  UNKNOWN  the key is not machine-checkable at all (manual: / digest:)

A verdict is about the ANALYSIS, not about the reader's checkout. Freshness is decided by whether the
keyed objects are REACHABLE in the repository, not by which branch happens to be checked out beside
them — the two are different questions, and conflating them gave one analysis two verdicts on two hosts
the same minute (log/pending.md `staleness-key-is-host-relative`).

REGISTRATIONS: a recorded expiry date is only worth having if something reads it. An unrenewed domain
takes its DNS and its mail with it, so this reports days remaining and flags anything inside 90 days.
Deliberately NOT a gate rule: a check whose result changes with the calendar would make the gate
non-deterministic, and a gate that fails on a Tuesday for no committed reason is a gate people disable.

Exit: 0 = nothing stale or expiring, 1 = something needs action, 2 = setup problem.
Usage: python3 bin/dmstale.py [--quiet] [--days N]   (--quiet prints only what needs attention)
"""
import datetime
import glob, os, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUIET = '--quiet' in sys.argv
HORIZON = int(sys.argv[sys.argv.index('--days') + 1]) if '--days' in sys.argv else 90


def live_git_head(path):
    """Short sha of the tree at `path`, or None if it is absent / not a git repo."""
    if not os.path.isdir(path):
        return None
    try:
        r = subprocess.run(['git', '-C', path, 'rev-parse', '--short=7', 'HEAD'],
                           capture_output=True, text=True, timeout=10)
        return r.stdout.strip() or None
    except Exception:
        return None


def reachable(path, oid):
    """Is the keyed commit REACHABLE in the repository at `path`?

    THIS IS THE FIX for `staleness-key-is-host-relative`. The old test compared the key against whatever
    tree the reader had CHECKED OUT, which is a fact about the reader: on 2026-08-07 one laptop reported
    `41 fresh, 1 stale` and another reported the same four entries STALE the same minute, because one
    had `split-api-library` checked out and the other `v1-endpoint`. Neither was wrong about its own
    tree, and the analysis was current in both places.

    An analysis of source code depends on the OBJECTS it read, not on which branch happens to be checked
    out beside them. Reachability is a property of the repository, so every clone that has the object
    agrees — which is what makes the verdict portable instead of host-relative.
    """
    if not os.path.isdir(path):
        return None
    try:
        return subprocess.run(['git', '-C', path, 'cat-file', '-e', oid + '^{object}'],
                              capture_output=True, timeout=10).returncode == 0
    except Exception:
        return None


def resolve_here(p):
    """A covers_paths value -> a path on THIS machine, via the host's own roots map (std-vocab@5.1)."""
    if isinstance(p, str) and p.startswith('root:'):
        try:
            import dmwhere
            beans = dmwhere.load()
            _hid, hfm = dmwhere.this_host(beans)
            path, _why = dmwhere.resolve(p, dmwhere.roots_of(hfm))
            return path
        except Exception:
            return None
    return p


def verdict(entry):
    """(state, detail) for one cache entry."""
    key = str(entry.get('staleness_key') or '')
    paths = entry.get('covers_paths') or []
    if not key.startswith('git-head:'):
        return 'UNKNOWN', f"{key or 'no staleness_key'} — not machine-checkable"
    want = key.split(':', 1)[1]
    if not paths:
        return 'UNKNOWN', "git-head key but no covers_paths — nowhere to check"
    for p in paths:
        local = resolve_here(p)
        if local is None:
            return 'NOT-HERE', f"{p} — this host declares no resolution for it"
        got = reachable(local, want)
        if got is None:
            # NOT an assertion that the analysis aged. A tree this machine does not have is a fact about
            # THIS MACHINE, and calling it UNKNOWN alongside genuinely unreadable keys hid that.
            return 'NOT-HERE', f"{local} is not on this host"
        if not got:
            return 'STALE', f"{local} does not contain {want} — the analysis read objects this repo lacks"
        live = live_git_head(local)
        if live and want[:min(len(want), len(live))] != live[:min(len(want), len(live))]:
            # Reachable but not at HEAD: the analysis is VALID and the tree has simply moved on or sits
            # on another branch. Reporting that as staleness is what produced two verdicts for one fact.
            return 'FRESH', f"{want} (reachable; this tree is checked out at {live})"
    return 'FRESH', f"{want}"


counts = {'FRESH': 0, 'STALE': 0, 'UNKNOWN': 0, 'NOT-HERE': 0}
rows = []
for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))):
    head, _ = dmparse.read(f)
    if head is None:
        continue
    try:
        fm = dmparse.loads(head) or {}
    except Exception:
        continue
    ac = fm.get('analysis_cache')
    if not isinstance(ac, dict):
        continue
    for ctype, e in sorted(ac.items()):
        if not isinstance(e, dict):
            continue
        state, detail = verdict(e)
        counts[state] += 1
        rows.append((state, f"{fm.get('bean')}", ctype, detail))

for state, bean, ctype, detail in rows:
    if QUIET and state == 'FRESH':
        continue
    print(f"{state:8} {bean}.analysis_cache[{ctype}]  {detail}")

# ---- registrations: what lapses if nobody acts -------------------------------------------------
reg_rows, expiring = [], 0
for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))):
    head, _ = dmparse.read(f)
    if head is None:
        continue
    try:
        fm = dmparse.loads(head) or {}
    except Exception:
        continue
    reg = fm.get('registration')
    if not isinstance(reg, dict) or not reg.get('expires'):
        continue
    exp = datetime.date.fromisoformat(str(reg['expires']))
    days = (exp - datetime.date.today()).days
    state = 'EXPIRED' if days < 0 else ('EXPIRING' if days <= HORIZON else 'OK')
    if state != 'OK':
        expiring += 1
    reg_rows.append((state, fm.get('bean'), days, exp, reg))

if reg_rows:
    print()
    for state, bean, days, exp, reg in sorted(reg_rows, key=lambda r: r[2]):
        if QUIET and state == 'OK':
            continue
        auto = reg.get('auto_renew', 'unknown')
        flag = '  <-- auto-renew UNKNOWN: nothing is known to prevent this' if (
            state != 'OK' and auto != 'enabled') else ''
        print(f"{state:8} {bean}.registration  expires {exp} ({days} days)  "
              f"auto_renew={auto}  registrar={str(reg.get('registrar'))[:40]}{flag}")
    print(f"\nregistrations: {sum(1 for r in reg_rows if r[0] == 'OK')} ok, "
          f"{sum(1 for r in reg_rows if r[0] == 'EXPIRING')} expiring within {HORIZON} days, "
          f"{sum(1 for r in reg_rows if r[0] == 'EXPIRED')} EXPIRED")

print(f"\nanalysis_cache: {counts['FRESH']} fresh, {counts['STALE']} stale, "
      f"{counts['NOT-HERE']} not on this host, {counts['UNKNOWN']} unknown")
if counts['NOT-HERE']:
    print("NOT-HERE is not staleness: those analyses may be perfectly current on the machine that "
          "holds their source. Give this host a `roots:` entry to resolve them here.")
if counts['STALE']:
    print("STALE entries must NOT be trusted — re-run the analysis, then bump as_of + staleness_key "
          "(VOCAB analysis_cache.staleness_rule).")
sys.exit(1 if (counts['STALE'] or expiring) else 0)
