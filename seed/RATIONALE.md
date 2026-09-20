---
rationale_for: seed/std-vocab.md
---
# daftar — why the law says what it says

LAWS are clear and brief, there for usability and efficiency. REASONING — this document — is their backbone: why a law
is the way it is, the argument for a design, what was considered and refused. JOURNALS are the leads reasoning is drawn
from, and HISTORY is the exact record of events the journals are written from. Each layer points down to the next.

Every section here is keyed by the PATH of the law item it supports, so the two are related without either containing the
other. `python3 bin/dmwhy.py <path or name>` reads them together. A key that names nothing in the law is an error
(`test/rationale.py`): a reason cannot outlive its law unnoticed.

Much of what follows arrived verbatim from comments that once sat inside the law, and still mixes reasoning with journal
and history — a date, who found what. Sorting that is editorial work that can now be done here, where it cannot change
what the gate reads.

## schema_language

TIER-0 UNIVERSAL STANDARD VOCABULARY — portable, estate-agnostic classification carried BY THE SKILL.
Gardens pin a version via `extends: std-vocab@<version>` (VOCAB.md / GARDEN.md) — the `version:` key two
lines above is the one that governs, and the gate ERRORS if a pin disagrees with it.
Changes are governed by the PROMOTION PROTOCOL (SKILL.md): human-ratified rule-changes, semver —
additive term = MINOR bump; changed handling/merge/anchor rule = MAJOR (can retroactively re-classify).
Each term declares: meaning · context_keys · anchor{class,establishing} · merge{cardinality,order,authority}
· canonical (normalizer) · escape · exceptions(dated case-law).
== THE SCHEMA LANGUAGE (added 2026-08-02, P2 / plan D4, human-ratified rule-change) ==
INVARIANT SERVED: "type rules live in the VOCAB, not in code." bin/dmcheck.py is now a fixed CORE
(front-matter shape, id==filename, kebab, provenance, anchors + establishing dedup, ip dedup, DAG,
link integrity, journal<->commit binding) plus ONE generic loop that enforces every term from the
`schema:` block below. There are NO per-term blocks in the gate. To change a type rule, edit the
schema here — that is a human-ratified rule-change — and the gate follows without a code edit.
A term with no `schema:` is documentation only; the gate never enforces it on beans.

## schema_language.attr_domains

WHAT `in:` MAY SAY. Every attribute is a position in EXACTLY ONE domain,
so `in:` is one thing, and it is never absent.

## crown

== NATURES: the root axiom layer (added 2026-08-02, P3 / plan D1, human-ratified rule-change) ==
`nature` is the ROOT of the type system and `kind` is a REFINEMENT of it, not a parallel taxonomy.
Every bean carries a nature; every kind below declares the `of_nature` it refines; the gate holds the
two equal. Policy that used to be stated per kind (anchor family, minimum anchors) attaches HERE, so a
new kind inherits a coherent identity policy for free and may override only if it truly differs.
The crown itself is a MODEL axiom (MODEL.md Ownership), never instantiated as beans.
== THE CROWN (added 2026-08-02, P7b, human-ratified) ==
MODEL §Ownership states the axiom in prose; this makes it NAMEABLE in data without instantiating it as
beans. These are the TERMINI every ownership chain resolves to. A bean names its branch directly only
where ownership does not pass through another being — in practice, persons. Everything else chains up
through a person or an org and terminates here transitively.
The branch a bean may name is fixed by its nature (natures[].crown owns that mapping — not restated here).

## identity_policy

NB the crown OWNS but never ANSWERS. Responsibility has no crown form: a duty must land on a being
that can be asked, so responsibility always terminates in a bean (or, for a person, in themselves).

P3/D1: identity policy attaches to the ROOT AXIS...

## identity_policy.keyed_by

...this bean field selects the policy row...

## identity_policy.registry

...from this registry...

## identity_policy.applies_at_identity_status

...and the minimum bites once identity is confirmed.

## natures[physical].crown

Extension owns physical beings

## natures[physical].establishing_anchor_family

serial / mac / wg_pubkey — bound to the matter itself

## natures[physical].min_establishing_anchors

required once identity.status is `confirmed`

## natures[metaphysical].crown

Thought owns metaphysical beings

## natures[metaphysical].establishing_anchor_family

url / fqdn / git remote / manifest or doc id

## natures[living].crown

life-bounded ownership; lapses at teardown

## bodies

== ANCHOR SYSTEMS: the systems a POSITION may be stated in (added 5.1, human-ratified rule-change) ==
A POSITION IS NEVER BARE. `iso_date` hardcodes ONE anchor system — the Gregorian calendar — as though it
were time itself; an absolute path hardcodes ONE — a particular host's filesystem — as though it were
place. It is the same defect twice, and it cost this estate a session each time: a commit declared to
exist on NO branch and NOT on disk (true of the machine searched, false of the estate), and one analysis
reported FRESH on one host and STALE on another the same minute.
DIMENSION-SPANNING ON PURPOSE. Time and place are the same structure with different direction lines, so
they share ONE registry rather than each minting its own. A system declares the dimension it positions
in, and whether a position there ESTABLISHES the location or merely CORROBORATES it — the same split
identity anchors already use, for the same reason: a value that migrates cannot fix what you are at.
EACH SYSTEM OWNS ITS ONE FORM, so no bean, tool or session invents a second spelling. That is not
tidiness: `staleness_key` alone already carries four unowned spellings (`git-head:`, `git-commit:`,
`digest:`, `manual:`), which is how one analysis acquired two verdicts. A system whose addresses have NO
canonical form says so with `pattern: none` and a reason — the same explicit-absence rule `enforced_by`
already applies to terms, because an unstated pattern and a deliberately absent one must not look alike.
THE REGISTRY IS OPEN. A new system is a VOCABULARY edit and never a code edit: the gate reads `pattern`
generically through `entry_pattern_from_registry` and names no system, exactly as it names no term.
== A SYSTEM KNOWS ITS OWN SHAPE ==
The `place` aspect has always confessed that it cannot describe its systems: "lines: open … metered: none — the
aspect claims no measure it cannot give every system". The operator said where the answer lives on 2026-08-05:
a position is "a position in a SUBASPECT which here is not always linear". A system row may therefore state —
levels            the resolutions a position may be HELD to, coarse -> fine: a named list, or a counted range
`{ by, from, to }`. A level is METRIC when it names a `units` row: a day is, A MONTH IS NOT,
which is why `units` never held month — it was always a level and never a measure. Levels are
what the imported trees of knowledge arrived with (broad / narrow / detailed), what a calendar
is (year … millisecond), what a network design is (core / distribution / access; an OSPF area),
and what a map is (country … neighbourhood). Holding a position at a COARSER level is always
honest; a finer one is never inferred.
within            a position here is only meaningful INSIDE a position of one of those systems (a port within an
address; a postal code within a country).
resolves_through  reading a position here needs one there (civil time through geography).
neighbours        `counted` | `metered` | `none`: whether positions have a neighbour relation at all. It is what
a routing protocol computes over, and what makes "every 10th release" sayable with no meter.
restrictions      its own `lines`, `metered`, `order`, `ends` — NARROWING its aspect's, never widening them.
same_ground_as    this system PARTITIONS THE SAME GROUND as those: two calendars over one line of days, a
postal layer and an administrative tree over one territory, two classifications of one world of
work. `crosswalk` says how a position in one is found in another: `computed` (by rule),
`table` (somebody publishes the correspondence), `observed` (it is looked up in what was seen),
`none`. Neither system is the other's parent; that is what distinguishes this from `within`.
example           one position in the system's form. The gate holds it to the system's own pattern, so the form
a reader is shown is one the gate accepts.
THE GATE CHECKS THE SHAPE, not its use: that what a row names exists, that `within` and `resolves_through` never
loop, that a metric level names a real unit, that a restriction is one the figure offers and does not widen the
aspect's. The consumers are extents and recurrences, which ask the SYSTEM what it permits as they ask the aspect
today. `system_registries` names the registries whose rows are systems, so the gate names none.
== WHERE, BY COORDINATES: bodies and coordinate reference systems ==
ISO 19111 and ISO 19112 divide spatial referencing in two, and this law follows them. BY COORDINATES: numbers in a
COORDINATE REFERENCE SYSTEM — a datum fixed to a BODY, axes, units. BY IDENTIFIER: a name somebody maintains — a
street address, a postal code, an administrative code, a map database's element id, a grid cell's code. The first is
THE ROOT: every identifier RESOLVES THROUGH a coordinate position and none of them IS one. A map database is
somebody else's truth (ground rule 3) — useful, re-drawn without notice, and never what a place is anchored to.
"THE THIRD FLOOR" is neither: it is a position in a frame that TRAVELS WITH ITS BUILDING (an engineering frame), and
confusing it with a fixed coordinate is how a room acquires a latitude.

A BODY IS PART OF THE POSITION. A latitude is a latitude ON something. `bodies` is open: the Moon and Mars are here
because reference systems for them are published (the IAU's), and the machinery is the same on any of them.

## reference_system_kinds

THE REGISTRY IS A SAMPLE, NOT THE LIST. There are several thousand published reference systems, and ANY
`<authority>:<code>` is a legal position: the authorities' own registries (EPSG for the Earth, IAU_2015 for other
bodies) are the owners of that enum, and copying them here would be a stale second copy within the year. The rows
below are the ones whose SHAPE this law states, so a tool can read them, and one of each `kind` ISO 19111 names.
`frame` is the distinction that matters most and is met least: a STATIC frame is fixed to a tectonic plate, so a
point on the ground keeps its coordinates; a DYNAMIC frame is fixed to the whole Earth, so the ground DRIFTS in it
by centimetres a year, and a coordinate is complete only with the EPOCH it was measured at (`@2026.72`).

## system_shape

THE WORDS A SYSTEM'S SHAPE MAY USE, declared so the gate carries no copy of them.

## anchor_systems[unix-filesystem].levels

a tree of any depth; a position is held to whatever depth it is written at

## anchor_systems[git-object-graph].neighbours

parent and child commits: a history is walked, never measured

## anchor_systems[gregorian-civil]

== A CALENDAR IS NOT TIME ==
It is ONE PARTITION of the line of days into named cells — years, months — and there are many. "The 15th of every month" has no
meaning until it says WHOSE month: the 15th of a Solar Hijri month and of a Gregorian month are different
repetitions over the same line, and a lunar Hijri month drifts against both by eleven days a year. So a LEVEL
BELONGS TO ITS SYSTEM, and whatever says "each month" names the calendar.

EVERY CALENDAR HERE PARTITIONS THE SAME LINE (`same_ground_as`), and they all meet at one level, THE DAY.
Conversion is therefore calendar -> day -> calendar, and `bin/dmcal.py` does it for every calendar that reckons
BY RULE. Not all do, and `reckoning` says which: `arithmetic` (a rule gives every date), `astronomical` (computed
from the sky for a meridian), `observational` (a month begins when the moon is SEEN), `tabulated` (an authority
publishes it). For the last three a position is converted by looking it up, never by arithmetic, and the tool
REFUSES rather than approximates — a date silently wrong by a day is worse than no date.

`day_begins` is `midnight` or `sunset`: the Hebrew and the Hijri day begins at sunset, so an EVENING position in
one of them falls on the previous civil day. `calendar` is the identifier Unicode CLDR publishes (BCP 47 `ca`),
which is where this list comes from — all eighteen of CLDR's, and the Julian calendar, which CLDR leaves out and
which the Coptic, Ethiopic and Hijri epochs are all stated in.

NO CALENDAR IS PRIVILEGED. A garden states a moment in the calendar it was KNOWN in — a document dated ۲۲ شهریور
۱۴۰۵ is recorded `persian:1405-06-22`, not silently turned into somebody else's date — and what makes two positions
in two calendars comparable is the DAY they both fall on, reached by rule where the calendar has one.
`bin/dmcal.py` is dependency-free on purpose: a conversion that needs a package fetched over a network is a build
that fails at the worst possible moment.
ONE FORM MEANS ONE SET OF DIGITS. A pattern's `\d` matches every script's digits, so the law's patterns are matched
ASCII-ONLY: a position is WRITTEN in ASCII digits whatever calendar it is in, and the digits a reader sees are a
matter for whatever shows it to them.
EVERY DATED ATTRIBUTE OF THE STANDARD IS TYPED `date`: a day in ANY calendar, held to that calendar's own form.
WHAT STILL READS ONLY THE GREGORIAN CALENDAR, named because 16.0 does not fix it: `leaf_orders.instant` (the merge
absorbs a coarser reading into a finer one only within it) and the journal's heading form. Each is a Gregorian-only
READER, not a rule that time is Gregorian.
THE FORM IS TAGGED — `persian:1405-06-29` — because `1405-06-29` is ALSO a Gregorian date, in the year 1405.
One form per system; and between calendars, forms that cannot be mistaken for each other.

## anchor_systems[geographic].restrictions

the one place system with a measure: what "every 5 metres" needs

## anchor_systems[event-anchored].neighbours

positioned ONLY by neighbours — and so countable: "every 10th release"

## anchor_systems[ipv4]

== ADDRESSES AND PORTS ARE PLACES — what 6.0 made a separate registry, and why it came home ==
6.0 gave ipv4 and ipv6 their own registry, `address_systems`, with `dimension: address`, because "where a being
IS" and "where it ANSWERS" are two questions: a mail server can be bare metal in a room and answer at
203.0.113.10, an address it does not even hold locally. The questions ARE two. But that is a difference in the
RELATION between a being and a position, and this law carries relations as TERMS — `located_at` (is found at)
and `endpoints` (answers at) — exactly as `observed`, `as_of`, `expires` and `created` are four relations to ONE
dimension of time. Nobody minted a dimension "expiry-time".

And `address` was a dimension NO ASPECT HELD. Every sequence aspect names the dimension whose systems it holds
(`time`, `place`); none named `address`, so these two systems belonged to no figure — nothing said how they are
ordered or whether a region of one is possible. Meanwhile the law had already described them as a place:
`leaf_orders.cidr` is a CONTAINMENT order ("absorbed by a network that contains it"), partial, acyclic, bounded
by /0 and /32 — `place`'s restrictions one for one — and the ipv4 row says of a prefix that it "narrows a
position". A path and a git object id are both `place` and are independent of each other in just the way an
address and a network segment are. Two independent systems in one dimension is the ordinary case.

A PORT IS A POSITION NESTED IN AN ADDRESS, the way a path is nested in a host. Every place system here is a
scoped compound — `<host>:<path>`, `<repo>@<sha>`, `<network>/<segment>` — and an endpoint's merge identity,
`protocol+system+at+port?`, already treated the port as part of WHICH position this is. It had no system
because the TRANSPORT LAYER HAD NO ROW: `tcp` and `udp` existed only as the value of a field. Each layer of a
stack owns a position system — the link layer MAC space, the network layer address space, the transport layer
port space — and an endpoint is a stack of positions, one per layer.

WHAT IT BUYS, measured in the garden this grew in: `port: "110/143/993/995"` — the defect `endpoints` was
written to end — is refused at last; and seven listening surfaces that are unix socket PATHS can be endpoints,
because `endpoints.system` is now any place system and `unix-filesystem` has always been one.

## anchor_systems[ipv4].levels

a prefix IS the level a position is held to: /24 is coarser than /32

## anchor_systems[iso-3166]

== THREE CANONICAL SYSTEMS FOR A GARDEN THAT KEEPS A MAP. Off the shelf, none invented. They exist so that
a many-layered place model — an administrative tree, a postal layer over the same ground, a drawn map — is held in
systems every garden shares, and two gardens that never met agree which place they mean.

## anchor_systems[street-address]

== MORE WAYS OF SAYING WHERE BY IDENTIFIER — each resolves through a coordinate, none is one ==

## roles

== ROLES: what a being DOES, as against what it IS (added 7.0) ==
THE FIX FOR AN AMBIGUITY THIS VOCABULARY SHIPPED WITH. `router` was a KIND until 7.0, and the proof it
was wrong is an asymmetry the corpus already carried: a mail server recorded five roles as free-text data
(`primary-mail, file-server, monitoring, webmail, erp-host`) while a router's single role was a kind.
Both are machines. What makes one a router is that it forwards traffic — which since 6.0 IS data, in
`treatments`. A kind answers what a being IS; a role answers what it DOES, and a being does several
things at once. Encoding one of the things it does as the thing it is made `kind` un-askable for every
machine that does two.

## operating_systems

== OPERATING SYSTEMS: what a machine runs, and what that IMPLIES about its positions (added 7.0) ==
It is a REGISTRY and not prose because it CONSTRAINS. `owns.os` was free text — a distribution name with its
point release — and a router, the one machine whose OS is genuinely distinctive, could not state it at all:
its OS lived only inside a summary sentence and an `owns.model` string.

`path_grammar` IS THE JOIN, and it is the answer to "where do ntfs and ext4 go". They do not go here.
`unix-filesystem` and `windows-filesystem` in `anchor_systems` are PATH GRAMMARS — properties of an
OS's API — and NOT filesystems. The two axes are independent: NTFS mounted on Linux through ntfs-3g
has unix paths, and one SMB share is `/mnt/share0` on the server and `\\server\share0` from a workstation. So an
OS declares which grammar its filesystem positions take, and `roots` is held to it by
`entry_must_match`. Storage FORMAT is a different registry entirely — see `storage_formats`.

## operating_systems[linux]

COMMON SYSTEMS (9.0). Until 9.0 this registry held exactly the four systems of the garden it grew in, so almost
every newcomer's first machine needed a local addition. `linux` is the honest row for a distribution not listed.

## storage_formats

== STORAGE FORMATS: the OTHER filesystem axis, the one ntfs and ext4 actually belong to (added 7.0) ==
`layer` mirrors `net_protocols.layer` and for the same reason: storage is a STACK and the stack is what
`carried_by` records. MEASURED on real machines rather than imagined — the chain
`partition -> crypto_LUKS -> LVM2_member -> ext4` is literally what `lsblk` prints on an encrypted laptop, and a
RAID server adds `linux_raid_member -> md` beneath it. `luks_root: true`, a bare boolean in an `attributes` block,
is that whole chain flattened to one bit.

## planes

== PLANES: what a surface, a link or a treatment is FOR ==
Off the shelf: the three planes every network design is sorted by. DATA is the traffic a device exists to carry;
CONTROL is how it decides where traffic goes (a routing adjacency, a spanning tree); MANAGEMENT is how an operator
reaches it (ssh, a vendor console, SNMP). The split matters because the three deserve different exposure: a data
surface is often public by design, and A MANAGEMENT SURFACE ANSWERING ON THE INTERNET is the oldest finding in any
audit. With a plane stated, that is a CELL a term can declare rather than a line in somebody's report.

## registry_links

== REGISTRY LINKS: a row of one registry names a row of another, and the gate resolves it ==
A protocol is also a TECHNOLOGY with a specification somebody publishes, and the technology catalogue is rooted in
the UNESCO fields of knowledge. A link is declared here ONCE, so the gate names neither registry.

## net_protocols

== NET PROTOCOLS: the one owner of what a being may SPEAK (added 6.0) ==
A REGISTRY rather than an enum on a term, for the reason `anchor_systems` is one: adding a protocol
must never be a rule-change. A row carries what is true of the PROTOCOL — which layer it occupies,
what carries it, and whether it manufactures a link others ride — so that no bean re-states any of it.

WHAT IS DELIBERATELY NOT HERE — IMPLEMENTATIONS. Samba OFFERS smb; the MySQL server SPEAKS mysql;
Postfix speaks smtp. An implementation is a BEAN (kind instance/product) that carries `endpoints`, and
putting `samba` in this list beside `smb` would give one thing two names — the exact duplication
`values_from` exists to stop. This was the first correction the design took: two of the names it was
asked to model explicitly, `samba` and `mysql`, are implementations, and encoding them as protocols
would have built the ambiguity into the law.

NOR ARE TLS VARIANTS SEPARATE ROWS. `https` is `http` whose endpoint takes the `encrypted` position;
smtps and submission are `smtp` on other ports. A protocol that differs from another only by what
wraps it is not another protocol, and giving it a row would put the same fact in two places — once as
a name and once as an aspect position — which is how the two come to disagree.

`layer` is DESCRIPTIVE, like `dimension` on anchor_systems: the gate consumes `protocol` (as the enum)
and nothing else in the row. It is here because carriage is what makes this a stack and not a list.

## net_protocols[tcp]

THE TRANSPORT LAYER. Until now `tcp` and `udp` were only the VALUE of the `transport:` field below, which
is why a port had no system to be a position in. A row here is what lets an endpoint NAME its transport when it
differs from its protocol's usual one — a DNS server answers on 53/udp AND 53/tcp, and the law could not say so.

## net_protocols[ipv4]

== THE STACK COMPLETED, AND THE CONTROL PLANE. `layer` runs link -> network -> transport -> application, and
each layer that ADDRESSES owns a positioning system (`positions:`). A ROUTING PROTOCOL is a control-plane row with
the two facts network design sorts them by: `family` — how it learns (link-state floods a map and each router
computes; distance-vector trusts its neighbours' sums; path-vector carries the whole path, so policy can refuse
one) — and `scope` — interior to one administration, or exterior, between them. What one computes over is what a
system row calls `neighbours`: an adjacency, a metric, AREAS AS LEVELS, and summarisation as containment.

## net_protocols[ethernet]

APPENDED AFTER THE APPLICATION ROWS RATHER THAN BESIDE `wireguard`, where they belong by layer.
dmsafe compares leaf paths BY INDEX, so inserting a row mid-list reads as deleting the fields of
every row after it — the rollback said so and was right about what it could see. Grouping by layer
is a legibility preference; a clean, honest diff is not.

## units

== UNITS: the resolution a position is actually held to (added 5.1) ==
DECLARED, NEVER INFERRED FROM DIGITS. A journal can state most entries as `## 2026-08-04` and a few as
`## 2026-08-04 20:04 +0300`, and nothing records which of the first were measured to the day and which
were measured finer and rounded. Two positions whose resolutions OVERLAP ARE NOT ORDERED, and a model
that cannot say so invents an order instead — which is the failure this registry exists to make
expressible. Keyed by `dimension`, so a length or an angle joins without a rule-change.

## vacancy_reasons

== VACANCIES (Tier-0). P6/B2: whoever DECLARES a position accounts for it, so the duty to explain
these is discharged HERE — an adopting garden must never inherit an obligation to justify a position it
never asked for. The gate applies ANTI-ROT only to garden-local vacancies: a garden that OCCUPIES one of
these is a prediction coming true, and it cannot edit Tier-0 to withdraw the vacancy, so treating that
as an error would be an unfixable failure.
The reasons a vacancy may give, declared rather than known by the gate. A reason is a CATEGORY OF
ABSENCE — why nothing occupies a position the law makes available — and that is a statement about the
world, which the vocabulary owns and the interpreter must not carry a copy of. Adding a reason is a
rule-change here, not an edit to bin/.

## leaf_orders

`universal`: the position is declared because the STRUCTURE is general, not because an occupant is
expected here. A figure with a side missing is a worse model than a figure with a side nobody stands on, and a
standard that waits for one garden's occupant before completing a mechanism ties every garden to the first
one's size. It is a reason and not a licence: the position must belong to a mechanism that IS occupied
somewhere on the same figure, and its `why` says which.
== LEAF SUBSUMPTION ORDERS (declared 2026-08-03, Phase 6) ==
`merge_field` absorbs a general value into a more precise one where the two are ORDERED: 192.168.0.0/24
into 192.168.0.0/16, "AlmaLinux 9" into "AlmaLinux 9.8". WHICH keys are ordered that way was decided in
code by two hardcoded checks on the key's NAME, whose own comment called them "the last hardcoded merge
knowledge here, and they belong in the vocabulary". They are here now.

This is the fallback for the facts INSIDE `owns` / `details` / `attributes`. A term's own `merge.order`
still wins where a term exists — but those inner keys are FACTS, not terms, and `bin/dmmerge.py` says
so outright: "listing them would bury the real gap in three hundred names". A registry of ORDERS is the
shape that fits, because the rule is about a family of names and not about any one of them.

## leaf_orders[cidr].exact

`provides_ip`, `public_ip` and `mgmt_ip` were also listed by name in the code —

## leaf_orders[cidr].why

all three end in `_ip`, so every one of them was already covered by the suffix
and the list was dead weight. Measured before deleting it, not assumed.

## leaf_orders[version].exact

`version` does NOT end in `_version`, so unlike the cidr list this one earns

## leaf_orders[version].why

its place; `os` is the estate's one bare version-shaped fact name.

## leaf_orders[containment].system

11.0: and the windows one, whose rows carry the same `root:`/`<host>:` forms

## leaf_orders[instant].every_calendar

This order follows what a value IS, not what its key is called. Time sits under a dozen names in one corpus
(observed, as_of, found, since, created, expires, …) and under `at`, which also holds paths; a name list would miss
the next name and misfire on `at`. A value in a calendar's ONE form is a time.

It named one calendar until 18.0, so a day written in any other contained nothing and two gardens dating the same
fact in two calendars could only disagree. Calendars meet at the day, so containment is asked there. Across two
calendars it is asked only when both begin their day at the same moment: where a day begins at sunset, which day a
clock time falls in depends on the place and the season, and an order computed by arithmetic would be an invention.

## vacancies[owned_by.entry_one_of]

== THE ENTRY FORMS THE OWNERSHIP TERMS OFFER (declared vacant 2026-08-03) ==
`entry_one_of` positions are positions like any other: the law offers a form and something should
occupy it or say why not. Nothing counted them until the reverse gate learned to, and all three of
these turned out to be genuinely unoccupied rather than overlooked.

## vacancies[aspect:necessity]

== THE DEFAULT POSITION, VACANT BECAUSE A DEFAULT NO LONGER OCCUPIES (declared 2026-08-03) ==
Until today the reverse gate collected occupancy with `entry.get(attr, default)`, so this position
looked exercised by five edges that never mention it — the gate crediting its own default. Occupancy
is STATEMENT now, and what that leaves behind is this: a position every requirement in the estate
effectively sits at, and none has ever taken a stance on.

## figures

== FIGURES: the shapes an aspect may take (added 9.2, human-ratified rule-change, "T0") ==
Until 9.2 every aspect was an OPPOSITION (a square, or a one-axis binary) and `figure:` was free text. Time, place,
routine steps and "must stay acyclic" are not oppositions: they are positions related by NEIGHBOURHOOD
along direction lines. So a second figure is declared, and `figure` becomes an enum this registry owns.

SEQUENCE IS THE GENERAL STRUCTURE; everything ordered is a RESTRICTION of it. The operator's model, from
the time conversation of 2026-08-05: an instant is a sequence restricted to one position on one line;
"acyclic" is a sequence restricted from returning; a calendar is one anchor system on a metered line,
never time itself. A sequence is therefore declared ONLY by its restrictions, each stated, none assumed:
an unstated restriction is how a model silently becomes narrower than the world (the `dag` rule once
took "acyclic" to be the definition of walkable).

EXTENT. A sequence with an order has a DOMAIN, and a bounded region of it (a start and an end, either
possibly open) is an extent: a duration on time, an area on place, a stretch of a routine. Duration is
therefore not a time concept but an aspect-having-a-domain concept. An opposition has no "between": its
positions are modalities without order, so extent on one is declared IMPOSSIBLE rather than skipped.

## figures[opposition].meaning

NAMED FOR WHAT IT IS, NOT FOR ITS DIMENSION. Aristotle's square of opposition is this figure's TWO-axis
case, a plain binary its one-axis case (`confidentiality`) and a cube its three-axis case. Calling the
figure "square" would fix a count the gate is required to derive: "when doing the squares make sure
cubes don't bite" (the operator, 2026-08-02).

## extent_form

== EXTENT (11.2): the bounded region `figures` has declared POSSIBLE since 11.0, carried at last ==
The figure block above says it and says why — "a sequence with an order has a domain, and a bounded region
of it is an extent (a duration on time)" — and for two versions nothing could write one. A corpus measured
on 2026-09-20 held about forty durations as PROSE because of it: thirteen "daily", five "weekly", "every 5
minutes", "for 204 days", four retention policies, log rotation, certificate lifetimes. None of them
readable by anything. That is the shape of defect this vocabulary exists to refuse — a rule with no
position for its own data — and it was in the law's own description of itself.

DURATION IS NOT A TIME CONCEPT. It is an aspect-having-a-domain concept: a duration on `time`, an area on
`place`, a stretch of a `routine`. So the region names the ASPECT it lies in and the rules follow from
that aspect's own restrictions, rather than time getting a construct nothing else can use.

## value_types

== VALUE TYPES (10.0, T3): the named types an attribute may be `in: { type: … }` ==
They were patterns written in the gate's code. A TIME value type is a POSITION: `iso_date` is not "a date
format" but the calendar system held at unit DAY, so every `observed: 2026-08-09` in a garden was always a
position in gregorian-civil whose second and minute are UNKNOWN, not zero. Saying so needs no data change;
it states what those values already were. A type with no system (kebab) is only a form.

## journal

== THE JOURNAL (10.0, T3): where the record of what was done is, and how an entry is headed ==
The journal is the garden's time record, and it had no rule for time. One real garden, measured on
2026-09-19: 663 entries, 276 headed with a date only, 387 with a time in `+0300` or `+0330` while the calendar
system's one form is `+03:00`; and one entry headed 23:59 that was committed at 23:32, a precision written
rather than read. A heading is now a position in gregorian-civil's one form, held to at least the MINUTE,
with its offset, because an entry is ordered against every other and a reading with no offset cannot be.
Only headings ADDED by a commit are checked: the journal is never rewritten, so its history keeps the forms
it was written in, and those stay what they were.

## journal.checks

entries a commit adds; never the history

## aspects[necessity].meaning

The canonical closed figure for necessity is Aristotle's SQUARE OF OPPOSITION (De Interpretatione;
the modal square). Nothing invented: the four modalities and their contradictories are off the shelf,
and the diagonals ARE the complement pairs. `consumes` and `depends_on` are positions on this aspect,
which is what the operator meant by "consumption is going to be necessity aspect" — consumption is
not a standalone edge but one way a being can NEED something.

## aspects[necessity].poles

BOTH axes: a square is 2-dimensional,

## aspects[necessity].positions

and declaring one would orient it like a line

## aspects[capability].meaning

The SECOND aspect, and the first evidence that the machinery generalises. It reuses the square of
opposition but NOT the same square: `necessity` is ALETHIC modality (what IS the case — this input is
required), while capability is DEONTIC (what MAY or MUST be the case — this being must not do that).
Conflating them is the same error as one axis doing two jobs: "this VPS cannot send mail directly" and
"recursion must stay off" feel alike and are not — one is a fact about the world, the other a rule.
Positions relate a being to a CAPABILITY (an open kebab name), not to another being, which is what
the necessity aspect could not express.

## aspects[capability].poles

both deontic axes

## aspects[feasibility].meaning

The THIRD aspect, and the reason a term may sit on more than one. It shares the ALETHIC square with
`necessity` but asks a different question of it: necessity asks whether a REQUIREMENT is binding,
feasibility asks whether a STATE OF AFFAIRS can obtain. Reusing `necessity` for this would have been
equivocation — its positions are documented in requirement terms ("without it the being cannot do its
work"), which is not what "recursion could be switched on" means.
WHY IT EARNS ITS PLACE: a prohibition on something IMPOSSIBLE is harmless; a prohibition on something
POSSIBLE is where the risk lives. a DNS server's recursion ban matters precisely BECAUSE recursion could
be switched on, whereas a VPS's mail-egress ban is belt-and-braces over a block that already stops it.
Only carrying both modalities distinguishes those two, and they demand very different vigilance.

## aspects[feasibility].poles

both alethic axes

## aspects[confidentiality].meaning

The FOURTH aspect, and the first that is ONE-DIMENSIONAL. `poles` already allowed it — "one axis
(a contradictory PAIR), or a LIST of axes — a figure may be 1-dimensional" — and nothing had
exercised it. A one-axis figure is the honest shape here: whether a channel protects its payload
is a single contradictory pair, and there is no second modality of it.

WHAT WAS CONSIDERED AND REJECTED: a second axis for PEER VERIFICATION (verified/unverified), which
would have made this a square like the other three. It was dropped rather than forced. In the three
existing squares the two axes are related by subalternation — necessary implies possible, required
implies permitted — and verification does not stand in that relation to encryption in any way that
survives contact with opportunistic TLS, where the channel is encrypted and the peer is proven by
nothing. Inventing the implication to make the figure symmetrical would be exactly the silent
generalisation the protocol forbids. Peer verification is a real and separate question, and it can
be its own aspect the day something needs to take a position on it.

## aspects[time]

== SEQUENCE ASPECTS (9.2, T0). No positions and no poles: a sequence is not a closed set of modalities
but a domain walked along lines.

## aspects[time].order

two positions whose RESOLUTIONS overlap are unordered: `2026-09-19` (unit day) is

## aspects[time].acyclic

neither before nor after `2026-09-19 22:50` (unit minute); it contains it

## aspects[place].meaning

SEMI-DEFINED (the operator's note, 2026-08-05): declared so the figure is proven against a second
aspect, and because civil time RESOLVES THROUGH place: an offset is a geographic fact. No term takes a
position on it yet; its lines are open because a filesystem tree, a site and a coordinate differ in how
many there are.

## aspects[place].metered

geographic coordinates are metered and containment is not; until a term needs

## aspects[place].order

the difference, the aspect claims no measure it cannot give every system

containment orders a path within its tree and nothing across trees

## aspects[walk].meaning

THE `dag` RULE, RE-READ. A term whose schema says `dag: true` is a position on this aspect: its edges are
a sequence restricted to `acyclic`, and the gate refuses a cycle BECAUSE this row says acyclic, not
because code names the key. Nothing about the check changed; what changed is that acyclicity is now
one declared restriction of a sequence instead of the definition of walkable.

## aspects[walk].term_key

a term carrying `dag: true` places its edges on this aspect

## aspects[walk].domain

its positions are beans, not positions in an anchor system

## aspects[routine].meaning

T4 (10.1): a procedure is a SEQUENCE OF STEPS, and the operator's own description of it (2026-08-05) is
the definition: "completely sequential even with branches, for example steps of a routine even with
their conditions". Lines are OPEN because a branch adds one. It is NOT acyclic: a routine may loop (retry
until it passes), which is exactly why acyclicity had to stop being the definition of walkable.
CLOSED NEIGHBOURHOODS, the third ply: a step's `next` is COMPLETE, these branches and no others, so the
gate can refuse a branch that points nowhere, a step nothing reaches, and a routine with no end.

## aspects[routine].domain

its positions are the routine's own steps

## registry_files

== PROFILES (added 2026-08-02, std-vocab@2.0 / P6 E4) ==
Terms that are general to a KIND of garden rather than to all gardens. A garden opts in with
`extends_profiles: [<name>]`; one that manages no code should not inherit code terms, and without
profiles the only options were to force them on everyone or to leave them local forever.
== KNOWLEDGE: published classifications as UNIVERSAL ANCHORS (9.1, the `knowledge` profile) ==
A garden that records what a thing IS in the world's own terms — which field of knowledge a skill draws on,
which occupation a role is, which technology a program is — should use codes every other garden uses too, so
two gardens that never met agree that "ISCO-08 2522" and "Samba" are the same objects. The classifications
are DATA the law points at, kept whole (every level) in seed/knowledge/, not restated in this prose.

## knowledge_schemes[isco-08].crosswalk

seed/knowledge/crosswalk-isco-08-isced-f-2013.tsv

## knowledge_schemes[technology].within

every technology names the UNESCO field(s) it belongs to (its `isced_f_2013` column): the

## knowledge_schemes[technology].neighbours

fields of knowledge are the ROOT, and a protocol, a product or a routing mechanism hangs from one

## profiles.code.terms[code_paths].meaning

The 'paths vocab' (added 2026-08-01, human-directed): so an agent LOCATES code without re-walking a tree,
and knows which trees are REFERENCE-ONLY (never re-scanned each session).

## profiles.code.terms[code_paths].schema

GATE (P2): enforced generically from here, not from code

## profiles.code.terms[code_paths].schema.required_on_kinds

a kind:codebase bean MUST carry a non-empty code_paths

## profiles.code.terms[code_paths].agent_directive

MOVED OUT 2026-08-02 (P1 / D6, human-ratified): `summary_ref` and `last_indexed` left this term and now
live in `analysis_cache`. Rationale (one-owner-of-a-fact): a summary is an ANALYSIS RESULT, not a property
of a filesystem path, and a date is a weaker staleness signal than the source's own git sha. code_paths
now does exactly ONE job — LOCATE the tree and say whether it may be walked. An analysis_cache entry
binds back to the tree it analysed via its `covers_paths`.

## profiles.code.terms[git_remote].anchor

a remote URL is globally unique for the repo → establishes a codebase's identity

## profiles.network.terms[endpoints].meaning

WHAT A BEING ANSWERS ON. This is the half `ip` never had: an address with no protocol and no port
is a fact about a network interface, not about anything a being can reach. A mail server's
`details.boot_surface.mail_ports_expected` was straining toward this shape and could not get
there — it carries `{ port: 25, service: postscreen }` beside `port: "110/143/993/995"`, four
ports jammed into one string, and `service` naming IMPLEMENTATIONS where it means protocols.

## profiles.network.terms[endpoints].schema.attrs.transport

THE TRANSPORT IS USUALLY THE PROTOCOL'S OWN, so an entry states it only when it differs: a DNS server's second
endpoint says `transport: tcp`. The default is READ FROM THE PROTOCOL'S ROW rather than typed here, so the
protocol stays the one owner of what usually carries it.

## profiles.network.terms[endpoints].schema.cells[·]

LOOPBACK is excluded: there is no path there for anything to be on.

## profiles.network.terms[links].meaning

A LINK IS A THING, NOT A SENTENCE. Today the estate's tunnels live as prose in `owns:` on three
beans, and the direct cost of that is on record: the router's `owns.wg_tunnel` said it dials
endpoint 203.0.113.19 while the VPS's `owns.wg_identity` said it dials .16 and listed .19 as a freed
spare. Two beans, the same scanning agent, one day apart, and the gate cannot see it because
`owns` has no rule to check. A link whose far end is a RESOLVED REF cannot contradict itself.

## profiles.network.terms[reaches].meaning

WHAT A BEING NEEDS TO TALK TO. Deliberately NOT a dag: a server reaches its router and the router reaches
the server, and that is ordinary rather than a cycle to be refused.

## profiles.network.terms[treatments].meaning

NOT A LAYER, AND KEPT OUT OF THE STACK ON PURPOSE. routes, nat, mangle and acl are not positions
in a protocol stack — they are what a forwarding device DOES to traffic that is passing through
it. Folding them into `endpoints` or `links` would be the force-fit that ground rule 2 forbids:
the shape would be satisfied and it would be the wrong shape.

## profiles.network.terms[treatments].schema.required_on_roles

7.0: was `required_on_kinds: [router]` until `router` stopped being a kind

## profiles.domain.terms[registration].meaning

PROMOTED 2026-09-17 (human-ratified, std-vocab 8.2) from one garden's local vocabulary, where it had been
a candidate "to revisit with a second garden that has domains". A cold-start drill garden modelled a
domain and had nowhere standard to put its registrar or expiry. A PROFILE, not the core: a garden
with no domains inherits neither the term nor its requirement.

## profiles.domain.terms[registration].schema.expiry

WHICH DATE AGES, said here rather than in the tool. bin/dmstale.py named `registration` and
`expires` in its own source until 2026-09-20: this term was born garden-local with the tool
extended for it the same day, and when it was promoted to Tier-0 nobody went back. A garden
that invents a term with an expiry got no warning, however well the gate enforced the date —
first-class to the gate, invisible to the tool that would have made it useful.

## profiles.knowledge.terms[knowledge].meaning

THE RELATION TO KNOWLEDGE. A bean that is not itself a field, an occupation or a technology still stands
in relation to them: a Samba instance USES the technology samba; a mail-filtering design DRAWS ON the
field 0612; a person's role is CLASSIFIED AS 2522. One term for every scheme: the entry names its scheme
and the gate checks the code against THAT scheme's registry. `topic` names the concept inside the field
("fluid pressure and flow" for espresso, inside physics) — the overlap between domains is the point.

## terms[capabilities].meaning

Open key, closed figure — the same shape as analysis_cache, which is the proven pattern here: a NEW
capability needs no rule-change, while the STANCE taken on it must sit on the figure. This is where
a prohibition stops being a prose safety note and becomes something the gate carries.

## terms[capabilities].schema.attrs.why

a stance with no reason is folklore; the reason IS the fact

## terms[capabilities].schema.attrs.permission

TWO aspects: what is ALLOWED, and what is SO

## terms[capabilities].schema.cells

Two squares span a GRID, and the grid has cells NEITHER square can see. Checking each aspect
alone permits both kinds below. The split matters: one pair cannot both be true, the other pair
can and is simply bad.

## terms[capabilities].schema.cells[·]

incoherent — an ERROR: one of the two positions is mis-stated

in_breach — a WARNING: both CAN hold; the state needs action

## terms[consumes].meaning

SETTLED at 2.1. The v2 plan proposed retiring it as unused; it had a live occupant, and the operator
assigned it a home: "consumption is going to be necessity aspect". It is now a position-bearing
relation ON that aspect rather than a standalone edge, which is what unblocked its promotion — it was
the one term 2.0 deferred for INSTABILITY rather than scope.

## terms[consumes].schema.is_ref

an input is needed unless an edge says otherwise

## terms[refs].meaning

THE OPEN RESIDUAL. Any edge that is not one of the canonical relations above lives here, and MUST
name its own relation via `rel:`. The KEY is a slot label (it may be arbitrary, e.g. `party_acme`);
`rel:` is the relation TYPE, so an edge read alone still says what it is. `rel` is OPEN and kebab —
deliberately NOT an enum, for the same reason analysis_cache's cache_type is not one: a new kind of
relation must never require a rule-change. It is therefore outside the reverse gate by design.

## terms[depends_on]

LOCAL kinds: object types this garden manages that std-vocab doesn't schematize. Each gets a small schema
(MODEL Rule 6). A kind that proves general is promoted alongside its terms.

## terms[depends_on].schema.is_ref

the sibling of `consumes`: depends_on needs
a BEING, consumes needs its PRODUCED STATE

## terms[status]

== CORE GRAMMAR ENUMS (promoted 2026-08-02, std-vocab@2.0 / P6 E3) ==
These were CODE CONSTANTS in bin/dmcheck.py (STATUSES, ID_STATUS, ANCHOR_CLASSES, AUTHORITY, SRC) —
the last place in the system where a type rule lived outside the vocabulary. Absorbing them completes
D4 ("type rules live in the VOCAB, not code"). Each is addressed by `path:`, because these are NESTED
fields rather than top-level terms. MAJOR: two of them were WARNINGS in code and are ERRORS now, and a
garden using a value not listed here will be rejected where it previously passed.

## terms[status].schema

`closed` ADDED 7.0 (2026-08-07, human-ratified). A bounded piece of work that FINISHED is not
`deprecated` — deprecated means superseded, still present, and not to be relied on, which is a
judgement about something that continues to exist. A session that did its work and stopped has no
such shadow over it. The estate had no word for the difference and both wrong answers were already
in the corpus: one session bean called itself `deprecated`, which reads as though
its work were discredited, and another stayed `active` indefinitely, which
reads as though it were still running. The second is the more dangerous of the two — a reader
scanning for live sessions would find a ghost.
SCOPED BY SENSE, NOT BY RULE: `closed` belongs to kinds that BOUND their work — session, program,
contract. Nothing forbids it elsewhere and nothing should invent a per-kind status mechanism to try;
`draft` has always been equally meaningless on a host and has never needed guarding.

## terms[status].merge

Two gardens disagreeing about a being's lifecycle state is a real disagreement about the world,
so it surfaces as a conflict rather than one of them quietly winning.

## terms[provenance_src].merge

THE RANK, DECLARED AT LAST (11.3). MODEL.md and MERGE.md state the guard — an `inferred` value never
overrides an `asserted-by-human` one — and until 11.3 the order that implements it was four numbers in
bin/dmmerge.py, the oldest rule in the system kept as a constant in a tool. It is the same construct
`anchor_authority` uses below. The merge reads it for two things: which src a value several gardens agree
on keeps (the highest), and the guard itself — a value at the TOP of this rank is never dropped in favour
of one below it, whatever precision the lower one claims. The merge REFUSES to run if this is absent.

## terms[provenance_src].values_meaning

EACH PLACE IN THE RANK, EARNED. The rank orders HOW A FACT IS KNOWN:

## terms[analysis_cache]

`borrows` IS WHAT THE MERGE READS; `values_meaning` is for the reader. The LABEL is never rewritten — a
merged value still says a tool produced it, which Phase 7 (2026-08-03) showed is exactly what must not be
lost or gained by passing through a tool. Only the weighing borrows.

## terms[analysis_cache].meaning

Design step D6, executed as P1 (2026-08-02, human-ratified rule-change).
An OPEN, TYPED, bean-level cache of ANALYSIS RESULTS, so an agent READS a recorded result instead of
re-deriving it. Adding a NEW <cache_type> requires NO schema change and NO bean restructure — that is the
whole point of the term: the garden can start caching a new kind of code/analysis (a new language, a new
lens) forever, without a future migration.

## terms[analysis_cache].schema

GATE (P2): enforced generically from here, not from code

## terms[analysis_cache].schema.shape

NB the KEY is open: no `values`/`values_from` is declared for it,

## terms[analysis_cache].schema.key_form

so the gate can only ever require kebab-case, never a fixed list.

## terms[analysis_cache].schema.required_on_kinds

a kind:codebase bean MUST carry a non-empty analysis_cache

## terms[analysis_cache].schema.attrs.as_of

Rule 6: absolute dates only

## terms[analysis_cache].schema.attrs.staleness_key

11.0: a staleness key is a POSITION, and `git-head:<sha>` was resolved against whatever tree the
READER had checked out — one analysis, one verdict per machine. The git-object-graph form names the
repository, so every reader asks the same object graph. `manual:<why>` stays for what no key can track.

## terms[analysis_cache].open_keys

restated for the human reader; the gate reads schema.key_form

## terms[nature].meaning

Ontological type of a being — the routing key from a bean up to the ownership crown (MODEL §Ownership).
physical -> nature (res extensa), metaphysical -> logos (res cogitans), living -> love (conatus);
all resolve up to god (Deus sive Natura). The crown is a MODEL axiom, NOT instantiated as beans.

## terms[nature].schema

GATE (P2 interpreter; P3 made it the root axiom)

## terms[nature].schema.required

P3/D1: MANDATORY on every bean, whatever its kind

## terms[nature].schema.must_equal_kind_attr

and it must agree with the kind that refines it

## terms[owned_by].meaning

Faceted ownership. ONE owner per facet (the 'one and only one owner' law, held per facet).
Co-ownership of a SINGLE facet is never a raw fact -> a `contract` bean (agreement_ref + conflict_rule).

## terms[owned_by].schema

GATE (P2): enforced generically from here, not from code

## terms[owned_by].schema.alt_form

the INHERITED form: a single `via` ref, no facets

## terms[owned_by].schema.key_form

otherwise every key must be a declared facet

## terms[owned_by].schema.entry_one_of

a bean, a contract, outside, or the axiom itself

## terms[owned_by].schema.entry_must_match

the branch is NOT free: nature routes it

## terms[owned_by].schema.entry_form_from_kind_attr

a kind may PIN which form it must use (see kind: person)

## terms[owned_by].schema.dag

ownership must stay acyclic

## terms[owned_by].schema.attrs.contract

`external` and `crown` resolve to no bean by design

## terms[responsibility].meaning

P7 (2026-08-02, human-ratified). THE CLOSING ARC. Operator: "the ownership is trapped in the same
paradox isn't it? ... ownership is only meaningful where the responsibility covers on the opposite
aspect." `owned_by` alone is one-directional — a being points UP to its owner, up to the crown. That
is one arc of a loop, and P5's `external` form made the gap visible: BIND terminates in prose at
neither a bean nor the crown. Responsibility is the OPPOSITE arc, the holder answering DOWN for the
being. Together they close. `external` then stops being an escape hatch and becomes an ordinary
position: owned outside, answered for inside — which is the true statement about every third-party
thing this estate runs.

## terms[responsibility].schema.alt_form

inherited, exactly as ownership inherits

## terms[responsibility].schema.key_form

the SAME facet lattice — the two arcs pair per facet

## terms[responsibility].schema.entry_one_of

NB no `crown`: the crown owns but never answers

## terms[responsibility].schema.facet_parity_with

the loop must CLOSE: same facets on both arcs

## terms[facets].meaning

The ownership-facet lattice: DISTINGUISHABLE (crisp boundary; resolve overlap by a depends_on edge or
boundary refinement, NEVER ambiguous double-coverage), DEPENDENCY-bearing (DAG), and RECURSIVE
(a facet may decompose into sub-facets, ownership recursing within).

## terms[facets].enforced_by

AT TIER-0 there is nothing to check: this term defines the lattice RULES

## terms[facets].rules

(below) but declares no values, because `legal`/`technical` are defensible
universals while the extensible three are unoccupied predictions. A garden
supplying values inherits the drift guard through its overlay, and that IS
enforced there. Left as an empty `schema:` key by the 1.1 promotion until
golden V5 caught it — a term that states no rule and no reason is exactly
the silent gap this release exists to remove.
values_from:facets)
definition below, so the two can never drift apart.
NB: 'facilitation of creation/production' is NOT modelled as an ownership facet — a facilitator is a
HABITAT the creation act lived in (lives_in, time-windowed), and any equal-sharing of that facilitator
stake is captured by a `contract` over the creation aspect. Kept lean on purpose.

## terms[instance_of].schema

GATE (P2): enforced generically from here, not from code

## terms[instance_of].schema.is_ref

the mapping IS the ref

## terms[lives_in].meaning

Habitat / containment stack — RECURSIVE and typed; DISTINCT from ownership (a token is NOT owned by its
host). e.g. addon-token lives_in odoo-instance lives_in host{linux-baremetal|docker|windows|odoo.sh}.

## terms[lives_in].schema

GATE (P2): enforced generically from here, not from code

## terms[lives_in].schema.dag

habitat containment must stay acyclic

## terms[lives_in].schema.is_ref

the mapping IS the ref

## terms[lives_in].merge

habitat_types MOVED to the `provides_habitat` term below (P5): the list had no bean field, so a
habitat's TYPE could not be recorded at all — the hole the reverse gate found on its first run.

## terms[provides_habitat].meaning

P5/D5. Closes the hole the reverse gate found in P3.5: `lives_in` names WHICH being a token lives in
but never WHAT SORT of habitat that being is. The type belongs to the habitat, not to the lodger —
a VPS is a linux habitat whoever lives on it — so it is declared here and required on any bean that
is actually the target of a lives_in edge. A habitat can no longer be untyped.

## terms[provides_habitat].schema.required_on_targets_of

values: GARDEN-LOCAL. Habitat TYPING is universal; `odoo-instance` and `odoo.sh-subscription` are not (P6/B2).

## terms[creator].meaning

DISTINCT from owned_by.legal.owner even though creation CONFERS legal ownership (VOCAB facets.legal):
they coincide across this estate today, but a transfer would separate them and the creation fact must
survive it. Recording both is therefore not a duplicate authoritative fact.

## terms[ip].schema.value_form

needs real parsing, not a regex — the `canonical` rule is 'python ipaddress normal form'

## terms[ip].anchor

reassignable (DHCP/NAT/reuse) → corroborating only, never sole

## terms[hostname].anchor

reassignable

## terms[fqdn].anchor

DNS-unique within its namespace

## terms[mac].merge

a host may have several NICs

## terms[serial].schema.governs_anchor

NO PATTERN: serials are vendor-shaped, and inventing one would reject valid data to look thorough. But they
are COMPARED case- and space-insensitively (9.0): no vendor issues two serials differing only by case, and
a drill committed `syn-0042` beside `SYN-0042` as two machines with 0 errors.

## terms[wg_pubkey].anchor

crypto-anchored to the keypair

## terms[emp_id].enforced_by

no canonical form declared: an employer-assigned id has whatever shape the employer uses.

## terms[emp_id].anchor

name is NEVER an anchor

## terms[id].enforced_by

kebab-case, id == filename, and uniqueness per (space,base) are CORE bean-grammar checks — schematising them would duplicate a rule that already bites.

## terms[ref].meaning

NARROWED at 2.0 (P6/E6): this term used to CLAIM refs/consumes/depends_on and state the DAG rule for
them. Those are now first-class relations with their own schemas, so `ref` describes only the LINK
FORM they share. This is the MAJOR change of the release: an existing term's handling moved.

## terms[ref].enforced_by

the link FORM and its resolution are CORE checks (target exists, named field present, shallow). Since 2.0 the acyclicity is declared per relation via schema.dag rather than here.

## terms[shell-log].enforced_by

a PROCESS term: it governs how an agent logs shell work to log/journal.md, not the shape of any bean field. There is no bean data for a gate to check, and that is a property of the term, not a gap.

## terms[kind]

== THE BEAN-GRAMMAR AND FACT-SECTION KEYS (added std-vocab@5.0, 2026-08-02, human-ratified) ==
These were never terms. They did not need to be while the gate enforced them in CORE and nothing else
read them — but `bin/dmmerge.py` became generic over top-level keys, and a key with no `merge:` facet
is merged by a SHAPE GUESS. A guess can be the wrong guess, so each of them now declares how it
merges. Most ratify what the guess already did; the three that do not are marked.

## terms[owns].enforced_by

Rule 1 is a Part B judgment: no gate can tell a duplicate from a reference

## terms[merge_open]

== THE MERGE DRIVER'S OWN STATE (declared 2026-08-03, Phase 5 / D22) ==
`bin/dmmerge.py` writes these and `bin/dmcheck.py` reads them, and until now there was NO TERM
BETWEEN THEM — two tools agreeing about a key by coincidence, which is precisely the shape the
law-in-data rule exists to forbid. They are also the reason the unclean marker no longer lives on
`status`: `status` is a `single` merged term, so the driver writing its own flag there collided with
the algebra on one key, and the next merge turned it into a conflict the in-place writer could not
write back.

## terms[provenance_of].meaning

PER-LEAF PROVENANCE, BESIDE THE VALUES AND NEVER INSIDE THEM. `owns.os: AlmaLinux 9.8` stays what a
human reads; this says who said it. Written only by the merge driver, on beans it produced. Without
it a merged bean read back can only be re-merged as the READER's own assertion — every value
restamped `generated-by-tool` — which disarms the guard that an `inferred` value may never override
an `asserted-by-human` one, because SRC_RANK is what enforces that guard.

## terms[between]

== CONTRACT KEYS. `contract` is a Tier-0 kind and its `schema:` prose already names these five; they
are declared here so the merge reads them from the same place the kind describes them.

## terms[between].merge

SINGLE, not set — and this CHANGES what the shape guess did. The parties to an agreement are
constitutive of it: unioning two gardens' lists would silently produce a three-party contract
nobody agreed to. Two gardens disagreeing about who signed is a conflict for a human.

## terms[over].merge

SINGLE, not a per-key collection — a reference capsule is one thing, exactly like `lives_in`.

## terms[trigger]

== MAPPING KEYS. A `mapping` document records how bean data feeds a command or checklist. These were
missed on the first pass because `dmmerge.load_garden` globs `beans/*.md` only — the corpus merge
never saw them, though `.gitattributes` dispatches `mappings/*.md` to the same driver. Found by the
golden check that scans BOTH, which is the argument for asserting over the corpus rather than over
whatever the tool under test happens to read.

## terms[steps].schema

10.1, T4: a list of PROSE lines (read in list order, as before) or a list of STEP ENTRIES
`{id, do, next: [{to, when?}], note?}`, never a mix. `next` absent or empty ends the routine; two or more
`next` entries are a branch and each names its condition in `when`.

## terms[steps].merge

NOT a set: these are a SEQUENCE, and order carries the meaning — validating after installing is a
different procedure from validating before. A set-union would reorder them into nonsense, so the
whole list merges as one atom and two gardens with different steps conflict.

## terms[located_at].meaning

THE BEING'S LOCATIONS. The meaningful object is the being — a codebase — and it may be found as a
tree on a host, as reachable objects in a repository, or as a PRINTED COPY on a shelf. None of those
is privileged and a being may be at several at once. `openness` is the field that carries what cost
this estate a session: a position that is NOT KNOWN is recorded as unknown rather than omitted,
because an omitted location reads as "there is none" and that is how an exhaustive search over the
wrong domain produced output identical to a real one.

## terms[timing].meaning

WHEN, AT A DECLARED RESOLUTION. The open key is what makes this serve sessions without a session
schema: `start`, `sync`, `stop` are keys, not law, and a run with four sync points needs no
rule-change to record them. The closed part is each entry's shape — the same open-key/closed-figure
pattern `analysis_cache` proved.

## terms[roots].meaning

THE RESOLUTION HALF of the `root:` position form. A bean says WHERE a thing is in a portable way
(`root:addin/CloudApi`); a HOST says what that root means on itself. Two hosts therefore
never edit the same text to disagree about a path — each states its own resolution on its own bean,
which is what makes adding a machine a one-line change instead of a corpus migration.
It lives on the HOST because that is whose fact it is. A root map in a shared file would be one
document every machine has to edit, which is the merge conflict this design exists to avoid.

## terms[roots].schema.entry_must_match[·]

THE JOIN (7.0): a host's roots are stated in the path grammar its OWN OS declares, so the two
can no longer disagree. `keyed_by: os` selects the operating_systems row by a field of the BEAN,
which is the same machinery that fixes a crown branch from a bean's nature. It is on `roots` and
NOT on `located_at`, deliberately: roots is the host describing itself and every bean carrying
it has an `os`, while `located_at` is carried by codebases, which have none.

## terms[roles].meaning

WHAT A BEING DOES. A LIST, and that is the whole point: a server may do five things and a router one,
and until 7.0 the estate expressed the first as free text in `owns.roles` and the second as a KIND.
Making this a term is what let `kind: router` be retired without losing the requirement that a
router document its treatments — `required_on_roles` reaches a list where `required_on_kinds` could
only ever reach a scalar.

## terms[os].meaning

WHAT A MACHINE RUNS, and the reason it is a registry rather than a string: it CONSTRAINS. An OS row
declares the `path_grammar` its filesystem positions take, and `roots` is held to it below. Before
7.0 this was `owns.os` free text — a distribution name with its point release — and a router, the one
machine whose OS genuinely differs in kind, could not state it at all.

## terms[volumes].meaning

THE STORAGE STACK, and the deliberate twin of `links`. Both record a layered carriage on one being;
both use `carried_by` to name the entry beneath; and neither is declared acyclic, for the reason
written out at length on `links` — `carried_by` names another entry on the SAME bean, so there is no
cross-bean graph for the gate to walk.

THIS IS WHERE ext4 AND ntfs LIVE, and it is not where `unix-filesystem` lives. That distinction is
the point of the term: a path grammar is a property of the OS's API and a storage format is a
property of the volume, and NTFS mounted through ntfs-3g has unix paths, so a model that had one
axis for both could not describe an ordinary Windows disk read from Linux.

## terms[beanger].meaning

THE OPERATOR'S TERM, THEIR DESIGN AND THEIR NAME, 2026-08-07. BEAN + LEDGER: a per-datum ledger,
bean-structured. `log/journal.md` is the ledger of what the ESTATE did; a beanger is the ledger of
what ONE DATUM has been, and since 7.0 it has the same append-only record shape.

THE SPLIT: the CURRENT value stays on the bean, in `owns`, where a reader already looks and where
every existing ref already points. The beanger carries the DEFINITION, the way to READ it, and the
RECORD LOG. The first draft copied the current value in here, which duplicated the fact and would
have dragged RETIRED values into the single-owner IP scan — an address a being no longer holds must
not still be owned by it: a released address belongs to nobody.

WHY IT EXISTS, from this corpus: `owns.provides_ip: 203.0.113.10` is a definition and a value fused
into one scalar with NO DATE AT ALL. A re-scan of such a field cannot tell UNCHANGED from NEVER
LOOKED, and the day the value moves, when it moved is gone. Not hypothetical — a router's `owns
.wg_tunnel` carried an endpoint that HAD moved, .19 to .16, with nothing recording either fact.

THE FOUR OPERATIONS. `add`, `change` and `remove` move the value; `confirm` does not, and that is
precisely why it is the one that had to be invented. Without a record for "checked, and it was as
recorded", a re-scan that finds nothing new leaves no trace, and silence then means both "verified
this morning" and "nobody has looked since July". `confirm` is the operation that makes the ledger
able to say how CONFIDENT it is, separately from what it says.

WHAT IS DERIVED AND THEREFORE NOT STORED. `since` is the `at` of the newest add-or-change; `last_seen`
is the `at` of the newest record of any kind; `next` is simply the following element of an ORDERED
list. All three were stored fields in the first draft and all three are gone: a fact stated twice is
a fact that can disagree with itself, which is the argument this vocabulary already makes for
refusing a direction aspect. The chain is walkable both ways from `prev` plus list order, which is
what "walkable all ways" actually required.

## terms[beanger].record_attrs.seq

ONE LEVEL DEEPER THAN THE GATE VALIDATES, AND SAID SO RATHER THAN IMPLIED. The interpreter checks
the entries of a term, not the entries of a list INSIDE an entry, so everything below is convention
the gate does not yet enforce. That is a real gap and it is named here instead of being dressed up:
`attrs` reaches `beanger.<datum>`, not `beanger.<datum>.records[]`. Closing it needs
a nested-entry mechanism in bin/dmcheck.py — a GATE change, tracked in [[design-network-stack]].

## terms[workspace].meaning

WHERE A SESSION DOES ITS WORK. Added 7.0 with `bin/dmsession.py`, because several sessions on one
host is a thing the estate now wants and one working copy cannot give it: two sessions in one clone
share one git INDEX, so `git add -A` from either stages the other's half-finished edits, and the
gate reads the STAGED blobs. Session A can then be refused for session B's mistake, or commit B's
unfinished bean under A's message with A's journal entry attached. Both writes are individually
legal, so no rule in this ledger catches it.

A WORKTREE IS THE FIX AND THE BRANCH IS THE HAND-OFF. Each session gets its own working copy and its
own index while sharing one object store, so they cannot stage over each other — and they can still
read and merge one another's branches with no network hop, which is the sync-between-sessions half.

## terms[capture].meaning

THE THIRD STATE GROUND RULE 3 NOW ALLOWS, ratified 2026-08-07. Until today a fact was either OURS or
SOMEBODY ELSE'S, and somebody else's could only be POINTED at. That rule was written for a good
reason — a ledger that mirrors every device's config silently becomes a stale second copy of it —
and it has one fatal gap: A POINTER TO A MACHINE THAT HAS DIED REPRODUCES NOTHING. The operator
asked for beans complete enough to rebuild the estate, and a pointer cannot do that.

WHAT MAKES A CAPTURE SAFE IS THAT IT KNOWS WHAT IT IS. It names the thing it copied and who owns it,
the command that produced it, the moment it was taken, and the key by which a reader decides whether
it still holds. A copy carrying all four is useful; a copy carrying none is the stale mirror the old
rule feared, and the difference is entirely in the metadata rather than in the content.

A CAPTURE IS NEVER AUTHORITATIVE AND IS NEVER APPLIED BACK. It does not live in `owns`, so it is not
scanned as a fact this bean owns — the same reasoning that keeps a `beanger` archive out of the
single-owner IP check, because an address a being no longer holds must not still be owned by it.
Restoring FROM a capture means reading the source first and treating the capture as the thing to
compare against, not the thing to paste.

`redactions` IS REQUIRED, AND THAT IS THE WHOLE SECRETS DISCIPLINE. `no secrets` is founding here,
and a router export contains wireguard private keys, PPPoE passwords and community strings. Making
the field required means "nothing was removed" has to be WRITTEN DOWN as a claim somebody made,
rather than being the silent default of a field nobody filled in. An omission looks identical to a
clean capture; a required attr does not.

## terms[capture].schema.attrs.staleness_key

TWO WAYS A STALENESS KEY LIES, both met within an hour of this term being written and both worth
stating here rather than only on the bean that hit them. (1) THE SOURCE STAMPS ITSELF: a RouterOS
export carries its own generation time, so a plain hash of the output changes on every run even
when nothing changed — a key must be computed over the content with such lines excluded, and the
exclusion must be written INTO the key so the check is reproducible. (2) STORAGE REWRITES THE
BYTES: git's default text handling converted CRLF to LF on commit, so the stored copy hashed
differently from what the command produces. Captures need `-text` in `.gitattributes`. Neither is
exotic; both make the key report "changed" forever, which is as useless as never reporting it.

## terms[risks].meaning

ONE INVENTORY. Until 7.0 this estate kept TWO that did not know about each other, plus loose
findings in `details` on individual beans:
(1) one server's `details.risk_register` — 15 open findings as prose rows, ALL on that server
regardless of what they were about: a monitoring container, web vhosts on a VPS, a file share. None of
them is a fact about the server, and the bean that owns the failing thing could not be asked.
(2) `capabilities` entries sitting at `permission: forbidden` + `feasibility: possible`, which the
model already CALLS a live risk in the feasibility aspect's own commentary. Two of them exist
— a public-resolver exposure and a DNS recursion — and NEITHER appeared in the
register. Two inventories, no overlap, and no way to ask "what is wrong" once.

WHY NOT JUST FOLD EVERYTHING INTO `capabilities`, which was the first idea and is wrong. Most
findings do fit its grid — R1 and R4 and R6 are all "forbidden, and currently the case", which is
already an in_breach cell. But R13 is "unattended LUKS unlock UNPROVEN" and R14 is "LIKELY a 502",
and neither is a modal claim at all: they are EPISTEMIC, about what nobody has established. The
capability aspects can say a thing is impossible or contingent; they cannot say nobody has looked.
A register is full of exactly that, so forcing it into the grid would have silently converted "we
do not know" into "it is fine", which is the worst possible loss for a risk inventory.

`state` CARRIES THAT DISTINCTION and is the term's whole point. `live` and `latent` are the two the
capability grid could express; `unproven` is the one it could not and the one a register needs most.

## kinds[org]

== being-kinds for the ownership / type-token / habitat model (2026-08-02, human-ratified) ==

## kinds[person].ownership_form

a person may be owned ONLY by the crown (love, while alive) — never by a

## kinds[person].meaning

bean. This also RESERVES the crown form: no other kind may name the
axiom directly, so every other chain must pass through a being.

## kinds[host]

== kinds that were in USE but undeclared before P3. Under D1 a kind need only name the nature it
refines and what it means; anchor family + min-anchors come from that nature.

## recurrence_form

A repetition is what an instant and an extent were missing: an instant is a sequence restricted to one position, an
extent is a bounded region of one, and a recurrence is a sequence whose NEIGHBOUR RELATION IS GIVEN BY A RULE instead of
by listing — each occurrence is the one before it, shifted. It is the sequence that is unchanged when slid along itself.

There are three kinds of shift because a sequence offers three things to count in. Neighbours are what a sequence IS, so
a stride by neighbours needs no meter at all: it is how "every tenth release" is said of a line of events that has no
clock. A measure needs metering, and metering belongs to the system as much as to the aspect: place is not metered, and
geography is, in metres. A cell needs a level, and a level belongs to its system: a month is a level of ONE calendar,
which is why `each` refuses to stand without `in`.

A routine is what happens and a recurrence is when. They compose; they were never the same thing, which is why a routine
that must end could not hold a repetition that does not.

Considered and refused: a calendar bucket as a unit (`every: { count: 1, unit: month }`). A month is not a length — it
is 28 to 31 days in one calendar, 29 or 30 in another — and writing it as a measure would make arithmetic of something
that is not arithmetic.

## vacancies[registry:anchor_systems]

== ASPECTS (added 2026-08-02, std-vocab@2.1) ==
DIMENSION-AGNOSTIC. An aspect declares its own axes and the gate does not care how many: `poles` is one
contradictory PAIR, or a LIST of pairs. A figure may be 1-dimensional (a plain binary), 2 (a square),
3 (a cube), or more — what is required is that every declared axis runs between genuine opposites, so a
position is addressable along it. The count is DERIVED from the declaration, never assumed, because
assuming a count is exactly how a square silently mis-models a cube. Likewise a term's `cells`
are N-ary: they constrain ONE aspect or SEVERAL, and the machinery is the same either way.
An ASPECT is a CLOSED figure of positions — the operator's requirement that a classification have no
loose ends. A line has undefined extremes and forces partial membership; a closed figure does not, so
polarity lives in OPPOSED POSITIONS rather than at the ends of a scale. Each position names its
COMPLEMENT, which is what lets a being be addressed by opposition as well as by identity ("the light is
not where darkness is"). The gate enforces the sanity rules — closure, orientation, complement mutuality
— and names no aspect, so a new aspect is data, never a code change.
== POSITION SYSTEMS AND RESOLUTIONS NOT YET TAKEN (declared 5.1, 2026-08-07) ==
Declared here rather than left silent because the whole argument for naming an anchor system is that
an UNSTATED domain is what makes a negative result read as strong. A registry that quietly carried
systems nothing occupies would be committing the same error one level up.

## schema_language.values_from

A registry is its own enum owner. Five terms existed only to hold a `values` list equal to a registry's column, each
with a drift guard to keep the copy honest, and none was ever carried on a bean. The copy cost something every time a
registry grew: a release that added units restated all of them on the `unit` term, and a garden that added one row
stated it twice — the row, and the value on a term it did not own. `values_from: "registry:<name>[].<field>"` reads
the column where it lives, so there is no copy and nothing to guard. A position in a registry is addressed
`registry:<name>`, which is where a vacancy for an unused row is declared.

## journal.system

The journal kept its own copy of one calendar's form, as a pattern beside the system that already owned it: a second
spelling of a rule, and one that made a journal in any other calendar unwritable. A heading's moment is a position in
a calendar, so it is judged by that calendar's own form; the journal adds only what a JOURNAL needs — the minute, and
the offset. `any` is the default because a language has no calendar of its own; a garden that wants one names it.

## schema_language.attr_domains.system

`form_of` asks a sibling attribute which system a position is in. An attribute that is only ever in ONE system (a
moment a tool stamps is always `unix-epoch`) had no way to say so and stayed `untyped`, its form written in its
`meaning` for a reader and for nothing else.

## schema_language.attr_domains.key_of

A part of a being — a link, a volume, a capture — is named by its key, not by a ref: it is not a managed object and
joins no graph. Until 18.0 such a name was `untyped`, so a tunnel could ride a link that did not exist. The gate
resolves it and draws no edge.

## quantities

Area and volume are not new figures: they are an extent on a sequence with two or three lines, and the unit carries the
power. Speed and acceleration are not extents at all: they are RATES, a quantity per unit of another, which is a
negative power. One construct — a product of integer powers of a few base dimensions — says all of them, and it is the
model the SI and Unicode CLDR both publish, so nothing was invented.

A factor is a pair of whole numbers, never a decimal: five eighteenths of a metre per second is exact, 0.2777… is not,
and a canonical form must not depend on how a float was rounded.

Truncation is kept out at each of the four places it could enter. THE LAW: a factor is a pair of whole numbers in lowest
terms, checked by the gate, so no rounded constant can be declared. THE RECORD: a count is a whole number or a decimal
string, so nothing a float has already lost can be written down. THE ARITHMETIC: whole-number ratios only, so every
conversion between every pair of units comes back exactly, at any number of digits — the suite tries them all. THE
DISPLAY: a terminating decimal in full, anything else as a fraction. A fraction is exact and hard to read at a glance,
so a rounded decimal may stand BESIDE it, marked `≈`: the mark is what keeps it from being written back, because no
count may contain it. The rule was never that a reader may not see a decimal; it is that a rounded number may not pass
for the value. And a conversion is a reading, never a record: the measured value in its measured unit is the
fact, so an error cannot build up through a chain. What stays inexact is what is inexact in the world — a logarithmic
level turned back into a ratio, a great-circle distance — and those are computed for a reader and never stored as law.

A logarithmic quantity is marked because it COMPOSES differently: along a chain of links, attenuations add. That is one
instance of a wider idea — how a quantity composes along a walk (sum, product, or the weakest link, as a generated
fact's standing already does) — which is noted here and not yet built.

Considered and refused: temperature in degrees Celsius, which needs an offset as well as a factor; and compact strings
such as `12.5 m/s`, a second spelling of what `{ count, unit }` already says.

## terms[located_at]

== POSITION TERMS (added 5.1, human-ratified rule-change) ==
`located_at` and `timing` are the SAME STRUCTURE pointed at two dimensions, which is the whole claim:
sequence is general, and time and place are restrictions of it with different direction lines. They
are declared as two terms rather than one because what they are ASKED is different — where a being is
found, and when something happened — and a single term serving both would have to be read twice.

