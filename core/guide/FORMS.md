# Forms — what an agent writes most, the way the gate accepts it

Read this page before writing in a garden. It holds six of `COOKBOOK.md`'s recipes as forms, after the misreadings
agents make most, and then the forms for **what nobody said**. Every bean here passes the gate as written: a suite
commits each one into a freshly grown garden. Shapes it does not hold are in the cookbook.

Write what you were told, in these shapes, and copy no value from here: `sam`, `ali`, `XTS`, `123456789abc` and the
amounts below are the example's, and so is the dinner's time. Every fact is a statement, one line, `- <verb>: { <role>:
<filler>, … }`, and every bean's first statement says who knows the rest: `say` (someone said it), `read` (a body read
it), `derive` (it was worked out from other statements) or `make` (it was made here). Its `at` is `now`, and the save
writes the moment in its place. Beans that name each other are committed together. A bean is saved with its journal
entry in one command, which writes the entry (its heading read from the clock), stages everything and commits:

```sh
python3 bin/save.py "<who>" "<what you did>" --body "- action: added [[<id>]]."
```

`log/journal.md` is never edited by hand. When the gate refuses, its message says what to write: fix it, then run
`python3 bin/save.py --again`. For a question this page does not answer, `AGENTS.md` says where the law is. Every
command here is written `python3`; on Windows it is `python`.

## Common misreadings

What agents got wrong most often in measured runs — each a value nobody said, invented:

- **Today is not the day it happened.** A statement's `at` is the day it happened, and nobody's guess: left out where
  nobody said it, `unknown` where its verb requires one. The knowing act's `at: now` is when it was written down,
  never when it happened, and a date in another bean is that bean's.
- **A payment's amount is the whole that moved.** `bear` shares divide it: 90 paid by one and borne two parts to one is
  `of: { count: "90.00", … }` with shares 2 and 1 — never the 30 that one of them owes.
- **A currency is named by its code, looked up, not guessed** (*A currency*, at the end). When no row or more than one
  fits, ask — or leave the payment out and say in its bean's body what is missing.
- **Everyone named is a person bean**, also someone only spoken about. One who is not the gardener is kept by name only
  on their own word: their `agree` to an agreement this garden holds — a consent to be kept here by name is one — or
  the garden they keep, met here. Without it, they are an opaque id, their name held off git (`python3 bin/held.py
  person`), and the gate refuses them by name. A meeting in which something was agreed is itself an event.
- **How something was paid is written only as said** — a card, cash, a transfer, and whose — in the payment's
  `through`.
- **An agent's own act is its session's.** What you were told is said by whoever told you: `say: { by: sam, at: now }`.
  What you found out yourself is `derive`d by your session's bean, never `say` by a person.
- **Everything is between the two `---` lines.** Below them is prose the gate cannot see.

## The gardener, first

A garden is kept by its **gardener**.

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

## Another person, and the garden she keeps

Ali keeps a garden of her own. It is named by its id, which Ali read out from it: the namespace `garden-id` gives it.

<!-- example: beans/garden-ali.md -->
```markdown
---
bean: garden-ali
kind: garden
title: "garden-ali — the garden Ali keeps"
summary: "Ali's own daftar garden. She keeps it; what passes between it and this one is proposed, never written."
statements:
  - say:  { by: sam, at: now }
  - name: { by: garden-id, of: self, as: "123456789abc" }
  - own:  { by: ali, of: self }
---
Ali's garden. Its id is what `python3 bin/propose.py id` printed there.
```

Ali agreed to be kept here by name. Her yes is her `agree`; Sam reports it, so Sam's act knows it.

<!-- example: beans/ali-consent.md -->
```markdown
---
bean: ali-consent
kind: contract
title: "Ali's consent"
summary: "Ali agreed to be kept here by name."
statements:
  - say:     { by: sam, at: now }
  - own:     { by: theone, of: self }
  - answer:  { by: sam, of: self, as: law }
  - answer:  { by: ali, of: self, as: law }
  - agree:   { id: consent, by: [sam, ali], of: "Ali is kept in Sam's garden by name", through: spoken }
  - concern: { of: [ali] }
---
Agreed on the phone. Where she will be is never written here.
```

Her name here is the one her own garden gave her, qualified by its id so that it crosses: the namespace `garden` gives
it.

<!-- example: beans/ali.md -->
```markdown
---
bean: ali
kind: person
title: "Ali"
summary: "Ali, who keeps a garden of her own; Sam shares costs with her."
statements:
  - say:    { by: sam, at: now }
  - name:   { by: garden, of: self, as: "123456789abc/person:ali" }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Ali keeps garden-ali.
```

## A happening: an event

A dinner, a meeting, a call in which something was agreed is an `event`. It `be`s at its time; those present `attend`
it; whoever hosted it answers for it.

<!-- example: beans/dinner-at-sams.md -->
```markdown
---
bean: dinner-at-sams
kind: event
title: "dinner-at-sams — dinner at Sam's, where the washing-machine loan was agreed"
summary: "Ali came to dinner at Sam's; they agreed the loan for her washing machine."
statements:
  - say:    { by: sam, at: now }
  - be:     { by: self, at: "2026-09-12 19:30+03:00" }   # at: the example's — write the moment someone said
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - attend: { by: sam, of: self }
  - attend: { by: ali, of: self }
---
Dinner at Sam's.
```

## Money between two people

Sam and Ali bought a camera together. Ali paid the whole; they bear it two parts to one.

<!-- example: beans/shared-camera.md -->
```markdown
---
bean: shared-camera
kind: contract
title: "shared-camera — Sam and Ali bought a camera together"
summary: "Sam and Ali share a camera; Ali paid for it, and they bear its cost two to one."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - answer: { by: ali, of: self, as: law }
  - agree:  { id: agreed, by: [sam, ali], of: "a camera the two of them use", through: spoken }
  - pay:    { id: camera, by: ali, of: { count: "90.00", unit: XTS }, through: agreed, note: "the camera, bought online" }
  - bear:   { by: sam, of: camera, share: "2" }
  - bear:   { by: ali, of: camera, share: "1" }
---
Sam uses the camera more, so Sam bears two parts of its cost and Ali one.
```

## An agreement paid in instalments

Sam lent Ali the price of a washing machine, to be repaid in six monthly instalments, with interest on one paid late.
Each clause is a statement on the permission square, `obligatory` of the payment it asks, `through` the agreement. What
it holds beside its words — when it falls due, how it repeats, what brings it into force — is its form, `clause`
(core/law/measures.yaml), and rule `measured` judges it.

<!-- example: beans/washer-loan.md -->
```markdown
---
bean: washer-loan
kind: contract
title: "washer-loan — Sam lent Ali the price of a washing machine, repaid monthly"
summary: "Sam paid for Ali's washing machine; Ali repays it in six monthly instalments, with interest on one paid late."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - answer:     { by: ali, of: self, as: law }
  - agree:      { by: sam, of: "the price of Ali's washing machine", through: dinner-at-sams, as: lender }
  - agree:      { by: ali, of: "the price of Ali's washing machine", through: dinner-at-sams, as: borrower }
  - pay:        { id: instalment, by: ali, to: sam, of: { count: "20.00", unit: XTS } }
  - obligatory: { id: instalments, of: instalment, through: self, note: "Ali repays 20 XTS on the first day of each month, six times", clause: { every: { of: time, in: gregorian-civil, each: month, at: "1", times: "6" } } }
  - pay:        { id: interest, by: ali, to: sam, of: { count: "1", unit: "%" } }
  - obligatory: { id: late-interest, of: interest, through: self, note: "an instalment paid after its day carries one percent of itself for each month it is late", clause: { when: { said: "an instalment is paid late" } } }
  - pay:        { id: the-loan, by: sam, of: { count: "120.00", unit: XTS }, note: "Sam paid the shop for Ali's washing machine" }
  - bear:       { by: ali, of: the-loan, share: "1" }
---
Agreed in words spoken over dinner; nothing was written down.
```

## Proposing to another garden

Ali's garden is recorded here, and hers records Sam's (above). A name that is to cross is qualified first:

```sh
python3 bin/propose.py mint shared-camera     # prints the qualified name and how to write it
python3 bin/propose.py mint sam               # the gardener, whom every agreement names
```

then the proposal is made, under an agreement both gardeners `agree` to:

```sh
python3 bin/propose.py make --to garden-ali --under shared-camera shared-camera
```

and in Ali's garden read and taken:

```sh
python3 bin/propose.py read ../PROPOSAL-<garden>-<when>.md    # writes nothing
python3 bin/propose.py take ../PROPOSAL-<garden>-<when>.md    # writes in the working tree; commits nothing
```

What Sam's garden knew crosses as it was known: each act it brings keeps the moment it was known at there and holds, in
its `at`, the bean Ali's garden records Sam's by — `say: { by: sam, at: [2026-09-23T10:05+03:00, garden-sam] }`. Each
bean taken holds `take: { by: ali, of: self, from: garden-sam, through: <the fingerprint>, at: now }`, and Ali's save —
the command `take` prints, its entry naming what was taken — stamps it and commits: the ratification.

Taking is not accepting. In her garden, Ali's own yes to the agreement is her own word on it — one more knowing act,
hers, over the statement that says they agreed:

<!-- example-statements: beans/shared-camera.md -->
```yaml
  - say:    { by: ali, of: [agreed], at: now }
```

## What nobody said

A fact nobody said is never made up. A role its verb requires that nobody said is `unknown`; one it does not require is
left out; and the statement's `note` says what is not yet known. Each form below passes the gate as written, beside the
forms above.

### An event whose day nobody said

An event `be`s at its time. When nobody said its day, place it by what it came after or before — `"after:<bean>"`,
`"before:<bean>"` — and say in `note` what is known of when:

<!-- unsaid: beans/call-with-ali.md, for be -->
```markdown
---
bean: call-with-ali
kind: event
title: "call-with-ali — Sam called Ali about the phone, some day after the dinner"
summary: "Sam and Ali spoke on the phone after the dinner at Sam's and agreed a loan for her phone; nobody said the day."
statements:
  - say:    { by: sam, at: now }
  - be:     { by: self, at: "after:dinner-at-sams", note: "after the dinner at Sam's; its day was not said" }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - attend: { by: sam, of: self }
  - attend: { by: ali, of: self }
---
Sam called Ali some day after the dinner; nobody said which.
```

### A day nobody said

A day nobody said is left out of its statement, as the agreements above show: the camera's payment has no `at`. A
party's yes is its `agree`, with or without a day; a party with no `agree` has no acceptance on record, and no consent.
One who said yes on a day nobody said did agree: write the `agree`, placed by what it came after where that is known,
as in the loan below.

### An amount nobody said

A payment's amount is required, so while nobody has said it, it is `unknown`, and its note says how it will be known.
Over that call, Sam lent Ali the price of a phone and of its case, repaid monthly, one in six instalments and one in
four; nobody said the prices, which is which, or from which day:

<!-- unsaid: beans/phone-loan.md, for pay, agree -->
```markdown
---
bean: phone-loan
kind: contract
title: "phone-loan — Sam lent Ali the price of a phone and its case, repaid in six instalments and in four"
summary: "Sam paid for Ali's phone and its case; she repays one in six monthly instalments, one in four. The prices, which is which and the day were not said."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - answer:     { by: ali, of: self, as: law }
  - agree:      { by: sam, of: ["the price of Ali's phone", "the price of its case"], through: call-with-ali, as: lender, at: "after:dinner-at-sams" }
  - agree:      { by: ali, of: ["the price of Ali's phone", "the price of its case"], through: call-with-ali, as: borrower, at: "after:dinner-at-sams", note: "on the call" }
  - pay:        { id: six, by: ali, to: sam, of: unknown, note: "not yet said: what the phone and its case cost, and which is repaid in six instalments and which in four" }
  - obligatory: { id: in-six, of: six, through: self, note: "Ali repays one of the two in six monthly instalments; how much, and from when, is not yet said" }
  - pay:        { id: four, by: ali, to: sam, of: unknown, note: "nor from which day" }
  - obligatory: { id: in-four, of: four, through: self, note: "and the other in four" }
details:
  in-six: { every: { of: time, in: gregorian-civil, each: month, times: "6" } }
  in-four: { every: { of: time, in: gregorian-civil, each: month, times: "4" } }
---
Agreed on the phone; nothing was written down, and the prices are still to be said.
```

When someone says the prices, each `unknown` gives way to the amount, and the note goes.

### A question still open

What a bean has not answered is its `unknown`s and the roles it leaves out, each statement's `note` saying what is
missing, and its body saying so in prose. A key of your own is refused: the gate takes only the header, the
statements, and `details` for what fits no verb yet. A question that needs a person's decision goes to the queue,
`log/pending.md`.

### A currency

An amount's `unit` is its currency's code. Find it by the currency's name in English, in the table the gate reads:

```sh
grep -i "<its name in English>" seed/knowledge/currencies.tsv
```

(In PowerShell: `Select-String "<its name in English>" seed\knowledge\currencies.tsv`.) Take the row whose `status` is
`current`: its `code` is the unit, and its `digits` how many decimal places an amount in it may have — `"12.50"` in a
currency of two, `"1250"` in one of none.

### An id nobody told you

A name that establishes an identity is what makes a thing known to every garden, so one nobody gave you is never made
up, and never copied from this page. Its `name` says `as: unknown`, and its note what is missing. Ali's garden, before
she has read its id out:

<!-- unsaid: beans/garden-ali.md, for name -->
```markdown
---
bean: garden-ali
kind: garden
title: "garden-ali — the garden Ali keeps"
summary: "Ali's own daftar garden. She keeps it; what passes between it and this one is proposed, never written."
statements:
  - say:  { by: sam, at: now }
  - name: { by: garden-id, of: self, as: unknown, note: "its id: what `python3 bin/dmpropose.py id` prints in Ali's garden" }
  - own:  { by: ali, of: self }
---
Ali's garden. Its id is still to be read out there.
```

Until that id is known, the name her garden gave her cannot be written either: her bean is her name here until the id
arrives and her garden's name for her is added — a name that establishes an identity, which the gardener ratifies. The
gate refuses a name qualified by a garden this one does not know:

<!-- unsaid: beans/ali.md, for name -->
```markdown
---
bean: ali
kind: person
title: "Ali"
summary: "Ali, who keeps a garden of her own; Sam shares costs with her."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Ali keeps garden-ali. The name her garden gave her is written here once its id is known.
```
