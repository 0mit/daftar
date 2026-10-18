#!/usr/bin/env python3
"""export — statements written out as another system's records, through a crosswalk of the law, where the flow law lets them go.

    python3 bin/export.py <crosswalk> <being> [<being> ...]          # each being's records, in the crosswalk's format
    python3 bin/export.py <crosswalk> <being> --ids <id>[,<id> ...]  # only the statements of those ids
    python3 bin/export.py <crosswalk> <being> --from store:<name>    # its statements in git and in that store, as one
    python3 bin/export.py <crosswalk> <being> --format csv --to <file>
    python3 bin/export.py daftar <being> --from store:<name> --by <being> [--write]   # a store's rows into its bean
    python3 bin/export.py proposal <bean> ... --to <garden> --under <agreement>       # to another garden

(`python` on Windows.) The statements of a being are the union of its bean and every store named, as one set (MODEL.md,
The store). Each is read back through the crosswalk (core/crosswalk.py `Carry.back`), written in the format, and what
the records have no place for is listed, never dropped in silence.

WHERE IT MAY GO is the flow law's, asked before anything is written (core/law/flows.yaml): a file written on this host,
or what is printed, is shown to whoever runs it (`composed-here`); a garden's own material never goes to a public
repository (`kept-private`); another garden is given a proposal (bin/propose.py), never a file. A sealed statement is
never read: it stays where it is held.

DAFTAR'S OWN FORMS need no crossing, and their own tools keep them: `daftar` (a store's rows into a bean, known there
by a `derive`) is bin/store.py's export; `proposal` is bin/propose.py's make. This door hands each to its tool.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, ROOT)
import parse as dmparse  # noqa: E402,F401 — its import sets UTF-8 on stdout and stderr

from core import formats  # noqa: E402
from core.crosswalk import Carry, Refused  # noqa: E402


def _plain(x):
    import store as dmstore
    return dmstore._plainid(x)


class Export:
    """One export: a crosswalk, the stores whose rows join the beans, and the layer it goes to."""

    def __init__(self, root=ROOT, crosswalk=None, *, stores=(), to='request', law=None):
        from core.check import garden_law
        self.root = root
        self.law = law or garden_law(root, root if os.path.isfile(os.path.join(root, 'core', 'law', 'core.yaml')) else None)
        self.stores = list(stores)
        ok, grant, rows = self.law.decide('store' if self.stores else 'estate', to, 'show' if to == 'request' else
                                          'publish' if to == 'public' else 'make', None)
        if not ok:
            raise Refused(f"the flow law does not let a garden's statements go to {to} ({grant}"
                          f"{': ' + ', '.join(rows) if rows else ''}): nothing is written")
        self._garden = None
        try:
            import knowledge as dmknowledge
            schemes = list(dmknowledge.Knowledge(root).schemes.values())
        except Exception:                      # noqa: BLE001 — a garden with no knowledge writes no coding
            schemes = []
        self.carry = Carry(self.law, crosswalk, names=None, named_as=self.named_as, schemes=schemes)

    @property
    def garden(self):
        if self._garden is None:
            from core import engine
            self._garden = engine.Garden.read(self.root)
        return self._garden

    def statements(self, being):
        """[(verb, roles)] of the being, its bean's and each store's, one set; a sealed statement never."""
        import json
        out, seen = [], set()
        b = self.garden.beans.get(being)
        for _i, v, r in (b.items if b is not None else []):
            if 'held' in r:
                continue
            key = json.dumps({v: {k: x for k, x in r.items() if k != 'id'}}, sort_keys=True, default=str)
            if key not in seen:
                seen.add(key)
                out.append((v, {k: _plain(x) for k, x in r.items()}))
        for S in self.stores:
            for v, r, _acts in S.get(being):
                r = S.denormalize(being, v, r)
                key = json.dumps({v: {k: x for k, x in r.items() if k != 'id'}}, sort_keys=True, default=str)
                if key not in seen:
                    seen.add(key)
                    out.append((v, {k: _plain(x) for k, x in r.items()}))
        return out

    def named_as(self, being, namespace):
        """The name `namespace` gives the being, in its bean or a store: what a field read through `named` writes."""
        b = self.garden.beans.get(being)
        for _i, v, r in (b.items if b is not None else []):
            if v == 'name' and r.get('by') == namespace and 'held' not in r:
                return r.get('as')
        for S in self.stores:
            for v, r, _a in S.get(being):
                if v == 'name' and r.get('by') == namespace:
                    return r.get('as')
        return None

    def records(self, beings, ids=None):
        """([record], [what was not carried]) of the beings, in order."""
        recs, listed = [], []
        for being in beings:
            sts = self.statements(being)
            if ids:
                sts = [(v, r) for v, r in sts if r.get('id') in ids]
            for rec, missed in self.carry.back(being, sts):
                if rec:
                    recs.append(rec)
                listed += [f"{being}: {m}" for m in missed]
        return recs, listed

    def text(self, beings, fmt=None, ids=None):
        fmt = fmt or (self.carry.row['format'][0] if isinstance(self.carry.row['format'], list) else self.carry.row['format'])
        recs, listed = self.records(beings, ids)
        fields = [f for f, sp in self.carry.fields.items() if isinstance(sp, dict) and 'drop' not in sp]
        return formats.write(fmt, recs, fields=fields), listed


def _arg(argv, flag, default=None):
    vals = [argv[i + 1] for i, a in enumerate(argv[:-1]) if a == flag]
    return vals[-1] if vals else default


def main(argv):
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__.strip())
        return 0 if argv else 2
    if argv[0] == 'proposal':                                 # to another garden: a proposal, propose.py's
        import propose as dmpropose
        return dmpropose.main(['make'] + argv[1:])
    if argv[0] == 'daftar':                                   # a store's rows into the being's bean: store.py's
        import store as dmstore
        frm = _arg(argv, '--from', '')
        if not frm.startswith('store:'):
            print("export: a garden's own statements come from a store: --from store:<name>", file=sys.stderr)
            return 2
        rest = [a for i, a in enumerate(argv[1:], 1) if argv[i - 1] != '--from' and a != '--from']
        return dmstore.main(['export', frm.split(':', 1)[1]] + rest)
    flags = {'--from', '--format', '--to', '--ids', '--path'}
    pos, i = [], 0
    while i < len(argv):
        if argv[i] in flags:
            i += 2
            continue
        pos.append(argv[i])
        i += 1
    if len(pos) < 2:
        print("export: <crosswalk> <being> ...", file=sys.stderr)
        return 2
    try:
        stores = []
        if _arg(argv, '--from') or _arg(argv, '--path'):
            import store as dmstore
            frm = _arg(argv, '--from') or ''
            stores.append(dmstore.open_store(frm.split(':', 1)[1] if frm.startswith('store:') else None,
                                             path=_arg(argv, '--path'), root=ROOT, create=False))
        ids = [x for x in (_arg(argv, '--ids') or '').split(',') if x]
        E = Export(ROOT, pos[0], stores=stores)
        out, listed = E.text(pos[1:], _arg(argv, '--format'), ids or None)
    except (Refused, formats.Refused) as e:
        print(f"export: refused — {e}", file=sys.stderr)
        return 1
    dest = _arg(argv, '--to')
    if dest:
        with open(dest, 'wb' if isinstance(out, bytes) else 'w', **({} if isinstance(out, bytes) else
                                                                      {'encoding': 'utf-8', 'newline': ''})) as fh:
            fh.write(out)
        print(f"export: wrote {dest}")
    else:
        sys.stdout.write(out if isinstance(out, str) else out.decode('utf-8', 'replace'))
    for m in listed:
        print(f"not carried: {m}", file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
