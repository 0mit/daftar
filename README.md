# daftar

*Daftar* (دفتر) is the Persian word for a notebook. This one is kept by you and your AI agents, about the
things you work on together, and you can read it without them.

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

The notebook is yours: you are its **gardener**, and the first thing in it is you. You tell your agent, in a
chat: *"the NAS in the hallway is at 192.168.1.20, I set it up last April, the serial on the sticker is
4XK9-2217."* The agent writes one file and commits it. The file holds the facts, and each fact holds its source
(abridged — the full file also carries a title, a summary, and who owns and answers for the machine: you):

```yaml
bean: hallway-nas
genos: host
nature: soma
identity:
  status: confirmed
  anchors:
    - { key: serial, value: "4XK9-2217",    class: hardware, establishing: true }
    - { key: ip,     value: "192.168.1.20", class: network,  establishing: false }
provenance: { src: asserted-by-human, by: "you", as_of: now }
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
is first a **nature**, one of two, named in Greek — `soma`, a body, which takes room in space; `lekton`, what exists
by being said and agreed, placed in an order — and then a **genos**, its kind, that refines it: a host and a person
are soma, each standing at its level among bodies (a device, an organism); a domain, a product, a codebase, a design,
an agreement between people, a document, a dinner where something was agreed, a running instance of a program are
lekton. Life is no nature: a thing lives while its genos says it does — a machine while it is powered, an agreement
while it holds, a person while they live — and a life comes from a life, a chain the ledger walks. Money is measured, like a length:
an amount in the currency it was paid in, exact and never rounded, and what one person owes another is read from
what was paid and what was agreed — never written down beside them, where it could drift. The rules for what a
thing may say attach to its nature and every genos beneath inherits them, so a new genos arrives with a coherent
identity policy for free. The same is true of ownership: every thing has exactly one owner, and exactly one entry
saying who answers for it, per facet — legal, technical, financial — and every chain ends at a person, at someone
outside the notebook, or at the crown. An agreement between two people may be owned by neither of them, and then
both answer for it.

The vocabulary that says all this is a document, versioned, read by the gate on every commit; the gate itself
names no term. A garden adds what it needs — its own terms, its own values, its own profiles — and a local
term that proves general is promoted to the standard by a pull request, which a person ratifies. A mechanism
can be declared whole, ahead of its first occupant, with its empty positions marked as such: the language is
designed larger than any one garden's use of it, so that the next kind of thing, from a garden nobody here has
seen, already has somewhere to stand.

## What a garden can say

The same small set of machines carries every kind of fact. Each is a line of the law, read by the gate and by every
tool, so a garden that needs one uses it whole, and a garden that needs none never meets it:

- **Time, in any calendar.** A day or a moment is a *position*: in the Gregorian, the Persian, the Hebrew calendar or
  a dozen more, at the precision it was said — a day, a minute — and, where nobody said the day, placed by what it
  followed. Deep time too: a year, a mega-annus, the geological chart's own stages.
- **Place, and what a thing takes there.** From the most general placement to the most bodily — a code in its order, a
  record in a register, a process in its machine, a meeting in the hours of those present, a machine in its rack — each
  says what it takes from where it is placed: nothing, a share, or room. A host says what it can hold; a share past it
  is warned, and room past it — two things in one place at once — refused.
- **Codes, with their scheme.** An occupation, a field of knowledge, a technology, an account in a garden's own chart:
  one form, `isco-08:2522`, `analytic:rent`, checked against the scheme it names.
- **Series and readings.** What a gauge held at each position of a line, and its whole checked exactly; a reading, who
  made it, when, and what it was of.
- **Money and agreements.** Parties, the clauses that bind them, the payments between them; what is owed read from what
  was paid and what was agreed, never written beside them; where each amount belongs, along a garden's own plans.
- **Readings, never stored.** `bin/dmreckon.py` computes what follows from what is recorded — a total, a share, an
  ancestor's roll-up, a published mechanism — each time it is asked, so a result can never drift from its inputs.
- **Pages.** The `view` profile draws a garden as pages — its parts and how they relate, live values beside them — from
  one drawing module the garden keeps, checked against the law like everything else.

`python3 bin/daftar.py catalog` shows the whole language and how its parts relate; `--part <item>` shows one.

## Between gardens

A notebook is kept by its gardener — a person, or an organisation — and nothing outside it writes there. But people
deal with one another — they share a cost, lend and repay, agree on something and keep to it — and the other person
may keep a notebook of their own. Two gardens meet the way two networks do: each its own domain, and the two
**peers**, each configured at its own end, and neither reaching inside the other. Ownership rises through each garden
to its gardener, and the crown is where it ends; between gardens, what they share is the language they pin. Two
gardens that pin different versions of the language cannot exchange until one of them moves.

What passes is only ever a **proposal**. Your agent writes one file — the beans you choose to give, under an
agreement you and the other gardener have made — and lays it beside your notebook, never inside theirs. Their
agent reads it in their notebook and shows them what it would change; it is taken in only when they commit it:
their gate, their journal, their hand. Every fact keeps who said it as it crosses, so what you asserted arrives as your
assertion and nothing on the other side quietly overrules it. Taking an agreement in records what you offered; their
yes to it is theirs, written in their own notebook, in their own words. A thing you both hold — the agreement, the
people in it — is named once, by the notebook that recorded it first, and the name travels with it, so the two
notebooks see one thing where they would otherwise see two; a name someone else gave — a package's, a registry
number — is the same in every notebook already. An agreement between two people may be owned by neither of them, and
then both answer for it: nobody owns the crown, and no garden owns the way between them.

A garden is known by the commit it grew from, so two gardens need no registry and no account anywhere to name each
other. Growing a garden writes a random seed into that first commit, so two notebooks on one machine are never taken
for one, even when they carry the same name and were grown in the same second. The first time two gardens meet, each
gardener records the other's garden and whoever keeps it, in one commit of their own. A rehearsal is a garden
grown for it, never a copy of a real one, and each gardener marks it as a rehearsal in their own records.

## Who does what

| | you, the gardener | your agent | the gate |
|---|---|---|---|
| **write** | say what is true, in a chat | writes the fact and the journal entry, commits | refuses a commit that breaks a rule or is not journalled |
| **decide** | ratify identity, safety flags, any change to the rules, and what another garden proposes | records what it observed or inferred; proposes the rest | — |
| **read** | ask; or open the files yourself, any time | reads the one file that owns the fact, and its source | — |

The line between "records" and "proposes" is the **Contract of Parts** in `MODEL.md`: an agent alone may
record an observation or an inference; a person ratifies identity, safety and law. What an agent may not
decide, it parks in a queue and carries on.

daftar's words stand in layers (manifesto: layers), each read at a different time; what each holds, and which files
are law, is `MODEL.md`'s:

1. **The manifesto** — `MANIFESTO.md`. Read when someone asks what daftar is for.
2. **Laws** — the vocabulary and the model. Read by the gate on every commit, and by an agent when it arrives.
3. **Reasoning** — why each rule is as it is. Read when a rule surprises someone.
4. **Journals** — what was done and why. Read by the next agent to pick up where the last one stopped, and by
   a person on the day something is wrong.
5. **History** — git. Read by nobody, until it is the only thing left.

## Start

You need a coding agent with a shell and git — as of September 2026, in the alphabet's order: Aider, Claude Code,
Codex CLI, Cursor, Gemini CLI, GitHub Copilot's agent, and the like, on Linux, macOS or Windows — and a place for a
private git repository. The notebook is yours (manifesto: never-sells).

Tell the agent:

> Read https://raw.githubusercontent.com/0mit/daftar/master/INSTALL.md and follow it, with the newest release tag. My
> notebook goes at `~/garden-sam`; my private remote is `git@github.com:me/garden.git`.

([`INSTALL.md`](INSTALL.md) is that page.)

The agent grows the notebook with you as its gardener: your own person bean is the first thing in it, and
`GARDEN.md` names you, so every agent that comes after knows whose notebook it is working in — the gate's last
line says it.

The next time you sit down, tell it to read `AGENTS.md` in the notebook.
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
| **gardener** | the person — or organisation — who keeps a garden, named in its `GARDEN.md`: the first bean of a garden grown with `--gardener`. Agents tend a garden; its gardener keeps it and ratifies what an agent may not decide |
| **seed** | `seed/`: the kit a new garden is grown from — the vocabulary, the templates, `germinate.py` |
| **vocabulary** | the rules, as data: `seed/std-vocab.md` for every garden, plus a garden's own `VOCAB.md` |
| **gate** | `bin/dmcheck.py`, run as a pre-commit hook: a commit that breaks a rule is refused |
| **journal** | `log/journal.md`: every change, who made it and why. The gate refuses an unrecorded change |
| **anchor** | a fact that identifies an object (a serial, a domain name), so two gardens recognise the same thing |
| **nature / genos** | what sort of being it is: `soma`, a body, taking room in space, or `lekton`, what exists by being said and agreed — refined by a genos, its kind, such as `host`, which for a body names its level among bodies. The words are Greek, and `MODEL.md` gives each |
| **facet** | an aspect of ownership, e.g. `legal` or `technical`; each has exactly one owner, and one entry saying who answers for it |
| **crown** | where every ownership chain ends: in the life chain — who gave a thing its life, walked to `agape`, love that does not possess, and to `theos`, which no bean names. A person is owned by no one: `owned_by: { legal: { crown: agape } }` |
| **profile** | an opt-in group of rules in a field's own words, e.g. `domain` or `accounting`; it adds terms, and adds to the core's terms without rewriting them, so a garden may take every profile at once |
| **position** | where something is on a line — a day in a calendar, a moment, a path on a machine, the second of a series — in the one form its system declares |
| **coding** | a code written with the scheme it is a code of, `<scheme>:<code>`: an occupation, a technology, an account |
| **placement** | how one thing is in, at or among another, from the most general to the most bodily; each says what it takes from its host — nothing, a share, or room |
| **vacancy** | a value the vocabulary offers that nothing uses yet, stated with a reason |
| **Contract of Parts** | `MODEL.md`: which decisions an agent may take alone and which a person must ratify |
| **proposal** | what one garden offers another: one file of beans, laid outside both gardens, which the other garden's gardener takes in by committing it — or does not. Taking it in accepts nothing on the gardener's behalf. `bin/dmpropose.py` |
| **peering** | how gardens meet: as peers, each configured at its own end, through the agreements between their gardeners and the proposals made under them, in the language they share. Owned by no garden |

## Adopt a new release

Releases are tags on this repository. From inside a garden:

```sh
python3 bin/dmupgrade.py <tag>        # the newest tag listed on the repository's Releases/Tags page
```

It updates exactly the files `seed/LANGUAGE` declares, moves the vocabulary pins, records the release in
`GARDEN.md`, translates what the law re-spelled, writes the journal entry and runs the gate — and does **not**
commit. It refuses a tag older than the one the garden records (pass `--allow-downgrade` to mean it), and puts every
file back if the garden would fail its gate under the release. Read `git diff`, fill in the two marked fields of the
journal entry, and commit when you have decided to adopt it.

A release that re-spells what a garden holds translates it where it is written, every comment going with the fact
it sat on, and proves each file: the new front matter must hold exactly what the release says it should. What only a
person can decide — a tree of another code with no bean of its own, a value that is no single position — stops the
upgrade, named, before anything is touched. `seed/CHANGELOG.md` says what each version of the law brought;
`INSTALL.md` has the crossings of older gardens.

## Propose a change to the law

Found a case the vocabulary cannot express, or a rule that is wrong? Open a pull request. Merging one is
the ratification, so a proposal carries its evidence: see [CONTRIBUTING.md](CONTRIBUTING.md).

## What is here

| path | what it is |
|---|---|
| `INSTALL.md` | how a garden is grown, written for the agent that will grow it |
| `seed/std-vocab.md` | the vocabulary — the law every garden pins |
| `seed/germinate.py`, `seed/LANGUAGE` | how a garden is grown (Python, so on Windows too; `germinate.sh` hands over to it), and what it receives |
| `bin/dmcheck.py` | the gate |
| `bin/daftar.py` | the one entry: `daftar catalog` (the language and its relations), `daftar why`, `daftar rules`, `daftar form` |
| `bin/dm*.py` | the other tools — merge, proposals between gardens (`dmpropose`), what is owed (`dmledger`), readings computed from what is recorded (`dmreckon`), upgrade, rules (`dmrules`), reasons (`dmwhy`), safe edits, the journal entry (`dmjournal`), a change saved in one command (`dmsave`), cursors, sessions, staleness, calendars, coordinates, units. Each says what it does in its first lines |
| `assets/<profile>/` | what a profile brings besides its rules — the `view` profile's page drawer and server, `assets/view/README.md` |
| `MODEL.md`, `CHECKLIST.md`, `MERGE.md` | the model, the write procedure, the merge algebra |
| `seed/RATIONALE.md` | why each rule is as it is, keyed by the rule's own path; `python3 bin/dmwhy.py <name>` reads law and reason together |
| `AGENTS.md`, `.claude/skills/daftar/` | one text, twice: the door for an agent with a shell — a reading order, no rules. The second is one tool's adapter, which loads the door by itself; another tool's adapter would stand beside it |
| `seed/WELCOME.md` | the door for an assistant with no shell, written to be pasted into a chat |
| `seed/README.md`, `seed/COOKBOOK.md` | worked beans that pass the gate as written: the gardener, a host, a domain and the agreement it is held under, a service, a rented server, a cost shared between two people, an agreement paid in instalments, a statement, an event, another person's garden, a series, a course on its walk, a workshop's staff and bookings, a co-op's own codes, analytic accounts, a rack and what it holds |
| `seed/FORMS.md` | what an agent reads before writing: six of the cookbook's recipes, byte for byte, and what to write when nobody said |
| `test/` | the release suites, all run in CI (`CONTRIBUTING.md` has the command); `fast.py` runs in every garden's hook |

## A seed, on a notebook

افتاد، بر روی دفتری که بر روی میزی که بر روی زمین قرار گرفته بود، دانه‌ی کاجی که مختصات آغازیدن وجود خود را از حتی
پایین‌تر از سطح پست زمین گرفته و به بالاتر از اکثر چیزها رسیده بود. به جز خیال خام و خوشِ بستری برای جوانه زدن، در این
زمانه‌ی پیر، چه چیز ممکن بود دانه‌ی رسیده را قانع کند که از آن بلندا به فرش فرود آید؟ خیال پریدن و سودای شکفتن داشت، در
دلش شوق جوانه زدن مدت‌ها بود از ترس فنا شدن فزونی گرفته بود، اما چگونه ممکن بود بدون فرود آمدن بتواند سعود کند؟ آیا
ایمانی از جنس الماس در دلش خیال شکفتن را آسوده می‌کرد؟ آیا ترس از فنا شدن، نرسیدن و یا به جای اشتباهی رسیدن داشت؟ آیا
درخت کهنه‌سال، بی که دانه بداند، بخواهد، از میوه جدایش کرده بود؟ چه کسی می‌داند؟ به هر ترتیب دانه افتاده بود و دیگر
خبری از عرش والا نبود، اگرش بستری حاصل‌خیز فراهم می‌بود حتما که می‌شکفت و شاید اگر اقبال ناظرش می‌بود روزی درختی پیر
می‌شد و میوه‌های دانه‌دار می‌داد، ولی اکنون در حاشیه‌ی دفتری نیم سیاه و نیم سپید در انتظار نوازش دستی بالجبار آرمیده است.

It fell — onto a notebook that lay on a table that stood on the ground — a pine seed that had taken the
coordinates of the beginning of its existence from lower even than the lowly face of the earth, and had risen
higher than most things. In this old age of the world, what but the raw, sweet fancy of a bed to sprout in could
have persuaded a ripe seed to come down from that height to the floor? It had a fancy of flying and a longing to
bloom; in its heart the eagerness to sprout had long outgrown the fear of perishing — yet how could it rise
without coming down? Did a faith of diamond in its heart set its dream of blooming at rest? Did it fear
perishing, not arriving, or arriving in the wrong place? Had the old tree, without the seed's knowing or
wanting, parted it from the fruit? Who knows? However it was, the seed had fallen, and of the high throne there
was no more word. Had a fertile bed been ready for it, it would surely have bloomed — and perhaps, had fortune
watched over it, it would one day have grown into an old tree and borne seeded fruit. But now, in the margin of
a notebook half black and half white, it rests, as it must, awaiting the caress of a hand.

*The Persian was written by Omid in a notebook, under a tree, some years before any of this; the seed, the
garden and the bean were named later, and the notebook had the words first. The English was first rendered by
the agent that worked beside him on 2026-09-22 (Claude, Fable 5.1) and revised at his word on 2026-09-24
(Claude, Opus 5.5), closer to the Persian: its existence, the lowly earth, the throne and the floor, the caress.
It stands as an agreement between them: he takes another person's change to his text where it is more
beautiful; the agent's text is its own.*

## License

The code: [AGPL-3.0-or-later](LICENSES/AGPL-3.0-or-later.txt), with the
[garden exception](LICENSES/LicenseRef-daftar-garden-exception.txt). The law, the guides and the site:
[CC BY 4.0](LICENSES/CC-BY-4.0.txt). The seeds of a garden's own files: [CC0 1.0](LICENSES/CC0-1.0.txt). Every path:
[LICENSE](LICENSE) and `REUSE.toml`. What daftar holds to is [MANIFESTO.md](MANIFESTO.md); who answers for it is
[CHARTER.md](CHARTER.md).
