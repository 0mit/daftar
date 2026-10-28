"""odoo_rpc — daftard's answers to the calls Odoo's own web client makes (design §10.2): its search, its views, its
groups, over records the garden gives — never a second store.

THE RECORDS are a provider's: `records(model)` gives each record of a model as a dict — `id`, and each field's value as
Odoo's client reads it (a many2one as [id, display name], a x2many as a list of ids, a date as 'YYYY-MM-DD', False for
none). daftard's provider reads them from the garden through the law's crosswalk of that model (P5.3); what the garden
does not say, no record has. THE VIEWS are the series' own, captured (importers/odoo/views.py).

EVERY DOMAIN IS ANDED WITH THE READER'S GRANTS: the provider gives only records the reader may read (closed by
default), and the client's domain narrows that, never widens it. SUMS ARE EXACT: a group's aggregate is summed as a
fraction and given to the client as the nearest number at the end.

The domain language is Odoo's (odoo/osv/expression.py): prefix `&`, `|`, `!`, an implicit `&` between terms, leaves
`[path, operator, value]` with dotted paths through relations, and the operators =, !=, <, <=, >, >=, =?, like,
not like, ilike, not ilike, =like, =ilike, in, not in, child_of, parent_of, any, not any; the leaves (1, '=', 1) and
(0, '=', 1). Records with `active` False are left out unless the domain names `active` or the context says
`active_test: False`.
"""
import re
from fractions import Fraction

TRUE_LEAF, FALSE_LEAF = (1, '=', 1), (0, '=', 1)


class Unsupported(Exception):
    """A call or an operator this answerer does not take: said, never guessed."""


class Denied(Exception):
    """A call Odoo itself refuses (its AccessError), refused here as Odoo refuses it."""


# ------------------------------------------------------------------------------------------------ values

def _id(v):
    """The id a relational value holds: [id, name] → id; id → id; False → False."""
    if isinstance(v, (list, tuple)) and v and not isinstance(v[0], (list, tuple)):
        return v[0] if len(v) == 2 and isinstance(v[1], str) else v
    return v


def _name(v):
    return v[1] if isinstance(v, (list, tuple)) and len(v) == 2 and isinstance(v[1], str) else v


def _like(pattern, text, ci):
    """SQL LIKE: % any run, _ any one character."""
    if text is False or text is None:
        return False
    rx = '^' + ''.join('.*' if c == '%' else '.' if c == '_' else re.escape(c) for c in str(pattern)) + '$'
    return re.match(rx, str(text), re.I | re.S if ci else re.S) is not None


# ------------------------------------------------------------------------------------------------ domains

def normalize(domain):
    """A domain with every implicit `&` written: prefix form, one tree."""
    domain = [tuple(x) if isinstance(x, list) else x for x in (domain or [])]
    if not domain:
        return [TRUE_LEAF]
    out, expected = [], 1
    for t in domain:
        if expected == 0:
            out.insert(0, '&')
            expected = 1
        if t in ('&', '|'):
            expected += 1
        elif t == '!':
            pass
        else:
            expected -= 1
        out.append(t)
    return out


class Domain:
    """A domain read once, evaluated on records. `follow(model, field, value)` gives the related records a dotted path
    reaches (for many2one, the record; for x2many, the records); `fields(model)` describes a model's fields."""

    def __init__(self, domain, model, fields, follow, context=None, hierarchy=None):
        self.tree, self.model, self.fields, self.follow = normalize(domain), model, fields, follow
        self.context, self.hierarchy = context or {}, hierarchy

    def names_active(self):
        return any(isinstance(t, tuple) and str(t[0]).split('.')[0] == 'active' for t in self.tree)

    def __call__(self, rec):
        pos = [0]

        def walk():
            t = self.tree[pos[0]]
            pos[0] += 1
            if t == '&':
                a, b = walk(), walk()
                return a and b
            if t == '|':
                a, b = walk(), walk()
                return a or b
            if t == '!':
                return not walk()
            return self.leaf(self.model, rec, t)
        return walk()

    def leaf(self, model, rec, leaf):
        if leaf == TRUE_LEAF:
            return True
        if leaf == FALSE_LEAF:
            return False
        if len(leaf) != 3:
            raise Unsupported(f'a leaf of {len(leaf)} parts: {leaf!r}')
        path, op, value = leaf
        head, _, rest = str(path).partition('.')
        desc = (self.fields(model) or {}).get(head)
        if desc is None and head != 'id':
            raise Unsupported(f'{model} has no field {head!r}')
        v = rec.get(head, False)
        ftype = (desc or {}).get('type', 'integer')
        if rest or op in ('any', 'not any'):
            if ftype not in ('many2one', 'one2many', 'many2many'):
                raise Unsupported(f'{model}.{head} is no relation to follow')
            related = self.follow(model, head, v)
            sub = rest and [(rest, op, value)] or (value if isinstance(value, list) else [])
            target = desc.get('relation')
            inner = Domain(sub, target, self.fields, self.follow, self.context, self.hierarchy)
            hit = any(inner(r) for r in related)
            return (not hit) if op == 'not any' else hit
        if op in ('child_of', 'parent_of'):         # the records under (or over) those named, along the model's parent
            target = model if head == 'id' else (desc or {}).get('relation')
            if not target or self.hierarchy is None:
                raise Unsupported(f'{op} on {model}.{head}')
            return compare(v, 'in', self.hierarchy(target, value, op), ftype)
        return compare(v, op, value, ftype)


def compare(v, op, value, ftype):
    """One leaf on one value, as Odoo's SQL would decide it."""
    relational = ftype in ('many2one', 'one2many', 'many2many')
    if ftype == 'many2one':
        if op in ('like', 'not like', 'ilike', 'not ilike', '=like', '=ilike') or (
                op in ('=', '!=') and isinstance(value, str)):
            v = _name(v)
        else:
            v = _id(v)
    if ftype in ('one2many', 'many2many'):
        ids = list(v or [])
        if op in ('=', '!=') and value is False:
            return (not ids) if op == '=' else bool(ids)
        if op in ('in', 'not in', '=', '!='):
            want = set(value if isinstance(value, (list, tuple)) else [value])
            hit = bool(set(ids) & want)
            return hit if op in ('in', '=') else not hit
        raise Unsupported(f'the operator {op!r} on a {ftype}')
    if op == '=?':
        return True if value in (False, None) else compare(v, '=', value, ftype)
    empty = v is False or v is None or (v == '' and not relational)
    if op in ('=', '!='):
        same = empty if value is False else (not empty and _eq(v, value))
        return same if op == '=' else not same
    if op in ('in', 'not in'):
        vals = list(value or [])
        inside = (empty and False in vals) or (not empty and any(_eq(v, x) for x in vals if x is not False))
        return inside if op == 'in' else not inside
    if op in ('<', '<=', '>', '>='):
        if empty or value is False:
            return False
        a, b = _ord(v), _ord(value)
        return {'<': a < b, '<=': a <= b, '>': a > b, '>=': a >= b}[op]
    if op in ('like', 'ilike', 'not like', 'not ilike'):
        hit = _like('%' + str(value) + '%', v, op.endswith('ilike')) if value not in (False, None) else empty
        return hit if not op.startswith('not') else not hit
    if op in ('=like', '=ilike'):
        return _like(value, v, op == '=ilike')
    if op in ('child_of', 'parent_of'):
        raise Unsupported(f'{op} needs the hierarchy: the answerer reads it')
    raise Unsupported(f'the operator {op!r}')


def _eq(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b or a == b and type(a) is type(b)
    try:
        return Fraction(str(a)) == Fraction(str(b))
    except (ValueError, ZeroDivisionError):
        return str(a) == str(b)


def _ord(x):
    try:
        return (0, Fraction(str(x)))
    except (ValueError, ZeroDivisionError):
        return (1, str(x))




# ------------------------------------------------------------------------------------------------ the calls
# Each answers as Odoo 17's server does (odoo/models.py, addons/web/models/models.py), over what it is handed: its
# reading of the records, the fields and the views; nothing else of the garden is within its reach.

DEFAULTS = {'one2many': [], 'many2many': [], 'integer': 0, 'float': 0, 'monetary': 0, 'properties': []}
NUMERIC = ('integer', 'float', 'monetary')
AGGREGATES = ('sum', 'avg', 'max', 'min', 'count', 'count_distinct', 'bool_and', 'bool_or', 'array_agg')
SPEC = re.compile(r'^(\w+)(?::(\w+)(?:\((\w+)\))?)?$')
TOO_MANY = 'Too many items to display.'
MONTHS = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November',
          'December')


def AND(*domains):
    """Domains joined by `&`, each in its prefix form."""
    parts = [normalize(d) for d in domains if d]
    if not parts:
        return [TRUE_LEAF]
    return ['&'] * (len(parts) - 1) + [t for p in parts for t in p]


def is_true(domain):
    return normalize(domain) == [TRUE_LEAF]


def _value(desc, v):
    """A field's value as Odoo's records hold it, where the record has none: False, 0 or []."""
    return DEFAULTS.get((desc or {}).get('type'), False) if v is None else v


def _ids(x):
    """The ids a call names, as Odoo's browse takes them: a list, or one id."""
    if isinstance(x, (list, tuple)):
        return [i for i in x if not isinstance(i, bool)]
    return [x] if isinstance(x, int) and not isinstance(x, bool) else []


def _number(x):
    """An exact sum given to the client: an integer where it is one."""
    if isinstance(x, Fraction):
        return int(x) if x.denominator == 1 else float(x)
    return x


def _when(v, ftype):
    import datetime as dt
    s = str(v)
    if ftype == 'date':
        return dt.datetime.strptime(s[:10], '%Y-%m-%d')
    return dt.datetime.strptime(s[:19], '%Y-%m-%d %H:%M:%S')


def _interval(v, ftype, granularity, tz=None, hour24=False, week_start=None):
    """(label, {from, to}) of the interval of `granularity` a date or datetime falls in, as Odoo labels and bounds it
    (English words; a datetime is cut in the reader's zone and its bounds given in UTC; an hour on the 12-hour clock as
    17 writes it, or on the 24-hour clock as 19 does). A week starts on Monday and is numbered as ISO 8601 numbers it,
    unless `week_start` (19: the language's first day, 1 Monday … 7 Sunday) says another day: then it starts on that
    day, and is numbered as 19 numbers it, its first week the one that holds the first of January."""
    import datetime as dt
    t = _when(v, ftype)
    zone = None
    if ftype == 'datetime' and tz:
        try:
            from zoneinfo import ZoneInfo
            zone = ZoneInfo(tz)
            t = t.replace(tzinfo=dt.timezone.utc).astimezone(zone).replace(tzinfo=None)
        except Exception:
            zone = None
    if granularity == 'hour':
        start = t.replace(minute=0, second=0)
        end = start + dt.timedelta(hours=1)
        label = f"{start.strftime('%H' if hour24 else '%I')}:00 {start.strftime('%d')} {MONTHS[start.month - 1][:3]}"
    elif granularity == 'day':
        start = t.replace(hour=0, minute=0, second=0)
        end = start + dt.timedelta(days=1)
        label = f"{start.strftime('%d')} {MONTHS[start.month - 1][:3]} {start.year}"
    elif granularity == 'week':
        first = (week_start - 1) if week_start else 0               # 0 Monday … 6 Sunday
        start = (t - dt.timedelta(days=(t.weekday() - first) % 7)).replace(hour=0, minute=0, second=0)
        end = start + dt.timedelta(days=7)
        if first == 0:
            y, w, _d = start.isocalendar()
        else:                       # odoo/tools/date_utils.py `weeknumber`, for a week that does not start on Monday
            def week_of(day):
                return day - dt.timedelta(days=(day.weekday() - first) % 7)
            d = start.date()
            if d >= week_of(d.replace(year=d.year + 1, month=1, day=1)):
                y, w = d.year + 1, 1
            else:
                y, w = d.year, (d - week_of(d.replace(month=1, day=1))).days // 7 + 1
        label = f"W{w} {y}"
    elif granularity == 'quarter':
        m = 3 * ((t.month - 1) // 3) + 1
        start = t.replace(month=m, day=1, hour=0, minute=0, second=0)
        end = start.replace(year=start.year + (m + 3 > 12), month=(m + 3 - 1) % 12 + 1)
        label = f"Q{(m - 1) // 3 + 1} {start.year}"
    elif granularity == 'year':
        start = t.replace(month=1, day=1, hour=0, minute=0, second=0)
        end = start.replace(year=start.year + 1)
        label = str(start.year)
    else:                                                       # month, the default
        start = t.replace(day=1, hour=0, minute=0, second=0)
        end = start.replace(year=start.year + (start.month == 12), month=start.month % 12 + 1)
        label = f"{MONTHS[start.month - 1]} {start.year}"
    if zone is not None:
        start = start.replace(tzinfo=zone).astimezone(dt.timezone.utc).replace(tzinfo=None)
        end = end.replace(tzinfo=zone).astimezone(dt.timezone.utc).replace(tzinfo=None)
    fmt = '%Y-%m-%d' if ftype == 'date' else '%Y-%m-%d %H:%M:%S'
    return label, {'from': start.strftime(fmt), 'to': end.strftime(fmt)}


class Answerer:
    """The calls of one series' client, for one reader, answered over what it is handed and nothing else: `records(m)`,
    the records the reader may read — the provider ANDs their grants in, and nothing here reaches any other record —
    `fields(m)`, the fields as the capture describes them, `views(m, wanted)`, the captured views, and
    `favourites(m, action_id)`, the reader's own saved searches."""

    def __init__(self, records, fields, views, favourites=None, series='17.0', week_start=7):
        self.records, self.fields, self.views = records, fields, views
        self.favourites = favourites or (lambda model, action_id: [])
        self.speak(series, week_start)

    def speak(self, series, week_start=7):
        """Answer as `series` answers. 19 reads records in their source's own order where the client names none (Odoo's
        `_order`: the order the source keeps them in), and starts a week on its language's first day (res.lang
        `week_start`, 1 Monday … 7 Sunday, as the language's translations of the client say it)."""
        self.major = int(m.group(1)) if (m := re.match(r'(\d+)\.', str(series or ''))) else 17
        self.keep_order = self.major >= 19
        self.week_start = week_start if isinstance(week_start, int) and 1 <= week_start <= 7 else 7
        return self

    # ---- reading records
    def follow(self, model, field, value):
        target = (self.fields(model).get(field) or {}).get('relation')
        ids = _id(value)
        ids = set(ids if isinstance(ids, (list, tuple)) else [] if ids in (False, None) else [ids])
        return [r for r in self.records(target) if r['id'] in ids] if target else []

    def parent_of(self, model):
        """The field a model's records are ordered under one another by (Odoo's `_parent_name`), where it has one."""
        f = self.fields(model).get('parent_id') or {}
        return 'parent_id' if f.get('type') == 'many2one' and f.get('relation') == model else None

    def hierarchy(self, model, value, op):
        """The ids `child_of` (the records named and every one beneath them) or `parent_of` (and every one above) reach."""
        start = {_id(x) for x in (value if isinstance(value, (list, tuple)) else [value]) if x not in (False, None)}
        recs = {r['id']: r for r in self.records(model)}
        parent = self.parent_of(model)
        if parent is None:
            return sorted(start, key=str)
        out = set()
        if op == 'child_of':
            out, grew = set(start), True
            while grew:
                grew = False
                for r in recs.values():
                    if r['id'] not in out and _id(r.get(parent)) in out:
                        out.add(r['id'])
                        grew = True
        else:
            for x in start:
                while x in recs and x not in out:
                    out.add(x)
                    x = _id(recs[x].get(parent))
        return sorted(out, key=str)

    def search(self, model, domain, context=None, order=None):
        context = context or {}
        d = Domain(domain, model, self.fields, self.follow, context, self.hierarchy)
        hide = context.get('active_test', True) and 'active' in self.fields(model) and not d.names_active()
        got = [r for r in self.records(model) if (not hide or r.get('active', True)) and d(r)]
        # as PostgreSQL orders: ascending puts the unset last, descending first, unless the order says NULLS FIRST/LAST
        for key in reversed([k.strip() for k in (order or ('' if self.keep_order else 'id')).split(',') if k.strip()]):
            words = key.lower().split()
            name, desc = key.split()[0], 'desc' in words[1:2]
            nulls_first = ('first' in words[2:]) if 'nulls' in words else desc
            got.sort(key=lambda r, n=name: _ord(_name(r.get(n))) if r.get(n) not in (False, None) else (2, ''),
                     reverse=desc)
            unset = [r for r in got if r.get(name) in (False, None)]
            got = ([r for r in got if r.get(name) not in (False, None)])
            got = unset + got if nulls_first else got + unset
        return got

    def project(self, model, rec, spec):
        """A record as web_read gives it for a specification: a many2one its id, or with `fields` the record it points
        at read again by them; an x2many its ids, or with `fields` the records; anything else as held."""
        desc_of = self.fields(model)
        out = {'id': rec['id']}
        for name, sub in (spec or {}).items():
            if name == 'id':
                continue
            desc = desc_of.get(name) or {}
            ftype, v = desc.get('type'), _value(desc, rec.get(name))
            sub = sub if isinstance(sub, dict) else {}
            if ftype == 'many2one':
                if not v:
                    out[name] = False
                elif 'fields' not in sub:
                    out[name] = _id(v)
                else:
                    target = next((r for r in self.records(desc.get('relation')) if r['id'] == _id(v)), None)
                    got = self.project(desc.get('relation'), target, sub['fields']) if target else {'id': _id(v)}
                    got['display_name'] = (target or {}).get('display_name') or _name(v)
                    out[name] = got
            elif ftype in ('one2many', 'many2many'):
                ids = list(_id(v) or []) if isinstance(v, (list, tuple)) else []
                if 'fields' in sub:
                    by = {r['id']: r for r in self.records(desc.get('relation'))}
                    out[name] = [self.project(desc.get('relation'), by[i], sub['fields']) for i in ids if i in by]
                else:
                    out[name] = ids
            else:
                out[name] = v
        return out

    def read(self, model, ids, fields=None, load='_classic_read'):
        """Odoo's `read`: the records of `ids` the reader may read, in that order; a many2one as [id, name] (`load`
        None: its id)."""
        desc_of = self.fields(model)
        by = {r['id']: r for r in self.records(model)}
        names = list(fields or [n for n in desc_of if desc_of[n].get('type') not in ('binary',)])
        out = []
        for i in _ids(ids):
            r = by.get(i)
            if r is None:
                continue
            row = {'id': i}
            for n in names:
                if n == 'id':
                    continue
                desc = desc_of.get(n) or {}
                v = _value(desc, r.get(n))
                if desc.get('type') == 'many2one':
                    v = (_id(v) if load is None else [_id(v), _name(v)]) if v else False
                elif desc.get('type') in ('one2many', 'many2many'):
                    v = list(v or [])
                row[n] = v
            out.append(row)
        return out

    # ---- the calls
    def call(self, model, method, args, kwargs):
        kw, ctx = dict(kwargs or {}), (kwargs or {}).get('context') or {}
        args = list(args or [])

        def arg(i, name, default=None):
            return args[i] if len(args) > i else kw.get(name, default)
        if model == 'ir.filters' and method == 'get_filters':
            return self.favourites(arg(0, 'model'), arg(1, 'action_id'))
        if method == 'get_views':
            got = self.views(model, kw.get('views') or arg(0, 'views') or [])
            opts = kw.get('options') or {}
            if opts.get('load_filters') and 'search' in got.get('views', {}):
                got['views']['search']['filters'] = self.favourites(model, opts.get('action_id'))
            return got
        if method == 'fields_get':
            allfields, attributes = arg(0, 'allfields'), arg(1, 'attributes')
            desc = self.fields(model)
            return {n: ({k: v for k, v in d.items() if k in attributes} if attributes else d)
                    for n, d in desc.items() if not allfields or n in allfields}
        if method == 'web_search_read':
            got = self.search(model, arg(0, 'domain') or [], ctx, kw.get('order'))
            off, lim, cap = kw.get('offset') or 0, kw.get('limit'), kw.get('count_limit')
            page = got[off:off + lim] if lim else got[off:]
            current = len(page) + off
            if not page:
                length = 0
            elif lim and ((len(page) == lim and not (cap and cap <= current)) or ctx.get('force_search_count')):
                length = min(len(got), cap) if cap else len(got)
            else:
                length = current
            spec = arg(1, 'specification') or {}
            return {'length': length, 'records': [self.project(model, r, spec) for r in page]}
        if method == 'web_read':
            ids = _ids(arg(0, 'ids'))
            by = {r['id']: r for r in self.records(model)}
            return [self.project(model, by[i], arg(1, 'specification') or {}) for i in ids if i in by]
        if method == 'read':
            return self.read(model, arg(0, 'ids') or [], arg(1, 'fields'), kw.get('load', '_classic_read'))
        if method in ('search', 'search_read', 'search_count'):
            got = self.search(model, arg(0, 'domain') or [], ctx, kw.get('order') if method != 'search_count' else None)
            if method == 'search_count':
                lim = kw.get('limit')
                return min(len(got), lim) if lim else len(got)
            off = arg(1 if method == 'search' else 2, 'offset') or 0
            lim = arg(2 if method == 'search' else 3, 'limit')
            page = got[off:off + lim] if lim else got[off:]
            if method == 'search':
                return [r['id'] for r in page]
            return self.read(model, [r['id'] for r in page], arg(1, 'fields'))
        if self.major >= 19:
            got = self.call_19(model, method, arg, kw, ctx)
            if got is not NotImplemented:
                return got
        if method == 'name_search':
            name, dom = arg(0, 'name') or '', arg(1, 'args') or []
            operator, limit = arg(2, 'operator') or 'ilike', arg(3, 'limit', 100)
            leaf = [] if (name == '' and operator in ('like', 'ilike')) else [('display_name', operator, name)]
            got = self.search(model, AND(dom, leaf) if leaf else dom, ctx)
            return [[r['id'], r.get('display_name') or str(r['id'])] for r in (got[:limit] if limit else got)]
        if method == 'read_group':
            return self.read_group(model, arg(0, 'domain') or [], arg(1, 'fields') or [], arg(2, 'groupby') or [],
                                   ctx, arg(3, 'offset') or 0, arg(4, 'limit'), arg(5, 'orderby'), arg(6, 'lazy', True))
        if method == 'web_read_group':
            domain, groupby = arg(0, 'domain') or [], arg(2, 'groupby') or []
            limit, offset, lazy = arg(3, 'limit'), arg(4, 'offset') or 0, arg(6, 'lazy', True)
            groups = self.read_group(model, domain, arg(1, 'fields') or [], groupby, ctx, offset, limit,
                                     arg(5, 'orderby'), lazy)
            if not groups:
                length = 0
            elif limit and len(groups) == limit:
                length = len(self.read_group(model, domain, [], groupby if not lazy else groupby[:1], ctx, 0, None,
                                             None, False))
            else:
                length = len(groups) + offset
            return {'groups': groups, 'length': length}
        if method == 'search_panel_select_range':
            return self.select_range(model, arg(0, 'field_name'), kw, ctx)
        if method == 'search_panel_select_multi_range':
            return self.select_multi_range(model, arg(0, 'field_name'), kw, ctx)
        if method == 'has_group':
            return False
        if method == 'check_access_rights':      # Odoo's client is served read-only: reading, yes; nothing else
            return arg(0, 'operation') == 'read'
        raise Unsupported(f'{model}.{method}')

    # ---- groups
    def read_group(self, model, domain, fields, groupby, ctx, offset=0, limit=None, orderby=None, lazy=True):
        """Odoo's read_group: the records grouped by the first of `groupby` (all of them where not lazy), each group with
        its value, its count, its aggregates summed exactly, its domain and, for a date, its range."""
        desc_of = self.fields(model)
        groupby = [groupby] if isinstance(groupby, str) else list(groupby or [])
        lazy_by = groupby[:1] if lazy else groupby
        got = self.search(model, domain, ctx)
        count_key = f"{lazy_by[0].split(':')[0]}_count" if lazy and len(lazy_by) == 1 else '__count'
        aggs = {}                                    # result name -> (field, function)
        for spec in fields or []:
            if spec == '__count':
                continue
            m = SPEC.match(str(spec))
            if not m:
                raise Unsupported(f'the field specification {spec!r}')
            name, func, fname = m.groups()
            field = fname or name
            if func and func not in AGGREGATES:
                raise Unsupported(f'the aggregate {func!r}')
            desc = desc_of.get(field)
            if desc is None or field in [g.split(':')[0] for g in lazy_by]:
                continue
            func = func or desc.get('group_operator') or desc.get('aggregator') or ('sum' if desc.get('type') in NUMERIC else None)
            if func is None or (desc.get('type') in ('many2one', 'many2many') and func not in ('count_distinct', 'array_agg', 'count')):
                continue
            aggs[name] = (field, func)

        def keys(r, spec):
            field, _, gran = spec.partition(':')
            desc = desc_of.get(field) or {}
            v = r.get(field)
            if desc.get('type') == 'many2many':
                return [(i, i) for i in (v or [])] or [(False, False)]
            if v in (None, False, ''):
                return [(False, False)]
            if desc.get('type') == 'many2one':
                return [(_id(v), [_id(v), _name(v)])]
            if desc.get('type') in ('date', 'datetime'):
                label, rng = _interval(v, desc['type'], gran or 'month', ctx.get('tz'))
                return [((label, rng['from']), (label, rng))]
            return [(v, v)]
        buckets = {}
        for r in got:
            combos = [((), ())]
            for spec in lazy_by:
                combos = [(k + (a,), vals + (b,)) for k, vals in combos for a, b in keys(r, spec)]
            for k, vals in combos:
                buckets.setdefault(k, (vals, []))[1].append(r)
        by_id = {}
        out = []
        for k, (vals, rs) in buckets.items():
            g = {}
            extra = []
            for spec, val in zip(lazy_by, vals):
                field, _, _gran = spec.partition(':')
                desc = desc_of.get(field) or {}
                if desc.get('type') in ('date', 'datetime'):
                    if val is False:
                        g[spec] = False
                        g.setdefault('__range', {})[spec] = False
                        extra.append((field, '=', False))
                    else:
                        g[spec] = val[0]
                        g.setdefault('__range', {})[spec] = val[1]
                        extra += ['&', (field, '>=', val[1]['from']), (field, '<', val[1]['to'])]
                elif desc.get('type') == 'many2many':
                    if val is False:
                        others = sorted({i for r in got for i in (r.get(field) or [])}, key=str)
                        g[spec] = False
                        extra.append((field, 'not in', others))
                    else:
                        if not by_id.get(field):
                            by_id[field] = {x['id']: x for x in self.records(desc.get('relation'))}
                        rel = by_id[field].get(val)
                        g[spec] = [val, (rel or {}).get('display_name') or str(val)]
                        extra.append((field, '=', val))
                else:
                    g[spec] = val
                    extra.append((field, '=', _id(val) if desc.get('type') == 'many2one' and val else val))
            g[count_key] = len(rs)
            for name, (field, func) in aggs.items():
                ftype = (desc_of.get(field) or {}).get('type')
                vals_ = [r.get(field) for r in rs]
                if func == 'array_agg':
                    g[name] = [(_id(v) if ftype == 'many2one' else v) or None for v in vals_]
                elif func in ('count_distinct', 'count'):
                    seen = [(_id(v) if ftype == 'many2one' else v) for v in vals_ if v not in (None, False)]
                    g[name] = len(set(map(str, seen))) if func == 'count_distinct' else len(seen)
                elif func in ('bool_and', 'bool_or'):
                    g[name] = (all if func == 'bool_and' else any)(bool(v) for v in vals_)
                else:
                    nums = [Fraction(str(v)) for v in vals_ if v not in (None, False)]
                    if not nums:
                        g[name] = False if func in ('max', 'min', 'avg') else 0
                        continue
                    total = {'sum': lambda: sum(nums, Fraction(0)), 'max': lambda: max(nums), 'min': lambda: min(nums),
                             'avg': lambda: sum(nums, Fraction(0)) / len(nums)}[func]()
                    g[name] = _number(total)                     # exact until here
            g['__domain'] = AND(domain, extra) if extra else normalize(domain)
            if len(lazy_by) < len(groupby):
                g['__context'] = {'group_by': groupby[len(lazy_by):]}
            out.append(g)
        out = self.order_groups(model, out, orderby or ','.join(lazy_by), lazy_by)
        return out[offset:offset + limit] if limit else out[offset:]

    def order_groups(self, model, groups, orderby, lazy_by):
        """The groups in the order asked: by their values (a many2one by its record's place among them, a selection by
        its place in the field's list, a date by its range), or by an aggregate or the count; the unset last."""
        desc_of = self.fields(model)
        for term in reversed([t.strip() for t in str(orderby).split(',') if t.strip()]):
            name, desc_ = term.split()[0], 'desc' in term.lower().split()[1:2]
            spec = next((s for s in lazy_by if s.split(':')[0] == name.split(':')[0]), None)
            desc = desc_of.get(name.split(':')[0]) or {}
            rank = None
            if spec and desc.get('type') == 'many2one':
                rank = {r['id']: i for i, r in enumerate(self.search(desc.get('relation'), [], {'active_test': False}))}
            elif spec and desc.get('type') == 'selection':
                rank = {k: i for i, (k, _l) in enumerate(desc.get('selection') or [])}

            def key(g, spec=spec, rank=rank, name=name):
                if spec is None:
                    v = g.get(name)
                    return (0, _ord(v)) if v not in (None, False) else (1, (1, ''))
                v = g.get(spec)
                if v in (None, False):
                    return (1, (1, ''))
                if desc.get('type') in ('date', 'datetime'):
                    return (0, (1, (g.get('__range') or {}).get(spec, {}).get('from', '')))
                if rank is not None:
                    return (0, (0, Fraction(rank.get(_id(v), len(rank)))))
                return (0, _ord(_name(v)))
            set_ = [g for g in groups if key(g)[0] == 0]
            unset = [g for g in groups if key(g)[0] == 1]
            set_.sort(key=key, reverse=desc_)
            groups = (unset + set_) if desc_ else (set_ + unset)
        return groups

    # ---- the search panel
    def _image(self, model, field, domain, ctx, set_count=False, limit=None):
        """{value: {id, display_name, __count?}}: the values the field takes over the records of `domain`, in the order
        Odoo's groups give them."""
        desc = self.fields(model).get(field) or {}
        groups = self.read_group(model, AND(domain, [(field, '!=', False)]), [field], [field], ctx, 0,
                                 limit or None, None, True)
        labels = dict((k, n) for k, n in desc.get('selection') or [])
        out = {}
        for g in groups:
            v = g.get(field)
            if desc.get('type') == 'selection':
                vid, name = v, labels.get(v, v)
            else:
                vid, name = _id(v), _name(v)
            values = {'id': vid, 'display_name': name}
            if set_count:
                values['__count'] = g[f'{field}_count']
            out[vid] = values
        return out

    def _field_image(self, model, field, kw, ctx, model_domain, extra_domain, only_counters=False, set_limit=False):
        count_domain = AND(model_domain, extra_domain)
        if only_counters:
            return self._image(model, field, count_domain, ctx, True)
        enable = kw.get('enable_counters')
        no_extra = is_true(extra_domain)
        image = self._image(model, field, model_domain, ctx, bool(enable and no_extra), set_limit and kw.get('limit'))
        if enable and not no_extra:
            counts = self._image(model, field, count_domain, ctx, True)
            for vid, values in image.items():
                values['__count'] = (counts.get(vid) or {}).get('__count', 0)
        return image

    def _selection_range(self, model, field, kw, ctx, model_domain, extra_domain):
        enable, expand = kw.get('enable_counters'), kw.get('expand')
        image = {}
        if enable or not expand:
            image = self._field_image(model, field, kw, ctx, model_domain, extra_domain, only_counters=bool(expand))
        if not expand:
            return list(image.values())
        out = []
        for value, label in (self.fields(model).get(field) or {}).get('selection') or []:
            values = {'id': value, 'display_name': label}
            if enable:
                values['__count'] = (image.get(value) or {}).get('__count', 0)
            out.append(values)
        return out

    def _comodel(self, rel, domain, ctx, limit, short=False):
        """The comodel's records of `domain`, at most `limit`, each with its display name (`short`: without the names of
        those above it, as Odoo names them where they are shown as a tree)."""
        got = self.search(rel, domain, ctx)
        got = got[:limit] if limit else got
        for r in got:
            yield r, ((r.get('name') if short and r.get('name') else None) or r.get('display_name') or str(r['id']))

    def select_range(self, model, field, kw, ctx):
        desc = self.fields(model).get(field) or {}
        if desc.get('type') not in ('many2one', 'selection'):
            raise Unsupported(f'a search panel category on a {desc.get("type")} field')
        model_domain = kw.get('search_domain') or []
        extra_domain = AND(kw.get('category_domain') or [], kw.get('filter_domain') or [])
        if desc['type'] == 'selection':
            return {'parent_field': False,
                    'values': self._selection_range(model, field, kw, ctx, model_domain, extra_domain)}
        rel = desc.get('relation')
        hierarchize = kw.get('hierarchize', True)
        parent = self.parent_of(rel) if hierarchize else None
        hierarchize = parent is not None
        comodel_domain = kw.get('comodel_domain') or []
        enable, expand, limit = kw.get('enable_counters'), kw.get('expand'), kw.get('limit')
        image = {}
        if enable or not expand:
            image = self._field_image(model, field, kw, ctx, model_domain, extra_domain, only_counters=bool(expand),
                                      set_limit=bool(limit and not (expand or hierarchize or comodel_domain)))
        if not (expand or hierarchize or comodel_domain):
            values = list(image.values())
            if limit and len(values) == limit:
                return {'error_msg': TOO_MANY}
            return {'parent_field': parent or False, 'values': values}
        if not expand:
            ids = list(image)
            comodel_domain = AND(comodel_domain, [('id', 'parent_of' if hierarchize else 'in', ids)])
        rows = list(self._comodel(rel, comodel_domain, ctx, limit, short=hierarchize))
        if hierarchize:
            keep_ids = [r['id'] for r, _n in rows] if expand else list(image)
            allowed = {r['id']: r for r, _n in rows}
            keep = {}
            for i in keep_ids:
                chain, x, whole = [], i, True
                while x:
                    if x in keep:
                        whole = keep[x]
                        break
                    r = allowed.get(x)
                    if r is None:
                        whole = False
                        break
                    chain.append(x)
                    x = _id(r.get(parent))
                for c in chain:
                    keep[c] = whole
            rows = [(r, n) for r, n in rows if keep.get(r['id'])]
        if limit and len(rows) == limit:
            return {'error_msg': TOO_MANY}
        values = {}
        for r, n in rows:
            v = {'id': r['id'], 'display_name': n}
            if hierarchize:
                v[parent] = _id(r.get(parent)) or False
            if enable:
                v['__count'] = (image.get(r['id']) or {}).get('__count', 0)
            values[r['id']] = v
        if hierarchize and enable:                            # each value counts what is beneath it too
            local = {i: v['__count'] for i, v in values.items()}
            for i, v in values.items():
                up = v[parent]
                while up and local[i]:
                    if up not in values:
                        break
                    values[up]['__count'] += local[i]
                    up = values[up][parent]
        return {'parent_field': parent or False, 'values': list(values.values())}

    def select_multi_range(self, model, field, kw, ctx):
        import json
        desc = self.fields(model).get(field) or {}
        if desc.get('type') not in ('many2one', 'many2many', 'selection'):
            raise Unsupported(f'a search panel filter on a {desc.get("type")} field')
        model_domain = kw.get('search_domain') or []
        extra_domain = AND(kw.get('category_domain') or [], kw.get('filter_domain') or [])
        if desc['type'] == 'selection':
            return {'values': self._selection_range(model, field, kw, ctx, model_domain, extra_domain)}
        rel = desc.get('relation')
        group_by, limit = kw.get('group_by'), kw.get('limit')
        gdesc = self.fields(rel).get(group_by) or {} if group_by else {}

        def group_of(r):
            v = r.get(group_by)
            if gdesc.get('type') == 'many2one':
                return (_id(v), _name(v)) if v else (False, 'Not Set')
            if gdesc.get('type') == 'selection':
                return (v, dict(gdesc.get('selection') or []).get(v, v)) if v else (False, 'Not Set')
            return (v, v) if v else (False, 'Not Set')
        comodel_domain = kw.get('comodel_domain') or []
        enable, expand = kw.get('enable_counters'), kw.get('expand')
        if desc['type'] == 'many2many':
            if not expand:
                ids = list(self._image(model, field, model_domain, ctx, False, limit))
                comodel_domain = AND(comodel_domain, [('id', 'in', ids)])
            rows = list(self._comodel(rel, comodel_domain, ctx, limit))
            if limit and len(rows) == limit:
                return {'error_msg': TOO_MANY}
            group_domain = kw.get('group_domain') or {}
            out = []
            for r, n in rows:
                v = {'id': r['id'], 'display_name': n}
                gid = None
                if group_by:
                    gid, v['group_name'] = group_of(r)
                    v['group_id'] = gid
                if enable:
                    local = AND(extra_domain, group_domain.get(json.dumps(gid), []) if group_by and isinstance(group_domain, dict) else [])
                    v['__count'] = len(self.search(model, AND(model_domain, [(field, 'in', r['id'])], local), ctx))
                out.append(v)
            return {'values': out}
        image = {}
        if enable or not expand:
            gd = kw.get('group_domain') or []
            image = self._field_image(model, field, kw, ctx, model_domain,
                                      AND(extra_domain, gd if isinstance(gd, list) else []),
                                      only_counters=bool(expand),
                                      set_limit=bool(limit and not (expand or group_by or comodel_domain)))
        if not (expand or group_by or comodel_domain):
            values = list(image.values())
            if limit and len(values) == limit:
                return {'error_msg': TOO_MANY}
            return {'values': values}
        if not expand:
            comodel_domain = AND(comodel_domain, [('id', 'in', list(image))])
        rows = list(self._comodel(rel, comodel_domain, ctx, limit))
        if limit and len(rows) == limit:
            return {'error_msg': TOO_MANY}
        out = []
        for r, n in rows:
            v = {'id': r['id'], 'display_name': n}
            if group_by:
                v['group_id'], v['group_name'] = group_of(r)
            if enable:
                v['__count'] = (image.get(r['id']) or {}).get('__count', 0)
            out.append(v)
        return {'values': out}

    # ---- series 19 (odoo/addons/web/models/models.py of 19.0): the calls whose signature or answer changed
    def call_19(self, model, method, arg, kw, ctx):
        """A call as 19's server answers it, or NotImplemented where it answers as 17's does."""
        if model == 'properties.base.definition' and method == 'get_properties_base_definition':
            return self.base_definitions_19(arg(0, 'model_name'), arg(1, 'field_name'))
        if method == 'name_search':                       # 19 names its domain `domain`
            return self.name_search_19(model, arg(0, 'name') or '', arg(1, 'domain') or [], arg(2, 'operator') or 'ilike',
                                       arg(3, 'limit', 100), ctx)
        if method == 'web_name_search':                   # the many2one's suggestions, read by a specification
            spec = arg(1, 'specification') or {}
            pairs = self.name_search_19(model, arg(0, 'name') or '', arg(2, 'domain') or [], arg(3, 'operator') or 'ilike',
                                        arg(4, 'limit', 100), ctx)
            if set(spec) == {'display_name'}:
                return [{'id': i, 'display_name': n, '__formatted_display_name': n} for i, n in pairs]
            by = {r['id']: r for r in self.records(model)}
            return [self.project(model, by[i], spec) for i, _n in pairs if i in by]
        if method in ('has_access', 'check_access'):     # served read-only: reading, yes; nothing else
            operation = arg(1, 'operation')               # a method of records: their ids come first
            if operation == 'read':
                return True if method == 'has_access' else None
            if method == 'has_access':
                return False
            raise Unsupported(f'{model}.{method}({operation!r}): daftard answers no write')
        if method == 'formatted_read_group':
            if arg(3, 'having'):
                raise Unsupported('a group read with `having`')
            return self.formatted_19(model, arg(0, 'domain') or [], list(arg(1, 'groupby') or []), list(arg(2, 'aggregates') or []),
                                     ctx, arg(4, 'offset') or 0, arg(5, 'limit'), arg(6, 'order'))
        if method == 'web_read_group':                    # 19's signature: domain, groupby, aggregates, its openings
            return self.web_read_group_19(model, arg(0, 'domain') or [], list(arg(1, 'groupby') or []),
                                          list(arg(2, 'aggregates') or []), arg(3, 'limit'), arg(4, 'offset') or 0,
                                          arg(5, 'order'), ctx, kw)
        return NotImplemented

    def base_definitions_19(self, model, field):
        """19's `properties.base.definition.get_properties_base_definition(model_name, field_name)`: the property
        definitions of a properties field whose records have no parent to hold them (res.partner's `properties`, say),
        which 19's client asks for wherever it lists a model's fields — the search editor's filters and group-bys
        among them. 19 reads them from its base definition record of that field (web/models/
        properties_base_definition.py). daftard holds no such record: a garden's beans define no property, and what a
        garden captures of a register — views and field descriptions — carries no definition. So the answer is 19's
        own where no base definition record exists — none — and the client offers no property to filter or group by.
        Never a record, never a write (19 would make the record on a model's first create; nothing is made here). As
        19 refuses, a field that is no properties field of a model the reader may read is refused."""
        desc = self.fields(model) if isinstance(model, str) else None
        if not desc or not isinstance(field, str) or (desc.get(field) or {}).get('type') != 'properties':
            raise Denied('You can not read that field definition.')
        return {'length': 0, 'records': []}

    def name_search_19(self, model, name, domain, operator, limit, ctx):
        leaf = [] if (name == '' and operator in ('like', 'ilike')) else [('display_name', operator, name)]
        got = self.search(model, AND(domain, leaf) if leaf else domain, ctx)
        return [[r['id'], r.get('display_name') or str(r['id'])] for r in (got[:limit] if limit else got)]

    GRANULARITY_19 = ('hour', 'day', 'week', 'month', 'quarter', 'year')

    def _group_value_19(self, model, rec, spec, ctx):
        """[(value, domain)] of one record for one groupby spec, as 19's formatters give them (one per id of a
        many2many)."""
        field, _, gran = spec.partition(':')
        if '.' in field:
            raise Unsupported(f'a group by a related path ({spec!r})')
        desc = self.fields(model).get(field)
        if desc is None and field != 'id':
            raise Unsupported(f'{model} has no field {field!r}')
        ftype, v = (desc or {}).get('type', 'integer'), rec.get(field)
        if ftype == 'many2many':
            names = {r['id']: r.get('display_name') or str(r['id']) for r in self.records(desc.get('relation'))} if v else {}
            return [([i, names.get(i, str(i))], [(field, '=', i)]) for i in v] or [(False, [(field, 'not any', [])])]
        if ftype == 'many2one' or field == 'id':
            if not v:
                return [(False, [(field, '=', False)])]
            return [([_id(v), _name(v) if isinstance(v, (list, tuple)) else str(v)], [(field, '=', _id(v))])]
        if ftype in ('date', 'datetime'):
            gran = gran or 'month'
            if gran not in self.GRANULARITY_19:
                raise Unsupported(f'the granularity {gran!r}')
            if v in (None, False, ''):
                return [(False, [(field, '=', False)])]
            label, rng = _interval(v, ftype, gran, ctx.get('tz'), hour24=True,   # 19 writes an hour on the 24-hour clock
                                   week_start=self.week_start)
            return [([rng['from'], label], ['&', (field, '>=', rng['from']), (field, '<', rng['to'])])]
        v = False if v is None else v
        return [(v, [(field, '=', v)])]

    def formatted_19(self, model, domain, groupby, aggregates, ctx, offset=0, limit=None, order=None):
        """19's formatted_read_group over the records the reader may read: each group's value per groupby spec, its
        `__extra_domain`, and each aggregate (`field:func`, `__count`) summed exactly."""
        if ctx.get('fill_temporal'):
            raise Unsupported('a group read that fills the time between groups (fill_temporal)')
        desc_of = self.fields(model)
        got = self.search(model, domain, ctx)
        buckets = {}
        for r in got:
            combos = [((), (), [])]
            for spec in groupby:
                combos = [(k + (json_key(val),), vals + (val,), doms + [dom])
                          for k, vals, doms in combos for val, dom in self._group_value_19(model, r, spec, ctx)]
            for k, vals, doms in combos:
                buckets.setdefault(k, (vals, doms, []))[2].append(r)
        out = []
        for _k, (vals, doms, rs) in buckets.items():
            g = dict(zip(groupby, vals))
            g['__extra_domain'] = conjunction_19(doms)
            for spec in aggregates:
                g[spec] = self._aggregate_19(model, spec, rs)
            out.append(g)
        out = self._order_19(model, out, order or ', '.join(groupby), groupby)
        return out[offset:offset + limit] if limit else out[offset:]

    def _aggregate_19(self, model, spec, rs):
        if spec == '__count':
            return len(rs)
        field, _, func = spec.partition(':')
        desc = self.fields(model).get(field) or {}
        func = 'array_agg' if func == 'recordset' else func
        if func not in AGGREGATES + ('array_agg_distinct',):
            raise Unsupported(f'the aggregate {spec!r}')
        ftype = desc.get('type')
        vals = [r.get(field) for r in rs]
        if func in ('array_agg', 'array_agg_distinct'):
            got = [(_id(v) if ftype == 'many2one' else v) or None for v in vals]
            return sorted(set(got), key=lambda x: (x is None, str(x))) if func == 'array_agg_distinct' else got
        if func in ('count_distinct', 'count'):
            seen = [(_id(v) if ftype == 'many2one' else v) for v in vals if v not in (None, False)]
            return len(set(map(str, seen))) if func == 'count_distinct' else len(seen)
        if func in ('bool_and', 'bool_or'):
            return (all if func == 'bool_and' else any)(bool(v) for v in vals)
        nums = [Fraction(str(v)) for v in vals if v not in (None, False)]
        if not nums:
            return False if func in ('max', 'min', 'avg') else 0
        return _number({'sum': lambda: sum(nums, Fraction(0)), 'max': lambda: max(nums), 'min': lambda: min(nums),
                        'avg': lambda: sum(nums, Fraction(0)) / len(nums)}[func]())

    def _order_19(self, model, groups, order, groupby):
        """The groups in the order asked (`spec [ASC|DESC] [NULLS FIRST|LAST]`, a spec a groupby or an aggregate): a
        many2one by its record's place among its model's, a selection by its place in the field's list, a date by its
        range, an aggregate by its value; the unset last ascending and first descending, as PostgreSQL orders them."""
        desc_of = self.fields(model)
        for term in reversed([t.strip() for t in str(order).split(',') if t.strip()]):
            words = term.split()
            spec, desc_ = words[0], len(words) > 1 and words[1].lower() == 'desc'
            nulls_first = ('first' in [w.lower() for w in words[2:]]) if 'nulls' in [w.lower() for w in words] else desc_
            field = spec.split(':')[0]
            desc = desc_of.get(field) or {}
            rank = None                                   # a selection groups by its key, as 19's SQL orders it
            if spec in groupby and desc.get('type') == 'many2one':
                rank = {r['id']: i for i, r in enumerate(self.search(desc.get('relation'), [], {'active_test': False}))}

            def key(g, spec=spec, rank=rank):
                v = g.get(spec)
                if v in (None, False):
                    return None
                if isinstance(v, list):                   # [id, name] or [range start, label]
                    v = v[0]
                if rank is not None:
                    return (0, Fraction(rank.get(v, len(rank))))
                return _ord(v)
            set_ = [g for g in groups if key(g) is not None]
            unset = [g for g in groups if key(g) is None]
            set_.sort(key=key, reverse=desc_)
            groups = (unset + set_) if nulls_first else (set_ + unset)
        return groups

    def _group_order_19(self, model, dict_order, groupby, aggregates):
        """19's _get_read_group_order: the order a level of groups is read in, from the order the client asked."""
        if not dict_order:
            return ', '.join(groupby)
        groupby, spec = list(groupby), []
        for fname, direction in dict_order.items():
            if fname == '__count':
                spec.append(f'{fname} {direction}')
                continue
            for g in list(groupby):
                if fname == g or g.startswith(f'{fname}:'):
                    groupby.remove(g)
                    spec.append(f'{g} {direction}')
                    break
            else:
                for agg in aggregates:
                    if agg.startswith(f'{fname}:'):
                        spec.append(f'{agg} {direction}')
                        break
                else:
                    desc = self.fields(model).get(fname) or {}
                    if desc.get('aggregator') or desc.get('group_operator'):
                        spec.append(f"{fname}:{desc.get('aggregator') or desc.get('group_operator')} {direction}")
        return ', '.join(spec + groupby)

    def _with_length_19(self, model, domain, groupby, aggregates, ctx, offset, limit, order):
        groups = self.formatted_19(model, domain, groupby, aggregates, ctx, offset, limit, order)
        if not groups:
            length = 0
        elif limit and len(groups) == limit:
            length = limit + len(self.formatted_19(model, domain, groupby, [], ctx, limit, None, order))
        else:
            length = len(groups) + offset
        return groups, length

    def web_read_group_19(self, model, domain, groupby, aggregates, limit, offset, order, ctx, kw):
        """19's web_read_group: the first level of groups and their count, each group opened as the client asks
        (`opening_info`) or, for a kanban, the first ten (`auto_unfold`): its subgroups, or its records read by
        `unfold_read_specification`."""
        if not groupby:
            raise Unsupported('a group read with nothing to group by')
        aggregates = list(aggregates) + ([] if '__count' in aggregates else ['__count'])
        dict_order = {}
        for part in (str(order).split(',') if order else ()):
            words = part.split()
            if not words:
                continue
            dict_order[words[0]] = ' '.join(w.upper() for w in words[1:]) or 'ASC'
        groups, length = self._with_length_19(model, domain, [groupby[0]], aggregates, ctx, offset, limit,
                                              self._group_order_19(model, dict_order, [groupby[0]], aggregates))
        openings = []
        default_limit = kw.get('unfold_read_default_limit', 80)
        self._open_19(model, openings, groups, domain, groupby, aggregates, dict_order, bool(kw.get('auto_unfold')),
                      kw.get('opening_info'), default_limit, kw.get('opening_info'), [TRUE_LEAF], ctx)
        if openings:
            # the client's order where it names one, else the source's own (Odoo's `_order` breaks every tie)
            order_terms = [f'{f} {d}' for f, d in dict_order.items() if f not in groupby and f != '__count']
            spec = kw.get('unfold_read_specification') or {}
            for o in openings:
                if not o['group']['__count']:
                    o['group']['__records'] = []
                    continue
                rs = self.search(model, AND(domain, o['domain']), ctx, ', '.join(order_terms))
                rs = rs[o['offset']:o['offset'] + o['limit']] if o['limit'] else rs[o['offset']:]
                o['group']['__records'] = [self.project(model, r, spec) for r in rs]
        grs = kw.get('groupby_read_specification') or {}
        level = groups
        for spec in groupby:
            if spec in grs:
                desc = self.fields(model).get(spec) or {}
                by = {r['id']: r for r in self.records(desc.get('relation'))}
                for g in level:
                    v = g.get(spec)
                    g['__values'] = self.project(desc.get('relation'), by[v[0]], grs[spec]) if v and v[0] in by else {'id': False}
            level = [sg for g in level for sg in (g.get('__groups') or {}).get('groups', ())]
        return {'groups': groups, 'length': length}

    def _open_19(self, model, openings, groups, domain, groupby, aggregates, dict_order, auto_unfold, opening_info,
                 default_limit, parent_info, parent_domain, ctx):
        """19's _open_groups."""
        max_open = ctx.get('max_number_opened_groups') or 10
        parent = {o.get('value') if not isinstance(o.get('value'), list) else o['value'][0]: o
                  for o in (parent_info or []) if isinstance(o, dict)}
        spec = groupby[0]
        desc = self.fields(model).get(spec.split(':')[0].split('.')[0]) or {}
        relational = desc.get('type') in ('many2one', 'one2many', 'many2many')
        last = len(groupby) == 1
        sub_order = None if last else self._group_order_19(model, dict_order, [groupby[1]], aggregates)
        opened = 0
        for g in groups:
            fold_info = '__fold' in g
            fold = g.pop('__fold', False)
            v = g[spec]
            raw = v[0] if isinstance(v, list) else v
            limit, offset, progress, sub_info = default_limit, 0, None, None
            if opening_info and raw in parent:
                info = parent[raw]
                if info.get('folded'):
                    continue
                limit, offset = info.get('limit'), info.get('offset') or 0
                progress, sub_info = info.get('progressbar_domain'), info.get('groups')
            elif (not auto_unfold and not fold_info) or opened >= max_open or fold or (relational and not v):
                continue
            opened += 1
            if last:
                rd = AND(parent_domain, g['__extra_domain'])
                if progress:
                    rd = AND(rd, progress)
                if offset and offset >= g['__count']:
                    g['__offset'] = offset = 0
                openings.append({'domain': rd, 'limit': limit, 'offset': offset, 'group': g})
            else:
                sub_domain = AND(parent_domain, g['__extra_domain']) if g['__extra_domain'] else parent_domain
                subgroups, length = self._with_length_19(model, AND(sub_domain, domain), [groupby[1]], aggregates, ctx,
                                                         offset, limit, sub_order)
                g['__groups'] = {'groups': subgroups, 'length': length}
                self._open_19(model, openings, subgroups, domain, groupby[1:], aggregates, dict_order, False, opening_info,
                              default_limit, sub_info, sub_domain, ctx)


def conjunction_19(domains):
    """Domains that are each a conjunction of leaves, joined as 19 joins them: one flat `&` over every leaf."""
    leaves = [t for d in domains for t in normalize(d) if t != '&']
    if any(t in ('|', '!') for t in leaves):
        raise Unsupported('a group whose domain is no conjunction')
    leaves = [t for t in leaves if t != TRUE_LEAF] or [TRUE_LEAF]
    return ['&'] * (len(leaves) - 1) + leaves


def json_key(v):
    """A group value as a key: a list ([id, name], [start, label]) by its first part."""
    return ('l', str(v[0])) if isinstance(v, list) else ('v', repr(v))
