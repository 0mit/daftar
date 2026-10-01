# Proposing changes

This repository is the home of daftar's **language**: the vocabulary, the gate, the tools and the
documents that say what they mean. Every garden that speaks it — including the maintainers' own — is a
satellite. Satellites propose; the maintainers decide. **Merging a pull request is the ratification.**

That follows `MODEL.md`'s Contract of Parts: a change to a vocabulary term or rule, or to a clause of the manifesto
(class G), is proposed by anyone and ratified by a human, and it is recorded distinctly as a rule-change (manifesto:
parts, changes).

## Before you open a pull request

1. **Say which of two things you are proposing, because they are judged differently.**
   - **A term for a kind of FACT** — something an estate contains (a registration, a rental, a risk). It
     starts as a `local_terms` entry in your garden's `VOCAB.md`, used by real beans, and is promoted here
     once it has held real cases. A term for a fact nobody has yet recorded usually generalises wrongly,
     because what it gets wrong is the world, and only the world can correct it.
   - **A MECHANISM** — a figure, a schema construct, a positioning system, a unit, a missing side of a
     structure the law already uses. A mechanism may be proposed WHOLE, ahead of its occupants. The
     standard is a language for every estate, and a language shaped only by what its first garden happened
     to contain is tied to that garden's size: `extent` waited two versions for an occupant while forty
     durations sat in prose because nothing could say them. The test is not "has our garden met it" but
     **would a stranger with a different estate expect it to be there** — and is it:
     *universal* (no estate in it), *general* (the same shape as something the law already has, extended
     rather than invented beside it), *canonical* (an off-the-shelf concept where the tradition has one),
     *useful* (you can name who would reach for it), and *simple to read*. Its unoccupied positions are
     declared vacant with the reason `universal` and a `why` — so the law still accounts for every position
     it offers, and nobody mistakes design for evidence.
2. **Bring evidence for what evidence can settle.** For a fact-term: what happened in a real garden, what
   the vocabulary could not say, and the beans it affected — from the estate, never from a test. For a
   mechanism: the structure it completes, the neighbours it was modelled on, and what was considered and
   rejected. Judgment and common sense are evidence here; say whose. For any change to the law, paste what
   `python3 bin/dmreview.py --law --against <the tag you started from>` prints: it counts what the change adds,
   removes, restates and narrates, and judges nothing — the maintainer who merges judges, beauty included.
3. **Leave your estate out of it.** Do not paste host names, addresses, paths, people, or findings from
   your own garden into the proposal or into the law. Use neutral examples — `host-a`, `203.0.113.10`,
   `/home/user/…`. The vocabulary ships to everyone (manifesto: never-sells).
4. **Say which kind of change it is.** Adding a term, a value or a registry row is **minor**: nothing that
   passed before stops passing. Changing a rule, a merge order or a requirement is **major**: it can
   re-classify beans that already passed, in every garden.
5. **Run the tests** — one command a line, which runs alike in a Unix shell and in PowerShell (`python` on Windows);
   each ends by saying how many of its checks passed, or how many failed, and every one must be green:

   ```sh
   python3 bin/dmsafe.py
   python3 test/assets.py
   python3 test/germinate.py
   python3 test/refusals.py
   python3 test/journal.py
   python3 test/days.py
   python3 test/ordinal.py
   python3 test/profiles.py
   python3 test/rope.py
   python3 test/root.py
   python3 test/core.py
   python3 test/core_save.py
   python3 test/core_translate.py
   python3 test/core_standards.py
   python3 test/core_rehearse.py
   python3 test/core_guides.py
   python3 test/core_merge.py
   python3 test/save.py
   python3 test/sequence.py
   python3 test/stamps.py
   python3 test/converge.py
   python3 test/upgrade.py
   python3 test/knowledge.py
   python3 test/figures.py
   python3 test/place.py
   python3 test/expiry.py
   python3 test/reform.py
   python3 test/positions.py
   python3 test/shape.py
   python3 test/calendars.py
   python3 test/rationale.py
   python3 test/recurrence.py
   python3 test/quantities.py
   python3 test/money.py
   python3 test/peering.py
   python3 test/site.py
   python3 test/public.py
   python3 test/docs.py
   python3 test/manifesto.py
   python3 test/layers.py
   python3 test/base.py
   python3 test/view.py
   python3 test/viewcap.py
   python3 test/senses.py
   python3 test/uncertainty.py
   python3 test/zones.py
   python3 test/reckon.py
   python3 test/privacy.py
   python3 test/held.py
   python3 test/passes.py
   python3 test/launch.py
   python3 test/hub.py
   python3 test/agreements.py
   python3 test/observations.py
   python3 test/crosswalk.py
   python3 test/rehearsal.py
   python3 test/deeptime.py
   python3 test/catalogue.py
   python3 test/garden.py
   reuse lint
   ```

   CI runs a brief set of them on every push and pull request — the documents, the manifesto, the journal, the assets,
   the site and what is public — and the whole list only when the workflow is run by hand; before a release, run the
   whole list here with `python3 test/timings.py -j 6` (`reuse lint` is the REUSE tool, `pip install reuse`). `test/site.py` builds the page again with `site/board.py`,
   which clones this repository at the tag `site/RELEASE` names: a clone without its tags cannot run it.

   Two files under test/ measure rather than judge, and CI does not run them. The one runner of the whole list is
   `python3 test/timings.py [-j N] [--status FILE]`: it runs the suites above, N at a time, and appends each one's seconds
   to `test/timings.tsv`. With `--status`, it also keeps a JSON document of the run in progress, which a page can draw
   as a race. `python3 test/cost.py` measures the gate's cost per 10,000 series rows, with each YAML loader, and appends
   it to the same file. Run it before a change that moves population-sized data.

## This repository carries the language, never a garden

A garden is private; this is not, and the two are edited in the same sessions. What leaks is never the
beans — it is the prose around them: an example path in a comment, a measurement written with the machines'
real names, a commit message, a pull request body. Those are the places nobody greps.

    git config daftar.garden /path/to/your/garden     # once per clone
    python3 bin/dmpublic.py --garden <path> [--range origin/master..HEAD] [--text pr-body.md]

`bin/install.sh` installs a **pre-push hook** that runs it over the files and over the messages of the
commits being pushed. It derives the forbidden names from the garden itself — every bean and mapping id,
the value of every identity anchor, root names — so a bean added tomorrow is covered tomorrow, and nobody
maintains a denylist. It guards names of three letters and more, bean titles of three words and more, and every network
and email address a bean holds (those kept for documentation aside). A word the published technology catalogue carries,
or the law's own name for a kind of being, is not a leak; a word of the other published tables is public only in its
own table; anything else that is genuinely public goes in `seed/PUBLIC-ALLOW` with its reason.

**Check the pull request body too.** The hook cannot see it: write it to a file, run `--text` over it, then
open the pull request. This rule exists because five estate names reached this repository in one night, in
comments and pull request text, and were found by the operator rather than by a diff.

Say it without the name: "one host", "another machine", `/home/user/tree`, `host-a` and `host-b`.

## Your contribution's terms

What you contribute is given under the licence of the part it goes into, as `REUSE.toml` gives it: code under the GNU
AGPL 3.0 or later with the garden exception, which you grant for your contribution as the steward grants it for his;
the law and the guides under CC BY 4.0; the seeds of a garden's own files under CC0 1.0. Contributing to the law, you
make the patent promise of `CHARTER.md` §4 for your own patents; contributing code, you grant the licence of the AGPL's
section 11. You keep your copyright: nothing is assigned.

**Sign each commit** (`git commit -s`). The sign-off is the Developer Certificate of Origin 1.1
(https://developercertificate.org), and the licence it names is the one `REUSE.toml` gives the file. It is added by a
person, never by an agent on its own: that person has read the change, has the right to give it (an employer's right
included), and answers for it. The agent is named in its own trailer (`Co-Authored-By:` or `Assisted-by:`). A sign-off
may use the name the contributor is known by, and an address the leak guard does not refuse: an account's
no-reply address is one. Commits made before this section was added carry none; they are the
steward's own. CI refuses a pull request with a commit that carries no sign-off.

## Editing the vocabulary itself

- The vocabulary is `seed/std-vocab.md`: YAML front matter (the law) and a short Markdown body. Edit the front
  matter, and add one entry to `seed/CHANGELOG.md`, the law's journal, above the newest, naming the change and why.
- **The layers** (manifesto: layers; which file sits in which is the law's `layers`, and `MODEL.md` says what each holds). What a reader needs in order to APPLY a rule
  goes in the item's own `meaning:` or `why:`, present tense, no date, no name, with no commentary; why it is that way
  goes in `seed/RATIONALE.md` under the item's path (`python3 bin/dmwhy.py <name>` reads both; `--check` finds a
  reason whose law is gone); the changelog entry says what changed and why; the commits are the record.
- Bump its `version:` in the same change — minor for additive, major for a changed rule — and nothing else:
  gardens move their own pins when they adopt a release.
- `python3 bin/dmrules.py` inside a garden prints every rule as the gate reads it; use it to check that your
  term says what you meant.
- `python3 bin/dmwhy.py <name>` shows why an existing rule is the way it is (`seed/RATIONALE.md`); `HISTORY.md` has
  the design steps before that. Read the relevant part before proposing to change one.
- `python3 bin/dmcatalog.py --part <name>` shows what a change to an item touches: every file that mentions, states,
  covers or explains it, what it uses and what uses it, and the rules, checklist items and suite checks that name it.
  `--findings` lists the candidates for a reword it sees (an item nothing references, one domain under two names, a
  sibling shaped unlike the rest), for a person to judge.
- Some comments mention `test/golden.py` and `test/diffgate.py`. They are the maintainers' corpus tests,
  which need a real garden's beans and so are not published.

## The site

`site/` holds the project's public page: one page, `site/index.html`, that shows daftar through four lenses (someone
curious, a gardener, an agent, a keeper of the law) and ten mechanisms, a board for every crossing. `python3
site/board.py` writes it from the release that `site/RELEASE` names, cloned at that tag. A keeper's board is read from
that release (the law's meanings, their reasons, the catalogue's rules, checks and relations), so it cannot drift from
it. An agent's board is proved: the builder grows a garden from the release, writes the beans of `site/garden.yaml`,
and saves them with the command the gate board shows, and the gate must pass them. It then breaks each board's form
once, as its `scene` in `site/boards.yaml` says, and shows the refusal the gate printed. The words each lens reads are
written in `site/boards.yaml`, in each of the page's languages (English, and Persian, read right to left), with the
page's own words under `ui`; the law's words, the forms and what the gate prints stay as the release states them. The
page's template, style and script are `site/board.html` and `site/assets/`. A
change to a tool reaches the page only through a release: bump `site/RELEASE` to its tag, run `python3
site/board.py`, and commit the page. `python3 test/site.py` builds the page again in a temporary directory and fails
until the committed page agrees with it. It also checks that the page parses under a policy that runs no script and
loads no style but the site's own, that every link inside the site resolves, that nothing is loaded from outside it,
and that every issue form asks for the situation and warns against pasting from a garden; with `git config
daftar.garden` set, it runs the leak guard over every file of the site.

To ask rather than propose (a need, a use case, a suggestion, a question, a bug), open an issue. Each form asks for
the situation in your own words, and for nothing from your garden.

## What happens next

A maintainer reads the proposal against its neighbours — the sibling terms and records it would affect —
and either merges it, asks for changes, or closes it with the reason. Merged changes reach gardens in the
next release tag, which each garden adopts with `bin/dmupgrade.py` when its own human decides to.

## Releases

Maintainers tag releases `vMAJOR.MINOR.PATCH` on `master`. The vocabulary's own version lives in
`seed/std-vocab.md` (`version:`), and its changelog is `seed/CHANGELOG.md`; a release names both.
