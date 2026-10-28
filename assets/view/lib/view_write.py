#!/usr/bin/env python3
"""view_write — the view's ONE write path: what a sheet's Save writes, and what a drawing's entry form of a verb adds
(the view finished for a handplace, design V1 §4 and §5). `view serve` calls it, and so may any host that serves a
garden's pages (a worker that imports this file from the release the garden runs): one implementation.

    write(root, who, bean, ops, kind=None, may=None, what=None) -> {ok, bean, commit, refusals, output}

`ops` is a list for one bean, each one of:
    {op: add,    verb, roles, id?, held?, while?, read?}  a statement appended; its id minted where it gives none
    {op: change, key, verb?, roles, held?, while?, read?}  the statement `key` names, rewritten in place
    {op: remove, key}                                      the statement `key` names, taken out
    {op: change, header: title | summary, value}           a header fact, rewritten (an empty summary is taken out)
    {op: change, header: tags, value: [words]}             the bean's tags, as a set (none: the key taken out)
    {op: held, key, entry}                                 a RECORD held off git the bean points to, on this host's store
                                                           (bin/held.py `records`): its fields by name, each one line,
                                                           a field given empty taken out; made where the bean has none
                                                           (`contact`, a person's, pointed to from the body; any other
                                                           from `details`) — opened by the held bar, its consent standing
`key` names a statement as bin/safe.py names it: `<verb>#<id>`, or `<verb>@<n>` for one with no id — changed or removed
only where it is the one statement of its verb. With `bean` None and `kind`, the ops make a NEW being of that kind:
its id minted opaque (`p-<8 hex>` for a person, its title the id; `<kind>-<8 hex>` for any other), its file written
whole.

WHAT HAPPENS, IN ORDER. The clone holds nothing uncommitted (its undo is git's). Each op is read against its verb's row:
the roles and qualifiers it takes, and text that is one line. `may(act, bean, positions)` is asked for the bean — and
where the whole is not open, for the part each op touches (the statement by its id, a verb for one added, `title` or
`summary`), as a grant's `cover` opens parts; and a held value, whatever the whole, only where a grant NAMES it (`held`:
the gardener aside, never by a grant of the whole bean). Each edit goes through bin/safe.py by its key with an expected count of 1;
a held value is sealed by bin/held.py before its statement is written, so what it says reaches the store and never the
bean's file. The statements added or changed are known by a `say` of the writer's, at `now` — or, where an op says the
writer read it from a source (`read: {from, through}`: a place a lookup found, from the map or the gazetteer that has
it), by a `read` of the writer's from that source, so the ledger says where the value came from (design §12). The bean
is read again,
each statement written is read back as intended and judged by the one judge, a statement alone (core/judge.py
`statement`), and
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


def _may_held(may, root, who, bean, part):
    """Whether `may` opens a held `part` of `bean` to write. A host's own `may` from before the naming rule cannot say
    it (it takes no `held`): then only the gardener, whom every law opens it to — the default is caution."""
    try:
        return bool(may('write', bean, [part], held=True))
    except TypeError:
        import importlib
        return who == importlib.import_module('pass').gardener_of(root)


def default_may(root, who):
    """The law's answer for the writer, where the caller gives none: bin/pass.py `may`."""
    import importlib
    dmpass = importlib.import_module('pass')

    def may(act, bean, positions=None, held=False):
        return dmpass.may(who, act, bean, positions=positions, root=root, held=held).granted
    return may


def write(root, who, bean, ops, kind=None, may=None, what=None):
    root = os.path.abspath(root)
    for p in (root, os.path.join(root, 'bin')):
        if p not in sys.path:
            sys.path.insert(0, p)
    import safe
    import held as dmheld
    from core import engine, judge as dmjudge
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
    plan, touched, asked = [], set(), []
    for n, op in enumerate(ops):
        if isinstance(op, dict) and op.get('op') == 'held':        # a record held off git: read below, by `_records`
            asked.append((n, op))
            continue
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
        rd = op.get('read')
        if rd is not None:                       # read from a source: `from` a being or someone, `through` one line
            frm = rd.get('from') if isinstance(rd, dict) else None
            source = isinstance(frm, str) or (isinstance(frm, dict) and isinstance(frm.get('someone'), str)
                                              and not _text_only(frm, 'read.from'))
            why = ("`read` says where the value was read: {from, through}" if not isinstance(rd, dict)
                   else _text_only(rd.get('through'), 'read.through')
                   or ('' if source else "`read.from` is the being the value was read from, or `{someone: <kind>}`"))
            if why:
                refuse(n, key, why)
                continue
        plan.append((n, op['op'], key, verb, {'id': sid, 'roles': dict(roles), 'held': bool(op.get('held') or sealed),
                                              'while': wh, 'old': old, 'read': rd}))
    rplan = _records(root, bean, b, asked, refuse, G, L) if asked else []
    if refusals:
        return result(False)
    if not plan and not rplan:
        refuse(None, None, "nothing to write: each op says what the bean says already")
        return result(False)

    # ---- 2. MAY THE WRITER WRITE IT: the whole bean, or each part an op touches — and a held value, only where a grant
    # NAMES it (bin/pass.py `may_core`, `held`): its statement's id, else its verb; never by a grant of the whole bean
    whole = may('write', bean)
    for n, act, key, verb, x in plan:
        if act == 'header':
            continue
        o = x if act == 'remove' else x['old']
        if not (act != 'remove' and x['held'] or o is not None and 'held' in o):
            continue
        part = o['id'] if o is not None and isinstance(o.get('id'), str) else verb
        if not _may_held(may, root, who, bean, part):
            refuse(n, key if act != 'add' else f"{verb}#{x['id']}",
                   f"what {key if act != 'add' else 'a `' + verb + '`'} holds is kept off git: only the gardener, or a grant "
                   f"that names it to {who}, opens it to write")
    for r_ in rplan:                             # a record held off git: by the part it is pointed to from
        if not _may_held(may, root, who, bean, r_['part']):
            refuse(r_['n'], f"held:{r_['key']}", f"what {bean} holds off git ({r_['key']}) is opened to write only to the "
                                               f"gardener, or to whom a grant names `{r_['part'].split('.')[0]}` of it")
    if refusals:
        return result(False)
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
            read_ids = {x['id'] for _n, act, _k, _v, x in plan if act == 'add' and x.get('read')}
            said_ids = [x['id'] for _n, act, _k, _v, x in plan if act == 'add' and not x.get('read')]
            body = ([f"- say: {{ by: {who}, of: [{', '.join(said_ids)}], at: now }}\n"] if read_ids and said_ids
                    else [] if read_ids else [f"- say: {{ by: {who}, at: now }}\n"]) + \
                [line(n, verb, x) for n, act, _k, verb, x in plan if act == 'add'] + reads(who, plan)
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
            for r_ in rplan:
                try:
                    done.append(_write_record(root, path, bean, b, r_, made, unseal_after, entry))
                except (safe.UnsafeEdit, ValueError, dmheld.NotHere) as e:
                    refuse(r_['n'], f"held:{r_['key']}", f"it cannot be held here, nothing written: {e}")
                    raise
            read_ids = {x['id'] for _n, act, _k, _v, x in plan if act in ('add', 'change') and x.get('read')}
            said = [i for i in said if i not in read_ids]
            if said:
                safe.add_statements(path, f"- say: {{ by: {who}, of: [{', '.join(said)}], at: now }}\n")
            for st in reads(who, plan):
                safe.add_statements(path, st)
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
    back = dmheld.records(os.path.join(root, 'beans', bean + '.md'), root=root) if rplan else []
    for r_ in rplan:                             # each record written reads back from where the bean points to it
        hit = next((x for x in back if x['pointer'] == r_['new']), None)
        if hit is None or (hit['record'] or {}).get('entry') != r_['record']['entry']:
            refuse(r_['n'], f"held:{r_['key']}", f"what {bean} holds off git ({r_['key']}) does not read back as written")
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
        for rule, _where, msg in dmjudge.statement(L, G2, b2, i, v, r, by=J):
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


_RKEY = re.compile(r'^[a-z][a-z0-9-]*$')
_FIELD = re.compile(r'^[a-z][a-z0-9_-]*$')


def _record_why(x, where, depth=0):
    """Why fields a person gave are not what a held record keeps — each field named by one word, each value one line of
    text, or a map of such one level down — or ''."""
    if not isinstance(x, dict):
        return f"`{where}` is its fields by name"
    for k, v in x.items():
        if not (isinstance(k, str) and _FIELD.match(k)):
            return f"{k!r} in `{where}` is no field's name: one word, lowercase"
        if isinstance(v, dict) and depth == 0:
            why = _record_why(v, f"{where}.{k}", 1)
        else:
            why = _text_only(v, f"{where}.{k}")
        if why:
            return why
    return ''


def _records(root, bean, b, asked, refuse, G, L):
    """The records a write's `held` ops change or make, read against what the bean points to on this host's store:
    [{n, key, part, old (pointer), record, store, basis}]. A record the bean points to that another host keeps, or that
    was erased, is written there or never again — never made a second time here. Where its consent is recorded (a
    body's `on <basis>`, a details entry's `basis`) it must still stand."""
    import held as dmheld
    from core import engine
    if b is None:
        for n, _op in asked:
            refuse(n, None, "what is held of a being is written once the being is made: save it first")
        return []
    recs = dmheld.records(os.path.join(root, 'beans', bean + '.md'), root=root)
    judge = engine.Judge(L, G)
    out = []
    for n, op in asked:
        key, given = op.get('key'), op.get('entry')
        if not (isinstance(key, str) and _RKEY.match(key)):
            refuse(n, None, "a held record is named by its key: one word, lowercase (`contact`)")
            continue
        fact = f"held:{key}"
        why = _record_why(given, key) or ('' if given else f"`{key}` is given no field")
        if why:
            refuse(n, fact, why)
            continue
        here = [r for r in recs if (r['record'] or {}).get('key') == key]
        if len(here) > 1:
            refuse(n, fact, f"{bean} points to `{key}` twice: which one is meant is the gardener's to say")
            continue
        if here:
            r = here[0]
            was = dict(r['record'].get('entry') or {})
            merged = dict(was)
            for k, v in given.items():
                if isinstance(v, dict):                  # a map one level down: a field in it given empty taken out
                    v = {a: y for a, y in v.items() if y not in ('', None)}
                if v in ('', None) or v == {}:
                    merged.pop(k, None)
                else:
                    merged[k] = v
            if merged == was:
                continue                         # it says what the record says already: nothing to write for it
            if not merged:
                refuse(n, fact, f"a held record keeps something: `{key}` is taken away by erasing it for its subject "
                                f"(bin/held.py erase), never emptied")
                continue
            if r['basis'] and r['basis'] not in G.beans and judge.statement(r['basis'], G.beans.get(bean)) is None:
                refuse(n, fact, f"the word `{key}` was kept on ({r['basis']}) no longer stands: nothing is written to it")
                continue
            out.append({'n': n, 'key': key, 'part': r['part'], 'old': r['pointer'], 'store': r['pointer'][5:].split('/')[0],
                        'basis': r['basis'], 'record': dict(r['record'], entry=merged)})
            continue
        body = key == 'contact'
        if any(r['here'] is not True and (r['part'] == 'body') == body for r in recs):
            refuse(n, fact, f"what {bean} holds off git is kept on another machine, or was erased: it is written there, "
                            f"and never made again here")
            continue
        if body and b.kind != 'person':
            refuse(n, fact, "a contact is a person's: their name and the ways to reach them")
            continue
        fields = {k: ({a: y for a, y in v.items() if y not in ('', None)} if isinstance(v, dict) else v)
                  for k, v in given.items()}
        fields = {k: v for k, v in fields.items() if not (v in ('', None) or v == {})}
        if not fields:
            refuse(n, fact, f"`{key}` is given no field")
            continue
        about = sorted(({bean} if b.kind == 'person' else set())
                       | {x for _i, v, r in b.items if v == 'concern' for x in _listed(r.get('of')) if isinstance(x, str)})
        out.append({'n': n, 'key': key, 'part': 'body' if body else 'details', 'old': None, 'store': None, 'basis': None,
                    'record': {'bean': bean, 'term': 'person' if body else 'details', 'key': key, 'entry': fields,
                               'about': about}})
    return out


def _write_record(root, path, bean, b, r, made, unseal_after, entry):
    """One record written: a new one in the store (the one the record it replaces is in), its pointer put where the bean
    points to it — the old pointer swapped for it, once and only once; a new contact a line of the body; a new record a
    label of `details` — and the record it replaces taken out once the write is saved. Says what it did."""
    import held as dmheld, safe
    import importlib
    dmpass = importlib.import_module('pass')
    level = dmpass.sensitivity(dict(b.header), None, dmpass.gardener_of(root))[0]
    # a being of no sensitivity is held at bin/held.py's own least level, its default
    p = dmheld.write_record(r['record'], root=root, store=r['store'], **({'level': level} if level != 'none' else {}))
    made.append(p)
    r['new'] = p
    if r['old']:
        def swap(text):
            if text.count(r['old']) != 1:
                raise safe.UnsafeEdit(f"{bean} names {r['old']} {text.count(r['old'])} times, not once")
            return text.replace(r['old'], p)
        safe.edit(path, swap)
        unseal_after.append(r['old'])
    elif r['part'] == 'body':
        safe.edit(path, lambda t: t.rstrip('\n') + f"\n\nHeld: `{p}`.\n")
    else:
        label = 'h-' + p.rsplit('/', 1)[1][:8]
        safe.edit(path, lambda t: _details_add(t, label, p))
        r['part'] = f"details.{label}"
    entry.append(f"- held: {bean} {r['key'] if r['part'] == 'body' else r['part']} added")
    return f"wrote `{r['key']}`, held off git ({len(r['record']['entry'])} field(s))"


def _details_add(text, label, pointer):
    """The bean's text with `details.<label>: { held: <pointer> }` added: under a `details:` block, or as one."""
    import safe
    lines = text.split('\n')
    close = next((i for i in range(1, len(lines)) if lines[i] == '---'), None)
    if close is None:
        raise safe.UnsafeEdit("no front matter to add it to")
    at = next((i for i in range(1, close) if lines[i].startswith('details:')), None)
    if at is None:
        lines[close:close] = ['details:', f'  {label}: {{ held: "{pointer}" }}']
    elif lines[at].strip() == 'details:':
        child = next((ln for ln in lines[at + 1:close] if ln.strip()), '')
        indent = len(child) - len(child.lstrip(' ')) or 2
        lines.insert(at + 1, ' ' * indent + f'{label}: {{ held: "{pointer}" }}')
    else:
        raise safe.UnsafeEdit("`details` is written in flow: a held record is added to it by hand")
    return '\n'.join(lines)


def reads(who, plan):
    """The `read` statements of a write: one for each source a value was read from, knowing each statement read from
    it (`of`), by the writer, at `now`."""
    by_source = {}
    for _n, act, _k, _verb, x in plan:
        if act in ('add', 'change') and x.get('read'):
            key = (_flow({'from': x['read']['from']}), x['read']['through'])
            by_source.setdefault(key, (x['read']['from'], []))[1].append(x['id'])
    return [f"- read: {_flow({'by': who, 'of': ids, 'from': frm, 'through': through, 'at': 'now'})}\n"
            for (_k, through), (frm, ids) in by_source.items()]


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
