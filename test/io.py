#!/usr/bin/env python3
"""Imports and exports: one machinery around the store, every format in and out through the law's crosswalks (2.12).

Grows a garden of the core from a release made of this tree (test/grow.py), and runs bin/import.py and bin/export.py
in it as a person or a tool would:

  formats   each format the release reads and writes gives back the records it wrote; a CSV cell a spreadsheet would
            read as a formula is written as text; an XML document that declares an entity is refused before it is
            parsed; a format the release does not read is refused by name
  file-tree a listing of paths (a scan's index) into a store: the volume held by its carrier, each folder part of its
            parent and named by it, each file a holding, each content named by its BLAKE3 and measured, the ids the
            catalogue's; a name in bytes `escaped`; what the reader does not read counted; the holdings back out
  again     the same source, read by the same act, is imported already and writes nothing; a second reading keeps every
            row once and adds its act to each (`known_also`): "not seen since" is a reading of the acts
  copies    a manifest of copies: each copy a holding made from the holding it copies (`make` from, through), its source
            left out where the store keeps none
  exif      a photograph's content produced by the camera its serial names, through its lens, at the moment with its
            fraction and offset, a clock with no offset kept to its day; a serial no being has leaves `unknown`, listed
            with the camera's make and model; named since, the next import fills it and takes the old out by `gone`
  dwc       a Darwin Core occurrence written into a bean with its act (`--write`), saved through the gate, and exported
            back column for column
  flows     the flow law asked for every pass: what is sealed never reaches a store; a document's lines into a store
            are said by it (`store-stated`); a garden's statements are never exported to a public repository
  list      `import --list` names the crosswalks that say how their records come
  readers   one table of readers in the law names every reader the release and its profiles have, and nothing else: a
            provider's (bin/fetch.py), a model's (bin/import.py), a profile's (the bank statements' adapters)
  ics       a calendar written by the `ics` format, its events in the civil calendar, an alarm before
  own       the garden's own statements through the same doors: a bean into a store and back (bin/store.py's import
            and export)

Run: python3 test/io.py   (0 = green; about a minute)
"""
import hashlib
import json
import os
import shutil
import socket
import sqlite3
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'test'))
import grow  # noqa: E402

FAILS = []
PY = sys.executable
B3A = '6437b3ac38465133ffb63b75273a8db548c558465d79db03fd359c6cd5bd9d85'     # BLAKE3("abc")
B3B = 'af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262'     # BLAKE3("")
B3C = 'b' * 64                                                                  # a content's digest, invented


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def doc(bid, kind, *statements, details=''):
    return (f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{bid}\"\nstatements:\n" + ''.join(f"  - {s}\n" for s in statements)
            + details + f"---\n{bid}, invented.\n")


def write(rel, text):
    p = os.path.join(G, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def save(what, body):
    return grow.run(PY, 'bin/save.py', 'sam', what, '--body', body, cwd=G)


def py(program, *args):
    """A program run in the garden, its answer the last JSON line it prints."""
    r = grow.run(PY, '-c', "import json, os, sys, sqlite3, importlib\nsys.path[:0] = ['.', 'bin']\n" + program, *args,
                 cwd=G)
    lines = [ln for ln in r.stdout.splitlines() if ln.startswith('{')]
    return (json.loads(lines[-1]) if lines else None), r


def folder_id(volume, path):
    return 'd-' + hashlib.sha256(volume.encode() + b'\0' + path).hexdigest()[:16]


FORMATS = r'''
from core import formats
from decimal import Decimal
recs = [{'code': 'a1', 'name': 'one', 'n': '3'}, {'code': 'b2', 'name': 'two words', 'n': '4.50'}]
out = {}
for f in ('tsv', 'csv', 'jsonl', 'json'):
    text = formats.write(f, recs)
    back = [dict(x) for x in formats.read(f, text.encode('utf-8'))]
    out[f] = [{k: str(v) for k, v in x.items()} for x in back] == recs
p = sys.argv[1] + '/recs.sqlite'
open(p, 'wb').write(formats.write('sqlite', recs))
out['sqlite'] = [dict(x) for x in formats.read('sqlite', p, {'table': 'record'})] == recs
out['where'] = [dict(x)['code'] for x in formats.read('sqlite', p, {'table': 'record', 'where': {'code': ['b2']}})]
out['decimal'] = isinstance(list(formats.read('json', b'[{"v": 0.1}]'))[0]['v'], Decimal)
out['formula'] = formats.write('csv', [{'a': '=SUM(A1)', 'b': '-3'}]).splitlines()[1]
try:
    list(formats.read('xml', b'<!DOCTYPE x [<!ENTITY e "boom">]><x>&e;</x>'))
    out['entity'] = None
except formats.Refused as e:
    out['entity'] = str(e)
out['xml'] = [dict(x) for x in formats.read('xml', b'<d><Ntry><Amt Ccy="EUR">9.50</Amt></Ntry><Ntry><Amt Ccy="TRY">1</Amt></Ntry></d>', {'path': 'Ntry'})]
try:
    formats.read('vcard', b'')
    out['vacant'] = None
except formats.Refused as e:
    out['vacant'] = str(e)
out['bytes'] = formats.escape(b'IMG\xff%\n.CR2')
print(json.dumps(out))
'''

TREE = r'''
imp = importlib.import_module('import')
import store
from core.formats import folder_id
S = store.open_store('cat')
I = imp.Import('.', 'file-tree', keep='store', store=S,
               acts={'derive': {'in': 'nas', 'by': 'nas', 'at': '2026-10-18T12:00:00+03:00'}})
done = I.source(sys.argv[1], volume='vol-1', carrier='disk-1',
                act={'in': 'vol-1', 'id': sys.argv[2], 'by': 'nas', 'from': 'vol-1', 'at': sys.argv[3],
                     'through': 'scan (test)'})
I.done()
q = lambda sql, *a: S.db.execute(sql, a).fetchall()
print(json.dumps({'done': done, 'rows': S.count(), 'beings': q("SELECT kind, COUNT(*) FROM being GROUP BY kind"),
  'vol': S.get('vol-1'), 'photos': S.get(folder_id('vol-1', b'Photos')), 'y': S.get(folder_id('vol-1', b'Photos/2026')),
  'c': S.get('c-' + sys.argv[4][:24]), 'also': q("SELECT COUNT(*) FROM known_also")[0][0],
  'lines': I.account.lines(each=False)}, default=str))
'''

COPIES = r'''
imp = importlib.import_module('import')
import store
from core.formats import folder_id
S = store.open_store('cat')
S.put('arch-1', 'make', {'id': 'made', 'by': 'nas', 'at': '2026-10-17T22:00:00+03:00'})
I = imp.Import('.', 'copies', keep='store', store=S, acts={'folder': 'arch-1#made', 'volume': 'arch-1#made',
               'make': {'by': 'nas', 'through': 'archive-1'}})
I.source(sys.argv[1], volume='arch-1', carrier='disk-1')
I.done()
f = folder_id('arch-1', b'Captured/2026/2026-10-16')
print(json.dumps({'f': S.get(f), 'kinds': S.db.execute("SELECT kind FROM being WHERE id LIKE 'c-0000%'").fetchall(),
                  'notes': I.account.lines(each=False)}, default=str))
'''

EXIF = r'''
imp = importlib.import_module('import')
import store
S = store.open_store('cat')
I = imp.Import('.', 'exif-image', keep='store', store=S, named={'*': 'device-serial'},
               acts={'read': {'in': 'vol-1', 'by': 'nas', 'from': 'vol-1', 'through': 'exiftool (test)',
                              'at': sys.argv[2]}})
I.source(sys.argv[1], volume='vol-1', root=sys.argv[3])
I.done()
pa = [r for v, r, _a in S.get('c-' + sys.argv[4][:24]) if v == 'produce']
pb = [r for v, r, _a in S.get('c-' + sys.argv[5][:24]) if v == 'produce']
gone = S.db.execute("SELECT being, why FROM gone").fetchall()
print(json.dumps({'a': pa, 'b': pb, 'gone': gone, 'lines': I.account.lines(each=False)}, default=str))
'''

READERS = r'''
from core import readers
from core.check import garden_law
L = garden_law('.', '.')
sys.path.insert(0, 'assets/accounting/lib') if os.path.isdir('assets/accounting/lib') else None
law = {n: r for n, r in L.readers.items()}
code = set(readers.IMPORTED) | set(readers.FETCHED)
try:
    import statements
    home = set(statements.FORMATS)
except ImportError:
    home = None
print(json.dumps({'law_release': sorted(n for n, r in law.items() if not r.get('home')), 'code': sorted(code),
                  'law_accounting': sorted(n for n, r in law.items() if r.get('home') == 'accounting'),
                  'asset': sorted(home) if home is not None else None,
                  'ics': __import__('core.formats', fromlist=['x']).write('ics', [
                      {'uid': 'u-1@g', 'start': '2026-10-19T09:30:00+03:00', 'summary': 'a visit, early', 'notice': 600},
                      {'uid': 'u-2@g', 'start': 'no day', 'summary': 'none'}], stamp='20261019T000000Z')}))
'''

FLOWS = r'''
imp = importlib.import_module('import')
exp = importlib.import_module('export')
import store
from core.crosswalk import Refused
S = store.open_store('cat')
out = {}
for layer, verb in (('held', 'read'), ('words', 'say'), ('world', 'read')):
    I = imp.Import('.', 'file-tree', keep='store', store=S, source_layer=layer)
    try:
        out[layer] = I.flow(verb)
    except Refused as e:
        out[layer] = 'refused: ' + str(e)
out['derive'] = imp.Import('.', 'file-tree', keep='store', store=S).flow('derive')
try:
    exp.Export('.', 'fhir-r5-observation', to='public')
    out['public'] = None
except Refused as e:
    out['public'] = str(e)
out['show'] = bool(exp.Export('.', 'fhir-r5-observation'))
print(json.dumps(out))
'''

T = tempfile.mkdtemp(prefix='core-io-')
G = os.path.join(T, 'g')
S = os.path.join(T, 'stores')
os.makedirs(S)
try:
    REL = grow.release(os.path.join(T, 'release'))
    r = grow.garden(REL, G, 'sam')
    check("a garden of the core grows, and carries the tools import and export", r.returncode == 0
          and all(os.path.isfile(os.path.join(G, 'bin', f)) for f in ('import.py', 'export.py'))
          and os.path.isfile(os.path.join(G, 'core', 'formats.py')), r.out[-600:])
    me = socket.gethostname().lower().split('.')[0]
    vocab = open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read()
    write('VOCAB.md', vocab.replace('namespaces: []', 'namespaces:\n  - { namespace: device-serial, once: "true" }', 1))
    write('beans/nas.md', doc('nas', 'host', 'say: { by: sam, at: now }',
                              f'name: {{ by: dns, of: self, as: "{me}.example.org" }}',
                              details=f"details:\n  roots:\n    test:\n      system: unix-filesystem\n      at: \"{me}:{S}\"\n"
                                      f"  stores:\n    cat:\n      at: \"root:test/cat.sqlite\"\n      form: sqlite\n"))
    write('beans/disk-1.md', doc('disk-1', 'host', 'say: { by: sam, at: now }'))
    write('beans/camera-1.md', doc('camera-1', 'host', 'say: { by: sam, at: now }',
                                   'name: { by: device-serial, of: self, as: "A100" }'))
    write('beans/lens-1.md', doc('lens-1', 'host', 'say: { by: sam, at: now }',
                                 'name: { by: device-serial, of: self, as: "L7" }'))
    write('beans/archive-1.md', doc('archive-1', 'host', 'say: { by: sam, at: now }'))
    r = save('the fixtures', '- action: RULE-CHANGE — VOCAB.md adds the namespace device-serial; wrote [[nas]], '
                             '[[disk-1]], [[camera-1]], [[lens-1]], [[archive-1]]')
    check("the fixtures are saved: a host that keeps a store, a disk, a camera and a lens named by their serials",
          r.returncode == 0, r.out[-1200:])

    # ---- list
    r = grow.run(PY, 'bin/daftar.py', 'import', '--list', cwd=G)
    check("list: `daftar import --list` names the crosswalks that say how their records come, with their formats",
          r.returncode == 0 and all(n in r.out for n in ('file-tree-folder', 'file-tree-copy', 'exif-image',
                                                          'fhir-r5-observation', 'dwc-occurrence'))
          and 'odoo-17.0' not in r.out, r.out[-1200:])

    # ---- formats
    j, r = py(FORMATS, S)
    ok = j is not None
    check("formats: tsv, csv, jsonl, json and sqlite each give back the records they wrote",
          ok and all(j[f] for f in ('tsv', 'csv', 'jsonl', 'json', 'sqlite')), (j, r.out[-1200:]))
    check("...a database's records filtered by its columns' values, and a number read as written, never a float",
          ok and j['where'] == ['b2'] and j['decimal'], j)
    check("...a CSV cell a spreadsheet would read as a formula is written as text; a negative number stays a number",
          ok and j['formula'] == "'=SUM(A1),-3", j and j['formula'])
    check("...an XML document that declares an entity is refused before it is parsed; one that does not gives its "
          "elements", ok and j['entity'] and 'refused before it is parsed' in j['entity']
          and j['xml'][0]['Amt'] == {'@Ccy': 'EUR', '#text': '9.50'}, j)
    check("...a format the release reads none of is refused by name; a name in bytes is written `escaped`",
          ok and j['vacant'] and 'vcard' in j['vacant'] and j['bytes'] == 'IMG%FF%25%0A.CR2', j)

    # ---- file-tree
    idx = os.path.join(T, 'vol-1.sqlite')
    db = sqlite3.connect(idx)
    db.execute("CREATE TABLE entry (path BLOB PRIMARY KEY, type TEXT, size INTEGER, mtime_ns INTEGER, hash TEXT)")
    db.executemany("INSERT INTO entry VALUES (?, ?, ?, ?, ?)", [
        (b'Photos', 'd', None, 1, None), (b'Photos/2026', 'd', None, 1, None),
        (b'Photos/2026/a.cr2', 'f', 3, 1, B3A), (b'Photos/2026/IMG\xff.jpg', 'f', 0, 1, B3B),
        (b'Photos/2026/b.jpg', 'f', 5, 1, B3C), (b'Photos/copy-of-a.cr2', 'f', 3, 1, B3A),
        (b'notes.txt', 'f', 9, 1, None), (b'link', 'l', None, 1, None)])
    db.commit()
    db.close()
    Y = folder_id('vol-1', b'Photos/2026')
    j, r = py(TREE, idx, 'scan', '2026-10-18T11:00:00+03:00', B3A)
    ok = j is not None
    hy = {tuple(sorted((k, str(v)) for k, v in rr.items() if k != 'id')) for v, rr, _a in (j or {}).get('y', [])
          if v == 'hold'}
    check("file-tree: a scan's index into a store — the volume held by its carrier, known by the scan's reading",
          ok and any(v == 'hold' and rr.get('by') == 'disk-1' and rr.get('of') == 'vol-1' and a == ['vol-1#scan']
                     for v, rr, a in j['vol']), (j, r.out[-1500:]))
    check("...each folder part of its parent, or of its volume, and named by it; its id the catalogue's",
          ok and any(v == 'part' and rr.get('of') == 'vol-1' for v, rr, _a in j['photos'])
          and any(v == 'name' and rr.get('by') == 'vol-1' and rr.get('as') == 'Photos' for v, rr, _a in j['photos'])
          and any(v == 'part' and rr.get('of') == folder_id('vol-1', b'Photos') for v, rr, _a in j['y']), j)
    check("...each file a holding of its folder: its content by its handle, its name, a name in bytes `escaped`",
          ok and (('as', 'a.cr2'), ('by', Y), ('of', 'c-' + B3A[:24])) in hy
          and (('as', 'IMG%FF.jpg'), ('by', Y), ('of', 'c-' + B3B[:24])) in hy, hy)
    check("...each content named by its BLAKE3 and measured in bytes, once, derived from the readings of its volume",
          ok and any(v == 'name' and rr.get('by') == 'blake3' and rr.get('as') == B3A for v, rr, _a in j['c'])
          and any(v == 'measure' and rr.get('value') == {'count': '3', 'unit': 'By'} and a[0].startswith('nas#derive-')
                  for v, rr, a in j['c'])
          and len([1 for v, rr, _a in j['c'] if v == 'name']) == 1, j and j['c'])
    check("...a file whose content nobody read holds `unknown`; a link is no file; what the reader does not read counted",
          ok and ['content', 3] in j['beings'] and ['folder', 2] in j['beings']
          and any('mtime_ns × 8' in ln for ln in j['lines']), j)
    rows1 = j['rows'] if ok else -1

    # ---- again
    j, r = py(TREE, idx, 'scan', '2026-10-18T11:00:00+03:00', B3A)
    check("again: the same source, read by the same act, is imported already: nothing is written",
          j is not None and j['done'] is False and j['rows'] == rows1 and j['also'] == 0, (j, r.out[-800:]))
    j, r = py(TREE, idx, 'scan-2', '2026-10-19T11:00:00+03:00', B3A)
    check("...a second reading keeps every row once, and its act is added to each it read: when it was last seen is "
          "read from the acts, never stored", j is not None and j['done'] is True and j['rows'] == rows1 + 2
          and j['also'] >= 7 and all(len(a) == 2 for _v, _r, a in j['c']), (j, r.out[-800:]))

    # ---- export: the holdings back out
    r = grow.run(PY, 'bin/daftar.py', 'export', 'file-tree-file', Y, '--from', 'store:cat', '--format', 'csv', cwd=G)
    check("export: a folder's holdings read back from the store as the listing's records, in CSV",
          r.returncode == 0 and 'a.cr2' in r.stdout and 'IMG%FF.jpg' in r.stdout and 'c-' + B3A[:24] in r.stdout,
          r.out[-800:])

    # ---- copies
    man = os.path.join(T, 'manifest.sqlite')
    db = sqlite3.connect(man)
    db.execute("CREATE TABLE copied (h TEXT PRIMARY KEY, dest BLOB, size INTEGER, class TEXT, src_vol TEXT, "
               "src_path BLOB, day TEXT, day_from TEXT, at REAL)")
    db.executemany("INSERT INTO copied VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (B3A, b'Captured/2026/2026-10-16/a.cr2', 3, 'captured-photo', 'vol-1', b'Photos/2026/a.cr2', '2026-10-16',
         'exif DateTimeOriginal', 1760600000.0),
        ('0' * 64, b'Captured/2026/2026-10-16/z.cr2', 5, 'captured-photo', 'vol-9', b'x/z.cr2', '2026-10-16', 'name',
         1760600001.0)])
    db.commit()
    db.close()
    j, r = py(COPIES, man)
    ok = j is not None
    makes = [rr for v, rr, _a in (j or {}).get('f', []) if v == 'make']
    check("copies: each copy a holding of its folder, known by a `make` from the holding it copies, through the copier",
          ok and any(rr.get('from') and rr['from'][0].startswith(Y + '#hold-') and rr.get('through') == 'archive-1'
                     for rr in makes), (j, r.out[-1500:]))
    check("...a copy whose source the store keeps no holding of is kept, its `from` left out and counted",
          ok and len(makes) == 2 and len([m for m in makes if 'from' not in m]) == 1
          and any('kept nowhere here' in ln for ln in j['notes']) and j['kinds'] == [['content']], j)

    # ---- exif
    vroot = os.path.join(T, 'vol')
    exif = os.path.join(T, 'exif.json')
    with open(exif, 'w', encoding='utf-8') as fh:
        json.dump([{"SourceFile": os.path.join(vroot, 'Photos/2026/a.cr2'), "IFD0:Make": "Maker",
                    "IFD0:Model": "Body One", "ExifIFD:SerialNumber": "A100", "ExifIFD:LensSerialNumber": "L7",
                    "ExifIFD:LensModel": "35mm", "Composite:SubSecDateTimeOriginal": "2026:10:16 00:36:46.17+03:00",
                    "ExifIFD:ISO": 1600},
                   {"SourceFile": os.path.join(vroot, 'Photos/2026/b.jpg'), "IFD0:Make": "Maker",
                    "IFD0:Model": "Body Two", "ExifIFD:SerialNumber": "B200", "ExifIFD:LensSerialNumber": "0000000000",
                    "Composite:SubSecDateTimeOriginal": "2025:01:02 03:04:05"}], fh)
    j, r = py(EXIF, exif, '2026-10-18T13:00:00+03:00', vroot, B3A, B3C)
    ok = j is not None
    check("exif: a photograph's content produced by the camera its serial names, through its lens, at the moment the "
          "picture states, with its fraction and offset", ok and any(
              r2.get('by') == 'camera-1' and r2.get('through') == 'lens-1' and r2.get('of') == 'c-' + B3A[:24]
              and r2.get('at') == '2026-10-16T00:36:46.17+03:00' for r2 in j['a']), (j, r.out[-1500:]))
    check("...a serial no being has leaves the camera `unknown`, listed with its make and model; a lens of zeros is none; "
          "a clock with no offset kept to its day",
          ok and any(r2.get('by') == 'unknown' and r2.get('at') == '2025-01-02' and 'through' not in r2 for r2 in j['b'])
          and any('B200' in ln and 'Body Two' in ln for ln in j['lines'])
          and any('kept to its day' in ln for ln in j['lines']), j)
    check("...every other tag counted as not carried", ok and any('ExifIFD:ISO × 1' in ln for ln in j['lines']), j)
    write('beans/camera-2.md', doc('camera-2', 'host', 'say: { by: sam, at: now }',
                                   'name: { by: device-serial, of: self, as: "B200" }'))
    r = save('a second camera, named by its serial', '- action: wrote [[camera-2]]')
    j, r = py(EXIF, exif, '2026-10-19T13:00:00+03:00', vroot, B3A, B3C)
    ok = j is not None
    check("...named since, the next import fills it: the camera is the being its serial names, and the statement "
          "that held `unknown` is taken out by `gone`, its reason recorded",
          ok and [r2.get('by') for r2 in j['b']] == ['camera-2'] and any('filled' in w for _b, w in j['gone']),
          (j, r.out[-1500:]))

    # ---- dwc, into a bean and back
    occ = os.path.join(T, 'occ.csv')
    with open(occ, 'w', encoding='utf-8') as fh:
        fh.write("occurrenceID,eventDate,decimalLatitude,decimalLongitude,geodeticDatum,coordinateUncertaintyInMeters,"
                 "locality,recordedBy\ngps-1,2026-05-02,57.1203,-6.1044,EPSG:4326,30,the north landing,keeper\n")
    write('beans/gps-1.md', doc('gps-1', 'host', 'say: { by: sam, at: now }'))
    r = save('a tracker', '- action: wrote [[gps-1]]')
    r = grow.run(PY, 'bin/daftar.py', 'import', 'dwc-occurrence', occ, '--into', 'bean', '--write', cwd=G)
    r2 = save('a position carried from Darwin Core', '- action: wrote [[gps-1]]: a position carried by `daftar import`')
    text = open(os.path.join(G, 'beans', 'gps-1.md'), encoding='utf-8').read()
    check("dwc: an occurrence written into its bean with the act that knows it (`--write`), saved through the gate; "
          "what a `be` has no place for listed", r.returncode == 0 and r2.returncode == 0 and 'read:' in text
          and 'EPSG:4326;57.1203,-6.1044' in text and 'recordedBy' in r.stderr, r.out[-800:] + r2.out[-1200:])
    r = grow.run(PY, 'bin/daftar.py', 'export', 'dwc-occurrence', 'gps-1', cwd=G)
    import csv
    import io
    rows = [{k: v for k, v in x.items() if v} for x in csv.DictReader(io.StringIO(r.stdout))]
    check("...and exported back column for column, every column not listed equal",
          r.returncode == 0 and rows == [{'occurrenceID': 'gps-1', 'eventDate': '2026-05-02', 'geodeticDatum': 'EPSG:4326',
                                          'decimalLatitude': '57.1203', 'decimalLongitude': '-6.1044',
                                          'coordinateUncertaintyInMeters': '30', 'locality': 'the north landing'}]
          and 'not carried' not in r.stderr, (rows, r.out[-800:]))

    # ---- readers
    j, r = py(READERS)
    ok = j is not None
    check("readers: one table in the law names every reader the release has — a provider's and a model's — and the "
          "code has none it does not name", ok and j['law_release'] == j['code'] and len(j['code']) == 12,
          (j and (j['law_release'], j['code']), r.out[-1200:]))
    check("...and a profile's: the bank statements' adapters, each a reader the law names with its home",
          ok and (j['asset'] is None or j['asset'] == j['law_accounting']) and len(j['law_accounting']) == 5, j)

    # ---- ics
    ics = (j or {}).get('ics', '')
    check("ics: a calendar written by the `ics` format — an event at its moment in UTC, its summary escaped, an alarm "
          "before; one at no day of the civil calendar left out",
          'DTSTART:20261019T063000Z' in ics and 'SUMMARY:a visit\\, early' in ics and 'TRIGGER:-PT10M' in ics
          and 'u-2@g' not in ics and ics.endswith('END:VCALENDAR\r\n'), ics)

    # ---- the garden's own, through the same doors
    write('beans/session-x.md', doc('session-x', 'session', 'make: { by: self, at: now }'))
    write('beans/note-1.md', doc('note-1', 'document', 'say: { by: sam, at: now }', 'hold: { id: h1, by: nas, of: self }'))
    r = save('a note and a session', '- action: wrote [[note-1]], [[session-x]]')
    r = grow.run(PY, 'bin/daftar.py', 'import', 'daftar', 'note-1', '--into', 'store:cat', cwd=G)
    r2 = grow.run(PY, 'bin/daftar.py', 'export', 'daftar', 'note-1', '--from', 'store:cat', '--by', 'session-x', cwd=G)
    check("own: a bean's statements into a store through `daftar import daftar`, with the act that knows them, and its "
          "bean holding every one of them already when exported back (bin/store.py's import and export)",
          r.returncode == 0 and 'kept in cat' in r.out and r2.returncode == 0 and 'holds every statement' in r2.out,
          r.out[-600:] + r2.out[-600:])

    # ---- flows
    j, r = py(FLOWS)
    ok = j is not None
    check("flows: what is sealed never reaches a store; a reading of the world into one is `store-recorded`",
          ok and j['held'].startswith('refused') and j['world'] == 'store-recorded', (j, r.out[-1200:]))
    check("...a document's lines into a store are said by it (`store-stated`); what a tool derives, `store-derived`",
          ok and j['words'] == 'store-stated' and j['derive'] == 'store-derived', j)
    check("...a garden's statements never go to a public repository; to whoever runs the export, they are shown",
          ok and j['public'] and 'public' in j['public'] and j['show'], j)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\nio: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
