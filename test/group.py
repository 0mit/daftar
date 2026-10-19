#!/usr/bin/env python3
"""Groupings, one engine (core 2.15; MODEL.md, Groupings): patterns, classes and their previews.

law: core/law/lines.yaml's slots, the operations `fit`, `inherit` and `shared`, the table `groupings` read as readings of
the law, and a result's `line`; the knowledge profile's forms `pattern` and `class`; the view's `aspects` and the
archetype `cursor`; the shipped `name-patterns` (DCF's two conventions) and the fetched `media-types`.
engine (core/groupings.py): a template parsed and refused by name, matched with a date checked by its calendar (the
Persian one by bin/cal.py), digits of any script read as ASCII; mining — a counter's runs and gaps, a Persian date, a
date and a time, a digest; the line; inheritance (said, inherited, an exception nearer, set apart, suggested); a cycle;
a camera's unset clock. gate: a garden's pattern and class schemes held to their forms, each breach refused by name, a
garden's own grouping beside the law's. reckon: `fit` over the files a folder holds, `inherit` down `part` and through
the folders that hold a content, `shared` between two cursors. crosswalk: a field's `else` (an older Canon's serial in
its maker notes), the `quicktime` moment, the unset clock listed by the account. reader: shared-mime-info's database,
its document type set aside, an entity refused; the host's copy read where nothing was fetched.

Run: python3 test/group.py   (0 = green)
"""
import json, os, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'bin'))
from core import read, groupings, formats, readers  # noqa: E402
from core.law import Law  # noqa: E402
import grow  # noqa: E402

FAILS = []
PY = sys.executable


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def run(*a, cwd=None):
    e = dict(grow.ENV)
    p = subprocess.run(a, capture_output=True, text=True, encoding='utf-8', errors='replace', cwd=cwd or G, env=e)
    return p.returncode, p.stdout + p.stderr


def write(path, t):
    p = os.path.join(G, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(t)


def bean(bid, kind, title, *statements):
    write(f'beans/{bid}.md', f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{title}\"\nsummary: \"{title}, invented.\"\n"
                             "statements:\n" + ''.join(f"  - {s}\n" for s in statements) + f"---\n{title}.\n")


def gate():
    rc, out = run(PY, 'core/check.py', '.')
    return [ln for ln in out.splitlines() if ln and not ln.startswith('core check')]


def reading(name, body):
    path = os.path.join(T, f'{name}.yaml')
    with open(path, 'w', encoding='utf-8') as fh:
        fh.write(body)
    return run(PY, 'bin/reckon.py', '--ad-hoc', path)


LAW = os.path.join(ROOT, 'core', 'law')
LINES = read.data(os.path.join(LAW, 'lines.yaml'))
SYSTEMS = {str(r['system']): r for r in read.data(os.path.join(LAW, 'systems.yaml'))['systems']
           if r.get('dimension') == 'time' and r.get('reckoning') == 'arithmetic'}
SLOTS = {str(r['slot']): r for r in LINES['slots']}
T = tempfile.mkdtemp(prefix='group-')
G = os.path.join(T, 'g')
try:
    # ---- THE LAW
    L = Law.load()
    probs = L.problems()
    check("law: the law holds together with its slots, operations, groupings, forms, aspects and schemes", not probs,
          probs[:3])
    check("law: nine slots, and `fit`, `inherit`, `shared` among the operations",
          list(SLOTS) == ['counter', 'number', 'date', 'time', 'hex', 'alnum', 'word', 'text', 'extension']
          and {'fit', 'inherit', 'shared'} <= {r['op'] for r in LINES['operations']}, list(SLOTS))
    check("law: the groupings — name-series, day, root, names, passes at home in the core, moves in accounting",
          [(g['grouping'], g['home']) for g in LINES['groupings']] == [
              ('name-series', 'core'), ('day', 'core'), ('root', 'core'), ('names', 'core'), ('passes', 'core'),
              ('moves', 'accounting')], LINES['groupings'])
    P = read.data(os.path.join(LAW, 'profiles.yaml'))
    know = next(p for p in P['profiles'] if p['profile'] == 'knowledge')
    check("law: the knowledge profile brings the forms `pattern` and `class`; the view the aspects and the cursor",
          know.get('forms') == ['pattern', 'class'] and 'cursor' in [a['archetype'] for a in P['archetypes']]
          and [a['aspect'] for a in P['aspects']][:6] == ['holds', 'carried-by', 'copies', 'in-backup', 'its-series',
                                                          'its-class'], know)
    F = read.data(os.path.join(LAW, 'formats.yaml'))
    check("law: the clock epochs a device's clock counts from, each a published one",
          [e['epoch'] for e in F['clock_epochs']] == ['zero', 'quicktime', 'unix', 'fat', 'gps', 'year-00'])

    # ---- THE ENGINE: templates
    t = groupings.Template('IMG_{counter:4}.{extension}', SLOTS, systems=SYSTEMS)
    check("engine: a template matches without case and reads digits of any script as ASCII",
          t.match('img_0042.jpg') == {'counter': '0042', 'extension': 'jpg'}
          and t.match('IMG_۰۰۴۲.JPG') == {'counter': '0042', 'extension': 'JPG'} and t.match('IMG_42.jpg') is None)
    p = groupings.Template('{date:yyyymmdd}-hesabdari.{extension}', SLOTS, calendar='persian-calendar', systems=SYSTEMS)
    check("engine: a date is a day its calendar has, asked of bin/cal.py — 1397-01-19 is a Persian day, 1397-12-30 "
          "is not (1397 is no leap year)",
          p.match('13970119-hesabdari.pdf') == {'date': '13970119', 'extension': 'pdf'}
          and p.match('13971230-hesabdari.pdf') is None)
    bad = {}
    for tpl in ('{nope}', '{hex}', '{counter:x}', '{text}{text}', 'a{extension}b', '{date:dd-mm-yyyy}', 'a{b'):
        try:
            groupings.parse(tpl, SLOTS)
        except groupings.TemplateError as e:
            bad[tpl] = str(e)
    check("engine: a template not in its form is refused by name — an unknown slot, a width it needs, a width that is no "
          "number, two `text`, an extension not at the end, a form the slot lacks, an open brace",
          len(bad) == 7 and 'no slot' in bad['{nope}'] and 'names its width' in bad['{hex}'], bad)

    # ---- THE ENGINE: mining
    m = groupings.mine(['IMG_7378.CR2', 'IMG_7379.CR2', 'IMG_7381.CR2', 'IMG_7382.CR2', 'IMG_7385.CR2'], SYSTEMS)
    c = m['slots'][0] if m else {}
    check("engine: names of one shape make a template — a counter, its first and last, and the positions nobody holds",
          m and m['template'] == 'IMG_{counter:4}.{extension}' and c.get('first') == 7378 and c.get('last') == 7385
          and c.get('missing') == 3 and c.get('gaps') == [[7380, 7380], [7383, 7384]], m)
    m = groupings.mine(['13970119-hesabdari.pdf', '13970120-hesabdari.pdf', '13970125-hesabdari.pdf'], SYSTEMS)
    check("engine: a run of digits every one of which is a day of a calendar is a date of each calendar that has them "
          "all — Persian, and the arithmetical Islamic ones (1397 AH) — none chosen, and not Gregorian",
          m and m['template'] == '{date:yyyymmdd}-hesabdari.{extension}' and 'persian-calendar' in m['slots'][0]['calendars']
          and 'gregorian-civil' not in m['slots'][0]['calendars'], m)
    m = groupings.mine(['20250329_190257.jpg', '20250329_190301.jpg', '20250402_101500.jpg'], SYSTEMS)
    check("engine: a Gregorian date and a time of day, mined",
          m and m['template'] == '{date:yyyymmdd}_{time:hhmmss}.{extension}'
          and 'gregorian-civil' in m['slots'][0]['calendars'], m)
    m = groupings.mine(['0008f0bd117c57f9_0', '000941a07919a73b_0', '000a7c4488845345_0'], SYSTEMS)
    check("engine: a digest is a digest, never a date or a counter", m and m['template'] == '{hex:16}_0', m)
    check("engine: names of two shapes make no template", groupings.mine(['a1.jpg', 'bb.jpg'], SYSTEMS) is None)

    # ---- THE ENGINE: fitting and the line
    rows = groupings.rows_of([('mine', [{'code': 'cam', 'template': 'IMG_{counter:4}.{extension}', 'grouping': 'name-series'},
                                        {'code': 'thumbs', 'template': 'Thumbs.db', 'suggests': 'roles:dropping'}])],
                             SLOTS, SYSTEMS)
    items = [(f'h{i}', n, 'f1') for i, n in enumerate(
        ['IMG_7378.CR2', 'IMG_7379.CR2', 'IMG_7381.CR2', 'thumbs.db', 'notes.txt', 'IMG_9000.CR2'])] + \
        [('h9', 'IMG_0001.JPG', 'f2')]
    gs = groupings.fit(items, rows, SYSTEMS)
    by = {(g['code'], g['container']): g for g in gs}
    cam = by.get(('mine:cam', 'f1'), {})
    check("engine: fit groups each name by the most specific row it fits, inside its container, the rest by its shape",
          sorted(cam.get('members', [])) == ['h0', 'h1', 'h2', 'h5'] and ('mine:cam', 'f2') in by
          and by.get(('mine:thumbs', 'f1'), {}).get('suggests') == ['roles:dropping']
          and any(g['code'] is None and g['members'] == ['h4'] for g in gs), gs)
    ln = groupings.line(cam, ['range', 'count', 'missing'])
    check("engine: a group's one line — its range, how many, how many missing", ln == 'IMG_7378–9000.CR2 · 4 · 1,619 missing',
          ln)

    # ---- THE ENGINE: classes
    said = {'root': ['work:orchard'], 'other': ['work:personal']}
    wholes = {'sub': ['root'], 'c1': ['sub'], 'c2': ['sub', 'other'], 'c3': ['sub'], 'bin': ['root'], 'c4': ['bin']}
    sugg = {'c3': ['roles:dropping'], 'bin': ['roles:generated']}
    apart = {'roles:dropping', 'roles:generated'}

    def inh(b, fits=None):
        return groupings.inherit(b, said.get, wholes.get, lambda x: sugg.get(x, []), lambda x: x in apart, fits=fits,
                                 scheme='work')
    check("engine: said stands; a part inherits its whole's code down `part` and through the folder that holds it",
          inh('root') == [('work:orchard', 'said', 'root')] and inh('c1') == [('work:orchard', 'inherited', 'root')], inh('c1'))
    check("engine: a content held in two folders of two codes holds both — two relations, no loop",
          sorted(x[0] for x in inh('c2')) == ['work:orchard', 'work:personal'], inh('c2'))
    check("engine: a dropping is set apart by its `apart` code, and what an apart whole holds inherits nothing",
          inh('c3')[0][0] is None and 'roles:dropping' in inh('c3')[0][1] and inh('c4')[0][0] is None, (inh('c3'), inh('c4')))
    check("engine: a member that does not fit its whole is set apart, with why",
          inh('c1', fits=lambda b, w: 'by kind and day') == [(None, 'set apart: by kind and day', 'root')])
    check("engine: a cycle among a scheme's own parents is found and named",
          groupings.cycle({'a': ['b'], 'b': ['c'], 'c': ['a']}) == ['a', 'b', 'c', 'a'] and
          groupings.cycle({'a': ['b'], 'b': []}) is None)

    # ---- THE ENGINE: clocks
    ep = F['clock_epochs']
    check("engine: an unset clock — a PowerShot's 1980-01-01 00:00:10, a phone's GPS 1980-01-06, a two-digit year's "
          "2000-01-04, all zeros — and a set one",
          [groupings.unset_clock(x, ep) for x in ('1980:01:01 00:00:10', '1980:01:06 00:01:48', '2000:01:04 07:24:49',
                                                   '0000:00:00 00:00:00', '2013:05:10 14:22:01')]
          == ['fat', 'gps', 'year-00', 'zero', None])
    check("engine: the conversion `moment` carries no moment from an unset clock, and reads QuickTime's as UTC",
          formats.moment_in('1980:01:01 00:01:16', 'exif')[0] is None
          and 'never set' in formats.moment_in('1980:01:01 00:01:16', 'exif')[1]
          and formats.moment_in('2015:03:02 12:10:29', 'quicktime') == ('2015-03-02T12:10:29+00:00', None))

    # ---- THE READER: shared-mime-info
    xml = (b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE mime-info [\n  <!ELEMENT mime-info (mime-type)+>\n]>\n'
           b'<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">\n'
           b'  <mime-type type="image/x-canon-cr2"><comment>Canon CR2 raw image</comment><comment xml:lang="fa">x</comment>'
           b'<sub-class-of type="image/tiff"/><glob pattern="*.cr2"/></mime-type>\n'
           b'  <mime-type type="application/pdf"><comment>PDF document</comment><generic-icon name="x-office-document"/>'
           b'<glob pattern="*.pdf"/><alias type="application/x-pdf"/></mime-type>\n</mime-info>\n')
    got = readers.shared_mime_info(xml)['rows']
    pdf = next(r for r in got if r['code'] == 'application/pdf')
    cr2 = next(r for r in got if r['code'] == 'image/x-canon-cr2')
    check("reader: shared-mime-info — its document type set aside, each type with its English comment, its family "
          "(its generic icon, or its top-level type's), globs, what it is a subclass of",
          [r['code'] for r in got if r['level'] == 'top'] == ['application', 'image'] and pdf['family'] == 'x-office-document'
          and cr2['family'] == 'image-x-generic' and cr2['name_en'] == 'Canon CR2 raw image'
          and cr2['sub_class_of'] == 'image/tiff' and pdf['aliases'] == 'application/x-pdf', got)
    try:
        readers.shared_mime_info(xml.replace(b'<!ELEMENT mime-info (mime-type)+>', b'<!ENTITY x "y">'))
        refused = None
    except readers.Refused as e:
        refused = str(e)
    check("reader: a database that declares an entity is refused before it is read", refused and 'entity' in refused,
          refused)
    host = os.path.join(T, 'freedesktop.org.xml')
    with open(host, 'wb') as fh:
        fh.write(xml)
    import fetch as dmfetch
    check("reader: the host's copy read by the scheme's reader, kept nowhere",
          {r['code'] for r in dmfetch.read_host('media-types', host)} >= {'application/pdf', 'image/x-canon-cr2'})

    # ---- THE CROSSWALK: else, an older Canon's serial in its maker notes
    from core.crosswalk import Carry
    names = {('anchor-serial', '1234567890'): 'old-camera'}
    carry = Carry(L, 'exif-image', names=lambda ns, v: names.get((ns, v)), given_names={'*': 'anchor-serial'})
    rec = {'content': 'c-1', 'Composite:SubSecDateTimeOriginal': '2013:05:10 14:22:01', 'Canon:SerialNumber': '1234567890',
           'IFD0:Make': 'Canon', 'IFD0:Model': 'Canon EOS 450D'}
    being, sts, listed, notes, _a, _h = carry.into(rec)
    prod = next((r for v, r in sts if v == 'produce'), {})
    check("crosswalk: a field's `else` — the maker notes' serial read where the Exif has none, and not listed as left",
          prod.get('by') == 'old-camera' and not any(f == 'Canon:SerialNumber' for f, _w in listed), (sts, listed))
    rec2 = dict(rec, **{'Composite:SubSecDateTimeOriginal': '1980:01:01 00:00:10'})
    _b, sts2, listed2, _n, _a, _h = carry.into(rec2)
    prod2 = next((r for v, r in sts2 if v == 'produce'), {})
    check("crosswalk: an unset clock carries no moment, and the account lists it with its epoch",
          'at' not in prod2 and any('fat epoch' in str(w) for f, w in listed2), (sts2, listed2))

    # ---- A GARDEN: the gate, and the readings
    rel = grow.release(os.path.join(T, 'release'))
    r = grow.garden(rel, G, 'sam', '--profile', 'knowledge')
    check("garden: grown with the knowledge profile", r.returncode == 0, r.out[-800:])
    write('VOCAB.md', """---
profiles: [knowledge]
schemes:
  - { scheme: names, classifies: "the names this garden's files and folders take", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/names", levels: [ { level: pattern } ], neighbours: none, sources: extracts/names.tsv, form: pattern }
  - { scheme: work, classifies: "whose work a thing is", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/work", levels: [ { level: code } ], neighbours: none, sources: extracts/work.tsv, form: class }
  - { scheme: roles, classifies: "what a thing is in its place", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/roles", levels: [ { level: code } ], neighbours: none, sources: extracts/roles.tsv, form: class }
files:
  - { registry: names, file: extracts/names.tsv, key: code }
  - { registry: work, file: extracts/work.tsv, key: code }
  - { registry: roles, file: extracts/roles.tsv, key: code }
---
# the garden's own rows
""")
    write('extracts/names.tsv', 'code\tlevel\tname\ttemplate\treads\tsuggests\tgrouping\tmarks\twithin\n'
                                'cam\tpattern\ta camera\'s file\tIMG_{counter:4}.{extension}\t\t\tname-series\t\t\n'
                                'thumbs\tpattern\tWindows\' thumbnails\tThumbs.db\t\troles:dropping\t\t\t\n'
                                'pkg\tpattern\ta package\'s own file\tpackage.json\t\troles:code-tree\t\tby\t\n'
                                'bin\tpattern\ta build\'s output\tbin\tname.as\troles:generated\t\t\troles:code-tree\n')
    write('extracts/work.tsv', 'code\tlevel\tname\tstands_for\tapart\norchard\tcode\tthe orchard co-op\torchard\t\n'
                               'personal\tcode\tthe gardener\'s own\t\t\nother\tcode\tnone of these\t\t\n')
    write('extracts/roles.tsv', 'code\tlevel\tname\tapart\ndropping\tcode\ta system\'s dropping\ttrue\n'
                                'code-tree\tcode\ta code tree\t\ngenerated\tcode\ta build\'s output\ttrue\n')
    bean('orchard', 'org', 'the orchard co-op', 'say: { by: sam, at: now }')
    bean('d-root', 'folder', 'Orchard', 'read: { by: sam, at: now }', 'classify: { id: c, of: self, as: "work:orchard" }',
         'say: { by: sam, of: [c], at: now }')
    bean('d-sub', 'folder', 'photos', 'read: { by: sam, at: now }', 'part: { by: self, of: d-root }',
         'name: { by: d-root, of: self, as: photos }',
         'hold: { id: h1, by: self, of: c-1, as: IMG_7378.CR2 }', 'hold: { id: h2, by: self, of: c-2, as: IMG_7379.CR2 }',
         'hold: { id: h3, by: self, of: c-3, as: IMG_7381.CR2 }', 'hold: { id: h4, by: self, of: c-4, as: Thumbs.db }')
    bean('d-mine', 'folder', 'mine', 'read: { by: sam, at: now }', 'part: { by: self, of: d-root }',
         'classify: { id: c, of: self, as: "work:personal" }', 'say: { by: sam, of: [c], at: now }',
         'hold: { id: h5, by: self, of: c-5, as: notes.txt }')
    for i in range(1, 6):
        bean(f'c-{i}', 'content', f'content {i}', 'read: { by: sam, at: now }',
             f'measure: {{ of: self, as: information, value: {{ count: {i * 1000}, unit: By }} }}')
    found = gate()
    check("gate: a garden's pattern and class schemes in their forms pass", not found, found[:4])
    rc, out = run(PY, 'bin/save.py', 'sam', 'RULE-CHANGE: the schemes of names and classes; folders and files', '--body',
                  '- RULE-CHANGE: the schemes `names`, `work` and `roles`, ratified by sam\n'
                  '- action: wrote the folders, the files and the schemes\n' + ''.join(
                      f'- bean: {b}\n' for b in ['orchard', 'd-root', 'd-sub', 'd-mine', 'c-1', 'c-2', 'c-3', 'c-4', 'c-5']))
    check("gate: saved through the gate", rc == 0, out[-1200:])

    keep = open(os.path.join(G, 'extracts/names.tsv'), encoding='utf-8').read()
    write('extracts/names.tsv', keep + 'odd\tpattern\tbroken\tIMG_{nope}\t\troles:nobody\tno-such\tfolder\t\n')
    found = gate()
    check("gate: a pattern row out of its form refused by name — an unknown slot, a code no scheme has, a grouping no "
          "row is, a `marks` that is not `by`",
          any('template' in f and 'no slot' in f for f in found) and any('suggests' in f for f in found)
          and any('grouping' in f for f in found) and any('marks' in f for f in found), found)
    write('extracts/names.tsv', keep)
    keepw = open(os.path.join(G, 'extracts/work.tsv'), encoding='utf-8').read()
    write('extracts/work.tsv', keepw + 'orchard2\tcode\tthe orchard again\torchard\tmaybe\n')
    found = gate()
    check("gate: a class code standing for a being another stands for, and an `apart` that is not `true`, refused",
          any('stands for orchard' in f for f in found) and any('apart' in f for f in found), found)
    write('extracts/work.tsv', keepw)
    keepv = open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read()
    write('VOCAB.md', keepv.replace('files:\n', 'groupings:\n  - { grouping: day, home: core, meaning: "mine", steps: '
                                    '[ { id: a, op: select, kind: folder } ], line: [count] }\n'
                                    '  - { grouping: mine, home: core, meaning: "a garden\'s own", steps: [ { id: a, op: '
                                    'select, kind: folder } ], line: [count, nonsense] }\nfiles:\n'))
    found = gate()
    check("gate: a garden's own grouping read beside the law's — one named as the law's refused, a line's field the line "
          "has not refused",
          any('grouping of the law already' in f for f in found) and any('nonsense' in f for f in found), found)
    write('VOCAB.md', keepv)

    rc, out = reading('fit', 'what: "the files each folder holds, by their names"\nsteps:\n'
                             '  - { id: folders, op: select, kind: folder }\n'
                             '  - { id: files, op: select, of: folders, entries: hold }\n'
                             '  - { id: runs, op: fit, of: files, path: as, by: by }\n')
    check("reckon: `fit` — a folder's files by the pattern each fits, its run and its gap, the rest by its shape",
          rc == 0 and 'IMG_7378–7381.CR2 in d-sub' in out and 'Thumbs.db in d-sub' in out and 'notes.txt in d-mine' in out,
          out[-1500:])
    rc, out = reading('inherit', 'what: "whose work each content is"\ninputs:\n  - { name: scheme, origin: { act: say }, '
                                 'type: kebab }\nsteps:\n  - { id: contents, op: select, kind: content }\n'
                                 '  - { id: classed, op: inherit, of: contents, scheme: { input: scheme } }\n')
    rc, out = run(PY, 'bin/reckon.py', '--ad-hoc', os.path.join(T, 'inherit.yaml'), '--input', 'scheme=work')
    check("reckon: `inherit` — a content inherits the orchard's code through its folder and that folder's whole; one in the "
          "gardener's own folder holds that nearer code; Thumbs.db is set apart as a dropping",
          rc == 0 and 'work:orchard (inherited from d-root)' in out and 'work:personal (inherited from d-mine)' in out
          and 'set apart: roles:dropping' in out, out[-1500:])
    rc, out = reading('shared', 'what: "what two folders both carry"\nsteps:\n'
                                '  - { id: two, op: select, kind: content, where: [ { path: bean, "∈": [c-1, c-5] } ] }\n'
                                '  - { id: both, op: shared, of: two, aspect: carried-by }\n')
    check("reckon: `shared` — what two cursors both reach by an aspect's relation: nothing carries c-1 and c-5 both",
          rc == 0 and '= groups' in out and 'd-' not in out.split('= groups')[-1], out[-800:])
    rc, out = reading('shared2', 'what: "what carries the first three files"\nsteps:\n'
                                 '  - { id: three, op: select, kind: content, where: [ { path: bean, "∈": [c-1, c-2, c-3] } ] }\n'
                                 '  - { id: both, op: shared, of: three, aspect: carried-by }\n')
    check("reckon: `shared` — the folder that carries all three", rc == 0 and 'd-sub' in out.split('= groups')[-1],
          out[-800:])

    # ---- the gate's replies: one line for one refusal in many places
    for i in (1, 2, 3, 4, 5, 7):
        bean(f'x-{i:04d}', 'content', f'x {i}', 'read: { by: sam, at: now }', 'part: { by: self }')
    found = gate()
    one = [f for f in found if '(× 6)' in f]
    check("gate: one rule saying one thing of six beans is one line, its places shown as their group's line",
          len(one) == 1 and 'x-0001–0007' in one[0] and '1 missing' in one[0], found)
    for i in (1, 2, 3, 4, 5, 7):
        os.remove(os.path.join(G, 'beans', f'x-{i:04d}.md'))

    # ---- bin/group.py over a store
    prog = r"""
import sys
sys.path.insert(0, 'bin'); sys.path.insert(0, '.')
from store import Store
s = Store(sys.argv[1])
s.being('vol-a', 'volume', 'a volume, invented')
for b in ('d-top', 'd-day', 'd-nm', 'd-docs', 'd-app', 'd-app-bin', 'd-bin'):
    s.being(b, 'folder')
for i in range(1, 12):
    s.being(f'c-{i}', 'content')
A = 'vol-a#' + s.put('vol-a', 'read', {'id': 'scan-1', 'by': 'sam', 'from': 'vol-a', 'at': '2026-10-18T10:00:00+03:00'})
for b, whole, name in (('d-top', 'vol-a', 'top'), ('d-day', 'd-top', '2015-11-20'), ('d-nm', 'd-top', 'node_modules'),
                       ('d-docs', 'd-top', 'docs'), ('d-app', 'd-top', 'app'), ('d-app-bin', 'd-app', 'bin'),
                       ('d-bin', 'd-top', 'bin')):
    s.put(b, 'part', {'by': 'self', 'of': whole}, act=A)
    s.put(b, 'name', {'by': whole, 'of': 'self', 'as': name}, act=A)
files = [('d-day', 'IMG_7475.CR2', 1), ('d-day', 'IMG_7476.CR2', 2), ('d-day', 'IMG_7479.CR2', 3), ('d-day', 'Thumbs.db', 4),
         ('d-nm', 'index.js', 5), ('d-nm', 'package.json', 6), ('d-docs', 'report.pdf', 7), ('d-docs', 'IMG_7480.CR2', 8),
         ('d-app', 'package.json', 9), ('d-app-bin', 'app.exe', 10), ('d-bin', 'tool.sh', 11)]
for folder, name, i in files:
    s.put(f'c-{i}', 'measure', {'of': 'self', 'as': 'information', 'value': {'count': str(1000000 * (12 - i)), 'unit': 'By'}}, act=A)
    s.put(folder, 'hold', {'by': 'self', 'of': f'c-{i}', 'as': name}, act=A)
print('built')
"""
    write('build_store.py', prog)
    store_file = os.path.join(T, 'cat.sqlite')
    rc, out = run(PY, 'build_store.py', store_file)
    check("group: a small store built — a volume, its folders and files, each content's size", rc == 0 and 'built' in out,
          out[-1800:])
    os.remove(os.path.join(G, 'build_store.py'))
    write('extracts/names.tsv', keep + 'nm\tpattern\ta package manager\'s tree\tnode_modules\tname.as\troles:generated\t\t\t\n')
    rc, out = run(PY, 'bin/group.py', 'of', 'd-day', '--path', store_file)
    check("group: `of` a folder — its runs of names in their lines, the registry first (the garden's own camera row), the rest by "
          "their shape", rc == 0 and 'IMG_7475–7479.CR2 · 3 · 2 missing' in out and 'Thumbs.db · 1' in out, out[-800:])
    rc, out = run(PY, 'bin/group.py', 'root', 'd-top', '--code', 'work:orchard', '--path', store_file)
    check("group: `root` — a code read as said of a folder holds beneath it; a dropping and a package manager's tree "
          "are set apart by their `apart` codes, with why",
          rc == 0 and 'work:orchard' in out and 'names:thumbs → roles:dropping' in out
          and 'folder names:nm → roles:generated' in out, out[-1200:])
    check("group: `root` — a `bin` inside a tree a package.json marks as code is a build's output, set apart (a row that "
          "applies `within` a code tree); a `bin` elsewhere is its root's own",
          rc == 0 and 'folder names:bin → roles:generated' in out and 'set apart' in out
          and out.count('roles:generated') == 2, out[-1200:])
    rc, out = run(PY, 'bin/group.py', 'measure', '--path', store_file, '-j', '2')
    check("group: `measure` — every name of the store fitted, spread over processes",
          rc == 0 and '11 names in 6 folders' in out, out[-800:])
    rc, out = run(PY, 'bin/group.py', 'mine', '--path', store_file, '--top', '10', '--min', '2', '--json')
    got = json.loads(out[out.index('{'):]) if rc == 0 and '{' in out else {}
    check("group: `mine` — the largest folders' names fitted, the registry's counted, the rest's templates ranked",
          rc == 0 and got.get('known', {}).get('names:cam') == 4, out[-800:])
    rc, out = run(PY, 'bin/group.py', 'line', 'hold-0001', 'hold-0002', 'hold-0003', 'hold-0007', 'notes.txt')
    check("group: `line` — any list of names in the lines of the grouping `names`, what the gate's replies print",
          rc == 0 and 'hold-0001–0007 · 4 · 3 missing' in out, out[-600:])
    write('extracts/names.tsv', keep)

    # ---- accounting: a statement's lines grouped by the pattern of their words (the grouping `moves`)
    G2 = os.path.join(T, 'books')
    r = grow.garden(rel, G2, 'sam', '--profile', 'accounting', '--profile', 'knowledge')
    check("moves: a garden that keeps accounts, grown", r.returncode == 0, r.out[-600:])
    G1, G = G, G2
    write('VOCAB.md', """---
profiles: [accounting, knowledge]
schemes:
  - { scheme: merchants, classifies: "the words a bank writes for a merchant", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/merchants", levels: [ { level: pattern } ], neighbours: none, sources: extracts/merchants.tsv, form: pattern }
  - { scheme: home, classifies: "where Sam's money goes", holding: extract, licence: CC0-1.0, publisher: the gardener, url: "https://example.org/home", levels: [ { level: plan }, { level: account } ], neighbours: none, sources: extracts/home.tsv }
files:
  - { registry: merchants, file: extracts/merchants.tsv, key: code }
  - { registry: home, file: extracts/home.tsv, key: code }
---
# the garden's own rows
""")
    write('extracts/merchants.tsv', 'code\tlevel\tname\ttemplate\treads\tsuggests\tgrouping\n'
                                    'migros\tpattern\ta supermarket\'s branch\tMIGROS {number:4} {word}\tnote\thome:food\tmoves\n'
                                    'fuel\tpattern\ta fuel station\tSHELL {counter:4}\tnote\thome:car\tmoves\n')
    write('extracts/home.tsv', 'code\tlevel\tparent\tname\nspend\tplan\t\twhere it goes\nfood\taccount\tspend\tfood\n'
                               'car\taccount\tspend\tthe car\n')
    lines = [('MIGROS 1234 ISTANBUL', '12.50'), ('MIGROS 5678 ANKARA', '30.00'), ('SHELL 0001', '900.00'),
             ('SHELL 0002', '850.00'), ('NETFLIX.COM', '199.99'), ('MIGROS 1234 ISTANBUL', '7.25')]
    bean('statement-sept', 'document', 'a bank statement, September', 'read: { by: sam, at: now }',
         *[f'pay: {{ id: line-{i:03d}, by: sam, of: {{ count: "{amt}", unit: TRY }}, at: "2026-09-{i:02d}", note: "{w}" }}'
           for i, (w, amt) in enumerate(lines, 1)])
    found = gate()
    check("moves: a statement's lines and a scheme of merchants' words pass the gate", not found, found[:4])
    rc, out = reading('moves', 'what: "the lines of one merchant"\nsteps:\n'
                               '  - { id: statements, op: select, kind: document }\n'
                               '  - { id: lines, op: select, of: statements, entries: pay }\n'
                               '  - { id: merchants, op: fit, of: lines, path: note }\n')
    check("moves: accounting's category of moves as a grouping — a supermarket's lines in one group (its branches' "
          "words a slot), a fuel station's in another with its counter, the rest each by its shape",
          rc == 0 and 'MIGROS {number:4} {word}: 3' in out and 'SHELL 0001–0002: 2' in out and 'NETFLIX.COM: 1' in out,
          out[-1200:])
    G = G1
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ngroup: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
