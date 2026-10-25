# seed/knowledge — sources, licences and attribution

The files in this directory are **data**, each under its own terms, distributed alongside daftar's
AGPL-3.0-or-later code and CC BY 4.0 law as separate works (aggregation). The gate reads them through `registry_files` in
`seed/std-vocab.md`. Nothing here was invented to look complete: every row is copied from its source
or derived from recorded evidence, and each file says which.

## isced-f-2013.tsv — ISCED Fields of Education and Training 2013

- **Source:** UNESCO Institute for Statistics, *ISCED Fields of Education and Training 2013 (ISCED-F 2013)*
  and *Detailed Field Descriptions* (2015), doi:10.15220/978-92-9189-179-5-en.
- **Licence:** CC BY-SA 3.0 IGO. This file holds the codes and English titles as published, unchanged, and is
  distributed under the same licence. The share-alike obligation applies to this file, not to daftar's code.
- **Attribution:** "Source: UNESCO Institute for Statistics, ISCED-F 2013."

## isco-08.tsv — International Standard Classification of Occupations 2008

- **Source:** International Labour Organization, ISCO-08 structure (all four levels: codes and English titles).
- **Copyright:** © International Labour Organization, 2012. The ILO's pre-2023 works carry no open licence.
  The structure (all 619 codes and English titles) is reproduced here with the source indicated. The ILO has
  been asked (rights@ilo.org, September 2026) to confirm that it may be redistributed as data.
- **Fetched, from the release after this one's adoption:** the law holds ISCO-08 `fetched` (core/law/registries.yaml):
  each machine downloads the ILO's own structure file (`ISCO-08 EN Structure and definitions.xlsx`) with
  `python3 bin/fetch.py isco-08`, keeps it unchanged outside git, and reads its codes there; this copy stays in the
  release only until gardens hold their own. Measured 2026-10-09: the ILO's file and this copy hold the same 619 codes,
  levels and parents; 28 titles differ in wording ("Services Managers", "Service Managers"), the ILO's file being the
  later.
- **Not included:** the ILO's definitions and task descriptions (not redistributable without permission).
  Standardized job descriptions come from ESCO instead (see below), which maps every occupation to exactly one
  ISCO-08 unit group.
- **Other languages are not shipped here.** A garden that needs titles in another language keeps them in its
  own overlay with a `name_<lang>` column (`bin/knowledge.py` reads `label(scheme, code, lang)`), under
  whatever terms apply to that translation. For ISCO-08, a translation needs the ILO's permission
  (rights@ilo.org).

## technology.tsv — established technologies and their official documentation

- **Curated by daftar.** Every `docs` URL is the project's OWN documentation (checked 2026-09-19; the thirteen rows of the
  view's stack — django to opentelemetry — checked 2026-09-30, each answering), never a
  third party's. `isced_f_2013` and `isco_08` name the fields a technology draws on and the occupations that
  run it — a judgement, open to correction by pull request like any row. CC BY 4.0, with daftar's law.

## signals.tsv — what a running technology reports about itself

- **The names read at the OpenTelemetry semantic conventions** (opentelemetry.io/docs/specs/semconv, HTTP and system
  metrics, read 2026-09-30): each signal's name, instrument, unit and stability as published there. The meanings are
  daftar's own words; no file of the conventions is copied. CC BY 4.0, with daftar's law.

## technology-daftar.tsv — what daftar does with a technology

- **daftar's own.** A row says a technology is `spoken` only where its adapter is a file of the release and the suite it
  names passes; `planned` otherwise, a position held for it. CC BY 4.0, with daftar's law.

## name-patterns.tsv — the names a published convention gives files and folders

- **Curated by daftar**, each row a convention its publisher documents: DCF, the Design rule for Camera File system
  (JEITA CP-3461, CIPA DC-009), which names a camera's files with four free characters and a number from 0001 to
  9999, and its folders with a number from 100 to 999 and five free characters. The templates are daftar's writing of
  the rule in the slots of core/law/lines.yaml; no text of the standard is copied. A maker's own prefix, and a
  garden's own patterns, are each garden's extract, not the release's. CC BY 4.0, with daftar's law.

## media-types — the media types and their families, from shared-mime-info (fetched)

- **Not shipped.** Each machine fetches freedesktop.org's shared-mime-info with `python3 bin/fetch.py media-types`
  (`https://gitlab.freedesktop.org/xdg/shared-mime-info/-/archive/2.4/shared-mime-info-2.4.tar.gz`, 7,852,841 bytes,
  sha-256 531291d0387eb94e16e775d7e73788d06d2b2fdd8cd2ac6b6b15287593b6a2de, read 2026-10-19), and the reader
  `shared-mime-info` reads its `data/freedesktop.org.xml.in`: 908 media types, each with its English comment, its
  generic icon (one of the nineteen its document type names: image-x-generic, x-office-document, package-x-generic,
  application-x-executable, text-x-script …), its globs and what it is a subclass of. A host that installs the database
  keeps the same file in /usr/share/mime/packages/freedesktop.org.xml, and the reader reads it there where no fetch was
  made. Its top-level types are RFC 6838's.
- **Its licence** is the GNU General Public License, version 2 or later (the licence core/law/registries.yaml names): the
  release carries none of it, and what a garden reads of it stays on the machine that fetched it.

## crosswalk-isco-08-isced-f-2013.tsv — which fields an occupation draws on

- **Derived, not official** (no official ISCO-08 ↔ ISCED-F 2013 crosswalk exists). Each row counts, for one
  ISCO-08 unit group, how many role→skill requirements of a hand-classified skills standard reach one ISCED-F
  field (split by importance: core, common, specialist), how many roles contribute, and the most frequent
  concrete topics. Coverage is that standard's domains only (96 unit groups) and grows as other gardens
  classify roles. CC BY 4.0, with daftar's law.

## currencies.tsv — the currencies, their numbers and the decimal places in use

- **Source:** Unicode CLDR 48.2.2, fetched from `unicode-org/cldr-json`: `cldr-core/supplemental/currencyData.json`
  (the decimal places in ordinary use, `fractions`, and which currencies are tender where, `region`),
  `cldr-core/supplemental/codeMappings.json` (the ISO 4217 numeric codes) and
  `cldr-numbers-full/main/en/currencies.json` (the English names). One row per three-letter code CLDR names.
- **Derived columns:** `numeric` zero-padded to three digits as ISO 4217 writes it; `status` is `current` when some
  territory lists the currency as tender with no end date, `special` for an X-code that is not (gold, the testing
  code XTS, "unknown" XXX), and `historic` otherwise. `digits` is CLDR's, which follows use: it may differ from the
  minor unit ISO 4217 lists (the Iranian rial is written with none).
- **Licence:** Unicode License v3 (permissive; its notice travels with the file's copies). ISO 4217's own list was
  not used: its terms of redistribution are not stated where it is published.
- **Refreshed** at a release by fetching the same three files again; a redenomination arrives as a new code, and the
  old one stays, `historic`, so an old amount can still be said.

## Job descriptions — ESCO (to be added)

ESCO (European Skills, Competences, Qualifications and Occupations), © European Union, reusable under
Commission Decision 2011/833/EU. Attribution: "This service uses the ESCO classification of the European
Commission." Modified or adapted versions must be marked as such.

## time-zones.tsv — the civil time zones (N8)

- **Source:** the IANA time zone database (tzdb), release 2026d, its `zone1970.tab`: one row for each zone whose civil
  clocks have agreed since 1970, with the countries it overlaps (ISO 3166 codes, the most populous first), its principal
  location (ISO 6709, `±DDMM±DDDMM` or `±DDMMSS±DDDMMSS`) and its comment where a country has several zones. One row
  is added from the same database's `etcetera` file: `Etc/UTC`, so that a reading can be asked in UTC itself.
- **Derived:** the rows sorted by zone; the columns renamed `zone`, `countries`, `coordinates`, `comment`.
- **Licence:** public domain, as the database itself states.
- **What the file is NOT:** the offsets. A zone's offset at a moment is READ, through Python's `zoneinfo` and the
  platform's copy of the same database (`bin/cal.py offset`), and never stored: an offset changes when a government
  changes it, and a stored one would be wrong from that day on without anyone having written anything.
- **Refreshed** at a release from the tzdb release then current; a zone the database retires stays a row until no
  garden names it, and a link (`backward`) is never a row: a zone is named by its canonical name.

## ics-chart-2026-06.tsv — the units of the International Chronostratigraphic Chart (step 8)

- **Source:** the International Commission on Stratigraphy's SKOS vocabulary of the chart, `chart.ttl` in
  github.com/i-c-stratigraphy/chart, `owl:versionInfo` 2026-06 (modified 2026-06-20): 178 units.
- **Derived:** one row per `skos:Concept` — `unit` its local name as the chart names it (`Meghalayan`,
  `CambrianStage2`), `parent` its `skos:broader`, `rank` its `gts:rank` in lower case (`super-eon`, `eon`, `era`,
  `period`, `sub-period`, `epoch`, `age`), `begins_ma`/`ends_ma` the `gtsd:inMYA` of `time:hasBeginning`/`hasEnd`
  as written, their `schema:marginOfError` where stated, and `name_en` its English `skos:prefLabel`. Sorted oldest
  first. Pridoli is ranked both Age and Epoch by the chart and is held at its higher rank, `epoch`. The chart states no
  English label for 21 units (the Lower, Middle and Upper series of several periods, and the Upper Pleistocene): their
  `name_en` is empty, as published, and none is invented.
- **Licence:** CC BY 4.0, © International Commission on Stratigraphy (NOTICE).
- **What the file is NOT:** a boundary's definition. A unit's base is fixed by its GSSP (the next file); the ages here are
  readings of those points, and the margins are kept as the chart states them, with no probability read into them.

## ics-gssps-2026-09.tsv — what fixes each unit's base: the golden spikes (step 8)

- **Source:** the ICS table of Global Boundary Stratotype Sections and Points, `data/source/gssps.ttl` in
  github.com/i-c-stratigraphy/gssps at commit 54344ff (2026-09-18): 117 boundaries.
- **Derived:** one row per `gssp:GSSP` or `gssp:GSSA` — `boundary` the unit whose base it is (the record's own name, which
  is the chart's unit; where the record names another unit sharing that base, the stage is kept), `fixing` `marked` for a
  GSSP and `declared` for a GSSA (the aspect `fixing`), `at` its `geo:asWKT` point as `EPSG:4326;<lat>,<lon>` (GeoJSON and
  WKT give longitude first; the law's form is latitude first), `level` its `gssp:boundaryLevel`, `location` its
  `schema:location`, `status` `ratified` or `proposed` read from `schema:status`, `status_as_published` that text itself,
  and `cite` its citation. 104 are marked and 13 declared; 88 are ratified and 27 proposed. A proposed boundary has no
  point yet; one declared boundary (the Eoarchean) names a place as its reference, which does not fix it.
- **Licence:** CC BY 4.0, © International Commission on Stratigraphy (NOTICE).
- **Refreshed** at a release with the chart; a boundary ratified since moves from `proposed` with its point.

## substances.tsv — substances by their chemical formula (D38)

- **Source:** the formula of each substance, a fact of chemistry and no one's expression: `carbon-dioxide` CO2,
  `dioxygen` O2, `water` H2O, `glucose` C6H12O6, and `pentacosane` C25H52 (a paraffin wax, the release's invented
  candle's). `charge` is the net charge of one unit, 0 for these.
- **Licence:** facts; the file is CC0 1.0.
- **What the file is for:** `conservation` (bin/reckon.py) reads a walk's `takes` and `gives` against these formulas
  and says whether every element and the charge is conserved. A substance with no one formula (a polymer, a mixture)
  is not a row, and a walk that names one is not read for conservation.

## mechanisms.yaml, coefficients.yaml — models and constants with their sources (step 9)

- **Empty at this release** (`[]`): a row is added only with terms that allow it to be shipped, its `source` cited and
  its `terms` stated (`mechanism_form`, `coefficient_form`). A garden adds its own through `registry_additions`.
- **Licence:** the files are CC0 1.0; a row shipped later under other terms goes in a file of its own, one per licence.

## units-<scheme>.tsv — a standard's codes of units, crossed into the law's units and kinds

- **daftar's own.** Each row names one code of a standard's own list and the law's row it crosses to — a unit in UCUM,
  a kind, a line, a system's positions or its cells, a shape — or, crossing to nothing, why (`units_crosswalk_form`,
  core/law/registries.yaml). The pairings and the reasons are daftar's; the codes cited remain their publishers', and no
  name, description or definition of theirs is copied. CC BY 4.0, with daftar's law. `bin/units.py` reads them; the
  standard's own table is held where its scheme's `holding` says.

## unece-rec20 — UN/CEFACT Recommendation No. 20, codes for units of measure used in international trade (fetched)

- **Not shipped.** Each machine fetches UN/CEFACT's own spreadsheet (Revision 17, `rec20_Rev17e-2021.xlsx`) with
  `python3 bin/fetch.py unece-rec20`, keeps it unchanged outside git and reads its codes there: code, status, English
  name, symbol. unece.org may answer a script with a challenge meant for a browser; a person then downloads the file
  there and reads it with `--from`. The reader was built on 2026-10-11 against a copy of that file taken from a public
  mirror, unece.org refusing the machine it ran on (305,526 bytes, sha-256
  994a85c3682e67604d42dbda3b35d672338a45b400f5397a96a4c5467ee8056d): 2,136 codes, 309 marked deleted and 71 deprecated.
- **Its terms are an open question:** as read on 2026-10-08, UNECE's site footer says CC BY 4.0 and its terms-of-use
  page says otherwise, and UNECE has not been asked which governs its code lists (`LicenseRef-UNECE-terms` until it
  answers). Holding it fetched makes each copy its fetcher's own use under UNECE's terms, whichever they are.
- **units-unece-rec20.tsv** crosses 179 of its codes into the law: each code whose unit the law writes, the counts of
  things (C62, H87, EA, NAR, SET, PR), the calendar's cells an invoice counts (DAY, WEE, MON, ANN — never Rec 20's own
  durations of them) and the three temperature scales' readings; and says why seven codes cross to nothing (J2, 4P,
  GL, DZN, QAN, E14, ZZ). A code it does not name is one whose unit the law does not write.

## loinc — LOINC, observations of a lab and a clinic (fetched)

- **Not shipped.** A person signed in at loinc.org with a free account, who accepts its licence, downloads LOINC's
  release; `python3 bin/fetch.py loinc --from <the zip or its LoincTable/Loinc.csv>` keeps it unchanged outside git and
  reads each term's code, status, property, scale and long common name. loinc.org answered this build machine with a
  browser challenge on 2026-10-11, so the reader was built on LOINC's published table format (the samples HL7's and
  HAPI FHIR's terminology tests carry, LOINC 2.6x to 2.7x columns) and the crossing on the property and scale tables
  of LOINC 2.81's Users' Guide (§2.3, Table 8; §2.6, Table 12), read through the Internet Archive.
- **units-loinc.tsv** crosses LOINC's two axes, not its terms: each property the guide lists (212, with `-` for a
  panel and `Pr`, which older tables carry) to a kind, a line or nothing with its reason, and each scale (10) to a
  shape, a line or nothing. 121 properties cross; 31 name a kind the law holds not yet and are vacant, `universal` (a
  catalytic or a number concentration, a molality, a viscosity…); 60 are no measure, or no one kind (a finding, an
  identity, an address, a logarithm, a score). A
  term's kind is read through its property, and how its value is written through its scale; a temperature read as a
  number is a position on its scale.
- **Its licence** lets LOINC's parts be used "to organize, categorize, and be constituents of LOINC terms, and provide
  links to external terminologies", with its notice (NOTICE); the crossing is that use: it links LOINC's property and
  scale abbreviations, as its table writes them, to the law's kinds, in daftar's own words.

## ifc-4x3 — IFC 4.3, what a building model measures and in what units (fetched)

- **Not shipped.** Each machine fetches buildingSMART's schema in EXPRESS (`IFC4X3_ADD2.exp`, IFC 4.3.2.0) with
  `python3 bin/fetch.py ifc-4x3`, and reads its measure types and its SI units — each name of `IfcSIUnitName`, alone
  and after each prefix of `IfcSIPrefix` (`MILLI.METRE`). standards.buildingsmart.org answered this build machine with a
  browser challenge on 2026-10-11, so the reader was built against buildingSMART's own IFC 4.3 RC4 schema from its
  development repository (`reference_schemas/IFC4x3_RC4.exp`): the same EXPRESS, 92 measure types.
- **units-ifc-4x3.tsv** crosses the 92 measure types and 72 SI units the law writes: 63 measure types to a kind (a
  temperature to its line, a descriptive measure to text), 26 to nothing, vacant `universal` — the structural and
  hygrothermal kinds the law has not yet (a modulus of elasticity, a section modulus, a warping constant, a section's
  second moment of area, a viscosity…) — and three to nothing with their reasons. A model's conversion-based unit
  (a foot, a pound) is read by the exact factor it states (`bin/units.py --unit-of`), not by name: its name is the
  model's, and IFC fixes none.
- **Its licence** is CC BY-ND 4.0 (© buildingSMART International): the schema is fetched, never redistributed, and the
  crossing cites its type and unit names and links each to the law's rows, changing nothing of the schema.

## epsg-uom — EPSG's units of measure (ISO 19111), fetched

- **Not shipped.** A person signed in at epsg.org downloads the EPSG Dataset as its SQL scripts (a zip);
  `python3 bin/fetch.py epsg-uom --from <the zip or its …Data_Script.sql>` keeps it unchanged outside git and reads each
  row of `epsg_unitofmeasure`: code, name, type, target unit, factor_b, factor_c and whether it is deprecated. The
  reader was built on 2026-10-11 against an unchanged public copy of the PostgreSQL data script of the EPSG Dataset
  13.103 (its 95 units), the download itself asking for an account.
- **units-epsg-uom.tsv** names all 95: 22 cross — the metric lengths, the international foot, yard and mile, the US
  survey foot (`[ft_us]`, added to the law with it), the radian, degree, arc-minute, arc-second and grad, unity and
  the parts per million and billion, the second, and EPSG's year, which is the annus the law holds (31 556 925.445 s)
  — and 73 cross to nothing with their reasons: the surveys' own historical feet, yards, chains and links, the
  notations of a degree in minutes and seconds or with its hemisphere, the rates per year, a seismic grid's bin widths.
  Every crossed unit is the size EPSG states (its factor_b / factor_c of its target; π, written to fourteen decimals,
  as π): test/core_standards.py holds the crossing to it.
- **Its terms** are the EPSG Dataset's terms of use (epsg.org/terms-of-use.html): the dataset is fetched by each
  machine, never redistributed; the crossing cites EPSG's codes.

## gs1-ai — GS1's application identifiers (fetched)

- **Not shipped.** Each machine fetches GS1's Barcode Syntax Dictionary (`gs1-syntax-dictionary.txt`, maintained by GS1
  AISBL at github.com/gs1/gs1-syntax-dictionary, under the licence its scheme's row names) with
  `python3 bin/fetch.py gs1-ai`, and reads each
  application identifier — each of a range — with its specification and its title. The reader was built on
  2026-10-11 against its release 2026-01-27 (541 identifiers).
- **units-gs1-ai.tsv** crosses its measures by family, as GS1 writes them: `310n` a net weight in kg, the AI's last
  digit `n` the decimal point's place (`decimals: n`), so (3103)001250 is 1.250 kg and the law's 1.250 kg is written
  back as it. 55 of 61 families cross: the metric and the imperial weights, lengths, areas and volumes, net and of a
  logistic unit, a grammage, a count, a percentage off; the law gains the square and cubic inch, foot and yard, the US
  gallon and quart, and the troy ounce for them. Six cross to nothing with their reasons: an ounce that GS1 lets be a
  weight or a volume (357n), and the amounts and prices, whose currency the AI leaves local or each value names.
  Where several families cross to one unit (a net and a gross weight, a length, a width and a height), the law's value
  is written back as the first of them, a net weight or a length: the law's quantity says how much, never which
  dimension of a parcel it was.
- **Its licence** would let it ship; daftar ships no one's table, so it is fetched like the others.

## cldr-units.tsv, units-cldr-units.tsv — the units' names in English, Persian and Turkish (CLDR)

- **cldr-units.tsv** is read by `bin/fetch.py`'s `cldr-units-json` from Unicode's own package of CLDR's unit names,
  `cldr-units-full` 48.2.0 (registry.npmjs.org, sha-256
  754d55f183570c53029a77493302f432fb3e905df35a715f9cb022e2ebcb093c): for each of CLDR's 232 units its code and its long
  display name in English, Persian and Turkish, as CLDR writes them, and nothing else. Unicode License v3: the release
  carries it, and each machine may fetch a later one (`python3 bin/fetch.py cldr-units`).
- **units-cldr-units.tsv** crosses 111 of CLDR's unit ids into the law — each whose unit the law writes, a month, a week
  and a year to a calendar's cells, the three temperatures to their scales — and says why seven cross to nothing (a
  quarter, a century, a night's stay, a degree of no stated scale…). So a widget names the law's `m` as CLDR names
  `length-meter`: metre, متر, metre (`python3 bin/units.py --name m fa cldr-units`). The pairings and reasons are
  daftar's own, CC BY 4.0.

## geonames — the GeoNames gazetteer, a country at a time (fetched)

- **Not shipped.** Each machine fetches the countries its garden needs from GeoNames' daily export with
  `python3 bin/fetch.py geonames <CC>` (`https://download.geonames.org/export/dump/<CC>.zip`), and reads each feature
  of the country's table in the nineteen columns its readme.txt names: its geonameid, name and ASCII name, its alternate
  names as GeoNames writes them, its point in WGS 84, its feature class and code, its country and first two divisions,
  its population, its zone and the day it last changed. The reader was built on 2026-10-11 against that day's export of
  Iran (`IR.zip`, 254,654 features, sha-256 795df164b7d90d31c4a739af18e772bed8d7883948a0d73584f386e021e0d2c9) and of
  Turkey (`TR.zip`, 99,888 features, sha-256 887a47909f77121dcd2632eea0a66d63c7f5b43b1ecd4b6eae521f16425db66b), read
  as one table.
- **Its licence** is CC BY 4.0: what a garden shows of it credits GeoNames, and an unchanged copy may be handed on.

## osm-places — OpenStreetMap's places, as the dumps Photon reads give them (fetched)

- **Not shipped.** Each machine fetches a region's dump with `python3 bin/fetch.py osm-places <continent>/<country>`
  (`https://download1.graphhopper.com/public/<continent>/<country>/photon-dump-<country>-1.0-latest.jsonl.zst`, its
  `.md5` beside it), and reads, of the places at a country's scale (Photon's layers country, state, county, city,
  district, locality), the element, its tag, its own name and its English, Persian and Turkish names, its centroid in
  WGS 84 and its country; a dump is streamed, never held decompressed. The reader was built on 2026-10-11 against the
  dump of Iran with the data of 2026-10-03 (112,376,109 bytes, md5 260427949b1214b85e6b36f77e5e6018 as published,
  sha-256 b15bdec0e72ac9fdf85dc27bff5e5ee1a01429e86c2c88c66da9d8ccecc72768): 72,840 places of its 1,196,260 objects.
- **Its licence** is the Open Database Licence 1.0, © OpenStreetMap contributors: what a garden shows of it says so,
  and a database made from it stays under it.

## cldr-bcp47.tsv — the types of the Unicode keys a reader sets (CLDR)

- **Source:** CLDR's own `common/bcp47` — `calendar.xml` (the keys `ca`, `fw`, `hc`), `number.xml` (`nu`) and
  `timezone.xml` (`tz`, each type with the IANA zones it stands for) — as the copy of CLDR on the machine that wrote it
  carries them (LibreOffice's liblangtag, CLDR 41's types: `fw` and `hc` since 28, the newest since 41), written by
  `python3 assets/view/lib/view_prefs.py --from-ldml <cldr>/common/bcp47`. One row per type of each key, with its
  aliases (`-` for none) and CLDR's description; a deprecated type is left out. Unicode License v3.
- **Read by:** `assets/view/lib/view_prefs.py`, which keeps a reader's own way of reading as one BCP 47 tag (UTS #35):
  a type not here is refused with a sentence, and a `tz` is shown in the IANA zone its first alias names.
- **Behind CLDR 48:** two zones (America/Ciudad_Juarez, America/Coyhaique) and eleven numbering systems the runtime of
  2026 knows are not here; written again from a later CLDR's `common/bcp47`, they are.

## The schemes of beings: the positions of the ladder each classifies (`at`)

Each licence below was quoted from its source first-hand on 2026-10-24, with the URL it was read at; each reader was
built that day against the file named, its SHA-256 given. A scheme's `at` (core/law/registries.yaml) names the
positions of the ladder whose beings its codes classify: the gate refuses a code said of a being whose kind holds none of
them (rule bearer).

## col — the Catalogue of Life, eXtended Release (fetched)

- **Not shipped.** Each machine fetches the release's ColDP archive with `python3 bin/fetch.py col`
  (`https://api.checklistbank.org/dataset/316691/export.zip?format=COLDP`, which answers with the archive
  ChecklistBank prepared), and reads its NameUsage.tsv: each accepted name and synonym with its rank, parent and
  authorship. Built against COL26.10 XR, issued 2026-10-16 (144,796,066 bytes, sha-256
  eee7ab4bc2d5cfc0c0d28c0d56c4f1d92d6cc65df8f36883eef8f49ec603f93d): 8,504,545 name usages. The XR has no Darwin
  Core Archive: ChecklistBank answers "DwCA archive for dataset 316691 not found".
- **Its licence** is CC BY 4.0: ChecklistBank's record of the release says `"license": "cc by"`
  (https://api.checklistbank.org/dataset/316691). What a garden shows of it credits the Catalogue of Life, citing the
  release's DOI, 10.48580/dgzlf.

## ncbitaxon — NCBI's taxonomy, as the OBO Foundry builds it (fetched)

- **Not shipped.** `python3 bin/fetch.py ncbitaxon` (`http://purl.obolibrary.org/obo/ncbitaxon.obo`), read by the
  reader `obo`: each taxon with its rank, parent and names. Built against the build of 2026-07-12 (688,489,597 bytes,
  sha-256 a73eb642b33e2ec8480ef452574885b9d2627c97898d62ac096f0b173a292b69): 2,854,484 taxa.
- **Its licence:** NCBI "itself places no restrictions on the use or distribution of the data contained therein"
  (https://www.ncbi.nlm.nih.gov/home/about/policies/); the OBO build's own header names CC0 1.0 (`terms:license
  https://creativecommons.org/publicdomain/zero/1.0/`), as the OBO Foundry's page does.

## uberon, cl, hao, po — anatomy and cells (fetched)

- **Not shipped.** Each is read by the reader `obo` from its purl
  (`http://purl.obolibrary.org/obo/<name>.obo`): each term of the ontology's own prefix, its parents, what it is part
  of, its synonyms. Built against UBERON releases/2026-10-01 (22,529,133 bytes, sha-256
  d4751a15d7551a8414caee2628c62bf68301d567caf54ccfa3eef383ae7cbb61, 16,141 terms); the Cell Ontology
  releases/2026-06-08 (17,353,259 bytes, sha-256 7e19b4aef8e7fe7720b0c4474c6a5b8713c904ea9ab7b7d5d96f2cb28b8fc51f,
  3,531 terms); the Hymenoptera Anatomy Ontology's master copy (918,246 bytes, sha-256
  2fbbc0ccfda41d1b1d201dff9abe4056ca635878ab1bcedf958cf484d8c2c633, 2,596 terms, no data-version); the Plant Ontology
  releases/2026-01-09 (1,338,438 bytes, sha-256 d90949737a9925bdb775ba7dd4a9521cb63ca4acd40211e4c7661655f379f4c9,
  1,793 terms).
- **Their licences**, each from its repository's LICENSE and its file's header: UBERON CC BY 3.0 ("Attribution 3.0
  Unported", `dcterms-license http://creativecommons.org/licenses/by/3.0/`); the Cell Ontology CC BY 4.0; the
  Hymenoptera Anatomy Ontology CC0 1.0 ("CC0 1.0 Universal"); the Plant Ontology CC BY 4.0.

## chebi — chemical entities (fetched)

- **Not shipped.** `python3 bin/fetch.py chebi` (`http://purl.obolibrary.org/obo/chebi.obo`), read by `obo`. Built
  against release 256 (271,094,615 bytes, sha-256 1fd3e7d0b9ba51934b20ebcda01eefe6e14f3b3b835a737a4665414da2122c50):
  219,012 entities.
- **Its licence** is CC BY 4.0: "The data on this website is available under the Creative Commons License (CC BY
  4.0), and governed by EMBL-EBI's terms of use" (https://www.ebi.ac.uk/chebi/about); the file's header says the same.

## iucn-get — the IUCN Global Ecosystem Typology (fetched)

- **Not shipped.** `python3 bin/fetch.py iucn-get` reads the map details of the typology's version 2.1.3
  (`https://zenodo.org/api/records/10081251/files/map-details.xml/content`, 114,612 bytes, sha-256
  6df0b503e5e4503de7538da2ec84d54584a12eb5ab8b16b85c0d0165585c2379): 109 functional groups by code and name, and the 25
  biomes and 10 realms their codes name.
- **Its licence:** the Zenodo record is CC BY 4.0 (`cc-by-4.0`). The biomes' and realms' names are not read: they are
  in the typology's descriptive profiles (Keith et al., eds., 2020), "© 2020 IUCN", whose reproduction "for resale or
  other commercial purposes is prohibited without prior written permission"
  (https://portals.iucn.org/library/sites/library/files/documents/2020-037-En.pdf).

## etim — ETIM's classes of technical products (fetched, never forked)

- **Not shipped.** `python3 bin/fetch.py etim` reads ETIM 10.0's international English edition as its CSV export
  (`ETIM-10.0-ALL-SECTORS-CSV-METRIC-EI-2024-12-05.zip`, 2,895,379 bytes, sha-256
  9b2aa17f105315884661fe6a7a35f5fdbc8835d768a5906117cbc420420b6214, downloaded without an account): 159 groups and
  5,640 classes with their synonyms. Its group "Machine element" (EG020017) holds 31 classes.
- **Its licence:** "The ETIM Classification Model … and ETIM MC (Modelling Class) extension are made available under
  the Open Data Commons Attribution Licence" — and "we would like to make sure that worldwide there is only one copy of
  the model being maintained by the rightful author and owner" (https://www.etim-international.com/?p=1811). So each
  machine reads ETIM's own copy, and daftar cites its codes, never its texts.

## cpv — the EU's Common Procurement Vocabulary (fetched)

- **Not shipped.** `python3 bin/fetch.py cpv` reads the Publications Office's Genericode of CPV 2008, version
  20260520-0 (its Cellar item, 26,352,171 bytes, sha-256
  aedd06f0ee402c8a49d3d8b9928c10656e4d6a3918d55328b0efae53440b50f1): 9,454 codes with their English names.
- **Its terms:** the CPV is Commission Regulation (EC) No 213/2008; Commission Decision 2011/833/EU makes the
  Commission's published documents "available for reuse: (a) for commercial or non-commercial purposes … (b) without
  charge … and (c) without the need to make an individual application", on conditions that may include "the obligation
  for the reuser to acknowledge the source" and "not to distort the original meaning" (Articles 4 and 6, read at
  http://publications.europa.eu/resource/celex/32011D0833). The vocabulary's own record names no licence, and the
  Publications Office sends questions on "the conditions under which the content of the CELLAR, and of the EU
  Vocabularies may be re-used" to op-copyright@publications.europa.eu. Held as `LicenseRef-EU-Commission-Decision-2011-833`:
  fetched by each machine, its codes cited, nothing shipped.

## wikidata — any being, by its item (at its authority)

- **Not held, and asked nothing.** A code of it (`wikidata:Q48378`) is checked here by its form alone. The finder
  (`python3 bin/knowledge.py propose`) reads only the schemes held here: it sends no being's words to Wikidata.
- **Its licence:** "All structured data (i.e. the main, Property, Lexeme, and EntitySchema namespaces) is released into
  the public domain under Creative Commons Zero" (https://www.wikidata.org/wiki/Wikidata:Licensing).

## made.yaml — the made scheme: made bodies by their form and their role (shipped)

- **Daftar's own words**, CC BY 4.0, with daftar's law. Each row is a concept: a pattern in the core's basic set — a
  body of a compliance, its features, `part` and `join`, the core's pairs and closures (core/law/verbs.yaml) — with its
  limits. Its ground is Reuleaux, *The Kinematics of Machinery* (1876; A. B. W. Kennedy's translation, public domain):
  pairs of elements, links, chains and mechanisms, the pairs kept by their shapes, a force or the chain, and the
  flexible tension- and pressure-organs; the pairs are named as ISO 10303-105:2019 (STEP kinematics) names its pair
  entities, and the features after ISO/TS 10303-1814's machining features where one fits — names only, no text of
  either standard copied; a feature as a dependent part of its body, and a fiat part of one body, after Smith (1996)
  and Smith and Varzi (2000). No published topological definition of a part's type was found: the patterns are
  daftar's own.
- **Its 46 rows** are machine-elements.tsv of the beings' design (2026-10-24, daftar's own words) rewritten as patterns:
  the mechanics design's 47 concepts, measured on a generic seed of six assemblies and a held-out water pump
  (test/mechanics-seed.yaml), less the radial shaft seal, which no part of the seed exercises. The draft's families
  (transmission, bearing, seal, fastener, fluid power, damping) are roles, what bodies do, and are not rows.
- **Its crosswalk** — the columns `wikidata`, `etim` and `cpv` — is the draft's: each concept's Wikidata item (CC0),
  and the codes ETIM (ODC-By 1.0) and the CPV (Commission Decision 2011/833/EU) give it, cited and never their texts;
  their own tables are each machine's fetched copy (`etim`, `cpv` above).
