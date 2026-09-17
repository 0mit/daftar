---
spec: merge
status: reviewed          # v0.3 — synthesized from 3 independent high-level reviews. Spec is final; implementation is phased (§15).
version: "0.3"
---
# Gardens, Seeds & Lossless Merge

Extends MODEL.md. Makes daftar **distributed and convergent**: beans authored by different sessions / agents / models in separate **gardens** merge into canonical superset **seeds** — losslessly, order-agnostically, deterministically, without duplicating objects. Synthesized from three deep reviews (CRDT/merge-correctness · identity/dedup · human↔AI cooperation-contract). This document is the agreed design; the engine is `bin/dmmerge.py`.

## 1. Terms of this layer
- **Universal object** — the real thing (host, router, employee, incident). One identity across all time and gardens.
- **Bean** — one *garden's* record of a universal object; may be partial.
- **Seed** — the most-inclusive bean: the canonical superset of every garden's bean of that object. Merge targets are always seeds.
- **Garden** — an environment/collection of beans (a working copy: session/repo/scan), declared by `GARDEN.md`.
- **Identity anchor** — the *typed* stable identifier(s) that decide sameness (the merge key), decoupled from the garden-local filename `id`.

## 2. Invariants (the guarantees)
1. **Lossless** — the merge drops no fact and no log line; even an auto-subsumed value is preserved in provenance (recoverable). Correction is possible only as a **logged, attributed supersession**, never a silent delete.
2. **Order-agnostic** — commutative **and** associative **by construction** (§5 CRDT lattice join), not by prose rules that "hope to compose."
3. **Idempotent** — `merge(A,A)=A` **on canonical form**; a seed is a fixed point of `canon`. Merge ≝ `canon(join(canon(A),canon(B)))`. (Idempotence is *not* the dedup mechanism — identity resolution §4 is.)
4a. **Merge-determinism (HARD invariant)** — same input beans ⇒ byte-identical seed, for any model/agent.
4b. **Scan-convergence (METRIC, not a guarantee)** — two models scanning the *same environment* produce *mergeable* beans. Best-effort; measured by a golden test (§11); never promised.
5. **No duplicate objects** — identity is a **global partition** (union-find §4), not a pairwise/arrival-order decision.
6. **Governed conflicts** — contradictions and uncertain matches route to the existing **exception-ack** (SKILL.md); a conflict **never blocks capture** (losslessness) — it marks the seed *pending/unclean*. Determinism holds **given the recorded decision** (§10).

## 3. Provenance — see MODEL.md
The provenance/truth-status record and the guard that an `inferred` value may never auto-override an
`asserted-by-human` one were **promoted into MODEL.md**, which is their owner. This section restated them.

## 4. Identity — typed anchors + deterministic resolution
### 4.1 What establishes identity — see MODEL.md and the `anchor_class` term
Since P4 (2026-08-02, human-ratified) an anchor establishes identity iff it carries `establishing: true`.
`class` is a hint at why and decides nothing. This section held the pre-P4 table that made `class`
decisive; it was **deleted rather than annotated**, because a revoked rule left in a spec is read as law
by whoever finds it first. Git holds it.

### 4.2 Anchor capsule (mandated, validated, backfilled onto every bean)
```yaml
identity:
  status: confirmed              # confirmed | provisional (anchorless/weak → provisional)
  anchors:
    - { key: wg_pubkey, value: "…", class: hardware, scope: global, observed: 2026-07-30, until: null, authority: operator-asserted }
  replaces: { bean: <old-device> }   # device-swap lifecycle link (optional)
  aka: [host-a, laptop-7]            # garden-local ids seen for this object
```
### 4.3 Minimum-anchor policy — per NATURE, see MODEL.md and VOCAB `natures:`
Since P3/D1 the anchor family and the minimum count hang off the bean's **nature**, not its kind, and are
declared once in the `natures:` registry. The per-kind table that stood here routed through five kinds the
gate does not accept, and is deleted.

### 4.4 Resolution algorithm (deterministic)
1. **Normalize** each anchor via its VOCAB term. 2. **Fuse edges** = equal **hardware/logical** anchors (same key+scope, overlapping validity); **assoc edges** = equal network/role anchors (candidates, never fuse). 3. **Components** = connected components over **fuse edges only** (union-find). 4. **Component-wide contradiction check**: a differing **single-valued** establishing anchor → don't fuse → split + exception-ack (set-valued keys, e.g. dual-NIC MACs, may hold several). 5. **Lifecycle**: a `replaces:` link = same role / different device — do **not** fuse device beans; hardware differences across it are expected, not contradictions. 6. **Assoc promotion**: a network/role edge that is the *only* link between components is surfaced, not auto-merged (operator promotes via ack). 7. **Articulation-point / merge-bomb guard**: if removing one bean splits a component into hardware-distinct sub-clusters, that bean carries two identities → flag → ack. 8. **Canonical seed-id** = kind-prefixed slug of the lexicographically-least **establishing** anchor value; garden-local ids → `aka:`. See §4.6 for the case where a component has no establishing anchor at all. 9. **Post-merge**: run `dmcheck.py` on the result; any cross-seed single-owner collision (e.g. `.160` owned twice) → ack demotes one to a `ref:`.
### 4.5 Auto vs user-assisted — deleted
The exact rule that stood here was expressed entirely in terms of "hardware/logical fuse edges", which
§4.1 above revoked. Rewriting it against `establishing:` is real work and is not attempted in prose that
nothing checks; `bin/dmmerge.py` is the implementation, and it now reads the flag.

### 4.6 A component with NO establishing anchor — the id is a name, not an identity
An anchorless component still needs a key, and §4.4.8's rule cannot supply one. It falls back to the
component's least garden-local id — and that fallback is **not identity-bearing**: §16 is explicit that
garden-local ids may legitimately collide, because id ≠ identity. Two such components can therefore
propose the *same* seed id while being genuinely distinct objects that were correctly not fused.

Three rules, added 2026-08-02 (operator-directed, after the collision was found to silently drop a bean):

1. **One seed per component, always.** A component may never vanish into another's key. Losslessness
   (invariant 1) is not conditional on identity being strong; it is exactly where identity is weakest that
   a dropped object is least likely to be noticed.
2. **Colliding ids are disambiguated by component membership** — the sorted set of `(garden, bean-id)`
   members, hashed. Components *partition* the node set, so two distinct components can never share that
   value: uniqueness is a property of the partition, not a hope about a hash. It is order-agnostic, so
   invariant 4a (merge-determinism) still holds, and an anchor-derived id is never suffixed.
3. **The seed says which it is.** `identity.id_basis` is `anchor` or `garden-local`; a disambiguated seed
   also carries `identity.id_collision` naming the id it shared. Without this the two kinds of id are
   indistinguishable by looking at the string while meaning entirely different things. A `garden-local`
   seed is `identity: provisional` by policy and must never be auto-merged.

If, despite all of the above, two seeds ever collide, `dmmerge` **raises**. Returning a garden with a host
quietly missing from it is the one outcome a merge must never have.

## 5. Fact merge — CRDT lattice join (invariants #1–3 hold by construction)
Each field's value is the **antichain of maximal elements under a per-term subsumption `⊑`**. Merge = union the value-sets, then **reduce to the antichain** (drop every element subsumed by another) — idempotent + confluent ⇒ a true join-semilattice ⇒ commutative + associative + idempotent. Resolved field = antichain size 1; governed conflict = size ≥ 2 (a canonical, deterministic set — governance never perturbs bytes). `⊑`, cardinality, and tie-break live in the **VOCAB `merge:` facet** so MERGE stays a thin driver and conflict logic is *not* duplicated in code:
```yaml
merge: { cardinality: single|set|multi, order: none|prefix|version|cidr|subsumes|by-<field>,
         authority: scanned<operator-asserted<external }
```
Driver: differ + `set` → union (auto); differ + `single` + order-comparable → keep the subsuming value, record the subsumed in provenance (auto); differ + `single` + incomparable → antichain → exception-ack. **`inferred` never subsumes `asserted-by-human`** regardless of `order`.

### 5.1 The merge is GENERIC over top-level keys (2026-08-02, operator-directed)
`dmmerge` merges **every** top-level key a bean carries, and names none of them. Until this date it
gathered `owns`/`attributes`/`details` plus seven keys it handled explicitly and **silently dropped the
other 31** the corpus uses — `nature`, both ownership arcs, `capabilities`, `analysis_cache`,
`code_paths`, `registration`, the whole §4 relation algebra, even `title` and `summary`. Invariant 1 says
the merge drops no fact; it dropped most of them, and no test could fail because the fixtures were shaped
like the implementation rather than like the model.

What a key IS comes from its term's `merge:` facet, read from both vocabulary tiers exactly as the gate
reads them, so the merge and the gate cannot disagree:

- **`single`** — the value is ONE atom. Two gardens disagreeing about it is a real conflict, not a pick.
- **`set`** — union, deduplicated, sorted by canonical string (total over every JSON type).
- **`multi` + `order: by-<field>`** — a COLLECTION whose members merge independently. A mapping keys by
  its own keys (`by-facet`, `by-capability`, `by-cache-type`, `by-key`); a list of entries keys by its
  declared **identity** — one field (`by-path`, `by-role`) or several joined by `+`
  (`by-protocol+system+at+port?`), so two gardens describing the same path merge that path instead of
  unioning two near-identical entries. A trailing `?` says an entry may lack that field and its absence is
  part of the identity; an entry missing an unmarked field is **refused**, never matched by its content.
  The gate holds the declaration to the schema: an unmarked field must be required on every entry, a `?`
  field must be declared and not required (std-vocab@8.0). Two gardens that each know a *different* member
  end up with both; two that disagree about the *same* member conflict on that member alone.

A key no term describes is merged by **shape** — mapping → collection, list → set, scalar → atom — and
its name is reported, never hidden, because a shape guess can still be the wrong guess. Closing that gap
means declaring a `merge:` facet on the term, not editing the driver.

Three consequences worth stating. `kind` resolves to a **scalar** or a conflict; it used to emit a list,
which `dmcheck` cannot resolve. `provenance` is kept **per garden** rather than merged, because two
gardens having different provenance is not a disagreement about the world and merging it would
manufacture a conflict on every fused seed. And the git merge driver verifies its own OUTPUT — every
top-level key either side had must appear in the rendered bean, measured rather than declared — and
**refuses**, leaving the file untouched, if any is missing. A driver that overwrites a working file with
a bean stripped of its nature has destroyed the working copy, and the gate that would refuse that bean
only runs afterwards.

### 5.2 Merging BEANS is only half a merge (2026-08-02, operator-directed)
`dmmerge` converged two gardens' data while their TYPE SYSTEMS stayed divergent. A merged corpus could
therefore hold a bean of a kind the merged law never declared, or a bean in breach of an obligation the
garden that wrote it had never adopted — checked by nobody, because each garden's gate only ever saw its
own half. Promoting kinds to Tier-0 shrank this; it did not close it.

A garden's law is three things: its **Tier-0 pin**, the **profiles** it opted into, and its **local
overlay**. All three reconcile before the beans mean anything.

- **Different Tier-0 pins BLOCK the merge.** This is not a conflict to record and carry — it is a reason
  the merge should not happen. Two gardens on different versions are not speaking the same language, and
  merging would validate one garden's beans against the other's law. Adopting a version is a
  human-ratified rule-change; a merge tool may not perform one on someone's behalf.
- **Local terms and kinds union by name.** Identical definitions merge silently. The same name defined
  DIFFERENTLY is a conflict for a human: a term is law, two readings cannot both hold, and picking one
  quietly would re-classify beans in the garden that loses.
- **Profiles union**, and the inheritance is stated out loud. A profile only one garden opted into
  becomes an obligation for the merged garden — correct, because the beans that need it are now in the
  corpus, but never silent.

Then the merged corpus is checked against the merged law, which is what "merges cleanly" MEANS: no kind
it uses is undeclared, no top-level key it uses is undeclared, and no bean owes a required term it lacks.
A merge whose data converges and whose law does not is reported as such and exits non-zero.

Two consequences worth stating. Merging can HEAL a divergence: a garden's `domain` bean written without
`registration` is covered once it fuses with another garden's bean that has it. And the obligation set is
built from the opted-in profiles only — an early version built it from every profile the vocabulary
offers and reported that a garden owed `code_paths` for a profile it had never opted into, which is the
precise mistake the profile mechanism exists to prevent.

## 6. Canonical form — byte-identical seeds  (do NOT hash YAML)
- **Two layers:** authoring = YAML front-matter + Markdown body (unchanged, ergonomic). **Canonical/compare/hash = a derived JSON projection via JCS (RFC 8785) + SHA-256.** YAML is unsafe as a hash oracle (coercion, comment loss, ordering, float round-trip).
- **Normalization (declared in VOCAB handling):** numbers = integers or `{value, unit}` decimal-strings — **no binary floats**; strings NFC + trim + LF; per-type canonicalizers (IP → `ipaddress` normal form, FQDN → IDNA+lowercase, MAC → lowercase colon); map keys sorted; **lists declared per key as `set-list` (dedup+sort) vs `sequence-list` (order preserved)** — never blanket-sort sequences; conflict/provenance lists canonically sorted.
- **Purge every `now()`-derived value from canonical bytes** (`merged-at`, `created`, scan times) — timing lives in git metadata only, outside the hash. (Else determinism/idempotence break.)
- **Markdown body** = grow-set of provenance-stamped sections `{garden_id, text}`, unioned, rendered sorted by garden-id, and **excluded from the hash / determinism guarantee** (prose is not cross-model convergent — say so honestly; only structured front-matter carries determinism).

## 7. Log merge (lossless, idempotent, order-agnostic)
- **entry-id = SHA-256(JCS{utc_ts, actor, garden_id, seq, body})** — keyed on **origin identity (garden+seq)**, not raw content, so two coincidentally-identical events stay distinct and re-merging the same garden is idempotent. Hash a structured object, never a concatenated string.
- Logs are a **global grow-only set** keyed by entry-id, each entry **subject-tagged with bean-refs**; a bean/seed's history is a deterministic filter view. Bean-scoped entries travel & merge with the bean; a garden-global journal holds cross-bean narrative.
- **Total order = (utc_ts, garden_id, seq, entry-id)** — deterministic under clock skew (explicitly: deterministic, not guaranteed causal; add Lamport clocks only if causal order is ever required).

## 8. Merge is a semantic operation — git never text-merges
- **`dmmerge`** (a tool, alongside `dmcheck.py`) computes the CRDT join, renders canonical output, then commits. Git provides durability / blame / rollback / transport **only**.
- Wire a **custom git merge driver** via `.gitattributes` (`beans/* mappings/* seeds/* log/* merge=daftar`) so even `git merge` dispatches to `dmmerge` instead of the line-based engine.
- **The gate covers merge outputs:** the resulting garden must re-pass `dmcheck.py`; a cross-seed single-owner collision is a conflict → exception-ack.

## 9. The Contract of Parts — see MODEL.md
The full 11-row table lives in **MODEL.md**, which is its single owner. It had five copies: here,
MODEL.md, SKILL.md, `GARDEN.md` `policy.authority`, and the class letters in `log/pending.md`. The four
others are pointers now. Classes referenced by letter elsewhere (F identity, G vocab/law, J merge) are
defined there.

## 10. Exception-ack for merge — async & scalable
- Exceptions gain `status: proposed|acked`, `proposed_by`, `acked_by`.
- **Park-and-proceed:** the AI records a *proposed* resolution **plus the related+sibling neighborhood it would have shown**, does everything safe around it, and the human ratifies a **single pending-decisions queue** later (no blocking for overnight/batch merges).
- **Precedent auto-applies:** once acked, it generalizes to matching cases without re-prompting; only a genuinely novel neighborhood re-triggers the protocol.
- **Pending vs clean:** an unresolved conflict **commits** (lossless capture) but the seed is marked **unclean** (`status: at-risk` + `merge_open:`); the gate **warns**, never hard-fails. Determinism: a seed is reproducible **post-ratification**; a pre-ratification seed is legitimately **pending**.

## 11. Determinism — hard guarantee vs soft metric
- **Hard (merge-determinism):** delivered by the CRDT join (§5) + JCS canonical form (§6) + purged timestamps + deterministic seed-id (§4.4).
- **Soft (scan-convergence):** a **golden CI test** — run N models on one fixed environment, gate on field-overlap / conflict-rate. **Levers:** closed VOCAB + required per-kind `schemas/` slots with **enumerated value domains**; per-type canonicalizers; a fixed anchor-priority list; a **per-kind extraction checklist** (so models *probe* the same attributes, not merely format them alike). **Quarantine:** free-text `attributes:`, prose, `open:` questions, scan times are provenance-tagged **non-authoritative** — never a conflict source, never in the hash.

## 12. VOCAB additions this requires (blocking for the acceptance test)
New terms **mac, serial, hostname, fqdn, emp_id, wg_pubkey**; every term gains an **`anchor: {class, establishing}`** facet and a **`merge: {cardinality, order, authority}`** facet; the `identity.anchors` capsule is mandated + validated + **backfilled onto the 5 existing beans**. Extend `dmcheck.py`: anchor presence/class/normalization, per-fact provenance shape, `merge:` facets, cross-seed single-owner collisions, and journal↔commit binding.

## 13. GARDEN.md (manifest)
`garden: <id>`, `origin: "session/env"`, `models: […]`, `created:` (git-metadata, not canonical), `seeds_from: […]`. Lets a cold agent know which garden it is in and what has merged.

## 14. Acceptance test — two phases (don't conflate them)
- **Phase A (hard):** synthetic gardens permuted across **all** merge orders → assert **byte-identical** seeds (proves order-agnosticism + determinism).
- **Phase B (soft):** real multi-model scans of the **≥3 mail-repeated-delivery sessions** → merge in any order → confirm **every discovery present, deduplicated, lossless**, only genuine conflicts surfaced; **measure** convergence. Do not read Phase-B prose differences as a determinism failure. (The "mail-delivery incident" is an *anchorless* kind → incident dedup is user-assisted by design.)

## 15. Implementation phasing — superseded
The P1-P4 gates named here were all shipped, and their numbering **collides head-on** with the v2 P0-P7d
used by `log/journal.md`, `test/golden.py`'s section headers and both design beans. Two numbering schemes
in one repo is a trap for a cold reader, so this one is deleted rather than renumbered. What actually
happened is in the journal.

## 16. Resolved by the reviews (settled open questions)
- Unresolved conflicts **never block capture** — mark pending/unclean; gate warns.
- Logs: **per-bean** (travel/merge with the bean) + a garden-global narrative with bean-refs.
- Canonical seed-id = least **establishing** anchor; garden-local ids → `aka:`. The anchorless case is §4.6.
- Determinism is **post-ratification**; a pre-ratification seed is *pending*, not clean.
- **id-clash removed** from the contradiction path (garden-local ids may legitimately collide — id ≠ identity).
- Idempotence is **not** the dedup mechanism (identity resolution is).

## 17. Still open (deferred)
- Causal (Lamport) log ordering — only if ever required.
- Multi-operator **authority** (which human may ratify which kinds) — ties to authenticated identity.
- Offsite mirrors / generated DR deliverables — deferred per operator.
