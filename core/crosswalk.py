"""crosswalk — a foreign system's records read from a garden's statements, as core/law/crosswalks.yaml says (P5.3).

    from core import crosswalk
    crosswalk.records(root, 'odoo', '17.0', 'hr.department')   # [{id, name, parent_id: [id, name] | False, …}]

THE ONE READER of the crosswalks: daftard's answers to Odoo's client and any other reader take records from here, so
two readers can never disagree about what a record is. Nothing is written and nothing is kept: a record is read from
the beans each time it is asked for.

A FIELD MAY READ WHAT A STATEMENT HOLDS AS ODOO WRITES IT: a position (`position: from | to | days | moment-from |
moment-to`: an extent's first or last day, the days it spans, or the first or last moment of its days in the garden's
zone, given in UTC), the records of a model a path reaches (`many`), or where the bean's course stands on its walk, by
the walk's own form (`stands`: no move yet, a step, a final step, an exit).

A PATH MAY RUN THROUGH BEANS: `agree[as=employee].by/title` is the title of the bean the first step reaches. A filter
may name alternatives, `[by=tr-tckn|ir-national-code]`, so no one country's numbers stand above another's.

WHAT IS HELD IS NEVER READ FROM GIT. A field marked `held` is read only from sealed statements (MODEL: what harm can come
of, git does not keep), through what the host that keeps them resolves: `unseal(bean, verb, sealed roles)` gives what a
sealed statement said, or None. A reader handed no `unseal` reads no held field: it is empty, as what the garden does
not say. Which reader a host resolves them for is the host's to ask of the garden's grants, never this reader's.

A record's `id` is a number the system's client can hold, the same for a bean every time and on every machine: the
first 31 bits of the SHA-256 of `<model>:<bean>`. Two beans whose numbers meet are refused, by name, never guessed.
"""
import hashlib
import os
import re

from core import engine
from core.check import garden_law

PATH = re.compile(r'^(?P<verb>[a-z][a-z-]*)(\[(?P<filters>[a-z-]+=[^,\]]+(,[a-z-]+=[^,\]]+)*)\])?\.(?P<role>[a-z]+)$')
OWN = ('title', 'summary', 'bean')


class Refused(Exception):
    """What cannot be read as asked: said, never guessed."""


def parse_path(path):
    """(verb, {role: (value, …)}, role) of a statement path, or None where it is the bean's own title, summary or id."""
    if path in OWN:
        return None
    m = PATH.match(str(path))
    if not m:
        raise Refused(f"{path!r} is no path: title, summary, bean, or <verb>[<role>=<value>,…].<role>")
    filters = {k: tuple(v.split('|')) for k, v in (f.split('=', 1) for f in (m.group('filters') or '').split(',') if f)}
    return m.group('verb'), filters, m.group('role')


def steps(path):
    """The steps of a path, split at each `/` outside a filter's brackets: each but the last reaches a bean, through the
    role it reads."""
    out, depth, cur = [], 0, ''
    for c in str(path):
        depth += (c == '[') - (c == ']')
        if c == '/' and depth == 0:
            out.append(cur)
            cur = ''
        else:
            cur += c
    return out + [cur]


def follow(bean, path, garden=None, unseal=None, held=False):
    """What the path reads, from the bean: its title, summary or id, or the role of its first own statement of the verb
    that the filters allow; through each step but the last, the bean that step reaches (in `garden`, a {id: bean}) —
    None where any step reaches none. `held`: the last step reads sealed statements only, through `unseal`."""
    *through, last = steps(path)
    for step in through:
        nxt = follow(bean, step)
        nxt = nxt.split('#', 1)[0] if isinstance(nxt, str) else None     # a statement's bean, where it names one
        bean = (garden or {}).get(nxt) if nxt else None
        if bean is None:
            return None
    p = parse_path(last)
    if p is None:
        return None if held else (bean.id if last == 'bean' else bean.header.get(last))
    verb, filters, role = p
    for _i, v, r in bean.items:
        if v != verb or ('held' in r) != bool(held):
            continue
        if held:
            r = unseal(bean.id, v, r) if unseal else None
            if not isinstance(r, dict):
                continue
        if all(str(r.get(k)) in vals for k, vals in filters.items()) and role in r:
            return r[role]
    return None


def zone_of(root):
    """The zone a garden reckons its days in (GARDEN.md `zone`), or None."""
    try:
        from core import read
        return read.document(os.path.join(root, 'GARDEN.md'))[0].get('zone') if root else None
    except Exception:
        return None


def position(value, how, systems, zone=None):
    """A position (one, or an extent) as Odoo writes it, read by the law's one reader of positions (core/frame.py) in
    its `systems`: `from`/`to` its first or last day (YYYY-MM-DD, Gregorian, whatever calendar wrote it), `days` how
    many days it spans, both ends counted, `moment-from`/`moment-to` its first or last moment — a day's first or last in
    `zone` — in UTC (YYYY-MM-DD HH:MM:SS). False where it is no position of a calendar."""
    import datetime
    from core import frame
    dmcal = engine.dmcal
    try:
        p = frame.read(str(value), systems, zone)
    except frame.Refused:
        return False
    tz = None
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo(str(zone or 'UTC'))
    except Exception:
        return False

    def utc(q):                                         # a moment it names, as a UTC datetime
        return datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc) + \
            datetime.timedelta(milliseconds=q.moment - dmcal.UNIX_DAY * dmcal.DAY_MS)

    def day(q):                                         # its day number: a day's own, or a moment's day in the zone
        if q.day is not None:
            return q.day
        return datetime.date.toordinal(utc(q).astimezone(tz).date()) if q.moment is not None else None
    first, last = p, p.end or p
    d0, d1 = day(first), day(last)
    if d0 is None or d1 is None:
        return False
    if how == 'days':
        return d1 - d0 + 1
    if how in ('from', 'to'):
        return '%04d-%02d-%02d' % dmcal.g_from_day(d0 if how == 'from' else d1)
    if how in ('moment-from', 'moment-to'):
        q = first if how == 'moment-from' else last
        if q.moment is not None:
            t = utc(q)
        else:
            y, m, d = dmcal.g_from_day(q.day)
            t = datetime.datetime(y, m, d) + (datetime.timedelta(0) if how == 'moment-from' else
                                              datetime.timedelta(hours=23, minutes=59, seconds=59))
            t = t.replace(tzinfo=tz).astimezone(datetime.timezone.utc)
        return t.strftime('%Y-%m-%d %H:%M:%S')
    return False


def number(model, bean_id):
    return int.from_bytes(hashlib.sha256(f'{model}:{bean_id}'.encode('utf-8')).digest()[:4], 'big') & 0x7fffffff


class Reader:
    """The crosswalks of one system and series over one garden, read once."""

    def __init__(self, root, system, series, law=None, garden=None, unseal=None):
        self.law = law or garden_law(root)
        self.G = garden or engine.Garden.read(root)
        self.unseal = unseal
        self.zone = self.G.zone or zone_of(root)
        rows = [r for r in getattr(self.law, 'crosswalks', {}).values()
                if str(r.get('system')) == system and str(r.get('series')) == series]
        self.rows = {str(r['model']): r for r in rows}
        self._selected = {}

    def row(self, model):
        r = self.rows.get(model)
        if r is None:
            raise Refused(f"the law has no crosswalk of {model} for this series")
        return r

    def selected(self, model):
        """{bean id: bean} the row of the model selects, in the order of their ids."""
        if model in self._selected:
            return self._selected[model]
        self._selected[model] = {}                      # a row that selects through itself sees nothing of itself yet
        r = self.row(model)
        sel = r.get('select') or {}
        out = {}
        for bid in sorted(self.G.beans):
            b = self.G.beans[bid]
            if b.kind != r.get('kind') or getattr(b, 'unread', False):
                continue
            if 'with' in sel and self.follow(b, sel['with']) is None:
                continue
            if 'without' in sel and self.follow(b, sel['without']) is not None:
                continue
            if 'within' in sel and self.reach(b, sel['within']['along'], sel['within']['model']) is None:
                continue
            out[bid] = b
        ids = {}
        for bid in out:
            n = number(model, bid)
            if n in ids:
                raise Refused(f"{model}: {ids[n]} and {bid} meet at one record number; rename one of them")
            ids[n] = bid
        self._selected[model] = out
        return out

    def reach(self, bean, path, model):
        """The first bean the model's row selects, reached by following the path from the bean (never the bean itself)."""
        seen, here = {bean.id}, bean
        while True:
            nxt = self.follow(here, path)
            nxt = nxt.split('#', 1)[0] if isinstance(nxt, str) else nxt
            if not isinstance(nxt, str) or nxt in seen or nxt not in self.G.beans:
                return None
            if nxt in self.selected(model):
                return nxt
            seen.add(nxt)
            here = self.G.beans[nxt]

    def follow(self, bean, path, held=False):
        """What a path reads from a bean of this garden (`follow`), through the beans it holds."""
        return follow(bean, path, self.G.beans, self.unseal, held)

    def display(self, model, bid):
        rec = self.record(model, bid, fields=('display_name', 'name'))
        return rec.get('display_name') or rec.get('name') or bid

    def record(self, model, bid, fields=None):
        r, b = self.row(model), self.G.beans[bid]
        out = {'id': number(model, bid)}
        for name, spec in (r.get('fields') or {}).items():
            if fields is not None and name not in fields:
                continue
            out[name] = self.field(model, b, spec)
        return out

    def field(self, model, b, spec):
        if 'value' in spec:
            v = spec['value']
            return {'true': True, 'false': False}.get(v, v) if isinstance(v, str) else v
        if 'stands' in spec:
            return self.stands(b, spec['stands'])
        path = spec.get('from', 'title')
        target = spec.get('model')
        held = spec.get('held') in (True, 'true')
        if 'position' in spec:
            v = self.follow(b, path)
            return False if v is None else position(v, spec['position'], self.law.systems, self.zone)
        if spec.get('many') in (True, 'true') and target is not None:
            v = self.follow(b, path)
            hits = [str(x).split('#', 1)[0] for x in (v if isinstance(v, list) else [v]) if isinstance(x, str)]
            return [number(target, h) for h in hits if h in self.selected(target)]
        if spec.get('join') is not None:                # titles along the path within this model, farthest first
            names, seen, here = [self.follow(b, path)], {b.id}, b
            while True:
                up = self.follow(here, spec.get('along'))
                if not isinstance(up, str) or up in seen or up not in self.selected(model):
                    break
                seen.add(up)
                here = self.G.beans[up]
                names.insert(0, self.follow(here, path))
            return str(spec['join']).join(str(n) for n in names if n is not None)
        if target is None:
            v = self.follow(b, path, held)
            return False if v is None else v
        if spec.get('inverse') in (True, 'true'):
            return [number(target, oid) for oid, o in self.selected(target).items() if self.follow(o, path) == b.id]
        hit = self.reach(b, path, target) if spec.get('chain') in (True, 'true') else self.follow(b, path)
        hit = hit.split('#', 1)[0] if isinstance(hit, str) else hit       # a statement's bean, where it names one
        if not isinstance(hit, str) or hit not in self.selected(target):
            return False
        return [number(target, hit), self.display(target, hit)]

    def stands(self, b, kinds):
        """Where the bean's course stands on its walk, by the walk's own form (core/lines.py, the walk's one reading):
        `none` before its first move, `final` or `exit` at such a step, `step` at any other — each given as `kinds`
        names it. A course on a walk this reader does not hold stands nowhere it can say: False."""
        from core import lines
        courses = lines.courses_of(b, self.G)
        if not courses:
            placed = any(v == 'be' and r.get('as') == 'order' for _i, v, r in b.items)
            return False if placed else kinds.get('none', False)
        cid, course = next(iter(courses.items()))
        moves = [m for _i, m in lines.moves_of(b) if m.get('course') == cid]
        if not moves:
            return kinds.get('none', False)
        st = next((s for s in lines.steps_of(self.G.beans[course['walk']]) if s.get('id') == moves[-1].get('step')), {})
        return kinds.get('final' if st.get('final') else 'exit' if st.get('exit') else 'step', False)

    def records(self, model, beans=None):
        """Every record of the model, or those of the beans named."""
        sel = self.selected(model)
        return [self.record(model, bid) for bid in sel if beans is None or bid in beans]


def records(root, system, series, model, beans=None):
    """Every record of `model` the garden at `root` holds, as the law's crosswalk of it reads them."""
    return Reader(root, system, series).records(model, beans)


def models(root, system, series):
    """The models the law crosses for that series."""
    return sorted(Reader(root, system, series).rows)


if __name__ == '__main__':
    import json
    import sys
    if len(sys.argv) != 4:
        sys.exit('usage: python3 -m core.crosswalk <system> <series> <model>   (in a garden)')
    print(json.dumps(records(os.getcwd(), *sys.argv[1:]), ensure_ascii=False, indent=1))
