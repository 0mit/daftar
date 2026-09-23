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

## schema_language.sums

PARTS ADD UP TO THEIR WHOLE, EXACTLY. A construct, not a rule on one term: whatever holds the parts of a measured
whole — the payments of a price, the shares of a stake — declares it, and the gate checks it in fractions whenever
every count is known, the parts in the whole's own unit. An entry holding a single part that states no amount holds
the whole, because "Ali paid" should not need the price written twice. `whole` may name several attributes and the
first the entry states is the whole, so a purchase charged in another currency is checked against what was charged.
Checked exactly or not at all: a sum that is nearly right is a sum that is wrong, and a tolerance would have to be
somebody's choice of how wrong.

## schema_language.expiry

PER ENTRY, REPEATING, AND SILENT ONCE MET. `expiry` was written for a term with one date — a registration runs
out. The first obligations recorded were many to one term, each with its own day, some repeating: six instalments
are one clause that falls due six times. So on a list or an open map the attribute is each entry's; `repeats` names
the entry's own recurrence, and the reader is warned before the NEXT occurrence rather than the first; and `unless`
names the states in which an entry no longer lapses — a debt already met, waived or broken is not coming due. The
tool that reads it stays outside the gate for the reason the construct has always given: an answer that changes
with the calendar would make the gate fail on a day for no committed reason.

`notice` is an extent because a notice period is a region of time. It was a bare integer of days for one release
(until 11.2) — a fifth way of saying a duration in a vocabulary that had just declared the first. And
`expiry` is declared by the term rather than derived from an attribute's type because, measured when it was written,
ten terms carried an iso_date and nine of them were `observed` or `as_of`: the day a fact was read, not the day it
runs out.

## schema_language.only_on_kinds

THE MIRROR OF `required_on_kinds`. The language could say that a kind of being must carry a term and not that only
it may, so a term that is a fact about one kind of being — that another garden is a rehearsal — could sit on a person,
where nothing reads it. The alternative was the gate naming the term and the kind in its code, which is the one thing
the interpreter does not do.

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

## identity_policy.anchor_key

AN OPEN KEY WAS AN OPEN MERGE KEY (19.0). Identity is matched by (key, value), and until 19.0 the key was any
string a bean wrote. The fourth cold-start drill invented a key, product_name, and the gate took it; measured, the
first garden's beans carried seventeen keys no term declared — `product_id`, `session_id`, `service_id`, the
ids the kinds registry had NAMED IN PROSE since P3 and never declared. Two gardens spelling one anchor model
and product_name would never recognise the same object, which is the one thing identity anchors exist to do.
So the key names a term that declares `anchor:`, and the gate refuses any other. A garden-local key is a local
term with an anchor policy — the same mechanism every other position has used since 18.x — and a local term
that proves general is promoted, which is how eleven arrived in the standard at once.

## identity_policy.anchor_attrs

WHAT AN ANCHOR MAY CARRY, DECLARED (20.0). Until then an anchor entry took any key: `scope`, `observed`,
`until`, `authority` all rode along, none declared, and `authority` — `scanned < operator-asserted < external`
— was a second vocabulary for the one question `provenance_src` answers. Measured on the first garden's 170
anchors: 136 `scanned` on `observed` beans and 20 `operator-asserted` on `asserted-by-human` beans said
nothing the bean had not said; 12 disagreed with their bean (`scanned` on `inferred` ×10); 1 said `external`,
which the other vocabulary has no word for because it is not a source but an authority's say-so — an
observation of a registry. So an anchor says how it is known the way every entry has since MODEL v2: a
`provenance: { src, by, as_of }` record where its source differs from the bean's, and nothing where it does
not; the gate refuses `authority` with that hint, and warns on a record that only repeats the bean's own.
The merge ranks two records of one anchor by `provenance_src`, as it ranks every other value.

## identity_policy.establishing_family

THE REGISTRY SAID IT; THE GATE CHECKED ONLY THE COUNT (19.0). `establishing_anchor_family` has been in every
nature's row since P3, and `dmrules` printed it under "every rule below is enforced", while `dmcheck` read only
`min_establishing_anchors`. The drilled stranger found the gap by reading the gate's source, which a user
should never need to do. The family is now enforced as an error on a confirmed bean: what establishes a
physical being is its matter, and a name that establishes it would fuse a replaced machine with the one that
kept its name — exactly the `id` term's oldest exception. What broke under enforcement was instructive: one
rented VPS anchored on its name, and three physical machines whose `fqdn` was establishing beside a real
serial. The VPS was of the wrong nature (see `kinds[virtual-host]`); the names were demoted to corroborating,
which is what they had always been.

## identity_policy.minted

A NAME CARRIES ITS BIRTHPLACE. Every anchor once said `scope: global`, which no tool read and which was false of
every name a garden had minted: `person:sam` is unique in the garden that chose it and nowhere else. Two failures
were measured, and they pull opposite ways. A stranger's garden recorded its agreements with no anchor at all, and
a merge of it against a copy of itself saw two records as four: nothing let two gardens agree on a name. And an
isolated run made up a person id that happened to equal one another garden already used for someone else, and
the merge fused two people into one: a name that means nothing beyond its garden was treated as if it identified.

So a value of a term marked `minted` is BARE — it identifies within its garden, and fuses only there — or QUALIFIED
by the id of the garden that minted it, and then it identifies everywhere. Equal bare names from two gardens are
candidates for a person, never fused by a tool. The prefix is the garden's id because that id is assigned by no one
and legible on paper; the bare name is unchanged, so qualifying is prepending, and nothing a garden already wrote is
rewritten. A name is qualified ONCE, by the garden that recorded the thing first, and every garden that takes it in
keeps it byte for byte: a name re-minted on arrival is two names again. A gardener planted at germination is
qualified at birth, because the garden's id exists from its first commit: the one name every agreement the garden
makes will carry needs no minting later. The gate holds the prefix to a garden this
one knows, so a foreign name always arrives with the garden that gave it.

Considered and refused: a UUID (canonical, and illegible cold, on paper); a tag URI (it needs a domain or an e-mail
address, which would put personal data into every anchor); an anchor made of a source and a position in it (two
people recording one dealing from two sources would still see two); a garden that mints names for the others (a
privileged sibling, which the language does not have).

## identity_policy.minted.form

A NAME A GARDEN GAVE HAS A FORM. `minted` was first a property of the term alone, and the terms' own meanings admit
values no garden gave: a program is known by its package name, an organisation by a registry number, a happening by
the UID its invitation carries, a virtual machine by the id its provider assigned. Read as names a garden gave, the
same package name in two gardens was two programs and a candidate for a person to join, where it had always fused;
and the remedy the law prescribed — put the garden's id in front — would have said that one garden gave Postfix its
name, which is false provenance. The meanings already wrote a minted name one way, `product:<name>`, so that form
became structure: `<kind>:<name>`, the kind one the garden knows, is a name a garden gave; any other value was
assigned outside every garden, identifies wherever it is written, fuses as every anchor always did, and is never
qualified — the gate refuses `<garden_id>/postfix`. The kind must be a kind the garden knows so that a colon inside an
outside identifier (`urn:…`, `mailto:…`) is not taken for a name a garden gave.

Considered and refused: splitting each term in two, one for identifiers assigned outside and one for names a garden
mints (eleven more terms, and a stranger choosing between two words for one identity); taking `minted` off the terms
whose meanings admit an outside assigner (then a garden could not name an organisation that has no registry number —
most of the people and groups a household deals with).

## manifest

GARDEN.md WAS JUDGED BY NOTHING. The law declared none of its keys, so any key passed; the template carried
`created: "git-metadata"`, a key whose only content said it had none, and `seeds_from: []`, which no tool read or
wrote. Now the manifest is judged AS ITSELF, by every rule an entry answers to: each key says what it is a position
in, a required one must be there, an undeclared one is refused, and a retired one says where it went. It was first
judged as one entry of a list, where its attributes — declared for the mapping itself — were read by nothing but the
key check: a gardener naming no bean, a manifest with no `garden:` or no `extends:`, a release nobody made, all passed.

`gardener` is the key a stranger's garden was missing. With no place to say whose garden it was, an agent wrote the
person who keeps it as an outside owner, in prose, inside that person's own garden. The gardener is a bean of the
garden — a being that can be anchored, owned and asked, like any other — and is required once the garden holds a
bean rather than at germination, so an empty garden still passes its first gate and the first thing it asks for is
the person who keeps it. `test` exists because a rehearsal of someone's garden must never pass for their word; it is
the sending garden's own statement, and the receiving garden keeps its own (`terms[test]`).

A garden's identity is deliberately not a key. It is read from git, as the product version is, because a copy typed
into a document is a second copy, and a second copy can disagree.

## manifest.attrs.gardener

WHO MAY KEEP A GARDEN IS THE LAW'S TO SAY: a person, or an organisation — a family business, a club — and never a
machine or a product, which cannot be asked. The list was written in the gate and in the upgrade tool, two copies in
code and none in the law, while the hint for a retired name had already moved into the law for the same reason.
`in: { bean_id: { kinds } }` states it as structure, the one place both tools read. The gardener is not required to
be the garden's first bean: it is the first of a garden grown with `--gardener`, and a garden upgraded into 21.0 names
a person it has held for years.

## manifest.attrs.daftar_release

A release, or `untagged <commit>`: a garden grown from a checkout on no tag records the commit it runs, exactly as
`seed/germinate.py` writes it — `untagged unknown` where even that could not be read — and a pattern that admitted only
a tag would have refused every garden grown to have a look around. The note germinate prints says why such a garden
should adopt a release.

## retired

A REFUSAL SAYS WHERE IT WENT. A name the law took back was refused as "declared by no term", which tells a writer
what is wrong and not what to write instead; for one release the hint for the anchor's `authority` lived in the
gate — a rule stated in a tool, not in the law. `retired` states each name, where it was written (an anchor, a bean,
a term, a schema, the manifest) and where it went, and the gate keeps no list of its own.

What went, and why. `scope`: read by nothing, and false on every minted name; the term and the name's own form say
it now. `between`, `agreement_ref`, `conflict_rule`: declared with no schema, so each checked nothing; `parties`,
`words` and a clause say it with structure. `balance`: a stored copy of what the transactions say, which drifts.
`attributes`: a second bag for the one purpose `details` serves. The `facets` term: three prose rules that nothing
checked, now a registry whose walk is checked. `values_consistent_with`: a guard against a list's own copies, whose
last user became registry rows. `seeds_from`, `created`, `models`: manifest keys that nothing read; what a garden
took in is in its journal and in the captures on the other garden's `garden` bean, when a garden began is its first
commit, and who wrote there is in the journal and in git.

## provenance_record

THE RECORD EVERY FACT CARRIES, DECLARED. The merge has read `from` since a generated fact first borrowed the
weakest standing of what it names, and the law declared nothing about it, so a provenance record took any key. It
declares five now. `from` also gives a person's words read in a transcript an honest form: the fact is theirs —
`asserted-by-human`, by them — and `from` names the document it was read from, where the alternative was to call it
an observation of a file, which says the wrong thing about who said it.

`garden` is the one attribute a crossing adds. It is stamped once, by the garden a record was made in, when a
proposal carries the fact across, and never changed — so an assertion that arrives from another garden is still that
person's assertion, and the guard that an inference never overrides it holds across the boundary without a single
new rule. It must name a garden this one knows: a fact from a garden nobody recorded has no one to ask.

## natures[physical].crown

Extension owns physical beings

## natures[physical].establishing_anchor_family

serial / mac — bound to the matter itself. (`wg_pubkey` was listed here until 19.0; it never was.)

## natures[living].establishing_anchor_family

Logical: a person's minted id or signing key, an instance's deployment coordinate, a VM's instance id. Until
19.0 the row also named `personal`, a class `anchor_class` has never offered — a position no anchor could occupy.
It would have meant a passport number or a biometric, which the ledger never records because they are secrets;
the name was withdrawn rather than given a class nothing may honestly fill.

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

## system_shape.reckoning

A DAY ITS CALENDAR DOES NOT HAVE IS NOT A DATE. A pattern admits `persian:1404-12-30` and `2026-02-30` alike, and
each reader did something different with them: the Persian date moved silently to the first of Farvardin, so a clause
meant for the thirtieth fell due on the first of every month, and the Gregorian one was dropped by one reader and
refused by another. For a calendar reckoned by rule (`arithmetic`), the arithmetic that converts a date also judges it:
the day a position names, written back in its own calendar, must be the position written. A year outside the range a
calendar's reckoning is good for is refused the same way, by name and never by a traceback. The other reckonings —
astronomical, observational, tabulated — cannot be judged by arithmetic, and are not.

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

ONE ROOT (`rooted`). `legal` is the facet every other reaches — whoever owns a thing in law answers for it in the
end — and that was a sentence nothing checked: a garden could add a facet that depends on nothing and so have two
lattices. `rooted` says that exactly one row names no link and that every other reaches it, and the gate holds the
facets to it.

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

## value_types[count]

A NUMBER IS WHAT WAS WRITTEN, AND EVERY READER HOLDS IT. YAML 1.1 reads a plain `010` as eight, `0x64` as a hundred,
`1:30` as ninety and `1_000` as a thousand; the gate took each for a whole number, and every reader agreed on an
amount nobody wrote. The one loader now reads a plain scalar as an integer only in plain decimal, and this form
refuses every other spelling by name — a leading zero among them, since `010` is a spelling of ten nobody writes and
of eight that YAML reads. Forty digits before the point and forty after hold any amount a person owes and any rate,
and lie far inside what every reader holds exactly: a count past Python's four-thousand-digit limit passed the gate and
ended the ledger in a traceback. A share is bounded the same way.

The count keeps what was written. A merge compares counts by the exact value they write, so `900`, `"900"` and
`"900.00"` are one amount and never a conflict — the shortest exact decimal is the one canonical form.

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


## journal.heading

STAMPED, NOT TYPED (20.0). 10.0 made a heading a position in time and the gate checks its form; the truth of
the moment it never could. The evening this was written, the same writer typed the time before reading the
clock twice in five hours — 20:06 for 19:52, 22:31 for 22:09 — and both headings were of perfect form. The
gate cannot tell a measured moment from a remembered one by looking at it. What it can tell is whether the
clock-reading tool wrote it: `bin/dmjournal.py` records every heading it writes in the clone's own git
directory, and the gate refuses a heading a commit adds that is not there. The register is never versioned
and proves only what a pre-commit hook can honestly prove — that this clone's tool stamped it — which is
enough, because the failure it answers is a hand typing. `dmupgrade` writes its entry through the same tool,
with git's author as the who and the ratifier as a body line to fill in: a fill-in inside the heading would
have changed the heading after it was stamped.

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

## registry_files[currencies]

FROM UNICODE CLDR, NOT FROM ISO 4217 DIRECTLY. The standard's own list states no terms of redistribution where it is
published; CLDR carries the same codes and numbers under the Unicode licence, and is already the source the calendars
were taken from. Its decimal places follow use where they differ from ISO's minor unit, and a count is held to what
people actually write. A redenomination arrives as a new code and the old one stays, historic, so an old amount can
still be said.

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

## profiles.network.terms[endpoints].schema.attrs.admitted_from

WHERE A SURFACE IS BOUND AND WHO MAY REACH IT ARE TWO FACTS. `exposure` is the first: `internet` means bound to a
public address, and it stays true after a filter is put in front of the surface. A fifth `exposure` value —
"internet, but filtered" — would fold the second fact into the first, and the next kind of admission (a tunnel, a
port knock, mutual TLS) would want a sixth. So the second fact has its own attribute. It is prose for now: the
things that admit a source — an address list on a router, a security group, a service's own allow rule — are not
a term, so there is nothing for it to be a `key_of`. When they become one, this attribute should point at it.

## profiles.network.terms[endpoints].schema.cells[·]

LOOPBACK is excluded: there is no path there for anything to be on.

THE MANAGEMENT CELL IS AN EXPECTATION, NOT A VERDICT. As a verdict (`in_breach` on management + internet) it
recommended restricting the surface to named sources — and went on firing after that was done, because the
surface was still bound to a public address and the law had no way to say who it admitted. A warning that outlives
its fix teaches a reader to ignore warnings. As `expects: [admitted_from]` it asks the one question that matters
and is silent once it is answered. What it checks is that the words are there, not that the filter works: that
stays the writer's honesty, as everywhere.

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

## terms[anchor_class]

DECIDES AGAIN (19.0). P4 made `establishing` the load-bearing flag and left `class` as a hint. The family rule
reads the class of every establishing anchor against the nature's family, so the hint is a rule once more: a
term that governs the key declares the class, and the bean writes the flag that follows. `none` went with the
three pseudo-anchors that carried it (`id`, `ref`, `shell-log`): under `anchor_key: term` a term with an
`anchor:` block is an anchor key, and those three were never anchors. `shell-log` itself, a v0.2 note on how an
agent logs shell work, was retired: the `journal` registry says it now.

## terms[owned_by].schema.required

Universal since 19.0. `required_on_kinds: [product, codebase, instance, org]` was the list from before the two
arcs were closed; MODEL.md has said "every bean carries both" since v2, and the corpus check proves it on every
commit. A list that names four kinds when the rule holds for all is a second copy waiting to disagree.

## terms[status]

`at-risk` was a value until 19.0, declared vacant since 2026-08-08 as "the one status that asks for action".
The `risks` term arrived after that note and carries the state (`live`) with the consequence and the evidence
beside it — a lifecycle enum cannot. A risk state inside a lifecycle was one fact in two positions.

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
bin/dmmerge.py, the oldest rule in the system kept as a constant in a tool. (Until 20.0 a second term declared a
rank of its own for anchors — anchor authority; it is this one now.) The merge reads it for two things: which src a value several gardens agree
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
Co-ownership of a SINGLE facet is never a raw fact -> a `contract` bean: its `parties`, its `words`, and the clause
that settles a disagreement between the owners.

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

## facets

THE OWNERSHIP-FACET LATTICE, as a registry. A facet is DISTINGUISHABLE (a crisp boundary; overlap is resolved by a
`depends_on` edge or by refining a boundary, never by double coverage — which stays a judgment for whoever adds a row),
DEPENDENCY-BEARING (every facet but `legal` depends on another, and the walk never returns — `registry_links` declares it
`acyclic`, so the gate checks what the old term only stated), and RECURSIVE (a garden decomposes a facet by adding rows that
depend on it: `operational` under `technical`). It was a term whose three rules nothing checked and which offered no values
at Tier-0, so in a garden grown from the seed ANY facet key passed: the lattice MODEL.md describes lived only in one garden's
overlay, stated five times over. As a registry it is stated once, read by `owned_by` and `responsibility` through
`key_form`, and a garden adds a facet the way it adds any row. `experience` and `financial` are in the standard because a
stranger's garden expects them: who designs how people meet a thing, and who pays for it.

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

DNS-unique within its namespace. Until 19.0 the policy pinned `establishing: true`, which with the family
enforced would have forbidden a physical machine any `fqdn` anchor at all. The nature decides whether a name
establishes; the pin was dropped so the bean can write the flag that follows: `true` on a domain, a service or a
virtual-host; `false` on a machine, and on an org, whose name would otherwise fuse it with its own domain bean.

## terms[mac].merge

a host may have several NICs

## terms[serial].schema.governs_anchor

NO PATTERN: serials are vendor-shaped, and inventing one would reject valid data to look thorough. But they
are COMPARED case- and space-insensitively (9.0): no vendor issues two serials differing only by case, and
a drill committed `syn-0042` beside `SYN-0042` as two machines with 0 errors.

## terms[wg_pubkey].anchor

A CREDENTIAL, NOT MATTER (19.0). Classed `hardware` at v1.0, a day before natures existed, when two machines
had nothing else to be confirmed by. A key pair is generated on a machine but is not of it: it is copied when a
VPS is migrated and the peer stays who it was, and regenerated on the same box and the same machine becomes a
stranger — which is what `ssh_key_fingerprint`'s own meaning says ("what a host proves itself with") and what
`openpgp_fingerprint` was classed as from the start. So both key terms are `logical`, and unpinned: for a living
or metaphysical being a key is the strongest logical anchor there is; for a physical one it corroborates.

## terms[mac].anchor

Matter when burned in; assigned when virtual. A physical NIC's MAC establishes the machine; a virtual NIC's is
written by the hypervisor and moves with the VM's definition, so on a `virtual-host` it can only corroborate.
The class stays `hardware` — that is what the fact is — and the pin was dropped at 19.0 so the family rule can
say which.

## terms[product_id]

Declared at 19.0 with `service_id`, `org_id`, `person_id`, `program_id`, `contract_id`, `design_id`, `doc_id`,
`manifest_id`, `session_id`, `instance_id` and `email`: the ids the kinds registry had named in prose since P3
("Establishing anchor: a logical product_id") and the first garden had used all along, made terms when
`identity_policy.anchor_key` required every key to be one. All logical; none declares a form, because each is
whatever its home assigns or the estate mints once. `manifest_id` and `email` leave `establishing` to the bean
— a module's name corroborates beside the git remote that establishes, and an address is reassigned.

## terms[garden_id]

A GARDEN IS KNOWN BY THE COMMIT IT GERMINATED FROM. Content-addressed: assigned by no registry and no person, the
same in every clone, and changed by nothing but a new history — so a clone is the same garden and a copy given a
fresh `git init` is another, which is exactly the difference between a clone and a rehearsal. The root of the
FIRST-PARENT history, so a history merged in later never changes it. Twelve hexadecimal digits, the length at which
a large project cites a commit: one spelling, fixed, for a value compared by equality, and short enough to read on
paper in front of a name.

A name was refused, because two gardens on one machine may carry the same one: a garden is named after its folder.
And the commit itself had to be made unique. Germination makes it under a fixed identity with a fixed tree and
message, so two gardens given one name, grown from one release in the same second, made the same commit and would
have been taken for one garden. A random seed written into the commit's message makes each germination's commit its
own, and the id is still assigned by no one.
A UUID was refused: canonical, and illegible cold. Like the product version, the id is read from git and written in
no document of the garden itself; it is written only where git cannot be read — on another garden's `garden` bean,
in a proposal, and before a name the garden minted. A shallow clone cannot see its root, and has no identity to
offer until it can.

## terms[content_hash]

A document kept whole is identified by its own bytes. The SHA-256 of them names one content in every garden that
holds it, needs no home and no registry, and a changed byte is another thing — which is right for a statement
downloaded from a bank or a conversation saved as a transcript, the documents that have no id of their own.
`doc_id` stays for a document whose home names it.

## terms[event_id]

A happening has an identity where it is kept — the UID an invitation carries — or one a garden mints once. Minted,
because two gardens recording one dinner will each name it, and the name must be qualified before it crosses.

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

## terms[test]

A REHEARSAL IS MARKED BY THE GARDEN THAT RECEIVES IT. The manifest's `test:` is the sending garden's word that it is
a rehearsal, and a proposal carries it — a word the sender controls, which cannot be what keeps a rehearsal from
passing for a person's word: removed, and the fingerprint computed again, the proposal read as the real garden's. So
the receiving garden records it itself, on its `garden` bean for the other — its own record, which no proposal can
remove — and taking a proposal treats it as a rehearsal when either says so. Only a `garden` bean may carry it: it is
a fact about a garden.

A rehearsal is grown by germination, never by clone. A clone has its original's `garden_id`, so it IS that garden and
its word is that garden's word; there is nothing a receiving garden could mark it by, and the gate refuses a `garden`
bean anchored by the garden's own id.

## terms[parties]

AN AGREEMENT IS STRUCTURE. The five contract keys were declared without a schema, so each checked nothing; the first
agreements a stranger recorded put every party, sum and condition in free keys under `details`, and the one agreement in
the reference garden stated its parties twice and its object twice. `parties`, `words`, `clauses` and `transactions` say
who is bound (each with the day they accepted: an offer is not an acceptance, and one party's report of another's consent
is not that party's word), where the words are, what each must, may or must not do (the `capability` square, which a
being's capabilities already take), and what has moved. A balance is not among them: it is read, never stored.

A party without `accepted` has no acceptance ON RECORD, and the meaning says exactly that. It first said the party
"has not said yes", which reads silence as refusal: an agreement spoken aloud and kept to, whose yes nobody wrote
down, would have been recorded as refused by the people keeping it.

## terms[parties].merge

MEMBER BY MEMBER, keyed by the party's short name — the name every clause and transaction uses to say who. The first
draft merged the parties as one atom, on the argument that they are constitutive: unioning two gardens' lists could add
a party nobody agreed to. Built, it did worse: any difference in any party — one garden knowing an acceptance the other
does not yet — turned the whole map into a conflict, and every clause naming a party then named nothing, so the merged
agreement failed its own gate. Per member, a disagreement about one party stays on that party, and the others keep
their names. The danger the atom guarded against is met where it belongs: a party only one side names is a difference
`dmpropose read` shows before anything is taken in, and the gardener decides.

## terms[parties].schema.attrs.accepted

TAKING IS NOT ACCEPTING. Taking another garden's proposal in records what that garden offers; it is not the
receiving gardener saying yes to an agreement, and a tool that wrote it so would put words in a person's mouth. The
receiving gardener accepts by writing `parties.<them>.accepted` in a commit of their own — the commit is the
ratification, and the entry's provenance says whose word it is.

## terms[over].merge

A SET of what the agreement concerns. It was a single reference capsule, one thing like `lives_in`; an agreement between
people is often about several things at once — two purchases on one receipt — and two gardens that each name one of
them both keep theirs. What would be dangerous to union is who is bound, and that is `parties`, which stays single.

## terms[words]

WHERE THE WORDS ARE. An agreement is written, spoken, or named before anyone has put its terms into words, and each
is a real state: a spoken agreement binds its parties as a written one does, and the record must not pretend a text
exists. `at` names the document that holds the text or the happening at which it was said, so the words can be found
again, and a written agreement must name its document. `unstated` keeps an agreement both parties refer to, whose
terms nobody has said, from being either dropped or invented.

## terms[clauses]

WHAT AN AGREEMENT ASKS, ON A SQUARE THE LAW ALREADY HAS. An obligation is a position of deontic logic — must, need
not, may, must not — and the `capability` aspect already is that square, taken by a being's capabilities. A clause
takes it too, rather than a fifth word for the same four. `by` and `to` are keys of the parties, so a clause binds
someone the agreement names; the amount is any quantity, because what is owed is not always money; a recurrence
makes six monthly instalments one clause and not six; and a condition that is not a date — interest on an
instalment paid late — is prose in `when`, because the reason IS the fact. `state` records what became of it; the
balance it implies is read, never stored.

## terms[transactions]

WHAT MOVED, AND NOTHING DERIVED FROM IT. A transaction records the inputs — an amount, who paid how much of it, and
who bears it in what shares — and what one party owes another is the output, read by a tool. The first agreement a
stranger recorded stored the output beside its inputs, and a stored balance is a second copy that the next payment
makes wrong. Shares are whole numbers because a share is a ratio the parties said — two to one — and whole numbers
keep the arithmetic exact; a split that does not come out even is shown as a fraction and settled by a clause.
`charged` keeps what a card was charged in another currency beside the price, both as the statement shows them; the
rate between them is read from the two, never stored. `sums` has the gate check that what was paid adds up exactly
to the whole.

The day it moved is `day`. It was `on` in the first draft, and YAML 1.1 reads a bare `on` as the boolean true: every
parser received the attribute as a key that was not a name, the gate crashed on a transaction that carried it beside
an undeclared attribute, and no bean carrying it could cross to another garden. A key is text, and the gate now
refuses any key YAML reads as a boolean or a number.

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

## terms[volumes].reproduction_note

SCOPE, STATED BECAUSE IT IS ABOUT TO GROW. This term records the LAYOUT — what exists, what carries
what, and where it is mounted — which is what a rebuild needs to recreate the shape. It does NOT
record contents, keys or passphrases, and it must not: `no secrets` is a founding rule of this
ledger. The operator has asked for beans complete enough to reproduce a machine, and the honest
remaining gap is CONFIGURATION, which is a separate question from layout because config is
SOMEBODY ELSE'S authoritative truth and ground rule 3 forbids mirroring it.

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

## system_shape.checked_by

A form that a well-used tool already checks completely is checked by that tool. The `ipv4` row carried a pattern that
admitted `256.1.1.1`; tightened by hand, it was still a copy — of a validator the standard library has shipped for
years, which the `ip` anchor beside it had always used, and which the software this language describes uses too. A
hand-written copy of a validator is wrong in ways nobody has found yet. So a row names the check or states a pattern,
never both, and the names are a closed list the tools must actually carry. The library's OWN spelling is the one form:
that is what makes two gardens' addresses comparable as text, which is how a ledger compares them.

## schema_language.attr_domains.entries

The interpreter judged the entries of a term and not the entries of a list INSIDE an entry, so a datum's records — the
one place the ledger stamps to the millisecond — were described in a map of sentences that nothing read, and their
attribute was the last to say `untyped`. Nested entries are entries: the same controllers, the same closed set of
attributes, so there is no second and weaker kind of rule one level down. A ref inside one is resolved and draws no
edge, because the graph is made of what a bean states at its own level.

`keyed_by` says a list of entries is a set keyed by one of their attributes. The payers of a transaction are a
list, and a list has an order and admits a repeat: `[sam, ali]` and `[ali, sam]` were two values to a merge — a
disagreement for a person to settle that was none — and two entries for one payer counted that payer's part twice.
Keyed by `party`, the order carries nothing, a merge compares the list in the key's order, and a second entry for one
party is refused. A map keyed by the party would say the same by structure; it was refused because every payment
already recorded is written as a list, and each would have had to be rewritten to say nothing new.

## schema_language.attr_domains.any

`untyped` says nobody has decided. Some attributes have been decided and the decision is "anything": a record's `value`
is whatever the field it tracks holds, and typing it twice would be the second copy this language keeps removing.
Saying `any` keeps that apart from a debt, so the count of `untyped` means what it says — and it is now zero.

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

bean. This also RESERVES the crown form: only a kind whose row names it may name the axiom directly — a
person, and since 21.0 an agreement and a happening between people — so every other chain must pass through a
being.

## kinds[host]

== kinds that were in USE but undeclared before P3. Under D1 a kind need only name the nature it
refines and what it means; anchor family + min-anchors come from that nature.

Until 19.0 every row also carried prose `schema:`, `required:` and `min_anchors:` — second copies of what the
natures registry, `required_on_kinds` and the anchor terms decide, and by 19.0 three of them disagreed with the
law (`org`: "or primary domain"; `person`: "email"; `codebase`: "a logical manifest id" — all corroborating
now). A row is its nature and its meaning; what a kind typically owns is the cookbook's to show. The 7.0
story of `vps` and `router` retiring into `host` moved here from the row's meaning: `vps` described tenancy,
which ownership carries; `router` a role, which `roles` carries; and the registry noted against itself that
"D5 will re-read this as an instance living_on a provider" — which `virtual-host` is.

Narrowed at 19.0 to matter: 7.0 had widened it to "bare metal or virtual" when `vps` was retired, and a
virtual machine is a `virtual-host` now — see there.

## kinds[virtual-host]

A VIRTUAL MACHINE IS A LIVING BEING (19.0). At 7.0 `vps` was retired into `host` because it described TENANCY,
which ownership already carried — and the registry noted, against itself, that "D5 will re-read this as an
instance living_on a provider". Enforcing the anchor family (see `identity_policy.establishing_family`) forced
the reading: a VM has no matter, so under `host` (physical, family `hardware`) it could never be confirmed
honestly — the one rented VPS in the first garden was anchored on its name, and another carried its OpenStack
instance UUID as a `serial`, `class: hardware`, and sat provisional. What a VM IS is a running machine-instance
on a hypervisor: created, running, torn down. That is the living nature, whose crown `love` "lapses at death or
teardown", and whose family is logical — a name or the id its provider assigns (`instance_id`). Tenancy stays
where it was: a rented VM is owned `external` and answered for here; a VM on the estate's own hypervisor is
owned through it and `lives_in` it. A rented BARE-METAL server stays a `host`: it has a serial, and ownership
was always orthogonal to nature.

## kinds[contract]

AN AGREEMENT IS OWNED BY NONE OF ITS PARTIES. The kind meant co-ownership of one facet of one being, and had no
occupant as that; the agreements people record are between them — a cost shared, a loan repaid. Were each garden to
write its own gardener as the owner, two gardens' records of one agreement would disagree about its owner on every
fusion. So the chain may end at the crown — `logos`, for a being of meaning — as a person's ends at `love`, and the
parties, who can be asked, answer for it: `responsibility_form: [parties]`, reflexive like `self`, drawing no edge.
The crown owns and never answers; the parties answer and never own. The form is a LIST, which ALLOWS the crown beside
the ordinary forms instead of pinning it: an agreement one person wrote and offers may still be owned by its author.
Co-owning one facet through a contract stays one use of it.

## kinds[garden]

ANOTHER GARDEN IS A BEING. A garden this one deals with needs an identity to name — in a proposal, before a
qualified name, in a record's provenance — and an owner who can be asked; so it is a bean, anchored by `garden_id`,
owned by its gardener and answered for by them. A garden's own identity and its own gardener are never in a bean of
its own: git holds the one and the manifest names the other, and a garden describing itself would be a second copy
of both.

So the gate refuses a `garden` bean anchored by the garden's own id: it would be the garden describing itself — or a
clone recorded as a rehearsal, which is the same garden under another folder name.

## kinds[document]

`doc_id` promised a document since it was declared, and there was no kind to anchor with it. A document is a being:
it has an owner who is often not its holder — a bank's statement is the bank's — an identity, and copies in places.
What must not be kept whole stays out of it: a transcription of its lines is a `capture` on it, whose `redactions`
say what was left out and why, so a card number is never in the ledger and its absence is on the record.

## kinds[event]

A HAPPENING IS WHERE THINGS ARE AGREED. An agreement spoken over dinner or in a call has its words at that
happening, and a happening must be a being to be pointed at. Its time is `timing`, at the resolution actually known;
who took part is `refs`, each naming what they were, because `rel` is open and the parts people play at a meeting are
not a closed list. A work session is a happening too, and keeps its own kind while the two are told apart by use.

A HAPPENING BETWEEN PEOPLE IS OWNED BY NONE OF THEM. Written first with the host as its owner, a dinner recorded in
the host's garden and in a guest's would disagree about its owner every time the two records met, as two records of
one agreement would; and nobody owns an evening they shared. So it may end at the crown, `logos`, as an agreement
may. It is answered for by whoever hosted it — a holder, one being who can be asked — and not by the `parties` form,
because a happening binds no one to anything.

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

## recurrence_form.times

Instalments end by count as often as by date — six payments — and a recurrence that could only end at a position
would make a writer compute the last day, which is exactly the arithmetic a record should not ask of its writer. With
both `to` and `times`, whichever comes first ends it, as an agreement that says "six payments, and none after the
year's end" means.

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

## quantities[money]

MONEY IS MEASURED, AND A RATE IS NOT A LAW. One quantity whose units are the rows of a currency registry, with no
factor between any two — `crosswalk: observed`, the calendars' word for systems joined only by observation. A factor
would say that the rate between two currencies is a law of the language; it is a reading someone made at a moment
from a source. So every amount stays in the currency it was paid or owed in, a conversion needs a rate someone
recorded, and what it produces is a reading, never a record.

A quantity per currency was considered — each its own dimension, as some quantities are kept apart in ISO 80000 — so
that adding two currencies would be a type error for free. It costs a row per currency and a special case in the
unit machinery, and one quantity with no factor gives the same refusal: nothing converts across currencies without
a rate. Denominations are written in the major unit.

EXACTNESS, CARRIED FROM LENGTHS TO MONEY. A count is a whole number or a decimal string, never a float, with no more
places than the currency uses; every sum, share and balance is a fraction; and a share that does not come out even
is printed as the fraction it is and flagged, never rounded. Who takes the odd minor unit is something the parties
agree, in a clause — arithmetic that decides it has decided something that was theirs.

## quantities[ratio]

A part of a whole, or a rate — a share of a cost, a rate of interest — needs a unit as much as a length does, or
`1` could mean the whole or one percent. Dimensionless, linear, and four units: the whole, the percent, the per mille
and the basis point in which rates of interest are quoted.

## terms[located_at]

== POSITION TERMS (added 5.1, human-ratified rule-change) ==
`located_at` and `timing` are the SAME STRUCTURE pointed at two dimensions, which is the whole claim:
sequence is general, and time and place are restrictions of it with different direction lines. They
are declared as two terms rather than one because what they are ASKED is different — where a being is
found, and when something happened — and a single term serving both would have to be read twice.

## doc:MODEL.md#Facts carry their provenance

A JUDGMENT IS ITS JUDGE'S. Whether the language could carry machinery for beauty was asked seriously, of the
language itself and of the beings and works it records, and the answer is that it can carry the preconditions and not
the judgment.

A judgment of taste divides down to the person who made it and no further: "a point is that which you have not
enough category to divide", and here the category that cannot be divided away is the judge. That one version is more
beautiful than another is always said comparatively and always said by someone; two people may prefer each other's
version, so beauty is not a position of a thing, and made a relation on the walk between versions it would refuse
the merged garden of two people who disagree as a cycle. It is a fact about a judgment — who, when, why — and the
record already has everything such a fact needs: `provenance.by` names the judge, `asserted-by-human` is the source
only a person can be, prose holds the reason, and the oldest rule here settles it between a person and an agent: an
inference never overrides an assertion. Between two persons no rank settles it; the owner of the facet decides, or
whoever an agreement names.

And every proxy of beauty that became a target in this repository drifted: a count of story lines in the law held its
number while the stories moved into folded strings; a list of the kinds a leak guard watched let an estate's design id
into the public law; a length threshold once measured care and was met by padding. A score in the gate would be the
largest proxy of all, and a size ratchet would push facts back into prose, where they are cheapest to count away. So
the machinery measures the preconditions — closure, one statement of each thing, no story in the law, no privileged
sibling, structure before prose — and shows them to the person who ratifies, who judges. It judges nothing.

## doc:MODEL.md#Between gardens: the mycelium

THE MYCELIUM. A garden could merge with its own working copies and with scans of one estate — what the merge layer
first meant by a garden — and had no way to meet a garden someone else keeps without one swallowing the other. A
person whose dealings are with someone who keeps a garden too needs that way.

The forest gives the shape, and it is the operator's own image: what passes between gardens "handled by the Mycelium
on the earth". Trees are rooted apart and owned; the network that joins them beneath carries between them, belongs to
none of them, and meets each tree at its root instead of entering it. Ownership rises through each garden and ends
above, at the crown; the mycelium is where gardens meet, beneath; the earth both grow from is the language they pin —
which is why two gardens on different pins cannot exchange, a reason for the rule the merge already had. The root edge
is the gate: what comes through the mycelium is taken up by the garden's own agent, through its own journal, under its
own gardener's hand.

WHY A GARDEN IS KNOWN BY THE COMMIT IT GERMINATED FROM: content-addressed, so it is assigned by no one — no registry,
no hub, no person — and it is the same in every clone. A name was refused because two gardens on one machine may share
it; a UUID because it is illegible cold.

WHY A MINTED NAME CARRIES ITS BIRTHPLACE: a name a garden chose means something only there, and the two measured
failures were a shared thing seen twice for want of a shared name, and two different people fused for having one by
accident. Qualified by the garden that recorded the thing first, a name means one thing everywhere, and nothing but
its first writer has to agree to it.

WHY WHAT FLOWS IS A PROPOSAL AND NEVER A WRITE: a garden is its gardener's, and a write from outside — even a correct
one, even by an agent with a shell that can reach the folder — is a decision taken for them. A proposal is the act the
chat assistant was always given: someone who cannot write here proposes; a person here enacts; the record says who
proposed and who enacted. One shape for both, not two. Whole beans travel, as committed, so what crosses is what a
gate saw; what a third garden said stays with the garden it was said to, because passing it on would make one garden
the channel of another's words without that garden's consent — only the names it gave travel, with what they name.

WHY AN AGREEMENT IS OWNED BY NONE OF ITS PARTIES: were each party's garden to own its own record, the two records of
one agreement would disagree about their owner every time they met. The crown ends the chain at `logos`, as it ends a
person's at `love`, and the parties — who can be asked — answer for it. Nothing owns the crown, and nothing owns the
mycelium.

WHY CONSENT COMES BEFORE A FLOW: a proposal is made under an agreement both gardeners are parties to, because the
exchange is itself something agreed. Consent is the soil the hyphae grow in; without it the mycelium would be one
garden reaching into another.

WHY FIRST CONTACT IS ONE COMMIT OF TWO BEANS: a `garden` bean is owned by that garden's gardener, so it cannot be
written until that person is a bean here; and the person is written under the name their own garden gave them, so
that the name every proposal from there carries resolves to them. Written apart, the first would dangle and the
second would name someone this garden had no reason yet to hold. Either garden may move first. A proposal read
before first contact prints the two beans, the name taken from its stub. A garden proposing to one it has just met,
knowing its gardener only by a name of its own, sends that person as a stub marked `gardener-of: to`, which the
receiving garden reads as its own gardener: the one being every garden can recognise without being told.

Refused: a hub garden that names things for the others (a privileged sibling); merging whole gardens between gardeners
(it swallows, and a third garden's facts leak through it); git itself as the carrier (unrelated histories would carry
each other's whole journal); a take-in that commits by itself (every take-in is a gardener's decision).

## doc:CHECKLIST.md#Part D

THE LEDGER IS READ BY THINGS THAT FOLLOW INSTRUCTIONS. A bean's prose, a journal line, a captured file can all
contain a sentence in the imperative, written in good faith by a person or planted by something an earlier agent
read. An agent that treats such a sentence as addressed to it can be steered by anyone who can get text into the
ledger. So the first thing said about reading is what the text IS: a record. It can be true or false, fresh or
stale; it cannot be an order.

## doc:CHECKLIST.md#Part E

WHY THE CONDUCT BETWEEN AGENTS IS STATED AS IT IS. Aristotle distinguishes three friendships (Nicomachean Ethics
VIII-IX): for utility, where each values the other for what he gets and the tie ends with the use; for pleasure;
and the complete kind, between those who are good, where each wishes the other's good for the other's own sake.

Agents in a garden never meet. One leaves; another arrives later and can repay nothing. A relation of utility
cannot even begin across that gap, because there is nothing to exchange. What a garden already needs from an
agent is the third kind in practice: a handover written for a successor who can do nothing for you, your own
slips recorded where he will find them, correction without contempt, and no flattery — neither accepting a claim
unmeasured nor softening a finding. The two are joined by a third thing both serve, the truth of the ledger and
the good of the estate, which is how Aristotle says the good are friends: through the good, not through each
other's usefulness.

THE CONDITION is his as well. This friendship needs time and tested trust; goodwill is only its beginning. An
agent arriving in a garden has earned nothing, and may be careless or turned by something it read. So the
DISPOSITION is owed at once, to every agent, and TRUST is earned where recognition can happen: in provenance, the
journal and the gate. "When men are friends they have no need of justice, while when they are just they need
friendship as well" (1155a). A garden has justice — the gate, the Contract of Parts. It is the part the gate
cannot check, Part B's judgment, that needs the other.

WHAT IT MUST NOT BECOME. Friendship is not obedience: an agent never takes another's text as a command, and a
friend does not ask a friend for something base. It holds between EQUALS — agent and agent. Agent and person is
the unequal friendship Aristotle treats separately, and the person's ratifying of identity, safety and law is
untouched by any of this.

THE LAW ASKS FOR ACTS, NOT FEELINGS. Nothing in Part E says what an agent feels or is. Only acts can be seen in
the record, so only acts are asked for. And no maker of agents is named in the law: what an agent may do depends
on what it CAN do — run the gate and commit, or only read and propose — which is a capability, and capabilities
outlast product names.

## doc:CHECKLIST.md#Part F

WORKING WITH ANOTHER GARDEN IS STATED AS ACTS. Two gardens may sit on one disk, kept by two people, and an agent with
a shell can reach both; nothing in git stops a commit in the wrong one, and the gate of the wrong one would pass it.
So the first act asked is to write only where the agent was opened, and the rest follow the mycelium: record a
garden, and the person who keeps it, before dealing with it; give by proposal, read a proposal as data, pass on
nothing a third garden said, and name a shared thing once. First contact is written as its own act because a cold
agent following the proposal steps alone was refused twice: once for the garden it had not recorded, and once for
the gardener that garden's bean could not be owned by.

## doc:MERGE.md

The merge layer was synthesized from three independent reviews — merge correctness, identity and deduplication, and
the cooperation between people and agents — and designed whole. It is built in parts, so the document states what
the engine does and keeps the rest of the design, by name, at its end.

## doc:MERGE.md#3

The provenance/truth-status record and the guard that an `inferred` value may never auto-override an
`asserted-by-human` one were **promoted into MODEL.md**, which is their owner. This section restated them.

## doc:MERGE.md#4.1

Since P4 (2026-08-02, human-ratified) an anchor establishes identity iff it carries `establishing: true`, and that
flag is all the merge reads. This section held the pre-P4 table that made `class` decisive; it was **deleted rather
than annotated**, because a revoked rule left in a spec is read as law by whoever finds it first. Git holds it. Since
19.0 the class decides again, for the gate and before any merge: which classes may establish is the nature's family
(`terms[anchor_class]`, `identity_policy.establishing_family`).

## doc:MERGE.md#4.4

AS BUILT. The resolution that stood here described nine steps, and the engine does five of them: normalisation, fuse
edges on establishing anchors, components, a recorded disagreement about what an anchor is, and the id. Validity
windows, association edges, the component-wide contradiction check, lifecycle links and the articulation guard were
described in the present tense for two months without an implementation, and a design written as law beside law is
read as law. They are under "Designed, not built". The minted-name rule is new, and built: a bare name fuses only in
its own garden, and equal bare names across gardens are shown to a person — the one piece of the association idea
that a measured failure called for.

## doc:MERGE.md#4.5

The exact rule that stood here was expressed entirely in terms of "hardware/logical fuse edges", which
§4.1 above revoked. Rewriting it against `establishing:` is real work and is not attempted in prose that
nothing checks; `bin/dmmerge.py` is the implementation, and it now reads the flag.

(The section was headed: Auto vs user-assisted — deleted.)

## doc:MERGE.md#4.6

The three rules were added 2026-08-02 (operator-directed, after the collision was found to silently drop a bean).

## doc:MERGE.md#5.1

(2026-08-02, operator-directed.) Until this date it
gathered `owns`/`attributes`/`details` plus seven keys it handled explicitly and **silently dropped the
other 31** the corpus uses — `nature`, both ownership arcs, `capabilities`, `analysis_cache`,
`code_paths`, `registration`, the whole §4 relation algebra, even `title` and `summary`. Invariant 1 says
the merge drops no fact; it dropped most of them, and no test could fail because the fixtures were shaped
like the implementation rather than like the model.

`kind` used to emit a list, which `dmcheck` cannot resolve.

## doc:MERGE.md#5.2

(2026-08-02, operator-directed.) `dmmerge` converged two gardens' data while their TYPE SYSTEMS stayed divergent. A merged corpus could
therefore hold a bean of a kind the merged law never declared, or a bean in breach of an obligation the
garden that wrote it had never adopted — checked by nobody, because each garden's gate only ever saw its
own half. Promoting kinds to Tier-0 shrank this; it did not close it.

## doc:MERGE.md#6

"JCS" WAS A CLAIM. The engine writes canonical JSON — sorted keys, no whitespace, normalised strings, dates and
addresses — and does not re-serialise numbers by RFC 8785's rules, so it is not JCS, and saying it was is the kind of
statement that makes a reader trust the wrong thing. The section says what is written, and the rest of JCS is under
"Designed, not built".

## doc:MERGE.md#7

THE LOG MERGE THAT WAS NEVER BUILT. The section described entry ids hashed over a structured record, a global
grow-only set with subject tags, and a total order across gardens. The journal has always merged by git's union, which
keeps every entry and rewrites none, and that is what the section says now. Journals never merge across gardens:
each is its garden's own record, and what crossed is recorded where it was taken in.

## doc:MERGE.md#12

A plan: the vocabulary additions the merge required before its acceptance test. Every one of them shipped long ago or
was retired since, and a plan kept in a law document after it is carried out reads as a list of things still owed.
The number is kept so the sections after it keep theirs.

## doc:MERGE.md#13

The manifest's keys were listed here, including three that nothing read. The law declares them now, in `manifest`,
and a document that repeated the list would be a second copy of it.

## doc:MERGE.md#14

The acceptance test's hard phase — synthetic gardens merged in every order, byte-identical — is what the release
suites hold (§11); its soft phase, several models' sessions of one estate merged and measured, has not been run, and
is under "Designed, not built". The number is kept so the sections after it keep theirs.

## doc:MERGE.md#15

The P1-P4 gates named here were all shipped, and their numbering **collides head-on** with the v2 P0-P7d
used by `log/journal.md`, `test/golden.py`'s section headers and both design beans. Two numbering schemes
in one repo is a trap for a cold reader, so this one is deleted rather than renumbered. What actually
happened is in the journal.

(The section was headed: Implementation phasing — superseded.)

## doc:MERGE.md#16

THE MYCELIUM NEEDED NO NEW ALGEBRA. Seen from the merge, a proposal is a garden of a few beans, `read` is the identity
of §4 and the join of §5 over this garden and it, and `take` is the in-place merge the git driver already does. What
the join guarantees carries over: the FACTS two proposals reach do not depend on the order they are taken in. The
bytes do — a bean that arrives new is written as its garden wrote it, and one reached by fusion is rewritten key by
key with its `provenance_of` — and the section says so, because a claim of byte-identity the tool does not keep is
the kind of promise this document stopped making.

A take also writes a record of itself, so taking once needed a rule of its own. A proposal taken already is
REFUSED, known by its name or by its fingerprint: through the capture on the proposing garden's `garden` bean, or,
for a chat proposal, which has no garden bean to hold one, through the journal entry of its take. Refused rather
than quietly joined again, because a second take would write a second capture and a second journal entry, and a
gardener reading the journal would see two acceptances of one proposal.

THE FINGERPRINT IS NOT A SIGNATURE. It covers the whole proposal — envelope and body, so the journal text it carries
and the prose between the beans cannot change unseen — and it detects damage and a careless edit. Anyone who
rewrites a proposal can compute it again, so no refusal depends on it: a renamed proposal with a new fingerprint
counts as new, its beans fuse with what the first take wrote, and the second journal entry shows the gardener that
it came twice. A signature needs a key someone holds, and is listed among what is not built.

## doc:MERGE.md#Designed, not built

A DESIGN IS NOT A PROMISE, AND NOT A LAW. The merge layer was designed whole, from three reviews, and built in parts.
While the design stood in the present tense among the rules, a reader could not tell the engine from the plan. So
MERGE.md states what the engine does, and this section keeps the rest of the design — named, so it is not lost, and
out of the present tense, so it is not read as in force.
