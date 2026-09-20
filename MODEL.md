# daftar — the model

A ledger that people and AI agents both read and write: plain files in git, every change checked by a gate
and recorded in a journal. It is meant to read correctly cold — on paper, years later — so legibility and
provenance come before brevity. Why each rule exists is in `seed/RATIONALE.md`, keyed by the rule's own path; the
design steps before that are in `HISTORY.md` in the daftar repository.

## Beans and gardens
- A **bean** is one managed thing — a machine, a domain, a program, a person, a contract — as one file,
  `beans/<id>.md`. The YAML front matter holds the facts; the Markdown body is for people. A **mapping**
  (`mappings/<id>.md`) records a procedure or relationship that is not itself a thing.
- A **garden** is a git repository of beans: one estate's ledger. `GARDEN.md` names it, pins the vocabulary
  version (`extends: std-vocab@<version>`) and records the daftar release it runs (`daftar_release`).
- The **seed** (`seed/`) is the kit a garden is grown from. When gardens are merged, the result for each object
  is a **canonical bean** — see `MERGE.md`, which calls it a *seed*; that is not `seed/`, the kit.

## Facts carry their provenance
A fact knows who said it and how they know.
- Each bean states a default `provenance: { src, by, as_of }`, where `src` is `observed`, `inferred`,
  `asserted-by-human` or `generated-by-tool`. The vocabulary ranks them by HOW THE FACT IS KNOWN and says why
  (`provenance_src`). A `generated-by-tool` fact has no standing of its own: it names what it was computed
  from in `provenance.from`, and weighs as the weakest of those.
- A fact whose source differs from the bean's default carries its own record.
- **An `inferred` value never overrides an `asserted-by-human` one**, whatever precision it claims.

## Identity: anchors
Every bean has an `identity:` block of **anchors** — facts that say which object this is, so two gardens can
recognise the same thing whatever its file is called.
- Each anchor says `establishing: true` (it identifies the object) or `false` (it only corroborates).
  Only establishing anchors decide that two beans are one object.
- Typically hardware anchors (`serial`, `mac`) and logical ones (`fqdn`, a product or service id) establish;
  network ones (`ip`, `hostname`) corroborate. Where the vocabulary declares a policy for an anchor, it
  overrules the bean.
- How many establishing anchors a confirmed bean needs depends on its nature. A bean below that is
  `identity.status: provisional`, and the gate warns.
- Two beans with the same establishing anchor are the same object: the gate refuses it. Serials are compared
  ignoring case and spaces.

## Type: nature, then kind
Every bean has a `nature` — `physical`, `metaphysical` or `living` — and a `kind` that refines it (`host` is
physical; `domain`, `product`, `codebase` are metaphysical; `person` and `instance` are living). The gate
refuses a nature that contradicts the kind. Rules about what sort of being something is — such as identity
anchors — attach to the nature, so every kind under it inherits them.

## Ownership and responsibility
Two arcs, over the same **facets** (`legal`, `technical`, …; facets may depend on each other — `technical`
depends on `legal` — but never overlap):
- `owned_by` points up: each facet has **exactly one owner**.
- `responsibility` points down: each facet has **exactly one holder** who answers for the thing.
- **Every facet with an owner has a holder, and vice versa.** The gate enforces the pairing.

The forms an entry can take:
- `{ owner: { bean: … } }` — owned by another bean. The chain must end somewhere: the gate refuses one that
  stops at a bean owning nothing.
- `{ external: "…" }` — owned outside this ledger: a rented server's provider, software's vendor, a domain's
  registry. Someone here still answers for it.
- `{ via: { bean: … } }` — inherits the parent's owners, e.g. an instance through the product it runs.
- `{ contract: { bean: … } }` — shared ownership of one facet, only through a `contract` bean that records the
  agreement and a deterministic rule for conflicts.
- `{ crown: <branch> }` — where every chain ends. In practice only a **person** writes it: a person is owned by
  no bean, so `owned_by: { legal: { crown: love } }`, and answers for themselves:
  `responsibility: { legal: { self: true } }`. The branch follows the nature (`nature` for physical, `logos`
  for metaphysical, `love` for living); the gate checks it.

Ownership is separate from **habitat**: a running instance is owned through its product, and separately
`lives_in` the machine it runs on. Moving machines changes the habitat, never the owner.

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
2. **Abstraction, not force-fit — and structure before prose.** A fact that fits no term goes in `attributes:`
   or `details:`, intact — never bent into a term that nearly fits, never dropped. But INSIDE a term, an entry
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
| **F** | choose or settle a bean's **identity anchors** | **a person ratifies** — it governs every future merge |
| **G** | add or change a **vocabulary term or rule** (the law) | **a person ratifies**, logged distinctly as a RULE-CHANGE |
| **H** | add a dated **`exceptions:`** entry | an agent proposes, a person co-decides |
| **I** | an **automatic merge** with no conflict | an agent alone |
| **J** | resolve a **merge conflict or uncertain identity** | **a person ratifies** |
| **K** | **log** what was done | everyone, always |

When the class is unclear, an agent proposes and a person ratifies. An agent that meets something it may not
decide parks it in `log/pending.md` as `status: proposed`, does everything safe around it, and carries on.

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
    in any declared calendar's own form (`persian:1405-06-29 00:45+03:30`), to the minute, with its offset. Entries already written are never checked or rewritten.
- These checks confirm that the words are there, not that they are true; honesty is still the writer's.
- Each person and each agent session commits under its own git identity, so the log's "who" is real.
- `CHECKLIST.md` is how a write is made.

## Merging
Gardens merge object by object, matched on establishing anchors: losslessly, in any order, with the same
result, and never creating two beans for one object. A genuine disagreement is kept, both values, for a person
to settle. `MERGE.md` has the full algebra.
