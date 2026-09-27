#!/usr/bin/env python3
"""dmcatalog — the catalogue of the language: every part, how the parts relate, and what each is held to.

    python3 bin/dmcatalog.py                   # the catalogue: each file under the layer that holds it, then the law
    python3 bin/dmcatalog.py --part <name>     # one part: what it holds, its relations both ways, its checklists
    python3 bin/dmcatalog.py --findings        # the findings, every one
    python3 bin/dmcatalog.py --json            # the whole map, sorted, for a tool: parts, relations, findings

(`python` on Windows.) GENERATED, NEVER KEPT. Every line is read from the sources each time it is asked, and nothing is
restated here: the law's front matter through bin/dmparse.py, the layer map and what a release keeps through
bin/dmpass.py, an attribute's domain through bin/dmform.py, the reasons through bin/dmwhy.py, and the rules as
bin/dmrules.py prints them. So the catalogue of a release cannot disagree with the release, and run again after a
change it maps the change.

THE PARTS are the items of the law — each term (the law's own and its profiles'), each registry (a list of the law's
front matter), each section (a mapping of it), each profile and each layer — and each file of the tree. What a part
holds sits inside its entry, never as a part of its own: a term's attributes, a registry's rows, a tool's functions, a
suite's checks, a document's headings. The layers are the one registry whose rows are parts, because they are the map's
own regions: every file is held by one, or by none, and says which.

THE RELATIONS, each read where it is written:

    imports    file → file       an import, or a module loaded from its path (a directory of plugins, each of them)
    runs       file → file       a real process: a subprocess call, or a call to a function of the same file that
                                 makes one, read from the syntax tree — a help text naming a tool runs nothing. A
                                 hook, a shell script and a workflow run what their lines run
    mentions   file → law item   a term, a registry or a section named whole in backticks or quotes; a `<name>` profile
    names      file → file       a document, a page or a suite naming a file by its path, or a tool by its name
    explains   file → law item   a reason, keyed by the path of what it explains
    holds      layer → file      the law's `layers`
    uses       term → law item   an attribute's domain: a registry, an aspect, a value type, a form, another term
    covers     suite → file      a suite importing, running or loading a tool;  suite → term  a check naming it
    states     document → term   the term written as a key at the head of a line of an example block
    ships      profile → file    the files of its asset, `assets/<profile>/`

THE CHECKLISTS of a part: the rules bin/dmrules.py prints for it (a term's own block; for a registry or a section, the
sections of the rules whose heading names it and the lines naming it in backticks; the core grammar is the gate's own),
the items of CHECKLIST.md that name it, and the checks of the suites whose names name it.

THE FINDINGS are candidates for a person to judge, never verdicts: a law item that nothing references; a tool that no
suite imports, runs or names; one domain taken under different attribute names whose meanings share their words; a
sibling whose shape differs from the rest of its group (the terms of one tier or profile, the rows of one registry); a
name the law gives several items; a file that lists the beans itself — a call that reads a directory of beans, one
finding a call — instead of reading them through bin/dmreckon.py.

IN A GARDEN it maps the garden's copy of the language: the law, and the files the release keeps (`seed/LANGUAGE`). The
garden's own files are the garden's, and no part of the language.

It writes nothing, and opens no network path.
"""
import ast, html, json, os, re, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse          # the one loader, and UTF-8 streams on every platform
import dmform           # an attribute's domain, read as the gate reads it
import dmpass           # the layer map, and what a release keeps
import dmwhy            # the one reader of the reasons

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAW, CHECKLIST, RULES = 'seed/std-vocab.md', 'CHECKLIST.md', 'bin/dmrules.py'
LAW_KINDS = ('term', 'registry', 'section', 'profile', 'layer')
RELATIONS = ('imports', 'runs', 'mentions', 'names', 'explains', 'holds', 'uses', 'covers', 'states', 'ships')

# A FILE'S KIND is this catalogue's word for what the file is, read from its path; where it SITS is the law's `layers`.
# The first pattern that matches names it, `*` crossing `/` as the layer map matches.
KINDS = ((LAW, 'law'), ('bin/hooks/*', 'hook'), ('bin/*.py', 'tool'), ('bin/*.sh', 'tool'), ('seed/germinate.*', 'tool'),
         ('assets/*/bin/*', 'tool'), ('assets/*/lib/*', 'module'), ('assets/*/templates/*', 'template'),
         ('test/*.py', 'suite'), ('test/*', 'fixture'), ('seed/knowledge/*.md', 'document'),
         ('seed/knowledge/*', 'knowledge table'),
         ('seed/*.template', 'template'), ('seed/LICENSE*', 'licence'), ('LICENSE*', 'licence'),
         ('site/*.html', 'page'), ('site/*.py', 'tool'), ('site/*', 'site asset'),
         ('.github/workflows/*', 'workflow'), ('.github/*', 'form'), ('*.md', 'document'), ('*', 'other'))
# What a document, a page or a suite may name a file by: its path, with one of these endings.
_PATHY = re.compile(r"(?<![\w$/.-])((?:[\w-]+/)*[\w.-]+\.(?:py|sh|md|tsv|yaml|yml|json|html|toml|txt|js|template))\b")
_TOKEN = re.compile(r"[\w.-]+(?:/[\w.-]+)*\.(?:py|sh)\b")      # what a command line runs
_STOP = frozenset('the and for with that this its are not any one each from which what where when their have has was was '
                  'but can may must only also into than then them they there these those who whom whose been being '
                  'more most other some such very own same how why all nor out off per via upon onto over under'.split())
CLOSE = 0.34            # two meanings that share at least this share of their words are close (Jaccard, words of 3+)
RARE, COMMON = 0.1, 0.8  # a sibling is odd holding a key at most RARE of its group hold, or lacking one COMMON hold


def _read(root, path):
    try:
        with open(os.path.join(root, *path.split('/')), encoding='utf-8') as fh:
            return fh.read()
    except (OSError, UnicodeDecodeError):
        return None


def _kind(path):
    return next(k for p, k in KINDS if dmpass.matches(p, path))


def _words(text):
    return {w for w in re.findall(r'[a-z]{3,}', str(text or '').lower()) if w not in _STOP}


def _head(span):
    """The law name a code span begins with, when the span is that name alone or the name and what follows it on a
    path (`name:`, `name.attr`, `name[row]`)."""
    m = re.match(r'[a-z][a-z0-9_]*', span)
    if m and (m.end() == len(span) or span[m.end()] in ':.['):
        return m.group(0)
    return None


def law_names_in(text, names, profiles=()):
    """{law name} a text names: whole in backticks, in quotes or in <code>, or as the head of a path written so."""
    out = set()
    for m in re.finditer(r'`([^`\n]+)`|<code>([^<]+)</code>', text):
        h = _head(html.unescape((m.group(1) or m.group(2) or '').strip()))
        if h in names:
            out.add(h)
    for m in re.finditer(r"'([a-z][a-z0-9_]*)'|\"([a-z][a-z0-9_]*)\"", text):
        if (m.group(1) or m.group(2)) in names:
            out.add(m.group(1) or m.group(2))
    for p in profiles:
        if re.search(r"`%s` profile|profile `%s`" % (re.escape(p), re.escape(p)), text):
            out.add('profile:' + p)
    return out


# ============================================================================ a Python file, read from its syntax tree
_LISTERS = {('os', 'listdir'), ('os', 'scandir'), ('os', 'walk'), ('glob', 'glob'), ('glob', 'iglob')}
_PROCESS = {('os', 'system'), ('os', 'popen'), ('os', 'execv'), ('os', 'execvp'), ('os', 'execl'), ('os', 'execlp')}
_SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_PYTHON = re.compile(r'(?:^|[\s/\\])(?:python[0-9.]*|py)(?:\.exe)?(?:$|\s)')     # a Python, as a command names one


PY = '<python>'          # the name an expression is given that holds `sys.executable`: the Python running it


def _strings(node):
    """(the string constants of an expression, the names it reads — `sys.executable` read as PY)."""
    s, n = set(), set()
    for x in ast.walk(node):
        if isinstance(x, ast.Constant) and isinstance(x.value, str):
            s.add(x.value)
        elif isinstance(x, ast.Name):
            n.add(x.id)
        elif isinstance(x, ast.Attribute) and x.attr == 'executable' and isinstance(x.value, ast.Name) \
                and x.value.id == 'sys':
            n.add(PY)
    return s, n


def _own(node):
    """The nodes of one scope: everything under it but what a function or lambda defined inside holds."""
    todo = list(ast.iter_child_nodes(node))
    while todo:
        x = todo.pop()
        yield x
        if not isinstance(x, _SCOPES):
            todo.extend(ast.iter_child_nodes(x))


def _assigned(nodes):
    """{name: [the expressions assigned it]}: its assignments and loops, among the nodes of a scope."""
    env = {}
    for x in nodes:
        if isinstance(x, ast.Assign):
            pairs = [(t, x.value) for t in x.targets]
        elif isinstance(x, (ast.AnnAssign, ast.AugAssign)) and x.value is not None:
            pairs = [(x.target, x.value)]
        elif isinstance(x, (ast.For, ast.AsyncFor, ast.comprehension)):
            pairs = [(x.target, x.iter)]
        elif isinstance(x, ast.NamedExpr):
            pairs = [(x.target, x.value)]
        else:
            continue
        for t, v in pairs:
            for nm in ast.walk(t):
                if isinstance(nm, ast.Name):
                    env.setdefault(nm.id, []).append(v)
    return env


class _Env:
    """A scope's assignments, and the scope it sits in: a name is read in the innermost scope that assigns it and in
    every one around it, since which of them a line reads is a question of the order it runs in, which this never runs.
    An expression is read only when a name is asked for, and once."""
    __slots__ = ('own', 'up', 'memo')

    def __init__(self, own, up, memo):
        self.own, self.up, self.memo = own, up, memo

    def get(self, name):
        s, n, e = set(), set(), self
        while e is not None:
            for v in e.own.get(name, ()):
                got = e.memo.get(id(v))
                if got is None:
                    got = e.memo[id(v)] = _strings(v)
                s |= got[0]
                n |= got[1]
            e = e.up
        return s, n


class Py:
    """What one Python file does, read from its syntax tree and never run: what it imports and from where, what it
    loads by path, the commands it runs, the calls that list a directory of beans, and a suite's checks. A name is
    followed to what its scope, or a scope around it, assigns it, so `os.path.join(ROOT, 'bin', 'dmcheck.py')` named
    once and run later is still read."""

    def __init__(self, text):
        self.tree = ast.parse(text)
        self.doc = (ast.get_docstring(self.tree) or '').strip().split('\n')[0]
        self.defs = sorted(x.name for x in self.tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)))
        self.classes = sorted(x.name for x in self.tree.body if isinstance(x, ast.ClassDef))
        self.imports, self.loads, self.runs, self.unresolved, self.checks = [], [], [], [], []
        self.walks, self.paths, self._memo = set(), [], {}
        self.scopes = list(self._scopes(self.tree, None))
        mods, funcs = {'subprocess'}, set()
        for _node, _env, nodes in self.scopes:
            for x in nodes:
                if isinstance(x, ast.Import):
                    for a in x.names:
                        self.imports.append((a.name, (), x.lineno))
                        if a.name == 'subprocess' and a.asname:
                            mods.add(a.asname)
                elif isinstance(x, ast.ImportFrom) and x.module and not x.level:
                    self.imports.append((x.module, tuple(a.name for a in x.names), x.lineno))
                    if x.module == 'subprocess':
                        funcs.update(a.asname or a.name for a in x.names)
        self.imports.sort(key=lambda i: i[2])
        runners = self._runners(mods, funcs)
        for node, env, nodes in self.scopes:
            for c in (x for x in nodes if isinstance(x, ast.Call)):
                self._call(c, env, mods, funcs, runners, node)

    def _scopes(self, node, up):
        nodes = list(_own(node))
        env = _Env(_assigned(nodes), up, self._memo)
        yield node, env, nodes
        for x in nodes:
            if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield from self._scopes(x, env)

    @staticmethod
    def resolve(strings, names, env, rounds=6):
        """Every string an expression can hold, its names followed through the scopes' assignments."""
        out, seen, todo = set(strings), set(), set(names)
        for _ in range(rounds):
            nxt = set()
            for n in todo - seen:
                seen.add(n)
                s, more = env.get(n)
                out.update(s)
                nxt.update(more)
            todo = nxt - seen
            if not todo:
                break
        return out

    @staticmethod
    def _reach(names, env, rounds=6):
        seen, todo = set(), set(names)
        for _ in range(rounds):
            seen |= todo
            todo = {m for n in todo for m in env.get(n)[1]} - seen
            if not todo:
                break
        return seen

    @staticmethod
    def _dotted(f):
        return (f.value.id, f.attr) if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) else None

    def _is_process(self, c, mods, funcs):
        d = self._dotted(c.func)
        return bool(d and (d[0] in mods or d in _PROCESS)) or (isinstance(c.func, ast.Name) and c.func.id in funcs)

    def _runners(self, mods, funcs):
        """The functions of this file that start a process with what they are given, followed to a fixed point: a
        function that hands its argument to such a function is one too."""
        runners, grew = set(), True
        while grew:
            grew = False
            for node, env, nodes in self.scopes:
                if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or node.name in runners:
                    continue
                params = self._params(node)
                for c in (x for x in nodes if isinstance(x, ast.Call)):
                    if not (self._is_process(c, mods, funcs) or self._callee(c) in runners):
                        continue
                    n = set()
                    for arg in list(c.args) + [k.value for k in c.keywords if k.arg in ('args', 'cmd')]:
                        n |= _strings(arg)[1]
                    if self._reach(n, env) & params:
                        runners.add(node.name)
                        grew = True
                        break
        return runners

    def _python_first(self, c, env, direct=True):
        """Whether a command's first word is a Python: `sys.executable`, a name that holds it, or — in a call that starts
        the process itself, whose first word is the command's — `python3`."""
        x = c.args[0] if c.args else None
        while isinstance(x, (ast.List, ast.Tuple, ast.BinOp)):
            x = x.left if isinstance(x, ast.BinOp) else (x.elts[0] if x.elts else None)
        if isinstance(x, ast.Attribute):
            return x.attr == 'executable'
        if isinstance(x, ast.Name):
            return PY in self._reach({x.id}, env) or (direct and any(_PYTHON.search(v) for v in env.get(x.id)[0]))
        return direct and isinstance(x, ast.Constant) and isinstance(x.value, str) and bool(_PYTHON.search(x.value))

    @staticmethod
    def _callee(c):
        return c.func.id if isinstance(c.func, ast.Name) else c.func.attr if isinstance(c.func, ast.Attribute) else None

    @staticmethod
    def _params(node):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return set()
        a = node.args
        return ({p.arg for p in a.posonlyargs + a.args + a.kwonlyargs} | {p.arg for p in (a.vararg, a.kwarg) if p}) \
            - {'self', 'cls'}

    def _call(self, c, env, mods, funcs, runners, scope):
        d = self._dotted(c.func)
        callee = self._callee(c)
        attr = isinstance(c.func, ast.Attribute)
        runs = self._is_process(c, mods, funcs) or callee in runners
        load = callee == 'spec_from_file_location' and len(c.args) >= 2
        path = attr and callee in ('insert', 'append') and isinstance(c.func.value, ast.Attribute) \
            and c.func.value.attr == 'path' and isinstance(c.func.value.value, ast.Name) and c.func.value.value.id == 'sys'
        lists = d in _LISTERS or (attr and callee in ('iterdir', 'glob', 'rglob') and not (d and d[0] == 'glob'))
        if isinstance(c.func, ast.Name) and c.func.id == 'check' and c.args:
            self.checks.append((self.render(c.args[0]), c.lineno))
        if not (runs or load or path or lists):
            return
        s, n = set(), set()
        for a in list(c.args) + [k.value for k in c.keywords if k.arg in ('args', 'cmd', 'path', 'location')]:
            s2, n2 = _strings(a)
            s |= s2
            n |= n2
        if load:
            s2, n2 = _strings(c.args[1])
            self.loads.append((self.resolve(s2, n2, env), c.lineno))
        elif runs:
            got = self.resolve(s, n, env)
            self.runs.append((got, c.lineno))
            inner = scope.name in runners and self._reach(n, env) & self._params(scope) if hasattr(scope, 'name') else False
            if not inner and not any(_TOKEN.search(x) for x in got) and self._python_first(c, env, callee not in runners):
                self.unresolved.append(c.lineno)       # a Python runs, and which file it runs is not written here
            # git's own list of the beans
            if {'ls-files', 'ls-tree'} & got and any(re.search(r'^(?:beans|mappings)(?:/|$)', x) for x in got):
                self.walks.add((c.lineno, c.col_offset))
        if path:            # where its imports are looked for: a directory put on sys.path
            self.paths.append(self.resolve(s, n, env))
        if lists:           # a listing of the beans: a call that reads a directory whose path names `beans` or `mappings`
            r = _strings(c.func.value) if attr and d not in _LISTERS else (set(), set())
            where = self.resolve(s | r[0], n | r[1], env)
            if any(re.search(r'(?:^|[/\\])(?:beans|mappings)(?:$|[/\\])', x) for x in where):
                self.walks.add((c.lineno, c.col_offset))

    @classmethod
    def render(cls, node):
        """A check's name as its source writes it: the words, and `{…}` for what an f-string fills in."""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            return ''.join(v.value if isinstance(v, ast.Constant) else '{' + ast.unparse(v.value) + '}'
                           for v in node.values)
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Mod)):
            return cls.render(node.left) + ('' if isinstance(node.op, ast.Add) else ' % ') + cls.render(node.right)
        return ast.unparse(node)


# ============================================================================ the catalogue
class Catalogue:
    def __init__(self, root=ROOT):
        self.root = root
        text = _read(root, LAW)
        law = dmparse.loads(dmparse.split_front_matter(text)[0]) if text else None
        if not isinstance(law, dict):
            raise ValueError(f"{LAW} is not there or its front matter does not read: there is no catalogue without the law")
        self.law, self.version = law, str(law.get('version'))
        self.map = dmpass.Map.here(root)
        self.garden = os.path.isfile(os.path.join(root, 'GARDEN.md'))
        self.files = [f for f in self.map.files if not self.garden or self.map.keeper_of(f) == 'release']
        self.parts, self.edges = {}, set()
        self.release = self._release()
        self._law_parts()
        self._file_parts()
        self._uses()
        self._explains()
        self._checklists()
        self.findings = self._findings()

    def _release(self):
        """The release this tree is. In a garden, the one its GARDEN.md says it adopted (`daftar_release`, which germination
        and bin/dmupgrade.py write), as the gate reads it: a garden's own history carries no daftar tag, and describing it
        named the garden's own commits. In the release's repository, the tag git describes."""
        g = _read(self.root, 'GARDEN.md') if self.garden else None
        fm = dmparse.loads(dmparse.split_front_matter(g)[0] or '') if g else None
        if isinstance(fm, dict) and fm.get('daftar_release'):
            return str(fm['daftar_release'])
        r = subprocess.run(['git', '-C', self.root, 'describe', '--tags', '--always', '--dirty'], capture_output=True,
                           text=True, encoding='utf-8', errors='replace')
        return r.stdout.strip() or 'untagged'

    def part(self, pid, kind, name, **contents):
        self.parts[pid] = {'kind': kind, 'name': name, 'contents': contents,
                           'checklists': {'rules': [], 'checklist': [], 'checks': []}}
        return self.parts[pid]

    def edge(self, rel, a, b, via=None):
        if a in self.parts and b in self.parts and a != b:
            self.edges.add((rel, a, b, via or ''))

    # -------------------------------------------------------------- the law's items
    def _law_parts(self):
        law = self.law
        self.terms = {}
        for t in law.get('terms') or []:
            if isinstance(t, dict) and isinstance(t.get('term'), str):
                self.terms.setdefault(t['term'], (t, 'tier0'))
        self.profiles = {str(p): r for p, r in (law.get('profiles') or {}).items() if isinstance(r, dict)}
        for p, r in self.profiles.items():
            for t in r.get('terms') or []:
                if isinstance(t, dict) and isinstance(t.get('term'), str):
                    self.terms.setdefault(t['term'], (t, 'profile:' + p))
        for name, (t, tier) in self.terms.items():
            s = t.get('schema') if isinstance(t.get('schema'), dict) else {}
            self.part('term:' + name, 'term', name, tier=tier, meaning=t.get('meaning'), shape=s.get('shape'),
                      keys=sorted(str(k) for k in t), attributes={}, merge=t.get('merge'),
                      context_keys=t.get('context_keys'))
        self.registries = sorted(k for k, v in law.items() if isinstance(v, list) and k != 'terms')
        self.sections = sorted(k for k, v in law.items() if isinstance(v, dict) and k != 'profiles')
        for k in self.registries:
            rows = law[k]
            dicts = [r for r in rows if isinstance(r, dict)]
            key = next(iter(dicts[0]), None) if dicts else None
            fields = {}
            for r in dicts:
                for f in r:
                    fields[str(f)] = fields.get(str(f), 0) + 1
            self.part('registry:' + k, 'registry', k, rows=len(rows), key=key,
                      row_names=[str(r.get(key)) for r in dicts if key in r] if dicts else [str(x) for x in rows],
                      fields=fields)
        for k in self.sections:
            self.part('section:' + k, 'section', k, keys=[str(x) for x in law[k]])
        for p, r in self.profiles.items():
            self.part('profile:' + p, 'profile', p, meaning=r.get('meaning'),
                      terms=[str(t.get('term')) for t in r.get('terms') or [] if isinstance(t, dict)],
                      vacancies=len(r.get('vacancies') or []), asset=f'assets/{p}/')
        for r in self.map.rows:
            self.part('layer:' + r['layer'], 'layer', r['layer'], files=r.get('files', True), beneath=r.get('beneath'),
                      holds=r.get('holds') or [], meaning=r.get('meaning'))
        # the names a file may mention: a term's, a registry's, a section's
        # the names a file may mention, each with every item the law gives it: a text naming `roles` names the term and
        # the registry alike, and nothing in it says which
        self.names = {}
        for pid in ['term:' + n for n in self.terms] + ['registry:' + k for k in self.registries] \
                + ['section:' + k for k in self.sections]:
            self.names.setdefault(pid.split(':', 1)[1], []).append(pid)

    # -------------------------------------------------------------- the files
    def _file_parts(self):
        by_layer, self.unplaced = self.map.placed()
        where = {f: l for l, fs in by_layer.items() for f in fs}
        self.by_base = {}
        for f in self.files:
            self.by_base.setdefault(f.rsplit('/', 1)[-1], []).append(f)
        self.libs = sorted({x.split('/lib/')[0] + '/lib' for x in self.files if re.match(r'assets/[^/]+/lib/', x)})
        self.pydirs = sorted({x.rsplit('/', 1)[0] if '/' in x else '' for x in self.files if x.endswith('.py')})
        self.py = {}
        for f in self.files:
            text = _read(self.root, f)
            kind = _kind(f)
            c = {'lines': text.count('\n') + (0 if text.endswith('\n') or not text else 1)} if text is not None else \
                {'bytes': os.path.getsize(os.path.join(self.root, *f.split('/')))}
            layer = where.get(f)
            self.part(f, kind, f, layer=layer, kept=self.map.keeper_of(f), **c)
            if layer:
                self.edge('holds', 'layer:' + layer, f)
            m = re.match(r'assets/([^/]+)/', f)
            if m and m.group(1) in self.profiles:
                self.edge('ships', 'profile:' + m.group(1), f)
            if text is None:
                continue
            self.parts[f]['text'] = text
        self.unplaced = [f for f in self.unplaced if f in self.parts]
        for f in self.files:
            text = self.parts[f].pop('text', None)
            if text is None:
                continue
            c = self.parts[f]['contents']
            if f.endswith('.py'):
                self._python(f, text, c)
            elif f.endswith('.md'):
                c['headings'] = [h.strip() for h in re.findall(r'(?m)^#{1,3} (.+)$', _unfenced(text))]
                self._document(f, text)
            elif f.endswith('.html'):
                t = re.search(r'<title>(.*?)</title>', text, re.S)
                c['title'] = html.unescape(t.group(1).strip()) if t else None
                self._document(f, text)
            elif f.endswith('.tsv'):
                rows = [l for l in text.split('\n') if l and not l.startswith('#')]
                c['columns'], c['rows'] = (rows[0].split('\t') if rows else []), max(len(rows) - 1, 0)
            elif self.parts[f]['kind'] in ('hook', 'workflow') or f.endswith('.sh'):
                self._script(f, text)
            if not f.endswith('.py') and self.parts[f]['kind'] not in ('knowledge table', 'licence', 'fixture'):
                for n in law_names_in(text, self.names, self.profiles):
                    for pid in self.names.get(n, [n]):
                        self.edge('mentions', f, pid)
            if self.parts[f]['kind'] in ('document', 'page', 'form', 'workflow', 'template', 'other') \
                    and not f.endswith('.py'):
                self._names(f, text)

    def file_of(self, token, near, context=()):
        """The file of this tree a token names: its path, or the one file of that name — of several, the one whose
        directories the command names too, else the one beside the file that names it."""
        token = token.strip().lstrip('./') if not token.startswith('../') else token
        if token in self.parts and '/' in token or token in self.files:
            return token
        base = token.rsplit('/', 1)[-1]
        cands = self.by_base.get(base, [])
        if '/' in token:
            cands = [c for c in cands if c.endswith('/' + token) or c == token] or cands
        if len(cands) == 1:
            return cands[0]
        fit = [c for c in cands if all(seg in context for seg in c.split('/')[:-1])]
        if len(fit) == 1:
            return fit[0]
        near_ = [c for c in cands if c.rsplit('/', 1)[0] == near]
        return near_[0] if len(near_) == 1 else (cands[0] if cands and any(c.count('/') == 0 for c in cands[:1])
                                                  and token == base else None)

    def _tokens(self, strings):
        out = set()
        for s in strings:
            if _TOKEN.fullmatch(s.strip()):
                out.add(s.strip())
            out.update(m.group(0) for m in _TOKEN.finditer(s))
        return out

    def _python(self, f, text, c):
        try:
            p = Py(text)
        except SyntaxError as e:
            c['unparsed'] = f"line {e.lineno}: {e.msg}"
            return
        self.py[f] = p
        here = f.rsplit('/', 1)[0] if '/' in f else ''
        c.update(summary=p.doc, functions=p.defs, classes=p.classes)
        dirs = [d for got in reversed(p.paths) for d in self._dirs(got, here)]
        for mod, names, _line in p.imports:
            for m in [mod + '.' + n for n in names] + [mod]:
                t = self._module(m, dirs + [here], f)
                if t:
                    self.edge('imports', f, t)
                    if m != mod:
                        continue
                    break
        for got, line in p.loads:
            hit = [self.file_of(t, here, got) for t in self._tokens(got)]
            hit = [h for h in hit if h]
            if not hit:          # a directory of plugins: every module in the directory the path names
                dirs = [d for d in (here + '/' + s if here else s for s in got) if any(
                    x.startswith(d + '/') and x.endswith('.py') and x.count('/') == d.count('/') + 1 for x in self.files)]
                hit = [x for d in dirs for x in self.files
                       if x.startswith(d + '/') and x.endswith('.py') and x.count('/') == d.count('/') + 1]
            for h in hit:
                self.edge('imports', f, h, 'loaded by path')
        ran = set()
        for got, line in p.runs:
            for t in self._tokens(got):
                h = self.file_of(t, here, {seg for s in got for seg in re.split(r'[/\\ ]', s)})
                if h:
                    self.edge('runs', f, h)
                    ran.add(h)
        if p.unresolved:
            c['runs_unnamed'] = sorted(set(p.unresolved))
        if p.walks:
            c['bean_walks'] = sorted(line for line, _col in p.walks)      # one line per call
        if self.parts[f]['kind'] == 'suite':
            c['checks'] = len(p.checks)
            for m in [x for x in self.edges if x[1] == f and x[0] in ('imports', 'runs')]:
                if self.parts[m[2]]['kind'] in ('tool', 'module', 'hook'):
                    self.edge('covers', f, m[2], m[0])
            self._names(f, text)
            for name, line in p.checks:
                for n in law_names_in(name, self.terms):
                    self.edge('covers', f, 'term:' + n, 'a check names it')
        for n in law_names_in(text, self.names, self.profiles):
            for pid in self.names.get(n, [n]):
                self.edge('mentions', f, pid)

    def _module(self, mod, first, importer):
        """The file an import names: in a directory the importer put on sys.path, beside it, among the tools, or in an
        asset's library — the first that holds it, and never the importer itself; else none of this tree's."""
        rel = mod.replace('.', '/')
        for d in first + ['bin'] + self.libs:
            for cand in (f'{d}/{rel}.py' if d else f'{rel}.py', f'{d}/{rel}/__init__.py' if d else f'{rel}/__init__.py'):
                if cand in self.parts and cand != importer:
                    return cand
        return None

    def _dirs(self, got, here):
        """The directories of this tree a sys.path entry can be: one whose every segment its path names, or the
        importer's own (`os.path.dirname(__file__)`)."""
        out = [d for d in self.pydirs if d and set(d.split('/')) <= got]
        return out or ([here] if not got or got <= {'__file__'} else [])

    def _script(self, f, text):
        """What a hook, a shell script or a workflow runs: the files its lines name — never in a comment, and never in
        what it says (`echo`, `printf`), which tells a person what to run rather than running it."""
        here = f.rsplit('/', 1)[0] if '/' in f else ''
        for line in text.split('\n'):
            if line.lstrip().startswith('#'):
                continue
            line = re.sub(r'\b(?:echo|printf)\s+(?:"[^"]*"|\'[^\']*\'|[^;&|]*)', '', line)
            for t in self._tokens([line]):
                h = self.file_of(t, here, set(re.split(r'[/\\ "$]', line)))
                if h:
                    self.edge('runs', f, h)

    def _names(self, f, text):
        here = f.rsplit('/', 1)[0] if '/' in f else ''
        for m in _PATHY.finditer(text):
            h = self.file_of(m.group(1), here)
            if h:
                self.edge('names', f, h)
        for m in re.finditer(r'\b(dm[a-z]+)\b', text):
            for h in self.by_base.get(m.group(1) + '.py', []):
                if self.parts[h]['kind'] == 'tool':
                    self.edge('names', f, h)

    def _document(self, f, text):
        """The terms a document or a page states: written as a key at the head of a line of an example block."""
        blocks = [m.group(2) for m in re.finditer(r'(?ms)^(`{3,})[^\n]*\n(.*?)^\1[ \t]*$', text)] if f.endswith('.md') \
            else [html.unescape(re.sub(r'<[^>]+>', '', m.group(1))) for m in re.finditer(r'(?s)<pre[^>]*>(.*?)</pre>', text)]
        for b in blocks:
            for k in re.findall(r'(?m)^([a-z][a-z0-9_]*):(?:\s|$)', b):
                if k in self.terms:
                    self.edge('states', f, 'term:' + k)

    # -------------------------------------------------------------- what a term's attributes take their values in
    def _uses(self):
        terms = [t for t, _tier in self.terms.values()]
        self.sense = dmform.sense_uses(terms, self.law)
        for name, uses in self.sense.items():
            for domain, where, facet, rule in uses:
                term, _, inner = where.partition('.')
                path = (inner + '.' if inner else '') + name
                if 'term:' + term not in self.parts:
                    continue
                label = self._label(domain, facet, rule, self._record(term, path))
                self.parts['term:' + term]['contents']['attributes'][path] = label
                tgt, detail = self._target(facet, rule)
                self.edge('uses', 'term:' + term, tgt, path + (' in ' + detail if detail else ''))
        for name, (t, _tier) in self.terms.items():
            s = t.get('schema') if isinstance(t.get('schema'), dict) else {}
            for k in ('values_from', 'key_form'):
                v = s.get(k)
                if isinstance(v, str):
                    v = v[len('values_from:'):] if v.startswith('values_from:') else v
                    m = re.match(r'registry:([a-z_0-9]+)', v)
                    self.edge('uses', 'term:' + name, 'registry:' + m.group(1) if m else 'term:' + v, k)
            v = s.get('value_in_registry')
            if isinstance(v, dict):
                self.edge('uses', 'term:' + name, 'registry:' + str(v.get('registry')), 'value_in_registry')

    def _record(self, term, path):
        t = self.terms[term][0]
        attrs, rec = ((t.get('schema') or {}).get('attrs')), None
        for seg in path.split('.'):
            rec = attrs.get(seg) if isinstance(attrs, dict) else None
            if not isinstance(rec, dict):
                return None
            d = rec.get('in')
            attrs = d.get('entries') if isinstance(d, dict) else None
        return rec

    @staticmethod
    def _label(domain, facet, rule, rec):
        """An attribute's domain in words a reader can follow: the gate's sense of it (bin/dmform.py), with the aspect
        or the closed list named, and a registry or a system another attribute names said so."""
        if facet == 'aspect':
            return 'aspect:' + str(rule.get('aspect'))
        if facet == 'values':
            return 'values:' + '|'.join(str(v) for v in rule)
        if facet == 'registry' and isinstance(rule, dict) and rule.get('registry_from'):
            return 'registry named by ' + str(rule['registry_from'])
        if facet == 'system_from' and isinstance(rule, dict):
            return f"a position in the system named by {rule.get('keyed_by')}"
        if facet is None:
            return dmform.domain_kind(rec.get('in') if isinstance(rec, dict) else None) or 'unknown'
        return str(domain)

    @staticmethod
    def _target(facet, rule):
        if facet == 'aspect':
            return 'registry:aspects', str(rule.get('aspect'))
        if facet == 'type':
            return 'registry:value_types', str(rule)
        if facet == 'registry' and isinstance(rule, dict) and rule.get('registry'):
            return 'registry:' + str(rule['registry']), None
        if facet == 'system_from' and isinstance(rule, dict):
            return 'registry:' + str(rule.get('registry')), None
        if facet == 'system':
            return 'registry:anchor_systems', str(rule)
        if facet == 'key_of':
            return 'term:' + str(rule), None
        if facet == 'quantity':
            return 'registry:quantities', str(rule)
        if facet in ('extent', 'recurrence'):
            return f'section:{facet}_form', None
        if facet == 'origin_of':
            return 'registry:acts', None
        if facet == 'bean_id' and isinstance(rule, dict) and rule.get('gene'):
            return 'registry:gene', ','.join(str(g) for g in rule['gene'])
        return None, None

    # -------------------------------------------------------------- the reasons
    def _explains(self):
        why = dmwhy.WHY and os.path.relpath(dmwhy.WHY, ROOT).replace(os.sep, '/')
        if self.root != ROOT or not why or why not in self.parts:
            return
        for key in dmwhy.rationale():
            if key.startswith('doc:'):
                self.edge('explains', why, key[4:].split('#', 1)[0], key)
                continue
            segs = dmwhy._SEG.findall(key)          # the reasons' own grammar of a path, read where it is kept
            head = segs[0][0] if segs and segs[0][0] else None
            nxt = segs[1] if len(segs) > 1 else ('', '')
            if head == 'terms' and nxt[1]:
                tgt = 'term:' + nxt[1]
            elif head == 'profiles' and nxt[0]:
                t = next((i for n, i in segs[2:4] if i), None)
                tgt = 'term:' + t if t and len(segs) > 3 and segs[2][0] == 'terms' else 'profile:' + nxt[0]
            elif head == 'layers' and nxt[1] and 'layer:' + nxt[1] in self.parts:
                tgt = 'layer:' + nxt[1]
            else:
                tgt = ('registry:' if head in self.registries else 'section:') + head \
                    if head in self.registries or head in self.sections else None
            if tgt:
                self.edge('explains', why, tgt, key)

    # -------------------------------------------------------------- what each part is held to
    def _checklists(self):
        # the rules, as bin/dmrules.py prints them for every profile the law offers
        r = subprocess.run([sys.executable, os.path.join(self.root, *RULES.split('/')), '--terms', '--core', '--every-profile'],
                           capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=self.root)
        lines, sections, title = r.stdout.split('\n'), [], None
        for i, ln in enumerate(lines):
            if i + 1 < len(lines) and lines[i + 1].startswith('─') and ln.strip():
                title = ln.strip()
                sections.append((title, []))
            elif title and ln.strip() and not ln.startswith('─'):
                sections[-1][1].append(ln.rstrip())
        for title, body in sections:
            if title.startswith('TERMS'):
                cur = None
                for ln in body:
                    m = re.match(r'^  (\S+)\s+\[[^\]]*\]\s*(.*)$', ln)
                    if m:
                        cur = 'term:' + m.group(1) if 'term:' + m.group(1) in self.parts else None
                        if cur:
                            self._rule(cur, title, m.group(2))
                    elif cur and ln.startswith('    '):
                        self._rule(cur, title, ln.strip().lstrip('· '))
                continue
            if title.startswith('CORE'):
                for ln in body:
                    self._rule('bin/dmcheck.py', title, ln.strip().lstrip('· '))
                continue
            if title.startswith('NOT READ'):
                continue
            head = title.split(' — ')[0].lower()
            whole = [pid for pid in self._law_ids() if _named_in(self.parts[pid]['name'], head)]
            for ln in body:
                for pid in set(whole) | {pid for n in law_names_in(ln, self.names) for pid in self.names[n]}:
                    self._rule(pid, title, ln.strip().lstrip('· '))
        # the items of CHECKLIST.md
        text = _read(self.root, CHECKLIST) or ''
        part_letter, n, items = None, 0, []
        for ln in text.split('\n'):
            m = re.match(r'^## Part ([A-Z])\b', ln)
            if m:
                part_letter, n = m.group(1), 0
            elif part_letter and ln.startswith('- [ ] '):
                n += 1
                items.append([f'{part_letter}.{n}', ln[6:].strip()])
            elif items and part_letter and ln.startswith('  ') and ln.strip():
                items[-1][1] += ' ' + ln.strip()
            elif ln.startswith('#'):
                part_letter = part_letter if ln.startswith('### ') else None
        for item, words in items:
            for pid in self._named(words, CHECKLIST):
                self.parts[pid]['checklists']['checklist'].append({'item': item, 'text': words})
        # the checks of the suites
        for f, p in sorted(self.py.items()):
            if self.parts[f]['kind'] != 'suite':
                continue
            for name, line in sorted(p.checks, key=lambda x: x[1]):
                for pid in self._named(name, f):
                    self.parts[pid]['checklists']['checks'].append({'suite': f, 'line': line, 'check': name})

    def _law_ids(self):
        return [p for p, v in self.parts.items() if v['kind'] in ('registry', 'section', 'term')]

    def _rule(self, pid, section, line):
        if pid in self.parts and line:
            self.parts[pid]['checklists']['rules'].append({'section': section.split(' — ')[0], 'rule': line})

    def _named(self, words, where):
        """The parts a line of prose names: a law item in backticks or quotes, a file by its path, a tool by its name."""
        out = {pid for n in law_names_in(words, self.names, self.profiles) for pid in self.names.get(n, [n])}
        here = where.rsplit('/', 1)[0] if '/' in where else ''
        for m in _PATHY.finditer(words):
            h = self.file_of(m.group(1), here)
            if h:
                out.add(h)
        for m in re.finditer(r'\b(dm[a-z]+)\b', words):
            out.update(h for h in self.by_base.get(m.group(1) + '.py', []) if self.parts[h]['kind'] == 'tool')
        return sorted(p for p in out if p in self.parts)

    # -------------------------------------------------------------- the findings
    def _findings(self):
        into = {}
        for rel, a, b, _via in self.edges:
            into.setdefault(b, set()).add((rel, a))
        # a law item nothing references: no tool, module, hook, suite or document mentions, states or covers it, and no
        # reason explains it — the law's own file, its journal and history, and the pages (printed from the law and the
        # tools, so they name every item by construction) are not counted
        quiet = {LAW} | {f for f in self.files if self.parts[f]['contents'].get('layer') in ('journal', 'history')}
        counted = {'tool', 'module', 'hook', 'suite', 'document', 'template', 'workflow', 'form'}
        unreferenced = []
        for pid, v in sorted(self.parts.items()):
            if v['kind'] not in ('term', 'registry', 'section', 'profile'):
                continue
            by = sorted({a for rel, a in into.get(pid, ()) if rel in ('mentions', 'states', 'covers', 'explains', 'names')
                         and a not in quiet and self.parts[a]['kind'] in counted})
            if not by:
                unreferenced.append({'part': pid})
        # a tool no suite imports, runs, loads or names
        named = {b for rel, a, b, _ in self.edges if rel in ('imports', 'runs', 'covers', 'names')
                 and self.parts[a]['kind'] == 'suite'}
        untested = [{'part': f} for f in sorted(self.files) if self.parts[f]['kind'] == 'tool' and f not in named]
        # one name the law gives several items: a text that names it cannot say which it means. A term named for the
        # registry whose rows it takes is one such (the senses' structural reading); a profile named for its main term is
        # another. Listed, since whether each is meant is a person's to say.
        shared = {}
        for pid, v in self.parts.items():
            if v['kind'] in ('term', 'registry', 'section', 'profile'):
                shared.setdefault(v['name'], []).append(pid)
        one_name = [{'name': n, 'parts': sorted(ps)} for n, ps in sorted(shared.items()) if len(ps) > 1]
        return {'unreferenced': unreferenced, 'untested_tools': untested, 'one_domain_many_names': self._close_names(),
                'odd_siblings': self._odd_siblings(), 'own_bean_walks': self._walks(), 'one_name_many_items': one_name}

    def _close_names(self):
        """One domain taken under different attribute names whose meanings share their words: a name for the same
        thing said twice, or two things one name could carry."""
        groups = {}
        for name, uses in self.sense.items():
            for domain, where, facet, rule in uses:
                if facet in (None, 'prose', 'entries'):
                    continue
                # grouped by the gate's sense of the domain (bin/dmform.py), finer where the sense leaves out what it
                # is a position in: the aspect, the closed list, the term whose keys, the quantity, the system, the gene
                key = 'values:' + '|'.join(sorted(str(v) for v in rule)) if facet == 'values' else \
                    f'{facet}:{rule.get("aspect")}' if facet == 'aspect' else \
                    f'{facet}:{rule}' if facet in ('key_of', 'quantity', 'system') else \
                    f'{facet}:' + ','.join(map(str, rule.get('gene') or [])) if facet == 'bean_id' and isinstance(rule, dict) \
                    else str(domain)
                term, _, inner = where.partition('.')
                rec = self._record(term, (inner + '.' if inner else '') + name) if term in self.terms else None
                groups.setdefault(key, {}).setdefault(name, []).append((where, (rec or {}).get('meaning') or ''))
        out = []
        for key, names in groups.items():
            ns = sorted(names)
            for i, a in enumerate(ns):
                for b in ns[i + 1:]:
                    best = (0.0, set())
                    for wa, ma in names[a]:
                        for wb, mb in names[b]:
                            x, y = _words(ma), _words(mb)
                            if x and y:
                                j = len(x & y) / len(x | y)
                                if j > best[0]:
                                    best = (j, x & y)
                    if best[0] >= CLOSE:
                        out.append({'domain': key, 'names': [a, b], 'similarity': round(best[0], 2),
                                    'shared': sorted(best[1]),
                                    'at': sorted({w for w, _ in names[a]} | {w for w, _ in names[b]})})
        return sorted(out, key=lambda x: (-x['similarity'], x['domain'], x['names']))

    def _odd_siblings(self):
        """A sibling whose shape differs from the rest of its group: a key few of its siblings hold, or one it lacks
        that most of them hold. The terms of one tier or profile, and the rows of one registry, are each a group."""
        groups = {}
        for name, (t, tier) in self.terms.items():
            groups.setdefault(('terms of ' + tier), {})['term:' + name] = {str(k) for k in t}
        for k in self.registries:
            rows = [r for r in self.law[k] if isinstance(r, dict)]
            key = next(iter(rows[0]), None) if rows else None
            for i, r in enumerate(rows):
                groups.setdefault('rows of registry:' + k, {})[f"registry:{k}[{r.get(key, i)}]"] = {str(x) for x in r}
        out = []
        for g, members in groups.items():
            if len(members) < 4:
                continue
            counts = {}
            for keys in members.values():
                for x in keys:
                    counts[x] = counts.get(x, 0) + 1
            n = len(members)
            for m, keys in members.items():
                rare = sorted(x for x in keys if counts[x] / n <= RARE)
                lacks = sorted(x for x, c in counts.items() if c / n >= COMMON and x not in keys)
                if rare or lacks:
                    out.append({'group': g, 'part': m, 'holds_rare': rare, 'lacks_common': lacks})
        return sorted(out, key=lambda x: (x['group'], x['part']))

    def _walks(self):
        out = []
        for f, p in self.py.items():
            if p.walks and self.parts[f]['kind'] in ('tool', 'module', 'hook') and f != 'bin/dmreckon.py':
                out.append({'part': f, 'walks': len(p.walks), 'lines': sorted(line for line, _col in p.walks),
                            'reads_through_dmreckon': ('imports', f, 'bin/dmreckon.py', '') in self.edges})
        return sorted(out, key=lambda x: (-x['walks'], x['part']))

    # -------------------------------------------------------------- the map, whole
    def data(self):
        return {'catalogue': {'release': self.release, 'law': self.version, 'of': 'garden' if self.garden else 'release',
                              'parts': len(self.parts), 'relations': len(self.edges)},
                'parts': {k: self.parts[k] for k in sorted(self.parts)},
                'relations': [{'rel': r, 'from': a, 'to': b, **({'via': v} if v else {})}
                              for r, a, b, v in sorted(self.edges)],
                'unplaced': sorted(self.unplaced),
                'findings': self.findings}


def _unfenced(text):
    return re.sub(r'(?ms)^(`{3,})[^\n]*\n.*?^\1[ \t]*$', '', text)


def _named_in(name, heading):
    """A law item a heading of the rules names, in its words: `schema_language` as "schema language", a registry by its
    one row's word as well (`natures` as "nature")."""
    phrase = name.replace('_', ' ')
    forms = {phrase}
    if phrase.endswith('ies'):
        forms.add(phrase[:-3] + 'y')
    elif phrase.endswith('s') and len(phrase) > 4:
        forms.add(phrase[:-1])
    return any(re.search(r'(?<![a-z])%s(?![a-z])' % re.escape(f), heading) for f in forms)


# ============================================================================ what a person reads
def _counts(cat):
    out, into = {}, {}
    for rel, a, b, _ in cat.edges:
        out.setdefault(a, {}).setdefault(rel, 0)
        out[a][rel] += 1
        into.setdefault(b, {}).setdefault(rel, 0)
        into[b][rel] += 1
    return out, into


_BY = {'imports': 'imported by', 'runs': 'run by', 'mentions': 'mentioned by', 'names': 'named by',
       'explains': 'explained by', 'holds': 'held by', 'uses': 'used by', 'covers': 'covered by', 'states': 'stated by',
       'ships': 'shipped by'}


def report(cat):
    d = cat.data()
    out, into = _counts(cat)
    kinds = {}
    for v in cat.parts.values():
        kinds[v['kind']] = kinds.get(v['kind'], 0) + 1
    files = len(cat.files)
    print(f"the catalogue of daftar {d['catalogue']['release']} (std-vocab {cat.version}), "
          f"{'this garden’s copy of the language' if cat.garden else 'the release'}: {files} files, "
          f"{len(cat.parts) - files} law items, {len(cat.edges)} relations")
    chain = []
    try:
        chain = cat.map.chain() or []
    except ValueError:
        pass
    order = chain + [r['layer'] for r in cat.map.rows if r['layer'] not in chain]
    width = max([len(f) for f in cat.files] + [20])
    for layer in order + [None]:
        fs = sorted(f for f in cat.files if cat.parts[f]['contents'].get('layer') == layer)
        if not fs:
            continue
        print(f"\n{layer or 'in no layer'} — {len(fs)} file{'s' if len(fs) != 1 else ''}")
        for f in fs:
            c = cat.parts[f]['contents']
            size = f"{c['lines']} lines" if 'lines' in c else f"{c.get('bytes', 0)} bytes"
            rels = [f"{r} {n}" for r, n in sorted(out.get(f, {}).items()) if r != 'holds'] + \
                   [f"{_BY[r]} {n}" for r, n in sorted(into.get(f, {}).items()) if r not in ('holds', 'ships')]
            print(f"  {f:{width}} {cat.parts[f]['kind']:15} {size:>11}   {' · '.join(rels)}")
    print(f"\nthe law's items — std-vocab {cat.version}")
    tiers = {}
    for name, (_t, tier) in sorted(cat.terms.items()):
        tiers.setdefault(tier, []).append(name)
    for tier in sorted(tiers, key=lambda t: (t != 'tier0', t)):
        print(f"  terms, {tier} ({len(tiers[tier])}): {', '.join(tiers[tier])}")
    print(f"  registries ({len(cat.registries)}): "
          + ', '.join(f"{k} {cat.parts['registry:' + k]['contents']['rows']}" for k in cat.registries))
    print(f"  sections ({len(cat.sections)}): {', '.join(cat.sections)}")
    print(f"  profiles ({len(cat.profiles)}): "
          + ', '.join(f"{p} ({len(cat.parts['profile:' + p]['contents']['terms'])} terms)" for p in cat.profiles))
    print(f"  layers ({len(cat.map.rows)}): {', '.join(r['layer'] for r in cat.map.rows)}")
    f = d['findings']
    print("\nfindings — candidates for a person to judge, never verdicts (`--findings` lists every one)")
    print(f"  law items nothing references: {len(f['unreferenced'])}"
          + (f" — {', '.join(x['part'] for x in f['unreferenced'][:12])}{' …' if len(f['unreferenced']) > 12 else ''}"
             if f['unreferenced'] else ''))
    print(f"  tools no suite imports, runs or names: {len(f['untested_tools'])}"
          + (f" — {', '.join(x['part'] for x in f['untested_tools'])}" if f['untested_tools'] else ''))
    print(f"  one domain under different names, meanings close: {len(f['one_domain_many_names'])}"
          + (f" — first: {' / '.join(f['one_domain_many_names'][0]['names'])} in {f['one_domain_many_names'][0]['domain']}"
             if f['one_domain_many_names'] else ''))
    print(f"  siblings whose shape differs from their group's: {len(f['odd_siblings'])}")
    print(f"  names the law gives several items: {len(f['one_name_many_items'])}"
          + (f" — {', '.join(x['name'] for x in f['one_name_many_items'])}" if f['one_name_many_items'] else ''))
    w = f['own_bean_walks']
    print(f"  files that list the beans themselves: {len(w)}"
          + (f" — {', '.join(x['part'].rsplit('/', 1)[-1][:-3] + ' ' + str(x['walks']) for x in w)}" if w else ''))


def show_findings(cat):
    f = cat.findings
    print("findings — candidates for a person to judge, never verdicts")
    print(f"\nlaw items nothing references ({len(f['unreferenced'])}) — no tool, module, hook, suite or document names "
          f"it, and no reason explains it")
    for x in f['unreferenced']:
        print(f"  {x['part']}")
    print(f"\ntools no suite imports, runs or names ({len(f['untested_tools'])})")
    for x in f['untested_tools']:
        print(f"  {x['part']}")
    print(f"\none domain under different attribute names, meanings sharing at least {CLOSE:.0%} of their words "
          f"({len(f['one_domain_many_names'])})")
    for x in f['one_domain_many_names']:
        print(f"  {x['similarity']:.2f}  {' / '.join(x['names']):40} in {x['domain']}   at {', '.join(x['at'])}")
        print(f"        shared: {', '.join(x['shared'])}")
    print(f"\nsiblings whose shape differs from their group's ({len(f['odd_siblings'])}) — a key at most {RARE:.0%} of "
          f"the group hold, or one lacked that at least {COMMON:.0%} hold")
    for x in f['odd_siblings']:
        bits = ([f"holds {', '.join(x['holds_rare'])}"] if x['holds_rare'] else []) + \
               ([f"lacks {', '.join(x['lacks_common'])}"] if x['lacks_common'] else [])
        print(f"  {x['part']:48} {'; '.join(bits)}   ({x['group']})")
    print(f"\nnames the law gives several items ({len(f['one_name_many_items'])}) — a text naming one cannot say which")
    for x in f['one_name_many_items']:
        print(f"  {x['name']:24} {', '.join(x['parts'])}")
    print(f"\nfiles that list the beans themselves, rather than read them through bin/dmreckon.py "
          f"({len(f['own_bean_walks'])})")
    for x in f['own_bean_walks']:
        print(f"  {x['part']:40} {x['walks']:3}  lines {', '.join(map(str, x['lines']))}"
              + ("   (imports dmreckon too)" if x['reads_through_dmreckon'] else ''))


def find(cat, name):
    """The parts a name picks: an id exactly, else every law item of that name, else a file by its path's end."""
    if name in cat.parts:
        return [name]
    hit = sorted(p for p, v in cat.parts.items() if v['name'] == name and v['kind'] in LAW_KINDS)
    hit = hit or sorted(p for p in cat.files if p.endswith('/' + name) or p.rsplit('/', 1)[-1] in (name, name + '.py'))
    return hit


def show_part(cat, pid):
    v = cat.parts[pid]
    c = v['contents']
    where = f", in the {c['layer']} layer" if c.get('layer') else (", in no layer" if v['kind'] not in (
        'term', 'registry', 'section', 'profile', 'layer') else '')
    kept = f", kept by the {'release' if c['kept'] == 'release' else 'tree that holds it'}" if 'kept' in c else ''
    print(f"{pid} — {v['kind']}{where}{kept}")
    for k in sorted(c):
        if k in ('layer', 'kept'):
            continue
        val = c[k]
        if isinstance(val, dict):
            print(f"  {k}:" + ('' if val else ' none'))
            for kk in sorted(val):
                print(f"    {kk}: {val[kk]}")
        elif isinstance(val, list):
            print(f"  {k} ({len(val)}): {', '.join(map(str, val))}" if val else f"  {k}: none")
        elif val not in (None, ''):
            print(f"  {k}: {val}")
    outs = {}
    ins = {}
    for rel, a, b, via in sorted(cat.edges):
        if a == pid:
            outs.setdefault(rel, []).append(b + (f" ({via})" if via else ''))
        if b == pid:
            ins.setdefault(rel, []).append(a + (f" ({via})" if via else ''))
    print("  relations:" + ('' if outs or ins else ' none'))
    for rel in RELATIONS:
        if rel in outs:
            print(f"    {rel} ({len(outs[rel])}): {', '.join(outs[rel])}")
    for rel in RELATIONS:
        if rel in ins:
            print(f"    {_BY[rel]} ({len(ins[rel])}): {', '.join(ins[rel])}")
    ck = v['checklists']
    print(f"  rules (bin/dmrules.py): {len(ck['rules'])}")
    for r in ck['rules']:
        print(f"    [{r['section']}] {r['rule']}")
    print(f"  CHECKLIST.md items that name it: {len(ck['checklist'])}")
    for r in ck['checklist']:
        print(f"    {r['item']}  {r['text'][:200]}{'…' if len(r['text']) > 200 else ''}")
    print(f"  suite checks that name it: {len(ck['checks'])}")
    for r in ck['checks']:
        print(f"    {r['suite']}:{r['line']}  {r['check'][:200]}{'…' if len(r['check']) > 200 else ''}")


def main(argv):
    try:
        cat = Catalogue()
    except ValueError as e:
        print(f"dmcatalog: {e}", file=sys.stderr)
        return 2
    if '--json' in argv:
        print(json.dumps(cat.data(), ensure_ascii=False, indent=1, sort_keys=True, default=str))
        return 0
    if '--findings' in argv:
        show_findings(cat)
        return 0
    if '--part' in argv:
        i = argv.index('--part')
        name = argv[i + 1] if i + 1 < len(argv) else ''
        hit = find(cat, name)
        if not hit:
            print(f"dmcatalog: no part is named {name!r} — a law item by its name (`units`, `term:view`), a file by its "
                  f"path or its name (`bin/dmsave.py`, `dmsave`)", file=sys.stderr)
            return 1
        for n, pid in enumerate(hit):
            if n:
                print()
            show_part(cat, pid)
        return 0
    report(cat)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
