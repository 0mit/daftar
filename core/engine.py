"""engine — the core's eighteen rules, applied to a garden written in statements (core spec §12).

A bean keeps its header (`bean`, `kind`, `title`, `summary`, `tags`, `details`), a list of `statements` and its body.
A statement is one verb and its roles: `- pay: { id: paid, by: ada, of: { count: "10.00", unit: XTS }, at: 2026-09-20 }`.
What a verb takes is its row's valency, read from the law; so the gate looks for itself — that reading needs a reader
and what is read is the row of `read`, and no rule here names it. The rules name only what they are about: the knowing
acts and their `now`, a row's default, the stand of the order, the line life is given along, the crown and `necessary`,
the figures, the foundation and its property, the frame, a namespace that gives once, and the flow table.

    judge(law, garden) -> [(rule, where, message)]       each one an error: the law is strict

`ratify` is a rule of the commit (a change to the law is a RULE-CHANGE a person ratifies), applied by the save; its
other half — a grant to ratify is the gardener's own act — is judged here. So are the rules today's gate held that the
core took over in v1 (ratified 2026-10-01, "do the pending items including consent and other old gate checks"):
`consent` (a person kept by name on their own word), `harm` (special-category sealed, a sealed statement's form, a
sensitivity lowered on a person's word), `room` (two beings in one room, one port, one hour; what a garden declares
exclusive), `vacancy` (a garden's row used, or said vacant), and the parts of `form`, `order` and `names` they added.
The commit's halves of `consent`, `harm` and `kept` are core/commit.py's."""
import os
import re
import subprocess
import sys
from fractions import Fraction

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import frame, read  # noqa: E402
import dmcal  # noqa: E402 — a day's length, to reckon a day's span beside a moment's
from core.law import listed, shapes_of, TRUE  # noqa: E402
import dmpass  # noqa: E402 — the one matcher of a path against a layer's pattern
import dmparse  # noqa: E402 — the one splitter of a front matter, the one reader of a garden's id, the control characters

HEADER = ('bean', 'kind', 'title', 'summary', 'tags', 'details', 'statements')
DOCUMENTS = ('beans', 'mappings')          # where a garden keeps its beans (dmpass.DOCUMENTS)
ID = re.compile(r'^[a-z0-9][a-z0-9_-]*$', re.ASCII)
HELD = re.compile(r'^root:[a-z0-9][a-z0-9-]*/[0-9a-f]{32}$')        # a sealed statement's pointer (dmheld mints it)
SEALED = {'held', 'id', 'while', 'why', 'note'}                    # all a sealed statement carries
OPAQUE = re.compile(r'^p-[0-9a-f]{8}$')                             # a person written by an opaque id (dmheld person)
GARDEN_ID = re.compile(r'^[0-9a-f]{12}$')
QUALIFIED = re.compile(r'^([0-9a-f]{12})/([a-z][a-z0-9-]*):([a-z0-9][a-z0-9._-]*)$')
LEVELS = ('none', 'personal', 'special-category')                  # sensitivity, lowest first (dmpass.LEVELS)
GARDENER_KINDS = ('person', 'org')                                  # who may keep a garden (today's `manifest`)
TEXT = dict(holds_no='Cc', but=('\t',), lines_in='block')          # text holds no control character (`value_types`)
PORTS = ('tcp-port', 'udp-port')                                    # the systems whose positions are ports (IANA)


class Bean:
    """One bean as read: its id, kind, header, statements as written, and why it could not be read (or None)."""

    def __init__(self, bid, path=None, header=None, unread=None, raw=None, body=None):
        self.id, self.path, self.unread, self.raw, self.body = bid, path, unread, raw, body
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

    def __init__(self, beans, zone=None, files=(), root=None, manifest=None, gid=None):
        self.beans, self.zone, self.files, self.root = beans, zone, list(files), root
        self.manifest = manifest or {}
        self.has_manifest, self.manifest_unread = False, None   # a GARDEN.md read from a tree (Garden.read) is judged
        self.gardener = self.manifest.get('gardener') if isinstance(self.manifest.get('gardener'), str) else None
        self.gid = gid                     # this garden's own id, read from git (None outside one)

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
                    head, body = read.document(p)
                    with open(p, encoding='utf-8') as fh:
                        raw = dmparse.split_front_matter(fh.read())[0]
                    beans[bid] = Bean(bid, p, head, raw=raw, body=body)
                except read.Unread as e:
                    beans[bid] = Bean(bid, p, unread=str(e))
        manifest, unread = {}, None
        if os.path.isfile(os.path.join(root, 'GARDEN.md')):
            try:
                manifest = read.document(os.path.join(root, 'GARDEN.md'))[0]
            except read.Unread as e:
                unread = str(e)
            if not isinstance(manifest, dict):
                manifest, unread = {}, "its front matter is no mapping of the manifest's keys"
        try:
            gid = dmparse.garden_id(root)
        except Exception:
            gid = None
        g = cls(beans, manifest.get('zone'), _files(root), root, manifest, gid)
        g.has_manifest, g.manifest_unread = os.path.isfile(os.path.join(root, 'GARDEN.md')), unread
        return g


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
            # TODAY'S WORD SAYS WHERE IT WENT (std-vocab's `retired`, v1 part 4): the verb whose row `replaces` it
            went = {w: v for w, v in self.L.replaces if w in extra}
            said = {'face': "the verb `{}` of the face", 'role': "the role `{}`"}
            self.err('form', b.id, f"{', '.join(extra)}: a bean keeps its header ({', '.join(HEADER[:-1])}) and its "
                                   f"statements, nothing else — a fact is a statement, and what fits no verb yet is "
                                   f"kept whole in `details`" + ('' if not went else '. In today\'s words: ' + '; '.join(
                                       f"`{w}` is " + ('dropped' if v == 'dropped' else
                                                       said[v.split()[0]].format(v.split()[1]) if ' ' in v else
                                                       f"the verb `{v}`")
                                       for w, v in sorted(went.items())) + " (core/law/verbs.yaml `replaces`)"))
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
        if 'held' in r and v is not None:
            self.sealed(b, where, r)
            return
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
                if verb == 'name' and isinstance(r.get('by'), str) and r.get('as') != 'unknown' \
                        and (self.L.namespaces.get(r['by']) or {}).get('once') == TRUE:     # a name nobody said names nobody
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

    # ------------------------------------------------------------------------------------------------ what today's gate held
    def _beans_in(self, x, b):
        """The beans a filler names, `self` read as its bean: one or a list."""
        return [b.id if v == 'self' else v for v in listed(x) if v == 'self' or (isinstance(v, str) and v in self.G.beans)]

    def _is_person(self, bid):
        """A being at reason: a person (the kind's `rung`)."""
        bean = self.G.beans.get(bid)
        return bool(bean) and (self.L.kinds.get(bean.kind) or {}).get('rung') == 'reason'

    def _acts_of(self, b, i, r):
        """The knowing acts that cover statement [i] of bean b: those whose `of` names its id, else those with no `of`."""
        sid = r.get('id') if isinstance(r.get('id'), str) else None
        named = [(v, rr) for _j, v, rr in b.items if v in self.L.knowing and sid is not None and sid in listed(rr.get('of'))]
        return named or [(v, rr) for _j, v, rr in b.items if v in self.L.knowing and 'of' not in rr]

    def _declined(self):
        """(bean, index) of every statement a `decline` names: what was declined holds nothing."""
        out = set()
        for b in self.G.beans.values():
            for _i, verb, r in b.items:
                if verb == 'decline':
                    for x in listed(r.get('of')):
                        hit = self.statement(x, b)
                        if hit:
                            out.add((hit[0].id, hit[1]))
        return out

    def _related(self, a, c):
        """Whether one being is part of, or at, the other, through any number of steps."""
        up = {}
        for b in self.G.beans.values():
            for _i, verb, r in b.items:
                if (verb == 'part' and 'of' in r) or (verb == 'be' and 'at' in r):
                    for x in self._beans_in(r.get('by'), b):
                        up.setdefault(x, set()).update(self._beans_in(r.get('of') if verb == 'part' else r.get('at'), b))
        return self._reaches(up, a, c) or self._reaches(up, c, a)

    def _span(self, x, to_the_moment=False):
        """(lo, hi) in ms of a time position or an extent — a day is the whole day — or None. With `to_the_moment`, only
        an extent whose two ends are moments."""
        if not isinstance(x, str) or x in ('now', 'unknown'):
            return None
        try:
            p = frame.read(x, self.systems, self.G.zone)
        except frame.Refused:
            return None
        if to_the_moment and (p.moment is None or p.end is None or p.end.moment is None):
            return None

        def ms(q, end):
            if q.moment is not None:
                return q.moment
            return (q.day + (1 if end else 0)) * dmcal.DAY_MS if q.day is not None else None
        lo = ms(p, False)
        hi = ms(p.end, True) if p.end is not None else ms(p, True)
        return (lo, hi) if lo is not None and hi is not None else None

    def _codes(self, x):
        """The scheme of every code `<scheme>:<code>` a structure holds, as written."""
        if isinstance(x, dict):
            for v in x.values():
                yield from self._codes(v)
        elif isinstance(x, list):
            for v in x:
                yield from self._codes(v)
        elif isinstance(x, str) and ':' in x:
            yield x.split(':', 1)[0]

    def _marked(self):
        """The schemes marked special-category: the garden's own, as it declares them (dmknowledge reads them)."""
        try:
            return {k for k, r in self.L.std.knowledge.schemes.items()
                    if isinstance(r, dict) and r.get('sensitive') == 'special-category'}
        except Exception:
            return set()

    def derived(self, bid):
        """The sensitivity a bean derives, never stored: special-category where it holds a code of a scheme so marked,
        unsealed; personal where it is the bean of a person who is not the gardener, or concerns one."""
        b, marked = self.G.beans[bid], self._marked()
        if marked and any(s in marked for _i, _v, r in b.items if 'held' not in r for s in self._codes(r)) or \
                (marked and any(s in marked for s in self._codes(b.header.get('details')))):
            return 'special-category'
        g = self.G.gardener
        if (self._is_person(bid) and bid != g) or any(
                x != g and self._is_person(x) for _i, v, r in b.items if v == 'concern' for x in self._beans_in(r.get('of'), b)):
            return 'personal'
        return 'none'

    def sealed(self, b, where, r):
        """A sealed statement: its verb, a pointer, an id, and what it is held `while`; nothing of what it said."""
        extra = sorted(set(r) - SEALED)
        if extra:
            self.err('harm', where, f"is sealed, and holds {', '.join(extra)} beside it: a sealed statement keeps its verb "
                                    f"and carries only held, id, while, why and note — what it said is in the held store")
        if not (isinstance(r.get('held'), str) and HELD.match(r['held'])):
            self.err('harm', where, "`held` is `root:<root>/<32 lowercase hexadecimal digits>`, a key bin/dmheld.py "
                                    "mints, which says nothing of what it holds")
        if not isinstance(r.get('id'), str):
            self.err('harm', where, "a sealed statement has an id, which the journal names when it is sealed or erased")
        w = r.get('while')
        if w is not None:
            if not (isinstance(w, str) and (w in self.L.conditions or self.statement(w, b) is not None)):
                self.err('form', where, f"`while: {w}` matches no condition and no statement")
        elif self.derived(b.id) != 'none':
            self.err('harm', where, "is held on nothing: the bean concerns a person who is not the gardener — write "
                                    "`while: <their agree, or the agreement's>`, the word it is held on")

    def text_and_gardener(self):
        """Text holds no control character; GARDEN.md names a gardener the garden holds, once it holds a bean."""
        for b in self.G.beans.values():
            try:
                found = dmparse.control_characters(b.raw, TEXT['holds_no'], TEXT['but'], TEXT['lines_in']) if b.raw else []
            except Exception:
                found = []
            for path, ch, _style, is_key in found:
                self.err('form', b.id, f"{'the key ' if is_key else ''}{path} holds U+{ord(ch):04X}: text holds no "
                                       f"control character but a tab, and a line feed only in a block scalar (`|`, `>`)")
        self.manifest()
        if not (self.G.beans and self.G.manifest):
            return
        g = self.G.manifest.get('gardener')
        if not g:
            self.err('form', 'GARDEN.md', "names no gardener: a garden is kept by someone — write their bean, and name it "
                                          "here, `gardener: <bean>`")
        elif not (isinstance(g, str) and g in self.G.beans and self.G.beans[g].kind in GARDENER_KINDS):
            self.err('form', 'GARDEN.md', f"`gardener: {g}` — the gardener is a person or an organisation this garden "
                                          f"holds a bean for")

    def manifest(self):
        """GARDEN.md holds the manifest's keys alone, each in its form (core.yaml `manifest`), and pins this law."""
        if self.G.manifest_unread:
            self.err('form', 'GARDEN.md', f"does not read ({self.G.manifest_unread}): the manifest says which garden this "
                                          f"is, whose, and which law it runs")
            return
        if not self.G.has_manifest:
            return
        M, forms = self.L.manifest, self.L.manifest_forms
        for k, v in self.G.manifest.items():
            row = M.get(k)
            if row is None:
                self.err('form', 'GARDEN.md', f"`{k}` is no key of the manifest, whose keys are {', '.join(M)} — a "
                                              f"standing note for readers belongs in its body")
                continue
            form = row.get('form')
            if form in forms:
                if not (isinstance(v, str) and re.fullmatch(forms[form]['pattern'], v)):
                    self.err('form', 'GARDEN.md', f"`{k}: {v}` — {forms[form].get('says')}")
            elif form == 'pin':
                want = f"core@{self.L.version}"
                if v != want:
                    self.err('form', 'GARDEN.md', f"`{k}: {v}` — a garden of statements runs this law, `{want}`: the pin "
                                                  f"moves with the law, a RULE-CHANGE (bin/dmupgrade.py moves it)")
            elif form == 'text' and not isinstance(v, str):
                self.err('form', 'GARDEN.md', f"`{k}` is text")
            elif form == 'texts' and not (isinstance(v, str) or (isinstance(v, dict) and v and all(
                    isinstance(x, str) for x in v.values()))):
                self.err('form', 'GARDEN.md', f"`{k}` is text, or texts each under a name of its own")
        for k, row in M.items():
            if row.get('required') == 'true' and k not in self.G.manifest:
                self.err('form', 'GARDEN.md', f"`{k}:` is missing — the manifest requires it: {row.get('meaning')}")

    def cycles(self):
        """Nothing owns itself, is part of itself, is at itself or needs itself through others."""
        for verb, low, high, says in (('own', ('of',), ('by', 'from'), 'owns'), ('part', ('by',), ('of',), 'is part of'),
                                      ('be', ('by',), ('at',), 'is at'), ('need', ('by',), ('of',), 'needs')):
            graph, first = {}, {}
            for b in self.G.beans.values():
                for i, v, r in b.items:
                    if v != verb or 'held' in r:
                        continue
                    for a in [x for k in low for x in self._beans_in(r.get(k), b)]:
                        for c in [x for k in high for x in self._beans_in(r.get(k), b)]:
                            graph.setdefault(a, set()).add(c)
                            first.setdefault((a, c), f"{b.id}[{i}] {verb}")
            for (a, c), where in sorted(first.items()):
                path = [a] if a == c else self._path(graph, c, a)
                if path:
                    self.err('order', where, f"{' → '.join([a, c] + path[:-1] + ([a] if a != c else []))}: nothing "
                                             f"{says} itself through others")

    def gardens(self):
        """A garden's id names another garden; a name qualified to cross names a garden this one knows."""
        known = {self.G.gid} if self.G.gid else set()
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                a = r.get('as')
                if verb != 'name' or r.get('by') != 'garden-id' or 'held' in r or a == 'unknown':
                    continue
                if not (isinstance(a, str) and GARDEN_ID.match(a)):
                    self.err('names', f"{b.id}[{i}] name", f"{a!r}: a garden's id is the first twelve hexadecimal digits "
                                                          f"of the root of its history, as `python3 bin/dmpropose.py id` "
                                                          f"prints it")
                elif a == self.G.gid:
                    self.err('names', f"{b.id}[{i}] name", f"{a} is this garden's own id: a `garden` bean records another "
                                                          f"garden, and this one's id is read from its git. A rehearsal "
                                                          f"is grown, never cloned, and has an id of its own")
                else:
                    known.add(a)
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                a = r.get('as')
                if verb != 'name' or r.get('by') != 'garden' or 'held' in r or a == 'unknown':
                    continue
                m = QUALIFIED.match(a) if isinstance(a, str) else None
                if not m:
                    self.err('names', f"{b.id}[{i}] name", f"{a!r}: a name a garden gave, qualified to cross, is "
                                                          f"`<garden_id>/<kind>:<name>` — an identifier someone else "
                                                          f"assigned is never qualified: write it by the namespace that "
                                                          f"assigned it")
                elif m.group(2) not in self.L.kinds:
                    self.err('names', f"{b.id}[{i}] name", f"`{m.group(2)}` is no kind of the law")
                elif m.group(1) not in known:
                    self.err('names', f"{b.id}[{i}] name", f"{m.group(1)} is no garden this one knows: record it first, "
                                                          f"a `garden` bean named by its id (`name: {{ by: garden-id }}`)")

    def grants(self):
        """A grant to ratify is the gardener's own act: on the gardener's bean, by the gardener, said by the gardener."""
        g = self.G.gardener
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if verb != 'grant' or r.get('as') != 'ratify' or 'held' in r:
                    continue
                said = any(v == 'say' and self._beans_in(rr.get('by'), b) == [g] for v, rr in self._acts_of(b, i, r))
                if not (g and b.id == g and self._beans_in(r.get('by'), b) == [g] and said):
                    self.err('ratify', f"{b.id}[{i}] grant", "a grant to ratify is the gardener's own act: on the "
                                                             "gardener's bean, `by` the gardener (`self` there), said by "
                                                             "the gardener")

    def consent(self):
        """Another person is kept by name only on their own word."""
        g, declined, agreed, kept = self.G.gardener, self._declined(), set(), set()
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if 'held' in r:
                    continue
                if verb == 'agree' and (b.id, i) not in declined:
                    agreed.update(self._beans_in(r.get('by'), b))
                if verb == 'own' and any(self.G.beans[x].kind == 'garden' for x in self._beans_in(r.get('of'), b)):
                    kept.update(self._beans_in(r.get('by'), b))
        for bid, bean in sorted(self.G.beans.items()):
            if not self._is_person(bid) or bid == g or bid in agreed or bid in kept:
                continue
            if OPAQUE.match(bid) and bean.header.get('title') == bid:
                continue
            self.err('consent', bid, "names a person who is not the gardener, and no word of theirs is recorded: an "
                                     "`agree` of theirs to an agreement this garden holds, or the garden they keep, met "
                                     "here (a `garden` bean they `own`) — or write them under an opaque id, as `python3 "
                                     "bin/dmheld.py person` mints one, their name held off git")

    def harm(self):
        """Special-category material only sealed; a sensitivity lowered only on a person's own word."""
        marked = self._marked()
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if marked and 'held' not in r and any(s in marked for s in self._codes(r)):
                    self.err('harm', f"{b.id}[{i}] {verb}", "holds a code of a scheme marked special-category, "
                                                            "unsealed: seal it before the commit that would carry it — "
                                                            "a value committed is in every clone for good")
                if verb != 'rate' or 'held' in r or r.get('as') not in LEVELS:
                    continue
                for t in self._beans_in(r.get('of'), b):
                    lv = self.derived(t)
                    by_person = any(v == 'say' and self._beans_in(rr.get('by'), b)
                                    and all(self._is_person(x) for x in self._beans_in(rr.get('by'), b))
                                    for v, rr in self._acts_of(b, i, r))
                    if LEVELS.index(r['as']) < LEVELS.index(lv) and not by_person:
                        self.err('harm', f"{b.id}[{i}] rate", f"rates {t} {r['as']}, below the {lv} it derives: "
                                                              f"lowering is a person's own word, said by a person "
                                                              f"(class E), never derived")
            if marked and any(s in marked for s in self._codes(b.header.get('details'))):
                self.err('harm', f"{b.id} details", "holds a code of a scheme marked special-category, unsealed: what "
                                                    "fits no verb yet is sealed as a statement is")

    def room(self):
        """Two bodies in one room — a sayable takes no room — two listeners at one port, one being in two places in one
        hour; and what a garden declares exclusive."""
        declined = self._declined()

        def once(seen, key, w, where, says):
            o = seen.get(key)
            if o and o[0] != w and not self._related(o[0], w):
                self.err('room', where, says(o))
            else:
                seen.setdefault(key, (w, where))
        rooms, ports = {}, {}
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if 'held' in r or verb not in ('be', 'serve'):
                    continue
                where, at = f"{b.id}[{i}] {verb}", []
                for x in listed(r.get('at')):
                    if isinstance(x, str) and x not in self.G.beans and x not in ('self', 'now', 'unknown'):
                        try:
                            at.append(frame.read(x, self.systems, self.G.zone))
                        except frame.Refused:
                            pass
                places = [p for p in at if p.day is None and p.moment is None]
                for w in self._beans_in(r.get('by'), b):
                    if verb == 'be' and r.get('as') == 'location' and self.nature(self.G.beans[w].kind) == 'body':
                        for p in places:
                            once(rooms, (p.system, p.text), w, where,
                                 lambda o, p=p, w=w: f"{w} is at {p.text}, where {o[0]} is ({o[1]}): two beings are not "
                                                     f"in one room at once — one of them has moved, or one is part of, "
                                                     f"or at, the other")
                    if verb == 'serve':
                        for a in [p for p in places if p.system not in PORTS]:
                            for q in [p for p in places if p.system in PORTS]:
                                once(ports, (a.system, a.text, q.system, q.text), w, where,
                                     lambda o, a=a, q=q, w=w: f"{w} listens at {a.text} {q.system} {q.text}, where "
                                                              f"{o[0]} listens ({o[1]}): one port on one address is one "
                                                              f"listener's at a time")
        hours = {}
        for b in self.G.beans.values():
            for i, verb, r in b.items:
                if verb != 'attend' or 'held' in r or (b.id, i) in declined:
                    continue
                sp = self._span(r.get('at'), True)
                for t in self._beans_in(r.get('of'), b) if sp is None else []:
                    sp = next((s for _j, v2, r2 in self.G.beans[t].items if v2 == 'be' and 'held' not in r2
                               for x in listed(r2.get('at')) for s in [self._span(x, True)] if s), None) or sp
                if sp:
                    for w in self._beans_in(r.get('by'), b):
                        hours.setdefault(w, []).append((sp, f"{b.id}[{i}] attend", tuple(self._beans_in(r.get('of'), b))))
        self._overlaps(hours, lambda w, w1, w2: f"{w} attends this and what {w1} attends, and their times overlap: a "
                                                f"happening takes the time of those present, and nobody spends one hour "
                                                f"twice", distinct=True)
        for x in self.L.exclusive:
            held = {}
            for b in self.G.beans.values():
                for i, verb, r in b.items:
                    if verb != x.get('verb') or 'held' in r or (b.id, i) in declined:
                        continue
                    sp = self._span(r.get('at'))
                    for w in self._beans_in(r.get('by'), b) if sp else []:
                        held.setdefault(w, []).append((sp, f"{b.id}[{i}] {verb}", ()))
            self._overlaps(held, lambda w, w1, w2, v=x.get('verb'): f"{w} is held twice over overlapping times, here "
                                                                      f"and at {w1}: `{v}` is exclusive in this garden "
                                                                      f"(VOCAB.md `exclusive`) — one being, once")

    def _overlaps(self, spans, says, distinct=False):
        for w, lst in sorted(spans.items()):
            lst.sort(key=lambda e: e[0])
            for j in range(len(lst)):
                for k in range(j + 1, len(lst)):
                    (l1, h1), w1, o1 = lst[j]
                    (l2, h2), w2, o2 = lst[k]
                    if l2 < h1 and l1 < h2 and not (distinct and o1 == o2):
                        self.err('room', w2, says(w, w1, w2))

    def vacancy(self):
        """Each row a garden adds is used, or says why it is vacant."""
        leaves, units, kinds, verbs, spaces = set(), set(), set(), set(), set()

        def walk(x):
            if isinstance(x, dict):
                if set(x) == {'count', 'unit'}:
                    units.add(x['unit'])
                if isinstance(x.get('someone'), str):
                    kinds.add(x['someone'])
                for v in x.values():
                    walk(v)
            elif isinstance(x, list):
                for v in x:
                    walk(v)
            elif isinstance(x, str):
                leaves.add(x)
        for b in self.G.beans.values():
            kinds.add(b.kind)
            walk(b.header.get('details'))             # what fits no verb yet uses a row as well
            for _i, verb, r in b.items:
                verbs.add(verb)
                walk(r)
                if verb == 'name' and isinstance(r.get('by'), str):
                    spaces.add(r['by'])
        levels = {row.get('level') for row in self.L.kinds.values()} | {s.get('at') for row in self.L.levels.values()
                                                                         for s in listed(row.get('stands'))
                                                                         if isinstance(s, dict)} | leaves
        used = {'kinds': kinds, 'levels': levels, 'verbs': verbs | {x.get('verb') for x in self.L.exclusive},
                'namespaces': spaces, 'units': units}
        for key, name, row in self.L.garden_rows:
            if row.get('vacant'):
                continue
            hit = name.split(':', 1)[1] in leaves if key == 'tables' else name in used[key] or \
                (key == 'units' and (row.get('name') in leaves or name in leaves))     # a unit, by its code or its name
            if not hit:
                self.err('vacancy', f"VOCAB.md {key}", f"`{name}` is a row this garden added, and nothing uses it: use "
                                                       f"it in the commit that adds it, or say why it is vacant "
                                                       f"(`vacant: <why>`)")

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
        self.text_and_gardener()
        self.cycles()
        self.gardens()
        self.grants()
        self.consent()
        self.harm()
        self.room()
        self.vacancy()
        return self.out


def judge(law, garden):
    """[(rule, where, message)] for `garden` under `law`: the law's own problems first, then the garden's."""
    return list(law.problems()) + Judge(law, garden).run()
