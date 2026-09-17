---
name: daftar
description: >
  Read and write the git-backed ledger that is the shared language between human and AI — "beans"
  (managed objects: hosts, routers, VPSes, domains, products, deployments, people, …), their typed
  identity anchors, provenance-stamped facts, and their edges. Use whenever a fact about the estate is
  discovered, changed, merged, or needed. The garden is the repository this session is working in.
---

# daftar

The garden is **the repository you are in**. Everything below is found there; nothing is carried by this
file, because a skill that carries rules becomes a second copy of them that can disagree with the first —
which is what this file used to be, and it went sixty-three commits stale saying so, pointing every agent
that read it at a directory that does not exist.

**Read these, in this order, before writing anything:**

1. `beans/daftar.md`, **if this garden has one** — its `standing:` list says which documents are **law**,
   which are **history**, and which are a **guide**. A garden grown from `seed/` has none: there
   `seed/std-vocab.md` and `VOCAB.md` are the law, and `seed/README.md` shows a first person and host.
2. `MODEL.md` — the data model and the **Contract of Parts**: what you may enact and what a human must
   ratify. Identity anchors (F), safety flags (E), and any change to the vocabulary or the law (G) are
   ratified, never enacted.
3. `CHECKLIST.md` — Part A (what the gate checks), Part B (the judgment only a person can make), Part C
   (how a write is made), Part D (how a read is made), Part E (how to work beside another session).
4. `python3 bin/dmrules.py` — every rule in force, derived from the vocabulary rather than restated.

**Before touching a file:** `python3 bin/dmcursor.py <bean-or-path>`. It resolves a path back to the being
that owns it, says whether a cached analysis is still true — so the answer to "must I read this tree?" is
usually no, with evidence rather than hope — and reports what must be attended to, including constraints
inherited from a habitat two hops up.

**Before editing front matter:** use `bin/dmsafe.py`. Measure first (`count`), then state the number you
expect; there is no default. Six documented incidents in this repo came from text surgery that changed
more locations than intended, and the last was reproduced an hour after the tool was built to prevent it.

**Every write:** edit the one bean that owns the fact, append to `log/journal.md` in the same commit, and
commit. The gate reads the **staged** blobs and refuses a bean whose change is not journalled. A change to
the vocabulary or the law must say RULE-CHANGE distinctly.

**When you meet a case the vocabulary does not cleanly cover:** stop, show the human the relevant term
with its sibling records, and decide together — or, working async, park it in `log/pending.md` as
`status: proposed` with the neighbourhood you would have shown, do everything safe around it, and carry
on. Never silently generalise.

**Growing the standard:** a garden-local term that proves general is promoted into `seed/std-vocab.md`
with a semver bump — additive is minor, a changed rule is major, because a changed rule can retroactively
re-classify beans that already passed. That is a rule-change: propose, show the neighbourhood, the human
ratifies, and the garden adopts it by moving its pin.
