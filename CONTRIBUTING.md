# Proposing changes

This repository is the home of daftar's **language**: the vocabulary, the gate, the tools and the
documents that say what they mean. Every garden that speaks it — including the maintainers' own — is a
satellite. Satellites propose; the maintainers decide. **Merging a pull request is the ratification.**

That follows `MODEL.md`'s Contract of Parts: a change to a vocabulary term or rule (class G) is proposed
by anyone and ratified by a human, and it is recorded distinctly as a rule-change.

## Before you open a pull request

1. **Prove it locally first.** A new term normally starts as a `local_terms` entry in your garden's
   `VOCAB.md`, used by real beans. A term that has held real cases is promoted here; one invented for a
   case not yet met usually generalises wrongly.
2. **Bring evidence from a real garden, not from a test.** What happened, what the vocabulary could not
   say, and the beans it affected.
3. **Leave your estate out of it.** Do not paste host names, addresses, paths, people, or findings from
   your own garden into the proposal or into the law. Use neutral examples — `host-a`, `203.0.113.10`,
   `/home/user/…`. The vocabulary ships to everyone.
4. **Say which kind of change it is.** Adding a term, a value or a registry row is **minor**: nothing that
   passed before stops passing. Changing a rule, a merge order or a requirement is **major**: it can
   re-classify beans that already passed, in every garden.
5. **Run the tests:**

   ```sh
   python3 bin/dmsafe.py && python3 test/germinate.py && python3 test/converge.py && python3 test/upgrade.py && python3 test/knowledge.py && python3 test/figures.py && python3 test/place.py
   ```

   CI runs the same on every pull request.

## Editing the vocabulary itself

- The vocabulary is `seed/std-vocab.md`: YAML front matter (the law) and a Markdown body ending in a
  changelog. Edit the front matter; add one changelog entry at the end, naming the change and why.
- Bump its `version:` in the same change — minor for additive, major for a changed rule — and nothing else:
  gardens move their own pins when they adopt a release.
- `python3 bin/dmrules.py` inside a garden prints every rule as the gate reads it; use it to check that your
  term says what you meant.
- `HISTORY.md` explains why existing rules are the way they are — read the relevant part before proposing to
  change one.
- Some comments mention `test/golden.py` and `test/diffgate.py`. They are the maintainers' corpus tests,
  which need a real garden's beans and so are not published.

## What happens next

A maintainer reads the proposal against its neighbours — the sibling terms and records it would affect —
and either merges it, asks for changes, or closes it with the reason. Merged changes reach gardens in the
next release tag, which each garden adopts with `bin/dmupgrade.py` when its own human decides to.

## Releases

Maintainers tag releases `vMAJOR.MINOR.PATCH` on `master`. The vocabulary's own version lives in
`seed/std-vocab.md` (`version:`) with a changelog at the end of that file; a release names both.
