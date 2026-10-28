"""mechanics — a being fitting a concept's pattern (core 4.2): the matcher `fits` calls for `{concept: <code>}`, the
canonical signature the law's self-check holds one to a row, and a drawing of the bodies a garden joins.

THE BASIC SET (Reuleaux 1876, on mereotopology). A BODY is one piece of matter, its compliance one of
the core's `compliances`; a FEATURE is a dependent part of one body, a position of its own frame (`hub#bore`, the system
`local-frame`); `part` says what a whole is made of; `join` says two bodies touch at a feature of each, in one of the
core's `pairs`, kept by one or more of its `closures`. Six relations are read from these, never stored:
  - a LINK: bodies made one by fastenings — a fixed pair between rigid bodies, a helical pair closed by friction — and
    the fiat parts of one body (Reuleaux's link-formation);
  - COUPLED: one link, or both fixed to one elastic body;
  - SIBLING and OUTSIDE: parts of one whole, or not;
  - a device's joints LIFTED to its parts: a pair is read between two bodies or the parts beneath them, never inside one;
  - the LEAST WHOLE: a role is read of the least whole that bears it, never of a whole whose part bears it.

A CONCEPT is a row of a scheme of the form `concept` (core/law/profiles.yaml): its pattern is a root and other nodes,
each a constraint, and edges among them that must hold (`edges`) or must not (`not`). A form is said (`classify`) and a
role read; a body said to be of a concept fits it as said. A pattern with a `not` is read only of a body drawn whole:
what is not drawn is not known to be absent, and a fact the drawing does not hold fits no constraint on it — the matcher
never guesses. The matcher is a bounded subgraph match: each node of a pattern is a distinct body.

A DRAWING is what the matcher reads: bodies with what is known of each, the parts of each whole, and the joints. One is
drawn from a garden (`drawing`) of what its statements say — a body's kind, its parts, its joints, the concepts it is
said to be, and what `specify` says of it (core 4.12): its compliance, its shape, its section and its designation, each
feature's kind, side, profile and count, and that a whole is drawn whole; where no `specify` says one of the first
three, a form said of it says what its pattern's root holds. A fact no word of the law says yet (a body's material,
function or use) is not held. A test or a tool may give a drawing whole.
"""
import itertools
import json

LIMITS = ('shape', 'section', 'material', 'use', 'function', 'designation')
SAID_LIMITS = ('shape', 'section', 'designation')                  # the limits `specify` says (core 4.12)
FROM_FORM = ('compliance', 'shape', 'section')                     # what a said form's root says of its body
NODE_KEYS = ('compliance', 'compliance_not', 'device', 'not_fiat', 'features', 'fits') + LIMITS
FEATURE_KEYS = ('kind', 'side', 'profile', 'count')
READ = ('part', 'one-link', 'coupled', 'sibling', 'outside')        # the relations an edge may name beside a pair
EDGE_KEYS = ('x', 'y', 'pair', 'link', 'rel', 'closure', 'closure_any', 'a', 'b')
DEPTH = 6                                                          # how deep one concept's `fits` names another


def listed(x):
    return [] if x is None else list(x) if isinstance(x, (list, tuple)) else [x]


def _true(v):
    return str(v).lower() == 'true'


# ------------------------------------------------------------------------------------------------ the drawing
class Node:
    """One body, or one device, as a drawing holds it. Each fact is None where the drawing does not hold it."""

    def __init__(self, nid, device=None, compliance=None, features=None, limits=None, said=(), whole=False,
                 fiat_of=None):
        self.id, self.device, self.compliance = nid, device, compliance
        self.features = features                    # {name: {kind, side, profile, count}}, or None: not drawn
        self.limits = dict(limits or {})            # {limit: value} the drawing holds
        self.said = set(said)                       # the codes it is said to be (`classify`), each `<scheme>:<code>`
        self.whole = whole                          # drawn whole: what is not drawn of it is known absent
        self.fiat_of = fiat_of                      # the body it is a fiat part of
        self.parts, self.fiat = [], []


class Drawing:
    """Bodies, the parts of each whole and the joints among them; the links read from them once."""

    def __init__(self, nodes, joints):
        self.nodes = {n.id: n for n in nodes}
        self.joints = []
        for j in joints:
            if j['x'] in self.nodes and j['y'] in self.nodes:
                self.joints.append(dict(j, closures=set(listed(j.get('closures')))))
        self.parent = {}
        for n in self.nodes.values():
            for p in n.parts + n.fiat:
                self.parent.setdefault(p, n.id)
        self._links = None
        self._members = {}
        self.memo = {}                              # what each matcher read of it: {id(matcher): {(node, code): fit}}

    def comp(self, n):
        a = self.nodes[n]
        if a.fiat_of and a.fiat_of in self.nodes:
            return self.nodes[a.fiat_of].compliance
        return a.compliance

    def members(self, n):
        """n and every part and fiat part beneath it."""
        if n not in self._members:
            out, todo = {n}, [n]
            while todo:
                m = todo.pop()
                for c in self.nodes[m].parts + self.nodes[m].fiat:
                    if c in self.nodes and c not in out:
                        out.add(c)
                        todo.append(c)
            self._members[n] = out
        return self._members[n]

    @property
    def links(self):
        """Reuleaux's links: bodies made one by fastenings and the fiat parts of one body, each body's link by its root."""
        if self._links is None:
            root = {n: n for n in self.nodes}

            def find(n):
                while root[n] != n:
                    root[n] = root[root[n]]
                    n = root[n]
                return n

            for n, a in self.nodes.items():
                if a.fiat_of in self.nodes:
                    root[find(n)] = find(a.fiat_of)
            for j in self.joints:
                rigid = self.comp(j['x']) == 'rigid' and self.comp(j['y']) == 'rigid'
                if rigid and (j['pair'] == 'fixed' or (j['pair'] == 'helical' and 'friction' in j['closures'])):
                    root[find(j['x'])] = find(j['y'])
            self._links = {n: find(n) for n, a in self.nodes.items() if a.device is not True}
        return self._links

    def link(self, n):
        if n not in self.links:
            return self.members(n)
        return {m for m, r in self.links.items() if r == self.links[n]}

    def one_link(self, a, b):
        return a in self.links and b in self.links and self.links[a] == self.links[b]

    def coupled(self, a, b):
        if self.one_link(a, b):
            return True

        def fixed_to(n):
            return {j['y'] if j['x'] == n else j['x'] for j in self.joints if j['pair'] == 'fixed' and n in (j['x'], j['y'])}

        return any(self.comp(c) == 'elastic' for c in fixed_to(a) & fixed_to(b))

    def outside(self, a, b):
        return self.parent.get(a) is None or self.parent.get(a) != self.parent.get(b)

    def sibling(self, a, b):
        return self.parent.get(a) is not None and self.parent.get(a) == self.parent.get(b)

    def features_of(self, n):
        return [f for m in self.members(n) for f in (self.nodes[m].features or {}).values()]


def feature_fits(want, have):
    """Whether a feature `have` holds the constraint `want`: each of kind, side, profile one of its values, count its
    count. A feature not drawn, or a constraint on what it does not hold, fits nothing."""
    if not want:
        return True
    if have is None:
        return False
    for k, v in want.items():
        got = have.get(k)
        if got is None:
            return False
        if k == 'count':
            if str(got) != str(v):
                return False
        elif str(got) not in [str(x) for x in listed(v)]:
            return False
    return True


# ------------------------------------------------------------------------------------------------ the matcher
class Matcher:
    """Every concept of the schemes of the form `concept`, by its code `<scheme>:<code>`; `fits` of a node of a drawing."""

    def __init__(self, concepts, checked=None):
        self.c = dict(concepts)
        self.checked = checked                      # checked(check, value): a designation held to its check, or None

    def designated(self, value, check):
        """Whether a body's designation holds to the check a pattern names; never, where no check can be applied."""
        if self.checked is None or not isinstance(value, str):
            return False
        try:
            return bool(self.checked(str(check), value))
        except Exception:                           # noqa: BLE001 — a check that cannot be applied fits nothing
            return False

    def code(self, scheme_of, name):
        """A pattern's `fits` names a code of its own scheme, or one written with its scheme."""
        return name if ':' in str(name) else f"{scheme_of}:{name}"

    def fits(self, d, n, code, depth=0):
        """'said' (it is said to be of the concept), 'read' (its pattern holds of it), or False."""
        memo = d.memo.setdefault(id(self), {})
        key = (n, code)
        if key in memo:
            return memo[key]
        memo[key] = False                           # a cycle fits nothing
        a, c = d.nodes[n], self.c.get(code)
        if c is None:
            ok = False
        elif code in a.said:
            ok = 'said'
        elif not a.whole and listed(c['pattern'].get('not')):
            ok = False                              # never guessed: an absence is read only of a body drawn whole
        elif not self.match(d, n, code, depth):
            ok = False
        elif c.get('level') == 'role' and any(self.fits(d, m, code, depth + 1) == 'read' for m in d.members(n) - {n}):
            ok = False                              # a role is read of the least whole that bears it
        else:
            ok = 'read'
        memo[key] = ok
        return ok

    def node_ok(self, d, n, want, scheme, depth):
        a = d.nodes[n]
        for k, v in (want or {}).items():
            if k == 'compliance':
                if d.comp(n) is None or d.comp(n) != v:
                    return False
            elif k == 'compliance_not':
                if d.comp(n) is None and a.device is not True or d.comp(n) in listed(v):
                    return False
            elif k == 'device':
                if a.device is None or a.device != _true(v):
                    return False
            elif k == 'not_fiat':
                if a.fiat_of:
                    return False
            elif k == 'features':
                have = d.features_of(n) if a.device else list((a.features or {}).values())
                if not all(any(feature_fits(w, h) for h in have) for w in listed(v)):
                    return False
            elif k == 'fits':
                if depth > DEPTH or not self.fits(d, n, self.code(scheme, v), depth + 1):
                    return False
            elif k == 'designation':
                if not self.designated(a.limits.get(k), v):
                    return False                    # a designation fits the check its pattern names (core 4.12)
            elif a.limits.get(k) is None or str(a.limits.get(k)) != str(v):
                return False                        # a limit: shape, section, material, use, function
        return True

    def edge_ok(self, d, x, y, e):
        if e.get('rel') == 'part':
            return y in d.nodes[x].parts or y in d.nodes[x].fiat
        if e.get('rel') == 'one-link':
            return d.one_link(x, y)
        if e.get('rel') == 'coupled':
            return d.coupled(x, y)
        if e.get('rel') == 'outside':
            return d.outside(x, y)
        if e.get('rel') == 'sibling':
            return d.sibling(x, y)
        if e.get('link') is not None:
            pairs, sx, sy = set(listed(e['link'])), d.link(x), d.link(y)
        else:
            pairs, sx, sy = set(listed(e.get('pair'))), d.members(x), d.members(y)
        for j in d.joints:
            for (a, af, b, bf) in ((j['x'], j.get('xf'), j['y'], j.get('yf')), (j['y'], j.get('yf'), j['x'], j.get('xf'))):
                if a in sx and b in sy and a not in sy and b not in sx and j['pair'] in pairs:
                    if e.get('closure') and not set(listed(e['closure'])) <= j['closures']:
                        continue
                    if e.get('closure_any') and not set(listed(e['closure_any'])) & j['closures']:
                        continue
                    fa = (d.nodes[a].features or {}).get(af) if af else None
                    fb = (d.nodes[b].features or {}).get(bf) if bf else None
                    if feature_fits(e.get('a'), fa) and feature_fits(e.get('b'), fb):
                        return True
        return False

    def match(self, d, n, code, depth):
        c = self.c[code]
        scheme = code.split(':', 1)[0]
        p = c['pattern']
        if not self.node_ok(d, n, p.get('root'), scheme, depth):
            return False
        nodes = p.get('nodes') or {}
        edges, nots = listed(p.get('edges')), listed(p.get('not'))
        positive = [m for m in nodes if any(m in (e.get('x'), e.get('y')) for e in edges)]
        negonly = [m for m in nodes if m not in positive]
        others = [m for m in d.nodes if m != n]

        def holds(bind, e):
            return self.edge_ok(d, bind[e['x']], bind[e['y']], e)

        def search(i, bind):
            if i == len(positive):
                if not all(holds(bind, e) for e in edges):
                    return False
                for e in nots:                      # each not-edge: no body of its constraints makes it hold
                    free = [v for v in (e.get('x'), e.get('y')) if v in negonly]
                    if not free:
                        if holds(bind, e):
                            return False
                        continue
                    v = free[0]
                    for m in others:
                        if m in bind.values() or any(b in d.members(m) or m in d.members(b) for b in bind.values()):
                            continue                # a whole of a bound body, or its part, is the same contact again
                        if self.node_ok(d, m, nodes[v], scheme, depth) and holds({**bind, v: m}, e):
                            return False
                return True
            v = positive[i]
            for m in others:
                if m in bind.values() or not self.node_ok(d, m, nodes[v], scheme, depth):
                    continue
                bind[v] = m
                ready = [e for e in edges if e.get('x') in bind and e.get('y') in bind]
                if all(holds(bind, e) for e in ready) and search(i + 1, bind):
                    return True
                del bind[v]
            return False

        return search(0, {'root': n})

    def contradicts(self, d, n, code, depth=0):
        """Why the node is KNOWN not to fit the concept's root, by what the drawing holds of it — its kind's device or
        body, a compliance a device has none of, a fiat part where the root is none, a limit it holds otherwise, the
        root of a concept the root fits — else ''. Nothing not drawn is a contradiction: an edge never is."""
        c = self.c.get(code)
        if c is None:
            return ''
        a, scheme = d.nodes[n], code.split(':', 1)[0]
        for k, v in (c['pattern'].get('root') or {}).items():
            if k == 'device' and a.device is not None and a.device != _true(v):
                return (f"a {code} is {'a device, bodies joined' if _true(v) else 'one body'}, and this is "
                        f"{'a device' if a.device else 'one body'}")
            if k in ('compliance', 'compliance_not') and a.device is True:
                return f"a {code} is a body of a compliance, and a device is bodies joined, with no compliance of its own"
            if k == 'compliance' and d.comp(n) is not None and d.comp(n) != v:
                return f"a {code} is {v}, and this is {d.comp(n)}"
            if k == 'compliance_not' and d.comp(n) in listed(v):
                return f"a {code} is not {d.comp(n)}"
            if k == 'not_fiat' and a.fiat_of:
                return f"a {code} is a body of its own, and this is a fiat part of {a.fiat_of}"
            if k == 'designation' and a.limits.get(k) is not None and self.checked is not None \
                    and not self.designated(a.limits[k], v):
                return f"a {code}'s designation is written as the check {v} reads one, and this one's is {a.limits[k]}"
            if k in LIMITS and k != 'designation' and a.limits.get(k) is not None and str(a.limits[k]) != str(v):
                return f"a {code}'s {k} is {v}, and this one's is {a.limits[k]}"
            if k == 'fits' and depth < DEPTH:
                why = self.contradicts(d, n, self.code(scheme, v), depth + 1)
                if why:
                    return why
        return ''


# ------------------------------------------------------------------------------------------------ the signature
def _canon_value(v):
    return json.dumps(v, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def signature(pattern, limits=True):
    """The pattern in canonical form: the least string over every renaming of its nodes, so two patterns that differ
    only by their nodes' names are one; with `limits` false, its topology alone, its limits taken out."""
    def strip(d):
        d = dict(d or {})
        if not limits:
            for k in LIMITS:
                d.pop(k, None)
        return _canon_value(d)

    def edge(e, ren):
        rest = {k: v for k, v in e.items() if k not in ('x', 'y')}
        if not limits:
            rest = {k: v for k, v in rest.items() if k not in LIMITS}
        return f"{ren.get(e.get('x'), e.get('x'))}-{ren.get(e.get('y'), e.get('y'))}:{_canon_value(rest)}"

    nodes = pattern.get('nodes') or {}
    names = list(nodes)
    best = None
    for perm in itertools.permutations(range(len(names))):
        ren = {'root': 'R', **{names[i]: f"n{perm[i]}" for i in range(len(names))}}
        parts = [f"R={strip(pattern.get('root'))}"]
        parts += sorted(f"{ren[k]}={strip(v)}" for k, v in nodes.items())
        parts += sorted(edge(e, ren) for e in listed(pattern.get('edges')))
        parts += sorted('!' + edge(e, ren) for e in listed(pattern.get('not')))
        s = '|'.join(parts)
        if best is None or s < best:
            best = s
    return best


# ------------------------------------------------------------------------------------------------ the pattern's form
def pattern_problems(row, scheme, codes, tables):
    """[message]: a concept row's pattern held to its form — a root, nodes each a constraint of NODE_KEYS, edges each
    between two of its nodes (or the root) by one pair of the core's `pairs`, a link by pairs, or a relation read
    (READ), with closures of the core's `closures`; a compliance of `compliances`; a `fits` naming a concept of the law;
    a shape of `outlines`, a section of `sections`, a designation a check that reads one, a feature's kind of
    `features`, its side of `sides` and its profile of `sections`, each only of a kind that takes it (core 4.12, where
    `tables` holds them); every node reached from the root through the edges that must hold, or named only by an edge
    that must not."""
    out = []
    p = row.get('pattern')
    if not isinstance(p, dict):
        return ["pattern: a concept holds its pattern, `{ root, nodes, edges, not }`"]
    for k in sorted(set(p) - {'root', 'nodes', 'edges', 'not'}):
        out.append(f"pattern: `{k}` is no part of a pattern: root, nodes, edges, not")
    nodes = p.get('nodes') or {}
    if not isinstance(nodes, dict):
        return out + ["pattern.nodes: a map of each node's name to its constraint"]
    if 'root' in nodes:
        out.append("pattern.nodes: `root` is the pattern's own node, never one of its other nodes")

    def feature(where, f):
        if not isinstance(f, dict):
            return
        kinds = tables.get('features')
        if kinds is None:
            return
        named = listed(f.get('kind'))
        for x in named:
            if str(x) not in kinds:
                out.append(f"{where}: a feature of kind {x!r}, no row of the core's `features`")
        for k, table in (('side', 'sides'), ('profile', 'sections')):
            if f.get(k) is None:
                continue
            for x in listed(f[k]):
                if str(x) not in (tables.get(table) or ()):
                    out.append(f"{where}: {k} {x!r} is no row of the core's `{table}`")
            bare = [str(x) for x in named if str(x) in kinds and str((kinds[str(x)] or {}).get(k)) != 'true']
            if bare:
                out.append(f"{where}: a {k} of a feature of kind {', '.join(bare)}, which takes none")

    def node(where, want):
        if not isinstance(want, dict):
            out.append(f"{where}: a constraint is a map of {', '.join(NODE_KEYS)}")
            return
        for k, v in want.items():
            if k not in NODE_KEYS:
                out.append(f"{where}: `{k}` is no constraint of a node: {', '.join(NODE_KEYS)}")
            elif k == 'compliance' and v not in tables['compliances']:
                out.append(f"{where}: compliance {v!r} is no row of the core's `compliances`")
            elif k == 'compliance_not' and not set(listed(v)) <= set(tables['compliances']):
                out.append(f"{where}: compliance_not names a row the core's `compliances` has not")
            elif k in ('device', 'not_fiat') and str(v) not in ('true', 'false'):
                out.append(f"{where}: {k} is `true` or `false`")
            elif k == 'fits' and (f"{scheme}:{v}" if ':' not in str(v) else str(v)) not in codes:
                out.append(f"{where}: fits {v!r}, which is no concept of the law")
            elif k == 'features':
                for f in listed(v):
                    bad = sorted(set(f) - set(FEATURE_KEYS)) if isinstance(f, dict) else ['(not a map)']
                    if bad:
                        out.append(f"{where}: a feature is held by {', '.join(FEATURE_KEYS)}, not {', '.join(bad)}")
                    feature(where, f)
            elif k == 'shape' and 'outlines' in tables and str(v) not in tables['outlines']:
                out.append(f"{where}: shape {v!r} is no row of the core's `outlines`")
            elif k == 'section' and 'sections' in tables and str(v) not in tables['sections']:
                out.append(f"{where}: section {v!r} is no row of the core's `sections`")
            elif k == 'designation' and 'designations' in tables and str(v) not in tables['designations']:
                out.append(f"{where}: designation {v!r} is no check of core/law/checks.yaml that reads a designation")

    node('pattern.root', p.get('root') or {})
    for name, want in nodes.items():
        node(f"pattern.nodes.{name}", want)
    known = {'root'} | set(nodes)
    for part in ('edges', 'not'):
        for i, e in enumerate(listed(p.get(part))):
            where = f"pattern.{part}[{i}]"
            if not isinstance(e, dict):
                out.append(f"{where}: an edge is a map of {', '.join(EDGE_KEYS)}")
                continue
            for k in sorted(set(e) - set(EDGE_KEYS)):
                out.append(f"{where}: `{k}` is no key of an edge: {', '.join(EDGE_KEYS)}")
            for end in ('x', 'y'):
                if e.get(end) not in known:
                    out.append(f"{where}: {end} {e.get(end)!r} is no node of the pattern")
            if e.get('x') == e.get('y'):
                out.append(f"{where}: an edge joins two nodes, each a distinct body")
            how = [k for k in ('pair', 'link', 'rel') if e.get(k) is not None]
            if len(how) != 1:
                out.append(f"{where}: an edge is a joint of a pair (`pair`), between links (`link`), or a relation "
                           f"read (`rel`): one of the three")
            for k in ('pair', 'link'):
                bad = [x for x in listed(e.get(k)) if x not in tables['pairs']]
                if bad:
                    out.append(f"{where}: {k} {', '.join(map(str, bad))}: no row of the core's `pairs`")
            if e.get('rel') is not None and e['rel'] not in READ:
                out.append(f"{where}: rel {e['rel']!r} is none of the relations read: {', '.join(READ)}")
            for k in ('closure', 'closure_any'):
                bad = [x for x in listed(e.get(k)) if x not in tables['closures']]
                if bad:
                    out.append(f"{where}: {k} {', '.join(map(str, bad))}: no row of the core's `closures`")
            if e.get('rel') is not None and any(e.get(k) for k in ('closure', 'closure_any', 'a', 'b')):
                out.append(f"{where}: a relation read holds no closure and no feature: they are a joint's")
            for k in ('a', 'b'):
                f = e.get(k)
                if f is not None and (not isinstance(f, dict) or set(f) - set(FEATURE_KEYS)):
                    out.append(f"{where}: {k} is a feature's constraint, of {', '.join(FEATURE_KEYS)}")
                elif f is not None:
                    feature(f"{where}.{k}", f)
    reached, todo = {'root'}, ['root']
    edges = [e for e in listed(p.get('edges')) if isinstance(e, dict)]
    while todo:
        m = todo.pop()
        for e in edges:
            for a, b in ((e.get('x'), e.get('y')), (e.get('y'), e.get('x'))):
                if a == m and b in known and b not in reached:
                    reached.add(b)
                    todo.append(b)
    nots = [e for e in listed(p.get('not')) if isinstance(e, dict)]
    for name in nodes:
        if name not in reached and not any(name in (e.get('x'), e.get('y')) for e in nots):
            out.append(f"pattern.nodes.{name}: no edge reaches it from the root")
    for i, e in enumerate(nots):
        if len({e.get('x'), e.get('y')} - reached) > 1:
            out.append(f"pattern.not[{i}]: an edge that must not hold has one end the root reaches")
    return out


# ------------------------------------------------------------------------------------------------ a garden's drawing
def drawing(beans, kind_of, said_of, concept_codes):
    """The drawing a garden's statements make. `beans`: [(bean id, kind, [(verb, roles)])]; `kind_of(kind)`: (nature,
    organisation) of a kind; `said_of`: the code of a `classify`'s `as` where it is a concept's, else None;
    `concept_codes`: the law's concepts, by code (a map of each to its row, or the codes alone).

    A node is each bean of a body's kind, and each `{ someone: <kind> }` a joint names; a device is a being whose kind
    stands at device on organisation; a part of a component is a fiat part of it (a component holds no made part); a
    feature is each `<body>#<feature>` a joint names at its body, its kind, side, profile and count as `specify` says
    them (core 4.12); what is said of a body is each concept code it is classified by. A body's compliance, shape,
    section and designation are what its own `specify` says, and where it says none of the first three, what the root
    of a form said of it holds; a whole is drawn whole where its `specify` says `whole: "true"`."""
    nodes, joints, parts, said, spec, featured = {}, [], [], {}, {}, {}

    def add(nid, kind):
        if nid in nodes:
            return
        nature, org = kind_of(kind)
        if nature != 'body':
            return
        nodes[nid] = Node(nid, device=(org == 'device'))

    def being(x, bid, at):
        if x == 'self':
            return bid
        if isinstance(x, str):
            return x
        if isinstance(x, dict) and isinstance(x.get('someone'), str):
            nid = f"{{someone: {x['someone']}}}@{at}"
            add(nid, x['someone'])
            return nid
        return None

    for bid, kind, items in beans:
        add(bid, kind)
    for bid, kind, items in beans:
        for i, (verb, r) in enumerate(items):
            if verb == 'part':
                parts.append((being(r.get('by'), bid, f"{bid}[{i}].by"), being(r.get('of'), bid, f"{bid}[{i}].of")))
            elif verb == 'join':
                x, y = being(r.get('by'), bid, f"{bid}[{i}].by"), being(r.get('to'), bid, f"{bid}[{i}].to")
                if x is None or y is None:
                    continue
                feats = {}
                for pos in listed(r.get('at')):
                    frame, _, feat = str(pos).partition('#')
                    if feat and frame in (x, y):
                        feats.setdefault(frame, feat)
                joints.append({'x': x, 'xf': feats.get(x), 'y': y, 'yf': feats.get(y), 'pair': r.get('as'),
                               'closures': listed(r.get('closure'))})
            elif verb == 'classify':
                code = said_of(r.get('as'))
                who = being(r.get('of'), bid, f"{bid}[{i}].of")
                if code and who:
                    said.setdefault(who, set()).add(code)
            elif verb == 'specify':
                of = r.get('of')
                frame, _, feat = (bid if of == 'self' else str(of)).partition('#') if isinstance(of, str) else ('', '', '')
                if frame == 'self':
                    frame = bid
                if feat:
                    featured.setdefault((frame, feat), {k: str(r[k]) for k in ('feature', 'side', 'profile', 'count')
                                                     if r.get(k) is not None})
                elif frame:
                    spec.setdefault(frame, r)
    for p, w in parts:
        if p in nodes and w in nodes:
            if nodes[w].device is False:
                nodes[w].fiat.append(p)
                nodes[p].fiat_of = w
            else:
                nodes[w].parts.append(p)
    for j in joints:
        for end, f in (('x', 'xf'), ('y', 'yf')):
            if j[f] and j[end] in nodes:
                nodes[j[end]].features = dict(nodes[j[end]].features or {}, **{j[f]: {}})
    for (nid, feat), f in featured.items():
        if nid in nodes:
            got = {'kind' if k == 'feature' else k: v for k, v in f.items()}
            nodes[nid].features = dict(nodes[nid].features or {}, **{feat: got})
    rows = concept_codes if isinstance(concept_codes, dict) else {}
    for nid, codes in said.items():
        if nid in nodes:
            nodes[nid].said |= codes & set(concept_codes)
    for nid, n in nodes.items():
        r = spec.get(nid) or {}
        if r.get('compliance') is not None:
            n.compliance = str(r['compliance'])
        n.limits.update({k: str(r[k]) for k in SAID_LIMITS if r.get(k) is not None})
        n.whole = str(r.get('whole')).lower() == 'true'
        for code in sorted(n.said):                 # a said form says what its root holds, where nothing else says it
            row = rows.get(code) or {}
            if row.get('level') != 'form':
                continue
            root = (row.get('pattern') or {}).get('root') or {}
            if n.compliance is None and root.get('compliance') is not None and n.device is not True:
                n.compliance = str(root['compliance'])
            for k in FROM_FORM[1:]:
                if n.limits.get(k) is None and root.get(k) is not None:
                    n.limits[k] = str(root[k])
    return Drawing(list(nodes.values()), joints)
