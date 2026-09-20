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

Pure: it reads nothing, writes nothing, imports nothing outside the standard library.
"""
import datetime, math, re, sys


class NotByRule(Exception):
    pass


def _q(a, b):
    return a // b


# ------------------------------------------------------------------ gregorian, and the three that are its years renamed
def g_to_day(y, m, d):
    return datetime.date(y, m, d).toordinal()


def g_from_day(n):
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
    m = math.ceil(doy / 31) if doy <= 186 else math.ceil((doy - 6) / 30)
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


def hebrew_from_day(n):
    y = _q(n - HEBREW_EPOCH, 366) + 1
    while _h_new_year(y + 1) <= n:
        y += 1
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
NOT_BY_RULE = {
    'chinese':          "astronomical: months begin at the new moon and the year is fitted to the solstices, as computed for a meridian",
    'dangi':            "astronomical, as the Chinese calendar is, computed for Korea",
    'islamic':          "observational: a month begins when the crescent is sighted",
    'islamic-rgsa':     "observational: the sighting as announced in Saudi Arabia",
    'islamic-umalqura': "tabulated: the Umm al-Qura calendar is a published table, not a rule",
}
_TAGGED = re.compile(r'^([a-z][a-z0-9-]*):(-?\d+)-(\d{2})(L?)-(\d{2})$')
_JAPANESE = re.compile(r'^japanese:([a-z]+)-(\d+)-(\d{2})-(\d{2})$')
_ISO_WEEK = re.compile(r'^(-?\d{4})-W(\d{2})-([1-7])$')
_GREGORIAN = re.compile(r'^(\d{4})-(\d{2})-(\d{2})')


def to_day(position):
    """The day number of a position written in its system's one form (the date part)."""
    position = str(position).strip()
    m = _ISO_WEEK.match(position)
    if m:
        return datetime.date.fromisocalendar(int(m.group(1)), int(m.group(2)), int(m.group(3))).toordinal()
    m = _JAPANESE.match(position)
    if m:
        era, ey, mo, d = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        if era not in _ERA_FIRST_YEAR:
            raise ValueError(f"no era '{era}' is reckoned here: {sorted(_ERA_FIRST_YEAR)}")
        n = g_to_day(_ERA_FIRST_YEAR[era] + ey - 1, mo, d)
        if japanese_from_day(n)[0] != era:
            raise ValueError(f"{position} does not fall within the {era} era")
        return n
    m = _TAGGED.match(position)
    if m:
        cal, y, mo, leap, d = m.group(1), int(m.group(2)), int(m.group(3)), m.group(4), int(m.group(5))
        if cal in NOT_BY_RULE:
            raise NotByRule(f"{cal} is not reckoned by rule — {NOT_BY_RULE[cal]}. Convert it by looking it up, and record where")
        if cal not in BY_RULE:
            raise ValueError(f"no calendar '{cal}'")
        if leap:
            raise ValueError(f"{cal} has no leap-month marker: only the astronomical lunisolar calendars write one")
        return BY_RULE[cal][0](y, mo, d)
    m = _GREGORIAN.match(position)
    if m:
        return g_to_day(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    raise ValueError(f"'{position}' is in no calendar's form")


def japanese_from_day(n):
    y, m, d = g_from_day(n)
    for era, start in JAPANESE_ERAS:
        if (y, m, d) >= start:
            return era, y - _ERA_FIRST_YEAR[era] + 1, m, d
    raise ValueError("before 1873-01-01 Japan did not reckon by the Gregorian calendar, and this does not guess")


def from_day(n, calendar):
    """The position of day `n` in `calendar`, in that system's one form."""
    if calendar in ('gregory', 'gregorian-civil'):
        return '%04d-%02d-%02d' % g_from_day(n)
    if calendar in ('iso8601', 'iso-week'):
        t = datetime.date.fromordinal(n).isocalendar()
        return '%04d-W%02d-%d' % (t[0], t[1], t[2])
    if calendar == 'japanese':
        return 'japanese:%s-%d-%02d-%02d' % japanese_from_day(n)
    if calendar in NOT_BY_RULE:
        raise NotByRule(f"{calendar} is not reckoned by rule — {NOT_BY_RULE[calendar]}")
    y, m, d = BY_RULE[calendar][1](n)
    return '%s:%d-%02d-%02d' % (calendar, y, m, d)


def convert(position, calendar):
    return from_day(to_day(position), calendar)


EVERY = ['gregory', 'iso8601', 'julian', 'persian', 'islamic-civil', 'islamic-tbla', 'hebrew', 'coptic', 'ethiopic',
         'ethioaa', 'indian', 'buddhist', 'roc', 'japanese']


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__); return 0
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
