# seed/knowledge — sources, licences and attribution

The files in this directory are **data**, each under its own terms, distributed alongside daftar's
Apache-2.0 code as separate works (aggregation). The gate reads them through `registry_files` in
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
  run it — a judgement, open to correction by pull request like any row. Apache-2.0 with daftar.

## crosswalk-isco-08-isced-f-2013.tsv — which fields an occupation draws on

- **Derived, not official** (no official ISCO-08 ↔ ISCED-F 2013 crosswalk exists). Each row counts, for one
  ISCO-08 unit group, how many role→skill requirements of a hand-classified skills standard reach one ISCED-F
  field (split by importance: core, common, specialist), how many roles contribute, and the most frequent
  concrete topics. Coverage is that standard's domains only (96 unit groups) and grows as other gardens
  classify roles. Apache-2.0 with daftar.

## Job descriptions — ESCO (to be added)

ESCO (European Skills, Competences, Qualifications and Occupations), © European Union, reusable under
Commission Decision 2011/833/EU. Attribution: "This service uses the ESCO classification of the European
Commission." Modified or adapted versions must be marked as such.
