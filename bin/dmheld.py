#!/usr/bin/env python3
"""dmheld — what a garden keeps OFF git: the held layer (24.0; N30, F2, F13, S6).

    python3 bin/dmheld.py put <bean> <term> <key|index> [--root <name>] [--basis <bean>] [--until <date>]
    python3 bin/dmheld.py person [--root <name>] [--basis <bean>] <field>=<value> ...   # name=…, phone=…, email=…
    python3 bin/dmheld.py resolve <pointer> [--host <bean>]
    python3 bin/dmheld.py erase <person>
    python3 bin/dmheld.py check
    python3 bin/dmheld.py due [--days N]

A SEALED ENTRY is `{held: root:<name>/<32 hex>, basis?, until?}` in place of an entry's attributes (`held_form`). What
it held is a file `<store>/<32 hex>.yaml` holding `{bean, term, key, entry, about}`, where `<store>` is what THIS host's
`roots` entry `<name>` resolves to — a root that says what it `keeps`. The key is minted at random and says nothing.

GIT KEEPS ONLY THE POINTER: no hash, no name, no count. The gate never reads a store — a gate that fails on one
machine and passes on another is a gate people disable — so a store is checked where it is: here, by `check`, and
by bin/dmsave.py before every save.

ERASURE deletes every file the subject is in and writes the key to `<store>/ERASED`, which names no one: a pointer
to it then resolves to `Erased`, and one this host cannot reach to `NotHere`. Neither is an error of the bean.

A PERSON who is not the gardener and has not consented to be kept by name is written as `person` mints one: the id
`p-<8 hex>`, the title the id, one anchor `person:<id>`; the name and the ways to reach them held off git.

`put` and `erase` print the one journal line F13 asks for (`- held: <bean> <key> added|erased`): give it to
bin/dmsave.py's `--body`, and say no more of what was held.
"""
import os, re, secrets, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dmparse   # noqa: E402 — the one reader of a front matter
import dmpass    # noqa: E402 — sensitivity, and the gardener
import dmwhere   # noqa: E402 — this host, and what a root means on it
import yaml      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POINTER = re.compile(r'^root:([a-z0-9][a-z0-9-]*)/([0-9a-f]{32})$')


class NotHere(Exception):
    """No root on this host resolves the pointer: this host does not hold it."""


class Erased(Exception):
    """The material was erased for its subject; the pointer stays and says only that."""


def _host(root, host=None):
    beans = dmpass.beans_here(root)
    if host:
        return host, beans.get(host)
    return dmwhere.this_host(beans)


def stores(root=ROOT, host=None):
    """{root name: (path, row)} of every root this host declares a store (`keeps`)."""
    _hid, hfm = _host(root, host)
    out = {}
    for name, row in (dmwhere.roots_of(hfm) or {}).items():
        if isinstance(row, dict) and row.get('keeps'):
            path, _why = dmwhere.resolve('root:' + name, {name: row})
            if path:
                out[name] = (path, row)
    return out


def _file(pointer, root, host):
    m = POINTER.match(str(pointer))
    if not m:
        raise ValueError(f"{pointer!r} is not a held pointer — `root:<name>/<32 hex>`")
    st = stores(root, host).get(m.group(1))
    if not st:
        raise NotHere(f"this host declares no store `{m.group(1)}` — it does not hold {pointer}")
    return st[0], m.group(2)


def _erased(path):
    try:
        with open(os.path.join(path, 'ERASED'), encoding='utf-8') as fh:
            return {l.strip() for l in fh}
    except OSError:
        return set()


def resolve(pointer, *, root=ROOT, host=None):
    """What a pointer holds, `{bean, term, key, entry, about}` — or raises NotHere, or Erased."""
    path, key = _file(pointer, root, host)
    f = os.path.join(path, key + '.yaml')
    if not os.path.isfile(f):
        if key in _erased(path):
            raise Erased(f"{pointer} was erased for its subject")
        raise NotHere(f"{pointer}: the store `{pointer[5:].split('/')[0]}` is here and does not hold it")
    with open(f, encoding='utf-8') as fh:
        return yaml.safe_load(fh)


def _write(path, key, record):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, key + '.yaml'), 'w', encoding='utf-8', newline='\n') as fh:
        yaml.safe_dump(record, fh, allow_unicode=True, sort_keys=False)


def _pick(level, root, host, name=None):
    """The store for material of this level: the one named, or the first that keeps at least it."""
    st = stores(root, host)
    if name:
        if name not in st:
            raise NotHere(f"this host declares no store `{name}` (a `roots` entry with `keeps`)")
        path, row = st[name]
        if dmpass.LEVELS.index(row['keeps']) < dmpass.LEVELS.index(level):
            raise ValueError(f"the store `{name}` keeps {row['keeps']}, and this is {level}")
        return name, path
    for n, (path, row) in sorted(st.items()):
        if row.get('keeps') in dmpass.LEVELS and dmpass.LEVELS.index(row['keeps']) >= dmpass.LEVELS.index(level):
            return n, path
    raise NotHere(f"this host declares no store that keeps {level} material — a `roots` entry with `keeps: {level}`")


# ---- the bean's text: only the one term's block is rewritten, the rest of the file byte for byte ----
def _read_bean(root, bean):
    p = os.path.join(root, 'beans', bean + '.md')
    with open(p, encoding='utf-8') as fh:
        text = fh.read()
    return p, text


def _replace_term(text, term, value):
    """The text with top-level `term:` (and its indented block) rewritten as `value`, dumped in flow form."""
    lines = text.split('\n')
    end = lines.index('---', 1)
    i = next((n for n in range(1, end) if re.match(rf'^{re.escape(term)}:(\s|$)', lines[n])), None)
    if i is None:
        raise KeyError(term)
    j = i + 1
    while j < end and (lines[j].startswith((' ', '\t', '-')) or lines[j] == ''):
        j += 1
    if isinstance(value, dict):
        block = [f"{term}:"] + [f"  {k}: {_flow(v)}" for k, v in value.items()]
    else:
        block = [f"{term}:"] + [f"  - {_flow(v)}" for v in value]
    return '\n'.join(lines[:i] + block + lines[j:])


def _flow(v):
    """One value in the flow form a garden writes an entry in: `{ held: "root:vault/…", basis: { bean: b } }`."""
    import json
    if isinstance(v, dict):
        return '{ ' + ', '.join(f"{k}: {_flow(x)}" for k, x in v.items()) + ' }' if v else '{}'
    if isinstance(v, list):
        return '[ ' + ', '.join(_flow(x) for x in v) + ' ]' if v else '[]'
    if isinstance(v, bool) or v is None or isinstance(v, (int, float)):
        return yaml.safe_dump(v, default_flow_style=True).split('\n')[0].replace('...', '').strip()
    s = str(v)
    return s if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*', s) and not re.fullmatch(r'(?i)(true|false|null|yes|no|on|off|[0-9.eE+-]+)', s) \
        else json.dumps(s, ensure_ascii=False)


def put(bean, term, key, *, root=ROOT, host=None, store=None, basis=None, until=None):
    """Seal one entry of `term` on `bean` (a key of an open map, or an index of a list): its whole entry goes to a store
    here, and the bean keeps `{held, basis?, until?}`. Returns (pointer, the journal line)."""
    path_, text = _read_bean(root, bean)
    fm = dmparse.loads(dmparse.split_front_matter(text)[0])
    node = fm.get(term)
    if isinstance(node, dict):
        if key not in node:
            raise KeyError(f"{bean} has no {term}[{key}]")
        entry = node[key]
    elif isinstance(node, list):
        entry = node[int(key)]
    else:
        raise KeyError(f"{bean}.{term} is not a list or an open map of entries")
    level = dmpass.sensitivity(fm, types_law(root))[0]
    name, path = _pick(level, root, host, store)
    hexkey = secrets.token_hex(16)
    about = sorted({e.get('who') for e in fm.get('about') or [] if isinstance(e, dict)}
                   | ({bean} if fm.get('genos') == 'person' else set()))
    _write(path, hexkey, {'bean': bean, 'term': term, 'key': key, 'entry': entry, 'about': about})
    sealed = {'held': f"root:{name}/{hexkey}"}
    if basis:
        sealed['basis'] = {'bean': basis}
    if until:
        sealed['until'] = until
    if isinstance(node, dict):
        label = 'h-' + hexkey[:8]
        node = {(label if k == key else k): (sealed if k == key else v) for k, v in node.items()}
    else:
        label = f"{term}[{sealed['held']}]"
        node = [sealed if i == int(key) else v for i, v in enumerate(node)]
    with open(path_, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(_replace_term(text, term, node))
    return sealed['held'], f"- held: {bean} {term}.{label} added" if isinstance(fm.get(term), dict) else \
        f"- held: {bean} {term} added"


def types_law(root):
    """The law as sensitivity reads it: the registries, and the gardener."""
    import types
    import dmseq
    law = dmseq.Law.of_garden()          # the gate's reading of the law, a garden's additions included
    return types.SimpleNamespace(registry=law.registry, gardener=dmpass.gardener_of(root))


def person(fields, *, root=ROOT, host=None, store=None, basis=None):
    """Mint an opaque person `p-<8 hex>`: the bean in git says nothing of them; `fields` (a name, a phone, an e-mail)
    are held off git under their own subject. Returns the id."""
    while True:
        pid = 'p-' + secrets.token_hex(4)
        if not os.path.exists(os.path.join(root, 'beans', pid + '.md')):
            break
    name, path = _pick('personal', root, host, store)
    hexkey = secrets.token_hex(16)
    _write(path, hexkey, {'bean': pid, 'term': 'person', 'key': 'contact', 'entry': dict(fields), 'about': [pid]})
    g = dmpass.gardener_of(root) or 'keeper'
    with open(os.path.join(root, 'beans', pid + '.md'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(f"---\nbean: {pid}\ngenos: person\ntitle: \"{pid}\"\nstatus: active\n"
                 f"summary: \"a person whose name and contacts are held off git\"\nnature: empsychon\n"
                 f"owned_by: {{ legal: {{ crown: agape }} }}\nresponsibility: {{ legal: {{ self: true }} }}\n"
                 f"identity: {{ status: confirmed, anchors: [ {{ key: person_id, value: \"person:{pid}\", class: logical, "
                 f"establishing: true }} ] }}\n"
                 f"provenance: {{ src: asserted-by-human, by: {g}, as_of: now }}\n---\n"
                 f"Held: `root:{name}/{hexkey}`{' on ' + basis if basis else ''}.\n")
    return pid


def erase(subject, *, root=ROOT, host=None):
    """Delete every file of every store here that the subject is in; the keys go to `ERASED`. Returns the pointers."""
    gone = []
    for name, (path, _row) in sorted(stores(root, host).items()):
        for f in sorted(os.listdir(path)) if os.path.isdir(path) else []:
            if not f.endswith('.yaml'):
                continue
            try:
                with open(os.path.join(path, f), encoding='utf-8') as fh:
                    rec = yaml.safe_load(fh) or {}
            except (OSError, yaml.YAMLError):
                continue
            if rec.get('bean') == subject or subject in (rec.get('about') or []):
                os.remove(os.path.join(path, f))
                with open(os.path.join(path, 'ERASED'), 'a', encoding='utf-8', newline='\n') as fh:
                    fh.write(f[:-5] + '\n')
                gone.append(f"root:{name}/{f[:-5]}")
    return gone


def _pointers(fm):
    """(term, label, sealed entry) of every sealed entry — and the `held` of a series — a front matter holds."""
    for t, node in (fm or {}).items():
        items = node.items() if isinstance(node, dict) else enumerate(node) if isinstance(node, list) else []
        for label, e in items:
            if isinstance(e, dict) and isinstance(e.get('held'), str):
                yield t, label, e


def check(*, root=ROOT, host=None, beans=None):
    """[(level, text)]: each pointer resolves here, or is erased, or is another host's; each record is the entry the bean
    says it is; an `until` passed is warned. Where the store is, and nowhere else."""
    out = []
    for bid, fm in sorted((beans or dmpass.beans_here(root)).items()):
        for t, label, e in _pointers(fm):
            try:
                rec = resolve(e['held'], root=root, host=host)
            except Erased:
                continue
            except NotHere as x:
                out.append(('warn', f"{bid}: {t}[{label}] — {x}"))
                continue
            except ValueError as x:
                out.append(('error', f"{bid}: {t}[{label}] — {x}"))
                continue
            if not isinstance(rec, dict) or rec.get('bean') != bid or rec.get('term') != t:
                out.append(('error', f"{bid}: {t}[{label}] points at material held for another place "
                                     f"({rec.get('bean') if isinstance(rec, dict) else '?'})"))
    for bid, t, label, days in due(root=root, beans=beans, days=0):
        out.append(('warn', f"{bid}: {t}[{label}] was to be erased {-days} day(s) ago — bin/dmheld.py erase"))
    return out


def due(*, root=ROOT, beans=None, days=30):
    """[(bean, term, label, days left)] of sealed entries whose `until` falls within `days`."""
    import time
    import dmcal
    today = int(time.time() // 86400)
    out = []
    for bid, fm in sorted((beans or dmpass.beans_here(root)).items()):
        for t, label, e in _pointers(fm):
            if e.get('until') is None:
                continue
            try:
                left = dmcal.to_day(str(e['until'])) - today
            except Exception:
                continue
            if left <= days:
                out.append((bid, t, label, left))
    return out


def unresolved_new(*, root=ROOT):
    """The pointers the working tree's beans hold that HEAD's do not, and which do not resolve here: a save refuses
    them — material sealed on this host is on this host."""
    import subprocess
    bad = []
    for bid, fm in sorted(dmpass.beans_here(root).items()):
        r = subprocess.run(['git', '-C', root, 'show', f'HEAD:beans/{bid}.md'], capture_output=True, text=True,
                           encoding='utf-8', errors='replace')
        was = set()
        if r.returncode == 0:
            _f = dmparse.split_front_matter(r.stdout)[0]
            try:
                was = {e['held'] for _t, _l, e in _pointers(dmparse.loads(_f) if _f else {})}
            except Exception:
                was = set()
        for t, label, e in _pointers(fm):
            if e['held'] in was:
                continue
            try:
                resolve(e['held'], root=root)
            except (NotHere, Erased, ValueError) as x:
                bad.append(f"{bid}: {t}[{label}] — {x}")
    return bad


def _opt(argv, name, default=None):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1]
        del argv[i:i + 2]
        return v
    return default


def main(argv):
    argv = list(argv)
    if not argv or argv[0] in ('-h', '--help'):
        print(__doc__)
        return 0 if argv else 2
    cmd = argv.pop(0)
    store, basis, until, host = _opt(argv, '--root'), _opt(argv, '--basis'), _opt(argv, '--until'), _opt(argv, '--host')
    try:
        if cmd == 'put' and len(argv) == 3:
            ptr, line = put(*argv, store=store, basis=basis, until=until, host=host)
            print(f"sealed as {ptr}\njournal line (give it to bin/dmsave.py --body, and say no more of it):\n  {line}")
        elif cmd == 'person':
            fields = dict(a.split('=', 1) for a in argv if '=' in a)
            pid = person(fields, store=store, basis=basis, host=host)
            print(f"{pid}: written as beans/{pid}.md; its name and contacts are held off git")
        elif cmd == 'resolve' and len(argv) == 1:
            print(yaml.safe_dump(resolve(argv[0], host=host), allow_unicode=True, sort_keys=False).rstrip())
        elif cmd == 'erase' and len(argv) == 1:
            gone = erase(argv[0], host=host)
            print(f"erased {len(gone)} held record(s) for {argv[0]}; each pointer now resolves to Erased — git "
                  f"is unchanged, and a journal line, if any, says only `- held: {argv[0]} erased`")
        elif cmd == 'check':
            found = check(host=host)
            for lv, t in found:
                print(f"{lv.upper()}: {t}")
            print(f"held: {sum(1 for f in found if f[0] == 'error')} error(s), {sum(1 for f in found if f[0] == 'warn')} warning(s)")
            return 1 if any(f[0] == 'error' for f in found) else 0
        elif cmd == 'due':
            for b, t, l, d in due(days=int(_opt(argv, '--days', '30'))):
                print(f"{b}: {t}[{l}] — {'due in ' + str(d) + ' day(s)' if d >= 0 else str(-d) + ' day(s) past'}")
        else:
            print(__doc__)
            return 2
    except (NotHere, Erased, KeyError, ValueError) as x:
        print(f"dmheld: {x}", file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
