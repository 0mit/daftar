# daftar: a review of v0.38.0

> The review that branch `claude/magical-feynman-lg8qm0` (pull request 51) answers, as it was written before any
> fix. What became of each finding, and what is left, is in `HANDOVER.md`. Working material for that branch:
> whoever merges decides whether it stays.

Repository `0mit/daftar`, HEAD `5f55653` (the merge of PR #50), law `seed/std-vocab.md` version 24.0, site release `v0.38.0`.
Read on 2026-09-26/27. Nothing in the repository was changed.

---

## 1. What was read, and how

The files were read in dependency order: the orientation documents first, then the model documents, the law, the core code, the other tools, the `view` asset, the tests, the site, and last the metadata.

| Group | Files | Depth |
|---|---|---|
| Orientation | README, MANIFESTO, CHARTER, INSTALL, CONTRIBUTING, AGENTS, SKILL.md, seed/README, seed/WELCOME | Read in full |
| Model | MODEL.md, CHECKLIST.md, MERGE.md, HISTORY.md | Read in full |
| Law | seed/std-vocab.md (3,716 lines), RATIONALE.md (3,314), CHANGELOG.md, FORMS.md, COOKBOOK.md, knowledge/SOURCES.md and TSVs, germinate.py, templates | Read in full (TSVs checked for shape, not row by row) |
| Core code | dmparse, dmform, dmcheck (6,384 lines), dmrules, dmwhy, dmjournal, dmsave, dmsafe, dmcursor, dmpass, dmhook, install.py/.sh, hooks | Read in full |
| Other tools | dmreckon, dmmerge, dmpropose, dmheld, dmpublic, dmhub, dmforms | Read in full |
| | dmupgrade, dmlaunch, dmledger | Main paths read |
| | dmstale, dmseq, dmreview, dmcal, dmwhere, dmreform, dmcrosswalk, dmpos, dmgeo, dmknowledge, dmunits, dmfacets, dmdigest, dmacross, dmsession | Docstrings, structure and a scan for risky constructs; **bodies sampled** |
| `assets/view` | README, view_serve.py, the loaders in view_model.py, the escaping in view_runtime.js | Read in full |
| | dmview, view_kit, view_report, view_export, sources/*, templates | **Sampled** |
| Tests | 51 suites (19,586 lines), timings.tsv, weighing.yaml, gold/finder.tsv | Every docstring; hub, rehearsal, converge and fast in part; **the other bodies sampled** |
| Site | build.py, terminology.py, machinery/, pages, CSS, drawings | Docstrings and page text; **terminology.html (1.25 MB) sampled** |
| Metadata | .github (ci, pages, issue forms, PR template), REUSE.toml, NOTICE, LICENSE, LICENSES/*, .gitattributes, .gitignore, seed/LANGUAGE | Read in full; `LICENSES/*` compared byte for byte with `seed/LICENSE-*` (identical) |

Findings were confirmed by running code where that was cheap: the merge driver on three files, `dmmerge.subsumes`, `dmcal.from_day`, the view form's YAML builder, the layer map, and the test suites (§6).

---

## 2. What daftar is

daftar is a **language for a ledger that agents and people keep together in git**.

- **Garden and beans.** A *garden* is a git repository. Each managed thing is a *bean*: one Markdown file whose YAML front matter holds the facts.
- **Provenance.** Every fact says who said it and how they know: `observed`, `inferred`, `stated-in-document`, `asserted-by-human` or `generated-by-tool`.
- **The gate.** The law is data (`seed/std-vocab.md`, overlaid by the garden's `VOCAB.md`). A pre-commit *gate*, `bin/dmcheck.py`, refuses any commit that breaks it.
- **The journal.** Every change is journalled in the same commit, under a heading that only `bin/dmjournal.py` may write, read from the clock.

Around that core:

- **An ontology.** Every bean has a *nature* (`soma`, `lekton`, `empsychon`) refined by a *genos*. Ownership chains end at a *crown*. Ownership and responsibility are paired per facet. Identity rests on *anchors*.
- **Contract of Parts.** This decides what an agent may enact and what a person must ratify. Identity (F), safety (E) and the law (G) are always a person's.
- **A schema language.** Attributes, domains and figures (squares of opposition, sequences), exact quantities and money, calendars and places, series, courses, agreements, observations, and readings in a closed grammar of operations.
- **Privacy.** Sensitivity is derived from what a bean holds. Material can be sealed off git. People are kept by name only with their consent. Grants are closed by default.
- **Peering.** Gardens meet only by *proposal* files. A merge algebra (a lattice join keyed on anchors) combines what they say.
- **Surrounding tools.** A hub that re-judges signed pushes; a `view` asset that serves drawings with live values; a site generated from what the tools print.

It is ambitious and unusually rigorous. The engineering culture shows everywhere:

- Every rule has a written reason (RATIONALE, keyed by the path of the rule).
- Every refusal says what to write instead.
- Every number is exact.
- Most defects the project met are written down where the next reader will find them.

---

## 3. Architecture in one page

- **Law.** `seed/std-vocab.md` holds 108 terms, 16 gene, about 50 anchor systems (22 of them calendars), units with exact rational factors, about 40 operations, about 35 flow rows, 17 layers and 5 profiles. A garden's `VOCAB.md` overlays it. Profiles are `code`, `network`, `domain`, `knowledge` and `view`.
- **Gate.** `dmcheck.py` runs about 75 checks ("plies") in a declared order. It judges the staged index, not the working tree. Its commit-time half checks:
  - the journal names each bean it changes;
  - a change to the law says RULE-CHANGE;
  - journal headings are registered, and `as_of` equals the heading's day;
  - series parts are written once;
  - no private keys, no gutted subtrees, no removed keys left unsaid.

  The *reverse gate* holds every declared position to being either occupied or vacant with a reason.
- **One reader per question.** `dmparse` reads documents (integers in plain decimal only, duplicate keys refused), `dmform` reads attributes, `dmpass` reads layers, flows, origins, sensitivity and `may`, `dmreckon` does all arithmetic, `dmseq` reads series and `dmcal` reads calendars.
- **Writes.** `dmsave` = journal, stage, commit. `dmsafe` makes measured edits and checks what an edit removed. `dmheld` keeps sealed material off git.
- **Between gardens.** `dmpropose` handles proposals (make, read, take, mint). `dmmerge` merges gardens and is also the per-bean git merge driver. `dmacross` reads another garden's published commit.
- **Around the garden.** `dmhub` is a pre-receive hook: signed commits, the writer's grants, then the gate. `dmlaunch` is daftar's own agent loop, with every piece of a request logged as a pass before it is sent. `dmhook` puts advisory guards into another agent harness. `assets/view` serves drawings, actions and entry forms, closed by default.

---

## 4. Strengths

1. **Refuse rather than guess.** This holds throughout:
   - calendars that are not reckoned by rule are refused;
   - datum transformations without PROJ are refused;
   - a reading outside a mechanism's fitted range is refused;
   - a merge across two different pins is refused;
   - a proposal that crashes the scratch gate is refused.
2. **Exactness.**
   - Money and quantities are `Fraction`s. `dmledger` holds no float, no rounding and no division operator, and `test/money.py` reads its source to enforce that.
   - An uncertain value is carried as u, combined GUM-style. A difference inside the band its uncertainty cannot resolve is reported as NOT KNOWN.
3. **Defensive handling of untrusted input.**
   - `dmpropose` refuses YAML aliases and deep nesting.
   - It escapes terminal control characters, and refuses line separators that could forge journal lines.
   - It lays files outside every garden with `open(..., 'x')` (so no symlink is followed), and edits the stamped copy only through surgery that is verified by re-parsing.
   - `dmparse` refuses duplicate keys and odd integer forms. The site pages run under a strict CSP with no script.
4. **Determinism.** The gate is independent of the clock. A merge produces canonical JSON and a SHA-256 fingerprint. The site is built under a held clock.
5. **Tests.** 51 suites grow real gardens with real hooks and check both directions (accepts and refuses), always with invented fixtures (XTS money, neutral names).
6. **Documentation and self-honesty.** Nearly every design decision is recorded with the incident that motivated it. The project lists what is "designed, not built".
7. **Cross-platform care.** It handles Windows code pages, CRLF in hooks, the Microsoft Store Python alias and PowerShell 5.1.

---

## 5. Findings, most severe first

Each finding says how it was established:
- **[run]**: reproduced by running code;
- **[read]**: confirmed by reading code and data;
- **[doc]**: a documentation inconsistency.

### Critical

**C1. The hub runs the pushed commit's own gate, and a non-gardener writer may change `bin/` with no grant.** [read]
`bin/dmhub.py` does two things that combine badly:
- `gate()` runs `<checkout of the pushed commit>/bin/dmcheck.py --all` (`dmhub.py:187`) and accepts on exit 0 plus " 0 error(s)" in its output. That is the pushed tree's code, run with the hub's interpreter.
- `rights()` (`dmhub.py:143-170`) asks for a grant only for the `law`/`manifesto` layers (`ratify:G`) and for `beans/` and `mappings/` (`write`, plus `ratify:F` for anchors). I checked the layer map: `bin/*.py` and `bin/hooks/*` are in layer `gate`, kept by the release, and need nothing.

So any registered writer can push a commit that replaces `bin/dmcheck.py` with a script that prints a passing verdict. The hub then:
- runs it, which is **arbitrary code execution as the hub user**;
- accepts the push, which **bypasses every grant the real gate would have enforced**;
- lets every clone then run that code from its own hooks.

The same freedom covers `.gitattributes` (merge dispatch), `assets/*`, `test/*`, `log/*`, `captures/*`, `series/*` and the view page's drawing module, which the `view` server executes (see M4).
`test/hub.py` never has a writer change `bin/`.
*Fix:*
- The hub runs its **own** trusted gate over the pushed tree, never pushed code.
- It requires the gardener (or `ratify:G`) for every file `keeper_of(...) == 'release'`, for the `gate` layer and for `.gitattributes`.
- Add that case to `test/hub.py`.

### High

**H1. `dmupgrade` runs code fetched from the network with no authentication of the release.** [read]
- `main()` shallow-clones `--branch <tag>` from GitHub or `--from <url>` (`dmupgrade.py:2014`).
- It then **executes the release's own `bin/dmupgrade.py`** (`:2017-2034`).
- It then runs `bin/install.py`, which copies the new hooks into `.git/hooks`.

All of this happens before anyone reads `git diff`. There is no `git verify-tag` and no pinned commit hash. The sha is only recorded in the journal afterwards. A moved tag, a compromised account or a hostile `--from` is code execution in every garden that upgrades.
*Fix:* signed tags plus `git verify-tag` (or a steward-signed manifest of tag → sha). Print the sha and ask for confirmation before delegating to the fetched tool.

**H2. The git merge driver ignores the common ancestor.** [run]
- `dmmerge.py --file %O %A %B` reads `_O` and never uses it (`dmmerge.py:1747`). The result is a two-way lattice join, not a three-way merge.
- Reproduced in a scratch directory. Base: `status: active`, plus `roles`. Ours: the base, unchanged. Theirs: `status: retired`, and `roles` removed.
- Result:
  - `status: {conflict: [active, retired]}` with `merge_open: true`. A clean one-sided edit became a matter for a person.
  - `roles` came back **silently**, with no conflict mark. Theirs' journalled removal was undone.
  - The gate's removed-key check compares against HEAD (ours), so the merge commit passes.

This contradicts MERGE.md invariant 1 ("a value is corrected only by a recorded, attributed change"). The lattice join is right for merging different gardens, which share no base. It is wrong for merging branches of one garden.
*Fix:* read `%O`. Take a change or removal made on one side only. Record a conflict only where both sides changed a position differently. Test the driver against a base.

**H3. Special-category data is only warned about, and sealing happens after the plain value may already be committed.** [read]
- `check_sensitivity` (`dmcheck.py:3322-3325`) *warns* when special-category material is in git unsealed.
- `dmheld put` rewrites the working-tree bean afterwards.
- `test/rehearsal.py:162-167` shows the gate passing with plain readings in the bean. The suite's "no special value in any blob" property holds only because the test seals before its first save.
- Erasure deletes only the store files. No tool or document deals with a plain value already in history, in clones, in `captures/proposals/*` or on a hub.

MODEL.md says "what harm can come of, git does not keep". That is true only if the writer never slips.
*Fix:*
- *Refuse* a commit that **adds** unsealed special-category material, as `check_persons` already refuses an added person who has not consented.
- Let `put` act on a new or staged entry.
- Document how to purge history (`git filter-repo`) and how to reach every clone.

**H4. Any `contract` bean may grant access to any bean.** [read]
- `dmpass.may` treats every bean of `genos: contract` as a holder that may decide grants (`dmpass.py:1151`), and honours whatever its `over` selection selects.
- The law's own meaning is narrower: "an agreement's on its bean for what it shares".
- `check_grants` restricts only `ratify:`.

So whoever can add or edit a contract bean can open `read` (or `write`, or `act:<tool>`) on a person's bean or a special-category bean to any audience. In a single-writer garden that is any committer; under a hub it is a writer granted `write` on some contract. `view_serve.Host.may` and `dmhub.rights` both rely on `dmpass.may`.
*Fix:* restrict a contract holder's `over` to itself and to the beans it names as parties or shares, and check that in `check_grants`.

### Medium

**M1. YAML injection in the served entry form.** [run]
- `view_serve.Host.write` builds `{ attr: <value>, … }` by string formatting with the viewer's raw values (`view_serve.py:424`). Only newlines are refused.
- The value `hello, by: someone-else, when: 2026-01-01, flag: yes` parsed as four attributes, with a date and a boolean.
- So a viewer with `write` can set attributes the form does not offer, and coerce types. The gate still refuses attributes the term does not declare, but accepts any it does.

*Fix:* quote every value with `json.dumps`, as `dmpropose._q` does, and assert after parsing that exactly the offered keys are present.

**M2. The `version` merge order treats any string prefix as a refinement.** [run]
- `subsumes` uses `str(b).startswith(str(a))` (`dmmerge.py:830`).
- `'9'⊑'90'`, `'1.2'⊑'1.23'` and `'v1'⊑'v10'` are all True. A real disagreement between two versions is silently absorbed into the longer string. It is kept only in `provenance_of`, not shown to a person.

*Fix:* require the prefix to end at a component boundary (the next character one of `.-_ +`), or compare parsed components. Add the case to `test/converge.py`.

**M3. For `group` readings, the law, the reckoner and the cookbook disagree on how a calendar is named.** [run]
- The law's `operations.group.system` is a row of `anchor_systems`: `gregorian-civil`, `persian-calendar`, and so on.
- `dmreckon._takes_check` never validates a registry domain (`dmreckon.py:419-446`).
- The COOKBOOK's `system: gregory` (`COOKBOOK.md:885`) is a CLDR identifier, not a law row. It passes, and works.
- `_cell` hands the value straight to `dmcal.from_day`, which knows CLDR ids and special-cases only `gregorian-civil`.
- `from_day(…, 'persian-calendar')` raises "no calendar 'persian-calendar'".

So whoever follows the law is refused for every non-Gregorian calendar; whoever follows the cookbook writes a value the law does not hold.
*Fix:* validate registry domains, map a system row to its `calendar:` in `_cell`, and correct the COOKBOOK.

**M4. Writing a garden's files is executing code on its `view` host.** [read]
- The page's drawing module and the monitor adapters are loaded with `exec_module` (`view_model.py:397-399, 436-438`).
- The server re-executes itself on a new HEAD once `dmview check` passes, and that check itself imports the module.
- `drawings_path` joins the `file:` pointer with no containment check.

Combined with C1, a writer's pushed drawing module runs on the view host.
*Fix:* state this trust boundary, reserve changes to `view.drawings` for the gardener, and contain the path.

**M5. The served page caches grant answers without regard to time.** [read]
- `Host.may` caches `dmpass.may` answers (`view_serve.py:157-163`) and clears them only when HEAD moves (`:211`).
- A grant whose `during` has ended therefore keeps granting reads, actions and writes until someone commits.

*Fix:* add the day to the cache key, or expire the cache daily.

**M6. CI on push and pull request does not run the behavioural suites.** [read]
- `ci.yml` runs only a brief set on push and PR: dmsafe, assets, journal, dmreview --law, site, terminology, public, docs, manifesto, `reuse lint`, sign-off.
- Everything else runs only by hand (`workflow_dispatch`): germinate, refusals, save, stamps, converge, upgrade, peering, privacy, held, passes, launch, hub, view, money, reckon, agreements and the rest.
- With 24 law versions in eight weeks, many of them MAJOR, this is the largest regression risk.

*Fix:* run the full list on PRs, in parallel jobs (`test/timings.py -j`), or at least nightly.

**M7. The duplicate-IP escape hatch cannot be used.** [read]
- `check_duplicate_authoritative_ip` honours top-level `shared_identifiers`, `scope` and `network`, and its error message recommends them (`dmcheck.py:5368-5381`). The `ip` term's `escape` says the same.
- None of the three is a declared term, so `check_undeclared_keys` refuses any bean that writes one.

*Fix:* declare them (a RULE-CHANGE), or change the advice.

**M8. `dmsafe.edit` writes before it verifies, and not atomically.** [read]
- `dmsafe.py:427` truncates and writes the new text, then parses it, then writes the original back on failure.
- A crash or kill in between leaves a broken or lossy bean. `dmupgrade.write_text` already does this correctly: temp file, then `os.replace`.

*Fix:* verify in memory, then write through a temporary file and `os.replace`. The same applies to `dmheld._write` and to the writes in `take` and `put_back`.

**M9. The leak guard `dmpublic` misses more than it appears to.** [read]
- Names shorter than 4 characters are never guarded (`nas`, `vps`, `ali`).
- It collects only ids and anchor values. A title, a summary, a non-anchor IP or a contact address is not collected.
- The public-word allowance takes **every** token of 4 characters or more from ISCO, ISCED and technology.tsv, which is thousands of common English words. A host called `nurse`, `baker` or `manager` is silently unguarded.
- Paths with spaces are skipped.
- It protects only where the developer has set `git config daftar.garden`.

**M10. Licensing of ISCO-08.** [read]
- `seed/knowledge/*` is in `seed/LANGUAGE`, so every garden redistributes `isco-08.tsv`, including any garden pushed to a public host.
- The ILO's pre-2023 works carry no open licence. The project's own LicenseRef "grants no right in it", and NOTICE says permission was asked on 2026-09-19.

*Fix:* until the ILO answers, ship the codes without the titles, or fetch the table at germination behind an explicit acknowledgement.

### Low: code

- `dmrules` merges an overlaid term's schema shallowly (`{**base.schema, **overlay.schema}`, `dmrules.py:88-90`), so an overlay's `attrs` replace the base's wholesale. `dmcheck._overlay` merges attribute by attribute. `dmrules` can therefore misreport an overlaid term.
- `dmpass.trace` returns a `words` verdict on any quoted match, even a short or common one. The `distinctive` test is applied only to refusals, so attribution to a person's words is weak for small numbers and short words.
- `dmmerge.facet()` reads the shape of `items[0]` for any member with no declared merge facet, and every member of a `multi` term is such a member. Such a member merges by whichever garden arrived first, which breaks order-agnosticism in that corner. `dmfacets` documents this.
- Some tools read only the standard law, so a garden that restates a registry in `VOCAB.md` is read two ways:
  - `dmmerge` reads `LEAF_ORDERS`, `SYSTEM_ROWS` and `TIME_SYSTEMS` from `std-vocab` only;
  - `dmpass.Origins` reads `natures` from the law only;
  - the gate reads the restated rows.
- `dmhook` writes its hook command without quotes, `f'{sys.executable} {me} {verb}'`, which breaks on paths with spaces. `install.py` does quote its paths.
- `dmhook`'s guards are advisory, and say so: `'dmsave.py' not in cmd` is a substring test, and `NO_VERIFY` does not catch `git commit -n`.
- `dmcheck`:
  - the at-authority check uses `re.fullmatch` without `re.ASCII`, against the rule that every pattern is matched through `law_match`;
  - git reads time out after 5 s (`:83, :5621, :5634`), which can become a refusal on a large or slow garden;
  - the RULE-CHANGE duty is a substring test, so "not a RULE-CHANGE" satisfies it (`:5773`).
- `dmparse.comment_start` ignores backslash-escaped quotes in double-quoted scalars. `dmsafe.flow_spans` treats escapes differently from `dmcheck._flow_pairs`.
- `dmjournal`'s stamp register grows without bound, and any process can append to it (the guard is on trust).
- `dmreckon`:
  - a `where` comparison between different quantities silently excludes the member; only `min`, `max` and `order` refuse;
  - uncertainties combine in quadrature, assuming independence, and the output does not say so;
  - `used_within` windows by year or month are Gregorian only;
  - `order` over text values raises `TypeError`, and `used()` raises `KeyError` on a clause without `used_by`.
- `dmheld` stores are plaintext YAML, relying on host file permissions, which is not stated.
- `view_serve`:
  - a negative `Content-Length` blocks a thread;
  - the login throttle is per-IP sleep, with an unbounded dictionary and no lockout;
  - the cookie lacks `Secure`;
  - logout does not revoke a token, so a stolen one lives 12 hours.
- `dmhub.Tree.checkout` uses `shell=True`. The inputs are a sha and a temporary path, so the risk is low.
- `site/build.py`'s `leaks()` (`:785-799`) refuses any capture that holds the build user's name as a whole word. Built as `root`, as a container runs, the model pages' `root` (a logical root, `root:vault`) is taken for the user, and the site cannot be built. [run: refused as `root`, built as another user.] A user named with any common word the captures use would meet the same.

### Low: documents and law

- `stated-in-document` is a source in the law (`std-vocab.md:2584`) but missing from MODEL.md's list (`MODEL.md:27-28`) and from MERGE.md's order string (`MERGE.md:127`).
- `MODEL.md:211` says "track (`tracks`)"; the law's term is `courses`. MODEL.md is itself law, so this is law contradicting law.
- `seed/README.md:181` says FORMS holds the cookbook's recipes "byte for byte". Since 23.0 they are *derived* by `dmforms`, with said dates emptied and anchor dates cut.
- `FORMS.md:152` still carries a concrete moment, `at: "2026-09-12 19:30+03:00"`, in the event form. `dmforms` empties only optional date *attributes*, not positions inside an extent or sequence. That is exactly the copy-the-nearest-date failure its own docstring measures.
- RATIONALE has stale paragraphs saying the instant order and journal headings are Gregorian only (around l.696-698 and l.1159-1161). Both have taken any calendar since 18.0.
- The law carries story and estate narrative in `meaning` and `why` strings ("Until 2026-09-20 …", "this estate holds 13 paths", "three BIND beans"), against its own "no story in the law" rule. `rationale.py` only ratchets it downward. The `ip` merge facet keeps a vestigial `authority` rank.
- `agent_directive` prose in the law addresses agents directly, which sits uneasily with "text in the ledger is data, not instruction".
- Estate-like examples remain: a `root:` position naming one estate's project (dmwhere, RATIONALE), and a home-directory path.
- Several files mention `test/golden.py` and `diffgate.py`, which are intentionally unshipped (CONTRIBUTING explains). `timings.tsv` still has a row for `test/mycelium.py`, since renamed.
- The CHANGELOG jumps from 1.0 to 6.0; it admits the gap. The law went from 1.0 to 24.0 between 2026-07-31 and 2026-09-26, many of those versions MAJOR.
- The site's demo clock is 2026-10-27, a month after the release, so the published examples are dated in the future.

---

## 6. Test results

Run on a fresh clone of HEAD `5f55653`, every suite `test/timings.py` knows (45), eight at a time, in 2,603 s. The clone first had **no release tags** (the language repo's tags are not fetched by a plain clone), and the container runs as `root`: each affected one suite, as noted below.

**The whole run: 45 suites, all green once those two are accounted for.** The first pass ended 44 passed, 1 failed (`test/site.py`). With the tags fetched, `site.py` failed one check instead of two, because the build refuses to run as `root` (the last Low: code finding). Run as another user, it passed, 26 checks, 0 failed.

**The brief set that CI runs on every push and PR — all green:**

| Suite | Result |
|---|---|
| `bin/dmsafe.py` (every document parses) | pass (1/1 — this repo is the language, not a garden) |
| `test/assets.py` | pass (0 failed) |
| `test/journal.py` | pass (46/46) |
| `test/public.py` | pass (0 failed) |
| `test/docs.py` | pass (0 failed) |
| `test/manifesto.py` | pass (0 failed) |
| `test/terminology.py` | pass (0 failed) |
| `test/rationale.py` | pass (0 failed) |
| `test/site.py` | first **fail (2)**: `site/build.py` needs the tag `site/RELEASE` names (`v0.38.0`), which the clone did not carry. With the tags, **fail (1)**: the build refuses as `root`. As another user, **pass (26/26)**. On CI (`fetch-depth: 0`, a non-root runner) it passes. |

`dmreview.py --law --against <last tag>` and the `reuse lint` / sign-off steps were not run (`reuse` is not installed here).

**The behavioural suites, which CI does not run on a PR (finding M6), all pass.** The longest:

| Suite | Result | Time |
|---|---|---|
| `test/peering.py` | 173/173 | 2,602 s |
| `test/upgrade.py` | 166/166 | 1,223 s |
| `test/germinate.py` | 114/114 | 782 s |
| `test/refusals.py` | 0 failed | 743 s |
| `test/sequence.py` | 87 passed, 0 failed | 438 s |
| `test/converge.py` | 50/50 | 239 s |
| `test/passes.py` | 73/73 | 153 s |
| `test/launch.py` | 39/39 | 102 s |
| `test/save.py` | 38/38 | 177 s |
| `test/stamps.py` | 27/27 | 223 s |
| `test/rehearsal.py` | 0 failed | 69 s |

The rest, 0 failed each: agreements, view, expiry, viewcap, money, calendars, privacy, layers, positions, held, observations, deeptime, reckon, base, figures, reform, shape, uncertainty, place, recurrence, zones, crosswalk, senses, quantities, knowledge.

One suite passed only in part here: `test/hub.py` passed with its SSH-signature check **skipped**, because this machine's `ssh-keygen` cannot check a signature (`-Y check-novalidate`). Only its OpenPGP path ran.

---

## 7. Recommendations, in order

1. **Close C1 now** if any garden runs a hub with more than one writer. The hub runs its own gate; release-kept files, the `gate` layer and `.gitattributes` need the gardener.
2. **Authenticate releases (H1):** signed tags and `git verify-tag`, and confirm before running a fetched tool.
3. **Make the merge driver three-way (H2)**, with a test of a change and a removal made on one side only.
4. **Enforce the privacy promise at the gate (H3):** refuse an added unsealed special-category value.
5. **Scope contract grants (H4)** in `may` and in `check_grants`.
6. **Quote the form values (M1)**, and put time in the grant cache key (M5).
7. **Run the full test list on PRs (M6).** Add the missing cases: a hub writer changing `bin/`, the version boundary, the driver against a base, non-Gregorian `group`.
8. **Fix the version order (M2)** and the calendar-system mapping (M3), including COOKBOOK:885.
9. **Write atomically (M8)** wherever a bean or store file is written.
10. **Resolve ISCO-08 (M10)** before more gardens are grown.
11. **Clean the document drift** in §5, and slow the law's MAJOR releases until the suites run on every PR.

---

## 8. Overall judgment

The design is coherent, careful and far more thoroughly reasoned than most projects of its size. Its core promises largely hold as built: the gate is deterministic and explains its refusals, provenance is ranked, arithmetic is exact, and peering is data-only with loop detection.

The weak points sit at the **trust boundaries added in 24.0 and at the edges of the core**:
- the hub trusts pushed code;
- the upgrade trusts a tag;
- the view server trusts form text and a cached answer;
- a contract is trusted to grant anything;
- the branch merge driver ignores the base it is given.

None of these needs a redesign; each has a local fix. The biggest process risk is that the suites which would catch regressions like these run only when someone starts them by hand.
