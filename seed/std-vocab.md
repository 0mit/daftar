---
version: "11.2"
# TIER-0 UNIVERSAL STANDARD VOCABULARY — portable, estate-agnostic classification carried BY THE SKILL.
# Gardens pin a version via `extends: std-vocab@<version>` (VOCAB.md / GARDEN.md) — the `version:` key two
# lines above is the one that governs, and the gate ERRORS if a pin disagrees with it.
# Changes are governed by the PROMOTION PROTOCOL (SKILL.md): human-ratified rule-changes, semver —
# additive term = MINOR bump; changed handling/merge/anchor rule = MAJOR (can retroactively re-classify).
# Each term declares: meaning · context_keys · anchor{class,establishing} · merge{cardinality,order,authority}
# · canonical (normalizer) · escape · exceptions(dated case-law).
# == THE SCHEMA LANGUAGE (added 2026-08-02, P2 / plan D4, human-ratified rule-change) ==
# INVARIANT SERVED: "type rules live in the VOCAB, not in code." bin/dmcheck.py is now a fixed CORE
# (front-matter shape, id==filename, kebab, provenance, anchors + establishing dedup, ip dedup, DAG,
# link integrity, journal<->commit binding) plus ONE generic loop that enforces every term from the
# `schema:` block below. There are NO per-term blocks in the gate. To change a type rule, edit the
# schema here — that is a human-ratified rule-change — and the gate follows without a code edit.
# A term with no `schema:` is documentation only; the gate never enforces it on beans.
schema_language:
  shape:                "scalar | mapping | list_of_entries | open_map_of_entries — the term's on-bean form"
  required:             "true — EVERY bean must carry the term (the root-axiom case; stronger than required_on_<axis>s)"
  required_on_kinds:    "[<kind>...] — a bean of this kind MUST carry the term, non-empty"
  must_equal_kind_attr: "<attr> — the term's value must equal the bean's kind's <attr> in the `kinds` registry (e.g. nature == kind.of_nature)"
  required_on_natures:  "[<nature>...] — same, keyed on nature instead of kind (reserved for P3; the interpreter already honours it)"
  required_on_roles:    "[<role>...] — same, keyed on ROLE. It needed no new interpreter key: the axis has always been read from the vocabulary key rather than named in code. What it DID need (7.0, human-ratified) is that an axis may be MULTI-VALUED — a machine holds one kind and one nature but SEVERAL roles — so the mechanism now reads an axis carried as a scalar, as a list of scalars, or as a list of entries each naming it, and fires if ANY held value matches. That generality is the reason `router` could stop being a kind."
  values:               "[<enum>...] — shape:scalar, the allowed values; also the enum this term EXPORTS to values_from/key_form"
  values_from:          "<term> — reuse another term's `values` list instead of restating it (one owner of an enum)"
  values_consistent_with: "[<path>...] — paths whose contents must equal `values` (drift guard). A path is `attr` or `attr[].sub` inside the term, or `registry:<name>[].<sub>` for a top-level VOCAB registry."
  key_form:             "kebab | values | values_from:<term> — the rule the KEYS of a mapping/open_map must satisfy"
  required_attrs:       "[<attr>...] — shape:mapping, attrs the mapping itself must carry"
  entry_required_attrs: "[<attr>...] — attrs EVERY entry needs (a list item, or an open_map value)"
  entry_values:         "{<attr>: [<enum>...]} — per-entry enums"
  entry_pattern:        "{<attr>: <regex>} — an entry attr must match this form (11.0). For a POSITION, prefer `entry_pattern_from_registry`, which lets the system own its one form; this is for a value whose form is the term's own business"
  entry_soft_pattern:   "{<attr>: {pattern, why}} — the same, as a WARNING (11.0): the form a value SHOULD take while a corpus is being migrated onto it, so a garden is told what to fix without its next commit being refused"
  entry_types:          "{<attr>: <value type>} — per-entry value types, each a row of `value_types` (10.0): its pattern, and for a time type its system and unit"
  entry_one_of:         "[<attr>...] — each entry must carry at least one of these"
  entry_required_if:    "[{attr, equals, requires: [...]}] — conditional requirement inside an entry"
  entry_expect_if:      "[{attr, starts_with, expects, why}] — a soft expectation; failing it WARNS, never blocks"
  attr_extents:         "[<attr>...] — these attrs of the mapping hold an EXTENT (`extent_form`): a bounded region of some aspect's domain. The gate checks the region against the aspect it names — that the figure permits a region at all, that a measure appears only on a metered aspect and in that aspect's own dimension, and that a position is in one of the aspect's domain systems' canonical forms."
  entry_extents:        "[<attr>...] — the same, inside each entry of a list or open map"
  expiry:               "{attr, notice, why} — ONE of this term's attrs is the position at which the thing LAPSES if nothing is done, and a reader should be warned before it. `notice` is HOW LONG BEFORE, as an EXTENT on `time` (11.2; it was a bare `horizon_days` integer for one release, which was a fifth way of saying a duration in a vocabulary that had just declared the first). `why` is the CONSEQUENCE, printed with the warning, because a date alone does not say what is lost. Read by bin/dmstale.py, not by the gate: a check whose answer changes with the calendar would make the gate non-deterministic, and a gate that fails on a Tuesday for no committed reason is a gate people disable. Deliberately NOT derivable from `attr_types: iso_date` — ten terms carry an iso_date and nine of them are `observed` or `as_of`, the date a fact was READ rather than the date it runs out. A term that does not declare this is never warned about, which is why a garden's own term can buy the warning its Tier-0 neighbour has."
  ref_fields:           "[self|<attr>...] — sub-nodes that are {bean|mapping} refs; the gate RESOLVES them (dangling = error)"
  entry_ref_fields:     "[<attr>...] — same, but inside each entry"
  pointer_fields:       "{<attr>: bean_field_pointer} — a pointer that is '<section>.<key>' on this bean, {bean,field} on another, or 'file:<path>'"
  on_sequence:          "<aspect> — the term's value is a walk on that SEQUENCE aspect (10.1): prose lines in list order, or step entries {id, do, next: [{to, when?}]} whose neighbourhoods are CLOSED; the gate refuses a `to` that names no step, a step nothing reaches, a branch with no condition, a routine with no end, and a loop when the aspect declares acyclic"
  dag:                  "true — this term's edges are positions on the `walk` sequence aspect (9.2: `dag` is that aspect's `term_key`), and they join the acyclic check BECAUSE that aspect declares `acyclic: true`"
  required_on_targets_of: "<term> — a bean that is the TARGET of that relation must carry this term (e.g. anything lived in must say what kind of habitat it is)"
  entry_must_match:     "[{attr, registry, keyed_by, take}] — an entry attr must equal a registry row's attr, the row selected by a field on the bean (e.g. the crown branch is fixed by the bean's nature)"
  entry_in_registry:    "{<attr>: {registry, take}} — an entry attr's value must be a ROW of that registry, so the registry OWNS that enum and no term restates it"
  entry_pattern_from_registry: "{attr, registry, keyed_by, take} — an entry attr must match the PATTERN its own system declares, so a system owns its one format and nothing spells a position a second way. `keyed_by` selects the row by a field of the ENTRY (which system is this position in), where entry_must_match selects by a field of the BEAN. A row declaring `pattern: none` has DELIBERATELY no canonical form and is honoured rather than skipped by accident."
  entry_form_from_kind_attr: "<attr> — if the bean's kind declares this attr, every entry must use the form it names, AND that form is RESERVED to kinds that name it. Pinning both requires and reserves, so no other bean can short-circuit its chain to the axiom (e.g. only kind:person may use `crown`)."
  governs_anchor:       "<key> — this term governs the FORMAT of anchors carrying that key; pairs with value_pattern or value_form"
  value_pattern:        "<regex> — the canonical form an anchor value must match (with canonical_note as the human statement of it)"
  value_form:           "ip — a format needing real parsing rather than a pattern"
  enforced_by:          "core | none — an explicit statement for a term with NO schema: either CORE already enforces it, or there is genuinely nothing to check and this says why"
  cross_aspect:         "{incoherent: [...], in_breach: [...]} — combinations over ONE OR MORE of a term's aspects; N-ary, so the same construct constrains a single figure or a grid of any dimension. Incoherent = error (a position must be mis-stated); in_breach = warning (all can hold, and the state needs action)."
  poles:                "one axis (a contradictory PAIR), or a LIST of axes — a figure may be 1-dimensional, 2, 3 or more, and the gate derives the count rather than assuming it"
  on_aspect:            "{aspect, attr, default} OR a LIST of them — a term's entries may take positions on SEVERAL aspects at once (e.g. what is allowed AND what is possible) — every entry of this term takes a POSITION on that aspect; an entry may name its own via an attr called after the aspect, else the default applies"
  facet_parity_with:    "<term> — this term and that one must carry the SAME facet keys (two arcs of one loop); one present without the other is a loose end"
  values_add:           "[<value>...] — GARDEN overlay only: APPEND values to a Tier-0 term's enum instead of replacing it, so the garden accounts only for what it added (8.2)"
  compare_form:         "upper-trim — with governs_anchor: the anchor is compared in this form for uniqueness (whitespace removed, uppercased), and a stored value not already in it warns (9.0)"
  value_in_registry:    "{registry, take} — with governs_anchor: the anchor value must be a ROW of that registry (a code of a published classification, 9.1)"
  registry_from:        "<attr> — inside entry_in_registry: the registry is NAMED by another field of the same entry, so one term can check a code against whichever scheme the entry says it is in (9.1)"
  inverse_of:           "<term>, or {term, cardinality: one-to-one | many-to-one} — this relation mirrors another and the gate holds the pair consistent so the convenience edge cannot drift from the fact. A BARE NAME means one-to-one and the mirror is enforced BOTH ways. `many-to-one` enforces only the functional direction: many instances point at one type, and the type cannot point back at all of them through a single mapping. Declare the cardinality; assuming a bijection is how a rule becomes unsatisfiable without anyone noticing."
# == NATURES: the root axiom layer (added 2026-08-02, P3 / plan D1, human-ratified rule-change) ==
# `nature` is the ROOT of the type system and `kind` is a REFINEMENT of it, not a parallel taxonomy.
# Every bean carries a nature; every kind below declares the `of_nature` it refines; the gate holds the
# two equal. Policy that used to be stated per kind (anchor family, minimum anchors) attaches HERE, so a
# new kind inherits a coherent identity policy for free and may override only if it truly differs.
# The crown itself is a MODEL axiom (MODEL.md Ownership), never instantiated as beans.
# == THE CROWN (added 2026-08-02, P7b, human-ratified) ==
# MODEL §Ownership states the axiom in prose; this makes it NAMEABLE in data without instantiating it as
# beans. These are the TERMINI every ownership chain resolves to. A bean names its branch directly only
# where ownership does not pass through another being — in practice, persons. Everything else chains up
# through a person or an org and terminates here transitively.
# The branch a bean may name is fixed by its nature (natures[].crown owns that mapping — not restated here).
crown:
  - branch: god
    root: true
    meaning: "the one substance, Deus sive Natura — every chain terminates here. NOT nameable on a bean: you reach god only through your branch."
  - branch: nature
    meaning: "Extension, res extensa — the terminus for physical beings"
  - branch: logos
    meaning: "Thought, res cogitans — the terminus for metaphysical beings"
  - branch: love
    meaning: "the conatus — the terminus for LIVING beings, while alive; life-bounded, lapses at death or teardown. This branch is what makes a person UNOWNABLE BY ANOTHER BEING: no bean may hold a person, only love, and only while they live. That is a protection, not a formality — the gate enforces it via person.ownership_form."
  # NB the crown OWNS but never ANSWERS. Responsibility has no crown form: a duty must land on a being
  # that can be asked, so responsibility always terminates in a bean (or, for a person, in themselves).
identity_policy:                                 # P3/D1: identity policy attaches to the ROOT AXIS...
  keyed_by: nature                               # ...this bean field selects the policy row...
  registry: natures                              # ...from this registry...
  applies_at_identity_status: confirmed          # ...and the minimum bites once identity is confirmed.
natures:
  - nature: physical
    meaning: "res extensa — a being with extension in space: machines, hardware, sites"
    crown: nature                                  # Extension owns physical beings
    establishing_anchor_family: [hardware]         # serial / mac / wg_pubkey — bound to the matter itself
    min_establishing_anchors: 1                    # required once identity.status is `confirmed`
  - nature: metaphysical
    meaning: "res cogitans — a being constituted by meaning or agreement: code, products, orgs, domains, designs, contracts"
    crown: logos                                   # Thought owns metaphysical beings
    establishing_anchor_family: [logical]          # url / fqdn / git remote / manifest or doc id
    min_establishing_anchors: 1
  - nature: living
    meaning: "conatus — a being that strives to persist as itself: persons, and running instances while alive"
    crown: love                                    # life-bounded ownership; lapses at teardown
    establishing_anchor_family: [logical, personal]
    min_establishing_anchors: 1
# == ANCHOR SYSTEMS: the systems a POSITION may be stated in (added 5.1, human-ratified rule-change) ==
# A POSITION IS NEVER BARE. `iso_date` hardcodes ONE anchor system — the Gregorian calendar — as though it
# were time itself; an absolute path hardcodes ONE — a particular host's filesystem — as though it were
# place. It is the same defect twice, and it cost this estate a session each time: a commit declared to
# exist on NO branch and NOT on disk (true of the machine searched, false of the estate), and one analysis
# reported FRESH on one host and STALE on another the same minute.
# DIMENSION-SPANNING ON PURPOSE. Time and place are the same structure with different direction lines, so
# they share ONE registry rather than each minting its own. A system declares the dimension it positions
# in, and whether a position there ESTABLISHES the location or merely CORROBORATES it — the same split
# identity anchors already use, for the same reason: a value that migrates cannot fix what you are at.
# EACH SYSTEM OWNS ITS ONE FORM, so no bean, tool or session invents a second spelling. That is not
# tidiness: `staleness_key` alone already carries four unowned spellings (`git-head:`, `git-commit:`,
# `digest:`, `manual:`), which is how one analysis acquired two verdicts. A system whose addresses have NO
# canonical form says so with `pattern: none` and a reason — the same explicit-absence rule `enforced_by`
# already applies to terms, because an unstated pattern and a deliberately absent one must not look alike.
# THE REGISTRY IS OPEN. A new system is a VOCABULARY edit and never a code edit: the gate reads `pattern`
# generically through `entry_pattern_from_registry` and names no system, exactly as it names no term.
anchor_systems:
  - system: unix-filesystem
    dimension: place
    meaning: "a position in ONE NAMED HOST's UNIX filesystem. The host is part of the position: /home/user/addin on laptop-a and on laptop-b are different positions that print identically."
    pattern: '^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:/.*)$'
    form_note: "root:<logical root>[/<relative path>] — resolved per host through that host's OWN root map, which is the form that survives a second machine; or <host>:<absolute path> stated outright where there is no root to hang it on"
    establishes: false
    why: "a path is reassignable and a tree can be checked out anywhere, so it CORROBORATES a location and never fixes it — the same rule that keeps `hostname` and `ip` corroborating-only"
    scope_note: "UNIX-SHAPED ON PURPOSE, and named so rather than called `host-filesystem`. C:\\Users\\user\\source\\repos\\addin cannot satisfy this pattern, and bending it in would give one system two formats — the exact reinvention the pattern rule exists to stop. `windows-filesystem` is declared beside it as a SEPARATE system for exactly that reason."
  - system: git-object-graph
    dimension: place
    meaning: "a position in a repository's object graph — REACHABLE-FROM, not CHECKED-OUT-AT. This is the system `staleness_key: git-head:<sha>` was reaching for and missing: it compared against whatever tree the reader happened to have checked out, which is a fact about the reader and not about the analysis."
    pattern: '^[a-z0-9][a-z0-9._-]*@[0-9a-f]{7,40}$'
    form_note: "<repo>@<object id> — ONE spelling, always. Not git-head:, not git-commit:, not a bare sha: a sha with no repository named is a position with no system."
    establishes: true
    why: "an object id is content-addressed — it names the same object in every clone that has it, and no two clones can disagree about what it contains"
  - system: physical
    dimension: place
    meaning: "where a PHYSICAL COPY is: a printed listing on a shelf, a disk in a drawer, a machine in a room. Declared because a codebase is not always a tree on a host — this ledger's own first rule is that it must survive being printed on paper and rescanned, and a printed copy has an address like anything else."
    pattern: none
    pattern_why: "a shelf, a room and a building have no canonical form this garden could impose without inventing one. Stating `none` is the honest position: the address is prose, and prose is what a human reads to go and find it."
    establishes: false
    why: "a physical copy can be moved, and two copies can sit in two places — a location corroborates which artefact you are holding, never which being it is a copy of"
  - system: gregorian-civil
    dimension: time
    meaning: "a calendar position with a stated offset. Civil time RESOLVES THROUGH a geographic position, which is why it does not establish on its own."
    pattern: '^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z)?)?$'
    form_note: "YYYY-MM-DD[THH:MM[:SS[.sss]][+HH:MM|Z]] — the RESOLUTION actually held is stated separately in `unit` and is never inferred from how many digits were typed"
    establishes: false
    why: "a wall-clock reading without its geographic frame is ambiguous. The estate's own case: a cutoff computed on a +03 host was applied to UTC logs, and the watch reported zero hits while a campaign was running."
  - system: unix-epoch
    dimension: time
    meaning: "a time position as milliseconds since 1970-01-01T00:00:00Z. Declared at 7.0 for `beanger` records, whose ORDER is the thing being recorded — two operations in one session land in the same second, and a position that cannot separate them cannot order them."
    pattern: '^\d{13}$'
    form_note: "exactly 13 digits: epoch MILLISECONDS, never seconds. One length, one meaning — a 10-digit value would be a different unit wearing the same shape, which is the ambiguity `unit` was added to stop."
    establishes: false
    why: "a moment corroborates when something was done and never fixes which being did it. It differs from `gregorian-civil` in one useful way: it carries no offset, so it cannot be misread the way a +03 label on a UTC reading was misread in this estate's own journal."
  - system: geographic
    dimension: place
    meaning: "a position on the earth. Named here because CIVIL TIME RESOLVES THROUGH IT — an offset is a geographic fact wearing a time costume — so a registry carrying gregorian-civil without it would hide the resolution chain."
    pattern: '^(site:[a-z0-9][a-z0-9-]*|-?\d+\.\d+,-?\d+\.\d+)$'
    form_note: "site:<declared site name>, or <lat>,<lon> as signed decimals"
    establishes: false
    why: "a site is a label people reassign, and a coordinate corroborates where a machine is without fixing which machine it is"
  - system: event-anchored
    dimension: any
    meaning: "a position fixed by NEIGHBOURING EVENTS rather than by any coordinate — 'after the branch was pushed, before the cutover'. Fully positioned while carrying no calendar value at all. Declared because it is what makes this a registry rather than a two-item enum: SEQUENCE is the general structure and a coordinate system is one restriction of it."
    pattern: '^(after|before):.+$'
    form_note: "after:<position> or before:<position>; state both as two entries when an interval is meant"
    establishes: false
    why: "an event anchor positions relative to other positions — it fixes an interval, never a point"
  - system: network-segment
    dimension: place
    meaning: "WHERE A BEING IS ATTACHED in a network's topology: a VLAN, a wireless network, an address range with a role. Declared 11.0, operator-ratified: a segment is a PLACE (where you are), which is a different question from an address (where you answer) — those have their own registry, and a being keeps its address while moving between segments."
    pattern: '^[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9.:-]*$'
    form_note: "<network>/<segment>, e.g. an office network's guest VLAN or its wireless network for laptops. The network is named because two sites both have a `vlan-13` and they are not the same place."
    establishes: false
    why: "a being moves between segments — a laptop joins the guest network and then the staff one — so a segment corroborates where it is and never fixes which being it is"
  - system: windows-filesystem
    dimension: place
    meaning: "a position in ONE NAMED HOST's Windows filesystem. A SEPARATE SYSTEM from unix-filesystem, not a dialect of it: C:\\Users\\user\\source\\repos\\addin and /home/user/addin share no canonical form, and one system carrying two patterns is exactly the reinvention this registry forbids."
    pattern: '^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:[A-Za-z]:\\.*)$'
    form_note: "root:<logical root>[/<relative path>], or <host>:<Drive>:\\<path> stated outright. The two colons are unambiguous — hostname, then drive letter — and the root: form is IDENTICAL to the unix one on purpose: a LOGICAL root is what crosses systems, a literal path is what does not. That is the whole mechanism for resolving one repository on machines that do not agree what a path looks like."
    establishes: false
    why: "a path is reassignable and a tree can be checked out anywhere — it corroborates a location, never fixes it. Identical to the unix case, because the reason has nothing to do with the operating system."
# == ADDRESS SYSTEMS: where a being ANSWERS, as against where it IS (added 6.0) ==
# The exact shape of `anchor_systems`, asking the other question. `anchor_systems` answers WHERE A BEING
# IS — a path, an object id, a shelf. This answers WHERE IT ANSWERS: the address another being sends to.
# Two registries because they are two questions: a mail server can BE bare metal in a room and ANSWER at
# 203.0.113.10, a public address it does not even hold locally, and neither position implies the other.
#
# WHY TWO SYSTEMS AND NOT ONE `ip`. std-vocab already made this call for filesystems and wrote the reason
# down: "one system carrying two patterns is exactly the reinvention this registry forbids". The `ip`
# term IS that reinvention — ONE term with `value_form: ip`, silently accepting both families. v4 and v6
# share no canonical form and no address arithmetic, and in this estate they do not even share
# reachability: a host booted with `ipv6.disable=1` has no v6 at all, so an address in one family is unreachable at a host that
# answers on the other. A checker that cannot tell them apart cannot notice that.
address_systems:
  - system: ipv4
    dimension: address
    meaning: "a 32-bit Internet Protocol address, optionally carrying a prefix length."
    pattern: '^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$'
    form_note: "dotted quad, optionally /prefix. The bare address and the prefixed form are the SAME system: a prefix narrows a position, it does not change what kind of position it is."
    establishes: false
    why: "reassignable by DHCP, NAT, failover and plain reuse — it corroborates which being answers and never fixes which being it IS. The same rule the `ip` anchor has always carried, now stated where the position is."
  - system: ipv6
    dimension: address
    meaning: "a 128-bit Internet Protocol address, optionally carrying a prefix length."
    pattern: '^([0-9a-f]{0,4}:){2,7}[0-9a-f]{0,4}(/\d{1,3})?$'
    form_note: "lowercase hex in RFC 5952 compressed form, optionally /prefix. NOT a dialect of ipv4 — it shares no format with it, and one pattern covering both could not tell a malformed quad from a valid v6 address."
    establishes: false
    why: "everything ipv4's reason says, and one more: v6 addresses are also AUTOCONFIGURED, so a being may answer at an address nobody assigned and nobody recorded."

# == ROLES: what a being DOES, as against what it IS (added 7.0) ==
# THE FIX FOR AN AMBIGUITY THIS VOCABULARY SHIPPED WITH. `router` was a KIND until 7.0, and the proof it
# was wrong is an asymmetry the corpus already carried: a mail server recorded five roles as free-text data
# (`primary-mail, file-server, monitoring, webmail, erp-host`) while a router's single role was a kind.
# Both are machines. What makes one a router is that it forwards traffic — which since 6.0 IS data, in
# `treatments`. A kind answers what a being IS; a role answers what it DOES, and a being does several
# things at once. Encoding one of the things it does as the thing it is made `kind` un-askable for every
# machine that does two.
roles:
  - { role: router,             meaning: "forwards traffic between networks and decides what may cross" }
  - { role: mail-primary,       meaning: "the MX of record for the estate's domains" }
  - { role: mail-backup,        meaning: "a secondary MX that spools and drains to the primary" }
  - { role: file-server,        meaning: "serves file shares to the local network" }
  - { role: dns-resolver,       meaning: "resolves names on behalf of local clients" }
  - { role: dns-authoritative,  meaning: "answers authoritatively for zones the estate holds" }
  - { role: monitoring,         meaning: "collects and alerts on the health of other beings" }
  - { role: web,                meaning: "serves HTTP to people or machines" }
  - { role: app-host,           meaning: "runs application instances (Odoo and friends) for others to use" }
  - { role: vpn-gateway,        meaning: "terminates tunnels and carries another being's public identity" }
  - { role: ledger-hub,         meaning: "holds the bare repository every working copy of this ledger pushes to" }
  - { role: workstation,        meaning: "a machine a person works AT, rather than one that serves others" }

# == OPERATING SYSTEMS: what a machine runs, and what that IMPLIES about its positions (added 7.0) ==
# It is a REGISTRY and not prose because it CONSTRAINS. `owns.os` was free text — a distribution name with its
# point release — and a router, the one machine whose OS is genuinely distinctive, could not state it at all:
# its OS lived only inside a summary sentence and an `owns.model` string.
#
# `path_grammar` IS THE JOIN, and it is the answer to "where do ntfs and ext4 go". They do not go here.
# `unix-filesystem` and `windows-filesystem` in `anchor_systems` are PATH GRAMMARS — properties of an
# OS's API — and NOT filesystems. The two axes are independent: NTFS mounted on Linux through ntfs-3g
# has unix paths, and one SMB share is `/mnt/share0` on the server and `\\server\share0` from a workstation. So an
# OS declares which grammar its filesystem positions take, and `roots` is held to it by
# `entry_must_match`. Storage FORMAT is a different registry entirely — see `storage_formats`.
operating_systems:
  - { os: slackware, family: unix,    path_grammar: unix-filesystem,
      meaning: "Slackware Linux." }
  - { os: almalinux, family: unix,    path_grammar: unix-filesystem,
      meaning: "AlmaLinux, a RHEL-compatible distribution." }
  - os: windows
    family: windows
    path_grammar: windows-filesystem
    meaning: "Microsoft Windows. Its path grammar is `windows-filesystem`."
  - os: routeros
    family: network-os
    path_grammar: none
    path_grammar_why: >
      DELIBERATELY none, and the most interesting row here. RouterOS positions are CONFIG MENU paths —
      `/ip firewall nat`, `/interface/wireguard/peers` — not filesystem paths, and they resolve in a
      configuration tree rather than in a directory. `pattern: none` is already an honoured value in
      `anchor_systems`, declared there for the `physical` system, so refusing to invent a grammar is a
      shape this law can already express rather than a special case invented for this row.
    meaning: "MikroTik RouterOS. Not a general-purpose OS: no user filesystem worth positioning in."
  # COMMON SYSTEMS (9.0). Until 9.0 this registry held exactly the four systems of the garden it grew in, so almost
  # every newcomer's first machine needed a local addition. `linux` is the honest row for a distribution not listed.
  - { os: linux,   family: unix, path_grammar: unix-filesystem, meaning: "A Linux system whose distribution is not listed here, or not worth distinguishing." }
  - { os: debian,  family: unix, path_grammar: unix-filesystem, meaning: "Debian GNU/Linux." }
  - { os: ubuntu,  family: unix, path_grammar: unix-filesystem, meaning: "Ubuntu." }
  - { os: rhel,    family: unix, path_grammar: unix-filesystem, meaning: "Red Hat Enterprise Linux." }
  - { os: fedora,  family: unix, path_grammar: unix-filesystem, meaning: "Fedora Linux." }
  - { os: arch,    family: unix, path_grammar: unix-filesystem, meaning: "Arch Linux." }
  - { os: alpine,  family: unix, path_grammar: unix-filesystem, meaning: "Alpine Linux." }
  - { os: freebsd, family: unix, path_grammar: unix-filesystem, meaning: "FreeBSD." }
  - { os: macos,   family: unix, path_grammar: unix-filesystem, meaning: "Apple macOS." }

# == STORAGE FORMATS: the OTHER filesystem axis, the one ntfs and ext4 actually belong to (added 7.0) ==
# `layer` mirrors `net_protocols.layer` and for the same reason: storage is a STACK and the stack is what
# `carried_by` records. MEASURED on real machines rather than imagined — the chain
# `partition -> crypto_LUKS -> LVM2_member -> ext4` is literally what `lsblk` prints on an encrypted laptop, and a
# RAID server adds `linux_raid_member -> md` beneath it. `luks_root: true`, a bare boolean in an `attributes` block,
# is that whole chain flattened to one bit.
storage_formats:
  - { format: ext4,              layer: filesystem,     posix: true,  meaning: "the estate's ordinary Linux filesystem" }
  - { format: ext2,              layer: filesystem,     posix: true,  meaning: "a common /boot filesystem" }
  - { format: vfat,              layer: filesystem,     posix: false, meaning: "the usual EFI system partition. NOT posix: it carries no ownership or permission bits, which is why an EFI partition cannot hold anything whose mode matters." }
  - { format: swap,              layer: swap,                         meaning: "paging space; a formatted volume that holds no filesystem" }
  - { format: crypto_LUKS,       layer: encryption,                   meaning: "a LUKS container. CARRIES another volume rather than holding files itself — the clearest case for `carried_by`." }
  - { format: LVM2_member,       layer: volume-manager,               meaning: "an LVM physical volume; the logical volumes inside it are separate entries that name it in `carried_by`" }
  - { format: linux_raid_member, layer: raid,                         meaning: "an md RAID member. e.g. raid1 for /boot, raid6 for share arrays." }
  - { format: ntfs,              layer: filesystem,     posix: false, meaning: "the Windows filesystem. Declared and unoccupied — see the vacancy. It is named here because the question 'where does ntfs go' is what produced this registry, and the answer is that it is a STORAGE FORMAT and never a path grammar." }

# == NET PROTOCOLS: the one owner of what a being may SPEAK (added 6.0) ==
# A REGISTRY rather than an enum on a term, for the reason `anchor_systems` is one: adding a protocol
# must never be a rule-change. A row carries what is true of the PROTOCOL — which layer it occupies,
# what carries it, and whether it manufactures a link others ride — so that no bean re-states any of it.
#
# WHAT IS DELIBERATELY NOT HERE — IMPLEMENTATIONS. Samba OFFERS smb; the MySQL server SPEAKS mysql;
# Postfix speaks smtp. An implementation is a BEAN (kind instance/product) that carries `endpoints`, and
# putting `samba` in this list beside `smb` would give one thing two names — the exact duplication
# `values_from` exists to stop. This was the first correction the design took: two of the names it was
# asked to model explicitly, `samba` and `mysql`, are implementations, and encoding them as protocols
# would have built the ambiguity into the law.
#
# NOR ARE TLS VARIANTS SEPARATE ROWS. `https` is `http` whose endpoint takes the `encrypted` position;
# smtps and submission are `smtp` on other ports. A protocol that differs from another only by what
# wraps it is not another protocol, and giving it a row would put the same fact in two places — once as
# a name and once as an aspect position — which is how the two come to disagree.
#
# `layer` is DESCRIPTIVE, like `dimension` on anchor_systems: the gate consumes `protocol` (as the enum)
# and nothing else in the row. It is here because carriage is what makes this a stack and not a list.
net_protocols:
  - protocol: ssh
    layer: application
    transport: tcp
    default_ports: [22]
    meaning: "the Secure Shell transport: an authenticated, encrypted channel that other protocols ride."
  - protocol: sftp
    layer: application
    transport: tcp
    rides_on: [ssh]
    meaning: "file transfer carried INSIDE an ssh channel. It has no port of its own, and `rides_on` is what records that rather than a fabricated default."
  - protocol: git
    layer: application
    transport: tcp
    rides_on: [ssh, http]
    meaning: "the git wire protocol. It is usually carried — `host-a:git/ledger.git` and `vps-a:addin` are both git over ssh — so its protection is whatever carries it, and the row says so instead of claiming one."
  - protocol: http
    layer: application
    transport: tcp
    default_ports: [80, 443]
    meaning: "the Hypertext Transfer Protocol. 443 is this same protocol with an endpoint taking the `encrypted` position, NOT a separate protocol called https."
  - protocol: smtp
    layer: application
    transport: tcp
    default_ports: [25, 465, 587]
    meaning: "mail transfer. One protocol on three ports: 25 relay, 465 implicit TLS, 587 submission — the port is a fact about the endpoint and the protection is an aspect position, so none of the three needs its own row."
  - protocol: pop3
    layer: application
    transport: tcp
    default_ports: [110, 995]
    meaning: "mailbox retrieval, download-oriented. 995 is the same protocol wrapped in TLS."
  - protocol: imap
    layer: application
    transport: tcp
    default_ports: [143, 993]
    meaning: "mailbox access, server-side-state-oriented. 993 is the same protocol wrapped in TLS."
  - protocol: smb
    layer: application
    transport: tcp
    default_ports: [445]
    meaning: "the Server Message Block file-sharing protocol. The PROTOCOL — Samba is one implementation of it and is a bean, not a row."
  - protocol: mysql
    layer: application
    transport: tcp
    default_ports: [3306]
    meaning: "the MySQL/MariaDB client-server wire protocol. Again the protocol, not the server."
  - protocol: dns
    layer: application
    transport: udp
    default_ports: [53]
    meaning: "the Domain Name System query protocol. Added beyond the eighteen names the design was asked for, because this estate runs three BIND beans and omitting it would have forced them to record their listening surface as something they do not speak."
  - protocol: wireguard
    layer: link
    transport: udp
    default_ports: [51820]
    synthesizes_link: true
    meaning: "a tunnel protocol that MANUFACTURES A LINK: a wireguard peering produces an interface other protocols are then carried over. `synthesizes_link` is what distinguishes it from every application row above, and it is why `links` is a term and not a note."
  - protocol: pptp
    layer: link
    transport: tcp
    default_ports: [1723]
    synthesizes_link: true
    meaning: >
      the Point-to-Point Tunneling Protocol. Registered so the estate can state that it does NOT use it
      and never will — see the `network` profile's vacancies, where the position is declared `impossible`
      rather than `prediction`. Its MS-CHAPv2 authentication and MPPE encryption are both broken by
      published attacks, so a tunnel built on it protects nothing while LOOKING like a VPN in every
      inventory. A registry that omitted it could not express that judgment at all; the vacancy is where
      the judgment lives, and occupying the position warns.
  # APPENDED AFTER THE APPLICATION ROWS RATHER THAN BESIDE `wireguard`, where they belong by layer.
  # dmsafe compares leaf paths BY INDEX, so inserting a row mid-list reads as deleting the fields of
  # every row after it — the rollback said so and was right about what it could see. Grouping by layer
  # is a legibility preference; a clean, honest diff is not.
  - protocol: ethernet
    layer: link
    meaning: "an ethernet link, including an aggregated one. Added while MIGRATING the corpus, not while designing it: `carried_by` had nothing to terminate on until a base link existed, and an aggregated bond is a real measured one. This row is the design's own claim tested on itself — adding a protocol is a registry row, not a rule-change to any term."
  - protocol: pppoe
    layer: link
    rides_on: [ethernet]
    synthesizes_link: true
    meaning: "PPP over Ethernet: a WAN dial that runs directly on ethernet frames, with no IP transport or port of its own (9.0 removed a `transport: tcp` / port 1723 copied from pptp). Like wireguard it MANUFACTURES a link, which is what lets a tunnel name it in `carried_by`."

# == UNITS: the resolution a position is actually held to (added 5.1) ==
# DECLARED, NEVER INFERRED FROM DIGITS. A journal can state most entries as `## 2026-08-04` and a few as
# `## 2026-08-04 20:04 +0300`, and nothing records which of the first were measured to the day and which
# were measured finer and rounded. Two positions whose resolutions OVERLAP ARE NOT ORDERED, and a model
# that cannot say so invents an order instead — which is the failure this registry exists to make
# expressible. Keyed by `dimension`, so a length or an angle joins without a rule-change.
units:
  - unit: millisecond
    dimension: time
    meaning: "the finest resolution this ledger records; sessions and their sync points are held here"
  - unit: second
    dimension: time
    meaning: "a position held to the second"
  - unit: minute
    dimension: time
    meaning: "a position held to the minute — the journal's 34 offset-bearing entries sit here"
  - unit: day
    dimension: time
    meaning: "a position held to the calendar day — what every `iso_date` in this corpus actually holds"
# == VACANCIES (Tier-0). P6/B2: whoever DECLARES a position accounts for it, so the duty to explain
# these is discharged HERE — an adopting garden must never inherit an obligation to justify a position it
# never asked for. The gate applies ANTI-ROT only to garden-local vacancies: a garden that OCCUPIES one of
# these is a prediction coming true, and it cannot edit Tier-0 to withdraw the vacancy, so treating that
# as an error would be an unfixable failure.
# The reasons a vacancy may give, declared rather than known by the gate. A reason is a CATEGORY OF
# ABSENCE — why nothing occupies a position the law makes available — and that is a statement about the
# world, which the vocabulary owns and the interpreter must not carry a copy of. Adding a reason is a
# rule-change here, not an edit to bin/.
vacancy_reasons: [prediction, impossible, out-of-context]

# == LEAF SUBSUMPTION ORDERS (declared 2026-08-03, Phase 6) ==
# `merge_field` absorbs a general value into a more precise one where the two are ORDERED: 192.168.0.0/24
# into 192.168.0.0/16, "AlmaLinux 9" into "AlmaLinux 9.8". WHICH keys are ordered that way was decided in
# code by two hardcoded checks on the key's NAME, whose own comment called them "the last hardcoded merge
# knowledge here, and they belong in the vocabulary". They are here now.
#
# This is the fallback for the facts INSIDE `owns` / `details` / `attributes`. A term's own `merge.order`
# still wins where a term exists — but those inner keys are FACTS, not terms, and `bin/dmmerge.py` says
# so outright: "listing them would bury the real gap in three hundred names". A registry of ORDERS is the
# shape that fits, because the rule is about a family of names and not about any one of them.
leaf_orders:
  - order: cidr
    suffix: _ip
    exact: []          # `provides_ip`, `public_ip` and `mgmt_ip` were also listed by name in the code —
                       # all three end in `_ip`, so every one of them was already covered by the suffix
                       # and the list was dead weight. Measured before deleting it, not assumed.
    why: "an address or network is absorbed by a network that contains it (ipaddress.subnet_of)"
  - order: version
    suffix: _version
    exact: [os, version]   # `version` does NOT end in `_version`, so unlike the cidr list this one earns
                           # its place; `os` is the estate's one bare version-shaped fact name.
    why: "a release string is absorbed by a more precise one that starts with it"
  - order: containment
    system: unix-filesystem   # 11.0: and the windows one, whose rows carry the same `root:`/`<host>:` forms
    also_systems: [windows-filesystem]
    why: "a tree is absorbed by a subtree of it under the SAME host or logical root (`host-a:/home/user` by `host-a:/home/user/tree`). Positions on two hosts, two roots or two systems are UNORDERED and stay a disagreement: the same path on two machines is two different trees, which is the whole reason a position names its host."
  - order: instant
    system: gregorian-civil   # 9.3, T2: this order follows what a value IS, not what its key is called. Time
                              # sits under a dozen names in one corpus (observed, as_of, found, since, created,
                              # expires, …) and under `at`, which also holds paths; a name list would miss the
                              # next name and misfire on `at`. A value in this system's ONE form is a time.
    why: "a calendar reading is absorbed by a finer one it CONTAINS (`2026-09-19` by `2026-09-19 22:50+03:00`), compared by the parts actually written and in the coarser reading's own offset, never as strings. Every other pair is unordered (the `time` aspect's order is partial): two readings that do not nest stay a disagreement for a person. The absorbed reading is kept in provenance, as every subsumed value is."
vacancies:
  - at: status.values
    position: at-risk
    reason: prediction
    why: >
      No bean is at-risk today, and until 2026-08-08 nothing said so — the position sat unoccupied and
      unaccounted while four of the other five were in use. It surfaced only because adding `closed` sent
      a reader through the enum counting occupants, which is the reverse gate's own argument arriving by
      hand rather than by tool. Kept because it is the one status that asks for ACTION rather than
      describing a state: a being still relied upon and known to be failing. An estate that keeps a risk
      register yet never marks a bean at-risk has an inventory nobody consults, which is worth noticing.
  - at: storage_format.values
    position: ntfs
    reason: prediction
    why: >
      Measured at zero across the corpus on 2026-08-07. Declared anyway because "where does ntfs go" is
      the question that produced this registry, and the answer needs to be visible: it is a STORAGE FORMAT
      and never a path grammar. It arrives with the first Windows machine given a bean — the same one
      `os.values = windows` waits for, which is why the two vacancies rise and fall together.
  # == THE ENTRY FORMS THE OWNERSHIP TERMS OFFER (declared vacant 2026-08-03) ==
  # `entry_one_of` positions are positions like any other: the law offers a form and something should
  # occupy it or say why not. Nothing counted them until the reverse gate learned to, and all three of
  # these turned out to be genuinely unoccupied rather than overlooked.
  - at: "owned_by.entry_one_of"
    position: contract
    reason: prediction
    why: "Co-ownership of a single facet. The machinery is built and unused: the one `contract` bean in the reference garden is NOT an ownership contract — its own summary says it is a standalone co-facilitation contract, and its terms name two organisations as creation-facilitators, 'NOT owners of the code', which is owned outright by the operator. Nothing is co-owned today. Expected to arrive with the first facet two parties genuinely share, which is what the form and its `agreement_ref` + `conflict_rule` requirements exist for."
  - at: "responsibility.entry_one_of"
    position: contract
    reason: prediction
    why: "A duty two parties hold jointly, under an agreement. The mirror of the vacancy above and vacant for the same reason: no facet in this estate is co-owned, so none is co-answered-for. It would arrive with the ownership one, since responsibility pairs with ownership facet by facet."
  - at: "responsibility.entry_one_of"
    position: external
    reason: prediction
    why: "A duty held by a party outside this ledger. NOT an oversight and not symmetric with `owned_by.external`, which IS occupied — a rented VPS's `owned_by.legal` is `external: <provider>`, because the VPS is rented and the provider owns the machine. MODEL.md's rule is exactly this asymmetry: a rented VPS is owned by the provider and ANSWERED FOR by the operator, because a duty must land on a being that can be asked. The position would be occupied by an obligation genuinely borne by an outside party — a provider's SLA that nobody here can be asked about — and this estate has recorded none."
  - at: "aspect:feasibility"
    position: necessary
    reason: prediction
    why: "Unavoidability — a being that CANNOT NOT have a capability. Unoccupied because every capability recorded so far is under someone's control, ours or a provider's. It is expected to arrive with the first capability imposed by a substrate that no party can switch off: a VPS provider that re-applies its own network metadata on every boot which is close, but that is provider POLICY and therefore contingent, not necessary."
  - at: "aspect:capability"
    position: omissible
    reason: prediction
    why: "Recording that a being MAY LACK something is low-information until a capability is contested — expected first where an agent might add a capability believing it required, e.g. marking DNSSEC omissible on an internal-only zone so nobody enables it for form's sake."
  # == THE DEFAULT POSITION, VACANT BECAUSE A DEFAULT NO LONGER OCCUPIES (declared 2026-08-03) ==
  # Until today the reverse gate collected occupancy with `entry.get(attr, default)`, so this position
  # looked exercised by five edges that never mention it — the gate crediting its own default. Occupancy
  # is STATEMENT now, and what that leaves behind is this: a position every requirement in the estate
  # effectively sits at, and none has ever taken a stance on.
  - at: "aspect:necessity"
    position: contingent
    reason: prediction
    why: "Every requirement recorded in this estate so far is load-bearing: all 5 consumes/depends_on edges sit at `necessary`. A contingent requirement — used but not needed — is the ordinary case for an optional integration, and is expected to arrive with the first one."
  - at: "aspect:necessity"
    position: possible
    reason: prediction
    why: "A requirement a being COULD take is a planning position rather than a recorded fact, so it is expected to appear when the ledger starts carrying intended architecture alongside actual."
  - at: analysis_cache.policy
    position: skim
    reason: prediction
    why: "Mirrors code_paths.scan_policy: no analysis has yet been produced by reading structure only. Expected to fill together with the vendored-dependency and generated-artifact roles."
  - at: analysis_cache.form
    position: inline
    reason: prediction
    why: "Every cached analysis today points at a bean field (form: summary_ref). inline would carry the result inside the cache entry itself — right for a result too small to deserve its own field, e.g. a dependency count or a single digest."
  - at: analysis_cache.form
    position: external
    reason: prediction
    why: "No cached analysis lives in an off-bean document yet. external is the form for a result too large to sit in a bean at all — a full dependency graph or a coverage report."

# == ASPECTS (added 2026-08-02, std-vocab@2.1) ==
# DIMENSION-AGNOSTIC. An aspect declares its own axes and the gate does not care how many: `poles` is one
# contradictory PAIR, or a LIST of pairs. A figure may be 1-dimensional (a plain binary), 2 (a square),
# 3 (a cube), or more — what is required is that every declared axis runs between genuine opposites, so a
# position is addressable along it. The count is DERIVED from the declaration, never assumed, because
# assuming a count is exactly how a square silently mis-models a cube. Likewise `cross_aspect`
# combinations are N-ary: they constrain ONE aspect or SEVERAL, and the machinery is the same either way.
# An ASPECT is a CLOSED figure of positions — the operator's requirement that a classification have no
# loose ends. A line has undefined extremes and forces partial membership; a closed figure does not, so
# polarity lives in OPPOSED POSITIONS rather than at the ends of a scale. Each position names its
# COMPLEMENT, which is what lets a being be addressed by opposition as well as by identity ("the light is
# not where darkness is"). The gate enforces the sanity rules — closure, orientation, complement mutuality
# — and names no aspect, so a new aspect is data, never a code change.
  # == POSITION SYSTEMS AND RESOLUTIONS NOT YET TAKEN (declared 5.1, 2026-08-07) ==
  # Declared here rather than left silent because the whole argument for naming an anchor system is that
  # an UNSTATED domain is what makes a negative result read as strong. A registry that quietly carried
  # systems nothing occupies would be committing the same error one level up.
  - at: anchor_system.values
    position: physical
    reason: prediction
    why: "No being in this estate is recorded as a physical copy yet. It is expected and not hypothetical: this ledger's first rule is that it must survive being printed on paper and rescanned, a codebase can exist as a printed listing or a disk in a drawer, and the operator named exactly that case when this term was designed. It is the one system deliberately carrying `pattern: none`, so occupying it also exercises the deliberate-absence path."
  - at: anchor_system.values
    position: geographic
    reason: prediction
    why: "Declared because CIVIL TIME RESOLVES THROUGH IT — a UTC offset is a geographic fact — so a registry offering gregorian-civil while hiding what it resolves through would conceal the chain. Unoccupied because no bean states where its machine physically is: `owns.site` holds prose (a data-centre name) that has never been read as a position. Expected to fill the first time a time reading has to be reconciled across two sites — a +03:00 host read against UTC logs is the shape of that defect."
  - at: anchor_system.values
    position: event-anchored
    reason: prediction
    why: "A position fixed only by its neighbours — 'after the push, before the cutover' — carrying no coordinate at all. Declared because it is what makes this a registry of SYSTEMS rather than a pair of coordinate schemes: sequence is the general structure and a calendar is one restriction of it. Unoccupied because every position recorded so far has had a coordinate available. Expected first in the journal, where an entry's real position is often 'between these two commits' and a date was written because the form demanded one."
  - at: anchor_system.values
    position: network-segment
    reason: prediction
    why: "WHERE A BEING IS ATTACHED in a network — a VLAN, a wireless network, an address range with a role. Declared 11.0 with the operator's ratification that a segment is a place and not an address. Unoccupied because no bean yet states which segment it is attached to; expected first where one network carries staff, guests and laptops on separate segments and the difference decides what a machine may reach."
  - at: unit.values
    position: second
    reason: prediction
    why: "Nothing in this ledger is currently held to the second: session moments are recorded at millisecond, and everything else at day. Kept because it is the resolution a log line carries, and the digestion of host logs is the obvious first occupant."
  - at: located_at.openness
    position: unknown
    reason: prediction
    why: "The position that would have prevented a real loss: a commit was recorded as absent when it was merely not looked for on the machine that had it. Unoccupied TODAY because every location in the corpus has been established — which is the state this position exists to distinguish from, and it earns its declaration by being the one an agent must reach for instead of omitting the entry."
# == FIGURES: the shapes an aspect may take (added 9.2, human-ratified rule-change, "T0") ==
# Until 9.2 every aspect was an OPPOSITION (a square, or a one-axis binary) and `figure:` was free text. Time, place,
# routine steps and "must stay acyclic" are not oppositions: they are positions related by NEIGHBOURHOOD
# along direction lines. So a second figure is declared, and `figure` becomes an enum this registry owns.
#
# SEQUENCE IS THE GENERAL STRUCTURE; everything ordered is a RESTRICTION of it. The operator's model, from
# the time conversation of 2026-08-05: an instant is a sequence restricted to one position on one line;
# "acyclic" is a sequence restricted from returning; a calendar is one anchor system on a metered line,
# never time itself. A sequence is therefore declared ONLY by its restrictions, each stated, none assumed:
# an unstated restriction is how a model silently becomes narrower than the world (the `dag` rule once
# took "acyclic" to be the definition of walkable).
#
# EXTENT. A sequence with an order has a DOMAIN, and a bounded region of it (a start and an end, either
# possibly open) is an extent: a duration on time, an area on place, a stretch of a routine. Duration is
# therefore not a time concept but an aspect-having-a-domain concept. An opposition has no "between": its
# positions are modalities without order, so extent on one is declared IMPOSSIBLE rather than skipped.
figures:
  - figure: opposition
    # NAMED FOR WHAT IT IS, NOT FOR ITS DIMENSION. Aristotle's square of opposition is this figure's TWO-axis
    # case, a plain binary its one-axis case (`confidentiality`) and a cube its three-axis case. Calling the
    # figure "square" would fix a count the gate is required to derive: "when doing the squares make sure
    # cubes don't bite" (the operator, 2026-08-02).
    meaning: "a CLOSED figure of contradictory pairs: finite positions, each naming its mutual complement, oriented by one or more axes (the count is derived from `poles`, never assumed)"
    requires: [poles, positions]
    extent: impossible
    extent_why: "the positions are modalities, not points on a line: nothing lies between `necessary` and `possible`, so there is no region to bound"
  - figure: sequence
    meaning: "positions related by NEIGHBOURHOOD along direction lines, walkable, and declared only by its restrictions"
    requires: [lines, metered, order, acyclic, ends, domain]
    restrictions:
      lines:   "a positive integer, or `open`: how many direction lines. Things are one or more; the gate reads the count, it never assumes one"
      metered: "a dimension from `units` (a position carries a measure at a stated unit), or `none` (neighbourhood only: before, after, next)"
      order:   "total | partial | none. `partial` means some pairs are NOT ordered, and the model says so instead of inventing an order"
      acyclic: "true | false: whether walking a line can return to where it began"
      ends:    "open | bounded | open-start | open-end: the domain's boundaries"
      domain:  "{ systems: <dimension> | none }: the anchor-system dimension whose positions the aspect holds (systems of dimension `any` sit in every domain), or `none` when its positions are beans"
    order_values: [total, partial, none]
    ends_values: [open, bounded, open-start, open-end]
    extent: possible
    extent_why: "a sequence with an order has a domain, and a bounded region of it is an extent (a duration on time)"
# == EXTENT (11.2): the bounded region `figures` has declared POSSIBLE since 11.0, carried at last ==
# The figure block above says it and says why — "a sequence with an order has a domain, and a bounded region
# of it is an extent (a duration on time)" — and for two versions nothing could write one. A corpus measured
# on 2026-09-20 held about forty durations as PROSE because of it: thirteen "daily", five "weekly", "every 5
# minutes", "for 204 days", four retention policies, log rotation, certificate lifetimes. None of them
# readable by anything. That is the shape of defect this vocabulary exists to refuse — a rule with no
# position for its own data — and it was in the law's own description of itself.
#
# DURATION IS NOT A TIME CONCEPT. It is an aspect-having-a-domain concept: a duration on `time`, an area on
# `place`, a stretch of a `routine`. So the region names the ASPECT it lies in and the rules follow from
# that aspect's own restrictions, rather than time getting a construct nothing else can use.
extent_form:
  of:      "the ASPECT whose domain this region lies in. Its figure must declare `extent: possible` — an opposition's positions are modalities with nothing between them, so a region on one is refused rather than silently allowed."
  from:    "optional: the position the region starts at, in the canonical form of one of that aspect's domain systems"
  to:      "optional: the position it ends at"
  measure: "optional: { count, unit } — how much of the domain it spans. A METERED aspect only: a stretch of a routine has no length, because `routine` declares `metered: none`, and the unit's dimension must be the one the aspect meters."
  requires: "at least one of from / to / measure — a region with no bound at either end and no length is not a region"
  open_ends: >
    Ends may be open, as `figures` says, and which ones are open is carried by which keys are present:
    `from` alone is open-ended, `to` alone is open-start, and a `measure` alone is a LENGTH whose ends are
    not fixed at all. That last is what most of a real corpus's durations turn out to be — "for 204 days"
    says how long and never says from when.
  not_a_recurrence: >
    AN EXTENT IS ONE REGION, NOT A REPEATING ONE. "every 5 minutes" and "bills on the 15th of each month"
    are RECURRENCE RULES: a rule for generating positions, which is a different kind of thing and is
    deliberately NOT expressible here. The distinction is not pedantry — a recurrence needs a rule
    (calendar-anchored, or every N units from a start) and the two have different failure modes. A garden
    that needs one should propose it rather than writing a measure that lies about being a repetition.
  not_a_calendar_bucket: >
    `units` holds millisecond, second, minute and day, and deliberately no month, week or year. A month is
    not a measure — it is 28, 29, 30 or 31 days — and a year is not either. A term whose real rule is "on
    this date each month" is recording a recurrence anchored to a calendar, not a length, and `measure`
    would make it look like arithmetic that it is not.

# == VALUE TYPES (10.0, T3): the named types `entry_types` / `attr_types` may use ==
# They were patterns written in the gate's code. A TIME value type is a POSITION: `iso_date` is not "a date
# format" but the calendar system held at unit DAY, so every `observed: 2026-08-09` in a garden was always a
# position in gregorian-civil whose second and minute are UNKNOWN, not zero. Saying so needs no data change;
# it states what those values already were. A type with no system (kebab) is only a form.
value_types:
  - type: iso_date
    system: gregorian-civil
    unit: day
    pattern: '^\d{4}-\d{2}-\d{2}$'
    refusal: "must be an ABSOLUTE date YYYY-MM-DD (Rule 6 paper-durable)"
    meaning: "a calendar position held to the DAY; its time of day is not known, which is different from midnight"
  - type: kebab
    pattern: '^[a-z0-9]+(-[a-z0-9]+)*$'
    refusal: "must be kebab-case (the name is open, but still paper-durable)"
    meaning: "an open name in lowercase words joined by hyphens"
# == THE JOURNAL (10.0, T3): where the record of what was done is, and how an entry is headed ==
# The journal is the garden's time record, and it had no rule for time. One real garden, measured on
# 2026-09-19: 663 entries, 276 headed with a date only, 387 with a time in `+0300` or `+0330` while the calendar
# system's one form is `+03:00`; and one entry headed 23:59 that was committed at 23:32, a precision written
# rather than read. A heading is now a position in gregorian-civil's one form, held to at least the MINUTE,
# with its offset, because an entry is ordered against every other and a reading with no offset cannot be.
# Only headings ADDED by a commit are checked: the journal is never rewritten, so its history keeps the forms
# it was written in, and those stay what they were.
journal:
  path: log/journal.md
  heading_form: "## <YYYY-MM-DD HH:MM[:SS[.sss]]><+HH:MM|Z> · <who> · <what>"
  heading_pattern: '^## \d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2}(\.\d{1,3})?)?([+-]\d{2}:\d{2}|Z) · \S.* · \S.*$'
  system: gregorian-civil
  unit_at_least: minute
  checks: added     # entries a commit adds; never the history
aspects:
  - aspect: necessity
    # The canonical closed figure for necessity is Aristotle's SQUARE OF OPPOSITION (De Interpretatione;
    # the modal square). Nothing invented: the four modalities and their contradictories are off the shelf,
    # and the diagonals ARE the complement pairs. `consumes` and `depends_on` are positions on this aspect,
    # which is what the operator meant by "consumption is going to be necessity aspect" — consumption is
    # not a standalone edge but one way a being can NEED something.
    meaning: "what a being requires in order to do its work"
    figure: opposition
    poles: [[necessary, contingent], [possible, impossible]]   # BOTH axes: a square is 2-dimensional,
                                          # and declaring one would orient it like a line
    positions:
      - { position: necessary,  complement: contingent, meaning: "without it the being cannot do its work at all" }
      - { position: contingent, complement: necessary,  meaning: "the being uses it, but could do its work without it" }
      - { position: possible,   complement: impossible, meaning: "the being could take it; nothing forbids it" }
      - { position: impossible, complement: possible,   meaning: "the requirement exists but the recorded target CANNOT satisfy it. Distinct from an ABSENT edge: a missing backup is a gap, while a backup that cannot work is worse, because the record makes it look present. First occupied 2026-08-02 by a domain's backup MX record that named its own primary." }

  - aspect: capability
    # The SECOND aspect, and the first evidence that the machinery generalises. It reuses the square of
    # opposition but NOT the same square: `necessity` is ALETHIC modality (what IS the case — this input is
    # required), while capability is DEONTIC (what MAY or MUST be the case — this being must not do that).
    # Conflating them is the same error as one axis doing two jobs: "this VPS cannot send mail directly" and
    # "recursion must stay off" feel alike and are not — one is a fact about the world, the other a rule.
    # Positions relate a being to a CAPABILITY (an open kebab name), not to another being, which is what
    # the necessity aspect could not express.
    meaning: "what a being may or must be able to do"
    figure: opposition
    poles: [[required, omissible], [permitted, forbidden]]     # both deontic axes
    positions:
      - { position: required,  complement: omissible,  meaning: "the being MUST have it — remove it and the being stops working correctly" }
      - { position: omissible, complement: required,   meaning: "the being need not have it; its absence breaks nothing" }
      - { position: permitted, complement: forbidden,  meaning: "the being MAY have it; nothing forbids it" }
      - { position: forbidden, complement: permitted,  meaning: "the being MUST NOT have it. The enforcer may be our own policy or an outside party (a provider blocking a port), so an entry may name it in `by`." }

  - aspect: feasibility
    # The THIRD aspect, and the reason a term may sit on more than one. It shares the ALETHIC square with
    # `necessity` but asks a different question of it: necessity asks whether a REQUIREMENT is binding,
    # feasibility asks whether a STATE OF AFFAIRS can obtain. Reusing `necessity` for this would have been
    # equivocation — its positions are documented in requirement terms ("without it the being cannot do its
    # work"), which is not what "recursion could be switched on" means.
    # WHY IT EARNS ITS PLACE: a prohibition on something IMPOSSIBLE is harmless; a prohibition on something
    # POSSIBLE is where the risk lives. a DNS server's recursion ban matters precisely BECAUSE recursion could
    # be switched on, whereas a VPS's mail-egress ban is belt-and-braces over a block that already stops it.
    # Only carrying both modalities distinguishes those two, and they demand very different vigilance.
    meaning: "whether a state of affairs CAN obtain for this being, independent of whether it is allowed"
    figure: opposition
    poles: [[necessary, contingent], [possible, impossible]]     # both alethic axes
    positions:
      - { position: necessary,  complement: contingent, meaning: "unavoidably the case — the being cannot not have it" }
      - { position: contingent, complement: necessary,  meaning: "it IS the case, but could be otherwise — which is exactly why it is worth recording" }
      - { position: possible,   complement: impossible, meaning: "not the case, but it COULD be. A prohibition sitting here is a live risk, not a formality." }
      - { position: impossible, complement: possible,   meaning: "it cannot be the case at all — something outside the rule already prevents it" }

  - aspect: confidentiality
    # The FOURTH aspect, and the first that is ONE-DIMENSIONAL. `poles` already allowed it — "one axis
    # (a contradictory PAIR), or a LIST of axes — a figure may be 1-dimensional" — and nothing had
    # exercised it. A one-axis figure is the honest shape here: whether a channel protects its payload
    # is a single contradictory pair, and there is no second modality of it.
    #
    # WHAT WAS CONSIDERED AND REJECTED: a second axis for PEER VERIFICATION (verified/unverified), which
    # would have made this a square like the other three. It was dropped rather than forced. In the three
    # existing squares the two axes are related by subalternation — necessary implies possible, required
    # implies permitted — and verification does not stand in that relation to encryption in any way that
    # survives contact with opportunistic TLS, where the channel is encrypted and the peer is proven by
    # nothing. Inventing the implication to make the figure symmetrical would be exactly the silent
    # generalisation the protocol forbids. Peer verification is a real and separate question, and it can
    # be its own aspect the day something needs to take a position on it.
    meaning: "whether a channel protects what crosses it from anything on the path"
    figure: opposition
    poles: [encrypted, cleartext]
    positions:
      - { position: encrypted, complement: cleartext, meaning: "the payload is unreadable to anything between the two ends" }
      - { position: cleartext, complement: encrypted, meaning: "the payload is readable by anything on the path. The DEFAULT, deliberately: a channel nobody has said protects anything does not, and a default that assumed otherwise would report an estate safer than it is." }

  # == SEQUENCE ASPECTS (9.2, T0). No positions and no poles: a sequence is not a closed set of modalities
  # but a domain walked along lines.
  - aspect: time
    meaning: "when: a position on the one line everything that happens is ordered along"
    figure: sequence
    lines: 1
    metered: time
    order: partial          # two positions whose RESOLUTIONS overlap are unordered: `2026-09-19` (unit day) is
                            # neither before nor after `2026-09-19 22:50` (unit minute); it contains it
    acyclic: true
    ends: open
    domain: { systems: time }
  - aspect: place
    # SEMI-DEFINED (the operator's note, 2026-08-05): declared so the figure is proven against a second
    # aspect, and because civil time RESOLVES THROUGH place: an offset is a geographic fact. No term takes a
    # position on it yet; its lines are open because a filesystem tree, a site and a coordinate differ in how
    # many there are.
    meaning: "where: a position among the places a being can be, whether a coordinate, a site or a path in a tree"
    figure: sequence
    lines: open
    metered: none           # geographic coordinates are metered and containment is not; until a term needs
                            # the difference, the aspect claims no measure it cannot give every system
    order: partial          # containment orders a path within its tree and nothing across trees
    acyclic: true
    ends: bounded
    domain: { systems: place }
  - aspect: walk
    # THE `dag` RULE, RE-READ. A term whose schema says `dag: true` is a position on this aspect: its edges are
    # a sequence restricted to `acyclic`, and the gate refuses a cycle BECAUSE this row says acyclic, not
    # because code names the key. Nothing about the check changed; what changed is that acyclicity is now
    # one declared restriction of a sequence instead of the definition of walkable.
    meaning: "a relation a reader can walk from being to being without coming back: ownership, habitat, part-of, dependency"
    figure: sequence
    lines: 1
    metered: none
    order: partial
    acyclic: true
    ends: open
    term_key: dag           # a term carrying `dag: true` places its edges on this aspect
    domain: { systems: none }   # its positions are beans, not positions in an anchor system
  - aspect: routine
    # T4 (10.1): a procedure is a SEQUENCE OF STEPS, and the operator's own description of it (2026-08-05) is
    # the definition: "completely sequential even with branches, for example steps of a routine even with
    # their conditions". Lines are OPEN because a branch adds one. It is NOT acyclic: a routine may loop (retry
    # until it passes), which is exactly why acyclicity had to stop being the definition of walkable.
    # CLOSED NEIGHBOURHOODS, the third ply: a step's `next` is COMPLETE, these branches and no others, so the
    # gate can refuse a branch that points nowhere, a step nothing reaches, and a routine with no end.
    meaning: "the steps a procedure takes, the branches between them and the conditions that choose a branch"
    figure: sequence
    lines: open
    metered: none
    order: partial
    acyclic: false
    ends: bounded
    domain: { systems: none }   # its positions are the routine's own steps

# == PROFILES (added 2026-08-02, std-vocab@2.0 / P6 E4) ==
# Terms that are general to a KIND of garden rather than to all gardens. A garden opts in with
# `extends_profiles: [<name>]`; one that manages no code should not inherit code terms, and without
# profiles the only options were to force them on everyone or to leave them local forever.
# == KNOWLEDGE: published classifications as UNIVERSAL ANCHORS (9.1, the `knowledge` profile) ==
# A garden that records what a thing IS in the world's own terms — which field of knowledge a skill draws on,
# which occupation a role is, which technology a program is — should use codes every other garden uses too, so
# two gardens that never met agree that "ISCO-08 2522" and "Samba" are the same objects. The classifications
# are DATA the law points at, kept whole (every level) in seed/knowledge/, not restated in this prose.
registry_files:
  - { registry: isced-f-2013, file: seed/knowledge/isced-f-2013.tsv, key: code }
  - { registry: isco-08,      file: seed/knowledge/isco-08.tsv,      key: code }
  - { registry: technology,   file: seed/knowledge/technology.tsv,   key: code }
  - { registry: crosswalk-isco-08-isced-f-2013, file: seed/knowledge/crosswalk-isco-08-isced-f-2013.tsv, key: isco_08 }
knowledge_schemes:
  - scheme: isced-f-2013
    classifies: fields of knowledge (education and training)
    publisher: UNESCO Institute for Statistics
    url: "https://uis.unesco.org/en/topic/international-standard-classification-education-isced"
    levels: [broad, narrow, detailed]
    sources: seed/knowledge/SOURCES.md
  - scheme: isco-08
    classifies: occupations
    publisher: International Labour Organization
    url: "https://ilostat.ilo.org/methods/concepts-and-definitions/classification-occupation/"
    levels: [major, sub-major, minor, unit]
    sources: seed/knowledge/SOURCES.md
  - scheme: technology
    classifies: established technologies (software, protocols, operating systems), each with its OFFICIAL documentation
    publisher: daftar (curated; every row names the project's own documentation, never a third party's)
    url: "seed/knowledge/technology.tsv"
    levels: [flat]
    sources: seed/knowledge/SOURCES.md
profiles:
  code:
    meaning: "for a garden that manages source code: locating trees, and the repo identity of a code bean"
    vacancies:
    - at: code_paths.role
      position: vendored-dependency
      reason: prediction
      why: "No bean vendors a third-party tree into its own source today. Kept because vendoring is an ordinary state for a code estate, and without the position a vendored tree would be recorded as own-source, silently losing the distinction between code we wrote and code we merely carry."
    - at: code_paths.role
      position: generated-artifact
      reason: prediction
      why: "No bean records a build-output tree yet. Kept because an artifact tree must never be indexed as own-source: it is derived, so re-analysing it teaches nothing the source did not already say."
    terms:
    - term: code_paths
      # The 'paths vocab' (added 2026-08-01, human-directed): so an agent LOCATES code without re-walking a tree,
      # and knows which trees are REFERENCE-ONLY (never re-scanned each session).
      meaning: >
        The on-disk code trees a code bean is built from or references. Each entry is a CLASSED path so any
        agent locates code without re-walking a tree, and knows which trees are reference-only (never re-scanned
        each session — consult summary_ref + grep only for one specific symbol on demand).
      context_keys: ["code_paths"]
      schema:                                          # GATE (P2): enforced generically from here, not from code
        shape: list_of_entries
        required_on_kinds: [codebase]                  # a kind:codebase bean MUST carry a non-empty code_paths
        entry_required_attrs: [path, role, scan_policy]
        entry_values:
          role: [own-source, framework-reference, vendored-dependency, generated-artifact]
          scan_policy: [index, reference-only, skim]
        entry_soft_pattern:
          path: { pattern: '^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:([/A-Za-z]).*)$',
                  why: "a bare absolute path names no host: give it `root:<name>/…` (resolved by each host's `roots`) or `<host>:<path>`" }
      entry_attrs:
        path:        "WHERE THE TREE IS, as a position: `root:<name>[/<relative>]` resolved through each host's own `roots` map, or `<host>:<absolute path>` stated outright. A bare absolute path names no host and WARNS (11.0): this estate holds 13 paths that exist on two machines as two different trees, so a path with no host is a position in a system nobody named."
        role:        "own-source | framework-reference | vendored-dependency | generated-artifact"
        scan_policy: "index (own code — walk fully) | reference-only (do NOT re-scan each session; consult analysis_cache, grep on demand only) | skim (structure only)"
        stack:       "language/runtime tag, e.g. python-django | csharp-dotnet (optional)"
        entrypoint:  "manifest / solution / addin that roots the tree (optional)"
      # MOVED OUT 2026-08-02 (P1 / D6, human-ratified): `summary_ref` and `last_indexed` left this term and now
      # live in `analysis_cache`. Rationale (one-owner-of-a-fact): a summary is an ANALYSIS RESULT, not a property
      # of a filesystem path, and a date is a weaker staleness signal than the source's own git sha. code_paths
      # now does exactly ONE job — LOCATE the tree and say whether it may be walked. An analysis_cache entry
      # binds back to the tree it analysed via its `covers_paths`.
      agent_directive: >
        LATER AGENTS / OTHER MODELS: before scanning any code for this product, READ the owning bean's code_paths
        to LOCATE the tree, then READ its analysis_cache for a result that stands in for the scan. Treat
        scan_policy:reference-only trees (e.g. a vendored framework at /home/user/src/framework-17) as READ-BY-SUMMARY
        — do NOT walk them for general context; grep only when you need one specific symbol. Re-analyse a tree only
        when the covering analysis_cache entry has gone STALE (its staleness_key no longer matches the live source);
        then refresh that entry. This is how the garden avoids re-scanning 1.6 GB of framework code every session.
      merge: { cardinality: multi, order: by-path }
      exceptions: []
      promotion: { status: candidate, note: "reference-only scan-policy looks general (every estate has a big framework/vendor tree agents shouldn't re-walk) — REVIEW in the planned attrs-to-universal session" }
    - term: git_remote
      meaning: "a source repository's remote URL (the crypto/logical identity of a code tree)"
      context_keys: ["git_remote"]
      anchor: { class: logical, establishing: true }   # a remote URL is globally unique for the repo → establishes a codebase's identity
      merge: { cardinality: single, order: none }
      canonical: "verbatim remote string (e.g. host:path or scheme URL); lowercase host only"
      promotion: { status: candidate, note: "general (any code garden has repos) — REVIEW in the attrs-to-universal session" }
    - term: git_host
      meaning: "the being hosting the source repository of a code bean (storage habitat, not ownership)"
      context_keys: ["git_host"]
      schema: { shape: mapping, required_attrs: [bean], ref_fields: [self] }
      merge: { cardinality: single, order: none }

  network:
    meaning: >
      for a garden that manages machines that talk to each other: what a being ANSWERS ON, what it
      REACHES FOR, the LINKS those ride over, and what a forwarding device DOES to traffic in between.
      A garden with one host and no network should inherit none of it.
    vacancies:
    - at: net_protocol.values
      position: pptp
      reason: impossible
      why: >
        Nothing in this estate speaks it and nothing ever should. `impossible` rather than `prediction`,
        which is the whole point of registering it: MS-CHAPv2 and MPPE are broken by published attacks,
        so a pptp tunnel protects nothing while presenting as a VPN in every inventory that lists it.
        Measured: zero occurrences across the estate it was declared in. Declaring the
        position and refusing it is how the estate states a standing decision that would otherwise exist
        only as an absence — and an absence is indistinguishable from nobody having thought about it.
    - at: address_system.values
      position: ipv6
      reason: prediction
      why: >
        No being in this estate ANSWERS at a v6 address. Measured 2026-08-07 rather than assumed: a host
        booted with `ipv6.disable=1` records it as `capabilities.ipv6-socket-binding` with feasibility
        `impossible`, and the only v6 address anywhere in the corpus is `2001:db8::53` — a
        REMOTE resolver a VPS failed to reach, which is a fact about somebody else's endpoint and not
        about ours. `prediction` and not `impossible`: v6 is ordinary and arriving, and the position
        exists so that the day one endpoint takes it, the gate says the prediction came true instead of
        letting a whole address family appear with nothing noticing.
    terms:
    - term: address_system
      # The enum OWNER, exactly as `anchor_system` owns the anchor systems. Nothing else may list them:
      # this term's `values` are held equal to the registry by the gate's own drift check.
      meaning: "the address system a network position is stated in — the one owner of that enum"
      context_keys: [address_system]
      schema:
        shape: scalar
        values: [ipv4, ipv6]
        values_consistent_with: ["registry:address_systems[].system"]
      enforced_by: none   # never carried on a bean; it exists to OWN the enum `endpoints` and `links`
                          # select from, and its occupancy is counted through their entries.
      merge: { cardinality: single, order: none }
    - term: net_protocol
      # The second enum owner. Same contract, same reason.
      meaning: "a protocol a being may speak — the one owner of that enum"
      context_keys: [net_protocol]
      schema:
        shape: scalar
        values: [ssh, sftp, git, http, smtp, pop3, imap, smb, mysql, dns, ethernet, pppoe, wireguard, pptp]
        values_consistent_with: ["registry:net_protocols[].protocol"]
      enforced_by: none
      merge: { cardinality: single, order: none }
    - term: endpoints
      # WHAT A BEING ANSWERS ON. This is the half `ip` never had: an address with no protocol and no port
      # is a fact about a network interface, not about anything a being can reach. A mail server's
      # `details.boot_surface.mail_ports_expected` was straining toward this shape and could not get
      # there — it carries `{ port: 25, service: postscreen }` beside `port: "110/143/993/995"`, four
      # ports jammed into one string, and `service` naming IMPLEMENTATIONS where it means protocols.
      meaning: >
        The listening surfaces this being offers: for each, the protocol spoken, the address system and
        address it answers at, the port, and what the channel protects. An endpoint entry is a STATEMENT
        THAT THE BEING ANSWERS THERE — which is why a `forbidden` position on one is a breach by itself.
      context_keys: [endpoints]
      schema:
        shape: list_of_entries
        entry_required_attrs: [protocol, system, at]
        entry_in_registry:
          protocol: { registry: net_protocols,   take: protocol }
          system:   { registry: address_systems, take: system }
        entry_pattern_from_registry:
          { attr: at, registry: address_systems, keyed_by: system, take: pattern }
        entry_values:
          exposure: [loopback, lan, link, internet]
        entry_types: { observed: iso_date }
        on_aspect:
          - { aspect: confidentiality, attr: confidentiality, default: cleartext }
          - { aspect: capability,      attr: permission,      default: permitted }
        cross_aspect:
          in_breach:
            - { permission: forbidden,
                why: "a listening surface that MUST NOT exist, recorded as existing. Unlike a capability, an endpoint entry is not a stance about a possibility — it is a statement that the being answers there — so `forbidden` alone is the breach and needs no second aspect to confirm it. A database container published on 0.0.0.0:5432, reachable across the LAN, is this shape." }
            - { permission: required, confidentiality: cleartext,
                why: "a channel the estate REQUIRES and which protects nothing on the wire. A mail policy that forces cleartext delivery to a partner domain that mail must still reach is exactly this, so the requirement and the exposure are both real and neither can simply be withdrawn. KNOWN OVER-FIRE, stated rather than silently narrowed: a LOOPBACK endpoint satisfies this cell and is benign, because on loopback there is no path for anything to be on. `cross_aspect` combines aspect positions and cannot see `exposure`, which is an entry_value — so the cell cannot be made exposure-aware without a gate change. A reader meeting this warning on a loopback surface should reconcile it there, the way a DNS server's bean reconciles its recursion prohibition, rather than treat it as a finding." }
      entry_attrs:
        protocol:       "which protocol is spoken here — a row of net_protocols, never an implementation name"
        system:         "ipv4 | ipv6 — it selects the form `at` must take. Named `system` and not `address_system` to match `roots`, `located_at` and `timing`: `keyed_by` resolves a registry row by a field that must exist on BOTH the entry and the row, so the two are one name by construction. Getting it wrong produced 21 identical errors and no ambiguity about the cause."
        at:             "the address answered at, in that system's ONE canonical form"
        port:           "the TCP/UDP port. Omitted where the protocol rides another (sftp over ssh) and has none of its own."
        exposure:       "loopback (this machine only) | lan (the local segment) | link (reachable only over a named link, e.g. the wireguard tunnel) | internet (bound to a public address directly)"
        via_link:       "optional: the `links` key this surface is reachable over, when it is not reachable without it"
        confidentiality: "the position on the confidentiality aspect — what the channel protects. Defaults to cleartext, because a channel nobody has said protects anything does not."
        permission:     "the position on the capability aspect — whether this surface MAY exist at all"
        observed:       "ABSOLUTE date the surface was checked. Endpoints age faster than almost anything else here."
      merge: { cardinality: multi, order: "by-protocol+system+at+port?" }
    - term: links
      # A LINK IS A THING, NOT A SENTENCE. Today the estate's tunnels live as prose in `owns:` on three
      # beans, and the direct cost of that is on record: the router's `owns.wg_tunnel` said it dials
      # endpoint 203.0.113.19 while the VPS's `owns.wg_identity` said it dials .16 and listed .19 as a freed
      # spare. Two beans, the same scanning agent, one day apart, and the gate cannot see it because
      # `owns` has no rule to check. A link whose far end is a RESOLVED REF cannot contradict itself.
      meaning: >
        The links this being terminates: physical interfaces and the tunnels that manufacture one. A
        tunnel is not a special case here — it is a link whose `protocol` row declares
        `synthesizes_link`, which is what lets other traffic be recorded as riding it.
      context_keys: [links]
      schema:
        shape: open_map_of_entries
        key_form: kebab
        entry_required_attrs: [protocol]
        entry_in_registry:
          protocol: { registry: net_protocols, take: protocol }
        entry_ref_fields: [peer]
        entry_types: { observed: iso_date }
        on_aspect:
          - { aspect: confidentiality, attr: confidentiality, default: cleartext }
      entry_attrs:
        protocol:   "what makes this link — wireguard for a tunnel, and a physical row where one exists"
        peer:       "a {bean, field} ref to the far end. A REF, not a retyped address: this is the field whose absence produced the .169/.146 contradiction."
        carried_by: "optional: the `links` entry this one rides over — a tunnel rides a WAN link rides an interface"
        confidentiality: "what the link protects, for everything carried over it"
        observed:   "ABSOLUTE date the link was checked"
      dag_note: >
        NOTHING HERE IS ACYCLIC, and the first draft of this term got that wrong twice in one line. It
        carried `dag: true` over `peer` and `carried_by`, and the design review caught both before any bean
        was written. `peer` is MUTUAL — a router peers a VPS and the VPS peers the router — so the acyclic check
        would have refused the very first tunnel recorded honestly: a rule made unsatisfiable by its own
        subject matter. `carried_by` names another entry on THE SAME bean, so it is not a cross-bean edge
        and there is no graph to walk; it is documented ordering, and `entry_ref_fields` deliberately omits
        it. PROTOCOL carriage is separately and permanently not acyclic — wireguard is carried by udp over
        ipv4 and then carries ipv4, because that recursion is what encapsulation IS — which is why
        `rides_on` in the registry is descriptive and joins no check. Written at this length because a rule
        that cannot be satisfied is worse than no rule: it is the failure `inverse_of` already carries a
        cardinality to avoid, met twice more in a single term.
      merge: { cardinality: multi, order: by-key }
    - term: reaches
      # WHAT A BEING NEEDS TO TALK TO. Deliberately NOT a dag: a server reaches its router and the router reaches
      # the server, and that is ordinary rather than a cycle to be refused.
      meaning: >
        The beings this one must be able to reach in order to work, each naming the protocol it reaches
        for and how badly it needs it. It takes positions on the EXISTING `necessity` aspect, because
        needing a network peer is not a new modality — it is what `consumes` and `depends_on` already are.
      context_keys: [reaches]
      schema:
        shape: open_map_of_entries
        key_form: kebab
        entry_required_attrs: [protocol]
        entry_in_registry:
          protocol: { registry: net_protocols, take: protocol }
        entry_ref_fields: [target]
        entry_types: { observed: iso_date }
        on_aspect:
          - { aspect: necessity, attr: necessity, default: necessary }
      entry_attrs:
        protocol:  "what it speaks to get there"
        target:    "a {bean[, field]} ref to what it reaches. A ref rather than an address, so the far end stays the one owner of its own address."
        via_link:  "optional: the link this reach must cross"
        necessity: "the position on the necessity aspect — `necessary` if the being cannot do its work without it"
        observed:  "ABSOLUTE date the reach was verified to work"
      merge: { cardinality: multi, order: by-key }
    - term: treatments
      # NOT A LAYER, AND KEPT OUT OF THE STACK ON PURPOSE. routes, nat, mangle and acl are not positions
      # in a protocol stack — they are what a forwarding device DOES to traffic that is passing through
      # it. Folding them into `endpoints` or `links` would be the force-fit that ground rule 2 forbids:
      # the shape would be satisfied and it would be the wrong shape.
      meaning: >
        What a forwarding device does to traffic crossing it: the routes, address translations, packet
        marks and access lists that decide where something goes and whether it arrives at all. Required
        on a router, because a router that documents no treatment has documented nothing about itself.
      context_keys: [treatments]
      schema:
        shape: list_of_entries
        required_on_roles: [router]   # 7.0: was `required_on_kinds: [router]` until `router` stopped being a kind
        entry_required_attrs: [kind, what, why]
        entry_values:
          kind: [route, nat, mangle, acl, queue]
        entry_ref_fields: [to]
        entry_types: { observed: iso_date }
        on_aspect:
          - { aspect: capability, attr: permission, default: permitted }
      entry_attrs:
        kind:  "route (where traffic goes) | nat (what its addresses become) | mangle (what marks it carries) | acl (whether it is allowed at all) | queue (what bandwidth it gets)"
        what:  "the treatment itself, briefly. A POINTER to the device's own config, never a copy of it — ground rule 3: the router owns its rules and they are not hand-edited from here."
        why:   "what breaks if it is removed. This is the load-bearing attr: a treatment with no stated consequence is an inventory row, and inventory is what the device's own export already gives you."
        to:    "optional: a {bean, field} ref to where the treatment sends traffic"
        permission: "the position on the capability aspect. `required` is the one that earns this term: a server's outbound SPF identity can DEPEND on firewall mangle marks, and today that is a prose safety note nothing enforces."
        observed: "ABSOLUTE date the treatment was read off the device"
      merge: { cardinality: multi, order: by-kind+what }
  domain:
    meaning: >
      for a garden that holds delegated names — registered domains. The one class of fact that can lose a name
      outright is its registration: an unrenewed domain takes its DNS and its mail with it. A garden with no
      domains should inherit none of it.
    terms:
    - term: registration
      # PROMOTED 2026-09-17 (human-ratified, std-vocab 8.2) from one garden's local vocabulary, where it had been
      # a candidate "to revisit with a second garden that has domains". A cold-start drill garden modelled a
      # domain and had nowhere standard to put its registrar or expiry. A PROFILE, not the core: a garden
      # with no domains inherits neither the term nor its requirement.
      meaning: "the registration facts of a delegated name: who holds the record, when it lapses, and when that was last observed"
      context_keys: ["registration"]
      schema:
        shape: mapping
        required_on_kinds: [domain]
        required_attrs: [registrar, created, expires, auto_renew, observed, source]
        attr_types: { created: iso_date, expires: iso_date, observed: iso_date }
        # WHICH DATE AGES, said here rather than in the tool. bin/dmstale.py named `registration` and
        # `expires` in its own source until 2026-09-20: this term was born garden-local with the tool
        # extended for it the same day, and when it was promoted to Tier-0 nobody went back. A garden
        # that invents a term with an expiry got no warning, however well the gate enforced the date —
        # first-class to the gate, invisible to the tool that would have made it useful.
        expiry:
          attr: expires
          notice: { of: time, measure: { count: 90, unit: day } }
          why: "an unrenewed name takes its DNS and its mail with it"
      attrs:
        registrar:  "the registrar of record — who the renewal is actually paid to"
        registrant: "optional: the party holding the registration, where the registry discloses it"
        created:    "ABSOLUTE date the registration began"
        expires:    "ABSOLUTE date it lapses if unrenewed — the fact that can lose the name"
        auto_renew: "enabled | disabled | unknown. `unknown` is the honest default: it is a registrar-ACCOUNT setting and does not appear in WHOIS, so it cannot be observed the way the dates can."
        observed:   "ABSOLUTE date these facts were read. They age: an expiry moves on renewal, and a registrar changes on transfer."
        source:     "where they were read from"
      merge: { cardinality: single, order: none }

  knowledge:
    meaning: >
      for a garden that says what things ARE in the world's shared terms: the field of knowledge a skill or a
      technology draws on (ISCED-F 2013), the occupation a role or a person's work is (ISCO-08), and the
      established technology a program, instance or host runs (with its official documentation). The codes are
      UNIVERSAL ANCHORS: the same in every garden, so knowledge merges across gardens that never met.
    terms:
    - term: isced_f_2013
      meaning: "an ISCED-F 2013 field code (UNESCO) — a being that IS a field of knowledge, e.g. a course or a body of practice"
      context_keys: ["isced_f_2013", "identity.anchors[].isced_f_2013"]
      schema:
        governs_anchor: isced_f_2013
        value_pattern: '^[0-9]{2,4}$'
        canonical_note: "the code as published: 2 digits broad, 3 narrow, 4 detailed"
        value_in_registry: { registry: isced-f-2013, take: code }
      anchor: { class: logical, establishing: true }
      merge: { cardinality: single, order: none }
    - term: isco_08
      meaning: "an ISCO-08 occupation code (ILO) — a being that IS an occupation or a role classified as one"
      context_keys: ["isco_08", "identity.anchors[].isco_08"]
      schema:
        governs_anchor: isco_08
        value_pattern: '^[0-9]{1,4}$'
        canonical_note: "the code as published: 1 digit major, 2 sub-major, 3 minor, 4 unit group"
        value_in_registry: { registry: isco-08, take: code }
      anchor: { class: logical, establishing: true }
      merge: { cardinality: single, order: none }
    - term: technology
      meaning: "a technology code from seed/knowledge/technology.tsv — a being that IS that technology (a third-party product bean, typically)"
      context_keys: ["technology", "identity.anchors[].technology"]
      schema:
        governs_anchor: technology
        value_pattern: '^[a-z0-9][a-z0-9-]*$'
        canonical_note: "kebab-case, as in seed/knowledge/technology.tsv"
        value_in_registry: { registry: technology, take: code }
      anchor: { class: logical, establishing: true }
      merge: { cardinality: single, order: none }
    - term: knowledge
      # THE RELATION TO KNOWLEDGE. A bean that is not itself a field, an occupation or a technology still stands
      # in relation to them: a Samba instance USES the technology samba; a mail-filtering design DRAWS ON the
      # field 0612; a person's role is CLASSIFIED AS 2522. One term for every scheme: the entry names its scheme
      # and the gate checks the code against THAT scheme's registry. `topic` names the concept inside the field
      # ("fluid pressure and flow" for espresso, inside physics) — the overlap between domains is the point.
      meaning: "how this being stands to published knowledge: classified as an occupation, drawing on a field, using a technology"
      context_keys: [knowledge]
      schema:
        shape: list_of_entries
        entry_required_attrs: [scheme, code, rel]
        entry_values:
          rel: [classified_as, draws_on, uses]
        entry_in_registry:
          scheme: { registry: knowledge_schemes, take: scheme }
          code:   { registry_from: scheme, take: code }
      attrs:
        scheme: "which classification: isced-f-2013, isco-08, technology"
        code:   "the code in it"
        rel:    "classified_as (this IS of that kind) | draws_on (this rests on that knowledge) | uses (this runs that technology)"
        topic:  "optional: the concept inside the field this draws on"
        note:   "optional"
      merge: { cardinality: multi, order: by-scheme+code+rel }

terms:
  - term: capabilities
    # Open key, closed figure — the same shape as analysis_cache, which is the proven pattern here: a NEW
    # capability needs no rule-change, while the STANCE taken on it must sit on the figure. This is where
    # a prohibition stops being a prose safety note and becomes something the gate carries.
    meaning: "what this being may or must be able to do: an OPEN map of capability name -> the stance taken on it"
    context_keys: ["capabilities"]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [why]        # a stance with no reason is folklore; the reason IS the fact
      on_aspect:                                   # TWO aspects: what is ALLOWED, and what is SO
        - { aspect: capability,  attr: permission,  default: permitted }
        - { aspect: feasibility, attr: feasibility, default: possible }
      cross_aspect:
        # Two squares span a GRID, and the grid has cells NEITHER square can see. Checking each aspect
        # alone permits both kinds below. The split matters: one pair cannot both be true, the other pair
        # can and is simply bad.
        incoherent:                                # an ERROR: one of the two positions is mis-stated
          - { permission: required,  feasibility: impossible,
              why: "an unsatisfiable requirement — it must be had and cannot be. Either the requirement is not real, or the impossibility is not, and until that is resolved the entry asserts a contradiction." }
          - { permission: forbidden, feasibility: necessary,
              why: "an unenforceable prohibition — it must not be had and unavoidably is. A rule that cannot be obeyed is not a rule; the being needs a different mitigation, or the necessity is overstated." }
        in_breach:                                 # a WARNING: both CAN hold; the state needs action
          - { permission: required,  feasibility: possible,
              why: "REQUIRED but NOT CURRENTLY THE CASE — the requirement is unmet right now." }
          - { permission: forbidden, feasibility: contingent,
              why: "FORBIDDEN but CURRENTLY THE CASE — the prohibition is being violated right now." }
    entry_attrs:
      permission: "the position taken on the capability aspect (required | omissible | permitted | forbidden)"
      feasibility: "the position on the feasibility aspect — whether the being CAN be in that state at all, independent of whether it may. `forbidden` + `possible` is a live risk; `forbidden` + `impossible` is already prevented by something else."
      why:        "WHY this stance holds — the consequence of violating it, in prose an operator can act on"
      by:         "optional: who imposes it, when the enforcer is not us (e.g. a hosting provider)"
    merge: { cardinality: multi, order: by-capability }
  - term: consumes
    # SETTLED at 2.1. The v2 plan proposed retiring it as unused; it had a live occupant, and the operator
    # assigned it a home: "consumption is going to be necessity aspect". It is now a position-bearing
    # relation ON that aspect rather than a standalone edge, which is what unblocked its promotion — it was
    # the one term 2.0 deferred for INSTABILITY rather than scope.
    meaning: "an input this being requires — the produced state of another being that it reads to do its work"
    context_keys: ["consumes"]
    schema:
      shape: list_of_entries
      entry_ref_fields: [self]
      on_aspect: { aspect: necessity, default: necessary }   # an input is needed unless an edge says otherwise
    merge: { cardinality: multi, order: "by-bean?+mapping?+field?" }
  - term: refs
    # THE OPEN RESIDUAL. Any edge that is not one of the canonical relations above lives here, and MUST
    # name its own relation via `rel:`. The KEY is a slot label (it may be arbitrary, e.g. `party_acme`);
    # `rel:` is the relation TYPE, so an edge read alone still says what it is. `rel` is OPEN and kebab —
    # deliberately NOT an enum, for the same reason analysis_cache's cache_type is not one: a new kind of
    # relation must never require a rule-change. It is therefore outside the reverse gate by design.
    meaning: "the open residual relation: any typed edge outside the canonical set, self-described by `rel`"
    context_keys: ["refs"]
    schema:
      shape: open_map_of_entries
      entry_required_attrs: [rel]
      entry_types: { rel: kebab }
      entry_ref_fields: [self]
    merge: { cardinality: multi, order: by-key }
# LOCAL kinds: object types this garden manages that std-vocab doesn't schematize. Each gets a small schema
# (MODEL Rule 6). A kind that proves general is promoted alongside its terms.
  - term: depends_on
    meaning: "a being this being requires to function; recovery ordering reads this edge"
    context_keys: ["depends_on"]
    schema:
      shape: open_map_of_entries
      entry_ref_fields: [self]
      dag: true
      on_aspect: { aspect: necessity, default: necessary }   # the sibling of `consumes`: depends_on needs
                                                             # a BEING, consumes needs its PRODUCED STATE
    merge: { cardinality: multi, order: by-bean }
  # == CORE GRAMMAR ENUMS (promoted 2026-08-02, std-vocab@2.0 / P6 E3) ==
  # These were CODE CONSTANTS in bin/dmcheck.py (STATUSES, ID_STATUS, ANCHOR_CLASSES, AUTHORITY, SRC) —
  # the last place in the system where a type rule lived outside the vocabulary. Absorbing them completes
  # D4 ("type rules live in the VOCAB, not code"). Each is addressed by `path:`, because these are NESTED
  # fields rather than top-level terms. MAJOR: two of them were WARNINGS in code and are ERRORS now, and a
  # garden using a value not listed here will be rejected where it previously passed.
  - term: status
    meaning: "the lifecycle state of a bean"
    context_keys: ["status"]
    # `closed` ADDED 7.0 (2026-08-07, human-ratified). A bounded piece of work that FINISHED is not
    # `deprecated` — deprecated means superseded, still present, and not to be relied on, which is a
    # judgement about something that continues to exist. A session that did its work and stopped has no
    # such shadow over it. The estate had no word for the difference and both wrong answers were already
    # in the corpus: one session bean called itself `deprecated`, which reads as though
    # its work were discredited, and another stayed `active` indefinitely, which
    # reads as though it were still running. The second is the more dangerous of the two — a reader
    # scanning for live sessions would find a ghost.
    # SCOPED BY SENSE, NOT BY RULE: `closed` belongs to kinds that BOUND their work — session, program,
    # contract. Nothing forbids it elsewhere and nothing should invent a per-kind status mechanism to try;
    # `draft` has always been equally meaningless on a host and has never needed guarding.
    schema:
      path: status
      values: [active, planned, at-risk, deprecated, draft, closed]
    # Two gardens disagreeing about a being's lifecycle state is a real disagreement about the world,
    # so it surfaces as a conflict rather than one of them quietly winning.
    merge: { cardinality: single, order: none }
  - term: identity_status
    meaning: "whether a bean's identity is established or still provisional (MERGE.md §4)"
    context_keys: ["identity.status"]
    schema:
      path: identity.status
      values: [confirmed, provisional]
  - term: anchor_class
    meaning: "the HINT at why an anchor establishes or corroborates. Since P4 it decides nothing — `establishing` does — but it remains useful provenance about the KIND of evidence."
    context_keys: ["identity.anchors[].class"]
    schema:
      path: identity.anchors[].class
      values: [hardware, logical, network, role, none]
  - term: anchor_authority
    meaning: "how much weight an anchor's value carries on merge"
    context_keys: ["identity.anchors[].authority"]
    schema:
      path: identity.anchors[].authority
      values: [scanned, operator-asserted, external]
    merge: { order: "scanned<operator-asserted<external" }
  - term: provenance_src
    meaning: "how a fact came to be known. `inferred` may NEVER auto-override `asserted-by-human` (MODEL Rule: the provenance guard)."
    context_keys: ["provenance.src"]
    schema:
      path: provenance.src
      values: [observed, inferred, asserted-by-human, generated-by-tool]
  - term: analysis_cache
    # Design step D6, executed as P1 (2026-08-02, human-ratified rule-change).
    # An OPEN, TYPED, bean-level cache of ANALYSIS RESULTS, so an agent READS a recorded result instead of
    # re-deriving it. Adding a NEW <cache_type> requires NO schema change and NO bean restructure — that is the
    # whole point of the term: the garden can start caching a new kind of code/analysis (a new language, a new
    # lens) forever, without a future migration.
    meaning: >
      An OPEN map of typed, provenance-stamped, staleness-keyed analysis results, held on the bean that owns the
      analysed thing. Each entry STANDS IN FOR re-running that analysis for as long as its staleness_key still
      matches the live source; once the key moves, the entry is STALE and must not be trusted.
    context_keys: ["analysis_cache"]
    schema:                                         # GATE (P2): enforced generically from here, not from code
      shape: open_map_of_entries                    # NB the KEY is open: no `values`/`values_from` is declared for it,
      key_form: kebab                               # so the gate can only ever require kebab-case, never a fixed list.
      required_on_kinds: [codebase]                 # a kind:codebase bean MUST carry a non-empty analysis_cache
      entry_required_attrs: [produced_by, as_of, staleness_key, policy]
      entry_values:
        policy: [index, reference-only, skim]
        form:   [summary_ref, inline, external]
      entry_types: { as_of: iso_date }              # Rule 6: absolute dates only
      entry_pattern:
        # 11.0: a staleness key is a POSITION, and `git-head:<sha>` was resolved against whatever tree the
        # READER had checked out — one analysis, one verdict per machine. The git-object-graph form names the
        # repository, so every reader asks the same object graph. `manual:<why>` stays for what no key can track.
        staleness_key: '^([a-z0-9][a-z0-9._-]*@[0-9a-f]{7,40}|manual:.+)$'
      entry_soft_pattern:
        covers_paths: { pattern: '^(root:[a-z0-9][a-z0-9-]*(/[^:]*)?|[a-z0-9][a-z0-9.-]*:([/A-Za-z]).*)$',
                        why: "a bare absolute path names no host — the same defect `code_paths.path` carries" }
      entry_required_if:
        - { attr: form, equals: summary_ref, requires: [summary_ref] }
      entry_expect_if:
        - { attr: staleness_key, starts_with: "manual:", expects: covers_paths,
            why: "an agent cannot tell where to re-check it" }
      pointer_fields: { summary_ref: bean_field_pointer }
    open_keys: true                                 # restated for the human reader; the gate reads schema.key_form
    key_note: >
      kebab-case <cache_type>. Known types so far (a NON-exhaustive registry, NOT an enum the gate enforces):
      code-structure | framework-surface | api-surface | api-client-contract | security-surface | bcf-domain.
      Anticipated: dep-graph | sql-schema | revit-ui | csharp-api | python-models | test-coverage.
    entry_attrs:                                    # human documentation; the GATE reads schema: above
      produced_by:    "the agent/tool id that produced this analysis (provenance — who to ask, who to blame)"
      as_of:          "ABSOLUTE date the analysis was produced, YYYY-MM-DD (Rule 6 paper-durable)"
      staleness_key:  "the value that makes this entry VALID; when it MOVES, the entry is STALE. The FORM is
                       `entry_pattern.staleness_key` above and is not restated here: `<repo>@<object-id>`,
                       a position in a named repository's object graph, or `manual:<why>` for what no key
                       can track. Until 2026-09-20 this line listed three spellings — the git-head, the
                       digest and the manual one — two of which the pattern eighteen lines above had
                       already refused since 11.0. A person reading the term was taught the form the gate
                       rejects, which is the same defect as a law the code ignores, pointing the other
                       way. (The superseded wording is in git, and is deliberately NOT quoted here: a
                       document that quotes a spelling it is abolishing still contains it, and the check
                       in test/place.py cannot tell a quotation from a lesson. Nor should it have to.)"
      policy:         "index | reference-only | skim — how the analysed source is to be treated"
      form:           "summary_ref | inline | external — where the cached result physically lives"
      summary_ref:    "REQUIRED when form: summary_ref. A pointer, or a list of pointers, to the recorded result. Each pointer is either '<section>.<key>' (a field on THIS bean, gate-resolved), or {bean: <id>, field: <key>} (a field on ANOTHER bean, gate-resolved), or 'file:<path>' (an on-disk document)."
      covers_paths:   "the code_paths path(s) this entry analysed — this is WHERE an agent re-checks staleness_key"
      relevant_scope: "optional: which part of a large covered tree matters to THIS bean (e.g. 'CE module: hr')"
      digest:         "optional short content hash of the cached result itself"
    staleness_rule: >
      An entry is VALID only while its staleness_key matches the live source at covers_paths. A STALE entry is
      NEVER silently used: re-run the analysis, then REFRESH the entry (new as_of + new staleness_key). Trusting
      a stale entry is a provenance violation, not a shortcut.
    agent_directive: >
      LATER AGENTS / OTHER MODELS: BEFORE analysing any code for this bean, READ analysis_cache. If an entry of the
      type you need exists AND its staleness_key still matches the live source at covers_paths, USE IT — do not
      re-derive it. Re-analyse ONLY when the key has moved, or when no entry of that type exists; then WRITE BACK a
      refreshed entry (bump as_of + staleness_key). To start caching a NEW kind of analysis, simply add a new
      kebab-case <cache_type> key — no VOCAB change, no gate change, no bean restructure is ever required.
    merge: { cardinality: multi, order: by-cache-type }
    exceptions: []
    promotion: { status: candidate, note: "strongly general — every garden with code wants typed, staleness-keyed, re-usable analysis. Propose to std-vocab in the P6 promotion review." }
  - term: nature
    # Ontological type of a being — the routing key from a bean up to the ownership crown (MODEL §Ownership).
    # physical -> nature (res extensa), metaphysical -> logos (res cogitans), living -> love (conatus);
    # all resolve up to god (Deus sive Natura). The crown is a MODEL axiom, NOT instantiated as beans.
    meaning: "the ontological category of a being; routes it to the correct branch of the ownership crown"
    context_keys: ["nature"]
    schema:                                          # GATE (P2 interpreter; P3 made it the root axiom)
      shape: scalar
      values: [physical, metaphysical, living]       # also the enum other terms reuse via values_from: nature
      values_consistent_with: ["registry:natures[].nature"]   # the enum IS the natures registry above
      required: true                                 # P3/D1: MANDATORY on every bean, whatever its kind
      must_equal_kind_attr: of_nature                # and it must agree with the kind that refines it
    merge: { cardinality: single, order: none }
    promotion: { status: candidate, note: "universal ontology (Spinoza crown) — review in attrs-to-universal session" }
  - term: owned_by
    # Faceted ownership. ONE owner per facet (the 'one and only one owner' law, held per facet).
    # Co-ownership of a SINGLE facet is never a raw fact -> a `contract` bean (agreement_ref + conflict_rule).
    meaning: "who owns a being, per facet; introduced (explicit) at a node and inherited down the tree"
    context_keys: ["owned_by"]
    schema:                                          # GATE (P2): enforced generically from here, not from code
      shape: mapping
      required_on_kinds: [product, codebase, instance, org]
      alt_form: { key: via, ref_fields: [via] }      # the INHERITED form: a single `via` ref, no facets
      key_form: values_from:facets                   # otherwise every key must be a declared facet
      entry_one_of: [owner, contract, external, crown]   # a bean, a contract, outside, or the axiom itself
      entry_ref_fields: [owner, contract]            # `external` and `crown` resolve to no bean by design
      entry_must_match:                              # the branch is NOT free: nature routes it
        - { attr: crown, registry: natures, keyed_by: nature, take: crown }
      entry_form_from_kind_attr: ownership_form      # a kind may PIN which form it must use (see kind: person)
      dag: true                                      # ownership must stay acyclic
    forms:
      explicit:  "owned_by: { <facet>: { owner: {bean: <person|org>} }, ... }   # introduce facet-owners here"
      inherited: "owned_by: { via: {bean: <parent>} }                           # inherit parent's facet-owners"
      co_owned:  "owned_by: { <facet>: { contract: {bean: <contract>} } }       # a SINGLE facet co-owned -> a contract resolves it"
      external:  "owned_by: { <facet>: { external: '<who>' } }                  # owned OUTSIDE this garden (third-party software, a vendor); names the owner in prose because they are not a managed object here"
      crown:     "owned_by: { <facet>: { crown: <branch> } }                     # ownership TERMINATES at the axiom; the branch must be the one this bean's nature routes to"
    merge: { cardinality: multi, order: by-facet }
    promotion: { status: candidate, note: "universal — review in attrs-to-universal session" }
  - term: responsibility
    # P7 (2026-08-02, human-ratified). THE CLOSING ARC. Operator: "the ownership is trapped in the same
    # paradox isn't it? ... ownership is only meaningful where the responsibility covers on the opposite
    # aspect." `owned_by` alone is one-directional — a being points UP to its owner, up to the crown. That
    # is one arc of a loop, and P5's `external` form made the gap visible: BIND terminates in prose at
    # neither a bean nor the crown. Responsibility is the OPPOSITE arc, the holder answering DOWN for the
    # being. Together they close. `external` then stops being an escape hatch and becomes an ordinary
    # position: owned outside, answered for inside — which is the true statement about every third-party
    # thing this estate runs.
    meaning: "who ANSWERS FOR this being, per facet — the arc that makes an ownership claim actionable"
    context_keys: ["responsibility"]
    schema:
      shape: mapping
      alt_form: { key: via, ref_fields: [via] }      # inherited, exactly as ownership inherits
      key_form: values_from:facets                   # the SAME facet lattice — the two arcs pair per facet
      entry_one_of: [holder, contract, external, self]   # NB no `crown`: the crown owns but never answers
      entry_ref_fields: [holder, contract]
      facet_parity_with: owned_by                    # the loop must CLOSE: same facets on both arcs
      dag: true
    forms:
      explicit:  "responsibility: { <facet>: { holder: {bean: <person|org>} } }"
      inherited: "responsibility: { via: {bean: <parent>} }"
      shared:    "responsibility: { <facet>: { contract: {bean: <contract>} } }   # shared duty -> a contract, as with co-ownership"
      external:  "responsibility: { <facet>: { external: '<who>' } }              # answered for outside this garden"
      self:      "responsibility: { <facet>: { self: true } }                      # a being answers for ITSELF (persons). Reflexive, so it is deliberately NOT an edge — a self-edge would be a cycle, and autonomy is not a dependency."
    rules:
      parity: "every facet with an OWNER must have a HOLDER and vice versa. An ownership claim nothing answers for is a loose end; a duty nobody owns is orphaned."
      not_the_same_as_ownership: "they are opposite arcs, not synonyms. A rented VPS is owned by the provider and answered for by the operator; that is the normal case, not an exception."
    merge: { cardinality: multi, order: by-facet }
    promotion: { status: candidate, note: "prerequisite for promoting owned_by (see design-std-vocab-promotion B3) — owned_by cannot go to Tier-0 while its external form dangles" }
  - term: facets
    # The ownership-facet lattice: DISTINGUISHABLE (crisp boundary; resolve overlap by a depends_on edge or
    # boundary refinement, NEVER ambiguous double-coverage), DEPENDENCY-bearing (DAG), and RECURSIVE
    # (a facet may decompose into sub-facets, ownership recursing within).
    meaning: "the typed lattice of ownership facets used by owned_by"
    context_keys: ["facets"]
    enforced_by: none      # AT TIER-0 there is nothing to check: this term defines the lattice RULES
                           # (below) but declares no values, because `legal`/`technical` are defensible
                           # universals while the extensible three are unoccupied predictions. A garden
                           # supplying values inherits the drift guard through its overlay, and that IS
                           # enforced there. Left as an empty `schema:` key by the 1.1 promotion until
                           # golden V5 caught it — a term that states no rule and no reason is exactly
                           # the silent gap this release exists to remove.
                                                     # values_from:facets)
                                                     # definition below, so the two can never drift apart.
    # NB: 'facilitation of creation/production' is NOT modelled as an ownership facet — a facilitator is a
    # HABITAT the creation act lived in (lives_in, time-windowed), and any equal-sharing of that facilitator
    # stake is captured by a `contract` over the creation aspect. Kept lean on purpose.
    rules:
      distinguishable: "each facet has a crisp boundary; resolve overlap by a depends_on edge or boundary refinement, never double-coverage"
      dependency: "facets form a DAG via depends_on"
      recursive: "a facet may decompose into sub-facets (e.g. technical -> {operational, architectural, data})"
    promotion: { status: candidate }
  - term: instance_of
    meaning: "the code product a running instance (token) instantiates"
    context_keys: ["instance_of"]
    schema:                                          # GATE (P2): enforced generically from here, not from code
      shape: mapping
      required_on_kinds: [instance]
      required_attrs: [bean]
      ref_fields: [self]                             # the mapping IS the ref
    form: "instance_of: {bean: <product|codebase>}"
    merge: { cardinality: single, order: none }
    promotion: { status: candidate }
  - term: lives_in
    # Habitat / containment stack — RECURSIVE and typed; DISTINCT from ownership (a token is NOT owned by its
    # host). e.g. addon-token lives_in odoo-instance lives_in host{linux-baremetal|docker|windows|odoo.sh}.
    meaning: "the immediate habitat a token lives in/on; recursive (habitat may itself be a token); a DAG"
    context_keys: ["lives_in"]
    schema:                                          # GATE (P2): enforced generically from here, not from code
      shape: mapping
      required_on_kinds: [instance]
      required_attrs: [bean]
      ref_fields: [self]                             # the mapping IS the ref
      dag: true                                      # habitat containment must stay acyclic
    form: "lives_in: {bean: <habitat>}   # follow the chain for the full stack"
    # habitat_types MOVED to the `provides_habitat` term below (P5): the list had no bean field, so a
    # habitat's TYPE could not be recorded at all — the hole the reverse gate found on its first run.
    merge: { cardinality: single, order: none }
    promotion: { status: candidate, note: "universal containment (vps-on-provider, container-on-host, addon-in-odoo) — review later" }
  - term: provides_habitat
    # P5/D5. Closes the hole the reverse gate found in P3.5: `lives_in` names WHICH being a token lives in
    # but never WHAT SORT of habitat that being is. The type belongs to the habitat, not to the lodger —
    # a VPS is a linux habitat whoever lives on it — so it is declared here and required on any bean that
    # is actually the target of a lives_in edge. A habitat can no longer be untyped.
    meaning: "the kind of habitat this being offers to the tokens that live in it"
    context_keys: ["provides_habitat"]
    schema:
      shape: scalar
      # values: GARDEN-LOCAL. Habitat TYPING is universal; `odoo-instance` and `odoo.sh-subscription` are not (P6/B2).
      required_on_targets_of: lives_in
    merge: { cardinality: single, order: none }
    promotion: { status: candidate, note: "universal containment typing — review at P6" }
  - term: part_of
    meaning: "the whole this being is a component of (composition; a being is part_of at most one whole)"
    context_keys: ["part_of"]
    schema: { shape: mapping, required_attrs: [bean], ref_fields: [self], dag: true }
    merge: { cardinality: single, order: none }
    promotion: { status: candidate, note: "universal composition — review at P6" }
  - term: creator
    # DISTINCT from owned_by.legal.owner even though creation CONFERS legal ownership (VOCAB facets.legal):
    # they coincide across this estate today, but a transfer would separate them and the creation fact must
    # survive it. Recording both is therefore not a duplicate authoritative fact.
    meaning: "the being that made this being"
    context_keys: ["creator"]
    schema: { shape: mapping, required_attrs: [bean], ref_fields: [self] }
    merge: { cardinality: single, order: none }
  - term: ip
    meaning: "an Internet Protocol address identifying a network interface/endpoint"
    context_keys: ["*_ip", "*_ips", "provides_ip", "identifiers.ipv4", "identifiers.ipv6"]
    schema:
      governs_anchor: ip
      value_form: ip        # needs real parsing, not a regex — the `canonical` rule is 'python ipaddress normal form'
    anchor: { class: network, establishing: false }        # reassignable (DHCP/NAT/reuse) → corroborating only, never sole
    merge: { cardinality: single, order: cidr, authority: "scanned<operator-asserted<external" }
    canonical: "python ipaddress normal form (v4/v6); reject bad octets"
    escape: "bean `shared_identifiers:` (floating/VRRP/anycast) or `scope:`/`network:` (reused private range)"
    exceptions:
      - { case: "shared/floating/VRRP/anycast IP", decision: "co-owned; own-bean+ref OR shared_identifiers", why: "many nodes answer for one address", acked: 2026-07-31 }
      - { case: "reused RFC1918 range on isolated LANs", decision: "qualify with scope/network", why: "private ranges exist independently", acked: 2026-07-31 }
      - { case: "dotted-quad that is NOT an ip (v17.0.0.0, CIDR base)", decision: "only values under context_keys are ips; parse with ipaddress", why: "free-text mis-read as IPs", acked: 2026-07-31 }
      - { case: "IPv6 / abbreviated shorthand (.160)", decision: "canonical full form required; ipv6 deduped", why: "invisible to IPv4-only check", acked: 2026-07-31 }
  - term: hostname
    meaning: "a machine's OS hostname"
    context_keys: ["hostname", "identity.anchors[].hostname"]
    schema:
      governs_anchor: hostname
      value_pattern: '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$'
      canonical_note: "lowercase; one label or dotted"
    anchor: { class: network, establishing: false }        # reassignable
    merge: { cardinality: single, order: none }
    canonical: "lowercase"
  - term: fqdn
    meaning: "a DNS-unique fully-qualified domain name"
    context_keys: ["fqdn"]
    schema:
      governs_anchor: fqdn
      value_pattern: '^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$'
      canonical_note: "IDNA + lowercase; at least two labels"
    anchor: { class: logical, establishing: true }         # DNS-unique within its namespace
    merge: { cardinality: single, order: none }
    canonical: "IDNA + lowercase"
  - term: mac
    meaning: "an IEEE MAC address of a NIC"
    context_keys: ["mac", "*_mac"]
    schema:
      governs_anchor: mac
      value_pattern: '^([0-9a-f]{2}:){5}[0-9a-f]{2}$'
      canonical_note: "lowercase colon form"
    anchor: { class: hardware, establishing: true }
    merge: { cardinality: set, order: none }               # a host may have several NICs
    canonical: "lowercase colon form"
    exceptions:
      - { case: "cloned/spoofed or reused MAC (freed lease)", decision: "scope+date the anchor; never sole establisher if transient", why: "MACs can be duplicated", acked: 2026-07-31 }
  - term: serial
    meaning: "a hardware/chassis serial or asset serial"
    context_keys: ["serial", "identity.anchors[].serial"]
    schema:
      # NO PATTERN: serials are vendor-shaped, and inventing one would reject valid data to look thorough. But they
      # are COMPARED case- and space-insensitively (9.0): no vendor issues two serials differing only by case, and
      # a drill committed `syn-0042` beside `SYN-0042` as two machines with 0 errors.
      governs_anchor: serial
      compare_form: upper-trim
    anchor: { class: hardware, establishing: true }
    merge: { cardinality: single, order: none }
  - term: wg_pubkey
    meaning: "a WireGuard public key (crypto identity of an interface/peer)"
    context_keys: ["wg_pubkey"]
    schema:
      governs_anchor: wg_pubkey
      value_pattern: '^[A-Za-z0-9+/]{43}=$'
      canonical_note: "exact base64, 44 characters"
    anchor: { class: hardware, establishing: true }        # crypto-anchored to the keypair
    merge: { cardinality: single, order: none }
    canonical: "exact base64 (44 chars)"
  - term: emp_id
    meaning: "an employer-assigned unique employee identifier"
    context_keys: ["emp_id"]
    enforced_by: none      # no canonical form declared: an employer-assigned id has whatever shape the employer uses.
    anchor: { class: logical, establishing: true }         # name is NEVER an anchor
    merge: { cardinality: single, order: none }
  - term: id
    meaning: "a bean/mapping identifier = its filename stem (garden-local; NOT identity)"
    context_keys: ["bean", "mapping"]
    enforced_by: core      # kebab-case, id == filename, and uniqueness per (space,base) are CORE bean-grammar checks — schematising them would duplicate a rule that already bites.
    anchor: { class: none, establishing: false }
    handling: { format: "kebab-case; quote if numeric/reserved; kind-prefixed for high-cardinality kinds", unique: "per (space,base)" }
    exceptions:
      - { case: "duplicate legit human names (two hosts both called 'file-server')", decision: "ids disambiguate via kind-prefix+slug; anchor to serial/asset-tag; title may repeat (warn)", why: "labels collide; ids must not", acked: 2026-07-31 }
      - { case: "device replaced, role kept", decision: "role bean (stable) vs device bean (serial-anchored); retired → deprecated + role re-points via replaces:", why: "not silent id reuse", acked: 2026-07-31 }
  - term: ref
    # NARROWED at 2.0 (P6/E6): this term used to CLAIM refs/consumes/depends_on and state the DAG rule for
    # them. Those are now first-class relations with their own schemas, so `ref` describes only the LINK
    # FORM they share. This is the MAJOR change of the release: an existing term's handling moved.
    meaning: "the LINK FORM {bean|mapping: <id>[, field: <key>]} — a pointer to the single owner of a value. The relations that USE this form declare themselves (see refs, depends_on, and a garden's own edges)."
    context_keys: []
    enforced_by: core      # the link FORM and its resolution are CORE checks (target exists, named field present, shallow). Since 2.0 the acyclicity is declared per relation via schema.dag rather than here.
    anchor: { class: none, establishing: false }
    handling: { resolve: "target exists in right space; field present in target owns/attributes/details; shallow (ref-to-ref=warn)", graph: "acyclicity is declared PER RELATION via schema.dag — not asserted here for a fixed list of sections (narrowed at 2.0)" }
    exceptions:
      - { case: "'bean' as a plain DATA key", decision: "links only inside refs/consumes/depends_on", why: "reserved word collides with data", acked: 2026-07-31 }
      - { case: "YAML-coerced ref target (bean: no→False)", decision: "non-string target = error; quote the id", why: "coerced targets silently skipped", acked: 2026-07-31 }
  - term: shell-log
    meaning: "PROCESS term — how agent shell executions are logged: format + kept/summarized/discarded"
    context_keys: ["log/journal.md", "log/*"]
    enforced_by: none      # a PROCESS term: it governs how an agent logs shell work to log/journal.md, not the shape of any bean field. There is no bean data for a gate to check, and that is a property of the term, not a gap.
    anchor: { class: none, establishing: false }
    handling: { classes: { state-change: "KEEP full (cmd+purpose+outcome)", one-shot-recon: "SUMMARIZE one line", repeated-discardable: "DISCARD per-iteration; keep pattern+final" } }
    exceptions:
      - { case: "repeated/discardable output (monitor ticks, polling, retries)", decision: "log pattern+final once", why: "per-iteration noise buries signal", acked: 2026-07-31 }
  # == THE BEAN-GRAMMAR AND FACT-SECTION KEYS (added std-vocab@5.0, 2026-08-02, human-ratified) ==
  # These were never terms. They did not need to be while the gate enforced them in CORE and nothing else
  # read them — but `bin/dmmerge.py` became generic over top-level keys, and a key with no `merge:` facet
  # is merged by a SHAPE GUESS. A guess can be the wrong guess, so each of them now declares how it
  # merges. Most ratify what the guess already did; the three that do not are marked.
  - term: kind
    meaning: "which kind of being this bean records; a refinement of its nature, from the `kinds` registry"
    context_keys: [kind]
    enforced_by: core
    merge: { cardinality: single, order: none }
  - term: title
    meaning: "the bean's human title — one line, what this object is called"
    context_keys: [title]
    enforced_by: core
    merge: { cardinality: single, order: none }
  - term: summary
    meaning: "the bean's human summary — what this object IS, readable cold"
    context_keys: [summary]
    enforced_by: core
    merge: { cardinality: single, order: none }
  - term: tags
    meaning: "free retrieval labels. Deliberately open and never an enum: a tag is a finding aid, not a claim."
    context_keys: [tags]
    enforced_by: none
    merge: { cardinality: set, order: none }
  - term: owns
    meaning: "the facts this bean is the ONE owner of (MODEL Ground rule 1). Elsewhere they are pointed at, never copied."
    context_keys: [owns]
    enforced_by: none          # Rule 1 is a Part B judgment: no gate can tell a duplicate from a reference
    merge: { cardinality: multi, order: by-key }
  - term: attributes
    meaning: "the abstraction layer: a datum kept intact because it does not yet fit a category (MODEL Ground rule 2). Never dropped, never mis-bucketed."
    context_keys: [attributes]
    enforced_by: none
    merge: { cardinality: multi, order: by-key }
  - term: details
    meaning: "namespaced capsules of rich detail, so the bean stays paper-durable without crowding `owns` (Rule 6)"
    context_keys: [details]
    enforced_by: none
    merge: { cardinality: multi, order: by-key }
  - term: open
    meaning: "the questions this bean has not answered. An open item is a standing debt, not a defect."
    context_keys: [open]
    enforced_by: none
    merge: { cardinality: set, order: none }
  # == THE MERGE DRIVER'S OWN STATE (declared 2026-08-03, Phase 5 / D22) ==
  # `bin/dmmerge.py` writes these and `bin/dmcheck.py` reads them, and until now there was NO TERM
  # BETWEEN THEM — two tools agreeing about a key by coincidence, which is precisely the shape the
  # law-in-data rule exists to forbid. They are also the reason the unclean marker no longer lives on
  # `status`: `status` is a `single` merged term, so the driver writing its own flag there collided with
  # the algebra on one key, and the next merge turned it into a conflict the in-place writer could not
  # write back.
  - term: merge_open
    meaning: "this bean holds an unresolved merge: both values are kept and a human has not yet chosen. Written by the merge driver, read by the gate, cleared by the person who resolves it."
    context_keys: [merge_open]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: merge_conflicts
    meaning: "the dotted paths inside this bean that hold a captured disagreement. The companion to merge_open: it says WHERE, so a human does not have to search the document for it."
    context_keys: [merge_conflicts]
    enforced_by: none
    merge: { cardinality: set, order: none }
  - term: provenance_of
    # PER-LEAF PROVENANCE, BESIDE THE VALUES AND NEVER INSIDE THEM. `owns.os: AlmaLinux 9.8` stays what a
    # human reads; this says who said it. Written only by the merge driver, on beans it produced. Without
    # it a merged bean read back can only be re-merged as the READER's own assertion — every value
    # restamped `generated-by-tool` — which disarms the guard that an `inferred` value may never override
    # an `asserted-by-human` one, because SRC_RANK is what enforces that guard.
    meaning: "who said each merged value and how they know, keyed by the same dotted path merge_conflicts uses: {path: [{value, src, seen_in, subsumed?}]}. A subsumed value appears here and NOWHERE else, because the document carries only the winner."
    context_keys: [provenance_of]
    enforced_by: none
    merge: { cardinality: single, order: none }
  # == CONTRACT KEYS. `contract` is a Tier-0 kind and its `schema:` prose already names these five; they
  # are declared here so the merge reads them from the same place the kind describes them.
  - term: between
    meaning: "the parties to a contract"
    context_keys: [between]
    enforced_by: none
    # SINGLE, not set — and this CHANGES what the shape guess did. The parties to an agreement are
    # constitutive of it: unioning two gardens' lists would silently produce a three-party contract
    # nobody agreed to. Two gardens disagreeing about who signed is a conflict for a human.
    merge: { cardinality: single, order: none }
  - term: over
    meaning: "what a contract is over: the bean, and which facet or aspect of it"
    context_keys: [over]
    enforced_by: none
    # SINGLE, not a per-key collection — a reference capsule is one thing, exactly like `lives_in`.
    merge: { cardinality: single, order: none }
  - term: agreement_ref
    meaning: "provenance pointer to the agreement text a contract records"
    context_keys: [agreement_ref]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: conflict_rule
    meaning: "the deterministic rule that resolves a co-ownership dispute, via the MERGE lattice"
    context_keys: [conflict_rule]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: balance
    meaning: "whether a contract's exchange is settled or ongoing"
    context_keys: [balance]
    enforced_by: none
    merge: { cardinality: single, order: none }
  # == MAPPING KEYS. A `mapping` document records how bean data feeds a command or checklist. These were
  # missed on the first pass because `dmmerge.load_garden` globs `beans/*.md` only — the corpus merge
  # never saw them, though `.gitattributes` dispatches `mappings/*.md` to the same driver. Found by the
  # golden check that scans BOTH, which is the argument for asserting over the corpus rather than over
  # whatever the tool under test happens to read.
  - term: trigger
    meaning: "what causes a mapping to run: manual, an event, or a schedule"
    context_keys: [trigger]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: tool
    meaning: "the executable a mapping drives, with the host it is run on"
    context_keys: [tool]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: steps
    meaning: "the ordered steps a mapping performs"
    context_keys: [steps]
    # 10.1, T4: a list of PROSE lines (read in list order, as before) or a list of STEP ENTRIES
    # `{id, do, next: [{to, when?}], note?}`, never a mix. `next` absent or empty ends the routine; two or more
    # `next` entries are a branch and each names its condition in `when`.
    schema:
      on_sequence: routine
    # NOT a set: these are a SEQUENCE, and order carries the meaning — validating after installing is a
    # different procedure from validating before. A set-union would reorder them into nonsense, so the
    # whole list merges as one atom and two gardens with different steps conflict.
    merge: { cardinality: single, order: none }
  - term: produces
    meaning: "the artifact a mapping writes, and the reload or restart that publishes it"
    context_keys: [produces]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: authority
    meaning: "which side of a generated artifact is the source of truth, and which must never be hand-edited"
    context_keys: [authority]
    enforced_by: none
    merge: { cardinality: single, order: none }
  # == POSITION TERMS (added 5.1, human-ratified rule-change) ==
  # `located_at` and `timing` are the SAME STRUCTURE pointed at two dimensions, which is the whole claim:
  # sequence is general, and time and place are restrictions of it with different direction lines. They
  # are declared as two terms rather than one because what they are ASKED is different — where a being is
  # found, and when something happened — and a single term serving both would have to be read twice.
  - term: anchor_system
    # The enum OWNER. Nothing else may list the systems: this term's `values` are held equal to the
    # registry by the gate's own drift check, exactly as `nature` is held equal to `natures`.
    meaning: "the anchor system a position is stated in — the one owner of that enum"
    context_keys: [anchor_system]
    schema:
      shape: scalar
      values: [unix-filesystem, windows-filesystem, git-object-graph, physical, gregorian-civil, unix-epoch, geographic, event-anchored, network-segment]
      values_consistent_with: ["registry:anchor_systems[].system"]
    enforced_by: none   # it is never carried on a bean: it exists to OWN the enum that `located_at` and
                        # `timing` select their systems from. Occupancy is counted through their entries.
    merge: { cardinality: single, order: none }
  - term: unit
    meaning: "the resolution a position is held to — the one owner of that enum"
    context_keys: [unit]
    schema:
      shape: scalar
      values: [millisecond, second, minute, day]
      values_consistent_with: ["registry:units[].unit"]
    enforced_by: none   # as with anchor_system: an enum owner, carried through other terms' entries
    merge: { cardinality: single, order: none }
  - term: located_at
    # THE BEING'S LOCATIONS. The meaningful object is the being — a codebase — and it may be found as a
    # tree on a host, as reachable objects in a repository, or as a PRINTED COPY on a shelf. None of those
    # is privileged and a being may be at several at once. `openness` is the field that carries what cost
    # this estate a session: a position that is NOT KNOWN is recorded as unknown rather than omitted,
    # because an omitted location reads as "there is none" and that is how an exhaustive search over the
    # wrong domain produced output identical to a real one.
    meaning: >
      Where this being is found: a list of positions, each in a named anchor system, each stating how far
      it is known to reach. A being may be located in several systems at once, and a location that is not
      known is STATED as unknown rather than left out.
    context_keys: [located_at]
    schema:
      shape: list_of_entries
      entry_required_attrs: [system, openness]
      entry_values:
        openness: [here, elsewhere, unreachable, unknown]
      entry_in_registry:
        system: { registry: anchor_systems, take: system }
      entry_required_if:
        - { attr: openness, equals: here,        requires: [at] }
        - { attr: openness, equals: elsewhere,   requires: [at] }
        - { attr: openness, equals: unreachable, requires: [at] }
      entry_pattern_from_registry:
        { attr: at, registry: anchor_systems, keyed_by: system, take: pattern }
      entry_types: { observed: iso_date }
    entry_attrs:
      system:   "which anchor system this position is stated in — it selects the form the position must take"
      at:       "the position itself, in that system's ONE canonical form. Required unless openness is `unknown`, which is precisely the case where there is no position to state."
      openness: "here (reachable from the machine that recorded it) | elsewhere (reachable, and NOT from here) | unreachable (known, and cannot be reached) | unknown (nobody has established where it is)"
      observed: "ABSOLUTE date this location was checked. A location ages: a tree is moved, a branch is checked out elsewhere, a printout is filed."
      note:     "optional prose — the only place a `physical` address can live, since that system declares no canonical form"
    merge: { cardinality: multi, order: "by-system+at?" }
  - term: timing
    # WHEN, AT A DECLARED RESOLUTION. The open key is what makes this serve sessions without a session
    # schema: `start`, `sync`, `stop` are keys, not law, and a run with four sync points needs no
    # rule-change to record them. The closed part is each entry's shape — the same open-key/closed-figure
    # pattern `analysis_cache` proved.
    meaning: >
      When something happened, as an OPEN map of moment-name -> a position in a time anchor system at a
      STATED resolution. The resolution is declared, never inferred from how many digits were typed, so
      two positions whose resolutions overlap can be known to be unordered rather than silently ordered.
    context_keys: [timing]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      required_on_kinds: [session]
      entry_required_attrs: [system, at, unit]
      entry_in_registry:
        system: { registry: anchor_systems, take: system }
        unit:   { registry: units, take: unit }
      entry_pattern_from_registry:
        { attr: at, registry: anchor_systems, keyed_by: system, take: pattern }
    entry_attrs:
      system: "the time anchor system — gregorian-civil for a calendar reading, event-anchored for a position fixed only by its neighbours"
      at:     "the position, in that system's ONE canonical form"
      unit:   "the resolution ACTUALLY HELD. `2026-08-07T05:21` recorded at unit: minute means the second is not known — not that it was zero."
      by:     "optional: who or what read the clock, when that is not the bean's default provenance"
    key_note: >
      kebab-case moment names. Used so far: start | sync | stop. The key is DELIBERATELY OPEN and the gate
      is forbidden from enumerating it — a run with four sync points, or a moment nobody has named yet,
      must never require a rule-change.
    merge: { cardinality: multi, order: by-key }
  - term: roots
    # THE RESOLUTION HALF of the `root:` position form. A bean says WHERE a thing is in a portable way
    # (`root:addin/CloudApi`); a HOST says what that root means on itself. Two hosts therefore
    # never edit the same text to disagree about a path — each states its own resolution on its own bean,
    # which is what makes adding a machine a one-line change instead of a corpus migration.
    # It lives on the HOST because that is whose fact it is. A root map in a shared file would be one
    # document every machine has to edit, which is the merge conflict this design exists to avoid.
    meaning: >
      This host's resolution of logical roots: the map that turns a portable `root:<name>` position into a
      literal position on THIS machine. Absence is not an error — a host that does not resolve a root
      simply does not hold that thing, and a reader is told so rather than shown a path that is not there.
    context_keys: [roots]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [system, at]
      entry_in_registry:
        system: { registry: anchor_systems, take: system }
      entry_pattern_from_registry:
        { attr: at, registry: anchor_systems, keyed_by: system, take: pattern }
      entry_must_match:
        # THE JOIN (7.0): a host's roots are stated in the path grammar its OWN OS declares, so the two
        # can no longer disagree. `keyed_by: os` selects the operating_systems row by a field of the BEAN,
        # which is the same machinery that fixes a crown branch from a bean's nature. It is on `roots` and
        # NOT on `located_at`, deliberately: roots is the host describing itself and every bean carrying
        # it has an `os`, while `located_at` is carried by codebases, which have none.
        - { attr: system, registry: operating_systems, keyed_by: os, take: path_grammar }
      entry_types: { observed: iso_date }
    entry_attrs:
      system: "which filesystem system this host resolves the root in — pinned since 7.0 to the grammar this host's `os` declares, so it is checked rather than merely stated"
      at:     "the literal position this root means HERE, host named, in that system's canonical form"
      observed: "ABSOLUTE date the resolution was checked — a tree gets moved"
    key_note: >
      kebab-case root names, shared across hosts by AGREEMENT rather than by a registry: a root is a name
      two machines both choose to use, and centralising the list would re-introduce the one shared document
      this term exists to avoid.
    merge: { cardinality: multi, order: by-key }
  - term: role
    # The enum OWNER, the shape `anchor_system` and `net_protocol` already use. Never carried on a bean:
    # it exists so the `roles` registry is the one place the list lives.
    meaning: "a job a being does — the one owner of that enum"
    context_keys: [role]
    schema:
      shape: scalar
      values: [router, mail-primary, mail-backup, file-server, dns-resolver, dns-authoritative,
               monitoring, web, app-host, vpn-gateway, ledger-hub, workstation]
      values_consistent_with: ["registry:roles[].role"]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: roles
    # WHAT A BEING DOES. A LIST, and that is the whole point: a server may do five things and a router one,
    # and until 7.0 the estate expressed the first as free text in `owns.roles` and the second as a KIND.
    # Making this a term is what let `kind: router` be retired without losing the requirement that a
    # router document its treatments — `required_on_roles` reaches a list where `required_on_kinds` could
    # only ever reach a scalar.
    meaning: "the jobs this being does, each a row of the `roles` registry"
    context_keys: [roles]
    schema:
      shape: list_of_entries
      entry_required_attrs: [role]
      entry_in_registry:
        role: { registry: roles, take: role }
      entry_types: { observed: iso_date }
    entry_attrs:
      role:     "which job — a registry row, so a typo is an error and not a new role"
      why:      "optional: what this being does in that role that another in the same role would not"
      observed: "ABSOLUTE date the role was confirmed to be one this being actually performs"
    merge: { cardinality: multi, order: by-role }
  - term: os
    # WHAT A MACHINE RUNS, and the reason it is a registry rather than a string: it CONSTRAINS. An OS row
    # declares the `path_grammar` its filesystem positions take, and `roots` is held to it below. Before
    # 7.0 this was `owns.os` free text — a distribution name with its point release — and a router, the one
    # machine whose OS genuinely differs in kind, could not state it at all.
    meaning: "the operating system this machine runs — a row of the `operating_systems` registry"
    context_keys: [os]
    schema:
      shape: scalar
      values: [slackware, almalinux, windows, routeros, linux, debian, ubuntu, rhel, fedora, arch, alpine, freebsd, macos]
      values_consistent_with: ["registry:operating_systems[].os"]
    version_note: >
      The RELEASE (15.0, 9.7) is deliberately NOT part of this value. A version moves on every upgrade
      while the OS does not, and putting both in one scalar would make the enum unclosable — a new point
      release would be a rule-change. The release belongs in `owns.os_release`, beside the date it was read.
    merge: { cardinality: single, order: none }
  - term: storage_format
    meaning: "a format a volume may carry — the one owner of that enum"
    context_keys: [storage_format]
    schema:
      shape: scalar
      values: [ext4, ext2, vfat, swap, crypto_LUKS, LVM2_member, linux_raid_member, ntfs]
      values_consistent_with: ["registry:storage_formats[].format"]
    enforced_by: none
    merge: { cardinality: single, order: none }
  - term: volumes
    # THE STORAGE STACK, and the deliberate twin of `links`. Both record a layered carriage on one being;
    # both use `carried_by` to name the entry beneath; and neither is declared acyclic, for the reason
    # written out at length on `links` — `carried_by` names another entry on the SAME bean, so there is no
    # cross-bean graph for the gate to walk.
    #
    # THIS IS WHERE ext4 AND ntfs LIVE, and it is not where `unix-filesystem` lives. That distinction is
    # the point of the term: a path grammar is a property of the OS's API and a storage format is a
    # property of the volume, and NTFS mounted through ntfs-3g has unix paths, so a model that had one
    # axis for both could not describe an ordinary Windows disk read from Linux.
    meaning: >
      The storage this machine holds, as a layered stack: each entry a formatted volume, naming what
      carries it. Recorded so a machine can be REBUILT from its bean rather than from memory of it.
    context_keys: [volumes]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [format]
      entry_in_registry:
        format: { registry: storage_formats, take: format }
      entry_types: { observed: iso_date }
    entry_attrs:
      format:     "a row of storage_formats — ext4, crypto_LUKS, LVM2_member and so on"
      carried_by: "the `volumes` key beneath this one. A local key and NOT a ref: the stack is intra-bean, which is why it joins no acyclic check."
      uuid:       "the volume's own identifier, as its format reports it. The datum a rebuild needs and the one that survives a device rename."
      at:         "where it is mounted, in this machine's path grammar. Absent for a volume that holds no filesystem — a LUKS container or an LVM member is mounted nowhere."
      observed:   "ABSOLUTE date the layout was read off the machine"
    reproduction_note: >
      SCOPE, STATED BECAUSE IT IS ABOUT TO GROW. This term records the LAYOUT — what exists, what carries
      what, and where it is mounted — which is what a rebuild needs to recreate the shape. It does NOT
      record contents, keys or passphrases, and it must not: `no secrets` is a founding rule of this
      ledger. The operator has asked for beans complete enough to reproduce a machine, and the honest
      remaining gap is CONFIGURATION, which is a separate question from layout because config is
      SOMEBODY ELSE'S authoritative truth and ground rule 3 forbids mirroring it. See
      [[design-network-stack]] `open:` for where that is being taken up.
    merge: { cardinality: multi, order: by-key }

  - term: beanger
    # THE OPERATOR'S TERM, THEIR DESIGN AND THEIR NAME, 2026-08-07. BEAN + LEDGER: a per-datum ledger,
    # bean-structured. `log/journal.md` is the ledger of what the ESTATE did; a beanger is the ledger of
    # what ONE DATUM has been, and since 7.0 it has the same append-only record shape.
    #
    # THE SPLIT: the CURRENT value stays on the bean, in `owns`, where a reader already looks and where
    # every existing ref already points. The beanger carries the DEFINITION, the way to READ it, and the
    # RECORD LOG. The first draft copied the current value in here, which duplicated the fact and would
    # have dragged RETIRED values into the single-owner IP scan — an address a being no longer holds must
    # not still be owned by it: a released address belongs to nobody.
    #
    # WHY IT EXISTS, from this corpus: `owns.provides_ip: 203.0.113.10` is a definition and a value fused
    # into one scalar with NO DATE AT ALL. A re-scan of such a field cannot tell UNCHANGED from NEVER
    # LOOKED, and the day the value moves, when it moved is gone. Not hypothetical — a router's `owns
    # .wg_tunnel` carried an endpoint that HAD moved, .19 to .16, with nothing recording either fact.
    #
    # THE FOUR OPERATIONS. `add`, `change` and `remove` move the value; `confirm` does not, and that is
    # precisely why it is the one that had to be invented. Without a record for "checked, and it was as
    # recorded", a re-scan that finds nothing new leaves no trace, and silence then means both "verified
    # this morning" and "nobody has looked since July". `confirm` is the operation that makes the ledger
    # able to say how CONFIDENT it is, separately from what it says.
    #
    # WHAT IS DERIVED AND THEREFORE NOT STORED. `since` is the `at` of the newest add-or-change; `last_seen`
    # is the `at` of the newest record of any kind; `next` is simply the following element of an ORDERED
    # list. All three were stored fields in the first draft and all three are gone: a fact stated twice is
    # a fact that can disagree with itself, which is the argument this vocabulary already makes for
    # refusing a direction aspect. The chain is walkable both ways from `prev` plus list order, which is
    # what "walkable all ways" actually required.
    meaning: >
      A per-datum ledger: what a datum IS, which field on this bean holds its CURRENT value, how to read
      it, and the append-only log of every operation on it — each stamped to the millisecond, attributed,
      and linked to the one before.
    context_keys: [beanger]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [defines, tracks, source, records]
      pointer_fields: { tracks: bean_field_pointer }
    entry_attrs:
      defines: "WHAT this datum is, structurally — the part that stays true across every value it will ever hold. Written so a reader who has never seen the machine can tell which reading would refresh it."
      tracks:  "a pointer to the field holding the CURRENT value — `<section>.<key>` on this bean. The value is NOT copied here: it lives in one place and this names it."
      source:  "the exact command or file the value is read from, so the next scan reads THE SAME THING. Without it a differing value cannot be told from a differing METHOD — the failure this estate met when /sys/class/net reported a bond's MAC where ethtool -P reported the NIC's."
      records: "the append-only log, OLDEST FIRST. See `record_attrs`."
    record_attrs:
      # ONE LEVEL DEEPER THAN THE GATE VALIDATES, AND SAID SO RATHER THAN IMPLIED. The interpreter checks
      # the entries of a term, not the entries of a list INSIDE an entry, so everything below is convention
      # the gate does not yet enforce. That is a real gap and it is named here instead of being dressed up:
      # `entry_required_attrs` reaches `beanger.<datum>`, not `beanger.<datum>.records[]`. Closing it needs
      # a nested-entry mechanism in bin/dmcheck.py — a GATE change, tracked in [[design-network-stack]].
      seq:   "1-based position in this datum's log. The identity `prev` points at."
      at:    "the moment of the RECORD, epoch MILLISECONDS (see the `unix-epoch` anchor system). Milliseconds because two operations in one session can land in the same second and their order is the thing being recorded."
      unit:  "the resolution the moment was ACTUALLY held to — a row of `units`. Defaults to millisecond for anything this ledger stamped itself. A record reconstructed from a date carries `unit: day` and an `at` of that day's midnight, so that thirteen digits of apparent precision cannot be mistaken for thirteen digits of knowledge. This is the same rule `timing` already applies, and it exists because this estate has twice written a value that looked measured and was inferred."
      op:    "add | change | remove | confirm. `confirm` is the only one that does not move the value."
      value: "the value AS OF this record. Present on add and change; on `confirm` it is omitted, because repeating an unchanged value is the duplication this design removed. On `remove` it is omitted for the same reason — the outgoing value is already on the record before."
      prev:  "the `seq` of the record before, or null on the first. The BACK link only: forward is list order, and storing both would let them disagree."
      who:   "who performed it, in `provenance.by` form — `sam (operator)` for a person, `agent:<model>/<garden>` for an agent. One convention for attribution across the ledger, not a second."
      from_where: "the CURSOR the operation was performed FROM: `{host, session, guide}` — which machine, which working session, and which context the operator had in attention. All three are bean refs where a bean exists."
      to_where:   "what the operation was performed ON, as a bean ref, where that differs from the bean carrying the beanger. Absent for a plain local read."
      why:   "optional: what caused the change. Load-bearing on `change` and `remove`, where the value alone does not say what happened."
    merge: { cardinality: multi, order: by-key }

  - term: workspace
    # WHERE A SESSION DOES ITS WORK. Added 7.0 with `bin/dmsession.py`, because several sessions on one
    # host is a thing the estate now wants and one working copy cannot give it: two sessions in one clone
    # share one git INDEX, so `git add -A` from either stages the other's half-finished edits, and the
    # gate reads the STAGED blobs. Session A can then be refused for session B's mistake, or commit B's
    # unfinished bean under A's message with A's journal entry attached. Both writes are individually
    # legal, so no rule in this ledger catches it.
    #
    # A WORKTREE IS THE FIX AND THE BRANCH IS THE HAND-OFF. Each session gets its own working copy and its
    # own index while sharing one object store, so they cannot stage over each other — and they can still
    # read and merge one another's branches with no network hop, which is the sync-between-sessions half.
    meaning: "the working copy and branch a session commits from, on a named host"
    context_keys: [workspace]
    schema:
      shape: mapping
      required_on_kinds: [session]
      required_attrs: [host, at, branch]
      ref_fields: [host]
    attrs:
      host:      "a {bean} ref to the machine the session ran on. A session is not portable: its shell history, its reachability and what it could measure all belong to one machine."
      at:        "the working copy, as a position in that host's path grammar — `root:` form where a root exists, so it resolves on a second machine rather than reading as a literal path that is not there."
      branch:    "the git branch it commits to. `session/<slug>` by convention; `master` for a session that worked the main copy directly, which is what every session before 2026-08-07 did."
      opened_at: "epoch milliseconds, stamped by bin/dmsession.py. A session's own start is the one moment nobody should be estimating."
    merge: { cardinality: single, order: none }

  - term: capture
    # THE THIRD STATE GROUND RULE 3 NOW ALLOWS, ratified 2026-08-07. Until today a fact was either OURS or
    # SOMEBODY ELSE'S, and somebody else's could only be POINTED at. That rule was written for a good
    # reason — a ledger that mirrors every device's config silently becomes a stale second copy of it —
    # and it has one fatal gap: A POINTER TO A MACHINE THAT HAS DIED REPRODUCES NOTHING. The operator
    # asked for beans complete enough to rebuild the estate, and a pointer cannot do that.
    #
    # WHAT MAKES A CAPTURE SAFE IS THAT IT KNOWS WHAT IT IS. It names the thing it copied and who owns it,
    # the command that produced it, the moment it was taken, and the key by which a reader decides whether
    # it still holds. A copy carrying all four is useful; a copy carrying none is the stale mirror the old
    # rule feared, and the difference is entirely in the metadata rather than in the content.
    #
    # A CAPTURE IS NEVER AUTHORITATIVE AND IS NEVER APPLIED BACK. It does not live in `owns`, so it is not
    # scanned as a fact this bean owns — the same reasoning that keeps a `beanger` archive out of the
    # single-owner IP check, because an address a being no longer holds must not still be owned by it.
    # Restoring FROM a capture means reading the source first and treating the capture as the thing to
    # compare against, not the thing to paste.
    #
    # `redactions` IS REQUIRED, AND THAT IS THE WHOLE SECRETS DISCIPLINE. `no secrets` is founding here,
    # and a router export contains wireguard private keys, PPPoE passwords and community strings. Making
    # the field required means "nothing was removed" has to be WRITTEN DOWN as a claim somebody made,
    # rather than being the silent default of a field nobody filled in. An omission looks identical to a
    # clean capture; a required attr does not.
    meaning: >
      A dated, staleness-keyed copy of truth somebody else owns, taken so the thing can be REBUILT. Never
      authoritative, never applied back unread, never carrying a secret.
    context_keys: [capture]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [of, owned_by_them, source, taken_at, staleness_key, redactions, holds]
    entry_attrs:
      of:            "WHAT was copied — the config, the layout, the ruleset — in enough detail that a reader knows what they are holding."
      owned_by_them: "WHO owns the original and therefore the truth. A capture that does not name its owner reads as an authoritative fact, which is the failure ground rule 3 exists to prevent."
      source:        "the EXACT command that produced it, so it can be produced again and compared. The same argument `beanger.source` makes, and it earned it there within the hour: naming the command is what gets it run."
      taken_at:      "epoch milliseconds — a capture with no moment cannot be told from a guess."
      # TWO WAYS A STALENESS KEY LIES, both met within an hour of this term being written and both worth
      # stating here rather than only on the bean that hit them. (1) THE SOURCE STAMPS ITSELF: a RouterOS
      # export carries its own generation time, so a plain hash of the output changes on every run even
      # when nothing changed — a key must be computed over the content with such lines excluded, and the
      # exclusion must be written INTO the key so the check is reproducible. (2) STORAGE REWRITES THE
      # BYTES: git's default text handling converted CRLF to LF on commit, so the stored copy hashed
      # differently from what the command produces. Captures need `-text` in `.gitattributes`. Neither is
      # exotic; both make the key report "changed" forever, which is as useless as never reporting it.
      staleness_key: "how a reader decides whether this still holds: a config version, a change counter, a hash of the live export. The same job `analysis_cache.staleness_key` does for code, which is where this shape comes from rather than being invented beside it."
      redactions:    "WHAT WAS REMOVED and why. REQUIRED. Write `none — the source emits no secrets` explicitly if that is true; the point is that it is a claim, not a default."
      holds:         "the content itself for something small, or a `file:` pointer into this garden for something large. Large captures do not belong inline: a bean must stay legible on paper, and a 900-line router export is not."
      restores:      "optional: what this capture would let somebody rebuild, and what it would NOT. The honest half is usually the second."
    merge: { cardinality: multi, order: by-key }

  - term: risks
    # ONE INVENTORY. Until 7.0 this estate kept TWO that did not know about each other, plus loose
    # findings in `details` on individual beans:
    #   (1) one server's `details.risk_register` — 15 open findings as prose rows, ALL on that server
    #       regardless of what they were about: a monitoring container, web vhosts on a VPS, a file share. None of
    #       them is a fact about the server, and the bean that owns the failing thing could not be asked.
    #   (2) `capabilities` entries sitting at `permission: forbidden` + `feasibility: possible`, which the
    #       model already CALLS a live risk in the feasibility aspect's own commentary. Two of them exist
    #       — a public-resolver exposure and a DNS recursion — and NEITHER appeared in the
    #       register. Two inventories, no overlap, and no way to ask "what is wrong" once.
    #
    # WHY NOT JUST FOLD EVERYTHING INTO `capabilities`, which was the first idea and is wrong. Most
    # findings do fit its grid — R1 and R4 and R6 are all "forbidden, and currently the case", which is
    # already an in_breach cell. But R13 is "unattended LUKS unlock UNPROVEN" and R14 is "LIKELY a 502",
    # and neither is a modal claim at all: they are EPISTEMIC, about what nobody has established. The
    # capability aspects can say a thing is impossible or contingent; they cannot say nobody has looked.
    # A register is full of exactly that, so forcing it into the grid would have silently converted "we
    # do not know" into "it is fine", which is the worst possible loss for a risk inventory.
    #
    # `state` CARRIES THAT DISTINCTION and is the term's whole point. `live` and `latent` are the two the
    # capability grid could express; `unproven` is the one it could not and the one a register needs most.
    meaning: >
      The named ways this being can fail: what the defect is, what it costs, whether it is happening now,
      and how that was established. One inventory, on the bean that owns the failing thing.
    context_keys: [risks]
    schema:
      shape: open_map_of_entries
      key_form: kebab
      entry_required_attrs: [what, consequence, severity, state, evidence]
      entry_values:
        severity: [high, medium, low]
        state: [live, latent, unproven, resolved, superseded]
      entry_ref_fields: [owned_with]
    entry_attrs:
      what:        "the defect, plainly."
      consequence: "WHAT IT COSTS IF IT BITES. The load-bearing attr, and the one a prose register loses first — severity is an opinion about this, so recording severity without it records the opinion and drops the argument."
      severity:    "high | medium | low. An opinion, and it should follow from `consequence` rather than lead it."
      state:       >
        live (the defect IS the case right now) | latent (it is not, and nothing prevents it — the
        `forbidden` + `possible` shape) | unproven (nobody has established which, and that is the finding)
        | resolved | superseded (a different change made it moot; say which).
      evidence:    "how the state was established, specific enough to re-run. `unproven` states what WOULD establish it — a risk whose test is unnamed cannot be closed by anyone but its author."
      found:       "ABSOLUTE date the finding was first made."
      owned_with:  "optional {bean} ref: where the FIX lives, when that is not this bean. A defect on one being is often only fixable on another."
      note:        "optional: history, partial resolutions, and what a reader would otherwise re-derive."
    capability_note: >
      A `capabilities` entry at `forbidden` + `possible` IS a latent risk, and the two are deliberately
      NOT merged: a capability records the STANCE a being takes, a risk records a FAILURE MODE, and the
      same prohibition can hold on beings with no risk attached. Where one produces the other, the risk
      entry says so in `evidence` and cites the capability by name. The alternative — deriving risks from
      capabilities in the gate — was rejected because a derived finding cannot carry a `consequence` that
      anybody wrote, and the consequence is the part worth having.
    merge: { cardinality: multi, order: by-key }

kinds:
  - kind: codebase
    of_nature: metaphysical
    meaning: "a source-code tree managed as one object (a repo / Odoo addon / plugin project)."
    required: "code_paths (>=1 own-source entry) — enforced by the gate via the code_paths term."
    schema: "owns: repo/git_remote, stack, entrypoint, build/deploy target, api_surface (routes it exposes OR endpoints it consumes). Establishing anchor: git_remote (preferred) or a logical manifest/code id."
    min_anchors: "1 establishing (git_remote or a logical *_id) → else identity.status: provisional + open:"
  - kind: product
    of_nature: metaphysical
    meaning: "an umbrella bean tying a product's codebases + business context together; not itself code. A THIRD-PARTY product is recorded here for one reason only: so its per-host deployments have a TYPE to be instances of. That rationale belongs to this kind and is stated once — a product bean should describe the product, not re-explain why it exists. A product is a LOGICAL code unit — its mapping to storage (git repos) is many-to-many (sub-git or multi-git); git_remote is a source anchor, NOT product identity."
    schema: "owns: what-it-is, components (refs to codebase beans), business owner, deployment. nature: metaphysical; owned_by (explicit or via parent). Establishing anchor: a logical product_id."
    min_anchors: "1 establishing (logical product_id)"
  # == being-kinds for the ownership / type-token / habitat model (2026-08-02, human-ratified) ==
  - kind: org
    of_nature: metaphysical
    meaning: "an organization / juridical person (company) that owns beings."
    schema: "owns: business context. nature: metaphysical; owned_by: explicit facet-owners (legal/technical). Establishing anchor: a logical org_id or primary domain."
    min_anchors: "1 establishing (logical org_id or domain)"
  - kind: person
    of_nature: living
    ownership_form: crown          # a person may be owned ONLY by the crown (love, while alive) — never by a
                                   # bean. This also RESERVES the crown form: no other kind may name the
                                   # axiom directly, so every other chain must pass through a being.
    meaning: "a human being who can own/steward other beings. nature: living."
    schema: "identity anchor: email or a logical person_id. Persons are owned by love-while-alive via the crown axiom, so owned_by is NOT required on person."
    min_anchors: "1 establishing (logical person_id or email)"
  - kind: instance
    of_nature: living
    meaning: "a running token — a deployment of a code product in a habitat; carries the runtime facts (db/config/state). Distinct being from its code product."
    required: "instance_of (the product) + lives_in (the habitat) + owned_by (usually inherited via the product) — gate-enforced. nature: living."
    schema: "owns: runtime facts (db name, config, endpoints, live state). Establishing anchor: a deployment coordinate (host x product x db)."
    min_anchors: "1 establishing (deployment coordinate) -> else identity.status: provisional + open:"
  # == kinds that were in USE but undeclared before P3. Under D1 a kind need only name the nature it
  # refines and what it means; anchor family + min-anchors come from that nature.
  - kind: host
    of_nature: physical
    meaning: >
      A MACHINE THE ESTATE RUNS ON — bare metal or virtual, general-purpose or appliance. Widened at 7.0
      when `vps` and `router` were retired into it, because both described something other than what the
      being IS. `vps` described TENANCY, which `owned_by.legal.external` and `provides_habitat: linux-vm`
      already carried between them — and the kinds registry had flagged this against itself since P3
      ("D5 will re-read this as an instance living_on a provider"). `router` described a ROLE, which
      `roles:` now carries and `treatments` now evidences. What survives is the one question a kind
      should answer: this being is a machine.
    roles_note: >
      A host's ROLES are data, not kind. `treatments` is `required_on_roles: [router]`, so a machine
      declaring the router role must still document what it does to traffic — the mechanical guarantee
      `required_on_kinds: [router]` used to give is KEPT, and now reaches a machine that routes AMONG
      OTHER THINGS, which a kind could never express.
  - kind: domain
    of_nature: metaphysical
    meaning: "a DNS domain — a name held by agreement with a registry, not a thing in space."
  - kind: service
    of_nature: metaphysical
    meaning: "a named capability the estate provides or consumes (mail pipeline, monitoring), above any one host."
  - kind: program
    of_nature: metaphysical
    meaning: "a bounded body of work with an aim (a hardening programme), tracked as one object."
  - kind: design
    of_nature: metaphysical
    meaning: "a durable design/decision document — the recorded reasoning behind a change."
  - kind: session
    of_nature: metaphysical
    meaning: "a bounded stretch of work with a start, any number of sync points, and a stop. Declared because sessions already exist in practice — handed off in prose, their times nowhere in data — and because they are what makes `timing` earn a resolution: a session is the one object whose position must be held finer than a day."
    required: "timing (>=1 moment) — enforced by the gate via the timing term."
    schema: "timing: start / sync / stop, each a position in a time anchor system at a stated unit. owns: what the session did. Establishing anchor: a logical session_id."
    min_anchors: "1 establishing (logical session_id)"
  - kind: contract
    of_nature: metaphysical
    meaning: "a co-ownership agreement resolving multiple owners of ONE facet of ONE being (STRUCTURE ONLY for now — no instances)."
    schema: "between: [ownerA, ownerB]; over: {bean, facet}; agreement_ref (provenance -> the prior agreement text); conflict_rule (deterministic, MERGE lattice); balance: ongoing. nature: metaphysical. Establishing anchor: a logical contract_id."
    min_anchors: "1 establishing (logical contract_id)"
---
# daftar — Tier-0 Universal Standard Vocabulary

The portable, estate-agnostic classification shared by every garden — the abstract model of *types* (data + process) and *anchors* (identity classes). Gardens pin a version in their own `VOCAB.md` / `GARDEN.md` and add only local terms/exceptions there.

**Anchor classes.** Since P4 (2026-08-02, human-ratified) an anchor establishes identity if and only if it carries `establishing: true`. `class` survives as a *hint at why* — `hardware`, `logical`, `network`, `role`, `none` — and decides nothing. This prose once carried the pre-P4 table that made `class` decisive; it was deleted rather than annotated, because a law file that states revoked law in a region no tool reads is the worst place in the repo to be wrong. See `MODEL.md` and the `anchor_class` term above.

**Growth:** a garden-local term that proves general is **promoted** here via the SKILL promotion protocol (propose → show neighborhood → human ratifies → version bump + provenance). This file's version history is its changelog below.

## Changelog
- **1.0** (2026-07-31) — initial standard: `ip, hostname, fqdn, mac, serial, wg_pubkey, emp_id, id, ref, shell-log` with anchor/merge facets. Seeded from the project's v0.x design + 3 review rounds.
- **NOTE ON THE GAP.** This changelog jumps 1.0 → 6.0 and the four releases between them are missing.
  They were never written down here, and this file's own prose claims "this file's version history is its
  changelog below" — so the claim has been false since 2.0. Not backfilled from memory: git holds the real
  history and inventing entries from a diff would put a reconstruction where a record belongs. Recorded as
  a gap so the next reader knows it is one.
- **6.0** (2026-08-07, human-ratified rule-change) — **the network stack becomes data.** Two registries
  (`address_systems`: ipv4/ipv6 as SEPARATE systems, the call `anchor_systems` already made for
  filesystems; `net_protocols`: 14 rows). A fourth aspect, `confidentiality`, and the first ONE-DIMENSIONAL
  figure — `poles` always allowed it and nothing had exercised it. A `network` profile carrying
  `endpoints`, `links`, `reaches` and `treatments`, the last `required_on_kinds: [router]`. MAJOR rather
  than minor because that requirement retroactively re-classifies an existing bean, which is the stated
  criterion. Withdrew two Tier-0 vacancies the same day — `aspect:capability = permitted` and
  `aspect:necessity = necessary` — both predictions the new terms made come true within the hour.
- **7.0** (2026-08-07, human-ratified rule-change) — **kind stops carrying what a being DOES.** `router`
  and `vps` retired into a widened `host`: the first was a ROLE (the corpus already held a server's five roles
  as data while a router's one was a kind), the second was TENANCY (`owned_by.legal.external` and
  `provides_habitat` already said it, and the registry had flagged itself since P3). New registries
  `roles`, `operating_systems` and `storage_formats`; new terms `role`, `roles`, `os`, `storage_format`,
  `volumes`, and `beanger`. `roots.system` is now held by `entry_must_match` to the grammar its host's
  `os` declares. GATE CHANGE: `required_on_<axis>` reads a MULTI-VALUED axis — scalar, list of scalars, or
  list of entries — which is what let `treatments` move from `required_on_kinds: [router]` to
  `required_on_roles: [router]` without losing the guarantee. The gate's behaviour on every other corpus was unchanged.

- **8.0** (2026-09-17, human-ratified rule-change) — **a list's members are matched by a declared identity,
  never by accident.** `merge.order` for a `list_of_entries` term is `by-<field>[+<field>...]`, and a field
  may carry a trailing `?` meaning its ABSENCE is part of the identity. Three terms had declared `by-key`
  over entries that have no `key` field, so `bin/dmmerge.py` silently keyed each member by its whole
  content: the same role with a different `why` merged into TWO roles, with nothing said. Now: `roles`
  by-role; `treatments` by-kind+what; `endpoints` by-protocol+system+at+port? (protocol+system+at alone
  was measured NOT unique — 11 entries on three beans differ only by port — and
  an sftp endpoint, riding ssh, has no port of its own); `located_at` by-system+at? (an `unknown` position
  has no `at`, and by-at alone collided two unknowns in different systems); `consumes`
  by-bean?+mapping?+field? (an entry IS a ref, and the ref is its identity). MAJOR because merge outcomes
  change for beans that already passed. GATE CHANGE: the vocabulary is refused if a list term's identity
  names a field that is not required on every entry (unmarked) or not declared at all (`?`), and the
  merge refuses an entry missing an unmarked identity field instead of keying it by its content.

- **8.1** (2026-09-17, human-ratified rule-change) — **three predictions came true and are withdrawn.**
  Tier-0 vacancies `os.values = windows` `code_paths.scan_policy = skim` and `unit.values = minute`, each occupied by real beans. Checked
  against a real estate, not a fixture, before withdrawing. MINOR: a Tier-0 vacancy is advisory and no bean is re-classified. Deliberately
  NOT withdrawn: `analysis_cache.policy = skim` (no analysis reads structure only yet), `storage_format.values
  = ntfs` (no volume records it).

- **8.2** (2026-09-17, human-ratified rule-change) — **a garden can add, and the `domain` profile exists.** A
  cold-start drill found two things a new garden could not do without fighting the law. (1) To allow ONE value
  Tier-0 lacks, a garden had to copy a whole registry into VOCAB.md and declare a vacancy for every row it
  copied: now `schema: { values_add: [...] }` in a `local_terms` overlay appends to the enum, and
  `registry_additions: { <registry>: [rows] }` appends rows, and the garden accounts only for what it added.
  (2) A domain had no standard place for its registrar and expiry: `registration` is promoted from one
  garden's local vocabulary into a new opt-in `domain` profile, required on `kind: domain` for gardens that opt
  in. MINOR: both are additive, and no bean in a garden that does not opt in is re-classified.

- **9.0** (2026-09-17, human-ratified rule-change) — **a second cold-start drill, and what it found.** MAJOR, for
  one reason: `serial` now declares `compare_form: upper-trim`, so establishing serials that differ only by case
  or whitespace are ONE object — a garden holding `SYN-0042` and `syn-0042` as two machines, which passed before,
  is now refused. A stored serial not already in that form warns. Additive in the same release: the
  `operating_systems` registry and the `os` enum gain `linux`, `debian`, `ubuntu`, `rhel`, `fedora`, `arch`,
  `alpine`, `freebsd` and `macos` (until now the list held exactly the four systems of the garden it grew in),
  and the `pppoe` row loses a `transport: tcp` / port 1723 copied from `pptp`. A garden that added one of the new
  OS values locally with `values_add` is told to remove its copy.

- **9.1** (2026-09-19, proposed rule-change) — **knowledge as universal anchors: the `knowledge` profile.**
  Published classifications become shared codes every garden uses: ISCED-F 2013 fields of knowledge (UNESCO) and
  ISCO-08 occupations (ILO), each kept WHOLE in `seed/knowledge/` with their codes and English titles, plus a curated
  `technology` catalogue whose every row links the project's own official documentation, and an ISCO→ISCED
  crosswalk derived from a garden that classified hundreds of roles and skills by hand. Three generic gate
  additions: `registry_files` (a registry kept in a data file, never read as empty when missing),
  `value_in_registry` (an anchor must be a code of its scheme), and `registry_from` (an entry's code is checked
  against the scheme the entry names). An opt-in profile: a garden that does not extend `knowledge` inherits
  nothing. MINOR: additive; no bean anywhere is re-classified.

- **9.2** (2026-09-19, human-ratified rule-change, "T0") — **sequence: the second figure.** Until now every
  aspect was an opposition and `figure:` was free text (`square-of-opposition`, even on a one-axis aspect). A
  `figures` registry now owns that enum: `opposition`, named for what it is rather than for one dimension of it,
  since a square is its two-axis case and a cube its three-axis case; and a second figure, `sequence`: positions related by neighbourhood along direction lines, declared
  ONLY by five stated restrictions (`lines`, `metered`, `order`, `acyclic`, `ends`) plus its `domain`. Three
  aspects take it: `time` (one metered line, order PARTIAL, so positions whose resolutions overlap are
  unordered), `place` (semi-defined; civil time resolves through it), and `walk`, which re-reads the `dag`
  rule: a term with `dag: true` is a position on `walk`, and the gate refuses a cycle because `walk` declares
  `acyclic: true`, not because code names the key. An EXTENT (a duration, on time) is a bounded region of an
  ordered sequence's domain; an opposition has none, and says so. MINOR by effect: the re-reading of `dag` changes no
  verdict (proved by running both gates over a real garden and 47 mutations of it); the one new requirement is
  that an aspect's `figure` names a declared figure, which refuses only a GARDEN-LOCAL aspect with an undeclared
  figure, and no garden is known to declare a local aspect.

- **9.3** (2026-09-20, human-ratified rule-change, "T2") — **the merge orders positions in time.** `leaf_orders`
  gains `instant`, which applies to every value that is a position in `gregorian-civil`'s one form, whatever
  its key is called (a leaf order may now name a `system` instead of key names). A reading is absorbed by a
  finer one it contains; readings that do not nest stay a conflict, because `time` declares its order partial.
  MINOR: two gardens that recorded one moment at different resolutions now converge where they conflicted.

- **10.0** (2026-09-20, human-ratified rule-change, "T3") — **time in the record itself.** MAJOR, for one
  reason: a journal entry a commit ADDS must be headed with a position in gregorian-civil's one form, to at least
  the minute, with its offset (`## 2026-09-20 00:15+03:00 · who · what`), per the new `journal` block. A garden
  whose writers head entries with a date alone, or with `+0300`, has its next commit refused until they write the
  form; the entries already written are never checked. Additive in the same release: a `value_types` registry
  moves the gate's type patterns into the law, and declares `iso_date` as the calendar at unit DAY, so every
  existing date is a position whose time of day is unknown, with no data changed. `dmupgrade` heads its journal
  entry in the new form.

- **10.1** (2026-09-20, human-ratified rule-change, "T4") — **routines are sequences.** A `routine` aspect on
  the sequence figure (open lines, because branches add lines; NOT acyclic, because a routine may loop), and
  `steps` gains `on_sequence: routine`: its value is either prose lines, read in list order as before, or step
  entries `{id, do, next: [{to, when?}], note?}`. A step's `next` is a CLOSED neighbourhood, these branches and no
  others, so the gate refuses a branch that points nowhere, a step nothing reaches, a branch without its
  condition, and a routine that never ends. MINOR: prose steps stay legal, so no existing mapping changes.

- **11.0** (2026-09-20, human-ratified rule-change, "place P3") — **place, where time already went.** MAJOR, for
  one reason: `analysis_cache.staleness_key` must now be a position in the git object graph (`<repo>@<sha>`) or
  `manual:<why>`. `git-head:<sha>` was resolved against whatever tree the READER had checked out, so one
  analysis had one verdict per machine; a garden carrying the old spelling has its next commit refused until it
  restates them. Additive in the same release: a `network-segment` anchor system, because a segment is WHERE A
  BEING IS ATTACHED (a place) as against where it answers (an address); `entry_pattern` and `entry_soft_pattern`
  in the schema language; and `code_paths.path` / `covers_paths` WARN while they carry a bare absolute path,
  which names no host — in the estate this grew in, 13 such paths exist on two machines as two different trees.
  The error for those follows in a later release, once a corpus has been migrated onto `root:` positions.
