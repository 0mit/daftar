# Cookbook — the common things, written the way the gate accepts them

Every block marked `<!-- example: … -->` below is **committed into a freshly grown garden by
`test/germinate.py`**, after the laptop from `seed/README.md`, one recipe at a time and in the order of this page —
so the page can be followed from the top, each recipe needing only what came before it. If the law moves and one
stops passing, that test fails — so these are not illustrations that can quietly go stale.

The scenario: Sam keeps this garden. Sam registers `example.org`, keeps a NAS at home that serves the website for
it, and rents a VPS — and shares costs with a friend, Ali, who keeps a garden of her own.

Each recipe's bean is committed with its journal entry, written through `bin/dmjournal.py` (`seed/README.md` shows
how). Every command here is written `python3`; on Windows it is `python`.

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
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-17 }
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
`unknown`, because it is an account setting WHOIS does not show.

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
genos: product
title: "nginx — the web server software"
status: active
summary: "Third-party web server software, run here but owned by its project."
nature: lekton
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
genos: instance
title: "website — nginx on the NAS, serving example.org"
status: active
summary: "The web server instance on the NAS that answers for example.org."
nature: empsychon
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
provenance: { src: observed, by: "sam", as_of: 2026-09-17 }
owned_by: { legal: { external: "the hosting provider, which owns and operates the machine" } }
responsibility: { legal: { holder: { bean: sam } } }
provides_habitat: linux-vm
---
The rented server.
```

## Another person, and the garden she keeps

Ali keeps a garden of her own, and nothing outside a garden writes in it — not Sam, and not Sam's agent, even on
one machine. Gardens meet only by **proposal**: one file of beans, laid outside both gardens, that the other
garden's gardener takes in by committing it, or does not (`MODEL.md`, Between gardens: the mycelium).

Sam shares costs with Ali, and lent her money over a dinner — the recipes after this one — so she is recorded
before them, and so is her garden: the record of a person who keeps a garden of her own names her the way her
garden does.

**Know each other.** A garden is known by the commit it germinated from. Germination writes a random seed into that
commit, so two gardens grown with one name in the same second are still two. In each garden,
`python3 bin/dmpropose.py id` prints its id, its name and its gardener; the gardeners tell each other.

**First contact: the other garden, and who keeps it.** A garden deals only with a garden it has recorded:
a `garden` bean, anchored by the id the other gardener read out, owned by that gardener and answered for by them — so
that gardener is a person (or organisation) bean here too. Accepting a garden, and a name for whoever keeps it, is the
gardener's decision (class F): write the two beans, journal them in one entry, and commit them as ONE commit.

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
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-15 }
owned_by: { legal: { owner: { bean: ali } } }
responsibility: { legal: { holder: { bean: ali } } }
---
Ali's garden. Its id is what `python3 bin/dmpropose.py id` printed there.
```

`123456789abc` stands for Ali's garden's id: write the twelve digits `python3 bin/dmpropose.py id` printed there,
here and in her name below. An id copied from this page passes the gate, and the first proposal then goes to a
garden that does not exist.

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
provenance: { src: asserted-by-human, by: "sam", as_of: 2026-09-15 }
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
genos: contract
title: "washer-loan — Sam lent Ali the price of a washing machine, repaid monthly"
status: active
summary: "Sam paid for Ali's washing machine; Ali repays it in six monthly instalments, with interest on one paid late."
nature: lekton
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

`content_hash` is `sha256:` and the file's SHA-256 in lowercase hexadecimal: `sha256sum <file>` prints it on Linux,
`shasum -a 256 <file>` on macOS, and in PowerShell
`"sha256:" + (Get-FileHash -Algorithm SHA256 <file>).Hash.ToLower()` — `Get-FileHash` prints capitals, and the gate
refuses them.

On Windows the copy has a Windows path, in the `windows-filesystem` system. Write it in single quotes: inside double
quotes YAML reads a backslash as the start of an escape, and `"C:\Users…"` is refused before the gate reads it.

<!-- example-located-at: beans/card-statement-2026-09.md -->
```yaml
located_at:
  - { system: windows-filesystem, openness: here, at: 'laptop:C:\Users\sam\Documents\card-statement-2026-09.pdf', observed: 2026-10-02 }
```

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

It writes nothing: choosing an anchor is the gardener's decision (class F), so the gardener runs the printed command,
journals it and commits — `git add -A`, then `git commit`, two commands. A gardener planted by
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
after the take. In Ali's garden the entry reads:

<!-- example-entry: beans/shared-camera.md parties.ali -->
```yaml
  ali: { who: { bean: ali }, accepted: 2026-09-10, provenance: { src: asserted-by-human, by: "ali", as_of: 2026-09-20 } }
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
