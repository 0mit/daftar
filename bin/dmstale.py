#!/usr/bin/env python3
"""dmstale — report what has gone, or is going, out of date.

The VOCAB says an analysis_cache entry stands in for re-running its analysis ONLY while its
staleness_key still matches the live source at covers_paths. This is the tool that answers that
question, so the rule is checkable instead of merely written down.

  FRESH    the keyed objects are here and nothing since them touches the covered paths -> USE the summary
  STALE    commits after the key TOUCH the covered paths -> re-analyse, then bump as_of + staleness_key
  NOT-HERE this machine cannot answer: the tree is absent, no root resolves it, or this clone does not
           have the keyed objects YET (a clone that is behind is a fact about the reader, not staleness)
  UNKNOWN  the key is not machine-checkable at all (`manual:<why>`)

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
import glob, os, re, subprocess, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmcal
try:
    import yaml
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


def _here_names():
    """What this machine is called: its host bean's id and its hostname/fqdn anchors, lowercased."""
    try:
        import dmwhere
        beans = dmwhere.load()
        hid, hfm = dmwhere.this_host(beans)
        names = {str(hid).lower()} if hid else set()
        for a in ((hfm or {}).get('identity') or {}).get('anchors') or []:
            if a.get('key') in ('hostname', 'fqdn'):
                v = str(a.get('value', '')).lower()
                names |= {v, v.split('.')[0]}
        return names, hfm
    except Exception:
        return set(), None


def moved_since(repo_path, key, positions):
    """The commits after `key`, reachable from HEAD, that TOUCH the covered paths — or None when the key is
    not an ancestor of HEAD.

    THIS IS WHAT STALE MEANS (human-ratified 2026-09-20): the source moved under the analysis. Until now
    STALE was produced only by a MISSING object, so an analysis whose source had genuinely moved on was
    reported FRESH — the tool could not say the one thing its name promises.
    """
    try:
        anc = subprocess.run(['git', '-C', repo_path, 'merge-base', '--is-ancestor', key, 'HEAD'],
                             capture_output=True, timeout=10)
        if anc.returncode != 0:
            return None
        top = subprocess.run(['git', '-C', repo_path, 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, timeout=10).stdout.strip()
        rels = []
        for pos in positions:
            local = resolve_here(pos)
            if local and top and os.path.abspath(local).startswith(os.path.abspath(top)):
                rel = os.path.relpath(os.path.abspath(local), os.path.abspath(top))
                rels.append('.' if rel == '.' else rel)
        r = subprocess.run(['git', '-C', repo_path, 'log', '--oneline', '--no-decorate', f'{key}..HEAD', '--']
                           + (rels or ['.']), capture_output=True, text=True, timeout=20)
        return [l.strip() for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return None


def resolve_here(p):
    """A position -> a path on THIS machine, or None when this host does not hold it.

    Two forms carry a host (std-vocab@5.1, and the place migration of 11.0): `root:<name>/…`, resolved
    through this host's own `roots` map, and `<host>:<path>`, which resolves here only when the host it
    names IS this machine. Treating the second as a plain path was reporting a tree as absent while the
    reader stood in it.
    """
    if not isinstance(p, str):
        return p
    if p.startswith('root:'):
        try:
            import dmwhere
            _names, hfm = _here_names()
            path, _why = dmwhere.resolve(p, dmwhere.roots_of(hfm))
            return path
        except Exception:
            return None
    m = re.match(r'^([a-z0-9][a-z0-9.-]*):(/.*|[A-Za-z]:\\.*)$', p)
    if m:
        names, _hfm = _here_names()
        host = m.group(1).lower()
        return m.group(2) if (host in names or host.split('.')[0] in names) else None
    return p


DAYS_PER = {'day': 1, 'minute': 1 / 1440, 'second': 1 / 86400, 'millisecond': 1 / 86_400_000}


def notice_days(notice, default=90):
    """An extent on time -> how many days of notice, for comparing against a countdown in days.

    ONLY A LENGTH IS MEANINGFUL HERE. A notice bounded by `from`/`to` is a region of the calendar, not an
    amount of warning, so it is not converted and the default stands rather than a number being invented
    from it. The units it can convert are the ones `units` declares, which is why there is no month: a
    month is 28 to 31 days and `extent_form.not_a_calendar_bucket` says so at length.
    """
    m = (notice or {}).get('measure') if isinstance(notice, dict) else None
    if not isinstance(m, dict) or m.get('unit') not in DAYS_PER:
        return default
    try:
        return max(0, int(round(int(m['count']) * DAYS_PER[m['unit']])))
    except (TypeError, ValueError):
        return default


def expiry_terms():
    """{term: {attr, horizon_days, why}} for every term whose schema declares an expiry.

    The LAW is asked, including a garden's own `local_terms` — which is the whole point: a garden that
    invents a term with a date that runs out gets the same warning Tier-0's `registration` gets, without
    a release. dmcheck already loads and merges the vocabulary exactly as the gate sees it, so this asks
    it rather than re-reading std-vocab and drifting from what is actually in force.
    """
    try:
        import dmcheck as _law
    except Exception:
        return {}                      # no garden, no terms: report caches and say nothing about dates
    out = {}
    for name, term in (getattr(_law, 'TERMS', {}) or {}).items():
        decl = ((term or {}).get('schema') or {}).get('expiry')
        if isinstance(decl, dict) and decl.get('attr'):
            out[name] = decl
    return out


def refine(term, held, state):
    """A term's own extra sentence, where a general rule cannot carry the judgment.

    KEPT DELIBERATELY SMALL AND KEPT HERE. `registration` says more than "expires in N days": it says
    whether anything is known to PREVENT the loss, which is a second attribute's value read against the
    first. That is the single most useful line this tool prints — it joins a reader's ignorance to their
    exposure — and it is not expressible as `{attr, horizon_days, why}`. Rather than bend the schema
    language to fit one term on its first day, the general mechanism carries what generalises and the
    refinement stays beside the term it is about. If a second term wants one, that is the moment to ask
    what they have in common; one is not a pattern.
    """
    if term != 'registration':
        return ''
    auto = held.get('auto_renew', 'unknown')
    flag = '  auto-renew UNKNOWN: nothing on record prevents this' if (
        state != 'OK' and auto != 'enabled') else ''
    return f"  auto_renew={auto}  registrar={str(held.get('registrar'))[:40]}{flag}"


def verdict(entry):
    """(state, detail) for one cache entry."""
    key = str(entry.get('staleness_key') or '')
    paths = entry.get('covers_paths') or []
    # 11.0: a key is a POSITION in the git object graph, `<repo>@<sha>`. The repository is part of the key,
    # so a reader asks THAT repository instead of whatever tree it happens to stand in.
    m = re.match(r'^([a-z0-9][a-z0-9._-]*)@([0-9a-f]{7,40})$', key)
    if not m:
        return 'UNKNOWN', f"{key or 'no staleness_key'} — not machine-checkable"
    repo, want = m.group(1), m.group(2)
    if not paths:
        # The key names its repository, so an entry that lists no paths is still checkable wherever this
        # host declares a root of that name.
        paths = ['root:' + repo]
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
            # A CLONE THAT IS BEHIND IS NOT A STALE ANALYSIS (11.1 of this tool, human-ratified 2026-09-20).
            # Measured on two hosts the same minute: one said 45 fresh and 0 stale, the other 10 STALE —
            # every one of the ten a clone that simply lacked objects made on the first host and never
            # pushed to it. Calling that staleness re-created the one-verdict-per-host defect the key form
            # was changed to end.
            return 'NOT-HERE', (f"{local} does not have {want} yet — this CLONE is behind, which is a fact "
                                f"about it and not about the analysis; `git -C {local} fetch --all` answers it")
        moved = moved_since(local, want, [p for p in paths if resolve_here(p)])
        if moved is None:
            # The key is reachable but is not an ancestor of HEAD: this tree sits on another branch, so
            # "what changed since the key" has no answer here. The analysis read objects this repo holds.
            return 'FRESH', f"{want} (reachable; this tree is checked out at {live_git_head(local) or '?'})"
        if moved:
            return 'STALE', (f"{len(moved)} commit(s) after {want} touch the covered paths — "
                             f"{moved[0]}" + (" …" if len(moved) > 1 else ""))
    return 'FRESH', f"{want} (nothing since it touches the covered paths)"


# ---------------------------------------------------------------------------------------------------
# THE REPORT LIVES UNDER `if __name__ == '__main__'`, for the reason bin/dmcheck.py states for itself:
# importing this file must not run it or kill the process. It is not tidiness. `verdict()` above is the
# ONE implementation of FRESH / STALE / NOT-HERE / UNKNOWN, and until this guard existed no other tool
# could reach it — so bin/dmcursor.py grew a second, weaker copy that knew only the `git-head:<sha>`
# spelling std-vocab 11.0 replaced, and answered `UNKNOWN — unverifiable here` for every analysis in a
# migrated garden. One datum, two tools, two verdicts. A shared answer needs a shared implementation,
# and a script that exits on import cannot be one.
# ---------------------------------------------------------------------------------------------------


def report():
    QUIET = '--quiet' in sys.argv
    HORIZON_SET = '--days' in sys.argv
    HORIZON = int(sys.argv[sys.argv.index('--days') + 1]) if HORIZON_SET else 90
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

    # ---- what lapses if nobody acts -----------------------------------------------------------------
    # THE TERMS ARE ASKED OF THE VOCABULARY, NOT NAMED HERE. This block read `registration` and
    # `expires` out of its own source until 2026-09-20. That was never a decision: the term was born
    # garden-local and this tool was extended for it the same day, and when it was PROMOTED to Tier-0
    # nobody came back. The cost fell on the case the promotion was for — a garden that declares its own
    # term with its own expiry got nothing, however exactly the gate enforced the date. First-class to
    # the gate, invisible to the tool that would have made it useful.
    #
    # A term opts in with `schema.expiry: {attr, horizon_days, why}`. Nothing is inferred: nine of the
    # ten iso_date attrs in the standard are `observed` or `as_of` — when a fact was READ, not when it
    # runs out — so a tool that warned about every date would be wrong nine times in ten, and a warning
    # that is usually wrong is one people stop reading.
    exp_rows, expiring = [], 0
    for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))):
        head, _ = dmparse.read(f)
        if head is None:
            continue
        try:
            fm = dmparse.loads(head) or {}
        except Exception:
            continue
        for term, decl in expiry_terms().items():
            held = fm.get(term)
            attr = decl.get('attr')
            if not isinstance(held, dict) or not attr or not held.get(attr):
                continue
            try:
                # THROUGH THE DAY, in whatever calendar the date was stated in (16.0). A calendar that is not reckoned
                # by rule cannot be aged by arithmetic, and is skipped rather than guessed at.
                exp = datetime.date.fromordinal(dmcal.to_day(str(held[attr])))
            except (ValueError, dmcal.NotByRule):
                # The gate owns the form (attr_types: iso_date). A value it would refuse is not this
                # tool's to complain about twice, and guessing at it would be worse.
                continue
            days = (exp - datetime.date.today()).days
            # The horizon is the TERM's, and --days overrides every one of them: a domain and a rented
            # machine do not need the same notice, and the reader may want a different one from both.
            # It is an EXTENT on time (11.2) — the same construct a rental period is — rather than the
            # bare integer it was for one release, which was a fifth way of writing a duration in a
            # vocabulary that had just declared the first. The gate validates the region; this only
            # converts it, and only a unit it knows how to convert.
            horizon = HORIZON if HORIZON_SET else notice_days(decl.get('notice'))
            state = 'EXPIRED' if days < 0 else ('EXPIRING' if days <= horizon else 'OK')
            if state != 'OK':
                expiring += 1
            exp_rows.append((state, fm.get('bean'), days, exp, term, decl, held, horizon))

    if exp_rows:
        print()
        for state, bean, days, exp, term, decl, held, horizon in sorted(exp_rows, key=lambda r: r[2]):
            if QUIET and state == 'OK':
                continue
            why = f"  <-- {decl['why']}" if (state != 'OK' and decl.get('why')) else ''
            print(f"{state:8} {bean}.{term}  {decl['attr']} {exp} ({days} days)"
                  f"{refine(term, held, state)}{why}")
        print(f"\nexpiring: {sum(1 for r in exp_rows if r[0] == 'OK')} ok, "
              f"{sum(1 for r in exp_rows if r[0] == 'EXPIRING')} within their horizon, "
              f"{sum(1 for r in exp_rows if r[0] == 'EXPIRED')} EXPIRED"
              + (f"  [--days {HORIZON} overriding every term]" if HORIZON_SET else ''))

    print(f"\nanalysis_cache: {counts['FRESH']} fresh, {counts['STALE']} stale, "
          f"{counts['NOT-HERE']} not on this host, {counts['UNKNOWN']} unknown")
    if counts['NOT-HERE']:
        print("NOT-HERE is not staleness: those analyses may be perfectly current on the machine that "
              "holds their source. Give this host a `roots:` entry to resolve them here.")
    if counts['STALE']:
        print("STALE means the SOURCE MOVED under the analysis, not that a clone is behind.\n"
              "STALE entries must NOT be trusted — re-run the analysis, then bump as_of + staleness_key "
              "(VOCAB analysis_cache.staleness_rule).")
    sys.exit(1 if (counts['STALE'] or expiring) else 0)


if __name__ == '__main__':
    report()
