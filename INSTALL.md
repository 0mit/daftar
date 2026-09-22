# Installing daftar — for the agent that will do it

Someone pointed you here because they want a daftar **garden**: a private git repository where you, and any
agent after you, keep facts about their things — each fact with its source, every change journalled, a gate
refusing what breaks a rule. `README.md` says why. This page says how, and it is written for you to follow,
not for the person to type.

Ask the person only for what you cannot know:

1. **where the garden goes** — a directory that does not exist yet (below: `~/garden`);
2. **the private remote**, or that there is none yet (below: `git@github.com:me/garden.git`);
3. **the identity you commit under** — a name that says which agent you are, and an address they choose.

Requires Python 3 and PyYAML (`pip install PyYAML`). Nothing else. Nothing here contacts any service.

## 1. Get the language, pinned to a release

```sh
git clone https://github.com/0mit/daftar.git ~/daftar
cd ~/daftar
git checkout "$(git tag -l 'v*' --sort=-v:refname | head -1)"
```

The release you check out may be older than this page and not carry it: read the page to the end first, or
keep it open from the web. Everything from step 2 on is in the garden itself. A garden records which
release it runs, and `bin/dmupgrade.py` moves it to a newer one when the person decides to. Growing from an
untagged clone works, but pins the garden to nothing anyone else can fetch; `germinate.sh` will say so if you do.

## 2. Grow the garden

```sh
sh seed/germinate.sh ~/garden
```

The target must not exist. The script copies what `seed/LANGUAGE` declares — the vocabulary, the tools, the
gate, the templates, `AGENTS.md` — makes the first commit as `germinate`, installs the gate as the pre-commit
hook, runs it, and prints zero errors and zero warnings. Read what it prints: its last lines are the ones that
matter.

## 3. Give it an identity and a home

```sh
cd ~/garden
git config user.name  "agent (<model>, <session>)"       # the form germinate.sh prints; e.g. "agent (claude fable-5.1, claude-code 2026-09-22)"
git config user.email "<the address the person chose>"
git remote add origin git@github.com:me/garden.git      # if there is a remote
git push -u origin HEAD                                 # the branch is whatever `git init` named it
```

Every commit after the first is yours. Write the journal's "who" as the same name, so a reader later tells a
person's decision from an agent's action by either record; the gate checks that the entry is there, not that
the two names agree. A person who commits by hand sets their own identity the same way.

## 4. Read the garden's own door

```sh
cat AGENTS.md
python3 bin/dmcheck.py --all
```

`AGENTS.md` is a reading order: the model, the checklist, the rules in force. It carries no rules itself,
because the law is in the garden — this repository's copy may be newer or older than the one the garden pins.
Show the person the gate's last line. From here on, everything you need is in the garden.

## 5. Every later session

The person will say something like *"load daftar"* or *"read AGENTS.md in ~/garden"*. Do that first: run the
gate, read the reading order, look at the journal's tail for what the last session left, and then work. When
the person decides something in the session — ratifies an identity anchor, approves a change — the commit is
still yours, and the journal entry says who decided and in what words: `human (name) ratified, applied by
agent (…)` is the shape this garden's own journal uses. Before you leave, write the journal entry the next
agent will need — it may be of another make, with none of your context.

## If you have no shell

You are in a chat window, and cannot run any of the above. Then you cannot run the gate, and cannot write to a
garden; do not say you have. `seed/WELCOME.md` is written for you: what you can honestly produce is a
*proposal* — the full text of a bean, the journal entry that would go with it, and a list of what you could
not check — for a person, or an agent with a shell, to commit.

## By hand, without an agent

The same three steps grow a garden for a person. Then `seed/README.md` shows a person, a host, and the journal
entry that commits them, and `seed/COOKBOOK.md` a domain, a service on a machine, a rented server, and how to
add a value the vocabulary lacks. All of them pass the gate exactly as written, because a test grows a garden
and commits them. A journal heading is a position in time, read from the clock — so a tool writes it, never
a hand:

```sh
python3 bin/dmjournal.py "your-name" "what you did" < entry.md     # the entry's body on standard input
```

When the gate refuses something, its message names the rule and, for the common mistakes, the line to write.
`MODEL.md` explains the model, `CHECKLIST.md` how a write is made, and `python3 bin/dmrules.py` prints every
rule in force.
