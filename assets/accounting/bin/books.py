#!/usr/bin/env python3
"""books — the books of an entity, read: the accounting profile's readings (lib/books_read.py).

    python3 assets/accounting/bin/books.py vouchers [--from <day>] [--to <day>] [--json]
    python3 assets/accounting/bin/books.py trial    --unit <currency> [--from <day>] [--to <day>] [--json]
    python3 assets/accounting/bin/books.py ledger   <code> --unit <currency> [--party <bean>] [--from] [--to] [--json]
    python3 assets/accounting/bin/books.py pl       --unit <currency> [--from <day>] [--to <day>] [--json]
    python3 assets/accounting/bin/books.py balance  --unit <currency> [--at <day>] [--json]
    python3 assets/accounting/bin/books.py open     [--json]
    python3 assets/accounting/bin/books.py closes   [--json]

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
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
sys.path[:0] = [os.path.join(os.path.dirname(HERE), 'lib'), ROOT, os.path.join(ROOT, 'bin')]
import books_read as br  # noqa: E402
import units as dmunits  # noqa: E402


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


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0
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
