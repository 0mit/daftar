"""frame — a position in its system: the dot a filler of the shape `position` names (core spec §7, the rule `frame`).

A body takes room in space∞time and a sayable takes a place in the taxis; either way a position is a dot in a SYSTEM of
positions, written in that system's ONE form, and the systems are the standards' (`standards.Standards.systems`): the
calendars, the reference systems, the filesystems, the address spaces, the ordinal line. Nothing here names one.

HOW A POSITION NAMES ITS SYSTEM. A position is read in a system when exactly one system's form reads it whole —
`2026-10-01`, `persian:1405-07-09`, `192.0.2.10`, `ordinal:3`, `EPSG:4326;35.69,51.39` — or when it is written
`<system>:<value>` and that system's form reads the value: `tcp-port:445`. One that two systems read (`445` is a TCP
port, a UDP port and a geohash) is refused as ambiguous, and one that none reads is refused: a position is never guessed.

AN EXTENT is two positions of one system, written as ISO 8601 writes an interval (`2026-10-01/2027-09-30`,
`persian:1405-07-09/1406-07-08`): the end takes the start's tag when it carries none, and the start is not after it.

A DAY IS CHECKED, NOT ONLY ITS SPELLING. A position in a calendar is read by dmcal, which refuses a day its calendar
does not have (`persian:1404-12-30`) and a moment whose clock does not exist; a calendar that is not reckoned by rule
(the sighting of the moon) is read by its form alone.

THE OTHER HALF (`complement`). A day, or a clock reading with no offset, says when but not where the day is reckoned:
its place half is the bearer's, the garden's zone, where its system's row allows that (`complement: [stated, bearer]`).
A garden that names no zone leaves it nowhere, and the position is refused. `now` is the moment of the save, which the
save writes in its place."""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'bin'))
import dmcal    # noqa: E402 — positions in any calendar, through the day
import dmparse  # noqa: E402 — the one judge of a system's form

TAG = re.compile(r'^([a-z][a-z0-9-]*):(.+)$', re.S)
OFFSET = re.compile(r'(Z|[+-]\d{2}:\d{2})$')


class Refused(ValueError):
    """A string that is no position: the message says why, and what to write."""


class Position:
    __slots__ = ('text', 'system', 'end', 'day', 'moment', 'stated')

    def __init__(self, text, system, end=None, day=None, moment=None, stated=True):
        self.text, self.system, self.end, self.day, self.moment, self.stated = text, system, end, day, moment, stated

    def __repr__(self):
        return f"Position({self.text!r} in {self.system})"


def _systems_reading(text, systems):
    return [n for n, r in systems.items() if dmparse.in_form(r, text)]


def _dot(text, systems):
    """(system, value) of a single position, or Refused."""
    if text == 'now':
        return 'now', text
    m = TAG.match(text)
    if m and m.group(1) in systems and dmparse.in_form(systems[m.group(1)], m.group(2)):
        return m.group(1), m.group(2)
    reading = _systems_reading(text, systems)
    if len(reading) == 1:
        return reading[0], text
    if len(reading) > 1:
        raise Refused(f"{text!r} is read by {len(reading)} systems ({', '.join(sorted(reading))}): write it with its "
                      f"system, `<system>:{text}`")
    raise Refused(f"{text!r} is in no system's form: a position is a dot in a system the standards declare, written "
                  f"in its one form — `2026-10-01`, `persian:1405-07-09`, `192.0.2.10`, `tcp-port:445`, `ordinal:3`")


def _time(value):
    """(day, moment, stated) of a position in a calendar: its day number, the moment in ms where a clock and its offset
    are written (or a count from an epoch) and the calendar is reckoned by rule, and whether it is whole as written.
    Refused for a day or a clock that does not exist."""
    try:
        return None, dmcal.moment(value).ms, True       # a moment, whole: a day, a clock and its offset; an epoch count
    except dmcal.NotByRule:
        return None, None, bool(OFFSET.search(value))
    except ValueError:
        pass
    date, _sep, clock = re.split(r'([ T])', value, maxsplit=1) if re.search(r'[ T]', value) else (value, '', '')
    try:
        dmcal.calendar_of(date)
    except ValueError:
        return None, None, True     # a line of time no calendar of dmcal reckons (bp-1950, the chronostratigraphy)
    try:
        day = dmcal.to_day(date)
    except dmcal.NotByRule:
        day = None
    except ValueError as e:
        raise Refused(str(e)) from None
    if not clock:
        return day, None, False     # a day: reckoned in the bearer's zone
    stated = bool(OFFSET.search(clock))
    try:
        dmcal.moment(value if stated else value + 'Z')    # the clock itself, read: hours 00-23, minutes 00-59
    except dmcal.NotByRule:
        pass
    except ValueError as e:
        raise Refused(str(e)) from None
    return day, None, stated        # with no offset, a clock is reckoned in the bearer's zone


def _ordered(row):
    """A system whose dots follow one another: a line of time, or a line as the ordinal numbers are."""
    return str(row.get('dimension')) == 'time' or str(row.get('datum')) == 'line'


def _value_in(text, system, systems):
    """The value `text` holds in `system`, written whole in its form or tagged `<system>:` — None if neither."""
    if dmparse.in_form(systems[system], text):
        return text
    m = TAG.match(text)
    if m and m.group(1) == system and dmparse.in_form(systems[system], m.group(2)):
        return m.group(2)
    return None


def read(text, systems, zone=None):
    """The Position `text` names in one of `systems` ({name: row}), its other half found in `zone` (the bearer's, a
    garden's) where it needs one. Refused, saying why, for anything else.

    THE SLASH BETWEEN TWO DOTS OF AN ORDERED LINE IS ISO 8601's. Today's law gives `network-segment` and `git-remote`
    forms that also read `2026-10-01/2027-09-30`; so two halves in the form of one system whose dots follow one another
    are read as an extent first, and a segment or a remote spelled that way is written with its system."""
    if not isinstance(text, str):
        raise Refused(f"a position is one string in its system's form, not a {type(text).__name__}")
    if text.count('/') == 1:
        a, b = text.split('/')
        m = TAG.match(a)
        if m and not TAG.match(b):
            b = f"{m.group(1)}:{b}"         # the end takes the start's tag: `persian:1405-07-09/1406-07-08`
        common = [s for s in systems if _ordered(systems[s]) and _value_in(a, s, systems) is not None
                  and _value_in(b, s, systems) is not None]
        if len(common) > 1:
            raise Refused(f"{text!r} is an extent in {len(common)} systems ({', '.join(sorted(common))}): write it "
                          f"with its system")
        if common:
            return _extent(text, common[0], a, b, systems, zone)
    system, value = _dot(text, systems)
    return _whole(text, system, value, systems, zone)


def _whole(text, system, value, systems, zone):
    if system == 'now':
        return Position(text, 'now', stated=True)
    row = systems[system]
    day = mo = None
    stated = True
    if str(row.get('dimension')) == 'time':
        day, mo, stated = _time(value)
    if not stated:
        comp = row.get('complement') or []
        if 'bearer' not in comp:
            raise Refused(f"{text!r} names no offset, and {system} finds the other half of a position only as "
                          f"{', '.join(comp) or 'nothing'}: write the offset")
        if not zone:
            raise Refused(f"{text!r} is a day, or a clock with no offset: it is reckoned in the bearer's zone, and this "
                          f"garden names none (GARDEN.md `zone`)")
    return Position(text, system, day=day, moment=mo, stated=stated)


def _extent(text, system, a, b, systems, zone):
    start = _whole(a, system, _value_in(a, system, systems), systems, zone)
    end = _whole(b, system, _value_in(b, system, systems), systems, zone)
    after = False
    if start.moment is not None and end.moment is not None:
        after = start.moment > end.moment
    elif start.day is not None and end.day is not None:
        after = start.day > end.day
    elif system == 'ordinal-number' or str(systems[system].get('datum')) == 'line':
        after = int(re.sub(r'\D', '', a)) > int(re.sub(r'\D', '', b))
    if after:
        raise Refused(f"{text!r}: an extent runs from its start to its end, and this one starts after it ends")
    return Position(text, system, end=end, day=start.day, moment=start.moment, stated=start.stated and end.stated)
