#!/usr/bin/env python3
"""The board (the view profile's archetype `cursor`; assets/view/lib/view_board.py): one being or several, the cursor,
kept still while the aspect around it turns, read over a garden's beans and the stores its host keeps.

A garden grown with the view and storage profiles; two trees scanned (assets/storage/bin/scan.py) and imported as two
volumes on two disks, and an archive's record of the copies it made from one of them imported as a third. Then, by
`view.py board`: the aspects are the law's rows of the profiles the garden takes, in the law's order, each turned about
the cursor; where a blank board may begin is read from the store; each aspect the reading draws answers what the
garden holds — what a volume holds, what two disks hold in common by the folders it sits in, where a content is held,
copied and backed up, the series its name is one of, the dataset its folder's tree is, and its keepings; a being's
sheet; finding inside the cursor. Then the same through daftard's worker (daftard/python/garden_worker.py): a bean's
statements on its sheet only for a reader the garden's grants open it to; an id of no shape refused before anything
is read. Nothing is written: the store's bytes and the garden's tree are the same after every question.

Run: python3 test/view_board.py   (0 = green)
"""
import hashlib, json, os, shutil, socket, sqlite3, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
sys.path.append(os.path.join(ROOT, 'test'))
from core import formats  # noqa: E402
import grow  # noqa: E402

FAILS = []
PY = sys.executable
T = tempfile.mkdtemp(prefix='board-')
G = os.path.join(T, 'g')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    p = subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=grow.ENV)
    return p.returncode, p.stdout + p.stderr


def board(*a):
    rc, out = run(PY, os.path.join('assets', 'view', 'bin', 'view.py'), 'board', *a)
    try:
        return rc, json.loads(out[out.index('{'):]) if rc == 0 else out
    except ValueError:
        return rc, out


def write(path, text):
    full = os.path.join(G, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def labels(group):
    return sorted(m['label'] for m in group['members'])


def sha(path):
    with open(path, 'rb') as fh:
        return hashlib.sha256(fh.read()).hexdigest()


try:
    try:
        import blake3  # noqa: F401
    except ImportError:
        print("SKIP  the board's store is made by scan.py, which needs the `blake3` module (pip install blake3)")
        sys.exit(0)
    rel = grow.release(os.path.join(T, 'release'))
    r = grow.garden(rel, G, 'sam', '--profile', 'storage', '--profile', 'view', '--zone', 'Europe/Istanbul')
    check("garden: grown with the view and storage profiles, which bring the board's reading and the scan",
          r.returncode == 0 and os.path.isfile(os.path.join(G, 'assets', 'view', 'lib', 'view_board.py'))
          and os.path.isfile(os.path.join(G, 'assets', 'storage', 'bin', 'scan.py')), r.out[-800:])

    # two trees on two disks that share three contents; an archive on a third that copied two of them from the first
    trees = {'t1': {'Photos/2026-10-01/IMG_0001.JPG': 'one', 'Photos/2026-10-01/IMG_0002.JPG': 'two',
                    'Docs/notes.txt': 'notes', 'Docs/only-a.txt': 'a alone'},
             't2': {'Backup/Photos/IMG_0001.JPG': 'one', 'Backup/Photos/IMG_0002.JPG': 'two',
                    'Other/notes.txt': 'notes', 'Other/only-b.txt': 'b alone'}}
    for name, files in trees.items():
        for p, body in files.items():
            full = os.path.join(T, name, p)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, 'w', encoding='utf-8') as fh:
                fh.write(body)
        rc, out = run(PY, os.path.join('assets', 'storage', 'bin', 'scan.py'), '--root', os.path.join(T, name),
                      '--index', os.path.join(T, name + '.sqlite'))
        check(f"scan: the tree {name} read into an index", rc == 0, out)
    me = socket.gethostname().lower().split('.')[0]
    write('beans/nas.md', f"---\nbean: nas\nkind: host\ntitle: \"nas\"\nsummary: \"nas, invented.\"\nstatements:\n"
                          f"  - say: {{ by: sam, at: now }}\n  - name: {{ by: dns, of: self, as: \"{me}.example.org\" }}\n"
                          f"details:\n  roots:\n    test:\n      system: unix-filesystem\n      at: \"{me}:{T}\"\n"
                          f"  stores:\n    cat:\n      at: \"root:test/cat.sqlite\"\n      form: sqlite\n---\nnas, invented.\n")
    for d in ('disk-a', 'disk-b', 'disk-c'):
        write(f'beans/{d}.md', f"---\nbean: {d}\nkind: host\ntitle: \"{d}\"\nsummary: \"{d}, invented.\"\nstatements:\n"
                               f"  - say: {{ by: sam, at: now }}\n  - part: {{ by: self, of: nas }}\n---\n{d}, invented.\n")
    rc, out = run(PY, 'bin/save.py', 'sam', 'the host and its disks', '--body',
                  '- action: wrote [[nas]], [[disk-a]], [[disk-b]] and [[disk-c]]')
    check("garden: a host that keeps a store, and three disks part of it, saved", rc == 0, out[-1200:])
    for vol, idx, disk in (('vol-a', 't1', 'disk-a'), ('vol-b', 't2', 'disk-b')):
        rc, out = run(PY, 'bin/import.py', 'file-tree', os.path.join(T, idx + '.sqlite'), '--volume', vol, '--carrier',
                      disk, '--into', 'store:cat')
        check(f"store: the index of {idx} imported as {vol} on {disk}", rc == 0, out)
    hs = dict(sqlite3.connect(os.path.join(T, 't1.sqlite')).execute("SELECT path, hash FROM entry WHERE type = 'f'"))
    man = os.path.join(T, 'copied.sqlite')
    db = sqlite3.connect(man)
    db.execute('CREATE TABLE copied (h TEXT, dest BLOB, size INTEGER, class TEXT, src_vol TEXT, src_path BLOB, day TEXT, '
               'day_from TEXT, at TEXT)')
    for p in (b'Photos/2026-10-01/IMG_0001.JPG', b'Photos/2026-10-01/IMG_0002.JPG'):
        db.execute('INSERT INTO copied VALUES (?,?,?,?,?,?,?,?,?)',
                   (hs[p], b'Captured/2026/2026-10-01/' + p.rpartition(b'/')[2], 3, 'photo', 'vol-a', p, '2026-10-01',
                    'name', '1792483200'))
    db.commit()
    db.close()
    rc, out = run(PY, 'bin/import.py', 'copies', man, '--volume', 'archive-m1', '--carrier', 'disk-c', '--into',
                  'store:cat')
    check("store: an archive's record of its copies imported as a third volume", rc == 0, out)
    store = os.path.join(T, 'cat.sqlite')
    before, head = sha(store), run('git', 'rev-parse', 'HEAD')[1].strip()
    c1 = formats.content_id(formats.blake3_hex(b'one'))
    c2 = formats.content_id(formats.blake3_hex(b'two'))
    shot = formats.folder_id('vol-a', b'Photos/2026-10-01')
    backup = formats.folder_id('vol-b', b'Backup/Photos')
    place = formats.folder_id('archive-m1', b'Captured/2026/2026-10-01')

    # ---- the aspects: the law's, of the profiles the garden takes
    rc, A = board('aspects')
    law = [r for r in grow._read.data(os.path.join(ROOT, 'core', 'law', 'profiles.yaml'))['aspects']
           if r['home'] in ('core', 'storage', 'view')]
    names = [a['lens'] for a in A['aspects']] if rc == 0 else []
    check("aspects: the law's rows of the core and of the profiles the garden takes, in the law's order — none of a "
          "profile it does not take", rc == 0 and names == [r['aspect'] for r in law]
          and 'its-moves' not in names and 'its-dataset' in names, (A, names))
    check("...each turned about the cursor by its place among them, laid out by its row of the law's orientations, "
          "every one of them drawn", rc == 0 and len({a['turn'] for a in A['aspects']}) == len(names)
          and all(a['drawn'] for a in A['aspects'])
          and {a['order'] for a in A['aspects']} <= {o['order'] for o in A['orientations']}, A)
    check("...and a blank board begins from what carries each volume the store keeps", rc == 0
          and sorted(s['id'] for s in A['starts']) == ['disk-a', 'disk-b', 'disk-c'], A)

    # ---- the core's aspects, over the store
    rc, L = board('lens', 'holds', 'vol-a')
    gs = {g['label']: g for g in L['groups']} if rc == 0 else {}
    check("holds: what a volume holds, its folders with how much each holds beneath it",
          rc == 0 and labels(gs.get('folders', {'members': []})) == ['Docs', 'Photos']
          and any(m['sub'] == '0 folders · 2 files' for m in gs['folders']['members']), L)
    rc, L = board('lens', 'holds', shot)
    check("...a folder its files, by the names it holds them under", rc == 0
          and labels(L['groups'][0]) == ['IMG_0001.JPG', 'IMG_0002.JPG'], L)
    rc, L = board('lens', 'holds', 'disk-a', 'disk-b')
    shared = [g for g in L['groups'] if g['side'] == 'shared'] if rc == 0 else []
    check("...two disks side by side: each one's own on its side, and what they hold in common between them, by the "
          "pair of folders it sits in, the pair holding most first",
          rc == 0 and [g['label'] for g in shared] == ['vol-a:Photos/2026-10-01 · vol-b:Backup/Photos',
                                                       'vol-a:Docs · vol-b:Other']
          and labels(shared[0]) == ['IMG_0001.JPG', 'IMG_0002.JPG']
          and {g['side'] for g in L['groups']} == {0, 1, 'shared'}, L)
    rc, L = board('lens', 'carried-by', c1)
    check("carried-by: a content's holders, by the volume each is on and the disk that carries it",
          rc == 0 and sorted(g['label'] for g in L['groups']) == ['archive-m1 on disk-c', 'vol-a on disk-a',
                                                                  'vol-b on disk-b']
          and all(g['at'] == 'before' for g in L['groups']), L)
    rc, L = board('lens', 'carried-by', 'disk-a')
    check("...and a disk the machine the garden says it is part of", rc == 0
          and [m['id'] for g in L['groups'] for m in g['members']] == ['nas'], L)
    rc, L = board('lens', 'copies', c1)
    gs = {g['label']: g for g in L['groups']} if rc == 0 else {}
    check("copies: a content held where it was found, before; copied, after, with when and from where",
          rc == 0 and sorted(m['id'] for m in gs.get('held', {'members': []})['members']) == sorted([shot, backup])
          and [m['id'] for m in gs.get('copied to', {'members': []})['members']] == [place]
          and 'from vol-a:Photos/2026-10-01' in gs['copied to']['members'][0]['sub'], L)
    rc, L = board('lens', 'in-backup', c1)
    check("in-backup: the place a content was copied into, and its other members by the volume each came from",
          rc == 0 and len(L['groups']) == 1 and L['groups'][0]['label'] == 'from vol-a'
          and [m['id'] for m in L['groups'][0]['members']] == [c2] and L['groups'][0]['head']['id'] == place, L)
    rc, L = board('lens', 'its-series', c1)
    check("its-series: the run of names a content is one of, drawn once, the other folders holding the same run said",
          rc == 0 and len(L['groups']) == 1 and labels(L['groups'][0]) == ['IMG_0001.JPG', 'IMG_0002.JPG']
          and L['groups'][0]['note'].count('the same 2 contents in') == 2, L)

    # ---- the storage profile's aspects, read by its asset
    rc, L = board('lens', 'its-dataset', shot)
    tree = formats.blake3_hex((formats.blake3_hex(b'one') + '  IMG_0001.JPG\n' + formats.blake3_hex(b'two')
                               + '  IMG_0002.JPG\n').encode())
    check("its-dataset: a folder's tree named by its manifest's BLAKE3, and every folder holding the same tree",
          rc == 0 and len(L['groups']) == 1 and L['groups'][0]['key'] == f'dataset:{tree}'
          and sorted(m['id'] for m in L['groups'][0]['members']) == sorted([shot, backup, place]), (tree, L))
    rc, L = board('lens', 'its-safety', c1)
    check("its-safety: a content's keepings, one a volume, and the policy it is judged by",
          rc == 0 and sorted(g['label'].split(' · ')[0] for g in L['groups'][1:]) == ['archive-m1', 'vol-a', 'vol-b']
          and L['groups'][0]['label'].startswith('no policy'), L)
    rc, L = board('lens', 'copies', 'vol-a')
    check("an aspect through a being of a kind it does not read answers no groups", rc == 0 and L['groups'] == [], L)
    rc, out = board('lens', 'its-moves', 'vol-a')
    check("...and an aspect of a profile the garden does not take is refused", rc == 1 and 'no aspect' in out, out)

    # ---- the sheet, and finding
    rc, S = board('being', c1)
    check("being: a content's sheet — its BLAKE3, its size, and every name it is held under", rc == 0
          and dict(map(tuple, S['facts'])).get('blake3') == formats.blake3_hex(b'one')
          and sorted(r[0] for r in S['lists'][0]['rows']) == ['archive-m1', 'vol-a', 'vol-b'], S)
    rc, S = board('being', 'disk-a')
    check("...a bean's, its statements, and what the store keeps of it", rc == 0 and S['garden']['bean'] == 'disk-a'
          and any(s.startswith('part:') for s in S['garden']['statements'])
          and ['holds', 'vol-a'] in S['facts'], S)
    rc, F = board('find', 'IMG', 'vol-a', 'vol-b')
    check("find: what each being of the cursor holds beneath it whose name has the text, on its side",
          rc == 0 and [g['side'] for g in F['groups']] == [0, 1]
          and all(labels(g) == ['IMG_0001.JPG', 'IMG_0002.JPG'] for g in F['groups']), F)
    rc, out = board('find', 'IM', 'vol-a')
    check("...a text of fewer than three letters is refused", rc == 1 and 'three letters' in out, out)

    # ---- through daftard's worker, as the page asks
    env = dict(os.environ, DAFTAR_KIND='core', DAFTARD_NOTIFY='off', PYTHONUTF8='1')
    w = subprocess.Popen([PY, os.path.join(ROOT, 'daftard', 'python', 'garden_worker.py')], cwd=G, env=env, text=True,
                         encoding='utf-8', stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    n = [0]

    def ask(method, params):
        n[0] += 1
        w.stdin.write(json.dumps({'id': n[0], 'method': method, 'params': params}) + '\n')
        w.stdin.flush()
        return json.loads(w.stdout.readline() or '{}')
    a = ask('board_aspects', {})
    lz = ask('board_lens', {'aspect': 'carried-by', 'cursor': [c1]})
    mine = ask('board_being', {'id': 'disk-a', 'reader': 'sam'})
    other = ask('board_being', {'id': 'disk-a', 'reader': 'zoe'})
    bad = ask('board_lens', {'aspect': 'holds', 'cursor': ['../beans']})
    nope = ask('board_lens', {'aspect': 'no-such', 'cursor': ['vol-a']})
    fd = ask('board_find', {'q': 'notes', 'cursor': ['disk-a', 'disk-b']})
    w.stdin.close()
    w.wait(timeout=60)
    check("worker: the board's aspects and a lens, as the page asks them", a.get('ok') and lz.get('ok')
          and [x['lens'] for x in a['result']['aspects']] == names and len(lz['result']['groups']) == 3, (a, lz))
    check("...a bean's statements on its sheet for its gardener, and none for a reader no grant opens it to",
          mine.get('ok') and mine['result']['garden'] and other.get('ok') and other['result']['garden'] is None
          and ['holds', 'vol-a'] in other['result']['facts'], (mine, other))
    check("...an id of no shape and an aspect the garden has not are refused, said to the person",
          bad.get('ok') is False and bad['error']['status'] == 400 and nope.get('ok') is False
          and nope['error']['status'] == 404, (bad, nope))
    check("...and finding beneath two disks at once, each on its side", fd.get('ok')
          and [g['side'] for g in fd['result']['groups']] == [0, 1]
          and all(labels(g) == ['notes.txt'] for g in fd['result']['groups']), fd)

    # ---- read only
    check("read only: the store's bytes, the garden's commit and its tree are as they were after every question",
          sha(store) == before and run('git', 'rev-parse', 'HEAD')[1].strip() == head
          and run('git', 'status', '--porcelain')[1].strip() == '', run('git', 'status', '--porcelain')[1])

    # ---- a garden that does not take the view profile has no board
    write('VOCAB.md', open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read().replace('view', 'knowledge', 1)
          if 'profiles: [' in open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read() else '')
    rc, out = board('aspects')
    check("a garden that takes no view profile has no board, and is told why", rc == 1 and 'view profile' in out, out)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nview_board: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
