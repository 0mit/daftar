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

## crosswalk-fhir-r5-observation.tsv, crosswalk-dwc.tsv — another standard's records, carried into beans (step 11)

- **Source:** the field names of HL7 FHIR R5's `Observation` resource (hl7.org/fhir/R5/observation.html; the
  specification is published under CC0) and of Darwin Core's occurrence terms (dwc.tdwg.org/terms; CC BY 4.0,
  Biodiversity Information Standards (TDWG)), and the UCUM codes of the units the law declares. Each row pairs one of
  their fields with the entry path of `observations` or `located_at` that carries it; the pairings and the notes are
  daftar's own.
- **Licence:** the FHIR crosswalk is CC0, as FHIR is; the Darwin Core crosswalk is CC BY 4.0, as Darwin Core is, with
  TDWG's attribution in NOTICE. The names they cite remain their publishers'.
- **What the files are for:** `bin/crosswalk.py` reads them, and nothing else, to carry records in and back. A field
  with no row is listed, never dropped; test/crosswalk.py proves a round trip equal field for field.

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
