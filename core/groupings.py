"""groupings — patterns, classes and their previews, one engine (core 2.15; MODEL.md, Groupings).

A name pattern, a class and a preview are one thing seen three ways: a GROUPING is a reading that gathers members by a
rule, derived and defeasible, read each time and never written; its MEMBERS, with what is set apart from it; and its
LINE, one line in place of a thousand names. This module is the engine the readings call (bin/reckon.py's `fit`,
`inherit` and `shared`, bin/group.py over a store, the gate's lines). The standard library alone; offline; the same
answer every time — no clock, no randomness, no order but the sort.

  Templates   parse(text, slots) and Template(text, …).match(name): a template is literal text and slots,
              `{<slot>}` or `{<slot>:<width or form>}`, each slot a row of core/law/lines.yaml `slots`; nothing in it is
              evaluated. A name the world gives is read with its digits of any script as ASCII digits, normalised here,
              at the boundary; a date is a day its calendar has, asked of bin/cal.py, never guessed.
  Mining      shape(name), mine(names): a name the registry does not know is cut into runs — a hexadecimal run of
              twelve or more holding a letter and a digit, decimal digits, letters of any script, each other character —
              and names of one shape make a template, literal where every member agrees, a slot where they vary.
  Fitting     fit(items, rows, …): each item by the most specific row its text fits (more literal characters, then
              fewer slots, then the code's order; its `within` and `beside` met), else by its mined shape; each group
              with its template and what its slots hold — a counter's first, last and the positions nobody holds.
  Classes     inherit(being, …): said, else inherited from the nearest whole (unless said nearer, set apart by an
              `apart` code, or not fitting its whole), else suggested — each code with where it came from.
  Lines       line(group, fields, …): a group's fields in the order its grouping names.
  Clocks      unset_clock(moment, epochs): a moment a device writes on the epoch its clock counts from (core/law/
              formats.yaml `clock_epochs`) is a clock never set, no moment."""
import datetime
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
import cal  # noqa: E402 — daftar's calendars, converted through the day

SLOT = re.compile(r'\{([a-z]+)(?::([A-Za-z0-9._-]+))?\}')
EXT = re.compile(r'\.([^\W_]{1,8})$')
HEXRUN = re.compile(r'[0-9A-Fa-f]{12,}')
TOKEN = re.compile(r'(\d+)|([^\W\d_]+)|(.)', re.S)
# THE ERA a mined date is read in: a run of digits is a date only where its day lies in it, in whatever calendar it is
# read. Wide on purpose, and fixed, so that the same names give the same templates on any day they are read.
ERA = (datetime.date(1900, 1, 1).toordinal(), datetime.date(2100, 12, 31).toordinal())
# What a slot matches as the engine reads it: the law's ASCII patterns (core/law/lines.yaml `slots.matches`) where it
# has one, and letters of any script where the law says so in words — a world's names are not ASCII.
ENGINE = {'word': r'[^\W\d_]+', 'extension': r'[^\W_]{1,8}', 'text': r'.+?'}
DATE_FORMS = {'yyyymmdd': r'\d{8}', 'yymmdd': r'\d{6}', 'yyyy-mm-dd': r'\d{4}-\d{2}-\d{2}',
              'yyyy_mm_dd': r'\d{4}_\d{2}_\d{2}', 'yyyy.mm.dd': r'\d{4}\.\d{2}\.\d{2}'}
TIME_FORMS = {'hhmmss': r'\d{6}', 'hhmm': r'\d{4}', 'hh-mm-ss': r'\d{2}-\d{2}-\d{2}', 'hh.mm.ss': r'\d{2}\.\d{2}\.\d{2}',
              'hh_mm_ss': r'\d{2}_\d{2}_\d{2}'}


class TemplateError(ValueError):
    pass


def ascii_digits(s):
    """`s` with every decimal digit of another script written as its ASCII digit: `IMG_۷۳۷۸` is read as `IMG_7378`."""
    return ''.join(str(unicodedata.digit(c)) if not c.isascii() and c.isdigit() else c for c in s)


# ------------------------------------------------------------------------------------------------ calendars, asked
def _prefix(system_row):
    """How a system writes a position before its digits — `persian:` — read from its pattern; '' for a calendar
    written bare (gregorian-civil)."""
    m = re.match(r'^\^\(?([a-z][a-z-]*:)', str((system_row or {}).get('pattern') or ''))
    return m.group(1) if m else ''


def is_day(y, m, d, system, systems):
    """True when the calendar `system` (a row of `systems`, reckoned by rule) has the day y-m-d, and the day lies in
    ERA. Asked of bin/cal.py: a day it does not have is refused there, never moved."""
    row = systems.get(system) or {}
    if row.get('reckoning') != 'arithmetic' or row.get('dimension') != 'time':
        return False
    try:
        n = cal.to_day(f"{_prefix(row)}{y:04d}-{m:02d}-{d:02d}")
    except Exception:          # noqa: BLE001 — ValueError for a day it has not, NotByRule, a year it cannot reach
        return False
    return ERA[0] <= n <= ERA[1]


def _ymd(value, form, system):
    if form == 'yyyymmdd':
        return int(value[:4]), int(value[4:6]), int(value[6:8])
    if form == 'yymmdd':
        yy = int(value[:2])
        base = 1300 if system == 'persian-calendar' else (1900 if yy >= 50 else 2000)
        return base + yy, int(value[2:4]), int(value[4:6])
    y, m, d = re.split(r'\D', value)
    return int(y), int(m), int(d)


def calendars_of(values, form, systems):
    """The calendars, of those `systems` reckons by rule, in which every value is a day: none chosen where two fit."""
    out = []
    for name in sorted(systems):
        try:
            if all(is_day(*_ymd(v, form, name), name, systems) for v in values):
                out.append(name)
        except (ValueError, IndexError):
            continue
    return out


def is_time(values, form):
    for v in values:
        p = [int(x) for x in re.findall(r'\d\d', v)]
        if not (p[0] < 24 and p[1] < 60 and (len(p) < 3 or p[2] < 61)):
            return False
    return True


# ------------------------------------------------------------------------------------------------ templates
def parse(text, slots):
    """[('lit', text) | ('slot', slot, arg)] of a template, its slots rows of `slots` ({slot: row}); TemplateError for
    an unknown slot, a width it requires and lacks or takes and is not, a form it does not have, a second `text`, an
    `extension` not at the end after a dot, or a brace no slot closes."""
    out, i, texts = [], 0, 0
    body = text.replace('{{', '\0').replace('}}', '\1')
    for m in SLOT.finditer(body):
        lit = body[i:m.start()]
        if '{' in lit or '}' in lit:
            raise TemplateError(f"{text!r}: a brace no slot closes (`{{{{` and `}}}}` write one)")
        if lit:
            out.append(('lit', lit.replace('\0', '{').replace('\1', '}')))
        name, arg = m.group(1), m.group(2)
        row = slots.get(name)
        if row is None:
            raise TemplateError(f"{text!r}: `{name}` is no slot — one of {', '.join(sorted(slots))}")
        forms = row.get('forms') if isinstance(row.get('forms'), list) else None
        if forms is not None:
            if arg not in forms:
                raise TemplateError(f"{text!r}: a {name} slot names its form, one of {', '.join(forms)}")
        elif arg is not None:
            if row.get('width') not in ('allowed', 'required'):
                raise TemplateError(f"{text!r}: a {name} slot takes no width")
            if not arg.isdigit() or arg.startswith('0'):
                raise TemplateError(f"{text!r}: a width is a whole number, `{{{name}:4}}`")
        elif row.get('width') == 'required':
            raise TemplateError(f"{text!r}: a {name} slot names its width, `{{{name}:16}}`")
        if name == 'text':
            texts += 1
            if texts > 1:
                raise TemplateError(f"{text!r}: one `text` slot a template, so that it still says what is fixed")
        out.append(('slot', name, arg))
        i = m.end()
    lit = body[i:]
    if '{' in lit or '}' in lit:
        raise TemplateError(f"{text!r}: a brace no slot closes (`{{{{` and `}}}}` write one)")
    if lit:
        out.append(('lit', lit.replace('\0', '{').replace('\1', '}')))
    for k, part in enumerate(out):
        if part[0] == 'slot' and part[1] == 'extension':
            if k != len(out) - 1 or k == 0 or out[k - 1][0] != 'lit' or not out[k - 1][1].endswith('.'):
                raise TemplateError(f"{text!r}: an `extension` slot ends a template, after a dot")
    return out


class Template:
    """A template compiled for matching. `match(text)` gives {slot: value} — a second slot of one name as `<slot>2`
    — or None; a date is kept only where its calendar has the day."""

    def __init__(self, text, slots, case='any', calendar=None, extensions=None, systems=None):
        self.text, self.calendar, self.systems = text, calendar, systems or {}
        self.parts = parse(text, slots)
        self.extensions = {e.lower() for e in extensions or []}
        rx, self.slots = [], []
        for part in self.parts:
            if part[0] == 'lit':
                rx.append(re.escape(part[1]))
                continue
            _, name, arg = part
            gid = f"s{len(self.slots)}"
            self.slots.append((gid, name, arg))
            if name == 'date':
                pat = DATE_FORMS[arg]
            elif name == 'time':
                pat = TIME_FORMS[arg]
            else:
                pat = ENGINE.get(name) or str(slots[name].get('matches'))
                if arg and name in ('counter', 'number'):
                    pat = r'\d{%s}' % arg
                elif arg and name == 'hex':
                    pat = r'[0-9A-Fa-f]{%s}' % arg
                elif arg and name == 'alnum':
                    pat = r'[A-Za-z0-9_]{%s}' % arg
                elif arg and name == 'word':
                    pat = r'[^\W\d_]{%s}' % arg
            rx.append(f'(?P<{gid}>{pat})')
        self.rx = re.compile('^' + ''.join(rx) + '$', 0 if case == 'exact' else re.I)
        self.literal = sum(len(p[1]) for p in self.parts if p[0] == 'lit')
        self.width = len(self.slots)

    def match(self, text):
        m = self.rx.match(ascii_digits(text))
        if not m:
            return None
        out = {}
        for gid, name, arg in self.slots:
            v = m.group(gid)
            if name == 'date':
                cals = [self.calendar] if self.calendar else sorted(self.systems)
                if not any(_day_of(v, arg, c, self.systems) for c in cals):
                    return None
            elif name == 'time' and not is_time([v], arg):
                return None
            elif name == 'extension' and self.extensions and v.lower() not in self.extensions:
                return None
            key = name if name not in out else f"{name}{sum(1 for k in out if k.startswith(name)) + 1}"
            out[key] = v
        return out


def _day_of(v, form, system, systems):
    try:
        return is_day(*_ymd(v, form, system), system, systems)
    except (ValueError, IndexError):
        return False


# ------------------------------------------------------------------------------------------------ mining
def split_ext(name):
    """(stem, extension): the extension the last dot begins, 1–8 letters or digits, lowercased; none on a name that is
    only a dot and an extension (`.gitignore`)."""
    m = EXT.search(name)
    if m and m.start() > 0:
        return name[:m.start()], m.group(1).lower()
    return name, ''


def tokens(stem):
    """[(kind, text)]: X a hexadecimal run of twelve or more holding a letter and a digit, D decimal digits (read as
    ASCII), L letters of any script, S each other character alone."""
    out, i = [], 0
    for m in HEXRUN.finditer(stem):
        h = m.group(0)
        if not (any(c.isdigit() for c in h) and any(c.isalpha() for c in h)):
            continue
        out += _plain(stem[i:m.start()])
        out.append(('X', h))
        i = m.end()
    return out + _plain(stem[i:])


def _plain(s):
    out = []
    for m in TOKEN.finditer(s):
        d, l, o = m.groups()
        out.append(('D', ascii_digits(d)) if d else ('L', l) if l else ('S', o))
    return out


def shape(name):
    """(the shape's key, the extension): letters and other characters kept without case, digit and hex runs as their
    width — names of one shape are siblings a template may cover."""
    stem, ext = split_ext(name)
    return tuple((k, t.casefold()) if k in 'LS' else (k, len(t)) for k, t in tokens(stem)), ext


def _lit(s):
    return s.replace('{', '{{').replace('}', '}}')


def mine(names, systems, fill=0.5):
    """The template names of ONE shape fit — literal where every member agrees, a slot where they vary — with what
    each slot holds; None where they are not of one shape. A digit run is a date where every value is a day of one
    calendar or more (`calendars`, all said), a time where every value is a time, a counter where the values are
    distinct and fill half or more of their span, else a number. Letters that vary are a word."""
    keys, toks, exts = set(), [], set()
    for n in names:
        stem, ext = split_ext(n)
        t = tokens(stem)
        keys.add(tuple((k, x.casefold()) if k in 'LS' else (k, len(x)) for k, x in t))
        toks.append(t)
        exts.add(ext)
    if len(keys) != 1:
        return None
    key = next(iter(keys))
    cols = [[t[i][1] for t in toks] for i in range(len(key))]
    parts, slots, i = [], [], 0
    while i < len(key):
        kind = key[i][0]
        col = cols[i]
        if kind == 'D' and i + 4 < len(key) and key[i + 1][0] == 'S' and key[i + 3] == key[i + 1] \
                and key[i + 2] == ('D', 2) and key[i + 4] == ('D', 2) and key[i][1] in (4, 2):
            sep = key[i + 1][1]
            if key[i][1] == 4 and f'yyyy{sep}mm{sep}dd' in DATE_FORMS:
                form = f'yyyy{sep}mm{sep}dd'
                vals = [f'{a}{sep}{b}{sep}{c}' for a, b, c in zip(col, cols[i + 2], cols[i + 4])]
                cals = calendars_of(vals, form, systems)
                if cals:
                    parts.append(f'{{date:{form}}}')
                    slots.append({'slot': 'date', 'form': form, 'calendars': cals, 'values': sorted(set(vals))})
                    i += 5
                    continue
            if key[i][1] == 2 and f'hh{sep}mm{sep}ss' in TIME_FORMS:
                form = f'hh{sep}mm{sep}ss'
                vals = [f'{a}{sep}{b}{sep}{c}' for a, b, c in zip(col, cols[i + 2], cols[i + 4])]
                if is_time(vals, form):
                    parts.append(f'{{time:{form}}}')
                    slots.append({'slot': 'time', 'form': form, 'values': sorted(set(vals))})
                    i += 5
                    continue
        if kind in 'LS':
            if len({c.casefold() for c in col}) == 1:
                parts.append(_lit(col[0]))
            else:
                parts.append('{word}')
                slots.append({'slot': 'word', 'values': sorted(set(col))})
        elif kind == 'X':
            parts.append(f'{{hex:{key[i][1]}}}')
            slots.append({'slot': 'hex', 'width': key[i][1]})
        else:
            w = key[i][1]
            if len(set(col)) == 1:
                parts.append(col[0])
            elif w in (8, 6) and calendars_of(col, 'yyyymmdd' if w == 8 else 'yymmdd', systems):
                form = 'yyyymmdd' if w == 8 else 'yymmdd'
                parts.append(f'{{date:{form}}}')
                slots.append({'slot': 'date', 'form': form, 'calendars': calendars_of(col, form, systems),
                              'values': sorted(set(col))})
            elif w == 6 and is_time(col, 'hhmmss'):
                parts.append('{time:hhmmss}')
                slots.append({'slot': 'time', 'form': 'hhmmss', 'values': sorted(set(col))})
            else:
                nums = sorted({int(c) for c in col})
                span = nums[-1] - nums[0] + 1
                if len(nums) == len(col) and len(nums) >= 2 and len(nums) / span >= fill:
                    parts.append(f'{{counter:{w}}}')
                    slots.append(counted('counter', w, nums))
                else:
                    parts.append(f'{{number:{w}}}')
                    slots.append({'slot': 'number', 'width': w})
        i += 1
    text = ''.join(parts) + ('.{extension}' if exts - {''} else '')
    return {'template': text, 'slots': slots, 'extensions': sorted(e for e in exts if e), 'count': len(names)}


def counted(slot, width, nums):
    """What a counter holds: its first and last, how many, and the positions between nobody holds (each run of them as
    [first, last])."""
    gaps, prev = [], None
    for n in nums:
        if prev is not None and n > prev + 1:
            gaps.append([prev + 1, n - 1])
        prev = n
    return {'slot': slot, 'width': width, 'first': nums[0], 'last': nums[-1], 'count': len(nums),
            'missing': sum(b - a + 1 for a, b in gaps), 'gaps': gaps}


# ------------------------------------------------------------------------------------------------ fitting
class Row:
    """A pattern row (the knowledge profile's form `pattern`), compiled."""

    def __init__(self, scheme, row, slots, systems, order):
        self.scheme, self.code, self.order = scheme, str(row.get('code')), order
        self.template = Template(str(row['template']), slots, case=row.get('case') or 'any',
                                 calendar=row.get('calendar') or None,
                                 extensions=str(row.get('extensions') or '').split(), systems=systems)
        self.reads = row.get('reads') or None
        self.suggests = str(row.get('suggests') or '').split()
        self.grouping = row.get('grouping') or None
        self.marks = row.get('marks') or None
        self.within = row.get('within') or None
        self.beside = row.get('beside') or None

    @property
    def coding(self):
        return f"{self.scheme}:{self.code}"

    def key(self):
        return (-self.template.literal, self.template.width, self.order)


def rows_of(schemes, slots, systems):
    """[Row] of every pattern row of `schemes` — [(scheme, rows)] in the order they are read, the garden's own first —
    most specific first. A row whose template is not in its form is left out here; the law's check names it."""
    out, order = [], 0
    for scheme, rows in schemes:
        for r in rows:
            if not r.get('template'):
                continue
            try:
                out.append(Row(scheme, r, slots, systems, order))
            except TemplateError:
                continue
            order += 1
    return sorted(out, key=Row.key)


def fit(items, rows, systems, reads=None, holds=None, beside=None, mine_rest=True):
    """Groups of `items` — [(key, text, container)] — by the most specific row each text fits, else by its mined
    shape within its container. `holds(key, coding)` says whether one of the item's wholes holds a code (a row's
    `within`); `beside(key, coding)` whether most of its siblings do (`beside`); `reads`, the field a row must read
    for these texts (rows that read another are not tried). Each group: {template, code (None when mined), container,
    members [keys], texts, slots, suggests}."""
    groups, rest = {}, {}
    for key, text, container in items:
        text = str(text)
        hit = None
        for r in rows:
            if reads is not None and (r.reads or 'as') != reads:
                continue
            if r.within and not (holds and holds(key, r.within)):
                continue
            if r.beside and not (beside and beside(key, r.beside)):
                continue
            got = r.template.match(text)
            if got is not None:
                hit = (r, got)
                break
        if hit:
            g = groups.setdefault((hit[0].coding, container), {'template': hit[0].template.text,
                                                              'code': hit[0].coding, 'container': container,
                                                              'members': [], 'texts': [], 'values': [],
                                                              'suggests': hit[0].suggests,
                                                              'grouping': hit[0].grouping})
            g['members'].append(key)
            g['texts'].append(text)
            g['values'].append(hit[1])
        else:
            rest.setdefault((shape(text), container), []).append((key, text))
    out = [_summed(g) for _, g in sorted(groups.items(), key=lambda kv: (str(kv[0][1]), kv[0][0]))]
    for (shp, container), kts in sorted(rest.items(), key=lambda kv: (str(kv[0][1]), str(kv[0][0]))):
        texts = [t for _, t in kts]
        m = mine(texts, systems) if mine_rest and len(texts) > 1 else None
        out.append({'template': m['template'] if m else _lit(texts[0]), 'code': None, 'container': container,
                    'members': [k for k, _ in kts], 'texts': texts, 'slots': m['slots'] if m else [],
                    'suggests': [], 'grouping': None})
    return out


def _summed(g):
    """A matched group's slots summed over its members: a counter's run and gaps, a date's or time's extent, a word's
    values."""
    slots = []
    for name in sorted({k for v in g['values'] for k in v}, key=lambda k: list(g['values'][0]).index(k)
                       if k in g['values'][0] else 99):
        vals = [v[name] for v in g['values'] if name in v]
        base = re.sub(r'\d+$', '', name)
        if base == 'counter':
            nums = sorted({int(x) for x in vals})
            slots.append(counted('counter', len(vals[0]), nums))
        elif base in ('date', 'time'):
            slots.append({'slot': base, 'first': min(vals), 'last': max(vals), 'values': sorted(set(vals))})
        elif base in ('word', 'alnum', 'extension'):
            slots.append({'slot': base, 'values': sorted({x.lower() if base == 'extension' else x for x in vals})})
    out = dict(g)
    del out['values']
    out['slots'] = slots
    return out


# ------------------------------------------------------------------------------------------------ lines
def ranged(group):
    """The group's template with its counter's first and last, or its date's extent, in place of the slot:
    `IMG_7378–7395.CR2`; the extension in place of its slot where every member has one."""
    t = group['template']
    for s in group.get('slots') or []:
        if s['slot'] == 'counter' and 'first' in s:
            w = s.get('width') or 1
            span = f"{s['first']:0{w}d}" if s['first'] == s['last'] else f"{s['first']:0{w}d}–{s['last']:0{w}d}"
            t = re.sub(r'\{counter(?::\d+)?\}', span, t, count=1)
        elif s['slot'] == 'date' and s.get('values'):
            v = sorted(s['values'])
            t = re.sub(r'\{date:[^}]+\}', v[0] if v[0] == v[-1] else f"{v[0]}–{v[-1]}", t, count=1)

    if '{extension}' in t:                 # as the members write it, where they agree without case
        seen = {}
        for x in group.get('texts') or []:
            m = EXT.search(x)
            if m and m.start() > 0:
                seen.setdefault(m.group(1).lower(), m.group(1))
        exts = [seen[k] for k in sorted(seen)]
        if len(exts) == 1:
            t = t.replace('{extension}', exts[0], 1)
        elif exts:
            t = t.replace('{extension}', '{' + ','.join(exts[:4]) + ('…' if len(exts) > 4 else '') + '}', 1)
    return t.replace('{{', '{').replace('}}', '}')


def line(group, fields, writers=None):
    """The group's one line: each field of `fields` (a grouping's `line`) in order, written by `writers[<field>]` where
    the caller gives one (a position in the reader's calendar, a being by its title), its own text else; a field the
    group cannot say is left out, never written empty."""
    writers = writers or {}
    out = []
    for f in fields:
        name, _, path = str(f).partition(':')
        if name in writers:
            v = writers[name](group, path)
        elif name == 'range':
            v = ranged(group)
        elif name == 'count':
            v = f"{len(group.get('members') or []):,}"
        elif name == 'missing':
            n = sum(s.get('missing') or 0 for s in group.get('slots') or [] if s['slot'] == 'counter')
            v = f"{n:,} missing" if n else None
        elif name == 'extent':
            ds = [s for s in group.get('slots') or [] if s['slot'] in ('date', 'time')]
            v = ' · '.join(s['first'] if s['first'] == s['last'] else f"{s['first']}–{s['last']}" for s in ds) or None
        elif name == 'values':
            ws = [s for s in group.get('slots') or [] if s['slot'] == 'word']
            v = ', '.join(ws[0]['values'][:4]) + ('…' if len(ws[0]['values']) > 4 else '') if ws else None
        elif name == 'code':
            v = group.get('code')
        elif name == 'apart':
            n = len(group.get('apart') or [])
            v = f"{n:,} set apart" if n else None
        else:
            v = group.get(name)
        if v not in (None, ''):
            out.append(str(v))
    return ' · '.join(out)


# ------------------------------------------------------------------------------------------------ classes
def inherit(being, said, wholes, suggested=None, apart=None, fits=None, scheme=None, limit=4096):
    """[(code, where it came from, through)] of `being` in one class scheme:
      said(b)       -> the codes said of b (a `classify` in a bean)
      wholes(b)     -> what b inherits from: its whole up `part`, and for a content each folder that holds it
      suggested(b)  -> the codes the patterns b's name fits suggest, of any scheme
      apart(code)   -> True for a code whose members inherit nothing (the form `class`, `apart`), of any scheme
      scheme        -> the scheme asked: a suggested code of it is the member's where nothing is said or inherited
      fits(b, w)    -> None when b fits the whole w, else why it is set apart (the grouping's `weighs`)
    Said, else inherited from the nearest wholes that hold a said code — a nearer said code stopping the walk, an `apart`
    code holding its subtree to itself, a member that does not fit set apart with why — else suggested. A being is
    visited once: `part` is free of cycles by rule `order`, and a store's cycle, which its check refuses, ends here."""
    own = list(said(being) or [])
    if own:
        return [(c, 'said', being) for c in own]
    sugg = list(suggested(being) or []) if suggested else []
    if apart and any(apart(c) for c in sugg):           # a program's tree, a dropping, another's code: of any scheme
        return [(None, f"set apart: {', '.join(c for c in sugg if apart(c))}", being)]
    out, seen, todo, hops = [], {being}, [(w, being) for w in wholes(being) or []], 0
    while todo and hops < limit:
        hops += 1
        w, child = todo.pop(0)
        if w in seen:
            continue
        seen.add(w)
        codes = list(said(w) or [])
        if codes:
            why = fits(being, w) if fits else None
            if why:
                out.append((None, f'set apart: {why}', w))
            else:
                out.extend((c, 'inherited', w) for c in codes)
            continue
        if apart and suggested and any(apart(c) for c in suggested(w) or []):
            out.append((None, 'set apart: inside a whole that keeps its own', w))
            continue
        todo.extend((x, w) for x in wholes(w) or [])
    got = [x for x in out if x[0] is not None]
    if got:
        return got
    mine = [c for c in sugg if not scheme or c.split(':', 1)[0] == scheme]
    if mine:
        return [(c, 'suggested', being) for c in mine]
    return [x for x in out if x[0] is None]


def cycle(edges):
    """A cycle among a scheme's own relations — {code: [codes it is part of]} — as a list of codes, or None."""
    state = {}
    for start in sorted(edges):
        if state.get(start):
            continue
        stack = [(start, iter(edges.get(start) or []))]
        path, state[start] = [start], 1
        while stack:
            node, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop()
                path.pop()
                state[node] = 2
                continue
            if state.get(nxt) == 1:
                return path[path.index(nxt):] + [nxt]
            if not state.get(nxt):
                state[nxt] = 1
                path.append(nxt)
                stack.append((nxt, iter(edges.get(nxt) or [])))
    return None


# ------------------------------------------------------------------------------------------------ clocks
def unset_clock(moment, epochs):
    """The epoch a moment sits on when the device that wrote it never set its clock — the row of `clock_epochs` whose
    `written` it is, or within whose `window` after its `at` it falls — else None. `moment` as a device writes it
    (`1980:01:01 00:00:10`, `1980-01-01T00:00:10Z`)."""
    m = str(moment or '').strip()
    digits = re.sub(r'\D', '', m)
    if digits and set(digits) == {'0'}:
        return next((e['epoch'] for e in epochs if e.get('written')), 'zero')
    d = re.match(r'^(-?\d{4})[:-](\d{2})[:-](\d{2})', m)
    if not d:
        return None
    try:
        day = datetime.date(int(d[1]), int(d[2]), int(d[3])).toordinal()
    except ValueError:
        return None
    best = None                         # of two epochs whose windows hold it, the nearest before it names it
    for e in epochs:
        at = re.match(r'^(\d{4})-(\d{2})-(\d{2})', str(e.get('at') or ''))
        w = e.get('window') or {}
        if not at:
            continue
        start = datetime.date(int(at[1]), int(at[2]), int(at[3])).toordinal()
        days = int(w.get('count') or 0) if str(w.get('unit')) == 'd' else 0
        if start <= day <= start + days and (best is None or start > best[0]):
            best = (start, e['epoch'])
    return best[1] if best else None
