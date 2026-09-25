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
