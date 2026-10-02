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
