"""inforce — WHAT IS IN FORCE in a garden, read once: a statement while it holds, a decision once its course stands at its
walk's final step, less what a statement of an ending verb ends, and, where asked, while its standing on the square
allows it. core/crosswalk.py reads through it, and so does a walk's tool, so no two of them can disagree about what
holds. (bin/routines.py still reads a need's `while` by itself: seed/RATIONALE.md says so.)

    from core.inforce import InForce
    F = InForce(root)                          # the garden at root, read once
    F.holds(bean, roles)                       # True, False, or None: not known
    F.decisions(walk, include=None)            # [bean]: the decisions in force on the walk, in the order they came in
    F.ended(bean, roles, verb, among=None)     # True where a statement of `verb` ends it
    F.standing(bean, roles)                    # True while a permitted (or obligatory) of it holds and no forbidden does
    F.in_force(bean, roles, among, ended_by, standing)   # all of these at once
    F.matching(spec, naming=None)              # [(bean, roles)] the statements a crosswalk's `statements` form names
    F.policy(walk, include, verbs, ended_by)   # a walk tool's statements: those of the decisions in force on its walk
    InForce(root, assume={'<bean>#<reckon id>'})   # the garden as it would stand once those readings hold: the plan's

A STATEMENT HOLDS (core/law/core.yaml `while`) with no `while`, or while what its `while` names holds: another statement,
which holds while it is there and its own `while` holds, or a reading (`reckon`), read by bin/reckon.py, the one reader of
readings. A `while` naming a condition of the law (`ensemble`) says what the statement holds of, not when: it holds. A
reading that cannot be read is not known (None), never guessed, and the caller says what not known is to it: an account
is not made (a walk's tool), a record does not show it (core/crosswalk.py).

A DECISION is a bean placed on a walk (`be … as: order`). It is IN FORCE once its course stands at a step its walk marks
final (`walk: { final: true }`), never by a step's name, and decisions come into force in the order of their courses'
last moves. A walk's tool adds the request it is planning last (`include`): the garden as it would stand after it.
Where a request's statements are held `while` a reading of its course (the course reaching its end), the tool reads the
garden after it by `assume`: those readings taken as holding, every other read as it is.

WHAT ENDS A STATEMENT is a statement of a verb the caller names (`ended_by`). The law's own verbs end nothing of
themselves, and a garden's ending verb (`revoke`, `withdraw`) is its own row until the standard carries one. The ending
statement names the statement (`<bean>#<id>`, or its id in its own bean) or its bean (`self`, or the bean's id) in `of`;
it holds; it is among the decisions in force, where the caller asks of a walk; and its day (`at`), where it says one, has
come in the garden's zone.

ITS STANDING on the square: where asked, a statement counts while a `permitted` or an `obligatory` of it holds and no
`forbidden` of it holds or is not known to hold. Each of the three is read as any statement is, wherever it is written.
"""
import collections
import os

from core import engine, lines

Policy = collections.namedtuple('Policy', 'order kept ended dangling unknown')
POSITIONS = ('permitted', 'obligatory', 'forbidden')


def filters_of(text):
    """{role: (value, …)} of a filter `<role>=<value>[|<value>…],…` (a crosswalk path's own filter form)."""
    out = {}
    for f in str(text or '').split(','):
        if '=' in f:
            k, v = f.split('=', 1)
            out[k.strip()] = tuple(x.strip() for x in v.split('|'))
    return out


class InForce:
    """What is in force in one garden, read once: each `while` read at most once, each decision at most once."""

    def __init__(self, root, G=None, law=None, today=None, assume=()):
        self.root = root
        self.G = G or engine.Garden.read(root)
        self.assume = set(assume)                   # readings (`<bean>#<id>`) taken as holding: a plan's world
        self._law = law
        self._today = today                         # a day number of the law's calendar, or None: today, in the zone
        self._holds, self._by_verb, self._conditions = {}, None, None

    # ---------------------------------------------------------------------------------------------- the garden read
    @property
    def law(self):
        if self._law is None:
            from core.check import garden_law
            self._law = garden_law(self.root)
        return self._law

    def by_verb(self, verb):
        """[(bean id, roles)] of every statement of `verb` in the garden, in the order of the beans and their items."""
        if self._by_verb is None:
            self._by_verb = collections.defaultdict(list)
            for bid in sorted(self.G.beans):
                for _i, v, r in self.G.beans[bid].items:
                    self._by_verb[v].append((bid, r))
        return self._by_verb.get(verb, [])

    def statement(self, ref, bean=None):
        """(bean id, verb, roles) of `<bean>#<id>`, or of a bare id in `bean`; None where there is none."""
        b, sid = ref.split('#', 1) if '#' in ref else (bean, ref)
        B = self.G.beans.get(b)
        for _i, v, r in (B.items if B is not None else []):
            if r.get('id') == sid:
                return b, v, r
        return None

    def names(self, bean, x):
        """What `x`, written in a role of a statement of `bean`, names: ('bean', id) or ('statement', '<bean>#<id>')."""
        x = str(x)
        if x == 'self':
            return 'bean', bean
        if '#' in x:
            return 'statement', x
        if self.statement(x, bean) is not None:
            return 'statement', f"{bean}#{x}"
        return 'bean', x

    # ---------------------------------------------------------------------------------------------- while it holds
    def holds(self, bean, roles, _seen=()):
        """True, False, or None (not known): whether the statement holds now, by its `while`."""
        w = roles.get('while') if isinstance(roles, dict) else None
        if w is None:
            return True
        w = str(w)
        if self._conditions is None:
            self._conditions = set(getattr(self.law, 'conditions', ()) or ())
        if w in self._conditions:
            return True
        ref = w if '#' in w else f"{bean}#{w}"
        if ref in _seen:
            return False                            # a condition that holds only while it holds holds nothing
        if ref not in self._holds:
            hit = self.statement(ref)
            if hit is None:
                res = False
            elif hit[1] == 'reckon':
                res = True if ref in self.assume else self._reading(ref)
            else:
                res = self.holds(hit[0], hit[2], _seen + (ref,))
            self._holds[ref] = res
        return self._holds[ref]

    def _reading(self, ref):
        try:
            import reckon as dmreckon
            v = dmreckon.holds(ref, root=self.root)
        except Exception:  # noqa: BLE001 — a reading nobody can read is not known: said by None, never guessed
            return None
        return v if v in (True, False, None) else bool(v)

    # ---------------------------------------------------------------------------------------------- decisions
    def decisions(self, walk, include=None):
        """[bean id] of the decisions in force on `walk`, in the order they came into force; `include` last."""
        W = self.G.beans.get(walk)
        steps = {s.get('id'): s for s in lines.steps_of(W)} if W is not None else {}
        found = []
        for bid in sorted(self.G.beans):
            if bid == include:
                continue
            b = self.G.beans[bid]
            for cid, c in lines.courses_of(b, self.G).items():
                if c.get('walk') != walk:
                    continue
                moves = [m for _i, m in lines.moves_of(b) if m.get('course') == cid]
                if moves and _true((steps.get(moves[-1].get('step')) or {}).get('final')):
                    found.append((_moment(moves[-1].get('at')), bid))
                    break
        order = [bid for _at, bid in sorted(found)]
        return order + ([include] if include and include not in order else [])

    # ---------------------------------------------------------------------------------------------- what ends it
    def ended(self, bean, roles, verb, among=None):
        """Whether a statement of `verb` ends the statement (or its bean): it names it in `of`, holds, is among the
        decisions given (`among`, where given), and its day, where it says one, has come."""
        sid = roles.get('id') if isinstance(roles, dict) else None
        mine = {('bean', bean)} | ({('statement', f"{bean}#{sid}")} if sid else set())
        for b, r in self.by_verb(verb):
            if among is not None and b not in among:
                continue
            of = r.get('of')
            if not any(self.names(b, x) in mine for x in (of if isinstance(of, list) else [of]) if x is not None):
                continue
            if self.holds(b, r) is not True:
                continue
            if r.get('at') is not None and not self.come(r['at']):
                continue
            return True
        return False

    def ends_nothing(self, verb, among):
        """[`<bean>#<id>` or `<bean>`] that a statement of `verb` among the decisions names and no decision among them
        holds: an ending that ends nothing in force."""
        present = {('bean', b) for b in among}
        for b in among:
            present |= {('statement', f"{b}#{r.get('id')}") for _i, _v, r in self.G.beans[b].items if r.get('id')}
        out = []
        for b, r in self.by_verb(verb):
            if b not in among:
                continue
            of = r.get('of')
            for x in (of if isinstance(of, list) else [of]):
                if x is not None and self.names(b, x) not in present:
                    out.append(self.names(b, x)[1])
        return sorted(set(out))

    def come(self, at):
        """Whether a position's first day (or its moment) has come, in the garden's zone; a position that does not read
        has not."""
        import time
        from core import frame
        try:
            p = frame.read(str(at), self.law.systems, self.G.zone)
        except Exception:  # noqa: BLE001
            return False
        if p.day is not None:
            return p.day <= self.today()
        if p.moment is not None:                    # the calendar's milliseconds, from its day 0
            return p.moment - engine.dmcal.UNIX_DAY * engine.dmcal.DAY_MS <= time.time() * 1000
        return False

    def today(self):
        """Today's day number (a proleptic Gregorian ordinal, as bin/cal.py counts days) in the garden's zone."""
        if self._today is None:
            import datetime
            try:
                from zoneinfo import ZoneInfo
                self._today = datetime.datetime.now(ZoneInfo(str(self.G.zone or 'UTC'))).date().toordinal()
            except Exception:  # noqa: BLE001 — a zone nobody can read: the machine's day
                self._today = datetime.date.today().toordinal()
        return self._today

    # ---------------------------------------------------------------------------------------------- its standing
    def standing(self, bean, roles):
        """Whether a permitted or obligatory of the statement holds, and no forbidden of it holds or may hold."""
        sid = roles.get('id') if isinstance(roles, dict) else None
        if not sid:
            return False                            # a statement no other can name has no standing to read
        me = ('statement', f"{bean}#{sid}")
        allowed = barred = False
        for verb in POSITIONS:
            for b, r in self.by_verb(verb):
                of = r.get('of')
                if not any(self.names(b, x) == me for x in (of if isinstance(of, list) else [of]) if x is not None):
                    continue
                h = self.holds(b, r)
                if verb == 'forbidden':
                    barred = barred or h is not False
                else:
                    allowed = allowed or h is True
        return allowed and not barred

    # ---------------------------------------------------------------------------------------------- all at once
    def in_force(self, bean, roles, among=None, ended_by=None, standing=False):
        """True, False, or None: the statement holds, its bean is among the decisions given (where given), no statement
        of `ended_by` ends it, and (`standing`) its standing allows it."""
        h = self.holds(bean, roles)
        if h is not True:
            return h
        if among is not None and bean not in among:
            return False
        if ended_by and self.ended(bean, roles, ended_by, among):
            return False
        if standing and not self.standing(bean, roles):
            return False
        return True

    def matching(self, spec, naming=None):
        """[(bean id, roles)] of the statements a `statements` form names, in force: of its `verb`, its `with` filters,
        naming the bean `naming` in its role `naming` (where both are given), each in force as the form asks."""
        verb, flt = spec.get('verb'), filters_of(spec.get('with'))
        among = self.decisions(spec['in_force_on']) if spec.get('in_force_on') else None
        role = spec.get('naming')
        out = []
        for b, r in self.by_verb(verb):
            if not all(str(r.get(k)) in vals for k, vals in flt.items()):
                continue
            if naming is not None and role:
                x = r.get(role)
                if not any(self.names(b, y) == ('bean', naming) for y in (x if isinstance(x, list) else [x])
                           if y is not None):
                    continue
            if self.in_force(b, r, among, spec.get('ended_by'), _true(spec.get('standing'))) is True:
                out.append((b, r))
        return out

    def policy(self, walk, include=None, verbs=None, ended_by=None):
        """The statements a walk's tool renders: those of the decisions in force on the walk, in the order they came into
        force, each bean's in its own order, less the ending statements (`ended_by`) and what they end — and less what
        does not hold (`unknown`: what could not be read). `dangling`: what an ending names that is nowhere in force."""
        order = self.decisions(walk, include)
        kept, ended, unknown = [], [], []
        for b in order:
            for _i, v, r in self.G.beans[b].items:
                if ended_by and v == ended_by:
                    continue
                if verbs is not None and v not in verbs:
                    continue
                sid = r.get('id')
                if ended_by and self.ended(b, r, ended_by, order):
                    ended.append(f"{b}#{sid}" if sid else b)
                    continue
                h = self.holds(b, r)
                if h is None:
                    unknown.append(f"{b}#{sid}" if sid else b)
                elif h:
                    kept.append((b, sid, v, r))
        return Policy(order, kept, sorted(set(ended)), self.ends_nothing(ended_by, order) if ended_by else [], unknown)


def _true(v):
    return v is True or str(v).lower() == 'true'


def _moment(at):
    """A move's moment as a sortable key: its milliseconds where it reads, else its text after every that does."""
    try:
        return (0, engine.dmcal.moment(str(at)).ms, '')
    except Exception:  # noqa: BLE001
        return (1, 0, str(at or ''))


if __name__ == '__main__':
    import json
    import sys
    if len(sys.argv) not in (2, 3) or sys.argv[1] in ('-h', '--help'):
        sys.exit('usage: python3 -m core.inforce <walk> [<the request being planned>]   (in a garden)')
    p = InForce(os.getcwd()).policy(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
    print(json.dumps({'order': p.order, 'kept': [f"{b}#{i}" if i else b for b, i, _v, _r in p.kept],
                      'unknown': p.unknown}, ensure_ascii=False, indent=1))
