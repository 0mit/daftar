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
             NOT YET READ: the payments recorded `under:` a clause are not matched to its occurrences, so an occurrence
             paid, paid late or unpaid is not told apart — the next one is the calendar's, whatever was paid.

EVERY FIGURE IS EXACT. A count is a whole number or a decimal written as a string, no longer than a count may be
(bin/dmunits.py, `DIGITS`), and it is read as a `fractions.Fraction`; every sum, share, balance and rate is one. This file holds no float, calls no rounding and has no
division operator — a quotient is `Fraction(n, d)` — and test/money.py reads its source to hold it to that. A share
that does not come out even in the currency's decimal places is printed as the fraction it is, `200/3 XTS`, and said to
be so: who takes the remainder is a clause the parties agree, never a rounding a tool chooses for them.

TWO CURRENCIES ARE NEVER ADDED. No factor joins two currencies (the `money` quantity says `crosswalk: observed`), so
every position, debt and net is per currency. A transaction priced in one currency and `charged` in another shows the
rate it implies — charged over amount, exactly — as a reading of the statement, never as a rate to reuse.

WHAT IS NOT READ IS SAID. A transaction whose figures cannot be read exactly, a bean whose front matter does not parse,
an entry a merge left as a disagreement for a person (`{conflict: [a, b]}`): each is left out of every total and named
in a NOTE, so a total is never smaller than it looks without the reader being told why.

The law is read, not named: the transactions are every term whose schema declares `sums`, its whole and its parts come
from that rule, the parties from the `key_of` its parts name and the party's bean from the parties term's `ref`, and the
clauses from every term that falls due between those parties (`expiry` and a `key_of` the parties). Never writes.
Exit 0; 2 when this is not a garden, or a bean named is not here or does not parse, or `--between` is not two parties.
"""
import datetime, glob, os, re, sys
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
# one place the tool names attributes of the law — the attribute and its share. Who a bearer IS is read like a payer:
# the attribute of its entries that is a key of the parties; what a share may be, from the pattern the law gives it.
# PROPOSED, NOT RATIFIED (a change to the law, class G, for a person): `sums: {whole: [charged, amount],
# parts: paid_by.amount, borne: borne_by.share}`, after which these two names leave this file and a garden's own term
# that bears in shares is read the same way.
BEARING, SHARE = 'borne_by', 'share'
# THE CONDITION THAT BRINGS A CLAUSE INTO FORCE, where that is not a date. A clause holding one has no due date to be
# missing, so its `due` is not "not yet known". The law has no construct that says which attribute is the condition —
# it says so only in the attribute's meaning — so it is named here, beside the bearer. PROPOSED, NOT RATIFIED (class G):
# `expiry: {attr: due, …, condition: when}`, after which this name leaves this file too.
CONDITION = 'when'


class NotAGarden(Exception):
    pass


def law():
    """The law as the gate loaded it: every term of both tiers, every unit (a currency among them, with its digits),
    every positioning system. Asked of bin/dmcheck.py, the way bin/dmstale.py asks it, so this reads what is in force.
    Only a garden has a law in force: without its VOCAB.md there is nothing here to read."""
    if not os.path.exists(os.path.join(ROOT, 'VOCAB.md')):
        raise NotAGarden(f"not in a garden (no VOCAB.md at {ROOT}) — run the copy of this tool in a garden's bin/")
    import dmcheck
    return dmcheck.TERMS, dmcheck.UNITS, dmcheck.SYSTEMS


def _in(rec):
    return (rec or {}).get('in') if isinstance(rec, dict) else None


def _keyed(sch, attr):
    """(field, parties-term) — the field of `attr`'s entries that is a key of a parties term: who paid, who bears."""
    fields = (_in((sch.get('attrs') or {}).get(attr)) or {}).get('entries') or {}
    return next(((f, _in(r).get('key_of')) for f, r in fields.items()
                 if isinstance(_in(r), dict) and _in(r).get('key_of')), (None, None))


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
        party = _keyed(sch, pattr)
        # WHEN IT HAPPENED: the attribute the law types as a date — found by its type, so a garden's term that names
        # its day otherwise is read the same way.
        dates = [a for a, r in (sch.get('attrs') or {}).items()
                 if isinstance(_in(r), dict) and _in(r).get('type') in ('date', 'iso_date')]
        said_as = [a for a, r in (sch.get('attrs') or {}).items() if isinstance(r, dict) and r.get('required') and _in(r) == 'prose']
        share = ((_in((sch.get('attrs') or {}).get(BEARING)) or {}).get('entries') or {}).get(SHARE)
        out.append((name, {'wholes': [w for w in wholes if w], 'parts': pattr, 'part_amount': pfield,
                           'party': party[0], 'parties': party[1], 'dates': dates, 'said_as': said_as,
                           'bearer': _keyed(sch, BEARING)[0], 'schema': sch,
                           'share_pattern': _in(share).get('pattern') if isinstance(_in(share), dict) else None}))
    return out


def party_refs(terms, names):
    """{parties-term: the attribute of its entries that is a `ref` to the party's bean} — `who`, as the law declares it."""
    out = {}
    for name in names:
        attrs = (((terms.get(name) or {}).get('schema') or {}).get('attrs') or {})
        out[name] = next((a for a, r in attrs.items() if _in(r) == 'ref'), None)
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
    """A count, exactly — or None. Only a whole number or a decimal string is read, by the gate's own pattern (one
    sign, ASCII digits, no exponent): anything else — a float above all — has already lost what it lost."""
    return read_count(q)[0]


def read_count(q):
    """(the count exactly, or None; why it is not read, or ''). A count longer than a count may be is refused by
    bin/dmunits.py with the reason, and the reason is kept for the NOTE — never a traceback that ends the reading."""
    try:
        return (dmunits.exact(q.get('count')) if isinstance(q, dict) else None), ''
    except ValueError as e:
        return None, f" ({e})"


def read_share(s, pattern):
    """A bearer's share as a whole number of parts, or None: what the law's pattern for a share admits (the gate's own
    reading), a positive whole number, and no longer than a count may be (bin/dmunits.py's DIGITS). `yes` is not a
    share, nor is `1.5`, nor five thousand digits — each of those once ended the reading in a traceback, or was read as
    something nobody wrote."""
    if isinstance(s, bool) or not isinstance(s, (int, str)):
        return None
    try:
        text = str(s)
        if pattern and not re.fullmatch(pattern, text):
            return None
        n = int(text) if text.isascii() and text.isdigit() and len(text) <= dmunits.DIGITS else None
    except (ValueError, re.error):              # an int too long for Python to write out; a pattern it cannot read
        return None
    return n if n is not None and n >= 1 else None


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
    """`in: {entries: …}` holds a list of entries, or one mapping. Anything else is one entry that is not a mapping —
    kept, so that the reader is told of it rather than find it gone."""
    return v if isinstance(v, list) else [] if v is None else [v]


def not_an_entry(v):
    """What a list of entries holds in an entry's place, in the reader's words: `an empty entry` for `- ` or `null`, `a
    list [sam]` for a list, and anything else as it is written, in backticks (`sam`) — never Python's `None` or
    `['sam']`, which nobody wrote."""
    if v is None:
        return "an empty entry"
    return f"a list {dmstale.brief(v)}" if isinstance(v, (list, tuple)) else dmstale.brief(v, quote=True)


def read_transaction(key, e, rule, units):
    """One transaction, read: {whole, unit, paid, borne, priced, notes}. `paid` and `borne` are None when it cannot be
    read exactly, and `notes` then say why — a figure left out is said to be left out, never guessed at."""
    tx = {'key': key, 'what': ' — '.join(str(e[a]) for a in rule['said_as'] if e.get(a) is not None),
          'day': next((e[a] for a in rule['dates'] if e.get(a) is not None), None),
          'notes': [], 'paid': None, 'borne': None, 'whole': None, 'unit': None, 'priced': None}
    wattr = next((w for w in rule['wholes'] if e.get(w) is not None), None)
    whole = e.get(wattr) if wattr else None
    W, why = read_count(whole)
    if W is None:
        tx['notes'].append(f"its {wattr or 'amount'} is not a count this can read exactly{why} — left out")
        return tx
    unit = str(whole.get('unit'))
    tx['whole'], tx['unit'] = W, unit
    # THE RATE A STATEMENT IMPLIES: priced in one currency, charged in another. Read exactly and shown, never stored.
    for other in rule['wholes']:
        o = e.get(other)
        if other != wattr and isinstance(o, dict) and str(o.get('unit')) != unit and count_of(o):   # a zero price implies no rate
            tx['priced'] = (count_of(o), str(o.get('unit')))
    parts = _list(e.get(rule['parts']))
    odd = [p for p in parts if not isinstance(p, dict)]
    if odd:
        # A PART THAT IS NOT AN ENTRY IS NOT DROPPED IN SILENCE: `paid_by: [sam, {party: ali, …}]` read as "paid by ali"
        # was a total that left sam out without a word. The gate refuses it; the working tree may still hold it.
        tx['notes'].append(f"{rule['parts']} holds {not_an_entry(odd[0])}, which is not an entry "
                           f"({{{rule['party']}, {rule['part_amount']}}}) — left out until it is one")
        return tx
    stated = [(p.get(rule['party']), p.get(rule['part_amount'])) for p in parts]
    if not stated:
        tx['notes'].append("nobody is recorded as having paid it — left out")
        return tx
    paid = {}
    if len(stated) == 1 and stated[0][1] is None:
        paid[str(stated[0][0])] = W                       # a single payer who states no amount paid the whole
    else:
        for who, q in stated:
            c, why = read_count(q)
            if q is None or c is None:
                tx['notes'].append(f"how much {who} paid is not known exactly{why} — left out until it is")
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
    if W == 0 and any(paid.values()):
        # A WHOLE OF NOTHING WITH PARTS THAT ARE SOMETHING: each bearer's share of a payer's part is in proportion to
        # the whole, and there is no proportion to nothing. Read, it would move the positions and owe nobody anything.
        tx['notes'].append(f"its whole is 0 {unit} and what was paid is not — no share of nothing can be read; left out. "
                           f"Money that passed from one party to another is a transaction paid by one and borne by the other")
        return tx
    shares = {}
    for b in _list(e.get(BEARING)):
        if not isinstance(b, dict):
            tx['notes'].append(f"{BEARING} holds {not_an_entry(b)}, which is not an entry "
                               f"({{{rule['bearer']}, {SHARE}}}) — left out until it is one")
            return tx
        who, s = str(b.get(rule['bearer'])), b.get(SHARE)
        if s is None:
            tx['notes'].append(f"{who} is named as bearing it and names no {SHARE} — left out until it does")
            return tx
        n = read_share(s, rule.get('share_pattern'))
        if n is None:
            tx['notes'].append(f"{who}'s {SHARE} {dmstale.brief(s, quote=True)} is not a whole number of parts as the "
                               f"law writes one — left out")
            return tx
        shares[who] = shares.get(who, 0) + n
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
    """({bean id: front matter}, {file stem: why it was not read}) — a bean that does not parse is not skipped in
    silence: whatever it records is missing from every total, and the reader is told which file and why."""
    beans, unread = {}, {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'beans', '*.md'))):
        stem = os.path.splitext(os.path.basename(f))[0]
        head, _ = dmparse.read(f)
        if head is None:
            unread[stem] = "it has no front matter"
            continue
        try:
            fm = dmparse.loads(head) or {}
        except Exception as e:
            unread[stem] = f"its front matter does not parse ({str(e).splitlines()[0] if str(e) else type(e).__name__})"
            continue
        if isinstance(fm, dict) and fm.get('bean'):
            beans[str(fm['bean'])] = fm
    return beans, unread


def _conflict(v):
    return dmstale.conflicted(v) is not None


def _differ(sides):
    """The attributes on which the sides of a disagreement differ, in words."""
    keys = sorted({str(k) for x in sides if isinstance(x, dict) for k in x})
    return [k for k in keys if len({repr(x.get(k)) if isinstance(x, dict) else repr(x) for x in sides}) > 1]


def _ref_bean(p, ref):
    r = p.get(ref) if isinstance(p, dict) and ref else None
    return str(r.get('bean')) if isinstance(r, dict) and r.get('bean') else None      # the law's ref form: {bean: <id>}


def read_agreement(bid, fm, mterms, cterms, prefs, units):
    """Everything this tool reads of one agreement: its parties, its transactions per currency, its clauses."""
    ag = {'bean': bid, 'title': fm.get('title'), 'parties': {}, 'txs': [], 'owed': {}, 'position': {}, 'notes': [],
          'clauses': [], 'disputed': []}
    for pt, ref in prefs.items():
        held = fm.get(pt)
        if _conflict(held):
            ag['notes'].append(f"`{pt}` holds a merge conflict as a whole — no party is read until a person chooses")
            continue
        for k, p in (held.items() if isinstance(held, dict) else []):
            sides = dmstale.conflicted(p)
            if sides is None:
                ag['parties'][str(k)] = _ref_bean(p, ref)
                continue
            # ONE PARTY IN DISPUTE (the parties merge member by member): where every side names the same bean, who the
            # party is stands, and only what the sides differ on waits for a person.
            who = {_ref_bean(x, ref) for x in sides}
            ag['parties'][str(k)] = who.pop() if len(who) == 1 else None
            ag['notes'].append(f"party {k} holds a merge conflict, differing in: {', '.join(_differ(sides)) or 'form'} — "
                               + ("who it is agrees, so it is read" if ag['parties'][str(k)] else
                                  "the sides name different beans, so it is read as nobody until a person chooses"))
    for term, rule in mterms:
        held = fm.get(term)
        if _conflict(held):
            ag['notes'].append(f"`{term}` holds a merge conflict nobody has resolved — nothing in it is read until a "
                               f"person chooses")
            continue
        items = list(held.items()) if isinstance(held, dict) else list(enumerate(held)) if isinstance(held, list) else []
        for k, e in items:
            sides = dmstale.conflicted(e)
            if sides is not None:
                ag['txs'].append({'key': k, 'whole': None, 'paid': None, 'borne': None, 'notes': [
                    f"holds a merge conflict — {len(sides)} sides, differing in: {', '.join(_differ(sides)) or 'form'}; "
                    f"not read until a person chooses"]})
                continue
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
        if _conflict(held):
            ag['notes'].append(f"`{term}` holds a merge conflict as a whole — no clause is read until a person chooses")
            continue
        items = list(held.items()) if isinstance(held, dict) else list(enumerate(held)) if isinstance(held, list) else []
        for k, e in items:
            sides = dmstale.conflicted(e)
            if sides is not None:
                # NEITHER IN FORCE NOR MET: one side may say `met` and the other not, and which is so is a person's call.
                # Listed apart, with what the sides differ on, so it is neither silently dropped nor silently owed.
                ag['disputed'].append((term, k, sides))
            elif isinstance(e, dict) and not dmstale.silenced(e, decl):
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
    facts, unknown, asides = [], [], []
    for a, rec in (sch.get('attrs') or {}).items():
        f = form['attrs'].get(a, {})
        v = e.get(a)
        if a in heading or a == rep:
            continue
        if 'aspect' in f:
            facts.append(str(v if v is not None else (f['aspect'] or {}).get('default') or '—'))
        elif v is None:
            # A CLAUSE IN FORCE BY A CONDITION has no due date to be missing: "not yet known: due" read as if it had one.
            if 'quantity' in f or (a == due and e.get(CONDITION) is None):
                unknown.append(a)
        elif a == CONDITION:
            facts.append(f"in force when: \"{v}\"")
        elif 'quantity' in f:
            c, why = read_count(v)
            facts.append(f"{a} " + (said(c, v.get('unit'), units) if c is not None else
                                    f"{dmstale.brief(v.get('count') if isinstance(v, dict) else v, quote=True)}"
                                    f"{' ' + str(v.get('unit')) if isinstance(v, dict) else ''} "
                                    f"(not a count this reads exactly{why})"))
        elif a == due:
            text, asides = due_words(a, v, e.get(rep) if rep else None, systems, today)
            facts.append(text)
        elif 'key_of' in f or 'values' in f or 'type' in f:
            facts.append(f"{a} {v}")
        elif 'recurrence' in f:
            facts.append(f"{a} {dmstale.describe(v)}")
        else:
            facts.append(f"{a}: \"{v}\"")
    lines = [head, "        " + ' · '.join(facts)]
    if unknown:
        lines.append("        not yet known: " + ', '.join(unknown))
    return lines + [f"        NOTE {n}" for n in asides]


def due_words(attr, v, rec, systems, today):
    """(text, notes) — when a clause falls due and, for one that repeats, when it falls due NEXT, walked by
    bin/dmstale.py; the notes name each cell the walk skipped on the way to it (a month without the day named)."""
    shown = dmstale.brief(v)
    try:
        first = dmcal.to_day(str(v))
    except (ValueError, dmcal.NotByRule) as why:
        return f"{attr} {shown} ({why})", []
    if not isinstance(rec, dict):
        return f"{attr} {shown} ({_when(first, today)})", []
    skipped, notes = [], []
    fw = dmstale.from_words(first, rec, attr, v)
    try:
        day, i, times, ended = dmstale.next_due(first, rec, today, systems, skipped=skipped)
    except dmstale.Unreckoned as why:
        return (f"{attr} {shown}, then {dmstale.describe(rec)} — the next occurrence cannot be walked here: {why}",
                [fw] if fw else [])
    of = f" of {times}" if times is not None else ''
    return (f"{attr} {shown}, then {dmstale.describe(rec)} — {'the last was' if ended else 'next'} "
            f"{dmstale.show_day(day, rec, systems, notes=notes)} ({_when(day, today)}), occurrence {i}{of}",
            notes + ([] if ended else [dmstale.skip_words(c) for c in skipped]) + ([fw] if fw else []))


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
        line = f"     {tx['key']}" + (f"  {tx['day']}" if tx.get('day') else '') + f"  {said(tx['whole'], tx['unit'], units)}"
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
            print(dmunits.speakable(f"       priced {said(c, u, units)}, charged {said(tx['whole'], tx['unit'], units)}: "
                  f"{text} {tx['unit']} per {u}" + (f" (≈ {ap})" if ap else '') + " — a reading of the statement, never a stored rate"))
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
    if ag['disputed']:
        print(f"   clauses in a merge conflict ({len(ag['disputed'])}) — neither in force nor met until a person chooses:")
        for term, key, sides in ag['disputed']:
            print(f"    {key}  NOTE {len(sides)} sides, differing in: {', '.join(_differ(sides)) or 'form'}")
    print()


def main(argv):
    # A PIPE ON WINDOWS IS WRITTEN IN THE ANSI CODE PAGE: a glyph it cannot carry (a party's name in Persian, a date in
    # another calendar's script) is replaced rather than let the reading die half-printed — which is when an agent,
    # reading through a pipe, would see it die.
    try:
        sys.stdout.reconfigure(errors='replace')
    except (AttributeError, ValueError):
        pass
    if argv and argv[0] in ('-h', '--help'):
        # the interpreter as it is named where this runs: `python3` may be the Microsoft Store's alias on Windows
        print(dmunits.speakable(__doc__.replace('python3 bin/', ('python' if os.name == 'nt' else 'python3') + ' bin/')))
        return 0
    between = None
    if '--between' in argv:
        i = argv.index('--between')
        between = argv[i + 1:i + 3]
        argv = argv[:i] + argv[i + 3:]
        if len(between) != 2 or between[0] == between[1]:
            print("dmledger: --between takes two party beans, e.g. --between sam ali"); return 2
    try:
        terms, units, systems = law()
    except NotAGarden as e:
        print(f"dmledger: {e}"); return 2
    mterms = money_terms(terms)
    pterms = sorted({r['parties'] for _t, r in mterms if r['parties']})
    prefs = party_refs(terms, pterms)
    cterms = clause_terms(terms, pterms)
    beans, unread = load_beans()
    for b in argv + (between or []):
        if b in unread:
            print(f"dmledger: the bean '{b}' is here and cannot be read: {unread[b]}"); return 2
        if b not in beans:
            print(f"dmledger: no bean '{b}' in {os.path.join(ROOT, 'beans')}"); return 2
    today = datetime.date.today().toordinal()
    held = [t for t, _r in mterms] + [t for t, _s in cterms]
    for stem, why in sorted(unread.items()):
        print(f"NOTE beans/{stem}.md is not read — {why}; whatever it records is missing from every total below")
    chosen = argv or sorted(b for b, fm in beans.items() if any(fm.get(t) is not None for t in held))
    ags = [read_agreement(b, beans[b], mterms, cterms, prefs, units) for b in chosen]
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
