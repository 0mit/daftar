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
is first a **nature**, one of three, named in Greek — `soma`, a body; `lekton`, what exists by being said and
agreed; `empsychon`, what lives, while it lives — and then a **genos**, its kind, that refines it: a host is soma;
a domain, a product, a codebase, a design, an agreement between people, a document, a dinner where something was
agreed are lekton; a person, or a running instance of a program, is empsychon. Money is measured, like a length:
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

## Between gardens

A notebook is kept by its gardener — a person, or an organisation — and nothing outside it writes there. But people
deal with one another — they share a cost, lend and repay, agree on something and keep to it — and the other person
may keep a notebook of their own. Two gardens meet the way trees in a forest do: not by growing into each other, but
beneath, through the **mycelium** — the network that joins trees rooted apart, carries between them, and is owned by
none of them. Ownership rises through each garden to its gardener, and the crown is where it ends, above; the
mycelium is where gardens meet, beneath, in the earth of the language they share. Two gardens that pin different
versions of the language cannot exchange until one of them moves.

What passes is only ever a **proposal**. Your agent writes one file — the beans you choose to give, under an
agreement you and the other gardener have made — and lays it beside your notebook, never inside theirs. Their
agent reads it in their notebook and shows them what it would change; it is taken in only when they commit it:
their gate, their journal, their hand. Every fact keeps who said it as it crosses, so what you asserted arrives as your
assertion and nothing on the other side quietly overrules it. Taking an agreement in records what you offered; their
yes to it is theirs, written in their own notebook, in their own words. A thing you both hold — the agreement, the
people in it — is named once, by the notebook that recorded it first, and the name travels with it, so the two
notebooks see one thing where they would otherwise see two; a name someone else gave — a package's, a registry
number — is the same in every notebook already. An agreement between two people may be owned by neither of them, and
then both answer for it: nobody owns the crown, and nobody owns the mycelium.

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

Four layers, each standing on the one beneath, and each read at a different time:

1. **Laws** — the vocabulary and the model. Read by the gate on every commit, and by an agent when it arrives.
2. **Reasoning** — why each rule is as it is. Read when a rule surprises someone.
3. **Journals** — what was done and why. Read by the next agent to pick up where the last one stopped, and by
   a person on the day something is wrong.
4. **History** — git. Read by nobody, until it is the only thing left.

## Start

You need a coding agent with a shell and git — as of September 2026: Claude Code, Cursor, Codex CLI, Gemini
CLI, GitHub Copilot's agent, Aider, and the like, on Linux, macOS or Windows — and a place for a private git
repository. The notebook is
yours; nothing here ever sees it.

Tell the agent:

> Read https://raw.githubusercontent.com/0mit/daftar/master/INSTALL.md and follow it. My notebook goes at
> `~/garden-sam`; my private remote is `git@github.com:me/garden.git`.

([`INSTALL.md`](INSTALL.md) is that page.)

The agent grows the notebook with you as its gardener: your own person bean is the first thing in it, and
`GARDEN.md` names you, so every agent that comes after knows whose notebook it is working in — the gate's last
line says it.

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
| **gardener** | the person — or organisation — who keeps a garden, named in its `GARDEN.md`: the first bean of a garden grown with `--gardener`. Agents tend a garden; its gardener keeps it and ratifies what an agent may not decide |
| **seed** | `seed/`: the kit a new garden is grown from — the vocabulary, the templates, `germinate.py` |
| **vocabulary** | the rules, as data: `seed/std-vocab.md` for every garden, plus a garden's own `VOCAB.md` |
| **gate** | `bin/dmcheck.py`, run as a pre-commit hook: a commit that breaks a rule is refused |
| **journal** | `log/journal.md`: every change, who made it and why. The gate refuses an unrecorded change |
| **anchor** | a fact that identifies an object (a serial, a domain name), so two gardens recognise the same thing |
| **nature / genos** | what sort of being it is: `soma`, a body; `lekton`, what exists by being said and agreed; or `empsychon`, what lives, while it lives — refined by a genos, its kind, such as `host`. The words are Greek, and `MODEL.md` gives each |
| **facet** | an aspect of ownership, e.g. `legal` or `technical`; each has exactly one owner, and one entry saying who answers for it |
| **crown** | where every ownership chain ends: at `theos`, which no bean names, through a branch for each nature — `physis` for soma, `logos` for lekton, `agape`, love that does not possess, for empsychon. A person writes `owned_by: { legal: { crown: agape } }` |
| **profile** | an opt-in group of rules, e.g. `domain`, for gardens that hold that kind of thing |
| **vacancy** | a value the vocabulary offers that nothing uses yet, stated with a reason |
| **Contract of Parts** | `MODEL.md`: which decisions an agent may take alone and which a person must ratify |
| **proposal** | what one garden offers another: one file of beans, laid outside both gardens, which the other garden's gardener takes in by committing it — or does not. Taking it in accepts nothing on the gardener's behalf. `bin/dmpropose.py` |
| **mycelium** | how gardens meet: beneath, through the agreements between their gardeners and the proposals made under them, in the language they share. Owned by no garden |

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

A garden moving into std-vocab 21.0 must name its gardener. The garden's own copy of the tool may be older than the
flag for it, so name them in the environment, which every copy passes on:
`DAFTAR_GARDENER=sam python3 bin/dmupgrade.py <tag>` for an existing person or organisation bean, adding
`DAFTAR_GARDENER_NAME="Sam"` to plant a new one (`INSTALL.md` has the PowerShell form). A garden already at 21.0 or
later takes `--gardener sam` and `--gardener-name "Sam"` instead. Crossing into std-vocab 22.0 changes every bean and
asks nothing: its words for what a being is are translated into the law's Greek ones.

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
| `bin/dm*.py` | the other tools — merge, proposals between gardens (`dmpropose`), what is owed (`dmledger`), upgrade, rules (`dmrules`), reasons (`dmwhy`), safe edits, the journal entry (`dmjournal`), cursors, sessions, staleness, calendars, coordinates, units. Each says what it does in its first lines |
| `MODEL.md`, `CHECKLIST.md`, `MERGE.md` | the model, the write procedure, the merge algebra |
| `seed/RATIONALE.md` | why each rule is as it is, keyed by the rule's own path; `python3 bin/dmwhy.py <name>` reads law and reason together |
| `AGENTS.md`, `.claude/skills/daftar/` | one text, twice: the door for an agent with a shell — a reading order, no rules |
| `seed/WELCOME.md` | the door for an assistant with no shell, written to be pasted into a chat |
| `seed/README.md`, `seed/COOKBOOK.md` | worked beans that pass the gate as written: the gardener, a host, a domain, a service, a rented server, a cost shared between two people, an agreement paid in instalments, a statement, an event, another person's garden |
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

[Apache-2.0](LICENSE).
