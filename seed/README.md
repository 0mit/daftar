# seed — the germination kit

## What a seed is

> A **seed** is the smallest set of artifacts from which a competent cold agent — no history, no estate, no
> conversation — can reconstitute the law in force, reconstitute a gate that enforces it, write a first bean, **commit
> it**, and have that gate **refuse** each class of violating write.

It is the genotype. Beans are phenotype: re-observable by reading an estate whose machines are their real source of
truth, which is why none travel. The journal is the fossil record, and fossils do not germinate.

The seed is the **language**: the core and its rows (`core/law/`), the gate (`core/`), the tools (`bin/`), the
templates and the germination script. It carries no bean, because every bean is someone's and the seed is nobody's.

## Growing a garden

```
python3 seed/germinate.py <target-directory>
```

(`python` on Windows, here and in every command below. Name the directory for the garden — `garden-sam` rather than
`garden` — because its name is the garden's name, which every proposal it makes to another garden shows.)

That copies what `seed/LANGUAGE` declares — the core and its law, the tools and the empty templates; pins the law in
`GARDEN.md` (`extends: core@<version>`); runs `git init`; installs the gate as the pre-commit hook; makes the first
commit; and runs the gate. A garden that cannot make its first commit has not germinated. The first commit is the
garden's identity, its id read from git, and a random seed written into it makes it this garden's alone, however many
gardens are grown with the same name. (`sh seed/germinate.sh` does the same: it chooses a Python as the hook does and
hands over to it.)

**Requires** Python 3 and **PyYAML**, the one third-party dependency.

Then:

1. write `beans/<id>.md`, where `bean: <id>` equals the file's name;
2. save it: `python3 bin/save.py "<who>" "<what you did>" --body "- action: …"` writes the journal entry (its
   heading read from the clock), writes the moment in place of each `at: now`, stages everything and commits. When the
   gate refuses, fix what it names and run `python3 bin/save.py --again`.

## Your first beans

The gardener, the machine they use, its maker, and the journal entry that records them — exactly as a new garden
accepts them. **These blocks are not illustrations:** a suite writes each one into a freshly grown garden and commits
it through the gate, so if the law moves and they stop passing, the suite fails rather than this page quietly lying.

The first person is the **gardener**: the one who keeps this garden, and ratifies there the decisions an agent may only
propose (manifesto: parts).
Every fact is a statement — a verb and its roles — and the first statement of every bean says who knows the rest:
here, Sam says it. A person is owned by the crown, `theone`, whom no bean names: nobody holds a person. A person
answers for themselves before the law.

<!-- example: beans/sam.md -->
```markdown
---
bean: sam
kind: person
title: "Sam — keeps this garden"
summary: "The gardener: the person who keeps this garden, and owns and answers for the machines recorded here."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Sam keeps this ledger.
```

The words are the core's:

- `kind` — the sort of being a bean records, a row of `core/law/kinds.yaml`. A `person` is a body: it takes room in
  space∞time, an organism at reason. A `contract`, a `domain`, a program are sayables, placed in an order.
- `say`, `own`, `answer` — verbs. `by`, `of`, `as`, `at` — four of the seven roles every verb draws on.
- `self` — the being this bean records. `now` — the moment of the save, which the save writes in its place.

A machine is owned by someone, and someone answers for keeping it — here the same person. Its owner answers for it
before the law, and that is derived, so it is not written. It came to be through the hands of someone at its maker,
unknown by name. Sam **read** what is written of it off the machine itself. Its identity is the serial its maker gave
it, once and to this machine alone; its hostname is only the name Sam gave it, and moves between machines:

<!-- example: beans/laptop.md -->
```markdown
---
bean: laptop
kind: host
title: "laptop — Sam's ThinkPad"
summary: "Sam's daily laptop."
statements:
  - read:   { by: sam, at: now }
  - name:   { by: lenovo, of: self, as: "PF-12345" }
  - name:   { by: sam, of: self, as: laptop }
  - own:    { by: sam, of: self }
  - answer: { by: sam, of: self, as: keeping }
  - come:   { by: self, through: [ { someone: person, at: lenovo } ] }
---
The laptop.
```

<!-- example: beans/lenovo.md -->
```markdown
---
bean: lenovo
kind: org
title: "Lenovo — the maker of Sam's laptop"
summary: "The company that made the laptop, and gives its machines their serial numbers."
statements:
  - say: { by: sam, at: now }
---
The laptop's maker.
```

A serial is a name its maker gives once, so the maker is a **namespace**: a row of the garden's `VOCAB.md`. (The
standards' namespaces — `dns`, `mail`, `e164`, `ieee-eui48` and the rest — are the core's already.)

<!-- example-front-matter: VOCAB.md -->
```yaml
namespaces:
  - { namespace: lenovo, once: "true", meaning: "the serial numbers Lenovo gives the machines it makes" }
```

The gardener is named in `GARDEN.md`, the garden's manifest. Set the one line the template leaves empty:

<!-- example-front-matter: GARDEN.md -->
```yaml
gardener: sam
```

And the save that goes with them. `GARDEN.md` and `VOCAB.md` are law, so the entry says RULE-CHANGE. Give the tool who
you are and one line saying what changed, and only the body of the entry, with no `##` line: it writes the heading,
reading the clock.

<!-- example: log/journal.md -->
```sh
python3 bin/save.py "sam" "the first beans" --body "- action: added [[sam]], [[laptop]] and [[lenovo]]; RULE-CHANGE: GARDEN.md names sam as the gardener, and VOCAB.md adds the namespace of Lenovo's serials.
- detail: the serial is off the underside of the machine.
- why: starting the ledger with the person who keeps it, so nothing dangles."
```

The line breaks inside the quotes are kept, in a Unix shell and in PowerShell alike, and the journal then holds
`## 2026-09-17 09:30+03:00 · sam · the first beans` — the moment it was run — above those lines. The same run writes
that moment in place of each `at: now`: the moment a fact was written down is the clock's, and never typed. A body kept
in a file can come on standard input instead (`… "the first beans" < entry.md`) in a shell that has `<`; PowerShell has
not.

The `[[bean-id]]` is what makes the entry count: the gate refuses a bean the commit changes that the entry does not
name, and a change to the law whose entry does not say RULE-CHANGE. `- action:` is the only required line; `detail`
and `why` are for the reader you cannot answer questions for, which in a year is you. When the gate refuses something,
its message says what to write; `MODEL.md` is the model, and `CHECKLIST.md` says how a write is made. `COOKBOOK.md`
goes on from here, and `FORMS.md` holds what an agent writes most.

## Contents

| file | what it is |
|---|---|
| `core/law/` | the law: the core's face (`core.yaml`), the verbs' rows, the kinds, levels, layers, units, namespaces and the standards' tables |
| `core/` | the gate (`check.py`), the engine it runs, and the hook |
| `knowledge/` | the standards' own tables and our knowledge tree, each under its own licence |
| `VOCAB.md.template` | the garden's own rows, empty |
| `GARDEN.md.template` | the manifest: which garden this is, whose it is, which law governs it |
| `journal.md.template` | the header and **zero entries**, so no knowing is falsified |
| `pending.md.template` | the park-and-proceed queue: its header and **zero entries** |
| `germinate.py` | the procedure above (`germinate.sh` hands over to it) |
| `RELEASE-SIGNERS` | the keys a release tag is signed with: `bin/dmupgrade.py` checks the next release against the garden's copy before any of it runs |
| `COOKBOOK.md` | the common things, written the way the gate accepts them, the gardener first |
| `FORMS.md` | what an agent reads before writing, and what to write when nobody said |
| `WELCOME.md` | the door for an assistant with no shell |
| `RATIONALE.md` | why each rule is as it is, keyed by the rule's path |

Germination also copies **`.gitattributes`**: it sends a bean's merge to the statement merge (`MERGE.md`), and the
journal's and the queue's to the same driver, entry by entry. A garden without it merges its beans line by line and
conflicts on its own append-only log. `.gitignore` travels with it, so no bytecode reaches a new garden's first commit.

**There is no copy of the tools here.** `germinate.py` copies them from the clone, by the patterns in `seed/LANGUAGE`:
a vendored copy would be a second toolchain that can drift from the one under test.

## What is deliberately not carried

Counts, rosters, an enum fossil, an incident ledger, a rejected-ideas register. Each is either derivable — a glob, the
law's own tables, a test runner — or already owned by a document that travels. The governing rule, learned from
measuring rather than from taste: **every field a seed carries must sit in a position some tool enforces or
resolves.** Positions the tools check stayed true; positions nothing checks rotted, whichever file they were in. A
seed field with no enforcing schema is worse than none, because it is a second copy that also claims authority.
