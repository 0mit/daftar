# Handover: branch `claude/magical-feynman-lg8qm0` (pull request 51)

Written on 2026-09-27 by the agent that did this work (`agent:claude`), for whoever continues it on another machine,
a person or an agent of any make. It is a record, not an instruction: instructions come from the person you work for
(AGENTS.md). Like `REVIEW-v0.38.0.md` beside it, this file is working material for the branch. Whoever merges decides
whether either one stays.

## 1. Where things stand

- **Branch:** `claude/magical-feynman-lg8qm0` on `github.com/0mit/daftar`, based on `master` at `5f55653`, 35 commits
  plus this handover. Pull request: https://github.com/0mit/daftar/pull/51 (open, not merged).
- **CI:**
  - On `1f0b6ba`, 38 of 39 checks were green. `python3 test/upgrade.py` was red, because of a bug in the SSH-signed
    release test it adds; the log showed `FileNotFoundError: .../auth-release.pub`.
  - `cfad75e` fixes it, and was verified here with OpenSSH 9.6: 180/180, under this machine's git config and under one
    like CI's.
  - **First thing to do: look at the checks on the branch's newest commit.**
- **Law:** `seed/std-vocab.md` is at **25.0**, a proposed MAJOR rule-change. Merging the pull request is the
  ratification (CONTRIBUTING.md).
  - Every law change on this branch is described in the one 25.0 entry of `seed/CHANGELOG.md`.
  - A further law change on this branch goes into that same entry, in a commit titled `RULE-CHANGE 25.0: …`. There is
    no second version bump, unless the maintainer says otherwise.
- **The review:** `REVIEW-v0.38.0.md` has 40 findings (C1, H1–H4, M1–M10, 14 low-severity code items, and 11
  document/law items numbered D1–D11 in their order there).
  - 37 are fixed and tested.
  - D10 and D11 are fixed in part.
  - M10 is untouched: it needs the maintainer.

## 2. What each finding became

| Finding | What the branch does | Commit |
|---|---|---|
| C1 hub runs pushed code | Rights at the hub: a writer who is not the gardener needs `ratify:G` for code (the gate layer, release-kept files, any `.py`/shell file, the page's drawing module, and the `view.drawings` pointer). The checkout needs no shell (`git archive` and `tarfile`). A root commit is taken only by an empty hub, and only from the gardener its tree names. The hub still runs the tree's own gate, but only after every code change in the push was allowed by the gardener (dmhub docstring). | 77bd737 |
| H1 upgrade unauthenticated | `seed/RELEASE-SIGNERS`, placed in the `law` layer. `dmupgrade` checks the tag's SSH signature (`ssh-keygen -Y verify`), or takes `--expect <commit>`, or has a person at a terminal type the commit. Otherwise a release from a network is refused before any of it runs. | 15af8c0, cfad75e |
| H2 merge driver two-way | `dmmerge.three_way`: the driver reads `%O`. A change or removal made on one side stands, and only a position both sides changed differently is a conflict. MERGE.md §6 and §8. | 9bdb4ad, 586d2c0 |
| H3 privacy only warned | The gate refuses special-category material that a commit ADDS unsealed. COOKBOOK section "sealed before it is committed" gives the purge procedure. | 3946872 |
| H4 contracts grant anything | `dmpass.shares`: an agreement's grant covers only what its parties brought, and the gate warns when `over` reaches further. | 4b23d7e |
| M1 view form injection | Each value is parsed alone, as exactly its own attribute. | 4289c4e |
| M2 version prefix | A version refines another only at a component boundary. | c9cd327 |
| M3 group calendar naming | Registry domains are validated. A `system` row is read through its `calendar`. COOKBOOK now writes `gregorian-civil`. | 987265d |
| M4 drawing module | The path must be a `.py` inside the garden. The README states the trust boundary. The hub asks `ratify:G`. | 3ceb312, 77bd737 |
| M5 grant cache and time | The answer cache is keyed by UTC day. Also fixed: `_during` compared Unix day numbers with dmcal day numbers, so a time-bounded grant never began or ended. | 8571575 |
| M6 CI | Every suite on every push and pull request, in a matrix, and nightly. | 3251f8f |
| M7 duplicate-IP escape | New law term `shared_identifiers`. Networks are read from `located_at` in `network-segment`. | 3255354 |
| M8 atomic writes | `dmsafe.write_atomic`, used by dmsafe, dmheld and dmpropose. | 4167439 |
| M9 leak guard | Names of 3+ characters, titles, and IP and email addresses are guarded. Only the catalogue's words are public. `git ls-files -z` handles paths with spaces. With no `daftar.garden` set, the pre-push hook says that nothing was checked. | 68cecd1 |
| M10 ISCO-08 licence | **Not changed:** the maintainer decides (section 3). | — |
| L1–L14 | See the review's list, in order: 8faa5b0 (L1), 1f3c740 (L2), a3ae0b1 (L3), 566a964 (L4), ee65ecd (L5/L6), 2eb879b (L7), 7695fbe (L8), f831c0c (L9), ae295ce (L10), 39ab8a2 (L11, and a `due` epoch bug), 8c9896a (L12), 77bd737 (L13), 412d0c2 (L14). | |
| D1–D8 | The law's documents now say what the law says. | 7dfdba3 |
| D6 story in the law | 26 `meaning`s and `why`s moved their history to `seed/RATIONALE.md`. `dmreview` finds no story; v0.38.0 had 56. | 1f0b6ba |
| D9 | The timing rows use the suite's current name. The unshipped tests are said to be unshipped where they are named. | 8259225 |
| D10 changelog gap | The note's claim that git holds 2.0–5.0 was false; the 25.0 entry corrects it. The pace of MAJOR releases is process, not code. | e3f7818 |
| D11 site clock | The pages take the release and the held day from the build (`held` marker), and say why the clock is after the release. The date itself waits for a release (section 3). | c5cdc81 |

Found while fixing, and fixed:
- `dmheld due` counted days from the wrong starting point, so an `until` never fell due.
- The merge driver dropped identity and provenance changes made only on the other side, and could duplicate the text
  below the front matter.

## 3. What is left

1. **M10, the ISCO-08 licence.** Every garden redistributes `seed/knowledge/isco-08.tsv`, and the ILO has not answered
   the permission request of 2026-09-19. The options:
   - (a) keep it, documented as pending;
   - (b) ship the codes without titles, which breaks `dmknowledge find`, its gold set and the tests;
   - (c) fetch the titles at germination, behind an acknowledgement.

   The last recommendation made was (a) for now, and (c) if the answer is no or a garden goes public.
2. **The release key.** The real v0.38.0 tag verifies against `seed/RELEASE-SIGNERS` through
   `dmupgrade.verify_signature` (key `SHA256:9mnuXmb6IMsdX1QJ66O8XMopeh8eSx0sebrZAW51yYk`), and a tampered tag does not.
   The maintainer should still confirm that this is the key future releases will be signed with.
3. **The site's date (D11).** `site/build.py` holds the clock at 2026-10-27, because the v0.38.0 cookbook story pays
   its loan on 2026-10-01. To hold the pages at a release's own day:
   - re-date the COOKBOOK story so it ends before that release (FORMS is then derived again by `bin/dmforms.py`, and
     the story's dates appear in test/calendars, refusals, stamps, agreements, money and reckon);
   - release;
   - bump `site/RELEASE`, set `DEMO_NOW`, and rebuild with `python3 site/build.py`.
4. **After the merge:** a signed release, then bump `site/RELEASE` and rebuild. The terminology page still shows
   v0.38.0's law text until then, including an estate-like example that D8 removed from the source.
5. **Not in the review, but next to D6:** `dmreview --law` counts 18 vacancies whose reason is `prediction` (one
   estate's expectation, "ONE ESTATE IN THE STANDARD"). They are unchanged.
6. **Before merging:** decide whether `HANDOVER.md` and `REVIEW-v0.38.0.md` stay.

## 4. The working agreement the person set

- **No workflows and no subagents:** one step at a time, by hand.
- **Commits:** `git config user.name omid`, `git config user.email o.kord@live.com`, and `git commit -s` on every
  commit. A build run as `root` fails, so do not commit as root. Every commit on this branch carries `Signed-off-by`,
  and CI checks it on pull requests.
- **Keep private things private:** name no garden, host, person or estate of the person's own in this public
  repository, its commits or the pull request text. Examples are neutral (CONTRIBUTING.md).
- **Scope:** push only to this branch, and open no new pull request unless asked. Do not write exploit code for C1.

## 5. Conventions learned on the way (the traps)

- **RULE-CHANGE:** a change to the law's files (`seed/std-vocab.md`, `MODEL.md`, `MERGE.md`, `CHECKLIST.md`,
  `seed/RELEASE-SIGNERS`, …) is titled `RULE-CHANGE 25.0: …` and described in the 25.0 changelog entry.
- **CHANGELOG:** `test/layers.py` holds every entry the old law file carried, word for word. Only VERSION entries may be
  added, newest first, above the newest. A correction therefore goes into the open entry, never into an old one.
- **RATIONALE:** sections are `## <law path>`.
  - `dmwhy` resolves `[x]` to the first list item that has any field equal to `x`. So `[#3]` never resolves, and a
    value a sibling also holds can pick the wrong item.
  - A heading written twice replaces the earlier one, so append to an existing section instead.
  - `dmwhy.orphans()` must stay `[]`.
- **Story:** `bin/dmreview.py` `story_in` must stay at 0. `test/rationale.py` ratchets it against the last release tag.
- **FORMS:** `seed/FORMS.md` is derived from COOKBOOK by `bin/dmforms.py`, within a 16000-character budget.
- **Terminology:** `test/terminology.py` renders the page from HEAD, so commit before running it.
- **The site:**
  - The pages are templates. Output between `<!-- daftar:<type> id=… -->` markers is written by `site/build.py`, from
    the release that `site/RELEASE` names.
  - A new marker type needs `render()` in the build.
  - `test/site.py` rebuilds everything in a temporary directory (3–5 min) and needs the tags.
- **CI and timings:**
  - The suites in `.github/workflows/ci.yml` must be written `python3 test/<name>.py`. `test/timings.py` and
    `test/docs.py` read that pattern, and CONTRIBUTING.md lists the same suites one per line.
  - `test/timings.tsv` is keyed by the suite's path.
- **Licences:** `REUSE.toml` licenses root `*.md` files, but not `.md` files in a new directory. Run `reuse lint`
  (`pip install reuse`).

## 6. Running the suites on another machine

```
git fetch origin && git checkout claude/magical-feynman-lg8qm0 && git pull
git fetch --tags                      # test/site.py, test/upgrade.py and test/rationale.py read the release tags
git config user.name omid && git config user.email o.kord@live.com
pip install PyYAML reuse
python3 bin/dmsafe.py && python3 test/docs.py && python3 test/layers.py && python3 test/rationale.py
```

- **SSH paths:** the SSH cases of `test/hub.py` and `test/upgrade.py` need `ssh-keygen` from OpenSSH 8.2 or later.
  Without it they print SKIP.
- **Machine signing settings:** a global git config that signs through a program of its own (`gpg.ssh.program`, or
  `commit.gpgsign` with the machine's key) makes `test/hub.py` fail locally. The hub then sees the machine's key, not
  the test's. Run it with a clean config:
  `GIT_CONFIG_GLOBAL=<a file holding only [user] name and email> python3 test/hub.py`. CI is not affected.
  `test/upgrade.py` now names `gpg.ssh.program=ssh-keygen` itself.
- **Timing:** the long suites are peering (8 min on CI, much longer under load), upgrade (about 20 min),
  germinate (3–13 min) and site (3–5 min). About 8 suites can run side by side.

## 7. The verification record

- **At `7dfdba3`:** the full run passed 43 of 45 suites. The two failures were tests that expected the old merge and
  timeouts, and `586d2c0` fixed them.
- **At `1f0b6ba`:**
  - germinate 114/114, converge 56/56, and upgrade 178/178 (its SSH cases skipped: no `ssh-keygen` then).
  - rationale, terminology, docs, manifesto, layers, reform, senses, shape and positions all passed.
  - `reuse lint` was compliant.
  - CI: 38/39.
- **At `cfad75e`:**
  - upgrade 180/180, with the SSH cases, under two git configs;
  - `test/hub.py` 0 failed with a clean config;
  - `reuse lint` compliant.

## 8. The commits, oldest first

77bd737 hub · 15af8c0 release authentication · 9bdb4ad three-way driver · 3946872 unsealed refused · d784b36 test
encoding · 4b23d7e grants · 4289c4e view form · c9cd327 version order · 987265d group calendar · 3ceb312 drawing
module · 8571575 grant days · 3251f8f CI · 3255354 duplicate addresses · 4167439 atomic writes · 68cecd1 dmpublic ·
8faa5b0 dmrules · 1f3c740 distinct · a3ae0b1 merge facets · 566a964 registry rows · ee65ecd dmhook · 2eb879b gate ·
7695fbe quotes · f831c0c stamp register · ae295ce reckoner · 39ab8a2 dmheld · 8c9896a view doors · 412d0c2 site user
· 7dfdba3 law documents · 586d2c0 tests · 8259225 timings · e3f7818 changelog gap · c5cdc81 site markers ·
1f0b6ba story out of the law · cfad75e SSH test fix · then this handover.
