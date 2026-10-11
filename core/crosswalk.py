"""crosswalk — a foreign system's records read from a garden's statements, as core/law/crosswalks.yaml says (P5.3).

    from core import crosswalk
    crosswalk.records(root, 'odoo', '17.0', 'hr.department')   # [{id, name, parent_id: [id, name] | False, …}]

THE ONE READER of the crosswalks: daftard's answers to Odoo's client and any other reader take records from here, so
two readers can never disagree about what a record is. Nothing is written and nothing is kept: a record is read from
the beans each time it is asked for.

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


def number(model, bean_id):
    return int.from_bytes(hashlib.sha256(f'{model}:{bean_id}'.encode('utf-8')).digest()[:4], 'big') & 0x7fffffff


class Reader:
    """The crosswalks of one system and series over one garden, read once."""

    def __init__(self, root, system, series, law=None, garden=None, unseal=None):
        self.law = law or garden_law(root)
        self.G = garden or engine.Garden.read(root)
        self.unseal = unseal
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
        path = spec.get('from', 'title')
        target = spec.get('model')
        held = spec.get('held') in (True, 'true')
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
        if not isinstance(hit, str) or hit not in self.selected(target):
            return False
        return [number(target, hit), self.display(target, hit)]

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
