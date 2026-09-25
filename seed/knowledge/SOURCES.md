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
  own overlay with a `name_<lang>` column (`bin/dmknowledge.py` reads `label(scheme, code, lang)`), under
  whatever terms apply to that translation. For ISCO-08, a translation needs the ILO's permission
  (rights@ilo.org).

## technology.tsv — established technologies and their official documentation

- **Curated by daftar.** Every `docs` URL is the project's OWN documentation (checked 2026-09-19), never a
  third party's. `isced_f_2013` and `isco_08` name the fields a technology draws on and the occupations that
  run it — a judgement, open to correction by pull request like any row. CC BY 4.0, with daftar's law.

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
