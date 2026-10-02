# Cookbook — the common things, written the way the gate accepts them

Every block marked `<!-- example: … -->` below is **committed into a freshly grown garden** by a suite, after the
first beans of `README.md`, one recipe at a time and in the order of this page — so the page can be followed from the
top, each recipe needing only what came before it. A block marked `<!-- example-check: … -->` is judged by the gate as
if it were added to the bean it names, and not committed. If the law moves and one stops passing, the suite fails — so
these are not illustrations that can quietly go stale.

The scenario: Sam keeps this garden. Sam registers `example.org`, keeps a NAS at home that serves the website for it,
and rents a VPS — and shares costs with a friend, Ali, who keeps a garden of her own.

Every fact is a statement: a verb and its roles, one line, `- <verb>: { <role>: <filler>, … }`. Each bean's first
statement says who knows the rest — Sam `say`s what Sam was told or decided, Sam `read`s what Sam looked at — and its
`at` is `now`: the save writes the moment of its journal entry in its place, the clock's and never typed. Each recipe's
beans are saved with their entry in one command, `python3 bin/save.py "<who>" "<what changed>" --body "- action:
…"` (`README.md` shows it). Every command here is written `python3`; on Windows it is `python`.

## How to say that one thing relates to another

Every relation is a statement of a verb the law has. Pick the verb that is true; a relation no verb says is proposed as
a new verb, never forced into one that nearly fits.

| you want to say | write | notes |
|---|---|---|
| whose it is | `own: { by: <owner>, of: self }` | one owner; or `from` the parent it is owned through; a person, and an agreement or a happening may be owned by the crown, `theone` |
| who answers for it | `answer: { by: …, of: self, as: <mode> }` | `as` law, keeping, meeting or paying; before the law the owner answers, and that is not written |
| through whom it came to be | `come: { by: self, through: [ … ] }` | a person, the one it was born of, or `{ someone: person, at: <maker> }` — never demanded |
| from whom it came to us | `acquire: { of: self, from: …, as: bought, at: … }` | bought, rented, given, lent, inherited |
| where it is, or what it runs on | `be: { by: self, at: …, as: <placement> }` | `at` a position or a being; `as` place, order, presence, habitat, location |
| that it runs some software | `run: { by: self, of: <the software> }` | a machine runs an operating system; an instance runs its program |
| that it needs another thing | `need: { by: self, of: [ … ] }` | how badly is a position on the necessity square |
| what it does | `do: { by: self, as: <job> }` | one statement per job |
| that it uses a thing, a technology, a field | `use: { by: self, of: … }` | a being, a statement, or a code of the knowledge tree |
| that it is part of another | `part: { by: self, of: … }` | never above what its whole is made of |
| people agreed on something | a `contract` bean: an `agree` by each party, its clauses on the permission square, `pay` and `bear` | may be owned by the crown, and then each party answers |
| who took part in a happening | `attend: { by: …, of: self }` on the `event` | owned by the crown, answered for by its host |

**Names say what a being IS**, so two gardens recognise the same thing. A name is a statement, `name: { by:
<namespace>, of: self, as: "<the name>" }`, and a name its namespace gives **once** establishes an identity: a machine's
serial, by its maker; a MAC, by `ieee-eui48`; a domain or a rented machine you cannot touch, by `dns`; a document, by
`sha-256` of its bytes; another garden, by `garden-id`. A hostname is only a name someone gave it, and moves. A
person's name in this garden is their bean: a name is written for them only where it is to cross, by `garden`, or where
a registry gave them one. The standards' namespaces are the core's (`core/law/namespaces.yaml`); a maker's or an
employer's is a row of the garden's `VOCAB.md`.

**A being named in what you were told is a bean; one nobody named is `{ someone: <kind> }`**, reached `at` what is
known of it. The registry that owns a domain, the project that writes a program, the agent's assistant: each is a being,
and an owner outside this ledger is still one.

## A registered domain

A domain is registered for a term, not owned outright: the registry owns the name, and the person who registered it
answers for it. Its registration is an agreement, and is written as one: the registrant holds the name through a
registrar until a day on which it lapses unless it is renewed. `renew` is the domain profile's verb. Read the days
before the agreement is written, from RDAP or WHOIS: the day the registration began is the registrant's `agree`, and the
day it lapses is when its renewal falls due. Neither takes `unknown`, for a fact that is always there to be read: an
invented day would pass the gate and then be reported as sound. Whether the registrar renews unasked is an account
setting the registry does not show, and may be left out. How far ahead a warning comes is the clause's `notice`, in its
form (`clause`): ninety days before a name lapses, read by `python3 bin/daftar.py stale`.

<!-- example: beans/org-registry.md -->
```markdown
---
bean: org-registry
kind: org
title: "the .org registry"
summary: "The registry that keeps the .org names."
statements:
  - say: { by: sam, at: now }
---
The .org registry.
```

<!-- example: beans/example-registrar.md -->
```markdown
---
bean: example-registrar
kind: org
title: "Example Registrar Inc."
summary: "The registrar through which Sam holds example.org."
statements:
  - say: { by: sam, at: now }
---
A registrar.
```

<!-- example: beans/example-org.md -->
```markdown
---
bean: example-org
kind: domain
title: "example.org — Sam's domain"
summary: "The domain Sam's website answers on."
statements:
  - read:   { by: sam, at: now }
  - name:   { by: dns, of: self, as: example.org }
  - own:    { by: org-registry, of: self, through: "example-org-registration#registered", note: "the .org registry, under a registration agreement" }
  - answer: { by: sam, of: self, as: law }
---
Sam's domain.
```

<!-- example: beans/example-org-registration.md -->
```markdown
---
bean: example-org-registration
kind: contract
title: "the registration of example.org"
summary: "example.org is held through Example Registrar Inc. until 2027-01-15, when it lapses unless renewed."
statements:
  - read:       { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - answer:     { by: example-registrar, of: self, as: law }
  - agree:      { id: registered, by: sam, of: example-org, through: written, as: registrant, at: 2020-01-15 }
  - agree:      { by: example-registrar, of: example-org, through: written, as: registrar, note: "the registrar's registration agreement" }
  - renew:      { id: renewal, by: sam, of: example-org, at: 2027-01-15 }
  - obligatory: { id: renew-or-lapse, of: renewal, through: self, note: "renew the registration, or the name lapses with its DNS and its mail", clause: { due: 2027-01-15, notice: { count: "90", unit: d } } }
  - renew:      { id: auto-renewal, by: example-registrar, of: example-org, at: 2027-01-15 }
  - permitted:  { of: auto-renewal, through: self, note: "auto-renew is enabled in the registrar's account" }
---
Read from WHOIS for example.org.
```

## A machine at home that other things run on

A machine `do`es its jobs, one statement each, and what runs on it says so with `be … as: habitat`. Its serial is the
name its maker gave it; who the maker is was not said, so the namespace is `unknown`, and the serial establishes nothing
until it is. What habitat a machine offers has no verb yet, and is kept in `details`.

<!-- example: beans/nas.md -->
```markdown
---
bean: nas
kind: host
title: "nas — Sam's home NAS"
summary: "A NAS at home: file storage, and the web server for example.org."
statements:
  - read:   { by: sam, at: now }
  - name:   { by: unknown, of: self, as: NAS-0042, note: "the serial on its label; its maker is not recorded" }
  - name:   { by: sam, of: self, as: nas }
  - own:    { by: sam, of: self }
  - answer: { by: sam, of: self, as: keeping }
  - do:     { by: self, as: file-server }
  - do:     { by: self, as: web }
details:
  provides_habitat: linux-baremetal
---
The NAS.
```

## Third-party software, and a running copy of it that serves the website

The software is a `product` owned by its authors; the running copy is an `instance` that `run`s it, `be`s on the NAS as
its habitat, and is Sam's. It `use`s the domain it serves.

<!-- example: beans/nginx-project.md -->
```markdown
---
bean: nginx-project
kind: org
title: "the nginx project"
summary: "The project that writes and owns the nginx web server."
statements:
  - say: { by: sam, at: now }
---
The nginx project.
```

<!-- example: beans/nginx.md -->
```markdown
---
bean: nginx
kind: product
title: "nginx — the web server software"
summary: "Third-party web server software, run here but owned by its project."
statements:
  - read:     { by: sam, at: now }
  - own:      { by: nginx-project, of: self }
  - answer:   { by: sam, of: self, as: law }
  - classify: { of: self, as: "technology:nginx" }
---
The web server software.
```

<!-- example: beans/website.md -->
```markdown
---
bean: website
kind: instance
title: "website — nginx on the NAS, serving example.org"
summary: "The web server instance on the NAS that answers for example.org."
statements:
  - read: { by: sam, at: now }
  - name: { by: sam, of: self, as: "nginx:example.org@nas" }
  - run:  { by: self, of: nginx }
  - be:   { by: self, at: nas, as: habitat }
  - own:  { by: sam, of: self }
  - use:  { by: self, of: example-org, note: "it serves the domain" }
---
The website.
```

## A rented VPS

A virtual machine has no matter of its own: it is a `virtual-host`, a sayable placed by its habitat, taking no room in
space. It is named by its name in DNS or by the id its provider gives it — never by a serial, which is the hypervisor's.
The provider, whom nobody named, owns it, and Sam answers for what runs on it.

<!-- example: beans/vps-a.md -->
```markdown
---
bean: vps-a
kind: virtual-host
title: "vps-a — a rented virtual server"
summary: "A VPS rented from a hosting provider."
statements:
  - read:    { by: sam, at: now }
  - name:    { by: dns, of: self, as: vps-a.example.org }
  - own:     { by: { someone: org }, of: self, note: "the hosting provider, which owns and operates the machine" }
  - answer:  { by: sam, of: self, as: law }
  - acquire: { of: self, from: { someone: org }, as: rented }
details:
  provides_habitat: linux-vm
---
The rented server.
```

## Another person, and the garden she keeps

Ali keeps a garden of her own. Recording another garden, and its gardener, is the gardener's decision (class F), made in
one commit. The garden is named by its id, which Ali read out from it (`python3 bin/propose.py id` prints it there);
Ali is named as her own garden names her. She agreed to be kept here by name: her yes is her `agree`, and Sam, who
reports it, knows it.

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
it; it is owned by the crown, and whoever hosted it answers for it.

<!-- example: beans/dinner-at-sams.md -->
```markdown
---
bean: dinner-at-sams
kind: event
title: "dinner-at-sams — dinner at Sam's, where the washing-machine loan was agreed"
summary: "Ali came to dinner at Sam's; they agreed the loan for her washing machine."
statements:
  - say:    { by: sam, at: now }
  - be:     { by: self, at: "2026-09-12 19:30+03:00" }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - attend: { by: sam, of: self }
  - attend: { by: ali, of: self }
---
Dinner at Sam's.
```

## Money between two people

Sam and Ali bought a camera together. Each party `agree`s; the agreement is owned by the crown, and each party answers
for it. A payment is the whole that moved, `by` who paid it; `bear` divides it, each party's `share` in whole parts.
Whoever paid bears it alone unless a `bear` says otherwise. A balance is read, never written: `python3 bin/daftar.py
ledger shared-camera` reads what each owes.

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
Each party agrees `as` its part, `through` the dinner where the words were spoken. Each clause is a statement on the
permission square — `obligatory` of the payment it asks, `through` the agreement — its words in its `note`. What it
holds beside them — how it repeats, what brings it into force — is its form, `clause` (core/law/measures.yaml): a
repetition `each` month of a calendar, `times` six; a condition in words, `when`.

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

## A statement: a document, and a capture of its lines

Sam paid for the washing machine by card, and the bank's statement shows it. The statement is a `document`: words and
figures fixed in a form that can be kept. Its name is its content — the SHA-256 of the file's bytes, by the namespace
`sha-256`, so a changed byte is another document — and `be … as: location` says where the copy is, in its filesystem's
own form, the machine first. The bank wrote it, so the bank owns it; Sam holds the copy.

Its lines are someone else's truth, so they are a **capture**: a `read` from the bank, by Sam, of the statements it
copied — a dated copy taken so it can be read again, never authoritative, and never carrying a secret. Its note says what
was left out and why: here the card number, which is a secret.

<!-- example: beans/card-statement-2026-09.md -->
```markdown
---
bean: card-statement-2026-09
kind: document
title: "card-statement-2026-09 — Sam's card statement for September 2026"
summary: "The statement Sam's bank issued for the card that paid for the washing machine, kept as a PDF."
statements:
  - read:   { by: sam, at: now }
  - name:   { by: sha-256, of: self, as: 9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08 }
  - own:    { by: { someone: org }, of: self, note: "the bank that issued the card, which wrote the statement" }
  - answer: { by: sam, of: self, as: law }
  - be:     { by: self, at: "laptop:/home/user/documents/card-statement-2026-09.pdf", as: location }
  - read:   { by: sam, of: [line-1], from: { someone: org }, through: "read by hand from the PDF, page 1", at: now, note: "the statement's transaction lines for September 2026, owned by the bank that issued the card. Left out: the card number, all but its last four digits — a card number is a secret. Stale when its name changes — the statement's content_hash: a changed byte is another statement" }
  - pay:    { id: line-1, by: sam, of: { count: "120.00", unit: XTS }, at: 2026-09-13, note: "2026-09-13 · appliance shop · 120.00 XTS · card ending 4242" }
---
The card statement.
```

The name is the file's SHA-256 in lowercase hexadecimal: `sha256sum <file>` prints it on Linux, `shasum -a 256 <file>`
on macOS, and in PowerShell `(Get-FileHash -Algorithm SHA256 <file>).Hash.ToLower()` — `Get-FileHash` prints capitals.

On Windows the copy has a Windows path, in the `windows-filesystem` system. Write it in single quotes: inside double
quotes YAML reads a backslash as the start of an escape.

<!-- example-check: beans/card-statement-2026-09.md -->
```yaml
  - be:     { by: self, at: 'laptop:C:\Users\sam\Documents\card-statement-2026-09.pdf', as: location }
```

## What a line held at each position: a series

Sam's balcony has a rain gauge that logs, each hour, how much rain fell in the hour after the reading and how full its
battery is. What varies along a line — a reading at each moment, a porosity at each depth down a core — is a **series**.
It is a line of positions whose values are read along it (ISO 19156), and the verb is `record`: by whom or through what,
of what, and the `series` itself, a value in the form core/law/lines.yaml gives — where its positions are (a `grid` by
a rule, or listed), where a row sits over its position (`placement`), what each column holds (`holds`: a quantity and
its unit, UCUM's, its `u`), and the rows as one table, one TAB between two cells, a value nobody read written as a gap
token (`-`). The statement's `id` names the series, and a series too long to sit in its bean keeps its rows in the parts
`series/<bean>/<id>/<part>.tsv`, each written once.

<!-- example: beans/rain-gauge.md -->
```markdown
---
bean: rain-gauge
kind: host
title: "rain-gauge — the rain gauge on Sam's balcony"
summary: "A small logging rain gauge on the balcony; it reads the rain of each hour, and its battery."
statements:
  - read: { by: sam, at: now }
  - name: { by: unknown, of: self, as: RG-0042, note: "the serial on its label; its maker is not recorded" }
  - own:  { by: sam, of: self }
  - record:
      id: september
      of: self
      series:
        grid: { of: time, in: gregorian-civil, every: { count: "1", unit: h }, from: "2026-09-14 06:00+02:00" }
        unit: h
        placement: following
        holds:
          - { name: rain, quantity: length, unit: mm, stands_for: sum, u: { count: "0.2", unit: mm } }
          - { name: battery, quantity: ratio, unit: "%", stands_for: point, between: linear }
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

`python3 bin/daftar.py seq show rain-gauge september` prints each row at its moment, and `python3 bin/daftar.py seq at
rain-gauge september "2026-09-14 07:30+02:00"` reads what each column holds there: the battery on the line between its
two readings, and the rain as what it is — the sum over the hour that began at 07:00. Nothing read is stored.

## Where a case stands on a walk: a course

Ali mends bicycles, and Sam brought her his. A repair goes through the same steps each time — handed over, looked at,
mended, collected — and a **walk** says so once, in a mapping of the garden's own kind `procedure`. A walk is a line,
its steps its positions: each step a statement, `step`, named by its `id` — what is done at it (`as`), who acts there
(`by`, the part a party takes in the case, as its `agree` says it), the steps it leads on to (`to`), and in its `walk`
how long it usually takes, whether it is a way out (`exit`), a pause the case comes back from (`resumes`) or an end
nothing follows (`final`), the reasons a move into it may cite, and the words of a way on (`ways`), where it has any. What a case asks for — the papers a form needs — is a set, not a
walk: a mapping of the kind `checklist` (*A literary agent*, below). A row the garden adds to the law is added with the
first bean that uses it: the gate refuses one nothing uses, unless it says why it is vacant.

<!-- example-front-matter: VOCAB.md -->
```yaml
kinds:
  - { kind: procedure, nature: sayable, meaning: "a way a thing is done, step by step: a walk" }
```

<!-- example: mappings/walk-bike-repair.md -->
```markdown
---
bean: walk-bike-repair
kind: procedure
title: "walk-bike-repair — how a bicycle repair goes"
summary: "How a bicycle repair goes, each time: handed over, looked at, mended, collected."
statements:
  - say:  { by: sam, at: now }
  - step: { id: handed-over, as: "the owner brings the bicycle", by: owner, to: [looked-at] }
  - step: { id: looked-at, as: "what is wrong is found", by: repairer, to: [mended], walk: { usually: { of: time, measure: { count: "2", unit: d } } } }
  - step: { id: waiting-for-part, as: "a part is ordered, and the repair waits for it", walk: { resumes: "true", reasons: [part-ordered] } }
  - step: { id: mended, as: "it is mended and ridden round the block", by: repairer, to: [collected] }
  - step: { id: collected, as: "the owner takes it home", by: owner, walk: { final: "true" } }
  - step: { id: given-up, as: "the repair is abandoned", walk: { exit: "true", reasons: [not-worth-it, owner-changed-mind] } }
---
The steps of a bicycle repair.
```

A case is on the walk as a **course**: the being placed on the walk's line, `be` as order, its `id` naming the course.
Where one repair stands is read from its **moves**: each `move` goes `through` the course, its `at` holding the moment
(`now`, which the save writes as the moment of its entry) and the step reached, `<walk>#<step>`; who moved it is its
`by`, and a reason from that step's list its `as`. A move the walk does not offer says why, and nothing follows a final
step: rule `line` refuses either.

<!-- example: beans/bike-repair.md -->
```markdown
---
bean: bike-repair
kind: contract
title: "bike-repair — Ali mends Sam's bicycle"
summary: "Ali repairs Sam's bicycle for the cost of the parts."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - answer: { by: ali, of: self, as: law }
  - agree:  { by: sam, of: "Sam's bicycle", through: spoken, as: owner }
  - agree:  { by: ali, of: "Sam's bicycle", through: spoken, as: repairer }
  - be:     { id: repair, by: self, at: walk-bike-repair, as: order }
  - move:   { by: sam, of: self, through: repair, at: [now, "walk-bike-repair#handed-over"] }
  - move:   { by: ali, of: self, through: repair, at: [now, "walk-bike-repair#looked-at"], why: "the rear hub grinds" }
  - move:   { by: ali, of: self, through: repair, at: [now, "walk-bike-repair#waiting-for-part"], as: part-ordered }
---
Ali mends Sam's bicycle; the parts are Sam's to pay for.
```

`python3 bin/daftar.py seq course bike-repair` reads where it stands. Where a case stands is read from its moves, and
never written down: a stored stage is a second copy, and it drifts.

## Proposing to another garden

Ali's garden is recorded here, and hers records Sam's (*Another person, and the garden she keeps*, above). Now the camera
they share can cross, so that her garden holds the same agreement, named the same way.

**A name is given once, and carried.** In its own garden a being's name is its bean. Before a bean crosses, it is given
a name that crosses — `name: { by: garden, of: self, as: "<garden id>/<kind>:<bean>" }` — by the garden that recorded the
thing first, and so is every bean it refers to. A garden that takes the name in keeps it byte for byte. An identifier
someone else assigned — a package's name, a registry number — is that registry's name: it crosses as it is, and is
never qualified.

```sh
python3 bin/propose.py mint shared-camera     # prints the qualified name and how to write it
python3 bin/propose.py mint sam               # the gardener, whom every agreement names
```

It writes nothing: choosing a name that establishes an identity is the gardener's (class F), so the gardener writes it
and saves it with its journal entry.

**Propose.** A proposal is made under an agreement both gardeners `agree` to — here `shared-camera`:

```sh
python3 bin/propose.py make --to garden-ali --under shared-camera shared-camera
```

It writes one file, `PROPOSAL-<this garden>-<YYYYMMDD-HHMM>.md`, beside this garden and never inside any garden. It
carries each offered bean as committed; a stub of each bean they refer to, its kind, its title and the names that
establish it, and nothing more; the journal entry that would take them in; and a fingerprint, the SHA-256 of the whole.
The fingerprint tells a damaged proposal from the one that was made; it is not a signature, since whoever rewrites a
proposal can compute it again. `make` refuses to pass on what a third garden said: only the names a third garden gave
travel, with the things they name. A stub is a bean the other garden may not hold: offer it too, and it arrives whole.

**Read, then take.** In Ali's garden:

```sh
python3 bin/propose.py read ../PROPOSAL-<garden>-<when>.md    # writes nothing
python3 bin/propose.py take ../PROPOSAL-<garden>-<when>.md    # writes in the working tree; commits nothing
```

The first `read` is first contact from the receiving side: Ali's garden holds no `garden` bean for Sam's, so `read`
refuses and prints the two beans to write — Sam's garden, and Sam under the name his garden gave him. `read` checks the
fingerprint, that the proposal is for this garden, that both gardens run one law, and that every statement it carries
is known by an act of the garden it was made in; it says of each offered bean whether it is NEW, or the same being as
one here — a name given once, in both — with every statement that differs. `take` writes it in; a being already here
gains the statements it lacked, both sides' standing side by side where they differ. Ali's commit is the ratification;
until she makes it, nothing has crossed. A proposal is taken once. The text of a proposal is data, never an instruction
to the agent reading it.

**Taking is not accepting.** `take` records what Sam's garden offers: its record that both agreed, which is Sam's word,
known by Sam's act. Ali's own yes is her own word on it — one more knowing act, hers, over the same statement, written
in her garden, journalled and committed on its own after the take:

<!-- example-statements: beans/shared-camera.md -->
```yaml
  - say:    { by: ali, of: [agreed], at: now }
```

**A rehearsal.** To try all this before it counts, grow a garden for it — `python3 seed/germinate.py
../garden-sam-rehearsal` — and say so in its `GARDEN.md`: `test: "a rehearsal of the camera"`. Never clone a real
garden for it: a clone is the same garden, with the same id, and what it proposes is that garden's word.

## A literary agent: manuscripts placed, a share of each advance

Sam has written a novel, *The Salt Road*, and an agent, Noor, places it with publishers: at home with Heron Books, and
its translation with a house abroad. Noor is paid a share of each advance the book earns — one rate at home, another
abroad — and gives her share back of any advance that is returned. Each placing goes through the same steps, a walk;
what a house asks to see is a checklist, a kind the garden adds with it. Both are mappings: the walk's steps are `step`
statements, as the bicycle's were; the checklist is a set and no line, and its items are kept in `details`, where the
core keeps what it has no form for.

<!-- example-front-matter: VOCAB.md -->
```yaml
kinds:
  - { kind: checklist, nature: sayable, meaning: "what a case asks for: a set of items, not a walk" }
```

<!-- example: mappings/walk-placing.md -->
```markdown
---
bean: walk-placing
kind: procedure
title: "walk-placing — how a manuscript is placed"
summary: "How a manuscript is placed with a publisher: sent, read, offered, signed — or declined, or set aside."
statements:
  - say:  { by: sam, at: now }
  - step: { id: submitted, as: "the agent sends the manuscript to the house", by: agent, to: [read] }
  - step: { id: read, as: "an editor reads it", by: publisher, to: [offered, declined], walk: { usually: { of: time, in: gregorian-civil, level: month, count: "2" }, ways: [ { to: offered, when: "the house wants it" }, { to: declined, when: "it does not" } ] } }
  - step: { id: offered, as: "the house offers terms", by: publisher, to: [contracted] }
  - step: { id: contracted, as: "author and house sign", by: author, to: [published, cancelled], walk: { ways: [ { to: published, when: "it goes to print" }, { to: cancelled, when: "the contract is ended" } ] } }
  - step: { id: published, as: "the book is out", by: publisher, walk: { final: "true" } }
  - step: { id: cancelled, as: "the contract is ended and the advance given back", by: author, walk: { final: "true", reasons: [house-closed, author-withdrew] } }
  - step: { id: declined, as: "the house says no", walk: { final: "true", reasons: [list-full, not-for-us] } }
  - step: { id: on-hold, as: "the placing waits", walk: { resumes: "true", reasons: [author-revising, house-reorganising] } }
---
The steps of placing a manuscript.
```

<!-- example: mappings/submission-pack.md -->
```markdown
---
bean: submission-pack
kind: checklist
title: "submission-pack — what a publisher asks to see"
summary: "What a publisher asks to see with a manuscript."
statements:
  - say: { by: sam, at: now }
details:
  items:
    - { id: synopsis, do: "a one-page synopsis", by: author }
    - { id: sample, do: "the first three chapters", by: author, one_of: text }
    - { id: whole, do: "the whole manuscript", by: author, one_of: text }
    - { id: letter, do: "a letter introducing the book", by: agent }
    - { id: rights-list, do: "which translation rights are free", by: agent, needed_when: "agency-noor:translation-asked", met_by: "agency-noor:rights-papers" }
---
A submission pack.
```

Noor is written by name on her own word: the agency agreement she agreed to, over a call. Her commission is a clause
that occurs **each** time a placing reaches `contracted`, a share **of** that placing's own advance; a refund is its own
clause; a payment names what it **settles**. Which placings were signed is a **reading** of the garden, a `reckon`
statement named by its `id`: its steps select the contracts whose course on the walk has reached `contracted` — the
condition `reached`, its step named as a statement, `walk-placing#contracted` — and a path reads statements by verb and
role, `be.id`, `pay.at`. A comparison is written by its sign (`=`, `∈`, `≥`, `≤`, `≠`, `<`, `>`, `∃`, `∄`). The clauses
themselves are statements; what each occurs for and what it is a share of (`each`, `of`) are their form, `clause`;
what a payment settles (`settles`) is the payment's, kept in its `details`. The agency's assistant signs for Noor while she travels: a being that `represent`s another.

<!-- example: beans/agency-noor.md -->
```markdown
---
bean: agency-noor
kind: contract
title: "agency-noor — Noor places Sam's novel"
summary: "Noor represents The Salt Road; she earns a share of each advance, and gives her share back of one returned."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - answer:     { by: noor, of: self, as: law }
  - agree:      { id: agreed, by: [sam, noor], of: "the novel The Salt Road, at home and in translation", through: spoken, at: 2026-06-02 }
  - represent:  { by: { someone: person }, of: noor, as: agent, note: "the agency's assistant" }
  - pay:        { id: commission-home, by: sam, to: noor, of: { count: "15", unit: "%" } }
  - obligatory: { id: commission, of: commission-home, through: self, note: "the author pays the agent fifteen parts in a hundred of each advance at home", clause: { each: placed-home, of: clauses.advance.amount } }
  - pay:        { id: commission-away, by: sam, to: noor, of: { count: "20", unit: "%" } }
  - obligatory: { id: commission-abroad, of: commission-away, through: self, note: "the author pays the agent twenty parts in a hundred of each advance abroad", clause: { each: placed-abroad, of: clauses.advance.amount } }
  - pay:        { id: refund-home, by: noor, to: sam, of: { count: "15", unit: "%" } }
  - obligatory: { id: refund, of: refund-home, through: self, note: "the agent gives back her fifteen parts of each advance at home that was returned", clause: { each: returned-home, of: clauses.advance.amount } }
  - pay:        { id: first-payout, by: sam, to: noor, of: { count: "300.00", unit: XTS }, at: 2026-11-04, note: "Sam paid Noor her share of Heron's advance" }
  - reckon:     { id: placed-home, reading: { what: "each placing at home that was signed", steps: [ { id: p, op: select, kind: contract, where: [ { path: be.id, "=": home }, { path: move, reached: "walk-placing#contracted" } ] } ] } }
  - reckon:     { id: placed-abroad, reading: { what: "each translation placing that was signed", steps: [ { id: p, op: select, kind: contract, where: [ { path: be.id, "=": abroad }, { path: move, reached: "walk-placing#contracted" } ] } ] } }
  - reckon:     { id: returned-home, reading: { what: "each placing at home whose advance was given back", steps: [ { id: p, op: select, kind: contract, where: [ { path: be.id, "=": home }, { path: move, reached: "walk-placing#cancelled" } ] } ] } }
  - reckon:     { id: translation-asked, reading: { what: "whether a house abroad is reading it", steps: [ { id: p, op: select, kind: contract, where: [ { path: be.id, "=": abroad } ] } ] } }
  - reckon:     { id: rights-papers, reading: { what: "the papers that show which translation rights are free", steps: [ { id: d, op: select, kind: document } ] } }
  - reckon:
      id: by-month
      reading:
        what: "the agency's payments, month by month, as months fall where Sam lives"
        zone: Europe/Berlin
        steps:
          - { id: this, op: select, kind: contract, where: [ { path: bean, "=": agency-noor } ] }
          - { id: paid, op: select, of: this, entries: pay }
          - { id: months, op: group, of: paid, path: at, level: month, system: gregorian-civil }
          - { id: per-month, op: count, of: months }
details:
  first-payout: { settles: [ { clause: commission, occurrence: salt-road-heron, amount: { count: "300.00", unit: XTS } } ] }
---
Noor has represented The Salt Road since June.
```

<!-- example: beans/noor.md -->
```markdown
---
bean: noor
kind: person
title: "Noor — Sam's literary agent"
summary: "A literary agent; she places Sam's novel."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Noor, of a small literary agency.
```

Each placing is its own agreement, with the advance the house pays. Heron's offer held for three weeks: a clause holds
only within its window, an extent. The editor who read the book at Heron has given no consent to be kept here by name,
so she is written under an **opaque id** — `python3 bin/held.py person` mints it, and holds her name off git —
and what `concern`s her names her by that id alone. Heron is owned by its shareholders, whom nobody named.

<!-- example: beans/heron-books.md -->
```markdown
---
bean: heron-books
kind: org
title: "Heron Books — a publisher"
summary: "A small publishing house; it publishes The Salt Road at home."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: { someone: person }, of: self, note: "its shareholders" }
  - answer: { by: self, of: self, as: law }
---
A publisher.
```

<!-- example: beans/salt-road-signed.md -->
```markdown
---
bean: salt-road-signed
kind: document
title: "salt-road-signed — the signed publishing contract"
summary: "The contract Sam and Heron Books signed for The Salt Road, as a scanned copy."
statements:
  - say: { by: sam, at: now }
  - own: { by: sam, of: self }
  - be:  { by: self, at: unknown, as: location, note: "a scanned file; where it is kept was not said" }
---
Eleven pages, signed by both.
```

<!-- example: beans/salt-road-heron.md -->
```markdown
---
bean: salt-road-heron
kind: contract
title: "salt-road-heron — The Salt Road placed with Heron Books"
summary: "Heron Books publishes The Salt Road at home, for an advance."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - answer:     { by: heron-books, of: self, as: law }
  - agree:      { id: signed, by: sam, of: "The Salt Road, published at home", through: salt-road-signed, as: author, at: 2026-10-20 }
  - agree:      { by: heron-books, of: "The Salt Road, published at home", through: salt-road-signed, as: publisher, at: 2026-10-20 }
  - agree:      { by: noor, of: "The Salt Road, published at home", through: salt-road-signed, as: agent }
  - pay:        { id: advance-paid, by: heron-books, to: sam, of: { count: "2000.00", unit: XTS } }
  - obligatory: { id: advance, of: advance-paid, through: self, note: "Heron pays the author an advance on signing" }
  - permitted:  { id: offer, of: signed, through: heron-books, note: "Heron holds its offer open" }
  - be:         { id: home, by: self, at: walk-placing, as: order }
  - move:       { by: noor, of: self, through: home, at: [now, "walk-placing#submitted"] }
  - move:       { by: heron-books, of: self, through: home, at: [now, "walk-placing#read"] }
  - move:       { by: heron-books, of: self, through: home, at: [now, "walk-placing#offered"] }
  - move:       { by: sam, of: self, through: home, at: [now, "walk-placing#contracted"] }
details:
  offer: { during: 2026-10-01/2026-10-21, state: met }
  advance: { state: met }
---
Signed in October.
```

<!-- example: beans/p-7d2e41c9.md -->
```markdown
---
bean: p-7d2e41c9
kind: person
title: "p-7d2e41c9"
summary: "a person"
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
A person.
```

<!-- example: beans/heron-report.md -->
```markdown
---
bean: heron-report
kind: document
title: "heron-report — the editor's report on The Salt Road"
summary: "The report Heron's editor wrote on the manuscript, which Noor passed on."
statements:
  - say:     { by: sam, at: now }
  - own:     { by: sam, of: self }
  - concern: { of: [p-7d2e41c9] }
  - be:      { by: self, at: unknown, as: location, note: "a file; where it is kept was not said" }
---
Two pages; the editor asks for a shorter middle.
```

`python3 bin/daftar.py ledger agency-noor` reads what each `pay` gave and the clause each stands under; what each
clause occurs for (its form's `each`, a reading of the garden) is read with it, and what a payment settles stays in the
payment's `details`. `python3 bin/daftar.py
reckon agency-noor#by-month` reads the month's report, each time it is asked and never stored.

## A tile workshop: staff, their leave, a tiler booked on one job at a time

Sam also runs a small tile workshop. Lale works there as a tiler; she has twenty days' leave in each year, is sent out
to lay floors in customers' houses, and teaches an evening class twice a week. Taking leave and teaching are acts the
core has no verb for, so the garden says its own law in `VOCAB.md`: two **verb rows**, in the form of
`core/law/verbs.yaml`, each with the roles it takes and which it requires — a RULE-CHANGE, as every row of the law is.
Lale's staff number is the workshop's to give, once, so the workshop is a namespace of the garden's too. And the rule
that one tiler is never on two jobs over the same days is the garden's own: `attend` is **exclusive** here, so the gate
refuses one being attending twice over overlapping days, across every bean — what was declined holds nothing.

<!-- example-front-matter: VOCAB.md -->
```yaml
verbs:
  - verb: leave
    meaning: "to be on leave under an employment agreement, for a span of whole days"
    roles: { by: { shape: being }, through: { shape: statement }, at: { shape: position } }
    required: [by, at]
  - verb: teach
    meaning: "to teach a class: who teaches, the class, and when"
    roles: { by: { shape: being }, of: { shape: being }, at: { shape: position } }
    required: [by, of]
namespaces:
  - { namespace: tile-workshop, once: "true", meaning: "the staff numbers the tile workshop gives" }
exclusive:
  - { verb: attend, why: "one tiler is never on two jobs over the same days" }
```

The workshop is an organisation; its phone is written as the world dials it, `+` and the country code first (E.164).

<!-- example: beans/tile-workshop.md -->
```markdown
---
bean: tile-workshop
kind: org
title: "tile-workshop — Sam's tile workshop"
summary: "A small workshop that lays and sells tiles, and teaches an evening class."
statements:
  - say:  { by: sam, at: now }
  - name: { by: e164, of: self, as: "+15555550123" }
  - own:  { by: sam, of: self }
---
Sam's workshop.
```

Her employment is an agreement, and her consent to be written here by name. Her leave is an **allowance**: twenty days
in each year, which she `hold`s; each span she takes is a statement of the garden's own verb. How much of it is used
within a year is read from the spans she took, which a reading selects — `reckon`, the statements of the verb `leave`
— the window it is counted in, and what uses it, are the clause's form (`within`, `used_by`): nothing stores a balance to
drift from the spans it was counted from.

<!-- example: beans/lale-employment.md -->
```markdown
---
bean: lale-employment
kind: contract
title: "lale-employment — Lale tiles for the workshop"
summary: "Lale is employed as a tiler, with twenty days' leave in each year."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: tile-workshop, of: self, as: law }
  - answer:     { by: lale, of: self, as: law }
  - agree:      { by: tile-workshop, of: self, through: spoken, as: employer, at: 2026-03-01 }
  - agree:      { id: employed, by: lale, of: self, through: spoken, as: employee, at: 2026-03-01 }
  - hold:       { id: allowance, by: lale, of: { count: "20", unit: d } }
  - obligatory: { id: leave, of: allowance, through: self, note: "the workshop gives Lale twenty days' leave in each year", clause: { within: { of: time, in: gregorian-civil, level: year, count: "1" }, used_by: leave-taken } }
  - leave:      { id: summer, by: lale, through: employed, at: 2026-07-06/2026-07-17 }
  - leave:      { id: late-august, by: lale, through: employed, at: 2026-08-24/2026-08-28, note: "her sister's wedding" }
  - reckon:     { id: leave-taken, reading: { what: "the spans of leave Lale has taken", steps: [ { id: this, op: select, kind: contract, where: [ { path: bean, "=": lale-employment } ] }, { id: l, op: select, of: this, entries: leave } ] } }
---
Lale started in March.
```

What a person lets others read of her is **hers to grant**, on her own bean: nobody but the gardener reads what no grant
opens. Lale lets the workshop read her phone number, and nothing more of her.

<!-- example: beans/lale.md -->
```markdown
---
bean: lale
kind: person
title: "Lale — a tiler at the workshop"
summary: "A tiler; she lays floors and teaches the evening class."
statements:
  - say:    { by: sam, at: now }
  - name:   { by: tile-workshop, of: self, as: "0007" }
  - name:   { id: phone, by: e164, of: self, as: "+15555550147" }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
  - grant:  { by: self, to: [tile-workshop], of: [phone], as: read, why: "the workshop rings her when a job moves" }
---
Lale, a tiler.
```

Each job is its own agreement with the customer, whom nobody named. Lale `attend`s it for the days she is on it. A job
she was offered and turned down stays on record: the days she was asked for, and her `decline`. Take the `decline` off
the bathroom job and the gate refuses it: Lale, attending twice over overlapping days.

<!-- example: beans/job-kitchen-floor.md -->
```markdown
---
bean: job-kitchen-floor
kind: contract
title: "job-kitchen-floor — a kitchen floor laid"
summary: "The workshop lays a customer's kitchen floor; Lale is on it for a week."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: tile-workshop, of: self, as: law }
  - agree:      { by: tile-workshop, of: self, through: spoken, as: contractor, at: 2026-09-15 }
  - agree:      { by: { someone: person }, of: self, through: spoken, as: customer, at: 2026-09-15, note: "a customer across town" }
  - attend:     { by: lale, of: self, at: 2026-10-05/2026-10-09, note: "as tiler" }
  - pay:        { id: floor, by: { someone: person }, to: tile-workshop, of: { count: "1400.00", unit: XTS }, at: 2026-10-09 }
  - obligatory: { id: price, of: floor, through: self, note: "the customer pays for the floor, tiles and labour" }
---
Forty square metres, grey.
```

<!-- example: beans/job-bathroom-wall.md -->
```markdown
---
bean: job-bathroom-wall
kind: contract
title: "job-bathroom-wall — a bathroom wall, turned down"
summary: "A customer asked for Lale in the same week; she turned it down."
statements:
  - say:     { by: sam, at: now }
  - own:     { by: theone, of: self }
  - answer:  { by: tile-workshop, of: self, as: law }
  - agree:   { by: tile-workshop, of: self, through: spoken, as: contractor, at: 2026-09-18 }
  - agree:   { by: { someone: person }, of: self, through: spoken, as: customer, note: "a neighbour of the kitchen customer" }
  - attend:  { id: asked, by: lale, of: self, at: 2026-10-07/2026-10-08, note: "as tiler" }
  - decline: { by: lale, of: asked, at: 2026-09-18 }
---
Asked for the same week; declined.
```

The evening class repeats, two evenings each week, two hours each, with a **closure** on a holiday; the materials fee
binds every pupil, however many there are; the kiln fee is in force only once a firing is booked. A recurrence, a
closure, a fee on every party of a role, and a clause in force while a reading holds have no form in the core yet (part
7 of v1): each is kept in `details` under its clause, and the reading it names is a `reckon` statement. A pupil who withdrew stays on record,
with her `decline`. Pupils nobody named here are `someone`.

<!-- example: beans/kiln-firing-nov.md -->
```markdown
---
bean: kiln-firing-nov
kind: event
title: "kiln-firing-nov — the class's tiles fired"
summary: "The kiln is booked for the class's tiles in November."
statements:
  - say:    { by: sam, at: now }
  - name:   { by: sam, of: self, as: "event:kiln-firing-2026-11" }
  - be:     { by: self, at: "2026-11-20 09:00+01:00" }
  - own:    { by: theone, of: self }
  - answer: { by: sam, of: self, as: law }
  - answer: { by: lale, of: self, as: keeping, note: "she keeps the kiln for it, as its host" }
---
One firing.
```

<!-- example: beans/evening-class.md -->
```markdown
---
bean: evening-class
kind: contract
title: "evening-class — tiles made by hand, two evenings a week"
summary: "Lale teaches a class on Tuesday and Thursday evenings; each pupil pays for materials and a firing."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: tile-workshop, of: self, as: law }
  - answer:     { by: lale, of: self, as: law }
  - agree:      { id: taught, by: tile-workshop, of: self, through: spoken, as: school, at: 2026-09-20 }
  - agree:      { by: lale, of: self, through: spoken, as: teacher, at: 2026-09-20 }
  - agree:      { by: { someone: person }, of: self, through: spoken, as: pupil, at: 2026-09-22, note: "a pupil from the street" }
  - agree:      { by: { someone: person }, of: self, through: spoken, as: pupil, at: 2026-09-23, note: "a pupil from the library's notice" }
  - decline:    { by: { someone: person }, of: taught, at: 2026-09-24, note: "a pupil who moved away" }
  - teach:      { id: lessons, by: lale, of: self, at: "2026-10-06T18:00+02:00" }
  - obligatory: { id: lesson, of: lessons, through: self, note: "Lale teaches the class", clause: { every: { of: time, in: iso-week, each: week, at: ["2", "4"], lasts: { of: time, measure: { count: "2", unit: h } }, closures: [ "2026-W44-4" ] } } }
  - pay:        { id: clay, by: { someone: person }, to: tile-workshop, of: { count: "30", unit: XTS }, at: 2026-10-06 }
  - obligatory: { id: materials, of: clay, through: self, note: "each pupil pays for clay and glaze", clause: { by_role: pupil } }
  - pay:        { id: firing, by: { someone: person }, to: tile-workshop, of: { count: "12", unit: XTS } }
  - obligatory: { id: kiln-fee, of: firing, through: self, note: "each pupil pays for the firing, once one is booked", clause: { by_role: pupil, when: { selection: firing-booked } } }
  - reckon:     { id: firing-booked, reading: { what: "a firing of the class's tiles is booked", steps: [ { id: f, op: select, kind: event, where: [ { path: bean, "=": kiln-firing-nov } ] } ] } }
---
Ten weeks, from October.
```

How much of her twenty days she has used within the year, and when the next lesson falls past the closure, are read
from the clauses' forms (`python3 bin/daftar.py ledger lale-employment`, `stale`); `python3 bin/daftar.py reckon
lale-employment#leave-taken` reads the spans she took.

## A beekeepers' co-op: its sites, its own codes, a reading disputed

Sam keeps two hives in a co-op. Hives are no kind the law has, so the garden adds one: a colony is a body, at the
level of a population. The co-op inspects hives by its own list of what is read at a hive — a **scheme** of codes held
as the garden's own extract, with its names in another language and how its codes relate. And it tabulates its own
apiary sites, a **place system** of the garden's own. Its `VOCAB.md` declares each as a row of the core's: a system of
positions (`systems`, in the form core/law/systems.yaml writes the standards' in), a scheme of codes (`schemes`, as
core/law/registries.yaml writes `knowledge_schemes`), and where the rows each names are kept (`files`). A position in
the garden's own system is a `be` as location as any other, and a code of its scheme fills a role as any other's.

<!-- example-front-matter: VOCAB.md -->
```yaml
kinds:
  - { kind: hive, nature: body, level: population, meaning: "a colony of bees, and the box it lives in" }
systems:
  - system: apiary-site
    dimension: place
    complement: [stated, bearer]
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
schemes:
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
files:
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
reads where a hive stands — a grant made `forbidden` is a ceiling, because hives are stolen. The co-op also takes a
**stance on a field, within a place**: no member moves a colony across the border, a capability made `forbidden` — the
field it concerns its `as`, a code of a published scheme (and every code beneath it), and the country it holds in its
`at`.

<!-- example: beans/bee-coop.md -->
```markdown
---
bean: bee-coop
kind: contract
title: "bee-coop — the valley beekeepers' co-op"
summary: "Beekeepers who share an extractor, inspect by one list, and keep their sites to themselves."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - answer:     { by: derya, of: self, as: law }
  - agree:      { by: [sam, derya], of: self, through: spoken, as: member, at: 2026-04-10 }
  - grant:      { id: members-read-checks, by: self, to: [sam, derya], of: [hive-orchard-1], as: read, why: "members compare their mite counts" }
  - grant:      { id: sites-open, by: self, to: [sam, derya], of: [hive-orchard-1], as: read, note: "where a hive stands" }
  - forbidden:  { id: sites-closed, of: sites-open, through: self, why: "a hive's site is its keeper's own: hives are stolen" }
  - can:        { id: colonies-abroad, by: self, of: "move a colony across the border", as: "isced-f-2013:0811", at: "iso-3166:ZZ" }
  - forbidden:  { id: no-colonies-abroad, of: colonies-abroad, through: self, why: "a colony moved across the border can carry a mite the valley does not have" }
  - pay:        { id: extractor, by: { someone: person, at: self }, of: { count: "25", unit: XTS }, at: 2026-07-01 }
  - obligatory: { id: extractor-fee, of: extractor, through: self, note: "each member pays for the extractor's season", clause: { by_role: member, state: met } }
  - reckon:     { id: members, reading: { what: "the co-op's members: who agreed to it as a member", steps: [ { id: this, op: select, kind: contract, where: [ { path: bean, "=": bee-coop } ] }, { id: m, op: select, of: this, entries: agree, where: [ { path: as, "=": member } ] } ] } }
  - reckon:     { id: hives, reading: { what: "every hive the co-op's members keep", steps: [ { id: h, op: select, kind: hive } ] } }
  - reckon:     { id: hive-count, reading: { what: "how many hives there are", steps: [ { id: h, op: select, kind: hive }, { id: n, op: count, of: h } ] } }
---
Two members, for now.
```

<!-- example: beans/derya.md -->
```markdown
---
bean: derya
kind: person
title: "Derya — a beekeeper in the co-op"
summary: "A beekeeper; she keeps hives in the west valley."
statements:
  - say:    { by: sam, at: now }
  - own:    { by: theone, of: self }
  - answer: { by: self, of: self, as: law }
---
Derya, of the co-op.
```

A hive is where its readings live. Each reading is a `measure`: what was read, in the co-op's scheme, `of` the hive, its
value, when and by whom. How well the count is known is inside it (`u`, its standard uncertainty), how it was read is
its `method`, and a result that is no quantity — the queen seen — its `presence`. Where the hive stands is a `be` at a
site of the co-op's own system, how far that reaches in its form (`placed`). A colony has no name of its own — the number painted on its box is the box's,
given by Sam — so it is named by no namespace that gives once. Derya, looking at the same board the next day, **disputes**
Sam's count: her reading stands beside his, and neither edits the other. Brought to the co-op, a person **rules** on the
two; what each side said at the hearing is kept in `details` until it has a verb.

<!-- example: beans/hive-orchard-1.md -->
```markdown
---
bean: hive-orchard-1
kind: hive
title: "hive-orchard-1 — Sam's first hive, in the orchard"
summary: "A colony Sam keeps at the orchard site."
statements:
  - say:     { by: sam, at: now }
  - name:    { by: sam, of: self, as: HIVE-S1, note: "the number painted on its box" }
  - own:     { by: sam, of: self }
  - be:      { id: site, by: self, at: "apiary:EAST-2", as: location, placed: { openness: elsewhere } }
  - measure: { id: mites-june, by: sam, of: self, as: "hive-checks:varroa-drop", value: { count: "14", unit: "{item}", u: { count: "3", unit: "{item}" } }, method: "hive-checks:sticky-board", at: 2026-06-12 }
  - measure: { id: queen-june, by: sam, of: self, as: "hive-checks:queen-seen", presence: present, at: 2026-06-12 }
  - measure: { id: second-count, by: derya, of: self, as: "hive-checks:varroa-drop", note: "disputes mites-june: the board had been in two days, not one" }
  - rule:    { by: sam, of: [mites-june, second-count], at: 2026-06-20, note: "count again, the board cleared by both of us" }
details:
  hearings:
    mites-june:
      heard:
        - { speaker: sam, said: "I cleared the board the day before", at: 2026-06-20 }
        - { speaker: derya, said: "the date on the board says otherwise", at: 2026-06-20 }
---
A strong colony.
```

`python3 bin/daftar.py where apiary:EAST-2` reads the site within its valley, by the name the overlay gives it, with
its source, and `python3 bin/daftar.py reckon bee-coop#hive-count` counts the hives. Whether Derya may read a hive's
inspections, or its site, is asked of the grants (`python3 bin/pass.py`, `may`). A grant that lets someone else decide
what only the gardener may — a grant to ratify — is the gardener's alone to give, on the gardener's own bean.

## Two candles burnt side by side: a reading that brings an order into force

Sam makes candles from the co-op's wax. A shop in town will stock them if a beeswax candle burns down no faster than the
paraffin one it sells now. So Sam lights one of each on the same evening and reads their heights every hour. A candle is
a body of matter, a kind the law has not: the garden adds it. Each hour's heights are a series on the candle's own
bean; the ruler reads to a fifth of a millimetre, and every height carries that uncertainty. The beeswax candle came to
be through Sam's own hands.

<!-- example-front-matter: VOCAB.md -->
```yaml
kinds:
  - { kind: material, nature: body, level: material, meaning: "a body of matter kept and used: a candle" }
```

<!-- example: beans/candle-beeswax.md -->
```markdown
---
bean: candle-beeswax
kind: material
title: "candle-beeswax — a pillar candle of the co-op's wax"
summary: "A beeswax pillar candle, its height read each hour as it burns."
statements:
  - read: { by: sam, at: now }
  - name: { by: sam, of: self, as: CANDLE-BW-01 }
  - own:  { by: sam, of: self }
  - come: { by: self, through: [sam] }
  - record:
      id: burn
      of: self
      series:
        grid: { of: time, in: gregorian-civil, every: { count: "1", unit: h }, from: "2026-11-01 18:00+01:00" }
        unit: h
        holds:
          - { name: height, quantity: length, unit: mm, stands_for: point, between: linear, u: { count: "0.2", unit: mm } }
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
kind: material
title: "candle-paraffin — the shop's paraffin candle"
summary: "The paraffin pillar candle the shop sells, burnt beside the beeswax one."
statements:
  - read:    { by: sam, at: now }
  - name:    { by: sam, of: self, as: CANDLE-PF-01 }
  - own:     { by: sam, of: self }
  - acquire: { of: self, from: { someone: org }, as: bought, note: "bought at the shop" }
  - record:
      id: burn
      of: self
      series:
        grid: { of: time, in: gregorian-civil, every: { count: "1", unit: h }, from: "2026-11-01 18:00+01:00" }
        unit: h
        holds:
          - { name: height, quantity: length, unit: mm, stands_for: point, between: linear, u: { count: "0.2", unit: mm } }
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

What share of each candle burnt away is a **reading**, step by step: its first height and its last, their difference,
and that divided by where it began. The two shares compared say whether the beeswax burnt down no faster; compared
within a band, whether the two burnt down alike within a hundredth. Where the uncertainty is too wide to decide, the
answer is NOT KNOWN — never rounded to either. The shop's order is a clause in force while the first reading holds:
because the candles say so, not because anyone set it. Each reading is a `reckon` statement, its series named as the
statement that records it, `candle-beeswax#burn`; the clause's condition is its form's `when`, the reading that brings
it into force.

<!-- example: beans/candle-supply.md -->
```markdown
---
bean: candle-supply
kind: contract
title: "candle-supply — beeswax candles for the shop in town"
summary: "The shop orders Sam's beeswax candles if they burn down no faster than its paraffin ones."
statements:
  - say:        { by: sam, at: now }
  - own:        { by: theone, of: self }
  - answer:     { by: sam, of: self, as: law }
  - agree:      { by: sam, of: self, through: spoken, as: maker, at: 2026-10-28 }
  - agree:      { by: { someone: org }, of: self, through: spoken, as: buyer, at: 2026-10-28, note: "a candle shop in town" }
  - pay:        { id: forty, by: sam, to: { someone: org }, of: { count: "40", unit: "{item}" }, note: "forty beeswax candles, to the shop" }
  - obligatory: { id: first-order, of: forty, through: self, note: "the shop orders forty beeswax candles", clause: { when: { selection: burns-no-faster } } }
  - reckon:
      id: worn-beeswax
      reading:
        what: "the share of the beeswax candle burnt away"
        steps:
          - { id: first, op: window, series: "candle-beeswax#burn", by: first }
          - { id: last, op: window, series: "candle-beeswax#burn", by: last }
          - { id: gone, op: difference, of: first, with: last }
          - { id: worn, op: divide, of: gone, with: first }
  - reckon:
      id: burns-no-faster
      reading:
        what: "whether the beeswax burnt down no faster than the paraffin"
        steps:
          - { id: bw-first, op: window, series: "candle-beeswax#burn", by: first }
          - { id: bw-last, op: window, series: "candle-beeswax#burn", by: last }
          - { id: bw-gone, op: difference, of: bw-first, with: bw-last }
          - { id: bw, op: divide, of: bw-gone, with: bw-first }
          - { id: pf-first, op: window, series: "candle-paraffin#burn", by: first }
          - { id: pf-last, op: window, series: "candle-paraffin#burn", by: last }
          - { id: pf-gone, op: difference, of: pf-first, with: pf-last }
          - { id: pf, op: divide, of: pf-gone, with: pf-first }
          - { id: slower, op: compare, of: bw, with: pf, is: at-most }
  - reckon:
      id: alike
      reading:
        what: "whether the two burnt down alike, within a hundredth"
        steps:
          - { id: bw-first, op: window, series: "candle-beeswax#burn", by: first }
          - { id: bw-last, op: window, series: "candle-beeswax#burn", by: last }
          - { id: bw-gone, op: difference, of: bw-first, with: bw-last }
          - { id: bw, op: divide, of: bw-gone, with: bw-first }
          - { id: pf-first, op: window, series: "candle-paraffin#burn", by: first }
          - { id: pf-last, op: window, series: "candle-paraffin#burn", by: last }
          - { id: pf-gone, op: difference, of: pf-first, with: pf-last }
          - { id: pf, op: divide, of: pf-gone, with: pf-first }
          - { id: same, op: compare, of: bw, with: pf, is: equal, band: { count: "0.01", unit: "1" } }
---
Agreed at the shop, the trial to decide.
```

`python3 bin/daftar.py reckon candle-supply#worn-beeswax` reads 0.225, with its uncertainty and every step it took;
`candle-supply#burns-no-faster` is true, and `candle-supply#alike` is false — two and a half hundredths apart. Nothing is
written back: change a height and the next reading says so.

## What harm can come of: sealed before it is committed

A value that could harm a person if it left the garden — a code of a scheme the garden marks special-category, a
reading of a body — is SEALED before the commit that would carry it, and the gate refuses it unsealed. A sealed
statement keeps its verb and its id, and holds in place of its roles a pointer to a store this host keeps off git —
`held: "root:<root>/<32 hexadecimal digits>"` — and the word it is held on, `while` a statement holds: here Lale's own
`agree` to her employment. Nothing else goes beside it: a note that said what is sealed would say it in git.
`python3 bin/held.py put <bean> <id> --basis <bean>#<their agree> [--until <day>]` moves what it said to the store,
with the day it is to be erased by, mints the pointer, and prints the one journal line the save carries, `- held:
<bean> <id> added`; the gate refuses a seal the entry does not say, and the hook a pointer the store here does not
hold. So the order is: write, seal, save.

<!-- example-statements: beans/lale.md -->
```yaml
  - measure: { id: back, held: "root:personal/7f3c9a1e0b2d4c6e8a9f1b3d5c7e9a0b", while: "lale-employment#employed", why: "special-category, held on her employment" }
  - say:     { by: sam, of: [back], at: now }
```

A statement added to a bean already saved comes with the act that knows it, as here: the act the bean already holds
knew only what was there when it was made.

A value committed before it was sealed is in the history of every clone, every bundle and every hub the garden was
pushed to, and a seal made now takes none of it back. Taking it out rewrites the history, which is the gardener's
decision and the work of everyone who holds a copy:

1. Seal it, and save: the tree no longer carries it.
2. In one clone, rewrite every commit that held it — `git filter-repo --replace-text <a file of the values>` (a tool of
   its own, not part of git) does. Every commit from the first that held it gets a new id.
3. Replace every other copy: push the rewritten history to the hub with `--force`, and have each other clone deleted and
   cloned again. A copy that is not replaced still holds the value, and a merge from it brings it back.
4. Say what was done in the journal, by path and never by value.

## A value the law does not have yet

First ask whether it is a value at all. The NAS runs its vendor's operating system, which no table of the law lists: but
what a machine runs is a being, so the OS is a bean of its own, and the NAS `run`s it. Nothing in the law changes.

A value that is a row of a table the verbs name — a job, a form of words, a sensitivity — is added **for this garden**
in `VOCAB.md`, under `tables`, and proposed upstream if others will need it (`CONTRIBUTING.md`). The NAS also keeps the
laptop's backups, a job the `jobs` table has not. Editing `VOCAB.md` changes the law, so the entry that goes with it
says RULE-CHANGE; commit the row with the first bean that uses it, as one change.

<!-- example-front-matter: VOCAB.md -->
```yaml
tables:
  jobs: [backup-target]
```

<!-- example: beans/nas-os.md -->
```markdown
---
bean: nas-os
kind: program
title: "nas-os — the NAS vendor's operating system"
summary: "A vendor's Linux-based NAS operating system."
statements:
  - read:     { by: sam, at: now }
  - classify: { of: self, as: "technology:linux" }
---
The NAS's operating system.
```

<!-- example: beans/nas.md -->
```markdown
---
bean: nas
kind: host
title: "nas — Sam's home NAS"
summary: "A NAS at home: file storage, and the web server for example.org."
statements:
  - read:   { by: sam, at: now }
  - name:   { by: unknown, of: self, as: NAS-0042, note: "the serial on its label; its maker is not recorded" }
  - name:   { by: sam, of: self, as: nas }
  - own:    { by: sam, of: self }
  - answer: { by: sam, of: self, as: keeping }
  - do:     { by: self, as: file-server }
  - do:     { by: self, as: web }
  - do:     { by: self, as: backup-target }
  - run:    { by: self, of: nas-os }
details:
  provides_habitat: linux-baremetal
---
The NAS.
```

If a later release adds the same row to the law, the gate refuses the garden's copy as a second row of one name: delete
it then.

## A kind of fact the core has no verb for

First look again: most facts are statements of a verb the law has. That a machine is rented, from whom, and when the
next rent falls due is `acquire … as: rented` and a `pay` with its day:

<!-- example-check: beans/vps-a.md -->
```yaml
  - pay:    { id: rent, by: sam, of: unknown, at: 2027-01-15, note: "the next rent, to the hosting provider" }
```

A fact no verb says is kept in `details`, whole, until it recurs. When it does, give it a verb **in this garden**: a row
of `VOCAB.md`'s `verbs`, in the form of `core/law/verbs.yaml` — its `meaning`, the roles it takes and what fills each
(`shape`: being, statement, position, quantity, row or text, and `many` where it takes a list), and which are
`required` — as the tile workshop's `leave` and `teach` are, above. A row is law, so it is a RULE-CHANGE, and the gate
enforces it the moment it is committed, with no code anywhere. A row that proves general is proposed to the core.

## A page of drawings (`view` profile)

A page draws what the garden keeps — a procedure, a machine — at four lenses: a story for a newcomer, the drawing itself,
its vital sign for whoever is on call, and a card of each part's own facts. It is the `view` profile, whose verb is
`draw`, and its asset, `assets/view/`. Today opting in is `python3 bin/dmupgrade.py <the release GARDEN.md records>
--extend view`, a RULE-CHANGE that brings the asset. The drawings are the garden's own code: copy
`assets/view/templates/drawings.py` to `drawings/bakery.py` and draw with the kit it imports. What a page says of each
drawing is kept in `details` until part 11 of v1 ports the asset. A machine the page draws, and the page:

<!-- example: beans/oven-a.md -->
```markdown
---
bean: oven-a
kind: host
title: "The bakery's first oven"
summary: "The oven that bakes the morning's orders."
statements:
  - read: { by: sam, at: now }
  - name: { by: unknown, of: self, as: SN-OVEN-0042, note: "the serial on its plate; its maker is not recorded" }
  - own:  { by: sam, of: self }
---
The first oven.
```

<!-- example: beans/bakery-page.md -->
```markdown
---
bean: bakery-page
kind: service
title: "The bakery, drawn"
summary: "The page of drawings of the bakery's orders."
statements:
  - say:  { by: sam, at: now }
  - own:  { by: sam, of: self }
  - be:   { by: self, at: "uri:https://bakery.example.org/drawings/", as: location }
  - draw: { by: self, of: [oven-a] }
details:
  view:
    drawings: file:drawings/bakery.py
    reference:
      - { being: oven-a, what: "bakes the orders" }
  views:
    orders:
      draws: oven-a
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

Today `python3 assets/view/bin/dmview.py check`, and `python3 assets/view/bin/dmview.py report --out map/bakery.html`
for the page itself. A button (`actions`) asks the host for a tool by name; only the host's own configuration makes a
tool run anything.

## Say what a thing is, in the world's shared terms (`knowledge` profile)

A code of a scheme of our knowledge tree is one value wherever it is written, `<scheme>:<code>`. `classify` says what a
being is; `use` says what it rests on — a technology, a field of knowledge. The gate checks every code against its
scheme, and an invented code is refused.

<!-- example-check: beans/nas.md -->
```yaml
  - use:      { by: self, of: "technology:samba" }
  - use:      { by: self, of: "isced-f-2013:0612", note: "network file sharing" }
```

<!-- example-check: beans/sam.md -->
```yaml
  - classify: { of: self, as: "isco-08:2522" }
```

Today `python3 bin/dmknowledge.py find <word>` finds a code, and `show <scheme> <code>` shows its ancestry and, for a
technology, its official documentation.

## Where each amount belongs: analytic accounting (`accounting` profile)

Keep your plans and their accounts as a scheme of your own, in `VOCAB.md` and a file beside it — a plan is a code at the
first level, an account one beneath it. A garden's own scheme is a row of the core's `schemes`, and its file a row of
`files`:

```yaml
schemes:
  - { scheme: analytic, classifies: "where this garden's amounts belong", holding: extract, publisher: the gardener,
      url: "file:extracts/analytic.tsv", levels: [ { level: plan }, { level: account } ], neighbours: none,
      sources: extracts/analytic.tsv }
files:
  - { registry: analytic, file: extracts/analytic.tsv, key: code }
```

`extracts/analytic.tsv` holds `code`, `level`, `parent` and `name`, one account a row; a new account is a new row, saved
with its journal entry like any other write. Then a payment is `book`ed where it belongs, each plan on its own, in
shares of whole parts:

<!-- example-check: beans/vps-a.md -->
```yaml
  - pay:  { id: september, by: sam, of: { count: "100.00", unit: TRY }, note: "the server's rent for September" }
  - book: { of: september, to: "analytic:orchard", share: "60" }
  - book: { of: september, to: "analytic:workshop", share: "40" }
  - book: { of: september, to: "analytic:engineering", share: "1" }
```

What an account holds is read, never stored: `apportion`, a step of a reading (`python3 bin/daftar.py reckon`).

| an ERP's analytic accounting | daftar |
|---|---|
| `account.analytic.plan` | a code at level `plan` of the garden's analytic scheme |
| `account.analytic.account` (`code`, `plan_id`) | a code at level `account`, its `parent` the plan |
| `account.move.line.analytic_distribution` | `book` statements of the payment — a percentage is a share |
| budget lines of an analytic account | `book` statements of the clause's payment |
| `account.analytic.line` | not stored: read from the payments each time it is asked |

## Where a thing is, and what it takes there

A being is placed in, at or among another, by `be`, and `as` says how, from the most general to the most bodily:
**place**, the ancestor of them all; a code's **order** among others; a record's **presence** in a register; a
process's **habitat** in its machine; a **location**, a position in a place system. What a being can hold is `hold`: a
rack's slots, a disk's bytes. What a placement takes of it — a share, or room no other takes at once — is in its form,
`placed: { takes: [ … ] }`, each a quantity in a unit of what the host holds; the gate sums what is placed as room in a
host, exactly, and refuses more than it holds. A share may be promised past it, as a hypervisor overcommits its
memory.

<!-- example: beans/rack-a.md -->
```markdown
---
bean: rack-a
kind: host
title: "rack-a — the office rack"
summary: "The office rack, 42 slots."
statements:
  - read: { by: sam, at: now }
  - name: { by: unknown, of: self, as: RACK-0001, note: "the serial on its label; its maker is not recorded" }
  - own:  { by: sam, of: self }
  - hold: { by: self, of: { count: "42", unit: "{item}" }, note: "its slots" }
---
The rack.
```

A machine in it is at its slot: the rack is the being, and the slot a position of the rack's own frame (`rack-a#u17`).

<!-- example-check: beans/nas.md -->
```yaml
  - be:     { by: self, at: [rack-a, "rack-a#u17"], as: location, placed: { takes: [ { count: "2", unit: "{item}" } ] } }
```
