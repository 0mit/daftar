"""formats — bytes and records, by the formats of the law (core/law/formats.yaml): one reader and one writer a format and
none privileged, the conversions a crosswalk's field is read through, and the readers that give the records of a model
where a format alone cannot (2.12; MODEL.md, Imports and exports).

    from core import formats
    for rec in formats.read('csv', path):          # each a Record: a mapping of its fields, its place in `rec.at`
        ...
    text = formats.write('json', records)

A RECORD is a mapping of fields to values, as its format writes them: a CSV's row by its header, a JSON object as it is
nested, a database's row by its columns. A field is named by its path (`subject.reference`, `note[0].text`), or by its
key where the key is written whole (`ExifIFD:SerialNumber`). A number is read as it is written, never as a binary float,
and a name the world gives in bytes is written `escaped`.

THE READERS, which turn a format's records into a model's where no mapping can say how, are core/readers.py's: every
reader of the law's one table (core/law/formats.yaml `readers`) in one place.
"""
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
from decimal import Decimal


class Refused(Exception):
    """A source no format of the law reads as asked: said, never guessed."""


class Record(dict):
    """One record: its fields, where it was read (`at`), and the model a reader gave it (`model`)."""
    __slots__ = ('at', 'model')

    def __init__(self, fields=(), at=None, model=None):
        super().__init__(fields)
        self.at, self.model = at, model


# ------------------------------------------------------------------------------------------------ a name in bytes
_KEEP = re.compile(rb'[\x00-\x1f\x7f%]')


def escape(raw):
    """A name the world gives in bytes, as text (`escaped`): UTF-8, and `%XX` for a byte that is no part of well-formed
    UTF-8, a control character (C0, DEL, C1) and `%` itself."""
    if isinstance(raw, str):
        raw = os.fsencode(raw)
    out = []
    for ch in bytes(raw).decode('utf-8', 'surrogateescape'):
        o = ord(ch)
        if 0xDC80 <= o <= 0xDCFF:                       # a byte surrogateescape kept: not well-formed UTF-8
            out.append('%%%02X' % (o - 0xDC00))
        elif o < 0x20 or o == 0x7F or 0x80 <= o <= 0x9F or ch == '%':
            out.extend('%%%02X' % b for b in ch.encode('utf-8'))
        else:
            out.append(ch)
    return ''.join(out)


def unescape(text):
    """The bytes a text written `escaped` stands for."""
    out, i = bytearray(), 0
    while i < len(text):
        if text[i] == '%' and re.match(r'^[0-9A-F]{2}$', text[i + 1:i + 3]):
            out.append(int(text[i + 1:i + 3], 16))
            i += 3
        else:
            out += text[i].encode('utf-8')
            i += 1
    return bytes(out)


# ------------------------------------------------------------------------------------------------ fields of a record
_STEP = re.compile(r'^([^\[\]]+)((?:\[\d+\])*)$')


def get(rec, path):
    """The value at a field's path in a record, or None: the key written whole first, then the path step by step, `[n]`
    an item of a list."""
    if not isinstance(rec, dict):
        return None
    if path in rec:
        return rec[path]
    cur = rec
    for step in path.split('.'):
        m = _STEP.match(step)
        if not m or not isinstance(cur, dict) or m.group(1) not in cur:
            return None
        cur = cur[m.group(1)]
        for n in re.findall(r'\[(\d+)\]', m.group(2)):
            if not isinstance(cur, list) or int(n) >= len(cur):
                return None
            cur = cur[int(n)]
    return cur


def put(rec, path, value):
    """Set the field at its path, making each mapping and list on the way (`note[0].text` makes a list of one)."""
    steps = []
    for step in path.split('.'):
        m = _STEP.match(step)
        steps.append(m.group(1))
        steps += [int(n) for n in re.findall(r'\[(\d+)\]', m.group(2))]
    cur = rec
    for i, k in enumerate(steps):
        last = i == len(steps) - 1
        if isinstance(k, int):
            while len(cur) <= k:
                cur.append(None)
        if last:
            cur[k] = value
            return
        nxt = [] if isinstance(steps[i + 1], int) else {}
        here = cur[k] if isinstance(k, int) else cur.get(k)
        if not isinstance(here, type(nxt)):
            cur[k] = nxt
        cur = cur[k]


def leaves(node, path=''):
    """{path: value} of every value a record holds, a list's items as `[i]`: what the account counts."""
    out = {}
    if isinstance(node, dict):
        for k, v in node.items():
            out.update(leaves(v, f"{path}.{k}" if path else str(k)))
    elif isinstance(node, list):
        for i, v in enumerate(node):
            out.update(leaves(v, f"{path}[{i}]"))
    else:
        out[path] = node
    return out


# ------------------------------------------------------------------------------------------------ the formats
def _bytes(source):
    if isinstance(source, (bytes, bytearray)):
        return bytes(source)
    with open(source, 'rb') as fh:
        return fh.read()


def _text(source):
    try:
        return _bytes(source).decode('utf-8-sig')
    except UnicodeDecodeError as e:
        raise Refused(f"not UTF-8 text: {e}") from None


def _tsv(source, spec):
    import parse as dmparse
    try:
        header, rows = dmparse.table_read(_text(source))
    except dmparse.TableError as e:
        raise Refused(f"no table in its one form: {e}") from None
    for n, row in enumerate(rows, 2):
        yield Record(zip(header, row), at=f"line {n}")


def _csv(source, spec):
    for n, row in enumerate(csv.DictReader(io.StringIO(_text(source))), 2):
        yield Record({k: v for k, v in row.items() if v not in ('', None) and k is not None}, at=f"line {n}")


def _number_json(text):
    return json.loads(text, parse_float=Decimal, parse_int=Decimal)


def _at_path(data, path):
    for step in [s for s in str(path or '').split('.') if s]:
        data = data.get(step) if isinstance(data, dict) else None
    return data


def held_bytes(v):
    """Whether a text read by `_named_text` holds a byte that is no part of UTF-8 (U+DC80–U+DCFF, surrogateescape)."""
    return isinstance(v, str) and any('\udc80' <= ch <= '\udcff' for ch in v)


def _named_text(source):
    """A JSON source's text: UTF-8, and a byte that is no part of UTF-8 kept as the byte it is (surrogateescape) — a
    tool such as exiftool writes a file's name in the bytes the name has, which the reader gives back as those bytes."""
    return _bytes(source).decode('utf-8-sig', 'surrogateescape')


def _json(source, spec):
    try:
        data = _number_json(_named_text(source))
    except ValueError as e:
        raise Refused(f"not JSON: {e}") from None
    data = _at_path(data, (spec or {}).get('path'))
    items = data if isinstance(data, list) else [data] if isinstance(data, dict) else []
    for i, item in enumerate(items):
        if isinstance(item, dict):
            yield Record(item, at=f"record {i + 1}")


def _jsonl(source, spec):
    for n, line in enumerate(_named_text(source).split('\n'), 1):
        if line.strip():
            try:
                item = _number_json(line)
            except ValueError as e:
                raise Refused(f"line {n} is no JSON: {e}") from None
            if isinstance(item, dict):
                yield Record(item, at=f"line {n}")


def snapshot(path, pages=256, sleep=0.01):
    """A database another process commits to, copied into memory in steps: no long read holds up its writer."""
    src = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=60)
    mem = sqlite3.connect(':memory:')
    try:
        src.backup(mem, pages=pages, sleep=sleep)
    finally:
        src.close()
    return mem


def _sqlite(source, spec):
    spec = spec or {}
    table = spec.get('table')
    if not table or not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', str(table)):
        raise Refused("a database's records are the rows of a table its crosswalk names (`records: { table }`)")
    db = snapshot(source) if spec.get('live') else sqlite3.connect(f"file:{source}?mode=ro", uri=True, timeout=60)
    try:
        where, args = [], []
        for col, vals in (spec.get('where') or {}).items():
            if not re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', str(col)):
                raise Refused(f"{col!r} is no column")
            vals = vals if isinstance(vals, list) else [vals]
            where.append(f'"{col}" IN ({", ".join("?" * len(vals))})')
            args += [str(v) for v in vals]
        sql = f'SELECT * FROM "{table}"' + (f" WHERE {' AND '.join(where)}" if where else '')
        if spec.get('order'):
            sql += f' ORDER BY "{spec["order"]}"'
        cur = db.execute(sql, args)
        names = [d[0] for d in cur.description]
        for n, row in enumerate(cur, 1):
            yield Record({k: v for k, v in zip(names, row) if v is not None}, at=f"row {n}")
    finally:
        db.close()


def undeclared(raw, what='a record'):
    """The `xml` format's guard: a document that declares a document type or an entity is refused before it is parsed,
    so nothing in it is expanded, run or fetched."""
    if re.search(rb'<!(DOCTYPE|ENTITY)', raw if isinstance(raw, bytes) else str(raw).encode('utf-8'), re.I):
        raise Refused(f"it declares a document type or an entity: {what} is data, refused before it is parsed")


def _xml(source, spec):
    import xml.etree.ElementTree as ET
    raw = _bytes(source)
    undeclared(raw)
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as e:
        raise Refused(f"not XML: {e}") from None

    def local(tag):
        return tag.rsplit('}', 1)[-1]

    def as_record(el):
        out = {f"@{local(k)}": v for k, v in el.attrib.items()}
        for child in el:
            v = as_record(child)
            name = local(child.tag)
            if name in out:
                out[name] = out[name] if isinstance(out[name], list) else [out[name]]
                out[name].append(v)
            else:
                out[name] = v
        text = (el.text or '').strip()
        if text and not out:
            return text
        if text:
            out['#text'] = text
        return out
    path = [s for s in str((spec or {}).get('path') or '').split('/') if s]
    found = [root]
    for step in path:
        found = [c for el in found for c in el if local(c.tag) == step]
    for i, el in enumerate(found):
        r = as_record(el)
        yield Record(r if isinstance(r, dict) else {'#text': r}, at=f"element {i + 1}")


def read(fmt, source, records=None):
    """The records of `source` (a path, or the bytes) in the format `fmt`, as the crosswalk's `records` asks."""
    if fmt not in READ:
        raise Refused(f"the format {fmt!r} is read by none of this release's readers ({', '.join(READ)})")
    return READ[fmt](source, records)


def _dumps(node, indent=0):
    """JSON with each number as it was written."""
    pad = '  ' * (indent + 1)
    if isinstance(node, dict):
        if not node:
            return '{}'
        return '{\n' + ',\n'.join(f"{pad}{json.dumps(k, ensure_ascii=False)}: {_dumps(v, indent + 1)}"
                                  for k, v in node.items()) + '\n' + '  ' * indent + '}'
    if isinstance(node, list):
        if not node:
            return '[]'
        return '[\n' + ',\n'.join(pad + _dumps(v, indent + 1) for v in node) + '\n' + '  ' * indent + ']'
    if isinstance(node, Decimal):
        return str(node)
    return json.dumps(node, ensure_ascii=False)


def cell(c):
    """A cell a spreadsheet would read as a formula (=, +, -, @, a tab or a return first) is written as text, a quote
    before it; a number stays a number (the csv format's guard, for every CSV daftar writes)."""
    s = '' if c is None else str(c)
    if s[:1] in ('=', '+', '-', '@', '\t', '\r') and not re.fullmatch(r'[-+]?\d+(\.\d+)?', s):
        return "'" + s
    return s


def _flat_fields(records, fields):
    cols = list(fields or [])
    for r in records:
        for k in r:
            if k not in cols:
                cols.append(k)
    return [c for c in cols if any(c in r for r in records)]


def ics_escape(s):
    return str(s).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def ics_time(at):
    """A gregorian-civil position as an iCalendar DATE, or DATE-TIME — in UTC where its offset is written, floating where
    none is: (its VALUE parameter, its text), or None where it is not one."""
    import datetime
    m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2})(?::(\d{2}))?(Z|[+-]\d{2}:\d{2})?)?", str(at).strip())
    if not m:
        return None
    y, mo, d, h, mi, se, off = m.groups()
    if h is None:
        return ("VALUE=DATE", y + mo + d)
    if not off:
        return ("", "%s%s%sT%s%s%s" % (y, mo, d, h, mi, se or "00"))
    t = datetime.datetime.fromisoformat("%s-%s-%sT%s:%s:%s%s" % (y, mo, d, h, mi, se or "00", "+00:00" if off == "Z" else off))
    return ("", t.astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ"))


def ics_duration(secs):
    secs = int(secs)
    d, r = divmod(secs, 86400)
    h, r = divmod(r, 3600)
    m, s = divmod(r, 60)
    t = "".join(x for x in ("%dH" % h if h else "", "%dM" % m if m else "", "%dS" % s if s else "") if x)
    return "P" + ("%dD" % d if d else "") + ("T" + t if t else ("" if d else "T0S"))


def _ics(records, stamp=None):
    """RFC 5545: one VEVENT a record {uid, start, summary, notice?}, a VALARM `notice` seconds before where one is
    given; a record whose start is no position of the civil calendar is left out."""
    import datetime
    stamp = stamp or datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//daftar//view ics//EN", "CALSCALE:GREGORIAN"]
    for r in records:
        t = ics_time(r.get('start'))
        if t is None:
            continue
        kind, when = t
        lines += ["BEGIN:VEVENT", "UID:" + str(r.get('uid')), "DTSTAMP:" + stamp,
                  "DTSTART%s:%s" % (";" + kind if kind else "", when), "SUMMARY:" + ics_escape(r.get('summary', ''))]
        if r.get('notice'):
            lines += ["BEGIN:VALARM", "ACTION:DISPLAY", "DESCRIPTION:" + ics_escape(r.get('summary', '')),
                      "TRIGGER:-" + ics_duration(r['notice']), "END:VALARM"]
        lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def write(fmt, records, fields=None, **opts):
    """`records` written in the format `fmt`: text, or bytes for a database."""
    records = list(records)
    if fmt == 'ics':
        return _ics(records, stamp=opts.get('stamp'))
    if fmt == 'json':
        return _dumps(records) + '\n'
    if fmt == 'jsonl':
        return ''.join(json.dumps(r, ensure_ascii=False, default=str, sort_keys=False) + '\n' for r in records)
    if fmt == 'csv':
        cols = _flat_fields(records, fields)
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator='\n')
        w.writerow([cell(c) for c in cols])
        for r in records:
            w.writerow([cell(r.get(c)) for c in cols])
        return buf.getvalue()
    if fmt == 'tsv':
        import parse as dmparse
        cols = _flat_fields(records, fields)
        return dmparse.table_write(cols, [[('-' if r.get(c) in (None, '') else r.get(c)) for c in cols] for r in records])
    if fmt == 'sqlite':
        import tempfile
        cols = _flat_fields(records, fields)
        fd, tmp = tempfile.mkstemp(suffix='.sqlite')
        os.close(fd)
        try:
            db = sqlite3.connect(tmp)
            db.execute(f"CREATE TABLE record ({', '.join(json.dumps(c) for c in cols)})")
            db.executemany(f"INSERT INTO record VALUES ({', '.join('?' * len(cols))})",
                           [[(str(r[c]) if isinstance(r.get(c), Decimal) else r.get(c)) for c in cols] for r in records])
            db.commit()
            db.close()
            with open(tmp, 'rb') as fh:
                return fh.read()
        finally:
            os.unlink(tmp)
    raise Refused(f"the format {fmt!r} is written by none of this release's writers ({', '.join(WRITE)})")


READ = {'tsv': _tsv, 'csv': _csv, 'json': _json, 'jsonl': _jsonl, 'sqlite': _sqlite, 'xml': _xml}
WRITE = ('tsv', 'csv', 'json', 'jsonl', 'sqlite', 'ics')
EXTENSIONS = {'.tsv': 'tsv', '.csv': 'csv', '.json': 'json', '.jsonl': 'jsonl', '.ndjson': 'jsonl', '.sqlite': 'sqlite',
              '.sqlite3': 'sqlite', '.db': 'sqlite', '.xml': 'xml'}


def format_of(path, allowed):
    """The format a source is in: the only one its crosswalk allows, or the one its name's extension says."""
    allowed = [str(f) for f in (allowed if isinstance(allowed, list) else [allowed]) if f]
    if len(allowed) == 1:
        return allowed[0]
    ext = os.path.splitext(str(path))[1].lower()
    if EXTENSIONS.get(ext) in allowed:
        return EXTENSIONS[ext]
    raise Refused(f"{path}: say its format (`--format`), one of {', '.join(allowed)}")


# ------------------------------------------------------------------------------------------------ the conversions
_EPOCHS = []


def clock_epochs():
    """The epochs a device's clock starts from (core/law/formats.yaml `clock_epochs`), read once."""
    if not _EPOCHS:
        from core import read
        law = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'law', 'formats.yaml')
        _EPOCHS.extend(r for r in (read.data(law) or {}).get('clock_epochs') or [] if isinstance(r, dict))
    return _EPOCHS


def moment_in(value, how):
    """(the law's position, a note or None) of a moment as a system writes it; (None, why) where it is none — and none
    where the device that wrote it never set its clock: a moment on, or within a month after, an epoch of
    `clock_epochs` (a PowerShot writes 1980-01-01 00:00 and the seconds since it was switched on)."""
    s = str(value).strip()
    if how in ('exif', 'quicktime', 'iso'):
        from core import groupings
        ep = groupings.unset_clock(s, clock_epochs())
        if ep:
            return None, f"{s!r} is a clock never set: it sits on the {ep} epoch (clock_epochs)"
    if how in ('exif', 'quicktime'):
        m = re.match(r'^(\d{4}):(\d{2}):(\d{2})[ T](\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2})?$', s)
        if not m or m.group(1) == '0000':
            return None, f"{s!r} is no moment as {'Exif' if how == 'exif' else 'QuickTime'} writes one"
        if how == 'quicktime' and not m.group(8):           # its header's time is UTC, as the format says
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}T{m.group(4)}:{m.group(5)}:{m.group(6)}+00:00", None
        day = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
        if not m.group(8):
            return day, "a clock with no offset: kept to its day"
        frac = (m.group(7) or '')[:4]                     # the law writes a moment to the millisecond at most
        return f"{day}T{m.group(4)}:{m.group(5)}:{m.group(6)}{frac}{m.group(8)}", None
    if how == 'epoch':
        import datetime
        try:
            t = datetime.datetime.fromtimestamp(float(s), datetime.timezone.utc)
        except (ValueError, OverflowError, OSError):
            return None, f"{s!r} is no count of seconds"
        from core import groupings
        ep = groupings.unset_clock(t.strftime('%Y-%m-%dT%H:%M:%S'), clock_epochs())
        if ep:
            return None, f"{s!r} is a clock never set: it sits on the {ep} epoch (clock_epochs)"
        return t.strftime('%Y-%m-%dT%H:%M:%S+00:00'), None
    if how == 'iso':
        return s, None
    return None, f"{how!r} is no way a moment is written here (exif, quicktime, epoch, iso)"


def moment_out(value, how):
    s = str(value)
    if how == 'exif':
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})(?:[T ](\d{2}):(\d{2}):(\d{2})(\.\d+)?(Z|[+-]\d{2}:\d{2}))?$', s)
        if not m:
            return None
        if not m.group(4):
            return f"{m.group(1)}:{m.group(2)}:{m.group(3)}"
        return f"{m.group(1)}:{m.group(2)}:{m.group(3)} {m.group(4)}:{m.group(5)}:{m.group(6)}{m.group(7) or ''}{m.group(8)}"
    return s


def conversion(spec):
    """(its name, its argument, its options) of a field's `as`: `escaped`, or `{ moment: exif }`."""
    if isinstance(spec, str):
        return spec, None, {}
    if isinstance(spec, dict):
        opts = {k: v for k, v in spec.items() if k in ('hint', 'none')}
        name = next(k for k in spec if k not in ('hint', 'none'))
        return name, spec[name], opts
    return None, None, {}


# ------------------------------------------------------------------------------------------------ conventions
def folder_id(volume, path):
    """A folder's id, as the catalogue mints it: `d-` and 16 hexadecimal digits of the SHA-256 of the volume's id, a zero
    byte and its path (bytes)."""
    if isinstance(path, str):
        path = os.fsencode(path)
    return 'd-' + hashlib.sha256(volume.encode() + b'\0' + bytes(path)).hexdigest()[:16]


def content_id(blake3):
    return 'c-' + str(blake3)[:24]


def _path_bytes(p):
    return bytes(p) if isinstance(p, (bytes, bytearray, memoryview)) else os.fsencode(str(p))


def local_moment(t):
    """A count of seconds as the moment it was on this machine's clock, with its offset: how a copier writes when."""
    if t is None:
        return None
    import time
    s = time.strftime('%Y-%m-%dT%H:%M:%S%z', time.localtime(float(t)))
    return s[:-2] + ':' + s[-2:]
