---
spec: merge
status: in-force
---
# Gardens, canonical beans, and lossless merge

Extends MODEL.md. It states what the merge engine, `bin/dmmerge.py`, does: beans recorded in different gardens —
working copies, sessions, agents of different makes, the gardens of different people — merge into one **canonical
bean** per object, losslessly, in any order, with the same bytes for the same inputs, and never two beans for one
object. What was designed and is not built is listed at the end, under its own heading; nothing above that heading
is a promise.

## 1. Terms of this layer
- **Object** — the real thing a bean records: a host, a person, an agreement. One identity across gardens and time.
- **Bean** — one garden's record of an object. It may be partial.
- **Canonical bean** — what the merge makes of one object: every garden's record of it joined, each value with the
  gardens that said it and how they knew. `bin/dmmerge.py` prints each under the key `seed`; that is not `seed/`,
  the kit a garden is grown from.
- **Garden** — a git repository of beans, named by `GARDEN.md` and identified by `garden_id` (MODEL.md). A merge
  input is a garden directory, a working copy of one, or a proposal (§16).
- **Identity anchor** — a typed fact that says which object a bean records (MODEL.md, Identity). Anchors are the
  merge key; a bean's file name is not.

## 2. Invariants
1. **Lossless** — the merge drops no value. A value another subsumes is kept in the canonical bean's provenance; a
   disagreement keeps every value. A value is corrected only by a recorded, attributed change, never by a silent
   delete.
2. **Order-agnostic** — commutative and associative by construction: identity is a partition computed over every
   input at once (§4), and each field is a join (§5).
3. **Idempotent** — merging a garden with itself changes nothing, and a canonical bean merged again is itself:
   merge = `canon(join(canon(A), canon(B)))`. Idempotence is not how duplicates are found; identity is (§4).
4. **Deterministic** — the same input beans give byte-identical canonical beans, whoever runs the merge (§6).
5. **No duplicate objects** — identity is a global partition, never a pairwise decision in arrival order.
6. **Governed conflicts** — a disagreement never blocks capture: it is kept, both values, and the bean is marked
   unclean for a person to settle (§10; MODEL.md, the Contract of Parts). A canonical bean is final once that
   person has decided; before, it is pending.

## 3. Provenance — see MODEL.md
The provenance record, and the guard that an `inferred` value may never auto-override an `asserted-by-human` one,
are stated in MODEL.md, which owns them.

## 4. Identity — typed anchors, resolved over every input at once
### 4.1 What establishes identity — see MODEL.md
An anchor establishes identity if and only if it carries `establishing: true`, and the merge reads that flag and no
other. Which anchors may establish for a bean is the gate's business before the merge: the nature's family
(`identity_policy.establishing_family`), read through the anchor's class (`anchor_class`).

### 4.2 The anchor capsule
```yaml
identity:
  status: confirmed              # confirmed | provisional
  anchors:
    - { key: serial, value: "…", class: hardware, establishing: true, observed: 2026-07-30 }
    - { key: ip, value: "…", class: network, establishing: false, provenance: { src: observed, by: "…", as_of: 2026-07-30 } }   # its own record, because it differs from the bean's
  aka: [host-a, laptop-7]        # garden-local ids this object has been recorded under
```
What an anchor may carry is `identity_policy.anchor_attrs`.

### 4.3 How many establishing anchors — see MODEL.md and `natures`
The minimum hangs off the bean's nature, declared once in the `natures` registry.

### 4.4 Resolution, as built
1. **Normalise** each anchor value (Unicode NFC, trimmed; an IP address in its normal form) and compare it in its
   term's compare form where the term declares one — a serial ignoring case and spaces.
2. **Fuse edges** join two beans that carry the same establishing anchor: the same key and the same compared value.
   An anchor that does not establish joins nothing.
3. **A bare minted name fuses only within its own garden.** The value of an anchor term marked `minted` that is not
   written `<garden_id>/<name>` (`identity_policy.minted`) identifies within the garden that minted it, so its fuse
   edge is keyed by that garden's identity as well. Each input carries its garden's identity: `garden_id` read from
   git for a directory that is the top of a garden's own repository, `from.garden` for a proposal. An input whose
   garden cannot be named is a garden of its own — never assumed to be another input's. A qualified name, and every
   anchor whose term is not minted, fuses across gardens as in step 2.
4. **Components** are the connected components over fuse edges (union-find), computed over every input at once.
5. **Two records of one anchor** that differ only in how they are known resolve by the `provenance_src` rank. Any
   other difference about what an anchor is — whether it establishes, its class — is kept in
   `identity.anchor_conflicts` for a person (class F), and meanwhile the canonically least record is used, so the
   result does not depend on which garden came first.
6. **Candidates.** Equal bare minted names from different gardens, on beans not already one object through another
   anchor, are reported — "CANDIDATES — a person decides (class J)" — and never fused. Whether two names are one thing
   is a person's decision; the name then kept is class F: the garden that recorded the thing first qualifies it, and
   the other takes it in.
7. **The canonical bean's id** is its kind, then a slug of its least establishing anchor value; the gardens' own
   ids become `aka`. Two components whose ids coincide — two gardens' equal bare names, or no anchor at all — are
   told apart as §4.6 says.

After a merge the merged garden must pass its own gate, like any garden (§8).

### 4.5 (nothing in force)
The number is kept so the sections after it keep theirs.

### 4.6 A component with NO establishing anchor — the id is a name, not an identity
An anchorless component still needs a key, and §4.4.7 cannot supply one from an anchor. It falls back to the
component's least garden-local id — and that fallback is **not identity-bearing**: a garden-local id is a name, and
two gardens may give one name to two objects. So may two gardens' bare minted names (§4.4.3), which is why the
rules below apply to them too.

Three rules:

1. **One canonical bean per component, always.** A component may never vanish into another's key. Losslessness
   (invariant 1) is not conditional on identity being strong; it is exactly where identity is weakest that a dropped
   object is least likely to be noticed.
2. **Colliding ids are disambiguated by component membership** — the sorted set of `(garden, bean-id)` members,
   hashed. Components partition the inputs, so two distinct components can never share that value: uniqueness is a
   property of the partition, not a hope about a hash. It is order-agnostic, so invariant 4 still holds, and an
   id derived from an anchor that identifies everywhere is never suffixed.
3. **The canonical bean says which it is.** `identity.id_basis` is `anchor` or `garden-local`; a disambiguated one
   also carries `identity.id_collision`, naming the id it shared. A `garden-local` canonical bean is provisional and
   is never merged automatically.

If, despite all of the above, two canonical beans ever collide, `dmmerge` **raises**. Returning a garden with an
object quietly missing from it is the one outcome a merge must never have.

## 5. Fact merge — a lattice join (invariants 1–3 hold by construction)
Each field's value is the **antichain of maximal elements under a per-term subsumption order**. Merge unions the
value-sets, then reduces them to the antichain (drops every element another subsumes) — idempotent and confluent, so
a join-semilattice: commutative, associative, idempotent. A field resolved to one value is settled; two or more is a
governed conflict, kept as a canonical, deterministic set. Cardinality and order live in each term's `merge:` facet,
so the engine names no term and the conflict logic is written once:
```yaml
merge: { cardinality: single|set|multi, order: none|version|cidr|instant|containment|by-<field>|"a<b<c" }
# and, once, on provenance_src: { order: "generated-by-tool<inferred<observed<asserted-by-human", borrows: generated-by-tool }
```
Values differ and the term is a `set`: union. Values differ, the term is `single` and the order compares them: keep
the subsuming value and record the subsumed in provenance. Values differ and nothing compares them: both are kept, a
conflict for a person (§10). **`inferred` never subsumes `asserted-by-human`**, whatever the order says. A value
several gardens agree on keeps the highest source the rank declares; a `generated-by-tool` value weighs as the
weakest source it names in `provenance.from`.

### 5.1 The merge is GENERIC over top-level keys
`dmmerge` merges **every** top-level key a bean carries, and names none of them.

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
  field must be declared and not required. Two gardens that each know a *different* member end up with
  both; two that disagree about the *same* member conflict on that member alone.

A key no term describes is merged by **shape** — mapping → collection, list → set, scalar → atom — and
its name is reported, never hidden, because a shape guess can still be the wrong guess. Closing that gap
means declaring a `merge:` facet on the term, not editing the driver.

Three consequences worth stating. `kind` resolves to a **scalar** or a conflict, never a list. `provenance` is kept
**per garden** rather than merged, because two gardens having different provenance is not a disagreement about the
world and merging it would manufacture a conflict on every fused bean. And the git merge driver verifies its own
OUTPUT — every top-level key either side had must appear in the rendered bean, measured rather than declared — and
**refuses**, leaving the file untouched, if any is missing.

### 5.2 Merging BEANS is only half a merge
A garden's law is three things: its **Tier-0 pin**, the **profiles** it opted into, and its **local
overlay**. All three reconcile before the beans mean anything.

- **Different Tier-0 pins BLOCK the merge.** This is not a conflict to record and carry — it is a reason
  the merge should not happen. Two gardens on different versions are not speaking the same language, and
  merging would validate one garden's beans against the other's law. Adopting a version is a
  human-ratified rule-change; a merge tool may not perform one on someone's behalf.
- **Local terms and kinds union by name.** Identical definitions merge silently. The same name defined
  DIFFERENTLY is a conflict for a person: a term is law, two readings cannot both hold, and picking one
  quietly would re-classify beans in the garden that loses.
- **Profiles union**, and the inheritance is stated out loud. A profile only one garden opted into
  becomes an obligation for the merged garden — correct, because the beans that need it are now in the
  corpus, but never silent.

Then the merged corpus is checked against the merged law, which is what "merges cleanly" MEANS: no kind
it uses is undeclared, no top-level key it uses is undeclared, and no bean owes a required term it lacks.
A merge whose data converges and whose law does not is reported as such and exits non-zero. The obligation
set is built from the opted-in profiles only, and a merge can heal a divergence: a bean written without a
required term is covered once it fuses with another garden's bean that has it.

## 6. Canonical form — the same bytes for the same inputs
- **Two layers.** Beans are written as YAML front matter and a Markdown body. They are compared and hashed as a JSON
  projection, never as YAML, which coerces types, loses comments and orders keys as it pleases.
- **What the engine writes:** map keys sorted; no insignificant whitespace; UTF-8, unescaped; every string NFC and
  trimmed; an IP address in its normal form; a date or moment in ISO 8601; an anchor in its term's compare form; a
  `set` sorted by canonical string; a conflict's values and every `seen_in` sorted. This is close to JCS (RFC 8785)
  and is not it: a number is written as Python's `json` writes it, not re-serialised by ECMAScript's rules. A
  quantity's count is never a float (MODEL.md, Agreements and money), and the gate warns about a float in `owns` or
  `details`.
- **The fingerprint** of each canonical bean is the SHA-256 of that text; the merged garden's fingerprint is the
  SHA-256 of the sorted per-bean hashes, so it does not depend on the order of the inputs.
- **No clock value enters a canonical bean.** The engine writes none; a merged bean's provenance says
  `as_of: merged`, and when a merge happened is git's to say.
- **The body is outside the guarantee.** Prose is not convergent across models, and the canonical bean carries no
  body. The git merge driver keeps ours and appends theirs below `<!-- theirs -->`, for a person.

## 7. The journal
- `log/journal.md` and `log/pending.md` merge by git's own union (`merge=union` in `.gitattributes`): both sides'
  entries are kept, none is lost, and none is rewritten.
- **Journals never merge across gardens.** Each garden's journal is its own record. What one garden took in from
  another is written in the receiving garden's journal, by the entry that takes it in, and in the capture on the
  other garden's `garden` bean (§16).

## 8. Merge is a semantic operation — git never text-merges a bean
- `.gitattributes` sends `beans/*.md` and `mappings/*.md` to the `daftar` merge driver (`bin/dmmerge.py --file`),
  so even `git merge` dispatches to the semantic merge instead of the line-based one. It merges ONE bean in place:
  only the keys that differ are rewritten, each key it does not touch keeps its text and its comments, and it
  **refuses**, leaving the file untouched, when the result would lose a key or the body, or when the tree's pin
  disagrees with the vocabulary installed there.
- `python3 bin/dmmerge.py <garden> <garden> …` merges whole gardens: it reconciles the law first (§5.2), prints each
  canonical bean and the fingerprint, and reports the canonical beans with a garden-local id, the candidates (§4.4),
  the keys merged by shape, and whether the merged law covers the merged corpus. It commits nothing. An input is
  labelled by its directory's name, or by its path where two inputs share a name — two gardens on one machine may.
- **The gate covers what a merge makes:** the merged garden must pass `bin/dmcheck.py` like any other commit.

## 9. The Contract of Parts — see MODEL.md
The table lives in **MODEL.md**, which is its single owner. Classes referenced by letter here (F identity, G the
law, J a merge conflict or uncertain identity) are defined there.

## 10. Conflicts: captured first, decided by a person
- **An unresolved conflict commits.** The bean keeps every value (`{ conflict: [...] }` at the path), and is marked
  unclean: `merge_open: true`, with `merge_conflicts:` naming each path — never on `status`, which is a merged term
  of its own. The gate **warns** on such a bean and does not refuse it; its per-term rules stand down on a value
  nobody has chosen yet.
- **A person decides**, picks one value, and clears the marker; that is the recorded, attributed supersession
  invariant 1 allows. A conflict record with no `merge_open` marker is an undeclared merge, and the gate refuses it.
- **An agent that may not decide parks it:** the question goes to `log/pending.md` as `status: proposed`, with the
  neighbourhood a person would need to see, and the agent does everything safe around it (MODEL.md).

## 11. Determinism
**Merge-determinism is the hard guarantee**, delivered by the join (§5), the canonical form (§6), the absence of
clock values, and the deterministic id (§4.4.7, §4.6). The release suites hold it: `test/converge.py` grows gardens
from the seed, lets them diverge, and pulls them back into one — refinements subsume, sets union, a disagreement
keeps both values and marks the bean, every journal entry survives the union, and the result passes its gate.

## 12. (nothing in force)
The number is kept so the sections after it keep theirs.

## 13. GARDEN.md (the manifest)
What `GARDEN.md` may hold is declared in the law, as `manifest` in `seed/std-vocab.md`, and the gate judges the
manifest like an entry. It tells a cold agent which garden it is in, whose it is, and which law governs it; a
garden's identity is read from git and is not among its keys.

## 14. (nothing in force)
The number is kept so the sections after it keep theirs.

## 15. (nothing in force)
The number is kept so that references to the sections after it hold.

## 16. Between gardens: proposals
Two gardens kept by two gardeners never merge whole, and neither writes in the other (MODEL.md, Between gardens: the
mycelium). What passes is a proposal (`bin/dmpropose.py`), and the algebra above serves it unchanged.

- **A proposal is a garden.** Its offered beans, verbatim as committed in the proposing garden, are a merge input
  like any other, carrying that garden's identity (`from.garden`) and its pin; its stubs carry only the identity of
  each bean the offered ones refer to — id, kind, nature, title and identity capsule — and no facts. Its fingerprint
  is the SHA-256 of the canonical JSON (§6) of the offered beans' front matter, so a proposal altered on its way is
  known.
- **`read` is the merge of §4 and §5 with the law reconciled first (§5.2).** It checks the fingerprint, that the
  proposal is addressed to this garden, and that both gardens pin one vocabulary — different pins block, as they
  block any merge. Then it resolves identity over this garden's beans and the offered ones together (§4.4): each
  offered bean FUSES with a local bean, is NEW, or is a CANDIDATE (an equal bare minted name, or a local bean of the
  same kind whose identity is provisional), and for a fusing bean it shows the fields that differ as the join would
  record them; each stub RESOLVES to a local bean or is UNRESOLVED. It writes nothing.
- **`take` applies the join in the working tree.** NEW beans are written with their references rewritten from stub
  ids to the local beans their anchors resolve to; a fusing bean is merged in place, as the git driver merges one
  (§8), a disagreement kept, both values (§10). Nothing is committed: the gardener's commit is the ratification.
- **`take` is idempotent through its capture's staleness key.** Each take records the proposal as a `capture` on
  the proposing garden's `garden` bean, keyed by the proposal, with its fingerprint as the `staleness_key` and the
  proposal itself held under `captures/proposals/`. The same proposal taken twice is the same join taken twice,
  which changes nothing (invariant 3); the second take finds the capture the first left, and there is nothing to
  take.
- **Order-agnostic, because the join is.** Proposals taken in either order reach the same beans (invariant 2); only
  the journal and the captures record the order, as they record every act.
- **Provenance crosses unchanged.** `provenance.garden` is stamped on each offered record that lacks one, once, by
  the proposing garden and only in the proposal; nothing else in a record changes. So the rank of §5, and the guard
  that an `inferred` value never overrides an `asserted-by-human` one, hold across gardens exactly as within one.
- **Journals stay apart (§7).** The proposing garden journals what left, to which garden, under which agreement,
  with the fingerprint; the receiving garden journals what it took, quoting the proposal's journal text as data.

## Designed, not built
Each of these was designed for this layer and is not in the engine. None is in force; each would arrive as a
change to the engine and to this document together.
- **Validity windows on fuse edges**, and **association edges** on equal network or role anchors, surfaced to a
  person as candidates when they are the only link between two components.
- **A component-wide contradiction check**: a differing single-valued establishing anchor inside one component
  splits it, with an acknowledgement for a person.
- **Lifecycle links**: a `replaces:` link between a role and the device that fills it, so a swapped device is not
  fused with the one it replaced.
- **An articulation-point guard**: a bean whose removal splits a component into hardware-distinct parts carries two
  identities, and is flagged.
- **Cross-bean single-owner collisions settled by acknowledgement**, one demoted to a reference.
- **Canonical form by JCS itself** (RFC 8785), and lists declared per key as set-like or sequence-like.
- **The body as a grow-set** of provenance-stamped sections, one per garden, rendered sorted by garden.
- **A log merge by entry id** — SHA-256 over the timestamp, actor, garden, sequence and body — as a global grow-only
  set with subject tags, per-bean logs that travel with the bean, a total order by (timestamp, garden, sequence,
  entry id), and causal (Lamport) order should it ever be needed.
- **Acknowledged exceptions for merge**: exceptions carrying `proposed` or `acked` with who proposed and who
  acknowledged, one queue of pending decisions, and a precedent that applies itself to matching cases.
- **Scan-convergence measured**: several models scan one estate, and a golden test gates on field overlap and
  conflict rate, with per-kind extraction checklists; and the multi-model merge of one estate's sessions, in every
  order, checked for every discovery kept, deduplicated and lossless.
- **Authority among several people**: which person may ratify which kinds, tied to an authenticated identity.
- **Signed proposals**, and **a proposal across two pins**.
- **Offsite mirrors** and generated recovery deliverables.
