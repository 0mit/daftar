#!/usr/bin/env python3
"""core_beings — the beings by their levels (core 3.2): a body kind a level, a scheme that names
the levels it classifies (`at`), the readers of the open standards of known beings, the codes looked up in their sorted
index, the one finder, and the machine elements daftar writes for what the open standards leave.

- the law: `organism` beside `person` and a body kind for each other level, each a universal vacancy; the twelve
  schemes' rows, each `at` a level of the law, and a copy of the law whose `at` names no level refused;
- the readers, each on a small file of its format: `obo` (an ontology's own terms, its ranks, synonyms, parts and an
  obsolete term; an imported term left out), `coldp`, `etim-csv` (UTF-16, as ETIM writes it), `cpv-genericode` and
  `iucn-get-maps`, and what each refuses;
- the index: a fetched copy keeps its codes sorted, and a code is found there by a binary search, never by its rows;
- the gate: a taxon said of an organism stands, of a host is refused by rule `bearer`, naming the levels; a machine
  element of a component stands, of an organism is refused; a sayable classed by ETIM stands; a code its copy lacks is
  refused;
- the finder: `propose` reads only the schemes whose `at` names the being's level; Wikidata's items picked by their
  class, never their label, and through an item the codes of the schemes it names; a lookup at Wikidata refused, nothing
  sent, until the garden's flow law grants the party; `find` passes the schemes of beings over unless one is named;
- machine-elements.tsv in its form: every parent and whole a row of it, every item and code in its scheme's form.

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
import copy  # noqa: E402
import csv  # noqa: E402
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
    kinds = {r['kind']: r for r in read.data(os.path.join(LAW, 'kinds.yaml'))['kinds']}
    levels = {r['level'] for r in read.data(os.path.join(LAW, 'levels.yaml'))['levels']}
    BODIES = ('organism', 'cell', 'tissue', 'organ', 'population', 'community', 'ecosystem', 'material', 'component',
              'celestial-body')
    check("kinds: organism a body at level organism beside person (rung reason), host the made body at device",
          kinds['organism'].get('nature') == 'body' and kinds['organism'].get('level') == 'organism'
          and not kinds['organism'].get('rung') and kinds['person'].get('rung') == 'reason'
          and kinds['host'].get('level') == 'device', (kinds.get('organism'), kinds.get('host')))
    check("kinds: a body kind for each other level a body can be at, each at its own level",
          all(kinds.get(k, {}).get('nature') == 'body' and kinds[k].get('level') == k for k in BODIES),
          [k for k in BODIES if kinds.get(k, {}).get('level') != k])
    vac = {(v['at'], v['position']): v for v in read.data(os.path.join(LAW, 'vacancies.yaml'))['vacancies']}
    check("vacancies: each of them a universal vacancy of the table kinds",
          all(vac.get(('table:kinds', k), {}).get('reason') == 'universal' for k in BODIES),
          [k for k in BODIES if ('table:kinds', k) not in vac])
    reg = read.data(os.path.join(LAW, 'registries.yaml'))
    schemes = {r['scheme']: r for r in reg['knowledge_schemes']}
    AT = {'col': ['organism', 'population'], 'ncbitaxon': ['organism', 'population'], 'uberon': ['organ', 'tissue'],
          'cl': ['cell'], 'hao': ['organ', 'tissue'], 'po': ['organ', 'tissue', 'cell'], 'iucn-get': ['ecosystem'],
          'etim': ['component', 'device'], 'machine-elements': ['component', 'device']}
    check("schemes: each scheme of beings names the levels it classifies, each a level of the law",
          all(schemes[s].get('at') == a for s, a in AT.items())
          and all(set(r.get('at') or []) <= levels for r in schemes.values()),
          {s: schemes.get(s, {}).get('at') for s in AT})
    check("schemes: held as each licence allows — ETIM and CPV fetched, never shipped; Wikidata at its authority, typed "
          "by its classes; machine-elements daftar's own, shipped under CC BY 4.0",
          schemes['etim']['holding'] == 'fetched' and schemes['etim']['licence'] == 'ODC-By-1.0'
          and schemes['cpv']['holding'] == 'fetched' and schemes['wikidata']['holding'] == 'at-authority'
          and schemes['wikidata']['lookup'] == {'api': 'https://www.wikidata.org/w/api.php', 'instance_of': 'P31',
                                                'subclass_of': 'P279'}
          and not schemes['wikidata'].get('at')
          and schemes['machine-elements']['holding'] == 'shipped' and schemes['machine-elements']['licence'] == 'CC-BY-4.0')
    L = Law.load()
    check("the law's own proof reads no problem of a scheme's levels", not L.scheme_levels_problems(),
          L.scheme_levels_problems())
    bad = os.path.join(T, 'law')
    shutil.copytree(LAW, bad)
    with open(os.path.join(bad, 'registries.yaml'), encoding='utf-8') as fh:
        text = fh.read()
    with open(os.path.join(bad, 'registries.yaml'), 'w', encoding='utf-8') as fh:
        fh.write(text.replace('    at: [organism, population]\n    named_in: [{ scheme: wikidata, property: P10585 }]',
                              '    at: [organism, organism, a-garden]\n    named_in: [{ scheme: nowhere, property: P1 }]', 1))
    L2 = copy.copy(L)
    L2.dir = bad
    probs = [m for _w, m in L2.scheme_levels_problems()]
    check("...and a copy whose `at` names no level, names a level twice, or is named in no scheme, refused",
          any("'a-garden' is no level of the law" in m for m in probs) and any('a level twice' in m for m in probs)
          and any('named_in' in m for m in probs), probs)

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

    # ---- THE GATE: rule bearer and a scheme's levels
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

    bean('hive-bee', 'organism', 'Apis mellifera', 'read: { by: sam, at: now }', 'classify: { of: self, as: "col:FN46" }')
    bean('pulley-a', 'component', 'a pulley', 'read: { by: sam, at: now }',
         'classify: { of: self, as: "machine-elements:pulley" }')
    bean('motor-offer', 'product', 'an electric motor, as sold', 'read: { by: sam, at: now }',
         'classify: { of: self, as: "etim:EC001851" }')
    found = gate()
    check("gate: a taxon of an organism, a machine element of a component, and ETIM's class of a product (a sayable, "
          "at no level) stand", not found, found[:6])
    bean('edge-router', 'host', 'the edge router', 'read: { by: sam, at: now }', 'classify: { of: self, as: "col:FN46" }')
    bean('bee-two', 'organism', 'a bee', 'read: { by: sam, at: now }',
         'classify: { of: self, as: "machine-elements:pulley" }')
    found = gate()
    check("gate: a taxon of a host is refused by rule bearer, naming the levels the scheme classifies and the host's",
          any('bearer' in f and 'edge-router' in f and "col's codes classify beings at organism, population, and a host "
              "is at device" in f for f in found), found)
    check("gate: a machine element of an organism is refused alike",
          any('bearer' in f and 'bee-two' in f and 'at component, device, and a organism is at organism' in f
              for f in found), found)
    os.remove(os.path.join(G, 'beans', 'edge-router.md'))
    os.remove(os.path.join(G, 'beans', 'bee-two.md'))
    bean('bee-three', 'organism', 'a bee', 'read: { by: sam, at: now }', 'classify: { of: self, as: "col:FN47" }')
    found = gate()
    check("gate: a code the fetched copy does not hold is refused, looked up in its index",
          any('bee-three' in f and 'FN47' in f and 'no code of col' in f for f in found), found)
    os.remove(os.path.join(G, 'beans', 'bee-three.md'))

    # ---- THE FINDER
    K = dmk.Knowledge(G)
    check("propose: the schemes asked for a level are those whose `at` names it",
          K.at_level('organism') == ['col', 'cpv', 'ncbitaxon'] and 'machine-elements' in K.at_level('component')
          and 'col' not in K.at_level('device'), (K.at_level('organism'), K.at_level('component')))
    got = [p['coding'] for p in K.propose('Apis mellifera', 'organism')]
    check("propose: a taxon by its name, from the copy fetched here, and nothing of a scheme of made things",
          got == ['col:FN46'], got)
    got = [p['coding'] for p in K.propose('pulleys', 'component')]
    check("propose: a machine element by its name, its plural folded", got == ['machine-elements:pulley'], got)
    check("propose: nothing for the same word at a level its schemes do not classify",
          not K.propose('pulley', 'organism'))
    got = [(p['coding'], p['how']) for p in K.propose('rubber damper element', 'component')]
    check("propose: an element by its synonym", got == [('machine-elements:damper-ring', 'synonym')], got)
    check("find: the schemes of beings are passed over unless one is named",
          not [x for x in K.find('pulley') if x[1] == 'machine-elements']
          and [x for x in K.find('pulley', scheme='machine-elements')])

    SENT = []
    ENTITIES = {
        'Q99': {'claims': {'P31': [{'mainsnak': {'datavalue': {'value': {'id': 'Q5741069'}}}}]},
                'labels': {'en': {'value': 'Honey Bee'}}, 'descriptions': {'en': {'value': 'a band'}}},
        'Q30034': {'claims': {'P31': [{'mainsnak': {'datavalue': {'value': {'id': 'Q16521'}}}}],
                              'P10585': [{'mainsnak': {'datavalue': {'value': 'FN46'}}}],
                              'P685': [{'mainsnak': {'datavalue': {'value': '7460'}}}]},
                   'labels': {'en': {'value': 'Apis mellifera'}}, 'descriptions': {'en': {'value': 'species of insect'}}},
        'Q5741069': {'claims': {'P279': [{'mainsnak': {'datavalue': {'value': {'id': 'Q2088357'}}}}]}},
        'Q2088357': {'claims': {}}, 'Q16521': {'claims': {}},
    }

    def get(params):
        SENT.append(dict(params))
        if params['action'] == 'wbsearchentities':
            return {'search': [{'id': 'Q99'}, {'id': 'Q30034'}]}
        return {'entities': {i: ENTITIES.get(i, {'claims': {}}) for i in params['ids'].split('|')}}

    got = K.propose('honey bee', 'organism', get=get)
    codings = [p['coding'] for p in got]
    check("propose with Wikidata: the item picked by its class (a taxon), not the first by its label (a band), and "
          "through it the codes of the schemes it names, each checked in the copy held here",
          codings == ['wikidata:Q30034', 'col:FN46', 'ncbitaxon:7460']
          and [p['status'] for p in got][2] == 'not held here' and SENT[0]['search'] == 'honey bee', got)
    SENT.clear()
    check("propose with Wikidata: no item of the classes a level asks, none proposed",
          [p['coding'] for p in K.propose('honey bee', 'component', get=get)] == [])
    p = grow.run(PY, 'bin/knowledge.py', 'propose', '--level', 'organism', 'honey', 'bee', '--wikidata', 'wikimedia', cwd=G)
    check("propose at the command line: Wikidata refused, nothing sent, where no bean names the party; the held "
          "schemes' proposals shown", p.returncode == 1 and 'NotGranted' in p.out and 'no bean here names' in p.out
          and 'flow: sent-out' in p.out, p.out[-600:])
    bean('wikimedia', 'org', 'the Wikimedia Foundation, which keeps Wikidata', 'read: { by: sam, at: now }')
    p = grow.run(PY, 'bin/knowledge.py', 'propose', '--level', 'organism', 'honey', 'bee', '--wikidata', 'wikimedia', cwd=G)
    check("...and where a bean names it but the flow law grants it nothing", p.returncode == 1
          and 'does not grant it' in p.out, p.out[-600:])
    p = grow.run(PY, 'bin/knowledge.py', 'propose', 'hive-bee', cwd=G)
    check("propose a bean: its level read from its kind, its words from its title",
          p.returncode == 0 and 'col:FN46' in p.out and 'level organism' in p.out, p.out[-600:])
    p = grow.run(PY, 'bin/knowledge.py', 'propose', 'motor-offer', cwd=G)
    check("propose a bean of a sayable kind: refused, it is at no level", p.returncode == 1
          and 'at no level' in p.out, p.out[-400:])

    # ---- MACHINE-ELEMENTS.TSV
    with open(os.path.join(ROOT, 'seed', 'knowledge', 'machine-elements.tsv'), encoding='utf-8') as fh:
        me = list(csv.DictReader(fh, delimiter='\t'))
    codes = {r['code'] for r in me}
    import re
    check("machine-elements: its columns, each row a family or an element with its name and its meaning in daftar's words",
          list(me[0]) == ['code', 'level', 'parent', 'part_of', 'name', 'synonyms', 'meaning', 'wikidata', 'etim', 'cpv']
          and len(codes) == len(me) and all(r['level'] in ('family', 'element') and r['name'] and r['meaning'] for r in me))
    check("machine-elements: every parent and every whole a row of it, a family at the top",
          all((not r['parent']) == (r['level'] == 'family') and (not r['parent'] or r['parent'] in codes)
              and (not r['part_of'] or r['part_of'] in codes) for r in me))
    check("machine-elements: every item and code in its scheme's form — Wikidata's item, ETIM's class or group, CPV's code",
          all((not r['wikidata'] or re.fullmatch(schemes['wikidata']['code_pattern'], r['wikidata']))
              and (not r['etim'] or re.fullmatch(schemes['etim']['code_pattern'], r['etim']))
              and (not r['cpv'] or re.fullmatch(schemes['cpv']['code_pattern'], r['cpv'])) for r in me)
          and sum(1 for r in me if r['wikidata']) >= 30)
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\n{len(FAILS)} failed" if FAILS else "\n0 failed")
sys.exit(1 if FAILS else 0)
