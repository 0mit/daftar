"""books_read — the books of an entity, in a chart, READ from what the garden says and never stored: the accounting
profile's one reader (core/law/profiles.yaml, `accounting`).

    B = books_read.read(root, entity=None, chart=None)    # the gardener's books in the garden's one chart, by default
    B.vouchers                                            # every voucher, numbered in day order, each balanced
    trial(B, unit, start=None, end=None)                  # each account: opening, debit, credit, closing — rolled up
    ledger(B, code, unit, party=None, start=None, end=None)   # an account's lines with their running balance
    statement(B, unit, start, end) / balance(B, unit, at) # profit and loss over an extent; the balance at a day
    open_items(B)                                         # what waits: each line in the account awaiting an account,
                                                          # or holding a payment whose means is unsaid
    closes(B)                                             # each close: its day, its commit, its pin

WHAT IS READ. Every `pay` the entity paid (`by`), received (`to`) or bears a share of (`bear`); every `book` and
`match` of the entity's (`by`; absent, the gardener's) in the chart; every clause's asked payment the books accrue. A
voucher is read for each:
  - A PAYMENT THAT MOVED, with bookings that name one side: the other side is read from the payment — its means (the
    account that `stands_for` its `through`; else the chart's `unsaid`), its shares (each other bearer's current
    account: the account that stands for them, or that holds parties of their kind), what it settles of an obligation
    these books accrue (that obligation's account). The entity's own part goes where its bookings say, in their shares
    or amounts; what none says waits in `awaiting`. Paid: Cr the means, Dr the parts. Received: Dr the means, Cr where
    it belongs. Borne, another having paid: Dr the part, Cr the payer's account.
  - A PAYMENT WITH A BOOKING THAT NAMES BOTH SIDES is written whole: its lines are its bookings. Read or written, never
    both.
  - A PAYMENT A CLAUSE ASKS, booked here: accrued on its due day (and each occurrence of its `every` that has fallen
    due), the judged side against the party's account. A clause that occurs `each` time a reading holds a member is not
    walked here: it is said, in `notes`.
  - ANY OTHER STATEMENT BOOKED (a measure, the books' `open`, a booking): its bookings, as written.
  - A MOVE BOOKED IN THE REVERSE SENSE (`sense: "-1"`): the lines of what it books, their ends exchanged, on its own day.
  - A MATCH: its statements counted once — the records said carry the voucher; the lines read from a source are their
    evidence, and give the means where a record names none.
A CLOSE is a `pin` of a reading whose step is `books`, at a commit (`closes`): the books through its day are read as
that commit read them, and what is read through that day now and was not then is read on the first day after it, as the
difference. EVERY FIGURE IS EXACT (fractions), PER CURRENCY: two currencies are never added. What is not read is said,
in `notes`, never dropped in silence.
"""
import datetime
import os
import sys
from fractions import Fraction

KNOWING = ('say', 'read', 'derive', 'make')
SQUARE = ('obligatory', 'permitted', 'forbidden', 'omissible')
ZERO = Fraction(0)


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _paths(root):
    for p in (root, os.path.join(root, 'bin')):
        if p not in sys.path:
            sys.path.insert(0, p)


class Chart:
    """A scheme whose form is `chart`: its rows, each account's element (its own, or its nearest ancestor's), the being
    each stands for, the kinds whose parties' accounts it holds, the roles, the day each closed, which are postable."""

    def __init__(self, scheme, rows):
        self.scheme = scheme
        self.rows = {str(r.get('code')): {k: (v or '').strip() if isinstance(v, str) else v for k, v in r.items()}
                     for r in rows if r.get('code')}
        parents = {str(r.get('parent') or '') for r in self.rows.values()}
        self.postable = {c for c in self.rows if c not in parents}
        self.stands = {r['stands_for']: c for c, r in self.rows.items() if r.get('stands_for')}
        self.parties = {}
        for c, r in self.rows.items():
            for k in str(r.get('parties') or '').split():
                self.parties.setdefault(k, []).append(c)
        self.roles = {r['role']: c for c, r in self.rows.items() if r.get('role')}

    def path(self, code):
        out, c, seen = [], code, set()
        while c in self.rows and c not in seen:
            seen.add(c)
            out.insert(0, c)
            c = str(self.rows[c].get('parent') or '')
        return out or [code]

    def element(self, code):
        for c in reversed(self.path(code)):
            if self.rows.get(c, {}).get('element'):
                return self.rows[c]['element']
        return ''

    def name(self, code):
        return (self.rows.get(code) or {}).get('name') or code

    def role(self, *roles):
        return next((self.roles[r] for r in roles if r in self.roles), None)


class Books:
    def __init__(self, root, entity, chart, G, charts, analytic):
        self.root, self.entity, self.chart, self.G, self.analytic = root, entity, chart, G, analytic
        self.charts = charts
        self.notes, self.vouchers = [], []

    # ------------------------------------------------------------------------------------------------ accounts
    def account(self, x):
        """A filler of `from` or `to` as an account of this chart: a code of it, a being it stands for, a party it holds
        (by the party's kind; a party nobody named, `unknown`, in the one account that holds parties) — (code, party) —
        or (None, why)."""
        C = self.chart
        if x == 'unknown' or isinstance(x, dict):
            kind = x.get('someone') if isinstance(x, dict) else None
            hold = C.parties.get(kind, []) if kind else sorted({c for cs in C.parties.values() for c in cs})
            if len(hold) == 1:
                return hold[0], 'unknown'
            return None, f"a party nobody named, and {len(hold)} accounts hold parties: say which"
        if isinstance(x, str) and ':' in x:
            sch, c = x.split(':', 1)
            if sch != C.scheme:
                return None, f"{x} is of {sch}, not of this chart"
            return (c, None) if c in C.postable else (None, f"{x} is no postable account")
        if isinstance(x, str) and x in C.stands:
            return C.stands[x], None
        b = self.G.beans.get(x) if isinstance(x, str) else None
        kind = b.kind if b is not None else None
        hold = C.parties.get(kind) or []
        if len(hold) == 1:
            return hold[0], x
        if len(hold) > 1:
            return None, f"{x} is a {kind}, held by {', '.join(hold)}: say which with `stands_for`, or name the code"
        return None, f"no account of {C.scheme} stands for {x}" + (f", nor holds a {kind}" if kind else '')

    # ------------------------------------------------------------------------------------------------ vouchers
    def add(self, ref, read_as, day, unit, lines, memo='', notes=(), statements=(), knew=None):
        """A voucher of `ref`, read as a payment (`pay`), an asked payment (`asked`), an entry written whole (`entry`), a
        move in the reverse sense (`reversal`) or the difference a close leaves (`after-close`)."""
        v = {'ref': ref, 'as': read_as, 'day': day, 'unit': unit, 'lines': [l for l in lines if l['dr'] or l['cr']],
             'memo': memo, 'notes': list(notes), 'statements': list(statements) or [ref], 'knew': knew}
        self.vouchers.append(v)
        return v


def line(account, amount, party=None, memo='', analytic=None):
    """A line whose `amount` is a debit when positive and a credit when negative."""
    return {'account': account, 'party': party, 'dr': amount if amount > 0 else ZERO, 'cr': -amount if amount < 0 else ZERO,
            'memo': memo, 'analytic': dict(analytic or {})}


def _count(q):
    import units as dmunits
    if not isinstance(q, dict):
        return None, None
    try:
        return dmunits.exact(q.get('count')), str(q.get('unit'))
    except ValueError:
        return None, str(q.get('unit'))


def _day(v):
    """A day number of a position as written (any calendar the law reads), or None."""
    import stale as dmstale
    v = v[0] if isinstance(v, list) and v else v
    try:
        return dmstale.day_of(v) if v is not None else None
    except ValueError:
        return None


def charts_of(root, G):
    """{scheme: Chart} for each scheme of the garden whose form is `chart`; [schemes] that are no chart (analytic)."""
    import knowledge as dmknowledge
    K = dmknowledge.Knowledge(root)
    charts, other = {}, []
    for sch, row in K.schemes.items():
        if not isinstance(row, dict):
            continue
        if row.get('form') == 'chart':
            try:
                charts[sch] = Chart(sch, K.rows(sch))
            except (KeyError, OSError):
                pass
        elif row.get('holding') == 'extract':
            other.append(sch)
    return charts, other


def read(root, entity=None, chart=None, today=None, pinned=True):
    """The books of `entity` (the gardener's where none is named) in `chart` (the garden's one chart where none is); with
    `pinned`, a period a `pin` closed read as the pinned commit read it (`closes`)."""
    _paths(root)
    from core import engine
    import importlib
    dmpass = importlib.import_module('pass')
    G = engine.Garden.read(root)
    entity = entity or dmpass.gardener_of(root)
    charts, analytic = charts_of(root, G)
    if chart is None:
        if len(charts) != 1:
            raise ValueError(f"name the chart: this garden keeps {len(charts)} ({', '.join(sorted(charts)) or 'none'})")
        chart = next(iter(charts))
    if chart not in charts:
        raise ValueError(f"{chart} is no chart of this garden (a scheme whose form is `chart`)")
    B = Books(root, entity, charts[chart], G, charts, analytic)
    B.sides = sides(root)
    _vouchers(B, today or datetime.date.today().toordinal())
    if pinned:
        closed = closes(B)
        if closed:
            _as_pinned(B, closed, today)
    _numbered(B)
    return B


def closes(B):
    """[(day, commit, pin)] of each period the books' order is fixed through: a `pin` of a reading whose step is `books`
    (through `to`, in this chart and these books), at a moment and a commit — the close. In the order of their days."""
    G, out = B.G, []
    readings = {}
    for bid, b in G.beans.items():
        for _i, v, r in b.items:
            if v != 'reckon' or not isinstance(r.get('id'), str) or not isinstance(r.get('reading'), dict):
                continue
            for st in _listed(r['reading'].get('steps')):
                if isinstance(st, dict) and st.get('op') == 'books' and st.get('to') is not None \
                        and str(st.get('chart') or B.chart.scheme) == B.chart.scheme \
                        and str(st.get('entity') or G.gardener) == B.entity:
                    readings[f"{bid}#{r['id']}"] = _day(st['to'])
    from core.lines import GRAPH                         # a position of git-object-graph: <repo>@<commit>
    for bid, b in G.beans.items():
        for _i, v, r in b.items:
            if v != 'pin' or 'held' in r:
                continue
            refs = [x if '#' in str(x) else f"{bid}#{x}" for x in _listed(r.get('of')) + _listed(r.get('from'))]
            hit = next((readings[x] for x in refs if x in readings), None)
            sha = next((m.group(2) for a in _listed(r.get('at')) for m in [GRAPH.match(str(a))] if m), None)
            if hit is not None and sha:
                out.append((hit, sha, f"{bid}#{r.get('id')}"))
    return sorted(out)


def _as_pinned(B, closed, today):
    """THE BOOKS' ORDER FIXED THROUGH EACH CLOSED DAY. Each closed period (the days after the close before it, through its
    own) is read as the books read at its pinned commit; what that commit read through an earlier closed day and the
    commit before it did not — a move that came between the two closes with an earlier day — is read on the first day
    after that earlier close, as its difference; and so for what is read now, after the last close, on the first day
    after it. So each period is what its close pinned, and the books through any closed day add up to what was read at
    that close."""
    import shutil
    import subprocess
    import tempfile
    readings = []
    for day, sha, pin in closed:                       # each close's books, read at its commit, by this reader
        tmp = tempfile.mkdtemp(prefix='books-pinned-')
        try:
            arch = subprocess.run(['git', '-C', B.root, 'archive', sha], capture_output=True)
            if arch.returncode:
                B.notes.append(f"the close {pin} names a commit this garden has not ({sha}): it is not read")
                continue
            subprocess.run(['tar', '-x', '-C', tmp], input=arch.stdout, check=True)
            then = read(tmp, entity=B.entity, chart=B.chart.scheme, today=today, pinned=False)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        readings.append((day, sha, pin, then.vouchers))
    if not readings:
        return
    within = lambda v, lo, hi: v['day'] is not None and (lo is None or v['day'] > lo) and (hi is None or v['day'] <= hi)

    def difference(after, before, upto, at, pin, sha, memo):
        """The lines by which `after` reads the days through `upto` otherwise than `before` did, as one voucher per
        currency on day `at`."""
        diff = {}
        for sign, vs in ((1, after), (-1, before)):
            for v in vs:
                if within(v, None, upto):
                    for ln in v['lines']:
                        k = (v['unit'], ln['account'], ln['party'])
                        diff[k] = diff.get(k, ZERO) + sign * (ln['dr'] - ln['cr'])
        refs = sorted({v['ref'] for v in after if within(v, None, upto)} ^
                      {v['ref'] for v in before if within(v, None, upto)})
        for unit in sorted({k[0] for k, x in diff.items() if x and k[0]}):
            lines_ = [line(a, x, party=p) for (u, a, p), x in sorted(diff.items(), key=lambda kv: str(kv[0]))
                      if u == unit and x]
            out.append({'ref': f"{pin}@after", 'as': 'after-close', 'day': at, 'unit': unit, 'lines': lines_,
                        'memo': memo, 'notes': [f"came after the close {pin} (commit {sha[:12]}): "
                                                + (', '.join(refs[:12]) or 'what it read, changed')],
                        'statements': [f"{pin}@after"], 'knew': None})

    out, prev = [], None
    for k, (day, sha, pin, vs) in enumerate(readings):
        out += [v for v in vs if within(v, prev, day)]
        if k:
            pday, psha, ppin, pvs = readings[k - 1]
            difference(vs, pvs, pday, pday + 1, ppin, psha,
                       f"what was read through {datetime.date.fromordinal(pday).isoformat()} after the books were "
                       f"closed through it, before the next close")
        prev = day
    lday, lsha, lpin, lvs = readings[-1]
    now = list(B.vouchers)
    out += [v for v in now if v['day'] is None or v['day'] > lday]
    difference(now, lvs, lday, lday + 1, lpin, lsha,
               f"what was read through {datetime.date.fromordinal(lday).isoformat()} after the books were closed "
               f"through it")
    B.vouchers = out


def _numbered(B):
    B.vouchers.sort(key=lambda v: (v['day'] if v['day'] is not None else 10 ** 9, v['ref']))
    for n, v in enumerate(B.vouchers, 1):
        v['number'] = n
        dr, cr = sum((l['dr'] for l in v['lines']), ZERO), sum((l['cr'] for l in v['lines']), ZERO)
        v['total'], v['balanced'] = dr, dr == cr
        if dr != cr and not any('differ' in n_ for n_ in v['notes']):
            v['notes'].append(f"debits {dr} and credits {cr} differ")


def _knowing(b):
    """{statement id: (act verb, its moment)} of bean `b`: the act that names it, else one that names nothing."""
    out, blanket = {}, None
    for _i, v, r in b.items:
        if v not in KNOWING:
            continue
        at = r.get('at')
        moment = next((str(x) for x in _listed(at) if isinstance(x, str) and x[:1].isdigit()), None)
        if r.get('of') is None:
            blanket = (v, moment)
        for x in _listed(r.get('of')):
            out.setdefault(str(x), (v, moment))
    if blanket:
        for _i, v, r in b.items:
            if isinstance(r.get('id'), str):
                out.setdefault(r['id'], blanket)
    return out


def _vouchers(B, today):
    G, E, C = B.G, B.entity, B.chart
    gardener = G.gardener
    pays, asked, bears, books, analytic, reverses, matches, acts = {}, set(), {}, {}, {}, [], [], {}
    for bid, b in sorted(G.beans.items()):
        if b.unread:
            continue
        acts[bid] = _knowing(b)
        for _i, v, r in b.items:
            if 'held' in r:
                continue
            ref = lambda x: x if '#' in str(x) else f"{bid}#{x}"
            if v == 'pay' and isinstance(r.get('id'), str):
                pays[f"{bid}#{r['id']}"] = (bid, r)
            elif v in SQUARE and isinstance(r.get('of'), str):
                asked.add(ref(r['of']))
            elif v == 'bear' and isinstance(r.get('of'), str):
                bears.setdefault(ref(r['of']), []).append(r)
            elif v in ('book', 'match') and str(r.get('by') or gardener) == E:
                if v == 'book' and str(r.get('sense')) == '-1' and isinstance(r.get('of'), str):
                    reverses.append((bid, r, ref(r['of'])))      # the move it books, in the reverse sense
                elif v == 'book' and isinstance(r.get('of'), str):
                    sides = [r.get(k) for k in ('from', 'to')]
                    codes = [s for s in sides if isinstance(s, str) and ':' in s]
                    if any(c.split(':', 1)[0] == C.scheme for c in codes) or (not codes and any(sides)):
                        books.setdefault(ref(r['of']), []).append((bid, r))
                    elif codes and r.get('from') is None and codes[0].split(':', 1)[0] in B.analytic:
                        analytic.setdefault(ref(r['of']), []).append((bid, r))
                elif v == 'match':
                    matches.append((bid, r, [ref(x) for x in _listed(r.get('of')) if isinstance(x, str)]))
    known = lambda ref: acts.get(ref.split('#', 1)[0], {}).get(ref.split('#', 1)[1], (None, None))
    # A MATCH: the lines read from a source are evidence of the records said, which carry the voucher
    evidence, means_from = set(), {}
    for _bid, _r, refs in matches:
        said = [x for x in refs if known(x)[0] != 'read']
        lines_ = [x for x in refs if known(x)[0] == 'read']
        if said and lines_:
            evidence |= set(lines_)
            through = next((pays[x][1].get('through') for x in lines_ if x in pays), None)
            for x in said:
                means_from[x] = through
    accrued = {ref for ref in books if ref in asked}
    done = set()
    for ref, (bid, p) in sorted(pays.items()):
        if ref in evidence or ref in asked:
            continue
        mine = books.get(ref, [])
        parties = {str(p.get('by')), str(p.get('to'))} | {str(x.get('by')) for x in bears.get(ref, [])}
        if E not in parties and not mine:
            continue
        _pay_voucher(B, ref, p, mine, bears.get(ref, []), analytic.get(ref, []), means_from.get(ref), accrued, pays,
                     known(ref)[1])
        done.add(ref)
    for ref in sorted(accrued):
        _accrual(B, ref, pays.get(ref), books[ref], today, known(ref)[1])
        done.add(ref)
    for ref, bks in sorted(books.items()):                       # any other statement booked, written whole
        if ref in done or ref in pays:
            continue
        # ONE VOUCHER A DAY: the bookings of one statement on one day are one entry (each booked on its own day, else
        # the day of what it books) — the books' `open` carries every journal entry the bookkeeper writes, each its own
        ob, _h, oid = ref.partition('#')
        hit = G.beans.get(ob).ids.get(oid) if G.beans.get(ob) else None
        own = _day(hit[2].get('at')) if hit else None
        days = {}
        for b_, r in bks:
            days.setdefault(_day(r.get('at')) or own, []).append((b_, r))
        for day, group in sorted(days.items(), key=lambda kv: (kv[0] is None, kv[0] or 0)):
            lines_, notes = [], []
            for _bid, r in group:
                lines_ += _written(B, r, None, None, notes)
            memo = '; '.join(dict.fromkeys(str(r.get('why')) for _b, r in group if r.get('why')))
            B.add(ref if day == own or len(days) == 1 else f"{ref}@{datetime.date.fromordinal(day).isoformat()}",
                  'entry', day, _unit_of(group), lines_, memo=memo, notes=notes, knew=known(ref)[1],
                  statements=[f"{b_}#{r['id']}" for b_, r in group if isinstance(r.get('id'), str)] or [ref])
    for bid, r, of in reverses:
        # THE MOVE IN THE REVERSE SENSE: a booking written whole, its two ends exchanged; a booking of one side, or a
        # statement, every line its voucher holds — on the reversal's own day
        ob, _h, oid = of.partition('#')
        hit = G.beans.get(ob).ids.get(oid) if G.beans.get(ob) else None
        notes, unit = [], None
        if hit and hit[1] == 'book' and hit[2].get('from') is not None and hit[2].get('to') is not None:
            lines_, unit = _written(B, hit[2], None, None, notes), _unit_of([(ob, hit[2])])
        else:
            whole = hit[2].get('of') if hit and hit[1] == 'book' else None
            ref_ = (whole if '#' in str(whole) else f"{ob}#{whole}") if whole else of
            found = [v for v in B.vouchers if v['ref'] == ref_ or v['ref'].startswith(ref_ + '@')]
            lines_ = [l for v in found for l in v['lines']]
            unit = found[0]['unit'] if found else None
        if not lines_:
            notes.append(f"what it reverses ({of}) is not in these books")
        B.add(f"{bid}#{r.get('id') or 'reverse'}", 'reversal', _day(r.get('at')), unit,
              [dict(l, dr=l['cr'], cr=l['dr']) for l in lines_], memo=f"the reverse of {of}", notes=notes,
              knew=known(f"{bid}#{r.get('id')}")[1] if r.get('id') else None)



def _unit_of(bks):
    for _b, r in bks:
        s = r.get('share')
        if isinstance(s, dict) and s.get('unit'):
            return str(s['unit'])
    return None


def _written(B, r, whole, unit, notes, sign=1):
    """The lines of a booking that names both sides: its amount, or its share of `whole`."""
    fa, fp = B.account(r.get('from'))
    ta, tp = B.account(r.get('to'))
    s = r.get('share')
    amt = None
    if isinstance(s, dict):
        amt, _u = _count(s)
    elif s is not None and whole is not None:
        amt = None                                        # a share of a whole: distributed by the caller
    if amt is None:
        notes.append(f"a written booking states no amount: {r.get('id') or r.get('of')}")
        return []
    if fa is None or ta is None:
        notes.append(f"{r.get('id') or r.get('of')}: {fp if fa is None else tp}")
        return []
    return [line(ta, sign * amt, party=tp), line(fa, -sign * amt, party=fp)]


def _spread(B, part, bks, side, notes, ana):
    """The entity's `part` over its one-sided bookings (shares, or amounts): [(account, amount, party)]; what they do not
    place waits in `awaiting`."""
    C = B.chart
    out, placed = [], ZERO
    shares, amounts = [], []
    for _bid, r in bks:
        acct, why = B.account(r.get(side))
        if acct is None:
            notes.append(why)
            continue
        s = r.get('share')
        if isinstance(s, dict):
            a, _u = _count(s)
            amounts.append((acct, a if a is not None else ZERO, why))
        else:
            try:
                shares.append((acct, Fraction(str(s)) if s is not None else Fraction(1), why))
            except (ValueError, ZeroDivisionError):
                notes.append(f"a share {s!r} is not read")
    if amounts:
        for acct, a, party in amounts:
            out.append((acct, a, party))
            placed += a
    elif shares:
        total = sum((x for _a, x, _p in shares), ZERO)
        for acct, x, party in shares:
            out.append((acct, part * x / total, party))
            placed += part * x / total
    rest = part - placed
    if rest:
        wait = C.role('awaiting')
        if wait is None:
            notes.append(f"{rest} waits for an account, and the chart names none `awaiting`")
        else:
            out.append((wait, rest, None))
            notes.append("a part awaits an account" if not bks else f"{rest} of it is booked nowhere: it awaits an account")
    return out


def _analytic_of(ana):
    out = {}
    for _bid, r in ana:
        s = r.get('share')
        try:
            x = Fraction(str(s)) if s is not None and not isinstance(s, dict) else Fraction(1)
        except (ValueError, ZeroDivisionError):
            continue
        out[str(r.get('to'))] = out.get(str(r.get('to')), ZERO) + x
    total = sum(out.values(), ZERO)
    return {k: v / total for k, v in out.items()} if total else {}


def _party_account(B, who, notes):
    """(the account of a party in this chart, the party where the account holds several), or `awaiting` and why not."""
    acct, party = B.account(who)
    if acct is None:
        notes.append(party)
        return B.chart.role('awaiting'), None
    return acct, party


def _pay_voucher(B, ref, p, mine, bears, ana, matched_means, accrued, pays, knew):
    C, E = B.chart, B.entity
    notes = []
    W, unit = _count(p.get('of'))
    ch, cu = _count(p.get('charged'))
    if ch is not None and cu != unit:                    # priced in one currency, charged in another: what moved
        W, unit = ch, cu
    if W is None:
        B.notes.append(f"{ref}: its amount is not a count read exactly — left out")
        return
    day = _day(p.get('at'))
    written = [r for _b, r in mine if r.get('from') is not None and r.get('to') is not None]
    if written:
        lines_ = []
        for r in written:
            if isinstance(r.get('share'), dict):
                lines_ += _written(B, r, W, unit, notes)
            else:
                share = Fraction(str(r.get('share') or 1))
                total = sum((Fraction(str(x.get('share') or 1)) for x in written if not isinstance(x.get('share'), dict)), ZERO)
                fa, _fp = B.account(r.get('from'))
                ta, _tp = B.account(r.get('to'))
                if fa and ta:
                    lines_ += [line(ta, W * share / total), line(fa, -W * share / total)]
        B.add(ref, 'pay', _day(next((r.get('at') for r in written if r.get('at')), None)) or day, unit, lines_,
              memo=str(p.get('note') or ''), notes=notes, knew=knew)
        return
    by, to = str(p.get('by')), str(p.get('to') or '')
    # THE MEANS: the side opposite the entity's part — `from` for what it paid, `to` for what it received — where a
    # booking of its own names it (its judgment of what it paid through, kept in its books, never in the payment);
    # else the account that stands for the payment's `through`, or for a matched line's; else `unsaid`
    means_side = 'to' if (to == E and by != E) else 'from'
    stated = [m for m in mine if m[1].get(means_side) is not None and m[1].get('to' if means_side == 'from' else 'from') is None]
    mine = [m for m in mine if m not in stated]
    through = p.get('through') if isinstance(p.get('through'), str) else None
    means = C.stands.get(through) if through else None
    if means is None and matched_means:
        means = C.stands.get(matched_means)
    if stated:
        means = None
    elif means is None:
        means = C.role('unsaid', 'awaiting')
        notes.append(f"its means is not said, or has no account here ({through or 'none'})")

    def means_lines(amount):
        """The means side's lines for `amount` (a debit when positive): as the entity's own bookings name it, else the
        one account read."""
        if not stated:
            return [line(means, amount)]
        sign = 1 if amount > 0 else -1
        return [line(acct, sign * x, party=party) for acct, x, party in _spread(B, abs(amount), stated, means_side,
                                                                                    notes, {})]
    shares = {}
    for x in bears:
        try:
            s = x.get('share')
            shares[str(x.get('by'))] = shares.get(str(x.get('by')), ZERO) + (Fraction(str(s.get('count') if isinstance(s, dict) else s)) if s is not None else Fraction(1))
        except (ValueError, ZeroDivisionError):
            notes.append(f"a share of {x.get('by')} is not read")
    if not shares:
        shares = {by: Fraction(1)}
    total = sum(shares.values(), ZERO)
    a = _analytic_of(ana)
    lines_ = []
    settled = ZERO
    for st in _listed(p.get('settles')):                 # what it settles of an obligation these books accrue
        if not isinstance(st, dict):
            continue
        cl = st.get('clause')
        asked_ref = _asked_of(B, ref, cl)
        if asked_ref not in accrued:
            continue
        amt, _u = _count(st.get('amount')) if isinstance(st.get('amount'), dict) else (W, unit)
        other = str(pays[asked_ref][1].get('to') if by == E else pays[asked_ref][1].get('by'))
        acct, party = _party_account(B, other, notes)
        lines_.append(line(acct, amt if by == E else -amt, party=party, memo=f"settles {cl}"))
        settled += amt
    R = W - settled
    if by == E and to == E:
        lines_ += means_lines(-W)
        for acct, x, party in _spread(B, W, mine, 'to', notes, a):
            lines_.append(line(acct, x, party=party, analytic=a))
    elif by == E:
        lines_ += means_lines(-W)
        for who, s in shares.items():
            part = R * s / total
            if who == E:
                for acct, x, party in _spread(B, part, [m for m in mine if m[1].get('to') is not None], 'to', notes, a):
                    lines_.append(line(acct, x, party=party, analytic=a))
            else:
                acct, party = _party_account(B, who, notes)
                lines_.append(line(acct, part, party=party, memo=f"the share of {who}"))
    elif to == E:
        # RECEIVED: the whole reached its means. What the entity bears of it is owed back to the payer, as bin/ledger.py
        # reads a transfer (each bearer owes the payer its share); the rest belongs where its own bookings say
        lines_ += means_lines(W)
        owe = R * shares.get(E, ZERO) / total if E in shares and by not in (E,) and set(shares) != {by} else ZERO
        if owe:
            acct, party = _party_account(B, by, notes)
            lines_.append(line(acct, -owe, party=party, memo=f"owed to {by}"))
        for acct, x, party in _spread(B, R - owe, [m for m in mine if m[1].get('from') is not None], 'from', notes, a):
            lines_.append(line(acct, -x, party=party, analytic=a))
    elif E in shares:
        part = R * shares[E] / total
        for acct, x, party in _spread(B, part, [m for m in mine if m[1].get('to') is not None], 'to', notes, a):
            lines_.append(line(acct, x, party=party, analytic=a))
        acct, party = _party_account(B, by, notes)
        lines_.append(line(acct, -part, party=party, memo=f"paid by {by}"))
    else:
        notes.append("the entity is no party to it; its bookings name one side only")
    B.add(ref, 'pay', day, unit, lines_, memo=str(p.get('note') or ''), notes=notes, knew=knew)


def _asked_of(B, ref, clause):
    """The asked payment a clause (`<bean>#<id>` or an id of the payment's bean) is a position of."""
    bid = ref.split('#', 1)[0]
    cref = clause if '#' in str(clause) else f"{bid}#{clause}"
    cb, cid = cref.split('#', 1)
    b = B.G.beans.get(cb)
    hit = b.ids.get(cid) if b else None
    if hit and hit[1] in SQUARE and isinstance(hit[2].get('of'), str):
        return hit[2]['of'] if '#' in hit[2]['of'] else f"{cb}#{hit[2]['of']}"
    return None


def _accrual(B, ref, pay, bks, today, knew):
    """An obligation booked here: recognised on its due day and at each occurrence that has fallen due."""
    import stale as dmstale
    C, E = B.chart, B.entity
    notes = []
    if pay is None:
        return
    bid, p = pay
    W, unit = _count(p.get('of'))
    b = B.G.beans.get(bid)
    clause = next((r.get('clause') for _i, v, r in b.items if v in SQUARE and r.get('of') == p.get('id')), None) or {}
    days = []
    at = next((r.get('at') for _b, r in bks if r.get('at')), None)
    if at:
        days = [_day(at)]
    elif clause.get('each') is not None:
        B.notes.append(f"{ref}: its clause occurs for each member of a reading ({clause.get('each')}); its occurrences "
                       f"are bin/ledger.py's to read, and are accrued here only on a day a booking of it says")
        return
    elif clause.get('due'):
        first = _day(clause['due'])
        if isinstance(clause.get('every'), dict) and first is not None:
            try:
                for n in dmstale.occurrences(first, clause['every']):
                    if n > today:
                        break
                    days.append(n)
            except Exception as e:      # noqa: BLE001 — a repetition that cannot be walked is said
                notes.append(f"its repetition is not walked: {e}")
                days = [first]
        else:
            days = [first]
    by, to = str(p.get('by')), str(p.get('to') or '')
    for n, day in enumerate(days or [None], 1):
        lines_ = []
        if by == E:
            for acct, x, party in _spread(B, W, [m for m in bks if m[1].get('to') is not None], 'to', notes, {}):
                lines_.append(line(acct, x, party=party))
            acct, party = _party_account(B, to, notes)
            lines_.append(line(acct, -W, party=party, memo='owed'))
        elif to == E:
            for acct, x, party in _spread(B, W, [m for m in bks if m[1].get('from') is not None], 'from', notes, {}):
                lines_.append(line(acct, -x, party=party))
            acct, party = _party_account(B, by, notes)
            lines_.append(line(acct, W, party=party, memo='owed to the entity'))
        B.add(f"{ref}@{n}" if len(days) > 1 else ref, 'asked', day, unit, lines_, memo=str(p.get('note') or ''),
              notes=notes, knew=knew)


# ---------------------------------------------------------------------------------------------------- the readings
def _within(v, start, end):
    return (start is None or (v['day'] is not None and v['day'] >= start)) and \
           (end is None or (v['day'] is not None and v['day'] <= end))


def sides(root):
    """{element: +1 | -1} — the sense each element's balance is read in (the profile's table `elements`, its `sense`):
    a balance is a net charge, what arrived less what left; read along the arrival (`1`: an asset, an expense) or
    against it (`-1`: a liability, equity, an income), as the view's `orientations` give each order its sense — so a
    liability that grows is drawn growing (a magnitude: more is up)."""
    from core import read
    data = read.data(os.path.join(root, 'core', 'law', 'profiles.yaml'))
    return {str(r['element']): (-1 if str(r.get('sense')) == '-1' else 1) for r in data.get('elements') or []
            if isinstance(r, dict) and r.get('element')}


def trial(B, unit, start=None, end=None):
    """Each account touched, rolled up its chart: opening (before `start`), debit, credit, closing (debit less credit);
    and its `balance`, the closing read in its element's sense (a liability's credit balance positive)."""
    acc = {}
    for v in B.vouchers:
        if v['unit'] != unit or (end is not None and (v['day'] is None or v['day'] > end)):
            continue
        before = start is not None and v['day'] is not None and v['day'] < start
        for l in v['lines']:
            a = acc.setdefault(l['account'], {'opening': ZERO, 'dr': ZERO, 'cr': ZERO})
            if before:
                a['opening'] += l['dr'] - l['cr']
            else:
                a['dr'] += l['dr']
                a['cr'] += l['cr']
    rows = {}
    for code, a in acc.items():
        for c in B.chart.path(code):
            r = rows.setdefault(c, {'opening': ZERO, 'dr': ZERO, 'cr': ZERO})
            for k in r:
                r[k] += a[k]
    out = []
    for code in sorted(rows, key=B.chart.path):
        r = rows[code]
        el = B.chart.element(code)
        closing = r['opening'] + r['dr'] - r['cr']
        out.append(dict(r, code=code, name=B.chart.name(code), element=el, closing=closing,
                        balance=closing * B.sides.get(el, 1), posts=code in acc))
    leaf = [acc[c] for c in acc]
    totals = {k: sum((a[k] for a in leaf), ZERO) for k in ('opening', 'dr', 'cr')}
    return {'rows': out, 'totals': totals, 'balanced': totals['dr'] == totals['cr'] and totals['opening'] == 0,
            'unit': unit}


def ledger(B, code, unit, party=None, start=None, end=None):
    rows, run, opening = [], ZERO, ZERO
    for v in B.vouchers:
        if v['unit'] != unit:
            continue
        for l in v['lines']:
            if l['account'] != code or (party and l['party'] != party):
                continue
            amt = l['dr'] - l['cr']
            if start is not None and (v['day'] is None or v['day'] < start):
                opening += amt if v['day'] is not None else 0
                continue
            if end is not None and v['day'] is not None and v['day'] > end:
                continue
            run += amt
            rows.append({'number': v['number'], 'ref': v['ref'], 'day': v['day'], 'memo': l['memo'] or v['memo'],
                         'party': l['party'], 'dr': l['dr'], 'cr': l['cr'], 'balance': opening + run})
    return {'code': code, 'party': party, 'opening': opening, 'rows': rows, 'closing': opening + run, 'unit': unit}


def statement(B, unit, start=None, end=None):
    """Profit and loss over an extent: income and expense, each as its element reads it (income credit-normal)."""
    t = trial(B, unit, start, end)
    inc = [r for r in t['rows'] if r['element'] == 'income']
    exp = [r for r in t['rows'] if r['element'] == 'expense']
    net = lambda rs: sum((r['cr'] - r['dr'] for r in rs if r['posts']), ZERO)
    return {'income': inc, 'expense': exp, 'result': net(inc) + net(exp), 'unit': unit}


def balance(B, unit, at=None):
    t = trial(B, unit, None, at)
    by = lambda el: [r for r in t['rows'] if r['element'] == el]
    result = sum((r['cr'] - r['dr'] for r in t['rows'] if r['posts'] and r['element'] in ('income', 'expense')), ZERO)
    return {'assets': by('asset'), 'liabilities': by('liability'), 'equity': by('equity'), 'result': result,
            'unit': unit}


def open_items(B):
    wait = {B.chart.role('awaiting'), B.chart.role('unsaid')} - {None}
    out = []
    for v in B.vouchers:
        for l in v['lines']:
            if l['account'] in wait:
                out.append({'ref': v['ref'], 'day': v['day'], 'account': l['account'], 'dr': l['dr'], 'cr': l['cr'],
                            'unit': v['unit']})
    return out
