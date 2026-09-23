#!/usr/bin/env python3
"""dmledger — what the parties to an agreement owe one another, READ from what moved and never written.

    python3 bin/dmledger.py                                      # every agreement in this garden
    python3 bin/dmledger.py <contract-bean> [<contract-bean> ...] # these agreements
    python3 bin/dmledger.py --between <party-bean> <party-bean>  # two parties, netted across the agreements they share

WHAT IS OWED IS NEVER STORED (std-vocab 21.0, `transactions`, and the retired `balance`). "ali owes sam 300" is
derivable from "900 paid by sam, borne two to one", and a bean that stored both kept a second copy that would drift the
first time a transaction was added and the balance was not. So an agreement records only what MOVED — each amount, who
paid how much of it, who bears it in what shares — and this tool reads the rest, the same way every time:

  POSITION   per agreement and per currency, what each party paid less the share it bears. A single payer that states
             no amount paid the whole; a transaction with no bearers is borne by whoever paid it.
  WHO OWES   each bearer owes each payer its share of what that payer put in, and the two directions between a pair are
             netted: "ali owes sam 300 XTS". With --between, netted again across every agreement the two share.
  CLAUSES    each clause still in force — not met, waived or broken, as the law's `expiry.unless` says — with when it
             falls due, when it falls due NEXT if it repeats (walked through the day in its own calendar, by the same
             function bin/dmstale.py warns with), the condition that brings it into force, and what is not yet known.

EVERY FIGURE IS EXACT. A count is a whole number or a decimal written as a string, and it is read as a
`fractions.Fraction`; every sum, share, balance and rate is one. This file holds no float, calls no rounding and has no
division operator — a quotient is `Fraction(n, d)` — and test/money.py reads its source to hold it to that. A share
that does not come out even in the currency's decimal places is printed as the fraction it is, `200/3 XTS`, and said to
be so: who takes the remainder is a clause the parties agree, never a rounding a tool chooses for them.

TWO CURRENCIES ARE NEVER ADDED. No factor joins two currencies (the `money` quantity says `crosswalk: observed`), so
every position, debt and net is per currency. A transaction priced in one currency and `charged` in another shows the
rate it implies — charged over amount, exactly — as a reading of the statement, never as a rate to reuse.

The law is read, not named: the transactions are every term whose schema declares `sums`, its whole and its parts come
from that rule, the parties from the `key_of` its parts name, and the clauses from every term that falls due between
those parties (`expiry` and a `key_of` the parties). Never writes. Exit 0; 2 when a named bean is not here.
"""
import datetime, glob, os, sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmcal
import dmparse
import dmform
import dmunits
import dmstale
try:
    import yaml  # noqa: F401  (dmparse needs it; say so plainly rather than fail inside it)
except ImportError:
    print("ERROR: PyYAML required"); sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# WHO BEARS A TRANSACTION, AND IN WHAT SHARES. The law's `sums` rule says which attribute is the whole and which the
# parts; it has no construct that says "this attribute bears the cost, in these whole-number shares", so this is the
# one place the tool names an attribute of the law. If a second term ever bears in shares, the law should say it.
BEARING, SHARE = 'borne_by', 'share'


def law():
    """The law as the gate loaded it: every term of both tiers, every unit (a currency among them, with its digits),
    every positioning system. Asked of bin/dmcheck.py, the way bin/dmstale.py asks it, so this reads what is in force."""
    import dmcheck
    return dmcheck.TERMS, dmcheck.UNITS, dmcheck.SYSTEMS


def _in(rec):
    return (rec or {}).get('in') if isinstance(rec, dict) else None


def money_terms(terms):
    """[(term, rule)] for every term whose schema declares `sums`: its whole, its parts, and the parties they name."""
    out = []
    for name, t in sorted(terms.items()):
        sch = (t or {}).get('schema') or {}
        rule = sch.get('sums')
        if not isinstance(rule, dict):
            continue
        wholes = rule.get('whole') if isinstance(rule.get('whole'), list) else [rule.get('whole')]
        pattr, _, pfield = str(rule.get('parts') or '').partition('.')
        fields = (_in((sch.get('attrs') or {}).get(pattr)) or {}).get('entries') or {}
        party = next(((f, _in(r).get('key_of')) for f, r in fields.items()
                      if isinstance(_in(r), dict) and _in(r).get('key_of')), (None, None))
        # WHEN IT HAPPENED: the attribute the law types as a date — found by its type, not by its name, because the
        # name the law gives it (`on`) is one YAML 1.1 reads as the boolean true, in the law and in a bean alike.
        dates = [a for a, r in (sch.get('attrs') or {}).items()
                 if isinstance(_in(r), dict) and _in(r).get('type') in ('date', 'iso_date')]
        said_as = [a for a, r in (sch.get('attrs') or {}).items() if isinstance(r, dict) and r.get('required') and _in(r) == 'prose']
        out.append((name, {'wholes': [w for w in wholes if w], 'parts': pattr, 'part_amount': pfield,
                           'party': party[0], 'parties': party[1], 'dates': dates, 'said_as': said_as, 'schema': sch}))
    return out


def clause_terms(terms, parties_terms):
    """[(term, schema)] for every term that FALLS DUE BETWEEN PARTIES: it declares an `expiry`, and an attribute of it
    is a key of a parties term. Read from the law, so a garden's own kind of obligation is listed the same way."""
    out = []
    for name, t in sorted(terms.items()):
        sch = (t or {}).get('schema') or {}
        if not isinstance(sch.get('expiry'), dict) or dmform.scope_of(sch) != 'entry':
            continue
        keyed = {_in(r).get('key_of') for r in (sch.get('attrs') or {}).values() if isinstance(_in(r), dict)}
        if keyed & set(parties_terms):
            out.append((name, sch))
    return out


def count_of(q):
    """A count, exactly — or None. Only a whole number or a decimal string is read: anything else (a float above
    all) has already lost what it lost, and the gate refuses it."""
    c = q.get('count') if isinstance(q, dict) else None
    if isinstance(c, bool):
        return None
    if isinstance(c, int):
        return Fraction(c)
    if isinstance(c, str) and _decimal(c):
        return Fraction(c)
    return None


def _decimal(s):
    """`-12.50` — a whole number or a decimal, with no exponent and nothing a float would have made of it."""
    head, dot, tail = s.lstrip('-').partition('.')
    return head.isdigit() and head.isascii() and (not dot or (tail.isdigit() and tail.isascii()))


def digits_of(unit, units):
    d = (units.get(str(unit)) or {}).get('digits')
    return int(d) if isinstance(d, (int, str)) and str(d).isdigit() else None


def amount(x, unit, units):
    """(text, uneven) — an amount EXACTLY. As a decimal when it comes out even in the currency's decimal places; as
    the fraction it is when it does not, with `uneven` set so the reader is told. Never rounded."""
    d = digits_of(unit, units)
    if d is not None and (x * 10 ** d).denominator != 1:
        return f"{x.numerator}/{x.denominator}", True
    return dmunits.show(x), False


def said(x, unit, units, sign=False, note=True):
    """An amount and its unit, in words, with the note an uneven one needs (or without it, where a list of amounts
    carries one note for all of them — `uneven_note`)."""
    text, uneven = amount(x, unit, units)
    if sign and x > 0:
        text = '+' + text
    return f"{text} {unit}" + (_uneven_words(unit, units) if uneven and note else '')


def _uneven_words(unit, units):
    return f" (does not come out even in {unit}'s {digits_of(unit, units)} places — who takes the remainder is a clause)"


def uneven_note(xs, unit, units):
    """One line for every amount of a list that does not come out even, or None."""
    odd = [amount(x, unit, units)[0] for x in xs if amount(x, unit, units)[1]]
    return f"{', '.join(odd)} {unit}{_uneven_words(unit, units)}" if odd else None


def _list(v):
    """`in: {entries: …}` holds a list of entries, or one mapping."""
    return v if isinstance(v, list) else [v] if isinstance(v, dict) else []


def read_transaction(key, e, rule, units):
    """One transaction, read: {whole, unit, paid, borne, priced, notes}. `paid` and `borne` are None when it cannot be
    read exactly, and `notes` then say why — a figure left out is said to be left out, never guessed at."""
    tx = {'key': key, 'what': ' — '.join(str(e[a]) for a in rule['said_as'] if e.get(a) is not None),
          'on': next((e[a] for a in rule['dates'] if e.get(a) is not None), None),
          'notes': [], 'paid': None, 'borne': None, 'whole': None, 'unit': None, 'priced': None}
    wattr = next((w for w in rule['wholes'] if e.get(w) is not None), None)
    whole = e.get(wattr) if wattr else None
    W = count_of(whole)
    if W is None:
        tx['notes'].append(f"its {wattr or 'amount'} is not a count this can read exactly — left out")
        return tx
    unit = str(whole.get('unit'))
    tx['whole'], tx['unit'] = W, unit
    # THE RATE A STATEMENT IMPLIES: priced in one currency, charged in another. Read exactly and shown, never stored.
    for other in rule['wholes']:
        o = e.get(other)
        if other != wattr and isinstance(o, dict) and str(o.get('unit')) != unit and count_of(o):   # a zero price implies no rate
            tx['priced'] = (count_of(o), str(o.get('unit')))
    parts = _list(e.get(rule['parts']))
    stated = [(p.get(rule['party']), p.get(rule['part_amount'])) for p in parts if isinstance(p, dict)]
    if not stated:
        tx['notes'].append("nobody is recorded as having paid it — left out")
        return tx
    paid = {}
    if len(stated) == 1 and stated[0][1] is None:
        paid[str(stated[0][0])] = W                       # a single payer who states no amount paid the whole
    else:
        for who, q in stated:
            c = count_of(q)
            if q is None or c is None:
                tx['notes'].append(f"how much {who} paid is not known exactly — left out until it is")
                return tx
            if str(q.get('unit')) != unit:
                tx['notes'].append(f"{who} paid in {q.get('unit')} and the whole is in {unit} — left out; a payment in "
                                   f"another currency is a transaction of its own, or `charged`")
                return tx
            paid[str(who)] = paid.get(str(who), Fraction(0)) + c
        if sum(paid.values()) != W:
            tx['notes'].append(f"what was paid adds up to {said(sum(paid.values()), unit, units)} and the whole is "
                               f"{said(W, unit, units)} — left out; the parts of a whole add up to it")
            return tx
    shares = {}
    for b in _list(e.get(BEARING)):
        s = b.get(SHARE) if isinstance(b, dict) else None
        if isinstance(s, bool) or not str(s).isdigit() or not str(s).isascii() or int(str(s)) < 1:
            tx['notes'].append(f"a share of {s!r} is not a whole number of parts — left out")
            return tx
        shares[str(b.get('party'))] = shares.get(str(b.get('party')), 0) + int(str(s))
    tx['paid'] = paid
    if not shares:
        tx['borne'] = dict(paid)                           # no bearers: whoever paid it bears it
    else:
        total = sum(shares.values())
        tx['borne'] = {p: Fraction(W * s, total) for p, s in shares.items()}
    return tx


def owed(tx):
    """{(debtor, creditor): amount} for one transaction: each bearer owes each payer its share of what that payer put
    in. Summed over creditors, a party's debts less its credits are exactly its position — paid less borne."""
    out = {}
    if tx['paid'] is None or not tx['whole']:
        return out
    for debtor, b in tx['borne'].items():
        for creditor, p in tx['paid'].items():
            if debtor != creditor:
                out[(debtor, creditor)] = out.get((debtor, creditor), Fraction(0)) + Fraction(b * p, tx['whole'])
    return out


def net(pairs):
    """[(debtor, creditor, amount)] — the two directions between each pair set against each other, largest first."""
    done, out = set(), []
    for (a, b) in sorted(pairs):
        if (a, b) in done or (b, a) in done:
            continue
        done.add((a, b))
        x = pairs.get((a, b), Fraction(0)) - pairs.get((b, a), Fraction(0))
        if x > 0:
            out.append((a, b, x))
        elif x < 0:
            out.append((b, a, -x))
    return sorted(out, key=lambda r: (-r[2], r[0], r[1]))


def load_beans():
    beans = {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))):
        head, _ = dmparse.read(f)
        if head is None:
            continue
        try:
            fm = dmparse.loads(head) or {}
        except Exception:
            continue
        if isinstance(fm, dict) and fm.get('bean'):
            beans[str(fm['bean'])] = fm
    return beans


def _conflict(v):
    return isinstance(v, dict) and isinstance(v.get('conflict'), list)


def read_agreement(bid, fm, mterms, cterms, pterms, units):
    """Everything this tool reads of one agreement: its parties, its transactions per currency, its clauses."""
    ag = {'bean': bid, 'title': fm.get('title'), 'parties': {}, 'txs': [], 'owed': {}, 'position': {}, 'notes': [],
          'clauses': []}
    for pt in pterms:
        for k, p in (fm.get(pt).items() if isinstance(fm.get(pt), dict) and not _conflict(fm.get(pt)) else []):
            who = p.get('who') if isinstance(p, dict) else None
            ag['parties'][str(k)] = str(who.get('bean')) if isinstance(who, dict) and who.get('bean') else None
    for term, rule in mterms:
        held = fm.get(term)
        if _conflict(held):
            ag['notes'].append(f"`{term}` holds a merge conflict nobody has resolved — nothing in it is read until a "
                               f"person chooses")
            continue
        items = list(held.items()) if isinstance(held, dict) else list(enumerate(held)) if isinstance(held, list) else []
        for k, e in items:
            if not isinstance(e, dict):
                continue
            tx = read_transaction(k, e, rule, units)
            ag['txs'].append(tx)
            if tx['paid'] is None:
                continue
            cur = tx['unit']
            for (d, c), x in owed(tx).items():
                ag['owed'].setdefault(cur, {})[(d, c)] = ag['owed'].setdefault(cur, {}).get((d, c), Fraction(0)) + x
            pos = ag['position'].setdefault(cur, {})
            for p, x in tx['paid'].items():
                pos[p] = pos.get(p, Fraction(0)) + x
            for p, x in tx['borne'].items():
                pos[p] = pos.get(p, Fraction(0)) - x
    for term, sch in cterms:
        held = fm.get(term)
        decl = sch.get('expiry') or {}
        items = list(held.items()) if isinstance(held, dict) and not _conflict(held) else \
            list(enumerate(held)) if isinstance(held, list) else []
        for k, e in items:
            if isinstance(e, dict) and not dmstale.silenced(e, decl):
                ag['clauses'].append((term, k, e, sch))
    return ag


def _when(n, today):
    d = n - today
    return 'today' if d == 0 else f"in {d} day{'s' if d != 1 else ''}" if d > 0 else f"{-d} day{'s' if d != -1 else ''} ago"


def clause_lines(term, key, e, sch, units, systems, today):
    """A clause in words: its own sentence, then every attribute the law declares for it, read by its domain — who,
    to whom, how much, when it falls due and next falls due, the condition — then what is not yet known."""
    form = dmform.attribute_form({}, sch)
    decl = sch.get('expiry') or {}
    due, rep = decl.get('attr'), decl.get('repeats')
    # ITS OWN SENTENCE FIRST: the attributes the law requires in prose (`what`), as its parties would say it.
    heading = [a for a, r in (sch.get('attrs') or {}).items()
               if form['attrs'].get(a, {}).get('required') and _in(r) == 'prose' and e.get(a) is not None]
    head = f"    {key}" + ''.join(f"  \"{e[a]}\"" for a in heading)
    facts, unknown = [], []
    for a, rec in (sch.get('attrs') or {}).items():
        f = form['attrs'].get(a, {})
        v = e.get(a)
        if a in heading or a == rep:
            continue
        if 'aspect' in f:
            facts.append(str(v if v is not None else (f['aspect'] or {}).get('default') or '—'))
        elif v is None:
            if 'quantity' in f or a == due:
                unknown.append(a)
        elif 'quantity' in f:
            c = count_of(v)
            facts.append(f"{a} " + (said(c, v.get('unit'), units) if c is not None else f"{v.get('count')!r} {v.get('unit')} "
                                    f"(not a count this reads exactly)"))
        elif a == due:
            facts.append(due_words(a, v, e.get(rep) if rep else None, systems, today))
        elif 'key_of' in f or 'values' in f or 'type' in f:
            facts.append(f"{a} {v}")
        elif 'recurrence' in f:
            facts.append(f"{a} {dmstale.describe(v)}")
        else:
            facts.append(f"{a}: \"{v}\"")
    lines = [head, "        " + ' · '.join(facts)]
    if unknown:
        lines.append("        not yet known: " + ', '.join(unknown))
    return lines


def due_words(attr, v, rec, systems, today):
    """When a clause falls due — and, for one that repeats, when it falls due NEXT, walked by bin/dmstale.py."""
    try:
        first = dmcal.to_day(str(v))
    except (ValueError, dmcal.NotByRule) as why:
        return f"{attr} {v} ({why})"
    if not isinstance(rec, dict):
        return f"{attr} {v} ({_when(first, today)})"
    try:
        day, i, times, ended = dmstale.next_due(first, rec, today, systems)
    except dmstale.Unreckoned as why:
        return f"{attr} {v}, then {dmstale.describe(rec)} — the next occurrence cannot be walked here: {why}"
    of = f" of {times}" if times is not None else ''
    return (f"{attr} {v}, then {dmstale.describe(rec)} — {'the last was' if ended else 'next'} "
            f"{dmstale.show_day(day, rec, systems)} ({_when(day, today)}), occurrence {i}{of}")


def print_agreement(ag, units, systems, today):
    print(f"== {ag['bean']}" + (f" — {ag['title']}" if ag.get('title') else ''))
    if ag['parties']:
        print("   parties: " + ', '.join(f"{k}" + (f" [[{b}]]" if b and b != k else '') for k, b in sorted(ag['parties'].items())))
    for n in ag['notes']:
        print(f"   NOTE {n}")
    if ag['txs']:
        print(f"   transactions ({len(ag['txs'])}):")
    for tx in ag['txs']:
        if tx['whole'] is None:
            print(f"     {tx['key']}  — " + '; '.join(tx['notes']))
            continue
        line = f"     {tx['key']}" + (f"  {tx['on']}" if tx.get('on') else '') + f"  {said(tx['whole'], tx['unit'], units)}"
        if tx['paid'] is not None:
            line += "  paid by " + ', '.join(f"{p}" + ('' if len(tx['paid']) == 1 else f" {said(x, tx['unit'], units)}")
                                             for p, x in sorted(tx['paid'].items()))
            line += ("  · borne by " + ', '.join(f"{p} {said(x, tx['unit'], units, note=False)}" for p, x in sorted(tx['borne'].items()))
                     if tx['borne'] != tx['paid'] else "  · borne by whoever paid it")
        print(line + (f"  \"{tx['what']}\"" if tx.get('what') else ''))
        if tx['priced']:
            c, u = tx['priced']
            rate = Fraction(tx['whole'], c)
            text = dmunits.show(rate)
            ap = dmunits.approx(rate) if '/' in text else None
            print(f"       priced {said(c, u, units)}, charged {said(tx['whole'], tx['unit'], units)}: "
                  f"{text} {tx['unit']} per {u}" + (f" (≈ {ap})" if ap else '') + " — a reading of the statement, never a stored rate")
        odd = uneven_note(list(tx['borne'].values()), tx['unit'], units) if tx['borne'] else None
        for n in tx['notes'] + ([odd] if odd else []):
            print(f"       NOTE {n}")
    for cur in sorted(ag['position']):
        pos = ag['position'][cur]
        print(f"   {cur}  position (paid less borne): " + ' · '.join(f"{p} {said(x, cur, units, sign=True, note=False)}"
                                                                     for p, x in sorted(pos.items())))
        lines = net(ag['owed'].get(cur, {}))
        for d, c, x in lines:
            print(f"   {d} owes {c} {said(x, cur, units)}")
        if not lines:
            print(f"   {cur}: settled — nobody owes anybody")
    if ag['clauses']:
        print(f"   clauses in force ({len(ag['clauses'])}):")
        for term, key, e, sch in ag['clauses']:
            for l in clause_lines(term, key, e, sch, units, systems, today):
                print(l)
    print()


def main(argv):
    if argv and argv[0] in ('-h', '--help'):
        print(__doc__); return 0
    between = None
    if '--between' in argv:
        i = argv.index('--between')
        between = argv[i + 1:i + 3]
        argv = argv[:i] + argv[i + 3:]
        if len(between) != 2 or between[0] == between[1]:
            print("dmledger: --between takes two party beans, e.g. --between sam ali"); return 2
    terms, units, systems = law()
    mterms = money_terms(terms)
    pterms = sorted({r['parties'] for _t, r in mterms if r['parties']})
    cterms = clause_terms(terms, pterms)
    beans = load_beans()
    for b in argv + (between or []):
        if b not in beans:
            print(f"dmledger: no bean '{b}' in {os.path.join(ROOT, 'beans')}"); return 2
    today = datetime.date.today().toordinal()
    held = [t for t, _r in mterms] + [t for t, _s in cterms]
    chosen = argv or sorted(b for b, fm in beans.items() if any(fm.get(t) is not None for t in held))
    ags = [read_agreement(b, beans[b], mterms, cterms, pterms, units) for b in chosen]
    if between:
        return print_between(between, ags, units)
    if not ags:
        print("dmledger: no agreement here records what moved or what is owed (" + ', '.join(held) + ")")
    for ag in ags:
        print_agreement(ag, units, systems, today)
    return 0


def print_between(pair, ags, units):
    """Two parties, netted across every agreement both are party to — per currency, never across two."""
    a, b = pair
    total, shared = {}, 0
    print(f"== between {a} and {b}")
    for ag in ags:
        ka = [k for k, bean in ag['parties'].items() if bean == a]
        kb = [k for k, bean in ag['parties'].items() if bean == b]
        if not ka or not kb:
            continue
        shared += 1
        for cur in sorted(ag['owed']):
            pairs = ag['owed'][cur]
            if not any((d in ka and c in kb) or (d in kb and c in ka) for d, c in pairs):
                continue                                  # nothing moved between these two, whatever moved between others
            x = sum((v for (d, c), v in pairs.items() if d in ka and c in kb), Fraction(0)) - \
                sum((v for (d, c), v in pairs.items() if d in kb and c in ka), Fraction(0))
            total[cur] = total.get(cur, Fraction(0)) + x
            print(f"   {ag['bean']}: " + (f"{a} owes {b} {said(x, cur, units)}" if x > 0 else
                                         f"{b} owes {a} {said(-x, cur, units)}" if x < 0 else f"settled in {cur}"))
    if not shared:
        print(f"   no agreement here has both {a} and {b} among its parties")
        return 0
    if not total:
        print(f"   nothing recorded has moved between them in {shared} agreement{'s' if shared != 1 else ''}")
        return 0
    print(f"   net, across {shared} agreement{'s' if shared != 1 else ''}:")
    for cur in sorted(total):
        x = total[cur]
        print(f"   {a} owes {b} {said(x, cur, units)}" if x > 0 else
              f"   {b} owes {a} {said(-x, cur, units)}" if x < 0 else f"   {cur}: settled — neither owes the other")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
