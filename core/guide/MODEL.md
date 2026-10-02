# daftar — the model

A ledger that people and AI agents both read and write: plain files in git, every fact one statement, every change
checked by a gate and recorded in a journal. What daftar holds to is `MANIFESTO.md`; this document is the law beneath
it. The words the gate knows are the core, `core/law/core.yaml`, and every other word is a row beside it in
`core/law/`. Why each rule exists is in `seed/RATIONALE.md`, keyed by the rule's own path.

## The root
- **The dot.** A position is a dot, without parts in its own system. What is divided keeps its order and its wholeness.
- **Two frames.** A body takes room in **space∞time**: one structure with two faces, place and time, neither without
  the other. A sayable takes a place in the **taxis** (τάξις, an order): its positions say *which* — the third clause,
  article 12, a name in its namespace — and are no time and no place. Neither frame is prior.
- **The ladder.** What stands on what, from the frames to the crown, on seven lines: the frame; matter; gravitation;
  the living, possible on a world in **balance**; reason (λόγος), possible on a living organism in **proportion**; the
  made; and the said, which runs name → statement → discourse → corpus. Each step stands on another `made-of` (the
  lower is in it) or `possible-on` (the lower is its condition, `while` the condition holds). A part never stands above
  what its whole is made of, and nothing stands on itself through others.
- **Weight.** What holds at a step holds for all that stands on it. Every body has weight; a sayable has none of its
  own.
- **The life chain.** A being came to be through others (`come`): born of, made, said, started. A living being comes
  through the living; a made or said one through hands — a being at reason — or through a tool whose own coming goes
  on. Every chain ends at the crown, `theone`, the Necessary Existent, with two faces, love and wisdom. Nothing demands
  a chain: a being that states none is held at the crown all the same.

## Beans and gardens
- A **bean** is one being — a machine, a domain, a program, a person, a contract — as one file, `beans/<id>.md`. Its
  front matter holds a header and its statements; its Markdown body is for people. A procedure or a relationship that
  is no thing is a bean under `mappings/`, of a kind the garden declares.
- The **header** is `bean` (the file's name), `kind`, `title`, `summary`, `tags`, and `details`: what fits no verb yet,
  kept whole until a verb is proposed for it. Nothing else stands beside `statements`.
- A **garden** is a git repository of beans: one ledger. `GARDEN.md` names it, names its gardener, pins the law it
  runs (`extends: core@<version>`, the law's own version), records the release (`daftar_release`) and the zone its days
  are reckoned in (`zone`); it may say what it rehearses (`test`), where it began (`origin`) and the gardener's standing
  rules (`policy`), and holds no other key (`core/law/core.yaml`, `manifest`). A garden is known by its id, read from git and never written as its own: the first twelve hexadecimal
  digits of the root of its first-parent history, a name of the namespace `garden-id`.
- A garden is kept by its **gardener**, a person or an organisation it holds a bean for. The gardener ratifies; an
  agent tends the garden, and proposes what is not its to decide (manifesto: parts). A garden is written by its own
  writers alone (manifesto: gardener).
- The **seed** (`seed/`) is the kit a garden is grown from.

## The statement
Every fact is one statement: a **verb** and its **roles**.

```yaml
- pay: { id: paid, by: ada, of: { count: "10.00", unit: XTS }, at: 2026-09-20 }
```

| Role | What fills it |
|---|---|
| `by` | who does it, or the subject of a verb that takes no object (Pāṇini's *kartṛ*) |
| `of` | what the act reaches, or what it is about (*karman*) |
| `through` | the means: a tool, a document, words, a link, a course, an agreement, a cause (*karaṇa*) |
| `to` | for whom, or towards what (*sampradāna*) |
| `from` | the fixed point it departs from: a source, a giver, a parent (*apādāna*) |
| `at` | the locus: a position in a frame, or the being a thing stands on, runs on or is kept at (*adhikaraṇa*) |
| `as` | in what capacity, or as what: the name given, the job done, the way a thing stands (Aristotle's *qua*) |

- A filler is a **being** (a bean; `self`, the being this bean records; the crown; or `{ someone: <kind>, at: <a being
  or a place> }`, one nobody names), a **statement** (its `id`, or `<bean>#<id>` in another bean), a **position**, a
  **quantity** (`{ count, unit }`), a **row** of a table the law keeps, or **text**.
- A role takes one filler, a list where its verb's row says `many`, or a map where it says `keyed`.
- Beside its roles a statement carries the qualifiers its verb's row declares (`share` on `bear`), and four keys:
  `id` (its name in the bean, one word), `while` (it holds while a condition or another statement matches), `why` and
  `note` (prose). Nothing else — but a **sealed** statement, which keeps its verb and its id and carries `held`, a
  pointer, in place of its roles (*Who may see*, below).
- `unknown` fills a required role nobody has said. A role that is not required is left out instead.
- `now` is the moment of the save, written at `at` alone; the save writes the moment in its place.
- Every key and value is read as a string, as YAML 1.2's core schema reads it: `on` is a word, not `true`, and
  `2026-10-01` is text in a calendar's form, not a date object.
- The comparators are named by their Unicode signs: `= ≠ < ≤ > ≥ ∈ ∃ ∄`.

## Knowing: who said it, and how they know
A statement is in the ledger because someone **said** it, **read** it, **made** it or **derived** it (manifesto:
provenance). These four verbs are the knowing acts; each takes statements as its `of`.

```yaml
- say:  { by: sam, of: [agreed, paid], at: now }
```

- A knowing act with no `of` covers every statement of its bean that no other act covers. Every statement is covered.
- A knowing act's `at` is written `now`, and the save writes the moment in its place. A moment typed there is refused:
  only the clock supplies it.
- `say` is by a person (a body at reason) or a document (a sayable). `read` is by a body. `derive` is computed from
  what was given — a count, a digest, a merge, an inference — and names it, `from`: it holds nothing its inputs did not,
  and is no better than they were. `make` is made here from nothing given: prose written, a name minted.
- **An agent's act is its session's.** An act an agent made is `by` the session bean it ran in, the one whose start and
  stop hold the act's moment; an agent's reading is `derive`, since `read` takes a body. Where no session holds it, the
  act is `by: unknown`, the agent named in its `note`.
- **Two knowers stand side by side.** Two statements about one thing, said by two knowers, both stand; neither
  overrides the other, whatever precision it claims (manifesto: never-overrides). A disagreement needs no marker. A
  person settles it with a `rule` statement, which names the statements disputed and the one chosen.
- **A judgment is its judge's** (manifesto: judge). That one version is better, clearer or more beautiful than another
  is a statement its judge `say`s, with its reason in `why` — never a property of the thing, and never derived. Whose
  judgment decides for a being is whoever `answer`s for it in the mode the judgment concerns, and under an agreement
  whoever its statements name.

## Verbs and their rows
A verb is a row with its valency: the roles it takes, what fills each, which are required, the qualifiers it allows,
and the default it derives where it has one.

```yaml
- verb: bear
  roles: { by: { shape: being }, of: { shape: statement } }
  qualifiers: { share: { shape: quantity } }
  required: [by, of]
```

- **The face's 21 verbs** (`core/law/core.yaml`): the knowing acts `say` `read` `derive` `make`; the order `be` (where
  a being is), `stand`, `part`, `name`; the four questions `come` `own` `answer` `acquire`; the layers' `pass`; and
  the two squares' eight positions.
- **The 35 rows** (`core/law/verbs.yaml`):

  | Group | Verbs |
  |---|---|
  | agreements, money, permission | `agree` `decline` `pay` `bear` `grant` `can` `represent` |
  | what a being needs, does and holds | `need` `meet` `use` `do` `hold` `run` `open` `move` `attend` `produce` |
  | knowing about a being | `measure` `classify` `concern` `rate` |
  | failure and remedy, disagreement | `fail` `repair` `rule` |
  | between gardens | `propose` `take` |
  | the network profile | `serve` `carry` `route` `translate` `filter` |
  | the other profiles | `book` (accounting), `renew` (domain), `mark`, `draw` (view) |

- **A default is never written.** Where a row derives a statement — before the law, the owner answers; whoever paid
  bears it, alone — writing that statement is refused as a placeholder.
- **A new relation is a new verb**, proposed and ratified as the law is. There is no open relation: every relation is a
  statement of a verb the law has.

## The order
- **being**: what is. Its record is a bean.
- **nature**: **body** (takes room in space∞time) or the **sayable** (takes a place in the taxis, and stands on reason).
- **kind**: a row of `core/law/kinds.yaml`, or of the garden's VOCAB.md: its nature, and its line and level, or its
  rung. `host` and `person` are bodies — a host a device, a person an organism at reason; `codebase`, `product`, `org`,
  `instance`, `virtual-host`, `domain`, `service`, `program`, `design`, `session`, `contract`, `garden`, `document`
  and `event` are sayables. A kind's level is on a line that holds its nature.
- **stand**: the one relation of the order, `stand: { by: cell, at: molecule, as: made-of }`.
- **part**: `part: { by: wheel, of: car }`. A part never stands above what its whole is made of.
- **line**: an ordered run of positions. Time is a line, and so is a walk.
- **level**: a step of a line. The face keeps the two frames, reason and the said's four levels; the bodies' other 22
  are rows of our knowledge tree (`core/law/levels.yaml`).
- **The squares.** A figure is a square of opposition whose four positions are verbs over a statement:

  | Square | Contraries | Subcontraries |
  |---|---|---|
  | necessity | `necessary` · `impossible` | `possible` · `contingent` |
  | permission | `obligatory` · `forbidden` | `permitted` · `omissible` |

  Contraries cannot both stand, nor contradictories (`necessary` · `contingent`, `obligatory` · `omissible`), on one
  statement through one source; subcontraries can. A `necessary` statement names what it is necessary `through`,
  except of the crown: `necessary: { of: theone }`. A risk is `possible` of a failure; a clause is a statement on the
  permission square, `through` the agreement that asks it.

## The four questions
Four things are asked of every being, each its own statement, never one:

```yaml
- come:    { by: self, through: [ { someone: person, at: maker } ] }   # through whom it came to be
- own:     { by: sam, of: self }                                       # whose it is
- answer:  { by: sam, of: self, as: keeping }                          # who answers for it, and in which mode
- acquire: { of: self, from: shop, as: bought, at: 2025-03-01 }        # from whom it came to us
```

- **Whose it is — `own`, one owner, no modes.** `by` the owner; or `from` the parent a being is owned through (an
  instance through the product it runs); and `through` the agreement, where its owners own it together. An owner
  outside the ledger is still a being: a bean for the provider, the authors, the registry. A **person** is owned only by
  the crown, `own: { by: theone, of: self }`: no bean holds a person. An **agreement** may be owned by the crown, and a
  **happening** between people (an `event`) too. The crown owns and never answers.
- **Who answers for it — `answer`, one statement per mode**, `as` one of four: `law` (before the law), `keeping` (who
  runs and keeps it), `meeting` (how others meet it), `paying` (who pays for it).
  - Before the law, the owner answers. That is derived, never written; an `answer` `as: law` is written only where
    another answers: a person for themselves (`by: self`), each party of a crown-owned agreement, the host of a
    happening, a keeper who takes it over.
  - `keeping` stands only on what runs or is kept; nobody keeps a record.
- **From whom it came to us — `acquire`**, `as` one of bought, rented, given, lent, inherited, `from` the vendor or
  the giver, `at` the day, `through` the agreement. The seller of a server is neither the hands that made it (its
  `come`) nor its owner.
- Ownership is not place: an instance is owned through its product and `be`s `at` the machine it runs on. Moving a
  machine changes where things are, never whose they are.

## Agreements and money
- **An agreement** is a bean of the kind `contract`. Each party `agree`s, `of` what it concerns, `through` its words
  (`written`, `spoken`, `unstated`, or the document or event that holds them), `as` its part in it (lender, tenant),
  `at` the day it said yes. A party that said no `decline`s.
- **An offer is not an acceptance.** An `agree` is a party's yes. The day nobody said is left out; one placed only by
  what it followed is written so, `at: "after:<bean>"`. One party's report of another's yes is the reporter's word,
  and the knowing act that covers it says so.
- **A clause is a statement on the permission square**, `through` the agreement: `obligatory: { of: rent, through:
  agreed }`, where `rent` is the `pay` it asks for. Each clause asks one statement; what it holds beside — the day it
  falls due, how it repeats, when it falls due relative to another position, how long before a reader is told, its
  window, an allowance, what it occurs for, what brings it into force — is its form, `clause` (core/law/measures.yaml),
  on the position on the square (or on a `can`, a clause in its words alone), judged by rule `measured`.
- **Money is a quantity.** An amount is `{ count, unit }`: the unit a currency of ISO 4217, the count plain decimal
  digits with no more places than the currency uses. A count or a share is what was written, never converted. No
  factor joins two currencies: a rate is a `measure` someone made, at a moment, from a source.
- **Who paid and who bears it** are statements: `pay` (`by` the payer, `of` the whole amount, `to` the payee,
  `through` what it was paid under) and `bear` (`by` each who bears it, `of` the payment, `share` their part). Whoever
  paid bears it alone unless a `bear` says otherwise.
- **A balance is read, never written.** What one party owes another is computed from the payments and the clauses
  (`python3 bin/daftar.py ledger`, from each `pay` and `bear`), exactly, in fractions; a stored balance is a second copy, and it drifts. Who takes
  a remainder is a clause, never arithmetic.
- **A party may act for another** (`represent`): what it does binds that one.

## Place and time
- **`be` says where a being is**: `at` a position, or at a being — the rack a machine stands in, the machine a program
  runs on, the register a record is in — and `as` the way it is placed: `place`, the most general; a code's `order`
  among others; a record's `presence` in a register; a process's `habitat` in its machine; a `location` in a place
  system, measured from its datum.
- **A position is a dot in a system**, written in that system's one form: `2026-10-01`, `persian:1405-07-09`,
  `"2026-09-12 19:30+03:00"`, `192.0.2.10`, `tcp-port:445`, `ordinal:3`. Where two systems read one spelling, it
  carries its system's name before a colon (`uri:https://example.org`); a spelling no system reads is refused. The
  systems are the standards' (`core/law/`): calendars, reference systems, filesystems, address spaces,
  the ordinal line.
- **An extent** is two positions of one system, as ISO 8601 writes an interval: `2026-10-01/2027-09-30`,
  `persian:1405-07-09/1406-07-08`.
- **A day finds its other half** by its system's complement: stated (an offset), the bearer's (the garden's `zone`),
  or the system's. A day in a garden that names no zone is refused.
- **A day nobody said** is placed by what it came after or before, `"after:<bean>"` or `"before:<bean>"`: it orders
  and names no day.
- **What a being can hold** is `hold`: `hold: { by: nas, of: { count: "2", unit: TBy } }`, read beside what is placed
  in it.
- **Two bodies are not in one room at once.** Two `be … as: location` at one position — a rack's slot, an address —
  are refused unless one is part of, or at, the other (a sayable takes no room); so are two listeners at one port on one address; and a being
  attending two happenings whose times, to the moment, overlap. A garden may declare a verb **exclusive** in its
  `VOCAB.md` (`exclusive: [ { verb: attend, why: … } ]`): then one being holds it once over any extent of its `at`,
  across every bean, and what was declined holds nothing.

## Names: what establishes an identity
A name is a statement: the namespace gives it.

```yaml
- name: { by: lenovo, of: self, as: "PF-12345" }        # a maker's serial
- name: { by: dns, of: self, as: "example.org" }        # a domain name
```

- A namespace is a row: the standards' are the core's (`core/law/namespaces.yaml`: `dns`, `mail`, `e164`,
  `ieee-eui48`, `uuid`, `sha-256`, `openpgp`, `ssh`, `wireguard`, `garden-id`, `garden`), and a garden adds its own
  in VOCAB.md — a maker's serials, an employer's numbers — named for whoever gives them.
- A namespace's row says whether it gives a name **once**. A name given once names one being, and that is what
  establishes an identity: the gate refuses one name given once to two beings.
- In its own garden a being's name is its bean. A name that is to cross to another garden is qualified by the garden
  that gave it, `name: { by: garden, of: self, as: "<garden_id>/person:sam" }`, and a garden that takes it in keeps it
  byte for byte: its id is this garden's, or one a `garden` bean here is named by. An identifier someone else assigned
  — a package's name, a registry number — is that registry's name, and nobody's to qualify.
- A garden's id (`garden-id`) is twelve hexadecimal digits, and never this garden's own: a `garden` bean records
  another garden.
- Choosing or settling a name that establishes an identity is the gardener's (class F).

## What a being is, measured, coded and used
- **`measure`** reads a property of a being (ISO 19156): `of` the being, `as` the property, its `value`, `at` the
  moment, `through` the instrument, `by` the observer. A reading made again is a new statement; change is read, never
  stored. A unit is UCUM's code (`kg`, `GiBy`, `Cel`), its English name the law's (`core/law/units.yaml`).
- **`classify`** says what a being is in the world's shared terms: a code of a scheme of our knowledge tree,
  `<scheme>:<code>` — `isco-08:2522`, `isced-f-2013:0612`, `technology:samba`. **`use`** says what it rests on: a
  technology, a field. Every code is checked against its scheme; an invented code is refused. The schemes are kept
  whole in `seed/knowledge/`, each under its own licence, and read by today's `python3 bin/dmknowledge.py`.
- **Readings** — how many, whether any, which first, how much — are asked of the garden each time and never written
  back as statements (`python3 bin/daftar.py reckon`). A reading is declared by `reckon`, its steps in its `reading`;
  what rests on one is fixed by `pin`, the moment it was read at and the commit, `<garden>@<object id>`.
- **Lines.** What a line held at each position is a series, `record`; a walk is a mapping's `step` statements, a case
  on it a `be` as order, and where it stands is read from its `move`s (`python3 bin/daftar.py seq`). Each line's own
  structure is a value in a form of core/law/lines.yaml, and rule `line` judges it. A region of a line (`extent`) and a
  repetition along one (`recurrence`) are forms of core/law/measures.yaml; how well a value is known is inside it (`u`,
  or `accuracy` with its kind); and what a placement holds there — what it takes of its host, how well its position is
  known, its window — is `be`'s form `placed`. Rule `measured` judges them, and sums what is placed as room in a host
  against what it `hold`s.

## Layers, standing and the law
- **The layers**: manifesto, law, reasoning, journal, history, queue, names; beside them the sources the flow law adds
  (`core/law/layers.yaml`). The MANIFESTO says what daftar holds to, one clause to a sentence, and the gate never
  applies it: the law carries it, and a document names the clause it carries, `(manifesto: <key>)`. LAWS are clear
  and brief. REASONING is their backbone (`seed/RATIONALE.md`). JOURNALS are the leads reasoning is drawn from.
  HISTORY is the exact record they are written from.
- **Standing** is the law's own: the layer a file sits in. A file stands in one layer.
- **A pass** moves statements from a layer to a layer by a method, `pass: { of: [r1], from: world, to: estate,
  through: record, as: read }` — into the estate, `as` the act it is known by there — and stands only where the flow
  table grants it (`core/law/flows.yaml`): of the rows that hold it the nearest decides, a row that names `as` nearer
  than one that names only layers, and of two as near, a refusal. A row `ratified` is refused until a garden's own row
  grants the party it names, with the basis it grants on; a garden's own rows otherwise only refuse.
- **A session's pass log** (`captures/passes/<slug>.jsonl`, which the session's bean names in `details`, `pass_log: {
  requests: { holds: "file:<path>" } }`) holds what its launcher (`bin/launch.py`) and its save logged, one pass to a
  line, in the pass's valency with where it came from and went: `{"from": {"layer": "words"}, "to": {"bean": "lease",
  "at": "agree#a1.at"}, "through": "say", "as": "say", "metadata": {"quoted": 1}}` — a file `{file}`, a value `{bean,
  at}` at its statement's path, another garden `{garden}`, a layer that holds no files `{layer}`; `metadata` only the
  counts and ids `core/law/flows.yaml` names, never the material. A commit that stages the log claims the session:
  the log only grows, each pass it gains is granted, every said value the commit adds — a role of a statement a `say`
  knows — has a granted pass into it (the save traces each one), and a `say` by a person it adds has a pass from
  `words` or `instructions` into its bean.
- **The law** is `core/law/*.yaml`, this document, `CHECKLIST.md`, `MERGE.md`, `VOCAB.md`, `GARDEN.md`, the standards'
  tables in `seed/knowledge/`, and every file a release keeps (`seed/LANGUAGE`). A change to any of them is a
  RULE-CHANGE, which a person ratifies.
- **`VOCAB.md`** is the garden's own rows, under these keys only: `kinds`, `levels`, `namespaces`, `flows`,
  `flow_sources`, `standing`, `verbs`, `units`, `tables` (rows added to a table the verbs name), `exclusive`, and a
  system of positions, a scheme of codes and the files they name of its own (`systems`, `schemes`, `files`) — and the
  profiles it takes, by their names (`profiles`). A row
  never takes a name the law has: one name, one row. **Every row the garden adds is used** by a statement or a bean, or
  says why it is vacant (`vacant: <why>`), the manifesto's `whole`: a row is added with the first bean that uses it.
- **Profiles** — network, domain, accounting, view, knowledge, code — stand on the core (`core/law/profiles.yaml`):
  their verbs are rows of `core/law/verbs.yaml` marked with their `home`, their tables, forms and words their own, and
  what one adds to a form of the core (the code profile's attributes of a placement) is named. A garden **takes** a
  profile by its name in `VOCAB.md`'s `profiles`, a RULE-CHANGE, and uses none of a profile it does not take (rule
  `profile`). A profile may bring an **asset**, `assets/<profile>/`, which a garden receives while it takes the profile
  and which opens no concept of its own: the `view` profile's draws a page whose drawings are its `draw` statements.
- A garden's row that proves general is **promoted** to the standard by a pull request to the daftar repository
  (manifesto: learn-once). A mechanism that is universal may come complete before anything occupies it (manifesto: whole).

## Ground rules
1. **One statement, one place** (manifesto: once). A fact is stated in the bean of the being it is about; elsewhere it
   is taken by its id, `<bean>#<id>`.
2. **Abstraction, not force-fit — and structure before prose.** What fits no verb goes into `details`, whole: never
   bent into a verb that nearly fits, never dropped. Inside a statement there are only its roles, its qualifiers and
   the four keys; a remark goes in `note` or `why`, and a new kind of fact is proposed as a new verb or a new row
   (manifesto: structure).
3. **Reference external truth, or capture it knowingly.** A fact is stated here, pointed to where it is kept, or
   captured: a dated copy taken so something can be rebuilt, never authoritative, never applied back without reading
   the source again.
4. **Legible to people and agents.** Plain YAML and Markdown, small files.
5. **No cleverness that needs explaining.**
6. **Reads correctly cold** (manifesto: cold). Spelled-out words, explicit units, absolute positions.
7. **No secret in the ledger** (manifesto: never-secret). Nothing a garden holds carries a secret — a password, a key,
   a token, a card number, a government number. Where a secret is needed, the ledger says where it is kept, never what
   it is. Rotating one that reached the ledger is the gardener's, journalled without its value. A private key has a
   form a gate can know, and the gate refuses it in any file a commit stages; every other secret is the writer's to
   keep out.

## The Contract of Parts: who decides
This table is the one statement of who may decide what (manifesto: parts).

| | Decision | Who |
|---|---|---|
| **A** | record a newly **observed**, reversible fact | an agent alone: a statement its session derives, `at: now`, journalled |
| **B** | record an **inference** not directly observed | an agent alone: `derive`, naming what it was derived `from`; not settled |
| **C** | **change or remove** a statement | its own session's earlier statement: an agent (journal both); one a person said, or one safety rests on: **a person ratifies** |
| **D** | state or change what a **person said** (`say` by a person) | **a person only**; an agent may propose |
| **E** | change a **safety-critical** statement: a sensitivity (`rate`), a `forbidden`, a failure in progress | **a person ratifies** |
| **F** | choose or settle a **name that establishes an identity**, or take one in from another garden | **a person ratifies**: it governs every future merge |
| **G** | change **the law** — the core, a verb's row, a kind, a namespace, a flow, VOCAB.md, GARDEN.md; or a clause of MANIFESTO.md | **a person ratifies**, journalled as a RULE-CHANGE |
| **H** | a dated exception to a rule | the core's rules take none; the letter is kept so the others keep theirs |
| **I** | an **automatic merge** with no conflict | an agent alone |
| **J** | settle a **merge conflict or an uncertain identity** | **a person ratifies** |
| **K** | **journal** what was done | everyone, always |

The person who ratifies in a garden is its gardener — for an organisation, a person who answers for it — or, for a class
the gardener delegates for named beans, the person a `grant` names (`as: ratify`, `class: <letter>`). Nothing is
delegated by default. When the class is unclear, an agent proposes and a person ratifies. An agent that meets something
it may not decide parks it in `log/pending.md` as `status: proposed`, does everything safe around it, and carries on.

## The journal and the gate
- **Each change carries its journal entry**, in `log/journal.md` and in the same commit: who, what and why
  (manifesto: hidden). People record decisions and approvals; agents record what they ran, why, and what happened. A heading is
  written by the clock (`bin/journal.py`, which `bin/save.py` calls), never typed.
- **The gate** is `core/check.py`, run at every commit by the pre-commit hook `bin/hooks/pre-commit` on the staged
  files. Its twenty-one rules are strict: each breach is an error, and the commit is refused. `CHECKLIST.md`, Part A,
  lists them: the core's thirteen, and five that today's gate held — `consent`, `harm`, `room`, `vacancy`, `kept`.
- **The commit's own rules**: every bean a commit changes is named by the journal entry it adds; a statement it adds is
  known by an act it adds, at that entry's moment; a change to the law says RULE-CHANGE. Only the commit that adopts
  the core in a garden, a RULE-CHANGE, carries the moments its history recorded: `bin/dmupgrade.py <a release of the
  core>` translates the garden in place and writes its entry with the translator's count, and a person fills in who
  ratified it and why, and commits. A garden grown from a release of the core is in it from its first commit. **What is kept is not damaged**: the
  journal is appended to and never rewritten, a series' part is written once, and a commit names in its entry each
  header key or statement it takes out of a bean, empties none it keeps, and leaves every bean a body.
- These rules confirm that the words are there and well formed, not that they are true; honesty is still the writer's
  (manifesto: checked).
- Each person and each agent session commits under its own git identity, so the log's "who" is real.
- A garden with more than one writer has a hub that judges every push again (`bin/hub.py`): each commit signed
  by a key a writer's bean names (`name: { by: ssh, … }` or `openpgp`), what it changes within that writer's grants,
  and the whole garden by the gate.
- A release a garden upgrades to is authenticated before any of it runs: a signed tag against the keys the garden's own
  release names (`seed/RELEASE-SIGNERS`), or the commit a person names or confirms (`bin/dmupgrade.py`).

## Who may see, and what is held off git
- **Sensitivity is derived, never stored**: a code of a scheme the garden marks special-category makes a bean
  special-category; a bean that `concern`s a person who is not the gardener, or such a person's own bean, makes it
  personal. A person may raise it with `rate`; only a person's own word lowers it — a `rate` said by a person, never
  derived (class E).
- **Another person is kept by name only on their own word**: an `agree` of theirs, not declined, to an agreement this
  garden holds — a consent to be kept here by name is one — or, for the gardener of a garden this one has met, the
  meeting itself: the `garden` bean they `own`. Otherwise they are an opaque id (`p-<8 hex>`, its title the id), their
  name and the ways to reach them held off git. Their future whereabouts are held off git whatever they agreed to: a
  happening wholly ahead, attended by such a person, keeps its location sealed.
- **What harm can come of, git does not keep.** Special-category material is **sealed** before the commit that would
  carry it: the statement keeps its verb and its id, and in place of its roles holds `held`, a pointer to a store a
  host resolves (`root:<root>/<32 hexadecimal digits>`), and, where the bean concerns a person who is not the gardener,
  the word it is held on, `while: <their agree>`. The entry that seals or unseals one says so, `- held: <bean> <id>
  added` or `erased`. No seal takes back a value already in the history. `python3 bin/held.py` seals a statement by
  its id, mints the pointer, and keeps in the store what it said and the day it is to be erased by, which the host that
  holds it reads (`due`, `check`); the hook checks at each commit that the store here holds what it adds. The gate
  never reads a store: a gate that judged one machine's disk would pass on one and fail on another.
- **Who may do what is closed by default.** The gardener may; anyone else may what a `grant` opens — `as` read, write,
  enact or ratify, `of` the beans or statements it covers, `to` whom, `at` the extent it holds over — held by the
  gardener, by the person a record is of or concerns, or by an agreement over its own bean; a position on the
  permission square that forbids a grant refuses what it would open. `python3 bin/pass.py` reads them (`may`).

## Merging
Two branches of one garden merge bean by bean. A bean's statements are a set: what both sides hold is kept once, and
what either side added is kept, a disagreement side by side. The header and `details` merge three ways against their
common base, and a change both sides made differently to one place is a true conflict, refused for a person to settle.
`MERGE.md` states it.

## Between gardens
(manifesto: gardener)
Inside a garden is interior — its clones, its writers, its hub. Between gardens is exterior: each garden autonomous,
known by its id, and two that deal with each other peers, each configured at its own end.

- **First contact.** Another garden this one deals with is a bean of the kind `garden`, named by its id (`name: { by:
  garden-id, of: self, as: "<its id>" }`), owned by that garden's gardener and answered for by them, so that gardener
  is a bean here too, named as their own garden names them. Recording a new garden and its gardener is the gardener's
  decision (class F), made in one commit. A `garden` bean named by this garden's own id is refused.
- **A name crosses as it was given.** A thing two gardens share is named once, by the garden that recorded it first,
  qualified by that garden's id; a garden that takes it in keeps it byte for byte.
- **What passes is a proposal, never a write** (`propose`, `take`). A proposal is one file, laid outside every garden,
  for one garden, made under an agreement both gardeners `agree` to. It carries whole beans as the proposing garden
  committed them, a stub of each bean they refer to, and the journal entry that would take them in. It passes on what
  was said in the proposing garden or by the garden proposed to, and of what a third garden said only the names it
  gave: `python3 bin/propose.py make`, `read` and `take`. A being is known beyond its garden by a name a namespace
  gives once, and a stub carries those names; nothing is stamped on what crosses.
- **Knowing crosses unchanged.** A statement travels with the act that knows it, and a person's word arrives as that
  person's word. An act known in another garden keeps the moment it was known at there, and holds that garden's bean
  beside it in its `at`; the commit that brings it takes it from that garden (`take`, by the gardener, `through` the
  proposal's fingerprint), stamped by the gardener's save.
- **Taking in is a write like any other.** What a proposal brings is another person's word (class D), a name another
  garden gave (F), and every disagreement or uncertain identity (J). Reading a proposal writes nothing; taking it in
  writes in the working tree and never commits; the gardener's commit is the ratification. A proposal is taken once.
- **Taking in an agreement is not accepting it.** A party's yes is its own `agree`, recorded by its own garden in a
  commit of its own.
- **A test garden** says so in `GARDEN.md` (`test:`), and its beans are no facts about the world; a garden this one
  records as a rehearsal holds `rehearse` on its bean, and what comes from it is taken only as a rehearsal's. A rehearsal is grown,
  never cloned: a clone is the same garden, with the same id and the same word.
- **Two gardens exchange only while they run the same law** (`extends`).
