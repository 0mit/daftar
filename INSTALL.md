# Installing daftar — for the agent that will do it

Someone pointed you here because they want a daftar **garden**: a private git repository where you, and any
agent after you, keep facts about their things — each fact with its source, every change journalled, a gate
refusing what breaks a rule. `README.md` says why. This page says how, and it is written for you to follow,
not for the person to type.

Ask the person only for what you cannot know:

1. **where the garden goes** — a directory that does not exist yet, named for this garden (below: `~/garden-sam`).
   Its name is the garden's name: another garden sees it, and so does every proposal this one makes. Give each
   garden a name of its own — not `~/garden` for every one — in kebab-case, lowercase words joined by hyphens:
   germinate refuses any other name before it creates anything, and `--name garden-sam` names a garden whose
   directory is called something else;
2. **who keeps it** — the garden's **gardener**: a short id for them (lowercase and hyphens, below: `sam`) and how
   they are called (below: `Sam`), and whether it is a person or an organisation. A garden is someone's, and a
   garden grown this way begins with their bean;
3. **the private remote**, or that there is none yet (below: `git@github.com:me/garden.git`);
4. **the identity you commit under** — a name that says which agent you are, and an address they choose.

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
python3 seed/germinate.py ~/garden-sam --gardener sam --gardener-name "Sam"
```

(`sh seed/germinate.sh ~/garden-sam --gardener sam --gardener-name "Sam"` does the same; it hands over to the
Python. For an organisation, add `--gardener-genos org`.)

The target must not exist. The script copies what `seed/LANGUAGE` declares — the vocabulary, the tools, the
gate, the templates, `AGENTS.md` — makes the first commit as `germinate`, installs the gate as the pre-commit
hook, and then plants the gardener: a person bean, `beans/sam.md` (an `org` bean with `--gardener-genos org`), named
in `GARDEN.md` as `gardener: sam`, in a second commit with its journal entry. It runs the gate and prints zero errors and zero warnings. Read what it
prints: its last lines are the ones that matter. Grown without `--gardener`, the garden asks for its gardener as
its first bean, and the gate refuses every other bean until `GARDEN.md` names one.

## 3. Give it an identity and a home

```sh
cd ~/garden-sam
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

`AGENTS.md` is a reading order: `seed/FORMS.md` before writing — what an agent writes most, the way the gate
accepts it — and the model, the checklist and the rules in force when a question needs them. It carries no rules
itself, because the law is in the garden — this repository's copy may be newer or older than the one the garden pins.
Show the person the gate's last line. From here on, everything you need is in the garden.

## 5. Every later session

The person will say something like *"load daftar"* or *"read AGENTS.md in ~/garden-sam"*. Do that first: run the
gate, read the reading order, look at the journal's tail for what the last session left, and then work. When
the person decides something in the session — ratifies an identity anchor, approves a change — the commit is
still yours, and the journal entry says who decided and in what words: `human (name) ratified, applied by
agent (…)` is the shape this garden's own journal uses. Before you leave, write the journal entry the next
agent will need — it may be of another make, with none of your context.

## Upgrading a garden to a newer release

```sh
python3 bin/dmupgrade.py <tag>
```

It fetches the release, applies it, translates what the law re-spelled, writes the journal entry, runs the gate,
and commits nothing: read `git diff`, fill in the entry's two `fill in` fields, commit. If anything stops it
midway, or the garden fails the new gate, every file is put back as it was. Crossing into std-vocab 22.0 changes
every bean and asks nothing: `kind:` becomes `genos:`, and a nature and a crown branch take their Greek names
(`MODEL.md` says what each means).

Because that crossing changes every bean, bring in what the garden's other copies hold first — merge every branch,
and every clone's commits — so that it translates everything at once. A branch or a clone still at 21.0 afterwards is
merged INTO the garden that crossed, never the other way round. There the merge driver reads each side of a bean in
22.0's words, so the bean keeps one `genos` and one nature; but the crossing changed that bean too, so each key the
branch changed on it comes back as a disagreement for a person to settle (`merge_open`), as whenever two sides change
one bean. A bean only that branch added arrives as it was written; the gate names the command that translates it,
which is the same one, run again with the release `GARDEN.md` records. The garden's OWN code is never translated: a
tool, a test or a template of its own that reads a bean's `kind` must be taught `genos` and the Greek natures before
the crossing is relied on — the upgrade names the files of the garden's own that say a retired word.

Moving a garden into std-vocab 21.0 also asks who keeps it. Name the gardener in the environment — the one form
every garden's own tool passes on, whatever release it runs (a tool older than the `--gardener` flag rejects the
flag, then hands over to the release's tool, which reads the environment):

```sh
DAFTAR_GARDENER=sam python3 bin/dmupgrade.py <tag>                               # sam: an existing person or org bean
DAFTAR_GARDENER=sam DAFTAR_GARDENER_NAME="Sam" python3 bin/dmupgrade.py <tag>    # plants a new person bean for them
```

`DAFTAR_GARDENER_GENOS=org` beside them plants an organisation instead, as `germinate --gardener-genos org` does. A
garden already at 21.0 or later takes the same as flags: `--gardener sam`, with `--gardener-name "Sam"` to plant and
`--gardener-genos org` for an organisation. (`DAFTAR_GARDENER_KIND` and `--gardener-kind`, their names before 22.0,
are still read.) Whatever is missing, the refusal prints the line that fixes it, in the form
this garden's tool accepts. A garden whose name is not in the form 21.0 gives a garden's name (kebab-case) is refused
before anything is touched, with the `garden:` line to write in `GARDEN.md` and the RULE-CHANGE entry that goes with
it.

## On Windows

Everything here is Python and git, so it runs in PowerShell — with `python` for `python3`, backslashes or forward
slashes as you like, and `$HOME` for `~`:

```powershell
git clone https://github.com/0mit/daftar.git $HOME\daftar
cd $HOME\daftar
git checkout (git tag -l 'v*' --sort=-v:refname | Select-Object -First 1)
python seed\germinate.py $HOME\garden-sam --gardener sam --gardener-name "Sam"
cd $HOME\garden-sam
git config user.name  "agent (<model>, <session>)"
git config user.email "<the address the person chose>"
python bin\dmcheck.py --all
```

**Which Python.** On Windows `python` and `python3` may not be Python at all: they can be the Microsoft Store's
*App execution aliases*, which only offer to install it. `python -c "import sys; print(sys.executable)"` tells
them apart: a Python prints its own path, the alias answers "Python was not found" or opens the Store
(`where.exe python` lists it under `WindowsApps`). Install Python from python.org, or turn the aliases off
(Settings > Apps > Advanced app settings > App execution aliases). The installer from python.org usually brings
the `py` launcher too: `py -3 seed\germinate.py …` runs the newest Python 3 even where the aliases are in the
way. PyYAML: `py -3 -m pip install PyYAML` (or `python -m pip install PyYAML`).

The gate runs as a git hook; Git for Windows runs hooks with the shell it ships. The hook, `bin/install.py` and
`bin/install.sh` choose the first Python that runs AND imports yaml — `git config daftar.python`, then `python3`,
`python` and `py -3` — skipping the Store alias, and record it per clone as `git config daftar.python`; when none
works they say, for each, why. To choose one yourself: `git config daftar.python C:/path/to/python.exe`.

**UTF-8.** Every bean is UTF-8, and the tools read and write it correctly whatever the machine's language —
their output through a pipe, a journal entry's body on standard input, and `bin/dmsafe.py`'s block included.
Windows PowerShell 5.1 does not: it reads a UTF-8 file without a BOM in the old code page, so a Persian bean —
or any bean with a character outside ASCII — read with `type` or `Get-Content` arrives garbled, and a bean
written with `>` or `Out-File` is saved as UTF-16, which the gate cannot read. Read with
`Get-Content -Encoding UTF8 beans\sam.md` (or through Python), and write through the tools or an editor that
saves UTF-8. When a tool's output is read through a pipe, `$env:PYTHONUTF8 = "1"` and
`[Console]::OutputEncoding = [Text.Encoding]::UTF8` make Python write UTF-8 and PowerShell read it as UTF-8. The
hooks set `PYTHONUTF8` themselves. PowerShell 7 reads and writes UTF-8 by default.

**Three things a Unix shell does that Windows PowerShell 5.1 does not**, and the form every page and every tool's
message here uses instead, so that what is printed runs as printed:

- `&&` joins two commands only from PowerShell 7. Run `git add -A`, then `git commit`: two commands.
- `<` does not redirect standard input in any PowerShell. A journal entry's body goes in as an argument:
  `python bin\dmjournal.py "<who>" "<what>" --body "- action: …"`. A line break typed inside the quotes is kept;
  so is `` `n `` inside double quotes. Windows PowerShell 5.1 drops a double quote *inside* an argument — write the
  body without one there (PowerShell 7.3 and later pass it intact). A block for `bin/dmsafe.py` goes in as a file:
  `python bin\dmsafe.py insert-after beans\sam.md responsibility --block block.yaml`.
- `>` and `Out-File` write UTF-16, which the gate does not read (above): a bean is saved as UTF-8. Only
  `bin/dmjournal.py`'s body and `bin/dmsafe.py`'s block may be UTF-16, with its mark; without the mark each is
  refused (read as UTF-8 it is a NUL after every letter), and `bin/dmjournal.py` refuses every control character but
  a tab.

An upgrade that names the gardener through the environment clears it again at the end, because a PowerShell
session keeps what `$env:` sets, and the next garden upgraded in it would take the same gardener without being
asked:

```powershell
$env:DAFTAR_GARDENER = "sam"; python bin\dmupgrade.py <tag>; Remove-Item Env:DAFTAR_GARDENER, Env:DAFTAR_GARDENER_NAME, Env:DAFTAR_GARDENER_GENOS, Env:DAFTAR_GARDENER_KIND -ErrorAction SilentlyContinue
```

**Line ends.** Git for Windows checks text out with CRLF by default, and a git hook with a CR in it does not run.
The garden's `.gitattributes` keeps its shell files LF, and `bin/install.py` installs the hooks with LF whatever
the checkout did — so after any checkout, `python bin\install.py` puts working hooks in place.

## If you have no shell

You are in a chat window, and cannot run any of the above. Then you cannot run the gate, and cannot write to a
garden; do not say you have. `seed/WELCOME.md` is written for you: what you can honestly produce is a
*proposal* — the full text of a bean, the journal entry that would go with it, and a list of what you could
not check — for a person, or an agent with a shell, to commit.

## By hand, without an agent

The same three steps grow a garden for a person. Then `seed/README.md` shows a person, a host, and the journal
entry that commits them, and `seed/COOKBOOK.md` goes on from the gardener: machines, a domain, another person and
the garden she keeps, a dinner, a cost shared and a loan repaid in instalments, a statement, a proposal between two
gardens, and how to add a value the vocabulary lacks. All of them pass the gate exactly as written, because a test
grows a garden and commits them one recipe at a time, in the order of the page. A journal heading is a position in
time, read from the clock — so a tool writes it, never a hand; you give it the body:

```sh
python3 bin/dmjournal.py "your-name" "what you did" --body "- action: added [[laptop]]."
```

When the gate refuses something, its message names the rule and, for the common mistakes, the line to write;
`python3 bin/dmwhy.py <name>` says why that rule is as it is. `MODEL.md` explains the model, `CHECKLIST.md` how a
write is made, and `python3 bin/dmrules.py` prints every rule in force.
