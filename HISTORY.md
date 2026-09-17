# daftar — history: why the model and the checklist say what they say

MODEL.md and CHECKLIST.md are written for someone using daftar: what the rules are, and how a write is made.
This file keeps what they used to carry as well — the design steps, the incidents each rule answers, and the
philosophy behind the ownership model — for anyone who wants to know *why* a rule exists before proposing to
change it. Nothing here is a rule that is not also in MODEL.md, CHECKLIST.md or the vocabulary; where they
differ, those files govern. Plan codes such as P3/D1 or P7b name steps of the original design, and the dates
are when a change was ratified.

Below: MODEL.md and CHECKLIST.md as they stood at release v0.4.3, verbatim.

---

## MODEL.md at v0.4.3

The source-of-truth ledger and shared language between human and AI. Git-backed; every change gated + logged. Built to be obvious to an average network admin / developer, and to survive being **printed on paper and rescanned with every detail intact**.

### Purpose — a portable human↔AI language
One shared source of truth both human and AI can read and write; **portable** (plain files + git, no runtime to read the data); **inclusive** (any object/kind); **safe** (no secrets, no silent corruption, no silent generalization). Legibility and provenance outrank brevity.

### Beans, gardens, seeds
- **bean** — one file per managed object (`beans/<id>.md`), YAML front-matter (machine truth) + Markdown body (human context). Each garden names its root bean in `GARDEN.md`.
- **garden** — a collection of beans (this working copy); declared by `GARDEN.md`, pins a `std-vocab` version.
- **seed** — `seed/`: the germination kit a new garden is grown from (the vocabulary, the templates, `germinate.sh`). Not to be confused with the **canonical bean**, the superset bean a merge produces (MERGE.md): beans from different sessions/agents/models **converge** into one, matched by identity anchors, not filenames.

### Facts carry provenance + truth-status (the linchpin)
An authoritative fact is not a bare value — it knows **who said it and how they know**:
- Each bean declares a default `provenance: { src, by, as_of }`.
- `src ∈ observed | inferred | asserted-by-human | generated-by-tool`. A fact that differs from the bean default (e.g. a human-asserted value in an agent-scanned bean) carries its **own** `{value, src, by, as_of, authority}` record.
- **Guard:** an `inferred` value may **never** auto-override an `asserted-by-human` value, whatever precision it claims. This is what makes a fact trustable **cold, on paper**.

### Identity — typed anchors (see MERGE.md §4)
Every bean carries an `identity:` capsule of **classed** anchors — the merge key, decoupled from the filename:
- Each anchor states **`establishing: true|false`** — establish identity, or merely corroborate it. That two-way split is load-bearing (P4/D1): only establishing anchors fuse objects on merge. `class` (hardware/logical/network/role) survives as an optional **hint at why**, no longer as the decision. Typically hardware (serial/mac/wg_pubkey) and logical (fqdn/git_remote/emp_id) establish; network (ip/hostname) and role (mail_identity) corroborate. Where a **vocabulary term declares an anchor policy it overrules the bean**, so a role anchor that migrates between objects can never be promoted to establishing.
- Min-anchor policy hangs off the **nature**, not the kind (P3/D1, 2026-08-02): each entry in VOCAB's `natures:` registry declares its `establishing_anchor_family` and `min_establishing_anchors`, and `identity_policy:` names the axis that selects the row. A bean below policy is `identity: status: provisional` (the gate warns, an `open:` item tracks it). A new kind therefore inherits a coherent identity policy for free.

### Type — nature is the root axiom, kind refines it (added 2026-08-02, P3 / plan D1, human-ratified)
`nature ∈ {physical, metaphysical, living}` is the **root of the type system** and is **mandatory on every bean**. `kind` (host, codebase, domain, instance, …) is a **refinement** of a nature, not a parallel taxonomy: each kind declares in VOCAB the `of_nature:` it refines, and the gate rejects any bean whose `nature` contradicts its kind. Policy that is really about *what sort of being this is* — identity anchors, minimum anchors — therefore attaches at the **nature** level and is inherited by every kind beneath it; a kind states only what it means and may override only where it genuinely differs. Natures are declared once in VOCAB's `natures:` registry, which is also the enum the `nature` term validates against, so the two cannot drift.

### Ownership — one root, faceted, recursive (the crown; added 2026-08-02, human-ratified)
Ownership is a single-rooted, recursive relation, **orthogonal** to habitat (`lives_in`) and to type/token (`instance_of`). Every existing being has **exactly one owner per facet**.
- **The crown (axiom — stated once here, never instantiated as beans):** the one substance **`god`** (*Deus sive Natura*, *natura naturans*) owns everything; every chain terminates there. It branches by the being's `nature:` — **`nature`** (Extension / *res extensa*) owns **physical** beings, **`logos`** (Thought / *res cogitans*) owns **metaphysical** beings, **`love`** (the *conatus*) owns **living instances while alive** (life-bounded; lapses at teardown). A bean's `nature:` field routes it to its branch; the branch resolves up to `god`. **Since P7b the crown is nameable in data** — `owned_by: { <facet>: { crown: <branch> } }` — without ever being instantiated as beans, and the gate holds the branch to the one the bean's nature routes to. A bean names its branch directly only where ownership passes through no other being: in practice, **persons**. `kind: person` is *pinned* to the crown form, so **no bean may hold a person** — only `love`, and only while they live. That is the branch's purpose, and it is now enforced rather than asserted. The crown **owns but never answers**: `responsibility` has no crown form, because a duty must land on a being that can be asked. A person therefore answers for **themselves** (`self: true`), written deliberately as a non-edge — autonomy is reflexive, not a dependency, and as a real edge it would be a self-cycle.
- **Facets:** ownership is faceted (`legal`, `technical`, …); the one-owner law holds *per facet*. Facets are a **distinguishable** (no ambiguous double-coverage), **dependency-bearing (DAG)**, **recursive** lattice — seed edge `technical depends_on legal`.
- **Inheritance:** `owned_by` is introduced with explicit facet-owners at a node and **inherited** down the tree (`owned_by: {via: {bean: <parent>}}`) unless overridden.
- **Responsibility — the closing arc** (P7, 2026-08-02, human-ratified): `owned_by` alone is **one-directional** — a being points *up* to its owner, up to the crown. That is one arc of a loop. **`responsibility:`** is the opposite arc: the holder answering *down* for the being, over the **same facet lattice**. The gate enforces **parity** — every facet with an owner must have a holder and vice versa. An ownership claim nothing answers for is a loose end; a duty nobody owns is orphaned. This is what makes an `external` owner an ordinary position rather than an escape hatch: a rented VPS is **owned by the provider and answered for by the operator**, and third-party software is **owned by its vendor and answered for by whoever runs it**. That is the normal case, not an exception.
- **Co-ownership** of a single facet is never raw — it requires a **`contract`** bean: a *balanced ongoing* agreement carrying `agreement_ref` (provenance → the prior agreement text) + `conflict_rule` (deterministic, via the MERGE lattice). This is the **Contract of Parts applied to ownership**.
- **Ownership ≠ habitat:** a running token is **owned** via its product's owner (up to `god`) and *separately* **lives_in** a habitat (host / container / odoo-instance). Migrating hosts changes habitat, never ownership.

### Vocabulary — two tiers + governed growth (see VOCAB.md, std-vocab, SKILL.md)
Type/process rules live in the **vocabulary**, not in code:
- **Tier-0 Universal Standard Vocab** (`std-vocab`, carried by the skill, versioned) — the estate-agnostic classification (terms + anchor classes + merge lattices). Gardens `extends: std-vocab@<ver>` (pinned → deterministic).
- **Tier-1 Garden Vocab** (`VOCAB.md`) — local terms + dated exceptions + flagged specializations.
- **Promotion:** a local term that proves general is uploaded to std-vocab via the SKILL promotion protocol (propose → show neighborhood → **human ratifies** → version bump + provenance). The standard classification thus **standardizes and improves over time**.

### Ground rules
1. **No duplicate authoritative data.** A fact lives in exactly one bean's `owns:`; elsewhere it is `ref:`'d. (Enforced for identifiers per the vocab.)
2. **Abstraction, not force-fit.** An uncategorizable unique datum goes in `attributes:`/`details:` (the abstraction layer) — kept intact, categorized later. Never dropped, never mis-bucketed.
3. **Reference external truth, don't mirror it — or CAPTURE it, dated and knowing it is a copy.** THREE states, not two (2026-08-07, human-ratified rule-change). *Authoritative here*: this ledger owns the fact. *Pointer*: somebody else owns it and we name them ("owned by X, do not hand-edit"). *Capture*: a timestamped, staleness-keyed copy taken so the thing can be **rebuilt** — never authoritative, and never applied back without re-reading the source first. The two-state rule existed to stop a ledger silently becoming a stale second copy of every device's config; that danger is real and unchanged. What it got wrong is that **a pointer to a machine that has died reproduces nothing**, and reproduction is much of why an estate is written down at all. A capture is the honest middle: it states what it copies, who owns the original, when it was taken, which command took it, and how a reader tells whether it still holds. It carries **no secrets, ever** — the `capture` term makes `redactions` a *required* attr precisely so that "nothing was removed" must be an explicit claim rather than an omission nobody notices.
4. **Human + AI legible.** Plain YAML+Markdown, small greppable files.
5. **Understandable by an average admin/dev.** No cleverness that needs explaining.
6. **Capsule clarity — paper-durable.** Self-contained; spelled-out keys; explicit **units**; absolute **dates**; rich detail in namespaced `details:` capsules; each new `kind` gets a small schema so complexity stays organized. Reads correctly cold, years later.

### Links (functional + efficient)
**Relations** (P4/D3) are a small set of canonical typed edges — `owned_by`, `lives_in`, `instance_of`, `part_of`, `created_in`, `creator`, `git_host`, `runtime`, `manages`, `depends_on`, `consumes` — plus ONE open residual, `refs`. Each declares its own shape and whether it must stay acyclic; `owned_by`/`lives_in`/`part_of`/`depends_on` are **DAGs**. All use `{ bean|mapping: <id> [, field: <key>] }` and the validator resolves every pointer (dangling target or missing field = error). Keep refs one hop (shallow).
Every **`refs`** entry must carry **`rel: <name>`** naming its relation type, because the key is only a slot label (`party_acme`, `c_survey`) — `rel` is what makes an edge self-describing when read alone. `rel` is deliberately **open** and kebab-case, never an enum: a new kind of relation must not require a rule-change. A relation declaring **`inverse_of`** is held consistent with its mirror, so a convenience edge cannot drift from the fact.

### The Contract of Parts — human↔AI authority
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
and logged distinctly from an ordinary edit. The gate enforces the logging half: a staged change to the law needs a staged journal entry that says RULE-CHANGE.
**Enforce the honour system:** a state-changing commit must carry a journal entry (gate-checked), and the
actor is a distinct git committer per model and session, so "human vs AI" in the log is real rather than
self-declared.

### Provenance — the dual logging duty (`log/journal.md`)
- **Agent:** high-detail logs of consequential actions (state-changing shell execs: command + purpose + outcome; decisions + reasoning). Granularity governed by the `shell-log` vocab term.
- **Human:** decisions, approvals, events — so the "why" survives.
A state-changing commit must carry a journal entry that NAMES each changed bean or mapping (the gate checks this, and refuses an entry that still contains a `(fill in` template field).

### The write gate (session/model-agnostic)
Every write passes **CHECKLIST.md**; its mechanical half is enforced by `bin/dmcheck.py` as a git **pre-commit hook** → a violating write cannot be committed by any model in any session. Run `python3 bin/dmcheck.py`; commit only at `0 error(s)`.

### Distributed & convergent (see MERGE.md)
Beans from different gardens merge into canonical beans — lossless, order-agnostic, deterministic, no duplicate objects — via a CRDT lattice join over a JCS-canonical projection, with conflicts routed to the exception-ack protocol. Full spec + invariants in **MERGE.md**.

---

## CHECKLIST.md at v0.4.3

Session/model-agnostic. Part A is enforced mechanically by `bin/dmcheck.py`, run as a git **pre-commit hook** — a failing write cannot be committed by any model or session. The hook is **versioned** at `bin/hooks/pre-commit`, because `.git/hooks` is not cloned and a fresh clone would otherwise have no gate at all: after cloning, run **`sh bin/install.sh`** — the one installer. Part B is judgment the writer confirms; Part C is how a write is made.

The gate reads the **staged blobs**, not the working tree, so what is checked is what is committed — they differ under partial staging. Two rules exist only there: a staged document must still **parse**, and a staged edit that **removes a top-level key** must have that key named in the staged journal entry. Replayed over this garden's whole history, that second rule fired **zero** false positives; every real removal was already declared in the journal.

### Part A — mechanical (auto-enforced; commit blocked on any fail)
- [ ] Valid YAML front-matter; `bean:`/`mapping:` id = filename, kebab-case.
- [ ] **Every top-level key is declared** by a vocabulary term; a fact that fits no term goes in `details:`/`attributes:`, and a new kind of fact is proposed in `log/pending.md`. **No key is written twice** in one mapping at any depth — YAML would silently keep only the second.
- [ ] Required fields — beans: `bean, kind, title, status, summary (warn), identity, provenance`; mappings: `mapping, kind, summary`.
- [ ] Enum-valued fields (`status`, `identity.status`, `provenance.src`, anchor `class`/`authority`) match the VOCABULARY — this checklist deliberately no longer restates the values, because a second copy of a rule is a rule that can disagree with itself. `python3 bin/dmrules.py` prints them all, derived from the law in force.
- [ ] **Every anchor** has `key, value, establishing`. Since P4 `establishing: true|false` is the load-bearing split and `class` is an optional HINT at *why*; where a vocabulary term declares an anchor policy it OVERRULES the bean.
- [ ] **Establishing anchors unique** — no hardware/logical anchor value shared by two beans (that's one object → merge).
- [ ] **Links resolve** — each `{bean|mapping: X[, field]}` points to an existing target + field. Acyclicity is declared PER RELATION via `schema.dag`, not fixed to one list of sections.
- [ ] **Every rule is passed by the objects too** (the reverse gate): a declared position is occupied, or declared vacant with a reason.
- [ ] **No duplicate authoritative IP** (one owner; `shared_identifiers:`/`scope:` for legit shared).
- [ ] `VOCAB.md` pins `extends: std-vocab@<ver>` matching the installed std-vocab.
- [ ] A list term merged member by member declares an identity its entries carry: every unmarked `by-` field is required on each entry, and a `?` field is declared but optional (MERGE.md, std-vocab@8.0).

### Part B — judgment (writer confirms; the gate cannot)
Part B is not a leftovers list. It is the set of things a machine **cannot** check, kept separate so that what the gate does check is unambiguous. Items leave this list when they become mechanizable — three have.

**Unenforceable is not unsupportable.** Run **`python3 bin/dmreview.py`** before a judgment pass: it gathers the evidence each item below needs — relative time words that fix prose to a day the reader cannot identify, dates baked into key *names*, near-duplicate values the verbatim check cannot see, anchors claiming operator authority on beans the operator did not assert, keys used exactly once. **Nothing it prints is a violation**, and it always exits 0 by design: a judgment aid that can fail a build becomes a rule, and a rule encoding a judgment nobody made launders an opinion into an enforcement. If a signal ever earns enforcement, it moves to Part A with evidence.

- [ ] **Abstraction, not force-fit:** an uncategorizable unique datum goes to `attributes:`/`details:` intact, rather than being bent into a term that nearly fits. *Judgment: the gate can see that a term's shape is satisfied, never that the shape was the right one.*
- [ ] **Provenance honest:** `src`/`by`/`as_of` reflect who really said it and how they know. *Judgment, and tested: a rule flagging `authority: operator-asserted` on a bean whose `provenance.src` is `observed` was considered and REJECTED — per-anchor authority legitimately differs from a bean's default, which the model explicitly supports. The real failure mode is an agent stamping operator authority on a value it minted itself, and no gate can see that; only a reader comparing the claim to reality can.*
- [ ] **Identity right:** the anchor genuinely identifies the object. *The mechanical half is enforced (establishing flag, per-nature minimums, a term's anchor policy overruling a bean). What remains is whether the value is TRUE.*
- [ ] **External truth referenced, not mirrored** ("owned by X, do not hand-edit"). *Verbatim duplication is now caught (Part A); a paraphrase of someone else's truth is not, and paraphrase is the more common way this goes wrong.*
- [ ] **Capsule / paper-durable (Rule 6):** obvious keys, explicit units, absolute dates, reads correct cold years later. *Dates and shapes are enforced; whether prose actually reads correctly to a stranger is not.*
- [ ] **No silent generalization:** an uncovered case ran the exception-ack protocol. *The reverse gate now forces a declared position to be occupied or explained, which covers the vocabulary half. The bean half — quietly treating a new case as an old one — remains judgment.*
- [ ] **One logical change per commit**, message `"<id>: <what> (<why>)"`. *Judgment: a commit's coherence is not countable.*
- [ ] **The evidence came from the ESTATE, not from a test.** Before recording that something is true of the world — in a bean, in the journal, in a note to a future session — check what actually demonstrated it. *Judgment, and learned the hard way on 2026-08-02: an acceptance fixture used `analysis_cache.policy: skim` for no reason; a scratch garden copied it; the gate correctly warned that a garden had occupied a Tier-0 vacancy; and that warning was written down as "a second garden has genuinely occupied it, withdraw the vacancy". The occupant was a fixture we wrote. The gate was right about what it could see — SOME garden occupies this — and the leap from "a garden" to "the estate" is the part no gate can make for you. Note the distinction: deliberately occupying a vacant position is CORRECT in `test/golden.py`, where the mutation exists to prove the gate refuses it. The question is whether the thing was the subject of the test or an incidental value that wandered in.*

**Moved to Part A this session** — no longer your job to remember:
- *Single owner of a fact* → the gate warns when one long authoritative value appears verbatim in two beans. It is a REGRESSION GUARD: this rule was violated earlier today, when one framework description was restated in twelve beans, and it is silent now only because that was fixed.
- *Authority respected* → a staged change to `VOCAB.md` / `GARDEN.md` / `std-vocab.md` now REQUIRES a journal entry. A rule-change was previously the one write not required to be logged, which is exactly backwards: it is the most consequential write in the system.
- *Provenance logged* → the journal binding (already mechanical), now covering rule-changes too.

### Part C — editing (how a write is MADE, not what it says)
Beans and vocabularies are **structured documents edited with text surgery**, because their comments and layout carry meaning a YAML round-trip would flatten. Text surgery is blind to structure, and in one session it broke documents five times. Part C exists because the *content* being right does not make the *edit* safe.

**Prefer operations that PREVENT the mistake** — they address a document by **key**, not by offset, pattern or indent depth, so the shapes that caused every incident cannot be expressed:
- [ ] `dmsafe.insert_after(path, key, block)` — lands after a key's **whole block**, never between the key and its children. *(Incident 1: an insert after the key's LINE broke nine documents at once.)*
- [ ] `dmsafe.replace_block(path, key, block)` — the span comes from the structure, so it cannot run too far. *(Incident 2: a stop-pattern swallowed four blocks and left valid YAML behind.)*
- [ ] `dmsafe.remove_block(path, key)` — the removal is declared by **calling it**; there is no flag to forget.
- [ ] `dmsafe.set_nested(path, 'a.b', block, expect=N)` — a **nested** key addressed by path (`a.b`, or `a[].b` to reach into each list item), anchored to its **ancestry** rather than to an indentation string. **State how many locations you expect**: incident 5 meant one `poles:` and silently changed four, and the count is the safeguard — not the depth.
- [ ] A missing landmark **fails loudly** instead of silently matching nothing, and so does a path matching **zero** locations. *(Incident 3, and its nested twin.)*
- [ ] `dmsafe.flow_set(path, 'identity.anchors[key=fqdn].authority', v, expect=N)` — reaches **inside** a one-line flow mapping (`{ a: 1, b: 2 }` — most anchors). A **selector** picks the item by a field of its own, and only the **value bytes** change: quoting, spacing, key order and trailing comments survive, which is the whole reason these documents are edited as text rather than round-tripped.
- [ ] `dmsafe.flow_insert(path, 'identity.anchors[]', 'establishing', 'false', after='class', expect=N)` — adds a key to flow mappings, optionally right after a named one. *(This is the P4 migration's shape: dozens of anchors given an `establishing` flag by blind regex. It worked, and nothing would have told me if it hadn't.)*

> **dmsafe is opt-in — it protects only the writes you remember to route through it.** That cost is real: a test fixture reproduced incident 4 an hour after the tool preventing it was built. So the **gate now runs dmsafe's own comparison against the staged blobs**: a destroyed document, a **gutted** key (one that survives while its subtree is emptied — invisible to a top-level check), and a bean left with **no human body** are all refused at commit time, whether or not the edit went through the tool. Use the operations because they are better; rely on the gate because it is not optional.

**Fall back to `dmsafe.edit(path, transform, allow_remove=[...])`** only when no operation fits. It cannot prevent the mistake, but it CATCHES it: it parses before and after, compares **leaf paths**, and rolls back an edit that breaks a document, empties it, or loses content you did not declare.
- [ ] **Declare removals.** Removing is fine; removing *by accident* is not, and the only difference is whether you said so.
- [ ] **A pattern that matched nothing is a bug**, not a no-op — that is how a file you believe you fixed stays broken. Refused.
- [ ] Never `open(path, 'w')` directly. *(Incident 4: it truncated the file before the read that was supposed to supply its content.)*

**Every operation REQUIRES `expect=N` — there is no default.** The count is the safeguard, not the addressing: across six incidents the cause was never *where* an edit landed but that it landed in more places than intended with nothing saying so. A default would let you skip the one step that makes intent explicit, which is why `allow_remove`, a vacancy's reason and an explicit `enforced_by: none` are all required too.
- [ ] **Measure, then act:** `dmsafe.count(path, 'a[].b')` → `(n, kind)`. It reports zero rather than raising, so it is always safe to ask. Requiring a count without providing a way to obtain one would only invite a guess.
- [ ] Over-match, zero-match, `expect=0` and a **duplicated top-level key** are all refused rather than resolved to the first thing found.
- [ ] Setting a value to what it already is is a **no-op**, and refused — the same rule as a pattern that matched nothing.

**What none of this catches:** an edit that is well-formed, loses nothing, and is simply *wrong*. That is Part B.

### Part D — reading (measure before you look, and carry what you must hold in mind)
Part C makes a WRITE safe. Part D is the step before it: deciding what to read. The same discipline — **measure, then act** — and the same reason: the expensive mistake is not reading the wrong file, it is reading a gigabyte of source to re-derive something already recorded and still true.
- [ ] **Point a cursor first:** `python3 bin/dmcursor.py <bean | any file path>`. A file path resolves back to the being that owns it, which is the question you actually have — *I am about to touch this file*.
- [ ] **Believe the measurement, not the instinct.** A cache marked `FRESH` has had its staleness key checked against the live source: **use it, do not re-derive it.** A tree marked `DO NOT WALK` is reference-only, and the summary stands in for it.
- [ ] **Carry the attention.** A cursor gathers what must be held in mind — capabilities `FORBIDDEN`/`REQUIRED`, edges `IMPOSSIBLE` or in breach, safety notes — and classifies them: a **LIVE RISK** (forbidden yet possible) demands different care from one *already prevented elsewhere*, and an **UNENFORCED** requirement from one that holds itself.
- [ ] **Attention is inherited along every chain the vocabulary declares acyclic** — habitat, dependency, composition, ownership. A token running on a host is bound by that host's constraints (nothing on a VPS that cannot send mail directly can send it, whatever the token believes), and a being is bound by what it **depends on** and by the whole it is **part of**. The cursor names which chain carried what.
- [ ] Those directions are **derived, not declared**: a relation that must stay acyclic is exactly one you can walk, which `schema.dag` already says. There is **no direction aspect**, and there should not be — a fact stated twice is a fact that can disagree with itself. Which sub-keys hold a ref is read from `ref_fields`/`entry_ref_fields` for the same reason, so a cursor walks the *same* graph the gate resolves.

Run before committing: `python3 bin/dmcheck.py` → must print `0 error(s)`.
Also available: `python3 bin/dmrules.py` (the rules in force, derived) · `python3 bin/dmstale.py` (caches and registrations that have aged) · `python3 bin/dmsafe.py` (parse-check every document) · `python3 bin/dmsession.py list` (who else is working here — Part E).

### Part E — working beside another session (measure who else is here, before you write anything)
Parts A–D assume one writer. **Two sessions in one working copy share one git INDEX**, and the gate reads the *staged* blobs — so `git add -A` from either stages the other's half-finished edits. Session A can be refused for session B's mistake, or commit B's unfinished bean under A's message with A's journal entry attached. **Nothing in Part A catches this: both writes are individually legal.**
- [ ] **Ask first: `python3 bin/dmsession.py list`.** It names every worktree, its branch and how far ahead it is. One line means you are alone and may work in the main copy.
- [ ] **If anyone else is here, take your own copy:** `python3 bin/dmsession.py open <slug> --purpose "…"`. A git **worktree** gives each session its own working copy and its **own index**, sharing one object store — so sessions cannot stage over each other and can still see each other's branches with no network round trip. `open` refuses unless the gate is installed in the shared git dir, and refuses a dirty main copy (a worktree branches from HEAD, so the new session would start *without* those changes).
- [ ] **The slug names the PURPOSE**, not a date and not a host — `split-api-for-multi-version-support`. The session bean it writes is how the next session learns what happened; a skeleton left in place teaches it nothing.
- [ ] **Close from the MAIN copy, never from inside the worktree** — `close` deletes that directory, and deleting your own cwd leaves every later command failing with "Unable to read current working directory". It refuses if you are standing inside it, if the session's gate does not pass, if the worktree has uncommitted changes, and — since 2026-08-08 — if the **main** copy is dirty or mid-merge, because that copy is shared and a merge lands in it.
- [ ] **A close that hits a conflict stops and tells you.** It does **not** auto-abort: the merge state is the information, and MERGE.md §10 is lossless capture first, human choice after. Your branch and worktree are untouched; settle the main copy and re-run.
- [ ] **First thing to suspect on a conflict in `log/journal.md` or a bean:** `git check-attr merge -- log/journal.md beans/<any-bean>.md` → must print `union` and `daftar`. Both attributes were missing between 2026-08-07 and 2026-08-08 — deleted without mention by a commit about something else — and while they were gone, two sessions appending *entirely unrelated* journal entries conflicted every time. Git does not warn when a merge attribute is missing, any more than when it names a driver that is not configured.

**Changing the gate itself** is the one write this checklist cannot check, because Part A *is* the gate: a rule it stops enforcing takes its own test green with it. Before proposing one, run the gate you have AND the gate of the release you started from over the same garden, and compare their output byte for byte: it says only that behaviour did not *move*, never that it is right, and a deliberate change is exactly the differences you then read. A test that asserts a finding merely *contains* a phrase is blind to what a refactor actually moves — the order findings print in, an extra finding beside the expected one, a warning promoted to an error, a traceback beside a correct verdict.
