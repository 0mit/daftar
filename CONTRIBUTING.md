# Proposing changes

This repository is the home of daftar's **language**: the vocabulary, the gate, the tools and the
documents that say what they mean. Every garden that speaks it — including the maintainers' own — is a
satellite. Satellites propose; the maintainers decide. **Merging a pull request is the ratification.**

That follows `MODEL.md`'s Contract of Parts: a change to a vocabulary term or rule (class G) is proposed
by anyone and ratified by a human, and it is recorded distinctly as a rule-change.

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
   `/home/user/…`. The vocabulary ships to everyone.
4. **Say which kind of change it is.** Adding a term, a value or a registry row is **minor**: nothing that
   passed before stops passing. Changing a rule, a merge order or a requirement is **major**: it can
   re-classify beans that already passed, in every garden.
5. **Run the tests** — one command a line, which runs alike in a Unix shell and in PowerShell (`python` on Windows);
   each ends by saying how many of its checks passed, or how many failed, and every one must be green:

   ```sh
   python3 bin/dmsafe.py
   python3 test/germinate.py
   python3 test/refusals.py
   python3 test/journal.py
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
   python3 test/mycelium.py
   python3 test/public.py
   python3 test/docs.py
   ```

   CI runs the same on every pull request.

## This repository carries the language, never a garden

A garden is private; this is not, and the two are edited in the same sessions. What leaks is never the
beans — it is the prose around them: an example path in a comment, a measurement written with the machines'
real names, a commit message, a pull request body. Those are the places nobody greps.

    git config daftar.garden /path/to/your/garden     # once per clone
    python3 bin/dmpublic.py --garden <path> [--range origin/master..HEAD] [--text pr-body.md]

`bin/install.sh` installs a **pre-push hook** that runs it over the files and over the messages of the
commits being pushed. It derives the forbidden names from the garden itself — every bean and mapping id,
the value of every identity anchor, root names — so a bean added tomorrow is covered tomorrow, and nobody
maintains a denylist. A word the published classifications carry is not a leak; anything else that is genuinely public
goes in `seed/PUBLIC-ALLOW` with its reason.

**Check the pull request body too.** The hook cannot see it: write it to a file, run `--text` over it, then
open the pull request. This rule exists because five estate names reached this repository in one night, in
comments and pull request text, and were found by the operator rather than by a diff.

Say it without the name: "one host", "another machine", `/home/user/tree`, `host-a` and `host-b`.

## Editing the vocabulary itself

- The vocabulary is `seed/std-vocab.md`: YAML front matter (the law) and a Markdown body ending in a
  changelog. Edit the front matter; add one changelog entry, above its version's neighbours, naming the change and why.
- **Four layers, each standing on the one beneath.** LAWS are clear and brief, for usability and efficiency: what a
  reader needs in order to APPLY a rule goes in the item's own `meaning:` or `why:`, present tense, no date, no name,
  and the law carries no commentary. REASONING is the backbone for the laws: why it is that way goes in
  `seed/RATIONALE.md` under the item's path (`python3 bin/dmwhy.py <name>` reads both; `--check` finds a reason whose
  law is gone). JOURNALS are the leads for the reasoning: the changelog entry says what changed and why. HISTORY is the
  exact record the journals are written from: the commits themselves. A thing belongs in exactly one layer.
- Bump its `version:` in the same change — minor for additive, major for a changed rule — and nothing else:
  gardens move their own pins when they adopt a release.
- `python3 bin/dmrules.py` inside a garden prints every rule as the gate reads it; use it to check that your
  term says what you meant.
- `python3 bin/dmwhy.py <name>` shows why an existing rule is the way it is (`seed/RATIONALE.md`); `HISTORY.md` has
  the design steps before that. Read the relevant part before proposing to change one.
- Some comments mention `test/golden.py` and `test/diffgate.py`. They are the maintainers' corpus tests,
  which need a real garden's beans and so are not published.

## What happens next

A maintainer reads the proposal against its neighbours — the sibling terms and records it would affect —
and either merges it, asks for changes, or closes it with the reason. Merged changes reach gardens in the
next release tag, which each garden adopts with `bin/dmupgrade.py` when its own human decides to.

## Releases

Maintainers tag releases `vMAJOR.MINOR.PATCH` on `master`. The vocabulary's own version lives in
`seed/std-vocab.md` (`version:`) with a changelog at the end of that file; a release names both.
