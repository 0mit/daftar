#!/usr/bin/env python3
"""view_core — the `view` asset in a garden of the core (v1 part 11): the page and the beings it draws, read from their
statements, and the law the asset reads, from core/law/.

ONE VIEW, BUILT HERE. The asset draws what it reads in the shape it has always drawn — a page's `view`, `views`,
`view_bindings` and `view_monitors`, a being's `genos`, its owner, its places, what it serves, what it runs — so this
module reads a bean of statements once and gives it in that shape, and nothing else in the asset reads statements its
own way. It never writes: the page is written as statements by `page_statements`, through bin/safe.py.

    the page            its own `draw`, holding the form `page` (today's `view`, its monitors folded in), names its
                        drawings in order; each drawing is a `draw` of what it draws, holding the form `drawing`
                        (an entry of today's `views`, the values that sit on it under `values`)
    a being             what bin/garden.py `terms` gives (its header, what `details` keeps, its places, its clauses,
                        its names) and, from its statements: `genos` (its kind), `nature`, `owned_by` (`own`),
                        `lives_in` (`be` as habitat), `part_of` (`part`), `instance_of` (`run`), `endpoints` (`serve`),
                        `knowledge` (`classify`, `use`), `reaches` (`need` through a protocol), `steps` (a walk's), and
                        each verb it says under the verb's own name, the facts a card shows
    the law             the lenses and archetypes (core/law/profiles.yaml), the units by the law's English names with
                        their factors, the protocols, the schemes and the signals, the form of a drawing's value

A unit is handed to the asset by the law's English name (`percent`, as the runtime formats it), a count as a number:
the core writes every value as text, and its units by their UCUM codes.
"""
import os
import re
import sys

NATURES = {'body': 'soma', 'sayable': 'lekton'}      # the core's natures, by today's words the drawings are keyed by
HEADER_FACTS = ('title', 'summary', 'tags')
READS = {'need.through': 'reaches', 'page.monitors': 'view_monitors'}   # an archetype's `reads`, as a being reads here
ANCHOR_KEYS = {'dns': 'fqdn', 'ieee-eui48': 'mac', 'mail': 'email', 'e164': 'phone', 'garden-id': 'garden_id',
               'sha-256': 'content_hash', 'openpgp': 'openpgp_fingerprint', 'ssh': 'ssh_key_fingerprint',
               'wireguard': 'wg_pubkey', 'garden': 'identifier'}   # the core's namespaces, by the anchor key a card names them by


def runs_core(root):
    """True where the garden's GARDEN.md pins the core (bin/check.py, the one reader of the pin)."""
    b = os.path.join(root, 'bin')
    if b not in sys.path:
        sys.path.insert(0, b)
    if not os.path.isfile(os.path.join(b, 'check.py')):
        return False
    import check
    return check.runs_core(check.pin(root))


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _number(v):
    if isinstance(v, str) and re.fullmatch(r'-?[0-9]+', v):
        return int(v)
    if isinstance(v, str) and re.fullmatch(r'-?[0-9]*\.[0-9]+', v):
        return float(v)
    return v


def typed(x, spec=None):
    """A form's value as today's reader held it: a count a number (`{type: count}`, a quantity's or a length's
    `count`), the rest as written."""
    dom = spec.get('in') if isinstance(spec, dict) else None
    if isinstance(x, dict):
        attrs = (dom.get('attrs') or dom.get('entries') or {}) if isinstance(dom, dict) else \
            (spec.get('attrs') or {}) if isinstance(spec, dict) and 'attrs' in spec else {}
        if isinstance(dom, dict) and isinstance(dom.get('map_of'), dict):
            return {k: typed(v, {'attrs': dom['map_of']}) for k, v in x.items()}
        return {k: (_number(v) if k == 'count' else typed(v, attrs.get(k))) for k, v in x.items()}
    if isinstance(x, list):
        return [typed(v, spec) for v in x]
    if isinstance(dom, dict) and dom.get('type') == 'count':
        return _number(x)
    return x


class Law:
    """The law the asset reads, in a garden of the core: what today's gate gave it (`registry`, `UNITS`, `TERMS`,
    `SCHEMAS`), read from core/law/."""

    def __init__(self, L, root):
        self.L, self.root = L, root
        from core import measures
        names = measures.unit_names(root)
        self.names = names
        self.UNITS = {}
        for code, row in L.units.items():
            f = row.get('factor')
            f = [int(f[0]), int(f[1])] if isinstance(f, list) and len(f) == 2 and all(str(x).isdigit() for x in f) else None
            self.UNITS[str(row.get('name') or code)] = {'unit': row.get('name') or code, 'quantity': row.get('quantity'),
                                                       'factor': f}
        d = (L.forms.get('drawing') or {}).get('attrs') or {}
        values = (((d.get('values') or {}).get('in') or {}).get('map_of')) or {}
        self.TERMS = {'view_bindings': {'schema': {'attrs': values}}}
        self.SCHEMAS = {}

    def registry(self, name):
        L, std = self.L, self.L.std
        if name in ('view_lenses', 'lenses'):
            return [dict(r, depth=_number(r.get('depth')), max={k: _number(v) for k, v in (r.get('max') or {}).items()})
                    for r in L.profile_tables.get('lenses') or []]
        if name in ('view_archetypes', 'archetypes'):       # what the facts propose a shape by, as this view names
            return [dict(r, reads=[READS.get(x, x) for x in _listed(r.get('reads'))]) if r.get('reads') else r
                    for r in L.profile_tables.get('archetypes') or []]
        if name in ('net_protocols', 'protocols'):
            return list(std.protocols.values())
        if name in std.tables:
            return std.tables[name]
        files = {r.get('registry'): r for r in std.tables.get('registry_files') or [] if isinstance(r, dict)}
        if name in files:
            return std._tsv(files[name].get('file'))
        return []


class Garden:
    """A garden of the core as the asset reads it: each bean once, in today's shape."""

    def __init__(self, root):
        self.root = os.path.abspath(root)
        for p in (self.root, os.path.join(self.root, 'bin')):
            if p not in sys.path:
                sys.path.insert(0, p)
        import garden as gm
        from core import check
        self.gm = gm
        self.G = gm.core_garden(self.root)
        self.L = check.garden_law(self.root)
        self.law = Law(self.L, self.root)
        self._today = {}

    def reload(self):
        """Read the garden again, after a write."""
        self.gm._CORE.pop(self.root, None)
        self.gm._CACHE.clear()
        self.G = self.gm.core_garden(self.root)
        self._today = {}

    def taken(self):
        return list(self.L.taken)

    def space(self, bid):
        b = self.G.beans.get(bid)
        return os.path.basename(os.path.dirname(b.path)) if b is not None and b.path else None

    def pages(self):
        from core import profiles
        return sorted(bid for bid, b in self.G.beans.items() if self.space(bid) == 'beans' and profiles.page_of(b))

    def today(self, bid, folder='beans'):
        """A bean (or a mapping) in the shape the asset reads; {} where the garden holds none by that id there."""
        b = self.G.beans.get(bid) if isinstance(bid, str) else None
        if b is None or self.space(bid) != folder:
            return {}
        if bid not in self._today:
            self._today[bid] = self._read(b)
        return self._today[bid]

    def _read(self, b):
        from core import frame, lines, profiles
        beans = set(self.G.beans)
        v = self.gm.terms(b, beans)
        kind = self.L.kinds.get(b.kind) or {}
        v['genos'] = b.kind
        if kind.get('nature'):
            v['nature'] = NATURES.get(kind['nature'], kind['nature'])
        details = b.header.get('details') if isinstance(b.header.get('details'), dict) else {}
        v.setdefault('details', details)         # a path of the core (`details.refs.boat.bean`) reads as a reading's does
        live = [(verb, r) for _i, verb, r in b.items if isinstance(r, dict) and 'held' not in r]
        facts = {}                               # each verb it says, under its own name, and narrowed by its `as`
        for verb, r in live:                     # (`be.habitat`): the facts a card shows, each what it says of it
            said = {k: x for k, x in r.items() if k not in ('id', 'placed') and not (k in ('by', 'of') and x in ('self', b.id))}
            facts.setdefault(verb, []).append(said)
            if isinstance(r.get('as'), str):
                facts.setdefault(f"{verb}.{r['as']}", []).append({k: x for k, x in said.items() if k != 'as'})
        for k, rows in facts.items():
            if k not in v:
                rows = [next(iter(x.values())) if len(x) == 1 else x for x in rows]
                v[k] = rows[0] if len(rows) == 1 else rows
        names = []                               # the names it is known by: today's anchors, each by its key
        for verb, r in live:
            if verb == 'name' and isinstance(r.get('as'), str) and isinstance(r.get('by'), str) \
                    and r.get('of') in (None, 'self', b.id):
                ns = r['by']
                key = ANCHOR_KEYS.get(ns) or (ns[7:] if ns.startswith('anchor-') else ns)
                names.append({'key': key, 'value': r['as'],
                              'establishing': (self.L.namespaces.get(ns) or {}).get('once') == 'true'})
        if names:
            v['identity'] = dict(v.get('identity') or {}, anchors=names)
        own = next((r for verb, r in live if verb == 'own' and r.get('of') in (None, 'self', b.id)), None)
        if own:
            if isinstance(own.get('by'), str) and own['by'] in beans:
                v['owned_by'] = {'owner': {'bean': own['by']}}
            elif isinstance(own.get('from'), str) and own['from'] in beans:
                v['owned_by'] = {'from': {'bean': own['from']}}
        for verb, r in live:
            if verb == 'be' and r.get('as') == 'habitat' and isinstance(r.get('at'), str) and r['at'] in beans:
                v.setdefault('lives_in', {'bean': r['at']})
            elif verb == 'part' and isinstance(r.get('of'), str) and r['of'] in beans:
                v.setdefault('part_of', {'bean': r['of']})
            elif verb == 'run' and isinstance(r.get('of'), str) and r['of'] in beans:
                v.setdefault('instance_of', {'bean': r['of']})
        kept = details.get('endpoints') if isinstance(details.get('endpoints'), dict) else {}
        eps = []
        for verb, r in live:
            if verb != 'serve':
                continue
            e = {'protocol': r.get('through')}
            for x in _listed(r.get('at')):
                try:
                    p = frame.read(x, self.L.systems, self.G.zone) if isinstance(x, str) else None
                except frame.Refused:
                    p = None
                if p is None:
                    continue
                text = x[len(p.system) + 1:] if x.startswith(p.system + ':') else x
                if p.system.endswith('-port'):
                    e['port'] = text
                else:
                    e['system'], e['at'] = p.system, text
            e.update(kept.get(r.get('id')) or {})
            eps.append(e)
        if eps:
            v['endpoints'] = eps
        know = []
        for verb, r in live:
            if verb == 'classify' and isinstance(r.get('as'), str) and r.get('of') in (None, 'self', b.id):
                know.append({'code': r['as'], 'rel': 'classified_as'})
            elif verb == 'use' and isinstance(r.get('of'), str) and ':' in r['of']:
                know.append({'code': r['of'], 'rel': 'uses'})
        if know:
            v['knowledge'] = know
        kept = details.get('reaches') if isinstance(details.get('reaches'), dict) else {}
        reach = {}
        for verb, r in live:
            if verb == 'need' and r.get('through') and isinstance(r.get('id'), str):
                to = next((x for x in _listed(r.get('of')) if isinstance(x, str)), None)
                e = dict(kept.get(r['id']) or {}, protocol=r['through'])
                if to:
                    e['to'] = {'bean': to} if to in beans else to
                reach[r['id'][8:] if r['id'].startswith('reaches-') else r['id']] = e
        if reach:
            v['reaches'] = reach
        if any(verb == 'step' for verb, _r in live):
            v['steps'] = lines.steps_of(b)
        act = next(((verb, r) for verb, r in live if verb in self.L.knowing), None)
        if act and 'provenance' not in v:        # how it is known: its first knowing act, who, and the day
            verb, r = act
            day = next((x for x in _listed(r.get('at')) if isinstance(x, str) and re.match(r'[0-9]{4}-', x)), None)
            v['provenance'] = dict({'src': verb, 'by': r.get('note') if isinstance(r.get('note'), str) else r.get('by')},
                                   **({'as_of': day[:10]} if day else {}))
        if profiles.page_of(b):
            v.update(self.page_terms(b))
        return v

    def page_terms(self, b):
        """The page's `view`, `views`, `view_bindings` and `view_monitors`, from its `draw` statements."""
        from core import measures, profiles
        names = self.law.names
        forms = self.L.forms
        pid, page = profiles.page_of(b)
        view = typed(dict(page['page']), {'attrs': (forms.get('page') or {}).get('attrs') or {}})
        mons = view.pop('monitors', None)
        if isinstance(view.get('fields'), list):
            view['fields'] = [{('genos' if k == 'kind' else 'term' if k == 'fact' else k): x for k, x in e.items()}
                              if isinstance(e, dict) else e for e in view['fields']]
        if 'note' in page:
            view['note'] = page['note']
        out = {'view': view}
        if mons:
            out['view_monitors'] = mons
        views, binds = {}, {}
        dspec = {'attrs': (forms.get('drawing') or {}).get('attrs') or {}}
        for did, r in profiles.drawings_of(b):
            d = measures.in_today_words(typed(dict(r['drawing']), dspec), names)
            target = next((x for x in _listed(r.get('of')) if isinstance(x, str)), None)
            space = self.space(target)
            entry = {'draws': {'mapping' if space == 'mappings' else 'bean': target}}
            for k, x in d.items():
                if k != 'values':
                    entry[k] = x
            if 'note' in r:
                entry['note'] = r['note']
            views[did] = entry
            for bk, e in (d.get('values') or {}).items():
                binds[bk] = dict({'view': did}, **e)
        out['views'] = views
        if binds:
            out['view_bindings'] = binds
        return out


# ------------------------------------------------------------------------------------------------ the page, written
def page_statements(view, views, bindings, monitors, L, space_of):
    """The page in statements, from its terms in today's shape: [(id, verb roles)] — a `draw` of each drawing, in the
    order `views` lists them, its values folded in, then the page's own `draw`. A unit is written by its UCUM code."""
    from core import translate
    def ucum(x):
        if isinstance(x, dict):
            return {k: (translate.ucum_of(v, L) or v if k == 'unit' and isinstance(v, str) else ucum(v))
                    for k, v in x.items()}
        if isinstance(x, list):
            return [ucum(v) for v in x]
        return str(x) if isinstance(x, (int, float)) and not isinstance(x, bool) else x
    out, order = [], []
    for key, v in views.items():
        ref = v.get('draws')
        target = (ref.get('mapping') or ref.get('bean')) if isinstance(ref, dict) else ref
        roles = {'id': key, 'by': 'self', 'of': [target]}
        if isinstance(v.get('note'), str):
            roles['note'] = v['note']
        form = {k: ucum(x) for k, x in v.items() if k not in ('draws', 'note')}
        vals = {bk: ucum({k: x for k, x in e.items() if k != 'view'}) for bk, e in bindings.items()
                if isinstance(e, dict) and e.get('view') == key}
        if vals:
            form['values'] = vals
        roles['drawing'] = form
        out.append((key, roles))
        order.append(key)
    page = {k: ucum(x) for k, x in view.items() if k != 'note'}
    if isinstance(page.get('fields'), list):
        page['fields'] = [{('kind' if k == 'genos' else 'fact' if k == 'term' else k): x for k, x in e.items()}
                          if isinstance(e, dict) else e for e in page['fields']]
    if monitors:
        page['monitors'] = ucum(monitors)
    roles = {'id': 'page', 'by': 'self', 'of': order, 'page': page}
    if isinstance(view.get('note'), str):
        roles['note'] = view['note']
    out.append(('page', roles))
    return out
