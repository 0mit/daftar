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

OBLIGATIONS (std-vocab 21.0): on a term whose value is a list or an open map — an agreement's clauses — the
date is each ENTRY's, and each is warned about by itself. An entry that repeats (`expiry.repeats`) is warned
about before its NEXT occurrence, walked through the day in the calendar it is counted in; one the law's
`expiry.unless` names — a debt already met — is silent. A repetition that cannot be walked by arithmetic (a
calendar that is not reckoned by rule, a place in the cell written in prose) is skipped with a NOTE, never guessed;
so is a date that is not a day of its calendar, and one beyond the days bin/dmcal.py reckons. Nothing one entry
holds ends the report: every other warning is still printed. A stride of days is reckoned, not walked; a walk through
cells counts so far and then goes on from the cell before today's; and what one run walks cell by cell is bounded,
past which a clause is a NOTE. A day is shown in the calendar it was written in, or the repetition counted in.

Every value a bean holds is printed through one escaper (`esc`): what a bean says reaches the terminal as text.

Exit: 0 = nothing stale or expiring, 1 = something needs action, 2 = setup problem.
Usage: python3 bin/dmstale.py [--quiet] [--days N]   (--quiet prints only what needs attention)
"""
import datetime
import glob, os, re, subprocess, sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse
import dmcal
import dmform
import dmunits
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


def _law(name):
    """A table of the law as the gate loaded it (`TERMS`, `SYSTEMS`, `UNITS`), or {} where there is no garden."""
    try:
        import dmcheck as _l
    except Exception:
        return {}
    return getattr(_l, name, {}) or {}


# ---------------------------------------------------------------------------------------------------
# WHEN A REPETITION FALLS DUE AGAIN (21.0). `expiry.repeats` names an attribute `in: recurrence`, and the
# position falls due again at each occurrence after the first. The occurrences are walked THROUGH THE DAY,
# in the calendar the recurrence is counted in, as bin/dmcal.py converts: "the 15th of each month" is a
# different day in a Persian month and a Gregorian one, and neither is privileged. What cannot be walked by
# arithmetic raises `Unreckoned` with the reason, and the reader is told rather than given a guess.
# bin/dmledger.py asks the same function for a clause's next occurrence, so the two can never disagree.
#
# A CELL IS READ FROM THE SYSTEM'S OWN FORM, NOT FROM A LIST OF CALENDARS. The law gives each system its levels
# (`anchor_systems[].levels`), finest last, and its one written form: `2026-09-20` is year, month, day; `2026-W38-7`
# year, week, day; `japanese:reiwa-8-09-20` era, year, month, day. So `each: month` is the level one above the day,
# its cell is every day whose form agrees up to the month, and the place in the cell is the form's last field. No
# calendar is named here and none is walked by a rule of its own: a week is walkable where the system has a week,
# Japanese months are the months its form writes, and a calendar dmcal learns tomorrow is walked the same way.
# ---------------------------------------------------------------------------------------------------
class Unreckoned(Exception):
    pass


_CAP = 100_000       # occurrences walked before giving up: a daily repetition for two and a half centuries
# WHAT ONE RUN MAY WALK, across every clause it reads. A cell of a calendar costs a few conversions through the day, and a
# clause may begin in its calendar's first year: a monthly clause from `hebrew:0001-07-01` is some 71,000 months to
# today — seconds of work, which a proposal from another garden could carry two hundred times, and every run of a reader
# would then walk all of them again. So a walk COUNTS only so far (_JUMP cells) and then jumps to the cell before today;
# a stride of days and `each: day` are not walked at all, but reckoned; and whatever a run still walks one cell at a
# time is bounded TWICE. Each repetition may walk _CLAUSE cells and no more, so no clause spends another's share: one
# that would walk further is a NOTE of its own ("not walked: this repetition alone …"). And a run walks _BUDGET cells in
# all, a backstop against many such clauses: past it, a clause is a NOTE ("not walked: this run's budget is spent").
# Either NOTE is a clause that was not read for its due day, so the run exits 1 — never a quiet report that looks clean
# because another garden's clauses spent what the garden's own needed. Counts, not seconds, so the same garden gives
# the same report on any machine.
_JUMP = 1_000
_CLAUSE = 30_000            # a monthly repetition counted from the first year of the Gregorian calendar: some 24,300
_BUDGET = 150_000
_RUN = {'spent': 0, 'unread': False}


class BudgetSpent(Unreckoned):
    """A repetition not walked because a bound on walking was reached — a clause not read for its due day."""


def new_run():
    """A reader's run begins: the cells it may still walk one at a time are the whole _BUDGET again."""
    _RUN['spent'], _RUN['unread'] = 0, False


def _spender():
    """The spend of ONE repetition's walk: its own allowance, and the run's."""
    here = [0]

    def spend(n=1):
        here[0] += n
        _RUN['spent'] += n
        if here[0] > _CLAUSE:
            _RUN['unread'] = True
            raise BudgetSpent(f"not walked: this repetition alone would walk more than {_CLAUSE} cells of its calendar "
                              f"one at a time — it is counted from a far past (a clause that says `times:` is counted "
                              f"from its first occurrence); read its due day by hand, or write its first due day nearer")
        if _RUN['spent'] > _BUDGET:
            _RUN['unread'] = True
            raise BudgetSpent(f"not walked: this run's budget is spent — it has walked {_BUDGET} cells of a calendar one "
                              f"at a time already, across the clauses before this one; a clause counted from a far past "
                              f"costs one cell per step since (a clause that says `times:` is counted from its first "
                              f"occurrence)")
    return spend
# CELLS IN A ROW WITH NO OCCURRENCE before the walk gives up and says the place does not occur. The rarest place a real
# calendar has is the 29th of February, missing at most seven years running (1897 to 1903); a place missing a hundred
# cells running is one the calendar does not have — `at: "31"` in a calendar of thirty-day months, `02-30` anywhere.
# Without this bound such a clause, which the gate cannot refuse (`at` is prose to it), walked forever.
_MISS_CAP = 100
_FIELD = re.compile(r'^(.*[^-.:])[-.]([^-.:]+)$')


def _split(form, k):
    """(label, [the last k fields]) of a position in its system's form — `2026-09-20`, 1 -> ('2026-09', ['20']) — or None
    when the form has fewer fields than that."""
    fields = []
    for _ in range(k):
        m = _FIELD.match(form)
        if not m:
            return None
        form, f = m.group(1), m.group(2)
        fields.insert(0, f)
    return form, fields


class _Cells:
    """The cells of one level of one system, walked through the day: where the cell holding a day begins and ends,
    and which day of it is at a place. Every answer is read from the system's own written form, via bin/dmcal.py."""

    def __init__(self, row):
        self.row, self.cal, self._memo = row, row.get('calendar'), {}

    def form(self, n):
        if n not in self._memo:
            self._memo[n] = dmcal.from_day(n, self.cal)
        return self._memo[n]

    def cut(self, n, k):
        got = _split(self.form(n), k)
        if got is None:
            raise Unreckoned(f"`{self.form(n)}` has fewer than {k + 1} fields: the level is not written in its form")
        return got

    def label(self, n, k):
        return self.cut(n, k)[0]

    def place(self, n, k):
        fields = self.cut(n, k)[1]
        if not all(f.isdigit() and f.isascii() for f in fields):
            raise Unreckoned(f"`{self.form(n)}` writes its place in the cell as `{'-'.join(fields)}`, and this tool counts "
                             f"only a place written in numbers")
        return tuple(int(f) for f in fields)

    def _edge(self, n, k, step):
        """The day beside the cell holding `n` — the first after it (step +1) or the last before it (step -1). Found by
        doubling out and halving back, because a cell is a run of days that never comes back once left."""
        own, near, far, d = self.label(n, k), n, n + step, 1
        while self.label(far, k) == own:
            near, d = far, d * 2
            far = n + step * d
        while abs(far - near) > 1:
            mid = (near + far) // 2
            if self.label(mid, k) == own:
                near = mid
            else:
                far = mid
        return far

    def start(self, n, k):
        return self._edge(n, k, -1) + 1

    def end(self, n, k):
        """The first day of the NEXT cell."""
        return self._edge(n, k, +1)

    def find(self, s, e, k, at):
        """The day in the cell [s, e) whose last k fields read `at`, or None when the cell has no such place."""
        if k == 1:
            n = s + at[0] - self.place(s, 1)[0]           # places run on by one a day (a cell may begin past 1)
            return n if s <= n < e and self.place(n, 1) == at else None
        c = s
        while c < e:
            ce = min(self.end(c, k - 1), e)
            if self.place(c, k)[0] == at[0]:
                return self.find(c, ce, k - 1, at[1:])
            c = ce
        return None


def _at(rec, k, default):
    """Where in each cell: `at` as k whole numbers joined by `-` (`15` in a month, `12-01` in a year); the first
    occurrence's own place when silent."""
    at = rec.get('at')
    if at is None:
        return default
    parts = str(at).split('-')
    if isinstance(at, bool) or len(parts) != k or not all(p.isdigit() and p.isascii() for p in parts):
        want = '`15`' if k == 1 else '`' + '-'.join(['MM', 'DD', 'NN'][:k]) + '`' if k <= 3 else f"{k} numbers"
        raise Unreckoned(f"`at: {at}` is prose to this tool — in a cell {k} level{'s' if k != 1 else ''} above the day it "
                         f"walks a place written {want}")
    return tuple(int(p) for p in parts)


def _place_words(at):
    return '-'.join('%02d' % x for x in at) if len(at) > 1 else str(at[0])


def _after_first(first, rec, systems, units, skipped=None, near=None, times=None):
    """Every occurrence AFTER `first`, in order, unbounded, as (index, day) — the first occurrence is index 1: the
    stride the recurrence names, and nothing else. A cell that has no occurrence — a month without the day named — is
    appended to `skipped` as (start, end, label, place), so the reader can be told it was skipped rather than left to
    wonder.

    `near` is the day the reader wants the occurrences around (today, or the day the repetition ends): a stride and
    `each: day` begin at the occurrence on or before it, reckoned, their index exact — but never past the `times`-th,
    which is the last there is, so a repetition that ended long ago is found ended rather than falling due today; a
    walk through cells counts from `first` for _JUMP cells and then — unless `times` is stated, where the index is what
    ends the repetition — jumps to the cell before the one holding `near`, and its occurrences from there on are
    yielded with the index None: not counted, never guessed."""
    _spend = _spender()          # this repetition's own allowance, and the run's
    every, each = rec.get('every'), rec.get('each')
    if isinstance(every, dict):
        unit = units.get(str(every.get('unit'))) if every.get('unit') is not None else None
        day = units.get('day')
        if every.get('unit') is None:
            raise Unreckoned("`every: {count}` strides by neighbours, and which position is a day's neighbour is the "
                             "system's to say — stride by a measure (`every: {count, unit: day}`) or by a cell (`each:`)")
        count = dmunits.exact(every.get('count'))       # a count longer than a count may be raises, and is said below
        if not unit or not day or not isinstance(unit.get('factor'), (list, tuple)) or count is None or count <= 0:
            raise Unreckoned(f"`every: {brief(every, 120)}` is not a stride this tool can measure in days")
        stride = Fraction(count * Fraction(*unit['factor']), Fraction(*day['factor']))      # exact: a quotient of fractions
        if stride < 1:
            raise Unreckoned(f"a stride of {every['count']} {every['unit']} is finer than the day this tool reads")
        if stride.denominator != 1:
            raise Unreckoned(f"a stride of {every['count']} {every['unit']} is not a whole number of days, and this tool "
                             f"reads days")
        step = int(stride)
        k = max(1, (near - first) // step) if near is not None and near > first else 1     # reckoned, not walked
        if times is not None:
            k = max(1, min(k, times - 1))           # occurrence k + 1: never past the times-th, the last there is
        while True:
            _spend()
            yield k + 1, first + k * step
            k += 1
    row = (systems or {}).get(rec.get('in')) or {}
    cal = row.get('calendar')
    if each is None or not cal:
        raise Unreckoned(f"`each: {each}` needs the system it is counted in (`in:`), and '{rec.get('in')}' names no calendar")
    if row.get('reckoning') not in (None, 'arithmetic'):
        raise Unreckoned(f"{row.get('system')} is reckoned {row.get('reckoning')}, not by rule — look the next "
                         f"occurrence up in what was published or observed")
    # THE LEVELS ARE THE LAW'S: which the system has, in order, and which of them is the day (the level whose unit is
    # the day — `day` in most calendars, `kin` in the Mayan count).
    levels = [l.get('level') for l in row.get('levels') or [] if isinstance(l, dict)]
    days = [l.get('level') for l in row.get('levels') or [] if isinstance(l, dict) and l.get('unit') == 'day']
    if each not in levels:
        raise Unreckoned(f"{row.get('system')} has no level `{each}` — its levels are {', '.join(map(str, levels))}")
    if not days:
        raise Unreckoned(f"{row.get('system')} declares no level whose unit is the day, and this tool walks days")
    k = levels.index(days[0]) - levels.index(each)
    if k < 0:
        raise Unreckoned(f"`each: {each}` is finer than the day this tool reads")
    if k == 0:
        n = max(first, near - 1) if near is not None else first                              # reckoned, not walked
        if times is not None:
            n = max(first, min(n, first + times - 2))   # the next yielded, n + 1, is never past the times-th
        while True:
            n += 1
            _spend()
            yield n - first + 1, n
    cells = _Cells(row)
    try:
        at = _at(rec, k, None) or cells.place(first, k)
    except ValueError as e:
        raise Unreckoned(str(e))
    s, misses, longest, i, walked = cells.start(first, k), 0, 0, 1, 0
    while True:
        _spend()
        walked += 1
        if walked == _JUMP and near is not None and times is None and s < near:
            # FAR ENOUGH COUNTED: to the cell before the one holding `near`, so the occurrence before it is still seen
            # (and every cell skipped after that one), and the index is no longer counted.
            s2 = cells.start(cells.start(near, k) - 1, k)
            if s2 > s:
                s, i = s2, None
        e = cells.end(s, k)
        n = cells.find(s, e, k, at)
        if n is None:
            # A CELL WITHOUT THE PLACE HAS NO OCCURRENCE (RFC 5545 §3.3.10: an invalid date is ignored, not moved):
            # "the 31st of each month" skips a month of 30 rather than inventing a day the parties never named. The
            # skip is recorded, because a reader who is not told of it cannot tell a rule from a gap.
            misses += 1
            if k == 1:
                longest = max(longest, cells.place(e - 1, 1)[0])
            if skipped is not None:
                skipped.append((s, e, cells.label(s, k), _place_words(at)))
            if misses >= _MISS_CAP:
                raise Unreckoned(f"no {each} of {row.get('system')} in {misses} running has a place {_place_words(at)}"
                                 + (f" (the longest runs to {longest})" if k == 1 else '')
                                 + " — the clause names a place its calendar does not have")
        else:
            misses = 0
            if n > first:
                i = i + 1 if i is not None else None
                yield i, n
        s = e


def occurrences(first, rec, systems=None, units=None, skipped=None):
    """The day numbers on which a position first due on day `first` falls due: `first` itself, then each occurrence
    the recurrence `rec` names after it — ending at `times` (the first included) or at `to`, whichever comes first
    (`recurrence_form`). Unbounded when neither is stated. Raises Unreckoned when it cannot be walked by arithmetic."""
    for _i, n in _occurrences(first, rec, systems, units, skipped):
        yield n


def _occurrences(first, rec, systems=None, units=None, skipped=None, near=None):
    """occurrences(), as (index, day): the index None where the walk jumped toward `near` rather than count (see
    _after_first)."""
    systems = systems if systems is not None else _law('SYSTEMS')
    units = units if units is not None else _law('UNITS')
    _writable(first)
    times = rec.get('times')
    times = times if isinstance(times, int) and not isinstance(times, bool) and times >= 1 else None
    end = None
    if rec.get('to') is not None:
        try:
            end = day_of(rec['to'])
        except (ValueError, dmcal.NotByRule) as e:
            raise Unreckoned(f"`to: {brief(rec['to'])}` — {e}")
    if end is not None and first > end:
        return
    yield 1, first
    if times == 1:
        return
    # WHERE THE READER LOOKS: today — or, for a repetition that ends before today, its end, so its last is found.
    near = near if end is None or near is None else min(near, end)
    try:
        for i, n in _after_first(first, rec, systems, units, skipped, near=near, times=times):
            if end is not None and n > end:
                return
            yield i, _writable(n)
            if times is not None and i is not None and i >= times:
                return
    except (ValueError, OverflowError, KeyError, dmcal.NotByRule) as e:
        raise Unreckoned(str(e))


def _writable(n):
    """`n`, when it is a day bin/dmcal.py reckons — so every reader can write it; else Unreckoned. A stride of three
    million days lands past the year 9999, and a day nobody can write was a traceback in every reader, which cost the
    garden every other warning too."""
    try:
        return dmcal.within(n, f"an occurrence on day {n}")
    except ValueError as e:
        raise Unreckoned(f"{e}, so no reader could write it") from None


def next_due(first, rec, today, systems=None, units=None, skipped=None):
    """The occurrence a reader must be warned about: the first on or after `today` — or, when the repetition ended
    before today, its last. Returns (day, index, times, ended); `index` counts from 1, the first included. Where a list
    is given as `skipped`, the cells the walk skipped between the occurrence before that one and it are put in it."""
    last, seen = None, []
    for i, n in _occurrences(first, rec, systems, units, seen, near=today):
        if n >= today:
            if skipped is not None:
                skipped.extend(c for c in seen if c[1] > (last[0] if last else first) and c[0] < n)
            return n, i, rec.get('times'), False
        last = (n, i)
        if i is not None and i >= _CAP:
            raise Unreckoned(f"more than {_CAP} occurrences fall before today")
        seen.clear()                              # a cell skipped before an occurrence already past is not news
    if last is None:
        raise Unreckoned("the repetition ends before its first occurrence")
    return last[0], last[1], rec.get('times'), True


def nth(i, times=None):
    """Which occurrence, in words: `occurrence 3 of 12` — or, where the walk jumped rather than count, that it did."""
    if i is None:
        return f"occurrence not counted (more than {_JUMP} cells after the first: the walk went on from the one before today's)"
    return f"occurrence {i}" + (f" of {times}" if times is not None else '')


def skip_words(cell):
    """A skipped cell in words, for a NOTE."""
    _s, _e, label, place = cell
    return (f"no occurrence in {label} — it has no {place}, and a cell without the place is skipped (RFC 5545), "
            f"never moved to a day nobody named; if the parties meant another day, the clause says which")


def describe(rec):
    """A recurrence in words, as it is written: `each month in gregorian-civil at 15, 6 times`."""
    if not isinstance(rec, dict):
        return brief(rec, 120)
    ev = rec.get('every')
    head = (f"each {brief(rec['each'])}" if rec.get('each') is not None else
            f"every {brief(ev.get('count'))}{' ' + brief(ev['unit']) if ev.get('unit') is not None else ' neighbours'}"
            if isinstance(ev, dict) else brief(rec, 120))
    return (head + (f" in {brief(rec['in'])}" if rec.get('in') else '')
            + (f" at {brief(rec['at'])}" if rec.get('at') is not None else '')
            + (f", from {brief(rec['from'])}" if rec.get('from') is not None else '')
            + (f", to {brief(rec['to'])}" if rec.get('to') is not None else '')
            + (f", {brief(rec['times'])} times" if rec.get('times') is not None else ''))


def silenced(entry, decl):
    """True when `expiry.unless` names this entry's state: a debt already met no longer lapses."""
    for attr, values in ((decl or {}).get('unless') or {}).items():
        if entry.get(attr) is not None and str(entry.get(attr)) in [str(v) for v in (values or [])]:
            return True
    return False


def conflicted(v):
    """The sides of a disagreement bin/dmmerge.py captured and nobody has resolved (`{conflict: [a, b]}`), or None."""
    return v['conflict'] if isinstance(v, dict) and isinstance(v.get('conflict'), list) else None


def due_entries(fm, term, decl, today=None, notes=None):
    """[(label, held, day, shown, detail)] — what falls due in one term of one bean, read as the law declares it.

    A term whose value IS the thing (a registration) has one date; a term whose value is a list or an open map has
    one per ENTRY, labelled `[<key>]`. `day` is None when the entry cannot be walked, and `detail` then says why.
    Where a list is given as `notes`, a sentence the reader should have beside a row is put in it as (label, text):
    a month the repetition skipped, a disagreement a merge left for a person."""
    today = today if today is not None else datetime.date.today().toordinal()
    attr, rep = decl.get('attr'), decl.get('repeats')
    sch = ((_law('TERMS').get(term) or {}).get('schema') or {})
    held = fm.get(term)
    if dmform.scope_of(sch) == 'entry' and conflicted(held):
        # THE WHOLE TERM IN DISPUTE: nothing in it is one garden's word more than the other's, so no entry is read —
        # and the reader is told, because silence here would read as "nothing falls due".
        return [('', held, None, None, f"the whole of `{term}` holds a merge conflict ({len(conflicted(held))} sides) — "
                                       f"no entry is read until a person chooses")]
    if dmform.scope_of(sch) == 'entry' and isinstance(held, (dict, list)):
        items = (list(held.items()) if isinstance(held, dict) else list(enumerate(held)))
        entries = [(f"[{k}]", e) for k, e in items if isinstance(e, dict)]
    else:
        entries = [('', held)] if isinstance(held, dict) else []
    out = []
    for label, e in entries:
        sides = conflicted(e)
        if sides is not None:
            out += _due_in_dispute(label, e, [x for x in sides if isinstance(x, dict)], attr, rep, decl, today)
            continue
        if not e.get(attr) or silenced(e, decl):
            continue
        try:
            # THROUGH THE DAY, in whatever calendar the date was stated in (16.0). A calendar that is not reckoned
            # by rule cannot be aged by arithmetic, and is skipped rather than guessed at.
            first = day_of(e[attr])
        except dmcal.NotByRule:
            continue                          # looked up, never computed: left alone rather than guessed at (16.0)
        except ValueError as why:
            # A DAY THAT CANNOT BE READ IS SAID, NEVER DROPPED: `2026-02-30` read as nothing at all was a clause that
            # silently stopped falling due, while bin/dmledger.py named it. The gate refuses such a day; the working
            # tree, where this reads, may still hold one.
            out.append((label, e, None, None, f"{attr} {brief(e[attr])} is not a day this can read: {why}"))
            continue
        rec = e.get(rep) if rep else None
        beside = []
        if not isinstance(rec, dict):
            out.append((label, e, first, show_day(first, notes=beside, written=e[attr]), ''))
        else:
            skipped = []
            try:
                day, i, times, ended = next_due(first, rec, today, skipped=skipped)
            except Unreckoned as why:
                out.append((label, e, None, None, f"{attr} {brief(e[attr])}, then {describe(rec)}: {why}"))
            else:
                out.append((label, e, day, show_day(day, rec, notes=beside, written=e[attr]),
                            f"  — {'the last' if ended else 'next'}: {nth(i, times)}, {describe(rec)}"))
                if not ended:
                    beside += [skip_words(c) for c in skipped]
            fw = from_words(first, rec, attr, e[attr])
            beside += [fw] if fw else []
        if notes is not None:
            notes += [(label, t) for t in beside]
    return out


# A CHARACTER THAT CONTROLS A TERMINAL OR ENDS A LINE — every Unicode `Cc` (C0, DEL, C1: the 8-bit CSI and NEL among
# them) and the Unicode line and paragraph separators. What a bean says is DATA, and printed raw such a character is an
# instruction to the reader's terminal: `\e[2A\e[2K` climbs back over the line above and writes a debt the other way
# round, `\e[8m` conceals every line after it, `\r` writes over the start of its own line. The gate refuses them in a
# bean; a working tree, or a garden older than that refusal, may still hold them — so every value a reader here shows
# passes through ONE escaper, the one bin/dmpropose.py prints a proposal with: each such character as its escape.
_CTRL = re.compile('[\x00-\x1f\x7f-\x9f\u2028\u2029]')


def esc(s):
    """A string as it may be printed: every character `_CTRL` names as `\\xNN` or `\\uNNNN`, the rest as it is."""
    return _CTRL.sub(lambda m: (f"\\x{ord(m.group(0)):02x}" if ord(m.group(0)) < 0x100 else
                                f"\\u{ord(m.group(0)):04x}"), str(s))


def say(line):
    """ONE line of a report as it is printed: every control character escaped, a line feed among them — the guard
    behind the escaping of each value where the line is built, so no value this tool forgot can reach the terminal. A
    line feed kept here was a line of the bean's own making: a key or a name holding one printed a second line, which
    could say anything — a debt the other way round. So a report of several lines prints each with a call of its own."""
    return esc(line)


def written(v):
    """A value as a bean writes it: a list, a mapping, `null`, `true` in YAML's flow form — `[sam]`, `{count: 5}` — and
    anything else as itself. Python's own spelling (`['sam']`, `None`, `True`) is a language the reader did not write in.
    Every character that controls a terminal is shown as its escape (`esc`). Raises ValueError for an int too long for
    Python to write out."""
    if v is None or isinstance(v, (bool, list, tuple, dict)):
        try:
            t = yaml.safe_dump(list(v) if isinstance(v, tuple) else v, default_flow_style=True, allow_unicode=True,
                               sort_keys=False, width=10 ** 9)
        except yaml.YAMLError:                # a value no bean could hold: said as Python has it rather than not at all
            return esc(str(v))
        return esc((t[:-4] if t.endswith('\n...\n') else t).strip())     # a bare scalar ends its own document
    return esc(str(v))


def brief(v, width=60, quote=False):
    """A value as a reader is shown it (`written`): whole when it is short, else its start and its length — in backticks
    when `quote` is set. A value of five thousand characters is one the reader is told of, not handed."""
    try:
        t = written(v)
    except ValueError:                        # an int too long for Python to write out
        return (f"a {'number' if isinstance(v, int) else 'value holding a number'} of more than "
                f"{sys.get_int_max_str_digits()} digits")
    q = '`' if quote else ''
    return f"{q}{t}{q}" if len(t) <= width else f"{q}{t[:width]}…{q} ({len(t)} characters)"


def day_of(v):
    """The day number of a position a bean wrote — text, or a date YAML read — or ValueError saying it is none. A list,
    a map, a boolean or nothing is no date, and is said to be one in the reader's words, never handed to dmcal as
    Python spells it (`['a', 'b']`, `True`)."""
    if isinstance(v, (str, datetime.date)) and not isinstance(v, bool):
        return dmcal.to_day(str(v))
    raise ValueError(f"{brief(v, quote=True)} is not a date")


def from_words(first, rec, attr, v):
    """A sentence for the reader when a repetition's own `from` names another day than the one it repeats from — or None.
    The walk starts at the entry's `attr` (its first due date): that is the day the entry names, and a `from` that says
    another is told, never silently preferred and never silently dropped."""
    f = rec.get('from') if isinstance(rec, dict) else None
    if f is None:
        return None
    try:
        if day_of(f) == first:
            return None                       # the same day, however it is written
        unread = ''
    except (ValueError, dmcal.NotByRule) as e:
        unread = f", which is not a day this can read ({e})"
    return (f"its repetition says `from: {brief(f)}`{unread}, and its `{attr}` is {brief(v)} — it is walked from its "
            f"`{attr}`, the day the entry names; if it begins on another day, `{attr}` is that day and `from` agrees")


def _due_in_dispute(label, e, sides, attr, rep, decl, today):
    """A disagreement over one entry: each side that still lapses is walked, and the EARLIEST is what the reader is
    warned of, until a person chooses. Warning of the earlier date is the error that costs a look; warning of the later,
    or of neither, is the error that costs the debt. Every side met, waived or broken is silence, as one would be.

    A SIDE THAT CANNOT BE WALKED IS SAID, NEVER DROPPED: "the earliest is shown" over the sides that could be read, with
    a side on `2026-02-30` or a stride past the year 9999 left out without a word, was a row that said OK while a side
    it did not name had already fallen due. Each such side is a row of its own with no day, which the report prints as
    a NOTE — under --quiet too — and the row that is shown says it is the earliest of the others."""
    walked, unwalked = [], []
    for x in sides:
        if silenced(x, decl) or not x.get(attr):
            continue
        try:
            first = day_of(x[attr])
        except dmcal.NotByRule:
            unwalked.append(f"{attr} {brief(x[attr])} cannot be aged by rule — it is looked up, never computed")
            continue
        except ValueError as why:
            unwalked.append(f"{attr} {brief(x[attr])} is not a day this can read: {why}")
            continue
        rec = x.get(rep) if rep else None
        beside = []
        if not isinstance(rec, dict):
            walked.append((first, show_day(first, notes=beside, written=x[attr]), '; '.join([''] + beside)))
            continue
        try:
            day, i, times, ended = next_due(first, rec, today)
        except Unreckoned as why:
            unwalked.append(f"{attr} {brief(x[attr])}, then {describe(rec)}: {why}")
            continue
        fw = from_words(first, rec, attr, x[attr])
        shown = show_day(day, rec, notes=beside, written=x[attr])
        walked.append((day, shown, f", {'the last' if ended else 'next'}: {nth(i)}, {describe(rec)}"
                                   + '; '.join([''] + beside + ([fw] if fw else []))))
    live = [x for x in sides if not silenced(x, decl)]
    words = f"a merge conflict: {len(sides)} sides disagree, {len(live)} of them not met, waived or broken"
    if walked:
        day, shown, how = min(walked)
        others = (f"; {len(unwalked)} side{'s' if len(unwalked) != 1 else ''} cannot be walked here (NOTE), and the "
                  f"earliest of the others is shown" if unwalked else "; the earliest is shown")
        return ([(label, e, day, shown, f"  — {words}{others}{how}, until a person chooses")]
                + [(label, e, None, None, f"a side of this merge conflict cannot be walked here, and the date shown for "
                                          f"it is the earliest of the others: {u}") for u in unwalked])
    if live:
        return [(label, e, None, None, f"{words}, and no due date among them can be walked here"
                                       + (f" ({'; '.join(unwalked)})" if unwalked else '') + " — a person chooses")]
    return []


def system_of(value, systems=None):
    """The positioning system a written position is in — the row of the law's `anchor_systems` whose `pattern` it
    matches and that names a calendar — or {}. Found as the gate finds it, by the law's pattern: no calendar is named
    here, so a garden that writes its days in the Persian calendar is shown them in it."""
    text = str(value) if isinstance(value, (str, datetime.date)) and not isinstance(value, bool) else None
    for row in (systems if systems is not None else _law('SYSTEMS')).values():
        pat = row.get('pattern') if isinstance(row, dict) else None
        if text is not None and row.get('calendar') and isinstance(pat, str) and pat != 'none':
            try:
                if re.search(pat, text):
                    return row
            except re.error:
                continue
    return {}


def show_day(n, rec=None, systems=None, notes=None, written=None):
    """Day `n` in the calendar the recurrence is counted in, where it names one; else in the calendar the position was
    WRITTEN in (`written`, the value as the bean has it); in the Gregorian calendar only where neither says — and where
    none can write it, as its day number, with the reason put in `notes`, where a list is given, so the reader is told
    why a day is shown as a number. Never raises: a day nobody can write is still a day to be warned of."""
    systems = systems if systems is not None else _law('SYSTEMS')
    row = systems.get((rec or {}).get('in')) or {}
    if not row.get('calendar') and written is not None:
        row = system_of(written, systems)
    why = None
    for cal in ([row['calendar']] if row.get('calendar') else []) + ['gregory']:
        try:
            return dmcal.from_day(n, cal)
        except (ValueError, OverflowError, dmcal.NotByRule) as e:
            why = e
    if notes is not None:
        notes.append(f"day {n} cannot be written as a date here ({why}) — it is shown as its day number")
    return f"day {n}"


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
    return f"  auto_renew={brief(auto)}  registrar={esc(str(held.get('registrar'))[:40])}{flag}"


def verdict(entry):
    """(state, detail) for one cache entry — the detail as it may be printed (`esc`): it quotes the entry's own key and
    paths, which are what a bean says."""
    state, detail = _verdict(entry)
    return state, esc(detail)


def _verdict(entry):
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


def _out(line=''):
    """print(), through the guard: what a bean says reaches the terminal as text, never as an instruction to it."""
    print(say(line))


def report():
    new_run()
    # A PIPE ON WINDOWS IS WRITTEN IN THE ANSI CODE PAGE, and a date in another calendar's script, or a title in
    # Persian, is not in it: a glyph the stream cannot carry is replaced rather than let the report die mid-way.
    try:
        sys.stdout.reconfigure(errors='replace')
    except (AttributeError, ValueError):
        pass
    QUIET = '--quiet' in sys.argv
    HORIZON_SET = '--days' in sys.argv
    _d = sys.argv[sys.argv.index('--days') + 1] if HORIZON_SET and sys.argv.index('--days') + 1 < len(sys.argv) else '90'
    if not (_d.isascii() and _d.isdigit()):
        _out("dmstale: --days takes a whole number of days, e.g. --days 30"); sys.exit(2)
    HORIZON = int(_d)
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
        if not isinstance(fm, dict):
            continue                                # front matter that is not a mapping is the gate's to refuse
        ac = fm.get('analysis_cache')
        if not isinstance(ac, dict):
            continue
        for ctype, e in sorted(ac.items()):
            if not isinstance(e, dict):
                continue
            state, detail = verdict(e)
            counts[state] += 1
            rows.append((state, esc(fm.get('bean')), esc(ctype), detail))

    for state, bean, ctype, detail in rows:
        if QUIET and state == 'FRESH':
            continue
        _out(f"{state:8} {bean}.analysis_cache[{ctype}]  {detail}")

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
    exp_rows, expiring, notes = [], 0, []
    for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))):
        head, _ = dmparse.read(f)
        if head is None:
            continue
        try:
            fm = dmparse.loads(head) or {}
        except Exception:
            continue
        if not isinstance(fm, dict):
            continue
        for term, decl in expiry_terms().items():
            asides = []
            try:
                due = due_entries(fm, term, decl, notes=asides)
            except Exception as e:                  # noqa: BLE001 — the report goes on, and says what it could not read
                # ONE ENTRY THAT CANNOT BE READ MUST NOT COST THE READER EVERY OTHER WARNING — a domain about to lapse
                # among them. A day beyond the year 9999 once ended this report in a traceback, and every registration
                # in the garden went unreported with it. Whatever a defect here is, it is said as a NOTE.
                notes.append((fm.get('bean'), term, f"could not be read ({type(e).__name__}: {brief(e, 200)}) — the rest "
                                                    f"of this report stands"))
                continue
            for label, held, day, shown, detail in due:
                if day is None:
                    notes.append((fm.get('bean'), term + label, detail))
                    notes.extend((fm.get('bean'), term + label, t) for l, t in asides if l == label)
                    continue
                days = day - datetime.date.today().toordinal()
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
                exp_rows.append((state, fm.get('bean'), days, shown, term + label, decl, held, horizon, detail, term,
                                 [t for l, t in asides if l == label]))

    if exp_rows or notes:
        _out()
        for state, bean, days, shown, where, decl, held, horizon, detail, term, beside in sorted(exp_rows, key=lambda r: r[2]):
            if QUIET and state == 'OK':
                continue
            why = f"  <-- {decl['why']}" if (state != 'OK' and decl.get('why')) else ''
            _out(f"{state:8} {esc(bean)}.{esc(where)}  {decl['attr']} {shown} ({days} days){detail}"
                  f"{refine(term, held, state)}{why}")
            for text in beside:                     # a month the repetition skipped, said beside the row it explains
                _out(f"{'NOTE':8} {esc(bean)}.{esc(where)}  {text}")
        for bean, where, detail in notes:
            _out(f"{'NOTE':8} {esc(bean)}.{esc(where)}  {detail}")
        _out()
        _out(f"expiring: {sum(1 for r in exp_rows if r[0] == 'OK')} ok, "
              f"{sum(1 for r in exp_rows if r[0] == 'EXPIRING')} within their horizon, "
              f"{sum(1 for r in exp_rows if r[0] == 'EXPIRED')} EXPIRED"
              + (f", {len(notes)} that cannot be walked here (NOTE)" if notes else '')
              + (f"  [--days {HORIZON} overriding every term]" if HORIZON_SET else ''))

    _out()
    _out(f"analysis_cache: {counts['FRESH']} fresh, {counts['STALE']} stale, "
          f"{counts['NOT-HERE']} not on this host, {counts['UNKNOWN']} unknown")
    if counts['NOT-HERE']:
        _out("NOT-HERE is not staleness: those analyses may be perfectly current on the machine that "
              "holds their source. Give this host a `roots:` entry to resolve them here.")
    if counts['STALE']:
        _out("STALE means the SOURCE MOVED under the analysis, not that a clone is behind.")
        _out("STALE entries must NOT be trusted — re-run the analysis, then bump as_of + staleness_key "
              "(VOCAB analysis_cache.staleness_rule).")
    sys.exit(1 if (counts['STALE'] or expiring or _RUN['unread']) else 0)


if __name__ == '__main__':
    report()
