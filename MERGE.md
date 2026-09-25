---
spec: merge
status: in-force
---
# Gardens, canonical beans, and lossless merge

Extends MODEL.md. It states what the merge engine, `bin/dmmerge.py`, does: beans recorded in different gardens —
working copies, sessions, agents of different makes — merge into one **canonical bean** per object, losslessly, in
any order, with the same bytes for the same inputs under the same labels, and never two beans for one object. The
gardens of different people meet by proposal, through the same algebra (§16). What was designed and is not built is
listed at the end, under its own heading; nothing above that heading is a promise.

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
4. **Deterministic** — the same input beans, under the same labels, give byte-identical canonical beans, whoever
   runs the merge (§6). A label is recorded in what the merge writes (§8), so the same gardens merged from
   differently named directories give the same facts in other bytes.
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
    - { key: serial, value: "…", class: hardware, establishing: true, observed: now }
    - { key: ip, value: "…", class: network, establishing: false, provenance: { src: observed, by: "…", as_of: now } }   # its own record, because it differs from the bean's
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
3. **A bare minted name fuses only within its own garden.** A value of an anchor term marked `minted` is a name a
   garden gave when it has the minted form (`identity_policy.minted`: `<genos>:<name>`, the genos one the garden
   knows). Written so and not qualified — not `<garden_id>/<genos>:<name>` — it identifies within the garden that
   minted it, so its fuse edge is keyed by that garden's identity as well. Each input carries its garden's identity:
   `garden_id` read from git for a directory that is the top of a garden's own repository, `from.garden` for a
   proposal. An input whose garden cannot be named is a garden of its own — never assumed to be another input's. A
   qualified name, a value of a minted term in any other form — an identifier someone else assigned, such as a
   package's name or a registry number, which no garden may qualify — and every anchor whose term is not minted
   fuse across gardens as in step 2.
4. **Components** are the connected components over fuse edges (union-find), computed over every input at once.
5. **Two records of one anchor** that differ only in how they are known resolve by the `provenance_src` rank. Any
   other difference about what an anchor is — whether it establishes, its class — is kept in
   `identity.anchor_conflicts` for a person (class F), and meanwhile the canonically least record is used, so the
   result does not depend on which garden came first.
6. **Candidates.** Equal bare minted names from different gardens, on beans not already one object through another
   anchor, are reported — "CANDIDATES — a person decides (class J)" — and never fused. Whether two names are one thing
   is a person's decision; the name then kept is class F: the garden that recorded the thing first qualifies it, and
   the other takes it in.
7. **The canonical bean's id** is its genos, then a slug of its least establishing anchor value; the gardens' own
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
   property of the partition, not a hope about a hash. It is order-agnostic, so invariant 4 still holds. An id is
   suffixed only where two components' ids coincide — two gardens' equal bare names, no anchor at all, or two
   different anchor values that slug to one id (`AB_1` and `AB-1` are both `ab-1`).
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

Three consequences worth stating. `genos` resolves to a **scalar** or a conflict, never a list. `provenance` is kept
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
- **`local_terms` and `local_gene` union by name.** Identical definitions merge silently. The same name defined
  DIFFERENTLY is a conflict for a person: a term is law, two readings cannot both hold, and picking one
  quietly would re-classify beans in the garden that loses.
- **Profiles union**, and the inheritance is stated out loud. A profile only one garden opted into
  becomes an obligation for the merged garden — correct, because the beans that need it are now in the
  corpus, but never silent.

Then the merged corpus is checked against the merged law, which is what "merges cleanly" MEANS: no genos
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
- **One fact written two ways is one value.** A quantity's count is compared in one form, the shortest exact decimal,
  as a string: `900`, `"900"` and `"900.00"` are one amount, and so are `"12.50"` and `"12.5"`. A list of entries the
  law keys by an attribute (`keyed_by`, as `paid_by` and `borne_by` are keyed by `party`) is ordered by that key, so
  the same parties in another order are one list. The engine writes the canonical form; a bean keeps what was
  written.
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
  other garden's `garden` bean (§16); what it took in from a chat, which is no garden, in the journal alone.

## 8. Merge is a semantic operation — git never text-merges a bean
- `.gitattributes` sends `beans/*.md` and `mappings/*.md` to the `daftar` merge driver (`bin/dmmerge.py --file`),
  so even `git merge` dispatches to the semantic merge instead of the line-based one. It merges ONE bean in place:
  only the keys that differ are rewritten, each key it does not touch keeps its text and its comments, and it
  **refuses**, leaving the file untouched, when the result would lose a key or the body, or when the tree's pin
  disagrees with the vocabulary installed there. Each side is first read in the words of the law the tree runs: a
  bean changed on a branch or a clone still at 21.0 is translated into 22.0's as `bin/dmupgrade.py` translates a
  garden crossing into it, so the merged bean carries one `genos` and no disagreement over a word; a side that cannot
  be translated without a person is refused. A mapping keeps its `kind`, and is merged as written.
- `python3 bin/dmmerge.py <garden> <garden> …` merges whole gardens: it reconciles the law first (§5.2), prints each
  canonical bean and the fingerprint, and reports the canonical beans with a garden-local id, the candidates (§4.4),
  the keys merged by shape, and whether the merged law covers the merged corpus. It commits nothing. An input is
  labelled by its directory's name, however the path was typed (`.`, a trailing `/.`, a relative or an absolute
  path name one directory); two inputs that share a name — two gardens on one machine may — are labelled
  `<name>@<garden_id>`, and two clones of one garden, which share even that, by their real paths. The label is what a
  canonical bean records in `gardens`, `seen_in` and its provenance. An input whose `GARDEN.md` says `test:` is
  labelled a test garden, and so is each canonical bean it contributes to. What the merge prints does not depend on
  the order of its inputs: the law's conflicts are listed in one order, and of a term two gardens define differently
  the canonically least definition is the one the coverage check reads.
- **The gate covers what a merge makes:** the merged garden must pass `bin/dmcheck.py` like any other commit.

## 9. The Contract of Parts — see MODEL.md
The table lives in **MODEL.md**, which is its single owner. Classes referenced by letter here (F identity, G the
law, J a merge conflict or uncertain identity) are defined there.

## 10. Conflicts: captured first, decided by a person
- **An unresolved conflict commits.** The bean keeps every value (`{ conflict: [...] }` at the path), and is marked
  unclean: `merge_open: true`, with `merge_conflicts:` naming each path — never on `status`, which is a merged term
  of its own. A second conflict on a bean already marked joins the first: `merge_conflicts` becomes the union of the
  paths, and `merge_open` stays one key. The gate **warns** on such a bean and does not refuse it; its per-term rules stand down on a value
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
`test/mycelium.py` holds them between gardens kept by different people: the same canonical beans and candidates in
every order of three gardens, a bare name fused only within its garden, and the refusals of §16.

## 12. (nothing in force)
The number is kept so the sections after it keep theirs.

## 13. GARDEN.md (the manifest)
What `GARDEN.md` may hold is declared in the law, as `manifest` in `seed/std-vocab.md`, and the gate judges the
manifest as itself: every attribute the law declares, in its form, the required ones present, `gardener` a bean the
garden holds of a genos the manifest admits, and nothing the law does not declare. It tells a cold agent which garden
it is in, whose it is, and which law governs it; a garden's identity is read from git and is not among its keys. A
garden that is a rehearsal says so there (`test:`), and a merge labels its input so (§8).

## 14. (nothing in force)
The number is kept so the sections after it keep theirs.

## 15. (nothing in force)
The number is kept so that references to the sections after it hold.

## 16. Between gardens: proposals
Two gardens kept by two gardeners never merge whole, and neither writes in the other (MODEL.md, Between gardens: the
mycelium). What passes is a proposal (`bin/dmpropose.py`), and the algebra above serves it: the identity of §4 and
the join of §5, applied in the receiving garden.

- **A proposal is a garden of a few beans.** Its offered beans, verbatim as committed in the proposing garden, are a
  merge input carrying that garden's identity (`from.garden`) and its pin. A rehearsal is a garden grown by
  germination, with its own id; a clone of a real garden is that garden, and what it proposes is that garden's
  word. Its stubs carry only the identity of each
  bean the offered ones refer to — id, genos, nature, title and establishing anchors — and no facts. Every name it
  carries has the form the law gives a name: a bean or stub id is kebab-case and lands in `beans/`, the proposal is
  `<garden>-<YYYYMMDD>-<HHMM>` (with `-<n>` for a second in one minute; a chat's is `chat-<YYYYMMDD>-<HHMM>`), a
  garden id is twelve hexadecimal digits, and no string in the envelope holds a line break.
- **The fingerprint** is the SHA-256 of the canonical JSON (§6) of the envelope without its fingerprint and the
  body — every byte after the front matter, line ends read as `\n`, blank lines at either end not counted. It shows
  a proposal damaged or carelessly edited on its way. It is not a signature: whoever rewrites a proposal can compute
  it again, so every refusal below holds whatever the fingerprint says — each checks what the proposal claims
  against what the receiving garden holds, never against the fingerprint.
- **`read` writes nothing.** It checks the names, the fingerprint, that the proposal is addressed to this garden,
  and that both gardens pin one vocabulary: different pins block, as they block any merge (§5.2). Only the pins are
  compared; a local term an offered bean relies on is caught by the gate's verdict below. A proposal from a garden
  this garden holds no `garden` bean for is refused, and the refusal prints the two beans a first contact writes
  (MODEL.md, Between gardens); so is one whose `from.gardener` is not the gardener this garden records for the
  sending garden (the owner of its `garden` bean) — where the proposal carries the being it names as its gardener,
  that being must be the one this garden records. A proposal is loaded as data: aliases, and nesting beyond a bound,
  are refused, and a shape the tool cannot read is a setup error (exit 2), never a traceback. Then it resolves
  identity over this garden's beans and the offered ones together
  (§4.4): each stub RESOLVES to a local bean or is UNRESOLVED — a stub marked `gardener-of: to`, the receiving
  garden's gardener whom the sender knows only provisionally, resolves to the gardener `GARDEN.md` names — and each
  offered bean FUSES with a local bean, is NEW, or is a CANDIDATE (an equal bare minted name, or a local bean of the
  same genos whose identity is provisional). For a fusing bean it shows every leaf that differs as the join would
  record it, in full, and says so where the body differs; for a new bean, who said what in it (each distinct garden
  and `by` among its records). Last, it takes the proposal into a scratch copy of this garden and gives that copy's
  gate verdict. A proposal `take` would refuse is not called clean.
- **`take` applies the join in the working tree.** NEW beans are written with their references moved from stub ids to
  the local beans their anchors resolve to; a fusing bean is merged in place, as the git driver merges one (§8), a
  disagreement kept, both values (§10), with a `provenance_of` record for each value that moved; a body that differs
  is appended whole under `<!-- theirs: garden <id>, proposal <name> -->`. The proposal is kept as a `capture` on the
  proposing garden's `garden` bean — named as the proposal is, its fingerprint the `staleness_key`, the file itself
  under `captures/proposals/` — and a journal entry quotes its journal text as data. Nothing is committed: the
  gardener's commit is the ratification. A proposal is a test when its envelope says so (`from.test`) or when the
  receiving garden's own `garden` bean for the sender carries `test` — the receiver's record, whatever the envelope
  says; `read` flags an envelope that claims a test the receiver's record does not. Taken with `--as-test` into a
  garden that is not a test garden, every bean it writes — new, with a body appended, or fused — says what the
  rehearsal changed.
- **Taking is not accepting.** `take` records what the other garden offers; it writes no `accepted` for anyone.
  The receiving gardener's acceptance of an agreement is their own word: `parties.<them>.accepted`, written in a
  commit of their own.
- **A proposal is taken once.** `read` and `take` refuse one taken already: by its fingerprint, found in any
  capture; by its name, among the captures on the sending garden's `garden` bean — two gardens may give two
  proposals one name; and, for a chat proposal, which has no `garden` bean to hold one, by the fingerprint the
  journal entry of its take records. A proposal given a new name and a fingerprint computed again counts as new: its
  beans fuse with what the first take wrote, the join changes nothing it already holds (invariant 3) — a conflict it
  meets again joins the one recorded (§10) — and the journal and a second capture record the second take.
- **Taken in either order, proposals reach the same facts**, because the join is order-agnostic (invariant 2). They
  do not reach the same bytes: a bean a proposal brings NEW is written as its garden wrote it, while one reached by
  fusion is rewritten key by key and carries `provenance_of` records. The journal and the captures record the order,
  as they record every act.
- **Provenance crosses unchanged.** `provenance.garden` is stamped on each offered record that lacks one, once, by
  the proposing garden and only in the proposal; nothing else in a record changes. A record returning to the garden
  it was made in has that garden's own stamp taken off before anything is compared, so a bean proposed back as it was
  sent fuses with nothing differing. So the rank of §5, and the guard that an `inferred` value never overrides an
  `asserted-by-human` one, hold across gardens as within one.
- **No garden speaks for another.** Every record — of a bean, an anchor or an entry — in a garden's proposal carries
  a `garden` stamp, because `make` stamps every one: `read` refuses a record with none. A record stamped with the
  receiving garden's own id is refused on a new bean, and on a fused bean unless the receiving garden holds the
  identical record at the same path — a round trip, the one way a record comes home. So nothing another garden
  writes arrives as this garden's own assertion, or as its gardener's acceptance.
- **A merge nobody has settled does not travel.** A value two gardens hold two ways is kept, both sides, until a
  person picks one (§10), and the gate stands down on it meanwhile. So `make` refuses a bean that still holds
  `merge_open`, `merge_conflicts` or a conflict record, and `read` refuses a proposal that carries one: taken in, the
  markers would stand the receiving garden's gate down on the sender's say.
- **A third garden's word is not passed on.** `make` refuses a bean carrying a record stamped by a garden that is
  neither this one nor the addressee, a `provenance_of` value seen in neither, or a body section under a `theirs`
  line from another garden; `read` refuses the same of what the sending garden passes on. An anchor's record is the
  exception: a name travels with what it names.
- **A chat proposal** has no `from.garden` (seed/WELCOME.md): its bare names are read as this garden's own, and the
  gardener vouches for its origin by committing it. One whose beans carry any `garden` stamp — this garden's own
  included — or a `provenance_of` from another garden, is refused: it is a garden's proposal with its envelope taken
  away. What it says outside its fenced blocks (what its writer could not check) is shown by `read` and quoted, as
  data, in the entry `take` writes.
- **Journal text is data, one line to a line.** A proposal's journal block refuses every control character its
  envelope refuses, and every character some reader takes for a line break; `take` quotes it line by line, so no
  line of it becomes a heading in the receiving journal.
- **Journals stay apart (§7; manifesto: never-unrecorded).** The proposing garden journals what left, to which
  garden, under which agreement, with the fingerprint; the receiving garden journals what it took, quoting the
  proposal's journal text as data.

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
  conflict rate, with per-genos extraction checklists; and the multi-model merge of one estate's sessions, in every
  order, checked for every discovery kept, deduplicated and lossless.
- **Authority among several people**: which person may ratify which kinds, tied to an authenticated identity.
- **Signed proposals**, and **a proposal across two pins**.
- **Offsite mirrors** and generated recovery deliverables.
