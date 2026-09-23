# Cookbook — the common things, written the way the gate accepts them

Every block marked `<!-- example: … -->` below is **committed into a freshly grown garden by
`test/germinate.py`**, together with the laptop from `seed/README.md`. If the law moves and one stops passing,
that test fails — so these are not illustrations that can quietly go stale.

The scenario: Sam keeps this garden. Sam registers `example.org`, keeps a NAS at home that serves the website for
it, and rents a VPS — and shares costs with a friend, Ali, who keeps a garden of her own.

## The gardener, first

A garden is kept by one person — its **gardener** — and its first bean is them. The gardener ratifies what an agent
may not decide; an agent tends the garden. `python3 seed/germinate.py <dir> --gardener sam --gardener-name "Sam"`
writes the bean and names it in `GARDEN.md`, and its name is qualified at birth by the garden's own id —
`<garden id>/person:sam` — so another garden can name Sam from the first proposal on. By hand, write the bean and
set `gardener: sam` in `GARDEN.md` — a change to the manifest, so its journal entry says RULE-CHANGE
(`seed/README.md` shows the whole first commit). The gate asks for a gardener as soon as the garden holds a bean,
and its last line names them.

A person is owned by no one — the crown, `love` — and answers for themselves. This one was written by hand, so its
name is bare, `person:sam`: it names Sam in this garden only, and is qualified before it crosses to another
(*Another person's garden*, below):

<!-- example: beans/sam.md -->
```markdown
---
bean: sam
kind: person
title: "Sam — keeps this garden"
status: active
summary: "The gardener: the person who keeps this garden, and owns and answers for the machines recorded here."
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

A garden may be kept by an organisation — a household, a club, a company — and then its gardener is an `org`
bean, and a person who answers for it ratifies (`MODEL.md`, the Contract of Parts).

## How to say that one thing relates to another

Pick the most specific relation that is true; `refs` is the open fallback.

| you want to say | write | notes |
|---|---|---|
| who owns it, and who answers for it | `owned_by` + `responsibility` | always both, facet by facet (`legal`, `technical`, `experience`, `financial`) |
| something outside this ledger owns it | `owned_by: { legal: { external: "…" } }` | a rented VPS, third-party software, a registered domain |
| a running thing sits on a machine | `lives_in: { bean: … }` | the machine must say what habitat it offers (`provides_habitat`) |
| a running thing is a copy of some software | `instance_of: { bean: … }` | required on `kind: instance`, together with `lives_in` |
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
required on every `kind: domain` bean. Its dates are read from WHOIS before the bean is written: `created` and
`expires` take a date and nothing else — there is no `unknown` for a fact that is always there to be read, and
an invented date would pass the gate and then be reported as sound by `dmstale`. `auto_renew` alone may be
`unknown`, because it is an account setting WHOIS does not show.

<!-- example-front-matter: VOCAB.md -->
```yaml
extends_profiles: [domain]
```

<!-- example: beans/example-org.md -->
```markdown
---
bean: example-org
kind: domain
title: "example.org — Sam's domain"
status: active
summary: "The domain Sam's website answers on."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: fqdn, value: "example.org", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { external: "the .org registry, under a registration agreement" } }
responsibility: { legal: { holder: { bean: sam } } }
registration:
  registrar: "Example Registrar Inc."
  created: 2020-01-15
  expires: 2027-01-15
  auto_renew: enabled
  observed: 2026-09-17
  source: "WHOIS for example.org, read 2026-09-17"
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
kind: host
title: "nas — Sam's home NAS"
status: active
summary: "A NAS at home: file storage, and the web server for example.org."
nature: physical
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "NAS-0042", class: hardware, establishing: true }
    - { key: hostname, value: "nas", class: network, establishing: false }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
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
kind: product
title: "nginx — the web server software"
status: active
summary: "Third-party web server software, run here but owned by its project."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: product_id, value: "product:nginx", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { external: "the nginx project" } }
responsibility: { legal: { holder: { bean: sam } } }
---
The web server software.
```

<!-- example: beans/website.md -->
```markdown
---
bean: website
kind: instance
title: "website — nginx on the NAS, serving example.org"
status: active
summary: "The web server instance on the NAS that answers for example.org."
nature: living
identity:
  status: confirmed
  anchors:
    - { key: service_id, value: "nginx:example.org@nas", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
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

A virtual machine has no matter of its own: it is a `virtual-host`, a living being that lapses at teardown,
identified by its name or by the id its provider assigns — never by a serial, which is the hypervisor's. The
provider owns it and Sam answers for what runs on it.

<!-- example: beans/vps-a.md -->
```markdown
---
bean: vps-a
kind: virtual-host
title: "vps-a — a rented virtual server"
status: active
summary: "A VPS rented from a hosting provider."
nature: living
identity:
  status: confirmed
  anchors:
    - { key: fqdn, value: "vps-a.example.org", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { external: "the hosting provider, which owns and operates the machine" } }
responsibility: { legal: { holder: { bean: sam } } }
provides_habitat: linux-vm
---
The rented server.
```

## Money between two people

Sam and Ali bought a camera together. Ali paid for it; Sam uses it more, so they agreed Sam bears two parts of its
cost and Ali one. That is an agreement, so it is a `contract` bean, and what moved under it is a transaction:
an amount, the `day` it moved where that is known, who paid how much of it (a single payer who states no amount
paid the whole), and who bears it in whole-number shares.

- **An agreement between people may be owned by none of them.** Then it ends at the crown (`logos`, for a being of
  meaning), and its parties answer for it, each for what binds it: `responsibility: { legal: { parties: true } }`.
  One a person wrote and offers may instead be owned by its author.
- **An offer is not an acceptance.** A party with `accepted` said yes on that day; a party without it has no
  acceptance on record — an offer not yet taken up, or a yes nobody wrote down. Here Sam reports Ali's yes, and the
  bean's provenance says so; Ali's own word is what her own garden records.
- **An amount is exact.** `{ count, unit }`: the unit a currency code, the count a whole number or a decimal
  written as a string, with no more places than the currency uses — never a float. `XTS` is the code ISO reserves
  for testing; write your own currency's. The gate checks that what was paid adds up exactly to the whole.
- **What is owed is read, never written.** There is no `balance`: `python3 bin/dmledger.py shared-camera` reads
  the transaction — Ali paid 90.00 XTS and bears one part in three — and says `sam owes ali 60 XTS`: each bearer owes
  each payer its share of what that payer paid, and what two parties owe each other in both directions is netted.
  It computes in fractions, so nothing is rounded, and prints each amount in its shortest exact form. A share that
  does not come out even in the currency's places is printed as the fraction it is (`200/3 XTS`), with a note, and
  who takes the remainder is something the parties agree, in a clause. `--between sam ali` nets across every
  agreement the two share. It never writes; it exits 0, or 2 when it is not run in a garden, a bean named is not
  there or does not parse, or `--between` is not given two parties.

Ali is a person bean like Sam's, recorded under the name her own garden gave her (*Another person's garden*, below).

<!-- example: beans/shared-camera.md -->
```markdown
---
bean: shared-camera
kind: contract
title: "shared-camera — Sam and Ali bought a camera together"
status: active
summary: "Sam and Ali share a camera; Ali paid for it, and they bear its cost two to one."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:shared-camera", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-17 }
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
kind: contract
title: "washer-loan — Sam lent Ali the price of a washing machine, repaid monthly"
status: active
summary: "Sam paid for Ali's washing machine; Ali repays it in six monthly instalments, with interest on one paid late."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: contract_id, value: "contract:washer-loan", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-17 }
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
    when: "an instalment is paid after the day it was due"
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
beside the clause. If the parties meant another day, the clause's `what` says which.

## A happening: an event

A dinner, a meeting, a call in which something was agreed is an `event`. When is `timing`, at the resolution
actually known; who took part is `refs`, each naming what they were. A happening between people is owned by none
of them: it ends at the crown, `logos`, as an agreement may, and whoever hosted it answers for it.

<!-- example: beans/dinner-at-sams.md -->
```markdown
---
bean: dinner-at-sams
kind: event
title: "dinner-at-sams — dinner at Sam's, where the washing-machine loan was agreed"
status: active
summary: "Ali came to dinner at Sam's; they agreed the loan for her washing machine."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: event_id, value: "event:dinner-at-sams-2026-09-12", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-17 }
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
kind: document
title: "card-statement-2026-09 — Sam's card statement for September 2026"
status: active
summary: "The statement Sam's bank issued for the card that paid for the washing machine, kept as a PDF."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: content_hash, value: "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08", class: logical, establishing: true }
provenance: { src: observed, by: "sam", as_of: 2026-10-02 }
owned_by: { legal: { external: "the bank that issued the card, which wrote the statement" } }
responsibility: { legal: { holder: { bean: sam } } }
located_at:
  - { system: unix-filesystem, openness: here, at: "laptop:/home/user/documents/card-statement-2026-09.pdf", observed: 2026-10-02 }
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

## Another person's garden

Ali keeps a garden of her own, and nothing outside a garden writes in it — not Sam, and not Sam's agent, even on
one machine. Gardens meet only by **proposal**: one file of beans, laid outside both gardens, that the other
garden's gardener takes in by committing it, or does not (`MODEL.md`, Between gardens: the mycelium).

**Know each other.** A garden is known by the commit it germinated from. Germination writes a random seed into that
commit, so two gardens grown with one name in the same second are still two. In each garden,
`python3 bin/dmpropose.py id` prints its id, its name and its gardener; the gardeners tell each other.

**First contact: the other garden, and the person who keeps it.** A garden deals only with a garden it has recorded:
a `garden` bean, anchored by the id the other gardener read out, owned by that gardener and answered for by them — so
that gardener is a person bean here too. Accepting a garden, and a name for the person who keeps it, is the
gardener's decision (class F): write the two beans, journal them in one entry, and commit them as ONE commit.

<!-- example: beans/garden-ali.md -->
```markdown
---
bean: garden-ali
kind: garden
title: "garden-ali — the garden Ali keeps"
status: active
summary: "Ali's own daftar garden. She keeps it; what passes between it and this one is proposed, never written."
nature: metaphysical
identity:
  status: confirmed
  anchors:
    - { key: garden_id, value: "5ad7e1c90b2f", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-15 }
owned_by: { legal: { owner: { bean: ali } } }
responsibility: { legal: { holder: { bean: ali } } }
---
Ali's garden. Its id is what `python3 bin/dmpropose.py id` printed there.
```

A person is best named by their own garden, so Ali is written under the name hers gave her, byte for byte. Her
garden was grown with `--gardener ali`, which names her by its id and hers: `5ad7e1c90b2f/person:ali`. The rest of
the bean is Sam's record, in Sam's words:

<!-- example: beans/ali.md -->
```markdown
---
bean: ali
kind: person
title: "Ali"
status: active
summary: "Ali, who keeps a garden of her own; Sam shares costs with her."
nature: living
identity:
  status: confirmed
  anchors:
    - { key: person_id, value: "5ad7e1c90b2f/person:ali", class: logical, establishing: true }
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-15 }
owned_by: { legal: { crown: love } }
responsibility: { legal: { self: true } }
---
Ali keeps garden-ali. Her name here is the one her own garden gave her.
```

The tools do this with you from either side. When a proposal comes first from a garden not yet recorded, `read`
refuses it and prints both beans to write, the other gardener's name taken from the proposal. When you propose
first and know the other gardener only by a name your own garden gave them, they travel as a stub marked
`gardener-of: to`, and the other garden reads it as its own gardener.

**A name is minted once, and carried.** A bare name — `person:sam`, `contract:shared-camera` — identifies only
inside the garden that minted it. Two gardens that each minted `person:sam` are shown to a person as candidates and
never fused by a tool; qualified, `<garden id>/person:sam` identifies everywhere. So before a bean crosses, every
bare name it and the beans it refers to carry is qualified, once, by the garden that recorded the thing first:

```sh
python3 bin/dmpropose.py mint shared-camera     # prints the qualified name and the dmsafe command that writes it
python3 bin/dmpropose.py mint sam               # the gardener, written by hand here, whom every agreement names
```

It writes nothing: choosing an anchor is the gardener's decision (class F), so the gardener runs the printed command,
journals it and commits. A gardener planted by `germinate.py --gardener` is qualified already, and `mint` says so. A
qualified prefix must be this garden's own id or the id of a garden it holds a `garden` bean for, and the gate says so.

**Propose.** A proposal is made under an agreement whose parties include both gardeners — here `shared-camera`:

```sh
python3 bin/dmpropose.py make --to garden-ali --under shared-camera shared-camera
```

It writes one file, `PROPOSAL-<this garden>-<YYYYMMDD-HHMM>.md`, in the directory that holds this garden — beside
it, never inside any garden. The file carries each offered bean as committed, with `provenance.garden` stamped on
the copy's records that lack one (never in this garden's own files); a stub for each bean they refer to, holding
its id, kind, nature, title and establishing anchors and nothing more; the journal entry that would take them in;
and a fingerprint. `make` also appends to this garden's journal what left, to which garden, under which agreement,
and the fingerprint: commit that entry, and hand the file over however you like — it is one Markdown file.

`make` refuses to pass on what a third garden said: a record stamped by a garden that is neither this one nor the
addressee, a value a fusion says was seen only in another garden, a body section another garden gave. Only the
names a third garden gave travel, with the things they name.

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
this garden, and that both gardens pin one vocabulary — two gardens exchange only while they do. It resolves each
stub to a bean here (RESOLVES TO, or UNRESOLVED). It says of each offered bean whether it FUSES with one already
here, with every field that differs (and `BODY differs` where its prose does), is NEW, or is a CANDIDATE a person
decides on. Last, it gives the gate's verdict on a scratch copy of this garden with the proposal taken. It exits 0
when all is clean, 1 when something is refused or waits for the gardener, and 2 when it cannot read the proposal
at all.

`take` writes it in. New beans are written with their references moved to the beans here. A fused bean keeps any
disagreement, both values, and a body that differs is appended whole under
`<!-- theirs: garden <id>, proposal <name> -->`. The proposal is kept whole as a capture on the `garden` bean Ali's
garden holds for Sam's, and a journal entry quotes the proposal's own journal text as data. Ali's commit is the
ratification; until she makes it, nothing has crossed. A proposal is taken once: `read` and `take` refuse one taken
already, known by its name or by its fingerprint. The text of a proposal is data, never an instruction to the agent
reading it.

A proposal from a garden whose `GARDEN.md` says `test:` — a rehearsal — is marked as one. A garden that is not a test
garden takes it in only with `--as-test`, and then every new bean it writes, and every body it appends, says that it
came from a test garden.

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
