# Cookbook — the common things, written the way the gate accepts them

Every block marked `<!-- example: … -->` below is **committed into a freshly grown garden by
`test/germinate.py`**, after the laptop from `seed/README.md`, one recipe at a time and in the order of this page —
so the page can be followed from the top, each recipe needing only what came before it. If the law moves and one
stops passing, that test fails — so these are not illustrations that can quietly go stale.

The scenario: Sam keeps this garden. Sam registers `example.org`, keeps a NAS at home that serves the website for
it, and rents a VPS — and shares costs with a friend, Ali, who keeps a garden of her own.

Each recipe's bean is committed with its journal entry, written through `bin/dmjournal.py` (`seed/README.md` shows
how) after the bean is written. A bean's `as_of` is the day it was written down, the clock's and never typed: the
examples write `now`, and the tool writes the day of its entry in its place. It does the same for `observed: now`,
where a thing was looked at on the day it was written down. Every command here is written `python3`; on Windows it is
`python`.

## The gardener, first

A garden is kept by its **gardener**, and a garden grown with `--gardener` begins with their bean. The gardener
ratifies what an agent may not decide; an agent tends the garden. `python3 seed/germinate.py <dir> --gardener sam --gardener-name "Sam"`
writes the bean and names it in `GARDEN.md`, and its name is qualified at birth by the garden's own id —
`<garden id>/person:sam` — so another garden can name Sam from the first proposal on. By hand, write the bean and
set `gardener: sam` in `GARDEN.md` — a change to the manifest, so its journal entry says RULE-CHANGE
(`seed/README.md` shows the whole first commit). The gate asks for a gardener as soon as the garden holds a bean,
and its last line names them.

A person is owned by no one — the crown, `agape` — and answers for themselves. This one was written by hand, so its
name is bare, `person:sam`: it names Sam in this garden only, and is qualified before it crosses to another
(*Another person's garden*, below):

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

A garden may be kept by an organisation — a household, a club, a company — and then its gardener is an `org`
bean, and a person who answers for it ratifies (`MODEL.md`, the Contract of Parts).
`python3 seed/germinate.py <dir> --gardener ben-household --gardener-genos org --gardener-name "Ben's household"`
plants one: owned outside the garden, by whoever its own rules say, and answering for itself.

## How to say that one thing relates to another

Pick the most specific relation that is true; `refs` is the open fallback.

| you want to say | write | notes |
|---|---|---|
| who owns it, and who answers for it | `owned_by` + `responsibility` | always both, facet by facet: `legal`, `technical` and the other rows of the law's `facets` registry |
| something outside this ledger owns it | `owned_by: { legal: { external: "…" } }` | a rented VPS, third-party software, a registered domain |
| a running thing sits on a machine | `lives_in: { bean: … }` | the machine must say what habitat it offers (`provides_habitat`) |
| a running thing is a copy of some software | `instance_of: { bean: … }` | required on `genos: instance`, together with `lives_in` |
| it cannot work without another thing | `depends_on: { <name>: { bean: … } }` | must stay acyclic |
| people agreed on something | a `contract` bean: `parties`, `words`, `clauses`, `transactions` | may be owned by none of its parties: `crown: logos`, answered for by `parties: true` |
| who took part in a happening | `refs` on the `event`, `rel: host`, `present`, `invited`, `paid` | owned by none of them: `crown: logos`, answered for by its host |
| anything else — "serves", "is DNS for", "backs up" | `refs: { <slot>: { bean: …, rel: <kebab-verb> } }` | `rel` is free text, so a new relation needs no rule change |

Anchors say what an object IS, so two gardens recognise the same thing. A machine is best anchored on
hardware (a serial or a MAC); a rented machine you cannot touch on its name (`fqdn`); a domain on its `fqdn`;
software or a deployment on a logical id you choose (`product_id`, `service_id`). A person uses a logical id
(`person_id`) — never their name. An agreement or a happening uses an id you mint (`contract_id`, `event_id`); a
document its `content_hash`, or the reference its home gives it (`doc_id`); another garden its `garden_id`.

## A registered domain

A domain is registered for a term, not owned outright, so the registry is the `external` owner and the
person who renews it answers for it. Registration facts belong to the opt-in **`domain` profile**: a garden
that holds domains adds this inside `VOCAB.md`'s front matter, and `registration` then becomes available and
required on every `genos: domain` bean. Its dates are read from WHOIS before the bean is written: `created` and
`expires` take a date and nothing else — there is no `unknown` for a fact that is always there to be read, and
an invented date would pass the gate and then be reported as sound by `dmstale`. `auto_renew` alone may be
`unknown`, because it is an account setting WHOIS does not show. `observed` is the day they were read — here the day
of writing, so `now`.

<!-- example-front-matter: VOCAB.md -->
```yaml
extends_profiles: [domain]
```

<!-- example: beans/example-org.md -->
```markdown
---
bean: example-org
genos: domain
title: "example.org — Sam's domain"
status: active
summary: "The domain Sam's website answers on."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: fqdn, value: "example.org", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { external: "the .org registry, under a registration agreement" } }
responsibility: { legal: { holder: { bean: sam } } }
registration:
  registrar: "Example Registrar Inc."
  created: 2020-01-15
  expires: 2027-01-15
  auto_renew: enabled
  observed: now
  source: "WHOIS for example.org"
---
Sam's domain.
```

## A machine at home that other things run on

`provides_habitat` is what lets something `lives_in` it. `roles` says what the machine does — a list,
because a machine does several things.

<!-- example: beans/nas.md -->
```markdown
---
bean: nas
genos: host
title: "nas — Sam's home NAS"
status: active
summary: "A NAS at home: file storage, and the web server for example.org."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "NAS-0042", class: hardware, establishing: true }
    - { key: hostname, value: "nas", class: network, establishing: false }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } }, technical: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } }, technical: { holder: { bean: sam } } }
provides_habitat: linux-baremetal
roles:
  - { role: file-server }
  - { role: web }
---
The NAS.
```

## Third-party software, and a running copy of it that serves the website

The software is a `product` owned by its authors; the running copy is an `instance` of it that lives on
the NAS and is Sam's. "Serves this domain" has no dedicated relation, so it is a `refs` entry with a `rel`.

<!-- example: beans/nginx.md -->
```markdown
---
bean: nginx
genos: product
title: "nginx — the web server software"
status: active
summary: "Third-party web server software, run here but owned by its project."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: product_id, value: "product:nginx", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { external: "the nginx project" } }
responsibility: { legal: { holder: { bean: sam } } }
---
The web server software.
```

<!-- example: beans/website.md -->
```markdown
---
bean: website
genos: instance
title: "website — nginx on the NAS, serving example.org"
status: active
summary: "The web server instance on the NAS that answers for example.org."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: service_id, value: "nginx:example.org@nas", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
instance_of: { bean: nginx }
lives_in: { bean: nas }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
refs:
  domain: { bean: example-org, rel: serves }
---
The website.
```

## A rented VPS

A virtual machine has no matter of its own: it is a `virtual-host`, of the nature empsychon, and lapses at teardown.
It is identified by its name or by the id its provider assigns — never by a serial, which is the hypervisor's. The
provider owns it and Sam answers for what runs on it.

<!-- example: beans/vps-a.md -->
```markdown
---
bean: vps-a
genos: virtual-host
title: "vps-a — a rented virtual server"
status: active
summary: "A VPS rented from a hosting provider."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: fqdn, value: "vps-a.example.org", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { external: "the hosting provider, which owns and operates the machine" } }
responsibility: { legal: { holder: { bean: sam } } }
provides_habitat: linux-vm
---
The rented server.
```

## Another person, and the garden she keeps

Ali keeps a garden of her own, and nothing outside a garden writes in it — not Sam, and not Sam's agent, even on
one machine. Gardens meet only by **proposal**: one file of beans, laid outside both gardens, that the other
garden's gardener takes in by committing it, or does not (`MODEL.md`, Between gardens: peering).

Sam shares costs with Ali, and lent her money over a dinner — the recipes after this one — so she is recorded
before them, and so is her garden: the record of a person who keeps a garden of her own names her the way her
garden does.

**Know each other.** A garden is known by the commit it germinated from. Germination writes a random seed into that
commit, so two gardens grown with one name in the same second are still two. In each garden,
`python3 bin/dmpropose.py id` prints its id, its name and its gardener; the gardeners tell each other.

**First contact: the other garden, and who keeps it.** A garden deals only with a garden it has recorded:
a `garden` bean, anchored by the id the other gardener read out, owned by that gardener and answered for by them — so
that gardener is a person (or organisation) bean here too. Accepting a garden, and a name for whoever keeps it, is the
gardener's decision (class F): write the beans, journal them in one entry, and commit them as ONE commit.

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

`123456789abc` stands for Ali's garden's id: write the twelve digits `python3 bin/dmpropose.py id` printed there,
here and in her name below. An id copied from this page passes the gate, and the first proposal then goes to a
garden that does not exist.

**Another person is kept by name only on their own word.** A garden's git is copied whole to every clone, so a person
who is not the gardener is written by name only with their `consent`: an agreement in which they accepted being kept
here. Without it, write them as `python3 bin/dmheld.py person name=…` mints them — an opaque id, the name held off
git — and the gate refuses a named one. Ali said yes over the phone:

<!-- example: beans/ali-consent.md -->
```markdown
---
bean: ali-consent
genos: contract
title: "Ali's consent"
status: active
summary: "Ali agreed to be kept here by name."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:ali-consent", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, accepted: 2026-09-01 }
  ali: { who: { bean: ali }, accepted: 2026-09-01 }
words: { form: spoken, agreed: 2026-09-01 }
---
Agreed on the phone. Where she will be is never written here.
```

A person is best named by their own garden, so Ali is written under the name hers gave her, byte for byte. Her
garden was grown with `--gardener ali`, which names her by its id and hers: `<her garden's id>/person:ali`. The rest
of the bean is Sam's record, in Sam's words:

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
consent: { bean: ali-consent }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
---
Ali keeps garden-ali. Her name here is the one her own garden gave her.
```

The tools do this with you from either side. When a proposal comes first from a garden not yet recorded, `read`
refuses it and prints both beans to write, the other gardener's name taken from the proposal. When you propose
first and know the other gardener only by a name your own garden gave them, they travel as a stub marked
`gardener-of: to`, and the other garden reads it as its own gardener. How a proposal is made and taken is
*Proposing to another garden*, below, once there is something to propose.

## A happening: an event

A dinner, a meeting, a call in which something was agreed is an `event`. When is `timing`, at the resolution
actually known; who took part is `refs`, each naming what they were. A happening between people is owned by none
of them: it ends at the crown, `logos`, as an agreement may, and whoever hosted it answers for it.

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
    - { key: event_id, value: "event:dinner-at-sams-2026-09-12", class: logical, establishing: true }
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

Sam and Ali bought a camera together. Ali paid for it; Sam uses it more, so they agreed Sam bears two parts of its
cost and Ali one. That is an agreement, so it is a `contract` bean, and what moved under it is a transaction:
an amount, the `day` it moved where that is known, who paid how much of it (a single payer who states no amount
paid the whole), and who bears it in whole-number shares — each party once in each list, in any order.

- **An agreement between people may be owned by none of them.** Then it ends at the crown (`logos`, the branch for
  what is lekton, said and agreed), and its parties answer for it, each for what binds it:
  `responsibility: { legal: { parties: true } }`.
  One a person wrote and offers may instead be owned by its author.
- **An offer is not an acceptance.** A party with `accepted` said yes on that day; a party without it has no
  acceptance on record — an offer not yet taken up, or a yes nobody wrote down. Here Sam reports Ali's yes, and the
  bean's provenance says so; Ali's own word is what her own garden records.
- **An amount is exact.** `{ count, unit }`: the unit a currency code, the count a whole number or a decimal
  written as a string, with no more places than the currency uses — never a float, and always in plain decimal
  digits: YAML's other spellings of a number (`010`, `0x64`, `1:30`) are refused, never read as another amount.
  `900`, `"900"` and `"900.00"` are one amount to a merge; the bean keeps what was written. `XTS` is the code ISO reserves
  for testing; write your own currency's. The gate checks that what was paid adds up exactly to the whole.
- **What is owed is read, never written.** There is no `balance`: `python3 bin/dmledger.py shared-camera` reads
  the transaction — Ali paid 90.00 XTS and bears one part in three — and says `sam owes ali 60 XTS`: each bearer owes
  each payer its share of what that payer paid, and what two parties owe each other in both directions is netted.
  It computes in fractions, so nothing is rounded, and prints each amount in its shortest exact form. A share that
  does not come out even in the currency's places is printed as the fraction it is (`200/3 XTS`), with a note, and
  who takes the remainder is something the parties agree, in a clause. `--between sam ali` nets across every
  agreement the two share. It never writes; it exits 0, or 2 when it is not run in a garden, a bean named is not
  there or does not parse, or `--between` is not given two parties.

Ali is the person bean recorded above, under the name her own garden gave her.

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
  sam: { who: { bean: sam }, accepted: 2026-09-10 }
  ali: { who: { bean: ali }, accepted: 2026-09-10 }
over:
  - { what: "a camera the two of them use" }
words: { form: spoken, agreed: 2026-09-10 }
transactions:
  camera:
    what: "the camera, bought online"
    amount: { count: "90.00", unit: XTS }
    day: 2026-09-10
    paid_by:
      - { party: ali }
    borne_by:
      - { party: sam, share: 2 }
      - { party: ali, share: 1 }
---
Sam uses the camera more, so Sam bears two parts of its cost and Ali one.
```

## An agreement paid in instalments

Sam lent Ali the price of a washing machine, to be repaid in six monthly instalments, with interest on one paid
late. What the agreement asks is written as **clauses**, each a position on the `capability` square — `required`
(must, the reading when `stance` is silent), `omissible` (need not), `permitted` (may), `forbidden` (must not) —
with who it binds (`by`), whom it is owed to (`to`), how much, from when (`due`) and how it repeats (`every`). A
clause that is not brought into force by a date says what brings it (`when`). `bin/dmstale.py` warns before each
instalment falls due, and stops once a clause's `state` says it was met, waived or broken.

They agreed it over dinner, and nothing was written down: `words` says it was spoken, and where.

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
  sam: { who: { bean: sam }, role: lender, accepted: 2026-09-12 }
  ali: { who: { bean: ali }, role: borrower, accepted: 2026-09-12 }
over:
  - { what: "the price of Ali's washing machine" }
words: { form: spoken, at: { bean: dinner-at-sams }, agreed: 2026-09-12 }
clauses:
  instalments:
    what: "Ali repays 20 XTS on the first day of each month, six times"
    by: ali
    to: sam
    amount: { count: "20.00", unit: XTS }
    due: 2026-10-01
    every: { of: time, in: gregorian-civil, each: month, times: 6 }
  late-interest:
    what: "an instalment paid after its day carries one percent of itself for each month it is late"
    by: ali
    to: sam
    amount: { count: 1, unit: percent }
    when: { said: "an instalment is paid late" }
transactions:
  the-loan:
    what: "Sam paid the shop for Ali's washing machine"
    amount: { count: "120.00", unit: XTS }
    day: 2026-09-13
    paid_by:
      - { party: sam }
    borne_by:
      - { party: ali, share: 1 }
---
Agreed over dinner; nothing was written down.
```

`python3 bin/dmledger.py washer-loan` reads what Ali owes Sam and lists each clause in force with its next day.
When an instalment is paid, it is a transaction too — Ali paid it, Sam bears it, `under: instalments` — and the
clause's `state` says `met` once all six are. A clause left as a disagreement by a merge is neither in force nor
met: both tools report it as a disagreement for a person.

A monthly clause on a day some months lack — the 31st — has no occurrence in those months: the day is skipped, as
RFC 5545 skips it for a calendar, and never moved to a day nobody named. `dmstale` and `dmledger` say so in a note
beside the clause. If the parties meant another day, the clause's `what` says which. A day the calendar does not
have at all — `2026-02-30` — is refused by the gate.

Payments recorded `under:` a clause are not yet matched to its occurrences. `dmledger` reads what they add up to,
and takes the next day, and which occurrence it is, from the calendar alone: it does not say that an instalment was
missed or paid late, and nothing computes the late interest. That is still read by a person, from the transactions.

## A statement: a document, and a capture of its lines

Sam paid for the washing machine by card, and the bank's statement shows it. The statement is a `document`: words
and figures fixed in a form that can be kept. Its identity is its content — `content_hash`, the SHA-256 of the
file's bytes, so a changed byte is another document — and `located_at` says where the copy is. The bank wrote it,
so the bank owns it; Sam holds the copy.

Its lines are someone else's truth, so they are a **capture** on it: a dated copy taken so it can be read again,
never authoritative, and never carrying a secret. `redactions` says what was left out and why — here the card
number, which is a secret.

<!-- example: beans/card-statement-2026-09.md -->
```markdown
---
bean: card-statement-2026-09
genos: document
title: "card-statement-2026-09 — Sam's card statement for September 2026"
status: active
summary: "The statement Sam's bank issued for the card that paid for the washing machine, kept as a PDF."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: content_hash, value: "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { external: "the bank that issued the card, which wrote the statement" } }
responsibility: { legal: { holder: { bean: sam } } }
located_at:
  - { system: unix-filesystem, openness: here, at: "laptop:/home/user/documents/card-statement-2026-09.pdf", observed: now }
capture:
  lines:
    of: "the statement's transaction lines for September 2026"
    owned_by_them: "the bank that issued the card"
    source: "read by hand from the PDF, page 1"
    taken_at: 1790928000000
    staleness_key: "the statement's content_hash: a changed byte is another statement"
    redactions: "the card number, all but its last four digits — a card number is a secret"
    holds: "2026-09-13 · appliance shop · 120.00 XTS · card ending 4242"
---
The card statement.
```

`content_hash` is `sha256:` and the file's SHA-256 in lowercase hexadecimal: `sha256sum <file>` prints it on Linux,
`shasum -a 256 <file>` on macOS, and in PowerShell
`"sha256:" + (Get-FileHash -Algorithm SHA256 <file>).Hash.ToLower()` — `Get-FileHash` prints capitals, and the gate
refuses them.

On Windows the copy has a Windows path, in the `windows-filesystem` system. Write it in single quotes: inside double
quotes YAML reads a backslash as the start of an escape, and `"C:\Users…"` is refused before the gate reads it.

<!-- example-located-at: beans/card-statement-2026-09.md -->
```yaml
located_at:
  - { system: windows-filesystem, openness: here, at: 'laptop:C:\Users\sam\Documents\card-statement-2026-09.pdf', observed: now }
```

## What a line held at each position: a series

Sam's balcony has a rain gauge that logs, each hour, how much rain fell in the hour after the reading and how full
its battery is. What varies along a line — a reading at each moment, a porosity at each depth down a core — is a
**series**: an entry of `series` on the being that holds it. It says where its positions are, what each position
holds, and then the rows, as one table.

- **Where the positions are.** By a rule — a `grid`, a repetition with a `from`, row 0 at `from` and each next row at
  the next occurrence — or listed, in a `span`, an extent from whose `from` each row writes its offset in the first
  column (`at`; `from` and `to` when a row is a region). `unit` is what an offset counts and the resolution held: a
  grid's stride is a whole number of it.
- **Where a row sits** is `placement`: here each row stands at its hour and over the hour after it (`following`), as
  an hour's rain does; at a point is the reading when it is silent.
- **What each position holds** is `holds`, one channel per column: a measured value (`quantity` and its one `unit`), a
  position (`system`), or a code of a published scheme (`scheme`). `stands_for` says what a cell is over its row's
  place: the rain is a `sum` over its hour, the battery a reading at its moment. `between: linear` reads a point on a
  straight line between two rows, only where the line and the channel are both metered. `u` is the channel's standard
  uncertainty: a value read between rows is printed to its digits. `python3 bin/dmrules.py --terms` lists every
  position each of these may take.
- **The rows** are a table: a header naming each column once, then one line per row, one TAB between two cells. No
  cell is ever empty: a value nobody read is a gap token, which says why — here `-`, nothing was read; `python3
  bin/dmrules.py` lists the others. A table longer than a hundred rows goes in files instead, the parts
  `series/<bean>/<key>/<part>.tsv`, each added whole and never rewritten.

<!-- example: beans/rain-gauge.md -->
```markdown
---
bean: rain-gauge
genos: host
title: "rain-gauge — the rain gauge on Sam's balcony"
status: active
summary: "A small logging rain gauge on the balcony; it reads the rain of each hour, and its battery."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "RG-0042", class: hardware, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
series:
  september:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: hour }, from: "2026-09-14 06:00+02:00" }
    unit: hour
    placement: following
    holds:
      - { name: rain, quantity: length, unit: millimetre, stands_for: sum, u: { count: "0.2", unit: millimetre } }
      - { name: battery, quantity: ratio, unit: percent, stands_for: point, between: linear }
    rows: |
      rain	battery
      0	84
      1.4	84
      3.2	83
      -	-
      0.6	81
---
The balcony's rain gauge. Its fourth hour was not read: the logger was off while its battery was changed.
```

`python3 bin/dmseq.py show rain-gauge september` prints each row at its moment — `2026-09-14 06:00+02:00`, then
each next hour — with the table's line it came from. `python3 bin/dmseq.py at rain-gauge september "2026-09-14
07:30+02:00"` reads what each channel holds there: the battery on the line between its two readings, and the rain as
what it is — the sum over the hour that began at 07:00, never a share of it. Nothing is read before the first row or
after the last, and nothing read is stored. A cell someone sets aside — a reading they judge wrong — stays in the
table, and `excluded` names the row, the channel, who judged it and why.

## Where a case stands on a walk: a course

Ali mends bicycles, and Sam brought her his. A repair goes through the same steps each time — handed over, looked at,
mended, collected — and a **walk** says so once: the `steps` of a mapping. Each step may say who acts at it (`by`, a
key of the case's `parties`), how long it usually takes (`usually`), and whether it is a way out reached from any step
(`exit`), a pause the case comes back from (`resumes`), or an end nothing follows (`final`); `reasons` lists what a
move into it may cite. A step holds nothing else: a key the walk does not declare is refused.

<!-- example: mappings/walk-bike-repair.md -->
```markdown
---
mapping: walk-bike-repair
kind: procedure
summary: "How a bicycle repair goes, each time: handed over, looked at, mended, collected."
steps:
  - { id: handed-over, do: "the owner brings the bicycle", by: owner, next: [ { to: looked-at } ] }
  - { id: looked-at, do: "what is wrong is found", by: repairer, usually: { of: time, measure: { count: 2, unit: day } }, next: [ { to: mended } ] }
  - { id: waiting-for-part, do: "a part is ordered, and the repair waits for it", resumes: true, reasons: [part-ordered] }
  - { id: mended, do: "it is mended and ridden round the block", by: repairer, next: [ { to: collected } ] }
  - { id: collected, do: "the owner takes it home", by: owner, final: true }
  - { id: given-up, do: "the repair is abandoned", exit: true, reasons: [not-worth-it, owner-changed-mind] }
---
The steps of a bicycle repair.
```

Where one repair stands is a **course** on the case: `courses` names the walk, and each **move** along it is an entry of
`moves` — the step reached, who moved it, a `reason` from that step's list and `why` in words. Its moment is
`at: now`: the save writes the moment of its journal entry in its place, read from the clock and never typed. A move
follows a `next` of the step before it, or reaches a way out or a pause; after a pause the case returns to where it
was; a move the walk does not offer is refused unless its `why` says why, and then it warns; nothing follows a final
step.

<!-- example: beans/bike-repair.md -->
```markdown
---
bean: bike-repair
genos: contract
title: "bike-repair — Ali mends Sam's bicycle"
status: active
summary: "Ali repairs Sam's bicycle for the cost of the parts."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:bike-repair", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  owner: { who: { bean: sam } }
  repairer: { who: { bean: ali } }
over:
  - { what: "Sam's bicycle" }
words: { form: spoken }
courses:
  repair: { walk: { mapping: walk-bike-repair } }
moves:
  - { course: repair, at: now, step: handed-over, by: sam }
  - { course: repair, at: now, step: looked-at, by: ali, why: "the rear hub grinds" }
  - { course: repair, at: now, step: waiting-for-part, by: ali, reason: part-ordered }
---
Ali mends Sam's bicycle; the parts are Sam's to pay for.
```

`python3 bin/dmseq.py course bike-repair` reads where it stands: at `waiting-for-part`, since the moment of that move,
and how long ago. When the part comes, the next move returns to `looked-at`; after `mended`, who acts next is the
`owner`, read as Sam from the case's `parties`. Where a case stands is read from its moves, and never written down: a
stored stage is a second copy, and it drifts.

**A checklist is a set, not a walk.** What a case asks for — the documents a form needs, the parts a publisher wants
to see — is the `items` of a mapping of `kind: checklist`, each with an `id`, what it asks for (`do`), who provides it
(`by`), and, of items any one of which will do, the same `one_of`. When an item is needed and what meets it are
selections: `needed_when` and `met_by` each name a key of `selections`, bare on the checklist itself or
`<bean>:<key>` on another bean, as any part of a being is named.

## Proposing to another garden

Ali's garden is recorded here, and hers records Sam's (*Another person, and the garden she keeps*, above). Now the
camera they share can cross, so that her garden holds the same agreement, named the same way.

**A name is minted once, and carried.** A name a garden gives is written `<genos>:<name>` — `person:sam`,
`contract:shared-camera`. Bare, it identifies only inside the garden that minted it: two gardens that each minted
`person:sam` are shown to a person as candidates and never fused by a tool; qualified, `<garden id>/person:sam`
identifies everywhere. So before a bean crosses, every bare name it and the beans it refers to carry is qualified,
once, by the garden that recorded the thing first. An identifier someone else assigned — a package's name, a
registry number, the UID an invitation carries — is not a name a garden gave: it crosses as it is, identifies the
same thing in every garden, and is never qualified.

```sh
python3 bin/dmpropose.py mint shared-camera     # prints the qualified name and the dmsafe command that writes it
python3 bin/dmpropose.py mint sam               # the gardener, written by hand here, whom every agreement names
```

It writes nothing: choosing an anchor is the gardener's decision (class F), so the gardener runs the printed command
and saves the change with its journal entry, in one command: `bin/dmsave.py`. A gardener planted by
`germinate.py --gardener` is qualified already, and `mint` says so. A qualified prefix must be this garden's own id
or the id of a garden it holds a `garden` bean for, and the gate says so.

**Propose.** A proposal is made under an agreement whose parties include both gardeners — here `shared-camera`:

```sh
python3 bin/dmpropose.py make --to garden-ali --under shared-camera shared-camera
```

It writes one file, `PROPOSAL-<this garden>-<YYYYMMDD-HHMM>.md`, in the directory that holds this garden — beside
it, never inside any garden. The file carries each offered bean as committed, with `provenance.garden` stamped on
the copy's records that lack one (never in this garden's own files); a stub for each bean they refer to, holding
its id, genos, nature, title and establishing anchors and nothing more; the journal entry that would take them in;
and a fingerprint. `make` also appends to this garden's journal what left, to which garden, under which agreement,
and the fingerprint: commit that entry, and hand the file over however you like — it is one Markdown file.

`make` refuses to pass on what a third garden said: a record stamped by a garden that is neither this one nor the
addressee, a value a fusion says was seen only in another garden, a body section another garden gave. Only the
names a third garden gave travel, with the things they name.

A stub is a bean the other garden may not hold. The loan names the dinner it was agreed at; if Ali's garden has no
record of that dinner, her `read` says the stub is UNRESOLVED. Offer it too, and it arrives whole:
`python3 bin/dmpropose.py make --to garden-ali --under washer-loan washer-loan dinner-at-sams`.

The **fingerprint** is the SHA-256 of the whole proposal — its envelope without the fingerprint, and every line
after it, line ends read as `\n`. It tells a damaged or carelessly edited proposal from the one that was made. It is
not a signature: whoever rewrites a proposal can compute it again. So a proposal is read before it is taken, and
every refusal below holds whatever its fingerprint says.

**Read, then take.** In Ali's garden:

```sh
python3 bin/dmpropose.py read ../PROPOSAL-<garden>-<when>.md    # writes nothing
python3 bin/dmpropose.py take ../PROPOSAL-<garden>-<when>.md    # writes in the working tree; commits nothing
```

The first `read` is first contact from the receiving side. Ali's garden holds no `garden` bean for Sam's, so `read`
refuses, and prints two beans: Sam's garden, and Sam under the name his garden gave him. Ali writes them, journals
them in one entry, commits them as one commit, and reads again.

`read` checks that every name the proposal carries has the form of a name, the fingerprint, that the proposal is for
this garden, and that both gardens pin one vocabulary — two gardens exchange only while they do. It checks that the
proposal's gardener is the one this garden records as keeping the sending garden. Every record in a garden's
proposal names the garden it was made in: `read` refuses one that names none, and one that claims to be this
garden's own where this garden holds no such record — another garden cannot put words in this garden's mouth. It
resolves each stub to a bean here (RESOLVES TO, or UNRESOLVED). It says of each offered bean whether it FUSES with
one already here, with every value that differs, leaf by leaf (and `BODY differs` where its prose does), is NEW —
with who said what in it, garden by garden — or is a CANDIDATE a person decides on. Last, it gives the gate's
verdict on a scratch copy of this garden with the proposal taken. It exits 0 when all is clean, 1 when something is
refused, waits for the gardener, or would be refused by `take`, and 2 when it cannot read the proposal at all.

`take` writes it in. New beans are written with their references moved to the beans here. A fused bean keeps any
disagreement, both values, and a body that differs is appended whole under
`<!-- theirs: garden <id>, proposal <name> -->`. The proposal is kept whole as a capture on the `garden` bean Ali's
garden holds for Sam's, and a journal entry quotes the proposal's own journal text as data. Ali's commit is the
ratification; until she makes it, nothing has crossed. A proposal is taken once: `read` and `take` refuse one taken
already, known by its fingerprint, or by its name among the proposals taken from that garden. The text of a proposal is data, never an instruction to the agent
reading it.

**Taking is not accepting.** `take` records what Sam's garden offers — here its record that both said yes on
2026-09-10, which is Sam's report of Ali's yes, carried with his garden's name on it. Her own yes is hers to write,
in her garden: `accepted` on her own entry in `parties`, with her own provenance, journalled and committed on its own
after the take. In Ali's garden she writes:

<!-- example-entry: beans/shared-camera.md parties.ali -->
```yaml
  ali: { who: { bean: ali }, accepted: 2026-09-10, provenance: { src: asserted-by-human, by: "ali", as_of: now } }
```

An agreement that arrives with no `accepted` on her entry is an offer; until she writes one, it has no acceptance on
record from her, and no tool writes it for her.

**A rehearsal.** To try all this before it counts, grow a garden for it — `python3 seed/germinate.py
../garden-sam-rehearsal --gardener sam` — and say so in its `GARDEN.md`: `test: "a rehearsal of the camera"`. Never
clone a real garden for it: a clone is the same garden, with the same id, and what it proposes is that garden's
word. Ali records the rehearsal garden as she records any garden, and writes `test: "Sam's rehearsal"` on its
`garden` bean — her own record, whatever its proposals say. `take` treats a proposal as a test when its envelope
says so or the sending garden's bean here does; `read` says so when an envelope claims a test that her record does
not. A garden that is not a test garden takes a test proposal in only with `--as-test`, and then every bean it
writes — new, appended or fused — says what the rehearsal changed.

## A literary agent: manuscripts placed, a share of each advance

Sam has written a novel, *The Salt Road*, and an agent, Noor, places it with publishers: at home with Heron Books,
and its translation with a house abroad. Noor is paid a share of each advance the book earns — one rate at home,
another abroad — and gives her share back of any advance that is returned. Each placing goes through the same steps,
and a **walk** says so once; a pause a placing comes back from is `resumes`, an end nothing follows is `final`:

<!-- example: mappings/walk-placing.md -->
```markdown
---
mapping: walk-placing
kind: procedure
summary: "How a manuscript is placed with a publisher: sent, read, offered, signed — or declined, or set aside."
steps:
  - { id: submitted, do: "the agent sends the manuscript to the house", by: agent, next: [ { to: read } ] }
  - { id: read, do: "an editor reads it", by: publisher, usually: { of: time, in: gregorian-civil, level: month, count: 2 }, next: [ { to: offered, when: "the house wants it" }, { to: declined, when: "it does not" } ] }
  - { id: offered, do: "the house offers terms", by: publisher, next: [ { to: contracted } ] }
  - { id: contracted, do: "author and house sign", by: author, next: [ { to: published, when: "it goes to print" }, { to: cancelled, when: "the contract is ended" } ] }
  - { id: published, do: "the book is out", by: publisher, final: true }
  - { id: cancelled, do: "the contract is ended and the advance given back", by: author, final: true, reasons: [house-closed, author-withdrew] }
  - { id: declined, do: "the house says no", final: true, reasons: [list-full, not-for-us] }
  - { id: on-hold, do: "the placing waits", resumes: true, reasons: [author-revising, house-reorganising] }
---
The steps of placing a manuscript.
```

What a house asks to see with a manuscript is a set, not a walk — a **checklist**. The list of which translation
rights are still free is needed only when a house asks for them, and it is met when a paper that shows them is
here: both are readings (`needed_when`, `met_by`) the agency agreement below holds.

<!-- example: mappings/submission-pack.md -->
```markdown
---
mapping: submission-pack
kind: checklist
summary: "What a publisher asks to see with a manuscript."
items:
  - { id: synopsis, do: "a one-page synopsis", by: author }
  - { id: sample, do: "the first three chapters", by: author, one_of: text }
  - { id: whole, do: "the whole manuscript", by: author, one_of: text }
  - { id: letter, do: "a letter introducing the book", by: agent }
  - { id: rights-list, do: "which translation rights are free", by: agent, needed_when: "agency-noor:translation-asked", met_by: "agency-noor:rights-papers" }
---
A submission pack.
```

Noor is written by name, on her consent — the agency agreement she accepted, over a call. Her commission is a clause that occurs
**`each`** time a reading holds a member: each placing that reached `contracted`, at home or abroad, and it is a
share **`of`** that placing's own advance. A refund is its own clause, occurring for each placing that was cancelled:
an occurrence never leaves the ledger. A payment names what it **`settles`**, occurrence by occurrence. Noor's
assistant signs for her while she travels: a party **`acting_for`** another. A month's report is a reading too.

<!-- example: beans/agency-noor.md -->
```markdown
---
bean: agency-noor
genos: contract
title: "agency-noor — Noor places Sam's novel"
status: active
summary: "Noor represents The Salt Road; she earns a share of each advance, and gives her share back of one returned."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:agency-noor", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  author: { who: { bean: sam }, role: author, accepted: 2026-06-02 }
  agent: { who: { bean: noor }, role: agent, accepted: 2026-06-02 }
  assistant: { external: "the agency's assistant", role: agent, acting_for: agent }
over:
  - { what: "the novel The Salt Road, at home and in translation" }
words: { form: spoken, agreed: 2026-06-02 }
selections:
  placed-home: { what: "each placing at home that was signed", steps: [ { id: p, op: select, genos: contract, where: [ { path: courses.home, reached: contracted } ] } ] }
  placed-abroad: { what: "each translation placing that was signed", steps: [ { id: p, op: select, genos: contract, where: [ { path: courses.abroad, reached: contracted } ] } ] }
  returned-home: { what: "each placing at home whose advance was given back", steps: [ { id: p, op: select, genos: contract, where: [ { path: courses.home, reached: cancelled } ] } ] }
  translation-asked: { what: "whether a house abroad is reading it", steps: [ { id: p, op: select, genos: contract, where: [ { path: courses.abroad, exists: true } ] } ] }
  rights-papers: { what: "the papers that show which translation rights are free", steps: [ { id: d, op: select, genos: document } ] }
  by-month:
    what: "the agency's payments, month by month, as months fall where Sam lives"
    zone: Europe/Berlin
    steps:
      - { id: this, op: select, genos: contract, where: [ { path: bean, is: agency-noor } ] }
      - { id: paid, op: select, of: this, entries: "transactions.*" }
      - { id: months, op: group, of: paid, path: day, level: month, system: gregory }
      - { id: per-month, op: count, of: months }
clauses:
  commission:
    what: "the author pays the agent fifteen parts in a hundred of each advance at home"
    by: author
    to: agent
    amount: { count: 15, unit: percent }
    each: placed-home
    of: clauses.advance.amount
  commission-abroad:
    what: "the author pays the agent twenty parts in a hundred of each advance abroad"
    by: author
    to: agent
    amount: { count: 20, unit: percent }
    each: placed-abroad
    of: clauses.advance.amount
  refund:
    what: "the agent gives back her fifteen parts of each advance at home that was returned"
    by: agent
    to: author
    amount: { count: 15, unit: percent }
    each: returned-home
    of: clauses.advance.amount
transactions:
  first-payout:
    what: "Sam paid Noor her share of Heron's advance"
    amount: { count: "300.00", unit: XTS }
    day: 2026-11-04
    paid_by:
      - { party: author }
    settles:
      - { clause: commission, occurrence: salt-road-heron, amount: { count: "300.00", unit: XTS } }
---
Noor has represented The Salt Road since June.
```

<!-- example: beans/noor.md -->
```markdown
---
bean: noor
genos: person
title: "Noor — Sam's literary agent"
status: active
summary: "A literary agent; she places Sam's novel."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "person:noor", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
consent: { bean: agency-noor }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
---
Noor, of a small literary agency.
```

Each placing is its own agreement, with its course along the walk and the advance the house pays. Heron's offer
held for three weeks: a clause holds only **`during`** its window. The editor who read the book at Heron has given
no consent to be kept here by name, so she is written under an **opaque id** — `python3 bin/dmheld.py person`
mints it, and holds her name off git, where the garden keeps personal material — and what is written **`about`** her
names her by that id alone.

<!-- example: beans/heron-books.md -->
```markdown
---
bean: heron-books
genos: org
title: "Heron Books — a publisher"
status: active
summary: "A small publishing house; it publishes The Salt Road at home."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: org_id, value: "org:heron-books", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { external: "its shareholders" } }
responsibility: { legal: { self: true } }
---
A publisher.
```

<!-- example: beans/salt-road-signed.md -->
```markdown
---
bean: salt-road-signed
genos: document
title: "salt-road-signed — the signed publishing contract"
status: active
summary: "The contract Sam and Heron Books signed for The Salt Road, as a scanned copy."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: doc_id, value: "document:salt-road-signed", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
located_at: [ { system: unix-filesystem, openness: unknown } ]
---
Eleven pages, signed by both.
```

<!-- example: beans/salt-road-heron.md -->
```markdown
---
bean: salt-road-heron
genos: contract
title: "salt-road-heron — The Salt Road placed with Heron Books"
status: active
summary: "Heron Books publishes The Salt Road at home, for an advance."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:salt-road-heron", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  author: { who: { bean: sam }, role: author, accepted: 2026-10-20 }
  agent: { who: { bean: noor }, role: agent }
  publisher: { who: { bean: heron-books }, role: publisher, accepted: 2026-10-20 }
words: { form: written, at: { bean: salt-road-signed }, agreed: 2026-10-20 }
clauses:
  offer: { what: "Heron holds its offer open", by: publisher, to: author, during: { of: time, from: 2026-10-01, to: 2026-10-21 }, state: met }
  advance: { what: "Heron pays the author an advance on signing", by: publisher, to: author, amount: { count: "2000.00", unit: XTS }, state: met }
courses:
  home: { walk: { mapping: walk-placing } }
moves:
  - { course: home, at: now, step: submitted, by: noor }
  - { course: home, at: now, step: read, by: heron-books }
  - { course: home, at: now, step: offered, by: heron-books }
  - { course: home, at: now, step: contracted, by: sam }
---
Signed in October.
```

<!-- example: beans/p-7d2e41c9.md -->
```markdown
---
bean: p-7d2e41c9
genos: person
title: "p-7d2e41c9"
status: active
summary: "a person"
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "person:p-7d2e41c9", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
---
A person.
```

<!-- example: beans/heron-report.md -->
```markdown
---
bean: heron-report
genos: document
title: "heron-report — the editor's report on The Salt Road"
status: active
summary: "The report Heron's editor wrote on the manuscript, which Noor passed on."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: doc_id, value: "document:heron-report", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
about: [ { who: p-7d2e41c9 } ]
located_at: [ { system: unix-filesystem, openness: unknown } ]
---
Two pages; the editor asks for a shorter middle.
```

`python3 bin/dmledger.py agency-noor` reads each occurrence: Heron's placing, owed 300 XTS (15 percent of 2000 XTS),
settled 300 XTS by `first-payout`, nothing outstanding; `refund` occurs for nothing yet. `python3 bin/dmreckon.py
agency-noor:by-month` reads the month's report, each time it is asked and never stored. Who at the agency may read
what is a **grant** (*A tile workshop*, below), and the report shown as a table, or kept as a document, is a page's
(*A page of drawings*).

## A tile workshop: staff, their leave, a tiler booked on one job at a time

Sam also runs a small tile workshop. Lale works there as a tiler; she has twenty days' leave in each year, is sent
out to lay floors in customers' houses, and teaches an evening class twice a week. Two things here are the garden's
own, and a garden says its own law in `VOCAB.md`: a term for the leave a person takes, and the rule that one tiler is
never booked on two jobs over the same days — the law's `exclusive` overlay on `parties`, said by this garden and by
no other.

<!-- example-front-matter: VOCAB.md -->
```yaml
local_terms:
  - term: leave
    meaning: "the leave a person takes under an employment agreement, span by span"
    context_keys: [leave]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      attrs:
        during: { required: true, in: extent, meaning: "the days taken, from and to, each counted whole" }
        note:   { in: prose, meaning: "optional prose" }
    merge: { cardinality: multi, order: by-key }
  - { term: parties, schema: { exclusive: { extent: during, being: who, role: role } } }
```

The workshop is an organisation; its phone is written as the world dials it, `+` and the country code first
(E.164). Lale's staff number is the workshop's to give, so it is an anchor with an **`issuer`**: the same number from
another employer is another anchor, never a clash.

<!-- example: beans/tile-workshop.md -->
```markdown
---
bean: tile-workshop
genos: org
title: "tile-workshop — Sam's tile workshop"
status: active
summary: "A small workshop that lays and sells tiles, and teaches an evening class."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: org_id, value: "org:tile-workshop", class: logical, establishing: true }
    - { key: phone, value: "+15555550123", class: logical, establishing: false }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
---
Sam's workshop.
```

Her employment is an agreement, and her consent to be written here by name. Her leave is an **allowance**: a clause
with an `amount`, the window it is counted **`within`** — here each calendar year — and the reading whose members
**use** it (`used_by`). The ledger reads how much is used; nothing stores a balance to drift from the spans it was
counted from.

<!-- example: beans/lale-employment.md -->
```markdown
---
bean: lale-employment
genos: contract
title: "lale-employment — Lale tiles for the workshop"
status: active
summary: "Lale is employed as a tiler, with twenty days' leave in each year."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:lale-employment", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  employer: { who: { bean: tile-workshop }, role: employer, accepted: 2026-03-01 }
  tiler: { who: { bean: lale }, role: employee, accepted: 2026-03-01 }
words: { form: spoken, agreed: 2026-03-01 }
selections:
  leave-taken: { what: "the spans of leave Lale has taken", steps: [ { id: l, op: select, entries: "leave.*" } ] }
clauses:
  leave:
    what: "the workshop gives Lale twenty days' leave in each year"
    by: employer
    to: tiler
    amount: { count: 20, unit: day }
    within: { of: time, in: gregorian-civil, level: year, count: 1 }
    used_by: leave-taken
leave:
  summer: { during: { of: time, from: 2026-07-06, to: 2026-07-17 } }
  late-august: { during: { of: time, from: 2026-08-24, to: 2026-08-28 }, note: "her sister's wedding" }
---
Lale started in March.
```

What a person lets others read of her is **hers to grant**, on her own bean: nobody but the gardener reads what no
grant opens. Lale lets the workshop read her phone number, and nothing more of her.

<!-- example: beans/lale.md -->
```markdown
---
bean: lale
genos: person
title: "Lale — a tiler at the workshop"
status: active
summary: "A tiler; she lays floors and teaches the evening class."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "person:lale", class: logical, establishing: true }
    - { key: emp_id, value: "0007", class: logical, establishing: true, issuer: { bean: tile-workshop } }
    - { key: phone, value: "+15555550147", class: logical, establishing: false }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
consent: { bean: lale-employment }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
grants:
  workshop-rings: { act: read, positions: [ { path: phone } ], audience: { who: tile-workshop }, why: "the workshop rings her when a job moves" }
---
Lale, a tiler.
```

Each job is its own agreement with the customer, and Lale is a party to it only for the days she is on it:
`during` on her entry. Because this garden made `parties` exclusive, the gate refuses a second job that holds Lale,
as tiler, over any of the same days, and names both agreements. A job she was offered and turned down stays on record
as **`declined`**, and holds no days.

<!-- example: beans/job-kitchen-floor.md -->
```markdown
---
bean: job-kitchen-floor
genos: contract
title: "job-kitchen-floor — a kitchen floor laid"
status: active
summary: "The workshop lays a customer's kitchen floor; Lale is on it for a week."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:job-kitchen-floor", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  workshop: { who: { bean: tile-workshop }, role: contractor, accepted: 2026-09-15 }
  customer: { external: "a customer across town", role: customer, accepted: 2026-09-15 }
  tiler: { who: { bean: lale }, role: tiler, during: { of: time, from: 2026-10-05, to: 2026-10-09 } }
words: { form: spoken, agreed: 2026-09-15 }
clauses:
  price: { what: "the customer pays for the floor, tiles and labour", by: customer, to: workshop, amount: { count: "1400.00", unit: XTS }, due: 2026-10-09 }
---
Forty square metres, grey.
```

<!-- example: beans/job-bathroom-wall.md -->
```markdown
---
bean: job-bathroom-wall
genos: contract
title: "job-bathroom-wall — a bathroom wall, turned down"
status: active
summary: "A customer asked for Lale in the same week; she turned it down."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:job-bathroom-wall", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  workshop: { who: { bean: tile-workshop }, role: contractor }
  customer: { external: "a neighbour of the kitchen customer", role: customer }
  tiler: { who: { bean: lale }, role: tiler, during: { of: time, from: 2026-10-07, to: 2026-10-08 }, declined: 2026-09-18 }
words: { form: spoken, agreed: 2026-09-18 }
---
Asked for the same week; declined.
```

The evening class repeats: two evenings **`every`** week, each lasting two hours, with a **closure** on a holiday.
The offset in `due` says the zone its hours are kept in. The materials fee binds **every party of a role**
(`by_role`), however many pupils there are; a pupil who withdrew stays on record, `declined`. The kiln fee is in
force only once a firing is booked: a clause **`when`** a reading holds something, read each time and never set by
hand.

<!-- example: beans/kiln-firing-nov.md -->
```markdown
---
bean: kiln-firing-nov
genos: event
title: "kiln-firing-nov — the class's tiles fired"
status: active
summary: "The kiln is booked for the class's tiles in November."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: event_id, value: "event:kiln-firing-2026-11", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { holder: { bean: sam } } }
timing:
  start: { system: gregorian-civil, at: "2026-11-20 09:00+01:00", unit: hour }
refs:
  kiln-keeper: { bean: lale, rel: host }
---
One firing.
```

<!-- example: beans/evening-class.md -->
```markdown
---
bean: evening-class
genos: contract
title: "evening-class — tiles made by hand, two evenings a week"
status: active
summary: "Lale teaches a class on Tuesday and Thursday evenings; each pupil pays for materials and a firing."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:evening-class", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  workshop: { who: { bean: tile-workshop }, role: school, accepted: 2026-09-20 }
  teacher: { who: { bean: lale }, role: teacher, accepted: 2026-09-20 }
  pupil-a: { external: "a pupil from the street", role: pupil, accepted: 2026-09-22 }
  pupil-b: { external: "a pupil from the library's notice", role: pupil, accepted: 2026-09-23 }
  pupil-c: { external: "a pupil who moved away", role: pupil, declined: 2026-09-24 }
words: { form: spoken, agreed: 2026-09-20 }
selections:
  firing-booked: { what: "a firing of the class's tiles is booked", steps: [ { id: f, op: select, genos: event, where: [ { path: bean, is: kiln-firing-nov } ] } ] }
clauses:
  lesson:
    what: "Lale teaches the class"
    by: teacher
    to: workshop
    due: "2026-10-06T18:00+02:00"
    every: { of: time, in: iso-week, each: week, at: ["2", "4"], lasts: { of: time, measure: { count: 2, unit: hour } }, closures: [ "2026-W44-4" ] }
  materials: { what: "each pupil pays for clay and glaze", by_role: pupil, to: workshop, amount: { count: 30, unit: XTS }, due: 2026-10-06 }
  kiln-fee: { what: "each pupil pays for the firing, once one is booked", by_role: pupil, to: workshop, amount: { count: 12, unit: XTS }, when: { selection: firing-booked } }
---
Ten weeks, from October.
```

`python3 bin/dmledger.py lale-employment` reads how much of her twenty days she has used within the year ending
today — seventeen, in 2026 — and says OVER when her spans pass the allowance. `python3 bin/dmledger.py evening-class`
names the pupil who declined, binds the fees on every party whose role is pupil, holds the kiln fee in force while
its reading holds the firing, and gives the next lesson, past the closure. Take `declined` off the bathroom job and
the gate refuses it: Lale, as tiler, held twice over overlapping days, with both agreements named.

## A beekeepers' co-op: its sites, its own codes, a reading disputed

Sam keeps two hives in a co-op. The co-op tabulates its own apiary sites, valley by site, and inspects hives by its
own list of what is read at a hive. Both are the garden's own law: a **tabulated place system**, its cells in a table
the garden holds, with an **overlay** whose every row says its source; and a **scheme** held as the garden's own
extract, with its names in another language (`labels`) and how its codes relate (`relations`). Hives are no kind of
thing the standard has, so the garden adds one (`local_gene`).

<!-- example-front-matter: VOCAB.md -->
```yaml
local_gene:
  - { genos: hive, of_nature: empsychon, meaning: "a colony of bees, and the box it lives in" }
registry_additions:
  anchor_systems:
    - system: apiary-site
      dimension: place
      resolves_through: geographic
      levels: [ { level: valley }, { level: site } ]
      neighbours: counted
      cells_in: { registry: apiary-sites, take: code }
      overlay: { registry: apiary-site-changes }
      meaning: "the co-op's apiary sites, as its register tabulates them"
      pattern: '^apiary:[A-Z]+(-[0-9]+)?$'
      form_note: "`apiary:<code>` — `apiary:EAST-1`"
      example: "apiary:EAST-1"
      establishes: false
      why: "a site says roughly where, never which hive"
  knowledge_schemes:
    - scheme: hive-checks
      classifies: what a beekeeper reads of a hive at an inspection, and how
      holding: extract
      licence: CC0-1.0
      release: "the co-op's own, 2026"
      relations: hive-checks-relations
      labels: [ { language: fr, registry: hive-checks-fr, attribution: "traduction de la coopérative" } ]
      publisher: the co-op
      url: "extracts/hive-checks.tsv"
      levels: [ { level: check } ]
      neighbours: none
      sources: extracts/hive-checks.tsv
registry_files:
  - { registry: apiary-sites, file: extracts/apiary-sites.tsv, key: code }
  - { registry: apiary-site-changes, file: extracts/apiary-site-changes.tsv, key: code }
  - { registry: hive-checks, file: extracts/hive-checks.tsv, key: code }
  - { registry: hive-checks-relations, file: extracts/hive-checks-relations.tsv, key: from }
  - { registry: hive-checks-fr, file: extracts/hive-checks-fr.tsv, key: code }
```

The tables are tab-separated, one row per cell or code. An overlay row changes a cell of the register — here a site
renamed when the co-op took on the meadow beside it — and says where that came from.

<!-- example: extracts/apiary-sites.tsv -->
```tsv
code	parent	level	name	point
EAST		valley	the east valley	EPSG:4326;10.42,20.31
EAST-1	EAST	site	the orchard	EPSG:4326;10.421,20.312
EAST-2	EAST	site	the mill field	EPSG:4326;10.418,20.305
WEST		valley	the west valley	EPSG:4326;10.30,20.28
```

<!-- example: extracts/apiary-site-changes.tsv -->
```tsv
code	parent	level	name	point	source
EAST-2	EAST	site	the mill field and meadow	EPSG:4326;10.418,20.305	the co-op's meeting of May 2026
```

<!-- example: extracts/hive-checks.tsv -->
```tsv
code	parent	name
brood		the brood a colony is raising
varroa-drop		the mites that fall from a colony in a day
queen-seen		whether the queen was seen
sticky-board		a board under the hive the mites fall onto
frame-count		frames counted one by one
```

<!-- example: extracts/hive-checks-relations.tsv -->
```tsv
from	to	rel
varroa-drop	sticky-board	requires
```

<!-- example: extracts/hive-checks-fr.tsv -->
```tsv
code	name
brood	couvain
varroa-drop	chute de varroas
queen-seen	reine vue
```

The co-op is an agreement among its members, and the consent of each to be written here by name. What members may
read of one another's hives is the agreement's to **grant**: each member reads every hive's inspections, and nobody
reads where a hive stands — a **`forbidden`** grant is a ceiling that no permitted grant passes, because hives are
stolen. The co-op also takes a **stance on a code, within a place**: no member moves a colony across the border,
said as a capability forbidden on a field of work (`isced-f-2013`, livestock and crops) within a country.

<!-- example: beans/bee-coop.md -->
```markdown
---
bean: bee-coop
genos: contract
title: "bee-coop — the valley beekeepers' co-op"
status: active
summary: "Beekeepers who share an extractor, inspect by one list, and keep their sites to themselves."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:bee-coop", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  sam: { who: { bean: sam }, role: member, accepted: 2026-04-10 }
  derya: { who: { bean: derya }, role: member, accepted: 2026-04-10 }
words: { form: spoken, agreed: 2026-04-10 }
selections:
  members: { what: "the co-op's members", steps: [ { id: m, op: select, genos: person, where: [ { path: consent.bean, is: bee-coop } ] } ] }
  hives: { what: "every hive the co-op's members keep", steps: [ { id: h, op: select, genos: hive } ] }
  hive-count: { what: "how many hives there are", steps: [ { id: h, op: select, genos: hive }, { id: n, op: count, of: h } ] }
grants:
  members-read-checks: { act: read, over: hives, positions: [ { path: observations } ], audience: { selection: members }, why: "members compare their mite counts" }
  sites-closed: { act: read, over: hives, positions: [ { path: located_at } ], audience: { selection: members }, stance: forbidden, why: "a hive's site is its keeper's own: hives are stolen" }
capabilities:
  no-colonies-abroad:
    why: "a colony moved across the border can carry a mite the valley does not have"
    permission: forbidden
    code: { scheme: isced-f-2013, code: "0811" }
    within: { system: iso-3166, at: ZZ }
clauses:
  extractor-fee: { what: "each member pays for the extractor's season", by_role: member, amount: { count: 25, unit: XTS }, due: 2026-07-01, state: met }
---
Two members, for now.
```

<!-- example: beans/derya.md -->
```markdown
---
bean: derya
genos: person
title: "Derya — a beekeeper in the co-op"
status: active
summary: "A beekeeper; she keeps hives in the west valley."
nature: empsychon
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "person:derya", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
consent: { bean: bee-coop }
owned_by: { legal: { crown: agape } }
responsibility: { legal: { self: true } }
---
Derya, of the co-op.
```

A hive is where its readings live. Each reading names what was read in the co-op's scheme, how, when and by whom;
the count of mites carries its uncertainty. A colony has no number of its own — the number painted on its box is
the box's — so its identity stays `provisional`. Derya, looking at the same board the next day, **disputes** Sam's count:
a verdict is its own entry that **`answers`** the one it is on, and never edits it. Brought to the co-op, the dispute
is a **hearing**, over both entries: a ruling stands only once every side is heard.

<!-- example: beans/hive-orchard-1.md -->
```markdown
---
bean: hive-orchard-1
genos: hive
title: "hive-orchard-1 — Sam's first hive, in the orchard"
status: active
summary: "A colony Sam keeps at the orchard site."
nature: empsychon
identity:
  status: provisional
  anchors:
    - { key: serial, value: "HIVE-S1", class: hardware, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
located_at:
  - { system: apiary-site, openness: elsewhere, at: "apiary:EAST-2" }
observations:
  mites-june:
    property: { scheme: hive-checks, code: varroa-drop }
    value: { count: "14", unit: item, u: { count: "3", unit: item } }
    at: 2026-06-12
    method: { scheme: hive-checks, code: sticky-board }
    by: sam
  queen-june:
    property: { scheme: hive-checks, code: queen-seen }
    presence: present
    at: 2026-06-12
    by: sam
  second-count:
    answers: "hive-orchard-1:observations.mites-june"
    answer: disputes
    by: derya
    note: "the board had been in two days, not one"
hearings:
  mites-june:
    over: [ { path: "hive-orchard-1:observations.mites-june" }, { path: "hive-orchard-1:observations.second-count" } ]
    heard:
      - { speaker: sam, said: "I cleared the board the day before", at: 2026-06-20 }
      - { speaker: derya, said: "the date on the board says otherwise", at: 2026-06-20 }
    ruling: { by: sam, what: "count again, the board cleared by both of us", at: 2026-06-20 }
---
A strong colony.
```

`python3 bin/dmwhere.py apiary:EAST-2` reads the site within its valley, by the name the overlay gives it, with its
source. `python3
bin/dmreckon.py bee-coop:hive-count` counts the hives. Whether Derya may read a hive's inspections, or its site, is
asked of the grants, which name the grant that answers (`dmpass.may`): the inspections are open to her, the site is
forbidden. A grant that lets someone else decide what only the gardener may — a `ratify:` grant — is the gardener's
alone to give, on the gardener's own bean.

## Two candles burnt side by side: a reading that brings an order into force

Sam makes candles from the co-op's wax. A shop in town will stock them if a beeswax candle burns down no faster than
the paraffin one it sells now. So Sam lights one of each on the same evening and reads their heights every hour. A
candle is a body of matter, which the standard has no kind for; the garden adds one.

<!-- example-front-matter: VOCAB.md -->
```yaml
local_gene:
  - { genos: material, of_nature: soma, meaning: "a body of matter kept and used: a candle" }
```

Each hour's heights are a **series** on the candle's own bean, one row per hour. The ruler reads to a fifth of a
millimetre, and every height carries that uncertainty (`u`), so whatever is computed from them carries it too.

<!-- example: beans/candle-beeswax.md -->
```markdown
---
bean: candle-beeswax
genos: material
title: "candle-beeswax — a pillar candle of the co-op's wax"
status: active
summary: "A beeswax pillar candle, its height read each hour as it burns."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "CANDLE-BW-01", class: hardware, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
series:
  burn:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: hour }, from: "2026-11-01 18:00+01:00" }
    unit: hour
    holds:
      - { name: height, quantity: length, unit: millimetre, stands_for: point, between: linear, u: { count: "0.2", unit: millimetre } }
    rows: |
      height
      200
      191
      182
      173
      164
      155
---
Poured in October.
```

<!-- example: beans/candle-paraffin.md -->
```markdown
---
bean: candle-paraffin
genos: material
title: "candle-paraffin — the shop's paraffin candle"
status: active
summary: "The paraffin pillar candle the shop sells, burnt beside the beeswax one."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "CANDLE-PF-01", class: hardware, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
series:
  burn:
    grid: { of: time, in: gregorian-civil, every: { count: 1, unit: hour }, from: "2026-11-01 18:00+01:00" }
    unit: hour
    holds:
      - { name: height, quantity: length, unit: millimetre, stands_for: point, between: linear, u: { count: "0.2", unit: millimetre } }
    rows: |
      height
      200
      190
      180
      170
      160
      150
---
Bought at the shop.
```

What share of each candle burnt away is a **reading**, step by step: its first height and its last (`window`), their
difference, and that divided by where it began. The two shares, each read so, compared say whether the beeswax burnt down no faster
(`compare`, `at-most`); a comparison `equal` within a **`band`** says whether the two burnt down alike, within a
hundredth. Where the uncertainty is too wide to decide the band, the answer is NOT KNOWN — never rounded to either.
The shop's order is a clause **`when`** the first reading holds: in force because the candles say so, not because
anyone set it.

<!-- example: beans/candle-supply.md -->
```markdown
---
bean: candle-supply
genos: contract
title: "candle-supply — beeswax candles for the shop in town"
status: active
summary: "The shop orders Sam's beeswax candles if they burn down no faster than its paraffin ones."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:candle-supply", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { crown: logos } }
responsibility: { legal: { parties: true } }
parties:
  maker: { who: { bean: sam }, role: maker, accepted: 2026-10-28 }
  shop: { external: "a candle shop in town", role: buyer, accepted: 2026-10-28 }
words: { form: spoken, agreed: 2026-10-28 }
selections:
  worn-beeswax:
    what: "the share of the beeswax candle burnt away"
    steps:
      - { id: first, op: window, series: "candle-beeswax:series.burn", by: first }
      - { id: last, op: window, series: "candle-beeswax:series.burn", by: last }
      - { id: gone, op: difference, of: first, with: last }
      - { id: worn, op: divide, of: gone, with: first }
  burns-no-faster:
    what: "whether the beeswax burnt down no faster than the paraffin"
    steps:
      - { id: bw-first, op: window, series: "candle-beeswax:series.burn", by: first }
      - { id: bw-last, op: window, series: "candle-beeswax:series.burn", by: last }
      - { id: bw-gone, op: difference, of: bw-first, with: bw-last }
      - { id: bw, op: divide, of: bw-gone, with: bw-first }
      - { id: pf-first, op: window, series: "candle-paraffin:series.burn", by: first }
      - { id: pf-last, op: window, series: "candle-paraffin:series.burn", by: last }
      - { id: pf-gone, op: difference, of: pf-first, with: pf-last }
      - { id: pf, op: divide, of: pf-gone, with: pf-first }
      - { id: slower, op: compare, of: bw, with: pf, is: at-most }
  alike:
    what: "whether the two burnt down alike, within a hundredth"
    steps:
      - { id: bw-first, op: window, series: "candle-beeswax:series.burn", by: first }
      - { id: bw-last, op: window, series: "candle-beeswax:series.burn", by: last }
      - { id: bw-gone, op: difference, of: bw-first, with: bw-last }
      - { id: bw, op: divide, of: bw-gone, with: bw-first }
      - { id: pf-first, op: window, series: "candle-paraffin:series.burn", by: first }
      - { id: pf-last, op: window, series: "candle-paraffin:series.burn", by: last }
      - { id: pf-gone, op: difference, of: pf-first, with: pf-last }
      - { id: pf, op: divide, of: pf-gone, with: pf-first }
      - { id: same, op: compare, of: bw, with: pf, is: equal, band: { count: "0.01", unit: one } }
clauses:
  first-order: { what: "the shop orders forty beeswax candles", by: shop, to: maker, amount: { count: 40, unit: item }, when: { selection: burns-no-faster } }
---
Agreed at the shop, the trial to decide.
```

`python3 bin/dmreckon.py candle-supply:worn-beeswax` reads 0.225, with its uncertainty and every step it took;
`candle-supply:burns-no-faster` is true, and `candle-supply:alike` is false — two and a half hundredths apart. `python3
bin/dmledger.py candle-supply` shows the order in force while that reading holds. Nothing is written back: change a
height and the next reading says so. A reading can be asked as the garden stood at an earlier commit (`--at`, with `--moment` for the clock), and the
act that fixes one records that commit and moment as its **pin** (`pin_form`), so it can be read again. Were Ali to
burn a candle of the same wax in her own garden, Sam's garden could read her heights only at a commit she published
and granted it: `python3 bin/dmacross.py read garden-ali <bean>:<path>`, which copies nothing.

## What harm can come of: sealed before it is committed

A value that could harm a person if it left the garden — a code of a scheme marked `sensitive: special-category`, a
reading of a body — is SEALED before the commit that would carry it. `python3 bin/dmheld.py put <bean> <term> <key>`
moves the entry into a store this host keeps off git (a root of the host's bean that `keeps: special-category`),
leaves a pointer in its place, and prints the one journal line the save carries (`- held: <bean> <key> added`). The
gate refuses a commit that adds such material unsealed, naming the path and never the value, so the order is: write,
seal, save.

A value committed before it was sealed is in the history of every clone, every bundle and every hub the garden was
pushed to, and a seal made now takes none of it back. Taking it out rewrites the history, which is the gardener's
decision and the work of everyone who holds a copy:

1. Seal it, and save: the tree no longer carries it.
2. In one clone, rewrite every commit that held it — `git filter-repo --replace-text <a file of the values>` (a tool
   of its own, not part of git) does. Every commit from the first that held it gets a new id.
3. Replace every other copy: push the rewritten history to the hub with `--force`, and have each other clone deleted
   and cloned again. A copy that is not replaced still holds the value, and a merge from it brings it back.
4. Say what was done in the journal, by path and never by value.

## A value the vocabulary does not have yet

The standard list of operating systems has no entry for the NAS's vendor OS. Do not bend the bean to fit:
add the value **for this garden** in `VOCAB.md`, and propose it upstream if others will need it
(`CONTRIBUTING.md`). Operating systems are a **registry**, and `os` reads its values from it, so the value is
added as a row — once, with everything a row carries — and the garden accounts only for the row it added.

Add this inside `VOCAB.md`'s front matter:

<!-- example-front-matter: VOCAB.md -->
```yaml
registry_additions:
  operating_systems:
    - { os: nas-os, family: unix, path_grammar: unix-filesystem, meaning: "A vendor's Linux-based NAS operating system." }
```

Then the NAS bean can say `os: nas-os`. **Commit the two together:** a value the garden adds must be used
by a bean, so the vocabulary change on its own is refused ("declared but NO bean occupies it"). The one
commit is one logical change — adding the thing and the value that describes it. Editing `VOCAB.md` changes the
law, so the journal entry that goes with it says RULE-CHANGE, and the gate refuses one that does not. If a later
daftar release adds the same value to the standard, the gate tells you to delete your local copy.

A term that carries its own closed list — `python3 bin/dmrules.py` shows which — takes the value with
`schema: { values_add: [...] }` in a `local_terms` entry instead; on a term that reads a registry, `values_add`
adds nothing. The gate's refusal of an unknown value says which of the two the term needs. (A germinated
`VOCAB.md` already has an empty `local_terms: []` line; replace it rather than adding a second — the gate
refuses a key written twice.)

## A kind of fact the standard has no term for

Keep it in `details:` until it recurs. When it does, give it a term **in this garden** — a term is data, so
the gate enforces it the moment it is written, with no code anywhere. Each attribute says ONE thing: what it
is a position `in:`, whether it is `required`, and what it `meaning`s. `python3 bin/dmrules.py` lists what
`in:` may say (`schema_language.attr_domains`): a closed list, a registry, an aspect, a value type, a pattern,
`extent`, `ref` — or `prose`, for a reason or a remark, which is deliberately not a position.

<!-- example-term: VOCAB.md -->
```yaml
local_terms:
  - term: rental
    meaning: "what a rented machine is rented from, and when the rent next falls due"
    context_keys: [rental]
    schema:
      shape: mapping
      attrs:
        provider: { required: true, in: prose,              meaning: "who it is rented from" }
        renews:   { required: true, in: { type: iso_date }, meaning: "ABSOLUTE date the next payment is due" }
        note:     { in: prose,                              meaning: "optional remark" }
    merge: { cardinality: single, order: none }
```

Then a bean can carry `rental: { provider: "a hosting company", renews: 2027-01-15 }`, and a bean that writes
`rental: { provider: "x", renews: "next January" }` — or adds a key the term does not declare — is refused. An
attribute whose `in:` is a closed list declares POSITIONS, and the gate will ask that each be used by a bean or
declared vacant with a reason. If the term proves general, propose it (`CONTRIBUTING.md`).

## A page of drawings (`view` profile)

A page draws what the garden keeps — a procedure, a machine — at four lenses: a story for a newcomer, the drawing
itself, its vital sign for whoever is on call, and a card of each part's own facts. It is the opt-in **`view`
profile**, and its asset, `assets/view/`, arrives with it. Opting in is a RULE-CHANGE, made by one command that writes
the profile in VOCAB.md, brings the asset, journals it and runs the gate (a new garden takes `--profile view` from
`seed/germinate.py` instead):

    python3 bin/dmupgrade.py <the release GARDEN.md records> --extend view

The drawings are the garden's own code: copy `assets/view/templates/drawings.py` to `drawings/bakery.py` and draw with
the kit it imports. The page is one bean; what it draws is its `views`, one entry per drawing under the key the
drawing module draws it by — a machine, or a procedure (a mapping with `steps`). A machine the page draws:

<!-- view-example: beans/oven-a.md -->
```markdown
---
bean: oven-a
genos: host
title: "The bakery's first oven"
status: active
summary: "The oven that bakes the morning's orders."
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "SN-OVEN-0042", class: hardware, establishing: true }
provenance: { src: observed, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
---
The first oven.
```

And the page. A drawing with no monitor behind it draws the health chain, each part it cannot see said so; a
monitor's values, and the other shapes, are in `assets/view/README.md`:

<!-- view-example: beans/bakery-page.md -->
```markdown
---
bean: bakery-page
genos: service
title: "The bakery, drawn"
status: active
summary: "The page of drawings of the bakery's orders."
nature: lekton
identity:
  status: confirmed
  anchors:
    - { key: service_id, value: "service:bakery-page", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: now }
owned_by: { legal: { owner: { bean: sam } } }
responsibility: { legal: { holder: { bean: sam } } }
view:
  drawings: file:drawings/bakery.py
  reference:
    - { being: oven-a, what: "bakes the orders" }
views:
  orders:
    draws: { bean: oven-a }
    purpose: "Every order in stock is baked the same morning."
    outcome: "The morning's orders leave the oven by nine."
    stages:
      - { label: "Check the stock", doer: "whoever takes the order" }
      - { label: "Bake", doer: "oven-a", beings: [ { being: oven-a } ] }
      - { label: "Hand it over", doer: "the counter" }
    questions:
      - { lens: orient, ask: "How does an order become bread?" }
      - { lens: operate, ask: "Is the oven baking?" }
    actions:
      - { element: preheat, tool: preheat, confirm: "Preheat oven-a now?" }
    archetype: health-chain
    blind:
      - { what: "the oven's temperature", why: "no monitor reads it yet" }
---
The bakery's page of drawings.
```

Then `python3 assets/view/bin/dmview.py check`, and `python3 assets/view/bin/dmview.py report --out map/bakery.html`
for the page itself. A button (`actions`) asks the host for a tool by name; only the host's own configuration makes a
tool run anything.

## Say what a thing is, in the world's shared terms (`knowledge` profile)

Opt in with `extends_profiles: [knowledge]` in VOCAB.md. Then:

```yaml
# a third-party product that IS a technology: anchor it, so every garden's "samba" is one object
identity: { status: confirmed, anchors: [ { key: technology, value: samba, class: logical, establishing: true } ] }
# anything may say what it stands on
knowledge:
  - { scheme: technology,   code: samba, rel: uses }
  - { scheme: isced-f-2013, code: "0612", rel: draws_on, topic: "network file sharing" }
  - { scheme: isco-08,      code: "2522", rel: classified_as }
```

`python3 bin/dmknowledge.py find <word>` finds a code; `show <scheme> <code>` shows its ancestry and, for a
technology, its official documentation.
