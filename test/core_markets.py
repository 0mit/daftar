#!/usr/bin/env python3
"""core_markets — what a garden that follows markets, filings and published series needs (core 4.8): the namespaces of
legal entities, markets and registers in the core, the profile `markets`, the formats of feeds, filings and series with
their readers and crosswalks, and units made by a rule.

Grows two gardens of the core from a release made of this tree (test/grow.py), one taking the profile `markets` and one
not, and checks:

  names      an LEI, a MIC, a Central Index Key and the codes of three registers held to their forms, the LEI's check
             digits held (GLEIF's own LEI, as GLEIF publishes it, and an altered copy); in the profile, an ISIN (ISO
             6166's worked example), a FIGI (OpenFIGI's example of its check digit) and a symbol at a market by its MIC,
             each beside an altered copy refused
  profile    an instrument named by its ISIN, its FIGI and its symbol passes where the garden takes `markets`, and is
             refused, kind and names, where it does not
  units      a count of what an annotation names and a price over a unit, neither a row of the law, pass the gate; a
             price converts exactly where its unit under the line does, in its currency, and into another only at a rate
  formats    RSS, Atom, JSON Feed, an XBRL instance and an SDMX-ML generic data message, each read from a small invented
             file; a document that declares an entity, and a structure-specific message, refused with why; parquet's
             row reads nothing today
  imports    one item, in all three feeds, is one document produced by the site its link names, found at its link; a
             filing's facts are measures of the filer its Central Index Key names, in the law's units, over their
             periods, a fact of a segment and a fact of words listed; a series' observation is a measure of the series
             its key names, over the days of its month, one with no number listed; the gate passes what they write

Invented beings; nothing here is a fact. (`python` on Windows.)

Run: python3 test/core_markets.py   (0 = green)
"""
import os
import shutil
import sys
import tempfile
from fractions import Fraction

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path[:0] = [ROOT, os.path.join(ROOT, 'bin'), os.path.join(ROOT, 'test')]
import grow  # noqa: E402
import units as dmunits  # noqa: E402
from core import formats  # noqa: E402

PY = sys.executable
FAILS = []


def check(name, cond, detail=""):
    print(("PASS  " if cond else "FAIL  ") + name + ("" if cond else "  — " + str(detail)[-1500:]))
    if not cond:
        FAILS.append(name)


def write(g, rel, text):
    p = os.path.join(g, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as fh:
        fh.write(text)


def bean(name, kind, *statements, body='Invented.'):
    return (f'---\nbean: {name}\nkind: {kind}\ntitle: "{name}"\nstatements:\n  - say: {{ by: sam, at: now }}\n'
            + ''.join(f'  - {s}\n' for s in statements) + f'---\n{body}\n')


def gate(g):
    r = grow.run(PY, 'core/check.py', cwd=g)
    return r, [ln for ln in r.out.splitlines() if ln and not ln.startswith(('core check', 'check:'))]


RSS = '''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:dc="http://purl.org/dc/elements/1.1/">
  <channel>
    <title>The Valley Courier</title>
    <link>https://news.example.org/</link>
    <description>News of the valley</description>
    <item>
      <title>The mill reopens</title>
      <link>https://news.example.org/2026/10/mill</link>
      <guid isPermaLink="false">urn:example:valley:1</guid>
      <description>The old mill opens its doors again.</description>
      <pubDate>Tue, 27 Oct 2026 08:30:00 +0100</pubDate>
      <dc:creator>A. Writer</dc:creator>
      <category>town</category>
    </item>
    <item>
      <title>A bridge is closed</title>
      <link>https://news.example.org/2026/10/bridge</link>
      <pubDate>Wed, 28 Oct 2026 07:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
'''

ATOM = '''<?xml version="1.0" encoding="utf-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>The Valley Courier</title>
  <id>urn:example:valley</id>
  <updated>2026-10-28T07:00:00Z</updated>
  <entry>
    <title type="text">The mill reopens</title>
    <id>urn:example:valley:1</id>
    <link rel="alternate" href="https://news.example.org/2026/10/mill"/>
    <published>2026-10-27T08:30:00+01:00</published>
    <updated>2026-10-27T09:00:00+01:00</updated>
    <summary>The old mill opens its doors again.</summary>
    <author><name>A. Writer</name></author>
  </entry>
</feed>
'''

JSON_FEED = '''{"version": "https://jsonfeed.org/version/1.1", "title": "The Valley Courier", "home_page_url": "https://news.example.org/",
 "items": [{"id": "urn:example:valley:1", "url": "https://news.example.org/2026/10/mill", "title": "The mill reopens",
            "summary": "The old mill opens its doors again.", "date_published": "2026-10-27T08:30:00+01:00",
            "content_text": "The old mill, closed since spring, opens its doors again.", "tags": ["town"]}]}
'''

FILING = '''<?xml version="1.0" encoding="UTF-8"?>
<xbrli:xbrl xmlns:xbrli="http://www.xbrl.org/2003/instance" xmlns:iso4217="http://www.xbrl.org/2003/iso4217"
    xmlns:xbrldi="http://xbrl.org/2006/xbrldi" xmlns:ex="http://example.org/taxonomy/2026"
    xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xlink="http://www.w3.org/1999/xlink">
  <link:schemaRef xlink:type="simple" xlink:href="ex-2026.xsd"/>
  <xbrli:context id="FY2026">
    <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000042</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:startDate>2026-01-01</xbrli:startDate><xbrli:endDate>2026-09-30</xbrli:endDate></xbrli:period>
  </xbrli:context>
  <xbrli:context id="END">
    <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000042</xbrli:identifier></xbrli:entity>
    <xbrli:period><xbrli:instant>2026-09-30</xbrli:instant></xbrli:period>
  </xbrli:context>
  <xbrli:context id="FY2026-WEST">
    <xbrli:entity><xbrli:identifier scheme="http://www.sec.gov/CIK">0000000042</xbrli:identifier>
      <xbrli:segment><xbrldi:explicitMember dimension="ex:RegionAxis">ex:WestMember</xbrldi:explicitMember></xbrli:segment>
    </xbrli:entity>
    <xbrli:period><xbrli:startDate>2026-01-01</xbrli:startDate><xbrli:endDate>2026-09-30</xbrli:endDate></xbrli:period>
  </xbrli:context>
  <xbrli:unit id="USD"><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unit>
  <xbrli:unit id="shares"><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unit>
  <xbrli:unit id="USDPerShare"><xbrli:divide>
    <xbrli:unitNumerator><xbrli:measure>iso4217:USD</xbrli:measure></xbrli:unitNumerator>
    <xbrli:unitDenominator><xbrli:measure>xbrli:shares</xbrli:measure></xbrli:unitDenominator>
  </xbrli:divide></xbrli:unit>
  <ex:Revenue contextRef="FY2026" unitRef="USD" decimals="-3">125000000</ex:Revenue>
  <ex:SharesOutstanding contextRef="END" unitRef="shares" decimals="0">5000000</ex:SharesOutstanding>
  <ex:EarningsPerShare contextRef="FY2026" unitRef="USDPerShare" decimals="2">1.25</ex:EarningsPerShare>
  <ex:Revenue contextRef="FY2026-WEST" unitRef="USD" decimals="-3">40000000</ex:Revenue>
  <ex:DescriptionOfBusiness contextRef="FY2026">A mill and its bakeries.</ex:DescriptionOfBusiness>
</xbrli:xbrl>
'''

SERIES = '''<?xml version="1.0" encoding="UTF-8"?>
<message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
    xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"
    xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
  <message:Header>
    <message:ID>EX1</message:ID><message:Test>false</message:Test><message:Prepared>2026-10-28T00:00:00</message:Prepared>
    <message:Sender id="EX"/>
    <message:Structure structureID="EX_PRICES" dimensionAtObservation="TIME_PERIOD">
      <common:Structure><Ref agencyID="EX" id="DSD_PRICES" version="1.0"/></common:Structure>
    </message:Structure>
  </message:Header>
  <message:DataSet structureRef="EX_PRICES">
    <generic:Series>
      <generic:SeriesKey>
        <generic:Value id="FREQ" value="M"/><generic:Value id="AREA" value="VL"/><generic:Value id="ITEM" value="BREAD"/>
      </generic:SeriesKey>
      <generic:Attributes><generic:Value id="UNIT_MEASURE" value="EUR"/></generic:Attributes>
      <generic:Obs>
        <generic:ObsDimension value="2026-08"/><generic:ObsValue value="2.40"/>
        <generic:Attributes><generic:Value id="OBS_STATUS" value="A"/></generic:Attributes>
      </generic:Obs>
      <generic:Obs>
        <generic:ObsDimension value="2026-09"/><generic:ObsValue value="NaN"/>
        <generic:Attributes><generic:Value id="OBS_STATUS" value="M"/></generic:Attributes>
      </generic:Obs>
    </generic:Series>
  </message:DataSet>
</message:GenericData>
'''
VOCAB_ROWS = '''namespaces:
  - { namespace: stats-key, once: "true", pattern: '^[A-Z0-9_.]+$', meaning: "a series' key at the valley's statistics office" }
schemes:
  - { scheme: ex-2026, classifies: "the concepts of an invented taxonomy", publisher: "an invented regulator", url: "http://example.org/taxonomy/2026", holding: at-authority, code_pattern: '^[A-Za-z][A-Za-z0-9_]*$', levels: [{ level: concept }], neighbours: none, sources: "invented" }
  - { scheme: ex-prices, classifies: "the measures of an invented structure", publisher: "an invented statistics office", url: "EX:DSD_PRICES(1.0)", holding: at-authority, code_pattern: '^[A-Z_]+$', levels: [{ level: measure }], neighbours: none, sources: "invented" }
'''


T = tempfile.mkdtemp(prefix='core-markets-')
try:
    REL = grow.release(os.path.join(T, 'release'))
    G, P = os.path.join(T, 'markets'), os.path.join(T, 'plain')
    r = grow.garden(REL, G, 'sam', '--gardener-name', 'Sam', '--profile', 'markets')
    r2 = grow.garden(REL, P, 'sam', '--gardener-name', 'Sam')
    check("two gardens grow, one taking the profile `markets` and one not",
          r.returncode == 0 and r2.returncode == 0 and 'markets' in open(os.path.join(G, 'VOCAB.md')).read()
          and 'markets' not in open(os.path.join(P, 'VOCAB.md')).read(), r.out[-600:] + r2.out[-600:])

    # ---- names, and the profile
    SHARE = ('name: { by: isin, of: self, as: "US0378331005" }', 'name: { by: figi, of: self, as: "BBG000BLNQ16" }',
             'name: { by: ticker, of: self, as: "ABCD:MILL" }')
    for g in (G, P):
        write(g, 'beans/mill-share.md', bean('mill-share', 'instrument', *SHARE))
        write(g, 'beans/mill-co.md', bean('mill-co', 'org', 'name: { by: sec-cik, of: self, as: "0000000042" }',
                                          'name: { by: edinet, of: self, as: "E00042" }',
                                          'name: { by: dart, of: self, as: "00000042" }',
                                          'name: { by: twse, of: self, as: "4242" }'))
        write(g, 'beans/gleif.md', bean('gleif', 'org', 'name: { by: lei, of: self, as: "506700GE1G29325QX363" }'))
        write(g, 'beans/abcd-market.md', bean('abcd-market', 'org', 'name: { by: mic, of: self, as: "ABCD" }'))
    r, found = gate(G)
    check("names: an LEI (GLEIF's own), a MIC, a Central Index Key, an EDINET, a DART and a TWSE code, and an instrument "
          "by its ISIN (ISO 6166's worked example), its FIGI (OpenFIGI's example) and its symbol at a market, where the "
          "garden takes `markets`", r.returncode == 0 and not found, r.out[-1500:])
    r, found = gate(P)
    check("profile: where the garden does not take `markets`, an instrument is refused, and so is each of its names in "
          "the profile's namespaces; the core's names pass",
          r.returncode != 0 and len(found) == 4 and all('profile' in ln and "markets profile's" in ln for ln in found)
          and any('kind' in ln and '`instrument`' in ln for ln in found)
          and all(any(f'`{ns}`' in ln for ln in found) for ns in ('isin', 'figi', 'ticker')), found)
    os.remove(os.path.join(P, 'beans', 'mill-share.md'))
    broken = {'lei': ('gleif', 'org', 'lei', '506700GE1G29325QX364', 'lei-checksum'),
              'isin': ('mill-share', 'instrument', 'isin', 'US0378331006', 'isin-checksum'),
              'figi': ('mill-share', 'instrument', 'figi', 'BBG000BLNQ17', 'figi-checksum'),
              'ticker': ('mill-share', 'instrument', 'ticker', 'ABCD-MILL', 'its form'),
              'mic': ('abcd-market', 'org', 'mic', 'abcd', 'its form'),
              'sec-cik': ('mill-co', 'org', 'sec-cik', '42', 'its form'),
              'edinet': ('mill-co', 'org', 'edinet', 'E0042', 'its form')}
    for what, (b, kind, ns, value, why) in broken.items():
        keep = open(os.path.join(G, 'beans', f'{b}.md'), encoding='utf-8').read()
        write(G, f'beans/{b}.md', bean(b, kind, f'name: {{ by: {ns}, of: self, as: "{value}" }}'))
        r, found = gate(G)
        check(f"names: an altered {what} ({value}) is refused by rule names, naming {why}",
              r.returncode != 0 and len(found) == 1 and found[0].startswith('names') and f'not a name {ns} gives' in found[0]
              and why in found[0], found)
        write(G, f'beans/{b}.md', keep)

    # ---- units made by a rule
    write(G, 'beans/crate-prices.md', bean('crate-prices', 'document',
          'measure: { id: crates, of: self, as: number, value: { count: "300", unit: "{crate}" }, at: "2026-10-01" }',
          'measure: { id: per-crate, of: self, as: money, value: { count: "1200", unit: "USD/{crate}" }, at: "2026-10-01" }',
          'measure: { id: per-kg, of: self, as: money, value: { count: "3.20", unit: "EUR/kg" }, at: "2026-10-01" }'))
    r, found = gate(G)
    check("units: a count of crates, a price per crate and a price per kilogram pass the gate, though none is a row",
          r.returncode == 0 and not found, r.out[-1200:])
    write(G, 'beans/crate-prices.md', bean('crate-prices', 'document',
          'measure: { id: rate, of: self, as: money, value: { count: "1.1", unit: "USD/EUR" }, at: "2026-10-01" }'))
    r, found = gate(G)
    check("...and a currency over a currency is no price: refused, its message saying what a rule makes",
          r.returncode != 0 and len(found) == 1 and "nor one its rules make" in found[0], found)
    os.remove(os.path.join(G, 'beans', 'crate-prices.md'))

    def conv(*a):
        try:
            return dmunits.convert(*a)
        except ValueError as e:
            return str(e)
    check("units: a price converts exactly where its unit under the line does — 3.20 EUR/kg is 0.0032 EUR/g, 100 IRT/kg "
          "1000 IRR/kg — and into itself",
          conv('3.20', 'EUR/kg', 'EUR/g') == Fraction(32, 10000) and conv('100', 'IRT/kg', 'IRR/kg') == 1000
          and conv('1200', 'USD/{crate}', 'USD/{crate}') == 1200,
          (conv('3.20', 'EUR/kg', 'EUR/g'), conv('100', 'IRT/kg', 'IRR/kg'), conv('1200', 'USD/{crate}', 'USD/{crate}')))
    check("...into another currency only at a rate someone observed (3.20 EUR/kg at 1.1 is 3.52 USD/kg), never between "
          "units of two quantities, and never between counts of two things",
          conv('3.20', 'EUR/kg', 'USD/kg', '1.1') == Fraction(352, 100) and 'rate' in str(conv('3.20', 'EUR/kg', 'USD/kg'))
          and 'nothing converts' in str(conv('1', 'USD/{crate}', 'USD/kg'))
          and 'no factor' in str(conv('2', '{crate}', '{seat}')),
          (conv('3.20', 'EUR/kg', 'USD/kg', '1.1'), conv('3.20', 'EUR/kg', 'USD/kg'), conv('1', 'USD/{crate}', 'USD/kg'),
           conv('2', '{crate}', '{seat}')))

    # ---- the five formats, each read from a small invented file
    def read(fmt, text):
        try:
            return list(formats.read(fmt, text.encode('utf-8')))
        except formats.Refused as e:
            return str(e)
    rss, atom, jf = read('rss', RSS), read('atom', ATOM), read('json-feed', JSON_FEED)
    check("formats: RSS gives each item of its channel, Atom each entry of its feed, JSON Feed each of its items",
          isinstance(rss, list) and [x.get('title') for x in rss] == ['The mill reopens', 'A bridge is closed']
          and isinstance(atom, list) and len(atom) == 1 and atom[0].get('id') == 'urn:example:valley:1'
          and isinstance(jf, list) and len(jf) == 1 and jf[0].get('url') == 'https://news.example.org/2026/10/mill',
          (rss, atom, jf))
    facts, obs = read('xbrl', FILING), read('sdmx', SERIES)
    check("formats: an XBRL instance gives each fact with its context's entity and period and its unit; an SDMX-ML "
          "generic message each observation with its series' key and attributes and the structure it names",
          isinstance(facts, list) and len(facts) == 5 and facts[0]['context']['entity']['identifier'] == '0000000042'
          and facts[2]['unit'] == {'numerator': ['iso4217:USD'], 'denominator': ['xbrli:shares']}
          and isinstance(obs, list) and len(obs) == 2 and obs[0]['key'] == {'FREQ': 'M', 'AREA': 'VL', 'ITEM': 'BREAD'}
          and obs[0]['structure'] == 'EX:DSD_PRICES(1.0)' and obs[0]['obs']['OBS_VALUE'] == '2.40', (facts, obs))
    from core import readers
    placed = {p: readers.sdmx_period(p) for p in ('2026', '2026-A1', '2026-S2', '2026-Q1', '2026-02', '2026-M02', '2028-02',
                                                  '2026-W05', '2026-08-15', '2026-13', '2026-Q5', '2026-S3', '2026-D032')}
    check("formats: SDMX's periods placed as the law writes a position — a year, a half, a quarter, a month (ISO 8601's "
          "or SDMX's) the days from its first to its last, a week its days in the ISO week calendar, a day as written; "
          "a period of no such form, none",
          placed == {'2026': '2026-01-01/2026-12-31', '2026-A1': '2026-01-01/2026-12-31', '2026-S2': '2026-07-01/2026-12-31',
                     '2026-Q1': '2026-01-01/2026-03-31', '2026-02': '2026-02-01/2026-02-28',
                     '2026-M02': '2026-02-01/2026-02-28', '2028-02': '2028-02-01/2028-02-29',
                     '2026-W05': '2026-W05-1/2026-W05-7', '2026-08-15': '2026-08-15', '2026-13': None, '2026-Q5': None,
                     '2026-S3': None, '2026-D032': None}, placed)
    ent = read('rss', RSS.replace('<rss version', '<!DOCTYPE rss [<!ENTITY e "x">]>\n<rss version'))
    ss = read('sdmx', SERIES.replace('GenericData', 'StructureSpecificData'))
    check("formats: a feed that declares an entity is refused before it is parsed; a structure-specific SDMX message is "
          "refused, saying why and what to read instead; another document is not read as a feed",
          isinstance(ent, str) and 'entity' in ent and isinstance(ss, str) and 'generic data' in ss
          and isinstance(read('atom', RSS), str) and isinstance(read('json-feed', '{"items": []}'), str), (ent, ss))
    import yaml
    with open(os.path.join(ROOT, 'core', 'law', 'formats.yaml'), encoding='utf-8') as fh:
        rows = {r['format']: r for r in yaml.safe_load(fh)['formats']}
    check("formats: parquet's row reads nothing today, and no reader of it is in the release",
          rows['parquet']['reads'] == 'false' and rows['parquet']['writes'] == 'false' and 'parquet' not in formats.READ,
          rows['parquet'])

    # ---- the imports, written into beans, and the gate
    vocab = open(os.path.join(G, 'VOCAB.md'), encoding='utf-8').read()
    write(G, 'VOCAB.md', vocab.replace('namespaces: []\n', VOCAB_ROWS, 1))
    write(G, 'beans/newsroom.md', bean('newsroom', 'org', 'name: { by: dns, of: self, as: news.example.org }'))
    write(G, 'beans/bread-index.md', bean('bread-index', 'series', 'name: { by: stats-key, of: self, as: "M.VL.BREAD" }'))
    src = {}
    for name, text in (('feed.rss', RSS), ('feed.atom', ATOM), ('feed.json', JSON_FEED), ('filing.xbrl', FILING),
                       ('series.xml', SERIES)):
        src[name] = os.path.join(T, name)
        with open(src[name], 'w', encoding='utf-8') as fh:
            fh.write(text)
    out = {}
    for cw, name, extra in (('feed-item', 'feed.rss', []), ('feed-item', 'feed.atom', []),
                            ('feed-item', 'feed.json', ['--format', 'json-feed']),
                            ('xbrl-fact', 'filing.xbrl', ['--named', 'sec-cik']),
                            ('sdmx-observation', 'series.xml', ['--named', 'stats-key'])):
        out[name] = grow.run(PY, 'bin/daftar.py', 'import', cw, src[name], '--into', 'bean', '--write', *extra, cwd=G)
    item = open(os.path.join(G, 'beans', 'i-1711cd63eb9e9c05.md'), encoding='utf-8').read() \
        if os.path.isfile(os.path.join(G, 'beans', 'i-1711cd63eb9e9c05.md')) else ''
    said = [ln.strip() for ln in item.splitlines() if ln.strip().startswith(('- be:', '- produce:'))]
    check("imports: one item, in RSS, Atom and JSON Feed, is one document — its id minted from its own id, its title "
          "its own, produced by the site its link names at the moment it was published, found at its link — each reading "
          "saying the same two statements (a bean written three times holds them three times; a store, once)",
          all(out[n].returncode == 0 for n in ('feed.rss', 'feed.atom', 'feed.json'))
          and 'title: "The mill reopens"' in item and len(said) == 6 and len(set(said)) == 2
          and 'produce: { by: newsroom, of: self, at: "2026-10-27T08:30:00+01:00" }' in item
          and 'at: "https://news.example.org/2026/10/mill", as: location' in item,
          item + ''.join(out[n].out[-500:] for n in ('feed.rss', 'feed.atom', 'feed.json')))
    second = [f for f in os.listdir(os.path.join(G, 'beans')) if f.startswith('i-') and f != 'i-1711cd63eb9e9c05.md']
    check("...an item with no id of its own is named by its link, and its author, its text and its categories are not "
          "carried, each dropped for its reason", len(second) == 1 and 'A. Writer' not in item and 'town' not in item,
          (second, item))
    mill = open(os.path.join(G, 'beans', 'mill-co.md'), encoding='utf-8').read()
    check("imports: a filing's facts are measures of the filer its Central Index Key names — its revenue in USD over the "
          "days of its period, its shares a count of `{share}` at its instant, its earnings a price per share — and its "
          "fact of a segment and its fact of words are listed, not carried",
          out['filing.xbrl'].returncode == 0
          and 'as: "ex-2026:Revenue", at: 2026-01-01/2026-09-30, value: { count: "125000000", unit: USD }' in mill
          and 'at: "2026-09-30", value: { count: "5000000", unit: "{share}" }' in mill
          and 'value: { count: "1.25", unit: "USD/{share}" }' in mill and '40000000' not in mill
          and out['filing.xbrl'].stderr.count('it names no being') == 2, mill + out['filing.xbrl'].out[-800:])
    series = open(os.path.join(G, 'beans', 'bread-index.md'), encoding='utf-8').read()
    check("imports: a series' observation is a measure of the series its key names, over the days of its month, in its "
          "unit; one with no number is listed, and so is its status",
          out['series.xml'].returncode == 0
          and 'as: "ex-prices:OBS_VALUE", at: 2026-08-01/2026-08-31, value: { count: "2.40", unit: EUR }' in series
          and series.count('measure:') == 1 and 'it names no being' in out['series.xml'].stderr
          and 'OBS_STATUS' in out['series.xml'].stderr, series + out['series.xml'].out[-800:])
    r, found = gate(G)
    check("imports: the gate passes every statement they wrote", r.returncode == 0 and not found, r.out[-2000:])
finally:
    shutil.rmtree(T, ignore_errors=True)

print(f"\ncore_markets: {len(FAILS)} failed")
sys.exit(1 if FAILS else 0)
