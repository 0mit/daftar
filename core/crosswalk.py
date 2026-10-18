"""crosswalk — a foreign system's records read from a garden's statements, as core/law/crosswalks.yaml says (P5.3),
and as the garden's own rows beside them say (its VOCAB.md `crosswalks`, in their form: core/law.py `own_crosswalks`).

    from core import crosswalk
    crosswalk.records(root, 'odoo', '17.0', 'hr.department')   # [{id, name, parent_id: [id, name] | False, …}]

THE ONE READER of the crosswalks: daftard's answers to Odoo's client and any other reader take records from here, so
two readers can never disagree about what a record is. Nothing is written and nothing is kept: a record is read from
the beans each time it is asked for.

BOTH WAYS (2.12; MODEL.md, Imports and exports). A row that names its `format` and its `act` is read by `Carry` in
both directions: `into` writes a record's fields into the statements the row says, and `back` reads statements back
into records, each with what it did not carry. bin/import.py and bin/export.py are its two doors; what it reads and
writes is the row's, and nothing of a standard is known here by name.

A FIELD MAY READ WHAT A STATEMENT HOLDS AS ODOO WRITES IT: a position (`position: from | to | days | moment-from |
moment-to`: an extent's first or last day, the days it spans, or the first or last moment of its days in the garden's
zone, given in UTC), the records of a model a path reaches (`many`), or where the bean's course stands on its walk, by
the walk's own form (`stands`: no move yet, a step, a final step, an exit).

WHAT IS IN FORCE is read by core/inforce.py, the one reader of it: a path reads only statements that hold (their
`while`), and a `statements` form names the statements in force wherever they are written — one record each, the beans
they name, or (a field) what they say of the bean read. core/law/crosswalks.yaml says the forms.

A PATH MAY RUN THROUGH BEANS: `agree[as=employee].by/title` is the title of the bean the first step reaches. A filter
may name alternatives, `[by=tr-tckn|ir-national-code]`, so no one country's numbers stand above another's. A step that
names a statement (`<bean>#<id>`) reaches that statement: the next step, where it is of that statement's verb, reads it
alone — `use.of/hold.of` is what the allowance an absence uses holds, never the employment's first allowance — and one
of another verb reads the bean it is in, as `use.of/part.of` reads the employment's department.

A ROW MAY SELECT WHAT REACHES IT (`reached`), the other side of `within`: the beans the records of another model reach
by a path, through any of their statements its last step reads — an employment holds several allowances, each of one
kind of time off.

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
from core import formats  # noqa: F401 — the records a row reads and writes (2.12)
from core.check import garden_law
from core.inforce import InForce

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


def follow(bean, path, garden=None, unseal=None, held=False, every=False, holds=None):
    """What the path reads, from the bean: its title, summary or id, or the role of its first own statement of the verb
    that the filters allow; through each step but the last, what that step reaches (in `garden`, a {id: bean}) — a bean,
    or a statement in one (`<bean>#<id>`), and then the next step, where it is of that statement's verb, reads that
    statement alone (of another verb, the bean it is in) — None where any step reaches none. `held`: the last step reads
    sealed statements only, through `unseal`. `every`: the last step's role in each statement it reads, a list. `holds`
    (bean id, roles) -> bool: a statement it says no of is passed over at every step, as if it were not written
    (core/inforce.py)."""
    *through, last = steps(path)
    named = None                                        # the statement the step before reached, where it named one
    for step in through:
        nxt = read_step(bean, step, named, holds=holds)
        bid, _, named = nxt.partition('#') if isinstance(nxt, str) else (None, '', '')
        bean = (garden or {}).get(bid) if bid else None
        if bean is None:
            return [] if every else None
    return read_step(bean, last, named or None, unseal, held, every, holds)


def read_step(bean, step, named=None, unseal=None, held=False, every=False, holds=None):
    """What one step of a path reads from the bean (`follow`): where the step before named a statement of the bean
    (`named`, its id) of this step's verb, that statement alone; a statement `holds` says no of, never."""
    p = parse_path(step)
    if p is None:
        v = None if held else (bean.id if step == 'bean' else bean.header.get(step))
        return ([] if v is None else [v]) if every else v
    verb, filters, role = p
    hit = (getattr(bean, 'ids', None) or {}).get(named) if named else None
    out = []
    for _i, v, r in ([hit] if hit is not None and hit[1] == verb else bean.items):
        if v != verb or ('held' in r) != bool(held):
            continue
        if holds is not None and not holds(bean.id, r):
            continue
        if held:
            r = unseal(bean.id, v, r) if unseal else None
            if not isinstance(r, dict):
                continue
        if all(str(r.get(k)) in vals for k, vals in filters.items()) and role in r:
            if not every:
                return r[role]
            out.append(r[role])
    return out if every else None


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
        self.F = InForce(root, self.G, self.law)        # what is in force: every statement it reads holds, and those
        self.unseal = unseal                            # a `statements` form names are read through it
        self.zone = self.G.zone or zone_of(root)
        rows = [r for r in getattr(self.law, 'crosswalks', {}).values()
                if str(r.get('system')) == system and str(r.get('series')) == series]
        self.rows = {str(r['model']): r for r in rows}
        self._selected = {}
        self._reached = {}

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
        if isinstance(r.get('statements'), dict):      # A RECORD A STATEMENT: each in force, keyed `<bean>#<id>`
            for bid, roles in self.F.matching(r['statements']):
                if roles.get('id'):
                    out[f"{bid}#{roles['id']}"] = (self.G.beans[bid], roles)
            return self._number(model, out)
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
            if 'reached' in sel and bid not in self.reached(sel['reached']['along'], sel['reached']['model']):
                continue
            if 'named_in' in sel and not self.F.matching(sel['named_in'], naming=bid):
                continue
            out[bid] = b
        return self._number(model, out)

    def _number(self, model, out):
        ids = {}
        for key in out:
            n = number(model, key)
            if n in ids:
                raise Refused(f"{model}: {ids[n]} and {key} meet at one record number; rename one of them")
            ids[n] = key
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

    def reached(self, path, model):
        """{bean id}: the beans the records of the model reach by the path, through any of their statements its last
        step reads (each holding, as every path reads) — an employment holds several allowances, and reaches each one's
        kind of time off."""
        if (path, model) not in self._reached:
            self._reached[(path, model)] = {v.split('#', 1)[0] for o in self.selected(model).values()
                                            for v in self.follow(o, path, every=True) if isinstance(v, str)}
        return self._reached[(path, model)]

    def follow(self, bean, path, held=False, every=False):
        """What a path reads from a bean of this garden (`follow`), through the beans it holds: statements that hold."""
        return follow(bean, path, self.G.beans, self.unseal, held, every, lambda bid, r: self.F.holds(bid, r) is True)

    def display(self, model, bid):
        rec = self.record(model, bid, fields=('display_name', 'name'))
        return rec.get('display_name') or rec.get('name') or bid

    def record(self, model, bid, fields=None):
        r = self.row(model)
        b, roles = self.selected(model)[bid] if isinstance(r.get('statements'), dict) else (self.G.beans[bid], None)
        out = {'id': number(model, bid)}
        for name, spec in (r.get('fields') or {}).items():
            if fields is not None and name not in fields:
                continue
            v = self.field(model, b, spec, roles)
            out[name] = (spec['map'].get(str(v), False) if isinstance(spec.get('map'), dict) and not isinstance(v, (list, bool))
                         else v)
        return out

    def related(self, b, values, spec):
        """The records of the field's `model` that these values (each written in a statement of `b`) name: one, or
        (`many`) each; a value with no `model` is the value itself."""
        target = spec.get('model')
        if target is None:
            vals = [v for v in values if v is not None]
            return vals if spec.get('many') in (True, 'true') else (vals[0] if vals else False)
        hits = [self.F.names(b.id, v)[1] for v in values if v is not None]
        hits = [h for h in hits if h in self.selected(target)]
        if spec.get('many') in (True, 'true'):
            return [number(target, h) for h in hits]
        return [number(target, hits[0]), self.display(target, hits[0])] if hits else False

    def field(self, model, b, spec, roles=None):
        if isinstance(spec.get('statements'), dict):   # the statements in force, anywhere, that name this bean
            hits = self.F.matching(spec['statements'], naming=b.id)
            if spec.get('exists') in (True, 'true'):
                return bool(hits)
            return self.related(b, [r.get(spec.get('from')) for _b, r in hits], dict(spec, many=spec.get('many', True)))
        if roles is not None and str(spec.get('from', 'title')) not in OWN and not PATH.match(str(spec.get('from'))):
            v = roles.get(spec.get('from'))             # a role of the record's own statement
            return self.related(b, v if isinstance(v, list) else [v], spec) if 'model' in spec else \
                (False if v is None else v)
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


# ============================================================================ both ways (2.12)
BESIDE = ('while', 'why', 'note')


def _filters(text):
    """{role: value} of a `statements` form's `with` ("as=location,by=x")."""
    return {k.strip(): v.strip() for k, v in (f.split('=', 1) for f in str(text or '').split(',') if '=' in f)}


def _getp(d, path):
    for k in str(path).split('.'):
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def _setp(d, path, v):
    parts = str(path).split('.')
    for k in parts[:-1]:
        d = d.setdefault(k, {})
    d[parts[-1]] = v


class Carry:
    """One crosswalk row read both ways: a record into the statements it says (`into`), and statements back into its
    records (`back`), each with what it did not carry.

    `names(namespace, value)` gives the being a namespace names by the value, or None; `named_as(being, namespace)` the
    name it gives the being, for the way back; `schemes` the schemes a coding's system is the `url` of, [{scheme, url}].
    """

    def __init__(self, law, name, names=None, named_as=None, schemes=(), given_names=None):
        if name not in getattr(law, 'crosswalks', {}):
            raise Refused(f"the law has no crosswalk `{name}`")
        self.law, self.name, self.row = law, name, law.crosswalks[name]
        if self.row.get('format') is None:
            raise Refused(f"the crosswalk `{name}` says nothing of how its records come and go: it is read one way, "
                          f"into a system's client (core/crosswalk.py Reader)")
        self.fields = dict(self.row.get('fields') or {})
        st = self.row.get('statements')
        self.verb = st.get('verb') if isinstance(st, dict) else None
        self.filters = _filters(st.get('with')) if isinstance(st, dict) else {}
        self.names, self.named_as = names, named_as
        self.given_names = dict(given_names or {})          # field (or `*`) -> the namespace `named: given` reads
        self.by_url = {str(x.get('url')): str(x.get('scheme')) for x in schemes if isinstance(x, dict) and x.get('url')}
        self.url_of = {v: k for k, v in self.by_url.items()}
        self.compose = {str(k): str(v) for k, v in (self.row.get('compose') or {}).items()}
        self.given = {str(k): v for k, v in (self.row.get('given') or {}).items()}
        self._cache = {}                                   # what is read once a row: shapes, the self role, the order
        self._plain = set(self.fields)                     # a record holding only these, each a scalar, needs no leaves
        self._bean_field = next((f for f, sp in self.fields.items() if isinstance(sp, dict) and sp.get('from') == 'bean'),
                                None)
        self._paths = {}                                   # field -> (verb, its group's key, its filters, role)
        for f, sp in self.fields.items():
            if isinstance(sp, dict) and not self.verb and 'from' in sp and sp['from'] not in ('bean', 'title', 'summary') \
                    and PATH.match(str(sp['from'])):
                verb, flt, role = parse_path(str(sp['from']))
                one = {k: vs[0] for k, vs in flt.items()}
                self._paths[f] = (verb, (verb, tuple(sorted(one.items()))), one, role)
        self._named = {}                                   # a statement's group -> the roles fields of the row write in it
        for f, (verb, key, one, role) in self._paths.items():
            self._named.setdefault(key, set()).update({role} | set((self.fields[f].get('with') or {})))
        if self.verb:
            self._named[(self.verb, tuple(sorted(self.filters.items())))] = {
                str(sp['from']).split('.')[0] for sp in self.fields.values() if isinstance(sp, dict) and 'from' in sp
                and sp['from'] not in ('bean', 'title', 'summary')}

    # -------------------------------------------------------------------------------------------- the law's verbs
    def _row(self, verb):
        return self.law.verbs.get(verb) or {}

    def _shapes(self, verb, role):
        key = ('shapes', verb, role)
        if key not in self._cache:
            spec = (self._row(verb).get('roles') or {}).get(role) or (self._row(verb).get('qualifiers') or {}).get(role)
            sh = spec.get('shape') if isinstance(spec, dict) else None
            self._cache[key] = sh if isinstance(sh, list) else [sh] if sh else []
        return self._cache[key]

    def _self_role(self, verb, roles):
        """The role `self` fills: the row's `self`, or the one required role of a being the verb leaves."""
        key = ('self', verb, frozenset(roles))
        if key not in self._cache:
            if self.row.get('self'):
                got = self.row['self'] if self.row['self'] not in roles else None
            else:
                left = [r for r in (self._row(verb).get('required') or []) if r not in roles
                        and 'being' in self._shapes(verb, r)]
                got = left[0] if len(left) == 1 else None
            self._cache[key] = got
        return self._cache[key]

    def _ordered(self, verb, roles):
        key = ('order', verb, tuple(roles))
        if key not in self._cache:
            r = self._row(verb)
            order = ['id'] + list(r.get('roles') or {}) + list(r.get('qualifiers') or {}) + list(BESIDE)
            self._cache[key] = sorted(roles, key=lambda k: order.index(k) if k in order else len(order))
        return {k: roles[k] for k in self._cache[key]}

    # -------------------------------------------------------------------------------------------- a field's value
    def _read(self, fname, spec, raw, rec, notes):
        """(the value carried, the record's leaves it used) of one field, or (None, why) where it is not carried."""
        from core import formats
        conv, arg, opts = formats.conversion(spec.get('as'))
        v = raw
        if isinstance(spec.get('map'), dict):                    # a value the system writes, as the law's
            inv = {str(b): a for a, b in spec['map'].items()}
            if str(v) not in inv:
                return None, f"{v!r} is a value the crosswalk does not map"
            v = inv[str(v)]
        if conv is None:
            return (str(v) if not isinstance(v, (dict, list)) else v), None
        if conv == 'escaped':
            return formats.escape(v if isinstance(v, (bytes, bytearray, memoryview)) else str(v)), None
        if conv == 'decimal':
            return str(v), None
        if conv == 'form':
            m = re.fullmatch(re.escape(str(arg)).replace(r'\{\}', '(.+)'), str(v))
            return (m.group(1), None) if m else (None, f"{v!r} is not in the form {arg}")
        if conv == 'coding':
            sysv, code = (v.get('system'), v.get('code')) if isinstance(v, dict) else (None, None)
            if not (sysv and code) or str(sysv) not in self.by_url:
                return None, f"a coding of {sysv!r}, which no scheme here has for its url"
            return f"{self.by_url[str(sysv)]}:{code}", {f"{fname}.system", f"{fname}.code"}
        if conv == 'moment':
            got, note = formats.moment_in(v, arg)
            if got is None:
                return None, note
            if note:
                notes.append((fname, note))
            return got, None
        if conv == 'named':
            if str(v) in [str(x) for x in (opts.get('none') or [])]:
                return '', None                                   # the system's way of saying it has none
            ns = arg if arg != 'given' else (self.given_names.get(fname) or self.given_names.get('*'))
            if ns is None:
                notes.append((fname, f"no namespace is given to look {v!r} up in (`--named`)"))
                return 'unknown', None
            arg = ns
            hit = self.names(str(arg), str(v)) if self.names else None
            if hit is None:
                hints = ', '.join(f"{h} {formats.get(rec, h)!r}" for h in (opts.get('hint') or [])
                                  if formats.get(rec, h) is not None)
                notes.append((fname, f"no being {arg} names {v!r}" + (f" ({hints})" if hints else '')))
                return 'unknown', None
            return hit, None
        if conv == 'prefix':
            return f"{arg}{v}", None
        if conv == 'part':
            return str(v), None
        return None, f"`{conv}` is no conversion this release reads"

    def _compiled(self):
        """The row's fields as a plan read once: (field, spec, kind, …) — what `into` does for every record."""
        if 'plan' in self._cache:
            return self._cache['plan']
        from core import formats
        plan = []
        for fname, spec in self.fields.items():
            if not isinstance(spec, dict):
                continue
            conv = formats.conversion(spec.get('as'))[0]
            frm = str(spec.get('from', ''))
            kind = 'drop' if 'drop' in spec else 'value' if 'value' in spec else \
                'part' if spec.get('part') is not None else 'bean' if frm == 'bean' else \
                'own' if frm in ('title', 'summary') else 'role' if self.verb else 'path'
            plain = conv is None and not isinstance(spec.get('map'), dict)
            plan.append((fname, spec, kind, frm, plain, '.' in fname or '[' in fname))
        self._cache['plan'] = plan
        return plan

    def into(self, rec):
        """(being, [(verb, roles)], [(field, why)] not carried, [(field, note)], {act role: value}, header) of one
        record: the statements the row says, each in its verb's order; a being of None where the record names none."""
        from core import formats
        listed, notes, used, vals, parts = [], [], set(), {}, {}
        for fname, spec, kind, frm, plain, deep in self._compiled():
            raw = formats.get(rec, fname) if deep else rec.get(fname)
            if raw is None:
                continue
            if kind == 'drop':
                used.add(fname)
                continue
            if kind == 'value':
                if str(raw) == str(spec['value']):
                    used.add(fname)
                continue
            if plain:
                v, why = (raw if isinstance(raw, (dict, list)) else str(raw)), None
            else:
                v, why = self._read(fname, spec, raw, rec, notes)
                if v is None:
                    listed.append((fname, why))
                    continue
            if why is None:
                used.add(fname)
            else:
                used |= why
            if kind == 'part':
                parts.setdefault(frm, {})[str(spec['part'])] = (fname, v)
            else:
                vals[fname] = v
        being = vals.get(self._bean_field) if self._bean_field else None
        if not being:
            return None, [], listed, notes, {}, {}
        header = {}
        groups = {}                                                 # (verb, filters) -> roles

        def group(verb, filters):
            key = (verb, tuple(sorted(filters.items())))
            got = groups.get(key)
            if got is None:
                got = groups[key] = dict(filters)
            return got
        if self.verb:
            group(self.verb, self.filters)
        for fname, spec, kind, frm, _plain, _deep in self._compiled():
            if fname not in vals or kind in ('bean', 'part'):
                continue
            v = vals[fname]
            if kind == 'own':
                header[frm] = v
                continue
            if v == '':
                continue
            if spec.get('unit') is not None:
                v = {'count': v, 'unit': str(spec['unit'])}
            if kind == 'role':
                _setp(group(self.verb, self.filters), frm, v)
                continue
            verb, key, one, role = self._paths[fname]
            roles = groups.get(key)
            if roles is None:
                roles = groups[key] = dict(one)
            roles[role] = v
            for r2, f2 in (spec.get('with') or {}).items():
                if f2 in vals:
                    roles[r2] = vals[f2]
        for path, form in self.compose.items():                    # a value made of its parts
            got = parts.get(path, {})
            want = re.findall(r'\{(\w+)\}', form)
            if all(w in got for w in want):
                if self.verb:
                    _setp(group(self.verb, self.filters), path, form.format(**{w: got[w][1] for w in want}))
                used |= {got[w][0] for w in want}
            else:
                listed += [(got[w][0], f"a part of {path}, whose other parts are not all there") for w in got]
        out = []
        for (verb, _f), roles in groups.items():
            for path, v in self.given.items():                     # what every statement written has
                parent = path.rsplit('.', 1)[0] if '.' in path else ''
                if not parent or _getp(roles, parent) is not None:
                    _setp(roles, path, v)
            for role in list(roles):                                # a count with no unit the law has is no value
                q = roles[role]
                if isinstance(q, dict) and 'count' in q and 'quantity' in self._shapes(verb, role):
                    unit = q.get('unit')
                    if unit is None or self.law.has('units', str(unit)):
                        why = f"a count of {unit!r}, which is no unit of the law" if unit else "a count with no unit"
                        feeding = [f for f, sp in self.fields.items() if isinstance(sp, dict)
                                   and str(sp.get('from', '')).split('.')[0] == role and f in vals]
                        listed += [(f, why) for f in feeding]
                        used -= set(feeding)
                        del roles[role]
            if not any(k not in self.filters for k in roles):
                continue
            for role in (self._row(verb).get('required') or []):    # one a field writes, the record not holding it:
                if role not in roles and role in self._named.get((verb, _f), ()):     # `unknown`, where nobody said
                    roles[role] = 'unknown'
            sr = self._self_role(verb, roles)
            if sr:
                roles[sr] = 'self'
            out.append((verb, self._ordered(verb, roles)))
        act = {}
        for role, f in (self.row.get('act') or {}).items():
            if role not in ('verb', 'per') and formats.get(rec, str(f)) is not None:
                act[role] = formats.get(rec, str(f))
                used.add(str(f))
        if not listed and len(used) == len(rec) and rec.keys() <= self._plain and \
                not any(isinstance(x, (dict, list)) for x in rec.values()):
            return being, out, listed, notes, act, header           # every value read: nothing to list
        named = {x for x, _w in listed}
        for leaf in formats.leaves(rec):                            # the account: every value read, or listed
            if leaf in used or leaf in named or any(leaf.startswith(u + '.') or leaf.startswith(u + '[') for u in used):
                continue
            listed.append((leaf, 'no field of the crosswalk reads it'))
        return being, out, listed, notes, act, header

    # -------------------------------------------------------------------------------------------- and back
    def _out(self, fname, spec, v):
        """A value of the law's, written as the system writes the field — or None where it cannot be."""
        from core import formats
        conv, arg, _o = formats.conversion(spec.get('as'))
        if isinstance(spec.get('map'), dict):
            if str(v) not in {str(k) for k in spec['map']}:
                return None
            v = {str(k): x for k, x in spec['map'].items()}[str(v)]
        if conv == 'decimal':
            from decimal import Decimal, InvalidOperation
            try:
                return Decimal(str(v))
            except InvalidOperation:
                return None
        if conv == 'form':
            return str(arg).replace('{}', str(v))
        if conv == 'coding':
            from core import engine as _e
            sch, _sep, code = str(v).partition(':')
            return {'system': self.url_of[sch], 'code': code} if sch in self.url_of and code else None
        if conv == 'moment':
            return formats.moment_out(v, arg)
        if conv == 'named':
            ns = arg if arg != 'given' else (self.given_names.get(fname) or self.given_names.get('*'))
            return self.named_as(str(v), str(ns)) if self.named_as and ns and v not in ('unknown', None) else None
        if conv == 'prefix':
            return None
        return v

    def back(self, being, statements):
        """[(record, [what of the statements it did not carry])] of a being's statements, each `(verb, roles)` as its bean
        writes them: one record a statement of the row's verb that its filters let through, or one record of the being."""
        from core import formats
        out = []
        if self.verb:
            todo = [(v, r) for v, r in statements if v == self.verb
                    and all(str(r.get(k)) == str(x) for k, x in self.filters.items())]
        else:
            todo = [(None, None)]
        for verb, roles in todo:
            rec, used = {}, set()
            for fname, spec in self.fields.items():
                if not isinstance(spec, dict) or 'drop' in spec:
                    continue
                if 'value' in spec:
                    continue
                frm = str(spec.get('from'))
                if frm == 'bean':
                    v = self._out(fname, spec, being)
                elif self.verb:
                    if spec.get('part') is not None:
                        whole = _getp(roles, frm)
                        form = self.compose.get(frm)
                        m = re.fullmatch(re.sub(r'\\\{(\w+)\\\}', r'(?P<\1>.+?)', re.escape(form)), str(whole)) \
                            if whole is not None and form else None
                        v = m.group(str(spec['part'])) if m else None
                        if m:
                            used.add(frm)
                    else:
                        v = _getp(roles, frm)
                        if isinstance(v, dict) and spec.get('unit') is not None:
                            v = v.get('count')
                        if v is not None:
                            used.add(frm)
                        v = self._out(fname, spec, v) if v is not None else None
                else:
                    p = parse_path(frm)
                    if p is None:
                        continue
                    pverb, flt, role = p
                    hit = next((r for vv, r in statements if vv == pverb
                                and all(str(r.get(k)) in vs for k, vs in flt.items()) and role in r), None)
                    v = hit.get(role) if hit else None
                    if isinstance(v, dict) and spec.get('unit') is not None:
                        v = v.get('count')
                    v = self._out(fname, spec, v) if v is not None else None
                if v is None or v == '':
                    continue
                formats.put(rec, fname, v)
            for fname, spec in self.fields.items():                 # a value every record of the system has
                if isinstance(spec, dict) and 'value' in spec and rec:
                    formats.put(rec, fname, spec['value'])
            missed = []
            if self.verb:
                for leaf, x in formats.leaves(roles).items():
                    if leaf in self.filters or x == 'self' or (leaf in self.given and str(x) == str(self.given[leaf])):
                        continue
                    if any(leaf == u or leaf.startswith(u + '.') for u in used):
                        continue
                    missed.append(leaf)
            out.append((rec, missed))
        return out


if __name__ == '__main__':
    import json
    import sys
    if len(sys.argv) != 4:
        sys.exit('usage: python3 -m core.crosswalk <system> <series> <model>   (in a garden)')
    print(json.dumps(records(os.getcwd(), *sys.argv[1:]), ensure_ascii=False, indent=1))
