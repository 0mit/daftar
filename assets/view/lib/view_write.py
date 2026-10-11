#!/usr/bin/env python3
"""view_write — the view's ONE write path: what a sheet's Save writes, and what a drawing's entry form of a verb adds
(the view finished for a handplace, design V1 §4 and §5). `view serve` calls it, and so may any host that serves a
garden's pages (a worker that imports this file from the release the garden runs): one implementation.

    write(root, who, bean, ops, kind=None, may=None, what=None) -> {ok, bean, commit, refusals, output}

`ops` is a list for one bean, each one of:
    {op: add,    verb, roles, id?, held?, while?}         a statement appended; its id minted where it gives none
    {op: change, key, verb?, roles, held?, while?}         the statement `key` names, rewritten in place
    {op: remove, key}                                      the statement `key` names, taken out
    {op: change, header: title | summary, value}           a header fact, rewritten (an empty summary is taken out)
    {op: change, header: tags, value: [words]}             the bean's tags, as a set (none: the key taken out)
`key` names a statement as bin/safe.py names it: `<verb>#<id>`, or `<verb>@<n>` for one with no id — changed or removed
only where it is the one statement of its verb. With `bean` None and `kind`, the ops make a NEW being of that kind:
its id minted opaque (`p-<8 hex>` for a person, its title the id; `<kind>-<8 hex>` for any other), its file written
whole.

WHAT HAPPENS, IN ORDER. The clone holds nothing uncommitted (its undo is git's). Each op is read against its verb's row:
the roles and qualifiers it takes, and text that is one line. `may(act, bean, positions)` is asked for the bean — and
where the whole is not open, for the part each op touches (the statement by its id, a verb for one added, `title` or
`summary`), as a grant's `cover` opens parts. Each edit goes through bin/safe.py by its key with an expected count of 1;
a held value is sealed by bin/held.py before its statement is written, so what it says reaches the store and never the
bean's file. The statements added or changed are known by a `say` of the writer's, at `now`. The bean is read again,
each statement written is read back as intended and judged by the gate's own judge (core/engine.py `Judge.one`), and
then bin/save.py saves it — ONE journal entry naming each statement added, changed or removed — and the gate judges the
whole commit. A REFUSAL UNDOES EVERYTHING: the working tree and the index as they were, every store record this write
made taken out; and each message is returned tied to the op whose statement it names (`op`: its index; `fact`: its
key), or to none where it names the bean.

The caller holds its own lock where it writes from more than one thread (view_serve holds one); bin/save.py queues
writers of one clone.
"""
import json, os, re, secrets, subprocess, sys

OPS = ('add', 'change', 'remove')
HEADERS = ('title', 'summary', 'tags')
BESIDE = ('note', 'why')                     # what a statement carries beside its roles that a sheet writes
_CTRL = re.compile('[\x00-\x08\x0a-\x1f\x7f-\x9f  ]')
_KEY = re.compile(r'^([a-z][a-z0-9-]*)(?:#([A-Za-z0-9][A-Za-z0-9_.-]*)|@(\d+))$')
_ID = re.compile(r'^[a-z0-9][a-z0-9-]*$')


def _listed(x):
    return x if isinstance(x, list) else [] if x is None else [x]


def _git(root, *a):
    return subprocess.run(['git', '-C', root] + list(a), capture_output=True, text=True, encoding='utf-8',
                          errors='replace')


def _flow(roles):
    import yaml
    return yaml.safe_dump(roles, default_flow_style=True, sort_keys=False, allow_unicode=True, width=10 ** 9).strip()


def _text_only(x, where):
    """Why a value a person gave is not one the ledger writes — every value text, one line — or ''."""
    if isinstance(x, dict):
        for k, v in x.items():
            why = _text_only(v, f"{where}.{k}")
            if why:
                return why
        return ''
    if isinstance(x, list):
        return next((w for w in (_text_only(v, f"{where}[{i}]") for i, v in enumerate(x)) if w), '')
    if not isinstance(x, str):
        return f"`{where}` is written as text, not as a {type(x).__name__}"
    if _CTRL.search(x):
        return f"`{where}` holds a line break or a control character: a value is one line of text"
    return ''


def _keys(b):
    """{key: (index, verb, roles)} of a bean's statements, keyed as bin/safe.py keys them."""
    out, nth = {}, {}
    for i, v, r in b.items:
        if not isinstance(r, dict):
            continue
        if isinstance(r.get('id'), str):
            out[f"{v}#{r['id']}"] = (i, v, r)
        else:
            out[f"{v}@{nth.get(v, 0)}"] = (i, v, r)
            nth[v] = nth.get(v, 0) + 1
    return out


def _mint(ids, verb):
    n = 1
    while f"{verb}-{n}" in ids:
        n += 1
    return f"{verb}-{n}"


def default_may(root, who):
    """The law's answer for the writer, where the caller gives none: bin/pass.py `may`."""
    import importlib
    dmpass = importlib.import_module('pass')

    def may(act, bean, positions=None):
        return dmpass.may(who, act, bean, positions=positions, root=root).granted
    return may


def write(root, who, bean, ops, kind=None, may=None, what=None):
    root = os.path.abspath(root)
    for p in (root, os.path.join(root, 'bin')):
        if p not in sys.path:
            sys.path.insert(0, p)
    import safe
    import held as dmheld
    from core import engine
    from core.check import garden_law
    refusals, made, unseal_after = [], [], []

    def refuse(n, fact, msg):
        refusals.append({'op': n, 'fact': fact, 'message': msg})

    def result(ok, out='', commit=None):
        return {'ok': ok, 'bean': bean, 'commit': commit, 'refusals': refusals, 'output': out}

    if not isinstance(ops, list) or not ops:
        refuse(None, None, "nothing to write: the ops are a list of what to add, change or remove")
        return result(False)
    if _git(root, 'status', '--porcelain').stdout.strip():
        refuse(None, None, "the garden holds changes not yet committed — nothing written")
        return result(False)
    G = engine.Garden.read(root)
    L = garden_law(root)
    may = may or default_may(root, who)
    new = bean is None
    if new:
        if kind not in L.kinds:
            refuse(None, None, f"{kind!r} is no kind of the law: a new being is a being of a kind")
            return result(False)
        while True:
            bean = ('p-' if kind == 'person' else f"{kind}-") + secrets.token_hex(4)
            if bean not in G.beans and not os.path.exists(os.path.join(root, 'beans', bean + '.md')):
                break
        b, keys = None, {}
    else:
        b = G.beans.get(bean) if isinstance(bean, str) else None
        if b is None or b.unread or os.path.basename(os.path.dirname(b.path or '')) != 'beans':
            refuse(None, None, f"the garden holds no bean {bean!r} that can be read")
            return result(False)
        keys = _keys(b)
    ids = {r['id'] for _i, _v, r in keys.values() if isinstance(r.get('id'), str)}
    counts = {}                                  # how many statements of each verb the bean holds
    for _i, v, _r in keys.values():
        counts[v] = counts.get(v, 0) + 1

    # ---- 1. EACH OP AGAINST ITS VERB'S ROW, AND THE BEAN
    plan, touched = [], set()
    for n, op in enumerate(ops):
        if not isinstance(op, dict) or op.get('op') not in OPS:
            refuse(n, None, "an op is one of add, change, remove")
            continue
        if 'header' in op:
            h, v = op.get('header'), op.get('value')
            if op['op'] != 'change' or h not in HEADERS:
                refuse(n, f"header:{h}", "a header fact is changed: the title, the summary, or the tags")
            elif h == 'tags':                    # A SET OF WORDS: each one line, none twice; the order as given
                words = [x.strip() for x in v] if isinstance(v, list) and all(isinstance(x, str) for x in v) else None
                if words is None or any(not x or _CTRL.search(x) for x in words) or len(set(words)) != len(words):
                    refuse(n, 'header:tags', "the tags are a list of words, each one line, none empty and none twice")
                elif 'header:tags' in touched:
                    refuse(n, 'header:tags', "the tags are changed once in a write")
                else:
                    touched.add('header:tags')
                    if b is None or sorted(b.header.get('tags') or []) != sorted(words):
                        plan.append((n, 'header', 'tags', words, None))
            elif not isinstance(v, str) or (h == 'title' and not v.strip()) or _CTRL.search(v):
                refuse(n, f"header:{h}", f"the {h} is one line of text" + (", and a title is never empty" if h == 'title' else ''))
            elif new and h == 'title' and kind == 'person':
                refuse(n, 'header:title', "a person kept without their word is titled by their id (rule `consent`)")
            elif f"header:{h}" in touched:
                refuse(n, f"header:{h}", f"the {h} is changed once in a write")
            elif b is not None and (b.header.get(h) or '') == v.strip():
                touched.add(f"header:{h}")           # it says what the bean says already: nothing to write for it
            else:
                touched.add(f"header:{h}")
                plan.append((n, 'header', h, v.strip(), None))
            continue
        if op['op'] in ('change', 'remove'):
            key = op.get('key')
            m = _KEY.match(key) if isinstance(key, str) else None
            if not m or key not in keys:
                refuse(n, key, f"{bean} holds no statement {key!r}")
                continue
            if key in touched:
                refuse(n, key, f"{key} is changed or taken out once in a write")
                continue
            touched.add(key)
            i, verb, old = keys[key]
            if m.group(3) is not None and counts.get(verb, 0) != 1:
                refuse(n, key, f"this `{verb}` has no id, and {bean} holds {counts.get(verb)} of its verb: a statement is "
                               f"changed or removed by its id (bin/safe.py, one line, an expected count of 1)")
                continue
            if op['op'] == 'remove':
                if 'held' in old:                # a held value is taken out where its store is: its record goes with it
                    try:
                        dmheld.resolve(old['held'], root=root)
                    except (dmheld.NotHere, dmheld.Erased, ValueError, OSError) as e:
                        refuse(n, key, f"{key} is held off git and kept elsewhere: it is taken out where it is kept ({e})")
                        continue
                plan.append((n, 'remove', key, verb, old))
                continue
            if op.get('verb') not in (None, verb):
                refuse(n, key, f"{key} is a `{verb}`: a change keeps its verb (a new verb is a statement added)")
                continue
        else:
            verb, old, key = op.get('verb'), None, None
        row = L.verbs.get(verb) if isinstance(verb, str) else None
        if row is None:
            refuse(n, key, f"{verb!r} is no verb of the law")
            continue
        roles = op.get('roles')
        if not isinstance(roles, dict) or not roles:
            refuse(n, key, f"a `{verb}` is written with its roles")
            continue
        takes = set(row.get('roles') or {}) | set(row.get('qualifiers') or {}) | set(BESIDE)
        stray = sorted(set(roles) - takes)
        if stray:
            refuse(n, key, f"`{verb}` takes no {', '.join(stray)}: it takes {', '.join(sorted(takes - set(BESIDE)))}")
            continue
        why = _text_only(roles, verb)
        if why:
            refuse(n, key, why)
            continue
        missing = [r_ for r_ in _listed(row.get('required')) if r_ not in roles]
        if missing:
            refuse(n, key, f"`{verb}` requires {', '.join(missing)} — `unknown` where nobody said")
            continue
        if old is not None and isinstance(old.get('id'), str):
            sid = old['id']                      # a change keeps the statement's id
        else:                                    # one added, or one with no id changed: the id given, or one minted
            sid = op.get('id')
            if sid is not None and not (isinstance(sid, str) and _ID.match(sid) and sid not in ids):
                refuse(n, key, f"{sid!r} is no id this bean can give a statement: one kebab word, not yet used")
                continue
            sid = sid or _mint(ids, verb)
            ids.add(sid)
        sealed = old is not None and 'held' in old
        if sealed and not op.get('held', True):
            refuse(n, key, f"{key} is held off git: it is changed as held, or taken out — never written into the bean")
            continue
        wh = op.get('while', old.get('while') if old else None)
        if wh is not None and not isinstance(wh, str):
            refuse(n, key, "`while` names the statement it is held while: `<bean>#<id>`")
            continue
        if old is not None and not sealed and not op.get('held') and wh == old.get('while') and \
                {k: y for k, y in old.items() if k not in ('id', 'while')} == roles:
            continue                             # it says what the statement says already: nothing to write for it
        plan.append((n, op['op'], key, verb, {'id': sid, 'roles': dict(roles), 'held': bool(op.get('held') or sealed),
                                              'while': wh, 'old': old}))
    if refusals:
        return result(False)
    if not plan:
        refuse(None, None, "nothing to write: each op says what the bean says already")
        return result(False)

    # ---- 2. MAY THE WRITER WRITE IT: the whole bean, or each part an op touches
    whole = may('write', bean)
    if not whole:
        if new:
            refuse(None, None, f"{who} may not make a being here: a new being is the gardener's, or a grant's that opens it")
            return result(False)
        for n, act, key, verb, x in plan:
            if act == 'header':                  # the part a grant's `cover` names: a header key,
                part, fact, said_as = key, f"header:{key}", f"the {key}"
            elif act == 'add':                   # the verb of a statement added,
                part, fact, said_as = verb, f"{verb}#{x['id']}", f"a `{verb}`"
            else:                                # or the statement changed or taken out, by its id (else its verb)
                o = x if act == 'remove' else x['old']
                part = o['id'] if isinstance(o.get('id'), str) else verb
                fact, said_as = key, f"`{key}`"
            if not may('write', bean, [part]):
                refuse(n, fact, f"no grant opens {said_as} of {bean} to {who} to write — closed by default")
    if refusals:
        return result(False)

    # ---- 3. WRITE, THROUGH bin/safe.py; HELD VALUES SEALED BEFORE THEIR STATEMENT IS WRITTEN
    path = os.path.join(root, 'beans', bean + '.md')
    fm = dict(b.header) if b is not None else {'bean': bean, 'kind': kind}
    fm['statements'] = [{v: r} for _i, v, r in (b.items if b is not None else [])]
    said, entry = [], []

    def line(n, verb, x):
        roles = dict({'id': x['id']}, **x['roles'])
        if x['held']:
            seal, jl = dmheld.seal_core(bean, verb, x['id'], roles, fm, root=root, basis=x['while'])
            made.append(seal['held'])
            entry.append(jl)
            if x['old'] is not None and 'held' in x['old']:
                unseal_after.append(x['old']['held'])
            return f"- {verb}: {dmheld._flow(seal)}\n"
        if x['while'] is not None:
            roles['while'] = x['while']
        return f"- {verb}: {_flow(roles)}\n"
    try:
        if new:
            title = next((v for _n, a, h, v, _x in plan if a == 'header' and h == 'title'), None) or bean
            summary = next((v for _n, a, h, v, _x in plan if a == 'header' and h == 'summary'), None)
            tags = next((v for _n, a, h, v, _x in plan if a == 'header' and h == 'tags'), None)
            body = [f"- say: {{ by: {who}, at: now }}\n"] + [line(n, verb, x) for n, act, _k, verb, x in plan if act == 'add']
            head = f"---\nbean: {bean}\nkind: {kind}\ntitle: {json.dumps(title, ensure_ascii=False)}\n" + \
                   (f"summary: {json.dumps(summary, ensure_ascii=False)}\n" if summary else '') + \
                   (f"tags: {json.dumps(tags, ensure_ascii=False)}\n" if tags else '')
            safe.write_atomic(path, head + "statements:\n" + ''.join('  ' + s for s in body) + f"---\n{title}\n")
            entry.insert(0, f"- action: made [[{bean}]], a {kind}, from an empty sheet, by [[{who}]]" +
                         ''.join(f"; added `{verb}#{x['id']}`" for _n, act, _k, verb, x in plan if act == 'add') + '.')
        else:
            done = []
            for n, act, key, verb, x in plan:
                try:
                    if act == 'header':
                        h, v = key, verb
                        if h == 'tags':
                            if not v:
                                if 'tags' in b.header:
                                    safe.remove_block(path, 'tags')
                                    done.append("took out the tags")
                            elif 'tags' in b.header:
                                safe.replace_block(path, 'tags', f"tags: {json.dumps(v, ensure_ascii=False)}\n",
                                                   allow_remove=tuple(f"tags[{i}]" for i in range(len(b.header['tags']))))
                                done.append("changed the tags")
                            else:
                                safe.insert_after(path, 'summary' if 'summary' in b.header else 'title',
                                                  f"tags: {json.dumps(v, ensure_ascii=False)}\n")
                                done.append("wrote the tags")
                        elif h == 'summary' and not v:
                            if 'summary' in b.header:
                                safe.remove_block(path, 'summary')
                                done.append("took out the summary")
                        elif h in b.header:
                            safe.replace_block(path, h, f"{h}: {json.dumps(v, ensure_ascii=False)}\n",
                                               allow_remove=(h,))
                            done.append(f"changed the {h}")
                        else:
                            safe.insert_after(path, 'title', f"{h}: {json.dumps(v, ensure_ascii=False)}\n")
                            done.append(f"wrote a {h}")
                    elif act == 'remove':
                        sel = key if '#' in key else verb
                        safe.remove_statements(path, sel, expect=1)
                        done.append(f"removed `{key}`")
                        if 'held' in x:
                            unseal_after.append(x['held'])
                            entry.append(f"- held: {bean} {x.get('id')} erased")
                    elif act == 'change':
                        sel = key if '#' in key else verb
                        gone = (f"statements.{key}",)
                        safe.replace_statements(path, sel, line(n, verb, x), expect=1, allow_remove=gone)
                        said.append(x['id'])
                        done.append(f"changed `{key}`" + (f" (now `{verb}#{x['id']}`)" if '@' in key else ''))
                    else:
                        safe.add_statements(path, line(n, verb, x))
                        said.append(x['id'])
                        done.append(f"added `{verb}#{x['id']}`")
                except safe.UnsafeEdit as e:
                    refuse(n, key if act != 'header' else f"header:{key}", f"the edit is refused, nothing written: {e}")
                    raise
                except (ValueError, KeyError, dmheld.NotHere) as e:
                    refuse(n, key, f"it cannot be held here, nothing written: {e}")
                    raise
            if said:
                safe.add_statements(path, f"- say: {{ by: {who}, of: [{', '.join(said)}], at: now }}\n")
            entry.insert(0, f"- action: [[{bean}]] written from its sheet by [[{who}]]: {'; '.join(done)}.")
    except Exception as e:                              # what bin/safe.py or bin/held.py refused: undone, said
        if not refusals:
            refuse(None, None, f"nothing written: {e}")
        _undo(root, made)
        return result(False)

    # ---- 4. READ BACK, AND JUDGED BY THE GATE'S OWN JUDGE, STATEMENT BY STATEMENT
    G2 = engine.Garden.read(root)
    b2 = G2.beans.get(bean)
    if b2 is None or b2.unread:
        refuse(None, None, f"{bean} does not read back: {getattr(b2, 'unread', 'not there')}")
        _undo(root, made)
        return result(False)
    J = engine.Judge(L, G2)
    at = {r.get('id'): (i, v, r) for i, v, r in b2.items if isinstance(r, dict) and isinstance(r.get('id'), str)}
    for n, act, key, verb, x in plan:
        if act not in ('add', 'change'):
            continue
        hit = at.get(x['id'])
        if hit is None or hit[1] != verb:
            refuse(n, key or f"{verb}#{x['id']}", f"`{verb}#{x['id']}` does not read back from {bean}")
            continue
        i, v, r = hit
        if not x['held'] and {k: y for k, y in r.items() if k not in ('id', 'while')} != x['roles']:
            refuse(n, key or f"{verb}#{x['id']}", f"`{verb}#{x['id']}` reads back otherwise than it was written: "
                                                  f"{_flow({k: y for k, y in r.items() if k != 'id'})}")
            continue
        J.out = []
        J.one(b2, i, v, r)
        for rule, _where, msg in J.out:
            refuse(n, key or f"{verb}#{x['id']}", f"{rule}: {msg}")
    if refusals:
        _undo(root, made)
        return result(False)

    # ---- 5. ONE SAVE: one journal entry naming each statement, judged whole by the gate
    what = what or (f"{bean}, made from an empty sheet" if new else f"{bean}, written from its sheet")
    r = subprocess.run([sys.executable, os.path.join(root, 'bin', 'save.py'), who, what, '--body', *entry],
                       cwd=root, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=600)
    out = (r.stdout + r.stderr)[-6000:]
    if r.returncode != 0:
        _tie(out, bean, plan, at, refuse)
        _undo(root, made)
        return result(False, out)
    for p in unseal_after:                          # the record a changed held statement no longer points to
        try:
            dmheld.unwrite(p, root=root)
        except (dmheld.NotHere, ValueError, OSError):
            pass
    return result(True, out, _git(root, 'rev-parse', 'HEAD').stdout.strip())


def _tie(out, bean, plan, at, refuse):
    """Each finding of the gate's, tied to the op whose statement it names (`<bean>[<i>] <verb>`), else to none."""
    by_index = {i: x_id for x_id, (i, _v, _r) in at.items()}
    owner = {}
    for n, act, key, verb, x in plan:
        if act in ('add', 'change'):
            owner[x['id']] = (n, key or f"{verb}#{x['id']}")
    pat = re.compile(r'^(\S+)\s+(%s)(?:\[(\d+)\]|: statements\[(\d+)\])?[^:]*:\s*(.*)$' % re.escape(bean))
    tied = False
    for ln in out.splitlines():
        m = pat.match(ln.strip())
        if not m:
            continue
        i = m.group(3) or m.group(4)
        sid = by_index.get(int(i)) if i is not None else None
        n, fact = owner.get(sid, (None, None))
        refuse(n, fact, f"{m.group(1)}: {m.group(5)}")
        tied = True
    if not tied:
        refuse(None, None, "the gate refused the save — nothing kept")


def _undo(root, made):
    """The working tree and the index as they were before the write — the clone was clean, so every change is the
    write's — and every store record it made taken out."""
    import held as dmheld
    _git(root, 'reset', '-q')
    for ln in _git(root, 'status', '--porcelain', '-uall').stdout.splitlines():
        p = ln[3:]
        if ln.startswith('??'):
            try:
                os.remove(os.path.join(root, p))
            except OSError:
                pass
        else:
            _git(root, 'checkout', 'HEAD', '--', p)
    for p in made:
        try:
            dmheld.unwrite(p, root=root)
        except (dmheld.NotHere, ValueError, OSError):
            pass
