# daftar

*Daftar* (دفتر) is the Persian word for a notebook. This one is kept for you by your AI agent, about the
things you and it work on, and you can read it without the agent.

## Why it exists

You work with AI agents on things that matter: servers, domains, a codebase, contracts, the people who answer
for them. Every session starts empty. Facts get lost, get invented, or get changed by someone who never said
so — and the next agent, perhaps of another make, inherits the mess and asks you again. An agent's built-in
memory helps that agent; it does not say who said what, it is not shared with another agent, and it is not
something you can pick up and read on the day the agent is gone.

daftar is a notebook with three rules:

1. **Every fact says who said it and how they know** — you, or the agent, and whether it was told, measured,
   or guessed.
2. **Every change is written in a journal, in the same commit** — what was done and why.
3. **A gate refuses any change that breaks a rule** — whether a person or an agent made it.

The notebook is plain text in a private git repository. You do not edit it. You talk to your agent; the agent
writes; the gate keeps both of you honest. When the network is down, or the agent is gone, you can still read
it, print it, hand it to a small local model, and carry on.

It is a handover between people, too. The person who set the machine up leaves; the one who inherits it
finds not a folder of notes but every fact with its source, every decision with its reason, and the journal
of what was done and why, in order — the same record a new agent reads. A handover written this way does not
depend on who is available to ask.

**It is not for everyone.** If one careful person keeps a few notes for one agent, this is more than you need.
It is for people who run several agents, of several makes, across many sessions, on one set of real things —
and who need what those agents leave behind to be true, attributed, and mergeable; and for anyone who will one
day hand that set of things to someone else.

**It is young, and it grows by use.** The model has been stable since its first weeks; the vocabulary moves
because gardens bring it cases it had not met — it has had many versions in its first months, and each was a
case someone brought. A garden pins a release, so a move never reaches you until you adopt it. Bring your own
cases: a kind of thing it cannot yet name, a rule that is wrong for you. That is how it is meant to grow.

## One example

You tell your agent, in a chat: *"the NAS in the hallway is at 192.168.1.20, I set it up last April, the serial
on the sticker is 4XK9-2217."* The agent writes one file and commits it. The file holds the facts, and each
fact holds its source (abridged — the full file also carries a title, a summary, and who owns and answers for
the machine):

```yaml
bean: hallway-nas
kind: host
nature: physical
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "4XK9-2217",    class: hardware, establishing: true,  authority: operator-asserted }
    - { key: ip,     value: "192.168.1.20", class: network,  establishing: false }
provenance: { src: asserted-by-human, by: "you", as_of: 2026-09-22 }
```

Six weeks later, in a new session — perhaps with an agent of another make, with none of the first one's
context — you ask *"is the NAS still on .20?"*. The agent does not guess and does not ask you again. It reads
the file: the address was **asserted by you, on 2026-09-22**, and it is a corroborating fact, not the machine's
identity; the serial is. If the agent then pings the machine and finds it on .21, it records that as
**observed, by itself, today** — beside your assertion, not over it. What a person said is never overwritten
by what an agent measured or inferred; only you can change that. And the change is in the journal, in the
same commit, with the reason.

That is the whole idea. Everything else in this repository is what makes it hold under many agents, many
sessions, and time:

- **Provenance is a field, not a sentence.** A memory file says "learned from the user in March" if the writer
  remembered to. A fact here cannot pass the gate without its source.
- **Identity is by anchor, not by file name.** A serial, a MAC address, a domain name, a product id. Two
  notebooks that never met can be merged object by object, and a disagreement is kept, both values, for a
  person to settle.
- **The rules are data.** What a machine may say, what a status may be, which decisions an agent may take
  alone and which a person must ratify — all of it is in a versioned vocabulary, not in code. Changing a rule
  is itself a journalled, ratified change.
- **It reads cold.** Plain YAML and Markdown, small files, absolute dates, explicit units. The tools are
  Python scripts with one dependency, and they work offline. On paper, years later, a fact still says what it
  said and who said it.

## Any thing, and the rules for it, as data

The example is a machine because machines are where this began. The notebook is not about machines. A thing
is first a **nature** — physical, metaphysical or living — and then a **kind** that refines it: a host is
physical; a domain, a product, a codebase, a design, a contract are metaphysical; a person, or a running
instance of a program, is living. The rules for what a thing may say attach to its nature and every kind
beneath inherits them, so a new kind arrives with a coherent identity policy for free. The same is true of
ownership: every thing has exactly one owner and exactly one holder who answers for it, per facet — legal,
technical — and every chain ends at a person, at someone outside the notebook, or at the crown.

The vocabulary that says all this is a document, versioned, read by the gate on every commit; the gate itself
names no term. A garden adds what it needs — its own terms, its own values, its own profiles — and a local
term that proves general is promoted to the standard by a pull request, which a person ratifies. A mechanism
can be declared whole, ahead of its first occupant, with its empty positions marked as such: the language is
designed larger than any one garden's use of it, so that the next kind of thing, from a garden nobody here has
seen, already has somewhere to stand.

## Who does what

| | you | your agent | the gate |
|---|---|---|---|
| **write** | say what is true, in a chat | writes the fact and the journal entry, commits | refuses a commit that breaks a rule or is not journalled |
| **decide** | ratify identity, safety flags, and any change to the rules | records what it observed or inferred; proposes the rest | — |
| **read** | ask; or open the files yourself, any time | reads the one file that owns the fact, and its source | — |

The line between "records" and "proposes" is the **Contract of Parts** in `MODEL.md`: an agent alone may
record an observation or an inference; a person ratifies identity, safety and law. What an agent may not
decide, it parks in a queue and carries on.

Four layers, each standing on the one beneath, and each read at a different time:

1. **Laws** — the vocabulary and the model. Read by the gate on every commit, and by an agent when it arrives.
2. **Reasoning** — why each rule is as it is. Read when a rule surprises someone.
3. **Journals** — what was done and why. Read by the next agent to pick up where the last one stopped, and by
   a person on the day something is wrong.
4. **History** — git. Read by nobody, until it is the only thing left.

## Start

You need a coding agent with a shell and git — as of September 2026: Claude Code, Cursor, Codex CLI, Gemini
CLI, GitHub Copilot's agent, Aider, and the like — and a place for a private git repository. The notebook is
yours; nothing here ever sees it.

Tell the agent:

> Read https://raw.githubusercontent.com/0mit/daftar/master/INSTALL.md and follow it. My notebook goes at
> `~/garden`; my private remote is `git@github.com:me/garden.git`.

([`INSTALL.md`](INSTALL.md) is that page.)

The next time you sit down, tell it to read `AGENTS.md` in the notebook — in Claude Code, *"load daftar"*.
From then on you talk about your things, and the agent keeps the notebook. You will rarely open the folder.

An assistant in a chat window, with no shell, cannot run the gate and so cannot write. Paste it
`seed/WELCOME.md`: what it gives back is a proposal for you, or an agent with a shell, to commit.

`INSTALL.md` also has the by-hand path, for a person without an agent.

## Words you will meet

Inside the notebook the parts have names. You will meet them in the agent's answers and in the files.

| word | meaning |
|---|---|
| **bean** | one managed thing, as one Markdown file in `beans/` — facts in the front matter, prose below |
| **garden** | a git repository of beans: one notebook. Private to whoever keeps it |
| **seed** | `seed/`: the kit a new garden is grown from — the vocabulary, the templates, `germinate.sh` |
| **vocabulary** | the rules, as data: `seed/std-vocab.md` for every garden, plus a garden's own `VOCAB.md` |
| **gate** | `bin/dmcheck.py`, run as a pre-commit hook: a commit that breaks a rule is refused |
| **journal** | `log/journal.md`: every change, who made it and why. The gate refuses an unrecorded change |
| **anchor** | a fact that identifies an object (a serial, a domain name), so two gardens recognise the same thing |
| **nature / kind** | what sort of being it is: `physical`, `metaphysical` or `living`, refined by a kind such as `host` |
| **facet** | an aspect of ownership, e.g. `legal` or `technical`; each has exactly one owner and one holder |
| **crown** | where every ownership chain ends. Its three branches are named for the natures: `nature` for physical things, `logos` for metaphysical, `love` for living — so a person writes `owned_by: { legal: { crown: love } }` |
| **profile** | an opt-in group of rules, e.g. `domain`, for gardens that hold that kind of thing |
| **vacancy** | a value the vocabulary offers that nothing uses yet, stated with a reason |
| **Contract of Parts** | `MODEL.md`: which decisions an agent may take alone and which a person must ratify |

## Adopt a new release

Releases are tags on this repository. From inside a garden:

```sh
python3 bin/dmupgrade.py <tag>        # the newest tag listed on the repository's Releases/Tags page
```

It updates exactly the files `seed/LANGUAGE` declares, moves the vocabulary pins, records the release in
`GARDEN.md`, writes the journal entry and runs the gate — and does **not** commit. It refuses a tag older than
the one the garden records (pass `--allow-downgrade` to mean it), and puts every file back if the garden would
fail its gate under the release. Read `git diff`, fill in the two marked fields of the journal entry, and commit
when you have decided to adopt it.

## Propose a change to the law

Found a case the vocabulary cannot express, or a rule that is wrong? Open a pull request. Merging one is
the ratification, so a proposal carries its evidence: see [CONTRIBUTING.md](CONTRIBUTING.md).

## What is here

| path | what it is |
|---|---|
| `INSTALL.md` | how a garden is grown, written for the agent that will grow it |
| `seed/std-vocab.md` | the vocabulary — the law every garden pins |
| `seed/germinate.sh`, `seed/LANGUAGE` | how a garden is grown, and what it receives |
| `bin/dmcheck.py` | the gate |
| `bin/dm*.py` | the other tools — merge, upgrade, rules (`dmrules`), reasons (`dmwhy`), safe edits, cursors, sessions, staleness, calendars, coordinates, units. Each says what it does in its first lines |
| `MODEL.md`, `CHECKLIST.md`, `MERGE.md` | the model, the write procedure, the merge algebra |
| `seed/RATIONALE.md` | why each rule is as it is, keyed by the rule's own path; `python3 bin/dmwhy.py <name>` reads law and reason together |
| `AGENTS.md`, `.claude/skills/daftar/` | one text, twice: the door for an agent with a shell — a reading order, no rules |
| `seed/WELCOME.md` | the door for an assistant with no shell, written to be pasted into a chat |
| `seed/README.md`, `seed/COOKBOOK.md` | worked beans that pass the gate as written: a person, a host, a domain, a service, a rented server |
| `test/` | the release suites, all run in CI (`CONTRIBUTING.md` has the command); `fast.py` runs in every garden's hook |

## License

[Apache-2.0](LICENSE).
