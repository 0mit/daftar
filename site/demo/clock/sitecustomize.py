"""Holds the day for the site's demo build. A Python process started with this directory on PYTHONPATH and
DAFTAR_DEMO_NOW set (an ISO moment with its offset) reads that moment from datetime.date.today() and
datetime.datetime.now(), so the pages say the same thing whatever day they are built on. Nothing else is changed:
time.time() still reads the machine's clock. Without DAFTAR_DEMO_NOW this file does nothing."""
import os
_at = os.environ.get('DAFTAR_DEMO_NOW')
if _at:
    import datetime as _dt
    _RealDate, _RealDT = _dt.date, _dt.datetime
    _moment = _RealDT.fromisoformat(_at)

    class date(_RealDate):
        @classmethod
        def today(cls):
            return cls(_moment.year, _moment.month, _moment.day)

    class datetime(_RealDT):
        @classmethod
        def now(cls, tz=None):
            m = _moment.astimezone(tz) if tz else _moment.astimezone().replace(tzinfo=None)
            return cls(m.year, m.month, m.day, m.hour, m.minute, m.second, m.microsecond, m.tzinfo)

        @classmethod
        def today(cls):
            return cls.now()

    _dt.date, _dt.datetime = date, datetime
