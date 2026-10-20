#!/usr/bin/env python3
"""The storage profile (core 2.19; MODEL.md, Storage): where each content is kept, what its keepings leave open, which
folders hold one dataset, the events of a tree's contents, and a transfer as a course.

engine (core/storage.py): a gap's groups, a day spanning the whole of it; a camera's unset clock placed between its
dated neighbours; a content's keepings judged against a policy's risks, the way nearest to met and what it lacks; a
tree's fingerprint and its manifest, an empty folder no part of it, an unread content making none.
gate: a garden's risks held to their form (a keeping property of the law, a least count), only where it takes the
profile; a policy scheme's rows (risks it covers, a length of time, codes of a scheme). reckon: `keepings` over the
garden's statements — three disks, two places, one attached, a key held twice, two names of one inode counted once;
`datasets` — two folders holding one tree, its name the BLAKE3 of its manifest; `group` with `gap`. asset:
assets/storage/bin/storage.py over a store kept here gives the readings `keepings`, `datasets` and `events` the
store's way; transfer.py writes the walk, keeps a course, refuses a move the walk does not offer, and meets the need
when the course is done.

Run: python3 test/storage.py   (0 = green)
"""
import json, os, shutil, socket, sqlite3, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import formats, storage  # noqa: E402
import grow  # noqa: E402

FAILS = []
PY = sys.executable
B3 = {n: (n * 64)[:64] for n in 'abcdef'}            # contents' digests, invented


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None, env=None):
    e = dict(grow.ENV, **(env or {}))
    p = subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e)
    return p.returncode, p.stdout + p.stderr


def write(path, t):
    p = os.path.join(G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def bean(bid, kind, *statements):
    write(f'beans/{bid}.md', f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{bid}\"\nsummary: \"{bid}, invented.\"\n"
                             "statements:\n  - say: { by: sam, at: now }\n" + ''.join(f"  - {s}\n" for s in statements)
          + f"---\n{bid}, invented.\n")


def gate():
    _rc, out = run(PY, 'core/check.py', '.')
    return [ln for ln in out.splitlines() if ln and not ln.startswith('core check')]


def reading(name, body, *args):
    path = os.path.join(T, f'{name}.yaml')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(body)
    return run(PY, 'bin/reckon.py', '--ad-hoc', path, *args)


VOCAB = """---
profiles: [storage, knowledge]
kinds:
  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }
risks:
  - { risk: disk-fault, meaning: "a disk stops reading", resolved_by: [ { disk: 2 }, { array: 1 } ] }
  - { risk: site-loss, meaning: "a place is lost to fire, flood or theft", resolved_by: [ { place: 2 } ] }
  - { risk: malice, meaning: "a program writes over every disk it reaches", resolved_by: [ { offline: 1 }, { immutable: 1 } ] }
  - { risk: decay, meaning: "bytes change unseen", resolved_by: [ { verified: 2 } ] }
  - { risk: key-loss, meaning: "the key to an encrypted keeping is lost", resolved_by: [ { key: 1 } ] }
schemes:
  - { scheme: keep, classifies: "what a content must be safe against", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/keep", levels: [ { level: code } ], neighbours: none, sources: extracts/keep.tsv, form: keep }
  - { scheme: media, classifies: "what a picture is", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/media", levels: [ { level: class } ], neighbours: none, sources: extracts/media.tsv, form: class }
  - { scheme: schemas, classifies: "where the members of a directory belong", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/schemas", levels: [ { level: schema }, { level: node } ], neighbours: none, sources: extracts/schemas.tsv, form: schema }
files:
  - { registry: keep, file: extracts/keep.tsv, key: code }
  - { registry: media, file: extracts/media.tsv, key: code }
  - { registry: schemas, file: extracts/schemas.tsv, key: code }
---
# the garden's own rows
"""
SCHEMAS = ('code\tlevel\tparent\tname\ttemplate\tmatches\tlinks\tversions\tage\tgap\n'
           'bx\tschema\t\ta box\t\t\t\t\t\t36 h\n'
           'blobs\tnode\tbx\tevery content once\t.blobs/{blake3}\t\ttrue\t\t\t\n'
           'days\tnode\tbx\tby the day it was made\tDays/{day:yyyy-mm-dd}/{name}\t\ttrue\t\t\t\n')
KEEP = ('code\tlevel\tname\tcovers\twithin\tfor\n'
        'precious\tcode\tkept against all\tdisk-fault site-loss malice decay key-loss\t365 d\tmedia:raw\n'
        'replaceable\tcode\tnone needed\t\t\t\n')

T = tempfile.mkdtemp(prefix='storage-')
G = os.path.join(T, 'g')
try:
    # ---- THE ENGINE, pure
    g = storage.gap_groups([(0, 0, 'a'), (3600, 3600, 'b'), (3600 * 40, 3600 * 40, 'c'), (3600 * 40, 3600 * 64, 'd'),
                            (3600 * 101, 3600 * 101, 'e')], 36 * 3600)
    check("engine: a new group wherever the time from the group so far to the next is longer than the gap; a day spans "
          "the whole of it, so the next is measured from its end", g == [['a', 'b'], ['c', 'd'], ['e']], g)
    pl = storage.placed_between([(1, 'p1'), (2, 'p2'), (3, 'p3'), (4, 'p4')], {'p1': 1, 'p4': 4}.get)
    check("engine: a picture whose camera's clock was never set is placed between its dated neighbours in the run",
          pl == {'p2': ('p1', 'p4'), 'p3': ('p1', 'p4')}, pl)
    K = storage.Keeping
    risks = {'disk-fault': [{'disk': 2}, {'array': 1}], 'malice': [{'offline': 1}], 'decay': [{'verified': 2}]}
    one = [K('v1', {'d1'}, verified=900)]
    j = storage.judge(one, risks, ['disk-fault', 'malice', 'decay'], within=200, now=1000)
    check("engine: one keeping on one attached disk leaves a disk's fault, malice and decay open, each with the way "
          "nearest to met and what it lacks",
          j['resolved'] == [] and [(e['risk'], e['lacks']) for e in j['open']] ==
          [('disk-fault', {'disk': 1}), ('malice', {'offline': 1}), ('decay', {'verified': 1})]
          and 'malice: 1 more keeping offline' in storage.lacking(j['open'][1]), j)
    two = one + [K('v2', {'d2'}, offline=True, verified=950)]
    j = storage.judge(two, risks, ['disk-fault', 'malice', 'decay'], within=200, now=1000)
    check("engine: a second keeping on another disk, offline and found whole since resolves all three",
          j['resolved'] == ['disk-fault', 'malice', 'decay'] and not j['open'], j)
    j = storage.judge(two, risks, None)
    check("engine: with no policy a content is read for what its keepings resolve, and judged against nothing",
          j['open'] == [] and 'disk-fault' in j['resolved'], j)
    tr = storage.Trees({'x': None, 'xs': 'x', 'y': None, 'ys': 'y', 'empty': 'y', 'z': None},
                       [('x', b'a.txt', B3['a'], 3), ('xs', b'b.txt', B3['b'], 3), ('y', b'a.txt', B3['a'], 3),
                        ('ys', b'b.txt', B3['b'], 3), ('z', b'a.txt', None, 3)],
                       {'xs': b'sub', 'ys': b'sub', 'empty': b'nothing'})
    check("engine: two trees alike — the same names and contents, an empty folder no part of either — share a "
          "fingerprint and a manifest; a tree holding an unread content has neither",
          tr.fingerprint('x') == tr.fingerprint('y') and tr.fingerprint('x') and tr.fingerprint('z') is None
          and tr.manifest('x') == (B3['a'] + '  a.txt\n' + B3['b'] + '  sub/b.txt\n').encode(), tr.manifest('x'))

    nodes = [('blobs', None, {}), ('captured', None, {'matches': 'media:raw'}), ('apart', None, {'matches': 'roles:placed'})]
    ap = {'roles:placed'}
    check("engine: in a box a member is at every node it matches — but one holding a code that sets apart only at the "
          "nodes that match such a code, and at a node every member is at (core 2.23)",
          [n for n, _l, _r in storage.belongs(nodes, ['media:raw'], True, ap)] == ['blobs', 'captured']
          and [n for n, _l, _r in storage.belongs(nodes, ['media:raw', 'roles:placed'], True, ap)] == ['blobs', 'apart']
          and [n for n, _l, _r in storage.belongs(nodes, ['media:raw', 'roles:placed'], True)] == ['blobs', 'captured', 'apart'],
          storage.belongs(nodes, ['media:raw', 'roles:placed'], True, ap))
    import importlib.util
    spec = importlib.util.spec_from_file_location('storage_asset', os.path.join(ROOT, 'assets', 'storage', 'bin', 'storage.py'))
    SA = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(SA)
    check("asset: a copy's source read from its `make`'s `from`, a list kept as JSON the store may hand back as bytes",
          SA.made_from(b'["d-1#hold-2"]') == ['d-1#hold-2'] and SA.made_from('["d-1#hold-2"]') == ['d-1#hold-2']
          and SA.made_from('d-1#hold-2') == ['d-1#hold-2'] and SA.made_from(None) == [], SA.made_from(b'["d-1#hold-2"]'))

    # ---- A GARDEN: the gate
    rel = grow.release(os.path.join(T, 'release'))
    r = grow.garden(rel, G, 'sam', '--profile', 'storage', '--profile', 'knowledge')
    check("garden: grown with the storage profile, which brings its asset", r.returncode == 0
          and os.path.isfile(os.path.join(G, 'assets', 'storage', 'bin', 'storage.py')), r.out[-800:])
    write('VOCAB.md', VOCAB)
    write('extracts/keep.tsv', KEEP)
    write('extracts/media.tsv', 'code\tlevel\tname\nraw\tclass\ta camera\'s raw file\n')
    write('extracts/schemas.tsv', SCHEMAS)
    def gate():                                     # the walk's kind is used once the walk is written, below
        _rc, out = run(PY, 'core/check.py', '.')
        return [ln for ln in out.splitlines() if ln and not ln.startswith('core check') and '`procedure`' not in ln]
    check("gate: a garden's risks and its policy scheme pass", gate() == [], gate())
    write('VOCAB.md', VOCAB.replace('{ disk: 2 }, { array: 1 }', '{ disk: 0 }, { tape: 1 }'))
    found = gate()
    check("gate: a risk resolved by no keeping property of the law, or by a count that is no whole number from 1, "
          "is refused by name", any('`tape` is no keeping property' in f for f in found)
          and any('a least count' in f for f in found), found)
    write('VOCAB.md', VOCAB)
    write('extracts/keep.tsv', KEEP.replace('disk-fault site-loss', 'disk-fault flood').replace('365 d', 'a year'))
    found = gate()
    check("gate: a policy covering a risk the garden has not, or kept within no length of time, is refused",
          any("'flood' is no row of `risks`" in f for f in found) and any('no length of time' in f for f in found),
          found)
    write('extracts/keep.tsv', KEEP)
    write('extracts/schemas.tsv', SCHEMAS.replace('Days/{day:yyyy-mm-dd}/{name}', 'Days/{day:yy}/{place}')
          + 'stray\tnode\tnobody\tno schema\tX/{name}\t\tmaybe\t\t\t\n')
    found = gate()
    check("gate: a schema's node whose slot is no row of `layout_slots`, or in no form its slot has, a node of no "
          "schema, and `links` that is not `true` are refused by name",
          any("{place} names no slot" in f for f in found) and any("`day` is written in" in f for f in found)
          and any("parent: 'nobody'" in f for f in found) and any("links: 'maybe'" in f for f in found), found)
    write('extracts/schemas.tsv', SCHEMAS)
    write('VOCAB.md', VOCAB.replace('profiles: [storage, knowledge]', 'profiles: [knowledge]')
          .replace('form: keep', 'form: class').replace('form: schema', 'form: class')
          .replace('  - { registry: keep, file: extracts/keep.tsv, key: code }\n', ''))
    found = gate()
    check("gate: a garden that does not take the storage profile has no risks of its own",
          any("storage profile's, which this garden does not take" in f for f in found), found)
    write('VOCAB.md', VOCAB)

    # ---- the garden's statements: three disks, two places, a key held twice, two names of one inode
    me = socket.gethostname().lower().split('.')[0]
    write('beans/nas.md', f"---\nbean: nas\nkind: host\ntitle: \"nas\"\nsummary: \"nas, invented.\"\nstatements:\n"
                          f"  - say: {{ by: sam, at: now }}\n  - name: {{ by: dns, of: self, as: \"{me}.example.org\" }}\n"
                          f"details:\n  roots:\n    test:\n      system: unix-filesystem\n      at: \"{me}:{T}\"\n"
                          f"  stores:\n    cat:\n      at: \"root:test/cat.sqlite\"\n      form: sqlite\n---\nnas, invented.\n")
    bean('disk-a', 'host', 'part: { by: self, of: nas }', 'be: { by: self, at: "geohash:tnke13", as: location }',
         'hold: { by: self, of: vol-a }')
    bean('disk-b', 'host', 'be: { by: self, at: "geohash:tnke13", as: location }', 'hold: { by: self, of: vol-b }')
    bean('disk-c', 'host', 'be: { by: self, at: "geohash:sxk9b2", as: location }', 'hold: { by: self, of: vol-c }',
         'need: { by: self, of: key-c }')
    bean('key-c', 'document', 'hold: { by: nas, of: self }', 'hold: { by: sam, of: self }')
    for v in 'abc':
        bean(f'vol-{v}', 'volume')
    bean('vol-a', 'volume', 'hold: { id: i1, by: self, of: c-2 }')
    bean('d-a', 'folder', 'part: { by: self, of: vol-a }', 'hold: { by: self, of: c-1, as: "IMG_1.CR2" }',
         'hold: { by: self, of: c-2, as: "IMG_2.CR2", through: "vol-a#i1" }',
         'hold: { by: self, of: c-2, as: "IMG_2 copy.CR2", through: "vol-a#i1" }')
    bean('d-b', 'folder', 'part: { by: self, of: vol-b }', 'hold: { by: self, of: c-1, as: "IMG_1.CR2" }')
    bean('d-c', 'folder', 'part: { by: self, of: vol-c }', 'hold: { by: self, of: c-1, as: "IMG_1.CR2" }')
    bean('d-b2', 'folder', 'part: { by: self, of: vol-b }', 'hold: { by: self, of: c-3, as: "notes.txt" }',
         'classify: { of: self, as: "keep:replaceable" }')
    for c, x in (('c-1', 'a'), ('c-2', 'b'), ('c-3', 'c')):
        bean(c, 'content', f'name: {{ by: blake3, of: self, as: "{B3[x]}" }}')
    bean('c-1', 'content', f'name: {{ by: blake3, of: self, as: "{B3["a"]}" }}', 'classify: { of: self, as: "media:raw" }')
    bean('c-2', 'content', f'name: {{ by: blake3, of: self, as: "{B3["b"]}" }}', 'classify: { of: self, as: "media:raw" }')
    # two folders holding one tree, a third another
    for x in 'xyz':
        bean(f'd-{x}', 'folder', 'part: { by: self, of: vol-a }', f'hold: {{ by: self, of: c-4, as: "a.txt" }}')
        bean(f'd-{x}s', 'folder', f'part: {{ by: self, of: d-{x} }}', f'name: {{ by: d-{x}, of: self, as: sub }}',
             f'hold: {{ by: self, of: {"c-5" if x != "z" else "c-6"}, as: "b.txt" }}')
    for c, x in (('c-4', 'd'), ('c-5', 'e'), ('c-6', 'f')):
        bean(c, 'content', f'name: {{ by: blake3, of: self, as: "{B3[x]}" }}')
    found = gate()
    check("gate: the disks, volumes, folders and contents — two names of one inode held through its one holding — pass",
          found == [], found)

    rc, out = reading('keepings', 'what: "what each content\'s keepings leave open"\ninputs:\n'
                                  '  - { name: scheme, origin: { act: say }, type: kebab }\nsteps:\n'
                                  '  - { id: contents, op: select, kind: content, where: [ { path: bean, "∈": [c-1, c-2, c-3] } ] }\n'
                                  '  - { id: open, op: keepings, of: contents, scheme: { input: scheme } }\n',
                      '--input', 'scheme=keep')
    check("reckon: `keepings` — a raw picture on three disks at two places, two of them offline, the encrypted one's "
          "key held twice, leaves only decay open: nothing says it was found whole since",
          rc == 0 and 'keep:precious · decay: 2 more keepings found whole within the policy' in out, out[-1500:])
    check("...one held on one attached disk under two names of one inode is one keeping, and leaves a disk's fault, the "
          "place and malice open too, each with what would close it",
          'disk-fault: 1 more keeping on another disk' in out and 'site-loss: 1 more keeping at another place' in out
          and 'malice: 1 more keeping offline' in out, out[-1500:])
    check("...and what a root its folder is classed by covers nothing is safe", 'keep:replaceable · safe' in out,
          out[-1500:])
    rc, out = reading('datasets', 'what: "the folders that hold one tree"\nsteps:\n'
                                  '  - { id: folders, op: select, kind: folder, where: [ { path: bean, "∈": [d-x, d-y, d-z] } ] }\n'
                                  '  - { id: trees, op: datasets, of: folders }\n')
    man = (B3['d'] + '  a.txt\n' + B3['e'] + '  sub/b.txt\n').encode()
    try:
        name = formats.blake3_hex(man)
    except formats.Refused:
        name = None
    check("reckon: `datasets` — two folders holding the same tree are one dataset, named by its manifest's BLAKE3; a "
          "third with another content is another",
          rc == 0 and (name is None or f"{name}: 2 member(s): d-x, d-y" in out) and '1 member(s): d-z' in out,
          (name, out[-1500:]))
    bean('c-1', 'content', f'name: {{ by: blake3, of: self, as: "{B3["a"]}" }}', 'classify: { of: self, as: "media:raw" }',
         'produce: { by: nas, of: self, at: "2026-10-01T10:00:00+00:00" }')
    bean('c-2', 'content', f'name: {{ by: blake3, of: self, as: "{B3["b"]}" }}', 'classify: { of: self, as: "media:raw" }',
         'produce: { by: nas, of: self, at: "2026-10-02T09:00:00+00:00" }')
    bean('c-3', 'content', f'name: {{ by: blake3, of: self, as: "{B3["c"]}" }}',
         'produce: { by: nas, of: self, at: "2026-10-05T09:00:00+00:00" }')
    rc, out = reading('events', 'what: "the events"\nzone: Etc/UTC\nsteps:\n'
                                '  - { id: made, op: select, kind: content, entries: produce }\n'
                                '  - { id: events, op: group, of: made, path: at, gap: "36 h" }\n')
    check("reckon: `group` with a gap — two pictures 23 hours apart are one event, a third three days on another",
          rc == 0 and '2026-10-01T10:00:00Z–2026-10-02T09:00:00Z' in out and '2026-10-05T09:00:00Z' in out, out[-1200:])

    bean('d-a', 'folder', 'part: { by: self, of: vol-a }', 'hold: { by: self, of: c-1, as: "IMG_1.CR2" }',
         'hold: { by: self, of: c-2, as: "IMG_2.CR2", through: "vol-a#i1" }',
         'hold: { by: self, of: c-2, as: "IMG_2 copy.CR2", through: "vol-a#i1" }',
         'classify: { of: self, as: "schemas:bx" }')
    rc, out = reading('layout', 'what: "the folder against its schema"\ninputs:\n'
                                '  - { name: scheme, origin: { act: say }, type: kebab }\nsteps:\n'
                                '  - { id: folders, op: select, kind: folder, where: [ { path: bean, "=": d-a } ] }\n'
                                '  - { id: placed, op: layout, of: folders, scheme: { input: scheme } }\n',
                      '--input', 'scheme=schemas')
    check("reckon: `layout` — a folder a box's schema is said of: each content's blob and its day's name to link, read "
          "from the garden's statements", rc == 0 and 'd-a · blobs · to link' in out and 'd-a · days · to link' in out,
          out[-1200:])

    # ---- THE ASSET over a store
    import store as dmstore
    sp = os.path.join(T, 'cat.sqlite')
    S = dmstore.Store(sp, root=G)
    S.being('nas', 'host') if not S.has_bean('nas') else None
    S.being('vol-s', 'volume')
    S.put('vol-s', 'read', {'id': 'scan', 'by': 'nas', 'from': 'vol-s', 'at': '2026-10-18T10:00:00+03:00'})
    A = 'vol-s#scan'
    S.put('disk-a', 'hold', {'by': 'disk-a', 'of': 'vol-s'}, act=A, judge=False)
    for f, parent, name in (('d-s1', 'vol-s', 'Photos'), ('d-s2', 'd-s1', '2026-10-01'), ('d-s3', 'vol-s', 'Copy'),
                            ('d-s4', 'd-s3', 'Photos'), ('d-s5', 'd-s4', '2026-10-01')):
        S.being(f, 'folder')
        S.put(f, 'part', {'by': f, 'of': parent}, act=A)
        S.put(f, 'name', {'by': parent, 'of': f, 'as': name}, act=A)
    for c, x in (('c-s1', 'a'), ('c-s2', 'b')):
        S.being(c, 'content')
        S.put(c, 'name', {'by': 'blake3', 'of': c, 'as': B3[x]}, act=A)
        S.put(c, 'measure', {'of': c, 'as': 'information', 'value': {'count': '3', 'unit': 'By'}}, act=A)
    for f in ('d-s2', 'd-s5'):
        S.put(f, 'hold', {'by': f, 'of': 'c-s1', 'as': 'IMG_0001.JPG'}, act=A)
        S.put(f, 'hold', {'by': f, 'of': 'c-s2', 'as': 'IMG_0002.JPG'}, act=A)
    S.being('c-zip', 'content')                       # a container on the disk, read as a volume of its own
    S.put('c-zip', 'name', {'by': 'blake3', 'of': 'c-zip', 'as': 'f' * 64}, act=A)
    S.being('d-s6', 'folder')
    S.put('d-s6', 'part', {'by': 'd-s6', 'of': 'vol-s'}, act=A)
    S.put('d-s6', 'name', {'by': 'vol-s', 'of': 'd-s6', 'as': 'Archives'}, act=A)
    S.put('d-s6', 'hold', {'by': 'd-s6', 'of': 'c-zip', 'as': 'old.zip'}, act=A)
    S.being('ct-zip', 'volume')
    S.put('ct-zip', 'hold', {'by': 'c-zip', 'of': 'ct-zip'}, act=A, judge=False)
    for i, c in enumerate(('c-m1', 'c-m2', 'c-m3')):
        S.being(c, 'content')
        S.put('ct-zip', 'hold', {'by': 'ct-zip', 'of': c, 'as': f'member{i}.txt'}, act=A)
    S.close()
    ST = os.path.join('assets', 'storage', 'bin', 'storage.py')
    rc, out = run(PY, ST, 'datasets', '--store', sp, '--same', '--json')
    rows = json.loads(out[:out.rindex(']') + 1]) if rc == 0 and ']' in out else []
    check("asset: `datasets` over a store — the folder copied beside its first is the same dataset, and so is each "
          "day beneath them", rc == 0 and len(rows) == 2 and all(len(r['folders']) == 2 for r in rows)
          and any(set(r['folders']) == {'d-s1', 'd-s4'} for r in rows), out[-1200:])
    rc, out = run(PY, ST, 'events', '--store', sp, '--of', 'vol-s', '--gap', '36 h')
    check("asset: `events` over a store — a content with no moment of its own takes the day its folder's name holds",
          rc == 0 and '2026-10-01 00:00Z–2026-10-01 23:59Z · 2' in out and '1 contents with no moment' in out, out[-800:])
    rc, out = run(PY, ST, 'keepings', '--store', sp, '--scheme', 'keep', '--of', 'vol-s')
    check("asset: `keepings` over a store — two contents kept twice and a container once, on one attached disk; no "
          "policy said of them", rc == 0 and 'no policy · 3 contents' in out, out[-800:])
    rc, out = run(PY, ST, 'keepings', '--store', sp, '--of', 'ct-zip', '--json')
    j = json.loads(out[:out.rindex('}') + 1]) if rc == 0 and '}' in out else {}
    check("asset: `keepings` of a container's volume — each member, kept on the disk its container is kept on",
          rc == 0 and len(j.get('contents') or []) == 3
          and all(k['disks'] == ['disk-a'] for c in j['contents'] for k in c['keepings']), out[-800:])
    rc, out = run(PY, ST, 'manifest', 'd-s1', '--store', sp)
    check("asset: `manifest` — a folder's tree as checksum lines, sorted, the day folder's path before each name",
          rc == 0 and out.startswith(B3['a'] + '  2026-10-01/IMG_0001.JPG\n' + B3['b'] + '  2026-10-01/IMG_0002.JPG\n'),
          out[-600:])

    # ---- a box: one flat folder of blobs, and a schema of links to them, read from the store and made
    box = os.path.join(T, 'box')
    os.makedirs(os.path.join(box, 'Photos', '2026-10-01'))
    S = dmstore.Store(sp, root=G)
    S.being('vol-box', 'volume')
    S.put('vol-box', 'read', {'id': 'scan', 'by': 'nas', 'from': 'vol-box', 'at': '2026-10-18T10:00:00+03:00'})
    AB = 'vol-box#scan'
    db1, db2 = formats.folder_id('vol-box', b'Photos'), formats.folder_id('vol-box', b'Photos/2026-10-01')
    for f, parent, name in ((db1, 'vol-box', 'Photos'), (db2, db1, '2026-10-01')):
        S.being(f, 'folder')
        S.put(f, 'part', {'by': f, 'of': parent}, act=AB)
        S.put(f, 'name', {'by': parent, 'of': f, 'as': name}, act=AB)
    hs = {}
    for nm, data in (('IMG_0001.JPG', b'abc'), ('IMG_0002.JPG', b'abcd')):
        with open(os.path.join(box, 'Photos', '2026-10-01', nm), 'wb') as fh:
            fh.write(data)
        h = hs[nm] = formats.blake3_hex(data)
        c = formats.content_id(h)
        if not S.kind_of(c):
            S.being(c, 'content')
        S.put(c, 'name', {'by': 'blake3', 'of': c, 'as': h}, act=AB)
        S.put(db2, 'hold', {'by': db2, 'of': c, 'as': nm}, act=AB)
    S.close()
    bean('box-schemas', 'document', 'classify: { of: "store:volume:vol-box", as: "schemas:bx" }')
    BX = os.path.join('assets', 'storage', 'bin', 'box.py')
    rc, out = run(PY, ST, 'layout', '--store', sp, '--of', 'vol-box', '--scheme', 'schemas', '--json')
    j = json.loads(out[:out.rindex('}') + 1]) if rc == 0 and '}' in out else {}
    check("box: `layout` of a box against the schema said of it — each content's blob and its day's name to link, the "
          "names it holds now given by no node of it",
          rc == 0 and j.get('box') and j['nodes'].get('blobs', {}).get('to link') == 2
          and j['nodes'].get('days', {}).get('to link') == 2
          and j['nodes'].get('(names no node gives)', {}).get('out of place') == 2, out[-1200:])
    plan = os.path.join(T, 'plan.jsonl')
    rc1, _ = run(PY, BX, 'plan', '--store', sp, '--of', 'vol-box', '--scheme', 'schemas', '--out', plan)
    rc2, out2 = run(PY, BX, 'link', '--plan', plan, '--root', box, '--store', sp, '--of', 'vol-box')
    blob = os.path.join(box, '.blobs', hs['IMG_0001.JPG'])
    day = os.path.join(box, 'Days', '2026-10-01', 'IMG_0001.JPG')
    first = os.path.join(box, 'Photos', '2026-10-01', 'IMG_0001.JPG')
    check("box: `link` makes each blob of a name that holds it and each name the schema gives, all one inode — no "
          "byte copied — and the blob read-only",
          rc1 == 0 and rc2 == 0 and os.path.isfile(blob) and os.path.samefile(blob, day) and os.path.samefile(blob, first)
          and not (os.stat(blob).st_mode & 0o222), out2[-800:])
    rc, out = run(PY, BX, 'verify', '--root', box)
    check("box: `verify` reads every blob's bytes against its name", rc == 0 and '2 blobs read: 0 not' in out, out[-400:])
    rc, out = run(PY, ST, 'layout', '--store', sp, '--of', 'vol-box', '--scheme', 'schemas', '--json')
    j = json.loads(out[:out.rindex('}') + 1]) if rc == 0 and '}' in out else {}
    S = dmstore.Store(sp, root=G)
    thr = S.db.execute("SELECT count(*) FROM v_hold WHERE t_through LIKE 'vol-box#i%'").fetchone()[0]
    S.close()
    check("box: read again, each blob and each day's name is in place, the names it held before stay, and every name "
          "of one inode is held through the volume's one holding of it",
          rc == 0 and j['nodes']['blobs']['in place'] == 2 and j['nodes']['days']['in place'] == 2
          and j['nodes']['(names no node gives)']['out of place'] == 2 and thr == 6, (thr, out[-1000:]))
    rc, out = run(PY, BX, 'link', '--plan', plan, '--root', box)
    check("box: the same plan again makes nothing, and refuses nothing", rc == 0 and '"blobs": 0, "names": 0, "refused": 0'
          in out, out[-400:])

    # ---- the full path beneath a volume (core 2.22): imported, then read by a pattern row over the whole path
    vocab_paths = VOCAB.replace("files:\n", "  - { scheme: names, classifies: \"what a name says\", holding: extract, licence: "
                                "CC0-1.0, publisher: the gardener, url: \"https://example.org/names\", levels: [ { level: "
                                "pattern } ], neighbours: none, sources: extracts/names.tsv, form: pattern }\nfiles:\n  - { "
                                "registry: names, file: extracts/names.tsv, key: code }\n")
    write('VOCAB.md', vocab_paths)
    write('extracts/names.tsv', 'code\tlevel\tparent\tname\ttemplate\treads\tsuggests\tmatch\n'
                                'dcim\tpattern\t\ta camera\'s folder, anywhere above\tDCIM\tpath\tmedia:raw\tword\n')
    lst = os.path.join(T, 'vol-p.jsonl')
    with open(lst, 'w', encoding='utf-8') as fh:
        for rec in ({'path': 'Shoot', 'type': 'd'}, {'path': 'Shoot/DCIM', 'type': 'd'},
                    {'path': 'Shoot/DCIM/100X', 'type': 'd'},
                    {'path': 'Shoot/DCIM/100X/frame.jpg', 'type': 'f', 'size': 3, 'hash': B3['e']},
                    {'path': 'Shoot/other.jpg', 'type': 'f', 'size': 3, 'hash': B3['f']}):
            fh.write(json.dumps(rec) + '\n')
    rc, out = run(PY, 'bin/import.py', 'file-tree', lst, '--volume', 'vol-p', '--carrier', 'disk-a', '--into', 'store:cat',
                  '--path', sp, '--act', json.dumps({'in': 'vol-p', 'id': 'scan', 'by': 'nas', 'from': 'vol-p',
                                                     'at': '2026-10-20T10:00:00+03:00', 'through': 'scan (test)'}))
    S = dmstore.Store(sp, root=G)
    deep = formats.folder_id('vol-p', b'Shoot/DCIM/100X')
    got = formats.path_of(S.db, S.db.execute('SELECT n FROM being WHERE id = ?', (deep,)).fetchone()[0]) \
        if S.kind_of(deep) else None
    own = S.db.execute(f"SELECT count(*) FROM v_name WHERE {formats.OWN_NAME}").fetchone()[0]
    S.close()
    check("path: a listing imported keeps each folder's path beneath its volume, the volume's name of it "
          "(`Shoot/DCIM/100X`), beside the name its parent gives it", rc == 0 and got == 'Shoot/DCIM/100X' and own >= 3,
          (got, own, out[-1200:]))
    rc, out = run(PY, ST, 'keepings', '--store', sp, '--scheme', 'keep', '--of', 'vol-p', '--json')
    j = json.loads(out[:out.rindex('}') + 1]) if rc == 0 and '}' in out else {}
    codes = {c['content']: c['code'] for c in j.get('contents') or []}
    check("path: a pattern row that reads the path suggests a class for a file whose folder's word is anywhere above it "
          "(`DCIM`, two folders up), read again by the store each time; a file beside it, under no such word, none",
          codes.get(formats.content_id(B3['e'])) == 'keep:precious' and codes.get(formats.content_id(B3['f'])) is None,
          (codes, out[-1200:]))
    write('VOCAB.md', VOCAB)
    os.remove(os.path.join(G, 'extracts', 'names.tsv'))

    # ---- the storage watcher: a live directory, its history in a box on another disk
    sys.path.insert(0, os.path.join(ROOT, 'assets', 'storage', 'bin'))
    import watch as WT
    live, hist = os.path.join(T, 'live'), os.path.join(T, 'history')
    os.makedirs(live)

    def index(name):
        p = os.path.join(T, name + '.sqlite')
        db = sqlite3.connect(p)
        db.execute('CREATE TABLE entry (path BLOB, type TEXT, size INTEGER, hash TEXT)')
        for fn in sorted(os.listdir(live)):
            data = open(os.path.join(live, fn), 'rb').read()
            db.execute('INSERT INTO entry VALUES (?, ?, ?, ?)', (fn.encode(), 'f', len(data), formats.blake3_hex(data)))
        db.commit()
        db.close()
        return p
    empty = index('w0')
    for fn, data in (('a.txt', b'one'), ('b.txt', b'b')):
        open(os.path.join(live, fn), 'wb').write(data)
    w1 = index('w1')
    o1 = WT.pass_(empty, w1, live, hist, now=1_800_000_000)
    open(os.path.join(live, 'a.txt'), 'wb').write(b'two')
    w2 = index('w2')
    o2 = WT.pass_(w1, w2, live, hist, now=1_800_000_100)
    open(os.path.join(live, 'a.txt'), 'wb').write(b'three')
    os.remove(os.path.join(live, 'b.txt'))
    w3 = index('w3')
    o3 = WT.pass_(w2, w3, live, hist, versions=2, now=1_800_000_200)
    vers = sorted(os.listdir(os.path.join(hist, 'Versions', 'a.txt')))
    check("watch: a pass says what was added, what changed under its name and what is gone, and keeps each content the "
          "first time it is seen as a read-only blob of the history box",
          len(o1['added']) == 2 and o1['kept'] == 2 and o2['changed'] == [b'a.txt'] and o2['kept'] == 1
          and o3['gone'] == [b'b.txt'] and len(vers) == 3, (o1, o2, o3, vers))
    check("...each name's versions are links to their blobs, and those past the cap are listed, never removed unasked",
          len(o3['past the cap']) == 1 and o3['pruned'] == 0, o3)
    o4 = WT.pass_(w3, w3, live, hist, versions=2, prune=True, now=1_800_000_300)
    one = formats.blake3_hex(b'one')
    check("...and with `prune` the version past the cap goes, and its blob with it, its last name gone; nothing else",
          o4['pruned'] == 1 and not os.path.exists(os.path.join(hist, '.blobs', one))
          and len(os.listdir(os.path.join(hist, 'Versions', 'a.txt'))) == 2
          and os.path.exists(os.path.join(hist, '.blobs', formats.blake3_hex(b'b'))), o4)

    # ---- a container read as a volume
    try:
        import libarchive, blake3  # noqa: F401
        have_ct = True
    except ImportError:
        have_ct = False
    if have_ct:
        import zipfile
        sys.path.insert(0, os.path.join(ROOT, 'assets', 'storage', 'bin'))
        import container as CT
        zp = os.path.join(T, 'c.zip')
        with zipfile.ZipFile(zp, 'w') as z:
            z.writestr('one.txt', 'abc')
            z.writestr('sub/empty.bin', '')
            z.writestr('../out.txt', 'x')
        idx = os.path.join(T, 'ct.sqlite')
        code, said = CT.read(zp, idx)
        rows = sqlite3.connect(idx).execute('SELECT path, type, hash, err FROM entry ORDER BY path').fetchall()
        check("container: a zip read as a volume's index — each member hashed by BLAKE3 as it streams, its folders "
              "listed once, a path that climbs out kept by its name alone and said",
              code == 0 and (b'one.txt', 'f', '6437b3ac38465133ffb63b75273a8db548c558465d79db03fd359c6cd5bd9d85', None)
              in rows and (b'sub', 'd', None, None) in rows
              and any(r[0] == b'out.txt' and 'climbs out' in (r[3] or '') for r in rows), rows)
        nz = os.path.join(T, 'n.zip')
        open(nz, 'wb').write(b'not a container at all')
        check("...a file that is no container is said so, not guessed", CT.read(nz, os.path.join(T, 'n.sqlite'))[0] == 2,
              'exit')
        if shutil.which('zip'):                         # Info-ZIP's zip writes an encrypted member (ZipCrypto)
            with open(os.path.join(T, 'one.txt'), 'w') as fh:
                fh.write('abc')
            subprocess.run(['zip', '-q', '-P', 'a-test-pass', 'l.zip', 'one.txt'], cwd=T, capture_output=True)
            c1, _ = CT.read(os.path.join(T, 'l.zip'), os.path.join(T, 'l1.sqlite'))
            c2, _ = CT.read(os.path.join(T, 'l.zip'), os.path.join(T, 'l2.sqlite'), 'a-test-pass')
            got = sqlite3.connect(os.path.join(T, 'l2.sqlite')).execute("SELECT hash FROM entry WHERE path = ?",
                                                                        (b'one.txt',)).fetchone()
            check("...an encrypted member waits for its passphrase (exit 3), and is read whole once given it",
                  c1 == 3 and c2 == 0 and got and got[0].startswith('6437b3ac'), (c1, c2, got))

    TR = os.path.join('assets', 'storage', 'bin', 'transfer.py')
    rc, out = run(PY, TR, 'setup', '--by', 'sam')
    beans = sorted(f[:-3] for f in os.listdir(os.path.join(G, 'beans')) if f.endswith('.md'))
    rc2, out2 = run(PY, 'bin/save.py', 'sam', 'the fixtures and the walk of a transfer', '--body',
                    '- action: RULE-CHANGE, ratified by sam — VOCAB.md takes the storage profile, its risks and the '
                    'schemes keep and media; wrote [[walk-transfer]], ' + ', '.join(f'[[{b}]]' for b in beans))
    check("transfer: `setup` writes the walk into the garden's mappings, and the gate takes it with the fixtures",
          rc == 0 and rc2 == 0, out + out2[-1500:])
    rc, cid = run(PY, TR, 'start', '--store', sp, '--to', 'vol-s', '--dataset', 'a' * 64, '--from', 'disk-a',
                  '--total', '6', '--note', 'a test')
    cid = cid.strip().splitlines()[-1]
    rcs = [run(PY, TR, 'move', cid, st, '--store', sp, *extra)[0]
           for st, extra in (('copying', ['--done', '3']), ('verifying', []))]
    rc_bad, out_bad = run(PY, TR, 'move', cid, 'queued', '--store', sp)
    rc_done, _ = run(PY, TR, 'move', cid, 'done', '--store', sp)
    rc_after, out_after = run(PY, TR, 'move', cid, 'copying', '--store', sp)
    rc, shown = run(PY, TR, 'show', cid, '--store', sp, '--json')
    j = json.loads(shown[:shown.rindex(']') + 1]) if rc == 0 and ']' in shown else [{}]
    S = dmstore.Store(sp, root=G)
    met = [r for v, r, _a in S.get('vol-s') if v == 'meet']
    need = [r for v, r, _a in S.get('vol-s') if v == 'need']
    S.close()
    check("transfer: a course of what it fills, needing the dataset from its source, its moves along the walk",
          cid.startswith('tr-') and rcs == [0, 0] and j[0].get('step') == 'done'
          and [m['step'] for m in j[0].get('moves', [])] == ['queued', 'copying', 'verifying', 'done']
          and need and need[0].get('from') == 'disk-a', (cid, rcs, j))
    check("...a move the walk does not offer is refused, as is any after a final step",
          rc_bad == 2 and 'goes on to' in out_bad and rc_after == 2 and 'has ended' in out_after, (out_bad, out_after))
    rc, waiting = run(PY, TR, 'start', '--store', sp, '--to', 'vol-s', '--dataset', 'b' * 64, '--note', 'waits')
    waiting = waiting.strip().splitlines()[-1]
    rc, out = run(PY, 'bin/leads.py', '--json')
    got = [x for x in (json.loads(out) if rc == 0 and out.strip().startswith('[') else []) if x.get('course') == waiting]
    check("leads: a transfer kept in a store this host keeps, at a step that is not final, is a case for the gardener — "
          "and the course that is done is none", got and got[0]['step'] == 'queued' and got[0]['for'] == 'sam'
          and 'walk-transfer' in got[0]['why'] and not any(x.get('course') == cid for x in json.loads(out)),
          out[-1200:])
    check("...and when it is done its need is met, and how far it came is its whole", rc_done == 0 and met
          and met[0].get('of') == f'vol-s#{cid}-need' and j[0].get('done') == 6, (met, j))
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nstorage: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
