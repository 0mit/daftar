#!/usr/bin/env python3
"""dmcal — positions in any calendar, converted THROUGH THE DAY.

    python3 bin/dmcal.py 2026-09-20                      # a position, read in every calendar that reckons by rule
    python3 bin/dmcal.py persian:1405-06-29 hebrew       # one position, in one other calendar
    python3 bin/dmcal.py --day 739880                    # a day number, in every calendar

A CALENDAR IS NOT TIME. It is one PARTITION of the line of days into named cells — years, months — and the law
declares each as a positioning system with its own levels (`seed/std-vocab.md`, `anchor_systems`, dimension
time). Every calendar here partitions the SAME line, so they all meet at one level: THE DAY. Converting is
therefore never calendar-to-calendar; it is calendar -> day number -> calendar, and a calendar only has to know
its own two functions. The day number is the count of days since 0001-01-01 in the proleptic Gregorian calendar
(Python's `date.toordinal()`, the "R.D." of Dershowitz & Reingold, whose algorithms these are).

NOT EVERY CALENDAR RECKONS BY RULE, and this tool refuses rather than approximates. The Chinese and Korean
calendars are astronomical; `islamic` and `islamic-rgsa` follow the sighting of the moon; `islamic-umalqura` is
a published table. For those a position is converted by LOOKING IT UP in what somebody observed or published,
never by arithmetic — the law says so in each row's `reckoning`, and `to_day` raises `NotByRule`.

A DAY DOES NOT BEGIN AT THE SAME MOMENT IN EVERY CALENDAR. The Hebrew and Islamic day begins at SUNSET. The day
number here is the civil day on which the calendar day's DAYLIGHT falls, which is the universal convention; an
evening position is the law's business (`day_begins`), not this tool's.

A DAY THAT DOES NOT EXIST IS REFUSED, NEVER MOVED. `persian:1404-12-30` names a day Esfand 1404 does not have, and
arithmetic alone would read it as the day after the 29th — a day nobody named. So a position is read only if it comes
back unchanged from its own day (`from_day(to_day(p)) == p`), and `to_day` raises ValueError for one that does not; so
it does for a year outside the days reckoned here (FIRST_DAY .. LAST_DAY, below), and `from_day` for a day outside them.

Pure: it reads nothing, writes nothing, imports nothing outside the standard library — except, run as a command, the
module that makes its output UTF-8 on every platform (bin/dmparse.py).
"""
import datetime, math, os, re, sys


class NotByRule(Exception):
    pass


def _q(a, b):
    return a // b


# ------------------------------------------------------------------ gregorian, and the three that are its years renamed
def g_to_day(y, m, d):
    return datetime.date(y, m, d).toordinal()


def g_from_day(n):
    if n < 1:
        raise ValueError(f"day {n} is before 0001-01-01, the first day the Gregorian reckoning here holds")
    t = datetime.date.fromordinal(n)
    return t.year, t.month, t.day


JAPANESE_ERAS = (('reiwa', (2019, 5, 1)), ('heisei', (1989, 1, 8)), ('showa', (1926, 12, 25)),
                 ('taisho', (1912, 7, 30)), ('meiji', (1873, 1, 1)))   # Meiji counted from 1868; Japan adopted the
                                                                       # Gregorian calendar on 1873-01-01, and a
                                                                       # position before that is not reckoned here
_ERA_FIRST_YEAR = {'reiwa': 2019, 'heisei': 1989, 'showa': 1926, 'taisho': 1912, 'meiji': 1868}


# ------------------------------------------------------------------ julian
JULIAN_EPOCH = -1


def julian_to_day(y, m, d):
    yy = y + 1 if y < 0 else y
    return (JULIAN_EPOCH - 1 + 365 * (yy - 1) + _q(yy - 1, 4) + _q(367 * m - 362, 12)
            + (0 if m <= 2 else (-1 if yy % 4 == 0 else -2)) + d)


def julian_from_day(n):
    approx = _q(4 * (n - JULIAN_EPOCH) + 1464, 1461)
    y = approx - 1 if approx <= 0 else approx
    prior = n - julian_to_day(y, 1, 1)
    yy = y + 1 if y < 0 else y
    corr = 0 if n < julian_to_day(y, 3, 1) else (1 if yy % 4 == 0 else 2)
    m = _q(12 * (prior + corr) + 373, 367)
    return y, m, n - julian_to_day(y, m, 1) + 1


# ------------------------------------------------------------------ coptic, ethiopic: twelve months of 30 and a little one
def _copt_to_day(epoch):
    return lambda y, m, d: epoch - 1 + 365 * (y - 1) + _q(y, 4) + 30 * (m - 1) + d


def _copt_from_day(epoch):
    def f(n):
        y = _q(4 * (n - epoch) + 1463, 1461)
        m = _q(n - _copt_to_day(epoch)(y, 1, 1), 30) + 1
        return y, m, n + 1 - _copt_to_day(epoch)(y, m, 1)
    return f


COPTIC_EPOCH, ETHIOPIC_EPOCH = 103605, 2796


# ------------------------------------------------------------------ the tabular Hijri calendars
def _isl_to_day(epoch):
    return lambda y, m, d: epoch - 1 + (y - 1) * 354 + _q(3 + 11 * y, 30) + 29 * (m - 1) + _q(m, 2) + d


def _isl_from_day(epoch):
    def f(n):
        y = _q(30 * (n - epoch) + 10646, 10631)
        prior = n - _isl_to_day(epoch)(y, 1, 1)
        m = _q(11 * prior + 330, 325)
        return y, m, n - _isl_to_day(epoch)(y, m, 1) + 1
    return f


ISLAMIC_CIVIL_EPOCH, ISLAMIC_TBLA_EPOCH = 227015, 227014      # Friday 622-07-16 Julian; and the astronomers' Thursday


# ------------------------------------------------------------------ persian (Solar Hijri): the breaks of the 33-year cycles
# The official calendar is astronomical — the year begins at the equinox as seen from Tehran. It is reproduced, over the
# range below, by the cycle-break table of Borkowski (1996), which is what the calendar libraries in daily use in Iran
# carry. Outside the range this REFUSES: an approximation that is silently wrong by a day is worse than no answer.
_P_BREAKS = (-61, 9, 38, 199, 426, 686, 756, 818, 1111, 1181, 1210, 1635, 2060, 2097, 2192, 2262, 2324, 2394, 2456, 3178)


def _persian_year(jy):
    """(is_leap, gregorian year, day of March on which 1 Farvardin falls)."""
    if not (_P_BREAKS[0] <= jy < _P_BREAKS[-1]):
        raise ValueError(f"persian year {jy} is outside {_P_BREAKS[0]}..{_P_BREAKS[-1] - 1}, the range this reckoning is good for")
    gy, leap_j, jp, jump = jy + 621, -14, _P_BREAKS[0], 0
    for jm in _P_BREAKS[1:]:
        jump = jm - jp
        if jy < jm:
            break
        leap_j += _q(jump, 33) * 8 + _q(jump % 33, 4)
        jp = jm
    n = jy - jp
    leap_j += _q(n, 33) * 8 + _q(n % 33 + 3, 4)
    if jump % 33 == 4 and jump - n == 4:
        leap_j += 1
    leap_g = _q(gy, 4) - _q((_q(gy, 100) + 1) * 3, 4) - 150
    march = 20 + leap_j - leap_g
    if jump - n < 6:
        n = n - jump + _q(jump + 4, 33) * 33
    leap = ((n + 1) % 33 - 1) % 4
    if leap == -1:
        leap = 4
    return leap == 0, gy, march


def persian_to_day(y, m, d):
    _leap, gy, march = _persian_year(y)
    return g_to_day(gy, 3, march) + ((m - 1) * 31 if m <= 7 else (m - 1) * 30 + 6) + d - 1


def persian_from_day(n):
    gy = g_from_day(n)[0]
    y = gy - 621
    if n < persian_to_day(y, 1, 1):
        y -= 1
    doy = n - persian_to_day(y, 1, 1) + 1
    m = -(-doy // 31) if doy <= 186 else -(-(doy - 6) // 30)      # a ceiling in whole numbers: no float is involved
    return y, m, n - persian_to_day(y, m, 1) + 1


# ------------------------------------------------------------------ hebrew: a lunisolar calendar reckoned wholly by rule
# Months are numbered as CLDR numbers them, from Tishri: 1 Tishri … 5 Shevat, 6 Adar I (LEAP YEARS ONLY), 7 Adar,
# 8 Nisan … 13 Elul. A common year has no month 6.
HEBREW_EPOCH = -1373427


def _h_leap(y):
    return (7 * y + 1) % 19 < 7


def _h_elapsed(y):
    months = _q(235 * y - 234, 19)
    parts = 12084 + 13753 * months
    day = 29 * months + _q(parts, 25920)
    return day + 1 if (3 * (day + 1)) % 7 < 3 else day


def _h_new_year(y):
    ny0, ny1, ny2 = _h_elapsed(y - 1), _h_elapsed(y), _h_elapsed(y + 1)
    delay = 2 if ny2 - ny1 == 356 else (1 if ny1 - ny0 == 382 else 0)
    return HEBREW_EPOCH + ny1 + delay


def _h_month_lengths(y):
    """[(cldr month number, days)] in the order the year runs, from Tishri."""
    days = _h_new_year(y + 1) - _h_new_year(y)
    heshvan = 30 if days in (355, 385) else 29
    kislev = 29 if days in (353, 383) else 30
    out = [(1, 30), (2, heshvan), (3, kislev), (4, 29), (5, 30)]
    out += [(6, 30), (7, 29)] if _h_leap(y) else [(7, 29)]
    return out + [(8, 30), (9, 29), (10, 30), (11, 29), (12, 30), (13, 29)]


def hebrew_to_day(y, m, d):
    n = _h_new_year(y)
    for num, length in _h_month_lengths(y):
        if num == m:
            if not 1 <= d <= length:
                raise ValueError(f"hebrew {y}-{m:02d} has {length} days")
            return n + d - 1
        n += length
    raise ValueError(f"hebrew year {y} has no month {m} — month 6 (Adar I) exists only in a leap year")


# THE YEAR IS ESTIMATED, NOT COUNTED UP TO (Dershowitz & Reingold, `hebrew-from-fixed`). The mean Hebrew year is
# 35975351/98496 days — 235 months of 29d 12h 793p in 19 years — and a year begins at most a month before its mean
# start and a few days after it, so the days since the epoch over the mean year, in whole numbers, give the year to
# within one either way: the latest of the three whose new year has come is the year. Counting up a year at a time from
# n/366 cost a second for every few hundred million days: a clause due in a year of eleven digits took 22 seconds to
# read, and one of sixteen never finished — in every reader of every garden it was taken into.
_H_MEAN_YEAR = (35975351, 98496)


def hebrew_from_day(n):
    approx = _q((n - HEBREW_EPOCH) * _H_MEAN_YEAR[1], _H_MEAN_YEAR[0]) + 1
    y = next((c for c in (approx + 1, approx, approx - 1) if _h_new_year(c) <= n), None)
    if y is None or not n < _h_new_year(y + 1):
        raise AssertionError(f"day {n}: the mean-year estimate {approx} is more than one year out")   # never: see above
    rest = n - _h_new_year(y)
    for num, length in _h_month_lengths(y):
        if rest < length:
            return y, num, rest + 1
        rest -= length
    raise AssertionError("unreachable")


# ------------------------------------------------------------------ the Indian national (Saka) calendar
def indian_to_day(y, m, d):
    gy = y + 78
    leap = gy % 4 == 0 and (gy % 100 != 0 or gy % 400 == 0)
    start = g_to_day(gy, 3, 21 if leap else 22)
    lengths = [31 if leap else 30] + [31] * 5 + [30] * 6
    return start + sum(lengths[:m - 1]) + d - 1


def indian_from_day(n):
    gy = g_from_day(n)[0]
    y = gy - 78
    if n < indian_to_day(y, 1, 1):
        y -= 1
    rest = n - indian_to_day(y, 1, 1)
    gy = y + 78
    leap = gy % 4 == 0 and (gy % 100 != 0 or gy % 400 == 0)
    for m, length in enumerate([31 if leap else 30] + [31] * 5 + [30] * 6, 1):
        if rest < length:
            return y, m, rest + 1
        rest -= length
    raise AssertionError("unreachable")


# ------------------------------------------------------------------ the table: a calendar is two functions
def _offset(k):
    return (lambda y, m, d: g_to_day(y - k, m, d)), (lambda n: (lambda t: (t[0] + k, t[1], t[2]))(g_from_day(n)))


BY_RULE = {
    'gregory':       (g_to_day, g_from_day),
    'julian':        (julian_to_day, julian_from_day),
    'buddhist':      _offset(543),
    'roc':           _offset(-1911),
    'persian':       (persian_to_day, persian_from_day),
    'islamic-civil': (_isl_to_day(ISLAMIC_CIVIL_EPOCH), _isl_from_day(ISLAMIC_CIVIL_EPOCH)),
    'islamic-tbla':  (_isl_to_day(ISLAMIC_TBLA_EPOCH), _isl_from_day(ISLAMIC_TBLA_EPOCH)),
    'coptic':        (_copt_to_day(COPTIC_EPOCH), _copt_from_day(COPTIC_EPOCH)),
    'ethiopic':      (_copt_to_day(ETHIOPIC_EPOCH), _copt_from_day(ETHIOPIC_EPOCH)),
    'ethioaa':       ((lambda y, m, d: _copt_to_day(ETHIOPIC_EPOCH)(y - 5500, m, d)),
                      (lambda n: (lambda t: (t[0] + 5500, t[1], t[2]))(_copt_from_day(ETHIOPIC_EPOCH)(n)))),
    'hebrew':        (hebrew_to_day, hebrew_from_day),
    'indian':        (indian_to_day, indian_from_day),
}
# THE DAY ITSELF, as astronomers count it: the Julian Day Number of the day's noon. Every calendar here meets the others at
# the day, and this is that meeting point given a name and a form. And the Mayan long count, which is nothing BUT a count
# of days, written in mixed base 20 and 18 from a zero day (the Goodman-Martinez-Thompson correlation, JDN 584283).
JDN_OFFSET, MAYAN_EPOCH = 1721425, -1137142      # JDN = day number + 1721425: 2000-01-01 is JDN 2451545

# THE DAYS RECKONED HERE: from the first the law's plain count of days writes (`jdn:0`, 1 January 4713 BCE in the Julian
# calendar) to the last its Gregorian form writes (`9999-12-31`: four digits of year). Every calendar is read and written
# over these days and no others, so each accepts only the years that fall within them — as the Persian reckoning always
# accepted only the years its table is good for. Within them every rule here is exact and quick. Beyond them a year of
# sixteen digits was arithmetic nobody finished, and a day no reader can write is a day it can never tell anyone about.
FIRST_DAY, LAST_DAY = -JDN_OFFSET, datetime.date.max.toordinal()


def within(n, what=None):
    """`n`, when it is a day reckoned here; else ValueError, saying which days are."""
    if isinstance(n, bool) or not isinstance(n, int):
        raise ValueError(f"{n!r} is not a day number")
    if not FIRST_DAY <= n <= LAST_DAY:
        raise ValueError(f"{what or f'day {n}'} is outside the days reckoned here: jdn:0 (4713 BCE) to 9999-12-31")
    return n


def mayan_to_day(parts):
    b, k, t, u, d = parts
    return MAYAN_EPOCH + b * 144000 + k * 7200 + t * 360 + u * 20 + d


def mayan_from_day(n):
    r = n - MAYAN_EPOCH
    out = []
    for size in (144000, 7200, 360, 20, 1):
        out.append(r // size); r %= size
    return tuple(out)


NOT_BY_RULE = {
    'bahai':            "astronomical since 2015: the year begins at the equinox as computed for Tehran, and one month is fixed by a new moon",
    'french-republican': "astronomical: the year begins at the autumn equinox as observed from Paris",
    'chinese':          "astronomical: months begin at the new moon and the year is fitted to the solstices, as computed for a meridian",
    'dangi':            "astronomical, as the Chinese calendar is, computed for Korea",
    'islamic':          "observational: a month begins when the crescent is sighted",
    'islamic-rgsa':     "observational: the sighting as announced in Saudi Arabia",
    'islamic-umalqura': "tabulated: the Umm al-Qura calendar is a published table, not a rule",
}
_TAGGED = re.compile(r'^([a-z][a-z0-9-]*):(-?\d+)-(\d{2})(L?)-(\d{2})$')
_JAPANESE = re.compile(r'^japanese:([a-z]+)-(\d+)-(\d{2})-(\d{2})$')
_JDN = re.compile(r'^jdn:(\d+)$')
_MAYAN = re.compile(r'^mayan:(\d+)\.(\d+)\.(\d+)\.(\d+)\.(\d+)$')
_ISO_WEEK = re.compile(r'^(-?\d{4})-W(\d{2})-([1-7])$')
_GREGORIAN = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')


def to_day(position):
    """The day number of a position written in its system's one form (the date part). ValueError for a day its calendar
    does not have, and for one outside the days reckoned here; NotByRule for a calendar that is not reckoned by rule."""
    position = str(position).strip()
    shown = position if len(position) <= 60 else f"{position[:60]}… ({len(position)} characters)"
    try:
        return within(_to_day(position, shown), shown)
    except OverflowError:
        # A YEAR TOO LARGE FOR THE MACHINE'S DATE is a year outside the days reckoned here, said as the others are — not
        # a second kind of failure every reader would have to know to catch.
        raise ValueError(f"{shown} is outside the days reckoned here: jdn:0 (4713 BCE) to 9999-12-31") from None


def _to_day(position, shown):
    # EVERY NUMBER IS READ BY _num: one wider than any count of days or years within the days reckoned here is outside
    # them, and is refused as that before it is read at all — Python itself refuses to read one of more than 4300 digits,
    # in words about its own settings that no reader of a calendar should be handed.
    def _num(text):
        if len(text.lstrip('-').lstrip('0')) > len(str(LAST_DAY + JDN_OFFSET)):
            raise ValueError(f"{shown} is outside the days reckoned here: jdn:0 (4713 BCE) to 9999-12-31")
        return int(text)

    m = _JDN.match(position)
    if m:
        return _num(m.group(1)) - JDN_OFFSET
    m = _MAYAN.match(position)
    if m:
        parts = tuple(_num(x) for x in m.groups())
        if not (parts[1] < 20 and parts[2] < 20 and parts[3] < 18 and parts[4] < 20):
            raise ValueError(f"{shown}: a katun and a tun run 0-19, a uinal 0-17, a kin 0-19")
        return mayan_to_day(parts)
    m = _ISO_WEEK.match(position)
    if m:
        try:
            return datetime.date.fromisocalendar(_num(m.group(1)), _num(m.group(2)), _num(m.group(3))).toordinal()
        except ValueError as e:
            raise ValueError(f"{shown} is not a day of the ISO week calendar ({e})")
    m = _JAPANESE.match(position)
    if m:
        era, ey, mo, d = m.group(1), _num(m.group(2)), _num(m.group(3)), _num(m.group(4))
        if era not in _ERA_FIRST_YEAR:
            raise ValueError(f"no era '{era}' is reckoned here: {sorted(_ERA_FIRST_YEAR)}")
        try:
            n = g_to_day(_ERA_FIRST_YEAR[era] + ey - 1, mo, d)
        except ValueError as e:
            raise ValueError(f"{shown} is not a day of the Japanese calendar ({e})")
        if japanese_from_day(n)[0] != era:
            raise ValueError(f"{shown} does not fall within the {era} era")
        return n
    m = _TAGGED.match(position)
    if m:
        cal, y, mo, leap, d = m.group(1), _num(m.group(2)), _num(m.group(3)), m.group(4), _num(m.group(5))
        if cal in NOT_BY_RULE:
            raise NotByRule(f"{cal} is not reckoned by rule — {NOT_BY_RULE[cal]}. Convert it by looking it up, and record where")
        if cal not in BY_RULE:
            raise ValueError(f"no calendar '{cal}'")
        if leap:
            raise ValueError(f"{cal} has no leap-month marker: only the astronomical lunisolar calendars write one")
        try:
            n = BY_RULE[cal][0](y, mo, d)
        except ValueError as e:
            raise ValueError(f"{shown} is not a day of the {cal} calendar ({e})")
        within(n, shown)
        # THE ROUND TRIP: a position is a day of its calendar only if that day, written back in the calendar, is the
        # position. Arithmetic takes the 30th of a month of 29 days to be the 1st of the next, and a clause due on it
        # was then walked on the 1st of every month — a day neither party named.
        back = BY_RULE[cal][1](n)
        if back != (y, mo, d):
            raise ValueError(f"{shown} is not a day of the {cal} calendar: counted by its rule it would fall on "
                             f"{cal}:{back[0]}-{back[1]:02d}-{back[2]:02d}, and a day nobody named is refused, never read "
                             f"as another")
        return n
    m = _GREGORIAN.match(position)
    if m:
        try:
            return g_to_day(_num(m.group(1)), _num(m.group(2)), _num(m.group(3)))
        except ValueError as e:
            raise ValueError(f"{shown} is not a day of the Gregorian calendar ({e})")
    raise ValueError(f"'{shown}' is in no calendar's form")


def japanese_from_day(n):
    y, m, d = g_from_day(n)
    for era, start in JAPANESE_ERAS:
        if (y, m, d) >= start:
            return era, y - _ERA_FIRST_YEAR[era] + 1, m, d
    raise ValueError("before 1873-01-01 Japan did not reckon by the Gregorian calendar, and this does not guess")


def from_day(n, calendar):
    """The position of day `n` in `calendar`, in that system's one form. ValueError for a day outside the days reckoned
    here, or before the first its calendar holds; NotByRule for a calendar that is not reckoned by rule."""
    within(n)
    if calendar in ('gregory', 'gregorian-civil'):
        return '%04d-%02d-%02d' % g_from_day(n)
    if calendar in ('iso8601', 'iso-week'):
        t = datetime.date(*g_from_day(n)).isocalendar()
        return '%04d-W%02d-%d' % (t[0], t[1], t[2])
    if calendar == 'julian-day':
        return 'jdn:%d' % (n + JDN_OFFSET)
    if calendar == 'mayan-long-count':
        if n < MAYAN_EPOCH:
            raise ValueError(f"day {n} is before the long count's zero day, mayan:0.0.0.0.0 (3114 BCE)")
        return 'mayan:%d.%d.%d.%d.%d' % mayan_from_day(n)
    if calendar == 'japanese':
        return 'japanese:%s-%d-%02d-%02d' % japanese_from_day(n)
    if calendar in NOT_BY_RULE:
        raise NotByRule(f"{calendar} is not reckoned by rule — {NOT_BY_RULE[calendar]}")
    if calendar not in BY_RULE:
        raise ValueError(f"no calendar '{calendar}'")
    y, m, d = BY_RULE[calendar][1](n)
    return '%s:%d-%02d-%02d' % (calendar, y, m, d)


def convert(position, calendar):
    return from_day(to_day(position), calendar)


EVERY = ['gregory', 'iso8601', 'julian', 'persian', 'islamic-civil', 'islamic-tbla', 'hebrew', 'coptic', 'ethiopic',
         'ethioaa', 'indian', 'buddhist', 'roc', 'japanese', 'julian-day', 'mayan-long-count']


def main(argv):
    # RUN AS A COMMAND IT SPEAKS UTF-8 ON EVERY PLATFORM, as every tool here does: bin/dmparse.py sets the streams once, on
    # import. A pipe on Windows is otherwise written in the ANSI code page, which has no Hebrew, no Persian and no `—`.
    # Imported here and not above, so that a reader importing this module still imports nothing but the standard library.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import dmparse  # noqa: F401
    if not argv or argv[0] in ('-h', '--help'):
        # the interpreter as it is named where this runs: `python3` may be the Microsoft Store's alias on Windows
        print(__doc__.replace('python3 bin/', ('python' if os.name == 'nt' else 'python3') + ' bin/')); return 0
    if argv[0] == '--day' and (len(argv) < 2 or not re.fullmatch(r'-?[0-9]+', argv[1], re.ASCII)):
        print("dmcal: --day takes a day number, e.g. --day 739880"); return 2
    try:
        n = int(argv[1]) if argv[0] == '--day' else to_day(argv[0])
        wanted = argv[2:] if argv[0] == '--day' else argv[1:]
        print(f"day {n}")
        for cal in (wanted or EVERY):
            try:
                print(f"  {cal:16} {from_day(n, cal)}")
            except (NotByRule, ValueError) as e:
                print(f"  {cal:16} — {e}")
        if not wanted:
            for cal, why in NOT_BY_RULE.items():
                print(f"  {cal:16} — not reckoned by rule: {why}")
        return 0
    except (NotByRule, ValueError) as e:
        print(f"dmcal: {e}"); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
