"""books_walks — the books' operations, each a walk of the garden whose plan is a write (bin/walktool.py `plan_writes`):
what it would add to the books and take out of them, shown to a person, ratified, written as shown, read back.

    write = books_walks.PLANS[<operation>](B, inputs, today)   # {what, body, beans}; a refusal raises W.Refused

Each operation reads its inputs by name (bin/walktool.py `inputs`: a page's action's inputs, `--input`s at the
terminal), and writes in the entity's books bean — the bean that holds its books' `open`, else the one holding most of
its bookings, else `books-<entity>`, made by the first write:

  book     `of` (a payment, `<bean>#<id>`), `account` (a postable account, by its code or its name), `analytic` (a code
           of a plan, optional), `means` (the account it was paid through, where the payment does not say it), `note`.
           The entity's part goes to the account; a booking of the same side made before is taken out where the
           payment's day is after the books' last close, and moved by a booking of it from the old account to the new
           one, on today, where it is not — a closed period is never rewritten.
  reverse  `of` (a payment, or a booking), `day` (today where none), `reason`: the move in the reverse sense from the
           day, which is after the last close.
  match    `line` (a payment read from a source), `payment` (the payment said): one movement, counted once; refused
           where their amounts differ, where either is matched already, or where the line is booked (book the payment).
  close    `day`: the books' reading through the day (`reckon`, its step `books`) and its `pin` at the commit the plan
           read — after the last close, not after today.
  entry    `day`, `memo`, `unit`, `lines` (`<account> dr|cr <amount>`, joined by `;`), `of` (optional): what no payment
           says, written whole and balanced, resting on `of` or the books' `open` (written by the first entry); an
           entry is corrected by its reverse and a new one, never edited.
  import   `file` (a path on this machine, or the SHA-256 of a file a page gave, kept by the host), `format`
           (camt.053, camt.054, ofx, mt940, csv), `means` (the being the account stands for: the bank account, the
           card), `mapping` (a CSV's, a file of the garden), `statement` (the bean's id; `statement-<the file's SHA-256,
           12>` where none): a statement bean, its lines payments read from the file through the means; refused whole
           where a line is not read, where opening + lines is not the closing, or where the file was imported already.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys
from fractions import Fraction

import books_read as br

HERE = os.path.dirname(os.path.abspath(__file__))


def _W():
    import walktool
    return walktool


def show(x):
    import units as dmunits
    return dmunits.show(x)


def refuse(why):
    raise _W().Refused(why)


# ------------------------------------------------------------------------------------------------ what the walks share
def books_bean(B):
    """(the bean the entity's bookkeeping is written in, whether a write makes it)."""
    E, counts = B.entity, {}
    for bid, b in sorted(B.G.beans.items()):
        for _i, v, r in b.items:
            if v == 'open' and str(r.get('by')) == E and r.get('of') == 'self':
                return bid, False
            if v in ('book', 'match') and str(r.get('by') or B.G.gardener) == E:
                counts[bid] = counts.get(bid, 0) + 1
    if counts:
        return max(sorted(counts), key=counts.get), False
    bid = f"books-{E}"
    return bid, bid not in B.G.beans


def new_bean(B, bid):
    return {'head': f'bean: {bid}\nkind: document\ntitle: "{bid} — the books of {B.entity}"',
            'body': f"The books of {B.entity}: the bookings, matches and closes its bookkeeper wrote, read with what "
                    f"they book (assets/accounting/README.md)."}


def statement(B, ref):
    """(bean id, verb, roles) of `<bean>#<id>`, or a refusal."""
    if not isinstance(ref, str) or '#' not in ref:
        refuse(f"{ref!r} names no statement: `<bean>#<id>`")
    bid, sid = ref.split('#', 1)
    b = B.G.beans.get(bid)
    hit = b.ids.get(sid) if b else None
    if not hit:
        refuse(f"{ref} is no statement of this garden")
    return bid, hit[1], hit[2]


def fresh_id(B, bid, base, taken=()):
    b = B.G.beans.get(bid)
    have = set(b.ids) if b else set()
    have |= set(taken)
    base = re.sub(r'[^a-z0-9-]+', '-', base.lower()).strip('-')[:60] or 'x'
    n, out = 1, base
    while out in have:
        n += 1
        out = f"{base}-{n}"
    return out


def last_close(B):
    c = br.closes(B)
    return c[-1][0] if c else None


def day_of(text, name):
    import stale as dmstale
    try:
        return dmstale.day_of(text)
    except (ValueError, TypeError):
        refuse(f"{name}: {text!r} is no day (YYYY-MM-DD)")


def iso(n):
    return datetime.date.fromordinal(n).isoformat()


def account(B, words, name):
    """A postable account of the chart, by its code (`<scheme>:<code>` or `<code>`) or its name, open on `today`."""
    C = B.chart
    w = str(words or '').strip()
    if not w:
        refuse(f"{name}: name an account of {C.scheme}")
    code = w.split(':', 1)[1] if w.startswith(C.scheme + ':') else w
    if code not in C.rows:
        named = [c for c, r in C.rows.items() if str(r.get('name') or '').strip() == w]
        if len(named) != 1:
            refuse(f"{name}: {w!r} is no code of {C.scheme}, and names " +
                   ("no account" if not named else f"{len(named)} accounts ({', '.join(named)})"))
        code = named[0]
    if code not in C.postable:
        refuse(f"{name}: {C.scheme}:{code} has accounts beneath it: name a postable one")
    return code


def amount_of(p):
    q = p.get('charged') if isinstance(p.get('charged'), dict) else p.get('of')
    n, u = br._count(q)
    if n is None:
        refuse("its amount is not a count read exactly")
    return n, u


def known_as(B, bid, sid):
    """The verb of the knowing act that knows statement `sid` of bean `bid`."""
    return br._knowing(B.G.beans[bid]).get(sid, (None, None))[0]


def flow(x):
    """A value written as the garden writes a statement: a flow mapping, an id or a plain word as it is, any other words
    quoted — so a statement written again reads as it was written."""
    if isinstance(x, dict):
        return '{ ' + ', '.join(f"{k}: {flow(v)}" for k, v in x.items()) + ' }'
    if isinstance(x, list):
        return '[' + ', '.join(flow(v) for v in x) + ']'
    t = str(x)
    plain = re.fullmatch(r'[a-z][a-z0-9-]*', t) and t not in ('true', 'false', 'null', 'yes', 'no', 'on', 'off')
    return t if plain else json.dumps(t, ensure_ascii=False)


def kept_known(B, bid, removing):
    """(the ids to take out beside `removing`, the statements to write again): a knowing act of bean `bid` that knows a
    statement taken out goes with all it knew (bin/walktool.py: all, or none), so what else it knew is taken out and
    written again as it was — known now by whoever ratifies the plan."""
    b = B.G.beans.get(bid)
    gone, more, again = set(removing), [], []
    if b is None:
        return more, again
    for _i, v, r in b.items:
        if v in br.KNOWING and gone & set(br._listed(r.get('of'))):
            for x in br._listed(r.get('of')):
                if x not in gone and x in b.ids:
                    gone.add(x)
                    more.append(x)
                    _j, verb, roles = b.ids[x]
                    again.append(f"{verb}: {flow(roles)}")
    return more, again


# ------------------------------------------------------------------------------------------------ book
def book(B, I, today, run=(None, None)):
    ref = I.get('of')
    bid, verb, p = statement(B, ref)
    if verb != 'pay':
        refuse(f"{ref} is a `{verb}`: the walk books a payment (`entry` books what no payment says)")
    E, C = B.entity, B.chart
    by, to = str(p.get('by')), str(p.get('to') or '')
    bears = [r for _i, v, r in B.G.beans[bid].items if v == 'bear' and r.get('of') in (p.get('id'), ref)]
    if E not in (by, to) and E not in {str(r.get('by')) for r in bears}:
        refuse(f"{ref} is no payment of {E}'s: {E} paid, received and bears none of it")
    matched = [r for b in B.G.beans.values() for _i, v, r in b.items if v == 'match'
               and ref in [x if '#' in str(x) else f"{b.id}#{x}" for x in br._listed(r.get('of'))]]
    if matched and known_as(B, bid, p.get('id')) == 'read':
        refuse(f"{ref} is a line matched with what was said of it: book the payment said, which carries the bookings")
    side = 'from' if (to == E and by != E) else 'to'
    other = 'to' if side == 'from' else 'from'
    code = account(B, I.get('account'), 'account')
    closed = (C.rows.get(code) or {}).get('closed')
    if closed and today > day_of(closed, 'closed'):
        refuse(f"account: {C.scheme}:{code} closed on {closed}")
    books, made = books_bean(B)
    pday = br._day(p.get('at'))
    shut = last_close(B)
    in_closed = shut is not None and pday is not None and pday <= shut
    mine = [(b.id, r) for b in B.G.beans.values() for _i, v, r in b.items if v == 'book' and isinstance(r.get('id'), str)
            and str(r.get('by') or B.G.gardener) == E and r.get('of') in (ref, p.get('id') if b.id == bid else None)
            and str(r.get('sense') or '1') == '1']
    before = [(b_, r) for b_, r in mine if str(r.get(side) or '').startswith(C.scheme + ':') and r.get(other) is None]
    ana_before = [(b_, r) for b_, r in mine if r.get('from') is None and isinstance(r.get('to'), str)
                  and r['to'].split(':', 1)[0] in B.analytic]
    taken, adds, removes, said = set(), [], {}, []
    base = fresh_id(B, books, f"bk-{ref.replace('#', '-')}")
    taken.add(base)
    note = f", note: {json.dumps(I['note'], ensure_ascii=False)}" if I.get('note') else ''
    if in_closed and before:
        # A CLOSED PERIOD IS NEVER REWRITTEN: what was booked stays, and a booking of it moves it, on today
        voucher = next((v for v in B.vouchers if v['ref'] == ref), None)
        for b_, r in before:
            old = str(r[side]).split(':', 1)[1]
            if old == code:
                refuse(f"{ref} is booked to {C.scheme}:{code} already")
            amt = sum((ln['dr'] - ln['cr'] for ln in (voucher or {}).get('lines', []) if ln['account'] == old),
                      Fraction(0))
            if not amt:
                refuse(f"{ref}: what {b_}#{r['id']} placed in {C.scheme}:{old} is not read in the books")
            mid = fresh_id(B, books, f"{base}-moved", taken)
            taken.add(mid)
            frm, too = (old, code) if amt > 0 else (code, old)
            of = r['id'] if b_ == books else f"{b_}#{r['id']}"
            adds.append(f'book: {{ id: {mid}, of: "{of}", from: "{C.scheme}:{frm}", to: "{C.scheme}:{too}", '
                        f'share: {{ count: "{show(abs(amt))}", unit: {voucher["unit"]} }}, '
                        f'at: "{iso(today)}"{note} }}')
            said.append(f"{ref}'s day is in the books closed through {iso(shut)}: what it placed in {C.scheme}:{old} "
                        f"is moved to {C.scheme}:{code} on {iso(today)}")
        for name in ('analytic', 'means'):
            if I.get(name):
                refuse(f"{name}: {ref}'s day is in the books closed through {iso(shut)}: its {name} stays as closed")
    else:
        if before and all(str(r[side]) == f"{C.scheme}:{code}" for _b, r in before) and not I.get('analytic') \
                and not I.get('means'):
            refuse(f"{ref} is booked to {C.scheme}:{code} already")
        for b_, r in before:
            removes.setdefault(b_, []).append(r['id'])
        adds.append(f'book: {{ id: {base}, of: "{ref}", {side}: "{C.scheme}:{code}"{note} }}')
        said.append(f"{ref}: {E}'s part booked {side} {C.scheme}:{code}" +
                    (f", replacing {', '.join(r['id'] for _b, r in before)}" if before else ''))
        if I.get('analytic'):
            sch, acode = analytic(B, I['analytic'])
            for b_, r in ana_before:
                if r['to'].split(':', 1)[0] == sch:
                    removes.setdefault(b_, []).append(r['id'])
            aid = fresh_id(B, books, f"{base}-a", taken)
            taken.add(aid)
            adds.append(f'book: {{ id: {aid}, of: "{ref}", to: "{sch}:{acode}" }}')
            said.append(f"{ref}: its part belongs to {sch}:{acode}")
        if I.get('means'):
            mcode = account(B, I['means'], 'means')
            for b_, r in mine:
                if str(r.get(other) or '').startswith(C.scheme + ':') and r.get(side) is None:
                    removes.setdefault(b_, []).append(r['id'])
            mid = fresh_id(B, books, f"{base}-m", taken)
            adds.append(f'book: {{ id: {mid}, of: "{ref}", {other}: "{C.scheme}:{mcode}" }}')
            said.append(f"{ref}: {'paid through' if other == 'from' else 'received into'} {C.scheme}:{mcode}")
    entries, again_books = [], []
    for b_, ids in sorted(removes.items()):
        more, again = kept_known(B, b_, ids)
        removes[b_] = sorted(set(ids) | set(more))
        if b_ != books:
            entries.append({'bean': b_, 'add': again, 'remove': removes[b_]})
        else:
            again_books = again
    own = {'bean': books, 'add': again_books + adds, 'remove': sorted(set(removes.get(books, [])))}
    if made:
        own['new'] = new_bean(B, books)
    entries.insert(0, own)
    return {'what': f"{ref} booked to {C.scheme}:{code}", 'beans': entries,
            'body': [f"- action: {s}" for s in said] + [f"- action: wrote [[{e['bean']}]]" for e in entries]}


def analytic(B, words):
    """(scheme, code) of an analytic code, `<scheme>:<code>` or a code one of the garden's plans holds once."""
    import knowledge as dmknowledge
    K = dmknowledge.Knowledge(B.root)
    w = str(words).strip()
    found = []
    for sch in B.analytic:
        try:
            codes = {str(r.get('code')) for r in K.rows(sch)}
        except (KeyError, OSError):
            continue
        c = w.split(':', 1)[1] if w.startswith(sch + ':') else w
        if c in codes:
            found.append((sch, c))
    if len(found) != 1:
        refuse(f"analytic: {w!r} is " + ("no code of a plan of this garden" if not found else
                                          f"a code of {len(found)} plans: say which, `<scheme>:<code>`"))
    return found[0]


# ------------------------------------------------------------------------------------------------ reverse
def reverse(B, I, today, run=(None, None)):
    ref = I.get('of')
    bid, verb, r = statement(B, ref)
    if verb not in ('pay', 'book'):
        refuse(f"{ref} is a `{verb}`: a payment or a booking is reversed")
    if verb == 'book' and str(r.get('sense') or '1') == '-1':
        refuse(f"{ref} is a reversal itself: book the move again")
    if not any(v['ref'] == ref or ref in v.get('statements', []) for v in B.vouchers) and \
            not (verb == 'book' and r.get('from') is not None and r.get('to') is not None):
        refuse(f"{ref} is not in the books of {B.entity}")
    day = day_of(I['day'], 'day') if I.get('day') else today
    shut = last_close(B)
    if shut is not None and day <= shut:
        refuse(f"day: the books are closed through {iso(shut)}: reverse it after that day")
    if not str(I.get('reason') or '').strip():
        refuse("reason: say why it is reversed")
    for b in B.G.beans.values():
        for _i, v, x in b.items:
            if v == 'book' and str(x.get('sense')) == '-1' and (x.get('of') == ref or f"{b.id}#{x.get('of')}" == ref):
                refuse(f"{ref} is reversed already ({b.id}#{x.get('id')})")
    books, made = books_bean(B)
    rid = fresh_id(B, books, f"rv-{ref.replace('#', '-')}")
    of = ref.split('#', 1)[1] if bid == books else ref
    own = {'bean': books, 'add': [f'book: {{ id: {rid}, of: "{of}", sense: "-1", at: "{iso(day)}", '
                                  f'why: {json.dumps(I["reason"].strip(), ensure_ascii=False)} }}'], 'remove': []}
    if made:
        own['new'] = new_bean(B, books)
    return {'what': f"{ref} reversed from {iso(day)}", 'beans': [own],
            'body': [f"- action: {ref} booked in the reverse sense from {iso(day)} in [[{books}]]: {I['reason'].strip()}"]}


# ------------------------------------------------------------------------------------------------ match
def match(B, I, today, run=(None, None)):
    refs = [I.get('line'), I.get('payment')]
    got = []
    for name, ref in zip(('line', 'payment'), refs):
        bid, verb, r = statement(B, ref)
        if verb != 'pay':
            refuse(f"{name}: {ref} is a `{verb}`, no payment")
        got.append((bid, r))
    if known_as(B, got[0][0], got[0][1].get('id')) != 'read':
        refuse(f"line: {refs[0]} was not read from a source: a line is what a bank's file says")
    if known_as(B, got[1][0], got[1][1].get('id')) == 'read':
        refuse(f"payment: {refs[1]} was read from a source too: match a line with the payment said")
    a, b = amount_of(got[0][1]), amount_of(got[1][1])
    if a != b:
        refuse(f"the line is {show(a[0])} {a[1]} and the payment {show(b[0])} {b[1]}: one "
               f"movement has one amount")
    E = B.entity
    for bean_ in B.G.beans.values():
        for _i, v, r in bean_.items:
            refs_r = [x if '#' in str(x) else f"{bean_.id}#{x}" for x in br._listed(r.get('of'))]
            if v == 'match' and str(r.get('by') or B.G.gardener) == E and set(refs) & set(refs_r):
                refuse(f"{', '.join(sorted(set(refs) & set(refs_r)))} is matched already ({bean_.id}#{r.get('id')})")
            if v == 'book' and str(r.get('by') or B.G.gardener) == E and refs[0] in refs_r:
                refuse(f"line: {refs[0]} is booked ({bean_.id}#{r.get('id')}): book the payment said, and take the "
                       f"line's booking out, before they are matched")
    books, made = books_bean(B)
    mid = fresh_id(B, books, f"m-{refs[1].replace('#', '-')}")
    own = {'bean': books, 'add': [f'match: {{ id: {mid}, of: ["{refs[0]}", "{refs[1]}"], at: "{iso(today)}" }}'],
           'remove': []}
    if made:
        own['new'] = new_bean(B, books)
    return {'what': f"{refs[0]} and {refs[1]}: one movement", 'beans': [own],
            'body': [f"- action: matched {refs[0]} with {refs[1]} in [[{books}]]"]}


# ------------------------------------------------------------------------------------------------ close
def asked_at(B, run):
    """The commit the close was asked at: the one before the commit that started the run (the course's `be`), or HEAD
    while that is not committed yet — the same at the plan, the check and the ratification, whatever the engine saves
    of the run between them."""
    git = lambda *a: subprocess.run(['git', '-C', B.root, *a], capture_output=True, text=True,
                                    encoding='utf-8').stdout.strip()
    bean, course = run
    b = B.G.beans.get(bean)
    rel = os.path.relpath(b.path, B.root) if b is not None and getattr(b, 'path', None) else f'beans/{bean}.md'
    started = git('log', '-n', '1', '--format=%H', '-S', f"id: {course}, by: self,", '--', rel)
    head = git('rev-parse', (started + '^') if started else 'HEAD')
    if not re.fullmatch(r'[0-9a-f]{40}', head):
        refuse("the garden has no commit to pin the books at")
    return head


def close(B, I, today, run=(None, None)):
    if not I.get('day'):
        refuse("day: the day the books are closed through")
    day = day_of(I['day'], 'day')
    if day > today:
        refuse(f"day: {iso(day)} is still to come: close a day that has passed")
    shut = last_close(B)
    if shut is not None and day <= shut:
        refuse(f"day: the books are closed through {iso(shut)} already")
    head = asked_at(B, run)
    books, made = books_bean(B)
    rid = fresh_id(B, books, f"books-{iso(day)}")
    pid = fresh_id(B, books, f"closed-{iso(day)}", {rid})
    step = f'{{ id: through, op: books, to: "{iso(day)}", chart: {B.chart.scheme}' + \
        (f', entity: {B.entity}' if B.entity != B.G.gardener else '') + ' }'
    own = {'bean': books, 'remove': [], 'add': [
        f'reckon: {{ id: {rid}, reading: {{ what: "the books of {B.entity} through {iso(day)}", steps: [ {step} ] }} }}',
        f'pin: {{ id: {pid}, of: [{rid}], at: [now, "garden@{head}"] }}']}
    if made:
        own['new'] = new_bean(B, books)
    shown = []
    for unit in sorted({v['unit'] for v in B.vouchers if v['unit']}):
        for r in br.trial(B, unit, None, day)['rows']:
            if r['posts']:
                shown.append(f"  {r['code']} {r['name']}: {show(r['closing'])} {unit}")
    print(f"the books of {B.entity} through {iso(day)}, as they are closed:\n" + '\n'.join(shown))
    return {'what': f"the books of {B.entity} closed through {iso(day)}", 'beans': [own],
            'body': [f"- action: the books of {B.entity} closed through {iso(day)}: their reading pinned at "
                     f"{head[:12]} in [[{books}]]"]}


# ------------------------------------------------------------------------------------------------ import
def import_(B, I, today, run=(None, None)):
    import statements as st
    path = name = said = str(I.get('file') or '')
    if re.fullmatch(r'[0-9a-f]{64}', path) and not os.path.isfile(path):     # a page's file: kept by the host off git,
        path = _W().file(name)                                                # under its SHA-256, which the run is given
        said = f"the file a page gave ({name[:12]}…)"
    elif not path or not os.path.isfile(path):
        refuse(f"file: {path!r} is no file on this machine, nor one a page gave (its SHA-256)")
    else:
        name = said = os.path.basename(path)
    fmt = str(I.get('format') or '')
    if fmt not in st.FORMATS:
        refuse(f"format: {fmt!r} is none of {', '.join(st.FORMATS)}")
    mapping = None
    if fmt == 'csv':
        mp = os.path.join(B.root, str(I.get('mapping') or ''))
        if not I.get('mapping') or not os.path.isfile(mp) or os.path.relpath(mp, B.root).startswith('..'):
            refuse("mapping: a CSV is read by a mapping, a file of this garden (its columns, its decimal mark, its days)")
        import yaml
        with open(mp, encoding='utf-8') as fh:
            mapping = yaml.safe_load(fh) or {}
    means = str(I.get('means') or '')
    if means not in B.chart.stands:
        refuse(f"means: {means!r} is no being an account of {B.chart.scheme} stands for: the bank account or the card "
               f"the statement is of")
    with open(path, 'rb') as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    sid = str(I.get('statement') or f"statement-{sha[:12]}")
    if not re.fullmatch(r'[a-z0-9][a-z0-9-]*', sid):
        refuse(f"statement: {sid!r} is no bean id")
    for b in B.G.beans.values():
        if ((b.header.get('details') or {}).get('statement') or {}).get('sha256') == sha:
            refuse(f"file: imported already, as [[{b.id}]]")
    if sid in B.G.beans:
        refuse(f"statement: a bean {sid} is here already")
    try:
        S = st.read(path, fmt, mapping)
    except st.Unreadable as e:
        refuse(f"file: {e}")
    if S['refused']:
        refuse("file: " + '; '.join(f"{w}: {why}" for w, why in S['refused'][:8]) + " — nothing is imported: a "
               "statement is read whole or not at all")
    if not S['lines']:
        refuse("file: it holds no line")
    total = {}
    for ln in S['lines']:
        total[ln['unit']] = total.get(ln['unit'], Fraction(0)) + Fraction(ln['count'])
    if S['opening'] and S['closing']:
        u = S['opening']['unit']
        if Fraction(S['opening']['count']) + total.get(u, 0) != Fraction(S['closing']['count']):
            refuse(f"file: its opening {S['opening']['count']} and its lines {show(total.get(u, 0))} {u} "
                   f"do not make its closing {S['closing']['count']}")
    E = B.entity
    adds = []
    for n, ln in enumerate(S['lines'], 1):
        cnt = Fraction(ln['count'])
        amt = f'{{ count: "{show(abs(cnt))}", unit: {ln["unit"]} }}'
        who = f'by: {E}' if cnt < 0 else f'by: {{ someone: org }}, to: {E}'
        note = ' '.join(x for x in (ln.get('text'), ln.get('party')) if x)
        adds.append(f'pay: {{ id: line-{n:03d}, {who}, of: {amt}, through: {means}, at: "{ln["day"]}"' +
                    (f', note: {json.dumps(note[:200], ensure_ascii=False)}' if note else '') + ' }')
    details = {'statement': {'file': name, 'sha256': sha, 'format': fmt, 'account': S['account'],
                             'opening': S['opening'], 'closing': S['closing'],
                             'lines': {f"line-{n:03d}": {k: ln.get(k) for k in ('ref', 'value_day', 'code') if ln.get(k)}
                                       for n, ln in enumerate(S['lines'], 1)}}}
    head = f'bean: {sid}\nkind: document\ntitle: "{sid} — the statement of {means}, {S["lines"][0]["day"]} to ' \
           f'{S["lines"][-1]["day"]}"\ndetails: ' + json.dumps(details, ensure_ascii=False)
    return {'what': f"{said}: {len(adds)} lines of {means}'s statement", 'beans': [
        {'bean': sid, 'new': {'head': head, 'body': f"The statement of {means}, read from {said} "
                                                    f"({fmt}): its lines as the payments it shows."},
         'add': adds, 'remove': [], 'known': {'act': 'read', 'from': means, 'through': f"file:{name}"}}],
        'body': [f"- action: wrote [[{sid}]]: {len(adds)} lines read from {said} ({fmt}, sha256 "
                 f"{sha[:12]})"]}


# ------------------------------------------------------------------------------------------------ entry
LINE = re.compile(r'^\s*(.+?)\s+(dr|cr)\s+(\d+(?:\.\d+)?)\s*$', re.I)


def side_of(B, words):
    """A side of a journal line as a booking names it: a postable account (`<scheme>:<code>`, by its code or its name),
    or a being — a party the chart holds, or a being an account stands for — as it is."""
    w = str(words).strip()
    if w in B.G.beans or w == 'unknown':
        acct, why = B.account(w)
        if acct is None:
            refuse(f"lines: {why}")
        return w
    return f"{B.chart.scheme}:{account(B, w, 'lines')}"


def entry(B, I, today, run=(None, None)):
    """A journal entry: what no payment says — the books' opening, a depreciation, a correction — written whole, its
    lines `<account> dr|cr <amount>` joined by `;`, balanced in its one currency, on a day after the last close. It rests
    on `of` (a payment, a measure, a booking), else on the books' `open`, which its first entry writes."""
    for name in ('day', 'memo', 'unit', 'lines'):
        if not str(I.get(name) or '').strip():
            refuse(f"{name}: an entry says its day, why (memo), its currency (unit) and its lines")
    day = day_of(I['day'], 'day')
    shut = last_close(B)
    if shut is not None and day <= shut:
        refuse(f"day: the books are closed through {iso(shut)}: an entry for it is written after that day")
    from core import check as dmcheck, measures
    L = dmcheck.garden_law(B.root)                  # the amounts read as the gate reads them (core/measures.py)
    unit = str(I['unit']).strip()
    why = measures.quantity_why(L, {'count': '1', 'unit': unit}, 'money')
    if why:
        refuse(f"unit: {why}")
    dr, cr = [], []
    for part in [x for x in str(I['lines']).split(';') if x.strip()]:
        m = LINE.match(part)
        if not m:
            refuse(f"lines: {part.strip()!r} is no line: `<account> dr|cr <amount>`, lines joined by `;`")
        amt = Fraction(m.group(3))
        if amt <= 0:
            refuse(f"lines: {part.strip()!r}: an amount is more than nothing")
        (dr if m.group(2).lower() == 'dr' else cr).append([side_of(B, m.group(1)), amt])
    if not dr or not cr:
        refuse("lines: an entry has a debit and a credit")
    if sum(a for _s, a in dr) != sum(a for _s, a in cr):
        refuse(f"lines: debits {show(sum(a for _s, a in dr))} and credits {show(sum(a for _s, a in cr))} {unit} do "
               f"not balance")
    for _s, a in dr + cr:
        why = measures.quantity_why(L, {'count': show(a), 'unit': unit}, 'money')
        if why:
            refuse(f"lines: {why}")
    books, made = books_bean(B)
    adds, taken = [], set()
    rests = I.get('of')
    if rests:
        rb, verb, _r = statement(B, rests)
        if verb not in ('pay', 'measure', 'book', 'open'):
            refuse(f"of: {rests} is a `{verb}`: an entry rests on a payment, a measure, a booking or the books' `open`")
        of = rests.split('#', 1)[1] if rb == books else rests
    else:
        b = B.G.beans.get(books)
        opened = next((r['id'] for _i, v, r in (b.items if b else []) if v == 'open' and r.get('of') == 'self'
                       and str(r.get('by')) == B.entity and isinstance(r.get('id'), str)), None)
        if opened is None:
            opened = fresh_id(B, books, 'opened')
            taken.add(opened)
            adds.append(f'open: {{ id: {opened}, by: {B.entity}, of: self, at: "{iso(day)}" }}')
        of = opened
    memo = json.dumps(str(I['memo']).strip(), ensure_ascii=False)
    i = j = 0
    while i < len(dr) and j < len(cr):                       # each debit met by credits, in the order written
        amt = min(dr[i][1], cr[j][1])
        bid = fresh_id(B, books, f"je-{iso(day)}", taken)
        taken.add(bid)
        adds.append(f'book: {{ id: {bid}, of: "{of}", from: "{cr[j][0]}", to: "{dr[i][0]}", share: {{ count: '
                    f'"{show(amt)}", unit: {unit} }}, at: "{iso(day)}", why: {memo} }}')
        dr[i][1] -= amt
        cr[j][1] -= amt
        i += dr[i][1] == 0
        j += cr[j][1] == 0
    own = {'bean': books, 'add': adds, 'remove': []}
    if made:
        own['new'] = new_bean(B, books)
    return {'what': f"a journal entry on {iso(day)}: {I['memo'].strip()}", 'beans': [own],
            'body': [f"- action: a journal entry on {iso(day)} in [[{books}]]: {I['memo'].strip()}"]}


PLANS = {'book': book, 'reverse': reverse, 'match': match, 'close': close, 'import': import_, 'entry': entry}
