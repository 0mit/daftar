#!/usr/bin/env python3
"""books — the books of an entity, read: the accounting profile's readings (lib/books_read.py).

    python3 assets/accounting/bin/books.py vouchers [--from <day>] [--to <day>] [--json]
    python3 assets/accounting/bin/books.py trial    --unit <currency> [--from <day>] [--to <day>] [--json]
    python3 assets/accounting/bin/books.py ledger   <code> --unit <currency> [--party <bean>] [--from] [--to] [--json]
    python3 assets/accounting/bin/books.py pl       --unit <currency> [--from <day>] [--to <day>] [--json]
    python3 assets/accounting/bin/books.py balance  --unit <currency> [--at <day>] [--json]
    python3 assets/accounting/bin/books.py open     [--json]
    python3 assets/accounting/bin/books.py closes   [--json]
    python3 assets/accounting/bin/books.py setup --by <who> [--tool <bean>]     # the walks, written into the garden
    python3 assets/accounting/bin/books.py <step> <bean> <course>               # a walk's step, run by bin/act.py

Each takes `--entity <bean>` (whose books; the gardener's by default), `--chart <scheme>` (the garden's one chart by
default) and `--today <day>` (the day clauses have fallen due by; today by default).

Every figure exact: a decimal where it terminates, n/d where it does not; a day a civil day, `YYYY-MM-DD`. With
`--json`, the same reading as data, every amount a count as text, never a JSON number. The books are read each time
(lib/books_read.py), never stored; exit 2 when a reading cannot be read (no chart, two charts and none named, no
currency named), with the reason.
"""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [os.path.join(os.path.dirname(HERE), 'lib'), ROOT, os.path.join(ROOT, 'bin')]
import books_read as br  # noqa: E402
import units as dmunits  # noqa: E402
import walktool as W  # noqa: E402


def _arg(a, flag, default=None):
    return a[a.index(flag) + 1] if flag in a and a.index(flag) + 1 < len(a) else default


def _day(text):
    import stale as dmstale
    return dmstale.day_of(text) if text else None


def plain(x):
    from fractions import Fraction
    if isinstance(x, Fraction):
        return dmunits.show(x)
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x


def text(cmd, out):
    """The reading as lines a person reads: every value a document holds through the one escaper (bin/parse.py)."""
    import parse as dmparse
    e, f = dmparse.escaped, lambda x: dmunits.show(x) if x else ''
    if cmd == 'vouchers':
        for v in out:
            yield f"{v['number']:>4}  {v['day'] or '(no day)'}  {e(v['ref'])}  {v['as']}  {v['unit'] or ''}" \
                  + ('' if v['balanced'] else '  NOT BALANCED')
            for ln in v['lines']:
                yield f"        {e(ln['account']):<8} {f(ln['dr']):>14} {f(ln['cr']):>14}  {e(ln['party'] or '')}"
            for n in v['notes']:
                yield f"        note: {e(n)}"
    elif cmd == 'trial':
        yield f"{'code':<8} {'name':<32} {'opening':>14} {'debit':>14} {'credit':>14} {'closing':>14}  {out['unit']}"
        for r in out['rows']:
            yield f"{e(r['code']):<8} {e(r['name'])[:32]:<32} {f(r['opening']):>14} {f(r['dr']):>14} {f(r['cr']):>14} " \
                  f"{f(r['closing']):>14}"
        t = out['totals']
        yield f"{'':<8} {'total':<32} {f(t['opening']):>14} {f(t['dr']):>14} {f(t['cr']):>14}  " \
              + ('balanced' if out['balanced'] else 'NOT BALANCED')
    elif cmd == 'ledger':
        yield f"{e(out['code'])}{' ' + e(out['party']) if out['party'] else ''}  opening {f(out['opening']) or 0} {out['unit']}"
        for r in out['rows']:
            yield f"{r['number']:>4}  {r['day'] or ''}  {e(r['ref']):<28} {f(r['dr']):>14} {f(r['cr']):>14} " \
                  f"{dmunits.show(r['balance']):>14}  {e(r['memo'] or '')}"
        yield f"closing {dmunits.show(out['closing'])} {out['unit']}"
    elif cmd in ('pl', 'balance'):
        groups = ('income', 'expense') if cmd == 'pl' else ('assets', 'liabilities', 'equity')
        for g in groups:
            yield g
            for r in out[g]:
                yield f"  {e(r['code']):<8} {e(r['name'])[:32]:<32} {dmunits.show(r['balance']):>14}"
        yield f"result {dmunits.show(out['result'])} {out['unit']}"
    elif cmd == 'open':
        for x in out:
            yield f"{x['day'] or '(no day)'}  {e(x['ref'])}  {e(x['account'])}  {f(x['dr']) or '-' + f(x['cr'])} {x['unit']}"
    elif cmd == 'closes':
        for x in out:
            yield f"through {x['day']}  at {x['commit'][:12]}  {e(x['pin'])}"


# ------------------------------------------------------------------------------------------------ the walks
WALK = 'walk-books-'            # each operation a walk of the garden, `walk-books-<operation>` (written by `setup`)


def _run(bean, course, show):
    """The write the run's operation plans, from its inputs (bin/walktool.py `inputs`), read against the books now."""
    import books_walks as bw
    walk, _steps = W.course(bean, course)
    op = walk[len(WALK):] if walk.startswith(WALK) else None
    if op not in bw.PLANS:
        raise W.Refused(f"{walk} is no walk of the books: walk-books-<{'|'.join(bw.PLANS)}>")
    I = W.inputs() if hasattr(W, 'inputs') else {}
    try:
        B = br.read(ROOT, entity=I.get('entity'), chart=I.get('chart'))
    except ValueError as e:
        raise W.Refused(str(e))
    write = bw.PLANS[op](B, I, datetime.date.today().toordinal(), (bean, course))
    return W.plan_writes(write) if show else write


def plan(bean, course):
    _run(bean, course, True)


def check(bean, course):
    """What the plan said holds still: the inputs read against the books as they are now, refused as at plan time."""
    import contextlib
    import io
    with contextlib.redirect_stdout(io.StringIO()):
        _run(bean, course, False)


SETUP = """---
bean: {walk}
kind: procedure
title: "{walk} — {title}"
statements:
  - say:  {{ by: {who}, at: now }}
  - use:  {{ by: self, of: {tool} }}
  - step: {{ id: plan, as: "what it would write, changing nothing", by: engine, to: [show] }}
  - step: {{ id: show, as: "the plan, shown", by: engine, to: [check] }}
  - step: {{ id: check, as: "the books allow it still", by: engine, to: [ratify] }}
  - step: {{ id: ratify, as: "the bookkeeper ratifies it", by: ratifier, to: [apply, show] }}
  - step: {{ id: apply, as: "written, as shown", by: engine, to: [verify] }}
  - step: {{ id: verify, as: "read back", by: engine, to: [done] }}
  - step: {{ id: done, as: "{done}", walk: {{ final: "true" }} }}
  - step: {{ id: refused, as: "nothing was written", walk: {{ exit: "true", reasons: [cannot-plan, check-failed, declined] }} }}
  - step: {{ id: rolled-back, as: "what was written taken out", walk: {{ exit: "true", reasons: [apply-failed, verify-mismatch] }} }}
---
{body}
"""
OPS = {'book': ('a payment booked where it belongs', 'booked',
                'A payment booked to an account: `of`, `account`, `analytic`, `means`, `note`.'),
       'reverse': ('a move booked in the reverse sense', 'reversed',
                   'A payment or a booking reversed from a day: `of`, `day`, `reason`.'),
       'match': ('a line and a payment, one movement', 'matched',
                 "A bank's line and the payment said, counted once: `line`, `payment`."),
       'close': ('the books closed through a day', 'closed',
                 "The books' reading through a day, pinned at a commit: `day`."),
       'entry': ('a journal entry, written whole', 'written',
                 'What no payment says, balanced: `day`, `memo`, `unit`, `lines` (`<account> dr|cr <amount>; …`), `of`.'),
       'remove': ('a document, or a payment recorded by mistake, taken out', 'taken out',
                  'A document recorded by mistake taken out whole, or a payment out of its bean, with what of the books '
                  'names it: `of`, `reason`.'),
       'chart': ('an account of the chart, added or changed', 'written',
                 "An account of the chart added beneath its parent, or changed — a row of the garden's own table: `code`, "
                 '`name`, `parent`, `level`, `element`, `stands-for`, `parties`, `role`, `closed`, `name-<lang>`.'),
       'import': ("a bank's statement read into the garden", 'imported',
                  "A statement file read into a bean of its lines: `file`, `format`, `means`, `mapping`, `statement`.")}


def setup(argv):
    """`setup --by <who> [--tool <bean>]`: the books' walks and their tool written into this garden as its own — each a
    bean of the garden's kind `procedure` using the tool, a `program` at this host's copy of this file — written, not
    saved: the gardener reads them and saves them (bin/save.py), a RULE-CHANGE where VOCAB.md must take a row first."""
    import platform                     # this machine's name, as bin/where.py reads it; no network is opened
    who = _arg(argv, '--by')
    tool = _arg(argv, '--tool', 'books-tool')
    if not who:
        print("books: setup --by <who>: the person who writes the walks", file=sys.stderr)
        return 2
    from core import engine
    G = engine.Garden.read(ROOT)
    missing = []
    vocab = open(os.path.join(ROOT, 'VOCAB.md'), encoding='utf-8').read() if os.path.isfile(
        os.path.join(ROOT, 'VOCAB.md')) else ''
    if not re.search(r'kind:\s*procedure\b', vocab):
        missing.append('kinds: - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }')
    try:
        host = W.this_host()
    except W.Refused as e:
        missing.append(f"a host bean naming this machine ({platform.node()}): {e}")
        host = None
    if missing:
        print("books: setup needs, first:\n  " + '\n  '.join(missing), file=sys.stderr)
        return 2
    wrote = []
    if tool not in G.beans:
        import parse as dmparse
        import where as dmwhere
        path = os.path.join(ROOT, 'beans', f'{tool}.md')
        try:            # this file on this machine, in the law's form (`<host>:/…`, `<host>:<Drive>:\…`), quoted as read
            at = dmparse.quoted(dmwhere.literal(os.path.abspath(os.path.join(HERE, 'books.py'))))
        except ValueError as e:
            print(f"books: setup cannot say where its tool is on this machine: {e}", file=sys.stderr)
            return 2
        with open(path, 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(f'---\nbean: {tool}\nkind: program\ntitle: "{tool} — the books\' tool"\nstatements:\n'
                     f'  - make: {{ by: {who}, at: now }}\n'
                     f'  - be: {{ by: self, at: {at}, as: location }}\n---\n'
                     f'The accounting profile\'s tool, as this garden runs it on {host}: each walk of the books runs '
                     f'its steps.\n')
        wrote.append(tool)
    for op, (title, done, body) in OPS.items():
        walk = WALK + op
        if walk in G.beans:
            continue
        os.makedirs(os.path.join(ROOT, 'mappings'), exist_ok=True)
        with open(os.path.join(ROOT, 'mappings', f'{walk}.md'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(SETUP.format(walk=walk, title=title, who=who, tool=tool, done=done, body=body))
        wrote.append(walk)
    if not wrote:
        print("books: the walks and their tool are this garden's already")
        return 0
    print("written, not saved: " + ', '.join(wrote) + "\nread them, then save them:\n  python3 bin/save.py "
          f"{who} \"the books' walks\" --body \"- action: wrote " + ', '.join(f'[[{b}]]' for b in wrote) + '"')
    return 0


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    if argv[0] in ('plan', 'check', 'apply', 'verify', 'restore'):
        return W.main('books', {'plan': plan, 'check': check, 'apply': W.apply_writes, 'verify': W.verify_writes,
                                'restore': W.restore_writes}, argv=argv)
    if argv[0] == 'setup':
        return setup(argv[1:])
    cmd, a = argv[0], argv[1:]
    if cmd not in ('vouchers', 'trial', 'ledger', 'pl', 'balance', 'open', 'closes'):
        print(f"books: no reading {cmd!r} — one of vouchers, trial, ledger, pl, balance, open, closes", file=sys.stderr)
        return 2
    unit = _arg(a, '--unit')
    if cmd in ('trial', 'ledger', 'pl', 'balance') and not unit:
        print(f"books: {cmd} is read in one currency: --unit <currency> (two currencies are never added)", file=sys.stderr)
        return 2
    if cmd == 'ledger' and (not a or a[0].startswith('--')):
        print("books: ledger <code>: name the account", file=sys.stderr)
        return 2
    try:
        today = _day(_arg(a, '--today')) or datetime.date.today().toordinal()
        start, end, at = _day(_arg(a, '--from')), _day(_arg(a, '--to')), _day(_arg(a, '--at'))
        B = br.read(ROOT, entity=_arg(a, '--entity'), chart=_arg(a, '--chart'), today=today)
    except ValueError as e:
        print(f"books: {e}", file=sys.stderr)
        return 2
    day = lambda n: datetime.date.fromordinal(n).isoformat() if n else None
    if cmd == 'vouchers':
        out = [dict(v, day=day(v['day'])) for v in B.vouchers if br._within(v, start, end)]
    elif cmd == 'trial':
        out = br.trial(B, unit, start, end)
    elif cmd == 'ledger':
        out = br.ledger(B, a[0], unit, _arg(a, '--party'), start, end)
        out['rows'] = [dict(r, day=day(r['day'])) for r in out['rows']]
    elif cmd == 'pl':
        out = br.statement(B, unit, start, end)
    elif cmd == 'balance':
        out = br.balance(B, unit, at)
    elif cmd == 'open':
        out = [dict(x, day=day(x['day'])) for x in br.open_items(B)]
    else:
        out = [{'day': day(d), 'commit': sha, 'pin': pin} for d, sha, pin in br.closes(B)]
    if '--json' in a:                                   # a reading's notes beside it; a list's, on the error stream
        print(json.dumps(plain(dict(out, notes=B.notes) if isinstance(out, dict) else out), ensure_ascii=False,
                         indent=1, default=str))
        for n in B.notes if isinstance(out, list) else ():
            print(f"note: {n}", file=sys.stderr)
    else:
        for ln in text(cmd, out):
            print(ln)
        for n in B.notes:
            print(f"note: {n}")
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
