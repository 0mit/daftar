# daftar — the law's changelog

The journal of `seed/std-vocab.md`: what each version of the law changed, and why. It was kept at the foot of the law
file until 23.1, which moved it here, because a record of what was is journal, not law. The entries from 1.0 to 16.2
run oldest first and those from 17.0 newest first, as they were written; a new version goes above the newest.

- **1.0** (2026-07-31) — initial standard: `ip, hostname, fqdn, mac, serial, wg_pubkey, emp_id, id, ref, shell-log` with anchor/merge facets. Seeded from the project's v0.x design + 3 review rounds.
- **NOTE ON THE GAP.** This changelog jumps 1.0 → 6.0 and the four releases between them are missing.
  They were never written down here, and this file's own prose claims "this file's version history is its
  changelog below" — so the claim has been false since 2.0. Not backfilled from memory: git holds the real
  history and inventing entries from a diff would put a reconstruction where a record belongs. Recorded as
  a gap so the next reader knows it is one.
- **6.0** (2026-08-07, human-ratified rule-change) — **the network stack becomes data.** Two registries
  (`address_systems`: ipv4/ipv6 as SEPARATE systems, the call `anchor_systems` already made for
  filesystems; `net_protocols`: 14 rows). A fourth aspect, `confidentiality`, and the first ONE-DIMENSIONAL
  figure — `poles` always allowed it and nothing had exercised it. A `network` profile carrying
  `endpoints`, `links`, `reaches` and `treatments`, the last `required_on_kinds: [router]`. MAJOR rather
  than minor because that requirement retroactively re-classifies an existing bean, which is the stated
  criterion. Withdrew two Tier-0 vacancies the same day — `aspect:capability = permitted` and
  `aspect:necessity = necessary` — both predictions the new terms made come true within the hour.
- **7.0** (2026-08-07, human-ratified rule-change) — **kind stops carrying what a being DOES.** `router`
  and `vps` retired into a widened `host`: the first was a ROLE (the corpus already held a server's five roles
  as data while a router's one was a kind), the second was TENANCY (`owned_by.legal.external` and
  `provides_habitat` already said it, and the registry had flagged itself since P3). New registries
  `roles`, `operating_systems` and `storage_formats`; new terms `role`, `roles`, `os`, `storage_format`,
  `volumes`, and `beanger`. `roots.system` is now held by `entry_must_match` to the grammar its host's
  `os` declares. GATE CHANGE: `required_on_<axis>` reads a MULTI-VALUED axis — scalar, list of scalars, or
  list of entries — which is what let `treatments` move from `required_on_kinds: [router]` to
  `required_on_roles: [router]` without losing the guarantee. The gate's behaviour on every other corpus was unchanged.

- **8.0** (2026-09-17, human-ratified rule-change) — **a list's members are matched by a declared identity,
  never by accident.** `merge.order` for a `list_of_entries` term is `by-<field>[+<field>...]`, and a field
  may carry a trailing `?` meaning its ABSENCE is part of the identity. Three terms had declared `by-key`
  over entries that have no `key` field, so `bin/dmmerge.py` silently keyed each member by its whole
  content: the same role with a different `why` merged into TWO roles, with nothing said. Now: `roles`
  by-role; `treatments` by-kind+what; `endpoints` by-protocol+system+at+port? (protocol+system+at alone
  was measured NOT unique — 11 entries on three beans differ only by port — and
  an sftp endpoint, riding ssh, has no port of its own); `located_at` by-system+at? (an `unknown` position
  has no `at`, and by-at alone collided two unknowns in different systems); `consumes`
  by-bean?+mapping?+field? (an entry IS a ref, and the ref is its identity). MAJOR because merge outcomes
  change for beans that already passed. GATE CHANGE: the vocabulary is refused if a list term's identity
  names a field that is not required on every entry (unmarked) or not declared at all (`?`), and the
  merge refuses an entry missing an unmarked identity field instead of keying it by its content.

- **8.1** (2026-09-17, human-ratified rule-change) — **three predictions came true and are withdrawn.**
  Tier-0 vacancies `os.values = windows` `code_paths.scan_policy = skim` and `unit.values = minute`, each occupied by real beans. Checked
  against a real estate, not a fixture, before withdrawing. MINOR: a Tier-0 vacancy is advisory and no bean is re-classified. Deliberately
  NOT withdrawn: `analysis_cache.policy = skim` (no analysis reads structure only yet), `storage_format.values
  = ntfs` (no volume records it).

- **8.2** (2026-09-17, human-ratified rule-change) — **a garden can add, and the `domain` profile exists.** A
  cold-start drill found two things a new garden could not do without fighting the law. (1) To allow ONE value
  Tier-0 lacks, a garden had to copy a whole registry into VOCAB.md and declare a vacancy for every row it
  copied: now `schema: { values_add: [...] }` in a `local_terms` overlay appends to the enum, and
  `registry_additions: { <registry>: [rows] }` appends rows, and the garden accounts only for what it added.
  (2) A domain had no standard place for its registrar and expiry: `registration` is promoted from one
  garden's local vocabulary into a new opt-in `domain` profile, required on `kind: domain` for gardens that opt
  in. MINOR: both are additive, and no bean in a garden that does not opt in is re-classified.

- **9.0** (2026-09-17, human-ratified rule-change) — **a second cold-start drill, and what it found.** MAJOR, for
  one reason: `serial` now declares `compare_form: upper-trim`, so establishing serials that differ only by case
  or whitespace are ONE object — a garden holding `SYN-0042` and `syn-0042` as two machines, which passed before,
  is now refused. A stored serial not already in that form warns. Additive in the same release: the
  `operating_systems` registry and the `os` enum gain `linux`, `debian`, `ubuntu`, `rhel`, `fedora`, `arch`,
  `alpine`, `freebsd` and `macos` (until now the list held exactly the four systems of the garden it grew in),
  and the `pppoe` row loses a `transport: tcp` / port 1723 copied from `pptp`. A garden that added one of the new
  OS values locally with `values_add` is told to remove its copy.

- **9.1** (2026-09-19, proposed rule-change) — **knowledge as universal anchors: the `knowledge` profile.**
  Published classifications become shared codes every garden uses: ISCED-F 2013 fields of knowledge (UNESCO) and
  ISCO-08 occupations (ILO), each kept WHOLE in `seed/knowledge/` with their codes and English titles, plus a curated
  `technology` catalogue whose every row links the project's own official documentation, and an ISCO→ISCED
  crosswalk derived from a garden that classified hundreds of roles and skills by hand. Three generic gate
  additions: `registry_files` (a registry kept in a data file, never read as empty when missing),
  `value_in_registry` (an anchor must be a code of its scheme), and `registry_from` (an entry's code is checked
  against the scheme the entry names). An opt-in profile: a garden that does not extend `knowledge` inherits
  nothing. MINOR: additive; no bean anywhere is re-classified.

- **9.2** (2026-09-19, human-ratified rule-change, "T0") — **sequence: the second figure.** Until now every
  aspect was an opposition and `figure:` was free text (`square-of-opposition`, even on a one-axis aspect). A
  `figures` registry now owns that enum: `opposition`, named for what it is rather than for one dimension of it,
  since a square is its two-axis case and a cube its three-axis case; and a second figure, `sequence`: positions related by neighbourhood along direction lines, declared
  ONLY by five stated restrictions (`lines`, `metered`, `order`, `acyclic`, `ends`) plus its `domain`. Three
  aspects take it: `time` (one metered line, order PARTIAL, so positions whose resolutions overlap are
  unordered), `place` (semi-defined; civil time resolves through it), and `walk`, which re-reads the `dag`
  rule: a term with `dag: true` is a position on `walk`, and the gate refuses a cycle because `walk` declares
  `acyclic: true`, not because code names the key. An EXTENT (a duration, on time) is a bounded region of an
  ordered sequence's domain; an opposition has none, and says so. MINOR by effect: the re-reading of `dag` changes no
  verdict (proved by running both gates over a real garden and 47 mutations of it); the one new requirement is
  that an aspect's `figure` names a declared figure, which refuses only a GARDEN-LOCAL aspect with an undeclared
  figure, and no garden is known to declare a local aspect.

- **9.3** (2026-09-20, human-ratified rule-change, "T2") — **the merge orders positions in time.** `leaf_orders`
  gains `instant`, which applies to every value that is a position in `gregorian-civil`'s one form, whatever
  its key is called (a leaf order may now name a `system` instead of key names). A reading is absorbed by a
  finer one it contains; readings that do not nest stay a conflict, because `time` declares its order partial.
  MINOR: two gardens that recorded one moment at different resolutions now converge where they conflicted.

- **10.0** (2026-09-20, human-ratified rule-change, "T3") — **time in the record itself.** MAJOR, for one
  reason: a journal entry a commit ADDS must be headed with a position in gregorian-civil's one form, to at least
  the minute, with its offset (`## 2026-09-20 00:15+03:00 · who · what`), per the new `journal` block. A garden
  whose writers head entries with a date alone, or with `+0300`, has its next commit refused until they write the
  form; the entries already written are never checked. Additive in the same release: a `value_types` registry
  moves the gate's type patterns into the law, and declares `iso_date` as the calendar at unit DAY, so every
  existing date is a position whose time of day is unknown, with no data changed. `dmupgrade` heads its journal
  entry in the new form.

- **10.1** (2026-09-20, human-ratified rule-change, "T4") — **routines are sequences.** A `routine` aspect on
  the sequence figure (open lines, because branches add lines; NOT acyclic, because a routine may loop), and
  `steps` gains `on_sequence: routine`: its value is either prose lines, read in list order as before, or step
  entries `{id, do, next: [{to, when?}], note?}`. A step's `next` is a CLOSED neighbourhood, these branches and no
  others, so the gate refuses a branch that points nowhere, a step nothing reaches, a branch without its
  condition, and a routine that never ends. MINOR: prose steps stay legal, so no existing mapping changes.

- **11.0** (2026-09-20, human-ratified rule-change, "place P3") — **place, where time already went.** MAJOR, for
  one reason: `analysis_cache.staleness_key` must now be a position in the git object graph (`<repo>@<sha>`) or
  `manual:<why>`. `git-head:<sha>` was resolved against whatever tree the READER had checked out, so one
  analysis had one verdict per machine; a garden carrying the old spelling has its next commit refused until it
  restates them. Additive in the same release: a `network-segment` anchor system, because a segment is WHERE A
  BEING IS ATTACHED (a place) as against where it answers (an address); `entry_pattern` and `entry_soft_pattern`
  in the schema language; and `code_paths.path` / `covers_paths` WARN while they carry a bare absolute path,
  which names no host — in the estate this grew in, 13 such paths exist on two machines as two different trees.
  The error for those follows in a later release, once a corpus has been migrated onto `root:` positions.

- **11.3** (2026-09-20, proposed rule-change) — **the rank the merge kept to itself, and a schema language that
  describes itself.** `provenance_src` declares `merge.order: "generated-by-tool<inferred<observed<asserted-by-human"`.
  MODEL.md and MERGE.md have always stated the guard; the order that implements it was a constant in
  `bin/dmmerge.py`, which now reads the declaration the way it reads `anchor_authority`'s and refuses to merge
  without one. No merge outcome changes: the declared order is the one the constant held. And `schema_language`
  declares four constructs the gate has interpreted for months and the language never mentioned — `path`,
  `alt_form`, `attr_types`, `canonical_note`; the gate now WARNS when a term's `schema:` uses a key the language
  does not declare, because an unknown construct is a rule that silently enforces nothing (a typo in
  `entry_required_attrs` has always passed). A warning and not an error, so this stays MINOR: no bean and no
  vocabulary that passed before is refused.

- **12.0** (2026-09-20, proposed rule-change) — **structure before prose, and a rank that says why.** MAJOR, for
  two reasons. (1) AN ENTRY HOLDS ONLY THE ATTRIBUTES ITS TERM DECLARES. Top-level keys have been closed since
  2026-09-17; one level down, one garden of 143 documents held forty attributes no term knew — sentences promoted
  to field names (`what_this_does_NOT_establish:`) so that prose would look like data. They are refused now, and
  prose goes in the attribute a term declares for it: `note` is declared on `code_paths`, `registration`, `refs`,
  `owned_by`, `responsibility`, `timing`, `roots` and `capture`. Declared because beans legitimately carried them:
  `capabilities.feasibility_why`, `risks.resolution` / `resolved`, `capture.supersedes`, `refs.path`,
  `git_host.repo`, `since` on the two ownership arcs. `provenance` is allowed on ANY entry, because MODEL.md has
  always said a fact may carry its own. A term that declares no attribute (`owns`, `details`, `attributes`) stays a
  free container, by declaration. (2) A SCHEMA KEY THE LANGUAGE DOES NOT DECLARE IS AN ERROR (a warning at 11.3).
  Also: `provenance_src` states what each src MEANS and why it ranks where it does, and `generated-by-tool`
  BORROWS its standing — it ranks as the weakest src in its `provenance.from`, and at the bottom only when it
  names none; the label is never rewritten. And a fourth vacancy reason, `universal`, for a position declared
  because the mechanism is general rather than because this garden expects an occupant.

- **13.0** (2026-09-20, proposed rule-change) — **the law keyed by attribute.** MAJOR: the SPELLING of a term's
  schema changes, and the old spelling is refused. Until now one attribute's law was scattered across as many
  constructs as it had properties — `entry_required_attrs`, `entry_values`, `entry_types`, `entry_in_registry`,
  `on_aspect`, `pointer_fields`… each a map keyed by attribute — and stated a second time, for people, in the
  term's `entry_attrs:`; the two copies are on record as having drifted twice. Now it is stated once:
  `schema.attrs.<name>: { required, in, meaning }`. EVERY ATTRIBUTE IS A POSITION IN EXACTLY ONE DOMAIN —
  measured over every term before the spelling was chosen: none carried two — so `in:` is one thing
  (`schema_language.attr_domains`): a closed list, a registry, an aspect, a value type, the form a sibling's
  system declares, a pattern, `extent`, `ref`, a pointer, `id`; or `prose`, which is deliberately not a position;
  or `untyped`, which owns up to a domain nobody has declared yet. An attribute that states no domain is refused.
  `cross_aspect`, `entry_required_if` and `entry_expect_if` were three constructs for one idea and are `cells`.
  The marker `self` inside the ref lists is `is_ref: true`. EIGHTEEN constructs and two doc maps are retired; a
  garden's overlay now merges `attrs` per attribute, so it can add one attribute to a standard term without
  restating the rest. NO VERDICT MOVES: proved over a real garden with the old law under the old gate against
  the translated law under the new one, every mutation applied to both, a mutated law compared with its own
  translation — identical output in every case. What changes is wording: a refusal names
  `schema.attrs.<name>` where it named a retired construct. A GARDEN DOES NOT REWRITE ITS OWN TERMS BY HAND:
  `bin/dmreform.py` translates them, keeps every comment, proves per term that the form read is unchanged, and
  leaves the file alone when it cannot; `bin/dmupgrade.py` runs it inside its rollback. The standard's own text
  was translated by the same tool, then its comments put back beside what they explain by hand. One comment was
  deleted, because it had become false: "human documentation; the GATE reads schema: above".

- **14.0** (2026-09-20, proposed rule-change) — **addresses and ports are places.** MAJOR: the `address_systems`
  registry and the `address_system` term are gone, so a garden that added a row there must move it. 6.0 gave ipv4
  and ipv6 their own registry and `dimension: address` because where a being IS and where it ANSWERS are two
  questions. They are — but that is a difference of RELATION, which this law carries as terms (`located_at`,
  `endpoints`), as `observed` / `expires` / `created` are relations to one dimension of time. And `address` was a
  dimension NO ASPECT HELD: the two systems belonged to no figure, while `leaf_orders.cidr` had already described
  them as a containment order, which is `place`'s. They join `anchor_systems` as place systems. A PORT is a
  position nested in an address the way a path is nested in a host; it had no system because the transport layer
  had no row. `tcp` and `udp` are `net_protocols` rows now (`layer: transport`), `tcp-port` and `udp-port` are
  place systems, and `endpoints.port` — `untyped` until now — is a position in the port space its transport
  names: `port: "110/143/993/995"`, the defect the term was written to end, is refused at last, and so is 70000.
  `endpoints.system` may be ANY place system, so a unix socket path is an endpoint like any other. An entry may
  state `transport` when it differs from its protocol's usual one. TWO GENERIC ADDITIONS, neither naming a term:
  `where:` narrows a registry domain to the rows that say so, and `default_from:` reads an attribute's value off a
  registry row when the entry is silent — never written back, never an occupant. NOT in this release, on purpose:
  a system row stating its OWN restrictions (a port line is one totally ordered counted line; geographic is
  metered) so that extents and recurrences can ask the system what it permits. That arrives with its consumer.

- **15.0** (2026-09-20, proposed rule-change) — **a system knows its own shape; the network stack completed and rooted
  in the fields of knowledge.** MAJOR for ONE reason: a verdict cell now sees EVERY attribute of an entry (it saw only
  aspect positions), and `endpoints`' cleartext-and-required cell names `exposure: [lan, link, internet]` — so the
  loopback over-fire it had carried since 6.0, and explained at length in its own `why`, ends. Everything else is
  additive. A SYSTEM ROW MAY STATE ITS SHAPE: `levels` (the resolutions a position may be held to — a named list or a
  counted range; a level is metric when it names a unit, and a month never does), `within`, `resolves_through`,
  `neighbours`, and its own `restrictions`, which narrow its aspect's and never widen them. It is the "subaspect" of
  the 2026-08-05 time conversation and the thing `place` has always said it lacked. Every existing system states it;
  the trees of knowledge already had. `units` gains `hour` and the first LENGTH, `metre`. Three canonical systems for
  a garden that keeps a map: `iso-3166`, `osm`, `postal-code`. `planes` (data / control / management) is a registry
  and an attribute of endpoints, links and treatments, with one new cell: a MANAGEMENT surface answering on the
  INTERNET. `net_protocols` gains the network layer, the rest of the link layer, and the control plane — OSPF, IS-IS,
  RIP, EIGRP, BGP, each with its `family` and `scope` — and EVERY protocol row names its entry in the catalogue of
  technologies (`registry_links`, resolved by the gate), which gains 29 rows and is declared `within` the UNESCO
  fields: a routing mechanism ledgered tomorrow hangs from the same tree of knowledge as a mail server does today.
  NOT built: places-in-the-network as a registry of site roles (no garden yet has site beans); extents and
  recurrences that ASK a system its shape (next).

- **16.0** (2026-09-20, proposed rule-change) — **a calendar is not time, and a coordinate is never bare.** MAJOR for
  three reasons: the `geographic` system's form changes from a bare `<lat>,<lon>` to
  `<authority>:<code>;<coordinates>[@<epoch>]`; `osm`, declared establishing one release ago, no longer establishes;
  and the law's patterns are matched ASCII-ONLY, so a position written in another script's digits — which the gate
  accepted as a date until now, because `\d` matches every script — is refused. CALENDARS: all eighteen that Unicode
  CLDR identifies, and the Julian, are time systems, each with its own `levels` (a month is a level of ITS calendar
  and never metric; the Hebrew and Chinese year has twelve months or thirteen; the Japanese calendar has an `era`
  level), its `reckoning` (arithmetic / astronomical / observational / tabulated), when its `day_begins` (the Hebrew
  and the Hijri day at sunset), and a TAGGED form, because `1405-06-29` is also a Gregorian date. They all partition
  one line of days (`same_ground_as`, `crosswalk`), so they meet at the DAY: `bin/dmcal.py` converts through it for the
  fourteen reckoned by rule and REFUSES the five that are not. NO CALENDAR IS PRIVILEGED: a moment is stated in the
  calendar it was known in. Every dated attribute of the standard is typed `date` — a day in ANY calendar — and `bin/dmstale.py`
  ages one through the day. (Still Gregorian-only, named: `leaf_orders.instant` and the journal's heading form.) COORDINATES, after ISO 19111 / 19112: `bodies` (a
  latitude is a latitude ON something — the Earth, the Moon, Mars), `reference_systems` with their `kind` and whether
  the `frame` is static or DYNAMIC (ground drifts in a dynamic frame, so a coordinate there needs its epoch), and
  `geographic` as THE ROOT OF PLACE: every way of saying where by IDENTIFIER — an administrative code, a postal code,
  a street address, a grid cell, a map database's element id, a `local-frame` position such as "third floor" that
  travels with its building — `resolves_through` it and none of them is one. `bin/dmgeo.py` reads a position, names
  its grid cells and measures on the body the system names; it does NOT transform between datums, which needs
  published parameters. Generic additions to a system's shape: `same_ground_as`, `crosswalk`, `example` (held to the
  system's own pattern by the gate); the words a shape may use are declared in `system_shape`, so the gate carries
  no copy.

- **16.1** (2026-09-20, proposed rule-change) — **the law and its reasons, kept apart and related by key.** MINOR: no
  rule moves. Every comment left this file's front matter — eight hundred lines of argument, incident and history that
  had grown beside the rules — for `seed/RATIONALE.md`, VERBATIM, each under the PATH of the law item it explains
  (`anchor_systems[geographic].restrictions`). The law now says what is in force, and carries as DATA — `meaning:`,
  `why:` — the reason a reader needs in order to apply it; the rationale says why it is that way; the changelog and a
  garden's journal say what happened. `bin/dmwhy.py <name>` reads law and rationale together, and `--check` refuses a
  reason whose law item is gone, so a reason cannot outlive its rule unnoticed. `test/rationale.py` holds the
  separation: no commentary in the law, section titles that are only titles, no orphaned reason, and a RATCHET on the
  narrative that still sits inside the law's data strings (14 lines; it may only fall). Additive in the same release,
  from a look at what GNU publishes: the day itself as a system (`julian-day`, the astronomers' count, whose day
  begins at NOON) and the Mayan long count, both reckoned by `bin/dmcal.py`; the Badi and the French Republican
  calendars, declared astronomical and therefore not converted; `guix-store`, a second place system in which a
  position says what it holds; and `openpgp_fingerprint` and `ssh_key_fingerprint` as establishing identity anchors.

- **16.2** (2026-09-20, proposed rule-change) — **recurrence.** MINOR, additive. `in: recurrence` and `recurrence_form`:
  a repetition is a sequence whose neighbours are given by a rule. It strides by NEIGHBOURS (`every: { count }` — every
  tenth release), by MEASURE (`every: { count, unit }` — every five minutes, every five metres) or by CELL (`each:
  <level>` of a named system — the 15th of each Persian month). Which stride a repetition may use is read from the
  aspect's figure and from the SHAPE the named system declares — neighbours, metering, levels — so a new system gets
  repetitions with no change to the gate. `each` requires `in:`, because a level belongs to its system. An extent may
  name a system too, and then carries a measure where the system is metered and its aspect is not.

- **core 2.0** (2026-10-10, daftar v2.0.0, human-ratified rule-change: the unified-tools design, ratified 2026-10-09,
  and the operator's word on each part, the pull requests #110–#118 merged on it) — **what a value is to a reader;
  every peer a judge; the dimensions on the ladder.** MAJOR, by this file's own measure: it refuses what a garden could
  write before — a kind at a step the ladder no longer has (rock, organ system, biosphere, installation, corpus), and a
  quantity stated of what cannot bear it (rule `weight` became `bearer`). Every garden known to this repository passes
  it unchanged. Proposed as core 1.1 while it was MINOR, and named 2.0 when the ladder made it otherwise.

  **What a value is, and what a stamp, a code and a name are held to** (#111). The values tree (`core/law/values.yaml`):
  what each value is to a person who reads, shows or types it, beside how it is written, rooted in the core's shapes,
  checked whole. No bidi control character (Unicode's Bidi_Control) in a code or in a name a namespace gives (Trojan
  Source); free text keeps its own. Eight namespaces — `ror`, `wikidata`, `orcid`, `ifc-guid`, `dicom-uid`, `gs1`,
  `tr-tckn`, `ir-national-code` — with `namespace_shape`: a check digit checked by a well-used validator
  (python-stdnum, the standard library's uuid), never by a copy, refused where it cannot run; a government number kept
  only in the held store, refused written in a bean, judged by the store before it seals one. One flow row,
  `refusal-detail-served`: a refusal's detail served by the machine that holds it, never sent. The method `stamp`: a
  save stamps only from a clock within half a minute of its time sources (`bin/clock.py`), and writes nothing
  otherwise. `holding: fetched`: a scheme downloaded by each machine from its provider into a cache outside git
  (`bin/fetch.py`), ISCO-08 first. The hub takes a person's own signed labels on `refs/daftar/custom/<person>`, judging
  every commit the ref gains, and never counts one as the garden's. The view asset carries the values tree's widgets
  (`assets/view/lib/widgets/`): each value shown exactly, in each reader's digits, separators and calendar from CLDR,
  none privileged.

  **Every peer a judge** (#110, #113, #115, #116). A journal and a queue merge entry by entry, never by git's line
  union. A clone fetches each peer into quarantine and judges what it brought by the hub's own rules — the signature,
  the writer, the rights, the gate — before anything is merged (`hub.py receive`, `bin/sync.py`); a merge is judged for
  what it changed itself. A mailbox takes another garden's proposal by a key that can do nothing else, delivered until
  it is acknowledged, its receipts taken (`bin/mailbox.py`); a peer behind NAT dials out, and an always-on peer relays
  one loopback port to it (`bin/relay.py`).

  **What waits, and actions on the law's own walk** (#112, #114). Leads — a decision, a case at its step, an
  obligation within its notice, a failure a reading shows, an open session — are read from the garden each time, never
  configured or stored (`bin/leads.py`). A ratified action runs on daftar's own sequence machinery — a walk, a course,
  its moves: planned, shown, checked, ratified by a person, applied, verified, refused or rolled back with its reasons
  (`bin/act.py`). A person signs in by a passkey they hold, which the garden names (namespace `passkey`, #117).

  **The dimensions on the ladder** (#118). Each dimension stands on the step it needs and is held by what it may be
  stated of: time and length the frame's faces; mass and charge on the force fields; temperature on mass while an
  ensemble, held by a material; money on reason; information no dimension but a count held by what is carried, the
  carrier saying what it holds. Space-time is the gravitational field, the one field that is the frame; the force
  fields and, resting on them, the matter fields lie beneath the dot; each force binds twice (hadron, nucleus; atom,
  molecule); material is any bound step in number. A step is told by the organization it adds: five that added none
  are gone. One path, one statement: the law refuses a stand or a bearer another path already gives. 56 kinds, 155
  units in UCUM with exact factors (twelve with none, each saying why), the toman, the line `potential`, the Earth's
  GM, a vertical system's surface.

- **core 1.0** (2026-10-02, daftar v1.0.0, human-ratified rule-change) — **the core becomes the language, and
  std-vocab is retired.** Every fact is a statement — a verb and its roles (`by`, `of`, `through`, `to`, `from`, `at`,
  `as`) — known by an act that says who said, read, made or derived it; the law is `core/law/`, its own source, and
  this file, std-vocab's journal, closes with it. Built in thirteen parts, each a pull request (#91–#103 and this
  release's): the standards' tables out of std-vocab; the guides written in statements; the gate and the statement
  merge by the law a garden runs; the adoption (`bin/dmupgrade.py v1.0.0` translates a garden of std-vocab 32 in place,
  every value placed and counted, in one RULE-CHANGE granted history's moments once); every tool on statements, named by
  its verb; the forms of lines, measures, flows, profiles and the gaps; the suites, each retired promise held, gone with
  why, or ported. The law has twenty-one rules, each strict; today's gate's 91 checks are accounted for in
  `test/ported.yaml` (56 to a rule, 21 to the law's own proof, 5 to a tool, 9 gone with why). The decisions are the
  garden's spec, `daftar-core-spec.md` §1–§16, with each part's choices for the operator's veto in its journal.

- **32.1** (2026-10-01, human-ratified rule-change) — **the core arrives in every garden, beside the gate, and judges
  none yet.** The layer map places it: `core/law/*.yaml` in `law`, and `core/*.py` and `core/hooks/*` in `gate`.
  seed/LANGUAGE ships them, so a garden receives the core with v0.49.0 and an edit to it is a RULE-CHANGE. `core/`
  holds the minimal core's law as data: the face (seven roles, the shapes, the two figures, the order with its two
  frames and the line of the said, the crown, thirteen rules), the 35 verb rows, the kinds, levels and layers generated
  from this law, and the units in UCUM with the law's English names attached. It also holds its engine:
  `core/check.py` judges a garden written in statements; `core/translate.py` writes a copy of a 32.x garden in
  statements, with the count of every value as its proof; `core/commit.py` holds the commit's rules (the knowing act
  at the save's moment, RULE-CHANGE ratified, the adoption granted history's moments once). Built and ratified as
  daftar PRs #81–#88. MINOR: nothing that passed stops passing, and no bean changes. 32.x stays the law and today's
  gate the gate; a garden rehearses the switch on a copy, and v1.0.0 makes the core the language.
- **32.0** (2026-09-30, human-ratified rule-change) — **the base: the ladder from the frame to the crown, the life chain
  as vias, and ownership without facets.** From the operator's reading of the names ("a better form for base
  categorization … we need to make sure to inspect this as logical as possible"), inspected against Hartmann, Ibn Sina and
  Heidegger and ratified whole: "All ratified go through design in one release". MAJOR: every garden is translated.
  - **The ladder** (`complexity`, with `lines`): the frame, space∞time, one structure with two faces (`dimensions`
    time and length are its `face`s); the body's dot on it; matter; gravitation (rock, celestial body, and the
    planetary system and the galaxy, new); the living; λόγος, reason; the made. Each step says how it stands on another,
    `{ level, as: made-of | possible-on, while? }`, and a step's condition is a row of `conditions` (balance, اعتدال, for
    life; proportion for reason). A step that holds no body (`bodies: false`: the frame, λόγος) is no genos's `level`; a
    kind stands at it as its `rung` — a person's body is an organism, and a person speaks (`rung: logos`). The sayable
    stands on λόγος (`natures` `stands_on`). A part never stands above what its whole is made of.
  - **What holds from a foundation** (`foundation_rules`): every body has weight; a sayable being's own mass is refused,
    unless the attribute measures the bodies it stands for (`of_bodies`).
  - **The crown is one**: `theone`, the Necessary Existent (واجب الوجود), with two faces, `love` and `wisdom`. A being it
    holds says `owned_by: { crown: true }`; `theos` and `agape` are retired.
  - **The life chain is vias** (`via`, retiring `creator`): the beings through whom this one came to be, each a bean or
    `someone` of a kind reached through what is known (`through`, or `outside`). Strict: a living being's vias are
    living; a made body's and a sayable being's reach hands, a being at `logos`, through any tool whose own via goes on.
    Never demanded. Every chain ends at the Creator, `theone`.
  - **Ownership has no facets**: `owned_by` is one owner — `owner`, `contract`, `external`, `crown: true`, or `from` a
    parent (the inherited form, until now `via`). **The facets are ways of answering** (`responsibility`, the
    `facets` of care): before the law the owner answers unless another is stated (`answered_by_owner`), so a legal
    entry that repeats the owner is refused as a placeholder; a facet stands only on beings it applies to (`applies_to`:
    nobody runs a record). `facet_parity_with` is withdrawn; the `ownership` division is the `answering` division.
  - **How a being came to us** (`acquired`): the vendor or giver, how, the day, the agreement.
  - **Names**: 26 new items named by hand in the nine languages (93 in all); `material` renamed where it met the new
    line `matter`; the organ's English roots corrected (it is the capacity that has organs).
  - **The 32.0 step** gives each bean its one owner, keeps each answering entry that says something (drops a legal one
    that repeats the owner, and a facet on a being it does not apply to), writes `creator` as `via`, and gives a body
    whose hardware names its maker `via: [{ someone: person, outside: <the maker> }]`.
- **31.0** (2026-09-30, human-ratified rule-change) — **the root: the dot, the frame, the order of bodies, life, and
  the crown as the life chain.** From the operator's questions of the view's design: whether `empsychon` had been
  mistaken for a sibling of `soma` and `lekton`, and "we define dot, point, نقطه as undivisable being …". MAJOR: a
  nature is retired and every garden is translated.
  - **The natures are two.** `soma`, a being that takes room in space; `lekton`, a being placed in an order, a register
    or a habitat. `empsychon` is retired: a person is soma, an organism; an instance and a virtual machine are lekton.
    `natures` keeps each register's anchor family, and no longer routes a crown.
  - **`complexity`**, the order of bodies: twenty levels in four lines (matter, the living, material, the made), each
    naming what it `stands_on`. A genos of the nature soma names its `level` (a host a `device`, a person an
    `organism`); a part never stands above its whole.
  - **Life is each genos's.** Every row of `gene` states `alive_while`: while what it lives, and how that is known —
    measured, derived, said or always. `status` is the lifecycle it lives in.
  - **The crown is the life chain.** `crown` keeps `theos` and `agape`; `physis` and `logos` are retired, and
    `{ crown: agape }` is the one form. `creator` is the life chain's edge, with `via`, acyclic.
  - **An origin may say `alive: true`**: the provenance guard ranks by act, then by life, then by nature, so a person's
    word stays above a document's.
  - **A genos may refine its nature's anchor family** (`identity_policy.refined_by`): a person, a body, is established
    by logical anchors only.
  - **The frame.** `place` and `time` name each other; `dimensions` marks the frame's two; every place or time system
    states its `complement` (`stated`, `bearer`, `system`); `compound` joins space and time; GARDEN.md states its
    `zone`, where the chain ends.
  - **`division_form` and `divisions`**: a whole, its parts and their wholeness, in one form; the law's five divisions
    name the rule that judges each, and a garden's own is judged by the gate.
  - **The names layer** (`name_form`, `seed/names/<language>.tsv`): the law's words named in its readers' languages,
    siblings, for publication; never read for meaning. Its first seventy items — the root, the frame, divisions, the
    relations, the acts, the layers, the lenses and the garden — are named by hand in nine languages (English, Persian,
    Turkish, Ancient Greek, German, French, Italian, Latin, Arabic) with their roots, every name `proposed`; the gate
    holds the files to the form and the languages to one another.
  - **The view, from fact to eye** (the view design, ratified with it): a page states where it is shown (`located_at`,
    in the new `uri` place system, beside which `unix-filesystem`'s `<host>:<path>` never opens its path with `//`, a
    URI's authority); a drawing may state its `frame`, an aspect that is a line; a part may `open` a drawing
    of its own, or a boundary a detail of its drawing (the region at a larger scale; closed, the flows between two
    regions are one line a pair), and the lenses' limits are errors, counted outside the details; the being serving a
    URI is found by its own `endpoints`; the facts propose an operate shape (`view_archetypes` `frame`,
    `reads`). The kit records the fact an element stands for (`of`) and draws a part no fact states as `implied`;
    `view_engrave` lays a drawing out from a being's parts and pipes.
  - **Knowledge of the view's stack**: thirteen technologies join the catalogue (a `format` category among them), each
    checked at its publisher; `signals`, the names OpenTelemetry's semantic conventions publish, which a binding's
    `signal` names and a source adapter asks in its own language; `technology-daftar`, what daftar speaks, spoken only
    where its adapter and its suite are the release's.
  - **Surfaces, as adapters**: `assets/view/lib/surfaces/` — html (the one file), python (the served page), django (a
    fragment a framework renders) — each passing one conformance suite before `technology-daftar` says it is spoken; the
    page's own chain to the eye engraved on its reference tab.
  - **The sheet**: every drawing a sheet with a title block made of the ledger's facts, pens by what they draw, revision
    clouds around what the last commit changed; `view.palette`, the garden's own colours in day, night and print.
  - **The 31.0 step** translates each `empsychon` bean by its genos and each `physis` or `logos` crown to `agape`, and
    writes GARDEN.md's `zone` from `--zone` (or `DAFTAR_ZONE`); a local genos still `empsychon`, or a body with no level,
    is a person's to decide.

- **30.0** (2026-09-30, human-ratified rule-change) — **what a clause is for: an agreement's `over` keyed, and a clause's
  `over` naming the part it is for.** From queue-44: two purchases, one repaid in six instalments and one in four, which
  is which not said; seven runs of eight kept the counts in prose, and the one that kept them as data named owners it
  also said were unknown. The operator: "option 2 with over, raise the limit".
  - **`over`** is an open map, keyed in kebab-case like `parties`, `clauses`, `transactions` and `selections`; it merges
    by key. A field path into it goes through its entries: `over.*.thing`.
  - **A clause's `over`** is a key of it: the part the clause is for. Absent where the clause is for all of it, or where
    nobody has said — the question then in `open:`.
  - **The 30.0 step** keys each list entry by the id of the being it names, or by the first words of what it says,
    told apart by a number, keeping each entry's comment; paths into `over` are rewritten through its entries.
  - **seed/FORMS.md**: the phone loan becomes two purchases, one in six instalments and one in four, which is which not
    said; the page's limit moves from 17,000 characters to 17,700.

- **29.2** (2026-09-30, human-ratified rule-change) — **a refusal names where the word was meant to be, and the law says
  what an empty acceptance records.** From queue-44: a consent agreement right but for its empty `accepted` was refused
  eight times in words naming no bean and no party, and its writer ended by inventing a day. The operator: "all ratified
  go ahead".
  - **The consent refusal diagnoses** (F2): it names the bean the person's `consent` names and every agreement holding
    them as a party, says what fails there — not held, not a contract, not a party, declined, `accepted` empty — and
    prints the one line to write, `parties.<key>.accepted: { system: event-anchored, at: "after:<words.at>", unit: day }`.
  - **New is new, staged or not**: a person bean the commit before does not hold is refused by `--all` as by the save;
    `--all` had warned where the save refused. The refusal also says what `bin/dmheld.py person` needs to run.
  - **`empty`** in an attribute's record says what an empty or absent value records, where another rule reads it:
    `parties.accepted` records no acceptance, and so no consent. bin/dmforms.py shows it on every line that empties the
    position (rule 6), in place of 'empty unless said'; seed/FORMS.md's own prose says the same, and the page's limit
    moves from 16,600 characters to 17,000.

- **29.1** (2026-09-28, human-ratified rule-change) — **time is place's sibling; a working copy is a position; each
  profile in its place on the line.** The operator: "yes it take (does a meeting take someone's hour?) … fold
  workspace.at and check if view and other profiles occupies the right place".
  - **The rung `time`**, declared by `timing`: a happening takes the hours of those present at it (the event's
    `takes_time_of`: present, host), and one being present at two happenings whose spans overlap is refused. An
    invitation takes nobody's hour (RFC 5545's TRANSPARENT).
  - **`workspace`** names its `system`, and its `at` is in that system's one form, on the machine it names; its own
    pattern retires. bin/dmsession.py writes it; the 29.0 step translates a garden's working copies.
  - **The profiles on the line**: `endpoints` is a `location` that takes room — one port on one address is one
    listener's, refused when two beings bind it unless one lives in the other; `endpoints.system` and a view's
    `reference.system` take systems of place only. `links`, `reaches`, `treatments`, `knowledge` and the view's terms
    relate beings and place none; the code profile's trees are locations and the domain's registration an agreement.
  - **`dmpublic`** refuses, in what a range adds, a word the garden's own `PUBLIC-DENY` keeps out.

- **29.0** (2026-09-28, human-ratified rule-change) — **the line from place to location, and one capsule for a code:
  the five places a profile and the core said one thing twice, folded.** MAJOR: stored facts are reshaped, and
  `bin/dmupgrade.py`'s 29.0 step translates them where they are written, every comment carried to where its fact goes.
  The operator: "All 5 ratified … to make sure we are doing the most structural implementation possible, look if we can
  fold them through profiles, with a why check for the being of any of them"; and, of the third and fourth, a place
  (جا) as the ancestral definition of a being's placement and a location (مکان) as the more physical one, the line that
  orders them by abstraction, and whether a placement makes its host more limited.
  - **`placement`, the line**: `place`, the ancestor every placement walks up to, and its modes in order — `order`,
    `presence`, `habitat`, `location` — each saying what it `takes` from where it places a being: none, a share, or room.
    A term states its rung (`lives_in` habitat, `located_at` and `workspace` location); a shipped scheme, so the
    ancestor machinery reads it.
  - **`capacity`** on a host and **`takes`** on a placement: shares past a capacity are warned (a host may promise more
    than it holds), room past it refused, and the same room taken twice at once refused unless one is part of the other.
  - **`located_at.host`**: the being a position's frame belongs to — alone, the place known and the position not.
    `local-frame` states its datum, `host`; a new place system, **`git-remote`**, holds a repository as a client names it.
  - **`coding`**, one value type for a code with its scheme, `<scheme>:<code>`: observations, a stance's code, a step's
    process and its inputs and outputs, a channel's property, a relation to knowledge, a distribution. `scheme` retires as
    an attribute; no scheme is named as a genos.
  - **`identifier`** takes a code a published scheme gives what it classifies, as a coding: `isco_08`, `isced_f_2013`
    and `technology` retire as anchor keys.
  - **The code profile** overlays `located_at` with `role`, `scan_policy`, `stack`, `entrypoint`, and requires one on a
    codebase: `code_paths` and `git_host` retire. A tree of another code it is read beside is that code's location,
    reached by `depends_on`.
  - **The domain profile** adds `auto_renew` to clauses: `registration` retires into the contract it is — parties
    `registrant` and `registrar`, `timing.registration`, a `renewal` clause that falls due on the day the name lapses.
    Clauses gain their own `notice`; `words` gains `external`, a text held outside the garden; a cell may require one of
    several attributes.
  - **Profiles compose with the core's senses**: an overlay's attribute is the law's word, judged by the law's row.

- **28.1** (2026-09-28, human-ratified rule-change) — **analytic accounting, in the field's words, on the core's
  machinery; and every profile composes with every other.** MINOR: additive, nothing a garden holds changes. The
  operator: "we need to keep the law clean and define the field specific names to help existing users through
  profiles"; "ratified, but re-inspect our other profiles and go hunt of a general-law and profile lense sense merging
  opportunity then make sure a gardener can use all profiles when needed without data-duplication and conflicts".
  - **A profile may extend a core term** (`overlays`): attributes beside the term's, `sums` and `cells` after its own,
    and never an attribute the term states. The gate judges every profile against every other whichever a garden
    extends: no profile term named as a core term or as another profile's, no overlay rewriting the core, no two
    profiles adding one attribute to one term. A garden may extend them all. A key a profile adds, in a garden that
    does not extend it, is refused with the profile named and the command that extends it.
  - **`sums`** takes a list of rules, a constant whole, parts in another unit of the whole's quantity (converted
    exactly), and `per: {level}`: the parts grouped by the ancestor of the code each names, each group a whole; a group
    stated partly one way and partly another is refused.
  - **`apportion`**, an operation of the reckoner: each code's part of the members' amounts, by shares within a group
    or by amounts, summed per code or per ancestor at a level; exact, and with `digits: true` in the currency's cents by
    the largest remainders — the one rule for a split that cannot be exact.
  - **The `accounting` profile**: `analytic_distribution` on `transactions` and on `clauses` (a budget line) — entries of
    `{scheme, code, share | amount}`, a plan's amounts making the amount. A plan is a code at the first level of the
    garden's own scheme and an account one beneath it: one mechanism, and a new account a journalled row, never a law
    change. The field's words and where each is kept: seed/COOKBOOK.md, beside an ERP's.
  - **One sense, merged**: the analytic share was first a ratio; the gate's one-sense rule refused it, since `share`
    already means whole parts of a whole, a party's share of a cost. The analytic share takes that sense: 60 and 40 are
    three fifths and two fifths, and a plan's shares are its whole.
- **28.0** (2026-09-28, human-ratified rule-change) — **the ordinal line: a sequence that holds at no time.** MAJOR: three
  system choosers are narrowed to the dimension their meaning names, which can refuse a bean that passed. The operator:
  "absorb 2 x 2 as a sequence with two 2s summing a 4 as the whole sequence numeric value having two nodes", then
  "ratified just make sure we are not misusing the aspect dimension and other terms, look through catalogue for any
  candidates to be generalized with our new method".
  - **The `ordinal` aspect**: which in order — the first, the second — with nothing between two neighbours; no time and
    no place, so what lies on it holds at none of them. Its domain is `any`. Named for what its positions say: `count`
    is the law's word for how many, and an ordinal says which.
  - **The `ordinal-number` system**, of dimension `any`, `datum: line`, written tagged — `ordinal:2` — since a bare
    number is a port's and a geohash's spelling too: a position counted from the first of the line it
    is read on (`datum: line` is new), so it counts on every line — the second node, the third meeting, the fifth seat.
    A position standing alone lies on no line: a day, a `timing` moment, a place or an endpoint naming it is refused.
  - **A series on a counted line**: a series whose system's neighbours are counted states no unit, a grid strides by
    neighbours, and an ordinal number's position n neighbours on is `from` + n.
  - **A series' `whole`**: `{value, of, by}` — the value the series is as a whole, the channel it is made of, and how
    (`by`, a row of `aggregates`); checked exactly against the rows. Two times two: two nodes of 2, a whole of 4 by sum
    (and by product), 2 by count.
  - **`aggregates`**, one registry: sum, product, mean, min, max, count, first, last — read by a series' whole and by the
    reckoner's `window`, which gains sum and product (a product only of what has no dimension).
  - **`event-anchored` states its datum: `named`** — the position it names, its offset known only in direction (the
    operator: "isn't event-anchored going to be a new use of the latest machinery with new law?"). A position is an offset
    from a datum, and the datum says the kind: fixed, with a measured offset (`bp-1950`); the line's first, with a counted
    one (`ordinal-number`); or named in the position itself (`event-anchored`). The gate reads from the datum whether a
    position can stand alone — the long form of a day takes a system of time or one whose datum it names — where it read
    it from `dimension: any`.
  - **Narrowed**: `timing.system` to systems of time or of dimension `any`; `located_at.system` and `roots.system` to
    systems of place. Every garden known held only such systems there.
- **27.1** (2026-09-28, human-ratified rule-change) — **the permission square says its own name.** MINOR, no rule
  changes: 26.0 renamed the aspect `capability` `permission`, and the prose kept the old name in six places — the meaning
  of `clauses` (law), MODEL.md twice, the cookbook's agreement chapter, and the reasons for the square, for a clause
  on it and for why a risk is not one. Each now says `permission`. `capabilities`, what a being may or must be able to
  do, is a term of its own and keeps its name.
- **27.0** (2026-09-28, human-ratified rule-change) — **a day is a position, in either of its forms, and a moment is in
  time and place together.** MAJOR: a garden's own term typed `iso_date`, `date` or `date_or_moment` is translated by
  `bin/dmupgrade.py`, one typed `moment` is named for its gardener, and a garden's own metered system states its meter.
  Found by the local-model bench at v0.41.1, where a person
  who had agreed was refused as one who had not, because nobody said the day of the yes; and by the catalogue of the
  language (`daftar catalog --part value_types`): 29 attributes of 19 terms hold a day, and none could hold one nobody said.
  - **One position type** (the operator: "fold date and moment into one position type"). `date`, `moment` and
    `date_or_moment` are one value type, `position`: a position in time in any calendar, held to the unit its form is
    written at — a day, or a moment to the minute or finer with its offset. What the three said moves to the attribute:
    `in: { type: position, unit: minute }` holds a move and a pin to the minute, and the unit is what the save writes for
    `now` (`observed` and an analysis's `as_of` say `day`). The rest take a position at any unit: a yes may be written to
    the minute. The three are retired into it.
  - **The long form.** `position` names the term whose one entry it may be written as (`long_form: timing`), and
    so every day position of the law — `accepted`, `declined`, `agreed`, `day`, `due`, `since`, `created`, `expires`,
    `observed`, `found`, `resolved`, `retracted`, an analysis's `as_of`, an observation's and a move's `at`, a pin's — takes
    `{system, at, unit, by?, note?}` besides its short form, at the type's unit. It is the same position: its `at` is the
    short form, judged as that. It says what only `timing` could: a day placed by what it followed (`event-anchored`), who
    read it, a note. No bean changes; the attribute names stay, because the law reads them by name. A provenance's
    `as_of` is the save's reading of the clock, never a day nobody said, and stays as it is.
  - **An acceptance whose day nobody said is an acceptance** (E, ratified by the gardener): written long and placed by what
    it followed, it counts as consent where the agreement is one. The forms show it; the refusal of a person kept by name
    without consent names it.
  - **`iso_date` is retired** into `position`, which holds every day it held. No term of the law used it.
  - **`event-anchored` refuses a placeholder**: a neighbour in angle brackets (`after:<what it followed>`, as the forms
    show the shape) is no neighbour, and a copy left unfilled is refused.
  - One reader: `bin/dmcal.py` reads both forms (`written`, `shown`), and `Unplaced` says a day placed by its neighbours
    names none; the readers that reckon with a day — the ledger, what falls due, the reckoner, a course, the page's
    calendar — read the long form as the short, and say of one placed by its neighbours that it names no day.
  - **A moment says where it was** (the operator: "moments they have time and places together"). A `timing` entry, and so
    every day written long, takes `where`: one place position `{system, at, zone?, u?, note?}`, a place system's. Civil
    time is read from a place, so the moment carries the place its time was read from, in the same entry.
    `bin/dmwhere.py` reads a moment's offset against the zone in force there — from the machine's zone database, which
    is why the gate does not.
  - **A meter is the system's.** An aspect says what a length along it is measured in — `time` a duration and, from
    27.0, `place` a distance (`metered: length`); a system says whether it has one. The 24 calendars state
    `restrictions: { metered: time }` as geography states length; a system whose neighbours are metered and states no
    meter is refused, and one that states none is not metered — a stride in years along the rock record's counted line
    is refused. Where no system is named the aspect's word is read, and a stride along place names its system, since
    place has many lines and a stride walks one.
  - **No time is absolute.** Every calendar whose day begins at a local moment resolves through a place
    (`resolves_through: geographic`), as gregorian-civil did, and the gate asks it of any that states `day_begins`;
    `unix-epoch` states its datum, 1970-01-01 00:00Z.
  - Left out, parked: a fact that holds at every time (2 × 2 = 4). No position of the law holds a time for it, so a
    "does not apply" system would have no occupant; it is the fact's to say, not a position's.
- **26.1** (2026-09-28, proposed rule-change) — **a link's peer is mutual.** MINOR, no rule changes: `links.peer` says in
  its meaning what its reasoning always said — a link has no direction, and each end records the other — beside the
  `to` a reach and a treatment are directed at. The catalogue had read the two as one domain under two names; they are
  two relations.
- **26.0** (2026-09-28, proposed rule-change) — **one word for one thing, and the law held to its own shape.** MAJOR:
  names a garden writes change, and a garden crosses by `bin/dmupgrade.py`, which translates them. Found by the
  catalogue of the language (`bin/dmcatalog.py --findings`), and by a garden another maker's agent wrote, which showed
  where a cold writer had to improvise.
  - **`identifier`.** Thirteen terms — `person_id`, `contract_id`, `event_id`, `session_id`, `program_id`,
    `design_id`, `doc_id`, `service_id`, `org_id`, `product_id`, `manifest_id`, `instance_id`, `emp_id` — each named
    the identity given to one genos, and a new genos needed a new term. They are one term. A minted name already
    says its genos (`person:sam`), and must now say the bean's own; an assigned id says its home by how it is
    written; an issued one carries `issuer`. A genos may narrow the forms (`gene[].identifier_forms`): a person's is
    minted or issued, never a bare number someone assigned, and a session's is minted. Whether an identifier
    establishes is the bean's to say, as it already was for a document's and a manifest's; each nature's minimum of
    establishing anchors still holds.
  - **`permission`.** An attribute that takes a position on an aspect is named after the aspect, and the gate checks
    it on every term. `feasibility`, `necessity` and `confidentiality` already were; the aspect `capability` was
    taken as `permission` by three terms and `stance` by two. The aspect is `permission`, and so is the attribute.
  - **`to`.** A reach's far end was `target`, and a treatment's and a clause's were `to`. It is `to`; a link's
    `peer`, which has no direction, stays.
  - **`term_form`.** A term holds what the term record declares and nothing else. Twenty-nine keys no tool read —
    notes, forms written out, handling, directives — moved to the reasoning, under each term's path; four
    `canonical` restated their schema's `canonical_note` and went; `ip`'s became its `canonical_note`; `os` and
    `git_remote` took what a writer needs into their `meaning`. Three registry rows' prose went the same way.
  - **`registry_forms`.** Every registry declares its columns, each required or optional, and every row keeps them —
    the law's, a profile's and a garden's alike. A column that names rows of another registry says so there, with
    `acyclic`, `rooted` and its `why`: `registry_links` is folded into it. A protocol's `technology` is optional, so a
    protocol no catalogue lists (a vendor's own) is written without inventing one.
  - **A bean with no provenance is an error**, as one whose provenance lacks `src` already was: a fact that cannot
    say who said it is not a fact.
  - **`verbs` and `tool_families`.** One entry to every tool, `bin/daftar.py <verb>`: each verb and the family of what
    it is for (law, gate, write, read, measure, between, launch) are rows of the law, and the gate holds that each verb
    names a tool the garden holds. The tools stay where every command names them; the entry groups them.
  - Retired, each saying where it went: the thirteen id terms, `capability` (aspect), `stance` and `target`
    (attributes).
- **25.1** (2026-09-27, proposed rule-change) — **a private page shows its addresses.** MINOR, additive: `view.visibility`,
  `public` or `private`, absent meaning public, so a page that says nothing stays as it was. A public page is one that
  may be published, and no drawing on it shows an address: the rule was made for that, and 25.0 applied it to every
  page. A private page is read only by the viewers its host signs in, and a network map read there needs its
  addresses. At the understand lens each part shows its own in its box, the one the page's `reference` chooses
  from the being's own record, and the host sends it only to a viewer who may see that being, as it already filters
  the cards; a drawing's own text may carry addresses too (a segment's range, an egress line, a word's definition),
  which every viewer of that drawing sees; `dmview check` names an address that fits nowhere in its box. The understand
  lens's row says so.

- **25.0** (2026-09-27, proposed rule-change) — **what runs is authenticated, and code is the gardener's.** A
  release a garden upgrades to is checked before any of it runs: a signed tag against the keys the garden's own release
  names, `seed/RELEASE-SIGNERS`, which the law places in `law` beside what a release ships (`bin/dmupgrade.py`,
  `--expect <commit>` for a person who checked the commit, a confirmation at a terminal otherwise). A hub asks
  `ratify:G` for a change to code — a file of the `gate` layer, one a release keeps, a Python or shell file, the
  drawing module a page names — and takes a commit with no parent only when it is empty (MODEL.md). The git merge
  driver merges three ways (MERGE.md §8): what one branch changed or removed since the base and the other left stands,
  and only a position both changed differently is a disagreement. Special-category material a commit adds unsealed is
  refused, not warned: no seal made after the commit takes the value back (MODEL.md). An agreement's grant decides over
  its own bean and what a party who accepted it owns or is the record of, and opens nothing else (`grants`,
  `dmpass.shares`). The `version` order absorbs a release only into one that goes on at a component's boundary: `9`
  and `90` are two releases, a disagreement, where they merged into `90` unseen. A reading's step names a registry's
  row where the law says so — a `group`'s `system` is a time system of `anchor_systems`, read through the calendar its
  row carries — and `gregory`, which the cookbook wrote, is refused, naming `gregorian-civil`. `shared_identifiers` is a
  term (MINOR on its own): the `ip` term's escape named it and the gate refused it as undeclared, and a reused private
  range is told apart by each bean's `located_at` in `network-segment`, where it was an undeclared `scope`. A pass the
  save traces carries `distinct` beside `quoted` (`pass_metadata`): how many finds named one thing, so a person's words
  credited by a short word alone say the attribution is weak. The law's documents say what the law says: MODEL.md
  names `stated-in-document` and `courses`, MERGE.md the source order as it is derived; two `agent_directive`s state
  rules rather than address an agent; the versions, dates, measurements of one estate and incidents that twenty-six
  `meaning`s and `why`s carried are in seed/RATIONALE.md under each item's path, and `this garden` and `the operator`
  are said as any garden reads them, so the story bin/dmreview.py `story_in` finds in the law is none where v0.38.0
  shipped 56 (a `prediction`'s reason, one estate's expectation, is counted apart and is unchanged). The `ip` term's
  `authority`, which nothing read, is gone. And the note on the gap after 1.0 said git holds the four releases this file lacks; it
  does not: this repository's history begins on 2026-09-17 with the law at 8.2, so the gap stays a gap. MAJOR, because
  a garden that upgraded unasked from a network is now asked, and a writer's push a hub took, and a commit carrying a
  special value the gate warned of, are now refused.

- **24.0** (2026-09-26, human-ratified rule-change, parts ratified one by one as the release was built) — **the law
  learns quantities, reckoning, privacy, agreements, observations, place in time, where a fact came from, and one
  sense per name.** MAJOR. A quantity holds `count`, `unit` and one of `u` or `accuracy`, and nothing else (Q-3, D17);
  a sequence has `courses` and `series.placement`; forty-four reckoning operations with `mechanism_form`,
  `coefficient_form`, `pin_form` and `weighings`, run by `bin/dmreckon.py`. Privacy: `sensitivity` is derived, never
  said; the `held` layer keeps what may not be committed (`held_form`, `bin/dmheld.py`); a person who is not the
  gardener, not a peered gardener and not an accepted party carries `consent` (F2, the export policy on a person's
  root); `about`, `grants` and `dmpass.may`; an `emp_id` issued by an organisation names its issuer (N17). Agreements:
  a clause's `when` is a reading or `{said: <words>}`, never bare prose (N6); `falls_due.at`, `within`, `used_by`,
  `bin/dmacross.py`; `provenance_record.via` between gardens, a loop refused. Observations and hearings with
  `knowledge_scheme_form`, one finder over every scheme. Place and time fused: `datum`, `cells_in`, `boundaries_in`,
  `overlay`, the ICS chart and its GSSPs, `fixing`, `mobility`, place read at a moment. The `origin` facet: a fact's
  source is an act `{act, nature?, by?}`, the rank derived. The flow law: thirty-five closed rows, pointers checked at
  commit, the journal append-only in fact; `bin/dmlaunch.py`, `bin/dmhook.py`; the view host asks `dmpass.may` before
  every page, table, action and write. A step may carry only the keys the term `steps` declares (N11), and `note` is
  one of them, as 10.1 said it was: a record-like entry — a step and its ways on, a capability, a dependency, a
  weighing and its pairs, a move, a fix, a role, a volume, a grant, an endpoint, a link, a hearing's statements and
  ruling, a payment's parties and settlements, and 14 more — takes a `note`, so a remark never needs a key of its own.
  `senses`: a name has one sense across the law, and a garden judges its own findings in VOCAB.md. A comment in the
  law's front matter is refused (§9k) and moved to the garden's reasons. Crosswalks to FHIR R5 and Darwin Core. The
  fact tables and the FHIR crosswalk are CC0 1.0; the time zones are tzdb 2026d, public domain. MAJOR because every
  one of N6, Q-3, N11, F2, N17, §9k and `senses` refuses a bean the law before it accepted. `bin/dmupgrade.py`
  translates a clause's prose `when` into `{said:}`, byte for byte where it was quoted, and moves §9k comments; it
  LISTS, and moves nothing of, a quantity with other keys, a step with an undeclared key, a person without consent, an
  `emp_id` without issuer, and a name with a second sense, because each is a person's to settle.

- **23.1** (2026-09-25, a minor rule-change: the first body of the Leviathan, whose design the operator ratified) — **The
  layer map.** The law gains `layers`: where material sits and what stands on what. Five of its rows are daftar's own
  words, each on the one beneath (`beneath`): the manifesto, the law, the reasoning, the journal, the history; beside
  them the queue (`log/pending.md`, edited in place), the guide, the estate, the gate, and the places a garden fills
  itself (a person's words, an agent's work); and the places material comes from or goes to that are no file
  (instructions, the world, the clock, a model's own output, a request, a remote party, a public repository, another
  garden). `holds` places what every garden has, by patterns matched as `seed/LANGUAGE`'s are and case by case on
  every platform; no harness path is written into the law. The gate refuses a map it cannot read (a malformed row, a
  chain with two tops), a file two of the law's rows hold, and a garden's own rows added to the map.
  `standing` is promoted from a garden's own terms: it places what the law does not. The gate refuses an entry that
  places a file the law places elsewhere, a file two entries place in two layers, a doc not written in the one form a
  path takes here, and a doc naming a file the garden does not hold. A file in no layer is counted and shown by
  `bin/dmpass.py`, never refused.
  The RULE-CHANGE duty keeps what it had — every file a release ships, and VOCAB.md, GARDEN.md and the law — and gains
  what a garden places in `law` or `manifesto`, a pattern entry included, and the move of such an entry itself.
  The changelog leaves the law file for `seed/CHANGELOG.md`: it is journal, not law.
  A garden crossing into 23.1 drops its own `standing` term, the vacancy it declared on it, and any entry of its own
  that the law now places otherwise, each named, with its key, on the upgrade's `translated:` line; an entry that
  would take a garden's own file out of its law, and a garden term stricter than the law's, are left for a person.
  A garden's own term that states again something a standard term states is WARNED of: it replaces the standard's
  there, key by key. Making that a refusal is a major change, for a person to ratify. A garden's `journal.path` in
  VOCAB.md is warned of too: no tool reads it.

- **23.0** (2026-09-24, human-ratified rule-change) — **a day nobody said has its form, and the day of writing is the
  clock's.** MAJOR: a commit that passed under 22.0 can be refused. TWO CHANGES, ratified together by the operator
  ("Ratified and beautiful have them in the current pr"), after a local model recording four conversations in which
  nobody said a day wrote 121 days across 18 runs — each the nearest date in view — and five runs read past the gate's
  warning on the form a day nobody said takes. `anchor_systems` vacancy `event-anchored`: `reason: prediction` ->
  `universal` — the form every garden needs for a happening whose day nobody said, declared whole with the calendar
  positions `timing.system` occupies; a garden standing on it is no longer warned (the MINOR half: nothing that passed
  stops passing). `provenance_record.as_of: stamped` — the day of writing is the day of a journal heading the same
  commit adds, read from the clock and never typed, written `now` and stamped in its place by the tool that stamps the
  heading; GATE: a provenance record a commit ADDS whose `as_of` is not the day of a heading it adds (one it did not
  already hold) is refused, and so is one with no `as_of`, and a `now` left unstamped in any stamp position. A record
  is matched by what it is — (src, by, as_of) — not by where it sits, so a record moved into a conflict, out of one or
  to a renamed bean is not added; a record carrying ANOTHER garden's `garden` keeps that garden's stamp (this garden's
  own id is no exemption); the merge engine's own record (`src: generated-by-tool, by: dmmerge`) says `merged`; a
  garden's first commit is exempt as before. The journal tool, the save and `dmpropose take` stamp before they write
  the entry, and only the documents the entry names.
  No bean already committed changes: `bin/dmupgrade.py` moves the pins. With the release (not law): the forms are
  derived from the cookbook by the law — a said date shown empty with its meaning, `as_of: now`, no day in an anchor.

- **22.0** (2026-09-24, human-ratified rule-change) — **the law says what a being is in one tongue: its Greek.**
  MAJOR: every bean changes. The words for what a being is came from four traditions, and one misused its own — in
  Aristotle, metaphysics studies every being, not the ones that are not physical. RENAMED: the crown's root `god` ->
  `theos` and its branches `nature` -> `physis`, `logos` kept, `love` -> `agape`; the natures `physical` -> `soma`,
  `metaphysical` -> `lekton`, `living` -> `empsychon`, their meanings said in the Greek words and unchanged in
  substance; a bean's `kind:` -> `genos:`, the registry `kinds` -> `gene`, each row `- genos: <name>`, and a garden's
  `local_kinds` -> `local_gene`; the schema constructs `required_on_kinds` -> `required_on_gene`, `only_on_kinds` ->
  `only_on_gene`, `must_equal_kind_attr` -> `must_equal_genos_attr`, `entry_form_from_kind_attr` ->
  `entry_form_from_genos_attr`, and `bean_id`'s `kinds` -> `gene`; `identity_policy.minted.form_kind: kinds` ->
  `form_genos: gene` — a minted name is still written `<genos>:<name>`, and no value a garden minted changes. KEPT:
  the bean attribute `nature`, the registry `natures` and a genos's `of_nature`; and a mapping's `kind`, which names no
  being — a `kind` term says so, beside the new `genos` term. `retired` names every old word with the one that took its
  place, so a refusal says where it went. GATE CHANGES: a key retired on a bean is refused on a bean even where another
  document still declares it (`kind`, a mapping's); a nature, a crown branch or a genos's `of_nature` in a retired word
  is refused naming its Greek one; a garden's VOCAB.md still carrying `local_kinds`, a `kinds` registry restated or
  added to, or `form_kind`, is refused naming where it went, never left unread; `in: { bean_id: … }` takes `gene` and
  nothing else; `required_on_<registry>` and `only_on_<registry>` read their axis from the field the registry's rows
  are named by, since γένη is not γένος with an `s`. With the release: `bin/dmupgrade.py` translates a garden crossing
  into 22.0 — in every bean its `kind`, its `nature` and the crown branch its ownership ends in; in VOCAB.md
  `local_kinds`, a restated or added `kinds` and their rows, the schema keys and `bean_id` of its own terms, a
  registry or a nature they name, and a vacancy at a renamed position; in the garden's own RATIONALE.md, a heading
  keyed by a path VOCAB.md renamed — each found by the YAML node that holds it, comments and prose untouched, each
  document proved to parse to exactly the old one renamed, and all of it reported on the journal entry's
  `translated:` line; a mapping keeps its `kind`. Run again in a garden that crossed already, it translates what came
  in since still in 21.0's words — a bean added on a branch or a clone still at 21.0 — and its entry asks nothing; the
  git merge driver reads each side of a bean (never a mapping) in the words of the law its tree runs; and a garden's
  own code is never translated — each file of it that says a retired word is named on the `translated:` line.
  Germinate plants the gardener in the new words and takes
  `--gardener-genos` (`--gardener-kind` still read), as `bin/dmupgrade.py` takes `--gardener-genos` and
  `DAFTAR_GARDENER_GENOS` (the old names still read); every tool reads and writes `genos`, `gene` and the Greek
  natures, and a merge's seed carries its `genos`. The reasons, and every option that was put to the operator — the
  one taken, and why — are in seed/RATIONALE.md under `natures`. The suites that hold it: test/upgrade.py (a 21.0
  garden translated and passing its gate; a branch still at 21.0 merged into it, and what it brought translated),
  test/refusals.py and test/germinate.py (every retired word refused, naming its Greek one).
- **21.0** (2026-09-23, proposed rule-change) — **what passes between: persons, and gardens.** MAJOR. Until now the
  language described one gardener's world. The first garden kept by someone who had not written the language needed
  what it could not say: money, an agreement between two people, the person who keeps the garden, and a thing two
  gardens share — so its agreements sat in free keys under `details`, the person who keeps it appeared in it only as
  an outside party in prose, and a merge of it against a copy of itself saw two records as four. BETWEEN PERSONS: a
  `money` dimension and quantity whose units are the currencies Unicode CLDR publishes (`currencies`, a registry
  file), with no factor between two of them — a rate is an observation, never a law — and a count held to the
  currency's decimal places; a `ratio` quantity; an agreement as structure — `parties` (each with the day it
  accepted, or no acceptance on record: an offer is not an acceptance; merged party by party, so a difference about
  one party stays on that party), `words` (written, spoken or not yet put into words, and where), `clauses` (each a
  position on the `capability` square, with amount, due day, recurrence and condition, and `expiry` per entry that
  `unless` silences once met) and `transactions` (what moved, on which `day`, who paid, who bears it in whole
  shares, their parts summing exactly to the whole through the new schema construct `sums`, and each party named
  once among the payers and once among the bearers through the new `keyed_by`, their order carrying nothing). A
  count or a share is what was written: plain decimal digits, bounded in number so every reader holds them exactly;
  the loader reads a plain scalar as an integer only in plain decimal, so YAML 1.1's octal, hexadecimal, binary,
  sexagesimal and underscore spellings (`010`, `0x64`, `1:30`) are refused, never read as another amount. A day a
  calendar reckoned by rule does not have (`2026-02-30`, a thirtieth of a twenty-nine-day month) is refused, never
  moved. A balance is read from them, never stored, so `balance` is retired. `contract` names `ownership_form:
  [crown]`: it may end at the crown and be answered for by its `parties`, owned by none of them — or be owned by its
  author, as before. `document` and `event` are kinds, identified by `content_hash` and `event_id`, and a happening
  between people may end at the crown too, answered for by whoever hosted it. `recurrence_form.times` counts
  instalments. BETWEEN GARDENS: the manifest is judged as itself (`manifest`): each attribute in its form, the
  required ones present, `daftar_release` a release tag or `untagged <commit | unknown>`, and its `gardener` a bean the garden
  holds, of a kind the manifest admits — a person or an organisation; a garden grown to rehearse says so in `test`; a
  garden is a being (`garden`, anchored by `garden_id`: the commit it germinated from, which no one assigns and every
  clone shares), and the receiving garden marks one it knows to be a rehearsal with `test`, its own record, whatever
  that garden's proposals say; the anchor terms whose values a garden mints say `minted: true`, and
  `identity_policy.minted` gives a minted name its form, `<kind>:<name>`, and qualifies it by the garden that gave it
  (`<garden_id>/<kind>:<name>`), so equal bare names from two gardens are candidates and never fused — while a value
  of such a term in any other form (a package's name, a registry number, an invitation's UID) was assigned outside
  every garden, fuses as every anchor does, and is refused qualified; `provenance_record` declares the record every
  fact carries, `from` and `garden` included. AND: the ownership facets are a registry whose `depends_on` walk is
  checked acyclic and reaches `legal`, with `experience` and `financial` beside `legal` and `technical`;
  `entry_form_from_kind_attr` reads a list, which allows a form where one names pins it; `retired` lists what the law
  took back, so a refusal says where it went — the anchor attribute `scope` (said by the term and the name's own form
  now), `between`, `agreement_ref`, `conflict_rule`, `balance`, `attributes` (into `details`), the `facets` term,
  `values_consistent_with`, and the manifest's `seeds_from`, `created` and `models`; the Tier-0 vacancy
  `located_at.openness = unknown` is withdrawn, occupied by a real bean; and the positions 21.0 adds that no garden
  uses yet are declared vacant, `universal`. GATE CHANGES: a key YAML does not read as text — `on`, `off`, `yes`,
  `no`, a bare number — is refused, never crashed on (the transactions attribute is `day` for that reason); what the
  gate cannot read it refuses, saying where, never with a traceback; a local term named for a retired one says where
  it went; a `garden` bean anchored by this garden's own id is refused; a journal line a commit adds holding a
  character some reader takes for a line break is refused, so no line can carry a heading nobody stamped. With the
  release: gardens meet by proposal (`bin/dmpropose.py`: a garden's first contact with another, a fingerprint that
  detects damage and is not a signature, a proposal taken once, every record stamped with the garden it was made in
  so that no garden speaks as another, and taking an agreement in never its acceptance, which is the receiving
  gardener's own word); a merge compares one fact written two ways as one value (a count in its shortest exact
  decimal, a keyed list in its key's order); what is owed is read (`bin/dmledger.py`), `bin/dmstale.py` warns before
  each clause falls due, and `bin/dmunits.py` converts between two currencies only at a rate passed in (`--rate`);
  germination writes a random seed into the first commit, so two gardens grown alike are two, and plants the
  gardener — a person, or with `--gardener-kind org` an organisation — qualified at birth, and a rehearsal is grown,
  never cloned; `bin/dmupgrade.py` carries a garden into 21.0 and names its gardener (`DAFTAR_GARDENER` where the
  garden's own tool is older than `--gardener`); the hooks choose a Python that imports yaml; the tools write UTF-8
  on every platform, `bin/dmjournal.py` included, which reads a body on standard input as UTF-8, refuses every control
  character but a tab, and prints the heading only once it is written; no command a tool prints or a page gives joins
  two with `&&` or removes files with `rm`, a path holding a space is quoted, and a body or a block goes in with
  `--body` or `--block` — so each runs in Windows PowerShell 5.1 too, with `python` for `python3`, but where a page or
  a tool's help shows a Unix shell's form (its `<`, its `$(…)`) and gives PowerShell's beside it; and MODEL.md says
  whose a judgment is. AFTER THE LAST REVIEW: TEXT IS TEXT — the law says a value holds no control character (every
  one Unicode names but a tab, and a line feed only where a value may hold lines), the gate refuses one in any key or
  value of a bean, a mapping, GARDEN.md or VOCAB.md, naming where it is and which (`U+001B`), and every message the
  gate, `bin/dmledger.py` and `bin/dmstale.py` print quotes what a bean wrote escaped, so a garden that already holds
  such bytes cannot drive its reader's terminal; a disagreement is left standing only as the merge captures one — a
  record of exactly `{conflict: [<two sides or more>]}`, at a path the bean's `merge_conflicts` names, while
  `merge_open` is set — and any other conflict record is refused by name; a value where the law asks for one position
  (a clause's `stance`) that is a list or a map is refused by name, and a proposal whose scratch gate ends without a
  verdict is not called clean; a bean, a mapping, GARDEN.md or VOCAB.md that is not UTF-8 is refused by name, saying
  what it looks like; each entry of a VOCAB.md block is read in its shape — by the gate for this garden's, by the
  merge for another's — and refused by name where it has another; the reverse gate counts the positions of a closed
  list on an attribute of a mapping-shaped term, and `words.form`'s `written` and `unstated` are declared vacant,
  `universal`; the law says, where it defines a date, that a day its calendar does not have is no date, the gate
  judges it in the calendars the law marks as reckoned by rule, and `bin/dmrules.py` prints it; the manifest's
  `policy` has the shape its meaning says: rules, in prose. Between gardens: `dmledger --between` names each shared
  agreement it left out of the net and why, and calls the net partial when it left one out; an entry that carries its
  own provenance goes back to the garden it came from and reads clean, however often it crosses — and a value both
  gardens changed at once reads as a disagreement, never a forgery; each recurrence is walked within its own allowance,
  and every recurrence of a run within one budget, a clause beyond either named as not walked and the run of dmstale
  then exiting 1, so no clause can hide another's due day; a proposal's records are stamped whichever way their keys
  are written (JSON's `"provenance":` too); a YAML set is refused as no shape a garden writes; a clause that does not
  repeat is shown due in the calendar it was written in; `make` says a party in a merge conflict is a person's to
  settle first; first contact prints each bean once, and an organisation's bean in the law's form for a gardener. The
  tools: germinate judges a garden's name by the law's form before it creates anything, takes `--name` where the
  directory is named otherwise, removes what it made when anything stops it, and grown from inside a garden records
  the release that garden runs; `bin/dmupgrade.py` refuses a garden whose name the release's law refuses before
  touching anything, printing the `garden:` line to write and its RULE-CHANGE entry, and plants an organisation as the
  gardener too (`--gardener-kind org`, `DAFTAR_GARDENER_KIND`); `bin/dmsafe.py` reads a block as UTF-8, or UTF-16 with
  its mark, on every platform, from standard input or from a file with `--block`. The suites that hold it:
  test/money.py (money and agreements), test/mycelium.py (gardens and proposals), test/refusals.py (what the gate
  refuses, and that it refuses rather than crashes), test/journal.py (the journal's one tool, and dmsafe's block),
  test/upgrade.py (a garden into the release, its name and its gardener), and test/germinate.py, which commits the
  cookbook's recipes one at a time, in the order of the page.
  THE LAW UNCHANGED, the tools corrected by what a first real rehearsal met: the fast check reads `captures/` as it
  reads the journal — a record held whole, whose quoted versions are what was said, never the garden stating its
  release; and `dmpropose make` tells a bean with no establishing anchor at all that it has no identity here yet —
  give it one, or name it in words where it is referred to — instead of pointing at `mint`, which has nothing to
  qualify.
- **20.0** (2026-09-22, proposed rule-change) — **a heading is stamped by the clock, not typed; an anchor says how it
  is known the way every fact does.** `journal.heading: stamped`: `bin/dmjournal.py` writes every heading from the
  clock and records it in the clone's git directory, and the gate refuses a heading a commit adds that the tool did
  not write. The form was checked since 10.0; the truth of the moment never was, and a writer typed the time before
  reading it twice in one evening. With the release: `seed/germinate.py` and `bin/install.py` — a garden grows
  on Windows, where `sh` is not a given; the shell scripts hand over to them. And the anchor:
  `anchor_authority` (`scanned < operator-asserted < external`) was a second vocabulary for the one question
  `provenance_src` answers, and the two disagreed on twelve anchors of the first garden. It is retired: an anchor
  carries `provenance: { src, by, as_of }` where its source differs from the bean's, and nothing where it does not
  — the rule every entry has had since MODEL v2. `identity_policy.anchor_attrs` declares what an anchor may
  carry, so a retired or invented attribute is refused with its reason. The merge ranks two records of one
  anchor by `provenance_src`, as it ranks every other value.
- **19.0** (2026-09-22, proposed rule-change) — **an anchor's key is a term, and a virtual machine is a living
  being.** The fourth cold-start drill invented an anchor key and the gate took it; measured, one garden's beans
  carried seventeen keys no term declared, and identity is matched by (key, value), so an open key was an open
  merge key. `identity_policy.anchor_key: term`: every anchor's key names a term that declares `anchor:`, and the
  gate refuses any other. The ids the kinds registry had named in prose since P3 are declared: `product_id`,
  `service_id`, `org_id`, `person_id`, `program_id`, `contract_id`, `design_id`, `doc_id`, `manifest_id`,
  `session_id`, and `email`. `identity_policy.establishing_family: enforced`: an establishing anchor of a confirmed
  bean is of its nature's family, as the registry has said and `dmrules` has printed since P3 — the gate had
  checked only the count. The one bean that broke it was a rented VPS anchored on its name, and the cookbook's
  recipe had the same shape, because a virtual machine has no matter to anchor: `virtual-host`, `of_nature:
  living`, is a running machine-instance that lapses at teardown, as `instance` is; `host` is matter. This is the
  reading the kinds registry foresaw at P3 ("D5 will re-read this as an instance living_on a provider").
  With it, the terms classed before there were natures: `wg_pubkey` and `ssh_key_fingerprint` are logical
  credentials, `mac` establishes only matter, none of the three pins `establishing` — the family decides;
  `anchor_class` decides again and loses `none`; `id` and `ref` carry no anchor block; `shell-log` is retired;
  the living family is `[logical]` (`personal` named a class that never existed); `owned_by` is required on
  every bean; `status` loses `at-risk`, which `risks.state` carries; the kinds rows are their nature and
  meaning, the prose `schema`/`required`/`min_anchors` copies gone; and the promotion notes on terms that are
  the standard are gone with them.
- **18.3** (2026-09-20, proposed rule-change) — **who may reach a surface is a fact of its own.** `endpoints` gains
  `admitted_from` (prose): the named sources a surface admits, beside `exposure`, which says only where it is bound.
  The management-on-the-internet cell becomes `expects: [admitted_from]` instead of `verdict: in_breach`: it warns
  while nothing is said about who may reach the surface and is silent once it is. It can only let a warning stop —
  no entry that passed is refused, and the cell fires on exactly the entries it fired on before. The gate's
  conditional cells (`requires` / `expects`) now take a `when` of more than one attribute, as verdict cells did.
- **18.2** (2026-09-20, proposed rule-change) — **a form a tool already checks is checked by that tool.** A system
  row states its form as a `pattern` or names a check with `checked_by`, never both. `ipv4` and `ipv6` are
  `checked_by: ipaddress-v4 / ipaddress-v6` — the standard library's validator, which the `ip` anchor has always
  used — and their patterns are gone. The form is the library's own spelling, so an address has one: `2001:db8::1`,
  not `2001:DB8::1` and not the exploded form. TIGHTER than 18.1 in that one respect.
- **18.1** (2026-09-20, proposed rule-change) — **nothing is untyped.** `in: { entries: {…} }` — entries INSIDE an
  entry, each judged as an entry by every rule an entry answers to; `in: bean_id`; `in: any`, a decision where `untyped`
  is a debt. `beanger.records` is typed with them and `record_attrs`, a map of sentences nothing read, is gone: a
  record's attributes are attributes. The law now has no `untyped` attribute. TIGHTER, and so able to refuse what
  passed: the `ipv4` row's pattern admitted `256.1.1.1` and `01.2.3.4`, and both rows any prefix length; an octet is
  now 0-255 without a leading zero and a prefix is 0-32 or 0-128. The `ip` anchor always checked this; a position in
  the same system did not.
- **18.0** (2026-09-20, proposed rule-change) — **what was owed.** MAJOR, four things.
  A REGISTRY IS ITS OWN ENUM OWNER: the five terms that only held a copy of a registry's column are gone
  (`anchor_system`, `unit`, `role`, `storage_format`, `net_protocol`) with their drift guards; `nature` and `os` read
  theirs with `values_from: "registry:<name>[].<field>"`. A position in a registry is addressed `registry:<name>`,
  which is where a vacancy for an unused row is declared (`dmupgrade` rewrites a garden's). A garden that adds a row
  states it once, under `registry_additions`.
  A MAPPING IS ONE ENTRY: a term whose value is a mapping is judged by the same controllers as an entry of a list.
  Until now the value scope had its own copies of four of them and none of the rest, so a closed list, a pattern or a
  pointer declared on a mapping's attribute was read by nothing.
  TWO DOMAINS: `in: { system: <anchor system> }`, a position in one named system; `in: { key_of: <term> }`, a key of
  that term's mapping on this bean or `<bean>:<key>` on another. With them twenty-six of the twenty-seven `untyped`
  attributes are typed — dates as dates, stamped moments as `unix-epoch`, a link a surface rides as a key of `links`
  — and a garden whose values were free text in those positions is told so. One remains, `beanger.records`.
  NO CALENDAR IS THE ONE TIME IS READ IN: the `instant` order holds between readings in any declared calendar, asked
  at the day, and across two calendars only when both begin their day at the same moment. A journal heading is a
  position in any declared calendar, in that calendar's own form, to the minute and with its offset; the journal's
  copy of one calendar's pattern is gone (`journal.system` names one for a garden that wants one).
- **17.0** (2026-09-20, proposed rule-change) — **quantities.** MAJOR: a `units` row names its `quantity` and its
  `factor` instead of a `dimension`, so a garden that added a unit restates it. A QUANTITY is a product of powers of
  base `dimensions`: duration is time, area is length squared, SPEED is length per time, ACCELERATION is length per
  time squared, a data rate is information per time. `in: { quantity: <name> }` types an attribute as a measured value
  `{ count, unit }`, and the unit must measure that quantity. An extent's measure may now be an AREA or a VOLUME: it
  spans as many lines as its unit has powers of the metered dimension, and never more than the system has (`geographic`
  has three; `time` has one, so there are no square seconds). `level` and `attenuation` are LOGARITHMIC quantities —
  decibels, and decibels per metre — whose values add where the ratios they stand for multiply. `bin/dmunits.py`
  converts within a quantity by exact rational factors and refuses across quantities.
  EXACTNESS IS A RULE, not a habit of the tool: a `factor` is two positive whole numbers in lowest terms and the gate
  refuses anything else; a `count` is a whole number or a decimal string, never a float; a conversion is printed in full
  or as a fraction of whole numbers, never rounded; and a conversion is a READING — a bean keeps the value in the unit
  it was measured in, so no chain of conversions can accumulate an error.
