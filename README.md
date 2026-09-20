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
cd daftar && git checkout "$(git tag -l 'v*' --sort=-v:refname | head -1)"   # pin a release
sh seed/germinate.sh ~/my-garden
```

Checking out a tag is the whole of "pin a release, and upgrade deliberately": your garden records which
release it runs, and `bin/dmupgrade.py` moves it when you decide to. Grow from an untagged clone and
`germinate.sh` will say so — it works, it is just not pinned to anything anyone else can fetch.

That gives you an empty garden with its first commit, the gate installed as a pre-commit hook, and zero
errors and zero warnings. Then:

1. write your first beans — `seed/README.md` has a person, a host **and the journal entry that commits
   them**, and `seed/COOKBOOK.md` a domain, a service running on a machine, a rented server and how to
   add a value the vocabulary lacks. All of them pass the gate exactly as written, because a test grows a
   garden and commits them;
2. append that entry to `log/journal.md` — the gate refuses a bean change that is not journalled, and a
   heading is a position in time, so read it from the clock (`date '+%Y-%m-%d %H:%M%:z'`);
3. `git add -A && git commit`.

When the gate refuses something, its message names the rule and, for the common mistakes, the line to write. `MODEL.md` explains the model,
`CHECKLIST.md` how a write is made, and `python3 bin/dmrules.py` prints every rule in force.

## If you work with a coding agent

This is what the ledger is *for*. A garden comes with `.claude/skills/daftar/` — open it in a tool that
reads skills and the agent loads **this garden's** law: the vocabulary in force, what it may decide alone
and what it must bring to you (`MODEL.md`, the Contract of Parts), and how to make a write that the gate
will accept (`CHECKLIST.md`).

The point is not that an agent can edit the files. It is that the two of you write in one language that
neither can quietly corrupt: every fact carries who said it and how they know, every change is journalled
in the same commit, and the rules are data the gate enforces rather than habits either of you remembers.
An agent that invents a field is refused. So are you.

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
refuses a tag older than the one the garden records (pass `--allow-downgrade` to mean it), puts every
file back if the garden would fail its gate under the release, and it always applies a release with that release's
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
| `bin/dm*.py` | the other tools — merge, upgrade, rules (`dmrules`), reasons (`dmwhy`), safe edits, cursors, sessions, staleness, calendars, coordinates, units. Each says what it does in its first lines |
| `MODEL.md`, `CHECKLIST.md`, `MERGE.md` | the model, the write procedure, the merge algebra |
| `seed/RATIONALE.md` | why each rule is as it is, keyed by the rule's own path; `python3 bin/dmwhy.py <name>` reads law and reason together |
| `HISTORY.md` | the design steps and incidents behind the first releases |
| `.claude/skills/daftar/` | a skill that points a coding agent at the garden's own rules |
| `test/` | the release suites, all run in CI (`CONTRIBUTING.md` has the command); `fast.py` runs in every garden's hook |

## License

[Apache-2.0](LICENSE).
