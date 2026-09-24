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
and the crown form is reserved to persons, agreements and happenings (`person`, `contract`, `event`), so the
bean necessarily carries an edge to a person in *this* estate. A prose `SEED.md` cannot be it either: `seed/` sits outside the gate's glob, so nothing
would check it, and unchecked prose is precisely what rotted everywhere else in this repo.

**`seed/` here is not the *seed* of MERGE.md.** There the word means the merge product — the **canonical bean**,
the most-inclusive bean, the superset of every garden's record of one object — and `bin/dmmerge.py` uses it the
same way. Two senses of one word in one repository is a trap; both documents say which they mean.

## Growing a garden

```
python3 seed/germinate.py <target-directory>
```

(`python` on Windows, here and in every command below. Name the directory for the garden — `garden-sam` rather
than `garden` — because its name is the garden's name, which every proposal it makes to another garden shows.)

That copies what `seed/LANGUAGE` declares — the daftar tools, the Tier-0 vocabulary, and the empty templates;
interpolates the version pin **from the vocabulary's own `version:` key** rather than typing it; `git init`s;
installs the hooks; makes the first commit; and runs the gate. A garden that cannot make its first commit has not
germinated, so the commit is part of the test rather than a step left to the reader. The first commit is the
garden's identity (`garden_id`), and a random seed written into it makes it this garden's alone, however many
gardens are grown with the same name. (`sh seed/germinate.sh` does the same: it chooses a Python as the hooks
do — the first that runs and imports yaml — and hands over to it.)

A garden is kept by someone, and the gardener is the first bean you write (below). `--gardener sam
--gardener-name "Sam"` writes it for you instead: a second commit plants the bean — its name qualified at birth by
the garden's id, `<garden id>/person:sam` — and names it in `GARDEN.md`, so the garden begins as someone's. Then the
first commit below is the laptop alone. An organisation that keeps a garden is planted with `--gardener-genos org`.

**Requires** Python 3 and **PyYAML** — the one third-party dependency. `bin/dmcheck.py` exits 2 without it.

Then:

1. write `beans/<id>.md`, where `bean: <id>` equals the filename
2. append what you did to `log/journal.md` with `bin/dmjournal.py` — the gate **refuses** a bean staged without it
3. `git add -A`, then `git commit` — two commands, because Windows PowerShell 5.1 cannot run `&&`

`python3 bin/dmsave.py "<who>" "<what you did>" --body "- action: …"` does 2 and 3 in one command, and when the gate
refuses, says what to run after the fix.

`python3 bin/dmrules.py` prints every rule in force, derived from the vocabulary rather than restated.

## Your first beans

The gardener, the machine they run, and the journal entry that records both — exactly as a new garden accepts
them. **These blocks are not illustrations:** `test/germinate.py` writes each one into a freshly grown
garden and commits, so if the law moves and they stop passing, the test fails rather than this page
quietly lying. The journal entry is checked the same way, because the first commit is refused far more
often for the entry than for the bean.

The first person is the **gardener**: the one who keeps this garden, and ratifies in it what an agent may not
decide. A person is owned by the crown and answers for themselves. Nobody holds a person, so these two lines are
the only way a person's ownership is written. (`germinate.py --gardener sam` writes a bean like this one for you,
its name qualified by the garden's id; written by hand, as here, the name is bare until `bin/dmpropose.py mint`
qualifies it, which it needs before it crosses to another garden — `COOKBOOK.md` shows how.)

<!-- example: beans/sam.md -->
```markdown
---
bean: sam
genos: person
title: "Sam — keeps this garden"
status: active
summary: "The gardener: the person who keeps this garden, and owns and answers for the machines recorded here."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "person:sam", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
---
Sam keeps this ledger.
```

Three of its words are the law's, in Greek, each with its siblings:

- `genos` (γένος, kind) — the sort of being a bean records, here a `person`: a row of the law's `gene` (γένη, the
  kinds). It refines the bean's `nature`.
- `empsychon` (ἔμψυχον, the ensouled) — a nature: a person, or a running instance, while alive. The other two are
  `soma` (σῶμα, a body — a machine, a site) and `lekton` (λεκτόν, the sayable — what exists by being said and agreed:
  code, a domain, a contract).
- `agape` (ἀγάπη, love that does not possess) — the crown's branch for what is empsychon. The crown is where every
  chain of ownership ends: its root is `theos` (θεός, god), which no bean names, and its other branches are `physis`
  (φύσις, nature) for soma and `logos` (λόγος, word) for lekton. No being holds a person; only agape does, and only
  while they live.

A machine is owned by someone and answered for by someone — here the same person, on both facets. It is `soma`,
and its identity is a HARDWARE anchor (a serial or a MAC), because a hostname moves between machines:

<!-- example: beans/laptop.md -->
```markdown
---
bean: laptop
genos: host
title: "laptop — Sam's ThinkPad"
status: active
summary: "Sam's daily laptop."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "PF-12345", class: hardware, establishing: true }
    - { key: hostname, value: "laptop", class: network, establishing: false }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: {owner: {bean: sam}}, technical: {owner: {bean: sam}} }
responsibility: { legal: {holder: {bean: sam}}, technical: {holder: {bean: sam}} }
---
The laptop.
```

The gardener is named in `GARDEN.md`, the garden's manifest, and the gate asks for it as soon as the garden
holds a bean. Set the one line the template leaves empty:

<!-- example-front-matter: GARDEN.md -->
```yaml
gardener: sam
```

And the entry that goes with them. **This is the step a first commit fails on**, for its heading: a POSITION IN
TIME, which the gate refuses unless `bin/dmjournal.py` wrote it, reading the clock. So write only the body — no
`##` line — and give the tool who you are and one line saying what changed; it writes the heading above the body
and appends both. `GARDEN.md` is law, so an entry that changes it says RULE-CHANGE:

<!-- example: log/journal.md -->
```sh
python3 bin/dmjournal.py "sam" "the first two beans" --body "- action: added [[sam]] and [[laptop]]; RULE-CHANGE: GARDEN.md names sam as the gardener.
- detail: the serial is off the underside of the machine; the person id is a name I chose and can keep.
- why: starting the ledger with the thing that owns everything else, so nothing dangles."
```

The line breaks inside the quotes are kept, in a Unix shell and in PowerShell alike, and the journal then holds
`## 2026-09-17 09:30+03:00 · sam · the first two beans` — the moment it was run — above those three lines. The same
run writes that day in place of each bean's `as_of: now`, so the beans are written before their entry: the day a fact
was written down is the clock's, and never typed. A body kept in a file can come on standard input instead
(`… "the first two beans" < entry.md`, the file holding the three lines and no heading) in a shell that has `<`;
PowerShell has not.

The `[[bean-id]]` is what makes the entry count: the gate refuses a staged bean that the entry does not
name, and a staged `GARDEN.md` whose entry does not say RULE-CHANGE. `- action:` is the only required line;
`detail` and `why` are for the reader you cannot answer questions for, which in a year is you. (If `--gardener`
planted the gardener already, the first commit is the laptop alone, and its entry names only `[[laptop]]`.) When
the gate refuses something, its message says what to write, and `python3 bin/dmwhy.py <name>` says why; `MODEL.md`
is the model, and `CHECKLIST.md` says how a write is made. `COOKBOOK.md` goes on from here.

## Contents

| file | what it is |
|---|---|
| `std-vocab.md` | the Tier-0 law. The **only** document the gate reads as law directly |
| `VOCAB.md.template` | the garden's local overlay, empty, with the pin interpolated |
| `GARDEN.md.template` | the manifest: which garden this is, whose it is, which version governs |
| `journal.md.template` | the header and **zero entries**, so no provenance is falsified |
| `pending.md.template` | the park-and-proceed queue: its header and **zero entries** |
| `germinate.py` | the procedure above (`germinate.sh` hands over to it) |
| `COOKBOOK.md` | the common things, written the way the gate accepts them, the gardener first |
| `FORMS.md` | what an agent reads before writing: six of the cookbook's recipes, byte for byte, and what to write when nobody said |
| `WELCOME.md` | the door for an assistant with no shell |
| `RATIONALE.md` | why each rule of `std-vocab.md` is as it is, keyed by the rule's path |

Germination also copies **`.gitattributes`** from the clone. It is part of the language rather than of any
estate: it is what dispatches bean merges to `bin/dmmerge.py` and gives `log/journal.md` a union merge.
A garden without it text-merges its beans line by line and conflicts on its own append-only log.

**There is no copy of `bin/` here.** `germinate.py` copies the toolchain from the clone at germination
time. A vendored copy would be a second toolchain that can drift from the one under test, and hand-listing
which modules to carry gets it wrong — `dmcheck.py` imports `dmsafe`, which is not obvious from reading it.
It carries every `bin/dm*.py`, `bin/hooks/` and the installers — by the patterns in `seed/LANGUAGE`, not by a
list of files — and nothing else under `bin/`: a garden may keep its own tools there, and they are its own. `.gitignore` travels with `.gitattributes`, so no bytecode reaches a new garden's first commit.

## What is deliberately not carried

Counts, rosters, an enum fossil, an incident ledger, a rejected-ideas register. (`MODEL.md`, `CHECKLIST.md`,
`MERGE.md` and the daftar skill DO travel since 2026-09-17: a garden grown without them had the law's data
and no statement of what it meant.) Each is either derivable — a glob, `dmrules.py`, a test runner — or already owned by a document
that travels. The governing rule, learned from measuring this repo rather than from taste: **every field a
seed carries must sit in a position some tool enforces or resolves.** Positions the tools check stayed
true here; positions nothing checks rotted, regardless of which file they were in. A seed field with no
enforcing schema is worse than none, because it is a second copy that also claims authority.
