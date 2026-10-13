# accounting — the books of an entity, read from what moved

`accounting` is the asset of the `accounting` profile. A garden that takes the profile (VOCAB.md `profiles:
[accounting]`, a RULE-CHANGE the gardener ratifies) receives it at `assets/accounting/`, and a garden that leaves the
profile has it taken away. Its files are the release's: an edit to one is a RULE-CHANGE, as an edit to any tool the
release ships is.

It opens no concept of its own. What it reads is the law's: a chart of accounts is a scheme naming the profile's form
`chart` (core/law/profiles.yaml), a booking is a `book` statement moving an amount from one account to another, a
correction is the move booked in the reverse sense (`sense: "-1"`), two records of one movement are a `match`, and a
period's close is a `pin` of a reading whose step is `books`. The gate judges each of them (rule `profile`, rule
`kept`); this asset reads them, and stores nothing.

## What it reads

    python3 assets/accounting/bin/books.py vouchers                       # every voucher, numbered in day order
    python3 assets/accounting/bin/books.py trial --unit XTS [--from] [--to]
    python3 assets/accounting/bin/books.py ledger 11 --unit XTS [--party ali]
    python3 assets/accounting/bin/books.py pl --unit XTS --from 2026-01-01 --to 2026-12-31
    python3 assets/accounting/bin/books.py balance --unit XTS --at 2026-12-31
    python3 assets/accounting/bin/books.py open                           # each line awaiting an account
    python3 assets/accounting/bin/books.py closes                         # each period closed: its day, its commit

Each reads the books of the gardener (`--entity <bean>` for another's) in the garden's one chart (`--chart <scheme>`
where it keeps more), and prints them for a person, or as data with `--json`: every amount a count as text, a decimal
where it terminates and `n/d` where it does not, never a JSON number. Two currencies are never added, so a reading that
sums is read in one (`--unit`).

**A voucher** is read for each payment the entity paid, received or bears a share of, and for each other statement it
booked (the books' `open`, a `measure`, another booking):

- a payment booked on **one side** takes the other from the payment: its means (the account that `stands_for` its
  `through`, or the account a matched bank line's means stands for; else the chart's `unsaid`), each other bearer's
  share (the account that stands for the bearer, or that holds parties of their kind), what it settles of an
  obligation these books accrue. The entity's own part goes where its bookings say; what none places waits in the
  account whose role is `awaiting`.
- a booking that names **both sides** is written whole: its lines are its own.
- a payment **a clause asks**, booked here, is accrued on its due day and on each occurrence of its `every` that has
  fallen due; a clause that occurs `each` time a reading holds a member is bin/ledger.py's to read, and is said.
- a move booked **in the reverse sense** is the lines of what it books, their ends exchanged, on its own day.
- a **match** counts one movement once: the record said carries the voucher, and the line read from a bank's file is its
  evidence.

**A balance** is what arrived at an account less what left it, rolled up the chart, and shown in the sense of its
element (core/law/profiles.yaml `elements`): an asset or an expense as what arrived, a liability, equity or an income
as what left — a magnitude, never a stored sign.

## Closing a period

A close is the books' reading through a day, pinned at a commit — no word of its own:

```yaml
  - reckon: { id: books-2026-09, reading: { what: "the books through September", steps: [ { id: through, op: books, to: "2026-09-30" } ] } }
  - pin: { id: closed-09, of: [books-2026-09], at: [now, "garden@<the commit before the close>"] }
```

From then on, rule `kept` refuses a commit that changes or takes out a payment, a booking or a match those books read,
on a day on or before the closed one, that was in its bean at the pinned commit: a correction is the move's reverse, and
a booking after that day. Each closed period is read as its own close's commit read it. What came after a close with
a day on or before it — a bank line found later, a booking made since — is read on the first day after that close, as
the difference: inside the next period where it came before that period was closed too, else on the first open day.
So the books through any closed day add up to what was read when it was closed. Nothing of the books is kept at
closing: the commit is. A garden that closes every month reads one past reading for each close, each time.

`python3 bin/reckon.py <bean>#<reading>` reads the step `books` itself: each account's net charge through the day, per
currency.
