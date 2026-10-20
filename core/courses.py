"""courses — the three axes a course of plan is read on (core 2.23, the operation `axes`): feasibility, efficiency and
necessity, each a score from 0 to 1 beside the evidence it rests on, weighed by a judge's weighing into one sum and a
mark — `optimum here, now`, `wasteful weight` — that orders what a person is shown and never decides.

Pure: bin/reckon.py gathers each member's facts from the garden and hands them here; nothing is read or written here.
A member's facts:

    {'id', 'needs': [{'id', 'blocking', 'met', 'meetable', 'impossible', 'in_force', 'amount': {count, unit} | None}],
     'needed_by': [{'bean', 'id', 'blocking', 'met', 'in_force'}], 'repairs': n, 'risks': n}

Every score is a Fraction until a weighing's weights, which are read (an eigenvector), multiply it.
"""
from fractions import Fraction

HALF = Fraction(1, 2)
CRITERIA = ('feasibility', 'efficiency', 'necessity')
OPTIMUM, WASTEFUL = 'optimum here, now', 'wasteful weight'


def _amount(q):
    """(Fraction, unit) of a quantity, or None."""
    if not isinstance(q, dict) or 'count' not in q:
        return None
    try:
        return Fraction(str(q['count'])), str(q.get('unit') or '1')
    except (ValueError, ZeroDivisionError):
        return None


def strength(n):
    return Fraction(1) if n.get('blocking', True) else HALF


def axes(members, weights=None):
    """[{id, feasibility, necessity, efficiency, yield, cost, amounts, evidence, sum, mark}] in the members' order."""
    rows = []
    for m in members:
        blocking = [n for n in m.get('needs') or [] if n.get('blocking', True) and n.get('in_force', True) is not False]
        if any(n.get('impossible') for n in blocking):
            feas = Fraction(0)
        elif blocking:
            feas = Fraction(sum(1 for n in blocking if n.get('met') or n.get('meetable')), len(blocking))
        else:
            feas = Fraction(1)
        need_now = sum((strength(n) for n in m.get('needed_by') or []
                        if n.get('in_force', True) is not False and not n.get('met')), Fraction(0))
        yields = sum((strength(n) for n in m.get('needed_by') or []), Fraction(0)) + Fraction(m.get('repairs') or 0)
        amounts = {}
        for n in m.get('needs') or []:
            if n.get('in_force', True) is False:
                continue
            a = _amount(n.get('amount'))
            if a:
                amounts[a[1]] = amounts.get(a[1], Fraction(0)) + a[0]
        rows.append({'id': m['id'], 'feasibility': feas, 'need_now': need_now, 'yield_raw': yields,
                     'amounts': amounts, 'risks': int(m.get('risks') or 0),
                     'evidence': {'blocking needs': len(blocking),
                                  'met or meetable': sum(1 for n in blocking if n.get('met') or n.get('meetable')),
                                  'impossible': sum(1 for n in blocking if n.get('impossible')),
                                  'needed by, now': [f"{n['bean']}#{n['id']}" for n in m.get('needed_by') or []
                                                     if n.get('in_force', True) is not False and not n.get('met')],
                                  'needed by': [f"{n['bean']}#{n['id']}" for n in m.get('needed_by') or []],
                                  'repairs': int(m.get('repairs') or 0), 'risks it makes possible': int(m.get('risks') or 0)}})
    most_need = max((r['need_now'] for r in rows), default=Fraction(0))
    most_yield = max((r['yield_raw'] for r in rows), default=Fraction(0))
    least = {}
    for r in rows:
        for u, a in r['amounts'].items():
            if a > 0 and (u not in least or a < least[u]):
                least[u] = a
    for r in rows:
        r['necessity'] = r['need_now'] / most_need if most_need else Fraction(0)
        r['yield'] = r['yield_raw'] / most_yield if most_yield else Fraction(0)
        ratios = [least[u] / a for u, a in r['amounts'].items() if a > 0]
        r['cost'] = (sum(ratios, Fraction(0)) / len(ratios) if ratios else Fraction(1)) / (1 + r['risks'])
        r['efficiency'] = r['yield'] * r['cost']
        r['costs'] = bool(r['amounts']) or r['risks'] > 0
        r['sum'] = None
        r['mark'] = None
    if weights:
        for r in rows:
            r['sum'] = sum(float(weights.get(c, 0)) * float(r[c]) for c in CRITERIA)
        able = [r for r in rows if r['feasibility'] == 1 and r['necessity'] > 0]
        best = max((r['sum'] for r in able), default=None)
        for r in rows:
            if r['necessity'] == 0 or (r['yield'] == 0 and r['costs']):
                r['mark'] = WASTEFUL
            elif best is not None and r in able and r['sum'] == best:
                r['mark'] = OPTIMUM
    return rows
