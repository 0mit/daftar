# Merging: a bean's statements are a set

Extends `MODEL.md`. It states how two branches of one garden — working copies, sessions, agents of different makes —
merge a bean: its statements as a set, both sides kept and a disagreement side by side; its header and `details` three
ways against their common base; and a true conflict refused, for a person to settle. Gardens of different people never
merge: they meet by proposal (`MODEL.md`, Between gardens).

## 1. Terms
- **Base, ours, theirs** — the bean as the two branches' common ancestor had it, and as each branch has it now. Git
  hands all three to the merge driver.
- **A statement's form** — its verb and every role, qualifier and key, each value read as a string, every map's keys
  sorted, every list in its order. Two statements are one when their forms are one; written two ways, they are two.
- **A true conflict** — a place both sides changed differently, where both cannot stand: one header key, one leaf of
  `details`, one `id`, one line of the body.

## 2. Invariants
1. **Lossless** — the merge drops no statement either side holds, and no act that knew one. A statement leaves only by
   a change one side made, recorded and journalled there.
2. **Order-agnostic** — merging theirs into ours and ours into theirs gives one bean, byte for byte.
3. **Idempotent** — a bean merged with itself is itself.
4. **Deterministic** — the same three inputs give the same bytes, whoever runs the merge. No clock value enters: the
   merge writes no moment of its own.
5. **Governed conflicts** — a true conflict is refused, never guessed: the bean is left as ours, the conflict is
   named, and a person settles it (class J).

## 3. The statements
- **A set, merged three ways.** A statement in base that either side removed is removed: changing a statement is
  removing it and adding another, and the change one side made stands. A statement either side added is kept. One both
  sides added is kept once.
- **A disagreement stands side by side.** Two statements both sides added about one thing — two amounts, two days —
  are both kept, each with the act that knows it. No marker is written: a person settles a disagreement with a `rule`
  statement (`MODEL.md`, Knowing).
- **An `id` names one statement.** Where the merged set would hold two different statements under one id — both sides
  changed one statement differently, or added two under one name — the merge is refused: a statement another takes by
  its id cannot be two.
- **Knowing is kept.** Each statement keeps the act that knew it. A knowing act a side added with no `of` covered what
  that side added, and the merged bean would let it cover the other side's too: the merge writes its `of`, the ids of
  the statements it covered on its own side. A statement it covered that has no id cannot be named, and the merge is
  refused: give it an id on its branch, and merge again.
- **The order.** The merged statements are base's in base's order, then those either side added, by their form.

## 4. The header, `details` and the body
- **The header** (`bean`, `kind`, `title`, `summary`) merges key by key, three ways: a key one side changed since base
  is that side's; both changed it alike, it is that; both changed it differently, a true conflict. `tags` merge as a
  set, as statements do.
- **`details`** merges leaf by leaf in the same way: a list is one leaf, and a key one side removed stays removed.
- **The body** merges as text, line by line, three ways; lines both sides changed differently are a true conflict.
- **A bean both sides added** has an empty base: its statements are the union of both, and a header key or a body the
  two wrote differently is a true conflict.
- **A bean one side removed** and the other changed is a true conflict.

## 5. Where it runs
- `.gitattributes` sends `beans/*.md` and `mappings/*.md` to the `daftar` merge driver, so `git merge` merges a bean by
  its statements and never by its lines. The driver is `bin/merge.py`, which `bin/install.py` configures, and the merge
  is `core/merge.py`. It refuses, leaving the file as ours, where the result would lose a statement, an act or the
  body, and where a side is not written in statements. git hands the driver three blobs and not three commits, so a
  side's words are read from the bean: one in today's words (a branch from before the garden adopted the core) is
  merged once it is written in statements (`bin/reform.py`).
- `log/journal.md` and `log/pending.md` merge by git's own union (`merge=union`): both sides' entries are kept, none
  rewritten.
- **The gate covers what a merge makes**: the merged bean passes `core/check.py` like any other commit, and the merge
  is committed with the journal entry that names what it merged: `git merge --no-commit`, then `bin/save.py`. A
  merge git commits itself runs the gate too (the `pre-merge-commit` hook): where it merged a bean both sides changed,
  it is refused until an entry of its own names that bean.
  What the other side committed comes as it was committed, judged then: its entries, a bean only it changed, the
  statements it added and the acts that know them. A statement neither side holds is known by an act of the merge's
  own entry; an act the merge gave its `of` is known as it was.
- **Journals never merge across gardens.** What one garden took in from another is written in the receiving garden's
  journal, by the entry that takes it in.

## 6. Conflicts: decided by a person
- A refused merge names each true conflict: the bean, the place, and both sides' values. Git leaves the bean
  conflicted, and nothing is committed until it is settled.
- **A person decides** (class J): they write the bean as it should stand, and the commit that settles it says so in its
  journal entry. Where both values should stand, they are written as two statements, each with its own id, and a
  `rule` says which holds.
- **An agent that may not decide parks it**: the question goes to `log/pending.md` as `status: proposed`, with the
  neighbourhood a person needs to see, and the agent does everything safe around it.
