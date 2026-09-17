# daftar — data model

The source-of-truth ledger and shared language between human and AI. Git-backed; every change gated + logged. Built to be obvious to an average network admin / developer, and to survive being **printed on paper and rescanned with every detail intact**.

## Purpose — a portable human↔AI language
One shared source of truth both human and AI can read and write; **portable** (plain files + git, no runtime to read the data); **inclusive** (any object/kind); **safe** (no secrets, no silent corruption, no silent generalization). Legibility and provenance outrank brevity.

## Beans, gardens, seeds
- **bean** — one file per managed object (`beans/<id>.md`), YAML front-matter (machine truth) + Markdown body (human context). Each garden names its root bean in `GARDEN.md`.
- **garden** — a collection of beans (this working copy); declared by `GARDEN.md`, pins a `std-vocab` version.
- **seed** — the canonical superset bean produced by merging gardens (MERGE.md). Beans from different sessions/agents/models **converge** — matched by identity anchors, not filenames.

## Facts carry provenance + truth-status (the linchpin)
An authoritative fact is not a bare value — it knows **who said it and how they know**:
- Each bean declares a default `provenance: { src, by, as_of }`.
- `src ∈ observed | inferred | asserted-by-human | generated-by-tool`. A fact that differs from the bean default (e.g. a human-asserted value in an agent-scanned bean) carries its **own** `{value, src, by, as_of, authority}` record.
- **Guard:** an `inferred` value may **never** auto-override an `asserted-by-human` value, whatever precision it claims. This is what makes a fact trustable **cold, on paper**.

## Identity — typed anchors (see MERGE.md §4)
Every bean carries an `identity:` capsule of **classed** anchors — the merge key, decoupled from the filename:
- Each anchor states **`establishing: true|false`** — establish identity, or merely corroborate it. That two-way split is load-bearing (P4/D1): only establishing anchors fuse objects on merge. `class` (hardware/logical/network/role) survives as an optional **hint at why**, no longer as the decision. Typically hardware (serial/mac/wg_pubkey) and logical (fqdn/git_remote/emp_id) establish; network (ip/hostname) and role (mail_identity) corroborate. Where a **vocabulary term declares an anchor policy it overrules the bean**, so a role anchor that migrates between objects can never be promoted to establishing.
- Min-anchor policy hangs off the **nature**, not the kind (P3/D1, 2026-08-02): each entry in VOCAB's `natures:` registry declares its `establishing_anchor_family` and `min_establishing_anchors`, and `identity_policy:` names the axis that selects the row. A bean below policy is `identity: status: provisional` (the gate warns, an `open:` item tracks it). A new kind therefore inherits a coherent identity policy for free.

## Type — nature is the root axiom, kind refines it (added 2026-08-02, P3 / plan D1, human-ratified)
`nature ∈ {physical, metaphysical, living}` is the **root of the type system** and is **mandatory on every bean**. `kind` (host, codebase, domain, instance, …) is a **refinement** of a nature, not a parallel taxonomy: each kind declares in VOCAB the `of_nature:` it refines, and the gate rejects any bean whose `nature` contradicts its kind. Policy that is really about *what sort of being this is* — identity anchors, minimum anchors — therefore attaches at the **nature** level and is inherited by every kind beneath it; a kind states only what it means and may override only where it genuinely differs. Natures are declared once in VOCAB's `natures:` registry, which is also the enum the `nature` term validates against, so the two cannot drift.

## Ownership — one root, faceted, recursive (the crown; added 2026-08-02, human-ratified)
Ownership is a single-rooted, recursive relation, **orthogonal** to habitat (`lives_in`) and to type/token (`instance_of`). Every existing being has **exactly one owner per facet**.
- **The crown (axiom — stated once here, never instantiated as beans):** the one substance **`god`** (*Deus sive Natura*, *natura naturans*) owns everything; every chain terminates there. It branches by the being's `nature:` — **`nature`** (Extension / *res extensa*) owns **physical** beings, **`logos`** (Thought / *res cogitans*) owns **metaphysical** beings, **`love`** (the *conatus*) owns **living instances while alive** (life-bounded; lapses at teardown). A bean's `nature:` field routes it to its branch; the branch resolves up to `god`. **Since P7b the crown is nameable in data** — `owned_by: { <facet>: { crown: <branch> } }` — without ever being instantiated as beans, and the gate holds the branch to the one the bean's nature routes to. A bean names its branch directly only where ownership passes through no other being: in practice, **persons**. `kind: person` is *pinned* to the crown form, so **no bean may hold a person** — only `love`, and only while they live. That is the branch's purpose, and it is now enforced rather than asserted. The crown **owns but never answers**: `responsibility` has no crown form, because a duty must land on a being that can be asked. A person therefore answers for **themselves** (`self: true`), written deliberately as a non-edge — autonomy is reflexive, not a dependency, and as a real edge it would be a self-cycle.
- **Facets:** ownership is faceted (`legal`, `technical`, …); the one-owner law holds *per facet*. Facets are a **distinguishable** (no ambiguous double-coverage), **dependency-bearing (DAG)**, **recursive** lattice — seed edge `technical depends_on legal`.
- **Inheritance:** `owned_by` is introduced with explicit facet-owners at a node and **inherited** down the tree (`owned_by: {via: {bean: <parent>}}`) unless overridden.
- **Responsibility — the closing arc** (P7, 2026-08-02, human-ratified): `owned_by` alone is **one-directional** — a being points *up* to its owner, up to the crown. That is one arc of a loop. **`responsibility:`** is the opposite arc: the holder answering *down* for the being, over the **same facet lattice**. The gate enforces **parity** — every facet with an owner must have a holder and vice versa. An ownership claim nothing answers for is a loose end; a duty nobody owns is orphaned. This is what makes an `external` owner an ordinary position rather than an escape hatch: a rented VPS is **owned by the provider and answered for by the operator**, and third-party software is **owned by its vendor and answered for by whoever runs it**. That is the normal case, not an exception.
- **Co-ownership** of a single facet is never raw — it requires a **`contract`** bean: a *balanced ongoing* agreement carrying `agreement_ref` (provenance → the prior agreement text) + `conflict_rule` (deterministic, via the MERGE lattice). This is the **Contract of Parts applied to ownership**.
- **Ownership ≠ habitat:** a running token is **owned** via its product's owner (up to `god`) and *separately* **lives_in** a habitat (host / container / odoo-instance). Migrating hosts changes habitat, never ownership.

## Vocabulary — two tiers + governed growth (see VOCAB.md, std-vocab, SKILL.md)
Type/process rules live in the **vocabulary**, not in code:
- **Tier-0 Universal Standard Vocab** (`std-vocab`, carried by the skill, versioned) — the estate-agnostic classification (terms + anchor classes + merge lattices). Gardens `extends: std-vocab@<ver>` (pinned → deterministic).
- **Tier-1 Garden Vocab** (`VOCAB.md`) — local terms + dated exceptions + flagged specializations.
- **Promotion:** a local term that proves general is uploaded to std-vocab via the SKILL promotion protocol (propose → show neighborhood → **human ratifies** → version bump + provenance). The standard classification thus **standardizes and improves over time**.

## Ground rules
1. **No duplicate authoritative data.** A fact lives in exactly one bean's `owns:`; elsewhere it is `ref:`'d. (Enforced for identifiers per the vocab.)
2. **Abstraction, not force-fit.** An uncategorizable unique datum goes in `attributes:`/`details:` (the abstraction layer) — kept intact, categorized later. Never dropped, never mis-bucketed.
3. **Reference external truth, don't mirror it — or CAPTURE it, dated and knowing it is a copy.** THREE states, not two (2026-08-07, human-ratified rule-change). *Authoritative here*: this ledger owns the fact. *Pointer*: somebody else owns it and we name them ("owned by X, do not hand-edit"). *Capture*: a timestamped, staleness-keyed copy taken so the thing can be **rebuilt** — never authoritative, and never applied back without re-reading the source first. The two-state rule existed to stop a ledger silently becoming a stale second copy of every device's config; that danger is real and unchanged. What it got wrong is that **a pointer to a machine that has died reproduces nothing**, and reproduction is much of why an estate is written down at all. A capture is the honest middle: it states what it copies, who owns the original, when it was taken, which command took it, and how a reader tells whether it still holds. It carries **no secrets, ever** — the `capture` term makes `redactions` a *required* attr precisely so that "nothing was removed" must be an explicit claim rather than an omission nobody notices.
4. **Human + AI legible.** Plain YAML+Markdown, small greppable files.
5. **Understandable by an average admin/dev.** No cleverness that needs explaining.
6. **Capsule clarity — paper-durable.** Self-contained; spelled-out keys; explicit **units**; absolute **dates**; rich detail in namespaced `details:` capsules; each new `kind` gets a small schema so complexity stays organized. Reads correctly cold, years later.

## Links (functional + efficient)
**Relations** (P4/D3) are a small set of canonical typed edges — `owned_by`, `lives_in`, `instance_of`, `part_of`, `created_in`, `creator`, `git_host`, `runtime`, `manages`, `depends_on`, `consumes` — plus ONE open residual, `refs`. Each declares its own shape and whether it must stay acyclic; `owned_by`/`lives_in`/`part_of`/`depends_on` are **DAGs**. All use `{ bean|mapping: <id> [, field: <key>] }` and the validator resolves every pointer (dangling target or missing field = error). Keep refs one hop (shallow).
Every **`refs`** entry must carry **`rel: <name>`** naming its relation type, because the key is only a slot label (`party_acme`, `c_survey`) — `rel` is what makes an edge self-describing when read alone. `rel` is deliberately **open** and kebab-case, never an enum: a new kind of relation must not require a rule-change. A relation declaring **`inverse_of`** is held consistent with its mirror, so a convenience edge cannot drift from the fact.

## The Contract of Parts — human↔AI authority
Who decides, and who must be asked. This table is the SINGLE OWNER of the classes; it had five copies
(here, MERGE.md §9, SKILL.md, `GARDEN.md` `policy.authority`, and the class letters in `log/pending.md`)
and the other four are pointers now.

| | Decision | Owner |
|---|---|---|
| **A** | record a newly **observed**, reversible fact | AI-autonomous (tag `src`, `as_of`, log) |
| **B** | record an **inference** not directly observed | AI-autonomous, constrained (tag `src: inferred`; not settled) |
| **C** | **overwrite/delete** an authoritative value | own prior *observed* → auto (log both); *asserted* / safety → **ratify** |
| **D** | set or alter a **human-asserted** fact | **human-only** (AI may only propose) |
| **E** | flip a **safety-critical** `status:` or flag | **human ratifies** |
| **F** | choose or settle a bean's **identity anchors** | **human ratifies** (it governs all future merges) |
| **G** | add or change a **vocabulary term or rule** (the law) | **human ratifies**, logged distinctly as a rule-change |
| **H** | add a dated **`exceptions:`** entry (case law) | AI proposes / human co-decides |
| **I** | **auto-merge**, inclusiveness-safe, no conflict | AI-autonomous |
| **J** | resolve a **merge conflict or uncertain identity** | **human ratifies** (emit a *pending* seed) |
| **K** | **logging** consequential actions | shared, non-optional |

**Keystone default:** any decision whose class is unclear ⇒ AI proposes / human ratifies. No-silent-
generalization, promoted from *rules* to *authority*.
**Protect the law:** editing `seed/std-vocab.md`, `VOCAB.md` or `MODEL.md` is a **rule-change** — ratified,
and logged distinctly from an ordinary edit. The gate enforces the logging half.
**Enforce the honour system:** a state-changing commit must carry a journal entry (gate-checked), and the
actor is a distinct git committer per model and session, so "human vs AI" in the log is real rather than
self-declared.

## Provenance — the dual logging duty (`log/journal.md`)
- **Agent:** high-detail logs of consequential actions (state-changing shell execs: command + purpose + outcome; decisions + reasoning). Granularity governed by the `shell-log` vocab term.
- **Human:** decisions, approvals, events — so the "why" survives.
A state-changing commit should carry a journal entry that references it (the gate checks this).

## The write gate (session/model-agnostic)
Every write passes **CHECKLIST.md**; its mechanical half is enforced by `bin/dmcheck.py` as a git **pre-commit hook** → a violating write cannot be committed by any model in any session. Run `python3 bin/dmcheck.py`; commit only at `0 error(s)`.

## Distributed & convergent (see MERGE.md)
Beans from different gardens merge into canonical seeds — lossless, order-agnostic, deterministic, no duplicate objects — via a CRDT lattice join over a JCS-canonical projection, with conflicts routed to the exception-ack protocol. Full spec + invariants in **MERGE.md**.
