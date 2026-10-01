"""lines — the forms of a line, read from a bean's statements and judged by rule `line` (v1 part 6).

Time is a line, and so is a walk (spec §5). What holds a line holds it in statements of five verbs, each line's own
structure in one qualifier of the shape `form`, whose attributes core/law/lines.yaml `forms` gives:

  series    `record: { id, of, by?, through?, series: <form series> }` — its positions by rule (`grid`) or listed
            (`span`), what each position holds (`holds`, one channel each), its rows, inline or in the parts
            `series/<bean>/<id>/<part>.tsv`, and the cells a judge set aside (`excluded`)
  walk      the `step` statements of a bean: `step: { id, as: <what is done>, by?: <who acts>, to?: [<steps it leads
            on to>], walk?: <form step> }` — how long it usually takes, whether it is a way out, a pause or an end, the
            reasons a move into it may cite, and the words of a way on (`ways`)
  course    a being placed on a walk: `be: { id, by: self, at: <walk>, as: order }`
  move      `move: { through: <course>, at: [<moment>, <walk>#<step>], by?, as?: <a reason the step lists>, why? }`
  reading   `reckon: { id, reading: <form reading> }` — its steps, each one operation of the closed list, its paths read
            over statements: `kind`, `bean`, `title`, `summary`, `tags`, `details.…`, or `<verb>.<role>…`, a verb's
            statements and a role of each; a condition names its comparator by the core's sign where it has one
  pin       `pin: { of: [<what rests on a reading>], from?: [<bean>#<reading>], at: [<moment>, <repo>@<commit>] }` —
            the moment and the commit of the garden's object graph a reading was read at

THE ONE VIEW. The tools that read a line — bin/dmseq.py, bin/dmreckon.py — read an entry in the shape today's term held
it, so this module gives each line as that entry (`series_of`, `steps_of`, `courses_of`, `moves_of`, `readings_of`),
and `view` gives a whole bean so: its header, its statements by verb, and its lines. One code reads both laws' lines,
and this is the only place the view is built. `law_view` is the law a line is read by — the reading's grammar from
lines.yaml, the units by their UCUM codes; until part 7 carries a unit's factor and part 13 the rest, the factors and
the other tables are today's, read through the gate's registry (the bridge)."""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))

KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
FLAGS = ('exit', 'resumes', 'final', 'digits', 'back', 'convention')   # what a form writes `true`, a tool reads True
HEADER_PATHS = ('kind', 'bean', 'title', 'summary', 'tags', 'details')   # a reading's path starts here, or at a verb
SIGNS = {'=': 'is', '∈': 'in', '≥': 'at_least', '≤': 'at_most', '∃': 'exists', '∄': 'absent'}    # the core's sign
NEW_SIGNS = ('≠', '<', '>')                                            # signs the core reads that today's words lack
GRAPH = re.compile(r'^([a-z0-9][a-z0-9._-]*)@([0-9a-f]{7,40})$')     # a position of git-object-graph: <repo>@<commit>


def typed(x):
    """A form's value as a tool reads it: every `true` of a flag a boolean, a whole `count` a number (a recurrence
    strides by one), the rest as written."""
    if isinstance(x, dict):
        return {k: (True if k in FLAGS and v == 'true' else False if k in FLAGS and v == 'false'
                    else int(v) if k == 'count' and isinstance(v, str) and v.isdigit() and v.isascii() else typed(v))
                for k, v in x.items()}
    if isinstance(x, list):
        return [typed(v) for v in x]
    return x


def _listed(x):
    return x if isinstance(x, list) else ([] if x is None else [x])


def _live(b, verb):
    """(index, roles) of each statement of `verb` in bean `b` that is not sealed."""
    return [(i, r) for i, v, r in b.items if v == verb and 'held' not in r]


# ------------------------------------------------------------------------------------------------ the lines, as entries
def series_of(b):
    """{id: series entry} of a bean: each `record`'s form, its `note` beside it."""
    out = {}
    for _i, r in _live(b, 'record'):
        if isinstance(r.get('id'), str) and isinstance(r.get('series'), dict):
            out[r['id']] = dict(typed(r['series']), **({'note': r['note']} if 'note' in r else {}))
    return out


def steps_of(b):
    """[step entry] of a bean that holds a walk, in the order written: the step's id, `do` (its `as`), `by`, `next` (its
    `to`, each with the words its `ways` gives), and its form."""
    out = []
    for _i, r in _live(b, 'step'):
        st = {k: v for k, v in typed(r.get('walk') or {}).items() if k != 'ways'} if isinstance(r.get('walk'), dict) else {}
        words = {w.get('to'): w for w in (r.get('walk') or {}).get('ways') or []
                 if isinstance(w, dict) and isinstance(w.get('to'), str)} \
            if isinstance(r.get('walk'), dict) else {}
        st = dict({'id': r.get('id'), 'do': r.get('as')}, **({'by': r['by']} if 'by' in r else {}), **st)
        if 'to' in r:
            st['next'] = [dict({'to': t}, **{k: v for k, v in (words.get(t) or {}).items() if k != 'to'})
                          for t in _listed(r['to']) if isinstance(t, str)]
        if 'note' in r:
            st['note'] = r['note']
        out.append(st)
    return out


def is_walk(G, bid):
    b = G.beans.get(bid) if isinstance(bid, str) else None
    return bool(b and not b.unread and _live(b, 'step'))


def courses_of(b, G):
    """{course id: {'walk', 'note'?}}: each `be` of the bean, as order, at a bean that holds a walk."""
    out = {}
    for _i, r in _live(b, 'be'):
        if r.get('as') != 'order' or not isinstance(r.get('id'), str):
            continue
        walks = [a for a in _listed(r.get('at')) if is_walk(G, a)]
        if walks:
            out[r['id']] = dict({'walk': walks[0]}, **({'note': r['note']} if 'note' in r else {}))
    return out


def split_at(at):
    """(moment, step ref) of a move's `at`: the one position, and the one `<walk>#<step>`."""
    moments = [a for a in _listed(at) if isinstance(a, str) and '#' not in a]
    steps = [a for a in _listed(at) if isinstance(a, str) and '#' in a]
    return (moments[0] if len(moments) == 1 else None), (steps[0] if len(steps) == 1 else None)


def moves_of(b):
    """[(index, move entry)] of a bean, in the order written: its course, moment, step, who moved it, its reason and why."""
    out = []
    for i, r in _live(b, 'move'):
        moment, step = split_at(r.get('at'))
        mv = {'course': r.get('through'), 'at': moment, 'step': step.split('#', 1)[1] if step else None}
        for k, o in (('by', 'by'), ('as', 'reason'), ('why', 'why'), ('note', 'note')):
            if k in r:
                mv[o] = r[k]
        out.append((i, mv))
    return out


def readings_of(b):
    """{id: reading entry} of a bean: each `reckon`'s form, its comparators in today's words for the reader."""
    out = {}
    for _i, r in _live(b, 'reckon'):
        if isinstance(r.get('id'), str) and isinstance(r.get('reading'), dict):
            out[r['id']] = dict(worded(typed(r['reading'])), **({'note': r['note']} if 'note' in r else {}))
    return out


def worded(entry):
    """A reading whose conditions name the core's signs, with each sign in the word the reader applies, and a series
    named as a statement (`<bean>#<id>`) by the path the reader follows to it (`<bean>:series.<id>`, the view's)."""
    out = dict(entry)
    steps = []
    for s in entry.get('steps') or []:
        if isinstance(s, dict) and isinstance(s.get('where'), list):
            s = dict(s, where=[{SIGNS.get(k, k): v for k, v in c.items()} if isinstance(c, dict) else c
                               for c in s['where']])
        if isinstance(s, dict):
            for k in ('series',) + (('with',) if s.get('op') == 'join' else ()):
                if isinstance(s.get(k), str) and re.match(r'^[a-z0-9][a-z0-9_-]*#[a-z0-9][a-z0-9_-]*$', s[k]):
                    s = dict(s, **{k: s[k].replace('#', ':series.', 1)})
        steps.append(s)
    if 'steps' in entry:
        out['steps'] = steps
    return out


def view(b, G):
    """A bean as the read tools read it: its header, each verb's statements (their roles, as `<verb>: [...]`), and its
    lines in the shape today's terms held them — `series`, `steps`, `courses`, `moves`, `selections`."""
    v = {k: b.header[k] for k in ('kind', 'title', 'summary', 'tags', 'details') if k in b.header}
    v['bean'] = b.id
    for _i, verb, r in b.items:
        v.setdefault(verb, []).append(r)
    for key, got in (('series', series_of(b)), ('steps', steps_of(b)), ('courses', courses_of(b, G)),
                     ('moves', [m for _i, m in moves_of(b)]), ('selections', readings_of(b))):
        if got:
            v[key] = got
    return v


# ------------------------------------------------------------------------------------------------ the law a line is read by
_VIEWS = {}


def _today(root):
    """Today's law, read with its types (a factor is two numbers), and a reader of its registries: a section of it, or
    the data file its `registry_files` names — the bridge until parts 7 and 13 carry these as the core's own."""
    import csv
    import dmparse
    path = os.path.join(root, 'seed', 'std-vocab.md')
    path = path if os.path.isfile(path) else os.path.join(ROOT, 'seed', 'std-vocab.md')
    base = os.path.dirname(os.path.dirname(path))
    with open(path, encoding='utf-8') as fh:
        law = dmparse.loads(dmparse.split_front_matter(fh.read())[0]) or {}
    files, cache = {r.get('registry'): r for r in law.get('registry_files') or [] if isinstance(r, dict)}, {}

    def registry(name):
        if name in cache:
            return cache[name]
        rows = law.get(name)
        decl = files.get(name)
        if rows is None and decl:
            try:
                with open(os.path.join(base, decl.get('file', '')), encoding='utf-8') as fh:
                    rows = dmparse.loads(fh.read()) if decl.get('format') == 'yaml' else list(
                        csv.DictReader((ln for ln in fh if not ln.startswith('#')), delimiter='\t'))
            except OSError:
                rows = None
        cache[name] = rows
        return rows
    return law, registry


def law_view(L, root=None):
    """A dmseq.Law for a garden of the core: the reading's grammar from lines.yaml (its comparisons as the reader's
    `comparators`), the kinds as the core's, the units by their UCUM codes; their factors, the quantities and the other
    tables today's (`_today`), until parts 7 and 13 carry them."""
    if id(L) in _VIEWS:
        return _VIEWS[id(L)]
    import dmseq
    today, registry_today = _today(root or ROOT)

    def keyed(rows, key):
        return {r[key]: r for r in rows or [] if isinstance(r, dict) and r.get(key) is not None}
    by_name = keyed(today.get('units'), 'unit')
    units = {}
    for code, row in L.units.items():
        old = by_name.get(row.get('name')) or {}
        units[code] = dict(old, unit=code, name=row.get('name'), quantity=row.get('quantity') or old.get('quantity'))
    ll = L.line_law or {}
    own = {'operations': ll.get('operations'), 'comparators': ll.get('comparisons'), 'aggregates': ll.get('aggregates'),
           'ordering_keys': ll.get('ordering_keys'), 'selection_form': ll.get('selection_form'),
           'pin_form': ll.get('pin_form'), 'units': list(units.values()),
           'kinds': [dict(r, kind=k) for k, r in L.kinds.items()]}

    def registry(name):
        return own[name] if own.get(name) is not None else registry_today(name)
    law = dmseq.Law(units, keyed(today.get('quantities'), 'quantity'), keyed(today.get('anchor_systems'), 'system'),
                    keyed(today.get('aspects'), 'aspect'), keyed(today.get('figures'), 'figure'), registry)
    _VIEWS[id(L)] = law
    return law


# ------------------------------------------------------------------------------------------------ the rule `line`
def attrs_problems(where, x, form, depth=0):
    """What is wrong with `x` as a value of `form` ({attrs, one_of?}) at the depth the core reads a form: a mapping, each
    key an attribute it declares, the required ones present, a value of a closed list one of it, a kebab word one, prose
    text, entries each judged so. A domain a tool reads (a unit, a quantity, an extent) is that tool's to judge."""
    attrs = form.get('attrs') or form.get('entries') or {}
    if not isinstance(x, dict):
        return [(where, f"is a mapping of {', '.join(sorted(attrs))}")]
    out = []
    for k in x:
        if k not in attrs:
            out.append((where, f"`{k}` is no attribute of it: it holds {', '.join(sorted(attrs))} — a remark is the "
                               f"statement's `note`"))
    for k, spec in attrs.items():
        spec = spec if isinstance(spec, dict) else {}
        if spec.get('required') in ('true', True) and k not in x:
            out.append((where, f"`{k}` is required: {str(spec.get('meaning') or '')[:160]}"))
        if k not in x:
            continue
        v, dom = x[k], spec.get('in')
        w = f"{where}.{k}"
        if isinstance(dom, list) and not (str(v) in dom or (isinstance(v, list) and all(str(e) in dom for e in v))):
            out.append((w, f"{v!r} is not one of {', '.join(dom)}"))
        elif dom == 'prose' and not isinstance(v, str):
            out.append((w, "is prose, written as text"))
        elif isinstance(dom, dict) and dom.get('type') == 'kebab' and not (isinstance(v, str) and KEBAB.match(v)):
            out.append((w, f"{v!r} is not a kebab word"))
        elif isinstance(dom, dict) and isinstance(dom.get('entries'), dict):
            items = v if isinstance(v, list) else [v]
            seen = set()
            for n, e in enumerate(items):
                out += attrs_problems(f"{w}[{n}]", e, dom, depth + 1)
                keys = [dom['keyed_by']] if isinstance(dom.get('keyed_by'), str) else _listed(dom.get('keyed_by'))
                if keys and isinstance(e, dict):
                    key = tuple(str(e.get(kk)) for kk in keys)
                    if key in seen:
                        out.append((f"{w}[{n}]", f"{'/'.join(key)} is written twice: one entry for each "
                                                 f"{', '.join(keys)}"))
                    seen.add(key)
    one = _listed(form.get('one_of'))
    if one and depth == 0 and sum(1 for k in one if k in x) != 1:
        out.append((where, f"holds one of {', '.join(one)}, and only one"))
    return out


def problems(J, b):
    """[(where, message)] of rule `line` for bean `b`, judged by the engine `J` (its law, its garden)."""
    L, G = J.L, J.G
    forms = L.forms or {}
    out = []
    if not (forms and b.items):
        return out
    import dmseq
    import dmreckon
    law = None

    def lw():
        nonlocal law
        law = law or law_view(L, G.root)
        return law
    for i, verb, r in b.items:
        if 'held' in r:
            continue
        where = f"{b.id}: statements[{i}] {verb}"
        if verb == 'record':
            if not isinstance(r.get('id'), str):
                out.append((where, "a series is named: its statement has an `id`, which its parts' folder and a "
                                   "reading name it by"))
                continue
            got = attrs_problems(f"{where}.series", r.get('series'), forms.get('series') or {})
            out += got
            if not got:
                entry = series_of(b)[r['id']]
                for level, w, what in dmseq.check_series(lw(), b.id, r['id'], entry,
                                                         dmseq.parts_of(G.root, b.id, r['id']) if G.root else None):
                    if level == 'error':
                        out.append((f"{where}.series{w}", what))
        elif verb == 'step':
            if not isinstance(r.get('id'), str):
                out.append((where, "a step is named: its statement has an `id`, which a move reaches it by"))
            if 'walk' in r:
                out += attrs_problems(f"{where}.walk", r['walk'], forms.get('step') or {})
            steps = {sid for sid, (_n, v, _r) in b.ids.items() if v == 'step'}
            for t in _listed(r.get('to')):
                if isinstance(t, str) and t not in steps:           # what is no name is valency's to refuse
                    out.append((f"{where}.to", f"{t!r} is no step of this walk ({', '.join(sorted(steps))}): a way on "
                                               f"leads to a step of the walk it is in"))
            for wy in ((r.get('walk') or {}).get('ways') or []) if isinstance(r.get('walk'), dict) else []:
                if isinstance(wy, dict) and wy.get('to') not in _listed(r.get('to')):
                    out.append((f"{where}.walk.ways", f"{wy.get('to')!r} is not a step this one leads to (`to`)"))
        elif verb == 'reckon':
            if not isinstance(r.get('id'), str):
                out.append((where, "a reading is named: its statement has an `id`, which a clause, a pin or a person "
                                   "names it by (`<bean>#<id>`)"))
                continue
            got = attrs_problems(f"{where}.reading", r.get('reading'), forms.get('reading') or {})
            out += got
            if not got:
                out += reading_problems(where, r['reading'], lw(), L.verbs)
        elif verb == 'move':
            out += _move_problems(where, r, b, G)
        elif verb == 'pin':
            out += _pin_problems(where, r, b, G)
    # each course's moves against its walk, in the order written (dmseq.check_moves, the one judge of a course)
    courses = courses_of(b, G)
    for cid, c in courses.items():
        moves = [(i, m) for i, m in moves_of(b) if m.get('course') == cid]
        steps = steps_of(G.beans[c['walk']])
        for i, level, what in dmseq.check_moves(moves, steps, c['walk']):
            if level == 'error':
                out.append((f"{b.id}: statements[{i}] move", what))
    if any(v == 'step' for _i, v, _r in b.items):
        for sid, why in dmseq.walk_problems(steps_of(b)):
            out.append((f"{b.id}: step {sid}", why))
    return out


def reading_problems(where, reading, law, verbs=None):
    """A reading's steps against the closed list (dmreckon's check), its conditions in the core's signs, and its paths
    read over statements: from a bean's header or a verb, or — where the step reads statements (`entries`) — from a
    statement's roles and keys."""
    import dmreckon
    out = []
    verbs = verbs or {}
    keys = {'id', 'while', 'why', 'note', 'held', 'by', 'of', 'through', 'to', 'from', 'at', 'as'} | {
        q for v in verbs.values() if isinstance(v, dict) for q in (v.get('qualifiers') or {})}
    reads = {}                                         # step id -> 'statement' where its members are statements
    for s in reading.get('steps') or [] if isinstance(reading.get('steps'), list) else []:
        if not isinstance(s, dict):
            continue
        member = 'statement' if s.get('entries') or reads.get(s.get('of')) == 'statement' else 'bean'
        if isinstance(s.get('id'), str):
            reads[s['id']] = 'statement' if s.get('entries') else reads.get(s.get('of'), 'bean')
        top = keys if member == 'statement' else None
        for c in s.get('where') or [] if isinstance(s.get('where'), list) else []:
            if not isinstance(c, dict):
                continue
            for k in c:
                if k in dmreckon_words():
                    out.append((f"{where}.reading.steps[{s.get('id')}]",
                                f"`{k}` is written by its sign in the core: `{WORD_SIGN[k]}`"))
            for k in ('reached', 'at_step'):
                if k in c and not (isinstance(c[k], str) and re.match(r'^[a-z0-9][a-z0-9_-]*#[a-z0-9][a-z0-9_-]*$', c[k])):
                    out.append((f"{where}.reading.steps[{s.get('id')}]",
                                f"`{k}` names the step as a statement of its walk, `<walk>#<step>` — not {c[k]!r}"))
            if isinstance(c.get('path'), str) and c['path'] != 'move':
                out += path_problems(f"{where}.reading.steps[{s.get('id')}]", c['path'], top or verbs)
        for k in ('path', 'amount', 'over'):
            if isinstance(s.get(k), str):
                out += path_problems(f"{where}.reading.steps[{s.get('id')}].{k}", s[k], top or verbs)
        if isinstance(s.get('entries'), str):
            out += path_problems(f"{where}.reading.steps[{s.get('id')}].entries", s['entries'], verbs)
        if isinstance(s.get('series'), str) and not re.match(r'^[a-z0-9][a-z0-9_-]*#[a-z0-9][a-z0-9_-]*$', s['series']):
            out.append((f"{where}.reading.steps[{s.get('id')}].series",
                        f"a series is named as a statement, `<bean>#<id>` — not {s['series']!r}"))
    for level, text in dmreckon.check_selection(where + '.reading', worded(typed(reading)), law):
        if level == 'error':
            out.append((where, text))
    return out


WORD_SIGN = {w: s for s, w in SIGNS.items()}


def dmreckon_words():
    return WORD_SIGN


def path_problems(where, path, starts=()):
    """A reading's path over statements: over a bean it starts at a key of the header or at a verb's statements
    (`pay.of`), on this bean or on another (`<bean>:<path>`); over a statement, at one of its roles or keys (`starts`
    a set). Anything else is today's words, refused by name."""
    rest = path.split(':', 1)[1] if ':' in path.split('.', 1)[0] else path
    first = re.split(r'[.\[]', rest, 1)[0]
    if isinstance(starts, set):
        if first in starts:
            return []
        return [(where, f"`{path}` is no role or key of the statements this step reads: {', '.join(sorted(starts))}")]
    if first in HEADER_PATHS or first in starts:
        return []
    return [(where, f"`{path}` reads today's words: in the core a path starts at {', '.join(HEADER_PATHS)}, or at a "
                    f"verb's statements (`pay.of`, `move.at`, `agree.by`)")]


def _move_problems(where, r, b, G):
    out = []
    courses = courses_of(b, G)
    c = courses.get(r.get('through')) if isinstance(r.get('through'), str) else None
    if c is None:
        return [(f"{where}.through", f"{r.get('through')!r} is no course of this bean: a course is the bean placed on a "
                                     f"walk, `be: {{ id, by: self, at: <walk>, as: order }}`"
                 + (f" — it has {', '.join(sorted(courses))}" if courses else ''))]
    moment, step = split_at(r.get('at'))
    if moment is None:
        out.append((f"{where}.at", "holds one moment, the move's — `now`, which the save writes"))
    if step is None:
        out.append((f"{where}.at", f"holds one step reached, `{c['walk']}#<step>`"))
    elif step.split('#', 1)[0] != c['walk']:
        out.append((f"{where}.at", f"{step!r} is a step of another walk: the course {r.get('through')!r} moves along "
                                   f"{c['walk']}"))
    else:
        hit = G.beans[c['walk']].ids.get(step.split('#', 1)[1])
        if not hit or hit[1] != 'step':
            out.append((f"{where}.at", f"{step!r} is no step of the walk {c['walk']}"))
    return out


def _pin_problems(where, r, b, G):
    out = []
    ats = _listed(r.get('at'))
    commits = [a for a in ats if isinstance(a, str) and GRAPH.match(a)]
    if len(commits) != 1 or len(ats) != 2:
        return [(f"{where}.at", "holds the moment the reading was read at (`now`, which the save writes) and the commit "
                                "it was read in, `<repo>@<object id>` (git-object-graph)")]
    sha = GRAPH.match(commits[0]).group(2)
    if G.root and 'through' not in r and os.path.isdir(os.path.join(G.root, '.git')) and subprocess.run(
            ['git', '-C', G.root, 'merge-base', '--is-ancestor', sha, 'HEAD'], capture_output=True).returncode:
        out.append((f"{where}.at", f"the commit {sha} is not an ancestor of HEAD: a reading is pinned to a commit this "
                                   f"garden has"))
    for f in _listed(r.get('from')):
        bid, _, sid = str(f).rpartition('#')
        other = G.beans.get(bid) if bid else b
        hit = other.ids.get(sid) if other else None
        if not hit or hit[1] != 'reckon':
            out.append((f"{where}.from", f"{f!r} is no reading: a pin rests on a `reckon` statement"))
    return out
