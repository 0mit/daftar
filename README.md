# daftar

A git-backed ledger that people and AI agents can both read and write. Every managed thing — a host, a
domain, a codebase, a person, a contract — is a **bean**: a Markdown file whose YAML front matter holds
the facts, each fact knowing who said it and how they know. The rules for what a bean may say live in a
versioned **vocabulary**, not in code, and a pre-commit **gate** refuses any commit that breaks them.

A collection of beans is a **garden**. Gardens are private; the language they speak is this repository.
Two gardens grown from it can merge — objects are matched by identity anchors, not by file names, and
disagreements are kept and surfaced rather than silently resolved.

**Status: early.** The model is stable enough to use and the vocabulary is still moving: it has had
several major versions in its first months. Pin a release, and upgrade deliberately.

## Grow a garden

Requires Python 3 and PyYAML (`pip install PyYAML`).

```sh
git clone https://github.com/0mit/daftar.git
sh daftar/seed/germinate.sh ~/my-garden
```

That gives you an empty garden with its first commit, the gate installed as a pre-commit hook, and zero
errors and zero warnings. Then:

1. write your first beans — `seed/README.md` has a person and a host, and `seed/COOKBOOK.md` a domain, a
   service running on a machine, a rented server and how to add a value the vocabulary lacks. All of them
   pass the gate exactly as written, because a test commits them;
2. append an entry to `log/journal.md` — the gate refuses a bean change that is not journalled;
3. `git add -A && git commit`.

When the gate refuses something, its message names the rule and, for the common mistakes, the line to write. `MODEL.md` explains the model,
`CHECKLIST.md` how a write is made, and `python3 bin/dmrules.py` prints every rule in force.

## Words you will meet

| word | meaning |
|---|---|
| **bean** | one managed thing, as one Markdown file in `beans/` — facts in the front matter, prose below |
| **garden** | a git repository of beans: one estate's ledger. Private to whoever keeps it |
| **seed** | `seed/`: the kit a new garden is grown from — the vocabulary, the templates, `germinate.sh` |
| **vocabulary** | the rules, as data: `seed/std-vocab.md` for every garden, plus a garden's own `VOCAB.md` |
| **gate** | `bin/dmcheck.py`, run as a pre-commit hook: a commit that breaks a rule is refused |
| **journal** | `log/journal.md`: every change, who made it and why. The gate refuses an unrecorded change |
| **anchor** | a fact that identifies an object (a serial, a domain name), so two gardens recognise the same thing |
| **nature / kind** | what sort of being it is: `physical`, `metaphysical` or `living`, refined by a kind such as `host` |
| **facet** | an aspect of ownership, e.g. `legal` or `technical`; each has exactly one owner and one holder |
| **crown** | where every ownership chain ends; in practice a person writes `owned_by: { legal: { crown: love } }` |
| **profile** | an opt-in group of rules, e.g. `domain`, for gardens that hold that kind of thing |
| **vacancy** | a value the vocabulary offers that nothing uses yet, stated with a reason |
| **Contract of Parts** | `MODEL.md`: which decisions an agent may take alone and which a person must ratify |

## Adopt a new release

Releases are tags on this repository. From inside a garden:

```sh
python3 bin/dmupgrade.py <tag>        # e.g. the newest tag listed on the repository's Releases/Tags page
```

It updates exactly the files `seed/LANGUAGE` declares, moves the vocabulary pins, records the release in
`GARDEN.md` (`daftar_release:`), writes the journal entry and runs the gate — and does **not** commit. It
refuses a tag older than the one the garden records, and it always applies a release with that release's
own copy of the tool. (A garden grown before v0.4.0 has a tool that cannot hand over: upgrade once,
commit, and run the same command again to record the release.) Read `git diff`, fill in the two marked fields of the
journal entry, and commit when you have decided to adopt it.

## Propose a change to the law

Found a case the vocabulary cannot express, or a rule that is wrong? Open a pull request. Merging one is
the ratification, so a proposal carries its evidence: see [CONTRIBUTING.md](CONTRIBUTING.md).

## What is here

| path | what it is |
|---|---|
| `seed/std-vocab.md` | the vocabulary — the law every garden pins |
| `seed/germinate.sh`, `seed/LANGUAGE` | how a garden is grown, and what it receives |
| `bin/dmcheck.py` | the gate |
| `bin/dm*.py` | the other tools: merge, upgrade, rules, safe edits, cursors, sessions |
| `MODEL.md`, `CHECKLIST.md`, `MERGE.md` | the model, the write procedure, the merge algebra |
| `.claude/skills/daftar/` | a skill that points a coding agent at the garden's own rules |
| `test/` | `germinate.py`, `converge.py` and `upgrade.py` run in CI; `fast.py` runs in every garden's hook |

## License

[Apache-2.0](LICENSE).
