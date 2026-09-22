# seed — the germination kit

## What a seed is

> A **seed** is the smallest set of artifacts from which a competent cold agent — no history, no estate,
> no conversation — can reconstitute the law in force, reconstitute a gate that enforces it, write a first
> bean, **commit it**, and have that gate **refuse** each class of violating write.

It is the genotype. Beans are phenotype: re-observable by scanning an estate whose machines are their real
source of truth, which is why none travel. The journal is the fossil record, and fossils do not germinate.

Two artifacts do two different jobs and neither can do both:

| | `seed/` | a garden's own product bean (optional) |
|---|---|---|
| is | the germination kit — the **language** | this garden's bean **for** the product |
| contains | the law, templates, and the germination script | only underivable ratified facts and gate-resolved pointers |
| copied into a new garden | yes, wholly | **never** |
| checked by | `test/germinate.py`, positively **and** negatively, in a real git repo | `bin/dmcheck.py` on every commit |
| carries an owner | no | yes — both arcs |

A seed *bean* cannot be what you copy: `owned_by` and `responsibility` are required on every bean,
and the crown form is reserved to `kind: person`, so the bean necessarily carries an edge to a person in
*this* estate. A prose `SEED.md` cannot be it either: `seed/` sits outside the gate's glob, so nothing
would check it, and unchecked prose is precisely what rotted everywhere else in this repo.

**`seed/` here is not the *seed* of MERGE.md.** There the word means the merge product — the **canonical bean**,
the most-inclusive bean, the superset of every garden's record of one object — and `bin/dmmerge.py` uses it the
same way. Two senses of one word in one repository is a trap; both documents say which they mean.

## Growing a garden

```
sh seed/germinate.sh <target-directory>
```

That copies the daftar tools from this clone's `bin/`, the Tier-0 vocabulary, and four empty templates; interpolates the
version pin **from the vocabulary's own `version:` key** rather than typing it; `git init`s; installs the
hooks; makes the first commit; and runs the gate. A garden that cannot make its first commit has not
germinated, so the commit is part of the test rather than a step left to the reader.

**Requires** Python 3 and **PyYAML** — the one third-party dependency. `bin/dmcheck.py` exits 2 without it.

Then:

1. write `beans/<id>.md`, where `bean: <id>` equals the filename
2. append what you did to `log/journal.md` — the gate **refuses** a bean staged without it
3. `git add -A && git commit`

`python3 bin/dmrules.py` prints every rule in force, derived from the vocabulary rather than restated.

## Your first beans

A person, the machine they run, and the journal entry that records both — exactly as a new garden accepts
them. **These blocks are not illustrations:** `test/germinate.py` writes each one into a freshly grown
garden and commits, so if the law moves and they stop passing, the test fails rather than this page
quietly lying. The journal entry is checked the same way, because the first commit is refused far more
often for the entry than for the bean.

A person is owned by the crown and answers for themselves. Nobody holds a person, so these two lines are
the only way a person's ownership is written:

<!-- example: beans/sam.md -->
```markdown
---
bean: sam
kind: person
title: "Sam — keeps this garden"
status: active
summary: "The person who owns and answers for the machines recorded here."
nature: living
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "person:sam", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { crown: love } }
responsibility: { legal: { self: true } }
---
Sam keeps this ledger.
```

A machine is owned by someone and answered for by someone — here the same person, on both facets. Its
identity is a HARDWARE anchor (a serial or a MAC), because a hostname moves between machines:

<!-- example: beans/laptop.md -->
```markdown
---
bean: laptop
kind: host
title: "laptop — Sam's ThinkPad"
status: active
summary: "Sam's daily laptop."
nature: physical
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "PF-12345", class: hardware, establishing: true }
    - { key: hostname, value: "laptop", class: network, establishing: false }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: {owner: {bean: sam}}, technical: {owner: {bean: sam}} }
responsibility: { legal: {holder: {bean: sam}}, technical: {holder: {bean: sam}} }
---
The laptop.
```

And the entry that goes with them. **This is the step a first commit fails on**, because a heading is a
POSITION IN TIME and the gate checks the form — so read it from the clock rather than typing a date:

<!-- example: log/journal.md -->
```markdown
## 2026-09-17 09:30+03:00 · sam · the first two beans
- action: added [[sam]] and [[laptop]].
- detail: the serial is off the underside of the machine; the person id is a name I chose and can keep.
- why: starting the ledger with the thing that owns everything else, so nothing dangles.
```

```sh
python3 bin/dmjournal.py "sam" "the first two beans" < entry.md     # writes the heading from the clock, appends the body
```

The `[[bean-id]]` is what makes the entry count: the gate refuses a staged bean that the entry does not
name. `- action:` is the only required line; `detail` and `why` are for the reader you cannot answer
questions for, which in a year is you. When the gate refuses something, its message says what to write;
`MODEL.md` says why, and `CHECKLIST.md` says how a write is made.

## Contents

| file | what it is |
|---|---|
| `std-vocab.md` | the Tier-0 law. The **only** document the gate reads as law directly |
| `VOCAB.md.template` | the garden's local overlay, empty, with the pin interpolated |
| `GARDEN.md.template` | the manifest: which garden this is, which version governs |
| `journal.md.template` | the header and **zero entries**, so no provenance is falsified |
| `pending.md.template` | the park-and-proceed queue: its header and **zero entries** |
| `germinate.sh` | the procedure above |

Germination also copies **`.gitattributes`** from the clone. It is part of the language rather than of any
estate: it is what dispatches bean merges to `bin/dmmerge.py` and gives `log/journal.md` a union merge.
A garden without it text-merges its beans line by line and conflicts on its own append-only log.

**There is no copy of `bin/` here.** `germinate.sh` copies the toolchain from the clone at germination
time. A vendored copy would be a second toolchain that can drift from the one under test, and hand-listing
which modules to carry gets it wrong — `dmcheck.py` imports `dmsafe`, which is not obvious from reading it.
It carries every `bin/dm*.py`, `bin/hooks/` and `bin/install.sh` — by that naming convention, not by a list
— and nothing else under `bin/`: a garden may keep its own tools there, and they are its own. `.gitignore` travels with `.gitattributes`, so no bytecode reaches a new garden's first commit.

## What is deliberately not carried

Counts, rosters, an enum fossil, an incident ledger, a rejected-ideas register. (`MODEL.md`, `CHECKLIST.md`,
`MERGE.md` and the daftar skill DO travel since 2026-09-17: a garden grown without them had the law's data
and no statement of what it meant.) Each is either derivable — a glob, `dmrules.py`, a test runner — or already owned by a document
that travels. The governing rule, learned from measuring this repo rather than from taste: **every field a
seed carries must sit in a position some tool enforces or resolves.** Positions the tools check stayed
true here; positions nothing checks rotted, regardless of which file they were in. A seed field with no
enforcing schema is worse than none, because it is a second copy that also claims authority.
