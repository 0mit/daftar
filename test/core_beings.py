#!/usr/bin/env python3
"""core_beings — the schemes of known beings on the ladder (core 4.1): a scheme that names the positions it classifies
(`at`), the readers of the open standards of known beings, the codes looked up in their sorted index, and the one
finder.

- the law: the eleven schemes' rows, each `at` the positions the ladder's design gives it (option scheme-at A), Wikidata
  with none; each held as its licence allows; the law's proof reads no problem of them;
- the readers, each on a small file of its format: `obo` (an ontology's own terms, its ranks, synonyms, parts and an
  obsolete term; an imported term left out), `coldp`, `etim-csv` (UTF-16, as ETIM writes it), `cpv-genericode` and
  `iucn-get-maps`, and what each refuses;
- the index: a fetched copy keeps its codes sorted, and a code is found there by a binary search, never by its rows;
- the gate: a taxon said of a person (an organism) and an anatomy's code of an organ stand; a taxon of a host, an
  organ's code of a component and ETIM's class of a product (a sayable, which holds no position) are refused by rule
  `bearer`, naming the positions; a code its copy lacks is refused;
- the finder: `propose` reads only the schemes whose `at` names a position the being's kind holds, by a name, a folded
  plural or a synonym; it asks no authority anything, and has no way to; `find` passes the schemes of beings over
  unless one is named.

Run: python3 test/core_beings.py   (0 = green)
"""
import io, os, shutil, subprocess, sys, tempfile, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = tempfile.mkdtemp(prefix='core-beings-')
CACHE = os.path.join(T, 'cache')
os.environ['DAFTAR_STANDARDS_CACHE'] = CACHE
for _p in (ROOT, os.path.join(ROOT, 'bin')):
    sys.path.insert(0, _p)
sys.path.append(os.path.join(ROOT, 'test'))
import grow  # noqa: E402
import fetch as dmfetch  # noqa: E402
import knowledge as dmk  # noqa: E402
from core import read, readers  # noqa: E402
from core.formats import Refused  # noqa: E402
from core.law import Law  # noqa: E402

grow.ENV['DAFTAR_STANDARDS_CACHE'] = CACHE
FAILS = []
PY = sys.executable
LAW = os.path.join(ROOT, 'core', 'law')


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[:1500]))
    if not cond:
        FAILS.append(name)


def refused(f, *a):
    try:
        f(*a)
    except Refused as e:
        return str(e)
    return ''


try:
    # ---- THE LAW
    reg = read.data(os.path.join(LAW, 'registries.yaml'))
    schemes = {r['scheme']: r for r in reg['knowledge_schemes']}
    AT = {'col': ['organism'], 'ncbitaxon': ['organism'], 'uberon': ['organ', 'tissue'], 'cl': ['cell'],
          'hao': ['organ', 'tissue'], 'po': ['organ', 'tissue'], 'chebi': ['molecule', 'material'],
          'iucn-get': ['ecosystem'], 'etim': ['device', 'component'], 'cpv': ['device', 'component']}
    check("schemes: each scheme of beings names the positions it classifies, as the ladder's option scheme-at A gives "
          "them, and Wikidata none",
          all(schemes[s].get('at') == a for s, a in AT.items()) and 'at' not in schemes['wikidata'],
          {s: schemes.get(s, {}).get('at') for s in AT})
    check("schemes: held as each licence allows — each fetched by every machine, never shipped; Wikidata at its "
          "authority, checked by its form",
          all(schemes[s]['holding'] == 'fetched' and schemes[s]['fetch'].get('reader') for s in AT)
          and schemes['etim']['licence'] == 'ODC-By-1.0' and schemes['wikidata']['holding'] == 'at-authority'
          and schemes['wikidata'].get('code_pattern')
          and not {'named_in', 'lookup', 'classes'} & {k for r in schemes.values() for k in r})
    L = Law.load()
    check("the law's own proof reads no problem of a scheme's positions", not L.scheme_at_problems(),
          L.scheme_at_problems())

    # ---- THE READERS
    OBO = b"""format-version: 1.2
data-version: tiny/releases/2026-01-01
ontology: tiny

[Term]
id: TINY:0000001
name: heart
synonym: "cardium" RELATED []
synonym: "cor" EXACT []
is_a: TINY:0000002 ! organ
relationship: part_of TINY:0000003 ! body

[Term]
id: TINY:0000002
name: organ

[Term]
id: TINY:0000003
name: body
is_a: OTHER:0000009 ! a parent imported

[Term]
id: OTHER:0000009
name: a term imported

[Term]
id: TINY:0000004
name: obsolete thing
is_obsolete: true

[Typedef]
id: part_of
name: part of
"""
    got = readers.obo(OBO)
    rows = {r['code']: r for r in got['rows']}
    check("obo: the ontology's own terms alone, by their local codes, the release its data-version",
          sorted(rows) == ['0000001', '0000002', '0000003', '0000004'] and got['release'] == 'tiny/releases/2026-01-01',
          (sorted(rows), got['release']))
    h = rows['0000001']
    check("obo: a term's parent, what it is part of, its exact and its other synonyms; an imported parent left out; an "
          "obsolete term marked",
          h['parent'] == '0000002' and h['part_of'] == '0000003' and h['synonyms'] == 'cor' and h['related'] == 'cardium'
          and h['level'] == 'term' and rows['0000003']['parent'] == '' and rows['0000004']['status'] == 'obsolete', rows)
    tax = readers.obo(b"format-version: 1.2\nontology: ncbitaxon\n\n[Term]\nid: NCBITaxon:7460\nname: Apis mellifera\n"
                      b"synonym: \"honey bee\" EXACT genbank_common_name []\nis_a: NCBITaxon:7459 ! Apis\n"
                      b"property_value: has_rank NCBITaxon:species\n")
    check("obo: a taxon's rank is its level, its common name a synonym",
          tax['rows'][0]['level'] == 'species' and tax['rows'][0]['synonyms'] == 'honey bee'
          and tax['rows'][0]['code'] == '7460', tax)
    check("obo: a file with no header, and a term twice, refused",
          'no OBO ontology' in refused(readers.obo, b"[Term]\nid: X:1\n")
          and 'twice' in refused(readers.obo, OBO.replace(b'id: TINY:0000004', b'id: TINY:0000002')))

    def zipped(files):
        b = io.BytesIO()
        with zipfile.ZipFile(b, 'w') as z:
            for n, data in files.items():
                z.writestr(n, data)
        return b.getvalue()

    USAGE = ('col:ID\tcol:parentID\tcol:status\tcol:rank\tcol:scientificName\tcol:authorship\tcol:extinct\n'
             'A1\t\taccepted\tkingdom\tAnimalia\t\t\nB2\tA1\taccepted\tgenus\tApis\tLinnaeus, 1758\t\n'
             'FN46\tB2\taccepted\tspecies\tApis mellifera\tLinnaeus, 1758\t\n'
             'SYN1\tFN46\tsynonym\tspecies\tApis mellifica\tLinnaeus, 1761\t\n')
    COL = zipped({'metadata.yaml': 'alias: COL99.1 XR\nissued: 2099-01-01\n', 'NameUsage.tsv': USAGE})
    got = readers.coldp(COL)
    rows = {r['code']: r for r in got['rows']}
    check("coldp: each name usage — rank, parent, authorship, status, a synonym's parent the taxon it names; the release "
          "its alias and day",
          len(rows) == 4 and rows['FN46'] == {'code': 'FN46', 'level': 'species', 'parent': 'B2', 'name': 'Apis mellifera',
                                              'authorship': 'Linnaeus, 1758', 'status': 'accepted'}
          and rows['SYN1']['parent'] == 'FN46' and rows['SYN1']['status'] == 'synonym' and got['release'] == 'COL99.1 XR 2099-01-01',
          (rows, got['release']))
    check("coldp: a package with no NameUsage.tsv, and an id twice, refused",
          'no NameUsage.tsv' in refused(readers.coldp, zipped({'Name.tsv': 'x'}))
          and 'second row' in refused(readers.coldp, zipped({'NameUsage.tsv': USAGE + 'FN46\tB2\taccepted\tspecies\tX y\t\t\n'})))

    def utf16(text):
        return text.encode('utf-16-le')

    ETIM = zipped({'ETIMARTGROUP.csv': utf16('ARTGROUPID;GROUPDESC\r\nEG020017;Machine element\r\n'),
                   'ETIMARTCLASS.csv': utf16('ARTCLASSID;ARTGROUPID;ARTCLASSDESC;ARTCLASSVERSION;ARTCLASSVERSIONDATE\r\n'
                                             'EC003882;EG020017;V belt pulley;3;\r\n'),
                   'ETIMARTCLASSSYNONYMMAP.csv': utf16('ARTCLASSID;CLASSSYNONYM\r\nEC003882;Belt pulley\r\n'
                                                       'EC003882;V belt pulley\r\n')})
    got = readers.etim_csv(ETIM)
    check("etim-csv: its UTF-16 tables, each group and each class in its group, a class's synonyms but its own name",
          got == [{'code': 'EG020017', 'level': 'group', 'parent': '', 'name': 'Machine element', 'synonyms': '', 'version': ''},
                  {'code': 'EC003882', 'level': 'class', 'parent': 'EG020017', 'name': 'V belt pulley',
                   'synonyms': 'Belt pulley', 'version': '3'}], got)
    check("etim-csv: a class in a group the export has not, refused",
          'no class read here' in refused(readers.etim_csv, zipped({
              'ETIMARTGROUP.csv': utf16('ARTGROUPID;GROUPDESC\r\n'),
              'ETIMARTCLASS.csv': utf16('ARTCLASSID;ARTGROUPID;ARTCLASSDESC;ARTCLASSVERSION;ARTCLASSVERSIONDATE\r\n'
                                        'EC003882;EG999999;x;1;\r\n'),
              'ETIMARTCLASSSYNONYMMAP.csv': utf16('ARTCLASSID;CLASSSYNONYM\r\n')})))

    def gc(codes):
        rows = ''.join(f'<Row><Value ColumnRef="Code"><SimpleValue>{c}</SimpleValue></Value><Value ColumnRef="Name">'
                       f'<SimpleValue>{n}</SimpleValue></Value><Value ColumnRef="de_label"><SimpleValue>x</SimpleValue>'
                       f'</Value></Row>' for c, n in codes)
        return ('<?xml version="1.0" encoding="UTF-8"?><gc:CodeList xmlns:gc="http://docs.oasis-open.org/codelist/ns/'
                'genericode/1.0/"><Identification><CanonicalVersionUri>http://publications.europa.eu/resource/dataset/cpv/'
                f'20990101-0</CanonicalVersionUri></Identification><SimpleCodeList>{rows}</SimpleCodeList></gc:CodeList>'
                ).encode()
    got = readers.cpv_genericode(gc([('42000000', 'Industrial machinery'), ('42100000', 'Machinery for mechanical power'),
                                     ('42140000', 'Gears and driving elements'), ('42141000', 'Plain gears'),
                                     ('42141400', 'Flywheels and pulleys')]))
    rows = {r['code']: r for r in got['rows']}
    check("cpv-genericode: each code's level by its digits not zero, its parent the nearest code above it, its English "
          "name; the release the list's version",
          [(rows[c]['level'], rows[c]['parent']) for c in sorted(rows)] == [
              ('division', ''), ('group', '42000000'), ('class', '42100000'), ('category', '42140000'),
              ('category', '42141000')] and rows['42141400']['name'] == 'Flywheels and pulleys'
          and got['release'].endswith('20990101-0'), (rows, got['release']))
    check("cpv-genericode: a code of seven digits, and a document type, refused",
          'no code of the CPV' in refused(readers.cpv_genericode, gc([('4200000', 'x')]))
          and 'document type' in refused(readers.cpv_genericode, b'<!DOCTYPE x [<!ENTITY a "b">]><x/>'))
    GET = (b'<?xml version="1.0" ?><root><Maps><Map efg_code="T2.2" update="2020-11-08"><Functional_group>T2.2 Deciduous '
           b'temperate forests</Functional_group></Map><Map efg_code="F1.1" update="2021-12-20"><Functional_group>F1.1 '
           b'Permanent upland streams</Functional_group></Map></Maps></root>')
    got = readers.iucn_get_maps(GET)
    check("iucn-get-maps: each functional group with its name, its biome and realm by their codes alone; the release the "
          "latest update",
          [(r['code'], r['level'], r['parent'], r['name']) for r in got['rows']] == [
              ('F', 'realm', '', ''), ('T', 'realm', '', ''), ('F1', 'biome', 'F', ''), ('T2', 'biome', 'T', ''),
              ('F1.1', 'group', 'F1', 'Permanent upland streams'), ('T2.2', 'group', 'T2', 'Deciduous temperate forests')]
          and got['release'] == 'the maps updated to 2021-12-20', got)
    check("iucn-get-maps: a map whose name is not its code's refused",
          'no functional group' in refused(readers.iucn_get_maps, GET.replace(b'>T2.2 Deciduous', b'>Deciduous')))

    # ---- THE INDEX: a code of a fetched copy found by a binary search
    sha, rows, d = dmfetch.keep('col', COL, 'test')
    with open(os.path.join(d, 'codes.txt'), encoding='utf-8') as fh:
        codes = fh.read().split('\n')
    check("fetch: the copy keeps its codes sorted, one a line", codes == ['A1', 'B2', 'FN46', 'SYN1', ''], codes)
    K = dmk.Knowledge(ROOT)
    check("knowledge: a code is found in the sorted codes, and one the copy lacks is not — its rows never read",
          K.has('col', 'FN46') and K.has('col', 'A1') and K.has('col', 'SYN1') and not K.has('col', 'FN47')
          and not K.has('col', 'B') and 'col' not in K._rows)
    big = os.path.join(T, 'codes.txt')
    with open(big, 'w', encoding='utf-8') as fh:
        fh.writelines('%07d\n' % i for i in range(0, 400000, 3))
    check("knowledge: the binary search over a long index finds each code it holds and none it does not",
          all(dmk._sorted_has(big, '%07d' % i) == (i % 3 == 0 and i < 400000)
              for i in (0, 1, 3, 299997, 299998, 399999, 400002)))

    # ---- THE GATE: rule bearer and a scheme's positions
    dmfetch.keep('etim', ETIM, 'test')
    REL = grow.release(os.path.join(T, 'release'))
    G = os.path.join(T, 'garden')
    r = grow.garden(REL, G, 'sam', '--profile', 'knowledge')
    check("a garden grows with the knowledge profile", r.returncode == 0, r.out[-600:])

    def bean(bid, kind, title, *statements):
        with open(os.path.join(G, 'beans', bid + '.md'), 'w', encoding='utf-8') as fh:
            fh.write(f"---\nbean: {bid}\nkind: {kind}\ntitle: \"{title}\"\nstatements:\n"
                     + ''.join(f"  - {s}\n" for s in statements) + f"---\n{title}.\n")

    def gate():
        p = grow.run(PY, 'core/check.py', '.', cwd=G)
        return [ln for ln in p.out.splitlines() if ln and not ln.startswith('core check')]

    bean('a-heart', 'organ', 'a heart', 'read: { by: sam, at: now }', 'classify: { of: self, as: "uberon:0000948" }')
    bean('a-pulley', 'component', 'a V belt pulley', 'read: { by: sam, at: now }',
         'classify: { of: self, as: "etim:EC003882" }')
    with open(os.path.join(G, 'beans', 'sam.md'), encoding='utf-8') as fh:
        text = fh.read()
    with open(os.path.join(G, 'beans', 'sam.md'), 'w', encoding='utf-8') as fh:
        fh.write(text.replace('statements:\n', 'statements:\n  - classify: { of: self, as: "col:FN46" }\n', 1))
    found = gate()
    check("gate: a taxon of a person (an organism), an anatomy's code of an organ and ETIM's class of a component stand",
          not found, found[:6])
    bean('edge-router', 'host', 'the edge router', 'read: { by: sam, at: now }', 'classify: { of: self, as: "col:FN46" }')
    bean('a-ring', 'component', 'a ring', 'read: { by: sam, at: now }', 'classify: { of: self, as: "uberon:0000948" }')
    bean('motor-offer', 'product', 'an electric motor, as sold', 'read: { by: sam, at: now }',
         'classify: { of: self, as: "etim:EC003882" }')
    found = gate()
    check("gate: a taxon of a host is refused by rule bearer, naming the positions the scheme classifies and the host's",
          any('bearer' in f and 'edge-router' in f and "col's codes classify beings at organism, and a host holds "
              "organisation device" in f for f in found), found)
    check("gate: an organ's code of a component is refused alike",
          any('bearer' in f and 'a-ring' in f and "uberon's codes classify beings at organ, tissue" in f for f in found),
          found)
    check("gate: ETIM's class of a product, a sayable, is refused: it holds no position on the ladder",
          any('bearer' in f and 'motor-offer' in f and 'no position on the ladder' in f for f in found), found)
    for b in ('edge-router', 'a-ring', 'motor-offer'):
        os.remove(os.path.join(G, 'beans', b + '.md'))
    bean('bee-three', 'component', 'a part', 'read: { by: sam, at: now }', 'classify: { of: self, as: "etim:EC999999" }')
    found = gate()
    check("gate: a code the fetched copy does not hold is refused, looked up in its index",
          any('bee-three' in f and 'EC999999' in f and 'no code of etim' in f for f in found), found)
    os.remove(os.path.join(G, 'beans', 'bee-three.md'))

    # ---- THE FINDER
    K = dmk.Knowledge(G)
    check("propose: the schemes asked for a position are those whose `at` names it",
          K.at_positions(['organism']) == ['col', 'ncbitaxon'] and K.at_positions(['component']) == ['cpv', 'etim']
          and K.at_positions(['organism', 'living', 'reason']) == ['col', 'ncbitaxon'] and K.at_positions(['device']) == ['cpv', 'etim'],
          (K.at_positions(['organism']), K.at_positions(['component'])))
    got = [p['coding'] for p in K.propose('Apis mellifera', ['organism'])]
    check("propose: a taxon by its name, from the copy fetched here, and nothing of a scheme of made things",
          got == ['col:FN46'], got)
    got = [p['coding'] for p in K.propose('V belt pulleys', ['component'])]
    check("propose: a made class by its name, its plural folded", got == ['etim:EC003882'], got)
    check("propose: nothing for the same words at a position its schemes do not classify",
          not K.propose('V belt pulley', ['organism']))
    got = [(p['coding'], p['how']) for p in K.propose('belt pulley', ['component'])]
    check("propose: a class by its synonym", got == [('etim:EC003882', 'synonym')], got)
    check("find: the schemes of beings are passed over unless one is named",
          not [x for x in K.find('pulley') if x[1] == 'etim'] and [x for x in K.find('pulley', scheme='etim')])
    check("propose: it holds no way to ask an authority — no reader of an API, no `--wikidata`",
          not any(hasattr(dmk, n) for n in ('web_get', 'items_at', 'UA'))
          and '--wikidata' not in (dmk.__doc__ or ''))
    p = grow.run(PY, 'bin/knowledge.py', 'propose', 'sam', cwd=G)
    check("propose a bean: the positions read from its kind, its words from its title",
          p.returncode == 0 and 'at organism, living, reason' in p.out, p.out[-600:])
    p = grow.run(PY, 'bin/knowledge.py', 'propose', 'motor-offer', cwd=G)
    check("propose a bean that is no bean here: refused", p.returncode == 1 and 'no bean' in p.out, p.out[-400:])
    bean('motor-offer', 'product', 'an electric motor, as sold', 'read: { by: sam, at: now }')
    p = grow.run(PY, 'bin/knowledge.py', 'propose', 'motor-offer', cwd=G)
    check("propose a bean of a sayable kind: refused, it holds no position", p.returncode == 1
          and 'at no position of the ladder' in p.out, p.out[-400:])
    p = grow.run(PY, 'bin/knowledge.py', 'propose', '--at', 'component', 'V', 'belt', 'pulley', cwd=G)
    check("propose at the command line, at a position", p.returncode == 0 and 'etim:EC003882' in p.out, p.out[-400:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\n{len(FAILS)} failed" if FAILS else "\n0 failed")
sys.exit(1 if FAILS else 0)
