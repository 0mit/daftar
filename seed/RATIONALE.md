---
rationale_for: seed/std-vocab.md
---
# daftar — why the law says what it says

This is the reasoning layer (manifesto: layers): why a law, or a clause of the manifesto, is the way it is, the argument
for a design, what was considered and refused.

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

## schema_language.is_ref

Declared at 13.0.

## schema_language.path

Added at 2.0 for the five core grammar enums, and not declared in the schema language until 11.3.

## schema_language.alt_form

In use since the first schema language; declared at 11.3.

## schema_language.dag

`dag` became the term key of the `walk` sequence aspect at 9.2.

## schema_language.values_add

Declared at 8.2.

## schema_language.compare_form

Declared at 9.0.

## schema_language.attr_domains

WHAT `in:` MAY SAY. Every attribute is a position in EXACTLY ONE domain,
so `in:` is one thing, and it is never absent.


A DOMAIN GIVES THE ORIGIN, so almost nothing states one. A closed list, a registry and an aspect are the law's; a
reference is the garden's (`by: law`); a date, a quantity, a position in a system, an extent and a recurrence are
said, the strictest reading — a day read from the clock or the world is the exception, and its position says so
(sixteen do); prose, a pattern and a kebab name are
made, because they are how a writer names and describes. `untyped` is said, the strictest, until someone declares
it. `entries` and `any` are `inner`: their positions are their own entries', or the field's they track, and an origin
of their own would be a second answer. Every domain `attr_domains` offers carries its origin beside its form, and the gate refuses a domain
without one — a new domain is placed when it is declared, not found empty by a flow the law cannot judge.

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

`relative`, `lapses`, `stance` and `condition` (24.0) each NAME an attribute of the term, as `attr` and `repeats` do, and
the gate refuses one that names none: a position stated relative to another, a permission that lapses rather than falls
due, the words chosen by the entry's effective stance, and a condition in place of a day. They are declared here and
read by the parts that build them.

## schema_language.required_on_gene

THE AXIS IS READ FROM THE REGISTRY (22.0). A `required_on_<registry>` or `only_on_<registry>` key names a registry, and
the bean attribute it is keyed on is the field that registry's rows are named by: `gene` gives `genos`, `natures` gives
`nature`, `roles` gives `role`. Until 22.0 the gate took the key's plural and dropped its `s`, which held while every
registry was an English plural; γένη is not γένος with an `s`. Reading the row's own field keeps the rule the
interpreter has always kept — the axis comes from the law, never from the gate's code.

## schema_language.only_on_gene

THE MIRROR OF `required_on_gene`. The language could say that a genos of being must carry a term and not that only
it may, so a term that is a fact about one genos of being — that another garden is a rehearsal — could sit on a person,
where nothing reads it. The alternative was the gate naming the term and the genos in its code, which is the one thing
the interpreter does not do.

## schema_language.at_most_one_of

A CONTRADICTION IS REFUSED WHERE IT IS WRITTEN (24.0). `entry_one_of` could say that an entry states at least one of a
group, and nothing could say that it states at most one: a clause could carry a stated `due` beside a `falls_due` that
computes one, and a value a `u` beside an `accuracy`, and every reader then chose between them in its own way. A group of
which at most one may be held says it once, in the law, and names both when two are written. Beside `entry_one_of` on
the same group it says exactly one.

## schema_language.keyed_by

ONE ENTRY PER KEY, ON THE TERM ITSELF (24.0). `keyed_by` inside `in: entries` held a nested list to one entry per value
since 21.0. Several mechanisms of 24.0 needed the same of a term's own entries, and some by more than one attribute —
one observer's one verdict on one entry — so the construct is stated beside `shape` too, and takes a list: one entry per
combination of values. An entry holding none of the attributes is not counted, because a key it does not have cannot be
repeated; a merge sorts a compound-keyed list by the tuple of its values.

## schema_language.exclusive

DECLARED, AND ON NO TERM (24.0). Some extents cannot overlap for one being in one role — one person booked twice for the
same days, one room lent twice — and the check is across every bean of the garden, not inside one. The construct is in
the language so that a garden which needs it writes it in its own VOCAB.md, as a RULE-CHANGE; the law puts it on no term,
because nothing the standard holds is exclusive for every garden.

## extent_form.level

A MONTH IS NOT A MEASURE (24.0). `not_a_calendar_bucket` refused a month as a length because it is 28 to 31 days, and
that left no way to say "for one month" at all. A length counted in CELLS of a level of the system named says it without
pretending to arithmetic: from a day, the other end is the same place in the cell that many cells on, and where that
cell has no such place, its last one, said aloud. `measure` and `level` never stand together, because one length has
one spelling.

## value_types[moment]

A POSITION BELOW THE DAY (24.0). Until 24.0 a clock time on a date was refused as finer than the type, and the only
moments the law knew were the journal's headings. A moment is held to the minute or finer, in any calendar, with the
offset it was read at — the form of a heading, so there is one form of a moment and not two.

## value_types[date_or_moment]

HELD TO THE UNIT IT IS WRITTEN AT (24.0). Some positions are a day for one entry and a moment for the next — a clause
due on a day, another due at eleven. Two attributes for one position would let an entry state both; `either` names the
types a value may be, and the value is held to the one it passes. It is the one row that uses `either`, declared by its
own meaning rather than as a new construct of the language.

## value_types[field_path]

ONE SPELLING OF A PATH INTO WHAT BEANS HOLD (24.0). A reading, a checklist, a grant and a page each name a value inside
a bean, and each would otherwise invent a syntax for it. The pattern is the law's, and one reader in bin/dmparse.py
reads it, so a path is judged and followed the same way everywhere. `>` follows a ref because the graph is made of refs;
`[<attr>=<value>]` selects entries by what they hold rather than by their position, which carries nothing.

## value_types[held_pointer]

A POINTER THAT SAYS NOTHING OF WHAT IT POINTS AT (24.0). Material kept off git is found through a logical root each
host resolves for itself, and a key minted at random: a name chosen by a person would carry what it names into the
history that the material was kept out of.

## value_types[language_tag]

A LANGUAGE AS THE WORLD ALREADY WRITES ONE (24.0). BCP 47 is the form every other system that names a language uses;
the pattern takes its language, script and region subtags, which is what a garden's words have needed.

## uncertainty_form

HOW WELL A VALUE IS KNOWN, IN THE WORDS OF THE GUIDE (24.0). A value was exact as written, always. A reading has an
uncertainty, and a comparison that ignores it says two values differ when nothing can tell them apart. `u` is the
standard uncertainty of JCGM 100:2008, in a unit of the value's own quantity; `accuracy` keeps what a maker stated, with
its kind, because turning it into `u` is a reader's act and a writer who did it would state a number nobody measured. A
value stating neither is exact as written, and a reader combining it says so rather than inventing one.

## accuracy_kinds

WHAT A MAKER'S ACCURACY MEANT (24.0). The same "± 5 m" is a bound, a 68 % radius or a 95 % radius, and they differ by a
factor of up to about four; the kind is written beside it so that a reader turns it into `u` by the rule for its kind.
`unstated` is kept as said and never read as a standard uncertainty.

## selection_form

ONE GRAMMAR OF READINGS, AND NO FORMULA (24.0). A clause's condition, a checklist's `met_by`, a grant's audience and a
page's table are each a selection of beans or entries and something computed from it. Written as steps of a closed list
of operations, each naming earlier steps only, a reading cannot loop and no string is evaluated; read each time by one
reader, it is never written back as a fact. An act that fixes a reading records the commit it was read at.

## operations

CLOSED, SO THAT A READER CAN HOLD EVERY ONE (24.0). Each row says what it takes, in the attribute language every term
uses, and what it gives. A set, a truth that may be NOT KNOWN, a value with its uncertainty, an order, groups: the
kinds are few so that a result is always one a person can check. bin/dmreckon.py applies these rows and nothing else; `takes` is an attribute block, read as `attrs` are. Rows are added by the release that builds their
evaluation, and by no other.

## comparators

A CONDITION NAMES ITS COMPARISON (24.0). `monotone` marks the comparisons whose answer never turns back — what has been
reached stays reached — because a reading over them can be read once per occurrence and not re-judged.

## terms[selections]

A READING IS DECLARED WHERE IT IS ABOUT (24.0). A selection is a key of a bean's `selections`, named from anywhere by
`key_of: selections` — the one spelling the law already had for "a key of a term on a bean" — rather than by a new
wrapper. It is read each time and never stored, so it cannot go stale.

## schema_language.series

ONE CONTROLLER FOR WHAT ONLY THE WHOLE ENTRY SAYS. Each attribute of a series is judged by the rule its domain already
has — the recurrence, the extent, each channel's registry and type. What none of them can say alone — that the unit
measures the line, that the stride is whole, that the header names the channels, that each cell is one its channel
holds, that a monotone channel never goes back, that an exclusion names a row — is read by the one reader of a series,
which the gate asks, as it asks the one reader of the layer map.

## crown

== NATURES: the root axiom layer (added 2026-08-02, P3 / plan D1, human-ratified rule-change) ==
`nature` is the ROOT of the type system and `genos` (until 22.0, `kind`) is a REFINEMENT of it, not a parallel
taxonomy. Every bean carries a nature; every genos declares the `of_nature` it refines; the gate holds the
two equal. Policy that used to be stated per genos (anchor family, minimum anchors) attaches HERE, so a
new genos inherits a coherent identity policy for free and may override only if it truly differs.
The crown itself is a MODEL axiom (MODEL.md Ownership), never instantiated as beans.
== THE CROWN (added 2026-08-02, P7b, human-ratified) ==
MODEL §Ownership states the axiom in prose; this makes it NAMEABLE in data without instantiating it as
beans. These are the TERMINI every ownership chain resolves to. A bean names its branch directly only
where ownership does not pass through another being — in practice, persons. Everything else chains up
through a person or an org and terminates here transitively.
The branch a bean may name is fixed by its nature (natures[].crown owns that mapping — not restated here).
The names — θεός, φύσις, λόγος, ἀγάπη since 22.0 — and what else was on the table: `natures`.

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
first garden's beans carried seventeen keys no term declared — a product's id, a session's, a service's, the
ids the registry of gene had NAMED IN PROSE since P3 and never declared. Two gardens spelling one anchor model
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
body — a being of the nature soma — is its matter, and a name that establishes it would fuse a replaced machine with the one that
kept its name — exactly the `id` term's oldest exception. What broke under enforcement was instructive: one
rented VPS anchored on its name, and three physical machines whose `fqdn` was establishing beside a real
serial. The VPS was of the wrong nature (see `gene[virtual-host]`); the names were demoted to corroborating,
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
became structure: `<genos>:<name>`, the genos one the garden knows, is a name a garden gave; any other value was
assigned outside every garden, identifies wherever it is written, fuses as every anchor always did, and is never
qualified — the gate refuses `<garden_id>/postfix`. The genos must be a genos the garden knows so that a colon inside an
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
`in: { bean_id: { gene } }` states it as structure, the one place both tools read. The gardener is not required to
be the garden's first bean: it is the first of a garden grown with `--gardener`, and a garden upgraded into 21.0 names
a person it has held for years.

## manifest.attrs.daftar_release

A release, or `untagged <commit>`: a garden grown from a checkout on no tag records the commit it runs, exactly as
`seed/germinate.py` writes it — `untagged unknown` where even that could not be read — and a pattern that admitted only
a tag would have refused every garden grown to have a look around. The note germinate prints says why such a garden
should adopt a release.

## manifest.attrs.policy

A GARDENER'S STANDING RULES ARE WORDS. Declared as `any`, the key took a number or a list as readily as a sentence,
and its meaning said prose. A gardener writes one rule, or several each under a name of its own — how work on a live
system is done, who decides what — so the key takes exactly that: one text, or texts under names. The schema language
says it once, as `in: { prose: named }`, beside `in: prose`.

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

What went at 22.0, and why: the law's words took their Greek roots (`natures` says why, and what else was on the
table). A bean's `kind` is its `genos`, the registry `kinds` is `gene`, and a garden's `local_kinds` its `local_gene`;
the schema's `required_on_kinds`, `only_on_kinds`, `must_equal_kind_attr` and `entry_form_from_kind_attr`, `bean_id`'s
`kinds` and the minted form's `form_kind` follow them; the natures `physical`, `metaphysical` and `living` are `soma`,
`lekton` and `empsychon`; and the crown's `god`, `nature` and `love` are `theos`, `physis` and `agape`. Each row says
where its name went, so a garden not yet upgraded is refused with the new word, never read as nothing. `nature` is a
name retired at the crown and is still a bean's attribute, and `kind` is retired on a bean and is still a mapping's: a
name retired in one place may be live in another, and a row's `at` says which.

## senses

ONE NAME, ONE SENSE, JUDGED ONCE (24.0). What an attribute name means is read from its domain, over every term the law,
its profiles and a garden declare, by bin/dmform.py. A name two domains give — `at` a moment in one term and a file
pattern in another — or a name spelled as a term or a table that takes none of it is a finding, and each finding is a
row: the one sense its uses share, in words. A finding with no row is a second sense and is refused, so a new name is
chosen where a new sense is meant; a row whose finding has gone is refused as stale, since no judgment outlives its
cause. Structure answers first, and a row only where structure cannot: an attribute taking a row of the table it is
named for (or of the one named for many of it, `view` of `views`), of the table whose key column carries its name, a
key of that term, or the attribute of the term it names, is in its sense without a row; a value type on a dimension
gives the dimension, so a day and a moment are one sense at two precisions; a domain nobody declared gives no sense to
compare; and a retired name is retired at its own position, which no attribute inside a term is.

The rows were a judgment kept in one test, over the one profile with an asset; the law now carries them, and the gate
asks them of every garden. A garden judges its own term's finding in VOCAB.md, and a garden's term giving a name the
law judged a domain the law's row did not judge is a finding of the garden's too: that row judged the domains it saw,
and whether the new use is in its sense is the garden's to say, in its own row, or to rename. Where a finding
was one sense under two names, the names were made one: a pass says `from` and `to`, as a flow row does; its metadata
counts `characters`, and nothing counts lines; a datum's `direction` is before or after, as an order's is ascending or
descending; a table of a view reads a `series`, which is what it points at; and a fixing position's `origin` is an
origin, in the form every position's origin takes.

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

## provenance_record.origin

STAMPED, NOT TYPED (23.0; since sources-by-nature, `as_of` read `by: save`), for the reason the journal heading is (20.0) and with the same reading of the clock. The
day of writing is a fact the writer is the one source of, and a writer who types it types a remembered day: measured
on a local model with no date in its context, every `as_of` it wrote was the nearest date in view — the forms'
example day, or the gardener's own stamp read in another bean. The gate cannot tell a typed day from a read one by its
form; it can tell whether it is the day of the heading the same commit adds, which the heading's tool read from the
clock. So one reading dates both, and there is no second register: a stamp is judged against versioned history that
any clone can read, and only where a commit adds it — a record left as it was is never re-judged, so no garden
changes on crossing. A record is matched by what it is — its src, its by and its day — not by where it sits: a
conflict wraps records, a settlement unwraps them, a bean is renamed, and none of that is a day of writing. Where a
stamp came from belongs to the value, not to a position: a record taken in from another garden carries that garden's
`garden` and keeps its stamp; the merge engine's own record says `merged`, because when a merge happened is git's to
say. Neither is an escape a writer can type: this garden's own id exempts nothing, and `merged` passes only on the
merge engine's record.

## schema_language.origin

EVERY POSITION SAYS WHERE ITS VALUE COMES FROM (24.0, the Leviathan's Body 2, ratified 2026-09-25). A tool that
must know whether a day was someone's word or the clock's kept its own list of names — `as_of` and `observed` in the
forms, in the save, twice in the gate, and once more in the bench's tracer — and five lists of one fact drift. The
position says it instead, once — `origin: {act, nature?, by?}` — and every reader asks bin/dmpass.py. It is stated only where
the domain's default is wrong, and the gate refuses one stated equal to its default, so the statements that exist are
exactly the exceptions a reader should notice.

It began as `stamped: true` (the release of 2026-09-25, F8, with a platform case's finding that a typed move's moment is
invented): a move records the moment it was made, and a typed moment is exactly where invented days came from, since a
writer types the nearest time in view. `by: save` is that facet with its siblings: the save writes `now` away — the
day of its heading at a date, the heading's whole moment at a moment, read from the position's type — and the gate holds
a value a commit adds to the reading of a heading the same commit adds. The save finds a `now` by the attribute's name,
so one name read as a day in one place and a moment in another is refused: it could not tell which to write. The day of
`as_of` keeps its own statement (`provenance_record.origin`) because it lives on every record, not on a term; so does
the journal's heading (`journal.origin`).

## acts

TWO QUESTIONS, NOT FIVE ANSWERS (sources-by-nature, ratified 2026-09-26). Part 10 wrote five origins — said, stamped,
observed, law-owned, composed — beside a list of clocks and a table of each domain's default, while where a crosswalk, a reckoning and a
datum come from, how a `provenance_src` is known and what fixes a boundary each answered the same question in a list of
its own. Laid side by side, every one of those names answers two questions at once: HOW the value came to be where it
is, and WHAT KIND of source it came from. `said` held a person and a document; `composed` held a minted name and a
digest; `observed` was a reading of a body. So the law asks the two apart. The act is one of four — made here, derived
from what was given, read off the world or a clock, said — and the source's nature is one of the natures a being
already has: a machine's clock is soma, a document lekton, a person empsychon. A tool's output is physis, derived by a
body from what it was given; a document's word is logos; a person's is agape.

`by` names the few places where WHO performs the act changes how it is judged: the save reads the clock, and a typed
value is refused (`save`, once `stamped`); the reckoner reads it at the moment of reading (`reader`); the schema owns the
values (`law`, once `law-owned`, widened by the gardener on 2026-09-26 to the beings, parts and fields a garden holds,
since the gate resolves every one); another garden said it, and the flow law judges it (`garden`). A reading typed by
its recorder has no `by`: the recorder may report a reading made before the entry that records it, so `now` is offered
and a typed value stands.

The order is DERIVED, not written: acts lightest first — what is made holds nothing given, what is derived holds
nothing its inputs did not, a reading can be read again, and what is said can be asked of the one who said it — then the
natures in their own order. That is the provenance rank as it always stood, and it places a value it never had a place
for: a document's word, above what was read off the world and below a person who can be asked.

## natures

THE GREEK NAMES (22.0). The law's words for what a being is came from four traditions at once: the crown's root was
Spinoza's god (`Deus sive Natura`), its branches Descartes' extension and thought and Spinoza's conatus, said in English
as `nature`, `logos` and `love`; the natures were `physical`, `metaphysical` and `living`, and a being's type its
`kind`. One of them was wrong in its own tradition: in Aristotle, metaphysics — τὰ μετὰ τὰ φυσικά — studies being as
such, every being, and not the ones that are not physical; a service or a contract is not "metaphysical". So each word
was given its Greek root. Every choice below was put to the operator with the ones beside it, and ratified on
2026-09-24; what was not taken is kept here, so that a later reader sees what else was on the table.

THE NATURES — `soma` · `lekton` · `empsychon`, from the Stoics: σῶμα, a body, a being with extension in space —
machines, hardware, sites; λεκτόν, the sayable, what exists by being said and agreed — code, domains, contracts,
organisations, designs; ἔμψυχον, the ensouled — persons, and running instances while alive. Taken because each is
exactly what the law already meant. Not taken: `physis` · `nomos` · `psyche` — Aristotle's contrast of what is by
nature (φύσει) with what is by convention (νόμῳ), with ψυχή for the living: crisp as a pair, but a machine is an
artefact of τέχνη, which Aristotle would not call physis. Not taken: `somatic` · `asomatic` · `empsychic` — the Stoic
pair written as English adjectives, closest in shape to the old words, and so the least surprising in a bean.

THE CROWN — `theos` · `physis` · `logos` · `agape`: θεός, the root every chain ends in and no bean names; φύσις for the
bodies; λόγος, kept, for the sayable; ἀγάπη, love that does not possess, for the ensouled — so "only love holds a
person, and only while alive" keeps its word. Not taken, for the third branch: `oikeiosis` — οἰκείωσις, the Stoic
"making one's own", by which a living being belongs to itself from birth: the most exact word for "unownable by
another", but it loses the word love. Not taken: `psyche` — ψυχή, life itself: plain and familiar, but it says life,
not love.

THE TYPE OF A BEING — `genos`, and the registry `gene` (γένος, γένη). Not taken, and the one the agent recommended:
keep `kind`. Kind, γένος and genus share one Indo-European root, *ǵenh₁-, to beget, so the English word is already the
Greek one, and renaming it touches every bean for no change of meaning. The operator chose the Greek word, so that the
law says in one tongue what a being is. What `kind` means besides — a network treatment's kind, a mapping's — is not a
being's type, and was not renamed (`terms[kind]`).

THE PAGE ON BEING — the public page once called "philosophy" is `Metaphysics` (τὰ μετὰ τὰ φυσικά): with the natures
renamed, the word no longer collides with a value on a bean. Not taken: First philosophy (πρώτη φιλοσοφία, Aristotle's
own name for the study, and the one the agent recommended); Ontology (ὄν and λόγος, a coinage of the 1600s).
Since 2026-09-26 the page is `Model`, by the operator's word ("now that we use another term for the kind lets rename
the github pages's website's metaphysic to model"): with `genos` where `kind` was, the page is named for what it
shows, the law's own `MODEL.md`, and not for a tradition.

KEPT AS IT WAS — the bean attribute `nature:`, the registry `natures` and a genos's `of_nature`. Its Greek word, φύσις,
is now the crown's branch for bodies, and `physis: soma` beside a branch called physis would read badly. Recorded, and
not taken: οὐσία (ousia), being or substance.

A rename every garden carries is a MAJOR version, and nothing in it is a person's to decide, so all of it is
translated: `bin/dmupgrade.py` renames the structure of every bean and of VOCAB.md when a garden crosses into 22.0, and
leaves its comments and prose as the garden wrote them. The law's `retired:` list names each old word, so a garden not
yet upgraded is refused with the word that took its place — never read as though it said nothing.

## natures[soma].crown

φύσις owns the bodies: a being of the nature soma ends there (until 22.0, "extension owns physical beings")

## natures[soma].establishing_anchor_family

serial / mac — bound to the matter itself. (`wg_pubkey` was listed here until 19.0; it never was.)

## natures[empsychon].establishing_anchor_family

Logical: a person's minted id or signing key, an instance's deployment coordinate, a VM's instance id. Until
19.0 the row also named `personal`, a class `anchor_class` has never offered — a position no anchor could occupy.
It would have meant a passport number or a biometric, which the ledger never records because they are secrets;
the name was withdrawn rather than given a class nothing may honestly fill.

## natures[soma].min_establishing_anchors

required once identity.status is `confirmed`

## natures[lekton].crown

λόγος owns what exists by being said and agreed (until 22.0, "thought owns metaphysical beings")

## natures[lekton].establishing_anchor_family

url / fqdn / git remote / manifest or doc id

## natures[empsychon].crown

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
datum             (24.0) what a position here is an offset FROM: `being`, the being the position names, or
{system, at, direction: before | after}, a position of another system. Two systems over one ground whose
datums are in one system are crosswalked by computing.
cells_in          (24.0) the table whose rows are its cells, `{registry, take}`; `overlay` a table whose rows win
over them, each with its `source`; `boundaries_in` what fixes each cell's base (`fixing`).
unit_symbols      (24.0) the symbols its positions are written in, each naming a unit of its dimension.
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

## value_types[date].exists

A DAY ITS CALENDAR DOES NOT HAVE IS NOT A DATE. A pattern admits `persian:1404-12-30` and `2026-02-30` alike, and
each reader did something different with them: the Persian date moved silently to the first of Farvardin, so a clause
meant for the thirtieth fell due on the first of every month, and the Gregorian one was dropped by one reader and
refused by another. For a calendar reckoned by rule (`arithmetic`), the arithmetic that converts a date also judges it:
the day a position names, written back in its own calendar, must be the position written. A year outside the range a
calendar's reckoning is good for is refused the same way, by name and never by a traceback. The other reckonings —
astronomical, observational, tabulated — cannot be judged by arithmetic, and are not.

The rule is stated where a date is defined, and which calendars it judges is read from each calendar's own
`reckoning`. Stated only in a reason, it was a rule `bin/dmrules.py` could not show; judged by whichever calendars a
tool happened to carry, the gate and the reader that walks a repetition could disagree about one calendar — a tool
that learned an observed calendar would have started refusing its days on arithmetic the law says it does not follow.

## anchor_systems[unix-filesystem].levels

a tree of any depth; a position is held to whatever depth it is written at

## anchor_systems[unix-filesystem].datum

A PATH IS AN OFFSET FROM A DATUM A HOST DEFINES (24.0, Body 2 of the Leviathan; carried from PLACE). `root:<name>/<rel>`
is `<rel>` from the root `<name>`, which each host states for itself in its `roots`; `<host>:<path>` is an offset from
the host named in the position; `<root>@<object>` is an object reachable from a root. Where and when were already one
mechanism, an offset from a being or from another system's position; a path is the third datum, and one resolver
(`dmwhere.on_host`) reads it for every tool that asks where a tree is. The systems a host anchors were a list of three
names in that tool, and a garden's own filesystem system would have been read as a coordinate; `datum: host` puts the
fact in the row, where the gate holds it to a place.

## anchor_systems[unix-epoch]

Declared at 7.0 for `beanger` records. The misreading its `why` names happened: a UTC reading labelled +03 was misread
in the journal of the estate the law was first written in.

## anchor_systems[network-segment]

Declared at 11.0, when the operator ratified that a segment is a place and not an address.

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
WHAT 16.0 LEFT READING ONLY THE GREGORIAN CALENDAR — `leaf_orders.instant` (the merge absorbs a coarser reading into a
finer one only within it) and the journal's heading form — 18.0 took into every calendar: the `instant` order holds
between readings in any declared calendar, asked at the day, and a heading is a position in any declared calendar's own
form. Each had been a Gregorian-only READER, never a rule that time is Gregorian.
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

**Why it has no pattern.** no two countries write an address the same way, and inventing a canonical form would reject valid addresses to look thorough. The address is prose; the country it is within is not.

## roles

== ROLES: what a being DOES, as against what it IS (added 7.0) ==
THE FIX FOR AN AMBIGUITY THIS VOCABULARY SHIPPED WITH. `router` was a GENOS until 7.0, and the proof it
was wrong is an asymmetry the corpus already carried: a mail server recorded five roles as free-text data
(`primary-mail, file-server, monitoring, webmail, erp-host`) while a router's single role was a genos.
Both are machines. What makes one a router is that it forwards traffic — which since 6.0 IS data, in
`treatments`. A genos answers what a being IS; a role answers what it DOES, and a being does several
things at once. Encoding one of the things it does as the thing it is made the genos un-askable for every
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

## registry_forms

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
Postfix speaks smtp. An implementation is a BEAN (genos instance/product) that carries `endpoints`, and
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

## net_protocols[pppoe]

9.0 removed a `transport: tcp` and a port, 1723, that had been copied from pptp.

## units

== UNITS: the resolution a position is actually held to (added 5.1) ==
DECLARED, NEVER INFERRED FROM DIGITS. A journal can state most entries as `## 2026-08-04` and a few as
`## 2026-08-04 20:04 +0300`, and nothing records which of the first were measured to the day and which
were measured finer and rounded. Two positions whose resolutions OVERLAP ARE NOT ORDERED, and a model
that cannot say so invents an order instead — which is the failure this registry exists to make
expressible. Keyed by `dimension`, so a length or an angle joins without a rule-change.

## aspects[temperature]

A TEMPERATURE IS WHERE SOMETHING IS ON A LINE, NOT HOW MUCH OF SOMETHING IT HAS. 36.4 °C is not 36.4 of anything: twice
it is not "twice as hot", and adding two readings means nothing. What is additive is a DIFFERENCE — a rise of 2.5
kelvin — exactly as a moment is a position on time and only a duration is a quantity. So the law says it the way it
already says time: an aspect of one metered line (`temperature`), scales that are position systems on it
(`kelvin-scale`, `celsius-scale`, `fahrenheit-scale`), and a quantity for the length of a region of it,
`temperature-difference`, whose unit is the kelvin. That keeps the rule that a unit's factor is a pair of whole numbers
with no offset (`## quantities`): the offset between Celsius and kelvin is the crossing between two SYSTEMS, computed
exactly (`crosswalk: computed`, as the calendars cross), and never a property of a unit.

The three scales are declared beside each other and none is the one a reading must be converted to: a thermometer that
reads Fahrenheit is recorded in Fahrenheit, as a date is recorded in the calendar it was written in (manifesto:
sibling).

## anchor_systems[celsius-scale]

`K = C + 273.15` and `F = C × 9/5 + 32` are definitions, so the crossing is exact arithmetic on decimals; nothing about
it is observed. `same_ground_as` says the three scales position the one line, which is what lets a reading in one be
compared with a reading in another at all.

## quantities[number]

HOW MANY THINGS, COUNTED, IS NOT A SHARE. Two seats at a recital, forty stems in a crate, three units of stock: each is
dimensionless, and each would have fitted `ratio` by its dimensions alone. It is kept apart for the reason `level` is:
it composes differently. Counts add; a share of a whole does not add to another share of another whole. So `number`
is its own kind, and its one unit is `item`. Not `each`, which the law already uses for "the same place in each cell"
(`recurrence_form.each`) and for one occurrence for each member of a selection: a unit named `each` would be a second
sense of one name.

## quantities[pressure]

A gauge pressure — how far above the air around it — and an absolute one are the same quantity measured from two
zeros. The zero is a property of what was measured (a tyre's gauge pressure, an atmosphere's absolute one), so it is
said in the property, and the unit stays one: `kilopascal` does not come in a gauge and an absolute kind. The
millimetre of mercury is the conventional one, a definition, so its factor is exact.

## units[annus]

AN AGE BEFORE THE PRESENT IS COUNTED IN A YEAR OF FIXED LENGTH. A calendar year varies — 365 or 366 days, and further
back a different calendar altogether — so an age of 12 million years cannot be counted in calendar years without
choosing whose. The geological sciences fixed the annus (IUPAC-IUGS, 2011) at 31556925.445 seconds, and astronomy the
julian year at exactly 365.25 days; both are declared, each as what its science publishes in, and neither is a
calendar year. A plate's drift is written in millimetres per julian year because that is how its velocities are
published.

## reference_systems

A REALISATION IS NOT ITS ENSEMBLE. WGS 84 as a receiver reports it is an ensemble of several realisations, and EPSG
states it accurate to about 2 m: two positions in it that differ by less than that may be one place. So the row says
so (`ensemble_accuracy`), and a reader prints it beside a position, so that nobody reads a plateau's motion of
millimetres a year out of it. Motion that fine is published in a single realisation, ITRF2020 (`EPSG:9990`), whose
frame epoch is given in its row.

A position may also be VERTICAL — one height, on one axis — or COMPOUND, a horizontal system and a vertical one written
together (`EPSG:4326+5773`), as EPSG writes compound systems: a borehole's collar has a place and a height, and neither
system alone says both.

## terms[located_at].schema.attrs.u

HOW WELL A POSITION IS KNOWN IS PART OF THE POSITION. A phone's fix and a surveyor's differ by three orders of
magnitude, and a position that does not say which cannot be compared with another honestly. Horizontal and vertical are
stated apart (`u`, `u_vertical`) because they are known apart: a satellite receiver is worst in height, which is also
where most local ground motion is. `accuracy` keeps what a receiver stated, with its kind, because the four meanings a
device's "accuracy" can have (a bound, one standard deviation, 95 in 100, or nothing said) turn into four different
standard uncertainties, and only a reader that knows which may turn it into one (`uncertainty_form`).

## terms[located_at].schema.attrs.zone

AN OFFSET IS READ FROM A ZONE, NEVER STORED. A civil clock's offset is the rule a government set for a zone, at a
moment, and governments change the rule: a stored offset is right until the day it silently is not. So a position says
which zone of the IANA database is in force there, and a reader asks the database for the offset at the moment it
needs (`dmcal.py --offset`). The zones are the database's canonical ones (`registry_files[time-zones]`), so a name is
checked against it and not guessed.

## registry_files[time-zones]

One row per zone whose clocks have agreed since 1970, as the IANA database's `zone1970.tab` lists them, and `Etc/UTC`
for a reading in UTC itself. The file holds names and places, never offsets: those are read from the platform's copy of
the same database at the moment asked, so the file never has to change when a government moves its clocks.

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
`universal`: the position is declared because the STRUCTURE is general, not because an occupant is
expected here. A figure with a side missing is a worse model than a figure with a side nobody stands on, and a
standard that waits for one garden's occupant before completing a mechanism ties every garden to the first
one's size. It is a reason and not a licence: the position must belong to a mechanism that IS occupied
somewhere on the same figure, and its `why` says which. A garden that stands on a `universal` position is not
warned: one garden's occupant withdraws nothing declared for every garden.

## leaf_orders

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

## vacancies[words.form]

AN AGREEMENT'S WORDS ARE DECLARED WHOLE. Written, spoken, or not yet put into words: the three ways any agreement
stands, and a stranger keeping one expects to find each. A closed list on a mapping's own attribute offers positions
like any entry's, and was not counted until the reverse gate learned to count it; `spoken` is taken, and the other two
are declared for every garden that does not stand on them. The domain profile's `registration.auto_renew` is declared
whole for the same reason.

## vacancies[registry:storage_formats]

Measured at zero across the corpus on 2026-08-07, when it was declared.

## vacancies[responsibility.entry_one_of]

When it was declared, no facet in the estate the law was first written in was co-owned, so none was co-answered-for.

## vacancies[external]

When it was declared, the estate the law was first written in had recorded no duty borne by an outside party.

## vacancies[contingent]

When it was declared, every requirement recorded in the estate the law was first written in was load-bearing: all 5 of
its consumes/depends_on edges sat at `necessary`.

## vacancies[physical]

When it was declared, no being in the estate the law was first written in was recorded as a physical copy, and the
operator named exactly that case — a codebase as a printed listing or a disk in a drawer — when the term was designed.

## vacancies[network-segment]

Declared at 11.0, with the operator's ratification that a segment is a place and not an address, while no bean yet
stated which segment it was attached to.

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

## figures[sequence].holds

A POSITION MAY HOLD WHAT WAS FOUND THERE (D47, "develop the sequence machinery to fit the need"). A perfusion chart, a
moth's night, a dendrometer's record, a core's strata and a case's stages are one shape: a line, positions on it, and at
each what was read. The operator ruled out a separate series form, so the sequence figure gains the capability beside
the one it had — `extent: possible`, a region of the line — and nothing is restated: a series' positions are the
recurrence's occurrences or an extent's offsets, both forms the law already owns. An opposition's positions are stances
a being takes; there is nothing further at one to hold, so it says `holds: impossible`, and the reason is printed where
a series is refused for lying on one.

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
ended the ledger in a traceback. A share is bounded the same way. An explicit `!!int` asks the loader the same question
and gets the same answer: the tag builds an integer only from plain decimal, so `!!int 010` is the text `010`, refused
as the untagged text is — the library's own constructor would have read it, quoted or not, in all four spellings.

The count keeps what was written. A merge compares counts by the exact value they write, so `900`, `"900"` and
`"900.00"` are one amount and never a conflict — the shortest exact decimal is the one canonical form.

## value_types[text]

TEXT IS WHAT A PERSON READS. A key and a string value are read by a person and printed by every tool, and a control
character is neither: nobody reads it, and a terminal obeys it. An escape sequence in an agreement's title, which
YAML's double quotes write as `\e`, moved the cursor up, erased the line a reader trusted and wrote the debt the other
way round; one in a path the gate itself quotes cleared the screen on every commit. The journal refused such
characters already; a bean, the thing the journal is about, did not. So text holds no character of the Unicode control
category: a tab, which a person types, is let through, and a line feed is held where a value's lines are lines on the
page — a block scalar. The same characters escaped inside double quotes (`"a\nb"`) make one line on the page two in
every reader, and `"C:\01-files"` silently held a NUL where a person wrote a backslash and a zero; both are said plainly
now, with the way to write what was meant. The rule is a value type, because every other type is text first; the
gate reads it from the node graph, where a scalar's style is known, and names the character rather than echo it. A
tool that prints what a garden already holds spells such characters out, so a garden written before the rule cannot
drive the terminal of the person reading the refusal.

## value_types[moment]

A MOMENT IS A JOURNAL HEADING'S POSITION, and nothing new. The heading has always been held to the minute, with its
offset, in any declared calendar; a value the save stamps from the clock takes the same form, so it is the form the
tool writes and the gate reads. Without the offset a wall-clock reading is ambiguous — the law's own `gregorian-civil`
row says why — so a moment always carries one. A day its calendar lacks is no moment, as it is no date.

## value_types[rows]

ONE TABLE, WRITTEN BY ONE WRITER (sequence critic §5.1, F11). The three sequence designs all kept a short series inline
as a tab-separated block, and none noticed that the merge re-emits a changed member through PyYAML, which will not
write a tab in a block even when asked: a merged chart came back as one escaped line, the same value and a page nobody
can read (measured, Y1). So the table has one reader and one writer, both in the parser, and the merge and the
proposals write a table through it, byte for byte. Tab-separated rather than space-separated because a cell may hold a
space; a file only, never inline, would put a five-row stratum table outside the bean it describes.

NO CELL IS EVER EMPTY (settled row 4). An empty cell leaves a trailing tab on a row, and an editor that trims trailing
whitespace changes the number of cells — measured in a design's own example, eleven of twelve rows. A value nobody read
is a gap token, which also says why.

A HUNDRED ROWS inline, then a warning: a bean stays legible on paper, and the pure-Python YAML reader a machine
without libyaml falls back to reads a large block sixty-five times slower (Y2). Measured again as the reader and the
writer were built: a block of 350,400 rows (6.9 MB) loads in 0.04 s with libyaml and 2.4 s without it; the table
reader then reads it in 0.29 s and the writer writes it in 0.42 s. The rows belong in the parts of a file
then, and a warning says so without refusing a bean that passed.

## gap_tokens

A GAP IS STATED, WITH WHY. A blank and a zero both lie about a missing reading: one says nothing and the other says
something false. The six tokens are the reasons a value is absent that the designs' cases met — nothing read, read and
unreadable, beyond an instrument's limit (with the limit, or the channel's own), nothing there to read (a core not
recovered, a ring never formed), and withheld from this copy, which a partial export of a held series needs. Nothing is
absorbed at a merge: a gap against a value is a disagreement a person sees, never the value winning.

## journal

== THE JOURNAL (10.0, T3): where the record of what was done is, and how an entry is headed ==
The journal is the garden's time record, and it had no rule for time. One real garden, measured on
2026-09-19: 663 entries, 276 headed with a date only, 387 with a time in `+0300` or `+0330` while the calendar
system's one form is `+03:00`; and one entry headed 23:59 that was committed at 23:32, a precision written
rather than read. A heading is now a position in a declared calendar's own form (gregorian-civil's until 18.0), held to
at least the MINUTE, with its offset, because an entry is ordered against every other and a reading with no offset
cannot be.
Only headings ADDED by a commit are checked: the journal is never rewritten, so its history keeps the forms
it was written in, and those stay what they were.

## journal.checks

entries a commit adds; never the history


## journal.origin

STAMPED, NOT TYPED (20.0; since sources-by-nature, the heading read `by: save`). 10.0 made a heading a position in time and the gate checks its form; the truth of
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

`impossible` was first occupied on 2026-08-02, by a domain's backup MX record that named its own primary.

## aspects[permission].meaning

The SECOND aspect, and the first evidence that the machinery generalises. It reuses the square of
opposition but NOT the same square: `necessity` is ALETHIC modality (what IS the case — this input is
required), while capability is DEONTIC (what MAY or MUST be the case — this being must not do that).
Conflating them is the same error as one axis doing two jobs: "this VPS cannot send mail directly" and
"recursion must stay off" feel alike and are not — one is a fact about the world, the other a rule.
Positions relate a being to a CAPABILITY (an open kebab name), not to another being, which is what
the necessity aspect could not express.

## aspects[permission].poles

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

## view_lenses

FOUR READINGS OF ONE DRAWING, EACH FOR ITS READER. A page drawn once for everybody is drawn for nobody: a newcomer needs
the promise and the path, a manager the causes, the person on call the one vital sign, an auditor the evidence. So a
drawing is read at four lenses, each a row: its `depth` orders them, its `form` says how it is drawn, and `max` bounds
what it may hold, so a lens that grows past its reader's attention is refused by the asset rather than tolerated. A
REGISTRY and not a term, as `roles` and `planes` are: the rows are the one owner of the lenses, and
`views.questions.lens` and `view.fields.shown_from` take a row by name, so a lens nobody declared is a refusal, not a
new lens. What each lens leaves out (an address, a live value) is said in its `meaning`, because a drawing that shows
an address at a lens whose reader should not see one shows it to every reader of the page.

## view_archetypes

THE SHAPE A VITAL SIGN IS DRAWN IN. What the person on call must know first differs by what is drawn: a store fills
toward a limit, redundant paths must each get through, a stream narrows. Each shape is a row, and what it needs is
stated once, as a `cells` requirement on `views` (a reservoir requires `fill` and `thresholds`), so the gate refuses a
shape that cannot be drawn; the asset holds the drawing code, and no second list of what a shape needs is kept in it.
The `race` row reads the steps of the procedure a view `draws` — its `steps`, a walk on the `routine` sequence — in
place of a table of phases, which would restate them. `health-chain` is the fallback, named so that falling back is a
choice written down.

## terms[observations]

A READING IS KEPT AS IT WAS MADE, AND WHAT FOLLOWS FROM READINGS IS READ (24.0, step 5). The shape is ISO 19156's: a
property, a feature of interest, a phenomenon time and a result, with the procedure and the observer. The property is
a code of a published scheme and never a garden's own word, so two gardens' readings of one thing meet by code. A
reading made again is a new entry: growth, drift and recovery are read from the entries, never stored beside them,
where they would go stale. `beanger` keeps one field's own history at the moments it was written; an observation keeps
the world at the moment it held.

## terms[observations].schema.attrs.by

WHO READ IT IS A BEING THE GARDEN HOLDS (24.0, N19). A reading's weight depends on the standing of whoever made it — a
person, an instrument — and standing can only be read from a bean. An observer written as a name alone could not be
weighed, nor asked again.

## terms[observations].schema.attrs.answers

A VERDICT IS AN ENTRY OF ITS OWN (24.0, N20). A second observer who confirms, disputes or will not say writes that as
an entry which answers the first, so the first is never edited by someone who did not make it, and the disagreement
stays visible with both speakers. One observer gives one verdict on one entry, wherever it is written: two would be one
voice counted twice. The answer `abstains` records that someone was asked and would not say, which is different from
never having been asked.

## terms[observations].schema.attrs.presence

AN ABSENCE IS A FINDING (24.0, step 5). A sign looked for and not seen, a list that does not name something, is
evidence, and a reading that simply is not there says nothing. An absent entry states no result, because a result
beside an absence would contradict it.

## terms[observations].schema.attrs.retracted

A READING IS WITHDRAWN, NEVER ERASED (24.0, step 5). Its observer's withdrawal is kept with the day it was made, and a
reading after that day does not read the entry. Only the observer can withdraw it, so the entry carries its own
provenance stated by a person.

## terms[hearings]

A DISAGREEMENT IS HEARD BEFORE IT IS RULED ON (24.0, N21; manifesto: heard). The entries in dispute, each speaker's own
words and the ruling are kept together, and the gate refuses a ruling while a speaker of the entries it is over has not
been heard. A ruling that skipped a side would be the record of a decision nobody could check was fair.

## knowledge_scheme_form

A SCHEME SAYS HOW ITS CODES ARE HELD (24.0, step 6). Some are small and free and ship with the release; some are a
garden's own, kept as an extract it edits as ordinary journalled writes, so configuration such as kinds of leave or a
questionnaire's questions is data, not law (F9, N28); some are too large, or not ours to copy, and are held at their
publisher and checked here by form alone — and the gate says once that they are not looked up, so a pass is not read as
more than it is. Licence and release say under which terms and from which edition the rows are, which is what anyone
passing them on needs.

## knowledge_scheme_form.sensitive

SENSITIVITY FOLLOWS THE CODE, NOT THE FIELD IT SITS IN (24.0, F3). A diagnosis is special-category material wherever it
is written, so the mark sits on the scheme once and every code of it carries it; nothing is left to a writer's memory.

## knowledge_scheme_form.relations

RELATIONS BETWEEN A SCHEME'S OWN CODES ARE ITS OWN ROWS (24.0, N23). Part of, requires, adjacent to: a scheme's
structure beyond its tree is kept as a table of its codes, resolved like any other link, so the finder and a reading can
follow it and a code that is not the scheme's is refused.

## knowledge_scheme_form.labels

A LABEL IN ANOTHER LANGUAGE KEEPS ITS PUBLISHER'S WORDS (24.0, N25). Translations are often published on condition
that an attribution is printed with them. The attribution is kept verbatim beside the labels it covers, and every reader
that prints a label prints it.

## profiles.code.terms[code_paths].meaning

The 'paths vocab' (added 2026-08-01, human-directed): so an agent LOCATES code without re-walking a tree,
and knows which trees are REFERENCE-ONLY (never re-scanned each session).

## profiles.code.terms[code_paths].schema

GATE (P2): enforced generically from here, not from code

## profiles.code.terms[code_paths].schema.required_on_gene

a genos:codebase bean MUST carry a non-empty code_paths

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

## profiles.network.vacancies[pptp]

Measured when it was declared: zero occurrences of pptp across the estate the law was first written in.

## profiles.network.vacancies[registry:anchor_systems]

Measured on 2026-08-07 rather than assumed: no being in the estate the law was first written in answered at a v6
address. A host booted with `ipv6.disable=1` recorded it as `capabilities.ipv6-socket-binding` with feasibility
`impossible`, and the only v6 address anywhere in the corpus was `2001:db8::53` — a REMOTE resolver a VPS failed to
reach, which is a fact about somebody else's endpoint and not about ours.

## profiles.network.terms[reaches].meaning

WHAT A BEING NEEDS TO TALK TO. Deliberately NOT a dag: a server reaches its router and the router reaches
the server, and that is ordinary rather than a cycle to be refused.

## profiles.network.terms[treatments].meaning

NOT A LAYER, AND KEPT OUT OF THE STACK ON PURPOSE. routes, nat, mangle and acl are not positions
in a protocol stack — they are what a forwarding device DOES to traffic that is passing through
it. Folding them into `endpoints` or `links` would be the force-fit that ground rule 2 forbids:
the shape would be satisfied and it would be the wrong shape.

## profiles.network.terms[treatments].schema.required_on_roles

7.0: was `required_on_kinds: [router]` until `router` stopped being a genos

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

## profiles.view

A PAGE THAT DRAWS WHAT THE GARDEN KEEPS, AS AN OPT-IN PROFILE. Documentation and live values that live apart drift
apart; the profile puts both on one page, drawn from the garden's own records. It is a profile, not the core: a garden
that draws nothing inherits none of it. Its contract is law the gate checks — four terms on one page bean, two
registries — and opting into the profile is what brings its asset, `assets/view/`, read through `bin/dmpass.py`, the
one reader of what a release ships: there is no second list of files and no second upgrade.

NO ASSET OPENS A CONCEPT OF ITS OWN. Everything the page says is a construct the law already has: what it draws is a
`ref` to a mapping or a bean; a length of time is an `extent` on `time`, a repetition a `recurrence`, a share a
`quantity` of `ratio`; a technology is a row of the `technology` registry; a value named in a drawing is a `key_of`
`view_bindings`; a being is a `bean_id`; an address is the being's own `located_at`, never restated on the page. Every
name the profile adds is held against the law's own names, so none is given a second sense (test/assets.py).

## profiles.view.terms[view]

THE PAGE IS ONE BEAN. Every fact the page states sits on the bean that carries `view`, and nothing about the beings it
draws is written on them: a binding says what the page shows at one drawn element, which is presentation, not a fact
about the being. The page names the garden's own drawing module by a `file:` `pointer`, which the gate resolves, and
the module stays the garden's code. `reference` chooses, per being, the place system whose position stands for it, and
the position is the being's own (`located_at`, its anchors, its `endpoints`): an address kept on the page would be a
second statement of it, and it drifts. `fields` says per genos, as `registry` rows of `gene` and `view_lenses`, which of
a being's own facts its card shows, from which lens on. `opens_on` is a `bean_id` held to the genos `org`.

## profiles.view.terms[view].schema.attrs.visibility

WHO READS THE PAGE DECIDES WHETHER ITS DRAWINGS CARRY ADDRESSES. A drawing is sent whole to everyone who may see it,
so an address in its text is shown to every one of them, and a page that may be published must show none: that is
the public page, and the default, so a page that says nothing fails closed. A private page is read only by the
viewers its host signs in, and for them a network map without its addresses is not a map. So there each part shows
its own address, taken from the being's own record by the page's `reference` and never restated on the page, and
the host sends it only to a viewer who may see that being, the grant that already decides the part's card. What a
drawing's own text says (a range, an egress line) belongs to no being the host could ask about, so it is shown to
every viewer of the drawing, and the page says so by being private. An enumeration and not a flag, as `openness`
is: the two values say who reads, and what follows from that is the asset's.

## profiles.view.terms[view_monitors]

WHERE LIVE VALUES COME FROM IS A BEING THE GARDEN HOLDS. A monitor is a `bean_id`: what it watches is its own `reaches`
and the targets' own `endpoints`, and which technology it runs is its own `knowledge`, so the asset picks the adapter
for that technology by the monitor's record and never by a name written in code. No technology is privileged: a
monitor of another technology is read by that technology's adapter, beside the first. What only one technology needs —
its alert rules, the credentials it reads by name — is pointed at by `settings`, a `pointer` into the monitor's own
record, stated and not checked until a term the law declares carries it, when a second technology or a second garden
shows what is general.

## profiles.view.terms[views]

ONE ENTRY PER DRAWING, CHECKED AS DATA. Each entry `draws` a `ref` — a mapping of `kind: procedure` or a bean — and
never restates what it draws. The operate lens's settings are typed attributes of the entry, and each archetype's
needs are `cells` requirements, so the gate refuses a reservoir with no thresholds and a race with no step. Time is
written in the law's own forms: a deadline or a span is an `extent` on `time`, a sampling interval a `recurrence`, and
a threshold a `quantity` of `ratio`; a length is never written as a bare number whose unit a reader must guess. The
values a shape reads are `key_of` `view_bindings` on the same page. The inspect lens's processes and pipes are
`pointer`s at the entry's top level, where the gate resolves a `{bean, field}` pointer, to the field of the being that
states them. A race reads the steps of the procedure it draws, 0 before the first and n at the n-th, so its phases are
the procedure's own.

## profiles.view.terms[view_bindings]

A LIVE VALUE IS READ WHEN THE PAGE IS DRAWN, AND NEVER STORED. A binding says which drawing and which element it sits
on, which of three kinds of live value it is (a `values` list, declared whole), its unit as a row of `units` and its
limits as counts in that unit. How it is computed is one entry per technology (`entries` `keyed_by` technology), each
in that technology's own language, so a second technology sits beside the first on the same binding rather than
replacing it; the adapter refuses what it cannot read. A unit the law does not have is a row a garden adds to `units` in
its VOCAB.md, and a temperature waits for the law's own temperature position rather than a unit that is not one.

## profiles.view.vacancies

DECLARED WHOLE. The nine shapes and the three kinds of live value are offered to every garden that extends the
profile, which takes the ones its drawings need; the rest stand vacant with the reason `universal`, so a stranger's
garden finds each where it expects it, and nobody mistakes the design for evidence.

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

LOCAL gene (`local_gene`): object types this garden manages that std-vocab doesn't schematize. Each gets a small
schema (MODEL Rule 6). A genos that proves general is promoted alongside its terms.

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
commit. A list that names four gene when the rule holds for all is a second copy waiting to disagree.

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
SCOPED BY SENSE, NOT BY RULE: `closed` belongs to the gene that BOUND their work — session, program,
contract. Nothing forbids it elsewhere and nothing should invent a per-genos status mechanism to try;
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

DERIVED SINCE sources-by-nature (2026-09-26): `order: source` ranks the values by what `values_source` says each is — its
act, then its nature (`acts`) — so the rank is read, not written. It came out as the written one did, which is the test
of the reading, and it placed the value the written one had no room for: `stated-in-document`.

## terms[provenance_src].values_meaning

EACH PLACE IN THE RANK, EARNED. The rank orders HOW A FACT IS KNOWN:

## terms[analysis_cache]

`borrows` IS WHAT THE MERGE READS; `values_meaning` is for the reader. The LABEL is never rewritten — a
merged value still says a tool produced it, which Phase 7 (2026-08-03) showed is exactly what must not be
lost or gained by passing through a tool. Only the weighing borrows.

restated for the human reader; the gate reads schema.key_form

**Its keys.** kebab-case <cache_type>. Known types so far (a NON-exhaustive registry, NOT an enum the gate enforces): code-structure | framework-surface | api-surface | api-client-contract | security-surface | bcf-domain. Anticipated: dep-graph | sql-schema | revit-ui | csharp-api | python-models | test-coverage.

**When an entry may be used.** An entry is VALID only while its staleness_key matches the live source at covers_paths. A STALE entry is NEVER silently used: re-run the analysis, then REFRESH the entry (new as_of + new staleness_key). Trusting a stale entry is a provenance violation, not a shortcut.

**What an agent does.** Before code of this bean is analysed, `analysis_cache` is read: an entry of the type needed whose `staleness_key` still matches the live source at `covers_paths` is used, not derived again. The code is analysed again only when the key has moved or no entry of that type exists, and a refreshed entry (a new `as_of` and `staleness_key`) is then written back. A new kind of analysis is a new kebab-case `<cache_type>` key: it asks no change of the law, the gate or the bean's shape.

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

## terms[analysis_cache].schema.required_on_gene

a genos:codebase bean MUST carry a non-empty analysis_cache

## terms[analysis_cache].schema.attrs.as_of

Rule 6: absolute dates only

## terms[analysis_cache].schema.attrs.staleness_key

11.0: a staleness key is a POSITION, and `git-head:<sha>` was resolved against whatever tree the
READER had checked out — one analysis, one verdict per machine. The git-object-graph form names the
repository, so every reader asks the same object graph. `manual:<why>` stays for what no key can track.

## mechanism_form

A MODEL IS A READING WITH A DOMAIN (24.0, step 9). A mechanism — how a tree's carbon follows from its girth, how fast a
wick burns — is written in the one reading grammar over named inputs, so the reckoner that reads a garden's own
selections reads it too, and no second evaluator exists. What makes it a model and not a fact is said beside it: the
domain its source fitted (`valid`), outside which the reader refuses rather than extrapolates, and the source's own
error, validated where the source states one, carried into the value's u. Where several are valid, the one with the
smaller validated error is read and the others are printed as the spread, so a choice between models is never hidden.

## coefficient_form

A CONSTANT HAS A SOURCE AND AN UNCERTAINTY (24.0). A coefficient is a value some source fitted or some convention fixed;
it is a row, with the cases it applies to and its u, so that a reading that uses it prints where it came from and how
well it is known. `convention` marks the ones fixed by agreement, which have no u because they were not measured.

## pin_form

A FIXED ACT NAMES THE STATE IT READ (24.0, N2). An invoice, a closed period or a verdict is fixed while the beans it read
go on changing. Recording the commit and the moment it was read at lets the same reading be read again, exactly, from
the same state, whatever has changed since — and a pin is judged to name a commit the garden has, so it cannot point at
a state that never was.

## compatibility

AGREEMENT WITHIN UNCERTAINTY LABELS, AND NEVER DECIDES (24.0). Two values of one measurand whose difference is within k
times its uncertainty are compatible in the metrologists' sense (VIM 2.47). The label orders what a person is shown; two
compatible values that differ stay two values, each with its speaker. Counts, money, anchors, codes and names are
exact, and are never called compatible: they are equal or they differ.

## ordering_keys

WHAT IS SHOWN FIRST IS COMPUTED IN THE OPEN (24.0, step 10). A merge's disagreements, a working loop's tests, a garden's
guards and its improvements are each ordered by a key the law declares as a reading, so the arithmetic that puts one
thing first is written where anyone can read and check it. A key only orders: the Contract's classes come before every
weight, and nothing is hidden or dropped by being last.

## terms[weighings]

A JUDGE'S JUDGMENTS ARE WRITTEN, AND THE WEIGHTS ARE READ (24.0, step 10). Pairwise judgment is the analytic hierarchy
process's way to weigh criteria a person cannot weigh all at once; only the judgments are the judge's facts, and the
weights and their consistency follow from them. Stored weights would go stale beside their judgments, so they are
never written. A consistency ratio above one tenth means the judgments contradict each other, and it stands only with
the judge's reason.

## terms[clauses].schema.attrs.within

AN ALLOWANCE IS AN AMOUNT WITHIN A WINDOW (24.0, N9). Ninety days within any hundred and eighty, twelve visits within
any thirty days, twenty days of leave each year: each is an amount and the stretch it is counted within, sliding or cut
by a calendar's level. What uses it is a reading (`used_by`), so the use is counted each time it is asked, never kept
as a running total that could drift from the entries it counts.

## terms[nature].meaning

Ontological type of a being — the routing key from a bean up to the ownership crown (MODEL §Ownership).
soma -> physis (φύσις), lekton -> logos (λόγος), empsychon -> agape (ἀγάπη); all resolve up to theos (θεός).
The crown is a MODEL axiom, NOT instantiated as beans. Until 22.0 the same routing was said in Latin, after
Descartes and Spinoza: physical -> nature (res extensa), metaphysical -> logos (res cogitans), living -> love
(conatus), all up to god (Deus sive Natura) — see `natures` for why the words changed.

## terms[nature].schema

GATE (P2 interpreter; P3 made it the root axiom)

## terms[nature].schema.required

P3/D1: MANDATORY on every bean, whatever its genos

## terms[nature].schema.must_equal_genos_attr

and it must agree with the genos that refines it

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

## terms[owned_by].schema.entry_form_from_genos_attr

a genos may PIN which form it must use (see genos: person)

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
enforced would have forbidden a machine of the nature soma any `fqdn` anchor at all. The nature decides whether a name
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
`openpgp_fingerprint` was classed as from the start. So both key terms are `logical`, and unpinned: for an
ensouled or a sayable being (empsychon, lekton) a key is the strongest logical anchor there is; for a body it
corroborates.

## terms[mac].anchor

Matter when burned in; assigned when virtual. A physical NIC's MAC establishes the machine; a virtual NIC's is
written by the hypervisor and moves with the VM's definition, so on a `virtual-host` it can only corroborate.
The class stays `hardware` — that is what the fact is — and the pin was dropped at 19.0 so the family rule can
say which.

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
An `identifier` stays for a document whose home names it.

## terms[id].enforced_by

kebab-case, id == filename, and uniqueness per (space,base) are CORE bean-grammar checks — schematising them would duplicate a rule that already bites.

## terms[ref].meaning

NARROWED at 2.0 (P6/E6): this term used to CLAIM refs/consumes/depends_on and state the DAG rule for
them. Those are now first-class relations with their own schemas, so `ref` describes only the LINK
FORM they share. This is the MAJOR change of the release: an existing term's handling moved.

## terms[ref].enforced_by

the link FORM and its resolution are CORE checks (target exists, named field present, shallow). Since 2.0 the acyclicity is declared per relation via schema.dag rather than here.

## terms[genos]

== THE BEAN-GRAMMAR AND FACT-SECTION KEYS (added std-vocab@5.0, 2026-08-02, human-ratified) ==
These were never terms. They did not need to be while the gate enforced them in CORE and nothing else
read them — but `bin/dmmerge.py` became generic over top-level keys, and a key with no `merge:` facet
is merged by a SHAPE GUESS. A guess can be the wrong guess, so each of them now declares how it
merges. Most ratify what the guess already did; the three that do not are marked.

`genos` is the type of a being, and was `kind` until 22.0; why the Greek word, and what else was on the table, is
under `natures`.

## terms[kind]

A MAPPING KEEPS ITS KIND (22.0). A bean's type is its `genos`: a row of `gene`, refining a nature, deciding its identity
policy and the forms its ownership may take. A mapping records a procedure or a relationship — a checklist, an
automation — which is no being: it has no nature, and its `kind` is read from no registry. Renaming it with the bean's
would have said that a checklist is a genos of being. So the two keys part at 22.0: a bean says `genos`, and the gate
refuses `kind` on a bean with where it went (`retired`), while a mapping says `kind` as it always has.

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

## terms[merge_conflicts].meaning

A CAPTURE IS WHAT THE DRIVER WROTE, AND NOTHING LOOKS LIKE ONE BY ACCIDENT. The rules stand down on a value two
gardens hold two ways, so that a disagreement can be committed whole and settled by a person. They stood down on any
record written `{conflict: …}` under a `merge_open` marker, and so a document could shield values the gate refuses — a
party nobody is, a day no calendar has, parts that do not add up — behind one warning: with the path left out of
`merge_conflicts`, with one side, or with other keys beside `conflict`, none of which the merge driver writes. What the
driver writes is exact: the marker, the path named, and a record holding two values or more that differ. That, and only
that, is a capture; any other conflict record is refused, named at its path, and a person picks a value.

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

## terms[clauses].schema.attrs.each

AN OCCURRENCE NEVER LEAVES (24.0, N3). A share of each sale is one clause, not one per sale: the clause occurs once for
each member a reading holds. Were an occurrence allowed to leave the reading — a sale later refunded dropping out of
"the sales" — what was owed for it, and perhaps paid, would silently stop existing, and a refund would be owed twice
or never. So the reading uses only conditions that cannot be lost (`comparators[].monotone`: a step reached stays
reached), and a refund is its own clause, the reverse, occurring once for each refund. `settles` names the
occurrences a payment is for, each its own amount, so one payment across two rates is read exactly.

## terms[clauses].schema.attrs.falls_due

A DUE RELATIVE TO ANOTHER POSITION IS READ, NEVER STORED (24.0, N4). "The tenth of the month after each tuning" is a
rule; the day it gives is derived each time, as a balance is. Its place in the cell reached is `at`, as a
recurrence's is — not `on`, which YAML 1.1 reads as the boolean true, the defect `transactions.day` was renamed for.

## terms[clauses].schema.attrs.when

A CONDITION IS A READING WHERE ONE CAN SAY IT (24.0, N6). Written in prose, "once the parts arrive" is true or false
only to a person reading it. Written as a reading, the reader knows whether the clause is in force, and a clause not
yet in force is silent rather than a due date called missing. Prose stays, as `said`, for a condition no reading can
say yet; a bare string is refused so that the two are never confused.

## terms[clauses].schema.expiry

THE WORDS FOLLOW THE STANCE (24.0, N5). "Falls due, and from that day the party is owed it" is wrong for a permission,
which is never owed: it opens, and it lapses. The words are chosen by the clause's position on the capability square,
so a reader is warned of a permission's window closing in a permission's words.

## terms[parties].schema.attrs.acting_for

WHO ACTS IS NOT ALWAYS WHO IS BOUND (24.0, N13). An employee, a lawyer, a parent: their act binds another party. The
agent is a party of its own, with its own acceptance, and says whom it binds; a party acting for itself is refused,
because it says nothing. `declined` (N14) records a refusal as `accepted` records a yes, with the same provenance.

## provenance_record.attrs

BETWEEN GARDENS IS A ROUTING DOMAIN, AND A NAME CARRIES ITS PATH (24.0, ratified 2026-09-26). A garden is an autonomous
system and its `garden_id` its number; a being's name, announced from garden to garden, is a route. The receiver trusts
only its peer — the last hop, a garden it met — and records the rest as said, not verified: `garden` the origin, `via`
each garden after it, appended by the one that passes it on and never rewritten. A path holding the receiver's own id
after its origin is a loop and is refused, as a path-vector protocol drops a route carrying its own number. Facts do
not travel this way: what a third garden said is still not a garden's to pass on; only the name, and a person's
`consent` with their name, as a community travels with a route.

## recurrence_form.closures

AN OCCURRENCE THAT DOES NOT FALL IS SAID (24.0, N7). A lesson each Tuesday and Thursday, an hour long, not on a
holiday: RFC 5545's DTSTART with DURATION and EXDATE, in the recurrence's own system. A closure still counts toward
`times`, as an EXDATE does, and the reader is told of it rather than left to find a lesson missing.

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

## terms[steps].schema.attrs

A STEP SAYS WHAT A CASE ON IT NEEDS, AND NOTHING ELSE (N11, F8; S2, major). A client-work case's walks needed who acts at a step,
how long it usually takes, the ways out, a pause that comes back to where it was, an end that is final and one that is
not (a client given up returns), and the reasons a move may cite; the machinery's tree needed what a step takes in and
gives out, stated once on the step. The gate read only `id`, `do` and `next`, and every other key passed unexamined —
a walk with `by`, `usually`, `exit` and `reasons` in shapes of a writer's own choosing passed with no comment. So the
term declares its attributes, each step is judged as an entry, and a key it does not declare is refused: a garden whose
steps carry another key stops passing, which is what makes this major. Prose steps stay legal: the term declares no
shape. A pause and a way out are reached from any step, with no `next` naming them, because a case can be put on hold
or withdrawn at any stage; a pause is no end.

## schema_language.moves_along

WHERE A CASE STANDS IS READ, NOT STORED (N10, F8; the client-work and platform cases). A stage written on a case is a
second copy of its last move, and it drifts. A course is a series along time whose value at each move is a step of a
named walk: the moves are the facts — the step reached, who moved it, a reason from the step's own list, why in words,
and the moment, stamped. The gate holds one course's moves to its walk: a move follows a `next`, reaches a way out or a
pause, returns from a pause to where it was, and nothing follows a final step; a move the walk does not offer passes
only with its `why`, and warns, because the world does not always follow a procedure and the record must say so
rather than refuse it. The moves merge by course, moment and step, so a step visited twice never collides with itself; a move is stamped to the minute, so two moves of one course to one step in one minute would be one move written twice, and the gate says so before a merge must refuse it.

## terms[courses]

A COURSE NAMES ITS WALK ONCE; its moves name the course. The moves are a list of their own term, not nested in the course,
so two gardens' moves of one case unite by their key at a merge instead of one course entry conflicting with another.

## terms[moves]

A MOVE IS KEPT, NEVER REWRITTEN. Each is who moved the case, to which step, when and why; where the case went next is the
next move, so the list is the case's history and its present is read from its end. The moment is stamped by the save.

## terms[items]

A CHECKLIST IS A SET, NOT A WALK (the client-work case). A sequence is positions related by neighbourhood; a checklist's
items have none, so they are a plain list, and items of which any one will do share a `one_of` name. What makes an
item needed, and what meets it, is a selection over the beans of the case — so the law names no garden's own term (a
document's kind) inside an item. The selection's own form is declared with the reckoner; an item names one by the bean
that declares it and its key.

## terms[located_at].meaning

THE BEING'S LOCATIONS. The meaningful object is the being — a codebase — and it may be found as a
tree on a host, as reachable objects in a repository, or as a PRINTED COPY on a shelf. None of those
is privileged and a being may be at several at once. `openness` is the field that carries what cost
this estate a session: a position that is NOT KNOWN is recorded as unknown rather than omitted,
because an omitted location reads as "there is none" and that is how an exhaustive search over the
wrong domain produced output identical to a real one.

## terms[lines]

A BEING LENDS A LINE (sequence critic S4). A depth down a core could not be written: in coordinates it is refused, and
in a local frame it has no length. The being says once where its line starts and which way it runs, and a position on
it is a distance in metres, in the `along` system.

## anchor_systems[along]

METRES, WRITTEN IN THE POSITION (settled row 14). A counted position within a being already has a system (`local-frame`,
a ring counted from the pith); a distance along one did not. The form names the being and its line and carries metres
always, so it describes itself: a unit kept on the bean would silently re-read every position the day it changed. The
`+` is required, since `<being>/<line>` alone is a network segment's form.

## anchor_systems[relative]

WHERE AND WHEN ARE ONE MECHANISM (24.0, PLACE; ratified 2026-09-26). A position is an offset from a DATUM: a being
named in the position (`datum: being`), or a position of another system, before or after it. `marker-a+3.2,-1.5` is
metres east and north of where the mark is; `bp1950:3.93ka` is anni before 1950. The two were first drafted as siblings
— a place reader and a deep-time reader — and the operator saw they were one ("ain't it obvious yet the fuse of the time
and place?"). An offset taped from a mark survives the receiver that placed the mark, and is good to centimetres where
the receiver is good to metres: that is why the report of fixed beings with no such offset exists (`dmreview --places`),
as a policy printed and never a rule. The form is `+`, since `local-frame` owns `#` and `along` owns `/`: one spelling is
read by one system (test/place.py).

## anchor_systems[bp-1950]

AN AGE BEFORE THE PRESENT IS AN OFFSET, NOT A CALENDAR (24.0, step 8). Deep time lies beyond every calendar's reach,
and the sciences that count it name their present: 1950 for radiocarbon, 2000 for ice cores. Each system states its
datum in structure, so `b2k = bp-1950 + 50 a` is COMPUTED from the two datums and written nowhere as a constant that
could drift from them. The unit symbols name the law's fixed-length anni, never a calendar year.

## anchor_systems[ics-chronostrat]

A CELL OF DEEP TIME IS FIXED BY A MARK, AND ITS AGE IS A READING (24.0, step 8). The International Chronostratigraphic
Chart names the units of Earth's history at seven levels, and ICS fixes the base of most by a Global Boundary Stratotype
Section and Point: one point in one rock section, where a marker appears. A better dating moves the age and never the
boundary. The chart's units are the system's cells (`cells_in`) and the GSSPs its boundaries (`boundaries_in`), each
shipped as published (CC BY 4.0, International Commission on Stratigraphy). The margins the chart states are kept as
said: it gives no probability, so none is read. `AT` IS BEING-IN (در بودن, the operator's word): a position names the
cell it is in at some level, so an age within a boundary's margin is in both cells beside it, and neither is chosen.

## aspects[fixing]

TWO WAYS A BOUNDARY IS FIXED, AND THEY ARE CONTRADICTORY (24.0, PLACE). ICS itself sorts its boundaries so: a GSSP is
fixed by a point in the rock, a GSSA by an age declared with no point. The pair is general — a survey datum fixed by a
monument, a zero fixed by decree — so it is an aspect of its own, and the pole a boundary is on says which dimension
establishes it and which is read from it: the cut `establishes` already makes for anchors.

## terms[fixes]

A MARK IS SAID AT BOTH ENDS (24.0, PLACE). A boundary a table says is marked in a being, and the being that says it
marks it, are one fact seen from two sides, and the gate holds them to each other as `inverse_of` holds a relation and
its mirror: a mark the being does not claim, a claim the table does not make, a mark along another being's line, and a
mark on a boundary declared as a value are refused. The level is a position `along` the being's own line: the distance
up a quarry face, down a core, into a stalagmite.

## terms[located_at].schema.attrs.mobility

PLACE IS READ AT A TIME (24.0, step 7). Rootedness is a position over a window, never a kind: a tree is `fixed` while
`during` holds, and a transplant is two entries. The readers take a moment and answer where a being was then; one that
dropped the time would say where a tree stands today about a survey taken before it was moved. Motion is read only
between fixed marks.

## terms[capabilities].schema.attrs.within

A STANCE HOLDS SOMEWHERE (24.0, N26). A permission on a code of a published scheme — and on every code beneath it — is
held within a place, in that place's own system, so a seed library's rule for crop seed on its island is one entry and
never a sentence.

## terms[timing].meaning

WHEN, AT A DECLARED RESOLUTION. The open key is what makes this serve sessions without a session
schema: `start`, `sync`, `stop` are keys, not law, and a run with four sync points needs no
rule-change to record them. The closed part is each entry's shape — the same open-key/closed-figure
pattern `analysis_cache` proved.

## terms[series]

THE WORLD ALONG A LINE (D47; sequence critic §6, S0–S5). One entry is one recording: its positions by rule or listed,
the unit an offset counts, where a row sits, the channels and the rows. Everything else a reader needs is read and
never stored — a value between rows, a window's mean, a trend — and printed with the rows it came from.

NOTHING IS COPIED FROM ANOTHER FORM (settled row 1). A grid is a recurrence whose occurrences hold rows, and a listed
series is an extent whose offsets do; the stride stays a whole number of the unit held (settled row 5), because a
decimal stride is a unit not yet chosen.

A CHANNEL HOLDS ONE KIND OF THING: a measured value in one unit, a position in a system (temperature is a position, D8),
or a code of a scheme. What a cell stands for over its row's place is said, so a mean is never read at a point and a
point never summed over a region. Between two rows only a point on a metered line and a metered channel is read, on a
straight line (settled row 6): anything else would invent a measure the law denies. An uncertainty is the channel's,
and a value read with it is printed to its digits (GUM 7.2.6, settled row 16).

A JUDGMENT NAMES ITS JUDGE (settled row 7). A cell set aside is kept and shown, with who set it aside and why, and read
by nothing — never a flag on the row.

WHERE THE ROWS SIT (F12). A short table stays in the bean; a long one is the parts `series/<bean>/<key>/<part>.tsv`, in
the estate, because a garden's own readings are its facts and not a capture of someone else's. A part is written once
and never rewritten: a new download is a new part, so two gardens' parts meet as a set of files with no merge driver,
and git's own object id pins each one, so no hash is stored. Git neither turns a part's line ends nor merges it as
text.

KEPT OFF GIT (F13, F14). A special series is sealed whole in the held layer, and the entry says nothing but where; it
waits for that layer, so the position is declared and vacant.

## terms[roots].meaning

THE RESOLUTION HALF of the `root:` position form. A bean says WHERE a thing is in a portable way
(`root:src/app`); a HOST says what that root means on itself. Two hosts therefore
never edit the same text to disagree about a path — each states its own resolution on its own bean,
which is what makes adding a machine a one-line change instead of a corpus migration.
It lives on the HOST because that is whose fact it is. A root map in a shared file would be one
document every machine has to edit, which is the merge conflict this design exists to avoid.
And so the host an `at` names is the bean it sits on, and the gate says so. The resolver takes that host for
the datum and never asks it again, so a root on laptop-a whose `at` said `laptop-b:/srv/x` read as a path
here. What a machine is called is dmwhere's one reading: the bean's id and its hostname and fqdn anchors.

## terms[roots].schema.entry_must_match[·]

THE JOIN (7.0): a host's roots are stated in the path grammar its OWN OS declares, so the two
can no longer disagree. `keyed_by: os` selects the operating_systems row by a field of the BEAN,
which is the same machinery that fixes a crown branch from a bean's nature. It is on `roots` and
NOT on `located_at`, deliberately: roots is the host describing itself and every bean carrying
it has an `os`, while `located_at` is carried by codebases, which have none.

## terms[roots].schema.attrs.system

Pinned to the grammar the host's `os` declares since 7.0.

## terms[roles].meaning

WHAT A BEING DOES. A LIST, and that is the whole point: a server may do five things and a router one,
and until 7.0 the estate expressed the first as free text in `owns.roles` and the second as a GENOS.
Making this a term is what let the genos `router` be retired without losing the requirement that a
router document its treatments — `required_on_roles` reaches a list where a requirement keyed on the
being's type (`required_on_gene`, since 22.0) could only ever reach a scalar.

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

## terms[beanger].schema.attrs.source

The estate the law was first written in met that failure: /sys/class/net reported a bond's MAC where ethtool -P
reported the NIC's.

## terms[beanger].schema.attrs.records.in.entries.unit

The rule exists because the estate the law was first written in twice wrote a value that looked measured and was
inferred.

## system_shape.sources

WHERE A SYSTEM'S MACHINERY COMES FROM, in the one pair every position uses (sources-by-nature). A reckoning by
arithmetic is derived; one by the sky or by sight is read off a body; a table is said, by a document. A crosswalk
is derived, tabled or observed in the same way. A datum read at a being is a reading of a body; one read at a host is
mixed — a body, and the name it is kept under — so its nature is both; a datum written as a position is said. Kept
beside the words they source, not on them, because a system row states the word and the law states once what it means.

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

## terms[workspace].schema.attrs.branch

Every session before 2026-08-07 worked the main copy directly, on `master`.

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

## terms[capture].schema.attrs.source

The argument earned its place in `beanger.source` within the hour of being made: naming the command is what got it
run.

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

## gene[org]

== being-gene for the ownership / type-token / habitat model (2026-08-02, human-ratified) ==

## gene[person].ownership_form

a person may be owned ONLY by the crown (agape, while alive) — never by a

## gene[person].meaning

bean. This also RESERVES the crown form: only a genos whose row names it may name the axiom directly — a
person, and since 21.0 an agreement and a happening between people — so every other chain must pass through a
being.

## gene[host]

== gene that were in USE but undeclared before P3. Under D1 a genos need only name the nature it
refines and what it means; anchor family + min-anchors come from that nature.

Until 19.0 every row also carried prose `schema:`, `required:` and `min_anchors:` — second copies of what the
natures registry, `required_on_gene` and the anchor terms decide, and by 19.0 three of them disagreed with the
law (`org`: "or primary domain"; `person`: "email"; `codebase`: "a logical manifest id" — all corroborating
now). A row is its nature and its meaning; what a genos typically owns is the cookbook's to show. The 7.0
story of `vps` and `router` retiring into `host` moved here from the row's meaning: `vps` described tenancy,
which ownership carries; `router` a role, which `roles` carries; and the registry noted against itself that
"D5 will re-read this as an instance living_on a provider" — which `virtual-host` is.

Narrowed at 19.0 to matter: 7.0 had widened it to "bare metal or virtual" when `vps` was retired, and a
virtual machine is a `virtual-host` now — see there.

## gene[virtual-host]

A VIRTUAL MACHINE IS EMPSYCHON (19.0). At 7.0 `vps` was retired into `host` because it described TENANCY,
which ownership already carried — and the registry noted, against itself, that "D5 will re-read this as an
instance living_on a provider". Enforcing the anchor family (see `identity_policy.establishing_family`) forced
the reading: a VM has no matter, so under `host` (soma, family `hardware`) it could never be confirmed
honestly — the one rented VPS in the first garden was anchored on its name, and another carried its OpenStack
instance UUID as a `serial`, `class: hardware`, and sat provisional. What a VM IS is a running machine-instance
on a hypervisor: created, running, torn down. That is the nature empsychon, whose crown `agape` "lapses at death or
teardown", and whose family is logical — a name or the id its provider assigns (`identifier`). Tenancy stays
where it was: a rented VM is owned `external` and answered for here; a VM on the estate's own hypervisor is
owned through it and `lives_in` it. A rented BARE-METAL server stays a `host`: it has a serial, and ownership
was always orthogonal to nature.

## gene[contract]

AN AGREEMENT IS OWNED BY NONE OF ITS PARTIES. The genos meant co-ownership of one facet of one being, and had no
occupant as that; the agreements people record are between them — a cost shared, a loan repaid. Were each garden to
write its own gardener as the owner, two gardens' records of one agreement would disagree about its owner on every
fusion. So the chain may end at the crown — `logos`, for what is lekton, said and agreed — as a person's ends at
`agape`, and the parties, who can be asked, answer for it: `responsibility_form: [parties]`, reflexive like `self`,
drawing no edge.
The crown owns and never answers; the parties answer and never own. The form is a LIST, which ALLOWS the crown beside
the ordinary forms instead of pinning it: an agreement one person wrote and offers may still be owned by its author.
Co-owning one facet through a contract stays one use of it.

## gene[garden]

ANOTHER GARDEN IS A BEING. A garden this one deals with needs an identity to name — in a proposal, before a
qualified name, in a record's provenance — and an owner who can be asked; so it is a bean, anchored by `garden_id`,
owned by its gardener and answered for by them. A garden's own identity and its own gardener are never in a bean of
its own: git holds the one and the manifest names the other, and a garden describing itself would be a second copy
of both.

So the gate refuses a `garden` bean anchored by the garden's own id: it would be the garden describing itself — or a
clone recorded as a rehearsal, which is the same garden under another folder name.

## gene[document]

The law named a document's id before there was a genos to anchor it with. A document is a being:
it has an owner who is often not its holder — a bank's statement is the bank's — an identity, and copies in places.
What must not be kept whole stays out of it: a transcription of its lines is a `capture` on it, whose `redactions`
say what was left out and why, so a card number is never in the ledger and its absence is on the record.

## gene[event]

A HAPPENING IS WHERE THINGS ARE AGREED. An agreement spoken over dinner or in a call has its words at that
happening, and a happening must be a being to be pointed at. Its time is `timing`, at the resolution actually known;
who took part is `refs`, each naming what they were, because `rel` is open and the parts people play at a meeting are
not a closed list. A work session is a happening too, and keeps its own genos while the two are told apart by use.

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

Where a repetition starts and ends are POSITIONS, and the readers walk to them, so each is held as every other position
is: to the form of the system the repetition is counted in, and to a day that system's calendar has. Only `due` was
held once; a monthly clause could end on `2026-02-30`, on a Persian day in a Gregorian count, or on `garbage`, and pass.

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
== EVENT-ANCHORED, UNIVERSAL (23.0) ==
Declared in 5.1 as a prediction — "expected first in the journal" — and occupied instead by every garden that
recorded a happening whose day nobody said, because the forms show it for exactly that. A prediction that comes
true warns, addressed to whoever maintains the law; so every garden following the forms was warned on every such
event. Measured on a local model over one day's runs, five met the warning and all five called it noise ("a law
issue, not a bean issue"): a warning every writer gets for doing the right thing teaches writers to read past
warnings, and a new garden is meant to start quiet. The position belongs to a mechanism that is occupied on the
same figure — `timing.system`, through gregorian-civil and unix-epoch — so it is `universal`: declared because the
structure is whole, and a garden standing on it withdraws nothing.

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

## terms[items].schema.attrs.met_by

A SELECTION IS A PART OF THE BEING THAT DECLARES IT. A checklist item names the selection that makes it needed, and the
one that meets it, as a key of `selections`: bare on the checklist, `<bean>:<key>` on another bean. That is `key_of`,
the one way a part of a being is named, so the gate resolves the bean and the key and draws no edge. A second spelling,
`<bean>#<key>` through `bean_id`, was built first and removed before the release: two spellings of one name are two
things a merge would not compare.

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

Considered and refused: temperature in degrees Celsius as a UNIT, which needs an offset as well as a factor; and compact
strings such as `12.5 m/s`, a second spelling of what `{ count, unit }` already says. Temperature arrived at 24.0 by the
other door (`aspects[temperature]`): a reading is a position on a line, and only a difference is a quantity.

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
number while the stories moved into folded strings; a list of the gene a leak guard watched let an estate's design id
into the public law; a length threshold once measured care and was met by padding. A score in the gate would be the
largest proxy of all, and a size ratchet would push facts back into prose, where they are cheapest to count away. So
the machinery measures the preconditions — closure, one statement of each thing, no story in the law, no privileged
sibling, structure before prose — and shows them to the person who ratifies, who judges. It judges nothing.

## doc:MODEL.md#Between gardens: peering

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
person's at `agape`, and the parties — who can be asked — answer for it. Nothing owns the crown, and nothing owns the
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

WHY THE FIELD'S OWN TERMS, AND NOT THE FOREST'S: the mycelium was the first picture, and it served while one hop was
all there was. Once a record could pass on through a garden that did not say it, the questions were the ones
networks already answer — who is a peer, what one exports and imports, the path a route took, how a loop is refused —
and a picture of its own would have to be translated into them by every reader who knows them. So between gardens is
a routing domain: a garden an autonomous domain numbered by its id, its inside interior, the rest exterior, first
contact peering, and consent the export policy on a person's root. The law names the terms and no vendor.

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
So the first act asked is to write only where the agent was opened, and the rest follow from peering: record a
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

`genos` — `kind` then — used to emit a list, which `dmcheck` cannot resolve.

## doc:MERGE.md#5.2

(2026-08-02, operator-directed.) `dmmerge` converged two gardens' data while their TYPE SYSTEMS stayed divergent. A merged corpus could
therefore hold a bean of a genos the merged law never declared, or a bean in breach of an obligation the
garden that wrote it had never adopted — checked by nobody, because each garden's gate only ever saw its
own half. Promoting gene to Tier-0 shrank this; it did not close it.

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
used by `log/journal.md`, `test/golden.py`'s section headers (the maintainers' corpus test, not shipped here)
and both design beans. Two numbering schemes in one repo is a trap for a cold reader, so this one is deleted
rather than renumbered. What actually happened is in the journal.

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

## layers

THE LAYER MAP IS LAW DATA (23.1). Which file is law, which is reasoning, which is journal, was stated in five places
that disagreed: a garden's own list, the gate's derivation of the law documents from it, the tool that reads the
reasons, the README, and the door for agents. A map that decides what may flow where has to be one statement a tool
can read, or every guard built on it guards a different map. So the law places what every garden has, by the same
patterns a release uses to say what it ships, and a garden places the rest.

FIVE OF THEM ARE A CHAIN, AND THE REST STAND BESIDE IT. The manifesto, the law, the reasoning, the journal and the
record are daftar's own words, each standing on the one beneath, and `beneath` says so as a link the gate resolves
and holds acyclic. The estate is not one of them: a bean is a fact about the world, not daftar speaking. Nor is the
guide, whose values are an example's; nor the gate, which applies the law and is not it; nor the queue.

THE QUEUE IS NOT THE JOURNAL. The list of what waits for a person is edited in place as each item moves: measured in
one real garden, eighty lines of it removed over thirty-four commits. A journal is appended and never rewritten.
One file cannot be both, so it stands in a place of its own.

PLACES THAT ARE NO FILE are declared with the rest, ahead of their occupants: what a person asked, the world outside,
the clock, a model's own output, a request, a remote party, a public repository, another garden. A flow is judged
from one place to another, and a flow law with no name for where material came from could only guess.

THE KEEPER IS ANOTHER AXIS. Whether a file came from a release is read from the release's own list of what it ships.
A tool is law in the sense that a change to it is a RULE-CHANGE, and it sits in the gate, not the law, in the sense
of what it is for. Two questions, two statements. The duty to journal a change distinctly follows both: what a
release keeps, and what sits in the law or the manifesto, a garden's own law included; and an entry that moves a
file into or out of those carries it too, or a file could leave the law in the commit that changed it.

NO HARNESS IS NAMED. A path that one agent's harness reads from is a privilege written into universal law; the
mirror of the door for agents that a release ships is left out of the map, counted where the map is shown.

## layers[law].holds

THE KEYS A RELEASE IS SIGNED WITH ARE LAW (25.0). An upgrade runs the release's own tool, its germinate.py and the hooks
it installs, fetched from a network; a tag that moved, an account that was taken, a source that was not the project's,
would each run in every garden that upgrades. So a signed tag is checked against keys the garden already holds, and
they are the ones the release it runs brought, as a package manager's keyring is: which next release a garden trusts is
decided by the release it trusts now, and a key changes only in a release its predecessor signed. What decides whether
code runs is in force, applied alone, and a change to it is a RULE-CHANGE: it is law, beside what a release ships.
Not taken: the keys fetched with the release (the release would vouch for itself); a key named in the tool's code (a
change of key would be a change of code, and the tool is the thing being checked).

## layers[estate].holds

A SERIES' PARTS ARE ESTATE (F12). They are a garden's own facts, in rows too many for a bean, and they belong to the bean
whose series they are: a staged part is journalled as a change to that bean.

## terms[sensitivity]

HARM IS READ FROM WHAT A BEAN HOLDS, NOT FROM WHAT SOMEBODY REMEMBERED TO WRITE. A diagnosis code is special-category
material whether or not anyone marked the bean, so the level is derived each time and never stored: a stored level is
a second copy that goes stale the day a code is added. What a person may add is what no rule can see — a note that
names a condition in its own words — so a mark raises the level. Lowering it is a safety change (Contract E): a tool
that lowered it would be deciding, alone, that a person's record may travel.

REFUSED WHERE A COMMIT ADDS IT, WARNED WHERE IT IS (25.0). A warning came after the harm: the gate warned of a reading
written unsealed, and a writer who committed anyway had put the value in every clone, every bundle and every hub, where
the seal made next took none of it back. A person added without consent was refused from the start for the same
reason. What is already in git is warned, not refused: refusing it would stop every commit of a garden whose history
already holds it, and only a rewrite of every copy takes it out, which is the gardener's decision.

## terms[consent]

ANOTHER PERSON IS NOT THE GARDENER'S TO PUBLISH. A garden's git is copied whole to every clone, and a clone outlives
every promise made about it, so a person who has not agreed to be kept there by name is kept under an opaque id and
their name is held off git. Consent is an agreement they accepted — their own word, the same act the law already
records for a party — and not a flag somebody set on their behalf. Where a person will be is dearer than who they
are, so their future whereabouts are held off git whatever they consented to. What is already in a garden is warned,
never moved: its gardener decides at the crossing.

BETWEEN GARDENS, THE MEETING IS THE WORD. Gardens meet as equals: either may ask and either may offer, so consent cannot
depend on who moved first, nor on a document only the sender makes. Two gardeners read their ids out to each other,
and each records the other's garden and its keeper. That exchange is each one giving their name, and the gardener who
records it decides, as their own act (class F), whether it was really them. Trust sits with whoever receives, so
authenticity is checked there. A certifier above both would be a privilege the network of equals does not have.

## terms[about]

WHOM A RECORD CONCERNS IS NOT WHO OWNS IT. A certificate about a client is the practice's record and the client's
data. Erasure, a person's request to be shown what is kept, and the derived sensitivity all ask the same question,
so it is asked of one term.

## terms[grants]

CLOSED BY DEFAULT, AND DECIDED BY WHOEVER HOLDS THE GRANT. A garden served to more than its gardener needs one answer
to "may this person see this", and an answer each host kept in its own configuration is an answer nobody can read in
the ledger. A grant is held where the decision belongs — the gardener's bean, a person's own bean for her own record,
an agreement's bean for what it shares — and a `forbidden` one is a no that no `permitted` one passes, so a person's
refusal about herself is not undone by a wider grant. Delegating a ratification is the gardener's own act, or the
Contract of Parts would be rewritable by anyone who can write a grant.

WHAT AN AGREEMENT SHARES IS WHAT ITS PARTIES BROUGHT (25.0). An agreement's grant counted over whatever its `over`
selected, so whoever could write one agreement could open any person's bean, or any special-category record, to anyone.
An agreement speaks for the people who accepted it, and for nothing they did not bring: its own bean, and a bean one of
them owns or is the record of. Beyond that its grant opens nothing, and the gate warns rather than refuses, because a
selection grows with the garden and a bean somebody else adds must not stop their commit.

## held_form

GIT KEEPS ONLY WHAT MAY TRAVEL. An entry that cannot is sealed: the bean keeps an opaque pointer, and the entry is kept
in a store that a host names in its `roots`. No hash is kept in git, because a hash of a phone number is the phone
number to anyone who can count to fifteen digits. The gate never reads a store — a gate that passes on one machine
and fails on another is a gate people turn off — so a store is checked where it is, by the save. A sealed entry is
journalled in one line that says only that it was sealed.

## identity_policy.issued

AN EMPLOYEE NUMBER BELONGS TO ITS EMPLOYER. Two employers who each issued 0042 issued two identities, and a garden that
merged them on the number would merge two people. An issued anchor names its issuer; one that does not is warned
rather than refused, because an upgrade cannot invent who issued a number.

## terms[standing]

A GARDEN PLACES WHAT THE LAW DOES NOT. It was a term one garden kept for itself, read by the gate under that name.
Promoted, its values are the rows of the map that hold files, so a new place needs no second list. An entry that
places a file where the law places it says nothing new; one that places it elsewhere would give a file two
places, and is refused. A pattern may stand for many files, because a garden's handovers or a person's letters
are many files of one kind.

## terms[phone]

A NUMBER IS WRITTEN ONE WAY, OR TWO SPELLINGS ARE TWO PEOPLE. `0044 20 …`, `+44 (0)20 …` and `+4420…` are one line, and
a merge that compares text would keep three. E.164 is the form every exchange routes by: `+`, the country code, the
digits, nothing between. The number is logical, as an email address is: it reaches someone, and whether it
establishes who is the bean's to say. A third party's number is personal data about someone who did not write it
here, so it is held off git unless their own consent puts it in.

## terms[pass_log]

A CLAIM NEEDS SOMETHING TO BE CHECKED AGAINST. A session that says what it read and where it wrote it can be held to
that, but only if the record is its own and only grows. The log is a file, one pass to a line, named by the session's
bean, so a commit that changes it claims that session and owes what the flow law asks of a claim. A session that
keeps no log claims nothing and is held to nothing more than any writer, which is why a log is offered and never
required.

## methods

HOW MATERIAL MOVED IS PART OF WHETHER IT MAY. The same words, taken down from a person, are her statement; copied from
another bean, they are a copy, and a copy is not said. A flow row names its method, so the list of methods is closed:
a method nobody declared could carry anything past every row.

## flows

EVERY PASS HAS A ROW, OR IT IS REFUSED. A garden's material comes from places of unequal standing — a person's words, a
tool's output, the law, another garden — and a value placed in the estate carries where it came from. A list of what
is forbidden is never finished, so the rows say what is allowed, source by destination by method, and each says why.
Where two rows hold, the nearer decides, because the particular case is the one someone thought about.

## flow_form

THE FORM OF A ROW IS FIXED, SO THAT THE LAW OF FLOWS CAN BE READ BY A TOOL. A row's guard is computed from where a
tool checks it, never typed, because a typed guard is a claim that is true until the tool changes. A garden may add
refusals and may grant a named party where the standard asks for ratification, but never unguard a row of the
standard: a garden that could loosen the law would loosen it the first time the law was in the way.

## pass_form

A PASS IS RECORDED BY WHERE, NOT WHAT. The record of a pass names its source, its destination and its method, and
never holds the material, since a log of what passed that held the material would be a second copy of it, and
the one least guarded. What a pass carries is found where it landed, and the log only says that it went there.

## pass_metadata

WHAT A PASS MAY SAY OF ITSELF IS COUNTS AND LOCATORS. A hash of a day or an amount does not hide it, and a snippet is
the material. So a pass holds how long its material was, where it sat in the session, the id of the git object that
already holds it (a locator into the repository, not a digest of a value), and how often its value was found in its
source, which is the measure of whether it was quoted or only hoped.

## doc:MANIFESTO.md#serve

THE FIRST OF THE NINE LIVES. In the *Phaedrus* (248d–e) the soul that has seen most is born into the first of nine
lives: «φιλοσόφου ἢ φιλοκάλου ἢ μουσικοῦ τινος καὶ ἐρωτικοῦ», a lover of wisdom, or of beauty, or one of the Muses'
people and of love. The eighth is the sophist or the demagogue (σοφιστικὸς ἢ δημοκοπικός); the ninth, the tyrant
(τυραννικός). The eldest Muses, Calliope and Urania, are told of those who spend their lives in philosophy (259d). The
clause takes its place in the first life and names the two it refuses: the one who sells the appearance of wisdom,
«σοφίας … δόξαν, οὐκ ἀλήθειαν» (275a), and the one who closes what belongs to all.

A NOTEBOOK HOLDS REMINDERS, NOT MEMORY. Theuth offered writing as a drug for memory and wisdom, «μνήμης τε … καὶ σοφίας
φάρμακον» (274e); Thamus answered that it is a drug for reminding, «οὔκουν μνήμης ἀλλὰ ὑπομνήσεως φάρμακον» (275a), and
that a written word, wronged, «τοῦ πατρὸς ἀεὶ δεῖται βοηθοῦ» — always needs its father to help it (275e). daftar's
answer to both is its structure: a record is a reminder, never a memory, and every fact keeps its father beside it,
who said it and how they know (provenance). The wise man will still sow «ἐν γράμμασι κήπους», gardens in letters,
storing reminders «ἑαυτῷ … καὶ παντὶ τῷ ταὐτὸν ἴχνος μετιόντι», for himself and for everyone who follows the same
track (276d). That is daftar's word for its repositories, and the clause `after`.

WHY NOT THE MUSES' SERVANT. «Μουσάων θεράπων» (*Theogony* 100) is Hesiod's title for the bard, whose life the
*Phaedrus* ranks sixth (ποιητικός, 248e), and whose song makes the grieving forget (*Theogony* 55, 102–103). A
ledger's work is the opposite of forgetting.

## doc:MANIFESTO.md#who-where

ONE PERSON, SEVERAL NAMES. A person may carry the name a state registered, the name they have been called by all
their life, and a name they publish under. A rule that admits only the registered one makes the person prove, at every
crossing, that the others are theirs. The cost is paid again at each crossing, by the person and by everyone who must
check, and it falls hardest on whoever crosses most. daftar holds a person as one being with several anchors, each
saying who said it and how they know, so the crossing is made once. daftar's own steward carries three names, and its
charter says which is used where.

## doc:MANIFESTO.md#gain

WHY THE GAIN IS DIVIDED IN THREE. The tools that make daftar's efficiency were paid for three times over: by those who
do the work and those who buy it; by the base, the world's shared knowledge the models learned from and the earth's
resources they run on; and, where a right on the ground is trodden on, by whoever holds that right. So the gain is
divided in three, and the steward's share is none (gain, cost). The text this manifesto was first drawn from gave the
whole difference to those who work and those who buy; the steward's rule divides it in three, and keeps from that text
what matters most, that none of it is his.

A THIRD HELD, NOT A REWARD. The third for a right on the ground is paid toward what an established right is owed, never
on top of it. A published promise of a reward can bind as one, and a bounty for suing is the opposite of prudence. It
is held without end, because a right can be established late.

## doc:MANIFESTO.md#sibling

NO SIBLING, AND NO ESTATE, STANDS ABOVE ANOTHER. The old orders gave privilege by estate — by birth, nation, rank, or
the register one was entered in — and the harm of it is written in every history. A tool that anyone can run, in any
language, on any machine, has no reason to carry that privilege forward, and every reason not to: whatever it
privileges, it multiplies. New tools need an ethics fit for them. So daftar's law names no country, language,
calendar, currency, body, vendor or make of agent as the one the others are measured from, and no release carries a
declaration in the form of one country's law.

## doc:MANIFESTO.md#lawful

EVERY PLACE'S LAW IS A SIBLING. The places on daftar's path differ:
- some protect a work only when it is first published there;
- some ask that a grant of rights be written and signed;
- some hold that a model's output has no author;
- some bar money across their borders.

None is privileged (sibling). daftar is written in the form of none of them, and asks no one to break the law where
they stand. What a place's law asks of a person, the steward answers for what he himself publishes.

## profiles.code.terms[code_paths]

MOVED OUT 2026-08-02 (P1 / D6, human-ratified): `summary_ref` and `last_indexed` left this term and now
live in `analysis_cache`. Rationale (one-owner-of-a-fact): a summary is an ANALYSIS RESULT, not a property
of a filesystem path, and a date is a weaker staleness signal than the source's own git sha. code_paths
now does exactly ONE job — LOCATE the tree and say whether it may be walked. An analysis_cache entry
binds back to the tree it analysed via its `covers_paths`.

**What an agent does.** A reader of this product's code reads the owning bean's `code_paths` to locate the tree, then its `analysis_cache` for a result that stands in for a scan. A tree whose `scan_policy` is `reference-only` (a vendored framework, say) is read by its summary and not walked for context; it is searched only for one named symbol. A tree is analysed again only when the entry that covers it is STALE (its `staleness_key` no longer matches the live source), and that entry is then refreshed.

## profiles.code.terms[git_remote]

**Its canonical form.** verbatim remote string (e.g. host:path or scheme URL); lowercase host only

## profiles.network.terms[links]

The first draft of this term got it wrong twice in one line: it carried `dag: true` over `peer` and `carried_by`, and
the design review caught both before any bean was written — the failure `inverse_of` carries a cardinality to avoid,
met twice more in a single term. The note is long for that reason.

**Why it is acyclic.** NOTHING HERE IS ACYCLIC. `peer` is MUTUAL — a router peers a VPS and the VPS peers the router — so an acyclic check would refuse the very first tunnel recorded honestly: a rule made unsatisfiable by its own subject matter. `carried_by` names another entry on THE SAME bean, so it is not a cross-bean edge and there is no graph to walk; it is documented ordering, and it is deliberately NOT `in: ref`. PROTOCOL carriage is separately and permanently not acyclic — wireguard is carried by udp over ipv4 and then carries ipv4, because that recursion is what encapsulation IS — which is why `rides_on` in the registry is descriptive and joins no check. A rule that cannot be satisfied is worse than no rule: it is the failure `inverse_of` carries a cardinality to avoid.

## terms[owned_by]

**Its forms, written out.**

```
owned_by: { <facet>: { owner: {bean: <person|org>} }, ... }   # introduce facet-owners here
owned_by: { via: {bean: <parent>} }                           # inherit parent's facet-owners
owned_by: { <facet>: { contract: {bean: <contract>} } }       # a SINGLE facet co-owned -> a contract resolves it
owned_by: { <facet>: { external: '<who>' } }                  # owned OUTSIDE this garden (third-party software, a vendor); names the owner in prose because they are not a managed object here
owned_by: { <facet>: { crown: <branch> } }                     # ownership TERMINATES at the axiom; the branch must be the one this bean's nature routes to. A person is pinned to it; an agreement between parties, or a happening between people, may choose it — owned by none of them
```

## terms[responsibility]

**Its forms, written out.**

```
responsibility: { <facet>: { holder: {bean: <person|org>} } }
responsibility: { via: {bean: <parent>} }
responsibility: { <facet>: { contract: {bean: <contract>} } }   # shared duty -> a contract, as with co-ownership
responsibility: { <facet>: { external: '<who>' } }              # answered for outside this garden
responsibility: { <facet>: { self: true } }                      # a being answers for ITSELF (persons). Reflexive, so it is deliberately NOT an edge — a self-edge would be a cycle, and autonomy is not a dependency.
responsibility: { <facet>: { parties: true } }                   # an agreement is answered for by the parties it binds, each for its own clauses. Reflexive like `self`: the parties are named in `parties`, so this draws no edge. Reserved to the gene that name it (an agreement).
```

**Its rules, in words.** - `parity`: every facet with an OWNER must have a HOLDER and vice versa. An ownership claim nothing answers for is a loose end; a duty nobody owns is orphaned.
- Not the same as ownership: they are opposite arcs, not synonyms. A rented VPS is owned by the provider and answered for by whoever runs it; that is the normal case, not an exception.

## terms[instance_of]

**Its form, written out.**

```
instance_of: {bean: <product|codebase>}
```

## terms[lives_in]

**Its form, written out.**

```
lives_in: {bean: <habitat>}   # follow the chain for the full stack
```

## terms[ip]

**The way out, when one address is several beans'.** bean `shared_identifiers:` (floating/VRRP/anycast), or the network the address is on, as the bean's `located_at` in `network-segment` (reused private range)

## terms[id]

**How it is handled.** - `format`: kebab-case; quote if numeric/reserved; genos-prefixed for high-cardinality gene
- `unique`: per (space,base)

## terms[ref]

`graph` was narrowed at 2.0: from acyclicity asserted for a fixed list of sections to acyclicity declared per
relation.

**How it is handled.** - `resolve`: target exists in right space; field present in target owns/attributes/details; shallow (ref-to-ref=warn)
- `graph`: acyclicity is declared PER RELATION via schema.dag — not asserted here for a fixed list of sections

## terms[timing]

**Its keys.** kebab-case moment names. Used so far: start | sync | stop. The key is DELIBERATELY OPEN and the gate is forbidden from enumerating it — a run with four sync points, or a moment nobody has named yet, must never require a rule-change.

## terms[roots]

**Its keys.** kebab-case root names, shared across hosts by AGREEMENT rather than by a registry: a root is a name two machines both choose to use, and centralising the list would re-introduce the one shared document this term exists to avoid.

## terms[os]

**Why the release is not part of the value.** The RELEASE (15.0, 9.7) is deliberately NOT part of this value. A version moves on every upgrade while the OS does not, and putting both in one scalar would make the enum unclosable — a new point release would be a rule-change. The release belongs in `owns.os_release`, beside the date it was read.

## terms[volumes]

SCOPE, STATED BECAUSE IT IS ABOUT TO GROW. This term records the LAYOUT — what exists, what carries
what, and where it is mounted — which is what a rebuild needs to recreate the shape. It does NOT
record contents, keys or passphrases, and it must not: `no secrets` is a founding rule of this
ledger. The operator has asked for beans complete enough to reproduce a machine, and the honest
remaining gap is CONFIGURATION, which is a separate question from layout because config is
SOMEBODY ELSE'S authoritative truth and ground rule 3 forbids mirroring it.

**What it records, and what it never does.** The LAYOUT only — what exists, what carries what, and where it is mounted: what a rebuild needs to recreate the shape. Never contents, keys or passphrases. Configuration is not layout: it is somebody else's authoritative truth, referenced and never mirrored.

## terms[risks]

**Why a risk is not a capability.** A `capabilities` entry at `forbidden` + `possible` IS a latent risk, and the two are deliberately NOT merged: a capability records the STANCE a being takes, a risk records a FAILURE MODE, and the same prohibition can hold on beings with no risk attached. Where one produces the other, the risk entry says so in `evidence` and cites the capability by name. The alternative — deriving risks from capabilities in the gate — was rejected because a derived finding cannot carry a `consequence` that anybody wrote, and the consequence is the part worth having.

## anchor_systems[unix-filesystem]

**Its scope.** UNIX-SHAPED ON PURPOSE, and named so rather than called `host-filesystem`. C:\Users\user\source\repos\tree cannot satisfy this pattern, and bending it in would give one system two formats — the exact reinvention the pattern rule exists to stop. `windows-filesystem` is declared beside it as a SEPARATE system for exactly that reason.

## anchor_systems[physical]

**Why it has no pattern.** a shelf, a room and a building have no canonical form a garden could impose without inventing one. Stating `none` is the honest position: the address is prose, and prose is what a human reads to go and find it.

## operating_systems[routeros]

**Why it has no path grammar.** DELIBERATELY none, and the most interesting row here. RouterOS positions are CONFIG MENU paths — `/ip firewall nat`, `/interface/wireguard/peers` — not filesystem paths, and they resolve in a configuration tree rather than in a directory. `pattern: none` is already an honoured value in `anchor_systems`, declared there for the `physical` system, so refusing to invent a grammar is a shape this law can already express rather than a special case invented for this row.

## terms[identifier]

ONE TERM FOR AN IDENTITY A BEING IS GIVEN (26.0). Until then each genos had a term of its own — thirteen of them —
and every one said the same thing — the logical identity of a <genos>, an id its home assigns
or a name the garden mints once, `<genos>:<name>`. A new genos needed a new term before its first bean could be named,
so the law grew by one word per kind of being, and a name already carried its genos: `person:sam` under a term named for persons
said "person" twice. The catalogue of the language showed the pattern as thirteen siblings of one shape.

What the thirteen told apart is kept, and said where it belongs. That a minted name is the bean's own genos is now
checked, where before a `contract:` name under the persons' term passed. Which forms a genos admits is a column of its row
in `gene` (`identifier_forms`), so the one prose rule that mattered — a person is never identified by a number a state
assigns — is a check: a person's identifier is minted or issued, and one that reads as neither is warned, as an issued
anchor with no issuer always was, because an upgrade can invent no issuer. Whether an identifier ESTABLISHES is the
bean's to say, as it already was for a document's reference and a manifest's name; the natures' minimum of
establishing anchors still stands behind it, so a confirmed person with none is still told.

What stays apart, and why: `garden_id`, `content_hash`, `email`, `phone`, `fqdn`, `hostname`, `mac`, `serial`,
`wg_pubkey` and the two fingerprints each have a value system of their own — a pattern, a canonical form, a registry —
and are read off the thing or its address, never given to it.

**The ids it gathers.** They were made terms at 19.0, when `identity_policy.anchor_key` required every key to be
one: the ids the registry of gene had named in prose since P3 and the first garden had used all along. All logical;
none declares a form, because each is whatever its home assigns or a garden mints once. A module's name leaves
`establishing` to the bean — it corroborates beside the git remote that establishes.

**A happening's.** It has an identity where it is kept — the UID an invitation carries — or one a garden mints once.
Minted, because two gardens recording one dinner will each name it, and the name must be qualified before it crosses.

**An employee number.** No canonical form is declared: an employer-assigned id has whatever shape the employer uses,
and it identifies only with its issuer. A name is never an anchor.

## term_form

ONE SHAPE FOR A TERM (26.0). A term had grown keys that no tool read — a note on its keys, the release left out of a
value, a form written out, a directive to an agent — each named for the occasion. They were prose riding on the law: a
reader could not tell a rule from a remark, and nothing kept the next one from arriving under a new name. The record
is now declared, and the gate holds every term to it, the law's, a profile's and a garden's alike. What a writer needs
to apply a term is its `meaning`; why it is so is reasoning, here, under the term's path.

## registry_forms

EVERY REGISTRY DECLARES ITS COLUMNS (26.0). The catalogue found forty-six siblings shaped unlike their group, and most
were a row carrying a note its siblings lacked, or a column only one row needed. A registry's form says which columns a
row holds and which it may, so a note cannot ride on a row, a fact of a new kind is a column the form is given first,
and a garden's rows are held to the same form as the law's. It took in what `registry_links` said, because a link is
one thing a column says: where its values come from. A form admits what a tool lets a garden write — a system's
`overlay`, a scheme's `labels` — even where no row of the law uses it yet, because a form is for every garden.

## tool_families

THE TOOLS BY WHAT THEY ARE FOR (26.0). Every tool lay flat in one directory, one layer of the law, and a reader met
forty of them in alphabetical order. A family says what a tool is for, in the words of what a person does: read the
law, judge, write, read the garden, measure, deal with another garden, run the loop. The files did not move: every
command a document, a hook or a garden's habit names still runs, and a move would have doubled each file as a shim on
systems without links. The entry groups them instead.

## verbs

ONE ENTRY (26.0). `bin/daftar.py <verb>` runs a tool under the Python that runs the entry, so one command works alike
wherever Python does — on Windows too, where `python3` may be missing or a store alias. The verb is the tool's name
without `dm`, so the row states the family and nothing a file name already says; what the tool does is the first line
of its own help, read from it, never restated.

