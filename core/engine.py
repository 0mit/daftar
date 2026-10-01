"""engine — the core's thirteen rules, applied to a garden written in statements (core spec §12).

A bean keeps its header (`bean`, `kind`, `title`, `summary`, `tags`, `details`), a list of `statements` and its body.
A statement is one verb and its roles: `- pay: { id: paid, by: ada, of: { count: "10.00", unit: XTS }, at: 2026-09-20 }`.
What a verb takes is its row's valency, read from the law; so the gate looks for itself — that reading needs a reader
and what is read is the row of `read`, and no rule here names it. The rules name only what they are about: the knowing
acts and their `now`, a row's default, the stand of the order, the line life is given along, the crown and `necessary`,
the figures, the foundation and its property, the frame, a namespace that gives once, and the flow table.

    judge(law, garden) -> [(rule, where, message)]       each one an error: the law is strict

`ratify` is a rule of the commit (a change to the law is a RULE-CHANGE a person ratifies), applied by the save."""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import frame, read  # noqa: E402
from core.law import listed, shapes_of, TRUE  # noqa: E402
import dmpass  # noqa: E402 — the one matcher of a path against a layer's pattern

HEADER = ('bean', 'kind', 'title', 'summary', 'tags', 'details', 'statements')
DOCUMENTS = ('beans', 'mappings')          # where a garden keeps its beans (dmpass.DOCUMENTS)
ID = re.compile(r'^[a-z0-9][a-z0-9_-]*$', re.ASCII)


class Bean:
    """One bean as read: its id, kind, header, statements as written, and why it could not be read (or None)."""

    def __init__(self, bid, path=None, header=None, unread=None):
        self.id, self.path, self.unread = bid, path, unread
        self.header = header or {}
        self.kind = self.header.get('kind')
        st = self.header.get('statements')
        self.statements = st if isinstance(st, list) else []
        self.items = []                                       # (index, verb, roles) for the well-formed ones
        for i, s in enumerate(self.statements):
            if isinstance(s, dict) and len(s) == 1:
                (verb, roles), = s.items()
                if isinstance(roles, dict):
                    self.items.append((i, verb, roles))
        self.ids = {r['id']: (i, v, r) for i, v, r in self.items if isinstance(r.get('id'), str)}


class Garden:
    """The beans of a garden, the zone its days are reckoned in, and the files its layers place."""

    def __init__(self, beans, zone=None, files=(), root=None):
        self.beans, self.zone, self.files, self.root = beans, zone, list(files), root

    @classmethod
    def read(cls, root):
        """A garden from its tree: `beans/**/*.md` and `mappings/**/*.md`, GARDEN.md's `zone`, and the files git tracks
        (or the tree's)."""
        beans = {}
        for dirpath, _dirs, names in [w for d in DOCUMENTS for w in os.walk(os.path.join(root, d))]:
            for n in sorted(names):
                if not n.endswith('.md'):
                    continue
                p = os.path.join(dirpath, n)
                bid = n[:-3]
                try:
                    head, _body = read.document(p)
                    beans[bid] = Bean(bid, p, head)
                except read.Unread as e:
                    beans[bid] = Bean(bid, p, unread=str(e))
        zone = None
        try:
            zone = read.document(os.path.join(root, 'GARDEN.md'))[0].get('zone')
        except read.Unread:
            pass
        return cls(beans, zone, _files(root), root)


def _files(root):
    try:
        out = subprocess.run(['git', '-C', root, 'ls-files', '-z'], capture_output=True, check=True).stdout
        return [p for p in out.decode('utf-8').split('\0') if p]
    except (OSError, subprocess.CalledProcessError):
        files = []
        for dirpath, dirs, names in os.walk(root):
            dirs[:] = [d for d in dirs if d != '.git']
            files += [os.path.relpath(os.path.join(dirpath, n), root).replace(os.sep, '/') for n in names]
        return sorted(files)


class Judge:
    def __init__(self, law, garden):
        self.L, self.G = law, garden
        self.out = []
        self.systems = law.std.systems

    def err(self, rule, where, msg):
        self.out.append((rule, where, msg))

    # ------------------------------------------------------------------------------------------------ beings
    def kind_of(self, x, b):
        """The kind of the being `x` names in bean `b`: None for the crown, `unknown`, or what names no being."""
        if isinstance(x, dict):
            return x.get('someone')
        if x == 'self':
            return b.kind
        if isinstance(x, str) and x in self.G.beans:
            return self.G.beans[x].kind
        return None

    def nature(self, kind):
        return (self.L.kinds.get(kind) or {}).get('nature')

    def line_of(self, kind):
        row = self.L.kinds.get(kind) or {}
        return row.get('line') or (self.L.level_line(row['level']) if row.get('level') else None)

    def norm(self, x, b):
        """A filler as one value, wherever it is written: `self` is the bean, a statement id is `<bean>#<id>`."""
        if x == 'self':
            return b.id
        if isinstance(x, str) and x in b.ids:
            return f"{b.id}#{x}"
        if isinstance(x, dict):
            return tuple(sorted((k, self.norm(v, b) if not isinstance(v, (dict, list)) else repr(v)) for k, v in x.items()))
        if isinstance(x, list):
            return tuple(self.norm(v, b) for v in x)
        return x

    def statement(self, ref, b):
        """(bean, index, verb, roles) of the statement `ref` names, or None."""
        if not isinstance(ref, str):
            return None
        if '#' in ref:
            bid, sid = ref.split('#', 1)
            other = self.G.beans.get(bid)
            hit = other.ids.get(sid) if other else None
            return (other,) + hit if hit else None
        hit = b.ids.get(ref)
        return (b,) + hit if hit else None

    # ------------------------------------------------------------------------------------------------ shapes
    def why_not(self, shape, x, spec, b):
        """'' when `x` has the shape `shape` and the narrowing of `spec`, else why not."""
        if shape == 'being':
            return self._being(x, spec, b)
        if shape == 'statement':
            if self.statement(x, b) is not None:
                return ''
            return f"{x!r} is no statement of this bean (another bean's is written `<bean>#<id>`)" \
                if isinstance(x, str) else "a statement is named by its id"
        if shape == 'position':
            try:
                frame.read(x, self.systems, self.G.zone)
                return ''
            except frame.Refused as e:
                return str(e)
        if shape == 'quantity':
            return self._quantity(x)
        if shape == 'row':
            return self.L.has(spec.get('table'), x)
        if shape == 'text':
            return '' if isinstance(x, str) else f"text is written as a string, not a {type(x).__name__}"
        return f"no shape {shape!r}"

    def _being(self, x, spec, b):
        if isinstance(x, dict):
            if 'someone' not in x or set(x) - {'someone', 'at'}:
                return "a being nobody names is written `{ someone: <kind>, at: <a being or a place> }`"
            if not isinstance(x['someone'], str) or x['someone'] not in self.L.kinds:
                return f"{x['someone']!r} is no kind of the law"
            if 'at' in x:
                at = x['at']
                if not (isinstance(at, str) and (at in self.G.beans or at == 'self')) and self.why_not('position', at, {}, b):
                    return f"someone is reached at a being or a place; {at!r} is neither"
            kind = x['someone']
        elif isinstance(x, str):
            if x in self.L.crown:
                kind = None
            elif x == 'self' or x in self.G.beans:
                kind = self.kind_of(x, b)
            else:
                return f"{x!r} is no bean of this garden, nor `self`, nor the crown"
        else:
            return f"a being is named by its bean, not by a {type(x).__name__}"
        nat = self.nature(kind)
        if spec.get('nature') and nat not in listed(spec['nature']):
            return f"this role takes a being that is {' or '.join(listed(spec['nature']))}; {x if isinstance(x, str) else kind} " \
                   f"is {nat or ('the crown' if x in self.L.crown else 'of no nature the law knows')}"
        if spec.get('rung') and nat == 'body' and (self.L.kinds.get(kind) or {}).get('rung') != spec['rung']:
            return f"a body fills this role only at {spec['rung']} (a person); {x if isinstance(x, str) else kind} is a " \
                   f"{kind}"
        return ''

    def _quantity(self, x):
        if isinstance(x, str):
            return '' if self.L.std.count(x) is not None else \
                f"{x!r}: a bare number is a count of the unit one, in plain decimal digits"
        if not isinstance(x, dict) or set(x) != {'count', 'unit'}:
            return "a quantity is `{ count, unit }`, or a bare number (a count of the unit one)"
        if self.L.std.count(x['count']) is None:
            return f"its count {x['count']!r} is not plain decimal digits, read exactly"
        return self.L.has('units', x['unit'])

    # ------------------------------------------------------------------------------------------------ one bean
    def bean(self, b):
        if b.unread:
            self.err('form', b.id, b.unread)
            return
        extra = [k for k in b.header if k not in HEADER]
        if extra:
            self.err('form', b.id, f"{', '.join(extra)}: a bean keeps its header ({', '.join(HEADER[:-1])}) and its "
                                   f"statements, nothing else — a fact is a statement, and what fits no verb yet is "
                                   f"kept whole in `details`")
        if b.header.get('bean') != b.id:
            self.err('form', b.id, f"`bean: {b.header.get('bean')}` — a bean names itself as its file does, `{b.id}`")
        if b.kind not in self.L.kinds:
            self.err('form', b.id, f"`kind: {b.kind}` is no kind of the law")
        for k in ('title', 'summary'):
            if k in b.header and not isinstance(b.header[k], str):
                self.err('form', b.id, f"`{k}` is text")
        if 'tags' in b.header and not (isinstance(b.header['tags'], list) and all(isinstance(t, str) for t in b.header['tags'])):
            self.err('form', b.id, "`tags` is a list of words")
        if not isinstance(b.header.get('statements', []), list):
            self.err('form', b.id, "`statements` is a list, each item one verb and its roles")
        seen = {}
        for i, s in enumerate(b.statements):
            if not (isinstance(s, dict) and len(s) == 1 and isinstance(next(iter(s.values())), dict)):
                self.err('form', f"{b.id}[{i}]", "a statement is one verb and its roles: `- <verb>: { <role>: <filler> }`")
        for i, verb, r in b.items:
            if 'id' in r:
                if not isinstance(r['id'], str) or not ID.match(r['id']):
                    self.err('form', f"{b.id}[{i}] {verb}", f"its id {r['id']!r} is one word: letters, digits, `-`")
                elif r['id'] in seen:
                    self.err('form', f"{b.id}[{i}] {verb}", f"the id `{r['id']}` names statement [{seen[r['id']]}] already")
                else:
                    seen[r['id']] = i
        for i, verb, r in b.items:
            self.one(b, i, verb, r)
        self.knowing(b)

    def one(self, b, i, verb, r):
        where = f"{b.id}[{i}] {verb}"
        v = self.L.verbs.get(verb)
        if v is None:
            near = sorted(self.L.verbs, key=lambda n: (n[:1] != verb[:1], abs(len(n) - len(verb)), n))[:3]
            self.err('form', where, f"`{verb}` is no verb of the law (nearest: {', '.join(near)}); a new verb is a row, "
                                    f"proposed and ratified")
            return
        roles, quals = v.get('roles') or {}, v.get('qualifiers') or {}
        for k in r:
            if k not in roles and k not in quals and k not in self.L.beside:
                self.err('form', where, f"`{k}` is no role, qualifier or key `{verb}` takes: it takes "
                                        f"{', '.join(list(roles) + list(quals))}, and {', '.join(sorted(self.L.beside))}")
        for k in ('why', 'note'):
            if k in r and not isinstance(r[k], str):
                self.err('form', where, f"`{k}` is prose")
        if 'while' in r:
            w = r['while']
            if not (isinstance(w, str) and (w in self.L.conditions or self.statement(w, b) is not None)):
                self.err('form', where, f"`while: {w}` matches no condition ({', '.join(sorted(self.L.conditions))}) "
                                        f"and no statement")
        required = listed(v.get('required'))
        for k in required:
            if k not in r:
                self.err('valency', where, f"`{k}` is required: {verb} {self._valency(v)} — `unknown` where nobody said")
        ch = (v.get('choice') or {}).get('one_of')
        if ch and sum(1 for k in listed(ch) if k in r) != 1:
            self.err('valency', where, f"one of {', '.join(listed(ch))}, and only one")
        for k, spec in list(roles.items()) + list(quals.items()):
            if k in r:
                self.fill(where, k, spec, r[k], k in required or k in listed(ch), b)     # a choice is required too

    def _valency(self, v):
        req = listed(v.get('required'))
        return 'takes ' + ', '.join(f"{k}{'' if k in req else '?'}" for k in (v.get('roles') or {}))

    def fill(self, where, k, spec, value, required, b):
        if 'now' in (value if isinstance(value, list) else [value]) and k != 'at':
            self.err('frame', where, f"`{k}: now` — `now` is the moment of the save, which the save writes at `at` alone")
            return
        if value == 'unknown':
            if not required:
                self.err('valency', where, f"`{k}: unknown` — `unknown` fills a required role nobody said; leave this "
                                           f"one out")
            return
        if isinstance(value, list):
            if spec.get('many') != TRUE:
                self.err('valency', where, f"`{k}` takes one filler, not a list")
                return
            if not value:
                self.err('valency', where, f"`{k}: []` says nothing: leave the role out")
                return
            vals = value
        elif spec.get('keyed') == TRUE:
            if not isinstance(value, dict) or not value:
                self.err('valency', where, f"`{k}` is a map whose keys are names")
                return
            vals = list(value.values())
        else:
            vals = [value]
        shapes = shapes_of(spec)
        for x in vals:
            whys = [self.why_not(s, x, spec, b) for s in shapes]
            if all(whys):
                rule = 'frame' if shapes == ['position'] else 'valency'
                said = whys[0] if len(whys) == 1 else '; '.join(f"not a {s}: {w}" for s, w in zip(shapes, whys))
                self.err(rule, where, f"`{k}`: {said}")

    # ------------------------------------------------------------------------------------------------ knowing
    def knowing(self, b):
        covered, blanket = set(), False
        for i, verb, r in b.items:
            if verb not in self.L.knowing:
                continue
            if 'of' in r:
                covered |= {x for x in listed(r['of']) if isinstance(x, str)}
            else:
                blanket = True
            at = r.get('at')
            if at != 'now':
                try:
                    p = frame.read(at, self.systems, self.G.zone)
                    ok = p.moment is not None and p.stated and p.end is None
                except frame.Refused:
                    ok = False
                if not ok:
                    self.err('knowing', f"{b.id}[{i}] {verb}", f"`at: {at}` — the moment of a knowing act is the save's: "
                                                              f"write `now`, and the save writes the moment in its place")
        if blanket:
            return
        for i, verb, r in b.items:
            if verb not in self.L.knowing and not (isinstance(r.get('id'), str) and r['id'] in covered):
                self.err('knowing', f"{b.id}[{i}] {verb}", "known by no act: say who said, read, made or derived it — "
                                                          "a knowing act in this bean whose `of` names it, or one with "
                                                          "no `of`, which covers the rest")

    # ------------------------------------------------------------------------------------------------ across beans
    def placeholder(self):
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                d = (self.L.verbs.get(verb) or {}).get('default')
                if not d or any(r.get(k) != val for k, val in (d.get('when') or {}).items()):
                    continue
                same = []
                for role, how in (d.get('fill') or {}).items():
                    if role not in r:
                        same = []
                        break
                    got = self._derive(how, r, b)
                    same.append(got is not None and self.norm(r[role], b) == got)
                if not same or not all(same):
                    continue
                if d.get('alone') == TRUE and any(v2 == verb and j != i and self.norm(r2.get('of'), b) == self.norm(r.get('of'), b)
                                                  for j, v2, r2 in b.items):
                    continue
                self.err('placeholder', f"{b.id}[{i}] {verb}", f"says what the law derives already ({d.get('says')}): "
                                                               f"a default is never written")

    def _derive(self, how, r, b):
        if 'the' in how:
            hit = self.statement(r.get(how['the']), b)
            if hit is None:
                return None
            other, _j, _v, r2 = hit
            return self.norm(r2.get(how['take']), other) if how['take'] in r2 else None
        hits = [r2 for _j, v2, r2 in b.items if v2 == how['verb']
                and all(self.norm(r2.get(theirs), b) == self.norm(r.get(mine), b) for theirs, mine in how['match'].items())]
        return self.norm(hits[0].get(how['take']), b) if len(hits) == 1 and how['take'] in hits[0] else None

    def order(self):
        graph = {lv: {s['at'] for s in listed(row.get('stands')) if isinstance(s, dict)} for lv, row in self.L.levels.items()}
        edges = []
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if verb == 'stand' and 'by' in r and 'at' in r:
                    a, c = self.norm(r['by'], b), self.norm(r['at'], b)
                    if isinstance(a, str) and isinstance(c, str):
                        graph.setdefault(a, set()).add(c)
                        edges.append((a, c, f"{b.id}[{i}] stand"))
        for a, c, where in edges:
            path = [a] if a == c else self._path(graph, c, a)
            if path:
                self.err('order', where, f"{a} stands at {' → '.join([c] + path[:-1]) if path[:-1] else c}, which stands "
                                         f"on {a}: nothing stands on itself through others")
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if verb != 'part' or 'by' not in r or 'of' not in r:
                    continue
                lp = (self.L.kinds.get(self.kind_of(r['by'], b)) or {}).get('level')
                lw = (self.L.kinds.get(self.kind_of(r['of'], b)) or {}).get('level')
                if lp and lw and lp != lw and lp not in self.L.below(lw, ways=('made-of',)):
                    self.err('order', f"{b.id}[{i}] part", f"a part never stands above its whole: {lp} is not {lw} and "
                                                           f"not a level {lw} is made of")

    @staticmethod
    def _path(graph, start, target):
        """The steps from `start` to `target` through `graph`, ending at `target` — [] where there is no way."""
        back, todo = {start: None}, [start]
        while todo:
            n = todo.pop(0)
            for m in sorted(graph.get(n, ())):
                if m == target:
                    steps = [n]
                    while back[steps[-1]] is not None:
                        steps.append(back[steps[-1]])
                    return list(reversed(steps))[1:] + [m]
                if m not in back:
                    back[m] = n
                    todo.append(m)
        return []

    @staticmethod
    def _reaches(graph, start, target):
        seen, todo = set(), [start]
        while todo:
            n = todo.pop()
            for m in graph.get(n, ()):
                if m == target:
                    return True
                if m not in seen:
                    seen.add(m)
                    todo.append(m)
        return False

    def life(self):
        comes = {}
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if verb == 'come' and 'by' in r:
                    comes.setdefault(self.norm(r['by'], b), []).append((b, i, r))
        for who, sts in comes.items():
            for b, i, r in sts:
                where = f"{b.id}[{i}] come"
                line = self.line_of(self.kind_of(r['by'], b))
                given = (self.L.lines.get(line) or {}).get('given') == TRUE
                for t in listed(r.get('through')):
                    if isinstance(t, str) and t in self.L.crown:
                        continue                           # the chain's end
                    tk = self.kind_of(t, b)
                    if given:
                        if self.line_of(tk) != line:
                            self.err('life', where, f"a being of the line {line} comes through the {line}: "
                                                    f"{t if isinstance(t, str) else tk} is not")
                    else:
                        hands = (self.L.kinds.get(tk) or {}).get('rung') == 'reason'     # a being at reason
                        tool = isinstance(t, str) and self.norm(t, b) in comes
                        if not (hands or tool):
                            self.err('life', where, f"a made or said being comes through hands (a being at reason), or "
                                                    f"through a tool whose own coming goes on: "
                                                    f"{t if isinstance(t, str) else tk} is neither")
        graph = {w: {self.norm(t, b) for b, _i, r in sts for t in listed(r.get('through')) if isinstance(t, str)}
                 for w, sts in comes.items()}
        for w, sts in comes.items():
            if self._reaches(graph, w, w):
                self.err('life', f"{sts[0][0].id}[{sts[0][1]}] come", f"{w} comes through itself: every chain ends at "
                                                                      f"the crown, and a circle never ends")

    def necessity_and_squares(self):
        ops = {}
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                v = self.L.verbs.get(verb) or {}
                if verb == 'necessary' and 'through' not in r and not (isinstance(r.get('of'), str) and r['of'] in self.L.crown):
                    self.err('necessity', f"{b.id}[{i}] necessary", "only the crown is necessary by itself: say what "
                                                                    "this is necessary `through`")
                if v.get('figure'):
                    key = (self.norm(r.get('of'), b), self.norm(r.get('through'), b))
                    ops.setdefault(key, []).append((verb, f"{b.id}[{i}] {verb}"))
        for (of, through), vs in ops.items():
            for a, wa in vs:
                for c, wc in vs:
                    if (a, c) in self.L.incompatible and a < c:
                        self.err('squares', wa, f"{a} and {c} of {of} through {through} cannot both stand ({wc})")

    def weight(self):
        for f in self.L.foundations:
            prop, holds = f.get('property'), f.get('holds_for')
            if not prop:
                continue
            for b in self.G.beans.values():
                for i, verb, r in b.items:
                    if r.get('as') == prop and 'of' in r:
                        nat = self.nature(self.kind_of(r['of'], b))
                        if nat and nat != holds:
                            self.err('weight', f"{b.id}[{i}] {verb}", f"{f.get('foundation')} holds for a {holds}: a "
                                                                      f"{prop} is a {holds}'s, and {self.norm(r['of'], b)} "
                                                                      f"is {nat}")

    def names(self):
        given = {}
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if verb == 'name' and isinstance(r.get('by'), str) and (self.L.namespaces.get(r['by']) or {}).get('once') == TRUE:
                    given.setdefault((r['by'], r.get('as')), []).append((self.norm(r.get('of'), b), f"{b.id}[{i}] name"))
        for (ns, nm), hits in given.items():
            beings = sorted({str(h[0]) for h in hits})
            if len(beings) > 1:
                self.err('names', hits[-1][1], f"{ns} gives {nm!r} once, and it names {', '.join(beings)}")

    def layers(self):
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if verb != 'pass':
                    continue
                m = (r.get('from'), r.get('to'), r.get('through'))
                rows = [f for f in self.L.flows if m[0] in listed(f.get('from')) and m[1] in listed(f.get('to'))
                        and m[2] in listed(f.get('through'))]
                if not rows or any(f.get('grant') != 'granted' for f in rows):
                    self.err('layers', f"{b.id}[{i}] pass", f"no row of the flow table grants {m[0]} → {m[1]} through "
                                                            f"{m[2]}" + (f" ({', '.join(str(f.get('flow', '')) for f in rows)} refuses it)"
                                                                         if rows else ''))
        if self.L.standing:
            for p in self.G.files:
                hold = sorted({s['layer'] for s in self.L.standing for h in listed(s.get('holds')) if dmpass.matches(h, p)})
                if len(hold) > 1:
                    self.err('layers', p, f"a file stands in one layer, and this one in {', '.join(hold)}")

    def run(self):
        if self.G.zone is not None and self.G.zone not in self.L.std.zones:
            self.err('frame', 'GARDEN.md', f"`zone: {self.G.zone}` is no zone of the IANA time zone database "
                                           f"(seed/knowledge/time-zones.tsv): `Region/City`")
        for b in self.G.beans.values():
            self.bean(b)
        self.placeholder()
        self.order()
        self.life()
        self.necessity_and_squares()
        self.weight()
        self.names()
        self.layers()
        return self.out


def judge(law, garden):
    """[(rule, where, message)] for `garden` under `law`: the law's own problems first, then the garden's."""
    return list(law.problems()) + Judge(law, garden).run()
