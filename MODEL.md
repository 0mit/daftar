# daftar — the model

A ledger that people and AI agents both read and write: plain files in git, every change checked by a gate
and recorded in a journal. It is meant to read correctly cold — on paper, years later — so legibility and
provenance come before brevity. Why each rule exists is in `seed/RATIONALE.md`, keyed by the rule's own path; the
design steps before that are in `HISTORY.md` in the daftar repository.

## Beans and gardens
- A **bean** is one managed thing — a machine, a domain, a program, a person, a contract — as one file,
  `beans/<id>.md`. The YAML front matter holds the facts; the Markdown body is for people. A **mapping**
  (`mappings/<id>.md`) records a procedure or relationship that is not itself a thing.
- A **garden** is a git repository of beans: one estate's ledger. `GARDEN.md` names it, names its gardener,
  pins the vocabulary version (`extends: std-vocab@<version>`) and records the daftar release it runs
  (`daftar_release`); the law's `manifest` says what else it may hold. A garden is known by the commit it
  germinated from (`garden_id`), read from git: `GARDEN.md` carries no id, and in the garden's own beans it appears
  only as the prefix of a name the garden minted.
- A garden is kept by its **gardener**: the bean `GARDEN.md` names in `gardener:`, of a kind the law's `manifest`
  admits — a person or an organisation. A garden grown with `--gardener` begins with it. The gardener ratifies what an
  agent may not decide; an agent tends the garden. Nothing outside a garden writes in it.
- `GARDEN.md` is judged as itself, against the law's `manifest`: each attribute's form, the required ones present,
  and the gardener a bean the garden holds.
- The **seed** (`seed/`) is the kit a garden is grown from. When gardens are merged, the result for each object
  is a **canonical bean** (`MERGE.md`); the merge tool prints it under the key `seed`, which is not `seed/`, the kit.

## Facts carry their provenance
A fact knows who said it and how they know.
- Each bean states a default `provenance: { src, by, as_of }`, where `src` is `observed`, `inferred`,
  `asserted-by-human` or `generated-by-tool`. The vocabulary ranks them by HOW THE FACT IS KNOWN and says why
  (`provenance_src`). A `generated-by-tool` fact has no standing of its own: it names what it was computed
  from in `provenance.from`, and weighs as the weakest of those.
- A fact whose source differs from the bean's default carries its own record. What a record may hold, and what
  each of its attributes means, is the law's `provenance_record` — among them the records a fact was taken or
  computed from, and the garden the record was made in, where that is not this one.
- **An `inferred` value never overrides an `asserted-by-human` one**, whatever precision it claims.
- **A judgment is its judge's.** That one version is better, clearer or more beautiful than another is recorded
  as a judgment — by whom (`provenance.by`), with its reason in prose — never as a property of the thing and never
  computed. A person's is `asserted-by-human`; an agent's is `inferred`, and never overrides a person's. Whose
  judgment decides for a being is its owner's, for the facet the judgment concerns, and under an agreement
  whoever its clauses name.

## Identity: anchors
Every bean has an `identity:` block of **anchors** — facts that say which object this is, so two gardens can
recognise the same thing whatever its file is called.
- Each anchor says `establishing: true` (it identifies the object) or `false` (it only corroborates).
  Only establishing anchors decide that two beans are one object.
- What establishes follows the nature: matter (`serial`, `mac`) for a physical being; a logical id (`fqdn`, a
  product or service id) for a metaphysical or living one. Network anchors (`ip`, `hostname`) corroborate. Every
  anchor's key is a term of the vocabulary, and where that term declares a policy, it overrules the bean.
- How many establishing anchors a confirmed bean needs depends on its nature. A bean below that is
  `identity.status: provisional`, and the gate warns.
- Two beans with the same establishing anchor are the same object: the gate refuses it. Serials are compared
  ignoring case and spaces.

## Type: nature, then kind
Every bean has a `nature` — `physical`, `metaphysical` or `living` — and a `kind` that refines it (`host` is
physical; `domain`, `product`, `codebase`, `contract`, `document`, `event` and `garden` are metaphysical; `person`,
`instance` and `virtual-host` are living: a virtual machine has no matter and lapses at teardown). The gate
refuses a nature that contradicts the kind. Rules about what sort of being something is — such as identity
anchors — attach to the nature, so every kind under it inherits them.

## Ownership and responsibility
Two arcs, over the same **facets** — the rows of the law's `facets` registry, and any a garden adds. A facet may
depend on others — every other facet reaches `legal` through what it depends on — but never on itself through them,
and never overlaps another:
- `owned_by` points up: each facet has **exactly one owner**.
- `responsibility` points down: each facet has **exactly one responsibility entry**, saying who answers for the
  thing — a holder, say, or the parties of an agreement, or a person for themselves.
- **Every facet with an owner has a responsibility entry, and vice versa.** The gate enforces the pairing.

The forms an entry can take:
- `{ owner: { bean: … } }` — owned by another bean. The chain must end somewhere: the gate refuses one that
  stops at a bean owning nothing.
- `{ external: "…" }` — owned outside this ledger: a rented server's provider, software's vendor, a domain's
  registry. Someone here still answers for it.
- `{ via: { bean: … } }` — inherits the parent's owners, e.g. an instance through the product it runs.
- `{ contract: { bean: … } }` — one facet owned together, through a `contract` bean: the agreement between its
  owners, whose clauses say how they decide.
- `{ crown: <branch> }` — where every chain ends. The branch follows the nature (`nature` for physical, `logos`
  for metaphysical, `love` for living); the gate checks it. A **person** is pinned to it: owned by no bean,
  `owned_by: { legal: { crown: love } }`, and answering for themselves: `responsibility: { legal: { self: true } }`.
  An **agreement** between parties may choose it: owned by none of its parties, `owned_by: { legal: { crown:
  logos } }`, and answered for by them, each for the clauses it is bound by: `responsibility: { legal: { parties:
  true } }`. A **happening** between people (an `event`) may choose it too: owned by none of those who took part,
  and answered for by whoever hosted it, as its holder. The crown owns and never answers; the parties answer and
  never own. The crown is written only by these three kinds, and `parties` only by an agreement.

Ownership is separate from **habitat**: a running instance is owned through its product, and separately
`lives_in` the machine it runs on. Moving machines changes the habitat, never the owner.

## Agreements and money
- An agreement is a `contract` bean: who it binds (`parties`), where its words are (`words`: written, spoken, or not
  yet put into words, and the `document` or `event` that holds them), what it asks of each party (`clauses`, each a
  position on the `capability` square — must, need not, may, must not — with its amount, its day, how it repeats and
  what brings it into force), and what has moved under it (`transactions`).
- **An offer is not an acceptance.** A party with `accepted` said yes on that day; a party without it has no
  acceptance on record — an offer not yet taken up, or an agreement whose acceptance nobody recorded. One party's
  report of another's acceptance is the reporter's word, and its provenance says so.
- **Money is a quantity.** An amount is `{ count, unit }`: the unit is a currency, the count a whole number or a
  decimal string with no more places than the currency uses. A count or a share is what was written: plain decimal
  digits, as many as the law's pattern bounds — a spelling YAML would read as another number (`010`, `0x64`, `1:30`)
  is refused, never converted. No factor joins two currencies: a rate is an observation someone made, at a moment,
  from a source, and is recorded as one.
- **Who paid and who bears it are one entry per party**, and their order says nothing: the law marks each list keyed
  by its party (`keyed_by`), and the gate refuses a party named twice in one.
- **A balance is read, never written.** What one party owes another is computed from the transactions and the
  clauses (`bin/dmledger.py`), exactly, in fractions; a stored balance is a second copy, and it drifts. A share that
  does not come out even in the currency's places is shown as the fraction it is, and who takes the remainder is a
  clause, never arithmetic.

## Relations
A small set of typed edges — `owned_by`, `responsibility`, `lives_in`, `instance_of`, `part_of`,
`depends_on`, `consumes`, `creator`, `git_host` and a few more (`python3 bin/dmrules.py` lists them) — plus
one open fallback, `refs`.
- Every edge is `{ bean|mapping: <id> [, field: <key>] }`, and the gate resolves it: a missing target or field
  is an error.
- `owned_by`, `lives_in`, `part_of` and `depends_on` must stay acyclic.
- Every `refs` entry names its relation with `rel: <kebab-case>`, e.g. `{ bean: example-org, rel: serves }`.
  `rel` is free text, so a new kind of relation needs no rule change.
- A relation declared as the mirror of another (`inverse_of`) is held consistent with it.
- `seed/COOKBOOK.md` shows which to use when.

## The vocabulary
The rules are data, not code.
- **`seed/std-vocab.md`** is the standard every garden pins. Opt-in **profiles** add groups of rules for
  gardens that need them (`code`, `network`, `domain`, `knowledge`).
- **`VOCAB.md`** is the garden's own layer: local terms, profiles it opts into (`extends_profiles`), values it
  adds to a term's own closed list (`values_add`), rows it adds to a registry (`registry_additions`), and dated
  exceptions. A term that reads its values from a registry takes a row; `values_add` on it adds nothing.
- **Every position the vocabulary offers is accounted for:** used by a bean, or declared vacant with a reason.
  A garden accounts only for what it declares itself.
- **Four layers, each standing on the one beneath.** LAWS are clear and brief, for usability and efficiency: an item's
  own `meaning:` and `why:` say what a reader needs to apply it, and the law carries no commentary. REASONING is their
  backbone (`seed/RATIONALE.md`, keyed by the item's path; `python3 bin/dmwhy.py <name>` reads both). JOURNALS are the
  leads reasoning is drawn from. HISTORY is the exact record of events the journals are written from.
- A local term that proves general is **promoted** to the standard by a pull request to the daftar repository.
  A term for a kind of fact earns promotion with real cases; a MECHANISM (a figure, a construct, a system, a
  unit) may be declared whole, ahead of its occupants, when it is universal and general — its empty positions
  declared vacant as `universal`. `CONTRIBUTING.md` has the test.
- **Aspects have a shape (a figure).** An *opposition* is a closed set of contradictory positions along one or
  more axes (necessity, capability and feasibility are squares; confidentiality is a single axis). A *sequence* is a domain walked along direction lines
  and is declared only by its restrictions: how many lines, whether positions are measured, whether they are
  totally, partially or not ordered, whether a walk can return, and where the domain ends. `time`, `place`
  and `walk` are sequences; "must stay acyclic" is the `walk` aspect's restriction, and a duration is a
  bounded region of an ordered sequence.

## Knowledge: universal anchors
The `knowledge` profile (vocabulary 9.1) lets a garden say what things ARE in the world's shared terms, with
codes every garden uses: fields of knowledge (ISCED-F 2013), occupations (ISCO-08), and established
technologies, each linked to its project's own documentation. They are kept whole as data in `seed/knowledge/`
(each file under its own licence, see `SOURCES.md`) and read by `bin/dmknowledge.py`.
- As an **anchor** (`isco_08`, `isced_f_2013`, `technology`) the code IS the object's identity, so two gardens
  that never met recognise the same occupation, field or technology.
- As a **relation** (`knowledge:` entries `{scheme, code, rel, topic?}` with `rel` classified_as, draws_on or
  uses) any bean says what it rests on — an instance uses a technology, a design draws on a field.
- The gate checks every code against its scheme; an invented code is refused.

## Ground rules
1. **One owner per fact.** A fact lives in one bean's `owns:`; elsewhere it is referenced.
2. **Abstraction, not force-fit — and structure before prose.** A fact that fits no term goes in `details:`,
   intact — never bent into a term that nearly fits, never dropped. But INSIDE a term, an entry
   holds only the attributes that term declares: a remark goes in the attribute declared for prose (`note`,
   `why`), and a new kind of fact is proposed as a new attribute. A sentence written as a key looks like data
   and is readable by nothing.
3. **Reference external truth, or capture it knowingly.** A fact is either *authoritative here*, a *pointer* to
   whoever owns it, or a *capture*: a dated, staleness-keyed copy taken so something can be rebuilt, never
   authoritative, never applied back without re-reading the source, and never containing secrets.
4. **Legible to people and agents.** Plain YAML and Markdown, small files.
5. **No cleverness that needs explaining.**
6. **Reads correctly cold.** Spelled-out keys, explicit units, absolute dates, detail in named `details:`
   blocks.

## The Contract of Parts: who decides
This table is the one statement of who may decide what.

| | Decision | Who |
|---|---|---|
| **A** | record a newly **observed**, reversible fact | an agent alone (tag `src`, `as_of`; log it) |
| **B** | record an **inference** not directly observed | an agent alone, marked `src: inferred`, not settled |
| **C** | **overwrite or delete** an authoritative value | own earlier *observed* value: an agent (log both); *asserted* or safety-related: **a person ratifies** |
| **D** | set or change a **human-asserted** fact | **a person only**; an agent may propose |
| **E** | change a **safety-critical** `status:` or flag | **a person ratifies** |
| **F** | choose or settle a bean's **identity anchors**, or take one in from another garden | **a person ratifies** — it governs every future merge |
| **G** | add or change a **vocabulary term or rule** (the law) | **a person ratifies**, logged distinctly as a RULE-CHANGE |
| **H** | add a dated **`exceptions:`** entry | an agent proposes, a person co-decides |
| **I** | an **automatic merge** with no conflict | an agent alone |
| **J** | resolve a **merge conflict or uncertain identity** | **a person ratifies** |
| **K** | **log** what was done | everyone, always |

The person who ratifies in a garden is its gardener — for an organisation, a person who answers for it. When the
class is unclear, an agent proposes and a person ratifies. An agent that meets something it may not decide parks it
in `log/pending.md` as `status: proposed`, does everything safe around it, and carries on.

## The journal and the gate
- Every change is recorded in `log/journal.md` in the same commit: who, what and why. People record decisions
  and approvals; agents record what they ran, why, and what happened.
- `bin/dmcheck.py` runs as a git pre-commit hook. It refuses a commit that breaks a rule, including:
  - a bean or mapping change whose journal entry does not name it;
  - a change to the law whose entry does not say RULE-CHANGE. The law is `seed/std-vocab.md`, `VOCAB.md`,
    `GARDEN.md` and every file the release ships (`seed/LANGUAGE`: this document, the checklist, the tools and
    the gate itself);
  - a journal entry that still contains a template's `(fill in` field;
  - a journal heading a commit adds that is not a position in time: `## 2026-09-20 00:15+03:00 · who · what`,
    in any declared calendar's own form (`persian:1405-06-29 00:45+03:30`), to the minute, with its offset — or
    that `bin/dmjournal.py` did not write, reading the clock. Entries already written are never checked or
    rewritten;
  - a journal line a commit adds that holds a character some reader takes for a line break, besides the line end
    itself: one line of the journal is one line to every reader.
- These checks confirm that the words are there, not that they are true; honesty is still the writer's.
- Each person and each agent session commits under its own git identity, so the log's "who" is real.
- `CHECKLIST.md` is how a write is made.

## Merging
Gardens merge object by object, matched on establishing anchors: losslessly, in any order, with the same
result, and never creating two beans for one object. A genuine disagreement is kept, both values, for a person
to settle. A name a garden minted fuses only within that garden unless it is qualified by the garden's id; equal
bare names from two gardens are shown to a person, never fused. Values are compared in one canonical form, so that
one fact written two ways is not a disagreement: an amount by its value (`900`, `"900"` and `"900.00"` are one), a
list keyed by party by its entries, whatever their order. The bean keeps what was written. `MERGE.md` has the
algebra.

## Between gardens: the mycelium
A garden is kept by its gardener, and nothing outside it writes there. **Gardens meet only by proposal.**
- **A garden's identity** is `garden_id`: the first twelve hexadecimal digits of the root of its first-parent
  history. It is read from git and never stated as the garden's own: `GARDEN.md` carries no id, and it appears in
  the garden's beans only as the prefix of names the garden minted. A clone is the same garden; a copy given a new
  history is another. Germination writes a random seed into the first commit, so two gardens grown alike are never
  one.
- **First contact.** Another garden this one deals with is a `garden` bean, anchored by its `garden_id`, owned by
  that garden's gardener and answered for by them — so that gardener is a person or organisation bean here, named
  as their own garden names them. Recording a new garden, and its gardener, is the gardener's decision (class F),
  made in one commit.
- **A name is minted once and carried.** A value of an anchor term marked `minted` is a name a garden gave when it
  has the form the law's `identity_policy.minted` gives one: `<kind>:<name>`, the kind one this garden knows
  (`person:sam`, `contract:shared-camera`). Bare, it identifies only within that garden; qualified —
  `<garden_id>/<kind>:<name>` — it identifies everywhere. A thing two gardens share is named once, by the garden that
  recorded it first, and qualified when it is to cross; a garden that takes the name in keeps it byte for byte, and
  a qualified name here is qualified by this garden or by a garden it holds a `garden` bean for.
- **An identifier someone else assigned is nobody's to qualify.** A value of a minted term in any other form — a
  package's name, a registry or tax number, the UID an invitation carries, a provider's id — was assigned outside
  every garden: it identifies wherever it is written and fuses as any anchor does, and the gate refuses it
  prefixed with a garden's id.
- **What passes is a proposal** (`bin/dmpropose.py`), never a write: one file, laid outside every garden, for one
  garden, made under an agreement whose parties include both gardeners. It carries whole beans as the proposing
  garden committed them, a stub of each bean they refer to (its identity and nothing more), the journal entry that
  would take them in, and a fingerprint — a check that it arrived as it was made, which anyone who rewrites it can
  compute again, and so never a signature. It passes on what was said in the proposing garden or by the garden
  proposed to, and of what a third garden said only the names it gave.
- **Provenance crosses unchanged.** A record travels as it was written; `garden` is added once, naming the garden
  the record was made in, and never changed — and it names a garden this one holds a
  `garden` bean for. A record that comes back to the garden it was made in is that garden's own again, and carries
  no `garden` there. A person's assertion arrives as that person's assertion, and the provenance guard holds across
  the boundary.
- **Taking in is a write in the receiving garden like any other.** What a proposal brings is another person's
  assertion (class D), a name another garden gave (F), and every disagreement or uncertain identity (J). Reading a
  proposal writes nothing; taking it in writes in the working tree and never commits; the gardener's commit is the
  ratification. A proposal is taken once. A record in a garden's proposal names the garden it was made in; one that
  claims to be the receiving garden's own is its own only where the receiving garden holds that same record already.
- **Taking in an agreement is not accepting it.** Taking records what the other garden offers. A party's acceptance
  is its own word, recorded by its own garden: the receiving gardener accepts by writing `accepted` on their own
  entry in `parties`, in a commit of their own.
- **An agreement two gardens share may be owned by none of its parties, and then its parties answer for it** — the
  crown and `parties` forms above — so the two gardens' records of it agree about its owner.
- **A test garden** says so in `GARDEN.md` (`test:`). Its beans are not facts about the world. A rehearsal is grown
  by germination, never by clone: a clone is the same garden, with the same `garden_id`, and its word is that
  garden's. A garden that deals with a test garden marks its `garden` bean with `test` — its own record, whatever
  the other garden's proposals say. A proposal is a test when its envelope says so or the sending garden's bean here
  does; a garden that is not a test garden takes one in only as a test, and then every bean it writes says what the
  rehearsal changed.
- **Two gardens exchange only while they pin the same vocabulary.** A different pin blocks a proposal as it blocks
  a merge (`MERGE.md`).
