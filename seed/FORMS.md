# Forms — what an agent writes most, the way the gate accepts it

Read this page before writing in a garden. It holds the shapes of six recipes of `COOKBOOK.md` — the gardener,
another person and the garden she keeps, an event, money between two people, an agreement paid in instalments, and a
proposal to another garden: their example beans, copied from it byte for byte (the cookbook explains each) — after the
misreadings agents make most, and before the forms for **what nobody said**. Every bean on this page passes the gate as
written: `test/germinate.py` commits each one in a freshly grown garden, and `test/docs.py` holds the examples to the
cookbook's.

Write what you were told, in these shapes, and copy no value from here: `sam`, `ali`, `XTS`, `123456789abc` and the
amounts below are the example's. The shapes carry no day: a day someone said goes where a field is empty, and
`as_of: now` stays as it is — the save writes the day in its place. Beans that name each other are committed together. A bean is saved with its
journal entry in one command, which writes the entry (its heading read from the clock), stages everything and commits:

```sh
python3 bin/dmsave.py "<who>" "<what you did>" --body "- action: added [[<id>]]."
```

`log/journal.md` is never edited by hand. When the gate refuses, its message says what to write: fix it, then run
`python3 bin/dmsave.py --again`. `python3 bin/dmwhy.py <term>` says why a rule is as it is. For a question this page
does not answer, `AGENTS.md` says where the law is. Every command here is written `python3`; on Windows it is `python`.

## Common misreadings

What agents writing in gardens got wrong most often, in measured runs — each one a value nobody said, invented:

- **Today is not the day it happened.** `day`, `accepted`, `agreed` and `due` are shown empty below, and stay empty
  unless someone said that day — nor is the day of writing, or a date in another bean, the day it happened. An
  event's timing nobody said is `event-anchored` (*What nobody said*, at the end).
- **A transaction's amount is the whole that moved.** Its `borne_by` shares divide it: 90 paid by one and borne two
  parts to one is `amount: { count: "90", … }` with shares 2 and 1 — never the 30 that one of them owes.
- **A currency is named by its code, looked up, not guessed.** People say "lira", "euro", "rial":
  `grep -i "<the name>" seed/knowledge/currencies.tsv`, the row whose status is `current`. When no row or more than
  one fits, ask — or leave the transaction out and put the question in `open:`.
- **Everyone named is a person bean** — also someone only spoken about; and a conversation or a meeting in which
  something was agreed is itself an event, named by what was agreed there.
- **How something was paid is written only as said** — a card, cash, a transfer, and whose.
- **`open:` belongs to the front matter**, between the two `---` lines. Below them it is prose the gate cannot see.

## The gardener, first

A garden is kept by its **gardener**, and a garden grown with `--gardener` begins with their bean.

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

## Another person, and the garden she keeps

Ali keeps a garden of her own, and nothing outside a garden writes in it — not Sam, and not Sam's agent, even on one machine.

<!-- example: beans/garden-ali.md -->
```markdown
---
bean: garden-ali
genos: garden
title: "garden-ali — the garden Ali keeps"
status: active
summary: "Ali's own daftar garden. She keeps it; what passes between it and this one is proposed, never written."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: garden_id, value: "123456789abc", class: logical, establishing: true }   # replace with what `dmpropose id` printed in Ali's garden
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: ali } } }
responsibility: { legal: { holder: { bean: ali } } }
---
Ali's garden. Its id is what `python3 bin/dmpropose.py id` printed there.
```

<!-- example: beans/ali.md -->
```markdown
---
bean: ali
genos: person
title: "Ali"
status: active
summary: "Ali, who keeps a garden of her own; Sam shares costs with her."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "123456789abc/person:ali", class: logical, establishing: true }   # her garden's id, as above
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
---
Ali keeps garden-ali. Her name here is the one her own garden gave her.
```

## A happening: an event

A dinner, a meeting, a call in which something was agreed is an `event`.

<!-- example: beans/dinner-at-sams.md -->
```markdown
---
bean: dinner-at-sams
genos: event
title: "dinner-at-sams — dinner at Sam's, where the washing-machine loan was agreed"
status: active
summary: "Ali came to dinner at Sam's; they agreed the loan for her washing machine."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: event_id, value: "event:dinner-at-sams", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { holder: { bean: sam } } }
timing:
  start: { system: gregorian-civil, at: "2026-09-12 19:30+03:00", unit: minute }
refs:
  host:  { bean: sam, rel: host }
  guest: { bean: ali, rel: present }
---
Dinner at Sam's.
```

## Money between two people

Sam and Ali bought a camera together.

<!-- example: beans/shared-camera.md -->
```markdown
---
bean: shared-camera
genos: contract
title: "shared-camera — Sam and Ali bought a camera together"
status: active
summary: "Sam and Ali share a camera; Ali paid for it, and they bear its cost two to one."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:shared-camera", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, accepted: }   # accepted: the day this party accepted; empty unless said
  ali: { who: { bean: ali }, accepted: }   # accepted: the day this party accepted; empty unless said
over:
  - { what: "a camera the two of them use" }
words: { form: spoken, agreed: }   # agreed: the day it was agreed, in any calendar; empty unless said
transactions:
  camera:
    what: "the camera, bought online"
    amount: { count: "90.00", unit: XTS }
    day:   # day: the day it happened, where known; empty unless said
    paid_by:
      - { party: ali }
    borne_by:
      - { party: sam, share: 2 }
      - { party: ali, share: 1 }
---
Sam uses the camera more, so Sam bears two parts of its cost and Ali one.
```

## An agreement paid in instalments

Sam lent Ali the price of a washing machine, to be repaid in six monthly instalments, with interest on one paid late.

<!-- example: beans/washer-loan.md -->
```markdown
---
bean: washer-loan
genos: contract
title: "washer-loan — Sam lent Ali the price of a washing machine, repaid monthly"
status: active
summary: "Sam paid for Ali's washing machine; Ali repays it in six monthly instalments, with interest on one paid late."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:washer-loan", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, role: lender, accepted: }   # accepted: the day this party accepted; empty unless said
  ali: { who: { bean: ali }, role: borrower, accepted: }   # accepted: the day this party accepted; empty unless said
over:
  - { what: "the price of Ali's washing machine" }
words: { form: spoken, at: { bean: dinner-at-sams }, agreed: }   # agreed: the day it was agreed, in any calendar; empty unless said
clauses:
  instalments:
    what: "Ali repays 20 XTS on the first day of each month, six times"
    by: ali
    to: sam
    amount: { count: "20.00", unit: XTS }
    due:   # due: the day it falls due — the first day, when it repeats; empty unless said
    every: { of: time, in: gregorian-civil, each: month, times: 6 }
  late-interest:
    what: "an instalment paid after its day carries one percent of itself for each month it is late"
    by: ali
    to: sam
    amount: { count: 1, unit: percent }
    when: "an instalment is paid after the day it was due"
transactions:
  the-loan:
    what: "Sam paid the shop for Ali's washing machine"
    amount: { count: "120.00", unit: XTS }
    day:   # day: the day it happened, where known; empty unless said
    paid_by:
      - { party: sam }
    borne_by:
      - { party: ali, share: 1 }
---
Agreed over dinner; nothing was written down.
```

## Proposing to another garden

Ali's garden is recorded here, and hers records Sam's (*Another person, and the garden she keeps*, above).

```sh
python3 bin/dmpropose.py mint shared-camera     # prints the qualified name and the dmsafe command that writes it
python3 bin/dmpropose.py mint sam               # the gardener, written by hand here, whom every agreement names
```

```sh
python3 bin/dmpropose.py make --to garden-ali --under shared-camera shared-camera
```

```sh
python3 bin/dmpropose.py read ../PROPOSAL-<garden>-<when>.md    # writes nothing
python3 bin/dmpropose.py take ../PROPOSAL-<garden>-<when>.md    # writes in the working tree; commits nothing
```

<!-- example-entry: beans/shared-camera.md parties.ali -->
```yaml
  ali: { who: { bean: ali }, accepted: , provenance: { src: asserted-by-human, by: "ali", as_of: now } }   # accepted: the day this party accepted; empty unless said
```

## What nobody said

A fact nobody said is never made up — not to fill a form, and not to get past the gate. Each form below passes the gate
as written, in a garden that holds the recipes above.

### An event whose day nobody said

An event needs `timing`. When nobody said its day, place it by what it came after (`after:`) or before (`before:`) —
another bean's id, or a few words — at `unit: day`, and say in `note` what is known of when:

<!-- unsaid: beans/call-with-ali.md, for timing -->
```markdown
---
bean: call-with-ali
genos: event
title: "call-with-ali — Sam called Ali about the phone, some day after the dinner"
status: active
summary: "Sam and Ali spoke on the phone after the dinner at Sam's and agreed a loan for her phone; nobody said the day."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: event_id, value: "event:call-with-ali", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { holder: { bean: sam } } }
timing:
  start: { system: event-anchored, at: "after:dinner-at-sams", unit: day, note: "after the dinner at Sam's; its day was not said" }
refs:
  caller: { bean: sam, rel: host }
  callee: { bean: ali, rel: present }
open: ["which day the call was"]
---
Sam called Ali some day after the dinner; nobody said which.
```

The gate prints one WARN beside it: the law still declares `event-anchored` vacant, a note for whoever maintains the
law. The commit goes through.

### A day nobody said

A day nobody said — `accepted`, `agreed`, `day`, `due` — stays empty, as the forms show it, or is left out: each of
them may be absent. A party with no `accepted` has no acceptance on record, and the record then says just that. The
`as_of` of a provenance is the day the fact was written down: write `now`, and the save writes that day in its place.

### An amount nobody said

A transaction records what moved, so it has an amount: while nobody has said the amount, there is no transaction. A
clause may leave `amount` out, and its `what` then says how the amount will be known. Over that call, Sam lent Ali the
price of a phone, to be repaid monthly; nobody said the price, the instalments, or a day:

<!-- unsaid: beans/phone-loan.md, for clauses, words, parties -->
```markdown
---
bean: phone-loan
genos: contract
title: "phone-loan — Sam lent Ali the price of a phone, repaid monthly in amounts not yet said"
status: active
summary: "Sam paid for Ali's phone; she repays it monthly. The price, the instalments and the day were not said."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:phone-loan", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, role: lender }
  ali: { who: { bean: ali }, role: borrower }
over:
  - { what: "the price of Ali's phone" }
words: { form: spoken, at: { bean: call-with-ali } }
clauses:
  instalments:
    what: "Ali repays the price monthly; how much each month, and from when, is not yet said"
    by: ali
    to: sam
    every: { of: time, in: gregorian-civil, each: month }
open: ["what the phone cost", "how much each instalment is, how many, and from which day"]
---
Agreed on the phone; nothing was written down, and the instalments are still to be said.
```

### A question still open

What a bean has not answered goes in its `open:` list, as the two beans above show: `open: ["which day the call was"]`.
Any bean may carry one. A key of your own is refused: the gate takes only the keys the law declares.

### A currency

An amount's `unit` is its currency's code. Find it by the currency's name in English, in the table the gate reads:

```sh
grep -i "<its name in English>" seed/knowledge/currencies.tsv
```

(In PowerShell: `Select-String "<its name in English>" seed\knowledge\currencies.tsv`.) Take the row whose `status` is
`current`: its `code` is the unit, and its `digits` how many decimal places an amount in it may have — `"12.50"` in a
currency of two, `1250` in one of none. `XTS`, in the recipes above, is the code ISO keeps for testing, never a real
amount's.

### An id nobody told you

An anchor is what identifies a thing to every garden, so one nobody gave you is left out — never made up, and never
copied from this page. A bean left with no establishing anchor says `identity.status: provisional`, and `open:` says what
is missing. Ali's garden, before she has read its id out:

<!-- unsaid: beans/garden-ali.md, for identity -->
```markdown
---
bean: garden-ali
genos: garden
title: "garden-ali — the garden Ali keeps"
status: active
summary: "Ali's own daftar garden. She keeps it; what passes between it and this one is proposed, never written."
nature: lekton
identity:
  status: provisional
  anchors: []
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: ali } } }
responsibility: { legal: { holder: { bean: ali } } }
open: ["its id: what `python3 bin/dmpropose.py id` prints in Ali's garden"]
---
Ali's garden. Its id is still to be read out there.
```

Until that id is known, the name her garden gave her cannot be written either: her bean's `person_id` is `person:ali`,
a name this garden gives her, until the id arrives and her garden's name for her replaces it — a change to an anchor,
which the gardener ratifies.
